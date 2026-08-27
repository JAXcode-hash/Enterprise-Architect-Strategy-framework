# Architecture Base Plate Framework

*A repeatable, research-augmented method for standing up a new architecture direction and strategy — partitioned into validator skills, reconciled by an end-to-end orchestrator, and anchored on real volumetrics across Prod / RTL / Dev-Test.*

---

## 1. What a "base plate" is

A **base plate** is the structured, defensible foundation you produce *before* committing to a target architecture: the set of validated positions, pinned quantities, open questions, and cross-domain dependencies that a direction/strategy must stand on. It is not the design — it is the load-bearing surface the design bolts onto.

A **run** of the framework takes a candidate direction (a brief, a set of Capability Reference Architectures, an existing estate, or a greenfield intent) and produces a base plate by:

1. **Intake** — capture the direction, the in-scope objects/components, and the environment topology.
2. **Per-domain validation** — each validator skill works its domain independently: completes a checklist, raises further-questioning, pins volumetric anchors per environment, and declares the *hooks* it imposes on or requires from other domains.
3. **Orchestration (E2E)** — the orchestrator reconciles every domain's hooks against every other's, resolves contradictions, surfaces gaps, and produces an operability verdict plus a consolidated decision and risk register.
4. **Base plate output** — a single structured artefact you can defend at STRADA/ARC and iterate.

Each domain produces exactly **four artefact types**, which is what keeps runs comparable and the orchestrator's job tractable:

| Artefact | Purpose |
|---|---|
| **Checklist** | Binary/gradable verifications — the "did we cover it" surface. |
| **Further-questioning** | Open items requiring a stakeholder answer or web research before the position is safe. |
| **Volumetric anchors** | The numbers that must be pinned *per environment* to size and defend the position. |
| **Cross-domain hooks** | What this domain *imposes on* others and *requires from* others — the orchestrator's raw material. |

---

## 2. The three cross-cutting lenses

Applied *inside every domain*, not as separate stages:

- **Environment lens (Prod / RTL / Dev-Test).** Every checklist item and every anchor is evaluated three times. RTL is treated as first-class, not "prod-lite": it has its own connectivity, its own data-handling rules, and its own volumetric profile. The single highest-value environment question the framework forces: *what real/quasi-real data touches non-prod, and under what control?*
- **Integration lens (object-to-object).** Security is verified *at every interface*, not per component in isolation. Each integration between two objects is a first-class thing to validate: its trust boundary, its authN/authZ, its transport, its logging, its residency.
- **Volumetric lens.** Qualitative positions are anchored on quantities. "We'll allow outbound to partners" becomes "N allow-listed FQDNs, X GB/day egress, split P/RTL/D-T" — which is what makes it sizeable, costable, and defensible.

---

## 3. Domain catalogue

Nine validator domains. Each becomes one skill (§6). Ordered by how tightly they gate the others.

> **Note on "Type 1 / Type 2" logs:** interpreted here as **Type 1 = security-relevant/audit logging** (identity, access, control-plane, and detection events for SIEM/SOC, forensics, and regulatory retention) and **Type 2 = operational/observability logging** (application and infrastructure telemetry, health, performance). If LBG uses a specific internal taxonomy, rebind these two definitions in the SecOps skill and the rest of the framework follows unchanged.

### 3.1 Identity & Access Validation
**Scope:** human and workload identity, authentication, authorisation, privilege, secrets, federation.

- **Checklist (extract):** authN model per actor class (workforce / customer / service / machine); token type, lifetime, audience, and claims; authZ model (RBAC/ABAC/ReBAC) and policy location (in-app vs external PDP); privileged access path and JIT/JEA; secret and certificate lifecycle (issuance, storage, rotation, revocation); workload identity (federation vs long-lived credentials); federation trust inventory; break-glass; joiner/mover/leaver flow into non-prod.
- **Further-questioning:** Where is the authorisation *decision* made, and is it consistent across every integration? Which identities cross the Prod/RTL boundary? Who owns the IdP trust in RTL? Is any customer or production identity data present in Dev-Test?
- **Volumetric anchors (P / RTL / D-T):** # human identities; # workload/machine identities; token issuance rate (auth/s); peak session concurrency; # privileged accounts; # secrets & certs under management + rotation rate; # federation trusts; # authZ roles/policies.
- **Cross-domain hooks:** *imposes* the "who/what" schema on SecOps Type 1 logs and the subject on every Integration interface; *requires* Network reachability to IdP/PDP and Data protection for identity stores.

