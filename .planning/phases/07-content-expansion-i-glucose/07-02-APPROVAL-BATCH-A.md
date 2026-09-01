# Phase 7 — Approval Batch A: Glycolysis + Pyruvate Branch (plan 07-02)

**Status: AWAITING HUMAN VERDICTS — nothing below is approved. The registry (`data/citations.json`, `data/sources.json`) is UNTOUCHED until you reply and a continuation run records your verdicts in 07-02-SUMMARY.md (then plan 05 lands them).**

- **Assembled:** 2026-09-01 by the 07-02 executor
- **Basis:** 07-RESEARCH-glycolysis-pyruvate.md (researched 2026-08-30, all sources fetched live) + 5 approval-time re-fetches performed 2026-09-01 (log in Part 5)
- **Scope:** glycolysis.json (6 nodes) + pyruvate_branch.json (7 nodes) + intro.json (light touch). DC-A (restored-node topology), DC-B (host_o2_low), OQ-C (20-AA cast), -cand keep-ids policy are plan **07-01**'s checkpoint, NOT this one — flagged where they interact.
- **Binding policy (plan index):** when approving, `-cand` claim_ids are KEPT verbatim (tests pin them: tests/test_glucose_reachability.py:339-351); only `approval_status` flips. Rejections are recorded with provenance (LEHNINGER precedent), never silently deleted.

---

## How to reply (decision format)

Six numbered answers, one per item in Part 4. Shorthand accepted:

```
1: approve-all            (or list exceptions, e.g. "1: approve-all except AN-G-02 use softened wording")
2: default                (PFKM text-only fallback)  — or: 2: featured-mutant=W686C / 2: option-1 / 2: option-3
3: default                (7FS3 + 2VGG approach (b)) — or: 3: 2VGB / 3: 7FS3-no-mutant
4: default                (applyEdit on 6CFO)        — or: 4: option-b (load 6CER)
5: default                (yeast-counterfactual)     — or: 5: drop / 5: host-variation
6: default                (keep 5W8J, name inhibitor) — or: 6: other-LDH / 6: hide-ligand
```

"approve-all" in item 1 = approve every claim in Part 2 exactly as worded (with the two flag-resolutions noted inline for AN-G-02). To edit any wording, quote your replacement — it will be re-checked against the source before recording.

---

## Part 1 — Sources (approve per source; one approval unlocks all claims resting on it)

