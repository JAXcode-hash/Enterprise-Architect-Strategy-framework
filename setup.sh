#!/usr/bin/env bash
#
# Enterprise Architect Strategy - setup and verification.
#
# The framework itself has no dependencies. That is a design rule, not an
# accident: it has to run behind a corporate proxy on a locked-down laptop.
# So the default run installs nothing - it proves the framework works on the
# Python you already have.
#
# The optional extras exist only to regenerate the setup document. You do not
# need them to run an assessment.
#
#   ./setup.sh                verify the framework runs (installs nothing)
#   ./setup.sh --docs         also install the document-generation extras
#   ./setup.sh --all          both of the above
#   ./setup.sh --check        verify only, never install, exit non-zero on a problem
#   ./setup.sh --venv         put the optional pip extras in ./.venv
#   ./setup.sh --help
#
set -euo pipefail

MIN_MAJOR=3
MIN_MINOR=9
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

WANT_DOCS=0
CHECK_ONLY=0
USE_VENV=0

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  R=$'\033[31m'; G=$'\033[32m'; Y=$'\033[33m'; B=$'\033[1m'; D=$'\033[2m'; X=$'\033[0m'
else
  R=""; G=""; Y=""; B=""; D=""; X=""
fi

ok()   { printf '  %s✓%s %s\n' "$G" "$X" "$1"; }
warn() { printf '  %s!%s %s\n' "$Y" "$X" "$1"; }
bad()  { printf '  %s✗%s %s\n' "$R" "$X" "$1"; }
step() { printf '\n%s%s%s\n' "$B" "$1" "$X"; }
hint() { printf '    %s%s%s\n' "$D" "$1" "$X"; }

usage() { sed -n '3,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0; }

while [ $# -gt 0 ]; do
  case "$1" in
    --docs)  WANT_DOCS=1 ;;
    --all)   WANT_DOCS=1 ;;
    --check) CHECK_ONLY=1 ;;
    --venv)  USE_VENV=1; WANT_DOCS=1 ;;
    -h|--help) usage ;;
    *) bad "unknown option: $1"; echo; usage ;;
  esac
  shift
done

printf '%sEnterprise Architect Strategy - setup%s\n' "$B" "$X"
printf '%s%s%s\n' "$D" "$ROOT" "$X"

# ---------------------------------------------------------------------------
# 1. Python
# ---------------------------------------------------------------------------
step "1. Python"

PY=""
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= ('"$MIN_MAJOR"','"$MIN_MINOR"') else 1)' 2>/dev/null; then
      PY="$candidate"
      break
    fi
  fi
done

if [ -z "$PY" ]; then
  bad "no Python ${MIN_MAJOR}.${MIN_MINOR} or later found on PATH"
  hint "The framework needs only the standard library, but it needs a recent one:"
  hint "Path.is_relative_to and PEP 585 generics both arrived in 3.9."
  for candidate in python3 python py; do
    if command -v "$candidate" >/dev/null 2>&1; then
      hint "found $candidate = $("$candidate" --version 2>&1 | head -1)"
    fi
  done
  exit 1
fi

PYVER="$("$PY" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
ok "$PY $PYVER (need ${MIN_MAJOR}.${MIN_MINOR}+)"

# ---------------------------------------------------------------------------
# 2. Core dependencies - there are none, and that is the point
# ---------------------------------------------------------------------------
step "2. Core dependencies"

MISSING="$("$PY" - <<'PYEOF'
import importlib.util, sys
# Every module the engine imports. All standard library - if any of these is
# missing the Python install itself is broken, not the framework.
mods = ["argparse", "copy", "csv", "dataclasses", "datetime", "hashlib", "html",
        "http.server", "io", "json", "mimetypes", "os", "pathlib", "re", "shutil",
        "sys", "tempfile", "time", "traceback", "typing", "unicodedata",
        "unittest", "urllib.parse"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
print(" ".join(missing))
PYEOF
)"

if [ -n "$MISSING" ]; then
  bad "standard library modules missing: $MISSING"
  hint "This Python install is incomplete. On Debian/Ubuntu try: apt install python3-full"
  exit 1
fi
ok "all 23 required modules present - every one is standard library"
ok "nothing to install for the framework itself"

# ---------------------------------------------------------------------------
# 3. Prove it works
# ---------------------------------------------------------------------------
step "3. Verification"

if "$PY" -m eas lint >/dev/null 2>&1; then
  ok "catalogue is coherent"
else
  bad "catalogue lint failed"
  hint "run '$PY -m eas lint' to see why"
  exit 1
fi

