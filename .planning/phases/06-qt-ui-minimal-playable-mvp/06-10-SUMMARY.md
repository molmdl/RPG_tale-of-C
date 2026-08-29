---
phase: 06-qt-ui-minimal-playable-mvp
plan: 10
subsystem: ui
tags: [qt, pymol, bulk-download, cmd-fetch, progress-dialog, offline-fallback, cast-schema, mockcmd, wsl-testable]

# Dependency graph
requires:
  - phase: 06-02
    provides: "c14.paths.user_data_path() (Phase 6 user-data convention; not used directly here but the offline-lock UI this plan feeds builds on the same resolver)"
  - phase: 03-02
    provides: "AssetManager.fetch_pdb (type=pdb/async_=0/path=<abs> Pitfall-5 mitigations + RuntimeError on count_atoms<=0 = per-file failure signal)"
  - phase: 01-02
    provides: "c14.paths.data_path() (cwd-independent __file__-relative resolver for the downloaded-dir existence check + the bundled cast.json default)"
provides:
  - "c14/data/cast.json schema extension (source: bundled|download + pdb_id + character per enzyme) -- the expected-large-PDB list"
  - "c14/ui/bulk_download.py -- Qt-free BulkDownloadRunner (missing_large_pdbs, run_bulk_download, characters_to_lock, expected_download_characters), WSL-testable with MockCmd"
  - "c14/ui/bulk_download_dialog.py -- BulkDownloadDialog (QProgressDialog wrapper) + maybe_run_bulk_download one-time-prompt helper"
  - "tests/test_bulk_download.py -- 11 MockCmd unit tests (PLACEHOLDER skip, missing/existing detection, success, failure-continues, cancel-between, on_progress, characters_to_lock, Qt-free import)"
affects: [06-08, 06-14, 07-content-glucose, 09-content-full-cast]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Qt-free runner in c14/ui/ (gate-EXEMPT dir) importing NO pymol.Qt -- cmd injected as a function param (mirrors AssetManager); WSL-unit-testable with MockCmd; the QDialog wrapper imports pymol.Qt and calls the runner via on_progress/on_cancel_check callbacks"
    - "Per-FILE progress loop with QApplication.processEvents() BETWEEN fetches (NOT per-byte -- cmd.fetch(async_=0) is sync + blocking with NO progress callback, importing.py:1386-1393); cancel-between-fetches (Pitfall 7); retry = free idempotent cache (cmd.fetch skips existing, importing.py:1211-1213)"
    - "Per-character offline lock (Pattern 2): failed downloads -> characters_to_lock -> lock ONLY affected characters; glucose's bundled structures keep it always playable (SC4)"
    - "PLACEHOLDER guard in missing_large_pdbs: pdb_id.startswith('PLACEHOLDER') entries skipped so the prompt does NOT fire for placeholder content (Phase 6); Phase 7's real entries trigger it"

key-files:
  created:
    - c14/ui/bulk_download.py
    - c14/ui/bulk_download_dialog.py
    - tests/test_bulk_download.py
  modified:
    - c14/data/cast.json

key-decisions:
  - "object_name = enzyme_id (the PyMOL object name the story graph's `load` MolAction references); Phase 7 may revisit if a different convention emerges -- documented in bulk_download.py:missing_large_pdbs"
  - "Qt-free runner lives in c14/ui/ (gate-EXEMPT) but imports NO pymol.Qt -- kept WSL-testable by injecting cmd as a function param (AssetManager pattern); the QDialog wrapper (bulk_download_dialog.py) imports pymol.Qt and is py_compile-only in WSL"
  - "maybe_run_bulk_download returns a dict {ran, failed, canceled, locked_characters} + duck-typed _apply_lock(controller, ...) -- decoupled from the 06-08 controller's exact API; if 06-08 names the lock method differently, update _apply_lock (single point of contact)"
  - "On cancel-no-retry: lock characters whose structures are STILL missing (re-run missing_large_pdbs) -- SC4-correct (locks only affected characters, not the whole game)"
  - "Phase 6 cast.json keeps the real per-enzyme large-PDB list MINIMAL/PLACEHOLDER (PLACEHOLDER_large_enzyme with pdb_id PLACEHOLDER_PDB) -- no fabricated PDB IDs (05.4 no-fabricated-science); Phase 7 fills the real list"

