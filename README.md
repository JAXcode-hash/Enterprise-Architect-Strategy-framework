# Enterprise Architect Strategy

A repeatable application for standing up an architecture direction. Give it a brief of any
complexity; nine cyber-security validator domains each offer defensible **options**, and an
**orchestrator** interrogates those options against each other to produce a coherent end-to-end
position with three levels of output.

Every request gets its **own isolated project**. No other project informs it.

```bash
./setup.sh                                               # verify - installs nothing
python3 -m eas new --brief briefs/example-regulated.md   # assess a direction
python3 -m eas serve                                     # the same thing in a browser
```

Python 3.9+ standard library only. **There is nothing to install** — `setup.sh`
(or `setup.ps1` on Windows) checks your Python, confirms the 23 stdlib modules the
engine uses are present, lints the catalogue and runs the test suite. It installs
packages only with `--docs`, and those are needed solely to rebuild the setup
document. No network access is required to run an assessment.

---

## What it produces

For every brief, three levels of detail plus the registers behind them:

| Output | For whom |
|---|---|
| `outputs/lld/<domain>.md` &times; 9 | The engineer building it and the assessor testing it. Checklist across Prod/RTL/Dev-Test, further-questioning with owners, volumetric anchors per environment, cross-domain hooks, risks, control mapping. |
| `outputs/hld.md` | The architecture forum. Scope boundaries, generated end-to-end flow, connectivity and trust boundaries, a summary of each domain, the N&times;N reconciliation matrix, delivery shape. |
| `outputs/exec-pack.md` | The reader who will not open the HLD. What it delivers and why, where the effort sits, a banded roadmap, and risks grouped by the kind of problem they create — timeline, workarounds, legal and regulatory, and the security exposures filtered up out of the low-level designs. |
| `outputs/base-plate.md` | The framework's own artefact: intake, nine domains, orchestration, registers, verdict. |
| `registers/` | The dual ledger — decisions and the evidence behind them — plus the risk and question backlogs as CSV. |
| `index.html` | A self-contained dashboard holding all of the above. No network requests; send it as a file. |

---

## How it works

### 1. Intake

The brief is read for signals — regulatory context, data sensitivity, estate shape,
constraints — and every signal keeps the phrase that fired it, so nothing downstream is
asserted without evidence. Complexity is graded **T1** (contained change) to **T4**
(estate-level programme) from the weighted signal set and brief length.

Two things make the intake more than pattern matching:

- **Silence is recorded.** What the brief did *not* say is carried forward as an explicit
  assumption. A brief that never mentions non-production has not established that
  non-production is out of scope.
- **Some signals create mandates.** "Residency is mandatory" does not merely favour options —
  it makes `data.residency.in-region` non-negotiable, and the orchestrator raises a gap against
  the owning domain if nothing supplies it. A hard constraint should not be outvoted by a pile
  of soft ones.

### 2. Fan-out — nine validator domains

| Code | Domain | Skill |
|---|---|---|
| IAM | Identity & Access | `validate-identity-access` |
| NET | Network Security | `validate-network-security` |
| DATA | Data Security | `validate-data-security` |
| INT | Integration & Interface | `validate-integration` |
| SEC | Security Operations | `validate-secops` |
| PLAT | Platform & Compute | `validate-platform-compute` |
| RES | Resilience & Continuity | `validate-resilience` |
| GRC | Governance, Risk & Compliance | `validate-grc` |
| ENV | Environment Parity & Route-to-Live | `validate-env-parity-rtl` |

#### Logging is modelled on ownership, not content

The SecOps domain encodes this organisation's three-type operating model, in which each type is
owned by a different function and the ownership decides who is obliged to do what:

- **Type 1 — Security Event Detection and Handling.** Owned by the central security monitoring
  function, driven by their threat modelling. Requirements are *dynamic*. Technology owners do
  not implement proactively; they are engaged when a source is required.
- **Type 2 — Security Compliance Reporting.** Owned by security governance and compliance, who
  determine what regulatory and audit obligations require and configure retention on the
  enterprise compliance platform.
- **Type 3 — General and Operational Logging.** The technology owner's own decision. Not
  centrally mandated, not centrally provided.

A team therefore has **no obligation to log a source neither central function has identified**.
Two consequences are enforced in the framework:

- **No brief can mandate Type 1**, and no domain may require it — only the monitoring function
  decides. A domain that needs attribution requires *ingestion compatibility* instead; a domain
  that needs evidence requires *Type 2*. A test asserts this holds.
- **Ingestion compatibility becomes the load-bearing design property.** Since requirements
  change with the threat landscape, the real architectural question is what it costs when the
  monitoring function asks. The anchor `Estimated effort to connect a newly requested source`
  makes that cost arguable rather than rhetorical.

