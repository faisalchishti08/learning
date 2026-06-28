"""History & Indian Culture. Stages: PRE/MAINS; MH = Maharashtra weightage."""


def _t(tid, text, stages=("PRE", "MAINS"), mh=False):
    d = {"id": tid, "text": text, "stages": list(stages)}
    if mh:
        d["mh"] = True
    return d


SUBJECT = {
    "key": "history",
    "title": "History & Indian Culture",
    "icon": "H",
    "blurb": "Ancient → Modern India, Maharashtra history, art & culture, Bhakti, world history. Prelims + Mains GS-1.",
    "category": "General Studies",
    "sections": [
        {"name": "Sources & Prehistory", "groups": [
            {"name": "Sources", "topics": [
                _t("hist-src-archaeo", "Archaeological sources — inscriptions, coins, monuments"),
                _t("hist-src-literary", "Literary sources — religious & secular texts"),
                _t("hist-src-foreign", "Foreign accounts — Greek, Chinese, Arab travellers"),
            ]},
            {"name": "Prehistoric Cultures", "topics": [
                _t("hist-pre-paleolithic", "Paleolithic age — tools and sites (Bhimbetka)"),
                _t("hist-pre-mesolithic", "Mesolithic age — microliths, rock art"),
                _t("hist-pre-neolithic", "Neolithic age — agriculture, settlements"),
                _t("hist-pre-chalco", "Chalcolithic cultures — Jorwe, Daimabad (Maharashtra)", mh=True),
            ]},
        ]},
        {"name": "Indus Valley Civilization", "groups": [
            {"name": "IVC", "topics": [
                _t("hist-ivc-extent", "Geographical extent and major sites"),
                _t("hist-ivc-town", "Town planning and architecture"),
                _t("hist-ivc-economy", "Economy, trade and crafts"),
                _t("hist-ivc-religion", "Religion, art and seals"),
                _t("hist-ivc-script", "Script and society"),
                _t("hist-ivc-sites", "Major sites — Harappa, Mohenjo-daro, Lothal, Dholavira, Kalibangan"),
                _t("hist-ivc-decline", "Decline — theories"),
            ]},
        ]},
        {"name": "Vedic Age & Religions", "groups": [
            {"name": "Vedic Period", "topics": [
                _t("hist-ved-early", "Early Vedic (Rigvedic) polity, society, economy"),
                _t("hist-ved-later", "Later Vedic period — changes"),
                _t("hist-ved-literature", "Vedic literature — Vedas, Brahmanas, Upanishads"),
                _t("hist-ved-varna", "Varna system and society"),
            ]},
            {"name": "Heterodox Sects", "topics": [
                _t("hist-rel-jainism", "Jainism — Mahavira, doctrines, councils"),
                _t("hist-rel-jain-spread", "Jain sects (Digambara/Svetambara), literature, art"),
                _t("hist-rel-buddhism", "Buddhism — Buddha, four noble truths"),
                _t("hist-rel-buddhism-councils", "Buddhist councils and schools (Hinayana/Mahayana/Vajrayana)"),
                _t("hist-rel-buddhism-literature", "Buddhist literature and spread"),
                _t("hist-rel-ajivika", "Ajivikas and other sects"),
            ]},
        ]},
        {"name": "Mahajanapadas to Mauryas", "groups": [
            {"name": "Pre-Mauryan", "topics": [
                _t("hist-maha-16", "16 Mahajanapadas and rise of Magadha"),
                _t("hist-maha-persian", "Persian and Macedonian (Alexander) invasions"),
            ]},
            {"name": "Mauryan Empire", "topics": [
                _t("hist-maur-chandragupta", "Chandragupta Maurya and Chanakya"),
                _t("hist-maur-ashoka", "Ashoka — Kalinga war, Dhamma, edicts"),
                _t("hist-maur-admin", "Mauryan administration and economy"),
                _t("hist-maur-art", "Mauryan art and architecture"),
                _t("hist-maur-decline", "Decline of the Mauryas"),
            ]},
        ]},
        {"name": "Post-Mauryan & Gupta Age", "groups": [
            {"name": "Post-Mauryan", "topics": [
                _t("hist-pm-shunga", "Shungas, Kanvas"),
                _t("hist-pm-satavahana", "Satavahanas — Deccan/Maharashtra polity & trade", mh=True),
                _t("hist-pm-indogreek", "Indo-Greeks and Shakas"),
                _t("hist-pm-kushana", "Kushanas — Kanishka, Gandhara/Mathura art"),
                _t("hist-pm-sangam", "Sangam age — Cholas, Cheras, Pandyas"),
                _t("hist-pm-sangam-lit", "Sangam literature and society"),
            ]},
            {"name": "Gupta & Post-Gupta", "topics": [
                _t("hist-gup-rise", "Gupta empire — Samudragupta, Chandragupta II"),
                _t("hist-gup-admin", "Gupta administration, economy, society"),
                _t("hist-gup-golden", "Golden age — science, literature, art"),
                _t("hist-gup-harsha", "Harshavardhana and Pushyabhuti dynasty"),
                _t("hist-gup-vakataka", "Vakatakas and Ajanta (Maharashtra)", mh=True),
            ]},
        ]},
        {"name": "Early Medieval India", "groups": [
            {"name": "Regional Kingdoms", "topics": [
                _t("hist-em-rashtrakuta", "Rashtrakutas (Maharashtra) — Ellora, Kailasa temple", mh=True),
                _t("hist-em-chalukya", "Chalukyas of Badami, Kalyani"),
                _t("hist-em-pallava", "Pallavas and Cholas — administration, art"),
                _t("hist-em-rajput", "Rajput kingdoms and tripartite struggle"),
                _t("hist-em-yadava", "Yadavas of Devagiri (Maharashtra)", mh=True),
            ]},
            {"name": "Early Invasions", "topics": [
                _t("hist-em-ghazni", "Mahmud of Ghazni and Muhammad Ghori"),
            ]},
        ]},
        {"name": "Delhi Sultanate & Provincial Kingdoms", "groups": [
            {"name": "Delhi Sultanate", "topics": [
                _t("hist-ds-slave", "Slave/Mamluk dynasty"),
                _t("hist-ds-khilji", "Khilji dynasty — Alauddin's reforms"),
                _t("hist-ds-tughlaq", "Tughlaq dynasty — Muhammad bin Tughlaq, Firoz Shah"),
                _t("hist-ds-later", "Sayyids and Lodis"),
                _t("hist-ds-admin", "Sultanate administration, economy, society"),
                _t("hist-ds-art", "Indo-Islamic architecture"),
            ]},
            {"name": "Provincial & Deccan", "topics": [
                _t("hist-ds-vijayanagara", "Vijayanagara empire — Krishnadevaraya"),
                _t("hist-ds-bahmani", "Bahmani kingdom and Deccan sultanates", mh=True),
            ]},
        ]},
        {"name": "Mughal Empire", "groups": [
            {"name": "Mughals", "topics": [
                _t("hist-mug-babur", "Babur and foundation; Humayun"),
                _t("hist-mug-sher", "Sher Shah Suri and administration"),
                _t("hist-mug-akbar", "Akbar — conquests, Din-i-Ilahi, Mansabdari"),
                _t("hist-mug-jahangir", "Jahangir and Shah Jahan"),
                _t("hist-mug-aurangzeb", "Aurangzeb — Deccan policy, decline"),
                _t("hist-mug-admin", "Mughal administration — Mansabdari, Zabt"),
                _t("hist-mug-art", "Mughal art, architecture, painting"),
                _t("hist-mug-decline", "Decline of the Mughal empire"),
            ]},
        ]},
        {"name": "Marathas (Maharashtra)", "groups": [
            {"name": "Maratha Empire", "topics": [
                _t("hist-mar-shivaji", "Shivaji — rise, conquests, coronation", mh=True),
                _t("hist-mar-ashtapradhan", "Ashtapradhan and Maratha administration", mh=True),
                _t("hist-mar-sambhaji", "Sambhaji, Rajaram, Tarabai", mh=True),
                _t("hist-mar-peshwa", "Peshwa era — Bajirao I, expansion", mh=True),
                _t("hist-mar-panipat", "Third Battle of Panipat (1761)", mh=True),
                _t("hist-mar-confederacy", "Maratha confederacy — Scindia, Holkar, Gaikwad, Bhosale", mh=True),
                _t("hist-mar-anglo", "Anglo-Maratha wars and fall", mh=True),
            ]},
            {"name": "Maratha Society, Forts & Legacy", "topics": [
                _t("hist-mar-forts", "Maratha forts and naval power (Kanhoji Angre)", ("PRE", "MAINS"), True),
                _t("hist-mar-revenue", "Maratha revenue system — Chauth, Sardeshmukhi", ("PRE", "MAINS"), True),
                _t("hist-mar-society", "Maratha society, culture and administration", ("PRE", "MAINS"), True),
            ]},
        ]},
        {"name": "Art, Culture, Literature & Architecture", "groups": [
            {"name": "Architecture", "topics": [
                _t("hist-art-temple", "Temple architecture — Nagara, Dravida, Vesara"),
                _t("hist-art-cave", "Cave architecture — Ajanta, Ellora, Elephanta (Maharashtra)", mh=True),
                _t("hist-art-stupa", "Buddhist stupas and viharas"),
                _t("hist-art-indoislamic", "Indo-Islamic and colonial architecture"),
            ]},
            {"name": "Performing & Fine Arts", "topics": [
                _t("hist-art-dance", "Classical dance forms"),
                _t("hist-art-music", "Hindustani and Carnatic music"),
                _t("hist-art-painting", "Painting traditions — miniature, folk"),
                _t("hist-art-theatre", "Theatre and folk arts (incl. Maharashtra — Tamasha, Lavani)", mh=True),
            ]},
            {"name": "Literature & Philosophy", "topics": [
                _t("hist-art-literature", "Sanskrit, Prakrit, Tamil and regional literature"),
                _t("hist-art-unesco", "UNESCO World Heritage sites in India"),
                _t("hist-art-fairs", "Major fairs, festivals and folk culture"),
            ]},
            {"name": "Classical Dance Forms", "topics": [
                _t("hist-dance-bharatanatyam", "Bharatanatyam (Tamil Nadu)"),
                _t("hist-dance-kathak", "Kathak (North India)"),
                _t("hist-dance-kathakali", "Kathakali (Kerala)"),
                _t("hist-dance-kuchipudi", "Kuchipudi (Andhra Pradesh)"),
                _t("hist-dance-odissi", "Odissi (Odisha)"),
                _t("hist-dance-manipuri", "Manipuri (Manipur)"),
                _t("hist-dance-mohiniyattam", "Mohiniyattam (Kerala)"),
                _t("hist-dance-sattriya", "Sattriya (Assam)"),
            ]},
            {"name": "Indian Philosophy (Six Darshanas)", "topics": [
                _t("hist-phil-nyaya", "Nyaya"),
                _t("hist-phil-vaisheshika", "Vaisheshika"),
                _t("hist-phil-samkhya", "Samkhya"),
                _t("hist-phil-yoga", "Yoga"),
                _t("hist-phil-mimamsa", "Mimamsa"),
                _t("hist-phil-vedanta", "Vedanta"),
            ]},
            {"name": "Music & Languages", "topics": [
                _t("hist-music-hindustani", "Hindustani music — gharanas, instruments"),
                _t("hist-music-carnatic", "Carnatic music — trinity, forms"),
                _t("hist-music-folk", "Folk music traditions of India"),
                _t("hist-lang-classical", "Classical languages of India (incl. Marathi)", ("PRE", "MAINS"), True),
            ]},
        ]},
        {"name": "Bhakti & Sufi Movements", "groups": [
            {"name": "Bhakti & Sufi", "topics": [
                _t("hist-bhk-nature", "Bhakti movement — origins, philosophy, saguna/nirguna"),
                _t("hist-bhk-north", "North Indian saints — Kabir, Nanak, Tulsidas, Surdas, Mirabai"),
                _t("hist-bhk-south", "South Indian Bhakti — Alvars and Nayanars"),
                _t("hist-bhk-sufi", "Sufi movement — silsilas, Chishti, Suhrawardi"),
            ]},
            {"name": "Maharashtra Saints (Varkari)", "topics": [
                _t("hist-bhk-dnyaneshwar", "Dnyaneshwar — Dnyaneshwari", mh=True),
                _t("hist-bhk-namdev", "Namdev", mh=True),
                _t("hist-bhk-eknath", "Eknath", mh=True),
                _t("hist-bhk-tukaram", "Tukaram — Abhangas", mh=True),
                _t("hist-bhk-ramdas", "Samarth Ramdas — Dasbodh", mh=True),
            ]},
        ]},
        {"name": "Modern India — British Conquest & Economy", "groups": [
            {"name": "British Expansion", "topics": [
                _t("hist-mod-plassey", "Battle of Plassey (1757)"),
                _t("hist-mod-buxar", "Battle of Buxar (1764) and Diwani"),
                _t("hist-mod-mysore", "Anglo-Mysore wars — Hyder Ali, Tipu Sultan"),
                _t("hist-mod-sikh", "Anglo-Sikh wars and annexation"),
                _t("hist-mod-doctrine", "Doctrine of Lapse and subsidiary alliance"),
            ]},
            {"name": "Governors-General & Viceroys", "topics": [
                _t("hist-gg-warren", "Warren Hastings"),
                _t("hist-gg-cornwallis", "Cornwallis — Permanent Settlement"),
                _t("hist-gg-wellesley", "Wellesley — Subsidiary Alliance"),
                _t("hist-gg-bentinck", "William Bentinck — social reforms"),
                _t("hist-gg-dalhousie", "Dalhousie — Doctrine of Lapse, railways"),
                _t("hist-gg-canning", "Canning — first Viceroy, 1857"),
                _t("hist-gg-ripon", "Ripon — local self-government, Ilbert Bill"),
                _t("hist-gg-curzon", "Curzon — partition of Bengal"),
                _t("hist-gg-mountbatten", "Mountbatten — last Viceroy"),
            ]},
            {"name": "Economic Impact", "topics": [
                _t("hist-mod-landrev", "Land revenue systems — Permanent, Ryotwari, Mahalwari"),
                _t("hist-mod-deind", "Deindustrialization and drain of wealth"),
                _t("hist-mod-railways", "Railways, commercialization of agriculture"),
                _t("hist-mod-famine", "Famines and famine policy"),
            ]},
            {"name": "Constitutional Development (British)", "topics": [
                _t("hist-act-regulating1773", "Regulating Act 1773"),
                _t("hist-act-pitts1784", "Pitt's India Act 1784"),
                _t("hist-act-charter1813", "Charter Act 1813"),
                _t("hist-act-charter1833", "Charter Act 1833"),
                _t("hist-act-charter1853", "Charter Act 1853"),
                _t("hist-act-goi1858", "Government of India Act 1858"),
                _t("hist-act-councils1861", "Indian Councils Act 1861"),
                _t("hist-act-councils1892", "Indian Councils Act 1892"),
                _t("hist-act-morley1909", "Morley-Minto Reforms 1909"),
                _t("hist-act-mont1919", "Montagu-Chelmsford Reforms / GoI Act 1919"),
                _t("hist-act-goi1935", "Government of India Act 1935"),
                _t("hist-mod-civilservice", "Civil services, police and judiciary under the British"),
            ]},
            {"name": "Social Legislation", "topics": [
                _t("hist-soc-sati", "Abolition of Sati (1829)"),
                _t("hist-soc-widow", "Widow Remarriage Act (1856)"),
                _t("hist-soc-consent", "Age of Consent Act (1891)"),
            ]},
        ]},
        {"name": "1857 Revolt & Socio-Religious Reform", "groups": [
            {"name": "Revolt of 1857", "topics": [
                _t("hist-1857-causes", "Causes of the Revolt of 1857"),
                _t("hist-1857-centres", "Centres and leaders of the revolt"),
                _t("hist-1857-failure", "Failure, consequences and aftermath"),
            ]},
            {"name": "Socio-Religious Reform", "topics": [
                _t("hist-srm-brahmo", "Brahmo Samaj — Raja Ram Mohan Roy"),
                _t("hist-srm-arya", "Arya Samaj — Dayananda Saraswati"),
                _t("hist-srm-ramakrishna", "Ramakrishna Mission — Vivekananda"),
                _t("hist-srm-aligarh", "Aligarh movement, Theosophical Society"),
                _t("hist-srm-mh", "Maharashtra reformers — Prarthana Samaj, Ranade, Agarkar", mh=True),
                _t("hist-srm-phule", "Jyotiba & Savitribai Phule — Satyashodhak Samaj", mh=True),
                _t("hist-srm-shahu", "Shahu Maharaj — social reforms", mh=True),
            ]},
        ]},
        {"name": "Indian National Movement", "groups": [
            {"name": "Early Nationalism", "topics": [
                _t("hist-inm-inc", "Formation of INC (1885); Moderates"),
                _t("hist-inm-extremist", "Extremists — Lal-Bal-Pal, Tilak", mh=True),
                _t("hist-inm-partition", "Partition of Bengal and Swadeshi movement"),
                _t("hist-inm-surat", "Surat split, Morley-Minto reforms"),
                _t("hist-inm-revolutionary", "Revolutionary nationalism — phase I"),
            ]},
            {"name": "Gandhian Era", "topics": [
                _t("hist-inm-champaran", "Gandhi's early movements — Champaran, Kheda, Ahmedabad"),
                _t("hist-inm-rowlatt", "Rowlatt Act and Jallianwala Bagh"),
                _t("hist-inm-ncm", "Non-Cooperation and Khilafat movement"),
                _t("hist-inm-swaraj", "Swaraj Party, Simon Commission"),
                _t("hist-inm-cdm", "Civil Disobedience Movement, Dandi March"),
                _t("hist-inm-rtc", "Round Table Conferences, Poona Pact"),
                _t("hist-inm-goi1935", "Government of India Act 1935 and provincial elections"),
                _t("hist-inm-qim", "Quit India Movement (1942)"),
                _t("hist-inm-ina", "Subhas Chandra Bose and INA"),
                _t("hist-inm-revolutionary2", "Revolutionary activities — HSRA, Bhagat Singh"),
            ]},
            {"name": "Independence & Partition", "topics": [
                _t("hist-inm-cabinet", "Cabinet Mission, interim government"),
                _t("hist-inm-mountbatten", "Mountbatten Plan and partition"),
                _t("hist-inm-independence", "Independence and integration challenges"),
            ]},
            {"name": "Peasant & Tribal Movements", "topics": [
                _t("hist-pm-indigo", "Indigo Revolt (1859)"),
                _t("hist-pm-deccan", "Deccan riots (Maharashtra)", ("PRE", "MAINS"), True),
                _t("hist-pm-santhal", "Santhal and Munda (Birsa) uprisings"),
                _t("hist-pm-champaranmov", "Champaran and Bardoli satyagraha"),
                _t("hist-pm-moplah", "Moplah and other peasant revolts"),
                _t("hist-pm-workers", "Trade union and workers' movements"),
            ]},
            {"name": "Press, Education & Personalities", "topics": [
                _t("hist-press-newspapers", "Growth of press and newspapers"),
                _t("hist-press-education", "Development of modern education"),
                _t("hist-press-women", "Women in the freedom struggle"),
                _t("hist-press-moderate-leaders", "Moderate leaders — Naoroji, Gokhale, Mehta"),
                _t("hist-press-gandhi-ideas", "Gandhian ideas — Satyagraha, Sarvodaya, Trusteeship"),
            ]},
        ]},
        {"name": "Maharashtra Modern History", "groups": [
            {"name": "Maharashtra in Freedom & After", "topics": [
                _t("hist-mhm-ambedkar", "B.R. Ambedkar — Dalit movement, Mahad, temple entry", ("PRE", "MAINS"), mh=True),
                _t("hist-mhm-nondbrahmin", "Non-Brahmin movement in Maharashtra", ("PRE", "MAINS"), mh=True),
                _t("hist-mhm-tribal", "Tribal and peasant movements in Maharashtra", ("PRE", "MAINS"), mh=True),
                _t("hist-mhm-samyukta", "Samyukta Maharashtra movement and formation of state (1960)", ("PRE", "MAINS"), mh=True),
            ]},
        ]},
        {"name": "Post-Independence India", "groups": [
            {"name": "Nation Building", "topics": [
                _t("hist-pi-integration", "Integration of princely states — Sardar Patel"),
                _t("hist-pi-linguistic", "Linguistic reorganization of states", ("PRE", "MAINS"), mh=True),
                _t("hist-pi-constitution", "Making of the Constitution"),
                _t("hist-pi-foreign", "Early foreign policy — Non-Alignment"),
                _t("hist-pi-economy", "Planned economy and Green Revolution"),
                _t("hist-pi-wars", "Wars (1962, 1965, 1971) and emergency"),
                _t("hist-pi-recent", "Liberalization 1991 and recent developments"),
                _t("hist-pi-pms", "Prime ministers and major policy shifts"),
                _t("hist-pi-movements", "Social movements post-1947 (JP, anti-emergency)"),
                _t("hist-pi-science", "Science, technology and institution building"),
            ]},
        ]},
        {"name": "World History", "groups": [
            {"name": "Revolutions & Industrialization", "topics": [
                _t("hist-wh-renaissance", "Renaissance and Reformation", ("MAINS",)),
                _t("hist-wh-industrial", "Industrial Revolution and its impact", ("MAINS",)),
                _t("hist-wh-american", "American Revolution", ("MAINS",)),
                _t("hist-wh-french", "French Revolution", ("MAINS",)),
                _t("hist-wh-russian", "Russian Revolution (1917)", ("MAINS",)),
            ]},
            {"name": "20th Century", "topics": [
                _t("hist-wh-ww1", "World War I — causes and consequences", ("MAINS",)),
                _t("hist-wh-interwar", "Inter-war period, Great Depression, rise of fascism", ("MAINS",)),
                _t("hist-wh-ww2", "World War II — causes and consequences", ("MAINS",)),
                _t("hist-wh-colonization", "Colonization and decolonization", ("MAINS",)),
                _t("hist-wh-coldwar", "Cold War and its end", ("MAINS",)),
                _t("hist-wh-un", "Formation of the UN and world order", ("MAINS",)),
            ]},
            {"name": "Political Philosophies", "topics": [
                _t("hist-wh-capitalism", "Capitalism — ideas and impact", ("MAINS",)),
                _t("hist-wh-socialism", "Socialism and communism", ("MAINS",)),
                _t("hist-wh-fascism", "Fascism and Nazism", ("MAINS",)),
                _t("hist-wh-nationalism", "Nationalism and liberalism", ("MAINS",)),
                _t("hist-wh-imperialism", "Imperialism and colonialism", ("MAINS",)),
            ]},
            {"name": "Regions & Movements", "topics": [
                _t("hist-wh-unification", "Unification of Germany and Italy", ("MAINS",)),
                _t("hist-wh-usa-civil", "American Civil War and abolition of slavery", ("MAINS",)),
                _t("hist-wh-china", "Chinese Revolution (1949)", ("MAINS",)),
                _t("hist-wh-africa", "African and Asian decolonization", ("MAINS",)),
                _t("hist-wh-latin", "Latin American independence movements", ("MAINS",)),
                _t("hist-wh-mideast", "West Asia — formation of Israel, conflicts", ("MAINS",)),
            ]},
        ]},
    ],
}
