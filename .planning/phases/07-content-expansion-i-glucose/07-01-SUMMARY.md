---
phase: 07-content-expansion-i-glucose
plan: 01
subsystem: planning-decisions
tags: [decision-ledger, phase-7, story-graph, edits-json, citations-registry, test-invariants]

# Dependency graph
requires:
  - phase: 07-content-expansion-i-glucose research
    provides: "07-RESEARCH-content-mechanics.md (§4/§7/§11), 07-RESEARCH-glycolysis-pyruvate.md (§9 DC-A/DC-B, §10 OQ-C/OQ-K) — the decision points + recommendations"
  - phase: 05.1-story-graph-design
    provides: "FROZEN skeleton: 55 nodes / 21 endings (1T+3G+2N+15B) / 14 edit-allowed / start intro.preface; 05.2 extensibility convention"
  - phase: 06-qt-ui-minimal-playable-mvp
    provides: "324-test baseline; TestPyrBranchRuntimeEligibility (5 tests); Phase 6 debug conclusion (restored branch nodes needed)"
provides:
  - "Decision ledger: 7 recorded structural/mechanics outcomes binding Phase 7 plans 05-16 (no later plan re-decides)"
  - "DC-A topology sanction: the ONLY sanctioned topology change this phase (+2 restored nodes, plan 12)"
  - "M1 approval policy: -cand ids kept verbatim on approval (flip approval_status only)"
  - "Downstream test-obligation ownership: plan 06 (TestPyrBranchRuntimeEligibility), plan 12 (55→57 counts), plan 16 (final 57/21 pins)"
affects: [plans 05, 06, 07, 08, 12, 13, 14, 16; Phase 8 (fa.stub/alc.stub); Phase 9 (real 20-AA cast)]

# Tech tracking
tech-stack:
  added: []   # checkpoint plan — no code, no dependencies
  patterns:
    - "Decision-ledger plan: checkpoint-only plan whose SUMMARY is the binding artifact; later plans implement recorded outcomes, never re-decide"

key-files:
  created:
    - ".planning/phases/07-content-expansion-i-glucose/07-01-SUMMARY.md (this ledger)"
  modified: []   # NO code or data files touched (per plan frontmatter files_modified: [])

key-decisions:
  - "DC-A = dc-a-add: add gly.pfk_restored + tca.aconitase_restored (55→57; plan 12 implements)"
  - "PLACEHOLDER_PHASE8: fa.stub/alc.stub left untouched, documented as Phase 8 stubs"
  - "DC-B host_o2_low: cond-neutralize both pyr.branch choices + honest O2-framing labels; plan 06 owns TestPyrBranchRuntimeEligibility updates"
  - "M5: NO known-wrong 1b entries in Phase 7 edits.json"
  - "M1: KEEP -cand claim_ids when approving — flip approval_status only; tests pin ids verbatim"
  - "OQ-C: real 20-AA cast deferred to Phase 9; bundled _smoke.pdb stays through Phase 7"
  - "OQ-K: test-impact ack = yes (plan 06 + plan 12 own the named test updates)"

patterns-established:
  - "Outcome: line convention — one verbatim human verdict per decision item, machine-scannable (plan key_links pattern)"

# Metrics
duration: 6 min
completed: 2026-09-01
---

# Phase 7 Plan 01: Structural + Mechanics Decision Checkpoint Summary

**Decision ledger locking Phase 7 topology/mechanics before any approval batch or content authoring: all 7 research recommendations accepted by the human, recorded verbatim below; no engine/molops surgery sanctioned; plans 05-16 implement, never re-decide.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-01T02:40:28Z
- **Completed:** 2026-09-01T02:46:12Z
- **Tasks:** 1 of 1 (checkpoint:decision — continuation; the human verdict arrived between the original checkpoint return and this continuation)
- **Files modified:** 1 (this SUMMARY — no code/data files)

## Decision Ledger (7 recorded outcomes)

Human verdict (verbatim): **all 7 recommendations accepted.** Each `Outcome:` line records the decision verbatim + rationale + the downstream plan that implements it.

### 1. DC-A — Restoration-branch-node topology

**Outcome:** dc-a-add — add gly.pfk_restored + tca.aconitase_restored (55→57; plan 12 implements; test-count updates owed).