| # | source_id (proposed) | What it is | License | Claims resting on it | Why needed | Verification |
|---|----------------------|-----------|---------|----------------------|-----------|--------------|
| S1 | `LIBRETEXTS-CATAB-GLYCOLYSIS` | "Glycolysis", LibreTexts Catabolism (Darik Benson) — all 10 steps + priming/payoff phases + PK regulation + pyruvate fate | CC BY-NC-SA 4.0 (footer verbatim) | GLY-INTRO-01, GLY-HXK-01, GLY-TRIOSE-01, GLY-PKM-01, AN-G-01 | The entire glycolysis node chain's teaching text | **Fetched live 2026-08-30 AND re-fetched 2026-09-01** — quotes confirmed |
| S2 | `LIBRETEXTS-CATAB-FERMENTATION` | "Fermentation", LibreTexts Catabolism (Benson + Blaber) — lactic in muscle, alcoholic in yeast, NAD+ recycling, yield | CC BY-NC-SA 4.0 (footer verbatim) | AN-G-02, AN-G-03, AN-G-04, AN-G-05, AN-ANAER-DEF-01 (opt) | The entire anaerobic branch (3 endings) + the OQ1 host-tension evidence | **Fetched live 2026-08-30 AND re-fetched 2026-09-01** — quotes confirmed |
| S3 | `LIBRETEXTS-CATAB-BIOOX` (re-confirm) | "Biological Oxidation", LibreTexts Catabolism | CC BY-NC-SA 4.0 | AN-ETC-02 (with S4) | O2-as-terminal-acceptor grounding for the crisis (Bad) ending | Verified 2026-08-15 (Phase 5); **re-fetched 2026-09-01** |
| S4 | `LIBRETEXTS-CATAB-ETC` (re-confirm) | "Electron Transport Chain", LibreTexts Catabolism | CC BY-NC-SA 4.0 | AN-ETC-02 (with S3) | "Electrons finally given to oxygen… proton gradient drives ATP" grounding | Verified 2026-08-15 (Phase 5); **re-fetched 2026-09-01** |
| S5 | `LIBRETEXTS-METAB-TCA` §16.01 pointer (source ALREADY APPROVED — new section pointer) | Jakubowski & Flatt Vol. II §16.01 "Production of Acetyl-CoA (Activated Acetate)" | CC BY-SA 4.0 (volume; subpage footer "not declared" — same documented gap as the approved 16.02) | PYR-PDH-01 | pyr.pdh's only pathway claim; the LibreTexts Catabolism PDH page is a stub (R1) so the approved book is the source, new section pointer recorded in review_notes (16.02 precedent) | **§16.01 subpage fetched live 2026-09-01** — exact sentences quoted in Part 2 claim #18 |
| S6 | `UNIPROT-P08237` | UniProtKB PFKM reviewed entry, variant table (VAR_006066 G209D) | CC BY 4.0 | DIS-PFKM-01-cand | The mutation's curated annotation ("loss of activity shown by complementation assays in yeast") | REST fetched live 2026-08-30 |
| S7 | `UNIPROT-P30613` | UniProtKB PKLR reviewed entry, variant table (VAR_011480 R479H) | CC BY 4.0 | DIS-PKLR-01-cand | "in CNSHA2; Amish; no conformational change" annotation | REST fetched live 2026-08-30 |
| S8 | `UNIPROT-P08559` | UniProtKB PDHA1 reviewed entry, variant table (VAR_004952 V167M) | CC BY 4.0 | DIS-PDHA1-01-cand | "disrupts magnesium binding and results in deficient activity" annotation | REST fetched live 2026-08-30 |
| S9 | `CLINVAR-VCV003375341` | ClinVar variation record for PFKM G209D | Public domain (US gov) | DIS-PFKM-01-cand | The classification: **"Likely pathogenic"** (NOT Pathogenic) | E-utilities fetched live 2026-08-30 |
| S10 | `CLINVAR-VCV000001510` | ClinVar variation record for PKLR R479H | Public domain (US gov) | DIS-PKLR-01-cand | The classification: **"Pathogenic"**, multiple submitters, no conflicts | E-utilities fetched live 2026-08-30 |
| S11 | `CLINVAR-VCV000985548` | ClinVar variation record for PDHA1 V167M | Public domain (US gov) | DIS-PDHA1-01-cand | The classification: **"Pathogenic/Likely pathogenic"** | E-utilities fetched live 2026-08-30 |
| S12 | PubMed cite-only set: 7825568 (Raben 1995), 8161798 (Kanno 1994), 11960989 (Valentini 2002), 29970614 (Whitley 2018), 8504306 (Chun 1993), 36753880 (Nain-Perez 2023), 29120638 (Rai 2017) | Primary-literature bibliographic records | Publisher (metadata public) | DIS-* + CAST-PDB claims (as evidence citations) | Existence + bibliographic data cross-verified via RCSB/UniProt/ClinVar | Cross-ref-verified 2026-08-30 (abstracts not fetched — say so in item 1 if you want them) |
| S13 | `PDB-7FS3`, `PDB-2VGB`, `PDB-2VGG`, `PDB-6CFO`, `PDB-6CER`, `PDB-5W8J` | RCSB structure entries (see Part 2 for per-PDB metadata) | CC0 / PDB usage policy | CAST-PKLR-PDB-01, CAST-PKLR-MUTANT-PDB-01, CAST-PDH-WT-PDB-01-cand, CAST-PDH-MUTANT-PDB-01-cand, CAST-LDH-PDB-01 | The game's cast structures for PK, PDH, LDH | Data API fetched live 2026-08-30. ⚠️ 1LIY is REMOVED from RCSB — 2VGG is the current R479H-mutant ID |
| S14 | `PUBCHEM-CID-5793` | PubChem compound record, D-glucose | Public domain (US gov) | CAST-GLC-PUBCHEM-01 | The glucose 3D model (intro.shell_glucose + gly.start) | PUG REST fetched live 2026-08-30 |
| S15 | `PUBCHEM-CID-1060` (OPTIONAL — not in the 07-02 roster) | PubChem compound record, pyruvic acid | Public domain (US gov) | CAST-PYR-PUBCHEM-01 (optional) | Only if you want a pyruvate small-molecule model at gly.pyruvate | PUG REST fetched live 2026-08-30 (neutral-acid-vs-anion text nuance noted) |

