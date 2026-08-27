"""The end-to-end orchestrator.

The orchestrator does not re-do domain work. It reconciles it.

Given one selected option per domain it:

  1. detects every incompatibility - unmet cross-domain capability
     requirements, hard conflicts, and mutex rules;
  2. repairs what it can by local search over single-option substitutions,
     always preferring the repair that costs the least domain fit, and
     recording every swap it makes and why;
  3. builds the N x N integration matrix, classifying each cell Satisfied,
     Contradiction, Gap, Unpinned or Not-applicable;
  4. raises the risks and questions that only exist because of a
     *combination*, which no single domain owns;
  5. grades an operability verdict.

Repair is deterministic: same catalogue plus same brief plus same pins gives
the same base plate, which is what makes a run defensible and comparable.
"""

from __future__ import annotations

import copy
from dataclasses import replace

from .model import Anchor, Cell, Option, Question, Reconciliation, Risk

MAX_REPAIR_ITERATIONS = 40


# --------------------------------------------------------------------------
# Violation detection
# --------------------------------------------------------------------------

class Violation:
    __slots__ = ("kind", "severity", "detail", "domains", "capability", "rule_id", "option_id")

    def __init__(self, kind, severity, detail, domains, capability="", rule_id="", option_id=""):
        self.kind = kind              # "gap" | "contradiction"
        self.severity = severity
        self.detail = detail
        self.domains = domains        # [provider_domain_key, consumer_domain_key]
        self.capability = capability
        self.rule_id = rule_id
        self.option_id = option_id

    def weight(self) -> int:
        base = {"contradiction": 10, "gap": 4}[self.kind]
        return base * {"L": 1, "M": 2, "H": 3, "C": 4}.get(self.severity, 2)

    def __repr__(self) -> str:
        return f"<Violation {self.kind} {self.domains} {self.capability or self.rule_id}>"


def _rule_fires(rule, selected_ids: set[str]) -> bool:
    if rule.when_all and not set(rule.when_all).issubset(selected_ids):
        return False
    if rule.when_any and not (set(rule.when_any) & selected_ids):
        return False
    return bool(rule.when_all or rule.when_any)


def find_violations(catalogue, selection: dict[str, Option],
                    mandates: dict[str, list[str]] | None = None) -> list[Violation]:
    provided: set[str] = set()
    for opt in selection.values():
        provided |= catalogue.expand(opt.provides)

    owner_domain: dict[str, str] = {}
    for cap, meta in catalogue.capabilities.items():
        for dom in catalogue.domains:
            if dom.code == meta["owner"]:
                owner_domain[cap] = dom.key
                break

    out: list[Violation] = []
    selected_ids = {o.id for o in selection.values()}

    for cap, sources in (mandates or {}).items():
        if cap in provided:
            continue
        owner = owner_domain.get(cap, "")
        out.append(Violation(
            kind="gap", severity="H",
            detail=(
                f"The brief makes '{cap}' non-negotiable "
                f"({catalogue.capabilities.get(cap, {}).get('desc', '')}) - established by "
                f"{', '.join(sources)}. No selected position supplies it."
            ),
            domains=[owner or list(selection)[0], owner or list(selection)[0]],
            capability=cap,
        ))

    for dom_key, opt in selection.items():
        for cap in opt.requires:
            if cap not in provided:
                out.append(Violation(
                    kind="gap",
                    severity="H",
                    detail=(
                        f"{opt.id} ({opt.name}) requires '{cap}' - "
                        f"{catalogue.capabilities.get(cap, {}).get('desc', '')} "
                        f"No selected option provides it."
                    ),
                    domains=[owner_domain.get(cap, dom_key), dom_key],
                    capability=cap,
                    option_id=opt.id,
                ))
        for other_id in opt.conflicts:
            if other_id in selected_ids and other_id != opt.id:
                other = catalogue.option(other_id)
                out.append(Violation(
                    kind="contradiction",
                    severity="H",
                    detail=f"{opt.id} declares a hard conflict with {other_id} ({other.name}).",
                    domains=[opt.domain, other.domain],
                    option_id=opt.id,
                ))

    for rule in catalogue.rules:
        if not _rule_fires(rule, selected_ids):
            continue
        if rule.kind == "mutex":
            doms = rule.domains or []
            keys = [catalogue.domain(d).key for d in doms] if doms else []
            out.append(Violation(
                kind="contradiction",
                severity=rule.severity,
                detail=rule.message + (f" Resolution: {rule.resolution}" if rule.resolution else ""),
                domains=keys or [list(selection)[0], list(selection)[0]],
                rule_id=rule.id,
            ))
        elif rule.kind == "requires-option" and rule.then_option not in selected_ids:
            req = catalogue.option(rule.then_option)
            out.append(Violation(
                kind="gap", severity=rule.severity,
                detail=rule.message,
                domains=[req.domain, catalogue.option(rule.when_all[0]).domain if rule.when_all else req.domain],
                rule_id=rule.id,
            ))
        elif rule.kind == "capability-gap" and rule.capability:
            if rule.capability not in provided:
                out.append(Violation(
                    kind="gap", severity=rule.severity, detail=rule.message,
                    domains=[owner_domain.get(rule.capability, ""), ""],
                    capability=rule.capability, rule_id=rule.id,
                ))
    return out


