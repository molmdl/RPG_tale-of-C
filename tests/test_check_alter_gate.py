"""Tests for the AST alter gate (tools/check_alter_gate.py) -- SC1 self-test.

Covers:
- alter_calls_in() catches every *.alter(...) Attribute CALL form uniformly
  (cmd.alter, self._cmd.alter, pymol.cmd.alter).
- alter_calls_in() does NOT false-positive on "alter" in comments, docstrings,
  or string literals (e.g. {"mode": "alter"} in c14/protonation_catalog.py) --
  AST precision over grep.
- find_violations() allowlist: an alter call in c14/pymol_layer/edit_ops.py is
  OK; the SAME call in c14/pymol_layer/molops.py is a violation (exit 1 path).
- find_violations() maps a SyntaxError to the errors list (exit 2 path).
- The real repo passes the gate with exit 0 (integration, like
  test_imports.py:test_gate_passes_on_clean_skeleton).

Pure WSL python3.6 -- NO pymol import. The gate is stdlib-only (ast + os).
"""
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GATE_SCRIPT = os.path.join(REPO_ROOT, "tools", "check_alter_gate.py")

# Make tools/ importable so we can import check_alter_gate directly.
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
import check_alter_gate  # noqa: E402  (path setup above)


class TestAlterCallsInCatchesAllForms(unittest.TestCase):
    """alter_calls_in() must catch every *.alter(...) Attribute call form."""

    ALTER_FORMS = [
        "cmd.alter('sele', 'resn=\\'GLY\\'')\n",                 # cmd.alter
        "self._cmd.alter('sele', 'resn=\\'GLY\\'')\n",           # self._cmd.alter
        "pymol.cmd.alter('sele', 'resn=\\'GLY\\'')\n",           # pymol.cmd.alter
    ]

    def test_alter_calls_in_catches_all_attribute_forms(self):
        d = tempfile.mkdtemp(prefix="c14_altergate_test_")
        for idx, src in enumerate(self.ALTER_FORMS):
            path = os.path.join(d, "alter_%d.py" % idx)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(src)
            calls = check_alter_gate.alter_calls_in(path, "alter_%d.py" % idx)
            self.assertGreaterEqual(
                len(calls), 1,
                "Expected >=1 alter call for source %r but got %r" % (src.strip(), calls),
            )


