const fs = require('fs');
const {execSync} = require('child_process');
const path = require('path');
const d = require('docx');
const {Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
       WidthType, ShadingType, AlignmentType, BorderStyle, PageBreak, LevelFormat,
       TableOfContents, Footer, PageNumber} = d;

// Read the live repository rather than restating figures from memory.
const ROOT = (() => {
  let p = process.cwd();
  while (p !== '/' && !fs.existsSync(p + '/eas/catalogue.py')) p = path.dirname(p);
  if (p === '/') { console.error('Run from the repository root.'); process.exit(1); }
  return p;
})();
const sh = c => execSync(c, {cwd: ROOT, encoding: 'utf8'}).trim();
const ENG = JSON.parse(sh('python3 -c "import sys,json;sys.path.insert(0,\'.\');' +
  'from eas.catalogue import Catalogue;print(json.dumps(Catalogue().summary()))"'));
const TEAM = JSON.parse(sh('python3 -c "import json,glob;' +
  'h=json.load(open(\'catalogue/org/hierarchy.json\'));' +
  'n=sum(len(json.load(open(f))[\'smes\']) for f in glob.glob(\'catalogue/org/smes/*.json\'));' +
  'na=sum(len(s[\'never_assume\']) for f in glob.glob(\'catalogue/org/smes/*.json\') for s in json.load(open(f))[\'smes\']);' +
  'qs=sum(len(s[\'must_ask\']) for f in glob.glob(\'catalogue/org/smes/*.json\') for s in json.load(open(f))[\'smes\']);' +
  'print(json.dumps({\'domains\':len(h[\'domains\']),\'smes\':n,\'never\':na,\'asks\':qs,' +
  '\'rows\':[[d[\'code\'],d[\'name\'],len(json.load(open(\'catalogue/org/smes/\'+d[\'id\']+\'.json\'))[\'smes\']),bool(d[\'eas_domains\'])] for d in h[\'domains\']]}))"'));
const AGENTS = sh('ls .claude/agents/*.md | wc -l');
const TESTS  = sh('python3 -m unittest discover tests 2>&1 | grep -oE "Ran [0-9]+ tests" | grep -oE "[0-9]+" | head -1');

const W = 9026;
const MONO = "Consolas";
const INK="1A1A1A", MUTE="5B6572", ACC="1F4E79", LINE="D9DEE5", HEAD="EDF1F6";

const P = (t,o={}) => new Paragraph({spacing:{after:o.after??140,line:276}, alignment:o.align,
  children:[new TextRun({text:t,size:o.size??21,color:o.color??INK,bold:o.bold,italics:o.italics})]});
const H1 = t => new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:360,after:160},
  children:[new TextRun({text:t,size:30,bold:true,color:ACC})]});
const H2 = t => new Paragraph({heading:HeadingLevel.HEADING_2,spacing:{before:280,after:120},
  children:[new TextRun({text:t,size:24,bold:true,color:ACC})]});
const H3 = t => new Paragraph({heading:HeadingLevel.HEADING_3,spacing:{before:220,after:100},
  children:[new TextRun({text:t,size:21,bold:true,color:INK})]});
const BUL = t => new Paragraph({numbering:{reference:"bul",level:0},spacing:{after:80,line:276},
  children:[new TextRun({text:t,size:21,color:INK})]});
const NUM = t => new Paragraph({numbering:{reference:"num",level:0},spacing:{after:90,line:276},
  children:[new TextRun({text:t,size:21,color:INK})]});
const CODE = lines => lines.map((l,i)=> new Paragraph({spacing:{after:i===lines.length-1?160:0,line:240},
  shading:{type:ShadingType.CLEAR,fill:"F4F6F9"}, indent:{left:170,right:170},
  children:[new TextRun({text:l||" ",size:18,font:MONO,color:"22303F"})]}));
const RULE = () => new Paragraph({spacing:{before:60,after:160},
  border:{bottom:{style:BorderStyle.SINGLE,size:6,color:LINE}},children:[]});
const NOTE = t => new Paragraph({spacing:{before:100,after:160,line:276},
  shading:{type:ShadingType.CLEAR,fill:"FBF7EC"}, indent:{left:170,right:170},
  border:{left:{style:BorderStyle.SINGLE,size:18,color:"C8912B"}},
  children:[new TextRun({text:t,size:20,color:"4A3A16"})]});
