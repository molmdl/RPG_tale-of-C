---
phase: 07-content-expansion-i-glucose
plan: 09
subsystem: content
tags: [etc, oxidative-phosphorylation, atp-synthase, soul-jump, anti-confusion, proton-leak, ucp1, uncoupling, pdb-loads, citation-gate, headless-smoke]

# Dependency graph
requires:
  - phase: 07-04 (approval batch C ledger)
    provides: the 9 locked ETC framing decisions (OQ2 oq2-uncoupling, CYC1=L215F, COX4I1 dual numbering, no-numeric-yields, no-ROS, complex_ii/iii promotion, Template-3 restore shortcut, 1E79 DCCD beat, anti-confusion binding)
  - phase: 07-05 (registry landing)
    provides: all ETC claim ids APPROVED in data/citations.json (ATP-SOUL-03/07/08/09, ETC-CI/CII/CIII/CIV/Q/CYTC/PMF/UCP/CHEM-01, DIS-NDUFS8/SDHA/CYC1/COX4I1 -cand)
  - phase: 05.4 (scene-template convention)
    provides: §3.6 mandatory anti-confusion teaching template + soul-transfer semantics
provides:
  - "Authored data/story_glucose/etc_atp.json — all 7 ETC nodes with two-layer text grounded ONLY in approved claim ids; zero numeric P/O yields; zero ROS claims"
  - "end.true explicit-soul finale (replaces bare 'you are ATP') + the mandatory 5.4 §3.6 anti-confusion teaching template + carbon-fate cross-ref + RNG-gate link"
  - "complex_ii/iii promoted to PDB-bearing (1ZOY/1BGY on_enter loads, appended after hide_all; topology untouched) per batch-C Decision 6b"
  - "etc.entry 'let go' choice relabeled to the proton-leak/uncoupling framing (OQ2 oq2-uncoupling, Decision 5)"
  - "OQ#4 restore-handle semantics EMPIRICALLY VERIFIED headlessly (07-04 Decision 6a mandate): Template-3 [edit, restore] self-undoes; restore-ONLY returns the WT — FLAGGED for plans 14/17"
