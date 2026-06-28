"""Render MPSC subject pages and hub to self-contained HTML strings."""
import json

CSS = """
:root{--bg:#0d1117;--panel:#161b22;--panel2:#1c2430;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#6db33f;--accent2:#34804f;--done:#3fb950;--bar-bg:#21262d;--pre:#388bfd;--mains:#d29922;--int:#a371f7;--mh:#3fb950;--chip:#21262d;}
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
.tabs{display:flex;gap:6px}.tab{background:var(--chip);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:8px;font-size:13px;cursor:pointer}
.tab.active{border-color:var(--accent);color:var(--accent)}
.toolbar input[type=search]{flex:1;min-width:180px;background:var(--panel2);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:8px;font-size:14px}
button{background:var(--chip);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:8px;font-size:13px;cursor:pointer}button:hover{border-color:var(--accent)}
.danger:hover{border-color:#f85149;color:#f85149}
main{max-width:1040px;margin:0 auto;padding:20px}
section.sec{margin-bottom:18px;border:1px solid var(--border);border-radius:12px;overflow:hidden;background:var(--panel)}
.sec-head{display:flex;align-items:center;gap:12px;padding:14px 18px;cursor:pointer;user-select:none;background:var(--panel2)}.sec-head:hover{background:#222b38}
.sec-head .vname{font-size:16px;font-weight:700}.sec-head .vcount{font-size:12px;color:var(--muted);min-width:48px;text-align:right}
.sec-head .minibar{margin-left:auto;width:90px;height:7px;background:var(--bar-bg);border-radius:99px;overflow:hidden}.sec-head .minibar>span{display:block;height:100%;width:0;background:var(--done)}
.sec-head .chev{transition:transform .2s;color:var(--muted)}section.sec.collapsed .chev{transform:rotate(-90deg)}section.sec.collapsed .sec-body{display:none}
.sec-body{padding:6px 10px 14px}
.grp{margin:14px 8px 4px;font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--accent);font-weight:700;border-top:1px solid var(--border);padding-top:12px}.grp:first-child{border-top:none;padding-top:4px}
ul.topics{list-style:none;margin:0;padding:0}
li.topic{display:flex;align-items:flex-start;gap:10px;padding:6px 10px;border-radius:8px}li.topic:hover{background:var(--panel2)}
li.topic input{margin-top:3px;width:16px;height:16px;accent-color:var(--done);cursor:pointer;flex:none}
li.topic label{cursor:pointer;font-size:14.5px}li.topic.done label{color:var(--muted);text-decoration:line-through}
.badge{font-size:10px;font-weight:700;padding:1px 6px;border-radius:99px;flex:none;margin-left:4px;vertical-align:middle}
.b-PRE{background:rgba(56,139,253,.18);color:var(--pre)}.b-MAINS{background:rgba(210,153,34,.18);color:var(--mains)}.b-INT{background:rgba(163,113,247,.18);color:var(--int)}
.b-MH{background:transparent;color:var(--mh);border:1px solid var(--mh)}
.hidden{display:none !important}
footer{text-align:center;color:var(--muted);font-size:12px;padding:20px}
@media(max-width:560px){.sec-head .minibar{width:60px}.stats{margin-left:0}}
"""

