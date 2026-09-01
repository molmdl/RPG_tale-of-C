---
phase: 07-content-expansion-i-glucose
plan: 02
subsystem: citations
tags: [citation-gate, approval-ledger, glycolysis, pyruvate, no-fabricated-science, clinvar, uniprot, rcsb-pdb, pubchem, libretexts]

# Dependency graph
requires:
  - phase: 07-content-expansion-i-glucose (research)
    provides: 07-RESEARCH-glycolysis-pyruvate.md — all sources fetched live 2026-08-30, candidate claims with verbatim anchors
  - phase: 07-content-expansion-i-glucose (plan 07-02 prep)
    provides: 07-02-APPROVAL-BATCH-A.md (commit ec2b3e8) — the batch material presented to the human
provides:
  - "Approval batch A ledger: per-source + per-claim human verdicts for glycolysis + pyruvate branch (22 claims APPROVED, 1 contingent DEFERRED, 1 source REJECTED with provenance)"
  - "6 recorded framing-decision outcomes (PFKM text-only fallback; PKLR 7FS3+2VGG; PDHA1 applyEdit-on-6CFO; ethanolic yeast-counterfactual; 5W8J keep+name inhibitor; claims approve-all with AN-G-02 softened)"
  - "OQ-C contingent-claim disposition (INTRO-CAST-20AA-01 deferred to Phase 9 per 07-01 decision #6)"
  - "Complete verdict inputs for plan 05 (registry landing) and plans 06/07/08/14 (content authoring)"
