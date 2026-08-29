---
phase: 06-qt-ui-minimal-playable-mvp
plan: 04
subsystem: achievements
tags: [json, persistence, achievements, pure-python, datetime, unittest, ast-gate, collection-based, idempotency, cross-session]

# Dependency graph
requires:
  - phase: 06-qt-ui-minimal-playable-mvp (06-02)
    provides: "c14.paths.user_data_path(*parts) -- user-writable path resolver OUTSIDE the plugin install dir (~/.pymol/c14-tale-of-c/ Linux/Mac, %APPDATA%/pymol/c14-tale-of-c/ Windows); pure-Python (os + pathlib), AST-gate clean, WSL-unit-testable"
provides:
  - "c14.achievements.AchievementBoard: collection-based achievement board (ACH-01) persisted to user_data_path('achievements.json') (ACH-02); on_turn(turn_result, character, is_new_game) detects endings (4 tiers) + records characters_tried + branches_discovered + unlocks tier achievements; idempotent (dedupes by id); auto-saves only when something changed"
  - "ACHIEVEMENT_CATALOG_V1 (6 v1 achievements: first_game, glucose_tried, true_ending, bad_ending, good_ending, normal_ending) + TIER_ACHIEVEMENT_ID (true/good/normal/bad -> tier achievement id)"
  - "15 WSL unit tests: each unlock type (4), no-first-game-mid-playthrough, branches recording, 3 idempotency forms, unknown-character no-op, persistence round-trip, backward-compat partial JSON, parent-dir creation, collection-based-not-leaderboard (ACH-01), ISO-UTC date"
affects: [06-06 controller (calls board.on_turn after each engine.start/choose/apply_player_edit), 06-12 achievements dialog (reads the JSON / AchievementBoard to render unlocks), Phase 8 fatty_acid_tried/alcohol_tried catalog extension]

# Tech tracking
tech-stack:
  added: []  # no new deps -- stdlib json/os/datetime + c14.paths only (Python 3.6 compatible)
  patterns:
    - "collection-based achievement board (NOT a ranked leaderboard -- ACH-01): schema has no score/rank/points keys; achievements_unlocked entries have only id/name/description/date (a fixed catalog the player 'fills in')"
    - "_unlock returns bool for change-tracking; on_turn saves ONLY when something changed (avoids redundant writes on no-op turns)"
    - "_unlock no-ops on unknown achievement ids (catalog lookup misses) -- safe for Phase 8 fatty_acid_tried/alcohol_tried expansion with no code change; the character is still recorded in characters_tried"
    - "forward-compatible .get merge on load: partial/older-schema JSON defaults missing keys to empty lists (no migration needed across phases)"
    - "decoupled controller-calls-board: the engine stays pure-domain (never calls the board -- 06-RESEARCH Open Question 6); the controller reads TurnResult.node.is_ending + node.id"

key-files:
  created:
    - "c14/achievements.py -- AchievementBoard + ACHIEVEMENT_CATALOG_V1 + TIER_ACHIEVEMENT_ID + on_turn unlock logic (pure-Python: json/os/datetime + c14.paths; AST-gate clean; FROZEN-verbatim from 06-RESEARCH Pattern 3 lines 204-280 + plan-endorsed _unlock-returns-bool refinement)"
    - "tests/test_achievements.py -- TestAchievementBoard (15 tests: each unlock type, idempotency x3, persistence, backward-compat, parent-dir, collection-based, ISO-UTC)"
  modified: []

key-decisions:
  - "_unlock returns bool to track all mutations (incl. unlocks) in one 'changed' flag; on_turn saves only when something changed (avoids redundant writes on no-op turns)"
  - "`self._unlock(...) or changed` ordering (NOT `changed or self._unlock(...)`) keeps the _unlock side effect live -- Python `or` short-circuits the RIGHT operand, so putting `changed` on the right ensures _unlock always executes even when changed is already True"
  - "_unlock no-ops on unknown achievement ids (catalog lookup misses) so Phase 8 fatty_acid_tried/alcohol_tried expansion needs no code change; the character is still recorded in characters_tried (the board records WHAT was tried regardless of catalog state)"
  - "Collection-based board (ACH-01): schema has NO score/rank/points; achievements_unlocked entries have only id/name/description/date (a fixed catalog the player 'fills in', NOT a ranked playthrough comparison)"
  - "Persists to user_data_path('achievements.json') OUTSIDE the plugin install dir (ACH-02): ~/.pymol/c14-tale-of-c/ Linux/Mac, %APPDATA%/pymol/c14-tale-of-c/ Windows -- survives PyMOL restarts AND plugin reinstalls (delete + re-unzip startup/ does NOT wipe this data)"
  - "Forward-compatible .get merge on load: `for k in self.data: self.data[k] = loaded.get(k, self.data[k])` -- present keys kept, missing keys default to empty lists (lets the schema grow across phases without a migration)"
  - "Decoupled: the controller (06-06) calls board.on_turn after each engine turn; the engine stays pure-domain (never calls the board -- 06-RESEARCH Open Question 6)"
  - "JSON persistence mirrors SaveStore (persist.py:38-65): indent=2 + trailing newline + parent-dir os.makedirs(parent, exist_ok=True)"

