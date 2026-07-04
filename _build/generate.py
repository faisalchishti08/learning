# -*- coding: utf-8 -*-
"""Generate one self-contained HTML checklist per Spring project + an index hub.

Run:  python3 _build/generate.py
Output: writes *.html into the parent (Learning/) directory.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import json
from shell import render
import topics as topicmod
import md as mdmod
import tutorial as tut
import tutorial_shell
import manifest as manifestmod
import data_java, data_microservices, data_genai, data_webdev, data_core, data_data_cloud, data_security, data_messaging, data_web, data_apps

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Ordered registry of every project (mirrors spring.io/projects active list).
# data_java is the Language Foundation card (hand-maintained java.html; here only to drive tutorials).
# data_microservices, data_genai & data_webdev are knowledge areas (not spring.io projects).
PROJECTS = []
for mod in (data_java, data_microservices, data_genai, data_webdev, data_core, data_data_cloud, data_security, data_messaging, data_web, data_apps):
    PROJECTS.extend(mod.PROJECTS)


def total_topics(sections):
    n = 0
    for s in sections:
        for g in s["groups"]:
            n += len(g["items"])
    return n


def write_project(p, links=None):
    # java.html is hand-maintained (bespoke template + its own progress key); never overwrite it.
    # It still participates in PROJECTS so its tutorials build and the resolver can sequence it.
    if p["file"] == "java.html":
        return total_topics(p["sections"])
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
                pg = built[idx - 1][0]
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


INDEX_SHELL = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Spring Projects — Mastery Checklists</title>
<style>
  :root{--bg:#0d1117;--panel:#161b22;--panel2:#1c2430;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#6db33f;--done:#3fb950;--bar-bg:#21262d;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.5}
  header{border-bottom:1px solid var(--border);padding:26px 20px;text-align:center;background:var(--panel)}
  header h1{margin:0 0 6px;font-size:26px}
  header p{margin:0;color:var(--muted);font-size:14px}
  .logo{width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#6db33f,#34804f);display:inline-flex;align-items:center;justify-content:center;font-weight:800;color:#fff;font-size:22px;margin-bottom:10px}
  main{max-width:1080px;margin:0 auto;padding:24px 20px 60px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
  a.card{display:block;text-decoration:none;color:var(--text);background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px 18px;transition:.15s}
  a.card:hover{border-color:var(--accent);transform:translateY(-2px)}
  a.card .nm{font-size:16px;font-weight:700;display:flex;align-items:center;gap:9px}
  a.card .dot{width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,#6db33f,#34804f);display:inline-flex;align-items:center;justify-content:center;font-weight:800;color:#fff;font-size:13px;flex:none}
  a.card .ds{margin:8px 0 0;font-size:12.5px;color:var(--muted)}
  a.card .ct{margin-top:10px;font-size:12px;color:var(--accent)}
  .cat{grid-column:1/-1;margin:18px 0 2px;font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);font-weight:700}
  footer{text-align:center;color:var(--muted);font-size:12px;padding:20px}
</style>
</head>
<body>
<header>
  <div class="logo">S</div>
  <h1>Spring Projects — Mastery Checklists</h1>
  <p>__GRANDTOTAL__ micro-topics across __NPROJ__ projects · click any project · progress saved per file</p>
</header>
<main>
  <div class="grid">
__CARDS__
  </div>
  <footer>Generated from the active project list at spring.io/projects. Each file is self-contained and tracks its own progress.</footer>
</main>
</body>
</html>
"""


def build_index(rows, grand_total):
    cards = []
    last_cat = None
    for p, n in rows:
        if p.get("cat") != last_cat:
            last_cat = p.get("cat")
            cards.append(f'    <div class="cat">{last_cat}</div>')
        cards.append(
            f'    <a class="card" href="{p["file"]}">'
            f'<div class="nm"><span class="dot">{p["logo"]}</span>{p["title"]}</div>'
            f'<p class="ds">{p["subtitle"]}</p>'
            f'<div class="ct">{n} topics →</div></a>'
        )
    html = INDEX_SHELL.replace("__CARDS__", "\n".join(cards))
    html = html.replace("__GRANDTOTAL__", f"{grand_total:,}")
    html = html.replace("__NPROJ__", str(len(rows)))
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def java_topic_count():
    """Count topics in the hand-maintained java.html (DATA is JS, count items)."""
    path = os.path.join(OUT, "java.html")
    if not os.path.exists(path):
        return None
    # Prefer node (evaluates the JS array exactly); fall back to a regex count.
    import subprocess
    try:
        js = ('const fs=require("fs");let s=fs.readFileSync(%r,"utf8");'
              'let m=s.match(/const DATA = (\\[[\\s\\S]*?\\]);\\s*\\n/);'
              'let D=eval(m[1]);let n=0;D.forEach(v=>v.groups.forEach(g=>n+=g.items.length));'
              'console.log(n);' % path)
        out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=15)
        if out.returncode == 0 and out.stdout.strip().isdigit():
            return int(out.stdout.strip())
    except Exception:
        pass
    import re
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"const DATA = (\[.*?\]);\s*\n", txt, re.S)
    if not m:
        return None
    # count quoted string items inside every items:[ ... ] block
    n = 0
    for block in re.findall(r"items:\s*\[(.*?)\]", m.group(1), re.S):
        n += len(re.findall(r'(?<!\\)"', block)) // 2
    return n or None


def main():
    rows = []
    grand = 0

    # Java SE (java.html) now flows through PROJECTS via data_java (listed first) — no special-case.
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
    man = manifestmod.build(PROJECTS, _exists, pilot="webdev")
    os.makedirs(os.path.join(OUT, "content"), exist_ok=True)
    with open(os.path.join(OUT, "content", "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)

    print(f"\nindex.html written. {len(rows)} projects, {grand} total micro-topics.")
    print(f"tutorial pages: {n_pages} built. next_phase: {man['next_phase']}")


if __name__ == "__main__":
    main()
