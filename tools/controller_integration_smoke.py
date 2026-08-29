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
#     __init__.py. So os.getcwd() (= repo root) + import c14.paths locates
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
# the workspace and `import c14` works (sys.path includes '' = cwd). Insert
# cwd explicitly as belt-and-suspenders so this script is robust if sys.path
# lacks ''.
sys.path.insert(0, os.getcwd())

import pymol
from pymol import cmd
import c14.paths
import c14.protonation_catalog  # pure-data catalog MODULE (passed by reference)
from c14.pymol_layer.molops import MolOps
from c14.pymol_layer.asset_manager import AssetManager
from c14.pymol_layer.edit_ops import EditOps
from c14.pymol_layer.protonation import ProtonationManager
from c14.edit_router import EditRouter, EditsTable
from c14.achievements import AchievementBoard
from c14.ui.controller import Controller

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
        cmd, editops, c14.protonation_catalog, assets)
    molops = MolOps(cmd, assets, editops, protonation)
    edits_path = str(c14.paths.data_path("data", "edits.json"))
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
# carbons so the resolver WOULD prompt + rewrite to "hero_atom and elem C").
_prompt_calls = []  # type: list


def _prompt_fn(message):
    _prompt_calls.append(message)
    return True


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
        view_provider=_view_provider, view_applier=_view_applier)
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
        view_provider=_view_provider, view_applier=_view_applier)

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
    # the same iterate approach). At least 1 atom in hero_atom has label "YOU".
    lbls = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate  (read label text; collector `lbls` avoids collision)
    cmd.iterate("hero_atom", "lbls.append(label)", space={"lbls": lbls})
    check("hero_you_label_dispatched",
          any(l == "YOU" for l in lbls),
          "labels=%r" % lbls)
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
    check("walk_pfk_to_fbp", False, repr(e))
    check("walk_fbp_to_pk", False, repr(e))
    check("walk_pk_to_pyr", False, repr(e))
    check("walk_pyr_to_branch", False, repr(e))
    check("pyr_branch_aerobic_cond_met", False, repr(e))
    check("pyr_branch_anaerobic_cond_not_met", False, repr(e))
    check("pyr_branch_to_pdh", False, repr(e))


# =========================================================================
# Stage 6: advance into TCA + verify tca.shuffle goto routing (06-06 Blocker B)
# -> reach a Bad ending (SC3 Bad path) + bad_ending achievement unlocked.
#
# Path: pyr.pdh -> (Continue into TCA) tca.entry -> (Continue)
#   tca.citrate_synthase -> (Continue to aconitase) tca.aconitase ->
#   (Continue to the shuffle) tca.shuffle.
# At tca.shuffle: is_mixed_weighted_node True; spin the wheel (choose(0) --
# RNG picks turn1/turn2); return via "The cycle turns again" (choose(0));
# repeat 5x to bump tca.shuffle visits to 6; the cycle-trap cond
# (visits.get('tca.shuffle', 0) > 5) becomes True; take_choice(cycle_trap)
# -> bad.cycle_trap_host_death (a Bad ending).
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
    # tca.aconitase -> tca.shuffle (Continue to the shuffle, index 0)
    turn = controller.choose(0)
    check("walk_aconitase_to_shuffle", turn.node.id == "tca.shuffle",
          "node=%r" % turn.node.id)

    # Assert is_mixed_weighted_node (06-06): tca.shuffle has 2 weighted + 1
    # non-weighted (edit:offer) eligible choice (cycle-trap cond not yet met).
    shuffle_node = controller._engine.graph.get_node("tca.shuffle")
    check("tca_shuffle_is_mixed",
          controller.is_mixed_weighted_node(shuffle_node) is True,
          "mixed=%r" % controller.is_mixed_weighted_node(shuffle_node))

    # Spin + return 5 times to bump tca.shuffle visits to 6 (1 initial + 5
    # returns). Each spin: choose(0) -> co2_turn1/2 (RNG picks). Each return:
    # choose(0) -> "The cycle turns again" -> tca.shuffle.
    for i in range(5):
        turn = controller.choose(0)  # spin -> co2_turn1 or co2_turn2
        check("tca_shuffle_spin_%d" % i,
              turn.node.id in ("tca.co2_turn1", "tca.co2_turn2"),
              "node=%r" % turn.node.id)
        turn = controller.choose(0)  # "The cycle turns again" -> tca.shuffle
        check("tca_shuffle_return_%d" % i,
              turn.node.id == "tca.shuffle",
              "node=%r" % turn.node.id)

    # After 6 visits, the cycle-trap cond (visits > 5) is met.
    visits = controller._engine.state.visit_counts.get("tca.shuffle", 0)
    check("tca_shuffle_visits_6", visits == 6,
          "visits=%r" % visits)
    cycle_trap = next(ch for ch in shuffle_node.choices
                      if "cycle_trap" in (ch.tags or []))
    trap_met = controller._engine.choice_cond_met(cycle_trap)
    check("tca_shuffle_cycle_trap_cond_met", trap_met is True,
          "trap_cond=%r" % trap_met)

    # take_choice(cycle_trap) -> bad.cycle_trap_host_death (via engine.goto,
    # NOT choose -- 06-06 Blocker B fix). This is a Bad ending (SC3 Bad path).
    turn = controller.take_choice(cycle_trap)
    check("bad_ending_reached",
          turn.node.id == "bad.cycle_trap_host_death"
          and turn.node.is_ending == "bad",
          "node=%r is_ending=%r" % (turn.node.id, turn.node.is_ending))
    # Assert the bad_ending achievement unlocked (06-04).
    ach_ids = [a["id"] for a in ach_board.data["achievements_unlocked"]]
    check("ach_bad_ending_unlocked", "bad_ending" in ach_ids,
          "unlocked=%r" % ach_ids)
except Exception as e:
    import traceback
    traceback.print_exc()
    check("walk_pdh_to_tca_entry", False, repr(e))
    check("walk_tca_entry_to_cs", False, repr(e))
    check("walk_cs_to_aconitase", False, repr(e))
    check("walk_aconitase_to_shuffle", False, repr(e))
    check("tca_shuffle_is_mixed", False, repr(e))
    check("tca_shuffle_spin_0", False, repr(e))
    check("tca_shuffle_return_0", False, repr(e))
    check("tca_shuffle_visits_6", False, repr(e))
    check("tca_shuffle_cycle_trap_cond_met", False, repr(e))
    check("bad_ending_reached", False, repr(e))
    check("ach_bad_ending_unlocked", False, repr(e))


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
    exceeds a sane step bound (catches infinite loops)."""
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
        if turn.node.id == "tca.shuffle":
            # Spin the wheel (choose(0) -- RNG picks among the 2 weighted
            # choices -> tca.co2_turn1 or tca.co2_turn2; both have finite dist).
            turn = controller.choose(0)
        else:
            # Pure non-weighted node: pick the eligible choice with the MIN
            # dist[goto]. Ties broken by list order (first wins).
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
        view_provider=_view_provider, view_applier=_view_applier)

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
        view_provider=_view_provider, view_applier=_view_applier)
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
        view_provider=_view_provider, view_applier=_view_applier)
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
    from c14.ui.bulk_download import (
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
