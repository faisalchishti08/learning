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
        have = set(f[:-3] for f in os.listdir(d) if f.endswith(".md")) if os.path.isdir(d) else set()
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
