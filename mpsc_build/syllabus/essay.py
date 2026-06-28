"""Essay (Mains Paper 3). Stages: MAINS; MH = Maharashtra themes."""


def _t(tid, text, stages=("MAINS",), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "essay",
    "title": "Essay",
    "icon": "📝",
    "blurb": "Essay technique and theme banks across philosophy, society, economy, polity, environment, S&T, Maharashtra. Mains Paper 3.",
    "category": "Mains GS",
    "sections": [
        {"name": "Essay Technique", "groups": [
            {"name": "Writing Craft", "topics": [
                _t("essay-tq-structure", "Essay structure — introduction, body, conclusion"),
                _t("essay-tq-brainstorm", "Brainstorming and mind-mapping"),
                _t("essay-tq-thesis", "Building a thesis and argument flow"),
                _t("essay-tq-intro", "Writing engaging introductions"),
                _t("essay-tq-conclusion", "Writing impactful conclusions"),
                _t("essay-tq-coherence", "Coherence, flow and paragraphing"),
                _t("essay-tq-multidimensional", "Multi-dimensional analysis"),
                _t("essay-tq-quotes", "Using quotes, examples and data"),
                _t("essay-tq-balance", "Balanced and nuanced argumentation"),
                _t("essay-tq-language", "Language, tone and word limit"),
            ]},
        ]},
        {"name": "Philosophical & Abstract Themes", "groups": [
            {"name": "Abstract", "topics": [
                _t("essay-ph-values", "Ethics, values and morality themes"),
                _t("essay-ph-quotes", "Quote-based abstract topics"),
                _t("essay-ph-life", "Life, success and human nature"),
                _t("essay-ph-knowledge", "Knowledge, wisdom and education"),
                _t("essay-ph-dualities", "Dualities (tradition vs modernity etc.)"),
            ]},
        ]},
        {"name": "Social Themes", "groups": [
            {"name": "Society", "topics": [
                _t("essay-so-women", "Women and gender themes"),
                _t("essay-so-youth", "Youth, education and society"),
                _t("essay-so-inequality", "Social justice and inequality"),
                _t("essay-so-diversity", "Diversity, unity and culture"),
                _t("essay-so-family", "Family, community and social change"),
            ]},
        ]},
        {"name": "Economic Themes", "groups": [
            {"name": "Economy", "topics": [
                _t("essay-ec-development", "Growth, development and inclusion"),
                _t("essay-ec-poverty", "Poverty, unemployment and welfare"),
                _t("essay-ec-globalization", "Globalization and economy"),
                _t("essay-ec-agriculture", "Agriculture and rural economy"),
                _t("essay-ec-technology-econ", "Technology and future of work"),
            ]},
        ]},
        {"name": "Polity & Governance Themes", "groups": [
            {"name": "Polity", "topics": [
                _t("essay-pl-democracy", "Democracy and governance"),
                _t("essay-pl-rights", "Rights, duties and citizenship"),
                _t("essay-pl-corruption", "Corruption and accountability"),
                _t("essay-pl-federalism", "Federalism and decentralization"),
                _t("essay-pl-reforms", "Administrative and electoral reforms"),
            ]},
        ]},
        {"name": "Environment & S&T Themes", "groups": [
            {"name": "Environment", "topics": [
                _t("essay-en-climate", "Climate change and sustainability"),
                _t("essay-en-development", "Environment vs development"),
                _t("essay-en-conservation", "Conservation and biodiversity"),
            ]},
            {"name": "Science & Technology", "topics": [
                _t("essay-st-ai", "AI, automation and society"),
                _t("essay-st-digital", "Digital revolution and ethics"),
                _t("essay-st-space", "Science, innovation and progress"),
            ]},
        ]},
        {"name": "Maharashtra & Regional Themes", "groups": [
            {"name": "Maharashtra", "topics": [
                _t("essay-mh-reform", "Maharashtra's social reform legacy", ("MAINS",), True),
                _t("essay-mh-development", "Regional development and disparities", ("MAINS",), True),
                _t("essay-mh-culture", "Maharashtra culture and identity", ("MAINS",), True),
            ]},
        ]},
        {"name": "Practice Topic Bank", "groups": [
            {"name": "Practice", "topics": [
                _t("essay-pr-current", "Current-affairs based essay topics"),
                _t("essay-pr-international", "International and global themes"),
                _t("essay-pr-mock", "Timed essay practice and review"),
                _t("essay-pr-pyqs", "Previous year essay topics analysis"),
            ]},
        ]},
        {"name": "Additional Theme Banks", "groups": [
            {"name": "More Themes", "topics": [
                _t("essay-at-health", "Health, pandemic and public welfare themes"),
                _t("essay-at-education", "Education and knowledge society themes"),
                _t("essay-at-internalsecurity", "Security and nationalism themes"),
                _t("essay-at-agriculture", "Agriculture and rural India themes"),
                _t("essay-at-international", "Globalization and world order themes"),
                _t("essay-at-governance", "Reforms and good governance themes"),
            ]},
        ]},
    ],
}
