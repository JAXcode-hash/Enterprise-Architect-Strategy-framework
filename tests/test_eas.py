"""Test suite. Stdlib unittest - `python3 -m unittest discover tests -v`."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from eas.catalogue import Catalogue                                  # noqa: E402
from eas.intake import run_intake, slugify                           # noqa: E402
from eas.orchestrator import find_violations, orchestrate            # noqa: E402
from eas.projects import Project                                     # noqa: E402
from eas.render.md2html import render as md2html                     # noqa: E402
from eas.roadmap import build_roadmap                                # noqa: E402
from eas.run import new_run                                          # noqa: E402
from eas.selector import rank_all                                    # noqa: E402

CAT = Catalogue()

SIMPLE = "Small internal reporting tool, tight budget, reuse existing platform, end of quarter."
REGULATED = (ROOT / "briefs" / "example-regulated.md").read_text()
STRATEGIC = (ROOT / "briefs" / "example-strategic.md").read_text()


class TestCatalogue(unittest.TestCase):
    def test_lints_clean(self):
        self.assertEqual(CAT.lint(), [], "catalogue must be coherent")

    def test_every_domain_has_options(self):
        for dom in CAT.domains:
            self.assertGreaterEqual(len(CAT.options_for(dom.key)), 3, dom.key)

    def test_every_requirement_is_satisfiable(self):
        provided = set()
        for o in CAT.options:
            provided |= CAT.expand(o.provides)
        for o in CAT.options:
            for cap in o.requires:
                self.assertIn(cap, provided, f"{o.id} requires unsatisfiable {cap}")

    def test_implication_map_expands(self):
        # A stronger position satisfies a weaker requirement.
        self.assertIn("data.nonprod.masked", CAT.expand(["data.nonprod.synthetic"]))
        self.assertIn("resilience.multi-az", CAT.expand(["resilience.multi-region"]))

    def test_no_option_may_require_type_1_logging(self):
        # Type 1 requirements belong to the central security monitoring function.
        # No initiative and no domain gets to demand one. A domain that needs
        # attribution requires ingestion compatibility; one that needs evidence
        # requires Type 2.
        for o in CAT.options:
            self.assertNotIn("secops.log.type1", o.requires,
                             f"{o.id} demands Type 1 - only the monitoring function decides that")

    def test_no_signal_may_mandate_type_1_logging(self):
        for key, spec in CAT.signals_def["signals"].items():
            self.assertNotIn("secops.log.type1", spec.get("mandates", []),
                             f"signal {key} mandates Type 1, which no brief can do")

    def test_delivering_centrally_implies_ingestion_compatibility(self):
        for cap in ("secops.log.type1", "secops.log.type2"):
            self.assertIn("secops.ingestion.compatible", CAT.expand([cap]),
                          f"{cap} must imply conformance to the ingestion standards")

    def test_every_domain_offers_a_spread_of_postures(self):
        for dom in CAT.domains:
            postures = {o.posture for o in CAT.options_for(dom.key)}
            self.assertGreaterEqual(len(postures), 2,
                                    f"{dom.key} offers only {postures} - no real choice")

    def test_options_carry_the_four_artefacts(self):
        for o in CAT.options:
            self.assertTrue(o.checklist, f"{o.id} has no checklist")
            self.assertTrue(o.questions, f"{o.id} has no further-questioning")
            self.assertTrue(o.anchors, f"{o.id} has no volumetric anchors")
            self.assertTrue(o.risks, f"{o.id} has no risks")


class TestIntake(unittest.TestCase):
    def test_complexity_scales_with_the_brief(self):
        tiers = [run_intake(b, CAT).tier for b in (SIMPLE, REGULATED, STRATEGIC)]
        self.assertEqual(tiers[0], "T1")
        self.assertIn(tiers[1], ("T3", "T4"))
        self.assertEqual(tiers[2], "T4")
        ranks = ["T1", "T2", "T3", "T4"]
        self.assertLess(ranks.index(tiers[0]), ranks.index(tiers[1]))
        self.assertLessEqual(ranks.index(tiers[1]), ranks.index(tiers[2]))

    def test_signals_carry_evidence_from_the_brief(self):
        intake = run_intake(REGULATED, CAT)
        for key, sig in intake.signals.items():
            if sig.inferred:
                continue
            self.assertTrue(sig.evidence.strip(), f"signal {key} fired with no evidence")

    def test_detects_the_constraints_that_matter(self):
        intake = run_intake(STRATEGIC, CAT)
        for key in ("data-residency", "ai-ml", "regulated", "non-prod-real-data",
                    "third-party-material", "multi-cloud"):
            self.assertTrue(intake.signal_on(key), f"missed signal {key}")

    def test_records_what_the_brief_did_not_say(self):
        intake = run_intake("We want to build a thing.", CAT)
        self.assertGreaterEqual(len(intake.unstated), 5)

    def test_mandates_derive_from_signals(self):
        intake = run_intake(STRATEGIC, CAT)
        self.assertIn("data.residency.in-region", intake.mandates)
        self.assertIn("grc.modelrisk.tiered", intake.mandates)

    def test_reads_structured_sections(self):
        intake = run_intake(REGULATED, CAT)
        self.assertTrue(intake.objects)
        self.assertTrue(intake.integrations)
        self.assertTrue(intake.constraints)
        self.assertTrue(any("Dev-Test" in e for e in intake.environments))

    def test_does_not_fire_a_signal_on_its_own_negation(self):
        # "No customer data" is not evidence of customer data. This false
        # positive used to propagate all the way into the selected architecture.
        intake = run_intake(
            "Small internal tool. No customer data. There is no PCI scope. "
            "Not internet-facing.", CAT)
        for key in ("pii", "pci", "internet-facing"):
            self.assertFalse(intake.signal_on(key), f"{key} fired on a negation")

    def test_still_fires_when_the_phrase_is_asserted(self):
        intake = run_intake("Customer data is in scope and PCI applies.", CAT)
        self.assertTrue(intake.signal_on("pii"))
        self.assertTrue(intake.signal_on("pci"))

    def test_slugify(self):
        self.assertEqual(slugify("Payments API: modernisation!"), "payments-api-modernisation")
        self.assertEqual(slugify(""), "untitled")


class TestSelector(unittest.TestCase):
    def test_scores_are_decomposable(self):
        intake = run_intake(REGULATED, CAT)
        for options in rank_all(CAT, intake).values():
            for o in options:
                self.assertAlmostEqual(o.score, round(sum(o.score_breakdown.values()), 3),
                                       places=3, msg=f"{o.id} score is not its breakdown")

    def test_constraint_briefs_pick_cheaper_postures(self):
        cheap = run_intake(SIMPLE, CAT)
        heavy = run_intake(STRATEGIC, CAT)
        cheap_top = rank_all(CAT, cheap)["identity-access"][0]
        heavy_top = rank_all(CAT, heavy)["identity-access"][0]
        self.assertLess(cheap_top.effort_rank, heavy_top.effort_rank)

    def test_ranking_is_stable(self):
        intake = run_intake(REGULATED, CAT)
        a = {k: [o.id for o in v] for k, v in rank_all(CAT, intake).items()}
        b = {k: [o.id for o in v] for k, v in rank_all(CAT, intake).items()}
        self.assertEqual(a, b)


class TestOrchestrator(unittest.TestCase):
    def _run(self, brief, **kw):
        intake = run_intake(brief, CAT)
        ranked = rank_all(CAT, intake)
        selection, recon = orchestrate(CAT, ranked, mandates=intake.mandates, **kw)
        return intake, ranked, selection, recon

    def test_reconciles_every_domain(self):
        _i, _r, selection, _recon = self._run(REGULATED)
        self.assertEqual(set(selection), set(CAT.domain_keys()))

    def test_deterministic(self):
        a = self._run(STRATEGIC)[2]
        b = self._run(STRATEGIC)[2]
        self.assertEqual({k: v.id for k, v in a.items()}, {k: v.id for k, v in b.items()})

    def test_resolves_the_mandates_a_brief_creates(self):
        # A sovereignty brief must end up with a position that actually delivers residency.
        intake, _r, selection, recon = self._run(STRATEGIC)
        provided = set()
        for o in selection.values():
            provided |= CAT.expand(o.provides)
        for cap in intake.mandates:
            self.assertIn(cap, provided, f"mandated {cap} left unsatisfied")
        self.assertEqual(recon.coverage["mandates_unmet"], 0)

    def test_never_overrules_a_locked_domain(self):
        _i, _r, selection, recon = self._run(
            STRATEGIC, overrides={"resilience": "RES-01", "data-security": "DATA-01"})
        self.assertEqual(selection["resilience"].id, "RES-01")
        self.assertEqual(selection["data-security"].id, "DATA-01")
        self.assertEqual(sorted(recon.coverage["locked_domains"]),
                         ["data-security", "resilience"])

    def test_detects_a_designed_contradiction(self):
        _i, _r, _s, recon = self._run(
            STRATEGIC, overrides={"data-security": "DATA-04", "resilience": "RES-03"})
        self.assertTrue(recon.contradictions, "sovereign + active-active must contradict")
        self.assertEqual(recon.verdict, "not-yet")

    def test_repairs_when_only_one_side_is_locked(self):
        _i, _r, selection, recon = self._run(STRATEGIC, overrides={"data-security": "DATA-04"})
        self.assertEqual(selection["data-security"].id, "DATA-04")
        self.assertEqual(recon.coverage["cells_contradiction"], 0)

    def test_pair_repair_escapes_a_single_swap_plateau(self):
        # Sovereignty forces both the data position and the non-prod data policy to move.
        _i, _r, selection, recon = self._run(STRATEGIC)
        self.assertEqual(selection["data-security"].id, "DATA-04")
        self.assertTrue(any(r.get("paired") for r in recon.repairs),
                        "expected a coordinated pair repair")

    def test_emergent_findings_need_a_combination(self):
        _i, _r, _s, recon = self._run(STRATEGIC)
        self.assertTrue(recon.emergent_risks or recon.emergent_questions)
        for r in recon.emergent_risks:
            self.assertTrue(r.emergent)
            self.assertIn("+", r.source, "an emergent risk names the combination that raised it")

    def test_worked_examples_reconcile_cleanly(self):
        # The three shipped briefs must reach a coherent position - no
        # contradictions and no unmet mandates - or the catalogue has a hole.
        for name in ("example-simple", "example-regulated", "example-strategic"):
            brief = (ROOT / "briefs" / f"{name}.md").read_text()
            _i, _r, _s, recon = self._run(brief)
            self.assertEqual(recon.coverage["cells_contradiction"], 0, name)
            self.assertEqual(recon.coverage["mandates_unmet"], 0, name)
            self.assertEqual(recon.gaps, [], f"{name}: {[g.detail for g in recon.gaps]}")

    def test_engagement_driven_posture_is_reachable_and_coherent(self):
        # The operating model makes "nothing forwarded until asked" a legitimate
        # position. A contained change should be able to take it cleanly.
        _i, _r, selection, recon = self._run(SIMPLE)
        self.assertEqual(selection["secops"].id, "SEC-01")
        self.assertEqual(recon.coverage["cells_contradiction"], 0)
        self.assertEqual(recon.coverage["mandates_unmet"], 0)

    def test_engagement_driven_posture_on_a_regulated_estate_is_challenged(self):
        # The same position on a regulated, exposed estate must not pass quietly:
        # it should leave the mandate unmet and raise the combination risks.
        _i, _r, selection, recon = self._run(REGULATED, overrides={"secops": "SEC-01"})
        self.assertEqual(selection["secops"].id, "SEC-01")
        self.assertGreater(recon.coverage["mandates_unmet"], 0,
                           "a regulated brief must still require Type 2 and ingestion readiness")
        sources = {r.source.split()[0] for r in recon.emergent_risks}
        self.assertIn("R-E16", sources, "IBS + engagement-driven must raise the evidence risk")
        self.assertTrue(any(r.severity == "C" for r in recon.emergent_risks))

    def test_a_hardened_estate_cannot_report_nothing(self):
        # Options that depend on central logging must be pulled down with it.
        _i, _r, unforced, _rec = self._run(REGULATED)
        _i2, _r2, forced, _rec2 = self._run(REGULATED, overrides={"secops": "SEC-01"})
        downgraded = [k for k in CAT.domain_keys()
                      if unforced[k].effort_rank > forced[k].effort_rank]
        self.assertGreaterEqual(len(downgraded), 3,
                                "forcing SEC-01 must cascade into the domains that need it")

    def test_matrix_is_square_and_complete(self):
        _i, _r, _s, recon = self._run(REGULATED)
        n = len(CAT.domain_keys())
        self.assertEqual(len(recon.cells), n * n)

    def test_verdict_moves_when_anchors_are_pinned(self):
        intake = run_intake(SIMPLE, CAT)
        ranked = rank_all(CAT, intake)
        _s, before = orchestrate(CAT, ranked, mandates=intake.mandates)
        self.assertEqual(before.verdict, "not-yet")
        self.assertTrue(before.unpinned)
        pins = {}
        for dom_key, anchors in before.anchors_by_domain.items():
            for a in anchors:
                if a.critical:
                    pins.setdefault(dom_key, {})[a.metric] = {
                        "prod": "1", "rtl": "1", "devtest": "1"}
        _s2, after = orchestrate(CAT, ranked, pins=pins, mandates=intake.mandates)
        self.assertEqual(after.unpinned, [])
        self.assertIn(after.verdict, ("conditional", "stable"))

    def test_unmet_requirement_is_found(self):
        # Hand-build an incoherent selection and confirm it is caught.
        intake = run_intake(REGULATED, CAT)
        ranked = rank_all(CAT, intake)
        broken = {k: next(o for o in ranked[k] if o.id == want)
                  for k, want in (("identity-access", "IAM-01"), ("integration", "INT-02"))}
        for k in CAT.domain_keys():
            broken.setdefault(k, ranked[k][0])
        violations = find_violations(CAT, broken)
        self.assertTrue(any(v.capability == "identity.pdp.central" for v in violations),
                        "INT-02 needs a central PDP that IAM-01 does not provide")


class TestRoadmap(unittest.TestCase):
    def _weeks(self, brief):
        intake = run_intake(brief, CAT)
        ranked = rank_all(CAT, intake)
        selection, _r = orchestrate(CAT, ranked, mandates=intake.mandates)
        return build_roadmap(CAT, selection, intake)["total_weeks"]

    def test_scales_with_complexity(self):
        simple, regulated, strategic = (self._weeks(b) for b in
                                        (SIMPLE, REGULATED, STRATEGIC))
        # A contained change must come out far shorter than an estate-level one.
        self.assertLess(simple * 3, regulated)
        self.assertLess(simple * 3, strategic)
        # Both of the heavy briefs are T4. Neither is inherently longer than the
        # other, so assert they land in the same ballpark rather than in an order
        # the framework does not actually guarantee.
        self.assertLess(abs(regulated - strategic) / max(regulated, strategic), 0.35)

    def test_stays_in_a_believable_range(self):
        intake = run_intake(STRATEGIC, CAT)
        ranked = rank_all(CAT, intake)
        selection, _r = orchestrate(CAT, ranked, mandates=intake.mandates)
        rm = build_roadmap(CAT, selection, intake)
        # A nine-domain strategic programme is over a year and under four.
        self.assertGreater(rm["total_weeks"], 52)
        self.assertLess(rm["total_weeks"], 208)
        self.assertLess(rm["range_weeks"][0], rm["total_weeks"])
        self.assertGreater(rm["range_weeks"][1], rm["total_weeks"])

    def test_phases_are_contiguous_and_ordered(self):
        intake = run_intake(REGULATED, CAT)
        ranked = rank_all(CAT, intake)
        selection, _r = orchestrate(CAT, ranked, mandates=intake.mandates)
        rm = build_roadmap(CAT, selection, intake)
        for p in rm["phases"]:
            self.assertLessEqual(p["starts_week"], p["ends_week"])
        self.assertEqual(rm["phases"][0]["starts_week"], 0)
        self.assertEqual(rm["phases"][-1]["ends_week"], rm["total_weeks"])


class TestMarkdown(unittest.TestCase):
    def test_tables_headings_and_inline(self):
        html = md2html("# H\n\n**b** `c`\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n- x\n")
        for fragment in ("<h1>H</h1>", "<strong>b</strong>", "<code>c</code>",
                         "<th>A</th>", "<td>1</td>", "<li>x</li>"):
            self.assertIn(fragment, html)

    def test_escapes_html_in_content(self):
        self.assertIn("&lt;script&gt;", md2html("<script>alert(1)</script>"))

    def test_escaped_pipes_survive_a_table_cell(self):
        html = md2html("| A |\n|---|\n| one \\| two |\n")
        self.assertIn("one | two", html)


class TestProjectIsolation(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_refuses_paths_that_escape(self):
        p = Project.create("t", "T", "brief", CAT.root, base=self.tmp)
        for bad in ("../escape.md", "/etc/passwd", "outputs/../../escape.md"):
            with self.assertRaises(ValueError, msg=bad):
                p.path(bad)

    def test_two_runs_do_not_cross_pollinate(self):
        a, _ = new_run(REGULATED, base=self.tmp, catalogue=CAT)
        b, _ = new_run(SIMPLE, base=self.tmp, catalogue=CAT)
        self.assertNotEqual(a.root, b.root)
        self.assertNotIn("Payments", b.read("brief.md"))
        self.assertNotIn("reporting tool", a.read("brief.md"))
        # Nothing written outside either project root.
        for proj in (a, b):
            for rel in proj.files():
                self.assertTrue((proj.root / rel).resolve().is_relative_to(proj.root))
        self.assertEqual(len(list(self.tmp.iterdir())), 2)

    def test_a_run_produces_every_deliverable(self):
        project, summary = new_run(REGULATED, base=self.tmp, catalogue=CAT)
        expected = {"brief.md", "project.json", "baseplate.json", "index.html",
                    "outputs/hld.md", "outputs/exec-pack.md", "outputs/base-plate.md",
                    "outputs/overview.md", "registers/decisions.md", "registers/evidence.md",
                    "registers/risks.csv", "registers/questions.csv",
                    "inputs/overrides.json", "inputs/anchors.json"}
        expected |= {f"outputs/lld/{k}.md" for k in CAT.domain_keys()}
        expected |= {f"options/{k}.md" for k in CAT.domain_keys()}
        self.assertTrue(expected.issubset(set(project.files())),
                        f"missing: {expected - set(project.files())}")
        self.assertIn(summary["verdict"], ("stable", "conditional", "not-yet"))

    def test_manifest_records_every_run(self):
        from eas.run import execute
        project, _ = new_run(SIMPLE, base=self.tmp, catalogue=CAT)
        execute(project, CAT)
        self.assertEqual(len(project.manifest["runs"]), 2)
        self.assertTrue(project.manifest["catalogue_fingerprint"])

    def test_dashboard_makes_no_external_requests(self):
        project, _ = new_run(SIMPLE, base=self.tmp, catalogue=CAT)
        page = project.read("index.html")
        for scheme in ("http://", "https://", "//cdn", "src=\"//"):
            self.assertNotIn(scheme, page, f"dashboard reaches out via {scheme}")

    def test_baseplate_json_is_complete(self):
        project, _ = new_run(REGULATED, base=self.tmp, catalogue=CAT)
        run = json.loads(project.read("baseplate.json"))
        for key in ("intake", "selection", "ranked", "reconciliation", "anchors",
                    "roadmap", "decisions", "evidence", "significant_effort"):
            self.assertIn(key, run)
        self.assertEqual(len(run["selection"]), 9)
        self.assertEqual(len(run["decisions"]), 9)


class TestRegisters(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.project, _ = new_run(REGULATED, base=self.tmp, catalogue=CAT)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_decision_ledger_covers_every_domain(self):
        text = self.project.read("registers/decisions.md")
        for dom in CAT.domains:
            self.assertIn(dom.name, text)

    def test_evidence_ledger_decomposes_scores(self):
        text = self.project.read("registers/evidence.md")
        self.assertIn("Breakdown", text)
        self.assertIn("Operability verdict graded", text)

    def test_risk_register_separates_emergent_risks(self):
        rows = self.project.read("registers/risks.csv").splitlines()
        self.assertGreater(len(rows), 20)
        self.assertIn("emergent", rows[0])


class TestSecurityArchitectureTeam(unittest.TestCase):
    """The org chart is data and the agents are generated from it."""

    ORG = ROOT / "catalogue" / "org"
    AGENTS = ROOT / ".claude" / "agents"

    @classmethod
    def setUpClass(cls):
        cls.h = json.loads((cls.ORG / "hierarchy.json").read_text())
        cls.smes = {
            d["id"]: json.loads((cls.ORG / "smes" / f"{d['id']}.json").read_text())["smes"]
            for d in cls.h["domains"]
        }

    def test_three_tiers_are_complete(self):
        self.assertEqual(len(self.h["domains"]), 12)
        self.assertEqual(sum(len(v) for v in self.smes.values()), 67)

    def test_every_agent_file_was_generated(self):
        expected = {"master-architect"}
        expected |= {f"architect-{d['id']}" for d in self.h["domains"]}
        expected |= {f"sme-{s['id']}" for v in self.smes.values() for s in v}
        actual = {p.stem for p in self.AGENTS.glob("*.md")}
        self.assertEqual(expected - actual, set(), "missing agents - run tools/gen_agents.py")
        self.assertEqual(actual - expected, set(), "stale agents - run tools/gen_agents.py")

    def test_sme_ids_are_unique_across_domains(self):
        seen = {}
        for dom, items in self.smes.items():
            for s in items:
                self.assertNotIn(s["id"], seen,
                                 f"{s['id']} in both {dom} and {seen.get(s['id'])}")
                seen[s["id"]] = dom

    def test_peers_are_same_domain_only(self):
        # Cross-domain contact goes through escalation, never through a peer link.
        for dom, items in self.smes.items():
            local = {s["id"] for s in items}
            for s in items:
                for peer in s.get("peers", []):
                    self.assertIn(peer, local,
                                  f"{s['id']} peers with {peer} outside {dom}")
                self.assertNotIn(s["id"], s.get("peers", []), f"{s['id']} peers with itself")

    def test_every_sme_refuses_assumptions_and_asks_owned_questions(self):
        for items in self.smes.values():
            for s in items:
                self.assertTrue(s["never_assume"], f"{s['id']} assumes everything")
                self.assertTrue(s["must_ask"], f"{s['id']} asks nothing")
                for q in s["must_ask"]:
                    self.assertTrue(q.get("of", "").strip(),
                                    f"{s['id']} has a question with no owner")
                self.assertTrue(s["escalate_when"], f"{s['id']} never escalates")

    def test_protocol_is_stamped_identically_into_every_agent(self):
        # An SME's view of when to escalate must not drift from its Architect's
        # view of when to accept, so both come from one source.
        rule = self.h["protocols"]["escalation"]["goes_to_master"][0]
        for d in self.h["domains"]:
            text = (self.AGENTS / f"architect-{d['id']}.md").read_text()
            self.assertIn(rule, text, f"architect-{d['id']} missing the escalation protocol")
        sme_rule = self.h["protocols"]["sme"][0]
        for items in self.smes.values():
            for s in items:
                text = (self.AGENTS / f"sme-{s['id']}.md").read_text()
                self.assertIn(sme_rule, text, f"sme-{s['id']} missing the isolation protocol")

    def test_every_sme_routes_up_to_its_own_architect(self):
        for dom, items in self.smes.items():
            for s in items:
                text = (self.AGENTS / f"sme-{s['id']}.md").read_text()
                self.assertIn(f"architect-{dom}", text)
                self.assertIn("Tier 2", text)

    def test_engine_domain_references_resolve(self):
        keys = set(CAT.domain_keys())
        for d in self.h["domains"]:
            for e in d["eas_domains"]:
                self.assertIn(e, keys, f"{d['id']} maps to unknown engine domain {e}")

    def test_domains_the_engine_does_not_cover_are_flagged(self):
        uncovered = {d["id"] for d in self.h["domains"] if not d["eas_domains"]}
        self.assertEqual(uncovered, {"offsec", "human", "phys", "emrg"})
        # The Master Architect must say so, or a run that skipped them reads as clean.
        master = (self.AGENTS / "master-architect.md").read_text()
        self.assertIn("no counterpart in the Enterprise Architect Strategy engine", master)
        self.assertIn("incomplete rather than clean", master)

    def test_interfaces_are_symmetric_enough_to_route(self):
        ids = {d["id"] for d in self.h["domains"]}
        for d in self.h["domains"]:
            for other in d.get("interfaces_with", []):
                self.assertIn(other, ids, f"{d['id']} interfaces with unknown {other}")
                self.assertNotEqual(other, d["id"], f"{d['id']} interfaces with itself")


if __name__ == "__main__":
    unittest.main(verbosity=2)