### 3.2 Network Security Validation
**Scope:** DNS and name resolution, private connectivity, internet outbound, ingress, segmentation, east-west.

- **Checklist (extract):** DNS resolution topology (authoritative, conditional forwarding, NRPT/split-horizon, hairpin/trombone risks); private connectivity option per flow (ExpressRoute/Interconnect/PrivateLink/Private Endpoint/S2S VPN) and its failure/failover mode; internet-outbound design (egress via proxy/NAT/firewall, allow-listing granularity — IP vs FQDN vs L7 URL); ingress and public-surface exposure + WAF posture; macro/micro-segmentation and east-west policy; address-space plan and overlap risk across P/RTL/D-T; certificate-trust prerequisites for any inspection/steering.
- **Further-questioning:** Does any name resolve differently across environments, and is that intentional? What is the *single controllable variable* for correctness (e.g. NRPT rule set) versus what is inherited? Where does outbound actually egress in RTL, and is it inspected? Are there split-tunnel constraints imposed by a forwarding profile?
- **Volumetric anchors (P / RTL / D-T):** # VPN tunnels / IPsec SAs per connection; # private circuits + bandwidth; CIDR allocated vs consumed, # VNets/VPCs/subnets; DNS QPS + # zones + # NRPT/conditional-forward rules; egress GB/day per destination class; # allow-listed FQDNs/URLs; # public endpoints + ingress RPS; # east-west service pairs.
- **Cross-domain hooks:** *imposes* reachability and residency constraints on Data and Integration, and flow-log sources on SecOps; *requires* Identity for any identity-aware routing/proxy and GRC for residency rules.

### 3.3 Data Security Validation
**Scope:** classification, encryption, key management, residency/sovereignty, tokenisation/masking, retention, DLP.

- **Checklist (extract):** classification per store and per flow; encryption at rest (algorithm, key ownership, HYOK/BYOK/CMK) and in transit (TLS floor, mTLS where required); key management lifecycle and blast radius per key; residency and sovereignty per store and per cross-boundary flow; tokenisation/masking coverage; retention and disposal per class; DLP coverage on egress paths; **non-prod data handling** (synthetic vs masked vs real).
- **Further-questioning:** What is the maximum-sensitivity data element in scope, and does its handling hold across all three environments? Does any private-connectivity or DNS decision move data across a residency boundary? Is production data ever used in RTL/Dev-Test, and if so under what masking guarantee?
- **Volumetric anchors (P / RTL / D-T):** data-at-rest GB/TB per classification + growth GB/month; transaction volume (TPS steady/peak, TPD); # datastores; # KMS keys + rotation frequency; # cross-boundary flows + in-transit GB/day; retention days per class; backup volume + RPO; # DLP/tokenisation rules; **% real data in non-prod**.
- **Cross-domain hooks:** *imposes* residency/encryption requirements on Network and key-access requirements on Identity; *requires* SecOps for data-access audit and Resilience for backup/restore.

### 3.4 Integration & Interface Validation
**Scope:** every object-to-object integration — APIs, events/messages, batch/file, third-party.

- **Checklist (extract):** interface inventory (internal + external) with trust boundary marked per edge; per-interface authN/authZ, transport, and payload protection; contract and schema governance; sync vs async and idempotency/replay handling; third-party integrations and their DORA/CTP relevance; error, retry, and poison-message handling; per-interface logging sufficiency.
- **Further-questioning:** For each edge crossing a trust boundary, is security *verified at the edge* rather than assumed from the component? Which integrations differ between Prod and RTL (stubs, mocks, sandboxes) and does that mask a real risk? Which third parties are material/CTP?
- **Volumetric anchors (P / RTL / D-T):** # interfaces per environment; # APIs + req rate per interface; # trust boundaries crossed; # event topics + msg/s throughput; payload size distribution; # external third-party integrations; # data-sharing agreements.
- **Cross-domain hooks:** *imposes* subject/authZ requirements on Identity and flow requirements on Network; *requires* Data classification per payload and SecOps per-interface logging.

### 3.5 Security Operations Validation
**Scope:** Type 1 (security/audit) and Type 2 (operational) logging, SIEM/SOAR, detection, monitoring, incident response.

