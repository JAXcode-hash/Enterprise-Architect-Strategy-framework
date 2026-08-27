const fs = require('fs');
const d = require('docx');
const {Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
       WidthType, ShadingType, AlignmentType, BorderStyle, PageBreak, LevelFormat,
       TableOfContents, Footer, PageNumber} = d;

const W = 9026;                     // A4 content width in DXA
const MONO = "Consolas";
const INK = "1A1A1A", MUTE = "5B6572", ACC = "1F4E79", LINE = "D9DEE5", HEAD = "EDF1F6";

const P = (t, o={}) => new Paragraph({
  spacing: {after: o.after ?? 140, line: 276},
  alignment: o.align, indent: o.indent,
  children: [new TextRun({text: t, size: o.size ?? 21, color: o.color ?? INK,
                          bold: o.bold, italics: o.italics, font: o.font})]
});
const RUNS = (runs, o={}) => new Paragraph({
  spacing: {after: o.after ?? 140, line: 276}, indent: o.indent,
  children: runs.map(r => new TextRun({text: r.t, size: r.size ?? 21, color: r.color ?? INK,
                                       bold: r.bold, italics: r.italics, font: r.font}))
});
const H1 = t => new Paragraph({heading: HeadingLevel.HEADING_1, spacing: {before: 360, after: 160},
  children: [new TextRun({text: t, size: 30, bold: true, color: ACC})]});
const H2 = t => new Paragraph({heading: HeadingLevel.HEADING_2, spacing: {before: 280, after: 120},
  children: [new TextRun({text: t, size: 24, bold: true, color: ACC})]});
const H3 = t => new Paragraph({heading: HeadingLevel.HEADING_3, spacing: {before: 220, after: 100},
  children: [new TextRun({text: t, size: 21, bold: true, color: INK})]});
const BUL = (t, lvl=0) => new Paragraph({
  numbering: {reference: "bul", level: lvl}, spacing: {after: 80, line: 276},
  children: [new TextRun({text: t, size: 21, color: INK})]});
const NUM = t => new Paragraph({
  numbering: {reference: "num", level: 0}, spacing: {after: 80, line: 276},
  children: [new TextRun({text: t, size: 21, color: INK})]});
const CODE = lines => lines.map((l, i) => new Paragraph({
  spacing: {after: i === lines.length - 1 ? 160 : 0, line: 240},
  shading: {type: ShadingType.CLEAR, fill: "F4F6F9"},
  indent: {left: 170, right: 170},
  children: [new TextRun({text: l || " ", size: 18, font: MONO, color: "22303F"})]}));
const RULE = () => new Paragraph({spacing: {before: 60, after: 160},
  border: {bottom: {style: BorderStyle.SINGLE, size: 6, color: LINE}}, children: []});
const NOTE = t => new Paragraph({
  spacing: {before: 100, after: 160, line: 276},
  shading: {type: ShadingType.CLEAR, fill: "FBF7EC"},
  indent: {left: 170, right: 170},
  border: {left: {style: BorderStyle.SINGLE, size: 18, color: "C8912B"}},
  children: [new TextRun({text: t, size: 20, color: "4A3A16"})]});

