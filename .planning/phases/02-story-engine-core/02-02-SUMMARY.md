---
phase: 02-story-engine-core
plan: 02
subsystem: story-engine
tags: [python, stdlib, json, story-graph, interpreter, rng, ink, testability-boundary]

# Dependency graph
requires:
  - phase: 01-foundations-testability-citation-gate
    provides: AST import gate (tools/check_imports.py) enforcing the pure-Python testability boundary; CitationRegistry plain-class precedent; 3.6-compat conventions (no @dataclass, no walrus, .format())
  - phase: 02-01
    provides: Node/Choice/MolAction (model.py) with from_dict/to_dict; RngEngine.random() seedable single-PRNG; GameState (record_visit/mark_finished/set_flag/incr/flags/character/counters/visit_counts) — the data model + state the loader parses and the interpreter walks
provides:
  - "c14.story.graph.StoryGraph: load(story_dir) reads manifest.json + merges per-file node fragments into one {id: Node} dict via Node.from_dict (injects the JSON key as the node id); get_node/all_nodes(dict)/start_node/endings"
  - "c14.story.interpreter.StoryInterpreter: pick_choice (weighted -> single Choice via rng.random()*total + cumulative sum; non-weighted -> eligible list), enter_node (emits on_enter MolAction list, records visit, detects ending), _cond (restricted-namespace safe eval, fail-safe False), apply_effects (set/incr)"
  - "data/story/manifest.json + data/story/intro.json: minimal 2-node story bundle (intro.start -> 2 weighted choices -> intro.ending_good/ending_bad); placeholder content; {nodes: {id: {claim_ids}}} shape preserved for the citation gate"
  - "tests/test_interpreter.py: 12 unit tests proving Phase 2 success criterion #1 (full walk in pure Python with a mock MolAction sink, zero pymol import) + RNG determinism through the walk"
affects: [02-04 (engine wires graph+interpreter+state+rng into the walk loop), 02-05 (persist save/load round-trips a walked GameState), Phase 3 (MolOps consumes the emitted MolAction lists), Phase 5.1 (story graph design uses this walker/shape), Phase 6 (Qt UI controller dispatches MolActions to pymol_layer)]

# Tech tracking
tech-stack:
  added: []  # stdlib only — no new dependencies (json, os; eval for the cond sandbox)
  patterns:
    - "Ink-inspired story walker (ARCHITECTURE.md Pattern 2) adopted near-verbatim — JSON graph we own, ~200-line pure-Python interpreter, no ink runtime dep"
    - "MolAction-as-pure-data emission: enter_node returns node.on_enter (list[MolAction]); NEVER cmd.* — the testability boundary; the caller/controller dispatches to pymol_layer"
    - "Dependency-injected RngEngine: pick_choice draws via the single passed-in rng (Anti-Pattern 7 — never ad-hoc random.random()); interpreter is stateless across calls"
    - "Restricted-namespace _cond eval: {flags, char, counters, visits} with no builtins; trusted-content security model; fail-safe False on any exception"
    - "Loader injects JSON key as node id: keeps the {nodes: {id: {claim_ids}}} shape (citation-gate forward-compat) while satisfying Node.from_dict's required id field"

key-files:
  created:
    - "c14/story/graph.py — StoryGraph plain class: load(story_dir) manifest+merge loader; get_node/all_nodes/start_node/endings + __len__/__contains__/__repr__"
    - "c14/story/interpreter.py — StoryInterpreter plain class: pick_choice/enter_node/_cond/apply_effects (ARCHITECTURE.md Pattern 2 near-verbatim)"
    - "data/story/manifest.json — story bundle index (version, default_seed, start, files)"
    - "data/story/intro.json — minimal 3-node story (intro.start + 2 weighted choices + 2 endings); placeholder claim_ids; citation-gate shape preserved"
    - "tests/test_interpreter.py — 12 unit tests (2 graph + 10 interpreter incl. full-walk + no-pymol + cond + apply_effects)"
  modified: []

key-decisions:
  - "Loader injects the JSON object key as the node's `id` field before Node.from_dict (Node.from_dict requires d['id']); this keeps the {nodes: {id: {claim_ids}}} shape the Phase 1 citation gate story-walker reads, without duplicating the id inside each node body"
  - "_cond uses a 4-key restricted namespace {flags, char, counters, visits} with __builtins__ emptied; story content is trusted (bundled, team-authored, not user input) so eval is bounded to reading state fields; any exception -> fail-safe False (a malformed condition silently hides its choice, never crashes the game)"
  - "pick_choice returns a single Choice when all eligible choices are weighted (RNG decides) and the eligible list when non-weighted (caller/player picks by index) — matches ARCHITECTURE.md Pattern 2 near-verbatim, with a total==0 guard added (fall through to eligible instead of returning None)"
  - "enter_node returns node.on_enter as a pure-data MolAction list and NEVER calls cmd.* — the testability boundary; the future controller (Phase 2 engine / Phase 6 Qt UI) is the only thing that translates MolActions to cmd.* via c14/pymol_layer/molops.py"
  - "The minimal story (intro.json) is explicitly placeholder content (placeholder-* claim_ids, placeholder:structure asset key) — no real science, respecting the CITE-01 gate; the mock MolAction sink in tests just collects emitted actions (no real load happens in Phase 2)"
  - "StoryInterpreter is stateless across calls — GameState and RngEngine are dependency-injected per call so a single instance serves any playthrough and the state/engine remain the saveable/replayable units"

