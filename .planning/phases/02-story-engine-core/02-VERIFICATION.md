---
phase: 02-story-engine-core
verified: 2026-08-13T20:05:24Z
status: passed
score: 4/4 Phase 2 success criteria verified (31/31 plan-level must-have truths verified)
re_verification: No — initial verification
human_verification:
  - test: "Qt GUI save/load buttons + real PyMOL molecular scene rendering"
    expected: "A real PyMOL session shows the loaded scene reconstructed by replaying on_enter MolActions via the cmd layer"
    why_human: "Explicitly OUT of Phase 2 scope by design (Phase 2 goal = WSL architecture proof, zero PyMOL/Qt). The cmd-layer translation (Phase 4) and Qt UI buttons (Phase 6) are downstream. The engine-level save/load + on_enter replay IS proven here; only the human-visible PyMOL/Qt wiring is deferred. Not a Phase 2 gap."
---

# Phase 2: Story Engine Core — Verification Report

**Phase Goal:** The entire game architecture is proven end-to-end in WSL — a minimal 2-node story is playable (intro node → weighted choice → ending node) with mocked MolActions, RNG determinism is verified, and save/load round-trips — before any PyMOL/Qt code is written. This is the architecture proof point that de-risks everything downstream.
**Verified:** 2026-08-13T20:05:24Z
**Status:** passed
**Re-verification:** No — initial verification

## Verification Method

Goal-backward verification. Plan frontmatter `must_haves` (truths, artifacts, key_links) from all 5 plans (02-01 … 02-05) were checked against the ACTUAL code — source files were read, the AST gate was run, the full unittest suite was run (97 tests), the demo was executed, and the refactored citation gate was exercised on both single-file and directory inputs. SUMMARY claims were NOT trusted; every truth was re-derived from executable evidence.

---

## Goal Achievement

### Observable Truths (Phase 2 Success Criteria)

| # | Truth (Success Criterion) | Status | Evidence |
|---|---------------------------|--------|----------|
| 1 | A minimal story graph (intro → weighted choice → ending) loads and the StoryInterpreter walks it in pure Python with a mocked MolAction sink (no PyMOL import) | ✓ VERIFIED | `python3.6 -m unittest discover -s tests -v` → 97/97 pass; `test_full_playthrough_reaches_ending`, `test_playthrough_emits_molactions_to_mock_sink`, `test_no_pymol_import_full_stack` all ok; demo `tools/demo_playthrough.py` exits 0 playing intro.start → weighted pick → intro.ending_bad; `assertNotIn('pymol', sys.modules)` holds after full stack exercise; AST gate `tools/check_imports.py` exits 0 |
| 2 | The RngEngine produces identical outcomes given the same seed across two runs and different outcomes given a different seed; both fixed-seed (demo) and random (play) modes are exercisable (unit-tested) | ✓ VERIFIED | `test_same_seed_same_ending`, `test_same_seed_same_molaction_sequence`, `test_diff_seed_both_endings_appear` (seeds 0..30 → 16 bad + 15 good), `test_random_mode_reproducible_after_record` all pass; spot-check: same seed 42 → same ending twice, diff seeds → set{'good','bad'}; `test_rng.py` (6 tests) covers determinism, diff-seed, random-mode records seed, state JSON round-trip, weighted_pick determinism |
| 3 | A save serializes GameState (current node, character, flags, RNG seed + state, visit counts, edit history) to human-readable JSON, and load restores an identical session by replaying the current node's on_enter MolActions | ✓ VERIFIED | `test_save_load_restores_identical_state` (`to_dict()` equality incl. rng_state), `test_save_load_replays_on_enter` (sink collects on_enter after load), `test_save_mid_playthrough_load_continues_same` (save before choose → load → choose reaches SAME ending as no-save run), `test_save_load_no_double_visit` (visit_counts[start]==1 not 2), `test_save_file_is_human_readable_json` (contains "current_node"/"seed"/"rng_state"); explicit mid-playthrough spot-check confirmed identical ending + no double-visit + valid JSON |
| 4 | A reachability checker (pure Python) runs on the toy graph and reports which endings are reachable — green on a well-formed graph, red on one with an orphaned ending | ✓ VERIFIED | `test_reachability_green_on_toy_graph` (rep.is_ok, reachable == {intro.ending_good, intro.ending_bad}, unreachable == []), `test_reachability_red_on_orphaned_variant` (orphaned "intro.ending_orphan" → not is_ok, in unreachable_endings), `test_validate_graph_clean_on_toy_graph`; `test_validate.py` (14 tests) covers green/red/missing-start/multi-hop/dangling-divert/none-goto; spot-check confirmed `check_reachability(g.all_nodes(), g.start_node()).is_ok == True` |