function TBL(header, rows, widths) {
  const cell = (txt, o={}) => new TableCell({
    width: {size: o.w, type: WidthType.DXA},
    shading: o.head ? {type: ShadingType.CLEAR, fill: HEAD} : undefined,
    margins: {top: 70, bottom: 70, left: 100, right: 100},
    children: String(txt).split(" ").map(line => new Paragraph({
      spacing: {after: 0, line: 250},
      children: [new TextRun({text: line, size: o.head ? 18 : 19, bold: o.head,
                              color: o.head ? "22303F" : INK,
                              font: o.mono ? MONO : undefined})]}))
  });
  return new Table({
    columnWidths: widths,
    width: {size: W, type: WidthType.DXA},
    borders: {
      top:{style:BorderStyle.SINGLE,size:4,color:LINE}, bottom:{style:BorderStyle.SINGLE,size:4,color:LINE},
      left:{style:BorderStyle.SINGLE,size:4,color:LINE}, right:{style:BorderStyle.SINGLE,size:4,color:LINE},
      insideHorizontal:{style:BorderStyle.SINGLE,size:4,color:LINE},
      insideVertical:{style:BorderStyle.SINGLE,size:4,color:LINE}},
    rows: [
      new TableRow({tableHeader: true,
        children: header.map((h, i) => cell(h, {w: widths[i], head: true}))}),
      ...rows.map(r => new TableRow({
        children: r.map((c, i) => cell(c, {w: widths[i], mono: /^`/.test(String(c))
          ? false : false}))}))
    ]
  });
}

const children = [];
const A = (...xs) => xs.forEach(x => children.push(x));

/* ===================== TITLE ===================== */
A(new Paragraph({spacing:{before:1800, after:0},
   children:[new TextRun({text:"Enterprise Architect Strategy", size:52, bold:true, color:ACC})]}),
  new Paragraph({spacing:{after:400},
   children:[new TextRun({text:"Setup, operating flow and worked examples", size:28, color:MUTE})]}),
  RULE(),
  RUNS([{t:"A repeatable method for standing up an architecture direction: a deterministic base-plate engine over nine validator domains, and a three-tier security architecture team of 80 agents over twelve. This document covers how to set it up, how work flows through it, where the hand-offs are, and what it produces.", size:22, color:MUTE}], {after:300}),
  TBL(["", ""], [
    ["Repository", "Enterprise-Architect-Strategy-framework"],
    ["Branch", "claude/enterprise-architect-strategy-app-8vp6mr"],
    ["Runtime", "Python 3.9+ standard library only — no dependencies"],
    ["Engine", "9 validator domains, 32 options, 60 capabilities, 33 cross-domain rules"],
    ["Team", "1 Master Architect, 12 Domain Architects, 67 capability SMEs"],
    ["Worked examples", "SASE migration to Prisma Access; AI agents in the CI/CD pipeline"],
  ], [2400, 6626]),
  new Paragraph({children:[new PageBreak()]}));

/* ===================== CONTENTS ===================== */
A(H1("Contents"),
  new TableOfContents("Contents", {hyperlink: true, headingStyleRange: "1-2"}),
  new Paragraph({children:[new PageBreak()]}));

/* ===================== 1. WHAT THIS IS ===================== */
A(H1("1. What this is"),
  P("Two halves that do different jobs, deliberately kept apart."),

  H2("1.1 The engine — what is stable"),
  P("A deterministic Python application. It reads a brief, grades its complexity, has nine validator domains each rank a set of catalogued options, then reconciles those options against each other end to end and grades a verdict. Same catalogue, brief, overrides and pins always produce the same base plate, which is what makes two runs comparable and a decision defensible."),
  P("It produces three levels of output from one run:"),
  TBL(["Output", "For whom"], [
    ["outputs/lld/<domain>.md ×9", "The engineer building it and the assessor testing it. Checklist across Prod/RTL/Dev-Test, further-questioning with owners, volumetric anchors per environment, cross-domain hooks, risks, control mapping."],
    ["outputs/hld.md", "The architecture forum. Scope boundaries, generated end-to-end flow, connectivity and trust boundaries, per-domain summaries, the N×N reconciliation matrix, delivery shape."],
    ["outputs/exec-pack.md", "The reader who will not open the HLD. What it delivers and why, where the effort sits, a banded roadmap, and risks grouped by the kind of problem they create — timeline, workarounds, legal and regulatory, and security exposures filtered up out of the low-level designs."],
    ["registers/", "The dual ledger — decisions and the evidence behind them — plus risk and question backlogs as CSV."],
    ["index.html", "A self-contained dashboard holding all of the above. No network requests; send it as a file."],
  ], [2400, 6626]),

  H2("1.2 The team — what changes"),
  P("Above the engine sits an organisation of agents: SME depth that can be rationalised and sense-checked against other SMEs' knowledge, with an orchestration layer whose job is to stop anybody assuming anything they were not told."),
  ...CODE([
    "                    master-architect                 tier 0   evaluates, reconciles, grades",
    "                           |",
    "      +--------------------+--------------------+",
    "      |                    |                    |",
    "architect-grc        architect-iam        architect-secops ...  tier 1  x12",
    "      |                    |                    |",
    " +----+----+          +----+----+          +----+----+",
    "sme-...  sme-...    sme-...  sme-...    sme-...  sme-...        tier 2  x67",
  ]),
  P("The division is the point: the engine holds durable patterns in a catalogue, the SMEs hold the depth and the facts that change with a product release or a supervisory statement.", {italics:true, color:MUTE}));

/* ===================== 2. SETUP ===================== */
A(H1("2. Setup"),
  H2("2.1 Prerequisites"),
  P("Python 3.9 or later. Nothing else. No pip install, no build step, no network access required at runtime — the framework has to run behind a corporate proxy on a locked-down laptop, and the generated dashboard makes no external requests."),

  H2("2.2 Install and verify"),
  ...CODE([
    "git clone <repo> && cd Enterprise-Architect-Strategy-framework",
    "git checkout claude/enterprise-architect-strategy-app-8vp6mr",
    "",
    "python3 -m eas lint                    # the catalogue must be coherent",
    "python3 -m unittest discover tests     # 61 tests",
    "python3 -m eas catalogue               # every domain and option",
  ]),
  NOTE("`eas lint` is not a formality. It refuses a catalogue where an option requires a capability nothing provides — an unsatisfiable requirement is a catalogue bug that would otherwise surface as an unfixable run finding."),

  H2("2.3 Repository layout"),
  TBL(["Path", "Holds"], [
    ["catalogue/", "The framework's content as data — domains, the shared capability vocabulary, options per domain, cross-domain rules, intake signals, benefits."],
    ["catalogue/org/", "The org chart — hierarchy and protocols, plus 67 SME knowledge bases, one file per domain."],
    ["eas/", "The engine — intake, selector, orchestrator, roadmap, renderers, CLI, web server."],
    [".claude/agents/", "80 generated agents. Do not edit; edit catalogue/org/ and regenerate."],
    [".claude/skills/", "Twelve skills. The nine validators are generated from the catalogue."],
    ["briefs/", "Worked example briefs, simple through strategic."],
    ["projects/", "One isolated directory per assessment. Git-ignored."],
    ["tools/", "gen_skills.py and gen_agents.py — the generators."],
  ], [2400, 6626]),

  H2("2.4 Commands"),
  ...CODE([
    "# Create an isolated project from a brief and run it",
    "python3 -m eas new --brief briefs/example-sase-migration.md",
    "python3 -m eas new --text \"...\"          # inline",
    "cat brief.md | python3 -m eas new         # stdin",
    "",
    "# Work the project as answers land",
    "python3 -m eas list",
    "python3 -m eas set  <project-id> data-security DATA-04     # fix a domain's position",
    "python3 -m eas pin  <project-id> secops \"Type 2 compliance log volume\" \\",
    "                    \"420 GB/day\" \"40 GB/day\" \"5 GB/day\"",
    "python3 -m eas run  <project-id>                            # re-reconcile",
    "",
    "python3 -m eas serve --port 8000          # the same lifecycle in a browser",
    "",
    "# After changing the catalogue",
    "python3 -m eas lint && python3 tools/gen_skills.py && python3 tools/gen_agents.py",
  ]),

  H2("2.5 Project isolation"),
  P("Every request gets its own directory. A project reads and writes only within it; path escapes are refused rather than resolved. Each records the catalogue fingerprint that produced it, so a later phase can tell whether two projects were assessed against the same framework version before it tries to reconcile their strategies. Cross-project conflict detection is deliberately out of scope for this phase."),
  new Paragraph({children:[new PageBreak()]}));

/* ===================== 3. THE TEAM ===================== */
A(H1("3. The team and its routing rules"),
  H2("3.1 Which tier to engage"),
  TBL(["You have", "Engage", "Why"], [
    ["A question inside one capability", "sme-<capability>", "Depth, in isolation, with the assumptions it refused to make"],
    ["A question spanning one domain", "architect-<domain>", "It fans out to its own SMEs and reconciles them"],
    ["Anything touching two or more domains", "master-architect", "Only it can see what two domains have each assumed the other handles"],
    ["A whole architecture direction", "master-architect", "It runs the engine for the nine domains it covers and the Architects for the rest"],
  ], [2900, 2200, 3926]),
  P("Start at the lowest tier that can hold the whole question. Going straight to the Master Architect for a single-domain question wastes the independent check the tier exists to provide."),

  H2("3.2 The four rules that make it work"),
  P("These are enforced, not described. The protocol text lives once in catalogue/org/hierarchy.json and is stamped verbatim into all 80 agents, so an SME's understanding of when to escalate cannot drift from its Architect's understanding of when to accept. A test asserts it."),
  BUL("SMEs work in isolation. An SME must not speculate about another capability's position, even one it understands well. An Architect must not brief one SME with another's output before both have reported — a primed SME confirms rather than assesses."),
  BUL("Nothing is assumed. Every SME carries an explicit never-assume list: the specific things that look settled and are not. Where one applies and the answer was not given, it becomes a question with a named owner — never a placeholder and never a plausible guess."),
  BUL("Routing goes up, not sideways. A same-domain need returns a routing request to the Architect; a cross-domain need returns a dependency. An SME never contacts a peer and never resolves a cross-domain dependency itself."),
  BUL("Escalation is bounded. Anything resolvable inside a domain stays there. The Master Architect sees only cross-domain dependencies and caveats, which keeps it able to evaluate rather than participate."),

  H2("3.3 The state only the Master Architect can find"),
  TBL(["State", "Meaning"], [
    ["Satisfied", "One domain needs something, another supplies it, and both describe the same thing."],
    ["Contradiction", "Two domains have taken positions that cannot both hold. Blocking."],
    ["Gap", "A domain needs something no domain supplies. Becomes a question with an owner."],
    ["Assumed", "Two domains have each assumed the other handles it. The most dangerous state, because both outputs look complete."],
  ], [2000, 7026]),
  P("Assumed is the one neither Domain Architect can see, because from inside each domain the assumption looks like a reasonable reading of the other's scope. Section 4 shows exactly this happening on a real migration."),

  H2("3.4 Coverage against the engine"),
  P("Eight of the twelve security domains map onto the engine's nine validator domains. Four do not: offensive security, human and organisational, physical and environmental, and emerging and specialised. A base-plate run assesses nothing in them."),
  NOTE("A run's clean verdict is not coverage of those four domains. The Master Architect agent states this explicitly and a test asserts it keeps saying so — but on any real engagement it is the reviewer's job to check those Architects were engaged."),
  new Paragraph({children:[new PageBreak()]}));

module.exports = {children, A, H1, H2, H3, P, RUNS, BUL, NUM, CODE, RULE, NOTE, TBL, W,
                  Document, Packer, Paragraph, TextRun, HeadingLevel, PageBreak, LevelFormat,
                  AlignmentType, Footer, PageNumber, d};
