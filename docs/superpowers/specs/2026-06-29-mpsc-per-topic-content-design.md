# MPSC Per-Topic Learning Content — Design Spec

**Date:** 2026-06-29
**Owner:** faisal
**Status:** Approved design → ready for implementation plan
**Builds on:** the MPSC tracker (`mpsc_build/` + `mpsc/`, 1,711 micro-topics across 17 subjects, live at https://faisalchishti08.github.io/mpsc/).

## 1. Purpose

For **every micro-topic** in the MPSC tracker, generate **comprehensive, exam-complete learning content** that opens when the topic is clicked. The content must be rich enough that the candidate does not need any other book or material for that topic, and must include the kinds of questions asked / likely to be asked (Prelims + Mains). English medium.

This spec covers the **system** (storage, build pipeline, viewer, generation loop, quality gate). The actual 1,711-topic content is produced by running the generation loop (separate Sonnet sessions), driven by a runnable prompt produced alongside this work.

## 2. Confirmed decisions

| Decision | Choice |
|----------|--------|
| Delivery | **One standalone HTML page per topic** at `mpsc/topics/<topic_id>.html`. Topic label in the checklist links to it (opens in a new tab so checkbox state survives). |
| Depth | **Comprehensive, exam-complete** — ~500–900 words per topic + questions; goal: no other source needed. |
| Source | **Model knowledge** (strong on Indian GS/MPSC); web research only for volatile facts (current schemes, latest data, Maharashtra specifics). |
| Questions | **Model-generated, labeled** — Prelims (MCQ-style) + Mains (descriptive), each tagged `Asked` (representative PYQ-style) or `Expected`. |
| Run mode | **Sequential** — the running session writes each topic itself, one at a time (max consistency). No content subagents. |
| Rollout order | **Priority by exam weight**: maharashtra → history → polity → geography → economy → environment → society → science_tech → current_affairs → international_relations → internal_security → ethics → csat → geography_optional → essay → language → interview. |

## 3. Content source format

- One Markdown file per topic: `mpsc_build/content/<subject_key>/<topic_id>.md`.
  - `<subject_key>` = subject `key` (e.g. `history`); `<topic_id>` = the existing stable topic `id` (e.g. `hist-mod-1857-revolt`).
- Markdown is chosen for editability and version control. Tables (PYQ tables, comparisons) may be authored as raw HTML inside the Markdown (passed through verbatim).
- A small front-matter-free convention: the file is pure content following the template (§4). The topic title/badges are injected by the generator from syllabus data — **not** repeated in the `.md`.

## 4. Content template (every topic)

Each `.md` MUST contain these sections, in order, with these exact `##` headers (the content-lint gate enforces them):

```markdown
## Overview
<2–4 sentences: what it is + why it matters for MPSC>

## In-Depth
<the full exam-rich explanation: concepts, mechanisms, facts, dates, data, named
examples, cause–effect. This is the bulk. Use ### sub-headings, lists, and HTML
tables where useful.>

## Maharashtra Connection
<state-specific angle; if genuinely none, write "Not directly Maharashtra-specific."
and add any indirect link.>

## Key Facts
- <crisp bullet facts / figures / dates for quick revision (≥5 bullets)>

## Memory Aids
<mnemonics, acronyms, or a short text mind-map; "—" allowed if truly N/A>

## Exam Traps
<common confusions / mistakes for this topic>

## Questions
**Prelims (MCQ-style):**
1. [Asked] <question> — *answer/hint*
2. [Expected] <question> — *answer/hint*
3. ... (≥3 total)

**Mains (descriptive):**
1. [Asked] <question>
2. [Expected] <question>
   (≥2 total)

## Linkages
- <related topic names / ids, cross-subject where relevant>
```

`[Asked]` = representative of what has historically been asked (model judgement, not a verified PYQ DB). `[Expected]` = high-probability future question. The viewer renders this labeling so the candidate knows the difference.

## 5. Build pipeline

- **`mpsc_build/mdlite.py`** — vendored, zero-dependency Markdown→HTML converter. Supports: `#`/`##`/`###` headings, unordered (`-`,`*`) and ordered (`1.`) lists, `**bold**`, `*italic*`, `` `code` ``, `>` blockquote, `---` hr, `[text](url)` links, paragraphs, and **raw-HTML block passthrough** (lines beginning with `<` are emitted verbatim, enabling tables). Deterministic, no network.
- **`mpsc_build/template.py`** — add `render_topic_page(subject, topic, content_html) -> str`: a standalone page with the existing dark theme, header showing topic title + stage/MH badges + breadcrumb "← <Subject>" linking back to `../<subject>.html`, and the rendered content. Self-contained (inline CSS).
- **`mpsc_build/generate.py`** — after generating subject pages, walk `content/`; for each `<subject>/<id>.md`, render to `mpsc/topics/<id>.html`. Pass the set of topic-ids-with-content into `render_page` so the checklist can mark/links them.
- **Checklist change (`render_page`)**: if a topic has content, render its label as `<a class="tlink" href="topics/<id>.html" target="_blank">…</a>` plus a `📖` marker; else plain `<label>` as today. Checkbox unchanged.

## 6. Quality gate

- **`mpsc_build/validate_content.py`** (run in addition to `validate.py`): for every `.md` present, assert:
  - all eight `##` section headers present, in order;
  - total length ≥ 350 words;
  - `## Questions` contains ≥3 `Prelims` items and ≥2 `Mains` items;
  - every referenced `<topic_id>` filename matches a real topic id in the syllabus (no orphan content).
  - Exits non-zero (fails build) on any violation — blocks thin/low-effort content from shipping.
- This does NOT judge factual accuracy (model-generated); the footer discloses that and flags volatile facts for verification.

## 7. Generation loop (resumable, multi-session)

- **Done = file exists.** `mpsc_build/content_status.py` prints, in priority order, the next batch of topics whose `.md` is missing (with subject, id, text, stages, mh).
- A run: pick the next missing topic in priority order → write its `.md` to the §4 template at comprehensive depth → lint just that file → move on. After finishing a subject (or every ~25 topics if a subject is large), run `generate` + `validate` + `validate_content`, commit, and push the `mpsc/` subtree to the `mpsc` repo (live deploy).
- A run ends cleanly when context is getting full: it commits whatever is done and reports remaining counts. The next session resumes from `content_status.py` — no state to corrupt.
- **Order within a subject:** syllabus order (section → group → topic).

## 8. Deployment

- Same as the tracker: commit to Learning `main`, then `git subtree split --prefix=mpsc -b <tmp>` and push `<tmp>:main` to `git@github.com:faisalchishti08/mpsc.git`; Pages rebuilds. Topic pages live at `https://faisalchishti08.github.io/mpsc/topics/<id>.html`.

## 9. Out of scope (YAGNI)

- No real PYQ database integration (model-generated, labeled — can be a future upgrade).
- No images/diagrams as files (text mnemonics + HTML tables only).
- No search across content, no spaced-repetition, no per-topic notes (separate future features).
- No Marathi content (English medium).

## 10. Success criteria

- Clicking any topic with content opens a comprehensive, well-structured learning page (all template sections), styled like the site, with a working back link.
- Each content page is self-sufficient for that topic and shows labeled Prelims + Mains questions.
- Generation is fully resumable across sessions; partially-generated state always builds and deploys cleanly (topics without content degrade gracefully to plain labels).
- Content-lint gate blocks thin content.
- A runnable Sonnet prompt exists that drives the loop end-to-end.

## 11. Effort note

1,711 comprehensive topics ≈ 1M+ words. This is many sequential sessions. The architecture's job is to make that **safe, resumable, and incrementally live** — high-priority subjects (Maharashtra, History, Polity, Geography, Economy ≈ 773 topics) deliver first.