**Score:** 4/4 success criteria verified

---

### Per-Plan Must-Have Truths

#### Plan 02-01 (Foundation: model, rng, state)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Node.from_dict builds a Node carrying id, text_dramatic, text_teaching, claim_ids, choices (list of Choice), on_enter (list of MolAction), is_ending, tags, on_enter_divert | ✓ VERIFIED | `c14/story/model.py:188-208` Node.from_dict parses nested choices→Choice, on_enter→MolAction; `test_node_from_dict_full`, `test_node_roundtrip` pass |
| 2 | Choice.from_dict builds a Choice carrying label, goto, cond, weight, effects, tags | ✓ VERIFIED | `c14/story/model.py:108-119` Choice.from_dict; `test_choice_defaults`, `test_choice_from_dict` pass |
| 3 | MolAction is pure data (op, target, args) with NO pymol/PyQt5 import | ✓ VERIFIED | `c14/story/model.py:26-79` MolAction class; `grep "import (pymol\|PyQt5)" c14/story/model.py` → none; AST gate exit 0 |
| 4 | RngEngine(seed=42)×2 identical; RngEngine(42) vs RngEngine(43) differ | ✓ VERIFIED | `test_same_seed_same_sequence`, `test_diff_seed_diff_sequence` pass |
| 5 | Both modes: fixed-seed (seed=int) and random-seed (seed=None) records seed for replay | ✓ VERIFIED | `c14/rng.py:44-54` (secrets.randbits(31) when None); `test_random_mode_records_seed` passes; `eng.state.seed` is int after random start |
| 6 | RngEngine.get_state() JSON-serializable (lists not tuples); reconstructable from (seed, state) → same next draw | ✓ VERIFIED | `c14/rng.py:79-119` (list(st[1]) / tuple(state_dict["state"])); `test_state_json_roundtrip`, `test_fixed_mode_reproducible` pass |
| 7 | GameState.to_dict/from_dict round-trip preserves version, seed, character, current_node, flags, counters, visit_counts, edits_history, rng_state, protonation_pref, started_at, finished, ending_tier | ✓ VERIFIED | `c14/state.py:66-114`; `test_roundtrip_preserves_all_fields`, `test_to_dict_keys` pass; demo shows full rng_state (625-int list) round-trips identically |
| 8 | All three modules import cleanly in WSL with zero pymol/PyQt5 imports | ✓ VERIFIED | `python3.6 tools/check_imports.py` → "clean", exit 0; `python3.6 -m py_compile` all OK |

#### Plan 02-02 (Graph loader + Interpreter)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | StoryGraph.load reads manifest.json + merges listed files into {id: Node} via Node.from_dict | ✓ VERIFIED | `c14/story/graph.py:50-88` load(); `test_load_minimal_story` passes (3 nodes, 2 endings) |
| 2 | Minimal story (intro.json) has intro.start (2 weighted choices) → intro.ending_good + intro.ending_bad; manifest indexes intro.json with default_seed + start | ✓ VERIFIED | `data/story/intro.json` (2 weighted choices weight 1.0, is_ending good/bad); `data/story/manifest.json` (start: intro.start, files: [intro.json]) |
| 3 | pick_choice on all-weighted node uses RngEngine to pick one (deterministic); non-weighted returns eligible list | ✓ VERIFIED | `c14/story/interpreter.py:43-73` (rng.random()*total + cumulative sum); `test_pick_choice_weighted_returns_single`, `test_pick_choice_deterministic` pass |
| 4 | enter_node runs on_enter MolActions (returns list, no cmd.*), records visit_counts, detects is_ending (marks finished + ending_tier) | ✓ VERIFIED | `c14/story/interpreter.py:75-99` (record_visit, mark_finished, returns list(node.on_enter)); `test_enter_node_emits_molactions`, `test_enter_node_records_visit`, `test_enter_node_detects_ending` pass |
| 5 | Full walk completes in pure Python with mock MolAction sink — zero pymol import | ✓ VERIFIED | `test_full_walk_reaches_ending`, `test_full_walk_no_pymol_import` pass; demo confirms |
| 6 | RNG determinism through the walk: same seed → same ending; different seed may differ | ✓ VERIFIED | `test_pick_choice_deterministic`, `test_pick_choice_diff_seed_may_differ` pass; integration `test_same_seed_same_ending` + `test_diff_seed_both_endings_appear` (31 seeds) pass |

