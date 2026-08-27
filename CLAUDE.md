# Enterprise Architect Strategy — working notes

Read `README.md` first for what this is. This file is for changing it.

## How a run works

`python3 -m eas new --brief <path>` →
intake (brief → evidenced signals + complexity tier + mandates) →
fan-out (nine domains rank their options) →
fan-in (orchestrator repairs, reconciles, grades) →
render (9 LLDs, HLD, exec pack, base plate, registers, dashboard).

Everything lands in one isolated `projects/<slug>-<date>/`.

## Environment definitions

Every checklist item and every volumetric anchor is asserted three times:

- **Prod** — live service.
- **RTL** — route-to-live. First-class, not prod-lite: its own connectivity, its own
  data-handling rules, its own volumetric profile. The highest-value question the framework
  forces is what real or quasi-real data touches non-prod, and under what control.
- **Dev-Test** — development and functional test.

## Type 1 / Type 2 logging

- **Type 1** — security-relevant and audit logging: identity, access, control-plane and
  detection events, for SIEM/SOC, forensics and regulatory retention.
- **Type 2** — operational and observability logging: application and infrastructure telemetry,
  health, performance.

If your organisation uses a different taxonomy, rebind these two definitions in
`catalogue/options/secops.json` and the rest of the framework follows unchanged.

## Rules that keep the framework honest

1. **The catalogue is data.** Domain expertise lives in `catalogue/`, never in `eas/`. If you
   find yourself hard-coding an option id or a control reference in the engine, it belongs in
   the catalogue instead.
2. **Every `requires` must be satisfiable.** An option requiring a capability nothing provides
   is a catalogue bug, not a run finding. `python3 -m eas lint` refuses it.
3. **Do not over-claim in `provides`.** An option provides a capability only if it genuinely
   delivers it. Tokenisation says nothing about jurisdiction; enumerating cross-boundary flows
   is not the same as constraining them. Over-claiming silently satisfies mandates that are
   not actually met, which is the worst failure this framework can have.
4. **Scores stay decomposable.** Every point traces to a named signal and the phrase that fired
   it. Never add a score component that cannot be explained in one line in the evidence ledger.
5. **Never invent a volumetric.** An unpinned anchor is a finding. A guessed one propagates
   into sizing and cost and is much harder to catch later.
6. **Reconciliation is deterministic.** Same catalogue, brief, overrides and pins, same base
   plate. No randomness, no wall-clock dependence in the engine.
7. **Isolation is absolute.** A run reads only its own project. `Project.path()` refuses
   escapes rather than resolving them.
8. **Stdlib only.** The framework has to run behind a corporate proxy on a locked-down laptop.
   No dependencies, and the generated dashboard makes no network requests.

## Changing the catalogue

```bash
$EDITOR catalogue/options/<domain>.json
python3 -m eas lint                 # must be clean
python3 tools/gen_skills.py         # regenerate the nine validator skills
python3 -m unittest discover tests  # 42 tests
```

The validator `SKILL.md` files are **generated**. Edit the catalogue, not the skills —
hand edits are overwritten. `orchestrate-baseplate` and `eas-baseplate` are hand-written and
are not touched by the generator.

## Adding a domain option

An option is a full posture bundle, not a feature. It needs all of:

- `provides` / `requires` from the shared vocabulary in `catalogue/capabilities.json`
- `fit` weights against signals that exist in `catalogue/signals.json`
- effort, cost, security, regulatory and operational-burden scores
- a checklist, further-questioning items with owners, volumetric anchors, and risks

Risks carry a category — `security`, `timeline`, `workaround`, `legal-reg`, `cost`,
`operational` — because the exec pack groups by the kind of problem a risk creates for the
programme, not by which domain raised it.

## Adding a cross-domain rule

`catalogue/compat.json`. Five kinds:

| Kind | Use it when |
|---|---|
| `mutex` | Two positions genuinely cannot both hold. Include a `resolution`. |
| `emergent-risk` | A risk exists only because of a combination, and no single domain owns it. |
| `anchor-required` | One domain's choice makes *another* domain's anchor sizing-critical. |
| `question-raised` | A question only arises once two positions are read together. |
| `requires-option` | One option specifically needs another. Prefer capabilities where you can. |

Prefer expressing a dependency as a capability in `requires` — the engine derives those
automatically and they survive new options being added. Reserve explicit rules for what
capabilities cannot express.

## Modifying the orchestrator

`eas/orchestrator.py`. The repair loop is single-swap local search with a bounded pair-swap
fallback for plateaus that need two coordinated moves. If you change the search, keep it
deterministic and keep every substitution recorded with what it addressed and what it cost —
"the domain wanted X and the estate needs Y" is exactly the decision that gets challenged.

## Phase 2 — not yet built

Cross-project conflict detection. Each project already records a `catalogue_fingerprint`, which
is the prerequisite: two projects can only be compared meaningfully if they were assessed
against the same framework version. Deliberately out of scope for now — this phase is about
making a single assessment defensible.
