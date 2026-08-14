# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-12)

**Core value:** The player experiences cellular respiration as a story with consequences — every choice and edit on the C14 hero either advances them toward a destiny (ATP [the hero's electrons harvested into energy via the ETC], storage, CO2, or catastrophe) or diverts them into a branch, with real PDB proteins as the cast and scientifically validated chemistry as the plot.
**Current focus:** Phase 3 — PyMOL cmd Layer + Asset Management (Headless) — IN PROGRESS. Plan 03-01 (GATE: headless harness + api-sanity smoke + source-citation convention) COMPLETE ✓ — the WSL->Windows headless bridge is proven (10 cmd.* stages all green via SMOKE_RESULT sentinel), the harness contract is established for Plans 02+03, and the cmd.create pitfall is empirically corrected. Next: Plan 03-02 (AssetManager) + 03-03 (MolOps). Phase 2 remains complete+verified (97 tests, demo exits 0, zero PyMOL/Qt in c14/).

## Current Position

Phase: 3 of 13 (PyMOL cmd Layer + Asset Management — Headless) — IN PROGRESS
Plan: 1 of 3 complete in current phase (03-01 done; 03-02 + 03-03 next)
Status: In progress — 03-01 GATE plan complete (headless bridge proven; harness + sentinel + citation convention established; cmd.create pitfall corrected)
Last activity: 2026-08-14 — Completed 03-01-PLAN.md (api-sanity smoke PASSED: 10/10 stages green via SMOKE_RESULT sentinel; 22 source-citations; bundled fixture + run_headless.sh + gitignore delivered)

Progress: [█████████░] ~30% (9 plans complete of 11 planned in phases 1-3; phases 4-13 not yet planned)

## Performance Metrics

**Velocity:**
- Total plans completed: 9
- Average duration: 25 min
- Total execution time: 3.42 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundations & Citation Gate | 3/3 ✓ | 56 min | 19 min |
| 2. Story Engine Core | 5/5 ✓ | 78 min | 16 min |
| 3. PyMOL cmd Layer | 1/3 | 91 min | 91 min |

**Recent Trend:**
- Last 3 plans: 02-05 (4 min), 03-01 (91 min), [03-02 next]
- Trend: 03-01 (the Phase 3 GATE) was the heaviest single plan so far (91 min) — it empirically proved the WSL->Windows headless bridge, established the SMOKE_RESULT sentinel + source-citation contracts, and corrected the cmd.create pitfall. The 91 min includes context loading (reading 03-RESEARCH.md + all context files) + file creation + the headless smoke run (network fetches). Plans 02+03 are lighter (reuse the harness + convention).

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 12-phase comprehensive build order (10 integer milestones + 2 INSERTED decimal design phases at 5.1/5.2); Phase 5 (Key Decisions + source approval) runs parallel with Phases 2–4 and gates all content (Phases 6–9).
- [Roadmap]: Architecture = 3-tier testability layering (pure-Python domain → pymol.cmd headless layer → pymol.Qt human-verify layer); ink-inspired story graph as JSON we own; edit routing via lookup table + bad-ending fallback; citation registry as architectural no-fabricated-science gate.
- [Roadmap]: Two INSERTED design phases (5.1 Story Graph Design, 5.2 Cast & Hero Representation Design) sit between Phase 5 decisions and Phase 6 MVP — they make the story graph topology + MC-choice/edit-node integration contracts and the 3D visual language explicit, reviewable artifacts before any Qt UI or cited content is built. Both own 0 requirements (design phases, per Phase 10 precedent); they enable downstream delivery.
- [Roadmap]: Content is a marathon across Phases 7–9 (glucose → fatty acid + alcohol → anaerobic + full cast), dominated by per-claim approval throughput (Pitfall 7), not engineering difficulty.
- [Roadmap]: Content phases 7/8/9 are NOT split into more phases despite the heavy per-claim citation load. Instead each uses granular per-pathway-segment plans (5–7 for P7, 4–6 for P8, 4–5 for P9). Rationale: (a) per-claim approval is orthogonal to phase structure — the human approves claims individually regardless; (b) already at top of comprehensive depth (12 phases), splitting would exceed range; (c) content segments are sequential (continuity), so phases buy no parallelism; (d) phase-level verifier marginal value is low for content (citation gate already enforced at build time); (e) plans give the per-segment review cadence the user wants with less ceremony. See ROADMAP.md "Content Phase Plan Granularity".
- [Roadmap]: Phase 11 (Documentation Finalization & Verification) split OUT of Phase 10 per user feedback. Phase 10 keeps polish, playtest-driven edit-table expansion, accessibility, full manual GUI test matrix, pre-ship citation gate. Phase 11 owns: update README + in-game help to match final shipped content (cast list, slogan, PDB IDs + resolutions), verify all docs reflect shipped game, final docs verification as the last release gate. Phase 11 owns 0 new requirements (verifies/updates DOC-01, DOC-02 created in Phase 9, per the Phase 10 0-requirement precedent). Phase 11 depends on Phase 10 (content polish settled before docs finalization) — it is the LAST release gate before ship.
- [Execution 01-01]: AST-based import gate (tools/check_imports.py) adopted over grep — 0 false positives on comments/strings, catches aliased `import pymol.cmd as c`. Strict-ban policy: flags any pymol/PyQt5 Import/ImportFrom including inside TYPE_CHECKING guards. Directory location = tier (c14/ root scanned; pymol_layer/ + ui/ excluded).
- [Execution 01-01]: c14/__init__.py stays pure-Python in Phase 1 (zero pymol/PyQt5 imports); __init_plugin__ deferred to Phase 6 (lazy-delegate to c14/ui/plugin_entry.py per research Pattern 1).
- [Execution 01-01]: Python 3.6 stdlib only — unittest (pytest not installed); subprocess uses stdout/stderr=PIPE not capture_output (3.7+); py_compile + unittest paired (Pitfall 3: py_compile necessary but not sufficient).
- [Execution 01-03]: Citation gate predicate is `approval_status == "approved"` (strict equality), NOT `!= "pending"` — research Pitfall 6: `!= "pending"` would erroneously pass a `rejected` claim. A rejected claim fails identically to a pending one (no special case). Verified by the rejected fixture (exit 1, status 'rejected').
- [Execution 01-03]: Keep all three approval_status values {pending, approved, rejected} in the enum — `rejected` records provenance (why a claim was refused) rather than silently deleting. Phase 1 success criterion (names only pending/approved) fully satisfied by the `== "approved"` test.
- [Execution 01-03]: `object_pairs_hook` duplicate-key detection in CitationRegistry.load (~6 lines) — without it, json.load silently last-wins on duplicate claim_id keys, clobbering an approval/rejection. Verified raising on 3.6.9 (Pitfall 3).
- [Execution 01-03]: Three-way exit codes (0=pass / 1=missing-or-unapproved / 2=config-load-error) for the citation gate — lets CI distinguish "broken fixtures/tooling" (exit 2) from "genuinely unapproved science" (exit 1). Phase 1 success criterion only requires non-zero on fail; the split is a clean-to-have the plan adopted.
- [Execution 01-03]: `data/citations.json` lives at REPO ROOT `data/` (content source file, read at pre-ship time by the gate), NOT `c14/data/` (bundled runtime asset that ships in the plugin zip). Distinct directories with distinct roles — established early to avoid future confusion.
- [Execution 01-03]: Registry shipped as JSON object (`data/citations.json`), NOT JSONL (`data/claims.jsonl`) — research Pitfall 2: O(1) lookup, structural dup-key prevention, matches authoritative ARCHITECTURE.md. The `.jsonl` references in earlier research are superseded.
- [Execution 01-03]: Story-walker (`collect_referenced_claim_ids`) isolated in one function in `tools/check_citations.py` — Phase 2 swaps it for `c14.story.validate.collect_claim_ids("data/story/")` with zero changes to the gate's core logic (forward-compatible contract).
- [Execution 01-02]: c14.paths.data_path() is a pure `__file__`-relative resolver (NO existence check) — separation of concerns; callers handle FileNotFoundError; supports "compute where a future file would go". selfcheck() DOES check existence (raises FileNotFoundError) — the fail-loud layout invariant for plugin load (Pitfall 1 mitigation, Phase 6+ caller). Return type pathlib.Path; str(path) coerces for PyMOL cmd.* string-path APIs.
- [Execution 01-02]: CWD-independence proven via real `os.chdir(tempfile.mkdtemp())` in setUp — honest end-to-end proof, better than `mock.patch('os.getcwd')` which only proves the call site. Existence-of-fixture-from-foreign-CWD IS the proof; adopted near-verbatim from 01-RESEARCH-paths.md Pattern 2.
- [Execution 01-02]: README.md satisfies DOC-04 already (verified, NOT modified) — 01-RESEARCH-paths.md read the 57-line file in full; banner + description + TBD: Installation/References/Cast all present. Read-only verification task produced no commit (no changes; respects CITE-01 gate and later-phase content ownership).
- [Execution 01-02]: Bundled data lives inside `c14/data/` (ships in PyMOL Plugin Manager zip); distinct from repo-root `data/` (Plan 03's citations.json source/registry file, read at pre-ship time). Two directories, two roles — established early to avoid future confusion.
- [Execution 02-01]: Plain classes (NOT @dataclass) for Node/Choice/MolAction/RngEngine/GameState — 3.6.9 has no dataclasses module (Phase 1 Pitfall 1); matches CitationRegistry precedent. ARCHITECTURE.md shows @dataclass but the plan explicitly overrides for 3.6 compat; field names/semantics kept near-verbatim.
- [Execution 02-01]: MolAction is pure data (op/target/args) with NO pymol import — the testability-boundary carrier. The future c14/pymol_layer/molops.py (Phase 3/4) translates it to cmd.*. Domain tier never names a pymol type (ARCHITECTURE.md Pattern 1 / Anti-Pattern 1, enforced by the AST gate).
- [Execution 02-01]: RngEngine random-mode picks seed via `secrets.randbits(31)` (3.6-safe stdlib) and records it on .seed for replay. Single random.Random per playthrough; ALL stochastic draws go through it (Anti-Pattern 7). get_state/set_state/from_state convert tuples<->lists for JSON; verified the exact next draw survives JSON round-trip on 3.6.9.
- [Execution 02-01]: GameState stores seed + rng_state as plain data (does NOT hold a live RngEngine); the engine syncs rng.get_state() into state before save and rebuilds via RngEngine.from_state(seed, rng_state) on load. to_dict key order fixed to ARCHITECTURE.md GameState JSON for diff-stable saves; from_dict uses .get defaults for partial/older-save tolerance. finished=True (truthy bool) when ending reached, None while playing.
- [Execution 02-03]: Duck-typed _choices/_goto/_is_ending helpers (hasattr() dispatch) make check_reachability/validate_graph work on BOTH Node objects (node.choices/.goto/.is_ending) and raw JSON dicts (node.get('choices')/['goto']/['is_ending']) — single algorithm code path, no duplication. Lets the same validator serve the loader's Node objects and the gate's raw JSON fixtures.
- [Execution 02-03]: collect_claim_ids does its OWN minimal file loading (does NOT import c14.story.graph) so Plan 03 stays independent of Plan 02 for parallel execution. Accepts a file (backward-compat with Phase 1 fixtures) OR a directory (manifest.json + merge files). The minor manifest-reading overlap with graph.py is an acceptable trade for module independence.
- [Execution 02-03]: check_reachability skips edges to nonexistent nodes (graceful — can't reach what doesn't exist); validate_graph flags them as dangling_divert (structural). Separation of concerns: reachability checker reports reach; validator reports structure. Missing-start_id returns is_ok=False (graceful, no crash).
- [Execution 02-03]: Citation gate surgical refactor complete — inline collect_referenced_claim_ids replaced by c14.story.validate.collect_claim_ids; gate core logic (registry cross-ref, [MISSING]/[UNAPPROVED] report, 0/1/2 exit codes) UNCHANGED; --story accepts file OR directory. All 12 existing tests pass (zero regression — Phase 1 forward-compatible contract honored: the walker was isolated in one function precisely so this swap is surgical).
- [Execution 02-02]: StoryGraph.load(story_dir) injects the JSON object key as the node's `id` field before Node.from_dict (which requires d["id"]) — keeps the {nodes: {id: {claim_ids}}} shape the Phase 1 citation gate story-walker reads, without duplicating the id inside each node body. Loader is CWD-independent (explicit story_dir arg); all_nodes() returns the {id: Node} dict (NOT a list) as the Plan 03/05 contract.
- [Execution 02-02]: StoryInterpreter (ARCHITECTURE.md Pattern 2 near-verbatim) emits pure-data MolAction lists from enter_node — NEVER cmd.* (testability boundary proven by a full walk with a mock sink + `'pymol' not in sys.modules`). pick_choice: weighted -> single Choice via rng.random()*total + cumulative sum (single injected RngEngine, Anti-Pattern 7); non-weighted -> eligible list. _cond: restricted-namespace {flags,char,counters,visits} eval with no builtins, trusted-content model, fail-safe False on any exception.
- [Execution 02-02]: Phase 2 success criterion #1 PROVEN — minimal story (intro.start -> 2 weighted choices -> 2 endings) loads and the interpreter walks it (enter -> weighted pick -> advance -> enter ending) in pure Python with a mock MolAction sink and zero pymol import. RNG determinism through the walk holds (same seed -> same ending; diff seeds diverge) — criterion #2 partially proven (full save/load determinism in Plan 05).
- [Execution 02-04]: SaveStore is a thin pure-data layer (json.dump indent=2 + GameState.from_dict; parent-dir creation + trailing newline). It does NOT replay MolActions and does NOT save .pse (Anti-Pattern 5); the ENGINE owns the on_enter replay on load (Pattern 6). Human-readable, diff-friendly saves (Decision D2).
- [Execution 02-04]: GameEngine is the turn loop (start/choose/_enter/save/load) wiring StoryInterpreter + GameState + RngEngine. It emits on_enter MolActions PER-ACTION to an injected molaction_sink (a callable taking a single MolAction) — never cmd.* (the testability boundary; a plain list .append is the test mock). Chose per-action dispatch because the plan's test done-criteria (len(sink)==2, sink[0].op with sink.append) required it; the plan's key_links prose ("callable(list)") conflicted with its own tests, so the tests won. Phase 4+ molops.apply(action) receives one action per call (the natural unit).
- [Execution 02-04]: RNG-state sync — _enter() writes rng.get_state() into state after every entry and save() syncs before serializing; load() rebuilds the RngEngine via RngEngine.from_state(seed, rng_state) and replays the current node's on_enter with record_visit=False (no visit double-count). Exact-next-draw equivalence proven (test_rng_state_survives_save_load). Phase 2 success criterion #3 PROVEN (save/load restores an identical session by replaying on_enter); criterion #2 proven through the engine (the single seeded RngEngine carries through start->choose->save->load).
- [Execution 02-04]: interpreter.enter_node gained a backward-compatible record_visit=True param (2-line additive edit) so load-replay can skip the visit bump. All 12 existing interpreter tests still pass (zero regression — Plan 02 forward-compatible contract honored).
- [Execution 02-05]: Phase 2 GOAL ACHIEVED — 17-test integration suite (tests/test_integration.py) + runnable demo (tools/demo_playthrough.py) prove all 4 Phase 2 success criteria end-to-end in pure Python with zero PyMOL/Qt import. The integration test imports the FULL domain stack at module top (engine+graph+rng+state+persist+validate+model) and asserts 'pymol'/'PyQt5' not in sys.modules after a full playthrough — the testability boundary proven across the entire architecture, not just per-module. SC2 strongest proof: mid-playthrough save (before the weighted choice) -> load -> choose reaches the SAME ending as never saving (saved RNG position converges). SC4 orphaned-variant built via Node.from_dict on a copy of g.all_nodes(). The demo (seed 42, exits 0) is the human-visible proof twin. 97 tests pass; AST gate clean. No deviations (plan executed exactly as written; the per-action dispatch contract from 02-04 was pre-flagged and adapted correctly).
- [Execution 03-01]: Headless bridge verdict via STDOUT sentinel, NOT exit code — run-conda-pymol.bat ALWAYS returns 0 (`call conda deactivate` overwrites %ERRORLEVEL%; PyMOL's parsing.run_file swallows exceptions). SC #1's "exit code 0" reinterpreted as "SMOKE_RESULT: PASS sentinel present". The harness (tools/run_headless.sh) greps ^SMOKE_RESULT: PASS (presence=pass, absence=fail — stricter than grepping FAIL which falsely passes if the smoke crashes before printing the sentinel). Every later headless test (Plans 02+03) reuses this contract.
- [Execution 03-01]: cmd.create pitfall EMPIRICALLY CORRECTED — the "silent no-op" claim (PITFALLS.md Pitfall 3) did NOT reproduce for a new-target backup. Real gotchas: (a) create(bak,src,1,1) copies ONLY state 1 → incomplete multi-state backup (silent data loss); (b) create(obj,obj) self-copy is DESTRUCTIVE (raises CmdException + corrupts source); (c) default-args cmd.create(backup,source) (source_state=0,target_state=0=ALL states) is the working form — matches ARCHITECTURE.md:304. PITFALLS.md updated (5 targeted edits). Phase 4 restore uses default-args create.
- [Execution 03-01]: delete post-condition MUST use ?-prefix — bare count_atoms("deleted_obj") RAISES CmdException('Invalid selection name'); count_atoms("?"+name) returns 0 (safe). The ? is PyMOL's existing-objects-only selector prefix (used throughout source, e.g. creating.py:1001).
- [Execution 03-01]: Source-citation convention established — every cmd.* call carries `# src: tmp/pymol-src/modules/pymol/<file>.py:<line> cmd.<name>` on the line directly above it (22 citations in api_sanity_smoke.py; greppable via `grep -rn "# src: tmp/pymol-src"`). Line numbers pinned to PyMOL 2.5.0 (all 12 verified against tmp/pymol-src/modules/pymol/). Plans 02+03 must follow this for AssetManager + MolOps.
- [Execution 03-01]: Bundled (c14/data/assets/bundled/, committed, ships in plugin zip) vs Downloaded (c14/data/assets/downloaded/, gitignored, runtime cache) asset directory split. cmd.fetch skips download if file exists (importing.py:1211-1213) = free idempotent cache. Verified: check-ignore downloaded/ -> path; check-ignore bundled/ -> nothing.

### Pending Todos

None yet.

### Blockers/Concerns

Issues that affect future work:

- [Phase 5]: 4 science-framing Key Decisions gate content authoring. Pitfall 4 (ATP/True-Ending carbon-fate reframing) is now RESOLVED (2026-08-13, via the soul-jump reframing — electrons-as-soul harvested into ATP via ETC after the RNG-weighted TCA path; carbon body released as CO2; see PROJECT.md Key Decisions). The remaining 3 are HOW decisions for the human, still Pending: C14-decay timescale (Pitfall 9); anaerobic framing; batch-vs-per-claim approval. They are flagged as Phase 5 tasks. Start this track early — it is the timeline-domininating risk (Pitfall 7). The anaerobic decision now specifically gates Phase 5.1 (Story Graph Design); the ATP/True-Ending decision (resolved) no longer blocks it.
- [Phase 5.1 / 5.2 (INSERTED)]: Two design phases gate Phase 6. Phase 5.1 (Story Graph Design) needs Phase 2 + the Phase 5 ATP decision [now RESOLVED via soul-jump — electrons-as-soul → ATP via ETC after RNG-weighted TCA path; True-ending node = electron harvest, NOT carbon-becomes-ATP]; it produces the glucose skeleton + MC-choice/edit-node integration contracts (resolves the user's story-design / MC-vs-editing / editing↔story concerns). Phase 5.2 (Representation Design) needs Phase 3 + 5.1; it produces the hero-highlight + scene-template convention (resolves the user's cast/hero-representation concern). Both are review-checkpoints, not requirement-delivery phases.
- [Phase 4]: Highest technical-risk phase — the `alter`→`sort` silent-corruption trap (Pitfall 6) bites here. The `cmd.create` pitfall (Pitfall 3) is now EMPIRICALLY CORRECTED (03-01): the "no-op" claim did not reproduce; real gotchas are 1,1-drops-multi-state + destructive-self-copy + default-args-working. Phase 4 restore uses default-args `cmd.create(backup, source)` (all states). Address the alter→sort trap on day one of Phase 4 with the `apply_edit` helper + backup-snapshot pattern.
- [Phase 6]: First human-verify milestone — Qt/GUI cannot be exercised from WSL (Pitfall 2). Manual GUI test matrix begins here. Now implements the reviewed Phase 5.1 + 5.2 design artifacts rather than inventing them inline. Plugin loader should also call `c14.paths.selfcheck()` at startup (Pitfall 1 mitigation — fail loud on broken bundled layout); the helper is designed for this and the Phase 1 test is the first caller.
- [Phase 11]: Documentation finalization + verification is the LAST release gate, after Phase 10's content polish. It depends on Phase 10 being complete (playtest-driven content changes settled) so docs reflect final shipped content. It owns 0 new requirements — verifies/updates DOC-01, DOC-02 against shipped reality.
- [Coverage]: REQUIREMENTS.md previously stated "34 total" v1 requirements; actual enumerated v1 set is 32 (PATH-01, STAT-01 are v2). Traceability uses 32. The 5.1/5.2/11 phases own 0 requirements — coverage unchanged at 32/32.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 001 | Resolve Pitfall 4 (C14/ATP carbon-fate conflict) — adopt soul-jump reframing (electrons-as-soul → ETC → ATP, tied to RNG TCA shuffle) + cleanup wrong claims across planning docs | 2026-08-13 | 7b6119c | [001-resolve-pitfall-4-c14-atp-carbon-fate-co](./quick/001-resolve-pitfall-4-c14-atp-carbon-fate-co/) |

## Session Continuity

Last session: 2026-08-14 (Phase 3 execution — Plan 03-01 GATE complete: headless bridge proven, harness + sentinel + citation convention established)
Stopped at: Completed 03-01-PLAN.md (api-sanity smoke PASSED: 10/10 cmd.* stages green via SMOKE_RESULT sentinel; 22 source-citations; tools/run_headless.sh + bundled _smoke.pdb + gitignore delivered; PITFALLS.md Pitfall 3 empirically corrected). Next: Plan 03-02 (AssetManager) + 03-03 (MolOps), both reuse this harness.
Resume file: None
