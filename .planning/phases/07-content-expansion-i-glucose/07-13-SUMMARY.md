---
phase: 07-content-expansion-i-glucose
plan: 13
subsystem: story-content (TCA cycle — text, claims, RNG-shuffle semantics, D5 promotion)
tags: [tca-cycle, rng-shuffle, design-b, isotope-surprise, succinate-symmetry, ogdh-promotion, d5, pdb-loads, citation-gate]

# Dependency graph
requires:
  - phase: 07-03 (approval batch B)
    provides: D1-D10 verdicts (D1=design B, D3=5GRE, D5=PROMOTE, D6=1ACO, D7=CS monomer+note, D8=4WLU, D9=softened IDH wording, D10=N=5 game-design) + all 20 batch-B claim approvals landed in the registry by 07-05
  - phase: 07-05 (registry landing)
    provides: data/citations.json as the source of truth (77 claims, all cited ids approved, -cand suffixes kept verbatim)
  - phase: 07-12 (restoration topology)
    provides: tca.aconitase_restored node (on_enter pinned edit→load→align→show_as; router-only entry; the derived 1ACO resi 85 ↔ human S112 mapping)
  - phase: 07-14 (edits.json signatures)
    provides: the 12-bucket schema + the exploration-enzyme branch_node convention (route to the enzyme node's own main-path successor) + the chain-less-target rule for narrative-only nodes
provides:
  - "data/story_glucose/tca.json fully authored: 12/12 nodes two-layer text on approved claims only, 0 placeholders (tca citation-gate bucket 9→0)"
  - "Design-B shuffle: TCA-RNG-WEIGHT-02-cand + TCA-CARBON-FATE-01-cand bound at tca.shuffle (WEIGHT-01 superseded at this node only, stays approved); weighted choice labels re-anchored to exit-position/retained; isotope-surprise teaching beat at isocitrate_dh/akg_dh/co2_turn1/co2_turn2"
  - "D5 promotion implemented end-to-end: edit:enzyme:tca.akg_dh tag + edit:offer choice + edits.json 13th bucket (resi 189→PRO, branch tca.succinyl_coa_synthetase) + invariant test 14→15 — all in this one plan per the 07-03 obligation"
  - "PDB loads per batch B: tca.aconitase pdb:1ACO (D6), tca.isocitrate_dh pdb:5GRE (D3), tca.malate_dh +pdb:4WLU (D8); CS keeps 1CSC AU monomer + homodimer teaching note (D7)"
  - "Derived numbering bridges (pure-stdlib, RCSB+UniProt live): 5GRE chain-A resi 177 = human IDH3A M204 (PDB = UniProt − 27, 100% NW identity); 4WLU resi 37 = GLY (direct alignment)"
affects: [plan 16 (cross-cutting tests: re-pin 15 edit-allowed + design-B seeded-fate mapping + diagram regen), plan 17 (human-verify: TCA reveals + shuffle RNG + akg_dh EditDialog), phase 8+ (FA synthesis picks up the citrate-export exit), plan 15 residuals (none — completed in parallel)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Design-B shuffle authoring: game-design weight VALUE stays 0.5/0.5 while choice labels + texts re-anchor to the succinate-symmetry scramble (exit position vs retained) — value and semantics separated per D1"
    - "Evidence-tier honesty in teaching text: single-submitter/no-assertion-criteria caveat written INTO the OGDH disease paragraph (registry review_notes → review wording per D5)"
    - "Rejected PDBs never named in player-facing text (5GRF omitted; registry provenance only) — the 07-06 2OZL precedent"
    - "Registered-but-dormant cast records disclosed in text with a no-reveal-mechanics reason (6WCV, 5UPP — the 07-08 2VGG/6CER dormant pattern)"

key-files:
  created:
    - ".planning/phases/07-content-expansion-i-glucose/07-13-SUMMARY.md"
  modified:
    - "data/story_glucose/tca.json (12/12 nodes authored; 5 sanctioned structural changes; 0 placeholders)"
    - "tests/test_glucose_reachability.py (test_15_edit_allowed_nodes; offer bound 15; D5 docstrings)"
    - "rpg/data/edits.json (13th bucket tca.akg_dh)"

key-decisions:
  - "Shuffle claims swapped per D1: [TCA-RNG-WEIGHT-02-cand, TCA-RNG-CITRATE-PROCHIRALITY-01, TCA-CARBON-FATE-01-cand]; WEIGHT-01 stays registered/approved, superseded at this node only"
  - "Shuffle weighted LABELS re-anchored (exit position / retained) — sanctioned by research §8 ('weights, texts, claim_ids, and re-anchored labels are all JSON'); weights/conds/gotos/tags byte-untouched"
  - "tca.aconitase_restored claim_ids [] → [DIS-ACO2-01-cand] per the 07-12 swap contract ('text + claim swaps are plans 08/13'), mirroring 07-08's gly.pfk_restored precedent"
  - "akg_dh edits.json bucket: chain-less 'resi 189' → PRO; branch_node = own main-path successor tca.succinyl_coa_synthetase (07-14 exploration convention); NO restored node for OGDH"
  - "OGDH disease text carries the MANDATORY evidence-tier caveat in review wording (single-submitter, no assertion criteria, literature-only) — 'a confirmed pathogenic mutation, with that provenance stated'"
  - "4WLU load added to malate_dh (D8 recorded+approved); resi-37 numbering verified directly aligned (no bridge needed); 5GRE gets the −27 bridge documented in teaching text"

patterns-established:
  - "Structural-half discipline: tags/on_enter/choices byte-identical vs HEAD except the 5 sanctioned changes; machine-verified by a git-show structural diff before commit"
  - "Registry-review_notes obligations discharged at authoring time (5GRE/4WLU numbering checks) via pure-stdlib PDB parse + NW alignment — no PyMOL needed for pure numbering derivations"

# Metrics
duration: 25 min
completed: 2026-09-03
---

# Phase 7 Plan 13: TCA Content + D5 Promotion Summary

**All 12 TCA nodes authored two-layer on approved claims only — design-B shuffle re-anchored (exit-position/retained labels, 0.5/0.5 untouched), the isotope-surprise beat carried at the CO2 gates, 1ACO/5GRE/4WLU loads landed, and the 07-03 D5 OGDH promotion implemented end-to-end (graph tag + edit:offer + edits.json 13th bucket + invariant test 14→15) in one plan.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-03T03:42:46Z
- **Completed:** 2026-09-03T04:08:11Z
- **Tasks:** 2 of 2 (+ the assigned edits.json bucket commit)
- **Files modified:** 3 (tca.json, test_glucose_reachability.py, edits.json)

## Accomplishments

- **12/12 nodes authored, zero placeholders.** Every dramatic/teaching paragraph traces to a bound approved claim; the tca citation-gate bucket dropped 9 → 0 (full-gate residual = exactly the 2 Phase-8 stubs, `fa.stub`/`alc.stub`, retained by the 07-01 ledger and expected by the plan-16 sweep).
- **Design B landed at the shuffle.** claim_ids → `TCA-RNG-WEIGHT-02-cand` + `TCA-RNG-CITRATE-PROCHIRALITY-01` + `TCA-CARBON-FATE-01-cand` (WEIGHT-01 remains registered/approved, superseded at this node only). Weighted choice labels re-anchored to "your carbon lands in an exit position" / "your carbon is retained aboard"; weights (0.5/0.5), conds, gotos, and tags byte-untouched. Teaching states: the scramble is the cycle's one genuinely stochastic carbon event; the trap option is a game-design cap (N=5, not a science claim — D10); the shuffle is deliberately hero-carbon-agnostic (stated simplification).
- **Isotope-surprise beat** at `isocitrate_dh`/`akg_dh` + both CO2 nodes: "the CO2 leaving derive from the recycled oxaloacetate frame, not necessarily yours" (TCA-CARBON-FATE-01-cand verbatim anchors, incl. the "requires several turns" + "might not be lost" Wikipedia sentences).
- **Loads per batch B:** aconitase `pdb:TBD_ACONITASE` → `pdb:1ACO` (D6, homology caveat + "mapping derived by real sequence alignment, never assumed"); isocitrate_dh `pdb:5GRF` → `pdb:5GRE` (D3, WT-only cast rule, no rejected id named in text); malate_dh += `pdb:4WLU` (D8). CS keeps `pdb:1CSC` with the D7 teaching note (AU monomer shown; functional enzyme is a homodimer; assembly load = engine enhancement deliberately out of scope). SCS/fumarase stay narrative-only (6WCV/5UPP registered-but-dormant, disclosed with the no-reveal-mechanics reason).
- **D5 promotion, whole arc in this plan:** `tca.akg_dh` += `edit:enzyme:tca.akg_dh` + edit:offer choice; OGDH P189L disease text with the MANDATORY single-submitter/no-assertion-criteria/literature-only caveat in review wording; `rpg/data/edits.json` 13th bucket (`resi 189` → PRO, branch_node `tca.succinyl_coa_synthetase`, claim `DIS-OGDH-01-cand` verbatim); invariant test updated to the 15-set.
- **Numbering bridges derived before authoring** (the DIS-IDH3A/DIS-MDH2 review_notes obligations): 5GRE chain-A **resi 177 = human M204** (offset −27; Needleman-Wunsch of UniProt P50213 vs the PDB ATOM sequence, 100% identity in aligned pairs, linear −27 across neighboring anchors); 4WLU **resi 37 = GLY in all 4 chains** (UniProt and PDB numbering align directly — the game's residue-37 story maps cleanly). Documented in the respective teaching texts.
- **Restored node:** text + claim swap ONLY — plan-12 on_enter `[edit → load pdb:1ACO → align(super, name CA) → show_as]` verified byte-identical vs HEAD, never redefined.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author TCA texts + swaps + loads** — `714c678` (feat)
2. **Task 2: Apply D5 outcome to the edit-allowed invariant** — `6b2f955` (feat)
3. **Assigned: add tca.akg_dh edits.json bucket per D5** — `fcf5472` (feat; own commit per the orchestrator assignment / 07-14 watch item)

**Plan metadata:** (this commit — `docs(07-13): complete TCA content plan`)

## Files Created/Modified

- `data/story_glucose/tca.json` — 12/12 nodes two-layer authored; 5 sanctioned structural changes (aconitase load 1ACO; isocitrate_dh load 5GRE; malate_dh +4WLU load; akg_dh tag + edit:offer choice; shuffle labels re-anchored); claim swap map applied exactly; restored node text+claim only
- `tests/test_glucose_reachability.py` — `test_14_edit_allowed_nodes` → `test_15_edit_allowed_nodes` (id set += `tca.akg_dh`), offer-node bound 14→15, D5 history in docstrings
- `rpg/data/edits.json` — 13th bucket `tca.akg_dh` (validate_edits_table CLEAN vs the real 57-node graph; known→`tca.succinyl_coa_synthetase` round-trip verified; wrong sele → bad pool; case-independent signature match confirmed)

## Decisions Made

- **Shuffle label re-anchor included** (beyond literal "texts"): research §8 names "re-anchored labels" as part of the data-only change set; the old "first-turn/second-turn CO2 exit" labels encoded the superseded WEIGHT-01 semantics. Weights/conds/gotos/tags untouched (verified by structural diff).
- **CAST claims bound where a load landed**: `CAST-ACO2-PDB-01-cand` on tca.aconitase, `CAST-IDH3-PDB-01-cand` on isocitrate_dh, `CAST-MDH2-PDB-01-cand` on malate_dh (mirrors the 07-08 pyruvate_kinase pattern: the load's grounding claim rides the node).
- **tca.aconitase_restored claim_ids [] → [DIS-ACO2-01-cand]**: the restoration teaching re-asserts the S112R story (the arc's "why"), per the 07-12 DESIGN addendum ("claim_ids [] — text + claim swaps are plans 08/13") and the 07-08 gly.pfk_restored precedent.
- **Rejected PDB (5GRF) never named in player-facing text** — registry provenance only (the 07-06 2OZL precedent); the teaching says "an earlier candidate carried a crystallization mutation in the regulatory γ subunit and was replaced after verification."
- **"rate-limiting" softened per D9 without naming the banned phrase** — "some tables call this the cycle's pace-setting step, but the stronger claim rests on a regulation source this game has not yet verified"; the claim's exact approved wording "a key regulatory step" is used in both layers.
- **OGDH edit framed as "a staged exploration, not an on-structure correction"** — accurate to the exploration-routing semantics (no restored node, no on_enter edit op; narrative-only node, no PDB).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Bound DIS-ACO2-01-cand on tca.aconitase_restored ([] → 1 claim)**
- **Found during:** Task 1 (restored-node authoring)
- **Issue:** The plan said "TEXT ONLY" for the restored node but the 07-12 DESIGN addendum explicitly assigns the claim swap to plans 08/13 ("claim_ids [] (text + claim swaps are plans 08/13)"), and the restoration teaching re-asserts the S112R/ICRD pinned wording — an unbound claim reference would be ungrounded.
- **Fix:** `claim_ids: [] → ["DIS-ACO2-01-cand"]`, mirroring 07-08's identical call on gly.pfk_restored.
- **Files modified:** data/story_glucose/tca.json
- **Verification:** citation gate green for the node; plan-12 on_enter byte-identical
- **Committed in:** 714c678 (Task 1)

**2. [Rule 3 - Blocking] Removed a rejected-PDB mention (5GRF) from teaching text**
- **Found during:** Task 1 (banned-phrase scan)
- **Issue:** First draft named 5GRF ("replacing 5GRF, whose γ-K151A crystallization mutation…"); 5GRF is a REJECTED registry entry — the 07-06 precedent (2OZL) keeps rejected ids out of player-facing text entirely.
- **Fix:** Rewrote the cast sentence to state the WT-only rule without naming the rejected id.
- **Files modified:** data/story_glucose/tca.json
- **Verification:** scan for rejected ids (5GRF/1C97/2B3Y/2DFD) = 0 hits
- **Committed in:** 714c678 (Task 1)

**3. [Rule 2 - Missing Critical] Discharged the 5GRE/4WLU numbering-check obligations owed by the registry review_notes**
- **Found during:** Task 1 (load authoring — the checks become load-bearing exactly when the loads land)
- **Issue:** DIS-IDH3A-01-cand notes make the 5GRE α-chain-vs-UniProt mapping a "plan 13" authoring-time task; DIS-MDH2-01-cand notes the 4WLU construct-offset check. The existing edits.json signatures (`resi 204`, `resi 37`) were authored chain-less against structures that did not yet load.
- **Fix:** Fetched 5GRE/4WLU into the gitignored runtime cache (the same files the game fetches at runtime) and derived the mappings with pure-stdlib PDB parsing + NW alignment (UniProt P50213/P40926 fetched live 2026-09-03): 5GRE chain-A resi 177 = human M204 (−27, 100% identity); 4WLU resi 37 = GLY in all chains (direct). Bridges documented in teaching text. No signature changes (exploration routing applies no on-structure edit — the 07-14 mechanics).
- **Files modified:** data/story_glucose/tca.json (text only); cache files are gitignored
- **Verification:** NW alignment cross-checked on neighboring anchors (196/200/205/210 all −27); 4WLU GLY-37 in chains A-D
- **Committed in:** 714c678 (Task 1)

---

**Total deviations:** 3 auto-fixed (2 missing-critical, 1 blocking) — all within-task, no scope creep.
**Impact on plan:** All three were obligations already recorded in the registry/precedents that the plan's file work made load-bearing. No engine, topology (beyond D5), or dependency changes.

## Issues Encountered

- **Transient red suite between Task 1 and Task 2 commits** (expected): the D5 tag makes `test_14_edit_allowed_nodes` fail until the same-plan test update lands — the mechanical consequence of the mandated task split; same pattern as 07-12's feat→test commits. Task 2 restored green immediately.
- **Parallel 07-15 landed mid-execution** (commits `76e2aa2` + `be076f6`): cast.json now holds the 12 real enzymes, so `check_edit_coverage.py` went **exit 0 before my edits.json commit** — the previously-documented 2-CAST-placeholder residual is RESOLVED (07-15 finished). With my akg_dh bucket the counts are: edits.json 13 buckets, cast 12 enzymes, coverage = cast ⊆ edits GREEN.
- **Graph-diagram staleness (residual for plan 16, not touched here):** the 05.1 diagram + DESIGN summary line still say "14 edit-allowed"; the true count is now 15. Per the 07-03 ledger, plan 16 owns "count invariants 57/21 with edit-allowed per the D5 outcome" — flagged for it.

## User Setup Required

None — no external service configuration required. (5GRE/4WLU were fetched into the gitignored runtime cache `rpg/data/assets/downloaded/` — the same location the AssetManager populates at runtime; no setup action owed.)

## Next Phase Readiness

- **Plan 16 (cross-cutting)**: re-pin 15 edit-allowed (this plan's `test_15_edit_allowed_nodes` is the reference), the design-B seeded-fate mapping (research §8; shuffle semantics now landed in labels/texts), the 57/21 pins, the diagram regen (14→15 residual above), and the documented citation-gate residual (2 Phase-8 stubs).
- **Plan 17 (human-verify)**: the TCA arcs to exercise — aconitase restoration reveal (1ACO, chain-A uppercase), the shuffle RNG + trap-cap wording, the akg_dh EditDialog (known option should read the resi-189 restore), the IDH/MDH2 cast loads.
- **Phase 8 (FA synthesis)**: the citrate-export exit (end.good.fatty_acid, authored by 07-10) now has its full TCA-side branch text leading into it.
- No blockers carried forward from this plan.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-03*
