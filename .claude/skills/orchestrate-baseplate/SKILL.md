---
name: orchestrate-baseplate
description: >-
  The end-to-end orchestrator for the Enterprise Architect Strategy framework. Use after the
  nine validator domains have offered their options, to interrogate every domain's choice
  against every other, resolve contradictions, surface gaps and unpinned anchors, and grade an
  operability verdict. Also use when a base plate needs re-reconciling because an option was
  overridden or a volumetric anchor was pinned.
---

# Orchestrate a base plate

The orchestrator does not re-do domain work. It **reconciles** it.

Nine validator domains each produce four artefacts and a ranked set of options. The
orchestrator's job is to ask the question no single domain can answer: *do these positions
actually work together?*

## What it does, in order

### 1. Take each domain's leading option

Every domain scores its options against the intake signals. The top-scoring option is a
starting position, not a decision — it was chosen with no knowledge of what the other eight
domains picked.

### 2. Find every incompatibility

Four kinds, from three sources:

| Source | What it catches |
|---|---|
| Each option's `requires` list | A domain needs a capability no selected position supplies. |
| The brief's **mandates** | A capability the brief made non-negotiable that nothing supplies. |
| `catalogue/compat.json` mutex rules | Two positions that cannot both hold. |
| An option's `conflicts` list | A declared hard incompatibility between two specific options. |

Each becomes a **Contradiction** (incompatible positions — blocking) or a **Gap** (a required
hook with no owning position).

### 3. Repair, cheapest fit-loss first

Local search over single-option substitutions: try every alternative in every unlocked domain,
keep the swap that most reduces unresolved cross-domain weight, break ties on the smallest loss
of domain fit. Repeat to a fixed point.

When single swaps plateau, try **coordinated pairs**. Some reconciliations genuinely need two
moves at once — taking a sovereignty position, for example, can force a matching change in the
non-production data policy, and neither move helps on its own.

A domain fixed by hand in `inputs/overrides.json` is **never overruled**. The orchestrator
routes repairs through the other domains and reports whatever it could not reconcile.

Every substitution is recorded with what it addressed and what it cost, because "the domain
wanted X and the estate needs Y" is exactly the kind of decision that gets challenged later.

### 4. Build the N×N integration matrix

Rows impose, columns receive. Each non-empty cell is classified:

- **Satisfied** — the required hook is met and consistent.
- **Contradiction** — two domains assert incompatible positions. Blocking.
- **Gap** — a required hook has no owning position. Becomes a further-questioning item with an owner.
- **Unpinned** — a position depends on an anchor nobody has quantified. Blocks sizing.

The seed dependencies worth checking by hand if you are running this without the engine:

- **Identity → SecOps.** The Type 1 who/what schema must be present in the log fields. *Failure mode:* logs that cannot attribute an action.
- **Network (DNS, private connectivity) → Data (residency).** A routing or resolution choice must not silently move data across a residency boundary. *Failure mode:* a failover path that egresses through the wrong region.
- **Network (outbound) → Data (DLP) → SecOps (egress detection).** Every egress path needs a data control *and* a detection. *Failure mode:* an allow-listed FQDN with no DLP and no log.
- **Integration (each edge) → Identity + Data + SecOps.** Every trust-boundary edge needs authZ, payload classification and a consumable log. *Failure mode:* an internal integration trusted by location, not identity.
- **Platform (provenance) → GRC (evidence).** Provenance claims must produce the evidence GRC will be asked for. *Failure mode:* an assurance level asserted, unprovable.
- **All volumetric anchors → Resilience (capacity).** Summed peak anchors must fit provisioned capacity and the stated RTO/RPO. *Failure mode:* log volume or TPS the sized platform cannot carry at peak.
- **Environment Parity → all.** Any domain that produced only a Prod column is an automatic finding.

### 5. Raise what only exists in combination

Some risks and questions belong to no single domain — they arise from two positions read
together. Micro-segmentation into a combined logging pipeline. A stated impact tolerance
alongside backup-based regional recovery. Customer identity data under provider-managed keys.
These are held in `catalogue/compat.json` as `emergent-risk` and `question-raised` rules, and
they are the findings a per-domain review structurally cannot produce.

`anchor-required` rules do the reverse: one domain's choice makes *another* domain's anchor
sizing-critical. Choosing micro-segmentation makes the SecOps Type 1 volume critical, because
that decision is what changes the number.

### 6. Grade the verdict

| Verdict | Meaning |
|---|---|
| **Stable** | No contradictions, no unpinned critical anchors, no blocking questions. Defensible as it stands. |
| **Conditional** | Coherent end to end, but with named open questions gating specific decisions. Assign an owner and a date to each. |
| **Not yet a base plate** | Contradictions remain, or critical anchors are unpinned. Positions that depend on an unquantified anchor cannot be sized, costed or defended. |

A fresh run almost always grades **Not yet**, because nobody has pinned any numbers. That is
the framework working, not failing. Pin anchors, re-run, and watch it move.

## Running it

```bash
python3 -m eas new --brief briefs/your-brief.md    # intake, fan-out, fan-in, render
python3 -m eas run <project-id>                    # re-reconcile after a change
python3 -m eas set <project-id> <domain> <OPT-ID>  # fix a domain, then re-reconcile
python3 -m eas pin <project-id> <domain> "<metric>" "<prod>" "<rtl>" "<devtest>"
python3 -m eas serve                               # the same lifecycle in a browser
```

Reconciliation is **deterministic**: the same catalogue, brief, overrides and pins always
produce the same base plate. That is what makes two runs comparable and a decision defensible.

## The dual ledger

Positions and the checks behind them are kept apart, so either can be challenged independently:

- `registers/decisions.md` — the position, its rationale, the alternatives, the owner, and
  whether the orchestrator overruled the domain.
- `registers/evidence.md` — what was checked, by what method, what came back, and when,
  including the decomposition of every score.

Keeping scoring decomposable is not bookkeeping. Where a model or an automated judgement
influences a material decision, a score that cannot be taken apart cannot be defended under
model-risk challenge.

## What the orchestrator will not do

- It will not overrule a domain fixed in `inputs/overrides.json`. It reports instead.
- It will not invent a number. An unpinned anchor stays unpinned and blocks the verdict.
- It will not read another project. Every run is isolated.
