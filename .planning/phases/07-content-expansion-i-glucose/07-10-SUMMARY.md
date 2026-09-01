---
phase: 07-content-expansion-i-glucose
plan: 10
subsystem: story-content (endings)
tags: [endings, cataplerotic, citrate-export, transamination, amphibolic, uncoupling, ucp1, proton-leak, carbon-fate, soul-jump, citation-gate]

# Dependency graph
requires:
  - phase: 07-content-expansion-i-glucose (07-03)
    provides: batch-B cataplerotic claim approvals (TCA-CITRATE-EXPORT-01, TCA-TRANSAMINATION-01, TCA-AMPHIBOLIC-01, TCA-CO2-EXIT-01) + anti-confusion guardrails
  - phase: 07-content-expansion-i-glucose (07-04)
    provides: OQ2 outcome (oq2-uncoupling; ETC-UCP-01) + framing rules (no numeric P/O yields; no ROS; proton-leak text says PROTONS)
  - phase: 07-content-expansion-i-glucose (07-05)
    provides: registry landing — all cited claims APPROVED in data/citations.json (77 claims; J&F 19.3 landing-confirm discharged for ETC-UCP-01)
provides:
  - "Authored good + normal ending texts: 3/3 nodes (end.good.fatty_acid, end.good.amino_acid, end.normal.co2) grounded entirely in approved claims"
  - "PLACEHOLDER_PHASE7_ENDINGS bucket fully resolved (0 residual refs; 0 TBD strings in the file)"
  - "NARRATIVE-FRAMING FLAG deleted — resolved by the 07-04 oq2-uncoupling outcome"
