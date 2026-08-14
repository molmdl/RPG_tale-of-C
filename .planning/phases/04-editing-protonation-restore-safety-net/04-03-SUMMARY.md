---
phase: 04-editing-protonation-restore-safety-net
plan: 03
subsystem: protonation
tags: [pymol, protonation, curated-variants, catalog, his-hid-hie-hip, editops-delegation, alter-gate, placeholder-claim, sc4]

# Dependency graph
requires:
  - phase: 04-editing-protonation-restore-safety-net (plan 04-01)
    provides: EditOps.apply_edit(object_name, edit_steps) -> RestoreHandle (the step-list dispatch under one backup; always sort+rebuild), take_backup (public, returns handle but does NOT register in _handles), restore_from_handle (works with any explicit handle -- the self-managed-handle restore path), RestoreHandle plain class
  - phase: 03-pymol-cmd-layer (plan 03-02)
    provides: AssetManager.load_bundled(filename, object_name) (Mode a load pre-built protonated structure), inject-cmd testability pattern
  - phase: 01-foundations (plan 01-01)
    provides: tools/check_imports.py AST gate (c14/ root scanned; pymol_layer/ excluded), the testability boundary this plan honors
provides:
  - c14/protonation_catalog.py -- pure-data variant CATALOG (HIS HID/HIE/HIP + ASP/GLU/LYS/CYS/TYR placeholder entries, all claim_id=PLACEHOLDER_PHASE5) + lookup/variants_for/residues API
  - c14/pymol_layer/protonation.py -- ProtonationManager (apply_variant/switch_variant/current_variant/list_variants/restore; Mode a/b routing; delegates alter/h_add/remove/sort/rebuild to edit_ops.apply_edit)
  - The h_ops ordering convention encoded as catalog data (remove=OLD resn before alter, add=NEW resn after alter) + enforced by _apply_alter partitioning (Pitfall 2)
  - The "add" -> "h_add" step-op translation (catalog uses human-readable "add"; edit_ops step dict uses "h_add")
  - Phase 4 boundary guards (test_phase4_placeholder_claim_ids + test_no_pka_values_in_catalog) -- enforce the PLACEHOLDER_PHASE5 + no-fabricated-science boundary until Phase 5+
affects: [04-04 (check_alter_gate allowlists edit_ops.py only -- ProtonationManager is NOT in the allowlist because it delegates; 04-04 confirms), 04-05 (molops protonate branch delegates to ProtonationManager.apply_variant; headless protonation_smoke verifies the REAL cmd.* contract), 06 (Phase 6 UI switch calls switch_variant/list_variants/current_variant/restore)]

# Tech tracking
tech-stack:
  added: []  # PyMOL 2.5.0 APIs only (delegated to edit_ops) -- no new dependencies
  patterns:
    - "Catalog Split: pure-data variant table (c14/protonation_catalog.py, domain tier, AST-gate-clean) vs mechanism dispatcher (c14/pymol_layer/protonation.py, gate-exempt). Data is unit-testable in pure WSL; the claim_id audit trail lives in the domain tier (where CITE-01 lives)."
    - "4-dep injection: ProtonationManager(cmd, edit_ops, catalog, assets) -- catalog passed as a MODULE reference so the real c14.protonation_catalog is used in unit tests (no mock needed for the data tier)."
    - "Self-managed handle restore: ProtonationManager tracks its own RestoreHandle in self._backup for both Mode a (take_backup) and Mode b (apply_edit); restore uses edit_ops.restore_from_handle (not edit_ops.restore, which only works after apply_edit registers in _handles). This is the 04-01 contract for callers that manage their own handle."
    - "h_ops resn-phase ordering as catalog data: remove ops use OLD resn in sele, add ops use NEW resn in sele; _apply_alter partitions by op and reorders (removes -> alter -> adds). Encodes Pitfall 2 at the data level + enforces at the mechanism level."

key-files:
  created:
    - c14/protonation_catalog.py          # pure-data variant CATALOG (210 lines; 6 residues x 2-3 variants = 13 entries; lookup/variants_for/residues)
    - c14/pymol_layer/protonation.py      # ProtonationManager (225 lines; 4-dep injection; Mode a/b routing; delegates to edit_ops)
    - tests/test_protonation_catalog.py   # 10 pure-Python catalog tests (schema, lookup, variants_for, residues, PLACEHOLDER guard, no-pKa guard, h_ops resn-phase ordering)
    - tests/test_protonation_manager.py   # 18 MockCmd/MockEditOps dispatch tests (routing, switch state, restore, no-direct-alter AST guard, step ordering, citations)
  modified: []

