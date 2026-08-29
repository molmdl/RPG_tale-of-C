---
phase: 06-qt-ui-minimal-playable-mvp
plan: 08
subsystem: ui
tags: [pymol.Qt, PyQt5, QMainWindow, Qt-widgets, thin-adapter, signal-slot]

# Dependency graph
requires:
  - phase: 06-06
    provides: the Qt-free Controller (mediator) + HeroResolver -- MainWindow is a thin renderer over its TurnResult API (start_game/choose/take_choice/request_edit/build_edit_intent/save/load + is_mixed_weighted_node + _pending_edit_enzyme_id)
  - phase: 06-04
    provides: AchievementBoard (constructed at MainWindow init with default user_data_path for ACH-02 cross-session)
  - phase: 06-03
    provides: view-matrix injection (view_provider/view_applier wired to cmd.get_view/set_view)
  - phase: 06-01
    provides: the 4 deferred molops dispatches (set_color/label/set/align) + load target-prefix fallback the on_enter sequences use
  - phase: 03/04
    provides: MolOps + AssetManager + EditOps + ProtonationManager + EditRouter (the injected molops stack MainWindow constructs)
provides:
  - MainWindow (QMainWindow) -- the SC1 core UI surface (toolbar [New/Save/Load/Achievements/Help] + central StoryPanel/ChoicePanel + status bar)
  - StartDialog (modal; Glucose only in Phase 6; optional seed)
  - StoryPanel (text_dramatic + text_teaching stacked + ending banner)
  - ChoicePanel (pure-MC buttons / tca.shuffle mixed-node Spin+Edit+cycle-trap / ending "Start a new game")
  - render_turn (the controller→view seam; handles endings + the edit.prompt→EditDialog seam)
  - prompt_fn = QMessageBox.question wrapper (the OQ-6 warn+confirm gate wired)
affects: [06-14 (human-verify integration), 06-07 (plugin entry point launches MainWindow), Phase 7+ (content renders through this window)]

# Tech tracking
tech-stack:
  added: []  # pymol.Qt/PyQt5 already approved (PROJECT.md); no new deps
  patterns:
    - "Thin-adapter UI over a Qt-free controller (06-RESEARCH Pattern 1): widgets are dumb renderers; all domain work goes through the controller"
    - "Dumb-renderer widgets: NO cmd.* / cond-eval / RNG-pick / QMessageBox inside the panels (all delegated)"
    - "Deferred sibling-dialog imports inside handlers (lazy on click) so main_window.py py_compiles without 06-09/06-11 (parallel-execution safety)"
    - "Qt signal (ChoicePanel.new_game_requested) for panel->MainWindow decoupling (no parent back-reference)"
    - "lambda _=False, c=choice/i=index default-arg capture for Qt signal late-binding (matches help_dialog.py:85-87)"

key-files:
  created:
    - c14/ui/widgets.py
    - c14/ui/main_window.py
  modified: []

key-decisions:
  - "edit.prompt seam routed via engine.apply_player_edit(intent, intent.enzyme_id) + _record_achievement + _render directly (Rule 1 deviation -- the plan prescribed controller.apply_edit at edit.prompt but it raises RuntimeError there; 06-09's EditDialog.submit docstring confirms the same bug + says the real fix belongs in 06-06's controller, out of scope for both 06-08 + 06-09)"
  - "_resolve_story_dir falls back to repo-root data/story_glucose in dev (Rule 3 -- c14/data/story_glucose is absent until the 06-07 zip build bundles it; without the fallback the MainWindow crashes in a bare checkout)"
  - "Deferred sibling-dialog imports (edit_dialog/save_load_dialogs/achievements_dialog/help_dialog) inside their handlers -- py_compiles without them + matches the lazy entry-point pattern"
  - "StartDialog seed validation: a non-integer seed shows a warning + vetoes the accept (the player fixes the input); blank -> None (random/play mode)"
  - "ChoicePanel iterates ALL non-weighted choices (not just cond-eligible) at a mixed node so the cycle-trap shows greyed-out before its cond is met (the plan: 'grey out the cycle-trap until visits > 5')"

