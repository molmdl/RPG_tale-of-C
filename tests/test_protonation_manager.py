# Source: stdlib unittest + MockCmd/MockEditOps/MockCatalog/MockAssets inject
# pattern (04-RESEARCH-protonation.md "Pattern 1: 3-Tier Testability"; reuses
# the inject pattern from tests/test_molops.py:39-65 + tests/test_edit_ops.py).
# Python 3.6 compatible (unittest, os -- all stdlib; NO pymol import).
#
# Pure-WSL unit tests for c14.pymol_layer.protonation.ProtonationManager. The
# module under test has cmd + edit_ops + catalog + assets INJECTED via the
# constructor (NO pymol import at module top), so these tests run under
# python3.6 with no pymol installed. MockCmd records cmd.* dispatches;
# MockEditOps records apply_edit/take_backup/restore_from_handle calls;
# MockCatalog is the real c14.protonation_catalog module (pure data); MockAssets
# records load_bundled calls.
#
# The REAL cmd.* sequence is verified by tools/protonation_smoke.py (04-05,
# headless via tools/run_headless.sh) -- NOT these unit tests. Unit tests
# prove: dispatch through edit_ops (no direct alter/h_add), Mode a/b routing,
# switch state, restore clears state, no-direct-alter gate guard, step
# ordering (Pitfall 2), citation presence.
"""Unit tests for ProtonationManager (MockCmd/MockEditOps dispatch + switch
state + restore + sanctioned-alter gate guard + step ordering).

Pure WSL python3.6 -- NO pymol import. Verifies:
  * apply_variant Mode (b) routes through edit_ops.apply_edit (NOT direct
    cmd.alter/cmd.h_add) with steps ordered removes -> alter -> h_add
    (Pitfall 2).
  * apply_variant Mode (a) routes through edit_ops.take_backup +
    cmd.delete + assets.load_bundled (NOT edit_ops.apply_edit).
  * switch_variant / apply_variant record state (current_variant).
  * restore clears state + delegates to edit_ops.restore_from_handle.
  * Unknown residue / variant raise KeyError (delegated to catalog.lookup).
  * list_variants delegates to catalog.variants_for.
  * NO self._cmd.alter( or self._cmd.h_add( in protonation.py source
    (the alter gate allowlist stays at edit_ops.py only).
  * Source-citation comments present on every direct self._cmd.* call.
"""
import ast
import os
import unittest

import c14.protonation_catalog as catalog_mod
from c14.pymol_layer.protonation import ProtonationManager


# ----------------------------------------------------------------------
# Mocks
# ----------------------------------------------------------------------

class MockCmd(object):
    """Records every cmd.* dispatch as (name, args, kwargs); returns 0.

    delete is an explicit method (so it's recorded predictably); other
    attrs use __getattr__ fallback. count_atoms returns a configurable int
    (not recorded -- mirrors tests/test_edit_ops.py MockCmd precedent)."""

    def __init__(self):
        self.calls = []
        self._count = 3

    def __getattr__(self, name):
        # Returns a recording stub for any cmd.* attr not explicitly defined.
        def f(*a, **k):
            self.calls.append((name, a, k))
            return 0
        return f

    def delete(self, name):
        # Explicit so the recording is predictable + the Mode-a path reads
        # cleanly. (Still recorded, like __getattr__ would.)
        self.calls.append(("delete", (name,), {}))
        return 0

    def count_atoms(self, sel="(all)"):
        # Explicit -> not recorded (mirrors test_edit_ops MockCmd precedent).
        return self._count


