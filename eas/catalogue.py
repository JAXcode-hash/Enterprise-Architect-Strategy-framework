"""Catalogue loading and linting.

The catalogue is the framework's content: domains, the shared capability
vocabulary, one option file per domain, and the cross-domain rules. It is
data, not code, so a domain expert can extend it without touching the engine.

`lint()` is the guard that keeps it coherent - an option that requires a
capability nothing provides is a catalogue bug that would otherwise surface
as an unfixable run finding.
"""

from __future__ import annotations

import json
from pathlib import Path

from .model import Domain, Option, Rule

DEFAULT_CATALOGUE = Path(__file__).resolve().parent.parent / "catalogue"


class CatalogueError(Exception):
    pass


class Catalogue:
    def __init__(self, root: Path | str = DEFAULT_CATALOGUE):
        self.root = Path(root)
        if not self.root.is_dir():
            raise CatalogueError(f"catalogue directory not found: {self.root}")
        self.domains: list[Domain] = []
        self.options: list[Option] = []
        self.rules: list[Rule] = []
        self.capabilities: dict[str, dict] = {}
        self.implies: dict[str, list[str]] = {}
        self.signals_def: dict = {}
        self._load()

    # -- loading ----------------------------------------------------------

    def _read(self, name: str) -> dict:
        p = self.root / name
        if not p.is_file():
            raise CatalogueError(f"missing catalogue file: {p}")
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CatalogueError(f"{p}: {e}") from e

    def _load(self) -> None:
        self.domains = [Domain(**d) for d in self._read("domains.json")["domains"]]
        caps = self._read("capabilities.json")
        self.capabilities = caps["capabilities"]
        self.implies = caps.get("implies", {})
        self.signals_def = self._read("signals.json")

        for dom in self.domains:
            raw = self._read(f"options/{dom.key}.json")
            if raw.get("domain") != dom.key:
                raise CatalogueError(
                    f"options/{dom.key}.json declares domain {raw.get('domain')!r}"
                )
            for o in raw["options"]:
                self.options.append(Option.from_dict(o, dom.key))

        self.rules = [Rule.from_dict(r) for r in self._read("compat.json")["rules"]]

    # -- lookups ----------------------------------------------------------

    def domain(self, key: str) -> Domain:
        for d in self.domains:
            if d.key == key or d.code == key:
                return d
        raise KeyError(key)

    def domain_keys(self) -> list[str]:
        return [d.key for d in sorted(self.domains, key=lambda x: x.order)]

    def code_for(self, domain_key: str) -> str:
        return self.domain(domain_key).code

    def option(self, option_id: str) -> Option:
        for o in self.options:
            if o.id == option_id:
                return o
        raise KeyError(option_id)

    def options_for(self, domain_key: str) -> list[Option]:
        return [o for o in self.options if o.domain == domain_key]

    def providers_of(self, capability: str) -> list[Option]:
        return [o for o in self.options if capability in self.expand(o.provides)]

    def expand(self, provided: list[str]) -> set[str]:
        """Expand a provides list through the implication map.

        A stronger position satisfies a weaker requirement; without this the
        orchestrator would raise a contradiction between two positions that
        actually agree.
        """
        out: set[str] = set(provided)
        frontier = list(provided)
        while frontier:
            cap = frontier.pop()
            for weaker in self.implies.get(cap, []):
                if weaker not in out:
                    out.add(weaker)
                    frontier.append(weaker)
        return out

    # -- linting ----------------------------------------------------------

    def lint(self) -> list[str]:
        """Return a list of catalogue problems. Empty list means healthy."""
        problems: list[str] = []
        known_caps = set(self.capabilities)
        ids = [o.id for o in self.options]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            problems.append(f"duplicate option ids: {sorted(dupes)}")

        all_provided: set[str] = set()
        for o in self.options:
            all_provided |= self.expand(o.provides)

        for o in self.options:
            for cap in o.provides:
                if cap not in known_caps:
                    problems.append(f"{o.id}: provides unknown capability {cap!r}")
            for cap in o.requires:
                if cap not in known_caps:
                    problems.append(f"{o.id}: requires unknown capability {cap!r}")
                elif cap not in all_provided:
                    problems.append(
                        f"{o.id}: requires {cap!r} which no option in the catalogue provides"
                    )
            for cap in o.requires:
                if cap in self.expand(o.provides):
                    problems.append(f"{o.id}: requires {cap!r} from itself")
            for other in o.conflicts:
                if other not in ids:
                    problems.append(f"{o.id}: conflicts with unknown option {other!r}")
            if o.posture not in ("tactical", "balanced", "strategic"):
                problems.append(f"{o.id}: unknown posture {o.posture!r}")

        known_signals = set(self.signals_def["signals"]) | {
            f"tier-{t}" for t in ("T1", "T2", "T3", "T4")
        } | {"large-scale", "small-scale"}
        for o in self.options:
            for sig in o.fit:
                if sig not in known_signals:
                    problems.append(f"{o.id}: fit references unknown signal {sig!r}")

        for dom in self.domains:
            if not self.options_for(dom.key):
                problems.append(f"domain {dom.key} has no options")

        for r in self.rules:
            for oid in r.when_all + r.when_any + ([r.then_option] if r.then_option else []):
                if oid not in ids:
                    problems.append(f"{r.id}: references unknown option {oid!r}")
            if r.kind not in (
                "mutex", "requires-option", "emergent-risk",
                "anchor-required", "question-raised", "capability-gap",
            ):
                problems.append(f"{r.id}: unknown rule kind {r.kind!r}")
            if r.capability and r.capability not in known_caps:
                problems.append(f"{r.id}: unknown capability {r.capability!r}")

        return problems

    def summary(self) -> dict:
        return {
            "domains": len(self.domains),
            "options": len(self.options),
            "capabilities": len(self.capabilities),
            "rules": len(self.rules),
            "signals": len(self.signals_def["signals"]),
            "options_per_domain": {d.key: len(self.options_for(d.key)) for d in self.domains},
        }
