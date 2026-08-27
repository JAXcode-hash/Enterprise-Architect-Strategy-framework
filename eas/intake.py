"""Intake: turn a brief of any complexity into a structured, evidenced position.

A brief may be three sentences or thirty pages. The intake reads it the same
way either way:

  * fire signals from the catalogue's pattern set, recording the phrase that
    fired each one, so every downstream score traces to a sentence
  * grade complexity T1-T4 from the weighted signal set plus brief length
  * pull structured sections (objects, integrations, environments,
    constraints, drivers) where the brief has them
  * record what the brief did *not* say, which is the part that matters -
    a silence is not an absence of requirement, it is an unasked question
"""

from __future__ import annotations

import re
import unicodedata

from .model import COMPLEXITY_TIERS, Intake, Signal, TIER_NAMES

# Sections we will read if the brief happens to be structured.
_SECTION_ALIASES = {
    "objects": ["objects", "components", "in-scope objects", "scope", "in scope",
                "systems", "applications", "capabilities"],
    "integrations": ["integrations", "interfaces", "dependencies", "connectivity",
                     "data flows", "flows"],
    "environments": ["environments", "environment topology", "topology", "estate"],
    "constraints": ["constraints", "known constraints", "assumptions", "limitations",
                    "non-negotiables"],
    "drivers": ["drivers", "objectives", "outcomes", "goals", "why", "business case",
                "benefits", "rationale"],
}

# Silence checks - a brief that says nothing about these is not a brief that
# has no requirement here. Each becomes an intake-level open question.
_SILENCE_CHECKS = [
    ("environments", ["rtl", "non-prod", "non production", "dev-test", "dev test",
                      "test environment", "staging", "pre-prod", "uat"],
     "The brief does not describe the non-production estate. Every domain position "
     "has to hold in RTL and Dev-Test as well as Prod; assume nothing about them."),
    ("data-classification", ["classif", "sensitiv", "confidential", "restricted",
                             "personal data", "pii", "cardholder"],
     "The brief does not state the maximum-sensitivity data element in scope. That "
     "single fact bounds the data, network and regulatory positions."),
    ("volumetrics", ["tps", "per second", "throughput", "volume", "gb", "tb",
                     "users", "transactions", "peak", "concurrency"],
     "The brief carries no volumetrics. Every position will be qualitative and "
     "therefore unsizeable until numbers are pinned."),
    ("resilience", ["rto", "rpo", "availability", "resilien", "disaster", "failover",
                    "impact tolerance", "uptime"],
     "The brief states no availability or recovery requirement. The resilience "
     "position is currently an assumption rather than a decision."),
    ("third-party", ["third part", "vendor", "supplier", "saas", "partner", "outsourc"],
     "The brief does not mention third parties. If any exist, materiality and exit "
     "obligations apply and are currently unassessed."),
    ("identity", ["identity", "authentic", "authoris", "authoriz", "access", "sso",
                  "iam", "credential"],
     "The brief does not describe how actors authenticate or how access is decided, "
     "which every other domain's position depends on."),
    ("logging", ["log", "monitor", "siem", "detect", "audit", "observab"],
     "The brief does not mention logging or detection. This is the domain most often "
     "shortchanged by the others, and its cost lands elsewhere."),
    ("timeline", ["date", "deadline", "timeline", "roadmap", "quarter", "phase",
                  "milestone", "go-live", "go live"],
     "The brief states no delivery timeline, so option effort cannot be assessed "
     "against a real constraint."),
]


def slugify(text: str, maxlen: int = 48) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    text = re.sub(r"-{2,}", "-", text)
    return (text[:maxlen].rstrip("-") or "untitled")


def _first_heading(brief: str) -> str:
    for line in brief.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()
    for line in brief.splitlines():
        s = line.strip()
        if s:
            return s[:120]
    return "Untitled direction"


def _sections(brief: str) -> dict[str, list[str]]:
    """Pull markdown sections into the buckets we understand."""
    out: dict[str, list[str]] = {k: [] for k in _SECTION_ALIASES}
    current: str | None = None
    for line in brief.splitlines():
        stripped = line.strip()
        heading = None
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip().lower()
        elif re.match(r"^\*\*(.+?)\*\*:?\s*$", stripped):
            heading = re.match(r"^\*\*(.+?)\*\*:?\s*$", stripped).group(1).lower()
        if heading is not None:
            heading = re.sub(r"^\d+[.)]\s*", "", heading).rstrip(":").strip()
            current = None
            for bucket, aliases in _SECTION_ALIASES.items():
                if any(heading == a or heading.startswith(a) for a in aliases):
                    current = bucket
                    break
            continue
        if current and stripped:
            item = re.sub(r"^[-*•]\s*", "", stripped)
            item = re.sub(r"^\d+[.)]\s*", "", item)
            if item and not item.startswith("|"):
                out[current].append(item)
    return out


