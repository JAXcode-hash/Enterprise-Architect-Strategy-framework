"""One run of the framework, end to end.

    intake -> fan-out (nine validators) -> fan-in (orchestrator) -> render

Everything is written inside one project directory. Re-running the same project
picks up whatever has been pinned or overridden in `inputs/` since last time,
which is the iterate step of the lifecycle: the base plate is a living artefact
until the verdict reaches Stable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .catalogue import Catalogue
from .intake import run_intake
from .model import dumps
from .orchestrator import orchestrate
from .projects import Project
from .registers import (build_decisions, build_evidence, decisions_markdown,
                        evidence_markdown, questions_csv, risks_csv)
from .render import baseplate as r_baseplate
from .render import exec_pack as r_exec
from .render import hld as r_hld
from .render import html as r_html
from .render import lld as r_lld
from .render import options as r_options
from .render.common import esc
from .roadmap import build_roadmap, significant_effort
from .selector import rank_all


def _overview(catalogue, project, intake, selection, recon, roadmap, effort) -> str:
    cov = recon.coverage
    out = [
        f"## {esc(intake.title)}",
        "",
        f"Assessed across nine security and architecture domains from the brief in "
        f"`brief.md`. Graded **{intake.tier}** on complexity. "
        f"**Verdict: {recon.verdict.replace('-', ' ').title()}.**",
        "",
        recon.verdict_rationale,
        "",
        "### Selected positions",
        "",
        "| Domain | Position | Posture | Build | Cost | Adjusted by orchestrator |",
        "|---|---|---|---|---|---|",
    ]
    repaired = {r["domain"]: r for r in recon.repairs}
    locked = set(cov.get("locked_domains", []))
    for k in catalogue.domain_keys():
        o = selection[k]
        note = ("fixed by owner" if k in locked
                else f"yes - from `{repaired[k]['from']}`" if k in repaired else "no")
        out.append(f"| **{catalogue.code_for(k)}** {esc(catalogue.domain(k).name)} "
                   f"| `{o.id}` {esc(o.name)} | {o.posture} | {o.effort_weeks}w ({o.effort_band}) "
                   f"| {o.cost_band} | {note} |")
    out += ["", "### What to do next", ""]
    nxt = []
    if recon.contradictions:
        nxt.append(f"Resolve **{len(recon.contradictions)} contradiction(s)** between domains - "
                   "these block the base plate. See the Exec pack.")
    if recon.unpinned:
        nxt.append(f"Pin **{len(recon.unpinned)} sizing-critical anchor(s)** in "
                   "`inputs/anchors.json`, then re-run.")
    if cov["questions_blocking"]:
        nxt.append(f"Assign an owner and a date to each of the "
                   f"**{cov['questions_blocking']} blocking question(s)** in "
                   "`registers/questions.csv`.")
    if recon.gaps:
        nxt.append(f"Close **{len(recon.gaps)} gap(s)** where one domain needs something no "
                   "other domain supplies.")
    if not nxt:
        nxt.append("Nothing is blocking. Take the base plate to the architecture forum.")
    out += [f"{i}. {t}" for i, t in enumerate(nxt, start=1)]
    out += ["",
            "To change a domain's position by hand, set it in `inputs/overrides.json` and "
            "re-run - the orchestrator will not overrule a fixed domain, it routes repairs "
            "through the others and reports what it could not reconcile.", ""]
    return "\n".join(out)


def execute(project: Project, catalogue: Catalogue | None = None) -> dict:
    """Run (or re-run) an existing project. Returns a summary dict."""
    catalogue = catalogue or Catalogue()
    problems = catalogue.lint()
    if problems:
        raise RuntimeError("catalogue is not healthy:\n  " + "\n  ".join(problems))

    brief = project.read("brief.md")
    if not brief.strip():
        raise RuntimeError(f"project {project.id} has an empty brief.md")

    manifest = project.manifest
    intake = run_intake(brief, catalogue, title=manifest.get("title"))

    ranked = rank_all(catalogue, intake)
    overrides = project.read_json("inputs/overrides.json", {}) or {}
    pins = project.read_json("inputs/anchors.json", {}) or {}
    selection, recon = orchestrate(catalogue, ranked, overrides=overrides, pins=pins,
                                   mandates=intake.mandates)

    roadmap = build_roadmap(catalogue, selection, intake)
    effort = significant_effort(catalogue, selection)

    # ---- documents ------------------------------------------------------
    docs_lld = {k: r_lld.render(catalogue, k, project, intake, selection, recon, ranked)
                for k in catalogue.domain_keys()}
    docs_opt = {k: r_options.render_domain_options(catalogue, k, ranked, selection, recon, intake)
                for k in catalogue.domain_keys()}
    doc_hld = r_hld.render(catalogue, project, intake, selection, recon, roadmap)
    doc_exec = r_exec.render(catalogue, project, intake, selection, recon, roadmap, effort)
    doc_bp = r_baseplate.render(catalogue, project, intake, selection, recon, ranked)

    decisions = build_decisions(catalogue, selection, ranked, recon)
    evidence = build_evidence(catalogue, selection, recon, intake)
    risks = [r for o in selection.values() for r in o.risks] + recon.emergent_risks
    questions = [q for o in selection.values() for q in o.questions] + recon.emergent_questions

    run_json = {
        "project": manifest,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "intake": intake.to_dict(),
        "selection": {k: selection[k].to_dict() for k in catalogue.domain_keys()},
        "ranked": {k: [{"id": o.id, "name": o.name, "score": o.score, "rank": o.rank,
                        "breakdown": o.score_breakdown} for o in v]
                   for k, v in ranked.items()},
        "reconciliation": recon.to_dict(),
        "anchors": {k: [a.to_dict() for a in v] for k, v in recon.anchors_by_domain.items()},
        "rules_fired": getattr(recon, "rules_fired", []),
        "roadmap": roadmap,
        "significant_effort": effort,
        "decisions": [d.to_dict() for d in decisions],
        "evidence": [e.to_dict() for e in evidence],
    }

    overview = _overview(catalogue, project, intake, selection, recon, roadmap, effort)

    # ---- write, all inside the project ----------------------------------
    for k, body in docs_lld.items():
        project.write(f"outputs/lld/{k}.md", body)
    for k, body in docs_opt.items():
        project.write(f"options/{k}.md", body)
    project.write("outputs/hld.md", doc_hld)
    project.write("outputs/exec-pack.md", doc_exec)
    project.write("outputs/base-plate.md", doc_bp)
    project.write("outputs/overview.md", overview)
    project.write("registers/decisions.md", decisions_markdown(decisions))
    project.write("registers/evidence.md", evidence_markdown(evidence))
    project.write("registers/risks.csv", risks_csv(risks))
    project.write("registers/questions.csv", questions_csv(questions))
    project.write_json("options/ranked.json", run_json["ranked"])
    project.write("baseplate.json", dumps(run_json))

    project.write("index.html", r_html.render(
        catalogue, project, intake, selection, recon, roadmap,
        {"overview": overview, "exec": doc_exec, "hld": doc_hld, "baseplate": doc_bp,
         "lld": docs_lld, "options": docs_opt,
         "decisions": decisions_markdown(decisions),
         "evidence": evidence_markdown(evidence),
         "run": run_json},
    ))

    summary = {
        "verdict": recon.verdict,
        "tier": intake.tier,
        "selection": {k: selection[k].id for k in catalogue.domain_keys()},
        **{k: recon.coverage[k] for k in
           ("cells_contradiction", "cells_gap", "anchors_unpinned_critical",
            "questions_blocking", "risks_total", "repairs_applied")},
        "estimate_months": roadmap["range_months"],
    }
    project.record_run(recon.verdict, summary)
    return summary


def new_run(brief: str, title: str | None = None, catalogue: Catalogue | None = None,
            base=None) -> tuple[Project, dict]:
    """Create a brand-new isolated project from a brief and run it."""
    catalogue = catalogue or Catalogue()
    intake = run_intake(brief, catalogue, title=title)
    project = Project.create(intake.slug, intake.title, brief, catalogue.root, base=base)
    summary = execute(project, catalogue)
    return project, summary
