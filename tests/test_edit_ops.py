# Source: stdlib unittest + MockCmd inject pattern (04-RESEARCH-editing-safety.md
# section "Headless Test Strategy"; reuses the inject-cmd pattern from
# tests/test_molops.py:39-65). Python 3.6 compatible (unittest, os, re -- all
# stdlib; NO pymol import).
#
# Pure-WSL unit tests for c14.pymol_layer.edit_ops.EditOps. The module under
# test has `cmd` INJECTED via the constructor (NO pymol import at module top),
# so these tests run under python3.6 with no pymol installed. A MockCmd
# records every cmd.* dispatch (name/args/kwargs) via __getattr__; count_atoms
# and iterate are EXPLICIT methods (bypass __getattr__) so they are NOT
# recorded in self.calls -- calls[0] is always the first real dispatch (the
# Phase 3 MockCmd precedent, test_molops.py:39-65).
#
# The REAL cmd.* calls (alter/sort/rebuild/create/delete/remove/fuse/iterate/
# count_atoms against the PyMOL 2.5.0 API) are verified by tools/edit_smoke.py
# (04-05, headless via tools/run_headless.sh) -- NOT these unit tests. Unit
# tests prove: dispatch order, sort-after-alter for all 4 step ops, backup-
# before-edit, default-args create, delete-before-create, restore verifies
# (atom count + residue signature), unknown-step raises, protonation_change
# partitions h_ops removes-before-alter adds-after-alter, citation presence,
# no 1,1-create, no self-copy.
"""Unit tests for EditOps (MockCmd dispatch order + sort-after-alter + backup/
restore mechanics + citation presence + Pitfall guards).

Pure WSL python3.6 -- NO pymol import. MockCmd records the cmd.* dispatch
(name, args, kwargs) for alter/sort/rebuild/create/delete/remove/fuse.
count_atoms and iterate are EXPLICIT methods (not recorded) so calls[0] is
always the first real dispatch. Verifies:
  * apply_edit dispatch order: backup-first, alter-after-backup, sort+rebuild-
    after-alter (SC1 unit-level for all 4 step ops).
  * take_backup: default-args create (no state args), delete-stale-first,
    raises on count mismatch.
  * restore: delete-before-create, verifies atom count + residue signature,
    clears handle registry, raises when no handle registered.
  * protonation_change: partitions h_ops into removes (before alter) + adds
    (after alter), matching 04-03 _apply_alter.
  * Source-citation comments present on every self._cmd.* call (SC #4
    machine-checkable).
  * No Pitfall 2 (1,1 state args) or Pitfall 3 (self-copy create) violations.
"""
import os
import re
import unittest

from c14.pymol_layer.edit_ops import EditOps, RestoreHandle


class MockCmd(object):
    """Records every cmd.* dispatch as (name, args, kwargs); returns 0.

    ``count_atoms`` and ``iterate`` are EXPLICIT methods (override the
    __getattr__ fallback) so they are NOT recorded in ``self.calls`` --
    ``calls[0]`` is always the first real dispatch (the Phase 3 MockCmd
    precedent, test_molops.py:39-65).

    ``count_atoms`` returns ``self._count`` for live objects and
    ``self._count_bak`` for backup objects (names starting with ``_bak_``),
    so the backup count-mismatch test can set them differently.

    ``iterate`` populates ``stored.list`` from ``self._residue_sig`` (a list
    of ``(chain, resi, resn)`` tuples) so the residue-signature collection is
    unit-testable.
    """

    def __init__(self):
        self.calls = []
        self._count = 3
        self._count_bak = 3
        self._residue_sig = [("A", "1", "ALA"), ("A", "2", "GLY")]

    def __getattr__(self, name):
        # Returns a recording stub for any cmd.* attr except count_atoms and
        # iterate (which are explicit methods and bypass __getattr__).
        def f(*a, **k):
            self.calls.append((name, a, k))
            return 0
        return f

    def count_atoms(self, sel="(all)"):
        # Explicit method -> normal attribute lookup finds this BEFORE
        # __getattr__, so count_atoms is not recorded. Returns _count_bak for
        # backup names so the mismatch test can differentiate.
        if isinstance(sel, str) and sel.startswith("_bak_"):
            return self._count_bak
        return self._count

    def iterate(self, selection, expression, quiet=1, space=None):
        # Explicit method -> not recorded. Populates stored.list from the
        # configurable _residue_sig so _collect_residue_signature is testable.
        if space is not None and "stored" in space:
            space["stored"].list = list(self._residue_sig)
        return 0


