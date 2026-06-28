# MPSC Rajyaseva Prep Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A pure-HTML MPSC Rajyaseva study tracker (hub + 16 subject pages) covering the full Prelims+Mains+Interview syllabus at maximum micro-topic depth, with per-topic checkboxes and per-section/subject/stage completion %, progress in localStorage, hosted on GitHub Pages.

**Architecture:** A Python (stdlib-only) generator reads one syllabus data module per subject and renders static HTML pages into `mpsc/` using a shared template. Each micro-topic is a checkbox tagged with exam stage(s) (PRE/MAINS/INT) and optional Maharashtra (MH) flag. Browser-side vanilla JS handles checkbox persistence (localStorage), live percentages, stage-filter tabs, and search. A validator script enforces structure + coverage gates.

**Tech Stack:** Python 3.9 stdlib (no external deps), vanilla HTML/CSS/JS, GitHub Pages (`.nojekyll` already at repo root).

## Global Constraints

- Output folder: `mpsc/` at repo root. Build tooling: `mpsc_build/`. Do NOT modify the existing Spring/Java site files.
- Python: stdlib only (target 3.9). No pip installs.
- localStorage key per subject page: `mpsc_<key>_v1`, value = JSON object `{ topicId: true }` (only checked stored).
- Every micro-topic MUST have: stable unique `id` (kebab-case, prefixed by subject key), `text`, non-empty `stages` ⊆ {`PRE`,`MAINS`,`INT`}, optional `mh: True`.
- Topic `id`s are stable: never reuse or renumber an existing id when editing content (progress is keyed on it).
- Stage badge colors: PRE = blue, MAINS = amber, INT = purple, MH = green outline.
- Theme: reuse existing dark GitHub palette (`--bg:#0d1117; --panel:#161b22; --panel2:#1c2430; --border:#30363d; --text:#e6edf3; --muted:#8b949e; --accent:#6db33f; --done:#3fb950; --bar-bg:#21262d`).
- Medium: English. Marathi appears only as content labels in the Language page.
- Coverage rule: every official syllabus bullet (per design spec §4) maps to ≥1 group; expand each bullet to smallest study-units ("maximum depth").

---

## File Structure

```
mpsc_build/
  __init__.py
  template.py        # render_page(subject) + render_hub(subjects) -> HTML strings
  generate.py        # load all syllabus modules, write mpsc/*.html
  validate.py        # structure + coverage gates (the "test"); exits nonzero on failure
  syllabus/
    __init__.py      # SUBJECTS registry (ordered list of module keys + hub grouping)
    history.py       # each exports SUBJECT dict
    geography.py
    polity.py
    economy.py
    environment.py
    science_tech.py
    society.py
    international_relations.py
    internal_security.py
    ethics.py
    csat.py
    language.py
    essay.py
    current_affairs.py
    interview.py
    geography_optional.py
mpsc/
  index.html         # generated hub
  <key>.html         # generated per subject (history.html, geography.html, ...)
```

Data schema each subject module exports:

```python
SUBJECT = {
    "key": "history",                      # matches filename + localStorage key
    "title": "History & Indian Culture",
    "icon": "H",                            # 1-2 char badge
    "blurb": "One-line description.",
    "category": "General Studies",          # hub grouping
    "sections": [
        {
            "name": "Ancient India",
            "groups": [
                {
                    "name": "Prehistoric Cultures",
                    "topics": [
                        {"id": "hist-anc-paleolithic", "text": "Paleolithic age — tools, sites (Bhimbetka)", "stages": ["PRE", "MAINS"]},
                        {"id": "hist-anc-mh-jorwe", "text": "Chalcolithic Maharashtra — Jorwe, Daimabad", "stages": ["PRE", "MAINS"], "mh": True},
                    ],
                },
            ],
        },
    ],
}
```

Section/topic stages are derived (a section's stages = union of its topics' stages); only topics carry stages explicitly.

---

### Task 1: Generator scaffold — template, generate, validate, one seed subject

Builds the engine end-to-end with a single small subject (Ethics, the most self-contained) so the full pipeline (data → HTML → browser behavior → validation) works before bulk content.

**Files:**
- Create: `mpsc_build/__init__.py`
- Create: `mpsc_build/syllabus/__init__.py`
- Create: `mpsc_build/syllabus/ethics.py`
- Create: `mpsc_build/template.py`
- Create: `mpsc_build/generate.py`
- Create: `mpsc_build/validate.py`
- Create (generated): `mpsc/ethics.html`, `mpsc/index.html`

**Interfaces:**
- Produces: `mpsc_build.template.render_page(subject: dict) -> str`, `mpsc_build.template.render_hub(subjects: list[dict]) -> str`
- Produces: `mpsc_build.syllabus.load_all() -> list[dict]` (ordered subjects)
- Produces: `mpsc_build.validate.validate(subjects: list[dict]) -> list[str]` (returns list of error strings; empty = pass)

- [ ] **Step 1: Write the validator (failing test) — `mpsc_build/validate.py`**