patterns-established:
  - "Pattern: dumb-renderer widgets delegate ALL domain work to the controller (ChoicePanel calls controller.choose/take_choice/request_edit; never cmd.* / _engine.choice_cond_met is the only engine reach -- sanctioned by the plan for cond-gating)"
  - "Pattern: render_turn is the controller->view seam; the MainWindow implements it + the controller calls it after each engine turn"
  - "Pattern: lambda _=False, c=choice default-arg capture avoids the Qt signal late-binding closure bug (the _ receives the clicked bool; the captured var is the default arg)"

# Metrics
duration: 13 min
completed: 2026-08-30
---

# Phase 6 Plan 08: Main Window + Widgets Summary

**QMainWindow + StartDialog + StoryPanel/ChoicePanel -- a thin Qt renderer over the 06-06 Controller, wiring the toolbar (New/Save/Load/Achievements/Help), the tca.shuffle mixed-node UI (Spin/Edit/cycle-trap), the OQ-6 QMessageBox prompt_fn, and the edit.prompt->EditDialog seam**

## Performance

- **Duration:** 13 min
- **Started:** 2026-08-29T18:19:12Z
- **Completed:** 2026-08-29T18:32:38Z
- **Tasks:** 2
- **Files modified:** 2 (both created)

## Accomplishments
- StoryPanel (text_dramatic 14pt + text_teaching 10pt gray, stacked not tabbed, teaching in a QScrollArea) + an ending banner ("Ending reached: <tier>"); handles empty/TBD dramatic text with a placeholder.
- ChoicePanel: 3 rendering modes -- ending ("Start a new game" button -> new_game_requested signal), mixed weighted+non-weighted (tca.shuffle: "Spin the wheel" -> choose(0) + edit:offer -> request_edit + cond-gated cycle-trap -> take_choice, greyed until visits > 5), pure-MC (one button per eligible choice -> choose(index)) / pure-weighted (single Spin + "(luck decides)" info label). Eligibility EXACTLY matches the engine's pick_choice filter (both call interpreter._cond).
- MainWindow (QMainWindow): constructs the molops stack (real cmd + AssetManager + EditOps + ProtonationManager + MolOps + EditRouter over c14/data/edits.json) + AchievementBoard (default user_data_path for ACH-02) + Controller (view=self); toolbar [New/Save/Load/Achievements/Help]; central StoryPanel+ChoicePanel; status bar (node/character/seed). prompt_fn = QMessageBox.question wrapper (OQ-6 gate); count_fn/view_provider/view_applier injected.
- StartDialog: modal; Glucose enabled (FA/Alcohol disabled "future phase" tooltip per 05.1 fa.stub/alc.stub); seed QLineEdit (blank=random/play; int=demo; invalid -> warn + veto).
- render_turn: ending -> render_ending + status; edit.prompt -> WARNING 4 seam (open EditDialog with stashed enzyme_id, on accept build_edit_intent + route); normal -> render_node + choices + status.
- All sibling dialogs imported DEFERRED inside handlers (py_compiles without 06-09/06-11; resolves at click time). Verified compatible with the now-committed 06-09 EditDialog + 06-11 save_load_dialogs APIs.

## Task Commits

Each task was committed atomically:

1. **Task 1: StoryPanel + ChoicePanel widgets** -- `5e0845a` (feat)
2. **Task 2: MainWindow + StartDialog + controller wiring** -- `f7b713b` (feat)

**Plan metadata:** (pending -- SUMMARY + STATE commits below)

