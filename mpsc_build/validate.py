"""Structure + coverage gates for MPSC syllabus data. Run: python3 -m mpsc_build.validate"""
import sys
from mpsc_build.syllabus import load_all

VALID_STAGES = {"PRE", "MAINS", "INT"}

# Coverage gate — minimum micro-topics per subject (max-depth guard).
MIN_TOPICS = {
    "ethics": 60,
    "history": 220, "geography": 180, "polity": 200, "economy": 170,
    "environment": 110, "science_tech": 120, "society": 110,
    "international_relations": 70, "internal_security": 70,
    "csat": 70, "language": 50, "essay": 50,
    "current_affairs": 60, "interview": 50, "geography_optional": 200,
}


def validate(subjects):
    errors = []
    seen_ids = set()
    seen_keys = set()
    for s in subjects:
        key = s.get("key")
        if not key or key in seen_keys:
            errors.append(f"bad/duplicate subject key: {key!r}")
        seen_keys.add(key)
        for field in ("title", "icon", "blurb", "category", "sections"):
            if not s.get(field):
                errors.append(f"[{key}] missing field: {field}")
        if not s.get("sections"):
            continue
        topic_count = 0
        for sec in s["sections"]:
            if not sec.get("name") or not sec.get("groups"):
                errors.append(f"[{key}] bad section: {sec.get('name')!r}")
            for grp in sec.get("groups", []):
                if not grp.get("name") or not grp.get("topics"):
                    errors.append(f"[{key}] bad group in {sec.get('name')!r}: {grp.get('name')!r}")
                for t in grp.get("topics", []):
                    topic_count += 1
                    tid = t.get("id")
                    if not tid:
                        errors.append(f"[{key}] topic missing id: {t.get('text')!r}")
                    elif tid in seen_ids:
                        errors.append(f"duplicate topic id: {tid}")
                    seen_ids.add(tid)
                    if not t.get("text"):
                        errors.append(f"[{key}] topic {tid} missing text")
                    stages = set(t.get("stages", []))
                    if not stages or not stages <= VALID_STAGES:
                        errors.append(f"[{key}] topic {tid} bad stages: {t.get('stages')}")
        minimum = MIN_TOPICS.get(key, 1)
        if topic_count < minimum:
            errors.append(f"[{key}] only {topic_count} topics, need >= {minimum} (max-depth coverage gate)")
    return errors


def main():
    errors = validate(load_all())
    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("OK: all syllabus data valid")


if __name__ == "__main__":
    main()
