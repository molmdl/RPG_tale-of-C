---
phase: 07-content-expansion-i-glucose
plan: 03
subsystem: citations-approval (batch B — TCA cycle + RNG shuffle + cataplerotic exits)
tags: [tca-cycle, rng-shuffle, carbon-fate, approval-ledger, citation-registry, succinate-symmetry, cataplerotic]

# Dependency graph
requires:
  - phase: 05-key-decisions
    provides: hybrid approval workflow (sources batch-approved, HIGH-STAKES claims individually reviewed, ROUTINE claims source-inherited) + registry schema (review_tier / inherits_source_approval / claim_text) + the -cand keep-ids policy
  - phase: 07 research
    provides: 07-RESEARCH-tca-rng.md (all candidates live-verified 2026-08-30; NOTHING pre-approved)
provides:
  - "Batch-B approval ledger: D1-D10 outcomes + per-claim VERDICTs (8 HIGH-STAKES + 12 ROUTINE) + per-source VERDICTs + 3 rejections with provenance"
  - "Design-B shuffle semantics approved (succinate-symmetry 50/50 re-anchor; weight VALUE 0.5/0.5 unchanged; topology unchanged)"
  - "OGDH promotion decision (D5): tca.akg_dh edit-allowed 14→15 — implemented by plan 13 exactly as recorded here"
  - "IDH 'rate-limiting' wording softened to 'a key regulatory step' (16.03 never fetched)"