PAGE_JS = """
const KEY='mpsc___KEY___v1';
const DATA=__DATA__;
let done=JSON.parse(localStorage.getItem(KEY)||'{}');
let filter='ALL';
function save(){localStorage.setItem(KEY,JSON.stringify(done));}
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
    const el=document.getElementById('st-'+s);
    if(st[s][1]===0){el.style.display='none';}
    else{el.style.display='';el.textContent=({PRE:'Prelims',MAINS:'Mains',INT:'Interview'})[s]+' '+st[s][0]+'/'+st[s][1]+' ('+c+'%)';}});
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


def render_page(subject, content_ids=frozenset()):
    key = subject["key"]
    secs_html = []
    for i, sec in enumerate(subject["sections"]):
        groups_html = []
        for g in sec["groups"]:
            items = []
            for t in g["topics"]:
                st = ",".join(t["stages"])
                if t["id"] in content_ids:
                    label = (f'<label><a class="tlink" target="_blank" '
                             f'href="topics/{t["id"]}.html">{t["text"]}</a> '
                             f'<span class="pin" title="Study notes available">📖</span>{_badges(t)}</label>')
                else:
                    label = f'<label>{t["text"]}{_badges(t)}</label>'
                items.append(
                    f'<li class="topic" data-stages="{st}"><input type="checkbox" '
                    f'data-id="{t["id"]}">{label}</li>'
                )
            groups_html.append(
                f'<div class="grp">{g["name"]}</div><ul class="topics">{"".join(items)}</ul>'
            )
        secs_html.append(
            f'<section class="sec" data-sec="{i}"><div class="sec-head">'
            f'<span class="chev">&#9660;</span><span class="vname">{sec["name"]}</span>'
            f'<span class="minibar"><span></span></span><span class="vcount">0/0</span></div>'
            f'<div class="sec-body">{"".join(groups_html)}</div></section>'
        )
    data = {"sections": [
        {"idx": i, "groups": [
            {"topics": [{"id": t["id"], "stages": t["stages"]} for t in g["topics"]]}
            for g in sec["groups"]]}
        for i, sec in enumerate(subject["sections"])]}
    js = PAGE_JS.replace("__KEY__", key).replace("__DATA__", json.dumps(data))
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


TOPIC_CSS = CSS + """
.content{max-width:820px;margin:0 auto;padding:8px 20px 60px}
.content h2{font-size:20px;margin:26px 0 8px;color:var(--accent);border-bottom:1px solid var(--border);padding-bottom:5px}
.content h3{font-size:16px;margin:18px 0 6px}
.content p{margin:8px 0}
.content ul,.content ol{margin:8px 0 8px 4px;padding-left:22px}
.content li{margin:4px 0}
.content code{background:var(--bar-bg);padding:1px 5px;border-radius:5px;color:#79c0ff;font-size:13px}
.content blockquote{border-left:3px solid var(--accent);margin:10px 0;padding:4px 14px;color:var(--muted)}
.content table{border-collapse:collapse;margin:12px 0;width:100%;font-size:14px}
.content th,.content td{border:1px solid var(--border);padding:6px 10px;text-align:left}
.content th{background:var(--panel2)}
.content hr{border:none;border-top:1px solid var(--border);margin:18px 0}
.crumb{font-size:13px;color:var(--muted);text-decoration:none;border:1px solid var(--border);padding:5px 10px;border-radius:8px}
.crumb:hover{border-color:var(--accent);color:var(--text)}
.disclaimer{margin-top:30px;padding:12px 16px;background:var(--panel);border:1px solid var(--border);border-radius:10px;color:var(--muted);font-size:12.5px}
"""


def render_topic_page(subject, topic, content_html):
    badges = "".join(f'<span class="badge b-{s}">{s}</span>' for s in topic["stages"])
    if topic.get("mh"):
        badges += '<span class="badge b-MH">MH</span>'
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{topic['text']} — MPSC</title><style>{TOPIC_CSS}</style></head><body>
<header><div class="title"><a class="crumb" href="../{subject['key']}.html">← {subject['title']}</a>
<div class="logo">{subject['icon']}</div></div>
<h1 style="font-size:21px;margin:10px 0 4px">{topic['text']} {badges}</h1></header>
<main class="content">{content_html}
<div class="disclaimer">Study notes generated for MPSC preparation. Cross-check current schemes,
latest data and exact dates before the exam.</div></main></body></html>"""


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
.overall{max-width:1040px;margin:16px auto 0;padding:0 20px;display:flex;align-items:center;gap:12px}
.overall .bar{flex:1}
"""
    hub_js = """
let gtot=0,gdn=0;
document.querySelectorAll('a.card').forEach(c=>{
  const k=c.dataset.key,tot=+c.dataset.total;
  const done=JSON.parse(localStorage.getItem('mpsc_'+k+'_v1')||'{}');
  const n=Object.keys(done).length;const p=tot?Math.round(n/tot*100):0;
  c.querySelector('.cbar>span').style.width=p+'%';c.querySelector('.cp').textContent=p+'%';
  gtot+=tot;gdn+=n;
});
const gp=gtot?Math.round(gdn/gtot*100):0;
document.getElementById('gbar').style.width=gp+'%';
document.getElementById('gpct').textContent=gdn+' / '+gtot+' topics ('+gp+'%)';
"""
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MPSC Rajyaseva — Master Syllabus Tracker</title><style>{hub_css}</style></head><body>
<header style="text-align:center"><div class="logo" style="margin:0 auto 8px">M</div>
<h1 style="margin:0">MPSC Rajyaseva — Master Syllabus Tracker</h1>
<p class="sub" style="color:var(--muted);margin:6px 0 0">{total} micro-topics · Prelims + Mains + Interview · progress saved in your browser</p></header>
<div class="overall"><div class="bar"><span id="gbar"></span></div><span class="pct" id="gpct" style="min-width:auto">0%</span></div>
<main><div class="grid">{''.join(blocks)}</div>
<footer>Self-contained. Each subject tracks its own progress in your browser (localStorage).</footer></main>
<script>{hub_js}</script></body></html>"""