patterns-established:
  - "Qt-free-runner + QDialog-wrapper split: heavy loop logic in a Qt-free module (MockCmd-testable in WSL) + a thin Qt wrapper that injects processEvents via callbacks -- reusable for any future modal-progress-over-blocking-cmd-op UX"
  - "Per-file progress over a blocking cmd.* call: update label + value + processEvents BETWEEN iterations; never attempt per-byte progress (impossible when the call blocks the event loop)"
  - "Offline fallback = per-character lock, not whole-game lock: map failures -> character set -> lock only affected characters; bundled-structure characters stay playable"

# Metrics
duration: 10 min
completed: 2026-08-30
---

# Phase 6 Plan 10: Bulk-Download Prompt (CAST-04) Summary

**Qt-free BulkDownloadRunner (MockCmd-testable) + BulkDownloadDialog (per-file progress + processEvents + cancel-between-fetches + retry + per-character offline lock) + cast.json source/pdb_id schema extension**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-08-29T16:38:21Z
- **Completed:** 2026-08-29T16:48:34Z
- **Tasks:** 3
- **Files modified:** 4 (1 modified, 3 created)

## Accomplishments
- Extended `c14/data/cast.json` schema with `source` (bundled|download) + `pdb_id` + `character` fields per enzyme; kept the real per-enzyme large-PDB list MINIMAL/PLACEHOLDER for Phase 6 (PLACEHOLDER_large_enzyme with pdb_id PLACEHOLDER_PDB, character glucose, claim_id PLACEHOLDER_PHASE7) -- no fabricated PDB IDs (05.4 no-fabricated-science); Phase 7 fills the real list.
- Built `c14/ui/bulk_download.py` -- a Qt-free runner (importable in pure WSL python3.6 with NO pymol.Qt; cmd injected like AssetManager) with `missing_large_pdbs` (PLACEHOLDER guard + Pitfall 3 lowercase filename check + idempotent-cache respected), `run_bulk_download` (per-file fetch_pdb loop with on_progress/on_cancel_check callbacks; RuntimeError on count_atoms<=0 = failure signal; loop CONTINUES past a failure), `characters_to_lock` (Pattern 2 per-character lock mapping with cast.json fallback), `expected_download_characters` (lock UI universe). Delegates to AssetManager.fetch_pdb (Pitfall 5 mitigations baked in); NEVER calls cmd.fetch directly.
- Built `c14/ui/bulk_download_dialog.py` (gate-EXEMPT; `from pymol.Qt import QtCore, QtWidgets`) -- `BulkDownloadDialog(QProgressDialog)` wrapping the Qt-free runner with per-file progress + `QApplication.processEvents()` BETWEEN fetches (NOT per-byte -- cmd.fetch blocks, Pitfall 1) + cancel-between-fetches (Pitfall 7; button label "Cancel (after current file)") + retry. Plus `maybe_run_bulk_download(controller, cmd, parent)` -- the one-time-prompt entry point for MainWindow._new_game (06-08): no-missing -> no prompt (game starts instantly); on failed -> characters_to_lock + lock ONLY affected characters (glucose stays playable); on canceled -> QMessageBox Retry? -> re-run with recomputed still-missing list (free idempotent cache), or lock still-missing characters (SC4).
- Added `tests/test_bulk_download.py` -- 11 pure-WSL MockCmd unit tests (no pymol/Qt import) covering: PLACEHOLDER skip (Phase 6 -> []), missing/existing detection (Pitfall 3 lowercase via temp downloaded dir + monkeypatched c14.paths.data_path), success, failure-recorded + loop-continues (middle obj fails, others succeed), cancel-between-files (on_cancel_check breaks the loop, not mid-fetch), on_progress (i, total, pdb_id) per file, characters_to_lock mapping + dedup + empty-when-no-failure (SC4), Qt-free import (runtime gate twin).