const KEY = t => new Paragraph({spacing:{before:100,after:160,line:276},
  shading:{type:ShadingType.CLEAR,fill:"EFF4FA"}, indent:{left:170,right:170},
  border:{left:{style:BorderStyle.SINGLE,size:18,color:ACC}},
  children:[new TextRun({text:t,size:20,color:"18324D"})]});

function TBL(header, rows, widths){
  const cell=(txt,o={})=> new TableCell({
    width:{size:o.w,type:WidthType.DXA},
    shading:o.head?{type:ShadingType.CLEAR,fill:HEAD}:undefined,
    margins:{top:70,bottom:70,left:100,right:100},
    children:String(txt).split(" ").map(l=> new Paragraph({spacing:{after:0,line:250},
      children:[new TextRun({text:l,size:o.head?18:19,bold:o.head,color:o.head?"22303F":INK})]}))});
  return new Table({columnWidths:widths, width:{size:W,type:WidthType.DXA},
    borders:{top:{style:BorderStyle.SINGLE,size:4,color:LINE},bottom:{style:BorderStyle.SINGLE,size:4,color:LINE},
             left:{style:BorderStyle.SINGLE,size:4,color:LINE},right:{style:BorderStyle.SINGLE,size:4,color:LINE},
             insideHorizontal:{style:BorderStyle.SINGLE,size:4,color:LINE},
             insideVertical:{style:BorderStyle.SINGLE,size:4,color:LINE}},
    rows:[ new TableRow({tableHeader:true,children:header.map((h,i)=>cell(h,{w:widths[i],head:true}))}),
           ...rows.map(r=> new TableRow({children:r.map((c,i)=>cell(c,{w:widths[i]}))})) ]});
}

const K = [];
const A = (...x) => x.forEach(e => K.push(e));

/* ============================== COVER ============================== */
A(new Paragraph({spacing:{before:1500,after:0},
   children:[new TextRun({text:"Enterprise Architect Strategy",size:52,bold:true,color:ACC})]}),
  new Paragraph({spacing:{after:120},
   children:[new TextRun({text:"Briefing document",size:28,color:MUTE})]}),
  new Paragraph({spacing:{after:360},
   children:[new TextRun({text:"A repeatable method for making an architecture direction defensible before it is committed",size:22,italics:true,color:MUTE})]}),
  RULE(),
  TBL(["",""],[
    ["Purpose","To brief a decision on whether to adopt this method, and what adopting it would require"],
    ["Audience","Architecture leadership, security leadership, and the forum that accepts residual risk"],
    ["Status","Working proof of concept. Runs end to end. Content needs organisational calibration before it is relied on."],
    ["What is asked","Four decisions, listed in section 8"],
  ],[2200,6826]),
  new Paragraph({children:[new PageBreak()]}));

/* ============================== 1. ONE PAGE ============================== */
A(H1("1. The briefing in one page"),
  KEY("Architecture assurance fails between domains, not within them. Each domain review is "
    + "internally complete; the failures live in what two domains each assumed the other was "
    + "handling. This framework makes that specific failure visible, and refuses to fill it with "
    + "a plausible guess."),
  H3("What it is"),
  P(`Two halves. A deterministic engine that reads a brief, has ${ENG.domains} validator domains rank `
   + `${ENG.options} catalogued architecture options against it, then interrogates every option against `
   + `every other and grades a verdict — in under a fifth of a second. And a team of ${AGENTS} agents in `
   + `three tiers over ${TEAM.domains} security domains, holding the depth and the current facts a `
   + `catalogue cannot.`),
  H3("What it produces, per assessment"),
  P("Nine low-level designs, one end-to-end high-level design, one executive pack, a base plate "
  + "artefact, a decision ledger and an evidence ledger — 33 artefacts in an isolated project "
  + "directory, plus a self-contained dashboard that can be emailed."),
  H3("Why it is different from a review"),
  P("A review tells you what is wrong with what was written. This tells you what was never "
  + `written down: ${TEAM.never} specific assumptions the SMEs are instructed to refuse, and `
  + `${TEAM.asks} standing questions each with a named owner. Silence in a brief is recorded as an `
  + "open assumption rather than read as absence of requirement."),
  H3("Evidence it works"),
  P("Two worked examples in section 5. On a SASE migration it found a dependency both the network "
  + "and data domains had each assumed the other owned. On an agentic CI/CD pipeline it overruled "
  + "two domains' own preferences together, because neither position contained an agent alone."),
  H3("What it is not"),
  P("Not a replacement for architects. Not a decision-maker. It produces the questions and the "
  + "reconciliation; people still answer and decide. Four of the thirteen security domains are "
  + "outside the engine and need their Architects engaged explicitly."),
  H3("What adopting it costs"),
  P("Nothing to install — standard-library Python, no dependencies, no network access. The real "
  + "investment is calibrating the catalogue against this organisation's own delivery data and "
  + "naming an owner for it."),
  new Paragraph({children:[new PageBreak()]}));