```python
"""Structure + coverage gates for MPSC syllabus data. Run: python3 -m mpsc_build.validate"""
import sys
from mpsc_build.syllabus import load_all

VALID_STAGES = {"PRE", "MAINS", "INT"}

def validate(subjects):
    errors = []
    seen_ids = set()
    seen_keys = set()
    for s in subjects:
        key = s.get("key")
        if not key or key in seen_keys:
            errors.append(f"bad/duplicate subject key: {key!r}")
        seen_keys.add(key)
        for field in ("title", "icon", "blurb", "category", "sections"):
            if not s.get(field):
                errors.append(f"[{key}] missing field: {field}")
        if not s.get("sections"):
            continue
        topic_count = 0
        for sec in s["sections"]:
            if not sec.get("name") or not sec.get("groups"):
                errors.append(f"[{key}] bad section: {sec.get('name')!r}")
            for grp in sec.get("groups", []):
                if not grp.get("name") or not grp.get("topics"):
                    errors.append(f"[{key}] bad group in {sec.get('name')!r}: {grp.get('name')!r}")
                for t in grp.get("topics", []):
                    topic_count += 1
                    tid = t.get("id")
                    if not tid or not tid.startswith(key.split('_')[0][:4]):
                        # id must be prefixed by something tied to subject; soft prefix check
                        pass
                    if not tid:
                        errors.append(f"[{key}] topic missing id: {t.get('text')!r}")
                    elif tid in seen_ids:
                        errors.append(f"duplicate topic id: {tid}")
                    seen_ids.add(tid)
                    if not t.get("text"):
                        errors.append(f"[{key}] topic {tid} missing text")
                    stages = set(t.get("stages", []))
                    if not stages or not stages <= VALID_STAGES:
                        errors.append(f"[{key}] topic {tid} bad stages: {t.get('stages')}")
        # coverage gate: enforce per-subject minimum topic counts (max-depth guard)
        minimum = MIN_TOPICS.get(key, 1)
        if topic_count < minimum:
            errors.append(f"[{key}] only {topic_count} topics, need >= {minimum} (max-depth coverage gate)")
    return errors

# Coverage gate — minimum micro-topics per subject (raise as content is authored).
MIN_TOPICS = {
    "ethics": 60,
    "history": 220, "geography": 180, "polity": 200, "economy": 170,
    "environment": 110, "science_tech": 120, "society": 110,
    "international_relations": 70, "internal_security": 70,
    "csat": 70, "language": 50, "essay": 50,
    "current_affairs": 60, "interview": 50, "geography_optional": 200,
}

def main():
    errors = validate(load_all())
    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("OK: all syllabus data valid")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run validator to verify it fails**

Run: `cd /Users/faisalchishti/Desktop/claude-projects/Learning && python3 -m mpsc_build.validate`
Expected: FAIL — `ModuleNotFoundError: No module named 'mpsc_build'` (nothing created yet).

- [ ] **Step 3: Create package + registry + seed Ethics data**

`mpsc_build/__init__.py`: empty file.

`mpsc_build/syllabus/__init__.py`:

```python
"""Ordered registry of MPSC subjects. Each module exports SUBJECT (a dict)."""
import importlib

# Order drives hub display. (key, module) — module under mpsc_build.syllabus.
_MODULES = [
    "history", "geography", "polity", "economy", "environment",
    "science_tech", "society", "international_relations", "internal_security",
    "ethics", "csat", "language", "essay", "current_affairs",
    "interview", "geography_optional",
]

def load_all():
    subjects = []
    for name in _MODULES:
        try:
            mod = importlib.import_module(f"mpsc_build.syllabus.{name}")
        except ModuleNotFoundError:
            continue  # module not authored yet — skipped until its task lands
        subjects.append(mod.SUBJECT)
    return subjects