- **Checklist (extract):** log source inventory mapped to both types; Type 1 field completeness (who/what/where/when/outcome) traceable to the Identity schema; Type 2 coverage for health/performance; ingestion pipeline and retention tiers (hot/warm/cold); detection use-cases mapped to in-scope threats; alerting and MTTD/MTTR targets; SOAR playbooks; IR runbook and evidence handling; **non-prod logging** (is RTL/Dev-Test monitored, and should it be?).
- **Further-questioning:** Does every integration and every egress path emit a log a detection can consume? Are Type 1 and Type 2 separated at ingestion (retention, access, cost differ)? What is monitored in RTL — and is a gap there a real detection blind spot?
- **Volumetric anchors (P / RTL / D-T):** log volume GB/day + EPS, split Type 1 vs Type 2; # log sources/connectors; retention TB per tier + days; # detection use-cases; alert rate/day; MTTD/MTTR targets; # SOAR playbooks; ingestion cost anchor.
- **Cross-domain hooks:** *requires* fields from Identity, sources from Network/Integration/Data/Platform; *imposes* an emit-and-retain obligation back on all of them (this is the domain most often shortchanged by the others).

### 3.6 Platform & Compute Validation
**Scope:** runtime and workload placement, supply chain, IaC, admission control, provenance.

- **Checklist (extract):** workload placement and isolation model; image/build provenance (SLSA level, signing/Sigstore, Binary Authorization / admission control); IaC governance and drift detection (OPA/Rego gates); base-image and dependency hygiene; runtime protection; **parity of the platform itself across environments**.
- **Further-questioning:** Is the RTL platform built by the same pipeline as Prod, or hand-crafted? What provenance guarantee survives promotion? Where can unsigned/unverified artefacts enter in non-prod?
- **Volumetric anchors (P / RTL / D-T):** # workloads/services; # clusters/nodes + capacity (vCPU/mem); # container images; deployment frequency; # pipelines + provenance coverage %; # IaC modules; # admission-control policies.
- **Cross-domain hooks:** *imposes* provenance evidence on GRC and identity on Identity (workload identity); *requires* Network placement and SecOps runtime telemetry.

### 3.7 Resilience & Continuity Validation
**Scope:** availability, DR, capacity, backup/restore, failover.

