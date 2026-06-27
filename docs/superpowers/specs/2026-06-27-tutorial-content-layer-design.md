# Tutorial Content Layer — Design Spec

**Date:** 2026-06-27
**Status:** Approved design → ready for implementation planning
**Owner:** faisal

## 1. Problem

The Learning hub has **27 cards / ~5,272 micro-topics**, each a checkbox in a
self-contained HTML checklist generated from `_build/data_*.py`. Today a topic is
just a string you tick off. There is **no learning content** — to actually study a
topic you must leave the site (W3Schools, MDN, docs, etc.).

**Goal:** make this a one-stop tutorial spot. Clicking a topic opens an in-depth,
example-driven, runnable tutorial for that exact topic — basics → advanced, in
simple language, with diagrams and explained code — so the user never has to go
anywhere else. After reading, mark the topic complete.

## 2. Goals & non-goals

**Goals**
- Every topic gets its own tutorial page following a fixed 7-part template.
- Pages are self-contained, offline-capable, theme-matched to the existing dark UI.
- Runnable, copy-pasteable code examples with line-by-line walkthroughs.
- Click a topic in the checklist → land on its tutorial; mark-complete syncs back.
- Content is generated incrementally, one bounded phase at a time, via a single
  re-runnable daily driver prompt that always resumes where it left off.
- De-risk via a **pilot**: build the full pipeline + UX, validate quality on the
  first 2–3 sections of one area before mass rollout.

**Non-goals**
- No backend, no database, no build server. Static files only (GitHub Pages + `file://`).
- No external runtime dependencies (no CDN, no npm at runtime). Build-time Python only.
- Not rewriting the existing checklist topic data — only **appending** a content layer.
- Not reordering existing topics (would shift stable IDs).

## 3. Key decisions (locked with user)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Rollout | **Pilot one area first** (Web Development), then roll out the rest phase by phase |
| 2 | Content UX | **Dedicated tutorial page per topic** (`.html`), not inline/modal |
| 3 | Template | **Full 7-part** (what / why / concept / diagram / runnable example / walkthrough / gotchas) |
| 4 | Phase size | **One section per phase**, auto-split to **≤12 topics** per phase |
| 5 | Gen method | **Sequential single-thread** (main session writes pages one by one) |
| 6 | Source format | **Markdown source** files, built to HTML via a small bundled converter |

## 4. Architecture

### 4.1 Topic identity
- The checklist already assigns each topic a 1-based per-card index `gi` (see
  `_build/shell.py`). That index is the **stable topic ID** (`t{gi}`).
- A topic maps to exactly one tutorial page:
  `tutorials/<card>/<NNNN>-<slug>.html`
  where `<card>` = card filename stem (`webdev`), `<NNNN>` = zero-padded `gi`,
  `<slug>` = kebab-case of the topic text (deduped if needed).
- **Invariant:** existing topics are never reordered or deleted, only appended.
  Reordering would re-number `gi` and break links. A build-time check asserts the
  topic-text→gi mapping for already-built content is unchanged.

### 4.2 Content source (Markdown)
- One file per topic: `content/<card>/<NNNN>-<slug>.md`.
- Front-matter (simple `key: value` block between `---` fences):
  `card`, `gi`, `slug`, `title`.