The five SecOps options are postures toward this model — from engagement-driven with no
compatibility designed in, through ingestion-compatible-by-design, to an embedded detection
partnership. Forcing the cheapest posture onto a regulated estate makes the framework cascade
downgrades through five other domains, because a hardened estate that reports nothing centrally
is not a coherent position.

Each domain offers 3–5 options spanning tactical to strategic. An option is a full posture
bundle, not a feature: what it costs, how long it takes, what it does for security and for
regulatory evidencing, the checklist it brings, the questions it opens, the numbers it needs
pinned, the risks it carries — and critically, **what it gives the rest of the estate and what
it needs back**.

Scores are decomposable by construction. Every point traces to a named signal and the phrase in
the brief that fired it, because a score that cannot be taken apart cannot be defended under
model-risk challenge.

### 3. Fan-in — the orchestrator

The part that makes this more than nine parallel checklists.

1. **Detect.** Unmet capability requirements, unmet mandates, mutex rules, declared conflicts.
2. **Repair.** Local search over single-option substitutions, keeping the swap that most
   reduces unresolved cross-domain weight at the least cost in domain fit. When single swaps
   plateau, try coordinated **pairs** — taking a sovereignty position can force a matching
   change in the non-production data policy, and neither move helps on its own.
3. **Reconcile.** Build the N&times;N matrix; classify each cell Satisfied, Contradiction, Gap
   or Unpinned.
4. **Raise what only exists in combination.** Micro-segmentation feeding a combined logging
   pipeline. A stated impact tolerance alongside backup-based regional recovery. Customer
   identity data under provider-managed keys. These are the findings a per-domain review
   structurally cannot produce.
5. **Grade.**

| Verdict | Meaning |
|---|---|
| **Stable** | No contradictions, no unpinned critical anchors, no blocking questions. |
| **Conditional** | Coherent end to end; named open questions gate specific decisions. |
| **Not yet a base plate** | Contradictions remain, or sizing-critical anchors are unpinned. |

A first run almost always grades **Not yet**, because nobody has pinned any numbers. That is
the framework working. Its useful output is the list of anchors to chase and questions to
assign.

A domain fixed by hand is **never overruled** — the orchestrator routes repairs through the
others and reports what it could not reconcile.

Reconciliation is deterministic. Same catalogue, brief, overrides and pins, same base plate.

---

## Working a project

```bash
python3 -m eas new --brief briefs/example-regulated.md    # create and run
python3 -m eas list                                       # every project
python3 -m eas show <project-id>                          # manifest and latest run

# Iterate — the base plate is a living artefact until the verdict reaches Stable
python3 -m eas set <project-id> data-security DATA-04     # fix a domain's position
python3 -m eas pin <project-id> secops "Type 2 compliance log volume" "420 GB/day" "40 GB/day" "5 GB/day"
python3 -m eas run <project-id>                           # re-reconcile

python3 -m eas catalogue                                  # every domain and option
python3 -m eas lint                                       # check the catalogue is coherent
python3 -m eas serve --port 8000                          # browser UI
```

The browser UI does the same lifecycle: paste a brief, read the options each domain offered,
override a position, pin an anchor, re-orchestrate.

---

## Project isolation

```
projects/<slug>-<date>/
  brief.md              the exact brief assessed
  project.json          manifest: id, created, engine version, catalogue fingerprint, run history
  inputs/               overrides and anchor pins — the only mutable inputs
  options/              every option each domain offered, scored, with rationale
  outputs/              lld/ &times;9, hld.md, exec-pack.md, base-plate.md
  registers/            decisions.md, evidence.md, risks.csv, questions.csv
  baseplate.json        the whole run, machine-readable
  index.html            self-contained dashboard
```

A project reads and writes only within its own directory; path escapes are refused rather than
resolved. Each project records the **catalogue fingerprint** that produced it, so a later phase
can tell whether two projects were assessed against the same framework version before it tries
to reconcile their strategies against each other.

Cross-project conflict detection is deliberately out of scope for this phase.

---

## Extending it

The content is data, not code — `catalogue/` is where the domain expertise lives:

| File | Holds |
|---|---|
| `domains.json` | The nine domains and their gating order. |
| `capabilities.json` | The shared cross-domain vocabulary, plus the implication map that lets a stronger position satisfy a weaker requirement. |
| `options/<domain>.json` | Each domain's options: postures, effort, hooks, checklist, questions, anchors, risks, controls. |
| `compat.json` | Cross-domain rules — mutex, emergent-risk, anchor-required, question-raised. |
| `signals.json` | Intake detection patterns, complexity weights, and the mandates a signal creates. |
| `benefits.json` | Capability → the business outcome the exec pack states. |

