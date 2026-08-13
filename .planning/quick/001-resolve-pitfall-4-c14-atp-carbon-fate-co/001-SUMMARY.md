---
phase: quick-001
plan: 01
subsystem: docs
tags: [pitfall-4, soul-jump, carbon-fate, atp, ending-semantics, c14]

# Dependency graph
requires:
  - phase: research (PITFALLS.md Pitfall 4 identification)
    provides: The science conflict the soul-jump reframing resolves
provides:
  - "Pitfall 4 RESOLVED via soul-jump reframing (electrons-as-soul -> ATP via ETC after RNG-weighted TCA path; carbon body -> CO2)"
  - "Consistent ending semantics across all planning docs (True=soul harvested into ATP, Good=carbon retained pre-oxidation, Normal=CO2 without full harvest, Bad=failure/cycle-trap/host-death/critical-residue-break)"
  - "C14 treated as a tracking label, not a fate determinant, everywhere"
affects: [phase-5, phase-5.1, phase-7, phase-8, story-graph-design, content-authoring]

# Tech tracking
tech-stack:
  added: []
  patterns: ["soul-jump reframing: narrative electrons harvested into ATP via ETC (carbon body exits as CO2) — the canonical True-ending science framing"]

key-files:
  created: []
  modified:
    - spec.md
    - .planning/PROJECT.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
    - .planning/research/PITFALLS.md
    - .planning/research/SUMMARY.md
    - .planning/research/FEATURES.md

key-decisions:
  - "Pitfall 4 RESOLVED (2026-08-13) via soul-jump reframing: hero's electrons ('soul') harvested into ATP via ETC -> ATP synthase after the RNG-weighted TCA path; carbon body released as CO2 via PDH + TCA decarboxylations. Preserves the dramatic True=ATP arc with scientific accuracy."
  - "Pitfall 9 (C14 decay timescale) left Pending — NOT resolved by this task."
  - "C14 is a tracking label only, not a fate determinant — established across all docs."

patterns-established:
  - "RESOLVED provenance pattern: original pitfall text retained verbatim for traceability; a RESOLVED note block inserted at the top explains the adopted resolution."

# Metrics
duration: 29min
completed: 2026-08-13
---

# Quick Task 001: Resolve Pitfall 4 (C14/ATP Carbon-Fate Conflict) Summary

**Pitfall 4 resolved via the soul-jump reframing (electrons-as-soul -> ATP via ETC after RNG-weighted TCA path; carbon body -> CO2) propagated across 8 planning docs; Pitfall 9 left Pending.**

## Performance

- **Duration:** ~29 min
- **Started:** 2026-08-13T05:17:02Z
- **Completed:** 2026-08-13T05:46:18Z
- **Tasks:** 3/3
- **Files modified:** 8 (documentation only — no source code, tests, or fixtures)