class MockEditOps(object):
    """Records apply_edit / take_backup / restore_from_handle / restore calls.

    apply_edit(object_name, steps) records (name, object_name, steps) and
    returns a sentinel handle (a small dict so tests can assert it's stored).
    take_backup(object_name) records + returns a sentinel handle. restore /
    restore_from_handle record the call (the ProtonationManager uses
    restore_from_handle for its self-managed handle)."""

    def __init__(self):
        self.calls = []  # list of (name, args...)
        self._apply_edit_calls = []  # (object_name, steps)
        self._take_backup_calls = []  # object_name
        self._restore_from_handle_calls = []  # handle
        self._restore_calls = []  # object_name
        self._handle_counter = 0

    def apply_edit(self, object_name, edit_steps):
        self.calls.append(("apply_edit", object_name, edit_steps))
        self._apply_edit_calls.append((object_name, edit_steps))
        self._handle_counter += 1
        return {"_sentinel": "handle", "_n": self._handle_counter,
                "object_name": object_name}

    def take_backup(self, object_name):
        self.calls.append(("take_backup", object_name))
        self._take_backup_calls.append(object_name)
        self._handle_counter += 1
        return {"_sentinel": "handle", "_n": self._handle_counter,
                "object_name": object_name}

    def restore_from_handle(self, handle):
        self.calls.append(("restore_from_handle", handle))
        self._restore_from_handle_calls.append(handle)
        return handle.get("object_name") if isinstance(handle, dict) else None

    def restore(self, object_name):
        self.calls.append(("restore", object_name))
        self._restore_calls.append(object_name)
        return object_name


class MockAssets(object):
    """Records load_bundled(filename, object_name) calls."""

    def __init__(self):
        self.calls = []

    def load_bundled(self, filename, object_name):
        self.calls.append(("load_bundled", filename, object_name))
        return object_name


# A small Mode-(a) catalog for the load-routing test. The real
# c14.protonation_catalog ships only Mode-(b) alter entries in Phase 4; this
# fake catalog lets us exercise Mode (a) dispatch without touching the real
# CATALOG. Matches the schema (mode=load, source_file, claim_id, label).
LOAD_CATALOG = {
    "LOADME": {
        "LOADME_X": {
            "mode": "load",
            "source_file": "x.pdb",
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Load-mode test variant",
        },
    },
}


def _make_load_catalog_module():
    """Build a fake catalog module-like object with lookup/variants_for."""
    class _LoadCatalog(object):
        CATALOG = LOAD_CATALOG

        @staticmethod
        def lookup(residue_key, variant_id):
            group = LOAD_CATALOG.get(residue_key)
            if group is None:
                raise KeyError(
                    "protonation_catalog: unknown residue {!r}".format(
                        residue_key))
            spec = group.get(variant_id)
            if spec is None:
                raise KeyError(
                    "protonation_catalog: unknown variant {!r} for residue "
                    "{!r}".format(variant_id, residue_key))
            return spec

        @staticmethod
        def variants_for(residue_key):
            group = LOAD_CATALOG.get(residue_key, {})
            return [(vid, s.get("label", vid)) for vid, s in group.items()]

        @staticmethod
        def residues():
            return sorted(LOAD_CATALOG.keys())
    return _LoadCatalog


def _read_protonation_source():
    """Read c14/pymol_layer/protonation.py as text (for citation/gate tests)."""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_path = os.path.join(repo, "c14", "pymol_layer", "protonation.py")
    with open(src_path, "r") as fh:
        return fh.read()


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

