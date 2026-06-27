# Tutorial Content Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tutorial-content layer so every checklist micro-topic links to a self-contained, in-depth, runnable tutorial page, generated incrementally one bounded phase at a time via a re-runnable daily driver.

**Architecture:** Topics keep their existing per-card 1-based index `gi` as a stable ID. Each topic's tutorial is authored as a Markdown file under `content/<card>/`, converted at build time by a zero-dependency Python Markdown subset converter, wrapped in a themed self-contained page shell, and emitted to `tutorials/<card>/<NNNN>-<slug>.html`. `generate.py` builds the pages, lints them, computes prev/next, injects a link-map so only built topics become clickable in the checklist, and writes a manifest that drives phased generation.

**Tech Stack:** Python 3.9 (stdlib only — no pip installs), `unittest` for tests, static HTML/CSS/JS (no runtime deps), localStorage for progress.

## Global Constraints

- Python **3.9** compatible — no walrus-in-f-string backslashes, no 3.10+ syntax. Stdlib only; **no pip installs**.
- Tests use **`unittest`** (pytest is not installed). Run with `python3 -m unittest discover -s _build/tests -p 'test_*.py' -v`.
- Generated pages must be **fully self-contained** (all CSS/JS inline, no external URLs) and theme-matched to existing files (`--bg:#0d1117; --accent:#6db33f;` dark theme).
- **Append-only:** never reorder or delete existing topics in `_build/data_*.py` (would shift `gi` and break links).
- Tutorial filename format: `tutorials/<card>/<gi:04d>-<slug>.html`. Storage key reused from checklist: `spring-checklist:<card>.html`; topic checkbox ID: `t<gi>`.
- The 7 required tutorial headings, exact text and order: `1. What it is`, `2. Why & when`, `3. Core concept`, `4. Diagram`, `5. Runnable example`, `6. Walkthrough`, `7. Gotchas & takeaways`.
- Commit message footer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Run all build commands and tests with `python3` from the repo root `/Users/faisalchishti/Desktop/claude-projects/Learning`.

---

### Task 1: Topic identity utilities (`_build/topics.py`)

**Files:**
- Create: `_build/topics.py`
- Create: `_build/tests/test_topics.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `slugify(text: str) -> str` — html-stripped, ascii kebab-case, max 60 chars, never empty.
  - `enumerate_topics(project: dict) -> list[dict]` — yields `{"gi":int,"section":str,"tag":str,"group":str,"text":str,"slug":str}` in checklist order; `gi` is 1-based per card matching `shell.py`.
  - `card_stem(project: dict) -> str` — `project["file"]` without `.html`.
  - `page_path(stem: str, gi: int, slug: str) -> str` — `"tutorials/<stem>/<gi:04d>-<slug>.html"`.

- [ ] **Step 1: Write the failing test**

Create `_build/tests/test_topics.py`:
```python
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import topics

PROJ = {
    "file": "webdev.html",
    "sections": [
        {"name": "HTML", "tag": "html", "groups": [
            {"g": "Basics", "items": ["The <!DOCTYPE> declaration", "Semantic elements"]}]},
        {"name": "CSS", "tag": "css", "groups": [
            {"g": "Layout", "items": ["Flexbox: justify-content"]}]},
    ],
}

class TestTopics(unittest.TestCase):
    def test_slugify_basic(self):
        self.assertEqual(topics.slugify("Semantic elements"), "semantic-elements")

    def test_slugify_strips_html_and_symbols(self):
        self.assertEqual(topics.slugify("The <!DOCTYPE> declaration"), "the-doctype-declaration")

    def test_slugify_never_empty(self):
        self.assertEqual(topics.slugify("<<>>"), "topic")

    def test_enumerate_gi_is_sequential_per_card(self):
        ts = topics.enumerate_topics(PROJ)
        self.assertEqual([t["gi"] for t in ts], [1, 2, 3])
        self.assertEqual(ts[2]["section"], "CSS")
        self.assertEqual(ts[2]["slug"], "flexbox-justify-content")

    def test_card_stem(self):
        self.assertEqual(topics.card_stem(PROJ), "webdev")

    def test_page_path_zero_pads(self):
        self.assertEqual(topics.page_path("webdev", 7, "semantic-elements"),
                         "tutorials/webdev/0007-semantic-elements.html")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s _build/tests -p 'test_topics.py' -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'topics'`.

- [ ] **Step 3: Write minimal implementation**

Create `_build/topics.py`:
```python
# -*- coding: utf-8 -*-
"""Stable topic identity helpers: gi enumeration, slugs, page paths."""
import re
import unicodedata


def slugify(text):
    s = re.sub(r"<[^>]+>", "", text)                      # strip any HTML tags
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    s = s[:60].strip("-")
    return s or "topic"


def enumerate_topics(project):
    out = []
    gi = 0
    for sec in project["sections"]:
        for grp in sec["groups"]:
            for text in grp["items"]:
                gi += 1
                out.append({
                    "gi": gi,
                    "section": sec["name"],
                    "tag": sec.get("tag", ""),
                    "group": grp["g"],
                    "text": text,
                    "slug": slugify(text),
                })
    return out


def card_stem(project):
    return project["file"].replace(".html", "")


def page_path(stem, gi, slug):
    return "tutorials/%s/%04d-%s.html" % (stem, gi, slug)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s _build/tests -p 'test_topics.py' -v`
Expected: PASS (6 tests OK).

- [ ] **Step 5: Commit**

```bash
git add _build/topics.py _build/tests/test_topics.py
git commit -m "feat: topic identity helpers (slug, gi enumeration, page path)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Markdown converter (`_build/md.py`)

**Files:**
- Create: `_build/md.py`
- Create: `_build/tests/test_md.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `convert(md: str) -> str` — HTML string. Supports headings, paragraphs, **bold**, _italic_, `inline code`, fenced code (escaped, with `lang-<x>` class), ordered/unordered lists, pipe tables, blockquotes, links, and raw block-HTML passthrough (`<svg>`, `<div>`, `<table>`, `<figure>`, `<pre>`, `<details>`, `<section>`, `<aside>`).

- [ ] **Step 1: Write the failing test**

Create `_build/tests/test_md.py`:
```python
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import md

