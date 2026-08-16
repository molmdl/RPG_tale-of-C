"""SC2 reachability validation on the real glucose skeleton (Phase 5.1).

Proves the Phase 2 reachability checker guards REAL content: all 4 ending
tiers (true/good/normal/bad) are reachable from intro.select via choice.goto
chains (GREEN), and a deliberately-orphaned variant is flagged RED.

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
    """SC2: the reachability checker on the real 34-node glucose skeleton."""

    def setUp(self):
        self._story_dir = GLUCOSE_STORY_DIR

    def test_manifest_loads_all_34_nodes(self):
        """The manifest lists 7 files; StoryGraph.load merges them with no
        duplicate-id ValueError. Node count grows as the skeleton is expanded
        (Phase 5.1 tiered-completeness expansion adds pyruvate_kinase, LDH,
        5 TCA enzymes, 3 ETC complexes). See 05.1-EXPANSION-SUMMARY.md."""
        g = StoryGraph.load(self._story_dir)
        nodes = g.all_nodes()
        self.assertEqual(len(nodes), 43,
                         "glucose skeleton has 43 nodes after the full tiered-completeness expansion")
        self.assertEqual(g.start_node(), "intro.select",
                         "manifest start is intro.select")

    def test_reachability_green_all_four_tiers(self):
        """SC2 GREEN: all 4 ending tiers reachable from intro.select via
        choice.goto chains. The BFS ignores cond/weight, so both the aerobic
        and anaerobic subtrees are traversed; the True ending is structurally
        reachable via the aerobic path (the anaerobic guard is a runtime cond
        concern, not a structural one)."""
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
        # exactly 11 ending nodes (1 True + 3 Good + 2 Normal + 5 Bad)
        all_endings = [n for n in g.all_nodes().values() if n.is_ending]
        self.assertEqual(len(all_endings), 11,
                         "exactly 11 ending nodes (1T+3G+2N+5B)")

    def test_reachability_red_orphaned_true_ending(self):
        """SC2 RED (variant 1): remove the choice.goto edge to end.true
        (change etc.atp_synthase's choice to goto a non-existent node) ->
        end.true becomes unreachable -> is_ok False. Mirrors the
        test_integration.py:348-362 orphan pattern."""
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
        edge -> flagged unreachable. Mirrors test_integration.py:348-356."""
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


if __name__ == "__main__":
    unittest.main()
