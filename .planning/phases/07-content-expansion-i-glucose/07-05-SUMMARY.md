---
phase: 07-content-expansion-i-glucose
plan: 05
subsystem: citations-registry
tags: [citation-gate, registry-landing, approval-ledger, no-fabricated-science, tca-rng, etc, bad-ending-pool, hybrid-approval-schema]

# Dependency graph
requires:
  - phase: 07-content-expansion-i-glucose (plans 01-04)
    provides: the four wave-1 ledgers (structural decisions + approval batches A/B/C) — the authoritative verdict record this plan lands
  - phase: 05-key-decisions
    provides: hybrid approval workflow + registry schema (review_tier / inherits_source_approval / claim_text) + -cand keep-ids policy + rejection-with-provenance precedent
provides:
  - "Registry landed: data/citations.json 5 -> 77 claims (73 approved + 4 pending); data/sources.json 5 -> 81 records (72 approved + 6 rejected + 3 pending)"
  - "All 13 -cand claims approved with ids verbatim (M1); D1=B shuffle claims (TCA-RNG-WEIGHT-02-cand + TCA-CARBON-FATE-01-cand) and D5=promote claims (DIS-OGDH-01-cand + conditional PMID-36520152) landed FIRED"
  - "Landing-time subpage confirms DISCHARGED live (J&F 19.1/19.2/19.3 + J&F 16.04 webfetches 2026-09-01) -> ETC-UCP-01 and ATP-SOUL-07 landed approved; 1ZP0 individually fetched at landing (3.5 A)"
  - "Rejections retained with provenance: R1 stub, 5GRF, 1C97, 2B3Y, LIBRETEXTS-METAB-ETC-II (+ the Phase-5 LEHNINGER record)"
  - "Gate residual reduced to exactly the 9 placeholder buckets (50 MISSING refs, 0 unapproved) — content plans 06-16 can now cite only approved claims"