class TestApplyVariantAlter(unittest.TestCase):
    """Mode (b) alter: routes through edit_ops.apply_edit (NOT direct
    cmd.alter/cmd.h_add); steps ordered removes -> alter -> h_add (Pitfall 2)."""

    def setUp(self):
        self.mock_cmd = MockCmd()
        self.mock_edit = MockEditOps()
        self.mock_assets = MockAssets()
        self.pm = ProtonationManager(
            self.mock_cmd, self.mock_edit, catalog_mod, self.mock_assets)

    def test_apply_variant_alter_routes_through_edit_ops(self):
        """apply_variant('HIS','HIS_HID') calls mock_edit.apply_edit('HIS',
        steps) with steps = [remove('resn HIS and name HE2'),
        alter('HIS', "resn='HID'"), h_add('resn HID and name ND1')] in THIS
        ORDER (removes -> alter -> adds -- Pitfall 2). Assert mock_edit.
        apply_edit was called; assert mock_cmd.alter was NOT called directly
        (sanctioned-alter gate)."""
        self.pm.apply_variant("HIS", "HIS_HID")
        # apply_edit was called exactly once with target "HIS".
        self.assertEqual(len(self.mock_edit._apply_edit_calls), 1)
        obj, steps = self.mock_edit._apply_edit_calls[0]
        self.assertEqual(obj, "HIS")
        # The steps list has exactly 3 entries: remove, alter, h_add.
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0]["op"], "remove")
        self.assertEqual(steps[0]["sele"], "resn HIS and name HE2")
        self.assertEqual(steps[1]["op"], "alter")
        self.assertEqual(steps[1]["sele"], "HIS")
        self.assertEqual(steps[1]["expr"], "resn='HID'")
        self.assertEqual(steps[2]["op"], "h_add")
        self.assertEqual(steps[2]["sele"], "resn HID and name ND1")
        # mock_cmd.alter was NOT called directly (sanctioned-alter gate).
        alter_calls = [c for c in self.mock_cmd.calls if c[0] == "alter"]
        self.assertEqual(alter_calls, [],
                         "Mode (b) must NOT call cmd.alter directly -- "
                         "routes through edit_ops.apply_edit")
        # mock_cmd.h_add was NOT called directly.
        h_add_calls = [c for c in self.mock_cmd.calls if c[0] == "h_add"]
        self.assertEqual(h_add_calls, [],
                         "Mode (b) must NOT call cmd.h_add directly -- "
                         "routes through edit_ops.apply_edit")

    def test_apply_variant_alter_step_order_remove_before_alter_before_add(self):
        """For HIS_HID, the steps passed to mock_edit.apply_edit have the
        remove step FIRST, the alter step SECOND, the h_add step LAST (the
        Pitfall 2 ordering -- removes while resn is still HIS, alter to HID,
        then h_add while resn is HID)."""
        self.pm.apply_variant("HIS", "HIS_HID")
        _, steps = self.mock_edit._apply_edit_calls[0]
        ops = [s["op"] for s in steps]
        self.assertEqual(ops, ["remove", "alter", "h_add"],
                         "Pitfall 2: steps must be removes -> alter -> adds")

    def test_apply_variant_alter_hip_has_two_adds_no_removes(self):
        """HIS_HIP has 2 add ops (no removes): steps = [alter, h_add, h_add].
        Verifies the partition handles the no-removes + multi-adds case."""
        self.pm.apply_variant("HIS", "HIS_HIP")
        _, steps = self.mock_edit._apply_edit_calls[0]
        ops = [s["op"] for s in steps]
        self.assertEqual(ops, ["alter", "h_add", "h_add"])

    def test_apply_variant_alter_asp_no_h_ops(self):
        """ASP_ASP has empty h_ops: steps = [alter] only (no removes, no adds).
        Verifies the partition handles the empty-h_ops case."""
        self.pm.apply_variant("ASP", "ASP_ASP")
        _, steps = self.mock_edit._apply_edit_calls[0]
        ops = [s["op"] for s in steps]
        self.assertEqual(ops, ["alter"])

    def test_apply_variant_alter_records_backup_handle(self):
        """After apply_variant Mode (b), self._backup[target] holds the handle
        returned by edit_ops.apply_edit (so restore can use it)."""
        self.pm.apply_variant("HIS", "HIS_HID")
        self.assertIn("HIS", self.pm._backup)
        handle = self.pm._backup["HIS"]
        self.assertEqual(handle.get("object_name"), "HIS")


