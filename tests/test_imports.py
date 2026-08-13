"""Tests for the AST import-boundary gate (tools/check_imports.py) + domain py_compile sweep.

Covers:
- banned import forms are caught (7 forms incl. aliased submodule imports)
- no false positives on comments / string literals (AST > grep)
- the gate exits 0 on the clean c14/ skeleton
- every domain-tier .py passes py_compile (syntax) -- pairs with the gate
  per 01-RESEARCH-testability.md Pitfall 3 (py_compile necessary but not sufficient).
"""
import os
import py_compile
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GATE_SCRIPT = os.path.join(REPO_ROOT, "tools", "check_imports.py")
C14_ROOT = os.path.join(REPO_ROOT, "c14")

# Make tools/ importable so we can import check_imports directly.
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
import check_imports  # noqa: E402  (path setup above)

SKIP_DIRS = {"pymol_layer", "ui", "__pycache__"}


class TestViolationsInCatchesBannedImports(unittest.TestCase):
    """violations_in() must catch every banned static import form."""

    BANNED_FORMS = [
        "import pymol\n",
        "from pymol import cmd\n",
        "import pymol.cmd as c\n",
        "from pymol.Qt import QtWidgets\n",
        "from pymol.cgo import CGO\n",
        "import PyQt5.QtCore\n",
        "from PyQt5 import QtWidgets as W\n",
    ]

    def test_violations_in_catches_banned_imports(self):
        d = tempfile.mkdtemp(prefix="c14_gate_test_")
        for idx, src in enumerate(self.BANNED_FORMS):
            path = os.path.join(d, "violation_%d.py" % idx)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(src)
            rel = "violation_%d.py" % idx
            violations = check_imports.violations_in(path, rel)
            self.assertGreaterEqual(
                len(violations), 1,
                "Expected >=1 violation for source %r but got %r" % (src.strip(), violations),
            )


class TestViolationsInNoFalsePositives(unittest.TestCase):
    """violations_in() must NOT flag pymol/PyQt5 appearing only in comments/strings."""

    def test_violations_in_no_false_positives(self):
        src = (
            "# import pymol here -- this is just a comment\n"
            "x = 'from pymol import cmd'  # string literal, not an import\n"
            "y = \"import PyQt5.QtCore\"\n"
            "import json  # a real, allowed import\n"
        )
        d = tempfile.mkdtemp(prefix="c14_gate_clean_")
        path = os.path.join(d, "clean.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(src)
        violations = check_imports.violations_in(path, "clean.py")
        self.assertEqual(
            violations, [],
            "Expected zero violations (AST must ignore comments/strings) but got %r" % violations,
        )


class TestGatePassesOnCleanSkeleton(unittest.TestCase):
    """The real c14/ skeleton (domain tier) must pass the gate with exit 0."""

    def test_gate_passes_on_clean_skeleton(self):
        # The gate resolves ROOT from its own __file__, so cwd does not matter.
        # NOTE: capture_output= is 3.7+; on 3.6 use stdout/stderr=PIPE explicitly.
        result = subprocess.run(
            [sys.executable, GATE_SCRIPT],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(
            result.returncode, 0,
            "Gate failed on clean skeleton.\nstdout=%r\nstderr=%r"
            % (result.stdout.decode("utf-8"), result.stderr.decode("utf-8")),
        )
        stdout = result.stdout.decode("utf-8")
        self.assertIn("clean", stdout, "Expected 'clean' in gate stdout, got: %r" % stdout)


class TestPyCompileAllDomainModules(unittest.TestCase):
    """Every domain-tier .py (excluding pymol_layer/ui/__pycache__) must py_compile."""

    def test_py_compile_all_domain_modules(self):
        compiled = []
        for dirpath, dirnames, filenames in os.walk(C14_ROOT):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in sorted(filenames):
                if not fn.endswith(".py"):
                    continue
                full = os.path.join(dirpath, fn)
                # doraise=True -> raises py_compile.PyCompileError on failure.
                py_compile.compile(full, doraise=True)
                compiled.append(full)
        self.assertGreaterEqual(
            len(compiled), 1,
            "Expected to compile at least one domain .py file; found none (walk broken?)",
        )


if __name__ == "__main__":
    unittest.main()
