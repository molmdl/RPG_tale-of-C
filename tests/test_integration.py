"""End-to-end integration test: proves the Phase 2 architecture in WSL.

Full playthrough with a mock MolAction sink (success criterion #1), RNG
determinism across seeds (#2), save/load round-trip with on_enter replay
(#3), reachability green/red (#4), and the refactored citation gate working
on the multi-file story directory. Pure Python, stdlib only -- NO PyMOL.

This is the capstone of Phase 2. Plans 01-04 built the pieces (model, rng,
state, graph, interpreter, validate, persist, engine) in isolation with unit
tests; this test wires them together and proves the WHOLE system works as one
in pure Python before any PyMOL/Qt code is written. Running::

    python3.6 -m unittest tests.test_integration -v

exercises the full stack end-to-end: GameEngine drives StoryInterpreter over
StoryGraph with RngEngine + GameState, SaveStore round-trips, and
check_reachability validates -- all in pure Python with a mock MolAction sink.

Design constraints honored:
- Python 3.6 stdlib ONLY (``unittest``, ``os``, ``sys``, ``tempfile``, ``json``,
  ``collections``, ``subprocess``, ``shutil``). NO pymol/PyQt5 imports.
- subprocess uses ``stdout/stderr=PIPE`` + manual decode (NOT
  ``capture_output`` / ``text`` -- both 3.7+; matches the verified Phase 1
  pattern in tests/test_citations.py). Uses ``sys.executable`` (not a
  hardcoded interpreter) so the same python running the test runs the gate.
- CWD-independent: the story dir + repo root are resolved relative to this
  test file (``__file__``-relative), matching the Phase 1 invariant.
- The module imports the full domain stack at the top level (GameEngine,
  StoryGraph, RngEngine, GameState, SaveStore, check_reachability,
  validate_graph, Node) -- this proves the ENTIRE stack imports in pure
  Python (the ``test_no_pymol_import_full_stack`` / ``test_no_pyqt`` checks
  then confirm none of those transitively pulled pymol/Qt).
- ``GameEngine`` dispatches MolActions PER-ACTION to the sink (the 02-04
  deviation): ``self.molaction_sink(action)`` per action, so a plain list's
  ``.append`` collects individual ``MolAction`` objects (not lists). The
  toy story's ``intro.start`` on_enter emits 2 actions (hide_all, load) and
  each ending's on_enter emits 1 (hide_all); after start + choose the sink
  holds 3 individual MolAction objects.
"""

import collections
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

# Full-domain-stack import: proves every module imports in pure Python (the
# test_no_pymol/pyqt checks below confirm none of these pulled PyMOL/Qt).
from c14.engine import GameEngine  # noqa: F401 (used directly)
from c14.story.graph import StoryGraph  # noqa: F401 (used directly)
from c14.rng import RngEngine  # noqa: F401 (imported to prove clean import)
from c14.state import GameState  # noqa: F401 (imported to prove clean import)
from c14.persist import SaveStore  # noqa: F401 (imported to prove clean import)
from c14.story.validate import check_reachability, validate_graph  # noqa: F401
from c14.story.model import Node  # noqa: F401 (used for the orphaned variant)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(HERE, "..")
GATE_SCRIPT = os.path.join(REPO_ROOT, "tools", "check_citations.py")


def _write_temp_registry(content):
    """Write ``content`` (a JSON string) to a NamedTemporaryFile; return path.

    Caller must ``os.unlink(path)`` when done. ``delete=False`` so the file
    survives closing (CitationRegistry.load re-opens it). Matches the
    verified Phase 1 pattern in tests/test_citations.py.
    """
    fh = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        fh.write(content)
        fh.flush()
    finally:
        fh.close()
    return fh.name


