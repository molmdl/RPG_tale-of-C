---
phase: 04-editing-protonation-restore-safety-net
plan: 05
subsystem: editing
tags: [pymol, molops, editops, protonation, headless-smoke, alter-gate, delegation]

# Dependency graph
requires:
  - phase: 04-01 (EditOps)
    provides: "apply_edit + 4 convenience methods + take_backup/restore/restore_from_handle (the sanctioned alter path + backup/restore safety net)"
  - phase: 04-03 (ProtonationManager)
    provides: "ProtonationManager.apply_variant/switch_variant/current_variant/list_variants/restore + protonation_catalog (curated variants)"
  - phase: 04-04 (alter gate + coverage scan + fixtures)
    provides: "check_alter_gate.py AST gate + _edit_smoke.pdb + _his_smoke.pdb fixtures (committed, network-independent)"
  - phase: 03-03 (MolOps)
    provides: "MolOps.apply per-action dispatch (8 ops implemented; edit/protonate/restore were NotImplementedError Phase 4 boundary)"
provides:
  - "molops.apply(MolAction('edit',...)) delegates to EditOps (point_mutation/substrate_remove_group/substrate_add_group/protonation_change by edit_type)"
  - "molops.apply(MolAction('protonate',...)) delegates to ProtonationManager.apply_variant (by variant_id)"
  - "molops.apply(MolAction('restore',...)) delegates to EditOps.restore (by target)"
  - "Backward-compatible constructor widening: MolOps(cmd, asset_manager=None, editops=None, protonation=None)"
  - "Headless edit_smoke.py proving SC1 (byres post-edit) + SC2 (backup/restore round-trip for 3 edit types)"
  - "Headless protonation_smoke.py proving SC4 (apply HID + switch HIE + restore) + EDIT-05 (backup covers protonation)"
  - "Fixed h_ops selection scoping in ProtonationManager._apply_alter (target-scoped selections prevent backup corruption)"
affects: [05.1-story-graph-design, 06-qt-ui-mvp]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Delegation pattern: molops edit/restore/protonate branches delegate to injected EditOps/ProtonationManager (no direct cmd.alter — alter gate stays at edit_ops.py)"
    - "Backward-compatible constructor widening: optional editops=None + protonation=None params (existing MolOps(cmd) calls still work; missing helper -> RuntimeError, not NotImplementedError)"
    - "Headless smoke harness: check()/FAILS/SMOKE_RESULT sentinel (reused from molops_smoke.py); inject REAL pymol.cmd to prove the actual API contract (3-tier testability)"
    - "Target-scoped h_ops selections: ProtonationManager._apply_alter prepends target to each h_op sele to prevent remove/h_add from affecting the backup object"

key-files:
  created:
    - "tools/edit_smoke.py: headless SC1+SC2 smoke (9 stages, EditOps directly on _edit_smoke.pdb)"
    - "tools/protonation_smoke.py: headless SC4+EDIT-05 smoke (8 stages, ProtonationManager on _his_smoke.pdb)"
  modified:
    - "c14/pymol_layer/molops.py: edit/restore/protonate branches delegate to EditOps/ProtonationManager; __init__ gains editops+protonation optional params"
    - "tests/test_molops.py: 3 NotImplementedError tests -> RuntimeError tests; 8 new delegation tests added"
    - "c14/pymol_layer/protonation.py: _apply_alter h_ops selections now scoped to target (Rule 1 bug fix)"
    - "tests/test_protonation_manager.py: updated assertion for scoped h_ops selections"

key-decisions:
  - "Unknown ops still raise NotImplementedError (stray op fails loudly); edit/protonate/restore now raise RuntimeError when their helper is not injected (backward-compatible)"
  - "Phase 4 placeholder: target = residue key (e.g. 'HIS'); _residue_key returns target verbatim; Phase 5+ target schema may need parsing"
  - "h_ops selections scoped to target ('{target} and {h_op_sele}') to prevent backup corruption (Pitfall 9 fix)"

patterns-established:
  - "Delegation over NotImplementedError: Phase 4 replaces NotImplementedError with delegation to injected helpers; missing helper -> RuntimeError (not NotImplementedError)"
  - "Headless smoke proves REAL cmd.* contract: unit tests prove dispatch mapping with MockCmd; headless smokes prove the actual PyMOL API behavior (the alter->sort trap mitigation, backup/restore round-trip, protonation switch)"