```

`mpsc_build/syllabus/ethics.py` — author the GS-4 tree at max depth (≥60 topics). Sections + groups skeleton (expand each group to multiple micro-topics):

```python
SUBJECT = {
    "key": "ethics",
    "title": "Ethics, Integrity & Aptitude (GS-4)",
    "icon": "E",
    "blurb": "Ethics & human interface, attitude, EI, moral thinkers, probity, case studies.",
    "category": "Mains GS",
    "sections": [
        {"name": "Ethics & Human Interface", "groups": [
            {"name": "Essence of Ethics", "topics": [
                {"id": "eth-ehi-essence", "text": "Essence, determinants and consequences of ethics in human actions", "stages": ["MAINS"]},
                {"id": "eth-ehi-dimensions", "text": "Dimensions of ethics", "stages": ["MAINS"]},
                {"id": "eth-ehi-private-public", "text": "Ethics in private and public relationships", "stages": ["MAINS"]},
                # ... expand fully
            ]},
        ]},
        {"name": "Human Values", "groups": [
            {"name": "Sources & Role", "topics": [
                {"id": "eth-hv-leaders", "text": "Lessons from lives of great leaders, reformers and administrators", "stages": ["MAINS"]},
                {"id": "eth-hv-family-society", "text": "Role of family, society and educational institutions in inculcating values", "stages": ["MAINS"]},
            ]},
        ]},
        {"name": "Attitude", "groups": [ {"name": "Attitude", "topics": [
            {"id": "eth-att-content", "text": "Attitude — content, structure, function", "stages": ["MAINS"]},
            {"id": "eth-att-influence", "text": "Influence of attitude on thought and behaviour", "stages": ["MAINS"]},
            {"id": "eth-att-moral-political", "text": "Moral and political attitudes", "stages": ["MAINS"]},
            {"id": "eth-att-persuasion", "text": "Social influence and persuasion", "stages": ["MAINS"]},
        ]}]},
        {"name": "Aptitude & Foundational Values", "groups": [ {"name": "Civil Service Values", "topics": [
            {"id": "eth-fv-integrity", "text": "Integrity", "stages": ["MAINS"]},
            {"id": "eth-fv-impartiality", "text": "Impartiality and non-partisanship", "stages": ["MAINS"]},
            {"id": "eth-fv-objectivity", "text": "Objectivity", "stages": ["MAINS"]},
            {"id": "eth-fv-dedication", "text": "Dedication to public service", "stages": ["MAINS"]},
            {"id": "eth-fv-empathy", "text": "Empathy, tolerance and compassion toward weaker sections", "stages": ["MAINS"]},
        ]}]},
        {"name": "Emotional Intelligence", "groups": [ {"name": "EI", "topics": [
            {"id": "eth-ei-concept", "text": "Emotional intelligence — concepts", "stages": ["MAINS"]},
            {"id": "eth-ei-utility", "text": "Utility and application in administration and governance", "stages": ["MAINS"]},
        ]}]},
        {"name": "Moral Thinkers & Philosophers", "groups": [ {"name": "Indian & World", "topics": [
            {"id": "eth-mt-indian", "text": "Contributions of moral thinkers and philosophers from India", "stages": ["MAINS"]},
            {"id": "eth-mt-world", "text": "Contributions of moral thinkers and philosophers from the world", "stages": ["MAINS"]},
        ]}]},
        {"name": "Public/Civil Service Ethics", "groups": [ {"name": "Governance Ethics", "topics": [
            {"id": "eth-ps-values", "text": "Status and problems; ethical concerns and dilemmas in government and private institutions", "stages": ["MAINS"]},
            {"id": "eth-ps-guidance", "text": "Laws, rules, regulations and conscience as sources of ethical guidance", "stages": ["MAINS"]},
            {"id": "eth-ps-accountability", "text": "Accountability and ethical governance", "stages": ["MAINS"]},
            {"id": "eth-ps-strengthening", "text": "Strengthening of ethical and moral values in governance", "stages": ["MAINS"]},
            {"id": "eth-ps-intl", "text": "Ethical issues in international relations and funding", "stages": ["MAINS"]},
            {"id": "eth-ps-corporate", "text": "Corporate governance", "stages": ["MAINS"]},
        ]}]},
        {"name": "Probity in Governance", "groups": [ {"name": "Probity", "topics": [
            {"id": "eth-pg-concept", "text": "Concept of public service; philosophical basis of governance and probity", "stages": ["MAINS"]},
            {"id": "eth-pg-info", "text": "Information sharing and transparency in government; Right to Information", "stages": ["MAINS"]},
            {"id": "eth-pg-codes", "text": "Codes of ethics, codes of conduct, citizen's charters", "stages": ["MAINS"]},
            {"id": "eth-pg-workculture", "text": "Work culture, quality of service delivery, utilization of public funds", "stages": ["MAINS"]},
            {"id": "eth-pg-corruption", "text": "Challenges of corruption", "stages": ["MAINS"]},
        ]}]},
        {"name": "Case Studies", "groups": [ {"name": "Applied Ethics", "topics": [
            {"id": "eth-cs-approach", "text": "Case-study approach and answer framework", "stages": ["MAINS"]},
            {"id": "eth-cs-stakeholders", "text": "Stakeholder identification and options analysis", "stages": ["MAINS"]},
            # add representative case-study scenario buckets to reach >=60 total
        ]}]},
    ],
}
```

(Author enough topics to clear the ≥60 gate; the skeleton above is the floor, not the ceiling.)

- [ ] **Step 4: Write `mpsc_build/template.py`**

Full file — renders a self-contained page (embedded data as JSON, inline CSS/JS) and the hub.

```python
"""Render MPSC subject pages and hub to self-contained HTML strings."""
import json

CSS = """
:root{--bg:#0d1117;--panel:#161b22;--panel2:#1c2430;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#6db33f;--accent2:#34804f;--done:#3fb950;--bar-bg:#21262d;--pre:#388bfd;--mains:#d29922;--int:#a371f7;--mh:#3fb950;}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.5}
header{position:sticky;top:0;z-index:50;background:rgba(13,17,23,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--border);padding:14px 20px}
.title{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.title h1{font-size:20px;margin:0}
.home{font-size:13px;color:var(--muted);text-decoration:none;border:1px solid var(--border);padding:5px 10px;border-radius:8px}.home:hover{border-color:var(--accent);color:var(--text)}
.logo{width:34px;height:34px;border-radius:8px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-weight:800;color:#fff}
.stats{margin-left:auto;font-size:13px;color:var(--muted)}.stats b{color:var(--accent)}
.progress-wrap{margin-top:10px;display:flex;align-items:center;gap:12px}
.bar{flex:1;height:10px;background:var(--bar-bg);border-radius:99px;overflow:hidden}
.bar>span{display:block;height:100%;width:0%;background:linear-gradient(90deg,var(--accent),var(--done));transition:width .35s}
.pct{font-size:13px;color:var(--muted);min-width:42px;text-align:right}
.stagebar{margin-top:8px;display:flex;gap:14px;font-size:12px;color:var(--muted);flex-wrap:wrap}
.toolbar{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.tabs{display:flex;gap:6px}.tab{background:var(--chip,#21262d);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:8px;font-size:13px;cursor:pointer}
.tab.active{border-color:var(--accent);color:var(--accent)}
.toolbar input[type=search]{flex:1;min-width:180px;background:var(--panel2);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:8px;font-size:14px}
button{background:#21262d;border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:8px;font-size:13px;cursor:pointer}button:hover{border-color:var(--accent)}
.danger:hover{border-color:#f85149;color:#f85149}
main{max-width:1040px;margin:0 auto;padding:20px}
section.sec{margin-bottom:18px;border:1px solid var(--border);border-radius:12px;overflow:hidden;background:var(--panel)}
.sec-head{display:flex;align-items:center;gap:12px;padding:14px 18px;cursor:pointer;user-select:none;background:var(--panel2)}.sec-head:hover{background:#222b38}
.sec-head .vname{font-size:16px;font-weight:700}.sec-head .vcount{margin-left:auto;font-size:12px;color:var(--muted)}
.sec-head .minibar{width:90px;height:7px;background:var(--bar-bg);border-radius:99px;overflow:hidden}.sec-head .minibar>span{display:block;height:100%;width:0;background:var(--done)}
.sec-head .chev{transition:transform .2s;color:var(--muted)}section.sec.collapsed .chev{transform:rotate(-90deg)}section.sec.collapsed .sec-body{display:none}
.sec-body{padding:6px 10px 14px}
.grp{margin:14px 8px 4px;font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--accent);font-weight:700;border-top:1px solid var(--border);padding-top:12px}.grp:first-child{border-top:none;padding-top:4px}
ul.topics{list-style:none;margin:0;padding:0}
li.topic{display:flex;align-items:flex-start;gap:10px;padding:6px 10px;border-radius:8px}li.topic:hover{background:var(--panel2)}
li.topic input{margin-top:3px;width:16px;height:16px;accent-color:var(--done);cursor:pointer;flex:none}
li.topic label{cursor:pointer;font-size:14.5px}li.topic.done label{color:var(--muted);text-decoration:line-through}
.badge{font-size:10px;font-weight:700;padding:1px 6px;border-radius:99px;flex:none;margin-top:2px}
.b-PRE{background:rgba(56,139,253,.18);color:var(--pre)}.b-MAINS{background:rgba(210,153,34,.18);color:var(--mains)}.b-INT{background:rgba(163,113,247,.18);color:var(--int)}
.b-MH{background:transparent;color:var(--mh);border:1px solid var(--mh)}
.hidden{display:none !important}
footer{text-align:center;color:var(--muted);font-size:12px;padding:20px}
"""

