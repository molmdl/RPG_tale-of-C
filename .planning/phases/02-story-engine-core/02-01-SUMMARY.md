---
phase: 02-story-engine-core
plan: 01
subsystem: testing
tags: [python, stdlib, random, json, data-model, rng, save-load]

# Dependency graph
requires:
  - phase: 01-foundations-testability-citation-gate
    provides: AST import gate (tools/check_imports.py) enforcing the pure-Python testability boundary; CitationRegistry plain-class precedent; 3.6-compat conventions (no @dataclass, no walrus, .format())
provides:
  - "c14.story.model: Node/Choice/MolAction plain classes with from_dict/to_dict — the story data model + the MolAction testability-boundary carrier (pure data, no pymol import)"
  - "c14.rng.RngEngine: seedable PRNG (single random.Random per playthrough) with JSON-serializable state — Anti-Pattern 7 mitigation"
  - "c14.state.GameState: saveable per-playthrough state with full JSON round-trip incl. seed + rng_state"
  - "20 new unit tests (7 model + 6 rng + 7 state) — total suite now 39 tests, all passing"
affects: [02-02 (loader), 02-03 (interpreter), 02-04 (engine), 02-05 (validator/persist), Phase 3 (MolOps consumes MolAction), Phase 4 (edit routing), Phase 6 (engine+save/load in Qt UI)]

# Tech tracking
tech-stack:
  added: []  # stdlib only — no new dependencies (random, secrets, datetime, json, typing)
  patterns:
    - "Plain classes (NOT @dataclass) for 3.6 compatibility — matches CitationRegistry precedent"
    - "MolAction as pure-data domain->pymol_layer carrier (testability boundary, ARCHITECTURE.md Pattern 1)"
    - "Single seeded RngEngine per playthrough; all stochastic draws go through it (Anti-Pattern 7)"
    - "JSON-serializable PRNG state (tuples<->lists) so save/load restores the exact next draw"
    - "GameState stores seed + rng_state as plain data; engine syncs/rebuilds RngEngine around them"

key-files:
  created:
    - "c14/story/__init__.py — story subpackage marker (pure-Python, no pymol/PyQt5)"
    - "c14/story/model.py — Node, Choice, MolAction plain classes with from_dict/to_dict/__eq__/__repr__"
    - "c14/rng.py — RngEngine plain class wrapping random.Random(seed)"
    - "c14/state.py — GameState plain class with to_dict/from_dict JSON round-trip"
    - "tests/test_model.py — 7 unit tests for Node/Choice/MolAction"
    - "tests/test_rng.py — 6 unit tests for RngEngine determinism + state round-trip"
    - "tests/test_state.py — 7 unit tests for GameState round-trip + helpers"
  modified: []

key-decisions:
  - "Plain classes (not @dataclass) for Node/Choice/MolAction/RngEngine/GameState — 3.6.9 has no dataclasses module (Phase 1 Pitfall 1, verified); matches CitationRegistry precedent"
  - "MolAction carries op/target/args as pure data with NO pymol import — the testability-boundary carrier; the future c14/pymol_layer/molops.py translates it to cmd.* (Phase 4)"
  - "RngEngine random-mode uses secrets.randbits(31) for a non-deterministic seed that is recorded on .seed for replay (3.6-safe; secrets module is stdlib)"
  - "RngEngine.get_state converts the random.Random state tuple to JSON lists; set_state/from_state converts back — verified the exact next draw survives JSON round-trip on 3.6.9"
  - "GameState.finished uses True (truthy) when an ending is reached, None while playing — matches the ARCHITECTURE.md JSON shape (\"finished\": null while playing)"
  - "GameState.to_dict key order is fixed to match the ARCHITECTURE.md GameState JSON for human-readable, diff-stable saves"

patterns-established:
  - "Pattern: from_dict/to_dict round-trip on every data class — the loader (02-02) and validator (02-05) rely on this contract"
  - "Pattern: None->empty-default for list/dict fields in constructors AND from_dict (graceful partial-save tolerance)"
  - "Pattern: __eq__ compares to_dict() for composite classes (Node, GameState) — robust against field-order drift"
  - "Pattern: # type: comments for 3.6-safe type hints (no runtime PEP 604 | syntax, no 3.7+ from __future__ import annotations)"

# Metrics
duration: 4 min
completed: 2026-08-13
---

# Phase 2 Plan 1: Foundation Modules (Model, RNG, State) Summary

**Three pure-Python stdlib-only foundation modules — story data model (Node/Choice/MolAction), seedable RngEngine, and saveable GameState — with JSON-serializable RNG state for replay, all 3.6-safe plain classes with 20 new unit tests**

