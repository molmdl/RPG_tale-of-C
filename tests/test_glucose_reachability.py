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

- Plan 05.2-01 (extensibility convention) added +1 bad-ending node (bad.denature_ph_change, pH-denaturation, edit:unknown): 54 -> 55 nodes, 20 -> 21 endings, Bad 14 -> 15 (1T+3G+2N+15B). The bad-ending-reachability test was generalized into a parametrized subTest convention proof (test_all_edit_prompt_bad_endings_reachable_convention) that auto-covers future Phase 7 additions WITHOUT test edits. The 14 edit-allowed + 0 single-Continue invariants are UNCHANGED by this addition.

Pure Python 3.6 stdlib only. NO pymol/PyQt5. Mirrors the proven pattern in
tests/test_integration.py:336-362 (the toy-graph SC2 tests).
"""
import os
import re
import unittest

from c14.story.graph import StoryGraph
from c14.story.interpreter import StoryInterpreter
from c14.story.model import Node
from c14.story.validate import check_reachability
from c14.state import GameState

HERE = os.path.dirname(os.path.abspath(__file__))
GLUCOSE_STORY_DIR = os.path.join(HERE, "..", "data", "story_glucose")


class TestGlucoseReachability(unittest.TestCase):
    """SC2: the reachability checker on the real 55-node glucose skeleton.

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
    preface Beat A is the new entry point). The bad-ending extensibility
    convention (Phase 5.2) is machine-checked by
    test_all_edit_prompt_bad_endings_reachable_convention.

    The Phase 5.1 replan Wave (Plans 05.1-07/08/09) applied the disease-
    mutant research + Continue-to-MC directive: 14 edit-allowed nodes (8
    disease-mutant promotions); 0 single-Continue nodes (Continue-to-MC
    conversion); the pyr.pdh 2OZL->6CFO cast fix; the etc.complex_i
    PLACEHOLDER->DIS-NDUFS8-01-cand claim_id fix; the tca.citrate_synthase
    edit:structural reframe. The 14 edit-allowed count + the 0 single-Continue
    invariant are UNCHANGED across the expansion Wave 2. The replan
    invariants are machine-checked by test_no_single_continue_choice,
    test_14_edit_allowed_nodes, and test_pdh_cast_pdb_fix_and_complex_i_claim_id.

    Plan 05.2-01 (extensibility convention) added +1 bad-ending node
    (bad.denature_ph_change, pH-denaturation, edit:unknown): 54 -> 55 nodes,
    20 -> 21 endings, Bad 14 -> 15 (1T+3G+2N+15B). The bad-ending-reachability
    test was generalized into a parametrized subTest convention proof that
    auto-covers future Phase 7 additions WITHOUT test edits. The 14
    edit-allowed + 0 single-Continue invariants are UNCHANGED by this
    addition."""

    def setUp(self):
        self._story_dir = GLUCOSE_STORY_DIR

    def test_manifest_loads_all_55_nodes(self):
        """The manifest lists 7 files; StoryGraph.load merges them with no
        duplicate-id ValueError. 55 nodes = 52 story nodes + fa.stub +
        alc.stub + edit.prompt. (Was 34 before the tiered-completeness
        expansion added 9 net nodes, then 43 before the expansion Wave 2
        added +9 bad-ending nodes [Plan 05.1-12] + 2 preface nodes
        [Plan 05.1-13], then 54 before Plan 05.2-01 added +1 bad-ending
        node [bad.denature_ph_change].) The manifest start is now
        intro.preface (the preface Beat A is the entry point after Plan
        05.1-13)."""
        g = StoryGraph.load(self._story_dir)
        nodes = g.all_nodes()
        self.assertEqual(len(nodes), 55,
                         "glucose skeleton has 55 nodes after the bad-ending + preface + extensibility expansion (43 base + 10 bad endings + 2 preface)")
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
        (1T+3G+2N+5B -> 1T+3G+2N+15B = 21 endings) via the Plan 05.1-12
        bad-ending expansion + the Plan 05.2-01 extensibility addition."""
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
        # exactly 21 ending nodes (1 True + 3 Good + 2 Normal + 15 Bad)
        all_endings = [n for n in g.all_nodes().values() if n.is_ending]
        self.assertEqual(len(all_endings), 21,
                         "exactly 21 ending nodes after the bad-ending expansion (1T+3G+2N+15B; the Bad tier grew 5 -> 15 via 10 new bad-ending nodes)")

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

    def test_all_edit_prompt_bad_endings_reachable_convention(self):
        """Bad-ending extensibility convention (Phase 5.2): every bad ending
        reachable from the edit.prompt structural stub is a valid bad ending
        with a correct edit:* tag, and the full-graph reachability stays GREEN.
        Parametrized via subTest over the stub's structural choices so future
        additions (Phase 7 content) auto-verify WITHOUT test edits. The 14
        edit-allowed + 0 single-Continue invariants are covered by the UNCHANGED
        test_14_edit_allowed_nodes + test_no_single_continue_choice (which still
        pass after the addition -- see those tests)."""
        g = StoryGraph.load(self._story_dir)
        edit_prompt = g.get_node("edit.prompt")
        valid_edit_tags = ("edit:unknown", "edit:known", "edit:known_critical")
        bad_targets = []
        for c in edit_prompt.choices:
            if c.goto is None or not c.goto.startswith("bad."):
                continue
            with self.subTest(choice_goto=c.goto):
                self.assertIn(c.goto, g.all_nodes(),
                              "structural choice target %r must exist" % c.goto)
                self.assertEqual(g.get_node(c.goto).is_ending, "bad",
                                 "target %r must be is_ending=bad" % c.goto)
                ctags = c.tags or []
                self.assertTrue(
                    any(t in valid_edit_tags for t in ctags),
                    "choice to %r must carry one of %s; got %s"
                    % (c.goto, valid_edit_tags, ctags))
                bad_targets.append(c.goto)
        self.assertGreaterEqual(
            len(bad_targets), 13,
            "edit.prompt should reach >=13 bad endings after Phase 5.2; "
            "got %d: %s" % (len(bad_targets), sorted(bad_targets)))
        rep = check_reachability(g.all_nodes(), g.start_node())
        self.assertTrue(rep.is_ok,
                        "reachability stays GREEN after the bad-ending addition")
        self.assertEqual(rep.unreachable_endings, [],
                         "no unreachable endings after the bad-ending addition")


