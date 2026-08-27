"""Per-domain option scoring.

Each validator domain offers a set of options. The selector ranks them against
the intake signals and returns the full ranked list - not just a winner. The
shortlist is the domain's deliverable; the orchestrator then interrogates the
leading choices against every other domain and may overrule them.

Scoring is deliberately decomposable. Every point in a score traces to a named
signal with the phrase from the brief that fired it, because a score that
cannot be taken apart cannot be defended under model-risk challenge
(framework sec 4.4, SS1/23).
"""

from __future__ import annotations

from .model import Intake, Option

# Weights for the parts of the score that are not signal fit.
W_FIT = 1.0
W_SECURITY = 0.6
W_REG = 0.5
W_EFFORT = 0.7        # penalty per effort band above the tier's comfort
W_COST = 0.4
W_OPS = 0.3
W_MANDATE = 1.6       # per mandated capability this option supplies

# What delivery weight each tier can reasonably carry, as an effort band rank.
_TIER_EFFORT_COMFORT = {"T1": 2, "T2": 3, "T3": 4, "T4": 5}

# How much a regulated context should push toward posture.
_POSTURE_BONUS = {"tactical": 0.0, "balanced": 0.5, "strategic": 1.0}


def score_option(option: Option, intake: Intake,
                 provides_expanded: set[str] | None = None) -> tuple[float, dict[str, float]]:
    """Return (score, breakdown). Breakdown keys are human-readable reasons."""
    breakdown: dict[str, float] = {}

    # A capability the brief made non-negotiable outweighs soft preference.
    supplied = provides_expanded if provides_expanded is not None else set(option.provides)
    for cap, sources in intake.mandates.items():
        if cap in supplied:
            breakdown[f"mandate:{cap}"] = round(W_MANDATE, 3)

    for signal_key, weight in option.fit.items():
        sig = intake.signals.get(signal_key)
        if sig and sig.value:
            contribution = round(weight * sig.confidence * W_FIT, 3)
            if contribution:
                breakdown[f"signal:{signal_key}"] = contribution

    breakdown["posture:security"] = round((option.security_score - 3) * W_SECURITY, 3)
    breakdown["posture:regulatory"] = round((option.reg_score - 3) * W_REG, 3)

    comfort = _TIER_EFFORT_COMFORT[intake.tier]
    over = max(0, option.effort_rank - comfort)
    if over:
        breakdown["penalty:effort-above-tier"] = round(-over * W_EFFORT, 3)
    under = max(0, comfort - option.effort_rank - 1)
    if under and intake.signal_on("regulated"):
        # A regulated T3/T4 that picks the cheapest possible option is usually
        # not being efficient, it is deferring the work into a risk register.
        breakdown["penalty:under-invested-for-tier"] = round(-under * 0.4, 3)

    breakdown["penalty:cost"] = round(-(option.cost_rank - 3) * W_COST, 3)
    breakdown["penalty:ops-burden"] = round(-(option.ops_burden - 3) * W_OPS, 3)

    if intake.signal_on("regulated"):
        breakdown["context:regulated-posture"] = round(_POSTURE_BONUS[option.posture], 3)
    if intake.signal_on("time-pressured") and option.effort_rank >= 4:
        breakdown["penalty:hard-date-vs-large-effort"] = -1.2
    if intake.signal_on("cost-constrained") and option.cost_rank >= 4:
        breakdown["penalty:cost-constraint-vs-spend"] = -1.0

    breakdown = {k: v for k, v in breakdown.items() if v}
    return round(sum(breakdown.values()), 3), breakdown


def rank_domain(catalogue, domain_key: str, intake: Intake) -> list[Option]:
    """Score and rank every option in one domain. Returns new Option copies."""
    import copy

    ranked: list[Option] = []
    for opt in catalogue.options_for(domain_key):
        o = copy.deepcopy(opt)
        o.score, o.score_breakdown = score_option(
            o, intake, provides_expanded=catalogue.expand(o.provides))
        ranked.append(o)
    ranked.sort(key=lambda o: (-o.score, o.effort_rank, o.id))
    for i, o in enumerate(ranked, start=1):
        o.rank = i
    return ranked


def rank_all(catalogue, intake: Intake) -> dict[str, list[Option]]:
    return {k: rank_domain(catalogue, k, intake) for k in catalogue.domain_keys()}


def explain(option: Option) -> str:
    """One-line, decomposable justification for a score."""
    if not option.score_breakdown:
        return "Neutral against every intake signal."
    parts = sorted(option.score_breakdown.items(), key=lambda kv: -abs(kv[1]))
    rendered = []
    for key, val in parts[:6]:
        label = key.split(":", 1)[1].replace("-", " ")
        rendered.append(f"{label} {val:+g}")
    return "; ".join(rendered)
