# Daily Tutorial Phases — paste this whole block into a fresh Claude Code session

You are continuing the Learning hub tutorial-content build. Do **UP TO THREE phases** this run,
committing + pushing after **each** phase, then stop. The system is already built — you only add
Markdown content; the build turns it into pages. Gold-standard quality bar:
`content/webdev/0001-clientserver-model.md` — match its depth.

## Repeat the loop below up to THREE times (stop early if a run prints `NEXT PHASE: None`)

1. Show the next phase's topics (reads the manifest, resolves topics automatically):

   ```bash
   python3 -c "import json,sys; sys.path.insert(0,'_build'); import topics,generate; \
   m=json.load(open('content/_manifest.json')); np=m['next_phase']; print('NEXT PHASE:', np); \
   stem=(np or '').split('/')[0]; \
   proj=([p for p in generate.PROJECTS if topics.card_stem(p)==stem] or [None])[0]; \
   gis=[g for s in m['cards'][stem]['sections'] for ph in s['phases'] if ph['id']==np for g in ph['gis']] if np else []; \
   en={t['gi']:t for t in topics.enumerate_topics(proj)} if proj else {}; \
   [print(g,'|',en[g]['section'],'|',en[g]['slug'],'|',en[g]['text']) for g in gis]"
   ```

   If it prints `NEXT PHASE: None`, stop the loop (everything is done).
   Otherwise note the card `stem` and the `gi | section | slug | text` lines — those are this
   phase's topics (≤12).

2. For each topic, author `content/<stem>/<gi:04d>-<slug>.md` (e.g. `content/webdev/0013-....md`)
   with front-matter then the fixed 7 headings **in this exact order**:

   ```
   ---
   card: <stem>
   gi: <gi>
   slug: <slug>
   title: <topic text>
   ---

   ## 1. What it is
   ## 2. Why & when
   ## 3. Core concept
   ## 4. Diagram
   ## 5. Runnable example
   ## 6. Walkthrough
   ## 7. Gotchas & takeaways
   ```

   Requirements (the build lint enforces most of these):
   - Plain language, basics → advanced. Use a short analogy where it helps.
   - **Part 4** = a real inline `<svg ...>...</svg>` diagram (theme colours: accent `#6db33f`,
     blue `#79c0ff`, panel `#1c2430`, text `#e6edf3`, muted `#8b949e`) + a one-line caption.
   - **Part 5** = a complete, copy-paste-**runnable** example (Node, browser HTML, or `curl`/`bash`,
     **no installs**) in a fenced code block with a language tag, plus a "**How to run:**" line.
   - **Part 6** = step-by-step explanation referencing the actual lines.
   - **Part 7** = at least one `>` blockquote gotcha + a bullet list of takeaways.
   - No `TODO`/`TBD`/`FIXME`/`placeholder` text anywhere.

3. Build (also lints; fails loudly on any problem):
   ```bash
   python3 _build/generate.py
   ```
   Fix any reported lint error and re-run until it prints `tutorial pages:` with no
   `Tutorial lint failed`.

4. Tests + gate — both must pass; do NOT commit if either fails:
   ```bash
   python3 -m unittest discover -s _build/tests -p 'test_*.py' -v
   python3 _build/check_phase.py
   ```

5. Commit and push **this phase** before starting the next loop iteration:
   ```bash
   git add content tutorials *.html
   git commit -m "content: phase <id> — <N> tutorials

   Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
   git push
   ```

## After the loop (3 phases done, or `NEXT PHASE: None`)

Reply with: each phase id you completed and its page count, the final `next_phase`, and a
reminder to hard-refresh (Cmd+Shift+R) on the Pages site.

## Rules

- Up to **THREE phases** per run, no more. Commit + push after **each** phase so progress is saved
  even if you run out of context mid-run.
- **Never reorder or delete** existing topics in `_build/data_*.py` — it shifts every `gi` and
  breaks all existing tutorial links. Append-only.
- Quality over speed: each page must stand on its own as a genuinely useful tutorial.
- The pilot card **webdev** finishes first (the manifest points there until every webdev topic is
  done), then the loop auto-rolls through every other card (microservices, genai, spring
  boot/framework, and the rest).
