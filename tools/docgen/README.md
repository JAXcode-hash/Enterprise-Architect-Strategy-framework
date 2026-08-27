# Setup document generator

Rebuilds `docs/eas-setup-and-flow.docx`. The three parts append to one shared
`children` array; `part3.js` requires `part2.js`, which requires `build_docx.js`,
so running part3 assembles the whole document.

```bash
npm install docx          # only dependency, and only for regenerating the document
node tools/docgen/part3.js docs/eas-setup-and-flow.docx
```

The figures in sections 4 and 6 come from real runs of the two example briefs.
If the catalogue changes, re-run those briefs and update the numbers rather than
letting the document drift from what the engine actually produces:

```bash
python3 -m eas new --brief briefs/example-sase-migration.md
python3 -m eas new --brief briefs/example-agentic-sdlc.md
```