class TestMd(unittest.TestCase):
    def test_heading(self):
        self.assertIn("<h2>Hello</h2>", md.convert("## Hello"))

    def test_paragraph_inline(self):
        out = md.convert("This is **bold** and `code` and _em_.")
        self.assertIn("<strong>bold</strong>", out)
        self.assertIn("<code>code</code>", out)
        self.assertIn("<em>em</em>", out)

    def test_fenced_code_is_escaped_and_tagged(self):
        out = md.convert("```js\nconst x = a < b && c > d;\n```")
        self.assertIn('<pre><code class="lang-js">', out)
        self.assertIn("a &lt; b &amp;&amp; c &gt; d", out)

    def test_inline_code_not_formatted_inside(self):
        out = md.convert("use `a**b**c` here")
        self.assertIn("<code>a**b**c</code>", out)

    def test_unordered_list(self):
        out = md.convert("- one\n- two")
        self.assertIn("<ul><li>one</li><li>two</li></ul>", out)

    def test_ordered_list(self):
        out = md.convert("1. first\n2. second")
        self.assertIn("<ol><li>first</li><li>second</li></ol>", out)

    def test_table(self):
        out = md.convert("| A | B |\n|---|---|\n| 1 | 2 |")
        self.assertIn("<table>", out)
        self.assertIn("<th>A</th>", out)
        self.assertIn("<td>1</td>", out)

    def test_blockquote(self):
        self.assertIn("<blockquote>note here</blockquote>", md.convert("> note here"))

    def test_link(self):
        self.assertIn('<a href="http://x.com">x</a>', md.convert("see [x](http://x.com)"))

    def test_raw_svg_passthrough(self):
        src = '<svg viewBox="0 0 10 10"><rect x="1" y="1"/></svg>'
        self.assertIn(src, md.convert(src))

    def test_multiline_svg_passthrough(self):
        src = '<svg>\n<rect/>\n</svg>'
        self.assertIn("<rect/>", md.convert(src))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s _build/tests -p 'test_md.py' -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'md'`.

- [ ] **Step 3: Write minimal implementation**

Create `_build/md.py`:
```python
# -*- coding: utf-8 -*-
"""Zero-dependency Markdown subset -> HTML, for tutorial pages (build-time only)."""
import re
import html

_BLOCK_HTML = re.compile(r"^<(svg|div|table|figure|pre|details|section|aside)\b", re.I)
NL = chr(10)


def _inline(text):
    codes = []

    def stash(m):
        codes.append(html.escape(m.group(1)))
        return "\x00%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])_([^_]+)_(?![\w*])", r"<em>\1</em>", text)

    def unstash(m):
        return "<code>%s</code>" % codes[int(m.group(1))]

    return re.sub(r"\x00(\d+)\x00", unstash, text)


def _cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def convert(src):
    lines = src.split(NL)
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()

        # fenced code
        if s.startswith("```"):
            lang = s[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # closing fence
            cls = ' class="lang-%s"' % lang if lang else ""
            out.append("<pre><code%s>%s</code></pre>" % (cls, html.escape(NL.join(buf))))
            continue

        # raw block html (svg etc.)
        m = _BLOCK_HTML.match(s)
        if m:
            close = "</%s>" % m.group(1)
            buf = [line]
            if close.lower() not in line.lower():
                i += 1
                while i < n and close.lower() not in lines[i].lower():
                    buf.append(lines[i])
                    i += 1
                if i < n:
                    buf.append(lines[i])
            i += 1
            out.append(NL.join(buf))
            continue

        if not s:
            i += 1
            continue

        # heading
        hm = re.match(r"(#{1,6})\s+(.*)", s)
        if hm:
            lvl = len(hm.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, _inline(hm.group(2)), lvl))
            i += 1
            continue

        # table (header + separator row)
        if "|" in line and i + 1 < n and "-" in lines[i + 1] and \
           re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]):
            header = _cells(lines[i])
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(_cells(lines[i]))
                i += 1
            thead = "".join("<th>%s</th>" % _inline(c) for c in header)
            body = ""
            for r in rows:
                body += "<tr>" + "".join("<td>%s</td>" % _inline(c) for c in r) + "</tr>"
            out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (thead, body))
            continue

        # blockquote
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % _inline(" ".join(buf)))
            continue

        # unordered list
        if re.match(r"^[-*]\s+", s):
            buf = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                buf.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % _inline(x) for x in buf) + "</ul>")
            continue

        # ordered list
        if re.match(r"^\d+\.\s+", s):
            buf = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                buf.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join("<li>%s</li>" % _inline(x) for x in buf) + "</ol>")
            continue

        # paragraph
        buf = []
        while i < n:
            t = lines[i].strip()
            if not t or t.startswith("```") or _BLOCK_HTML.match(t) or \
               re.match(r"(#{1,6})\s|^[-*]\s|^\d+\.\s|^>", t):
                break
            buf.append(t)
            i += 1
        out.append("<p>%s</p>" % _inline(" ".join(buf)))

    return NL.join(out)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s _build/tests -p 'test_md.py' -v`
Expected: PASS (11 tests OK).

- [ ] **Step 5: Commit**

```bash
git add _build/md.py _build/tests/test_md.py
git commit -m "feat: zero-dep markdown subset converter for tutorial pages

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Front-matter parse + 7-part lint (`_build/tutorial.py`)

**Files:**
- Create: `_build/tutorial.py`
- Create: `_build/tests/test_tutorial.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `parse(text: str) -> tuple[dict, str]` — returns `(front_matter, body)`. Front-matter is the `key: value` block between leading `---` fences.
  - `REQUIRED: list[str]` — the 7 heading texts in order.
  - `lint(fm: dict, body: str) -> list[str]` — returns list of error strings; empty list = pass.

- [ ] **Step 1: Write the failing test**

Create `_build/tests/test_tutorial.py`:
```python
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import tutorial

GOOD_BODY = """## 1. What it is
It is a thing explained simply.

## 2. Why & when
Because reasons.

## 3. Core concept
The mechanism in depth.

## 4. Diagram
<svg viewBox="0 0 10 10"><rect/></svg>

## 5. Runnable example
```js
console.log("hi");
```

## 6. Walkthrough
Line 1 logs hi to the console, which proves it runs.

## 7. Gotchas & takeaways
- Watch out for this.
"""

FULL = "---\ncard: webdev\ngi: 1\nslug: x\ntitle: X\n---\n\n" + GOOD_BODY

