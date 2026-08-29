---
phase: 06-qt-ui-minimal-playable-mvp
plan: 03
subsystem: persistence
tags: [view-matrix, save-load, dependency-injection, testability-boundary, backward-compat, unittest]

# Dependency graph
requires:
  - phase: 02-story-engine-core
    provides: GameState (to_dict/from_dict .get-default shape) + GameEngine save/load (RngEngine sync + on_enter replay -- Pattern 6) + the molaction_sink injection pattern
  - phase: 04-editing-protonation-restore
    provides: the inject-callback testability pattern (molaction_sink / edit_router) this plan mirrors for view capture/restore
provides:
  - GameState.view field (list of 18 floats or None) serialized in to_dict + deserialized in from_dict with default None (backward-compatible with old Phase-2 saves)
  - GameEngine.view_provider / view_applier constructor injection (default None = no-op) -- save captures the view via the provider (failure-tolerant), load applies it via the applier AFTER the on_enter replay (saved view wins over a zoom MolAction)
  - 11 unit tests proving view round-trip + old-save backward-compat + save-captures-via-mock-provider + load-applies-AFTER-replay (with ordering proof) + failure-tolerance + no-op-when-None guards
affects: [06-06 (controller injects lambda: list(cmd.get_view()) / lambda v: cmd.set_view(v)), 06-14 (headless integration smoke for the real cmd.get_view/set_view contract), SC#3 (load restores the exact session incl. view)]

# Tech tracking
tech-stack:
  added: []  # no new libraries -- stdlib only (Python 3.6 compatible)
  patterns:
    - "Dependency-injection for view capture/restore (mirrors molaction_sink) -- keeps engine.py AST-gate-clean + WSL-testable with mock lambdas"
    - "Failure-tolerant try/except around injected callbacks -- a callback error degrades to no-op, never blocks the core save/load (06-RESEARCH Pattern 4)"
    - ".get-default forward-compat for schema additions -- old saves load cleanly without a version bump"

key-files:
  created: []  # no new files
  modified:
    - c14/state.py  # view field: __init__ kwarg + to_dict key + from_dict .get default
    - c14/engine.py  # view_provider/view_applier __init__ params + save capture + load restore-after-replay
    - tests/test_state.py  # TestGameStateView (4 tests)
    - tests/test_engine.py  # TestEngineViewCallbacks (7 tests)

key-decisions:
  - "view stored as a plain JSON list of 18 floats (NOT numpy / 4x4) -- cmd.set_view accepts a sequence; 06-RESEARCH-persistence-achievements.md Anti-Pattern"
  - "view added at the END of to_dict (after ending_tier) for diff-stability of older saves"
  - "from_dict uses .get default None -- NO version bump; 06-RESEARCH Open Question '.get-with-default is enough' (forward-compat)"
  - "view_provider/view_applier default None = no-op (Phase 2 tests construct GameEngine without them + stay green; backward-compatible)"
  - "load applies the view AFTER _enter replay (the saved view wins over a node's zoom MolAction -- 06-RESEARCH Pattern 4 + Open Question 5)"
  - "try/except around BOTH injected callbacks -- failure-tolerant; a view capture/restore error never blocks save/load"

patterns-established:
  - "View capture/restore via injected callbacks (mirrors molaction_sink): the engine NEVER imports pymol; the controller (06-06) injects lambda: list(cmd.get_view()) / lambda v: cmd.set_view(v)"
  - "Saved-view-wins ordering: load applies set_view AFTER the on_enter replay so a queued zoom MolAction does not override the saved camera"
  - "Forward-compatible schema additions via .get defaults (no version bump) for additive, optional fields like the camera view"

# Metrics
duration: 12 min
completed: 2026-08-29
---

# Phase 6 Plan 03: View-Matrix Injection Summary

**GameState.view field (18-float camera, default None, backward-compatible) + GameEngine view_provider/view_applier injection (save captures, load restores AFTER replay, failure-tolerant, no-op if None) closing the Phase 2 view-matrix gap for SC#3 -- 11 unit tests green, engine.py + state.py stay AST-gate-clean**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-08-29T16:03:58Z
- **Completed:** 2026-08-29T16:15:33Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- GameState.view field (default None; round-trips through to_dict/from_dict; old Phase-2 saves without a `view` key load cleanly with view=None) closes the Phase 2 view-matrix gap for SC#3 ("load restores the exact session ... + view").
- GameEngine view_provider/view_applier injection (default None = no-op): `save` captures the view via the injected provider (failure-tolerant try/except -> None, never blocks the save); `load` applies the saved view via the injected applier AFTER the on_enter replay so a node's `zoom` MolAction does not override the saved camera (the saved view wins). Mirrors the molaction_sink injection -- engine.py stays stdlib-only (AST gate clean) + WSL-testable with mock lambdas.
- 11 unit tests green: view field round-trip + old-save backward-compat (4 in TestGameStateView) + save captures via mock provider + save no-capture when None + save failure-tolerant + load applies AFTER replay (with a single-shared-log ordering proof that the set_view is the LAST entry, after all replayed molactions) + load no-apply when applier None + load no-apply when view None + load failure-tolerant (7 in TestEngineViewCallbacks). Full suite green (253 tests) -- no Phase 2 regression.

## Task Commits

Each task's work was committed (see Deviations for the concurrent-session attribution note on Tasks 2-3):

1. **Task 1: Add view=None field to GameState (3 sites) -- backward-compatible** -- `7f32e5e` (feat(06-03)) -- my clean atomic commit
2. **Task 2: Add view_provider/view_applier injection to GameEngine** -- `cdafb3b` (engine.py changes present in this commit) -- swept by a concurrent session's `fix(06-05)` commit (see Deviations)
3. **Task 3: Add unit tests for the view field + the injection** -- `524362a` (test_state.py + test_engine.py changes present in this commit) -- swept by a concurrent session's `feat(06-01)` commit (see Deviations)

**Plan metadata:** (committed separately below)

_Note: Tasks 2 and 3 could not be committed as standalone `feat(06-03)` commits because a concurrent git session (executing 06-01/06-02/06-05 in the same repo) committed with an `add`-all style that swept my already-staged changes into their commits before my `git commit` ran (index.lock contention + staging superseded). The CODE is correct, present at HEAD, and fully verified (all tests green). History rewrite was declined as unsafe with an active concurrent session. See Deviations._

## Files Created/Modified
- `c14/state.py` -- added `view=None` kwarg to `GameState.__init__` (placed after `ending_tier`, before `version`), `self.view = view` assignment, `"view": self.view` in `to_dict` (last key, after `ending_tier`, for diff-stability), `view=d.get("view")` in `from_dict` (default None via `.get`); updated the Attributes docstring + the to_dict key-order comment.
- `c14/engine.py` -- added `view_provider=None, view_applier=None` kwargs to `GameEngine.__init__` (after `edit_router`), stored as `self._view_provider`/`self._view_applier`; `save` captures the view via `list(self._view_provider())` (failure-tolerant try/except -> None) before `SaveStore.save`; `load` applies the saved view via `self._view_applier(self.state.view)` AFTER `self._enter(...)` (failure-tolerant try/except -> pass), guarded by `view_applier is not None and state.view is not None`; updated the class docstring.
- `tests/test_state.py` -- added `TestGameStateView` (4 tests: view defaults None, view round-trips, old-save-without-view loads None, new_game view None); updated `test_to_dict_keys` expected set to include `"view"` (Rule 1 auto-fix).
- `tests/test_engine.py` -- added `TestEngineViewCallbacks` (7 tests: save captures when provider injected, save no-capture when None, save failure-tolerant, load applies AFTER replay with ordering proof, load no-apply when applier None, load no-apply when view None, load failure-tolerant); uses the real `data/story` graph + bound `sink.append` as the mock molaction_sink + lambdas as the mock provider/applier (NO pymol import).

## Decisions Made
- **view stored as a plain JSON list of 18 floats** (NOT numpy / 4x4): `cmd.set_view` accepts a sequence; storing as a plain list keeps state.py pure-stdlib + JSON-serializable + diff-friendly (06-RESEARCH-persistence-achievements.md Anti-Pattern).
- **view added at the END of `to_dict`** (after `ending_tier`): keeps the existing key order stable so older saves diff cleanly against the new shape; the new key is purely additive.
- **`from_dict` uses `.get` default None -- NO version bump**: the 06-RESEARCH Open Question (".get-with-default is enough") is honored; old Phase-2 saves without a `view` key load with view=None and no crash (forward-compatible).
- **view_provider/view_applier default None = no-op**: Phase 2 tests construct `GameEngine` without the callbacks and stay green; the engine remains WSL-testable with mock lambdas (mirrors the molaction_sink / edit_router injection precedents).
- **load applies the view AFTER `_enter` replay**: the on_enter replay may include a `zoom` MolAction; the saved view is applied after so the saved camera wins (06-RESEARCH Pattern 4 + Open Question 5). This is the desired "saved view wins" behavior.
- **try/except around BOTH injected callbacks**: a view-capture failure leaves `state.view = None` (the save proceeds); a view-apply failure is swallowed (the load still returns the TurnResult). Neither ever blocks the core save/load (06-RESEARCH Pattern 4).
- **Did NOT change `new_game` / `start` / `choose` / `apply_player_edit` / `_enter`**: a new game starts with view=None (the default); the view is captured only on save + restored only on load.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated `test_to_dict_keys` expected set to include `"view"`**
- **Found during:** Task 1 (add view field to GameState)
- **Issue:** The existing `tests/test_state.py::test_to_dict_keys` asserts the exact `to_dict()` key set. Task 1 legitimately adds a `"view"` key to `to_dict`, so the assertion failed (`'view' in first set but not second`) -- a regression in an existing test caused by the schema change mandated by the plan.
- **Fix:** Added `"view"` to the `expected_keys` set in `test_to_dict_keys` (one-line addition). This is a direct consequence of Task 1's schema change, so it was included in the Task 1 commit.
- **Files modified:** tests/test_state.py
- **Verification:** `python3.6 -m unittest tests.test_state` -- 7 tests green (test_to_dict_keys passes with the updated set).
- **Committed in:** `7f32e5e` (Task 1 commit)

**2. [Rule 1 - Bug] Used bound `sink.append` instead of the plan's `molaction_sink=list.append`**
- **Found during:** Task 3 (add unit tests)
- **Issue:** The plan's inline test example #5 wrote `molaction_sink=list.append` (the unbound `list.append` method descriptor). Calling `list.append(action)` binds `action` as `self` (the list) with no item arg -> `TypeError: append() takes exactly one argument (0 given)`. This would crash the test.
- **Fix:** Used the established `molaction_sink=sink.append` pattern (a bound method on a list instance, `sink = []`) per the plan's explicit instruction "Follow the existing test_engine.py style ... list sink as the mock molaction_sink -- test_engine.py:64" (which takes precedence over the sloppy inline example). All 7 new engine tests use bound `sink.append`.
- **Files modified:** tests/test_engine.py
- **Verification:** All 7 TestEngineViewCallbacks tests pass.
- **Committed in:** `524362a` (Task 3 commit, via concurrent-session sweep)

### Environmental Issue (Concurrent Git Session)

**3. Concurrent git session swept Tasks 2 and 3 into other phases' commits**
- **Found during:** Tasks 2 and 3 commit attempts
- **Issue:** A concurrent session was executing plans 06-01 / 06-02 / 06-05 in the same repo in parallel with this 06-03 execution. When I staged my Task 2 (`c14/engine.py`) and Task 3 (`tests/test_state.py`, `tests/test_engine.py`) changes and ran `git commit`, the concurrent session's commits (using an `add`-all style) had already swept my staged changes into their commits (`cdafb3b fix(06-05)` for engine.py; `524362a feat(06-01)` for the tests) before my `git commit` ran. My commit attempts then found "nothing to commit" (the changes were already at HEAD), and one attempt hit an `index.lock` from the concurrent process.
- **Resolution:** Verified all 06-03 code is correct, present at HEAD, and fully verified (py_compile + AST gate + 11 new tests + full 253-test suite green). DECLINED to rewrite history (rebase/reset/reorder) because an active concurrent session makes that unsafe (risk of corrupting the shared ref or losing the other session's work). The commit attribution is muddled (Tasks 2-3 carry wrong commit messages), but the CODE is correct and the verification is complete.
- **Impact:** Cosmetic (commit-message attribution). No code or correctness impact. A future history-cleanup pass (when no concurrent sessions are active) could split `cdafb3b`/`524362a` into clean per-phase commits, but this is not required for correctness or verification.

---

**Total deviations:** 3 (2 auto-fixed bugs [Rule 1], 1 environmental [concurrent-session commit sweep])
**Impact on plan:** All auto-fixes necessary for correctness (the key-set test had to track the schema change; the unbound-method example would have crashed). The environmental issue muddles commit attribution but does not affect code or verification. No scope creep.

## Issues Encountered
- **Concurrent git operations in a shared repo**: index.lock contention + two task changes swept into other sessions' commits. Resolved by verifying the code is present + verified at HEAD and declining unsafe history rewrite (documented above). This is an environmental artifact of running multiple plan executors in the same repo concurrently, not a code issue.

## User Setup Required
None -- no external service configuration required. This plan is pure-Python domain tier (state + engine + tests), WSL-testable, stdlib-only.

## Next Phase Readiness
- **SC#3 view-matrix gap closed at the domain tier**: `GameState.view` + `GameEngine` view_provider/view_applier injection are in place and unit-tested with mock callbacks.
- **Ready for 06-06 (controller)**: the controller can now inject `lambda: list(cmd.get_view())` (view_provider) and `lambda v: cmd.set_view(v)` (view_applier) to complete SC#3 end-to-end ("load restores the exact session: story position + RNG state + loaded structures + view").
- **Ready for 06-14 (headless integration smoke)**: a headless smoke can verify the real `cmd.get_view()` / `cmd.set_view()` contract (the 18-float round-trip) against the engine's injection points.
- **No blockers at the domain tier.**
- **Note (cosmetic):** the concurrent-session commit attribution for Tasks 2-3 is muddled (documented in Deviations); a future history-cleanup pass when no concurrent sessions are active could tidy the per-phase commits, but this is not required for correctness or the success criteria.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-29*
