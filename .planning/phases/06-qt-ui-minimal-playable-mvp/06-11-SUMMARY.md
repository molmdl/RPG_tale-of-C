---
phase: 06-qt-ui-minimal-playable-mvp
plan: 11
subsystem: ui
tags: [qt, qfiledialog, save-load, persistence, pymol.Qt]

# Dependency graph
requires:
  - phase: 06-02
    provides: "user_data_path('saves') resolver (outside plugin install dir -- survives reinstalls)"
  - phase: 06-06
    provides: "Controller.save(path) / Controller.load(path) API the dialogs route to"
  - phase: 06-03
    provides: "engine view-matrix injection (view_provider/view_applier) referenced by the docstring as the real save/load mechanism"
provides:
  - "ask_save_path(parent, default_name='save.json') -> path|None (QFileDialog save wrapper)"
  - "ask_load_path(parent) -> path|None (QFileDialog load wrapper)"
  - "_saves_dir() helper -- idempotent makedirs of user_data_path('saves')"
affects:
  - 06-08 (MainWindow wires Save/Load buttons: ask_save_path -> controller.save; ask_load_path -> controller.load)
  - 06-14 (human-verify SC3 round-trip: save mid-game, load restores exact session)

# Tech tracking
tech-stack:
  added: []  # pymol.Qt already approved (Phase 6)
  patterns:
    - "Thin QFileDialog wrapper: dialog collects path, returns path|None; caller routes to controller.save/load (engine does the real work)"
    - "user_data_path('saves') as the default save dir (mirrors achievements.json -- both outside the plugin install dir)"

key-files:
  created:
    - c14/ui/save_load_dialogs.py
  modified: []

key-decisions:
  - "Dialogs are THIN wrappers -- collect path only; controller.save/load + engine do the real work (on_enter replay rebuilds the scene; 06-03 view injection restores the camera). No .pse saved (Anti-Pattern 5); no manual scene re-apply after load (double-dispatch -- Pitfall 3)."
  - "Default save dir = user_data_path('saves') with idempotent os.makedirs -- survives reinstalls (Pitfall 5) and the first save 'just works' without the user pre-creating the dir."
  - "Filter 'RPG Save (*.json)' -- human-readable JSON saves (Phase 2 SaveStore, Decision D2; persist.py); diff-friendly + editable for educators."
  - "return path or None -- the caller (06-08 MainWindow) guards `if path:` before invoking controller.save/load so a cancel is a no-op."

patterns-established:
  - "Thin-dialog pattern: a Qt dialog collects a value (path) and returns it or None; the caller (MainWindow) routes it to the controller. The dialog itself does NO domain work."

# Metrics
duration: 1 min
completed: 2026-08-30
---

# Phase 6 Plan 11: Save/Load Dialogs Summary

**Thin `QFileDialog` wrappers (`ask_save_path`/`ask_load_path`) defaulting to `user_data_path("saves")` (with makedirs) and routing to `controller.save`/`load`; engine does the real work via on_enter replay + 06-03 view injection (no `.pse`, no double-dispatch).**

## Performance

- **Duration:** 1 min
- **Started:** 2026-08-29T17:57:54Z
- **Completed:** 2026-08-29T17:59:35Z
- **Tasks:** 1
- **Files modified:** 1 created

