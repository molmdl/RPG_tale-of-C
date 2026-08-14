---
phase: 04-editing-protonation-restore-safety-net
plan: 01
subsystem: editing
tags: [pymol, alter, sort, backup, restore, safety-net, editops, restore-handle]

# Dependency graph
requires:
  - phase: 03-pymol-cmd-layer
    provides: inject-cmd testability pattern (molops.py:80), source-citation convention (molops.py:33-37), MockCmd unit-test pattern (test_molops.py:39-65), empirically-corrected cmd.create default-args backup (STATE.md:84)
provides:
  - EditOps.apply_edit — the sole sanctioned cmd.alter path (step-list dispatch under one backup, always sort+rebuild)
  - RestoreHandle — plain class carrying backup_name + pre_atom_count + pre_residue_signature for SC2 round-trip verification
  - take_backup / restore / restore_from_handle — backup/restore safety net with atom-count + residue-signature verification
  - 4 convenience methods — point_mutation, substrate_remove_group, substrate_add_group, protonation_change (partitions h_ops removes-before-alter adds-after-alter)
  - _collect_residue_signature — sorted (chain,resi,resn) tuple list via cmd.iterate (Pitfall 7 mitigation)
affects: [04-03 (ProtonationManager composes step lists via apply_edit), 04-04 (check_alter_gate allowlists this module), 04-05 (molops edit/restore/protonate delegation)]

# Tech tracking
tech-stack:
  added: []  # PyMOL 2.5.0 APIs only — no new dependencies
  patterns:
    - "Sanctioned-alter-path: single-module allowlist (edit_ops.py is the ONLY place cmd.alter may appear; 04-04's check_alter_gate.py enforces)"
    - "Step-list dispatch: apply_edit takes a LIST of step dicts under ONE backup — ProtonationManager composes its own list; convenience methods build standard lists"
    - "Backup-before-edit: default-args cmd.create (all states) BEFORE any alter/h_add/remove/fuse; take_backup is public so ProtonationManager Mode (a) can call it before delete+load"
    - "Restore-with-verify: delete(obj) THEN create(obj,bak) + sort + rebuild + atom-count check + residue-signature check (SC2 round-trip)"

key-files:
  created:
    - c14/pymol_layer/edit_ops.py  # EditOps + RestoreHandle (273 lines, 16 self._cmd.* calls, 16 # src: citations)
    - tests/test_edit_ops.py       # MockCmd unit tests (393 lines, 17 tests)
  modified: []

key-decisions:
  - "apply_edit(object_name, edit_steps) -> RestoreHandle: the settled signature 04-03 + 04-05 depend on. edit_steps is a LIST of step dicts (not a single edit_type+kwargs) so ProtonationManager can compose multi-step sequences (removes + alter + adds) under ONE backup."
  - "Step-dict schema: {\"op\":\"alter\"|\"h_add\"|\"remove\"|\"fuse\", ...}. alter needs sele+expr; h_add/remove need sele; fuse needs sele1+sele2. Unknown op raises ValueError."
  - "RestoreHandle fields: object_name, backup_name, pre_atom_count, pre_residue_signature (sorted [(chain,resi,resn),...]). Plain class (3.6-compatible, no @dataclass)."
  - "_handles registry: apply_edit registers the handle (take_backup does NOT); restore(obj) looks up by object_name; restore_from_handle pops after restore. This means restore(obj) only works after apply_edit, not after bare take_backup."
  - "protonation_change h_ops partitioning: removes (OLD resn) BEFORE alter, adds (NEW resn) AFTER alter — matches 04-03 _apply_alter (Pitfall 2 ordering). The catalog authors selections with the right resn phase."

patterns-established:
  - "Step-list dispatch pattern: apply_edit takes a composable list of step dicts rather than a fixed edit_type+kwargs signature — lets ProtonationManager build multi-step sequences without calling apply_edit multiple times (one backup covers the whole sequence)"
  - "Explicit-method MockCmd: count_atoms and iterate are explicit methods on MockCmd (not __getattr__ fallback) so they are NOT recorded in self.calls — calls[0] is always the first real dispatch. count_atoms differentiates _bak_ prefix for mismatch testing; iterate populates stored.list from configurable _residue_sig."

# Metrics
duration: 13 min
completed: 2026-08-14
---

# Phase 4 Plan 1: EditOps (Sanctioned alter + Backup/Restore) Summary

**Sanctioned cmd.alter path (EditOps.apply_edit) with mandatory sort+rebuild after every edit, default-args create backup, and SC2 round-trip restore verified by atom count + residue signature**

