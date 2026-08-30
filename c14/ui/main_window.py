# c14/ui/main_window.py -- Phase 6 Plan 06-08 the Qt MainWindow + StartDialog.
#
# The core UI surface (SC1: "the main window opens with character selection,
# story text, choice panel, and cast/help/save/load/achievement controls"). The
# MainWindow is a THIN RENDERER over the 06-06 Controller's TurnResult API:
#
#   * It constructs the molops stack (real cmd + AssetManager + EditOps +
#     ProtonationManager + MolOps + EditRouter) + the Controller (06-06) at init
#     + wires the StoryPanel/ChoicePanel widgets (06-08 widgets.py).
#   * On each UI event it calls ONE controller method (start_game / choose /
#     take_choice / request_edit / apply_edit / save / load); the controller
#     calls back via view.render_turn(turn) to re-render. The MainWindow NEVER
#     calls cmd.* for molecular ops directly (always via the controller ->
#     molops) -- the only direct cmd.* uses are the injected count_fn
#     (cmd.count_atoms) + view_provider/view_applier (cmd.get_view/set_view)
#     + the prompt_fn (QMessageBox.question -- the OQ-6 warn+confirm gate).
#   * The toolbar [New Game] [Save] [Load] [Achievements] [Help] opens the
#     sibling dialogs (06-09 edit_dialog, 06-11 save_load_dialogs, 06-12
#     achievements_dialog, 06-13 help_dialog) via DEFERRED imports inside the
#     handlers -- so this file py_compiles even if a sibling dialog isn't
#     written yet (06-09/06-11 run in parallel); the import resolves at click
#     time.
#
# WARNING 4 seam (edit-prompt detection): when the controller's TurnResult node
# id == "edit.prompt" (the player clicked an edit:offer choice at a mixed
# weighted node -> controller.request_edit stashed the enzyme_id + gotos
# edit.prompt), render_turn opens the EditDialog (06-09) with the stashed
# enzyme_id. On accept, build_edit_intent + apply_edit route via the EditRouter.
# The MainWindow only WIRES this seam (NO modification to 06-06's controller or
# 06-09's dialog -- it calls the existing API: _pending_edit_enzyme_id +
# build_edit_intent + apply_edit).
#
# Gate-EXEMPT: c14/ui/ is in tools/check_imports.py SKIP_DIRS, so this module
# MAY import pymol.Qt + pymol.cmd + the gate-exempt pymol_layer modules. NO
# domain-tier (c14/ root) file imports pymol -- the boundary holds. Importing
# this module in pure WSL python3.6 FAILS (no Qt/pymol installed) -- that is
# EXPECTED (06-RESEARCH-ui-adapter.md Pitfall 1); only `python3.6 -m py_compile`
# is WSL-verifiable here. The functional window (opens, story renders, choices
# clickable, tca.shuffle Spin/Edit/cycle-trap, start dialog, save/load/
# achievements/help buttons route) is human-verify in plan 06-14.
#
# PYTHON 3.6 ONLY: plain classes, .format() strings, NO f-strings / @dataclass
# / walrus (matches the repo precedent; 3.6.9 has no dataclasses module).
"""c14/ui/main_window.py -- Qt MainWindow + StartDialog (SC1 core UI surface).

A thin renderer over the 06-06 Controller. Constructs the molops stack +
Controller + AchievementBoard at init; wires a toolbar (New/Save/Load/
Achievements/Help) + a central StoryPanel/ChoicePanel + a status bar. The
controller calls back via ``render_turn(turn)`` to re-render after each engine
turn. Sibling dialogs are imported lazily inside their handlers so this file
py_compiles without them (06-09/06-11 run in parallel).

Gate-EXEMPT (c14/ui/). py_compile is the only WSL-verifiable check; the
functional UI is human-verify in 06-14.
"""

import os

from pymol import cmd  # real cmd handle (prod only -- WSL import fails, EXPECTED)
from pymol.Qt import QtCore, QtGui, QtWidgets

import c14.paths
import c14.protonation_catalog  # pure-data catalog MODULE (passed by reference)
from c14.pymol_layer.molops import MolOps
from c14.pymol_layer.asset_manager import AssetManager
from c14.pymol_layer.edit_ops import EditOps
from c14.pymol_layer.protonation import ProtonationManager
from c14.edit_router import EditRouter, EditsTable
from c14.achievements import AchievementBoard
from c14.ui.controller import Controller
from c14.ui.widgets import StoryPanel, ChoicePanel


