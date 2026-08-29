"""c14/ui/save_load_dialogs.py -- thin QFileDialog wrappers -> controller.save/load.

Implements SAVE-01/02 UI + SC#3 ("a save mid-game and load restores the exact
session"). These are THIN wrappers: they collect a save-file path via
``QtWidgets.QFileDialog`` and return it (or ``None`` on cancel). The
MainWindow (06-08) wires them::

    # Save button
    path = ask_save_path(self)
    if path:
        self._controller.save(path)   # -> engine.save -> SaveStore (JSON, no .pse)
    # Load button
    path = ask_load_path(self)
    if path:
        self._controller.load(path)   # -> engine.load -> on_enter replay + set_view

The engine (06-03 view injection + Phase 2 on_enter replay) does the REAL
save/load work -- these dialogs just collect the path. No molecular work here.

Default save dir = ``user_data_path("saves")`` (06-02): OUTSIDE the plugin
install dir (~/.pymol/startup/<plugin>/) so a plugin reinstall (delete +
re-unzip) does NOT wipe the player's saves (06-RESEARCH-persistence-achievements.md
Pitfall 5). The dir is ``os.makedirs``-created on first use so the first save
"just works" without the user having to pre-create it.

Filter: ``"RPG Save (*.json)"`` -- human-readable JSON saves (Phase 2 SaveStore,
Decision D2; persist.py). The JSON format keeps saves diff-friendly for
debugging + is editable in a text editor (educators can inspect/patch a save).

Gate-EXEMPT: ``c14/ui/`` is in ``tools/check_imports.py`` SKIP_DIRS, so this
module MAY import ``pymol.Qt``. Importing this module in pure WSL python3.6
FAILS (no Qt installed) -- that is EXPECTED; only ``python3.6 -m py_compile``
is WSL-verifiable here. The functional round-trip (save mid-game, load, scene +
view + RNG + story position restored) is human-verify in plan 06-14 (SC3).

Anti-patterns AVOIDED (06-RESEARCH-ui-adapter.md Pitfall 3 +
06-RESEARCH-persistence-achievements.md):
- NO ``.pse`` session is saved (Anti-Pattern 5 -- persist.py:1-9; the scene
  rebuilds on load via on_enter replay, a pure function of game state).
- NO manual scene re-application after ``engine.load`` (double-dispatch bug --
  the engine already replays on_enter; the controller.load just renders).
- NO hardcoded save dir (use ``user_data_path`` so saves survive reinstalls --
  Pitfall 5).
- NO f-strings (Python 3.6 compatible, uses ``.format()``).
- Does NOT block the GUI: the save/load are fast JSON ops handled by the
  controller/engine; the dialog itself is a native modal QFileDialog.

Python 3.6 compatible: no f-strings, no ``@dataclass``, plain functions.
Matches the conventions of ``c14/ui/help_dialog.py`` +
``c14/ui/achievements_dialog.py`` (gate-EXEMPT, ``from pymol.Qt import ...``).
"""
import os

from pymol.Qt import QtWidgets

from c14.paths import user_data_path


def _saves_dir():
    # type: () -> str
    """Return the default save dir (``user_data_path("saves")``) as a str,
    creating it on first use.

    ``user_data_path`` resolves to ~/.pymol/c14-tale-of-c/saves on Linux/Mac,
    %APPDATA%/pymol/c14-tale-of-c/saves on Windows -- OUTSIDE the plugin
    install dir so a reinstall does not wipe saves (Pitfall 5). ``makedirs``
    with ``exist_ok=True`` makes the first save "just work" without the user
    pre-creating the dir; it is idempotent on later calls. Returns str (not
    Path) because ``QFileDialog`` wants a string default path.
    """
    d = str(user_data_path("saves"))
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    return d


def ask_save_path(parent, default_name="save.json"):
    # type: (QtWidgets.QWidget, str) -> str
    """Open a Save dialog defaulting to ``user_data_path("saves")/<default_name>``.

    Returns the chosen path (str) or ``None`` (user cancelled). Filter:
    ``RPG Save (*.json)``. The caller (MainWindow Save button, 06-08) passes
    the returned path to ``controller.save(path)`` only when non-None.

    Args:
        parent: the Qt parent widget (the MainWindow; for dialog stacking).
        default_name: the default filename shown in the dialog
            (``"save.json"``). The user can rename it.
    """
    path, _ = QtWidgets.QFileDialog.getSaveFileName(
        parent, "Save RPG: Tale of C Game",
        os.path.join(_saves_dir(), default_name), "RPG Save (*.json)")
    return path or None


def ask_load_path(parent):
    # type: (QtWidgets.QWidget) -> str
    """Open a Load dialog defaulting to ``user_data_path("saves")``.

    Returns the chosen path (str) or ``None`` (user cancelled). Filter:
    ``RPG Save (*.json)``. The caller (MainWindow Load button, 06-08) passes
    the returned path to ``controller.load(path)`` only when non-None.

    Args:
        parent: the Qt parent widget (the MainWindow; for dialog stacking).
    """
    path, _ = QtWidgets.QFileDialog.getOpenFileName(
        parent, "Load RPG: Tale of C Game",
        _saves_dir(), "RPG Save (*.json)")
    return path or None
