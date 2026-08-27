---
name: security-architecture-team
description: >-
  Engage the security architecture team - a Master Architect over twelve Domain Architects over
  sixty-seven capability SMEs. Use when a security question needs more depth than one person
  holds, when a position must be sense-checked across security domains, or when you need to know
  which questions have not been asked. Also for "get the SMEs on this", "what would a security
  architect ask", "is this coherent across domains", or picking the right agent for a security topic.
---

# The security architecture team

An amalgamous security architecture function: SME depth that can be rationalised and sense-checked
against other SMEs' knowledge, with an orchestration layer that stops anybody assuming anything
they were not told.

```
                      master-architect                     tier 0  evaluates, reconciles, grades
                             |
        +--------------------+--------------------+
        |                    |                    |
  architect-grc        architect-iam        architect-secops  ...  tier 1  x12  orchestrate,
        |                    |                    |                         compile, validate,
   +----+----+          +----+----+          +----+----+                    sense-check
   |         |          |         |          |         |
 sme-...   sme-...    sme-...   sme-...    sme-...   sme-...       tier 2  x67  capability depth,
                                                                            working in isolation
```

## Which tier to engage

| You have | Engage | Why |
|---|---|---|
| A question inside one capability | `sme-<capability>` | Depth, in isolation, with the assumptions it refused to make |
| A question spanning one domain | `architect-<domain>` | It fans out to its own SMEs and reconciles them |
| Anything touching two or more domains | `master-architect` | Only it can see what two domains have each assumed the other handles |
| A whole architecture direction | `master-architect` | It runs the engine for the nine domains it covers and the Architects for the rest |

Start at the lowest tier that can hold the whole question. Going straight to the Master Architect
for a single-domain question wastes the independent check that the tier exists to provide.

## The twelve domains

| Architect | Domain | SMEs | Covered by the engine |
|---|---|---|---|
| `architect-grc` | Governance, Risk & Compliance | 8 | yes |
| `architect-sae` | Security Architecture & Engineering | 6 | partly |
| `architect-iam` | Identity & Access Management | 6 | yes |
| `architect-app` | Application & Product Security | 6 | partly |
| `architect-data` | Data Security | 6 | yes |
| `architect-infra` | Infrastructure & Platform Security | 6 | yes |
| `architect-secops` | Security Operations | 8 | yes |
| `architect-offsec` | Offensive Security & Adversary Simulation | 5 | **no** |
| `architect-res` | Resilience & Continuity | 5 | yes |
| `architect-human` | Human & Organisational Security | 4 | **no** |
| `architect-phys` | Physical & Environmental Security | 3 | **no** |
| `architect-emrg` | Emerging & Specialised | 4 | **no** |

Four domains have no counterpart in the base-plate engine. A run assesses nothing in them, so a
position that never engaged those Architects is incomplete rather than clean.

## The rules that make it work

**SMEs work in isolation.** Each answers only within its capability and must not speculate about
another's, even one it understands. A primed SME confirms rather than assesses, so an Architect
never briefs one with another's output before both have reported.

**Nothing is assumed.** Every SME carries an explicit list of things that look settled and are
not. Where one applies and the answer was not given, it becomes a question with a named owner —
never a placeholder and never a reasonable-sounding guess.

**Routing goes up, not sideways.** An SME needing a peer's input returns a routing request to its
Architect; it does not contact the peer. An SME needing another domain returns a dependency; it
does not resolve it.

**Escalation is bounded.** Anything resolvable inside a domain stays there. The Master Architect
sees only cross-domain dependencies and caveats — which is what keeps it able to evaluate rather
than participate.

**Disagreement is a finding.** Two SMEs disagreeing is not averaged. The Architect identifies the
fact that separates them and routes it back as a specific question.

## Using it with the base-plate engine

The Enterprise Architect Strategy engine covers nine of the twelve domains with a catalogued
option set, cross-domain compatibility rules and volumetric anchors. It is deterministic and does
the mechanical reconciliation in under a second.

```bash
python3 -m eas new --brief briefs/example-regulated.md   # engine run
```

Then engage the team to do what the engine cannot: check its reasoning with SME depth, cover the
four domains it does not reach, and surface the current facts a catalogue of durable patterns
cannot hold.

The division is deliberate — the engine holds what is stable, the SMEs hold what changes.

## Changing the team

The org chart is data. Agents are generated, so edit the catalogue and regenerate:

```bash
$EDITOR catalogue/org/smes/<domain>.json     # add or change an SME
$EDITOR catalogue/org/hierarchy.json         # domains, protocols, escalation rules
python3 tools/gen_agents.py                  # regenerate all 80 agents
python3 -m unittest discover tests
```

The protocol is stamped into every agent from one source, so an SME's understanding of when to
escalate cannot drift from its Architect's understanding of when to accept.
