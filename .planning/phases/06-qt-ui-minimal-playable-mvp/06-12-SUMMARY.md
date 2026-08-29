---
phase: 06-qt-ui-minimal-playable-mvp
plan: 12
subsystem: ui
tags: [pymol.Qt, QDialog, achievements, pyqt5, collection-board]

# Dependency graph
requires:
  - phase: 06-04
    provides: AchievementBoard domain module + ACHIEVEMENT_CATALOG_V1 + persisted achievements.json (characters_tried / endings_found / branches_discovered / achievements_unlocked)
provides:
  - AchievementsDialog -- read-only Qt QDialog rendering the collection-based achievement board from AchievementBoard.data
affects: [06-14 (human-verify SC5 achievement board), MainWindow "Achievements" button wiring, Phase 8 catalog expansion (fatty_acid_tried / alcohol_tried auto-render once added to ACHIEVEMENT_CATALOG_V1)]

# Tech tracking
tech-stack:
  added: []   # no new deps -- pymol.Qt (PyQt5) already approved + shipped with PyMOL 2.5.0
  patterns:
    - "Read-only Qt dialog reads a domain module's .data dict directly (no copy, no file I/O of its own; the domain module owns persistence)"
    - "QScrollArea overflow wrapper + Close button (matches HelpDialog / 06-13 sibling convention)"
    - "Catalog cross-reference for locked-vs-unlocked display (iterate the fixed catalog; look up unlocked entries by id for their date)"

key-files:
  created:
    - c14/ui/achievements_dialog.py
  modified: []

key-decisions:
  - "Read-only dialog: NO unlock buttons (unlocks are gameplay-driven via the controller's on_turn; the board auto-detects + auto-persists via 06-04). The dialog never writes to the board."
  - "Cross-reference ACHIEVEMENT_CATALOG_V1 to show locked entries greyed (within the plan's explicitly-allowed optional scope; makes ACH-01's 'fills in a fixed catalog' framing visible -- NOT a leaderboard)."
  - "Catalog display order (not unlock-chronological) for stable rendering as the board grows across phases."
  - "Snapshot board.data at __init__ (dialog-open time); the board is kept current by the controller's on_turn calls during gameplay, not while the dialog is open."
  - "Hide the description on locked entries (greyed 'Name — Locked') -- no spoilers, gives the player a reason to seek the unlock."
  - "Importing ACHIEVEMENT_CATALOG_V1 from c14.achievements is safe: that module is pure-Python (stdlib only, gate-clean) and c14/ui/ is gate-EXEMPT, so the AST gate stays clean."

patterns-established:
  - "Read-only renderer dialog: UI reads domain.data; domain owns mutation + persistence (decoupling honored -- the controller calls board.on_turn, the dialog only reads)."

# Metrics
duration: 2 min
completed: 2026-08-30
---

# Phase 6 Plan 12: AchievementsDialog Summary

**Read-only Qt QDialog rendering the collection-based AchievementBoard (unlocked catalog with greyed locked placeholders + endings found + characters tried + branches count) straight from `board.data`**

## Performance

- **Duration:** 2 min
- **Started:** 2026-08-29T17:33:05Z
- **Completed:** 2026-08-29T17:34:40Z
- **Tasks:** 1
- **Files modified:** 1 (created)

## Accomplishments
- Built `c14/ui/achievements_dialog.py` -- `AchievementsDialog(QtWidgets.QDialog)`, the SC5 achievement-board UI (ACH-01/ACH-02).
- Renders the collection-based board from `AchievementBoard.data` (06-04): a summary line (Characters tried /3 | Endings found | Branches discovered -- counts, NOT scores), an "Unlocked" section (the fixed v1 catalog filled in), an "Endings found" section (Tier: node_id (character, date)), and a "Characters tried" line.
- Cross-references `ACHIEVEMENT_CATALOG_V1` so the player sees the FULL fixed catalog: unlocked entries show name + description + date; locked entries are greyed "Locked" placeholders (description hidden -- no spoilers). Makes ACH-01's "collection to fill in" framing visible (explicitly NOT a leaderboard).
- Read-only + cross-session: no unlock buttons (unlocks are gameplay-driven; the board auto-persists via 06-04); reads the board's persisted data (the board is constructed at MainWindow init with `user_data_path("achievements.json")` + `_load()`, so prior-session unlocks show automatically -- ACH-02). The dialog does NO file I/O of its own.
- Gate-EXEMPT (`c14/ui/` in `tools/check_imports.py` SKIP_DIRS); `py_compile` clean; AST gate clean. Importing in WSL fails (no Qt) -- EXPECTED; functional human-verify is 06-14 (SC5).

