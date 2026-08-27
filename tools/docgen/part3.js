require('./part2.js');
const M = require('./build_docx.js');
const {A, H1, H2, H3, P, RUNS, BUL, NUM, CODE, RULE, NOTE, TBL,
       Document, Packer, Paragraph, TextRun, HeadingLevel, PageBreak, LevelFormat,
       AlignmentType, Footer, PageNumber, d, children} = M;
const fs = require('fs');

/* ===================== 5. PROMPT TEMPLATES ===================== */
A(H1("5. Prompt templates"),
  P("Four templates: the brief the engine reads, and one invocation per tier. Slots in angle brackets are yours to fill."),

  H2("5.1 The brief template"),
  P("The intake reads any brief — three sentences or thirty pages — but it reads these headings if they are present, and it records what you did not say as an explicit assumption carried into the design."),
  ...CODE([
    "# <Direction name>",
    "",
    "## Drivers",
    "- <What this is for, in outcome terms. The funded driver, not the aspirational one.>",
    "",
    "## Scope",
    "<What is being built or changed, and what it sits in front of or behind.>",
    "",
    "## Objects",
    "- <Component> (new | existing, integration only | retiring)",
    "",
    "## Integrations",
    "- <A to B, over what, crossing which boundary>",
    "",
    "## Environments",
    "- Prod",
    "- RTL   <how it differs from Prod today — this is the highest-value line in the brief>",
    "- Dev-Test   <what data it holds>",
    "",
    "## Constraints",
    "- <Regulatory regimes that apply>",
    "- <Maximum-sensitivity data element in scope>",
    "- <Residency or sovereignty constraint>",
    "- <Any hard date, and whether it is externally imposed>",
    "- <Material third parties>",
    "- <Whatever volumetrics already exist — TPS, GB/day, user counts, regions>",
  ]),
  NOTE("Silence is recorded, not ignored. A brief that never mentions non-production has not established that non-production is out of scope — the intake will say so, and every domain will carry it as an assumption until someone answers."),

  H2("5.2 Invoking the Master Architect"),
  P("For anything spanning two or more domains, or a whole direction."),
  ...CODE([
    "Use master-architect.",
    "",
    "Direction: <one line>",
    "Brief: briefs/<file>.md",
    "",
    "Run the engine first, then evaluate its reasoning. Specifically:",
    "  - Engage the Domain Architects for <domains you know are load-bearing>.",
    "  - The engine does not cover offensive security, human, physical or",
    "    emerging/specialised — engage those Architects if this direction touches them,",
    "    and tell me if it does not.",
    "",
    "I want back:",
    "  - The verdict and why.",
    "  - Cross-domain contradictions, and any Assumed state you found.",
    "  - The numbers that most need pinning, in priority order.",
    "  - The blocking questions with their named owners.",
    "",
    "Do not resolve a dependency by assumption. An unresolved dependency is a finding",
    "with an owner.",
  ]),

  H2("5.3 Invoking a Domain Architect"),
  ...CODE([
    "Use architect-<domain>.",
    "",
    "Context: <the position or brief they need>",
    "Question: <the specific thing this domain must decide or assess>",
    "",
    "Fan out to the SMEs this actually touches — not all of them. Work each in isolation.",
    "Reconcile any disagreement rather than averaging it, and tell me which fact",
    "separated them.",
    "",
    "Return: the domain position, which SMEs contributed what, open questions with",
    "owners, interoperability findings inside the domain, and any cross-domain",
    "dependency you could not resolve here.",
    "",
    "Do not assume another domain's position. State it as a dependency.",
  ]),

  H2("5.4 Invoking an SME"),
  ...CODE([
    "Use sme-<capability>.",
    "",
    "Context: <only what this capability needs — do not paste another SME's output>",
    "Question: <the specific question>",
    "",
    "Work in isolation. Return your position, what you refused to assume and why,",
    "your questions with the role that owns each, any same-domain routing request,",
    "and any cross-domain dependency.",
  ]),
  NOTE("The one mistake worth avoiding: pasting another SME's conclusion into an SME prompt as background. A primed SME confirms rather than assesses, and you lose the independent reading you engaged it for."),
  new Paragraph({children:[new PageBreak()]}));

