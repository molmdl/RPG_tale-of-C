---
phase: 04-editing-protonation-restore-safety-net
verified: 2026-08-15T00:00:00Z
status: passed
score: 5/5 success criteria verified
re_verification: No — initial verification
---

# Phase 4: Editing, Protonation & Restore Safety Net — Verification Report

**Phase Goal:** The highest technical-risk feature — limited molecule editing with a restore safety net — works headlessly: the `alter`→`sort` silent-corruption trap is mitigated by a single sanctioned helper, backups/restore survive any edit, protonation defaults are curated variants (no pH engine), and edit routing (known→branch, unknown→bad-ending pool) is demonstrable end-to-end.

**Verified:** 2026-08-15
**Status:** passed
**Re-verification:** No — initial verification

## Verification Approach

Goal-backward verification against the 5 success criteria (SCs) from ROADMAP.md + the must_haves in all 5 PLAN frontmatters. Every claim below is backed by an actual command run against the real codebase (NOT SUMMARY claims). Gates were run with `python3.6`; headless smokes were run via `bash tools/run_headless.sh <script.py>` (the WSL→Windows PyMOL bridge, verdict via `^SMOKE_RESULT: PASS` stdout sentinel — NOT exit code, since `run-conda-pymol.bat` always returns 0).

## Goal Achievement

### Observable Truths (Success Criteria)