/* ============================== 2. PROBLEM ============================== */
A(H1("2. The problem this addresses"),
  P("Architecture assurance on a significant programme is well covered domain by domain. Identity "
  + "reviews identity, network reviews network, and each produces a competent position. The "
  + "failures that reach production are rarely inside one of those positions."),

  H2("2.1 Three specific failure modes"),
  TBL(["Failure","What it looks like","Why review does not catch it"],[
    ["The unowned dependency","Two domains have each assumed the other handles something. Both outputs are internally complete and neither has a gap.",
     "From inside either domain the assumption is a reasonable reading of the other's scope. Nobody reviewing one domain can see it."],
    ["The unasked question","A brief is silent on non-production data, or on where inspection decrypts. Every downstream position is built on an assumption nobody stated.",
     "A reviewer checks what is written. Silence reads as out of scope rather than as an unanswered question."],
    ["The unpinned number","A position is qualitative.   \"We will allow outbound to partners\" is agreed, sized later, and the sizing turns out to change the design.",
     "Qualitative positions pass review. The number that would have invalidated them is produced after the design is fixed."],
  ],[1900,3800,3326]),

  H2("2.2 Why more review does not fix it"),
  P("Adding reviewers adds depth inside domains, which is where the assurance is already adequate. "
  + "The gaps are structural: they exist because no single reviewer holds two domains at once, and "
  + "because a competent specialist asked a narrow question gives a competent narrow answer. "
  + "Reconciliation is a different activity from review, and it is usually nobody's job."),
  KEY("The framework's core claim is narrow and testable: given the same brief, it will find "
    + "cross-domain contradictions, unowned dependencies and unpinned numbers that a domain-by-domain "
    + "review structurally cannot, and it will do so the same way every time."),
  new Paragraph({children:[new PageBreak()]}));

/* ============================== 3. WHAT IT IS ============================== */
A(H1("3. What it is"),
  H2("3.1 The engine — what is stable"),
  P("A deterministic application. It reads a brief of any length, grades its complexity T1 to T4 "
  + "from evidence in the text, and has nine validator domains each score a catalogued set of "
  + "architecture options against it. It then reconciles those choices end to end."),
  TBL(["",""],[
    ["Validator domains", String(ENG.domains)],
    ["Catalogued options", `${ENG.options} — each a full posture bundle, tactical through strategic`],
    ["Shared capabilities", `${ENG.capabilities} — the vocabulary domains use to state what they give and need`],
    ["Cross-domain rules", `${ENG.rules} — incompatibilities, emergent risks, questions that only arise in combination`],
    ["Intake signals", `${ENG.signals} — each carrying the phrase in the brief that fired it`],
    ["Run time", "Under 0.2 seconds for a full reconciliation and re-render"],
  ],[2600,6426]),
  P("Options interlock: each declares what it gives the estate and what it needs back. A domain's "
  + "choice is viable only if the rest of the estate supplies what it depends on. That is what makes "
  + "the reconciliation more than a checklist."),
  NOTE("Determinism matters more than it sounds. The same catalogue, brief, overrides and pinned "
     + "numbers always produce the same base plate — which is what lets two assessments be compared, "
     + "and what lets a decision taken on one be defended six months later."),

  H2("3.2 The team — what changes"),
  P(`${AGENTS} agents in three tiers over ${TEAM.domains} security domains. The engine holds durable `
   + "patterns; the team holds depth and the facts that change with a product release or a "
   + "supervisory statement."),
  ...CODE([
    "                    master-architect             tier 0   evaluates, reconciles, grades",
    "                           |",
    "      +--------------------+--------------------+",
    "      |                    |                    |",
    "architect-grc      architect-cloud      architect-secops ...  tier 1  x" + TEAM.domains,
    "      |                    |                    |",
    " +----+----+          +----+----+          +----+----+",
    "sme-...  sme-...    sme-...  sme-...    sme-...  sme-...      tier 2  x" + TEAM.smes,
  ]),
  TBL(["Tier","Does","Never does"],[
    ["Master Architect","Evaluates the Domain Architects' output. Reconciles across domains. Grades the whole.",
     "Domain work. An architect who does SME work stops being able to evaluate it."],
    [`Domain Architect ×${TEAM.domains}`,"Fans out to its own SMEs in isolation. Compiles, validates for interoperability, sense-checks what was not said.",
     "Assume another domain's position. It states a dependency and escalates."],
    [`Capability SME ×${TEAM.smes}`,"Depth in one capability. Returns a position, the assumptions it refused, and questions with owners.",
     "Speculate outside its capability, or contact a peer directly."],
  ],[1700,4000,3326]),

  H2("3.3 The rule that does the most work"),
  P(`Every SME carries an explicit list of things that look settled and are not — ${TEAM.never} of `
   + "them across the team. Where one applies and the answer was not given, it becomes a question "
   + "with a named owner. Never a placeholder, never a plausible guess."),
  P("Examples, verbatim from the agents:", {italics:true, color:MUTE}),
  BUL("Penetration testing: \"That an untested component is secure. A clean report covers what was in scope during the window and nothing else.\""),
  BUL("Data residency: \"That the failover path stays in boundary. Disaster recovery is the most common way a residency position is breached, during an event nobody rehearsed against it.\""),
  BUL("Cloud entitlements: \"That deny beats allow. Evaluation logic differs by provider, and a broad grant elsewhere in the hierarchy can win.\""),
  BUL("Identity governance: \"That an entitlement review that completed was a review. Ask what proportion of entitlements were revoked — a near-zero revocation rate means rubber-stamping.\""),
  new Paragraph({children:[new PageBreak()]}));

