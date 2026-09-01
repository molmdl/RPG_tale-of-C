---
phase: 07-content-expansion-i-glucose
plan: 04
subsystem: content-approval
tags: [etc, oxidative-phosphorylation, atp-synthase, endings, bad-ending-pool, citation-gate, proton-leak, ucp1, approval-ledger, soul-jump]

# Dependency graph
requires:
  - phase: 07-research (07-RESEARCH-etc-endings.md)
    provides: verified candidate ledger — ETC chemistry claims C1–C14, 4 DIS-* disease candidates, bad-pool 14 mappings, 5 PDB candidates, source batch (all fetched live 2026-08-30)
  - phase: 5.1 (disease-mutant replan)
    provides: DIS-NDUFS8/SDHA/CYC1/COX4I1 -cand claim ids, PDB chain/residue mappings (coordinate-file verified 2026-08-20), edits.json signature formats
  - phase: 5 (atp-soul-jump research + first source batch)
    provides: ATP-SOUL-01..09 enumeration, hybrid claim taxonomy (rows 109/110), rejection-with-provenance precedent (LEHNINGER)
provides:
  - "Approval batch C ledger: 9 decision Outcomes + per-claim VERDICTs (C1–C13 + inherited ATP-SOUL) + per-source VERDICTs incl. one rejection with provenance"
  - "OQ2 resolution: oq2-uncoupling — etc.entry 'let go' = the real proton-leak/UCP1 branch (ETC-UCP-01, MEDIUM until J&F 19.3 subpage confirm at landing)"
  - "ETC framing rules locked for text authoring: no numeric P/O yields anywhere; no ROS claims in v1; proton-leak text says PROTONS, never 'electrons leak'; anti-confusion binding (electrons = the soul → ETC → ATP; carbon shed as CO2; never 'C14 becomes ATP')"
  - "CYC1 allele = L215F; COX4I1 dual-numbering convention (PDB numbering in signatures, human P152T in narrative)"
  - "complex_ii/iii PDB-bearing promotion (1ZOY/1BGY loads) + Template-3 restore shortcut (pre-edit backup IS WT) approved"
