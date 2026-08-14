# c14/pymol_layer/protonation.py -- Phase 4 Plan 04-03 ProtonationManager.
#
# Curated-variant protonation (CAST-03, NO pH engine). ProtonationManager is a
# thin dispatcher: it looks up a variant in the pure-data catalog
# (c14/protonation_catalog.py) and delegates the actual cmd.alter / cmd.h_add
# / cmd.remove / cmd.sort / cmd.rebuild to edit_ops.apply_edit (the ONE
# sanctioned-alter site from 04-01). The alter gate allowlist stays at exactly
# ONE module (edit_ops.py); ProtonationManager does NOT call cmd.alter or
# cmd.h_add directly. Every apply_variant takes a backup via edit_ops so
# EDIT-05 (restore safety net) covers protonation changes.
#
# DESIGN -- 3-tier testability pattern (inject cmd + edit_ops + catalog + assets):
#   * All 4 deps injected via __init__ so the dispatch / switch-state / routing
#     logic is unit-testable in pure WSL python3.6 with MockCmd/MockEditOps/
#     MockCatalog/MockAssets (mirrors molops.py:80 + the 04-01 EditOps pattern).
#   * The catalog is the c14.protonation_catalog MODULE (passed as a module
#     reference; ProtonationManager calls catalog.lookup(...) /
#     catalog.variants_for(...)). The REAL cmd.* contract is verified by
#     tools/protonation_smoke.py (04-05), NOT by these unit tests.
#
# GATE EXCLUSION: lives in c14/pymol_layer/ which tools/check_imports.py
# excludes via SKIP_DIRS = {"pymol_layer","ui","__pycache__"} -- the domain
# tier (c14/ root) stays pure-Python (no pymol import).
#
# SANCTIONED-ALTER GATE COMPLIANCE: ProtonationManager does NOT call
# self._cmd.alter(...) or self._cmd.h_add(...) ANYWHERE. The only direct
# self._cmd.* call is self._cmd.delete(target) in _apply_load (Mode a
# object-replace). All alter/h_add/remove/sort/rebuild go through
# self._edit.apply_edit(target, steps). A unit test
# (test_protonation_manager_no_direct_alter) asserts protonation.py source
# contains NO "self._cmd.alter(" and NO "self._cmd.h_add(" calls (the alter
# gate's allowlist stays at edit_ops.py only).
#
# PYTHON 3.6 ONLY: plain class, .format() strings, NO @dataclass / walrus
# (matches Phase 1/2/3/04-01 precedent; 3.6.9 has no dataclasses module).
#
# Every direct self._cmd.* call carries a `# src: tmp/pymol-src/modules/pymol/
# <file>.py:<line> cmd.<name>` comment on the line directly above -- the
# source-citation convention established by Plan 03-01 (success criterion #4).
# The only direct self._cmd.* call here is self._cmd.delete in _apply_load.
"""ProtonationManager -- curated-variant protonation dispatcher (CAST-03).

NO pH engine (CAST-03, PROJECT.md). apply_variant(target, variant_id) looks
up a variant in the pure-data catalog (c14.protonation_catalog) and routes
to Mode (a) load pre-built (AssetManager.load_bundled) or Mode (b) alter +
h_ops (edit_ops.apply_edit). switch_variant is the user-adjustable SC4 entry;
current_variant / list_variants support the Phase 6 UI. Every application
takes a backup via edit_ops so the switch is reversible (EDIT-05 covers
protonation).

Inject ``cmd`` + ``edit_ops`` + ``catalog`` + ``assets`` so the dispatch /
switch-state / routing logic is unit-testable in pure WSL python3.6 with
MockCmd/MockEditOps/MockCatalog/MockAssets (the real cmd.* contract is
verified by tools/protonation_smoke.py, not unit tests).
"""


