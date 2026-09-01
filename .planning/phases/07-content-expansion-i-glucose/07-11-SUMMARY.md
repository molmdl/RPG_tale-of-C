---
phase: 07-content-expansion-i-glucose
plan: 11
subsystem: content
tags: [bad-ending-pool, story-content, citation-gate, proton-leak, uncoupling, no-ros-v1, anti-confusion, py36, json]

# Dependency graph
requires:
  - phase: 07-04 (approval batch C ledger)
    provides: the 14 bad-pool mapping VERDICTs (which claims approved vs pending-generic), no-ROS-v1 + no-numeric-yields framing rules, 1ZP0 optional-load condition
  - phase: 07-05 (registry landing)
    provides: data/citations.json 77-claim registry with the 8 bad-pool claims APPROVED (BAD-HOST/CRIT/ACTSITE/DIFFUSE/CHANNEL/COFACTOR + ETC-UCP-01) and 4 PENDING (BAD-MISFOLD/INHIB/AGGREG/PH); PDB-1ZP0 source still pending
  - phase: 5.2 (bad-ending extensibility convention)
    provides: frozen 15-node pool structure + the parametrized edit.prompt-reachability convention test that auto-covers text-only edits
provides:
  - "Authored data/story_glucose/bad_endings.json: all 14 bad endings + edit.prompt carry final two-layer text; 8 nodes bind approved claims, 7 nodes carry claim_ids [] (2 mechanic-narrative + 4 pending-claim generic + the structural stub)"
  - "bad.proton_leak rewritten PROTONS-first (gradient bleed, PMF dissipated as heat, ATP synthesis falls) — zero electron-leak/ROS wording per batch-C Decision 7"
  - "Zero PLACEHOLDER_PHASE7* in bad_endings.json — the bad-pool bucket of the citation-gate residual is discharged (gate MISSING 50→29, the remainder owned by sibling plans)"