#### Plan 02-03 (Validator + citation gate refactor)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | check_reachability on well-formed graph → ReachabilityReport is_ok True, all endings reachable | ✓ VERIFIED | `c14/story/validate.py:167-207`; `test_reachability_green` passes |
| 2 | check_reachability on orphaned ending → is_ok False, orphan in unreachable_endings (RED) | ✓ VERIFIED | `test_reachability_red_orphaned` passes; integration `test_reachability_red_on_orphaned_variant` passes |
| 3 | validate_graph reports dangling diverts (choice.goto → nonexistent node) | ✓ VERIFIED | `c14/story/validate.py:214-235`; `test_validate_graph_dangling_divert`, `test_validate_graph_none_goto_ok` pass |
| 4 | collect_claim_ids accepts a single .json file OR a directory (manifest merge) | ✓ VERIFIED | `c14/story/validate.py:265-323` (os.path.isdir branch); `test_collect_claim_ids_file`, `test_collect_claim_ids_directory`, `test_collect_claim_ids_directory_multi_file` pass |
| 5 | tools/check_citations.py refactored: inline walker replaced by collect_claim_ids; core logic (0/1/2 exit + report) unchanged; --story accepts file OR dir | ✓ VERIFIED | `tools/check_citations.py:41` imports collect_claim_ids; gate on `data/story` dir → exit 0 ("3 claim reference(s) across 3 node(s)"); single-file fixtures → exit 0/1/2 preserved |
| 6 | All 12 existing citation tests still pass (backward compat) | ✓ VERIFIED | `python3.6 -m unittest tests.test_citations -v` → 12/12 ok |

#### Plan 02-04 (Persist + Engine)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SaveStore.save writes human-readable JSON (indent=2) of GameState.to_dict(); load returns equal GameState (all fields incl. seed + rng_state) | ✓ VERIFIED | `c14/persist.py:38-65` (indent=2, trailing newline, GameState.from_dict); `test_save_load_roundtrip`, `test_save_json_is_human_readable` pass |
| 2 | GameEngine(graph, sink).start(character, seed) enters start node, syncs rng_state, dispatches on_enter to sink | ✓ VERIFIED | `c14/engine.py:84-96` start(); `_enter` syncs `state.rng_state = rng.get_state()` and dispatches to sink; `test_start_enters_start_node`, `test_start_state_initialized` pass |
| 3 | GameEngine.choose(index) on weighted node auto-resolves RNG pick (index ignored); advances, dispatches on_enter | ✓ VERIFIED | `c14/engine.py:98-125` choose(); `test_choose_advances_to_ending`, `test_weighted_autopick_ignores_index` (choose(0) and choose(99) both advance) pass |
| 4 | GameEngine.save syncs rng_state then serializes; load rebuilds RngEngine from (seed, rng_state) and replays current node's on_enter | ✓ VERIFIED | `c14/engine.py:160-177` (save: sync+SaveStore; load: SaveStore.load + RngEngine.from_state + _enter(record_visit=False)); `test_save_load_roundtrip`, `test_load_replays_on_enter_molactions`, `test_load_does_not_double_count_visit`, `test_rng_state_survives_save_load` pass |
| 5 | Engine emits MolAction lists to sink — NEVER cmd.*; mock sink + no pymol import | ✓ VERIFIED | `c14/engine.py:151-153` per-action dispatch to `self.molaction_sink`; `test_no_pymol_import` passes; `assertNotIn('pymol', sys.modules)` after start+choose+save+load |