class TestTutorial(unittest.TestCase):
    def test_parse_front_matter(self):
        fm, body = tutorial.parse(FULL)
        self.assertEqual(fm["card"], "webdev")
        self.assertEqual(fm["title"], "X")
        self.assertTrue(body.lstrip().startswith("## 1. What it is"))

    def test_lint_passes_good(self):
        fm, body = tutorial.parse(FULL)
        self.assertEqual(tutorial.lint(fm, body), [])

    def test_lint_missing_heading(self):
        fm, body = tutorial.parse(FULL.replace("## 7. Gotchas & takeaways", "## 7. Wrong"))
        self.assertTrue(any("7. Gotchas" in e for e in tutorial.lint(fm, body)))

    def test_lint_no_code_in_example(self):
        broken = FULL.replace('```js\nconsole.log("hi");\n```', "no code here")
        fm, body = tutorial.parse(broken)
        self.assertTrue(any("code block" in e for e in tutorial.lint(fm, body)))

    def test_lint_placeholder(self):
        fm, body = tutorial.parse(FULL.replace("Because reasons.", "TODO fill in"))
        self.assertTrue(any("placeholder" in e for e in tutorial.lint(fm, body)))

    def test_lint_missing_front_matter_key(self):
        fm, body = tutorial.parse(FULL.replace("title: X\n", ""))
        self.assertTrue(any("title" in e for e in tutorial.lint(fm, body)))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s _build/tests -p 'test_tutorial.py' -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tutorial'`.

- [ ] **Step 3: Write minimal implementation**

Create `_build/tutorial.py`:
```python
# -*- coding: utf-8 -*-
"""Parse tutorial markdown front-matter and lint the fixed 7-part template."""
import re

REQUIRED = [
    "1. What it is",
    "2. Why & when",
    "3. Core concept",
    "4. Diagram",
    "5. Runnable example",
    "6. Walkthrough",
    "7. Gotchas & takeaways",
]


def parse(text):
    fm = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end].strip()
            for ln in block.splitlines():
                if ":" in ln:
                    k, v = ln.split(":", 1)
                    fm[k.strip()] = v.strip()
            body = text[end + 4:].lstrip("\n")
    return fm, body


def _section(body, heading):
    """Return the text under a `## <heading>` up to the next `## `."""
    pat = re.compile(r"^##\s+" + re.escape(heading) + r"\s*$", re.M)
    m = pat.search(body)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"^##\s+", body[start:], re.M)
    return body[start:start + nxt.start()] if nxt else body[start:]


def lint(fm, body):
    errs = []
    heads = [h.strip() for h in re.findall(r"^##\s+(.*)$", body, re.M)]
    present = [h for h in heads if h in REQUIRED]
    for r in REQUIRED:
        if r not in heads:
            errs.append("missing heading: %s" % r)
    if present != REQUIRED:
        errs.append("headings out of order or duplicated")

    ex = _section(body, "5. Runnable example")
    if "```" not in ex:
        errs.append("no fenced code block in '5. Runnable example'")

    diag = _section(body, "4. Diagram").strip()
    if "<svg" not in diag and "```" not in diag and len(diag) < 20:
        errs.append("weak or missing diagram in '4. Diagram'")

    walk = _section(body, "6. Walkthrough").strip()
    if len(walk) < 30:
        errs.append("walkthrough too short")

    if re.search(r"\b(TODO|TBD|FIXME|placeholder|lorem ipsum)\b", body, re.I):
        errs.append("placeholder text present")

    for k in ("card", "gi", "slug", "title"):
        if k not in fm:
            errs.append("front-matter missing '%s'" % k)
    return errs
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s _build/tests -p 'test_tutorial.py' -v`
Expected: PASS (6 tests OK).

- [ ] **Step 5: Commit**

```bash
git add _build/tutorial.py _build/tests/test_tutorial.py
git commit -m "feat: tutorial front-matter parser + 7-part lint gate

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Tutorial page shell (`_build/tutorial_shell.py`)

**Files:**
- Create: `_build/tutorial_shell.py`
- Create: `_build/tests/test_tutorial_shell.py`

**Interfaces:**
- Consumes: nothing (receives already-converted body HTML).
- Produces: `render(meta: dict, body_html: str, prev: dict|None, next: dict|None) -> str`.
  - `meta` keys: `title`, `area` (card title, e.g. "Web Development"), `section`, `gi`, `storage_key`, `back_href` (link to the card checklist + section anchor).
  - `prev`/`next`: `{"href": str, "title": str}` or `None`.
  - Output: full self-contained HTML page (theme-matched, inline CSS/JS, copy buttons, mark-complete synced to `storage_key`/`t<gi>`).

- [ ] **Step 1: Write the failing test**

Create `_build/tests/test_tutorial_shell.py`:
```python
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import tutorial_shell

META = {
    "title": "Semantic elements",
    "area": "Web Development",
    "section": "HTML",
    "gi": 7,
    "storage_key": "spring-checklist:webdev.html",
    "back_href": "../../webdev.html#sec-2",
}

class TestShell(unittest.TestCase):
    def setUp(self):
        self.html = tutorial_shell.render(
            META, "<h2>1. What it is</h2><pre><code>x</code></pre>",
            {"href": "0006-prev.html", "title": "Prev topic"},
            {"href": "0008-next.html", "title": "Next topic"})

    def test_is_full_document(self):
        self.assertTrue(self.html.lstrip().startswith("<!DOCTYPE html>"))

    def test_has_title_and_breadcrumb(self):
        self.assertIn("Semantic elements", self.html)
        self.assertIn("Web Development", self.html)
        self.assertIn("HTML", self.html)

    def test_uses_storage_key_and_id(self):
        self.assertIn("spring-checklist:webdev.html", self.html)
        self.assertIn('"t7"', self.html)

    def test_back_and_nav_links(self):
        self.assertIn("../../webdev.html#sec-2", self.html)
        self.assertIn("0006-prev.html", self.html)
        self.assertIn("0008-next.html", self.html)

    def test_copy_button_script_present(self):
        self.assertIn("clipboard", self.html)

    def test_self_contained_no_external(self):
        self.assertNotIn("http://", self.html)
        self.assertNotIn("https://", self.html)

    def test_body_injected(self):
        self.assertIn("1. What it is", self.html)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s _build/tests -p 'test_tutorial_shell.py' -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tutorial_shell'`.

