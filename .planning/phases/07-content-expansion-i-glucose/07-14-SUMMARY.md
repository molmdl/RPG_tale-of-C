---
phase: 07-content-expansion-i-glucose
plan: 14
subsystem: edit-routing
tags: [edits-json, edit-router, reverse-mutation, restoration-ux, branch-routing, signature-contract, pfkm, aco2, pdha1, pklr, ndufs8, sdha, cyc1, cox4i1]

# Dependency graph
requires:
  - phase: 07-content-expansion-i-glucose (07-12)
    provides: "gly.pfk_restored + tca.aconitase_restored node ids (the two FIXED branch_node targets) + the aconitase human S112 ↔ 1ACO resi-85 mapping + the chain-case empirical rule"
  - phase: 07-content-expansion-i-glucose (07-02, 07-04)
    provides: "Batch-A allele choices (PFKM G209D framing, PKLR R479H, PDHA1 V138M mature/PDB numbering) + batch-C ETC choices (CYC1 L215F→resi 131 chain D→LEU; COX4I1 PDB numbering resi 130 chain D→PRO; NDUFS8 resi 68 chain I→ARG; SDHA resi 512 chain A→ARG)"
  - phase: 07-content-expansion-i-glucose (07-RESEARCH-content-mechanics.md §4)
    provides: "The edits.json schema + authoring rules (lowercase targets, new_res arg, op whitelist, duplicate-signature rule, branch_node existence contract)"
provides:
  - "Complete rpg/data/edits.json: 12 enzyme buckets, each with 1 known-correct reverse-mutation signature + branch routing — the EditDialog's 'correct fix' options are built verbatim from these signatures"
  - "MANDATORY per-bucket branch_node table (below) — plan 16/17 consume it for round-trip + human-verify checks"
  - "M5 discharged: NO known-wrong 1b entries anywhere (per 07-01 decision #4); M3 partially discharged: fixture_enzyme_1 deleted from edits.json (its test-fixture twin lives in tests/fixtures/edit_routing/)"
  - "Local coordinate verification: 7FS3 resi 479 = ARG on ALL 8 chains; 6CFO chain A resi 138 = VAL; 1OCC chain D resi 130 = PRO; 4PFK resi 209 = HIS (framing note confirmed); 1ACO chain A resi 85 = SER"