def _resolve_story_dir():
    # type: () -> str
    """Resolve the story bundle dir.

    Prefer the bundled (shipped) path ``c14/data/story_glucose`` (where the
    build script 06-07 bundles it in the installable zip); fall back to the
    repo-root dev path ``data/story_glucose`` so the MainWindow works both in
    the installed plugin AND when running from the repo checkout (dev -- the
    build script only copies story_glucose into c14/data/ at zip-build time, so
    in a bare repo checkout c14/data/story_glucose/ does not exist). Returns
    the str path (or the shipped path if neither exists, letting
    ``StoryGraph.load`` raise a clear ``FileNotFoundError``).
    """
    shipped = c14.paths.data_path("data", "story_glucose")
    if shipped.is_dir():
        return str(shipped)
    # Dev fallback: repo-root data/story_glucose. __file__ = c14/ui/main_window.py
    # -> repo root = two dirs up from this file's directory.
    here = os.path.dirname(os.path.abspath(__file__))
    dev = os.path.join(here, "..", "..", "data", "story_glucose")
    if os.path.isdir(dev):
        return dev
    return str(shipped)  # let StoryGraph.load raise FileNotFoundError


class StartDialog(QtWidgets.QDialog):
    """Modal start dialog: character selection (Glucose only in Phase 6) + an
    optional seed input.

    Three radio buttons: Glucose (enabled, checked by default); Fatty acid +
    Alcohol (DISABLED with an "Available in a future phase." tooltip -- Phase 6
    is glucose-only per ``05.1-DESIGN.md`` fa.stub/alc.stub). A seed QLineEdit
    (optional): blank = random/play mode (``seed=None``); a valid integer =
    reproducible demo/fixed-seed mode. OK/Cancel.

    On accept, ``self.result_character`` ("glucose" in Phase 6) +
    ``self.result_seed`` (int or None) are set for the caller to read. An
    invalid (non-integer, non-blank) seed shows a warning + keeps the dialog
    open (the accept is vetoed).
    """

    def __init__(self, parent=None):
        super(StartDialog, self).__init__(parent)
        self.setWindowTitle("RPG: Tale of C -- New Game")
        self.setMinimumWidth(360)
        # Defaults read by the caller on accept.
        self.result_character = "glucose"
        self.result_seed = None

        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(QtWidgets.QLabel("<b>Choose your hero</b>"))
        # 3 radio buttons; Glucose enabled + checked; FA + Alcohol disabled
        # (Phase 6 is glucose-only per 05.1-DESIGN.md fa.stub/alc.stub).
        self._glucose = QtWidgets.QRadioButton("Glucose (C6H12O6) -- the sugar")
        self._glucose.setChecked(True)
        layout.addWidget(self._glucose)
        self._fatty = QtWidgets.QRadioButton("Fatty acid")
        self._fatty.setEnabled(False)
        self._fatty.setToolTip("Available in a future phase.")
        layout.addWidget(self._fatty)
        self._alcohol = QtWidgets.QRadioButton("Alcohol")
        self._alcohol.setEnabled(False)
        self._alcohol.setToolTip("Available in a future phase.")
        layout.addWidget(self._alcohol)

        # Seed input (optional; blank = random/play; int = reproducible demo).
        layout.addWidget(QtWidgets.QLabel(
            "Seed (optional -- blank = random play; an integer = "
            "reproducible demo)"))
        self._seed_edit = QtWidgets.QLineEdit()
        self._seed_edit.setPlaceholderText("e.g. 42 (blank = random)")
        layout.addWidget(self._seed_edit)

        # OK / Cancel (standard QDialogButtonBox).
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        # type: () -> None
        """Validate the seed (blank -> None; valid int -> int; invalid -> warn
        + veto the accept) + set result_character/result_seed before accepting.
        """
        text = self._seed_edit.text().strip()
        if not text:
            self.result_seed = None
        else:
            try:
                self.result_seed = int(text)
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self, "Invalid seed",
                    "The seed must be an integer (or blank for random play).")
                return  # veto -- do not call super().accept()
        # Character: only Glucose is enabled in Phase 6 (FA/Alcohol are disabled
        # radio buttons, so they can never be checked). Default to "glucose".
        self.result_character = "glucose"
        super(StartDialog, self).accept()