- [ ] **Step 3: Write minimal implementation**

Create `_build/tutorial_shell.py`:
```python
# -*- coding: utf-8 -*-
"""Self-contained tutorial page shell (theme-matched to the checklists)."""
import json

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__ — Tutorial</title>
<style>
  :root{--bg:#0d1117;--panel:#161b22;--panel2:#1c2430;--border:#30363d;--text:#e6edf3;
        --muted:#8b949e;--accent:#6db33f;--accent2:#34804f;--done:#3fb950;--code:#79c0ff;}
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;background:var(--bg);color:var(--text);line-height:1.65;
       font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
  header{position:sticky;top:0;z-index:20;background:rgba(13,17,23,.92);backdrop-filter:blur(8px);
         border-bottom:1px solid var(--border);padding:12px 20px}
  .crumb{font-size:12.5px;color:var(--muted)}
  .crumb a{color:var(--muted);text-decoration:none}
  .crumb a:hover{color:var(--accent)}
  .htitle{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:6px}
  .htitle h1{font-size:21px;margin:0}
  .back{font-size:13px;color:var(--muted);text-decoration:none;border:1px solid var(--border);
        padding:5px 10px;border-radius:8px}
  .back:hover{border-color:var(--accent);color:var(--text)}
  .mc{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer;
      border:1px solid var(--border);padding:6px 12px;border-radius:8px}
  .mc input{width:17px;height:17px;accent-color:var(--done);cursor:pointer}
  main{max-width:880px;margin:0 auto;padding:26px 20px 60px}
  h2{font-size:20px;margin:30px 0 10px;padding-top:14px;border-top:1px solid var(--border);color:var(--accent)}
  main > h2:first-child{border-top:none;padding-top:0;margin-top:0}
  h3{font-size:16px;margin:20px 0 8px}
  p{margin:10px 0}
  ul,ol{margin:10px 0;padding-left:22px}
  li{margin:5px 0}
  a{color:var(--code)}
  code{background:var(--panel2);padding:1px 6px;border-radius:5px;font-size:13.5px;color:var(--code);
       font-family:"SF Mono", Menlo,Consolas,monospace}
  pre{position:relative;background:#0a0e14;border:1px solid var(--border);border-radius:10px;
      padding:14px 16px;overflow:auto;margin:14px 0}
  pre code{background:none;padding:0;color:#c9d1d9;display:block;line-height:1.55;font-size:13.5px}
  pre .copy{position:absolute;top:8px;right:8px;background:var(--panel2);border:1px solid var(--border);
            color:var(--muted);font-size:12px;padding:3px 9px;border-radius:6px;cursor:pointer}
  pre .copy:hover{border-color:var(--accent);color:var(--text)}
  blockquote{margin:14px 0;padding:10px 16px;border-left:3px solid var(--accent);
             background:var(--panel);border-radius:0 8px 8px 0;color:#d8e0e8}
  table{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px}
  th,td{border:1px solid var(--border);padding:7px 11px;text-align:left}
  th{background:var(--panel2)}
  svg{max-width:100%;height:auto;background:var(--panel);border:1px solid var(--border);
      border-radius:10px;padding:10px;margin:12px 0;display:block}
  .nav{display:flex;justify-content:space-between;gap:12px;margin-top:40px;
       border-top:1px solid var(--border);padding-top:18px}
  .nav a{flex:1;text-decoration:none;color:var(--text);border:1px solid var(--border);
         border-radius:10px;padding:12px 14px;font-size:13px}
  .nav a:hover{border-color:var(--accent)}
  .nav .nxt{text-align:right}
  .nav .mini{display:block;color:var(--muted);font-size:11px;margin-bottom:3px}
  .nav .spacer{flex:1}
  footer{text-align:center;color:var(--muted);font-size:12px;padding:24px}
</style>
</head>
<body>
<header>
  <div class="crumb"><a href="__BACK__">__AREA__</a> › __SECTION__</div>
  <div class="htitle">
    <h1>__TITLE__</h1>
    <a class="back" href="__BACK__">← Back to checklist</a>
    <label class="mc"><input type="checkbox" id="mc"> Mark complete</label>
  </div>
</header>
<main>
__BODY__
  <div class="nav">__PREV____NEXT__</div>
  <footer>Progress saved in your browser. Self-contained tutorial page — works offline.</footer>
</main>
<script>
const KEY = __KEY__, ID = __ID__;
const box = document.getElementById("mc");
function load(){ try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch(e){ return {}; } }
box.checked = !!load()[ID];
box.addEventListener("change", ()=>{
  const st = load();
  if (box.checked) st[ID] = 1; else delete st[ID];
  localStorage.setItem(KEY, JSON.stringify(st));
});
document.querySelectorAll("pre").forEach(pre=>{
  const code = pre.querySelector("code"); if(!code) return;
  const b = document.createElement("button");
  b.className = "copy"; b.textContent = "Copy";
  b.addEventListener("click", ()=>{
    const t = code.innerText;
    const done = ()=>{ b.textContent = "Copied"; setTimeout(()=>b.textContent="Copy",1200); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, done);
    else { const ta=document.createElement("textarea"); ta.value=t; document.body.appendChild(ta); ta.select();
           try{document.execCommand("copy");}catch(e){} ta.remove(); done(); }
  });
  pre.appendChild(b);
});
</script>
</body>
</html>
"""


def _nav(item, cls, mini):
    if not item:
        return '<span class="spacer"></span>'
    return '<a class="%s" href="%s"><span class="mini">%s</span>%s</a>' % (
        cls, item["href"], mini, item["title"])


def render(meta, body_html, prev, next):
    html = PAGE
    html = html.replace("__TITLE__", meta["title"])
    html = html.replace("__AREA__", meta["area"])
    html = html.replace("__SECTION__", meta["section"])
    html = html.replace("__BACK__", meta["back_href"])
    html = html.replace("__BODY__", body_html)
    html = html.replace("__PREV__", _nav(prev, "prv", "← Previous"))
    html = html.replace("__NEXT__", _nav(next, "nxt", "Next →"))
    html = html.replace("__KEY__", json.dumps(meta["storage_key"]))
    html = html.replace("__ID__", json.dumps("t%d" % meta["gi"]))
    return html
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s _build/tests -p 'test_tutorial_shell.py' -v`
Expected: PASS (7 tests OK).
Note: `test_self_contained_no_external` asserts no `http://`/`https://` — keep the shell free of external URLs (the `lang="en"` and any `xmlns` belong only in authored SVG bodies, not the shell chrome).