/* ===================== 6. WORKED EXAMPLE ===================== */
A(H1("6. Worked example — AI agents in the CI/CD pipeline"),
  P("An agentic SDLC: agents that read repository content, propose code changes, run pipeline stages, and in later phases merge low-risk changes without a human reviewer. The pipeline deploys customer-facing services. Regulated under PRA and FCA with DORA applying; SS1/23 model risk governance in play; two external model providers, at least one material; agents read Restricted design records as grounding context."),
  P("This section is the actual output of a run, not an illustration.", {italics:true, color:"5B6572"}),

  H2("6.1 The run"),
  ...CODE(["python3 -m eas new --brief briefs/example-agentic-sdlc.md"]),
  TBL(["", ""], [
    ["Complexity", "T3 — multi-domain programme"],
    ["Verdict", "Not yet a base plate"],
    ["Contradictions", "0"],
    ["Gaps", "0"],
    ["Unpinned sizing-critical anchors", "65"],
    ["Blocking questions", "32"],
    ["Risks recorded", "42"],
    ["Orchestrator repairs", "2, both part of one coordinated pair"],
    ["Rough estimate", "15.5–35.8 months at ±40%"],
  ], [3400, 5626]),
  NOTE("Not yet a base plate is the correct first-run verdict, not a failure. Nobody has pinned any numbers. The useful output of a first run is the list of anchors to chase and the blocking questions to assign."),

  H2("6.2 The positions it reconciled to"),
  TBL(["Domain", "Position", "Note"], [
    ["IAM", "IAM-04 — Zero-trust identity fabric with mTLS and entitlement analytics", "Not the domain's own first choice — see 6.3"],
    ["NET", "NET-03 — Micro-segmented zero-trust network with identity-aware policy", "Not the domain's own first choice — see 6.3"],
    ["DATA", "DATA-02 — Customer-managed keys, per-flow classification, egress DLP", ""],
    ["INT", "INT-04 — Governed third-party integration tier with exit and concentration management", "The two model providers"],
    ["SEC", "SEC-04 — Type 1 detection sources and Type 2 compliance logging both delivered", ""],
    ["PLAT", "PLAT-02 — Signed artefacts, admission control, policy-gated IaC", ""],
    ["RES", "RES-02 — Active-passive multi-region with tested failover", ""],
    ["GRC", "GRC-03 — Full regulatory spine with model-risk governance and defensible scoring", "SS1/23"],
    ["ENV", "ENV-02 — Asserted parity with drift detection and enforced data policy", ""],
  ], [900, 4700, 3426]),

  H2("6.3 Where the orchestrator overruled the domains"),
  P("Two domains did not get their own highest-scoring option, and the substitution was a coordinated pair — neither move helped on its own:"),
  TBL(["Domain", "Wanted", "Got", "Why"], [
    ["IAM", "IAM-02 — central PDP", "IAM-04 — zero-trust identity fabric", "Agents act with an identity. Bounding what a compromised agent can reach needs identity strong enough to underpin per-hop policy, which IAM-02 does not deliver."],
    ["NET", "NET-02 — private connectivity, inspected egress", "NET-03 — micro-segmented, identity-aware", "Without per-service-pair policy keyed on workload identity, an agent that can reach the network can reach every service on it."],
  ], [1000, 1900, 2100, 4026]),
  P("This is the interrogation doing its job: the agentic pipeline's real risk is blast radius, and two domains that would each have chosen adequately in isolation were pulled up together because neither position contains an agent on its own."),

  H2("6.4 The security exposures it surfaced"),
  P("Filtered up out of the nine low-level designs into the exec pack. Five High, of which these are the ones specific to putting agents in the pipeline:"),
  TBL(["Source", "Exposure"], [
    ["GRC-03", "Models reachable from an untrusted input path can be manipulated through their inputs, and the manipulation is invisible in conventional application telemetry."],
    ["IAM-04", "The trust anchor becomes the single highest-value asset in the estate: compromise of it forges any workload identity."],
    ["PLAT-02", "Admission control enforced only in Prod makes non-prod the entry point for unverified artefacts — and non-prod is exactly where the agents run first."],
    ["SEC-04", "Type 1 requirements are dynamic by design. Coverage agreed at go-live decays as the threat landscape moves; a system well covered at launch can be poorly covered two years later without anything changing on either side."],
    ["DATA-02", "A key with broad blast radius makes key-management availability equivalent to data availability."],
  ], [1100, 7926]),

  H2("6.5 The timeline and workaround risks"),
  TBL(["Severity", "Source", "Risk"], [
    ["Critical", "IAM-04", "An identity fabric touches every workload, so its critical path runs through every delivery team at once. A single-team slip does not delay it, but a platform slip delays everyone."],
    ["Critical", "NET-03", "The policy set cannot be written before the service-pair inventory is complete, and on a brownfield estate that inventory is discovered by observing traffic over weeks, not read from documentation."],
    ["High", "INT-04", "An exit plan that exists on paper but has never been costed or rehearsed will not satisfy supervisory challenge, and the gap surfaces during a review rather than during design."],
    ["High", "INT-04", "Concentration through a shared fourth party is invisible in per-party assessments — relevant where two model providers may sit on the same underlying infrastructure."],
  ], [1100, 900, 7026]),

  H2("6.6 The roadmap it derived"),
  P("Waves are the layers of the dependency graph. A domain in a later wave starts once its providers are half-way through, which is when the interface it consumes is stable — full serialisation would produce a figure no delivery would recognise."),
  TBL(["Phase", "Weeks", "Elapsed"], [
    ["Mobilise, discover, answer the blocking questions", "6", "wk 0–6"],
    ["Wave 1: IAM", "44", "wk 6–50"],
    ["Wave 2: NET", "36", "wk 28–64"],
    ["Wave 3: DATA", "16", "wk 46–62"],
    ["Wave 4: INT", "18", "wk 54–72"],
    ["Wave 5: SEC", "20", "wk 63–83"],
    ["Wave 6: PLAT", "18", "wk 73–91"],
    ["Wave 7: RES, GRC, ENV", "22", "wk 82–104"],
    ["Assurance, rehearsal and evidence", "7", "wk 104–111"],
  ], [5426, 1800, 1800]),
  NOTE("Against a brief that commits to demonstrating the pattern by the end of the next financial year, a 15.5–35.8 month range is the finding. The identity and network work is what makes it long — and that is a scoping conversation to have now, not a date to defend later."),

  H2("6.7 The questions it will not answer for you"),
  P("Thirty-two blocking questions, each with a named owner. A representative selection:"),
  TBL(["Owner", "Question"], [
    ["Security Architect", "What is the blast radius if the fabric's trust anchor is compromised, and how is that anchor protected differently from everything else?"],
    ["Security Architect", "Which components cannot present a workload identity, and what boundary contains them instead?"],
    ["Platform Architect", "Is admission control enforcing in non-prod, or is non-prod the place unsigned artefacts get in?"],
    ["Platform Architect", "What happens to existing connections when the policy engine is unavailable — fail closed, or last-known-good?"],
    ["Network Architect", "Is the complete east-west service-pair inventory known, and how was it derived — from design, or from observed traffic?"],
    ["Model Risk", "Which decisions does this model influence, and at what materiality?"],
    ["Third-Party Risk", "Do several material parties depend on the same fourth party, creating concentration the individual assessments do not show?"],
  ], [1900, 7126]),

  H2("6.8 What the engine did not assess"),
  P("The run covers nine validator domains. For an agentic SDLC, two of the four uncovered domains matter directly and would be the next call:"),
  TBL(["Domain", "Why it matters here", "Engage"], [
    ["Emerging & Specialised", "Prompt injection, agent action bounding, model and embedding provenance. sme-ai-ml-security asks what untrusted content can reach the model's context and what the model can then cause to happen — the central question of an agentic pipeline.", "architect-emrg"],
    ["Offensive Security", "Nothing in the run validates that the containment actually holds. sme-purple-teaming asks which techniques have never been executed against the detections claiming to cover them.", "architect-offsec"],
    ["Human & Organisational", "Where agents merge without a reviewer, the question is what happens to a reported mistake. sme-security-culture asks it.", "architect-human"],
  ], [2000, 5026, 2000]),
  ...CODE([
    "Use architect-emrg.",
    "",
    "Context: projects/ai-agents-in-the-ci-cd-pipeline-agentic-sdlc-<date>/outputs/hld.md",
    "Question: the base plate covers nine domains and assesses nothing in AI/ML or",
    "agentic-system risk. Agents will hold repository commit rights, trigger pipeline",
    "stages, and later merge low-risk changes unreviewed. What does this design",
    "get wrong, and what has nobody asked?",
  ]),

  H2("6.9 Iterating"),
  P("The base plate is a living artefact until the verdict reaches Stable. Pin numbers and fix positions as answers land, and re-run — the change flows through the reconciliation and lands in both ledgers."),
  ...CODE([
    "python3 -m eas pin <project-id> secops \"Type 1 detection source volume\" \\",
    "                   \"180 GB/day\" \"20 GB/day\" \"2 GB/day\"",
    "python3 -m eas set <project-id> identity-access IAM-03   # if IAM-04 is unaffordable",
    "python3 -m eas run <project-id>",
  ]),
  P("A domain you fix by hand is never overruled — the orchestrator routes repairs through the other domains and reports whatever it could not reconcile. Setting IAM back to IAM-03 here would surface, rather than hide, what the network position then loses."),
  RULE(),
  RUNS([{t:"Generated from the framework's own output. The runs behind sections 4 and 6 are reproducible: same catalogue, brief, overrides and pins, same base plate.", size:19, italics:true, color:"5B6572"}]));