key-decisions:
  - "Catalog schema: {mode, resn, h_ops, source_file, claim_id, label}. mode in {'load','alter'}; alter entries have resn + h_ops (list); load entries have source_file; every entry has claim_id + label. Phase 4 ships only mode='alter' entries (the load path is exercised by a fake catalog in the unit test)."
  - "h_ops ordering convention (Pitfall 2): remove ops use OLD resn in sele (e.g. 'resn HIS and name HE2'), MUST run BEFORE alter; add ops use NEW resn (e.g. 'resn HID and name ND1'), MUST run AFTER alter. The catalog encodes this at the data level (test_h_ops_remove_uses_old_resn_add_uses_new_resn); _apply_alter partitions + reorders at the mechanism level."
  - "'add' -> 'h_add' step-op translation: the catalog h_ops use human-readable op='add'; the edit_ops step dict uses op='h_add' (the edit_ops step dispatch key). _apply_alter translates: op='add' -> {'op':'h_add','sele':...}. This keeps the catalog human-readable while matching the edit_ops contract."
  - "Self-managed handle restore (Rule 3 deviation): the plan said restore delegates to self._edit.restore(target), but take_backup (Mode a) does NOT register in edit_ops._handles (only apply_edit does -- 04-01 SUMMARY), so edit_ops.restore(target) would raise 'no backup handle registered' for Mode a. Used edit_ops.restore_from_handle(self._backup[target]) instead -- the 04-01 contract for self-managed handles (restore_from_handle works with any explicit handle, no _handles lookup needed). Works for BOTH modes because ProtonationManager tracks the handle in self._backup regardless of mode."
  - "AST-based no-direct-alter guard (Rule 1 deviation): the plan said to text-scan protonation.py for 'self._cmd.alter(' / 'self._cmd.h_add(' but the module docstring DOCUMENTS the gate compliance (mentions the patterns in comments), causing naive substring false positives. Used AST to walk for actual Call nodes (self._cmd.alter/self._cmd.h_add) -- mirrors the check_imports.py AST-gate precedent (Phase 1). Precise on actual calls, immune to comments/docstrings."
  - "Phase 4 boundary guards: test_phase4_placeholder_claim_ids (every claim_id == 'PLACEHOLDER_PHASE5'; FAILS if a real claim_id leaks in -- removed in Phase 5+) + test_no_pka_values_in_catalog (regex scan for pKa/pH/~float/doi -- catches fabricated science). These enforce the 'mechanics not chemistry' boundary until Phase 5 cited content lands."

patterns-established:
  - "Catalog Split pattern: pure-data domain tier (c14/protonation_catalog.py -- which variants exist, which claim_id backs each) vs mechanism tier (c14/pymol_layer/protonation.py -- how to apply a variant via cmd.*). Keeps the catalog unit-testable in pure WSL + the claim_id audit trail in the domain tier (CITE-01)."
  - "4-dep injection with module-as-catalog: ProtonationManager(cmd, edit_ops, catalog, assets) where catalog is a MODULE reference -- the real c14.protonation_catalog is used in unit tests (no mock needed for the data tier; the data is pure + stable). Mocks are only needed for cmd/edit_ops/assets (the mechanism tier)."
  - "AST-based call-site guard: for 'no direct self._cmd.X()' invariants, use AST to walk for actual Call nodes rather than naive substring search (comments/docstrings that DOCUMENT the invariant would false-positive on substring). Mirrors check_imports.py."

# Metrics
duration: 7 min
completed: 2026-08-14
---

# Phase 4 Plan 3: ProtonationManager + Protonation Catalog Summary

**Curated-variant ProtonationManager (SC4) with pure-data catalog (HIS HID/HIE/HIP + ASP/GLU/LYS/CYS/TYR PLACEHOLDER_PHASE5 entries), Mode a/b routing, and edit_ops delegation keeping the alter gate at ONE module**

## Performance

- **Duration:** 7 min
- **Started:** 2026-08-14T19:24:18Z
- **Completed:** 2026-08-14T19:31:22Z
- **Tasks:** 2
- **Files modified:** 4 (all new)