def _cost(violations: list[Violation]) -> int:
    return sum(v.weight() for v in violations)


# --------------------------------------------------------------------------
# Repair by local search
# --------------------------------------------------------------------------

def _repair_record(dom_key, incumbent, candidate, fit_loss, before, after,
                   violations, paired: bool = False) -> dict:
    resolved = [v.detail for v in violations
                if dom_key in v.domains or v.option_id == incumbent.id]
    if paired:
        reason = (
            f"Reconciling this required two coordinated changes - no single substitution "
            f"improved the position. {incumbent.id} was replaced by {candidate.id} as part of "
            f"that pair, taking the unresolved cross-domain weight from {before} to {after} at "
            f"a cost of {abs(fit_loss):g} points of domain fit."
        )
    else:
        reason = (
            f"The domain's own highest-scoring option was {incumbent.id}, but it could not be "
            f"reconciled end to end. Substituting {candidate.id} reduced the unresolved "
            f"cross-domain weight from {before} to {after} at a cost of "
            f"{abs(fit_loss):g} points of domain fit."
        )
    return {
        "domain": dom_key,
        "from": incumbent.id,
        "from_name": incumbent.name,
        "to": candidate.id,
        "to_name": candidate.name,
        "fit_loss": fit_loss,
        "violation_cost_before": before,
        "violation_cost_after": after,
        "paired": paired,
        "reason": reason,
        "addressed": resolved[:4],
    }


def _best_pair(catalogue, ranked, selection, locked, mandates, current_cost):
    """Cheapest pair of substitutions that improves on `current_cost`, or None."""
    moves = [
        (dom_key, cand)
        for dom_key, opts in ranked.items() if dom_key not in locked
        for cand in opts if cand.id != selection[dom_key].id
    ]
    best = None
    for i, (da, ca) in enumerate(moves):
        for db, cb in moves[i + 1:]:
            if da == db:
                continue
            trial = dict(selection)
            trial[da], trial[db] = ca, cb
            cost = _cost(find_violations(catalogue, trial, mandates))
            if cost >= current_cost:
                continue
            loss = round((selection[da].score - ca.score) + (selection[db].score - cb.score), 3)
            key = (cost, loss, ca.id, cb.id)
            if best is None or key < best[0]:
                best = (key, da, ca, db, cb, cost, loss)
    if best is None:
        return None
    _key, da, ca, db, cb, cost, loss = best
    half = round(loss / 2, 3)
    return [
        (da, selection[da], ca, cost, half),
        (db, selection[db], cb, cost, half),
    ]