### Pre-verified rejection (recorded with provenance unless you override)

| id | Verdict proposed | Provenance |
|----|------------------|-----------|
| R1 `LIBRETEXTS-CATAB-PYRUVATE-DH` | **REJECT as claim source** | LibreTexts Catabolism "Pyruvate Dehydrogenase Complex" page is a STUB (one Wikipedia figure, empty references) — fetched live 2026-08-30, unusable for PYR-PDH-01. Recorded so future researchers don't re-fetch it. PYR-PDH-01 routes to the approved book instead (S5). Same pattern as the LEHNINGER rejection (license) — rejected sources keep provenance, are not deleted. |

Already approved and NOT re-decided here: `LIBRETEXTS-METAB-GLYCOLYSIS`, `LIBRETEXTS-METAB-TCA`, `PDB-4PFK`, `PDB-1CSC`; claims `GLY-PFK-01`, `CAST-PFK-PDB-01`, `TCA-RNG-WEIGHT-01`, `TCA-RNG-CITRATE-PROCHIRALITY-01`, `CAST-CSC-PDB-01`.

---

## Part 2 — Claims (approve per claim; exact proposed claim_text below)

### A. Disease-mutant claims (3 — individually reviewed)

**#1 `DIS-PFKM-01-cand`** — node `gly.pfk`
- **Claim_text (REQUIRED wording — do NOT upgrade to "pathogenic"):** "PFKM G209D abolishes PFK-1 activity in yeast-complementation assays (Raben 1995) and is classified Likely pathogenic in ClinVar (VCV003375341) for Glycogen Storage Disease VII / Tarui disease (MIM:232800)."
- **Sources:** S6 (UniProt VAR_006066: "in GSD7; loss of activity shown by complementation assays in yeast") + S9 (ClinVar **Likely pathogenic**, multiple submitters, no conflicts, eval 2024-09-20) + Raben 1995 (S12).
- **Mechanics:** missense → `cmd.alter` compatible. Reverse fix: D209G. ⚠️ Residue 209 is HUMAN numbering; the approved cast 4PFK is bacterial — no sourced mapping exists (see Decision 2).

**#2 `DIS-PKLR-01-cand`** — node `gly.pyruvate_kinase`
- **Claim_text:** "PKLR R479H is classified Pathogenic in ClinVar (VCV000001510) for chronic nonspherocytic hemolytic anemia type 2 / pyruvate kinase deficiency (MIM:266200); the variant is annotated in the Amish population, and UniProt notes it causes no conformational change (VAR_011480; Valentini 2002)."
- **Sources:** S7 + S10 (ClinVar **Pathogenic**, multiple submitters, no conflicts, eval 2025-12-19) + Valentini 2002 / Kanno 1994 (S12). R479H re-confirmed (R479W appears nowhere in the curated table).
- **Mechanics:** missense; UniProt's "no conformational change" makes it the cleanest alter target in the game. Reverse fix: H479R. Residue 479 exists in 7FS3/2VGB/2VGG numbering (UniProt P30613 262–574 modeled) — no offset.

**#3 `DIS-PDHA1-01-cand`** — node `pyr.pdh`
- **Claim_text:** "PDHA1 V138M (mature numbering; V167M in the UniProt precursor including the 29-residue mitochondrial transit peptide) is classified Pathogenic/Likely pathogenic in ClinVar (VCV000985548); it disrupts magnesium binding and results in deficient activity of the pyruvate dehydrogenase complex (UniProt VAR_004952; Whitley 2018), causing PDH deficiency (MIM:312170, X-linked)."
- **Sources:** S8 + S11 (eval 2023-12-21) + Whitley 2018 / Chun 1993 (S12).
- **Mechanics:** missense. Reverse fix: M138V (**PDB/mature numbering — resi 138**; the offset 167↔138 is confirmed). Numbering-display convention for player-facing text = noted in Decision summary (show PDB resi 138, teach the V167M literature alias).