#### Plan 02-05 (Integration + Demo)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Full playthrough (start → weighted choice → ending) runs end-to-end in pure Python with mock MolAction sink — zero PyMOL (Phase 2 GOAL) | ✓ VERIFIED | `test_full_playthrough_reaches_ending`, `test_no_pymol_import_full_stack`, `test_no_pyqt_import_full_stack` pass; demo exits 0 |
| 2 | Same seed → same ending across two independent runs | ✓ VERIFIED | `test_same_seed_same_ending`, `test_same_seed_same_molaction_sequence` pass |
| 3 | Different seeds → different outcomes; across a range both endings appear | ✓ VERIFIED | `test_diff_seed_both_endings_appear` (seeds 0..30 → {'good','bad'}; 16 bad + 15 good) passes |
| 4 | Save mid-playthrough → load restores identical session; re-enters current node; played forward reaches same ending as original | ✓ VERIFIED | `test_save_mid_playthrough_load_continues_same` passes; explicit spot-check confirmed ending1==ending2 |
| 5 | Reachability green on toy graph (both endings reachable) + red on deliberately-orphaned variant | ✓ VERIFIED | `test_reachability_green_on_toy_graph`, `test_reachability_red_on_orphaned_variant`, `test_validate_graph_clean_on_toy_graph` pass |
| 6 | tools/demo_playthrough.py plays the 2-node story in WSL, prints text+choice+ending, saves, loads, prints restored state — exits 0 | ✓ VERIFIED | `python3.6 tools/demo_playthrough.py` → prints banner, start node text + 2 choices, 3 MolAction emissions, ending_bad, game state JSON, save path, loaded on_enter replay, restored state, "VERIFY: loaded state identical to saved state -- OK", exit 0 |

---

### Required Artifacts

All artifacts checked at three levels: **existence** (file present), **substantive** (real implementation, not stub; adequate length; has exports; no stub markers), **wired** (imported/used elsewhere).

| Artifact | Provides | Exists | Substantive | Wired | Status |
|----------|----------|--------|-------------|-------|--------|
| `c14/story/__init__.py` | c14.story subpackage marker | ✓ | ✓ (marker) | ✓ (importable) | ✓ VERIFIED |
| `c14/story/model.py` (244 lines) | Node, Choice, MolAction plain classes; from_dict/to_dict/__eq__/__repr__ | ✓ | ✓ (244 lines, 3 exported classes, no stubs) | ✓ (graph.py, interpreter.py, engine.py, validate.py, tests import) | ✓ VERIFIED |
| `c14/rng.py` (122 lines) | RngEngine: __init__(seed=None), random(), weighted_pick(), get_state/set_state/from_state, seed property | ✓ | ✓ (122 lines, exported class, no stubs) | ✓ (engine.py, interpreter tests, engine tests import) | ✓ VERIFIED |
| `c14/state.py` (187 lines) | GameState: to_dict/from_dict/new_game + flag/incr/record_visit/mark_finished helpers | ✓ | ✓ (187 lines, exported class, no stubs) | ✓ (persist.py, engine.py, tests import) | ✓ VERIFIED |
| `c14/story/graph.py` (126 lines) | StoryGraph.load(story_dir), get_node, all_nodes (dict), start_node, endings | ✓ | ✓ (126 lines, exported class, no stubs) | ✓ (engine.py, interpreter tests, integration tests import) | ✓ VERIFIED |
| `c14/story/interpreter.py` (157 lines) | StoryInterpreter: pick_choice, enter_node (record_visit param), _cond, apply_effects | ✓ | ✓ (157 lines, exported class, no stubs) | ✓ (engine.py imports + uses pick_choice/enter_node/apply_effects) | ✓ VERIFIED |
| `c14/story/validate.py` (323 lines) | check_reachability, validate_graph, collect_claim_ids, ReachabilityReport, Issue | ✓ | ✓ (323 lines, 2 classes + 3 functions, no stubs) | ✓ (check_citations.py imports collect_claim_ids; integration tests use check_reachability/validate_graph) | ✓ VERIFIED |
| `c14/persist.py` (68 lines) | SaveStore.save (indent=2, parent-dir creation) + load | ✓ | ✓ (68 lines, exported class, no stubs — thin by design) | ✓ (engine.py save/load delegate to it) | ✓ VERIFIED |
| `c14/engine.py` (183 lines) | GameEngine: start/choose/_enter/save/load + TurnResult; owns StoryInterpreter+GameState+RngEngine | ✓ | ✓ (183 lines, 2 exported classes, no stubs) | ✓ (demo + integration + engine tests import GameEngine) | ✓ VERIFIED |
| `data/story/manifest.json` (6 lines) | Bundle index: version, default_seed, start, files | ✓ | ✓ (valid JSON, all fields) | ✓ (StoryGraph.load reads it) | ✓ VERIFIED |
| `data/story/intro.json` (37 lines) | Minimal 2-node story: intro.start (2 weighted choices) + 2 endings; placeholder claim_ids | ✓ | ✓ (valid JSON, 3 nodes, 2 weighted choices, is_ending good/bad) | ✓ (StoryGraph.load + collect_claim_ids read it) | ✓ VERIFIED |
| `tools/check_citations.py` (123 lines) | Refactored gate: imports collect_claim_ids; --story file OR dir; 0/1/2 exit unchanged | ✓ | ✓ (123 lines, import present, exit codes preserved) | ✓ (invocation proven on dir + single-file) | ✓ VERIFIED |
| `tools/demo_playthrough.py` (122 lines) | Runnable architecture-proof demo; exits 0 | ✓ | ✓ (122 lines, real playthrough + save/load + verify) | ✓ (imports GameEngine + StoryGraph; runs end-to-end) | ✓ VERIFIED |
| `tests/test_model.py` (136 lines, 7 tests) | Model round-trip + defaults + from_dict + is_ending | ✓ | ✓ (7 test methods, real asserts) | ✓ (in unittest discover) | ✓ VERIFIED |
| `tests/test_rng.py` (79 lines, 6 tests) | Determinism, diff-seed, random-mode, state round-trip, weighted_pick | ✓ | ✓ (6 test methods, real asserts) | ✓ | ✓ VERIFIED |
| `tests/test_state.py` (108 lines, 7 tests) | GameState round-trip, keys, helpers, new_game, tolerates missing | ✓ | ✓ (7 test methods, real asserts) | ✓ | ✓ VERIFIED |
| `tests/test_interpreter.py` (175 lines, 12 tests) | Graph load, weighted pick, enter_node, cond, full walk, no pymol | ✓ | ✓ (12 test methods, real asserts) | ✓ | ✓ VERIFIED |
| `tests/test_validate.py` (217 lines, 14 tests) | Reachability green/red/multi-hop/missing-start, dangling divert, collect_claim_ids file/dir | ✓ | ✓ (14 test methods, real asserts) | ✓ | ✓ VERIFIED |
| `tests/test_persist.py` (118 lines, 5 tests) | Save/load round-trip, parent dir, human-readable, malformed/missing raises | ✓ | ✓ (5 test methods, real asserts) | ✓ | ✓ VERIFIED |
| `tests/test_engine.py` (217 lines, 10 tests) | start/choose/weighted-autopick/save-load/replay/no-double-visit/rng-survives/no-pymol/random-mode | ✓ | ✓ (10 test methods, real asserts) | ✓ | ✓ VERIFIED |
| `tests/test_integration.py` (405 lines, 17 tests) | End-to-end: all 4 success criteria + citation gate on dir + orphaned variant | ✓ | ✓ (17 test methods, real asserts incl. assertNotIn('pymol'/'PyQt5', sys.modules)) | ✓ | ✓ VERIFIED |

