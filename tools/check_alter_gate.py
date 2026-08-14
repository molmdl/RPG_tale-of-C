#!/usr/bin/env python3.6
"""tools/check_alter_gate.py -- AST gate enforcing the sanctioned-alter invariant (SC1).

Rule: any ``*.alter(...)`` Attribute CALL (i.e. an ``ast.Call`` whose ``func``
is an ``ast.Attribute`` with ``attr == "alter"``) may appear ONLY in
``c14/pymol_layer/edit_ops.py`` (the allowlist). Nowhere else in ``c14/``
(INCLUDING ``c14/pymol_layer/`` and ``c14/ui/`` -- unlike check_imports.py
which skips them) or ``tools/``.

Why AST (not grep): AST on ``Attribute(attr='alter')`` is precise -- it catches
``cmd.alter(...)``, ``self._cmd.alter(...)``, ``pymol.cmd.alter(...)`` uniformly,
and will NOT false-positive on the word "alter" in comments, docstrings, or
string literals (e.g. ``{"mode": "alter"}`` in c14/protonation_catalog.py is an
ast.Str/ast.Constant node, NOT an ast.Call -- correctly ignored). A grep on
``.alter(`` would false-positive on those string values; AST does not.

This makes SC1 ("apply_edit is the only sanctioned alter path -- grep finds no
bare cmd.alter outside it") a hard, machine-checkable invariant, NOT just a
unit-tested one. The unit tests (tests/test_edit_ops.py) prove apply_edit sorts;
THIS gate proves no stray ``cmd.alter`` elsewhere in the repo bypasses the
safety net. ProtonationManager (c14/pymol_layer/protonation.py, 04-03) is NOT
in the allowlist -- it delegates to edit_ops.apply_edit, so it has no
``cmd.alter`` call (the 04-03 unit test ``test_protonation_manager_no_direct_alter``
asserts this at the unit-test level; THIS gate is the repo-wide enforcement).

Exit codes (Phase 1 three-way convention, check_citations.py:6-11):

    0 = clean (no *.alter(...) Attribute calls outside the allowlist)
    1 = violation (a bare alter call outside edit_ops.py)
    2 = ERROR (AST parse failure / config error -- e.g. a .py with a SyntaxError)

Usage::

    python3.6 tools/check_alter_gate.py

Pure stdlib. Python 3.6 compatible. Importable in pure WSL python3.6 (no pymol).
"""
import ast
import os
import sys

# Repo root resolved from __file__ so the gate runs regardless of CWD (mirrors
# check_imports.py:32 + check_citations.py:39).
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The SOLE allowlisted file. Stored with forward-slash + relative to repo root
# so the comparison is OS-independent (os.walk yields OS-sep paths; we normalize
# via os.path.relpath + .replace(os.sep, "/") before the membership test).
ALLOWLIST = {"c14/pymol_layer/edit_ops.py"}

# Scan roots: c14/ (INCLUDING pymol_layer/ + ui/ -- the alter gate does NOT
# skip them, unlike check_imports.py) and tools/. We DO skip __pycache__.
SCAN_ROOTS = [os.path.join(REPO_ROOT, "c14"), os.path.join(REPO_ROOT, "tools")]
SKIP_DIRS = {"__pycache__"}


def _rel_posix(path):
    # type: (str) -> str
    """Return ``path`` relative to REPO_ROOT with forward slashes (POSIX).

    Normalizes OS-specific separators so the ALLOWLIST membership test is
    portable (os.walk on Linux yields "/"-separated paths already, but this
    makes the gate correct if ever run on Windows).
    """
    rel = os.path.relpath(path, REPO_ROOT)
    return rel.replace(os.sep, "/")


def alter_calls_in(path, rel):
    # type: (str, str) -> list
    """Return a list of ``"<rel>:<line>"`` strings for each ``*.alter(...)``
    Attribute CALL in the .py file at ``path``.

    ``rel`` is the display path (relative to repo root, POSIX). A SyntaxError
    is reported as a parse-failure entry so a broken .py surfaces here too
    (mapped to exit 2 by the caller).
    """
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as e:
        # Propagate as a distinct marker so main() can map to exit 2 (ERROR),
        # not exit 1 (violation). A SyntaxError is a config/tooling problem,
        # not a gate violation.
        return ["__SYNTAXERROR__:%s:%d %s" % (rel, e.lineno or 0, e.msg)]
    out = []
    for node in ast.walk(tree):
        # An *.alter(...) call: ast.Call whose func is ast.Attribute named alter.
        # This catches cmd.alter, self._cmd.alter, pymol.cmd.alter uniformly --
        # any <expr>.alter(...) regardless of the receiver expression. It does
        # NOT match the bare name alter() (ast.Name) or alter as a string
        # literal (ast.Str/ast.Constant) -- AST precision, no false positives.
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "alter":
                out.append("%s:%d" % (rel, node.lineno))
    return out


def find_violations(roots, allowlist):
    # type: (list, set) -> tuple
    """Walk ``roots`` and return ``(violations, errors)``.

    ``violations``: list of ``"<rel>:<line>"`` strings for each ``*.alter(...)``
    Attribute call OUTSIDE ``allowlist``. ``errors``: list of parse-failure /
    missing-root messages (-> exit 2). ``rel`` is relative to REPO_ROOT (POSIX).

    Extracted from ``main()`` so the exit-1 path is unit-testable in a temp dir
    without subprocess (mirrors the check_citations.py:run_gate testable-core
    pattern). ``main()`` calls this with the hardcoded SCAN_ROOTS + ALLOWLIST.
    """
    violations = []  # list of "rel:line" outside the allowlist
    errors = []      # list of parse-failure messages (-> exit 2)
    for root in roots:
        if not os.path.isdir(root):
            # A missing scan root is a config error (repo layout broken).
            errors.append("scan root not found: %s" % root)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune __pycache__ in-place (mirrors check_imports.py:81).
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in sorted(filenames):
                if not fn.endswith(".py"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = _rel_posix(full)
                calls = alter_calls_in(full, rel)
                for c in calls:
                    if c.startswith("__SYNTAXERROR__:"):
                        # Strip the marker, record as an ERROR (exit 2).
                        errors.append(c[len("__SYNTAXERROR__:"):])
                        continue
                    # c is "rel:line". Allowlisted file -> OK; else violation.
                    # The rel prefix up to the first ":" is the file path.
                    file_part = c.split(":", 1)[0]
                    if file_part in allowlist:
                        continue
                    violations.append(c)
    return violations, errors


def main():
    # type: () -> int
    violations, errors = find_violations(SCAN_ROOTS, ALLOWLIST)
    if errors:
        sys.stderr.write("ALTER GATE ERROR (%d):\n" % len(errors))
        for e in errors:
            sys.stderr.write("  " + e + "\n")
        sys.stderr.write(
            "Fix the parse error above -- the gate cannot scan a .py with a "
            "SyntaxError.\n")
        return 2
    if violations:
        sys.stderr.write("ALTER GATE VIOLATIONS (%d):\n" % len(violations))
        for v in sorted(violations):
            sys.stderr.write("  " + v + "\n")
        sys.stderr.write(
            "cmd.alter is only allowed in c14/pymol_layer/edit_ops.py (the "
            "sanctioned apply_edit helper); route other alter needs through "
            "EditOps.apply_edit.\n")
        return 1
    print("check_alter_gate: clean (no *.alter(...) Attribute calls outside "
          "c14/pymol_layer/edit_ops.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
