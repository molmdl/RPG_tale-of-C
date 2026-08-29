# Source: stdlib unittest pattern; CWD-independence proof via real os.chdir.
# Python 3.6 compatible (tempfile.mkdtemp, pathlib, unittest all stdlib).
# Adopted near-verbatim from .planning/phases/01-foundations-testability-citation-gate/
# 01-RESEARCH-paths.md "Code Examples" (prescriptive reference design).
"""Prove bundled-data resolution is CWD-independent (Phase 1 SC #3).

Every test runs from a foreign working directory (setUp chdir's into a
tempdir; tearDown restores). If data_path()/selfcheck() were
cwd-relative, the fixture would not be found from the temp dir ->
selfcheck() would raise -> test fails. Existence-from-foreign-CWD IS
the proof of __file__-relative (not cwd-relative) resolution. A real
os.chdir is the honest end-to-end proof (better than mock.patch of
os.getcwd, which only proves the call site, not the behavior).
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from c14.paths import data_path, selfcheck, user_data_path


class TestPathResolution(unittest.TestCase):
    """Prove bundled-data resolution is CWD-independent (Phase 1 SC #3)."""

    def setUp(self):
        # Run EVERY test from a foreign working directory so CWD-independence
        # is proven for free on every assertion, not just one named test.
        self._orig_cwd = os.getcwd()
        self._tmp = tempfile.mkdtemp(prefix="c14_pathtest_")
        os.chdir(self._tmp)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_selfcheck_resolves_from_arbitrary_cwd(self):
        # If resolution were cwd-relative, the fixture would not be found
        # from this temp dir -> selfcheck() would raise. Existence here IS
        # the proof of __file__-relative (not cwd-relative) resolution.
        resolved = selfcheck()  # raises FileNotFoundError if missing
        p = Path(resolved)
        self.assertTrue(p.is_absolute(), "{p} is not absolute".format(p=p))
        self.assertTrue(
            p.is_file(),
            "{p} does not exist from cwd={cwd}".format(p=p, cwd=os.getcwd()),
        )
        # And it must NOT be under the temp cwd (belt-and-suspenders):
        self.assertNotEqual(p.resolve().parent, Path(self._tmp).resolve())

    def test_data_path_returns_absolute_path(self):
        p = data_path("data", "selfcheck.json")
        self.assertTrue(p.is_absolute(), "{p} is not absolute".format(p=p))
        # The resolved path's parent must be the package data dir, derived
        # from __file__ (this test file lives at tests/test_paths.py, so
        # repo_root = parent.parent, and c14/ is under repo_root).
        pkg_root = Path(__file__).resolve().parent.parent / "c14"
        self.assertEqual(p.resolve().parent, (pkg_root / "data").resolve())

    def test_data_path_does_not_raise_for_nonexistent_file(self):
        # Resolver must NOT raise for a not-yet-present path; it just resolves.
        # Proves the resolver is pure (no existence coupling).
        p = data_path("data", "does-not-exist-yet.json")
        self.assertTrue(p.is_absolute())
        self.assertFalse(p.exists())


class TestUserDataPath(unittest.TestCase):
    """Prove user_data_path is platform-correct + CWD-independent + pure-resolver.

    Mirrors the Phase 1 CWD-independence proof pattern (real os.chdir into a
    tempdir in setUp) so every test runs from a foreign working directory AND
    snapshots os.environ so APPDATA set/unset in a single test is restored in
    tearDown (no cross-test or cross-session leakage). Uses the REAL
    os.path.expanduser (NOT mocked) so the assertion exercises the actual
    resolution the production code will use. Does NOT create any dirs on disk
    -- the resolver is a pure path-arithmetic function (no existence check).
    """

    def setUp(self):
        # Snapshot os.environ so an APPDATA set/unset in one test is fully
        # restored in tearDown (dict copy = deep enough; values are str).
        self._saved_env = dict(os.environ)
        # Run EVERY test from a foreign working directory so CWD-independence
        # is proven for free on every assertion (matches TestPathResolution).
        self._orig_cwd = os.getcwd()
        self._tmp = tempfile.mkdtemp(prefix="c14_userdatatest_")
        os.chdir(self._tmp)

    def tearDown(self):
        # Restore the environment exactly as it was (re-set APPDATA if it had a
        # value; clear it if the test deleted it). clear+update is the robust
        # full-snapshot restore (handles set->unset AND unset->set).
        os.environ.clear()
        os.environ.update(self._saved_env)
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_linux_mac_path_when_appdata_unset(self):
        # Linux/Mac branch: APPDATA unset -> ~/.pymol/c14-tale-of-c/<parts>.
        os.environ.pop('APPDATA', None)
        p = user_data_path("achievements.json")
        expected_suffix = os.path.join(
            os.path.expanduser('~'), '.pymol', 'c14-tale-of-c', 'achievements.json')
        self.assertTrue(
            str(p).endswith(expected_suffix),
            "{p} does not end with the Linux/Mac base {e}".format(p=p, e=expected_suffix))

    def test_windows_path_when_appdata_set(self):
        # Windows branch: APPDATA set -> %APPDATA%/pymol/c14-tale-of-c/<parts>.
        os.environ['APPDATA'] = 'C:\\Users\\test\\AppData\\Roaming'
        p = user_data_path("saves", "game.json")
        expected = os.path.join(
            'C:\\Users\\test\\AppData\\Roaming', 'pymol', 'c14-tale-of-c',
            'saves', 'game.json')
        self.assertEqual(
            str(p), expected,
            "Windows APPDATA branch resolved {p}, expected {e}".format(p=p, e=expected))

    def test_cwd_independence(self):
        # We already chdir'd into a tempdir in setUp. Capture the resolved path,
        # chdir somewhere ELSE, and confirm it is unchanged -- user_data_path
        # resolves via os.environ/expanduser, NOT os.getcwd(). (Honest
        # end-to-end proof, mirroring Phase 1 data_path CWD-independence.)
        before = str(user_data_path("x.json"))
        tmp2 = tempfile.mkdtemp(prefix="c14_userdatatest2_")
        try:
            os.chdir(tmp2)
            after = str(user_data_path("x.json"))
            self.assertEqual(
                after, before,
                "user_data_path changed with CWD: before={b} after={a}".format(
                    b=before, a=after))
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)

    def test_no_existence_check(self):
        # Pure resolver: must NOT raise even though neither file nor dir exists.
        # Callers makedirs as needed (matches data_path's pure-resolver design).
        p = user_data_path("does_not_exist.json")
        self.assertIsInstance(p, Path)
        self.assertFalse(
            p.exists(),
            "resolver should not require the target to exist; {p} exists".format(p=p))

    def test_returns_path_object(self):
        # Callers use str() for open(); the return is a pathlib.Path, not str.
        self.assertIsInstance(user_data_path("a"), Path)

    def test_multiple_parts(self):
        # joinpath must join ALL trailing parts (saves/sub/game.json), not just
        # the first. Assert against the platform-independent suffix so it holds
        # on both Linux/Mac and Windows APPDATA branches.
        os.environ.pop('APPDATA', None)
        p = user_data_path("saves", "sub", "game.json")
        self.assertTrue(
            str(p).endswith(os.path.join('.pymol', 'c14-tale-of-c', 'saves', 'sub', 'game.json')),
            "{p} does not join all parts".format(p=p))

    def test_no_parts(self):
        # Zero trailing parts -> the base user-data dir itself.
        os.environ.pop('APPDATA', None)
        p = user_data_path()
        expected = os.path.join(os.path.expanduser('~'), '.pymol', 'c14-tale-of-c')
        self.assertEqual(
            str(p), expected,
            "no-parts base resolved {p}, expected {e}".format(p=p, e=expected))

    def test_gate_clean(self):
        # c14.paths imports only os + pathlib (NO pymol/PyQt5) -> it imports
        # cleanly in pure WSL python3.6 with no PyMOL installed. The AST gate
        # (tools/check_imports.py) checks this statically; this test is its
        # runtime twin: importing the module must not pull in pymol/PyQt5 as a
        # side effect. (The module-level import at the top of this file already
        # proved importability; this re-asserts + checks sys.modules.)
        import sys
        import c14.paths  # noqa: F401  -- documents the gate-clean contract
        self.assertNotIn(
            'pymol', sys.modules,
            "c14.paths must not import pymol (AST gate + runtime proof)")
        self.assertNotIn(
            'PyQt5', sys.modules,
            "c14.paths must not import PyQt5 (AST gate + runtime proof)")


if __name__ == "__main__":
    unittest.main()