## Accomplishments
- Built the pure-data protonation_catalog (c14/protonation_catalog.py, 210 lines): CATALOG dict with 6 residues (HIS/ASP/GLU/LYS/CYS/TYR) x 2-3 variants each (13 entries total), all claim_id="PLACEHOLDER_PHASE5" (standard AMBER nomenclature only; NO pKa values, NO DOIs -- Phase 4 ships mechanics not cited content). Functions: lookup (raises clear KeyError), variants_for, residues. The h_ops ordering convention (remove=OLD resn before alter, add=NEW resn after alter -- Pitfall 2) is encoded as catalog-level data.
- Built the ProtonationManager (c14/pymol_layer/protonation.py, 225 lines): 4-dep injection (cmd, edit_ops, catalog, assets); apply_variant/switch_variant/current_variant/list_variants/restore API; Mode (a) load routing (edit_ops.take_backup + cmd.delete + assets.load_bundled); Mode (b) alter routing (delegates to edit_ops.apply_edit with steps = removes + alter + h_add, Pitfall 2 ordering). Does NOT call self._cmd.alter or self._cmd.h_add ANYWHERE (AST-verified -- the alter gate allowlist stays at edit_ops.py only). Every apply_variant takes a backup via edit_ops so EDIT-05 covers protonation.
- 28 pure-Python tests pass (10 catalog + 18 manager): schema validation, lookup/variants_for/residues, PLACEHOLDER_PHASE5 + no-pKa boundary guards, h_ops resn-phase ordering invariant, Mode a/b dispatch routing, switch state recording, restore clears state, no-direct-alter AST guard, step ordering (Pitfall 2), citation presence. Full suite 185 tests green (157 prior + 28 new), zero regressions.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create c14/protonation_catalog.py (pure-data variant table) + tests/test_protonation_catalog.py** - `3323e7e` (feat)
2. **Task 2: Create c14/pymol_layer/protonation.py (ProtonationManager) + tests/test_protonation_manager.py** - `bba108d` (feat)

## Files Created/Modified
- `c14/protonation_catalog.py` -- Pure-data variant CATALOG (6 residues x 2-3 variants = 13 PLACEHOLDER_PHASE5 entries) + lookup/variants_for/residues (210 lines)
- `c14/pymol_layer/protonation.py` -- ProtonationManager (apply_variant/switch_variant/current_variant/list_variants/restore; Mode a/b routing; delegates to edit_ops; 225 lines)
- `tests/test_protonation_catalog.py` -- 10 pure-Python catalog tests (schema, lookup, PLACEHOLDER guard, no-pKa guard, h_ops resn-phase ordering)
- `tests/test_protonation_manager.py` -- 18 MockCmd/MockEditOps dispatch tests (routing, switch state, restore, no-direct-alter AST guard, step ordering, citations)

