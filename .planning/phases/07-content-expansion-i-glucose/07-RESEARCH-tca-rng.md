# Phase 7 — TCA Cycle + RNG Shuffle + Cataplerotic Good-Exits: Research

**Researched:** 2026-08-30 (all live-source verifications dated 2026-08-30)
**Domain:** TCA-cycle carbon-fate chemistry (RNG grounding), per-claim inventory for the 12 `tca.json` nodes + 3 `endings.json` good/normal nodes, cataplerotic exit science, TCA disease-mutant re-verification, TCA cast PDB verification, RNG mechanics (data vs code)
**Confidence:** HIGH on all live-verified items; the shuffle→CO2 *design* choice itself is a human decision (3 options presented with evidence)
**Scope note:** Per the orchestrator brief — glycolysis/pyruvate-branch, ETC/ATP/ending-text files, and content mechanics are OTHER researchers' scope; only cross-boundary notes appear here. This file covers `data/story_glucose/tca.json` (12 nodes), the TCA-anchored `endings.json` claims (good exits + normal CO2), `data/citations.json` / `data/sources.json` entries, `rpg/data/edits.json` TCA entries, and TCA cast PDBs. NO engine/pymol_layer code proposals (constraint honored — §8 documents what is data vs code so the planner stays inside data files).

---

## 1. Summary

**What was researched.** (a) The chemistry grounding the `tca.shuffle` RNG — re-verifying the 2 approved high-stakes claims and chasing the queued "shuffle→CO2" weight claim; (b) the claim inventory for all 12 frozen TCA nodes + the 3 ending nodes whose claims this segment owns; (c) the OQ4 cataplerotic good-exit claims; (d) the pending disease-mutant candidates (IDH3A/SUCLG1/FH/MDH2/ACO2) re-verified live on UniProt + ClinVar, plus the owed OGDH deeper scan; (e) TCA cast PDBs re-verified on RCSB (1CSC, aconitase candidates, IDH3, SUCL, FH, MDH2); (f) what the planner can author as data vs what touches code.

**The single most important finding (carbon-fate subtlety).** The precise isotope-labeling chemistry — explicitly stated by a live-verified license-clear source (Wikipedia, CC BY-SA) — is that **the two CO2 released in a TCA turn derive from oxaloacetate carbons, NOT from the incoming acetyl carbons; the acetyl carbons are retained through the first turn and are lost only over several subsequent turns** (Wikipedia "Citric acid cycle", Overview, fetched 2026-08-30; corroborated by Wikipedia "Aconitase" Mechanism and by the approved LibreTexts 16.02's own Krebs-isotope narrative, which nevertheless keeps the "both acetyl carbons fully released by step 4" textbook *shorthand* in its Summary). The approved `TCA-RNG-WEIGHT-01` claim text ("probability that a given acetyl-CoA carbon exits as CO2 on the first turn vs the second turn = 0.5/0.5") is therefore a **game-design simplification that contradicts the precise carbon-fate chemistry if read literally**. Three defensible designs are presented in §2 (A: status quo + honest teaching text; B: re-anchor the shuffle's semantics to the succinate-symmetry 50/50 — recommended; C: full-precision carbonyl-vs-methyl duality). The weight VALUE (0.5/0.5) is defensible in every design — it is the *semantics* that need the human decision. The 0.5/0.5 value maps *exactly* onto the one genuinely stochastic event in TCA carbon bookkeeping: the label-scrambling 50/50 at the symmetric succinate/fumarate intermediates.

**Second major finding (prochirality gap fixable).** The known gap — LibreTexts 16.02 never uses the word "prochiral" for citrate — is fixable: Wikipedia's "Aconitase" Mechanism section states explicitly that aconitase abstracts the proton from *the carbon that came from oxaloacetate, not the one from acetyl-CoA, even though these two carbons are equivalent except that one is pro-R and the other pro-S (see Prochirality)*, and describes the 180° "citrate mode → isocitrate mode" flip. One sentence fills BOTH the prochirality gap AND the aconitase-discrimination statement (§3).

**Third major finding (OGDH negative overturned).** The owed deeper scan (Phase 5.1 examined only 14 of 163 ClinVar records) found **4 ClinVar-Pathogenic missense variants for OGDH**: P189L (OMIM 613022.0003; Whittle et al. 2023, PMID 36520152 — homozygous, unstable protein in HEK293, oxoglutarate dehydrogenase deficiency / OGDHD), R312K, S297Y, N320S. Caveat: single-submitter, "no assertion criteria provided", literature-only — a weaker evidence tier than FH R233H (multi-submitter). This turns `tca.akg_dh` from "no disease point mutant" into a real (but evidence-weaker) promotion candidate — a human decision (§6.6, checkpoint D5).

**Fourth finding (IDH3 cast PDB is a mutant).** The skeleton's `tca.isocitrate_dh` cast PDB **5GRF is the human IDH3 αγ heterodimer with a γ-K151A mutation** (crystallization mutant in the regulatory γ subunit; catalytic α is WT). A WT alternative exists: **5GRE** (WT αγ + Mg²⁺/citrate/ADP, 2.65 Å, same 2017 group). This mirrors the Phase 5.1 `pyr.pdh` 2OZL→6CFO precedent (mutant-as-cast disclosure/swap) — decision checkpoint D3.

**Everything else re-verified clean.** ACO2/SUCLG1/FH/MDH2 alleles confirmed live on UniProt (one rsID correction: FH R233H = rs121913123, not rs121913121); IDH3A M204I/R316C ClinVar-Pathogenic confirmed live (977473/977472); CS negative (0 variants, no disease block) confirmed; 1CSC re-verified (1.7 Å, *Gallus gallus*, AU = 1 chain, biological assembly 1 = dimer); human ACO2 still has 0 PDB cross-refs (live-confirmed 2026-08-30); 2B3Y verified as **human cytosolic aconitase (ACO1/IRP1) — the WRONG ISOFORM** for the TCA cast; 7ACN verified as PIG (*Sus scrofa*) aconitase 2.0 Å. Both cataplerotic good exits are grounded in license-clear live-verified sources — including a section that uses the word **"cataplerotic"** verbatim (Wikipedia) and the citrate→citrate-lyase→FA-synthesis mechanism inside the already-approved LibreTexts volume (16.04).

**Primary recommendation:** Keep the approved weight VALUE 0.5/0.5 (no engine change, no topology change); re-anchor the shuffle's claim semantics to the succinate-symmetry scramble (Design B, §2) with honest isotope-surprise teaching text at the CO2 nodes; re-anchor the prochirality claim with Wikipedia-Aconitase as explicit co-citation; swap 5GRF→5GRE for the IDH3 cast; keep `tca.akg_dh` narrative-only by default with the OGDH finding filed as a documented candidate. All of this is data-file work.

---

## 2. Shuffle→CO2 RNG weight design options (the highest-stakes decision)

### 2.1 The verified chemistry (all live-fetched 2026-08-30)

**Carbon bookkeeping of one TCA turn** (derived from the verified mechanism text; confidence HIGH for the parts directly quoted from sources, MEDIUM-HIGH for the derived turn-by-turn mapping — flagged inline):