# Metrics
duration: 29 min
completed: 2026-08-14
---

# Phase 4 Plan 05: molops edit/restore/protonate delegation + headless SC1+SC2+SC4 smokes Summary

**molops edit/restore/protonate branches now delegate to EditOps + ProtonationManager (no more NotImplementedError); two headless smokes prove SC1 (byres post-edit) + SC2 (backup/restore round-trip for 3 edit types) + SC4 (apply HID + switch HIE + restore) + EDIT-05 (backup covers protonation) against the REAL PyMOL cmd.* contract**

## Performance

- **Duration:** 29 min
- **Started:** 2026-08-14T22:44:59Z
- **Completed:** 2026-08-14T23:14:03Z
- **Tasks:** 3
- **Files modified:** 6 (2 created, 4 modified)

## Accomplishments
- molops.apply(MolAction("edit",...)) delegates to EditOps by edit_type (point_mutation/substrate_remove_group/substrate_add_group/protonation_change) — no more NotImplementedError for edit
- molops.apply(MolAction("protonate",...)) delegates to ProtonationManager.apply_variant by variant_id — no more NotImplementedError for protonate
- molops.apply(MolAction("restore",...)) delegates to EditOps.restore by target — no more NotImplementedError for restore
- Constructor widening is backward-compatible: MolOps(cmd) / MolOps(cmd, am) still work; missing helper -> RuntimeError
- Headless edit_smoke proves SC1 (post-edit byres returns 10 atoms, no silent corruption) + SC2 (backup/restore round-trip for point_mutation + substrate_remove_group + protonation_change) + backup independence (Pitfall 9)
- Headless protonation_smoke proves SC4 (apply HIS_HID: resn->HID, HE2 removed, HD1 kept; switch HIS_HIE: resn->HIE, HD1 removed, HE2 kept; current_variant tracks; list_variants returns 3 tautomers) + EDIT-05 (restore returns pre_count+pre_h_count+resn HIS; backup registered for every apply)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire molops.py edit/restore/protonate branches** - `d798176` (feat)
2. **Task 2: Create tools/edit_smoke.py (SC1+SC2 headless)** - `e9c5ea0` (feat)
3. **Task 3: Create tools/protonation_smoke.py (SC4+EDIT-05 headless) + fix h_ops scoping** - `51d0386` (feat)

## Files Created/Modified
- `c14/pymol_layer/molops.py` - edit/restore/protonate branches delegate to EditOps/ProtonationManager; __init__ gains editops+protonation optional params; unknown ops still raise NotImplementedError
- `tests/test_molops.py` - 3 NotImplementedError tests -> RuntimeError tests; 8 new delegation tests (point_mutation/protonation_change/substrate_remove_group/substrate_add_group/unknown_edit_type/protonate/restore/unknown_op); MockEditOps + MockProtonationManager classes added
- `tools/edit_smoke.py` - NEW headless SC1+SC2 smoke (9 stages: load, pre_signature, apply_point_mutation, sc1_byres_post_edit, sc2_restore_round_trip, backup_independence, substrate_remove_group, protonation_change_via_editops, final)
- `tools/protonation_smoke.py` - NEW headless SC4+EDIT-05 smoke (8 stages: load, pre_state, apply_hid, switch_hie, restore, backup_taken_before_variant, list_variants, final)
- `c14/pymol_layer/protonation.py` - _apply_alter h_ops selections now scoped to target (Rule 1 bug fix: prevents remove/h_add from corrupting the backup)
- `tests/test_protonation_manager.py` - updated assertion for scoped h_ops selections