affects: [07-09/10 (sibling ending plans, framing consistency), 07-13 (tca content), 07-16 (final sweep: expects the remaining placeholder buckets), future bad-pool source verifications (BAD-MISFOLD/INHIB/AGGREG/PH upgrade path), phase 11 (docs)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pending-claim node convention: claim_ids [] + GENERIC text (no specific mechanism claims) until the source verifies — text upgrade path documented, not blocked"
    - "Differentiated sibling endings: enzyme_collapse = single-enzyme loss of folded state vs misfolded_aggregate = cell-level quality-control/clearance story (cross-referenced in both teaching texts)"
    - "Mechanic-narrative endings carry NO science claims — Pitfall-10 explanatory template (the game models a curated set) only"

key-files:
  created:
    - .planning/phases/07-content-expansion-i-glucose/07-11-SUMMARY.md
  modified:
    - data/story_glucose/bad_endings.json
    - .planning/STATE.md

key-decisions:
  - "Claim binding per the registry's actual statuses (verified live at execution): 8 approved claims bound; BAD-MISFOLD-01/INHIB-01/AGGREG-01/PH-01 stayed claim_ids [] with generic text — their sources are UNVERIFIED in the registry, so no specific mechanism is asserted"
  - "1ZP0 optional load DECLINED: PDB-1ZP0 is still a pending source record (07-05 fetched metadata but did not approve), so wrong_substrate_trapped keeps [hide_all] and its text names no compounds (malonate/3-nitropropionate wording owed its own chemistry source per 07-04 verdict #6)"
  - "active_site_destroyed reuses BAD-ACTSITE-01 (the registry's single approved active-site claim; 07-04 verdict #11 = 'same class as #7'); texts differentiate severity, claims share the id"
  - "denature_ph stays claim-light per the pending BAD-PH-01: dramatic text softened from the stub's 'ionic bonds and salt bridges' to the generic 'interactions that held the enzyme's shape'; teaching carries ONLY the human-mandated physiological caveat (matrix ~pH 7.8, pathology/experimental framing) + the protonation-feature tie-in"
  - "edit.prompt keeps its structural-stub text byte-identical; only claim_ids PLACEHOLDER_PHASE7_EDIT→[] (stub carries no science; runtime bypasses via EditRouter per research OQ#8)"
  - "cycle_trap teaching distinguishes mechanics from science: the 0.5/0.5 loop is a game device, the death sentence is BAD-HOST-01 (S-BIOX verbatim anchor); no futile-cycling claim asserted"

patterns-established:
  - "Bad-ending two-layer pattern: dramatic = failure-mode vignette; teaching = the §6 explanation, claim-grounded where approved, purely generic where pending"
  - "Proton-leak wording rule in practice: PROTONS bleed/slip/dissipate; electrons only 'keep flowing' (never leak) — the anti-ROS guard is grep-checkable ('electrons leak' count = 0)"

# Metrics
duration: ~9 min
completed: 2026-09-01
---

# Phase 7 Plan 11: Bad-Ending Pool Content Summary

**All 15 bad-pool nodes authored per the batch-C §6 mapping: 8 approved claims bound (BAD-HOST/CRIT/ACTSITE×2/DIFFUSE/CHANNEL/COFACTOR + ETC-UCP-01), 4 pending-claim nodes kept generic, the proton-leak text rewritten PROTONS-first, and zero PLACEHOLDER_PHASE7* left in the file — with tier/tags/on_enter/choices byte-identical to the frozen pool.**

## Performance

- **Duration:** ~9 min (19:44–19:52 UTC; single-task plan, one interruption-free run)
- **Started:** 2026-09-01T19:44:00Z
- **Completed:** 2026-09-01T19:52:32Z
- **Tasks:** 1/1
- **Files modified:** 2 (data/story_glucose/bad_endings.json + STATE.md; + this SUMMARY)

## Accomplishments

- All 14 bad endings + the edit.prompt stub carry final two-layer text (dramatic vignette + teaching explanation) matching each node's §6 failure mode; the frozen structural half (tier/tags/on_enter/choices) is byte-identical to the pre-edit pool (machine-verified against git HEAD).
- Claim swaps landed exactly per the registry's live statuses: cycle_trap→BAD-HOST-01, critical_residue_break→BAD-CRIT-01, broken_active_site + active_site_destroyed→BAD-ACTSITE-01, lost_in_cytosol→BAD-DIFFUSE-01, proton_leak→ETC-UCP-01, substrate_channel_blocked→BAD-CHANNEL-01, cofactor_lost→BAD-COFACTOR-01; lost_connection/released_from_host → [] (Pitfall-10 mechanic-narrative template, no science claimed); enzyme_collapse/wrong_substrate_trapped/misfolded_aggregate/denature_ph_change → [] (pending claims, generic text); edit.prompt → [] (stub).
- bad.proton_leak satisfies the Decision-7 mandate: the dramatic text says the gradient bleeds away, protons slip back without turning ATP synthase, the proton-motive force dissipates as warmth — the only electron mention is "the electrons themselves keep flowing" (claim-accurate, never "electrons leak"; grep-verified zero electron-leak/ROS wording file-wide).
- The two misfold siblings differentiate as mandated: enzyme_collapse = single-enzyme loss of the folded working shape; misfolded_aggregate = the cell-level quality-control/clearance story; each teaching text cross-references the other.
- The bad-pool bucket of the citation-gate residual is discharged: gate references from bad_endings.json nodes dropped to 0 (grep PLACEHOLDER_PHASE7 = 0; overall MISSING 50→29, the remainder owned by the still-running sibling wave-3 plans).

## Task Commits

Each task was committed atomically:

1. **Task 1: Author all bad-pool texts + claim swaps** - `a3e20bd` (feat)

**Plan metadata:** (this commit) docs(07-11): complete bad-ending pool content plan

## Files Created/Modified

- `data/story_glucose/bad_endings.json` - the authored bad-ending pool: 15 nodes, two-layer text + approved-only claims; frozen structure untouched (43 insertions / 43 deletions — text+claims only)
- `.planning/STATE.md` - position/progress update (this plan)

## Decisions Made

- **Claim binding followed the registry, not just the ledger labels.** 07-04 verdict #6 marked BAD-INHIB-01 "MEDIUM", but 07-05 landed it (and BAD-MISFOLD/AGGREG/PH) as PENDING in data/citations.json — so all four nodes carry claim_ids [] and strictly generic text (no named inhibitors, no salt-bridge mechanism, no proteostasis specifics). Verified against the live registry before authoring.
- **1ZP0 optional load declined.** The plan's conditional (add `pdb:1ZP0` load if the anchor was approved) resolves to NOT approved: PDB-1ZP0 remains a pending source record, so `[hide_all]` stays and the structural anchor remains a future upgrade when the source lands.
- **active_site_destroyed shares BAD-ACTSITE-01 with broken_active_site** (07-04 verdict #11 = "same class as #7"; the registry has exactly one approved active-site claim). Texts differentiate severity; the claim id is shared.
- **denature_ph dramatic softened.** The skeleton stub asserted "ionic bonds and salt bridges" — the specific mechanism of the still-pending BAD-PH-01. Authored text keeps the general unfolding principle only; the teaching layer carries the human-mandated caveat (matrix ~pH 7.8; large pH shift = pathology/experimental condition) + the protonation-feature tie-in.
- **No player-facing claim ids or "pending" notes** in text — the claim binding lives in `claim_ids`; the generic-vs-cited distinction is documented here instead (per-node upgrade notes below).

## Deviations from Plan

None - plan executed exactly as written. (The plan's `<verification>` block lists `python3.6 tools/check_citations.py` without the required `--story/--registry` args — run with `--story data/story_glucose --registry data/citations.json`, the same invocation used since Phase 1. No behavior deviation.)

## Issues Encountered

- None blocking. Note: two sibling wave-3 plans (07-07 intro, 07-10 endings) committed while this plan ran; no file overlap (their diffs touch intro.json / endings.json exclusively, verified via `git show --stat`). The post-edit gate MISSING count reflects both (50→29 = this plan's 15 + their 6); the remaining 29 belong to the still-pending glycolysis/TCA/anaerobic/stub buckets per the 07-05 residual accounting.

## Pending-claim upgrade path (for the future source-verification plan)

| Node | Pending claim | Text unlock when verified |
|------|---------------|---------------------------|
| bad.enzyme_collapse | BAD-MISFOLD-01 (folding source) | name the folding/destabilization mechanism, bind the claim |
| bad.wrong_substrate_trapped | BAD-INHIB-01 + PDB-1ZP0 (pending source) | name the inhibitor chemistry (e.g. malonate/3-NP), add the 1ZP0 on_enter load (`sdh_inhibited`) |
| bad.misfolded_aggregate | BAD-AGGREG-01 (proteostasis source) | name quality-control/degradation specifics, bind the claim |
| bad.denature_ph_change | BAD-PH-01 (denaturation source) | restore the salt-bridge mechanism wording, bind the claim |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The bad-ending pool is content-complete and gate-clean; the parametrized 5.2 convention test auto-covered the text-only edit (20/20 reachability tests green, 324 suite green).
- Remaining Phase 7 gate residual (29 MISSING) is owned by the sibling wave-3 plans (glycolysis/TCA/ETC/anaerobic/stub buckets) and the plan-16 sweep.
- The four pending bad-pool claims are cleanly queued for a future source-verification landing (upgrade table above) — no text rework needed beyond the listed unlocks.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-01*
