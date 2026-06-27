# -*- coding: utf-8 -*-
"""Self-contained tutorial page shell (theme-matched to the checklists)."""
import json

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__ — Tutorial</title>
<style>
  :root{--bg:#0d1117;--panel:#161b22;--panel2:#1c2430;--border:#30363d;--text:#e6edf3;
        --muted:#8b949e;--accent:#6db33f;--accent2:#34804f;--done:#3fb950;--code:#79c0ff;}
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;background:var(--bg);color:var(--text);line-height:1.65;
       font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
  header{position:sticky;top:0;z-index:20;background:rgba(13,17,23,.92);backdrop-filter:blur(8px);
         border-bottom:1px solid var(--border);padding:12px 20px}
  .crumb{font-size:12.5px;color:var(--muted)}
  .crumb a{color:var(--muted);text-decoration:none}
  .crumb a:hover{color:var(--accent)}
  .htitle{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:6px}
  .htitle h1{font-size:21px;margin:0}
  .back{font-size:13px;color:var(--muted);text-decoration:none;border:1px solid var(--border);
        padding:5px 10px;border-radius:8px}
  .back:hover{border-color:var(--accent);color:var(--text)}
  .mc{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer;
      border:1px solid var(--border);padding:6px 12px;border-radius:8px}
  .mc input{width:17px;height:17px;accent-color:var(--done);cursor:pointer}
  main{max-width:880px;margin:0 auto;padding:26px 20px 60px}
  h2{font-size:20px;margin:30px 0 10px;padding-top:14px;border-top:1px solid var(--border);color:var(--accent)}
  main > h2:first-child{border-top:none;padding-top:0;margin-top:0}
  h3{font-size:16px;margin:20px 0 8px}
  p{margin:10px 0}
  ul,ol{margin:10px 0;padding-left:22px}
  li{margin:5px 0}
  a{color:var(--code)}
  code{background:var(--panel2);padding:1px 6px;border-radius:5px;font-size:13.5px;color:var(--code);
       font-family:"SF Mono", Menlo,Consolas,monospace}
  pre{position:relative;background:#0a0e14;border:1px solid var(--border);border-radius:10px;
      padding:14px 16px;overflow:auto;margin:14px 0}
  pre code{background:none;padding:0;color:#c9d1d9;display:block;line-height:1.55;font-size:13.5px}
  pre .copy{position:absolute;top:8px;right:8px;background:var(--panel2);border:1px solid var(--border);
            color:var(--muted);font-size:12px;padding:3px 9px;border-radius:6px;cursor:pointer}
  pre .copy:hover{border-color:var(--accent);color:var(--text)}
  blockquote{margin:14px 0;padding:10px 16px;border-left:3px solid var(--accent);
             background:var(--panel);border-radius:0 8px 8px 0;color:#d8e0e8}
  table{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px}
  th,td{border:1px solid var(--border);padding:7px 11px;text-align:left}
  th{background:var(--panel2)}
  svg{max-width:100%;height:auto;background:var(--panel);border:1px solid var(--border);
      border-radius:10px;padding:10px;margin:12px 0;display:block}
  .nav{display:flex;justify-content:space-between;gap:12px;margin-top:40px;
       border-top:1px solid var(--border);padding-top:18px}
  .nav a{flex:1;text-decoration:none;color:var(--text);border:1px solid var(--border);
         border-radius:10px;padding:12px 14px;font-size:13px}
  .nav a:hover{border-color:var(--accent)}
  .nav .nxt{text-align:right}
  .nav .mini{display:block;color:var(--muted);font-size:11px;margin-bottom:3px}
  .nav .spacer{flex:1}
  footer{text-align:center;color:var(--muted);font-size:12px;padding:24px}
</style>
</head>
<body>
<header>
  <div class="crumb"><a href="__BACK__">__AREA__</a> › __SECTION__</div>
  <div class="htitle">
    <h1>__TITLE__</h1>
    <a class="back" href="__BACK__">← Back to checklist</a>
    <label class="mc"><input type="checkbox" id="mc"> Mark complete</label>
  </div>
</header>
<main>
__BODY__
  <div class="nav">__PREV____NEXT__</div>
  <footer>Progress saved in your browser. Self-contained tutorial page — works offline.</footer>
</main>
<script>
const KEY = __KEY__, ID = __ID__;
const box = document.getElementById("mc");
function load(){ try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch(e){ return {}; } }
box.checked = !!load()[ID];
box.addEventListener("change", ()=>{
  const st = load();
  if (box.checked) st[ID] = 1; else delete st[ID];
  localStorage.setItem(KEY, JSON.stringify(st));
});
document.querySelectorAll("pre").forEach(pre=>{
  const code = pre.querySelector("code"); if(!code) return;
  const b = document.createElement("button");
  b.className = "copy"; b.textContent = "Copy";
  b.addEventListener("click", ()=>{
    const t = code.innerText;
    const done = ()=>{ b.textContent = "Copied"; setTimeout(()=>b.textContent="Copy",1200); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, done);
    else { const ta=document.createElement("textarea"); ta.value=t; document.body.appendChild(ta); ta.select();
           try{document.execCommand("copy");}catch(e){} ta.remove(); done(); }
  });
  pre.appendChild(b);
});
</script>
</body>
</html>
"""


def _nav(item, cls, mini):
    if not item:
        return '<span class="spacer"></span>'
    return '<a class="%s" href="%s"><span class="mini">%s</span>%s</a>' % (
        cls, item["href"], mini, item["title"])


def render(meta, body_html, prev, next):
    html = PAGE
    html = html.replace("__TITLE__", meta["title"])
    html = html.replace("__AREA__", meta["area"])
    html = html.replace("__SECTION__", meta["section"])
    html = html.replace("__BACK__", meta["back_href"])
    html = html.replace("__BODY__", body_html)
    html = html.replace("__PREV__", _nav(prev, "prv", "← Previous"))
    html = html.replace("__NEXT__", _nav(next, "nxt", "Next →"))
    html = html.replace("__KEY__", json.dumps(meta["storage_key"]))
    html = html.replace("__ID__", json.dumps("t%d" % meta["gi"]))
    return html
