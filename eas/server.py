"""The web UI.

A stdlib HTTP server - no framework, no build step, nothing to install. Start
it with `python3 -m eas serve` and work a brief through the whole lifecycle in
a browser: paste a direction, read the options each domain offered, override a
domain's position, pin a volumetric anchor, and re-orchestrate.

Each project's page is the same self-contained `index.html` written to disk, so
what you see in the browser is exactly what you can email to someone. When
served, one extra tab is injected: a console for the actions that change the
run.
"""

from __future__ import annotations

import html
import json
import mimetypes
import re
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .catalogue import Catalogue
from .projects import Project, projects_root
from .run import execute, new_run

_CAT: Catalogue | None = None


def catalogue() -> Catalogue:
    global _CAT
    if _CAT is None:
        _CAT = Catalogue()
    return _CAT


_INDEX_CSS = """
:root{--bg:#f7f8fa;--panel:#fff;--ink:#12161c;--muted:#5b6572;--line:#e2e6ec;
--accent:#2f5fd0;--ok:#0f7b4f;--warn:#a8620a;--bad:#b3261e;--code:#eef1f6}
@media (prefers-color-scheme:dark){:root{--bg:#0f1216;--panel:#161b22;--ink:#e6eaf0;
--muted:#9aa5b3;--line:#262d36;--accent:#7ea2f5;--ok:#4fc08d;--warn:#e2a03f;
--bad:#f0776c;--code:#1c222b}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:960px;margin:0 auto;padding:34px 24px 80px}
h1{font-size:23px;letter-spacing:-.3px;margin:0 0 6px}
.lede{color:var(--muted);margin:0 0 28px;font-size:14.5px}
h2{font-size:17px;margin:34px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px}
textarea{width:100%;min-height:230px;padding:13px;border:1px solid var(--line);
border-radius:8px;background:var(--bg);color:var(--ink);font:13.5px/1.6 ui-monospace,
SFMono-Regular,Menlo,Consolas,monospace;resize:vertical}
input[type=text]{width:100%;padding:9px 11px;border:1px solid var(--line);border-radius:7px;
background:var(--bg);color:var(--ink);font:inherit;font-size:14px}
select{padding:8px 10px;border:1px solid var(--line);border-radius:7px;background:var(--bg);
color:var(--ink);font:inherit;font-size:14px}
label{display:block;font-size:12.5px;color:var(--muted);margin:12px 0 4px;font-weight:600}
button{background:var(--accent);color:#fff;border:0;border-radius:7px;padding:10px 18px;
font:inherit;font-weight:600;font-size:14px;cursor:pointer;margin-top:14px}
button:hover{filter:brightness(1.08)}
button.ghost{background:none;color:var(--accent);border:1px solid var(--line)}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line)}
th{background:var(--code);font-size:12.5px;font-weight:620}
tbody tr:last-child td{border-bottom:0}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.pill{display:inline-block;padding:2px 9px;border-radius:99px;font-size:11.5px;font-weight:650}
.pill.stable{background:rgba(15,123,79,.14);color:var(--ok)}
.pill.conditional{background:rgba(168,98,10,.16);color:var(--warn)}
.pill.notyet{background:rgba(179,38,30,.14);color:var(--bad)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:700px){.grid{grid-template-columns:1fr}}
.hint{color:var(--muted);font-size:12.5px;margin-top:8px}
.ex{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.ex button{margin:0;background:none;border:1px solid var(--line);color:var(--muted);
padding:5px 11px;border-radius:99px;font-size:12.5px;font-weight:500}
.err{background:rgba(179,38,30,.1);border:1px solid var(--bad);color:var(--bad);
padding:12px 14px;border-radius:8px;margin-bottom:20px;font-size:13.5px}
"""

