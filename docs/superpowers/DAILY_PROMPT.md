# Daily Tutorial Phase — paste this whole block into a fresh Claude Code session

You are continuing the Learning hub tutorial-content build. Do **ONE phase only**, then stop.
The system is already built; you are just adding content. Spec + plan live in `docs/superpowers/`.
The gold-standard quality bar is `content/webdev/0001-clientserver-model.md` — match its depth.

## Steps

1. Show the next phase's topics by running this (it reads the manifest and resolves topics automatically):

   ```bash
   python3 -c "import json,sys; sys.path.insert(0,'_build'); import topics,generate; \
   m=json.load(open('content/_manifest.json')); np=m['next_phase']; \
   print('NEXT PHASE:', np); \
   stem=np.split('/')[0]; \
   proj=[p for p in generate.PROJECTS if topics.card_stem(p)==stem][0]; \
   gis=[g for s in m['cards'][stem]['sections'] for ph in s['phases'] if ph['id']==np for g in ph['gis']]; \
   en={t['gi']:t for t in topics.enumerate_topics(proj)}; \
   [print(g,'|',en[g]['section'],'|',en[g]['slug'],'|',en[g]['text']) for g in gis]"
   ```

   If it prints `NEXT PHASE: None`, reply "All phases complete." and stop.
   Otherwise note the card `stem`, and the `gi | section | slug | text` lines — those are this phase's topics (≤12).

2. For each topic, author `content/<stem>/<gi:04d>-<slug>.md` (e.g. `content/webdev/0013-....md`),
   following the fixed 7-part template **in this exact heading order**:

   ```
   ## 1. What it is
   ## 2. Why & when
   ## 3. Core concept
   ## 4. Diagram
   ## 5. Runnable example
   ## 6. Walkthrough
   ## 7. Gotchas & takeaways
   ```

   Front-matter at the top of every file:
   ```
   ---
   card: <stem>
   gi: <gi>
   slug: <slug>
   title: <topic text>
   ---
   ```

   Requirements per page (the build lint enforces most of these):
   - Plain language, basics → advanced. Use a short analogy where it helps.
   - **Part 4** has a real inline `<svg ...>...</svg>` diagram (use theme colours
     `#6db33f` accent, `#79c0ff` blue, `#1c2430` panel, `#e6edf3` text, `#8b949e` muted) plus a one-line caption.
   - **Part 5** has a complete, copy-paste-**runnable** example in a fenced code block with a
     language tag, plus a "**How to run:**" line. Prefer Node, browser HTML, or `curl`/`bash` so it runs with no install.
   - **Part 6** explains the example specifically, step by step (reference the actual lines).
   - **Part 7** has at least one `>` blockquote gotcha and a bullet list of takeaways.
   - No `TODO`/`TBD`/`FIXME`/`placeholder` text anywhere.

3. Build (this also lints every page and fails loudly on any problem):
   ```bash
   python3 _build/generate.py
   ```
   Fix any reported lint error and re-run until it prints the new `tutorial pages:` count
   with **no** "Tutorial lint failed" message.

4. Run the test suite — all must pass:
   ```bash
   python3 -m unittest discover -s _build/tests -p 'test_*.py' -v
   ```
   Then the phase gate — must print `CHECK PASS` (exit 0). Do NOT commit if it fails:
   ```bash
   python3 _build/check_phase.py
   ```

5. Verify the phase landed:
   - The generator's printed `next_phase` advanced past the phase you just built.
   - The card file (e.g. `webdev.html`) now links your new `gi`s — check:
     ```bash
     grep -c 'tutorials/<stem>/' <stem>.html
     ```

6. Commit and push:
   ```bash
   git add content tutorials *.html
   git commit -m "content: phase <id> — <N> tutorials

   Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
   git push
   ```

7. Reply with: the phase id you completed, how many pages built, the new `next_phase`,
   and a reminder to hard-refresh (Cmd+Shift+R) on the Pages site to bust the browser cache.

## Rules

- Exactly **ONE phase** per run. Do not run ahead into the next phase.
- **Never reorder or delete** existing topics in `_build/data_*.py` — that would shift every
  `gi` and break all existing tutorial links. Append-only.
- Quality over speed: each page must stand on its own as a genuinely useful tutorial.
- The pilot card is **webdev**; it is finished first (the manifest points `next_phase` there
  until every webdev topic is done), then the build rolls through the other cards automatically.