patterns-established:
  - "Pattern: StoryGraph.load(story_dir) is CWD-independent (explicit story_dir arg) — the engine/tests pass the path; testable with any directory, no c14.paths coupling in the loader"
  - "Pattern: all_nodes() returns the {id: Node} dict (NOT a list of values) — that dict shape is the contract consumed by Plan 03's check_reachability/validate_graph and Plan 05's tests"
  - "Pattern: the interpreter emits MolAction lists; tests use a plain list as the mock sink (sink.extend(si.enter_node(...))) — proving the domain tier needs no pymol"
  - "Pattern: weighted-choice determinism via rng.random()*total + cumulative sum (not random.choices) — keeps the draw on the single injected RngEngine (Anti-Pattern 7)"

# Metrics
duration: 14 min
completed: 2026-08-13
---

# Phase 2 Plan 2: Story Graph Loader + Interpreter Summary

**StoryGraph manifest+merge loader and StoryInterpreter walker (ARCHITECTURE.md Pattern 2, near-verbatim) — weighted RNG pick, pure-data MolAction emission, visit recording, ending detection — proving a full intro→choice→ending walk in pure Python with a mock MolAction sink and zero pymol import**

## Performance

- **Duration:** 14 min
- **Started:** 2026-08-13T18:37:58Z
- **Completed:** 2026-08-13T18:52:07Z
- **Tasks:** 2
- **Files modified:** 5 (all new)

## Accomplishments
- Created the story-bundle loader: `StoryGraph.load(story_dir)` reads `manifest.json` (version/default_seed/start/files) and merges every listed file's `nodes` dict into one `{id: Node}` mapping via `Node.from_dict` (injecting the JSON key as the node id; raising `ValueError` on duplicate node ids). Plus `get_node` / `all_nodes` (dict shape) / `start_node` / `endings` + dunder helpers.
- Created the story interpreter: `StoryInterpreter` (ARCHITECTURE.md Pattern 2, near-verbatim) with `pick_choice` (weighted → single Choice via `rng.random()*total` + cumulative sum; non-weighted → eligible list), `enter_node` (emits `on_enter` MolAction list, records visit, detects ending), `_cond` (restricted-namespace safe eval, fail-safe False), and `apply_effects` (set/incr).
- Created the minimal 2-node story fixture: `data/story/manifest.json` + `data/story/intro.json` (intro.start with 2 weighted "Proceed (luck decides)" choices → intro.ending_good / intro.ending_bad). Placeholder content throughout (placeholder-* claim_ids, placeholder:structure asset); the `{nodes: {id: {claim_ids}}}` shape preserved for forward-compat with the Phase 1 citation gate story-walker.
- Proved Phase 2 success criterion #1: a full walk (load → enter start → weighted pick → advance → enter ending) runs in pure Python with a mock MolAction sink and ZERO pymol import (`'pymol' not in sys.modules` asserted). RNG determinism through the walk verified (same seed → same ending; different seeds diverge).
- 12 new interpreter tests pass; total suite now 65 tests, all passing; AST gate green (no pymol/PyQt5 imports in the new domain-tier files).

## Task Commits

Each task was committed atomically:

1. **Task 1: StoryGraph loader + minimal 2-node story bundle** — `273165a` (feat)
2. **Task 2: StoryInterpreter + interpreter walk tests** — `25d7fee` (feat)

**Plan metadata:** (pending — see final commit below)

## Files Created/Modified
- `c14/story/graph.py` — `StoryGraph` plain class: `load(story_dir)` manifest+merge loader (injects JSON key as node id; ValueError on dup ids); `get_node`/`all_nodes` (dict)/`start_node`/`endings` + `__len__`/`__contains__`/`__repr__`. Pure-Python stdlib (json, os).
- `c14/story/interpreter.py` — `StoryInterpreter` plain class (ARCHITECTURE.md Pattern 2 near-verbatim): `pick_choice` (weighted RNG single / non-weighted list), `enter_node` (MolAction list + visit + ending), `_cond` (restricted-namespace eval, fail-safe False), `apply_effects` (set/incr). No pymol, no `random` import (rng injected).
- `data/story/manifest.json` — bundle index: version 1, default_seed 0, start "intro.start", files ["intro.json"].
- `data/story/intro.json` — minimal 3-node story (intro.start + 2 weighted choices + ending_good + ending_bad); placeholder claim_ids; `{nodes: {id: {claim_ids}}}` shape preserved.
- `tests/test_interpreter.py` — 12 unit tests: graph load + missing-raises; weighted pick returns single; RNG determinism; diff-seed divergence; MolAction emission; visit recording; ending detection; full walk reaches ending; no pymol import; condition evaluator; apply_effects. CWD-independent (story dir resolved via `__file__`).

