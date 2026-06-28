# MPSC Rajyaseva Prep Platform — Design Spec

**Date:** 2026-06-29
**Owner:** faisal
**Status:** Approved design → ready for implementation plan

## 1. Purpose

A pure-HTML, offline-capable study tracker for the **MPSC Rajyaseva (Maharashtra State Services) Examination** — Prelims + Mains + Interview. The candidate ticks/unticks every micro-topic and watches completion percentages per section, per subject, and per exam stage. Hosted on GitHub Pages; progress persists in the browser (localStorage / Chrome storage). Medium of preparation: **English**.

Hard requirement from user: **cover the entire syllabus, miss nothing, maximum-depth micro-topics.**

## 2. Exam structure (researched — new descriptive pattern, 2025+ onward)

Sources: [Drishti MPSC Mains](https://www.drishtiias.com/state-pcs/mpsc-mains-syllabus), [Drishti MPSC Prelims](https://www.drishtiias.com/state-pcs/mpsc-prelims-syllabus), [MPSC official](https://mpsc.gov.in/examination_syllabus/18).

MPSC revised Rajyaseva Mains to mirror the UPSC pattern (effective 2025/2026):

- **Prelims** — Paper 1 General Studies (merit) + Paper 2 CSAT (qualifying, 33%).
- **Mains** — 9 descriptive papers, 1750 marks counted for merit:
  - Paper 1 Marathi (300, qualifying), Paper 2 English (300, qualifying)
  - Paper 3 Essay (250)
  - Paper 4 GS-1, Paper 5 GS-2, Paper 6 GS-3, Paper 7 GS-4 Ethics (250 each)
  - Papers 8 & 9 Optional subject — two papers (250 each)
- **Interview / Personality Test.**
- **Optional chosen by candidate: Geography.**

## 3. Design decisions (confirmed with user)

| Decision | Choice |
|----------|--------|
| File structure | New isolated `mpsc/` folder: own `index.html` hub + one HTML page per subject. Does not touch the existing Spring/Java site. |
| Topic organization | **By knowledge domain**, NOT by paper (avoids Prelims/Mains duplication). |
| Stage handling | Each micro-topic tagged `PRE` / `MAINS` / `INT` (multi-valued). Filter tabs (All/Prelims/Mains/Interview) + colored stage badge per topic + per-stage completion %. |
| Maharashtra weightage | Topics with Maharashtra-specific weightage carry an extra `MH` badge. |
| Granularity | **Maximum depth** — every official syllabus line exploded into smallest study-units (per amendment, per river system, per freedom-struggle event, etc.). Thousands of topics total. |
| Optional subject | **Geography** — full Paper-1 + Paper-2 micro-topic breakdown, on its own page, separate from the GS Geography page. |
| Storage | `localStorage` per page, key `mpsc_<subject>_v1`. Hub reads all keys for aggregate %. |
| Build method | Python generator script holding the full syllabus data structure, emitting each HTML page (mirrors existing `content/` + `_build` workflow). Guarantees coverage + consistency. |
| Theme | Reuse existing dark GitHub theme + checklist UI from current repo pages. |

## 4. Subject pages (16) — full syllabus coverage map

Each page = collapsible **sections** → **groups** → **micro-topics** (checkbox + index + stage badge(s) + optional MH badge).

1. **History & Indian Culture** — Ancient, Medieval, Modern (mid-18th c.→present), Post-Independence consolidation, World History (Industrial Revolution, World Wars, colonization/decolonization, political philosophies), Art Forms/Literature/Architecture, Bhakti movement & Maharashtra saints, Maharashtra history (Marathas, freedom struggle, social reformers). *Stages: PRE, MAINS.*
2. **Geography (GS)** — Physical (geomorphology, climatology, oceanography basics), Indian geography, World geography, Maharashtra geography (Western Ghats, rivers, climate), Human & Economic geography, Geophysical phenomena (earthquakes, tsunami, volcanoes, cyclones), resource distribution, industry location. *Stages: PRE, MAINS.*
3. **Polity & Governance** — Constitution (historical underpinnings, evolution, features, every major amendment, basic structure), Union–State relations & federalism, separation of powers, Parliament & State Legislatures, Executive, Judiciary, Local Self-Government (Panchayati Raj, urban), RPA, constitutional & statutory bodies, governance/transparency/RTI/e-governance, civil services role. *Stages: PRE, MAINS, INT.*
4. **Economy** — Indian economy & planning, resource mobilization, growth/development/employment, inclusive growth, government budgeting, agriculture (crops, cropping patterns, irrigation, MSP, PDS, food security, food processing), land reforms, liberalization, infrastructure (energy/ports/roads/rail/airports), banking & money, Maharashtra economy. *Stages: PRE, MAINS.*
5. **Environment & Ecology + Disaster Management** — Ecology/biodiversity, climate change, conservation, pollution, EIA, environmental institutions/conventions, disaster risk & resilience. *Stages: PRE, MAINS.*
6. **Science & Technology** — General science (physics/chemistry/biology basics), S&T applications & indigenization, space, computers/IT, robotics, nano-tech, biotech, IPR, defence technology. *Stages: PRE, MAINS.*
7. **Indian Society & Social Justice** — Society features & diversity, role of women & women's organizations, population & associated issues, poverty & developmental issues, urbanization, globalization effects, communalism/regionalism/secularism, welfare schemes (Centre + State) for vulnerable sections, health/education/HR, social-sector issues, NGOs/SHGs. *Stages: PRE, MAINS.*
8. **International Relations** — India & neighbourhood, bilateral/regional/global groupings & agreements, effect of developed/developing nations' policies, diaspora, international institutions (structure & mandate). *Stages: MAINS, INT.*
9. **Internal Security** — Extremism–development linkage, internal security challenges (state & non-state actors), communication networks/media/social-media role, cyber security, money laundering, border security, organized crime–terrorism nexus, security forces & agencies. *Stages: MAINS, INT.*
10. **Ethics, Integrity & Aptitude (GS-4)** — Ethics & human interface, human values, attitude, aptitude & civil-service foundational values, emotional intelligence, moral thinkers (Indian & world), public/civil-service ethics, probity in governance, RTI/transparency, case studies. *Stages: MAINS.*
11. **CSAT / Aptitude (Prelims Paper 2)** — Comprehension, interpersonal/communication skills, logical reasoning & analytical ability, decision-making & problem-solving, general mental ability, basic numeracy (Class X), data interpretation (charts/graphs/tables), Marathi & English language comprehension. *Stages: PRE.*
12. **Language Papers (Marathi + English, Mains qualifying)** — Comprehension, precis writing, usage & vocabulary, short essays, translation (Eng↔Marathi). Grammar sub-units for each language. *Stages: MAINS.*
13. **Essay** — Essay-writing technique, structure, common theme buckets (philosophical, social, economic, polity, environment, S&T, Maharashtra-specific), practice-topic bank. *Stages: MAINS.*
14. **Current Affairs** — Framework page: state/national/international events, government schemes tracker, reports & indices, persons in news, awards, sports, summits, Maharashtra current affairs. Organized as recurring trackable buckets (not dated items). *Stages: PRE, MAINS, INT.*
15. **Interview / Personality Test** — DAF self-prep, home district/Maharashtra deep-dive, hobbies/optional defence, current-affairs opinion bank, situational/ethical questions, body-language & mock-interview checklist. *Stages: INT.*
16. **Geography (Optional, Papers 8 & 9)** — Full optional depth: Paper-1 (Geomorphology, Climatology, Oceanography, Biogeography, Environmental Geography, Geographical Thought, Human Geography — economic/population/settlement/regional planning, models & theories) + Paper-2 (Geography of India — physical, resources, agriculture, industry, transport, settlements, regional development & planning, political geography, contemporary issues). *Stages: MAINS.*

## 5. Per-page UI

- **Sticky header**: subject title, home link, overall % bar, per-stage mini-% (PRE/MAINS/INT), total topic count, completed count.
- **Filter tabs**: All / Prelims / Mains / Interview — hides non-matching topics; percentages recompute to the active filter's denominator.
- **Toolbar**: search box (filter topics by text), expand-all, collapse-all, reset progress (with confirm).
- **Sections** (collapsible): section header shows its own progress bar + count; body groups micro-topics under sub-headings.
- **Micro-topic row**: checkbox (accent green when done) + tabular index + label (strikethrough + muted when done) + stage badge(s) + optional `MH` badge.
- Theme/colors identical to existing repo pages (CSS variables `--bg #0d1117` etc.).

## 6. Data model & storage

- Each page embeds its syllabus as a JS data structure: `sections[] → { name, stages[], groups[] → { name, topics[] → { id, text, stages[], mh? } } }`.
- Stable string `id` per topic (e.g. `hist-mod-1857-revolt`) so checkbox state survives content edits/reordering.
- `localStorage["mpsc_<subject>_v1"]` = JSON `{ [topicId]: true }`. Only checked items stored.
- Percentages computed live from data + stored set. Per-stage % filters topics whose `stages` include the active stage.
- Hub `index.html` iterates known subject keys, reads each localStorage value, renders aggregate % on each card + a global overall %.

## 7. Build / generator

- `mpsc_build/` (or reuse `_build/` convention) Python script(s):
  - `syllabus/` — one Python module or JSON per subject holding the full topic tree.
  - `generate.py` — renders `mpsc/index.html` + `mpsc/<subject>.html` from a shared HTML template + per-subject data.
- Running the generator is idempotent; re-runs only change generated HTML, never localStorage.
- Coverage guarantee: each official syllabus bullet maps to ≥1 section; generator prints a per-subject topic count so coverage is auditable.

## 8. Out of scope (YAGNI)

- No backend, no accounts, no cloud sync (Chrome localStorage only, per user).
- No cross-device sync (optional future: export/import JSON button — deferred).
- No timer/Pomodoro, no notes-per-topic, no spaced-repetition (can add later).
- Marathi-medium content (English medium confirmed).
- Other 25 optionals (only Geography built).

## 9. Success criteria

- All 16 pages live under `mpsc/` on GitHub Pages, dark-themed, mobile-responsive.
- Every official syllabus line represented by trackable micro-topics at maximum depth.
- Ticking a topic persists across reloads; per-section / per-subject / per-stage % update instantly.
- Hub shows live aggregate progress across all subjects.
- Stage filter tabs work on every subject page.