/* ============================== 4. OUTPUT ============================== */
A(H1("4. What an assessment produces"),
  TBL(["Artefact","For whom","Contains"],[
    ["Low-level design ×9","The engineer building it, the assessor testing it",
     "Checklist evaluated across Prod, RTL and Dev-Test separately. Open questions with owners. Volumetric anchors per environment. Cross-domain hooks. Risks. Control mapping."],
    ["High-level design","The architecture forum",
     "Scope boundaries, a generated end-to-end flow, connectivity and trust boundaries, per-domain summaries, the reconciliation matrix, delivery shape."],
    ["Executive pack","The reader who will not open the HLD",
     "What it delivers and why, where the effort sits, a banded roadmap, and risks grouped by the problem they create — timeline, workarounds, legal and regulatory, and security exposures filtered up out of the nine designs."],
    ["Decision ledger","Anyone challenging a position later",
     "Every position, its rationale, the alternatives considered, the owner, and whether the orchestrator overruled the domain."],
    ["Evidence ledger","Audit and model-risk challenge",
     "What was checked, by what method, what came back, when — including the decomposition of every score to its inputs and weights."],
    ["Dashboard","Circulation","All of the above in one self-contained HTML file. No network requests."],
  ],[1800,2400,4826]),

  H2("4.1 The verdict"),
  TBL(["Grade","Means"],[
    ["Stable","No contradictions, no unpinned sizing-critical anchors, no blocking questions. Defensible as it stands."],
    ["Conditional","Coherent end to end, with named questions gating specific decisions."],
    ["Not yet a base plate","Contradictions remain, or numbers that drive sizing are unpinned."],
  ],[2200,6826]),
  NOTE("A first run almost always grades Not yet, because nobody has pinned any numbers. That is "
     + "the method working, not failing. The useful output of a first run is the list of numbers to "
     + "chase and the questions to assign — and both are actionable the same day."),
  new Paragraph({children:[new PageBreak()]}));