- [ ] **Step 5: Commit**

```bash
git add _build/tutorial_shell.py _build/tests/test_tutorial_shell.py
git commit -m "feat: self-contained tutorial page shell with copy + mark-complete

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Manifest builder (`_build/manifest.py`)

**Files:**
- Create: `_build/manifest.py`
- Create: `_build/tests/test_manifest.py`

**Interfaces:**
- Consumes: `topics.enumerate_topics`, `topics.card_stem`, `topics.page_path`.
- Produces:
  - `PHASE_CAP = 12`.
  - `build(projects: list[dict], exists_fn) -> dict` — builds the manifest. `exists_fn(relpath:str)->bool` reports whether a tutorial page already exists (a topic is `done` when its page exists). Splits each section into phases of ≤`PHASE_CAP` topics; sets `next_phase` to the first phase containing any pending topic.

- [ ] **Step 1: Write the failing test**

Create `_build/tests/test_manifest.py`:
```python
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import manifest

def make_project(n_html, n_css):
    return {
        "file": "webdev.html", "title": "Web Development",
        "sections": [
            {"name": "HTML", "tag": "html", "groups": [
                {"g": "G", "items": ["h%d" % i for i in range(n_html)]}]},
            {"name": "CSS", "tag": "css", "groups": [
                {"g": "G", "items": ["c%d" % i for i in range(n_css)]}]},
        ],
    }

class TestManifest(unittest.TestCase):
    def test_splits_into_phase_cap(self):
        proj = make_project(30, 5)   # HTML must split 12/12/6
        m = manifest.build([proj], lambda p: False)
        phases = m["cards"]["webdev"]["sections"][0]["phases"]
        self.assertEqual([len(p["gis"]) for p in phases], [12, 12, 6])

    def test_next_phase_is_first_pending(self):
        proj = make_project(3, 3)
        # mark all HTML pages (gi 1..3) as existing -> next is CSS phase
        done = {"tutorials/webdev/0001-h0.html", "tutorials/webdev/0002-h1.html",
                "tutorials/webdev/0003-h2.html"}
        m = manifest.build([proj], lambda p: p in done)
        self.assertEqual(m["next_phase"], "webdev/css#1")

    def test_topic_status_reflects_existence(self):
        proj = make_project(2, 0)
        done = {"tutorials/webdev/0001-h0.html"}
        m = manifest.build([proj], lambda p: p in done)
        ts = m["cards"]["webdev"]["sections"][0]["topics"]
        self.assertEqual(ts[0]["status"], "done")
        self.assertEqual(ts[1]["status"], "pending")

    def test_all_done_next_phase_none(self):
        proj = make_project(1, 0)
        m = manifest.build([proj], lambda p: True)
        self.assertIsNone(m["next_phase"])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s _build/tests -p 'test_manifest.py' -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'manifest'`.

- [ ] **Step 3: Write minimal implementation**

Create `_build/manifest.py`:
```python
# -*- coding: utf-8 -*-
"""Build the phase manifest that drives incremental tutorial generation."""
import topics

PHASE_CAP = 12


def _phase_id(stem, tag, idx):
    return "%s/%s#%d" % (stem, tag or "sec", idx)


def build(projects, exists_fn):
    cards = {}
    next_phase = None
    for proj in projects:
        stem = topics.card_stem(proj)
        ts = topics.enumerate_topics(proj)
        # group enumerated topics by section name (preserves order)
        by_section = []
        order = []
        index = {}
        for t in ts:
            if t["section"] not in index:
                index[t["section"]] = len(by_section)
                by_section.append([])
                order.append((t["section"], t["tag"]))
            by_section[index[t["section"]]].append(t)

        sections_out = []
        for si, (name, tag) in enumerate(order):
            sec_topics = by_section[si]
            topics_out = []
            for t in sec_topics:
                path = topics.page_path(stem, t["gi"], t["slug"])
                status = "done" if exists_fn(path) else "pending"
                topics_out.append({"gi": t["gi"], "slug": t["slug"],
                                   "text": t["text"], "status": status})
            phases = []
            for pi in range(0, len(sec_topics), PHASE_CAP):
                chunk = sec_topics[pi:pi + PHASE_CAP]
                gis = [t["gi"] for t in chunk]
                pstatus = "done" if all(
                    topics_out[g - sec_topics[0]["gi"]]["status"] == "done"
                    for g in gis) else "pending"
                pid = _phase_id(stem, tag, len(phases) + 1)
                phases.append({"id": pid, "gis": gis, "status": pstatus})
                if pstatus == "pending" and next_phase is None:
                    next_phase = pid
            sections_out.append({"name": name, "tag": tag,
                                 "topics": topics_out, "phases": phases})
        cards[stem] = {"title": proj.get("title", stem), "sections": sections_out}

    return {"cards": cards, "next_phase": next_phase}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s _build/tests -p 'test_manifest.py' -v`
Expected: PASS (4 tests OK).

- [ ] **Step 5: Commit**

```bash
git add _build/manifest.py _build/tests/test_manifest.py
git commit -m "feat: phase manifest builder (split <=12, next-pending pointer)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: Wire tutorials into the build (`_build/shell.py` + `_build/generate.py`)

**Files:**
- Modify: `_build/shell.py` (add `links` param; render linked topics)
- Modify: `_build/generate.py` (build tutorials, link-map, lint gate, write manifest)
- Create: `_build/tests/test_integration.py`

**Interfaces:**
- Consumes: `topics`, `md`, `tutorial`, `tutorial_shell`, `manifest`.
- Produces (in `generate.py`):
  - `build_tutorials() -> dict` — builds every `content/<card>/*.md` into `tutorials/<card>/*.html`, returns `{stem: {gi: relurl}}` link-map. Raises `SystemExit` with the lint errors if any page fails lint.
  - `shell.render(title, logo, subtitle, storage_key, data, links=None)` — `links` is `{gi: url}`; linked topics render as anchors.

- [ ] **Step 1: Write the failing integration test**

