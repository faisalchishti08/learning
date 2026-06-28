# MPSC Per-Topic Learning Content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the pipeline + viewer + quality gates so every MPSC micro-topic can have a comprehensive, exam-complete learning page that opens when the topic is clicked — and seed a few example topics proving it end-to-end.

**Architecture:** Per-topic Markdown content (`mpsc_build/content/<subject>/<id>.md`) → vendored zero-dep `mdlite` converter → `render_topic_page` emits standalone `mpsc/topics/<id>.html`; checklist labels with content become `📖` links. `validate_content.py` lints content; `content_status.py` lists remaining topics for the resumable generation loop.

**Tech Stack:** Python 3.9 stdlib only, vanilla HTML/CSS, GitHub Pages.

## Global Constraints

- Build tooling under `mpsc_build/`; site output under `mpsc/`. Do NOT touch the Spring/Java site.
- Python stdlib only (target 3.9). No pip installs. `mdlite` is vendored.
- Content file path: `mpsc_build/content/<subject_key>/<topic_id>.md` where ids are the existing stable topic ids.
- Content template = exactly 8 `##` sections, in order: `Overview`, `In-Depth`, `Maharashtra Connection`, `Key Facts`, `Memory Aids`, `Exam Traps`, `Questions`, `Linkages`.
- Topic page path: `mpsc/topics/<topic_id>.html`. Checklist links use `target="_blank"`.
- Theme variables identical to existing pages (`--bg:#0d1117` … `--accent:#6db33f`).
- "Done" = the `.md` file exists. Generation is resumable; missing-content topics degrade to plain labels.
- Deploy: commit to Learning `main`, `git subtree split --prefix=mpsc -b <tmp>`, push `<tmp>:main` to `git@github.com:faisalchishti08/mpsc.git`.

---

## File Structure

```
mpsc_build/
  mdlite.py            # NEW: markdown -> html (zero-dep)
  template.py          # MODIFY: add render_topic_page(); link labels with content in render_page()
  generate.py          # MODIFY: load content/, render topic pages, pass content-id set to render_page
  validate_content.py  # NEW: content-lint gate
  content_status.py    # NEW: list next missing topics in priority order
  content/
    <subject>/<id>.md  # content source (seeded here, mass-filled by the loop)
mpsc/
  topics/<id>.html     # NEW: generated per-topic pages
tests/
  test_mdlite.py       # NEW: stdlib assert tests for mdlite
```

---

### Task 1: `mdlite.py` — zero-dependency Markdown → HTML

**Files:**
- Create: `mpsc_build/mdlite.py`
- Create: `tests/test_mdlite.py`

**Interfaces:**
- Produces: `mpsc_build.mdlite.render(md: str) -> str` (returns an HTML fragment string)

- [ ] **Step 1: Write the failing test — `tests/test_mdlite.py`**

```python
"""Run: python3 tests/test_mdlite.py  (exits non-zero on failure)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mpsc_build.mdlite import render

def check(name, got, must_contain):
    for m in must_contain:
        if m not in got:
            print(f"FAIL {name}: missing {m!r} in {got!r}"); sys.exit(1)
    print("ok", name)

check("h2", render("## Overview"), ["<h2>Overview</h2>"])
check("h3", render("### Sub"), ["<h3>Sub</h3>"])
check("para", render("Hello world."), ["<p>Hello world.</p>"])
check("bold", render("a **b** c"), ["<strong>b</strong>"])
check("italic", render("a *b* c"), ["<em>b</em>"])
check("code", render("use `x` here"), ["<code>x</code>"])
check("ul", render("- one\n- two"), ["<ul>", "<li>one</li>", "<li>two</li>", "</ul>"])
check("ol", render("1. one\n2. two"), ["<ol>", "<li>one</li>", "</ol>"])
check("link", render("[g](http://x)"), ['<a href="http://x">g</a>'])
check("hr", render("---"), ["<hr>"])
check("blockquote", render("> note"), ["<blockquote>note</blockquote>"])
check("rawhtml", render("<table><tr><td>x</td></tr></table>"), ["<table><tr><td>x</td></tr></table>"])
check("escape", render("a < b & c"), ["a &lt; b &amp; c"])
print("ALL MDLITE TESTS PASSED")
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /Users/faisalchishti/Desktop/claude-projects/Learning && python3 tests/test_mdlite.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mpsc_build.mdlite'`.

