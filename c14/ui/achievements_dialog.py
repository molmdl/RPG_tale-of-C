"""c14/ui/achievements_dialog.py -- the achievements board dialog (ACH-01/ACH-02 UI).

A read-only ``QDialog`` that renders the collection-based achievement board
from an :class:`c14.achievements.AchievementBoard` instance. The board (06-04)
owns unlock detection + JSON persistence; this dialog is the RENDERER -- it
reads ``board.data`` at construction time (the board is kept in sync by the
controller's ``on_turn`` calls, so opening the dialog shows the current state).

ACH-01 (collection-based, NOT a leaderboard): the dialog shows WHAT was found
-- characters tried (set), endings found (one entry per unique node_id, with
tier + character + date), branches discovered (count), and the fixed v1
achievement catalog (``ACHIEVEMENT_CATALOG_V1``) "filled in" by the player:
unlocked entries show name + description + date; locked entries show greyed
"Locked" placeholders. There are NO scores, ranks, or points anywhere
(06-RESEARCH-persistence-achievements.md Anti-Pattern). The summary line
counts the collections; it does NOT rank playthroughs.

ACH-02 (cross-session): the ``AchievementBoard`` was constructed at MainWindow
init (06-08) with the default ``user_data_path("achievements.json")`` path and
``_load()``s the persisted file -- so prior-session unlocks show automatically.
This dialog just reads ``board.data``; it does NO file I/O of its own and never
writes to the board.

Read-only: there are NO unlock buttons (unlocks happen via gameplay; the board
auto-detects + auto-persists via 06-04). The dialog never mutates the board.

Gate-EXEMPT: ``c14/ui/`` is in ``tools/check_imports.py`` SKIP_DIRS, so this
module MAY import ``pymol.Qt`` (and the pure-Python ``c14.achievements``
domain module -- which itself imports NO pymol/PyQt5, so the gate stays
clean). Importing this dialog in pure WSL python3.6 FAILS (no Qt installed)
-- that is EXPECTED; only ``python3.6 -m py_compile`` is WSL-verifiable here.
The functional board (unlocks show after playthroughs, persists across PyMOL
restarts) is human-verify in plan 06-14 (SC5).

Scope guard (06-RESEARCH-persistence-achievements.md "Don't scope DOC-01/DOC-02"):
this dialog owns ONLY the achievement board. DOC-01/DOC-02 (dramatic cast list +
slogan) are Phase 9 -- NOT scoped here (the cast is not populated yet).

Python 3.6 compatible: no f-strings (uses ``.format()``); plain class, no
``@dataclass`` (3.7+). Matches the ``HelpDialog`` (``c14/ui/help_dialog.py``)
conventions: ``QScrollArea`` wrapping a content widget + a Close button.
"""

from pymol.Qt import QtCore, QtGui, QtWidgets

from c14.achievements import ACHIEVEMENT_CATALOG_V1


def _date_only(iso_or_empty):
    """Render an ISO-8601 timestamp (``2026-08-29T12:00:00Z``) as its date
    part (``2026-08-29``) for compact display. Returns ``""`` for empty/None.
    Tolerant: if there is no ``T``, returns the whole string unchanged.
    """
    if not iso_or_empty:
        return ""
    return iso_or_empty.split("T", 1)[0]


