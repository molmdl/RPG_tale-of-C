"""c14/ui/edit_dialog.py -- EditDialog (SC1 "edit interface"; EDIT-01/02/03 UI).

Gate-EXEMPT: ``c14/ui/`` is in ``tools/check_imports.py`` SKIP_DIRS, so this
module MAY import ``pymol.Qt``. Importing this dialog in pure WSL python3.6
FAILS (no Qt installed) -- that is EXPECTED; only ``python3.6 -m py_compile``
is WSL-verifiable here. The functional dialog (curated options render, a
selection builds an EditIntent whose signature routes via the EditRouter) is
human-verify in plan 06-14.

Curated, NOT free-form chemistry (PROJECT.md:80 -- "the game holds a curated
lookup table of known edits"; the chemistry-correctness engine is OUT OF
SCOPE). The dialog reads ``c14/data/edits.json`` for the current enzyme's
KNOWN edits (each entry has a ``signature`` dict {op, target, args} + a
``branch_node``) + offers them as the "correct fix" radio options, AND adds a
few plausible WRONG options (hardcoded for Phase 6 -- generic point mutations
using standard amino-acid codes, NOT fabricated disease mutations). The
player picks ONE radio option; the dialog returns the selected
``(op, target, args)`` tuple via :meth:`selected_edit`. NO free-form
residue-entry / free-form mutation-text -- that would produce EditIntents
whose :meth:`~c14.story.model.EditIntent.signature` matches nothing and
always routes to the bad-ending pool (a valid but unfun outcome; the curated
list makes the edit a meaningful choice).

The edit routing is the EditRouter's job (``c14/edit_router.py``), NOT the
dialog's. The dialog ONLY builds the ``(op, target, args)``; the controller
assembles the :class:`~c14.story.model.EditIntent` via
:meth:`~c14.ui.controller.Controller.build_edit_intent` and routes it via
:meth:`~c14.ui.controller.Controller.apply_edit` (which calls
``engine.apply_player_edit`` -> ``EditRouter.route``). Known edit (exact
signature match) -> the entry's ``branch_node``; unknown edit (no match) ->
the bad-ending pool (RngEngine-weighted, reproducible). The dialog does NOT
re-implement signature matching and does NOT call ``cmd.*`` (the routed
branch's ``on_enter`` MolAction("edit",...) applies the edit via molops).

WARNING 4 seam contract (3 parallel wave-4 plans, non-overlapping files):
This plan (06-09) owns ONLY ``c14/ui/edit_dialog.py``. It CONSUMES the seam
declared by 06-06 + 06-08; it does NOT modify their files:

- **06-06 (controller.py) provides**:
    * :meth:`Controller.request_edit(enzyme_id)` -- stashes
      ``self._pending_edit_enzyme_id`` + ``engine.goto("edit.prompt")``.
    * :attr:`Controller._pending_edit_enzyme_id` (the stash).
    * :meth:`Controller.build_edit_intent(op, target, args)` -- builds the
      EditIntent; reads ``enzyme_id`` from the current node's
      ``edit:enzyme:<id>`` tag, falling back to ``_pending_edit_enzyme_id`` at
      ``edit.prompt`` (which has no ``edit:enzyme:`` tag).
    * :meth:`Controller.apply_edit(edit_intent)` -- routes via
      ``engine.apply_player_edit`` + renders. (NOTE: 06-06's ``apply_edit``
      reads the enzyme_id from the CURRENT node's tag and raises RuntimeError
      when that node has no ``edit:enzyme:`` tag -- see the seam note in
      :meth:`EditDialog.submit`.)
- **06-08 (main_window.py) provides**: the ``render_turn`` detection of
  ``turn.node.id == "edit.prompt"`` -> opens ``EditDialog(controller,
  controller._pending_edit_enzyme_id, self)`` + on accept calls
  ``controller.build_edit_intent(...)`` + ``controller.apply_edit(intent)``
  (or calls :meth:`EditDialog.submit` which bundles those two).
- **06-09 (THIS plan) provides**: the :class:`EditDialog` class API --
  ``EditDialog(controller, enzyme_id, parent)`` + :meth:`selected_edit` ->
  ``(op, target, args)`` or None + the :meth:`EditDialog.submit` convenience.
  It does NOT reference or modify controller.py / main_window.py (consume the
  seam, don't edit the provider).

Phase 6 placeholder content: ``edits.json`` has 1 enzyme (``fixture_enzyme_1``)
with 1 known edit (point_mutation, ``resi 1`` -> ``GLY``). Phase 7 fills the
real per-enzyme entries (05.4-CONVENTION.md no-fabricated-science -- the wrong
options here are generic amino-acid codes, NOT real disease mutations; no
real PDB IDs in the edit options).

Python 3.6 compatible: no f-strings (uses ``.format()``); plain class, no
``@dataclass`` (3.7+). Matches the HelpDialog / AchievementsDialog conventions
(``from pymol.Qt import QtCore, QtGui, QtWidgets``).
"""
import json