**Rationale:** Fixed node ids give a clean restoration narrative and match the plan index, the 05.2 extensibility convention, and the Phase 6 debug-session conclusion ("Phase 7 must add BOTH the edits.json entries AND the restore branch nodes"). Only these two enzymes get restored nodes (PROJECT.md row 112: 1–2 enzymes carry the full restoration arc; research §4.4). The rejected option (dc-a-route: routing known edits to existing nodes) would re-fire on_enter on re-entry and contradict the fixed ids already pinned in the plan index.

**Downstream implementation:**
- **Plan 12** (restoration topology): adds the 2 nodes per mechanics §4 shape (on_enter: load WT PDB → applyEdit disease allele → op="align" WT reveal per 5.3), updates counts 55→57 in `tests/test_glucose_reachability.py` + 05.1-DESIGN §5/§6 + regenerates the graph diagram — SAME plan (OQ-K rule: count updates never deferred).
- **Plan 14** binds `branch_node` = the restored nodes for PFK + aconitase in edits.json.
- **Plans 08/13** author restored-node text / verify on_enter intact (structure owned by 12).
- **Plan 16** re-pins the final 57/21 invariants.

### 2. PLACEHOLDER_PHASE8 (fa.stub / alc.stub)

**Outcome:** leave untouched, document as Phase 8 stubs.

**Rationale:** The fatty-acid and alcoholic stubs are Phase 8 placeholders returning to intro.select; registering minimal claims or re-pointing them would spend approval budget on content that Phase 8 will replace anyway. They are not science claims until claimed.

**Downstream implementation:** **Plan 07** (intro content) annotates the stubs only — PLACEHOLDER_PHASE8 claim_ids stay; on_enter untouched. **Plan 16**'s PLACEHOLDER sweep expects exactly these documented residuals (0 remaining EXCEPT fa.stub/alc.stub). Phase 8 replaces them.

### 3. DC-B — `host_o2_low` setter

**Outcome:** cond-neutralize both pyr.branch choices + honest O2-framing labels; TestPyrBranchRuntimeEligibility updates owed in plan 06.

**Rationale:** The anaerobic subtree is structurally reachable (BFS ignores cond) but runtime-HIDDEN forever because nothing sets `host_o2_low`. Cond-neutralizing both choices makes both branches runtime-eligible without any flag-setter machinery, and honest O2-framing labels carry the teaching beat. Rejected alternatives, recorded so no plan revisits them: effects-setter choice on an earlier node (makes the host's condition a PLAYER choice — framing concern); new weighted RNG host-condition node (the weight value is a high-stakes per-claim approval not sanctioned by this checkpoint); `initial_flags` in manifest/GameState (ENGINE SURGERY — rejected outright by this phase's data/content-only constraint).

**Downstream implementation:** **Plan 06** (pyruvate-branch content) implements the cond-neutralization + labels and updates `TestPyrBranchRuntimeEligibility` in the SAME plan (aerobic-eligible-when-unset / anaerobic-hidden-when-unset / flip-when-set semantics change to always-eligible). NO topology change (55/21 pinned until plan 12). **OQ-K ack (outcome 7) formalizes this test ownership.**

### 4. M5 — Known-wrong (1b) edits.json entries

**Outcome:** NO known-wrong 1b entries in Phase 7.

**Rationale:** `edit_dialog._label_for_known()` labels ANY known entry "the correct fix" — a deliberately-known-wrong entry would be mislabeled to the player. Avoiding 1b entries means no data-driven label hook (a UI change) is needed; the wrong options remain the Phase 6 hardcoded plausible-wrong set, all collision-safe for the planned signatures.

**Downstream implementation:** **Plan 14** (edits.json authoring) — 13 enzyme buckets get known-CORRECT reverse-mutation signatures only; no known-wrong entries; bad_ending_pool untouched. The `edit:prompt` "1b binding is Phase 7 edits.json content" note from 05.1-DESIGN is hereby resolved as "not bound".

### 5. M1 — `-cand` claim-id policy on approval

**Outcome:** KEEP -cand claim_ids when approving, flip approval_status only; tests pin ids verbatim.

