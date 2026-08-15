---
phase: 05-pre-content-key-decisions-source-approval
plan: 03
subsystem: decisions
tags: [source-approval, hybrid, high-stakes, taxonomy, warning-flag]

# Dependency graph
requires:
  - phase: 01 (Foundations & Citation Gate)
    provides: the Phase 1 citation gate (tools/check_citations.py) whose predicate approval_status == "approved" is preserved UNCHANGED by this decision; the loader (c14/citations.py:87-97) that ignores unknown fields so the extended schema loads with zero change
  - phase: 05 Plan 05-01
    provides: SC#1 soul-jump metaphor (metamorphosis) + SC#2 C14-decay DROP + ending-count distribution (1 True + several Normal/Good + many Bad) — the framing context this decision sits inside
  - phase: 05 Plan 05-02
    provides: SC#3 anaerobic framing (d) + invariant re-wording (i) + host (mammal/human) — the 3rd of 4 Key Decisions resolved before this one
  - phase: 05 05-RESEARCH-source-approval.md
    provides: 4 workflow options (a-strict / b-batch / c-hybrid / d-per-source) + the comparison matrix + the advisory high-stakes taxonomy + backward-compat analysis (gate predicate preserved, loader ignores unknown fields)
provides:
  - SC#4 source-approval WORKFLOW decided — option (c) HYBRID + user-requested routine-claim warning flag (review_tier=routine + inherits_source_approval=true for leisure spot-check; NOT a blocking gate)
  - High-stakes taxonomy confirmed (advisory list adopted as-is): HIGH-STAKES=[RNG-weights, protonation-defaults, carbon-fate, contested] (individual per-claim review); ROUTINE=[enzyme-catalyzes-reaction-X, enzyme name/EC/cofactor, PDB existence/resolution/citation, pathway ordering] (source-inherited fast-track + warning flag)
  - Phase 1 gate backward-compatibility CONFIRMED — approval_status == "approved" preserved (Pitfall 6); loader ignores extended fields; data/sources.json never read by the gate
  - Plan 04 (schema implementation + first-batch population) UNBLOCKED — must CREATE data/sources.json (workflow is c, not a); must populate extended citations.json fields (source_id, review_tier, inherits_source_approval, review_notes, claim_text)
  - Plan 05 (human first-batch approval checkpoint) UNBLOCKED — approve sources first (batch), then high-stakes claims individually, then spot-check routine claims at leisure
affects: [Plan 05-04, Plan 05-05, Phase 7, Phase 8, Phase 9]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hybrid source-approval workflow: sources approved up front (batch) → high-stakes claims individually reviewed → routine claims source-inherited (fast-track) + warning-flagged for leisure spot-check. Process convention only — NOT a gate-enforcement change."
    - "Routine-claim warning flag: review_tier='routine' + inherits_source_approval=true in the registry. VISIBILITY mechanism (human filters + spot-checks at leisure), NOT a blocking gate. Phase 1 gate still passes routine claims via the source's approval."

key-files:
  created: []
  modified:
    - .planning/PROJECT.md (row 106 RESOLVED via (c) hybrid + taxonomy + warning flag + backward-compat + throughput; row 102 cross-ref; footer 2026-08-15)

key-decisions:
  - "SC#4 workflow = option (c) HYBRID + user-requested routine-claim warning flag: sources approved up front (batch), high-stakes claims individually reviewed, routine claims source-inherited (fast-track) + flagged with review_tier=routine + inherits_source_approval=true for leisure spot-check. The warning flag is a VISIBILITY mechanism, NOT a blocking gate — the Phase 1 gate still passes routine claims via the source's approval. Human's exact words: '(c) plus a warning on auto-stuff so i can check when i have time'."
  - "High-stakes taxonomy = advisory list adopted as-is: HIGH-STAKES (individual per-claim review) = [RNG-weights, protonation-defaults, carbon-fate, contested]; ROUTINE (source-inherited fast-track + warning flag) = [enzyme-catalyzes-reaction-X, enzyme name/EC/cofactor, PDB existence/resolution/citation, pathway ordering]."
  - "Phase 1 gate UNCHANGED — predicate approval_status == 'approved' preserved (strict equality, c14/citations.py:109, Pitfall 6 preserved); loader (c14/citations.py:87-97) ignores extended fields (source_id, review_tier, inherits_source_approval, review_notes, claim_text) so they load cleanly with zero loader change; data/sources.json is a separate file the gate never reads (verified)."