## Decisions Made
- Unknown ops still raise NotImplementedError (the boundary is preserved for genuinely unknown ops; edit/protonate/restore are now implemented + delegated)
- Phase 4 placeholder: target = residue key (e.g. "HIS" for the protonation smoke); _residue_key returns target verbatim. Phase 5+ target schema (e.g. "pdb:1TNR/chainA/HIS123") may need parsing
- The switch from HID to HIE requires restoring to HIS first (the catalog h_ops use "resn HIS" in remove selections, which requires the current resn to be HIS). This is a Phase 4 placeholder limitation; Phase 5+ may author switch-aware selections

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed h_ops selection scoping in ProtonationManager._apply_alter**
- **Found during:** Task 3 (protonation_smoke headless run)
- **Issue:** The h_ops selections (e.g. "resn HIS and name HE2") were NOT scoped to the target object, so cmd.remove also removed atoms from the backup object (_bak_HIS), corrupting it. This caused "restore atom-count mismatch" errors because the backup's atom count no longer matched the pre-edit count.
- **Fix:** _apply_alter now prepends the target to each h_op sele: `"{target} and {h_op_sele}"`. This scopes the remove/h_add to the target object only, preventing them from affecting the backup or other loaded objects (Pitfall 9 backup-independence fix).
- **Files modified:** c14/pymol_layer/protonation.py, tests/test_protonation_manager.py
- **Verification:** 198 unit tests pass; protonation_smoke SMOKE_RESULT: PASS; alter gate + import gate clean
- **Commit:** 51d0386 (part of Task 3 commit)

**2. [Rule 1 - Bug] Fixed pre_signature assertion in edit_smoke.py**
- **Found during:** Task 2 (edit_smoke headless run)
- **Issue:** The pre_signature assertion expected a 2-tuple per-residue list, but _collect_residue_signature returns a per-ATOM list (17 tuples for 17 atoms). The assertion was wrong.
- **Fix:** Changed the assertion to check the unique-residue SET == {("A","1","ALA"), ("A","2","GLY")} and the list length == atom count (17). The round-trip assertion (sig_restored == pre_sig) still works because both are the same per-atom list.
- **Files modified:** tools/edit_smoke.py
- **Verification:** edit_smoke SMOKE_RESULT: PASS
- **Commit:** e9c5ea0 (part of Task 2 commit)

**3. [Rule 1 - Bug] Used "HIS" as target instead of "scene" in protonation_smoke.py**
- **Found during:** Task 3 (protonation_smoke design)
- **Issue:** The plan specified `pm.apply_variant("scene", "HIS_HID")` but the Phase 4 placeholder _residue_key returns the target verbatim, so the catalog lookup would be lookup("scene", "HIS_HID") which raises KeyError (the catalog has "HIS", not "scene").
- **Fix:** Used "HIS" as the object name + target (the catalog residue key). This is the correct Phase 4 placeholder approach: target IS the residue key.
- **Files modified:** tools/protonation_smoke.py
- **Verification:** protonation_smoke SMOKE_RESULT: PASS
- **Commit:** 51d0386 (part of Task 3 commit)

---

**Total deviations:** 3 auto-fixed (3 bugs)
**Impact on plan:** All auto-fixes necessary for correctness. No scope creep. The h_ops scoping fix is the most significant — it prevents backup corruption in the real PyMOL cmd.* contract (the unit tests with MockCmd didn't catch it because MockCmd doesn't have real objects/backups).

## Issues Encountered
- The h_ops scoping bug was not catchable by the 04-03 unit tests because MockCmd doesn't have real objects or backups — the remove step's sele is just recorded as a string, not executed against real atoms. The headless smoke (with the REAL pymol.cmd) was needed to surface it. This validates the 3-tier testability pattern: unit tests prove dispatch mapping, headless smokes prove the real API contract.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 4 is COMPLETE: all 5 plans done (04-01 EditOps + 04-02 EditRouter + 04-03 ProtonationManager + 04-04 alter gate/coverage scan/fixtures + 04-05 molops delegation + headless smokes). All 5 SCs delivered: SC1 (alter->sort trap mitigated + machine-checkable AST gate + headless byres proof), SC2 (backup/restore round-trip for all 3 edit types, headlessly proven), SC3 (EditRouter routes known->branch, unknown->bad-ending pool, proven in 04-02), SC4 (ProtonationManager applies curated variants + user-adjustable switch, headlessly proven), SC5 (per-enzyme coverage scan green on placeholder cast).
- 198 tests pass; alter gate + import gate + coverage scan all GREEN; 2 headless smokes (edit + protonation) PASS.
- Ready for Phase 5 (Key Decisions + Source Approval) + Phase 5.1 (Story Graph Design) + Phase 5.2 (Representation Design) + Phase 6 (Qt UI MVP).
- The molops edit/protonate/restore delegation contract is the integration record downstream phases read: Phase 5.1 edit-node contract emits MolAction("edit",...) with args["edit_type"]; Phase 6 controller injects EditOps + ProtonationManager into MolOps.

---
*Phase: 04-editing-protonation-restore-safety-net*
*Completed: 2026-08-14*
