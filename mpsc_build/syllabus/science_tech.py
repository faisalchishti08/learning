"""Science & Technology. Stages: PRE/MAINS."""


def _t(tid, text, stages=("PRE", "MAINS"), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "science_tech",
    "title": "Science & Technology",
    "icon": "🔬",
    "blurb": "General science, space, defence, IT, biotech, nano-tech, IPR and S&T applications. Prelims + Mains GS-3.",
    "category": "General Studies",
    "sections": [
        {"name": "Physics", "groups": [
            {"name": "Fundamentals", "topics": [
                _t("sci-ph-motion", "Motion, force and laws of motion"),
                _t("sci-ph-energy", "Work, energy and power"),
                _t("sci-ph-gravitation", "Gravitation"),
                _t("sci-ph-heat", "Heat and thermodynamics"),
                _t("sci-ph-light", "Light, optics and applications"),
                _t("sci-ph-sound", "Sound and waves"),
                _t("sci-ph-electricity", "Electricity and magnetism"),
                _t("sci-ph-modern", "Modern physics — atomic and nuclear"),
                _t("sci-ph-semiconductors", "Semiconductors and electronics basics"),
                _t("sci-ph-laser", "Lasers and applications"),
                _t("sci-ph-superconductivity", "Superconductivity and modern materials"),
            ]},
        ]},
        {"name": "Chemistry", "groups": [
            {"name": "Fundamentals", "topics": [
                _t("sci-ch-matter", "States of matter and atomic structure"),
                _t("sci-ch-periodic", "Periodic table and chemical bonding"),
                _t("sci-ch-acids", "Acids, bases and salts"),
                _t("sci-ch-reactions", "Chemical reactions and catalysis"),
                _t("sci-ch-metals", "Metals, non-metals and alloys"),
                _t("sci-ch-organic", "Organic chemistry basics"),
                _t("sci-ch-polymers", "Polymers and plastics"),
                _t("sci-ch-everyday", "Chemistry in everyday life"),
                _t("sci-ch-radioactivity", "Radioactivity and nuclear chemistry"),
                _t("sci-ch-electrochem", "Electrochemistry and batteries"),
                _t("sci-ch-fertilizers", "Fertilizers, pesticides and chemicals"),
                _t("sci-ch-nanomaterials", "Nanomaterials and composites"),
                _t("sci-ch-food", "Food chemistry and adulteration"),
            ]},
        ]},
        {"name": "Biology", "groups": [
            {"name": "Life Sciences", "topics": [
                _t("sci-bi-cell", "Cell — structure and function"),
                _t("sci-bi-genetics", "Genetics and heredity"),
                _t("sci-bi-evolution", "Evolution and classification"),
                _t("sci-bi-plant", "Plant physiology and photosynthesis"),
                _t("sci-bi-human", "Human physiology — systems"),
                _t("sci-bi-nutrition", "Nutrition, vitamins and deficiency diseases"),
                _t("sci-bi-diseases", "Diseases — communicable and non-communicable"),
                _t("sci-bi-immunity", "Immunity and vaccines"),
                _t("sci-bi-microbes", "Microbes and human welfare"),
                _t("sci-bi-biomolecules", "Biomolecules — carbohydrates, proteins, lipids"),
                _t("sci-bi-ecology", "Ecology and environmental biology"),
                _t("sci-bi-biotech-link", "Biological classification and biodiversity"),
            ]},
            {"name": "Health & Medicine", "topics": [
                _t("sci-hm-publichealth", "Public health and epidemics", ("MAINS",)),
                _t("sci-hm-pharma", "Pharmaceuticals and drug development"),
                _t("sci-hm-medicaltech", "Medical technology and diagnostics"),
                _t("sci-hm-genomics", "Genomics and precision medicine"),
            ]},
        ]},
        {"name": "Space Technology", "groups": [
            {"name": "Space", "topics": [
                _t("sci-sp-isro", "ISRO — organization and achievements"),
                _t("sci-sp-launch", "Launch vehicles — PSLV, GSLV, SSLV"),
                _t("sci-sp-satellites", "Satellites — communication, remote sensing"),
                _t("sci-sp-navigation", "NavIC and navigation systems"),
                _t("sci-sp-missions", "Major missions — Chandrayaan, Mangalyaan, Aditya, Gaganyaan"),
                _t("sci-sp-applications", "Applications of space technology", ("MAINS",)),
                _t("sci-sp-privatespace", "Private space sector and reforms", ("MAINS",)),
                _t("sci-sp-international", "International space cooperation"),
            ]},
        ]},
        {"name": "Defence Technology", "groups": [
            {"name": "Defence", "topics": [
                _t("sci-df-drdo", "DRDO and defence research"),
                _t("sci-df-missiles", "Missile systems — Agni, Prithvi, BrahMos"),
                _t("sci-df-aircraft", "Aircraft, tanks and naval systems"),
                _t("sci-df-nuclear", "Nuclear doctrine and triad"),
                _t("sci-df-indigenous", "Indigenization and defence manufacturing", ("MAINS",)),
            ]},
        ]},
        {"name": "Information Technology", "groups": [
            {"name": "IT & Computing", "topics": [
                _t("sci-it-computers", "Computer fundamentals and networks"),
                _t("sci-it-internet", "Internet, web and protocols"),
                _t("sci-it-ai", "Artificial intelligence and machine learning"),
                _t("sci-it-bigdata", "Big data and cloud computing"),
                _t("sci-it-blockchain", "Blockchain and distributed ledger"),
                _t("sci-it-iot", "Internet of Things"),
                _t("sci-it-5g", "5G and telecommunications"),
                _t("sci-it-quantum", "Quantum computing"),
                _t("sci-it-cyber", "Cyber security and digital threats", ("MAINS",)),
                _t("sci-it-egovernance", "IT in governance and digital India", ("MAINS",)),
                _t("sci-it-supercomputing", "Supercomputing and HPC"),
                _t("sci-it-dataprivacy", "Data protection and privacy", ("MAINS",)),
                _t("sci-it-socialmedia", "Social media and misinformation", ("MAINS",)),
            ]},
        ]},
        {"name": "Biotechnology", "groups": [
            {"name": "Biotech", "topics": [
                _t("sci-bt-concepts", "Biotechnology — concepts and tools"),
                _t("sci-bt-geneticeng", "Genetic engineering and GMOs"),
                _t("sci-bt-genomeediting", "Genome editing (CRISPR)"),
                _t("sci-bt-agri", "Biotech in agriculture — Bt crops", ("MAINS",)),
                _t("sci-bt-health", "Biotech in health — gene therapy, biopharma"),
                _t("sci-bt-stemcell", "Stem cells and cloning"),
                _t("sci-bt-bioethics", "Bioethics and biosafety", ("MAINS",)),
            ]},
        ]},
        {"name": "Emerging Technologies", "groups": [
            {"name": "Frontier Tech", "topics": [
                _t("sci-em-nano", "Nanotechnology and applications"),
                _t("sci-em-robotics", "Robotics and automation"),
                _t("sci-em-3dprint", "3D printing and advanced manufacturing"),
                _t("sci-em-renewable", "New materials and energy storage"),
                _t("sci-em-drones", "Drones and unmanned systems"),
            ]},
        ]},
        {"name": "Energy & Nuclear Technology", "groups": [
            {"name": "Energy Tech", "topics": [
                _t("sci-en-nuclear", "Nuclear energy — reactors and fuel cycle"),
                _t("sci-en-thorium", "Three-stage nuclear program and thorium"),
                _t("sci-en-solar", "Solar and photovoltaic technology"),
                _t("sci-en-wind", "Wind and hydro energy technology"),
                _t("sci-en-hydrogen", "Hydrogen and fuel cells", ("MAINS",)),
                _t("sci-en-battery", "Battery and energy storage technology"),
                _t("sci-en-biofuel", "Biofuels and bioenergy"),
            ]},
        ]},
        {"name": "S&T in Agriculture & Daily Life", "groups": [
            {"name": "Applications", "topics": [
                _t("sci-ap-agritech", "Technology in agriculture — precision farming"),
                _t("sci-ap-foodtech", "Food technology and preservation"),
                _t("sci-ap-water", "Water purification and desalination"),
                _t("sci-ap-disaster", "Technology in disaster management"),
                _t("sci-ap-dailylife", "Science in everyday phenomena"),
            ]},
        ]},
        {"name": "S&T Policy & IPR", "groups": [
            {"name": "Policy", "topics": [
                _t("sci-pol-policy", "Science and technology policy of India", ("MAINS",)),
                _t("sci-pol-ipr", "Intellectual Property Rights — patents, copyrights", ("MAINS",)),
                _t("sci-pol-institutions", "S&T institutions — CSIR, DST, DBT"),
                _t("sci-pol-innovation", "Innovation ecosystem and R&D spending", ("MAINS",)),
                _t("sci-pol-indigenous", "Indigenous technology development", ("MAINS",)),
            ]},
        ]},
    ],
}