Create `_build/tests/test_integration.py`:
```python
import os, sys, shutil, tempfile, unittest
HERE = os.path.dirname(__file__)
BUILD = os.path.join(HERE, "..")
sys.path.insert(0, BUILD)
import shell

class TestShellLinks(unittest.TestCase):
    def test_links_render_anchor_when_present(self):
        data = [{"name": "S", "tag": "t", "groups": [{"g": "G", "items": ["Alpha", "Beta"]}]}]
        out = shell.render("T", "L", "sub", "k", data, links={1: "tutorials/x/0001-alpha.html"})
        self.assertIn('tutorials/x/0001-alpha.html', out)
        self.assertIn('const LINKS =', out)

    def test_no_links_param_still_works(self):
        data = [{"name": "S", "tag": "t", "groups": [{"g": "G", "items": ["Alpha"]}]}]
        out = shell.render("T", "L", "sub", "k", data)
        self.assertIn("const LINKS = {}", out.replace(" ", " "))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s _build/tests -p 'test_integration.py' -v`
Expected: FAIL — `render()` got an unexpected keyword argument `links` (or LINKS assertion fails).

- [ ] **Step 3a: Modify `_build/shell.py` — inject the link-map**

In `_build/shell.py`, in the `<script>` block, find:
```python
const STORAGE_KEY = "__STORAGE_KEY__";
const DATA = __DATA_JSON__;
```
Replace with:
```python
const STORAGE_KEY = "__STORAGE_KEY__";
const DATA = __DATA_JSON__;
const LINKS = __LINKS_JSON__;
```

- [ ] **Step 3b: Modify `_build/shell.py` — render linked label**

Find the topic-building block:
```python
      li.innerHTML = `
        <input type="checkbox" id="${id}" ${checked}>
        <span class="idx">${gi}.</span>
        <label for="${id}">${text}</label>`;
```
Replace with:
```python
      const turl = LINKS[gi];
      const labelHtml = turl
        ? `<a class="tlink" href="${turl}">${text}</a> <span class="pin" title="Open tutorial">📖</span>`
        : `<label for="${id}">${text}</label>`;
      li.innerHTML = `
        <input type="checkbox" id="${id}" ${checked}>
        <span class="idx">${gi}.</span>
        ${labelHtml}`;
```

- [ ] **Step 3c: Modify `_build/shell.py` — add link CSS**

Find:
```python
  li.topic.done label{color:var(--muted); text-decoration:line-through}
```
Add directly after it:
```python
  li.topic .tlink{color:var(--text);text-decoration:none;border-bottom:1px dotted var(--accent);font-size:14.5px}
  li.topic .tlink:hover{color:var(--accent)}
  li.topic .pin{font-size:11px;opacity:.55;flex:none}
  li.topic.done .tlink{color:var(--muted);text-decoration:line-through}
```

- [ ] **Step 3d: Modify `_build/shell.py` — `render()` signature**

Find:
```python
def render(title, logo, subtitle, storage_key, data):
    html = SHELL
    html = html.replace("__TITLE__", title)
    html = html.replace("__LOGO__", logo)
    html = html.replace("__SUBTITLE__", subtitle)
    html = html.replace("__STORAGE_KEY__", storage_key)
    html = html.replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False, indent=0))
    return html
```
Replace with:
```python
def render(title, logo, subtitle, storage_key, data, links=None):
    html = SHELL
    html = html.replace("__TITLE__", title)
    html = html.replace("__LOGO__", logo)
    html = html.replace("__SUBTITLE__", subtitle)
    html = html.replace("__STORAGE_KEY__", storage_key)
    html = html.replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False, indent=0))
    html = html.replace("__LINKS_JSON__", json.dumps(links or {}, ensure_ascii=False))
    return html
```

- [ ] **Step 4: Run shell test to verify it passes**

Run: `python3 -m unittest discover -s _build/tests -p 'test_integration.py' -v`
Expected: PASS (2 tests OK).

- [ ] **Step 5: Modify `_build/generate.py` — imports + tutorial build**

Find:
```python
from shell import render
import data_microservices, data_genai, data_webdev, data_core, data_data_cloud, data_security, data_messaging, data_web, data_apps
```
Replace with:
```python
import json
from shell import render
import topics as topicmod
import md as mdmod
import tutorial as tut
import tutorial_shell
import manifest as manifestmod
import data_microservices, data_genai, data_webdev, data_core, data_data_cloud, data_security, data_messaging, data_web, data_apps
```

Then find:
```python
def write_project(p):
    storage_key = "spring-checklist:" + p["file"]
    html = render(p["title"], p["logo"], p["subtitle"], storage_key, p["sections"])
    path = os.path.join(OUT, p["file"])
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return total_topics(p["sections"])
```
Replace with:
```python
def write_project(p, links=None):
    storage_key = "spring-checklist:" + p["file"]
    html = render(p["title"], p["logo"], p["subtitle"], storage_key, p["sections"], links=links)
    path = os.path.join(OUT, p["file"])
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return total_topics(p["sections"])


def build_tutorials():
    """Build content/<card>/*.md -> tutorials/<card>/*.html. Returns {stem:{gi:relurl}}."""
    content_root = os.path.join(OUT, "content")
    linkmap = {}
    lint_errors = []
    for p in PROJECTS:
        stem = topicmod.card_stem(p)
        enum = {t["gi"]: t for t in topicmod.enumerate_topics(p)}
        src_dir = os.path.join(content_root, stem)
        if not os.path.isdir(src_dir):
            continue
        # collect built pages for this card (by gi) to compute prev/next
        built = []
        for fn in sorted(os.listdir(src_dir)):
            if not fn.endswith(".md"):
                continue
            gi = int(fn.split("-", 1)[0])
            text = open(os.path.join(src_dir, fn), encoding="utf-8").read()
            fm, body = tut.parse(text)
            errs = tut.lint(fm, body)
            if errs:
                lint_errors.append("%s/%s: %s" % (stem, fn, "; ".join(errs)))
                continue
            built.append((gi, fm, body))
        built.sort(key=lambda x: x[0])
        out_dir = os.path.join(OUT, "tutorials", stem)
        os.makedirs(out_dir, exist_ok=True)
        for idx, (gi, fm, body) in enumerate(built):
            t = enum[gi]
            slug = t["slug"]
            fname = "%04d-%s.html" % (gi, slug)
            relurl = "tutorials/%s/%s" % (stem, fname)
            prev = None
            nxt = None
            if idx > 0:
                pg, pf, _pb = built[idx - 1]
                prev = {"href": "%04d-%s.html" % (pg, enum[pg]["slug"]),
                        "title": enum[pg]["text"]}
            if idx < len(built) - 1:
                ng = built[idx + 1][0]
                nxt = {"href": "%04d-%s.html" % (ng, enum[ng]["slug"]),
                       "title": enum[ng]["text"]}
            meta = {
                "title": fm.get("title", t["text"]),
                "area": p.get("title", stem),
                "section": t["section"],
                "gi": gi,
                "storage_key": "spring-checklist:%s.html" % stem,
                "back_href": "../../%s.html" % stem,
            }
            page = tutorial_shell.render(meta, mdmod.convert(body), prev, nxt)
            with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
                f.write(page)
            linkmap.setdefault(stem, {})[gi] = relurl
    if lint_errors:
        raise SystemExit("Tutorial lint failed:\n  " + "\n  ".join(lint_errors))
    return linkmap
```

