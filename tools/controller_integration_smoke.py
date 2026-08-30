#!/usr/bin/env python
# tools/controller_integration_smoke.py -- Phase 6 Plan 06-14 Task 1 the
# CAPSTONE headless integration smoke (SC1-3 mechanism proof).
#
# Pure pymol.cmd.* script (NO Qt -- uses a MockView) that exercises the FULL
# Controller path end-to-end against the REAL PyMOL 2.5.0 cmd + the REAL
# molops stack (AssetManager + EditOps + ProtonationManager + MolOps) + the
# REAL story_glucose graph + a real EditRouter + a real AchievementBoard.
# Proves the integration of 06-01 (4 deferred dispatches + load target-prefix
# fallback) + 06-03 (view-matrix injection) + 06-04 (achievements) + 06-05
# (pyr.branch cond fix + start-node _smoke.pdb swap + hero-highlight sequence)
# + 06-06 (Controller + goto routing + Blocker 1 fix c defensive swallow) +
# 06-10 (bulk-download runner).
#
# STAGES:
#   1. Setup the real molops stack + MockView + mock prompt_fn/count_fn.
#   2. (folded into stage 1) MockView class.
#   3. Construct the Controller (story_dir = repo-root data/story_glucose).
#   4. Start a glucose game -- assert intro.preface + hero-highlight dispatched
#      (hero_atom loaded from bundled _smoke.pdb, hero_cyan color, YOU label).
#   5. Advance to pyr.branch -- assert the 06-05 cond fix (aerobic eligible) +
#      proceed to pyr.pdh.
#   6. Advance to tca.shuffle -- assert is_mixed_weighted_node + spin + return
#      6x to bump visits + take_choice(cycle_trap) -> bad.cycle_trap_host_death
#      (a Bad ending reached -- SC3 Bad path) + bad_ending achievement unlocked.
#   6b. SAME-CONTROLLER restart after that bad ending (06-14 re-verify round 3,
#      debugger probe A formalized + probe-E stash symmetry): start_game AGAIN
#      on the SAME controller -> intro.preface, finished falsy, a NEW turn
#      rendered, _resolving_shuffle False, BOTH edit stashes cleared.
#   7. Reach a True ending via the BFS-distance-guided walk (fresh controller,
#      new seed) -- assert end.true + the milestone path + true_ending unlocked.
#   8. Save/load round-trip with view (06-03) -- mid-game save + load into a
#      2nd controller; assert current_node + seed + rng_state + view applied.
#   9. Bulk-download runner (06-10) -- missing_large_pdbs returns [] for the
#      Phase 6 placeholder cast.
#  10. Final SMOKE_RESULT sentinel.
#
# CRITICAL CONTRACT RULES (from 03-RESEARCH.md, reused from hero_highlight +
# molops_deferred_dispatch smokes):
#   * Gotcha #1: the process ALWAYS exits 0 through run-conda-pymol.bat. The
#     SMOKE_RESULT: stdout sentinel is the ONLY reliable verdict (NOT exit code).
#   * Gotcha #2: __file__ in a PyMOL-run script resolves to the pymol package's
#     __init__.py. So os.getcwd() (= repo root) + import rpg.paths locates
#     bundled fixtures.
#   * Gotcha #6: pymol.finish_launching() completes PyMOL startup before any
#     cmd.* call.
#
# The start node loads the bundled _smoke.pdb via the 06-01 load-branch
# bare-filename target fallback (NO KeyError, NO network). Mid-game nodes use
# real pdb:XXX targets that fail offline -- the controller's defensive
# try/except (06-06 Blocker 1 fix c) degrades gracefully (logs + continues);
# this smoke does NOT assert those mid-game loads succeed headlessly.
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/controller_integration_smoke.py
# Verdict: grep ^SMOKE_RESULT: PASS in the captured stdout (NOT $?).

import sys
import os

# Gotcha #2/#3/#4: cwd=repo root when run via the harness, so os.getcwd() is
# the workspace and `import rpg` works (sys.path includes '' = cwd). Insert
# cwd explicitly as belt-and-suspenders so this script is robust if sys.path
# lacks ''.
sys.path.insert(0, os.getcwd())

import pymol
from pymol import cmd
import rpg.paths
import rpg.protonation_catalog  # pure-data catalog MODULE (passed by reference)
from rpg.pymol_layer.molops import MolOps
from rpg.pymol_layer.asset_manager import AssetManager
from rpg.pymol_layer.edit_ops import EditOps
from rpg.pymol_layer.protonation import ProtonationManager
from rpg.edit_router import EditRouter, EditsTable
from rpg.achievements import AchievementBoard
from rpg.ui.controller import Controller

# Gotcha #6: complete PyMOL startup before any cmd.* call.
pymol.finish_launching()

import tempfile

FAILS = []


