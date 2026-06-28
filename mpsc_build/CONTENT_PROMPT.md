# MPSC Content-Factory Prompt (run in a fresh Claude Code session, model = Sonnet)

Paste everything below the line into a new session opened in the repo
`/Users/faisalchishti/Desktop/claude-projects/Learning`. It is resumable — run it
again and again; each run produces more topic content and stops cleanly.

---

You are generating comprehensive, exam-complete MPSC learning content for the tracker in this repo. The pipeline already exists and is live at https://faisalchishti08.github.io/mpsc/ . Do NOT redesign anything — just author content files and deploy.

## Your job
For MPSC Rajyaseva micro-topics, write one Markdown file per topic at:
`mpsc_build/content/<subject_key>/<topic_id>.md`
following the EXACT template below, at a depth where the candidate needs no other book. English medium. Work SEQUENTIALLY, one topic at a time, in priority order.

## Step 1 — find what's missing
Run: `python3 -m mpsc_build.content_status 25`
It prints PROGRESS and the next 25 missing topics in priority order (subject | topic_id | [stages/MH] | text). Work through them top to bottom.

## Step 2 — write each topic file
Create `mpsc_build/content/<subject>/<topic_id>.md` (the dir may need creating). Use the topic_id and subject exactly as printed. Follow this template with these EXACT `##` headers, in this order:

```
## Overview
<2–4 sentences: what it is + why it matters for MPSC>

## In-Depth
<the full exam-rich explanation: concepts, mechanisms, named facts, dates, data,
examples, cause–effect. Use ### sub-headings, bullet lists, and HTML <table>...</table>
for comparisons/data where useful. This is the bulk — be thorough and accurate.>

## Maharashtra Connection
<state-specific angle; if genuinely none write "Not directly Maharashtra-specific." and add any indirect link>

## Key Facts
- <≥5 crisp bullet facts / figures / dates for quick revision>

## Memory Aids
<mnemonics, acronyms, or a short text mind-map; a single "—" line is allowed if truly N/A>

## Exam Traps
<common confusions / mistakes specific to this topic>

## Questions
**Prelims (MCQ-style):**
1. [Asked] <question> — *answer/hint*
2. [Expected] <question> — *answer/hint*
3. [Expected] <question> — *answer/hint*

**Mains (descriptive):**
1. [Asked] <question>
2. [Expected] <question>

## Linkages
- <related topic ids / names, cross-subject where relevant>
```

Rules:
- `[Asked]` = representative of what has historically been asked (your best judgement; we have no verified PYQ DB). `[Expected]` = high-probability future question. Tag honestly.
- Minimum: all 8 sections, ≥350 words total, ≥3 Prelims items and ≥2 Mains items.
- Tables: author as raw HTML (`<table><tr><th>…</th></tr>…</table>`) — the converter passes HTML through.
- Source: use your own knowledge (you are strong on Indian GS/MPSC). Use web search ONLY for volatile facts — current scheme names/amounts, latest data/years, exact Maharashtra-specific specifics. Do not web-research every topic; it is too slow.
- Match the quality and structure of the three seed files already in the repo — read them first as exemplars:
  - `mpsc_build/content/maharashtra/mh-pr-formation.md`
  - `mpsc_build/content/history/hist-mar-shivaji.md`
  - `mpsc_build/content/polity/pol-cf-preamble.md`

## Step 3 — validate, build, deploy (after finishing a subject, OR every ~20 files)
Run, in order:
```
python3 -m mpsc_build.validate
python3 -m mpsc_build.validate_content
python3 -m mpsc_build.generate
```
All must pass (`OK …`). `validate_content` will reject thin files (missing sections, <350 words, too few questions) — fix any flagged file, then re-run.

Then commit and deploy:
```
git add mpsc_build/content mpsc
git commit -m "content: <subject> learning notes (<N> topics)"
git subtree split --prefix=mpsc -b mpsc-dep && \
  git push git@github.com:faisalchishti08/mpsc.git mpsc-dep:main && \
  git branch -D mpsc-dep
```
(Pages auto-rebuilds; topic pages go live at https://faisalchishti08.github.io/mpsc/topics/<id>.html)

## Step 4 — loop / stop cleanly
Repeat Steps 1–3. When your context is getting full, STOP after a clean commit+deploy and print the latest `python3 -m mpsc_build.content_status 1` PROGRESS line so the next session knows where to resume. Never leave uncommitted half-written files.

## Priority order (already encoded in content_status)
maharashtra → history → polity → geography → economy → environment → society → science_tech → current_affairs → international_relations → internal_security → ethics → csat → geography_optional → essay → language → interview.

## Definition of done
`python3 -m mpsc_build.content_status 1` prints `PROGRESS: 1711/1711 topics have content (100%)`.
