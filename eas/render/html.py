"""Self-contained project dashboard.

One HTML file per project, holding every document the run produced. No external
requests of any kind - the framework has to work behind a corporate proxy, on
an air-gapped laptop, or attached to an email.
"""

from __future__ import annotations

import html as _html
import json

from .md2html import render as md

_CSS = """
:root{--bg:#f7f8fa;--panel:#fff;--ink:#12161c;--muted:#5b6572;--line:#e2e6ec;
--accent:#2f5fd0;--ok:#0f7b4f;--warn:#a8620a;--bad:#b3261e;--code:#eef1f6;}
@media (prefers-color-scheme:dark){:root{--bg:#0f1216;--panel:#161b22;--ink:#e6eaf0;
--muted:#9aa5b3;--line:#262d36;--accent:#7ea2f5;--ok:#4fc08d;--warn:#e2a03f;
--bad:#f0776c;--code:#1c222b;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{background:var(--panel);border-bottom:1px solid var(--line);padding:18px 24px;
position:sticky;top:0;z-index:20}
header h1{margin:0 0 4px;font-size:19px;letter-spacing:-.2px}
header .meta{color:var(--muted);font-size:13px}
.badge{display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;
font-weight:600;margin-left:8px;vertical-align:1px}
.badge.stable{background:rgba(15,123,79,.14);color:var(--ok)}
.badge.conditional{background:rgba(168,98,10,.16);color:var(--warn)}
.badge.notyet{background:rgba(179,38,30,.14);color:var(--bad)}
nav{background:var(--panel);border-bottom:1px solid var(--line);padding:0 16px;
display:flex;gap:2px;overflow-x:auto;position:sticky;top:70px;z-index:19}
nav button{background:none;border:0;border-bottom:2px solid transparent;color:var(--muted);
padding:11px 14px;font:inherit;font-size:13.5px;cursor:pointer;white-space:nowrap}
nav button:hover{color:var(--ink)}
nav button.on{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
main{max-width:1120px;margin:0 auto;padding:26px 24px 80px}
section{display:none}section.on{display:block}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:12px;
margin:0 0 26px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.card .n{font-size:26px;font-weight:650;letter-spacing:-.5px}
.card .l{color:var(--muted);font-size:12.5px;margin-top:2px}
.card.bad .n{color:var(--bad)}.card.warn .n{color:var(--warn)}.card.ok .n{color:var(--ok)}
h1,h2,h3,h4{line-height:1.3;letter-spacing:-.2px}
h2{margin-top:34px;padding-bottom:6px;border-bottom:1px solid var(--line);font-size:20px}
h3{margin-top:26px;font-size:16.5px}h4{font-size:14.5px;margin-top:20px}
p{margin:.7em 0}
code{background:var(--code);padding:1.5px 5px;border-radius:4px;font-size:12.5px;
font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
pre{background:var(--code);padding:14px;border-radius:8px;overflow-x:auto;
border:1px solid var(--line)}
pre code{background:none;padding:0;font-size:12.5px;line-height:1.5}
blockquote{margin:14px 0;padding:10px 16px;border-left:3px solid var(--accent);
background:var(--panel);color:var(--muted);border-radius:0 6px 6px 0}
.tw{overflow-x:auto;margin:14px 0;border:1px solid var(--line);border-radius:8px;
background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);
vertical-align:top}
th{background:var(--code);font-weight:620;white-space:nowrap;font-size:12.5px;
position:sticky;top:0}
tbody tr:last-child td{border-bottom:0}
td:has(strong:only-child){white-space:nowrap}
ul,ol{padding-left:22px}li{margin:.3em 0}
hr{border:0;border-top:1px solid var(--line);margin:26px 0}
.sub{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 20px}
.sub button{background:var(--panel);border:1px solid var(--line);color:var(--muted);
padding:6px 12px;border-radius:99px;font:inherit;font-size:12.5px;cursor:pointer}
.sub button.on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.doc{display:none}.doc.on{display:block}
footer{color:var(--muted);font-size:12.5px;text-align:center;padding:30px 20px}
"""

_JS = """
function tab(id){
  document.querySelectorAll('main section').forEach(s=>s.classList.toggle('on',s.id===id));
  document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.t===id));
  try{localStorage.setItem('eas-tab',id)}catch(e){}
  window.scrollTo(0,0);
}
function sub(group,id){
  document.querySelectorAll('#'+group+' .doc').forEach(d=>d.classList.toggle('on',d.id===id));
  document.querySelectorAll('#'+group+' .sub button').forEach(
    b=>b.classList.toggle('on',b.dataset.d===id));
}
(function(){
  let t='overview';
  try{t=localStorage.getItem('eas-tab')||'overview'}catch(e){}
  if(!document.getElementById(t))t='overview';
  tab(t);
})();
"""


