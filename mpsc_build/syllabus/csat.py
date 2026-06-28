"""CSAT / Aptitude (Prelims Paper 2). Stages: PRE."""


def _t(tid, text, stages=("PRE",), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "csat",
    "title": "CSAT / Aptitude (Prelims Paper 2)",
    "icon": "🧮",
    "blurb": "Comprehension, reasoning, mental ability, numeracy, data interpretation. Prelims qualifying paper.",
    "category": "Prelims",
    "sections": [
        {"name": "Comprehension", "groups": [
            {"name": "Reading Comprehension", "topics": [
                _t("csat-cm-passages", "Reading and understanding passages"),
                _t("csat-cm-inference", "Drawing inferences and conclusions"),
                _t("csat-cm-maintheme", "Identifying main theme and tone"),
                _t("csat-cm-vocabulary", "Contextual vocabulary"),
                _t("csat-cm-marathi", "Marathi comprehension passages"),
                _t("csat-cm-english", "English comprehension passages"),
            ]},
        ]},
        {"name": "Interpersonal & Communication", "groups": [
            {"name": "Communication", "topics": [
                _t("csat-ic-skills", "Interpersonal and communication skills"),
                _t("csat-ic-decisionmaking", "Communication in decision-making"),
            ]},
        ]},
        {"name": "Logical Reasoning & Analytical Ability", "groups": [
            {"name": "Reasoning", "topics": [
                _t("csat-lr-syllogism", "Syllogisms"),
                _t("csat-lr-statements", "Statements and assumptions/arguments"),
                _t("csat-lr-arrangements", "Seating and linear arrangements"),
                _t("csat-lr-puzzles", "Puzzles and logical deductions"),
                _t("csat-lr-venn", "Venn diagrams"),
                _t("csat-lr-cause", "Cause and effect, course of action"),
                _t("csat-lr-analytical", "Analytical reasoning"),
                _t("csat-lr-datasufficiency", "Logical data sufficiency"),
                _t("csat-lr-inequalities", "Coded inequalities"),
                _t("csat-lr-input", "Input-output and machine logic"),
            ]},
        ]},
        {"name": "Decision-Making & Problem-Solving", "groups": [
            {"name": "Decision-Making", "topics": [
                _t("csat-dm-scenarios", "Decision-making scenarios"),
                _t("csat-dm-problemsolving", "Problem-solving approaches"),
                _t("csat-dm-ethics", "Ethical decision-making in administration"),
            ]},
        ]},
        {"name": "General Mental Ability", "groups": [
            {"name": "Mental Ability", "topics": [
                _t("csat-ma-series", "Number and letter series"),
                _t("csat-ma-coding", "Coding-decoding"),
                _t("csat-ma-bloodrelations", "Blood relations"),
                _t("csat-ma-direction", "Direction sense"),
                _t("csat-ma-ranking", "Ranking and ordering"),
                _t("csat-ma-clocks", "Clocks and calendars"),
                _t("csat-ma-analogy", "Analogy and classification"),
                _t("csat-ma-oddone", "Odd one out"),
                _t("csat-ma-mirror", "Mirror and water images"),
                _t("csat-ma-paperfolding", "Paper folding and cutting"),
                _t("csat-ma-cubes", "Cubes and dice"),
            ]},
        ]},
        {"name": "Basic Numeracy (Class X)", "groups": [
            {"name": "Arithmetic", "topics": [
                _t("csat-nm-numbersystem", "Number system and HCF/LCM"),
                _t("csat-nm-percentage", "Percentages"),
                _t("csat-nm-ratio", "Ratio and proportion"),
                _t("csat-nm-average", "Averages"),
                _t("csat-nm-profitloss", "Profit, loss and discount"),
                _t("csat-nm-interest", "Simple and compound interest"),
                _t("csat-nm-timework", "Time and work"),
                _t("csat-nm-timespeed", "Time, speed and distance"),
                _t("csat-nm-partnership", "Partnership and mixtures"),
            ]},
            {"name": "Algebra & Geometry", "topics": [
                _t("csat-nm-algebra", "Basic algebra and equations"),
                _t("csat-nm-mensuration", "Mensuration — area and volume"),
                _t("csat-nm-geometry", "Geometry basics"),
                _t("csat-nm-progression", "Progressions"),
            ]},
            {"name": "Modern Maths", "topics": [
                _t("csat-nm-permutation", "Permutations and combinations"),
                _t("csat-nm-probability", "Probability"),
                _t("csat-nm-sets", "Sets and basic counting"),
            ]},
        ]},
        {"name": "Data Interpretation", "groups": [
            {"name": "Data Interpretation", "topics": [
                _t("csat-di-tables", "Tables"),
                _t("csat-di-bar", "Bar graphs"),
                _t("csat-di-line", "Line graphs"),
                _t("csat-di-pie", "Pie charts"),
                _t("csat-di-caselet", "Caselets and mixed data"),
                _t("csat-di-sufficiency", "Data sufficiency"),
                _t("csat-di-interpretation", "Interpretation and approximation"),
                _t("csat-di-radar", "Radar and mixed charts"),
                _t("csat-di-comparison", "Comparison and growth-rate problems"),
            ]},
        ]},
        {"name": "Verbal & Non-Verbal Reasoning", "groups": [
            {"name": "Reasoning Detail", "topics": [
                _t("csat-vr-statementconclusion", "Statement and conclusion"),
                _t("csat-vr-assumptions", "Statement and assumptions"),
                _t("csat-vr-strongweak", "Strong and weak arguments"),
                _t("csat-vr-courseofaction", "Course of action"),
                _t("csat-vr-figureseries", "Figure series and pattern completion"),
                _t("csat-vr-embedded", "Embedded and hidden figures"),
            ]},
        ]},
        {"name": "Exam Strategy", "groups": [
            {"name": "Strategy", "topics": [
                _t("csat-st-timemanagement", "Time management in CSAT"),
                _t("csat-st-elimination", "Elimination and approximation techniques"),
                _t("csat-st-practice", "Previous year papers and mock tests"),
            ]},
        ]},
    ],
}
