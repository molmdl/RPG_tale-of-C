---
phase: 07-content-expansion-i-glucose
plan: 08
subsystem: content
tags: [glycolysis, two-layer-text, claim-swaps, clinvar, likely-pathogenic, pfkm-g209d, pklr-r479h, tarui, cnsha2, restoration-arc, citation-gate, oq-g]

# Dependency graph
requires:
  - phase: 07-content-expansion-i-glucose (plan 02)
    provides: batch-A approval ledger — 22 approved claims with exact verdicts; DC-2/DC-3 PFKM text-only fallback; DC-4 PKLR 7FS3+2VGG + MANDATORY L-type-vs-RBC line
  - phase: 07-content-expansion-i-glucose (plan 12)
    provides: gly.pfk_restored node (structure + on_enter edit→load→align→show_as) — this plan verifies it intact and authors TEXT only
  - phase: 07-content-expansion-i-glucose (plan 05)
    provides: registry (data/citations.json) — all bound claim ids resolve approved
  - phase: 07-content-expansion-i-glucose (plan 14)
    provides: edits.json contract — gly.pyruvate_kinase known fix routes to gly.pyruvate (no PKLR branch node exists)
provides:
  - "data/story_glucose/glycolysis.json fully authored: 6/6 pathway nodes + gly.pfk_restored two-layer text, all grounded ONLY in approved batch-A claims"
  - "Approved claim swaps per the plan map: gly.start→GLY-INTRO-01; gly.g6p→GLY-HXK-01; gly.fbp_to_pyruvate→GLY-TRIOSE-01; gly.pyruvate→AN-G-01; gly.pfk keeps GLY-PFK-01+CAST-PFK-PDB-01+DIS-PFKM-01-cand verbatim"
  - "OQ-G net-ATP fix: '2 ATP invested + 2 ATP recovered + 2 NADH banked' at gly.fbp_to_pyruvate (both layers); the ambiguous skeleton phrase 'Net so far: 2 ATP, 2 NADH' removed"
  - "PFKM G209D disease frame at the exact approved evidence tier (ClinVar 'Likely pathogenic' VCV003375341 — never bare 'pathogenic') + honest bacterial-4PFK cast disclosure + text-only restoration-arc framing (DC-2/DC-3)"
  - "PKLR R479H disease frame at the strongest tier (ClinVar 'Pathogenic' VCV000001510, Amish, CNSHA2 MIM:266200, UniProt 'no conformational change') + 7FS3 cast + the MANDATORY L-type-vs-RBC teaching line (DC-4) + 2VGG taught in text"