- Body = fixed 7-heading skeleton, **in this exact order**:
  1. `## 1. What it is` — plain-language definition, no jargon.
  2. `## 2. Why & when` — why it exists, when to reach for it, alternatives.
  3. `## 3. Core concept` — the mechanism explained from basics to advanced.
  4. `## 4. Diagram` — inline `<svg>` or ASCII diagram illustrating the concept.
  5. `## 5. Runnable example` — a complete, copy-paste-and-run example in a fenced
     code block with a language tag, plus a one-line "How to run" note.
  6. `## 6. Walkthrough` — line-by-line / step-by-step explanation of the example
     (or algorithm explanation where code isn't applicable).
  7. `## 7. Gotchas & takeaways` — common mistakes + bullet-point key takeaways.

### 4.3 Markdown converter — `_build/md.py`
Zero-dependency, build-time only. Supported subset (sufficient for tutorials):
- Headings `#`..`######`
- Paragraphs, line breaks
- **bold**, _italic_, `inline code`
- Fenced code blocks ` ```lang ` → `<pre><code class="lang-…">` with HTML-escaped
  body and a copy button (button injected by the shell, not the converter).
- Unordered + ordered lists (one level + simple nesting)
- Tables (pipe syntax)
- Blockquotes (used for gotchas/notes)
- **Raw HTML passthrough** for `<svg>…</svg>` and other block HTML (so diagrams
  render verbatim).
- Links `[text](url)`.
Anything outside the subset is escaped/printed literally rather than silently dropped.

### 4.4 Tutorial page shell — `_build/tutorial_shell.py`
Renders one converted topic into a self-contained page that matches the existing
dark theme (`--bg #0d1117`, `--accent #6db33f`, same fonts). Chrome:
- **Header:** breadcrumb `Area › Section`, topic title, "← Back to checklist"
  link (to `../../<card>.html#sec-<n>`), and a **Mark complete** checkbox.
- **Body:** the 7 rendered parts, each in a labeled card.
- **Code blocks:** every `<pre>` gets a **Copy** button (clipboard API + fallback).
- **Footer nav:** **← Prev topic** / **Next topic →** (within the same card, by `gi`).
- All CSS/JS inlined; no external requests.

### 4.5 Mark-complete sync
- The tutorial page uses the **same** `localStorage` key as its card checklist
  (`spring-checklist:<card>.html`) and the **same** topic ID (`t{gi}`).
- Toggling "Mark complete" on the tutorial writes `state[t{gi}]` exactly as the
  checklist does; the checklist reflects it on next load, and vice-versa.
- **Works on GitHub Pages** (single origin). **Known limitation:** under raw
  `file://`, browsers may scope `localStorage` per file, so cross-file sync isn't
  guaranteed offline. Pages is the primary target; documented, not blocking.

### 4.6 Checklist linking — change to `_build/shell.py` + `generate.py`
- `generate.py` scans `tutorials/<card>/` and builds a **link-map** `{gi: relUrl}`
  of topics that have a generated page.
- The map is injected into each card's HTML. In `shell.py`, when rendering a topic:
  - if `gi` is in the map → label becomes a link (`<a href=…>` + a small 📖 badge),
  - else → plain text as today.
- This makes partial rollout look intentional: built topics are clickable, the rest
  are normal checkboxes until their phase runs.

### 4.7 Build integration — `generate.py`
Extended responsibilities (in addition to current checklist + index build):
1. For every `content/<card>/*.md`: convert (`md.py`) → wrap (`tutorial_shell.py`)
   → write `tutorials/<card>/<NNNN>-<slug>.html`.
2. Compute prev/next per card by sorted `gi`.
3. **Lint** each tutorial before writing (see §6). Fail the build loudly on any
   violation so bad content can't silently ship.
4. Build the link-map and regenerate the affected card checklist(s).
5. Print a summary: pages built, topics linked per card, lint status.

### 4.8 Phase manifest — `content/_manifest.json`
Single source of truth for what's done and what's next:
```json
{
  "pilot": "webdev",
  "cards": {
    "webdev": {
      "title": "Web Development",
      "sections": [
        {"name": "HTML", "tag": "html",
         "topics": [{"gi": 41, "slug": "semantic-elements", "status": "done"}, ...],
         "phases": [{"id": "webdev/html#1", "gis": [41,42,...], "status": "done"}, ...]}
      ]
    }
  },
  "next_phase": "webdev/css#1"
}
```
- Built/refreshed from the data modules + existing `tutorials/` on each run.
- A topic is `done` when its tutorial file exists and passes lint.
- `next_phase` = first phase with any `pending` topic, in card→section→split order.

## 5. The daily driver (re-runnable phase prompt)

A single prompt the user pastes each day. It is **idempotent and resumable** — same
text every time, always continues from the manifest. High-level algorithm:

1. Read `content/_manifest.json`; determine `next_phase` and its pending `gi`s
   (cap 12; if a section is larger it is already split into `#1`, `#2`, …).
2. For each topic in the phase, in order:
   - Author `content/<card>/<NNNN>-<slug>.md` against the 7-part template:
     in-depth, simple language, runnable example, explained walkthrough, diagram.
3. Run `python3 _build/generate.py`.
4. Verify: build succeeded, lint passed for the new pages, each page renders (HTML
   well-formed, 7 sections present, ≥1 runnable code block, prev/next + back links
   resolve), checklist now links the new `gi`s.
5. Update the manifest (mark topics/phase `done`, advance `next_phase`).
6. Commit + push (`Co-Authored-By: Claude Opus 4.8`).
7. Print: `Phase <id> complete — N pages. Next: <next_phase> (M topics).`

The exact paste-ready prompt text is delivered as part of implementation (a file
`docs/superpowers/DAILY_PROMPT.md`), so the user can copy it verbatim.

## 6. Quality bar (automated lint, enforced each phase)

Each tutorial must pass before it is allowed to ship:
- All **7 headings present**, in order, none empty.
- **≥1 fenced code block** with a language tag in "Runnable example".
- "Walkthrough" references the example (non-trivial length).
- A **diagram** present in part 4 (`<svg>` or ASCII block).
- Front-matter `gi`/`slug`/`title` match the filename and the data-module topic text.
- No broken internal links (prev/next/back targets exist).
- No `TODO`/`TBD`/placeholder text.

## 7. Pilot plan

- **Area:** Web Development (`webdev.html`, ~1,109 topics, ~25 sections).
- **Estimate:** ≤12 topics/phase → ~90–95 phases for the pilot area.
- **Gate:** after the first **2–3 sections** are built, the user reviews real pages
  and signs off on depth/clarity/format before the remaining phases proceed.
- After the pilot area is fully built and approved, the same engine rolls through the
  remaining 26 cards with no code changes — only more content phases.

## 8. File/dir layout (new + changed)

```
content/
  _manifest.json
  webdev/
    0041-semantic-elements.md
    ...
tutorials/
  webdev/
    0041-semantic-elements.html
    ...
_build/
  md.py                # NEW  markdown→html (zero-dep)
  tutorial_shell.py    # NEW  per-topic page shell
  generate.py          # CHANGED  build tutorials, link-map, lint, manifest
  shell.py             # CHANGED  render topic as link when a page exists
docs/superpowers/
  specs/2026-06-27-tutorial-content-layer-design.md  # this file
  DAILY_PROMPT.md      # NEW  paste-ready daily driver prompt
```

## 9. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| 5,272 pages = huge effort | Bounded phases + manifest resume; pilot-gate before scale |
| Topic reordering breaks IDs | Append-only invariant + build-time mapping check |
| Inconsistent quality across thousands of pages | Fixed template + automated lint gate every phase |
| File-size / count sprawl | One small page per topic (not one giant file); no runtime deps |
| `file://` localStorage scoping | Pages is primary target; documented limitation |
| Markdown converter edge cases | Constrained subset + raw-HTML passthrough + escape-don't-drop fallback |

## 10. Success criteria

- A topic clicked in the checklist opens its tutorial page; content is in-depth,
  simple, with a runnable+explained example and a diagram.
- Mark-complete on the page reflects in the checklist (on Pages).
- The same daily prompt, pasted on consecutive days, advances the manifest and
  builds the next phase with zero manual bookkeeping.
- Pilot area (Web Development) reaches 100% built and passes the user's quality gate.