patterns-established:
  - "Collection-based achievement board persisted to a user-writable JSON (mirrors SaveStore's indent=2 + trailing newline + parent-dir makedirs)"
  - "_unlock-returns-bool change-tracking pattern: `self._unlock(...) or changed` ordering keeps side effects live (right operand of `or` short-circuits) -- reusable for any idempotent append-then-track pattern"
  - "Forward-compatible .get merge on load -- lets a persisted schema grow across phases without a migration"
  - "Duck-typed FakeNode/FakeTurn test mocks (board reads only .node.id + .node.is_ending) -- tests the contract, not the implementation; survives a TurnResult refactor"

# Metrics
duration: 5 min
completed: 2026-08-29
---

# Phase 6 Plan 04: Achievement Board Summary

**Pure-Python `AchievementBoard` persisted to `user_data_path('achievements.json')` -- collection-based (ACH-01, no scores/ranks), survives PyMOL restarts + plugin reinstalls (ACH-02), detects endings/characters/branches via `on_turn`, idempotent, with 15 WSL unit tests green (273 full suite, no regression)**

## Performance

- **Duration:** ~5 min (started 2026-08-29T16:38:22Z, completed 2026-08-29T16:43:38Z)
- **Started:** 2026-08-29T16:38:22Z
- **Completed:** 2026-08-29T16:43:38Z
- **Tasks:** 2
- **Files modified:** 2 (both created)

## Accomplishments

- **`c14/achievements.py`** -- a pure-Python domain module (json/os/datetime + `c14.paths`; NO pymol/PyQt5; AST-gate clean; WSL-testable). `AchievementBoard.on_turn(turn_result, character, is_new_game)` detects endings (`node.is_ending` tier -> tier achievement + `endings_found` deduped by `node_id`), records `characters_tried` (deduped) + `branches_discovered` (deduped by `node.id`), and unlocks `first_game` + `<character>_tried` on a new game. Idempotent. Auto-saves to `user_data_path("achievements.json")` (indent=2 + trailing newline + parent-dir `makedirs`, mirroring `SaveStore`) ONLY when something changed.
- **6 v1 catalog achievements** (`first_game` / `glucose_tried` / `true_ending` / `bad_ending` / `good_ending` / `normal_ending`) + `TIER_ACHIEVEMENT_ID` map. Only `glucose_tried` is defined for Phase 6 (glucose MVP); `_unlock` no-ops on unknown ids so Phase 8 `fatty_acid_tried` / `alcohol_tried` expansion needs no code change (the character is still recorded in `characters_tried` regardless).
- **15 unit tests** covering each unlock type (first_game, no-first-game-mid-playthrough, true/bad/good/normal endings, branches), 3 idempotency forms (same ending twice, same node twice, same character new game twice), unknown-character no-op, persistence round-trip, backward-compat partial JSON (`.get` merge), parent-dir creation, collection-based-not-leaderboard (ACH-01: no `score`/`rank`/`points` keys), and ISO-UTC date. Full suite green: **273 tests (258 prior + 15 new), no regression**; AST gate clean.

## Task Commits

