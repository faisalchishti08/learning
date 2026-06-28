"""Environment & Ecology + Disaster Management. Stages: PRE/MAINS; MH = Maharashtra."""


def _t(tid, text, stages=("PRE", "MAINS"), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "environment",
    "title": "Environment & Ecology",
    "icon": "🌿",
    "blurb": "Ecology, biodiversity, climate change, pollution, conservation, environmental laws, disaster management. Prelims + Mains GS-3.",
    "category": "General Studies",
    "sections": [
        {"name": "Ecology & Ecosystems", "groups": [
            {"name": "Ecology Basics", "topics": [
                _t("env-ec-ecology", "Ecology — levels of organization"),
                _t("env-ec-ecosystem", "Ecosystem — structure and components"),
                _t("env-ec-energyflow", "Energy flow, food chain and food web"),
                _t("env-ec-trophic", "Trophic levels and ecological pyramids"),
                _t("env-ec-cycles", "Biogeochemical cycles — carbon, nitrogen, phosphorus"),
                _t("env-ec-succession", "Ecological succession"),
                _t("env-ec-productivity", "Productivity and ecological efficiency"),
                _t("env-ec-services", "Ecosystem services"),
            ]},
            {"name": "Types of Ecosystems", "topics": [
                _t("env-ec-terrestrial", "Terrestrial ecosystems — forest, grassland, desert"),
                _t("env-ec-aquatic", "Aquatic ecosystems — freshwater, marine"),
                _t("env-ec-wetland", "Wetlands and their importance"),
                _t("env-ec-mangrove", "Mangroves and coastal ecosystems"),
            ]},
        ]},
        {"name": "Biodiversity", "groups": [
            {"name": "Biodiversity Basics", "topics": [
                _t("env-bd-levels", "Levels of biodiversity — genetic, species, ecosystem"),
                _t("env-bd-hotspots", "Biodiversity hotspots — India and world"),
                _t("env-bd-westernghats", "Western Ghats hotspot (Maharashtra)", ("PRE", "MAINS"), True),
                _t("env-bd-endemic", "Endemic, endangered and keystone species"),
                _t("env-bd-iucn", "IUCN Red List categories"),
                _t("env-bd-loss", "Causes of biodiversity loss", ("MAINS",)),
            ]},
            {"name": "Conservation", "topics": [
                _t("env-bd-insitu", "In-situ conservation — protected areas"),
                _t("env-bd-exsitu", "Ex-situ conservation — zoos, gene banks"),
                _t("env-bd-nationalparks", "National parks and wildlife sanctuaries"),
                _t("env-bd-biosphere", "Biosphere reserves"),
                _t("env-bd-mh-pa", "Protected areas of Maharashtra (Tadoba, Melghat)", ("PRE", "MAINS"), True),
                _t("env-bd-projecttiger", "Project Tiger, Project Elephant"),
                _t("env-bd-cites", "Conservation of flora and fauna programs"),
                _t("env-bd-conservationreserves", "Conservation and community reserves"),
                _t("env-bd-wetlandconserve", "Wetland conservation and Ramsar sites of India"),
                _t("env-bd-marine", "Marine protected areas and coral conservation"),
                _t("env-bd-invasive", "Invasive alien species"),
                _t("env-bd-act2002", "Biological Diversity Act 2002"),
            ]},
        ]},
        {"name": "Climate Change", "groups": [
            {"name": "Climate Science", "topics": [
                _t("env-cc-greenhouse", "Greenhouse effect and gases"),
                _t("env-cc-globalwarming", "Global warming — causes and impacts"),
                _t("env-cc-ozone", "Ozone depletion"),
                _t("env-cc-ipcc", "IPCC and climate assessments"),
                _t("env-cc-impacts", "Impacts on India and Maharashtra", ("MAINS",), True),
            ]},
            {"name": "Climate Action", "topics": [
                _t("env-cc-mitigation", "Mitigation and adaptation strategies", ("MAINS",)),
                _t("env-cc-napcc", "National Action Plan on Climate Change"),
                _t("env-cc-carbon", "Carbon markets and net-zero targets", ("MAINS",)),
                _t("env-cc-renewable", "Renewable energy transition"),
                _t("env-cc-isa", "International Solar Alliance and India's role"),
                _t("env-cc-cop", "Conference of Parties (COP) outcomes", ("MAINS",)),
                _t("env-cc-leaf", "LiFE mission and sustainable lifestyles"),
            ]},
        ]},
        {"name": "Pollution", "groups": [
            {"name": "Types of Pollution", "topics": [
                _t("env-po-air", "Air pollution — sources and effects"),
                _t("env-po-water", "Water pollution and eutrophication"),
                _t("env-po-soil", "Soil pollution"),
                _t("env-po-noise", "Noise pollution"),
                _t("env-po-thermal", "Thermal and radioactive pollution"),
                _t("env-po-plastic", "Plastic pollution and microplastics"),
            ]},
            {"name": "Waste Management", "topics": [
                _t("env-po-solid", "Solid waste management"),
                _t("env-po-ewaste", "E-waste and hazardous waste"),
                _t("env-po-biomedical", "Biomedical waste"),
                _t("env-po-airquality", "Air quality index and standards"),
                _t("env-po-stubble", "Stubble burning and urban smog"),
                _t("env-po-effluent", "Industrial effluent treatment"),
                _t("env-po-namami", "River cleaning programs (Namami Gange)"),
                _t("env-po-bioremediation", "Bioremediation and phytoremediation"),
            ]},
        ]},
        {"name": "Environmental Conservation & Governance", "groups": [
            {"name": "Laws & Institutions", "topics": [
                _t("env-gv-eia", "Environmental Impact Assessment"),
                _t("env-gv-epa", "Environment Protection Act 1986"),
                _t("env-gv-airwater", "Air and Water Acts"),
                _t("env-gv-forest", "Forest Conservation Act and Wildlife Protection Act"),
                _t("env-gv-fra", "Forest Rights Act 2006"),
                _t("env-gv-cpcb", "CPCB, MoEFCC and pollution boards"),
                _t("env-gv-ngt", "National Green Tribunal"),
            ]},
            {"name": "International Conventions", "topics": [
                _t("env-ic-unfccc", "UNFCCC, Kyoto Protocol, Paris Agreement"),
                _t("env-ic-cbd", "Convention on Biological Diversity"),
                _t("env-ic-cites", "CITES"),
                _t("env-ic-ramsar", "Ramsar Convention on wetlands"),
                _t("env-ic-montreal", "Montreal Protocol"),
                _t("env-ic-basel", "Basel, Rotterdam, Stockholm conventions"),
                _t("env-ic-unccd", "UNCCD and desertification"),
            ]},
        ]},
        {"name": "Sustainable Development", "groups": [
            {"name": "Sustainability", "topics": [
                _t("env-sd-concept", "Sustainable development — concept", ("MAINS",)),
                _t("env-sd-sdg", "Sustainable Development Goals"),
                _t("env-sd-greeneconomy", "Green economy and circular economy", ("MAINS",)),
                _t("env-sd-ecotourism", "Eco-tourism and conservation"),
                _t("env-sd-eia-process", "Environmental clearance process", ("MAINS",)),
                _t("env-sd-csr", "Environmental ethics and CSR", ("MAINS",)),
            ]},
        ]},
        {"name": "Agriculture & Environment", "groups": [
            {"name": "Environmental Issues", "topics": [
                _t("env-ae-soildegradation", "Soil degradation and desertification"),
                _t("env-ae-waterscarcity", "Water scarcity and groundwater depletion"),
                _t("env-ae-deforestation", "Deforestation and afforestation"),
                _t("env-ae-pesticides", "Pesticide and fertilizer pollution"),
                _t("env-ae-foodsecurity", "Climate impact on food security", ("MAINS",)),
            ]},
        ]},
        {"name": "Maharashtra Environment", "groups": [
            {"name": "State Issues", "topics": [
                _t("env-mh-ghats", "Western Ghats ecology (Gadgil/Kasturirangan)", ("PRE", "MAINS"), True),
                _t("env-mh-forests", "Forests and afforestation in Maharashtra", ("PRE", "MAINS"), True),
                _t("env-mh-rivers", "River pollution in Maharashtra", ("PRE", "MAINS"), True),
                _t("env-mh-drought", "Drought and water management", ("PRE", "MAINS"), True),
            ]},
        ]},
        {"name": "Disaster Management", "groups": [
            {"name": "Disaster Concepts", "topics": [
                _t("env-dm-types", "Types of disasters — natural and man-made"),
                _t("env-dm-cycle", "Disaster management cycle"),
                _t("env-dm-act", "Disaster Management Act 2005"),
                _t("env-dm-ndma", "NDMA and institutional framework"),
                _t("env-dm-riskreduction", "Disaster risk reduction (Sendai Framework)", ("MAINS",)),
                _t("env-dm-resilience", "Building resilient society", ("MAINS",)),
            ]},
            {"name": "Specific Disasters", "topics": [
                _t("env-dm-floods", "Flood and drought management"),
                _t("env-dm-earthquake", "Earthquake preparedness"),
                _t("env-dm-cyclone", "Cyclone and coastal disasters"),
                _t("env-dm-landslide", "Landslides (Western Ghats/Maharashtra)", ("PRE", "MAINS"), True),
                _t("env-dm-industrial", "Industrial and chemical disasters"),
            ]},
        ]},
    ],
}
