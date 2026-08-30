"""Unit tests for rpg.ui.controller (Controller + HeroResolver). Pure WSL.

Run: ``python3.6 -m unittest tests.test_controller -v``

The controller is the Qt-free mediator (06-06 Task 2): it wires QtWidgets
events -> GameEngine -> MolOps. These tests inject MockMolOps + MockView + mock
prompt_fn/count_fn + a real EditRouter (loaded from rpg/data/edits.json) and
drive the controller over the REAL data/story_glucose graph. NO pymol import
(the controller is Qt-free; the test module imports rpg.ui.controller which
imports only rpg.* domain modules + stdlib -- the implicit Qt-free gate).

Covers (06-06 Task 3's 18 tests):
- engine wiring (molaction_sink = controller's dispatch)
- start/choose/take_choice/apply_edit/request_edit/save/load routing
- tca.shuffle routing via engine.goto (SC#3 Blocker B fix)
- request_edit stashes enzyme_id + gotos edit.prompt (Warning 4 seam)
- build_edit_intent fallback to _pending_edit_enzyme_id at edit.prompt
- _dispatch_molaction swallows molops failure + continues (Blocker 1 fix c)
- achievement board called (is_new_game=True only on start)
- HeroResolver 4 cases (single-C no-op, multi-C prompt, rejected, no-highlight)
- is_mixed_weighted_node detects tca.shuffle
- Qt-free import (implicit gate)
"""
import contextlib
import io
import os
import shutil
import tempfile
import unittest

import rpg.paths
from rpg.edit_router import EditRouter, EditsTable
from rpg.story.model import Choice, EditIntent, MolAction, Node
from rpg.ui.controller import Controller, HeroResolver