## Decisions Made
- The loader injects the JSON object key as the node's `id` field before `Node.from_dict` (which requires `d["id"]`). This keeps the `{nodes: {id: {claim_ids}}}` shape that the Phase 1 citation gate story-walker reads, without duplicating the id inside each node body — verified forward-compatible by reading intro.json with the walker's exact contract.
- `_cond` evaluates conditions against a restricted namespace `{flags, char, counters, visits}` with `__builtins__` emptied. Story content is trusted (bundled, team-authored JSON, not user input), so `eval` is bounded to reading those four state fields; `flags.get('seen_tca', False)` and `char == 'glucose'` both work (dict `.get` is a method on the passed-in object, not a builtin). Any exception → fail-safe False (a malformed condition never crashes the game). The architecture's bare-name `not seen_tca` example would need flags merged into the namespace; per the plan's explicit 4-key namespace spec this isn't supported (and isn't tested) — the tested form is `flags.get(...)`.
- `pick_choice` returns a single `Choice` when all eligible choices are weighted (RNG decides) and the eligible `list[Choice]` when non-weighted. Adopted ARCHITECTURE.md Pattern 2 near-verbatim, adding a `total == 0` guard (fall through to return eligible instead of returning None on a degenerate all-zero-weight set).
- `enter_node` returns `node.on_enter` as a pure-data `MolAction` list and NEVER calls `cmd.*` — the strict testability boundary. The future controller (Phase 2 engine / Phase 6 Qt UI) is the only thing that translates MolActions to `cmd.*` via `c14/pymol_layer/molops.py`.
- The minimal story is explicitly placeholder (placeholder-* claim_ids, placeholder:structure asset key) — no real science, respecting the CITE-01 gate; the mock MolAction sink in tests just collects emitted actions.
- `StoryInterpreter` is stateless across calls — `GameState` and `RngEngine` are dependency-injected so a single instance serves any playthrough and the state/engine remain the saveable/replayable units.

## Deviations from Plan

None - plan executed exactly as written.

(Note: one extra test, `test_apply_effects`, was added beyond the plan's explicit test list — it covers the documented `apply_effects` method that the `_walk` helper relies on. This is a coverage strengthening, not a scope change.)

## Issues Encountered
- **Concurrent parallel execution of plan 02-03.** This plan (02-02) ran in parallel with plan 02-03 (validate) per the config's `parallelization: true`. The 02-03 session's commits (`6992ff5` feat, `695e9e7` refactor, `befad3b` docs) interleaved with 02-02's on the shared `main` branch during execution. At Task 1 commit time, `c14/story/validate.py` and `tests/test_validate.py` appeared as untracked files (02-03's in-flight work); by Task 2 they had been committed by the 02-03 session. The plans were **designed to be independent** — `validate.py`'s own docstring states it "does NOT import `c14.story.graph` ... so the two plans can run in parallel" — so no conflicts arose. I staged only 02-02's files in each task commit (never the 02-03 artifacts) and left the 02-03 SUMMARY/STATE updates to that session. The full 65-test suite passes with both plans' work present. This is expected parallel-execution behavior, not a defect.

## User Setup Required
None - no external service configuration required. Stdlib only; no new dependencies.

## Next Phase Readiness
- Phase 2 success criterion #1 is **proven**: the minimal story graph loads and the interpreter walks it (intro → weighted choice → ending) in pure Python with a mock MolAction sink and zero pymol import.
- Phase 2 success criterion #2 is **partially proven**: RNG determinism holds through the walk (same seed → same ending; different seeds diverge). Full determinism (incl. save/load PRNG-state round-trip through the walk) is proven in Plan 05's integration test.
- The StoryGraph loader + StoryInterpreter are the two halves Plan 02-04 (engine) wires together into the walk loop (engine holds GameState + RngEngine, delegates graph walking to the interpreter, dispatches emitted MolActions to the pymol_layer).
- The MolAction pure-data emission contract is exercised end-to-end — Phase 3's `c14/pymol_layer/molops.py` will consume the lists `enter_node` returns.
- The `{nodes: {id: {claim_ids}}}` story shape + the loader's manifest-merge are the contract Plan 02-03's `collect_claim_ids` (now landed) and Plan 02-05's validator/persist consume.
- No blockers. Ready for 02-04-PLAN.md (engine) and 02-05-PLAN.md (validator/persist).

---
*Phase: 02-story-engine-core*
*Completed: 2026-08-13*
