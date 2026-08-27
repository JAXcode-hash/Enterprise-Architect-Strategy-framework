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

## Log types — the organisation's operating model

Three types, each owned by a different function. The ownership is the point: it decides who is
obliged to do what, and the framework encodes that rather than a taxonomy of log content.

### Type 1 — Security Event Detection and Handling

Owned by the **central security monitoring function**. That function determines which logs are
required for threat detection and threat hunting, based on ongoing threat modelling and risk
assessment. **Requirements are dynamic** and evolve with the threat landscape.

Technology and application owners are **not required to proactively implement** logging and
forwarding for Type 1. They are engaged when a specific source is required, and must then
deliver it using approved security logging ingestion patterns. The monitoring function
maintains a documented, current log requirements register and the operational processes to
communicate changes to technology owners in a timely manner.

### Type 2 — Security Compliance Reporting

Owned by the **security governance and compliance function**. That function determines which
logs satisfy regulatory, audit and security compliance obligations, and ensures appropriate
retention is configured within the enterprise compliance logging platform. Technology owners
may be engaged when a source is required, or a change activity may trigger a security review
that assesses compliance logging requirements. Either way, technology teams comply with the
defined ingestion standards and logging patterns.

### Type 3 — General and Operational Logging

The **technology owner's** responsibility. Anything outside Type 1 and Type 2 is outside the
central security functions' remit. Technology owners implement logging and retention
appropriate to their operational, observability and local monitoring needs. There is no
centrally mandated requirement and no centrally provided infrastructure for Type 3.

### What this means for the framework

The key consequence: **a technology team has no obligation to implement logging and retention
for a source neither central function has identified as in scope.** This resolves the conflict
between legacy logging requirements and the target operating model.

Two things follow, and both are encoded:

1. **No brief can mandate Type 1.** `catalogue/signals.json` mandates `secops.log.type2` and
   `secops.ingestion.compatible` where the context demands them, and never `secops.log.type1` —
   only the monitoring function decides that. A domain option may not `require`
   `secops.log.type1` either. What a domain can legitimately require is a compliance obligation
   (`secops.log.type2`) or readiness for a future engagement
   (`secops.ingestion.compatible`). There is a test asserting this.
2. **Ingestion compatibility is the load-bearing design property.** Because requirements are
   dynamic, the architectural question is not "what do we log" but "what does it cost when the
   monitoring function asks". Teams should design pipelines that can adopt the approved
   ingestion standards — format, transport, authentication, integration pattern — even when the
   system is not currently connected. `secops.ingestion.compatible` is that property, and the
   anchor `Estimated effort to connect a newly requested source` is what makes the rework cost
   arguable rather than rhetorical.

The SecOps options are postures toward this model, not volumes of logging:

| Option | Posture |
|---|---|
| `SEC-01` | Engagement-driven, no ingestion compatibility. Consistent with the model, maximum retrofit. |
| `SEC-02` | Ingestion-compatible by design, delivery on engagement. The sensible default. |
| `SEC-03` | Type 2 connected at go-live; Type 1 still engagement-driven. |
| `SEC-04` | Type 1 and Type 2 both delivered; monitoring function engaged during design. |
| `SEC-05` | Embedded detection partnership with automated response. |

If your organisation revises these definitions, rebind them in
`catalogue/capabilities.json` (the `secops.*` entries) and
`catalogue/options/secops.json`, then re-run `python3 tools/gen_skills.py`.

## The agent hierarchy

Three tiers, 80 agents, generated from `catalogue/org/`:

- **`master-architect`** (tier 0) — evaluates the Domain Architects' output, reconciles across
  domains, grades the whole. Does not do domain work.
- **`architect-<domain>`** &times;12 (tier 1) — orchestrate, compile, validate and
  interoperability sense-check within one domain.
- **`sme-<capability>`** &times;67 (tier 2) — capability depth, working in isolation.

The four rules that make it more than a naming scheme:

1. **SMEs work in isolation.** An SME must not speculate about another capability's position.
   An Architect must not brief one SME with another's output before both have reported — a
   primed SME confirms rather than assesses.
2. **Nothing is assumed.** Every SME carries a `never_assume` list. Where an item applies and
   the answer was not given, it becomes a question with a named owner. Never a placeholder.
3. **Routing goes up, not sideways.** Same-domain need → routing request to your Architect.
   Cross-domain need → dependency escalated to the Master Architect. An SME never contacts a
   peer and never resolves a cross-domain dependency.
4. **Escalation is bounded.** Anything resolvable inside a domain stays there. The Master
   Architect sees only cross-domain dependencies and caveats, which is what keeps it able to
   evaluate rather than participate.

The protocol text is held once in `catalogue/org/hierarchy.json` and stamped verbatim into every
generated agent, so an SME's understanding of when to escalate cannot drift from its Architect's
understanding of when to accept. A test asserts this.

### Changing the team

```bash
$EDITOR catalogue/org/smes/<domain>.json   # add or change an SME
$EDITOR catalogue/org/hierarchy.json       # domains, protocols, escalation rules
python3 tools/gen_agents.py                # regenerate all 80 agents
python3 -m unittest discover tests
```

`gen_agents.py` deletes any agent carrying its generated marker before writing, so a removed SME
does not linger. Hand-written agents without the marker are left alone. A `peers` entry must
name a same-domain SME — cross-domain contact goes through escalation, and the generator refuses
a catalogue that breaks this.

### Coverage against the engine

Eight of the twelve security domains map onto the engine's nine validator domains. Four do not:
`offsec`, `human`, `phys`, `emrg`. A base plate run assesses nothing in them. Do not let a run's
clean verdict imply coverage there — the Master Architect agent says so explicitly and a test
asserts it keeps saying so.

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
