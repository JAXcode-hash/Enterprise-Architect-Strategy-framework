"""Delivery sequencing and rough-order estimation.

The roadmap is derived, not asserted. Domains are ordered by what they must
supply to each other: a domain that provides a capability another domain
requires has to land first. Waves are the layers of that dependency graph,
which is also where genuine parallelism is available.

Estimates are deliberately banded. A rough order of magnitude presented as a
single number invites a commitment the base plate cannot support, so every
figure carries an explicit uncertainty band that widens with complexity.
"""

from __future__ import annotations

from .model import Option

# Uncertainty band by complexity tier - wider where more is unknown.
_BAND = {"T1": 0.25, "T2": 0.30, "T3": 0.40, "T4": 0.50}

# Mobilisation before any build, in weeks.
_MOBILISE = {"T1": 2, "T2": 4, "T3": 6, "T4": 8}

# Assurance, rehearsal and evidence runway after the last build wave.
_ASSURANCE = {"T1": 2, "T2": 4, "T3": 7, "T4": 10}

# Coordination overhead once a wave carries more than this many domains.
_PARALLEL_COMFORT = 3
_COORDINATION_UPLIFT = 0.15

# How far a consumer domain can start before its provider finishes. A domain
# does not need its dependency complete to begin - it needs the interface
# stable. Strict serialisation would produce an estimate no programme would
# recognise; zero lag would ignore the dependency entirely.
_DEPENDENCY_LAG = 0.5


def dependency_edges(catalogue, selection: dict[str, Option]) -> list[tuple[str, str]]:
    """(provider_domain, consumer_domain) - provider must land first."""
    provider_of: dict[str, str] = {}
    for dom_key, opt in selection.items():
        for cap in catalogue.expand(opt.provides):
            provider_of.setdefault(cap, dom_key)

    edges: set[tuple[str, str]] = set()
    for dom_key, opt in selection.items():
        for cap in opt.requires:
            src = provider_of.get(cap)
            if src and src != dom_key:
                edges.add((src, dom_key))
    return sorted(edges)


def waves(catalogue, selection: dict[str, Option]) -> list[list[str]]:
    """Layer the dependency graph. Cycles are broken on the framework's gating order."""
    edges = dependency_edges(catalogue, selection)
    order = {d.key: d.order for d in catalogue.domains}
    remaining = set(selection)
    incoming: dict[str, set[str]] = {d: set() for d in remaining}
    for src, dst in edges:
        if src in remaining and dst in remaining:
            incoming[dst].add(src)

    layers: list[list[str]] = []
    while remaining:
        ready = sorted([d for d in remaining if not (incoming[d] & remaining)],
                       key=lambda d: order[d])
        if not ready:
            # Mutual dependency: fall back to the framework's gating order and
            # note that these domains have to be designed together.
            ready = [min(remaining, key=lambda d: order[d])]
        layers.append(ready)
        remaining -= set(ready)
    return layers


def _wave_weeks(selection: dict[str, Option], domains: list[str]) -> int:
    if not domains:
        return 0
    longest = max(selection[d].effort_weeks for d in domains)
    if len(domains) > _PARALLEL_COMFORT:
        longest = int(round(longest * (1 + _COORDINATION_UPLIFT)))
    return longest


def schedule(catalogue, selection: dict[str, Option]) -> tuple[dict[str, dict], list[list[str]]]:
    """Earliest start and end per domain, fast-tracked against its dependencies.

    Layering breaks any dependency cycle first, then each domain starts once
    every provider in an earlier layer is `_DEPENDENCY_LAG` of the way through.
    """
    layers = waves(catalogue, selection)
    layer_of = {d: i for i, layer in enumerate(layers) for d in layer}
    preds: dict[str, list[str]] = {d: [] for d in selection}
    for src, dst in dependency_edges(catalogue, selection):
        if layer_of.get(src, 0) < layer_of.get(dst, 0):
            preds[dst].append(src)

    plan: dict[str, dict] = {}
    for layer in layers:
        uplift = 1 + _COORDINATION_UPLIFT if len(layer) > _PARALLEL_COMFORT else 1.0
        for d in layer:
            weeks = selection[d].effort_weeks * uplift
            start = 0.0
            for p in preds[d]:
                start = max(start, plan[p]["start"] + _DEPENDENCY_LAG * plan[p]["weeks"])
            plan[d] = {
                "start": round(start, 1),
                "weeks": round(weeks, 1),
                "end": round(start + weeks, 1),
                "depends_on": [catalogue.code_for(p) for p in preds[d]],
                "layer": layer_of[d],
            }
    return plan, layers


