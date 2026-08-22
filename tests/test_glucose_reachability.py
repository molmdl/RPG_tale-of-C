"""SC2 reachability validation on the real glucose skeleton (Phase 5.1).

Proves the Phase 2 reachability checker guards REAL content: all 4 ending
tiers (true/good/normal/bad) are reachable from intro.preface via choice.goto
chains (GREEN), and a deliberately-orphaned variant is flagged RED.

The skeleton grew from 34 to 43 nodes in the Phase 5.1 tiered-completeness
expansion (Plan 05.1-EXPANSION), then from 43 to 54 nodes in the expansion
Wave 2 (Plans 05.1-12 + 05.1-13):
- Plan 05.1-12 (Req 1, CG-collection feel) added +9 bad-ending nodes
  (6 unknown-pool 1a + 3 known-consequence 1b) so the SAME wrong edit can
  produce DIFFERENT bad endings; the RngEngine-weighted unknown-edit
  bad-ending pool grew 2 -> 8 unknown + 3 known. The Bad ending tier grew
  5 -> 14 (ending distribution 1T+3G+2N+5B -> 1T+3G+2N+14B = 20 endings).
- Plan 05.1-13 (Req 2, preface sequence) added +2 preface nodes
  (intro.preface Beat A before character select + intro.shell_glucose
  Beat B before the journey); the manifest start changed
  intro.select -> intro.preface (the preface Beat A is the new entry point).

The Phase 5.1 replan Wave (Plans 05.1-07/08/09) applied the disease-mutant
research + Continue-to-MC directive to the post-expansion skeleton:
- 43 -> 54 nodes (the replan modified nodes in place; the +11 came from
  the expansion Wave 2 above, not the replan)
- 14 edit-allowed nodes (8 disease-mutant promotions grew the set from
  5+shuffle to 14: gly.pyruvate_kinase, 4 TCA enzymes, 3 ETC complexes)
- 0 single-Continue nodes (the Continue-to-MC conversion added an
  mc:observe Observe second choice to every formerly single-Continue node)
- 8 disease-mutant promotions (DIS-*-cand claim_ids, CANDIDATE pending
  Phase 7 per-claim approval)
- pyr.pdh cast PDB fixed 2OZL (S264E phospho-mimic mutant) -> 6CFO (WT)
- etc.complex_i claim_id PLACEHOLDER_PHASE7_ETC -> DIS-NDUFS8-01-cand
- tca.citrate_synthase edit:structural reframe (NO disease point mutant;
  7 ClinVar Pathogenic records are ALL structural variants)

The 14 edit-allowed count + the 0 single-Continue invariant are UNCHANGED
across the expansion Wave 2 (the 9 new bad endings are ending nodes with no
choices; the 2 new preface nodes each have 2 choices = Continue + Observe).

Pure Python 3.6 stdlib only. NO pymol/PyQt5. Mirrors the proven pattern in
tests/test_integration.py:336-362 (the toy-graph SC2 tests).
"""
import os
import unittest

from c14.story.graph import StoryGraph
from c14.story.validate import check_reachability
from c14.story.model import Node

HERE = os.path.dirname(os.path.abspath(__file__))
GLUCOSE_STORY_DIR = os.path.join(HERE, "..", "data", "story_glucose")


