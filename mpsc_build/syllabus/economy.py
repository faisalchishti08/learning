"""Economy. Stages: PRE/MAINS; MH = Maharashtra weightage."""


def _t(tid, text, stages=("PRE", "MAINS"), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "economy",
    "title": "Economy",
    "icon": "₹",
    "blurb": "Indian economy, planning, money & banking, public finance, agriculture, industry, infrastructure, Maharashtra economy. Prelims + Mains GS-3.",
    "category": "General Studies",
    "sections": [
        {"name": "Basics of Economy", "groups": [
            {"name": "Fundamentals", "topics": [
                _t("eco-bs-types", "Types of economies and sectors"),
                _t("eco-bs-microvsmacro", "Micro vs macroeconomics — basic concepts"),
                _t("eco-bs-factors", "Factors of production"),
                _t("eco-bs-demandsupply", "Demand, supply and market equilibrium"),
                _t("eco-bs-marketstructure", "Market structures — competition, monopoly"),
            ]},
            {"name": "National Income", "topics": [
                _t("eco-ni-concepts", "GDP, GNP, NNP, NDP — concepts"),
                _t("eco-ni-methods", "Methods of measuring national income"),
                _t("eco-ni-realnominal", "Real vs nominal income, GDP deflator"),
                _t("eco-ni-percapita", "Per capita income and limitations"),
                _t("eco-ni-sectors", "Sectoral composition and structural change"),
                _t("eco-ni-informal", "Informal economy and measurement issues"),
            ]},
        ]},
        {"name": "Planning & Development", "groups": [
            {"name": "Planning", "topics": [
                _t("eco-pl-history", "Economic planning in India — history"),
                _t("eco-pl-fiveyear", "Five Year Plans — objectives and achievements"),
                _t("eco-pl-niti", "NITI Aayog — shift from Planning Commission"),
                _t("eco-pl-resource", "Resource mobilization for development"),
            ]},
            {"name": "Growth & Development", "topics": [
                _t("eco-dev-growthvsdev", "Economic growth vs development"),
                _t("eco-dev-inclusive", "Inclusive growth and challenges", ("MAINS",)),
                _t("eco-dev-hdi", "Human Development Index and indicators"),
                _t("eco-dev-sustainable", "Sustainable development goals", ("MAINS",)),
                _t("eco-dev-employment", "Employment, unemployment and jobless growth", ("MAINS",)),
            ]},
        ]},
        {"name": "Money & Banking", "groups": [
            {"name": "Money & RBI", "topics": [
                _t("eco-mb-money", "Money — functions and supply (M1-M4)"),
                _t("eco-mb-rbi", "Reserve Bank of India — functions"),
                _t("eco-mb-monetary", "Monetary policy and instruments"),
                _t("eco-mb-inflation", "Inflation — types, causes, measurement (WPI, CPI)"),
                _t("eco-mb-repo", "Repo, reverse repo, CRR, SLR"),
                _t("eco-mb-deflation", "Deflation, stagflation and disinflation"),
                _t("eco-mb-omc", "Open market operations and liquidity"),
            ]},
            {"name": "Banking & Finance", "topics": [
                _t("eco-bk-system", "Banking system — commercial, cooperative, RRBs"),
                _t("eco-bk-npa", "Non-performing assets and recapitalization"),
                _t("eco-bk-inclusion", "Financial inclusion — Jan Dhan, payments banks"),
                _t("eco-bk-reforms", "Banking sector reforms and Basel norms"),
                _t("eco-bk-cooperative", "Cooperative banks in Maharashtra", ("PRE", "MAINS"), True),
            ]},
            {"name": "Financial Markets", "topics": [
                _t("eco-fm-capital", "Capital and money markets"),
                _t("eco-fm-sebi", "SEBI and stock markets"),
                _t("eco-fm-instruments", "Financial instruments — shares, bonds, derivatives"),
                _t("eco-fm-mutualfunds", "Mutual funds and NBFCs"),
            ]},
        ]},
        {"name": "Public Finance", "groups": [
            {"name": "Budget & Taxation", "topics": [
                _t("eco-pf-budget", "Union Budget — components and process"),
                _t("eco-pf-deficits", "Types of deficits — fiscal, revenue, primary"),
                _t("eco-pf-frbm", "FRBM Act and fiscal consolidation"),
                _t("eco-pf-directtax", "Direct taxes — income, corporate"),
                _t("eco-pf-gst", "Goods and Services Tax (GST)"),
                _t("eco-pf-finance-commission", "Finance Commission and devolution"),
                _t("eco-pf-publicdebt", "Public debt and expenditure management"),
                _t("eco-pf-subsidies", "Subsidies — types and rationalization", ("MAINS",)),
                _t("eco-pf-indirecttax", "Indirect taxes and tax structure"),
                _t("eco-pf-blackmoney", "Tax evasion, avoidance and reforms", ("MAINS",)),
                _t("eco-pf-cess", "Cess, surcharge and non-tax revenue"),
            ]},
        ]},
        {"name": "Agriculture", "groups": [
            {"name": "Crops & Production", "topics": [
                _t("eco-ag-cropping", "Cropping patterns and seasons"),
                _t("eco-ag-greenrev", "Green Revolution and its impact"),
                _t("eco-ag-irrigation", "Irrigation systems and water management"),
                _t("eco-ag-inputs", "Agricultural inputs — seeds, fertilizers, credit"),
                _t("eco-ag-mechanization", "Farm mechanization and e-technology"),
            ]},
            {"name": "Markets & Support", "topics": [
                _t("eco-ag-msp", "Minimum Support Price and procurement"),
                _t("eco-ag-pds", "Public Distribution System and food security"),
                _t("eco-ag-buffer", "Buffer stocks and FCI"),
                _t("eco-ag-marketing", "Agricultural marketing and APMC reforms", ("MAINS",)),
                _t("eco-ag-subsidies", "Farm subsidies — direct and indirect", ("MAINS",)),
                _t("eco-ag-foodprocessing", "Food processing — scope and supply chain"),
                _t("eco-ag-landreforms", "Land reforms in India", ("MAINS",)),
            ]},
            {"name": "Allied & Maharashtra", "topics": [
                _t("eco-ag-allied", "Animal husbandry, dairy, fisheries, horticulture"),
                _t("eco-ag-credit", "Agricultural credit and insurance (PM-Fasal Bima)"),
                _t("eco-ag-organic", "Organic and natural farming"),
                _t("eco-ag-mh", "Maharashtra agriculture — sugar, cotton, drought", ("PRE", "MAINS"), True),
                _t("eco-ag-mh-cooperatives", "Cooperative movement in Maharashtra", ("PRE", "MAINS"), True),
                _t("eco-ag-distress", "Agrarian distress and farmer welfare", ("MAINS",), True),
            ]},
        ]},
        {"name": "Industry & Infrastructure", "groups": [
            {"name": "Industry", "topics": [
                _t("eco-ind-policy", "Industrial policy — evolution"),
                _t("eco-ind-liberalization", "Liberalization, privatization, globalization (1991)"),
                _t("eco-ind-msme", "MSMEs and their role"),
                _t("eco-ind-publicsector", "Public sector undertakings and disinvestment"),
                _t("eco-ind-makeinindia", "Make in India, PLI and manufacturing"),
                _t("eco-ind-mh", "Industrial development in Maharashtra (MIDC)", ("PRE", "MAINS"), True),
            ]},
            {"name": "Infrastructure", "topics": [
                _t("eco-inf-energy", "Energy infrastructure and policy"),
                _t("eco-inf-transport", "Transport — roads, railways, ports, airports"),
                _t("eco-inf-ppp", "Investment models — PPP"),
                _t("eco-inf-digital", "Digital infrastructure and connectivity"),
                _t("eco-inf-urban", "Urban infrastructure and smart cities"),
                _t("eco-inf-renewable", "Renewable energy infrastructure"),
                _t("eco-inf-logistics", "Logistics, Gati Shakti and corridors"),
                _t("eco-inf-housing", "Housing and real estate (RERA)"),
            ]},
        ]},
        {"name": "External Sector", "groups": [
            {"name": "Trade & Investment", "topics": [
                _t("eco-ex-bop", "Balance of payments and trade"),
                _t("eco-ex-forex", "Foreign exchange and exchange rate"),
                _t("eco-ex-fdi", "FDI, FII and foreign investment policy"),
                _t("eco-ex-trade-policy", "Foreign trade policy and WTO", ("MAINS",)),
                _t("eco-ex-currency", "Currency convertibility and devaluation"),
            ]},
        ]},
        {"name": "Social Sector & Indicators", "groups": [
            {"name": "Welfare Economics", "topics": [
                _t("eco-ss-poverty", "Poverty — estimation and alleviation", ("MAINS",)),
                _t("eco-ss-hunger", "Hunger, malnutrition and food security", ("MAINS",)),
                _t("eco-ss-inequality", "Income inequality and Gini coefficient"),
                _t("eco-ss-schemes", "Employment and welfare schemes (MGNREGA etc.)"),
                _t("eco-ss-health-edu", "Health and education spending"),
                _t("eco-ss-socialsecurity", "Social security and pension schemes"),
                _t("eco-ss-labour", "Labour reforms and codes", ("MAINS",)),
            ]},
        ]},
        {"name": "Maharashtra Economy", "groups": [
            {"name": "State Economy", "topics": [
                _t("eco-mh-overview", "Maharashtra economy — structure and GSDP", ("PRE", "MAINS"), True),
                _t("eco-mh-budget", "Maharashtra state budget and finances", ("PRE", "MAINS"), True),
                _t("eco-mh-mumbai", "Mumbai as a financial hub", ("PRE", "MAINS"), True),
                _t("eco-mh-schemes", "Maharashtra welfare and development schemes", ("PRE", "MAINS"), True),
                _t("eco-mh-regional", "Regional imbalance and backward regions", ("MAINS",), True),
                _t("eco-mh-services", "Services and IT sector in Maharashtra", ("PRE", "MAINS"), True),
            ]},
        ]},
        {"name": "Contemporary Economic Issues", "groups": [
            {"name": "Current Themes", "topics": [
                _t("eco-ci-digital", "Digital economy and fintech", ("MAINS",)),
                _t("eco-ci-gig", "Gig economy and future of work", ("MAINS",)),
                _t("eco-ci-startup", "Startups and entrepreneurship"),
                _t("eco-ci-blackmoney", "Black money and money laundering", ("MAINS",)),
                _t("eco-ci-demographic", "Demographic dividend", ("MAINS",)),
                _t("eco-ci-climate-econ", "Climate change and green economy", ("MAINS",)),
                _t("eco-ci-cryptocurrency", "Cryptocurrency and CBDC (digital rupee)", ("MAINS",)),
                _t("eco-ci-ease", "Ease of doing business and reforms"),
                _t("eco-ci-atmanirbhar", "Atmanirbhar Bharat and self-reliance", ("MAINS",)),
            ]},
        ]},
        {"name": "Economic Theory & Thinkers", "groups": [
            {"name": "Concepts", "topics": [
                _t("eco-th-keynes", "Keynesian and classical economics", ("MAINS",)),
                _t("eco-th-welfare", "Welfare economics and market failure", ("MAINS",)),
                _t("eco-th-businesscycle", "Business cycles and recession"),
                _t("eco-th-multiplier", "Multiplier and accelerator effects"),
                _t("eco-th-publicgoods", "Public goods and externalities"),
            ]},
        ]},
        {"name": "International Economic Institutions", "groups": [
            {"name": "Global Bodies", "topics": [
                _t("eco-ie-imf", "IMF and World Bank"),
                _t("eco-ie-wto", "WTO and trade agreements", ("MAINS",)),
                _t("eco-ie-adb", "ADB, NDB and AIIB"),
                _t("eco-ie-credit", "Credit rating agencies and global indices"),
                _t("eco-ie-g20", "G20 and global economic governance", ("MAINS",)),
            ]},
        ]},
    ],
}