### B. Cast-structure claims (4 core + 2 conditional + 1 intro)

**#4 `CAST-PDH-WT-PDB-01-cand`** — node `pyr.pdh`
- **Claim_text:** "The game's PDH E1 wild-type cast structure is RCSB PDB 6CFO (2.70 Å, human PDHA1 E1 heterotetramer with the covalent TDP-acetyl-phosphinate analog + Mg²⁺; Whitley 2018, PubMed 29970614, DOI 10.1074/jbc.RA118.003996)."
- **Verification:** RCSB data API live 2026-08-30. Bonus corroboration: the approved §16.01 page itself embeds 6CFO ("iCn3D model of one human pyruvate dehydrogenase E1 component complex with TPnP… PDB ID: 6CFO" — fetched 2026-09-01).

**#5 `CAST-PDH-MUTANT-PDB-01-cand`** (conditional — needed only if Decision 4 → option-b) — node `pyr.pdh`
- **Claim_text:** "The V138M mutant reference structure is RCSB PDB 6CER (2.69 Å, human PDH E1 V138M mutation, same Whitley 2018 paper; ligands TPP + Mg²⁺)."

**#6 `CAST-PKLR-PDB-01`** — node `gly.pyruvate_kinase` (the 7FS3-vs-2VGB choice = Decision 3)
- **Claim_text (7FS3 variant):** "The game's pyruvate kinase cast structure is RCSB PDB 7FS3 (1.66 Å, human PKLR L-type in complex with allosteric modulator 15, oxalate, Mg²⁺, K⁺; Nain-Perez 2023, PubMed 36753880)."
- **Claim_text (2VGB variant):** "The game's pyruvate kinase cast structure is RCSB PDB 2VGB (2.73 Å, human erythrocyte R-type pyruvate kinase; Valentini 2002, PubMed 11960989 — the same paper that characterized the R479H disease variant)."
- **Caveat either way:** 7FS3 is L-type (liver) while the disease is RBC — a one-line teaching note; 2VGB is erythrocyte (matches disease tissue) but lower-res.

**#7 `CAST-PKLR-MUTANT-PDB-01`** (conditional — needed only if Decision 3 adopts the 2VGG approach) — node `gly.pyruvate_kinase`
- **Claim_text:** "The R479H mutant reference structure is RCSB PDB 2VGG (2.74 Å, 'Human erythrocyte pyruvate kinase: R479H mutant', Valentini 2002; keywords include 'DISEASE MUTATION'; the old ID 1LIY is superseded/removed — 2VGG is current)."

**#8 `CAST-LDH-PDB-01`** — node `anaer.ldh` (inhibitor caveat = Decision 6)
- **Claim_text:** "The game's LDH cast structure is RCSB PDB 5W8J (1.55 Å, human LDHA wild-type in complex with inhibitor compound 29; Rai 2017, PubMed 29120638, DOI 10.1021/acs.jmedchem.7b00941)."

**#9 `CAST-GLC-PUBCHEM-01`** — nodes `intro.shell_glucose` (+ unblocks `gly.start` show_as glucose)
- **Claim_text:** "The game's glucose model is PubChem CID 5793 (D-glucose, C6H12O6, MW 180.16, 3D conformer; IUPAC (3R,4S,5S,6R)-6-(hydroxymethyl)oxane-2,3,4,5-tetrol — the oxane ring is the pyranose ring form)."

**#10 `INTRO-CAST-20AA-01` — CONTINGENT, NOT approvable in this batch.** The 20-AA cast structure has NO source (still the bundled `_smoke.pdb` fixture). Plan 07-01's OQ-C decision (default: defer real cast to Phase 9) governs. If 07-01 defers, this claim is simply not authored this phase. Listed so the ledger is complete.