## Performance

- **Duration:** 13 min
- **Started:** 2026-08-14T18:51:01Z
- **Completed:** 2026-08-14T19:04:39Z
- **Tasks:** 2
- **Files modified:** 2 (both new)

## Accomplishments
- EditOps.apply_edit is the SOLE sanctioned cmd.alter path in the repo — dispatches a LIST of edit step dicts (alter/h_add/remove/fuse) under ONE backup, ALWAYS calls cmd.sort + cmd.rebuild after (the alter->sort trap mitigation, editing.py:1457-1460)
- Backup/restore safety net: take_backup (delete-stale + default-args create + count verify + residue signature) and restore_from_handle (delete-first + create-from-backup + sort + rebuild + atom-count verify + residue-signature verify) — SC2 round-trip mechanics
- 4 convenience methods build standard step lists: point_mutation, substrate_remove_group, substrate_add_group, protonation_change (partitions h_ops into removes-before-alter + adds-after-alter, matching 04-03 _apply_alter)
- Every self._cmd.* call carries a # src: citation (10 unique APIs, 16 call sites, all verified against tmp/pymol-src/modules/pymol/ at the cited file:line)
- 17 MockCmd unit tests prove: dispatch order, sort-after-alter for all 4 ops, backup-before-edit, default-args create, delete-before-create, restore verifies (atom count + residue signature), unknown-step raises, protonation_change partitioning, citation presence, Pitfall 2/3 guards

## Task Commits

Each task was committed atomically:

1. **Task 1: Create edit_ops.py — EditOps + RestoreHandle + apply_edit + convenience methods + backup/restore** - `7a5bcc0` (feat)
2. **Task 2: Create test_edit_ops.py — MockCmd unit tests** - `b01b158` (test)

## Files Created/Modified
- `c14/pymol_layer/edit_ops.py` — EditOps (sanctioned alter path) + RestoreHandle + apply_edit + 4 convenience methods + take_backup + restore + restore_from_handle + _collect_residue_signature (273 lines)
- `tests/test_edit_ops.py` — MockCmd unit tests: dispatch order, sort-after-alter, backup-first, delete-before-create, restore verifies, citations, Pitfall guards (393 lines, 17 tests)

## Decisions Made
- **apply_edit takes a step LIST (not edit_type+kwargs):** The plan's research showed ProtonationManager needs to compose multi-step sequences (removes + alter + adds) under ONE backup. A step-list signature lets the caller compose any sequence without multiple apply_edit calls (which would take multiple backups). The 4 convenience methods build standard lists; ProtonationManager builds its own. This is the contract 04-03 + 04-05 depend on.
- **_handles registry: apply_edit registers, take_backup does NOT:** restore(obj) looks up by object_name in _handles. Only apply_edit registers (step 4). This means restore(obj) works after apply_edit but NOT after a bare take_backup. restore_from_handle works with any handle (no lookup needed). This matches the usage pattern: apply_edit is the normal entry point; take_backup is for ProtonationManager Mode (a) which manages its own handle.
- **MockCmd.count_atoms differentiates _bak_ prefix:** Returns _count_bak for backup names, _count for live objects. This lets the count-mismatch test (test_take_backup_raises_on_count_mismatch) set _count=3, _count_bak=2 to trigger the RuntimeError without affecting other tests.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- An untracked `tests/test_edit_router.py` file appeared during execution (from parallel plan 04-02, which runs in parallel with 04-01 per the ROADMAP). It has 2 errors + 1 failure unrelated to this plan. Verified by running the full suite excluding that file: 140 tests pass (123 prior + 17 new from test_edit_ops) with zero regressions. The file is NOT part of plan 04-01 and was not modified by this execution.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- EditOps.apply_edit is ready for 04-03 (ProtonationManager composes step lists and calls apply_edit) — the `apply_edit(object_name, edit_steps) -> RestoreHandle` signature is settled.
- EditOps is ready for 04-04 (check_alter_gate.py allowlists exactly `c14/pymol_layer/edit_ops.py` — confirmed `self._cmd.alter` appears ONLY on line 129 inside apply_edit's step dispatch).
- EditOps is ready for 04-05 (molops edit/restore/protonate branches delegate to EditOps — the convenience methods + take_backup/restore cover all needed entry points).
- The headless smoke (04-05) will verify the REAL cmd.* contract (the unit tests prove dispatch logic only; the real API contract is deferred to 04-05 per the 3-tier testability pattern).

---
*Phase: 04-editing-protonation-restore-safety-net*
*Completed: 2026-08-14*
