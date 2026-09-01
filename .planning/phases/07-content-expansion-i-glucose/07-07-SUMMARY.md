---
phase: 07-content-expansion-i-glucose
plan: 07
subsystem: story-content
tags: [story-json, intro-nodes, claim-swaps, citation-registry, phase-8-stubs, glucose, two-layer-text]

# Dependency graph
requires:
  - phase: 07-content-expansion-i-glucose (plans 01/02/05)
    provides: "OQ-C deferral (07-01 decision #6) + batch-A verdicts (07-02: CAST-GLC-PUBCHEM-01 APPROVED; INTRO-CAST-20AA-01 DEFERRED) + registry landing (07-05: CAST-GLC-PUBCHEM-01 approved in data/citations.json)"
  - phase: 05.1-story-graph-design
    provides: "FROZEN skeleton: 55 nodes / 21 endings / start intro.preface; 5-node intro.json with placeholder text"
  - phase: 06-qt-ui-minimal-playable-mvp
    provides: "TestStartNodeOnEnterShape (pins the _smoke.pdb loads + 6-call hero-highlight on_enter) + 324-test baseline"
provides:
  - "Final-quality two-layer text for all 3 intro nodes (intro.preface / intro.select / intro.shell_glucose) in data/story_glucose/intro.json"
  - "Claim swaps per 02 verdicts: preface [] (20-AA fallback), select [] (pure UI), shell_glucose [CAST-GLC-PUBCHEM-01]"
  - "Explicit 'returns in Phase 8' stub annotations on fa.stub/alc.stub (claim_ids untouched)"
  - "Zero on_enter drift — start-node shape tests stay green"
affects: [plan 08 (glycolysis text inherits the shell_glucose->gly.start handoff), plan 10 (endings), plan 16 (PLACEHOLDER sweep expects fa.stub/alc.stub residuals), Phase 8 (replaces the stubs), Phase 9 (real 20-AA cast; INTRO-CAST-20AA-01 successor id)]

# Tech tracking
tech-stack:
  added: []   # content-only plan — no new libraries
  patterns:
    - "Two-layer intro authoring: dramatic = game framing (no science claims); teaching = only registry-approved claims, verbatim-grounded"
    - "Deferred-claim fallback: claim_ids [] + framing-only text when a contingent claim is DEFERRED (INTRO-CAST-20AA-01 -> Phase 9)"
    - "Stub annotation convention: text says 'returns in Phase 8', claim_ids keep PLACEHOLDER_PHASE8 so the gate residual stays exactly the 2 documented stub buckets"

key-files:
  created:
    - ".planning/phases/07-content-expansion-i-glucose/07-07-SUMMARY.md (this file)"
  modified:
    - "data/story_glucose/intro.json (text fields + claim_ids ONLY; on_enter byte-identical)"

key-decisions:
  - "intro.preface claim_ids -> [] (empty list, gate-valid): INTRO-CAST-20AA-01 was DEFERRED per 07-02 verdict #10 + 07-01 decision #6, so the plan's ONLY-if-approved swap does not fire; 02-recorded fallback = project-framing text with empty/minimal claim list"
  - "intro.shell_glucose claim_ids -> [CAST-GLC-PUBCHEM-01]; teaching text grounded strictly on the approved claim_text (D-glucose, C6H12O6, PubChem CID 5793, MW 180.16, 3D conformer, pyranose = IUPAC oxane ring)"
  - "intro.preface dramatic keeps the soul-jump-compatible destiny framing (electrons poured into ATP at the pathway's far end) — never 'the carbon becomes ATP'"
  - "C14 teaching = TRACKING LABEL only ('not a second atom, not a disease, not a fate'); no isotope-decay claims (Pitfall 9 pending) — the word radioactivity never appears"
  - "fa.stub/alc.stub: text annotated as explicit Phase 8 stubs; PLACEHOLDER_PHASE8 claim_ids kept verbatim (plan-01 outcome 2 + plan-16 sweep expectation)"

patterns-established:
  - "on_enter immutability under text authoring: text/claim_ids edits never touch on_enter arrays; parsed on_enter equality vs HEAD verified before commit"

# Metrics
duration: 12 min
completed: 2026-09-01
---

# Phase 7 Plan 07: Intro Content (Light Touch) Summary

**All 3 intro nodes authored two-layer with registry-grounded claim swaps (shell_glucose -> CAST-GLC-PUBCHEM-01; preface/select -> [] per the deferred-claim fallback) and explicit Phase 8 stub annotations — on_enter byte-identical, 324 tests + 20 reachability tests green.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-01T19:38:43Z
- **Completed:** 2026-09-01T19:50:10Z
- **Tasks:** 1 of 1
- **Files modified:** 1 (`data/story_glucose/intro.json`)

## Accomplishments