class ProtonationManager(object):
    """Curated-variant protonation dispatcher. NO pH engine (CAST-03).

    apply_variant(target, variant_id) looks up the variant in the catalog and
    routes to Mode (a) load pre-built (AssetManager) or Mode (b) alter+h_ops
    (edit_ops.apply_edit). switch_variant is the user-adjustable SC4 entry;
    current_variant / list_variants support the Phase 6 UI. Every application
    takes a backup via edit_ops so the switch is reversible (EDIT-05 covers
    protonation).
    """

    def __init__(self, cmd, edit_ops, catalog, assets):
        # type: (cmd, EditOps, module, AssetManager) -> None
        self._cmd = cmd
        self._edit = edit_ops          # the ONE sanctioned-alter site (04-01)
        self._catalog = catalog        # c14.protonation_catalog module (pure data)
        self._assets = assets          # AssetManager (Mode a)
        self._current = {}             # target -> variant_id (switch state)
        self._backup = {}              # target -> RestoreHandle (for restore)

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------
    def list_variants(self, target):
        # type: (str) -> list
        """Return [(variant_id, label), ...] for the target's residue key.

        Delegates to catalog.variants_for(residue_key(target)). Phase 4:
        target IS the residue key (e.g. "HIS"); Phase 5+ target schema may
        need parsing (see _residue_key).
        """
        return self._catalog.variants_for(self._residue_key(target))

    def current_variant(self, target):
        # type: (str) -> object
        """Return the currently-applied variant_id for ``target``, or None."""
        return self._current.get(target)

    def apply_variant(self, target, variant_id):
        # type: (str, str) -> str
        """Apply a curated variant to ``target``. Takes a backup first (EDIT-05).

        Mode (a) ``load``: edit_ops.take_backup(target) -> cmd.delete(target) ->
        AssetManager.load_bundled(spec["source_file"], target). No alter needed
        (the .pdb is pre-built).

        Mode (b) ``alter``: edit_ops.apply_edit(target, removes + alter + adds)
        -> backup + alter resn + targeted h_add/remove + sort + rebuild.

        Records the active variant + backup handle for switch reversal.
        Raises KeyError if (residue_key, variant_id) not in catalog (delegated
        to catalog.lookup).
        """
        spec = self._catalog.lookup(self._residue_key(target), variant_id)
        if spec["mode"] == "load":
            self._apply_load(target, spec)
        else:
            self._apply_alter(target, spec)
        self._current[target] = variant_id
        return variant_id

    def switch_variant(self, target, variant_id):
        # type: (str, str) -> str
        """User-adjustable switch (SC4). Equivalent to apply_variant -- every
        switch takes a fresh backup so it's reversible. Kept as a distinct
        name so the SC4 mapping is explicit in the Phase 6 UI."""
        return self.apply_variant(target, variant_id)

    def restore(self, target):
        # type: (str) -> None
        """Restore the pre-protonation state (EDIT-05).

        Delegates to edit_ops.restore_from_handle(self._backup[target]) -- the
        04-01 contract for self-managed handles (ProtonationManager tracks its
        own handle in self._backup for both Mode a take_backup + Mode b
        apply_edit; restore_from_handle works with any explicit handle, no
        _handles lookup needed). edit_ops.restore_from_handle verifies the
        round-trip (atom count + residue signature) and pops the handle.

        Clears the switch state + backup. Raises RuntimeError if no backup was
        registered for ``target``.
        """
        handle = self._backup.get(target)
        if handle is None:
            raise RuntimeError(
                "protonation: no backup registered for {!r}".format(target))
        self._edit.restore_from_handle(handle)
        self._current.pop(target, None)
        self._backup.pop(target, None)

    # ------------------------------------------------------------------
    # INTERNAL: residue-key derivation (Phase 4 placeholder)
    # ------------------------------------------------------------------
    def _residue_key(self, target):
        # type: (str) -> str
        """Derive the catalog residue key from ``target``.

        Phase 4 placeholder: target IS the residue key (e.g. "HIS" or
        "scene"). Phase 5+ target schema (e.g. "pdb:1TNR/chainA/HIS123") may
        need parsing; coordinate with the edit-node contract (Phase 5.1).
        """
        # Phase 4: target verbatim. Phase 5+ may parse a structured target.
        return target

    # ------------------------------------------------------------------
    # INTERNAL: Mode (a) load pre-built
    # ------------------------------------------------------------------
    def _apply_load(self, target, spec):
        # type: (str, dict) -> None
        """Mode (a): replace the object with a pre-built protonated structure.

        Takes a backup FIRST via edit_ops.take_backup (so restore works --
        EDIT-05; the handle is NOT registered in edit_ops._handles, but
        ProtonationManager tracks it in self._backup and uses
        restore_from_handle for the round-trip). Then cmd.delete(target) +
        AssetManager.load_bundled(spec["source_file"], target). NO alter
        (the .pdb is pre-built).
        """
        # 1. Backup first (so restore works -- EDIT-05). take_backup returns a
        # RestoreHandle but does NOT register it in edit_ops._handles; we
        # track it in self._backup and use restore_from_handle for restore.
        handle = self._edit.take_backup(target)
        # 2. Delete the current object (creating into an existing name MERGES
        # per creating.py docstring -- delete first is mandatory).
        # src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete
        self._cmd.delete(target)
        # 3. Load the pre-built protonated structure (load_bundled asserts
        # non-empty -- the citation lives in asset_manager.py).
        self._assets.load_bundled(spec["source_file"], target)
        # 4. Track the handle for switch reversal.
        self._backup[target] = handle

    # ------------------------------------------------------------------
    # INTERNAL: Mode (b) alter + targeted h_ops
    # ------------------------------------------------------------------
    def _apply_alter(self, target, spec):
        # type: (str, dict) -> None
        """Mode (b): build the edit_steps list and delegate to edit_ops.apply_edit.

        h_ops ordering (Pitfall 2 mitigation): removes (OLD resn) BEFORE alter,
        adds (NEW resn) AFTER alter. The catalog authors selections with the
        correct resn phase; _apply_alter partitions h_ops by op and reorders.

        SELECTION SCOPING (Pitfall 9 backup-independence fix): each h_op sele
        is scoped to ``target`` (``"{target} and {h_op_sele}"``) so the
        remove/h_add steps do NOT affect the backup object (_bak_<target>) or
        other loaded objects. Without scoping, a bare ``"resn HIS and name
        HE2"`` would match atoms in ALL objects including the backup, corrupting
        it (the backup's HE2 would be removed, breaking the SC2 round-trip).

        Translation: the catalog h_ops use "add" (human-readable); the edit_ops
        step dict uses "h_add" (the edit_ops step op). This translation happens
        here: op="add" -> {"op":"h_add","sele":...}.
        """
        # 1. removes: op="remove" h_ops -> {"op":"remove","sele":...} steps
        #    (run BEFORE alter while resn is still the OLD resn). Scoped to
        #    target so the backup is not corrupted.
        removes = [{"op": "remove",
                    "sele": "{0} and {1}".format(target, h["sele"])}
                   for h in spec.get("h_ops", []) if h["op"] == "remove"]
        # 2. alter: the resn rename (sele=target; in Phase 4 target IS the
        #    object name + the residue key -- the alter applies to the whole
        #    object, which is a single residue in the placeholder smoke).
        alter = [{"op": "alter", "sele": target,
                  "expr": "resn='{}'".format(spec["resn"])}]
        # 3. adds: op="add" h_ops -> {"op":"h_add","sele":...} steps
        #    (run AFTER alter while resn is the NEW resn). Scoped to target.
        #    Translation: catalog "add" -> edit_ops step "h_add".
        adds = [{"op": "h_add",
                 "sele": "{0} and {1}".format(target, h["sele"])}
                for h in spec.get("h_ops", []) if h["op"] == "add"]
        # 4. steps = removes + alter + adds (Pitfall 2 ordering).
        steps = removes + alter + adds
        # 5. Delegate to edit_ops.apply_edit (takes the backup + dispatches +
        #    sorts + rebuilds + registers handle + returns RestoreHandle).
        handle = self._edit.apply_edit(target, steps)
        # 6. Track the handle for switch reversal.
        self._backup[target] = handle
