#!/usr/bin/env python3.6
"""tools/check_imports.py -- enforce the pure-Python testability boundary.

Scans all .py under c14/ EXCLUDING c14/pymol_layer/ and c14/ui/.
Fails (exit 1) if any scanned file imports pymol.* or PyQt5.* (any form:
``import pymol``, ``from pymol.Qt import ...``, ``import pymol.cmd as c``,
etc.). Also flags dynamic imports (__import__/importlib) naming pymol/PyQt5
for human review.

STRICT-BAN policy: the gate flags ANY pymol/PyQt5 Import/ImportFrom node,
INCLUDING those inside ``if TYPE_CHECKING:`` guards. The MolAction-as-pure-data
architecture means the domain tier never needs to name a pymol type, so a
strict ban keeps the boundary airtight and the gate trivial. See
01-RESEARCH-testability.md Open Question 1.

Pure stdlib. Python 3.6 compatible. The canonical Phase 1 check command is::

    python3.6 tools/check_imports.py && python3.6 -m unittest discover -s tests -v

The AST gate proves no banned imports; the unittest run imports all domain
modules (proving import-cleanliness beyond py_compile). Together they satisfy
Phase 1 success-criterion #1 fully. Invoke the gate alone:

    python3.6 tools/check_imports.py

Exit 0 = clean; 1 = violations.
"""
import ast
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "c14")
SKIP_DIRS = {"pymol_layer", "ui", "__pycache__"}
BANNED_TOP = ("pymol", "PyQt5")


def _banned(module_name):
    # type: (str) -> bool
    if not module_name:
        return False
    return module_name.split(".", 1)[0] in BANNED_TOP


def violations_in(path, rel):
    # type: (str, str) -> list
    """Return a list of violation strings for the .py file at ``path``.

    ``rel`` is the display path (relative to the scanned root). A SyntaxError
    is reported as a violation so py_compile failures surface here too.
    """
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as e:
        return ["%s:%d SyntaxError (py_compile would fail): %s" % (rel, e.lineno or 0, e.msg)]
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _banned(alias.name):
                    out.append("%s:%d import %s" % (rel, node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if _banned(node.module):
                names = ", ".join(a.name for a in node.names)
                out.append("%s:%d from %s import %s" % (rel, node.lineno, node.module, names))
    # Secondary: dynamic imports of banned modules (AST can't see these as Import nodes)
    for i, line in enumerate(src.splitlines(), 1):
        s = line.strip()
        if s.startswith("#"):
            continue
        if ("__import__" in s or "import_module" in s) and ("pymol" in s.lower() or "pyqt5" in s.lower()):
            out.append("%s:%d REVIEW dynamic import: %s" % (rel, i, s))
    return out


def main():
    # type: () -> int
    bad = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]  # prune in-place
        for fn in sorted(filenames):
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT)
            bad.extend(violations_in(full, rel))
    if bad:
        sys.stderr.write("IMPORT BOUNDARY VIOLATIONS (%d):\n" % len(bad))
        for b in sorted(bad):
            sys.stderr.write("  " + b + "\n")
        sys.stderr.write("Domain-tier files must not import pymol/PyQt5. "
                         "Move the import into c14/pymol_layer/ or c14/ui/.\n")
        return 1
    print("check_imports: clean (no pymol/PyQt5 imports in c14/ domain tier)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