patterns-established:
  - "Key Decisions row resolution pattern (continued from 05-02): when a deferred row is resolved by a checkpoint:decision, update the Decision column (expand option list if research surfaced more), the Rationale column (the chosen tradeoff), and the Outcome column (the RESOLVED status + one-line description + backward-compat note + throughput estimate). Cross-reference from related prior rows (row 102 → row 106) without deleting provenance."

# Metrics
duration: 2min
completed: 2026-08-15
---

# Phase 5 Plan 03: SC#4 Source-Approval Workflow + High-Stakes Taxonomy Summary

**SC#4 source-approval workflow resolved via option (c) HYBRID + user-requested routine-claim warning flag (review_tier=routine + inherits_source_approval=true for leisure spot-check); high-stakes taxonomy confirmed (advisory as-is); Phase 1 gate unchanged**

## Performance

- **Duration:** ~2 min (continuation segment — Task 2 only; Task 1 was the prior-agent checkpoint:decision that the orchestrator resolved with the human)
- **Started:** 2026-08-15T14:14:57Z (continuation segment)
- **Completed:** 2026-08-15T14:17:11Z
- **Tasks:** 2 (1 checkpoint:decision [human, prior agent] + 1 auto-document [this agent])
- **Files modified:** 1 (.planning/PROJECT.md)

## Accomplishments
- SC#4 source-approval WORKFLOW decided by the human and documented in PROJECT.md Key Decisions row 106 — option (c) HYBRID: sources approved up front (batch), high-stakes claims individually reviewed, routine claims source-inherited (fast-track). Honors BOTH the per-claim safety guarantee on load-bearing claims AND Pitfall 7's timeline risk (~33h for full content under strict per-claim → ~6-8h under hybrid).
- High-stakes taxonomy CONFIRMED (advisory list adopted as-is): HIGH-STAKES (individual per-claim review) = [RNG-weights, protonation-defaults, carbon-fate, contested]; ROUTINE (source-inherited fast-track + warning flag) = [enzyme-catalyzes-reaction-X, enzyme name/EC/cofactor, PDB existence/resolution/citation, pathway ordering].
- User-requested ENHANCEMENT documented: routine/source-inherited claims are FLAGGED with `review_tier: "routine"` + `inherits_source_approval: true` in the registry so the human can spot-check them at leisure ("when i have time"). This is a VISIBILITY/FLAG mechanism, NOT a blocking gate — the Phase 1 gate still passes routine claims via the source's approval. The human can filter routine claims by `review_tier=routine` or `inherits_source_approval=true` to review them at any time.
- Phase 1 gate backward-compatibility CONFIRMED and recorded: predicate `approval_status == "approved"` preserved (strict equality, c14/citations.py:109, Pitfall 6 preserved); the loader (c14/citations.py:87-97) ignores the extended fields (source_id, review_tier, inherits_source_approval, review_notes, claim_text) so they load cleanly with zero loader change; data/sources.json is a separate file the gate never reads (verified by prior agent).
- Row 102 cross-referenced to row 106 (provenance preserved): per-claim checkpoint retained for HIGH-STAKES claims; routine claims source-inherited (hybrid option c) with a warning flag for leisure spot-check.
- ALL 4 Phase 5 Key Decisions now RESOLVED: SC#1 metaphor (metamorphosis), SC#2 DROP (C14-decay), SC#3 anaerobic framing (d), SC#4 workflow (c hybrid + warning flag). Phase 5 framing decisions complete; remaining Phase 5 work is mechanical (Plan 04 schema + Plan 05 human approval).