class TestGlucoseReachability(unittest.TestCase):
    """SC2: the reachability checker on the real 54-node glucose skeleton.

    The skeleton grew 34 -> 43 nodes in the Phase 5.1 tiered-completeness
    expansion (see 05.1-EXPANSION-SUMMARY.md): +1 gly.pyruvate_kinase,
    +1 anaer.ldh, +5 TCA enzymes (isocitrate_dh, akg_dh,
    succinyl_coa_synthetase, fumarase, malate_dh), +3 ETC complexes
    (complex_ii, complex_iii, complex_iv), -1 removed etc.complex_ii_iii_iv.

    The expansion Wave 2 (Plans 05.1-12 + 05.1-13) then grew 43 -> 54 nodes:
    Plan 05.1-12 (Req 1, CG-collection feel) added +9 bad-ending nodes
    (6 unknown-pool 1a + 3 known-consequence 1b) so the SAME wrong edit can
    produce DIFFERENT bad endings; the RngEngine-weighted bad-ending pool
    grew 2 -> 8 unknown + 3 known. The Bad ending tier grew 5 -> 14 (ending
    distribution 1T+3G+2N+5B -> 1T+3G+2N+14B = 20 endings). Plan 05.1-13
    (Req 2, preface sequence) added +2 preface nodes (intro.preface Beat A
    before character select + intro.shell_glucose Beat B before the
    journey); the manifest start changed intro.select -> intro.preface (the
    preface Beat A is the new entry point). The new bad-ending-reachability
    invariant is machine-checked by
    test_all_new_bad_endings_reachable_from_edit_prompt.

    The Phase 5.1 replan Wave (Plans 05.1-07/08/09) applied the disease-
    mutant research + Continue-to-MC directive: 14 edit-allowed nodes (8
    disease-mutant promotions); 0 single-Continue nodes (Continue-to-MC
    conversion); the pyr.pdh 2OZL->6CFO cast fix; the etc.complex_i
    PLACEHOLDER->DIS-NDUFS8-01-cand claim_id fix; the tca.citrate_synthase
    edit:structural reframe. The 14 edit-allowed count + the 0 single-Continue
    invariant are UNCHANGED across the expansion Wave 2. The replan
    invariants are machine-checked by test_no_single_continue_choice,
    test_14_edit_allowed_nodes, and test_pdh_cast_pdb_fix_and_complex_i_claim_id."""

    def setUp(self):
        self._story_dir = GLUCOSE_STORY_DIR

    def test_manifest_loads_all_54_nodes(self):
        """The manifest lists 7 files; StoryGraph.load merges them with no
        duplicate-id ValueError. 54 nodes = 51 story nodes + fa.stub +
        alc.stub + edit.prompt. (Was 34 before the tiered-completeness
        expansion added 9 net nodes, then 43 before the expansion Wave 2
        added +9 bad-ending nodes [Plan 05.1-12] + 2 preface nodes
        [Plan 05.1-13].) The manifest start is now intro.preface (the
        preface Beat A is the entry point after Plan 05.1-13)."""
        g = StoryGraph.load(self._story_dir)
        nodes = g.all_nodes()
        self.assertEqual(len(nodes), 54,
                         "glucose skeleton has 54 nodes after the bad-ending + preface expansion (43 base + 9 bad endings + 2 preface)")
        self.assertEqual(g.start_node(), "intro.preface",
                         "manifest start is intro.preface (the preface Beat A is the entry point after Plan 05.1-13)")

    def test_reachability_green_all_four_tiers(self):
        """SC2 GREEN: all 4 ending tiers reachable from intro.preface via
        choice.goto chains. The BFS ignores cond/weight, so both the aerobic
        and anaerobic subtrees are traversed; the True ending is structurally
        reachable via the aerobic path (the anaerobic guard is a runtime cond
        concern, not a structural one). The BFS now starts from intro.preface
        (Plan 05.1-13 shifted the manifest start intro.select -> intro.preface;
        the preface is upstream of everything, so all 4 tiers stay reachable).
        The endings are unchanged in tier -- only the Bad count grew
        (1T+3G+2N+5B -> 1T+3G+2N+14B = 20 endings) via the Plan 05.1-12
        bad-ending expansion."""
        g = StoryGraph.load(self._story_dir)
        rep = check_reachability(g.all_nodes(), g.start_node())
        self.assertTrue(rep.is_ok,
                        "glucose skeleton has no orphaned endings (green)")
        self.assertEqual(rep.unreachable_endings, [],
                         "no unreachable endings on the glucose skeleton")
        # all 4 ending tiers are reachable
        reachable_tiers = set()
        for ending_id in rep.reachable_endings:
            node = g.get_node(ending_id)
            reachable_tiers.add(node.is_ending)
        self.assertEqual(
            reachable_tiers,
            {"true", "good", "normal", "bad"},
            "all 4 ending tiers reachable; got " + str(reachable_tiers))
        # exactly 20 ending nodes (1 True + 3 Good + 2 Normal + 14 Bad)
        all_endings = [n for n in g.all_nodes().values() if n.is_ending]
        self.assertEqual(len(all_endings), 20,
                         "exactly 20 ending nodes after the bad-ending expansion (1T+3G+2N+14B; the Bad tier grew 5 -> 14 via 9 new bad-ending nodes)")

    def test_reachability_red_orphaned_true_ending(self):
        """SC2 RED (variant 1): remove the choice.goto edge to end.true
        (change etc.atp_synthase's choice to goto a non-existent node) ->
        end.true becomes unreachable -> is_ok False. Mirrors the
        test_integration.py:348-362 orphan pattern. The BFS uses
        g.start_node() which is now intro.preface (Plan 05.1-13) -- still
        RED because orphaning end.true is unreachable from intro.preface too."""
        g = StoryGraph.load(self._story_dir)
        orphaned = dict(g.all_nodes())
        # rebuild etc.atp_synthase without the choice that leads to end.true
        atp = orphaned["etc.atp_synthase"]
        orphaned["etc.atp_synthase"] = Node.from_dict({
            "id": atp.id,
            "text_dramatic": atp.text_dramatic,
            "text_teaching": atp.text_teaching,
            "claim_ids": atp.claim_ids,
            "on_enter": [m.to_dict() for m in atp.on_enter],
            "choices": [{"label": "Continue", "goto": "end.normal.co2"}],
        })
        rep = check_reachability(orphaned, g.start_node())
        self.assertFalse(rep.is_ok,
                         "orphaned variant is red (end.true unreachable)")
        self.assertIn("end.true", rep.unreachable_endings,
                      "end.true is flagged unreachable")

    def test_reachability_red_extra_orphaned_ending(self):
        """SC2 RED (variant 2): add an extra ending node with no incoming
        edge -> flagged unreachable. Mirrors test_integration.py:348-356.
        The BFS uses g.start_node() which is now intro.preface (Plan
        05.1-13) -- still RED because the orphaned ending is unreachable
        from intro.preface too."""
        g = StoryGraph.load(self._story_dir)
        orphaned = dict(g.all_nodes())
        orphaned["glucose.ending_orphan"] = Node.from_dict({
            "id": "glucose.ending_orphan",
            "is_ending": "bad",
            "choices": [],
        })
        rep = check_reachability(orphaned, g.start_node())
        self.assertFalse(rep.is_ok)
        self.assertIn("glucose.ending_orphan", rep.unreachable_endings)

    def test_no_pymol_import_on_load(self):
        """The glucose skeleton loads in pure Python (the testability
        boundary). Loading data/story_glucose/ must NOT import pymol/PyQt5."""
        import sys
        sys.modules.pop("pymol", None)
        sys.modules.pop("PyQt5", None)
        StoryGraph.load(self._story_dir)
        self.assertNotIn("pymol", sys.modules,
                         "loading the glucose skeleton did not import pymol")
        self.assertNotIn("PyQt5", sys.modules,
                         "loading the glucose skeleton did not import PyQt5")

    def test_no_single_continue_choice(self):
        """Replan invariant (Driver 2 -- Continue-to-MC): ZERO nodes have a
        single 'Continue' choice. The Continue-to-MC conversion (Plans
        05.1-07/08/09) added an mc:observe Observe second choice (or an
        edit:offer third choice) to every formerly single-Continue node, so
        no node is a linear click-through any more. A future regression that
        re-introduces a single-Continue node fails this test loudly."""
        g = StoryGraph.load(self._story_dir)
        single_continue = []
        for nid, node in g.all_nodes().items():
            choices = node.choices
            if len(choices) == 1 and choices[0].label == "Continue":
                single_continue.append(nid)
        self.assertEqual(
            len(single_continue), 0,
            "zero nodes should have a single 'Continue' choice (the "
            "Continue-to-MC invariant -- Driver 2 of the Phase 5.1 replan); "
            "found %d: %s" % (len(single_continue), single_continue))

    def test_14_edit_allowed_nodes(self):
        """Replan invariant (Driver 1 -- promotion): exactly 14 edit-allowed
        nodes (each carrying an edit:enzyme:<id> tag). The disease-mutant
        replan promoted 8 enzyme nodes to edit-allowed (gly.pyruvate_kinase,
        4 TCA enzymes -- isocitrate_dh/succinyl_coa_synthetase/fumarase/
        malate_dh, 3 ETC complexes -- complex_ii/iii/iv), growing the set
        from 5+shuffle to 14. Each edit-allowed node must carry an edit:offer
        choice routing to edit.prompt. tca.citrate_synthase carries the
        edit:structural reframe tag (NO disease point mutant) and has NO
        DIS-* claim_id."""
        g = StoryGraph.load(self._story_dir)
        edit_allowed = {}
        for nid, node in g.all_nodes().items():
            for tag in node.tags:
                if str(tag).startswith("edit:enzyme:"):
                    edit_allowed[nid] = node
                    break
        self.assertEqual(len(edit_allowed), 14,
                         "exactly 14 edit-allowed nodes after the disease-"
                         "mutant replan; found %d: %s"
                         % (len(edit_allowed), sorted(edit_allowed.keys())))
        expected_ids = {
            "gly.pfk", "pyr.pdh", "tca.citrate_synthase", "tca.aconitase",
            "tca.shuffle", "etc.complex_i", "gly.pyruvate_kinase",
            "tca.isocitrate_dh", "tca.succinyl_coa_synthetase",
            "tca.fumarase", "tca.malate_dh", "etc.complex_ii",
            "etc.complex_iii", "etc.complex_iv",
        }
        self.assertEqual(
            set(edit_allowed.keys()), expected_ids,
            "the 14 edit-allowed node ids must match the replan set exactly")
        # Each edit-allowed node has an edit:offer choice to edit.prompt.
        for nid, node in edit_allowed.items():
            has_offer = any(
                "edit:offer" in (c.tags or []) or c.goto == "edit.prompt"
                for c in node.choices)
            self.assertTrue(
                has_offer,
                "edit-allowed node %r must have an edit:offer choice (a "
                "choice whose tags include 'edit:offer' OR whose goto == "
                "'edit.prompt')" % nid)
        # tca.citrate_synthase reframe: edit:structural tag + NO DIS- claim.
        cs = edit_allowed["tca.citrate_synthase"]
        self.assertIn(
            "edit:structural", cs.tags,
            "tca.citrate_synthase carries the edit:structural reframe tag "
            "(CS has NO disease point mutant; 7 ClinVar Pathogenic records "
            "are ALL structural variants, not implementable via cmd.alter)")
        self.assertFalse(
            any(str(c).startswith("DIS-") for c in cs.claim_ids),
            "tca.citrate_synthase has NO DIS-* disease-mutant claim_id (it "
            "is edit:structural, not edit:disease); claim_ids=%s"
            % cs.claim_ids)

    def test_pdh_cast_pdb_fix_and_complex_i_claim_id(self):
        """Replan metadata fixes: (a) pyr.pdh cast PDB corrected 2OZL (S264E
        phospho-mimic mutant, NOT wild-type per RCSB title) -> 6CFO (WT,
        Whitley 2018); (b) pyr.pdh claim_ids include DIS-PDHA1-01-cand
        (PDHA1 V138M disease mutant) + CAST-PDH-WT-PDB-01-cand (6CFO WT
        cast); (c) etc.complex_i claim_ids == ['DIS-NDUFS8-01-cand'] (the
        PLACEHOLDER_PHASE7_ETC was REPLACED by DIS-NDUFS8-01-cand, Loeffen
        1998 first nuclear Complex I Leigh mutation). All DIS-*-cand +
        CAST-*-cand claims are CANDIDATE pending Phase 7 per-claim approval
        (skeleton REFERENCES candidates, does NOT assert disease as approved
        fact -- AGENTS.md no-fabricated-science rule)."""
        g = StoryGraph.load(self._story_dir)
        # (a) pyr.pdh cast PDB is 6CFO (WT), NOT 2OZL (phospho-mimic mutant).
        pdh = g.get_node("pyr.pdh")
        load_targets = [m.target for m in pdh.on_enter if m.op == "load"]
        self.assertIn(
            "pdb:6CFO", load_targets,
            "pyr.pdh on_enter loads pdb:6CFO (WT, Whitley 2018); "
            "load targets=%s" % load_targets)
        self.assertNotIn(
            "pdb:2OZL", load_targets,
            "pyr.pdh must NOT load pdb:2OZL (the S264E phospho-mimic mutant, "
            "NOT wild-type per RCSB title 'Human pyruvate dehydrogenase "
            "S264E variant')")
        # (b) pyr.pdh claim_ids include the disease + WT-cast candidates.
        self.assertIn("DIS-PDHA1-01-cand", pdh.claim_ids,
                      "pyr.pdh references DIS-PDHA1-01-cand (PDHA1 V138M, "
                      "PDHAD MIM:312170)")
        self.assertIn("CAST-PDH-WT-PDB-01-cand", pdh.claim_ids,
                      "pyr.pdh references CAST-PDH-WT-PDB-01-cand (6CFO WT "
                      "cast)")
        # (c) etc.complex_i claim_ids == ['DIS-NDUFS8-01-cand'] (PLACEHOLDER absent).
        ci = g.get_node("etc.complex_i")
        self.assertEqual(
            ci.claim_ids, ["DIS-NDUFS8-01-cand"],
            "etc.complex_i claim_ids REPLACED PLACEHOLDER_PHASE7_ETC with "
            "DIS-NDUFS8-01-cand (Loeffen 1998 PMID:9837812, first nuclear "
            "Complex I Leigh mutation); got %s" % ci.claim_ids)


if __name__ == "__main__":
    unittest.main()