def repair(catalogue, ranked: dict[str, list[Option]], selection: dict[str, Option],
           locked: set[str] | None = None,
           mandates: dict[str, list[str]] | None = None) -> tuple[dict[str, Option], list[dict]]:
    """Reduce violations by single-option substitutions, cheapest fit loss first.

    `locked` names domains the user has fixed by hand; the orchestrator will
    never overrule those, it will route the repair through another domain.
    """
    locked = locked or set()
    selection = dict(selection)
    repairs: list[dict] = []
    current = find_violations(catalogue, selection, mandates)
    current_cost = _cost(current)

    for _ in range(MAX_REPAIR_ITERATIONS):
        if current_cost == 0:
            break
        best = None
        for dom_key, options in ranked.items():
            if dom_key in locked:
                continue
            incumbent = selection[dom_key]
            for candidate in options:
                if candidate.id == incumbent.id:
                    continue
                trial = dict(selection)
                trial[dom_key] = candidate
                trial_cost = _cost(find_violations(catalogue, trial, mandates))
                if trial_cost >= current_cost:
                    continue
                fit_loss = round(incumbent.score - candidate.score, 3)
                # Prefer the biggest violation reduction; break ties on the
                # smallest loss of domain fit.
                key = (trial_cost, fit_loss, candidate.id)
                if best is None or key < best[0]:
                    best = (key, dom_key, incumbent, candidate, trial_cost, fit_loss)
        if best is None:
            # Single swaps have plateaued. Some reconciliations need two
            # coordinated moves - taking a sovereignty position, for instance,
            # can force a matching change in the non-prod data policy. Try
            # every ordered pair once before giving up.
            pair = _best_pair(catalogue, ranked, selection, locked, mandates, current_cost)
            if pair is None:
                break
            for step in pair:
                dom_key, incumbent, candidate, trial_cost, fit_loss = step
                selection[dom_key] = candidate
                repairs.append(_repair_record(
                    dom_key, incumbent, candidate, fit_loss, current_cost, trial_cost,
                    current, paired=True))
            current = find_violations(catalogue, selection, mandates)
            current_cost = _cost(current)
            continue
        _key, dom_key, incumbent, candidate, trial_cost, fit_loss = best
        selection[dom_key] = candidate
        repairs.append(_repair_record(dom_key, incumbent, candidate, fit_loss,
                                      current_cost, trial_cost, current))
        current = find_violations(catalogue, selection, mandates)
        current_cost = _cost(current)

    return selection, repairs


# --------------------------------------------------------------------------
# Matrix, anchors, emergent findings, verdict
# --------------------------------------------------------------------------

def build_matrix(catalogue, selection: dict[str, Option],
                 violations: list[Violation]) -> list[Cell]:
    owner_domain: dict[str, str] = {}
    for cap, meta in catalogue.capabilities.items():
        for dom in catalogue.domains:
            if dom.code == meta["owner"]:
                owner_domain[cap] = dom.key
                break

    provided: dict[str, list[str]] = {}
    for dom_key, opt in selection.items():
        for cap in catalogue.expand(opt.provides):
            provided.setdefault(cap, []).append(dom_key)

    keys = catalogue.domain_keys()
    cells: dict[tuple[str, str], Cell] = {}

    for row in keys:
        for col in keys:
            cells[(row, col)] = Cell(
                row=catalogue.code_for(row), col=catalogue.code_for(col),
                state="not-applicable", detail="",
            )

    # Satisfied dependencies, derived from what each option requires.
    for col, opt in selection.items():
        for cap in opt.requires:
            row = owner_domain.get(cap, col)
            if cap in provided:
                supplier = provided[cap][0]
                cell = cells[(row, col)]
                line = (
                    f"{catalogue.code_for(col)} needs '{cap}'; supplied by "
                    f"{selection[supplier].id} in {catalogue.code_for(supplier)}."
                )
                if cell.state in ("not-applicable", "satisfied"):
                    cell.state = "satisfied"
                    cell.detail = (cell.detail + " " + line).strip()
                    cell.capability = cap

    # Violations overwrite - a contradiction always wins the cell.
    for v in violations:
        if len(v.domains) < 2 or not v.domains[0] or not v.domains[1]:
            row = v.domains[0] if v.domains and v.domains[0] else keys[0]
            col = v.domains[1] if len(v.domains) > 1 and v.domains[1] else row
        else:
            row, col = v.domains[0], v.domains[1]
        if row not in cells and (row, col) not in cells:
            continue
        cell = cells.get((row, col))
        if cell is None:
            continue
        if cell.state == "contradiction" and v.kind != "contradiction":
            continue
        cell.state = v.kind
        cell.detail = v.detail
        cell.capability = v.capability
        cell.rule_id = v.rule_id
        cell.severity = v.severity

    return [cells[(r, c)] for r in keys for c in keys]