### C. Routine pathway claims (11)

**#11 `GLY-INTRO-01`** — node `gly.start` — source S1
- "Glycolysis converts one glucose into two pyruvates via ten enzymatic steps: a 2-ATP-investment priming phase and a 4-ATP-yield payoff phase (net 2 ATP + 2 NADH)."
- Verbatim anchors (re-fetched 09-01): "Glycolysis is the catabolic process in which glucose is converted into pyruvate via ten enzymatic steps." / priming "requires an input of energy in the form of 2 ATPs per glucose" / payoff "energy is released in the form of 4 ATPs, 2 per glyceraldehyde molecule."

**#12 `GLY-HXK-01`** — node `gly.g6p` — source S1
- "Hexokinase catalyzes glycolysis step 1: glucose + ATP → glucose-6-phosphate + ADP; the step is inhibited by its product G6P (product inhibition)."
- Verbatim: "alpha-D-Glucose is phosphorolated at the 6 carbon by ATP via the enzyme Hexokinase (Class: Transferase) to yield alpha-D-Glucose-6-phosphate (G-6-P). This is a regulatory step which is negatively regulated by the presence of glucose-6-phosphate."

**#13 `GLY-TRIOSE-01`** — node `gly.fbp_to_pyruvate` — source S1
- "Steps 4–9: aldolase cleaves FBP into DHAP + G3P; TPI equilibrates DHAP→G3P; GAPDH oxidizes G3P to 1,3-BPG (producing NADH); PGK and PK make ATP by substrate-level phosphorylation; PGAM + enolase prepare PEP."
- Verbatim: steps 4–9 of the page (aldolase Lyase / TPI Isomerase / GAPDH "phosphorolated at the 1 carbon… 1,3-Bisphosphoglycerate" / PGK "to yield ATP and 3-Phosphoglycerate" / PGAM / enolase).
- ⚠️ Text-accuracy note (OQ-G): the node's skeleton placeholder "Net so far: 2 ATP, 2 NADH" is ambiguous-to-wrong — after step 9 the account is 2 ATP invested + 2 ATP recovered + 2 NADH banked (the 2nd substrate-level ATP lands at PK). Phase 7 text fixes this phrasing.

**#14 `GLY-PKM-01`** — node `gly.pyruvate_kinase` — source S1
- "Pyruvate kinase catalyzes glycolysis step 10: PEP + ADP → pyruvate + ATP (the second substrate-level phosphorylation); allosterically inhibited by high-energy signals (ATP, acetyl-CoA, alanine, cAMP)."
- Verbatim: "ADP is once again phosphorolated, this time at the expense of PEP by the enzyme pyruvate kinase to yield another molecule of ATP and and pyruvate… high concentrations of ATP, Acetyl-CoA, Alanine, and cAMP" [indicate inhibition].

**#15 `AN-G-01`** — nodes `gly.pyruvate` + `pyr.branch` — source S1
- "Glycolysis ends at pyruvate; pyruvate's fate depends on oxygen: aerobically it feeds the TCA cycle (via PDH), anaerobically it is reduced to lactate or ethanol (fermentation)."
- Verbatim: "two new pyruvate molecules which can then be fed into the Citric Acid cycle… if oxygen is present, or can be reduced to lactate or ethanol in the absence of of oxygen using a process known as Fermentation." (The "via PDH" clause is grounded on S5/§16.01.)

**#16 `AN-G-05`** — node `pyr.branch` — source S2 — ALSO the load-bearing evidence for Decision 5 (OQ1)
- "Lactic fermentation occurs in oxygen-depleted muscle (and some bacteria); ethanolic fermentation occurs in yeast."
- Verbatim: "This process takes place in oxygen depleted muscle and some bacteria." / "The purpose of fermentation in yeast is the same as that in muscle and bacteria…" (section titles: "Lactic acid fermentation in contracting muscle" / "Alcoholic fermentation in yeast").