affects: [07-06..07-16 (content/edits/cast/test plans), phase-9 (deferred 20-AA cast), phase-8 (fa.stub/alc.stub), phase-11 (docs)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Registry-landing plan pattern: a dedicated sole-writer plan applies recorded batch verdicts (VERDICT/Outcome lines) to citations.json/sources.json in one commit"
    - "Landing-time condition pattern: subpage-confirm-at-landing discharged by live webfetch before an approval_status=approved is recorded (J&F Ch19 precedent, mirroring approved Ch 16)"
    - "Canonical-id alias reconciliation: batch ledgers used 2 ids for the same page (S-BIOX/LIBRETEXTS-CATAB-BIOOX; LIBRETEXTS-METAB-ETC/LIBRETEXTS-CATAB-ETC) — one canonical record + alias note; claim source_id fields point at canonical ids"
    - "source_id accepts a list for multi-source claims (loader load-and-ignores extended fields; Phase 5 single-string shape preserved where single)"

key-files:
  created:
    - ".planning/phases/07-content-expansion-i-glucose/07-05-SUMMARY.md (this file)"
  modified:
    - "data/citations.json"
    - "data/sources.json"

key-decisions:
  - "All verdicts applied exactly as recorded by plans 01-04 — NO new decisions; this plan is the sole registry writer (serialization rule honored)"
  - "M1 policy applied: all 13 -cand claim_ids kept verbatim, only approval_status flipped (tests pin ids at tests/test_glucose_reachability.py:339-351)"
  - "INTRO-CAST-20AA-01 NOT landed (deferred to Phase 9 per 07-01 decision #6); ATP-SOUL-01/02 NOT landed (batch-C C11 cross-ref-only); numeric P/O yield claim C14 never filed (banned by batch-C Decision 8)"
  - "Landing-time conditions discharged before recording: J&F 19.3 (UCP1/proton-leak, verbatim sections confirmed) -> ETC-UCP-01 approved; J&F 19.2 (F0F1/binding-change) -> ATP-SOUL-07 approved; 16.04 scope re-confirmed live; 1ZP0 fetched (3.5 A) -> BAD-INHIB-01 anchor verified but claim stays PENDING (chemistry wording source owed at authoring)"
  - "4 bad-pool claims landed PENDING (BAD-MISFOLD/AGGREG/PH: sources UNVERIFIED; BAD-INHIB-01: chemistry source owed) — mapping approved, text stays generic (batch-C Decision 9)"
  - "Gaignard (23910460 -> 93(2):384-389) and Pillai (31290619 -> 179(10):2138-2143 + corrected title) citation corrections landed in the registry records; 05.1 file annotated-not-rewritten"

patterns-established:
  - "Residual-documentation pattern: gate output accounted per placeholder bucket with owning-plan mapping (see Gate residuals below)"

# Metrics
duration: multi-session (~55 min + ~25 min active; one API-connection interruption between sessions)
completed: 2026-09-01
---

# Phase 7 Plan 05: Registry Landing Summary

**Landed all four wave-1 batch ledgers into the citation registry — 72 new approved claims + 67 new approved sources with -cand ids intact, 5 rejections provenance-tracked, landing-time subpage confirms discharged live — leaving the gate with exactly the 9 documented placeholder buckets as residual.**

## Performance

- **Duration:** multi-session (~55 min + ~25 min active; one API-connection interruption between sessions)
- **Started:** 2026-09-01T03:16:16Z
- **Completed:** 2026-09-01T19:24:51Z
- **Tasks:** 2 of 2
- **Files modified:** 2 data files (registry) + this SUMMARY + STATE.md

## Accomplishments

- **data/citations.json: 5 -> 77 claims** (73 approved + 4 pending). Every claim approved in batches A/B/C now holds `approval_status: "approved"` with `approved_by: "human"`, `approved_date: "2026-09-01"`, exact-as-presented `claim_text`, per-claim `review_tier` / `inherits_source_approval` / `source_id` (list for multi-source), and `review_notes` evidence trails on every high-stakes claim; PDB claims carry `pdb_id` + `resolution_angstrom`.
- **data/sources.json: 5 -> 81 records** (72 approved + 6 rejected + 3 pending), copying the Phase-5 record shapes; the LIBRETEXTS-METAB-TCA record now scopes 16.02 + 16.01 + 16.04 with **16.03 explicitly OUT of approved scope** (no 16.03-grounded claim may be filed; TCA-IDH3-01 softened to "a key regulatory step").
- **Landing-time verifications discharged live (webfetch 2026-09-01):** J&F Ch 19 chapter + 19.1 (complexes I–IV/cofactors), 19.2 (F0F1 + Boyer LOT binding-change — discharges ATP-SOUL-07's condition; page even models 1E79 + DCCD), 19.3 (coupling/uncoupling + dedicated UCP1 section — discharges ETC-UCP-01's condition), 16.04 re-confirmation (citrate-lyase/FA-synthesis verbatim), and the individually-owed 1ZP0 RCSB fetch (title verbatim, X-ray 3.5 Å, Sun 2005).
- **Gate re-run:** `CITATION GATE FAILED: 50 missing + 0 unapproved` — the residual is EXACTLY the 9 documented placeholder buckets (table below); all 20 story-referenced real claims (13 `-cand` + 7 Phase-5) resolve approved; zero unapproved references.
- **Full suite green:** 324 tests OK; both AST gates clean (registry-only change, as planned).

## Task Commits

1. **Task 1: Land all batch outcomes in the registry** — `dde6663` (feat(07-05): land all batch A/B/C outcomes in the citation registry)
2. **Task 2: Re-run citation gate + document residuals per bucket** — gate re-run executed (residual = placeholders only, zero unexplained); residual table recorded below in this SUMMARY; no registry fix required — committed with the plan metadata docs commit.

## Gate residuals (documented)

`python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json` → exit 1: **50 MISSING + 0 UNAPPROVED**. Every residual is a not-yet-authored placeholder bucket (no real claim is missing or unapproved):

| placeholder bucket | refs | nodes (file) | Owning plan (wave) | Note |
|---|---|---|---|---|
| `PLACEHOLDER_PHASE7` | 4 | intro.preface, intro.select, intro.shell_glucose (intro.json); pyr.pdh (pyruvate_branch.json) | 07-07 intro (w3) + 07-06 pyruvate (w4) | swapped during segment content authoring |
| `PLACEHOLDER_PHASE7_GLYCOLYSIS` | 5 | gly.start, gly.g6p, gly.fbp_to_pyruvate, gly.pyruvate_kinase, gly.pyruvate | 07-08 (w4) | |
| `PLACEHOLDER_PHASE7_TCA` | 9 | tca.entry, co2_turn1, co2_turn2, isocitrate_dh, akg_dh, succinyl_coa_synthetase, fumarase, malate_dh, divert_to_good | 07-13 (w5) | |
| `PLACEHOLDER_PHASE7_ETC` | 6 | etc.entry, complex_ii, complex_iii, complex_iv, atp_synthase, end.true | 07-09 (w3) | |
| `PLACEHOLDER_PHASE7_ANAEROBIC` | 6 | pyr.branch, anaer.entry, anaer.ldh, anaer.lactic, anaer.ethanolic, anaer.crisis | 07-06 (w4) | |
| `PLACEHOLDER_PHASE7_ENDINGS` | 3 | end.good.fatty_acid, end.good.amino_acid, end.normal.co2 | 07-10 (w3) | |
| `PLACEHOLDER_PHASE7_BAD` | 14 | all 14 bad.* endings | 07-11 (w3) | swaps cite the 7 approved + (later) 4 pending bad-pool claims; generic text where pending |
| `PLACEHOLDER_PHASE7_EDIT` | 1 | edit.prompt (bad_endings.json) | retained — NOT a content-plan swap | batch-C Decision 9 verdict: **NO CHANGE** — keep the placeholder; structural stub, runtime bypasses via EditRouter (research OQ#8). Plan 16's sweep expectation must accommodate this documented stub alongside fa.stub/alc.stub |
| `PLACEHOLDER_PHASE8` | 2 | fa.stub, alc.stub (intro.json) | documented Phase 8 stubs | 07-01 decision #2: leave untouched + annotate-only (plan 07); plan 16 sweep expects these residuals |

**Unexplained residuals: ZERO.** Registry now contains approvable backing for every swap the content plans will make.

## Files Created/Modified

- `data/citations.json` — 77 claims (73 approved / 4 pending); -cand ids verbatim; D2 co-source widening on TCA-RNG-CITRATE-PROCHIRALITY-01 (source_id now lists LIBRETEXTS-METAB-TCA + WIKIPEDIA-ACONITASE + WIKIPEDIA-TCA, claim text unchanged); OGDH single-submitter caveat + CYC1/COX4I1 citation corrections in review_notes.
- `data/sources.json` — 81 records; LIBRETEXTS-METAB-TCA notes updated (16.01 pointer + 16.04 scope + 16.03 out-of-scope); 6 rejections retained; 3 pending (PDB-7ACN, PDB-2DFD verified-not-selected; PDB-1ZP0 anchor-fetched).

## Decisions Made

None new — every verdict was recorded by plans 01-04 and applied as-is. The two landing-time conditions (J&F 19.2/19.3 subpage confirms) were discharged by live webfetch **before** recording ETC-UCP-01 and ATP-SOUL-07 as approved, per the batch-C ledger's explicit landing-time condition.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plan's gate command shorthand lacks required CLI args**
- **Found during:** Task 2 (gate re-run)
- **Issue:** The plan's `<verify>` and `<verification>` write `python3.6 tools/check_citations.py` with no args — the tool's argparse REQUIRES `--story` and `--registry` (bare invocation exits 2 with a usage error, not a gate result).
- **Fix:** Ran the gate-contract form documented in the plan's own cited context (07-RESEARCH-content-mechanics.md §3, lines 91-122): `python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json`.
- **Files modified:** none (invocation only)
- **Verification:** gate executed with the documented three-way exit contract (exit 1 = missing/unapproved claims, as reported above)
- **Committed in:** n/a (no code change)

**2. [Rule 1 - Bug] 07-02 ledger's "S3/S4 already present" was inaccurate — sources.json held only 5 Phase-5 records**
- **Found during:** Task 1 (source landing)
- **Issue:** The batch-A ledger Part 5 says "record S3/S4 as re-confirmed (already present)", but LIBRETEXTS-CATAB-BIOOX and LIBRETEXTS-CATAB-ETC had NO sources.json record (the file held exactly 5 Phase-5 sources; verified at execution start).
- **Fix:** Landed both as approved records from the recorded batch-A verdicts (human approval 2026-09-01; verification trail: live 2026-08-15 Phase 5 + re-fetched 2026-08-30 and 2026-09-01), with notes documenting the discrepancy so the provenance is honest.
- **Files modified:** data/sources.json
- **Verification:** sources.json counter check (81 records; 72/6/3 by status)
- **Committed in:** dde6663

**3. [Rule 1 - Bug] Same-page source aliases across batch ledgers reconciled to canonical ids**
- **Found during:** Task 1 (source landing)
- **Issue:** 07-04's ledger ids `S-BIOX` and `LIBRETEXTS-METAB-ETC` denote the SAME chem.libretexts Catabolism pages as 07-02's `LIBRETEXTS-CATAB-BIOOX` / `LIBRETEXTS-CATAB-ETC`; landing both would create duplicate records for one page.
- **Fix:** One canonical record per page (the 07-02 ids, matching the existing sources.json naming family), with the 07-04 alias noted inside the record; all claim `source_id` fields point at the canonical ids.
- **Files modified:** data/sources.json, data/citations.json
- **Verification:** 81 unique source records; no duplicate-page records
- **Committed in:** dde6663

**4. [Rule 1 - Bug] First sources.json assembly missed the 3 batch-B rejections**
- **Found during:** Task 1 (post-write validation)
- **Issue:** The counter check showed 3 rejected records (expected 6) — PDB-5GRF, PDB-1C97, PDB-2B3Y rejection-with-provenance entries were absent from the assembled fragment.
- **Fix:** Added the 3 rejected records with their full batch-B provenance (mutant-cast / catalytic-site-mutant / wrong-isoform) before committing.
- **Files modified:** data/sources.json
- **Verification:** rejected set = [LEHNINGER, LIBRETEXTS-CATAB-PYRUVATE-DH, PDB-5GRF, PDB-1C97, PDB-2B3Y, LIBRETEXTS-METAB-ETC-II]
- **Committed in:** dde6663

---

**Total deviations:** 4 auto-fixed (4 × Rule 1/3; 0 architectural, 0 user gates)
**Impact on plan:** All fixes were required for a faithful, complete landing; no scope creep; no engine/story/test files touched.

## Issues Encountered

- One API-connection interruption mid-assembly (between writing the claims fragments and concatenating them); recovered cleanly from the fragment files — no work lost, no partial file was ever committed.
- Documentation note for plan 16: the phase-end "gate exit 0" expectation must be read as "exit 1 with ONLY documented stub/bucket residuals" — the batch-C verdict retains `PLACEHOLDER_PHASE7_EDIT` at edit.prompt by design, alongside the fa.stub/alc.stub `PLACEHOLDER_PHASE8` residuals (07-01 decision #2).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Wave 2 complete** — plans 06-16 (content/edits/cast/tests) are unblocked: every claim they may cite now exists and is approved (or is a documented pending bad-pool claim whose text stays generic).
- Content-plan guardrails locked in the registry records: DIS-PFKM pinned to "Likely pathogenic"; OGDH single-submitter caveat mandatory; CYC1 = L215F (W96C documented discarded); COX4I1 dual numbering (PDB resi 130 / human P152T); no numeric P/O yields; no ROS claims; proton-leak text says PROTONS; anti-confusion binding on every ETC/ending text; TCA-IDH3 "a key regulatory step" (16.03 out of scope).
- Owed downstream (tracked, not blockers): bovine-1ACO ↔ human S112 mapping BEFORE any aconitase edits.json signature (Phase 5.1 OQ5, plans 12/13/14); 5GRE α-chain construct-numbering check at authoring (plan 13); BAD-INHIB-01 chemistry source at authoring (plan 11 + a future registry write); BAD-MISFOLD/AGGREG/PH sources whenever a folding/denaturation source verifies.
- Blockers: none.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-01*
