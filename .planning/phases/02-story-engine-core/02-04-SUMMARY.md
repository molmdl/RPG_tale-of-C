---
phase: 02-story-engine-core
plan: 04
subsystem: engine
tags: [save-load, game-engine, turn-loop, rng-state, json-serialization, testability-boundary, molaction-sink]

# Dependency graph
requires:
  - phase: 02-01
    provides: Node/Choice/MolAction model + RngEngine (from_state/get_state) + GameState (new_game/to_dict/from_dict/record_visit/mark_finished)
  - phase: 02-02
    provides: StoryGraph (load/start_node/get_node) + StoryInterpreter (pick_choice/enter_node/apply_effects/_cond)
provides:
  - SaveStore (save/load GameState to human-readable JSON, indent=2, parent-dir creation)
  - GameEngine turn loop (start/choose/_enter/save/load) wiring StoryInterpreter + GameState + RngEngine
  - TurnResult (node + on_enter MolActions + eligible choices)
  - Per-action MolAction dispatch to an injected molaction_sink (testability boundary -- never cmd.*)
  - Save/load with RNG-state sync + on_enter replay (Pattern 6) -- success criterion #3 proven
affects: [02-05 (integration test + runnable demo), Phase 3 (pymol_layer consumes MolActions from the sink), Phase 4 (edit_router integrates with engine), Phase 6 (Qt controller owns the GameEngine instance)]

# Tech tracking
tech-stack:
  added: []  # stdlib only (json, os) -- no new deps
  patterns:
    - "Pattern 6 (Save/Load as Game-State JSON): engine replays the current node's on_enter MolActions on load to reconstruct the scene; the scene is a pure function of game state, NOT a saved .pse session (Anti-Pattern 5 avoided)"
    - "Testability boundary via injection: GameEngine emits MolActions per-action to an injected callable sink (a plain list .append in tests); the engine NEVER imports/calls cmd.* -- 'pymol' not in sys.modules after a full playthrough with save/load"
    - "RNG-state sync: engine writes rng.get_state() into GameState after every enter (and before save); load rebuilds the RngEngine via RngEngine.from_state(seed, rng_state) so the exact next draw survives save/load (Anti-Pattern 7 single-seeded-engine discipline carried into the turn loop)"

key-files:
  created:
    - c14/persist.py
    - c14/engine.py
    - tests/test_persist.py
    - tests/test_engine.py
  modified:
    - c14/story/interpreter.py  # backward-compatible record_visit=True param on enter_node

key-decisions:
  - "SaveStore is a thin pure-data layer -- it does NOT replay MolActions and does NOT save .pse; the ENGINE owns the on_enter replay on load (Pattern 6). Kept SaveStore to json.dump/load + GameState.from_dict only."
  - "Per-action MolAction dispatch (not a single list call): the engine calls molaction_sink(action) once per on_enter MolAction so a plain list's .append collects one entry per action. Chosen because the plan's test done-criteria (len(sink)==2, sink[0].op=='hide_all' with sink.append as the sink) require per-action dispatch; the plan's key_links prose ('callable(list[MolAction])') conflicted with its own tests, so the tests (authoritative done criteria) won. See Deviations."
  - "record_visit=True param added to interpreter.enter_node (2-line backward-compatible additive edit) so the engine can replay on_enter on load WITHOUT double-counting visits. load passes record_visit=False; normal play + tests pass True (default). All 12 existing interpreter tests still pass."
  - "save() syncs rng.get_state() into state BEFORE serialization; _enter() also syncs after every entry, so a save at any point captures the exact PRNG position. load() rebuilds via RngEngine.from_state(seed, rng_state). Exact-next-draw equivalence proven by test_rng_state_survives_save_load."

patterns-established:
  - "Pattern: GameEngine owns one GameState + one RngEngine per playthrough; StoryInterpreter is stateless and dependency-injected (passed state+rng per call) -- a single interpreter serves any playthrough"
  - "Pattern: eligible_choices = node.choices for non-ending nodes, [] for endings -- the engine does NOT pre-draw the RNG for presentation; the RNG is only consumed when choose() resolves a weighted pick"
  - "Pattern: TurnResult is the engine/UI contract (node + molactions + eligible_choices); the controller dispatches molactions to pymol_layer and presents the node + choices to Qt"

# Metrics
duration: 49min
completed: 2026-08-13
---

# Phase 2 Plan 04: SaveStore + GameEngine Turn Loop Summary

**SaveStore (human-readable JSON of GameState) + GameEngine turn loop that wires StoryInterpreter/GameState/RngEngine, emits on_enter MolActions per-action to an injected sink, and round-trips save/load by syncing RNG state and replaying on_enter (Pattern 6) -- never cmd.\***

## Performance

- **Duration:** 49 min
- **Started:** 2026-08-13T19:02:54Z
- **Completed:** 2026-08-13T19:51:33Z
- **Tasks:** 2
- **Files modified:** 4 created + 1 modified

