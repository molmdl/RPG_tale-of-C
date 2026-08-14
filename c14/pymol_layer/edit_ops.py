# c14/pymol_layer/edit_ops.py -- Phase 4 Plan 04-01 EditOps.
#
# The SOLE sanctioned cmd.alter path in the entire repo. The alter->sort
# silent-corruption trap (editing.py:1457-1460 docstring WARNING: "You should
# always issue a sort command on an object after modifying any property which
# might affect canonical atom ordering ... Failure to do so will confound
# subsequent create and byres operations") is mitigated by ALWAYS calling
# cmd.sort + cmd.rebuild after any alter/h_add/remove/fuse step. The
# tools/check_alter_gate.py AST gate (04-04) allowlists exactly this module --
# cmd.alter may appear NOWHERE else in c14/ or tools/.
#
# Backup uses default-args cmd.create (source_state=0, target_state=0 = ALL
# states -- the Phase 3 empirical correction, STATE.md:84; the explicit-state
# form silently drops multi-state data). Restore = cmd.delete THEN cmd.create
# (delete first -- creating into an existing name MERGES per the creating.py
# docstring, so the delete is mandatory).
#
# DESIGN -- 3-tier testability pattern (inject cmd):
#   * cmd is INJECTED via the constructor (mirrors molops.py:80), so the
#     dispatch/sequence logic is unit-testable in pure WSL python3.6 with a
#     MockCmd (NO pymol installed). The REAL cmd.* contract is verified by
#     tools/edit_smoke.py (04-05, headless via tools/run_headless.sh), NOT by
#     these unit tests.
#
# GATE EXCLUSION: lives in c14/pymol_layer/ which tools/check_imports.py
# excludes via SKIP_DIRS = {"pymol_layer","ui","__pycache__"} -- the domain
# tier (c14/ root) stays pure-Python (no pymol import).
#
# PYTHON 3.6 ONLY: plain classes on instance attributes, .format() strings, NO
# @dataclass / walrus (matches Phase 1/2/3 precedent; 3.6.9 has no dataclasses
# module).
#
# Every self._cmd.* call carries a `# src: tmp/pymol-src/modules/pymol/<file>.py:<line>
# cmd.<name>` comment on the line directly above -- the source-citation
# convention established by Plan 03-01 (success criterion #4). Line numbers
# pinned to PyMOL 2.5.0 (all 10 verified against tmp/pymol-src/modules/pymol/).
"""EditOps -- the sole sanctioned cmd.alter path + backup/restore safety net.

This is the ONLY module in the repo allowed to call cmd.alter (the
tools/check_alter_gate.py allowlist = {c14/pymol_layer/edit_ops.py}). The
alter->sort silent-corruption trap -- documented verbatim in the cmd.alter
docstring (editing.py:1457-1460: "You should always issue a sort command on an
object after modifying any property which might affect canonical atom ordering
... Failure to do so will confound subsequent create and byres operations") --
is mitigated by ALWAYS calling cmd.sort + cmd.rebuild after any
alter/h_add/remove/fuse step.

Backup uses default-args cmd.create (all-states copy -- Phase 3 empirical
correction, STATE.md:84). Restore = cmd.delete THEN cmd.create (delete first
-- creating into an existing name MERGES per the creating.py docstring).

Inject ``cmd`` so the dispatch/sequence logic is unit-testable in pure WSL
python3.6 with a MockCmd (the real cmd.* calls are verified by
tools/edit_smoke.py, not unit tests).
"""


class RestoreHandle(object):
    """Opaque restore handle returned by apply_edit / take_backup.

    Carries the backup name + pre-edit atom count + pre-edit residue signature
    so restore() can verify the round-trip (SC2). Plain class (3.6-compatible,
    no @dataclass).

    Attributes:
        object_name: the live object that was backed up.
        backup_name: the backup object name (``_bak_<object_name>``).
        pre_atom_count: atom count of the object BEFORE any edit (for SC2
            round-trip verification).
        pre_residue_signature: sorted list of (chain, resi, resn) tuples
            collected via cmd.iterate BEFORE any edit (for SC2 residue-identity
            verification).
    """

    def __init__(self, object_name, backup_name, pre_atom_count,
                 pre_residue_signature):
        # type: (str, str, int, list) -> None
        self.object_name = object_name
        self.backup_name = backup_name
        self.pre_atom_count = pre_atom_count
        self.pre_residue_signature = pre_residue_signature