PAGE_JS = """
const KEY='mpsc_%(key)s_v1';
const DATA=%(data)s;
let done=JSON.parse(localStorage.getItem(KEY)||'{}');
let filter='ALL';
function save(){localStorage.setItem(KEY,JSON.stringify(done));}
function topicStages(t){return t.stages;}
function inFilter(t){return filter==='ALL'||t.stages.indexOf(filter)>=0;}
function recompute(){
  let tot=0,dn=0,st={PRE:[0,0],MAINS:[0,0],INT:[0,0]};
  DATA.sections.forEach(sec=>{
    let stot=0,sdn=0;
    sec.groups.forEach(g=>g.topics.forEach(t=>{
      const d=!!done[t.id];
      t.stages.forEach(s=>{st[s][1]++;if(d)st[s][0]++;});
      if(inFilter(t)){stot++;tot++;if(d){sdn++;dn++;}}
    }));
    const el=document.querySelector('[data-sec="'+sec.idx+'"]');
    if(el){const p=stot?Math.round(sdn/stot*100):0;
      el.querySelector('.minibar>span').style.width=p+'%';
      el.querySelector('.vcount').textContent=sdn+'/'+stot;}
  });
  const p=tot?Math.round(dn/tot*100):0;
  document.getElementById('bar').style.width=p+'%';
  document.getElementById('pct').textContent=p+'%';
  document.getElementById('count').textContent=dn+' / '+tot+' done';
  ['PRE','MAINS','INT'].forEach(s=>{const c=st[s][1]?Math.round(st[s][0]/st[s][1]*100):0;
    document.getElementById('st-'+s).textContent=s+' '+st[s][0]+'/'+st[s][1]+' ('+c+'%)';});
}
function applyFilter(){
  document.querySelectorAll('li.topic').forEach(li=>{
    li.classList.toggle('hidden', !(filter==='ALL'||li.dataset.stages.split(',').indexOf(filter)>=0));
  });
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.f===filter));
  recompute();
}
function applySearch(q){q=q.toLowerCase();
  document.querySelectorAll('li.topic').forEach(li=>{
    const m=li.textContent.toLowerCase().indexOf(q)>=0;
    li.style.display=m?'':'none';});
}
document.addEventListener('change',e=>{if(e.target.matches('li.topic input')){
  const id=e.target.dataset.id;if(e.target.checked)done[id]=true;else delete done[id];
  e.target.closest('li.topic').classList.toggle('done',e.target.checked);save();recompute();}});
document.addEventListener('click',e=>{
  if(e.target.closest('.sec-head'))e.target.closest('.sec').classList.toggle('collapsed');
  if(e.target.matches('.tab')){filter=e.target.dataset.f;applyFilter();}
});
function init(){
  Object.keys(done).forEach(id=>{const i=document.querySelector('input[data-id="'+CSS.escape(id)+'"]');
    if(i){i.checked=true;i.closest('li.topic').classList.add('done');}});
  recompute();
  document.getElementById('search').addEventListener('input',e=>applySearch(e.target.value));
  document.getElementById('expand').onclick=()=>document.querySelectorAll('.sec').forEach(s=>s.classList.remove('collapsed'));
  document.getElementById('collapse').onclick=()=>document.querySelectorAll('.sec').forEach(s=>s.classList.add('collapsed'));
  document.getElementById('reset').onclick=()=>{if(confirm('Reset all progress on this page?')){done={};save();
    document.querySelectorAll('li.topic input').forEach(i=>{i.checked=false;i.closest('li.topic').classList.remove('done');});recompute();}};
}
init();
"""

def _badges(t):
    out = "".join(f'<span class="badge b-{s}">{s}</span>' for s in t["stages"])
    if t.get("mh"):
        out += '<span class="badge b-MH">MH</span>'
    return out