def collect_anchors(catalogue, selection: dict[str, Option],
                    pins: dict[str, dict] | None = None) -> dict[str, list[Anchor]]:
    """Gather each domain's anchors, applying any pinned values from the project.

    A pin file lets a run be re-orchestrated as real numbers land - that is
    the iterate step of the lifecycle, and it is how a run moves from
    'Not yet a base plate' to Conditional or Stable.
    """
    pins = pins or {}
    selected_ids = {o.id for o in selection.values()}
    elevate: set[str] = set()
    for rule in catalogue.rules:
        if rule.kind == "anchor-required" and _rule_fires(rule, selected_ids):
            elevate.add(rule.anchor_metric)

    out: dict[str, list[Anchor]] = {}
    for dom_key, opt in selection.items():
        anchors: list[Anchor] = []
        for a in opt.anchors:
            a = replace(a)
            pinned = pins.get(dom_key, {}).get(a.metric) or pins.get(a.metric)
            if isinstance(pinned, dict):
                a.prod = str(pinned.get("prod", a.prod))
                a.rtl = str(pinned.get("rtl", a.rtl))
                a.devtest = str(pinned.get("devtest", a.devtest))
            elif isinstance(pinned, str):
                a.prod = a.rtl = a.devtest = pinned
            if a.metric in elevate:
                a.critical = True
                a.note = (a.note + " Elevated to sizing-critical by another domain's selection.").strip()
            anchors.append(a)
        out[dom_key] = anchors
    return out


def emergent_findings(catalogue, selection: dict[str, Option]) -> tuple[list[Risk], list[Question], list[dict]]:
    """Risks and questions that exist only because of a combination."""
    selected_ids = {o.id for o in selection.values()}
    risks: list[Risk] = []
    questions: list[Question] = []
    fired: list[dict] = []
    for rule in catalogue.rules:
        if not _rule_fires(rule, selected_ids):
            continue
        if rule.kind == "emergent-risk" and rule.risk:
            r = copy.deepcopy(rule.risk)
            trigger = sorted(set(rule.when_all) | (set(rule.when_any) & selected_ids))
            r.source = f"{rule.id} ({' + '.join(trigger)})"
            risks.append(r)
            fired.append({"rule": rule.id, "kind": rule.kind, "message": rule.message,
                          "trigger": trigger})
        elif rule.kind == "question-raised" and rule.question:
            q = copy.deepcopy(rule.question)
            trigger = sorted(set(rule.when_all) | (set(rule.when_any) & selected_ids))
            q.source = f"{rule.id} ({' + '.join(trigger)})"
            questions.append(q)
            fired.append({"rule": rule.id, "kind": rule.kind, "message": rule.message,
                          "trigger": trigger})
        elif rule.kind == "anchor-required":
            fired.append({"rule": rule.id, "kind": rule.kind, "message": rule.message,
                          "trigger": sorted(set(rule.when_all) | (set(rule.when_any) & selected_ids))})
    return risks, questions, fired


def grade(contradictions: list[Cell], gaps: list[Cell],
          unpinned_critical: list[Anchor], blocking_questions: int) -> tuple[str, str]:
    if contradictions:
        return "not-yet", (
            f"{len(contradictions)} unresolved contradiction(s) remain between domains. "
            "A base plate cannot be stable while two domains assert incompatible positions - "
            "these must be resolved by decision, not by note."
        )
    if unpinned_critical:
        return "not-yet", (
            f"No contradictions remain, but {len(unpinned_critical)} sizing-critical volumetric "
            "anchor(s) are still unpinned. Positions that depend on an unquantified anchor cannot "
            "be sized, costed or defended."
        )
    if gaps or blocking_questions:
        return "conditional", (
            f"The position is coherent end to end. {len(gaps)} gap(s) and {blocking_questions} "
            "blocking question(s) remain, each gating a specific decision rather than the whole "
            "direction. Assign an owner and a date to each."
        )
    return "stable", (
        "No contradictions, no unpinned critical anchors, and no blocking questions outstanding. "
        "The base plate is defensible as it stands."
    )


