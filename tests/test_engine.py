"""Unit tests for c14.engine.GameEngine + TurnResult. Pure-Python, stdlib only.

Run: ``python3.6 -m unittest tests.test_engine -v``

Proves Phase 2 success criterion #3: save serializes GameState (incl. RNG
seed + state); load restores an identical session by replaying the current
node's on_enter MolActions. The engine emits MolAction lists to a mock sink
and NEVER calls cmd.* (the testability boundary -- ``'pymol' not in
sys.modules`` after a full playthrough with save/load).

Uses the real ``data/story`` graph (intro.start -> 2 weighted choices -> 2
endings) and a mock MolAction sink (a plain list's ``.append``).
"""
import os
import shutil
import sys
import tempfile
import unittest

from c14.engine import GameEngine, TurnResult
from c14.story.graph import StoryGraph


def _story_dir():
    # type: () -> str
    """Repo-root data/story/ resolved relative to this test file (CWD-safe)."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "data", "story")


class TestGameEngine(unittest.TestCase):
    """Engine turn-loop tests: start, choose, save/load round-trip, RNG-state
    survival, on_enter replay, no-double-count on load, no-pymol boundary."""

    def setUp(self):
        self._paths = []
        self._dirs = []

    def tearDown(self):
        for p in self._paths:
            try:
                os.unlink(p)
            except OSError:
                pass
        for d in self._dirs:
            try:
                shutil.rmtree(d)
            except OSError:
                pass

    def _story_dir(self):
        # type: () -> str
        return _story_dir()

    def _make_engine(self, seed):
        # type: (object) -> tuple
        """Build a GameEngine over the real data/story graph with a list sink.

        ``seed`` is accepted for call-site symmetry with the plan's examples;
        the actual seed is passed to ``eng.start(...)`` by each test.
        """
        sink = []
        eng = GameEngine(StoryGraph.load(self._story_dir()),
                         molaction_sink=sink.append)
        return eng, sink

    def _tmpfile(self, name="save.json"):
        # type: (str) -> str
        """A path inside a fresh temp dir (cleaned in tearDown)."""
        d = tempfile.mkdtemp()
        self._dirs.append(d)
        p = os.path.join(d, name)
        self._paths.append(p)
        return p

    def test_start_enters_start_node(self):
        """start() enters the start node and dispatches its on_enter MolActions
        to the sink."""
        eng, sink = self._make_engine(0)
        tr = eng.start('glucose', 0)
        self.assertIsInstance(tr, TurnResult)
        self.assertEqual(tr.node.id, 'intro.start', "entered the start node")
        self.assertEqual(len(sink), 2, "start on_enter emits 2 MolActions")
        self.assertEqual(sink[0].op, 'hide_all', "first action is hide_all")

    def test_start_state_initialized(self):
        """After start, GameState is initialized at the start node with the
        recorded seed, character, and a single visit."""
        eng, _ = self._make_engine(0)
        eng.start('glucose', 0)
        self.assertEqual(eng.state.current_node, 'intro.start')
        self.assertEqual(eng.state.character, 'glucose')
        self.assertEqual(eng.state.seed, 0)
        self.assertFalse(eng.state.finished, "not finished at start")
        self.assertEqual(eng.state.visit_counts.get('intro.start'), 1,
                         "start visit recorded once")

    def test_choose_advances_to_ending(self):
        """choose() on intro.start (all weighted) advances to an ending and
        marks GameState finished."""
        eng, _ = self._make_engine(0)
        eng.start('glucose', 0)
        tr = eng.choose(0)
        self.assertIn(tr.node.is_ending, ('good', 'bad'),
                      "choose advances to an ending")
        self.assertTrue(eng.state.finished, "finished after reaching ending")
        self.assertEqual(eng.state.ending_tier, tr.node.is_ending,
                         "ending_tier matches the reached ending")

    def test_weighted_autopick_ignores_index(self):
        """On an all-weighted node the RNG decides; the index is ignored (no
        IndexError even for an out-of-range index). Same seed -> same ending."""
        eng1, _ = self._make_engine(0)
        eng1.start('glucose', 0)
        tr1 = eng1.choose(0)
        self.assertIn(tr1.node.is_ending, ('good', 'bad'))
        eng2, _ = self._make_engine(0)
        eng2.start('glucose', 0)
        tr2 = eng2.choose(99)  # does NOT IndexError (weighted: index unused)
        self.assertIn(tr2.node.is_ending, ('good', 'bad'))
        # Same seed -> same ending (RNG determinism; index had no effect).
        self.assertEqual(tr1.node.id, tr2.node.id,
                         "index ignored on weighted node; RNG decides")

    def test_save_load_roundtrip(self):
        """save then load restores an identical GameState (all fields incl.
        rng_state) and re-enters the current node."""
        eng, _ = self._make_engine(0)
        eng.start('glucose', 0)
        eng.choose(0)  # now at an ending
        p = self._tmpfile()
        eng.save(p)
        sink2 = []
        eng2 = GameEngine(StoryGraph.load(self._story_dir()),
                          molaction_sink=sink2.append)
        tr = eng2.load(p)
        self.assertEqual(eng2.state.to_dict(), eng.state.to_dict(),
                         "load restores identical state (all fields incl "
                         "rng_state)")
        self.assertEqual(tr.node.id, eng.state.current_node,
                         "load re-enters the current node")

    def test_load_replays_on_enter_molactions(self):
        """load replays the current node's on_enter MolActions to the sink,
        reconstructing the molecular scene (success criterion #3)."""
        eng, _ = self._make_engine(0)
        eng.start('glucose', 0)  # at intro.start (on_enter has 2 actions)
        p = self._tmpfile()
        eng.save(p)
        sink2 = []
        eng2 = GameEngine(StoryGraph.load(self._story_dir()),
                          molaction_sink=sink2.append)
        eng2.load(p)
        self.assertGreaterEqual(len(sink2), 1,
                                "load replays the current node's on_enter "
                                "MolActions to reconstruct the scene")

    def test_load_does_not_double_count_visit(self):
        """load re-enters the current node with record_visit=False so the
        visit count is not double-counted."""
        eng, _ = self._make_engine(0)
        eng.start('glucose', 0)  # visit_counts['intro.start'] = 1
        p = self._tmpfile()
        eng.save(p)
        sink2 = []
        eng2 = GameEngine(StoryGraph.load(self._story_dir()),
                          molaction_sink=sink2.append)
        eng2.load(p)
        self.assertEqual(eng2.state.visit_counts.get('intro.start'), 1,
                         "load replay does not double-count visits")

    def test_rng_state_survives_save_load(self):
        """The exact PRNG position survives save/load: the next draw after
        load matches the next draw after save (success criterion #2)."""
        eng, _ = self._make_engine(0)
        eng.start('glucose', 42)
        p = self._tmpfile()
        eng.save(p)  # save BEFORE drawing so both engines are at the same pos
        a = eng.rng.random()
        sink2 = []
        eng2 = GameEngine(StoryGraph.load(self._story_dir()),
                          molaction_sink=sink2.append)
        eng2.load(p)
        b = eng2.rng.random()
        self.assertEqual(a, b,
                         "load restores the exact PRNG position that was saved")

    def test_no_pymol_import(self):
        """After a full playthrough (start+choose+save+load), pymol is not in
        sys.modules -- the testability boundary holds."""
        eng, _ = self._make_engine(0)
        eng.start('glucose', 0)
        eng.choose(0)
        p = self._tmpfile()
        eng.save(p)
        sink2 = []
        eng2 = GameEngine(StoryGraph.load(self._story_dir()),
                          molaction_sink=sink2.append)
        eng2.load(p)
        self.assertNotIn('pymol', sys.modules,
                         "engine never imports pymol (testability boundary)")

    def test_random_seed_mode(self):
        """start(seed=None) is random/play mode: the seed is recorded as an int
        and two random starts pick different seeds (non-deterministic)."""
        eng, _ = self._make_engine(0)
        eng.start('glucose', None)  # random mode
        seed1 = eng.state.seed
        self.assertIsInstance(seed1, int, "random-mode seed recorded as int")
        eng.start('glucose', None)  # second random start
        seed2 = eng.state.seed
        self.assertNotEqual(seed1, seed2,
                            "two random-mode starts pick different seeds")


if __name__ == "__main__":
    unittest.main()