TEST_OUT="$("$PY" -m unittest discover tests 2>&1 | tail -3)"
if printf '%s' "$TEST_OUT" | grep -q '^OK$'; then
  ok "$(printf '%s' "$TEST_OUT" | grep -oE 'Ran [0-9]+ tests? in [0-9.]+s' | head -1), all passing"
else
  bad "test suite failed"
  printf '%s\n' "$TEST_OUT"
  exit 1
fi

COUNTS="$("$PY" - <<'PYEOF'
import json, sys, pathlib
sys.path.insert(0, ".")
from eas.catalogue import Catalogue
c = Catalogue()
s = c.summary()
agents = len(list(pathlib.Path(".claude/agents").glob("*.md")))
skills = len(list(pathlib.Path(".claude/skills").glob("*/SKILL.md")))
print(f"{s['domains']} domains, {s['options']} options, {s['capabilities']} capabilities, "
      f"{s['rules']} rules, {s['signals']} signals")
print(f"{agents} agents, {skills} skills")
PYEOF
)"
ok "$(printf '%s' "$COUNTS" | sed -n 1p)"
ok "$(printf '%s' "$COUNTS" | sed -n 2p)"

# ---------------------------------------------------------------------------
# 4. Optional extras
# ---------------------------------------------------------------------------
if [ "$WANT_DOCS" -eq 1 ] && [ "$CHECK_ONLY" -eq 0 ]; then
  step "4. Optional extras (document generation only)"
  hint "These are needed only to rebuild docs/eas-setup-and-flow.docx."
  hint "An assessment run needs none of them."

  # -- npm: the docx builder ------------------------------------------------
  if command -v npm >/dev/null 2>&1; then
    if node -e "require('docx')" >/dev/null 2>&1; then
      ok "npm 'docx' already available"
    else
      printf '    installing npm docx ...\n'
      if npm install --silent --no-audit --no-fund >/dev/null 2>&1; then
        ok "npm 'docx' installed"
      else
        warn "npm install failed - the document generator will not run"
        hint "behind a proxy? npm config set proxy \$HTTP_PROXY https-proxy \$HTTPS_PROXY"
      fi
    fi
  else
    warn "npm not found - skipping the document generator"
    hint "everything else works without it"
  fi

  # -- pip: the docx schema validator --------------------------------------
  PIP_TARGET=""
  if [ "$USE_VENV" -eq 1 ]; then
    if [ ! -d .venv ]; then
      "$PY" -m venv .venv >/dev/null 2>&1 && ok "created ./.venv" \
        || { warn "could not create ./.venv"; USE_VENV=0; }
    else
      ok "using existing ./.venv"
    fi
    [ "$USE_VENV" -eq 1 ] && PY_PIP=".venv/bin/python"
  fi
  if [ "${USE_VENV:-0}" -ne 1 ]; then
    PY_PIP="$PY"
    # Outside a venv, keep out of the system site-packages.
    [ -z "${VIRTUAL_ENV:-}" ] && PIP_TARGET="--user"
  fi

  if "$PY_PIP" -c "import lxml, defusedxml" >/dev/null 2>&1; then
    ok "python validator extras already available"
  else
    printf '    installing lxml and defusedxml ...\n'
    if "$PY_PIP" -m pip install --quiet --disable-pip-version-check $PIP_TARGET \
         -r requirements-dev.txt >/dev/null 2>&1; then
      ok "python validator extras installed"
    else
      warn "pip install failed - docx schema validation will not run"
      hint "behind a proxy? pip install --proxy \$HTTPS_PROXY -r requirements-dev.txt"
    fi
  fi

  # -- things we cannot install --------------------------------------------
  command -v soffice  >/dev/null 2>&1 && ok "LibreOffice present (docx to PDF rendering)" \
                                       || warn "LibreOffice not found - cannot render docx to PDF"
  command -v pandoc   >/dev/null 2>&1 && ok "pandoc present (docx text extraction)" \
                                       || warn "pandoc not found - cannot extract docx text"
elif [ "$WANT_DOCS" -eq 1 ]; then
  step "4. Optional extras"
  hint "--check given, so nothing was installed"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
step "Ready"
cat <<EOF
    $PY -m eas new --brief briefs/example-regulated.md    assess a direction
    $PY -m eas serve                                       browser UI on :8000
    $PY -m eas catalogue                                   every domain and option
    $PY -m eas list                                        your projects

    Briefs to try: briefs/example-simple.md, example-regulated.md,
                   example-strategic.md, example-sase-migration.md,
                   example-agentic-sdlc.md
EOF
if [ "$WANT_DOCS" -eq 0 ] && [ "$CHECK_ONLY" -eq 0 ]; then
  printf '\n%s    Only rebuilding the setup document? ./setup.sh --docs%s\n' "$D" "$X"
fi
printf '\n'
