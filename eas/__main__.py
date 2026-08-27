"""Command line entry point.

    python3 -m eas new  --brief briefs/example.md      create an isolated project and run it
    python3 -m eas new  --text "..."                    same, from an inline brief
    python3 -m eas run  <project-id>                    re-run after pinning anchors or overriding
    python3 -m eas list                                 list projects
    python3 -m eas show <project-id>                    print a project's summary
    python3 -m eas set  <project-id> <domain> <option>  fix a domain to an option, then re-run
    python3 -m eas pin  <project-id> <domain> "<metric>" <prod> <rtl> <devtest>
    python3 -m eas lint                                 check the catalogue is coherent
    python3 -m eas catalogue                            print the catalogue summary
    python3 -m eas serve [--port 8000]                  the web UI
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalogue import Catalogue
from .projects import Project, projects_root
from .run import execute, new_run

GREEN, YELLOW, RED, DIM, BOLD, OFF = (
    "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
)
_VCOL = {"stable": GREEN, "conditional": YELLOW, "not-yet": RED}


def _no_colour() -> bool:
    return not sys.stdout.isatty()


def c(text: str, colour: str) -> str:
    return text if _no_colour() else f"{colour}{text}{OFF}"


def _print_summary(project: Project, summary: dict) -> None:
    v = summary["verdict"]
    print()
    print(c(f"  {project.id}", BOLD))
    print(f"  Verdict           {c(v.replace('-', ' ').title(), _VCOL.get(v, ''))}")
    print(f"  Complexity        {summary['tier']}")
    print(f"  Contradictions    {summary['cells_contradiction']}")
    print(f"  Gaps              {summary['cells_gap']}")
    print(f"  Unpinned anchors  {summary['anchors_unpinned_critical']} (sizing-critical)")
    print(f"  Blocking Qs       {summary['questions_blocking']}")
    print(f"  Risks recorded    {summary['risks_total']}")
    print(f"  Repairs applied   {summary['repairs_applied']}")
    print(f"  Estimate          {summary['estimate_months'][0]}-{summary['estimate_months'][1]} months")
    print()
    print(c("  Positions", BOLD))
    for dom, opt in summary["selection"].items():
        print(f"    {dom:<18} {opt}")
    print()
    print(c("  Outputs", BOLD))
    for rel in ("index.html", "outputs/exec-pack.md", "outputs/hld.md",
                "outputs/lld/", "outputs/base-plate.md", "registers/", "baseplate.json"):
        print(f"    {project.root / rel}")
    print()


def cmd_new(args) -> int:
    if args.brief:
        text = Path(args.brief).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()
    if not text.strip():
        print("error: empty brief", file=sys.stderr)
        return 2
    project, summary = new_run(text, title=args.title)
    _print_summary(project, summary)
    return 0


def cmd_run(args) -> int:
    project = Project.open(args.project)
    summary = execute(project)
    _print_summary(project, summary)
    return 0


def cmd_list(_args) -> int:
    rows = Project.list_all()
    if not rows:
        print(f"no projects yet under {projects_root()}")
        return 0
    print(f"{'PROJECT':<44} {'CREATED':<21} {'VERDICT':<12} RUNS")
    for m in rows:
        v = m.get("latest_verdict", "-")
        print(f"{m['id']:<44} {m.get('created_utc', '-'):<21} "
              f"{c(v.replace('-', ' '), _VCOL.get(v, '')):<12} {len(m.get('runs', []))}")
    return 0


def cmd_show(args) -> int:
    project = Project.open(args.project)
    m = project.manifest
    print(json.dumps({k: v for k, v in m.items() if k != "runs"}, indent=2))
    runs = m.get("runs", [])
    if runs:
        print("\nlatest run:")
        print(json.dumps(runs[-1], indent=2))
    return 0


def cmd_set(args) -> int:
    catalogue = Catalogue()
    if args.domain not in catalogue.domain_keys():
        print(f"error: unknown domain '{args.domain}'. Valid: "
              + ", ".join(catalogue.domain_keys()), file=sys.stderr)
        return 2
    valid = [o.id for o in catalogue.options_for(args.domain)]
    if args.option not in valid:
        print(f"error: unknown option '{args.option}' for {args.domain}. Valid: "
              + ", ".join(valid), file=sys.stderr)
        return 2
    project = Project.open(args.project)
    overrides = project.read_json("inputs/overrides.json", {}) or {}
    overrides[args.domain] = args.option
    project.write_json("inputs/overrides.json", overrides)
    print(f"fixed {args.domain} to {args.option}; re-running")
    summary = execute(project, catalogue)
    _print_summary(project, summary)
    return 0


def cmd_pin(args) -> int:
    project = Project.open(args.project)
    pins = project.read_json("inputs/anchors.json", {}) or {}
    pins.setdefault(args.domain, {})[args.metric] = {
        "prod": args.prod, "rtl": args.rtl, "devtest": args.devtest,
    }
    project.write_json("inputs/anchors.json", pins)
    print(f"pinned '{args.metric}' in {args.domain}; re-running")
    summary = execute(project)
    _print_summary(project, summary)
    return 0


def cmd_lint(_args) -> int:
    problems = Catalogue().lint()
    if problems:
        print(c(f"{len(problems)} catalogue problem(s):", RED))
        for p in problems:
            print(f"  - {p}")
        return 1
    print(c("catalogue is coherent", GREEN))
    return 0


def cmd_catalogue(_args) -> int:
    cat = Catalogue()
    print(json.dumps(cat.summary(), indent=2))
    print()
    for dom in sorted(cat.domains, key=lambda d: d.order):
        print(c(f"{dom.code}  {dom.name}  [{dom.skill}]", BOLD))
        for o in cat.options_for(dom.key):
            print(f"   {o.id:<9} {o.posture:<10} {o.effort_weeks:>3}w  {o.name}")
        print()
    return 0


def cmd_serve(args) -> int:
    from .server import serve
    serve(host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="eas",
        description="Enterprise Architect Strategy framework - base plate a direction.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="create an isolated project from a brief and run it")
    n.add_argument("--brief", help="path to a brief file")
    n.add_argument("--text", help="inline brief text")
    n.add_argument("--title", help="override the project title")
    n.set_defaults(func=cmd_new)

    r = sub.add_parser("run", help="re-run an existing project")
    r.add_argument("project")
    r.set_defaults(func=cmd_run)

    sub.add_parser("list", help="list projects").set_defaults(func=cmd_list)

    s = sub.add_parser("show", help="print a project's manifest and latest run")
    s.add_argument("project")
    s.set_defaults(func=cmd_show)

    st = sub.add_parser("set", help="fix a domain to a specific option, then re-run")
    st.add_argument("project")
    st.add_argument("domain")
    st.add_argument("option")
    st.set_defaults(func=cmd_set)

    pn = sub.add_parser("pin", help="pin a volumetric anchor per environment, then re-run")
    pn.add_argument("project")
    pn.add_argument("domain")
    pn.add_argument("metric")
    pn.add_argument("prod")
    pn.add_argument("rtl")
    pn.add_argument("devtest")
    pn.set_defaults(func=cmd_pin)

    sub.add_parser("lint", help="check the catalogue is coherent").set_defaults(func=cmd_lint)
    sub.add_parser("catalogue", help="print the option catalogue").set_defaults(func=cmd_catalogue)

    sv = sub.add_parser("serve", help="run the web UI")
    sv.add_argument("--port", type=int, default=8000)
    sv.add_argument("--host", default="127.0.0.1")
    sv.set_defaults(func=cmd_serve)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