1. Citrate synthase condenses acetyl-CoA (2 C) with oxaloacetate (4 C) → citrate (6 C). The acetyl **methyl** carbon becomes the CH₂ of one carboxymethyl arm; the acetyl **carbonyl** carbon becomes that arm's carboxyl. The OAA carbonyl becomes citrate's central C-OH. *(Source-supported: LibreTexts 16.02 mechanism text — enolate of acetyl-CoA attacks OAA carbonyl, thioester hydrolysis forms citrate.)*
2. **Aconitase acts ONLY on the oxaloacetate-derived arm.** Verified verbatim (Wikipedia "Aconitase", Mechanism): *"The carbon atom from which the hydrogen is removed is the one that came from oxaloacetate in the previous step of the citric acid cycle, not the one that came from acetyl CoA, even though these two carbons are equivalent except that one is 'pro-R' and the other 'pro-S' (see Prochirality)."*
3. **Both decarboxylations (IDH, α-KGDH) remove OAA-derived carboxyls.** Verified (Wikipedia "Citric acid cycle", Overview): *"The carbons lost as CO2 originate from what was oxaloacetate, not directly from acetyl-CoA. The carbons donated by acetyl-CoA become part of the oxaloacetate carbon backbone after the first turn of the citric acid cycle. Loss of the acetyl-CoA-donated carbons as CO2 requires several turns of the citric acid cycle. However, because of the role of the citric acid cycle in anabolism, they might not be lost."*
4. **Derived turn-by-turn fate of a labeled acetyl carbon** (derivation confidence MEDIUM-HIGH — mechanism-consistent, textbook-classic, but the *specific turn numbers* are my derivation, not a quote; the qualitative result IS quoted in source 3):
   - **Acetyl carbonyl carbon:** retained through turn 1 (it is a citrate/isocitrate/α-KG carboxyl — but not one of the two released; the two released are the recruited OAA's carboxyls). After turn 1 it sits in a **carboxyl position of the regenerated OAA** (both OAA carboxyl positions are released in the turn the OAA is used) → **exits as CO2 in turn 2, deterministically** (the succinate-symmetry 50/50 only decides *which* of the two carboxyl positions — both are released).
   - **Acetyl methyl carbon:** survives turn 1 AND turn 2 as an internal (methylene/central) carbon. At each pass through the symmetric succinate/fumarate intermediates its next position is a **genuine 50/50 coin flip** (label scrambling at the symmetric molecule — the classic isotope result): with p=½ it lands in an OAA carboxyl position (**doomed — released as CO2 when that OAA is used**) and with p=½ it stays internal (**rides again**). Exit-turn distribution: **geometric, p=½ per turn starting turn 3** (P(turn 3)=½, P(turn 4)=¼, P(turn 5)=⅛ …).
5. **Per-turn stoichiometry check** (verified): 2 C enter as acetyl-CoA, 2 CO2 leave per turn (LibreTexts 16.02 net equation + Wikipedia table) — the pool as a whole balances even though a *specific labeled carbon* does not exit in its entry turn.
6. **The LibreTexts 16.02 page itself** keeps the shorthand in its Summary — verified verbatim: *"At this point, the two carbons of the original acetyl-CoA have been fully released as CO2"* (after describing step 4) — AND separately documents Krebs's ¹⁴C isotope-tracing methodology (pigeon muscle) without performing the label-fate analysis. So the *approved source* contains the naive sentence and NOT the precise result; the precise result needs the Wikipedia co-citation.

### 2.2 The three defensible designs

All three keep weight **0.5 / 0.5** (the approved value; no interpreter/engine change; no graph change — both weighted choices still goto `tca.co2_turn1` / `tca.co2_turn2`).

| | **Design A — status quo weights, honest teaching text** | **Design B — re-anchor the shuffle to the succinate-symmetry scramble** (RECOMMENDED) | **Design C — full-precision carbonyl/methyl duality** |
|---|---|---|---|
| **What the 50/50 models** | "First-turn CO2 exit vs second-turn CO2 exit" (as approved) — kept as a game-design abstraction | The **succinate-symmetry coin flip**: outcome 1 = "exit position" (hero carbon lands in an OAA carboxyl position → released as CO2 during this pass); outcome 2 = "retained" (internal position → rides another turn) | Hero's acetyl identity decided upstream: carbonyl-hero → deterministic turn-2 exit; methyl-hero → geometric 50/50 from turn 3 |
| **Scientific fidelity** | The naive model, explicitly disclosed as simplification in teaching text | The real stochastic event; exact for the methyl-carbon case; approximately-flavored for the carbonyl case (which exits turn 2 regardless — disclosed in text) | Exact for both carbons |
| **What changes in files** | `tca.json` texts only + optional 1 new carbon-fate claim documenting the simplification. Node dramatic texts keep the naive framing WITH a teaching-layer correction | `tca.json` texts re-anchored (node ids/weights/topology untouched; all texts are TBD placeholders); 1 new/updated claim for the shuffle semantics; new Wikipedia source records | Requires upstream glycolysis-content coordination (which glucose carbon is the hero → which acetyl carbon), conditional RNG semantics per hero carbon, possibly per-hero branch texts |
| **Claims needed** | Existing 2 approved claims stand + optional `TCA-CARBON-FATE-01-cand` (HIGH-STAKES: "for game simplicity the shuffle uses the textbook shorthand; the precise isotope result is …", sourced Wikipedia + LibreTexts 16.02) | `TCA-RNG-WEIGHT-01` superseded by `TCA-RNG-WEIGHT-02-cand` (same 0.5/0.5 value, re-anchored semantics; HIGH-STAKES individual review) + `TCA-CARBON-FATE-01-cand` (the OAA-derived-CO2 / acetyl-retention result) | Same as B + a hero-carbon-identity claim chain crossing into the glycolysis segment's scope |
| **Teaching payoff** | Two-layer text carries the load (dramatic = simplified, teaching = precise). Risk: dramatic/teaching layers *disagree* at the CO2 nodes — pedagogically awkward | The famous isotope-surprise becomes a STAR beat: at `isocitrate_dh`/`akg_dh` the teaching text reveals "the CO2 leaving are NOT yours — they are the recycled oxaloacetate's"; the shuffle's "retained" outcome + the existing loop choices give the geometric multi-turn experience; the cycle-trap (N>5) reads naturally as the cap on the geometric tail | Best science, but double content cost + cross-segment coupling |
| **Skeleton/test impact** | None (texts are TBD) | None (texts are TBD); the seeded-run documented-fate test (§8) maps outcomes → new node meanings | Upstream skeleton/choice changes (frozen-skeleton touch) + test updates |
| **Confidence** | HIGH | HIGH (weight value already accepted by human 2026-08-15; semantics re-anchor is a per-claim HIGH-STAKES review) | MEDIUM (feasibility depends on upstream hero-identity content, out of this segment's scope) |

**Cross-boundary note (glycolysis researcher):** which glucose carbon the hero is determines which acetyl carbon it becomes (glucose C1/C6 → pyruvate C3 → acetyl **methyl**; glucose C2/C5 → pyruvate C2 → acetyl **carbonyl**; glucose C3/C4 → released as CO2 **at PDH**, never reaching TCA). If the intro/preface fixes the hero's glucose carbon, that upstream choice interacts with designs B/C. Under A/B the shuffle is hero-carbon-agnostic (a deliberate simplification stated in text).

**RNG-weight claim candidates (all HIGH-STAKES, per-claim human review):**

- `TCA-RNG-WEIGHT-02-cand` (only if B chosen): "Game-design TCA shuffle weight 0.5/0.5, re-anchored: the two outcomes model the 50/50 label-scrambling of the hero carbon at the symmetric succinate/fumarate intermediates (the cycle's genuine stochastic carbon event), determining whether the carbon is positioned to exit as CO2 when the cycle next turns or rides another turn. Value unchanged from TCA-RNG-WEIGHT-01; semantics re-anchored per the isotope-labeling carbon-fate result." Source: `WIKIPEDIA-TCA` (+ `WIKIPEDIA-ACONITASE` for the mechanism) — pending source approval.
- `TCA-CARBON-FATE-01-cand` (A or B): "Isotope-labeling result: the two CO2 released in a TCA turn derive from oxaloacetate carbons, not directly from the incoming acetyl carbons; the acetyl carbons join the oxaloacetate backbone after the first turn and their loss as CO2 requires several subsequent turns." Source: `WIKIPEDIA-TCA` (verbatim-backed) — HIGH-STAKES (carbon-fate taxonomy, PROJECT.md row 109).

---

## 3. Existing RNG claims re-verification + the prochirality source gap

Both approved claims re-verified against the live LibreTexts 16.02 page (fetched 2026-08-30, same URL as registered in `data/sources.json` LIBRETEXTS-METAB-TCA):

| Approved claim | Live re-verification (2026-08-30) | Verdict |
|---|---|---|
| `TCA-RNG-CITRATE-PROCHIRALITY-01` | 16.02 text: citrate synthase mechanism forms **"(S)-citryl CoA"** ✓; aconitase: *"This cis-aconitate intermediate … undergoes a 180° flip around the C=C double bond. This is followed by rehydration to form the other isomer."* ✓; the page does **NOT** use "prochiral" for citrate (uses "prochiral" only for NADH in the MDH hydride-transfer note) ✓ — the registered CAVEAT is accurate | **Claim stands as approved.** The gap is real but the claim_text ("citrate is prochiral; aconitase discriminates…") over-reaches what the source literally says in exactly the way the review_notes documented |
| `TCA-RNG-WEIGHT-01` | 16.02 Summary contains the *"two carbons of the original acetyl-CoA have been fully released as CO2"* shorthand ✓ (the review_notes already flagged this); the page does NOT state a 0.5/0.5 exit probability ✓ (review_notes accurate) | **Claim stands as approved** (value = human-accepted game-design decision 2026-08-15); §2 shows its literal semantics conflict with the precise isotope result — the re-anchor decision (checkpoint D1) governs whether a `…-02` supersedes it |

### 3.1 The explicit prochirality source (gap fix) — NEW CANDIDATE SOURCE

**Wikipedia "Aconitase"** (https://en.wikipedia.org/wiki/Aconitase, CC BY-SA; fetched 2026-08-30, revision 1343733503), Mechanism section, states verbatim:

> "His-101 protonates the hydroxyl group on C3 of citrate, allowing it to leave as water, and Ser-642 concurrently abstracts the proton on C2 … **The carbon atom from which the hydrogen is removed is the one that came from oxaloacetate in the previous step of the citric acid cycle, not the one that came from acetyl CoA, even though these two carbons are equivalent except that one is 'pro-R' and the other 'pro-S' (see Prochirality).** At this point, the intermediate is rotated 180° … the intermediate is said to move from a 'citrate mode' to a 'isocitrate mode.'"

This single sentence explicitly provides: (1) the **pro-R/pro-S / prochirality** wording the LibreTexts page lacks; (2) the **aconitase OAA-vs-acetyl discrimination**; (3) the **180° flip** (consistent with 16.02). Cited by Wikipedia to Stryer 1981 and Beinert/Kennedy/Stout 1996 (Chem Rev 96:2335).

**Proposed action (checkpoint D2):** add source record `WIKIPEDIA-ACONITASE` (and `WIKIPEDIA-TCA`, §5) to `data/sources.json` (license `CC BY-SA 4.0`, `source_type: encyclopedia_open`), and either (a) extend `TCA-RNG-CITRATE-PROCHIRALITY-01`'s source list with the co-citation (registry edit + human re-approval of the widened source set) or (b) file `TCA-RNG-CITRATE-PROCHIRALITY-02-cand` with the dual citation and retire `-01`. Option (a) is minimal; option (b) keeps per-claim immutability clean. **Recommendation: (a)** — the claim text itself was approved; only the *supporting* source set widens.

Also verified on the same page: aconitase catalytic residues **His101 + Ser642** (pig/bovine numbering — matches the 7ACN/1C97 structures the LibreTexts page models; see §7 numbering caveat); Fe₄S₄ cluster with the labile Fe coordinated by water; inhibited by fluorocitrate (fluoroacetate poisoning) — usable as optional bad-ending/teaching color, NOT required.

---

## 4. Per-node claim inventory (all 12 `tca.json` nodes)

Registry status key: ✅ = approved in `data/citations.json`; cand = referenced in skeleton but NOT in registry (CANDIDATE pending Phase 7 per-claim approval); NEW = proposed here. Tier per the hybrid workflow (PROJECT.md row 109): HIGH-STAKES = RNG-weights/carbon-fate/contested → individual review; ROUTINE = enzyme-catalyzes-X / name/EC/cofactor / PDB existence-resolution / pathway ordering → source-inherited fast-track + `review_tier:"routine"`.

All reaction/energetics/cofactor facts below are verified in the live LibreTexts 16.02 fetch (ΔG°′ values, mechanisms, cofactors) and belong to the already-approved `LIBRETEXTS-METAB-TCA` source → routine-tier claims inherit its approval. Claim-id convention: `TCA-<ENZYME>-01` / `TCA-<TOPIC>-01` (matches `TCA-RNG-WEIGHT-01`, `DIS-<GENE>-01-cand` precedents).

| # | Node | Text layers need (grounding bullets) | Proposed claim_ids (tier) | Registry status |
|---|------|--------------------------------------|---------------------------|-----------------|
| 1 | `tca.entry` | Acetyl-CoA enters the cycle; condensation with OAA is the entry; the cycle is the hub of respiration; hero rides *inside the acetyl group* (anti-confusion: hero = carbon atom, C14 = label) | `TCA-ENTRY-01` (ROUTINE): "Acetyl-CoA delivers a 2-carbon acetyl group to the TCA cycle, condensing with oxaloacetate to form citrate" (LibreTexts 16.02 Introduction; Wikipedia-TCA). Optional `TCA-CARBON-FATE-01-cand` here or at the CO2 nodes | `PLACEHOLDER_PHASE7_TCA` → replace |
| 2 | `tca.citrate_synthase` | Reaction OAA + acetyl-CoA + H₂O → citrate + CoA-SH, ΔG°′ = −7.5 kcal/mol (thioester hydrolysis drives it); induced-fit open→closed; mechanism Asp375/His274/His320/Arg329 (⚠ pig-CS numbering — see §7 caveat); **(S)-citryl-CoA intermediate**; enzyme is a functional **homodimer** (see dimer convention D7); edit:structural (no disease point mutant — re-verified, §6.1) | Keep `CAST-CSC-PDB-01` ✅ + `TCA-RNG-CITRATE-PROCHIRALITY-01` ✅; NEW `TCA-CS-01` (ROUTINE): "Citrate synthase condenses oxaloacetate + acetyl-CoA → citrate via an (S)-citryl-CoA intermediate (ΔG°′ = −7.5 kcal/mol, driven by thioester hydrolysis)" (LibreTexts 16.02 §1) | ✅ + `PLACEHOLDER_PHASE7_TCA` → `TCA-CS-01` |
| 3 | `tca.aconitase` | Citrate ⇌ isocitrate via cis-aconitate; Fe₄S₄ cluster (labile Fe binds substrate); **180° flip of cis-aconitate**; **pro-R/pro-S discrimination** (OAA-derived arm acted on — Wikipedia-Aconitase sentence, §3.1); ΔG°′ ≈ +1.5 kcal/mol net (readily reversible); disease story: ACO2 S112R → ICRD (host going blind/losing motor control); PDB species decision D6 | `TCA-RNG-CITRATE-PROCHIRALITY-01` ✅ (+ optional Wikipedia co-citation, D2); `DIS-ACO2-01-cand` → file as `DIS-ACO2-01` (HIGH-STAKES — contested-ish disease claim; evidence re-verified live §6.2) ; NEW `TCA-ACONITASE-01` (ROUTINE): "Aconitase isomerizes citrate → isocitrate via cis-aconitate with a 180° flip, using an Fe₄S₄ cluster (ΔG°′ ≈ +1.5 kcal/mol)" | `DIS-ACO2-01-cand` (unregistered) + TBD_ACONITASE load placeholder |
| 4 | `tca.shuffle` | THE RNG node. Design B teaching text: the hero carbon passes through symmetric succinate/fumarate; a 50/50 scramble decides exit-position vs ride-again; the *only* genuinely random carbon event; grounded by prochirality (aconitase acts on the OAA arm — so the acetyl carbons' fate is deferred, not immediate) + the isotope result (§2.1). Cycle-trap choice is a game-design cap (OQ3, N=5, NOT a science claim — keep that framing) | Per D1: keep `TCA-RNG-WEIGHT-01` ✅ + `TCA-RNG-CITRATE-PROCHIRALITY-01` ✅ (Design A) OR supersede with `TCA-RNG-WEIGHT-02-cand` + `TCA-CARBON-FATE-01-cand` (Design B) — both HIGH-STAKES | ✅ (both approved; supersede = new files) |
| 5 | `tca.co2_turn1` | Design A: naive exit text + teaching correction. Design B: "the wheel put your carbon in an exit position" — the next decarboxylations release CO2 (the pool's, per the isotope surprise); loop choice = ride again (the geometric tail); forward choice = continue the story (your exit comes later — honest text) | `TCA-CARBON-FATE-01-cand` (HIGH-STAKES) + `TCA-IDH3-01` (ROUTINE, see row 7) | `PLACEHOLDER_PHASE7_TCA` → replace |
| 6 | `tca.co2_turn2` | Mirror of row 5 (Design B: the "retained" outcome — "the wheel kept you aboard"; teaching: your carbon now rides the 4-C acids; every future pass is a fresh 50/50) | Same as row 5 | `PLACEHOLDER_PHASE7_TCA` → replace |
| 7 | `tca.isocitrate_dh` | IDH3 (NAD⁺-dependent, mitochondrial, α₂βγ; α = catalytic subunit; activated by citrate/ADP — allosteric) oxidizes isocitrate → α-KG + CO₂ + NADH; ΔG°′ ≈ −2.0 kcal/mol; **rate-limiting/regulatory step of the cycle** (⚠ Wikipedia table marks the decarboxylation row "rate-limiting, irreversible"; LibreTexts 16.03 Regulation page covers regulation — verify the exact "rate-limiting IDH" wording against 16.03 before filing; MEDIUM-HIGH until checked); **the isotope-surprise beat**: the CO2 leaving is not necessarily yours (Design B); disease: IDH3A M204I → RP90; IDH1-R132H alternative declined (D4) | `DIS-IDH3A-01-cand` → file as `DIS-IDH3A-01` (HIGH-STAKES disease claim; M204I ClinVar-Pathogenic live-verified §6.3); NEW `TCA-IDH3-01` (ROUTINE): "Isocitrate dehydrogenase (NAD⁺-dependent, mitochondrial) oxidatively decarboxylates isocitrate → α-KG + CO₂ + NADH" | `PLACEHOLDER_PHASE7_TCA` + `DIS-IDH3A-01-cand`; PDB 5GRF→5GRE swap (D3) |
| 8 | `tca.akg_dh` | α-KG + NAD⁺ + CoA-SH → succinyl-CoA + CO₂ + NADH; ΔG°′ ≈ −7.2 kcal/mol; mechanistically homologous to PDH (same E1/E2/E3 architecture; TPP/lipoamide/FAD cofactors — LibreTexts explicitly cross-references 16.1); narrative-only node (Decision 2, NO PDB — frozen). Promotion question = D5 | NEW `TCA-OGDH-01` (ROUTINE): "α-Ketoglutarate dehydrogenase oxidatively decarboxylates α-KG → succinyl-CoA + CO₂ + NADH (E1/E2/E3 complex homologous to PDH; TPP/lipoamide/FAD)" (+ optional `DIS-OGDH-01-cand` if promoted, §6.6) | `PLACEHOLDER_PHASE7_TCA` → replace |
| 9 | `tca.succinyl_coa_synthetase` | Succinyl-CoA + GDP + Pi → succinate + GTP + CoA-SH; ΔG°′ ≈ −0.8 kcal/mol; the ONLY substrate-level phosphorylation in the cycle; phosphohistidine intermediate (His246 in E. coli numbering — caveat); GTP⇄ATP transphosphorylation; mammals have GDP- and ADP-forming isoforms (Wikipedia Variation — optional color); disease: SUCLG1 G85A → MTDPS9 | `DIS-SUCLG1-01-cand` → file as `DIS-SUCLG1-01` (HIGH-STAKES; re-verified §6.4); NEW `TCA-SCS-01` (ROUTINE): "Succinyl-CoA synthetase converts succinyl-CoA → succinate, coupling thioester cleavage to GTP synthesis — the cycle's only substrate-level phosphorylation" | `PLACEHOLDER_PHASE7_TCA` + `DIS-SUCLG1-01-cand` |
| 10 | `tca.fumarase` | Fumarate + H₂O ⇌ L-malate; stereospecific trans-hydration; ΔG°′ ≈ −0.9 kcal/mol; class-II enzyme; disease: FH R233H → HLRCC (catalytically inactive — the strongest candidate, multi-submitter) | `DIS-FH-01-cand` → file as `DIS-FH-01` (HIGH-STAKES; re-verified §6.4; rsID correction noted); NEW `TCA-FH-01` (ROUTINE): "Fumarase (fumarate hydratase) reversibly hydrates fumarate → L-malate (stereospecific trans-addition)" | `PLACEHOLDER_PHASE7_TCA` + `DIS-FH-01-cand` |
| 11 | `tca.malate_dh` | L-malate + NAD⁺ ⇌ OAA + NADH + H⁺; ΔG°′ = +7.1 kcal/mol (unfavorable — pulled forward by citrate synthase; textbook coupling example); regenerates OAA, closing the cycle; third NADH of the turn; MDH1 cytosolic / MDH2 mitochondrial isoforms; disease: MDH2 G37R → DEE51; loop choice → shuffle; forward → divert | `DIS-MDH2-01-cand` → file as `DIS-MDH2-01` (HIGH-STAKES; re-verified §6.4); NEW `TCA-MDH2-01` (ROUTINE): "Malate dehydrogenase oxidizes L-malate → oxaloacetate + NADH (ΔG°′ = +7.1 kcal/mol, driven by citrate-synthase pull); regenerates the cycle's OAA acceptor" | `PLACEHOLDER_PHASE7_TCA` + `DIS-MDH2-01-cand` |
| 12 | `tca.divert_to_good` | Branch-point: follow the soul to the ETC vs divert the carbon body. Grounding: the cycle is **amphibolic**; intermediates are **withdrawn for biosynthesis** (16.02 Summary: "amino acids, heme, nucleotides, and lipids"); the two real cataplerotic exits offered = citrate-export→FA synthesis + OAA/α-KG→amino acids (§5). Anti-confusion: diverting = the CARBON body exits pre-oxidation (Good); the ETC path = electrons (soul) continue, carbon eventually shed as CO2 | `TCA-AMPHIBOLIC-01` (ROUTINE): "The TCA cycle is amphibolic: its intermediates are withdrawn (cataplerotic) for biosynthesis — citrate for lipid synthesis, oxaloacetate/α-KG for amino-acid synthesis" — sources: Wikipedia-TCA ("cataplerotic" verbatim) + LibreTexts 16.02 Summary + 16.04 | `PLACEHOLDER_PHASE7_TCA` → replace |

**Ending-node claims owned by this segment** (files live in endings.json — text is another researcher's; the CLAIMS are ours per the brief):

| Node | Claim grounding | Proposed claim_ids (tier) |
|---|---|---|
| `end.good.fatty_acid` | Citrate exits the mitochondrion (acetyl-CoA cannot cross the inner membrane); cytosolic ATP-citrate-lyase cleaves citrate → acetyl-CoA + OAA; OAA returns as malate; cytosolic acetyl-CoA → fatty-acid/cholesterol synthesis. **Carbon retained pre-oxidation = Good.** Verified: Wikipedia-TCA §Intermediates (verbatim, uses "cataplerotic") + LibreTexts 16.04 ("citrate lyase cleaves citrate to form acetyl-CoA, which is used for fatty acid synthesis") | `TCA-CITRATE-EXPORT-01` (ROUTINE; both sources; scope = EXIT EVENT only — full FA-synthesis chemistry is Phase 8's character per the brief) |
| `end.good.amino_acid` | OAA → aspartate/asparagine; α-KG → glutamate/glutamine/proline/arginine; transamination: α-keto-acid + glutamate → amino acid + α-KG (PLP cofactor; Glu donates the amino group and becomes α-KG — a cycle intermediate). **Carbon skeleton retained = Good.** Verified: Wikipedia-TCA §Intermediates (verbatim) + 16.04 (GABA-shunt transaminase + "α-ketoacids … converted by transamination" note) | `TCA-TRANSAMINATION-01` (ROUTINE): "TCA intermediates provide carbon skeletons for amino-acid synthesis via transamination (OAA→Asp/Asn; α-KG→Glu/Gln/Pro/Arg; PLP-dependent)" |
| `end.normal.co2` | The unremarkable oxidation exit: carbon leaves as CO2 without the electron-harvest arc (narrative tier, not a separate biochemical path — the existing NARRATIVE-FRAMING FLAG in endings.json is consistent). Grounding: per-turn CO2 release (16.02 net equation) + Wikipedia carbon-fate sentence (the carbon eventually leaves as CO2 across turns) | `TCA-CO2-EXIT-01` (ROUTINE): "Each turn of the cycle releases 2 CO2 (net: acetyl-CoA + 3NAD⁺ + FAD + GDP + Pi + 2H₂O → 2CO₂ + 3NADH + FADH₂ + GTP …)" (16.02 Summary-of-the-Cycle net equation, verified verbatim) |

**Anti-confusion guardrails for the authors (mandatory, from AGENTS.md + PROJECT.md row 107):** the hero's electrons = soul → ETC → ATP; the carbon body is shed as CO2; NEVER write that the C14 carbon becomes ATP, becomes NADH, or "enters oxidative phosphorylation"; C14 = tracking label. At the cataplerotic good exits the framing is "your carbon body lives on" (retained); at the ETC path the framing is "your soul (electrons) journey on; your carbon body is shed." Keep the two framings separate (05.4-CONVENTION §3.6 template applies verbatim).

---

## 5. Cataplerotic good-exit claims (OQ4) — verified sources

Both exits are real, citable, license-clear, and (partly) already inside the approved source volume:

1. **Wikipedia "Citric acid cycle" → §"Intermediates as substrates for biosynthetic processes"** (fetched 2026-08-30; CC BY-SA) — uses the word **"cataplerotic"** verbatim: *"Several of the citric acid cycle intermediates are used for the synthesis of important compounds, which will have significant **cataplerotic** effects on the cycle."* Then, verbatim:
   - FA exit: *"Acetyl-CoA cannot be transported out of the mitochondrion. To obtain cytosolic acetyl-CoA, **citrate** is removed from the citric acid cycle and carried across the inner mitochondrial membrane into the cytosol. There it is cleaved by **ATP citrate lyase** into acetyl-CoA and oxaloacetate. The oxaloacetate is returned to mitochondrion as **malate** … The cytosolic acetyl-CoA is used for **fatty acid synthesis** and the production of cholesterol."*
   - Amino-acid exit: *"The carbon skeletons of many non-essential amino acids are made from citric acid cycle intermediates … [the] alpha keto-acids … acquire their amino groups from **glutamate** in a **transamination** reaction, in which **pyridoxal phosphate** is a cofactor … **oxaloacetate** … forms **aspartate and asparagine**; and **alpha-ketoglutarate** … forms **glutamine, proline, and arginine**."*
   - Amphibolic framing: *"Because the citric acid cycle is involved in both catabolic and anabolic processes, it is known as an **amphibolic** pathway."*
2. **LibreTexts Jakubowski & Flatt 16.04 (Variants of the Citric Acid Cycle)** — inside the ALREADY-APPROVED volume `LIBRETEXTS-METAB-TCA` (fetched 2026-08-30): *"In another anaplerotic reaction, **citrate lyase cleaves citrate to form acetyl-CoA, which is used for fatty acid synthesis** required by rapidly proliferating cells"* (cancer/reductive-carboxylation context) + *"The metabolites formed can be utilized for biosynthesis (OAA, α-KG, and succinyl-CoA)"* (glyoxylate-shunt intro) + the GABA-shunt transamination example (GABA transaminase + α-KG → glutamate + succinic semialdehyde).
3. **LibreTexts 16.02 Summary** (same approved volume): *"Because several cycle intermediates are continuously withdrawn for biosynthesis (of **amino acids**, heme, nucleotides, and **lipids**), a linear pathway would rapidly deplete its intermediates and halt"* + the anaplerotic replenishment logic.
4. **Bonus teaching point from 16.04** (grounds the Good-vs-Normal distinction): *"2 Cs enter the cycle as acetyl-CoA and two leave as CO2, so that no net synthesis can occur [from acetyl-CoA alone]"* — why the *intermediate-exit* (not the acetyl-exit) is the carbon-retaining fate.

**Scope discipline (per the brief):** claims cover the EXIT EVENT only (citrate export → cleavage → cytosolic acetyl-CoA destined for FA synthesis; OAA/α-KG → amino-acid carbon skeletons). The downstream FA-synthesis chemistry (Phase 8 fatty-acid character) and the amino-acid products' fates are OUT of this segment's claims.

**New source record needed:** `WIKIPEDIA-TCA` (https://en.wikipedia.org/wiki/Citric_acid_cycle, CC BY-SA 4.0) — required only if the explicit "cataplerotic" wording / ATP-citrate-lyase naming / Asp-Gln specificity wording is wanted in teaching text; otherwise the LibreTexts-volume claims (2)(3) alone suffice as routine-tier source-inherited claims. Recommendation: add the Wikipedia source — the verbatim wording is materially better for teaching text, and §2/§3 need Wikipedia sources anyway (one approval covers three claims).

---

## 6. Disease-mutant verification pass (live, 2026-08-30)

All via UniProt REST flat-text + NCBI ClinVar E-utilities (the Phase 5.1 toolset). Every candidate below is mechanical-compatible with `cmd.alter` point_mutation (all are single-residue missense). Reverse-mutation signatures for `rpg/data/edits.json` follow the Phase 5.1 proposals, now re-verified. Numbering caveats in §6.7.

### 6.1 Citrate synthase (CS, O75390) — negative RE-CONFIRMED
UniProt live fetch: **0 natural variants, no disease block.** The Phase 5.1 finding stands (all 7 ClinVar Pathogenic records are structural variants — inversions/CN-gains, not implementable via `cmd.alter`). `tca.citrate_synthase` stays **edit:structural** (no DIS- claim, no edits.json entry). No action beyond keeping the reframe.

### 6.2 Aconitase (ACO2, Q99798) — RE-CONFIRMED live
UniProt live fetch (2026-08-30): variants **S112R** (ICRD), **G259D** (ICRD, rs786204828), **K736N** (ICRD, rs786204829), **L74V** (OPA9, rs141772938), **G661R** (OPA9, rs752034900), T697N (somatic, breast-cancer sample); diseases **ICRD [MIM:614559]** + **OPA9 [MIM:616289]**. → File `DIS-ACO2-01` (S112R → reverse R112S; ICRD narrative) as HIGH-STAKES. Optional stronger alternative kept from Phase 5.1: G259D → D259G.

### 6.3 Isocitrate DH (IDH3A, P50213) — RE-CONFIRMED live (both layers)
- UniProt live fetch: 8 RP90 variants (A122T, A175V, **M204I**, M239T, P304H, M313T, **R316C**, Δ155-366) — UniProt labels the missense "uncertain significance" (STALE, as Phase 5.1 established).
- ClinVar live (esearch+esummary 2026-08-30): IDH3A pathogenic missense count = **9 records**; spot-verified: **M204I (VCV 977473) = Pathogenic**, **R316C (VCV 977472) = Pathogenic**, A175V (977470) = Pathogenic, M239T (977468) = Pathogenic; A122T = Conflicting.
- **IDH3A-vs-IDH1 tradeoff (checkpoint D4):** IDH3A = the actual NAD⁺-dependent mitochondrial TCA enzyme (faithful; skeleton default since Phase 5.1; ClinVar-Pathogenic confirmed) vs IDH1 R132H = the famous glioma oncomutation (UniProt O75874 live: R132H "in a glioma sample … abolishes magnesium binding", + real mutant PDB 3INM) — but IDH1 is the cytosolic NADP⁺ isoform, NOT the TCA enzyme, and would require re-framing the node's enzyme identity. **Recommendation: keep IDH3A default** (Phase 5.1 human-confirmed); optionally add a side teaching mention of IDH1-R132H (a separate claim if any text asserts it — not needed for the TCA node itself).

### 6.4 SUCLG1 (P53597), FH (P07954), MDH2 (P40926) — RE-CONFIRMED live
- **SUCLG1:** variants M14L (MTDPS9+liver), G37A (no disease note), **G85A (MTDPS9, rs267607097)**, **P170R (MTDPS9, rs267607099)**. → File `DIS-SUCLG6-01` naming note: use **`DIS-SUCLG1-01`** (G85A → reverse A85G; MTDPS9, OMIM 245400).
- **FH:** variants N107T, A117P, H180R, Q185R, K230R (FMRD+HLRCC), **R233H (HLRCC; "catalytically inactive mutant; abolished ability to promote DNA repair"; dbSNP:rs121913123)**, G282V, A308T (FMRD), F312C (FMRD), M328R, + more. **rsID CORRECTION vs Phase 5.1:** R233H = **rs121913123** (Phase 5.1 wrote rs121913121, which belongs to N107T per the live fetch). → File `DIS-FH-01` (R233H → reverse H233R; HLRCC OMIM 150800 / FMRD OMIM 606812) — the strongest evidence tier of the set (multi-submitter ClinVar Pathogenic + explicit functional annotation).
- **MDH2:** variants **G37R (DEE51; "severe defects in aerobic respiration… when assayed in a heterologous system"; rs782308…)**, **P133L (DEE51; "decreased protein abundance; strong decrease in malate dehydrogenase activity")**, P207L (DEE51). → File `DIS-MDH2-01` (G37R → reverse R37G; DEE51 OMIM 617339).

### 6.5 α-KG DH (OGDH, Q02218) — the owed deeper scan: **NEGATIVE OVERTURNED**
- UniProt live: disease block EMPTY; 1 variant (V1018I, no disease note).
- ClinVar live deeper scan (2026-08-30, full pathogenic-missense query — NOT just the trait-tagged first-14 of Phase 5.1): **4 Pathogenic missense records**:
  - **P189L** (c.566C>T, VCV002443831) — verified via the live ClinVar page: Pathogenic (1 submission, literature-only, **no assertion criteria provided**); condition **Oxoglutaricaciduria / oxoglutarate dehydrogenase deficiency (OGDHD)**; OMIM cross-ref **613022.0003** (gene OGDH MIM 613022; phenotype 203740); evidence: homozygous in an Ashkenazi-Jewish patient (Whittle et al. 2023, *Genetics in Medicine*, **PMID 36520152** — "Biallelic variants in OGDH … lead to a neurodevelopmental disorder characterized by global developmental delay, movement disorder, and metabolic abnormalities"); HEK293 expression → unstable protein.
  - **R312K** (c.935G>A, VCV 2443832), **S297Y** (c.890C>A, 2443830), **N320S** (c.959A>G, 1331346) — all Pathogenic (same esearch batch; same Whittle-2023 literature cluster presumed — VERIFY per-record before filing any of these three).
- **Mechanical compatibility:** all missense → `cmd.alter`-compatible ✓. `tca.akg_dh` is narrative-only (no PDB load) so no PDB-numbering mapping is needed — UniProt/MANE numbering (NP_002532.2 = MANE Select) is authoritative.
- **Evidence-strength caveat:** single-submitter, no assertion criteria, literature-only — weaker than FH's multi-submitter tier. Frame in text as "a confirmed pathogenic mutation" only after the human approves the claim; keep the caveat in review_notes.

### 6.6 akg_dh promotion decision (checkpoint D5)
Promoting `tca.akg_dh` to edit-allowed (adding `edit:enzyme:tca.akg_dh` + an edit:offer choice) **breaks the frozen Phase 5.1 invariant** (`test_14_edit_allowed_nodes` asserts exactly 14 edit-allowed nodes with an exact id set; would become 15 + test edits + DESIGN.md diagram updates). Options:
- **(a) Keep narrative-only (RECOMMENDED default):** file the OGDH finding as `DIS-OGDH-01-cand` in the registry as a documented candidate; no skeleton change; the teaching text can still *mention* OGDH deficiency as a real human disease with an approved claim (text-layer only, no edit mechanics).
- **(b) Promote:** new claim approval + skeleton tag/choice edits + invariant-test update (14→15) + DESIGN.md + diagram regeneration. Cost: touches the FROZEN 5.1 skeleton invariants for an evidence-weaker claim.

### 6.7 Numbering caveats for edits.json authoring
- **ACO2 (aconitase):** the cast PDB is non-human (D6: 1ACO bovine / 7ACN pig). Human S112R numbering ≠ PDB residue number. Phase 5.1 OQ5 (bovine↔human S112 mapping via sequence alignment before writing the `resi <N>` signature) REMAINS OPEN and is now load-bearing for `edits.json`. The 05.3 `align` convention machinery is the intended reconciliation path. Live-verified anchor: the catalytic Ser642 (pig/bovine aconitase numbering, per Wikipedia mechanism + 1C97 S642A) has a human ACO2 counterpart near the C-terminus — the alignment must be done on real sequences in Phase 7 before any `resi` signature is written. **Do not author the aconitase `edits.json` entry on assumed identity-of-numbering.**
- **IDH3A (5GRF/5GRE):** human structures; α chain = catalytic. M204I sits in the α subunit (UniProt P50213 numbering = MANE/NP_002532.2-equivalent); 5GRF/5GRE α-chain author numbering vs UniProt needs a 1-check mapping (constructs may carry tags/offsets) — same class of check as PDH 6CFO in 5.1.
- **SUCLG1 (6WCV), FH (5UPP), MDH2 (2DFD/4WLU):** human structures; expect minor construct offsets; verify with a targeted `cmd.iterate` resn/resi check at the mutation position during content authoring (headless-verifiable via run-conda-pymol.bat).
- **OGDH:** no PDB load (narrative-only) → UniProt numbering only, no mapping needed.

---

## 7. PDB verification (RCSB live, 2026-08-30)

| PDB | Live verification | Verdict for the cast |
|---|---|---|
| **1CSC** (approved `CAST-CSC-PDB-01`) | Title: "Structure of ternary complexes of citrate synthase with D- and L-malate: Mechanistic implications"; **1.70 Å**; deposited 1990-05-07 (Karpusas et al. 1991 paper — matches approved claim); organism *Gallus gallus* (UniProt P23007); **AU = 1 polymer chain; biological assembly 1 = HOMODIMER (2 chains, "author_and_software_defined_assembly")** | ✅ Stands. The **CS-dimer convention** (queued from Phase 6 close-out) is now concrete: loading `pdb:1CSC` via the existing molops gives the AU monomer; the dimer requires either the assembly mechanism (PyMOL `assembly` setting before load — verified present in bundled source `importing.py:1554-1563`; would be an AssetManager/molops code change = OUT of Phase-7 data scope) or a teaching-note monomer. Decision D7 |
| **1ACO** | Bovine (*Bos taurus*, P20004) mitochondrial aconitase, 2.05 Å, trans-aconitate bound, Lauble et al. 1994 (PMID 8151704) | ✅ Matches Phase 5.1 + skeleton note. Species/homology caveat stands (D6) |
| **7ACN** | **PIG** (*Sus scrofa*, P16276) aconitase, 2.0 Å, **isocitrate + nitroisocitrate bound**, Lauble/Kennedy/Beinert/Stout 1992 (PMID 1547214) | ✅ Verified as pig (memory said unverified — now confirmed). Alternative for D6: shows the PRODUCT (isocitrate) at the active site |
| **1C97** | Bovine **S642A mutant** aconitase with citrate, 1.8 Å (Lloyd et al. 1999; the LibreTexts iCn3D teaching model) | ⚠ Catalytic-site MUTANT structure — using it as the cast would re-create the 2OZL problem. Only viable with explicit mutant disclosure. NOT recommended as cast |
| **2B3Y** | **Human CYTOSOLIC aconitase = ACO1/IRP1** ("monoclinic crystal form of human cytosolic aconitase (IRP1)"), 1.85 Å | ❌ **WRONG ISOFORM** — not mitochondrial ACO2; do NOT use for the TCA cast (the brief's open question answered) |
| Human ACO2 | UniProt Q99798 live cross-ref query: **0 PDB entries** (re-confirmed 2026-08-30) | The `pdb:TBD_ACONITASE` placeholder MUST resolve to a non-human structure (or a homology model — out of scope); homology caveat text mandatory |
| **5GRF** (skeleton's isocitrate_dh load) | "Crystal structure of the **alpha gamma mutant (gamma-K151A)** of human IDH3 in complex with Mg²⁺, citrate and ADP", 2.5 Å | ⚠ MUTANT structure (γ regulatory subunit K151A; catalytic α is WT). Mirrors the 2OZL→6CFO precedent → D3 |
| **5GRE** | "Crystal structure of the **alpha gamma heterodimer of human IDH3** in complex with Mg²⁺, citrate and ADP" (WT), 2.65 Å | ✅ WT companion from the same 2017 group — RECOMMENDED swap for D3 |
| 6KDY | Human IDH3 **αβ** heterodimer with NAD⁺ (WT), 3.02 Å | Alternative (WT; shows NAD⁺; lower resolution; β not γ — the αγ dimer is the citrate/ADP-regulated form) |
| 5YVT | Human IDH3 αγ with Mg²⁺ + NADH, 2.4 Å | Alternative (WT; NADH-bound) |
| **6WCV** | "Tartryl-CoA bound to human GTP-specific succinyl-CoA synthetase", 1.52 Å | ✅ Human SUCLG1, excellent resolution (ligand = tartryl-CoA analog — disclose in teaching text if the ligand is shown) |
| **5UPP** | "Crystal structure of human fumarate hydratase", 1.8 Å | ✅ |
| **2DFD** | "Crystal Structure of Human Malate Dehydrogenase Type 2", 1.9 Å | ✅ |
| 4WLU | Human MDH2 with L-malate + NAD⁺ bound, 2.14 Å (LibreTexts' own teaching model) | Alternative to 2DFD — substrate+cofactor visible (pedagogically richer; slightly lower res). Optional D-swap, low priority |

**Also verified on 16.02 (for teaching text, not necessarily new claims):** LibreTexts itself models pig CS (2CTS), bovine S642A aconitase (1C97), human IDH1 (4L03) + human IDH3 αβ (6KDY), E. coli SCS (1CQI), pig SCS (5CAE), avian Complex II (1YQ3), E. coli fumarase (1FUQ), human MDH2 (4WLU) — a useful cross-check that our candidate PDB choices are mainstream teaching structures.

---

## 8. RNG mechanics cross-check — what is data vs code

**Read:** `rpg/rng.py`, `rpg/engine.py`, `rpg/story/interpreter.py` (pick_choice), `tests/test_rng.py`, `tests/test_engine.py`, `tests/test_integration.py`, `tests/test_glucose_reachability.py`, `tools/controller_integration_smoke.py`.

**Weights are pure data.** `tca.shuffle`'s two weighted choices carry `weight: 0.5` in JSON. `StoryInterpreter.pick_choice` (interpreter.py:43-71): if any eligible choice has a weight and the total > 0, the interpreter returns exactly one choice picked deterministically via the seeded `RngEngine` (cumulative-weight walk over `rng.random()*total`); the player's index is ignored. The `edit:offer` + cond-gated `cycle_trap` choices ride alongside via `GameEngine.goto` (engine.py:179-193; the Phase 6 "tca.shuffle auto-spin/auto-fire" user decision). **Any of the §2 designs needs ZERO engine/interpreter code changes** — weights, texts, claim_ids, and (if chosen) re-anchored labels are all JSON.

**What exists for seeded determinism today:**
- `tests/test_rng.py` — engine-level: same-seed-identical-sequence, diff-seed divergence, weighted_pick determinism, JSON state round-trip.
- `tests/test_engine.py` — weighted autopick determinism on the real `data/story` graph (same seed → same ending; index ignored on weighted nodes).
- `tests/test_integration.py:186-221` — toy-graph: same seed → same ending tier + identical MolAction sequence; across seeds 0..30 both endings appear.
- `tools/controller_integration_smoke.py` — **REAL glucose graph, seed=42**: starts a glucose game, walks to `tca.shuffle`, auto-spins (user decision 1, 2026-08-30), asserts visit counting + ending; end-to-end True-ending walk.
- `tests/test_glucose_reachability.py` — the 55-node/21-ending structural invariants (14 edit-allowed; 0 single-Continue; CS edit:structural reframe; cond-syntax guards).

**What Phase 7 must add (SC2: "a seeded run produces a documented, reproducible fate"):**
- A **unit test on the real glucose graph** with a fixed seed that (1) runs the deterministic walk through `tca.shuffle`, (2) asserts the DOCUMENTED outcome (which weighted branch at the shuffle, e.g. "seed=42 → goto tca.co2_turn1"), and (3) asserts the ending tier reached. Mechanically identical to `test_engine.py`'s pattern, pointed at `data/story_glucose`. If Design B is chosen, the documented fate's *meaning* changes (exit-position vs retained) — write the test AFTER D1 is decided, and document the mapping in the test docstring.
- Optionally: extend `tools/demo_playthrough.py` output to print the shuffle fate (classroom reproducibility aid — data/print-level change only).

**Data vs code boundary for the whole TCA segment (constraint honored):**
- DATA (all Phase 7 work): `data/story_glucose/tca.json` (texts, claim_ids, tags, weights, on_enter MolActions within the frozen op vocabulary), `data/story_glucose/endings.json` claim_ids, `data/citations.json` + `data/sources.json` (new claims + sources), `rpg/data/edits.json` (real TCA enzyme entries replacing the fixture), `rpg/data/cast.json` (real TCA cast rows), tests.
- CODE-ADJACENT (flag, do NOT plan inside Phase 7 content plans unless the human expands scope): (a) biological-assembly loading for the 1CSC dimer (`assembly` setting before fetch — `importing.py:1554-1563`; touches AssetManager/molops); (b) the aconitase bovine↔human residue mapping is content-adjacent (a one-off alignment artifact + the 05.3 align machinery — no new code, but a headless-verification script would call `cmd.*` directly like the 5.3 smoke precedent).

---

## 9. Candidate sources table (for human approval — NOTHING here is approved)

| Proposed source_id | Reference | URL | License | Covers (would ground) | Status |
|---|---|---|---|---|---|
| `WIKIPEDIA-TCA` | Wikipedia, "Citric acid cycle" | https://en.wikipedia.org/wiki/Citric_acid_cycle | CC BY-SA 4.0 | Carbon-fate isotope result (verbatim, §2.1); "cataplerotic" + citrate-export/ATP-citrate-lyase/FA-synthesis (verbatim, §5); transamination amino-acid exits (verbatim); amphibolic; per-turn stoichiometry; IDH "rate-limiting" table note; SCS GDP/ADP isoforms | **Candidate — needs approval** (fetched + quoted live 2026-08-30) |
| `WIKIPEDIA-ACONITASE` | Wikipedia, "Aconitase" | https://en.wikipedia.org/wiki/Aconitase | CC BY-SA 4.0 | Explicit pro-R/pro-S prochirality of citrate's two carboxymethyl carbons; aconitase acts on the OAA-derived carbon (verbatim, §3.1); 180° flip / citrate-mode→isocitrate-mode; His101/Ser642 catalytic residues; Fe₄S₄ | **Candidate — needs approval** (fetched + quoted live 2026-08-30) |
| `LIBRETEXTS-METAB-TCA` (existing, sections 16.03 + 16.04 added to scope) | Jakubowski & Flatt Vol. II Ch 16 (16.02 re-verified; 16.04 fetched) | registered URL + 16.04 subpage | CC BY-SA 4.0 (volume-level; per-page "not declared" metadata gap already documented in the registered notes) | 16.04: citrate-lyase→FA-synthesis (verbatim §5); GABA-shunt transamination; anaplerotic/cataplerotic framing; "no net synthesis from acetyl-CoA". 16.03: IDH regulation (NOT yet fetched — fetch before filing any 16.03-grounded claim) | Existing source approved; **16.04 section-coverage re-verified 2026-08-30**; 16.03 unfetched |
| `PMID-36520152` (Whittle et al. 2023, Genetics in Medicine) | "Biallelic variants in OGDH … neurodevelopmental disorder" | via ClinVar VCV002443831 links | journal article (citation of record, license not required for a factual claim citation — matches how ClinVar/OMIM refs are used elsewhere) | OGDH P189L pathogenic, OGDHD phenotype, unstable-protein functional evidence | **Candidate — needs approval only if akg_dh text mentions OGDH deficiency** (verified via live ClinVar page 2026-08-30) |
| `PDB-1ACO` / `PDB-7ACN` / `PDB-5GRE` / `PDB-6WCV` / `PDB-5UPP` / `PDB-2DFD` (+ optional 4WLU, 6KDY, 5YVT) | RCSB entries | rcsb.org/structure/&lt;ID&gt; | structural database (CC0-style PDB data) | Cast claims (`CAST-*-PDB-01` pattern: species/resolution/citation all live-verified §7) | **Candidates — one per cast PDB actually loaded** (mirror `PDB-4PFK`/`PDB-1CSC` precedent: routine-tier, source-inherited) |

**Rejected/avoided (consistent with existing policy):** Lehninger print textbook (license — already registered as rejected); 1C97 as cast (catalytic-site S642A mutant — same class of problem as the rejected 2OZL pyr.pdh cast); 2B3Y (wrong isoform).

---

## 10. Human decision checkpoints (numbered, with options)

**D1 — Shuffle→CO2 semantics (HIGH-STAKES, carbon-fate; the biggest decision).** Which design (§2.2)?
- (a) **Design A** — keep approved claim semantics; add an explicit simplification note in teaching text (optionally + `TCA-CARBON-FATE-01-cand`). Minimal files, maximal continuity with the 2026-08-15 approvals.
- (b) **Design B (RECOMMENDED)** — re-anchor the shuffle to the succinate-symmetry scramble (supersede `TCA-RNG-WEIGHT-01` with `-02` same-value claim + `TCA-CARBON-FATE-01-cand`); isotope-surprise teaching beat at the CO2 nodes; weight value and topology unchanged.
- (c) **Design C** — full-precision carbonyl/methyl duality (crosses into glycolysis hero-identity scope; highest cost).
- Also decide under (b): does the RNG outcome drive player GUIDANCE only (teaching text nudges the loop choice on "retained"), or should the graph gain any cond/branch logic? (Data-only cond-gating on flags/visits IS possible without engine changes, but the skeleton's mixed weighted node already handles the flow — recommendation: guidance-only.)

**D2 — Prochirality claim source widening.** (a) Keep `TCA-RNG-CITRATE-PROCHIRALITY-01` as approved, add Wikipedia-Aconitase + Wikipedia-TCA as co-sources (registry edit + re-approval) — RECOMMENDED; (b) file `…-02` dual-sourced and retire `-01`; (c) leave as-is (gap documented in review_notes only).

**D3 — IDH3 cast PDB: 5GRF (γ-K151A mutant, 2.5 Å) vs 5GRE (WT αγ, 2.65 Å) vs 6KDY (WT αβ + NAD⁺, 3.02 Å).** (a) Swap to 5GRE — WT, same group, citrate+ADP bound, mirrors the 2OZL→6CFO precedent — RECOMMENDED; (b) keep 5GRF with mandatory mutant disclosure in teaching text; (c) 6KDY if showing NAD⁺ matters more than resolution/regulation-binding. Whichever is chosen needs a `CAST-IDH3-PDB-01-cand` claim.

**D4 — IDH3A default reaffirmation.** (a) Confirm IDH3A (M204I→I204M or R316C→C316R) as the isocitrate_dh disease story — RECOMMENDED (ClinVar-Pathogenic re-verified); (b) revisit IDH1-R132H as a narrative side-encounter (scope expansion; needs its own claims + node). Phase 5.1 human already confirmed IDH3A as default — this is a re-affirmation checkpoint, not a re-open.

**D5 — akg_dh disposition (OGDH now HAS pathogenic missense).** (a) Keep narrative-only; file `DIS-OGDH-01-cand` (P189L→L189P) as a documented candidate + optionally a text-only mention claim — RECOMMENDED (frozen-invariant preserved; evidence tier weaker: single-submitter/no-assertion-criteria); (b) promote to edit-allowed (breaks the 14-edit-allowed invariant → test + DESIGN.md + diagram updates).

**D6 — Aconitase cast PDB species (no human ACO2 structure exists — live-confirmed).** (a) 1ACO bovine 2.05 Å (trans-aconitate-bound; the classic Ogston teaching structure; matches the skeleton note) — RECOMMENDED; (b) 7ACN pig 2.0 Å (isocitrate/product-bound); (c) 1C97 bovine S642A (NOT recommended — catalytic-site mutant). Whichever: `CAST-ACO2-PDB-01-cand` with the homology caveat + the D-numbering-mapping task before `edits.json` authoring.

**D7 — CS dimer cast convention (queued from Phase 6 close-out).** 1CSC AU = monomer; biological assembly = dimer (verified). (a) Load the AU monomer + teaching note "the functional enzyme is a homodimer" — RECOMMENDED for Phase 7 data-only scope; (b) load the biological assembly (requires a small AssetManager/molops enhancement — code change, out of the stated Phase 7 content-only scope; if wanted, split a tiny engineering plan); (c) swap to a multi-chain AU structure — none found among the main CS teaching structures (2CTS is also monomeric-AU), so (c) is not viable without the assembly mechanism.

**D8 — MDH2 cast PDB (low priority).** 2DFD (apo, 1.9 Å, skeleton default) vs 4WLU (L-malate + NAD⁺ bound, 2.14 Å — LibreTexts' own model). Either is defensible; 4WLU is pedagogically richer if the substrate/cofactor are shown.

**D9 — Source-approval batch.** Approve (or not) the §9 candidate sources: `WIKIPEDIA-TCA`, `WIKIPEDIA-ACONITASE`, `PMID-36520152` (only if D5 mentions OGDH deficiency), the 16.04-section scope extension of `LIBRETEXTS-METAB-TCA`, and the `PDB-*` cast records per D3/D6/D8. All are routine-tier EXCEPT the two HIGH-STAKES claims they ground (`TCA-RNG-WEIGHT-02-cand`, `TCA-CARBON-FATE-01-cand` under Design B, and the DIS-* disease claims) which get individual per-claim review per the hybrid workflow.

**D10 — Cycle-trap N (OQ3, re-flagged).** `visits.get('tca.shuffle', 0) > 5` is a game-design parameter, NOT a science claim. Under Design B the geometric distribution gives P(5 consecutive "retained") ≈ 3% — confirm N=5 (or adjust) at playtest. Keep the "not a science claim" framing in any text.

---

## 11. Open questions

1. **Hero-carbon identity upstream dependency (cross-boundary).** Which glucose carbon is the hero (intro/preface choice — glycolysis researcher's scope) determines whether the hero is the acetyl methyl (geometric 50/50 fate — Design B's exact case) or the acetyl carbonyl (deterministic turn-2 exit — B's approximation case) or a PDH-released carbon (never reaches TCA). Design B is hero-carbon-agnostic by construction; Design C is not. The planner should ask the glycolysis segment's plan whether the hero's glucose carbon is fixed and disclosed; if it is, one teaching sentence can bridge ("your [methyl/carbonyl] carbon's fate…").
2. **"Rate-limiting IDH" exact wording.** The skeleton's isocitrate_dh dramatic text says "This is the rate-limiting step of the TCA cycle." Wikipedia's table marks the oxalosuccinate-decarboxylation row "rate-limiting, irreversible" and 16.03 (Regulation) is the natural LibreTexts anchor — but 16.03 was NOT fetched in this pass. Fetch 16.03 before filing `TCA-IDH3-01`'s regulation sentence (or soften to "a key regulatory step").
3. **OGDH R312K / S297Y / N320S per-record verification.** Verified as Pathogenic via the esearch/esummary batch; the trait/OMIM cross-refs did not surface in esummary for these (empty trait_set in the API response — unlike P189L whose live VCV page showed OMIM 613022.0003). If any of the three is preferred over P189L, fetch its VCV page live before filing.
4. **Aconitase residue mapping (Phase 5.1 OQ5, still open, now load-bearing).** Human S112 (ICRD) ↔ bovine-1ACO (or pig-7ACN) residue number must be established by sequence alignment BEFORE the aconitase `edits.json` signature is written. The 05.3 align machinery + a headless `cmd.iterate` probe is the verified path. No number is asserted anywhere in this document.
5. **16.03 Regulation page** — unfetched this pass; needed only if regulation claims (IDH rate-limiting; CS/αKGDH product inhibition) enter teaching text at routine tier.
6. **5GRF/5GRE α-chain construct numbering** vs UniProt P50213 for the M204I/R316C `resi` mapping — same class of check as §6.7; do at content-authoring time with a headless iterate probe.
7. **endings.json text authorship boundary** — the good/normal ending NODE texts are another researcher's, but the CLAIMS grounding them (`TCA-CITRATE-EXPORT-01`, `TCA-TRANSAMINATION-01`, `TCA-CO2-EXIT-01`, `TCA-AMPHIBOLIC-01`) are this segment's to file. Coordinate the claim-id list handoff so the ending-text plan references registered claim_ids only.

---

## Sources

### Primary (HIGH confidence — fetched/queried live 2026-08-30)
- LibreTexts 16.02 "Reactions of the Citric Acid Cycle" (Jakubowski & Flatt) — full-text fetch: (S)-citryl-CoA; aconitase 180° flip; ΔG°′ table for all 8 steps; the "fully released as CO2" shorthand; Krebs ¹⁴C narrative; Summary stoichiometry. URL = registered LIBRETEXTS-METAB-TCA 16.02 subpage.
- LibreTexts 16.04 "Variants of the Citric Acid Cycle" — full-text fetch: citrate-lyase→FA-synthesis; GABA-shunt transamination; anaplerotic framing; no-net-synthesis point.
- Wikipedia "Citric acid cycle" (rev 1370238747) — carbon-fate isotope result; "cataplerotic" biosynthesis section; amphibolic; stoichiometry; rate-limiting note.
- Wikipedia "Aconitase" (rev 1343733503) — pro-R/pro-S prochirality + OAA-vs-acetyl discrimination; His101/Ser642; 180° flip.
- UniProt REST flat-text: Q99798 (ACO2), P50213 (IDH3A), P53597 (SUCLG1), P07954 (FH), P40926 (MDH2), O75390 (CS), Q02218 (OGDH), O75874 (IDH1), P16276 (7ACN species).
- NCBI ClinVar E-utilities: OGDH pathogenic-missense esearch (10 hits → 4 Pathogenic missense: 2443832/2443831/2443830/1331346) + VCV002443831 live page (P189L, OMIM 613022.0003, PMID 36520152); IDH3A pathogenic-missense esearch (9 hits; 977473 M204I + 977472 R316C Pathogenic verified).
- RCSB Data API: 1CSC, 1ACO, 7ACN, 2B3Y, 2CTS, 5GRF, 5GRE, 5YVT, 6KDY, 6WCV, 5UPP, 2DFD, 4WLU (titles/resolutions/species/assembly).
- RCSB Search API: IDH3A (P50213) entry list; UniProt Q99798 cross-ref emptiness re-confirmed.
- PyMOL bundled source: `tmp/pymol-src/modules/pymol/importing.py:1554-1563` (assembly-setting mechanism, verified).

### Secondary (MEDIUM confidence)
- Phase 5.1 research docs (`05.1-RESEARCH-disease-mutants-tca.md`, 2026-08-20) — ClinVar classifications for the 5 promoted candidates cross-checked against this pass's live queries (all consistent; 1 rsID corrected).
- OMIM MIM numbers via ClinVar trait cross-refs (OMIM direct fetch blocked 403 — Phase 5.1 precedent).

### Tertiary (flagged)
- The turn-by-turn label-fate derivation in §2.1 (carbonyl→turn 2 deterministic; methyl→geometric from turn 3) is MEDIUM-HIGH: mechanism-derived from verified quoted statements (source sentences 1-3), consistent with the classic isotope-labeling result, but the specific turn numbers are this research's derivation, not a verbatim quote. If the human wants a verbatim anchor for the geometric fate, a targeted search for the Lehninger Fig 16-7 equivalent on a license-clear page is a follow-up (the Wikipedia "requires several turns" sentence is the verbatim floor).

## Metadata

**Confidence breakdown:**
- Shuffle chemistry + carbon-fate: HIGH for quoted facts; MEDIUM-HIGH for derived turn mapping (flagged above).
- Existing-claim re-verification: HIGH (live fetches).
- Disease-mutant candidates: HIGH (UniProt + ClinVar live, dual-source per allele); OGDH promotion = HIGH for existence, MEDIUM for narrative strength (single-submitter caveat).
- PDB verifications: HIGH (RCSB Data API, every id checked live this pass).
- RNG mechanics (data vs code): HIGH (read from engine/interpreter/tests).
- Cataplerotic claims: HIGH (verbatim quotes from 2 live license-clear sources).

**Research date:** 2026-08-30. **Valid until:** ~2026-09-29 (30 days; ClinVar classifications and RCSB entries are the moving parts — a re-check before each checkpoint-approval batch is prudent; UniProt disease blocks stable).
**Approvals made by this research: NONE** — every claim/source/PDB above is a CANDIDATE for the human's per-claim checkpoints (D1-D10).
