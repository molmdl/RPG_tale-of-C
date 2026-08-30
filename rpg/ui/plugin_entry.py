"""Qt plugin entry point -- called by rpg/__init__.py.__init_plugin__.

Gate-exempt: may import pymol.Qt / pymol.plugins
(tools/check_imports.py SKIP_DIRS = {"pymol_layer", "ui", "__pycache__"}).
Defer pymol imports to INSIDE init_plugin / _open_main_window so merely
importing rpg/__init__.py (during PyMOL's __import__ phase) does NOT touch
Qt before the GUI is ready. Matches dynoplot.py:445-447 + optimize.py:29-31.
"""
_main_window = None  # singleton; constructed lazily on first menu click


def init_plugin(pmgapp):
    # type: (object) -> None
    """Register the 'RPG: Tale of C' menu item. Called once on plugin load."""
    from pymol.plugins import addmenuitemqt            # plugins/__init__.py:100
    addmenuitemqt('RPG: Tale of C', _open_main_window)  # label, no-arg callback


def _open_main_window():
    """Menu callback: construct (or re-show) the main game window."""
    global _main_window
    from pymol.Qt import QtWidgets                     # Qt is ready at click time
    from .main_window import MainWindow                # rpg/ui/main_window.py (06-08)
    if _main_window is None:
        _main_window = MainWindow()
    _main_window.show()
    _main_window.raise_()