**#17 `PYR-PDH-01`** — node `pyr.pdh` — source S5 (approved book, new §16.01 pointer)
- "The pyruvate dehydrogenase complex catalyzes the oxidative decarboxylation of pyruvate to acetyl-CoA (releasing CO2 and generating NADH), the committed entry of carbon into the citric acid cycle."
- Exact sentences quoted from §16.01 (fetched live 2026-09-01): "pyruvate enters the mitochondria and starts the process of oxidative decarboxylation by interacting with the pyruvate dehydrogenase complex" / "The end products of the … oxidative decarboxylation reaction are the two-carbon acetyl-CoAs, NADH, and CO2." / "The third carbon from pyruvate is released as CO2. The reaction is catalyzed by the enzyme pyruvate dehydrogenase complex (PDC)." / net reaction "pyruvate + CoASH + NAD+ → Acetyl-CoA + CO2 + NADH + H+".
- Teaching bonus (same page): TPP is one of the five vitamin-derived cofactors — supports the "violet cofactor cradle" note for 6CFO's TDP-analog + Mg²⁺ ligands.

**#18 `AN-G-04`** — nodes `anaer.entry` + `anaer.crisis` — source S2
- "Fermentation recycles NAD+ (from NADH) so glycolysis can continue; its energy yield is much less than TCA + ETC."
- Verbatim: "Fermentation is the process by which living organisms recycle NADH → NAD+." / "If the supply of NAD+ is not replenished by the ETC or fermentation, glycolysis is unable to proceed." / "The yield of energy is much less than if the organism were to continue on through the TCA cycle and ETC."

**#19 `AN-ANAER-DEF-01` (OPTIONAL)** — node `anaer.entry` — source S2
- "Fermentation recycles NAD+ without an electron-transport chain; anaerobic respiration instead uses a non-oxygen terminal electron acceptor (e.g. nitrate, sulfur, metals) with an ETC."
- Verbatim: "One way that a cell recycles NAD+ is through the process of respiration, a set of sequential electron transfers involving an electron transport chain to a terminal electron acceptor… In anaerobic organisms, the terminal electron acceptor can vary from species to species and include… various metals like Fe(III), Mn(IV) and Co(III), CO2, nitrate, sulfur… Another way that NAD+ is recycled from NADH is by a process called fermentation."

**#20 `AN-G-02`** — nodes `anaer.ldh` + `anaer.lactic` — source S2 — ⚠️ one wording flag, see below
- "In the absence of oxygen, pyruvate is reduced to lactate by lactate dehydrogenase, with NADH as the reducing agent; NAD+ is regenerated; no CO2 is released. This is the mammalian (muscle) fermentation."
- Verbatim: "Lactic acid fermentation occurs by converting pyruvate into lactate using the enzyme Lactate dehydrogenase and producing NAD+ in the process. This process takes place in oxygen depleted muscle and some bacteria."
- **Wording flag (honest-presentation note):** the "no CO2 is released" clause is IMPLIED by the page's reaction (pyruvate → lactate, single product; no decarboxylation step described) — no verbatim "no CO2" sentence exists on S-FERM/S-BIOX. Options: (i) approve as written (the implication is sound chemistry and was accepted in Phase 5 research framing), or (ii) soften to "its carbon is retained in lactate (no decarboxylation step occurs)" — airtight on the quoted text. State (i) or (ii) with your item-1 reply; default = (ii) softened wording.

**#21 `AN-G-03`** — node `anaer.ethanolic` — source S2 — framing = Decision 5
- "In yeast (not mammals), pyruvate is converted to acetaldehyde with release of CO2 by pyruvate decarboxylase; acetaldehyde is then reduced to ethanol by alcohol dehydrogenase, regenerating NAD+."
- Verbatim: "pyruvate being first converted into acetaldehyde by the enzyme pyruvate decarboxylase and releasing CO2" / "acetaldehyde is converted into ethanol using alcohol dehydrogenase and producing NAD+ in the process." The yeast scoping is IN the source (section title + "The purpose of fermentation in yeast…").