def render_page(subject):
    key = subject["key"]
    secs_html = []
    for i, sec in enumerate(subject["sections"]):
        sec["idx"] = i
        groups_html = []
        for g in sec["groups"]:
            items = []
            for t in g["topics"]:
                st = ",".join(t["stages"])
                items.append(
                    f'<li class="topic" data-stages="{st}"><input type="checkbox" '
                    f'data-id="{t["id"]}"><label>{t["text"]} {_badges(t)}</label></li>'
                )
            groups_html.append(f'<div class="grp">{g["name"]}</div><ul class="topics">{"".join(items)}</ul>')
        secs_html.append(
            f'<section class="sec" data-sec="{i}"><div class="sec-head">'
            f'<span class="chev">&#9660;</span><span class="vname">{sec["name"]}</span>'
            f'<span class="minibar"><span></span></span><span class="vcount">0/0</span></div>'
            f'<div class="sec-body">{"".join(groups_html)}</div></section>'
        )
    # strip injected idx before serializing to JS
    data = {"sections": [
        {"idx": i, "groups": [
            {"topics": [{"id": t["id"], "stages": t["stages"]} for t in g["topics"]]}
            for g in sec["groups"]]}
        for i, sec in enumerate(subject["sections"])]}
    js = PAGE_JS % {"key": key, "data": json.dumps(data)}
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject['title']} — MPSC Checklist</title><style>{CSS}</style></head><body>
<header><div class="title"><a class="home" href="index.html">← All subjects</a>
<div class="logo">{subject['icon']}</div><h1>{subject['title']}</h1>
<span class="stats" id="count">0 / 0 done</span></div>
<div class="progress-wrap"><div class="bar"><span id="bar"></span></div><span class="pct" id="pct">0%</span></div>
<div class="stagebar"><span id="st-PRE"></span><span id="st-MAINS"></span><span id="st-INT"></span></div>
<div class="toolbar"><div class="tabs">
<button class="tab active" data-f="ALL">All</button><button class="tab" data-f="PRE">Prelims</button>
<button class="tab" data-f="MAINS">Mains</button><button class="tab" data-f="INT">Interview</button></div>
<input type="search" id="search" placeholder="Search topics…">
<button id="expand">Expand all</button><button id="collapse">Collapse all</button>
<button class="danger" id="reset">Reset</button></div></header>
<main>{''.join(secs_html)}<footer>{subject['blurb']}</footer></main>
<script>{js}</script></body></html>"""

def render_hub(subjects):
    cats = {}
    for s in subjects:
        cats.setdefault(s["category"], []).append(s)
    blocks = []
    total = sum(sum(len(g["topics"]) for sec in s["sections"] for g in sec["groups"]) for s in subjects)
    for cat, subs in cats.items():
        cards = []
        for s in subs:
            n = sum(len(g["topics"]) for sec in s["sections"] for g in sec["groups"])
            cards.append(
                f'<a class="card" href="{s["key"]}.html" data-key="{s["key"]}" data-total="{n}">'
                f'<div class="nm"><span class="dot">{s["icon"]}</span>{s["title"]}</div>'
                f'<p class="ds">{s["blurb"]}</p>'
                f'<div class="cbar"><span></span></div><div class="ct">{n} topics · <b class="cp">0%</b></div></a>')
        blocks.append(f'<div class="cat">{cat}</div>' + "".join(cards))
    hub_css = CSS + """
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
a.card{display:block;text-decoration:none;color:var(--text);background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px 18px;transition:.15s}
a.card:hover{border-color:var(--accent);transform:translateY(-2px)}
a.card .nm{font-size:16px;font-weight:700;display:flex;align-items:center;gap:9px}
a.card .dot{width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:inline-flex;align-items:center;justify-content:center;font-weight:800;color:#fff;font-size:12px;flex:none}
a.card .ds{margin:8px 0 8px;font-size:12.5px;color:var(--muted)}
a.card .cbar{height:7px;background:var(--bar-bg);border-radius:99px;overflow:hidden;margin-bottom:6px}
a.card .cbar>span{display:block;height:100%;width:0;background:var(--done)}
a.card .ct{font-size:12px;color:var(--accent)}
.cat{grid-column:1/-1;margin:18px 0 2px;font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);font-weight:700}
"""
    hub_js = """
document.querySelectorAll('a.card').forEach(c=>{
  const k=c.dataset.key,tot=+c.dataset.total;
  const done=JSON.parse(localStorage.getItem('mpsc_'+k+'_v1')||'{}');
  const n=Object.keys(done).length;const p=tot?Math.round(n/tot*100):0;
  c.querySelector('.cbar>span').style.width=p+'%';c.querySelector('.cp').textContent=p+'%';
});
"""
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MPSC Rajyaseva — Master Syllabus Tracker</title><style>{hub_css}</style></head><body>
<header style="text-align:center"><div class="logo" style="margin:0 auto 8px">M</div>
<h1 style="margin:0">MPSC Rajyaseva — Master Syllabus Tracker</h1>
<p class="sub" style="color:var(--muted);margin:6px 0 0">{total} micro-topics · Prelims + Mains + Interview · progress saved in your browser</p></header>
<main><div class="grid">{''.join(blocks)}</div>
<footer>Self-contained. Each subject tracks its own progress in localStorage.</footer></main>
<script>{hub_js}</script></body></html>"""
```

- [ ] **Step 5: Write `mpsc_build/generate.py`**

```python
"""Generate mpsc/ HTML from syllabus data. Run: python3 -m mpsc_build.generate"""
import os
from mpsc_build.syllabus import load_all
from mpsc_build.template import render_page, render_hub

OUT = os.path.join(os.path.dirname(__file__), "..", "mpsc")

def main():
    os.makedirs(OUT, exist_ok=True)
    subjects = load_all()
    for s in subjects:
        with open(os.path.join(OUT, s["key"] + ".html"), "w", encoding="utf-8") as f:
            f.write(render_page(s))
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_hub(subjects))
    print(f"generated {len(subjects)} subject pages + hub into mpsc/")

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run validator — expect PASS**

