# Source: stdlib unittest + MockCmd inject pattern (03-RESEARCH.md §7).
# Python 3.6 compatible (unittest, os.path -- all stdlib; NO pymol import).
#
# Pure-WSL unit tests for c14.pymol_layer.asset_manager.AssetManager. The
# module under test imports ONLY `os` + `c14.paths` (cmd is INJECTED), so
# these tests run under python3.6 with no pymol installed. A MockCmd records
# the dispatch (name/args/kwargs) and returns a configurable count_atoms so
# the post-condition branches are exercisable.
#
# The REAL cmd.* calls (cmd.load, cmd.fetch, cmd.count_atoms against the
# PyMOL 2.5.0 API) are verified by tools/asset_smoke.py (headless via
# tools/run_headless.sh) -- NOT these unit tests. Unit tests prove the
# dispatch/path/arg logic + the citation convention; the smoke proves the
# real API contract (3-tier testability pattern).
"""Unit tests for AssetManager (MockCmd dispatch/path/args + citations).

Pure WSL python3.6 -- NO pymol import. MockCmd records the cmd.* dispatch
(name, args, kwargs) and returns a configurable count_atoms for post-
condition branches. Verifies:
  * load_bundled resolves an ABSOLUTE bundled/ path (cwd-independent).
  * fetch_pubchem / fetch_pdb pass type=, async_=0, path=<abs downloaded dir>.
  * count_atoms <= 0 post-condition raises RuntimeError.
  * source-citation comments are present (SC #4 machine-checkable).
"""
import os
import unittest

from c14.pymol_layer.asset_manager import AssetManager


class MockCmd(object):
    """Records every cmd.* dispatch as (name, args, kwargs); returns 0.

    ``count_atoms`` is an EXPLICIT method (overrides the __getattr__ fallback)
    returning ``self._count`` so the AssetManager post-condition branches
    (``if count_atoms(...) <= 0: raise``) are exercisable: set ``mock._count``
    to 3 for the success path, 0 for the empty-object path. Explicit
    count_atoms is NOT recorded in self.calls (it is a post-condition probe,
    not a dispatched op) so ``calls[0]`` is always the load/fetch call.
    """

    def __init__(self):
        self.calls = []
        self._count = 3

    def __getattr__(self, name):
        # Returns a recording stub for any cmd.* attr except count_atoms
        # (which is an explicit method and bypasses __getattr__ entirely).
        def f(*a, **k):
            self.calls.append((name, a, k))
            return 0
        return f

    def count_atoms(self, sel="(all)"):
        # Explicit method -> normal attribute lookup finds this BEFORE
        # __getattr__ is consulted, so count_atoms is not recorded.
        return self._count


class TestAssetManagerLoadBundled(unittest.TestCase):
    """load_bundled: absolute bundled path + count_atoms post-condition."""

    def setUp(self):
        self.mock = MockCmd()
        self.am = AssetManager(self.mock)

    def test_load_bundled_calls_cmd_load_with_absolute_path(self):
        self.am.load_bundled("_smoke.pdb", "obj")
        # The first (and only) cmd.* dispatch is cmd.load with (abs_path, "obj").
        self.assertEqual(len(self.mock.calls), 1)
        name, args, kwargs = self.mock.calls[0]
        self.assertEqual(name, "load")
        self.assertEqual(args[1], "obj")
        self.assertEqual(kwargs, {})
        # The path MUST be absolute (cwd-independent -- Pitfall 1) and point
        # at the bundled/ dir containing the fixture.
        self.assertTrue(
            os.path.isabs(args[0]),
            "load path is not absolute: {0}".format(args[0]),
        )
        self.assertIn("bundled", args[0])
        self.assertIn("_smoke.pdb", args[0])

    def test_load_bundled_raises_on_empty_object(self):
        # count_atoms returns 0 -> post-condition (<= 0) raises RuntimeError.
        self.mock._count = 0
        with self.assertRaises(RuntimeError):
            self.am.load_bundled("_smoke.pdb", "obj")


class TestAssetManagerFetchPubchem(unittest.TestCase):
    """fetch_pubchem: type=/async_=0/path=<abs downloaded> + post-condition."""

    def setUp(self):
        self.mock = MockCmd()
        self.am = AssetManager(self.mock)

    def test_fetch_pubchem_passes_type_async_path(self):
        self.am.fetch_pubchem("2244", "asp")
        self.assertEqual(len(self.mock.calls), 1)
        name, args, kwargs = self.mock.calls[0]
        self.assertEqual(name, "fetch")
        self.assertEqual(args, ("2244", "asp"))
        # Pitfall 5 mitigations: type= (NOT CIF default), async_=0 (sync),
        # path=<abs downloaded dir> (NOT cwd).
        self.assertEqual(kwargs["type"], "cid")
        self.assertEqual(kwargs["async_"], 0)
        self.assertTrue(
            os.path.isabs(kwargs["path"]),
            "fetch path is not absolute: {0}".format(kwargs["path"]),
        )
        self.assertIn("downloaded", kwargs["path"])

    def test_fetch_pubchem_kind_sid(self):
        self.am.fetch_pubchem("2244", "asp", kind="sid")
        _, _, kwargs = self.mock.calls[0]
        self.assertEqual(kwargs["type"], "sid")

    def test_fetch_pubchem_raises_on_empty_object(self):
        self.mock._count = 0
        with self.assertRaises(RuntimeError):
            self.am.fetch_pubchem("2244", "asp")


class TestAssetManagerFetchPdb(unittest.TestCase):
    """fetch_pdb: type= defaults to pdb (NOT CIF), async_=0, path=<abs>."""

    def setUp(self):
        self.mock = MockCmd()
        self.am = AssetManager(self.mock)

    def test_fetch_pdb_passes_type_async_path(self):
        self.am.fetch_pdb("1crn", "crn")
        self.assertEqual(len(self.mock.calls), 1)
        name, args, kwargs = self.mock.calls[0]
        self.assertEqual(name, "fetch")
        self.assertEqual(args, ("1crn", "crn"))
        # Default ftype="pdb" (NOT the cmd.fetch CIF default -- Pitfall 5a).
        self.assertEqual(kwargs["type"], "pdb")
        self.assertEqual(kwargs["async_"], 0)
        self.assertTrue(
            os.path.isabs(kwargs["path"]),
            "fetch path is not absolute: {0}".format(kwargs["path"]),
        )
        self.assertIn("downloaded", kwargs["path"])

    def test_fetch_pdb_custom_ftype(self):
        self.am.fetch_pdb("1crn", "crn", ftype="cif")
        _, _, kwargs = self.mock.calls[0]
        self.assertEqual(kwargs["type"], "cif")


class TestSourceCitationsPresent(unittest.TestCase):
    """SC #4: every cmd.* call carries a # src: comment (machine-checkable)."""

    def test_citations_present_in_source(self):
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        src_path = os.path.join(repo, "c14", "pymol_layer", "asset_manager.py")
        with open(src_path, "r") as fh:
            src = fh.read()
        # cmd.load citation (importing.py:635) -- load_bundled.
        self.assertIn(
            "# src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load",
            src,
        )
        # cmd.fetch citation (importing.py:1323) -- fetch_pubchem + fetch_pdb.
        self.assertIn(
            "# src: tmp/pymol-src/modules/pymol/importing.py:1323 cmd.fetch",
            src,
        )


if __name__ == "__main__":
    unittest.main()
