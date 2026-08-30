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
  - Task 2 human-verify verdict (recorded 2026-08-30) + the 3 SC2 bug fixes (edit-dialog 3-tuple contract, single-carbon hero default sele via empirically-verified `first` operator, stage-tag status bar) + the recorded open items
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
    - tools/probe_first_operator.py
  modified:
    - c14/ui/controller.py
    - c14/ui/edit_dialog.py
    - c14/ui/main_window.py
    - tests/test_controller.py
    - tools/controller_integration_smoke.py

key-decisions:
  - "The HeroResolver pre-pass count MUST be wrapped in try/except: it runs BEFORE the on_enter load dispatches, so the hero object does not exist yet at pre-pass time; a bare cmd.count_atoms on a non-existent object RAISES CmdException (03-01 decision). The count failure is treated as ambiguous (n=0) -> prompt (OQ-6 multi-C path)."
  - "The label assertion uses cmd.iterate (reading the label atom property), NOT count_atoms('... and label') -- `label` is an atom PROPERTY, not a selection keyword (hero_highlight_smoke.py:191-194 uses the same iterate approach)."
  - "06-14 fix session: the OQ-6 default sele is `first (<obj> and elem C)` -- EMPIRICALLY VERIFIED headlessly (tools/probe_first_operator.py): PyMOL 2.5.0 supports the `first` operator; it resolves to exactly 1 atom and picks C1 (id=1, the first carbon by internal order); spheres+label post-conditions work on the sele. The old `<obj> and elem C` matched ALL carbons (SC2a: both got spheres + YOU)."
  - "06-14 fix session (probe byproduct): the cmd.iterate atom-namespace property for atom id is `ID` (UPPERCASE, completing.py:18-29); lowercase `id` raises NameError. `label` is likewise a property, not a selector."
  - "06-14 fix session: EditDialog.selected_edit() returns the DOCUMENTED (op, target, args) 3-tuple (strips the display-only label from the stored (label, op, target, args) option tuple) -- the contract main_window.py:413 already unpacks."

patterns-established:
  - "Headless integration smoke pattern: real molops stack + MockView + mock prompt_fn/count_fn + real EditRouter/AchievementBoard; SMOKE_RESULT sentinel; check() helper; FAILS list; pymol.finish_launching() first; sys.path.insert(0, os.getcwd())"

# Metrics
duration: 14 min
completed: 2026-08-30
---

# Phase 6 Plan 14: Phase 6 CAPSTONE Summary

**Headless integration smoke proving the full Controller path end-to-end (SC1-3 mechanism: start + hero highlight, pyr.branch cond fix, tca.shuffle goto routing to a Bad ending, True ending via BFS-distance-guided walk, save/load with view, achievements, bulk-download runner); Task 2 human-verify VERDICT: SC1 PASS, SC3 PASS, SC4/SC5 PASS (placeholders expected), SC2 findings fixed (edit-dialog 3-tuple crash, both-carbons "YOU", orientation status bar) — 3 fix commits, all gates green, 5 open items recorded for the user/Phase 7.**

## Performance

- **Duration:** 14 min (Task 1) + ~35 min (Task 2 verdict + fix session)
- **Started:** 2026-08-29T18:45:30Z (Task 1); 2026-08-30T07:15Z (fix session)
- **Completed:** 2026-08-30 (Task 2 verdict recorded + fixes committed 07:47Z)
- **Tasks:** 2/2 complete (Task 1 auto COMPLETE; Task 2 checkpoint:human-verify COMPLETE — verdict recorded, SC2 bugs fixed, open items documented)
- **Files modified:** 6 (1 created Task 1, 1 fixed Task 1; 3 fixed + 1 created + 1 test-updated in the fix session)

## Accomplishments