After editing:

```bash
python3 -m eas lint             # an option requiring a capability nothing provides is a bug
python3 tools/gen_skills.py     # regenerate the nine validator skills from the catalogue
python3 -m unittest discover tests -v
```

The validator skills are **generated** from the catalogue rather than written by hand, so the
skills and the engine can never disagree about what a domain covers.

---

## The security architecture team

Above the engine sits an organisation of agents — an amalgamous security architecture function
with SME depth that can be rationalised and sense-checked against other SMEs' knowledge.

```
                      master-architect                     tier 0   evaluates, reconciles, grades
                             |
        +--------------------+--------------------+
        |                    |                    |
  architect-grc        architect-iam        architect-secops  ...   tier 1  x12  orchestrate,
        |                    |                    |                          compile, validate,
   +----+----+          +----+----+          +----+----+                     sense-check
   |         |          |         |          |         |
 sme-...   sme-...    sme-...   sme-...    sme-...   sme-...        tier 2  x67  capability depth,
                                                                             in isolation
```

**Tier 2 — 67 SMEs.** One per capability in the cyber security taxonomy: penetration testing,
key management, insider threat, post-quantum readiness, OT/ICS, and so on. Each works in
isolation and must not speculate about another capability's position. Each carries an explicit
list of things that look settled and are not — where one applies and the answer was not given,
it becomes a question with a named owner, never a placeholder or a plausible guess.

**Tier 1 — 12 Domain Architects.** Orchestrators, compilers, validators and interoperability
sense-checkers. They fan out to their own SMEs, reconcile disagreement rather than averaging it,
check each position against its peers for compatibility, and ask what an SME assumed when it
returned no questions against a thin brief.

**Tier 0 — Master Architect.** Evaluates the Domain Architects' output and reconciles across
domains. It does not do domain work — an architect who does SME work stops being able to
evaluate it. It is the only tier that can see the **Assumed** state: two domains that have each
assumed the other handles something, which from inside either domain looks like a reasonable
reading of the other's scope.

### Routing

| You have | Engage | |
|---|---|---|
| A question inside one capability | `sme-<capability>` | Depth, in isolation |
| A question spanning one domain | `architect-<domain>` | Fans out and reconciles its own SMEs |
| Anything touching two or more domains | `master-architect` | Cross-domain dependencies and caveats only |

Routing goes up, never sideways: an SME needing a peer returns a request to its Architect rather
than contacting the peer; an SME needing another domain returns a dependency rather than
resolving it. Anything resolvable inside a domain stays inside it.

### Coverage against the engine

The engine's nine validator domains cover eight of the twelve security domains. Four have no
counterpart at all — **offensive security**, **human and organisational**, **physical and
environmental**, and **emerging and specialised**. A base plate run assesses nothing in them, so
a position that never engaged those Architects is incomplete rather than clean. The division is
deliberate: the engine holds what is stable, the SMEs hold what changes.

### Skills

| Skill | Purpose |
|---|---|
| `security-architecture-team` | The org chart, routing rules and how to engage a tier |
| `eas-baseplate` | Run the framework end to end against a brief |
| `orchestrate-baseplate` | The reconciliation method, for working a base plate by hand |
| `validate-*` &times; 9 | One per engine domain: the four artefacts, the options, the hooks |

The 80 agents and the 9 validator skills are all **generated** from `catalogue/`, so the org
chart and the engine can never disagree about what a domain covers.

## Repository layout

```
catalogue/          the framework's content — domains, capabilities, options, rules, signals
  org/              the security architecture org chart — hierarchy, protocols, 67 SME knowledge bases
eas/                the engine — intake, selector, orchestrator, roadmap, renderers, CLI, server
  render/           lld, hld, exec_pack, baseplate, diagram, html, md2html
.claude/agents/     80 generated agents - 1 master, 12 domain architects, 67 SMEs
.claude/skills/     twelve skills; the nine validators are generated
briefs/             three worked examples, simple through strategic
projects/           one isolated directory per assessment
tests/              42 tests, stdlib unittest
tools/gen_skills.py regenerates the validator skills from the catalogue
tools/gen_agents.py regenerates the 80 agents from catalogue/org/
```

## Origin

Built from `docs/architecture-base-plate-framework.md`, which sets out the method: partitioned
validator domains, four artefacts each, three cross-cutting lenses (environment, integration,
volumetric), an end-to-end orchestrator, and a graded operability verdict over a dual ledger.
