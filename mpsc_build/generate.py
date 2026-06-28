"""Generate mpsc/ HTML from syllabus data. Run: python3 -m mpsc_build.generate"""
import os
from mpsc_build.syllabus import load_all
from mpsc_build.template import render_page, render_hub

OUT = os.path.join(os.path.dirname(__file__), "..", "mpsc")


def main():
    os.makedirs(OUT, exist_ok=True)
    subjects = load_all()
    for s in subjects:
        with open(os.path.join(OUT, s["key"] + ".html"), "w", encoding="utf-8") as f:
            f.write(render_page(s))
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_hub(subjects))
    print(f"generated {len(subjects)} subject pages + hub into mpsc/")


if __name__ == "__main__":
    main()
