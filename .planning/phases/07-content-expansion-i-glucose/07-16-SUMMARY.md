---
phase: 07-content-expansion-i-glucose
plan: 16
subsystem: testing (cross-cutting content-invariant suite)
tags: [content-invariants, citation-gate, edit-coverage, two-layer-text, claim-hygiene, seeded-determinism, design-b, restoration-arc, edit-router, reachability]

# Dependency graph
requires:
  - phase: 07-13 (TCA content + D5 promotion)
    provides: the design-B shuffle semantics (0.5/0.5 exit-position/retained labels), the 13th edits.json bucket (tca.akg_dh), test_15_edit_allowed_nodes, and the citation-gate residual = exactly the 2 Phase-8 stubs
  - phase: 07-12 (restoration topology)
    provides: gly.pfk_restored / tca.aconitase_restored nodes with the plan-12 [edit, load, align, show_as] on_enter shape
  - phase: 07-14 (edits.json signatures)
    provides: the 13-bucket edits.json (round-trip + validate_edits_table surfaces)
  - phase: 07-15 (cast.json + scene templates)
    provides: cast.json 12 real enzymes (coverage exit 0)
  - phase: 07-11 (counts owner) + 07-05 (registry landing)
    provides: 57/21 invariants in tests/test_glucose_reachability.py; data/citations.json all-approved except the 2 sanctioned stubs
provides:
  - "tests/test_glucose_content.py: 19-test cross-cutting suite enforcing the phase release conditions in CI (two-layer, no-TBD, claim hygiene, gate residual form, coverage, validate, 13-signature round-trip, design-B determinism, restoration arc, manifest relationships)"
  - "The DOCUMENTED design-B fate mapping pinned at engine level: seed 42 -> tca.co2_turn2 ('retained aboard'); both fates occur across seeds; tca.shuffle is the graph's ONLY weighted node"
  - "Reachability invariants converged to the 57-node reality (docstring refs to the 07-13-renamed test fixed)"
  - "05.1-DESIGN.md + regenerated diagram synced to 15 edit-allowed (post-D5) — the 07-13 flagged residual discharged"