affects: [07-05 (registry landing), 07-06, 07-07, 07-08, 07-14 (content plans), phase-9 (deferred 20-AA cast)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Approval-ledger pattern: checkpoint decisions recorded as per-item VERDICT lines in the plan SUMMARY; registry landing is a separate downstream plan (05)"
    - "-cand claim ids KEPT verbatim on approval (only approval_status flips) — tests pin ids (tests/test_glucose_reachability.py:339-351)"
    - "Rejections recorded with provenance, never silently deleted (LEHNINGER precedent; R1 LIBRETEXTS-CATAB-PYRUVATE-DH)"

key-files:
  created:
    - ".planning/phases/07-content-expansion-i-glucose/07-02-SUMMARY.md (this ledger)"
  modified: []

key-decisions:
  - "Human verdict (verbatim): '1: approve-all; 2-6: all defaults' — all 22 actionable batch-A claims approved as presented (AN-G-02 in the flagged default softened wording); DIS-PFKM-01-cand pinned to 'Likely pathogenic'"
  - "DC-2/DC-3 PFKM: text-only disease fallback (default) — no on-structure alter at an unsourced bacterial residue in 4PFK; G209D stays featured in teaching text"
  - "DC-4 PKLR cast: 7FS3 (1.66 A L-type) + 2VGG mutant-PDB approach for the restoration arc (default)"
  - "DC-5 PDHA1: applyEdit on 6CFO (default option-a); 6CER approved but unused this phase"
  - "OQ1 ethanolic: yeast-counterfactual teaching moment (default) — zero topology change, 21 endings preserved"
  - "OQ-E 5W8J: keep + teaching text names the bound inhibitor (default)"
  - "OQ-C contingent claim INTRO-CAST-20AA-01: DEFERRED — real 20-AA cast deferred to Phase 9 per 07-01 decision #6; _smoke.pdb fixture stays through Phase 7"
  - "R1 LIBRETEXTS-CATAB-PYRUVAATE-DH: REJECTED as claim source (stub page) — recorded with provenance"

patterns-established:
  - "Per-claim VERDICT lines are the machine-greppable approval record (plan verification: grep -c VERDICT covers every claim + 6 decisions)"

# Metrics
duration: 12min
completed: 2026-09-01
---

# Phase 7 Plan 02: Approval Batch A (Glycolysis + Pyruvate) Summary

**Approval ledger for glycolysis + pyruvate-branch science: human verdicts "1: approve-all; 2-6: all defaults" recorded per-source (15) and per-claim (23), 6 framing decisions resolved to defaults, 1 source rejected with provenance — registry still UNTOUCHED (plan 05 lands it).**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-01T02:43:16Z
- **Completed:** 2026-09-01T02:55Z
- **Tasks:** 1 of 1 (checkpoint:decision — human verdicts received and recorded)
- **Files modified:** 2 (this SUMMARY + STATE.md note)

## Accomplishments
- Every batch-A candidate source (15) and claim (23) now has a recorded human verdict — nothing rests on unapproved science.
- The 6 framing decisions (DC-2/DC-3 PFKM, DC-4 PKLR, DC-5 PDHA1, OQ1 ethanolic, OQ-E 5W8J) resolved to defaults with exact consequences recorded for downstream plans.
- The OQ-C-contingent claim is dispositioned against 07-01 decision #6 (defer real cast to Phase 9) rather than silently dropped.
- Pre-verified rejection R1 recorded with provenance (LEHNINGER precedent).
- Gates: 324 unit tests green; registry files untouched (verified via git status — landing is plan 05's job).

## Task Commits

1. **Task 1: Present + record batch A approvals and decisions** — batch material committed by the previous run at `ec2b3e8` (docs(07-02): assemble approval batch A material); verdicts recorded in this SUMMARY + committed as `docs(07-02): record batch-A approval verdicts` (single docs commit per the continuation objective — planning docs only).

---

# APPROVAL LEDGER — Batch A: Glycolysis + Pyruvate Branch

## Human verdicts (verbatim)

> **"1: approve-all; 2-6: all defaults"**

Orchestrator expansion of item 1 (binding): **APPROVE ALL as presented** — 20 core + the 4 optional/conditional as flagged; **DIS-PFKM-01-cand stays pinned to "Likely pathogenic"**; **AN-G-02 softened wording** per the flagged default (option ii); **the OQ-C-contingent claim resolves per 07-01 decision #6 = defer real cast to Phase 9** → contingent disposition recorded below.

Items 2–6 = defaults: (2) PFKM text-only fallback; (3) PKLR 7FS3 + 2VGG mutant approach; (4) PDHA1 applyEdit on 6CFO; (5) OQ1 ethanolic yeast-counterfactual; (6) 5W8J keep + name inhibitor.

Not re-fetched per the human's silence on the offer: RCSB/UniProt/ClinVar/PubChem records (verified live 2026-08-30 by the research session); abstracts for the S12 PubMed cite-only set not fetched. The 5 approval-time re-fetches performed 2026-09-01 (batch doc Part 5) stand as the verification record.

---

## Part 1 — Source verdicts (15 + 1 rejection)

- **VERDICT S1 `LIBRETEXTS-CATAB-GLYCOLYSIS`** — APPROVED (new source). CC BY-NC-SA 4.0; fetched live 2026-08-30 AND re-fetched 2026-09-01. Grounds GLY-INTRO-01, GLY-HXK-01, GLY-TRIOSE-01, GLY-PKM-01, AN-G-01.
- **VERDICT S2 `LIBRETEXTS-CATAB-FERMENTATION`** — APPROVED (new source). CC BY-NC-SA 4.0; fetched live 2026-08-30 AND re-fetched 2026-09-01. Grounds AN-G-02, AN-G-03, AN-G-04, AN-G-05, AN-ANAER-DEF-01 (opt); load-bearing evidence for Decision 5 (OQ1).
- **VERDICT S3 `LIBRETEXTS-CATAB-BIOOX`** — RE-CONFIRMED (approved in Phase 5; re-fetched live 2026-09-01). Co-grounds AN-ETC-02.
- **VERDICT S4 `LIBRETEXTS-CATAB-ETC`** — RE-CONFIRMED (approved in Phase 5; re-fetched live 2026-09-01). Co-grounds AN-ETC-02.
- **VERDICT S5 `LIBRETEXTS-METAB-TCA` §16.01 pointer** — APPROVED (new section pointer on the ALREADY-APPROVED source; 16.02 precedent). Volume CC BY-SA 4.0; subpage fetched live 2026-09-01; grounding uses ONLY the Jakubowski/Flatt body text, never the "(written by Claude...)" Learning-Goals/Summary boxes. Grounds PYR-PDH-01; body embeds 6CFO (corroborates claim #4).
- **VERDICT S6 `UNIPROT-P08237`** — APPROVED (new source). CC BY 4.0; REST fetched live 2026-08-30. Grounds DIS-PFKM-01-cand (VAR_006066 G209D).
- **VERDICT S7 `UNIPROT-P30613`** — APPROVED (new source). CC BY 4.0; REST fetched live 2026-08-30. Grounds DIS-PKLR-01-cand (VAR_011480 R479H).
- **VERDICT S8 `UNIPROT-P08559`** — APPROVED (new source). CC BY 4.0; REST fetched live 2026-08-30. Grounds DIS-PDHA1-01-cand (VAR_004952 V167M).
- **VERDICT S9 `CLINVAR-VCV003375341`** — APPROVED (new source). Public domain; E-utilities fetched live 2026-08-30. Classification: **"Likely pathogenic"** (NOT Pathogenic).
- **VERDICT S10 `CLINVAR-VCV000001510`** — APPROVED (new source). Public domain; fetched live 2026-08-30. Classification: **"Pathogenic"**, multiple submitters, no conflicts.
- **VERDICT S11 `CLINVAR-VCV000985548`** — APPROVED (new source). Public domain; fetched live 2026-08-30. Classification: **"Pathogenic/Likely pathogenic"**.
- **VERDICT S12 PubMed cite-only set** (7825568 Raben 1995, 8161798 Kanno 1994, 11960989 Valentini 2002, 29970614 Whitley 2018, 8504306 Chun 1993, 36753880 Nain-Perez 2023, 29120638 Rai 2017) — APPROVED (new sources, bibliographic records). Cross-ref-verified 2026-08-30; abstracts NOT fetched (human did not request; cite-only role unchanged).
- **VERDICT S13 `PDB-7FS3`, `PDB-2VGB`, `PDB-2VGG`, `PDB-6CFO`, `PDB-6CER`, `PDB-5W8J`** — APPROVED (new sources). CC0 / PDB usage policy; RCSB data API fetched live 2026-08-30. Note: 1LIY is REMOVED from RCSB — 2VGG is the current R479H-mutant ID. (2VGB and 6CER approved as sources; per-claim dispositions below govern whether their claims are consumed.)
- **VERDICT S14 `PUBCHEM-CID-5793`** — APPROVED (new source). Public domain; PUG REST fetched live 2026-08-30. Grounds CAST-GLC-PUBCHEM-01.
- **VERDICT S15 `PUBCHEM-CID-1060`** (OPTIONAL) — APPROVED (new source) as part of approve-all covering optional claim #23; pyruvic-acid neutral-acid-vs-physiological-anion nuance must be stated in text if ever consumed. Not in the 07-02 plan roster.
- **VERDICT R1 `LIBRETEXTS-CATAB-PYRUVATE-DH`** — **REJECTED as claim source** (pre-verified; human did not override). Provenance: the LibreTexts Catabolism "Pyruvate Dehydrogenase Complex" page is a STUB (one Wikipedia figure, empty references) — fetched live 2026-08-30, unusable for PYR-PDH-01. Recorded so future researchers don't re-fetch it. PYR-PDH-01 routes to the approved book instead (S5 §16.01). Same pattern as the LEHNINGER rejection — rejected sources keep provenance, are not deleted.

Already approved and NOT re-decided here: `LIBRETEXTS-METAB-GLYCOLYSIS`, `LIBRETEXTS-METAB-TCA`, `PDB-4PFK`, `PDB-1CSC`; claims `GLY-PFK-01`, `CAST-PFK-PDB-01`, `TCA-RNG-WEIGHT-01`, `TCA-RNG-CITRATE-PROCHIRALITY-01`, `CAST-CSC-PDB-01`.

---

## Part 2 — Claim verdicts (23 enumerated: #1–#23)

> **Count note (ledger clarification):** the batch doc's Part 3 tally ("20 core + 2 optional + 2 conditional + 1 contingent = 25") contains an arithmetic slip — only 23 claims are enumerated (#1–#23). Accurate tally: **18 core + 2 conditional (#5, #7) + 2 optional (#19, #23) + 1 contingent (#10) = 23**. The enumerated claims govern; every one has a VERDICT below. Net result: **22 APPROVED, 1 contingent DEFERRED (not approvable this batch).**

### A. Disease-mutant claims (3)

- **VERDICT #1 `DIS-PFKM-01-cand`** — **APPROVED as presented** (pinned wording). claim_text: "PFKM G209D abolishes PFK-1 activity in yeast-complementation assays (Raben 1995) and is classified **Likely pathogenic** in ClinVar (VCV003375341) for Glycogen Storage Disease VII / Tarui disease (MIM:232800)." ⚠️ Do NOT upgrade to "pathogenic" (S9 classification is Likely pathogenic). Sources S6 + S9 + Raben 1995. Mechanics: missense → cmd.alter compatible; reverse fix D209G; residue 209 is HUMAN numbering, 4PFK is bacterial — no sourced mapping (Decision 2 = text-only).
- **VERDICT #2 `DIS-PKLR-01-cand`** — **APPROVED as presented**. claim_text: "PKLR R479H is classified Pathogenic in ClinVar (VCV000001510) for chronic nonspherocytic hemolytic anemia type 2 / pyruvate kinase deficiency (MIM:266200); the variant is annotated in the Amish population, and UniProt notes it causes no conformational change (VAR_011480; Valentini 2002)." Sources S7 + S10 + Valentini 2002 / Kanno 1994. Mechanics: missense; reverse fix H479R; resi 479 exists in 7FS3/2VGB/2VGG numbering (no offset).
- **VERDICT #3 `DIS-PDHA1-01-cand`** — **APPROVED as presented**. claim_text: "PDHA1 V138M (mature numbering; V167M in the UniProt precursor including the 29-residue mitochondrial transit peptide) is classified Pathogenic/Likely pathogenic in ClinVar (VCV000985548); it disrupts magnesium binding and results in deficient activity of the pyruvate dehydrogenase complex (UniProt VAR_004952; Whitley 2018), causing PDH deficiency (MIM:312170, X-linked)." Sources S8 + S11 + Whitley 2018 / Chun 1993. Mechanics: missense; reverse fix M138V in **PDB/mature numbering (resi 138)**; player-facing text shows PDB resi 138 and teaches the V167M literature alias.

### B. Cast-structure claims (4 core + 2 conditional + 1 intro)

- **VERDICT #4 `CAST-PDH-WT-PDB-01-cand`** — **APPROVED as presented** (consumed). claim_text: "The game's PDH E1 wild-type cast structure is RCSB PDB 6CFO (2.70 Å, human PDHA1 E1 heterotetramer with the covalent TDP-acetyl-phosphinate analog + Mg²⁺; Whitley 2018, PubMed 29970614, DOI 10.1074/jbc.RA118.003996)." Corroborated by §16.01 body embedding 6CFO.
- **VERDICT #5 `CAST-PDH-MUTANT-PDB-01-cand`** (conditional) — **APPROVED as presented; DORMANT this phase**. claim_text: "The V138M mutant reference structure is RCSB PDB 6CER (2.69 Å, human PDH E1 V138M mutation, same Whitley 2018 paper; ligands TPP + Mg²⁺)." Decision 4 chose the default option (a) applyEdit on 6CFO, so 6CER is NOT consumed by any plan this phase; the approval stands recorded (status may flip in plan 05) so a later phase could adopt option-b without re-approval.
- **VERDICT #6 `CAST-PKLR-PDB-01`** — **APPROVED in the 7FS3 variant** (Decision 3 default). claim_text: "The game's pyruvate kinase cast structure is RCSB PDB 7FS3 (1.66 Å, human PKLR L-type in complex with allosteric modulator 15, oxalate, Mg²⁺, K⁺; Nain-Perez 2023, PubMed 36753880)." The 2VGB variant wording is NOT selected (2VGB remains an approved source only). Required teaching note: 7FS3 is L-type (liver) while the disease is RBC — one honest line.
- **VERDICT #7 `CAST-PKLR-MUTANT-PDB-01`** (conditional) — **APPROVED as presented; CONSUMED** (Decision 3 default adopts the 2VGG approach). claim_text: "The R479H mutant reference structure is RCSB PDB 2VGG (2.74 Å, 'Human erythrocyte pyruvate kinase: R479H mutant', Valentini 2002; keywords include 'DISEASE MUTATION'; the old ID 1LIY is superseded/removed — 2VGG is current)."
- **VERDICT #8 `CAST-LDH-PDB-01`** — **APPROVED as presented** (Decision 6 default governs presentation). claim_text: "The game's LDH cast structure is RCSB PDB 5W8J (1.55 Å, human LDHA wild-type in complex with inhibitor compound 29; Rai 2017, PubMed 29120638, DOI 10.1021/acs.jmedchem.7b00941)."
- **VERDICT #9 `CAST-GLC-PUBCHEM-01`** — **APPROVED as presented** (consumed; unblocks gly.start show_as glucose). claim_text: "The game's glucose model is PubChem CID 5793 (D-glucose, C6H12O6, MW 180.16, 3D conformer; IUPAC (3R,4S,5S,6R)-6-(hydroxymethyl)oxane-2,3,4,5-tetrol — the oxane ring is the pyranose ring form)."
- **VERDICT #10 `INTRO-CAST-20AA-01`** — **CONTINGENT — DEFERRED (NOT approved this batch; not authored this phase).** Disposition: the 20-AA cast structure has NO source (still the bundled `_smoke.pdb` fixture). Per **07-01 decision #6** (OQ-C 20-AA cast: **defer real cast structure to Phase 9; keep bundled _smoke.pdb fixture through Phase 7**), this claim is simply not authored this phase. Listed so the ledger is complete. Phase 9 must source + approve a real peptide structure before INTRO-CAST-20AA-01 can exist.

### C. Routine pathway claims (11 core + 1 optional + 1 optional-roster)

- **VERDICT #11 `GLY-INTRO-01`** — **APPROVED as presented** (source S1). "Glycolysis converts one glucose into two pyruvates via ten enzymatic steps: a 2-ATP-investment priming phase and a 4-ATP-yield payoff phase (net 2 ATP + 2 NADH)." Verbatim anchors re-fetched 09-01 (batch doc #11).
- **VERDICT #12 `GLY-HXK-01`** — **APPROVED as presented** (source S1). "Hexokinase catalyzes glycolysis step 1: glucose + ATP → glucose-6-phosphate + ADP; the step is inhibited by its product G6P (product inhibition)." Verbatim anchors (batch doc #12).
- **VERDICT #13 `GLY-TRIOSE-01`** — **APPROVED as presented** (source S1). "Steps 4–9: aldolase cleaves FBP into DHAP + G3P; TPI equilibrates DHAP→G3P; GAPDH oxidizes G3P to 1,3-BPG (producing NADH); PGK and PK make ATP by substrate-level phosphorylation; PGAM + enolase prepare PEP." Includes the OQ-G text-accuracy obligation: Phase 7 text fixes the skeleton's ambiguous "Net so far: 2 ATP, 2 NADH" placeholder (after step 9 the account is 2 ATP invested + 2 ATP recovered + 2 NADH banked; the 2nd substrate-level ATP lands at PK).
- **VERDICT #14 `GLY-PKM-01`** — **APPROVED as presented** (source S1). "Pyruvate kinase catalyzes glycolysis step 10: PEP + ADP → pyruvate + ATP (the second substrate-level phosphorylation); allosterically inhibited by high-energy signals (ATP, acetyl-CoA, alanine, cAMP)."
- **VERDICT #15 `AN-G-01`** — **APPROVED as presented** (source S1; "via PDH" clause grounded on S5 §16.01). "Glycolysis ends at pyruvate; pyruvate's fate depends on oxygen: aerobically it feeds the TCA cycle (via PDH), anaerobically it is reduced to lactate or ethanol (fermentation)."
- **VERDICT #16 `AN-G-05`** — **APPROVED as presented** (source S2; also the load-bearing evidence for Decision 5). "Lactic fermentation occurs in oxygen-depleted muscle (and some bacteria); ethanolic fermentation occurs in yeast."
- **VERDICT #17 `PYR-PDH-01`** — **APPROVED as presented** (source S5 — approved book, new §16.01 pointer; exact §16.01 sentences quoted in batch doc #17, fetched live 2026-09-01). "The pyruvate dehydrogenase complex catalyzes the oxidative decarboxylation of pyruvate to acetyl-CoA (releasing CO2 and generating NADH), the committed entry of carbon into the citric acid cycle." Teaching bonus (same page body): TPP is one of the five vitamin-derived cofactors — supports the "violet cofactor cradle" note for 6CFO's TDP-analog + Mg²⁺.
- **VERDICT #18 `AN-G-04`** — **APPROVED as presented** (source S2). "Fermentation recycles NAD+ (from NADH) so glycolysis can continue; its energy yield is much less than TCA + ETC."
- **VERDICT #19 `AN-ANAER-DEF-01`** (OPTIONAL) — **APPROVED as presented** (source S2). "Fermentation recycles NAD+ without an electron-transport chain; anaerobic respiration instead uses a non-oxygen terminal electron acceptor (e.g. nitrate, sulfur, metals) with an ETC." Consumable by plan 07 (anaerobic branch text).
- **VERDICT #20 `AN-G-02`** — **APPROVED in the SOFTENED wording** (flag default (ii) — airtight on the quoted text). Approved claim_text: "In the absence of oxygen, pyruvate is reduced to lactate by lactate dehydrogenase, with NADH as the reducing agent; NAD+ is regenerated; **its carbon is retained in lactate (no decarboxylation step occurs)**. This is the mammalian (muscle) fermentation." The original "no CO2 is released" clause is REPLACED by the softened clause (it was implied-by-reaction, not verbatim on S2/S3). Nodes: anaer.ldh + anaer.lactic.
- **VERDICT #21 `AN-G-03`** — **APPROVED as presented** (source S2; framing = Decision 5 default). "In yeast (not mammals), pyruvate is converted to acetaldehyde with release of CO2 by pyruvate decarboxylase; acetaldehyde is then reduced to ethanol by alcohol dehydrogenase, regenerating NAD+."
- **VERDICT #22 `AN-ETC-02`** — **APPROVED as presented** (sources S3 + S4 + S2). "Without oxygen the electron transport chain stalls (no terminal electron acceptor), oxidative phosphorylation cannot produce ATP, and the proton-motive force collapses; fermentation regenerates NAD+ but yields far less ATP." Verbatim anchors quoted in batch doc #22.
- **VERDICT #23 `CAST-PYR-PUBCHEM-01`** (OPTIONAL, not in the plan roster) — **APPROVED as presented** (source S15, CID 1060 pyruvic acid; the neutral-acid-vs-physiological-anion nuance must be stated in text if consumed). No phase consumes it unless a later plan opts in; approval recorded so it needs no re-approval later.

---

## Part 3 — The 6 decision outcomes (verbatim human reply; all defaults)

- **VERDICT Decision 1 — Claims verdict: "approve-all"** — every enumerated Part-2 claim approved exactly as presented/worded, with the two flagged resolutions applied inline: DIS-PFKM-01-cand pinned to "Likely pathogenic" (never upgraded), and AN-G-02 recorded in the softened (ii) wording. Per-claim rejections: none.
- **VERDICT Decision 2 — DC-2/DC-3 PFKM featured mutant + cast/mutation reconciliation: text-only disease fallback (default).** No on-structure alter at an unsourced bacterial residue (human G209D is numbered on human PFKM; approved cast 4PFK is bacterial, residue 209 does not exist there; no sequence-alignment source exists — OQ-B; 4OMT is 6.0 Å). Consequences: PFK keeps its restoration ARC as narrative only; G209D stays the featured mutant, carried in teaching text with the "Likely pathogenic" wording; NO new alignment-sourcing claim/task is opened; cast stays 4PFK (no 4OMT switch, no re-approval of CAST-PFK-PDB-01). PROJECT.md row 109 cap honored — PDH is the strongest restoration-arc candidate (real 6CFO/6CER geometry), so PFK text-only costs little.
- **VERDICT Decision 3 — DC-4 PKLR cast + restoration approach: 7FS3 + 2VGG mutant approach (default).** Cast = 7FS3 (1.66 Å L-type, modulator 15 + oxalate + Mg²⁺ + K⁺ — best resolution, active-site ligands visible; approves claim #6 7FS3 wording). Restoration arc uses the real R479H mutant structure 2VGG (approves claim #7; mirrors the PDH pattern). Required teaching line: 7FS3 is L-type (liver) vs the RBC disease tissue. 2VGB NOT selected (source S13 approved; #6 2VGB variant wording unused).
- **VERDICT Decision 4 — DC-5 PDHA1 restoration approach (OQ-DM2): option (a) applyEdit on 6CFO (default).** Approximate geometry via cmd.alter, consistent with the other enzymes. Claim #5 (6CER) is approved but UNUSED this phase. (Option (b) — load 6CER real-mutant geometry — not chosen.)
- **VERDICT Decision 5 — OQ1 ethanolic-fermentation framing in a mammalian host: (b) yeast-counterfactual teaching moment (default).** ZERO topology change (the frozen 55-node / 21-ending skeleton is untouched; anaer.ethanolic Normal-tier ending stays). Dramatic layer shows the alternate road ("in another host — a yeast cell…"); teaching layer states the real yeast chemistry (PDC releases CO2, ADH → ethanol, NAD+ regenerated) and honestly says the mammalian host does not run this path. Grounded: AN-G-03 + AN-G-05. (Alt (a) drop-node — would reverse the recorded 05.1-06 approval and change topology to 20 endings — NOT chosen. Alt (c) host variation — contradicts PROJECT.md row 97 Host=mammal — NOT chosen.)
- **VERDICT Decision 6 — OQ-E 5W8J inhibitor caveat: keep 5W8J + teaching text names the bound inhibitor (default).** 5W8J stays the LDH cast; teaching text names the bound research inhibitor ("a research inhibitor sits in the very pocket lactate would occupy"). (Alt: another LDH structure — would need a new verification pass — NOT chosen. Alt: hide/remove ligand via MolActions at on_enter — NOT chosen.)

---

## Part 4 — OQ-C contingent-claim disposition (cross-reference to 07-01)

**INTRO-CAST-20AA-01 (#10): DEFERRED — not approved, not authored this phase.**

- The claim resolves per **07-01 decision #6** (OQ-C 20-AA cast): **defer the real cast structure to Phase 9; keep the bundled `_smoke.pdb` fixture through Phase 7.**
- Rationale: the 20-AA cast has NO source — it is still the `_smoke.pdb` fixture — so there is nothing approvable in this batch (no-fabricated-science gate).
- Consequence for downstream plans: plans 06/07/08/14 author NO 20-AA cast claim; `intro.shell_glucose` keeps the fixture. Phase 9 owns sourcing + approving a real peptide structure, at which point INTRO-CAST-20AA-01 (or its successor id) enters a future approval batch.

---

## Part 5 — Disposition summary for downstream plans

**For plan 05 (registry landing — `data/citations.json` + `data/sources.json`):**
- Flip `approval_status` → `approved` for the 22 approved claims, KEEPING their `-cand` ids verbatim (tests pin them: tests/test_glucose_reachability.py:339-351). New claims born with bare ids (#6 7FS3 variant, #7, #8, #9, #11–#18, #20–#23 minus -cand holders).
- Land the 13 new sources (S1, S2, S6–S14) + optional S15 + the S5 §16.01 section pointer; record S3/S4 as re-confirmed (already present).
- Record R1 `LIBRETEXTS-CATAB-PYRUVATE-DH` as REJECTED with the provenance text above (never delete).
- Dormant approvals (#5 6CER, #23, S15) land as approved — being approved-but-unused is fine; re-approval is what we avoid.
- Do NOT land anything for INTRO-CAST-20AA-01 (#10) — deferred to Phase 9 per 07-01 decision #6.

**For plans 06/07/08/14 (content authoring):** author text/edits ONLY for approved claims, honoring the 6 decision outcomes — esp. the PFKM text-only fallback (no alter at resi 209 on 4PFK), the PKLR 7FS3+2VGG pairing with the L-type-vs-RBC teaching line, PDHA1 applyEdit on 6CFO at resi 138 (teach the V167M alias), the ethanolic yeast-counterfactual framing, the 5W8J inhibitor naming, AN-G-02's softened carbon-retention wording, and the OQ-G "net so far" fix at gly.fbp_to_pyruvate.

## Verification (per plan)

- `grep -c "VERDICT"` on this file: covers every enumerated claim (#1–#23) + the 6 decisions + 15 sources + R1. ✓
- `grep "DIS-PFKM-01-cand"`: present with the "Likely pathogenic" pinned wording noted (VERDICT #1 + Decision 1 + Decision 2). ✓
- `python3.6 -m unittest discover -s tests`: **324 tests OK** (re-verified post-recording; verdicts change no code). ✓
- Registry untouched: `git status` clean for `data/citations.json` + `data/sources.json` — plan 05 lands entries. ✓

## Decisions Made

All 6 framing decisions resolved to the research/plan defaults per the human's reply (recorded verbatim in Part 3 above). No human-edited claim wording anywhere in the batch (the only wording change is the pre-flagged AN-G-02 default (ii) soften, which the human accepted by taking defaults).

## Deviations from Plan

**None — plan executed exactly as written.** One ledger clarification (not a deviation): the batch doc's Part 3 count summary overstates the claim total (25 vs 23 enumerated); the enumerated claims govern and all 23 carry VERDICT lines. The continuation objective merged the task commit and metadata commit into a single `docs(07-02)` commit (planning docs only) — followed as instructed.

## Issues Encountered

None. The checkpoint returned cleanly; the human answered all 6 items in one pass.

## Next Phase Readiness

- Plan 05 (registry landing) has complete, unambiguous inputs: 22 approved claims + 14 sources + 1 pointer + 1 rejection with provenance.
- Plans 06/07/08/14 can author content against recorded decision outcomes with zero re-litigation.
- Phase-9 follow-up owed: real 20-AA cast structure sourcing (INTRO-CAST-20AA-01 disposition).
- Blockers: none.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-01*
