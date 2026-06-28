"""Maharashtra — Static GK & State-Specific (high PYQ weight). Stages: PRE/MAINS/INT; all MH."""


def _t(tid, text, stages=("PRE", "MAINS", "INT")):
    return {"id": tid, "text": text, "stages": list(stages), "mh": True}


SUBJECT = {
    "key": "maharashtra",
    "title": "Maharashtra (Static GK & State-Specific)",
    "icon": "महा",
    "blurb": "Consolidated Maharashtra static GK — state profile, geography, history, polity, economy, culture, schemes. ~45% of MPSC is state-specific.",
    "category": "Maharashtra Special",
    "sections": [
        {"name": "State Profile & Symbols", "groups": [
            {"name": "Basics", "topics": [
                _t("mh-pr-formation", "Formation of Maharashtra (1 May 1960) and Samyukta Maharashtra movement"),
                _t("mh-pr-symbols", "State symbols — animal, bird, tree, flower, butterfly"),
                _t("mh-pr-capital", "Capital (Mumbai) and winter capital (Nagpur)"),
                _t("mh-pr-area", "Area, population and ranking among states"),
                _t("mh-pr-emblem", "State emblem, song and language"),
                _t("mh-pr-boundaries", "Bordering states and geographical location"),
            ]},
        ]},
        {"name": "Administrative Setup", "groups": [
            {"name": "Divisions & Districts", "topics": [
                _t("mh-ad-divisions", "Six revenue divisions (Konkan, Pune, Nashik, Aurangabad, Amravati, Nagpur)"),
                _t("mh-ad-districts", "36 districts and recent district changes"),
                _t("mh-ad-talukas", "Talukas, tehsils and administrative hierarchy"),
                _t("mh-ad-vidarbha", "Vidarbha, Marathwada, Khandesh, Konkan, Desh regions"),
                _t("mh-ad-localbodies", "Zilla Parishads, Panchayat Samitis, Gram Panchayats"),
                _t("mh-ad-municipal", "Municipal corporations and councils"),
            ]},
        ]},
        {"name": "Geography of Maharashtra", "groups": [
            {"name": "Physical Features", "topics": [
                _t("mh-ge-sahyadri", "Sahyadri (Western Ghats) and ranges (Satmala, Ajanta, Balaghat)"),
                _t("mh-ge-peaks", "Highest peaks — Kalsubai, Salher, Mahabaleshwar"),
                _t("mh-ge-konkan", "Konkan coastal strip"),
                _t("mh-ge-plateau", "Deccan plateau and Maharashtra plateau"),
                _t("mh-ge-passes", "Mountain passes (ghats) — Thal, Bhor, Kasara"),
            ]},
            {"name": "Rivers & Water Bodies", "topics": [
                _t("mh-ge-godavari", "Godavari and tributaries"),
                _t("mh-ge-krishna", "Krishna and tributaries (Koyna, Panchganga)"),
                _t("mh-ge-tapi", "Tapi-Purna system"),
                _t("mh-ge-konkanrivers", "West-flowing Konkan rivers (Ulhas, Savitri, Vashishti)"),
                _t("mh-ge-dams", "Major dams — Koyna, Jayakwadi, Bhandardara, Ujani"),
                _t("mh-ge-lakes", "Lakes — Lonar, Pawna, Venna"),
                _t("mh-ge-waterfalls", "Waterfalls — Thoseghar, Dudhsagar, Vajrai"),
            ]},
            {"name": "Climate, Soil, Forests", "topics": [
                _t("mh-ge-climate", "Climate and rainfall regions"),
                _t("mh-ge-soils", "Soil types — black regur, laterite, alluvial"),
                _t("mh-ge-nationalparks", "National parks — Tadoba, Gugamal, Sanjay Gandhi, Chandoli, Navegaon, Pench"),
                _t("mh-ge-sanctuaries", "Wildlife sanctuaries and tiger reserves"),
                _t("mh-ge-biosphere", "Biosphere and conservation areas (Western Ghats)"),
            ]},
        ]},
        {"name": "History of Maharashtra", "groups": [
            {"name": "Ancient & Medieval", "topics": [
                _t("mh-hi-satavahana", "Satavahanas, Vakatakas, Rashtrakutas, Yadavas"),
                _t("mh-hi-caves", "Rock-cut caves — Ajanta, Ellora, Elephanta, Karla, Bhaja"),
                _t("mh-hi-bahmani", "Bahmani and Deccan sultanates"),
            ]},
            {"name": "Maratha Empire", "topics": [
                _t("mh-hi-shivaji", "Shivaji Maharaj — administration, forts, navy"),
                _t("mh-hi-ashtapradhan", "Ashtapradhan council"),
                _t("mh-hi-peshwas", "Peshwa period and Maratha confederacy"),
                _t("mh-hi-forts", "Major forts — Raigad, Pratapgad, Sinhagad, Shivneri, Torna"),
                _t("mh-hi-battles", "Key battles — Pratapgad, Sinhagad, Panipat III"),
            ]},
            {"name": "Modern & Reform", "topics": [
                _t("mh-hi-phule", "Jyotiba & Savitribai Phule, Satyashodhak Samaj"),
                _t("mh-hi-ambedkar", "Dr. B.R. Ambedkar — Mahad, Kalaram, Constitution"),
                _t("mh-hi-shahu", "Rajarshi Shahu Maharaj — reservation, reforms"),
                _t("mh-hi-ranade", "Ranade, Agarkar, Gokhale, Tilak"),
                _t("mh-hi-karve", "Maharshi Karve, Vitthal Ramji Shinde"),
                _t("mh-hi-freedom", "Maharashtra in the freedom struggle"),
                _t("mh-hi-samyukta", "Samyukta Maharashtra movement and martyrs"),
            ]},
        ]},
        {"name": "Polity & Governance (Maharashtra)", "groups": [
            {"name": "State Institutions", "topics": [
                _t("mh-po-legislature", "Vidhan Sabha and Vidhan Parishad"),
                _t("mh-po-governor", "Governor and Chief Minister"),
                _t("mh-po-secretariat", "Mantralaya and state secretariat"),
                _t("mh-po-mpsc", "MPSC — composition and functions"),
                _t("mh-po-lokayukta", "Maharashtra Lokayukta"),
                _t("mh-po-panchayatraj", "Panchayati Raj in Maharashtra (Bombay Village Panchayat Act)"),
                _t("mh-po-371", "Article 371(2) — special provisions for Vidarbha/Marathwada"),
            ]},
        ]},
        {"name": "Economy of Maharashtra", "groups": [
            {"name": "State Economy", "topics": [
                _t("mh-ec-overview", "GSDP, sectors and economic survey of Maharashtra"),
                _t("mh-ec-agriculture", "Agriculture — sugarcane, cotton, jowar, grapes, oranges"),
                _t("mh-ec-cooperatives", "Cooperative movement — sugar, dairy, credit"),
                _t("mh-ec-industry", "Industrial belts — Mumbai-Pune, MIDC, auto hub"),
                _t("mh-ec-mumbai", "Mumbai — financial capital, BSE, RBI"),
                _t("mh-ec-irrigation", "Irrigation projects and water disputes"),
                _t("mh-ec-power", "Power generation (Koyna, thermal, Tarapur)"),
                _t("mh-ec-ports", "Ports — JNPT, Mumbai; airports"),
            ]},
        ]},
        {"name": "Schemes & Welfare (Maharashtra)", "groups": [
            {"name": "State Schemes", "topics": [
                _t("mh-sc-agri", "Agriculture schemes — Jalyukt Shivar, Magel Tyala Shettale"),
                _t("mh-sc-women", "Women & child schemes (Ladki Bahin, Manodhairya)"),
                _t("mh-sc-employment", "Employment and housing schemes"),
                _t("mh-sc-health", "Health schemes (Mahatma Phule Jan Arogya Yojana)"),
                _t("mh-sc-education", "Education and scholarship schemes"),
                _t("mh-sc-welfare", "Welfare schemes for SC/ST/OBC and farmers"),
            ]},
        ]},
        {"name": "Culture, Festivals & Personalities", "groups": [
            {"name": "Culture", "topics": [
                _t("mh-cu-saints", "Varkari saints — Dnyaneshwar, Tukaram, Namdev, Eknath"),
                _t("mh-cu-folkarts", "Folk arts — Lavani, Tamasha, Powada, Koli dance"),
                _t("mh-cu-festivals", "Festivals — Ganesh Utsav, Gudi Padwa, Pandharpur Wari"),
                _t("mh-cu-literature", "Marathi literature and Jnanpith awardees"),
                _t("mh-cu-sahitya", "Akhil Bharatiya Marathi Sahitya Sammelan"),
                _t("mh-cu-cinema", "Marathi theatre and cinema"),
            ]},
            {"name": "Personalities & Awards", "topics": [
                _t("mh-cu-bharatratna", "Bharat Ratna and Padma awardees from Maharashtra"),
                _t("mh-cu-maharashtrabhushan", "Maharashtra Bhushan and state awards"),
                _t("mh-cu-sports", "Sportspersons from Maharashtra"),
                _t("mh-cu-scientists", "Scientists and reformers from Maharashtra"),
            ]},
        ]},
        {"name": "Maharashtra Miscellaneous GK", "groups": [
            {"name": "Misc & First-in-State", "topics": [
                _t("mh-mi-first", "First-in-Maharashtra facts"),
                _t("mh-mi-tourism", "Tourist places, hill stations, pilgrimage centres"),
                _t("mh-mi-institutions", "Important institutions and research centres"),
                _t("mh-mi-tribes", "Tribes of Maharashtra (Bhil, Warli, Gond, Katkari)"),
                _t("mh-mi-census", "Census data — literacy, sex ratio, urbanization"),
                _t("mh-mi-currentaffairs", "Maharashtra current affairs and recent developments"),
            ]},
        ]},
    ],
}