**Rationale:** Renaming `-cand` ids to bare ids on approval would break every pinned assertion across the test suite and the skeleton (test churn, drift risk). The id string is a stable key; `approval_status` is the state field.

**Downstream implementation:** **Plan 05** (registry landing) flips `approval_status` on approved `-cand` ids and keeps the ids verbatim. **Plan 16**'s all-node claim-ids-approved test pins ids verbatim. Consistency note: approval batch C (07-04) already recorded its ETC/DIS claims "APPROVED keeping -cand ids" under this policy.

### 6. OQ-C — 20-AA cast structure

**Outcome:** defer real cast structure to Phase 9; keep bundled _smoke.pdb through Phase 7.

**Rationale:** No sourced 20-AA cast structure exists (`_smoke.pdb` is a bundled test fixture); sourcing one now (peptide PDB or 20× PubChem fetches) adds approval + asset weight to a phase that already carries 19 plans. The bundled fixture is not a science claim until claimed.

**Downstream implementation:** **Plan 07** keeps `_smoke.pdb` on_enter UNTOUCHED (start-node shape tests stay green). **Plan 02** already recorded the knock-on: INTRO-CAST-20AA-01 contingent claim DEFERRED ("real 20-AA cast deferred to Phase 9 per 07-01 decision #6"). **Phase 9** (cast phase) sources the real structure.

### 7. OQ-K — Test-impact acknowledgment

**Outcome:** yes — plan 06 owns TestPyrBranchRuntimeEligibility updates and plan 12 owns 55→57 count updates in tests/test_glucose_reachability.py.

**Rationale:** Explicit acknowledgment that the two adopted structural/mechanics changes carry named test obligations, assigned to the implementing plans so they cannot be missed (the research flagged this as "easy to miss").

**Downstream implementation:** Plan 06 + plan 12 as stated. Cross-reference for completeness (NOT a decision of this checkpoint): the OGDH promotion invariant (edit-allowed 14→15 test update) is decided by **approval batch 03's** D5 checkpoint, not here — if D5 is approved, **plan 13** owns that count update in the SAME plan (per roster), and **plan 16** re-pins the final edit-allowed count per the D5 outcome.

### Constraint check (plan must-have truth)

**No engine/molops surgery is sanctioned by any recorded outcome.** All 7 outcomes are data/content-only: story JSON (plans 06/07/12/13/14), registry JSON (plan 05), cast deferral (Phase 9), test-ownership bookkeeping. The explicitly rejected `initial_flags` option would have touched GameState/engine — it is recorded as REJECTED above.

## Task Commits

Checkpoint-only plan (single `checkpoint:decision` task, `autonomous: false`):

1. **Task 1: Record structural + mechanics decision outcomes** — deliverable IS this SUMMARY; committed in the plan-metadata commit (no separate task commit; `files_modified: []` per plan frontmatter — no code/data files).

## Files Created/Modified

- `.planning/phases/07-content-expansion-i-glucose/07-01-SUMMARY.md` — the decision ledger (this file)

## Deviations from Plan

None — plan executed exactly as written. (The plan is a single decision checkpoint; the human accepted all 7 research recommendations verbatim.)

## Issues Encountered

None. (Concurrent-session note: sibling wave-1 plans 07-02 and 07-04 completed in parallel during this checkpoint's human-decision window; their STATE.md updates were present in the working tree when this plan updated STATE.md. Per the 05.1-14/06-05/06-03 precedent, history was not rewritten; the docs(07-01) commit stages STATE.md as merged — the swept-in 07-04 lines are that agent's tested+complete bookkeeping, attribution noted here.)

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Unblocked:** approval batch consumption (**plan 05** registry landing — M1 policy now binding) and the whole content Wave 3-4 chain (plans 06/07/08/09/10/11/12) plus edits.json (14), cast (15), cross-cutting pass (16).
- **Binding constraints for every later plan:** implement the recorded outcomes above; do NOT re-decide; no engine/molops surgery; only sanctioned topology change = plan 12's +2 restored nodes (55→57).
- **Watch items:** plan 06 must not forget the TestPyrBranchRuntimeEligibility rewrite (outcome 7 ack); plan 12 must update counts in the SAME plan; plan 16 is the backstop that catches any missed count update.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-01*
