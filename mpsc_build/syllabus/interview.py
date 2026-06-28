"""Interview / Personality Test. Stages: INT; MH = Maharashtra."""


def _t(tid, text, stages=("INT",), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "interview",
    "title": "Interview / Personality Test",
    "icon": "🎤",
    "blurb": "DAF prep, Maharashtra deep-dive, opinion bank, situational questions, mock-interview checklist. Final stage.",
    "category": "Interview",
    "sections": [
        {"name": "DAF Preparation", "groups": [
            {"name": "Detailed Application Form", "topics": [
                _t("int-daf-bio", "Name, meaning and personal background"),
                _t("int-daf-education", "Educational background and subjects"),
                _t("int-daf-graduation", "Graduation subject — deep questions"),
                _t("int-daf-work", "Work experience (if any)"),
                _t("int-daf-whycivil", "Why civil services — motivation"),
                _t("int-daf-service", "Service and cadre preferences"),
                _t("int-daf-achievements", "Achievements and positions held"),
                _t("int-daf-strengths", "Strengths, weaknesses and self-assessment"),
            ]},
        ]},
        {"name": "Home District & Maharashtra", "groups": [
            {"name": "Local & State Awareness", "topics": [
                _t("int-mh-district", "Home district profile — history, geography, economy", ("INT",), True),
                _t("int-mh-issues", "Local issues and developmental challenges", ("INT",), True),
                _t("int-mh-administration", "Maharashtra administration and structure", ("INT",), True),
                _t("int-mh-schemes", "Key Maharashtra schemes and policies", ("INT",), True),
                _t("int-mh-culture", "Maharashtra culture, history and personalities", ("INT",), True),
                _t("int-mh-current", "Maharashtra current affairs and politics", ("INT",), True),
            ]},
        ]},
        {"name": "Hobbies & Optional Defence", "groups": [
            {"name": "Personal Interests", "topics": [
                _t("int-hb-hobbies", "Hobbies — depth and discussion"),
                _t("int-hb-extracurricular", "Extracurricular activities"),
                _t("int-hb-geography", "Geography optional — defending choice", ("INT",), True),
                _t("int-hb-currentlinks", "Linking hobbies to current affairs"),
            ]},
        ]},
        {"name": "Current Affairs Opinion Bank", "groups": [
            {"name": "Opinions & Stance", "topics": [
                _t("int-op-national", "Stance on national issues"),
                _t("int-op-international", "Views on international developments"),
                _t("int-op-economy", "Opinion on economic policies"),
                _t("int-op-social", "Views on social issues"),
                _t("int-op-controversial", "Handling controversial topics neutrally"),
                _t("int-op-maharashtra", "Opinions on Maharashtra-specific issues", ("INT",), True),
            ]},
        ]},
        {"name": "Situational & Ethical Questions", "groups": [
            {"name": "Scenarios", "topics": [
                _t("int-si-administrative", "Administrative situational questions"),
                _t("int-si-ethical", "Ethical dilemma questions"),
                _t("int-si-pressure", "Handling pressure and conflict scenarios"),
                _t("int-si-decision", "Decision-making under constraints"),
            ]},
        ]},
        {"name": "Personality & Communication", "groups": [
            {"name": "Soft Skills", "topics": [
                _t("int-pc-bodylanguage", "Body language and posture"),
                _t("int-pc-communication", "Clarity and communication skills"),
                _t("int-pc-confidence", "Confidence and composure"),
                _t("int-pc-honesty", "Honesty and admitting unknowns"),
                _t("int-pc-listening", "Listening and responding"),
                _t("int-pc-dress", "Dress code and first impression"),
            ]},
        ]},
        {"name": "Mock Interview & Logistics", "groups": [
            {"name": "Preparation", "topics": [
                _t("int-mk-mock", "Mock interviews and feedback"),
                _t("int-mk-panel", "Understanding the interview panel"),
                _t("int-mk-marks", "Interview marks and weightage"),
                _t("int-mk-documents", "Document verification and logistics"),
                _t("int-mk-revision", "Final revision strategy"),
                _t("int-mk-newspaper", "Daily newspaper and editorial reading"),
            ]},
        ]},
        {"name": "Knowledge Areas", "groups": [
            {"name": "Awareness", "topics": [
                _t("int-ka-governance", "Governance and public administration awareness"),
                _t("int-ka-constitution", "Constitutional values and civil service ethics"),
                _t("int-ka-economy", "Basic economic and social awareness"),
                _t("int-ka-history", "History and culture quick awareness"),
            ]},
        ]},
    ],
}
