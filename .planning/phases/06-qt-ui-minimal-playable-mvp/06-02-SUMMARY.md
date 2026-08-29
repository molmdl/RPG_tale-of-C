---
phase: 06-qt-ui-minimal-playable-mvp
plan: 02
subsystem: infra
tags: [pathlib, cross-platform, user-data, persistence, pymol-convention, unittest, ast-gate, cwd-independence]

# Dependency graph
requires:
  - phase: 01-foundations-testability-citation-gate
    provides: c14/paths.py data_path + selfcheck (pure __file__-relative resolver), the AST import gate (tools/check_imports.py), and the CWD-independence test pattern (real os.chdir in setUp)
provides:
  - "c14.paths.user_data_path(*parts): user-writable path resolver outside the plugin install dir (~/.pymol/c14-tale-of-c/ Linux/Mac, %APPDATA%/pymol/c14-tale-of-c/ Windows)"
  - "8 unit tests proving Linux/Mac + Windows APPDATA + CWD-independence + pure-resolver (no existence check) + returns Path + multi-part join + no-parts base + gate-clean import"
affects: [06-04 achievement board, 06-10 bulk-download marker, 06-11 save/load dialogs, any Phase 6/7 subsystem persisting user data across restarts/reinstalls]

# Tech tracking
tech-stack:
  added: []  # no new deps -- os + pathlib stdlib only (Python 3.6 compatible)
  patterns:
    - "user-data-outside-plugin-install-dir: game data sits BESIDE ~/.pymol/startup/<plugin>/ (not inside) so a plugin reinstall (delete + re-unzip) does NOT wipe achievements/saves (ACH-02 / SC#5)"
    - "os.environ full-snapshot/restore in setUp/tearDown (dict copy -> clear+update) for platform-conditional tests (APPDATA set/unset) with zero cross-test leakage"
    - "runtime twin of the AST gate: test_gate_clean asserts 'pymol'/'PyQt5' NOT in sys.modules after importing c14.paths (static AST gate + runtime proof together)"

key-files:
  created: []
  modified:
    - "c14/paths.py -- added `import os` + `user_data_path(*relative_parts)` after selfcheck() (FROZEN-verbatim from 06-RESEARCH-persistence-achievements.md Pattern 5)"
    - "tests/test_paths.py -- added `TestUserDataPath` class (8 tests); updated import to include user_data_path"

key-decisions:
  - "user_data_path lives OUTSIDE the plugin install dir (~/.pymol/c14-tale-of-c/ beside ~/.pymol/startup/) so plugin reinstalls don't wipe achievements/saves (ACH-02 / SC#5)"
  - "Matches PyMOL's own user-dir convention (plugins/installation.py:22-29 get_default_user_plugin_path): ~/.pymol/ Linux/Mac, %APPDATA%/pymol/ Windows -- no cmd.get_user_path API exists (research-verified)"
  - "Pure resolver (no existence check) mirroring data_path's design -- callers makedirs as needed; decouples path arithmetic from filesystem state"
  - "Pure-Python (os + pathlib only, NO pymol import) keeps the AST gate clean + WSL-unit-testable; the Qt/controller layer just calls str(user_data_path(...))"
  - "FROZEN-verbatim implementation from 06-RESEARCH-persistence-achievements.md Pattern 5 (lines 389-414) -- no deviation from the researched design"

patterns-established:
  - "Platform-conditional test isolation via os.environ snapshot/restore (setUp dict-copies environ; tearDown clear+update restores) -- reusable for any APPDATA/HOME/USERPROFILE-dependent resolver"
  - "Runtime gate-twin test: importing a domain module and asserting banned modules absent from sys.modules (complements the static AST gate in check_imports.py)"
  - "Real os.chdir(tempfile.mkdtemp()) in setUp proves CWD-independence honestly (end-to-end), NOT mock.patch('os.getcwd') which only proves the call site"

# Metrics
duration: 4 min
completed: 2026-08-29
---

# Phase 6 Plan 02: user_data_path resolver Summary

**Pure-Python `user_data_path(*parts)` resolver (~/.pymol/c14-tale-of-c/ Linux/Mac, %APPDATA%/pymol/c14-tale-of-c/ Windows) that survives PyMOL restarts AND plugin reinstalls, with 8 WSL unit tests proving both platforms + CWD-independence + pure-resolver + AST-gate cleanliness**

## Performance

