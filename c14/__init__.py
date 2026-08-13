"""c14 -- RPG: Tale of C PyMOL plugin package.

Phase 1: minimal, pymol/PyQt5-FREE so pure-Python submodules stay
unit-testable in WSL. The PyMOL plugin __init_plugin__ entry point
arrives in Phase 6; when it does, it must lazy-delegate to
c14/ui/plugin_entry.py (never import pymol/PyQt5 at module top level
here -- see 01-RESEARCH-testability.md Pattern 1).
"""
__version__ = "0.0.1-dev"