class TestApplyVariantLoad(unittest.TestCase):
    """Mode (a) load: routes through edit_ops.take_backup + cmd.delete +
    assets.load_bundled (NOT edit_ops.apply_edit)."""

    def setUp(self):
        self.mock_cmd = MockCmd()
        self.mock_edit = MockEditOps()
        self.mock_assets = MockAssets()
        self.pm = ProtonationManager(
            self.mock_cmd, self.mock_edit, _make_load_catalog_module(),
            self.mock_assets)

    def test_apply_variant_load_routes_through_assets(self):
        """A Mode (a) variant (mode=load, source_file='x.pdb'):
        apply_variant calls mock_edit.take_backup THEN mock_cmd.delete THEN
        mock_assets.load_bundled; does NOT call mock_edit.apply_edit."""
        self.pm.apply_variant("LOADME", "LOADME_X")
        # take_backup was called first.
        self.assertEqual(self.mock_edit._take_backup_calls, ["LOADME"])
        # cmd.delete was called (the only direct cmd.* call in Mode a).
        delete_calls = [c for c in self.mock_cmd.calls if c[0] == "delete"]
        self.assertEqual(len(delete_calls), 1)
        self.assertEqual(delete_calls[0][1], ("LOADME",))
        # assets.load_bundled was called with the right args.
        self.assertEqual(self.mock_assets.calls,
                         [("load_bundled", "x.pdb", "LOADME")])
        # edit_ops.apply_edit was NOT called (Mode a uses take_backup, not
        # apply_edit -- no alter/h_ops needed).
        self.assertEqual(self.mock_edit._apply_edit_calls, [])

    def test_apply_variant_load_records_backup_handle(self):
        """After apply_variant Mode (a), self._backup[target] holds the handle
        returned by edit_ops.take_backup (so restore can use it)."""
        self.pm.apply_variant("LOADME", "LOADME_X")
        self.assertIn("LOADME", self.pm._backup)
        handle = self.pm._backup["LOADME"]
        self.assertEqual(handle.get("object_name"), "LOADME")


class TestSwitchAndCurrentState(unittest.TestCase):
    """switch_variant / apply_variant record state (current_variant)."""

    def setUp(self):
        self.mock_cmd = MockCmd()
        self.mock_edit = MockEditOps()
        self.mock_assets = MockAssets()
        self.pm = ProtonationManager(
            self.mock_cmd, self.mock_edit, catalog_mod, self.mock_assets)

    def test_switch_variant_records_state(self):
        """After switch_variant('scene','HIS_HIE'), current_variant('scene')
        == 'HIS_HIE'."""
        self.pm.switch_variant("HIS", "HIS_HIE")
        self.assertEqual(self.pm.current_variant("HIS"), "HIS_HIE")

    def test_apply_variant_records_state(self):
        """After apply_variant('scene','HIS_HID'), current_variant('scene')
        == 'HIS_HID'."""
        self.pm.apply_variant("HIS", "HIS_HID")
        self.assertEqual(self.pm.current_variant("HIS"), "HIS_HID")

    def test_current_variant_none_when_not_set(self):
        """current_variant on a target with no variant applied returns None."""
        self.assertIsNone(self.pm.current_variant("HIS"))


class TestRestore(unittest.TestCase):
    """restore clears state + delegates to edit_ops.restore_from_handle."""

    def setUp(self):
        self.mock_cmd = MockCmd()
        self.mock_edit = MockEditOps()
        self.mock_assets = MockAssets()
        self.pm = ProtonationManager(
            self.mock_cmd, self.mock_edit, catalog_mod, self.mock_assets)

    def test_restore_clears_state(self):
        """After apply_variant then restore, current_variant(target) is None
        and the backup is cleared; mock_edit.restore_from_handle was called
        with the stored handle."""
        self.pm.apply_variant("HIS", "HIS_HID")
        handle_before = self.pm._backup["HIS"]
        self.pm.restore("HIS")
        # current_variant is None after restore.
        self.assertIsNone(self.pm.current_variant("HIS"))
        # backup is cleared.
        self.assertNotIn("HIS", self.pm._backup)
        # restore_from_handle was called with the stored handle.
        self.assertEqual(len(self.mock_edit._restore_from_handle_calls), 1)
        self.assertEqual(self.mock_edit._restore_from_handle_calls[0],
                         handle_before)

    def test_restore_no_backup_raises(self):
        """restore(target) with no prior apply_variant raises RuntimeError
        ('no backup registered')."""
        with self.assertRaises(RuntimeError) as ctx:
            self.pm.restore("HIS")
        self.assertIn("no backup registered", str(ctx.exception))


