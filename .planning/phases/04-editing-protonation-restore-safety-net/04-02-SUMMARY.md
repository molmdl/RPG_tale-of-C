---
phase: 04-editing-protonation-restore-safety-net
plan: 02
subsystem: editing
tags: [edit-routing, edit-intent, bad-ending-pool, rng, lookup-table, pure-python, exact-matching]

# Dependency graph
requires:
  - phase: 02-story-engine-core
    provides: GameEngine (turn loop), GameState.add_edit/edits_history, RngEngine.weighted_pick, StoryGraph.load/all_nodes, StoryInterpreter.enter_node, story model (MolAction/Choice/Node), validate.py (Issue + _is_ending duck-typed helpers)
provides:
  - EditIntent class (routing INPUT, separate from MolAction) with signature() normalization
  - EditRouter (known->branch via exact dict equality, unknown->bad-ending pool via rng.weighted_pick)
  - EditsTable loader (CWD-independent json.load)
  - validate_edits_table (dangling/empty/non-ending/duplicate cross-validation against story graph)
  - scan_edit_coverage (SC5 helper -- per-enzyme minimum-coverage scan)
  - GameEngine.apply_player_edit (SC3 entry point: route -> add_edit -> _enter)
  - Backward-compatible edit_router=None constructor param
  - SC3 fixture bundle (placeholder edits.json + manifest.json + story.json)
affects: [04-04 (check_edit_coverage wraps scan_edit_coverage), 04-05 (molops edit delegation), 05.1 (edit-node contract uses EditIntent), 06 (Qt UI constructs EditIntents), 07+ (real cited edits.json content)]

# Tech tracking
tech-stack:
  added: []  # stdlib only (json); no new dependencies
  patterns:
    - "EditIntent as routing INPUT (player->router) separate from MolAction as execution OUTPUT (engine->molops) -- data-flow directionality"
    - "Exact dict equality matching on a normalized signature (op/target/args) -- zero fuzzy/chemistry logic (Pitfall 1)"
    - "Per-enzyme bad-ending pool OVERRIDE semantics (non-empty per-enzyme overrides global; absent/empty falls back to global)"
    - "Stateless EditRouter (RngEngine passed per route() call, mirrors StoryInterpreter precedent)"
    - "apply_player_edit reuses existing _enter + state.add_edit + molaction_sink (no new dispatch path)"

key-files:
  created:
    - c14/edit_router.py
    - tests/test_edit_router.py
    - tests/fixtures/edit_routing/edits.json
    - tests/fixtures/edit_routing/manifest.json
    - tests/fixtures/edit_routing/story.json
  modified:
    - c14/story/model.py
    - c14/engine.py

key-decisions:
  - "EditIntent is a NEW plain class separate from MolAction (routing input vs execution output; carries enzyme_id lookup key MolAction lacks)"
  - "Matching is EXACT dict equality on signature() -- no fuzzy/substring/similarity (smuggles in the out-of-scope chemistry engine)"
  - "Per-enzyme pool uses OVERRIDE semantics (not merge) -- simpler + deterministic"
  - "EditRouter is stateless across playthroughs (rng passed per route() call, mirroring StoryInterpreter)"
  - "apply_player_edit reuses existing _enter + add_edit + molaction_sink -- no new dispatch path; pure routing + entry only"
  - "edit_router=None default keeps the constructor backward-compatible (all Phase 2 tests stay green)"
  - "Only the GLOBAL pool emptiness is a validation error; absent/empty per-enzyme pools fall back to global (OVERRIDE semantics)"

patterns-established:
  - "Routing INPUT (EditIntent) vs execution OUTPUT (MolAction) directionality pattern"
  - "Exact-signature lookup table + bad-ending fallback routing pattern"
  - "RngEngine injected per call (not owned by the router) -- stateless domain service pattern"

# Metrics
duration: 12 min
completed: 2026-08-14
---

# Phase 4 Plan 2: Edit Routing Summary

**EditRouter with exact-signature lookup (known->branch) + RngEngine-weighted bad-ending pool (unknown->fallback) + GameEngine.apply_player_edit integration, proven headlessly with 17 pure-Python tests**

## Performance

- **Duration:** 12 min
- **Started:** 2026-08-14T18:52:29Z
- **Completed:** 2026-08-14T19:04:54Z
- **Tasks:** 3
- **Files modified:** 7 (2 modified + 5 created)

