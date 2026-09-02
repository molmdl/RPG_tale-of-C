---
phase: 07-content-expansion-i-glucose
plan: 06
subsystem: story-content
tags: [pyruvate-branch, fermentation, pdh, cond-neutralization, host_o2_low, two-layer-text, citation-gate, yeast-counterfactual, o2-branch]

# Dependency graph
requires:
  - phase: 07-content-expansion-i-glucose (plan 01)
    provides: "DC-B decision: REMOVE both pyr.branch conds + honest O2-framing labels; OQ-K: this plan owns the TestPyrBranchRuntimeEligibility rewrite in the SAME plan"
  - phase: 07-content-expansion-i-glucose (plan 02)
    provides: "Batch-A verdicts: 22 claims approved (AN-G-02 softened carbon-retention wording); DC-5 = option (a) keep 6CFO, 6CER dormant; OQ1 = yeast-counterfactual; OQ-E = 5W8J + name the inhibitor"
  - phase: 07-content-expansion-i-glucose (plan 05)
    provides: "Landed registry (data/citations.json) — every claim id this plan cites resolves APPROVED"
  - phase: 07-content-expansion-i-glucose (plan 12)
    provides: "57-node / 21-ending graph (the topology this plan must hold at exactly 7 pyruvate nodes)"
provides:
  - "data/story_glucose/pyruvate_branch.json authored: 7/7 nodes two-layer text grounded only in approved claims; claim swap map applied (pyr.branch→AN-G-01+AN-G-05; pyr.pdh→PYR-PDH-01 keeping both -cand ids verbatim; anaer.entry→AN-G-04; anaer.ldh→AN-G-02+CAST-LDH-PDB-01; anaer.lactic→AN-G-02; anaer.ethanolic→AN-G-03+AN-G-05; anaer.crisis→AN-G-04+AN-ETC-02)"
  - "The story's first real fork made honest AND always playable: both pyr.branch choices cond-free with O2-framing labels (aerobic = 'the tissue is oxygen-rich'; anaerobic = 'the air runs out'); O2 taught as a real tissue-level condition (host = mammal, 07-04 invariant)"
  - "anaer.ethanolic yeast-counterfactual teaching moment (07-02 OQ1 decision b): dramatic = the alternate-host vision; teaching = real yeast chemistry + 'your mammalian host does not run this road'; HOST-TENSION FLAG deleted"
  - "tests/test_glucose_reachability.py TestPyrBranchRuntimeEligibility rewritten to always-eligible semantics (the OQ-K obligation, discharged in the SAME plan): cond-neutral pin + both-eligible-when-unset + both-eligible-when-flag-set + upgraded not-stuck (==2)"
