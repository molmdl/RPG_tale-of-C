# Source: stdlib unittest + MockCmd/MockAssets inject pattern (03-RESEARCH.md
# section 7; reuses the inject-cmd pattern from tests/test_asset_manager.py).
# Python 3.6 compatible (unittest, os.path -- all stdlib; NO pymol import).
#
# Pure-WSL unit tests for c14.pymol_layer.molops.MolOps. The module under test
# imports ONLY `MolAction` from c14.story.model (which is pure data -- no
# pymol import) and has `cmd` + `asset_manager` INJECTED via the constructor,
# so these tests run under python3.6 with no pymol installed. A MockCmd
# records every cmd.* dispatch (name/args/kwargs); a MockAssets records every
# AssetManager delegation.
#
# The REAL cmd.* calls (hide/show/show_as/select/zoom/color/delete against the
# PyMOL 2.5.0 API) are verified by tools/molops_smoke.py (headless via
# tools/run_headless.sh) -- NOT these unit tests. Unit tests prove the
# per-op dispatch mapping + the Phase 4 NotImplementedError boundary + the
# citation convention; the smoke proves the real API contract + the `rep`
# keyword "representation visible" post-condition (3-tier testability pattern).
"""Unit tests for MolOps (MockCmd/MockAssets per-op dispatch + citations).

Pure WSL python3.6 -- NO pymol import. MockCmd records the cmd.* dispatch
(name, args, kwargs); MockAssets records every AssetManager delegation
(load_bundled/fetch_pubchem/fetch_pdb). Verifies:
  * The 8 implemented ops dispatch to the right cmd.*/AssetManager call with
    the right args (the MolAction -> cmd.* mapping table -- SC #3 logic).
  * `load` delegates to AssetManager per args["source"] (bundled/cid/pdb);
    defaults to "bundled"; raises RuntimeError if no AssetManager injected.
  * edit/protonate/restore/unknown raise NotImplementedError (explicit
    Phase 4 boundary).
  * source-citation comments are present on every direct cmd.* call (SC #4
    machine-checkable).
"""
import os
import unittest

from c14.pymol_layer.molops import MolOps
from c14.story.model import MolAction