# A signal must not fire on the phrase that rules it out. "No customer data"
# is not evidence of customer data. Cheap to check, and the false positive it
# prevents propagates all the way into the selected architecture.
_NEGATIONS = re.compile(
    r"\b(no|not|none|never|without|excludes?|excluding|exempt from|out of scope(?: for)?|"
    r"there is no|there are no|does not|do not|doesn't|don't|won't|will not)\b[^.;:]{0,28}$",
    re.IGNORECASE,
)


def _negated(brief: str, match: re.Match) -> bool:
    return bool(_NEGATIONS.search(brief[max(0, match.start() - 40):match.start()]))


def _evidence_for(brief: str, match: re.Match) -> str:
    start = max(0, match.start() - 60)
    end = min(len(brief), match.end() + 60)
    frag = brief[start:end].replace("\n", " ")
    frag = re.sub(r"\s+", " ", frag).strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(brief) else ""
    return f"{prefix}{frag}{suffix}"


def run_intake(brief: str, catalogue, title: str | None = None) -> Intake:
    defs = catalogue.signals_def
    signals: dict[str, Signal] = {}

    for key, spec in defs["signals"].items():
        hits = 0
        evidence = ""
        for pattern in spec["patterns"]:
            for m in re.finditer(pattern, brief, re.IGNORECASE):
                if _negated(brief, m):
                    continue
                hits += 1
                if not evidence:
                    evidence = _evidence_for(brief, m)
                break
        if hits:
            confidence = min(1.0, 0.55 + 0.15 * hits)
            signals[key] = Signal(key=key, value=True, confidence=round(confidence, 2),
                                  evidence=evidence)

    # Complexity tier: weighted signals plus a length bonus. A long brief that
    # says little still scores low; a short brief naming DORA, PCI and
    # multi-region still scores high.
    score = sum(defs["signals"][k]["weight_complexity"] for k in signals)
    for band in sorted(defs["tier_length_bonus"], key=lambda b: b["min_chars"]):
        if len(brief) >= band["min_chars"]:
            length_bonus = band["bonus"]
    score += length_bonus

    tier = "T1"
    for t in COMPLEXITY_TIERS:
        if score >= defs["tier_thresholds"][t]:
            tier = t
    tier_rationale = (
        f"Complexity score {score} from {len(signals)} detected signals "
        f"plus a length bonus of {length_bonus} for a {len(brief):,}-character brief. "
        f"Thresholds: " + ", ".join(f"{t}>={defs['tier_thresholds'][t]}" for t in COMPLEXITY_TIERS)
        + f". Graded {tier} ({TIER_NAMES[tier]})."
    )

    # Tier and scale become signals in their own right so options can express
    # fit against them directly.
    signals[f"tier-{tier}"] = Signal(key=f"tier-{tier}", value=True, confidence=1.0,
                                     evidence=tier_rationale, inferred=True)
    scale = "large-scale" if tier in ("T3", "T4") else "small-scale"
    signals[scale] = Signal(key=scale, value=True, confidence=0.8,
                            evidence=f"Inferred from complexity tier {tier}.", inferred=True)

    secs = _sections(brief)
    lowered = brief.lower()
    unstated = [
        text for _key, terms, text in _SILENCE_CHECKS
        if not any(t in lowered for t in terms)
    ]

    environments = secs["environments"] or ["Prod", "RTL", "Dev-Test"]

    # Capabilities the brief makes non-negotiable. These gate the option set
    # rather than merely weighting it - see catalogue/signals.json.
    mandates: dict[str, list[str]] = {}
    for key in signals:
        for cap in defs["signals"].get(key, {}).get("mandates", []):
            mandates.setdefault(cap, []).append(key)

    title = title or _first_heading(brief)
    return Intake(
        title=title,
        slug=slugify(title),
        raw_brief=brief,
        tier=tier,
        tier_rationale=tier_rationale,
        signals=signals,
        objects=secs["objects"],
        integrations=secs["integrations"],
        environments=environments,
        constraints=secs["constraints"],
        drivers=secs["drivers"],
        unstated=unstated,
        mandates=mandates,
    )