def _read_edit_ops_source():
    """Read c14/pymol_layer/edit_ops.py as text (for citation/pitfall tests)."""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_path = os.path.join(repo, "c14", "pymol_layer", "edit_ops.py")
    with open(src_path, "r") as fh:
        return fh.read()


class TestApplyEditDispatchOrder(unittest.TestCase):
    """apply_edit dispatch order: backup-first, alter-after-backup,
    sort+rebuild-after-alter (SC1 unit-level)."""

    def setUp(self):
        self.mock = MockCmd()
        self.ops = EditOps(self.mock)

    def test_apply_edit_point_mutation_call_sequence(self):
        """apply_edit(point_mutation) calls: delete(bak), create(bak,obj),
        [count_atoms x2 -- not recorded], [iterate -- not recorded],
        alter(sele,expr), sort(obj), rebuild(obj). Assert this order."""
        self.ops.apply_edit("pep", [
            {"op": "alter", "sele": "pep and resi 1", "expr": "resn='GLY'"}])
        calls = self.mock.calls
        # Recorded calls (count_atoms + iterate are explicit, not recorded):
        # delete, create, alter, sort, rebuild
        self.assertEqual(calls[0][0], "delete")
        self.assertEqual(calls[0][1], ("_bak_pep",))
        self.assertEqual(calls[1][0], "create")
        self.assertEqual(calls[1][1], ("_bak_pep", "pep"))
        self.assertEqual(calls[2][0], "alter")
        self.assertEqual(calls[2][1], ("pep and resi 1", "resn='GLY'"))
        self.assertEqual(calls[3][0], "sort")
        self.assertEqual(calls[3][1], ("pep",))
        self.assertEqual(calls[4][0], "rebuild")
        self.assertEqual(calls[4][1], ("pep",))
        # alter appears AFTER create (backup first)
        alter_idx = next(i for i, c in enumerate(calls) if c[0] == "alter")
        create_idx = next(i for i, c in enumerate(calls) if c[0] == "create")
        self.assertGreater(alter_idx, create_idx)
        # sort + rebuild appear AFTER alter (SC1 unit-level)
        sort_idx = next(i for i, c in enumerate(calls) if c[0] == "sort")
        rebuild_idx = next(i for i, c in enumerate(calls) if c[0] == "rebuild")
        self.assertGreater(sort_idx, alter_idx)
        self.assertGreater(rebuild_idx, alter_idx)

    def test_apply_edit_always_sorts_and_rebuilds_after_any_step(self):
        """For each step op (alter, h_add, remove, fuse), sort + rebuild
        appear AFTER the mutating call (the alter->sort trap mitigation is
        uniform across all 4 ops)."""
        step_variants = [
            {"op": "alter", "sele": "obj", "expr": "resn='GLY'"},
            {"op": "h_add", "sele": "obj"},
            {"op": "remove", "sele": "obj and name H"},
            {"op": "fuse", "sele1": "frag", "sele2": "obj and name C1"},
        ]
        for step in step_variants:
            self.mock.calls = []
            self.ops.apply_edit("obj", [step])
            calls = self.mock.calls
            mutating_ops = {"alter", "h_add", "remove", "fuse"}
            mut_idx = next(i for i, c in enumerate(calls)
                           if c[0] in mutating_ops)
            sort_idx = next(i for i, c in enumerate(calls) if c[0] == "sort")
            rebuild_idx = next(
                i for i, c in enumerate(calls) if c[0] == "rebuild")
            self.assertGreater(
                sort_idx, mut_idx,
                "sort after {} failed".format(step["op"]))
            self.assertGreater(
                rebuild_idx, mut_idx,
                "rebuild after {} failed".format(step["op"]))

    def test_apply_edit_takes_backup_before_edit(self):
        """The first recorded call is delete(bak), the second is create(bak,
        obj) -- the backup happens BEFORE any alter/h_add/remove/fuse."""
        self.ops.apply_edit("obj", [
            {"op": "alter", "sele": "obj", "expr": "resn='GLY'"}])
        calls = self.mock.calls
        self.assertEqual(calls[0][0], "delete")
        self.assertEqual(calls[0][1], ("_bak_obj",))
        self.assertEqual(calls[1][0], "create")
        self.assertEqual(calls[1][1], ("_bak_obj", "obj"))

    def test_unknown_edit_step_op_raises(self):
        """apply_edit with an unknown step op raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.ops.apply_edit("obj", [{"op": "bogus", "sele": "obj"}])
        self.assertIn("unknown edit step op", str(ctx.exception))


class TestTakeBackup(unittest.TestCase):
    """take_backup: default-args create, delete-stale-first, count mismatch."""

    def setUp(self):
        self.mock = MockCmd()
        self.ops = EditOps(self.mock)

    def test_take_backup_uses_default_args_create(self):
        """create called with NO source_state/target_state kwargs (default-args
        = all states; the 1,1 form drops multi-state data -- Pitfall 2)."""
        self.ops.take_backup("obj")
        create_call = next(c for c in self.mock.calls if c[0] == "create")
        # Only 2 positional args (bak, obj) -- no state indices
        self.assertEqual(len(create_call[1]), 2)
        self.assertNotIn("source_state", create_call[2])
        self.assertNotIn("target_state", create_call[2])

    def test_take_backup_deletes_stale_backup_first(self):
        """delete(bak) called BEFORE create(bak, obj) (idempotent clear of a
        stale backup -- Pitfall 6)."""
        self.ops.take_backup("obj")
        calls = self.mock.calls
        self.assertEqual(calls[0][0], "delete")
        self.assertEqual(calls[0][1], ("_bak_obj",))
        create_idx = next(i for i, c in enumerate(calls) if c[0] == "create")
        self.assertLess(0, create_idx)

    def test_take_backup_raises_on_count_mismatch(self):
        """count_atoms(bak) != count_atoms(obj) raises RuntimeError."""
        self.mock._count = 3
        self.mock._count_bak = 2
        with self.assertRaises(RuntimeError) as ctx:
            self.ops.take_backup("obj")
        self.assertIn("backup atom-count mismatch", str(ctx.exception))

    def test_take_backup_returns_restore_handle(self):
        """take_backup returns a RestoreHandle with the right fields."""
        handle = self.ops.take_backup("obj")
        self.assertIsInstance(handle, RestoreHandle)
        self.assertEqual(handle.object_name, "obj")
        self.assertEqual(handle.backup_name, "_bak_obj")
        self.assertEqual(handle.pre_atom_count, 3)
        self.assertEqual(
            handle.pre_residue_signature,
            [("A", "1", "ALA"), ("A", "2", "GLY")])


class TestRestore(unittest.TestCase):
    """restore / restore_from_handle: delete-before-create, verify round-trip,
    clear handle registry, no-handle raises."""

    def setUp(self):
        self.mock = MockCmd()
        self.ops = EditOps(self.mock)
        # Use apply_edit to register the handle (take_backup alone doesn't
        # register in _handles; apply_edit does).
        self.handle = self.ops.apply_edit("obj", [
            {"op": "alter", "sele": "obj", "expr": "resn='GLY'"}])

    def test_restore_deletes_before_create(self):
        """restore_from_handle calls delete(obj) BEFORE create(obj, bak)
        (Pitfall 4: create into existing name MERGES)."""
        self.mock.calls = []
        self.ops.restore_from_handle(self.handle)
        calls = self.mock.calls
        delete_idx = next(i for i, c in enumerate(calls) if c[0] == "delete")
        create_idx = next(i for i, c in enumerate(calls) if c[0] == "create")
        self.assertLess(delete_idx, create_idx)

    def test_restore_verifies_atom_count(self):
        """Post-restore count_atoms != handle.pre_atom_count raises
        RuntimeError('restore atom-count mismatch')."""
        self.mock._count = 99  # mismatched from handle.pre_atom_count (3)
        with self.assertRaises(RuntimeError) as ctx:
            self.ops.restore_from_handle(self.handle)
        self.assertIn("restore atom-count mismatch", str(ctx.exception))

    def test_restore_verifies_residue_signature(self):
        """Post-restore residue signature != handle.pre_residue_signature
        raises RuntimeError('restore residue-identity mismatch')."""
        self.mock._residue_sig = [("Z", "9", "ZZZ")]  # mismatched
        with self.assertRaises(RuntimeError) as ctx:
            self.ops.restore_from_handle(self.handle)
        self.assertIn("restore residue-identity mismatch", str(ctx.exception))

    def test_restore_from_handle_clears_handle_registry(self):
        """After restore_from_handle, the handle is popped from _handles; a
        second restore(obj) raises 'no backup handle'."""
        self.ops.restore_from_handle(self.handle)
        self.assertNotIn("obj", self.ops._handles)
        with self.assertRaises(RuntimeError):
            self.ops.restore("obj")

    def test_restore_no_handle_raises(self):
        """restore(obj) with no prior apply_edit raises RuntimeError('no
        backup handle registered')."""
        ops = EditOps(MockCmd())
        with self.assertRaises(RuntimeError) as ctx:
            ops.restore("obj")
        self.assertIn("no backup handle registered", str(ctx.exception))


class TestProtonationChange(unittest.TestCase):
    """protonation_change partitions h_ops: removes before alter, adds after
    alter (Pitfall 2 ordering, matching 04-03 _apply_alter)."""

    def test_protonation_change_partitions_h_ops_removes_before_alter_adds_after(self):
        """protonation_change with h_ops=[remove, add] calls apply_edit with
        steps = [remove, alter, h_add] (removes first, alter middle, adds
        after). Assert the MockCmd calls include remove then alter then h_add
        (in order) then sort + rebuild."""
        mock = MockCmd()
        ops = EditOps(mock)
        ops.protonation_change(
            "obj", "obj and resi 1", "HID",
            h_ops=[{"op": "remove", "sele": "resn HIS and name HE2"},
                   {"op": "add", "sele": "resn HID and name ND1"}])
        calls = mock.calls
        # Find the mutating calls and assert their order
        remove_idx = next(i for i, c in enumerate(calls) if c[0] == "remove")
        alter_idx = next(i for i, c in enumerate(calls) if c[0] == "alter")
        h_add_idx = next(i for i, c in enumerate(calls) if c[0] == "h_add")
        self.assertLess(remove_idx, alter_idx,
                        "remove must come before alter")
        self.assertLess(alter_idx, h_add_idx,
                        "alter must come before h_add")
        # sort + rebuild after all mutating ops
        sort_idx = next(i for i, c in enumerate(calls) if c[0] == "sort")
        rebuild_idx = next(i for i, c in enumerate(calls) if c[0] == "rebuild")
        self.assertGreater(sort_idx, h_add_idx)
        self.assertGreater(rebuild_idx, h_add_idx)


class TestSourceCitationsPresent(unittest.TestCase):
    """SC #4: every self._cmd.* call in edit_ops.py carries a # src: comment."""

    def test_citations_present_in_source(self):
        """Every self._cmd.* call line is immediately preceded by a
        # src: tmp/pymol-src/modules/pymol/ comment. Count the # src: comments
        and the self._cmd. calls; assert they match (every cmd call is
        cited)."""
        src = _read_edit_ops_source()
        # Expected unique citations (one per cmd.* API used)
        expected = [
            "# src: tmp/pymol-src/modules/pymol/editing.py:1424 cmd.alter",
            "# src: tmp/pymol-src/modules/pymol/editing.py:1216 cmd.h_add",
            "# src: tmp/pymol-src/modules/pymol/editing.py:800 cmd.remove",
            "# src: tmp/pymol-src/modules/pymol/editing.py:937 cmd.fuse",
            "# src: tmp/pymol-src/modules/pymol/editing.py:1257 cmd.sort",
            "# src: tmp/pymol-src/modules/pymol/viewing.py:1791 cmd.rebuild",
            "# src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete",
            "# src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create",
            "# src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms",
            "# src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate",
        ]
        for citation in expected:
            self.assertIn(
                citation, src,
                "missing source citation: {0}".format(citation))
        # Count: every self._cmd. call (non-comment line) has a matching
        # # src: citation (comment line starting with "# src: tmp/pymol-src")
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


class TestPitfallGuards(unittest.TestCase):
    """Pitfall 2 (no 1,1 state args) + Pitfall 3 (no self-copy create)
    guards on edit_ops.py source."""

    def test_no_bare_create_with_state_args(self):
        """No create() call with explicit 1,1 state args or source_state=1
        (Pitfall 2 guard)."""
        src = _read_edit_ops_source()
        for line in src.splitlines():
            self.assertNotIn(
                ", 1, 1)", line,
                "Pitfall 2: state args found: " + line.strip())
            self.assertNotIn(
                "source_state=1", line,
                "Pitfall 2: source_state=1 found: " + line.strip())

    def test_no_self_copy_create(self):
        """No create(X, X) self-copy pattern where the first two args are the
        same identifier (Pitfall 3 guard -- self-copy is destructive)."""
        src = _read_edit_ops_source()
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Find create(first_arg, second_arg) and assert they differ
            matches = re.findall(
                r"\.create\(([^,]+),\s*([^,\)]+)\)", line)
            for first, second in matches:
                self.assertNotEqual(
                    first.strip(), second.strip(),
                    "Pitfall 3: self-copy create({0}, {1}) found".format(
                        first.strip(), second.strip()))


if __name__ == "__main__":
    unittest.main()