## Accomplishments
- Built `c14/ui/save_load_dialogs.py` -- the SAVE-01/02 UI + SC3 save/load path collection (gate-EXEMPT; `from pymol.Qt import QtWidgets` + `from c14.paths import user_data_path`).
- `ask_save_path(parent, default_name="save.json")` opens a Save `QFileDialog` defaulting to `user_data_path("saves")/save.json` with filter `RPG Save (*.json)`; returns the chosen path or `None` (cancel).
- `ask_load_path(parent)` opens a Load `QFileDialog` defaulting to `user_data_path("saves")` with the same filter; returns the chosen path or `None`.
- `_saves_dir()` helper resolves `user_data_path("saves")` to a str and idempotently `os.makedirs(exist_ok=True)`-creates it on first use (the first save "just works"; safe on later calls).
- Anti-patterns avoided: NO `.pse` session saved (Anti-Pattern 5 -- the scene rebuilds on load via on_enter replay, a pure function of game state); NO manual scene re-apply after `engine.load` (double-dispatch bug -- the engine already replays on_enter); NO hardcoded save dir (uses `user_data_path` so saves survive reinstalls -- Pitfall 5); NO f-strings; does NOT block the GUI (fast JSON ops handled by controller/engine; the dialog is a native modal `QFileDialog`).
- The MainWindow (06-08) wiring contract documented inline: Save button -> `path = ask_save_path(self); if path: self._controller.save(path)`; Load button -> `path = ask_load_path(self); if path: self._controller.load(path)`. The controller's save/load (06-06) call engine.save/load (06-03: captures view via `view_provider`, restores via `view_applier` AFTER on_enter replay).
- `py_compile` clean (exit 0); AST gate (`tools/check_imports.py`) clean (exit 0); AST sanity confirms all 3 functions (`_saves_dir`, `ask_save_path`, `ask_load_path`) present.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create c14/ui/save_load_dialogs.py -- ask_save_path + ask_load_path** - `7f4e5cd` (feat)

**Plan metadata:** (pending -- committed after this SUMMARY + STATE update)

## Files Created/Modified
- `c14/ui/save_load_dialogs.py` -- Thin `QFileDialog` wrappers (`ask_save_path`/`ask_load_path`/`_saves_dir`) defaulting to `user_data_path("saves")` (makedirs) with `RPG Save (*.json)` filter; return path or None. Routes to `controller.save`/`load` (the engine does the real work via on_enter replay + 06-03 view injection; no `.pse`, no double-dispatch).

## Decisions Made
- Followed the plan exactly: implemented Pattern 4 verbatim from `06-RESEARCH-persistence-achievements.md` (lines 344-367), with the docstring expanded to match the documentation conventions of sibling dialogs (`c14/ui/help_dialog.py`, `c14/ui/achievements_dialog.py` -- gate-EXEMPT status, anti-pattern avoidance, Python 3.6 compatibility, controller-wiring contract).
- Kept the `# type:` comments from the plan's code (Py2/3.6-compatible type hints via comment form, matching the `c14/paths.py` + `c14/persist.py` + `c14/ui/controller.py` precedent).
- Did NOT add a default-name parameter to `ask_load_path` (the plan specifies none -- a Load dialog shows the dir listing, not a default filename).

## Deviations from Plan

None - plan executed exactly as written. The implementation matches the plan's code block verbatim (the `_saves_dir` helper + `ask_save_path` + `ask_load_path`); the only addition is an expanded module docstring documenting gate-EXEMPT status, the anti-patterns avoided, and the controller-wiring contract -- consistent with the docstring depth of the sibling `c14/ui/help_dialog.py` and `c14/ui/achievements_dialog.py` (within the "traceable, clean" AGENTS.md requirement; no behavioral change).

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. The save dir (`user_data_path("saves")`) is auto-created on first use at `~/.pymol/c14-tale-of-c/saves` (Linux/Mac) or `%APPDATA%/pymol/c14-tale-of-c/saves` (Windows) -- no user pre-creation needed.

## Next Phase Readiness
- `ask_save_path`/`ask_load_path` are ready for the MainWindow (06-08) to wire into its Save/Load buttons (`from .save_load_dialogs import ask_save_path, ask_load_path`).
- The functional save/load round-trip (save mid-game, load restores exact session: story position + RNG state + loaded structures + view) is human-verify in 06-14 (SC3). Importing this module in WSL FAILS (no Qt) -- EXPECTED; only `py_compile` is WSL-verifiable here.
- No blockers. The dialogs depend only on the already-complete 06-02 (`user_data_path`) + 06-06 (`controller.save`/`load`); both are committed.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-30*
