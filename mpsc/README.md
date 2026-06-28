# MPSC Rajyaseva — Master Syllabus Tracker

A pure-HTML study tracker for the **MPSC Rajyaseva (Maharashtra State Services) Examination** — Prelims + Mains + Interview. English medium. **1,711 micro-topics** across 17 subjects (incl. a dedicated Maharashtra Static GK page — ~45% of MPSC is state-specific), mapped to the new descriptive Mains pattern (2025+) and enriched against past-paper trends.

## Use it

Open `index.html` (the hub) in any browser, or visit the GitHub Pages URL at `/mpsc/`. Click a subject card to open its checklist.

- **Tick / untick** any micro-topic. Progress saves automatically in your browser (`localStorage`) — no login, no server.
- **Stage tabs** (All / Prelims / Mains / Interview) filter topics by exam stage. Each topic shows colored badges: `PRE`, `MAINS`, `INT`, and `MH` (Maharashtra weightage).
- **Per-section, per-subject and per-stage completion %** update live. The hub shows aggregate progress per subject and overall.
- **Search**, expand/collapse all, and reset-progress controls are in each page's toolbar.

Progress is per-browser. Clearing browser data clears progress.

## Subjects

General Studies (Prelims + Mains): History & Indian Culture · Geography · Polity & Governance · Economy · Environment & Ecology · Science & Technology · Indian Society & Social Justice · International Relations · Internal Security · Ethics (GS-4).
Prelims: CSAT / Aptitude. Mains: Language Papers (Marathi + English) · Essay · Geography Optional (Papers 8 & 9). Cross-cutting: Current Affairs. State-specific: Maharashtra (Static GK). Final: Interview / Personality Test.

## Rebuild

Content lives in `mpsc_build/syllabus/<subject>.py`. The pages in `mpsc/` are generated — do not edit them by hand.

```bash
python3 -m mpsc_build.validate   # structure + coverage gates
python3 -m mpsc_build.generate   # regenerate mpsc/*.html
```

To add or edit topics, change the relevant `syllabus/*.py` module (keep each topic `id` stable so saved progress survives), then regenerate.