- **Task 1 COMPLETE:** Headless integration smoke (`tools/controller_integration_smoke.py`) — 58/58 stage checks PASS, `SMOKE_RESULT: PASS`. Proves the full Controller path end-to-end against the REAL PyMOL 2.5.0 cmd + the REAL molops stack (AssetManager + EditOps + ProtonationManager + MolOps) + the REAL story_glucose graph + a real EditRouter + a real AchievementBoard, with a MockView (NO Qt):
  - **Stage 4 (start + hero highlight):** `start_game("glucose", seed=42)` -> intro.preface; the 06-05 start-node `_smoke.pdb` swap + 06-01 load-branch bare-filename target fallback load `hero_atom` (3 atoms, NO KeyError, NO network); the 6-call hero-highlight sequence dispatched (`hero_cyan` color defined, `YOU` label via `cmd.iterate`); achievements: `glucose_tried` + `first_game` unlocked (06-04).
  - **Stage 5 (pyr.branch cond fix — 06-05):** walked intro.preface -> ... -> pyr.branch; the aerobic choice's cond `not flags.get('host_o2_low')` is met (the 06-05 dict-method cond-syntax fix), the anaerobic choice's cond `flags.get('host_o2_low')` is NOT met; proceeded to `pyr.pdh`.
  - **Stage 6 (tca.shuffle goto routing — 06-06 Blocker B):** walked to `tca.shuffle`; `is_mixed_weighted_node` True (2 weighted + 1 non-weighted eligible); spun the wheel 5x + returned via "The cycle turns again" 5x (visits=6); the cycle-trap cond `visits.get('tca.shuffle', 0) > 5` became True; `take_choice(cycle_trap)` via `engine.goto` (NOT `choose` — 06-06 Blocker B fix) -> `bad.cycle_trap_host_death` (a Bad ending — SC3 Bad path); `bad_ending` achievement unlocked.
  - **Stage 7 (True ending via BFS-distance-guided walk):** fresh controller (seed=7); precomputed `dist[id]` = BFS shortest-path distance from every node to `end.true` over reverse choice edges (cond-IGNORED — `dist[intro.preface]=28`); the dist-guided walk deterministically reached `end.true` in 28 steps; milestone path asserted in-order (`intro.preface -> intro.select -> intro.shell_glucose -> gly.start -> gly.g6p -> gly.pfk -> gly.fbp_to_pyruvate -> gly.pyruvate_kinase -> gly.pyruvate -> pyr.branch -> pyr.pdh -> tca.entry -> tca.citrate_synthase -> tca.aconitase -> tca.shuffle -> tca.co2_turn1 -> tca.isocitrate_dh -> tca.akg_dh -> tca.succinyl_coa_synthetase -> tca.fumarase -> tca.malate_dh -> tca.divert_to_good -> etc.entry -> etc.complex_i -> etc.complex_ii -> etc.complex_iii -> etc.complex_iv -> etc.atp_synthase` then `end.true`); `true_ending` achievement unlocked.
  - **Stage 8 (save/load round-trip with view — 06-03):** saved at `gly.g6p` (mid-game, non-ending); the view was captured (18 floats); loaded into a 2nd controller; `current_node`, `seed`, `rng_state` all match; the view was applied (the `view_applier` was called); the scene rebuilt (on_enter replayed, the loaded controller's view rendered).
  - **Stage 9 (bulk-download runner — 06-10):** `missing_large_pdbs(cmd)` returns `[]` for the Phase 6 placeholder cast (PLACEHOLDER guard skips `PLACEHOLDER_PDB`); `run_bulk_download(cmd, [])` returns all-zeros; `characters_to_lock([])` returns empty set; `expected_download_characters()` returns empty set.
- **Task 2 COMPLETE (human-verify verdict + SC2 fixes):** the human played the game end-to-end in a real Windows PyMOL session. SC1 PASS, SC3 PASS (camera restores; manual color/rep edits intentionally not restored — scene rebuilds from on_enter replay), SC4 PASS (placeholders expected), SC5 PASS (with a fuller-inline-help preference noted). SC2's concrete bugs FIXED: the edit-dialog unpack crash (Fix 1 `c2d1008`), the both-carbons "YOU" highlight (Fix 2 `389ee3e` — default sele now `first (obj and elem C)`, empirically verified via `tools/probe_first_operator.py`), and the orientation gap (Fix 3 `3f483aa` — status bar shows node id + stage tag). 5 open items recorded for the user/Phase 7 (see the REMAINING OPEN ITEMS section).
- **No regression:** 309 unit tests green; AST gate clean; both smokes + the probe re-ran `SMOKE_RESULT: PASS` post-fix.

## Task Commits

1. **Task 1 HeroResolver fix** — `3a661f5` (fix) — `c14/ui/controller.py`
2. **Task 1 headless integration smoke** — `ad95068` (feat) — `tools/controller_integration_smoke.py`
3. **Fix 1 (SC2f): selected_edit returns the documented 3-tuple** — `c2d1008` (fix) — `c14/ui/edit_dialog.py`
4. **Fix 2 (SC2a): HeroResolver default sele -> first (obj and elem C)** — `389ee3e` (fix) — `c14/ui/controller.py` + `tests/test_controller.py` + `tools/controller_integration_smoke.py` + `tools/probe_first_operator.py`
5. **Fix 3 (SC2b): status bar shows node id + stage tag** — `3f483aa` (fix) — `c14/ui/main_window.py`
6. **Docs: Task 2 verdict + fixes + open items** — this commit — `06-14-SUMMARY.md` + `.planning/STATE.md`

**Plan metadata:** committed (docs commit below).

## Files Created/Modified

Task 1:
- `tools/controller_integration_smoke.py` — The headless end-to-end Controller path smoke (SC1-3 mechanism proof). Pure `pymol.cmd.*` (NO Qt — MockView). 10 stages, 58 checks, `SMOKE_RESULT: PASS`.
- `c14/ui/controller.py` — HeroResolver.resolve: wrapped the `count_fn(hero_sele)` call in try/except (the pre-pass runs BEFORE the on_enter load dispatches; a count failure is treated as ambiguous -> prompt).

Fix session (Task 2 verdict):
- `c14/ui/edit_dialog.py` — Fix 1 (SC2f): `selected_edit()` now returns `self._selected[1:]` (the documented `(op, target, args)` 3-tuple) instead of the raw stored 4-tuple `(label, op, target, args)`; docstrings updated. `main_window.py:413` untouched (it already matches the contract).
- `c14/ui/controller.py` — Fix 2 (SC2a): the OQ-6 default sele is now `"first ({0} and elem C)"` — resolves to EXACTLY ONE carbon (empirically verified); the old `"{0} and elem C"` matched ALL carbons so BOTH got spheres + "YOU" on the 2-carbon `_smoke.pdb` fixture.
- `tools/probe_first_operator.py` — NEW: the empirical `first`-operator probe (pure `pymol.cmd.*`, headless): 9/9 checks PASS. Verdict: `first` SUPPORTED; `count_atoms("first (hero_atom and elem C)")` == 1; picks C1 (id=1, resi 1 — the first carbon); sphere+label post-conditions work on the sele. Fallback (`elem C and index 1`) also verified == 1 but NOT needed. Byproduct documented: the iterate atom-id property is `ID` (uppercase).
- `tests/test_controller.py` — multi-C rewrite assertions expect the single-carbon default sele; added an assertion that the `color` op KEEPS its object-wide all-C sele (the 5.4 all-C-cyan convention).
- `tools/controller_integration_smoke.py` — comment updated to the new default sele; the `hero_you_label_dispatched` check strengthened from "at least one YOU" to EXACTLY ONE `YOU` label (post-fix: `labels=['YOU', '', '']`).
- `c14/ui/main_window.py` — Fix 3 (SC2b): the normal-node status bar now shows `node=<id>  stage=<tag>  character=<c>  seed=<s>` (stage read from the node's `stage:<x>` tag; omitted when absent) + a None-safe `_engine_state(attr)` helper.

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

## Checkpoint: human-verify — VERDICT RECORDED (2026-08-30)

**Task 2 status:** COMPLETE — the human tested the game in a real Windows PyMOL 2.5.0 session and reported the verdict below. The SC2 concrete bugs were fixed in the same session (3 fix commits); the open items are recorded for the user/Phase 7 (NOT resolved unilaterally).

### The human's verdict (abridged, faithful)

- **SC1 — PASS.** Install via Plugin Manager + "RPG: Tale of C" menu + the main window (toolbar / story panel / choice panel / status bar) all work.
- **SC2 — findings (bugs a, b, f + orientation):**
  - **(a)** "it highlight both carbons and highlight both as 'YOU'" — BUG (should be ONE hero carbon). **FIXED** (Fix 2, `389ee3e`).
  - **(b)** after Continue, reached a step showing an enzyme that keeps erroring on Continue: "Error-fetch: unable to load 'tbd_aconitase'" + console "Invalid selection name 'aconitase'", and the player is "not sure which point it is" — orientation problem. **Orientation FIXED** (Fix 3, `3f483aa`); the error noise is CORRECT behavior (see Fix 4 below).
  - **(f)** clicking "Edit enzyme" crashes: `main_window.py:413 _open_edit_dialog -> op, target, args = dlg.selected_edit() -> ValueError: too many values to unpack (expected 3)`. **FIXED** (Fix 1, `c2d1008`).
- **SC3 — PASS.** Camera view restores on save/load. Manual color/rep changes made BEFORE the save do NOT restore — EXPECTED per design: the scene rebuilds from the node's on_enter replay (default reps/colors), and the saved view = CAMERA only (06-03 view-matrix injection scope). Not a bug.
- **SC4 — PASS (placeholders expected).** Glucose starts instantly (bundled small/critical assets; the bulk-download prompt does NOT fire for the Phase 6 placeholder cast — `missing_large_pdbs` returns [] — the mechanism was verified headlessly in Task 1 Stage 9).
- **SC5 — PASS.** Achievements unlock + persist across PyMOL restarts; help shows the 4 editing pointers + 3 clickable wiki links. **User preference (OPEN, do NOT change help.json now):** the user prefers FULLER INLINE help (guidance in the GUI itself) with the wiki links only as reference — a pending design decision.

### Fixes (committed)

1. **Fix 1 (SC2f) — `c2d1008`** — `c14/ui/edit_dialog.py` `selected_edit()` (was line ~173-183): returned the raw `self._selected`, but `_on_accept` stores the FULL `(label, op, target, args)` option tuple (line ~126 comment) while the DOCUMENTED contract (its own docstring + `submit()`'s flow + the caller `main_window.py:413`) is the 3-tuple. Now returns `self._selected[1:]` (3-tuple) when set, else None. `main_window.py` NOT changed (it already matches the contract).
2. **Fix 2 (SC2a) — `389ee3e`** — `c14/ui/controller.py` `HeroResolver.resolve()` line ~143: the default sele `"{0} and elem C"` → `"first ({0} and elem C)"`. The old sele matched ALL carbons (`_smoke.pdb` = ethanol: C1 id 1, O1 id 2, C2 id 3) so BOTH carbons got spheres + "YOU". Per the OQ-6 prompt text ("Highlight the FIRST carbon as the hero?") + the 5.4 convention (ONE hero: sphere + YOU; other carbons: cyan sticks only), the default now resolves to EXACTLY ONE atom. **Empirical verdict (tools/probe_first_operator.py, headless PyMOL 2.5.0, 9/9 PASS): the PREFERRED `first` sele WON** — supported, count == 1, picks C1 (id=1, resi 1 = the first carbon), sphere+label post-conditions OK. The `index 1` fallback was verified (also == 1, also C1) but NOT needed. Tests (`tests/test_controller.py`) updated to the single-carbon sele (+ a new assertion that `color` keeps its object-wide all-C sele per the 5.4 convention); smoke (`tools/controller_integration_smoke.py`) label check strengthened to EXACTLY ONE "YOU" (post-fix `labels=['YOU', '', '']`).
3. **Fix 3 (SC2b orientation) — `3f483aa`** — `c14/ui/main_window.py` `render_turn()` normal-node branch: the status bar now reads `node=gly.start  stage=glycolysis  character=glucose  seed=42` (the node's `stage:<x>` tag extracted from `node.tags`; omitted when absent) + a None-safe `_engine_state(attr)` helper. One line, simple.
4. **Fix 4 (SC2b noise) — VERIFY ONLY, no commit.** The console lines `controller: molops.apply failed for op='load' target='pdb:TBD_ACONITASE': ...` are the controller's defensive one-line swallow (06-06 Blocker 1 fix c) — CORRECT behavior (mid-game `pdb:TBD_*` placeholders fail until Phase 7 fills real structures; the game keeps flowing — re-verified in the headless smoke output). The additional `Error-fetch: unable to load 'tbd_aconitase'` stderr line is PyMOL's own fetch print — deliberately NOT silenced. The optional "(structure placeholder — Phase 7)" status-bar hint was SKIPPED: it would require a new controller→view failure channel (not trivial; no over-engineering).

### Post-fix verification (all green)

- `python3.6 -m py_compile c14/ui/edit_dialog.py c14/ui/controller.py c14/ui/main_window.py` — exit 0.
- `python3.6 -m unittest discover -s tests` — 309 tests, OK.
- `python3.6 tools/check_imports.py` — clean (exit 0).
- `bash tools/run_headless.sh tools/controller_integration_smoke.py` — `SMOKE_RESULT: PASS`, all stage checks green (`hero_you_label_dispatched exactly_one_YOU=True`).
- `bash tools/run_headless.sh tools/hero_highlight_smoke.py` — `PASSED` (regression insurance).
- `bash tools/run_headless.sh tools/probe_first_operator.py` — `SMOKE_RESULT: PASS` (9/9; the `first`-operator verdict recorded above).

### REMAINING OPEN ITEMS (do NOT resolve unilaterally)

1. **Cycle-trap presented as an OPTION vs the user's expectation of a RESULT** — design decision pending the user (the FROZEN story skeleton topology — 55 nodes / 21 endings / cycle-trap as a choice — is NOT changed by these fixes).
2. **Help: fuller inline GUI guidance vs links-only** — pending the user (the user prefers fuller inline help; help.json NOT edited in this session).
3. **Citrate synthase dimer (biological assembly) loading** — Phase 7 cast convention.
4. **Real glucose + story-like text** — Phase 7.
5. **Per-node default color/focus** — 5.4 scene templates filled in Phase 7; ending CG — Phase 12.

### Phase 6 completion status

Task 1 (headless smoke) + Task 2 (human-verify) are both COMPLETE. The human-verify milestone has been exercised end-to-end: SC1/SC3/SC4/SC5 PASS; SC2's concrete bugs (a, b-orientation, f) are FIXED with all gates green; the remaining SC2-adjacent items are Phase 7 content placeholders (tbd_aconitase structures, story text) + the user-decision open items above — none block Phase 6 closure as Phase 6 scope (the MVP).

## Next Phase Readiness

- **Task 1 (headless smoke) COMPLETE:** the SC1-3 mechanism is proven end-to-end. The controller wiring, molops dispatch, view capture/restore, tca.shuffle goto routing, pyr.branch cond fix, hero highlight, achievements, save/load, and bulk-download runner all work headlessly.
- **Task 2 (human-verify) COMPLETE:** SC1/SC3/SC4/SC5 PASS; SC2's concrete bugs (a: both-carbons YOU, b: orientation, f: edit-dialog crash) FIXED (commits `c2d1008` + `389ee3e` + `3f483aa`), all gates green post-fix. The HeroResolver pre-pass count fix (3a661f5) was confirmed working in the real session (start_game did not crash; the OQ-6 prompt fired).
- **Open items carried forward (user decisions + Phase 7 content):** cycle-trap option-vs-result design decision (user); fuller inline help preference (user); citrate synthase dimer loading (Phase 7); real glucose + story-like text (Phase 7); per-node default color/focus + ending CG (Phase 7 / Phase 12). See the REMAINING OPEN ITEMS section above.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-30 (Task 1 + Task 2 verdict + SC2 fixes; open items recorded)*