- [ ] **Step 6: Modify `_build/generate.py` — call tutorial build + manifest in `main()`**

Find in `main()`:
```python
    for p in PROJECTS:
        n = write_project(p)
        grand += n
        rows.append((p, n))
        print(f"  {p['file']:<34} {n:>4} topics")

    build_index(rows, grand)
    print(f"\nindex.html written. {len(rows)} projects, {grand} total micro-topics.")
```
Replace with:
```python
    linkmap = build_tutorials()
    n_pages = sum(len(v) for v in linkmap.values())

    for p in PROJECTS:
        stem = topicmod.card_stem(p)
        n = write_project(p, links=linkmap.get(stem))
        grand += n
        rows.append((p, n))
        print(f"  {p['file']:<34} {n:>4} topics")

    build_index(rows, grand)

    def _exists(relpath):
        return os.path.exists(os.path.join(OUT, relpath))
    man = manifestmod.build(PROJECTS, _exists)
    os.makedirs(os.path.join(OUT, "content"), exist_ok=True)
    with open(os.path.join(OUT, "content", "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)

    print(f"\nindex.html written. {len(rows)} projects, {grand} total micro-topics.")
    print(f"tutorial pages: {n_pages} built. next_phase: {man['next_phase']}")
```

- [ ] **Step 7: Run full build to verify nothing breaks (no content yet)**

Run: `python3 _build/generate.py`
Expected: completes, prints `tutorial pages: 0 built. next_phase: webdev/...#1` (no `content/` dirs yet so 0 pages; manifest written).
Then run all tests: `python3 -m unittest discover -s _build/tests -p 'test_*.py' -v`
Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add _build/shell.py _build/generate.py _build/tests/test_integration.py content/_manifest.json
git commit -m "feat: wire tutorial build, link-map, lint gate and manifest into generator

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: Prove the pipeline — build pilot phase 1 (first ≤12 webdev topics)

This task produces the first real phase end-to-end and establishes the **gold-standard quality bar** every later page must match. It is also the template the daily driver replicates.

**Files:**
- Create: `content/webdev/<NNNN>-<slug>.md` for the topics in pilot phase 1
- Result: `tutorials/webdev/*.html` built, webdev checklist links them

**Interfaces:**
- Consumes: everything from Tasks 1–6.
- Produces: real tutorial pages + updated `content/_manifest.json` (phase 1 → done).

- [ ] **Step 1: Enumerate phase 1 topics**

Run:
```bash
python3 -c "import sys; sys.path.insert(0,'_build'); import topics, data_webdev; ts=topics.enumerate_topics(data_webdev.PROJECTS[0]); [print(t['gi'], '|', t['section'], '|', t['slug'], '|', t['text']) for t in ts[:12]]"
```
Expected: prints the first 12 topics (gi 1–12) with section + slug. These are pilot phase 1.

- [ ] **Step 2: Author the first tutorial as the gold standard**

For the **first** enumerated topic (gi 1), create `content/webdev/0001-<slug>.md` following this exact shape and quality (replace the subject with the real topic; keep all 7 headings, a real runnable example, a real diagram, a real walkthrough):

````markdown
---
card: webdev
gi: 1
slug: <slug-from-step-1>
title: <Topic title>
---

## 1. What it is

Two or three short paragraphs in plain language. No jargon without defining it. State precisely what this topic is and where it sits in the bigger picture.

## 2. Why & when

Why it exists, the problem it solves, and when you'd actually reach for it versus the alternatives. Use a short bullet list of concrete use-cases.

## 3. Core concept

The mechanism, from basics to advanced. Build it up step by step. Define every term. This is the longest section.

## 4. Diagram

<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="...">
  <rect x="20" y="40" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="76" fill="#e6edf3" font-size="14" text-anchor="middle">Client</text>
  <line x1="180" y1="70" x2="420" y2="70" stroke="#8b949e" stroke-width="2"/>
  <rect x="420" y="40" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="500" y="76" fill="#e6edf3" font-size="14" text-anchor="middle">Server</text>
</svg>

A one-line caption explaining what the diagram shows.

## 5. Runnable example

A complete, copy-paste-and-run example. Self-contained.

```html
<!doctype html>
<html>
  <body>
    <p id="out"></p>
    <script>document.getElementById("out").textContent = "It runs!";</script>
  </body>
</html>
```

**How to run:** save as `demo.html`, open in any browser.

## 6. Walkthrough

Step-by-step explanation of the example above, referencing the actual lines. Explain *why*, not just *what*.

1. The `<p id="out">` is the target element...
2. The inline `<script>`...

## 7. Gotchas & takeaways

> Common mistake: ...

- Key takeaway one.
- Key takeaway two.
- Key takeaway three.
````

- [ ] **Step 3: Build and verify the gold-standard page**

Run: `python3 _build/generate.py`
Expected: `tutorial pages: 1 built.` and no lint error.
Open `tutorials/webdev/0001-<slug>.html` in a browser; confirm: 7 sections render, code has a Copy button that works, diagram shows, Mark-complete toggles, Back link points to `../../webdev.html`.
Open `webdev.html`; confirm topic 1 is now a clickable 📖 link.

