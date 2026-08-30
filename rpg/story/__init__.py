"""Story subpackage: data model + graph loader + interpreter + validator.

Pure-Python, stdlib only. This subpackage is scanned by the Phase 1 AST gate
(``tools/check_imports.py``) as part of ``rpg/`` and MUST NOT import pymol or
PyQt5 -- the domain tier never names a PyMOL type (see ARCHITECTURE.md Pattern 1
and Anti-Pattern 1). The ``MolAction`` data carrier is the only bridge from
this tier to the future ``rpg/pymol_layer/`` translation; it is pure data, never
a ``cmd.*`` call.

Modules (built across Phase 2):
- ``rpg.story.model``       -- Node, Choice, MolAction plain classes (Plan 01).
- ``rpg.story.loader``      -- JSON graph loader (Plan 02).
- ``rpg.story.interpreter`` -- graph walker + choice/variant resolution (Plan 03).
- ``rpg.story.validate``    -- structural + reference validator (Plan 04/05).
"""