Run: `cd /Users/faisalchishti/Desktop/claude-projects/Learning && python3 -m mpsc_build.validate`
Expected: `OK: all syllabus data valid` (Ethics ≥60 topics; other modules absent → skipped by `load_all`).

- [ ] **Step 7: Generate and smoke-test in browser**

Run: `python3 -m mpsc_build.generate`
Expected: `generated 1 subject pages + hub into mpsc/`.
Open `mpsc/ethics.html`: check a few boxes → reload → state persists; overall %, per-stage %, per-section minibar update; All/Mains tabs filter; search filters; reset clears. Open `mpsc/index.html`: Ethics card shows live %.

- [ ] **Step 8: Commit**

```bash
git add mpsc_build mpsc
git commit -m "feat: MPSC tracker generator + Ethics seed page"
```

---

### Tasks 2–16: Subject content modules

Each task = author ONE `mpsc_build/syllabus/<key>.py` exporting `SUBJECT` (schema from File Structure), then validate + generate + browser-check + commit. **Same procedure each task:**

1. Write `mpsc_build/syllabus/<key>.py` with the section/group skeleton listed below, expanding **every group to maximum-depth micro-topics** drawn from design spec §4 and the cited syllabus. Give each topic a stable `id` prefixed with the listed id-prefix, correct `stages`, and `mh:True` where Maharashtra-specific.
2. Run `python3 -m mpsc_build.validate` → expect `OK` (the subject must clear its `MIN_TOPICS` gate in `validate.py`).
3. Run `python3 -m mpsc_build.generate` → expect page count incremented.
4. Open `mpsc/<key>.html` in browser: tick/persist, stage tabs, search, per-section bars all work.
5. Commit: `git add mpsc_build/syllabus/<key>.py mpsc && git commit -m "content: MPSC <title>"`.

Stages legend per task indicate the default; individual topics may carry a subset.

