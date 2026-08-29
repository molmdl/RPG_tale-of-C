# Source: stdlib unittest + MockCmd/MockAssets/MockEditOps/MockProtonationManager
# inject pattern (03-RESEARCH.md section 7; reuses the inject-cmd pattern from
# tests/test_asset_manager.py; extended in Phase 4 Plan 04-05 for the
# edit/restore/protonate delegation branches).
# Python 3.6 compatible (unittest, os.path -- all stdlib; NO pymol import).
#
# Pure-WSL unit tests for c14.pymol_layer.molops.MolOps. The module under test
# imports ONLY `MolAction` from c14.story.model (which is pure data -- no
# pymol import) and has `cmd` + `asset_manager` + `editops` + `protonation`
# INJECTED via the constructor, so these tests run under python3.6 with no
# pymol installed. A MockCmd records every cmd.* dispatch (name/args/kwargs);
# a MockAssets records every AssetManager delegation; a MockEditOps records
# every EditOps convenience-method call (point_mutation / substrate_remove_group
# / substrate_add_group / protonation_change / restore); a
# MockProtonationManager records apply_variant calls.
#
# The REAL cmd.* calls (hide/show/show_as/select/zoom/color/delete against the
# PyMOL 2.5.0 API) are verified by tools/molops_smoke.py (headless via
# tools/run_headless.sh) -- NOT these unit tests. The REAL cmd.* contract for
# the edit/restore/protonate delegation branches is verified by
# tools/edit_smoke.py + tools/protonation_smoke.py (04-05 headless smokes).
# Unit tests prove the per-op dispatch mapping + the Phase 4 delegation
# boundary + the citation convention; the smokes prove the real API contract +
# the `rep` keyword "representation visible" post-condition (3-tier
# testability pattern).
"""Unit tests for MolOps (MockCmd/MockAssets/MockEditOps/MockProtonationManager
per-op dispatch + citations).

Pure WSL python3.6 -- NO pymol import. MockCmd records the cmd.* dispatch
(name, args, kwargs); MockAssets records every AssetManager delegation
(load_bundled/fetch_pubchem/fetch_pdb); MockEditOps records every EditOps
convenience-method call; MockProtonationManager records apply_variant calls.
Verifies:
  * The 8 implemented ops dispatch to the right cmd.*/AssetManager call with
    the right args (the MolAction -> cmd.* mapping table -- SC #3 logic).
  * `load` delegates to AssetManager per args["source"] (bundled/cid/pdb);
    defaults to "bundled"; raises RuntimeError if no AssetManager injected.
  * edit/protonate/restore DELEGATE to EditOps/ProtonationManager (Phase 4
    Plan 04-05 -- no more NotImplementedError for these 3 ops). Without the
    injected helper, they raise RuntimeError (backward-compatible: MolOps(cmd)
    with no editops/protonation fails loudly, but with RuntimeError instead of
    NotImplementedError). Unknown edit_type raises ValueError. Unknown ops
    STILL raise NotImplementedError (a stray op fails loudly).
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


class MockEditOps(object):
    """Records every EditOps convenience-method call; returns a sentinel handle.

    Mirrors the EditOps method signatures (point_mutation /
    substrate_remove_group / substrate_add_group / protonation_change /
    restore) so the MolOps `edit` + `restore` op delegation is unit-testable
    in pure WSL python3.6 with no real cmd/pymol/edit_ops. Each method records
    a tuple of its salient args so the tests can assert which method was called
    with what (mirrors the MockAssets + MockCmd pattern).
    """

    def __init__(self):
        self.calls = []  # list of (method_name, salient_args_tuple)

    def point_mutation(self, object_name, sele, new_resn):
        self.calls.append(
            ("point_mutation", (object_name, sele, new_resn)))
        return "handle_point_mutation"

    def substrate_remove_group(self, object_name, group_sele):
        self.calls.append(
            ("substrate_remove_group", (object_name, group_sele)))
        return "handle_remove"

    def substrate_add_group(self, object_name, frag_atom_sele, target_atom_sele):
        self.calls.append(
            ("substrate_add_group",
             (object_name, frag_atom_sele, target_atom_sele)))
        return "handle_add"

    def protonation_change(self, object_name, sele, new_resn, h_ops=None):
        self.calls.append(
            ("protonation_change", (object_name, sele, new_resn, h_ops)))
        return "handle_protonation"

    def restore(self, object_name):
        self.calls.append(("restore", (object_name,)))
        return object_name


class MockProtonationManager(object):
    """Records every ProtonationManager.apply_variant call.

    Mirrors the ProtonationManager.apply_variant signature so the MolOps
    `protonate` op delegation is unit-testable in pure WSL python3.6 with no
    real cmd/pymol/protonation. Records the (target, variant_id) tuple.
    """

    def __init__(self):
        self.calls = []  # list of ("apply_variant", (target, variant_id))

    def apply_variant(self, target, variant_id):
        self.calls.append(("apply_variant", (target, variant_id)))
        return variant_id


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


class TestMolOpsEditProtonateRestoreDelegation(unittest.TestCase):
    """Phase 4 (04-05): edit/protonate/restore delegate to EditOps +
    ProtonationManager (no more NotImplementedError for these 3 ops).

    Without the injected helper, they raise RuntimeError (backward-compatible:
    MolOps(cmd) with no editops/protonation fails loudly, but with RuntimeError
    instead of NotImplementedError). Unknown edit_type raises ValueError.
    Unknown ops STILL raise NotImplementedError (a stray op fails loudly).
    """

    def test_edit_raises_runtime_error_without_editops(self):
        # MolOps(cmd) with NO editops -> a `edit` op raises RuntimeError (NOT
        # NotImplementedError -- the Phase 4 boundary is now a RuntimeError that
        # names the missing dep; the op IS implemented, just needs its helper).
        molops = MolOps(MockCmd())
        with self.assertRaises(RuntimeError):
            molops.apply(MolAction("edit", "obj", {"edit_type": "point_mutation"}))

    def test_protonate_raises_runtime_error_without_protonation(self):
        molops = MolOps(MockCmd())
        with self.assertRaises(RuntimeError):
            molops.apply(MolAction("protonate", "obj", {"variant_id": "HIS_HID"}))

    def test_restore_raises_runtime_error_without_editops(self):
        molops = MolOps(MockCmd())
        with self.assertRaises(RuntimeError):
            molops.apply(MolAction("restore", "obj"))

    def test_unknown_op_raises_not_implemented(self):
        # Genuinely unknown ops still raise NotImplementedError (the Phase 4
        # boundary is preserved for ops molops doesn't know about; edit/
        # protonate/restore are now implemented + delegated above).
        molops = MolOps(MockCmd())
        with self.assertRaises(NotImplementedError):
            molops.apply(MolAction("frobnicate", "obj"))

    def test_edit_delegates_to_editops_point_mutation(self):
        # MolOps(cmd, editops=mock) + apply(MolAction("edit",...,"point_mutation"))
        # -> mock_editops.point_mutation(target, sele, new_resn) called with the
        # right args (the Phase 4 delegation contract).
        mock_editops = MockEditOps()
        molops = MolOps(MockCmd(), editops=mock_editops)
        molops.apply(MolAction("edit", "pep", {
            "edit_type": "point_mutation",
            "sele": "pep and resi 1",
            "new_resn": "GLY",
        }))
        self.assertEqual(
            mock_editops.calls[0],
            ("point_mutation", ("pep", "pep and resi 1", "GLY")))

    def test_edit_delegates_to_editops_protonation_change(self):
        # edit_type="protonation_change" with h_ops -> the 4th convenience
        # method (protonation_change) is called with (target, sele, new_resn,
        # h_ops). The h_ops default is None if omitted (action.args.get).
        mock_editops = MockEditOps()
        molops = MolOps(MockCmd(), editops=mock_editops)
        h_ops = [{"op": "remove", "sele": "resn HIS and name HE2"}]
        molops.apply(MolAction("edit", "pep", {
            "edit_type": "protonation_change",
            "sele": "pep and resi 1",
            "new_resn": "HID",
            "h_ops": h_ops,
        }))
        self.assertEqual(
            mock_editops.calls[0],
            ("protonation_change", ("pep", "pep and resi 1", "HID", h_ops)))

    def test_edit_delegates_to_editops_substrate_remove_group(self):
        mock_editops = MockEditOps()
        molops = MolOps(MockCmd(), editops=mock_editops)
        molops.apply(MolAction("edit", "pep", {
            "edit_type": "substrate_remove_group",
            "group_sele": "pep and resi 2 and name CA",
        }))
        self.assertEqual(
            mock_editops.calls[0],
            ("substrate_remove_group", ("pep", "pep and resi 2 and name CA")))

    def test_edit_delegates_to_editops_substrate_add_group(self):
        mock_editops = MockEditOps()
        molops = MolOps(MockCmd(), editops=mock_editops)
        molops.apply(MolAction("edit", "pep", {
            "edit_type": "substrate_add_group",
            "frag_atom_sele": "frag and name C1",
            "target_atom_sele": "pep and name C2",
        }))
        self.assertEqual(
            mock_editops.calls[0],
            ("substrate_add_group", ("pep", "frag and name C1", "pep and name C2")))

    def test_edit_unknown_edit_type_raises_value_error(self):
        # An edit_type molops doesn't recognize raises ValueError (not
        # NotImplementedError -- the op IS "edit", but the edit_type is bogus).
        mock_editops = MockEditOps()
        molops = MolOps(MockCmd(), editops=mock_editops)
        with self.assertRaises(ValueError):
            molops.apply(MolAction("edit", "pep", {"edit_type": "bogus"}))

    def test_protonate_delegates_to_protonation_manager(self):
        # MolOps(cmd, protonation=mock) + apply(MolAction("protonate",...,
        # variant_id)) -> mock_pm.apply_variant(target, variant_id) called.
        mock_pm = MockProtonationManager()
        molops = MolOps(MockCmd(), protonation=mock_pm)
        molops.apply(MolAction("protonate", "scene", {"variant_id": "HIS_HID"}))
        self.assertEqual(
            mock_pm.calls[0], ("apply_variant", ("scene", "HIS_HID")))

    def test_restore_delegates_to_editops(self):
        # MolOps(cmd, editops=mock) + apply(MolAction("restore", target)) ->
        # mock_editops.restore(target) called (the EDIT-05 safety net entry).
        mock_editops = MockEditOps()
        molops = MolOps(MockCmd(), editops=mock_editops)
        molops.apply(MolAction("restore", "pep"))
        self.assertEqual(mock_editops.calls[0], ("restore", ("pep",)))


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


class TestMolOpsDeferredDispatch(unittest.TestCase):
    """Phase 6 (06-01): the 4 deferred dispatches (set_color/label/set/align
    from 5.4/5.3) map MolAction -> self._cmd.* with the right args.

    Reuses the existing MockCmd at test_molops.py:54-80 (records (name, args,
    kwargs) via __getattr__; count_atoms is an explicit method). Proves the
    per-op dispatch mapping; the REAL cmd.* contract is deferred to the
    headless smoke (tools/molops_deferred_dispatch_smoke.py -- Task 3). Covers
    the quoted-string label footgun, the cealign REVERSED arg order, the
    align_sele composition, and ValueError on an unknown align method.
    """

    def setUp(self):
        self.mock = MockCmd()
        self.molops = MolOps(self.mock)

    def test_set_color_dispatch(self):
        # set_color(name, rgb) -- the 5.4 hero_cyan palette (idempotent define).
        self.molops.apply(MolAction(
            "set_color", None, {"name": "hero_cyan", "rgb": [0.0, 0.75, 0.75]}))
        self.assertEqual(
            self.mock.calls[0],
            ("set_color", ("hero_cyan", [0.0, 0.75, 0.75]), {}))

    def test_label_dispatch_quotes_text(self):
        # The label expression is a QUOTED STRING '"YOU"' -- a bare "YOU"
        # would eval the atom property `YOU` (the footgun the dispatch
        # encapsulates; 05.4-CONVENTION.md section 2.1 / viewing.py:1332).
        self.molops.apply(MolAction("label", "hero_atom", {"text": "YOU"}))
        self.assertEqual(
            self.mock.calls[0], ("label", ("hero_atom", '"YOU"'), {}))

    def test_label_sele_defaults_to_target(self):
        # No "sele" key -> defaults to action.target ("hero_atom").
        self.molops.apply(MolAction("label", "hero_atom", {"text": "YOU"}))
        self.assertEqual(self.mock.calls[0][1][0], "hero_atom")

    def test_label_sele_explicit(self):
        # Explicit sele OVERRIDES target (args["sele"] wins).
        self.molops.apply(MolAction(
            "label", "hero_atom",
            {"sele": "mol and name C1", "text": "YOU"}))
        self.assertEqual(self.mock.calls[0][1][0], "mol and name C1")

    def test_label_clear_empty_text(self):
        # Empty text -> expression '""' (empty quoted string clears the label;
        # mirrors hero_highlight_smoke.py Stage 4 climax fade).
        self.molops.apply(MolAction("label", "hero_atom", {"text": ""}))
        self.assertEqual(self.mock.calls[0][1][1], '""')

    def test_set_dispatch(self):
        # set(name, value, sele) -- selection is 3rd positional, defaults to
        # target (the 5.4 ball-and-stick sphere_scale setting).
        self.molops.apply(MolAction(
            "set", "hero_atom", {"name": "sphere_scale", "value": 0.3}))
        self.assertEqual(
            self.mock.calls[0],
            ("set", ("sphere_scale", 0.3, "hero_atom"), {}))

    def test_set_sele_explicit(self):
        # Explicit sele OVERRIDES target as the 3rd positional arg.
        self.molops.apply(MolAction(
            "set", "hero_atom",
            {"name": "sphere_scale", "value": 0.3, "sele": "mol and name C1"}))
        self.assertEqual(self.mock.calls[0][1][2], "mol and name C1")

    def test_align_super_dispatch(self):
        # cmd.super(mobile, target) -- mobile MOVED, reference=fixed FIXED
        # (fitting.py:242 arg order; mobile first, reference second).
        self.molops.apply(MolAction(
            "align", "mol_a", {"reference": "mol_b", "method": "super"}))
        self.assertEqual(
            self.mock.calls[0], ("super", ("mol_a", "mol_b"), {}))

    def test_align_default_method_is_super(self):
        # Omit "method" -> defaults to "super" -> cmd.super called.
        self.molops.apply(MolAction("align", "mol_a", {"reference": "mol_b"}))
        self.assertEqual(self.mock.calls[0][0], "super")

    def test_align_cealign_reversed_args(self):
        # cmd.cealign(target, mobile) -- arg order is REVERSED per
        # fitting.py:27 (target=fixed FIRST, mobile SECOND). The dispatch
        # normalizes the reversal so callers always pass (mobile, reference)
        # and the dispatch swaps for cealign only.
        self.molops.apply(MolAction(
            "align", "mol_a", {"reference": "mol_b", "method": "cealign"}))
        self.assertEqual(
            self.mock.calls[0], ("cealign", ("mol_b", "mol_a"), {}))

    def test_align_method_align(self):
        # method="align" -> cmd.align(mobile, ref) (NOT reversed; same order
        # as super per fitting.py:306).
        self.molops.apply(MolAction(
            "align", "mol_a", {"reference": "mol_b", "method": "align"}))
        self.assertEqual(
            self.mock.calls[0], ("align", ("mol_a", "mol_b"), {}))

    def test_align_align_sele_composition(self):
        # align_sele composes "{target} and {sele}" for BOTH mobile AND ref
        # (the substructure scope -- 05.3-CONVENTION.md section 4).
        self.molops.apply(MolAction(
            "align", "mol_a",
            {"reference": "mol_b", "align_sele": "name CA"}))
        mobile_arg, ref_arg = self.mock.calls[0][1]
        self.assertEqual(mobile_arg, "mol_a and name CA")
        self.assertEqual(ref_arg, "mol_b and name CA")

    def test_align_unknown_method_raises_valueerror(self):
        # An align method molops doesn't recognize raises ValueError (NOT
        # NotImplementedError -- the op IS "align", but the method is bogus).
        with self.assertRaises(ValueError):
            self.molops.apply(MolAction(
                "align", "mol_a", {"reference": "mol_b", "method": "quaternion"}))

    def test_set_color_then_label_then_set_citations_present(self):
        # SC#4: every direct self._cmd.* call in the 4 new branches carries a
        # `# src: tmp/pymol-src` citation (mirrors TestSourceCitationsPresent
        # for the 8 original ops). One citation per cmd.* call site -- the
        # align branch has 3 (super/align/cealign), so 6 citations across 4 ops.
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        src_path = os.path.join(repo, "c14", "pymol_layer", "molops.py")
        with open(src_path, "r") as fh:
            src = fh.read()
        expected = [
            "# src: tmp/pymol-src/modules/pymol/viewing.py:2107 cmd.set_color",
            "# src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label",
            "# src: tmp/pymol-src/modules/pymol/setting.py:183 cmd.set",
            "# src: tmp/pymol-src/modules/pymol/fitting.py:242 cmd.super",
            "# src: tmp/pymol-src/modules/pymol/fitting.py:306 cmd.align",
            "# src: tmp/pymol-src/modules/pymol/fitting.py:27 cmd.cealign",
        ]
        for citation in expected:
            self.assertIn(
                citation, src,
                "missing source citation: {0}".format(citation),
            )


class TestMolOpsLoadTargetPrefix(unittest.TestCase):
    """Phase 6 (06-01): the `load` branch target-prefix fallback parses
    action.target = "pdb:XXX"/"cid:XXX"/"sid:XXX"/<bundled-filename> when no
    source/file/code/cid keys are present (the 5.1 skeleton on_enter form).

    Reuses the existing MockAssets at test_molops.py:86-105 (records
    (fetch_pubchem cid obj kind) / (fetch_pdb code obj fte) / (load_bundled
    filename obj)). The explicit-source backward-compat path (test_molops.py
    220-251) is regression-guarded by test_load_explicit_source_still_works.
    """

    def setUp(self):
        self.mock = MockCmd()
        self.assets = MockAssets()
        self.molops = MolOps(self.mock, self.assets)

    def test_load_target_pdb_prefix(self):
        # "pdb:4PFK" prefix stripped -> fetch_pdb("4PFK", "pfk"); object from
        # args (NOT the full "pdb:4PFK" string).
        self.molops.apply(MolAction("load", "pdb:4PFK", {"object": "pfk"}))
        self.assertEqual(
            self.assets.calls[0], ("fetch_pdb", "4PFK", "pfk", "pdb"))

    def test_load_target_cid_prefix(self):
        # "cid:2244" prefix stripped -> fetch_pubchem("2244", "sub", kind="cid").
        self.molops.apply(MolAction("load", "cid:2244", {"object": "sub"}))
        self.assertEqual(
            self.assets.calls[0], ("fetch_pubchem", "2244", "sub", "cid"))

    def test_load_target_sid_prefix(self):
        # "sid:2244" prefix stripped -> fetch_pubchem("2244", "sub", kind="sid").
        self.molops.apply(MolAction("load", "sid:2244", {"object": "sub"}))
        self.assertEqual(
            self.assets.calls[0], ("fetch_pubchem", "2244", "sub", "sid"))

    def test_load_target_bundled_no_prefix(self):
        # Bare filename (no prefix) -> load_bundled(target, object); NO network.
        self.molops.apply(MolAction("load", "_smoke.pdb", {"object": "mol"}))
        self.assertEqual(
            self.assets.calls[0], ("load_bundled", "_smoke.pdb", "mol"))

    def test_load_target_pdb_no_object_defaults_to_stripped_code(self):
        # No "object" key -> object defaults to the stripped code "4PFK" (NOT
        # the full "pdb:4PFK" string -- avoids a colon in the object name).
        self.molops.apply(MolAction("load", "pdb:4PFK", {}))
        self.assertEqual(
            self.assets.calls[0], ("fetch_pdb", "4PFK", "4PFK", "pdb"))

    def test_load_target_bundled_no_object_defaults_to_target(self):
        # No "object" key + bare filename -> object defaults to the target
        # itself (the filename).
        self.molops.apply(MolAction("load", "_smoke.pdb", {}))
        self.assertEqual(
            self.assets.calls[0], ("load_bundled", "_smoke.pdb", "_smoke.pdb"))

    def test_load_no_source_no_file_no_target_raises_valueerror(self):
        # No source, no file, no target (target is None) -> ValueError (the
        # branch cannot resolve what to load -- fail loudly, NOT a KeyError).
        with self.assertRaises(ValueError):
            self.molops.apply(MolAction("load", None, {"object": "x"}))

    def test_load_explicit_source_still_works_backward_compat(self):
        # REGRESSION GUARD: the load-branch rewrite must NOT break the 4
        # explicit-source forms at test_molops.py:220-251 (source:bundled+file,
        # source:cid+cid, source:pdb+code, no-source+file). Each must STILL
        # delegate identically to the same AssetManager method with the same
        # args (the explicit-source branches are UNCHANGED; the bundled branch
        # checks "file" in args FIRST before the target-prefix fallback).
        # 1) source:bundled + file -> load_bundled("f.pdb", "obj")
        self.molops.apply(MolAction(
            "load", "key", {"source": "bundled", "file": "f.pdb", "object": "obj"}))
        self.assertEqual(self.assets.calls[0], ("load_bundled", "f.pdb", "obj"))
        # 2) source:cid + cid -> fetch_pubchem("2244", "obj", "cid")
        self.assets.calls = []
        self.molops.apply(MolAction(
            "load", "key", {"source": "cid", "cid": "2244", "object": "obj"}))
        self.assertEqual(
            self.assets.calls[0], ("fetch_pubchem", "2244", "obj", "cid"))
        # 3) source:pdb + code -> fetch_pdb("1crn", "obj", "pdb")
        self.assets.calls = []
        self.molops.apply(MolAction(
            "load", "key", {"source": "pdb", "code": "1crn", "object": "obj"}))
        self.assertEqual(
            self.assets.calls[0], ("fetch_pdb", "1crn", "obj", "pdb"))
        # 4) no-source + file -> load_bundled("f.pdb", "obj") (default source)
        self.assets.calls = []
        self.molops.apply(MolAction(
            "load", "key", {"file": "f.pdb", "object": "obj"}))
        self.assertEqual(self.assets.calls[0], ("load_bundled", "f.pdb", "obj"))


if __name__ == "__main__":
    unittest.main()