class TestEndToEndArchitecture(unittest.TestCase):
    """End-to-end architecture proof: the four Phase 2 success criteria in one
    place. Full playthrough + RNG determinism + save/load round-trip +
    reachability green/red, all in pure Python with a mock MolAction sink.
    """

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

    # -- helpers ----------------------------------------------------------

    def _story_dir(self):
        # type: () -> str
        """Repo-root data/story/ resolved relative to this test file (CWD-safe)."""
        return os.path.join(HERE, "..", "data", "story")

    def _tmpfile(self, name="save.json"):
        # type: (str) -> str
        """A path inside a fresh temp dir (cleaned in tearDown)."""
        d = tempfile.mkdtemp()
        self._dirs.append(d)
        p = os.path.join(d, name)
        self._paths.append(p)
        return p

    def _play(self, seed, sink):
        # type: (object, list) -> tuple
        """Play a full game: start -> weighted choice -> ending.

        Builds a GameEngine over the real data/story graph with ``sink.append``
        as the MolAction sink (per-action dispatch -- the 02-04 contract: the
        sink receives individual MolAction objects), starts at 'glucose' with
        ``seed``, makes choice 0 (weighted -- the RNG decides; index ignored),
        and returns ``(engine, turn_result_at_ending)``.
        """
        eng = GameEngine(StoryGraph.load(self._story_dir()),
                         molaction_sink=sink.append)
        eng.start('glucose', seed)
        tr = eng.choose(0)
        return eng, tr

    # ====================================================================
    # Success criterion #1: full playthrough with mock sink, no PyMOL
    # ====================================================================

    def test_full_playthrough_reaches_ending(self):
        """A full playthrough (start -> weighted choice -> ending) reaches an
        ending node, marks GameState finished, and records the ending tier."""
        sink = []
        eng, tr = self._play(0, sink)
        self.assertIn(tr.node.is_ending, ('good', 'bad'),
                      "playthrough reaches an ending node")
        self.assertTrue(eng.state.finished, "GameState finished after ending")
        self.assertEqual(eng.state.ending_tier, tr.node.is_ending,
                         "ending_tier matches the reached ending")

    def test_playthrough_emits_molactions_to_mock_sink(self):
        """The mock MolAction sink collects the on_enter MolActions emitted
        at the start node (hide_all + load) AND at the ending node (hide_all)
        -- 3 individual MolAction objects via per-action dispatch."""
        sink = []
        self._play(0, sink)
        # intro.start on_enter = [hide_all, load]; ending on_enter = [hide_all]
        # => 3 individual MolAction objects collected via sink.append.
        self.assertGreaterEqual(len(sink), 3,
                                "start(2) + ending(1) on_enter MolActions")
        ops = set(a.op for a in sink)
        self.assertIn('hide_all', ops, "hide_all MolAction emitted")
        self.assertIn('load', ops, "load MolAction emitted at start node")

    def test_no_pymol_import_full_stack(self):
        """After a full playthrough, pymol is not in sys.modules -- the entire
        stack (engine + interpreter + graph + rng + state + persist + validate)
        never imported pymol; the testability boundary holds end-to-end."""
        sink = []
        self._play(0, sink)
        self.assertNotIn('pymol', sys.modules,
                         "full stack imports no pymol (SC1 testability boundary)")

    def test_no_pyqt_import_full_stack(self):
        """After a full playthrough, PyQt5 is not in sys.modules -- no Qt
        anywhere in the domain stack (the GUI layer is a future Phase 6
        concern, strictly separated from the pure-Python engine)."""
        sink = []
        self._play(0, sink)
        self.assertNotIn('PyQt5', sys.modules,
                         "full stack imports no PyQt5 (GUI is Phase 6)")

    # ====================================================================
    # Success criterion #2: RNG determinism
    # ====================================================================

    def test_same_seed_same_ending(self):
        """Same seed produces the same ending across two independent runs
        (RNG determinism: the single seeded RngEngine carries through)."""
        sink1 = []
        eng1, tr1 = self._play(0, sink1)
        sink2 = []
        eng2, tr2 = self._play(0, sink2)
        self.assertEqual(tr1.node.is_ending, tr2.node.is_ending,
                         "same seed -> same ending tier (determinism)")

    def test_same_seed_same_molaction_sequence(self):
        """Same seed produces the same MolAction sequence (same op/target/args
        in order) -- the whole playthrough is reproducible, not just the
        ending."""
        sink1 = []
        self._play(0, sink1)
        sink2 = []
        self._play(0, sink2)
        seq1 = [(a.op, a.target, a.args) for a in sink1]
        seq2 = [(a.op, a.target, a.args) for a in sink2]
        self.assertEqual(seq1, seq2,
                         "same seed -> identical MolAction sequence")

    def test_diff_seed_both_endings_appear(self):
        """Different seeds produce different outcomes: across seeds 0..30
        both endings appear (50/50 weights -> 31 seeds robustly cover both;
        P(one missing) ~ 2*(0.5)^31 ~= 9e-10 -- not flaky)."""
        endings = []
        for s in range(31):
            sink = []
            _, tr = self._play(s, sink)
            endings.append(tr.node.is_ending)
        dist = collections.Counter(endings)
        self.assertEqual(set(dist), {'good', 'bad'},
                         "both endings appear across seeds 0..30 (SC2); "
                         "distribution: {}".format(dict(dist)))

    def test_random_mode_reproducible_after_record(self):
        """A random-mode run (seed=None) is replayable from its recorded seed:
        the auto-picked seed is saved with GameState, and a fresh start with
        that seed reaches the same ending as the random run did (classroom
        reproducibility)."""
        g = StoryGraph.load(self._story_dir())
        noop = lambda a: None  # noqa: E731 (lambda acceptable in tests)
        eng = GameEngine(g, molaction_sink=noop)
        eng.start('glucose', None)  # random/play mode
        recorded_seed = eng.state.seed
        self.assertIsInstance(recorded_seed, int, "random seed recorded as int")
        p = self._tmpfile()
        eng.save(p)
        # load restores the recorded seed
        eng2 = GameEngine(g, molaction_sink=noop)
        eng2.load(p)
        self.assertEqual(eng2.state.seed, recorded_seed,
                         "loaded session carries the recorded seed")
        # play the random-mode run to its ending
        tr_random = eng.choose(0)
        # replay from the recorded seed -> same ending
        eng3 = GameEngine(g, molaction_sink=noop)
        eng3.start('glucose', recorded_seed)
        tr_replay = eng3.choose(0)
        self.assertEqual(tr_random.node.is_ending, tr_replay.node.is_ending,
                         "random-mode run replayable from its recorded seed")

    # ====================================================================
    # Success criterion #3: save/load round-trip
    # ====================================================================

    def test_save_load_restores_identical_state(self):
        """save -> load restores an identical GameState (every field incl.
        rng_state, current_node, visit_counts, ending_tier)."""
        sink = []
        eng, _ = self._play(0, sink)
        p = self._tmpfile()
        eng.save(p)
        eng2 = GameEngine(StoryGraph.load(self._story_dir()),
                          molaction_sink=lambda a: None)
        eng2.load(p)
        self.assertEqual(eng2.state.to_dict(), eng.state.to_dict(),
                         "load restores identical state (all fields incl "
                         "rng_state)")

    def test_save_load_replays_on_enter(self):
        """After load, the fresh engine's sink collected the current (ending)
        node's on_enter MolActions -- the scene is reconstructed by replaying
        on_enter (Pattern 6: the molecular scene is a pure function of game
        state, NOT a saved .pse session)."""
        sink = []
        eng, _ = self._play(0, sink)
        p = self._tmpfile()
        eng.save(p)
        sink2 = []
        eng2 = GameEngine(StoryGraph.load(self._story_dir()),
                          molaction_sink=sink2.append)
        eng2.load(p)
        self.assertGreaterEqual(len(sink2), 1,
                                "load replays the current node's on_enter "
                                "MolActions to reconstruct the scene")

    def test_save_mid_playthrough_load_continues_same(self):
        """The strongest save/load proof: save MID-playthrough (at intro.start,
        before the choice), then load + choose reaches the SAME ending as
        continuing without saving. The save/load preserved the exact RNG
        position, so both paths draw the same weighted pick."""
        g = StoryGraph.load(self._story_dir())
        eng1 = GameEngine(g, molaction_sink=lambda a: None)
        eng1.start('glucose', 42)  # at intro.start, rng_state captured
        p = self._tmpfile()
        eng1.save(p)  # save BEFORE choose (mid-playthrough)
        tr1 = eng1.choose(0)  # ending1 -- never saved, just continued
        eng2 = GameEngine(g, molaction_sink=lambda a: None)
        eng2.load(p)  # restore the mid-playthrough state
        tr2 = eng2.choose(0)  # ending2 -- continued from the save
        self.assertEqual(tr1.node.is_ending, tr2.node.is_ending,
                         "mid-playthrough save -> load -> continue reaches the "
                         "same ending as never saving (RNG position preserved)")

    def test_save_load_no_double_visit(self):
        """load re-enters the current node with record_visit=False so the
        visit count is NOT double-counted (start visit == 1 after load)."""
        g = StoryGraph.load(self._story_dir())
        eng = GameEngine(g, molaction_sink=lambda a: None)
        eng.start('glucose', 0)  # visit_counts['intro.start'] = 1
        self.assertEqual(eng.state.visit_counts.get('intro.start'), 1)
        p = self._tmpfile()
        eng.save(p)
        eng2 = GameEngine(g, molaction_sink=lambda a: None)
        eng2.load(p)
        self.assertEqual(eng2.state.visit_counts.get('intro.start'), 1,
                         "load replay does not double-count visits")

    def test_save_file_is_human_readable_json(self):
        """The save file is valid, human-readable JSON containing the key
        state fields (current_node, seed, rng_state) as text -- diff-friendly
        (Decision D2)."""
        sink = []
        eng, _ = self._play(0, sink)
        p = self._tmpfile()
        eng.save(p)
        with open(p, "r", encoding="utf-8") as fh:
            txt = fh.read()
        json.loads(txt)  # raises if not valid JSON
        self.assertIn('"current_node"', txt, "current_node present as text")
        self.assertIn('"seed"', txt, "seed present as text")
        self.assertIn('"rng_state"', txt, "rng_state present as text")

    # ====================================================================
    # Success criterion #4: reachability green/red
    # ====================================================================

    def test_reachability_green_on_toy_graph(self):
        """check_reachability is green on the real data/story graph: both
        endings are reachable from intro.start (no orphaned endings)."""
        g = StoryGraph.load(self._story_dir())
        rep = check_reachability(g.all_nodes(), g.start_node())
        self.assertTrue(rep.is_ok, "toy graph has no orphaned endings")
        self.assertEqual(set(rep.reachable_endings),
                         {'intro.ending_good', 'intro.ending_bad'},
                         "both endings reachable from intro.start")
        self.assertEqual(rep.unreachable_endings, [],
                         "no unreachable endings on the toy graph")

    def test_reachability_red_on_orphaned_variant(self):
        """check_reachability is red on a deliberately-orphaned variant: an
        extra ending node with no incoming edge is flagged unreachable."""
        g = StoryGraph.load(self._story_dir())
        orphaned = dict(g.all_nodes())  # copy the {id: Node} dict
        # add an orphaned ending (no choices, no incoming edge) as a Node
        orphaned["intro.ending_orphan"] = Node.from_dict({
            "id": "intro.ending_orphan",
            "is_ending": "bad",
            "choices": [],
        })
        rep = check_reachability(orphaned, g.start_node())
        self.assertFalse(rep.is_ok, "orphaned variant is not ok (red)")
        self.assertIn("intro.ending_orphan", rep.unreachable_endings,
                      "the orphaned ending is flagged unreachable")

    def test_validate_graph_clean_on_toy_graph(self):
        """validate_graph returns [] (no issues) on the toy graph -- no
        dangling diverts in the well-formed data/story."""
        g = StoryGraph.load(self._story_dir())
        issues = validate_graph(g.all_nodes())
        self.assertEqual(issues, [], "toy graph validates clean (no issues)")

    # ====================================================================
    # Cross-cutting: refactored citation gate on the multi-file story dir
    # ====================================================================

    def test_citation_gate_on_toy_story(self):
        """The refactored citation gate (Phase 2 walker in
        c14.story.validate.collect_claim_ids) works on the multi-file
        data/story directory end-to-end: with the toy story's 3 placeholder
        claim_ids all approved, the gate exits 0."""
        # temp registry: the toy story's 3 placeholder claims, all approved
        registry = {
            "placeholder-intro": {"approval_status": "approved"},
            "placeholder-good-ending": {"approval_status": "approved"},
            "placeholder-bad-ending": {"approval_status": "approved"},
        }
        reg_path = _write_temp_registry(json.dumps(registry))
        try:
            r = subprocess.run(
                [sys.executable, GATE_SCRIPT,
                 "--story", self._story_dir(),
                 "--registry", reg_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            stdout = r.stdout.decode("utf-8")
            stderr = r.stderr.decode("utf-8")
            self.assertEqual(r.returncode, 0,
                             "gate exits 0 (all placeholder claims approved)\n"
                             "stdout=%r\nstderr=%r" % (stdout, stderr))
            self.assertIn("PASSED", stdout, "gate reports a pass")
        finally:
            os.unlink(reg_path)


if __name__ == "__main__":
    unittest.main()