class TestPyrBranchRuntimeEligibility(unittest.TestCase):
    """Runtime-eligibility tests for the pyr.branch cond-syntax fix (06-05).

    The structural reachability tests in TestGlucoseReachability cover BFS
    (cond ignored). These tests exercise the interpreter's ``_cond`` at
    RUNTIME to confirm the fixed ``flags.get('host_o2_low')`` conds evaluate
    correctly: the aerobic choice is eligible when ``host_o2_low`` is unset
    (player can proceed to TCA -> True ending), the anaerobic choice is hidden
    until a flag-setter exists (Phase 7), and the flag flip inverts
    eligibility. Also includes a regression scan ensuring NO choice cond in the
    glucose story uses the broken ``flags.<attr>`` dict-attribute form.

    This is a COND-SYNTAX fix to the FROZEN 5.1 skeleton, NOT a topology
    change: the 55-node/21-ending structural reachability is unchanged (covered
    by TestGlucoseReachability above); these tests prove the FROZEN topology is
    actually PLAYABLE past pyr.branch (the 05.1-06 review didn't exercise
    runtime cond evaluation).
    """

    def setUp(self):
        self._story_dir = GLUCOSE_STORY_DIR

    def _pyr_branch_choices(self):
        """Return (aerobic_choice, anaerobic_choice) from pyr.branch.

        Aerobic = the choice whose cond starts with 'not ' (the
        ``not flags.get('host_o2_low')`` choice -> pyr.pdh -> TCA -> True
        ending). Anaerobic = the other cond-gated choice
        (``flags.get('host_o2_low')`` -> anaer.entry -> fermentation endings).
        """
        g = StoryGraph.load(self._story_dir)
        node = g.get_node("pyr.branch")
        aerobic = None
        anaerobic = None
        for c in node.choices:
            if c.cond and c.cond.startswith("not "):
                aerobic = c
            elif c.cond:
                anaerobic = c
        self.assertIsNotNone(
            aerobic,
            "pyr.branch has an aerobic choice (cond starts with 'not ')")
        self.assertIsNotNone(
            anaerobic,
            "pyr.branch has an anaerobic choice (cond without 'not ')")
        return aerobic, anaerobic

    def test_pyr_branch_aerobic_choice_eligible_when_host_o2_low_unset(self):
        """Aerobic choice (``not flags.get('host_o2_low')``) is eligible when
        ``host_o2_low`` is unset (fresh GameState, empty flags). ``flags.get``
        returns None -> ``not None`` is True -> the player CAN proceed
        aerobically to pyr.pdh -> TCA -> the True ending (SC#3 unblocked)."""
        aerobic, _ = self._pyr_branch_choices()
        interp = StoryInterpreter()
        state = GameState()  # empty flags -> host_o2_low unset
        self.assertIs(
            interp._cond(aerobic.cond, state), True,
            "aerobic choice eligible when host_o2_low unset (player can reach "
            "TCA -> True ending); cond=%r" % aerobic.cond)

    def test_pyr_branch_anaerobic_choice_hidden_when_host_o2_low_unset(self):
        """Anaerobic choice (``flags.get('host_o2_low')``) is HIDDEN when
        ``host_o2_low`` is unset. ``flags.get`` returns None -> ``bool(None)``
        is False -> the anaerobic branch is not selectable until a Phase 7
        flag-setter exists (no fabricated anaerobic reachability)."""
        _, anaerobic = self._pyr_branch_choices()
        interp = StoryInterpreter()
        state = GameState()  # empty flags -> host_o2_low unset
        self.assertIs(
            interp._cond(anaerobic.cond, state), False,
            "anaerobic choice hidden when host_o2_low unset (None is falsy); "
            "cond=%r" % anaerobic.cond)

    def test_pyr_branch_aerobic_hidden_when_host_o2_low_set_true(self):
        """Setting ``host_o2_low=True`` FLIPS eligibility: the aerobic choice
        becomes hidden (``not True`` is False) and the anaerobic choice becomes
        eligible (``True`` is truthy). Proves the cond is actually reading the
        flag, not just always-True (a regression guard against a cond that
        ignores the flag entirely)."""
        aerobic, anaerobic = self._pyr_branch_choices()
        interp = StoryInterpreter()
        state = GameState()
        state.set_flag("host_o2_low", True)
        self.assertIs(
            interp._cond(aerobic.cond, state), False,
            "aerobic choice hidden when host_o2_low=True (not True is False); "
            "cond=%r" % aerobic.cond)
        self.assertIs(
            interp._cond(anaerobic.cond, state), True,
            "anaerobic choice eligible when host_o2_low=True; cond=%r"
            % anaerobic.cond)

    def test_pyr_branch_both_choices_not_stuck(self):
        """Regression guard: at least ONE pyr.branch choice is eligible when
        ``host_o2_low`` is unset (the aerobic choice is True). The OLD broken
        ``flags.host_o2_low`` cond made BOTH choices False (AttributeError ->
        caught -> False) -> the player was STUCK at pyr.branch -> SC#3 blocked.
        This test proves the fix: the player can advance past pyr.branch."""
        aerobic, anaerobic = self._pyr_branch_choices()
        interp = StoryInterpreter()
        state = GameState()  # host_o2_low unset
        eligible = [c for c in (aerobic, anaerobic)
                    if interp._cond(c.cond, state)]
        self.assertGreaterEqual(
            len(eligible), 1,
            "at least one pyr.branch choice must be eligible when "
            "host_o2_low is unset (the OLD broken cond made both False -> "
            "stuck -> SC#3 blocked); conds=%r, %r"
            % (aerobic.cond, anaerobic.cond))

    def test_no_broken_dict_attribute_conds_remain(self):
        """Regression scan: NO choice cond in the glucose story uses the broken
        ``flags.<attr>`` dict-attribute form (which raises AttributeError in
        ``_cond`` -> caught -> False -> choice hidden -> potentially stuck).
        The dict-method form ``flags.get(...)`` is correct (matches
        tca.shuffle's working ``visits.get(...)`` sibling). Scans only ``flags.``
        attribute access (``visits.``/``counters.`` are separate dicts and are
        not flagged here). Catches any other node with the same bug so it
        surfaces immediately rather than stranding the player at runtime."""
        g = StoryGraph.load(self._story_dir)
        # Match flags.<identifier> NOT immediately followed by '(' (i.e. a bare
        # dict-attribute access, NOT a dict-method call like flags.get(...)).
        # The trailing (?![a-zA-Z0-9_]) word-boundary BEFORE (?!\() is REQUIRED:
        # without it the greedy [a-zA-Z0-9_]* backtracks from 'get' to 'ge' when
        # the next char is '(', making (?!\() succeed on the truncated prefix
        # 'flags.ge' -- a false positive that flags the CORRECT flags.get(...)
        # form as broken. The boundary forces the full identifier to match
        # first, so (?!\() only tests the char after the COMPLETE identifier.
        broken = re.compile(r"flags\.[a-zA-Z_][a-zA-Z0-9_]*(?![a-zA-Z0-9_])(?!\()")
        offenders = []
        for nid, node in g.all_nodes().items():
            for c in node.choices:
                if c.cond is None:
                    continue
                m = broken.search(c.cond)
                if m:
                    offenders.append((nid, c.cond, m.group(0)))
        self.assertEqual(
            offenders, [],
            "no choice cond should use the broken flags.<attr> "
            "dict-attribute form (use flags.get('<attr>') instead -- the "
            "interpreter exposes flags as a DICT so attribute access raises "
            "AttributeError -> caught -> choice hidden); offenders=%s"
            % offenders)


