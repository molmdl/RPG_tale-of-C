---
phase: 03-pymol-cmd-layer-asset-mgmt
verified: 2026-08-14T05:09:49Z
status: passed
score: 4/4 success criteria verified
re_verification: No — initial verification
---

# Phase 3: PyMOL cmd Layer + Asset Mgmt Verification Report

**Phase Goal:** The molecular layer is proven against the real PyMOL 2.5.0 API headlessly — structures load/fetch correctly, MolActions translate to the right `cmd.*` calls, and the known API pitfalls (`cmd.create` incomplete-multi-state-backup + destructive-self-copy [empirically corrected from the 'no-op' claim], `cmd.fetch` async/CIF/cwd defaults) are surfaced and mitigated before any editing or UI code depends on them.

**Verified:** 2026-08-14T05:09:49Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Phase 3 Success Criteria)

| #   | Truth (SC)                                                                                                                                                                                                                                                                                                                                 | Status     | Evidence (from ACTUAL code + run output, not SUMMARY claims)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | An api-sanity headless smoke (via `run-conda-pymol.bat -cq`) exercises each `cmd.*` call the game will use (load, fetch, show, hide, select, zoom, color, delete, create-for-backup) with post-condition assertions and passes via a `SMOKE_RESULT: PASS` stdout sentinel grepped by the bash harness (REINTERPRETED from "exit code 0" — the bat ALWAYS returns 0) | ✓ VERIFIED | `bash tools/run_headless.sh tools/api_sanity_smoke.py` → `PASSED` (exit 0). Captured output (`/tmp/opencode/api_sanity_smoke.txt`) shows all 10 stages `SMOKE: PASS`: load atoms=3, fetch_cid atoms=21, fetch_pdb atoms=327, show_rep rep-sticks=3, show_as rep-lines=3, select n=1, zoom, color, create_backup bak=3 smk=3, delete post=?smk->0. Final sentinel `SMOKE_RESULT: PASS`. `tools/run_headless.sh:46` greps `^SMOKE_RESULT: PASS` (PASS-presence check, NOT `$?`). Smoke uses default-args `cmd.create("bak","smk")` (line 154, NOT 1,1) and `?`-prefix delete post-condition `count_atoms("?smk")` (line 171). |
| 2   | AssetManager resolves a bundled PDB and a fetched PubChem substrate (`cmd.fetch` with `type='cid'`, `async_=0`, explicit `path=<plugin data dir>`) to local files, loading each into a non-empty PyMOL object (verified by `count_atoms`) — downloads land in the plugin data dir regardless of cwd                                            | ✓ VERIFIED | `bash tools/run_headless.sh tools/asset_smoke.py` → `PASSED`. All 4 stages `SMOKE: PASS`: load_bundled atoms=3 (bundled fixture, no network), fetch_pubchem atoms=21 (CID 2244), fetch_pubchem_file_landed at `C:\Users\nglok\...\c14\data\assets\downloaded\cid_2244.sdf` (cwd-independence — SC #2), fetch_pdb atoms=327 (1crn). `asset_manager.py:107` `self._cmd.fetch(str(cid), object_name, type=kind, async_=0, path=d)` — all 3 Pitfall 5 mitigations present. 8 MockCmd unit tests pass (absolute path, type/async_/path kwargs, RuntimeError on empty).                                                   |
| 3   | MolOps translates a queued MolAction list (hide_all, load, show, zoom, color) to the correct `cmd.*` sequence, and a headless smoke confirms the resulting object has the expected representation visible (asserted via `count_atoms` on the shown selection — the `rep <name>` selection keyword)                                            | ✓ VERIFIED | `bash tools/run_headless.sh tools/molops_smoke.py` → `PASSED`. Core SC #3 assertion `molops_scene_rep_visible` rep-sticks=3 `SMOKE: PASS` — `count_atoms("scene & rep sticks") > 0` after queueing `[hide_all, load(bundled), show(sticks), zoom, color]` and dispatching per-action via `molops.apply(a)`. Also: molops_scene_loaded atoms=3, molops_hide_all_cleared rep-lines=0, molops_show_as_atomic rep-lines=3 rep-sticks=0, molops_delete_post ?scene->0. 18 MockCmd/MockAssets unit tests pass (8 dispatch + 5 load-delegation + 4 Phase4-NotImplementedError boundary).                                |
| 4   | Every `cmd.*` call introduced carries a `file:line` source-citation comment referencing `tmp/pymol-src/modules/pymol/` (the "read the source first" convention is established)                                                                                                                                                              | ✓ VERIFIED | Citation grep counts: api_sanity_smoke.py=22, asset_manager.py=4, molops.py=8, asset_smoke.py=3, molops_smoke.py=6 (all exceed their plan thresholds: >=10, >=3, >=7 respectively). All 6 cited source files EXIST in `tmp/pymol-src/modules/pymol/` (importing.py, viewing.py, selecting.py, creating.py, commanding.py, querying.py). Spot-checked line numbers accurate: importing.py:635 `def load(...)`, importing.py:1323 `def fetch(...)`, creating.py:960 `def create(name, selection, source_state=0, ...)`, commanding.py:496 `def delete(name,_self=cmd):`. Unit tests `test_citations_present_in_source` (both asset + molops) assert presence machine-checkably.     |

**Score:** 4/4 success criteria verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tools/api_sanity_smoke.py` | Headless api-sanity smoke (every cmd.* call + post-conditions + SMOKE_RESULT sentinel) | ✓ VERIFIED | 179 lines; EXISTS, SUBSTANTIVE (10 stages, real cmd.* calls, no stubs), WIRED (imports c14.paths, calls pymol.finish_launching, run_headless.sh greps its sentinel). 22 `# src:` citations. Ran headless → all 10 stages PASS. |
| `tools/run_headless.sh` | Reusable bash wrapper for WSL→Windows headless bridge (greps ^SMOKE_RESULT: PASS) | ✓ VERIFIED | 53 lines; EXISTS, SUBSTANTIVE (wslpath -w, timeout 150, grep PASS-presence), WIRED (calls `C:\src\run-conda-pymol.bat -cq`, greps sentinel). Executable bit set. Used by all 3 smokes. |
| `c14/data/assets/bundled/_smoke.pdb` | Tiny 3-atom PDB fixture (one atom named C1) for load test | ✓ VERIFIED | 4 lines (3 ATOM records C1/O1/C2 + END); EXISTS, SUBSTANTIVE, WIRED (loaded by all 3 smokes; git-tracked). |
| `.gitignore` | Excludes `c14/data/assets/downloaded/` runtime cache | ✓ VERIFIED | Line 20 `c14/data/assets/downloaded/`. `git check-ignore downloaded/test.txt` → path printed (exit 0 = ignored); `git check-ignore bundled/_smoke.pdb` → nothing (exit 1 = NOT ignored). `git ls-files bundled/_smoke.pdb` → tracked. |
| `.planning/research/PITFALLS.md` | Pitfall 3 empirically corrected (no longer "no-op") | ✓ VERIFIED | Line 63 title corrected; line 70 EMPIRICALLY CORRECTED 2026-08-14 note (1,1 drops multi-state; self-copy destructive; default-args working); line 84 corrected Known-traps bullet. |
| `c14/pymol_layer/asset_manager.py` | AssetManager (load_bundled/fetch_pubchem/fetch_pdb; inject cmd; Pitfall 5 mitigations) | ✓ VERIFIED | 127 lines; EXISTS, SUBSTANTIVE (3 real methods + _download_dir, inject cmd, no pymol at top), WIRED (imports c14.paths, fetch calls pass type=/async_=0/path=, count_atoms post-conditions). 4 `# src:` citations. 8 unit tests pass. |
| `tests/test_asset_manager.py` | MockCmd unit tests (dispatch/path/args + citations; pure WSL python3.6) | ✓ VERIFIED | 174 lines; EXISTS, SUBSTANTIVE (8 tests in 4 classes, MockCmd with explicit count_atoms), WIRED (imports AssetManager, runs under python3.6 with no pymol). All 8 pass. |
| `tools/asset_smoke.py` | Headless smoke for AssetManager (real cmd.* + count_atoms + SMOKE_RESULT sentinel) | ✓ VERIFIED | 130 lines; EXISTS, SUBSTANTIVE (4 stages, injects real pymol.cmd), WIRED (imports AssetManager, calls finish_launching). Ran headless → all 4 stages PASS. |
| `c14/pymol_layer/molops.py` | MolOps (per-action apply() dispatch + NotImplementedError for Phase 4 ops) | ✓ VERIFIED | 128 lines; EXISTS, SUBSTANTIVE (8 implemented ops + NotImplementedError boundary + apply_all), WIRED (imports MolAction, injects cmd+AssetManager, load delegates to AssetManager). 8 `# src:` citations (7 call sites + 1 header). 18 unit tests pass. |
| `tests/test_molops.py` | MockCmd/MockAssets unit tests (per-op dispatch + citations; pure WSL python3.6) | ✓ VERIFIED | 233 lines; EXISTS, SUBSTANTIVE (18 tests in 4 classes, MockCmd + MockAssets), WIRED (imports MolOps + MolAction, runs under python3.6 with no pymol). All 18 pass. |
| `tools/molops_smoke.py` | Headless smoke queueing [hide_all,load,show,zoom,color] → count_atoms('scene & rep sticks')>0 + SMOKE_RESULT sentinel | ✓ VERIFIED | 180 lines; EXISTS, SUBSTANTIVE (5 post-condition stages + dispatch loop, injects real pymol.cmd + real AssetManager), WIRED (imports MolAction+AssetManager+MolOps, calls finish_launching). Ran headless → molops_scene_rep_visible rep-sticks=3 PASS (SC #3 proven). |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `tools/api_sanity_smoke.py` | `c14.paths.data_path` | `import c14.paths; resolve bundled fixture + downloaded dir as absolute paths` | ✓ WIRED | Line 40 `import c14.paths`; lines 58, 71, 86 call `c14.paths.data_path(...)`. Smoke load stage confirms absolute path resolves (atoms=3). |
| `tools/api_sanity_smoke.py` | `pymol.finish_launching` | completes PyMOL startup before any cmd.* call (Gotcha #6) | ✓ WIRED | Line 43 `pymol.finish_launching()` before any cmd.* call. |
| `tools/run_headless.sh` | stdout SMOKE_RESULT sentinel | `grep ^SMOKE_RESULT: PASS` (verdict via stdout, NOT $? which is always 0) | ✓ WIRED | Line 46 `if grep -q "^SMOKE_RESULT: PASS" "$OUT"; then` — PASS-presence check (absence = fail). |
| `c14/pymol_layer/asset_manager.py` | `c14.paths.data_path` | absolute path resolution for bundled fixture + downloaded dir (cwd-independent) | ✓ WIRED | Lines 74, 89 call `c14.paths.data_path(...)`. Unit test asserts `os.path.isabs(args[0])`. |
| `c14/pymol_layer/asset_manager.py` | `cmd.fetch` | `type=, async_=0, path=<abs dir>` (Pitfall 5a/b/c mitigation) | ✓ WIRED | Lines 107, 122 `self._cmd.fetch(str(...), object_name, type=..., async_=0, path=d)`. Unit tests assert all 3 kwargs. |
| `c14/pymol_layer/asset_manager.py` | `cmd.count_atoms` | post-condition assertion (count_atoms > 0 after load/fetch) | ✓ WIRED | Lines 91, 108, 123 `if self._cmd.count_atoms(...) <= 0: raise RuntimeError(...)`. |
| `c14/pymol_layer/molops.py` | `c14.story.model.MolAction` | import the pure-data carrier (ALLOWED — molops is gate-excluded; MolAction has no pymol import) | ✓ WIRED | Line 67 `from c14.story.model import MolAction`. AST gate clean (MolAction imports only stdlib — verified). |
| `c14/pymol_layer/molops.py` | `c14/pymol_layer/asset_manager.py` | `load` op delegates to AssetManager (fetch_pubchem/fetch_pdb/load_bundled per args['source']) | ✓ WIRED | Lines 109, 111, 113 `self._assets.fetch_pubchem/fetch_pdb/load_bundled(...)`. 5 unit tests verify all delegation paths + RuntimeError when no AssetManager. |
| `c14/pymol_layer/molops.py` | `cmd.*` (hide/show/show_as/select/zoom/color/delete) | the per-action dispatch target; every call cited with # src: | ✓ WIRED | Lines 88, 91, 94, 97, 100, 103, 116 — 7 direct `self._cmd.*` call sites, each with `# src:` comment above. 8 dispatch unit tests assert exact (name, args, kwargs) tuples. |

### Requirements Coverage

| Requirement | Status | Evidence |
| ----------- | ------ | -------- |
| **CAST-02**: Small-molecule substrates (the C14 hero + intermediates) are 3D models from PubChem (via `cmd.fetch type='cid'/'sid'`) or PDB (via `cmd.fetch type='pdb'`) | ✓ SATISFIED | `AssetManager.fetch_pubchem(cid, object_name, kind="cid")` supports cid AND sid (kind param), calls `cmd.fetch` with `type=kind` — headless-verified (CID 2244 → 21 atoms). `AssetManager.fetch_pdb(code, object_name, ftype="pdb")` calls `cmd.fetch` with `type=ftype` (default "pdb") — headless-verified (1crn → 327 atoms). `MolOps` `load` op delegates to AssetManager per `args["source"]` (cid/pdb/bundled) — unit-tested for all 3 paths. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `c14/pymol_layer/molops.py` | 63, 64, 77, 118 | `NotImplementedError` | ℹ️ Info (intentional) | By design — explicit Phase 4 boundary for edit/protonate/restore ops. Documented in PLAN + SUMMARY; unit-tested (`TestMolOpsPhase4Boundary`). NOT a stub; a deliberate fail-loud boundary so a stray MolAction never silently no-ops. |
| `tests/test_citations.py`, `tests/test_integration.py` | various | "placeholder" | ℹ️ Info (prior-phase) | Test fixtures in Phase 1/2 test files (citation registry), NOT Phase 3 files. Legitimate test-data string ("placeholder-claim-1"), not a stub pattern. |

**No blocker anti-patterns found in any Phase 3 file.** No TODO/FIXME/empty-returns/console.log-only implementations in the 8 Phase 3 files.

### Human Verification Required

None. Phase 3 is ALL headless (no Qt/GUI per AGENTS.md). The phase goal explicitly requires the molecular layer be "proven against the real PyMOL 2.5.0 API headlessly" — the three headless smokes (api_sanity, asset, molops) are the verification mechanism, and all three PASSED with their critical post-conditions green:
- api_sanity: 10/10 stages PASS (every cmd.* call the game will use)
- asset: 4/4 stages PASS (load_bundled + fetch_pubchem + file-landed-cwd-independence + fetch_pdb)
- molops: 5/5 post-condition stages PASS + dispatch loop no-exception (SC #3 `rep sticks` visible assertion = 3)

The `rep <name>` selection keyword is the headless-assertable proxy for "representation visible" (empirically confirmed in 03-RESEARCH.md §2), so no GUI visual check is needed to confirm SC #3.

### Gaps Summary

**No gaps found.** All 4 Phase 3 success criteria are verified against the ACTUAL codebase (not SUMMARY claims):

1. **SC #1 (api-sanity smoke):** `bash tools/run_headless.sh tools/api_sanity_smoke.py` → `PASSED`, all 10 cmd.* stages green, `SMOKE_RESULT: PASS` sentinel grepped by the harness (NOT exit code — the bat always returns 0). The `cmd.create` pitfall is empirically corrected in PITFALLS.md (default-args working; 1,1 drops multi-state; self-copy destructive) and the smoke uses default-args `cmd.create("bak","smk")` + `?`-prefix delete post-condition.

2. **SC #2 (AssetManager):** `bash tools/run_headless.sh tools/asset_smoke.py` → `PASSED`. load_bundled (3 atoms, no network), fetch_pubchem (CID 2244 → 21 atoms), fetch_pubchem_file_landed (file at absolute `C:\...\c14\data\assets\downloaded\cid_2244.sdf` — cwd-independence proven), fetch_pdb (1crn → 327 atoms). All fetch calls pass `type=, async_=0, path=<abs dir>` (Pitfall 5 mitigations — unit-tested + headless-verified).

3. **SC #3 (MolOps):** `bash tools/run_headless.sh tools/molops_smoke.py` → `PASSED`. Queued `[hide_all, load(bundled), show(sticks), zoom, color]` dispatched per-action via `molops.apply(a)` → `count_atoms("scene & rep sticks") = 3 > 0` (representation visible via the `rep` keyword). 18 MockCmd/MockAssets unit tests verify the per-op dispatch mapping + load delegation + Phase 4 NotImplementedError boundary.

4. **SC #4 (source-citation convention):** Every cmd.* call carries a `# src: tmp/pymol-src/modules/pymol/<file>.py:<line> cmd.<name>` comment (greppable counts: 22/4/8/3/6 across the 5 files; all exceed plan thresholds). All cited source files exist; spot-checked line numbers accurate (load@635, fetch@1323, create@960, delete@496). Citation presence is machine-checked by unit tests.

**Supporting evidence (all run during verification, not trusted from SUMMARYs):**
- `python3.6 -m py_compile` on all 7 Phase 3 .py files → exit 0
- `python3.6 tools/check_imports.py` → exit 0 (domain tier pure; pymol_layer gate-excluded)
- `python3.6 -m unittest tests.test_asset_manager tests.test_molops -v` → 26 tests OK
- `python3.6 -m unittest discover -s tests` → 123 tests OK (no regressions; matches SUMMARY claim)
- `git check-ignore` → downloaded/ ignored, bundled/ tracked (matches SUMMARY claim)
- 3 headless smokes → all `PASSED` via `^SMOKE_RESULT: PASS` sentinel

**Phase 3 goal is achieved.** The molecular layer is proven against the real PyMOL 2.5.0 API headlessly; the `cmd.create` and `cmd.fetch` pitfalls are surfaced and mitigated before any editing (Phase 4) or UI (Phase 6) code depends on them. The phase is ready to proceed.

---

_Verified: 2026-08-14T05:09:49Z_
_Verifier: OpenCode (gsd-verifier)_