_EXAMPLES = {
    "Small internal change (T1)":
        "# Internal reporting tool refresh\n\nReplace the ageing internal reporting tool with a "
        "managed service on our existing platform. Small internal user base, tight budget, "
        "reuse existing tooling, delivery by end of quarter.",
    "Regulated programme (T3)":
        "# Payments API modernisation\n\nExpose a PSD2-compliant open banking API on AWS by Q3 "
        "2026 under DORA and PCI-DSS. Cardholder data in scope. Multi-region failover required "
        "for this important business service. Real production data is currently copied into our "
        "test environment. A material third-party payment processor is involved.",
    "Estate-level (T4)":
        "# Sovereign AI platform\n\nStand up a UK-only sovereign platform hosting LLM inference "
        "over customer records for an important business service, under PRA, FCA, DORA and "
        "SS1/23. Kubernetes on two hyperscalers. Data residency is mandatory - no cross-border "
        "processing including vendor support. Multi-region active-active. Several material and "
        "critical third parties. Hard regulatory date.",
}


def _page(title: str, body: str) -> bytes:
    return (
        f"<!doctype html><html><head><meta charset=utf-8>"
        f"<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title><style>{_INDEX_CSS}</style></head>"
        f"<body><div class=wrap>{body}</div></body></html>"
    ).encode("utf-8")


def _home(error: str = "") -> bytes:
    rows = []
    for m in Project.list_all():
        v = m.get("latest_verdict", "-")
        cls = {"stable": "stable", "conditional": "conditional", "not-yet": "notyet"}.get(v, "")
        rows.append(
            f"<tr><td><a href='/p/{html.escape(m['id'])}/'>{html.escape(m.get('title', m['id']))}</a>"
            f"<div class=hint>{html.escape(m['id'])}</div></td>"
            f"<td><span class='pill {cls}'>{html.escape(v.replace('-', ' ').title())}</span></td>"
            f"<td>{html.escape(m.get('created_utc', '-')[:16].replace('T', ' '))}</td>"
            f"<td>{len(m.get('runs', []))}</td>"
            f"<td class=hint>{html.escape(m.get('catalogue_fingerprint', '-'))}</td></tr>"
        )
    table = (
        "<table><thead><tr><th>Project</th><th>Verdict</th><th>Created (UTC)</th>"
        "<th>Runs</th><th>Catalogue</th></tr></thead><tbody>"
        + "".join(rows) + "</tbody></table>"
        if rows else
        "<div class=panel><p class=hint>No projects yet. Paste a brief above to create the "
        "first one.</p></div>"
    )
    ex_buttons = "".join(
        f"<button type=button onclick=\"ex({json.dumps(v)})\">{html.escape(k)}</button>"
        for k, v in _EXAMPLES.items()
    )
    cat = catalogue().summary()
    err = f"<div class=err>{html.escape(error)}</div>" if error else ""
    return _page("Enterprise Architect Strategy", f"""
{err}
<h1>Enterprise Architect Strategy</h1>
<p class=lede>Paste a direction of any complexity. Nine cyber-security validator domains each
offer defensible options; an orchestrator interrogates those options against each other and
produces a low-level design per domain, an end-to-end high-level design and an executive pack.
Every request gets its own isolated project &mdash; no other project informs it.</p>

<div class=panel>
  <form method=post action="/new">
    <label for=title>Title (optional &mdash; taken from the first heading otherwise)</label>
    <input type=text id=title name=title placeholder="Payments API modernisation">
    <label for=brief>Brief</label>
    <textarea id=brief name=brief required placeholder="# Direction

What you are trying to do, the regulatory context, the estate, the constraints, any numbers you
already have. Three sentences works. Thirty pages works. Optional headings the intake will read:
Objects, Integrations, Environments, Constraints, Drivers."></textarea>
    <div class=ex>{ex_buttons}</div>
    <button type=submit>Assess this direction</button>
    <div class=hint>Catalogue: {cat['domains']} domains, {cat['options']} options,
      {cat['capabilities']} cross-domain capabilities, {cat['rules']} compatibility rules,
      {cat['signals']} intake signals.</div>
  </form>
</div>

<h2>Projects</h2>
{table}
<script>function ex(t){{document.getElementById('brief').value=t;
document.getElementById('brief').scrollIntoView({{block:'center'}});}}</script>
""")


