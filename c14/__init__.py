# Version: 0.0.1
# Author: RPG Tale of C contributors
# Citation-Required: No
"""c14 -- RPG: Tale of C PyMOL plugin package.

Phase 1: minimal, pymol/PyQt5-FREE so pure-Python submodules stay
unit-testable in WSL. The PyMOL plugin __init_plugin__ entry point
arrives in Phase 6; when it does, it must lazy-delegate to
c14/ui/plugin_entry.py (never import pymol/PyQt5 at module top level
here -- see 01-RESEARCH-testability.md Pattern 1).
"""
__version__ = "0.0.1-dev"


def __init_plugin__(pmgapp):
    # type: (object) -> None
    """PyMOL 2.5.0 plugin entry point.

    Called by pymol.plugins.PluginInfo.legacyinit after this module is
    imported (plugins/__init__.py:320-321). pmgapp is the PMGApp instance;
    modern Qt plugins IGNORE it and register via addmenuitemqt.

    All pymol/PyQt5 imports are deferred to c14/ui/plugin_entry.py
    (gate-exempt) so THIS file passes tools/check_imports.py.
    """
    # 1. Fail loud if the bundled data layout is broken (Phase 1 Pitfall 1).
    from .paths import selfcheck
    selfcheck()
    # 2. Delegate menu registration + window construction to the Qt layer.
    #    Relative import resolves whether PyMOL imports us as 'startup.c14'
    #    or 'pmg_tk.startup.c14'. The name 'ui' is NOT in BANNED_TOP.
    from .ui import plugin_entry
    plugin_entry.init_plugin(pmgapp)
