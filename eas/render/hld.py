"""High-level design - the end-to-end view.

Scope boundaries, the e2e flow, connectivity and trust boundaries, a summary of
each domain's low-level position, and the reconciliation result across all of
them. This is the document an architecture forum reviews.
"""

from __future__ import annotations

from .common import STATE_LABEL, esc, header
from .diagram import e2e_flow


def render(catalogue, project, intake, selection, recon, roadmap) -> str:
    caps: set[str] = set()
    for opt in selection.values():
        caps |= catalogue.expand(opt.provides)

    out = [header(project, intake, recon, "High-Level Design")]

    out += ["## 1. Direction and intake", "",
            f"**{intake.title}**", "",
            f"Graded **{intake.tier}** on complexity. {intake.tier_rationale}", ""]

    if intake.drivers:
        out += ["**Drivers stated in the brief**", ""] + [f"- {esc(d)}" for d in intake.drivers] + [""]

    detected = [(k, s) for k, s in sorted(intake.signals.items()) if not s.inferred]
    if detected:
        out += ["**What the brief established**", "",
                "| Signal | Confidence | Evidence from the brief |", "|---|---|---|"]
        for k, s in detected:
            out.append(f"| {catalogue.signals_def['signals'][k]['label']} | {s.confidence} "
                       f"| {esc(s.evidence)} |")
        out.append("")

    if intake.unstated:
        out += ["**What the brief did not establish**", "",
                "A silence is not an absence of requirement. Each of these is an "
                "unasked question carried into the design as an assumption:", ""]
        out += [f"- {u}" for u in intake.unstated]
        out.append("")

    out += ["## 2. Scope boundaries", "", "### In scope", ""]
    if intake.objects:
        out += [f"- {esc(o)}" for o in intake.objects]
    else:
        out += ["- The brief did not enumerate in-scope objects. The positions below apply to "
                "the whole of the direction as described, which is a broader scope than may "
                "have been intended - confirm before build."]
    out.append("")

    out += ["### Environments", "",
            "Every position is asserted across all three. Where one differs, that difference "
            "is a decision on record, not an accident.", ""]
    out += [f"- {esc(e)}" for e in intake.environments] + [""]

    out += ["### Explicitly not covered by this base plate", "",
            "- Anything the brief did not describe and this framework did not infer. The "
            "unstated list in section 1 is the honest boundary of what has been assessed.",
            "- Commercial terms, org design and funding approval.",
            "- Detailed engineering design below the domain LLDs in `outputs/lld/`.", ""]

    if intake.constraints:
        out += ["### Stated constraints", ""] + [f"- {esc(c)}" for c in intake.constraints] + [""]

    out += ["## 3. End-to-end flow", "",
            "Generated from the selected positions - each component appears because a domain "
            "chose it. Trust boundaries are drawn explicitly; an edge with no marked boundary "
            "is an unexamined assumption.", "",
            "```mermaid", e2e_flow(catalogue, selection, intake), "```", ""]

    out += ["## 4. Connectivity and trust boundaries", "",
            "| Boundary | Crossed by | Authorised how | Observed how |", "|---|---|---|---|"]
    net = selection["network-security"]
    iam = selection["identity-access"]
    integ = selection["integration"]
    sec = selection["secops"]
    edge_authz = ("Verified at the edge on every crossing"
                  if "integration.edge.authz" in caps
                  else "**Inferred from network location - not verified at the edge**")
    egress_ctrl = ("L7 inspected with FQDN allow-listing"
                   if "network.egress.inspected" in caps
                   else "Shared egress, IP-range allow-listing, uninspected")
    dlp = "with egress DLP" if "data.dlp.egress" in caps else "**with no data-loss control**"
    out += [
        f"| Public edge | External users and partners | "
        f"{'WAF and managed edge protection' if 'network.ingress.waf' in caps else '**No WAF selected**'} "
        f"| {'Type 1 sources delivered' if 'secops.log.type1' in caps else 'Not centrally observed'} |",
        f"| Application plane | Service-to-service calls | {edge_authz} ({integ.id}) "
        f"| {'Per-edge logging' if 'integration.per-edge-logging' in caps else '**Not logged per edge**'} |",
        f"| East-west | Peer services | "
        f"{'Default-deny per service pair' if 'network.segmentation.micro' in caps else 'Zone-level policy only'} "
        f"| {'Flow logs' if 'network.flowlogs' in caps else '**No flow logs**'} |",
        f"| Data plane | Application to store | "
        f"{'Customer-managed keys' if 'data.key.customer-managed' in caps else '**Provider-managed keys**'} "
        f"| {'Data access audited' if 'data.access.audited' in caps else '**Data access not audited**'} |",
        f"| Egress | Outbound to external destinations | {egress_ctrl} {dlp} "
        f"| {'Egress detection' if 'secops.detection.egress' in caps else '**No egress detection**'} |",
        f"| Control plane | Workloads to IdP / PDP / KMS | "
        f"{'Federated workload identity' if 'identity.workload.federated' in caps else 'Platform-native credentials'} ({iam.id}) "
        f"| {'Type 1 sources delivered' if 'secops.log.type1' in caps else 'Standards-ready, awaiting engagement' if 'secops.ingestion.compatible' in caps else '**Neither connected nor ingestion-compatible**'} ({sec.id}) |",
        "",
    ]
    out += [f"Network position: `{net.id}` - {net.name}.", ""]

    out += ["## 5. Domain positions", "",
            "One paragraph per domain. The full detail is in "
            "`outputs/lld/<domain>.md`; the options each domain offered are in "
            "`options/<domain>.md`.", ""]
    for dom_key in catalogue.domain_keys():
        dom = catalogue.domain(dom_key)
        opt = selection[dom_key]
        anchors = recon.anchors_by_domain[dom_key]
        unp = [a for a in anchors if a.critical and a.is_unpinned()]
        blocking = [q for q in opt.questions if q.blocking]
        heavy = [r for r in opt.risks if r.severity in ("H", "C")]
        out += [
            f"### {dom.code} - {dom.name}",
            "",
            f"**`{opt.id}` {opt.name}** ({opt.posture}, {opt.effort_weeks}w, cost band {opt.cost_band})",
            "",
            opt.summary,
            "",
        ]
        if opt.hld_notes:
            out += [f"*{n}*" for n in opt.hld_notes] + [""]
        out += [
            f"Carries {len(heavy)} high or critical risk(s), {len(blocking)} blocking "
            f"question(s), and {len(unp)} unpinned sizing-critical anchor(s) of "
            f"{len(anchors)} declared.",
            "",
        ]

    out += ["## 6. End-to-end reconciliation", "",
            "The orchestrator interrogates every domain's position against every other. "
            "Rows impose; columns receive.", ""]
    keys = catalogue.domain_keys()
    codes = [catalogue.code_for(k) for k in keys]
    lookup = {(c.row, c.col): c for c in recon.cells}
    out += ["| imposes \\ receives | " + " | ".join(codes) + " |",
            "|" + "---|" * (len(codes) + 1)]
    for r in codes:
        row = [f"| **{r}** "]
        for col in codes:
            cell = lookup.get((r, col))
            row.append(f"| {STATE_LABEL.get(cell.state, '-') if cell else '-'} ")
        out.append("".join(row) + "|")
    out.append("")
    cov = recon.coverage
    out += [f"{cov['cells_satisfied']} satisfied dependency cell(s), "
            f"{cov['cells_contradiction']} contradiction(s), {cov['cells_gap']} gap(s).", ""]

    if recon.repairs:
        out += ["### Where the orchestrator overruled a domain", "",
                "A domain's highest-scoring option is not automatically the right one for the "
                "estate. These substitutions were made to reconcile the whole:", "",
                "| Domain | Domain's choice | Reconciled choice | Fit cost |", "|---|---|---|---|"]
        for rp in recon.repairs:
            out.append(f"| {catalogue.code_for(rp['domain'])} | `{rp['from']}` {esc(rp['from_name'])} "
                       f"| `{rp['to']}` {esc(rp['to_name'])} | {abs(rp['fit_loss']):g} |")
        out.append("")

    if recon.contradictions:
        out += ["### Contradictions - blocking", "",
                "Two domains assert incompatible positions. These must be resolved by "
                "decision before the base plate is stable.", ""]
        for c in recon.contradictions:
            out += [f"**{c.row} vs {c.col}** ({c.severity}) - {c.detail}", ""]

    if recon.gaps:
        out += ["### Gaps - a required hook with no owning position", ""]
        for g in recon.gaps:
            out += [f"- **{g.row} -> {g.col}**: {g.detail}"]
        out.append("")

    if recon.emergent_risks:
        out += ["### Risks that exist only in combination", "",
                "No single domain owns these; they arise from two positions read together.", ""]
        for r in recon.emergent_risks:
            out += [f"- **{r.severity} / {r.category}** ({r.source}) - {r.statement} "
                    f"*Mitigation:* {r.mitigation}"]
        out.append("")

    if recon.unpinned:
        out += ["## 7. Unpinned sizing-critical anchors", "",
                "Positions depending on these cannot be sized or costed. This is the single "
                "most useful list to take away from this document.", "",
                "| Anchor | Unit | Unpinned in |", "|---|---|---|"]
        for a in recon.unpinned:
            out.append(f"| {esc(a.metric)} | {esc(a.unit)} | {', '.join(a.unpinned_envs())} |")
        out.append("")

    out += ["## 8. Delivery shape", "",
            f"Rough order of magnitude **{roadmap['range_weeks'][0]}-{roadmap['range_weeks'][1]} "
            f"weeks** ({roadmap['range_months'][0]}-{roadmap['range_months'][1]} months) at "
            f"{roadmap['uncertainty_band']} on a {roadmap['total_weeks']}-week central estimate.", "",
            roadmap["basis"], "",
            "| Wave | Domains | Starts (wk) | Ends (wk) |", "|---|---|---|---|"]
    for p in roadmap["phases"]:
        doms = ", ".join(catalogue.code_for(d) for d in p["domains"]) or "-"
        out.append(f"| {esc(p['name'])} | {doms} | {p['starts_week']:g} | {p['ends_week']:g} |")
    out += ["", "Critical path: "
            + " -> ".join(f"{x['domain']} (`{x['option']}`, {x['weeks']}w)"
                          for x in roadmap["critical_path"]), ""]

    out += ["## 9. Verdict", "",
            f"### {recon.verdict.replace('-', ' ').title()}", "",
            recon.verdict_rationale, "",
            "A base plate is a living artefact. It stays open until the verdict reaches "
            "Stable; pin anchors in `inputs/anchors.json`, record answers, and re-run.", ""]
    return "\n".join(out)