class TestAlterCallsInNoFalsePositives(unittest.TestCase):
    """alter_calls_in() must NOT flag 'alter' in comments/strings/dict-values."""

    def test_alter_calls_in_ignores_strings_and_comments(self):
        # The protonation_catalog.py pattern: {"mode": "alter"} is a STRING
        # literal, NOT a call. A grep on .alter( would false-positive on the
        # dict value if written as {"mode": "alter"}  -- but here the value is
        # a bare string with no parens. Include both forms to be thorough.
        src = (
            "# cmd.alter is the sanctioned path -- this is just a comment\n"
            "doc = \"use cmd.alter to change resn\"  # string literal\n"
            "mode = 'alter'  # bare string value, not a call\n"
            "config = {\"mode\": \"alter\"}  # dict value, AST = ast.Str\n"
            "import json  # a real, allowed import\n"
        )
        d = tempfile.mkdtemp(prefix="c14_altergate_clean_")
        path = os.path.join(d, "clean.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(src)
        calls = check_alter_gate.alter_calls_in(path, "clean.py")
        self.assertEqual(
            calls, [],
            "Expected zero alter calls (AST must ignore comments/strings) but got %r" % calls,
        )


class TestFindViolationsAllowlist(unittest.TestCase):
    """find_violations() must honor the allowlist: edit_ops.py OK, molops.py NOT."""

    def _make_repo_tree(self, allowlisted_src, stray_src):
        """Build a temp c14/ tree with pymol_layer/edit_ops.py + pymol_layer/molops.py.

        Returns (roots, allowlist, edit_ops_rel, molops_rel) so the test can
        call find_violations(roots, allowlist) and inspect the result.
        """
        d = tempfile.mkdtemp(prefix="c14_altergate_repo_")
        # Mirror the real layout: <d>/c14/pymol_layer/edit_ops.py + molops.py
        pymol_layer = os.path.join(d, "c14", "pymol_layer")
        os.makedirs(pymol_layer)
        edit_ops_path = os.path.join(pymol_layer, "edit_ops.py")
        molops_path = os.path.join(pymol_layer, "molops.py")
        with open(edit_ops_path, "w", encoding="utf-8") as fh:
            fh.write(allowlisted_src)
        with open(molops_path, "w", encoding="utf-8") as fh:
            fh.write(stray_src)
        # find_violations resolves rel paths against REPO_ROOT, so we must
        # override REPO_ROOT to the temp dir for the rel computation to match.
        # Easiest: monkey-patch check_alter_gate.REPO_ROOT for this test.
        orig = check_alter_gate.REPO_ROOT
        check_alter_gate.REPO_ROOT = d
        self.addCleanup(setattr, check_alter_gate, "REPO_ROOT", orig)
        roots = [os.path.join(d, "c14")]
        allowlist = {"c14/pymol_layer/edit_ops.py"}
        return roots, allowlist

    def test_allowlisted_alter_in_edit_ops_not_flagged(self):
        roots, allowlist = self._make_repo_tree(
            "def f(cmd):\n    cmd.alter('sele', 'resn=\\'GLY\\'')\n",
            "# no alter here\nimport json\n",
        )
        violations, errors = check_alter_gate.find_violations(roots, allowlist)
        self.assertEqual(violations, [], "Allowlisted alter in edit_ops.py must NOT be flagged; got %r" % violations)
        self.assertEqual(errors, [], "Expected no errors; got %r" % errors)

    def test_stray_alter_in_molops_flagged(self):
        roots, allowlist = self._make_repo_tree(
            "# edit_ops with no alter here\nimport json\n",
            "def f(cmd):\n    cmd.alter('sele', 'resn=\\'GLY\\'')\n",
        )
        violations, errors = check_alter_gate.find_violations(roots, allowlist)
        self.assertEqual(len(violations), 1, "Stray alter in molops.py MUST be flagged; got %r" % violations)
        self.assertIn("molops.py", violations[0], "Violation should name molops.py; got %r" % violations[0])
        self.assertEqual(errors, [], "Expected no errors; got %r" % errors)


class TestFindViolationsSyntaxError(unittest.TestCase):
    """A .py with a SyntaxError maps to the errors list (exit 2), not exit 1."""

    def test_syntax_error_reported_as_error_not_violation(self):
        d = tempfile.mkdtemp(prefix="c14_altergate_syntax_")
        bad_path = os.path.join(d, "c14", "broken.py")
        os.makedirs(os.path.dirname(bad_path))
        with open(bad_path, "w", encoding="utf-8") as fh:
            fh.write("def f(:\n    cmd.alter('sele','x')\n")  # SyntaxError
        orig = check_alter_gate.REPO_ROOT
        check_alter_gate.REPO_ROOT = d
        self.addCleanup(setattr, check_alter_gate, "REPO_ROOT", orig)
        roots = [os.path.join(d, "c14")]
        violations, errors = check_alter_gate.find_violations(roots, set())
        # The broken file must NOT be silently ignored -- it surfaces as an error.
        # e.msg on 3.6 is "invalid syntax" (not the literal word "SyntaxError");
        # the reliable marker is the filename + the parse-failure message.
        self.assertEqual(len(errors), 1, "Expected 1 parse error; got %r" % errors)
        self.assertIn("broken.py", errors[0], "Error should name the broken file; got %r" % errors[0])
        # And it must NOT be counted as a violation (exit 2, not exit 1).
        self.assertEqual(violations, [], "A SyntaxError must not be counted as a violation; got %r" % violations)


class TestGatePassesOnRealRepo(unittest.TestCase):
    """The real repo must pass the alter gate with exit 0 (integration)."""

    def test_gate_passes_on_real_repo(self):
        # The gate resolves paths from its own __file__, so cwd does not matter.
        # NOTE: capture_output= is 3.7+; on 3.6 use stdout/stderr=PIPE (Pitfall 3).
        result = subprocess.run(
            [sys.executable, GATE_SCRIPT],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(
            result.returncode, 0,
            "Alter gate failed on real repo.\nstdout=%r\nstderr=%r"
            % (result.stdout.decode("utf-8"), result.stderr.decode("utf-8")),
        )
        stdout = result.stdout.decode("utf-8")
        self.assertIn("clean", stdout, "Expected 'clean' in gate stdout, got: %r" % stdout)


if __name__ == "__main__":
    unittest.main()