def _console(project: Project) -> str:
    """The control panel injected into a served project page."""
    cat = catalogue()
    run = json.loads(project.read("baseplate.json") or "{}")
    selection = run.get("selection", {})
    overrides = project.read_json("inputs/overrides.json", {}) or {}
    pins = project.read_json("inputs/anchors.json", {}) or {}

    rows = []
    for key in cat.domain_keys():
        dom = cat.domain(key)
        current = selection.get(key, {}).get("id", "")
        opts = "".join(
            f"<option value='{o.id}'{' selected' if o.id == current else ''}>"
            f"{html.escape(o.id)} - {html.escape(o.name)} ({o.posture}, {o.effort_weeks}w)</option>"
            for o in cat.options_for(key)
        )
        locked = " (fixed)" if key in overrides else ""
        rows.append(
            f"<tr><td><strong>{dom.code}</strong> {html.escape(dom.name)}{locked}</td>"
            f"<td><form method=post action='override' style='display:flex;gap:8px'>"
            f"<input type=hidden name=domain value='{key}'>"
            f"<select name=option>{opts}</select>"
            f"<button style='margin:0' type=submit>Set &amp; re-run</button></form></td></tr>"
        )

    unpinned = [a for a in run.get("reconciliation", {}).get("unpinned", [])][:40]
    anchor_opts = "".join(
        f"<option value='{html.escape(a['metric'])}'>{html.escape(a['metric'])}"
        f" ({html.escape(a['unit'])})</option>" for a in unpinned
    )
    dom_opts = "".join(f"<option value='{k}'>{cat.code_for(k)} - {html.escape(cat.domain(k).name)}"
                       f"</option>" for k in cat.domain_keys())

    pinned_note = (f"<p class=hint>{sum(len(v) for v in pins.values() if isinstance(v, dict))} "
                   f"anchor(s) pinned so far.</p>" if pins else "")

    return f"""
<h2>Fix a domain's position</h2>
<p>The orchestrator will never overrule a domain you fix here. It routes repairs through the
other domains and reports whatever it could not reconcile.</p>
<div class="tw"><table><thead><tr><th>Domain</th><th>Position</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>

<h2>Pin a volumetric anchor</h2>
<p>Positions that depend on an unquantified anchor cannot be sized, costed or defended.
Pin the numbers as they land and re-run &mdash; that is how a run moves off
<em>Not yet a base plate</em>.</p>
{pinned_note}
<div class=panel>
<form method=post action="pin">
  <div class=grid>
    <div><label>Domain</label><select name=domain style="width:100%">{dom_opts}</select></div>
    <div><label>Anchor (sizing-critical and unpinned)</label>
      <select name=metric style="width:100%">{anchor_opts}</select></div>
  </div>
  <div class=grid>
    <div><label>Prod</label><input type=text name=prod placeholder="420 GB/day"></div>
    <div><label>RTL</label><input type=text name=rtl placeholder="40 GB/day"></div>
  </div>
  <label>Dev-Test</label><input type=text name=devtest placeholder="5 GB/day">
  <button type=submit>Pin &amp; re-run</button>
</form>
</div>

<h2>Run</h2>
<div class=panel>
<form method=post action="rerun">
  <p>Re-runs the whole framework against this project's brief, overrides and pins.
  Deterministic: the same inputs always give the same base plate.</p>
  <button type=submit>Re-run</button>
</form>
<p class=hint style="margin-top:16px">Files on disk:
<code>{html.escape(str(project.root))}</code> &mdash;
<a href="brief.md">brief.md</a> &middot;
<a href="outputs/exec-pack.md">exec-pack.md</a> &middot;
<a href="outputs/hld.md">hld.md</a> &middot;
<a href="outputs/base-plate.md">base-plate.md</a> &middot;
<a href="baseplate.json">baseplate.json</a> &middot;
<a href="registers/risks.csv">risks.csv</a> &middot;
<a href="registers/questions.csv">questions.csv</a></p>
</div>
<p style="margin-top:26px"><a href="/">&larr; All projects</a></p>
"""


def _inject_console(page: str, project: Project) -> str:
    """Add a Console tab to the project's own self-contained page."""
    page = page.replace(
        "<section id=\"data\">",
        f"<section id=\"console\"><style>{_INDEX_CSS}</style>{_console(project)}</section>"
        "<section id=\"data\">",
        1,
    )
    page = re.sub(
        r"(<nav>)(.*?)(</nav>)",
        lambda m: m.group(1) + m.group(2)
        + '<button data-t="console" onclick="tab(\'console\')">Console</button>'
        + m.group(3),
        page, count=1, flags=re.S,
    )
    return page