def _card(n, label, cls="") -> str:
    return (f'<div class="card {cls}"><div class="n">{_html.escape(str(n))}</div>'
            f'<div class="l">{_html.escape(label)}</div></div>')


def render(catalogue, project, intake, selection, recon, roadmap, docs: dict[str, str]) -> str:
    cov = recon.coverage
    vclass = {"stable": "stable", "conditional": "conditional", "not-yet": "notyet"}[recon.verdict]
    vlabel = recon.verdict.replace("-", " ").title()

    cards = "".join([
        _card(intake.tier, "Complexity tier"),
        _card(cov["cells_contradiction"], "Contradictions",
              "bad" if cov["cells_contradiction"] else "ok"),
        _card(cov["cells_gap"], "Gaps", "warn" if cov["cells_gap"] else "ok"),
        _card(f"{cov['anchors_pinned']}/{cov['anchors_total']}", "Anchors pinned",
              "warn" if cov["anchors_unpinned_critical"] else "ok"),
        _card(cov["questions_blocking"], "Blocking questions", "warn"),
        _card(cov["risks_total"], "Risks recorded"),
        _card(cov["repairs_applied"], "Orchestrator repairs"),
        _card(f"{roadmap['range_months'][0]}-{roadmap['range_months'][1]}", "Months (est.)"),
    ])

    tabs = [("overview", "Overview"), ("exec", "Exec pack"), ("hld", "HLD"),
            ("lld", "LLD by domain"), ("options", "Options"),
            ("baseplate", "Base plate"), ("registers", "Registers"), ("data", "Run data")]
    nav = "".join(f'<button data-t="{k}" onclick="tab(\'{k}\')">{_html.escape(v)}</button>'
                  for k, v in tabs)

    def doc_group(group_id: str, items: list[tuple[str, str, str]]) -> str:
        """items: (doc_id, button label, markdown)"""
        btns = "".join(
            f'<button data-d="{d}" class="{"on" if i == 0 else ""}" '
            f'onclick="sub(\'{group_id}\',\'{d}\')">{_html.escape(label)}</button>'
            for i, (d, label, _) in enumerate(items))
        bodies = "".join(
            f'<div class="doc {"on" if i == 0 else ""}" id="{d}">{md(body)}</div>'
            for i, (d, _l, body) in enumerate(items))
        return f'<div class="sub">{btns}</div>{bodies}'

    lld_items = [(f"lld-{k}", catalogue.code_for(k), docs["lld"][k])
                 for k in catalogue.domain_keys()]
    opt_items = [(f"opt-{k}", catalogue.code_for(k), docs["options"][k])
                 for k in catalogue.domain_keys()]
    reg_items = [
        ("reg-dec", "Decision ledger", docs["decisions"]),
        ("reg-evi", "Evidence ledger", docs["evidence"]),
    ]

    run_json = json.dumps(docs["run"], indent=2)[:400000]

    overview = md(docs["overview"])

    return f"""<title>{_html.escape(intake.title)} - base plate</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{_CSS}</style>
<header>
  <h1>{_html.escape(intake.title)}<span class="badge {vclass}">{vlabel}</span></h1>
  <div class="meta">Project <code>{_html.escape(project.id)}</code> &middot;
    complexity {intake.tier} &middot; {len(selection)} domains reconciled &middot;
    isolated run &mdash; no other project informed this assessment</div>
</header>
<nav>{nav}</nav>
<main>
  <section id="overview"><div class="cards">{cards}</div>{overview}</section>
  <section id="exec">{md(docs['exec'])}</section>
  <section id="hld">{md(docs['hld'])}</section>
  <section id="lld">{doc_group('lld', lld_items)}</section>
  <section id="options">{doc_group('options', opt_items)}</section>
  <section id="baseplate">{md(docs['baseplate'])}</section>
  <section id="registers">{doc_group('registers', reg_items)}</section>
  <section id="data"><h2>Machine-readable run</h2>
    <p>The complete reconciled base plate as JSON, exactly as written to
    <code>baseplate.json</code>.</p>
    <pre><code>{_html.escape(run_json)}</code></pre></section>
</main>
<footer>Enterprise Architect Strategy framework &middot; generated from
<code>brief.md</code> &middot; this file is self-contained and makes no network
requests</footer>
<script>{_JS}</script>
"""