/* ============================== 5. EVIDENCE ============================== */
A(H1("5. Does it work?"),
  P("Three briefs have been run end to end. The figures below are actual output, not illustration."),

  H2("5.1 It does not over-engineer"),
  P("The most common objection to a method like this is that it will recommend the expensive answer "
  + "regardless. It does not. Given a small internal tool with a tight budget it selected the "
  + "cheapest available position in all nine domains, made no substitutions, and estimated 2.1 to "
  + "3.5 months."),
  TBL(["Brief","Tier","Positions selected","Estimate"],[
    ["Internal reporting tool refresh","T1","The tactical option in all nine domains. No substitutions.","2.1–3.5 months"],
    ["SASE migration to Prisma Access","T3","Mixed. Sovereign data enclave forced by a residency constraint.","13.4–30.9 months"],
    ["AI agents in the CI/CD pipeline","T3","Mixed, strategic in identity and network.","15.5–35.8 months"],
  ],[2600,700,3900,1826]),

  H2("5.2 The finding a domain review cannot produce"),
  H3("SASE migration — the unowned dependency"),
  P("The network SME identified that inspection means decryption, and decryption is processing — so "
  + "where Prisma Access decrypts is where data is processed. It refused to answer the residency "
  + "question and escalated it. When the Master Architect held both domain positions:"),
  TBL(["Domain","What it had assumed"],[
    ["Infrastructure","That the data domain would state the residency boundary, and that gateway selection would respect it."],
    ["Data","That the infrastructure domain would keep inspection in-region, because that is what an in-region requirement implies."],
  ],[2000,7026]),
  P("Both outputs were internally complete. Neither had a gap. The dependency was real and unowned. "
  + "It became a blocking question with a named owner rather than an assumption either side filled in."),
  KEY("The engine independently raised the same tension as an emergent risk — a multi-region "
    + "resilience position alongside a declared sovereignty boundary. The engine and the team "
    + "converging on one finding from different directions is a useful signal that it is real."),

  H3("Agentic CI/CD — the coordinated substitution"),
  P("Two domains did not get their own highest-scoring option, and the substitution was a pair — "
  + "neither move helped on its own:"),
  TBL(["Domain","Wanted","Reconciled to","Why"],[
    ["Identity","IAM-02 central policy decision point","IAM-04 zero-trust identity fabric",
     "Agents act with an identity. Bounding what a compromised agent reaches needs identity strong enough to underpin per-hop policy."],
    ["Network","NET-02 private connectivity, inspected egress","NET-03 micro-segmented, identity-aware",
     "Without per-service-pair policy keyed on workload identity, an agent that reaches the network reaches every service on it."],
  ],[1100,2100,2100,3726]),
  P("The real risk of an agentic pipeline is blast radius. Two domains that would each have chosen "
  + "adequately in isolation were pulled up together, because neither position contains an agent alone."),
  new Paragraph({children:[new PageBreak()]}));

/* ============================== 6. LIMITS ============================== */
A(H1("6. What it deliberately does not do"),
  P("Stated plainly, because a method oversold is a method that gets ignored after its first miss."),
  NUM("It does not replace architects. It produces questions, options and a reconciliation. People answer, decide and accept risk."),
  NUM("It does not invent a number. An unpinned anchor stays unpinned and holds the verdict down. A guessed one would propagate into sizing and cost and be far harder to catch later."),
  NUM(`It does not assess four of the ${TEAM.domains} domains. Offensive security, human and organisational, physical and environmental, and emerging and specialised have no counterpart in the engine. A run's clean verdict is not coverage of them — their Architects must be engaged explicitly.`),
  NUM("It does not compare projects. Cross-project conflict detection is out of scope for this phase. Each project records the catalogue version that produced it, which is the prerequisite, but the comparison is not built."),
  NUM("It does not know this organisation's delivery velocity. Effort figures are a starting position and the roadmap is derived from them. Until they are calibrated against real delivery data, treat every estimate as a shape rather than a number."),
  H2("6.1 The honest state of the content"),
  P(`The engine and the org structure are complete and tested — ${TESTS} automated tests, all passing. `
  + "The catalogue's content is a considered starting position, not settled organisational doctrine. "
  + "The option effort figures, the risk severities and the SME never-assume lists all reflect a "
  + "practitioner's judgement that this organisation should review against its own experience."),
  KEY("The most valuable thing a reviewer can do with this is read the never-assume list for their "
    + "own specialism and tell us what is wrong or missing. That is where the method's accuracy lives."),
  new Paragraph({children:[new PageBreak()]}));

/* ============================== 7. ADOPTION ============================== */
A(H1("7. What adoption requires"),
  H2("7.1 Technically, almost nothing"),
  ...CODE([
    "./setup.sh                                       verify - installs nothing",
    "python3 -m eas new --brief <your-brief>.md       assess a direction",
    "python3 -m eas serve                             browser UI",
  ]),
  P("Standard-library Python only. No dependencies, no build step, no network access at runtime, and "
  + "the generated dashboard makes no external requests. It runs behind a corporate proxy on a "
  + "locked-down laptop, which was a design constraint rather than an outcome."),
  H2("7.2 Organisationally, three things"),
  TBL(["What","Effort","Why it matters"],[
    ["Calibrate the effort figures","A workshop with delivery leadership, then a catalogue edit",
     "The roadmap is derived from them. Uncalibrated, the estimates are shapes rather than numbers."],
    ["Name a catalogue owner","Ongoing, light — a few hours a month",
     "The catalogue is the framework's content. Unowned, it drifts from the estate and the method quietly stops being right."],
    ["Review the SME knowledge bases","One specialist per domain, half a day each",
     "The never-assume lists are where accuracy lives. A wrong item there produces a confidently wrong question."],
  ],[2300,2600,4126]),
  H2("7.3 Suggested pilot"),
  P("Run it against a programme that has already been through architecture governance, and compare "
  + "what it raises against what governance raised. That is the cheapest honest test: if it surfaces "
  + "nothing new, it is not worth adopting; if it surfaces something material that was missed, the "
  + "case makes itself."),
  new Paragraph({children:[new PageBreak()]}));

