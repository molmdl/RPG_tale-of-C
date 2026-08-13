---
phase: 02-story-engine-core
plan: 05
subsystem: testing
tags: [integration-test, end-to-end, determinism, save-load, reachability, demo, architecture-proof, testability-boundary, citation-gate]

# Dependency graph
requires:
  - phase: 02-01
    provides: Node/Choice/MolAction model + RngEngine (from_state/get_state/seed) + GameState (new_game/to_dict/record_visit/mark_finished)
  - phase: 02-02
    provides: StoryGraph (load/start_node/get_node/all_nodes) + StoryInterpreter (pick_choice/enter_node/apply_effects) + the minimal data/story graph (intro.start -> 2 weighted choices -> 2 endings)
  - phase: 02-03
    provides: check_reachability (ReachabilityReport.is_ok/reachable_endings/unreachable_endings) + validate_graph (Issue list) + collect_claim_ids (file OR directory) + the refactored citation gate CLI
  - phase: 02-04
    provides: SaveStore (save/load) + GameEngine (start/choose/save/load, per-action MolAction dispatch to sink, RNG-state sync + on_enter replay) + TurnResult
provides:
  - tests/test_integration.py -- 17 end-to-end tests proving all 4 Phase 2 success criteria in one place (full playthrough + RNG determinism + save/load round-trip + reachability green/red + citation gate on the multi-file story dir)
  - tools/demo_playthrough.py -- runnable, human-visible architecture-proof demo (plays the 2-node story in WSL, saves/loads, exits 0); the tangible Phase 2 proof artifact
  - The Phase 2 GOAL proven: the entire game architecture works end-to-end in pure Python with zero PyMOL/Qt import before any pymol_layer/ui code is written