## Accomplishments
- EditIntent class added to c14/story/model.py (routing INPUT, separate from MolAction) with signature() normalization (target stripped+lowercased, args stringified via _norm_val); MolAction/Choice/Node unchanged
- c14/edit_router.py created: EditRoutingError + EditsTable (loader) + EditRouter (known->branch via exact dict equality, unknown->bad-ending pool via rng.weighted_pick) + validate_edits_table + scan_edit_coverage -- pure-Python, AST-gate-clean (no pymol/random)
- GameEngine.apply_player_edit added (SC3 entry point: route -> state.add_edit -> _enter), reusing existing _enter + molaction_sink; backward-compatible edit_router=None constructor param
- SC3 fixture bundle created (placeholder enzyme + 1 known edit + global bad_ending_pool + 4-node story graph)
- 17-test SC3 demo passes (known->branch, unknown->pool, RNG determinism, unknown enzyme -> global pool, empty pool raises, 5 validation checks, clean fixture, coverage scan, 5 GameEngine integration tests); full suite 157 tests green (zero regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: EditIntent + EditRouter routing subsystem** - `03489cf` (feat)
2. **Task 2: GameEngine.apply_player_edit + SC3 fixture bundle** - `ab80619` (feat)
3. **Task 3: SC3 test suite + per-enzyme pool validation fix** - `ff7a09f` (test)

## Files Created/Modified
- `c14/edit_router.py` - EditRoutingError + EditsTable + EditRouter + validate_edits_table + scan_edit_coverage (NEW, 251 lines)
- `c14/story/model.py` - Added EditIntent class + _norm_val helper (MolAction/Choice/Node unchanged)
- `c14/engine.py` - Added edit_router param + apply_player_edit method (start/choose/_enter/save/load unchanged)
- `tests/test_edit_router.py` - 17 SC3 tests (TestEditRouter + TestGameEngineEditIntegration, 270 lines)
- `tests/fixtures/edit_routing/edits.json` - Placeholder edits table (1 enzyme + 1 known edit + global pool)
- `tests/fixtures/edit_routing/manifest.json` - Minimal story graph manifest (start=edit.start)
- `tests/fixtures/edit_routing/story.json` - 4 nodes (start + good-branch + 2 bad-endings)

## Decisions Made
- **EditIntent is a separate type from MolAction:** MolAction is the execution carrier (engine->molops, ops edit/protonate/restore); EditIntent is the routing carrier (player->router) and carries the enzyme_id lookup key MolAction lacks. Conflating them couples routing to execution and breaks data-flow directionality.
- **Exact dict equality matching:** The signature is a CONTRACT -- the UI produces EditIntents whose signature() matches the table; the table author writes the identical canonical form; the router compares with ==. No fuzzy/substring/similarity (that smuggles in the out-of-scope chemistry engine). Dict equality is order-independent on 3.6.9 (verified).
- **Per-enzyme pool OVERRIDE semantics:** If a per-enzyme bad_ending_pool is present + non-empty, use it; else fall back to global. Not merge (merge would need de-duplication + ordering rules -- unnecessary complexity).
- **EditRouter is stateless:** Holds only the immutable EditsTable; the RngEngine is passed per route() call (mirrors StoryInterpreter). Save/load reproducibility follows from the engine's existing RNG-state sync.
- **apply_player_edit reuses existing machinery:** route() -> state.add_edit() -> _enter(). No new dispatch path; the routed node's on_enter MolActions flow through the existing molaction_sink. The edit APPLICATION (backup + alter + sort) is the apply_edit helper's job (04-01/04-05), NOT the EditRouter's.
- **Backward-compatible constructor widening:** edit_router=None default keeps every existing Phase 2 test green (start/choose/save/load unchanged).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed per-enzyme pool validation flagging absent pools as empty**
- **Found during:** Task 3 (running test_validate_edits_table_clean)
- **Issue:** The reference implementation's `validate_edits_table` called `_check_pool(e.get("bad_ending_pool", []), eid, ...)` for every enzyme, which flags an ABSENT per-enzyme pool (key not in the dict) as `empty_bad_ending_pool`. But an absent per-enzyme pool is valid -- it means "fall back to the global pool" (OVERRIDE semantics). This caused the clean fixture (placeholder_enzyme has no per-enzyme pool) to incorrectly report an issue.
- **Fix:** Changed the per-enzyme loop to only check non-empty per-enzyme pools (`if per_pool:`). Only the GLOBAL pool emptiness is an error (it's the ultimate fallback). Absent/empty per-enzyme pools fall back to global and are not flagged.
- **Files modified:** c14/edit_router.py
- **Verification:** test_validate_edits_table_clean now passes (fixture validates to []); all 5 validation tests still pass; full suite 157 tests green
- **Committed in:** ff7a09f (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The fix corrects the validation logic to match the OVERRIDE semantics documented in the research. No scope creep -- the fix makes the implementation match the design intent.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SC3 (edit routing) is PROVEN: EditRouter routes known edits to defined branches and unknown edits to the bad-ending pool, demonstrated headlessly with 17 pure-Python tests (NO PyMOL).
- The EditIntent contract (op/target/args/enzyme_id + signature() normalization) is defined; Phase 5.1 SC4 will specify which story nodes allow edits + what EditIntent each player-edit-action generates.
- The edits.json schema is established (version + global bad_ending_pool + per-enzyme edits with signature/branch_node/claim_id); Phase 5+ will populate it with real cited content (CITE-01 per-claim approval). The claim_id field exists in the schema (forward-compat) but holds "placeholder-..." values in Phase 4.
- scan_edit_coverage is ready for 04-04's check_edit_coverage.py tool to wrap.
- apply_player_edit integration is ready for 04-05's molops edit/restore/protonate delegation (the routed branch's on_enter MolAction("edit",...) will be dispatched to editops via molops).
- No blockers for subsequent Phase 4 plans (04-03 ProtonationManager, 04-04 check_alter_gate + check_edit_coverage, 04-05 molops delegation).

---
*Phase: 04-editing-protonation-restore-safety-net*
*Completed: 2026-08-14*
