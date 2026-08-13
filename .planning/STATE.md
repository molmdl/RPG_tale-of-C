# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-12)

**Core value:** The player experiences cellular respiration as a story with consequences — every choice and edit on the C14 hero either advances them toward a destiny (ATP [the hero's electrons harvested into energy via the ETC], storage, CO2, or catastrophe) or diverts them into a branch, with real PDB proteins as the cast and scientifically validated chemistry as the plot.
**Current focus:** Phase 2 — Story Engine Core (Architecture Proof in WSL) — Phase 1 verified ✓ (15/15 must-haves passed)

## Current Position

Phase: 1 of 13 (Foundations & Testability Boundary + Citation Gate) — COMPLETE ✓
Plan: 3 of 3 complete in current phase (01-01 + 01-02 + 01-03 all done — Wave 1 + Wave 2)
Status: Phase complete + verified (15/15 must-haves passed; VERIFICATION.md status: passed)
Last activity: 2026-08-13 — Phase 1 verification passed; ROADMAP + REQUIREMENTS updated (PLGN-03, CITE-02, DOC-04 → Complete); ready for Phase 2

Progress: [███░░░░░░░░] ~6% (3 plans complete; overall total TBD — most phases not yet planned)

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: 19 min
- Total execution time: 0.93 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundations & Citation Gate | 3/3 ✓ | 56 min | 19 min |

**Recent Trend:**
- Last 5 plans: 01-01 (32 min), 01-03 (20 min), 01-02 (4 min)
- Trend: Wave 2 plans faster than Wave 1 (reference designs pre-verified on 3.6.9; near-verbatim adoption + read-only verification; no debugging needed)

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

### Pending Todos

None yet.

### Blockers/Concerns

Issues that affect future work:

- [Phase 5]: 4 science-framing Key Decisions gate content authoring. Pitfall 4 (ATP/True-Ending carbon-fate reframing) is now RESOLVED (2026-08-13, via the soul-jump reframing — electrons-as-soul harvested into ATP via ETC after the RNG-weighted TCA path; carbon body released as CO2; see PROJECT.md Key Decisions). The remaining 3 are HOW decisions for the human, still Pending: C14-decay timescale (Pitfall 9); anaerobic framing; batch-vs-per-claim approval. They are flagged as Phase 5 tasks. Start this track early — it is the timeline-domininating risk (Pitfall 7). The anaerobic decision now specifically gates Phase 5.1 (Story Graph Design); the ATP/True-Ending decision (resolved) no longer blocks it.
- [Phase 5.1 / 5.2 (INSERTED)]: Two design phases gate Phase 6. Phase 5.1 (Story Graph Design) needs Phase 2 + the Phase 5 ATP decision [now RESOLVED via soul-jump — electrons-as-soul → ATP via ETC after RNG-weighted TCA path; True-ending node = electron harvest, NOT carbon-becomes-ATP]; it produces the glucose skeleton + MC-choice/edit-node integration contracts (resolves the user's story-design / MC-vs-editing / editing↔story concerns). Phase 5.2 (Representation Design) needs Phase 3 + 5.1; it produces the hero-highlight + scene-template convention (resolves the user's cast/hero-representation concern). Both are review-checkpoints, not requirement-delivery phases.
- [Phase 4]: Highest technical-risk phase — the `alter`→`sort` silent-corruption trap (Pitfall 6) and `cmd.create` no-op trap (Pitfall 3) bite here. Address on day one of Phase 4 with the `apply_edit` helper + backup-snapshot pattern.
- [Phase 6]: First human-verify milestone — Qt/GUI cannot be exercised from WSL (Pitfall 2). Manual GUI test matrix begins here. Now implements the reviewed Phase 5.1 + 5.2 design artifacts rather than inventing them inline. Plugin loader should also call `c14.paths.selfcheck()` at startup (Pitfall 1 mitigation — fail loud on broken bundled layout); the helper is designed for this and the Phase 1 test is the first caller.
- [Phase 11]: Documentation finalization + verification is the LAST release gate, after Phase 10's content polish. It depends on Phase 10 being complete (playtest-driven content changes settled) so docs reflect final shipped content. It owns 0 new requirements — verifies/updates DOC-01, DOC-02 against shipped reality.
- [Coverage]: REQUIREMENTS.md previously stated "34 total" v1 requirements; actual enumerated v1 set is 32 (PATH-01, STAT-01 are v2). Traceability uses 32. The 5.1/5.2/11 phases own 0 requirements — coverage unchanged at 32/32.

## Session Continuity

Last session: 2026-08-13 (Phase 1 Plan 02 execution — Wave 2, parallel with 01-03; both now complete)
Stopped at: Completed 01-02-PLAN.md — c14.paths resolver + CWD-independence test + DOC-04 verification. Phase 1 is now COMPLETE (all 3 plans done: 01-01 + 01-02 + 01-03).
Resume file: None
