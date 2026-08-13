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

from c14.paths import data_path, selfcheck


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


if __name__ == "__main__":
    unittest.main()