## Files Created/Modified
- `c14/ui/widgets.py` -- StoryPanel (two-layer text + ending banner) + ChoicePanel (dumb renderer: pure-MC / tca.shuffle mixed-node / ending modes); gate-EXEMPT; py_compile clean.
- `c14/ui/main_window.py` -- MainWindow (QMainWindow: molops stack + Controller construction + toolbar + render_turn + edit.prompt seam) + StartDialog (Glucose-only character select + seed) + _resolve_story_dir (shipped + dev fallback); gate-EXEMPT; py_compile clean.

## Decisions Made
- **edit.prompt seam routing:** the plan prescribed `controller.apply_edit(intent)` at edit.prompt, but `apply_edit` raises RuntimeError there (edit.prompt has no `edit:enzyme:` tag -- the controller re-reads the enzyme_id from the current node; verified by `test_apply_edit_raises_when_no_enzyme_tag`). The 06-09 EditDialog.submit docstring confirms the same bug + says the real fix belongs in 06-06's controller (out of scope for 06-08 + 06-09 per file-ownership). Fixed in 06-08 by routing via `engine.apply_player_edit(intent, intent.enzyme_id)` + `_record_achievement` + `_render` directly (mirrors apply_edit's logic but uses the EditIntent's stashed enzyme_id). 06-06's controller + 06-09's dialog are UNMODIFIED. A future plan / 06-14 integration should make 06-06's `apply_edit` fall back to `edit_intent.enzyme_id` (or `_pending_edit_enzyme_id`) when `_current_enzyme_id()` is None so 06-09's `submit` helper works uniformly too.
- **story_dir dev fallback:** `_resolve_story_dir()` prefers `c14/data/story_glucose` (shipped, where 06-07 bundles it in the zip) + falls back to repo-root `data/story_glucose` (dev, where it lives in a bare checkout). Without the fallback the MainWindow crashes in dev (c14/data/story_glucose is absent until the zip build).
- **Deferred sibling imports:** all 4 sibling dialogs (edit_dialog/save_load_dialogs/achievements_dialog/help_dialog) imported inside their handlers so main_window.py py_compiles regardless of which parallel sibling exists at commit time.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] edit.prompt apply_edit raises -- routed via the engine directly**
- **Found during:** Task 2 (MainWindow render_turn / _open_edit_dialog)
- **Issue:** The plan prescribed `controller.apply_edit(intent)` after `build_edit_intent` at edit.prompt, but `Controller.apply_edit` re-reads the enzyme_id from the current node's `edit:enzyme:<id>` tag (controller.py:361) + raises `RuntimeError` at edit.prompt (which has NO such tag -- confirmed by `test_apply_edit_raises_when_no_enzyme_tag`). The controller's `apply_edit` is designed for the edit-allowed SOURCE node, not edit.prompt (its docstring: "do NOT use the pending stash here; that's for build_edit_intent at edit.prompt"). `build_edit_intent` IS designed for edit.prompt (stash fallback), so the EditIntent it returns already carries the stashed enzyme_id.
- **Fix:** In `_open_edit_dialog`, route via `self._controller._engine.apply_player_edit(intent, intent.enzyme_id)` + `self._controller._record_achievement(...)` + `self._controller._render(turn)` -- mirroring `apply_edit`'s exact logic but using the EditIntent's enzyme_id (set by `build_edit_intent` from the stash) instead of re-reading the absent node tag. This keeps 06-06's controller + 06-09's dialog unmodified (the plan's constraint) while making the edit.prompt seam functional. The 06-09 EditDialog.submit docstring (lines 209-219) acknowledges the same bug + defers the controller fix to a 06-06-owned change (out of scope for 06-08 + 06-09).
- **Files modified:** c14/ui/main_window.py (_open_edit_dialog)
- **Verification:** py_compile PASS; 308 tests green (controller + its test_apply_edit_raises_when_no_enzyme_tag unmodified); the engine-direct route mirrors apply_edit's molaction dispatch (the engine's sink is the controller's _dispatch_molaction, so on_enter MolActions flow to molops -> cmd.* as designed). Functional edit flow is human-verify in 06-14.
- **Committed in:** f7b713b (Task 2 commit)

**2. [Rule 3 - Blocking] story_dir dev fallback**
- **Found during:** Task 2 (MainWindow __init__ controller construction)
- **Issue:** The plan prescribed `story_dir = str(c14.paths.data_path("data", "story_glucose"))`. In the SHIPPED plugin this resolves correctly (the 06-07 build script bundles `data/story_glucose/` into `c14/data/story_glucose/` in the zip), but in a bare repo checkout (dev / 06-14 human-verify) `c14/data/story_glucose/` does NOT exist -- the story lives at repo-root `data/story_glucose/`. Without a fallback, `StoryGraph.load(story_dir)` raises `FileNotFoundError` on MainWindow construction in dev.
- **Fix:** Added `_resolve_story_dir()`: prefers the shipped `c14/data/story_glucose` (is_dir check); falls back to repo-root `data/story_glucose` (2 dirs up from this file); returns the shipped path (fail-loud) if neither exists. Works both in the installed plugin AND from a checkout.
- **Files modified:** c14/ui/main_window.py (_resolve_story_dir)
- **Verification:** py_compile PASS; both paths verified to exist (shipped absent in dev, repo-root present); the StoryGraph.load manifest read is the same either way.
- **Committed in:** f7b713b (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both auto-fixes necessary for the functional edit.prompt flow + dev-runability. No scope creep -- the deliverables (MainWindow + StartDialog + StoryPanel + ChoicePanel + render_turn + toolbar + edit.prompt seam) match the plan exactly; only the apply routing mechanism + the story-dir resolver changed.

## Issues Encountered
- The edit.prompt seam has a known cross-plan bug acknowledged by 06-06 (apply_edit raises at edit.prompt by design), 06-08 (this plan -- worked around via engine-direct route), + 06-09 (EditDialog.submit calls apply_edit verbatim + defers the controller fix). The clean long-term fix is a 1-line change to 06-06's `Controller.apply_edit` (fall back to `edit_intent.enzyme_id` when `_current_enzyme_id()` is None) + updating `test_apply_edit_raises_when_no_enzyme_tag` to use `enzyme_id=None`. That is OUT OF SCOPE for 06-08 (file ownership: 06-06 owns controller.py); noted here for a future plan / 06-14 integration. My 06-08 workaround makes the flow functional now.

## User Setup Required
None - no external service configuration required. (The plugin runs inside PyMOL; the molops stack uses the already-injected real cmd. No new dependencies.)

## Next Phase Readiness
- The SC1 core UI surface is built: MainWindow opens with character selection (StartDialog), story text (StoryPanel), choice panel (ChoicePanel), + the cast/help/save/load/achievement toolbar controls. Ready for 06-14 human-verify (the functional window: opens, story renders, choices clickable, tca.shuffle Spin/Edit/cycle-trap, start dialog, save/load/achievements/help buttons route).
- The edit.prompt seam is wired + functional (via the engine-direct workaround); the EditDialog (06-09, now committed) + save_load_dialogs (06-11, now committed) APIs match my deferred imports (verified: EditDialog(controller, enzyme_id, parent) + selected_edit() -> (op,target,args); ask_save_path(parent) + ask_load_path(parent)).
- **Blocker/concern for 06-14:** the edit.prompt apply routing uses a 06-08-local workaround (engine-direct) rather than the plan's prescribed `controller.apply_edit` (which raises). 06-14 human-verify should exercise the full edit:offer -> edit.prompt -> EditDialog -> apply -> routed branch flow. If 06-14 prefers 06-09's `EditDialog.submit` helper, that helper calls `apply_edit` (raises) -- so 06-14 should either use 06-08's inline `_open_edit_dialog` OR apply the 06-06 controller fix first.
- py_compile + AST gate pass (the WSL-verifiable checks); importing in WSL fails (no Qt) -- EXPECTED for c14/ui/ files.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-30*
