# -*- coding: utf-8 -*-
"""Build the phase manifest that drives incremental tutorial generation."""
import topics

PHASE_CAP = 12


def _phase_id(stem, tag, idx):
    return "%s/%s#%d" % (stem, tag or "sec", idx)


def build(projects, exists_fn, pilot=None):
    cards = {}
    pending_order = []   # global order of pending phase ids
    pilot_pending = []   # pending phase ids belonging to the pilot card
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
                if pstatus == "pending":
                    pending_order.append(pid)
                    if stem == pilot:
                        pilot_pending.append(pid)
            sections_out.append({"name": name, "tag": tag,
                                 "topics": topics_out, "phases": phases})
        cards[stem] = {"title": proj.get("title", stem), "sections": sections_out}

    # Pilot card finishes first; then fall back to global project order.
    next_phase = (pilot_pending or pending_order or [None])[0]
    return {"cards": cards, "pilot": pilot, "next_phase": next_phase}