| #  | Truth (Success Criterion) | Status | Evidence |
|----|---------------------------|--------|----------|
| SC1 | `apply_edit` is the only sanctioned alter path (no bare `cmd.alter` outside it); always calls `cmd.sort`+`cmd.rebuild`; headless test confirms post-edit `byres` returns expected atoms | ✓ VERIFIED | `python3.6 tools/check_alter_gate.py` → exit 0 ("clean — no `*.alter(...)` Attribute calls outside `c14/pymol_layer/edit_ops.py`"). `edit_ops.py:129` is the SOLE `self._cmd.alter` call site (inside `apply_edit`'s step dispatch). `edit_ops.py:144,146` ALWAYS call `self._cmd.sort(object_name)` + `self._cmd.rebuild(object_name)` after the step loop. Headless `edit_smoke.py` → `SMOKE_RESULT: PASS`; stage `sc1_byres_post_edit` PASS: `byres=10 gly=10 ala=0` (post-edit byres returns the 10 expected atoms, no silent corruption). |
| SC2 | For each edit type (point mutation, substrate edit, protonation change), backup-before-edit (default-args `cmd.create`, verified by `count_atoms`) + restore (`cmd.delete`+`cmd.create` from backup) returns object to pre-edit atom count + residue identity | ✓ VERIFIED | `edit_ops.py:203` `take_backup`: `self._cmd.create(bak, object_name)` — default-args (all-states, NO `1,1` state args); count_atoms verification at `:207-209`. `edit_ops.py:239-241` `restore_from_handle`: `self._cmd.delete(handle.object_name)` THEN `self._cmd.create(handle.object_name, handle.backup_name)`; round-trip verification (atom count `:248-251` + residue signature `:252-255`). Headless `edit_smoke.py` 3 stages PASS: `sc2_restore_round_trip` (count=17==17, sig matches — point_mutation); `substrate_remove_group` (after_remove=16<17, after_restore=17 — substrate edit); `protonation_change_via_editops` (hid=10, restored=17, sig matches — protonation change). |
| SC3 | EditRouter routes known edit (matching `edits.json` entry) to its story branch; routes unknown edit to bad-ending pool — demonstrated headlessly with fixture edit intents | ✓ VERIFIED | `python3.6 -m unittest tests.test_edit_router -v` → 17 tests OK (exit 0). `edit_router.py:142` `route()`: `entry.get("signature") == sig` (EXACT dict equality for known→branch); `:149` `rng.weighted_pick(list(pool), [1.0] * len(pool))` (unknown→pool). Tests prove: known→branch, unknown→pool, unknown-enzyme→global-pool, empty-pool→`EditRoutingError`, RNG determinism, `validate_edits_table` (6 issue types), `scan_edit_coverage`, + 5 `GameEngine.apply_player_edit` integration tests (known enters branch, unknown enters bad-ending, RNG reproducible, no-router→RuntimeError, backward-compat). `engine.py:135-161` `apply_player_edit`: `route` → `state.add_edit` → `self._enter(node_id)`. |
| SC4 | ProtonationManager applies a curated variant (load pre-built OR `cmd.alter` resn + targeted `h_add`/`remove`); user-adjustable switch between curated variants is exercisable | ✓ VERIFIED | Headless `protonation_smoke.py` → `SMOKE_RESULT: PASS`; stages: `apply_hid` (hid=13, hd1=1, he2=0, cur='HIS_HID'), `switch_hie` (hie=13, hd1=0, he2=1, cur='HIS_HIE' — switch exercisable), `restore` (count=14==14, his=14, h=4==4, cur=None), `backup_taken_before_variant` (handle=True — EDIT-05 covers protonation), `list_variants` (3 HIS tautomers). `protonation.py`: `apply_variant`(:96), `switch_variant`(:119), `current_variant`(:91), `list_variants`(:81) all present; delegates to `edit_ops.apply_edit`(:233) — NO direct `self._cmd.alter`/`self._cmd.h_add` CALLS (only mentions in comments :26,:31). `protonation_catalog.py`: HIS HID/HIE/HIP variants (:42-71), all `claim_id=="PLACEHOLDER_PHASE5"`, NO pKa values. h_ops scoping fix present (:215-217,:226-228): `"{0} and {1}".format(target, h["sele"])`. restore uses `edit_ops.restore_from_handle(self._backup[target])`(:144) — consistent with 04-03's noted deviation. |
| SC5 | Per-enzyme minimum-coverage scan asserts every cast enzyme has ≥1 known-edit entry + restore path; scan green on current enzyme set | ✓ VERIFIED | `python3.6 tools/check_edit_coverage.py` → exit 0: "EDIT COVERAGE PASSED: 1 enzyme(s) covered — each has >=1 edits.json entry. [COVERED] fixture_enzyme_1 (1 edit(s))". `cast.json` enzyme id `fixture_enzyme_1` == `edits.json` enzyme key `fixture_enzyme_1` (matching ids). The restore-path half of SC5 is proven headlessly by SC2 (`edit_smoke.py` round-trip PASS) + SC4 (`protonation_smoke.py` restore PASS). |

**Score:** 5/5 success criteria verified.

### Required Artifacts (Three-Level Verification)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `c14/pymol_layer/edit_ops.py` | EditOps + RestoreHandle + apply_edit + 4 convenience methods + take_backup + restore + restore_from_handle + _collect_residue_signature (min 120 lines, contains `class EditOps`) | ✓ VERIFIED | EXISTS; 273 lines (≥120); `class EditOps`(:84) + `class RestoreHandle`(:58) present; `apply_edit`(:106), `take_backup`(:191), `restore`(:217), `restore_from_handle`(:229), `_collect_residue_signature`(:259), 4 convenience methods (:155-185); WIRED — imported by `molops.py`, `protonation.py`, `edit_smoke.py`. |
| `c14/edit_router.py` | EditRoutingError + EditsTable + EditRouter + validate_edits_table + scan_edit_coverage (min 100 lines, contains `class EditRouter`) | ✓ VERIFIED | EXISTS; 255 lines (≥100); all 5 exports present; WIRED — imported by `engine.py:40`. |
| `c14/protonation_catalog.py` | Pure-data catalog (HIS HID/HIE/HIP + ASP/GLU/LYS/CYS/TYR) + lookup + variants_for (min 80 lines, contains `CATALOG = {`) | ✓ VERIFIED | EXISTS; 210 lines (≥80); `CATALOG = {`(:39); 7 residues × 2-3 variants each; `lookup`(:171), `variants_for`(:192), `residues`(:207); domain-tier pure-data (no pymol import — import gate clean). |
| `c14/pymol_layer/protonation.py` | ProtonationManager (apply_variant/switch_variant/current_variant/list_variants/restore; Mode a/b; min 100 lines, contains `class ProtonationManager`) | ✓ VERIFIED | EXISTS; 235 lines (≥100); `class ProtonationManager`(:58); all 5 public methods present; WIRED — imported by `molops.py`, `protonation_smoke.py`. |
| `c14/pymol_layer/molops.py` | edit/restore/protonate branches implemented (delegate); `__init__` gains editops+protonation optional params (contains `elif op == "edit":`) | ✓ VERIFIED | EXISTS; 205 lines; `elif op == "edit":`(:145), `elif op == "protonate":`(:174), `elif op == "restore":`(:184); `__init__`(:106) `editops=None, protonation=None` optional params; unknown ops still `NotImplementedError`(:195). |
| `c14/story/model.py` | EditIntent class (routing INPUT, separate from MolAction) with signature() normalization | ✓ VERIFIED | EXISTS; `class EditIntent`(:82); `signature()`(:112) normalizes (lowercase+strip target, `_norm_val` args); pure-data, domain-tier. |
| `c14/engine.py` | GameEngine.apply_player_edit + edit_router constructor param (backward-compatible default None) | ✓ VERIFIED | EXISTS; `apply_player_edit`(:135); `edit_router=None`(:88) backward-compat; routes→add_edit→_enter. |
| `tools/check_alter_gate.py` | AST gate enforcing cmd.alter only in edit_ops.py (exit 0/1/2; min 60 lines, contains `ALLOWLIST`) | ✓ VERIFIED | EXISTS; 168 lines (≥60); `ALLOWLIST = {"c14/pymol_layer/edit_ops.py"}`(:49); `find_violations` testable core; exit 0 on real repo. |
| `tools/check_edit_coverage.py` | Per-enzyme min-coverage scan (exit 0/1/2; min 50 lines, contains `def main`) | ✓ VERIFIED | EXISTS; 144 lines (≥50); `def main`(:129); `run_scan` testable core; inline JSON loading (no c14.edit_router import); exit 0 on real repo. |
| `tools/edit_smoke.py` | Headless SC1+SC2 smoke (contains `SMOKE_RESULT`) | ✓ VERIFIED | EXISTS; 222 lines; 8 stages including `sc1_byres_post_edit` + `sc2_restore_round_trip` + `substrate_remove_group` + `protonation_change_via_editops` + `backup_independence`; `SMOKE_RESULT: PASS` confirmed. |
| `tools/protonation_smoke.py` | Headless SC4 smoke (contains `SMOKE_RESULT`) | ✓ VERIFIED | EXISTS; 243 lines; 7 stages including `apply_hid` + `switch_hie` + `restore` + `backup_taken_before_variant` + `list_variants`; `SMOKE_RESULT: PASS` confirmed. |
| `c14/data/cast.json` | PLACEHOLDER cast manifest (one demo enzyme) | ✓ VERIFIED | EXISTS; `fixture_enzyme_1` with `fixture: "_edit_smoke.pdb"`, `claim_id: "PLACEHOLDER_PHASE5"`. |
| `c14/data/edits.json` | PLACEHOLDER edits manifest (one demo known-edit entry) | ✓ VERIFIED | EXISTS; `fixture_enzyme_1` with 1 edit (point_mutation → `fixture.branch_1`), `bad_ending_pool`: 2 nodes. |
| `c14/data/assets/bundled/_edit_smoke.pdb` | 2-residue ALA-GLY peptide fixture | ✓ VERIFIED | EXISTS (1347 bytes); headless smoke confirms 17 atoms, 2 residues (ALA resi 1 + GLY resi 2). |
| `c14/data/assets/bundled/_his_smoke.pdb` | HIS fixture with explicit H atoms (HD1, HE2) | ✓ VERIFIED | EXISTS (1110 bytes); headless smoke confirms 14 atoms, HD1+HE2 present. |
| `tests/test_edit_ops.py` | MockCmd unit tests (min 150 lines, contains `class TestEditOps`) | ✓ VERIFIED | EXISTS; 393 lines (≥150). |
| `tests/test_edit_router.py` | SC3 pure-Python demo (min 120 lines, contains `class TestEditRouter`) | ✓ VERIFIED | EXISTS; 270 lines (≥120); 17 tests pass. |
| `tests/test_protonation_catalog.py` | Pure-Python catalog tests | ✓ VERIFIED | EXISTS; 212 lines. |
| `tests/test_protonation_manager.py` | MockCmd/MockEditOps dispatch tests | ✓ VERIFIED | EXISTS; 478 lines. |
| `tests/test_molops.py` | Updated: edit/restore/protonate delegation assertions REPLACE NotImplementedError assertions | ✓ VERIFIED | EXISTS; 398 lines; NotImplementedError→RuntimeError replacement confirmed (:264-288: edit/protonate/restore raise RuntimeError without helper; unknown op still NotImplementedError); delegation assertions (:290-368) for all 4 edit_types + protonate + restore. |

### Key Link Verification (Wiring)

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `edit_ops.py apply_edit` | `cmd.alter/h_add/remove/fuse` | step dispatch loop | ✓ WIRED | `edit_ops.py:127-141` dispatches 4 step ops; `self._cmd.alter` ONLY at :129 (alter gate confirms sole site). |
| `edit_ops.py apply_edit` | `cmd.sort + cmd.rebuild` | always-after-edit guard | ✓ WIRED | `edit_ops.py:144,146` — unconditional after step loop (the alter→sort trap mitigation). |
| `edit_ops.py take_backup` | `cmd.delete(bak) → cmd.create(bak, obj)` | default-args create | ✓ WIRED | `edit_ops.py:201,203` — `delete` then `create(bak, object_name)` (no state args = all states). |
| `edit_ops.py restore_from_handle` | `cmd.delete → cmd.create → verify` | delete-first round-trip | ✓ WIRED | `edit_ops.py:239-255` — delete then create from backup, then count+signature verify. |
| `edit_router.py route` (known) | `entry["signature"] == sig` | exact dict equality | ✓ WIRED | `edit_router.py:142` — `entry.get("signature") == sig`; returns `entry["branch_node"]` (:143). |
| `edit_router.py route` (unknown) | `rng.weighted_pick(pool, [1.0]*len(pool))` | single injected RngEngine | ✓ WIRED | `edit_router.py:149` — uniform reproducible pick; `EditRoutingError` on empty pool (:146). |
| `engine.py apply_player_edit` | `router.route → state.add_edit → self._enter` | reuse existing _enter+add_edit+sink | ✓ WIRED | `engine.py:155-161` — route, record in edits_history, enter routed node. |
| `protonation.py apply_variant` (Mode b) | `edit_ops.apply_edit` | delegation (sanctioned-alter gate) | ✓ WIRED | `protonation.py:233` — `self._edit.apply_edit(target, steps)`; NO direct `self._cmd.alter`/`h_add`. |
| `protonation.py _apply_alter` | removes + alter + adds step list | h_ops partitioned (remove before, add after) | ✓ WIRED | `protonation.py:215-230` — removes(:215-217) + alter(:221-222) + adds(:226-228); selections scoped to `target` (the 04-05 backup-corruption fix). |
| `protonation.py restore` | `edit_ops.restore_from_handle(self._backup[target])` | EDIT-05 restore safety net | ✓ WIRED | `protonation.py:144` — uses `restore_from_handle` (not `edit_ops.restore`) because `take_backup` (Mode a) doesn't register in `_handles`; consistent with 04-03's noted deviation. |
| `molops.py edit branch` | `editops.point_mutation/substrate_*/protonation_change` | dispatch on `args["edit_type"]` | ✓ WIRED | `molops.py:156-173` — 4 edit_types dispatched; unknown→`ValueError`(:172); no-editops→`RuntimeError`(:155). |
| `molops.py protonate branch` | `protonation.apply_variant` | `args["variant_id"]` | ✓ WIRED | `molops.py:182-183`; no-protonation→`RuntimeError`(:180). |
| `molops.py restore branch` | `editops.restore` | object_name lookup | ✓ WIRED | `molops.py:190`; no-editops→`RuntimeError`(:189). |

### Requirements Coverage

Phase 4 requirements: EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-05, CAST-03.

| Requirement | Status | Evidence |
|-------------|--------|----------|
| EDIT-01 (point mutation) | ✓ SATISFIED | `edit_ops.point_mutation`(:155) + headless `edit_smoke.py` sc2_restore_round_trip PASS (ALA→GLY swap + restore). |
| EDIT-02 (substrate edit) | ✓ SATISFIED | `edit_ops.substrate_remove_group`(:161) + `substrate_add_group`(:166) + headless `substrate_remove_group` stage PASS (remove CA + restore). |
| EDIT-03 (protonation change) | ✓ SATISFIED | `edit_ops.protonation_change`(:171) + `ProtonationManager.apply_variant` + headless `protonation_smoke.py` apply_hid/switch_hie PASS. |
| EDIT-04 (edit routing: known→branch, unknown→bad-ending pool) | ✓ SATISFIED | `edit_router.py` + 17 unit tests pass (known→branch, unknown→pool, RNG determinism, validation, GameEngine integration). |
| EDIT-05 (restore safety net) | ✓ SATISFIED | `edit_ops.restore`/`restore_from_handle` + headless round-trip PASS for all 3 edit types + protonation restore PASS; `protonation.py:179` take_backup before every variant. |
| CAST-03 (curated protonation, no pH engine) | ✓ SATISFIED | `protonation_catalog.py` curated AMBER variants (HIS/ASP/GLU/LYS/CYS/TYR); NO pKa values; `ProtonationManager` is a thin dispatcher (no pH engine); user-adjustable switch proven headlessly. |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `c14/protonation_catalog.py` (all variants), `c14/data/cast.json`, `c14/data/edits.json` | `claim_id: "PLACEHOLDER_PHASE5"` | ℹ️ Info | INTENTIONAL Phase 4 boundary marker — real cited content is Phase 5+ (documented in catalog docstring + STATE.md). NOT a gap; the `test_phase4_placeholder_claim_ids` + `test_no_pka_values_in_catalog` tests enforce this boundary. |
| `protonation.py:159` (`_residue_key` returns target verbatim) | Phase 4 placeholder target schema | ℹ️ Info | INTENTIONAL — Phase 5+ may parse structured targets (e.g. `pdb:1TNR/chainA/HIS123`); documented in docstring. Not a gap for Phase 4. |

No 🛑 Blocker anti-patterns. No ⚠️ Warning TODO/FIXME/empty-return patterns in the phase's source files. The placeholder markers are the designed Phase 4 boundary (mechanics now, cited content Phase 5+), enforced by dedicated tests.

### Human Verification Required

None. Phase 4 is headless-only by design (per the verification brief). All 5 success criteria are proven either by pure-Python unit tests (run in WSL `python3.6`) or by headless PyMOL smokes (via `run-conda-pymol.bat -cq`, verdict via `SMOKE_RESULT: PASS` sentinel). No Qt/GUI code is exercised in this phase — that begins at Phase 6 (the first human-verify milestone).

### Gaps Summary

No gaps found. All 5 success criteria verified, all required artifacts exist + substantive + wired, all key links connected, all 6 requirements satisfied, no blocker anti-patterns.

The two `ℹ️ Info` items (`PLACEHOLDER_PHASE5` claim_ids + placeholder target schema) are the documented Phase 4 boundary — mechanics delivered now, cited content deferred to Phase 5+ — and are enforced by dedicated guard tests, so they are not gaps.

---

## Verification Run Summary (commands actually executed)

| Command | Result |
|---------|--------|
| `python3.6 tools/check_alter_gate.py` | exit 0 — "clean (no `*.alter(...)` Attribute calls outside `c14/pymol_layer/edit_ops.py`)" |
| `python3.6 tools/check_edit_coverage.py` | exit 0 — "EDIT COVERAGE PASSED: 1 enzyme(s) covered" |
| `python3.6 tools/check_imports.py` | exit 0 — "clean (no pymol/PyQt5 imports in c14/ domain tier)" |
| `python3.6 -m unittest tests.test_edit_router -v` | 17 tests OK (exit 0) |
| `python3.6 -m unittest discover -s tests` | 198 tests OK (exit 0) |
| `bash tools/run_headless.sh tools/edit_smoke.py` | PASSED — `SMOKE_RESULT: PASS`; 8/8 stages PASS (incl. `sc1_byres_post_edit` byres=10, `sc2_restore_round_trip`, `substrate_remove_group`, `protonation_change_via_editops`, `backup_independence`) |
| `bash tools/run_headless.sh tools/protonation_smoke.py` | PASSED — `SMOKE_RESULT: PASS`; 7/7 stages PASS (incl. `apply_hid`, `switch_hie`, `restore`, `backup_taken_before_variant`, `list_variants`) |

---

_Verified: 2026-08-15_
_Verifier: OpenCode (gsd-verifier)_
