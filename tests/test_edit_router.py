"""SC3 demo: EditRouter routes known -> branch, unknown -> bad-ending pool.

Pure-Python ``unittest``, NO PyMOL (the EditRouter is pure routing; the SC3
demo uses a mock ``molaction_sink = list.append``). Run::

    python3.6 -m unittest tests.test_edit_router -v

Tests map to the SC3 sub-claims (04-RESEARCH-edit-routing.md test list):

- ``TestEditRouter``: known->branch, unknown->pool, RNG determinism, unknown
  enzyme -> global pool, empty pool raises, validation (5 checks), clean
  fixture, coverage scan.
- ``TestGameEngineEditIntegration``: the full SC3 end-to-end -- apply_player_edit
  routes + records in edits_history + enters the routed node with on_enter
  MolActions flowing to the existing molaction_sink; RNG reproducibility; no-
  router raises; backward-compatible constructor widening.
"""

import os
import unittest

from c14.story.model import EditIntent
from c14.story.graph import StoryGraph
from c14.rng import RngEngine
from c14.engine import GameEngine
from c14.edit_router import (
    EditRoutingError, EditsTable, EditRouter,
    validate_edits_table, scan_edit_coverage,
)

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIR = os.path.join(HERE, "fixtures", "edit_routing")
EDITS_PATH = os.path.join(FIXTURE_DIR, "edits.json")

POOL = ["bad.lost_connection", "bad.released_from_host"]


def _load_table():
    # type: () -> EditsTable
    return EditsTable.load(EDITS_PATH)


def _load_graph():
    # type: () -> StoryGraph
    return StoryGraph.load(FIXTURE_DIR)


class TestEditRouter(unittest.TestCase):
    """SC3 routing mechanics (pure routing, no GameEngine)."""

    def test_known_edit_routes_to_branch(self):
        # SC3 known -> branch. The intent target "resi 57 and chain A" (upper)
        # must normalize to "resi 57 and chain a" (lower) to match the table
        # signature (signature() lowercases the target).
        router = EditRouter(_load_table())
        intent = EditIntent("point_mutation", "resi 57 and chain A",
                            {"new_res": "ALA"}, "placeholder_enzyme")
        node_id = router.route(intent, "placeholder_enzyme", RngEngine(0))
        self.assertEqual(node_id, "edit.placeholder_branch")

    def test_unknown_edit_routes_to_bad_ending_pool(self):
        # SC3 unknown -> pool. "resi 999" is not in the table.
        router = EditRouter(_load_table())
        intent = EditIntent("point_mutation", "resi 999",
                            {"new_res": "TRP"}, "placeholder_enzyme")
        node_id = router.route(intent, "placeholder_enzyme", RngEngine(0))
        self.assertIn(node_id, POOL)

    def test_rng_determinism_same_seed_same_pool_pick(self):
        # Same seed -> same bad-ending pick (reproducible). Don't assert r1 !=
        # r3 (could collide); assert both are valid pool members.
        intent = EditIntent("point_mutation", "resi 999",
                            {"new_res": "TRP"}, "placeholder_enzyme")
        r1 = EditRouter(_load_table()).route(intent, "placeholder_enzyme", RngEngine(42))
        r2 = EditRouter(_load_table()).route(intent, "placeholder_enzyme", RngEngine(42))
        self.assertEqual(r1, r2)  # reproducible
        r3 = EditRouter(_load_table()).route(intent, "placeholder_enzyme", RngEngine(7))
        self.assertIn(r3, POOL)  # different seed, still a valid pool member

    def test_unknown_enzyme_falls_through_to_global_pool(self):
        # Enzyme not in the table -> global fallback pool.
        router = EditRouter(_load_table())
        intent = EditIntent("point_mutation", "resi 57",
                            {"new_res": "ALA"}, "no_such_enzyme")
        node_id = router.route(intent, "no_such_enzyme", RngEngine(0))
        self.assertIn(node_id, POOL)

    def test_empty_pool_raises_edit_routing_error(self):
        # Pitfall 2: fail-loud (NOT a bare IndexError) on an empty pool.
        bad_table = EditsTable({
            "version": 1, "bad_ending_pool": [], "enzymes": {},
        })
        router = EditRouter(bad_table)
        with self.assertRaises(EditRoutingError):
            router.route(EditIntent("point_mutation", "x", {}, "e"),
                         "e", RngEngine(0))

    # -- validate_edits_table (5 issue kinds + clean) ------------------------

    def test_validate_edits_table_dangling_branch(self):
        # branch_node not in the story graph.
        nodes = _load_graph().all_nodes()
        table = EditsTable({
            "version": 1,
            "bad_ending_pool": POOL,  # valid
            "enzymes": {
                "placeholder_enzyme": {
                    "edits": [
                        {"signature": {"op": "point_mutation", "target": "x",
                                       "args": {}},
                         "branch_node": "nonexistent",  # DANGLING
                         "claim_id": "c1"},
                    ],
                },
            },
        })
        issues = validate_edits_table(table, nodes)
        self.assertIn("dangling_edit_branch", [i.kind for i in issues])

    def test_validate_edits_table_dangling_pool_node(self):
        # pool node id not in the story graph.
        nodes = _load_graph().all_nodes()
        table = EditsTable({
            "version": 1,
            "bad_ending_pool": ["nonexistent"],  # DANGLING
            "enzymes": {},
        })
        issues = validate_edits_table(table, nodes)
        self.assertIn("dangling_pool_node", [i.kind for i in issues])

    def test_validate_edits_table_empty_pool(self):
        # global pool empty.
        nodes = _load_graph().all_nodes()
        table = EditsTable({
            "version": 1,
            "bad_ending_pool": [],  # EMPTY
            "enzymes": {},
        })
        issues = validate_edits_table(table, nodes)
        self.assertIn("empty_bad_ending_pool", [i.kind for i in issues])

    def test_validate_edits_table_pool_node_not_ending(self):
        # pool node exists but is_ending is None (not an ending).
        nodes = _load_graph().all_nodes()
        table = EditsTable({
            "version": 1,
            "bad_ending_pool": ["edit.start"],  # exists but not an ending
            "enzymes": {},
        })
        issues = validate_edits_table(table, nodes)
        self.assertIn("pool_node_not_ending", [i.kind for i in issues])

    def test_validate_edits_table_duplicate_signature(self):
        # two edits in one enzyme share a signature.
        nodes = _load_graph().all_nodes()
        sig = {"op": "point_mutation", "target": "resi 57 and chain a",
               "args": {"new_res": "ALA"}}
        table = EditsTable({
            "version": 1,
            "bad_ending_pool": POOL,
            "enzymes": {
                "placeholder_enzyme": {
                    "edits": [
                        {"signature": sig, "branch_node": "edit.placeholder_branch",
                         "claim_id": "c1"},
                        {"signature": dict(sig), "branch_node": "edit.placeholder_branch",
                         "claim_id": "c2"},  # DUP (same canonical signature)
                    ],
                },
            },
        })
        issues = validate_edits_table(table, nodes)
        self.assertIn("duplicate_signature", [i.kind for i in issues])

    def test_validate_edits_table_clean(self):
        # The fixture bundle validates to [] (no issues).
        nodes = _load_graph().all_nodes()
        issues = validate_edits_table(_load_table(), nodes)
        self.assertEqual(issues, [])

    # -- scan_edit_coverage (SC5 helper) -------------------------------------

    def test_scan_edit_coverage_green_on_placeholder(self):
        table = _load_table()
        # placeholder_enzyme has >=1 edit entry -> green.
        self.assertEqual(scan_edit_coverage(table, ["placeholder_enzyme"]), [])
        # missing_enzyme has no entry -> flagged.
        issues = scan_edit_coverage(table, ["missing_enzyme"])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].kind, "missing_edit_coverage")
        self.assertEqual(issues[0].node_id, "missing_enzyme")