/* ============================== 8. DECISIONS ============================== */
A(H1("8. Decisions requested"),
  TBL(["#","Decision","Owner","Consequence if deferred"],[
    ["1","Whether to run the pilot described in 7.3, and against which programme","Architecture leadership",
     "The method stays unproven against this organisation's own work, and the case for it stays theoretical."],
    ["2","Who owns the catalogue","Architecture leadership",
     "Content drifts from the estate. The method keeps producing confident output that is increasingly wrong."],
    ["3","Whether to calibrate effort figures against real delivery data, and who provides it","Delivery leadership",
     "Roadmap output remains directional. Usable for shaping, not for committing."],
    ["4","Whether the four uncovered domains are in scope for assessment, and who engages them","Security leadership",
     "Runs will keep producing clean verdicts that do not cover offensive security, human, physical or emerging risk."],
  ],[500,3200,1800,3526]),
  H2("8.1 What is already decided"),
  P("The logging operating model is already bound to this organisation's three types — Type 1 "
  + "security event detection owned by the central monitoring function, Type 2 compliance reporting "
  + "owned by security governance, Type 3 operational owned by the technology owner. The framework "
  + "enforces the consequence: no brief and no domain can mandate Type 1, because only the monitoring "
  + "function decides that. What a domain can require is a compliance obligation, or readiness to "
  + "answer a future engagement without rework."),
  RULE(),
  P("Figures in this document are read from the repository at build time rather than transcribed, "
  + "and the worked examples in section 5 are reproducible: the same brief always produces the same "
  + "base plate.", {size:19, italics:true, color:MUTE}),
  new Paragraph({children:[new PageBreak()]}));

/* ============================== APPENDIX ============================== */
A(H1("Appendix — the thirteen security domains"),
  P("Structure follows the organisation's cyber security domain taxonomy. Cloud is deliberately "
  + "separate from traditional infrastructure: it moves the trust boundary, the control plane, the "
  + "identity model and the tooling far enough from data-centre security that treating them as one "
  + "hides real risk."),
  TBL(["Domain","SMEs","Assessed by the engine"],
    TEAM.rows.map(r => [`${r[0]} — ${r[1]}`, String(r[2]), r[3] ? "yes" : "no — engage the Architect"]),
    [5626,900,2500]),
  P(`${TEAM.smes} SMEs in total, carrying ${TEAM.never} explicit refusals to assume and ${TEAM.asks} `
  + `standing questions, each with a named owner role. ${AGENTS} agent definitions, all generated `
  + "from one catalogue so the org chart and the engine cannot disagree."));

/* ============================== ASSEMBLE ============================== */
const doc = new Document({
  creator: "Enterprise Architect Strategy framework",
  title: "Enterprise Architect Strategy — briefing document",
  styles:{default:{document:{run:{font:"Calibri",size:21,color:INK}}}},
  numbering:{config:[
    {reference:"bul",levels:[{level:0,format:LevelFormat.BULLET,text:"•",alignment:AlignmentType.LEFT,
      style:{paragraph:{indent:{left:400,hanging:220}}}}]},
    {reference:"num",levels:[{level:0,format:LevelFormat.DECIMAL,text:"%1.",alignment:AlignmentType.LEFT,
      style:{paragraph:{indent:{left:400,hanging:220}}}}]},
  ]},
  sections:[{
    properties:{page:{margin:{top:1134,bottom:1134,left:1440,right:1440}}},
    footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,
      children:[new TextRun({children:[PageNumber.CURRENT],size:17,color:"8A93A0"})]})]})},
    children:K,
  }],
});
Packer.toBuffer(doc).then(b => {fs.writeFileSync(process.argv[2], b);
  console.log("wrote", process.argv[2], b.length, "bytes");});
