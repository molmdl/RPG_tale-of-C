"""Unit tests for StoryGraph (loader) + StoryInterpreter (walker).

Proves Phase 2 success criterion #1: a minimal story graph (intro -> weighted
choice -> ending) loads and the interpreter walks it, presenting choices and
advancing to an ending -- all in pure Python with a mock MolAction sink that
collects emitted MolActions and ZERO pymol import (the testability boundary).

Pure-Python, stdlib only. CWD-independent: the story dir is resolved relative
to this test file so the suite runs from any cwd.
"""

import os
import sys
import unittest

from c14.story.graph import StoryGraph
from c14.story.interpreter import StoryInterpreter
from c14.story.model import Choice
from c14.rng import RngEngine
from c14.state import GameState


def _story_dir():
    # type: () -> str
    """Repo-root data/story/ resolved relative to this test file (CWD-safe)."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "data", "story")


class TestStoryGraph(unittest.TestCase):
    """Loader tests: manifest + per-file merge into a {id: Node} dict."""

    def test_load_minimal_story(self):
        g = StoryGraph.load(_story_dir())
        self.assertEqual(g.start_node(), "intro.start", "start from manifest")
        self.assertEqual(len(g), 3, "three nodes (start + 2 endings)")
        self.assertEqual(len(g.endings()), 2, "two endings")
        n = g.get_node("intro.start")
        self.assertEqual(len(n.choices), 2, "two weighted choices")
        self.assertEqual(n.choices[0].weight, 1.0, "choice is weighted")

    def test_get_node_missing_raises(self):
        g = StoryGraph.load(_story_dir())
        with self.assertRaises(KeyError):
            g.get_node("does.not.exist")


class TestStoryInterpreter(unittest.TestCase):
    """Walker tests: weighted pick, MolAction emission, visit recording,
    ending detection, full walk, no-pymol boundary, condition evaluator."""

    def _walk(self, seed):
        # type: (object) -> tuple
        """Full walk: load -> enter start -> weighted pick -> advance -> enter
        ending. Returns ``(ending_node_id, collected_molactions)``.

        The MolAction sink is a plain list (the mock) -- it just collects the
        emitted MolActions; no pymol_layer dispatch happens here.
        """
        g = StoryGraph.load(_story_dir())
        rng = RngEngine(seed)
        st = GameState.new_game("glucose", seed, g.start_node())
        si = StoryInterpreter()
        sink = []  # mock MolAction sink
        start = g.get_node(g.start_node())
        sink.extend(si.enter_node(start, st, rng))
        pick = si.pick_choice(start, st, rng)  # weighted -> single Choice
        si.apply_effects(pick, st)
        end = g.get_node(pick.goto)
        sink.extend(si.enter_node(end, st, rng))
        return end.id, sink

    def test_pick_choice_weighted_returns_single(self):
        g = StoryGraph.load(_story_dir())
        rng = RngEngine(0)
        st = GameState.new_game("glucose", 0, g.start_node())
        si = StoryInterpreter()
        start = g.get_node(g.start_node())
        pick = si.pick_choice(start, st, rng)
        self.assertFalse(isinstance(pick, list),
                         "weighted pick returns a single Choice, not a list")
        self.assertTrue(hasattr(pick, "goto"), "pick is a Choice with a goto")

    def test_pick_choice_deterministic(self):
        end_a, _ = self._walk(0)
        end_b, _ = self._walk(0)
        self.assertEqual(end_a, end_b,
                         "same seed -> same ending (RNG determinism)")

    def test_pick_choice_diff_seed_may_differ(self):
        base, _ = self._walk(0)
        # With weight 1.0/1.0 the split is ~50/50; over seeds 1..20 both
        # endings almost certainly appear, so at least one differs from seed 0.
        # (P(all 20 match seed 0) ~ 2*(0.5)^20 ~= 2e-6 -- robust, not flaky.)
        endings = [self._walk(s)[0] for s in range(1, 21)]
        self.assertTrue(
            any(e != base for e in endings),
            "at least one seed (1..20) picks a different ending than seed 0")

    def test_enter_node_emits_molactions(self):
        g = StoryGraph.load(_story_dir())
        rng = RngEngine(0)
        st = GameState.new_game("glucose", 0, g.start_node())
        si = StoryInterpreter()
        sink = []
        start = g.get_node(g.start_node())
        sink.extend(si.enter_node(start, st, rng))
        self.assertEqual(len(sink), 2, "intro.start on_enter emits 2 MolActions")
        self.assertEqual(sink[0].op, "hide_all", "first action is hide_all")

    def test_enter_node_records_visit(self):
        g = StoryGraph.load(_story_dir())
        rng = RngEngine(0)
        st = GameState.new_game("glucose", 0, g.start_node())
        si = StoryInterpreter()
        si.enter_node(g.get_node(g.start_node()), st, rng)
        self.assertEqual(st.visit_counts.get("intro.start"), 1,
                         "visit count recorded on entry")

    def test_enter_node_detects_ending(self):
        g = StoryGraph.load(_story_dir())
        rng = RngEngine(0)
        st = GameState.new_game("glucose", 0, g.start_node())
        si = StoryInterpreter()
        si.enter_node(g.get_node("intro.ending_good"), st, rng)
        self.assertTrue(st.finished, "finished set on ending entry")
        self.assertEqual(st.ending_tier, "good", "ending_tier is 'good'")

    def test_full_walk_reaches_ending(self):
        end_id, _ = self._walk(0)
        self.assertIn(end_id, ("intro.ending_good", "intro.ending_bad"),
                      "walk reaches an ending node")
        g = StoryGraph.load(_story_dir())
        self.assertIsNotNone(g.get_node(end_id).is_ending,
                             "reached node is an ending")

    def test_full_walk_no_pymol_import(self):
        self._walk(0)
        self.assertNotIn("pymol", sys.modules,
                         "domain layer never imports pymol (testability "
                         "boundary holds)")

    def test_cond_evaluator(self):
        g = StoryGraph.load(_story_dir())
        si = StoryInterpreter()
        st = GameState.new_game("glucose", 0, g.start_node())
        # None cond -> always eligible.
        self.assertTrue(si._cond(None, st), "None cond -> True")
        # char namespace (architecture's char=='glucose' example).
        self.assertTrue(si._cond("char == 'glucose'", st),
                        "char is glucose -> True")
        self.assertFalse(si._cond("char == 'fatty_acid'", st),
                         "char is not fatty_acid -> False")
        # flags namespace (dict .get works with no builtins).
        self.assertFalse(si._cond("flags.get('seen_tca', False)", st),
                         "unset flag -> False")
        st.set_flag("seen_tca", True)
        self.assertTrue(si._cond("flags.get('seen_tca', False)", st),
                        "set flag -> True")
        # malformed cond -> fail-safe False (never crashes).
        self.assertFalse(si._cond("not_a_valid python!!!", st),
                         "malformed cond -> fail-safe False")

    def test_apply_effects(self):
        si = StoryInterpreter()
        st = GameState.new_game("glucose", 0, "intro.start")
        ch = Choice(label="x", goto=None,
                    effects={"set": {"seen_tca": True}, "incr": {"turns": 2}})
        si.apply_effects(ch, st)
        self.assertTrue(st.flag("seen_tca"), "set effect applied to flags")
        self.assertEqual(st.counters.get("turns"), 2, "incr effect applied")


if __name__ == "__main__":
    unittest.main()