- **Duration:** ~4 min (started 2026-08-29T16:03:51Z, completed 2026-08-29T16:07:34Z)
- **Started:** 2026-08-29T16:03:51Z
- **Completed:** 2026-08-29T16:07:34Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added `user_data_path(*relative_parts)` to `c14/paths.py` (FROZEN-verbatim from research Pattern 5) -- the shared cross-cutting resolver for the achievement board (06-04), save/load dialogs (06-11), and bulk-download marker (06-10).
- Resolves to `~/.pymol/c14-tale-of-c/<parts>` (Linux/Mac, APPDATA unset) or `%APPDATA%/pymol/c14-tale-of-c/<parts>` (Windows, APPDATA set), matching PyMOL's own user-dir convention (`plugins/installation.py:22-29`).
- Lives OUTSIDE the plugin install dir (`~/.pymol/startup/<plugin>/`) so a plugin reinstall (delete + re-unzip) does NOT wipe user data (ACH-02 / SC#5).
- 8 new unit tests green: Linux/Mac path, Windows APPDATA path, CWD-independence (real `os.chdir`), no-existence-check (pure resolver), returns Path, multi-part join, no-parts base, gate-clean import.
- Pure-Python (os + pathlib only, NO pymol import) -- AST gate stays clean (`tools/check_imports.py` exit 0) and the module is WSL-unit-testable with no PyMOL installed.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add user_data_path(*parts) to c14/paths.py** -- `880190e` (feat)
2. **Task 2: Add unit tests for user_data_path in tests/test_paths.py** -- `f0c32f6` (test)

**Plan metadata:** (committed separately below as `docs(06-02): complete user-data-path-resolver plan`)

## Files Created/Modified
- `c14/paths.py` -- added `import os` at top + `user_data_path(*relative_parts)` function after `selfcheck()` (28 lines, FROZEN-verbatim from 06-RESEARCH-persistence-achievements.md Pattern 5). Existing `data_path`/`selfcheck` untouched (additive only).
- `tests/test_paths.py` -- added `TestUserDataPath` class (8 tests) with os.environ snapshot/restore setUp/tearDown; updated the import line to include `user_data_path`. Existing `TestPathResolution` (3 tests) untouched (additive only).

## Decisions Made
- **FROZEN-verbatim implementation** -- used the exact `user_data_path` body from `06-RESEARCH-persistence-achievements.md` Pattern 5 (lines 389-414) with no modification. The research had already verified the PyMOL convention against `tmp/pymol-src/modules/pymol/plugins/installation.py:22-29` and confirmed no `cmd.get_user_path` API exists; the plan mandated FROZEN-verbatim, so no redesign was warranted.
- **Additive only** -- `import os` added alongside `from pathlib import Path`; `user_data_path` appended after `selfcheck()`. The existing `data_path` and `selfcheck` were NOT modified (the plan's "additive only" AVOID constraint honored).
- **Test isolation via full environ snapshot** -- chose `os.environ.clear()` + `os.environ.update(self._saved_env)` in tearDown over a per-key save/restore because it robustly handles both set->unset (a test that sets APPDATA) and unset->set (a test that pops APPDATA) transitions with one pattern, guaranteeing zero cross-test or cross-session leakage.
- **Real `os.path.expanduser` (NOT mocked)** -- the plan's AVOID constraint. The Linux/Mac + no-parts tests assert the real resolution the production code will use; mocking expanduser would only prove the call site, not the behavior (mirrors the Phase 1 CWD-independence rationale).

## Deviations from Plan

None - plan executed exactly as written. The `user_data_path` body was taken FROZEN-verbatim from the research doc (Pattern 5), and the 8 tests cover all 8 cases the plan enumerated (Linux/Mac path, Windows APPDATA path, CWD-independence, no-existence-check, returns Path, multi-part join, no-parts base, gate-clean).

### Note on parallel execution

Phase 6 has `parallelization: true` in `.planning/config.json`. While executing 06-02, a parallel 06-03 executor committed `7f32e5e feat(06-03): add view=None field to GameState` (touching `c14/state.py` + `tests/test_state.py`) between this plan's Task 1 (`880190e`) and Task 2 (`f0c32f6`) commits. The files are disjoint (`paths.py`/`test_paths.py` vs `state.py`/`test_state.py`), so there was no conflict or cross-contamination -- each plan's `git add` was scoped to its own files. The full 215-test suite (which includes 06-03's state tests) remains green after both plans landed.

## Issues Encountered
None. All four `<verification>` checks passed on the first run:
- `python3.6 -m py_compile c14/paths.py tests/test_paths.py` -- exit 0.
- `python3.6 tools/check_imports.py` -- clean (paths.py imports only os + pathlib).
- `python3.6 -m unittest tests.test_paths -v` -- 11 tests pass (3 existing + 8 new).
- `python3.6 -m unittest discover -s tests` -- 215 tests pass, no regression.

## User Setup Required
None - no external service configuration required. This plan adds a pure-Python resolver + unit tests; no env vars, no network, no PyMOL session needed.

## Next Phase Readiness
- `user_data_path` is ready to be consumed by the achievement board (06-04: `user_data_path("achievements.json")`), the save/load dialogs (06-11: `user_data_path("saves", "<name>.json")`), and the bulk-download marker (06-10: `user_data_path(".bulk_download_state.json")`).
- The pure-resolver contract (no existence check) is documented in the docstring + proven by `test_no_existence_check`; callers must `os.makedirs(parent, exist_ok=True)` before writing (matches `SaveStore.save`'s existing `persist.py:47-49` makedirs + the research's `AchievementBoard._save` pattern).
- The CWD-independence invariant is proven (test_cwd_independence + the setUp chdir) so the resolver is safe to call from any PyMOL launch CWD.
- No blockers or concerns. The 8-test suite + the AST gate form the regression net for this resolver.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-29*