class AchievementsDialog(QtWidgets.QDialog):
    """Read-only renderer for the collection-based achievement board.

    Constructs the dialog from ``achievement_board.data`` on init: a summary
    line (characters tried / endings found / branches discovered) + an
    "Unlocked" section (the fixed v1 catalog filled in -- unlocked entries show
    name + description + date; locked entries are greyed "Locked" placeholders)
    + an "Endings found" section (``Tier: node_id (character, date)``) + a
    "Characters tried" line + a Close button. The content is wrapped in a
    ``QScrollArea`` so the dialog never overflows the screen as the board grows
    in later phases.

    Args:
        achievement_board: the :class:`c14.achievements.AchievementBoard`
            instance owned by the controller/MainWindow. Its ``.data`` dict is
            read here (a live reference -- the snapshot reflects the board
            state at dialog-open time; the controller's ``on_turn`` calls keep
            the board current during gameplay, not while the dialog is open).
        parent: optional Qt parent.
    """

    def __init__(self, achievement_board, parent=None):
        super(AchievementsDialog, self).__init__(parent)
        self._board = achievement_board
        self.setWindowTitle("RPG: Tale of C — Achievements")
        self.setMinimumWidth(520)

        data = self._board.data
        characters_tried = data.get("characters_tried", [])
        endings_found = data.get("endings_found", [])
        branches_discovered = data.get("branches_discovered", [])
        achievements_unlocked = data.get("achievements_unlocked", [])

        # Inner content widget -- held inside a QScrollArea so the dialog
        # handles overflow gracefully (scrollbars appear only when needed).
        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # --- Header + summary line (ACH-01 collection counts, NOT scores) ---
        content_layout.addWidget(QtWidgets.QLabel("<b>Achievements</b>"))
        summary = (
            "Characters tried: {0}/3  |  Endings found: {1}  |  "
            "Branches discovered: {2}"
        ).format(
            len(characters_tried), len(endings_found), len(branches_discovered))
        summary_label = QtWidgets.QLabel(summary)
        summary_label.setWordWrap(True)
        content_layout.addWidget(summary_label)

        # --- Unlocked section (the fixed v1 catalog "filled in" -- ACH-01) ---
        # Cross-reference ACHIEVEMENT_CATALOG_V1 so the player sees the FULL
        # fixed catalog: unlocked entries show name + description + date;
        # not-yet-unlocked entries show greyed "Locked" placeholders (the
        # description is hidden -- no spoilers, a reason to seek the unlock).
        # This makes the "collection to fill in" framing visible (NOT a
        # ranking). Unlocked dates come from the achievements_unlocked entries
        # (read straight from board.data); the catalog supplies the stable
        # display order + the name/description text.
        unlocked_by_id = {a["id"]: a for a in achievements_unlocked}
        unlocked_count = len(unlocked_by_id)
        catalog_count = len(ACHIEVEMENT_CATALOG_V1)
        content_layout.addWidget(QtWidgets.QLabel(
            "<b>Unlocked</b> ({0} of {1})".format(unlocked_count, catalog_count)))
        if not ACHIEVEMENT_CATALOG_V1:
            none_label = QtWidgets.QLabel("None yet.")
            none_label.setStyleSheet("color: gray;")
            content_layout.addWidget(none_label)
        for aid, name, desc in ACHIEVEMENT_CATALOG_V1:
            entry = unlocked_by_id.get(aid)
            if entry is not None:
                line = "{0} — {1}  ({2})".format(
                    name, desc, _date_only(entry.get("date", "")))
                lbl = QtWidgets.QLabel(line)
            else:
                lbl = QtWidgets.QLabel("{0} — Locked".format(name))
                lbl.setStyleSheet("color: gray;")
            lbl.setWordWrap(True)
            content_layout.addWidget(lbl)

        # --- Endings found section (Tier: node_id (character, date)) ---
        content_layout.addWidget(QtWidgets.QLabel("<b>Endings found</b>"))
        if not endings_found:
            none_label = QtWidgets.QLabel("None yet.")
            none_label.setStyleSheet("color: gray;")
            content_layout.addWidget(none_label)
        for e in endings_found:
            tier = (e.get("tier") or "").capitalize()
            line = "{0}: {1} ({2}, {3})".format(
                tier,
                e.get("node_id", "?"),
                e.get("character") or "—",
                _date_only(e.get("date", "")))
            lbl = QtWidgets.QLabel(line)
            lbl.setWordWrap(True)
            content_layout.addWidget(lbl)

        # --- Characters tried section ---
        content_layout.addWidget(QtWidgets.QLabel("<b>Characters tried</b>"))
        if characters_tried:
            chars_label = QtWidgets.QLabel(", ".join(characters_tried))
        else:
            chars_label = QtWidgets.QLabel("None yet.")
            chars_label.setStyleSheet("color: gray;")
        chars_label.setWordWrap(True)
        content_layout.addWidget(chars_label)

        # --- Close (read-only dialog: no unlock buttons) ---
        close = QtWidgets.QPushButton("Close")
        close.clicked.connect(self.accept)
        content_layout.addWidget(close)

        # Wrap the content in a scroll area (frameless so it blends in).
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        outer = QtWidgets.QVBoxLayout(self)
        outer.addWidget(scroll)

        # Sensible initial size; the scroll area engages when content is tall.
        self.setMinimumHeight(360)
        self.resize(540, 480)
