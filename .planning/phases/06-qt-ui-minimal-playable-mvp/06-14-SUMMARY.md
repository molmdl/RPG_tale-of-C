---
phase: 06-qt-ui-minimal-playable-mvp
plan: 14
subsystem: testing
tags: [pymol, headless-smoke, integration, controller, bfs-walk, hero-highlight, achievements, save-load, bulk-download]

# Dependency graph
requires:
  - phase: 06-qt-ui-minimal-playable-mvp (06-01 through 06-13)
    provides: the 4 deferred molops dispatches + load target-prefix fallback (06-01), user_data_path resolver (06-02), view-matrix injection (06-03), AchievementBoard (06-04), pyr.branch cond fix + start-node _smoke.pdb swap + hero-highlight sequence (06-05), Controller + goto routing + Blocker 1 fix c (06-06), plugin entry + menu (06-07), MainWindow + widgets (06-08), EditDialog (06-09), bulk-download runner (06-10), save/load dialogs (06-11), achievements dialog (06-12), help dialog (06-13)
provides:
  - Headless integration smoke (tools/controller_integration_smoke.py) proving the full Controller path end-to-end (SC1-3 mechanism proof)
  - HeroResolver pre-pass count robustness fix (the count_fn is called before the on_enter load dispatches)
  - Task 2 human-verify checkpoint material (the 5 SCs for a real Windows PyMOL session)
affects: [07-content-glucose, 10-polish-playtest]

# Tech tracking
tech-stack:
  added: []  # no new dependencies -- pure pymol.cmd.* + c14 domain modules
  patterns:
    - "BFS-distance-guided walk: precompute reverse-edge shortest-path dist from every node to end.true (cond-IGNORED), then walk picking the eligible choice with minimum dist[goto] -- deterministic + assertable, NOT 'many Continue clicks'"
    - "HeroResolver pre-pass count try/except: a count on a not-yet-loaded object is treated as ambiguous (n=0 != 1) -> prompt (OQ-6 multi-C path)"

key-files:
  created:
    - tools/controller_integration_smoke.py
  modified:
    - c14/ui/controller.py

key-decisions:
  - "The HeroResolver pre-pass count MUST be wrapped in try/except: it runs BEFORE the on_enter load dispatches, so the hero object does not exist yet at pre-pass time; a bare cmd.count_atoms on a non-existent object RAISES CmdException (03-01 decision). The count failure is treated as ambiguous (n=0) -> prompt (OQ-6 multi-C path)."
  - "The label assertion uses cmd.iterate (reading the label atom property), NOT count_atoms('... and label') -- `label` is an atom PROPERTY, not a selection keyword (hero_highlight_smoke.py:191-194 uses the same iterate approach)."

patterns-established:
  - "Headless integration smoke pattern: real molops stack + MockView + mock prompt_fn/count_fn + real EditRouter/AchievementBoard; SMOKE_RESULT sentinel; check() helper; FAILS list; pymol.finish_launching() first; sys.path.insert(0, os.getcwd())"

# Metrics
duration: 14 min
completed: 2026-08-30
---

# Phase 6 Plan 14: Phase 6 CAPSTONE Summary

**Headless integration smoke proving the full Controller path end-to-end (SC1-3 mechanism: start + hero highlight, pyr.branch cond fix, tca.shuffle goto routing to a Bad ending, True ending via BFS-distance-guided walk, save/load with view, achievements, bulk-download runner); Task 2 human-verify (SC1-5 in a real Windows PyMOL session) awaits the human.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-08-29T18:45:30Z
- **Completed:** 2026-08-29T19:00:02Z
- **Tasks:** 1/2 complete (Task 1 auto COMPLETE; Task 2 checkpoint:human-verify PENDING)
- **Files modified:** 2 (1 created, 1 fixed)

## Accomplishments