def _collapse_repairs(repairs: list[dict]) -> list[dict]:
    """One record per domain, preserving the true start and end of a repair chain.

    Local search can move a domain more than once - IAM-01 to IAM-02 to IAM-03 -
    as other domains settle. Reporting only the last hop would credit the wrong
    starting position to the domain, so collapse the chain but keep the path.
    """
    by_domain: dict[str, list[dict]] = {}
    order: list[str] = []
    for r in repairs:
        if r["domain"] not in by_domain:
            order.append(r["domain"])
        by_domain.setdefault(r["domain"], []).append(r)

    out: list[dict] = []
    for dom in order:
        chain = by_domain[dom]
        first, last = chain[0], chain[-1]
        if first["from"] == last["to"]:
            continue  # moved away and back again: no net change to report
        merged = dict(last)
        merged["from"] = first["from"]
        merged["from_name"] = first["from_name"]
        merged["violation_cost_before"] = first["violation_cost_before"]
        merged["fit_loss"] = round(sum(c["fit_loss"] for c in chain), 3)
        merged["paired"] = any(c.get("paired") for c in chain)
        merged["steps"] = [c["from"] for c in chain] + [last["to"]]
        seen, addressed = set(), []
        for c in chain:
            for detail in c["addressed"]:
                if detail not in seen:
                    seen.add(detail)
                    addressed.append(detail)
        merged["addressed"] = addressed[:4]
        via = (" via " + " -> ".join(merged["steps"][1:-1])) if len(chain) > 1 else ""
        merged["reason"] = (
            f"The domain's own highest-scoring option was {first['from']}, but it could not be "
            f"reconciled end to end. Substituting {last['to']}{via} took the unresolved "
            f"cross-domain weight from {first['violation_cost_before']} to "
            f"{last['violation_cost_after']} at a cost of {abs(merged['fit_loss']):g} points of "
            f"domain fit."
            + (" Part of this needed two coordinated changes - no single substitution improved "
               "the position." if merged["paired"] else "")
        )
        out.append(merged)
    return out


def orchestrate(catalogue, ranked: dict[str, list[Option]],
                overrides: dict[str, str] | None = None,
                pins: dict[str, dict] | None = None,
                mandates: dict[str, list[str]] | None = None,
                ) -> tuple[dict[str, Option], Reconciliation]:
    """Full fan-in: select, repair, reconcile, grade."""
    overrides = overrides or {}
    locked = set()
    selection: dict[str, Option] = {}
    for dom_key, options in ranked.items():
        chosen = options[0]
        if dom_key in overrides:
            for o in options:
                if o.id == overrides[dom_key]:
                    chosen = o
                    locked.add(dom_key)
                    break
        selection[dom_key] = chosen

    selection, repairs = repair(catalogue, ranked, selection, locked=locked, mandates=mandates)
    repairs = _collapse_repairs(repairs)
    violations = find_violations(catalogue, selection, mandates)
    cells = build_matrix(catalogue, selection, violations)

    contradictions = [c for c in cells if c.state == "contradiction"]
    gaps = [c for c in cells if c.state == "gap"]

    anchors_by_domain = collect_anchors(catalogue, selection, pins)
    unpinned = [a for anchors in anchors_by_domain.values()
                for a in anchors if a.critical and a.is_unpinned()]

    e_risks, e_questions, fired = emergent_findings(catalogue, selection)

    blocking = sum(1 for opt in selection.values() for q in opt.questions if q.blocking)
    blocking += sum(1 for q in e_questions if q.blocking)

    verdict, rationale = grade(contradictions, gaps, unpinned, blocking)

    total_anchors = sum(len(a) for a in anchors_by_domain.values())
    pinned_anchors = sum(1 for a in anchors_by_domain.values() for x in a if not x.is_unpinned())
    coverage = {
        "domains_assessed": len(selection),
        "checklist_items": sum(len(o.checklist) for o in selection.values()),
        "questions_total": sum(len(o.questions) for o in selection.values()) + len(e_questions),
        "questions_blocking": blocking,
        "anchors_total": total_anchors,
        "anchors_pinned": pinned_anchors,
        "anchors_unpinned_critical": len(unpinned),
        "cells_satisfied": sum(1 for c in cells if c.state == "satisfied"),
        "cells_contradiction": len(contradictions),
        "cells_gap": len(gaps),
        "rules_fired": len(fired),
        "repairs_applied": len(repairs),
        "risks_total": sum(len(o.risks) for o in selection.values()) + len(e_risks),
        "risks_emergent": len(e_risks),
        "locked_domains": sorted(locked),
        "mandates_total": len(mandates or {}),
        "mandates_unmet": sum(1 for v in violations if v.kind == "gap" and not v.option_id
                              and not v.rule_id),
    }

    recon = Reconciliation(
        verdict=verdict,
        verdict_rationale=rationale,
        cells=cells,
        contradictions=contradictions,
        gaps=gaps,
        unpinned=unpinned,
        emergent_risks=e_risks,
        emergent_questions=e_questions,
        repairs=repairs,
        coverage=coverage,
    )
    recon.anchors_by_domain = anchors_by_domain  # type: ignore[attr-defined]
    recon.rules_fired = fired                     # type: ignore[attr-defined]
    return selection, recon