## Task Commits

Each task was committed atomically:

1. **Task 1: SC#4 source-approval workflow decision + high-stakes taxonomy (checkpoint:decision)** - `—` (human chose workflow=c-hybrid + warning-flag enhancement, taxonomy=advisory-as-is)
2. **Task 2: Document SC#4 hybrid workflow + high-stakes taxonomy + routine-claim warning flag** - `6bb33dd` (docs)

**Plan metadata:** `pending` (docs: complete plan — committed after SUMMARY/STATE)

## Files Created/Modified
- `.planning/PROJECT.md` — Key Decisions row 106 (Batch-by-source vs strict per-claim approval): Decision column expanded to list all 4 research options (a/b/c/d) + chosen tradeoff; Outcome cell changed from "— Pending" to "RESOLVED via option (c) HYBRID" + the full taxonomy (HIGH-STAKES=[RNG-weights, protonation-defaults, carbon-fate, contested]; ROUTINE=[enzyme-catalyzes-reaction-X, enzyme name/EC/cofactor, PDB existence/resolution/citation, pathway ordering]) + the user-requested warning-flag enhancement (review_tier=routine + inherits_source_approval=true for leisure spot-check; NOT a blocking gate) + the backward-compat note (Phase 1 gate UNCHANGED — approval_status == 'approved' preserved, c14/citations.py:109, Pitfall 6; loader ignores extended fields, c14/citations.py:87-97; data/sources.json never read by gate) + the throughput estimate (glucose first batch ~1.5h; full content ~6-8h). Row 102 (Source approval = per-claim checkpoint): appended cross-reference note ("Refined in row 106: per-claim checkpoint retained for HIGH-STAKES claims; routine claims source-inherited (hybrid option c) with a warning flag for leisure spot-check") to the Rationale column; Outcome changed from "— Pending" to "Refined by row 106 (hybrid workflow, 2026-08-15)". Footer last-updated note prepended with "Source-approval workflow resolved via option (c) HYBRID + routine-claim warning flag; high-stakes taxonomy confirmed".

## Decisions Made

- **SC#4 workflow (human, via checkpoint:decision):** Option (c) HYBRID + user-requested routine-claim warning flag. The human's exact words: "(c) plus a warning on auto-stuff so i can check when i have time". Interpretation: sources approved up front (batch); high-stakes claims get individual per-claim review; routine claims get source-inherited fast-track AND are FLAGGED with `review_tier: "routine"` + `inherits_source_approval: true` in the registry so the human can spot-check them at leisure. The warning flag is a VISIBILITY mechanism, NOT a blocking gate — the Phase 1 gate still passes routine claims via the source's approval. Rationale: honors BOTH the per-claim safety guarantee on load-bearing claims (RNG weights, protonation defaults, carbon-fate, contested) AND Pitfall 7's timeline risk (~33h strict → ~6-8h hybrid for full content; ~1.5h for the glucose first batch).
- **SC#4 high-stakes taxonomy (human, via checkpoint:decision):** "Use advisory list as-is". HIGH-STAKES (individual per-claim review) = [RNG-weights, protonation-defaults, carbon-fate, contested]; ROUTINE (source-inherited fast-track + warning flag) = [enzyme-catalyzes-reaction-X, enzyme name/EC/cofactor, PDB existence/resolution/citation, pathway ordering]. This is the research's advisory list (§1c) adopted verbatim.
- **Phase 1 gate backward-compatibility (verified, not decided):** The gate predicate `approval_status == "approved"` (strict equality, NOT `!= "pending"`) is preserved for ALL four workflow options — the workflow is a PROCESS convention, not a gate-enforcement change. The loader (c14/citations.py:87-97) ignores the extended fields (source_id, review_tier, inherits_source_approval, review_notes, claim_text) so they load cleanly with zero loader change. data/sources.json is a separate file the gate never reads (tools/check_citations.py uses only registry.contains/is_approved/status — verified by prior agent). Pitfall 6 preserved.

## Deviations from Plan