**All 21 artifacts: ✓ VERIFIED** (exist, substantive, wired)

---

### Key Link Verification

| Plan | From | To | Via | Pattern Found | Status |
|------|------|----|-----|---------------|--------|
| 01 | c14/story/model.py | stdlib only | no pymol/PyQt5 import | `grep` → NO banned imports | ✓ WIRED |
| 01 | c14/rng.py | random.Random | wraps single random.Random(seed) | `self._rng = random.Random(self._seed)` (rng.py:54) | ✓ WIRED |
| 01 | c14/state.py | c14.rng (via rng_state) | GameState stores seed + rng_state | `rng_state` field in to_dict/from_dict (state.py:85,109) | ✓ WIRED |
| 02 | c14/story/graph.py | c14/story/model.py | load() builds Node via Node.from_dict | `nodes[node_id] = Node.from_dict(raw_with_id)` (graph.py:87) | ✓ WIRED |
| 02 | c14/story/interpreter.py | c14/rng.py | weighted branch draws rng.random()*total | `r = rng.random() * total` (interpreter.py:65) | ✓ WIRED |
| 02 | c14/story/interpreter.py | c14/state.py | enter_node records visit + mark_finished | `state.record_visit(node.id)` / `state.mark_finished(node.is_ending)` (interpreter.py:95,98) | ✓ WIRED |
| 02 | c14/story/interpreter.py | c14/story/model.py (MolAction) | enter_node returns node.on_enter (pure data) | `actions = list(node.on_enter)` (interpreter.py:96) — no cmd.* | ✓ WIRED |
| 03 | c14/story/validate.py | c14/story/model.py | traverses choices[].goto / reads claim_ids | `_choices`/`_goto`/`_is_ending` helpers + collect_claim_ids (validate.py:124-160,265-323) | ✓ WIRED |
| 03 | tools/check_citations.py | c14.story.validate.collect_claim_ids | refactored import replaces inline walker | `from c14.story.validate import collect_claim_ids` (check_citations.py:41); `referenced = collect_claim_ids(story_path)` (line 55) | ✓ WIRED |
| 03 | tests/test_validate.py | c14/story/validate.py | direct unit tests on the 3 functions | 14 tests call check_reachability/validate_graph/collect_claim_ids | ✓ WIRED |
| 04 | c14/engine.py | c14/story/interpreter.py | delegates pick_choice/enter_node/apply_effects | `self.interpreter.pick_choice` / `.enter_node` / `.apply_effects` (engine.py:113,124,140) | ✓ WIRED |
| 04 | c14/engine.py | c14/rng.py | owns RngEngine; from_state on load; get_state on save | `RngEngine(seed)` (93), `self.rng.get_state()` (144,164), `RngEngine.from_state(...)` (176) | ✓ WIRED |
| 04 | c14/engine.py | c14/state.py | owns GameState; new_game on start | `GameState.new_game(character, self.rng.seed, start_id)` (engine.py:95) | ✓ WIRED |
| 04 | c14/engine.py | c14/persist.py | save/load via SaveStore | `SaveStore.save(self.state, path)` (165), `SaveStore.load(path)` (175) | ✓ WIRED |
| 04 | c14/engine.py | MolAction sink (mock) | emits per-action to sink, never cmd.* | `for action in actions: self.molaction_sink(action)` (engine.py:151-153) | ✓ WIRED |
| 05 | tests/test_integration.py | full c14 stack | exercises GameEngine+StoryGraph+RngEngine+SaveStore+check_reachability | imports + uses all (integration.py:52-58) | ✓ WIRED |
| 05 | tools/demo_playthrough.py | c14.engine | imports GameEngine + runs playthrough | `from c14.engine import GameEngine` (demo:46) | ✓ WIRED |

