"""c14/ui/help_dialog.py -- in-game help dialog (DOC-03).

Renders the curated help content from ``c14/data/help.json``: the editing
pointers (point mutation / substrate edit / protonation change / restore
safety net -- the Phase 4 EDIT-01/02/03/05 mechanics in plain language) as
rich-text QLabels, and the small curated list of PyMOL wiki links as
QPushButtons that open the user's default browser via
``QtGui.QDesktopServices.openUrl`` (the Qt way -- cross-platform inside
PyMOL; never ``os.system``/``webbrowser``).

The help text is READ from help.json (not hardcoded) so it is editable
without touching Python (06-RESEARCH-persistence-achievements.md Pattern 6).
help.json carries only webfetch-verified wiki links (no fabricated URLs -- the
3 links were verified live 2026-08-29 and re-confirmed 2026-08-30 in plan
06-13).

Gate-EXEMPT: ``c14/ui/`` is in ``tools/check_imports.py`` SKIP_DIRS, so this
module MAY import ``pymol.Qt``. Importing this module in pure WSL python3.6
FAILS (no Qt installed) -- that is EXPECTED; only ``python3.6 -m py_compile``
is WSL-verifiable here. The functional dialog (pointers render, wiki links
open in the browser) is human-verify in plan 06-14.

Scope guard (06-RESEARCH-persistence-achievements.md Pattern 6): this dialog
owns ONLY DOC-03 (editing pointers + wiki links). DOC-01/DOC-02 (dramatic cast
list + slogan) are Phase 9 -- NOT scoped here (the cast is not populated yet).

Python 3.6 compatible: no f-strings (uses ``.format()``). The wiki-link
``lambda`` captures the URL via a default arg (``u=link["url"]``) to avoid
the late-binding closure bug; ``_`` is the ``clicked()`` bool signal arg.
"""
import json

from pymol.Qt import QtCore, QtGui, QtWidgets

import c14.paths


class HelpDialog(QtWidgets.QDialog):
    """In-game help dialog rendering ``c14/data/help.json``.

    Constructs the dialog from help.json on init: a "Molecule editing" section
    (one rich-text QLabel per editing pointer) + a "PyMOL wiki references"
    section (one QPushButton per wiki link, opening the user's browser via
    ``QtGui.QDesktopServices.openUrl``) + a Close button. The content is
    wrapped in a ``QScrollArea`` so the dialog never overflows the screen when
    the help text grows in later phases.
    """

    def __init__(self, parent=None):
        super(HelpDialog, self).__init__(parent)
        self.setWindowTitle("RPG: Tale of C — Help")
        self.setMinimumWidth(520)

        # Load curated help content from the bundled data file (cwd-independent
        # via c14.paths.data_path -- __file__-relative, Pitfall 1 mitigation).
        help_path = str(c14.paths.data_path("data", "help.json"))
        with open(help_path, "r", encoding="utf-8") as fh:
            self.data = json.load(fh)

        # Inner content widget -- held inside a QScrollArea so the dialog
        # handles overflow gracefully (scrollbars appear only when needed).
        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # --- Editing pointers (DOC-03 part 1) ---
        content_layout.addWidget(
            QtWidgets.QLabel("<b>Molecule editing</b>"))
        for pointer in self.data["editing_pointers"]:
            label = QtWidgets.QLabel(
                "<b>{0}</b><br/>{1}".format(pointer["title"], pointer["body"]))
            # Rich-text QLabel; word-wrap so long bodies don't run off the edge.
            label.setWordWrap(True)
            content_layout.addWidget(label)

        # --- PyMOL wiki references (DOC-03 part 2) ---
        content_layout.addWidget(
            QtWidgets.QLabel("<b>PyMOL wiki references</b>"))
        for link in self.data["wiki_links"]:
            btn = QtWidgets.QPushButton(link["label"])
            # Default-arg capture (`u=link["url"]`) avoids the late-binding
            # closure bug: each button remembers its own URL. `_` receives the
            # clicked() bool signal (unused). openUrl is the Qt way to launch
            # the user's default browser -- works cross-platform inside PyMOL.
            btn.clicked.connect(
                lambda _=False, u=link["url"]:
                QtGui.QDesktopServices.openUrl(QtCore.QUrl(u)))
            btn.setToolTip(link["note"])
            content_layout.addWidget(btn)

        # --- Close ---
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
