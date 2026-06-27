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
