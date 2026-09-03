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

- Plan 07-12 (Phase 7 restoration topology, the DC-A outcome of 07-01) added +2
  restoration-branch nodes: 55 -> 57 nodes, 21 endings UNCHANGED (restoration
  nodes are NON-ending). gly.pfk_restored (glycolysis.json) and
  tca.aconitase_restored (tca.json) are the FIXED branch_node targets the
  EditRouter routes known (correct reverse-mutation) edits to once rpg/data/
  edits.json binds them (Phase 7 plan 14). Their entry is ROUTER-ONLY (no
  incoming choice.goto edge -- engine.apply_player_edit routes directly to the
  branch node, bypassing choices; same runtime-vs-structural distinction as
  the edit.prompt stub), so the BFS neither reaches nor needs them; each
  carries 2 choices (Continue + mc:observe Observe) re-entering the main path
  (gly.fbp_to_pyruvate / tca.shuffle). Their on_enter carries the 05.3 §2 (iii)
  restoration-reveal op sequence: edit (the player's reverse mutation) -> load
  WT cast -> align (method=super, align_sele="name CA") -> show_as. The 14
  edit-allowed + 0 single-Continue invariants are UNCHANGED (restoration nodes
  are NOT edit-allowed).

- Plan 07-13 (Phase 7 TCA content) applied the 07-03 Decision D5 promotion:
  tca.akg_dh gains an edit:enzyme:tca.akg_dh tag + an edit:offer choice, so
  the edit-allowed invariant grew 14 -> 15 (the OGDH promotion's "same plan"
  test-update obligation per the 07-03 ledger: DIS-OGDH-01-cand P189L, the
  evidence-weaker single-submitter tier, promoted over research's
  narrative-only preference). Node/ending counts are UNCHANGED (a tag + a
  choice, not new nodes). The 0 single-Continue invariant is UNCHANGED (the
  new offer rides alongside the existing 2 choices).

Pure Python 3.6 stdlib only. NO pymol/PyQt5. Mirrors the proven pattern in
tests/test_integration.py:336-362 (the toy-graph SC2 tests).
"""
import os
import re
import unittest

from rpg.story.graph import StoryGraph
from rpg.story.interpreter import StoryInterpreter
from rpg.story.model import Node
from rpg.story.validate import check_reachability
from rpg.state import GameState

HERE = os.path.dirname(os.path.abspath(__file__))
GLUCOSE_STORY_DIR = os.path.join(HERE, "..", "data", "story_glucose")


class TestGlucoseReachability(unittest.TestCase):
    """SC2: the reachability checker on the real 57-node glucose skeleton.

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
    (bad.denature_ph_change, pH-denaturation, 1a edit:unknown): 54 -> 55 nodes,
    20 -> 21 endings, Bad 14 -> 15 (1T+3G+2N+15B). The bad-ending-reachability
    test was generalized into a parametrized subTest convention proof that
    auto-covers future Phase 7 additions WITHOUT test edits. The 14
    edit-allowed + 0 single-Continue invariants are UNCHANGED by this
    addition.

    Plan 07-12 (Phase 7 restoration topology) added the 2 DC-A restoration-
    branch nodes: 55 -> 57 nodes, 21 endings UNCHANGED. See the module
    docstring for the router-only-entry semantics.

    Plan 07-13 applied the 07-03 D5 promotion: tca.akg_dh is edit-allowed,
    growing the set 14 -> 15 (the OGDH "same plan" test-update obligation).
    Node/ending counts unchanged."""

    def setUp(self):
        self._story_dir = GLUCOSE_STORY_DIR

    def test_manifest_loads_all_57_nodes(self):
        """The manifest lists 7 files; StoryGraph.load merges them with no
        duplicate-id ValueError. 57 nodes = 52 story nodes + fa.stub +
        alc.stub + edit.prompt + the 2 Phase 7 plan-12 restoration nodes
        (gly.pfk_restored + tca.aconitase_restored, the 07-01 DC-A outcome).
        (Was 34 before the tiered-completeness expansion added 9 net nodes,
        then 43 before the expansion Wave 2 added +9 bad-ending nodes
        [Plan 05.1-12] + 2 preface nodes [Plan 05.1-13], then 54 before
        Plan 05.2-01 added +1 bad-ending node [bad.denature_ph_change],
        then 55 before Plan 07-12 added the +2 restoration nodes.) The
        manifest start is intro.preface (the preface Beat A is the entry
        point after Plan 05.1-13)."""
        g = StoryGraph.load(self._story_dir)
        nodes = g.all_nodes()
        self.assertEqual(len(nodes), 57,
                         "glucose skeleton has 57 nodes after the Phase 7 "
                         "restoration-topology addition (55 + gly.pfk_restored "
                         "+ tca.aconitase_restored)")
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
        bad-ending expansion + the Plan 05.2-01 extensibility addition. The
        Plan 07-12 restoration nodes are NON-ending additions (57 nodes, 21
        endings unchanged) and are NOT BFS entries (router-only -- see
        test_restoration_nodes_reachable_non_ending)."""
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

    def test_15_edit_allowed_nodes(self):
        """Count invariant (Driver 1 -- promotion): exactly 15 edit-allowed
        nodes (each carrying an edit:enzyme:<id> tag). History: the
        disease-mutant replan promoted 8 enzyme nodes to edit-allowed
        (gly.pyruvate_kinase, 4 TCA enzymes -- isocitrate_dh/
        succinyl_coa_synthetase/fumarase/malate_dh, 3 ETC complexes --
        complex_ii/iii/iv), growing the set from 5+shuffle to 14; Plan 07-13
        then applied the 07-03 Decision D5 promotion (tca.akg_dh gains the
        edit:enzyme:tca.akg_dh tag + an edit:offer choice), growing 14 -> 15
        (the OGDH promotion's "same plan" test-update obligation -- DIS-OGDH-
        01-cand P189L, approved with the single-submitter/no-assertion-criteria
        evidence-tier caveat). Each edit-allowed node must carry an edit:offer
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
        self.assertEqual(len(edit_allowed), 15,
                         "exactly 15 edit-allowed nodes after the 07-03 D5 "
                         "OGDH promotion (14 replan + tca.akg_dh by 07-13); "
                         "found %d: %s"
                         % (len(edit_allowed), sorted(edit_allowed.keys())))
        expected_ids = {
            "gly.pfk", "pyr.pdh", "tca.citrate_synthase", "tca.aconitase",
            "tca.shuffle", "etc.complex_i", "gly.pyruvate_kinase",
            "tca.isocitrate_dh", "tca.akg_dh",
            "tca.succinyl_coa_synthetase",
            "tca.fumarase", "tca.malate_dh", "etc.complex_ii",
            "etc.complex_iii", "etc.complex_iv",
        }
        self.assertEqual(
            set(edit_allowed.keys()), expected_ids,
            "the 15 edit-allowed node ids must match the replan set + the "
            "D5-promoted tca.akg_dh exactly")
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

    def test_restoration_nodes_reachable_non_ending(self):
        """Plan 07-12 restoration-topology invariants (the 07-01 DC-A outcome):
        gly.pfk_restored + tca.aconitase_restored exist with (a) NO ending
        tier (NON-ending -- the 21-ending count is unchanged), (b) NO
        edit:enzyme: tag (NOT edit-allowed; test_14_edit_allowed_nodes'
        exact-set assertion guards this from the other side), (c) a forward
        path back to the main path: every choice.goto target exists and an
        ENDING is reachable from the restored node via choice.goto chains
        (a restored branch is never a dead end), (d) the 05.3 §2 (iii)
        restoration-reveal on_enter op sequence in order: edit (the player's
        reverse mutation) -> load (the WT cast) -> align (method=super per
        the 07-04 batch-C convention) -> show_as, (e) full-graph structural
        reachability stays GREEN.

        Router-only entry (why the BFS neither reaches nor needs them): the
        restored nodes have NO incoming choice.goto edge --
        engine.apply_player_edit routes a KNOWN edit DIRECTLY to the branch
        node (edit_router.route -> _enter), bypassing choices. Same
        structural-vs-runtime distinction as the edit.prompt stub; these
        nodes are pinned HERE instead of via the BFS.

        The aconitase sele documents the derived human<->bovine mapping
        (tools/aconitase_mapping_probe.py, SMOKE_RESULT: PASS): human ACO2
        S112 (UniProt Q99798, the DIS-ACO2-01-cand allele S112R) -> bovine
        1ACO chain A resi 85 (SER) -- real Needleman-Wunsch alignment of the
        human sequence vs the cmd.iterate-extracted 1ACO ATOM-record sequence
        (96.4% identity), cross-checked by 1ACO's own DBREF record (PDB
        2-754 = UniProt P20004 29-781; 112 - 27 = 85) and the catalytic
        Ser642 anchor. Chain case is EMPIRICAL: PyMOL matches 'chain A'
        (uppercase) only. The PFK sele (resi 209 -> GLY) is the recorded
        game-design framing (07-02 batch A: text-only disease fallback, NO
        bacterial residue mapping asserted -- 4PFK resi 209 is HIS; the
        honest teaching text lands in plan 08)."""
        restored = {
            "gly.pfk_restored": {
                "edit_target": "pfk",
                "sele": "resi 209 and chain A",
                "new_resn": "GLY",
                "wt_object": "pfk_wt",
                "wt_pdb": "pdb:4PFK",
                "reentry": "gly.fbp_to_pyruvate",
            },
            "tca.aconitase_restored": {
                "edit_target": "aconitase",
                "sele": "resi 85 and chain A",
                "new_resn": "SER",
                "wt_object": "aconitase_wt",
                "wt_pdb": "pdb:1ACO",
                "reentry": "tca.shuffle",
            },
        }
        g = StoryGraph.load(self._story_dir)
        for nid, spec in restored.items():
            with self.subTest(restored_node=nid):
                node = g.get_node(nid)  # KeyError (a loud fail) if absent
                # (a) NON-ending.
                self.assertIsNone(
                    node.is_ending,
                    "%s must be a NON-ending node (the 21-ending count is "
                    "unchanged by the restoration topology)" % nid)
                # (b) NOT edit-allowed.
                self.assertFalse(
                    any(str(t).startswith("edit:enzyme:") for t in node.tags),
                    "%s must NOT carry an edit:enzyme: tag (restoration "
                    "nodes are not edit-allowed); tags=%s" % (nid, node.tags))
                # (d) the 05.3 on_enter op sequence, in order.
                ops = [m.op for m in node.on_enter]
                self.assertEqual(
                    ops, ["edit", "load", "align", "show_as"],
                    "%s on_enter must be the 05.3 restoration-reveal "
                    "sequence [edit, load, align, show_as]; got %s"
                    % (nid, ops))
                edit_m = node.on_enter[0]
                self.assertEqual(edit_m.target, spec["edit_target"])
                self.assertEqual(edit_m.args.get("edit_type"), "point_mutation")
                self.assertEqual(edit_m.args.get("sele"), spec["sele"])
                self.assertEqual(edit_m.args.get("new_resn"), spec["new_resn"])
                load_m = node.on_enter[1]
                self.assertEqual(load_m.target, spec["wt_pdb"])
                self.assertEqual(load_m.args.get("object"), spec["wt_object"])
                align_m = node.on_enter[2]
                self.assertEqual(align_m.target, spec["wt_object"],
                                 "align mobile = the WT object (it MOVES)")
                self.assertEqual(
                    align_m.args.get("reference"), spec["edit_target"],
                    "align reference (FIXED) = the edited enzyme object")
                self.assertEqual(
                    align_m.args.get("method"), "super",
                    "07-04 batch-C convention: op=align dispatches cmd.super")
                # (c) forward re-entry: goto targets exist + an ending is
                # reachable from the restored node.
                reentries = [c.goto for c in node.choices]
                self.assertIn(
                    spec["reentry"], reentries,
                    "%s must re-enter the main path at %s; choices got %s"
                    % (nid, spec["reentry"], reentries))
                for c in node.choices:
                    self.assertIn(
                        c.goto, g.all_nodes(),
                        "%s choice goto %r must exist" % (nid, c.goto))
                queue = [nid]
                visited = {nid}
                found_ending = False
                while queue and not found_ending:
                    cur = queue.pop()
                    cur_node = g.get_node(cur)
                    if cur_node.is_ending is not None:
                        found_ending = True
                        break
                    for c in cur_node.choices:
                        if c.goto in g.all_nodes() and c.goto not in visited:
                            visited.add(c.goto)
                            queue.append(c.goto)
                self.assertTrue(
                    found_ending,
                    "an ending must be reachable from %s via choice.goto "
                    "chains (a restored branch is never a dead end); "
                    "visited %d nodes" % (nid, len(visited)))
        # Router-only entry: no incoming choice.goto edge anywhere.
        for nid in restored:
            incoming = [src for src, other in g.all_nodes().items()
                        for c in other.choices if c.goto == nid]
            self.assertEqual(
                incoming, [],
                "restoration node %r must have NO incoming choice.goto edge "
                "(entry is router-only via engine.apply_player_edit); "
                "found %s" % (nid, incoming))
        # (e) full-graph structural reachability stays GREEN.
        rep = check_reachability(g.all_nodes(), g.start_node())
        self.assertTrue(
            rep.is_ok,
            "reachability stays GREEN after the restoration-topology addition")
        self.assertEqual(
            rep.unreachable_endings, [],
            "no unreachable endings after the restoration-topology addition")

    def test_edit_offer_nodes_carry_edit_enzyme_tag(self):
        """SC2f round-2 graph invariant (06-14 re-verify, debugger session
        .planning/debug/edit-prompt-empty-stash.md): EVERY node that offers an
        edit -- any choice carrying the 'edit:offer' tag OR whose goto IS
        'edit.prompt' (the DUAL predicate the ChoicePanel special-cases,
        widgets.py _render_pure + _render_mixed) -- must itself carry an
        'edit:enzyme:<id>' tag. This guarantees
        Controller._current_enzyme_id() is NON-None wherever the UI edit seam
        routes from, so request_edit always stashes a real enzyme_id and
        build_edit_intent can never raise the 'no pending enzyme_id stash'
        RuntimeError at edit.prompt. (Root cause of the user-reported bug:
        gly.pfk offered an edit as a PURE-MC node whose routing skipped
        request_edit; this invariant pins the data-side precondition that the
        fixed routing relies on.)"""
        g = StoryGraph.load(self._story_dir)
        offenders = []
        offer_nodes = 0
        for nid, node in g.all_nodes().items():
            offers = [c for c in node.choices
                      if "edit:offer" in (c.tags or [])
                      or c.goto == "edit.prompt"]
            if not offers:
                continue
            offer_nodes += 1
            has_tag = any(str(t).startswith("edit:enzyme:")
                          for t in node.tags)
            if not has_tag:
                offenders.append(nid)
        self.assertGreaterEqual(
            offer_nodes, 15,
            "the skeleton should have >=15 edit-offering nodes (the 15 "
            "edit-allowed set after the 07-03 D5 tca.akg_dh promotion); "
            "found %d" % offer_nodes)
        self.assertEqual(
            offenders, [],
            "every edit-offering node must carry an edit:enzyme:<id> tag "
            "(guarantees _current_enzyme_id() is non-None wherever the UI "
            "edit seam routes from); offenders=%s" % offenders)

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
        additions (Phase 7 content) auto-verify WITHOUT test edits. The 15
        edit-allowed + 0 single-Continue invariants are covered by
        test_15_edit_allowed_nodes + test_no_single_continue_choice (which still
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
    """Runtime-eligibility tests for the pyr.branch O2 branch (07-06).

    History: 06-05 fixed the cond SYNTAX (``flags.get('host_o2_low')`` dict-
    method form) and these tests then proved the cond-GATED semantics (aerobic
    eligible when ``host_o2_low`` unset / anaerobic hidden / flag flip
    inverts). The 07-01 DC-B outcome -- implemented by Phase 7 plan 06, the
    SAME plan that rewrote these tests (the OQ-K obligation) -- REMOVED both
    cond keys: nothing in the graph ever sets ``host_o2_low``, so the
    anaerobic subtree was structurally reachable (BFS ignores cond) but
    runtime-HIDDEN forever. Both pyr.branch choices are now UNCONDITIONAL
    (``cond is None`` -> always eligible per ``interpreter._cond``); the
    honest O2 framing moved into the choice labels + teaching text (oxygen
    availability is a real, tissue-level condition the player sets at the
    branch, like sprint-vs-rest physiology -- host = mammal per Phase 5).

    These tests now pin the ALWAYS-ELIGIBLE semantics: both choices carry no
    cond, both are eligible regardless of flag state (the flag is vestigial),
    and the player can take either road. The dict-attribute regression scan
    is kept: with the pyr.branch conds gone it passes trivially, and it
    still guards any FUTURE cond added anywhere in the story against the
    broken ``flags.<attr>`` form.

    Structural reachability (BFS, cond ignored) is covered by
    TestGlucoseReachability above; the node count is 57 after the sanctioned
    Phase 7 plan-12 restoration addition. This class is RUNTIME semantics.
    """

    def setUp(self):
        self._story_dir = GLUCOSE_STORY_DIR

    def _pyr_branch_choices(self):
        """Return (aerobic_choice, anaerobic_choice) from pyr.branch.

        Since the 07-06 cond-neutralization NEITHER choice carries a cond
        (the old cond-shape identification -- ``cond.startswith('not ')`` --
        no longer applies), so identification is by the FROZEN branch tags
        (``branch:aerobic`` -> pyr.pdh -> TCA; ``branch:anaerobic`` ->
        anaer.entry -> fermentation endings), preserved through the 07-06
        edit.
        """
        g = StoryGraph.load(self._story_dir)
        node = g.get_node("pyr.branch")
        aerobic = None
        anaerobic = None
        for c in node.choices:
            if "branch:aerobic" in (c.tags or []):
                aerobic = c
            elif "branch:anaerobic" in (c.tags or []):
                anaerobic = c
        self.assertIsNotNone(
            aerobic,
            "pyr.branch has an aerobic choice (branch:aerobic tag)")
        self.assertIsNotNone(
            anaerobic,
            "pyr.branch has an anaerobic choice (branch:anaerobic tag)")
        return aerobic, anaerobic

    def test_pyr_branch_choices_are_cond_neutral(self):
        """The 07-01 DC-B cond-neutralization, pinned: NEITHER pyr.branch
        choice carries a cond (``cond is None``). Nothing in the graph sets
        ``host_o2_low``, so any cond gating these choices would hide one
        subtree at runtime forever -- a regression re-adding a cond fails
        here loudly."""
        aerobic, anaerobic = self._pyr_branch_choices()
        self.assertIsNone(
            aerobic.cond,
            "aerobic choice must be cond-neutral (07-01 DC-B); cond=%r"
            % aerobic.cond)
        self.assertIsNone(
            anaerobic.cond,
            "anaerobic choice must be cond-neutral (07-01 DC-B); cond=%r"
            % anaerobic.cond)

    def test_pyr_branch_both_choices_eligible_when_flags_unset(self):
        """BOTH pyr.branch choices are eligible on a fresh GameState (empty
        flags): ``_cond(None, state)`` is True for each, so the player can
        proceed aerobically to pyr.pdh -> TCA -> the True ending OR take the
        air-runs-out road to anaer.entry -> the fermentation endings. The
        eligible set must contain both goto targets (replaces the old
        aerobic-eligible/anaerobic-hidden split)."""
        aerobic, anaerobic = self._pyr_branch_choices()
        interp = StoryInterpreter()
        state = GameState()  # empty flags -> host_o2_low unset (irrelevant)
        self.assertIs(
            interp._cond(aerobic.cond, state), True,
            "aerobic choice eligible on fresh state (cond-free); "
            "goto=%r" % aerobic.goto)
        self.assertIs(
            interp._cond(anaerobic.cond, state), True,
            "anaerobic choice eligible on fresh state (cond-free); "
            "goto=%r" % anaerobic.goto)
        self.assertEqual(
            {aerobic.goto, anaerobic.goto}, {"pyr.pdh", "anaer.entry"},
            "the two branch roads must target pyr.pdh (aerobic) and "
            "anaer.entry (anaerobic); got %r"
            % sorted([aerobic.goto, anaerobic.goto]))

    def test_pyr_branch_both_choices_eligible_when_host_o2_low_set_true(self):
        """Setting ``host_o2_low=True`` changes NOTHING: both choices stay
        eligible (replaces the old flip-when-set semantics). The flag is
        vestigial since the 07-06 cond removal -- no cond reads it -- so no
        flag value can hide either road. Proves eligibility does not depend
        on hidden state (a regression guard against a cond sneaking back)."""
        aerobic, anaerobic = self._pyr_branch_choices()
        interp = StoryInterpreter()
        state = GameState()
        state.set_flag("host_o2_low", True)
        self.assertIs(
            interp._cond(aerobic.cond, state), True,
            "aerobic choice STILL eligible with host_o2_low=True "
            "(flag is vestigial); cond=%r" % aerobic.cond)
        self.assertIs(
            interp._cond(anaerobic.cond, state), True,
            "anaerobic choice STILL eligible with host_o2_low=True "
            "(flag is vestigial); cond=%r" % anaerobic.cond)

    def test_pyr_branch_both_choices_not_stuck(self):
        """Regression guard, upgraded to the always-eligible semantics: BOTH
        pyr.branch choices are eligible when flags are unset (exactly 2, up
        from the old >=1). Lineage: the ORIGINAL broken ``flags.host_o2_low``
        cond made BOTH choices False (AttributeError -> caught -> False) ->
        the player was STUCK at pyr.branch -> SC#3 blocked; the 06-05
        dict-method fix made exactly one eligible; the 07-06
        cond-neutralization makes BOTH eligible -- the player can advance
        past pyr.branch on either road."""
        aerobic, anaerobic = self._pyr_branch_choices()
        interp = StoryInterpreter()
        state = GameState()  # host_o2_low unset (irrelevant)
        eligible = [c for c in (aerobic, anaerobic)
                    if interp._cond(c.cond, state)]
        self.assertEqual(
            len(eligible), 2,
            "BOTH pyr.branch choices must be eligible when flags are unset "
            "(the 07-06 always-eligible semantics: OLD broken cond -> both "
            "False -> stuck; cond-gated era -> one; now -> both); "
            "conds=%r, %r" % (aerobic.cond, anaerobic.cond))

    def test_no_broken_dict_attribute_conds_remain(self):
        """Regression scan: NO choice cond in the glucose story uses the broken
        ``flags.<attr>`` dict-attribute form (which raises AttributeError in
        ``_cond`` -> caught -> False -> choice hidden -> potentially stuck).
        The dict-method form ``flags.get(...)`` is correct (matches
        tca.shuffle's working ``visits.get(...)`` sibling). Scans only ``flags.``
        attribute access (``visits.``/``counters.`` are separate dicts and are
        not flagged here). Catches any other node with the same bug so it
        surfaces immediately rather than stranding the player at runtime.
        07-06 note: with the pyr.branch conds REMOVED (07-01 DC-B) this scan
        passes trivially today, but it stays as the guard for any FUTURE
        cond added anywhere in the story."""
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
    tests -- the 21-ending structural reachability is unchanged (covered by
    test_intro_topology_unchanged below re-running the counts; 57 nodes after
    the sanctioned Phase 7 plan-12 restoration addition).
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
        """Regression guard: the on_enter content edits (swapping TBD_*
        targets + adding the hero-highlight sequence) did NOT change the
        topology beyond the SANCTIONED Phase 7 plan-12 addition. Re-runs the
        frozen counts: 57 nodes (55 + the 2 restoration branch nodes of
        Plan 07-12, the only sanctioned topology change of Phase 7), 21
        endings (1T+3G+2N+15B), all 4 tiers reachable from intro.preface."""
        g = self._graph()
        self.assertEqual(
            len(g.all_nodes()), 57,
            "topology unchanged since Plan 07-12: 57 nodes (55 + the 2 "
            "restoration branch nodes -- the ONLY sanctioned topology change "
            "of Phase 7)")
        rep = check_reachability(g.all_nodes(), g.start_node())
        self.assertTrue(
            rep.is_ok,
            "reachability stays GREEN after the on_enter edit")
        all_endings = [n for n in g.all_nodes().values() if n.is_ending]
        self.assertEqual(
            len(all_endings), 21,
            "topology unchanged: 21 endings (1T+3G+2N+15B; the restoration "
            "nodes are NON-ending)")


if __name__ == "__main__":
    unittest.main()