affects: [Phase 3 (pymol_layer consumes MolActions the engine emits -- the demo sink is the future molops.apply(action) caller), Phase 5.1 (Story Graph Design -- can now start; depends on Phase 2 + the resolved ATP decision), Phase 6 (Qt controller owns the GameEngine; the demo's main() is the controller skeleton), /gsd-verify-phase 2 (Phase 2 is now ready for verification)]

# Tech tracking
tech-stack:
  added: []  # stdlib only (unittest, os, sys, tempfile, json, collections, subprocess, shutil) -- no new deps
  patterns:
    - "Full-stack pure-Python proof pattern: the integration test imports the entire domain stack (engine+graph+rng+state+persist+validate+model) at module top and asserts 'pymol' not in sys.modules and 'PyQt5' not in sys.modules after a full playthrough -- the testability boundary proven end-to-end, not just per-module"
    - "Mid-playthrough save/load determinism proof: save BEFORE the weighted choice (capturing rng_state after the start-node draws), then load+choose reaches the SAME ending as never saving -- the saved RNG position makes the two paths converge (the strongest save/load determinism test)"
    - "Runnable architecture-proof artifact: a small main() script that wires GameEngine+StoryGraph, prints the playthrough + MolAction emissions + save/load round-trip, and exits 0 -- the proof is human-visible and reproducible (fixed seed), not just a green test bar"

key-files:
  created:
    - tests/test_integration.py
    - tools/demo_playthrough.py
  modified: []  # pure additive capstone -- no source files changed

key-decisions:
  - "Adapted integration test + demo to the 02-04 per-action MolAction dispatch contract (sink receives individual MolAction objects via sink.append, NOT a list). The plan explicitly flagged this; confirmed by reading c14/engine.py line 153 (self.molaction_sink(action) per action). The integration test's test_playthrough_emits_molactions_to_mock_sink asserts len(sink)>=3 (hide_all+load at start, hide_all at ending) and the demo's sink(action) prints one MolAction per emission. Zero ambiguity."
  - "Used a raw dict {is_ending:'bad', choices:[]} via Node.from_dict for the orphaned-variant reachability test -- check_reachability's duck-typed _choices/_is_ending helpers (02-03) accept both Node objects and raw dicts, so the orphan is detected as an unreachable ending with no incoming edge. Node.from_dict requires an id field, so the orphan dict includes id:'intro.ending_orphan'."
  - "Imported the full domain stack (RngEngine, GameState, SaveStore, Node) at the test module top even though some are only used transitively via GameEngine -- this proves the ENTIRE stack imports in pure Python; the no-pymol/no-pyqt assertions then confirm none transitively pulled PyMOL/Qt. Marked with # noqa: F401 where not directly referenced."
  - "The citation-gate end-to-end test builds a temp registry with the toy story's 3 placeholder claim_ids (placeholder-intro, placeholder-good-ending, placeholder-bad-ending) all approved and runs the gate via subprocess (sys.executable, stdout/stderr=PIPE -- the 3.6 pattern, not capture_output) -- proves the refactored 02-03 walker works on the multi-file data/story directory, not just single-file fixtures."

patterns-established:
  - "Pattern: the integration test is the single source of truth for the Phase 2 architecture proof -- all 4 success criteria in one file, runnable with one command (python3.6 -m unittest tests.test_integration -v)"
  - "Pattern: the demo script is the human-visible proof twin of the integration test -- same stack, same flow, but prints the playthrough for a human to read; both must stay green as the architecture evolves"
  - "Pattern: subprocess tests use sys.executable (not a hardcoded interpreter) so the same python running the test runs the gate; stdout/stderr=PIPE + manual decode (3.6-safe, not capture_output/text)"

# Metrics
duration: 4min
completed: 2026-08-13
---

# Phase 2 Plan 05: End-to-End Integration Test + Runnable Demo Summary

**17-test integration suite + a runnable demo script proving all 4 Phase 2 success criteria end-to-end in pure Python (full playthrough + RNG determinism + save/load round-trip + reachability green/red) with zero PyMOL/Qt import -- the Phase 2 GOAL achieved**

## Performance

- **Duration:** 4 min
- **Started:** 2026-08-13T19:55:27Z
- **Completed:** 2026-08-13T19:59:43Z
- **Tasks:** 2
- **Files modified:** 2 created (no source files changed -- pure additive capstone)

## Accomplishments
- tests/test_integration.py: 17 end-to-end tests proving all 4 Phase 2 success criteria in one place, exercising the FULL stack (GameEngine + StoryInterpreter + StoryGraph + RngEngine + GameState + SaveStore + check_reachability + validate_graph) in pure Python with a mock MolAction sink
- Success criterion #1 PROVEN end-to-end: full playthrough (start -> weighted choice -> ending) with a mock MolAction sink; no pymol AND no PyQt5 in sys.modules after the full stack runs (the testability boundary holds across the entire architecture, not just per-module)
- Success criterion #2 PROVEN end-to-end: same seed -> same ending AND same MolAction sequence (op/target/args in order); seeds 0..30 reach both endings (16 bad / 15 good -- 50/50 robust); random-mode run replayable from its recorded seed (classroom reproducibility)
- Success criterion #3 PROVEN end-to-end: save/load restores identical GameState (all fields incl. rng_state); replays on_enter to reconstruct the scene; MID-playthrough save -> load -> continue reaches the SAME ending as never saving (the strongest determinism proof); no double-count visit; human-readable JSON (current_node/seed/rng_state present as text)
- Success criterion #4 PROVEN end-to-end: check_reachability green on data/story (both endings reachable, none unreachable) and red on a deliberately-orphaned variant (intro.ending_orphan flagged unreachable); validate_graph clean on the toy graph
- Cross-cutting: the refactored citation gate (02-03 walker in c14.story.validate.collect_claim_ids) works on the multi-file data/story directory end-to-end (subprocess exit 0 with the 3 placeholder claims approved)
- tools/demo_playthrough.py: the tangible architecture-proof artifact -- `python3.6 tools/demo_playthrough.py` plays the 2-node story, prints the dramatic text + weighted choices + each MolAction emission + the ending + game-state JSON + save/load round-trip + VERIFY OK, and exits 0. Deterministic (seed 42) so the output is reproducible
- 97 total tests pass (80 baseline + 17 new); AST gate clean; no pymol/PyQt5 import anywhere in c14/ -- the architecture is proven in WSL with zero PyMOL

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end integration test (architecture proof)** - `7dc36a8` (test)
2. **Task 2: Runnable architecture-proof demo script** - `1a1825f` (feat)

**Plan metadata:** (this commit) `docs(02-05): complete integration-test + demo plan`

## Files Created/Modified
- `tests/test_integration.py` - 17 tests in `TestEndToEndArchitecture`: helpers `_story_dir`/`_tmpfile`/`_play`; SC1 (full playthrough + mock sink + no pymol/pyqt); SC2 (same-seed same-ending + same MolAction sequence + diff-seed both endings + random-mode replay); SC3 (identical state + on_enter replay + mid-playthrough continue + no double visit + human-readable JSON); SC4 (reachability green on data/story + red on orphaned variant + validate_graph clean); cross-cutting citation-gate subprocess test on the multi-file story dir. Full domain stack imported at module top.
- `tools/demo_playthrough.py` - Runnable demo: sys.path insert of repo root (tools/ pattern); imports GameEngine + StoryGraph; `__file__`-relative STORY_DIR; fixed SEED=42; `sink(action)` prints each MolAction (per-action dispatch); main() prints banner -> start node (dramatic + teaching + weighted choices) -> choice made -> ending node + tier -> game-state JSON -> save -> load (replays on_enter) -> restored state -> VERIFY OK -> exit 0. Shebang `#!/usr/bin/env python3.6`.

## Decisions Made
- Adapted the integration test + demo to the 02-04 per-action MolAction dispatch contract (the plan explicitly flagged it). Confirmed by reading c14/engine.py: `self.molaction_sink(action)` per action (line 153). The integration test uses `sink.append` (collects individual MolAction objects; len>=3 after start+choose); the demo's `sink(action)` prints one MolAction per emission. See key-decisions.
- Built the orphaned-variant reachability test with `Node.from_dict({id, is_ending:'bad', choices:[]})` on a copy of `g.all_nodes()` -- the duck-typed check_reachability helpers accept Node objects; the orphan has no incoming edge so it is flagged unreachable. See key-decisions.
- Imported the full domain stack at the test module top (incl. transitively-used RngEngine/GameState/SaveStore/Node with `# noqa: F401`) to prove the entire stack imports in pure Python; the no-pymol/no-pyqt assertions confirm none transitively pulled PyMOL/Qt. See key-decisions.
- The citation-gate end-to-end test uses a temp registry (NamedTemporaryFile, delete=False) with the 3 placeholder claims approved + subprocess (sys.executable, stdout/stderr=PIPE) -- the 3.6-safe pattern from test_citations.py. See key-decisions.

## Deviations from Plan

None - plan executed exactly as written.

The plan explicitly flagged the 02-04 per-action MolAction dispatch contract and instructed adapting the integration test + demo to it; I confirmed the contract by reading c14/engine.py and implemented the assertions accordingly (len(sink)>=3 for individual MolAction objects; sink(action) printing one action per emission). No bugs, no missing critical functionality, no blocking issues, no architectural changes. The orphaned-variant test used `Node.from_dict` (the plan offered "Node.from_dict({...}) or a raw dict"); either works because check_reachability duck-types, and Node.from_dict was chosen to exercise the model import.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. Pure-Python, stdlib only.

## Next Phase Readiness
- **Phase 2 is COMPLETE.** All 4 success criteria proven end-to-end: (1) full playthrough with mock sink + no pymol/pyqt; (2) RNG determinism (same seed = same ending + same MolAction sequence; diff seeds = both endings; random-mode replayable); (3) save/load restores identical state + replays on_enter + mid-playthrough continue reaches same ending; (4) reachability green/red + validate_graph clean. The refactored citation gate works on the multi-file story directory.
- The runnable demo (`python3.6 tools/demo_playthrough.py`) is the tangible proof -- it plays the story, saves/loads, and exits 0. Phase 2 is ready for `/gsd-verify-phase 2`.
- 97 tests pass; AST gate clean; no pymol/PyQt5 imports anywhere in c14/. The architecture is proven in WSL with zero PyMOL -- the de-risk goal achieved.
- Phase 3 (PyMOL cmd Layer) can start -- the MolAction model the engine emits is the contract `c14/pymol_layer/molops.py` will consume (one MolAction per call -- the demo's `sink(action)` is the future `molops.apply(action)` caller).
- Phase 5.1 (Story Graph Design) can start -- it depended on Phase 2 + the now-RESOLVED ATP/True-Ending decision (soul-jump reframing).
- Blockers/concerns: None for Phase 2. The Phase 5 science-framing Key Decisions (C14-decay timescale, anaerobic framing, batch-vs-per-claim approval) remain the timeline-dominating risk for content authoring (Phases 7-9) -- flagged in STATE.md, not blocking Phase 2/3 engineering.

---
*Phase: 02-story-engine-core*
*Completed: 2026-08-13*
