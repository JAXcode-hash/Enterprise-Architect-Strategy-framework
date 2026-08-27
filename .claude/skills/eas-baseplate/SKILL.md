---
name: eas-baseplate
description: >-
  Run the Enterprise Architect Strategy framework end to end against a brief. Use when someone
  provides a direction, initiative, programme brief or architecture intent and wants it
  assessed for coverage and due diligence - producing per-domain low-level designs, an
  end-to-end high-level design, and an executive pack with roadmap, benefits and risks. Also
  use for "base plate this", "assess this initiative", "what are we missing", or when a new
  project needs standing up in this repository.
---

# Base plate a direction

One command turns a brief of any complexity into a defensible architecture position with three
levels of output. Each request gets its own isolated project; no other project informs it.

## The lifecycle

1. **Intake.** The brief is read for signals — regulatory context, data sensitivity, estate
   shape, constraints — with the phrase that fired each one kept as evidence. Complexity is
   graded T1 to T4. What the brief *did not say* is recorded too, because a silence is an
   unasked question rather than an absent requirement.
2. **Fan-out.** Nine cyber-security validator domains each score their options against those
   signals and produce a ranked shortlist with a decomposable rationale.
3. **Fan-in.** The orchestrator interrogates every domain's choice against every other,
   repairs what it can, and grades a verdict.
4. **Render.** Low-level design per domain, one end-to-end high-level design, one executive
   pack, the base plate artefact, and the dual ledger.
5. **Iterate.** Pin anchors and override positions as answers land, then re-run. The base
   plate is a living artefact until the verdict reaches Stable.

## Run it

```bash
python3 -m eas new --brief briefs/example-regulated.md   # from a file
python3 -m eas new --text "..."                          # inline
cat brief.md | python3 -m eas new                        # from stdin
python3 -m eas serve                                     # browser UI on :8000
```

Then:

```bash
python3 -m eas list                                       # every project
python3 -m eas run <project-id>                           # re-run after changes
python3 -m eas set <project-id> data-security DATA-04     # fix a domain's position
python3 -m eas pin <project-id> secops "Type 1 log volume" "420 GB/day" "40 GB/day" "5 GB/day"
python3 -m eas catalogue                                  # every domain and option
python3 -m eas lint                                       # check the catalogue is coherent
```

Stdlib Python 3 only. Nothing to install.

## What a brief needs

Anything works — three sentences or thirty pages. More detail produces a better-evidenced
assessment, not a different process. The intake reads optional markdown headings if present:
`Objects`, `Integrations`, `Environments`, `Constraints`, `Drivers`.

The things most worth stating, because their absence is flagged and then assumed:

- the regulatory context and the maximum-sensitivity data element in scope
- whether production-derived data reaches non-production
- any hard date, and whether it is externally imposed
- any residency or sovereignty constraint
- whether third parties are material
- whatever volumetrics already exist

## What comes out

```
projects/<slug>-<date>/
  brief.md                     the exact brief assessed
  index.html                   self-contained dashboard - no network requests
  baseplate.json               the whole run, machine-readable
  inputs/overrides.json        fix a domain to an option
  inputs/anchors.json          pin volumetrics per environment
  options/<domain>.md          every option offered, scored, with rationale
  outputs/lld/<domain>.md      low-level design, per domain
  outputs/hld.md               end-to-end design: scope, flow, boundaries, matrix
  outputs/exec-pack.md         benefits, effort, roadmap, risks by category
  outputs/base-plate.md        the framework's own base plate artefact
  registers/decisions.md       decision ledger
  registers/evidence.md        evidence / audit ledger
  registers/risks.csv          every risk, including the emergent ones
  registers/questions.csv      the further-questioning backlog
```

## Reading the verdict

A first run almost always grades **Not yet a base plate** — nobody has pinned any numbers yet.
That is the framework doing its job. The useful output of a first run is the list of
sizing-critical anchors to chase and the blocking questions to assign.

Work it in this order:

1. Resolve contradictions — two domains asserting incompatible positions. Blocking.
2. Pin the sizing-critical anchors. Re-run after each batch.
3. Assign an owner and a date to each blocking question.
4. Close the gaps where one domain needs something no other domain supplies.

## Extending the framework

The content is data, not code. To add a domain option, a compatibility rule or an intake
signal, edit `catalogue/` and then:

```bash
python3 -m eas lint            # an option requiring a capability nothing provides is a bug
python3 tools/gen_skills.py    # regenerate the nine validator skills from the catalogue
python3 -m unittest discover tests -v
```

## Project isolation

Every run writes only inside its own project directory and reads only its own brief, overrides
and pins. Two initiatives cannot cross-pollinate. Each project records the catalogue
fingerprint that produced it, so a later phase can tell whether two projects were assessed
against the same framework version before it tries to compare their strategies.