/* ===================== ASSEMBLE ===================== */
const doc = new Document({
  creator: "Enterprise Architect Strategy framework",
  title: "Enterprise Architect Strategy — setup, flow and worked examples",
  styles: {default: {document: {run: {font: "Calibri", size: 21, color: "1A1A1A"}}}},
  numbering: {config: [
    {reference: "bul", levels: [
      {level:0, format: LevelFormat.BULLET, text:"•", alignment: AlignmentType.LEFT,
       style:{paragraph:{indent:{left:400, hanging:220}}}},
      {level:1, format: LevelFormat.BULLET, text:"–", alignment: AlignmentType.LEFT,
       style:{paragraph:{indent:{left:760, hanging:220}}}}]},
    {reference: "num", levels: [
      {level:0, format: LevelFormat.DECIMAL, text:"%1.", alignment: AlignmentType.LEFT,
       style:{paragraph:{indent:{left:400, hanging:220}}}}]},
  ]},
  sections: [{
    properties: {page: {margin: {top: 1134, bottom: 1134, left: 1440, right: 1440}}},
    footers: {default: new (require('docx').Footer)({children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({children: [PageNumber.CURRENT], size: 17, color: "8A93A0"})]})]})},
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(process.argv[2], buf);
  console.log("wrote", process.argv[2], buf.length, "bytes");
});
