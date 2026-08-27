"""Executive pack.

What the initiative buys and why, where the delivery weight sits, roughly how
long it takes, and what could go wrong - with the security exposures filtered
up out of the low-level designs rather than left buried in them.

Written for a reader who will not open the HLD.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..model import Risk
from .common import CAT_LABEL, SEV_LABEL, esc, header

_BENEFITS_CACHE: dict | None = None


def _benefits(catalogue) -> dict:
    global _BENEFITS_CACHE
    if _BENEFITS_CACHE is None:
        p = Path(catalogue.root) / "benefits.json"
        _BENEFITS_CACHE = json.loads(p.read_text(encoding="utf-8"))["benefits"]
    return _BENEFITS_CACHE


def all_risks(selection, recon) -> list[Risk]:
    out: list[Risk] = []
    for opt in selection.values():
        out.extend(opt.risks)
    out.extend(recon.emergent_risks)
    return out


def render(catalogue, project, intake, selection, recon, roadmap, effort) -> str:
    caps: set[str] = set()
    for opt in selection.values():
        caps |= catalogue.expand(opt.provides)
    bmap = _benefits(catalogue)
    risks = all_risks(selection, recon)

    out = [header(project, intake, recon, "Executive Pack")]

    # ---------------------------------------------------------------- position
    cov = recon.coverage
    heavy = [r for r in risks if r.severity in ("H", "C")]
    out += [
        "## The position in one paragraph",
        "",
        f"**{intake.title}** has been assessed across nine security and architecture domains "
        f"and graded **{intake.tier}** on complexity "
        f"({len([s for s in intake.signals.values() if not s.inferred])} signals detected in the "
        f"brief). Nine positions were selected from {sum(len(catalogue.options_for(k)) for k in catalogue.domain_keys())} "
        f"candidate options and reconciled end to end. The reconciliation found "
        f"**{cov['cells_contradiction']} contradiction(s)** between domains and "
        f"**{cov['cells_gap']} gap(s)** where one domain needs something no other domain "
        f"provides. Delivery is a rough **{roadmap['range_months'][0]}-{roadmap['range_months'][1]} "
        f"months** at {roadmap['uncertainty_band']}. "
        f"**{len(heavy)} high or critical risks** are carried, of which "
        f"{cov['risks_emergent']} exist only because of how the domain positions combine. "
        f"{cov['anchors_unpinned_critical']} of {cov['anchors_total']} volumetric anchors that "
        f"drive sizing are still unpinned.",
        "",
        f"### Verdict: {recon.verdict.replace('-', ' ').title()}",
        "",
        recon.verdict_rationale,
        "",
    ]

    # ---------------------------------------------------------------- benefits
    out += ["## What this initiative delivers, and why it matters", "",
            "Each line is a capability the selected positions actually deliver, stated in "
            "terms of the outcome rather than the technology.", ""]
    seen: set[str] = set()
    headline: list[tuple[str, str, str]] = []
    also: dict[str, list[str]] = {}
    for dom_key in catalogue.domain_keys():
        code = catalogue.code_for(dom_key)
        taken = 0
        for cap in selection[dom_key].provides:
            b = bmap.get(cap)
            if not b or b["benefit"] in seen:
                continue
            seen.add(b["benefit"])
            # Two headline outcomes per domain keeps this readable at exec
            # altitude; the rest are listed but not argued.
            if taken < 2:
                headline.append((code, b["benefit"], b["why"]))
                taken += 1
            else:
                also.setdefault(code, []).append(b["benefit"])
    out += ["| Domain | What you get | Why it is worth doing |", "|---|---|---|"]
    for code, benefit, why in headline:
        out.append(f"| {code} | **{esc(benefit)}** | {esc(why)} |")
    out.append("")
    if also:
        out += ["The same positions also deliver:", ""]
        for code in sorted(also):
            out.append(f"- **{code}** - " + "; ".join(esc(b).lower() for b in also[code]) + ".")
        out.append("")

    missing = []
    for cap, b in bmap.items():
        if cap not in caps and catalogue.capabilities.get(cap):
            missing.append((catalogue.capabilities[cap]["owner"], b["benefit"]))
    if missing:
        notable = [m for m in missing if m[0] in ("SEC", "DATA", "NET", "IAM")][:8]
        if notable:
            out += ["### Deliberately not delivered", "",
                    "The selected positions do not provide these. Each is a decision that can "
                    "be revisited, and each is a residual exposure until it is:", ""]
            out += [f"- *{esc(b)}* ({owner})" for owner, b in notable]
            out.append("")

    # ------------------------------------------------------------------ effort
    out += ["## Where the effort and difficulty sit", "",
            "Ranked by combined delivery weight: build effort, cost band, high-severity risk "
            "count and blocking questions.", "",
            "| Rank | Domain | Position | Build | Cost | High/critical risks | Blocking questions |",
            "|---|---|---|---|---|---|---|"]
    for i, e in enumerate(effort[:6], start=1):
        out.append(
            f"| {i} | **{e['domain']}** {esc(e['domain_name'])} | `{e['option']}` {esc(e['name'])} "
            f"| {e['effort_weeks']}w ({e['effort_band']}) | {e['cost_band']} | {e['high_risks']} "
            f"| {e['blocking_questions']} |"
        )
    out += ["", "The top two are where a schedule will actually be won or lost:", ""]
    for e in effort[:2]:
        out.append(f"- **{e['domain']} - {esc(e['name'])}.** {e['why']}")
    out.append("")

    # ----------------------------------------------------------------- roadmap
    out += ["## Expected delivery roadmap", "",
            f"**{roadmap['range_weeks'][0]}-{roadmap['range_weeks'][1]} weeks "
            f"({roadmap['range_months'][0]}-{roadmap['range_months'][1]} months)**, "
            f"{roadmap['uncertainty_band']} around a {roadmap['total_weeks']}-week central "
            f"estimate. These are rough order of magnitude for shaping and funding, not a plan.",
            "",
            "| Phase | Weeks | Elapsed | What happens |", "|---|---|---|---|"]
    for p in roadmap["phases"]:
        out.append(f"| {esc(p['name'])} | {p['weeks']:g} | wk {p['starts_week']:g}-{p['ends_week']:g} "
                   f"| {esc(p['detail'])} |")
    out += ["", "**Critical path** - the chain that sets the end date:", ""]
    for x in roadmap["critical_path"]:
        out.append(f"- {x['domain']} `{x['option']}` {esc(x['name'])} - {x['weeks']}w "
                   f"(wk {x['starts_week']:g}-{x['ends_week']:g})")
    out += ["", f"*{roadmap['basis']}*", ""]

    # ------------------------------------------------------------------- risks
    out += ["## Risks that arise with the delivery", "",
            "Filtered up from the nine low-level designs and from the cross-domain "
            "reconciliation. Grouped by the kind of problem they create for the programme.", ""]

    order = ["timeline", "workaround", "legal-reg", "security", "cost", "operational"]
    headline = {
        "timeline": "Timeline challenges",
        "workaround": "Workaround and tactical-debt challenges",
        "legal-reg": "Legal and regulatory considerations",
        "security": "Security exposures arising from the chosen configurations",
        "cost": "Cost exposures",
        "operational": "Operational exposures",
    }
    for cat in order:
        group = sorted([r for r in risks if r.category == cat], key=lambda x: -x.rank)
        if not group:
            continue
        top = [r for r in group if r.severity in ("H", "C")] or group[:3]
        out += [f"### {headline[cat]}", "",
                f"{len(group)} recorded, {len([r for r in group if r.severity in ('H','C')])} "
                f"high or critical.", "",
                "| Severity | Source | Risk | Mitigation |", "|---|---|---|---|"]
        for r in top[:6]:
            tag = f"`{r.source}`" + (" *(emergent)*" if r.emergent else "")
            out.append(f"| **{SEV_LABEL.get(r.severity, r.severity)}** | {tag} "
                       f"| {esc(r.statement)} | {esc(r.mitigation)} |")
        out.append("")

    # ------------------------------------------------------- blocking decisions
    out += ["## What needs a decision now", ""]
    if recon.contradictions:
        out += ["### Contradictions between domains - these block the base plate", ""]
        for c in recon.contradictions:
            out += [f"- **{c.row} vs {c.col}** ({SEV_LABEL.get(c.severity, c.severity)}): {c.detail}"]
        out.append("")
    if recon.gaps:
        out += ["### Gaps - something is required that nothing supplies", ""]
        for g in recon.gaps[:10]:
            out.append(f"- **{g.row} -> {g.col}**: {g.detail}")
        out.append("")

    blocking = [q for opt in selection.values() for q in opt.questions if q.blocking]
    blocking += [q for q in recon.emergent_questions if q.blocking]
    if blocking:
        out += [f"### Blocking questions ({len(blocking)}) - each gates a specific decision", "",
                "| Owner | Question |", "|---|---|"]
        by_owner: dict[str, list] = {}
        for q in blocking:
            by_owner.setdefault(q.owner_role, []).append(q)
        for owner in sorted(by_owner, key=lambda o: -len(by_owner[o])):
            for q in by_owner[owner][:3]:
                out.append(f"| {esc(owner)} | {esc(q.question)} |")
        out += ["", f"_Full list of {cov['questions_total']} questions in "
                f"`registers/questions.csv`._", ""]

    if recon.unpinned:
        out += [f"### Numbers to pin ({len(recon.unpinned)})", "",
                "Positions depending on these cannot be sized, costed or defended. Chase these "
                "before the next funding conversation:", ""]
        for a in recon.unpinned[:12]:
            out.append(f"- **{esc(a.metric)}** ({esc(a.unit)}) - unpinned in "
                       f"{', '.join(a.unpinned_envs())}")
        if len(recon.unpinned) > 12:
            out.append(f"- _...and {len(recon.unpinned) - 12} more, listed in the HLD._")
        out.append("")

    if intake.unstated:
        out += ["### What the brief never said", "",
                "These were carried into the design as assumptions. Confirm or correct them:", ""]
        out += [f"- {u}" for u in intake.unstated] + [""]

    out += ["---", "",
            f"*Project `{project.id}`, generated from `brief.md` alone. Detail: `outputs/hld.md` for the end-to-end design, "
            f"`outputs/lld/` for the nine domain designs, `registers/` for the decision and "
            f"evidence ledgers.*", ""]
    return "\n".join(out)
