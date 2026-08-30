# rpg/ui/widgets.py -- Phase 6 Plan 06-08 the StoryPanel + ChoicePanel widgets.
#
# The rendering primitives the MainWindow (06-08 main_window.py) composes into
# SC1's "story text + choice panel" central surface. Both are DUMB RENDERERS:
# they render a Node / TurnResult into QtWidgets + emit button.clicked signals
# that route to the controller (06-06). They do NO domain work themselves:
#
#   * NO cmd.* calls (the controller + molops own molecular ops -- 06-RESEARCH
#     Anti-Pattern "UI doing domain work").
#   * NO condition re-evaluation (delegated to controller._engine.choice_cond_met
#     so the panel's eligibility filter EXACTLY matches the engine's pick_choice
#     filter -- both call interpreter._cond).
#   * NO weighted-pick logic (the engine's choose handles the RNG; the panel
#     just calls controller.choose(0) for a "Spin the wheel" button).
#   * NO QMessageBox (the controller's injected prompt_fn owns the OQ-6 gate;
#     the panel is dumb).
#
# StoryPanel (06-RESEARCH Pattern 4): text_dramatic (prominent, 14pt) STACKED
# above text_teaching (dimmed, 10pt gray) -- not tabbed, so both layers show at
# once (the educator audience benefits from simultaneous view). An ending banner
# ("Ending reached: <tier>") shows above the text when render_ending is called.
# Plain text + bold; no markdown (PROJECT.md "UI simple").
#
# ChoicePanel (06-RESEARCH Pattern 5 + the tca.shuffle mixed-node UI): one
# QPushButton per eligible Choice for a pure-MC node; for a mixed weighted +
# non-weighted node (tca.shuffle, detected via controller.is_mixed_weighted_node)
# it renders a "Spin the wheel" button (-> controller.choose -- the RNG picks
# among the weighted) + separate Edit (-> controller.request_edit) / conditional
# (-> controller.take_choice) buttons for the non-weighted choices. This is the
# SC#3 Blocker B UI side (06-06 controller's is_mixed_weighted_node + goto handle
# routing; this panel only renders + emits signals).
#
# Gate-EXEMPT: rpg/ui/ is in tools/check_imports.py SKIP_DIRS, so this module
# MAY import pymol.Qt (matches Pymol-script-repo/plugins/dynoplot.py:21 + the
# sibling dialogs achievements_dialog.py / help_dialog.py). Importing this
# module in pure WSL python3.6 FAILS (no Qt installed) -- that is EXPECTED
# (06-RESEARCH-ui-adapter.md Pitfall 1); only `python3.6 -m py_compile` is
# WSL-verifiable here. The functional widgets (story renders, choices clickable,
# tca.shuffle Spin/Edit/cycle-trap) are human-verify in plan 06-14.
#
# PYTHON 3.6 ONLY: plain classes, .format() strings, NO f-strings / @dataclass
# / walrus (matches the repo precedent; 3.6.9 has no dataclasses module). The
# late-binding closure bug is avoided via default-arg capture
# (`lambda _=False, c=choice: ...`) matching help_dialog.py:85-87 (the `_`
# receives the QPushButton.clicked bool signal; the captured vars are the
# default args, never overwritten by the signal arg).
"""rpg/ui/widgets.py -- StoryPanel + ChoicePanel (the rendering primitives).

Dumb renderers over the 06-06 Controller's TurnResult API. StoryPanel stacks
text_dramatic (prominent) + text_teaching (dimmed) + an optional ending banner.
ChoicePanel renders one button per eligible Choice (pure-MC), a "Spin the
wheel" button + Edit/conditional buttons (the tca.shuffle mixed-node case), or a
"Start a new game" button (at an ending). Button clicks route to
``controller.choose`` / ``take_choice`` / ``request_edit``; the panel never
calls cmd.*, never re-evaluates conditions, never re-implements the RNG pick.

Gate-EXEMPT (rpg/ui/). py_compile is the only WSL-verifiable check; the
functional UI is human-verify in 06-14.
"""

from pymol.Qt import QtCore, QtGui, QtWidgets


