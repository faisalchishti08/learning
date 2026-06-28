"""Geography Optional (Mains Papers 8 & 9). Stages: MAINS. Prefix: geoopt-."""


def _t(tid, text, stages=("MAINS",), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "geography_optional",
    "title": "Geography (Optional — Papers 8 & 9)",
    "icon": "G+",
    "blurb": "Full optional depth — Paper I (principles of geography) + Paper II (geography of India). Mains optional.",
    "category": "Optional",
    "sections": [
        # ===================== PAPER I =====================
        {"name": "P1 · Geomorphology", "groups": [
            {"name": "Geomorphic Processes", "topics": [
                _t("geoopt-gm-factors", "Factors controlling landform development"),
                _t("geoopt-gm-endogenetic", "Endogenetic and exogenetic forces"),
                _t("geoopt-gm-origin", "Origin and evolution of the earth's crust"),
                _t("geoopt-gm-isostasy", "Fundamentals of geomagnetism and isostasy"),
                _t("geoopt-gm-materials", "Earth materials and physical conditions of the interior"),
                _t("geoopt-gm-geosynclines", "Geosynclines"),
                _t("geoopt-gm-continentaldrift", "Continental drift"),
                _t("geoopt-gm-platetectonics", "Plate tectonics"),
                _t("geoopt-gm-orogeny", "Mountain building — orogeny and epeirogeny"),
                _t("geoopt-gm-vulcanicity", "Vulcanicity and seismicity"),
            ]},
            {"name": "Geomorphic Concepts", "topics": [
                _t("geoopt-gm-cycle", "Concepts of geomorphic cycles (Davis, Penck)"),
                _t("geoopt-gm-slope", "Slope development and landscape evolution"),
                _t("geoopt-gm-channel", "Channel morphology and fluvial processes"),
                _t("geoopt-gm-erosion", "Erosion surfaces"),
                _t("geoopt-gm-applied", "Applied geomorphology — hazards, hydrology, mining"),
                _t("geoopt-gm-economic", "Economic geology and environment"),
            ]},
        ]},
        {"name": "P1 · Climatology", "groups": [
            {"name": "Atmosphere & Climate", "topics": [
                _t("geoopt-cl-composition", "Temperature and pressure belts of the world"),
                _t("geoopt-cl-heatbudget", "Heat budget of the earth"),
                _t("geoopt-cl-circulation", "Atmospheric circulation"),
                _t("geoopt-cl-stability", "Atmospheric stability and instability"),
                _t("geoopt-cl-planetary", "Planetary and local winds, monsoons, jet streams"),
                _t("geoopt-cl-airmasses", "Air masses and fronts"),
                _t("geoopt-cl-cyclones", "Temperate and tropical cyclones"),
                _t("geoopt-cl-precipitation", "Types and distribution of precipitation"),
                _t("geoopt-cl-classification", "Climate classification (Koppen, Thornthwaite, Trewartha)"),
                _t("geoopt-cl-hydrological", "Hydrological cycle"),
                _t("geoopt-cl-globalwarming", "Global climate change and human role"),
            ]},
        ]},
        {"name": "P1 · Oceanography", "groups": [
            {"name": "Oceans", "topics": [
                _t("geoopt-oc-relief", "Ocean bottom relief — Atlantic, Indian, Pacific"),
                _t("geoopt-oc-temperature", "Temperature and salinity of oceans"),
                _t("geoopt-oc-heatbudget", "Heat and salt budgets, ocean deposits"),
                _t("geoopt-oc-waves", "Waves, currents and tides"),
                _t("geoopt-oc-resources", "Marine resources — biotic, mineral, energy"),
                _t("geoopt-oc-coral", "Coral reefs, coral bleaching"),
                _t("geoopt-oc-sealevel", "Sea-level changes"),
                _t("geoopt-oc-law", "Law of the sea and marine pollution"),
            ]},
        ]},
        {"name": "P1 · Biogeography", "groups": [
            {"name": "Biogeography", "topics": [
                _t("geoopt-bg-soil", "Genesis of soils"),
                _t("geoopt-bg-classification", "Classification and distribution of soils"),
                _t("geoopt-bg-soilprocess", "Soil profile and soil erosion"),
                _t("geoopt-bg-vegetation", "Factors influencing world vegetation"),
                _t("geoopt-bg-biomes", "Biomes of the world"),
                _t("geoopt-bg-ecosystem", "Ecosystem — components and functioning"),
                _t("geoopt-bg-biodiversity", "Biodiversity and its depletion"),
                _t("geoopt-bg-conservation", "Conservation of ecosystems"),
                _t("geoopt-bg-foodchain", "Social forestry and wildlife"),
            ]},
        ]},
        {"name": "P1 · Environmental Geography", "groups": [
            {"name": "Environment", "topics": [
                _t("geoopt-eg-principle", "Principle of ecology"),
                _t("geoopt-eg-humanecology", "Human ecological adaptations"),
                _t("geoopt-eg-degradation", "Environmental degradation and management"),
                _t("geoopt-eg-hazards", "Environmental hazards and disasters"),
                _t("geoopt-eg-conservation", "Conservation and sustainable development"),
                _t("geoopt-eg-policy", "Environmental policy and education"),
                _t("geoopt-eg-globalissues", "Global ecological imbalances"),
            ]},
        ]},
        {"name": "P1 · Geographical Thought", "groups": [
            {"name": "History of Thought", "topics": [
                _t("geoopt-gt-ancient", "Contributions of ancient and medieval geographers"),
                _t("geoopt-gt-german", "German, French and British schools of geography"),
                _t("geoopt-gt-determinism", "Environmental determinism and possibilism"),
                _t("geoopt-gt-dualism", "Dualisms in geography"),
                _t("geoopt-gt-quantitative", "Quantitative revolution and positivism"),
                _t("geoopt-gt-behavioural", "Behavioural geography"),
                _t("geoopt-gt-radical", "Radical, humanistic and welfare approaches"),
                _t("geoopt-gt-systems", "Systems analysis in geography"),
                _t("geoopt-gt-paradigm", "Paradigms and laws in geography"),
            ]},
        ]},
        {"name": "P1 · Human Geography — Economic", "groups": [
            {"name": "Economic Geography", "topics": [
                _t("geoopt-he-resources", "World economic development and resources"),
                _t("geoopt-he-agrilocation", "Von Thunen's model of agricultural location"),
                _t("geoopt-he-industriallocation", "Weber and Losch theories of industrial location"),
                _t("geoopt-he-resourceregions", "World resource and energy crisis"),
                _t("geoopt-he-agriregions", "World agricultural and industrial regions"),
                _t("geoopt-he-trade", "World trade and globalization"),
                _t("geoopt-he-transport", "Transport and communication networks"),
            ]},
        ]},
        {"name": "P1 · Human Geography — Population & Settlement", "groups": [
            {"name": "Population", "topics": [
                _t("geoopt-hp-distribution", "World population distribution and density"),
                _t("geoopt-hp-growth", "Population growth and demographic transition"),
                _t("geoopt-hp-migration", "Migration — causes and consequences"),
                _t("geoopt-hp-theories", "Theories of population (Malthus, Marx)"),
                _t("geoopt-hp-overpopulation", "Over/under-population and optimum"),
                _t("geoopt-hp-quality", "Population quality and human development"),
            ]},
            {"name": "Settlement", "topics": [
                _t("geoopt-hs-rural", "Rural settlements — types and patterns"),
                _t("geoopt-hs-urban", "Urban settlements and hierarchy"),
                _t("geoopt-hs-centralplace", "Christaller's central place theory"),
                _t("geoopt-hs-ranksize", "Rank-size rule and primate city"),
                _t("geoopt-hs-morphology", "Urban morphology and functional classification"),
                _t("geoopt-hs-problems", "Problems of urbanization"),
            ]},
        ]},
        {"name": "P1 · Regional Planning", "groups": [
            {"name": "Regional Concepts", "topics": [
                _t("geoopt-rp-region", "Concept of a region and regionalization"),
                _t("geoopt-rp-hierarchy", "Regional hierarchy"),
                _t("geoopt-rp-growthpole", "Growth poles and growth centres (Perroux)"),
                _t("geoopt-rp-models", "Models of regional development"),
                _t("geoopt-rp-planning", "Regional planning and development"),
                _t("geoopt-rp-disparities", "Regional disparities and balanced development"),
                _t("geoopt-rp-models2", "Models, theories and laws in human geography"),
            ]},
        ]},
        # ===================== PAPER II =====================
        {"name": "P2 · Physical Setting of India", "groups": [
            {"name": "Physiography", "topics": [
                _t("geoopt-in-space", "Space relationship of India with neighbours"),
                _t("geoopt-in-structure", "Structure and relief of India"),
                _t("geoopt-in-physiography", "Physiographic regions"),
                _t("geoopt-in-drainage", "Drainage systems and watersheds"),
                _t("geoopt-in-monsoon", "Mechanism of Indian monsoon"),
                _t("geoopt-in-climate", "Climatic regions and tropical cyclones"),
                _t("geoopt-in-soils", "Soils — types and distribution"),
                _t("geoopt-in-vegetation", "Natural vegetation and forests"),
                _t("geoopt-in-hazards", "Floods, droughts and natural hazards"),
            ]},
        ]},
        {"name": "P2 · Resources of India", "groups": [
            {"name": "Resources", "topics": [
                _t("geoopt-in-landresources", "Land and soil resources"),
                _t("geoopt-in-water", "Surface and groundwater resources"),
                _t("geoopt-in-forest", "Forest and wildlife resources"),
                _t("geoopt-in-minerals", "Mineral and energy resources"),
                _t("geoopt-in-marine", "Marine resources"),
                _t("geoopt-in-conservation", "Resource conservation and management"),
            ]},
        ]},
        {"name": "P2 · Agriculture in India", "groups": [
            {"name": "Agriculture", "topics": [
                _t("geoopt-in-agriinfra", "Agricultural infrastructure and inputs"),
                _t("geoopt-in-greenrev", "Green Revolution and its impact"),
                _t("geoopt-in-cropping", "Cropping patterns and agricultural regions"),
                _t("geoopt-in-agriproductivity", "Agricultural productivity and efficiency"),
                _t("geoopt-in-landreform", "Land reforms and land holdings"),
                _t("geoopt-in-irrigation", "Irrigation and water management"),
                _t("geoopt-in-foodsecurity", "Food security and droughts"),
                _t("geoopt-in-agriallied", "Livestock, fisheries and allied sectors"),
            ]},
        ]},
        {"name": "P2 · Industry in India", "groups": [
            {"name": "Industry", "topics": [
                _t("geoopt-in-industrialpolicy", "Evolution of industrial policy"),
                _t("geoopt-in-locationfactors", "Industrial location factors"),
                _t("geoopt-in-industrialregions", "Major industrial regions"),
                _t("geoopt-in-keyindustries", "Iron-steel, cotton, sugar, petrochemical industries"),
                _t("geoopt-in-industrialhouses", "Industrial houses and complexes"),
                _t("geoopt-in-sez", "SEZs and industrial corridors"),
                _t("geoopt-in-liberalization", "Liberalization and multinationals"),
            ]},
        ]},
        {"name": "P2 · Transport, Trade & Settlement", "groups": [
            {"name": "Transport & Trade", "topics": [
                _t("geoopt-in-transport", "Transport network — roads, rail, water, air"),
                _t("geoopt-in-trade", "Internal and international trade"),
                _t("geoopt-in-tradecentres", "Trade centres and ports"),
            ]},
            {"name": "Settlement", "topics": [
                _t("geoopt-in-ruralsettlement", "Rural settlement types and patterns"),
                _t("geoopt-in-urbanization", "Urbanization — trends and process"),
                _t("geoopt-in-urbansystem", "Urban morphology and town classification"),
                _t("geoopt-in-millioncities", "Million-plus cities and metropolitan regions"),
            ]},
        ]},
        {"name": "P2 · Cultural & Population Setting", "groups": [
            {"name": "Cultural Geography", "topics": [
                _t("geoopt-in-population", "Population — distribution, density, growth"),
                _t("geoopt-in-demographic", "Demographic attributes and transition"),
                _t("geoopt-in-migration", "Migration patterns in India"),
                _t("geoopt-in-tribes", "Racial, linguistic and ethnic diversity"),
                _t("geoopt-in-tribalareas", "Tribal areas and their problems"),
                _t("geoopt-in-religious", "Religious and cultural regions"),
            ]},
        ]},
        {"name": "P2 · Regional Development & Planning", "groups": [
            {"name": "Planning", "topics": [
                _t("geoopt-in-planning", "Experience of regional planning in India"),
                _t("geoopt-in-fiveyear", "Five Year Plans and regional development"),
                _t("geoopt-in-rivervalley", "River valley projects"),
                _t("geoopt-in-droughtprone", "Drought-prone area programmes"),
                _t("geoopt-in-hillarea", "Hill area and tribal area development"),
                _t("geoopt-in-planningregions", "Planning regions and target areas"),
                _t("geoopt-in-sustainable", "Sustainable development and regional planning"),
            ]},
        ]},
        {"name": "P2 · Political & Contemporary Issues", "groups": [
            {"name": "Political Geography", "topics": [
                _t("geoopt-in-federalism", "Indian federalism and space"),
                _t("geoopt-in-stateformation", "State reorganization and regional consciousness"),
                _t("geoopt-in-boundary", "International boundaries and disputes"),
                _t("geoopt-in-geopolitics", "India and geopolitics of the Indian Ocean"),
                _t("geoopt-in-borderissues", "Cross-border terrorism and border issues"),
            ]},
            {"name": "Contemporary Issues", "topics": [
                _t("geoopt-in-ecology", "Ecological problems and environmental hazards"),
                _t("geoopt-in-landdegradation", "Desertification and land degradation"),
                _t("geoopt-in-pollution", "Environmental pollution"),
                _t("geoopt-in-disaster", "Disaster management"),
                _t("geoopt-in-regionalimbalance", "Regional imbalance and development issues"),
                _t("geoopt-in-environmentaware", "Environmental awareness and remote sensing"),
                _t("geoopt-in-gis", "GIS and geographical information for planning"),
                _t("geoopt-in-watershed", "Watershed management and rainwater harvesting"),
                _t("geoopt-in-climatechangeindia", "Climate change impact on India"),
                _t("geoopt-in-maharashtra", "Geography of Maharashtra — regional study", ("MAINS",), True),
            ]},
        ]},
        {"name": "P2 · Techniques & Field Study", "groups": [
            {"name": "Geographical Techniques", "topics": [
                _t("geoopt-tech-maps", "Map projections and cartography"),
                _t("geoopt-tech-statistics", "Statistical methods in geography"),
                _t("geoopt-tech-remote", "Remote sensing and aerial photography"),
                _t("geoopt-tech-gis", "GIS and spatial analysis"),
                _t("geoopt-tech-fieldwork", "Field study and survey techniques"),
                _t("geoopt-tech-diagrams", "Diagrams, graphs and thematic mapping"),
            ]},
        ]},
    ],
}