## Task Commits

Each task was committed atomically:

1. **Task 1: Create AchievementsDialog (collection-based board renderer)** -- `1b3a4d2` (feat)

**Plan metadata:** (committed separately after this SUMMARY)

## Files Created/Modified
- `c14/ui/achievements_dialog.py` -- `AchievementsDialog(QtWidgets.QDialog)`: read-only renderer for the collection-based achievement board. Reads `AchievementBoard.data` (characters_tried / endings_found / branches_discovered / achievements_unlocked) + cross-references `ACHIEVEMENT_CATALOG_V1` for the locked-vs-unlocked catalog view. QScrollArea wrapper + Close button; no unlock buttons.

## Decisions Made
- **Read-only, no unlock buttons** -- unlocks happen via gameplay (the controller calls `board.on_turn`); the board auto-detects + auto-persists (06-04). The dialog never mutates the board. This honors the plan's AVOID list + ACH-01 (collection, not a progression mechanic).
- **Cross-reference the catalog for locked placeholders** -- the plan marked this "optional for Phase 6; at minimum show the unlocked list." Implemented the optional enhancement because it makes ACH-01's "fills in a fixed catalog" framing visible (the player sees what's still to find) and is forward-compatible (Phase 8 catalog additions auto-render). Locked descriptions are hidden (no spoilers).
- **Catalog display order, not unlock-chronological** -- stable rendering as the board grows; the unlocked date still comes from the `achievements_unlocked` entry.
- **Snapshot `board.data` at `__init__`** -- the board is kept current by the controller's `on_turn` calls during gameplay, not while the dialog is open, so reading at construction time shows the current state at dialog-open.
- **Import `ACHIEVEMENT_CATALOG_V1` from `c14.achievements`** -- that module is pure-Python (stdlib only, gate-clean); `c14/ui/` is gate-EXEMPT, so the AST gate stays clean. DRY (single source of truth for the catalog).

## Deviations from Plan

None -- plan executed exactly as written. The catalog cross-reference (locked placeholders) was an explicitly-allowed optional enhancement called out in the plan's `<action>` ("cross-reference ACHIEVEMENT_CATALOG_V1 to show locked vs unlocked -- optional for Phase 6"), not a deviation. The `.get(..., [])` defensive reads + `_date_only` helper + `setMinimumHeight(360)`/`resize(540, 480)` are minor robustness/UX refinements within the spirit of the plan (matching the `HelpDialog` sibling convention).

## Issues Encountered
None.

## User Setup Required

None -- no external service configuration required. The dialog reads the in-memory `AchievementBoard` (which persists to `user_data_path("achievements.json")` via 06-04); no new env vars, accounts, or dashboard config.

## Next Phase Readiness
- `AchievementsDialog` is ready for the MainWindow "Achievements" button wiring (constructs from the controller's `AchievementBoard` instance; `accept()` on Close).
- Functional verification (unlocks show after playthroughs, persists across PyMOL restarts, greyed locked entries fill in as the player progresses) is **human-verify in 06-14 (SC5)** -- cannot be automated from WSL (Qt needs a real display).
- Phase 8 catalog expansion (`fatty_acid_tried` / `alcohol_tried` added to `ACHIEVEMENT_CATALOG_V1`) auto-renders in this dialog with NO code change here (the dialog iterates the catalog at runtime).
- No blockers or concerns carried forward.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-30*