from pymol.Qt import QtCore, QtGui, QtWidgets  # noqa: F401 (QtCore/QtGui kept for parity with repo convention)

import c14.paths


class EditDialog(QtWidgets.QDialog):
    """Curated edit-options dialog -> ``(op, target, args)`` for an EditIntent.

    The edit mechanic's UI surface (SC1 "edit interface" + the EDIT-01/02/03
    UI). The dialog offers a CURATED list of edit options per enzyme (read
    from ``c14/data/edits.json`` for the current ``enzyme_id`` + a few
    plausible wrong options hardcoded for Phase 6). The player picks ONE
    radio option; :meth:`selected_edit` returns the selected
    ``(op, target, args)`` tuple (or None if nothing was selected / the dialog
    was canceled). The controller assembles the EditIntent from that tuple
    via :meth:`~c14.ui.controller.Controller.build_edit_intent` and routes it
    via :meth:`~c14.ui.controller.Controller.apply_edit`.

    A known edit (its ``signature`` matches an ``edits.json`` entry) routes
    to the entry's ``branch_node``. A wrong option (no match) falls through
    to the bad-ending pool -- a valid game outcome (the host enzyme is made
    worse), but the curated list makes the edit a meaningful choice rather
    than a guaranteed failure.

    If the enzyme has NO known edits in ``edits.json`` yet (Phase 7 fills
    them), the dialog shows an informational message ("No known edits for
    this enzyme yet (Phase 7 content). Your edit will route to the bad-ending
    pool.") and offers a single generic wrong option so the player can still
    attempt an edit (which routes to the bad-ending pool -- a valid outcome).

    Args:
        controller: the :class:`~c14.ui.controller.Controller` instance. Held
            for the :meth:`submit` convenience (which calls
            ``controller.build_edit_intent`` + ``controller.apply_edit``). The
            dialog itself does NOT call the controller; it only reads
            ``edits.json``.
        enzyme_id: the enzyme/substrate context id (e.g. ``fixture_enzyme_1``
            for the Phase 6 placeholder). Selects which enzyme's known edits
            to load from ``edits.json``.
        parent: optional Qt parent.
    """

    def __init__(self, controller, enzyme_id, parent=None):
        super(EditDialog, self).__init__(parent)
        self._controller = controller
        self._enzyme_id = enzyme_id
        self.setWindowTitle("RPG: Tale of C \u2014 Edit")
        self.setMinimumWidth(420)

        # Load the curated options: known edits (from edits.json) + a few
        # plausible wrong options (hardcoded for Phase 6). ``_options`` is a
        # list of (label, op, target, args) tuples; ``_selected`` holds the
        # checked radio's FULL option tuple on OK (selected_edit() strips the
        # display-only label -> the documented (op, target, args) 3-tuple).
        self._options, has_known = self._build_options(enzyme_id)
        self._selected = None

        layout = QtWidgets.QVBoxLayout(self)
        # Header: "Edit <enzyme_id>".
        layout.addWidget(QtWidgets.QLabel("Edit {0}".format(enzyme_id)))

        # If the enzyme has NO known edits, show an informational message
        # (Phase 7 fills them; the player's edit routes to the bad-ending pool
        # -- a valid outcome).
        if not has_known:
            msg = QtWidgets.QLabel(
                "No known edits for this enzyme yet (Phase 7 content). "
                "Your edit will route to the bad-ending pool.")
            msg.setWordWrap(True)
            msg.setStyleSheet("color: gray;")
            layout.addWidget(msg)

        # One QRadioButton per curated option, grouped in a QButtonGroup so
        # ``checkedId()`` returns the option index (the id assigned via
        # addButton(radio, idx)). Radio buttons are mutually exclusive (the
        # QButtonGroup default in exclusive mode).
        self._button_group = QtWidgets.QButtonGroup(self)
        for idx, (label, _op, _target, _args) in enumerate(self._options):
            radio = QtWidgets.QRadioButton(label)
            self._button_group.addButton(radio, idx)
            layout.addWidget(radio)
        # Default-select the first option (if any) so the player can just
        # click OK without first picking a radio.
        if self._options:
            first_radio = self._button_group.button(0)
            if first_radio is not None:
                first_radio.setChecked(True)

        # OK / Cancel. accepted -> _on_accept (records the selection + accepts
        # the dialog so exec_() returns Accepted); rejected -> reject (exec_()
        # returns Rejected, _selected stays None).
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    # ---- public API ----

    def selected_edit(self):
        # type: () -> object
        """Return the selected ``(op, target, args)`` tuple, or None.

        Returns None if the dialog was canceled or no option was selected.
        The caller (the 06-08 MainWindow, or :meth:`submit`) passes the three
        elements to :meth:`Controller.build_edit_intent` to assemble the
        EditIntent whose :meth:`~c14.story.model.EditIntent.signature` is
        matched against ``edits.json`` by the EditRouter.

        Contract note (06-14 SC2f fix): ``_on_accept`` stores the FULL
        ``(label, op, target, args)`` option tuple in ``_selected`` (the label
        is display-only); THIS method strips the label and returns the
        3-tuple ``(op, target, args)`` -- the documented contract consumed by
        ``main_window.py`` (``op, target, args = dlg.selected_edit()``) and
        :meth:`submit`.
        """
        if self._selected is None:
            return None
        return self._selected[1:]

    @staticmethod
    def submit(controller, enzyme_id, parent=None):
        # type: (object, str, object) -> object
        """Open the dialog + on accept build the EditIntent + apply it.

        Convenience bundling the declared seam (06-08 may call this OR inline
        the same three calls). Flow:

        1. ``dialog = EditDialog(controller, enzyme_id, parent)``.
        2. ``dialog.exec_()`` -- modal; returns ``Accepted`` if the player
           clicked OK.
        3. On accept: ``op, target, args = dialog.selected_edit()``.
        4. ``intent = controller.build_edit_intent(op, target, args)`` -- the
           controller reads the ``enzyme_id`` from the current node's
           ``edit:enzyme:<id>`` tag (falling back to the stashed
           ``_pending_edit_enzyme_id`` at ``edit.prompt``, set by
           :meth:`Controller.request_edit` at the edit-allowed source node).
        5. ``controller.apply_edit(intent)`` -- routes via the EditRouter
           (known -> branch node; unknown -> bad-ending pool) + renders the
           resulting TurnResult. Returns the TurnResult.

        Returns the TurnResult from ``apply_edit`` on accept, or None if the
        dialog was canceled / no option was selected.

        Seam note (Warning 4): 06-06's ``Controller.apply_edit`` reads the
        enzyme_id from the CURRENT node's ``edit:enzyme:<id>`` tag and raises
        ``RuntimeError`` when that node has no such tag (e.g. at
        ``edit.prompt``). The 06-08 seam calls ``build_edit_intent`` (which
        falls back to the stash at edit.prompt) + ``apply_edit`` at
        ``edit.prompt``; for ``apply_edit`` to succeed there, 06-06's
        ``apply_edit`` must also fall back to ``_pending_edit_enzyme_id`` (or
        use ``edit_intent.enzyme_id``). That fix is in 06-06's file
        (controller.py) -- OUT OF SCOPE for 06-09 (this plan owns only
        edit_dialog.py per Warning 4 file ownership). This helper calls the
        declared seam verbatim; the integration is verified in 06-14.
        """
        dialog = EditDialog(controller, enzyme_id, parent=parent)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            selected = dialog.selected_edit()
            if selected is not None:
                op, target, args = selected
                intent = controller.build_edit_intent(op, target, args)
                return controller.apply_edit(intent)
        return None

    # ---- internals ----

    def _on_accept(self):
        # type: () -> None
        """Record the checked option's FULL (label, op, target, args) tuple +
        accept the dialog (so ``exec_()`` returns Accepted). If no radio is
        checked (``checkedId()`` returns -1), ``_selected`` stays None and the
        dialog still accepts (the caller sees a None selection via
        :meth:`selected_edit`)."""
        idx = self._button_group.checkedId()
        if 0 <= idx < len(self._options):
            self._selected = self._options[idx]
        self.accept()

    def _build_options(self, enzyme_id):
        # type: (str) -> tuple
        """Load ``edits.json`` + build the curated ``(label, op, target, args)``
        options list for ``enzyme_id``.

        Returns ``(options, has_known)`` where ``has_known`` is True iff the
        enzyme has >=1 known edit in ``edits.json`` (drives the "no known
        edits" informational message).

        - Known edits are labeled "Restore <target> to <new_res> (the correct
          fix)" (point_mutation) / analogous for substrate_edit /
          protonation_change. Their ``(op, target, args)`` is read straight
          from the entry's ``signature`` dict so the built EditIntent's
          ``signature()`` EXACTLY matches the table (known -> branch).
        - A few plausible WRONG options (hardcoded for Phase 6 -- generic
          point mutations with standard amino-acid codes, NOT fabricated
          disease mutations) are added alongside the known edit(s). Their
          ``(op, target, args)`` does NOT match the table -> bad-ending pool
          (a valid game outcome).
        - If the enzyme has NO known edits (Phase 7 fills them), a single
          generic wrong option is offered (routes to the bad-ending pool).
        """
        # Load edits.json cwd-independent via c14.paths.data_path (the
        # __file__-relative resolver; Pitfall 1 mitigation -- the plugin may
        # be run from any CWD when unzipped into PyMOL's startup/ dir).
        edits_path = str(c14.paths.data_path("data", "edits.json"))
        with open(edits_path, "r", encoding="utf-8") as fh:
            table = json.load(fh)
        enzyme = table.get("enzymes", {}).get(enzyme_id)
        known = (enzyme or {}).get("edits", []) or []
        has_known = bool(known)

        options = []  # type: list
        # Known edits (the "correct fix" -- matches the table -> branch).
        for entry in known:
            sig = entry.get("signature", {}) or {}
            op = sig.get("op")
            target = sig.get("target")
            args = dict(sig.get("args", {}) or {})
            label = self._label_for_known(op, target, args)
            options.append((label, op, target, args))

        if has_known:
            # A few plausible wrong options alongside the known edit(s).
            # Hardcoded for Phase 6; generic amino-acid codes (NOT fabricated
            # disease mutations). These do NOT match the table -> bad pool.
            for wrong in self._plausible_wrong_options():
                options.append(wrong)
        else:
            # No known edits (Phase 7 fills them): a single generic wrong
            # option so the player can still attempt an edit (-> bad pool).
            options.append(self._generic_wrong_option())
        return options, has_known

    @staticmethod
    def _label_for_known(op, target, args):
        # type: (str, str, dict) -> str
        """Build a human-readable label for a known edit (the "correct fix").

        Per-op phrasing (EDIT-01/02/03). For Phase 6 only ``point_mutation``
        is used (fixture_enzyme_1); the substrate_edit / protonation_change
        branches are forward-compatible for Phase 7.
        """
        if op == "point_mutation":
            new_res = args.get("new_res", "?")
            return "Restore {0} to {1} (the correct fix)".format(target, new_res)
        if op == "substrate_edit":
            group = args.get("group", "?")
            action = args.get("action", "?")
            return "{0} {1} to the substrate (the correct fix)".format(action, group)
        if op == "protonation_change":
            resn = args.get("resn", "?")
            return "Change protonation to {0} (the correct fix)".format(resn)
        # Fallback (a future op type): a generic phrasing.
        return "{0} {1} {2} (the correct fix)".format(op, target, args)

    @staticmethod
    def _plausible_wrong_options():
        # type: () -> list
        """Return a few plausible WRONG edit options for Phase 6.

        Hardcoded generic point mutations using standard amino-acid codes
        (ALA = alanine, GLY = glycine). These are gameplay options -- the
        player ATTEMPTS an edit -- NOT scientific claims: they are NOT labeled
        as real disease mutations, and their effect is routing to the
        bad-ending pool ("your edit didn't restore the enzyme"). They do NOT
        match ``edits.json`` (different target / args than the known entry),
        so the EditRouter routes them to the bad-ending pool (a valid game
        outcome). No fabricated science (05.4-CONVENTION.md no-fabricated-
        science; no real PDB IDs; standard AA codes only).
        """
        return [
            ("Change resi 1 to ALA", "point_mutation", "resi 1", {"new_res": "ALA"}),
            ("Change resi 2 to GLY", "point_mutation", "resi 2", {"new_res": "GLY"}),
        ]

    @staticmethod
    def _generic_wrong_option():
        # type: () -> tuple
        """Return a single generic wrong option for an enzyme with NO known
        edits (Phase 7 fills them). Routes to the bad-ending pool (a valid
        outcome) -- the player can still attempt an edit."""
        return ("Attempt a point mutation (resi 1 to ALA)",
                "point_mutation", "resi 1", {"new_res": "ALA"})