- [ ] **Step 4: Author the remaining phase-1 topics (gi 2–12)**

Create `content/webdev/<NNNN>-<slug>.md` for gi 2 through 12, each matching the gold-standard depth and the 7-part template. Keep examples genuinely runnable and walkthroughs specific.

- [ ] **Step 5: Build, lint, and verify the full phase**

Run: `python3 _build/generate.py`
Expected: `tutorial pages: 12 built.`, no lint errors, `next_phase` advanced to phase 2.
Run: `python3 -m unittest discover -s _build/tests -p 'test_*.py' -v` → all PASS.
Spot-check 2–3 of the new pages in a browser (prev/next nav works across them).

- [ ] **Step 6: Commit**

```bash
git add content/webdev tutorials/webdev content/_manifest.json webdev.html
git commit -m "content: pilot phase 1 — first 12 Web Development tutorials

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: Daily driver prompt + README (`docs/superpowers/DAILY_PROMPT.md`)

**Files:**
- Create: `docs/superpowers/DAILY_PROMPT.md`
- Modify: `_build/README` note is optional; skip if none exists.

**Interfaces:**
- Consumes: the working pipeline + manifest from Tasks 1–7.
- Produces: a paste-ready prompt the user runs in a fresh session each day.

- [ ] **Step 1: Write the daily driver prompt**

Create `docs/superpowers/DAILY_PROMPT.md` with this exact content:
````markdown
# Daily Tutorial Phase — paste this whole block into a fresh Claude Code session

You are continuing the Learning hub tutorial-content build. Do ONE phase, then stop.

## Steps

1. Read `content/_manifest.json`. Find `next_phase`. If it is `null`, reply
   "All phases complete." and stop. Otherwise note its `id` and its `gis` list
   (the topic indices to build this phase, ≤12).

2. For each `gi` in the phase, in ascending order, find the topic's `section`,
   `slug`, and `text`:
   ```
   python3 -c "import sys; sys.path.insert(0,'_build'); import topics, generate; \
   [print(t['gi'],'|',t['section'],'|',t['slug'],'|',t['text']) \
   for p in generate.PROJECTS for t in topics.enumerate_topics(p) \
   if topics.card_stem(p)=='<CARD-STEM-FROM-PHASE-ID>' and t['gi'] in <GIS-LIST>]"
   ```

3. Author `content/<card>/<gi:04d>-<slug>.md` for each topic, following the
   fixed 7-part template (`## 1. What it is` … `## 7. Gotchas & takeaways`) at the
   same depth as `content/webdev/0001-*.md`. Requirements per page:
   - Plain language, basics → advanced.
   - Part 4 has a real inline `<svg>` (or ASCII) diagram + caption.
   - Part 5 has a complete, copy-paste-runnable example in a fenced code block
     with a language tag and a "How to run" line.
   - Part 6 explains the example specifically, line/step by line/step.
   - No TODO/TBD/placeholder text.

4. Run `python3 _build/generate.py`. It lints every page; fix any reported error
   and re-run until it prints the new page count with no lint failure.

5. Run `python3 -m unittest discover -s _build/tests -p 'test_*.py' -v`. All must PASS.

6. Verify: the manifest's `next_phase` advanced past the phase you built, and the
   `webdev.html` (or relevant card) now links the new `gi`s as 📖.

7. Commit and push:
   ```
   git add content tutorials *.html
   git commit -m "content: phase <id> — <N> tutorials

   Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
   git push
   ```

8. Reply with: the phase id you completed, how many pages built, and the new
   `next_phase`. Remind me to hard-refresh (Cmd+Shift+R) on the Pages site.

## Rules
- Exactly ONE phase per run. Do not run ahead.
- Never reorder or delete existing topics in `_build/data_*.py`.
- Quality over speed: every page must be genuinely useful as a standalone tutorial.
````

- [ ] **Step 2: Verify the prompt's enumeration command works**

Run (substituting a real card stem + gi list, e.g. `webdev` and `[13,14,15]`):
```bash
python3 -c "import sys; sys.path.insert(0,'_build'); import topics, generate; [print(t['gi'],'|',t['section'],'|',t['slug'],'|',t['text']) for p in generate.PROJECTS for t in topics.enumerate_topics(p) if topics.card_stem(p)=='webdev' and t['gi'] in [13,14,15]]"
```
Expected: prints topics 13–15 with section + slug (proves the daily command resolves topics).

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/DAILY_PROMPT.md
git commit -m "docs: paste-ready daily tutorial-phase driver prompt

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage:**
- §4.1 topic identity → Task 1 ✓
- §4.2 markdown source / 7-part skeleton → Tasks 3, 7 ✓
- §4.3 converter → Task 2 ✓
- §4.4 page shell (breadcrumb, back, prev/next, copy, mark-complete) → Task 4 ✓
- §4.5 mark-complete sync (same key/id) → Task 4 (test_uses_storage_key_and_id) ✓
- §4.6 checklist linking / link-map → Task 6 ✓
- §4.7 build integration (build, prev/next, lint, regenerate) → Task 6 ✓
- §4.8 manifest → Task 5, written in Task 6 ✓
- §5 daily driver → Task 8 ✓
- §6 lint quality bar → Task 3 (+ enforced in Task 6 build) ✓
- §7 pilot phase 1 + gate → Task 7 ✓

**Placeholder scan:** Task 7 intentionally leaves topic *content* to authoring time (content, not code) but provides a complete gold-standard template and exact build/verify commands — not a code placeholder. All code steps contain full implementations.

**Type consistency:** `render(meta, body_html, prev, next)` signature consistent across Task 4 and its Task 6 caller. `topics.card_stem`/`page_path`/`enumerate_topics` signatures consistent across Tasks 1, 5, 6. `tutorial.parse`/`lint` consistent across Tasks 3, 6. `manifest.build(projects, exists_fn)` consistent across Tasks 5, 6. Link-map shape `{stem:{gi:url}}` consistent in Task 6 producer and `write_project(p, links=linkmap.get(stem))` consumer; `shell.render(..., links={gi:url})` matches.

**Note on manifest phase status index math (Task 5):** `topics_out[g - sec_topics[0]["gi"]]` assumes a section's `gi`s are contiguous, which holds because `enumerate_topics` numbers sequentially and a section's topics are emitted consecutively. Valid.
