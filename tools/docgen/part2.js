const M = require('./build_docx.js');
const {A, H1, H2, H3, P, RUNS, BUL, NUM, CODE, RULE, NOTE, TBL,
       Document, Packer, Paragraph, TextRun, HeadingLevel, PageBreak, LevelFormat,
       AlignmentType, Footer, PageNumber, d, children} = M;
const fs = require('fs');

/* ===================== 4. THE FLOW — SASE ===================== */
A(H1("4. The flow and its hand-offs"),
  P("Worked against a real shape of problem: migrating internet egress and private application access from a colocation stack to Palo Alto Prisma Access, for an organisation with colo egress today, workloads in GCP, Azure and AWS, remote users, and eleven regions whose requirements genuinely differ."),

  H2("4.1 The situation"),
  TBL(["Element", "Today", "Target"], [
    ["Office egress", "Colo stack: perimeter firewalls, proxies, TLS inspection, DNS forwarders. End of life.", "Prisma Access, one policy set"],
    ["Remote users", "Backhauled over VPN, or not inspected at all", "Prisma Access mobile user gateways per region"],
    ["Cloud egress", "GCP, Azure and AWS each egress independently", "Service connections into Prisma Access"],
    ["Colo", "Internet egress plus private interconnect", "Private interconnect only"],
    ["Regions", "One policy set applied everywhere", "EU in-region inspection and retention; UK regulated under PRA/FCA; APAC local data handling and a different permitted-destination set; US highest throughput, loosest policy"],
  ], [1700, 3400, 3926]),
  P("Scale as briefed: ~14,000 remote users at peak, 40 sites, 3 clouds, 11 regions, ~9 TB/day aggregate egress, ~2,400 allow-listed FQDNs."),

  H2("4.2 The flow"),
  P("Ten steps. Every arrow is a hand-off, and every hand-off carries something specific."),

  H3("Step 1 — Intake"),
  P("A human hands the brief to master-architect. Nothing is interpreted yet."),
  H3("Step 2 — Run the engine"),
  P("master-architect runs the engine, which grades the brief T3 and produces a base plate across the nine validator domains in under a second. This is the mechanical work; it is not the assessment."),
  ...CODE(["python3 -m eas new --brief briefs/example-sase-migration.md"]),
  P("Result: T3, verdict Not yet a base plate, 0 contradictions, 61 unpinned sizing-critical anchors, 30 blocking questions, estimate 13.4–30.9 months. The engine repaired two domain choices to reconcile: integration INT-04 → INT-02, and data DATA-03 → DATA-04, the sovereign enclave position, because the brief makes residency non-negotiable."),

  H3("Step 3 — Master to Domain Architect"),
  P("master-architect engages architect-infra, because on a SASE migration the network domain holds the load. The hand-off is the brief plus the engine's network position, plus the specific question: does this position survive eleven regions with different requirements?"),

  H3("Step 4 — Domain Architect fans out, in isolation"),
  P("architect-infra engages three SMEs separately, and does not show any of them another's output:"),
  BUL("sme-network-security — the egress, DNS and private connectivity position"),
  BUL("sme-endpoint-security — remote user device posture, since remote users are now in the inspection path"),
  BUL("sme-mobile-security — the mobile access path and certificate pinning"),

  H3("Step 5 — An SME refuses to assume"),
  P("sme-network-security returns its position and, from its never-assume list, three things it will not take on trust:"),
  TBL(["It will not assume", "So it asks"], [
    ["That the egress path is where the design says", "Where does outbound actually egress in each environment, and is it inspected there? Dev-Test currently egresses through a cloud NAT gateway with no inspection at all — is that in scope or accepted?"],
    ["That name resolution is intentional", "Does any name resolve differently across environments, and was that decided? The colo DNS forwarders are retiring and their behaviour is inherited, not documented."],
    ["That allow-listing constrains the destination", "2,400 FQDNs is the count — but how many are IP-range entries to shared cloud endpoints, which permit every tenant behind them?"],
  ], [2600, 6426]),

  H3("Step 6 — Same-domain hand-off, routed through the Architect"),
  P("sme-network-security needs to know whether remote user devices can carry a posture signal the SASE tier could use. It does not contact sme-endpoint-security. It returns a routing request to architect-infra, which decides to make it. This is a hand-off within the domain and it never reaches the Master Architect."),
  NOTE("This is the rule doing work. If the SME had asked its peer directly, the Architect would not have known the dependency existed, and it would not have appeared in the domain position."),

  H3("Step 7 — Cross-domain dependency, escalated not resolved"),
  P("sme-network-security identifies the thing that actually decides this migration: inspection means decryption, and decryption is processing. Where Prisma Access decrypts is where data is processed. That is a data residency question, and the network SME must not answer it."),
  P("It returns a cross-domain dependency. architect-infra confirms it cannot be resolved inside the infrastructure domain and escalates to master-architect with the specific dependency, the SME position that created it, and what it needs back — not the whole domain output."),

  H3("Step 8 — Master routes to the owning domain"),
  P("master-architect engages architect-data, which engages sme-data-residency in isolation. That SME's never-assume list produces the question nobody had asked:"),
  NOTE("\"Trace every failover and replication path — does any leave the declared boundary under any failure mode?\" Applied here: when an EU user roams to the US, which gateway decrypts their traffic, and does that put EU data through US processing? And when a regional gateway fails, where does its traffic fail over to?"),

  H3("Step 9 — The Assumed state surfaces"),
  P("master-architect now holds both domain positions and finds what neither Architect could see:"),
  TBL(["Domain", "What it assumed"], [
    ["Infrastructure", "That the data domain would state the residency boundary, and that Prisma Access gateway selection would respect it."],
    ["Data", "That the infrastructure domain would keep inspection in-region, because that is what an in-region requirement implies."],
  ], [2000, 7026]),
  P("Both domain outputs were internally complete. Neither had a gap. The dependency was real and unowned, and only the tier that sees both could find it. It becomes a blocking question with a named owner — Network Architect, with Legal Counsel — not an assumption either side fills in."),

  H3("Step 10 — The remaining domains, then grade"),
  TBL(["Architect", "Engaged because", "Key hand-off back"], [
    ["architect-iam", "Users now authenticate to the SASE tier itself", "sme-federation-sso: the federation trust inventory must include the new trust, and revocation latency for it must be stated"],
    ["architect-grc", "Prisma Access becomes a dependency for every user's traffic", "sme-third-party-risk: this is a materiality and probable CTP assessment, with a costed exit plan — the engine flagged the same thing"],
    ["architect-secops", "Logs move from the colo stack to Prisma Access", "sme-security-monitoring-siem: existing colo sources disappear. Which were Type 1, and has the monitoring function been told they are being replaced?"],
    ["architect-res", "The SASE tier is now on the path for all egress", "sme-disaster-recovery: what is the measured failover time between regional gateways, and does gateway failover cross a residency boundary?"],
  ], [1900, 2600, 4526]),
  P("master-architect grades the whole. The engine had already raised the same residency-versus-resilience tension as an emergent risk (rule R-E05: a multi-region resilience position alongside a declared sovereignty boundary), which is the engine and the team converging on the same finding from different directions — a useful signal that it is real."),

  H2("4.3 The hand-offs, summarised"),
  TBL(["#", "From", "To", "What is handed over"], [
    ["1", "Human", "master-architect", "The brief, uninterpreted"],
    ["2", "master-architect", "engine", "The brief; returns a base plate for 9 domains"],
    ["3", "master-architect", "architect-infra", "Brief, engine network position, and the specific question"],
    ["4", "architect-infra", "3 SMEs, separately", "The question only — no other SME's output"],
    ["5", "sme-network-security", "architect-infra", "Position, what it refused to assume, questions with owners"],
    ["6", "sme-network-security", "architect-infra → sme-endpoint-security", "A same-domain routing request. Stays in the domain."],
    ["7", "architect-infra", "master-architect", "One cross-domain dependency, with the position that created it"],
    ["8", "master-architect", "architect-data → sme-data-residency", "The specific dependency, not the whole infra output"],
    ["9", "master-architect", "—", "Reconciles both; finds the Assumed state neither could see"],
    ["10", "master-architect", "iam, grc, secops, res", "Scoped questions; then grades the whole"],
  ], [500, 2100, 2500, 3926]),
  new Paragraph({children:[new PageBreak()]}));

module.exports = {};