class TestGameEngineEditIntegration(unittest.TestCase):
    """Full SC3 end-to-end: apply_player_edit routes + records + enters.

    Pure-Python, mock sink (``list.append``); NO PyMOL.
    """

    def test_apply_player_edit_known_enters_branch_emits_on_enter(self):
        sink = []
        eng = GameEngine(
            _load_graph(),
            molaction_sink=sink.append,
            edit_router=EditRouter(_load_table()),
        )
        eng.start("glucose", 0)
        intent = EditIntent("point_mutation", "resi 57 and chain A",
                            {"new_res": "ALA"}, "placeholder_enzyme")
        tr = eng.apply_player_edit(intent, "placeholder_enzyme")
        self.assertEqual(tr.node.id, "edit.placeholder_branch")
        # branch on_enter has the edit MolAction.
        self.assertTrue(any(a.op == "edit" for a in tr.molactions))
        # add_edit recorded it in edits_history.
        self.assertEqual(len(eng.state.edits_history), 1)
        # branch is_ending="good" -> playthrough finished.
        self.assertTrue(eng.state.finished)
        self.assertEqual(eng.state.ending_tier, "good")

    def test_apply_player_edit_unknown_enters_bad_ending(self):
        sink = []
        eng = GameEngine(
            _load_graph(),
            molaction_sink=sink.append,
            edit_router=EditRouter(_load_table()),
        )
        eng.start("glucose", 42)
        intent = EditIntent("point_mutation", "resi 999",
                            {"new_res": "TRP"}, "placeholder_enzyme")
        tr = eng.apply_player_edit(intent, "placeholder_enzyme")
        self.assertIn(tr.node.id, POOL)
        self.assertEqual(eng.state.ending_tier, "bad")

    def test_apply_player_edit_rng_reproducible(self):
        # Two engines, same seed, same unknown intent -> same bad-ending node.
        intent = EditIntent("point_mutation", "resi 999",
                            {"new_res": "TRP"}, "placeholder_enzyme")
        eng1 = GameEngine(_load_graph(), molaction_sink=[].append,
                          edit_router=EditRouter(_load_table()))
        eng1.start("glucose", 42)
        r1 = eng1.apply_player_edit(intent, "placeholder_enzyme").node.id
        eng2 = GameEngine(_load_graph(), molaction_sink=[].append,
                          edit_router=EditRouter(_load_table()))
        eng2.start("glucose", 42)
        r2 = eng2.apply_player_edit(intent, "placeholder_enzyme").node.id
        self.assertEqual(r1, r2)
        self.assertIn(r1, POOL)

    def test_apply_player_edit_no_router_raises(self):
        eng = GameEngine(_load_graph(), molaction_sink=[].append)
        eng.start("glucose", 0)
        intent = EditIntent("point_mutation", "resi 57",
                            {"new_res": "ALA"}, "placeholder_enzyme")
        with self.assertRaises(RuntimeError) as ctx:
            eng.apply_player_edit(intent, "placeholder_enzyme")
        self.assertIn("no edit_router", str(ctx.exception))

    def test_backward_compat_no_edit_router(self):
        # The existing Phase 2 path (GameEngine(graph), no edit_router, no sink)
        # still works -- backward-compatible constructor widening.
        eng = GameEngine(_load_graph())
        tr = eng.start("glucose", 0)
        self.assertIsNotNone(tr)
        self.assertEqual(tr.node.id, "edit.start")
        # start/choose/_enter/save/load are unchanged; no edit_router attr use.
        self.assertIsNone(eng.edit_router)


if __name__ == "__main__":
    unittest.main()