class EditOps(object):
    """The sole sanctioned cmd.alter path + backup/restore safety net.

    Inject ``cmd`` so the dispatch/sequence logic is unit-testable in pure WSL
    python3.6 with a MockCmd (the real cmd.* calls are verified by
    tools/edit_smoke.py, headless).

    apply_edit takes a LIST of edit steps under ONE backup, dispatches each
    step (alter/h_add/remove/fuse), then ALWAYS calls cmd.sort + cmd.rebuild
    (the alter->sort trap mitigation). ProtonationManager (04-03) composes its
    own step list; the 4 convenience methods build standard step lists.
    """

    def __init__(self, cmd):
        self._cmd = cmd
        self._handles = {}  # object_name -> RestoreHandle (for restore() lookup)

    # ------------------------------------------------------------------
    # LOW-LEVEL: the sole sanctioned alter path. Takes a LIST of edit steps
    # under ONE backup. ProtonationManager composes its own step list; the
    # 4 convenience methods below build standard step lists.
    # ------------------------------------------------------------------
    def apply_edit(self, object_name, edit_steps):
        """Apply a list of edit steps under one backup; return RestoreHandle.

        Step-dict schema::

            {"op": "alter"|"h_add"|"remove"|"fuse", ...}

        - alter: ``{"op":"alter","sele":...,"expr":...}``
        - h_add: ``{"op":"h_add","sele":...}``
        - remove:``{"op":"remove","sele":...}``
        - fuse:  ``{"op":"fuse","sele1":...,"sele2":...}``

        ALWAYS calls cmd.sort + cmd.rebuild after all steps (the alter->sort
        trap mitigation). Takes a backup BEFORE any step (SC2 backup-before-
        edit). Registers the handle for restore() lookup.
        """
        # 1. BACKUP first (default-args cmd.create = all states)
        handle = self.take_backup(object_name)
        # 2. Dispatch each step (alter / h_add / remove / fuse)
        for step in edit_steps:
            op = step["op"]
            if op == "alter":
                # src: tmp/pymol-src/modules/pymol/editing.py:1424 cmd.alter
                self._cmd.alter(step["sele"], step["expr"])
            elif op == "h_add":
                # src: tmp/pymol-src/modules/pymol/editing.py:1216 cmd.h_add
                self._cmd.h_add(step["sele"])
            elif op == "remove":
                # src: tmp/pymol-src/modules/pymol/editing.py:800 cmd.remove
                self._cmd.remove(step["sele"])
            elif op == "fuse":
                # src: tmp/pymol-src/modules/pymol/editing.py:937 cmd.fuse
                self._cmd.fuse(step["sele1"], step["sele2"])
            else:
                raise ValueError(
                    "unknown edit step op {!r}".format(op))
        # 3. ALWAYS sort + rebuild (the alter->sort trap mitigation)
        # src: tmp/pymol-src/modules/pymol/editing.py:1257 cmd.sort
        self._cmd.sort(object_name)
        # src: tmp/pymol-src/modules/pymol/viewing.py:1791 cmd.rebuild
        self._cmd.rebuild(object_name)
        # 4. Register handle for restore() lookup
        self._handles[object_name] = handle
        return handle

    # ------------------------------------------------------------------
    # CONVENIENCE: the 4 standard edit types (build step lists + call
    # apply_edit)
    # ------------------------------------------------------------------
    def point_mutation(self, object_name, sele, new_resn):
        """Point mutation: alter resn on ``sele`` to ``new_resn`` (EDIT-01)."""
        return self.apply_edit(object_name, [
            {"op": "alter", "sele": sele,
             "expr": "resn='{}'".format(new_resn)}])

    def substrate_remove_group(self, object_name, group_sele):
        """Substrate edit: remove a group of atoms (EDIT-02)."""
        return self.apply_edit(object_name, [
            {"op": "remove", "sele": group_sele}])

    def substrate_add_group(self, object_name, frag_atom_sele, target_atom_sele):
        """Substrate edit: fuse a fragment onto the substrate (EDIT-02)."""
        return self.apply_edit(object_name, [
            {"op": "fuse", "sele1": frag_atom_sele, "sele2": target_atom_sele}])

    def protonation_change(self, object_name, sele, new_resn, h_ops=None):
        """Protonation change: alter resn + targeted H add/remove (EDIT-05).

        h_ops: list of ``{"op":"remove"|"add","sele":"..."}`` dicts. Partitions
        h_ops into removes (OLD resn -- BEFORE alter) + adds (NEW resn -- AFTER
        alter), matching 04-03 _apply_alter (Pitfall 2 ordering). The catalog
        authors selections with the right resn phase.
        """
        removes = [{"op": "remove", "sele": h["sele"]}
                   for h in (h_ops or []) if h["op"] == "remove"]
        adds = [{"op": "h_add", "sele": h["sele"]}
                for h in (h_ops or []) if h["op"] == "add"]
        steps = removes + [{"op": "alter", "sele": sele,
                            "expr": "resn='{}'".format(new_resn)}] + adds
        return self.apply_edit(object_name, steps)

    # ------------------------------------------------------------------
    # BACKUP (public -- ProtonationManager Mode (a) calls this before
    # delete+load)
    # ------------------------------------------------------------------
    def take_backup(self, object_name):
        """Take a backup of ``object_name``; return a RestoreHandle.

        Backup = cmd.delete(bak) [idempotent clear of stale backup] +
        cmd.create(bak, obj) [default-args = ALL states]. Verifies the backup
        atom count matches the source, then captures the pre-edit residue
        signature for SC2 round-trip verification.
        """
        bak = "_bak_" + object_name
        # src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete
        self._cmd.delete(bak)
        # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create
        self._cmd.create(bak, object_name)
        # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
        n = self._cmd.count_atoms(object_name)
        # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
        if self._cmd.count_atoms(bak) != n:
            raise RuntimeError(
                "backup atom-count mismatch for {!r}".format(object_name))
        sig = self._collect_residue_signature(object_name)
        return RestoreHandle(object_name, bak, n, sig)

    # ------------------------------------------------------------------
    # RESTORE (SC2 round-trip -- deletes first, then creates from backup,
    # verifies atom count + residue signature)
    # ------------------------------------------------------------------
    def restore(self, object_name):
        """Restore ``object_name`` from its registered backup handle.

        Looks up the RestoreHandle registered by the most recent apply_edit /
        take_backup. Raises RuntimeError if no handle is registered.
        """
        handle = self._handles.get(object_name)
        if handle is None:
            raise RuntimeError(
                "no backup handle registered for {!r}".format(object_name))
        return self.restore_from_handle(handle)

    def restore_from_handle(self, handle):
        """Restore from an explicit RestoreHandle; verify the round-trip (SC2).

        Deletes the (possibly edited) live object FIRST, then creates it from
        the backup (delete-first is mandatory -- creating into an existing name
        MERGES per the creating.py docstring). Sorts + rebuilds, then verifies
        the post-restore atom count + residue signature match the pre-edit
        values captured in the handle.
        """
        # src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete
        self._cmd.delete(handle.object_name)
        # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create
        self._cmd.create(handle.object_name, handle.backup_name)
        # src: tmp/pymol-src/modules/pymol/editing.py:1257 cmd.sort
        self._cmd.sort(handle.object_name)
        # src: tmp/pymol-src/modules/pymol/viewing.py:1791 cmd.rebuild
        self._cmd.rebuild(handle.object_name)
        # VERIFY round-trip (SC2)
        # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
        if self._cmd.count_atoms(handle.object_name) != handle.pre_atom_count:
            raise RuntimeError(
                "restore atom-count mismatch for {!r}".format(
                    handle.object_name))
        if self._collect_residue_signature(handle.object_name) != handle.pre_residue_signature:
            raise RuntimeError(
                "restore residue-identity mismatch for {!r}".format(
                    handle.object_name))
        self._handles.pop(handle.object_name, None)
        return handle.object_name

    def _collect_residue_signature(self, object_name):
        """Collect a sorted (chain, resi, resn) signature via cmd.iterate.

        Returns a sorted list of (chain, resi, resn) tuples -- the residue-
        identity signature used for SC2 round-trip verification. A resn-only
        check would miss a point mutation (ALA->GLY restored looks identical
        if you only compare resn counts); the full (chain, resi, resn) tuple
        catches the swap (Pitfall 7).
        """
        stored = type("S", (), {"list": []})()
        # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
        self._cmd.iterate(
            object_name, "stored.list.append((chain,resi,resn))",
            space={"stored": stored})
        return sorted(stored.list)
