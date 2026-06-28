"""Internal Security. Stages: MAINS/INT. Topic id prefix: is-."""


def _t(tid, text, stages=("MAINS", "INT"), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "internal_security",
    "title": "Internal Security",
    "icon": "🛡",
    "blurb": "Security challenges, extremism, cyber security, border management, security forces. Mains GS-3 + Interview.",
    "category": "Mains GS",
    "sections": [
        {"name": "Internal Security Challenges", "groups": [
            {"name": "Overview", "topics": [
                _t("is-ov-framework", "Internal security — concept and framework"),
                _t("is-ov-stateactors", "Role of external state actors"),
                _t("is-ov-nonstate", "Role of non-state actors"),
                _t("is-ov-linkages", "Linkages of security threats"),
            ]},
        ]},
        {"name": "Extremism & Insurgency", "groups": [
            {"name": "Extremism", "topics": [
                _t("is-ex-lwe", "Left-wing extremism (Naxalism)"),
                _t("is-ex-development", "Development-extremism linkage"),
                _t("is-ex-northeast", "Insurgency in North-East India"),
                _t("is-ex-jk", "Militancy in Jammu & Kashmir"),
                _t("is-ex-counter", "Counter-insurgency strategies"),
                _t("is-ex-radicalization", "Radicalization and de-radicalization"),
            ]},
        ]},
        {"name": "Terrorism", "groups": [
            {"name": "Terrorism", "topics": [
                _t("is-tr-types", "Terrorism — types and causes"),
                _t("is-tr-crossborder", "Cross-border terrorism"),
                _t("is-tr-funding", "Terror financing"),
                _t("is-tr-laws", "Anti-terror laws — UAPA, NIA"),
                _t("is-tr-global", "Global counter-terrorism cooperation"),
            ]},
        ]},
        {"name": "Communication Networks & Media", "groups": [
            {"name": "Media & Security", "topics": [
                _t("is-md-networks", "Communication networks and security"),
                _t("is-md-socialmedia", "Role of social media in security"),
                _t("is-md-misinformation", "Misinformation and propaganda"),
                _t("is-md-basics", "Media's role in internal security challenges"),
            ]},
        ]},
        {"name": "Cyber Security", "groups": [
            {"name": "Cyber", "topics": [
                _t("is-cy-threats", "Cyber threats and attacks"),
                _t("is-cy-warfare", "Cyber warfare and critical infrastructure"),
                _t("is-cy-framework", "Cyber security framework and CERT-In"),
                _t("is-cy-crime", "Cyber crime and digital fraud"),
                _t("is-cy-dataprotection", "Data protection and security"),
            ]},
        ]},
        {"name": "Money Laundering & Economic Offences", "groups": [
            {"name": "Economic Security", "topics": [
                _t("is-ml-laundering", "Money laundering — methods and prevention"),
                _t("is-ml-pmla", "PMLA and FATF"),
                _t("is-ml-counterfeit", "Counterfeit currency and economic offences"),
                _t("is-ml-blackmoney", "Black money and hawala networks"),
            ]},
        ]},
        {"name": "Border Management", "groups": [
            {"name": "Borders", "topics": [
                _t("is-bm-land", "Land border management"),
                _t("is-bm-coastal", "Coastal security (Maharashtra coast)", ("MAINS", "INT"), True),
                _t("is-bm-infiltration", "Infiltration and smuggling"),
                _t("is-bm-organizedcrime", "Organized crime and terrorism nexus"),
                _t("is-bm-trafficking", "Drug and human trafficking"),
            ]},
        ]},
        {"name": "Security Forces & Agencies", "groups": [
            {"name": "Forces", "topics": [
                _t("is-sf-armed", "Armed forces — role in security"),
                _t("is-sf-paramilitary", "Central Armed Police Forces (CAPF)"),
                _t("is-sf-intelligence", "Intelligence agencies — IB, RAW"),
                _t("is-sf-police", "Police reforms and modernization"),
                _t("is-sf-mandate", "Mandate of security agencies"),
                _t("is-sf-disaster", "Forces in disaster response (NDRF)"),
            ]},
        ]},
        {"name": "Emerging Security Issues", "groups": [
            {"name": "Emerging", "topics": [
                _t("is-em-maritime", "Maritime security"),
                _t("is-em-space", "Space and technology security"),
                _t("is-em-energy", "Energy and resource security"),
                _t("is-em-food", "Food and water security as security issues"),
                _t("is-em-climate", "Climate change and security"),
                _t("is-em-ai", "AI, drones and emerging tech threats"),
                _t("is-em-bio", "Biosecurity and pandemic preparedness"),
            ]},
        ]},
        {"name": "Disaster & Civil Defence", "groups": [
            {"name": "Preparedness", "topics": [
                _t("is-dc-civildefence", "Civil defence and home guards"),
                _t("is-dc-criticalinfra", "Protection of critical infrastructure"),
                _t("is-dc-vip", "VIP and event security"),
                _t("is-dc-coordination", "Centre-state coordination in security", ("MAINS",)),
            ]},
        ]},
        {"name": "Security Governance", "groups": [
            {"name": "Governance", "topics": [
                _t("is-sg-policy", "National security policy and doctrine", ("MAINS",)),
                _t("is-sg-nsc", "National Security Council and architecture"),
                _t("is-sg-reforms", "Security sector reforms", ("MAINS",)),
                _t("is-sg-humanrights", "Security vs human rights balance", ("MAINS",)),
                _t("is-sg-community", "Community policing and public cooperation"),
            ]},
        ]},
    ],
}
