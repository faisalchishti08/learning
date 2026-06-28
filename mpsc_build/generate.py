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
