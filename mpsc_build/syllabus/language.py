"""Language Papers (Marathi + English, Mains qualifying). Stages: MAINS."""


def _t(tid, text, stages=("MAINS",), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "language",
    "title": "Language Papers (Marathi + English)",
    "icon": "✍",
    "blurb": "Comprehension, precis, grammar, vocabulary, essays, translation. Mains qualifying papers (Paper 1 & 2).",
    "category": "Mains Qualifying",
    "sections": [
        {"name": "Marathi — Comprehension & Writing", "groups": [
            {"name": "Marathi Skills", "topics": [
                _t("lang-mr-comprehension", "Comprehension of Marathi passages", ("MAINS",), True),
                _t("lang-mr-precis", "Precis writing in Marathi", ("MAINS",), True),
                _t("lang-mr-essay", "Short essays in Marathi", ("MAINS",), True),
                _t("lang-mr-letter", "Letter and report writing", ("MAINS",), True),
                _t("lang-mr-expansion", "Expansion of ideas", ("MAINS",), True),
            ]},
            {"name": "Marathi Grammar (व्याकरण)", "topics": [
                _t("lang-mr-shabdjati", "Shabd-jati (parts of speech)", ("MAINS",), True),
                _t("lang-mr-sandhi", "Sandhi and samas", ("MAINS",), True),
                _t("lang-mr-vibhakti", "Vibhakti (cases)", ("MAINS",), True),
                _t("lang-mr-kaal", "Kaal (tenses)", ("MAINS",), True),
                _t("lang-mr-alankar", "Alankar and vakprachar", ("MAINS",), True),
                _t("lang-mr-vipreet", "Synonyms, antonyms, idioms", ("MAINS",), True),
                _t("lang-mr-shudhlekhan", "Shuddhalekhan (spelling rules)", ("MAINS",), True),
            ]},
            {"name": "Marathi Vocabulary & Translation", "topics": [
                _t("lang-mr-vocabulary", "Vocabulary and usage", ("MAINS",), True),
                _t("lang-mr-translation", "Translation English to Marathi", ("MAINS",), True),
            ]},
        ]},
        {"name": "English — Comprehension & Writing", "groups": [
            {"name": "English Skills", "topics": [
                _t("lang-en-comprehension", "Comprehension of English passages"),
                _t("lang-en-precis", "Precis writing in English"),
                _t("lang-en-essay", "Short essays in English"),
                _t("lang-en-letter", "Letter and report writing"),
                _t("lang-en-paragraph", "Paragraph writing"),
            ]},
            {"name": "English Grammar", "topics": [
                _t("lang-en-tenses", "Tenses"),
                _t("lang-en-voice", "Active and passive voice"),
                _t("lang-en-narration", "Direct and indirect narration"),
                _t("lang-en-articles", "Articles and determiners"),
                _t("lang-en-prepositions", "Prepositions"),
                _t("lang-en-subjectverb", "Subject-verb agreement"),
                _t("lang-en-clauses", "Clauses and sentence structure"),
                _t("lang-en-errors", "Spotting errors and corrections"),
            ]},
            {"name": "English Vocabulary & Translation", "topics": [
                _t("lang-en-vocabulary", "Vocabulary, synonyms, antonyms"),
                _t("lang-en-idioms", "Idioms and phrases"),
                _t("lang-en-translation", "Translation Marathi to English", ("MAINS",), True),
            ]},
        ]},
        {"name": "Common Skills", "groups": [
            {"name": "Writing Practice", "topics": [
                _t("lang-cm-summarizing", "Summarizing and paraphrasing"),
                _t("lang-cm-coherence", "Coherence and cohesion in writing"),
                _t("lang-cm-formal", "Formal vs informal register"),
                _t("lang-cm-timemanagement", "Time management in language papers"),
                _t("lang-cm-practice", "Previous year papers practice"),
                _t("lang-cm-handwriting", "Handwriting and presentation"),
                _t("lang-cm-wordlimit", "Word-limit and answer structuring"),
            ]},
        ]},
        {"name": "Marathi Literature Basics (for language)", "groups": [
            {"name": "Literary Appreciation", "topics": [
                _t("lang-ml-prose", "Prose appreciation and comprehension", ("MAINS",), True),
                _t("lang-ml-poetry", "Poetry appreciation", ("MAINS",), True),
                _t("lang-ml-figures", "Figures of speech in Marathi", ("MAINS",), True),
                _t("lang-ml-proverbs", "Proverbs and idiomatic usage", ("MAINS",), True),
            ]},
        ]},
        {"name": "English Composition Detail", "groups": [
            {"name": "Composition", "topics": [
                _t("lang-ec-sentence", "Sentence transformation and rearrangement"),
                _t("lang-ec-clozetest", "Cloze test and fill-ups"),
                _t("lang-ec-onewords", "One-word substitution"),
                _t("lang-ec-confusable", "Commonly confused words"),
            ]},
        ]},
    ],
}