affects: [plan 05 (registry landing), plan 10 (ending texts cite cataplerotic claims), plan 13 (TCA content + D5 test update), plan 14 (edits.json TCA buckets), plan 15 (cast TBD_ACONITASE resolution), plan 16 (seeded determinism per design B + count invariants)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Approval-ledger SUMMARY as the batch verdict record: Outcome lines (decisions) + VERDICT lines (claims/sources), consumed verbatim by the registry-landing plan"
    - "Conditional verdicts resolved by decision trigger: D1=B fires TCA-RNG-WEIGHT-02-cand + TCA-CARBON-FATE-01-cand; D5=promote fires DIS-OGDH-01-cand + PMID-36520152"

key-files:
  created:
    - ".planning/phases/07-content-expansion-i-glucose/07-03-SUMMARY.md"
  modified: []

key-decisions:
  - "D1 = design B: shuffle re-anchored to the succinate-symmetry 50/50 scramble; 0.5/0.5 value + topology stand"
  - "D2 = (a): TCA-RNG-CITRATE-PROCHIRALITY-01 stays approved; Wikipedia co-sources widen the claim's source set"
  - "D3 = 5GRE (WT αγ 2.65 Å) replaces 5GRF (γ-K151A mutant — rejected with provenance)"
  - "D4 = IDH3A reaffirmed (M204I default; R316C alternate)"
  - "D5 = PROMOTE tca.akg_dh to edit-allowed (14→15; invariant-test update owed in plan 13; single-submitter caveat kept in review_notes)"
  - "D6 = 1ACO bovine 2.05 Å aconitase cast (1C97 + 2B3Y rejected with provenance)"
  - "D7 = 1CSC AU monomer + teaching note (assembly load flagged, NOT implemented — no engine surgery)"
  - "D8 = 4WLU (malate + NAD⁺ bound, 2.14 Å) MDH2 cast"
  - "D9 = §9 source batch approved (16.04 scope extension; 16.03 NOT fetched → IDH wording softened)"
  - "D10 = cycle-trap N=5 confirmed (game-design parameter, not a science claim)"

patterns-established:
  - "Conditional-approval semantics: a source approved 'only if D5' becomes fully approved when the trigger fires — recorded, not re-asked"

# Metrics
duration: ~20 min (continuation bookkeeping session; read-only verification + verdict recording)
completed: 2026-09-01
---

# Phase 7 Plan 03: Approval Batch B — TCA + RNG Shuffle Summary

**All-defaults approval ledger recorded: shuffle re-anchored to the succinate-symmetry 50/50 (design B, value 0.5/0.5 stands), OGDH promoted (edit-allowed 14→15), 8 HIGH-STAKES + 12 ROUTINE claims and 7 sources approved, 3 PDB rejections provenance-tracked — registry landing is plan 05's job.**

## Performance

- **Duration:** ~20 min (continuation session: verdict recording + verification + bookkeeping)
- **Started:** 2026-09-01T02:46:15Z
- **Completed:** 2026-09-01
- **Tasks:** 1/1 (checkpoint:decision — human answered "All defaults" with the D1-D10 specifics below; previous agent had done the read-only verification, no commits, registry untouched)
- **Files modified:** 0 code/data files (planning docs only — by design: this plan RECORDS verdicts; plan 05 lands them in the registry)

## Human verdict (verbatim basis)

The human replied: **"All defaults"** — i.e. every recommended option + every default listed in the 07-03 checkpoint resume-signal, with the explicit refinements quoted in the D1-D10 Outcome lines below. Claim verdicts per the human: the 8 HIGH-STAKES `-cand` ids approved (keep `-cand` suffix; flip `approval_status` only — registry landing is plan 07-05's job); ROUTINE claims approved source-inherited; IDH wording softened per D9.

---

## Part 1 — Decisions D1-D10 (Outcome lines verbatim + rationale)

**D1 — Shuffle→CO2 RNG semantics (the phase's highest-stakes decision).**
Outcome: **design B** — re-anchor to succinate-symmetry 50/50 scramble (0.5/0.5 stands; TCA-RNG-WEIGHT-02-cand + TCA-CARBON-FATE-01-cand verdicts = approved).
Rationale (research §2): the verified isotope chemistry says the two CO2 of a turn derive from oxaloacetate carbons, not the incoming acetyl carbons — so the approved `TCA-RNG-WEIGHT-01` "first-turn vs second-turn exit" reading contradicts the precise result if read literally. Design B re-anchors the 50/50 onto the one genuinely stochastic carbon event (label scrambling at symmetric succinate/fumarate): outcome 1 = exit position (released as CO2 when the cycle next turns), outcome 2 = retained (rides again — geometric tail, which the N=5 cycle-trap caps naturally). The isotope-surprise becomes the teaching beat at `isocitrate_dh`/`akg_dh` ("the CO2 leaving are not necessarily yours"). VALUE 0.5/0.5 unchanged → NO engine/interpreter change, NO topology change (weights/texts/claim_ids are all JSON; interpreter.py pick_choice untouched). RNG outcome drives player GUIDANCE only (research §10 D1 sub-question default; no cond/branch logic added).
Consequence for claims: `TCA-RNG-WEIGHT-02-cand` supersedes `TCA-RNG-WEIGHT-01` semantics at the shuffle node (same value; `-01` remains in the registry as the approved historical claim — supersession is a text/claim_id-authoring matter for plan 13, not a registry deletion). `TCA-CARBON-FATE-01-cand` grounds the CO2-node teaching text.
Consequence for tests: the seeded-run documented-fate test (research §8) maps outcomes to the new meanings — lands in plan 16 ("seeded determinism, design B final" per the plan index).

**D2 — Prochirality claim source widening.**
Outcome: **(a)** — keep the approved `TCA-RNG-CITRATE-PROCHIRALITY-01` claim, widen its sources with Wikipedia co-cites.
Rationale (research §3.1): the claim text itself was approved 2026-08-15; only the supporting source set widens. Wikipedia "Aconitase" (Mechanism) supplies verbatim the pro-R/pro-S prochirality wording + the OAA-vs-acetyl discrimination + the 180° citrate-mode→isocitrate-mode flip that LibreTexts 16.02 lacks (16.02 never says "prochiral" for citrate — the registered review_notes caveat was accurate). Minimal option (a) over (b) file-`-02`-and-retire-`-01`: keeps per-claim immutability intact with one registry edit. Plan 05 adds `WIKIPEDIA-ACONITASE` (+ `WIKIPEDIA-TCA`) to the claim's source list; the human's batch approval covers the widened set.

**D3 — IDH3 cast PDB.**
Outcome: **IDH3 cast = 5GRE WT αγ 2.65 Å (replaces 5GRF, which is rejected with provenance).**
Rationale (research §7): skeleton's 5GRF is the human IDH3 αγ heterodimer with a γ-K151A crystallization mutation in the regulatory γ subunit (catalytic α is WT) — the same mutant-as-cast problem as the Phase 5.1 2OZL→6CFO pyr.pdh precedent. 5GRE is the WT companion from the same 2017 group (Mg²⁺ + citrate + ADP bound — the citrate/ADP-regulated form). Needs `CAST-IDH3-PDB-01-cand` → filed per Part 2. Plan 13 swaps the `tca.isocitrate_dh` load target; the 5GRF/5GRE α-chain construct-numbering vs UniProt P50213 one-check mapping (M204I/R316C `resi`) stays a content-authoring-time headless-iterate task (research §6.7/§11.6).

**D4 — IDH3A disease default.**
Outcome: **reaffirm IDH3A, M204I default (alt R316C).**
Rationale (research §6.3): live re-verification 2026-08-30 — UniProt P50213 lists 8 RP90 missense variants incl. M204I + R316C (UniProt's "uncertain significance" label is STALE, as Phase 5.1 established); ClinVar: M204I = VCV 977473 Pathogenic, R316C = VCV 977472 Pathogenic (9 pathogenic-missense records). IDH3A is the actual NAD⁺-dependent mitochondrial TCA enzyme; IDH1-R132H (the famous glioma oncomutation) is the cytosolic NADP⁺ isoform — NOT the TCA enzyme — and stays declined (a side teaching mention would need its own claim; not filed).

**D5 — tca.akg_dh disposition (OGDH negative overturned by the deeper ClinVar scan).**
Outcome: **PROMOTE akg_dh to edit-allowed (14→15; test update owed in plan 13; note the single-submitter evidence tier in the ledger).**
Rationale (research §6.5-6.6): the owed scan found 4 ClinVar-Pathogenic OGDH missense variants; P189L (VCV002443831, OMIM 613022.0003, Whittle et al. 2023 PMID 36520152 — homozygous, unstable protein in HEK293, oxoglutarate dehydrogenase deficiency) is the filed candidate; `cmd.alter`-compatible missense; `tca.akg_dh` is narrative-only (no PDB) so UniProt/MANE numbering is authoritative with no PDB mapping needed. The human accepted the plan-index default rec (promote) over the research's narrative-only preference — the plan index pre-set promote as the default recommendation, and the human answered "All defaults".
Mechanical consequence (recorded, implemented by plan 13 EXACTLY): add `edit:enzyme:tca.akg_dh` + an edit:offer choice → edit-allowed count 14→15; `tests/test_glucose_reachability.py` invariant update lands in plan 13 (same execution) per the plan index roster ("OGDH promotion if D5 approved (tca.akg_dh tags + edit-allowed 14→15 test update SAME plan)"). Node/endings counts stay 55/21 (a tag + choice, not new nodes). Evidence-tier caveat (MANDATORY in review_notes at plan 05): single-submitter, "no assertion criteria provided", literature-only — weaker than FH R233H's multi-submitter tier; text may say "a confirmed pathogenic mutation" only with the caveat retained in the registry record.
DIS-OGDH-01-cand (P189L → reverse L189P) is therefore APPROVED as one of the 8 HIGH-STAKES claims (conditional on D5=promote — trigger fired).

**D6 — Aconitase cast PDB species.**
Outcome: **1ACO bovine 2.05 Å (Ogston teaching structure; 1C97 + 2B3Y rejected with provenance).**
Rationale (research §7): human ACO2 has 0 PDB cross-refs (live re-confirmed 2026-08-30) — the cast MUST be non-human; 1ACO = Bos taurus mitochondrial aconitase, 2.05 Å, trans-aconitate bound, Lauble et al. 1994 (PMID 8151704) — matches the skeleton note + Phase 5.1. Homology caveat text mandatory in teaching content. 7ACN (pig, 2.0 Å, isocitrate/product-bound) verified as the runner-up alternative — NOT selected. OWED before any `edits.json` aconitase signature (Phase 5.1 OQ5, now load-bearing): human S112 ↔ bovine-1ACO residue mapping via real sequence alignment (05.3 align machinery + headless iterate probe) — do NOT author on assumed identity-of-numbering (research §6.7).

**D7 — CS dimer cast convention.**
Outcome: **monomer + teaching note (assembly load = engine flag, not implemented).**
Rationale (research §7): 1CSC AU = 1 chain; biological assembly 1 = homodimer; loading the assembly needs the PyMOL `assembly` setting before fetch (importing.py:1554-1563) = an AssetManager/molops code change — OUT of Phase 7 data-only scope (plan-index global constraint: no engine surgery; CS dimer = flag-only if a new op is ever wanted). Plan 13 loads the AU monomer via the existing molops path + the teaching text states "the functional enzyme is a homodimer". `CAST-CSC-PDB-01` (approved Phase 5) stands unchanged.

**D8 — MDH2 cast PDB.**
Outcome: **4WLU malate+NAD⁺ bound 2.14 Å.**
Rationale (research §7): pedagogically richer (substrate + cofactor visible at the active site; LibreTexts' own teaching model); 2DFD (apo, 1.9 Å) verified but NOT selected. Human MDH2, minor construct-offset check at content-authoring time (§6.7).

**D9 — Source-approval batch (research §9).**
Outcome: **approve the §9 source batch** — WIKIPEDIA-TCA, WIKIPEDIA-ACONITASE, LIBRETEXTS-METAB-TCA +16.04 scope extension [16.03 NOT fetched → soften "rate-limiting" to "a key regulatory step"], PMID-36520152 conditional, PDBs per D3/D6/D8 + 6WCV + 5UPP.
Scope precision: the LIBRETEXTS-METAB-TCA extension covers section **16.04 only** (citrate-lyase→FA-synthesis, GABA-shunt transamination, anaplerotic/cataplerotic framing, no-net-synthesis point — all fetched + quoted 2026-08-30). Section **16.03 (Regulation) was NOT fetched** → NO 16.03-grounded claim may be filed; consequently `TCA-IDH3-01` drops "rate-limiting" in favor of **"a key regulatory step"** (research OQ-2/§11.2 + §11.5; the skeleton's `tca.isocitrate_dh` dramatic text "This is the rate-limiting step of the TCA cycle" gets the same softening when plan 13 authors the node text). PMID-36520152 was conditional ("only if akg_dh text mentions OGDH deficiency") — **condition triggered by D5=promote → approved** (journal-article citation-of-record, matching the ClinVar/OMIM ref pattern).

**D10 — Cycle-trap N.**
Outcome: **cycle-trap N=5 confirmed (game-design parameter, not science).**
Rationale (research §10 D10): `visits.get('tca.shuffle', 0) > 5` is a game-design cap, NOT a science claim; under design B the geometric tail gives P(5 consecutive "retained") ≈ 3%, so N=5 reads naturally as the cap. Keep the "not a science claim" framing in any text. Adjust-at-playtest remains open (no registry entry; nothing to land).

---

## Part 2 — Claim VERDICTs

Policy (plan index, binding): approved `-cand` ids are KEPT verbatim (tests pin them, tests/test_glucose_reachability.py:339-351); only `approval_status` flips — the registry landing is **plan 05's** job. HIGH-STAKES = review_tier "high-stakes" + inherits_source_approval false; ROUTINE = "routine" + true.

### A. HIGH-STAKES claims (8 — individually reviewed; ALL APPROVED, keep `-cand` suffix)

| # | claim_id | VERDICT | Claim essence (research anchor) | Sources | Conditional on |
|---|----------|---------|-------------------------------|---------|----------------|
| 1 | `TCA-RNG-WEIGHT-02-cand` | **APPROVED** (design B re-anchor) | Shuffle weight 0.5/0.5 re-anchored: the 50/50 label-scrambling of the hero carbon at symmetric succinate/fumarate — exit position vs ride again; value unchanged from TCA-RNG-WEIGHT-01 | WIKIPEDIA-TCA (+ WIKIPEDIA-ACONITASE mechanism) | D1=B → trigger FIRED |
| 2 | `TCA-CARBON-FATE-01-cand` | **APPROVED** | Isotope-labeling result: the two CO2 of a turn derive from OAA carbons, not directly from the incoming acetyl carbons; acetyl carbons join the OAA backbone after turn 1, lost as CO2 only over several subsequent turns | WIKIPEDIA-TCA (verbatim) | D1=A-or-B → FIRED under B |
| 3 | `DIS-ACO2-01-cand` | **APPROVED** | ACO2 S112R → ICRD (MIM:614559); reverse R112S; UniProt live re-verified (S112R/G259D/K736N ICRD; L74V/G661R OPA9) | UNIPROT-Q99798 + CLINVAR records | — (re-verified) |
| 4 | `DIS-IDH3A-01-cand` | **APPROVED** (D4 reaffirm) | IDH3A M204I → RP90; reverse I204M; ClinVar VCV 977473 Pathogenic (alt R316C = VCV 977472, reverse C316R) | UNIPROT-P50213 + CLINVAR | — (re-affirmed) |
| 5 | `DIS-SUCLG1-01-cand` | **APPROVED** | SUCLG1 G85A → MTDPS9 (OMIM 245400); reverse A85G; rs267607097; note `DIS-SUCLG1-01` naming (not SUCLG6) | UNIPROT-P53597 + CLINVAR | — (re-verified) |
| 6 | `DIS-FH-01-cand` | **APPROVED** | FH R233H → HLRCC (OMIM 150800); reverse H233R; **rsID CORRECTION: rs121913123** (Phase 5.1 wrote rs121913121 — that belongs to N107T); strongest evidence tier of the set (multi-submitter + functional annotation "catalytically inactive") | UNIPROT-P07954 + CLINVAR | — (re-verified) |
| 7 | `DIS-MDH2-01-cand` | **APPROVED** | MDH2 G37R → DEE51 (OMIM 617339); reverse R37G; "severe defects in aerobic respiration… heterologous system" | UNIPROT-P40926 + CLINVAR | — (re-verified) |
| 8 | `DIS-OGDH-01-cand` | **APPROVED** (conditional — D5) | OGDH P189L → oxoglutarate dehydrogenase deficiency OGDHD (OMIM 613022.0003 / phenotype 203740); reverse L189P; homozygous, unstable protein (HEK293); **MANDATORY caveat in review_notes: single-submitter, no assertion criteria, literature-only (weaker tier)** | UNIPROT-Q02218 + CLINVAR VCV002443831 + PMID-36520152 | D5=promote → trigger FIRED |

### B. ROUTINE claims (12 — approved source-inherited per the hybrid workflow)

All rest on the approved LIBRETEXTS-METAB-TCA volume (16.02 re-verified live; 16.04 newly scoped by D9) and/or WIKIPEDIA-TCA / WIKIPEDIA-ACONITASE (both approved D9). Each carries `review_tier:"routine"` + `inherits_source_approval:true` at plan 05 landing; leisure spot-check only.

| # | claim_id | VERDICT | Node | Grounding (verbatim anchor) |
|---|----------|---------|------|------------------------------|
| 9 | `TCA-ENTRY-01` | **APPROVED** | tca.entry | Acetyl-CoA delivers a 2-C acetyl group, condensing with OAA → citrate (16.02 Introduction) |
| 10 | `TCA-CS-01` | **APPROVED** | tca.citrate_synthase | OAA + acetyl-CoA → citrate via (S)-citryl-CoA intermediate, ΔG°′ = −7.5 kcal/mol, thioester-hydrolysis-driven (16.02 §1) |
| 11 | `TCA-ACONITASE-01` | **APPROVED** | tca.aconitase | Citrate ⇌ isocitrate via cis-aconitate, 180° flip, Fe₄S₄ cluster, ΔG°′ ≈ +1.5 kcal/mol (16.02 + WIKIPEDIA-ACONITASE) |
| 12 | `TCA-IDH3-01` | **APPROVED — WORDING SOFTENED per D9** | tca.isocitrate_dh (+ co2 nodes) | "Isocitrate dehydrogenase (NAD⁺-dependent, mitochondrial) oxidatively decarboxylates isocitrate → α-KG + CO₂ + NADH" + **"a key regulatory step of the cycle"** (NOT "rate-limiting" — 16.03 Regulation page never fetched; OQ-2 resolved by softening). Wikipedia's "rate-limiting, irreversible" table note is the un-fetched-16.03 placeholder and is NOT filed as a claim |
| 13 | `TCA-OGDH-01` | **APPROVED** | tca.akg_dh | α-KG → succinyl-CoA + CO₂ + NADH; E1/E2/E3 complex homologous to PDH; TPP/lipoamide/FAD (16.02, cross-referencing 16.1) |
| 14 | `TCA-SCS-01` | **APPROVED** | tca.succinyl_coa_synthetase | Succinyl-CoA → succinate coupled to GTP synthesis — the cycle's ONLY substrate-level phosphorylation; phosphohistidine intermediate (16.02; E. coli His246 numbering caveat) |
| 15 | `TCA-FH-01` | **APPROVED** | tca.fumarase | Fumarate + H₂O ⇌ L-malate, stereospecific trans-hydration, ΔG°′ ≈ −0.9 kcal/mol (16.02) |
| 16 | `TCA-MDH2-01` | **APPROVED** | tca.malate_dh | L-malate → OAA + NADH, ΔG°′ = +7.1 kcal/mol (unfavorable — pulled by citrate synthase); regenerates the cycle's OAA acceptor (16.02) |
| 17 | `TCA-AMPHIBOLIC-01` | **APPROVED** | tca.divert_to_good | The TCA cycle is amphibolic; intermediates withdrawn (cataplerotic) for biosynthesis — citrate for lipids, OAA/α-KG for amino acids (WIKIPEDIA-TCA verbatim + 16.02 Summary + 16.04) |
| 18 | `TCA-CITRATE-EXPORT-01` | **APPROVED** | end.good.fatty_acid | Citrate exported (acetyl-CoA cannot cross); ATP-citrate-lyase cleaves it → cytosolic acetyl-CoA → fatty-acid synthesis; OAA returns as malate (WIKIPEDIA-TCA verbatim + 16.04). Scope = EXIT EVENT only (FA-synthesis chemistry is Phase 8) |
| 19 | `TCA-TRANSAMINATION-01` | **APPROVED** | end.good.amino_acid | TCA intermediates → amino-acid carbon skeletons via transamination (OAA→Asp/Asn; α-KG→Glu/Gln/Pro/Arg; PLP-dependent) (WIKIPEDIA-TCA verbatim + 16.04) |
| 20 | `TCA-CO2-EXIT-01` | **APPROVED** | end.normal.co2 | Each turn releases 2 CO2 (16.02 net equation, verbatim-verified); the carbon eventually leaves as CO2 across turns (WIKIPEDIA-TCA carbon-fate sentence) |

### C. Standing approved claims (re-verified this batch — no re-decision needed)

- `TCA-RNG-CITRATE-PROCHIRALITY-01` — VERDICT: **stands as approved**; source set WIDENED per D2(a) with WIKIPEDIA-ACONITASE + WIKIPEDIA-TCA co-cites (plan 05 registry edit; claim text unchanged).
- `TCA-RNG-WEIGHT-01` — VERDICT: **stands as approved** (value = human-accepted game-design decision 2026-08-15); its *semantics* are superseded at the shuffle node by `TCA-RNG-WEIGHT-02-cand` under D1=B — `-01` stays in the registry (approved claims are never silently deleted; supersession is authoring-level, plan 13).
- `CAST-CSC-PDB-01` — VERDICT: **stands** (1CSC re-verified: 1.70 Å, Gallus gallus, AU = 1 chain, biological assembly = homodimer).
- `GLY-PFK-01`, `CAST-PFK-PDB-01` — untouched (batch A's scope).

### D. Anti-confusion guardrails (binding on all text authors, from AGENTS.md + PROJECT.md)

Hero = the carbon atom; C14 = its tracking isotope label, NOT its fate. Electrons = the narrative "soul" → NADH/FADH₂ → ETC → ATP (True ending = soul harvested into ATP); the carbon body is shed as CO2. NEVER write that the C14 carbon becomes ATP, becomes NADH, or "enters oxidative phosphorylation". At the cataplerotic good exits: "your carbon body lives on" (retained); at the ETC path: "your soul (electrons) journey on; your carbon body is shed" (05.4-CONVENTION §3.6 template verbatim).

---

## Part 3 — Source VERDICTs (research §9 batch, per D9)

| source_id | VERDICT | Reference / license | Covers |
|-----------|---------|---------------------|--------|
| `WIKIPEDIA-TCA` | **APPROVED** | Wikipedia "Citric acid cycle", https://en.wikipedia.org/wiki/Citric_acid_cycle, CC BY-SA 4.0 (fetched live 2026-08-30, rev 1370238747) | Carbon-fate isotope result (verbatim); "cataplerotic" + citrate-export/ATP-citrate-lyase/FA-synthesis (verbatim); transamination exits (verbatim); amphibolic; per-turn stoichiometry; IDH rate-limiting table note (NOT filed as claim wording — see softened TCA-IDH3-01); SCS GDP/ADP isoforms |
| `WIKIPEDIA-ACONITASE` | **APPROVED** | Wikipedia "Aconitase", https://en.wikipedia.org/wiki/Aconitase, CC BY-SA 4.0 (fetched live 2026-08-30, rev 1343733503) | Pro-R/pro-S prochirality + OAA-vs-acetyl discrimination + 180° flip (all verbatim); His101/Ser642 catalytic residues (pig/bovine numbering); Fe₄S₄ with labile Fe |
| `LIBRETEXTS-METAB-TCA` (existing source — **+16.04 SCOPE EXTENSION approved**) | **APPROVED (16.04 scope only)** | Jakubowski & Flatt Vol. II Ch 16; CC BY-SA 4.0 volume (per-page "not declared" metadata gap already documented) | 16.02 (re-verified live 2026-08-30: mechanisms, ΔG°′ table, the "fully released as CO2" shorthand, Krebs ¹⁴C narrative) + **16.04** (citrate-lyase→FA-synthesis; GABA-shunt transamination; anaplerotic framing; no-net-synthesis point). **16.03 (Regulation) NOT fetched → OUT of approved scope; no 16.03-grounded claim may be filed** (IDH wording softened accordingly) |
| `PMID-36520152` | **APPROVED (conditional → condition FIRED by D5=promote)** | Whittle et al. 2023, Genetics in Medicine, "Biallelic variants in OGDH … neurodevelopmental disorder"; via ClinVar VCV002443831 links; journal citation-of-record (license not required for factual citation — ClinVar/OMIM ref pattern) | OGDH P189L pathogenic; OGDHD phenotype; unstable-protein functional evidence |
| `PDB-5GRE` | **APPROVED** (per D3) | RCSB: WT human IDH3 αγ heterodimer + Mg²⁺/citrate/ADP, 2.65 Å, 2017 group | `CAST-IDH3-PDB-01-cand` (filed; routine tier) |
| `PDB-1ACO` | **APPROVED** (per D6) | RCSB: bovine (*Bos taurus* P20004) mitochondrial aconitase, 2.05 Å, trans-aconitate bound, Lauble et al. 1994 (PMID 8151704) | `CAST-ACO2-PDB-01-cand` (filed; routine tier; homology caveat + the OWED bovine↔human S112 mapping before any edits.json `resi` signature) |
| `PDB-4WLU` | **APPROVED** (per D8) | RCSB: human MDH2 with L-malate + NAD⁺ bound, 2.14 Å (LibreTexts' own teaching model) | `CAST-MDH2-PDB-01-cand` (filed; routine tier) |
| `PDB-6WCV` | **APPROVED** | RCSB: tartryl-CoA bound to human GTP-specific succinyl-CoA synthetase, 1.52 Å (ligand = tartryl-CoA analog — disclose in teaching text if shown) | SUCLG1 cast record (routine tier) |
| `PDB-5UPP` | **APPROVED** | RCSB: human fumarate hydratase, 1.8 Å | FH cast record (routine tier) |
| `PDB-7ACN` | Verified, **NOT selected** | Pig (*Sus scrofa* P16276) aconitase, 2.0 Å, isocitrate + nitroisocitrate (product) bound — D6 runner-up | Remains a verified alternative; no cast claim filed unless a later plan adopts it |
| `PDB-2DFD` | Verified, **NOT selected** | Human MDH2 apo, 1.9 Å — D8 runner-up | Same |
| `UNIPROT-Q99798/P50213/P53597/P07954/P40926/O75390/Q02218` + CLINVAR records | **APPROVED as evidence citations** | Live REST/E-utilities fetches 2026-08-30 (the Phase 5.1 toolset pattern; same usage as batch A's UniProt/ClinVar rows) | The DIS-* claims' annotations + classifications |

### Rejections (3 — recorded WITH provenance, never silently deleted; LEHNINGER precedent)

| id | VERDICT | Provenance |
|----|---------|------------|
| `PDB-5GRF` | **REJECTED as IDH3 cast** (replaced by 5GRE per D3) | RCSB live 2026-08-30: "Crystal structure of the alpha gamma **mutant (gamma-K151A)** of human IDH3…", 2.5 Å — a crystallization mutant in the regulatory γ subunit (catalytic α WT). Using it would re-create the 2OZL mutant-cast problem that Phase 5.1 fixed via the 6CFO swap. Rejection recorded in the registry so the skeleton's 5GRF reference resolves to the 5GRE swap, not a silent patch |
| `PDB-1C97` | **REJECTED as aconitase cast** | RCSB live 2026-08-30: bovine **S642A catalytic-site mutant** aconitase with citrate, 1.8 Å (Lloyd et al. 1999; the LibreTexts iCn3D teaching model). Catalytic-site mutant as cast = same disqualifying class as 5GRF/2OZL; viable only with explicit mutant disclosure — NOT recommended, NOT approved |
| `PDB-2B3Y` | **REJECTED as aconitase cast (wrong isoform)** | RCSB live 2026-08-30: human **CYTOSOLIC aconitase = ACO1/IRP1**, 1.85 Å — not the mitochondrial ACO2 the TCA cast needs. Wrong-isoform rejection recorded so no future researcher re-proposes it (the brief's open question, answered) |

---

## Part 4 — Verification (this plan)

- **Full suite:** `python3.6 -m unittest discover -s tests` → **Ran 324 tests in 3.852s — OK** (baseline holds; no code/data touched).
- **Reachability invariants:** `python3.6 -m unittest tests.test_glucose_reachability` → **Ran 20 tests — OK**; counts **unchanged this plan: 55 nodes / 21 endings** (skeleton FROZEN). The D5 edit-allowed **14→15 promotion lands in plan 13's invariant update** (same execution), per the plan index — NOT in this plan (this plan records the decision only; registry + skeleton untouched).
- **Registry untouched:** `git status`/`git diff HEAD` on `data/citations.json` + `data/sources.json` → empty; registry still holds exactly the 5 Phase-5 approved claims (GLY-PFK-01, TCA-RNG-CITRATE-PROCHIRALITY-01, TCA-RNG-WEIGHT-01, CAST-PFK-PDB-01, CAST-CSC-PDB-01) + 5 sources. All 20 batch-B claim approvals + 9+2 source approvals + 3 rejections above are RECORDED HERE and land in the registry via **plan 05** (the sole owner of citations.json/sources.json per the serialization constraint).
- **Ledger coverage greps (plan's verification):** `grep -c "VERDICT\|Outcome" 07-03-SUMMARY.md` covers D1-D10 + all sources/claims; `grep "TCA-RNG-WEIGHT-02-cand"` confirms the design-B outcome is recorded.
- **No fabricated science:** every approved item was live-fetched/queried 2026-08-30 (research) and only APPROVAL is recorded here; research made zero approvals itself (its §Metadata).

## Deviations from Plan

None — single-checkpoint plan executed exactly as written. The human answered the checkpoint; this continuation recorded the verdicts, ran the verification, and committed planning docs only. (Registry intentionally untouched — landing is plan 05's scoped job.)

## Downstream obligations (consumed by later plans — key_links)

- **Plan 05** (registry landing): flip the 8 `-cand` approval_status values (keep ids); add the 12 routine claims with review_tier/inherits_source_approval/claim_text; add the new sources (+16.04 scope note on LIBRETEXTS-METAB-TCA); add the 3 rejections with provenance; apply the D2 co-source widening to `TCA-RNG-CITRATE-PROCHIRALITY-01`; carry the OGDH single-submitter caveat in review_notes.
- **Plan 10** (endings content): cites the 03-approved cataplerotic claims (`TCA-CITRATE-EXPORT-01`, `TCA-TRANSAMINATION-01`, `TCA-CO2-EXIT-01`, `TCA-AMPHIBOLIC-01`).
- **Plan 13** (TCA content): design-B shuffle texts + `TCA-RNG-WEIGHT-02-cand`/`TCA-CARBON-FATE-01-cand` claim_ids at the shuffle/CO2 nodes; 5GRE swap; 1ACO cast (+ homology caveat); 4WLU cast; CS monomer + dimer teaching note (D7; assembly-load flag only); **OGDH promotion implementation: `edit:enzyme:tca.akg_dh` + edit:offer choice + edit-allowed 14→15 test update in the SAME plan**; IDH text softened to "a key regulatory step".
- **Plan 14** (edits.json): TCA buckets — ACO2 (after the OWED 1ACO bovine↔human S112 mapping), IDH3A M204I (alt R316C per D4), SUCLG1 G85A, FH R233H (rs121913123 corrected), MDH2 G37R, **+ OGDH P189L (reverse L189P; UniProt/MANE numbering — no PDB mapping needed; caveat tier)** per D5.
- **Plan 15** (cast): `pdb:TBD_ACONITASE` → 1ACO per D6; 5GRE/4WLU/6WCV/5UPP rows.
- **Plan 16** (cross-cutting): seeded-determinism test with the **design-B documented fate** (§8); count invariants 57/21 (post-plan-12) with edit-allowed per the D5 outcome.
