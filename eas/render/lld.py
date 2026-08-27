"""Low-level design - one per domain.

The detail an engineer builds from and an assessor tests against: the position,
its checklist evaluated across all three environments, the open questions with
owners, the volumetric anchors that must be pinned, the hooks this domain
imposes on and requires from the others, and the risks the position carries.
"""

from __future__ import annotations

from .common import anchors_table, esc, header, questions_table, risks_table


def render(catalogue, domain_key, project, intake, selection, recon, ranked) -> str:
    dom = catalogue.domain(domain_key)
    opt = selection[domain_key]
    anchors = recon.anchors_by_domain[domain_key]

    provided_by: dict[str, str] = {}
    for other_key, other in selection.items():
        for cap in catalogue.expand(other.provides):
            provided_by.setdefault(cap, other_key)

    consumers: list[tuple[str, str]] = []
    for other_key, other in selection.items():
        if other_key == domain_key:
            continue
        for cap in other.requires:
            if provided_by.get(cap) == domain_key:
                consumers.append((cap, other_key))

    out = [header(project, intake, recon, f"Low-Level Design - {dom.name}")]
    out += [
        f"**Domain** `{dom.code}` &nbsp;|&nbsp; **Position** `{opt.id}` "
        f"&nbsp;|&nbsp; **Validator skill** `{dom.skill}`",
        "",
        "## 1. Position",
        "",
        f"### {opt.id} - {opt.name}",
        "",
        opt.summary,
        "",
        f"*{opt.posture.title()} posture. Estimated {opt.effort_weeks} weeks (effort band "
        f"{opt.effort_band}), cost band {opt.cost_band}. Security posture {opt.security_score}/5, "
        f"regulatory evidencing {opt.reg_score}/5, ongoing operational burden {opt.ops_burden}/5.*",
        "",
        f"Scope of this domain: {dom.scope}",
        "",
    ]

    alternatives = [o for o in ranked[domain_key] if o.id != opt.id]
    if alternatives:
        out += ["**Alternatives considered and not taken**", ""]
        for a in alternatives:
            out.append(f"- `{a.id}` {a.name} - scored {a.score:g} against {opt.score:g}. "
                       f"{a.summary}")
        out.append("")

    out += ["## 2. Checklist", "",
            "Every item is evaluated three times - once per environment. An item that only "
            "holds in Prod is an environment-parity finding, not a pass.", "",
            "| # | Verification | Prod | RTL | Dev-Test |", "|---|---|---|---|---|"]
    for i, item in enumerate(opt.checklist, start=1):
        out.append(f"| {i} | {esc(item)} | ☐ | ☐ | ☐ |")
    if not opt.checklist:
        out.append("| - | _No checklist items declared._ | | | |")
    out.append("")

    out += ["## 3. Further questioning", "",
            "Open items requiring a stakeholder answer or research before this position is "
            "safe to build on. A blocking item gates a decision, not just a document.", ""]
    out += questions_table(opt.questions)

    out += ["## 4. Volumetric anchors", "",
            "Qualitative positions are anchored on quantities. Until an anchor marked "
            "sizing-critical is pinned in every environment, this position cannot be sized, "
            "costed or defended. Pin values in `inputs/anchors.json` and re-run.", ""]
    out += anchors_table(anchors)

    unpinned_crit = [a for a in anchors if a.critical and a.is_unpinned()]
    if unpinned_crit:
        out += [f"**{len(unpinned_crit)} sizing-critical anchor(s) remain unpinned in this "
                f"domain.** These are the numbers to chase first:", ""]
        out += [f"- {esc(a.metric)} ({esc(a.unit)}) - unpinned in "
                f"{', '.join(a.unpinned_envs())}" for a in unpinned_crit]
        out.append("")

    out += ["## 5. Cross-domain hooks", "", "### Imposes on others", ""]
    if consumers:
        out += ["| Capability supplied | Consumed by | Their position |", "|---|---|---|"]
        for cap, other_key in sorted(consumers):
            out.append(f"| `{cap}` | {catalogue.code_for(other_key)} "
                       f"({catalogue.domain(other_key).name}) | `{selection[other_key].id}` |")
        out.append("")
    else:
        out += ["_No other selected position consumes a capability this domain supplies. "
                "That is worth checking: a domain nobody depends on is either genuinely "
                "self-contained or has been reasoned about in isolation._", ""]

    out += ["### Requires from others", ""]
    if opt.requires:
        out += ["| Capability needed | Supplied by | Their position | Status |",
                "|---|---|---|---|"]
        for cap in opt.requires:
            src = provided_by.get(cap)
            if src:
                out.append(f"| `{cap}` | {catalogue.code_for(src)} | `{selection[src].id}` "
                           f"| Satisfied |")
            else:
                out.append(f"| `{cap}` | - | - | **GAP - nothing supplies this** |")
        out.append("")
    else:
        out += ["_This position requires nothing from other domains._", ""]

    out += ["## 6. Risks carried by this position", ""]
    out += risks_table(opt.risks)

    if opt.controls:
        out += ["## 7. Control mapping", "",
                "Controls this position is expected to satisfy. The evidence source for each "
                "belongs in the GRC domain's control map.", "",
                ", ".join(f"`{c}`" for c in opt.controls), ""]

    if opt.lld_notes:
        out += ["## 8. Design notes", ""]
        out += [f"- {n}" for n in opt.lld_notes]
        out.append("")

    out += ["---", "",
            f"*Generated for project `{project.id}`. Scores and positions in this document are "
            f"decomposable: see `registers/evidence.md` for what was checked and "
            f"`registers/decisions.md` for why each position was taken.*", ""]
    return "\n".join(out)