affects: [07-09 (ETC content — end.normal.co2 is the downstream node of etc.entry 'let go'; keep framing consistent), 07-11 (bad-pool — bad.proton_leak PROTON-text fix shares the ETC-UCP-01 ground), 07-13 (TCA — tca.divert_to_good branch texts feed these endings), 07-16/07-19 (final sweep/verification)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ending-tier semantics text pattern: good = carbon body retained (lives on); normal = chemistry completed, harvest arc did not — every science sentence mapped to a cited approved claim on the node"
    - "'Where the text uses them' citation discipline: a node cites every approved claim whose fact appears in its text (incl. cross-domain facts like TCA-CO2-EXIT-01 inside a fatty-acid ending)"

key-files:
  created:
    - ".planning/phases/07-content-expansion-i-glucose/07-10-SUMMARY.md"
  modified:
    - "data/story_glucose/endings.json"

key-decisions:
  - "end.normal.co2 carbon-fate grounded by REGISTRY-RESIDENT claims (TCA-CO2-EXIT-01 + PYR-PDH-01) — the plan context's 'ATP-SOUL-01/02 family per registry' resolves here because ATP-SOUL-01/02 were NOT landed (07-05 ledger: batch-C C11 cross-ref-only); ATP-SOUL-08 carries the electrons=soul framing"
  - "end.normal.co2 teaching includes the PMF/ATP-synthase setup sentences (cited ETC-PMF-01 + ATP-SOUL-07) because the node is reached from etc.entry BEFORE any ETC teaching node — the uncoupling payoff needs the gradient setup for comprehension"
  - "Good endings keep exit-event scope discipline with an in-world pointer ('a story for another path') — no downstream FA chemistry or protein synthesis taught (Phase 8 territory)"

patterns-established:
  - "Ending teaching-text voice: short dramatic line (carbon-body language) + single-paragraph teaching; anti-confusion guardrails honored verbatim (good = 'your carbon body lives on'; never carbon->ATP)"

# Metrics
duration: 12 min
completed: 2026-09-01
---

# Phase 7 Plan 10: Good + Normal Endings Content Summary

**All 3 glucose ending nodes authored with approved claims only: two cataplerotic good exits (citrate-export to FA synthesis; transamination to amino acids) and the oq2-uncoupling normal CO2 exit (proton leak/UCP1, protons never electrons, zero yields, zero ROS) — NARRATIVE-FRAMING FLAG deleted, PLACEHOLDER_PHASE7_ENDINGS bucket at 0.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-01T19:38:41Z
- **Completed:** 2026-09-01T19:50:18Z
- **Tasks:** 1/1
- **Files modified:** 1 (data/story_glucose/endings.json)

## Accomplishments

- **end.good.fatty_acid** — dramatic: "stored for tomorrow" (carbon body lives on). Teaching: amphibolic/cataplerotic framing → citrate exported (acetyl-CoA cannot cross the inner membrane) → ATP-citrate-lyase cleavage → cytosolic acetyl-CoA destined for fatty-acid synthesis + OAA returned as malate → why the intermediate exit retains carbon (per-turn 2-CO2 no-net-synthesis point). Exit-event scope only.
- **end.good.amino_acid** — dramatic: "Not burned: built." Teaching: amphibolic framing → OAA→aspartate/asparagine; alpha-KG→glutamate family (Glu/Gln/Pro/Arg) → transamination mechanism with glutamate as amino-group donor and PLP cofactor. Exit-event scope only.
- **end.normal.co2** — dramatic: everyday-exit flavor kept. Teaching: tier semantics ("narrative tier, not a separate biochemical path") + carbon fate (PDH releases the first CO2; each TCA turn releases two; every glucose carbon eventually departs as CO2) + the REAL uncoupling science per oq2-uncoupling: protons leak back without driving ATP synthase (basal leak / UCP1, most abundant in brown fat), proton-motive force dissipated as heat while electron transport and CO2 production carried on. PROTONS, never "electrons leak"; no ROS; no numeric P/O yields.
- **NARRATIVE-FRAMING FLAG bracket text deleted** (resolved by 07-04 Decision 5); all `PLACEHOLDER_PHASE7_ENDINGS` refs swapped for 9 approved claim_ids.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author good + normal ending texts** - `0cd8d67` (feat)

## Files Created/Modified

- `data/story_glucose/endings.json` - 3/3 ending nodes authored (text_dramatic + text_teaching + claim_ids only; on_enter/choices/tags/topology byte-identical)

## Decisions Made

1. **Carbon-fate ground truth for end.normal.co2 = TCA-CO2-EXIT-01 + PYR-PDH-01.** The plan's context map said "carbon-fate cross-ref claim (ATP-SOUL-01/02 family per registry)" — but ATP-SOUL-01/02 were deliberately NOT landed (07-05 ledger; batch-C C11 was cross-ref-only). The registry-resident members of that family are TCA-CO2-EXIT-01 (07-03 explicitly assigned it to end.normal.co2) for the CO2 fate and ATP-SOUL-08 for the electrons=soul/carbon-shed framing. Citing anything absent from the registry would fail the gate; this substitution is faithful to the ledger.
2. **PMF/ATP-synthase setup sentences included and cited** (ETC-PMF-01 + ATP-SOUL-07, both approved): end.normal.co2 is reached from etc.entry's "let go" choice before the player sees any ETC teaching node, so the uncoupling payoff ("protons leaked back without driving ATP synthase") is incomprehensible without the gradient setup. Every sentence maps to a cited approved claim.
3. **"Where the text uses them" citation widening on good endings:** end.good.fatty_acid also cites TCA-CO2-EXIT-01 (the text uses the per-turn CO2/no-net-synthesis contrast that explains why the intermediate exit retains carbon) and TCA-AMPHIBOLIC-01 (both good teachings open with the amphibolic/cataplerotic framing); end.good.amino_acid cites TCA-AMPHIBOLIC-01. All approved.
4. **Uncoupling heat/brown-fat wording** taken from the J&F 19.3 verbatim anchors recorded in ETC-UCP-01's registry review_notes ("loss of energy as heat"; "UCP1 … found most abundantly in brown fat") — the documented authoring-time alternative wording, not invented science.

## Deviations from Plan

None — plan executed exactly as written. (The claim-id substitutions in Decisions 1-3 stay inside the plan's own context map language: "ATP-SOUL-01/02 **family per registry**" and "+TCA-CO2-EXIT-01/TCA-AMPHIBOLIC-01 **where the text uses them**".)

## Issues Encountered

- Parallel wave-3 plans were landing during execution (07-07 committed mid-run; `data/story_glucose/bad_endings.json` was dirty from an in-flight 07-11 run). Scope discipline held: only `endings.json` was staged/committed by this plan. Consequently the citation-gate residual measured at verification time (29 MISSING / 0 UNAPPROVED) reflects several buckets already swapped by parallel plans, not just this one — the bucket attributable to THIS plan (`PLACEHOLDER_PHASE7_ENDINGS`) is at **0 residual** (verified by targeted grep).

## Verification (all green)

- `python3.6 -m unittest tests.test_glucose_reachability -v` → **Ran 20 tests — OK** (55 nodes / 21 endings: 1T+3G+2N+15B unchanged; no orphaned endings).
- `python3.6 -m unittest discover -s tests` → **Ran 324 tests — OK** (zero regression).
- `python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json` → 0 UNAPPROVED; `PLACEHOLDER_PHASE7_ENDINGS` residual = **0** (bucket resolved); remaining MISSING refs are the other plans' documented placeholder buckets (TCA/GLYCOLYSIS/ANAEROBIC/BAD/EDIT/PHASE8 per the 07-05 per-bucket owner table).
- `grep -c "NARRATIVE-FRAMING FLAG" data/story_glucose/endings.json` → **0** (flag text gone).
- JSON validity via `python3.6 -m json.tool` → OK; banned-phrase scan (electrons leak / rate-limiting / ROS / numeric-yield patterns) → 0 hits; TBD scan on the 3 nodes → 0 hits.

## Next Phase Readiness

- Endings content done; the good endings' branch point (`tca.divert_to_good`) and the shuffle texts are 07-13's — its texts should stay consistent with these endings' amphibolic framing and exit-event scope.
- 07-09 (ETC content) must keep etc.entry's "let go" relabel consistent with this node's uncoupling teaching (same ETC-UCP-01 ground).
- 07-11 must rewrite `bad.proton_leak` to PROTONS per Decision 7 (this plan's normal-co2 text already demonstrates the sanctioned wording).

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-01*