affects: [plan 15 (cast.json rewrite — coverage tool flags its 2 placeholder ids), plan 16 (durable validate-vs-real-graph tests + 57/21 re-pin), plan 17 (human-verify the edit dialog + reveals), plan 13 (tca.akg_dh promotion adds a 14th bucket — see watch items)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Canonical signature form: op ∈ point_mutation|substrate_edit|protonation_change; target written ALREADY LOWERCASE; point_mutation args key = new_res; claim_id = the DIS-* claim verbatim (-cand kept)"
    - "Exploration-enzyme routing: known-correct edit routes to the enzyme node's own main-path successor (existing node; re-entering fires its on_enter — mechanics §4.4); no restoration node, no on-structure edit"

key-files:
  created: []
  modified:
    - "rpg/data/edits.json (sole writer this phase; 15 lines → 103 lines)"

key-decisions:
  - "tca.citrate_synthase gets NO edits.json entry BY DESIGN (edit:structural, no implementable disease claim — tca §6.1: 0 natural variants; roster invariant is cast-ids ⊆ edits-keys, a subset)"
  - "Exploration-enzyme branch_node = the enzyme node's own main-path successor (existing node, per plan); tca.malate_dh routes to tca.divert_to_good (the forward soul-path) over the tca.shuffle loop-back — rationale recorded below"
  - "Signature targets written LOWERCASE ('resi 85 and chain a') per the must_haves + research §4.1; EditIntent.signature() lowercases both sides so routing is case-independent (round-trip + uppercase-intent variants verified)"
  - "Chain-less targets for the 5 plan-specified buckets (gly.pyruvate_kinase 'resi 479', tca.isocitrate_dh 'resi 204', tca.succinyl_coa_synthetase 'resi 85', tca.fumarase 'resi 233', tca.malate_dh 'resi 37') — no chain clause asserted where the plan gave none (narrative-only nodes / numbering caveats)"
  - "IDH3A signature = resi 204 → MET (reverse of M204I = I204M, per the registry claim_text 'IDH3A M204I ... alternate R316C'); the plan text's 'M204I→I' read as the truncated reverse-mutation name, consistent with the research table 'M204I→I204M' and 07-03 D4"

patterns-established:
  - "Per-bucket branch_node documentation table as the plan-16/17 contract (recorded in this SUMMARY)"

# Metrics
duration: 3 min
completed: 2026-09-03
---

# Phase 7 Plan 14: edits.json signatures (12 buckets + branch routing) Summary

**All 12 real mutable-enzyme buckets authored in rpg/data/edits.json with canonical lowercase reverse-mutation signatures (new_res args, verbatim DIS-*-cand claim_ids), PFK/aconitase routed to the plan-12 restored nodes, 10 exploration enzymes routed to their own main-path successors, fixture deleted, CS excluded by design — validate_edits_table clean against the real 57-node graph, all 12 signature round-trips route known→branch_node, 325 tests OK.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-09-02T20:00:22Z
- **Completed:** 2026-09-02T20:02:58Z
- **Tasks:** 2 of 2
- **Files modified:** 1 (rpg/data/edits.json)

## Accomplishments

- **edits.json is now the restoration UX data source**: every bucket carries ≥1 known-correct entry whose `(op, target, args)` the EditDialog offers verbatim as "Restore <target> to <new_res> (the correct fix)" — filling this file WAS wiring the correct-fix choice.
- **Restoration-arc routing landed**: gly.pfk → `gly.pfk_restored` (claim DIS-PFKM-01-cand) and tca.aconitase → `tca.aconitase_restored` (claim DIS-ACO2-01-cand, sele per the 07-12 mapping verbatim) — the branch_node ids the plan-12 nodes were built for.
- **M5 discharged** (07-01 decision #4): zero known-wrong 1b entries — the dialog's "correct fix" label is honest for every entry.
- **M3 half-discharged**: `fixture_enzyme_1` deleted from edits.json (the test-fixture twin remains in `tests/fixtures/edit_routing/`); cast.json itself is plan 15's file.
- **Verified against the real graph, not just the schema**: `validate_edits_table` returns [] on the loaded 57-node StoryGraph (no dangling branch_node, no dangling pool nodes, pool nodes are endings, no duplicate signatures); every signature round-trips (EditIntent built from the table routes to its branch_node; uppercase-target intents route identically).

## THE PER-BUCKET BRANCH_NODE TABLE (plan 16/17 consume this)

| # | enzyme_id | signature target (as authored, lowercase) | new_res | reverse of (disease allele) | claim_id | branch_node | successor rationale |
|---|-----------|--------------------------------------------|---------|------------------------------|----------|-------------|---------------------|
| 1 | `gly.pfk` | `resi 209 and chain a` | GLY | PFKM G209D → D209G (recorded framing; 4PFK resi 209 is HIS) | DIS-PFKM-01-cand | `gly.pfk_restored` | plan-12 restored node (fixed contract) |
| 2 | `gly.pyruvate_kinase` | `resi 479` | ARG | PKLR R479H → H479R | DIS-PKLR-01-cand | `gly.pyruvate` | node's main-path successor (both choices goto it) |
| 3 | `pyr.pdh` | `resi 138 and chain a` | VAL | PDHA1 V138M → M138V (PDB/mature numbering) | DIS-PDHA1-01-cand | `tca.entry` | node's main-path successor ("Continue into the TCA cycle") |
| 4 | `tca.aconitase` | `resi 85 and chain a` | SER | ACO2 S112R → R112S (07-12 mapping: human S112 ↔ 1ACO chain A resi 85) | DIS-ACO2-01-cand | `tca.aconitase_restored` | plan-12 restored node (fixed contract) |
| 5 | `tca.isocitrate_dh` | `resi 204` | MET | IDH3A M204I → I204M (alt R316C per 07-03 D4 — not selected) | DIS-IDH3A-01-cand | `tca.akg_dh` | node's main-path successor (both non-edit choices goto it) |
| 6 | `tca.succinyl_coa_synthetase` | `resi 85` | GLY | SUCLG1 G85A → A85G | DIS-SUCLG1-01-cand | `tca.fumarase` | node's main-path successor (narrative-only node, no PDB → chain-less target) |
| 7 | `tca.fumarase` | `resi 233` | ARG | FH R233H → H233R | DIS-FH-01-cand | `tca.malate_dh` | node's main-path successor (narrative-only node) |
| 8 | `tca.malate_dh` | `resi 37` | GLY | MDH2 G37R → R37G | DIS-MDH2-01-cand | `tca.divert_to_good` | main-path successor = the forward soul-path (see decision note below) |
| 9 | `etc.complex_i` | `resi 68 and chain i` | ARG | NDUFS8 R102H → H102R (PDB resi 68 = human 102 − 34 transit) | DIS-NDUFS8-01-cand | `etc.complex_ii` | node's main-path successor ("Continue down the chain") |
| 10 | `etc.complex_ii` | `resi 512 and chain a` | ARG | SDHA R554W → W512R (PDB resi 512 = human 554 − 42) | DIS-SDHA-01-cand | `etc.complex_iii` | node's main-path successor |
| 11 | `etc.complex_iii` | `resi 131 and chain d` | LEU | CYC1 L215F → F215L / F131L (PDB resi 131 = human 215 − 84; 07-04 D3 allele choice) | DIS-CYC1-01-cand | `etc.complex_iv` | node's main-path successor |
| 12 | `etc.complex_iv` | `resi 130 and chain d` | PRO | COX4I1 P152T → T130P (PDB resi 130 = human 152 − 22; 07-04 D4 PDB-numbering mandate) | DIS-COX4I1-01-cand | `etc.atp_synthase` | node's main-path successor ("Continue to ATP synthase") |

**tca.malate_dh routing note:** the node has two non-edit exits — `tca.shuffle` (the RNG loop-back) and `tca.divert_to_good` (the forward path to the ETC fork). "Main-path successor" = `tca.divert_to_good`: it is the linear path toward the True ending, and re-entering `tca.shuffle` would throw the player into another 50/50 RNG draw after a *correct* fix. Recorded here for plan 16/17; trivial to re-point in one JSON line if the human prefers the loop-back semantics.

**Shared-bucket note:** `tca.aconitase` is the shared bucket (tca.aconitase + tca.shuffle both bind `edit:enzyme:tca.aconitase`); the single entry serves both edit points — a known signature from either node routes to `tca.aconitase_restored`.

## Task Commits

1. **Task 1: Author the 12 buckets + remove fixture** — `fabedfa` (feat)
2. **Task 2: Validate against the real graph** — verification-only (no file changes; nothing to commit). Evidence recorded above + in Verification below.

**Plan metadata:** committed separately (docs(07-14)).

## Files Created/Modified

- `rpg/data/edits.json` — 12 enzyme buckets (13 tagged minus tca.citrate_synthase), reverse-mutation signatures + branch routing; version 1 + bad_ending_pool byte-preserved; fixture_enzyme_1 removed

## Decisions Made

- **Lowercase targets in signatures** (must_haves + research §4.1) despite 07-12 writing the contract with `chain A`: `EditIntent.signature()` lowercases both sides, so routing is identical either way (both variants round-trip-tested). The case-sensitive PyMOL matching only matters for the APPLY-time sele — which comes from the branch nodes' on_enter MolActions (already landed with uppercase `chain A`/`chain D` by plans 08/09/12), not from the edits.json target.
- **Chain-less targets where the plan gave no chain** (`resi 479`, `resi 204`, `resi 85`/`resi 233`/`resi 37`): 7FS3 carries ARG479 on ALL 8 chains (chain-less selects every copy honestly); the narrative-only TCA buckets load no PDB so no chain exists to name; isocitrate_dh's cast numbering is unsettled (5GRF → 5GRE per 07-03 D3) so a chain clause would assert an unsourced mapping.
- **IDH3A new_res = MET** (reverse of M204I), read from the registry claim_text ("IDH3A M204I ... alternate R316C") + the research table's "M204I→I204M"; the plan context's "M204I→I" is the truncated reverse-mutation name, same pattern as "R102H→H(102R)".
- **tca.malate_dh → tca.divert_to_good** (main-path) over the shuffle loop-back — rationale in the table note above.

## Deviations from Plan

None - plan executed exactly as written. (Task 2 produced no file changes — verification-only — so it has no task commit; recorded here rather than creating an empty commit.)

## Issues Encountered

- **check_edit_coverage exit 1 = expected, documented-pending-plan-15**: the tool scans cast.json (still holding `fixture_enzyme_1` + `PLACEHOLDER_large_enzyme`) and flags both as lacking edits.json coverage. This is precisely the plan's forecast ("it will flag cast.json gaps — expected until plan 15"). Plan 15 rewrites cast.json to the real roster (`cast-ids ⊆ edits-keys`, excluding CS); until then the coverage gate stays red on exactly these 2 lines.
- **5GRF resi 204 = TYR (local coordinate check)**: the current isocitrate_dh cast PDB's numbering does NOT carry human IDH3A Met204 at position 204 (chains A/B both TYR) — the signature is deliberately chain-less human-numbering framing (no on-structure mapping asserted), consistent with the 07-02 PFKM text-only-fallback pattern. Watch item for plan 13 (5GRE cast swap) and plan 17 (human-verify): if a real on-structure reverse edit is ever wanted at isocitrate_dh, the human↔cast residue mapping must be derived first (the 07-12 OQ5 rule).

## Verification (reproduced)

```
python3.6 -m unittest discover -s tests 2>&1 | tail -3   → Ran 325 tests — OK
python3.6 tools/check_edit_coverage.py                    → exit 1: [MISSING] fixture_enzyme_1, PLACEHOLDER_large_enzyme (cast-side, pending plan 15)
throwaway python3.6 -c (rpg.story.model + rpg.edit_router):
  - JSON parses; version 1; bad_ending_pool exact; 12 keys; CS absent; fixture absent
  - every signature: op whitelisted, target lowercase+stripped, new_res arg present, claim_id DIS-*-cand
  - validate_edits_table(table, StoryGraph.load('data/story_glucose').all_nodes()) == []
  - all 12 branch_nodes present in the 57-node graph
  - EditIntent-from-signature routes known → branch_node for all 12 (uppercase-target variant too)
```

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Plan 15 (cast.json)** is unblocked: edits.json now defines the 12-key target set; cast.json must be rewritten to the real roster with `cast-ids ⊆ edits-keys` (CS excluded from BOTH by design; the coverage gate goes green only after cast.json stops listing the 2 placeholders).
- **Plan 16 (tests)** should add the durable versions of this plan's throwaway checks: `validate_edits_table(edits, real graph) == []` + known-edit round-trip vs the real bundle (pattern: test_edit_router.py:175-192 + TestGameEngineEditIntegration) + the per-bucket table above as the fixture for expectations.
- **Plan 17 (human-verify)**: exercise the EditDialog at gly.pfk / tca.aconitase (the two restoration arcs) and at one exploration enzyme (e.g. etc.complex_iv) — known option should read "Restore resi 209 and chain a to GLY (the correct fix)" etc.; wrong options remain the Phase-6 hardcoded resi 1/2 decoys (collision-safe: no bucket targets resi 1/2).
- **Watch items:** (1) **tca.akg_dh promotion (07-03 D5, plan 13 in flight)** will add a 14th `edit:enzyme:*` bucket (`tca.akg_dh`) — plan 13 (or 16) must add its edits.json entry (reverse of DIS-OGDH-01-cand P189L → L189P → new_res PRO, narrative-only node → chain-less target per this plan's convention) or the shared-manifest subset grows by one; plan 14's 12-bucket scope per the plan text is correct for the CURRENT graph. (2) 5GRF numbering caveat above. (3) The aconitase restored-node's own `pdb:1ACO` load + sele were probe-verified in plan 12; the 4PFK/6CFO/7FS3/1OCC chain-ID case is verified uppercase in the local cache (all PDB chain IDs checked uppercase in this session's coordinate probe) — the 5LDW/1ZOY/1BGY chain case (I/A/D) comes from the 07-04 coordinate-verified record and re-verifies at plan 17 in the real session.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-03*
