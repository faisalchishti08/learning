# -*- coding: utf-8 -*-
"""Stable topic identity helpers: gi enumeration, slugs, page paths."""
import re
import unicodedata


def slugify(text):
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
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