Each task was committed atomically (path-scoped; only the task's files staged):

1. **Task 1: Create `c14/achievements.py`** -- `7eef2c9` (feat)
2. **Task 2: Add `tests/test_achievements.py`** -- `4c20b92` (test)

_Both tasks were `type="auto"` (no TDD attribute); the plan is Pattern A (fully autonomous, no checkpoints). No REFACTOR commit needed -- the implementation was clean on first pass._

## Files Created/Modified

- `c14/achievements.py` -- `AchievementBoard` class + `ACHIEVEMENT_CATALOG_V1` (6 v1 achievements) + `TIER_ACHIEVEMENT_ID` (4 tiers) + `on_turn` unlock logic; pure-Python, AST-gate clean; persists to `user_data_path("achievements.json")`.
- `tests/test_achievements.py` -- `TestAchievementBoard` (15 tests) with `FakeNode`/`FakeTurn` duck-typed mocks + temp-dir paths (never touches the real user data dir).

## Decisions Made

- **`_unlock` returns bool** for change-tracking; `on_turn` accumulates `changed = self._unlock(...) or changed` and saves ONLY when something changed (avoids redundant writes on no-op turns). The plan explicitly endorsed this ("have `_unlock` return bool, OR check len before/after") over the research example's `if changed or self.data["achievements_unlocked"]:` form (which would always save once any achievement exists).
- **`self._unlock(...) or changed` ordering** (NOT `changed or self._unlock(...)`): Python `or` short-circuits the right operand, so putting `changed` on the right ensures `_unlock`'s append side effect always executes even when `changed` is already `True`. This is a subtle but critical correctness point -- the naive `changed or self._unlock(...)` would SKIP the unlock when `changed` was already True.
- **`_unlock` no-ops on unknown ids** (catalog lookup misses): the controller can call `_unlock(character + "_tried")` for ANY character and it unlocks only when the catalog has the id. Phase 8 `fatty_acid_tried` / `alcohol_tried` expansion = just add the tuples to `ACHIEVEMENT_CATALOG_V1`; no `on_turn` / `_unlock` change. The character is still recorded in `characters_tried` (the board records WHAT was tried regardless of catalog state).
- **Collection-based, NOT leaderboard (ACH-01)**: the schema has no `score`/`rank`/`points` keys; `achievements_unlocked` entries have only `id`/`name`/`description`/`date`. The player "fills in" a fixed catalog; the board never ranks playthroughs.
- **Persists to `user_data_path('achievements.json')` OUTSIDE the plugin install dir (ACH-02)**: `~/.pymol/c14-tale-of-c/` (Linux/Mac) / `%APPDATA%/pymol/c14-tale-of-c/` (Windows) -- survives PyMOL restarts AND plugin reinstalls (delete + re-unzip `startup/` does NOT wipe this sibling dir).
- **Forward-compatible `.get` merge on load**: `for k in self.data: self.data[k] = loaded.get(k, self.data[k])` -- present keys kept, missing keys default to empty lists. Lets the schema grow across phases without a migration.
- **Decoupled from the engine**: the controller (06-06) calls `board.on_turn`; the engine stays pure-domain (never calls the board -- 06-RESEARCH Open Question 6).
- **JSON persistence mirrors `SaveStore`** (`persist.py:38-65`): `indent=2` + trailing newline + parent-dir `os.makedirs(parent, exist_ok=True)`.
- **FROZEN-verbatim design** from `06-RESEARCH-persistence-achievements.md` Pattern 3 (lines 204-280), with the plan-endorsed `_unlock`-returns-bool refinement for clean change-tracking.

## Deviations from Plan

None -- plan executed exactly as written. The `_unlock`-returns-bool refinement was explicitly endorsed by the plan ("have `_unlock` return bool, OR check len before/after"), so it is not a deviation.

## Issues Encountered

None.

## User Setup Required

None -- no external service configuration required (pure-Python domain module + unit tests; no network, no PyMOL, no Qt at test time).

## Next Phase Readiness

- **Ready for the controller (06-06):** `AchievementBoard.on_turn(turn_result, character, is_new_game)` is the contract -- call it after each `engine.start` / `choose` / `apply_player_edit`. The board reads `turn_result.node.id` + `turn_result.node.is_ending` (a `TurnResult`, `engine.py:54-55`) -- no engine change needed.
- **Ready for the achievements dialog (06-12):** read `AchievementBoard.data` (or re-`AchievementBoard(path=...)` to load the JSON) to render `characters_tried` / `endings_found` / `branches_discovered` / `achievements_unlocked`. The catalog (`ACHIEVEMENT_CATALOG_V1`) gives the full set so the dialog can show locked-vs-unlocked.
- **Ready for Phase 8 character expansion:** add `("fatty_acid_tried", "Fatty Acid", "...")` + `("alcohol_tried", "Alcohol", "...")` tuples to `ACHIEVEMENT_CATALOG_V1`; `_unlock` + `on_turn` need no change (the controller already calls `_unlock(character + "_tried")` for any character).
- **No blockers.** Full suite green (273 tests); AST gate clean; pure-Python (WSL-testable). The Qt dialog (06-12) + controller wiring (06-06) are the only remaining consumers.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-29*