affects: [07-08 (glycolysis content — shares AN-G-01 at gly.pyruvate; the branch labels must stay consistent), 07-13 (TCA — pyr.pdh feeds tca.entry), 07-14 (edits.json pyr.pdh signature: resi 138 → VAL on 6CFO), 07-16 (final sweep — this file has zero placeholders), 07-17/07-18 (human-verify the branch + PDH cast)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cond-neutralized branch pattern: both choices cond-free (cond=None → interpreter._cond returns True); the physiological framing lives in labels + teaching text, not in hidden flag state — identified in tests by frozen branch tags, never by cond shape"
    - "Counterfactual-ending pattern: a real-chemistry ending framed as 'another host's road' (yeast) with the honest not-this-host clause, converting a host-tension into pedagogy with zero topology change"
    - "Hero-neutral carbon wording at a fate node: 'one carbon leaves as CO2; if that shadow is you... if not, you ride onward' — never asserts which glucose carbon the hero is (OQ-H discipline)"

key-files:
  created:
    - ".planning/phases/07-content-expansion-i-glucose/07-06-SUMMARY.md (this file)"
  modified:
    - "data/story_glucose/pyruvate_branch.json (7/7 nodes two-layer text + claim swaps + cond-neutralized branch; on_enter/tags/tiers/choice topology byte-identical vs HEAD)"
    - "tests/test_glucose_reachability.py (TestPyrBranchRuntimeEligibility rewritten to always-eligible semantics; other classes untouched)"

key-decisions:
  - "Implemented 07-01 DC-B verbatim: both pyr.branch cond keys REMOVED; labels reworded to honest O2 framing; O2 taught as a real tissue condition (working muscle outpacing its O2 supply), never a game whim — honors the 07-04 host=mammal invariant"
  - "Implemented 07-02 DC-5 option (a): pyr.pdh on_enter kept byte-identical [hide_all, load pdb:6CFO object pdh]; 6CER stays approved-but-DORMANT (no mutant load added); teaching states 'the game edits the healthy structure in place'"
  - "Implemented 07-02 OQ1 option (b): anaer.ethanolic = yeast-counterfactual teaching moment, ZERO topology change; the HOST-TENSION FLAG line DELETED as mandated once the framing landed"
  - "Implemented 07-02 OQ-E Decision 6: 5W8J kept as the LDH cast; teaching names the bound research inhibitor (compound 29) 'in the very pocket lactate would occupy'"
  - "AN-G-02 taught ONLY in the approved softened wording: 'its carbon is retained in lactate (no decarboxylation step occurs)' — the rejected 'no CO2 is released' clause appears nowhere"
  - "pyr.pdh player-facing numbering = PDB/mature resi 138 with the V167M literature alias taught (29-residue transit peptide bridge), per 07-02 verdict #3/Decision 4"
  - "Hero-neutral carbon wording at pyr.pdh (research OQ-H): the CO2 shed is pyruvate's carboxyl carbon; the story does not claim which glucose carbon the hero rides"
  - "Claim swap map followed EXACTLY: anaer.entry cites AN-G-04 only — AN-ANAER-DEF-01 (approved, optional) left UNCONSUMED; zero placeholders remain in the file; topology untouched (7 nodes, zero added/removed)"

patterns-established:
  - "Always-eligible branch semantics pinned in tests: cond is None on both choices + eligibility independent of flag state (flag is vestigial) — a regression re-adding a cond fails test_pyr_branch_choices_are_cond_neutral loudly"

# Metrics
duration: 9 min
completed: 2026-09-03
---

# Phase 7 Plan 06: Pyruvate-Branch Content Summary

**All 7 pyruvate-branch nodes two-layer authored on approved claims; the O2 fork cond-neutralized with honest tissue-condition labels (07-01 DC-B); PDH taught on the 6CFO cast with the TPP/Mg²⁺ cradle and hero-neutral carbon wording; ethanolic ending reframed as the yeast counterfactual; TestPyrBranchRuntimeEligibility rewritten to always-eligible semantics in the same plan (OQ-K discharged).**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-02T19:52:45Z
- **Completed:** 2026-09-02T20:01:34Z
- **Tasks:** 2 of 2
- **Files modified:** 2 (data/story_glucose/pyruvate_branch.json; tests/test_glucose_reachability.py)

## Accomplishments

- **Task 1 (commit 295c3fd):** authored `data/story_glucose/pyruvate_branch.json` — 7/7 nodes carry non-empty `text_dramatic` + `text_teaching` grounded ONLY in approved registry claims; the full claim swap map applied with both `-cand` ids on pyr.pdh kept verbatim (pinned tests); zero placeholders remain in the file (gate residual for this file = 0; 13 claim refs across 7 nodes all approved).
- **The story's first real fork is now honest and always playable:** both `pyr.branch` choices lost their `cond` keys (nothing ever set `host_o2_low`, so the anaerobic subtree was structurally reachable but runtime-hidden forever); labels carry the O2 framing ("Proceed aerobically — the tissue is oxygen-rich" / "The air runs out — ferment (anaerobic)"); teaching explains O2 as a real, tissue-level physiological condition (hypoxic working muscle ferments — AN-G-05) and that the player sets the host's condition, sprint-style. The anaerobic choice's `effects: {"set": {"anaerobic": true}}` and all gotos/tags preserved.
- **pyr.pdh (the PDH gate):** PYR-PDH-01 teaching (oxidative decarboxylation → acetyl-CoA + CO2 + NADH, committed TCA entry; "the third carbon from pyruvate is released as CO2"); the 6CFO cast beat (2.70 Å, covalent TDP-acetyl-phosphinate analog + Mg²⁺ — "the cofactor cradle you see is thiamine pyrophosphate", the vitamin-B1-derived cofactor); the DIS-PDHA1-01-cand disease frame (V138M PDB/mature numbering + V167M UniProt-alias bridge via the 29-residue transit peptide; Pathogenic/Likely pathogenic; "disrupts magnesium binding" — broken at the Mg²⁺ cradle visible on screen); hero-neutral carbon wording (OQ-H) + the enzyme-health ≠ carbon-fate anti-confusion note (05.3 convention); on_enter byte-identical (6CFO load kept per DC-5 option a; 6CER untouched/dormant).
- **anaer.ldh:** AN-G-02 in the APPROVED SOFTENED wording only ("its carbon is retained in lactate (no decarboxylation step occurs)"); 5W8J cast named (1.55 Å human LDHA) with the bound research inhibitor (compound 29) named per OQ-E Decision 6.
- **anaer.ethanolic (Normal ending):** the 07-02 OQ1 option-(b) yeast counterfactual — dramatic gives the alternate-host vision ("in a yeast cell, this is the road you would take"); teaching states the real yeast chemistry verbatim-grounded on AN-G-03 (PDC releases CO2; ADH → ethanol, NAD+ regenerated) plus the honest clause "your mammalian host does not run this road — it lacks pyruvate decarboxylase" (AN-G-03 "(not mammals)" scoping + AN-G-05 host-distribution fact); the HOST-TENSION FLAG line DELETED as mandated.
- **anaer.crisis (Bad ending):** two-part teaching exactly per research — NAD+-supply fragility (AN-G-04: ETC-or-fermentation replenishment, else glycolysis stops) + yield collapse (AN-ETC-02: ETC stalls with no terminal acceptor, oxidative phosphorylation cannot produce ATP, PMF collapses, fermentation yields far less ATP); no ROS, no numeric P/O yields, no electrons-leak wording (07-04 invariants).
- **Task 2 (commit dbe51b2):** rewrote all 5 `TestPyrBranchRuntimeEligibility` tests to the always-eligible semantics — NEW `test_pyr_branch_choices_are_cond_neutral` (pins `cond is None` on both; a regression re-adding a cond fails loudly), `test_pyr_branch_both_choices_eligible_when_flags_unset` (both `_cond` True + gotos == {pyr.pdh, anaer.entry}), `test_pyr_branch_both_choices_eligible_when_host_o2_low_set_true` (flag is vestigial — eligibility independent of state), `test_pyr_branch_both_choices_not_stuck` upgraded (≥1 → ==2), and `test_no_broken_dict_attribute_conds_remain` KEPT (trivially green now; guards any future cond story-wide). Choice identification switched from cond-shape to the frozen `branch:aerobic`/`branch:anaerobic` tags. No other test class touched.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author two-layer text + claim swaps + branch treatment** — `295c3fd` (feat)
2. **Task 2: Update TestPyrBranchRuntimeEligibility to always-eligible semantics** — `dbe51b2` (test)

**Plan metadata:** `docs(07-06): complete pyruvate-branch content plan` (this SUMMARY; STATE.md NOT touched per the wave-4 coordination rule — the orchestrator consolidates).

## Files Created/Modified

- `data/story_glucose/pyruvate_branch.json` — all 7 nodes two-layer authored; claim swap map applied; pyr.branch cond-free with O2-framing labels; HOST-TENSION FLAG deleted; on_enter/tags/tiers/choice counts byte-identical vs HEAD (machine-verified)
- `tests/test_glucose_reachability.py` — TestPyrBranchRuntimeEligibility rewritten to always-eligible semantics (5 tests; class docstring records the 06-05 → 07-01 DC-B → 07-06 history); all other classes untouched

## Decisions Made

All decisions were implementations of previously recorded ledger outcomes (no new decisions):

- **07-01 DC-B (verbatim implementation):** both conds removed; honest O2-framing labels; teaching frames O2 as a real tissue condition. Alternatives stay rejected (effects-setter choice, RNG host-condition node, initial_flags engine surgery).
- **07-02 DC-5 option (a):** 6CFO load kept as-is; 6CER approved-but-dormant (no load added — verified in the byte-identical on_enter check).
- **07-02 OQ1 option (b):** yeast-counterfactual framing; zero topology change; flag line deleted.
- **07-02 OQ-E Decision 6:** 5W8J kept; inhibitor named in teaching.
- **Claim-map fidelity:** anaer.entry cites AN-G-04 only — AN-ANAER-DEF-01 (approved as optional in batch A, explicitly "consumable by plan 06" in the research) was left UNCONSUMED because the plan's binding swap map says `anaer.entry→AN-G-04`; the node's teaching text stays strictly within AN-G-04's verbatim anchors (NAD+ recycling, ETC-or-fermentation replenishment, yield ≪ TCA+ETC). Recorded so plan 16's sweep and future authors know the optional claim remains available.
- **Text-grounding discipline:** every scientific sentence traces to the claim_texts/registry notes of the claims cited on that node; tier semantics ("Good = carbon retained", "Bad = host death") are labeled as project framing, not science claims; the ethanolic "normal" tier is explained via the carbon-fate (released as CO2).

## Deviations from Plan

None — plan executed exactly as written.

Note (not a deviation): between the Task 1 and Task 2 commits, the 4 old cond-shape tests necessarily failed (they asserted the cond-gated semantics this plan replaces); the plan itself assigns the rewrite to Task 2 "in the SAME plan" and the final suite is fully green (325/325). The 5th test (`test_no_broken_dict_attribute_conds_remain`) passed trivially after Task 1, exactly as the plan predicted.

## Issues Encountered

None. Concurrent-session note: `rpg/data/edits.json` was dirty in the working tree from a parallel wave agent (plan-14 territory); per the 07-10/07-07 scope-discipline precedent it was NOT staged — both task commits contain only this plan's files.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Gate state:** full-story citation gate residual dropped 23 → 16 MISSING (the 7 pyruvate-branch placeholder references are gone); 0 UNAPPROVED. Remaining residual = other in-flight plans' documented buckets: tca 9 (plan 13) + gly 5 (plan 08) + fa.stub/alc.stub PLACEHOLDER_PHASE8 2 (documented Phase-8 stubs, kept by design per 07-01 decision #2).
- **Suite state:** 325/325 unit tests OK; 21/21 reachability-file tests OK; graph holds at 57 nodes / 21 endings / 14 edit-allowed with pyruvate_branch.json at exactly 7 nodes (topology frozen — zero added/removed by this plan).
- **For plan 08 (glycolysis content):** `gly.pyruvate` shares AN-G-01 — keep its crossroads teaching consistent with pyr.branch's O2-as-tissue-condition framing and the two new choice labels.
- **For plan 14 (edits.json):** the pyr.pdh signature stays per 07-02 Decision 4(a): applyEdit on 6CFO at `resi 138` → `new_res VAL` (player-facing 138; V167M alias already taught on the node).
- **For plans 17/18 (human verify):** the branch labels, the PDH Mg²⁺-cradle beat on 6CFO, the 5W8J inhibitor note, and the yeast-counterfactual ending are the four beats to eyeball in a real Windows PyMOL session.
- **Blockers:** none.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-03*