affects: [07-05 (registry landing), 07-09/10/11 (ETC + endings + bad-pool content), 07-14 (edits.json ETC signatures), phase 9 (cast), phase 11 (docs)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Approval-ledger summary: verbatim human Outcome lines per decision + VERDICT lines per claim/source"
    - "Subpage-confirm-at-landing: chapter-level source approval carries a landing-time subpage verification condition (same pattern as approved J&F Ch 16)"
    - "Dual numbering: PDB numbering in edits.json signatures + edit UI; human literature numbering in narrative + teaching bridge"
    - "Rejection retained with provenance (LEHNINGER precedent) — LIBRETEXTS-METAB-ETC-II"

key-files:
  created:
    - .planning/phases/07-content-expansion-i-glucose/07-04-SUMMARY.md
  modified:
    - .planning/STATE.md

key-decisions:
  - "Human verdict 2026-09-01: 'All 9 defaults' — every batch-C decision taken at the research recommendation"
  - "OQ2 = oq2-uncoupling: etc.entry 'let go' maps to the REAL proton-leak/UCP1 branch; ETC-UCP-01 is MEDIUM until the J&F 19.3 subpage is confirmed at landing"
  - "CYC1 allele = L215F (ClinVar 2025-11-20, criteria provided, single submitter) over skeleton default W96C — evidence-strength choice; both real MC3DN6 variants from PMID 23910460"
  - "COX4I1: edits.json uses PDB numbering (resi 130 and chain D, new_res PRO); narrative uses human P152T + teaching bridge (152 − 22 transit peptide = 130); P10515 artifact rejected — P13073 is COX4I1"
  - "no numeric P/O yields anywhere in v1; if ever taught, contested-tier + modern verified source + 'approximate' hedge (documented path, not v1)"
  - "no ROS claims in v1; proton-leak text aligned to PROTONS (never 'electrons leak' — that is ROS territory with no verified source)"
  - "complex_ii/iii promoted to PDB-bearing nodes (add 1ZOY + 1BGY loads + pre-edit/mutant-flag MolActions); Template-3 restore shortcut for the ETC quartet (the pre-edit backup IS the WT); restore-handle semantics verified headlessly in plan 09"

patterns-established:
  - "Outcome/VERDICT ledger lines as the machine-greppable record of human approval batches (plan 05 consumes them)"
  - "Source approval may carry an explicit landing-time condition (subpage confirm) recorded in the ledger"
  - "Structure upgrades (5XTD/9HZL/9I6F/7QSK/1BMF) documented as the future upgrade path, NOT swapped in v1 (protects verified residue mappings)"

# Metrics
duration: ~10 min (continuation segment; the plan reached its single checkpoint in a prior session and resumed when the human answered)
completed: 2026-09-01
---

# Phase 7 Plan 04: Approval Batch C — ETC + Endings + Bad-Ending Pool Summary

**Human verdict "All 9 defaults" recorded as the batch-C approval ledger: 5 ETC PDBs + J&F Ch 19 source batch approved, ETC-II REJECTED for outdated 3/2 P/O yields, OQ2 reframed to the real proton-leak/UCP1 branch, L215F chosen for CYC1, and the no-numeric-yields / no-ROS / anti-confusion framing rules locked before any ETC text is authored.**

## Performance

- **Duration:** ~10 min (continuation; single-checkpoint plan — the prior session ran the read-only verification and paused at the decision checkpoint)
- **Started (continuation):** 2026-09-01T02:43:23Z
- **Completed:** 2026-09-01
- **Tasks:** 1/1 (checkpoint:decision — verdicts recorded; registry landing is plan 07-05's job)
- **Files modified:** 2 (this SUMMARY + STATE.md)

---

## THE HUMAN VERDICT (verbatim)

> **"All 9 defaults"**

Recorded 2026-09-01. Every batch-C decision = the research recommendation. The 9 decision Outcomes follow.

## Decision Outcomes (9/9)

**Decision 1 — ETC PDB set.**
Human (verbatim): "ETC PDB set: approve 5LDW/1ZOY/1BGY/1OCC/1E79 as-is"
Outcome: APPROVED — all five structure candidates kept for v1 exactly as verified (research §3.1). 5LDW is cryo-EM 4.27 Å (cast text says EM, not X-ray); 1OCC already loads in the skeleton; all four disease-residue mappings stand (coordinate-verified 2026-08-20). Human-species upgrades (5XTD/9HZL/9I6F/7QSK) documented as the future upgrade path, NOT swapped — swapping would invalidate the verified mappings and force re-verification of the whole ETC edit arc.

**Decision 2 — ATP-synthase cast.**
Human (verbatim): "ATP-synthase cast: keep 1E79 (DCCD caveat = teaching beat)"
Outcome: APPROVED — 1E79 (bovine F1-ATPase, DCCD-inhibited, 2.4 Å, Gibbons 2000) kept; 1BMF recorded as the documented alternative, not selected. The DCCD caveat becomes an honest teaching beat (research §10.6 wording available: the enzyme is "shown with its DCCD inhibitor bound — the molecule researchers used to freeze it for photography"). 1E79 receives its FIRST source-record approval (never per-claim approved before; plan 05 adds the sources.json record).

**Decision 3 — CYC1 allele.**
Human (verbatim): "CYC1 allele: L215F (ClinVar 2025, criteria provided)"
Outcome: APPROVED — L215F replaces the skeleton-default W96C as the complex_iii disease allele (research §4.3). Both are real UniProt-annotated MC3DN6 variants from the same paper (PMID 23910460, corrected to 93(2):384–389); L215F wins on evidence strength (ClinVar VCV000066020, Pathogenic, last evaluated 2025-11-20, "criteria provided, single submitter" vs W96C's 2013 "no assertion criteria provided"). Implementation: PDB 1BGY chain D resi 131 (215 − 84 transit peptide = 131); restoration signature `{"op":"point_mutation","target":"resi 131 and chain D","args":{"new_res":"LEU"}}` (reverses the disease Phe131; human-literature restoration name F215L). W96C remains documented as the discarded skeleton default. Plans 09/14 implement.

**Decision 4 — COX4I1 numbering.**
Human (verbatim): "COX4I1 numbering: edits use PDB numbering (`resi 130 and chain D`, new_res PRO); text says human P152T + teaching bridge"
Outcome: APPROVED — dual-numbering convention locked (fills 05.1 OQ-DM7). edits.json signature uses PDB numbering: `{"op":"point_mutation","target":"resi 130 and chain D","args":{"new_res":"PRO"}}`; player-facing narrative uses the human literature name P152T with the teaching bridge ("the disease residue Pro152 in the human protein = residue 130 in chain D of the bovine structure you see"; 152 − 22 = 130, verified arithmetic from live UniProt P13073). Also recorded: the task brief's "UniProt P10515" is a different protein — rejected as an artifact; P13073 is COX4I1. Plans 09/14 implement.

**Decision 5 — OQ2 Normal-ending framing.**
Human (verbatim): "OQ2: **oq2-uncoupling** — 'let go' = real proton-leak/UCP1 branch (J&F 19.3, MEDIUM until subpage confirm at landing)"
Outcome: APPROVED — option (b) oq2-uncoupling (the recommendation). `etc.entry`'s "let go" choice maps to the REAL electron-stage fork: proton leak / uncoupling (basal inner-membrane proton permeability; UCP1-mediated non-shivering thermogenesis). Claim candidate **ETC-UCP-01** ("Proton leak/uncoupling dissipates the proton-motive force without driving ATP synthase; electron transport and CO2 production continue") — MEDIUM until the J&F 19.3 subpage-level coverage is confirmed at landing (plan 05's landing-time check). Keeps the carbon-fate claim identical in both branches (no invented carbon chemistry), gives `end.normal.co2` real teaching content, and fixes `bad.proton_leak`'s text mismatch. `end.normal.co2`'s NARRATIVE-FRAMING FLAG is RESOLVED — the flag text is deleted when plans 09/10/11 implement the framing. STORY-07 SC3 satisfied via a real branch.

**Decision 6 — Restore shortcut + complex_ii/iii promotion (two-part).**
Human (verbatim): "Template-3 restore shortcut (pre-edit backup IS WT; headless verify in plan 09) + complex_ii/iii promotion (add 1ZOY/1BGY loads): both approved"
Outcome: APPROVED (both parts).
- (6a) Template-3 restore shortcut: for all four ETC disease quartet enzymes, mutant_reveal_approach = (a) apply_edit → 05.3 Template 3 (`edit → restore → show_as → color → zoom`); the pre-edit backup IS the WT — no explicit WT-load+align needed (the WT PDB is already the loaded base object). `conformational_difference: "minor"` with a reasoned structural note at authoring time (point mutations at these resolutions have no major domain shift). The one engine-semantics check — confirm `op="restore"` on the branch node retrieves the WT backup (from the pre-edit disease mutation), not the player-edit's own backup (research OQ#4 / §10.4) — is verified headlessly during plan 09.
- (6b) complex_ii/iii promotion: `etc.complex_ii` and `etc.complex_iii` are promoted from narrative-only to PDB-bearing — add 1ZOY + 1BGY on_enter loads with pre-edit + mutant-flag MolActions per the 5.4 convention (5.4 OQ-10 per-enzyme decision). `etc.atp_synthase` stays non-edit (no disease mutant in scope — 05.1 confirmed). Plans 09/14 implement.

**Decision 7 — no-ROS-v1.**
Human (verbatim): "no-ROS-v1: no ROS claims; proton-leak text says PROTONS, never 'electrons leak'"
Outcome: APPROVED — no ROS/electron-leak claims anywhere in v1 (no verified in-hub source; research OQ#3). The proton-leak TEXT MISMATCH FLAG is resolved by mandate: `bad.proton_leak`'s current "your electrons leak to nowhere" wording is REWRITTEN to the proton phenomenon (the gradient bleeds away; ATP synthesis falls) per the oq2-uncoupling framing — the text says PROTONS, never "electrons leak". If ROS is ever wanted, it needs a new verified source (documented path, not v1).

**Decision 8 — P/O yields.**
Human (verbatim): "P/O yields: none anywhere"
Outcome: APPROVED — **no numeric P/O yields anywhere** in dramatic or teaching text (research C14 recommendation, now evidence-backed: the only in-hub page with numbers states the deprecated pre-1978 3/2 values). The dramatic arc loses nothing: "the falling electrons pump protons, and the returning protons power ATP synthase" is complete without numbers. If a yield sentence is ever wanted: contested-tier claim + modern source verified at approval time (check J&F 19.2's subpage first) + an explicit "approximate, varies with conditions" hedge — documented as the future path, NOT v1.

**Decision 9 — Sources/claims verdicts.**
Human (verbatim): "Sources/claims verdicts: approve per §6 (~15 new sources incl. LIBRETEXTS-BIOCHEM-JF-CH19 [subpage confirm at landing], LIBRETEXTS-METAB-ETC, S-BIOX re-confirmation; REJECT LIBRETEXTS-METAB-ETC-II with provenance — outdated 3/2 P/O yields; upgrades 5XTD/9HZL/9I6F documented not-v1; ETC claims C1-C13 + inherited ATP-SOUL-03/07/08/09; DIS-NDUFS8/SDHA/CYC1/COX4I1 -cand approved keeping -cand ids; bad-pool 14 mappings per §6 with BAD-MISFOLD/AGGREG/PH sources UNVERIFIED → stay pending, text stays generic)"
Outcome: APPROVED per §6 — the full per-claim and per-source VERDICT tables below. Registry landing is plan 07-05's exclusive job (sole-writer rule): flip `approval_status` to "approved", KEEP the -cand ids verbatim (M1 policy), retain the ETC-II rejection with provenance (LEHNINGER precedent), and run the landing-time subpage confirms.

---

## Per-claim VERDICTs (ETC chemistry, C1–C14)

Tier per the row-109 HYBRID taxonomy. All VERDICTs are the human's 2026-09-01 batch-C decision; plan 07-05 lands them in `data/citations.json`.

| # | Node | claim_id | Tier | VERDICT |
|---|------|----------|------|---------|
| C1 | `etc.entry` | `ATP-SOUL-03` (inherit) | routine | **VERDICT: APPROVED** — NADH/FADH2 deliver fuel electrons to the ETC (chem LibreTexts ETC verified verbatim + J&F 19.1) |
| C2 | `etc.complex_i` | `ETC-CI-01` | routine | **VERDICT: APPROVED** — Complex I receives electrons from NADH, passes them to ubiquinone |
| C3 | `etc.complex_ii` | `ETC-CII-01` | routine | **VERDICT: APPROVED** — Complex II (succinate dehydrogenase) oxidizes succinate→fumarate via FAD→FADH2 to ubiquinone; the TCA↔ETC bridge |
| C4 | `etc.complex_ii` + `iii` | `ETC-Q-01` | routine | **VERDICT: APPROVED** — Q is the mobile carrier collecting electrons from I and II (also ETF, glycerol-3-P DH), delivering QH2 to III |
| C5 | `etc.complex_iii` | `ETC-CIII-01` | routine | **VERDICT: APPROVED** — Complex III (bc1) oxidizes ubiquinol, passes electrons to cytochrome c |
| C6 | `etc.complex_iii` + `iv` | `ETC-CYTC-01` | routine | **VERDICT: APPROVED** — cytochrome c transfers electrons only from III to IV (intermembrane-space carrier) |
| C7 | `etc.complex_iv` | `ETC-CIV-01` | routine | **VERDICT: APPROVED** — Complex IV transfers electrons from cytochrome c to O2, reducing it to H2O; O2 = terminal acceptor (highest reduction potential); cross-refs the settled 2026-08-15 anaerobic verification |
| C8 | `etc.complex_i/iii/iv` | `ETC-PMF-01` | routine | **VERDICT: APPROVED** — I, III, IV pump protons building the proton-motive force; Complex II does NOT pump |
| C9 | `etc.atp_synthase` | `ATP-SOUL-07` (inherit) | **high-stakes** | **VERDICT: APPROVED** — the literal soul-jump step: proton gradient drives the F0 rotor → F1 phosphorylates ADP+Pi→ATP. Phase 5's "no dedicated LibreTexts home" flag RESOLVED via J&F 19.2 (binding-change mechanism). review_notes evidence trail required at landing |
| C10 | `etc.atp_synthase` / `end.true` | `ETC-CHEM-01` | routine | **VERDICT: APPROVED** — chemiosmotic phosphorylation; overall ETC reaction electrons+H+ +O2→H2O + energy captured as ATP |
| C11 | `end.true` | `ATP-SOUL-01` / `ATP-SOUL-02` | high-stakes | **VERDICT: CROSS-REF ONLY — NOT re-approved here.** Carbon-fate half (all glucose carbons exit as CO2 via PDH + TCA decarboxylases) is owned by the Phase 5 batch / TCA researcher (plan 07-03's batch); batch C defers to that verdict per the research's explicit "do NOT re-approve here" |
| C12 | `end.true` | `ATP-SOUL-08` (inherit) | **high-stakes** | **VERDICT: APPROVED** — the soul-jump framing claim: the hero's *electrons* (the narrative "soul") drive ATP synthesis; the carbon body was shed as CO2; the carbon never becomes ATP. Framing authority = PROJECT.md Pitfall 4 (row 107); review_notes required at landing |
| C13 | `end.true` | `ATP-SOUL-09` (inherit) | **high-stakes** | **VERDICT: APPROVED** — RNG-gate link: the soul reaches ATP only via the RNG-weighted TCA path (cross-refs approved TCA-RNG-CITRATE-PROCHIRALITY-01); review_notes required at landing |
| C14 | any ETC node | (numeric yields ≈2.5/1.5) | contested | **VERDICT: NOT APPROVED — RULE SUBSUMES IT.** Decision 8 = no numeric P/O yields anywhere; C14 never enters the registry as a usable claim. Documented conflict retained: LIBRETEXTS-METAB-ETC-II's "three ATP" per NADH is the deprecated 3/2 value (the rejection's provenance) |

**Inherited ATP-SOUL claims approved in this batch:** ATP-SOUL-03 (C1), ATP-SOUL-07 (C9), ATP-SOUL-08 (C12), ATP-SOUL-09 (C13) — approved with their inherited ids. ATP-SOUL-01/02 belong to the carbon-fate owner (C11 cross-ref). The ids stay verbatim (no renaming); plan 07-05 flips status only.

## Per-claim VERDICTs (disease candidates — `-cand` ids RETAINED per M1 policy)

| claim_id | VERDICT | Key facts locked |
|----------|---------|------------------|
| `DIS-NDUFS8-01-cand` | **VERDICT: APPROVED (keeps -cand id)** | NDUFS8 R102H (human O00217; VAR_019539; dbSNP rs121912638; MC1DN2/Leigh). ClinVar VCV000007512 "Conflicting classifications of pathogenicity" (2024-05-23, criteria provided, conflicting) — the known weak spot, kept on UniProt + original-paper strength (Loeffen 1998, PMID 9837812, "first nuclear-encoded complex I mutation in a Leigh patient"). PDB 5LDW chain I resi 68 (102 − 34 transit = 68); restoration signature `resi 68 and chain I` / `new_res ARG` |
| `DIS-SDHA-01-cand` | **VERDICT: APPROVED (keeps -cand id)** | SDHA R554W (human P31040; VAR_002449; LS). ClinVar VCV000008742 "Likely pathogenic" (2025-12-15, criteria provided, multiple submitters, no conflicts). Bourgeron 1995 (PMID 7550341), "first mutation in a nuclear-encoded respiratory-chain component". PDB 1ZOY chain A resi 512 (554 − 42 = 512); restoration `resi 512 and chain A` / `new_res ARG` (W512R) |
| `DIS-CYC1-01-cand` | **VERDICT: APPROVED (keeps -cand id) — allele = L215F per Decision 3** | CYC1 L215F (human P08574; VAR_070848; MC3DN6). ClinVar VCV000066020 Pathogenic (2025-11-20, criteria provided, single submitter). Gaignard 2013 (PMID 23910460 — citation CORRECTED to 93(2):384–389). PDB 1BGY chain D resi 131 (215 − 84 = 131); restoration `resi 131 and chain D` / `new_res LEU` (F215L human / F131L PDB). W96C (VCV000066019, 2013, no criteria) documented as the discarded skeleton default |
| `DIS-COX4I1-01-cand` | **VERDICT: APPROVED (keeps -cand id)** | COX4I1 P152T (human P13073 — NOT P10515, a different protein; VAR_084182; MC4DN16). ClinVar VCV000834063 Pathogenic (2020-10-23, no assertion criteria). Pillai 2019 (PMID 31290619 — citation CORRECTED to 179(10):2138–2143 + title "...developmental regression, intellectual disability, and seizures"). PDB 1OCC chain D resi 130 (152 − 22 = 130); restoration `resi 130 and chain D` / `new_res PRO` (T130P) per Decision 4's PDB-numbering mandate. Note: the OTHER MC4DN16 variant (101..102 KT→NS, PubMed 28766551) is a 2-residue indel — mechanically unusable for cmd.alter; never confused with P152T |

All four verified mechanically compatible (missense, residue present, correct WT identity in the actual coordinate files, 2026-08-20).

## Per-claim VERDICTs (bad-ending pool — 14 mappings per §6)

Pool structure FROZEN (no topology changes); Phase 7 authors text + claims only. Pending-source claims keep text GENERIC until their sources verify at landing.

| # | Node | Claim candidate | VERDICT |
|---|------|-----------------|---------|
| 1 | `bad.lost_connection` | generic mutability (Pitfall-10 explanatory template) | **VERDICT: APPROVED** — mechanic-narrative fallback #1; no external source needed |
| 2 | `bad.released_from_host` | same template, different flavor | **VERDICT: APPROVED** — fallback #2; no external source needed |
| 3 | `bad.cycle_trap_host_death` | `BAD-HOST-01` — sustained respiratory-chain failure starves the organism; electron flow to O2 is vital | **VERDICT: APPROVED** (routine-to-medium) — S-BIOX verbatim anchor verified live ("The flow of electrons is a vital process that provides the necessary energy for the survival of all organisms"). Death-side text only; visit-cap/RNG-loop mechanics = TCA researcher; NO futile-cycling claim asserted (unverified) |
| 4 | `bad.critical_residue_break` | `BAD-CRIT-01` — mutating a catalytic/structurally critical residue can abolish enzyme activity | **VERDICT: APPROVED** (routine) — J&F 19.1 + per-enzyme grounding via the approved DIS-* candidates |
| 5 | `bad.enzyme_collapse` | `BAD-MISFOLD-01` | **VERDICT: MAPPING APPROVED; CLAIM STAYS PENDING** — source (J&F Unit I folding chapter) UNVERIFIED → claim not approvable; text stays generic until a folding source verifies at landing |
| 6 | `bad.wrong_substrate_trapped` | `BAD-INHIB-01` — substrate analogs bind SDH and stall it | **VERDICT: MAPPING APPROVED; claim MEDIUM** — 1ZP0 existence verified (real SDH-inhibitor co-complex: 3-nitropropionate + TTFA, via 1ZOY's related-entries); entry to be individually fetched at landing; inhibitor-chemistry wording (named compounds malonate/3NP) needs its own per-claim chemistry source at authoring |
| 7 | `bad.broken_active_site` | `BAD-ACTSITE-01` (may merge with #4) | **VERDICT: APPROVED** (routine) — site-scoped sibling of #4; merge permitted |
| 8 | `bad.lost_in_cytosol` | `BAD-DIFFUSE-01` — metabolites react only when bound by their enzyme | **VERDICT: APPROVED** (routine, near-tautological) — J&F Ch 16 inherits |
| 9 | `bad.proton_leak` | `ETC-UCP-01` (shared with Decision 5) | **VERDICT: APPROVED as mapping; claim MEDIUM until J&F 19.3 subpage confirm at landing** — TEXT FIX MANDATED per Decision 7: aligns to the proton-leak phenomenon (PROTONS, never "electrons leak"); node id frozen, text rewritten |
| 10 | `bad.misfolded_aggregate` | `BAD-AGGREG-01` — misfolded proteins aggregate and are targeted by quality-control/degradation systems | **VERDICT: MAPPING APPROVED; CLAIM STAYS PENDING** — source UNVERIFIED → text stays generic; differentiate from #5 (collapse = enzyme-level loss of folded state; aggregate = proteostasis/cellular clearance story) |
| 11 | `bad.active_site_destroyed` | same class as #7 (`edit:known` severity sibling) | **VERDICT: APPROVED** (routine) — per-enzyme DIS claims / J&F 19.1 |
| 12 | `bad.substrate_channel_blocked` | `BAD-CHANNEL-01` — substrate can no longer reach the active site | **VERDICT: APPROVED** (routine) — with the generic-phrasing condition (avoids needing a channel-specific citation) |
| 13 | `bad.cofactor_lost` | `BAD-COFACTOR-01` — mutations in cofactor-binding residues prevent cofactor binding, abolish activity | **VERDICT: APPROVED** (routine) — J&F 19.1 + the verified PDB ligand lists (5LDW FMN/N3/FES/SF4/ZN; 1ZOY FAD/FES/SF4/HEM) |
| 14 | `bad.denature_ph_change` | `BAD-PH-01` — extreme pH disrupts salt bridges → denaturation → catalytic loss | **VERDICT: MAPPING APPROVED; CLAIM STAYS PENDING** — source UNVERIFIED → text stays generic; physiological caveat mandated (mitochondrial matrix ~pH 7.8 in vivo — a LARGE pH shift is a pathology/experimental condition, not routine; doubles as the protonation-feature tie-in) |
| — | `edit.prompt` | structural stub, no claims | **VERDICT: NO CHANGE** — keep `PLACEHOLDER_PHASE7_EDIT`; stub labels untouched (runtime bypasses via EditRouter; research OQ#8) |

## Per-source VERDICTs (plan 07-05 lands these records)

### APPROVED (~15 new records)

| source_id | VERDICT | Notes |
|-----------|---------|-------|
| `LIBRETEXTS-METAB-ETC` | **VERDICT: APPROVED** | Chemistry LibreTexts Catabolism/ETC page. CC BY-NC-SA 4.0. Verified live 2026-08-30 (+ 2026-08-15 anaerobic batch). Backs C1–C8, C10 (complex-level chemistry, carriers, PMF, chemiosmosis; NO yields, NO inhibitors) |
| `LIBRETEXTS-BIOCHEM-JF-CH19` | **VERDICT: APPROVED with landing-time condition** | Jakubowski & Flatt Vol. II Ch 19 (19.1 / 19.2 / 19.3) — same book as the already-approved LIBRETEXTS-METAB-TCA; CC BY-SA 4.0 volume-level (chapter page "not declared" — same metadata gap as approved Ch 16). Chapter + subpage descriptions fetched live 2026-08-30; subpage CONTENT confirm AT LANDING (plan 05) before ETC-UCP-01's UCP1 wording and ATP-SOUL-07's 19.2 wording land. Backs C9 (19.2), C1–C8 depth (19.1), ETC-UCP-01 (19.3) |
| `S-BIOX` | **VERDICT: RE-CONFIRMED (already approved Phase 5)** | Chemistry LibreTexts Biological Oxidation; re-fetched live 2026-08-30; backs BAD-HOST-01 (verbatim sentence) + O2-final-acceptor cross-refs |
| `PDB-5LDW` | **VERDICT: APPROVED** | Bovine respiratory Complex I, cryo-EM 4.27 Å, Zhu/Vinothkumar/Hirst 2016 (Nature 536:354–358, DOI 10.1038/nature19095, PMID 27509854). NDUFS8 = chain I. Cast text says "resolution 4.27 Å (cryo-EM)" |
| `PDB-1ZOY` | **VERDICT: APPROVED** | Porcine Complex II, X-ray 2.4 Å, Sun 2005 (Cell 121:1043–1057, DOI 10.1016/j.cell.2005.05.025, PMID 15989954). SDHA = chain A |
| `PDB-1BGY` | **VERDICT: APPROVED** | Bovine cytochrome bc1, X-ray 3.0 Å, Iwata 1998 (Science 281:64–71, DOI 10.1126/science.281.5373.64, PMID 9651245). CYC1 = chains D + P |
| `PDB-1OCC` | **VERDICT: APPROVED** | Bovine cytochrome c oxidase (fully oxidized), X-ray 2.8 Å, Tsukihara 1996 (Science 272:1136–1144, PMID 8638158). COX4I1 = chains D + Q; already loads in the skeleton |
| `PDB-1E79` | **VERDICT: APPROVED (first approval)** | Bovine F1-ATPase DCCD-inhibited, X-ray 2.4 Å, Gibbons/Montgomery/Leslie/Walker 2000 (Nat Struct Biol 7:1055–1061, DOI 10.1038/80981, PMID 11062563). NOT rat liver (task-brief assumption corrected). DCCD caveat = teaching beat per Decision 2 |
| UniProt O00217 / P31040 / P08574 / P13073 | **VERDICT: APPROVED (4 records)** | Variant + disease annotation layer for the DIS-* claims; CC BY 4.0; all fetched live 2026-08-30 (REST API). P13073 confirmed as COX4I1; "P10515" rejected as a task-brief artifact |
| ClinVar VCV000007512 / VCV000008742 / VCV000066019 / VCV000066020 / VCV000834063 | **VERDICT: APPROVED (5 records)** | Pathogenicity tiering for the DIS-* claims; fetched live 2026-08-30 (E-utilities) |
| PubMed 9837812 / 7550341 / 23910460 / 31290619 (+ 27509854 / 15989954 / 9651245 / 8638158 / 11062563 / 8065448) | **VERDICT: APPROVED** | Discovery papers + PDB primary citations; all fetched live 2026-08-30 (E-utilities) |

### REJECTED (retained with provenance — LEHNINGER precedent)

| source_id | VERDICT | Provenance |
|-----------|---------|------------|
| `LIBRETEXTS-METAB-ETC-II` | **VERDICT: REJECTED** | Chemistry LibreTexts "Electron Transport Chain II". **Why rejected:** states OUTDATED stoichiometry — "three ATP" per NADH and "an ATP for every two hydrogen ions" (the deprecated pre-1978 3/2 P/O values) — and does NOT cover the F0F1 rotary mechanism. Everything it offers beyond that is covered by `LIBRETEXTS-METAB-ETC` + J&F Ch 19. **Constraint:** it must NEVER source a numeric-yield claim (Decision 8 bans those anyway); plan 07-05 records approval_status="rejected" + this provenance note in sources.json — do NOT delete the record |

### DOCUMENTED, NOT-V1 (upgrade path only — no v1 source records required)

| item | VERDICT |
|------|---------|
| `PDB-5XTD` (human CI, EM 3.7 Å, Guo 2017) | **VERDICT: documented not-v1** — human-purist upgrade path; swapping would invalidate the verified NDUFS8 mapping |
| `PDB-9HZL` (human bc1, EM 2.52 Å, Nguyen 2026) | **VERDICT: documented not-v1** — upgrade path; CYC1 chains H/U re-verification owed if ever swapped |
| `PDB-9I6F` (human CIV HIGD2A-bound, EM 2.95 Å, Nguyen 2026) | **VERDICT: documented not-v1** — assembly/maturation-state nuance complicates the cast description |
| `7QSK` (bovine CI + Q10, EM 2.84 Å, Chung 2022) | **VERDICT: documented optional upgrade** — corrects the task brief's "human complex I 7QSK?" guess (it is BOVINE); only mammalian CI with the Q10 substrate in site |
| `PDB-1BMF` (bovine F1, 2.85 Å, Abrahams 1994) | **VERDICT: documented alternative, not selected** — Decision 2 kept 1E79; 1BMF's three β nucleotide states remain the binding-change visual upgrade if the human ever revisits |
| `PDB-1ZP0` (SDH + 3-NP + TTFA) | **VERDICT: existence anchor verified; MEDIUM until individually fetched** — landing-time metadata fetch; backs BAD-INHIB-01's structural anchor |

### UNVERIFIED — DO NOT CITE (claims stay pending, text stays generic)

| candidate | VERDICT |
|-----------|---------|
| J&F Unit I protein-folding / denaturation subpages; or a LibreTexts protein-denaturation page | **VERDICT: NOT VERIFIED — no approval** (research OQ#2). BAD-MISFOLD-01 / BAD-AGGREG-01 / BAD-PH-01 stay PENDING; their texts stay generic until these sources verify at landing |

## Citation corrections to land (research §9 #9 — part of Decision 9)

- **Gaignard 2013 (PMID 23910460):** correct to *Am J Hum Genet* **93(2):384–389**, DOI 10.1016/j.ajhg.2013.06.015 (05.1's "93(4):704–709" is wrong).
- **Pillai 2019 (PMID 31290619):** correct to *Am J Med Genet A* **179(10):2138–2143**, title ending "...developmental regression, intellectual disability, and seizures" (05.1's "179(10):1950–1956" + different title are wrong).
- Loeffen 1998 (63(6):1598–1608, DOI 10.1086/302154) and Bourgeron 1995 (11(2):144–9, DOI 10.1038/ng1095-144) verified correct — no change.
- The 05.1 research file is a planning artifact: annotate, do NOT rewrite history. Plan 07-05 lands the corrected numbers in `data/citations.json`.

## Anti-confusion binding (mandatory for every downstream ETC/ending text)

- **Electrons = the soul** → NADH/FADH2 → ETC → ATP synthase → ATP. **The carbon body is shed as CO2** (PDH + TCA decarboxylations).
- **NEVER** state or imply that the C14 carbon becomes ATP, enters oxidative phosphorylation, or becomes NADH. Electrons ≠ carbon.
- `end.true`'s dramatic text: with the soul-POV reading ("you" = the soul) the skeleton's "you are ATP" is defensible but borderline — research §9 #10 (final wording choice) was NOT one of this batch's 9 items and remains an authoring-time decision for the text plan, with the explicit-soul phrasing ("YOU are the spark within the ATP — your electrons now power the cell; your carbon body was shed as CO2") recommended and the MANDATORY 5.4 §3.6 teaching template ("Your carbon body is released as CO2; your electrons (the narrative 'soul') are carried by NADH/FADH2 to the ETC, which powers ATP synthase...") landing in teaching text regardless.

## Downstream implementation obligations (who implements what)

| Plan | Implements |
|------|-----------|
| **07-05** (registry landing) | Land ALL verdicts above in `data/citations.json` + `data/sources.json` (sole-writer rule): approved claims flip to "approved" keeping -cand ids verbatim; high-stakes claims (ATP-SOUL-07/08/09) get review_notes evidence trails; PDB claims get pdb_id/resolution_angstrom; ~15 new source records; retain the ETC-II rejection with provenance; land the Gaignard/Pillai citation corrections; run the landing-time subpage confirms (J&F 19.3 UCP1 coverage; 19.2 binding-change wording) BEFORE finalizing ETC-UCP-01 / ATP-SOUL-07 wordings; document gate residuals per placeholder bucket |
| **07-09** (ETC content) | complex_ii/iii promotion (1ZOY + 1BGY loads + pre-edit/mutant-flag MolActions); L215F text + restoration signature (`resi 131 and chain D` / `new_res LEU`); COX4I1 PDB-numbering signature + P152T teaching bridge; Template-3 restore reveals + the HEADLESS restore-handle verification (op="restore" returns the WT backup — research OQ#4); 1E79 DCCD teaching beat; 5LDW cryo-EM note; species-honesty line (bovine/porcine structures, human disease genetics); etc.entry "let go" relabel to the uncoupling framing |
| **07-10/11** (endings + bad-pool text) | end.normal.co2 uncoupling framing (ETC-UCP-01; delete the resolved NARRATIVE-FRAMING FLAG); end.true anti-confusion template; bad-pool texts per the 14 mapping VERDICTs (generic where pending); proton-leak text says PROTONS; no numeric yields; no ROS claims |
| **07-14** (edits.json) | The 4 ETC known-edit signatures per Decisions 3/4 + research §4.6 formats (complex_i `resi 68 chain I ARG`; complex_ii `resi 512 chain A ARG`; complex_iii `resi 131 chain D LEU`; complex_iv `resi 130 chain D PRO`) |

## Verification

- **Full test suite:** `python3.6 -m unittest discover -s tests` → **Ran 324 tests — OK** (matches the 07-05 baseline; zero regression).
- **Registry untouched (verified):** `data/citations.json` + `data/sources.json` contain no LIBRETEXTS-BIOCHEM-JF-CH19 / ETC-UCP-01 / ETC-CI-01 / BAD-HOST-01 entries; registry currently holds only the 5 first-batch claims (GLY-PFK-01, TCA-RNG-WEIGHT-01, TCA-RNG-CITRATE-PROCHIRALITY-01, CAST-PFK-PDB-01, CAST-CSC-PDB-01). Plan 07-05 is the sole writer that lands batch outcomes.
- **Ledger greps (plan's verification):** `grep -c "VERDICT\|Outcome"` → 40+ (all 9 decisions carry Outcome lines; every claim/source carries a VERDICT line); `grep "no numeric"` → present (P/O rule recorded).
- **Working tree:** clean before this commit — the checkpoint agent's read-only verification made no changes; no code, story JSON, edits.json, cast.json, or registry files touched.

## Deviations from Plan

None - plan executed exactly as written. (The plan is a single checkpoint:decision task; the human answered "All 9 defaults"; verdicts recorded; no code touched — by design, registry landing is plan 07-05.)

## Issues Encountered

- None blocking. Notes: (a) research §9 #10 (`end.true` final wording) was not among the batch's 9 resume-signal items and remains an authoring-time decision — recorded above, not silently resolved; (b) research open questions #5 (species narrative consistency), #7 (collapse-vs-aggregate text differentiation), #8 (edit.prompt stub labels) are authoring-time notes carried to plans 09/10/11, not batch decisions.

## Next Phase Readiness

- Batch C verdicts are COMPLETE and machine-greppable (Outcome/VERDICT lines) — plan 07-05 can land the registry as soon as its batch-A/B dependencies (07-02/07-03 summaries) exist.
- ETC framing rules are LOCKED before any text authoring: no numeric P/O yields anywhere; no ROS claims in v1; proton-leak text says PROTONS; anti-confusion binding on every ETC/ending node.
- All landing-time conditions are explicit: J&F 19.3 subpage confirm (ETC-UCP-01), 19.2 subpage confirm (ATP-SOUL-07 wording), 1ZP0 individual fetch (BAD-INHIB-01 anchor), BAD-MISFOLD/AGGREG/PH source verification — none block the other wave-2/3 plans from drafting against generic text.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-01*