def check(name, ok, detail=""):
    # type: (str, bool, str) -> None
    """Print a SMOKE: PASS|FAIL line and record failures for the final sentinel."""
    print("SMOKE: {0} {1} {2}".format("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILS.append(name)


# =========================================================================
# Stage 1 + 2: the real molops stack + MockView + injected callbacks.
#
# Mirrors the MainWindow (06-08) construction EXACTLY but with a MockView
# (NO Qt) + a mock prompt_fn (auto-confirm True -- the OQ-6 gate is wired but
# the smoke auto-confirms so the hero-highlight rewrite fires deterministically).
# =========================================================================

class MockView(object):
    """Records every render_turn(turn) call (replaces the Qt MainWindow)."""

    def __init__(self):
        self.turns = []  # type: list

    def render_turn(self, turn):
        self.turns.append(turn)


def _build_molops_stack():
    """Construct the real molops stack (AssetManager + EditOps +
    ProtonationManager + MolOps) + the EditRouter + AchievementBoard, mirroring
    the MainWindow (06-08) construction. Returns (molops, edit_router,
    achievement_board, ach_path)."""
    assets = AssetManager(cmd)
    editops = EditOps(cmd)
    protonation = ProtonationManager(
        cmd, editops, rpg.protonation_catalog, assets)
    molops = MolOps(cmd, assets, editops, protonation)
    edits_path = str(rpg.paths.data_path("data", "edits.json"))
    edit_router = EditRouter(EditsTable.load(edits_path))
    # Temp achievements path (NOT the real user_data_path -- no pollution).
    ach_path = tempfile.mktemp(suffix="_smoke_ach.json")
    achievement_board = AchievementBoard(path=ach_path)
    return molops, edit_router, achievement_board, ach_path


# View capture/restore (06-03): record the applied view for the save/load
# round-trip assertion (stage 8). view_provider = cmd.get_view (18 floats);
# view_applier records + calls cmd.set_view.
_applied_views = []  # type: list


def _view_provider():
    # src: tmp/pymol-src/modules/pymol/viewing.py cmd.get_view  (18-float matrix)
    return list(cmd.get_view())


def _view_applier(v):
    _applied_views.append(list(v))
    # src: tmp/pymol-src/modules/pymol/viewing.py cmd.set_view  (apply 18 floats)
    cmd.set_view(v)


# The OQ-6 warn+confirm gate (auto-confirm True -- the smoke auto-confirms so
# the hero-highlight rewrite fires deterministically; the _smoke.pdb has 2
# carbons so the resolver WOULD prompt + rewrite to the single-carbon default
# "first (hero_atom and elem C)" -- the 06-14 SC2a fix: exactly ONE hero).
_prompt_calls = []  # type: list


def _prompt_fn(message):
    _prompt_calls.append(message)
    return True


# The tca.shuffle edit-offer callback (user decision 1, 2026-08-30: the wheel
# auto-spins -- the aconitase edit is offered ONCE on the first entry). The
# smoke DECLINES the offer so the shuffle auto-spins deterministically.
# SEPARATE from _prompt_fn (the OQ-6 hero gate must keep auto-confirming).
_edit_offer_calls = []  # type: list


def _edit_offer_fn(message):
    _edit_offer_calls.append(message)
    return False


# count_fn wraps cmd.count_atoms (the HeroResolver's hero-selector count). Bare
# form per the plan -- the HeroResolver must be robust to a count on a
# not-yet-loaded object (the pre-pass runs BEFORE the on_enter load dispatches).
def _count_fn(sele):
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    return cmd.count_atoms(sele)


STORY_DIR = os.path.join(os.getcwd(), "data", "story_glucose")


def _make_controller(achievement_board=None):
    """Construct a Controller over the real glucose graph with the real molops
    stack + MockView + the injected callbacks. Each call gets a FRESH molops
    stack + MockView (controllers are independent)."""
    molops, edit_router, _ab, _ = _build_molops_stack()
    if achievement_board is None:
        # Share the caller's board? No -- each controller gets its own board
        # unless the caller passes one (stage 4+6 share a board; stage 7 gets
        # a fresh one). Actually the plan uses ONE board for stages 4-6 (start
        # -> Bad ending) + a FRESH board for stage 7 (True ending). This helper
        # builds a fresh board when none is passed.
        ach_path = tempfile.mktemp(suffix="_smoke_ach.json")
        achievement_board = AchievementBoard(path=ach_path)
    view = MockView()
    controller = Controller(
        STORY_DIR, molops, cmd, edit_router, view=view,
        prompt_fn=_prompt_fn, count_fn=_count_fn,
        achievement_board=achievement_board,
        view_provider=_view_provider, view_applier=_view_applier,
        edit_offer_fn=_edit_offer_fn)
    return controller, view, achievement_board


# =========================================================================
# Stage 3 + 4: construct the Controller + start a glucose game + assert the
# hero-highlight dispatches fired (SC2 mechanism proof).
# =========================================================================
controller = None  # type: object
mock_view = None  # type: object
ach_board = None  # type: object
ach_path_main = None  # type: object

try:
    molops_main, edit_router_main, ach_board, ach_path_main = _build_molops_stack()
    mock_view = MockView()
    controller = Controller(
        STORY_DIR, molops_main, cmd, edit_router_main, view=mock_view,
        prompt_fn=_prompt_fn, count_fn=_count_fn,
        achievement_board=ach_board,
        view_provider=_view_provider, view_applier=_view_applier,
        edit_offer_fn=_edit_offer_fn)

    # Start a glucose game (seed=42 for reproducibility).
    turn = controller.start_game("glucose", seed=42)

    # Assert the start node is intro.preface (the manifest start).
    check("start_node_intro_preface",
          turn.node.id == "intro.preface",
          "node=%r" % turn.node.id)
    # Assert the view rendered it.
    check("start_rendered",
          len(mock_view.turns) >= 1
          and mock_view.turns[-1].node.id == "intro.preface",
          "turns=%d" % len(mock_view.turns))
    # Assert the achievement board recorded glucose tried + first_game.
    check("ach_characters_tried_glucose",
          ach_board.data["characters_tried"] == ["glucose"],
          "chars=%r" % ach_board.data["characters_tried"])
    ach_ids = [a["id"] for a in ach_board.data["achievements_unlocked"]]
    check("ach_first_game_unlocked", "first_game" in ach_ids,
          "unlocked=%r" % ach_ids)

    # Assert the start-node hero-highlight dispatches fired (06-05 fix + 06-01
    # load-branch bare-filename target fallback). The intro.preface on_enter
    # loads the bundled _smoke.pdb as hero_atom (NO KeyError, NO network) +
    # runs the 6-call hero-highlight sequence (set_color + show_as + color +
    # show + set + label).
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    hero_count = cmd.count_atoms("hero_atom")
    check("hero_atom_loaded", hero_count > 0,
          "hero_atom=%d" % hero_count)
    # The set_color dispatched -- hero_cyan is a named color.
    # src: tmp/pymol-src/modules/pymol/querying.py:843 cmd.get_color_indices
    color_names = [n for (n, i) in cmd.get_color_indices(all=1)]
    check("hero_cyan_color_defined", "hero_cyan" in color_names,
          "has_hero_cyan=%r" % ("hero_cyan" in color_names,))
    # The "YOU" label dispatched -- read the label atom PROPERTY via
    # cmd.iterate (NOT count_atoms("... and label") -- `label` is an atom
    # property, NOT a selection keyword; hero_highlight_smoke.py:191-194 uses
    # the same iterate approach). EXACTLY ONE atom has the "YOU" label (the
    # 06-14 SC2a fix: the OQ-6 default sele resolves to one hero carbon --
    # the pre-fix "<obj> and elem C" default labeled BOTH carbons).
    lbls = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate  (read label text; collector `lbls` avoids collision)
    cmd.iterate("hero_atom", "lbls.append(label)", space={"lbls": lbls})
    check("hero_you_label_dispatched",
          lbls.count("YOU") == 1,
          "exactly_one_YOU=%r labels=%r" % (lbls.count("YOU") == 1, lbls))
except Exception as e:
    import traceback
    traceback.print_exc()
    check("start_node_intro_preface", False, repr(e))
    check("start_rendered", False, repr(e))
    check("ach_characters_tried_glucose", False, repr(e))
    check("ach_first_game_unlocked", False, repr(e))
    check("hero_atom_loaded", False, repr(e))
    check("hero_cyan_color_defined", False, repr(e))
    check("hero_you_label_dispatched", False, repr(e))


# =========================================================================
# Stage 5: advance to pyr.branch + verify the 06-05 cond fix (aerobic eligible)
# + proceed to pyr.pdh.
#
# Path: intro.preface -> (Continue) intro.select -> (Glucose)
#   intro.shell_glucose -> (Begin) gly.start -> (Continue) gly.g6p ->
#   (Continue) gly.pfk -> (Continue glycolysis) gly.fbp_to_pyruvate ->
#   (Continue) gly.pyruvate_kinase -> (Continue) gly.pyruvate -> (Continue)
#   pyr.branch.
# At each node the Continue choice is at index 0 in the eligible list.
# =========================================================================
try:
    # Walk intro.preface -> pyr.branch via Continue choices (index 0 each).
    # intro.preface -> intro.select
    turn = controller.choose(0)
    check("walk_intro_to_select", turn.node.id == "intro.select",
          "node=%r" % turn.node.id)
    # intro.select -> intro.shell_glucose (Glucose choice, index 0)
    turn = controller.choose(0)
    check("walk_select_to_shell", turn.node.id == "intro.shell_glucose",
          "node=%r" % turn.node.id)
    # intro.shell_glucose -> gly.start (Begin, index 0)
    turn = controller.choose(0)
    check("walk_shell_to_gly_start", turn.node.id == "gly.start",
          "node=%r" % turn.node.id)
    # gly.start -> gly.g6p (Continue, index 0)
    turn = controller.choose(0)
    check("walk_gly_start_to_g6p", turn.node.id == "gly.g6p",
          "node=%r" % turn.node.id)
    # gly.g6p -> gly.pfk (Continue, index 0)
    turn = controller.choose(0)
    check("walk_g6p_to_pfk", turn.node.id == "gly.pfk",
          "node=%r" % turn.node.id)

    # --- gly.pfk edit seam (SC2f round-2 fix, 06-14 re-verify): the pure-MC
    # edit:offer choice routes through request_edit (the stash is set at the
    # SOURCE node BEFORE the goto). Formalizes the debugger probe
    # (.planning/debug/edit-prompt-empty-stash.md): the ORIGINAL bug was that
    # gly.pfk's edit button advanced via the generic choose(i) -> edit.prompt
    # with an EMPTY stash -> build_edit_intent RuntimeError.
    enzyme_at_pfk = controller._current_enzyme_id()
    check("gly_pfk_current_enzyme_id", enzyme_at_pfk == "gly.pfk",
          "enzyme=%r" % enzyme_at_pfk)
    edit_turn = controller.request_edit(enzyme_at_pfk)
    check("gly_pfk_request_edit_lands_edit_prompt",
          edit_turn.node.id == "edit.prompt",
          "node=%r" % edit_turn.node.id)
    check("gly_pfk_request_edit_stash",
          controller._pending_edit_enzyme_id == "gly.pfk",
          "stash=%r" % controller._pending_edit_enzyme_id)
    intent_pfk = controller.build_edit_intent(
        "point_mutation", "resi 1", {"new_res": "GLY"})
    check("gly_pfk_build_edit_intent_enzyme",
          intent_pfk.enzyme_id == "gly.pfk",
          "intent.enzyme_id=%r (no raise)" % intent_pfk.enzyme_id)
    # Reposition back to gly.pfk (engine-level; the walk continues from the
    # enzyme node). gly.pfk's on_enter re-dispatch hits pdb:4PFK (fails
    # offline -> the 06-06 defensive swallow; NOT asserted headlessly).
    controller._engine.goto("gly.pfk")

    # gly.pfk -> gly.fbp_to_pyruvate (Continue glycolysis, index 0)
    turn = controller.choose(0)
    check("walk_pfk_to_fbp", turn.node.id == "gly.fbp_to_pyruvate",
          "node=%r" % turn.node.id)
    # gly.fbp_to_pyruvate -> gly.pyruvate_kinase (Continue, index 0)
    turn = controller.choose(0)
    check("walk_fbp_to_pk", turn.node.id == "gly.pyruvate_kinase",
          "node=%r" % turn.node.id)
    # gly.pyruvate_kinase -> gly.pyruvate (Continue, index 0)
    turn = controller.choose(0)
    check("walk_pk_to_pyr", turn.node.id == "gly.pyruvate",
          "node=%r" % turn.node.id)
    # gly.pyruvate -> pyr.branch (Continue, index 0)
    turn = controller.choose(0)
    check("walk_pyr_to_branch", turn.node.id == "pyr.branch",
          "node=%r" % turn.node.id)

    # At pyr.branch: assert the 06-05 cond fix. The aerobic choice's cond is
    # "not flags.get('host_o2_low')" -- with host_o2_low unset (flags.get
    # returns None -> falsy -> not None = True), the aerobic choice IS
    # eligible. The 06-05 fix was the dict-method cond syntax.
    branch_node = controller._engine.graph.get_node("pyr.branch")
    aerobic = next(ch for ch in branch_node.choices
                   if "branch:aerobic" in (ch.tags or []))
    aerobic_met = controller._engine.choice_cond_met(aerobic)
    check("pyr_branch_aerobic_cond_met", aerobic_met is True,
          "aerobic_cond=%r" % aerobic_met)
    # The anaerobic choice should NOT be eligible (host_o2_low is not set).
    anaerobic = next(ch for ch in branch_node.choices
                     if "branch:anaerobic" in (ch.tags or []))
    anaerobic_met = controller._engine.choice_cond_met(anaerobic)
    check("pyr_branch_anaerobic_cond_not_met", anaerobic_met is False,
          "anaerobic_cond=%r" % anaerobic_met)

    # Take the aerobic choice (index 0 in the eligible list = [aerobic]) ->
    # pyr.pdh.
    turn = controller.choose(0)
    check("pyr_branch_to_pdh", turn.node.id == "pyr.pdh",
          "node=%r" % turn.node.id)
except Exception as e:
    import traceback
    traceback.print_exc()
    check("walk_intro_to_select", False, repr(e))
    check("walk_select_to_shell", False, repr(e))
    check("walk_shell_to_gly_start", False, repr(e))
    check("walk_gly_start_to_g6p", False, repr(e))
    check("walk_g6p_to_pfk", False, repr(e))
    check("gly_pfk_current_enzyme_id", False, repr(e))
    check("gly_pfk_request_edit_lands_edit_prompt", False, repr(e))
    check("gly_pfk_request_edit_stash", False, repr(e))
    check("gly_pfk_build_edit_intent_enzyme", False, repr(e))
    check("walk_pfk_to_fbp", False, repr(e))
    check("walk_fbp_to_pk", False, repr(e))
    check("walk_pk_to_pyr", False, repr(e))
    check("walk_pyr_to_branch", False, repr(e))
    check("pyr_branch_aerobic_cond_met", False, repr(e))
    check("pyr_branch_anaerobic_cond_not_met", False, repr(e))
    check("pyr_branch_to_pdh", False, repr(e))


# =========================================================================
# Stage 6: tca.shuffle AUTO-RESOLVE (user decision 1, 2026-08-30) -> reach a
# Bad ending (SC3 Bad path) + bad_ending achievement unlocked.
#
# Entering the shuffle via ANY controller path auto-resolves (the controller
# _render choke point -- the soul jump is NOT a player decision):
#   * FIRST entry (visits == 1): the aconitase edit is offered ONCE
#     (_edit_offer_fn -> False here) -> AUTO-SPIN: the returned turn is
#     ALREADY the post-spin co2_turnX (the engine RNG picks among the
#     weighted ONLY; interpreter.pick_choice ignores the index) -- WITHOUT a
#     player Spin click, and the shuffle turn itself is never rendered.
#   * "The cycle turns again" (choose(0) at co2_turnX) re-enters the shuffle
#     -> auto-spins again. After the 5th return visits == 6 -> the cycle-trap
#     cond (visits > 5) is met -> the trap AUTO-FIRES as a RESULT ->
#     bad.cycle_trap_host_death + bad_ending achievement -- NO take_choice
#     call by this smoke.
#   * NO new RNG outcomes/weights (TCA-RNG-WEIGHT-01 covers only the existing
#     0.5/0.5); the FROZEN skeleton (55 nodes / 21 endings) is untouched --
#     the trap choice stays in the JSON, the controller just auto-takes it.
#
# Path: pyr.pdh -> tca.entry -> tca.citrate_synthase -> tca.aconitase ->
#   choose(0) "Continue to the shuffle" -> AUTO-SPIN -> co2_turnX -> 5x
#   choose(0) "The cycle turns again" -> the 5th AUTO-FIRES the trap.
# =========================================================================
try:
    # pyr.pdh -> tca.entry (Continue into the TCA cycle, index 0)
    turn = controller.choose(0)
    check("walk_pdh_to_tca_entry", turn.node.id == "tca.entry",
          "node=%r" % turn.node.id)
    # tca.entry -> tca.citrate_synthase (Continue, index 0)
    turn = controller.choose(0)
    check("walk_tca_entry_to_cs", turn.node.id == "tca.citrate_synthase",
          "node=%r" % turn.node.id)
    # tca.citrate_synthase -> tca.aconitase (Continue to aconitase, index 0)
    turn = controller.choose(0)
    check("walk_cs_to_aconitase", turn.node.id == "tca.aconitase",
          "node=%r" % turn.node.id)

    # is_mixed_weighted_node still detects the shuffle's mixed shape (the
    # ChoicePanel mixed mode stays; the auto-resolve just makes it
    # dead-for-shuffle in practice).
    shuffle_node = controller._engine.graph.get_node("tca.shuffle")
    check("tca_shuffle_is_mixed",
          controller.is_mixed_weighted_node(shuffle_node) is True,
          "mixed=%r" % controller.is_mixed_weighted_node(shuffle_node))

    # --- FIRST entry: choose(0) "Continue to the shuffle" -> the returned
    # turn is ALREADY the post-spin co2_turnX (auto-resolved pre-render; the
    # edit offer was declined once -> auto-spin; NO player Spin click).
    first_spin_node = None
    turn = controller.choose(0)
    first_spin_node = turn.node.id
    check("shuffle_auto_spin_no_click",
          turn.node.id in ("tca.co2_turn1", "tca.co2_turn2"),
          "node=%r (returned turn is already post-spin)" % turn.node.id)
    check("shuffle_edit_offer_declined_once",
          len(_edit_offer_calls) == 1,
          "offers=%d message=%r" % (len(_edit_offer_calls),
                                    _edit_offer_calls[0] if _edit_offer_calls
                                    else None))
    check("shuffle_first_entry_visits_1",
          controller._engine.state.visit_counts.get("tca.shuffle", 0) == 1,
          "visits=%r" % controller._engine.state.visit_counts.get(
              "tca.shuffle", 0))
    # The shuffle turn itself was never rendered (auto-resolves pre-render).
    check("shuffle_never_rendered",
          all(t.node.id != "tca.shuffle" for t in mock_view.turns),
          "renders=%d shuffle_in_renders=%r" % (
              len(mock_view.turns),
              any(t.node.id == "tca.shuffle" for t in mock_view.turns)))

    # --- Loop back 4x: each "The cycle turns again" (choose(0)) re-enters
    # the shuffle -> visits 2..5 -> auto-spins again to a co2_turnX (no
    # offer, no trap yet).
    for i in range(4):
        turn = controller.choose(0)
        check("tca_shuffle_autospin_%d" % i,
              turn.node.id in ("tca.co2_turn1", "tca.co2_turn2"),
              "node=%r" % turn.node.id)

    # --- 5th return: visits -> 6 -> the trap AUTO-FIRES as a RESULT
    # (bad.cycle_trap_host_death; NO take_choice call by this smoke).
    turn = controller.choose(0)
    check("trap_auto_fired_bad_ending",
          turn.node.id == "bad.cycle_trap_host_death"
          and turn.node.is_ending == "bad",
          "node=%r is_ending=%r" % (turn.node.id, turn.node.is_ending))
    check("trap_auto_fire_finished_bad",
          controller._engine.state.finished is True
          and controller._engine.state.ending_tier == "bad",
          "finished=%r tier=%r" % (controller._engine.state.finished,
                                   controller._engine.state.ending_tier))
    check("trap_auto_fire_visits_6",
          controller._engine.state.visit_counts.get("tca.shuffle", 0) == 6,
          "visits=%r" % controller._engine.state.visit_counts.get(
              "tca.shuffle", 0))
    # Assert the bad_ending achievement unlocked (06-04) -- the auto-fire
    # reused take_choice's achievement path.
    ach_ids = [a["id"] for a in ach_board.data["achievements_unlocked"]]
    check("ach_bad_ending_unlocked", "bad_ending" in ach_ids,
          "unlocked=%r" % ach_ids)

    # --- RNG determinism (same seed -> same spin outcome): a fresh
    # controller with the SAME seed replays the SAME first-spin node.
    molops_d, edit_router_d, _ab_d, _ = _build_molops_stack()
    controller_d = Controller(
        STORY_DIR, molops_d, cmd, edit_router_d, view=MockView(),
        prompt_fn=_prompt_fn, count_fn=_count_fn,
        achievement_board=AchievementBoard(
            path=tempfile.mktemp(suffix="_smoke_ach_d.json")),
        view_provider=_view_provider, view_applier=_view_applier,
        edit_offer_fn=_edit_offer_fn)
    controller_d.start_game("glucose", seed=42)
    for _ in range(4):
        controller_d.choose(0)  # intro.preface -> ... -> gly.g6p
    controller_d.choose(0)  # gly.g6p -> gly.pfk
    controller_d.choose(0)  # gly.pfk -> gly.fbp_to_pyruvate
    controller_d.choose(0)  # -> gly.pyruvate_kinase
    controller_d.choose(0)  # -> gly.pyruvate
    controller_d.choose(0)  # -> pyr.branch
    controller_d.choose(0)  # -> pyr.pdh
    controller_d.choose(0)  # -> tca.entry
    controller_d.choose(0)  # -> tca.citrate_synthase
    controller_d.choose(0)  # -> tca.aconitase
    spin_d = controller_d.choose(0).node.id  # -> shuffle -> AUTO-SPIN
    check("shuffle_spin_deterministic_same_seed",
          spin_d == first_spin_node,
          "seed42 first=%r replay=%r" % (first_spin_node, spin_d))
except Exception as e:
    import traceback
    traceback.print_exc()
    check("walk_pdh_to_tca_entry", False, repr(e))
    check("walk_tca_entry_to_cs", False, repr(e))
    check("walk_cs_to_aconitase", False, repr(e))
    check("tca_shuffle_is_mixed", False, repr(e))
    check("shuffle_auto_spin_no_click", False, repr(e))
    check("shuffle_edit_offer_declined_once", False, repr(e))
    check("shuffle_first_entry_visits_1", False, repr(e))
    check("shuffle_never_rendered", False, repr(e))
    check("tca_shuffle_autospin_0", False, repr(e))
    check("tca_shuffle_autospin_1", False, repr(e))
    check("tca_shuffle_autospin_2", False, repr(e))
    check("tca_shuffle_autospin_3", False, repr(e))
    check("trap_auto_fired_bad_ending", False, repr(e))
    check("trap_auto_fire_finished_bad", False, repr(e))
    check("trap_auto_fire_visits_6", False, repr(e))
    check("ach_bad_ending_unlocked", False, repr(e))
    check("shuffle_spin_deterministic_same_seed", False, repr(e))


# =========================================================================
# Stage 6b: SAME-CONTROLLER restart after the bad ending (06-14 re-verify
# round 3 -- S1 regression guard on the REAL molops stack + REAL graph).
#
# The debugger (.planning/debug/bad-end-restart-and-edit-pool.md) proved the
# controller/engine restart is CLEAN with WSL mocks (probe A: after the
# auto-fired trap, start_game on the SAME controller landed intro.preface,
# finished=None, guard False, view grew). This stage formalizes that proof
# against the REAL stack, plus the probe-E stash symmetry (both edit stashes
# cleared by the restart -- the Fix-2 start_game/load hardening).
#
# Reuses stage 6's flow result: the main `controller` is now FINISHED at
# bad.cycle_trap_host_death (trap auto-fired at visits==6, offer declined).
# The stage-5 gly.pfk edit seam left BOTH stashes set ('gly.pfk' / 'gly.pfk',
# engine-level goto repositioning never clears them) -- probe E's exact
# precondition. Then start_game AGAIN ON THE SAME CONTROLLER and assert the
# fresh game.
# =========================================================================
try:
    # Pre-restart context (probe A + probe E preconditions).
    check("restart_pre_finished_bad",
          bool(controller._engine.state.finished)
          and controller._engine.state.ending_tier == "bad",
          "finished=%r tier=%r" % (controller._engine.state.finished,
                                   controller._engine.state.ending_tier))
    check("restart_pre_guard_false",
          controller._resolving_shuffle is False,
          "guard=%r" % controller._resolving_shuffle)
    check("restart_pre_stash_enzyme",
          controller._pending_edit_enzyme_id == "gly.pfk",
          "stash=%r" % controller._pending_edit_enzyme_id)
    check("restart_pre_stash_source",
          controller._pending_edit_source_node_id == "gly.pfk",
          "source=%r" % controller._pending_edit_source_node_id)
    turns_before = len(mock_view.turns)

    # The SAME-controller restart (NOT a fresh controller -- stage 7 does
    # that; the S1 report was "restart the game on the ending screen").
    turn = controller.start_game("glucose", 42)

    check("restart_returns_intro_preface",
          turn.node.id == "intro.preface",
          "node=%r" % turn.node.id)
    # finished is falsy while playing (GameState.finished is None on a new
    # game; truthy only after an ending node is marked).
    check("restart_finished_falsy",
          not controller._engine.state.finished,
          "finished=%r" % controller._engine.state.finished)
    check("restart_view_new_turn",
          len(mock_view.turns) > turns_before
          and mock_view.turns[-1].node.id == "intro.preface",
          "turns %d->%d last=%r" % (
              turns_before, len(mock_view.turns),
              mock_view.turns[-1].node.id))
    check("restart_guard_false",
          controller._resolving_shuffle is False,
          "guard=%r" % controller._resolving_shuffle)
    # Probe-E symmetry (Fix 2): BOTH edit stashes are None post-restart.
    check("restart_stashes_cleared",
          controller._pending_edit_enzyme_id is None
          and controller._pending_edit_source_node_id is None,
          "enzyme=%r source=%r" % (controller._pending_edit_enzyme_id,
                                   controller._pending_edit_source_node_id))
except Exception as e:
    import traceback
    traceback.print_exc()
    check("restart_pre_finished_bad", False, repr(e))
    check("restart_pre_guard_false", False, repr(e))
    check("restart_pre_stash_enzyme", False, repr(e))
    check("restart_pre_stash_source", False, repr(e))
    check("restart_returns_intro_preface", False, repr(e))
    check("restart_finished_falsy", False, repr(e))
    check("restart_view_new_turn", False, repr(e))
    check("restart_guard_false", False, repr(e))
    check("restart_stashes_cleared", False, repr(e))


# =========================================================================
# Stage 7: reach a True ending via the BFS-distance-guided walk (fresh
# controller, new seed). The walk is deterministic + assertable (NOT "many
# Continue clicks"). Algorithm:
#   a. Precompute dist[id] = BFS shortest-path distance from every node to
#      end.true over the reverse choice edges (cond-IGNORED -- structural
#      reachability). dist[end.true] = 0; BFS backward. Nodes with no path get
#      infinity.
#   b. Walk loop: while turn.node.is_ending is None:
#      - path.append(turn.node.id)
#      - If tca.shuffle: choose(0) (RNG spins among the 2 weighted choices;
#        both have finite dist). Do NOT take edit:offer or cycle-trap.
#      - Else: eligible = [c for c in choices if cond is None or cond_met];
#        pick c* = min by dist[c*.goto] (ties broken by list order); index =
#        eligible.index(c*); choose(index).
#   c. Assert end.true + is_ending == "true" + true_ending unlocked.
#   d. Assert the milestone path (in-order).
# =========================================================================


def _compute_distances_to_end_true(graph):
    """BFS shortest-path distance from every node to end.true over the REVERSE
    choice edges (cond-IGNORED). dist[end.true] = 0; nodes with no path get a
    large sentinel (infinity). Returns {node_id: distance}."""
    INF = float("inf")
    nodes = graph.all_nodes()
    # Build reverse adjacency: for each node X with a choice goto Y, add X to
    # reverse_adj[Y] (so BFS from Y reaches X in one step backward).
    reverse_adj = {}  # type: dict
    for nid, node in nodes.items():
        for ch in node.choices:
            goto = ch.goto
            if goto is None:
                continue
            reverse_adj.setdefault(goto, []).append(nid)
    # BFS backward from end.true.
    dist = {nid: INF for nid in nodes}
    if "end.true" not in nodes:
        return dist
    dist["end.true"] = 0
    queue = ["end.true"]
    while queue:
        cur = queue.pop(0)
        d = dist[cur]
        for pred in reverse_adj.get(cur, []):
            if dist[pred] > d + 1:
                dist[pred] = d + 1
                queue.append(pred)
    return dist


def _bfs_walk_to_true(controller, dist, seed):
    """Walk from intro.preface to end.true using the BFS-distance-guided choice
    selection. Returns the path list (non-ending node ids visited, in order) +
    the final turn (the end.true TurnResult). Fails the check() if the walk
    exceeds a sane step bound (catches infinite loops).

    Shuffle note (user decision 1, 2026-08-30): tca.shuffle AUTO-RESOLVES in
    the controller, so choose() from tca.aconitase returns the POST-spin
    co2_turnX already -- the shuffle never surfaces as a rendered turn. The
    walk records the "tca.shuffle" milestone from the CHOICE TARGET (the
    chosen goto) instead of the returned turn.
    """
    path = []  # type: list
    turn = controller.start_game("glucose", seed=seed)
    max_steps = 100  # safety net (the natural path is ~28 steps)
    steps = 0
    while turn.node.is_ending is None:
        path.append(turn.node.id)
        steps += 1
        if steps > max_steps:
            check("true_walk_bounded", False,
                  "exceeded %d steps; path so far=%r" % (max_steps, path))
            return path, turn
        # Pure non-weighted node: pick the eligible choice with the MIN
        # dist[goto]. Ties broken by list order (first wins). (The shuffle is
        # never a rendered turn -- an incoming choice to it auto-resolves in
        # the controller, so no shuffle special-case is needed here.)
        node = turn.node
        eligible = [c for c in node.choices
                    if c.cond is None
                    or controller._engine.choice_cond_met(c)]
        if not eligible:
            check("true_walk_no_eligible_at_%s" % turn.node.id, False,
                  "no eligible choices at %s" % turn.node.id)
            return path, turn
        # Pick the choice with minimum dist[goto] (infinity for dead-ends).
        best = None
        best_dist = None
        for c in eligible:
            d = dist.get(c.goto, float("inf"))
            if best is None or d < best_dist:
                best = c
                best_dist = d
        if best.goto == "tca.shuffle":
            # The shuffle milestone: record the CHOICE TARGET -- the returned
            # turn is already the post-spin co2_turnX (auto-resolved).
            path.append("tca.shuffle")
        index = eligible.index(best)
        turn = controller.choose(index)
    return path, turn


try:
    # Fresh controller + fresh achievement board for the True-ending walk.
    molops_t, edit_router_t, ach_board_t, ach_path_t = _build_molops_stack()
    mock_view_t = MockView()
    controller_t = Controller(
        STORY_DIR, molops_t, cmd, edit_router_t, view=mock_view_t,
        prompt_fn=_prompt_fn, count_fn=_count_fn,
        achievement_board=ach_board_t,
        view_provider=_view_provider, view_applier=_view_applier,
        edit_offer_fn=_edit_offer_fn)

    graph = controller_t._engine.graph
    dist = _compute_distances_to_end_true(graph)

    # Sanity: end.true has dist 0; intro.preface has finite dist.
    check("bfs_dist_end_true_0", dist.get("end.true") == 0,
          "dist[end.true]=%r" % dist.get("end.true"))
    check("bfs_dist_preface_finite",
          dist.get("intro.preface", float("inf")) != float("inf"),
          "dist[intro.preface]=%r" % dist.get("intro.preface"))

    # Walk to end.true.
    path, final_turn = _bfs_walk_to_true(controller_t, dist, seed=7)

    # Assert the ending.
    check("true_ending_reached",
          final_turn.node.id == "end.true"
          and final_turn.node.is_ending == "true",
          "node=%r is_ending=%r" % (final_turn.node.id, final_turn.node.is_ending))

    # Assert the true_ending achievement unlocked (06-04).
    ach_ids_t = [a["id"] for a in ach_board_t.data["achievements_unlocked"]]
    check("ach_true_ending_unlocked", "true_ending" in ach_ids_t,
          "unlocked=%r" % ach_ids_t)

    # Assert the milestone path (in-order). The glycolysis chain between
    # gly.start and pyr.branch is not hardcoded -- assert the milestones appear
    # in order via path.index() monotonicity.
    milestones = [
        "intro.preface", "intro.select", "intro.shell_glucose", "gly.start",
        "pyr.branch", "pyr.pdh", "tca.entry", "tca.citrate_synthase",
        "tca.aconitase", "tca.shuffle",
        "tca.isocitrate_dh", "tca.akg_dh", "tca.succinyl_coa_synthetase",
        "tca.fumarase", "tca.malate_dh", "tca.divert_to_good", "etc.entry",
        "etc.complex_i", "etc.complex_ii", "etc.complex_iii",
        "etc.complex_iv", "etc.atp_synthase",
    ]
    # All milestones present in path.
    missing = [m for m in milestones if m not in path]
    check("true_path_milestones_present", not missing,
          "missing=%r" % missing)
    # Milestones in strictly increasing index order (monotonic).
    indices = [path.index(m) for m in milestones]
    monotonic = all(indices[i] < indices[i + 1] for i in range(len(indices) - 1))
    check("true_path_milestones_monotonic", monotonic,
          "indices=%r" % indices)
    # The spin result (between tca.shuffle and tca.isocitrate_dh) is
    # tca.co2_turn1 or tca.co2_turn2.
    shuf_idx = path.index("tca.shuffle")
    iso_idx = path.index("tca.isocitrate_dh")
    if shuf_idx + 1 < len(path):
        spin_node = path[shuf_idx + 1]
        check("true_path_spin_is_co2_turn",
              spin_node in ("tca.co2_turn1", "tca.co2_turn2"),
              "spin_node=%r" % spin_node)
    else:
        check("true_path_spin_is_co2_turn", False,
              "no node after tca.shuffle in path")
    # The final turn is end.true (not in path -- path records non-ending nodes
    # only; the loop exits when is_ending is not None).
    check("true_path_ends_at_end_true",
          final_turn.node.id == "end.true",
          "final=%r" % final_turn.node.id)
    # Print the full path for diagnostics.
    print("SMOKE_TRUE_PATH: {0}".format(path))
except Exception as e:
    import traceback
    traceback.print_exc()
    check("bfs_dist_end_true_0", False, repr(e))
    check("bfs_dist_preface_finite", False, repr(e))
    check("true_ending_reached", False, repr(e))
    check("ach_true_ending_unlocked", False, repr(e))
    check("true_path_milestones_present", False, repr(e))
    check("true_path_milestones_monotonic", False, repr(e))
    check("true_path_spin_is_co2_turn", False, repr(e))
    check("true_path_ends_at_end_true", False, repr(e))


# =========================================================================
# Stage 8: save/load round-trip with view (06-03).
#
# Fresh controller, walk to a mid-game non-ending node (gly.g6p -- on_enter is
# just [hide_all], no network load), save, then load into a 2nd controller.
# Assert: current_node matches, seed matches, rng_state matches (the next draw
# is identical), the view was applied (the view_applier was called), AND the
# scene rebuilt (on_enter replayed -- hide_all dispatched).
# =========================================================================
try:
    # Fresh controller for the save/load test.
    molops_s, edit_router_s, _ab_s, _ = _build_molops_stack()
    mock_view_s = MockView()
    controller_s = Controller(
        STORY_DIR, molops_s, cmd, edit_router_s, view=mock_view_s,
        prompt_fn=_prompt_fn, count_fn=_count_fn,
        achievement_board=AchievementBoard(
            path=tempfile.mktemp(suffix="_smoke_ach_s.json")),
        view_provider=_view_provider, view_applier=_view_applier,
        edit_offer_fn=_edit_offer_fn)
    # Walk to gly.g6p (intro.preface -> intro.select -> intro.shell_glucose ->
    # gly.start -> gly.g6p). gly.g6p's on_enter is [hide_all] (no network).
    controller_s.start_game("glucose", seed=99)
    controller_s.choose(0)  # -> intro.select
    controller_s.choose(0)  # -> intro.shell_glucose
    controller_s.choose(0)  # -> gly.start
    controller_s.choose(0)  # -> gly.g6p
    save_node = controller_s._engine.state.current_node
    check("save_at_non_ending_node",
          save_node == "gly.g6p" and controller_s._engine.state.finished is None,
          "node=%r finished=%r" % (save_node, controller_s._engine.state.finished))

    # Save.
    save_path = tempfile.mktemp(suffix="_smoke_save.json")
    controller_s.save(save_path)
    check("save_file_exists", os.path.isfile(save_path),
          "path=%r exists=%r" % (save_path, os.path.isfile(save_path)))
    # The view was captured (state.view is a list of 18 floats).
    captured_view = controller_s._engine.state.view
    check("save_view_captured",
          captured_view is not None and len(captured_view) == 18,
          "view_len=%r" % (len(captured_view) if captured_view else None))

    # Load into a 2nd controller (same construction).
    molops_l, edit_router_l, _ab_l, _ = _build_molops_stack()
    mock_view_l = MockView()
    controller_l = Controller(
        STORY_DIR, molops_l, cmd, edit_router_l, view=mock_view_l,
        prompt_fn=_prompt_fn, count_fn=_count_fn,
        achievement_board=AchievementBoard(
            path=tempfile.mktemp(suffix="_smoke_ach_l.json")),
        view_provider=_view_provider, view_applier=_view_applier,
        edit_offer_fn=_edit_offer_fn)
    # Record the applied_views count BEFORE load.
    applied_before = len(_applied_views)
    controller_l.load(save_path)
    # Assert current_node matches.
    check("load_current_node_matches",
          controller_l._engine.state.current_node == save_node,
          "loaded=%r saved=%r" % (controller_l._engine.state.current_node, save_node))
    # Assert seed matches.
    check("load_seed_matches",
          controller_l._engine.state.seed == controller_s._engine.state.seed,
          "loaded=%r saved=%r" % (controller_l._engine.state.seed,
                                  controller_s._engine.state.seed))
    # Assert rng_state matches (the next draw is identical).
    check("load_rng_state_matches",
          controller_l._engine.state.rng_state == controller_s._engine.state.rng_state,
          "rng_match=%r" % (controller_l._engine.state.rng_state
                            == controller_s._engine.state.rng_state))
    # Assert the view was applied (the view_applier was called during load).
    check("load_view_applied",
          len(_applied_views) > applied_before,
          "applied_before=%d applied_after=%d" % (applied_before, len(_applied_views)))
    # Assert the scene rebuilt (on_enter replayed -- the loaded controller's
    # view rendered the restored turn: mock_view_l.turns is non-empty). The
    # engine.load replays on_enter via the controller's molaction_sink then
    # renders the TurnResult via view.render_turn -- a non-empty turns list
    # proves the load + replay + render completed.
    check("load_scene_rebuilt",
          len(mock_view_l.turns) >= 1,
          "turns=%d" % len(mock_view_l.turns))

    # Clean up the save file.
    try:
        os.remove(save_path)
    except OSError:
        pass
except Exception as e:
    import traceback
    traceback.print_exc()
    check("save_at_non_ending_node", False, repr(e))
    check("save_file_exists", False, repr(e))
    check("save_view_captured", False, repr(e))
    check("load_current_node_matches", False, repr(e))
    check("load_seed_matches", False, repr(e))
    check("load_rng_state_matches", False, repr(e))
    check("load_view_applied", False, repr(e))
    check("load_scene_rebuilt", False, repr(e))


# =========================================================================
# Stage 9: bulk-download runner (06-10).
#
# missing_large_pdbs(cmd) returns [] for the Phase 6 placeholder cast (the only
# download enzyme is PLACEHOLDER_large_enzyme with pdb_id "PLACEHOLDER_PDB" --
# the PLACEHOLDER guard skips it). The prompt does NOT fire for placeholder
# content. This is the mechanism check (the full bulk-download is human-verify).
# =========================================================================
try:
    from rpg.ui.bulk_download import (
        missing_large_pdbs, run_bulk_download, characters_to_lock,
        expected_download_characters)
    missing = missing_large_pdbs(cmd)
    check("bulk_download_missing_empty_placeholder",
          missing == [],
          "missing=%r" % (missing,))
    # expected_download_characters is also empty (only PLACEHOLDER entries).
    expected_chars = expected_download_characters()
    check("bulk_download_expected_chars_empty",
          len(expected_chars) == 0,
          "expected=%r" % (expected_chars,))
    # characters_to_lock on an empty failed list returns empty set.
    locked = characters_to_lock([])
    check("bulk_download_no_locks_on_no_failures",
          len(locked) == 0,
          "locked=%r" % (locked,))
    # run_bulk_download on an empty missing list returns all-zeros.
    result = run_bulk_download(cmd, [])
    check("bulk_download_runner_empty",
          result == {"completed": 0, "failed": [], "canceled": False},
          "result=%r" % (result,))
except Exception as e:
    import traceback
    traceback.print_exc()
    check("bulk_download_missing_empty_placeholder", False, repr(e))
    check("bulk_download_expected_chars_empty", False, repr(e))
    check("bulk_download_no_locks_on_no_failures", False, repr(e))
    check("bulk_download_runner_empty", False, repr(e))


# =========================================================================
# Cleanup: delete the temp achievements files + loaded cmd objects.
# =========================================================================
try:
    for _p in [ach_path_main, ach_path_t]:
        if _p and os.path.isfile(_p):
            os.remove(_p)
except OSError:
    pass
try:
    # src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete
    cmd.delete("hero_atom")
    cmd.delete("aa_cast")
    cmd.delete("glucose")
except Exception:
    pass


# =========================================================================
# Stage 10: final sentinel.
# =========================================================================
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