- **Checklist (extract):** RTO/RPO per service tier; HA topology (# AZ/regions, active-active vs active-passive); failover trigger and tested behaviour; backup scope/frequency + restore test cadence; capacity headroom vs peak; dependency-failure and graceful-degradation behaviour; **RTL's role in DR rehearsal**.
- **Further-questioning:** Do the volumetric anchors from Network/Data/SecOps actually fit the provisioned capacity at peak? Is failover ever *tested*, and where? Does a private-connectivity or DNS single point of failure undermine the stated RTO?
- **Volumetric anchors (P / RTL / D-T):** RTO/RPO per tier; # AZ/regions; backup volume + frequency; restore-test cadence; capacity headroom %; peak concurrency.
- **Cross-domain hooks:** *requires* anchors from Network/Data/SecOps/Platform to size against; *imposes* nothing new but *validates* everyone else's numbers against capacity.

### 3.8 Governance, Risk & Compliance Validation
**Scope:** regulatory spine, control mapping, model risk, evidence, exceptions.

- **Checklist (extract):** applicable regime mapped (PRA/FCA, DORA, PCI-DSS v4, SS-series incl. CTP SS6/24, ISO 27001, NIST 800-53 as relevant); control-to-requirement mapping with evidence source; model-risk treatment where models/LLMs are in scope (SS1/23 — decomposable, defensible scoring); exception/waiver register; residual-risk decision owner.
- **Further-questioning:** Which positions are *decisions under uncertainty* that need a named owner rather than a control? Where does the framework's own scoring need to be defensible under model-risk challenge? Which third parties trip CTP thresholds?
- **Volumetric anchors (P / RTL / D-T):** # applicable controls; # mapped + evidenced; # exceptions/waivers; # material/CTP third parties; model-risk tier if applicable.
- **Cross-domain hooks:** *requires* evidence from every domain; *imposes* residency, retention, and evidence obligations back onto Data/Network/SecOps/Platform.

### 3.9 Environment Parity & Route-to-Live Validation
**Scope:** the Prod/RTL/Dev-Test relationship itself — parity, promotion, drift, and env-specific data/exception handling.

- **Checklist (extract):** environment topology and ownership; config-parity assertion (what is deliberately different vs accidentally drifted); promotion gates and what each gate verifies; per-environment data policy (synthetic/masked/real); env-specific exceptions register; secrets/identity separation across environments; is RTL representative enough to catch what Prod will hit?
- **Further-questioning:** For every position in every domain, does it hold in all three environments — and where it doesn't, is that a decision or an oversight? What is the config-drift delta right now?
- **Volumetric anchors:** env count + topology; # config divergences P vs RTL vs D-T; % real data per non-prod env; promotion lead time; # promotion gates; # env-specific exceptions.
- **Cross-domain hooks:** this domain is the environment lens made explicit — it *cross-examines* every other domain's three-column anchors and flags any domain that only reasoned about Prod.

---

## 4. The orchestrator (end-to-end)

The orchestrator does not re-do domain work. It **reconciles** it. Its inputs are the nine domains' four-artefact outputs; its output is an E2E operability verdict, a consolidated register, and the residual question backlog.

### 4.1 Integration matrix
Build an N×N matrix of domain-to-domain hooks. Each non-empty cell is a dependency the orchestrator must confirm is *satisfied and consistent*. Seed dependencies (non-exhaustive — the strong ones that catch most blind spots):

- **Identity → SecOps:** the Type 1 "who/what" schema must be present in the log fields. *Failure mode:* logs that can't attribute an action.
- **Network (DNS + private connectivity) → Data (residency):** a routing or resolution choice must not silently move data across a residency boundary. *Failure mode:* a hairpin or failover path that egresses data through the wrong region.
- **Network (outbound) → Data (DLP) → SecOps (egress detection):** every egress path needs a data control *and* a detection. *Failure mode:* an allow-listed FQDN with no DLP and no log.
- **Integration (each edge) → Identity + Data + SecOps:** every trust-boundary edge needs authZ, payload classification, and a consumable log. *Failure mode:* an internal integration trusted by location, not identity.
- **Platform (provenance) → GRC (evidence):** provenance claims must produce the evidence GRC will be asked for. *Failure mode:* SLSA asserted, unprovable.
- **All volumetric anchors → Resilience (capacity):** the summed peak anchors must fit provisioned capacity and the stated RTO/RPO. *Failure mode:* log volume or TPS that the sized platform can't carry at peak.
- **Environment Parity → all:** any domain that produced only a Prod column is an automatic finding.

### 4.2 Reconciliation logic
For each matrix cell, classify:
- **Satisfied** — the required hook is met and consistent.
- **Contradiction** — two domains assert incompatible positions (e.g. Data requires in-region key custody; Network's DR path leaves region). Must be resolved before the base plate is stable.
- **Gap** — a required hook has no owning position (e.g. an egress path with no detection). Becomes a further-questioning item with an owner.
- **Unpinned** — a position depends on an anchor nobody has quantified. Blocks sizing.

### 4.3 Operability verdict
The orchestrator emits a graded E2E verdict, not a pass/fail:
- **Stable** — no contradictions, no unpinned anchors on critical paths, gaps have owners and dates.
- **Conditional** — coherent but with named open questions that gate specific decisions.
- **Not yet a base plate** — contradictions or critical unpinned anchors remain.

### 4.4 Consolidated register (dual-ledger)
Mirror the decision/audit split you already use: a **decision ledger** (position, rationale, owner, environments it applies to, superseded-by) and an **evidence/audit ledger** (what was checked, which anchor pinned it, which research source, timestamp) — so scores and positions stay decomposable and defensible under SS1/23 challenge.

---

## 5. Run lifecycle

1. **Intake** → capture direction, object/component inventory, environment topology, and known constraints into the base-plate template (§7).
2. **Fan-out** → invoke the nine validator skills (parallel where independent; §6).
3. **Research** → each skill uses web/MCP research for current-state facts (vendor limits, regulatory text, protocol behaviour) and cites into its evidence ledger.
4. **Fan-in** → orchestrator builds the integration matrix, reconciles, grades.
5. **Output** → render the base plate; unresolved cells become the further-questioning backlog with owners.
6. **Iterate** → re-run affected domains as answers land; the decision ledger records supersessions. The base plate is a living artefact until the verdict reaches Stable.

---

## 6. Skill categorisation (one validator per domain + one orchestrator)

Each domain maps to a self-contained skill. Recommended shape:

| Skill | Type | Tools it needs | Research strategy |
|---|---|---|---|
| `validate-identity-access` | validator | web, MCP (IdP/PAM if available) | vendor token/limits, protocol behaviour |
| `validate-network-security` | validator | web, MCP (cloud/network) | vendor connectivity limits, DNS/NRPT behaviour |
| `validate-data-security` | validator | web, MCP (KMS/DB) | crypto standards, residency rules |
| `validate-integration` | validator | web, MCP (API/catalogue) | API security patterns, DORA/CTP text |
| `validate-secops` | validator | web, MCP (SIEM) | detection content, retention/regulatory floors |
| `validate-platform-compute` | validator | web, MCP (registry/CI) | SLSA, admission-control patterns |
| `validate-resilience` | validator | web | RTO/RPO norms, failover patterns |
| `validate-grc` | validator | web | current regulatory text (PRA/FCA/DORA/PCI v4/SS-series) |
| `validate-env-parity-rtl` | validator | web | — (mostly cross-examination) |
| `orchestrate-baseplate` | orchestrator | reads all validator outputs | — |

Each validator SKILL.md carries: its four-artefact template, its checklist, its further-questioning prompts, its per-environment anchor list, and its declared hooks. The orchestrator SKILL.md carries the integration matrix seed, the reconciliation logic, and the verdict/register templates. Validators are model-cheap; reserve the stronger model for the orchestrator's reconciliation.

---

## 7. Base-plate output template

```
# Base Plate — <direction name> — <date> — verdict: <Stable|Conditional|Not yet>

## 0. Intake
- Direction / intent:
- In-scope objects & integrations:
- Environment topology (Prod / RTL / Dev-Test):
- Known constraints:

## 1..9. <Domain> Validation
- Checklist result (with gaps flagged)
- Further-questioning (owner, due)
- Volumetric anchors — table [ P | RTL | D-T ]
- Cross-domain hooks (imposes / requires)

## 10. E2E Orchestration
- Integration matrix (Satisfied / Contradiction / Gap / Unpinned)
- Contradictions to resolve (blocking)
- Gaps with owners
- Unpinned critical anchors

## 11. Registers
- Decision ledger
- Evidence / audit ledger

## 12. Verdict & residual backlog
```

---

## 8. Tooling: Claude Code vs Projects

**Build the durable framework in Claude Code; optionally keep a thin Projects front door for quick interactive base-plating.** Reasoning below.

The framework *is* a "skills + validators + orchestrator" system, which is precisely the pattern Claude Code is now built around:

- **Validators = skills.** A SKILL.md is a versioned, folder-based procedure Claude loads by relevance or by `/name`. It travels with the repo, so the whole framework is one shareable folder with no per-user setup — versioned procedures the AI executes the same way every time, which is exactly the "repeatable, no blind spots" property you want.
- **Orchestrator = subagent (or Agent Team).** Claude Code subagents run in isolated context with their own tools/model and return only a result, so nine validators can fan out without polluting one transcript, then the orchestrator reconciles. Built-in Agent Teams gives you a coordinating "lead" over longer-lived workers if you want the heavier topology later.
- **Research + integration = MCP + web, natively,** with tool scope set per validator (read-only where appropriate).
- **Gating = hooks.** A SubagentStop-style gate lets you refuse to emit a base plate while contradictions or critical unpinned anchors remain — the machine-enforced version of your verdict grades.

**Projects can't do the orchestration.** A Project gives you persistent custom instructions plus knowledge files in one conversation — excellent for *case-specific* context, but it has no parallel validators, no isolated-context subagents, no orchestrator, and no gating. The current best-practice split is explicit: **Projects hold case knowledge; skills hold the reusable procedure.** Your framework is procedure, so it belongs in skills/Claude Code, not baked into a Project's instructions.

**Recommended topology:**

```
repo/
  .claude/
    skills/
      validate-identity-access/SKILL.md
      validate-network-security/SKILL.md
      ... (nine validators)
      orchestrate-baseplate/SKILL.md
    agents/
      baseplate-orchestrator.md      # subagent that fans out + reconciles
    hooks/
      subagent-stop-gate.*           # blocks emit on Contradiction/Unpinned-critical
  templates/
    base-plate.md                    # §7
  runs/
    <direction>-<date>/              # each run's output + registers
  CLAUDE.md                          # how a run works; env definitions; Type1/2 binding
```

Use a **Project** only as a lightweight entry point when you want to base-plate something interactively in the browser/app without cloning the repo — point its instructions at the same checklists and paste a direction in. It won't orchestrate, but it's fine for a first-pass sniff test that you then formalise with a full Claude Code run.

**One-line answer:** Claude Code for the framework (it maps 1:1 onto skills + subagent orchestrator + hooks); Projects only as an optional quick-start surface.
