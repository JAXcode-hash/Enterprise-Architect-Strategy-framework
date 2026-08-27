"""Project isolation.

Every request creates its own project directory holding its own brief, its own
inputs, its own outputs and its own registers. Nothing is read from another
project and nothing is written outside the project's own root, so two runs can
never cross-pollinate.

The manifest records a fingerprint of the catalogue that produced the run, so a
later phase can tell whether two projects were assessed against the same
framework version before it attempts to compare their strategies.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

ENGINE_VERSION = "1.0.0"
PROJECTS_DIRNAME = "projects"

_SUBDIRS = (
    "inputs",
    "options",
    "outputs/lld",
    "registers",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def projects_root(root: Path | None = None) -> Path:
    return (root or repo_root()) / PROJECTS_DIRNAME


def catalogue_fingerprint(catalogue_dir: Path) -> str:
    """Stable hash over every catalogue file, so runs are comparable or not."""
    h = hashlib.sha256()
    for path in sorted(Path(catalogue_dir).rglob("*.json")):
        h.update(path.relative_to(catalogue_dir).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()[:16]


def _unique_id(slug: str, root: Path) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    base = f"{slug}-{stamp}"
    candidate = base
    n = 2
    while (root / candidate).exists():
        candidate = f"{base}-{n:02d}"
        n += 1
    return candidate


class Project:
    """One isolated assessment. All paths are confined beneath `self.root`."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    # -- lifecycle --------------------------------------------------------

    @classmethod
    def create(cls, slug: str, title: str, brief: str, catalogue_dir: Path,
               base: Path | None = None) -> "Project":
        base = base or projects_root()
        base.mkdir(parents=True, exist_ok=True)
        pid = _unique_id(slug, base)
        root = base / pid
        root.mkdir()
        for sub in _SUBDIRS:
            (root / sub).mkdir(parents=True, exist_ok=True)
        proj = cls(root)
        proj.write("brief.md", brief)
        proj.write_json("project.json", {
            "id": pid,
            "title": title,
            "slug": slug,
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "engine_version": ENGINE_VERSION,
            "catalogue_fingerprint": catalogue_fingerprint(catalogue_dir),
            "brief_sha256": hashlib.sha256(brief.encode("utf-8")).hexdigest(),
            "isolation": (
                "This project reads and writes only within its own directory. No other "
                "project's brief, options, decisions or registers influence this run."
            ),
            "runs": [],
        })
        proj.write_json("inputs/overrides.json", {
            "_note": (
                "Fix a domain to a specific option id, e.g. {\"data-security\": \"DATA-03\"}. "
                "The orchestrator will never overrule a fixed domain - it routes repairs "
                "through the others and reports what it could not reconcile."
            )
        })
        proj.write_json("inputs/anchors.json", {
            "_note": (
                "Pin volumetric anchors per environment as they land, e.g. "
                "{\"secops\": {\"Type 2 compliance log volume\": {\"prod\": \"420 GB/day\", "
                "\"rtl\": \"40 GB/day\", \"devtest\": \"5 GB/day\"}}}. Re-run to move the "
                "verdict on."
            )
        })
        return proj

    @classmethod
    def open(cls, identifier: str, base: Path | None = None) -> "Project":
        base = base or projects_root()
        root = base / identifier
        if not (root / "project.json").is_file():
            raise FileNotFoundError(f"no project '{identifier}' under {base}")
        return cls(root)

    @staticmethod
    def list_all(base: Path | None = None) -> list[dict]:
        base = base or projects_root()
        if not base.is_dir():
            return []
        out = []
        for child in sorted(base.iterdir(), reverse=True):
            manifest = child / "project.json"
            if manifest.is_file():
                try:
                    out.append(json.loads(manifest.read_text(encoding="utf-8")))
                except json.JSONDecodeError:
                    continue
        return out

    # -- confined IO ------------------------------------------------------

    def path(self, rel: str) -> Path:
        """Resolve a path inside the project, refusing anything that escapes it."""
        if os.path.isabs(rel) or ".." in Path(rel).parts:
            raise ValueError(f"path escapes project isolation: {rel!r}")
        target = (self.root / rel).resolve()
        if not str(target).startswith(str(self.root) + os.sep) and target != self.root:
            raise ValueError(f"path escapes project isolation: {rel!r}")
        return target

    def write(self, rel: str, content: str) -> Path:
        p = self.path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def write_json(self, rel: str, obj) -> Path:
        return self.write(rel, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")

    def read(self, rel: str, default: str = "") -> str:
        p = self.path(rel)
        return p.read_text(encoding="utf-8") if p.is_file() else default

    def read_json(self, rel: str, default=None):
        raw = self.read(rel)
        if not raw.strip():
            return default
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return default
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if not k.startswith("_")}
        return data

    @property
    def manifest(self) -> dict:
        return self.read_json("project.json", {}) or {}

    @property
    def id(self) -> str:
        return self.manifest.get("id", self.root.name)

    def record_run(self, verdict: str, summary: dict) -> None:
        m = self.manifest
        m.setdefault("runs", []).append({
            "at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "verdict": verdict,
            "summary": summary,
        })
        m["latest_verdict"] = verdict
        self.write_json("project.json", m)

    def files(self) -> list[str]:
        out = []
        for p in sorted(self.root.rglob("*")):
            if p.is_file():
                out.append(p.relative_to(self.root).as_posix())
        return out