class TestStartNodeOnEnterShape(unittest.TestCase):
    """Start-node on_enter shape tests for the _smoke.pdb swap + the 6-call
    hero-highlight sequence (06-05 Task 3).

    The FROZEN 5.1 start nodes (intro.preface + intro.shell_glucose) used
    ``pdb:TBD_*`` load targets that are NOT real PDB IDs -- molops.load's
    target-prefix fallback (06-01) would route them to fetch_pdb -> a network
    fetch that fails -> the game crashes on intro.preface (the manifest start
    node) the moment the first load dispatches. These tests confirm the swap
    to the bundled ``_smoke.pdb`` placeholder (no network, no crash) + the
    6-call hero-highlight sequence on hero_atom (SC2 human-verifiable at
    Phase 6, no fabricated science -- _smoke.pdb is a test fixture, NOT a
    cited PDB).

    These are CONTENT-shape tests (the on_enter MolAction list), NOT topology
    tests -- the 55-node/21-ending structural reachability is unchanged
    (covered by test_intro_topology_unchanged below re-running the counts).
    """

    def setUp(self):
        self._story_dir = GLUCOSE_STORY_DIR

    def _graph(self):
        return StoryGraph.load(self._story_dir)

    def test_preface_on_enter_loads_bundled_placeholder_not_tbd(self):
        """intro.preface on_enter loads the bundled ``_smoke.pdb`` placeholder
        (no network fetch) and has NO ``pdb:TBD*`` crash target. The 2
        original TBD loads (TBD_HERO_CARBON + TBD_AA_CAST_20) are both swapped
        for _smoke.pdb so the start node does not crash on the first load
        (Blocker 1 fix b)."""
        node = self._graph().get_node("intro.preface")
        load_targets = [m.target for m in node.on_enter if m.op == "load"]
        for t in load_targets:
            self.assertFalse(
                t is not None and t.startswith("pdb:TBD"),
                "intro.preface on_enter must NOT load a pdb:TBD* target (it "
                "would network-fetch a non-existent PDB -> crash); got %r"
                % load_targets)
        self.assertIn(
            "_smoke.pdb", load_targets,
            "intro.preface on_enter loads the bundled _smoke.pdb placeholder; "
            "load targets=%s" % load_targets)

    def test_preface_on_enter_has_hero_highlight_sequence(self):
        """intro.preface on_enter contains the 6-call hero-highlight sequence
        from 05.4-CONVENTION.md section 3.3 (set_color hero_cyan + show_as
        sticks + color hero_cyan on elem C + show spheres + set sphere_scale
        0.3 + label YOU), IN ORDER, AFTER the hero_atom load (the load
        precedes the highlight so the ops act on a real object). SC2
        ('Starting a glucose game highlights the C14 hero atom') is
        human-verifiable at Phase 6 via this sequence."""
        node = self._graph().get_node("intro.preface")
        on_enter = node.on_enter
        # The hero_atom load must precede the highlight sequence.
        hero_load_idx = None
        for i, m in enumerate(on_enter):
            if m.op == "load" and m.args.get("object") == "hero_atom":
                hero_load_idx = i
                break
        self.assertIsNotNone(
            hero_load_idx,
            "intro.preface on_enter loads hero_atom before the highlight")
        # The 6-op sequence, in order, each matching a predicate. Walk
        # forward from after the hero_atom load; each op must be the next
        # matching one at a higher index (ordered subsequence).
        seq = [
            ("set_color", lambda m: m.args.get("name") == "hero_cyan"),
            ("show_as",   lambda m: m.args.get("rep") == "sticks"),
            ("color",     lambda m: m.args.get("color") == "hero_cyan"),
            ("show",      lambda m: m.args.get("rep") == "spheres"),
            ("set",       lambda m: m.args.get("name") == "sphere_scale"),
            ("label",     lambda m: m.args.get("text") == "YOU"),
        ]
        idx = hero_load_idx + 1
        for op_name, pred in seq:
            found = False
            while idx < len(on_enter):
                m = on_enter[idx]
                idx += 1
                if m.op == op_name and pred(m):
                    found = True
                    break
            self.assertTrue(
                found,
                "intro.preface on_enter hero-highlight sequence missing op "
                "%r (with its predicate) after the hero_atom load; "
                "on_enter=%s" % (op_name, [mm.to_dict() for mm in on_enter]))

    def test_shell_glucose_on_enter_loads_bundled_not_tbd(self):
        """intro.shell_glucose on_enter loads the bundled ``_smoke.pdb`` as
        ``glucose`` (no ``pdb:TBD`` network fetch, no crash on the second
        start-node load). NO hero-highlight here -- preface owns the highlight
        (keeps the diff minimal)."""
        node = self._graph().get_node("intro.shell_glucose")
        glucose_loads = [m for m in node.on_enter
                         if m.op == "load" and m.args.get("object") == "glucose"]
        self.assertEqual(
            len(glucose_loads), 1,
            "intro.shell_glucose on_enter has exactly one glucose load; got "
            "%s" % [m.to_dict() for m in glucose_loads])
        self.assertEqual(
            glucose_loads[0].target, "_smoke.pdb",
            "the glucose load uses the bundled _smoke.pdb placeholder (NOT "
            "pdb:TBD_GLUCOSE); target=%r" % glucose_loads[0].target)
        for m in node.on_enter:
            if m.op == "load":
                self.assertFalse(
                    m.target is not None and m.target.startswith("pdb:TBD"),
                    "intro.shell_glucose on_enter must NOT load a pdb:TBD* "
                    "target; got %r" % m.target)

    def test_start_nodes_do_not_reference_real_pdb_fetch(self):
        """NO start-node (intro.preface / intro.shell_glucose / intro.select)
        on_enter load target starts with ``pdb:`` -- the start nodes use
        bundled placeholders ONLY (no network fetch at game start; SC4
        'small/critical bundled so the game starts instantly'). intro.select
        / fa.stub / alc.stub have ``[hide_all]``-only on_enter (no load) and
        trivially pass."""
        g = self._graph()
        start_nodes = ["intro.preface", "intro.shell_glucose", "intro.select"]
        for nid in start_nodes:
            node = g.get_node(nid)
            for m in node.on_enter:
                if m.op == "load":
                    self.assertFalse(
                        m.target is not None and m.target.startswith("pdb:"),
                        "start node %r on_enter must NOT load a pdb: target "
                        "(start nodes use bundled placeholders only -- SC4 "
                        "instant-start); got %r" % (nid, m.target))

    def test_intro_topology_unchanged(self):
        """Regression guard: the on_enter content edit (swapping TBD_* targets
        + adding the hero-highlight sequence) did NOT change the topology.
        Re-runs the frozen skeleton counts: 55 nodes, 21 endings (1T+3G+2N+
        15B), all 4 tiers reachable from intro.preface."""
        g = self._graph()
        self.assertEqual(
            len(g.all_nodes()), 55,
            "topology unchanged: 55 nodes (the on_enter edit is content-only)")
        rep = check_reachability(g.all_nodes(), g.start_node())
        self.assertTrue(
            rep.is_ok,
            "reachability stays GREEN after the on_enter edit")
        all_endings = [n for n in g.all_nodes().values() if n.is_ending]
        self.assertEqual(
            len(all_endings), 21,
            "topology unchanged: 21 endings (1T+3G+2N+15B)")


if __name__ == "__main__":
    unittest.main()
