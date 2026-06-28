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
    for sub in load_all():
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