- **Task 1 COMPLETE:** Headless integration smoke (`tools/controller_integration_smoke.py`) — 58/58 stage checks PASS, `SMOKE_RESULT: PASS`. Proves the full Controller path end-to-end against the REAL PyMOL 2.5.0 cmd + the REAL molops stack (AssetManager + EditOps + ProtonationManager + MolOps) + the REAL story_glucose graph + a real EditRouter + a real AchievementBoard, with a MockView (NO Qt):
  - **Stage 4 (start + hero highlight):** `start_game("glucose", seed=42)` -> intro.preface; the 06-05 start-node `_smoke.pdb` swap + 06-01 load-branch bare-filename target fallback load `hero_atom` (3 atoms, NO KeyError, NO network); the 6-call hero-highlight sequence dispatched (`hero_cyan` color defined, `YOU` label via `cmd.iterate`); achievements: `glucose_tried` + `first_game` unlocked (06-04).
  - **Stage 5 (pyr.branch cond fix — 06-05):** walked intro.preface -> ... -> pyr.branch; the aerobic choice's cond `not flags.get('host_o2_low')` is met (the 06-05 dict-method cond-syntax fix), the anaerobic choice's cond `flags.get('host_o2_low')` is NOT met; proceeded to `pyr.pdh`.
  - **Stage 6 (tca.shuffle goto routing — 06-06 Blocker B):** walked to `tca.shuffle`; `is_mixed_weighted_node` True (2 weighted + 1 non-weighted eligible); spun the wheel 5x + returned via "The cycle turns again" 5x (visits=6); the cycle-trap cond `visits.get('tca.shuffle', 0) > 5` became True; `take_choice(cycle_trap)` via `engine.goto` (NOT `choose` — 06-06 Blocker B fix) -> `bad.cycle_trap_host_death` (a Bad ending — SC3 Bad path); `bad_ending` achievement unlocked.
  - **Stage 7 (True ending via BFS-distance-guided walk):** fresh controller (seed=7); precomputed `dist[id]` = BFS shortest-path distance from every node to `end.true` over reverse choice edges (cond-IGNORED — `dist[intro.preface]=28`); the dist-guided walk deterministically reached `end.true` in 28 steps; milestone path asserted in-order (`intro.preface -> intro.select -> intro.shell_glucose -> gly.start -> gly.g6p -> gly.pfk -> gly.fbp_to_pyruvate -> gly.pyruvate_kinase -> gly.pyruvate -> pyr.branch -> pyr.pdh -> tca.entry -> tca.citrate_synthase -> tca.aconitase -> tca.shuffle -> tca.co2_turn1 -> tca.isocitrate_dh -> tca.akg_dh -> tca.succinyl_coa_synthetase -> tca.fumarase -> tca.malate_dh -> tca.divert_to_good -> etc.entry -> etc.complex_i -> etc.complex_ii -> etc.complex_iii -> etc.complex_iv -> etc.atp_synthase` then `end.true`); `true_ending` achievement unlocked.
  - **Stage 8 (save/load round-trip with view — 06-03):** saved at `gly.g6p` (mid-game, non-ending); the view was captured (18 floats); loaded into a 2nd controller; `current_node`, `seed`, `rng_state` all match; the view was applied (the `view_applier` was called); the scene rebuilt (on_enter replayed, the loaded controller's view rendered).
  - **Stage 9 (bulk-download runner — 06-10):** `missing_large_pdbs(cmd)` returns `[]` for the Phase 6 placeholder cast (PLACEHOLDER guard skips `PLACEHOLDER_PDB`); `run_bulk_download(cmd, [])` returns all-zeros; `characters_to_lock([])` returns empty set; `expected_download_characters()` returns empty set.
- **No regression:** 309 unit tests green; AST gate clean (exit 0).

## Task Commits

1. **Task 1 HeroResolver fix** — `3a661f5` (fix) — `c14/ui/controller.py`
2. **Task 1 headless integration smoke** — `ad95068` (feat) — `tools/controller_integration_smoke.py`

**Plan metadata:** pending (Task 2 human-verify not yet complete — SUMMARY + STATE committed below).

## Files Created/Modified

- `tools/controller_integration_smoke.py` — The headless end-to-end Controller path smoke (SC1-3 mechanism proof). Pure `pymol.cmd.*` (NO Qt — MockView). 10 stages, 58 checks, `SMOKE_RESULT: PASS`.
- `c14/ui/controller.py` — HeroResolver.resolve: wrapped the `count_fn(hero_sele)` call in try/except. The pre-pass count runs BEFORE the on_enter load dispatches, so the hero object may not exist yet; a count failure is treated as ambiguous (n=0 != 1) -> prompt (OQ-6 multi-C path). Minimal fix (14 insertions, 1 deletion).

## Decisions Made

- The HeroResolver pre-pass count MUST be wrapped in try/except: it runs BEFORE the on_enter load dispatches (start_game/choose/take_choice all do the hero pre-pass BEFORE the engine enters the node + runs on_enter). At pre-pass time the hero object does NOT exist yet (the load is in on_enter). A bare `cmd.count_atoms` on a non-existent object RAISES `CmdException` (03-01 decision: "Invalid selection name"). The count failure is treated as ambiguous (n=0) -> prompt (OQ-6 multi-C path). This is the root-cause fix that benefits BOTH the headless smoke AND the real MainWindow (06-08) — both inject a count_fn wrapping `cmd.count_atoms`.
- The label assertion uses `cmd.iterate` (reading the `label` atom property), NOT `count_atoms('... and label')` — `label` is an atom PROPERTY, not a selection keyword (the plan prescribed `count_atoms('hero_atom and label')` which raises `CmdException: Misplaced )`). The correct approach (used by `hero_highlight_smoke.py:191-194`) is `cmd.iterate("hero_atom", "lbls.append(label)", ...)`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] HeroResolver pre-pass count crashes on a not-yet-loaded hero object**
- **Found during:** Task 1, Stage 4 (start a glucose game)
- **Issue:** `HeroResolver.resolve` called `count_fn(hero_sele)` (= `cmd.count_atoms("hero_atom")`) BEFORE the on_enter load dispatches. At pre-pass time the `hero_atom` object does NOT exist yet (the load is in `intro.preface`'s on_enter, which runs AFTER the pre-pass). A bare `cmd.count_atoms` on a non-existent object RAISES `CmdException: Invalid selection name "hero_atom"` (03-01 decision), crashing `start_game`. This bug affects BOTH the headless smoke AND the real MainWindow (06-08) — both inject `count_fn = lambda sele: cmd.count_atoms(sele)`.
- **Fix:** Wrapped the `count_fn(hero_sele)` call in `try/except Exception`. A count failure (object not yet loaded) is treated as ambiguous (`n=0 != 1`) -> prompt the player (OQ-6 multi-C path). The prompt + confirm is the no-fabricated-science guard regardless; the count only determines whether to skip the prompt (single-C deterministic) vs prompt (multi-C ambiguous).
- **Files modified:** `c14/ui/controller.py` (HeroResolver.resolve, 14 insertions / 1 deletion)
- **Verification:** 19 controller unit tests still green (the mock count_fn never raises, so the except branch is not exercised by existing tests); 309 full suite green; AST gate clean; the headless smoke Stage 4 now PASSES.
- **Commit:** `3a661f5`

**2. [Rule 1 - Bug] Plan's prescribed label selector was invalid PyMOL syntax**
- **Found during:** Task 1, Stage 4 (hero YOU label assertion)
- **Issue:** The plan prescribed `assert cmd.count_atoms('hero_atom and label') >= 1`. But `label` is an atom PROPERTY (read via `cmd.iterate`), NOT a PyMOL selection keyword. `count_atoms("hero_atom and label")` raises `CmdException: Misplaced )`. The plan's assertion was incorrect — the correct way (used by `hero_highlight_smoke.py:191-194`) is `cmd.iterate("hero_atom", "lbls.append(label)", ...)`.
- **Fix:** Changed the smoke's label assertion from `cmd.count_atoms("hero_atom and label")` to `cmd.iterate("hero_atom", "lbls.append(label)", space=...)` + `any(l == "YOU" for l in lbls)`. This is NOT a weakening — it uses the CORRECT PyMOL API to verify the same post-condition (the "YOU" label dispatched). The label dispatch itself (molops `label` op -> `cmd.label`) works correctly.
- **Files modified:** `tools/controller_integration_smoke.py` (the assertion, not the code under test)
- **Verification:** The headless smoke Stage 4 `hero_you_label_dispatched` check now PASSES (reads the label via iterate, asserts at least one "YOU").
- **Commit:** `ad95068` (part of the smoke commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for the integration to work. The HeroResolver fix is the root-cause fix for a crash that would affect the real MainWindow (Task 2) too. The label-assertion fix corrects an invalid PyMOL selector in the plan. No scope creep.

## Issues Encountered

- Mid-game `pdb:XXX` loads (`pdb:4PFK`, `pdb:6CFO`, `pdb:1CSC`, `pdb:TBD_ACONITASE`, `pdb:5GRF`, `pdb:7FS3`, `pdb:1OCC`) fail offline (network fetch) in the headless environment. The controller's defensive try/except (06-06 Blocker 1 fix c) degrades gracefully (logs + continues to the next on_enter action). The smoke does NOT assert those mid-game loads succeed headlessly — only the start-node bundled `_smoke.pdb` load is asserted (no network). This is the EXPECTED behavior per the plan.

## User Setup Required

None — no external service configuration required for Task 1. Task 2 (human-verify) requires a real Windows PyMOL 2.5.0 session (the WSL agent cannot run Qt/GUI per AGENTS.md).

## Checkpoint: human-verify pending

**Task 2 status:** awaiting human-verify

Task 2 is a `checkpoint:human-verify` that requires a **real Windows PyMOL 2.5.0 session** (the WSL agent CANNOT run Qt/GUI per AGENTS.md). The headless smoke (Task 1) proved the SC1-3 MECHANISM (controller wiring, molops dispatch, view capture/restore, tca.shuffle goto routing, pyr.branch cond fix, hero highlight). Task 2 verifies the Qt RENDERING + the real PyMOL session behavior the WSL agent cannot exercise — ALL 5 Success Criteria:

- **SC1 — install + menu + main window:** build the zip (`bash tools/build_plugin_zip.sh`), install via Plugin Manager, restart, confirm the "RPG: Tale of C" menu item + the main window opens (toolbar + story panel + choice panel + status bar).
- **SC2 — hero highlight + scene templates:** start a glucose game; confirm the C14 hero atom is highlighted (cyan + "YOU" label) in the loaded `_smoke.pdb` structure; the OQ-6 HeroResolver prompts "2 carbons... Highlight the first carbon?" — click Yes; advance through Continue choices; confirm residue representations at relevant stages.
- **SC3 — reach True + Bad endings + save/load round-trip:** play to `tca.shuffle`, spin 6+ times, click "cycle has spun too long" -> `bad.cycle_trap_host_death` (Bad ending, "Lost Connection" unlocks); new game -> aerobic path -> `end.true` (True ending, "Soul Harvested" unlocks); mid-game Save -> Load -> confirm story position + RNG state + structures + camera view restore.
- **SC4 — bulk-download:** confirm small/critical structures are bundled (glucose starts instantly); IF a download is triggered, confirm progress bar advances per-file, Cancel stops after the current file, Retry re-runs skipping already-downloaded, offline failure locks only the affected character. (Phase 6 cast has only PLACEHOLDER download enzymes — the prompt may NOT fire; the mechanism is verified headlessly in Task 1 Stage 9.)
- **SC5 — achievements + help:** click Achievements -> the board shows unlocks (First Steps + Glucose + endings found); close + reopen PyMOL -> unlocks PERSIST (ACH-02); click Help -> 4 editing pointers + 3 PyMOL wiki links (clickable, open in browser).

**Awaiting:** the user types "approved" (all 5 SCs pass) OR describes which SC(s) failed + what they observed. The agent will then diagnose + create gap-closure plans if needed.

## Next Phase Readiness

- **Task 1 (headless smoke) COMPLETE:** the SC1-3 mechanism is proven end-to-end. The controller wiring, molops dispatch, view capture/restore, tca.shuffle goto routing, pyr.branch cond fix, hero highlight, achievements, save/load, and bulk-download runner all work headlessly.
- **Task 2 (human-verify) PENDING:** the Qt rendering + real PyMOL session behavior must be verified by the human. Until Task 2 is approved, Phase 6 is NOT complete (this is the FIRST human-verify milestone — the game is played end-to-end for the first time).
- **Blockers/concerns:** the HeroResolver pre-pass count fix (3a661f5) is essential for the real MainWindow to not crash at start_game — it should be reviewed as part of Task 2.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-30 (Task 1); Task 2 awaiting human-verify*
