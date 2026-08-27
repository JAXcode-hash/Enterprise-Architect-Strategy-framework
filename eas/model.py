"""Core data model for the Enterprise Architect Strategy framework.

Everything the engine reasons about is expressed with these types:

    Capability  a tag in the shared cross-domain vocabulary
    Option      one defensible position a domain can take
    Rule        a cross-domain compatibility assertion
    Signal      something the intake brief told us about the initiative
    Cell        one square of the orchestrator's N x N reconciliation matrix
    Run         a single, isolated assessment of one brief

Stdlib only, by design: a run must be reproducible on any machine with
python3 and nothing else installed.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = "1.0"

# --------------------------------------------------------------------------
# Domains
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Domain:
    key: str            # "identity-access"
    code: str           # "IAM"
    name: str           # "Identity & Access Validation"
    order: int          # gating order from the base plate framework, sec 3
    scope: str
    skill: str          # the .claude skill that owns this domain

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


# --------------------------------------------------------------------------
# Risk / anchors / questions
# --------------------------------------------------------------------------

RISK_CATEGORIES = (
    "security",       # exposure created by a configuration choice
    "timeline",       # delivery / sequencing challenge
    "workaround",     # tactical debt taken to hit a date
    "legal-reg",      # legal, regulatory or contractual
    "cost",
    "operational",    # run-cost, toil, skills
)

SEVERITIES = ("L", "M", "H", "C")          # low, medium, high, critical
_SEV_RANK = {"L": 1, "M": 2, "H": 3, "C": 4}


@dataclass
class Risk:
    id: str
    category: str
    severity: str
    statement: str
    mitigation: str = ""
    source: str = ""            # option id or rule id that raised it
    domain: str = ""
    emergent: bool = False      # True when raised by a *combination*, not one option

    @property
    def rank(self) -> int:
        return _SEV_RANK.get(self.severity, 0)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class Anchor:
    """A volumetric anchor: the number that must be pinned per environment."""
    metric: str
    unit: str
    prod: str = "UNPINNED"
    rtl: str = "UNPINNED"
    devtest: str = "UNPINNED"
    critical: bool = False      # blocks sizing if unpinned
    note: str = ""

    def unpinned_envs(self) -> list[str]:
        out = []
        for env, val in (("Prod", self.prod), ("RTL", self.rtl), ("Dev-Test", self.devtest)):
            if not val or str(val).strip().upper() == "UNPINNED":
                out.append(env)
        return out

    def is_unpinned(self) -> bool:
        return bool(self.unpinned_envs())

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["unpinned_envs"] = self.unpinned_envs()
        return d


@dataclass
class Question:
    id: str
    question: str
    owner_role: str = "TBC"
    blocking: bool = False
    domain: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


# --------------------------------------------------------------------------
# Options
# --------------------------------------------------------------------------

POSTURES = ("tactical", "balanced", "strategic")
BANDS = ("XS", "S", "M", "L", "XL")
_BAND_RANK = {"XS": 1, "S": 2, "M": 3, "L": 4, "XL": 5}


@dataclass
class Option:
    """One defensible position a domain can take.

    An option is not a recommendation on its own. It carries what it *gives*
    the rest of the estate (`provides`) and what it *needs back* (`requires`),
    which is what lets the orchestrator interrogate it against every other
    domain's chosen position.
    """
    id: str
    domain: str
    name: str
    summary: str
    posture: str = "balanced"

    provides: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)   # hard option-id conflicts

    fit: dict[str, float] = field(default_factory=dict)  # signal -> weight
    effort_weeks: int = 0
    effort_band: str = "M"
    cost_band: str = "M"
    security_score: int = 3        # 1..5, higher = stronger posture
    reg_score: int = 3             # 1..5, higher = easier to evidence
    ops_burden: int = 3            # 1..5, higher = more run toil

    risks: list[Risk] = field(default_factory=list)
    anchors: list[Anchor] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    lld_notes: list[str] = field(default_factory=list)
    hld_notes: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)

    # populated by the selector at run time
    score: float = 0.0
    score_breakdown: dict[str, float] = field(default_factory=dict)
    rank: int = 0

    @property
    def effort_rank(self) -> int:
        return _BAND_RANK.get(self.effort_band, 3)

    @property
    def cost_rank(self) -> int:
        return _BAND_RANK.get(self.cost_band, 3)

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["effort_rank"] = self.effort_rank
        d["cost_rank"] = self.cost_rank
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any], domain: str) -> "Option":
        risks = [
            Risk(
                id=r.get("id") or f"{raw['id']}-R{i + 1}",
                category=r["category"],
                severity=r.get("severity", "M"),
                statement=r["statement"],
                mitigation=r.get("mitigation", ""),
                source=raw["id"],
                domain=domain,
            )
            for i, r in enumerate(raw.get("risks", []))
        ]
        anchors = [
            Anchor(
                metric=a["metric"],
                unit=a.get("unit", ""),
                prod=a.get("prod", "UNPINNED"),
                rtl=a.get("rtl", "UNPINNED"),
                devtest=a.get("devtest", "UNPINNED"),
                critical=bool(a.get("critical", False)),
                note=a.get("note", ""),
            )
            for a in raw.get("anchors", [])
        ]
        questions = [
            Question(
                id=q.get("id") or f"{raw['id']}-Q{i + 1}",
                question=q["question"],
                owner_role=q.get("owner_role", "TBC"),
                blocking=bool(q.get("blocking", False)),
                domain=domain,
                source=raw["id"],
            )
            for i, q in enumerate(raw.get("questions", []))
        ]
        return cls(
            id=raw["id"],
            domain=domain,
            name=raw["name"],
            summary=raw["summary"],
            posture=raw.get("posture", "balanced"),
            provides=list(raw.get("provides", [])),
            requires=list(raw.get("requires", [])),
            conflicts=list(raw.get("conflicts", [])),
            fit=dict(raw.get("fit", {})),
            effort_weeks=int(raw.get("effort_weeks", 0)),
            effort_band=raw.get("effort_band", "M"),
            cost_band=raw.get("cost_band", "M"),
            security_score=int(raw.get("security_score", 3)),
            reg_score=int(raw.get("reg_score", 3)),
            ops_burden=int(raw.get("ops_burden", 3)),
            risks=risks,
            anchors=anchors,
            checklist=list(raw.get("checklist", [])),
            questions=questions,
            controls=list(raw.get("controls", [])),
            lld_notes=list(raw.get("lld_notes", [])),
            hld_notes=list(raw.get("hld_notes", [])),
            references=list(raw.get("references", [])),
        )


# --------------------------------------------------------------------------
# Cross-domain compatibility rules
# --------------------------------------------------------------------------

RULE_KINDS = (
    "mutex",              # two selected options are incompatible
    "requires-option",    # option A requires option B specifically
    "emergent-risk",      # a *combination* creates a risk neither option owns
    "anchor-required",    # a selection makes an anchor sizing-critical
    "question-raised",    # a combination raises a further-questioning item
    "capability-gap",     # a selection needs a capability nobody provides
)

CELL_STATES = ("satisfied", "contradiction", "gap", "unpinned", "not-applicable")


@dataclass
class Rule:
    id: str
    kind: str
    message: str
    severity: str = "M"
    when_all: list[str] = field(default_factory=list)   # option ids all selected
    when_any: list[str] = field(default_factory=list)
    capability: str = ""
    then_option: str = ""
    anchor_metrics: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)    # matrix cell(s) this lands in
    resolution: str = ""
    risk: Risk | None = None
    question: Question | None = None

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Rule":
        risk = None
        if raw.get("risk"):
            r = raw["risk"]
            risk = Risk(
                id=r.get("id") or f"{raw['id']}-R",
                category=r["category"],
                severity=r.get("severity", "M"),
                statement=r["statement"],
                mitigation=r.get("mitigation", ""),
                source=raw["id"],
                domain=(raw.get("domains") or [""])[0],
                emergent=True,
            )
        question = None
        if raw.get("question"):
            q = raw["question"]
            question = Question(
                id=q.get("id") or f"{raw['id']}-Q",
                question=q["question"],
                owner_role=q.get("owner_role", "TBC"),
                blocking=bool(q.get("blocking", False)),
                domain=(raw.get("domains") or [""])[0],
                source=raw["id"],
            )
        return cls(
            id=raw["id"],
            kind=raw["kind"],
            message=raw["message"],
            severity=raw.get("severity", "M"),
            when_all=list(raw.get("when_all", [])),
            when_any=list(raw.get("when_any", [])),
            capability=raw.get("capability", ""),
            then_option=raw.get("then_option", ""),
            anchor_metrics=([raw["anchor_metric"]] if isinstance(raw.get("anchor_metric"), str)
                            and raw.get("anchor_metric") else list(raw.get("anchor_metric", []))),
            domains=list(raw.get("domains", [])),
            resolution=raw.get("resolution", ""),
            risk=risk,
            question=question,
        )


# --------------------------------------------------------------------------
# Intake
# --------------------------------------------------------------------------

@dataclass
class Signal:
    """Something the brief told us, with the evidence that it did."""
    key: str
    value: bool | str | float
    confidence: float           # 0..1
    evidence: str               # the phrase in the brief that fired it
    inferred: bool = False      # True when defaulted rather than found

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


COMPLEXITY_TIERS = ("T1", "T2", "T3", "T4")
TIER_NAMES = {
    "T1": "Contained change",
    "T2": "Programme workstream",
    "T3": "Multi-domain programme",
    "T4": "Estate-level strategic programme",
}


@dataclass
class Intake:
    title: str
    slug: str
    raw_brief: str
    tier: str = "T2"
    tier_rationale: str = ""
    signals: dict[str, Signal] = field(default_factory=dict)
    objects: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)
    environments: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    drivers: list[str] = field(default_factory=list)
    unstated: list[str] = field(default_factory=list)   # what the brief did NOT say
    # capability -> the signals that made it non-negotiable
    mandates: dict[str, list[str]] = field(default_factory=dict)

    def signal_on(self, key: str) -> bool:
        s = self.signals.get(key)
        return bool(s and s.value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "slug": self.slug,
            "tier": self.tier,
            "tier_name": TIER_NAMES.get(self.tier, ""),
            "tier_rationale": self.tier_rationale,
            "signals": {k: v.to_dict() for k, v in self.signals.items()},
            "objects": self.objects,
            "integrations": self.integrations,
            "environments": self.environments,
            "constraints": self.constraints,
            "drivers": self.drivers,
            "unstated": self.unstated,
            "mandates": self.mandates,
            "brief_sha256": hashlib.sha256(self.raw_brief.encode("utf-8")).hexdigest(),
            "brief_chars": len(self.raw_brief),
        }


# --------------------------------------------------------------------------
# Orchestration output
# --------------------------------------------------------------------------

@dataclass
class Cell:
    """One square of the N x N integration matrix."""
    row: str            # domain code that imposes
    col: str            # domain code that receives
    state: str
    detail: str
    capability: str = ""
    rule_id: str = ""
    severity: str = "M"

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class Decision:
    """Decision-ledger entry (framework sec 4.4, dual ledger)."""
    id: str
    domain: str
    position: str
    option_id: str
    rationale: str
    environments: str = "Prod / RTL / Dev-Test"
    owner: str = "TBC"
    superseded_by: str = ""
    status: str = "proposed"

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class Evidence:
    """Evidence / audit ledger entry (framework sec 4.4)."""
    id: str
    checked: str
    method: str
    result: str
    anchor: str = ""
    source: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


VERDICTS = ("stable", "conditional", "not-yet")
VERDICT_LABELS = {
    "stable": "Stable",
    "conditional": "Conditional",
    "not-yet": "Not yet a base plate",
}


@dataclass
class Reconciliation:
    verdict: str
    verdict_rationale: str
    cells: list[Cell] = field(default_factory=list)
    contradictions: list[Cell] = field(default_factory=list)
    gaps: list[Cell] = field(default_factory=list)
    unpinned: list[Anchor] = field(default_factory=list)
    emergent_risks: list[Risk] = field(default_factory=list)
    emergent_questions: list[Question] = field(default_factory=list)
    repairs: list[dict[str, Any]] = field(default_factory=list)
    coverage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "verdict_label": VERDICT_LABELS.get(self.verdict, self.verdict),
            "verdict_rationale": self.verdict_rationale,
            "cells": [c.to_dict() for c in self.cells],
            "contradictions": [c.to_dict() for c in self.contradictions],
            "gaps": [c.to_dict() for c in self.gaps],
            "unpinned": [a.to_dict() for a in self.unpinned],
            "emergent_risks": [r.to_dict() for r in self.emergent_risks],
            "emergent_questions": [q.to_dict() for q in self.emergent_questions],
            "repairs": self.repairs,
            "coverage": self.coverage,
        }


def json_default(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    raise TypeError(f"not JSON serialisable: {type(obj)!r}")


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=json_default, sort_keys=False)