affects: [07-12 (restored-node topology), 07-13 (TCA content), 07-14 (edits.json ETC signatures — MUST use restore-ONLY branch routing), 07-16 (cross-cutting tests), 07-17 (template-fill pass), 07-18 (human verify), phase 11 (docs)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Anti-confusion text contract: carbon-fate (CO2, shed) and electron-soul (ETC → ATP) framings kept separate in every ETC node's teaching layer"
    - "Disease-frame authoring pattern: discovery-paper hook + ClinVar classification honesty + human↔PDB numbering bridge (transit-peptide arithmetic) + geometry caveat + species honesty (bovine/porcine cast, human genetics)"
    - "Headless empirical-semantics smoke pattern (SMOKE_RESULT sentinel + OQ4_VERDICT analytical lines) for convention-vs-engine questions"

key-files:
  created:
    - tools/etc_restore_handle_smoke.py
  modified:
    - data/story_glucose/etc_atp.json
    - .planning/STATE.md

key-decisions:
  - "No plan-body deviations on content: loads added ONLY for complex_ii (1ZOY) + complex_iii (1BGY) per the plan's explicit instruction; complex_i stays narrative-only (5LDW taught in TEXT with the cryo-EM note, not loaded — no batch-C promotion covered it) and atp_synthase keeps [hide_all] (1E79 landed as the DCCD teaching beat, not a load)"
  - "ATP-SOUL-01/02 cross-ref is NARRATIVE-ONLY in end.true teaching (they are NOT in the registry per 07-05 — referencing them would fail the gate)"
  - "OQ#4 verdict recorded as a FLAG, not a fix: engine surgery is out of Phase 7 scope (plan-index global constraint); plans 14/17 must author ETC restoration branch nodes in the restore-ONLY form"

patterns-established:
  - "ETC teaching-text template: chemistry (approved claim wording) → disease frame → numbering bridge → geometry caveat → species honesty → Template-3 restore note"
  - "Empirical OQ verdict smoke: mechanical SMOKE_RESULT + analytical OQ*_VERDICT lines, so a convention finding never masquerades as a smoke crash"

# Metrics
duration: ~6h 31m wall-clock (2026-09-01T19:38Z → 2026-09-02T02:08Z; includes a long idle/queue gap — active execution well under 2h; parallel wave-3 plans 07-07/07-10/07-11 landed mid-session with zero file conflicts)
completed: 2026-09-02
---

# Phase 7 Plan 09: ETC Content — All 7 Nodes + Soul-Jump Finale Summary

**All 7 ETC nodes authored with two-layer text grounded exclusively in approved claims (zero numeric P/O yields, zero ROS, anti-confusion binding honored), complex_ii/iii promoted to real 1ZOY/1BGY loads, the end.true explicit-soul finale landed — plus the batch-C-mandated OQ#4 headless check, which EMPIRICALLY FELL: Template-3's [edit, restore] order self-undoes (restore returns the disease state); only the restore-ONLY form retrieves the WT (flagged for plans 14/17).**

## Performance

- **Duration:** ~6h 31m wall-clock (long idle/queue gap included; active execution well under 2h)
- **Started:** 2026-09-01T19:38:18Z
- **Completed:** 2026-09-02T02:08Z
- **Tasks:** 1/1 plan task + 1 ledger-mandated verification artifact
- **Files modified:** 2 (+1 created)

## Accomplishments

- **All 7 ETC nodes authored** (etc.entry, complex_i/ii/iii/iv, atp_synthase, end.true): dramatic + teaching layers non-empty, every scientific assertion traceable to an APPROVED claim id — zero numeric P/O yields (Decision 8), zero ROS claims, proton-leak text says PROTONS never "electrons leak" (Decision 7).
- **Claim swaps per the plan map** — etc.entry→ATP-SOUL-03+ETC-CI-01+ETC-UCP-01; complex_ii→ETC-CII-01+ETC-Q-01(+DIS-SDHA-01-cand); complex_iii→ETC-CIII-01+ETC-CYTC-01(+DIS-CYC1-01-cand); complex_iv→ETC-CIV-01+ETC-PMF-01(+DIS-COX4I1-01-cand); atp_synthase→ATP-SOUL-07+ETC-CHEM-01; end.true→ATP-SOUL-08+ATP-SOUL-09+ETC-CHEM-01. **etc.complex_i claim_ids remain EXACTLY ['DIS-NDUFS8-01-cand']** — the pinned equality assertion (tests/test_glucose_reachability.py:345-351) is green.
- **Batch-C Decision 6b promotion implemented**: complex_ii on_enter gained `load pdb:1ZOY (object complex_ii)`, complex_iii gained `load pdb:1BGY (object complex_iii)` — appended after hide_all; node ids/choices/topology untouched (55/21 invariants green).
- **OQ2 relabel (Decision 5)**: etc.entry's "Let go" choice is now "Let go — let the pressure bleed away as warmth (the proton-leak exit)"; teaching gives the real uncoupling semantics (protons slip back bypassing ATP synthase; electron transport and CO2 production continue — ETC-UCP-01).
- **end.true finale**: dramatic = the explicit-soul phrasing ("YOU are the spark within the ATP — your electrons now power the cell; your carbon body was shed as CO2"); teaching = the mandatory 5.4 §3.6 anti-confusion template + the carbon-fate cross-ref (all six carbons exit as CO2; none became ATP) + the ATP-SOUL-09 RNG-gate link (the 50/50 citrate-shuffle prochiral gate).
- **Disease frames + teaching apparatus per node**: NDUFS8 R102H (Leigh; Loeffen 1998 "first nuclear-encoded Complex I mutation in a Leigh patient"; ClinVar conflicting-classifications honesty) / SDHA R554W (Leigh; Bourgeron 1995 first nuclear-encoded respiratory-chain mutation; ClinVar Likely pathogenic) / CYC1 L215F (MC3DN6; Gaignard 2013; ClinVar Pathogenic 2025 criteria-provided; W96C documented as the discarded first draft) / COX4I1 P152T (MC4DN16 "resembling Leigh syndrome"; Pillai 2019; dual numbering P152T↔chain-D resi 130 with the 152−22=130 bridge); numbering bridges on all four (68/512/131/130 via transit-peptide arithmetic); the geometry caveat (alter changes identity, not side-chain packing) on every complex; species honesty (bovine/porcine cast, human genetics); 5LDW cryo-EM note; 1E79 DCCD "photography freeze" beat; Template-3 restoration wording (no mutant PDB exists — the game edits the healthy structure in place).

## Task Commits

Each task was committed atomically:

1. **Task 1: Author ETC text + claim swaps + PDB loads + finale** - `459a196` (feat)
2. **OQ#4 restore-handle headless verification** (07-04 Decision 6a mandate; ledger-assigned to plan 09, absent from the plan body) - `b88ae8e` (test)

**Plan metadata:** (this SUMMARY + STATE.md — the docs commit follows)

## Files Created/Modified

- `data/story_glucose/etc_atp.json` — all 7 ETC nodes: two-layer text, approved claim ids, 1ZOY/1BGY loads, OQ2 relabel, explicit-soul end.true (zero placeholders remain)
- `tools/etc_restore_handle_smoke.py` — OQ#4 empirical-semantics smoke (SMOKE_RESULT + OQ4_VERDICT lines; headless-verified SMOKE_RESULT: PASS)

## Verification (all green)

- `python3.6 -m unittest tests.test_glucose_reachability -v` → **Ran 20 tests — OK** (complex_i PIN + topology + all structural invariants)
- `python3.6 -m unittest discover -s tests` → **Ran 324 tests — OK** (zero regression)
- `python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json` → exit 1 with **23 MISSING / 0 UNAPPROVED — ZERO residual from etc_atp.json** (all 23 are other files' pending placeholder buckets: tca 9 [plan 13, wave 5], gly 5 + pyr 2 [plans 08/06, wave 4], anaer 5 [plan 06], fa.stub/alc.stub 2 [documented Phase-8 stubs])
- `grep -c "ATP per\|2.5 ATP\|three ATP" data/story_glucose/etc_atp.json` → **0**; `grep -c "electrons leak\|electron leak"` → **0**; `grep PLACEHOLDER` → **0**
- Headless smoke `tools/etc_restore_handle_smoke.py` → **SMOKE_RESULT: PASS** (real Windows PyMOL 2.5.0 cmd; 9/9 mechanical checks)

## Decisions Made

- **Loads scoped exactly to the batch-C promotion (Decision 6b): 1ZOY + 1BGY only.** The roster line's "PDB loads per 04 (1BGY/1OCC/1E79…)" is satisfied by the 1BGY load + the pre-existing 1OCC load + the 1E79 DCCD teaching beat — no 5LDW load on complex_i (it was never promoted) and no 1E79 load on atp_synthase (not in Decision 6b's scope; plan 17 owns template-fill conformance if the human wants them displayed).
- **ATP-SOUL-01/02 omitted from end.true claim_ids** — 07-05 did NOT land them (deferred/cross-ref per ledgers), so referencing them would fail the gate; the carbon-fate cross-ref is carried narratively and backed by ATP-SOUL-08's approved claim_text ("the carbon body was shed as CO2; the carbon never becomes ATP").
- **MC3DN6 lactic-acidosis episodes included in the CYC1 frame** (research §7's explicit text need — "matches the host-in-crisis narrative"), kept brief and tied to the approved DIS-CYC1-01-cand disease frame.
- **No numeric-yield hedging numbers quoted anywhere**; the deliberate absence is stated once (atp_synthase teaching: ratios are approximate, condition-dependent, textbooks disagree — per Decision 8's recorded rationale).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] cmd.iterate namespace gotcha in the OQ#4 smoke**

- **Found during:** the OQ#4 headless verification (first run)
- **Issue:** `cmd.iterate(..., "stored.list.append(resn)")` without the `space=` kwarg → `AttributeError: 'Scratch_Storage' object has no attribute 'list'` (the expression namespace cannot see the caller's local)
- **Fix:** pass `space={"stored": stored}` — mirrors the production pattern at `rpg/pymol_layer/edit_ops.py:268-273`
- **Files modified:** tools/etc_restore_handle_smoke.py
- **Verification:** re-run headlessly → all 9 mechanical checks PASS
- **Committed in:** b88ae8e

**2. [Ledger-mandated addition — verification artifact, not plan work] tools/etc_restore_handle_smoke.py**

- **Found during:** pre-execution context assembly
- **Issue:** the 07-04 batch-C ledger (Decision 6a) and research OQ#4 assign "restore-handle semantics verified headlessly in plan 09" to this plan, but the plan body's single task does not include it
- **Fix:** wrote + ran the headless empirical smoke (no product code touched; files_modified extended by this one verification tool)
- **Result:** OQ4_VERDICT: FAIL-TEMPLATE3 (see Issues Encountered) — recorded as a FLAG, not fixed (engine surgery out of Phase 7 scope)
- **Committed in:** b88ae8e

---

**Total deviations:** 2 (1 blocking auto-fix inside the added artifact; 1 ledger-mandated verification artifact)
**Impact on plan:** The authored content (the plan's actual deliverable) executed exactly as written — zero content deviations. The added smoke discharges a batch-C obligation and surfaced a load-bearing finding for plans 14/17.

## Issues Encountered

- **OQ#4 verdict: FAIL-TEMPLATE3 (empirical, real PyMOL cmd).** On a restoration branch node whose on_enter fires the reverse-mutation `edit` BEFORE `restore` (05.3 Template 3's literal sequence), the restore retrieves the player-edit's OWN backup — the DISEASE state — so the reveal would undo the restoration. Root cause (code-confirmed, empirically verified): `EditOps.apply_edit` registers `_handles[object_name]` on every call (edit_ops.py:148) so the second apply overwrites the pre-edit WT handle, AND `take_backup` deletes + recreates the `_bak_<obj>` object (edit_ops.py:199-203) so the WT backup object is destroyed. The restore-ONLY form (05.3 §2 option (ii)) works correctly: restore after the pre-edit disease application returns the WT. **FLAG for plans 14/17:** author ETC restoration branch nodes (and any restored-node on_enter) in the restore-ONLY form, or order `restore` BEFORE any same-object `edit`. NOT fixed here — engine surgery is out of Phase 7 scope (plan-index global constraint).
- **Parallel wave-3 plans landed mid-session** (07-07 intro, 07-10 endings, 07-11 bad-pool): zero file conflicts (disjoint files; shared-manifest serialization honored); their landing is part of why the gate residual reads 23 (my file contributes none).
- **check_citations.py requires explicit `--story`/`--registry` args** — the plan's verification line omits them; ran with the standard paths (`data/story_glucose` + `data/citations.json`).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **07-14 (edits.json) MUST route ETC known edits to restore-ONLY branch nodes** (or restore-before-edit ordering) per the OQ4_VERDICT — the ETC quartet's known-edit routing was already "exploration-node routing" (no restored nodes exist for ETC; only PFK + aconitase get restored nodes in plan 12), which dodges the trap for ETC, but the flag also binds plan 12's restored-node on_enter shapes (PFK/aconitase use the 05.3 Template-1/2 explicit-WT form, unaffected) and any future ETC reveal wiring in plan 17.
- **07-17 (template-fill)** owns bringing complex_i/atp_synthase on_enter to Type-3/Type-2 conformance if the human wants 5LDW/1E79 displayed — the texts already teach both structures honestly (cryo-EM note; DCCD beat) without loads.
- **07-16 (cross-cutting)**: etc_atp.json now has zero PLACEHOLDER strings and two-layer non-empty text on all 7 nodes — the sweep will find nothing here.
- Citation-gate residual 23 MISSING = exactly the still-unauthored placeholder buckets (tca/gly/pyr/anaer + the 2 documented Phase-8 stubs); 0 UNAPPROVED.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-02*