## Task Commits

Each task was committed atomically (path-scoped; only the files that task modified were staged):

1. **Task 1: Extend cast.json schema + Qt-free BulkDownloadRunner** -- `a173af1` (feat)
2. **Task 2: MockCmd unit tests for the runner** -- `2616673` (test)
3. **Task 3: BulkDownloadDialog (QProgressDialog wrapper with processEvents)** -- `94f774d` (feat)

**Plan metadata:** (this SUMMARY + STATE.md update -- committed separately after)

## Files Created/Modified
- `c14/data/cast.json` -- MODIFIED: added `source` (bundled|download) + `pdb_id` + `character` fields per enzyme; fixture_enzyme_1 marked source=bundled; PLACEHOLDER_large_enzyme (source=download, pdb_id=PLACEHOLDER_PDB, character=glucose) added as Phase 7 placeholder.
- `c14/ui/bulk_download.py` -- CREATED: Qt-free runner (missing_large_pdbs, run_bulk_download, characters_to_lock, expected_download_characters). Imports only os/json/c14.paths/c14.pymol_layer.asset_manager.AssetManager at module top (NO pymol.Qt); cmd injected as a function param. WSL-unit-testable with MockCmd.
- `c14/ui/bulk_download_dialog.py` -- CREATED: BulkDownloadDialog(QProgressDialog) + maybe_run_bulk_download + _apply_lock. Gate-EXEMPT (imports pymol.Qt); py_compile-only in WSL (importing fails with ModuleNotFoundError: No module named 'pymol' -- EXPECTED).
- `tests/test_bulk_download.py` -- CREATED: 11 MockCmd unit tests (pure WSL python3.6, no pymol/Qt import).