- **intro.preface** — dramatic: the blessed carbon + sick host + restoration mission (pure game framing; destiny framed soul-jump-compatible: "a soul of restless electrons is poured into... ATP", never the carbon-becomes-ATP claim). Teaching: the hero is ONE carbon atom; C14 = a TRACKING LABEL ("not a second atom, not a disease, and not a fate"); the 20-AA cast referenced framing-only as "placeholder stand-in figures... (the real cast arrives in a later chapter)" per OQ-C. No isotope-decay claims (Pitfall 9 pending); the word radioactivity does not appear.
- **intro.select** — pure UI text: character select; fatty acid + alcohol explicitly noted as Phase 8 ("their doors stay closed for now, and choosing them simply returns you here").
- **intro.shell_glucose** — dramatic: the shell becomes the form. Teaching: D-glucose, C6H12O6, PubChem CID 5793, MW 180.16, single 3D conformer, pyranose form via the IUPAC oxane ring — every element inside the APPROVED `CAST-GLC-PUBCHEM-01` claim_text (plus the spec-item-3 "small molecules are 3D models" framing).
- **fa.stub / alc.stub** — dramatic + teaching now explicitly annotate "returns in Phase 8" / "Phase 8 stub... carries no science yet"; `PLACEHOLDER_PHASE8` claim_ids kept verbatim; on_enter untouched.
- **Start shape protected** — all 5 on_enter arrays verified IDENTICAL (parsed equality vs HEAD; the edited lines never intersect on_enter). TestStartNodeOnEnterShape + topology tests green.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author intro text + swaps; annotate stubs; protect start shape** — `49da906` (feat)

**Plan metadata:** committed after SUMMARY + STATE updates (see git log).

## Files Created/Modified

- `data/story_glucose/intro.json` — 5 nodes: 3 intro nodes authored two-layer with claim swaps; 2 stubs annotated; on_enter/choices/tags/structure untouched.

## Claim-Swap Ledger (per plan context, gly §2.1 + 07-02 verdicts)

| Node | Old claim_ids | New claim_ids | Basis |
|------|---------------|---------------|-------|
| intro.preface | `["PLACEHOLDER_PHASE7"]` | `[]` | INTRO-CAST-20AA-01 DEFERRED (07-02 verdict #10; 07-01 decision #6) -> 02-recorded fallback: framing text + empty claim list |
| intro.select | `["PLACEHOLDER_PHASE7"]` | `[]` | 07-02/research §2.1: no claims needed (pure UI); `claim_ids: []` is gate-valid (walker skips empty) |
| intro.shell_glucose | `["PLACEHOLDER_PHASE7"]` | `["CAST-GLC-PUBCHEM-01"]` | APPROVED as presented (07-02 verdict #9; landed approved in registry by 07-05) |
| fa.stub | `["PLACEHOLDER_PHASE8"]` | `["PLACEHOLDER_PHASE8"]` (kept) | plan-01 outcome 2: stubs left as documented Phase 8 residuals |
| alc.stub | `["PLACEHOLDER_PHASE8"]` | `["PLACEHOLDER_PHASE8"]` (kept) | plan-01 outcome 2: stubs left as documented Phase 8 residuals |

Citation-gate effect: the intro placeholder references are GONE from the gate residual (0 intro lines in gate output); `CAST-GLC-PUBCHEM-01` resolves approved. Remaining residual = the other 8 documented placeholder buckets owned by plans 06/08/09/10/11/13/16 (fa.stub/alc.stub's PLACEHOLDER_PHASE8 = 2 of the expected plan-16 residuals).

## Decisions Made

- **Preface fallback applied as directed:** the plan's swap map says INTRO-CAST-20AA-01 ONLY if approved; batch A deferred it, so the 02-recorded fallback (project-framing text, empty/minimal claim list) was applied — `claim_ids: []` chosen over a framing-only invented id (inventing an id would fabricate a registry key).
- **Dramatic destiny wording** aligns with the PROJECT.md soul-jump reframing (electrons -> ATP) while keeping the mythic "become ATP" destiny the spec asks for — anti-confusion note honored.
- **No Phase-number leaks except sanctioned ones:** "Phase 8" appears only where the plan mandates it (intro.select + stub annotations); the preface teaching says "a later chapter" for the 20-AA cast (Phase 9 deferral framing-only).

## Deviations from Plan

None — plan executed exactly as written. (The `[]`-fallback on intro.preface is the plan-directed path for a DEFERRED claim, not a deviation; recorded here per the plan's own instruction "recorded in SUMMARY".)

## Issues Encountered

- **Concurrent wave-3 sessions in the same working tree** (same pattern as 07-01's concurrent-session note): while this plan edited intro.json, sibling plan 07-10 committed ending texts (`0cd8d67`, endings.json) and another session had bad_endings.json in flight. Per the established precedent, this plan's task commit staged ONLY `data/story_glucose/intro.json`; no sibling file was swept in; history not rewritten.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Unblocked:** plan 08 (glycolysis content) can now assume an authored intro and the shell_glucose -> gly.start handoff; plan 16's PLACEHOLDER sweep expects exactly the remaining documented buckets (incl. fa.stub/alc.stub).
- **Watch items:** Phase 8 replaces the fa.stub/alc.stub content (keep the annotation convention until then); Phase 9 owns the real 20-AA cast sourcing (INTRO-CAST-20AA-01 successor id enters a future approval batch).

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-01*