class MainWindow(QtWidgets.QMainWindow):
    """The SC1 core UI surface: a thin renderer over the 06-06 Controller.

    Constructs the molops stack (real cmd + AssetManager + EditOps +
    ProtonationManager + MolOps + EditRouter) + the Controller + the
    AchievementBoard (06-04, default user_data_path for ACH-02 cross-session)
    at init; wires a toolbar [New Game] [Save] [Load] [Achievements] [Help] +
    a central StoryPanel (06-08) / ChoicePanel (06-08) + a status bar (current
    node id / character / seed). The controller calls back via
    :meth:`render_turn` after each engine turn; the MainWindow NEVER calls
    cmd.* for molecular ops directly (always via the controller -> molops).

    Sibling dialogs (06-09 edit_dialog, 06-11 save_load_dialogs, 06-12
    achievements_dialog, 06-13 help_dialog) are imported LAZILY inside their
    handlers so this file py_compiles without them (parallel execution). The
    OQ-6 warn+confirm gate is wired via the ``prompt_fn`` lambda (a
    QMessageBox.question wrapper passed to the controller).
    """

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("RPG: Tale of C")
        self.setMinimumSize(640, 520)

        # ---- construct the molops stack (real cmd) ----
        # cmd AND AssetManager AND EditOps AND ProtonationManager are injected
        # into MolOps (the 3-tier testability pattern -- molops stays unit-
        # testable with MockCmd in WSL; here we wire the REAL cmd for prod).
        assets = AssetManager(cmd)
        editops = EditOps(cmd)
        protonation = ProtonationManager(
            cmd, editops, c14.protonation_catalog, assets)
        molops = MolOps(cmd, assets, editops, protonation)
        # EditRouter over the bundled c14/data/edits.json lookup table.
        edits_path = str(c14.paths.data_path("data", "edits.json"))
        edit_router = EditRouter(EditsTable.load(edits_path))

        # ---- AchievementBoard (06-04; default user_data_path for ACH-02) ----
        achievement_board = AchievementBoard()

        # ---- injected callbacks for the controller ----
        # view_provider/view_applier close the 06-03 view-matrix gap (save
        # captures cmd.get_view(); load applies cmd.set_view() AFTER the
        # on_enter replay so the saved camera wins).
        view_provider = lambda: list(cmd.get_view())
        view_applier = lambda v: cmd.set_view(v)
        # prompt_fn = the OQ-6 warn+confirm gate (a QMessageBox.question wrapper
        # -- passed to the controller so molops stays pure). Returns True iff
        # the user confirms highlighting the first carbon as the hero.
        prompt_fn = lambda message: (
            QtWidgets.QMessageBox.question(
                self, "Hero ambiguity", message,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            == QtWidgets.QMessageBox.Yes)
        # edit_offer_fn = the tca.shuffle one-time edit offer (user decision 1,
        # 2026-08-30: the wheel auto-spins -- the soul jump is not a decision;
        # the aconitase edit is OFFERED exactly once on the first entry). A
        # SEPARATE wrapper so the dialog title reads "The wheel is about to
        # turn" instead of the OQ-6 "Hero ambiguity" title.
        edit_offer_fn = lambda message: (
            QtWidgets.QMessageBox.question(
                self, "The wheel is about to turn", message,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            == QtWidgets.QMessageBox.Yes)
        # count_fn wraps cmd.count_atoms (the HeroResolver's hero-selector
        # count pre-check).
        count_fn = lambda sele: cmd.count_atoms(sele)

        # ---- the story bundle dir (shipped, with a dev fallback) ----
        story_dir = _resolve_story_dir()

        # ---- the Controller (06-06) -- view=self wires render_turn ----
        self._controller = Controller(
            story_dir, molops, cmd, edit_router, view=self,
            prompt_fn=prompt_fn, count_fn=count_fn,
            achievement_board=achievement_board,
            view_provider=view_provider, view_applier=view_applier,
            edit_offer_fn=edit_offer_fn)

        # ---- build the UI ----
        self._build_toolbar()
        self._build_central()
        self.statusBar().showMessage("Ready -- click New Game")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_toolbar(self):
        """Toolbar: [New Game] [Save] [Load] [Achievements] [Help]. Each action
        is connected to its handler (the sibling-dialog handlers import lazily
        inside the handler so this file compiles without them)."""
        toolbar = self.addToolBar("Game")
        toolbar.setMovable(False)
        act_new = toolbar.addAction("New Game")
        act_new.triggered.connect(self._new_game)
        act_save = toolbar.addAction("Save")
        act_save.triggered.connect(self._save)
        act_load = toolbar.addAction("Load")
        act_load.triggered.connect(self._load)
        act_ach = toolbar.addAction("Achievements")
        act_ach.triggered.connect(self._open_achievements)
        act_help = toolbar.addAction("Help")
        act_help.triggered.connect(self._open_help)

    def _build_central(self):
        """Central widget: StoryPanel (top, stretch 2) + ChoicePanel (bottom,
        stretch 1) in a QVBoxLayout. The ChoicePanel's new_game_requested
        signal (emitted at an ending) is wired to _new_game."""
        central = QtWidgets.QWidget()
        central_layout = QtWidgets.QVBoxLayout(central)
        self._story = StoryPanel()
        self._choice = ChoicePanel(self._controller)
        central_layout.addWidget(self._story, 2)
        central_layout.addWidget(self._choice, 1)
        self.setCentralWidget(central)
        # An ending's "Start a new game" button emits new_game_requested ->
        # re-open the StartDialog (same as the toolbar's New Game).
        self._choice.new_game_requested.connect(self._new_game)

    # ------------------------------------------------------------------
    # The view interface: the controller calls this after each engine turn
    # ------------------------------------------------------------------
    def render_turn(self, turn):
        """Render a TurnResult into the StoryPanel + ChoicePanel + status bar.

        Three cases:
        1. Ending (``node.is_ending is not None``): render_ending + the
           ChoicePanel's "Start a new game" button + an "Ending reached: <tier>"
           status-bar message.
        2. edit.prompt (``node.id == "edit.prompt"``): the WARNING 4 seam --
           the player clicked an edit:offer choice -> controller.request_edit
           stashed the enzyme_id + gotos edit.prompt. Render the prompt text,
           clear the choice panel, then open the EditDialog (06-09) with the
           stashed enzyme_id. On accept, build_edit_intent + apply_edit route
           via the EditRouter (which re-renders the routed branch -- this
           render_turn is superseded).
        3. Normal node: render_node + the ChoicePanel choices + a
           "node=<id> character=<c> seed=<s>" status-bar message.
        """
        node = turn.node
        if node.is_ending is not None:
            self._story.render_ending(node)
            self._choice.render_turn(turn, self._controller)
            tier = (node.is_ending or "").capitalize()
            self.statusBar().showMessage("Ending reached: {0}".format(tier))
            return
        if node.id == "edit.prompt":
            # WARNING 4 seam: open the EditDialog with the stashed enzyme_id.
            # request_edit (06-06) set _pending_edit_enzyme_id BEFORE the goto.
            self._story.render_node(node)
            self._choice.clear()
            self.statusBar().showMessage(
                "Edit prompt -- choose an edit in the dialog.")
            self._open_edit_dialog()
            return
        # Normal node: render story + choices + status bar.
        self._story.render_node(node)
        self._choice.render_turn(turn, self._controller)
        character = self._engine_state("character")
        seed = self._engine_state("seed")
        # Orientation aid (06-14 SC2b human-verify fix): include the node's
        # stage tag in the status bar so the player can tell WHERE they are
        # (e.g. "node=gly.start  stage=glycolysis ..."). Nodes carry
        # "stage:<x>" tags (c14/story/model.py Node.tags); a node without a
        # stage tag simply omits the segment.
        stage = next((t.split(":", 1)[1] for t in node.tags
                      if t.startswith("stage:")), None)
        status = "node={0}".format(node.id)
        if stage:
            status += "  stage={0}".format(stage)
        status += "  character={0}  seed={1}".format(character, seed)
        self.statusBar().showMessage(status)

    def _engine_state(self, attr):
        # type: (str) -> object
        """Read one attribute off the controller's engine state (or None when
        no game is running yet -- state is None before start_game/load)."""
        state = self._controller._engine.state
        if state is None:
            return None
        return getattr(state, attr, None)

    # ------------------------------------------------------------------
    # Toolbar handlers
    # ------------------------------------------------------------------
    def _new_game(self):
        """Open the StartDialog; on accept, start a new game via the
        controller (which resolves the hero for the start node + enters it +
        records the achievement turn + renders)."""
        dlg = StartDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self._controller.start_game(dlg.result_character, dlg.result_seed)

    def _save(self):
        """Open the save-path dialog (06-11); on a chosen path, save via the
        controller (which delegates to engine.save -- Pattern 6: the scene
        rebuilds on load via on_enter replay, no .pse saved)."""
        from c14.ui.save_load_dialogs import ask_save_path  # lazy: 06-11 parallel
        path = ask_save_path(self)
        if path:
            self._controller.save(path)
            self.statusBar().showMessage("Saved: {0}".format(path))

    def _load(self):
        """Open the load-path dialog (06-11); on a chosen path, load via the
        controller (which delegates to engine.load -- replays the current
        node's on_enter to reconstruct the scene + applies the saved view)."""
        from c14.ui.save_load_dialogs import ask_load_path  # lazy: 06-11 parallel
        path = ask_load_path(self)
        if path:
            self._controller.load(path)
            self.statusBar().showMessage("Loaded: {0}".format(path))

    def _open_achievements(self):
        """Open the read-only AchievementsDialog (06-12) over the controller's
        AchievementBoard (kept current by the controller's on_turn calls)."""
        from c14.ui.achievements_dialog import AchievementsDialog  # lazy
        AchievementsDialog(self._controller._achievement_board, self).exec_()

    def _open_help(self):
        """Open the HelpDialog (06-13) -- the in-game help (DOC-03 editing
        pointers + PyMOL wiki links)."""
        from c14.ui.help_dialog import HelpDialog  # lazy
        HelpDialog(self).exec_()

    # ------------------------------------------------------------------
    # The edit-prompt seam (WARNING 4 fix)
    # ------------------------------------------------------------------
    def _open_edit_dialog(self):
        """Open the EditDialog (06-09) with the stashed enzyme_id; on accept,
        build the EditIntent + route it via the EditRouter -> branch or
        bad-ending pool, then re-render.

        The stashed ``_pending_edit_enzyme_id`` was set by
        ``controller.request_edit`` (06-06) at the edit-allowed SOURCE node
        BEFORE the goto edit.prompt -- this is the seam 06-06 provides + 06-09
        consumes; 06-08 only wires it in render_turn.

        History note (06-14 re-verify round 2): the 06-08 deviation (routing
        via the engine directly instead of ``controller.apply_edit``) was
        written when ``apply_edit`` raised RuntimeError at edit.prompt. That
        fallback has since LANDED in 06-06 (``apply_edit`` now falls back to
        ``edit_intent.enzyme_id`` when the current node has no
        edit:enzyme:<id> tag), so ``controller.apply_edit(intent)`` would work
        here too. The inline routing is KEPT (verified behavior; also covered
        by the B1 stale-stash clear below, mirroring apply_edit's own
        success-path clear).

        The import is deferred (inside this handler) so this file py_compiles
        without 06-09's edit_dialog.py (parallel execution); the import resolves
        at click time.
        """
        from c14.ui.edit_dialog import EditDialog  # lazy: 06-09 parallel
        enzyme_id = self._controller._pending_edit_enzyme_id
        dlg = EditDialog(self._controller, enzyme_id, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            op, target, args = dlg.selected_edit()
            intent = self._controller.build_edit_intent(op, target, args)
            # Route via the engine directly (apply_edit raises at edit.prompt --
            # see the deviation note above). build_edit_intent set
            # intent.enzyme_id from the stashed _pending_edit_enzyme_id; the
            # engine's apply_player_edit routes via the EditRouter + enters the
            # routed node (dispatching its on_enter to the controller's
            # molaction_sink). _record_achievement + _render mirror apply_edit.
            turn = self._controller._engine.apply_player_edit(
                intent, intent.enzyme_id)
            self._controller._record_achievement(
                turn, self._controller._engine.state.character)
            # B1 stale-stash hardening (06-14 re-verify round 2): the seam is
            # DONE once the edit routes + enters the routed node -- clear both
            # pending values so a stale enzyme_id can never silently supply an
            # enzyme for a future, unrelated dialog. (controller.apply_edit
            # does the same on ITS success path; this inline path mirrors it.)
            self._controller._pending_edit_enzyme_id = None
            self._controller._pending_edit_source_node_id = None
            self._controller._render(turn)
        else:
            # B2 anti-stranding fix (06-14 re-verify round 2): CANCEL leaves
            # the player AT edit.prompt -- a node with NO player-facing
            # choices (its choices are structural BFS paths consumed by the
            # EditRouter, never rendered), i.e. an empty choice panel with no
            # way forward. The skeleton is FROZEN (55 nodes / 21 endings --
            # no return node/edge may be added), so show a status message +
            # ONE "Return to the enzyme" button wired to the controller's
            # return_to_edit_source (engine.goto of the SOURCE node id that
            # request_edit stashed). The scene rebuilds from the source
            # node's on_enter replay + its choices re-render -- the player is
            # back at the enzyme node, not stranded.
            self.statusBar().showMessage(
                "Edit canceled -- return to the enzyme to keep going.")
            self._choice.render_single_action(
                "Return to the enzyme", self._return_to_enzyme)

    def _return_to_enzyme(self):
        """The B2 'Return to the enzyme' button handler: goto the stashed
        SOURCE node via the controller (which re-renders the node + its
        choices through the normal render_turn path). No-op guard: without a
        stashed source there is nowhere to return to -- say so in the status
        bar instead of silently doing nothing."""
        turn = self._controller.return_to_edit_source()
        if turn is None:
            self.statusBar().showMessage(
                "No enzyme to return to -- start or load a game.")
