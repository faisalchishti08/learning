"""Indian Society & Social Justice. Stages: PRE/MAINS; MH = Maharashtra."""


def _t(tid, text, stages=("PRE", "MAINS"), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "society",
    "title": "Indian Society & Social Justice",
    "icon": "👥",
    "blurb": "Society, diversity, women, population, urbanization, social issues, welfare schemes, vulnerable sections. Prelims + Mains GS-1/GS-2.",
    "category": "General Studies",
    "sections": [
        {"name": "Features of Indian Society", "groups": [
            {"name": "Society & Diversity", "topics": [
                _t("soc-fs-features", "Salient features of Indian society"),
                _t("soc-fs-diversity", "Unity in diversity — language, religion, region"),
                _t("soc-fs-caste", "Caste system — features and changes", ("MAINS",)),
                _t("soc-fs-family", "Family, marriage and kinship"),
                _t("soc-fs-tribal", "Tribal society and issues", ("MAINS",)),
                _t("soc-fs-rural-urban", "Rural and urban society"),
                _t("soc-fs-multiculturalism", "Multiculturalism and pluralism"),
                _t("soc-fs-socialstructure", "Social stratification and mobility", ("MAINS",)),
            ]},
        ]},
        {"name": "Role of Women", "groups": [
            {"name": "Women & Gender", "topics": [
                _t("soc-wm-status", "Status of women — historical to contemporary"),
                _t("soc-wm-organizations", "Women's organizations and movements", ("MAINS",)),
                _t("soc-wm-empowerment", "Women's empowerment and schemes"),
                _t("soc-wm-violence", "Violence against women and laws", ("MAINS",)),
                _t("soc-wm-workforce", "Women in workforce and economy"),
                _t("soc-wm-reservation", "Women's political participation and reservation"),
                _t("soc-wm-genderissues", "Gender issues and patriarchy", ("MAINS",)),
                _t("soc-wm-laws", "Laws for women — dowry, domestic violence, harassment"),
                _t("soc-wm-feminism", "Feminist movements and gender equality", ("MAINS",)),
            ]},
        ]},
        {"name": "Population & Demography", "groups": [
            {"name": "Population", "topics": [
                _t("soc-pop-census", "Census of India and demographic data"),
                _t("soc-pop-growth", "Population growth and trends"),
                _t("soc-pop-policy", "Population policy and family planning"),
                _t("soc-pop-dividend", "Demographic dividend", ("MAINS",)),
                _t("soc-pop-ageing", "Ageing population and challenges"),
                _t("soc-pop-sexratio", "Sex ratio and gender imbalance"),
                _t("soc-pop-issues", "Population problems and remedies", ("MAINS",)),
                _t("soc-pop-literacy", "Literacy and human development trends"),
                _t("soc-pop-distribution", "Population distribution and migration patterns"),
            ]},
        ]},
        {"name": "Urbanization", "groups": [
            {"name": "Urban Issues", "topics": [
                _t("soc-ur-trends", "Urbanization trends in India"),
                _t("soc-ur-problems", "Problems of urbanization — slums, housing", ("MAINS",)),
                _t("soc-ur-migration", "Rural-urban migration"),
                _t("soc-ur-smartcities", "Smart cities and urban planning"),
                _t("soc-ur-mh", "Urbanization in Maharashtra (Mumbai, Pune)", ("PRE", "MAINS"), True),
                _t("soc-ur-remedies", "Solutions to urban challenges", ("MAINS",)),
            ]},
        ]},
        {"name": "Social Issues", "groups": [
            {"name": "Social Problems", "topics": [
                _t("soc-si-poverty", "Poverty and developmental issues", ("MAINS",)),
                _t("soc-si-unemployment", "Unemployment and underemployment"),
                _t("soc-si-illiteracy", "Illiteracy and education gaps"),
                _t("soc-si-childlabour", "Child labour and trafficking"),
                _t("soc-si-substance", "Substance abuse and addiction"),
                _t("soc-si-disparities", "Regional disparities", ("MAINS",), True),
                _t("soc-si-corruption", "Social effects of corruption"),
                _t("soc-si-farmerdistress", "Farmer distress and rural suicides", ("MAINS",), True),
                _t("soc-si-honourkilling", "Honour killings and social evils"),
                _t("soc-si-digitaldivide", "Digital divide and social inequality"),
            ]},
            {"name": "Identity & Ideology", "topics": [
                _t("soc-id-communalism", "Communalism — causes and effects", ("MAINS",)),
                _t("soc-id-regionalism", "Regionalism", ("MAINS",)),
                _t("soc-id-secularism", "Secularism in India", ("MAINS",)),
                _t("soc-id-casteism", "Casteism and untouchability"),
                _t("soc-id-empowerment", "Social empowerment and movements", ("MAINS",), True),
            ]},
        ]},
        {"name": "Globalization & Social Change", "groups": [
            {"name": "Change", "topics": [
                _t("soc-gl-effects", "Effects of globalization on society", ("MAINS",)),
                _t("soc-gl-culture", "Cultural change and Westernization"),
                _t("soc-gl-sanskritization", "Sanskritization and modernization", ("MAINS",)),
                _t("soc-gl-media", "Media, technology and social change"),
                _t("soc-gl-socialmovements", "Social movements in India", ("MAINS",)),
            ]},
        ]},
        {"name": "Vulnerable Sections & Welfare", "groups": [
            {"name": "Vulnerable Sections", "topics": [
                _t("soc-vs-sc", "Scheduled Castes — issues and welfare", ("MAINS",)),
                _t("soc-vs-st", "Scheduled Tribes — issues and welfare", ("MAINS",)),
                _t("soc-vs-obc", "OBCs and reservation policy", ("MAINS",)),
                _t("soc-vs-minorities", "Religious and linguistic minorities"),
                _t("soc-vs-children", "Children — rights and protection"),
                _t("soc-vs-elderly", "Elderly — welfare and challenges"),
                _t("soc-vs-disabled", "Persons with disabilities"),
                _t("soc-vs-transgender", "Transgender and LGBTQ rights"),
            ]},
            {"name": "Welfare Schemes", "topics": [
                _t("soc-ws-central", "Central welfare schemes for vulnerable sections", ("PRE", "MAINS")),
                _t("soc-ws-mh", "Maharashtra welfare schemes", ("PRE", "MAINS"), True),
                _t("soc-ws-implementation", "Issues in scheme implementation", ("MAINS",)),
                _t("soc-ws-rights", "Rights-based welfare approach"),
            ]},
        ]},
        {"name": "Social Sector — Health, Education, HR", "groups": [
            {"name": "Social Sector", "topics": [
                _t("soc-ss-health", "Health sector — issues and policy", ("MAINS",)),
                _t("soc-ss-education", "Education sector — NEP, access, quality", ("MAINS",)),
                _t("soc-ss-skill", "Skill development and human resources", ("MAINS",)),
                _t("soc-ss-nutrition", "Nutrition and food security"),
                _t("soc-ss-sanitation", "Sanitation and Swachh Bharat"),
                _t("soc-ss-hunger", "Hunger and malnutrition", ("MAINS",)),
            ]},
        ]},
        {"name": "Civil Society & NGOs", "groups": [
            {"name": "Civil Society", "topics": [
                _t("soc-cs-ngos", "NGOs — role and regulation", ("MAINS",)),
                _t("soc-cs-shg", "Self-Help Groups and microfinance"),
                _t("soc-cs-cooperatives", "Cooperatives and community organizations", ("PRE", "MAINS"), True),
                _t("soc-cs-donors", "Donors, charities and funding", ("MAINS",)),
                _t("soc-cs-participation", "Citizen participation in development"),
                _t("soc-cs-pressuregroups", "Pressure groups and social activism", ("MAINS",)),
            ]},
        ]},
        {"name": "Social Justice & Constitutional Provisions", "groups": [
            {"name": "Social Justice", "topics": [
                _t("soc-sj-reservation", "Reservation policy — evolution and debates", ("MAINS",)),
                _t("soc-sj-affirmative", "Affirmative action and social equity", ("MAINS",)),
                _t("soc-sj-atrocities", "SC/ST Prevention of Atrocities Act"),
                _t("soc-sj-manualscavenging", "Abolition of manual scavenging"),
                _t("soc-sj-bondedlabour", "Bonded labour and child rights laws"),
                _t("soc-sj-commissions", "National commissions for vulnerable groups"),
                _t("soc-sj-inclusion", "Social inclusion and exclusion", ("MAINS",)),
            ]},
        ]},
        {"name": "Maharashtra Society", "groups": [
            {"name": "State Society", "topics": [
                _t("soc-mh-reformers", "Social reform legacy of Maharashtra", ("PRE", "MAINS"), True),
                _t("soc-mh-tribal", "Tribal communities of Maharashtra", ("PRE", "MAINS"), True),
                _t("soc-mh-migration", "Migration and urban society in Maharashtra", ("MAINS",), True),
                _t("soc-mh-schemes", "Social welfare administration in Maharashtra", ("PRE", "MAINS"), True),
            ]},
        ]},
        {"name": "Education & Health Detail", "groups": [
            {"name": "Education", "topics": [
                _t("soc-ed-nep", "National Education Policy 2020", ("MAINS",)),
                _t("soc-ed-rte", "Right to Education and literacy programs"),
                _t("soc-ed-higher", "Higher education — challenges and reforms", ("MAINS",)),
                _t("soc-ed-digital", "Digital divide in education", ("MAINS",)),
            ]},
            {"name": "Health", "topics": [
                _t("soc-he-ayushman", "Ayushman Bharat and health insurance"),
                _t("soc-he-primary", "Primary health care and infrastructure", ("MAINS",)),
                _t("soc-he-mental", "Mental health and well-being"),
                _t("soc-he-mortality", "Maternal and child health indicators"),
            ]},
        ]},
    ],
}