class Handler(BaseHTTPRequestHandler):
    server_version = "eas/1.0"

    def log_message(self, fmt, *args):  # quieter than the default
        print(f"  {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")

    # -- helpers ----------------------------------------------------------

    def _send(self, body: bytes, status: int = 200, ctype: str = "text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        return {k: v[0] for k, v in urllib.parse.parse_qs(raw, keep_blank_values=True).items()}

    def _project_from(self, path: str) -> tuple[Project, str] | None:
        m = re.match(r"^/p/([^/]+)/?(.*)$", path)
        if not m:
            return None
        try:
            return Project.open(urllib.parse.unquote(m.group(1))), urllib.parse.unquote(m.group(2))
        except FileNotFoundError:
            return None

    # -- routes -----------------------------------------------------------

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            return self._send(_home())
        if path == "/api/catalogue":
            return self._send(json.dumps(catalogue().summary(), indent=2).encode(),
                              ctype="application/json")
        found = self._project_from(path)
        if not found:
            return self._send(_page("Not found", "<h1>Not found</h1>"
                                    "<p><a href='/'>Back to projects</a></p>"), 404)
        project, rel = found
        if rel in ("", "index.html"):
            page = project.read("index.html")
            if not page:
                return self._send(_page("Not run", "<h1>This project has not been run</h1>"), 404)
            return self._send(_inject_console(page, project).encode("utf-8"))
        try:
            target = project.path(rel)
        except ValueError:
            return self._send(_page("Refused", "<h1>Refused</h1>"
                                    "<p>That path escapes the project.</p>"), 403)
        if not target.is_file():
            return self._send(_page("Not found", "<h1>Not found</h1>"), 404)
        ctype = mimetypes.guess_type(target.name)[0] or "text/plain"
        if ctype.startswith("text/") or ctype in ("application/json",):
            ctype += "; charset=utf-8"
        if target.suffix in (".md", ".csv", ".json"):
            ctype = "text/plain; charset=utf-8"
        return self._send(target.read_bytes(), ctype=ctype)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        try:
            if path == "/new":
                form = self._form()
                brief = form.get("brief", "").strip()
                if not brief:
                    return self._send(_home("The brief was empty."), 400)
                project, _ = new_run(brief, title=(form.get("title") or "").strip() or None,
                                     catalogue=catalogue())
                return self._redirect(f"/p/{urllib.parse.quote(project.id)}/")

            found = self._project_from(path)
            if not found:
                return self._send(_page("Not found", "<h1>Not found</h1>"), 404)
            project, action = found
            form = self._form()

            if action == "override":
                domain, option = form.get("domain", ""), form.get("option", "")
                cat = catalogue()
                if domain in cat.domain_keys() and option in [
                        o.id for o in cat.options_for(domain)]:
                    ov = project.read_json("inputs/overrides.json", {}) or {}
                    ov[domain] = option
                    project.write_json("inputs/overrides.json", ov)
                    execute(project, cat)
            elif action == "pin":
                metric = form.get("metric", "").strip()
                domain = form.get("domain", "").strip()
                if metric and domain:
                    pins = project.read_json("inputs/anchors.json", {}) or {}
                    pins.setdefault(domain, {})[metric] = {
                        "prod": form.get("prod", "").strip() or "UNPINNED",
                        "rtl": form.get("rtl", "").strip() or "UNPINNED",
                        "devtest": form.get("devtest", "").strip() or "UNPINNED",
                    }
                    project.write_json("inputs/anchors.json", pins)
                    execute(project, catalogue())
            elif action == "rerun":
                execute(project, catalogue())
            return self._redirect(f"/p/{urllib.parse.quote(project.id)}/")
        except Exception:
            traceback.print_exc()
            return self._send(_page("Error", "<h1>Something went wrong</h1>"
                                    "<p>The traceback is on the server console.</p>"
                                    "<p><a href='/'>Back</a></p>"), 500)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    catalogue()  # fail fast on a broken catalogue
    projects_root().mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Enterprise Architect Strategy - http://{host}:{port}")
    print(f"Projects: {projects_root()}")
    print("Ctrl-C to stop.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
