"""The options each domain put on the table.

This is the domain validator's own deliverable: not a single answer, but the
set of defensible positions with what each costs, what it needs from other
domains, and why it scored the way it did. The orchestrator's choice is
recorded here too, including where it overruled the domain's own preference.
"""

from __future__ import annotations

from ..selector import explain
from .common import esc, risks_table


def render_domain_options(catalogue, domain_key, ranked, selection, recon, intake) -> str:
    dom = catalogue.domain(domain_key)
    chosen = selection[domain_key]
    repair = next((r for r in recon.repairs if r["domain"] == domain_key), None)
    locked = domain_key in recon.coverage.get("locked_domains", [])

    out = [
        f"# {dom.name} - options",
        "",
        f"**Domain** `{dom.key}` (`{dom.code}`) &nbsp;|&nbsp; **Skill** `{dom.skill}` "
        f"&nbsp;|&nbsp; **Complexity** {intake.tier}",
        "",
        f"*{dom.scope}*",
        "",
        "## Selected position",
        "",
        f"**{chosen.id} - {chosen.name}**",
        "",
        chosen.summary,
        "",
    ]
    if locked:
        out += ["> Fixed by hand in this project's `inputs/overrides.json`. The orchestrator "
                "did not overrule it and routed any repair through other domains.", ""]
    elif repair:
        out += [
            f"> The orchestrator overruled this domain's own preference. `{repair['from']}` "
            f"({repair['from_name']}) scored higher on domain fit but could not be reconciled "
            f"end to end. {repair['reason']}",
            "",
        ]
    else:
        out += ["> This was both the domain's highest-scoring option and reconcilable end to "
                "end, so no adjustment was needed.", ""]

    out += [
        "## All options considered",
        "",
        "Scores are decomposable by design - every point traces to a named intake signal "
        "and the phrase in the brief that fired it.",
        "",
        "| Rank | Option | Posture | Score | Effort | Cost | Security | Regulatory | Selected |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for o in ranked[domain_key]:
        mark = "**yes**" if o.id == chosen.id else ""
        out.append(
            f"| {o.rank} | `{o.id}` {esc(o.name)} | {o.posture} | {o.score:g} "
            f"| {o.effort_band} ({o.effort_weeks}w) | {o.cost_band} | {o.security_score}/5 "
            f"| {o.reg_score}/5 | {mark} |"
        )
    out.append("")

    for o in ranked[domain_key]:
        out += [
            f"### {o.id} - {o.name}",
            "",
            f"*{o.posture.title()} posture. {o.effort_weeks} weeks, effort band {o.effort_band}, "
            f"cost band {o.cost_band}. Security {o.security_score}/5, regulatory evidencing "
            f"{o.reg_score}/5, operational burden {o.ops_burden}/5.*",
            "",
            o.summary,
            "",
            f"**Score {o.score:g}** - {explain(o)}",
            "",
        ]
        if o.provides:
            out += ["**Gives the rest of the estate:** "
                    + ", ".join(f"`{c}`" for c in o.provides), ""]
        if o.requires:
            out += ["**Needs back from other domains:** "
                    + ", ".join(f"`{c}`" for c in o.requires), ""]
        if o.risks:
            out += ["**Risks carried by this option**", ""] + risks_table(o.risks)
    return "\n".join(out) + "\n"