## Accomplishments
- SaveStore serializes GameState to human-readable JSON (indent=2, parent-dir creation, trailing newline) and restores via GameState.from_dict -- pure data, no .pse, no on_enter replay (the engine owns that)
- GameEngine turn loop (start/choose/_enter/save/load) wires StoryInterpreter + GameState + RngEngine; emits on_enter MolActions per-action to an injected molaction_sink (testability boundary -- never cmd.*)
- Save/load with RNG-state sync + on_enter replay (Pattern 6) proven: load restores an identical GameState (all fields incl. rng_state), re-enters the current node, replays its on_enter MolActions to reconstruct the scene, and does NOT double-count visits -- Phase 2 success criterion #3 PROVEN
- RNG state survives save/load: the exact next draw after load matches the next draw after save (success criterion #2 component proven end-to-end through the engine)
- 15 new unit tests (5 persist + 10 engine); 80 total tests pass; AST gate green; no pymol import after a full playthrough with save/load

## Task Commits

Each task was committed atomically:

1. **Task 1: SaveStore JSON serializer + tests** - `803c3a8` (feat)
2. **Task 2: GameEngine turn loop + save/load + on_enter replay + interpreter record_visit edit + tests** - `44b8b00` (feat)

**Plan metadata:** (this commit) `docs(02-04): complete save-store + game-engine plan`

## Files Created/Modified
- `c14/persist.py` - SaveStore.save(state, path) writes human-readable JSON (indent=2, parent-dir creation, trailing newline); SaveStore.load(path) restores via GameState.from_dict. Pure data (de)serialization.
- `c14/engine.py` - GameEngine (start/choose/_enter/save/load) + TurnResult. Wires StoryInterpreter + GameState + RngEngine. Emits on_enter MolActions per-action to the injected sink. save syncs rng.get_state(); load rebuilds via RngEngine.from_state and replays on_enter with record_visit=False.
- `c14/story/interpreter.py` - enter_node gains backward-compatible `record_visit=True` param (load-replay passes False to avoid double-counting visits). 2-line additive edit.
- `tests/test_persist.py` - 5 tests: round-trip preserves all fields incl. rng_state, parent-dir creation, human-readable JSON, malformed->ValueError, missing->OSError.
- `tests/test_engine.py` - 10 tests: start enters + emits, state initialized, choose advances to ending, weighted autopick ignores index, save/load round-trip, load replays on_enter, load no double-count, rng state survives save/load, no pymol import, random seed mode.

## Decisions Made
- SaveStore is a thin pure-data layer (json.dump/load + GameState.from_dict); the ENGINE owns the on_enter replay on load (Pattern 6). See key-decisions.
- Per-action MolAction dispatch (molaction_sink called once per MolAction, not once with the list) -- the plan's test done-criteria required it; the key_links prose conflicted and the tests won. See Deviations.
- record_visit=True param added to interpreter.enter_node (backward-compatible) so load-replay skips the visit bump. See key-decisions.
- save() and _enter() both sync rng.get_state() into state; load() rebuilds via RngEngine.from_state(seed, rng_state). Exact-next-draw equivalence is the success-criterion proof.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] GameEngine dispatched the whole MolAction list to the sink instead of per-action**
- **Found during:** Task 2 (GameEngine + tests) -- first test run
- **Issue:** The initial `_enter` called `self.molaction_sink(actions)` (one call with the whole list). But the plan's test done-criteria (`test_start_enters_start_node`: `len(sink) == 2` and `sink[0].op == 'hide_all'` with `molaction_sink=sink.append`) require the sink to be called once PER MolAction so the list collects one entry per action. With the list-call, `len(sink)` was 1 and `sink[0]` was a list (no `.op`). The plan's `key_links` prose ("callable(list[MolAction])") conflicted with its own test assertions; the test assertions are the authoritative done criteria.
- **Fix:** Changed `_enter` to `for action in actions: self.molaction_sink(action)` (per-action dispatch). Updated the module docstring to "a callable taking a single MolAction -- dispatched per action". Updated the `_enter` docstring + inline comment to document the per-action contract and why (the mock sink's `.append` collects one entry per action).
- **Files modified:** c14/engine.py
- **Verification:** `tests.test_engine` -- all 10 tests pass (incl. `test_start_enters_start_node`: len(sink)==2, sink[0].op=='hide_all'); `test_load_replays_on_enter_molactions`: len(sink2)>=1 holds (replays 2 actions for intro.start). Full suite 80 tests pass; AST gate green.
- **Committed in:** 44b8b00 (Task 2 commit)

**2. [Planned, not a deviation] interpreter.enter_node record_visit param**
- The plan EXPLICITLY required adding `record_visit=True` to `StoryInterpreter.enter_node` as a mandatory surgical edit (listed in `<files>` / `files_modified`). Executed exactly as specified -- 2-line backward-compatible additive change; all 12 existing interpreter tests still pass. Documented here for completeness; not a Rule 1-4 deviation.

---

**Total deviations:** 1 auto-fixed (1 bug -- per-action dispatch to match test done-criteria)
**Impact on plan:** Minimal, in-scope. The per-action dispatch is the contract the plan's own tests defined; the prose was internally inconsistent. The fix makes the engine match its done-criteria with zero scope creep. The Phase 4+ controller sink will receive one MolAction per call (the natural unit for `c14/pymol_layer/molops.apply(action)`).

## Issues Encountered
None beyond the per-action dispatch fix above.

## User Setup Required
None - no external service configuration required. Pure-Python, stdlib only.

## Next Phase Readiness
- Phase 2 success criterion #3 PROVEN: save serializes GameState (incl. RNG seed + state) to human-readable JSON; load restores an identical session by replaying the current node's on_enter MolActions (Pattern 6); RNG state survives save/load (same next draw after load).
- Phase 2 success criterion #2 component proven through the engine: the single seeded RngEngine carries through start->choose->save->load with the exact next draw preserved.
- The engine is pure-Python (no pymol import) and ready for Plan 02-05 (end-to-end integration test + runnable demo) which will exercise the full start->choose->save->load->continue flow against the real data/story graph.
- Blockers/concerns: None. Plan 02-05 is the last plan in Phase 2 (the architecture proof); after it, Phase 2 is complete and Phase 5.1 (Story Graph Design) can start (it depends on Phase 2 + the now-RESOLVED ATP/True-Ending decision).

---
*Phase: 02-story-engine-core*
*Completed: 2026-08-13*
