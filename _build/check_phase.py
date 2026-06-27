# -*- coding: utf-8 -*-
"""Verify all authored tutorials pass the quality gate and are built.

Run:  python3 _build/check_phase.py
Exit 0 + 'CHECK PASS' when every content/*.md lints and has a built page.
Exit 1 + a list of problems otherwise. Safe to run in any session/model.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))
import topics as topicmod
import tutorial as tut
import generate  # provides PROJECTS

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    problems = []
    n_md = 0
    n_pages = 0

    for p in generate.PROJECTS:
        stem = topicmod.card_stem(p)
        enum = {t["gi"]: t for t in topicmod.enumerate_topics(p)}
        src_dir = os.path.join(OUT, "content", stem)
        if not os.path.isdir(src_dir):
            continue
        for fn in sorted(os.listdir(src_dir)):
            if not fn.endswith(".md"):
                continue
            n_md += 1
            path = os.path.join(src_dir, fn)
            text = open(path, encoding="utf-8").read()
            fm, body = tut.parse(text)

            # 1) lint the content
            for e in tut.lint(fm, body):
                problems.append("%s/%s: %s" % (stem, fn, e))

            # 2) front-matter gi/slug must match filename + the real topic
            try:
                gi = int(fn.split("-", 1)[0])
            except ValueError:
                problems.append("%s/%s: filename does not start with NNNN-" % (stem, fn))
                continue
            if gi not in enum:
                problems.append("%s/%s: gi %d not a real topic in this card" % (stem, fn, gi))
                continue
            expect_slug = enum[gi]["slug"]
            if fm.get("slug") != expect_slug:
                problems.append("%s/%s: front-matter slug '%s' != expected '%s'"
                                % (stem, fn, fm.get("slug"), expect_slug))

            # 3) the built HTML page must exist
            page = os.path.join(OUT, "tutorials", stem, "%04d-%s.html" % (gi, expect_slug))
            if os.path.exists(page):
                n_pages += 1
            else:
                problems.append("%s/%s: built page missing (run generate.py): %s"
                                % (stem, fn, os.path.relpath(page, OUT)))

    # next_phase from the manifest, if built
    next_phase = "?"
    man_path = os.path.join(OUT, "content", "_manifest.json")
    if os.path.exists(man_path):
        next_phase = json.load(open(man_path)).get("next_phase")

    if problems:
        print("CHECK FAIL — %d problem(s):" % len(problems))
        for pr in problems:
            print("  - " + pr)
        return 1

    print("CHECK PASS — %d tutorials authored, %d pages built. next_phase: %s"
          % (n_md, n_pages, next_phase))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