## Performance

- **Duration:** 4 min
- **Started:** 2026-08-13T18:27:33Z
- **Completed:** 2026-08-13T18:32:14Z
- **Tasks:** 3
- **Files modified:** 7 (all new)

## Accomplishments
- Created the story data model: Node/Choice/MolAction as plain classes (not @dataclass, 3.6-safe) with from_dict/to_dict round-trip; MolAction is the pure-data testability-boundary carrier (no pymol import) that the future pymol_layer translates to cmd.*
- Created RngEngine: a single seeded PRNG per playthrough (Anti-Pattern 7 mitigation) with fixed-seed (demo) and random-seed (play) modes, plus JSON-serializable state that restores the exact next draw on save/load
- Created GameState: the saveable unit with full JSON round-trip including seed + rng_state, a new_game() convenience constructor, and flag/counter/visit/edit/finish helpers for the interpreter
- All three modules import cleanly in WSL with zero pymol/PyQt5 imports (AST gate green); 39 total tests pass (19 Phase 1 + 20 new)

## Task Commits

Each task was committed atomically:

1. **Task 1: Story data model (Node, Choice, MolAction)** — `00f1149` (feat)
2. **Task 2: Seedable RngEngine (Anti-Pattern 7 mitigation)** — `d1fa650` (feat)
3. **Task 3: Saveable GameState with JSON round-trip incl. rng_state** — `a7881b2` (feat)

**Plan metadata:** (pending — see final commit below)

## Files Created/Modified
- `c14/story/__init__.py` — story subpackage marker (pure-Python, no pymol/PyQt5; module roadmap in docstring)
- `c14/story/model.py` — Node/Choice/MolAction plain classes; MolAction is the domain->pymol_layer carrier; Node.from_dict parses nested choices/on_enter
- `c14/rng.py` — RngEngine wrapping random.Random(seed); fixed/random modes; get_state/set_state/from_state JSON round-trip
- `c14/state.py` — GameState with to_dict/from_dict JSON round-trip incl. rng_state; new_game(); flag/incr/record_visit/add_edit/mark_finished helpers
- `tests/test_model.py` — 7 tests (round-trip, defaults, nested parse, ending property, full Node round-trip)
- `tests/test_rng.py` — 6 tests (same-seed determinism, diff-seed, random-mode records seed, fixed-mode reproducible, JSON state round-trip, weighted-pick determinism)
- `tests/test_state.py` — 7 tests (defaults, key set, full round-trip, human-readable JSON, new_game, helpers, from_dict tolerance)

## Decisions Made
- Used plain classes (not @dataclass) throughout — 3.6.9 has no dataclasses module (Phase 1 Pitfall 1); matches the CitationRegistry precedent and the plan's explicit override of ARCHITECTURE.md's @dataclass reference.
- RngEngine random-mode picks the seed via `secrets.randbits(31)` (3.6-safe stdlib) rather than os.urandom-derived int — `secrets` is the canonical stdlib choice for non-deterministic values and gives a comfortable positive int for random.Random.
- GameState.mark_finished sets `finished=True` (truthy bool) rather than an ISO timestamp — matches the ARCHITECTURE.md JSON shape (`"finished": null` while playing) and keeps the field a clean bool/null; `started_at` is the timestamp of record.
- GameState.__eq__ compares `to_dict()` equality (not attribute-by-attribute) — robust against field-order drift and the simplest correct definition for a composite data class.
- Added `__hash__` to MolAction (op+target tuple) so MolAction instances are usable as dict keys / set members if the engine ever needs to dedupe queued actions; Choice/Node are unhashable (their __eq__ makes them unhashable by default, which is fine — they're not used as keys).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. Stdlib only; no new dependencies.

## Next Phase Readiness
- Wave 1 foundation complete: model (Node/Choice/MolAction), rng (RngEngine), and state (GameState) are in place and import-clean. Plans 02-02 (loader), 02-03 (interpreter), 02-04 (engine), and 02-05 (validator/persist) build directly on these.
- The MolAction pure-data contract is established — Phase 3's c14/pymol_layer/molops.py will translate MolAction.op/target/args to cmd.* calls.
- The RngEngine JSON-state contract is established — Phase 2's persist (02-05) and the engine's save/load will sync rng.get_state() into GameState.rng_state and rebuild via RngEngine.from_state(seed, rng_state).
- The GameState field set (incl. rng_state) is the save-format contract — forward-compatible via from_dict's .get defaults.
- No blockers. Ready for 02-02-PLAN.md (story graph loader).

---
*Phase: 02-story-engine-core*
*Completed: 2026-08-13*
