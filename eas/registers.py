"""The dual ledger: decisions and evidence.

Framework sec 4.4 - positions and the checks behind them are kept apart, so a
score or a position can be decomposed and defended under model-risk challenge
rather than asserted.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from .model import Decision, Evidence
from .selector import explain


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_decisions(catalogue, selection, ranked, recon) -> list[Decision]:
    out: list[Decision] = []
    repaired = {r["domain"]: r for r in recon.repairs}
    for i, dom_key in enumerate(catalogue.domain_keys(), start=1):
        opt = selection[dom_key]
        dom = catalogue.domain(dom_key)
        alternatives = [o for o in ranked[dom_key] if o.id != opt.id][:2]
        rationale = (
            f"Scored {opt.score:g} against the intake signals ({explain(opt)}). "
            + (
                f"Considered against {', '.join(f'{a.id} ({a.score:g})' for a in alternatives)}. "
                if alternatives else ""
            )
        )
        status = "proposed"
        if dom_key in repaired:
            r = repaired[dom_key]
            rationale += (
                f"Not the domain's own first choice: {r['from']} ranked higher on domain fit but "
                f"could not be reconciled end to end, so the orchestrator substituted {r['to']}."
            )
            status = "orchestrator-adjusted"
        elif dom_key in recon.coverage.get("locked_domains", []):
            rationale += "Fixed by hand in the project's overrides; the orchestrator did not overrule it."
            status = "fixed-by-owner"
        out.append(Decision(
            id=f"D-{i:02d}",
            domain=dom.name,
            position=opt.name,
            option_id=opt.id,
            rationale=rationale.strip(),
            environments=" / ".join(["Prod", "RTL", "Dev-Test"]),
            owner=f"{dom.code} domain owner (TBC)",
            status=status,
        ))
    return out


def build_evidence(catalogue, selection, recon, intake) -> list[Evidence]:
    out: list[Evidence] = []
    n = 0
    ts = _now()

    def add(checked, method, result, anchor="", source=""):
        nonlocal n
        n += 1
        out.append(Evidence(id=f"E-{n:03d}", checked=checked, method=method,
                            result=result, anchor=anchor, source=source, timestamp=ts))

    add("Brief complexity graded", "Weighted signal detection over the brief text",
        f"Tier {intake.tier} - {intake.tier_rationale}", source="eas.intake")
    for key, sig in sorted(intake.signals.items()):
        if sig.inferred:
            continue
        add(f"Intake signal '{key}' detected",
            f"Regex pattern match, confidence {sig.confidence}",
            f"Evidence from brief: \"{sig.evidence}\"", source="catalogue/signals.json")

    for dom_key, opt in selection.items():
        dom = catalogue.domain(dom_key)
        add(f"{dom.name}: option scored and selected",
            f"Decomposable scoring, skill {dom.skill}",
            f"{opt.id} scored {opt.score:g}. Breakdown: "
            + ", ".join(f"{k}={v:+g}" for k, v in sorted(opt.score_breakdown.items())),
            source=f"catalogue/options/{dom_key}.json")
        add(f"{dom.name}: checklist surface established",
            "Option checklist expanded into the domain LLD",
            f"{len(opt.checklist)} checklist items, {len(opt.questions)} further-questioning items, "
            f"{len(opt.anchors)} volumetric anchors.",
            source=opt.id)

    add("Cross-domain reconciliation executed",
        "N x N integration matrix over selected options",
        f"{recon.coverage['cells_satisfied']} satisfied, "
        f"{recon.coverage['cells_contradiction']} contradiction, "
        f"{recon.coverage['cells_gap']} gap.", source="eas.orchestrator")

    for r in recon.repairs:
        add(f"Orchestrator repair in {r['domain']}",
            "Local search over single-option substitutions",
            f"{r['from']} -> {r['to']}; unresolved cross-domain weight "
            f"{r['violation_cost_before']} -> {r['violation_cost_after']}, "
            f"domain fit cost {abs(r['fit_loss']):g}.", source="eas.orchestrator")

    for f in getattr(recon, "rules_fired", []):
        add(f"Compatibility rule {f['rule']} fired",
            f"Rule kind: {f['kind']}",
            f"{f['message']} Triggered by {' + '.join(f['trigger'])}.",
            source="catalogue/compat.json")

    for a in recon.unpinned:
        add(f"Volumetric anchor '{a.metric}' checked",
            "Anchor pin lookup against inputs/anchors.json",
            f"UNPINNED in {', '.join(a.unpinned_envs())} - sizing-critical.",
            anchor=a.metric, source="inputs/anchors.json")

    add("Operability verdict graded", "Framework grading rules (sec 4.3)",
        f"{recon.verdict}: {recon.verdict_rationale}", source="eas.orchestrator")
    return out


def decisions_markdown(decisions: list[Decision]) -> str:
    lines = ["# Decision Ledger", "",
             "Each row is a position taken, why it was taken, and who owns it. "
             "A superseded position is retained rather than deleted.", "",
             "| ID | Domain | Position | Option | Status | Environments | Owner |",
             "|---|---|---|---|---|---|---|"]
    for d in decisions:
        lines.append(
            f"| {d.id} | {d.domain} | {d.position} | `{d.option_id}` | {d.status} "
            f"| {d.environments} | {d.owner} |"
        )
    lines += ["", "## Rationale", ""]
    for d in decisions:
        lines += [f"### {d.id} - {d.domain}", "", f"**Position:** {d.position} (`{d.option_id}`)",
                  "", d.rationale, ""]
    return "\n".join(lines) + "\n"


def evidence_markdown(evidence: list[Evidence]) -> str:
    lines = ["# Evidence / Audit Ledger", "",
             "What was checked, how, what came back, and when. Kept separate from the "
             "decision ledger so a position and its supporting check can be challenged "
             "independently.", "",
             "| ID | Checked | Method | Result | Anchor | Source |",
             "|---|---|---|---|---|---|"]
    for e in evidence:
        result = e.result.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {e.id} | {e.checked} | {e.method} | {result} | {e.anchor or '-'} | `{e.source}` |"
        )
    lines += ["", f"_All entries timestamped {evidence[0].timestamp if evidence else '-'}._", ""]
    return "\n".join(lines) + "\n"


def risks_csv(risks) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["id", "domain", "category", "severity", "emergent", "statement",
                "mitigation", "source"])
    for r in risks:
        w.writerow([r.id, r.domain, r.category, r.severity, "yes" if r.emergent else "no",
                    r.statement, r.mitigation, r.source])
    return buf.getvalue()


def questions_csv(questions) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["id", "domain", "blocking", "owner_role", "question", "source"])
    for q in questions:
        w.writerow([q.id, q.domain, "yes" if q.blocking else "no", q.owner_role,
                    q.question, q.source])
    return buf.getvalue()