## Decisions Made
- **object_name = enzyme_id** for the missing-code 4-tuple (the PyMOL object name the story graph's `load` MolAction references). Keeps the bulk-download object name consistent with the on_enter scene-rebuild naming. Phase 7 may revisit if a different convention emerges; documented in `bulk_download.py:missing_large_pdbs`.
- **Qt-free runner in c14/ui/ (gate-EXEMPT dir) but importing NO pymol.Qt** -- the runner stays WSL-testable by injecting cmd as a function param (AssetManager pattern); the QDialog wrapper (bulk_download_dialog.py) imports pymol.Qt and is py_compile-only in WSL. This split keeps the heavy loop logic unit-testable while the thin Qt wrapper handles processEvents.
- **maybe_run_bulk_download returns a dict** `{ran, failed, canceled, locked_characters}` + duck-typed `_apply_lock(controller, ...)` (hasattr check for `lock_characters`) -- decoupled from the 06-08 controller's exact API. If 06-08 names the lock method differently, update `_apply_lock` (single point of contact).
- **On cancel-no-retry: lock still-missing characters** (re-run missing_large_pdbs to find what's not on disk) -- SC4-correct (locks only affected characters; glucose stays playable if its bundled structures are intact), not a whole-game lock.
- **Phase 6 cast.json real-PDB list stays PLACEHOLDER** -- only PLACEHOLDER_large_enzyme with pdb_id "PLACEHOLDER_PDB" (the PLACEHOLDER guard in missing_large_pdbs skips it, so the prompt does NOT fire for placeholder content). Phase 7 fills the real per-enzyme large PDBs (human-approved per 05.4 no-fabricated-science). NO fabricated PDB IDs introduced here.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added `self.show()` at the start of `BulkDownloadDialog.run()`**
- **Found during:** Task 3 (BulkDownloadDialog)
- **Issue:** The plan's `run()` example updated the label + value + processEvents but did not explicitly show the dialog. QProgressDialog's default auto-show has a multi-second delay (`minimumDuration`), which would hide the progress bar during a fast fetch loop -- the user would see a blank/main-window-blocked state until the delay elapsed.
- **Fix:** Added `self.show()` + `QApplication.processEvents()` at the start of `run()` so the dialog is visible immediately before the first (blocking) fetch.
- **Files modified:** c14/ui/bulk_download_dialog.py
- **Verification:** py_compile clean (syntax); the functional visibility is human-verify in 06-14.
- **Committed in:** 94f774d (Task 3 commit)

**2. [Rule 2 - Missing Critical] Added cancel-no-retry lock of still-missing characters**
- **Found during:** Task 3 (maybe_run_bulk_download)
- **Issue:** The plan specified "on canceled: ask Retry? -> re-run if yes" but did not specify what happens on declined-retry. Without a lock, the player could start a character whose structures never downloaded -> a broken scene later.
- **Fix:** On declined-retry, re-run `missing_large_pdbs(cmd)` to find the still-missing codes and lock their characters via `characters_to_lock` (reason "canceled"). This is the SC4-correct behavior (locks only affected characters; glucose stays playable if its bundled structures are intact).
- **Files modified:** c14/ui/bulk_download_dialog.py
- **Verification:** py_compile clean; the functional lock is human-verify in 06-14.
- **Committed in:** 94f774d (Task 3 commit)

**3. [Minor test addition] Added `test_characters_to_lock_dedupes_characters` (11 tests vs the plan's 10)**
- **Found during:** Task 2 (tests)
- **Issue:** The plan listed 10 tests; I added an 11th to verify `characters_to_lock` deduplicates character ids when multiple failures map to the same character (two glucose failures + one fatty_acid -> {"glucose", "fatty_acid"}).
- **Fix:** Added the dedup test for robustness (within the "characters_to_lock mapping" scope the plan already covered).
- **Files modified:** tests/test_bulk_download.py
- **Verification:** All 11 tests green; full suite green (284 tests).
- **Committed in:** 2616673 (Task 2 commit)

---

**Total deviations:** 3 (2 Rule 2 missing-critical auto-additions for correct UX/SC4, 1 minor test addition)
**Impact on plan:** All auto-additions are within the plan's stated success criteria (per-file progress, cancel-between, retry, per-character offline lock) and necessary for correct operation. No scope creep.

## Issues Encountered
- **Initial test assertion mismatch (fixed inline before commit):** `test_run_bulk_download_failure_recorded` first asserted `"obj1" in err`, but `AssetManager.fetch_pdb` formats the RuntimeError message with the pdb_id (`code`), not the object_name (`asset_manager.py:125`: `"fetch_pdb: {0} produced no atoms".format(code)`). Fixed the assertion to `"pdb1" in err` before the Task 2 commit; all 11 tests then green. No commit carried the wrong assertion (caught during the test-verify step before staging).

## User Setup Required
None -- no external service configuration required. The bulk-download uses PyMOL's own `cmd.fetch` (PDB/RCSB); no API keys or dashboard configuration. The offline fallback (per-character lock) is in-memory per session.

## Next Phase Readiness
- **Ready for 06-08 (MainWindow/controller):** `maybe_run_bulk_download(controller, cmd, parent)` is the one-time-prompt entry point for `_new_game`; the controller should call it BEFORE starting the game and read the returned `locked_characters` set (or expose a `lock_characters` method that `_apply_lock` will call duck-typed). The dialog + runner are complete and unit-tested.
- **Ready for 06-14 (human-verify):** the functional bulk-download (per-file progress bar advances, cancel button responds between fetches, retry re-runs, offline lock applies only to affected characters) is human-verify in 06-14 -- not automatable from WSL (Qt needs a real display).
- **Ready for Phase 7 (content/glucose):** `cast.json` schema is extended (source/pdb_id/character); Phase 7 fills the real per-enzyme large-PDB list (replacing the PLACEHOLDER_large_enzyme entry with real, human-approved PDB IDs). The PLACEHOLDER guard in `missing_large_pdbs` will then let the real entries through (prompt fires).
- **Blockers/concerns:** none. The `object_name = enzyme_id` convention is a Phase 7 decision point -- if Phase 7's story-graph `load` MolActions use a different object-naming convention, update `missing_large_pdbs`'s object_name derivation (single line) + the `run_bulk_download` consumer.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-30*