class MockCmd(object):
    """Records every cmd.* dispatch as (name, args, kwargs); returns 0.

    ``count_atoms`` is an EXPLICIT method (overrides the __getattr__ fallback)
    returning ``self._count`` so post-condition probes in the smoke (NOT the
    unit tests here -- MolOps itself does not probe count_atoms) can be
    exercised. Explicit count_atoms is NOT recorded in self.calls so
    ``calls[0]`` is always the dispatched op (matches the Plan 02 MockCmd
    pattern; reused here for the MolOps dispatch tests).
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


class MockAssets(object):
    """Records every AssetManager delegation; returns the object_name.

    Mirrors the AssetManager method signatures (load_bundled/fetch_pubchem/
    fetch_pdb) so the MolOps `load` op delegation is unit-testable in pure
    WSL python3.6 with no real cmd/pymol. Each method records a tuple of its
    salient args so the tests can assert which delegate was called with what.
    """

    def __init__(self):
        self.calls = []

    def load_bundled(self, filename, object_name):
        self.calls.append(("load_bundled", filename, object_name))
        return object_name

    def fetch_pubchem(self, cid, object_name, kind="cid"):
        self.calls.append(("fetch_pubchem", cid, object_name, kind))
        return object_name

    def fetch_pdb(self, code, object_name, ftype="pdb"):
        self.calls.append(("fetch_pdb", code, object_name, ftype))
        return object_name


class TestMolOpsDispatch(unittest.TestCase):
    """One test per implemented op: assert the right cmd.* is called with right args."""

    def setUp(self):
        self.mock = MockCmd()
        self.molops = MolOps(self.mock)

    def test_hide_all(self):
        self.molops.apply(MolAction("hide_all"))
        self.assertEqual(self.mock.calls[0], ("hide", ("everything", "all"), {}))

    def test_show(self):
        self.molops.apply(MolAction("show", "obj", {"rep": "sticks"}))
        self.assertEqual(self.mock.calls[0], ("show", ("sticks", "obj"), {}))

    def test_show_with_sele(self):
        # sele from args OVERRIDES target (args["sele"] wins over action.target).
        self.molops.apply(
            MolAction("show", "obj", {"rep": "sticks", "sele": "obj and name CA"})
        )
        self.assertEqual(
            self.mock.calls[0], ("show", ("sticks", "obj and name CA"), {})
        )

    def test_show_as(self):
        self.molops.apply(MolAction("show_as", "obj", {"rep": "cartoon"}))
        self.assertEqual(self.mock.calls[0], ("show_as", ("cartoon", "obj"), {}))

    def test_select_focus(self):
        self.molops.apply(
            MolAction("select_focus", None, {"sele": "obj and name CA", "name": "focus"})
        )
        self.assertEqual(self.mock.calls[0], ("select", ("focus", "obj and name CA"), {}))

    def test_zoom(self):
        self.molops.apply(MolAction("zoom", "obj"))
        self.assertEqual(self.mock.calls[0], ("zoom", ("obj",), {}))

    def test_zoom_default_all(self):
        # target None -> "all" (action.target or "all" fallback).
        self.molops.apply(MolAction("zoom", None))
        self.assertEqual(self.mock.calls[0], ("zoom", ("all",), {}))

    def test_color(self):
        self.molops.apply(MolAction("color", "obj", {"color": "green"}))
        self.assertEqual(self.mock.calls[0], ("color", ("green", "obj"), {}))


class TestMolOpsLoad(unittest.TestCase):
    """`load` op delegates to AssetManager per args['source'] (bundled/cid/pdb)."""

    def setUp(self):
        self.mock = MockCmd()
        self.assets = MockAssets()
        self.molops = MolOps(self.mock, self.assets)

    def test_load_bundled_delegates(self):
        self.molops.apply(
            MolAction("load", "key", {"source": "bundled", "file": "f.pdb", "object": "obj"})
        )
        self.assertEqual(self.assets.calls[0], ("load_bundled", "f.pdb", "obj"))
        # No direct cmd.* call for the load op (delegation, not cmd.* dispatch).
        self.assertEqual(self.mock.calls, [])

    def test_load_cid_delegates(self):
        self.molops.apply(
            MolAction("load", "key", {"source": "cid", "cid": "2244", "object": "obj"})
        )
        self.assertEqual(self.assets.calls[0], ("fetch_pubchem", "2244", "obj", "cid"))

    def test_load_pdb_delegates(self):
        self.molops.apply(
            MolAction("load", "key", {"source": "pdb", "code": "1crn", "object": "obj"})
        )
        self.assertEqual(self.assets.calls[0], ("fetch_pdb", "1crn", "obj", "pdb"))

    def test_load_default_source_is_bundled(self):
        # No "source" key -> defaults to "bundled" (the AssetManager.load_bundled path).
        self.molops.apply(
            MolAction("load", "key", {"file": "f.pdb", "object": "obj"})
        )
        self.assertEqual(self.assets.calls[0], ("load_bundled", "f.pdb", "obj"))

    def test_load_without_assets_raises(self):
        # MolOps(mock) with NO AssetManager -> a `load` op raises RuntimeError.
        molops_no_assets = MolOps(self.mock)
        with self.assertRaises(RuntimeError):
            molops_no_assets.apply(MolAction("load", "key", {"file": "f.pdb"}))


class TestMolOpsPhase4Boundary(unittest.TestCase):
    """edit/protonate/restore/unknown raise NotImplementedError (Phase 4 boundary)."""

    def setUp(self):
        self.molops = MolOps(MockCmd())

    def test_edit_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.molops.apply(MolAction("edit", "obj"))

    def test_protonate_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.molops.apply(MolAction("protonate", "obj"))

    def test_restore_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.molops.apply(MolAction("restore", "obj"))

    def test_unknown_op_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.molops.apply(MolAction("frobnicate", "obj"))


class TestSourceCitationsPresent(unittest.TestCase):
    """SC #4: every direct cmd.* call in molops.py carries a # src: comment."""

    def test_citations_present_in_source(self):
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        src_path = os.path.join(repo, "c14", "pymol_layer", "molops.py")
        with open(src_path, "r") as fh:
            src = fh.read()
        # One citation per direct self._cmd.* call site (7 total):
        # hide, show, show_as, select, zoom, color, delete.
        expected = [
            "# src: tmp/pymol-src/modules/pymol/viewing.py:568 cmd.hide",
            "# src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show",
            "# src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as",
            "# src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom",
            "# src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color",
            "# src: tmp/pymol-src/modules/pymol/selecting.py:48 cmd.select",
            "# src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete",
        ]
        for citation in expected:
            self.assertIn(
                citation, src,
                "missing source citation: {0}".format(citation),
            )


if __name__ == "__main__":
    unittest.main()