def _story_dir():
    # type: () -> str
    """Repo-root data/story_glucose/ resolved relative to this test file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "data", "story_glucose")


def _edits_path():
    # type: () -> str
    """The bundled rpg/data/edits.json placeholder fixture."""
    return str(rpg.paths.data_path("data", "edits.json"))


# ---- mocks (no pymol -- the controller is Qt-free + cmd-injected) ----

class MockMolOps(object):
    """Records every apply(action) call. Optionally raises on configured
    0-based call indices (for the Blocker 1 fix c swallow test)."""

    def __init__(self, fail_indices=None):
        self.calls = []  # type: list
        self.fail_indices = set(fail_indices or [])

    def apply(self, action):
        idx = len(self.calls)
        self.calls.append(action)  # append BEFORE the raise so the call is recorded
        if idx in self.fail_indices:
            raise RuntimeError(
                "mock molops failure on call {}".format(idx))


class MockView(object):
    """Records every render_turn(turn) call."""

    def __init__(self):
        self.turns = []  # type: list

    def render_turn(self, turn):
        self.turns.append(turn)


class MockAchievementBoard(object):
    """Records every on_turn(turn, character, is_new_game) call."""

    def __init__(self):
        self.calls = []  # type: list

    def on_turn(self, turn, character, is_new_game=False):
        self.calls.append((turn, character, is_new_game))


class TestController(unittest.TestCase):
    """Controller mediator tests: engine wiring, routing (choose/take_choice/
    apply_edit/request_edit/save/load), achievement calls, is_mixed_weighted_node,
    _dispatch_molaction swallow, request_edit seam, build_edit_intent fallback."""

    def _make_controller(self, molops=None, view=None, prompt_fn=None,
                         count_fn=None, achievement_board=None):
        # type: (object, object, object, object, object) -> Controller
        """Build a Controller over the real glucose graph with a real EditRouter
        (from rpg/data/edits.json) + the injected mocks. cmd=None (count_fn is
        injected or unused when prompt_fn is None)."""
        edit_router = EditRouter(EditsTable.load(_edits_path()))
        return Controller(
            _story_dir(),
            molops if molops is not None else MockMolOps(),
            None,  # cmd -- unused (count_fn injected or no hero resolver)
            edit_router,
            view=view,
            prompt_fn=prompt_fn,
            count_fn=count_fn,
            achievement_board=achievement_board)

    # 1. engine wiring
    def test_engine_wiring_molaction_sink(self):
        """The engine's molaction_sink IS the controller's _dispatch_molaction
        (the controller wired itself as the sink at construction). Bound methods
        are fresh objects per access, so compare via == (which checks __self__
        + __func__) not `is`."""
        c = self._make_controller()
        self.assertEqual(c._engine.molaction_sink, c._dispatch_molaction,
                         "the engine's molaction_sink IS the controller's dispatch")
        # Also confirm the underlying function + instance match (belt + braces).
        self.assertIs(c._engine.molaction_sink.__func__,
                      Controller._dispatch_molaction,
                      "the sink's underlying function is _dispatch_molaction")
        self.assertIs(c._engine.molaction_sink.__self__, c,
                      "the sink's instance is the controller")

    # 2. start_game dispatches on_enter + renders
    def test_start_game_dispatches_on_enter_and_renders(self):
        """start_game dispatches intro.preface's on_enter MolActions to molops +
        renders the TurnResult (node.id == 'intro.preface')."""
        molops = MockMolOps()
        view = MockView()
        c = self._make_controller(molops=molops, view=view)
        turn = c.start_game("glucose", 42)
        self.assertGreaterEqual(len(molops.calls), 1,
                                "start_game dispatched intro.preface's on_enter to molops")
        self.assertEqual(len(view.turns), 1, "render_turn called once")
        self.assertEqual(view.turns[0].node.id, "intro.preface")
        self.assertEqual(c._engine.state.current_node, "intro.preface")

    # 3. choose forwards to engine.choose
    def test_choose_forwards_to_engine_choose(self):
        """choose(index) advances the current node + renders (the Continue
        choice at intro.preface -> intro.select)."""
        molops = MockMolOps()
        view = MockView()
        c = self._make_controller(molops=molops, view=view)
        c.start_game("glucose", 42)  # intro.preface
        view.turns.clear()
        c.choose(0)  # Continue -> intro.select
        self.assertNotEqual(c._engine.state.current_node, "intro.preface",
                            "choose advanced the current node")
        self.assertEqual(len(view.turns), 1, "render_turn called once after choose")

    # 4. take_choice uses engine.goto (tca.shuffle routing, Blocker B fix)
    def test_take_choice_uses_engine_goto(self):
        """take_choice(non_weighted_choice) routes via engine.goto (NOT choose,
        which would RNG-pick among the weighted choices). At tca.shuffle, the
        edit:offer choice -> edit.prompt (a non-weighted-choice target the RNG
        could never pick)."""
        molops = MockMolOps()
        view = MockView()
        c = self._make_controller(molops=molops, view=view)
        c.start_game("glucose", 42)  # intro.preface
        # Move to tca.shuffle directly (bypassing the long glycolysis path; the
        # UI would reach tca.shuffle via normal gameplay). MockMolOps records
        # the on_enter dispatch (no real PyMOL load).
        c._engine.goto("tca.shuffle")
        shuffle = c._engine.graph.get_node("tca.shuffle")
        edit_choice = next(ch for ch in shuffle.choices
                           if "edit:offer" in (ch.tags or []))
        c.take_choice(edit_choice)
        self.assertEqual(c._engine.state.current_node, "edit.prompt",
                         "take_choice used engine.goto -> edit.prompt (NOT "
                         "choose, which would RNG-pick among the weighted choices)")

    # 5. apply_edit reads enzyme_id from tags + routes
    def test_apply_edit_reads_enzyme_id_from_tags_and_routes(self):
        """At tca.citrate_synthase (edit:enzyme:tca.citrate_synthase tag),
        build_edit_intent reads the enzyme_id from the tag; apply_edit routes
        via the EditRouter. tca.citrate_synthase is NOT in edits.json -> unknown
        enzyme -> bad-ending pool."""
        molops = MockMolOps()
        view = MockView()
        c = self._make_controller(molops=molops, view=view)
        c.start_game("glucose", 42)
        c._engine.goto("tca.citrate_synthase")  # edit-allowed node
        intent = c.build_edit_intent("point_mutation", "resi 1", {"new_res": "GLY"})
        self.assertEqual(intent.enzyme_id, "tca.citrate_synthase",
                         "build_edit_intent read the enzyme_id from the current "
                         "node's edit:enzyme:<id> tag")
        c.apply_edit(intent)
        self.assertIn(c._engine.state.current_node,
                      ("bad.lost_connection", "bad.released_from_host"),
                      "apply_edit routed the unknown enzyme to the bad-ending pool")
        self.assertEqual(len(c._engine.state.edits_history), 1,
                         "the edit was recorded in edits_history")

    # 6. apply_edit raises when no enzyme tag AND intent carries no enzyme_id
    def test_apply_edit_raises_when_no_enzyme_tag(self):
        """At a non-edit node (intro.preface has no edit:enzyme tag) with an
        EditIntent that carries no enzyme_id, apply_edit raises RuntimeError
        (cannot route an edit without an enzyme_id from either source)."""
        c = self._make_controller()
        c.start_game("glucose", 42)  # intro.preface (no edit:enzyme tag)
        intent = EditIntent("point_mutation", "resi 1", {"new_res": "GLY"})  # enzyme_id=None
        with self.assertRaises(RuntimeError):
            c.apply_edit(intent)

    # 6b. apply_edit falls back to edit_intent.enzyme_id at edit.prompt
    def test_apply_edit_falls_back_to_intent_enzyme_id(self):
        """At a non-edit node (intro.preface has no edit:enzyme tag), if the
        EditIntent carries an enzyme_id (as build_edit_intent stashes it at
        edit.prompt), apply_edit uses that enzyme_id + routes (no raise). This
        is the edit.prompt seam: the enzyme_id comes from the source node via the
        intent, not from the current node. tca.citrate_synthase is NOT in
        edits.json -> unknown enzyme -> bad-ending pool (mirrors test #5)."""
        molops = MockMolOps()
        view = MockView()
        c = self._make_controller(molops=molops, view=view)
        c.start_game("glucose", 42)  # intro.preface (no edit:enzyme tag)
        # build_edit_intent would stash the enzyme_id into the intent; simulate
        # that by constructing an intent carrying an enzyme_id that routes to
        # the bad-ending pool (an unknown edit) -- the EditRouter's global pool.
        intent = EditIntent("point_mutation", "resi 999",
                            {"new_res": "ZZZ"}, "tca.citrate_synthase")
        c.apply_edit(intent)  # must NOT raise
        self.assertIn(c._engine.state.current_node,
                      ("bad.lost_connection", "bad.released_from_host"),
                      "apply_edit routed via the EditIntent's enzyme_id (no raise) "
                      "to the bad-ending pool")
        self.assertEqual(len(c._engine.state.edits_history), 1,
                         "the edit was recorded in edits_history")

    # 7. save/load call engine
    def test_save_load_call_engine(self):
        """save writes the state file (engine.save); load restores + renders the
        turn (engine.load replays on_enter via the controller's dispatch)."""
        molops = MockMolOps()
        view = MockView()
        c = self._make_controller(molops=molops, view=view)
        c.start_game("glucose", 42)
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        path = os.path.join(tmpdir, "save.json")
        c.save(path)
        self.assertTrue(os.path.isfile(path), "engine.save wrote the state file")
        view.turns.clear()
        c.load(path)
        self.assertEqual(len(view.turns), 1, "load rendered the restored turn")
        self.assertEqual(view.turns[0].node.id, "intro.preface",
                         "load restored the current node")

    # 8. achievement board called on start (is_new_game=True) + choose (False)
    def test_achievement_board_called_on_start(self):
        """start_game calls board.on_turn with is_new_game=True; choose calls it
        with is_new_game=False."""
        board = MockAchievementBoard()
        c = self._make_controller(achievement_board=board)
        c.start_game("glucose", 42)
        self.assertEqual(len(board.calls), 1, "on_turn called once on start")
        _, char, is_new = board.calls[0]
        self.assertEqual(char, "glucose")
        self.assertTrue(is_new, "is_new_game=True on start_game")
        board.calls.clear()
        c.choose(0)
        self.assertEqual(len(board.calls), 1, "on_turn called once on choose")
        _, _, is_new = board.calls[0]
        self.assertFalse(is_new, "is_new_game=False on choose")

    # 9. HeroResolver no-op on single-C
    def test_hero_resolver_noop_on_single_C(self):
        """count_fn returns 1 (single-C): resolve returns the actions UNCHANGED
        (same object) + prompt_fn NOT called (deterministic, no prompt)."""
        prompt_calls = []  # type: list
        prompt_fn = lambda msg: prompt_calls.append(msg) or True  # noqa: E731
        resolver = HeroResolver(lambda sele: 1, prompt_fn)
        actions = self._hero_on_enter()
        result = resolver.resolve(actions)
        self.assertIs(result, actions, "single-C: resolve returns the same list (no-op)")
        self.assertEqual(prompt_calls, [], "prompt_fn NOT called on single-C")

    # 10. HeroResolver prompts on multi-C
    def test_hero_resolver_prompts_on_multi_C(self):
        """count_fn returns 3 (multi-C), prompt_fn returns True: resolve returns
        a NEW list with the hero ops' sele rewritten to the default first-C +
        prompt_fn called once with a message containing '3 carbons'."""
        prompt_calls = []  # type: list
        prompt_fn = lambda msg: prompt_calls.append(msg) or True  # noqa: E731
        resolver = HeroResolver(lambda sele: 3, prompt_fn)
        actions = self._hero_on_enter()
        result = resolver.resolve(actions)
        self.assertIsNot(result, actions,
                         "multi-C + confirmed: resolve returns a NEW list")
        self.assertEqual(len(prompt_calls), 1, "prompt_fn called once")
        self.assertIn("3 carbons", prompt_calls[0],
                      "prompt message mentions the carbon count")
        # The hero ops' sele rewritten to the default first-C: the sele MUST
        # resolve to EXACTLY ONE carbon (06-14 SC2a fix -- the old
        # "<obj> and elem C" matched ALL carbons; `first (...)` picks one;
        # empirically verified headlessly -- tools/probe_first_operator.py).
        expected_default_sele = "first (hero_atom and elem C)"
        label = next(a for a in result if a.op == "label")
        self.assertEqual(label.args["sele"], expected_default_sele,
                         "label sele rewritten to default first-C (exactly 1 atom)")
        show_spheres = next(a for a in result
                            if a.op == "show" and a.args.get("rep") == "spheres")
        self.assertEqual(show_spheres.args["sele"], expected_default_sele,
                         "show spheres sele rewritten")
        set_sphere = next(a for a in result
                          if a.op == "set" and a.args.get("name") == "sphere_scale")
        self.assertEqual(set_sphere.args["sele"], expected_default_sele,
                         "set sphere_scale sele rewritten")
        # show_as sticks + color KEEP their object-wide sele (not rewritten;
        # the all-C-cyan scopes to elem C per the 5.4 convention).
        show_as = next(a for a in result if a.op == "show_as")
        self.assertNotIn("sele", show_as.args,
                         "show_as sticks keeps object-wide sele (no sele key)")
        color = next(a for a in result if a.op == "color")
        self.assertEqual(color.args["sele"], "hero_atom and elem C",
                         "color keeps the all-C object-wide sele (5.4 convention)")

    # 11. HeroResolver rejected leaves unchanged
    def test_hero_resolver_rejected_leaves_unchanged(self):
        """count_fn=3, prompt_fn returns False: resolve returns the actions
        UNCHANGED (same object)."""
        resolver = HeroResolver(lambda sele: 3, lambda msg: False)  # noqa: E731
        actions = self._hero_on_enter()
        result = resolver.resolve(actions)
        self.assertIs(result, actions,
                      "rejected: resolve returns the same list (unchanged)")

    # 12. HeroResolver no-op when no hero-highlight
    def test_hero_resolver_noop_when_no_hero_highlight(self):
        """on_enter with no 'YOU' label: resolve returns unchanged + count_fn
        NOT called (no hero-highlight to resolve)."""
        count_calls = []  # type: list
        count_fn = lambda sele: count_calls.append(sele) or 1  # noqa: E731
        resolver = HeroResolver(count_fn, lambda msg: True)  # noqa: E731
        actions = [MolAction("hide_all"), MolAction("load", "x", {"object": "y"})]
        result = resolver.resolve(actions)
        self.assertIs(result, actions, "no hero-highlight: resolve returns unchanged")
        self.assertEqual(count_calls, [],
                         "count_fn NOT called when no hero highlight")

    # 13. is_mixed_weighted_node detects tca.shuffle
    def test_is_mixed_weighted_node_detects_tca_shuffle(self):
        """tca.shuffle has 2 weighted + non-weighted (edit:offer; cycle-trap is
        cond-gated) -> is_mixed_weighted_node returns True."""
        c = self._make_controller()
        c.start_game("glucose", 42)  # need state for choice_cond_met
        shuffle = c._engine.graph.get_node("tca.shuffle")
        self.assertTrue(c.is_mixed_weighted_node(shuffle),
                        "tca.shuffle is mixed (weighted + non-weighted eligible)")

    # 14. is_mixed_weighted_node False for pure nodes
    def test_is_mixed_weighted_node_false_for_pure_nodes(self):
        """intro.preface (pure-MC, no weighted) -> False; a pure-weighted
        fixture node -> False."""
        c = self._make_controller()
        c.start_game("glucose", 42)
        preface = c._engine.graph.get_node("intro.preface")
        self.assertFalse(c.is_mixed_weighted_node(preface),
                         "intro.preface is pure-MC (no weighted choices)")
        pure_weighted = Node(id="test.pure_weighted", choices=[
            Choice("a", goto="x", weight=1.0),
            Choice("b", goto="y", weight=1.0),
        ])
        self.assertFalse(c.is_mixed_weighted_node(pure_weighted),
                         "pure-weighted node is not mixed")

    # 15. controller Qt-free import (implicit gate)
    def test_controller_qt_free_imports(self):
        """Importing rpg.ui.controller succeeds in pure WSL (no pymol/PyQt5).
        This test's module-level import already proves this; re-import +
        assert no pymol/PyQt5 leaked into sys.modules."""
        import importlib
        import sys
        mod = importlib.import_module("rpg.ui.controller")
        self.assertIsNotNone(mod, "rpg.ui.controller imports cleanly in pure WSL")
        self.assertNotIn("pymol", sys.modules,
                         "controller import did not pull in pymol")
        self.assertNotIn("PyQt5", sys.modules,
                         "controller import did not pull in PyQt5")

    # 16. request_edit stashes enzyme_id + gotos edit.prompt (Warning 4 seam)
    def test_request_edit_stashes_enzyme_id_and_gotos_edit_prompt(self):
        """request_edit(enzyme_id) stashes the enzyme_id + gotos edit.prompt via
        engine.goto (NOT choose). The MainWindow (06-08) reads
        _pending_edit_enzyme_id when render_turn sees edit.prompt."""
        molops = MockMolOps()
        view = MockView()
        c = self._make_controller(molops=molops, view=view)
        c.start_game("glucose", 42)  # intro.preface
        c.request_edit("tca.citrate_synthase")
        self.assertEqual(c._pending_edit_enzyme_id, "tca.citrate_synthase",
                         "request_edit stashed the enzyme_id")
        self.assertEqual(c._engine.state.current_node, "edit.prompt",
                         "request_edit used engine.goto -> edit.prompt (NOT choose)")

    # 16b. B2: request_edit ALSO stashes the SOURCE node id
    def test_request_edit_stashes_source_node_id(self):
        """request_edit stashes the node the player was ON (the edit-allowed
        SOURCE) in _pending_edit_source_node_id BEFORE the goto edit.prompt
        (B2 anti-stranding seam: the Cancel 'Return to the enzyme' button
        gotos this id; controller-side attribute only -- no skeleton change)."""
        c = self._make_controller()
        c.start_game("glucose", 42)  # intro.preface == the source here
        c.request_edit("tca.citrate_synthase")
        self.assertEqual(c._pending_edit_source_node_id, "intro.preface",
                         "the SOURCE node id (where the player was) is stashed")

    # 16c. B2: return_to_edit_source gotos the stashed source + clears BOTH
    def test_return_to_edit_source_returns_and_clears(self):
        """After request_edit (player at edit.prompt), return_to_edit_source
        gotos the stashed SOURCE node (the player is back at the enzyme node
        with its choices -- NOT stranded at the empty edit.prompt panel) and
        clears BOTH pending values (a fresh edit click re-stashes)."""
        molops = MockMolOps()
        view = MockView()
        c = self._make_controller(molops=molops, view=view)
        c.start_game("glucose", 42)  # intro.preface
        c.request_edit("tca.citrate_synthase")
        self.assertEqual(c._engine.state.current_node, "edit.prompt")
        turn = c.return_to_edit_source()
        self.assertEqual(turn.node.id, "intro.preface",
                         "returned to the SOURCE node (anti-stranding)")
        self.assertEqual(c._engine.state.current_node, "intro.preface")
        self.assertIsNone(c._pending_edit_enzyme_id,
                          "the enzyme stash is cleared on return")
        self.assertIsNone(c._pending_edit_source_node_id,
                          "the source stash is cleared on return")
        self.assertEqual(view.turns[-1].node.id, "intro.preface",
                         "the returned turn was rendered (choices re-render)")

    # 16d. B2: return_to_edit_source without a stash is a safe no-op
    def test_return_to_edit_source_noop_without_stash(self):
        """No stashed source (never requested an edit) -> returns None, no
        raise, no engine state change (the MainWindow shows a status message)."""
        c = self._make_controller()
        c.start_game("glucose", 42)
        turn = c.return_to_edit_source()
        self.assertIsNone(turn, "no stash -> None")
        self.assertEqual(c._engine.state.current_node, "intro.preface",
                         "no state change")

    # 16e. B1: a successful apply clears the pending stashes
    def test_apply_edit_clears_pending_stash_on_success(self):
        """After a successful apply_edit the edit seam is DONE: both pending
        values are cleared so a stale enzyme_id can never silently supply an
        enzyme for a future, unrelated dialog (B1 stale-stash hardening)."""
        c = self._make_controller()
        c.start_game("glucose", 42)  # intro.preface
        c.request_edit("tca.citrate_synthase")  # stashes + gotos edit.prompt
        intent = c.build_edit_intent("point_mutation", "resi 1",
                                     {"new_res": "GLY"})
        self.assertEqual(intent.enzyme_id, "tca.citrate_synthase")
        c.apply_edit(intent)  # routes to the bad-ending pool (unknown enzyme)
        self.assertIsNone(c._pending_edit_enzyme_id,
                          "the enzyme stash is cleared after a successful apply")
        self.assertIsNone(c._pending_edit_source_node_id,
                          "the source stash is cleared after a successful apply")

    # 17. build_edit_intent falls back to pending enzyme_id at edit.prompt
    def test_build_edit_intent_falls_back_to_pending_enzyme_id_at_edit_prompt(self):
        """After request_edit lands at edit.prompt, build_edit_intent falls back
        to _pending_edit_enzyme_id (edit.prompt has no edit:enzyme: tag, so
        _current_enzyme_id() returns None)."""
        c = self._make_controller()
        c.start_game("glucose", 42)
        c.request_edit("tca.citrate_synthase")  # stashes + gotos edit.prompt
        self.assertIsNone(c._current_enzyme_id(),
                          "edit.prompt has no edit:enzyme: tag")
        intent = c.build_edit_intent("point_mutation", "resi 1", {"new_res": "GLY"})
        self.assertEqual(intent.enzyme_id, "tca.citrate_synthase",
                         "build_edit_intent fell back to _pending_edit_enzyme_id")

    # 17b. SC2f round-2 fix: the formalized debugger probe at gly.pfk.
    def test_request_edit_at_gly_pfk_stashes_and_builds_intent(self):
        """Formalizes the debugger's probe
        (.planning/debug/edit-prompt-empty-stash.md): walk (controller path) to
        gly.pfk -- the FIRST pure-MC enzyme node on the glucose path and the
        node where the user hit the RuntimeError -- then request_edit the
        node's own edit:enzyme id + build_edit_intent. The stash must be set
        AT THE SOURCE NODE (before the goto) and the intent must carry
        enzyme_id 'gly.pfk' with NO raise. (The original bug: the pure-MC
        edit:offer choice routed through the generic choose(i), so
        edit.prompt was entered with an empty stash.)"""
        molops = MockMolOps()
        view = MockView()
        c = self._make_controller(molops=molops, view=view)
        c.start_game("glucose", 42)  # intro.preface
        # Position one step upstream (engine-level -- the established test
        # pattern, test #4/#5) and advance into gly.pfk via the CONTROLLER
        # (mirrors the real UI click on gly.g6p's "Continue" choice).
        c._engine.goto("gly.g6p")
        turn = c.choose(0)
        self.assertEqual(turn.node.id, "gly.pfk", "walked to gly.pfk")
        # The debugger probe: request_edit the CURRENT node's enzyme id.
        enzyme_id = c._current_enzyme_id()
        self.assertEqual(enzyme_id, "gly.pfk",
                         "gly.pfk carries the edit:enzyme:gly.pfk tag")
        c.request_edit(enzyme_id)
        self.assertEqual(c._pending_edit_enzyme_id, "gly.pfk",
                         "the stash is set at the SOURCE node (gly.pfk) "
                         "before the goto edit.prompt")
        self.assertEqual(c._engine.state.current_node, "edit.prompt")
        # build_edit_intent must NOT raise (the original bug's symptom) and
        # must carry the stashed enzyme_id.
        intent = c.build_edit_intent(
            "point_mutation", "resi 1", {"new_res": "GLY"})
        self.assertEqual(intent.enzyme_id, "gly.pfk",
                         "build_edit_intent used the stash set at gly.pfk")

    # 17c. Probe-E hardening (06-14 re-verify round 3): start_game clears
    #      BOTH pending edit stashes (formalizes the debugger's probe E in
    #      .planning/debug/bad-end-restart-and-edit-pool.md).
    def test_start_game_clears_pending_edit_stashes(self):
        """Walk to gly.pfk -> request_edit (both stashes set) -> start_game
        AGAIN on the SAME controller -> the restart is a NEW game: BOTH
        stashes are cleared and the returned turn is the manifest start
        (intro.preface). Probe E proved the stashes SURVIVED the restart
        (engine.start replaces GameState wholesale; the stashes are
        controller attributes) -- a stale enzyme_id for build_edit_intent +
        a stale SOURCE-node jump for return_to_edit_source."""
        molops = MockMolOps()
        view = MockView()
        c = self._make_controller(molops=molops, view=view)
        c.start_game("glucose", 42)  # intro.preface
        c._engine.goto("gly.g6p")
        turn = c.choose(0)  # -> gly.pfk (the pure-MC enzyme node)
        self.assertEqual(turn.node.id, "gly.pfk", "walked to gly.pfk")
        c.request_edit(c._current_enzyme_id())  # stashes enzyme + source
        self.assertEqual(c._pending_edit_enzyme_id, "gly.pfk",
                         "precondition: the enzyme stash is set")
        self.assertEqual(c._pending_edit_source_node_id, "gly.pfk",
                         "precondition: the source stash is set")
        # Restart on the SAME controller (probe E's exact shape).
        turn = c.start_game("glucose", 42)
        self.assertEqual(turn.node.id, "intro.preface",
                         "the restart landed at the manifest start node")
        self.assertIsNone(c._pending_edit_enzyme_id,
                          "the enzyme stash is cleared by the restart")
        self.assertIsNone(c._pending_edit_source_node_id,
                          "the source stash is cleared by the restart")
        self.assertEqual(view.turns[-1].node.id, "intro.preface",
                         "the restart was rendered (fresh intro view)")

    # 17d. Probe-E hardening, load variant: load clears BOTH pending stashes.
    def test_load_clears_pending_edit_stashes(self):
        """Save mid-game at gly.pfk, request_edit (both stashes set), then
        load on the SAME controller -> the load restores a DIFFERENT
        playthrough, so both stashes (controller attributes, never persisted)
        are cleared; the loaded turn is the saved node (gly.pfk)."""
        molops = MockMolOps()
        view = MockView()
        c = self._make_controller(molops=molops, view=view)
        c.start_game("glucose", 42)  # intro.preface
        c._engine.goto("gly.g6p")
        turn = c.choose(0)  # -> gly.pfk
        self.assertEqual(turn.node.id, "gly.pfk", "walked to gly.pfk")
        save_path = tempfile.mktemp(suffix="_ctrl_stash_save.json")
        try:
            c.save(save_path)
            c.request_edit(c._current_enzyme_id())  # -> edit.prompt, stashes
            self.assertEqual(c._engine.state.current_node, "edit.prompt")
            self.assertEqual(c._pending_edit_enzyme_id, "gly.pfk",
                             "precondition: the enzyme stash is set")
            self.assertEqual(c._pending_edit_source_node_id, "gly.pfk",
                             "precondition: the source stash is set")
            # Load on the SAME controller.
            turn = c.load(save_path)
            self.assertEqual(turn.node.id, "gly.pfk",
                             "the loaded game restored the saved node")
            self.assertIsNone(c._pending_edit_enzyme_id,
                              "the enzyme stash is cleared by the load")
            self.assertIsNone(c._pending_edit_source_node_id,
                              "the source stash is cleared by the load")
        finally:
            if os.path.isfile(save_path):
                os.remove(save_path)

    # 18. _dispatch_molaction swallows molops failure + continues (Blocker 1 fix c)
    def test_dispatch_molaction_swallows_molops_failure_and_continues(self):
        """MockMolOps raises on the 2nd apply but succeeds on 1st + 3rd.
        _dispatch_molaction swallows the failure (logs + continues); all 3
        actions are attempted (the 2nd's failure did NOT skip the 3rd)."""
        molops = MockMolOps(fail_indices={1})  # raises on the 2nd call (index 1)
        c = self._make_controller(molops=molops)
        a1 = MolAction("hide_all")
        a2 = MolAction("load", "pdb:1CSC", {"object": "x"})
        a3 = MolAction("show_as", "x", {"rep": "cartoon"})
        # Drive _dispatch_molaction directly 3 times (simulating the engine's
        # per-action loop). Capture stderr to assert the failure was logged.
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            c._dispatch_molaction(a1)  # succeeds
            c._dispatch_molaction(a2)  # raises internally -> swallowed
            c._dispatch_molaction(a3)  # succeeds (loop continued)
        self.assertEqual(len(molops.calls), 3,
                         "all 3 actions were attempted (the 2nd's failure was swallowed)")
        self.assertEqual(molops.calls[0], a1, "1st action forwarded")
        self.assertEqual(molops.calls[2], a3, "3rd action forwarded (loop continued)")
        self.assertIn("molops.apply failed", buf.getvalue(),
                      "the failure was logged to stderr")

    # ---- helper: a minimal hero-highlight on_enter (the 6-call 5.4 form) ----

    @staticmethod
    def _hero_on_enter():
        # type: () -> list
        """A minimal hero-highlight on_enter sequence (the 6-call 5.4 form +
        hide_all + load + set_color). The `label` op with text 'YOU' is the
        OQ-4 hero marker HeroResolver detects."""
        return [
            MolAction("hide_all"),
            MolAction("load", "_smoke.pdb", {"object": "hero_atom"}),
            MolAction("set_color", None, {"name": "hero_cyan", "rgb": [0.0, 0.75, 0.75]}),
            MolAction("show_as", "hero_atom", {"rep": "sticks"}),
            MolAction("color", "hero_atom",
                      {"color": "hero_cyan", "sele": "hero_atom and elem C"}),
            MolAction("show", "hero_atom", {"rep": "spheres", "sele": "hero_atom"}),
            MolAction("set", "hero_atom",
                      {"name": "sphere_scale", "value": 0.3, "sele": "hero_atom"}),
            MolAction("label", "hero_atom", {"sele": "hero_atom", "text": "YOU"}),
        ]


class TestShuffleAutoResolve(unittest.TestCase):
    """tca.shuffle AUTO-RESOLVE tests (user decision 1, 2026-08-30): the soul
    jump is NOT a player decision -- entering the shuffle via ANY controller
    path auto-resolves (controller._render choke point):

    - visits == 6 entry: the cycle-trap cond (visits > 5) is met -> the trap
      AUTO-FIRES as a RESULT (bad.cycle_trap_host_death + bad_ending
      achievement) with NO explicit take_choice call.
    - FIRST entry (visits == 1): the aconitase edit is offered ONCE via the
      injected edit_offer_fn (defaulting to prompt_fn). Declined -> AUTO-SPIN
      (the engine RNG picks among the WEIGHTED choices ONLY -- the index is
      ignored; NO new RNG outcomes/weights). Accepted -> request_edit ->
      edit.prompt with the stash 'tca.aconitase' (the shuffle's own
      edit:enzyme tag; guaranteed by the graph invariant test).
    - The trap choice stays in the FROZEN skeleton JSON (the controller just
      auto-takes it) -- 55 nodes / 21 endings untouched.

    Entry positioning uses engine.goto (bypasses the controller render path)
    to place the player at tca.aconitase, then the CONTROLLER choose() walks
    into the shuffle -- mirroring a real UI click.
    """

    def _make_controller(self, prompt_fn=None, count_fn=None,
                         edit_offer_fn=None, achievement_board=None):
        # type: (object, object, object, object, object) -> Controller
        """Controller over the real glucose graph + a real EditRouter + mocks.
        count_fn defaults to a deterministic single-C (no hero prompt) so the
        injected prompt fns are only exercised by the shuffle offer."""
        edit_router = EditRouter(EditsTable.load(_edits_path()))
        return Controller(
            _story_dir(),
            MockMolOps(),
            None,  # cmd -- unused
            edit_router,
            view=MockView(),
            prompt_fn=prompt_fn,
            count_fn=count_fn if count_fn is not None else (lambda sele: 1),
            achievement_board=achievement_board,
            edit_offer_fn=edit_offer_fn)

    def _goto_aconitase(self, c):
        # type: (Controller) -> None
        """Position the engine at tca.aconitase (engine-level -- no render,
        no auto-resolve)."""
        c._engine.goto("tca.aconitase")

    def test_first_entry_declined_auto_spins_to_co2_turn(self):
        """First shuffle entry with the offer DECLINED: the returned turn is
        ALREADY the post-spin co2_turnX (the engine RNG picked among the
        weighted ONLY) -- no Spin button, no player click on a shuffle
        choice; the shuffle turn itself is never rendered (auto-resolves
        pre-render); the offer prompt fired exactly once."""
        offer_calls = []  # type: list
        c = self._make_controller(
            prompt_fn=lambda msg: offer_calls.append(msg) or False)
        c.start_game("glucose", 42)
        self._goto_aconitase(c)
        view = c._view
        turn = c.choose(0)  # "Continue to the shuffle" -> AUTO-RESOLVE
        self.assertIn(
            turn.node.id, ("tca.co2_turn1", "tca.co2_turn2"),
            "the first entry auto-spun to a co2_turnX (RNG-weighted only); "
            "got %r" % turn.node.id)
        # The shuffle turn was NEVER rendered (superseded pre-render); the
        # final render IS the returned (post-spin) turn.
        rendered_ids = [t.node.id for t in view.turns]
        self.assertNotIn("tca.shuffle", rendered_ids,
                         "the shuffle turn is not rendered (auto-resolves "
                         "pre-render); rendered=%r" % rendered_ids)
        self.assertEqual(view.turns[-1].node.id, turn.node.id,
                         "the final render is the post-spin turn")
        # The edit offer fired EXACTLY once (first entry) and was declined.
        self.assertEqual(len(offer_calls), 1,
                         "the edit offer fired once on the first entry")
        self.assertIn("aconitase", offer_calls[0],
                      "the offer message names aconitase; got %r"
                      % offer_calls[0])
        # Exactly ONE shuffle visit so far (the trap cond is visits-based).
        self.assertEqual(
            c._engine.state.visit_counts.get("tca.shuffle", 0), 1)

    def test_visits_6_entry_auto_fires_trap(self):
        """The 6th shuffle entry (visits becomes 6) AUTO-FIRES the cycle-trap
        as a RESULT: bad.cycle_trap_host_death + the bad_ending tier turn
        recorded by the board -- with NO explicit take_choice call by the
        caller (only 'The cycle turns again' choose clicks)."""
        offer_calls = []  # type: list
        board = MockAchievementBoard()
        c = self._make_controller(
            prompt_fn=lambda msg: offer_calls.append(msg) or False,
            achievement_board=board)
        c.start_game("glucose", 42)
        self._goto_aconitase(c)
        turn = c.choose(0)  # entry 1: offer declined -> auto-spin -> co2_turnX
        self.assertIn(turn.node.id, ("tca.co2_turn1", "tca.co2_turn2"))
        # 4 more returns (visits 2..5): each auto-spins again to co2_turnX.
        for i in range(4):
            turn = c.choose(0)  # "The cycle turns again" (index 0)
            self.assertIn(
                turn.node.id, ("tca.co2_turn1", "tca.co2_turn2"),
                "return %d auto-spun (no offer, no trap yet); got %r"
                % (i, turn.node.id))
        # 5th return: visits -> 6 -> the trap cond is met -> AUTO-FIRE.
        turn = c.choose(0)
        self.assertEqual(
            turn.node.id, "bad.cycle_trap_host_death",
            "the 6th entry auto-fired the trap as a RESULT (no take_choice "
            "call by the caller); got %r" % turn.node.id)
        self.assertEqual(turn.node.is_ending, "bad")
        self.assertTrue(c._engine.state.finished,
                        "the playthrough finished at the Bad ending")
        self.assertEqual(c._engine.state.ending_tier, "bad",
                         "the recorded ending tier is bad")
        self.assertEqual(
            c._engine.state.visit_counts.get("tca.shuffle", 0), 6,
            "the trap fired exactly at visits == 6")
        # The bad-ending turn was recorded by the board (achievement path
        # reused -- take_choice's internal _record_achievement).
        self.assertEqual(
            board.calls[-1][0].node.id, "bad.cycle_trap_host_death",
            "the board recorded the auto-fired bad-ending turn")
        # No second offer ever fired (the offer is one-time; visits != 1).
        self.assertEqual(len(offer_calls), 1)

    def test_first_entry_accepted_routes_to_edit_prompt(self):
        """First shuffle entry with the offer ACCEPTED: routes through
        request_edit -> edit.prompt with the stash 'tca.aconitase' (the
        shuffle's own edit:enzyme:tca.aconitase tag) + the SOURCE stash
        'tca.shuffle' (for the Cancel return); build_edit_intent then carries
        enzyme_id 'tca.aconitase' with no raise."""
        c = self._make_controller(prompt_fn=lambda msg: True)
        c.start_game("glucose", 42)
        self._goto_aconitase(c)
        turn = c.choose(0)  # "Continue to the shuffle" -> offer -> YES
        self.assertEqual(
            turn.node.id, "edit.prompt",
            "the accepted offer routed to edit.prompt via request_edit")
        self.assertEqual(c._pending_edit_enzyme_id, "tca.aconitase",
                         "the stash is the shuffle's edit:enzyme target")
        self.assertEqual(c._pending_edit_source_node_id, "tca.shuffle",
                         "the SOURCE stash is the shuffle (Cancel returns "
                         "there -- which then auto-spins)")
        intent = c.build_edit_intent("point_mutation", "resi 1",
                                     {"new_res": "GLY"})
        self.assertEqual(intent.enzyme_id, "tca.aconitase",
                         "build_edit_intent used the stash (no raise)")

    def test_edit_offer_fn_used_over_prompt_fn(self):
        """A SEPARATE edit_offer_fn (MainWindow generalization): the shuffle
        offer goes to edit_offer_fn (declined -> auto-spin), NOT to the
        OQ-6 prompt_fn (which keeps its 'Hero ambiguity' hero-gate role)."""
        prompt_calls = []  # type: list
        offer_calls = []  # type: list
        c = self._make_controller(
            prompt_fn=lambda msg: prompt_calls.append(msg) or True,
            edit_offer_fn=lambda msg: offer_calls.append(msg) or False)
        c.start_game("glucose", 42)
        self._goto_aconitase(c)
        turn = c.choose(0)
        self.assertIn(turn.node.id, ("tca.co2_turn1", "tca.co2_turn2"),
                      "the declined edit_offer_fn led to an auto-spin")
        self.assertEqual(len(offer_calls), 1, "the offer hit edit_offer_fn")
        self.assertEqual(
            prompt_calls, [],
            "prompt_fn was NOT used for the shuffle offer (single-C "
            "count_fn -> no hero prompt either)")

    def test_offer_is_one_time_across_entries(self):
        """The edit offer fires ONLY on the first entry (visits == 1):
        entries 2..N auto-spin with NO second offer. The offer-already-made
        fact lives in GameState.visit_counts -- no new state."""
        offer_calls = []  # type: list
        c = self._make_controller(
            prompt_fn=lambda msg: offer_calls.append(msg) or False)
        c.start_game("glucose", 42)
        self._goto_aconitase(c)
        c.choose(0)  # entry 1: offer fired (declined) -> spin
        for i in range(3):
            c.choose(0)  # entries 2..4: NO offer
        self.assertEqual(len(offer_calls), 1,
                         "the offer fired exactly once across 4 entries")

    def test_spin_is_deterministic_same_seed(self):
        """RNG determinism: the same seed -> the same spin outcome (two fresh
        controllers, identical entry positioning, one RNG draw per spin)."""
        spins = []
        for seed in (42, 42):
            c = self._make_controller(
                prompt_fn=lambda msg: False)  # noqa: E731 -- declined offer
            c.start_game("glucose", seed)
            self._goto_aconitase(c)
            spins.append(c.choose(0).node.id)
        self.assertEqual(spins[0], spins[1],
                         "same seed -> same spin outcome; got %r" % (spins,))

    def test_load_returns_post_resolve_turn(self):
        """load() returns the POST-auto-resolve turn: save at co2_turnX (after
        the first declined offer), load, then the return choice auto-spins
        with NO second offer (visit_counts survived the round-trip)."""
        import os
        import shutil
        import tempfile
        offer_calls = []  # type: list
        c = self._make_controller(
            prompt_fn=lambda msg: offer_calls.append(msg) or False)
        c.start_game("glucose", 42)
        self._goto_aconitase(c)
        c.choose(0)  # entry 1: offer declined -> spin -> co2_turnX
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        path = os.path.join(tmpdir, "save.json")
        c.save(path)
        turn = c.load(path)  # re-enters co2_turnX (record_visit=False)
        self.assertIn(turn.node.id, ("tca.co2_turn1", "tca.co2_turn2"),
                      "load restored the co2_turnX position")
        turn = c.choose(0)  # entry 2: visits == 2 -> auto-spin, NO offer
        self.assertIn(turn.node.id, ("tca.co2_turn1", "tca.co2_turn2"),
                      "the return entry auto-spinned (post-resolve turn)")
        self.assertEqual(len(offer_calls), 1,
                         "no second offer after save/load (visits-based, "
                         "no new state)")


if __name__ == "__main__":
    unittest.main()