**All 17 key links: ✓ WIRED**

---

### Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **STORY-01**: A branching narrative graph (DAG of nodes) drives the story via text-based multiple choice at each branch point | ✓ SATISFIED (engine layer) | StoryGraph + StoryInterpreter + GameEngine implement the DAG walk with weighted + non-weighted multiple-choice branches; the minimal story proves the DAG mechanism (intro.start → 2 choices → 2 endings). Real glucose skeleton content is Phase 5.1 (by design). |
| **STORY-04**: RNG is seedable for classroom reproducibility: fixed-seed (demo) + random (play) modes both available | ✓ SATISFIED | RngEngine(seed=int) fixed mode + RngEngine(seed=None) random mode; determinism proven (same seed → same ending + same MolAction sequence); random mode records seed for replay. 6 unit tests + integration tests. |
| **SAVE-01**: Save button persists game progress/state to a JSON file (human-readable, diff-friendly) | ✓ SATISFIED (data layer) | SaveStore.save writes GameState.to_dict() as indent=2 JSON with trailing newline; human-readable keys (current_node, seed, rng_state) confirmed in file text. The UI "button" is Phase 6 (Qt) — the data layer this requirement needs is delivered in Phase 2. |
| **SAVE-02**: Load button restores a saved session (molecular scene reconstructed by replaying current node's MolActions) | ✓ SATISFIED (engine layer) | GameEngine.load rebuilds RngEngine from (seed, rng_state) and replays current node's on_enter MolActions via the sink (record_visit=False to avoid double-counting); Pattern 6 proven. The UI "button" is Phase 6; the load + on_enter replay engine capability is delivered. |

**All 4 Phase 2 requirements: SATISFIED** at the architecture/engine layer (which is exactly Phase 2's goal — the architecture proof point). The Qt UI "buttons" named in SAVE-01/SAVE-02 are explicitly Phase 6 work; the underlying engine + save format + replay mechanism they require are proven here.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | — | — | No TODO/FIXME/HACK/stub markers, no empty-stub returns, no walrus `:=`, no `from __future__ import annotations`, no `@dataclass` decorator (only docstring mentions saying "NOT @dataclass") in any Phase 2 c14/ module or test. |

**Anti-pattern scan: clean.** The only `@dataclass`/`from __future__` string matches are inside docstrings explicitly stating these 3.7+ features are NOT used (3.6 compatibility honored). `.pyc` binary matches are compiled bytecode containing those docstrings — not source usage.

---

### Cross-Cutting Invariants

| Invariant | Check | Result |
|-----------|-------|--------|
| No pymol/PyQt5 imports in c14/ | `python3.6 tools/check_imports.py` | ✓ exit 0 ("clean") |
| Python 3.6 syntax compatibility | `python3.6 -m py_compile` on all 11 source modules | ✓ all OK |
| No @dataclass (3.7+) | `grep -rn "@dataclass" c14/` | ✓ only docstring mentions (no decorator) |
| No walrus (3.8+) / no future annotations (3.7+) | `grep -rnE ":=\|from __future__ import annotations"` | ✓ none in source |
| Full test suite green | `python3.6 -m unittest discover -s tests -v` | ✓ 97/97 pass (19 Phase 1 + 78 Phase 2) |
| Demo runnable, exits 0 | `python3.6 tools/demo_playthrough.py` | ✓ exit 0 + "VERIFY: loaded state identical to saved state -- OK" |
| Citation gate backward compat | single-file fixtures exit 0/1/2 | ✓ 0 (pass) / 1 (pending) / 2 (malformed) preserved |
| Citation gate new dir capability | `--story data/story` + temp registry | ✓ exit 0 ("3 claim reference(s) across 3 node(s) -- all approved") |
| Testability boundary (no pymol after full stack) | `assertNotIn('pymol', sys.modules)` + `assertNotIn('PyQt5', sys.modules)` | ✓ both pass after full playthrough |

---

### Human Verification Required

| # | Test | Expected | Why Human | Blocks Phase 2? |
|---|------|----------|-----------|-----------------|
| 1 | Qt GUI save/load buttons + real PyMOL molecular scene rendering | A real PyMOL session shows the loaded scene reconstructed by replaying on_enter MolActions via the cmd layer | Explicitly OUT of Phase 2 scope by design (Phase 2 goal = WSL architecture proof, zero PyMOL/Qt). cmd-layer translation is Phase 4; Qt UI is Phase 6. The engine-level save/load + on_enter replay IS proven here. | **No** — not a Phase 2 gap |

No human verification items block the Phase 2 goal. Phase 2's stated goal is "proven end-to-end in WSL … before any PyMOL/Qt code is written" — which is exactly what was verified. The PyMOL/Qt wiring is deliberately deferred to Phases 4/6.

---

### Informational Notes (Not Gaps)

1. **Per-action sink dispatch (documented deviation, internally consistent).** The plan 02-04 body described the sink as `self.molaction_sink(actions)` (list dispatch), but the implemented engine dispatches per-action: `for action in actions: self.molaction_sink(action)` (engine.py:151-153). This is a deliberate, documented choice — the engine docstring, the demo (`def sink(action)`), and all tests (`sink.append`) align on the per-action contract. All test assertions (`len(sink) == 2`, `sink[0].op == 'hide_all'`) hold correctly. The `molaction_sink` key_link is present and the "never cmd.*" boundary holds. **Not a gap** — the deviation is internally consistent and the goal (testability boundary) is achieved.

2. **`c14/story/__init__.py`** is the subpackage marker (importable). Confirmed via successful `from c14.story.model import ...` across all consumers.

3. **`data/story/intro.json`** content is explicitly placeholder (claim_ids prefixed `placeholder-`, on_enter references `placeholder:structure`) — matches the spec's "no fabricated science" rule. The 3 placeholder claim_ids were approved via a temp registry to exercise the gate end-to-end.

---

### Gaps Summary

**No gaps found.** All 4 Phase 2 success criteria are verified against executable evidence (97 tests pass, demo exits 0, gate works on dir + single-file, all 4 success-criteria spot-check passes). All 31 plan-level must-have truths are verified. All 21 artifacts exist, are substantive, and are wired. All 17 key_links are confirmed in the source. No anti-patterns. No human-verification blockers for the Phase 2 goal.

The Phase 2 goal — "the entire game architecture is proven end-to-end in WSL … before any PyMOL/Qt code is written … the architecture proof point that de-risks everything downstream" — is **achieved**.

---

_Verified: 2026-08-13T20:05:24Z_
_Verifier: OpenCode (gsd-verifier)_
