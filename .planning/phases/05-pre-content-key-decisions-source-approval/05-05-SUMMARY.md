---
phase: 05-pre-content-key-decisions-source-approval
plan: 05
subsystem: decisions
tags: [source-approval, first-batch, gate, sc5, hybrid-workflow, lehninger-swap]

# Dependency graph
requires:
  - phase: 05 Plan 05-04
    provides: the PENDING first-batch registry (data/sources.json with 5 pending sources + data/citations.json with 5 pending seed claims) + the SC#4 hybrid-workflow schema (source_id/review_tier/inherits_source_approval/review_notes/claim_text) + the backward-compatible Phase 1 gate (loader ignores extended fields; gate predicate approval_status == "approved" unchanged)
  - phase: 05 Plan 05-03
    provides: SC#4 source-approval WORKFLOW decision = option (c) HYBRID + routine-claim warning flag (the approval sequence this plan executed: sources batch -> high-stakes individually -> routine source-inherited)
  - phase: 01 (Foundations & Citation Gate)
    provides: the Phase 1 citation gate (tools/check_citations.py) whose approval_status == "approved" predicate is the SC#5 enforcement mechanism proven operational on real approved data here
provides:
  - First batch of approved sources + seed claims in the registry (5 claims approved, 4 sources approved, 1 source [LEHNINGER] rejected with provenance) per the human's 2026-08-15 review
  - SC#5 PROVEN operational on real data — the gate exits 0 "CITATION GATE PASSED: 5 claim reference(s) across 2 node(s) -- all approved" on a fixture referencing the 5 approved first-batch claims
  - The Lehninger -> LibreTexts source swap resolved (LEHNINGER rejected per user license concern; the 2 high-stakes TCA RNG claims re-pointed to LIBRETEXTS-METAB-TCA = Jakubowski & Flatt, Fundamentals of Biochemistry Vol. II, Ch 16; CC BY-SA 4.0; web-verified 2026-08-15)
  - TCA-RNG-WEIGHT-01 game-design weight = 0.5/0.5 confirmed per user acceptance + mechanism grounding verified against the LibreTexts source
  - PHASE 5 COMPLETE — all 5 success criteria delivered (SC#1 Plan 01, SC#2 Plan 01, SC#3 Plan 02, SC#4 Plans 03+04+05, SC#5 Plan 05)
affects: [Phase 5.1, Phase 5.2, Phase 6, Phase 7, Phase 8, Phase 9]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Human-approval-then-record pattern: the human is the per-claim/per-source approver (CITE-01 no-fabricated-science rule); OpenCode only mechanically records the decision (flips pending -> approved/rejected in the registry). OpenCode NEVER auto-approves. Rejected entries retain provenance (review_notes records why) — a rejected claim fails the gate identically to a pending one (no Pitfall 6 regression)."
    - "Source-swap-on-rejection pattern: when a source is rejected (e.g. LEHNINGER per license concern), claims referencing it are re-pointed to an approved alternative (LIBRETEXTS-METAB-TCA) by updating source_id + source + review_notes. The rejected source record is retained (NOT deleted) for provenance. The claim's review_tier/inherits_source_approval are preserved (high-stakes claims stay high-stakes + inherits_source_approval=false even after the swap — they don't auto-inherit from the new source)."
    - "SC#5 real-data proof pattern: create a temp fixture story JSON referencing the approved claim_ids, run the gate, confirm exit 0 + 'CITATION GATE PASSED'. This is the end-to-end proof that the gate is operational on REAL approved data (not just placeholder fixtures). Paired with the regression check (existing placeholder fixture still exits 1 [MISSING] — unchanged pre-Plan-04 behavior)."

key-files:
  created: []
  modified:
    - data/citations.json
    - data/sources.json

key-decisions:
  - "LEHNINGER-CH-CITRIC_ACID_CYCLE REJECTED per user license concern (avoid print-textbook license issues). The 2 high-stakes TCA RNG claims (TCA-RNG-CITRATE-PROCHIRALITY-01, TCA-RNG-WEIGHT-01) were re-pointed from LEHNINGER to LIBRETEXTS-METAB-TCA (Jakubowski & Flatt, Fundamentals of Biochemistry Vol. II, Ch 16 The Citric Acid Cycle, section 16.02; CC BY-SA 4.0). Provenance retained."
  - "LIBRETEXTS-METAB-TCA source record updated with the confirmed exact chapter URL (https://bio.libretexts.org/.../16%3A_The_Citric_Acid_Cycle) + section 16.02 subpage URL in notes + license corrected to CC BY-SA 4.0 (the Vol. II cover page license; the subpage metadata shows 'not declared' — a gap, the volume license governs)."
  - "TCA-RNG-WEIGHT-01 weight = 0.5/0.5 confirmed per user acceptance ('this is the probability in textbook'). The source (LibreTexts 16.02) describes the stereospecific citrate synthase mechanism ((S)-citryl-CoA) + the aconitase 180-degree flip (discrimination between citrate's two carboxymethyl groups) — the mechanistic basis for the symmetric fate. HONEST CAVEAT: the page does NOT explicitly use 'prochiral' for citrate (only for NADH) and does NOT state the '0.5/0.5 first-turn vs second-turn probability' explicitly — that is the game-design value grounded in the mechanism the page DOES describe."
  - "First-batch approval breakdown: 5 claims approved / 0 rejected / 0 pending; 4 sources approved / 1 rejected (LEHNINGER) / 0 pending. ALL 5 first-batch claims are approved — the gate passes on any story referencing only them."
  - "SC#5 operational on real data: gate exits 0 'CITATION GATE PASSED: 5 claim reference(s) across 2 node(s) -- all approved' on a temp fixture referencing the 5 approved claims. Existing placeholder fixture still exits 1 [MISSING] (no regression). 12 citation unit tests pass."

patterns-established:
  - "First-batch approval is the SC#4<->SC#5 link: SC#4 (approve the first batch) is what makes SC#5 meaningful on real content (the gate was operational since Phase 1 but had no real approved claims until this plan). Future content batches (Phase 7/8/9) follow the same pattern: populate pending -> human checkpoint -> record decisions -> gate proves operational."
  - "High-stakes claim source-swap preserves review_tier: when a high-stakes claim's source is rejected and swapped to an alternative, the claim stays review_tier=high-stakes + inherits_source_approval=false (it does NOT auto-inherit from the new source — the human still individually reviewed it). This preserves the per-claim safety guarantee on load-bearing claims even through source changes."

# Metrics
duration: 22min
completed: 2026-08-15
---

# Phase 5 Plan 05: First-Batch Approval + SC#5 Gate Verification Summary

**First-batch sources + seed claims approved per human review (5 claims + 4 sources approved, LEHNINGER rejected per license concern and swapped to LibreTexts Jakubowski Ch 16 for the 2 high-stakes TCA RNG claims); SC#5 PROVEN operational on real data (gate exits 0 on a fixture referencing the 5 approved claims); Phase 5 COMPLETE — all 5 success criteria delivered**

## Performance

- **Duration:** ~22 min
- **Started:** 2026-08-15T17:45:29Z
- **Completed:** 2026-08-15T18:07:55Z
- **Tasks:** 2 (Task 1 = checkpoint:human-verify [prior agent], Task 2 = auto [this continuation agent])
- **Files modified:** 2 (data/citations.json, data/sources.json)

## Accomplishments

- **Recorded the human's first-batch approval decisions** (mechanical recording only — the human is the approver, OpenCode never auto-approves): flipped 5 PENDING seed claims -> APPROVED + 4 PENDING source records -> APPROVED, all with approved_by="human" + approved_date="2026-08-15". Every other field preserved (source_id, review_tier, claim_text, inherits_source_approval, etc.) — only approval_status/approved_by/approved_date/review_notes changed.
- **Resolved the Lehninger -> LibreTexts source swap** (PRE-STEP web research + decision logic): the human wanted to AVOID the Lehninger print textbook (license issues) and use a LibreTexts alternative. Web research via webfetch found the Jakubowski & Flatt *Fundamentals of Biochemistry* Vol. II, Ch 16 "The Citric Acid Cycle", section 16.02 "Reactions of the Citric Acid Cycle" (CC BY-SA 4.0) at `https://bio.libretexts.org/Bookshelves/Biochemistry/Fundamentals_of_Biochemistry_(Jakubowski_and_Flatt)/02%3A_Unit_II-_Bioenergetics_and_Metabolism/16%3A_The_Citric_Acid_Cycle/16.02%3A__Reactions_of_the_Citric_Acid_Cycle`. The page covers: (1) citrate synthase stereospecificity — explicitly "to form (S)-citryl CoA" then citrate; (2) the aconitase mechanism including the 180-degree flip of the cis-aconitate intermediate ("This cis-aconitate intermediate... undergoes a 1800 flip around the C=C double bond") — the enzymatic discrimination between citrate's two carboxymethyl groups; (3) the cycle presented "in wedge/dash form with stereochemistry included"; (4) Krebs's 14C isotope-labeling discovery. LEHNINGER was REJECTED (approval_status="rejected", provenance retained); the 2 high-stakes claims' source_id was swapped LEHNINGER -> LIBRETEXTS-METAB-TCA. HONEST CAVEAT recorded in review_notes: the page does NOT explicitly use "prochiral" for citrate (only for NADH) and does NOT state the "two acetyl-CoA carbons not equivalent until after the first turn" consequence explicitly — that is the standard biochemistry implication of the stereospecific mechanism the page DOES describe.
- **Confirmed TCA-RNG-WEIGHT-01 = 0.5/0.5** per the human's acceptance ("this is the probability in textbook"). The claim_text already carried 0.5/0.5; review_notes document the mechanism grounding (citrate synthase (S)-citryl-CoA stereospecificity + aconitase 180-degree flip = symmetric-fate basis) + the honest caveat that the page does not state the 0.5/0.5 probability explicitly (it is the game-design value the human chose, grounded in the mechanism).
- **PROVED SC#5 operational on real data:** created a temporary fixture story JSON (mirroring tests/fixtures/story_pass.json structure — 2 nodes, claim_ids arrays) referencing all 5 approved first-batch claim_ids, then ran `python3.6 tools/check_citations.py --story <temp_fixture> --registry data/citations.json` -> **exit 0 + "CITATION GATE PASSED: 5 claim reference(s) across 2 node(s) -- all approved."** This is the end-to-end proof that the Phase 1 gate is operational on REAL approved data (not just placeholder fixtures). Also ran the gate against the existing tests/fixtures/story_pass.json -> exit 1 [MISSING] on placeholder claims (unchanged pre-Plan-04 behavior — no regression). 12 citation unit tests pass (no regression).

## Task Commits

Each task was committed atomically:

1. **Task 1: Human reviews + approves (or rejects) the first batch** — (checkpoint:human-verify; prior agent read context + returned checkpoint; NO commit — Task 1 IS the checkpoint, no code/data change until the human decides)
2. **Task 2: Record the human's approval decisions + run the gate to prove SC#5 on real data** — `3ef835f` (feat)

**Plan metadata:** (docs: complete plan — committed after SUMMARY/STATE)

## Files Created/Modified

- `data/citations.json` (MODIFIED) — 5 PENDING seed claims flipped to APPROVED with approved_by="human" + approved_date="2026-08-15". The 2 high-stakes TCA RNG claims (TCA-RNG-CITRATE-PROCHIRALITY-01, TCA-RNG-WEIGHT-01) had source_id swapped LEHNINGER-CH-CITRIC_ACID_CYCLE -> LIBRETEXTS-METAB-TCA, source field updated to "LibreTexts: Jakubowski & Flatt, Fundamentals of Biochemistry Vol. II, Ch 16 The Citric Acid Cycle (section 16.02)", and review_notes extended with the web-verification result + honest caveat. Routine claims (GLY-PFK-01, CAST-PFK-PDB-01, CAST-CSC-PDB-01) approved via source inheritance (inherits_source_approval=true) per the hybrid workflow. Final: 5 approved / 0 rejected / 0 pending.
- `data/sources.json` (MODIFIED) — 4 PENDING source records flipped to APPROVED (LIBRETEXTS-METAB-GLYCOLYSIS, LIBRETEXTS-METAB-TCA, PDB-4PFK, PDB-1CSC). LEHNINGER-CH-CITRIC_ACID_CYCLE flipped to REJECTED with review_notes="Rejected per user request 2026-08-15 — avoid print-textbook license issues. Replaced by the LibreTexts Citric Acid Cycle chapter (LIBRETEXTS-METAB-TCA)... Provenance retained." LIBRETEXTS-METAB-TCA record updated with the confirmed exact chapter URL + section 16.02 subpage URL in notes + license corrected to CC BY-SA 4.0 (the Vol. II cover license). Final: 4 approved / 1 rejected / 0 pending.

## Decisions Made

- **LEHNINGER rejected per user license concern** (avoid print-textbook license issues). The human explicitly wanted a LibreTexts alternative. Web research found the Jakubowski & Flatt Ch 16 page (CC BY-SA 4.0) which covers the citrate-prochirality mechanism (citrate synthase (S)-citryl-CoA + aconitase 180-degree flip). The 2 high-stakes claims were re-pointed to LIBRETEXTS-METAB-TCA. This is the user's decision; OpenCode only executed the web research + mechanical swap.
- **TCA-RNG-WEIGHT-01 = 0.5/0.5** per user acceptance ("this is the probability in textbook"). The weight is a game-design value grounded in the symmetric-fate mechanism. The source verification confirmed the page describes the mechanism (citrate synthase stereospecificity + aconitase discrimination) but does NOT state the 0.5/0.5 probability explicitly — recorded honestly in review_notes.
- **Honest caveat on the prochirality source coverage:** the Jakubowski 16.02 page covers the MECHANISM (citrate synthase (S)-citryl-CoA stereospecificity + aconitase 180-degree flip = discrimination between citrate's two carboxymethyl groups) but does NOT explicitly use the word "prochiral" for citrate (it uses "prochiral" only for NADH) and does NOT explicitly state "the two acetyl-CoA carbons do not become equivalent until after the first turn." The claim_text is faithful to the mechanism the page describes; the "not equivalent until after the first turn" is the standard biochemistry implication. Recorded transparently in both high-stakes claims' review_notes so a future Phase 7 per-claim reviewer can decide whether to seek a more explicit prochirality source.
- **High-stakes claims stay high-stakes after the source swap:** TCA-RNG-CITRATE-PROCHIRALITY-01 + TCA-RNG-WEIGHT-01 retain review_tier="high-stakes" + inherits_source_approval=false even after being re-pointed to LIBRETEXTS-METAB-TCA. They do NOT auto-inherit from the new source — the human individually reviewed them (per the hybrid workflow's per-claim safety guarantee on load-bearing claims).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] PRE-STEP web research for the Lehninger -> LibreTexts swap (not in the original plan's Task 2 action)**
- **Found during:** Task 2 (before recording decisions)
- **Issue:** The original plan's Task 2 assumed the human's decisions would be a simple approve/reject list. The human's actual response DISMISSED the multi-choice question and gave free-form instructions: avoid Lehninger (license concern) + seek a LibreTexts alternative + accept 0.5/0.5 + verify the source. This required web research (webfetch) to find a LibreTexts Citric Acid Cycle page covering the prochirality mechanism BEFORE recording the decisions — a PRE-STEP not in the original plan.
- **Fix:** Executed the PRE-STEP web research (5 webfetch calls: 2 initial candidate URLs 404'd, then fetched the chem.libretexts.org Metabolism hub + the Jakubowski textbook cover + Vol. II TOC + Ch 16 section 16.02). Found the Jakubowski 16.02 page covers the mechanism. Applied the orchestrator's decision logic: rejected LEHNINGER, swapped the 2 high-stakes claims' source_id to LIBRETEXTS-METAB-TCA, wrote honest review_notes documenting the page's coverage + caveats.
- **Files modified:** data/sources.json (LIBRETEXTS-METAB-TCA URL + license + notes updated; LEHNINGER rejected), data/citations.json (2 high-stakes claims' source_id + source + review_notes updated)
- **Verification:** webfetch confirmed the page content (citrate synthase (S)-citryl-CoA + aconitase 180-degree flip); gate exits 0 on the approved claims; loader OK.
- **Committed in:** 3ef835f (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — the PRE-STEP web research required by the human's free-form instructions)
**Impact on plan:** The PRE-STEP was necessary to honor the human's license concern + source-swap request. It advanced the plan's objective (SC#4 first-batch approval + SC#5 gate operational) without scope creep — the deliverables are exactly what the plan specified (approved first batch + gate proven), just via a source swap the human requested. No code change; no test change; data + docs only.

## Issues Encountered

None. All Task 2 verifications passed: the JSON loads cleanly (loader OK 5 claims); the breakdown is correct (5 claims approved / 0 rejected / 0 pending; 4 sources approved / 1 rejected / 0 pending); the gate exits 0 "CITATION GATE PASSED" on the temp fixture referencing the 5 approved claims (SC#5 operational on real data); the existing placeholder fixture still exits 1 [MISSING] (no regression); the 12 citation unit tests pass (no regression). The PRE-STEP web research required 5 webfetch calls (2 initial 404s, then 3 successful fetches to locate + verify the Jakubowski Ch 16 section 16.02 page).

## User Setup Required

None - no external service configuration required. (This plan recorded the human's approval decisions + ran the gate; no code/schema change; the loader already handled the extended fields since Plan 04.)

## Next Phase Readiness

**Phase 5 COMPLETE — all 5 success criteria delivered:**
- **SC#1** (soul-jump metaphor confirmed): Plan 05-01 — metamorphosis reframing (carbon body shed as CO2 = chrysalis; narrative POV/sense follows electrons onward). DONE.
- **SC#2** (C14-decay framing decided): Plan 05-01 — DROP confirmed (radioactive decay removed as a bad-ending trigger; cycle-trap-until-host-death is the sole timescale bad-ending; NUBASE2020-C14 + C14-TIME-01 eliminated). DONE.
- **SC#3** (anaerobic framing decided): Plan 05-02 — option (d) CHOICE-FOR-GLUCOSE + BAD-FOR-FA/ALC; invariant re-worded to aerobic-scoped (i); host = mammal/human lactic. DONE.
- **SC#4** (source-approval workflow + first batch approved): Plan 05-03 (workflow = (c) HYBRID + routine-claim warning flag) + Plan 05-04 (registry schema + first-batch populated as pending) + Plan 05-05 (first batch approved here). DONE.
- **SC#5** (per-claim gate operational on real data): Plan 05-05 — gate exits 0 "CITATION GATE PASSED" on a fixture referencing the 5 approved first-batch claims. DONE.

### Flags for downstream phases

- **Phase 5.1 (Story Graph Design):** UNBLOCKED. Needs the ATP/soul-jump decision [RESOLVED Plan 05-01] + the anaerobic decision [RESOLVED Plan 05-02] + the aerobic-scoped reachability checker config (aerobically 1 True + several Normal/Good + many Bad per character; anaerobically True unreachable, glucose 3-ending branch, FA/ALC Bad-trigger only). The ending distribution (asymmetric, user-confirmed 2026-08-15) affects graph topology.
- **Phase 5.2 (Cast & Hero Representation Design):** UNBLOCKED (needs Phase 3 + 5.1). Produces the hero-highlight + scene-template convention.
- **Phase 6 (Qt UI MVP):** UNBLOCKED. Needs the SC#4 source-approval workflow operational [DONE — the registry + gate are operational]. The first human-verify milestone (Qt/GUI cannot be exercised from WSL; manual GUI test matrix begins here).
- **Phase 7 (Glucose content):** UNBLOCKED for content authoring. Needs the first-batch sources [APPROVED here — LIBRETEXTS-METAB-GLYCOLYSIS, LIBRETEXTS-METAB-TCA, PDB-4PFK, PDB-1CSC] + the ATP-soul-jump claim inventory [front-loaded in 05-RESEARCH, per-claim approval in Phase 7]. The full ~60-105 glucose claims get authored in Phase 7 using the same hybrid-workflow schema (source_id/review_tier/inherits_source_approval/review_notes/claim_text) + the same gate. NOTE for Phase 7: the 2 high-stakes TCA RNG claims (TCA-RNG-CITRATE-PROCHIRALITY-01, TCA-RNG-WEIGHT-01) are already approved here with the LibreTexts source — Phase 7 can reference them directly. The honest caveat in their review_notes (the LibreTexts page covers the mechanism but does not use "prochiral" for citrate explicitly) is available for a Phase 7 per-claim reviewer to reconsider if a more explicit prochirality source is desired.

**Blockers/concerns:** None. Phase 5 is COMPLETE. The only non-blocking note is the honest caveat on the prochirality source coverage (the Jakubowski page covers the mechanism but does not use the exact "prochiral" label for citrate) — this is documented transparently in the 2 high-stakes claims' review_notes and can be revisited in Phase 7 if the human wants a more explicit source. The gate is operational; the first batch is approved; the registry is backward-compatible.

---
*Phase: 05-pre-content-key-decisions-source-approval*
*Completed: 2026-08-15*