## Decisions Made
- **Catalog Split (data vs mechanism):** The variant CATALOG (which variants exist, which claim_id backs each) lives in c14/protonation_catalog.py (pure data, domain tier, AST-gate-clean); the ProtonationManager (how to apply a variant via cmd.*) lives in c14/pymol_layer/protonation.py (gate-exempt). This keeps the catalog unit-testable in pure WSL + the claim_id audit trail in the domain tier (where CITE-01 lives). Matches the 04-RESEARCH-protonation.md "Pattern 2: Catalog Split" recommendation.
- **4-dep injection with module-as-catalog:** ProtonationManager(cmd, edit_ops, catalog, assets) where catalog is the c14.protonation_catalog MODULE (passed as a module reference). Unit tests use the REAL catalog (no mock needed for the data tier -- it's pure + stable); mocks are only needed for cmd/edit_ops/assets (the mechanism tier). Mirrors the molops.py inject pattern but with the catalog as a 4th dep.
- **'add' -> 'h_add' step-op translation:** The catalog h_ops use human-readable op="add"; the edit_ops step dict uses op="h_add" (the edit_ops step dispatch key). _apply_alter translates: op="add" -> {"op":"h_add","sele":...}. This keeps the catalog human-readable while matching the 04-01 edit_ops contract.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used restore_from_handle instead of edit_ops.restore(target) for the restore path**
- **Found during:** Task 2 (ProtonationManager restore implementation)
- **Issue:** The plan said restore delegates to `self._edit.restore(target)` (the 04-01 EditOps.restore looks up the handle in _handles). But Mode (a) `_apply_load` calls `self._edit.take_backup(target)`, and per the 04-01 SUMMARY, `take_backup` does NOT register the handle in `edit_ops._handles` (only `apply_edit` does). So `edit_ops.restore(target)` would raise "no backup handle registered" for Mode (a). The plan's literal `self._edit.restore(target)` wouldn't work for Mode (a).
- **Fix:** Used `self._edit.restore_from_handle(self._backup[target])` instead -- the 04-01 contract for self-managed handles (restore_from_handle works with any explicit handle, no _handles lookup needed). ProtonationManager tracks its own handle in `self._backup` for BOTH modes (Mode a take_backup + Mode b apply_edit both return a handle stored in self._backup). The test was adjusted to assert `restore_from_handle` was called with the stored handle (not `restore(target)`).
- **Files modified:** c14/pymol_layer/protonation.py (restore method), tests/test_protonation_manager.py (test_restore_clears_state)
- **Verification:** test_restore_clears_state passes -- restore clears state + calls restore_from_handle with the stored handle; test_restore_no_backup_raises passes -- raises RuntimeError when no backup registered.
- **Committed in:** bba108d (Task 2 commit)

**2. [Rule 1 - Bug] AST-based no-direct-alter guard instead of naive substring scan**
- **Found during:** Task 2 (test_protonation_manager_no_direct_alter)
- **Issue:** The plan said to read protonation.py as text and assert NO `self._cmd.alter(` and NO `self._cmd.h_add(` substrings. But the module docstring DOCUMENTS the gate compliance (mentions "self._cmd.alter(...)" and "self._cmd.h_add(...)" in comments explaining the invariant), causing naive substring false positives. The text scan failed.
- **Fix:** Used AST to walk for actual `Call` nodes where func is `self._cmd.alter` / `self._cmd.h_add` (Attribute(attr=alter|h_add) on Attribute(attr=_cmd) on Name(id=self)). Mirrors the check_imports.py AST-gate precedent (Phase 1) -- precise on actual call expressions, immune to comments/docstrings.
- **Files modified:** tests/test_protonation_manager.py (test_protonation_manager_no_direct_alter)
- **Verification:** test_protonation_manager_no_direct_alter passes -- AST walk finds zero direct alter/h_add Call nodes; the gate invariant is precisely enforced.
- **Committed in:** bba108d (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both auto-fixes necessary for correctness. The restore_from_handle fix honors the plan's intent (EDIT-05 covers protonation; restore delegates to edit_ops + verifies round-trip) while using the correct 04-01 contract for self-managed handles. The AST guard fix makes the no-direct-alter invariant precise (no false positives from documentation). No scope creep.

## Issues Encountered
- An untracked `tests/test_check_alter_gate.py` + `tools/check_alter_gate.py` + `tools/check_edit_coverage.py` appeared during execution (from parallel plan 04-04, which runs in parallel with 04-03 per the ROADMAP). The test file has 1 failure (`test_syntax_error_reported_as_error_not_violation`) unrelated to this plan. Verified by running the full suite excluding that file: 185 tests pass (157 prior + 28 new from 04-03) with zero regressions. The files are NOT part of plan 04-03 and were not modified by this execution. This is the same parallel-execution situation documented in the 04-01 SUMMARY.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- ProtonationManager is ready for 04-04 (check_alter_gate allowlists edit_ops.py only -- ProtonationManager is NOT in the allowlist because it delegates; 04-04 confirms `self._cmd.alter` appears NOWHERE in protonation.py actual code, only in edit_ops.py).
- ProtonationManager is ready for 04-05 (molops `protonate` branch delegates to ProtonationManager.apply_variant(target, variant_id); the headless protonation_smoke verifies the REAL cmd.* contract -- the unit tests prove dispatch logic only; the real API contract is deferred to 04-05 per the 3-tier testability pattern).
- The `apply_variant(target, variant_id)` + `switch_variant` + `current_variant` + `list_variants` + `restore` API is ready for the Phase 6 UI switch (SC4 user-adjustable switch between curated variants).
- Phase 5+ content approval will replace the PLACEHOLDER_PHASE5 claim_ids with real cited claim_ids; the test_phase4_placeholder_claim_ids guard is REMOVED then. The test_no_pka_values_in_catalog guard stays (fabricated science is never allowed).

---
*Phase: 04-editing-protonation-restore-safety-net*
*Completed: 2026-08-14*