None — plan executed exactly as written, with the human's checkpoint:decision choices applied. The PROJECT.md row-106 edit matched the orchestrator's prescribed text (workflow + taxonomy + warning-flag enhancement + backward-compat note + throughput estimate). The row-102 cross-reference note was appended to the Rationale column (original rationale preserved per orchestrator instruction). The footer was updated. No auto-fixes were needed (all edits were documentation-only and applied cleanly on the first try). The warning-flag enhancement was the human's own addition to option (c) ("plus a warning on auto-stuff so i can check when i have time") — this is a user-requested refinement, not a deviation from the plan (the plan's checkpoint:decision explicitly invited the human to pick an option; the human picked (c) + added the warning flag, which the schema already supports per the research).

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. (This plan records a workflow decision only; no source was approved — that is Plan 05's job. No schema code was written — that is Plan 04's job.)

## Next Phase Readiness

**Ready for downstream Phase 5 plans (04 + 05) + content phases (7-9).** The SC#4 workflow decision is documented and unblocks:

- **Plan 05-04 (schema implementation + first-batch population):** CREATE `data/sources.json` (workflow is c, not a — sources.json is REQUIRED). Populate the extended `data/citations.json` schema fields on seed claims: `source_id` (links each claim to its source in sources.json), `review_tier` ("high-stakes" or "routine"), `inherits_source_approval` (true for routine, false for high-stakes), `review_notes` (optional human-review notes), `claim_text` (the factual assertion). Set `review_tier="routine"` + `inherits_source_approval=true` on routine claims (the warning flag — the human spot-checks these at leisure). Set `review_tier="high-stakes"` + `inherits_source_approval=false` on high-stakes claims (these get individual per-claim review in Plan 05). `data/citations.README.md` MUST document the warning-flag mechanism (how the human filters routine claims for leisure spot-check: filter on `review_tier=routine` or `inherits_source_approval=true`). The optional `tools/check_sources.py` drift-detection gate is ADVISORY (not required for v1 — the warning flag is the visibility mechanism; the Phase 1 gate is the only hard gate). Do NOT populate NUBASE2020-C14 or C14-TIME-01 (DROPPED in Plan 05-01).
- **Plan 05-05 (human first-batch approval checkpoint):** The human's first-batch approval sequence: (1) approve the SOURCES first (batch — the source-level approval that routine claims inherit); (2) approve the HIGH-STAKES claims individually (per-claim review — TCA-RNG-CITRATE-PROCHIRALITY-01, TCA-RNG-WEIGHT-01); (3) spot-check the ROUTINE claims at leisure (GLY-PFK-01, CAST-PFK-PDB-01, CAST-CSC-PDB-01 — these auto-approve via the source's approval but are FLAGGED with review_tier=routine + inherits_source_approval=true for the human to filter + review when they have time). Also remove NUBASE2020-C14 + C14-TIME-01 (DROPPED in Plan 05-01).
- **Phase 7 (All Glucose Endings) / Phase 8 (FA + Alcohol) / Phase 9 (Anaerobic + Full Cast):** content authoring now has a defined approval workflow — each content batch goes through: source approval (batch) → high-stakes per-claim review → routine source-inherited fast-track + warning flag. The ~400 full-content claims (Pitfall 7) are now tractable (~6-8h total under hybrid vs ~33h under strict per-claim).

**Blockers/concerns:** None from this plan. ALL 4 Phase 5 Key Decisions are now RESOLVED (SC#1 metaphor = metamorphosis; SC#2 C14-decay = DROP; SC#3 anaerobic framing = option (d); SC#4 workflow = option (c) hybrid + warning flag). Phase 5 framing decisions are COMPLETE. The remaining Phase 5 work is mechanical: Plan 04 (schema + first-batch populate) and Plan 05 (human approval checkpoint). No source was auto-approved by this plan. The warning-flag enhancement is a visibility mechanism — the human reviews routine claims at their own pace, not as a blocking gate.

---
*Phase: 05-pre-content-key-decisions-source-approval*
*Completed: 2026-08-15*