affects: [plan 17 (human-verify — the suite is its automated complement), plan 18/19 (phase-final verification runs this suite + gates), phase 8+ (the invariant suite auto-covers new FA/alcohol content the same way)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Residual-zero-except-documented-stubs gate assertion: subprocess gate run asserting exit 1 with EXACTLY the sanctioned [MISSING] lines and 0 [UNAPPROVED] — pins the documented stub residual instead of fabricating approvals"
    - "Registry cross-check twin: in-process CitationRegistry.is_approved walk over every non-stub claim reference + a negative pin that PLACEHOLDER_PHASE8 is NOT registered (no-fabricated-approval guard)"
    - "Engine-level determinism pin: documented fate via full choice[0] walk (proves zero RNG draws en route) + goto/choose at the mixed shuffle node (the controller's real entry) + only-weighted-node graph scan"
    - "Manifest set-relationship pin: cast(12) subset-of edits(13) == distinct edit:enzyme tag values(14) - {tca.citrate_synthase}"

key-files:
  created:
    - "tests/test_glucose_content.py"
  modified:
    - "tests/test_glucose_reachability.py (2 stale docstring refs to the pre-rename test_14_edit_allowed_nodes)"
    - ".planning/phases/05.1-story-graph-design-glucose-skeleton-integration-contracts/05.1-DESIGN.md (14->15 edit-allowed sync)"
    - ".planning/phases/05.1-story-graph-design-glucose-skeleton-integration-contracts/05.1-graph.txt + .svg (regenerated)"
    - "tools/render_story_graph.py (legend count derived, not hardcoded)"

key-decisions:
  - "Two-layer/TBD exemption set = {edit.prompt} ONLY (the 05.1-DESIGN-documented structural stub, never player-rendered); fa.stub/alc.stub asserted WITH text (07-04 authored honest Phase-8 notices) — stricter than the plan's original exemption list"
  - "Gate residual form: exit 1 with EXACTLY the 2 documented stub MISSING lines + 0 UNAPPROVED (orchestrator-sanctioned interpretation of the plan's 'gate exit 0'); PLACEHOLDER_PHASE8 deliberately NOT registered (would fabricate approval); gate tool untouched"
  - "Documented design-B fate = seed 42 -> tca.co2_turn2 (retained; first draw 0.6394 > 0.5 cumulative threshold) — the research's illustrative 'seed 42 -> co2_turn1' guess corrected by pinning reality"
  - "Host-O2 RNG event dropped from the determinism group: it was never implemented (07-01 DC-B made pyr.branch an explicit player choice); replaced by the only-weighted-node graph pin"

patterns-established:
  - "Content-invariant suite as CI: 'no fabricated science + no placeholder residue' is now machine-enforced (tests/test_glucose_content.py), complementing the Phase-1 gate"
  - "Doc-sync pattern: regenerated artifact + count/roster sync with bracketed [Post-D5 ...] historical notes, changelogs kept verbatim"

# Metrics
duration: 19 min
completed: 2026-09-03
---

# Phase 7 Plan 16: Cross-cutting content-invariant suite Summary

**19-test content-invariant suite (tests/test_glucose_content.py) turns "no fabricated science + no placeholder residue" into CI — two-layer/TBD scans, claim hygiene with the sanctioned 2-stub gate-residual form, edit-coverage + validate clean, 13-signature edit round-trip, design-B seeded determinism (seed 42 -> retained), restoration-arc mock-sink proof — plus reachability docstring convergence and the 05.1 DESIGN/diagram sync to 15 edit-allowed.**

## Performance

- **Duration:** 19 min
- **Started:** 2026-09-03T04:13:29Z
- **Completed:** 2026-09-03T04:32:36Z
- **Tasks:** 2 of 2 (+ the assigned doc-sync commit)
- **Files modified:** 6 (1 created, 5 modified)

## Accomplishments

- **tests/test_glucose_content.py (19 tests, all green against the real bundle):** (1) two-layer non-empty on all 56 player-facing nodes; (2) no-TBD scan over text + choice labels; (3) claim hygiene — 0 PLACEHOLDER_PHASE7*, PLACEHOLDER_PHASE8 only on fa.stub/alc.stub, every other reference approved via in-process registry cross-check + the no-fabricated-approval negative pin; (4) citation gate subprocess — exit 1 with exactly the 2 documented MISSING lines, "2 missing + 0 unapproved", bare invocation exit 2; (5) coverage tool exit 0 (12/12) + scan_edit_coverage green + validate_edits_table clean vs the real 57-node graph; (6) all 13 edits.json signatures round-trip to their recorded, EXISTING branch nodes; (7) design-B determinism — seed 42 -> tca.co2_turn2 via a full choice[0] engine walk (proving zero RNG draws en route), same-seed repro, both fates over 30 seeds, shuffle = only weighted node; (8) restoration arc — gly.pfk known edit routes to gly.pfk_restored whose on_enter is the plan-12 [edit, load pdb:4PFK, align(super), show_as], delivered to a mock sink in order; plus (9) the shared-manifest relationship pin cast(12) ⊆ edits(13) == tags(14) − {tca.citrate_synthase}.
- **Reachability file converged:** 57/21/4-tier/15-edit-allowed/D5 invariants verified intact (07-11/12/13 had already landed them); only residue was 2 docstring references to the pre-rename test_14_edit_allowed_nodes — fixed. No speculative additions.
- **Assigned doc-sync discharged (the 07-13 flagged residual):** 05.1-DESIGN.md updated wherever the edit-allowed count/roster appears — §4 facets (5 edit-allowed-class + 10 both-class incl. tca.akg_dh), §5 table 14 → 15 rows with the new tca.akg_dh row (edit:enzyme:tca.akg_dh + edit:offer, DIS-OGDH-01-cand OGDH P189L with the mandatory evidence-tier caveat, 07-14 exploration-routing branch tca.succinyl_coa_synthetase, no restored node), invariant-list item 7, SC5-inventory row 26 (MC-choice → both, PROMOTED post-D5). Historical changelogs kept verbatim with bracketed [Post-D5 …] notes. Diagram regenerated (57 nodes / 15 edit-allowed / authored content).
- **Full verification green:** 345 tests OK (326 baseline + 19 new); coverage exit 0; gate exit 1 (the sanctioned residual form, now machine-pinned).

## Task Commits

Each task was committed atomically:

1. **Task 1: Author tests/test_glucose_content.py** — `fefc3a6` (test)
2. **Task 2: Finalize reachability invariants (docstring convergence)** — `da851f6` (test)
3. **Assigned doc-sync: DESIGN + diagram to 15 edit-allowed** — `dd67177` (docs; includes the render-tool legend auto-fix)

**Plan metadata:** (this commit — `docs(07-16): complete cross-cutting content-invariant suite plan`)

## Files Created/Modified

- `tests/test_glucose_content.py` — NEW: the 19-test cross-cutting content-invariant suite (8 plan groups + manifest relationships + stub-marker honesty)
- `tests/test_glucose_reachability.py` — 2 stale docstring refs (test_14_edit_allowed_nodes → test_15_edit_allowed_nodes); assertions verified already converged
- `.planning/phases/05.1-story-graph-design-glucose-skeleton-integration-contracts/05.1-DESIGN.md` — 14 → 15 edit-allowed sync (counts, roster, new akg_dh row, invariant list, SC5 row 26)
- `.planning/phases/05.1-story-graph-design-glucose-skeleton-integration-contracts/05.1-graph.txt` / `.svg` — regenerated (57 nodes, 95 edges, 15 edit-allowed)
- `tools/render_story_graph.py` — legend edit-allowed count now DERIVED via node_style (was hardcoded "(14)", contradicting its own Summary line after any graph growth)

## Decisions Made

- **Exemption set for the two-layer/TBD scans is {edit.prompt}, not {fa.stub, alc.stub}.** The plan's context exempted fa.stub/alc.stub "as documented stubs", but ground truth shows 07-04 authored honest two-layer Phase-8 notice text on both — they pass the invariant and are asserted WITH the rest (stricter). The only empty-text/TBD node is edit.prompt, whose text_dramatic IS the documented `[STRUCTURAL STUB:…]` marker (05.1-DESIGN rows 55/138; never rendered — the controller intercepts edit.prompt → EditDialog). A stub-marker honesty test justifies the exemption and lifts it automatically if the marker is removed.
- **Gate assertion = the sanctioned residual form, not literal exit 0.** Per the orchestrator ground truth (and the plan's own truth #2), the real bundle exits 1 with EXACTLY the 2 documented stub MISSING lines and 0 UNAPPROVED. Registering PLACEHOLDER_PHASE8 as approved (to force exit 0) was explicitly forbidden — that would fabricate approval. The gate tool itself is untouched (Phase-1 scope).
- **Documented design-B fate pinned to reality: seed 42 → tca.co2_turn2 ("retained aboard").** The research §10 example ("e.g. seed 42 → co2_turn1") was an illustrative guess; the real first draw for seed 42 is 0.6394 > the 0.5 cumulative threshold. The mapping is now documented here, in the test docstrings, and pinned by test.
- **Determinism scope = the shuffle alone.** The host-O2 RNG event from research §7 was never implemented (07-01 DC-B: pyr.branch is an explicit player choice; both pyr.branch conds removed). The test group pins "tca.shuffle is the graph's ONLY weighted node" instead — any new weighted node must update that pin + the documented fate.
- **Engine-level determinism via goto+choose at the shuffle** — engine.goto is the controller's real entry for non-weighted choices at a mixed node (per engine.py docstring), and choose() performs the interpreter's weighted pick; the Phase-6 controller itself is UI-layer and out of scope, exactly as directed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plan's two-layer exemption list incomplete vs reality (edit.prompt)**
- **Found during:** Task 1 (group 1 authoring)
- **Issue:** The plan exempted fa.stub/alc.stub, but both have authored text; the only node failing two-layer non-empty is edit.prompt (documented 05.1 structural stub with empty teaching + "TBD —" marker dramatic). A literal implementation would false-fail on a never-rendered infrastructure node — and the same node is the bundle's single "TBD" residue, so the group-2 scan needed the same exemption.
- **Fix:** Exemption = DOCUMENTED_STUB_NODES = ("edit.prompt",); fa.stub/alc.stub asserted with text; added test_edit_prompt_stub_marker_is_honest tying the exemption to the [STRUCTURAL STUB: marker.
- **Files modified:** tests/test_glucose_content.py
- **Verification:** 19/19 green; the exemption is self-documenting
- **Committed in:** fefc3a6

**2. [Rule 1 - Bug] render_story_graph.py legend hardcoded "(14)"**
- **Found during:** Assigned doc-sync (diagram regeneration)
- **Issue:** The regenerated ASCII diagram's legend still read "[EDIT] = edit-allowed (14)" while the tool's own Summary line correctly computed 15 — a hardcoded literal that can never agree with the computed count after graph growth.
- **Fix:** Legend count now derived via the same node_style predicate _ascii_summary uses; regenerated the diagram.
- **Files modified:** tools/render_story_graph.py, 05.1-graph.txt, 05.1-graph.svg
- **Verification:** legend + Summary both say 15; suite 345 OK
- **Committed in:** dd67177

**3. [Rule 3 - Blocking] Stale docstring refs to the renamed reachability test**
- **Found during:** Task 2 (convergence verification)
- **Issue:** Two docstrings still referenced test_14_edit_allowed_nodes (renamed test_15_edit_allowed_nodes by 07-13's D5 promotion) — the assertions themselves were already converged.
- **Fix:** Updated both references with rename provenance.
- **Files modified:** tests/test_glucose_reachability.py
- **Verification:** full suite 345 OK
- **Committed in:** da851f6

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking)
**Impact on plan:** All three were convergence realities the plan's "verify current state, adjust ONLY if a prior plan left a count stale" mandate anticipated. No scope creep; no engine/dependency/gate changes.

## Issues Encountered

- **The plan frontmatter truth "Citation gate exits 0" is not achievable within scope** — the 2 PLACEHOLDER_PHASE8 stub references are 07-01-sanctioned Phase-8 content and the orchestrator forbade registering them or touching the gate. Implemented + pinned the sanctioned "residual-zero-except-documented-stubs" form instead (orchestrator ground truth #1). Plan 17/18 should treat gate exit 1-with-2-documented-stubs as the phase-green state, or a Phase-8 plan resolves the stubs to reach literal exit 0.
- **Observation (not acted on, per "keep everything else verbatim"):** 05.1-DESIGN.md's reachability-invariant list item 4 still describes the Phase-5.1-era state ("55 nodes … test_manifest_loads_all_55_nodes") — the live test is test_manifest_loads_all_57_nodes (renamed by 07-12). Out of the doc-sync's edit-allowed scope; flagged for the orchestrator.
- **Mock-sink is cumulative** (start() dispatches intro.preface's on_enter first) — the restoration-arc test isolates the dispatch under test with `del sink[:]` (documented in the test).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Plan 17 (human-verify):** the automated complement is in place — the human sessions should exercise exactly what this suite pins: the shuffle RNG (seeded classroom demo: seed 42 → "retained aboard"), the gly.pfk restoration reveal (4PFK, chain-A), the akg_dh EditDialog (resi-189 restore option), and the citation-gate residual explanation (2 Phase-8 stubs are sanctioned).
- **Plan 18/19 (phase-final):** run `python3.6 -m unittest discover -s tests` (345 OK), `tools/check_citations.py --story data/story_glucose --registry data/citations.json` (expect exit 1 + exactly 2 documented MISSING + 0 UNAPPROVED), `tools/check_edit_coverage.py` (exit 0), `tools/check_imports.py` + `tools/check_alter_gate.py` (exit 0 — unchanged this plan), zip rebuild + sanity.
- **Phase 8+ (FA/alcohol content):** tests/test_glucose_content.py auto-covers new story files via the graph walk; new weighted nodes will trip test_shuffle_is_the_only_weighted_node by design (update the pin + documented fate when a second RNG surface lands); new enzymes should extend cast ⊆ edits relationships (test_manifest_relationships pins the shape, not the ids, except the two named exceptions).
- No blockers carried forward from this plan.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-03*
