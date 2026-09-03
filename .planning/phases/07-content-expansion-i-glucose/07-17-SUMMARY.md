---
phase: 07-content-expansion-i-glucose
plan: 17
subsystem: content-verification
tags: [pymol, molactions, scene-templates, story-graph, conformance, verification, restore-reveal]

# Dependency graph
requires:
  - phase: 05.4-cast-hero-representation-design
    provides: the FROZEN 6-scene-type + 4-ending-tier template library (§4) this pass verifies against
  - phase: 05.3-wt-aligned-structure-load-convention
    provides: the §2(iii)/§6 restoration-reveal op contract (edit→load→align→show_as; target=mobile/reference=fixed)
  - phase: 07-12
    provides: the restored-node topology + THE ACONITASE MAPPING (align contract values verified here)
  - phase: 07-16
    provides: the 345-test content-invariant suite that machine-guards every frozen form this pass walked
provides:
  - "57/57-node 5.4 scene-template conformance verdict table (plan 18's input)"
  - "empirical op-by-op verification of BOTH restored-node 5.3 reveal wirings on real PyMOL (SMOKE_RESULT: PASS)"
  - "confirmation the sanctioned phase-7 structural state IS template-conformant (zero fixes, zero drift)"
affects: [07-18-final-gates-human-checkpoint, 07-19-scene-capture-tool, phase-9-full-cast, phase-12-ending-cutscenes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Template-conformance walk: tags+is_ending → 5.4 type → per-type op-sequence assertions at the phase-7-sanctioned granularity"
    - "Controller-faithful headless smoke: replay real story on_enter MolAction lists through real MolOps on real PyMOL cmd"

key-files:
  created:
    - "tmp/opencode-0717/reveal_wiring_smoke_07_17.py (gitignored; SMOKE_RESULT: PASS transcript in this SUMMARY)"
    - "tmp/opencode-0717/../verify harness (per-node walk; gitignored tmp/)"
  modified: []

key-decisions:
  - "Zero data fixes: the walked state is exactly the FROZEN phase-7 structural state (skeleton + 16 sanctioned loads + 2 pinned restored reveals); every apparent gap resolved as a frozen-form artifact, never edited"
  - "Restored nodes verified as the plan-12 pinned hide_all-LESS form [edit, load, align, show_as] — 05.3 §7.3 Template-1's leading hide_all would break the byte-intact pin (pin = frozen convention)"
  - "OQ#4 discharge: zero restore ops exist anywhere in the bundle → the restore-ONLY fix pattern never triggered; nothing to flag or fix"
  - "Watch item 6 (dotted object names) discharged vacuously: all 16 load object names are short/dot-free"

patterns-established:
  - "Conformance = type-appropriate ops at the sanctioned granularity (loads/hero-highlight/restored reveals), NOT the unlanded §5.2 selector depth (needs source-approved §6.2 claims — deferred with owners)"
---

# Phase 7 Plan 17: 5.4 Template-Fill Verification Summary

**57/57 glucose nodes verified 5.4-scene-template-conformant with ZERO fixes and ZERO drift; both restored nodes' 5.3 reveal wirings verified op-by-op on real Windows PyMOL (SMOKE_RESULT: PASS, finite RMSD, 319/754 matched CAs); suite 345 OK; citation gate at the sanctioned 2-stub residual**

## Performance

- **Duration:** 45 min
- **Started:** 2026-09-03T04:36:30Z
- **Completed:** 2026-09-03T05:21:22Z
- **Tasks:** 1/1
- **Files modified:** 0 (data files byte-identical vs HEAD — verified, not edited)

## Accomplishments
- Full per-node conformance walk of all 57 nodes: tags + is_ending → expected 5.4 type (6 types + 4 ending tiers + the 5.3 restoration form + the edit.prompt stub) → op-sequence assertions — **57/57 CONFORM** (verdict table below).
- **Restored nodes verified twice over**: (a) data-level — both carry the plan-12 pinned `[edit, load, align, show_as]` with the exact 07-12 ACONITASE-MAPPING contract args (edit sele "resi 209 and chain A"→GLY / "resi 85 and chain A"→SER; load pdb:4PFK→pfk_wt / pdb:1ACO→aconitase_wt; align target=WT-object(mobile), reference=enzyme(fixed), method=super, align_sele="name CA"); (b) **empirically** — a controller-faithful headless smoke replayed both real on_enter lists through the real MolOps dispatcher on real Windows PyMOL: edits land (resn verified GLY/SER), WT loads as a separate object, super+name CA aligns with finite RMSD (319 / 754 matched CAs), cartoon reveal visible, restore safety-net backup object present. **SMOKE_RESULT: PASS**.
- Ground-truth watch items discharged: **OQ#4** — zero `restore` ops exist anywhere in the bundle, so the self-undoing `[edit, restore]` ordering occurs 0 times and the sanctioned restore-ONLY fix pattern never triggered; **watch item 6** — zero dotted object names in any load op (all 16 are short names: pfk, pfk_wt, aconitase, aconitase_wt, pdh, ldh, citrate_synthase, isocitrate_dh, malate_dh, complex_ii/iii/iv, hero_atom, aa_cast, glucose).
- Zero text/claim/choice/node-id drift: `git diff HEAD -- data/story_glucose/` is EMPTY; hero-highlight + `_smoke.pdb` start ops byte-identical (start-shape tests green).

## Task Commits

1. **Task 1: Verify + fix template conformance across all 57 nodes** — no data commit (zero deviations found; nothing to commit — a no-op diff is the *successful* outcome here)

**Plan metadata:** see the docs(07-17) commit (PLAN.md + SUMMARY.md)

## Files Created/Modified
- NONE in the repo — all 7 story JSONs byte-identical vs HEAD (the conformance walk + PyMOL smoke live in gitignored `tmp/opencode-0717/`; scripts kept on disk for plan 18 re-runs).

## Per-node verdict table (57/57 — plan 18 consumes this)

Legend: type = expected 5.4 scene template (T1 preface / T2 substrate-traversal / T3 active-site-reveal / T4 branch-point / T5 rng-shuffle / T6-<tier> ending / T53 restoration-reveal / T2-cond narrative-only-edit-allowed per OQ-10(a) / STUB). All ops verified: hide_all first (except the pinned hide_all-less restored form), no dangling object refs, only documented ops (hide_all/load/show_as/show/color/label/set/set_color/edit/align).

| File | Node | Type | Verdict | Evidence |
|------|------|------|---------|----------|
| intro.json | intro.preface | T1 | CONFORM | frozen full form: hide_all→load _smoke.pdb(hero_atom)→6-call hero-highlight(set_color hero_cyan/show_as sticks/color elem C/show spheres/set sphere_scale 0.3/label YOU)→load aa_cast→show_as cartoon; byte-identical (start-shape tests green) |
| intro.json | intro.select | T1 | CONFORM | stripped [hide_all] (choice/UI beat per 5.4 §4.3) |
| intro.json | intro.shell_glucose | T1 | CONFORM | frozen form: hide_all→load _smoke.pdb(glucose)→show_as sticks→show_as aa_cast cartoon; exactly one glucose load (pinned) |
| intro.json | fa.stub | T1 | CONFORM | stripped [hide_all]; PLACEHOLDER_PHASE8 stub is the 07-01-sanctioned residual |
| intro.json | alc.stub | T1 | CONFORM | stripped [hide_all]; same sanctioned stub residual |
| glycolysis.json | gly.start | T2 | CONFORM | frozen skeleton variant: hide_all→show_as glucose sticks (glucose persisted from intro.shell_glucose on every path) |
| glycolysis.json | gly.g6p | T2 | CONFORM | [hide_all] (no substrate load sanctioned) |
| glycolysis.json | gly.pfk | T3 | CONFORM | hide_all→load pdb:4PFK (object pfk) — sanctioned cast load; no unapproved selector ops |
| glycolysis.json | gly.pfk_restored | T53 | CONFORM | plan-12 pinned [edit(pfk resi 209 chain A→GLY), load pdb:4PFK→pfk_wt, align(pfk_wt←super name CA→ref pfk), show_as pfk_wt cartoon]; re-entry choices Continue+mc:observe → gly.fbp_to_pyruvate; router-only entry intact; **PyMOL-verified** (edit lands GLY; align 319 CAs; cartoon on) |
| glycolysis.json | gly.fbp_to_pyruvate | T2 | CONFORM | [hide_all] |
| glycolysis.json | gly.pyruvate_kinase | T3 | CONFORM | hide_all→load pdb:7FS3 (object pyruvate_kinase) |
| glycolysis.json | gly.pyruvate | T2 | CONFORM | [hide_all] |
| pyruvate_branch.json | pyr.branch | T4 | CONFORM | [hide_all] (2-object comparison assets never sanctioned; DC-B made the fork a player choice at the choice layer) |
| pyruvate_branch.json | pyr.pdh | T3 | CONFORM | hide_all→load pdb:6CFO (object pdh); DC-5a load pinned by test |
| pyruvate_branch.json | anaer.entry | T4 | CONFORM | [hide_all] |
| pyruvate_branch.json | anaer.ldh | T3-style cast reveal | CONFORM | hide_all→load pdb:5W8J (object ldh) — sanctioned (07-02 #6, ground truth #3); not edit-allowed |
| pyruvate_branch.json | anaer.lactic | T6-good | CONFORM | [hide_all]; tier scene fills = Phase 12 (05.4 §6.4) |
| pyruvate_branch.json | anaer.ethanolic | T6-normal | CONFORM | [hide_all]; same Phase-12 owner |
| pyruvate_branch.json | anaer.crisis | T6-bad | CONFORM | [hide_all]; is_ending="bad" (the 15th bad tier member) |
| tca.json | tca.entry | T2 | CONFORM | [hide_all] |
| tca.json | tca.citrate_synthase | T3 (structural variant) | CONFORM | hide_all→load pdb:1CSC (object citrate_synthase) + homodimer teaching note (07-13 D7); NO mutant-flag ops (edit:structural — correct §5.2 sub-variant) |
| tca.json | tca.aconitase | T3 | CONFORM | hide_all→load pdb:1ACO (object aconitase) — 07-13 D6 load |
| tca.json | tca.aconitase_restored | T53 | CONFORM | plan-12 pinned [edit(aconitase resi 85 chain A→SER), load pdb:1ACO→aconitase_wt, align(aconitase_wt←super name CA→ref aconitase), show_as cartoon]; re-entry → tca.shuffle; **PyMOL-verified** (1ACO resi 85 natively SER per the 07-12 mapping — identity-preserving alter executes cleanly; align 754 CAs) |
| tca.json | tca.shuffle | T5 | CONFORM | [hide_all]; the graph's ONLY weighted node (0.5/0.5, pinned); prochiral scene assets never sanctioned |
| tca.json | tca.co2_turn1 | T2 (soul-transfer beat) | CONFORM | [hide_all]; CO2-shed visual assets never sanctioned (text owns the beat; anti-confusion wording is TEXT — authored) |
| tca.json | tca.co2_turn2 | T2 (soul-transfer beat) | CONFORM | [hide_all]; seed-42 documented fate target (determinism pin intact) |
| tca.json | tca.isocitrate_dh | T3 | CONFORM | hide_all→load pdb:5GRE (object isocitrate_dh) — 07-13 D3 |
| tca.json | tca.akg_dh | T2-cond | CONFORM | [hide_all] — MUST NOT load: no approved OGDH cast PDB (manifest pin cast(12)==edits(13)−{tca.akg_dh}) |
| tca.json | tca.succinyl_coa_synthetase | T2-cond | CONFORM | [hide_all]; 6WCV cast-sourced but load never promoted (dormant, 2VGG precedent) |
| tca.json | tca.fumarase | T2-cond | CONFORM | [hide_all]; 5UPP dormant likewise |
| tca.json | tca.malate_dh | T3 | CONFORM | hide_all→load pdb:4WLU (object malate_dh) — 07-13 D8 |
| tca.json | tca.divert_to_good | T4 | CONFORM | [hide_all] |
| etc_atp.json | etc.entry | T4 | CONFORM | [hide_all]; "let go" = proton-leak exit (text owns the science) |
| etc_atp.json | etc.complex_i | T2-cond | CONFORM | [hide_all] — 5LDW stays a TEXT teaching beat (cryo-EM 4.27 Å), NEVER promoted (ground truth #3) |
| etc_atp.json | etc.complex_ii | T3 | CONFORM | hide_all→load pdb:1ZOY (object complex_ii) — 07-09 Decision 6b |
| etc_atp.json | etc.complex_iii | T3 | CONFORM | hide_all→load pdb:1BGY (object complex_iii) — 07-09 Decision 6b |
| etc_atp.json | etc.complex_iv | T3 | CONFORM | hide_all→load pdb:1OCC (object complex_iv) |
| etc_atp.json | etc.atp_synthase | T2 | CONFORM | [hide_all] — 1E79 DCCD beat stays TEXT, NEVER promoted |
| etc_atp.json | end.true | T6-true | CONFORM | [hide_all]; soul-jump climax = TEXT (anti-confusion template authored per 5.4 §3.6); ATP scene = Phase 12 |
| endings.json | end.good.fatty_acid | T6-good | CONFORM | [hide_all] |
| endings.json | end.good.amino_acid | T6-good | CONFORM | [hide_all] |
| endings.json | end.normal.co2 | T6-normal | CONFORM | [hide_all] |
| bad_endings.json | bad.lost_connection | T6-bad | CONFORM | [hide_all] |
| bad_endings.json | bad.released_from_host | T6-bad | CONFORM | [hide_all] |
| bad_endings.json | bad.cycle_trap_host_death | T6-bad | CONFORM | [hide_all]; cycle_trap tag intact (0.5/0.5 loop = game device) |
| bad_endings.json | bad.critical_residue_break | T6-bad | CONFORM | [hide_all]; edit:known_critical |
| bad_endings.json | bad.enzyme_collapse | T6-bad | CONFORM | [hide_all] |
| bad_endings.json | bad.wrong_substrate_trapped | T6-bad | CONFORM | [hide_all] |
| bad_endings.json | bad.broken_active_site | T6-bad | CONFORM | [hide_all] |
| bad_endings.json | bad.lost_in_cytosol | T6-bad | CONFORM | [hide_all] |
| bad_endings.json | bad.proton_leak | T6-bad | CONFORM | [hide_all]; PROTONS-first text (Decision 7) untouched |
| bad_endings.json | bad.misfolded_aggregate | T6-bad | CONFORM | [hide_all] |
| bad_endings.json | bad.active_site_destroyed | T6-bad | CONFORM | [hide_all] |
| bad_endings.json | bad.substrate_channel_blocked | T6-bad | CONFORM | [hide_all] |
| bad_endings.json | bad.cofactor_lost | T6-bad | CONFORM | [hide_all] |
| bad_endings.json | bad.denature_ph_change | T6-bad | CONFORM | [hide_all] |
| bad_endings.json | edit.prompt | STUB | CONFORM | [hide_all]; structural stub untouched (structural on_enter + 13 choices intact; the ONLY text-invariant exemption) |

**Tallies:** 57 nodes / 21 endings (1T+3G+2N+15B — Type-6 tier mapping exact) / 15 edit-allowed == 15 edit:offer nodes / 16 load ops == exactly the sanctioned set (11 sanctioned phase-7 enzyme loads + 4 frozen _smoke.pdb/start loads + 2 restored WT loads) / 0 restore ops / 0 dotted object names / 0 pdb:TBD* targets / 0 dormant PDB loads (2VGG, 6CER, 1ZP0, 5LDW, 1E79, 5UPP, 6WCV all correctly absent from on_enter).

## Decisions Made
- **Zero fixes is the correct outcome.** Every apparent deviation resolved as a frozen-form artifact: the restored nodes' hide_all-less opener (plan-12 byte-intact pin outranks 05.3 §7.3 Template-1's leading hide_all), anaer.ldh's load (sanctioned cast reveal, not a bare T2), and the [hide_all]-only forms at T4/T5/T6/§5.2-depth nodes (assets/selector-claims never sanctioned in phase 7 — adding them would fabricate science). The pin-vs-fix rule was applied twice in the fix's disfavor, exactly as ground truth #2 directs.
- **Verification went empirical.** The plan's "full 5.3 reveal-wiring verification" was executed at BOTH levels: data-level op-by-op assertions AND a real-PyMOL replay of both restored on_enter sequences through the real MolOps dispatcher (controller-faithful; reads the actual story JSONs, no hand-copied ops).
- Deferred visual depth recorded with owners (NOT gaps): §5.2 per-enzyme cast-reveal selectors (active_site/catalytic/mutant/label_anchor) require source-approved §6.2 claims — Phase 9 full-cast territory, plan 18 reviews cast depth; Type-6 ending tier scenes + Type-4 branch 2-object + Type-5 prochiral scene = Phase 12 per 05.4 §6.4 (06-VERIFICATION concurs: "Ending cutscene/CG — Phase 12").

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Verification tooling created outside the plan's file list**
- **Found during:** Task 1
- **Issue:** The plan's file list contains only the 7 story JSONs, but "full 5.3 reveal-wiring verification" needs an executable check (data-level inspection alone cannot prove the align wiring works on real coordinates), and no repo tool existed for either the walk or the replay.
- **Fix:** Wrote both harnesses to gitignored `tmp/opencode-0717/` (per-node 5.4-type walker; controller-faithful reveal smoke reading the real story JSONs). No repo file added; nothing committed for them.
- **Files modified:** none in the repo (gitignored tmp/ only)
- **Verification:** walker 57/57 CONFORM; smoke SMOKE_RESULT: PASS (14/14 checks)
- **Committed in:** n/a (gitignored; transcript below)

**2. [Rule 1 - Bug] Two smoke-script bugs fixed during the run (verification-script only, no data impact)**
- **Found during:** Task 1 (smoke run 1)
- **Issue:** (a) Windows PyMOL's Python opens files cp1252 by default → UnicodeDecodeError on tca.json's UTF-8 text; (b) the smoke expected the session object set to be exactly {enzyme, enzyme_wt} but the restore safety net's `_bak_*` backup object is present BY DESIGN after any edit (edit_ops take_backup) — a wrong expectation in the smoke, not a data defect.
- **Fix:** explicit `encoding="utf-8"` on story-file reads; object-set assertions now ignore `_bak_*` (documented as expected engine behavior).
- **Files modified:** tmp/opencode-0717/reveal_wiring_smoke_07_17.py (gitignored)
- **Verification:** re-run → SMOKE_RESULT: PASS
- **Committed in:** n/a

---

**Total deviations:** 2 auto-fixed (1 blocking-verification-tooling, 1 smoke-script bug) — zero data deviations, zero story-file edits.
**Impact on plan:** Success criteria met without touching a single story byte: "57/57 nodes template-conformant; both restored nodes carry verified 5.3 reveal wiring; zero text/claim drift introduced."

## Verification evidence

- `python3.6 -m unittest discover -s tests` → **Ran 345 tests — OK** (baseline preserved; every pin intact)
- `python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json` → exit 1, **"2 missing + 0 unapproved"**, exactly the 2 sanctioned `[MISSING]` lines (fa.stub/alc.stub → PLACEHOLDER_PHASE8), 0 UNAPPROVED — the machine-pinned residual form unchanged
- `git diff HEAD --stat -- data/story_glucose/` → empty (byte-identical)
- Headless PyMOL reveal smoke (`run-conda-pymol.bat -cq`, gitignored script): **SMOKE_RESULT: PASS** —
  Scene A (gly.pfk→gly.pfk_restored, pdb:4PFK): source replay PASS (2534 atoms) · edit resi 209 chain A→GLY PASS · pfk_wt loaded PASS · super(name CA) finite RMSD, 319 matched CAs PASS · pfk_wt cartoon PASS · object set {pfk, pfk_wt} + _bak_pfk PASS
  Scene B (tca.aconitase→tca.aconitase_restored, pdb:1ACO): source replay PASS (6138 atoms) · edit resi 85 chain A→SER PASS (identity-preserving per the 07-12 mapping) · aconitase_wt PASS · super(name CA) finite RMSD, 754 matched CAs PASS · cartoon PASS · object set + _bak_aconitase PASS
  (RMSD 0.0000 is correct: both overlay objects are the same PDB in the same frame — a perfect overlay is the honest restoration visual; the teaching text owns the pedagogy.)

## Issues Encountered
- None blocking. Note for plan 18's human-verify: the visual layer plan 18 will SEE is exactly the walked state — start-node hero-highlight + sanctioned enzyme loads + the two restored overlay reveals; §5.2-depth cast reveals (active-site zooms, green/magenta flags, nameplate labels) and ending-tier scenes are NOT in the data (no approved selector claims / Phase-12 ownership). This is by-design, documented above, and the 07-15 flag stands: 6 of 12 cast PDBs bind DIS-* claims rather than CAST-* claims (plan 18 reviews).

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- **Ready for 07-18** (final gates + human checkpoint): the last automated gate before the human checkpoint is green — suite 345 OK, citation gate at the sanctioned residual, all 57 nodes template-conformant, both restored reveals empirically proven on real PyMOL.
- The per-node verdict table above is plan 18's input (per the orchestrator's coordination rule).
- Watch items carried INTO 18: (a) plan 18 reviews cast-claim binding depth (6/12 DIS-*-bound, CAST-* optional); (b) the deferred §5.2/Type-6/Type-4/Type-5 visual depth is Phase 9/12 scope — set expectations in the human checkpoint accordingly; (c) dotted-object-name watch item is discharged (no dotted names exist).
- STATE.md deliberately untouched (orchestrator consolidates).

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-03*
