"""The framework's own section 7 artefact - the base plate itself."""

from __future__ import annotations

from .common import STATE_LABEL, anchors_table, esc, questions_table, stamp


def render(catalogue, project, intake, selection, recon, ranked) -> str:
    verdict = {"stable": "Stable", "conditional": "Conditional",
               "not-yet": "Not yet a base plate"}[recon.verdict]
    out = [f"# Base Plate - {intake.title} - {stamp()} - verdict: {verdict}", "",
           f"Project `{project.id}` | Complexity {intake.tier}", "",
           "## 0. Intake", "",
           f"- **Direction / intent:** {esc(intake.title)}",
           f"- **In-scope objects & integrations:** "
           + ("; ".join(esc(o) for o in (intake.objects + intake.integrations))
              or "_not enumerated in the brief_"),
           f"- **Environment topology:** {', '.join(esc(e) for e in intake.environments)}",
           f"- **Known constraints:** "
           + ("; ".join(esc(c) for c in intake.constraints) or "_none stated_"),
           f"- **Complexity grading:** {intake.tier_rationale}",
           ""]
    if intake.unstated:
        out += ["- **Not established by the brief:**", ""]
        out += [f"  - {u}" for u in intake.unstated]
        out.append("")

    for i, dom_key in enumerate(catalogue.domain_keys(), start=1):
        dom = catalogue.domain(dom_key)
        opt = selection[dom_key]
        out += [f"## {i}. {dom.name}", "",
                f"**Position:** `{opt.id}` {opt.name}", "", opt.summary, "",
                "### Checklist result", ""]
        out += [f"- ☐ {esc(c)}" for c in opt.checklist] or ["- _none declared_"]
        out += ["", "### Further-questioning", ""]
        out += questions_table(opt.questions)
        out += ["### Volumetric anchors [ Prod | RTL | Dev-Test ]", ""]
        out += anchors_table(recon.anchors_by_domain[dom_key])
        out += ["### Cross-domain hooks", "",
                "- **Imposes:** " + (", ".join(f"`{c}`" for c in opt.provides) or "_nothing_"),
                "- **Requires:** " + (", ".join(f"`{c}`" for c in opt.requires) or "_nothing_"),
                ""]

    out += ["## 10. E2E Orchestration", "", "### Integration matrix", ""]
    codes = [catalogue.code_for(k) for k in catalogue.domain_keys()]
    lookup = {(c.row, c.col): c for c in recon.cells}
    out += ["| imposes \\ receives | " + " | ".join(codes) + " |",
            "|" + "---|" * (len(codes) + 1)]
    for r in codes:
        cells = [STATE_LABEL.get(lookup[(r, c)].state, "-") if (r, c) in lookup else "-"
                 for c in codes]
        out.append(f"| **{r}** | " + " | ".join(cells) + " |")
    out.append("")

    out += ["### Contradictions to resolve (blocking)", ""]
    out += [f"- **{c.row} vs {c.col}** ({c.severity}): {c.detail}"
            for c in recon.contradictions] or ["- _none_"]
    out += ["", "### Gaps with owners", ""]
    out += [f"- **{g.row} -> {g.col}**: {g.detail} _(owner: TBC)_"
            for g in recon.gaps] or ["- _none_"]
    out += ["", "### Unpinned critical anchors", ""]
    out += [f"- {esc(a.metric)} ({esc(a.unit)}) - unpinned in {', '.join(a.unpinned_envs())}"
            for a in recon.unpinned] or ["- _none_"]

    out += ["", "## 11. Registers", "",
            "- Decision ledger: `registers/decisions.md`",
            "- Evidence / audit ledger: `registers/evidence.md`",
            "- Risk register: `registers/risks.csv`",
            "- Question backlog: `registers/questions.csv`", "",
            "## 12. Verdict & residual backlog", "",
            f"### {verdict}", "", recon.verdict_rationale, ""]

    residual = [q for opt in selection.values() for q in opt.questions if q.blocking]
    residual += [q for q in recon.emergent_questions if q.blocking]
    if residual:
        out += [f"**Residual backlog: {len(residual)} blocking question(s).**", ""]
        out += [f"- [{q.owner_role}] {esc(q.question)}" for q in residual[:20]]
        if len(residual) > 20:
            out.append(f"- _...and {len(residual) - 20} more in `registers/questions.csv`._")
        out.append("")
    return "\n".join(out)