- [ ] **Step 3: Implement `mpsc_build/mdlite.py`**

```python
"""Minimal, deterministic Markdown -> HTML. Zero dependencies. Subset suited to
MPSC content: headings, lists, bold/italic/code, links, hr, blockquote,
paragraphs, and raw-HTML block passthrough (lines starting with '<')."""
import re
import html as _html

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITAL = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_CODE = re.compile(r"`([^`]+?)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

def _inline(text):
    # text is already HTML-escaped; apply inline markup
    text = _CODE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = _ITAL.sub(lambda m: f"<em>{m.group(1)}</em>", text)
    text = _LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    return text

def render(md):
    lines = md.replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    n = len(lines)
    para = []

    def flush_para():
        if para:
            out.append("<p>" + _inline(_html.escape(" ".join(para))) + "</p>")
            para.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped == "":
            flush_para(); i += 1; continue

        # raw HTML passthrough (tables etc.)
        if stripped.startswith("<"):
            flush_para(); out.append(stripped); i += 1; continue

        if stripped == "---":
            flush_para(); out.append("<hr>"); i += 1; continue

        m = re.match(r"(#{1,4})\s+(.*)", stripped)
        if m:
            flush_para()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>" + _inline(_html.escape(m.group(2))) + f"</h{lvl}>")
            i += 1; continue

        if stripped.startswith(">"):
            flush_para()
            out.append("<blockquote>" + _inline(_html.escape(stripped[1:].strip())) + "</blockquote>")
            i += 1; continue

        # unordered list
        if re.match(r"[-*]\s+", stripped):
            flush_para(); out.append("<ul>")
            while i < n and re.match(r"[-*]\s+", lines[i].strip()):
                item = re.sub(r"^[-*]\s+", "", lines[i].strip())
                out.append("<li>" + _inline(_html.escape(item)) + "</li>")
                i += 1
            out.append("</ul>"); continue

        # ordered list
        if re.match(r"\d+\.\s+", stripped):
            flush_para(); out.append("<ol>")
            while i < n and re.match(r"\d+\.\s+", lines[i].strip()):
                item = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                out.append("<li>" + _inline(_html.escape(item)) + "</li>")
                i += 1
            out.append("</ol>"); continue

        para.append(stripped); i += 1

    flush_para()
    return "\n".join(out)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python3 tests/test_mdlite.py`
Expected: ends with `ALL MDLITE TESTS PASSED`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add mpsc_build/mdlite.py tests/test_mdlite.py
git commit -m "feat: vendored mdlite markdown converter"
```

---

### Task 2: Topic page rendering + checklist links

**Files:**
- Modify: `mpsc_build/template.py` (add `render_topic_page`; update `render_page` signature + label rendering)
- Modify: `mpsc_build/generate.py` (load content, render topic pages, pass content-id set)

**Interfaces:**
- Consumes: `mpsc_build.mdlite.render`
- Produces: `mpsc_build.template.render_topic_page(subject: dict, topic: dict, content_html: str) -> str`
- Produces: updated `render_page(subject: dict, content_ids: set[str] = frozenset()) -> str`

- [ ] **Step 1: Add `render_topic_page` to `mpsc_build/template.py`** (append near `render_page`)

```python
TOPIC_CSS = CSS + """
.content{max-width:820px;margin:0 auto;padding:8px 20px 60px}
.content h2{font-size:20px;margin:26px 0 8px;color:var(--accent);border-bottom:1px solid var(--border);padding-bottom:5px}
.content h3{font-size:16px;margin:18px 0 6px}
.content p{margin:8px 0}
.content ul,.content ol{margin:8px 0 8px 4px;padding-left:22px}
.content li{margin:4px 0}
.content code{background:var(--bar-bg);padding:1px 5px;border-radius:5px;color:#79c0ff;font-size:13px}
.content blockquote{border-left:3px solid var(--accent);margin:10px 0;padding:4px 14px;color:var(--muted)}
.content table{border-collapse:collapse;margin:12px 0;width:100%;font-size:14px}
.content th,.content td{border:1px solid var(--border);padding:6px 10px;text-align:left}
.content th{background:var(--panel2)}
.content hr{border:none;border-top:1px solid var(--border);margin:18px 0}
.crumb{font-size:13px;color:var(--muted);text-decoration:none;border:1px solid var(--border);padding:5px 10px;border-radius:8px}
.crumb:hover{border-color:var(--accent);color:var(--text)}
.disclaimer{margin-top:30px;padding:12px 16px;background:var(--panel);border:1px solid var(--border);border-radius:10px;color:var(--muted);font-size:12.5px}
"""

def render_topic_page(subject, topic, content_html):
    badges = "".join(f'<span class="badge b-{s}">{s}</span>' for s in topic["stages"])
    if topic.get("mh"):
        badges += '<span class="badge b-MH">MH</span>'
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{topic['text']} — MPSC</title><style>{TOPIC_CSS}</style></head><body>
<header><div class="title"><a class="crumb" href="../{subject['key']}.html">← {subject['title']}</a>
<div class="logo">{subject['icon']}</div></div>
<h1 style="font-size:21px;margin:10px 0 4px">{topic['text']} {badges}</h1></header>
<main class="content">{content_html}
<div class="disclaimer">Study notes generated for MPSC preparation. Cross-check current schemes,
latest data and exact dates before the exam.</div></main></body></html>"""
```

- [ ] **Step 2: Update `render_page` to link topics that have content**

In `mpsc_build/template.py`, change the signature and the per-topic `<li>` build.

Replace the signature line:
```python
def render_page(subject):
```
with:
```python
def render_page(subject, content_ids=frozenset()):
```

Replace the label-building block inside the topic loop:
```python
            for t in g["topics"]:
                st = ",".join(t["stages"])
                items.append(
                    f'<li class="topic" data-stages="{st}"><input type="checkbox" '
                    f'data-id="{t["id"]}"><label>{t["text"]}{_badges(t)}</label></li>'
                )
```
with:
```python
            for t in g["topics"]:
                st = ",".join(t["stages"])
                if t["id"] in content_ids:
                    label = (f'<label><a class="tlink" target="_blank" '
                             f'href="topics/{t["id"]}.html">{t["text"]}</a> '
                             f'<span class="pin" title="Study notes available">📖</span>{_badges(t)}</label>')
                else:
                    label = f'<label>{t["text"]}{_badges(t)}</label>'
                items.append(
                    f'<li class="topic" data-stages="{st}"><input type="checkbox" '
                    f'data-id="{t["id"]}">{label}</li>'
                )
```

(The existing CSS already defines `.tlink` and `.pin`; reuse them.)

- [ ] **Step 3: Update `mpsc_build/generate.py` to build topic pages**

Replace the whole file with:
```python
"""Generate mpsc/ HTML from syllabus + per-topic content. Run: python3 -m mpsc_build.generate"""
import os
from mpsc_build.syllabus import load_all
from mpsc_build.template import render_page, render_hub, render_topic_page
from mpsc_build.mdlite import render as md_render

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "mpsc")
CONTENT = os.path.join(ROOT, "mpsc_build", "content")


def _topic_index(subjects):
    idx = {}
    for s in subjects:
        for sec in s["sections"]:
            for g in sec["groups"]:
                for t in g["topics"]:
                    idx[t["id"]] = (s, t)
    return idx


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, "topics"), exist_ok=True)
    subjects = load_all()
    idx = _topic_index(subjects)

    # which topics have content
    content_ids = set()
    n_pages = 0
    for sub in subjects:
        d = os.path.join(CONTENT, sub["key"])
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".md"):
                continue
            tid = fn[:-3]
            if tid not in idx:
                continue  # orphan; validate_content will flag
            content_ids.add(tid)
            s, t = idx[tid]
            md = open(os.path.join(d, fn), encoding="utf-8").read()
            html = render_topic_page(s, t, md_render(md))
            with open(os.path.join(OUT, "topics", tid + ".html"), "w", encoding="utf-8") as f:
                f.write(html)
            n_pages += 1

    for s in subjects:
        with open(os.path.join(OUT, s["key"] + ".html"), "w", encoding="utf-8") as f:
            f.write(render_page(s, content_ids))
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_hub(subjects))
    print(f"generated {len(subjects)} subject pages + hub + {n_pages} topic pages")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Verify build still works (no content yet → 0 topic pages)**

Run: `cd /Users/faisalchishti/Desktop/claude-projects/Learning && python3 -m mpsc_build.validate && python3 -m mpsc_build.generate`
Expected: `OK: all syllabus data valid` then `generated 17 subject pages + hub + 0 topic pages`.

- [ ] **Step 5: Commit**

```bash
git add mpsc_build/template.py mpsc_build/generate.py mpsc
git commit -m "feat: per-topic page rendering + content-aware checklist links"
```

---

### Task 3: Content-lint gate + status lister

**Files:**
- Create: `mpsc_build/validate_content.py`
- Create: `mpsc_build/content_status.py`

**Interfaces:**
- Produces: `mpsc_build.validate_content.validate_content() -> list[str]`
- Produces: `mpsc_build.content_status` CLI printing next missing topics in priority order

- [ ] **Step 1: Write `mpsc_build/validate_content.py`**

```python
"""Content-lint gate. Run: python3 -m mpsc_build.validate_content"""
import os, re, sys
from mpsc_build.syllabus import load_all

ROOT = os.path.join(os.path.dirname(__file__), "..")
CONTENT = os.path.join(ROOT, "mpsc_build", "content")
SECTIONS = ["Overview", "In-Depth", "Maharashtra Connection", "Key Facts",
            "Memory Aids", "Exam Traps", "Questions", "Linkages"]

def _all_ids():
    ids = set()
    for s in load_all():
        for sec in s["sections"]:
            for g in sec["groups"]:
                for t in g["topics"]:
                    ids.add(t["id"])
    return ids

def validate_content():
    errors = []
    ids = _all_ids()
    for sub in (load_all()):
        d = os.path.join(CONTENT, sub["key"])
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".md"):
                continue
            tid = fn[:-3]
            path = os.path.join(d, fn)
            md = open(path, encoding="utf-8").read()
            if tid not in ids:
                errors.append(f"orphan content (no such topic id): {sub['key']}/{fn}")
            headers = re.findall(r"^##\s+(.+)$", md, re.M)
            for want in SECTIONS:
                if want not in headers:
                    errors.append(f"{sub['key']}/{fn}: missing section '## {want}'")
            words = len(re.findall(r"\w+", md))
            if words < 350:
                errors.append(f"{sub['key']}/{fn}: only {words} words (need >= 350)")
            qblock = md.split("## Questions", 1)[-1]
            prelims = len(re.findall(r"\[(Asked|Expected)\]", qblock.split("Mains", 1)[0]))
            mains = len(re.findall(r"\[(Asked|Expected)\]", qblock.split("Mains", 1)[-1])) if "Mains" in qblock else 0
            if prelims < 3:
                errors.append(f"{sub['key']}/{fn}: < 3 Prelims questions")
            if mains < 2:
                errors.append(f"{sub['key']}/{fn}: < 2 Mains questions")
    return errors

def main():
    errs = validate_content()
    if errs:
        print(f"CONTENT FAIL: {len(errs)} error(s)")
        for e in errs[:80]:
            print("  -", e)
        sys.exit(1)
    print("OK: all content valid")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write `mpsc_build/content_status.py`**

```python
"""List generation progress + next missing topics in priority order.
Run: python3 -m mpsc_build.content_status [N]   (N = how many missing to list, default 30)"""
import os, sys
from mpsc_build.syllabus import load_all

ROOT = os.path.join(os.path.dirname(__file__), "..")
CONTENT = os.path.join(ROOT, "mpsc_build", "content")

PRIORITY = ["maharashtra", "history", "polity", "geography", "economy",
            "environment", "society", "science_tech", "current_affairs",
            "international_relations", "internal_security", "ethics", "csat",
            "geography_optional", "essay", "language", "interview"]

def _subjects_by_priority():
    subs = {s["key"]: s for s in load_all()}
    ordered = [subs[k] for k in PRIORITY if k in subs]
    ordered += [s for s in subs.values() if s["key"] not in PRIORITY]
    return ordered

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    total = done = 0
    missing = []
    for s in _subjects_by_priority():
        d = os.path.join(CONTENT, s["key"])
        have = set(f[:-3] for f in os.listdir(d)) if os.path.isdir(d) else set()
        for sec in s["sections"]:
            for g in sec["groups"]:
                for t in g["topics"]:
                    total += 1
                    if t["id"] in have:
                        done += 1
                    else:
                        missing.append((s["key"], t["id"], t["text"], ",".join(t["stages"]), bool(t.get("mh"))))
    print(f"PROGRESS: {done}/{total} topics have content ({round(done/total*100)}%)")
    print(f"NEXT {min(n, len(missing))} MISSING (priority order):")
    for key, tid, text, stages, mh in missing[:n]:
        print(f"  {key} | {tid} | [{stages}{'/MH' if mh else ''}] | {text}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run both (no content yet)**

Run: `python3 -m mpsc_build.validate_content && python3 -m mpsc_build.content_status 5`
Expected: `OK: all content valid`, then `PROGRESS: 0/1711 topics have content (0%)` and 5 maharashtra topics listed.

- [ ] **Step 4: Commit**

```bash
git add mpsc_build/validate_content.py mpsc_build/content_status.py
git commit -m "feat: content-lint gate + generation status lister"
```

---

### Task 4: Seed example topics + deploy proof

**Files:**
- Create: `mpsc_build/content/maharashtra/mh-pr-formation.md`
- Create: `mpsc_build/content/history/hist-mar-shivaji.md`
- Create: `mpsc_build/content/polity/pol-cf-preamble.md`

**Interfaces:**
- Consumes: all of Tasks 1–3.

- [ ] **Step 1: Write 3 seed content files** following the §4 template (the engineer writes full comprehensive content for each — Formation of Maharashtra, Shivaji Maharaj, Preamble — each ≥350 words, all 8 sections, ≥3 Prelims + ≥2 Mains questions with `[Asked]`/`[Expected]` labels). Example skeleton for `mh-pr-formation.md`:

```markdown
## Overview
Formation of Maharashtra on 1 May 1960 ... why it matters for MPSC.

## In-Depth
### Background — States Reorganisation
...full exam-rich detail with dates, the Samyukta Maharashtra movement, ...

## Maharashtra Connection
Core Maharashtra topic — ...

## Key Facts
- 1 May 1960 — Maharashtra state formed
- 105 martyrs (Hutatma) of the Samyukta Maharashtra movement
- ...

## Memory Aids
"1960 — Bombay split into Maharashtra + Gujarat" ...

## Exam Traps
Do not confuse Mahagujarat movement with Samyukta Maharashtra ...

## Questions
**Prelims (MCQ-style):**
1. [Asked] In which year was the state of Maharashtra formed? — *1960*
2. [Expected] The Samyukta Maharashtra movement was associated with which city's status? — *Bombay/Mumbai*
3. [Expected] How many martyrs are commemorated at Hutatma Chowk? — *105*

**Mains (descriptive):**
1. [Expected] Discuss the significance of the Samyukta Maharashtra movement in shaping the linguistic state.
2. [Expected] Examine the role of the States Reorganisation Commission in the creation of Maharashtra.

## Linkages
- hist-mhm-samyukta (Samyukta Maharashtra movement)
- pol-cf-reorg (Reorganization of states)
```

- [ ] **Step 2: Build + validate + content-lint**

Run: `python3 -m mpsc_build.validate && python3 -m mpsc_build.validate_content && python3 -m mpsc_build.generate`
Expected: both validators OK; `generated 17 subject pages + hub + 3 topic pages`.

- [ ] **Step 3: Verify locally (static checks — sandbox blocks http server)**

Run:
```bash
python3 - <<'EOF'
import os, glob
pages = glob.glob('mpsc/topics/*.html')
assert len(pages) == 3, pages
for p in pages:
    h = open(p).read()
    assert '<h2>Overview</h2>' in h and '<h2>Questions</h2>' in h, p
    assert 'class="crumb"' in h, p
# subject page links the seeded topic
hist = open('mpsc/history.html').read()
assert 'href="topics/hist-mar-shivaji.html"' in hist and '📖' in hist
print("OK seed topic pages + links")
EOF
```
Expected: `OK seed topic pages + links`.

- [ ] **Step 4: Commit + deploy**

```bash
git add mpsc_build/content mpsc
git commit -m "content: seed 3 example topic learning pages"
# deploy
git subtree split --prefix=mpsc -b mpsc-dep && \
  git push git@github.com:faisalchishti08/mpsc.git mpsc-dep:main && \
  git branch -D mpsc-dep
```

- [ ] **Step 5: Verify live**

After Pages rebuilds, confirm `https://faisalchishti08.github.io/mpsc/topics/mh-pr-formation.html` loads and `https://faisalchishti08.github.io/mpsc/maharashtra.html` shows the 📖 link on the Formation topic.

---

## Generation Loop (driven by separate Sonnet prompt — NOT a code task)

Once Tasks 1–4 are live, mass content is produced by repeatedly running the content-factory prompt in fresh Sonnet sessions. Each run:
1. `python3 -m mpsc_build.content_status 40` → next missing topics (priority order).
2. For each, sequentially, write `mpsc_build/content/<subject>/<id>.md` to the §4 template at comprehensive depth (model knowledge; brief web check only for volatile facts).
3. After a subject completes (or every ~25 files): `validate` + `validate_content` + `generate`, commit, deploy subtree.
4. Stop cleanly when context fills; report remaining counts. Next session resumes via `content_status`.

The runnable prompt is delivered separately and saved to `mpsc_build/CONTENT_PROMPT.md`.

---

## Self-Review

**Spec coverage:** §3 source format → Task 4 + loop. §4 template → enforced by Task 3 lint + used in Task 4. §5 pipeline (mdlite, render_topic_page, generate, checklist link) → Tasks 1–2. §6 quality gate → Task 3 `validate_content`. §7 loop/resumable (`content_status`, file-presence done) → Task 3 + loop section. §8 deploy → Task 4 Step 4. §9 out-of-scope respected. §10 success criteria → Task 4 verification. No gaps.

**Placeholder scan:** all code complete and runnable; Task 4 Step 1 requires the engineer to author real content (that IS the deliverable, bounded by the lint gate — not a placeholder in the code sense). No TODO/TBD in code.

**Type consistency:** `render(md)`, `render_topic_page(subject, topic, content_html)`, `render_page(subject, content_ids)`, `validate_content()`, content path `content/<key>/<id>.md`, 8 section names, `mpsc/topics/<id>.html` — consistent across Tasks 1–4 and the generate/lint/status modules.