affects: [07-13 (TCA content — same wave), 07-16 (final sweep — gly bucket now zero), 07-17/07-18 (human-verify the restoration reveal + cast beats), phase-8 (fa/alc stubs)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Restored-node text pattern: separate 'what is real' (mechanics) from 'what is framing' (the symbolic edit) in teaching text — disclosed, never hidden"
    - "Dormant-approved-mutant pattern (from plan 06): approved mutant PDB with no reveal home is consumed in TEXT with its claim bound, never force-loaded onto a healthy teaching node"
    - "Word-compliance scan as a text gate: bare-vs-pinned ClinVar classification checked by regex (?<!Likely )pathogenic"

key-files:
  created:
    - ".planning/phases/07-content-expansion-i-glucose/07-08-SUMMARY.md (this file)"
  modified:
    - "data/story_glucose/glycolysis.json (text + claim_ids ONLY; tags/on_enter/choices byte-identical vs HEAD — machine-verified)"

key-decisions:
  - "NO 2VGG on_enter load: the claim IS approved (07-02 verdict #7 CONSUMED per DC-4), but the frozen topology has NO PKLR restoration branch node (plan 12 added only gly.pfk_restored + tca.aconitase_restored; plan 14 routes the PKLR known fix → gly.pyruvate main-path node) and plan 06's DC-5 precedent keeps an approved-but-dormant mutant (6CER) unloaded — so 2VGG is consumed in teaching text with CAST-PKLR-MUTANT-PDB-01 bound; a static diseased-structure load on the healthy teaching node would fire on every visit with no reveal mechanics"
  - "gly.pfk_restored claim_ids [] -> [DIS-PFKM-01-cand]: teaching re-asserts the G209D pinned wording, so the claim must be bound for gate-grounding; sanctioned by the 07-12 DESIGN addendum ('claim_ids [] (text + claim swaps are plans 08/13)')"
  - "CAST-PKLR-MUTANT-PDB-01 added to gly.pyruvate_kinase beyond the plan's swap map: the teaching text teaches 2VGG, so its approved claim is bound (grounding completeness; claim verified approved in the live registry)"
  - "Node text uses 'committed step ... because of its large ΔG value' (S-GLY verbatim per research §2.2 note); 'rate-limiting' deliberately NOT used in node text even though the approved GLY-PFK-01 claim_text carries it"
  - "gly.start teaching avoids asserting 'cytosol' (S-GLY does not state the location verbatim — research §8 bullet); the word stays only in dramatic scene-setting, pre-existing skeleton framing"

patterns-established:
  - "Bare-pathogenic regex scan as the pre-commit wording gate for disease text"

# Metrics
duration: 8min
completed: 2026-09-03
---

# Phase 7 Plan 08: Glycolysis Content (Two-Layer Text + Claim Swaps + PFK Restoration-Arc Text) Summary

**All 6 glycolysis nodes + gly.pfk_restored authored on approved batch-A claims — PFKM G209D pinned to ClinVar "Likely pathogenic" with the bacterial-cast caveat disclosed, PKLR R479H at the strongest tier with the mandatory L-type-vs-RBC line, the OQ-G net-ATP phrasing fixed, and the plan-12 restoration on_enter verified byte-intact.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-03T03:25:56Z
- **Completed:** 2026-09-03T03:34:15Z
- **Tasks:** 1 of 1
- **Files modified:** 1 (data/story_glucose/glycolysis.json)

## Accomplishments

- 7/7 nodes in glycolysis.json now carry final two-layer text: gly.start, gly.g6p, gly.pfk, gly.pfk_restored, gly.fbp_to_pyruvate, gly.pyruvate_kinase, gly.pyruvate — every scientific assertion traces to an approved claim bound on the node (citation gate: 0 glycolysis MISSING, 0 UNAPPROVED anywhere).
- Claim swaps per the plan map applied; DIS-PFKM-01-cand and DIS-PKLR-01-cand kept verbatim (M1 policy; tests pin the ids).
- gly.pfk teaching: step 3 with the verbatim-grounded "committed step of glycolysis because of its large ΔG value" wording; the G209D disease frame at the exact approved tier — "abolishes PFK-1 activity in yeast-complementation assays (Raben 1995) and is classified Likely pathogenic in ClinVar (VCV003375341) for Glycogen Storage Disease VII / Tarui disease (MIM:232800)" — plus the honest cast note: 4PFK is the bacterial (Geobacillus stearothermophilus) enzyme whose own residue 209 is a histidine, so no on-structure mapping is asserted (OQ-B respected; DC-2/DC-3 text-only fallback).
- gly.pfk_restored: restoration-arc TEXT ONLY. Teaching separates the real mechanics (point mutation to GLY at resi 209, WT cast load 4PFK, cmd.super C-alpha alignment — all real PyMOL ops) from the disclosed framing ("a symbolic replay, not a structural correction of a real mutation"; no bacterial equivalent asserted). The plan-12 on_enter [edit → load → align → show_as] verified byte-identical vs HEAD and re-verified by the pinned test.
- gly.pyruvate_kinase: step 10 teaching; 7FS3 cast (1.66 Å, modulator + oxalate/Mg²⁺/K⁺, Nain-Perez 2023); the MANDATORY L-type-vs-RBC honesty line (7FS3 = liver L-type; the disease afflicts red blood cells, same PKLR gene); the R479H disease frame at the strongest tier (ClinVar "Pathogenic" VCV000001510, Amish, CNSHA2 MIM:266200, UniProt "no conformational change", Valentini 2002); 2VGG (the real R479H mutant structure) taught in text.
- gly.fbp_to_pyruvate: steps 4–9 verbatim chain (aldolase lyase → TPI → GAPDH/NADH → PGK/first substrate-level ATP → PGAM → enolase→PEP) with the OQ-G fix in BOTH layers: "2 ATP invested + 2 ATP recovered + 2 NADH banked — net ATP zero so far", explicitly deferring the second substrate-level ATP to pyruvate kinase. The skeleton's ambiguous "Net so far: 2 ATP, 2 NADH" is gone.
- gly.pyruvate: the crossroads arrival grounded on AN-G-01 (fate depends on oxygen: TCA via PDH aerobically / lactate or ethanol fermentation anaerobically), hand-off phrasing consistent with plan 06's pyr.branch labels.

## Task Commits

1. **Task 1: Author glycolysis text + swaps + restoration-arc text** — `de51bb0` (feat)

## Files Created/Modified

- `data/story_glucose/glycolysis.json` — text_dramatic + text_teaching + claim_ids on all 7 nodes; tags/on_enter/choices byte-identical vs HEAD (parsed-equality machine-verified before commit). Structural diff: 20 insertions / 20 deletions (text+claims only).

## Decisions Made

- **NO 2VGG on_enter load (documented interpretation of "add 2VGG load only if approved").** The claim IS approved (07-02 verdict #7, CONSUMED per DC-4), but the approved reveal home does not exist: plan 12's sanctioned topology added only gly.pfk_restored + tca.aconitase_restored (07-01 DC-A — the ONLY topology change of the phase), and plan 14's landed edits.json routes the gly.pyruvate_kinase known fix to `gly.pyruvate` (a main-path node whose on_enter fires on every normal visit). A static 2VGG load on the healthy teaching node would show the DISEASED structure on every pass with no reveal mechanics — not the approved restoration-arc pattern. Following the plan-06 DC-5 precedent (6CER approved-but-DORMANT, no load, text consumption), 2VGG is taught in text with CAST-PKLR-MUTANT-PDB-01 bound. A future phase that adds a PKLR reveal node can promote the load from this recorded approval without re-approval.
- **gly.pfk_restored claim_ids [] → [DIS-PFKM-01-cand].** The restoration teaching re-asserts the G209D pinned wording (the arc needs its "why"), so the claim is bound for gate-grounding. Sanctioned by the 07-12 DESIGN addendum: these nodes "carry claim_ids: [] (text + claim swaps are plans 08/13)".
- **CAST-PKLR-MUTANT-PDB-01 added to gly.pyruvate_kinase beyond the plan's literal swap map** (which listed GLY-PKM-01 + CAST-PKLR-PDB-01 + DIS-PKLR-01-cand): the teaching text teaches 2VGG, so its approved claim must be bound (grounding completeness — the same discipline plans 07/09/10/11 applied). Verified approved in the live registry before binding.
- **"rate-limiting" deliberately absent from node text.** The approved GLY-PFK-01 claim_text says "committed, rate-limiting", but the research hand-off (§2.2 note) grounds node text on the S-GLY verbatim "committed step ... because of its large ΔG value"; grep-verified 0 hits for rate-limiting in the file.
- **"cytosol" kept out of gly.start's teaching.** S-GLY does not state glycolysis's compartment verbatim (research §8 gly.start bullet: ground via S-FERM's fermentation-cytosol statement or soften) — teaching stays strictly inside GLY-INTRO-01's content; the word appears only in dramatic scene-setting, which is pre-existing skeleton framing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Bound CAST-PKLR-MUTANT-PDB-01 on gly.pyruvate_kinase**

- **Found during:** Task 1 (text authoring)
- **Issue:** The teaching text teaches PDB 2VGG (per DC-4 outcome), but the plan's claim-swap map did not list the 2VGG claim; an unbound scientific assertion would break the phase's grounding discipline (every scientific assertion traces to an approved claim bound on the node).
- **Fix:** Added "CAST-PKLR-MUTANT-PDB-01" to claim_ids (verified approved in data/citations.json first). No on_enter load added (see Decisions Made).
- **Files modified:** data/story_glucose/glycolysis.json
- **Verification:** citation gate 0 UNAPPROVED; suite 325 OK
- **Committed in:** de51bb0

**2. [Rule 2 - Missing Critical] Bound DIS-PFKM-01-cand on gly.pfk_restored ([] → 1 claim)**

- **Found during:** Task 1 (restored-node text authoring)
- **Issue:** The restoration teaching re-asserts the G209D approved wording (Raben 1995 + ClinVar VCV003375341); with claim_ids [] the assertion would be unbound.
- **Fix:** claim_ids ["DIS-PFKM-01-cand"] — explicitly sanctioned by the 07-12 DESIGN addendum ("text + claim swaps are plans 08/13"); on_enter/choices/tags untouched.
- **Files modified:** data/story_glucose/glycolysis.json
- **Verification:** test_restoration_nodes_reachable_non_ending green (pins ops/tags/choices, not claim_ids); gate resolves the id approved
- **Committed in:** de51bb0

---

**Total deviations:** 2 auto-fixed (2 missing-critical bindings, both additive claim_id changes — zero structural impact)
**Impact on plan:** Both bindings required by the phase's grounding discipline for text the plan itself mandated. No scope creep; no structural field touched.

## Issues Encountered

- The plan's `<verification>` gate line omits the required `--story/--registry` args (same pre-existing gap 07-09/07-11 recorded); ran the Phase-1-standard invocation `python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json`.
- Mid-execution, parallel wave plans 06 and 14 committed their files (pyruvate_branch.json content + edits.json signatures), moving the shared gate residual from 23 → 11 MISSING lines while this plan ran; the glycolysis bucket went 5 → 0. Remaining 11 = Phase-8 stubs (fa.stub/alc.stub, 2) + plan-13's TCA bucket (9, in flight). tools/check_edit_coverage.py exits 1 with the pre-existing cast.json residue (fixture_enzyme_1, PLACEHOLDER_large_enzyme) — identical at HEAD, owned by plan 15 (cast.json); unchanged-or-better ✓.
- git index.lock contention risk from parallel agents was watched for but did not occur (staged individually; single short commit).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Glycolysis content is COMPLETE: the citation-gate residual no longer contains any glycolysis lines; plan 16's sweep inherits a zero-placeholder glycolysis.json (fa/alc stubs are the documented Phase-8 exceptions in OTHER files).
- Plan 17/18 (human-verify): the beats to eyeball in real Windows PyMOL are (1) the gly.pfk 4PFK bacterial cast + its text frame, (2) the gly.pfk_restored reveal (edit→load→align→show_as with the disclosed symbolic-edit teaching), (3) the 7FS3 cast with oxalate/Mg²⁺ ligands visible, (4) the gly.fbp_to_pyruvate ledger phrasing.
- Plan 13 (TCA content) owns the remaining 9-line TCA placeholder bucket; nothing in this file blocks it.
- For a future phase: 2VGG's on_enter promotion (if a PKLR reveal node is ever sanctioned) needs no new claim approval — recorded approved here, consumed in text.
- Blockers: none.

## Verification (per plan)

- `python3.6 -m unittest tests.test_glucose_reachability -v`: 21 tests OK (incl. test_restoration_nodes_reachable_non_ending pinning gly.pfk_restored's on_enter op order + sele + reentry).
- `python3.6 -m unittest discover -s tests`: **325 tests OK** (count unchanged; zero regressions).
- `python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json`: 11 MISSING + 0 UNAPPROVED — 0 glycolysis lines (bucket was 5 at baseline); residual = documented other-plan buckets only.
- Structural integrity: parsed-equality diff vs HEAD — tags/on_enter/choices byte-identical on all 7 nodes; all text non-empty, non-TBD.
- Wording compliance: "Likely pathogenic" exactly once in each PFKM frame (gly.pfk + gly.pfk_restored); regex `(?<!Likely )pathogenic` = 0 hits; "confirmed pathogenic" = 0; OQ-G exact phrase "2 ATP invested + 2 ATP recovered + 2 NADH banked" present in both layers of gly.fbp_to_pyruvate; "Net so far: 2 ATP, 2 NADH" absent; rate-limiting/ROS (word-boundary)/electron-leak/TBD/PLACEHOLDER all 0.
- check_imports + check_alter_gate: clean.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-03*