class TestLookupErrors(unittest.TestCase):
    """apply_variant unknown residue / variant raise KeyError (delegated to
    catalog.lookup)."""

    def setUp(self):
        self.pm = ProtonationManager(
            MockCmd(), MockEditOps(), catalog_mod, MockAssets())

    def test_apply_variant_unknown_residue_raises(self):
        """apply_variant('XXX','...') raises KeyError (delegated to
        catalog.lookup)."""
        with self.assertRaises(KeyError) as ctx:
            self.pm.apply_variant("XXX", "XXX_FOO")
        self.assertIn("unknown residue", str(ctx.exception))

    def test_apply_variant_unknown_variant_raises(self):
        """apply_variant('HIS','HIS_XXX') raises KeyError."""
        with self.assertRaises(KeyError) as ctx:
            self.pm.apply_variant("HIS", "HIS_XXX")
        self.assertIn("unknown variant", str(ctx.exception))


class TestListVariants(unittest.TestCase):
    """list_variants delegates to catalog.variants_for."""

    def setUp(self):
        self.pm = ProtonationManager(
            MockCmd(), MockEditOps(), catalog_mod, MockAssets())

    def test_list_variants_delegates_to_catalog(self):
        """list_variants('HIS') returns catalog.variants_for('HIS')."""
        expected = catalog_mod.variants_for("HIS")
        self.assertEqual(self.pm.list_variants("HIS"), expected)

    def test_list_variants_unknown_residue_returns_empty(self):
        """list_variants('XXX') returns [] (delegated to catalog, no raise)."""
        self.assertEqual(self.pm.list_variants("XXX"), [])


class TestSanctionedAlterGateGuard(unittest.TestCase):
    """ProtonationManager source has NO actual Call nodes to self._cmd.alter
    or self._cmd.h_add (the alter gate allowlist stays at edit_ops.py only).

    Uses AST (not naive substring search) so comments/docstrings that DOCUMENT
    the gate compliance (e.g. 'ProtonationManager does NOT call
    self._cmd.alter(...)') don't false-positive. Mirrors the check_imports.py
    AST-gate precedent (Phase 1) -- precise on actual call expressions."""

    def test_protonation_manager_no_direct_alter(self):
        """AST-walk protonation.py; assert NO Call node where func is
        self._cmd.alter or self._cmd.h_add (the alter gate's allowlist stays at
        edit_ops.py only -- ProtonationManager delegates to edit_ops.apply_edit).
        Comments/docstrings mentioning the pattern do NOT count (AST-exact)."""
        src = _read_protonation_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            # Match self._cmd.alter(...) / self._cmd.h_add(...): an Attribute
            # (attr=alter|h_add) on an Attribute (attr=_cmd) on Name(id=self).
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in ("alter", "h_add"):
                continue
            if (isinstance(func.value, ast.Attribute)
                    and func.value.attr == "_cmd"
                    and isinstance(func.value.value, ast.Name)
                    and func.value.value.id == "self"):
                self.fail(
                    "ALTER GATE VIOLATION: ProtonationManager calls "
                    "self._cmd.{0}(...) directly at line {1} -- delegate to "
                    "edit_ops.apply_edit".format(func.attr, node.lineno))


class TestSourceCitationsPresent(unittest.TestCase):
    """Every direct self._cmd.* call in protonation.py is preceded by a
    # src: tmp/pymol-src/... comment (Phase 3 convention)."""

    def test_citations_present_in_source(self):
        """The only direct self._cmd.* call in protonation.py is
        self._cmd.delete in _apply_load; assert it carries a # src: citation.
        Also count: every self._cmd.* call line has a matching # src: comment."""
        src = _read_protonation_source()
        # The one expected citation: cmd.delete in _apply_load.
        expected = [
            "# src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete",
        ]
        for citation in expected:
            self.assertIn(
                citation, src,
                "missing source citation: {0}".format(citation))
        # Count: every self._cmd. call (non-comment line) has a matching
        # # src: citation (comment line starting with "# src: tmp/pymol-src").
        call_count = sum(
            1 for line in src.splitlines()
            if "self._cmd." in line and not line.strip().startswith("#"))
        src_count = sum(
            1 for line in src.splitlines()
            if line.strip().startswith("# src: tmp/pymol-src/modules/pymol/"))
        self.assertEqual(
            call_count, src_count,
            "cmd call count ({0}) != citation count ({1})".format(
                call_count, src_count))


if __name__ == "__main__":
    unittest.main()