class StoryPanel(QtWidgets.QWidget):
    """Two-layer story text renderer (06-RESEARCH Pattern 4).

    ``text_dramatic`` (prominent, 14pt) is stacked above ``text_teaching``
    (dimmed, 10pt gray) -- NOT tabbed, so both layers show at once (the educator
    audience benefits from the simultaneous view). An optional ending banner
    ("Ending reached: <tier>") shows above the text when :meth:`render_ending`
    is called. Plain text; no markdown rendering (PROJECT.md "UI simple").

    The teaching label is wrapped in a ``QScrollArea`` so long teaching text
    does not overflow the window (scrollbars appear only when needed). The
    dramatic label is short scene prose and needs no scroll.
    """

    def __init__(self, parent=None):
        super(StoryPanel, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        # Ending banner -- hidden unless render_ending shows it. Bold + a warm
        # gold so an ending reads as a milestone (not an error).
        self._banner = QtWidgets.QLabel("")
        self._banner.setWordWrap(True)
        self._banner.setStyleSheet(
            "font-size: 12pt; font-weight: bold; color: #b8860b;")
        self._banner.hide()
        layout.addWidget(self._banner)
        # Dramatic text (prominent).
        self._dramatic = QtWidgets.QLabel("")
        self._dramatic.setWordWrap(True)
        self._dramatic.setStyleSheet("font-size: 14pt;")
        layout.addWidget(self._dramatic)
        # Teaching text (dimmed), wrapped in a scroll area so long text does
        # not overflow. The scroll area owns the label (setWidget); the label
        # is NOT added to the layout directly (a widget has one parent).
        self._teaching = QtWidgets.QLabel("")
        self._teaching.setWordWrap(True)
        self._teaching.setStyleSheet("font-size: 10pt; color: gray;")
        teaching_scroll = QtWidgets.QScrollArea()
        teaching_scroll.setWidget(self._teaching)
        teaching_scroll.setWidgetResizable(True)
        teaching_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        layout.addWidget(teaching_scroll, 1)  # stretch=1: teaching takes the
        #                                      remaining vertical space.

    def render_node(self, node):
        """Populate the dramatic + teaching labels from a Node.

        As its FIRST action, blanks + hides the ending banner: every
        non-ending render (New Game / Load / a normal advance) clears a
        stale "Ending reached: <tier>" banner left by a previous ending
        (S1 bad-end-persistence root cause 1 -- 06-14 re-verify round 3,
        .planning/debug/bad-end-restart-and-edit-pool.md: only clear()
        hid the banner before, and the MainWindow never calls clear()).
        :meth:`render_ending` re-shows the banner AFTER this reset.

        Handles None/empty gracefully: an empty ``text_dramatic`` (the skeleton
        ships TBD text on many nodes) shows a placeholder so the panel never
        looks broken. ``text_teaching`` empty -> blank (no placeholder; the
        teaching layer is optional per node).
        """
        # Reset the ending banner FIRST (see docstring): setText("") + hide()
        # use the same attribute (self._banner) as render_ending/clear.
        self._banner.setText("")
        self._banner.hide()
        dramatic = getattr(node, "text_dramatic", "") or ""
        if not dramatic.strip():
            dramatic = "(This scene's story text is being written -- TBD.)"
        self._dramatic.setText(dramatic)
        self._teaching.setText(getattr(node, "text_teaching", "") or "")

    def render_ending(self, node):
        """Show an 'Ending reached: <tier>' banner (tier capitalized) above the
        node text, then populate the dramatic/teaching labels via render_node.

        Reuses :meth:`render_node` for the text so an ending node's
        text_dramatic/text_teaching still render (endings carry their own
        dramatic + teaching text per the 5.1 skeleton).

        ORDER NOTE (06-14 re-verify round 3): render_node now resets the
        banner as its first action, so the set+show here runs AFTER the
        render_node call -- same final widget state as before (banner shown
        with the tier text + node text rendered), but the ending banner is no
        longer immediately re-hidden by the delegated render_node reset.
        """
        tier = (getattr(node, "is_ending", None) or "").capitalize()
        self.render_node(node)
        self._banner.setText("Ending reached: {0}".format(tier))
        self._banner.show()

    def clear(self):
        """Reset all labels + hide the ending banner."""
        self._banner.setText("")
        self._banner.hide()
        self._dramatic.setText("")
        self._teaching.setText("")


class ChoicePanel(QtWidgets.QWidget):
    """Renders the eligible Choices for the current turn as QPushButtons.

    A dumb renderer: button clicks route to ``controller.choose`` (pure-MC +
    weighted RNG spin), ``controller.take_choice`` (non-weighted at a mixed
    node -- the cycle-trap), or ``controller.request_edit`` (the edit:offer at a
    mixed node). The panel NEVER calls cmd.* and NEVER re-evaluates conditions
    (it delegates to ``controller._engine.choice_cond_met`` so its eligibility
    filter EXACTLY matches the engine's ``pick_choice`` filter -- both call
    ``interpreter._cond``; the index passed to ``choose`` therefore maps 1:1 to
    the engine's eligible list).

    Three rendering modes (selected in :meth:`render_turn`):

    1. **Ending** (``node.is_ending is not None``): no choice buttons; show an
       "Ending reached: <tier>" label + a "Start a new game" button that emits
       :attr:`new_game_requested` (the MainWindow connects this to its
       StartDialog re-open).
    2. **Mixed weighted + non-weighted** (``controller.is_mixed_weighted_node``
       is True -- the tca.shuffle case): a "Spin the wheel" button
       (-> ``controller.choose(0)``, the RNG picks among the weighted) + one
       button per NON-weighted choice. The edit:offer button routes to
       ``controller.request_edit(controller._current_enzyme_id())`` (06-06 stashes
       the enzyme_id + gotos edit.prompt; the MainWindow's render_turn then
       detects ``turn.node.id == "edit.prompt"`` + opens the EditDialog). Other
       non-weighted buttons (the cycle-trap) route to
       ``controller.take_choice(choice)`` and are DISABLED when their cond is
       not met (greyed out -- the plan: "grey out the cycle-trap until visits >
       5"). The cycle-trap button is shown greyed-out BEFORE its cond is met so
       the player sees something will unlock after enough visits.
    3. **Pure-MC / pure-weighted**: one button per eligible choice for pure-MC
       (-> ``controller.choose(index)``; an edit affordance choice -- the
       dual predicate ``edit:offer`` tag OR ``goto == "edit.prompt"``,
       matching the graph invariant test -- routes to
       ``controller.request_edit`` instead, the SC2f round-2 fix); for
       pure-weighted a single "Spin the wheel" button
       (-> ``controller.choose(0)``) + an info label listing the
       possible outcomes with a "(luck decides)" note. Cond-unmet choices are
       disabled.
    """

    # Emitted by the "Start a new game" button at an ending. The MainWindow
    # connects this to its _new_game handler (re-opens the StartDialog). Keeps
    # the panel decoupled from the MainWindow (no parent back-reference).
    new_game_requested = QtCore.Signal()

    def __init__(self, controller, parent=None):
        super(ChoicePanel, self).__init__(parent)
        self._controller = controller
        self._layout = QtWidgets.QVBoxLayout(self)
        self._buttons = []  # live QPushButtons/QLabels (for clear() via deleteLater)
        # Info label for the pure-weighted "(luck decides)" note + the
        # "No choices available." fallback. Persists across renders (not cleared
        # by clear() -- set fresh each render_turn).
        self._info = QtWidgets.QLabel("")
        self._info.setWordWrap(True)
        self._info.setStyleSheet("color: gray;")
        self._layout.addWidget(self._info)
        # Trailing stretch so buttons pack at the top (not centered/expanded).
        self._layout.addStretch(1)

    # ------------------------------------------------------------------
    # PUBLIC: called by MainWindow.render_turn
    # ------------------------------------------------------------------
    def render_turn(self, turn, controller):
        """Render the choices for ``turn`` using ``controller``.

        ``turn.node`` is the current Node; ``controller`` is the 06-06
        Controller (passed in explicitly so the panel can be re-bound if the
        controller is swapped, mirroring the plan's ``render_turn(self, turn,
        controller)`` signature). Clears any prior buttons first.
        """
        self.clear()
        node = turn.node
        if getattr(node, "is_ending", None) is not None:
            self._render_ending(node)
            return
        if controller.is_mixed_weighted_node(node):
            self._render_mixed(node, controller)
        else:
            self._render_pure(node, controller)

    def clear(self):
        """Remove all rendered buttons/labels (deleteLater for safe Qt teardown).
        Leaves the persistent info label + the trailing stretch in place."""
        for b in self._buttons:
            b.deleteLater()
        self._buttons = []
        self._info.setText("")

    def render_single_action(self, label, callback):
        """Render ONE action button wired to ``callback`` (B2 anti-stranding
        seam, 06-14 re-verify round 2).

        Used by the MainWindow after an EditDialog CANCEL at ``edit.prompt``:
        the player is on a node with no player-facing choices, so instead of
        an empty choice panel a single "Return to the enzyme" button is shown
        (the skeleton is FROZEN -- no return node/edge could be added). The
        panel stays a DUMB renderer: it clears prior buttons + renders the
        button; the ``callback`` (owned by the MainWindow) performs the
        controller call (``controller.return_to_edit_source()``)."""
        self.clear()
        btn = QtWidgets.QPushButton(label)
        # `_=False` receives the clicked bool signal (default-arg capture --
        # no closure over loop vars here; callback is a single bound callable).
        btn.clicked.connect(lambda _=False: callback())
        self._add_widget(btn)

    # ------------------------------------------------------------------
    # INTERNAL: the three rendering modes
    # ------------------------------------------------------------------
    def _render_ending(self, node):
        """Ending: an 'Ending reached: <tier>' label + a 'Start a new game'
        button (emits new_game_requested). No choice buttons."""
        tier = (node.is_ending or "").capitalize()
        lbl = QtWidgets.QLabel("Ending reached: {0}".format(tier))
        lbl.setStyleSheet("font-weight: bold;")
        self._add_widget(lbl)
        btn = QtWidgets.QPushButton("Start a new game")
        # `_=False` receives the clicked bool signal; the button just emits the
        # new_game_requested signal (no closure capture needed).
        btn.clicked.connect(lambda _=False: self.new_game_requested.emit())
        self._add_widget(btn)

    def _render_mixed(self, node, controller):
        """Mixed weighted + non-weighted (tca.shuffle): a 'Spin the wheel'
        button (RNG picks among the weighted) + one button per NON-weighted
        choice (edit:offer -> request_edit; cycle-trap/other -> take_choice).

        NOTE (user decision 1, 2026-08-30): the tca.shuffle node AUTO-RESOLVES
        in the controller BEFORE any render (controller._auto_resolve_shuffle:
        trap auto-fires at visits>5 / the aconitase edit is offered once on
        the first entry / otherwise the wheel auto-spins), so this mixed mode
        NO LONGER renders for the shuffle in practice (dead-for-shuffle). It
        is KEPT: is_mixed_weighted_node stays for any future mixed
        weighted+non-weighted node, and a defensive shuffle render (e.g. a
        re-entrant _render call during resolution) still works.

        The non-weighted buttons are iterated over ALL non-weighted choices
        (not just cond-eligible) so a cond-gated cycle-trap shows greyed-out
        before its cond is met (the plan: 'grey out the cycle-trap until visits
        > 5'). Eligible non-weighted buttons are enabled; cond-unmet are
        disabled with a 'Not yet available.' tooltip.
        """
        # "Spin the wheel" -> RNG picks among the weighted (choose(0); the
        # engine's pick_choice returns a single weighted Choice when weighted
        # is non-empty, so the index is ignored).
        spin = QtWidgets.QPushButton("Spin the wheel")
        spin.setToolTip("Let fate decide which way the cycle turns (RNG).")
        spin.clicked.connect(lambda _=False: controller.choose(0))
        self._add_widget(spin)
        # Non-weighted choices (ALL of them, not just eligible -- see docstring).
        non_weighted = [c for c in node.choices if c.weight is None]
        for choice in non_weighted:
            btn = QtWidgets.QPushButton(choice.label)
            met = controller._engine.choice_cond_met(choice)
            btn.setEnabled(met)
            tags = getattr(choice, "tags", None) or []
            if "edit:offer" in tags:
                # edit:offer -> request_edit(current enzyme_id). The enzyme_id
                # is read from the CURRENT node's edit:enzyme:<id> tag at click
                # time (06-06 _current_enzyme_id); request_edit stashes it +
                # gotos edit.prompt so the MainWindow's render_turn can open the
                # EditDialog with the right enzyme. Do NOT call take_choice for
                # edit:offer -- request_edit bundles the stash + the goto.
                btn.clicked.connect(
                    lambda _=False:
                    controller.request_edit(controller._current_enzyme_id()))
            else:
                # cycle-trap / other cond-gated non-weighted -> take_choice
                # (engine.goto, NOT choose -- choose would RNG-pick weighted).
                btn.clicked.connect(
                    lambda _=False, c=choice: controller.take_choice(c))
            if not met:
                btn.setToolTip("Not yet available.")
            self._add_widget(btn)

    def _render_pure(self, node, controller):
        """Pure-MC or pure-weighted: one button per eligible choice (pure-MC,
        -> choose(index)) or a single 'Spin the wheel' + an info label
        (pure-weighted, -> choose(0); the RNG picks). Cond-unmet choices are
        disabled."""
        eligible = [c for c in node.choices
                    if controller._engine.choice_cond_met(c)]
        weighted = [c for c in eligible if c.weight is not None]
        if weighted:
            # Pure-weighted: the RNG picks among ALL eligible (all weighted).
            # Show the possible outcomes with a "(luck decides)" note + a
            # single Spin button (multiple buttons doing the same RNG pick
            # would be confusing UX -- one Spin is clearer).
            labels = ", ".join(c.label for c in weighted)
            self._info.setText(
                "Possible outcomes (luck decides): {0}".format(labels))
            spin = QtWidgets.QPushButton("Spin the wheel")
            spin.setToolTip("Let fate decide (RNG).")
            spin.clicked.connect(lambda _=False: controller.choose(0))
            self._add_widget(spin)
        else:
            # Pure-MC: one button per eligible choice -> choose(index). The
            # index is the position in `eligible`, which EXACTLY matches the
            # engine's pick_choice eligible list (both filter via _cond), so
            # choose(index) picks the right choice.
            for index, choice in enumerate(eligible):
                tags = getattr(choice, "tags", None) or []
                # SC2f round-2 fix (06-14 re-verify): an edit affordance on a
                # PURE-MC node must route through request_edit, NOT the generic
                # choose(i). Dual predicate (matches
                # tests/test_glucose_reachability.py's edit-offer invariant:
                # the choice carries the 'edit:offer' tag OR its goto IS
                # edit.prompt). The seam was originally designed for the only
                # then-existing edit node (the MIXED tca.shuffle, handled in
                # _render_mixed); the Phase 5.1 replan added edit:offer
                # choices to 13 pure-MC enzyme nodes without extending this
                # loop, so the edit button advanced via choose() ->
                # edit.prompt with the enzyme stash never set ->
                # build_edit_intent RuntimeError. Mirrors _render_mixed's
                # edit:offer handling verbatim: request_edit stashes the
                # enzyme_id (read from THIS node's edit:enzyme:<id> tag at
                # click time) + gotos edit.prompt; the MainWindow's
                # render_turn then opens the EditDialog.
                if ("edit:offer" in tags
                        or choice.goto == "edit.prompt"):
                    btn = QtWidgets.QPushButton(choice.label)
                    btn.clicked.connect(
                        lambda _=False:
                        controller.request_edit(
                            controller._current_enzyme_id()))
                else:
                    btn = QtWidgets.QPushButton(choice.label)
                    btn.clicked.connect(
                        lambda _=False, i=index: controller.choose(i))
                self._add_widget(btn)
        if not eligible:
            self._info.setText("No choices available.")

    # ------------------------------------------------------------------
    # INTERNAL: insert a widget above the trailing stretch + track it for
    # clear(). The trailing stretch is the LAST item (addStretch in __init__);
    # insertWidget(count-1) puts new widgets just above it.
    # ------------------------------------------------------------------
    def _add_widget(self, widget):
        self._buttons.append(widget)
        self._layout.insertWidget(self._layout.count() - 1, widget)
