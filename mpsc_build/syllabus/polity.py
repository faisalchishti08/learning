"""Polity & Governance. Stages: PRE/MAINS/INT; MH = Maharashtra weightage."""


def _t(tid, text, stages=("PRE", "MAINS"), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "polity",
    "title": "Polity & Governance",
    "icon": "P",
    "blurb": "Constitution, Parliament, Judiciary, federalism, local govt, constitutional bodies, governance. Prelims + Mains GS-2 + Interview.",
    "category": "General Studies",
    "sections": [
        {"name": "Constitutional Framework", "groups": [
            {"name": "Making & Sources", "topics": [
                _t("pol-cf-historical", "Historical underpinnings — Acts of 1858-1935"),
                _t("pol-cf-assembly", "Constituent Assembly — composition and working"),
                _t("pol-cf-making", "Making and enactment of the Constitution"),
                _t("pol-cf-sources", "Sources of the Constitution"),
                _t("pol-cf-features", "Salient features of the Constitution"),
                _t("pol-cf-preamble", "Preamble — significance and keywords"),
                _t("pol-cf-basic", "Basic structure doctrine"),
            ]},
            {"name": "Union & Territory", "topics": [
                _t("pol-cf-union", "Union and its territory (Art 1-4)"),
                _t("pol-cf-citizenship", "Citizenship (Art 5-11)"),
                _t("pol-cf-reorg", "Reorganization of states", ("PRE", "MAINS"), True),
                _t("pol-cf-oci", "OCI, PIO and citizenship amendments"),
                _t("pol-cf-parts", "Parts and structure of the Constitution"),
            ]},
        ]},
        {"name": "Fundamental Rights, DPSP & Duties", "groups": [
            {"name": "Fundamental Rights", "topics": [
                _t("pol-fr-overview", "Fundamental Rights — overview (Art 12-35)"),
                _t("pol-fr-equality", "Right to Equality (Art 14-18)"),
                _t("pol-fr-freedom", "Right to Freedom (Art 19-22)"),
                _t("pol-fr-exploitation", "Right against Exploitation (Art 23-24)"),
                _t("pol-fr-religion", "Right to Freedom of Religion (Art 25-28)"),
                _t("pol-fr-cultural", "Cultural and Educational Rights (Art 29-30)"),
                _t("pol-fr-remedies", "Right to Constitutional Remedies (Art 32)"),
                _t("pol-fr-writs", "Writs — habeas corpus, mandamus, prohibition, certiorari, quo-warranto"),
                _t("pol-fr-property", "Right to Property — from FR to legal right"),
                _t("pol-fr-amendability", "Amendability of Fundamental Rights"),
            ]},
            {"name": "DPSP & Duties", "topics": [
                _t("pol-dpsp-overview", "Directive Principles of State Policy (Art 36-51)"),
                _t("pol-dpsp-classification", "Classification of DPSP"),
                _t("pol-dpsp-frvsdpsp", "FR vs DPSP — conflict and harmony"),
                _t("pol-fd-duties", "Fundamental Duties (Art 51A)"),
                _t("pol-dpsp-amendments", "DPSP and constitutional amendments"),
                _t("pol-dpsp-implementation", "Implementation of DPSP — schemes and laws", ("MAINS",)),
            ]},
        ]},
        {"name": "Union Government", "groups": [
            {"name": "Executive", "topics": [
                _t("pol-ue-president", "President — election, powers, functions"),
                _t("pol-ue-vp", "Vice-President"),
                _t("pol-ue-pm", "Prime Minister and Council of Ministers"),
                _t("pol-ue-cabinet", "Cabinet committees and functioning"),
                _t("pol-ue-ag", "Attorney General of India"),
                _t("pol-ue-veto", "President's veto powers and ordinances"),
                _t("pol-ue-pardon", "Pardoning powers of President and Governor"),
            ]},
            {"name": "Parliament", "topics": [
                _t("pol-up-composition", "Parliament — Lok Sabha and Rajya Sabha"),
                _t("pol-up-sessions", "Sessions, sittings and procedures"),
                _t("pol-up-lawmaking", "Law-making process and types of bills"),
                _t("pol-up-budget", "Budget and financial procedure"),
                _t("pol-up-committees", "Parliamentary committees"),
                _t("pol-up-privileges", "Powers, privileges and immunities"),
                _t("pol-up-antidefection", "Anti-defection law (10th Schedule)"),
                _t("pol-up-speaker", "Speaker, Deputy Speaker and officers"),
                _t("pol-up-devices", "Parliamentary devices — question hour, motions, adjournment"),
                _t("pol-up-jointsitting", "Joint sitting and disqualification"),
            ]},
        ]},
        {"name": "State Government", "groups": [
            {"name": "State Executive & Legislature", "topics": [
                _t("pol-se-governor", "Governor — powers and role", ("PRE", "MAINS", "INT"), True),
                _t("pol-se-cm", "Chief Minister and State Council of Ministers", ("PRE", "MAINS"), True),
                _t("pol-se-legislature", "State Legislature — Assembly and Council", ("PRE", "MAINS"), True),
                _t("pol-se-adv-general", "Advocate General of the State"),
                _t("pol-se-mh", "Maharashtra legislature and government structure", ("PRE", "MAINS", "INT"), True),
                _t("pol-se-vidhanparishad", "Maharashtra Vidhan Parishad — composition", ("PRE", "MAINS"), True),
                _t("pol-se-cmoffice", "State Secretariat and administrative setup", ("PRE", "MAINS"), True),
                _t("pol-se-relations", "Governor-CM relations and discretionary powers", ("MAINS",)),
            ]},
        ]},
        {"name": "Judiciary", "groups": [
            {"name": "Courts", "topics": [
                _t("pol-jud-sc", "Supreme Court — composition and jurisdiction"),
                _t("pol-jud-hc", "High Courts"),
                _t("pol-jud-subordinate", "Subordinate courts"),
                _t("pol-jud-review", "Judicial review and judicial activism"),
                _t("pol-jud-pil", "Public Interest Litigation"),
                _t("pol-jud-independence", "Independence of judiciary, collegium, NJAC"),
                _t("pol-jud-tribunals", "Tribunals (Art 323A, 323B)"),
                _t("pol-jud-contempt", "Contempt of court"),
                _t("pol-jud-basicstructure-cases", "Landmark cases — Kesavananda, Minerva Mills, Maneka Gandhi"),
                _t("pol-jud-aor", "Advisory jurisdiction and special leave petition"),
            ]},
        ]},
        {"name": "Federalism & Centre-State Relations", "groups": [
            {"name": "Relations", "topics": [
                _t("pol-fed-features", "Federal features and unitary bias"),
                _t("pol-fed-legislative", "Legislative relations and lists"),
                _t("pol-fed-administrative", "Administrative relations"),
                _t("pol-fed-financial", "Financial relations"),
                _t("pol-fed-interstate", "Inter-state relations and councils"),
                _t("pol-fed-zonal", "Zonal councils and cooperative federalism"),
                _t("pol-fed-disputes", "Centre-state disputes and challenges", ("MAINS",)),
            ]},
            {"name": "Emergency Provisions", "topics": [
                _t("pol-em-national", "National Emergency (Art 352)"),
                _t("pol-em-president", "President's Rule (Art 356)"),
                _t("pol-em-financial", "Financial Emergency (Art 360)"),
            ]},
        ]},
        {"name": "Local Self-Government", "groups": [
            {"name": "Panchayati Raj & Urban", "topics": [
                _t("pol-lsg-73", "73rd Amendment and Panchayati Raj"),
                _t("pol-lsg-74", "74th Amendment and urban local bodies"),
                _t("pol-lsg-structure", "Three-tier structure and functions"),
                _t("pol-lsg-finance", "Finances and State Finance Commission"),
                _t("pol-lsg-mh", "Maharashtra local government — ZP, Panchayat Samiti, Gram Panchayat", ("PRE", "MAINS", "INT"), True),
                _t("pol-lsg-mh-urban", "Municipal corporations and councils in Maharashtra", ("PRE", "MAINS"), True),
                _t("pol-lsg-pesa", "PESA Act and tribal areas"),
            ]},
        ]},
        {"name": "Constitutional Bodies", "groups": [
            {"name": "Constitutional Bodies", "topics": [
                _t("pol-cb-eci", "Election Commission of India"),
                _t("pol-cb-upsc", "UPSC and State PSCs (MPSC)", ("PRE", "MAINS"), True),
                _t("pol-cb-fc", "Finance Commission"),
                _t("pol-cb-cag", "Comptroller and Auditor General"),
                _t("pol-cb-ag", "Attorney General and Advocate General"),
                _t("pol-cb-scst", "National Commissions for SC, ST, BC"),
                _t("pol-cb-language", "Special Officer for Linguistic Minorities"),
                _t("pol-cb-gststcouncil", "GST Council and inter-state institutions"),
            ]},
        ]},
        {"name": "Statutory & Regulatory Bodies", "groups": [
            {"name": "Non-Constitutional Bodies", "topics": [
                _t("pol-sb-niti", "NITI Aayog"),
                _t("pol-sb-nhrc", "National Human Rights Commission"),
                _t("pol-sb-cic", "Central Information Commission"),
                _t("pol-sb-cvc", "Central Vigilance Commission"),
                _t("pol-sb-cbi", "CBI and investigative agencies"),
                _t("pol-sb-lokpal", "Lokpal and Lokayukta", ("PRE", "MAINS"), True),
                _t("pol-sb-ncw", "National Commission for Women"),
                _t("pol-sb-regulators", "Regulatory bodies — RBI, SEBI, TRAI, CCI"),
            ]},
        ]},
        {"name": "Elections & Representation", "groups": [
            {"name": "Elections", "topics": [
                _t("pol-el-rpa", "Representation of People's Act — features"),
                _t("pol-el-process", "Electoral process and reforms"),
                _t("pol-el-parties", "Political parties and party system"),
                _t("pol-el-evm", "EVM, VVPAT and electoral funding"),
                _t("pol-el-pressure", "Pressure groups and interest groups", ("MAINS",)),
                _t("pol-el-model", "Model Code of Conduct"),
                _t("pol-el-delimitation", "Delimitation and reservation of seats"),
                _t("pol-el-criminalisation", "Criminalisation of politics and reforms", ("MAINS",)),
                _t("pol-el-statefunding", "State funding and electoral bonds", ("MAINS",)),
            ]},
        ]},
        {"name": "Constitutional Amendments", "groups": [
            {"name": "Key Amendments", "topics": [
                _t("pol-am-process", "Amendment procedure (Art 368)"),
                _t("pol-am-1st", "1st Amendment (1951)"),
                _t("pol-am-7th", "7th Amendment — states reorganization"),
                _t("pol-am-42nd", "42nd Amendment (1976)"),
                _t("pol-am-44th", "44th Amendment (1978)"),
                _t("pol-am-52nd", "52nd Amendment — anti-defection"),
                _t("pol-am-61st", "61st Amendment — voting age"),
                _t("pol-am-73-74", "73rd & 74th Amendments — local govt"),
                _t("pol-am-86th", "86th Amendment — right to education"),
                _t("pol-am-101st", "101st Amendment — GST"),
                _t("pol-am-103rd", "103rd Amendment — EWS reservation"),
                _t("pol-am-recent", "Recent amendments and significance"),
                _t("pol-am-91st", "91st Amendment — size of council of ministers"),
                _t("pol-am-97th", "97th Amendment — cooperative societies", ("PRE", "MAINS"), True),
                _t("pol-am-100th", "100th Amendment — land boundary agreement"),
                _t("pol-am-102nd", "102nd Amendment — National Commission for BC"),
                _t("pol-am-105th", "105th Amendment — states' power on OBC list"),
            ]},
        ]},
        {"name": "Governance", "groups": [
            {"name": "Governance & Accountability", "topics": [
                _t("pol-gov-transparency", "Transparency and accountability", ("MAINS", "INT")),
                _t("pol-gov-rti", "Right to Information Act", ("PRE", "MAINS", "INT")),
                _t("pol-gov-egovernance", "E-governance — models and initiatives", ("MAINS",)),
                _t("pol-gov-charter", "Citizen's charters", ("MAINS",)),
                _t("pol-gov-civilservices", "Role of civil services in democracy", ("MAINS", "INT")),
                _t("pol-gov-reforms", "Administrative reforms (2nd ARC)", ("MAINS",)),
                _t("pol-gov-corruption", "Corruption and measures against it", ("MAINS", "INT")),
                _t("pol-gov-policy", "Public policy formulation and implementation", ("MAINS",)),
                _t("pol-gov-socialaudit", "Social audit and grievance redressal", ("MAINS",)),
                _t("pol-gov-dbt", "Direct Benefit Transfer and Aadhaar governance", ("MAINS",)),
                _t("pol-gov-cooperative", "Citizen participation and good governance", ("MAINS", "INT")),
            ]},
            {"name": "Welfare & Social Justice", "topics": [
                _t("pol-sj-vulnerable", "Welfare mechanisms for vulnerable sections", ("MAINS",)),
                _t("pol-sj-ngo", "NGOs, SHGs and civil society in governance", ("MAINS",)),
                _t("pol-sj-schemes", "Government schemes — design and delivery", ("PRE", "MAINS")),
            ]},
        ]},
        {"name": "Comparative & Political Concepts", "groups": [
            {"name": "Concepts", "topics": [
                _t("pol-pc-comparison", "Comparison with other constitutions", ("MAINS",)),
                _t("pol-pc-separation", "Separation of powers and checks/balances", ("MAINS",)),
                _t("pol-pc-ruleoflaw", "Rule of law and constitutionalism", ("MAINS",)),
                _t("pol-pc-secularism", "Indian secularism", ("MAINS",)),
                _t("pol-pc-democracy", "Democracy and democratic decentralization", ("MAINS",)),
            ]},
        ]},
        {"name": "Schedules & Special Provisions", "groups": [
            {"name": "Schedules", "topics": [
                _t("pol-sch-overview", "Twelve Schedules of the Constitution"),
                _t("pol-sch-5-6", "Fifth and Sixth Schedules — tribal areas"),
                _t("pol-sch-8", "Eighth Schedule — languages"),
                _t("pol-sp-special", "Special provisions for states (Art 371, 371(2) Maharashtra)", ("PRE", "MAINS"), True),
                _t("pol-sp-scst", "Reservation and provisions for SC/ST/OBC"),
                _t("pol-sp-anglo", "Provisions for minorities and Anglo-Indians"),
            ]},
        ]},
        {"name": "Rights Bodies & Tribunals", "groups": [
            {"name": "Other Bodies", "topics": [
                _t("pol-ob-ncm", "National Commission for Minorities"),
                _t("pol-ob-ncpcr", "National Commission for Protection of Child Rights"),
                _t("pol-ob-ngt", "National Green Tribunal"),
                _t("pol-ob-cat", "Central Administrative Tribunal"),
                _t("pol-ob-statehrc", "State Human Rights Commissions and Lokayukta (Maharashtra)", ("PRE", "MAINS"), True),
            ]},
        ]},
        {"name": "Public Administration & Civil Services", "groups": [
            {"name": "Administration", "topics": [
                _t("pol-pa-structure", "Structure of Indian administration — Union, State, district", ("MAINS",)),
                _t("pol-pa-allindia", "All India Services and Central Services"),
                _t("pol-pa-district", "District administration — Collector and DM", ("MAINS",), True),
                _t("pol-pa-recruitment", "Recruitment, training and conduct rules"),
                _t("pol-pa-generalist", "Generalist vs specialist debate", ("MAINS",)),
                _t("pol-pa-neutrality", "Political neutrality and accountability", ("MAINS",)),
                _t("pol-pa-arc", "Administrative Reforms Commission recommendations", ("MAINS",)),
            ]},
        ]},
        {"name": "Rights & Social Justice Provisions", "groups": [
            {"name": "Rights Framework", "topics": [
                _t("pol-rj-humanrights", "Human rights framework in India", ("MAINS",)),
                _t("pol-rj-childrights", "Child rights and protection laws"),
                _t("pol-rj-disability", "Rights of persons with disabilities"),
                _t("pol-rj-minorityrights", "Minority rights and safeguards"),
                _t("pol-rj-rti-detail", "RTI — provisions, exemptions, amendments"),
                _t("pol-rj-cpc", "Consumer Protection and citizen rights"),
            ]},
        ]},
        {"name": "International & Cooperative Polity", "groups": [
            {"name": "External Dimension", "topics": [
                _t("pol-int-treaties", "Treaty-making powers and parliamentary oversight", ("MAINS",)),
                _t("pol-int-emergency-judicial", "Judicial pronouncements shaping polity", ("MAINS",)),
                _t("pol-int-coalition", "Coalition politics and governance", ("MAINS",)),
            ]},
        ]},
    ],
}