**#22 `AN-ETC-02`** — node `anaer.crisis` — sources S3 + S4 (+ S2 for the fermentation half)
- "Without oxygen the electron transport chain stalls (no terminal electron acceptor), oxidative phosphorylation cannot produce ATP, and the proton-motive force collapses; fermentation regenerates NAD+ but yields far less ATP."
- Verbatim anchors: S-BIOX — "with molecular oxygen as the final electron acceptor at the end" (terminal respiratory chain) / "The products NADH and FADH2… are able to reduce molecular oxygen (O2) thereby releasing large amounts of Gibbs energy used to make ATP." S-ETC — "finally given to oxygen resulting in the production of water" / "It is this proton gradient that drives phosphorolation of ADP to ATP." S-FERM — the yield/NAD+ sentences under #18.

**Optional #23 `CAST-PYR-PUBCHEM-01`** — see S15 (CID 1060, pyruvic acid; neutral-acid-vs-physiological-anion nuance would be stated in text). Not in the plan roster — approve only if you want it.

---

## Part 3 — Count summary

- **Sources:** 13 new-source approvals requested (S1, S2, S6–S14 = 13; S15 optional = 14) + 2 re-confirmations (S3, S4) + 1 new section pointer on an approved source (S5) + 1 pre-verified rejection (R1).
- **Claims:** 20 core (#1–9, #11–22 minus optional/contingent) + 2 optional (#19, #23) + 2 conditional (#5, #7) + 1 contingent-on-07-01 (#10). Every claim keeps its `-cand` id where it has one; new claims use their bare ids from birth.

---

## Part 4 — The 6 decisions (default = research/plan recommendation)

### Decision 1 — Claims verdict
Approve / reject / edit the Part-2 claims. Recommended: **approve as presented** (wording is source-verbatim or flagged where implied — see the AN-G-02 flag; choose (i)/(ii) there). Per-claim rejection is fine — each records provenance.

### Decision 2 — DC-2/DC-3: PFKM featured mutant + cast/mutation reconciliation
**Context:** the human mutation G209D is numbered on human PFKM; the approved cast 4PFK is bacterial (*G. stearothermophilus*, ~320 AA vs human 780) — residue 209 does not exist in 4PFK, and mapping it needs a sequence-alignment source that does not exist yet (OQ-B; human PFKM PDB 4OMT is 6.0 Å — poor visuals).
- **default (Recommended): text-only disease fallback** — no on-structure alter at an unsourced bacterial residue; PFK keeps its restoration ARC as narrative; G209D carried in teaching text with the "Likely pathogenic" wording.
- option-1: alignment-mapped alter — requires a NEW sourced residue-equivalence claim (UniProt P00512-vs-P08237 alignment verification task) before any alter.
- option-3: switch cast to 4OMT (6.0 Å — poor visuals; would also need re-approval of CAST-PFK-PDB-01).
- Also pick the featured mutant if not G209D (all UniProt-verified live 08-30): W686C (Japanese mild), R39L (Ashkenazi founder), D309G (Spanish, "complete loss of activity").
- Note: PROJECT.md row 109 caps the full restoration arc at 1–2 enzymes; PDH is the strongest arc candidate (real 6CFO/6CER geometry), so PFK text-only costs little.

### Decision 3 — DC-4: PKLR cast + restoration approach
- **default (Recommended): 7FS3** (1.66 Å L-type, modulator+oxalate+Mg+K — best resolution, active-site ligands visible) **+ adopt the 2VGG mutant-PDB approach** for the restoration arc (real R479H structure; mirrors the PDH option). Approves #6 (7FS3 wording) + #7.
- alt: **2VGB** (2.73 Å erythrocyte R-type — matches the RBC disease tissue; the Valentini disease-paper structure) ± 2VGG.
- alt: 7FS3/2VGB with NO mutant structure (approach-a-style alter on the WT cast).
- Caveat if 7FS3: L-type(liver)-structure vs RBC-disease framing — one honest teaching line.

### Decision 4 — DC-5: PDHA1 restoration approach (OQ-DM2, deferred here by 05.1-06)
- **default (Recommended): (a) applyEdit on 6CFO** — approximate geometry via cmd.alter, consistent with the other enzymes; #5 (6CER) unused.
- alt **(b) load 6CER real-mutant geometry** — spec item 4 "reveal correct 3D model" alignment; requires approving #5 (`CAST-PDH-MUTANT-PDB-01-cand`).

### Decision 5 — OQ1: ethanolic-fermentation framing in a mammalian host
**Context:** S-FERM verbatim assigns ethanolic fermentation to YEAST; mammals lack pyruvate decarboxylase. The skeleton's `anaer.ethanolic` Normal-tier ending carries the host-tension flag.
- **default (Recommended): (b) yeast-counterfactual teaching moment** — zero topology change; dramatic layer shows the alternate road ("in another host — a yeast cell…"); teaching layer states the real yeast chemistry (PDC releases CO2, ADH → ethanol, NAD+ regenerated) and honestly says the mammalian host does not run this path. Grounded: AN-G-03 + AN-G-05.
- alt (a): DROP the node/ending — topology change to the frozen skeleton (21→20 endings), reverses the recorded 05.1-06 approval, discards the canonical lecture-topic fermentation.
- alt (c): host variation — contradicts the resolved Host=mammal decision (PROJECT.md row 97).

### Decision 6 — OQ-E: 5W8J inhibitor caveat
**Context:** 5W8J is WT human LDHA + inhibitor compound 29 bound in the active site (cancer-drug-discovery structure).
- **default (Recommended): keep 5W8J + teaching text names the bound inhibitor** ("a research inhibitor sits in the very pocket lactate would occupy").
- alt: pick another LDH structure (NOT verified — would need a new verification pass before approval).
- alt: hide/remove the ligand via MolActions at on_enter.

*(Not decided here — plan 07-01's checkpoint: DC-A restored-node topology, DC-B host_o2_low setter, OQ-C 20-AA cast, -cand keep-ids policy, PLACEHOLDER_PHASE8, M5, OQ-K. This batch's outcomes slot into whatever 07-01 records.)*

---

## Part 5 — Approval-time verification log (performed 2026-09-01, per research §6 instructions)

| Fetch | Result |
|-------|--------|
| §16.01 subpage (bio.libretexts.org, Jakubowski & Flatt) | LIVE (page modified 2026-08-03). Full PDH text confirmed; exact sentences quoted in #17. License: volume CC BY-SA 4.0; subpage footer "not declared" — same documented gap as approved 16.02. NOTE: the page's Learning-Goals and Summary boxes are marked "(written by Claude, Sonnet 4.6, Anthropic)" — claim grounding uses only the Jakubowski/Flatt body text, never those boxes. Bonus: the body embeds 6CFO (corroborates #4). |
| Catabolism/Biological_Oxidation | LIVE. CC BY-NC-SA 4.0 footer confirmed. O2-as-final-acceptor + NADH/FADH2→O2 ATP text confirmed (anchors for #22). |
| Catabolism/Electron_Transport_Chain | LIVE. CC BY-NC-SA 4.0 footer confirmed. "finally given to oxygen… production of water" + proton-gradient-drives-ATP text confirmed (anchors for #22). |
| Catabolism/Glycolysis | LIVE. CC BY-NC-SA 4.0 (author Darik Benson). All 10 steps + phases + regulation text confirmed verbatim (anchors for #11–15). |
| Catabolism/Fermentation | LIVE. CC BY-NC-SA 4.0 (Benson + Blaber). Lactic/alcoholic/NAD+-recycling/yield text confirmed verbatim (anchors for #16, #18–21); bonus "Fermentation occurs in the cytosol of cells" supports the gly.start cytosol note (research §8). |

Not re-fetched (verified live 2026-08-30 by the research session, 2 days old): RCSB data API entries, UniProt variant tables, ClinVar records, PubChem records. Say so in your reply if you want any of those re-fetched before verdicts are recorded.

---

## Part 6 — What happens after you reply

1. A continuation run records every verdict + the 6 decision outcomes in `07-02-SUMMARY.md` (VERDICT lines per claim/source/decision), commits it.
2. Plan 05 (registry landing) applies the recorded outcomes to `data/citations.json` + `data/sources.json` — approved claims keep their `-cand` ids, `approval_status` flips; rejections recorded with provenance.
3. Plans 06/07/08/14 author text/edits ONLY for approved claims.