## Accomplishments
- Pitfall 4 (C14/ATP carbon-fate science conflict) marked RESOLVED across all planning docs via the soul-jump reframing — the hero's electrons (narrative "soul") are harvested into ATP via the ETC -> ATP synthase after the RNG-weighted TCA path, while the carbon body is released as CO2.
- Ending semantics (True/Good/Normal/Bad) made consistent across PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, FEATURES.md, PITFALLS.md, and SUMMARY.md.
- spec.md prose preserved — only a minimal HTML-comment annotation added on line 15 (the human's original "the true end is end up as ATP" remains intact).
- README.md verified clean (no ATP-becomes-ATP assertion; C14-as-tracking-label framing intact) — no edit needed.
- Pitfall 9 (C14 decay timescale) confirmed still Pending everywhere — NOT resolved by this task.

## Task Commits

Each task was committed atomically:

1. **Task 1: Declare the soul-jump resolution in canonical docs (PROJECT.md + spec.md)** - `a5a45d0` (docs)
2. **Task 2: Propagate the reframing across downstream planning docs (REQUIREMENTS.md, ROADMAP.md, STATE.md, FEATURES.md)** - `73fb7c6` (docs)
3. **Task 3: Mark RESOLVED in research provenance (PITFALLS.md, SUMMARY.md) + verify README.md + grep re-scan** - `97ea97c` (docs)

## Files Created/Modified

All edits are documentation-only (no source code, tests, or fixtures touched).

### spec.md
- **Line 15:** Minimal HTML-comment annotation added after "the true end is end up as ATP" pointing to the soul-jump resolution (Pitfall 4 NOTE). Human's original prose preserved verbatim.

### .planning/PROJECT.md (canonical Key Decisions source of truth)
- **Line 18 (Core Value):** ATP clarified as "the hero's electrons harvested into energy via the ETC".
- **Line 33 (4-ending-tiers active requirement):** True tier reframed to soul-jump (electrons/"soul" -> ATP via ETC; carbon body -> CO2).
- **Line 52 (Out-of-Scope Stat/XP):** Rationale reworded for soul framing (True ending = electrons harvested into ATP, so energy can't double as XP).
- **Lines 72-75 (Ending semantics block):** Fully rewritten to soul-jump framing. True = electrons/soul harvested into ATP; Good = carbon retained pre-oxidation; Normal = CO2 without full harvest; Bad = failure/cycle-trap/host-death/critical-residue-break (Pitfall 9 framing still pending).
- **Line 99 (Key Decisions — Stat/XP row):** Rationale reworded for soul framing.
- **Line 104 (Key Decisions — ATP/True-Ending row):** Marked "— Resolved (soul-jump)" with full resolution provenance. C14-decay row (line 105) left Pending (unchanged).
- **Line 109 (footer):** Updated to 2026-08-13.

### .planning/REQUIREMENTS.md
- **Line 4 (Core Value):** ATP clarified as "the hero's electrons harvested into energy via the ETC".
- **Line 24 (STORY-02):** True tier reframed to soul-jump; all 4 ending tiers re-described with consistent semantics.

### .planning/ROADMAP.md
- **Line 102 (Phase 5 success criterion 1):** Updated to "RESOLVED via the soul-jump reframing" (framing decision DONE; per-claim citation approval for ETC chemistry remains a separate Phase 7+ gate).
- **Line 171 (07-04 plan label):** Reframed from "True-ending carbon fate" to "True-ending soul-jump (hero's electrons -> ATP via ETC/ATP synthase)".

### .planning/STATE.md
- **Line 7 (Core value):** ATP clarified as "the hero's electrons harvested into energy via the ETC".
- **Line 74 (Phase 5 blocker):** Updated — Pitfall 4 now RESOLVED; remaining 3 decisions (C14-decay/Pitfall 9, anaerobic framing, batch-vs-per-claim) still Pending. Anaerobic decision now specifically gates Phase 5.1.
- **Line 75 (Phase 5.1 blocker):** ATP decision noted as resolved via soul-jump; True-ending node = electron harvest, NOT carbon-becomes-ATP.

### .planning/research/FEATURES.md
- **Line 45 (D3 row):** Four ending tiers reframed to soul-jump; Pitfall 4 resolution noted.
- **Line 66 (A3 row):** Stat/XP rationale reworded ("The True ending is the hero's electrons harvested into ATP (soul-jump reframing)").
- **Line 114 (MVP cast path):** True-ending path expanded to include PDH -> TCA -> ETC -> ATP synthase; soul-jump path noted as defining the True ending.

### .planning/research/PITFALLS.md
- **Pitfall 4 (after line 98 heading):** RESOLVED note block inserted at the top (before the Severity line). Original pitfall text (lines 100-123) retained verbatim for provenance. Note states: soul-jump reframing adopted; C14 = tracking label; Pitfall 9 still Pending.

### .planning/research/SUMMARY.md
- **Line 16 (executive summary):** ATP-conflict sentence marked RESOLVED via soul-jump reframing.
- **Line 100 (Pitfall 4 key-finding bullet):** Marked RESOLVED — human adopted soul-jump (a variant of option c).
- **Line 120 (Critical Pre-Content Decisions item 1):** Marked RESOLVED — no longer blocks True-Ending narrative.
- **Line 160 (Gaps to Address item 1):** Marked RESOLVED via soul-jump reframing.

### README.md
- **Verified clean — NO edit.** Line 13 ("controls a C14 atom — the hero") uses C14-as-tracking-label framing (not a fate claim). No assertion that the C14 carbon becomes ATP or enters oxidative phosphorylation was found.

## Grep Re-Scan Results (Verification)

Three `grep -rn` scans run from repo root (per plan; `rg` denied by opencode.json). Results below exclude `001-PLAN.md` (the plan file itself, which naturally contains the old strings as part of its instructions).

### Scan 1: `become ATP | becomes ATP | end up as ATP`
Matches found ONLY in:
- **spec.md:15** — human's prose, HTML-comment-annotated (expected).
- **PITFALLS.md:98,100,105,110** — heading + RESOLVED note + original provenance text (explaining why it's wrong) (expected).
- **SUMMARY.md:16,100** — provenance quoting the spec, both marked RESOLVED (expected).
- **PROJECT.md:104** — inside the RESOLVED Key Decisions row, quoting the spec's original wording in quotes: `(The spec's original "become ATP" line...)` (provenance/resolution context — acceptable).

**No bare assertions** in REQUIREMENTS.md, ROADMAP.md, STATE.md, FEATURES.md, or README.md. ✅

### Scan 2: `enters oxidative phosphorylation`
- **PITFALLS.md:100** — RESOLVED note: "a labeled carbon **never** enters oxidative phosphorylation" (the CORRECT claim, not a wrong one — acceptable per plan).
- ROADMAP.md line 171 **no longer matches** (reframed to "soul-jump"). ✅

### Scan 3: `carbon.*becomes.*ATP | C14.*ATP carbon`
Matches found ONLY in:
- **PITFALLS.md:100** — RESOLVED note saying the carbon does **NOT** become ATP carbon (correct claim).
- **PITFALLS.md:105** — original provenance explaining why carbon-becomes-ATP is wrong ("A carbon atom tracing respiration does **not** become the carbon skeleton of ATP").
- **PITFALLS.md:122** — original provenance "warning sign" text (describing what's WRONG).
- **STATE.md:75** — "NOT carbon-becomes-ATP" (a NEGATION in RESOLVED context — the correct claim).

**No bare assertions** elsewhere. ✅

### Conclusion
All grep re-scan results match the expected-match profile. No bare wrong-claim assertions remain in any planning doc. All matches are in clearly-marked provenance/RESOLVED context.

## Pitfall Status Confirmation

- **Pitfall 4 (ATP/True-Ending carbon-fate reframing):** ✅ **RESOLVED** (2026-08-13) via the soul-jump reframing. Confirmed in PROJECT.md Key Decisions table ("— Resolved (soul-jump)"), PITFALLS.md (RESOLVED note block), SUMMARY.md (4 RESOLVED markers).
- **Pitfall 9 (C14 decay timescale):** ✅ **Still Pending.** Confirmed in PROJECT.md Key Decisions table ("— Pending", unchanged), STATE.md blocker line 74 ("still Pending"), PITFALLS.md RESOLVED note ("Pitfall 9 remains Pending and is NOT resolved here").

## Decisions Made
- **Soul-jump reframing adopted (locked decision, implemented per plan):** The hero's electrons (narrative "soul") are harvested into ATP via the ETC -> ATP synthase after the RNG-weighted TCA path; the carbon body is released as CO2 via PDH + TCA decarboxylations. C14 is a tracking label, not a fate determinant. Tied to the RNG TCA shuffle (the soul reaches ATP only via the RNG-weighted path). Actual ETC/ATP-synthase chemistry claims still require per-claim citation approval in Phase 7+.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] FEATURES.md line 114 exact-match string mismatch**
- **Found during:** Task 2 (FEATURES.md MVP cast path edit)
- **Issue:** The plan's OLD string used `(e.g. hexokinase` (no comma after "e.g.") but the actual file content had `(e.g., hexokinase` (with comma). The edit tool could not find the oldString.
- **Fix:** Re-ran the edit with the corrected OLD string matching the actual file content `(e.g., hexokinase → … → ATP synthase)`. The NEW string also uses the same comma style for consistency. The substantive edit (adding PDH → TCA → ETC to the path + the soul-jump note) is identical to what the plan intended.
- **Files modified:** .planning/research/FEATURES.md
- **Verification:** Read-back of line 114 confirms the edit applied correctly.
- **Committed in:** `73fb7c6` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — exact-match string typo in plan)
**Impact on plan:** Trivial. The plan's intent was fully preserved; only the matching string's punctuation differed. No scope creep, no content change.

## Issues Encountered
None beyond the single deviation above.

## User Setup Required
None — documentation-only task, no external services or configuration.

## Next Phase Readiness
- **Pitfall 4 no longer blocks Phase 5.1 (Story Graph Design):** The ATP/True-Ending decision is resolved. The True-ending node in the story graph = electron harvest (soul-jump), NOT carbon-becomes-ATP. Phase 5.1 can proceed once Phase 2 is complete and the anaerobic framing decision is made.
- **Pitfall 9 (C14 decay) still gates Phase 5:** Remains a Pending science-framing decision for the human. Does not block Phase 5.1 (only the ATP + anaerobic decisions gate 5.1; ATP is now done, anaerobic remains).
- **Per-claim citation approval for ETC/ATP-synthase chemistry remains a Phase 7+ gate:** This task resolved the FRAMING decision, not the per-claim chemistry citations. ROADMAP.md Phase 5 criterion 1 clarifies this distinction.
- **Ending semantics are now consistent across all docs:** True = soul (electrons) harvested into ATP; Good = carbon body retained pre-oxidation; Normal = CO2 without full harvest; Bad = failure/cycle-trap/host-death/critical-residue-break. Future content-authoring phases (7-9) have a single canonical reference in PROJECT.md Key Decisions.

---
*Quick task: 001-resolve-pitfall-4-c14-atp-carbon-fate-co*
*Completed: 2026-08-13*