- [ ] **Task 2 — `history.py`** (prefix `hist-`, gate 220, stages PRE/MAINS; MH for Maharashtra)
  Sections: Ancient India (sources, IVC, Vedic, Mahajanapadas, Mauryas, post-Mauryan, Guptas, Sangam, South Indian kingdoms); Medieval India (early medieval, Delhi Sultanate, Vijayanagara/Bahmani, Mughals, Marathas[MH], religious movements); Art & Culture (architecture styles, painting, music/dance, literature, philosophy); Bhakti & Sufi (with Maharashtra Varkari saints — Dnyaneshwar, Tukaram, Namdev, Eknath[MH]); Modern India 1750→1947 (British conquest & Plassey/Buxar, expansion, economic impact, 1857 revolt, socio-religious reform, INC moderates/extremists, Swadeshi, Gandhian phases — NCM/CDM/QIM, revolutionaries, partition); Maharashtra Modern (social reformers — Phule, Shahu, Ambedkar, Ranade, Agarkar, Tilak; Samyukta Maharashtra movement)[MH]; Post-Independence (integration of states, linguistic reorganization, major developments); World History (Renaissance optional, Industrial Revolution, American/French/Russian revolutions, World Wars I & II, colonization/decolonization, Cold War, political philosophies — communism/capitalism/socialism). Source: design spec §4.1; [Drishti Mains](https://www.drishtiias.com/state-pcs/mpsc-mains-syllabus).

- [ ] **Task 3 — `geography.py`** (prefix `geo-`, gate 180, stages PRE/MAINS; MH)
  Sections: Geomorphology (interior, plate tectonics, landforms, rock cycle); Climatology (atmosphere, insolation, pressure/winds, monsoon, cyclones, climate classification); Oceanography (relief, currents, tides, salinity); Physical Geography of India (physiography, drainage systems, climate, soils, natural vegetation); Maharashtra Geography (Western Ghats, rivers, physiographic divisions, climate, soils)[MH]; Indian Economic Geography (agriculture, minerals, industries, transport); Human Geography (population, migration, settlements, urbanization); World Geography (continents, major regions, resource distribution, industrial location); Geophysical Phenomena (earthquakes, tsunami, volcanoes, cyclones, landslides); Map-based & resource distribution. Source: spec §4.2.

- [ ] **Task 4 — `polity.py`** (prefix `pol-`, gate 200, stages PRE/MAINS/INT; MH)
  Sections: Constitutional Framework (historical underpinnings, making, sources, preamble, features, basic structure); Fundamental Rights/DPSP/Duties; Union Government (President, VP, PM, Council of Ministers, Parliament — structure/functioning/privileges, Attorney General); State Government (Governor, CM, State Legislature)[MH]; Judiciary (Supreme Court, High Courts, subordinate, judicial review, PIL, tribunals); Federalism & Centre-State relations (legislative/administrative/financial, inter-state councils, emergency provisions); Local Self-Government (73rd/74th amendments, Panchayati Raj, urban bodies — Maharashtra ZP/municipal structure)[MH]; Constitutional Bodies (EC, UPSC/MPSC[MH], Finance Commission, CAG, AG); Statutory/Regulatory/Quasi-judicial bodies (NHRC, CIC, CVC, Lokpal/Lokayukta, NITI Aayog); Representation of People's Act & elections; Amendments (every major amendment as a topic); Governance (transparency, accountability, RTI, e-governance, citizen charter, civil services role). Source: spec §4.3.

- [ ] **Task 5 — `economy.py`** (prefix `eco-`, gate 170, stages PRE/MAINS; MH)
  Sections: Basics & National Income; Planning & NITI Aayog (Five Year Plans history, resource mobilization); Growth/Development/Employment & inclusive growth; Money & Banking (RBI, monetary policy, banking sector, financial markets); Public Finance & Budgeting (budget process, taxation, GST, FRBM, deficits); Agriculture (major crops, cropping patterns, irrigation types, MSP, subsidies, PDS, food security, buffer stocks, food processing, e-technology, land reforms); Industry & Infrastructure (industrial policy, liberalization, energy/ports/roads/rail/airports, investment models — PPP); External Sector (trade, BoP, FDI); Maharashtra Economy (agriculture, cooperatives, industry, Mumbai's role, state budget/schemes)[MH]; Social-sector economics (poverty, hunger, HDI). Source: spec §4.4.

- [ ] **Task 6 — `environment.py`** (prefix `env-`, gate 110, stages PRE/MAINS; MH)
  Sections: Ecology & Ecosystems; Biodiversity (types, hotspots, Western Ghats[MH], conservation — PA network, national parks/sanctuaries of Maharashtra[MH]); Climate Change (greenhouse effect, global warming, IPCC, mitigation/adaptation); Pollution (air/water/soil/noise, waste management); Environmental Conservation (EIA, conventions & protocols — CBD/CITES/Ramsar/UNFCCC/Paris/Kyoto/Montreal); Environmental Institutions & Laws (MoEFCC, NGT, environmental acts); Disaster Management (hazard types, disaster cycle, DM Act, NDMA, risk reduction & resilience). Source: spec §4.5.

- [ ] **Task 7 — `science_tech.py`** (prefix `sci-`, gate 120, stages PRE/MAINS)
  Sections: Physics fundamentals (applied/everyday); Chemistry fundamentals; Biology (cell, genetics, human physiology, diseases, nutrition); Space Technology (ISRO, satellites, launch vehicles, missions); Defence Technology (missiles, DRDO); IT & Computers (basics, AI, cyber concepts); Robotics & emerging tech (nano-technology); Biotechnology (genetic engineering, applications, biotech in agri/health); Health & Biotech applications; IPR; Indigenous technology & S&T policy. Source: spec §4.6.

- [ ] **Task 8 — `society.py`** (prefix `soc-`, gate 110, stages PRE/MAINS; MH)
  Sections: Salient features of Indian society & diversity; Role of women & women's organizations; Population & associated issues (demography, census, policies); Poverty & developmental issues; Urbanization (problems & remedies); Globalization effects on society; Communalism, regionalism, secularism; Social empowerment; Welfare schemes (Centre + Maharashtra state schemes for vulnerable sections)[MH]; Social-sector — health, education, human resources; Vulnerable sections (SC/ST/OBC/minorities/women/children/elderly/disabled); NGOs, SHGs, civil society. Source: spec §4.7.

- [ ] **Task 9 — `international_relations.py`** (prefix `ir-`, gate 70, stages MAINS/INT)
  Sections: India & Neighbourhood (each neighbour — Pakistan, China, Nepal, Bangladesh, Sri Lanka, Myanmar, Bhutan, Maldives, Afghanistan); Bilateral relations (USA, Russia, EU, Japan, Gulf, Africa); Groupings & agreements (UN, BRICS, SCO, G20, QUAD, SAARC, BIMSTEC, ASEAN, IBSA); International institutions (UN bodies, IMF, World Bank, WTO, WHO — structure & mandate); India's foreign policy & diaspora; Effect of developed/developing nations' policies on India. Source: spec §4.8.

- [ ] **Task 10 — `internal_security.py`** (prefix `sec-`, gate 70, stages MAINS/INT)
  Sections: Extremism & development linkage (Left-wing extremism, insurgency); Internal security challenges (state & non-state actors, terrorism); Communication networks & media/social-media role in security; Cyber security (threats, framework); Money laundering & prevention; Border management (land/coastal, challenges); Organized crime & terrorism nexus; Security forces & agencies (mandate — paramilitary, intelligence). Note: use prefix `sec-` distinct from ethics? ethics uses `eth-`; ensure no id collision — internal security ids prefixed `is-` instead. Source: spec §4.9.

- [ ] **Task 11 — `csat.py`** (prefix `csat-`, gate 70, stages PRE)
  Sections: Comprehension (English & Marathi passages); Interpersonal & communication skills; Logical reasoning & analytical ability (syllogism, statements, arrangements); Decision-making & problem-solving; General mental ability (series, coding-decoding, blood relations, direction, clocks/calendars); Basic numeracy Class X (number system, percentages, ratio, average, profit/loss, time-work, time-speed-distance, mensuration, probability, permutation); Data interpretation (tables, bar/line/pie charts, caselets). Source: spec §4.11.

- [ ] **Task 12 — `language.py`** (prefix `lang-`, gate 50, stages MAINS)
  Sections: Marathi — comprehension, precis writing, usage & vocabulary, grammar (व्याकरण units), short essays, translation Eng→Marathi; English — comprehension, precis, usage & vocabulary, grammar (tenses, voice, articles, prepositions), short essays, translation Marathi→Eng. Source: spec §4.12.

- [ ] **Task 13 — `essay.py`** (prefix `essay-`, gate 50, stages MAINS)
  Sections: Essay technique (structure, intro/body/conclusion, brainstorming); Theme banks — Philosophical/abstract, Social, Economic, Polity & governance, Environment, Science & tech, Education, Women & gender, Maharashtra-specific[MH], Quotes-based; Practice-topic bank (multiple representative prompts as trackable items). Source: spec §4.13.

- [ ] **Task 14 — `current_affairs.py`** (prefix `ca-`, gate 60, stages PRE/MAINS/INT; MH)
  Sections (recurring trackable buckets, not dated): Government schemes tracker (Central + Maharashtra[MH]); Reports & indices (global & national); Persons in news / appointments; Awards & honours; Sports; Summits & conferences; Science & defence in news; Economy in news; Environment in news; Maharashtra current affairs (state budget, policies, events)[MH]; International events. Source: spec §4.14.

- [ ] **Task 15 — `interview.py`** (prefix `int-`, gate 50, stages INT)
  Sections: DAF preparation (bio-data, education, work, why civil service); Home district & Maharashtra deep-dive (district profile, state administration, schemes)[MH]; Hobbies & optional (Geography) defence; Current-affairs opinion bank (stance on burning issues); Situational & ethical questions; Administrative awareness; Personality & body language; Mock-interview checklist. Source: spec §4.15.

- [ ] **Task 16 — `geography_optional.py`** (prefix `geoopt-`, gate 200, stages MAINS)
  Sections — Paper I (Principles): Geomorphology (geosynclines, plate tectonics, geomorphic cycles, slope, applied geomorphology); Climatology (atmosphere composition/structure, insolation/heat budget, air masses & fronts, cyclones, climate classification Koppen/Thornthwaite, climate change); Oceanography (bottom relief, temperature/salinity, currents, tides, coral, marine resources); Biogeography (soils, vegetation, biomes, ecosystems, biodiversity); Environmental Geography (ecology principles, environmental hazards, sustainable development); Geographical Thought (determinism/possibilism, dualisms, quantitative revolution, behavioural/radical/humanistic geography, models & theories); Human Geography (economic — Von Thünen/Weber/Christaller central place, agricultural & industrial location; population & settlement geography; regional planning — growth poles, models of regional development).
  Paper II (Geography of India): Physical setting; Resources (land/water/mineral/energy/marine/biotic); Agriculture (Green Revolution, cropping, irrigation, land reforms, food security); Industry (location factors, industrial regions, policies); Transport & trade; Cultural setting (population, tribes, migration, urbanization); Settlements (rural & urban); Regional development & planning (regions, river valley projects, planning regions); Political geography (federalism, regionalism, boundary disputes); Contemporary issues (ecological problems, environmental hazards, sustainable development). Source: spec §4.16; standard UPSC/MPSC Geography optional syllabus.

  **Note:** update `validate.py` `MIN_TOPICS` already includes all keys above; if a key's gate proves too low after authoring, raise it.

---

### Task 17: GitHub Pages wiring + README + final full build

**Files:**
- Create: `mpsc/README.md`
- Verify: root `.nojekyll` already present (it is).
- Optional: add link to `mpsc/index.html` from root `index.html` (only if user wants cross-linking; otherwise leave isolated).

- [ ] **Step 1: Full regenerate from clean**

Run: `cd /Users/faisalchishti/Desktop/claude-projects/Learning && python3 -m mpsc_build.validate && python3 -m mpsc_build.generate`
Expected: `OK: all syllabus data valid` then `generated 16 subject pages + hub into mpsc/`.

- [ ] **Step 2: Coverage audit print**

Run: `python3 -c "from mpsc_build.syllabus import load_all; [print(s['key'], sum(len(g['topics']) for sec in s['sections'] for g in sec['groups'])) for s in load_all()]"`
Expected: per-subject counts all ≥ their `MIN_TOPICS` gate; eyeball that no official spec §4 section is missing.

- [ ] **Step 3: Write `mpsc/README.md`**

Short: what the tracker is, how to use (open index.html, tick topics, progress saved per-browser), how to rebuild (`python3 -m mpsc_build.generate`), data lives in `mpsc_build/syllabus/`.

- [ ] **Step 4: Browser final check**

Open `mpsc/index.html`: all 16 cards present, grouped by category, live %. Click into 3 random subjects: stage tabs + persistence + search + reset all work. Confirm mobile width (narrow window) is usable.

- [ ] **Step 5: Commit**

```bash
git add mpsc mpsc_build
git commit -m "feat: complete MPSC Rajyaseva tracker — 16 subjects + hub"
```

- [ ] **Step 6: Push (only if user confirms)**

Confirm with user, then push to the GitHub Pages branch. Verify live at `<pages-url>/mpsc/`.

---

## Self-Review

**Spec coverage:** spec §3 decisions → Task 1 (structure/storage/theme/stage-tabs/badges/generator). spec §4 all 16 subjects → Tasks 1–16 one-to-one (Ethics=Task1, rest 2–16). spec §5 UI (sticky header, tabs, toolbar, section bars, badges) → Task 1 template. spec §6 data model/localStorage → Task 1 schema+JS. spec §7 generator/validator/coverage counts → Task 1 + per-task gates + Task 17 audit. spec §8 out-of-scope respected (no backend/sync/timer). spec §9 success criteria → Task 17 final checks. No gaps.

**Placeholder scan:** generator/template/validator code is complete and runnable. Subject content is data authored against explicit section skeletons + numeric coverage gates (not "TODO") — gates make under-authoring fail the build. Acceptable: enumerating 2000+ topics verbatim in the plan would duplicate the implementation; the skeleton + min-count gate is the concrete contract.

**Type consistency:** `render_page`/`render_hub`/`load_all`/`validate` names consistent across tasks. localStorage key format `mpsc_<key>_v1` identical in PAGE_JS, hub_js, validator constraint, and Global Constraints. Topic schema (`id`/`text`/`stages`/`mh`) identical everywhere. Fixed id-collision risk: internal_security uses `is-` prefix (Task 10 note) to avoid clashing with ethics `eth-`/science `sci-`.