def build_roadmap(catalogue, selection: dict[str, Option], intake) -> dict:
    plan, layers = schedule(catalogue, selection)
    band = _BAND[intake.tier]
    mob = _MOBILISE[intake.tier]
    assurance = _ASSURANCE[intake.tier]

    build_weeks = max((v["end"] for v in plan.values()), default=0)
    total = int(round(mob + build_weeks + assurance))

    phases = [{
        "name": "Mobilise, discover and answer the blocking questions",
        "weeks": mob,
        "starts_week": 0,
        "ends_week": mob,
        "domains": [],
        "items": [],
        "detail": (
            "Stand up the delivery, complete the discovery each domain named as a "
            "prerequisite, and close the blocking further-questioning items. A position "
            "that depends on an unanswered question cannot be committed to a date."
        ),
    }]

    for i, layer in enumerate(layers, start=1):
        starts = min(plan[d]["start"] for d in layer)
        ends = max(plan[d]["end"] for d in layer)
        parallel_note = (
            f" {len(layer)} domains run concurrently here, so a coordination uplift is applied."
            if len(layer) > _PARALLEL_COMFORT else ""
        )
        phases.append({
            "name": f"Wave {i}: " + ", ".join(catalogue.code_for(d) for d in layer),
            "weeks": round(ends - starts, 1),
            "starts_week": round(mob + starts, 1),
            "ends_week": round(mob + ends, 1),
            "domains": layer,
            "items": [
                f"{catalogue.code_for(d)} - {selection[d].name} "
                f"({selection[d].effort_weeks}w"
                + (f", after {', '.join(plan[d]['depends_on'])}" if plan[d]["depends_on"] else "")
                + ")"
                for d in layer
            ],
            "detail": (
                ("These domains supply capabilities later waves require, so they gate what follows."
                 if i < len(layers) else
                 "Final build wave; these domains consume what the earlier waves provided.")
                + parallel_note
            ),
        })

    phases.append({
        "name": "Assurance, rehearsal and evidence",
        "weeks": assurance,
        "starts_week": round(mob + build_weeks, 1),
        "ends_week": total,
        "domains": [],
        "items": [],
        "detail": (
            "Detection content tuning, failover and restore rehearsal at production scale, "
            "control evidence production, and closure of the exception register. This runway "
            "is the one most often cut, and cutting it is what leaves a position asserted "
            "rather than evidenced."
        ),
    })

    low = int(round(total * (1 - band)))
    high = int(round(total * (1 + band)))

    # The critical path is the chain of domains that actually sets the end date.
    tail = max(plan, key=lambda d: plan[d]["end"])
    chain = [tail]
    guard = 0
    while plan[chain[-1]]["depends_on"] and guard < 20:
        guard += 1
        code_to_key = {catalogue.code_for(k): k for k in plan}
        prev = max(
            (code_to_key[c] for c in plan[chain[-1]]["depends_on"] if c in code_to_key),
            key=lambda d: plan[d]["end"], default=None,
        )
        if prev is None or prev in chain:
            break
        chain.append(prev)
    chain.reverse()

    return {
        "tier": intake.tier,
        "phases": phases,
        "domain_schedule": {
            catalogue.code_for(d): {**v, "option": selection[d].id,
                                    "name": selection[d].name}
            for d, v in plan.items()
        },
        "total_weeks": total,
        "build_weeks": round(build_weeks, 1),
        "mobilise_weeks": mob,
        "assurance_weeks": assurance,
        "range_weeks": [low, high],
        "range_months": [round(low / 4.33, 1), round(high / 4.33, 1)],
        "uncertainty_band": f"+/-{int(band * 100)}%",
        "waves": [[catalogue.code_for(d) for d in layer] for layer in layers],
        "critical_path": [{
            "domain": catalogue.code_for(d),
            "option": selection[d].id,
            "name": selection[d].name,
            "weeks": selection[d].effort_weeks,
            "starts_week": round(mob + plan[d]["start"], 1),
            "ends_week": round(mob + plan[d]["end"], 1),
        } for d in chain],
        "dependency_edges": [
            [catalogue.code_for(a), catalogue.code_for(b)]
            for a, b in dependency_edges(catalogue, selection)
        ],
        "basis": (
            f"Domains in the same wave have no dependency on each other and run concurrently. "
            f"A domain in a later wave starts once its providers are {int(_DEPENDENCY_LAG * 100)}% "
            f"through, which is when the interface it consumes is stable - full serialisation "
            f"would produce a figure no delivery would recognise. Mobilisation ({mob}w) and the "
            f"assurance runway ({assurance}w) are set by complexity tier {intake.tier}. Figures "
            f"are rough order of magnitude for shaping and funding, not a plan."
        ),
    }


def significant_effort(catalogue, selection: dict[str, Option]) -> list[dict]:
    """Where the delivery weight and the delivery risk actually sit."""
    out = []
    for dom_key, opt in selection.items():
        heavy_risks = [r for r in opt.risks if r.severity in ("H", "C")]
        blocking = [q for q in opt.questions if q.blocking]
        weight = (
            opt.effort_rank * 2
            + len(heavy_risks)
            + len(blocking)
            + (2 if opt.cost_rank >= 4 else 0)
        )
        out.append({
            "domain": catalogue.code_for(dom_key),
            "domain_name": catalogue.domain(dom_key).name,
            "option": opt.id,
            "name": opt.name,
            "effort_weeks": opt.effort_weeks,
            "effort_band": opt.effort_band,
            "cost_band": opt.cost_band,
            "high_risks": len(heavy_risks),
            "blocking_questions": len(blocking),
            "weight": weight,
            "why": (
                f"{opt.effort_weeks} weeks of build at effort band {opt.effort_band} and cost "
                f"band {opt.cost_band}, carrying {len(heavy_risks)} high or critical risk(s) and "
                f"{len(blocking)} blocking question(s)."
            ),
        })
    out.sort(key=lambda x: -x["weight"])
    return out
