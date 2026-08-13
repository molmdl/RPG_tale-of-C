---
phase: 02-story-engine-core
plan: 03
subsystem: story-engine
tags: [validation, reachability, bfs, graph-algorithm, citation-gate, pure-python, python3.6, backward-compat, surgical-refactor]

# Dependency graph
requires:
  - phase: 01-foundations-testability-citation-gate (01-03)
    provides: CitationRegistry + the pre-ship citation gate (tools/check_citations.py) with its inline story-walker isolated in one function; the forward-compatible contract (Phase 2 swaps the walker with zero changes to the gate's core logic); three-way exit codes (0/1/2)
  - phase: 02-story-engine-core (02-01)
    provides: Node/Choice/MolAction plain classes (c14.story.model) — the graph shape check_reachability/validate_graph traverse via duck-typed helpers; 3.6-compat plain-class precedent
provides:
  - "c14.story.validate.check_reachability: pure BFS reachability checker (green on well-formed, red on orphaned ending) — establishes the 'all endings reachable' invariant (Pitfall 8), Phase 2 success criterion #4"
  - "c14.story.validate.validate_graph: structural validator detecting dangling diverts (choice.goto -> nonexistent node)"
  - "c14.story.validate.collect_claim_ids: file-OR-directory claim collector — the Phase 2 home of the gate's story-walker (forward-compatible with Phase 1's inline walker)"
  - "c14.story.validate.ReachabilityReport + Issue: plain result classes (is_ok property, __repr__)"
  - "Refactored tools/check_citations.py: imports c14.story.validate.collect_claim_ids; --story accepts file OR directory; gate core logic + 0/1/2 exit codes UNCHANGED"
  - "14 new unit tests (tests/test_validate.py) — total suite now 65 tests, all passing"
affects: [02-05 (StoryGraph integration — g.all_nodes() returns the {id: node} dict check_reachability/validate_graph accept), 06-mvp (citation gate runs on data/story/ directory at pre-ship), content phases 7-9 (gate enforces no-fabricated-science on authored claim_ids)]

# Tech tracking
tech-stack:
  added: []  # stdlib only — json, os, collections (no new dependencies)
  patterns:
    - "Duck-typed graph-algorithm helpers (_choices/_goto/_is_ending) that work on both Node objects (node.choices/.goto/.is_ending) and raw JSON dicts (node.get('choices')/['goto']/['is_ending']) — single code path, no duplication"
    - "File-or-directory loader pattern: collect_claim_ids detects os.path.isdir and dispatches to directory (manifest.json + merge files) vs single-file mode — backward-compatible"
    - "Surgical gate refactor: swap one function (the walker) for an import, keep all core logic + exit-code semantics unchanged — the Phase 1 forward-compatible contract honored"
    - "Partial git commit (git commit -- <pathspec>) to isolate a plan's files from a parallel plan's staged work — no cross-plan contamination during parallel execution"
    - "Separation of concerns: check_reachability skips edges to nonexistent nodes (graceful reachability); validate_graph flags them as dangling_diverts (structural validation)"

key-files:
  created:
    - "c14/story/validate.py — check_reachability (BFS), validate_graph (dangling diverts), collect_claim_ids (file-or-directory), ReachabilityReport + Issue plain classes, duck-typed _choices/_goto/_is_ending helpers (323 lines, stdlib only)"
    - "tests/test_validate.py — 14 unit tests: reachability green/red/multi-hop/missing-start/is_ok-property; validate_graph dangling-divert/clean/none-goto; collect_claim_ids file/no-claim-key/directory/multi-file/bad-schema/nonexistent"
  modified:
    - "tools/check_citations.py — refactored: inline collect_referenced_claim_ids removed -> c14.story.validate.collect_claim_ids import; --story accepts file OR directory; dead 'import json' removed; gate core logic + 0/1/2 exit codes + report format UNCHANGED (-39/+12 lines)"

key-decisions:
  - "Duck-typed _choices/_goto/_is_ending helpers make check_reachability/validate_graph work on both Node objects (from graph.py) and raw JSON dicts (from collect_claim_ids fixtures) via hasattr() — single algorithm code path, no duplication"
  - "collect_claim_ids does its OWN minimal file loading (does NOT import c14.story.graph) to keep Plan 03 independent of Plan 02 for parallel execution — the minor manifest-reading overlap with graph.py is an acceptable trade for module independence"
  - "check_reachability skips edges to nonexistent nodes (graceful — can't reach what doesn't exist); validate_graph flags them as dangling_diverts — clean separation of concerns between reachability and structural validation"
  - "check_reachability on a missing start_id returns is_ok=False with all endings unreachable (graceful, not a crash) — lets the checker report the problem"
  - "Partial git commit (git commit -- <pathspec>) used to isolate Task 1/2 files from the parallel Plan 02-02 agent's staged work — no cross-plan file contamination"

patterns-established:
  - "Duck-typed graph-algorithm helpers: _choices/_goto/_is_ending duck-type Node objects vs raw dicts so the same BFS/validator works on both the loader's Node objects and the gate's raw JSON fixtures"
  - "File-or-directory loader: os.path.isdir dispatch to manifest+merge vs single-file json.load — backward-compatible with Phase 1 single-file fixtures while supporting the new multi-file bundle"
  - "Surgical gate refactor: replace one function (the walker) with an import, preserve all exit codes + report format — the Phase 1 forward-compatible contract (isolated walker, unchanged core) honored with zero regression"

# Metrics
duration: 7 min
completed: 2026-08-13
---

# Phase 2 Plan 03: Graph Validator + Reachability Checker + Citation Gate Refactor Summary

**Pure-Python BFS reachability checker (green/red on well-formed/orphaned graphs) + dangling-divert validator + citation gate refactored to share one story-walker — 14 new tests, 12 existing tests backward-compatible, success criterion #4 proven**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-08-13T18:38:36Z
- **Completed:** 2026-08-13T18:45:25Z
- **Tasks:** 2
- **Files modified:** 3 (2 created, 1 refactored)

## Accomplishments

- `check_reachability` (pure BFS over `choice.goto` edges) establishes the "all endings reachable" invariant (Pitfall 8) — green on a well-formed graph, red on one with an orphaned ending. **Phase 2 success criterion #4 proven**: a reachability checker (pure Python) runs on the toy graph and reports which endings are reachable.
- `validate_graph` detects dangling diverts (a `choice.goto` pointing to a nonexistent node id) — the Pitfall 8 companion check.
- `collect_claim_ids` accepts a single `.json` file (backward-compatible with Phase 1 fixtures) OR a directory (reads `manifest.json` + merges listed files) — the Phase 2 home of the gate's story-walker.
- Citation gate **surgically refactored**: inline `collect_referenced_claim_ids` replaced by `c14.story.validate.collect_claim_ids`; gate core logic (registry cross-ref, `[MISSING]`/`[UNAPPROVED]` report, 0/1/2 exit codes) **UNCHANGED**; `--story` now accepts a file or directory. **All 12 existing citation tests still pass — zero regression** (the Phase 1 forward-compatible contract honored).
- Module independent of `c14.story.graph` (no import) — Plan 03 ran in parallel with Plan 02; the duck-typed helpers mean the same algorithms work on Plan 02's `Node` objects once integrated.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create c14/story/validate.py + tests/test_validate.py** — `6992ff5` (feat)
2. **Task 2: Refactor tools/check_citations.py to use c14.story.validate.collect_claim_ids** — `695e9e7` (refactor)

## Files Created/Modified

- `c14/story/validate.py` — `check_reachability(nodes, start_id) -> ReachabilityReport` (BFS, is_ok property); `validate_graph(nodes) -> list[Issue]` (dangling divert detection); `collect_claim_ids(story_path) -> dict` (file-or-directory); `ReachabilityReport` + `Issue` plain classes; duck-typed `_choices`/`_goto`/`_is_ending` helpers (work on Node objects OR raw dicts). Stdlib only: `json`, `os`, `collections`.
- `tests/test_validate.py` — 14 unit tests with inline raw-dict fixtures + tempdir-based file/directory fixtures. Covers reachability green/red/multi-hop/missing-start, validate_graph dangling-divert/clean/none-goto, collect_claim_ids file/no-claim-key/directory/multi-file/bad-schema/nonexistent.
- `tools/check_citations.py` — refactored: inline `collect_referenced_claim_ids` removed; `from c14.story.validate import collect_claim_ids` added; `--story` help updated to "Path to story JSON file OR story directory (with manifest.json)"; dead `import json` removed; gate core logic + exit codes + report format unchanged.

## Decisions Made

- **Duck-typed helpers** (`_choices`/`_goto`/`_is_ending`) use `hasattr()` to distinguish `Node` objects (`.choices`/`.goto`/`.is_ending` attributes) from raw dicts (`.get('choices')`/`['goto']`/`['is_ending']`). Single algorithm code path serves both the loader's `Node` objects and the gate's raw JSON fixtures — no duplication.
- **`collect_claim_ids` does its own file loading** (no `c14.story.graph` import) — keeps Plan 03 independent of Plan 02 for parallel execution. The minor manifest-reading overlap with `graph.py` is an acceptable trade for module independence + parallel execution.
- **Separation of concerns**: `check_reachability` skips edges to nonexistent nodes (graceful — can't reach what doesn't exist); `validate_graph` flags them as `dangling_divert` (structural). The reachability checker reports reach; the validator reports structure.
- **Missing-start graceful edge case**: `check_reachability` on a `start_id` not in `nodes` returns `is_ok=False` with all endings unreachable (no crash) — lets the checker report the problem.
- **Partial git commit** (`git commit -- <pathspec>`) isolated this plan's files from the parallel Plan 02-02 agent's staged work — no cross-plan file contamination.

## Deviations from Plan

### Notes (no rule triggered — within plan spirit)

**1. Extra edge-case tests beyond the 10 specified**
- **Found during:** Task 1 (test file creation)
- **Issue:** The plan's done criteria mentions "tests/test_validate.py passes (10 tests)"; I wrote 14 — 4 extra edge-case tests: `test_reachability_report_is_ok_property` (is_ok property contract), `test_validate_graph_none_goto_ok` (goto=None leaf is not a dangling divert), `test_collect_claim_ids_file_no_claim_ids_key` (narrative node with no claim_ids), `test_collect_claim_ids_directory_multi_file` (multi-file manifest merge).
- **Fix:** None needed — all 14 pass; strictly stronger coverage. The 10 specified tests are a subset.
- **Files modified:** tests/test_validate.py
- **Committed in:** 6992ff5 (Task 1 commit)

**2. Removed now-dead `import json` from tools/check_citations.py**
- **Found during:** Task 2 (surgical refactor)
- **Issue:** After removing the inline `collect_referenced_claim_ids` (which was the only user of `json.load`), `import json` became a dead import.
- **Fix:** Removed `import json` (clean-code completion of the surgical refactor — the function that used it was removed, so the import goes with it). No behavior change.
- **Files modified:** tools/check_citations.py
- **Committed in:** 695e9e7 (Task 2 commit)

---

**Total deviations:** 2 minor notes (0 rule-triggered auto-fixes; both are within-spirit cleanups: extra test coverage + dead-import removal). **Impact on plan:** None — strictly improves coverage and cleanliness. No scope creep.

## Issues Encountered

None. The surgical refactor preserved all 12 existing citation tests on the first run; the parallel Plan 02-02 agent's staged files were cleanly isolated via partial-commit pathspec. Directory mode was verified live on Plan 02-02's `data/story/` bundle (intro.json) — the gate correctly reported the bundle's placeholder claim_ids as missing (exit 1) against the test fixture registry.

## User Setup Required

None — no external service configuration required. Pure-Python stdlib module + a refactored in-repo gate script.

## Next Phase Readiness

- `check_reachability` / `validate_graph` accept the `{id: node}` dict that Plan 02-05's `StoryGraph.all_nodes()` returns — ready for integration (pinned to the dict, not a list, per the plan spec).
- `collect_claim_ids` directory mode verified on Plan 02-02's `data/story/` bundle — the gate can run on the real story directory at pre-ship (content phases 7-9).
- The citation-gate forward-compatible contract is fully honored — the gate and the validator now share one story-walker (`collect_claim_ids`), eliminating duplicated traversal logic.
- No blockers. Plan 03 is independent of Plan 02 (no `c14.story.graph` import) but compatible with it (duck-typed helpers work on `Node` objects).

---
*Phase: 02-story-engine-core*
*Completed: 2026-08-13*
