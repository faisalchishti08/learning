"""Current Affairs framework (recurring trackable buckets). Stages: PRE/MAINS/INT; MH."""


def _t(tid, text, stages=("PRE", "MAINS", "INT"), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "current_affairs",
    "title": "Current Affairs",
    "icon": "📰",
    "blurb": "Recurring trackable buckets — schemes, reports, persons, awards, summits, Maharashtra affairs. Prelims + Mains + Interview.",
    "category": "Cross-Cutting",
    "sections": [
        {"name": "Government Schemes", "groups": [
            {"name": "Central Schemes", "topics": [
                _t("ca-sc-agriculture", "Agriculture and farmer schemes"),
                _t("ca-sc-health", "Health and nutrition schemes"),
                _t("ca-sc-education", "Education and skill schemes"),
                _t("ca-sc-women", "Women and child welfare schemes"),
                _t("ca-sc-employment", "Employment and livelihood schemes"),
                _t("ca-sc-housing", "Housing and urban schemes"),
                _t("ca-sc-financial", "Financial inclusion schemes"),
                _t("ca-sc-infrastructure", "Infrastructure and energy schemes"),
            ]},
            {"name": "Maharashtra Schemes", "topics": [
                _t("ca-mh-schemes", "Maharashtra state schemes tracker", ("PRE", "MAINS", "INT"), True),
                _t("ca-mh-agri", "Maharashtra agriculture/irrigation schemes", ("PRE", "MAINS", "INT"), True),
                _t("ca-mh-welfare", "Maharashtra welfare and women schemes", ("PRE", "MAINS", "INT"), True),
            ]},
        ]},
        {"name": "Reports & Indices", "groups": [
            {"name": "Reports", "topics": [
                _t("ca-ri-global", "Global indices (HDI, Hunger, Happiness, EoDB)"),
                _t("ca-ri-economic", "Economic reports (Economic Survey, RBI, IMF)"),
                _t("ca-ri-environment", "Environment reports (IPCC, SoE)"),
                _t("ca-ri-national", "National reports (NITI Aayog, NCRB, ASER)"),
                _t("ca-ri-social", "Social and health indices"),
            ]},
        ]},
        {"name": "Persons & Appointments", "groups": [
            {"name": "Persons in News", "topics": [
                _t("ca-pn-appointments", "Key national appointments"),
                _t("ca-pn-constitutional", "Constitutional and statutory post-holders"),
                _t("ca-pn-international", "International leaders and appointments"),
                _t("ca-pn-obituaries", "Notable obituaries"),
                _t("ca-pn-mh", "Maharashtra administration and leaders", ("PRE", "MAINS", "INT"), True),
            ]},
        ]},
        {"name": "Awards & Honours", "groups": [
            {"name": "Awards", "topics": [
                _t("ca-aw-civilian", "Civilian awards (Padma, Bharat Ratna)"),
                _t("ca-aw-international", "International awards (Nobel, etc.)"),
                _t("ca-aw-literature", "Literature and arts awards"),
                _t("ca-aw-gallantry", "Gallantry and service awards"),
            ]},
        ]},
        {"name": "Sports", "groups": [
            {"name": "Sports", "topics": [
                _t("ca-sp-olympics", "Olympics and major multi-sport events"),
                _t("ca-sp-cricket", "Cricket and team sports"),
                _t("ca-sp-individual", "Individual sports and champions"),
                _t("ca-sp-awards", "Sports awards and records"),
            ]},
        ]},
        {"name": "Summits & Events", "groups": [
            {"name": "Summits", "topics": [
                _t("ca-su-international", "International summits and conferences"),
                _t("ca-su-bilateral", "Bilateral visits and agreements"),
                _t("ca-su-multilateral", "Multilateral grouping meetings"),
                _t("ca-su-national", "National events and conferences"),
            ]},
        ]},
        {"name": "Economy & S&T in News", "groups": [
            {"name": "Economy News", "topics": [
                _t("ca-en-policy", "Economic policy and budget updates"),
                _t("ca-en-banking", "Banking and financial news"),
                _t("ca-en-trade", "Trade and investment news"),
            ]},
            {"name": "Science News", "topics": [
                _t("ca-sn-space", "Space and ISRO missions in news"),
                _t("ca-sn-defence", "Defence acquisitions and exercises"),
                _t("ca-sn-technology", "Technology and innovation news"),
                _t("ca-sn-health", "Health and biotech news"),
            ]},
        ]},
        {"name": "Environment & Maharashtra News", "groups": [
            {"name": "Environment News", "topics": [
                _t("ca-ev-conservation", "Conservation and biodiversity news"),
                _t("ca-ev-climate", "Climate and disaster news"),
                _t("ca-ev-species", "Species and protected areas in news"),
            ]},
            {"name": "Maharashtra Affairs", "topics": [
                _t("ca-mha-budget", "Maharashtra budget and policies", ("PRE", "MAINS", "INT"), True),
                _t("ca-mha-events", "Maharashtra events and developments", ("PRE", "MAINS", "INT"), True),
                _t("ca-mha-projects", "Major projects in Maharashtra", ("PRE", "MAINS", "INT"), True),
            ]},
        ]},
        {"name": "Polity & International News", "groups": [
            {"name": "Polity News", "topics": [
                _t("ca-pol-bills", "Important bills and acts"),
                _t("ca-pol-judgments", "Landmark judgments"),
                _t("ca-pol-amendments", "Constitutional and policy changes"),
            ]},
            {"name": "International News", "topics": [
                _t("ca-in-conflicts", "Global conflicts and developments"),
                _t("ca-in-organizations", "International organizations news"),
                _t("ca-in-economy", "Global economic developments"),
            ]},
        ]},
        {"name": "Days, Themes & Misc", "groups": [
            {"name": "Misc Trackers", "topics": [
                _t("ca-mc-days", "Important national and international days"),
                _t("ca-mc-themes", "Year/day themes and observances"),
                _t("ca-mc-firstevents", "First/biggest/longest in news"),
                _t("ca-mc-books", "Books and authors in news"),
                _t("ca-mc-defence-exercises", "Defence exercises and operations"),
                _t("ca-mc-apps", "Government apps, portals and initiatives"),
            ]},
        ]},
        {"name": "Geographical Indications & Heritage", "groups": [
            {"name": "GI & Heritage", "topics": [
                _t("ca-gi-tags", "Geographical Indication (GI) tags"),
                _t("ca-gi-mh", "GI tags and heritage of Maharashtra", ("PRE", "MAINS", "INT"), True),
                _t("ca-gi-unesco", "New UNESCO sites and recognitions"),
                _t("ca-gi-ramsar", "New Ramsar sites and protected areas"),
            ]},
        ]},
    ],
}
