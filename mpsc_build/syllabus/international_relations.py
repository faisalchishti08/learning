"""International Relations. Stages: MAINS/INT."""


def _t(tid, text, stages=("MAINS", "INT"), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "international_relations",
    "title": "International Relations",
    "icon": "🌐",
    "blurb": "India & neighbourhood, bilateral ties, groupings, international institutions, diaspora. Mains GS-2 + Interview.",
    "category": "Mains GS",
    "sections": [
        {"name": "Foundations of India's Foreign Policy", "groups": [
            {"name": "Foreign Policy", "topics": [
                _t("ir-fp-principles", "Principles and evolution of India's foreign policy"),
                _t("ir-fp-nam", "Non-Aligned Movement"),
                _t("ir-fp-determinants", "Determinants of foreign policy"),
                _t("ir-fp-panchsheel", "Panchsheel and historical doctrines"),
                _t("ir-fp-strategic", "Strategic autonomy and multi-alignment"),
            ]},
        ]},
        {"name": "India & Neighbourhood", "groups": [
            {"name": "Neighbours", "topics": [
                _t("ir-nb-pakistan", "India-Pakistan relations"),
                _t("ir-nb-china", "India-China relations and border issues"),
                _t("ir-nb-nepal", "India-Nepal relations"),
                _t("ir-nb-bangladesh", "India-Bangladesh relations"),
                _t("ir-nb-srilanka", "India-Sri Lanka relations"),
                _t("ir-nb-myanmar", "India-Myanmar relations"),
                _t("ir-nb-bhutan", "India-Bhutan relations"),
                _t("ir-nb-maldives", "India-Maldives relations"),
                _t("ir-nb-afghanistan", "India-Afghanistan relations"),
                _t("ir-nb-neighbourhood-first", "Neighbourhood First and SAGAR policies"),
            ]},
        ]},
        {"name": "Bilateral Relations", "groups": [
            {"name": "Major Powers", "topics": [
                _t("ir-bl-usa", "India-USA relations"),
                _t("ir-bl-russia", "India-Russia relations"),
                _t("ir-bl-eu", "India-EU and UK relations"),
                _t("ir-bl-japan", "India-Japan relations"),
                _t("ir-bl-australia", "India-Australia relations"),
            ]},
            {"name": "Regions", "topics": [
                _t("ir-bl-gulf", "India and West Asia / Gulf"),
                _t("ir-bl-africa", "India-Africa relations"),
                _t("ir-bl-asean", "India and ASEAN / Act East policy"),
                _t("ir-bl-latinamerica", "India-Latin America relations"),
                _t("ir-bl-centralasia", "India and Central Asia (Connect Central Asia)"),
            ]},
        ]},
        {"name": "Groupings & Agreements", "groups": [
            {"name": "Multilateral Groupings", "topics": [
                _t("ir-gr-brics", "BRICS"),
                _t("ir-gr-sco", "Shanghai Cooperation Organisation"),
                _t("ir-gr-g20", "G20 and G7"),
                _t("ir-gr-quad", "QUAD and Indo-Pacific"),
                _t("ir-gr-saarc", "SAARC"),
                _t("ir-gr-bimstec", "BIMSTEC"),
                _t("ir-gr-ibsa", "IBSA and other groupings"),
                _t("ir-gr-commonwealth", "Commonwealth and NAM today"),
                _t("ir-gr-i2u2", "I2U2 and minilateral groupings"),
            ]},
        ]},
        {"name": "International Institutions", "groups": [
            {"name": "Global Bodies", "topics": [
                _t("ir-ii-un", "United Nations — structure and organs"),
                _t("ir-ii-unsc", "UN Security Council and reforms"),
                _t("ir-ii-imf-wb", "IMF and World Bank"),
                _t("ir-ii-wto", "World Trade Organization"),
                _t("ir-ii-who", "WHO and health diplomacy"),
                _t("ir-ii-icj", "International Court of Justice and ICC"),
                _t("ir-ii-specialized", "Specialized agencies — UNESCO, ILO, FAO"),
                _t("ir-ii-regional", "Regional organizations — EU, AU, OPEC"),
            ]},
        ]},
        {"name": "Global Issues & Diaspora", "groups": [
            {"name": "Contemporary Issues", "topics": [
                _t("ir-gi-effect", "Effect of policies of developed/developing nations on India"),
                _t("ir-gi-diaspora", "Indian diaspora — role and engagement"),
                _t("ir-gi-globalization", "Globalization and India"),
                _t("ir-gi-trade", "International trade and economic diplomacy"),
                _t("ir-gi-climate", "Climate diplomacy and India's stand"),
                _t("ir-gi-terrorism", "Global terrorism and cooperation"),
                _t("ir-gi-energy", "Energy security and resource diplomacy"),
                _t("ir-gi-softpower", "Soft power and cultural diplomacy"),
                _t("ir-gi-conflicts", "Major global conflicts and India's position"),
                _t("ir-gi-maritime", "Maritime security and Indian Ocean Region"),
                _t("ir-gi-cyber", "Cyber security in international relations"),
                _t("ir-gi-spacediplomacy", "Space and technology diplomacy"),
                _t("ir-gi-refugees", "Refugees and humanitarian issues"),
                _t("ir-gi-nuclear", "Nuclear diplomacy — NSG, NPT, treaties"),
            ]},
        ]},
        {"name": "Border & Security Diplomacy", "groups": [
            {"name": "Border Issues", "topics": [
                _t("ir-bd-loc", "LoC, LAC and border management"),
                _t("ir-bd-waterdisputes", "Trans-boundary water issues (Indus, Teesta)"),
                _t("ir-bd-connectivity", "Connectivity projects — BRI, INSTC, IMEC"),
                _t("ir-bd-defence", "Defence cooperation and arms imports"),
            ]},
        ]},
    ],
}
