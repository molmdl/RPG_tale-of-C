# Phase 5 Research — Source Approval Workflow + Glucose/TCA First-Batch Sources

**Researched:** 2026-08-15
**Aspect:** Source-approval workflow design (batch-by-source vs strict per-claim) + first batch of candidate sources for the glucose critical-path enzymes + TCA RNG weights — ONE focused slice of Phase 5 (Pre-Content Key Decisions & Source Approval).
**Phase goal addressed:** Success Criterion #4 (batch-by-source vs strict per-claim process agreed + first batch of approved sources in the registry) and Success Criterion #5 (CITE-01 per-claim checkpoint operational, enforced by the Phase 1 pre-ship gate).
**Decision owner:** THE HUMAN. This document GATHERS options + REAL candidate sources FOR THE HUMAN to decide. It does NOT decide the workflow. It does NOT approve any source. Every candidate source below is marked `CANDIDATE — needs human approval`.
**Confidence:** HIGH for the gate/registry mechanics and the 2 web-verified PDB IDs + the LibreTexts Metabolism hub; MEDIUM for the LibreTexts exact subpage URLs (hub verified, specific glycolysis/TCA subpages flagged for verification); the TCA-carbon-scrambling mechanism is textbook-standard but each claim still needs per-claim human approval.

---

> **No-fabricated-science invariant (read first).** Per `spec.md` (lines 12, 64, 66) and `AGENTS.md`, every scientific claim and citation must be verified against a real source AND explicitly human-approved per claim before landing in code/content. This research **proposes real, identifiable candidate sources** for the human to approve later. It does NOT invent DOIs, PDB IDs, or references. Exactly **two PDB IDs** below (`4PFK`, `1CSC`) were **verified to resolve** at `https://www.rcsb.org/structure/<ID>` during this research, and their deposited bibliographic data (resolution, authors, year, primary-citation DOI) is reported verbatim from the RCSB pages — not from memory. One additional PDB ID I checked from training memory (`1HKA`) turned out to be **NOT hexokinase** (it is HPPK, a folate-pathway enzyme) — this is documented below as a **cautionary finding** that validates why the no-fabricated-science rule and the verify-before-asserting discipline exist. All other PDB IDs are listed as `CANDIDATE — verify at rcsb.org before approval` and are NOT asserted as real. No textbook ISBN is invented.

---

## Summary

Phase 5 SC#4 has two independent sub-decisions the human must make: **(A) which approval WORKFLOW** to adopt (strict per-claim, batch-by-source, hybrid, or per-source-record), and **(B) which concrete sources** form the first approved batch for the glucose critical path + TCA weights. This research prepares both for the human.

The existing infrastructure is solid and was **verified operational** during this research:
- The Phase 1 pre-ship gate (`tools/check_citations.py`) was run against the test fixtures and behaved exactly per spec — PASS on approved claims, FAIL (exit 1) on `pending`, FAIL (exit 1) on `missing` (claim referenced by a story node but absent from the empty `data/citations.json`). The strict-equality predicate (`approval_status == "approved"`, NOT `!= "pending"`) is confirmed in `c14/citations.py:100-109` — a `rejected` claim fails identically to a `pending` one. **SC#5 is already satisfied at the gate level**; what remains is populating the first batch so the gate has real data to enforce.
- The registry (`data/citations.json`) is `{}` (empty) and its loader (`c14/citations.py`) enforces a strict per-claim schema: top-level is a JSON object, every key is a `claim_id`, every value is a dict with `approval_status ∈ {pending, approved, rejected}`. This shape constraint matters for the schema-extension question (see §2).

The workflow choice is a throughput-vs-safety tradeoff. **Strict per-claim** (the user's current choice per PROJECT.md Key Decisions) is safest but is the timeline-dominating risk (Pitfall 7: hundreds of claims × per-claim review). **Batch-by-source** amortizes the source-approval cost — approve ONE source up front, then all claims traceable to that source inherit the source's approval (each claim still gets a registry entry, but its review is fast-tracked by citing the approved source). **Hybrid** adds individual review for high-stakes/contested claims (RNG weight values, protonation defaults) on top of batch source approval. A fourth option (**per-source-record**) decouples "is this source approved to cite" from "is this specific claim approved" — the gate stays claim-level; the source approval is a separate registry the gate doesn't enforce.

**Primary recommendation (advisory):** Option **(c) HYBRID** — approve a small set of batch SOURCES up front (the LibreTexts Biological Chemistry / Metabolism modules + a Lehninger chapter cross-reference + the RCSB PDB entries as a structure source batch), so all routine pathway-mechanism claims fast-track by citing an approved source; but reserve individual per-claim review for the high-stakes claims the game depends on (the TCA RNG weight VALUES, the citrate-prochirality mechanism that grounds the shuffle, protonation defaults, and any carbon-fate claim). This preserves the user's chosen safety guarantee exactly where the science is load-bearing, while unblocking the ~60–100 routine glucose-critical-path claims that would otherwise dominate the timeline. The key **tradeoff flagged**: hybrid requires the human to define upfront which claim categories are "high-stakes" (individual review) vs "routine" (source-inherited) — a one-time taxonomy decision.

For the first batch of sources, the spec's preferred source family — "the biochemistry libretext" (spec.md line 12) — is real and verified: the Chemistry LibreTexts **Biological Chemistry → Supplemental Modules → Metabolism** hub (CC BY-NC-SA 4.0) is the natural home for glycolysis / pyruvate dehydrogenase / TCA content. The canonical print cross-reference is **Lehninger Principles of Biochemistry** (Nelson & Cox). Two glucose-critical-path PDB structures were web-verified at RCSB: **4PFK** (phosphofructokinase, *G. stearothermophilus*, 2.40 Å) and **1CSC** (citrate synthase, *Gallus gallus*, 1.70 Å) — both with full deposited bibliographic data. The TCA RNG-weight mechanism (citrate prochirality / the Ogston hypothesis / isotope-labeling carbon-fate studies) is textbook-standard and connects directly to the C14 hero's tracking role; the source backs the **mechanism**, and the human picks the **weight values** (game design grounded in science).

---

## 1. Workflow Options (for the human to choose)

For each option: how it maps onto the existing `data/citations.json` registry + `c14/citations.py` loader + `tools/check_citations.py` gate, how the gate enforces it, throughput estimate, and risk of fabricated science slipping through.

### (a) STRICT PER-CLAIM — every individual claim reviewed + approved one-by-one

- **What:** Each `claim_id` in the registry is reviewed and its `approval_status` flipped to `approved` individually by the human. No source-level batching. This is the user's currently-recorded choice (PROJECT.md Key Decisions: "Source approval = per-claim checkpoint").
- **Registry mapping:** Unchanged. `data/citations.json` = `{claim_id: {source, approval_status, ...}}` exactly as the Phase 1 schema. Each claim carries its own `source` string + `approval_status`.
- **Gate enforcement:** `tools/check_citations.py` + `CitationRegistry.is_approved()` (c14/citations.py:100-109) already enforce this perfectly: `approval_status == "approved"` per claim. **Zero gate change.** Verified operational this research (PASS/pending-fail/missing-fail all confirmed).
- **Throughput:** **Slowest.** Pitfall 7 estimate: ~4 tracks × ~20 proteins × ~5 claims ≈ **~400 claims** for full content; glucose first batch ≈ 21 enzymes × ~3–5 claims ≈ **~60–105 claims**. At even ~5 min/claim that's ~5–9 hours of human review for the glucose batch alone, ~33 hours for all content. This is the timeline-dominating risk.
- **Fabricated-science risk:** **Lowest.** Every claim is individually scrutinized. A wrong claim can only slip through if the human misapproves it on review — there is no inherited approval to hide behind.
- **When it's the right choice:** If the human's review bandwidth is high and the project is not timeline-constrained, or if absolute minimum risk is the only acceptable bar.

### (b) BATCH-BY-SOURCE — a source is approved up front; claims traceable to it inherit approval

- **What:** The human approves a SOURCE (e.g. "LibreTexts Metabolism / Glycolysis module", or "PDB entry 4PFK") once. Every claim whose `source_id` points to that approved source inherits the source's approval — the claim still gets its own registry entry, but its `approval_status` is fast-tracked to `approved` by citing the approved source. The per-claim checkpoint is preserved (the claim is still in the registry and the gate still checks it), but the human review per claim becomes a one-line "yes, this is in approved source X" rather than a full re-derivation.
- **Registry mapping:** Needs a **source registry** alongside the claim registry (see §2 for the concrete schema). Each claim gains a `source_id` field pointing into a separate `data/sources.json`; each source record carries its own `approval_status` + `approved_date`. The claim's `approval_status` is still the gate predicate — the "batch" is a *process convention* (approve source, then set the citing claims' statuses), not a gate-enforcement change.
- **Gate enforcement:** `tools/check_citations.py` is **unchanged** — it still checks `claim.approval_status == "approved"` per claim. The gate does NOT need to know about sources at all. (Optional enhancement: a separate `tools/check_sources.py` that asserts every claim's `source_id` resolves to an `approved` source — catches drift if a claim cites a source that was later rejected. This is an implementation task for the planner, not a research deliverable.)
- **Throughput:** **Much faster.** ~60–105 glucose claims collapse to **~3–6 source approvals** (LibreTexts glycolysis module, LibreTexts PDH/TCA module, Lehninger chapter cross-ref, a PDB-structures source batch) + a fast per-claim confirmation pass. Roughly a **10–20× amortization** for routine mechanism claims.
- **Fabricated-science risk:** **Medium.** Higher than (a): a wrong claim that cites an approved source can inherit approval without the human re-reading the source for that specific claim. Mitigation: (i) the human still eyeballs each claim's text vs the source on the fast-track pass; (ii) reserve a per-claim review tier for high-stakes claims (→ option c).
- **When it's the right choice:** When the source family is trusted (LibreTexts, Lehninger, RCSB PDB) and the claims are routine restatements of standard pathway facts (enzyme catalyzes reaction X; substrate is Y; product is Z).

### (c) HYBRID — sources approved up front (batch), high-stakes/contested claims still get individual review ⭐ *advisory recommendation*

- **What:** Combine (a) and (b). Approve a set of batch SOURCES up front (as in b). All *routine* claims inherit approval by citing an approved source. But a defined category of **high-stakes claims** always gets individual per-claim review regardless of source — because the game's correctness or the science's load-bearing nature depends on getting that specific value right.
- **High-stakes categories to reserve for individual review (advisory):**
  - **RNG weight VALUES** for the TCA shuffle — these are game-design decisions grounded in science; the source backs the *mechanism* (citrate prochirality, carbon scrambling), but the human picks the *values*. Each weight claim reviewed individually.
  - **Protonation defaults** per catalytic residue (the Phase 4 `protonation_catalog.py` real entries) — already gated as Phase 5+ content (CITE-01); each is a "this tautomer is the active one for enzyme X" claim.
  - **Carbon-fate claims** tied to the soul-jump / ending tiers (which carbon exits as CO2 at which step; which electrons go to NADH/FADH2) — these are the load-bearing science for the True/Normal ending distinction (Pitfall 4, RESOLVED).
  - **Any claim the human flags as contested or surprising** — case-by-case override.
- **Routine categories to fast-track via source inheritance (advisory):**
  - Enzyme catalyzes reaction X (substrate → product) — standard pathway fact.
  - Enzyme name / EC number / cofactor identity — lookup facts.
  - PDB structure existence + resolution + deposited citation — RCSB is the source of record.
  - Pathway ordering (glycolysis step 1, step 2, ...) — standard.
- **Registry mapping:** Same as (b) — a `data/sources.json` + per-claim `source_id`, with the claim's `approval_status` as the gate predicate. The "high-stakes" distinction is a **process convention + a claim field** (e.g. `review_tier: "high-stakes" | "routine"`), NOT a gate-enforcement change. The gate still checks `approval_status == "approved"`; the tier governs *how* a claim gets to `approved` (individual review vs source-inherited fast-track).
- **Gate enforcement:** `tools/check_citations.py` **unchanged**. Optional `tools/check_sources.py` (as in b). Optional: a test asserting every claim with `review_tier: "high-stakes"` has a non-empty `review_notes` field — catches a high-stakes claim that was fast-tracked by mistake. (Implementation task for the planner.)
- **Throughput:** **Fast for routine, rigorous for high-stakes.** The ~60–105 glucose claims split into ~5–10 high-stakes (individually reviewed) + ~55–95 routine (source-inherited). Human time ≈ (5–10 × 10 min) + (55–95 × 1 min) ≈ 1.5 hours. Versus (a)'s ~5–9 hours. Captures most of the throughput gain while preserving the safety guarantee exactly where it matters.
- **Fabricated-science risk:** **Low for high-stakes, medium for routine** — same as (a) on the load-bearing claims, same as (b) on the routine ones. The high-stakes tier is where fabricated/wrong science would actually break the game (wrong RNG weights, wrong protonation, wrong carbon fate); the routine tier is where a wrong claim is a pedagogical embarrassment, not a correctness break.
- **When it's the right choice:** When the human wants the safety of (a) on the claims that matter most AND the throughput of (b) on the claims that are standard restatements. This is the option that best fits the project's stated values (no fabricated science, educator audience) AND Pitfall 7's timeline risk.

### (d) PER-SOURCE-RECORD — decouple "source approved to cite" from "claim approved"

- **What:** Maintain a source registry (`data/sources.json`) where the human approves sources to *cite from* (the source exists, is authoritative, is acceptable for this project). Then each claim independently goes through per-claim approval (as in a), but the claim's source MUST be an already-approved source — a claim citing an unapproved source is auto-rejected. This is a weaker version of (b): it doesn't auto-inherit approval, it just gates *which sources are even eligible*.
- **Registry mapping:** `data/sources.json` (source_id → {reference, approval_status, approved_date}) + `data/citations.json` (claim_id → {source_id, approval_status, ...}). The claim's `source_id` MUST resolve to an `approved` source.
- **Gate enforcement:** `tools/check_citations.py` unchanged on the claim side. A NEW `tools/check_sources.py` enforces "every claim's source_id → approved source" (the eligible-source gate). Two gates, layered.
- **Throughput:** Between (a) and (b). You still review every claim individually, but you can't even propose a claim from a non-approved source — so the source-family decision is front-loaded and the per-claim review is "is this claim correctly drawn from an approved source" rather than "is this source acceptable AND is the claim correct".
- **Fabricated-science risk:** **Low.** Same per-claim scrutiny as (a), plus a structural barrier against citing sketchy sources. Slightly safer than (a) on source provenance, slightly slower than (b) on throughput.
- **When it's the right choice:** If the human wants to lock the *source family* decision upfront (LibreTexts + Lehninger + RCSB only; no Wikipedia, no random blogs) but still review every claim individually. A reasonable compromise if (c)'s "routine vs high-stakes" taxonomy feels too fuzzy to define upfront.

### Comparison matrix

| Option | Gate change | Human time (glucose batch) | Fabricated-science risk | Best fit |
|--------|-------------|----------------------------|-------------------------|----------|
| (a) Strict per-claim | none | ~5–9 h | lowest | max safety, ignore timeline |
| (b) Batch-by-source | none (process convention) | ~1–2 h | medium | max throughput, trust the sources |
| (c) Hybrid ⭐ | none + optional `check_sources` + tier test | ~1.5 h | low on high-stakes, medium on routine | **safety where it matters + throughput elsewhere** |
| (d) Per-source-record | new `check_sources.py` gate | ~3–4 h | low | lock source family, still review each claim |

**Advisory recommendation: (c) HYBRID.** It is the only option that honors BOTH the user's recorded preference for a per-claim safety checkpoint (PROJECT.md Key Decisions) AND Pitfall 7's timeline-dominating-risk warning. The cost is a one-time taxonomy decision (which claim categories are high-stakes). The sections below assume (c) is chosen but are written so the human can pick any option — the source candidates and the schema extension apply to (b), (c), and (d) alike.

---

## 2. Registry Schema Extension (concrete, backward-compatible)

> **Constraint from the existing loader.** `c14/citations.py:80-98` (`CitationRegistry.load`) validates that `data/citations.json` is a JSON object whose **every** top-level key is a `claim_id` and whose **every** value is a dict with `approval_status ∈ {pending, approved, rejected}`. This means a `sources` top-level key in the SAME file would FAIL the loader (its value is a sources-dict, not a claim with `approval_status`). So a same-file `sources` section requires a loader change. The cleanest backward-compatible option is a **separate `data/sources.json` file** that the gate never reads. (The planner may alternatively extend the loader to skip a reserved `_sources` key; that is an implementation decision, not a research one — I propose the separate-file approach because it is zero-risk to the existing gate.)

### Recommended: two files, gate unchanged

**`data/sources.json`** (NEW — not read by the Phase 1 gate; read by an optional new `tools/check_sources.py` if the human picks option b/c/d):

```json
{
  "LIBRETEXTS-METAB-GLYCOLYSIS": {
    "reference": "LibreTexts Biological Chemistry / Supplemental Modules / Metabolism / Glycolysis",
    "url": "https://chem.libretexts.org/Bookshelves/Biological_Chemistry/Supplemental_Modules_(Biological_Chemistry)/Metabolism",
    "license": "CC BY-NC-SA 4.0",
    "source_type": "educational_open_textbook",
    "approval_status": "approved",
    "approved_by": "human",
    "approved_date": "2026-08-XX",
    "notes": "Exact glycolysis subpage URL to be confirmed at approval time (hub verified live 2026-08-15)."
  },
  "LIBRETEXTS-METAB-TCA": {
    "reference": "LibreTexts Biological Chemistry / Supplemental Modules / Metabolism / Citric Acid Cycle (TCA)",
    "url": "https://chem.libretexts.org/Bookshelves/Biological_Chemistry/Supplemental_Modules_(Biological_Chemistry)/Metabolism",
    "license": "CC BY-NC-SA 4.0",
    "source_type": "educational_open_textbook",
    "approval_status": "approved",
    "approved_by": "human",
    "approved_date": "2026-08-XX",
    "notes": "Exact TCA/citric-acid-cycle subpage URL to be confirmed at approval time."
  },
  "LEHNINGER-CH-CITRIC_ACID_CYCLE": {
    "reference": "Lehninger Principles of Biochemistry (Nelson & Cox), chapter on the Citric Acid Cycle",
    "source_type": "print_textbook",
    "approval_status": "approved",
    "approved_by": "human",
    "approved_date": "2026-08-XX",
    "notes": "CANDIDATE - human to confirm edition + exact chapter number before approving. No ISBN asserted here."
  },
  "PDB-4PFK": {
    "reference": "RCSB PDB entry 4PFK - Phosphofructokinase (Geobacillus stearothermophilus), 2.40 A",
    "url": "https://www.rcsb.org/structure/4PFK",
    "pdb_doi": "10.2210/pdb4PFK/pdb",
    "primary_citation": "Evans, P.R.; Farrants, G.W.; Hudson, P.J. (1981) Philos Trans R Soc London ser B 293:53-62, DOI 10.1098/rstb.1981.0059, PubMed 6115424",
    "source_type": "structural_database_entry",
    "approval_status": "approved",
    "approved_by": "human",
    "approved_date": "2026-08-XX",
    "notes": "VERIFIED at rcsb.org 2026-08-15 - structure exists, resolution + citation read from the RCSB page."
  },
  "PDB-1CSC": {
    "reference": "RCSB PDB entry 1CSC - Citrate synthase (Gallus gallus), 1.70 A",
    "url": "https://www.rcsb.org/structure/1CSC",
    "pdb_doi": "10.2210/pdb1CSC/pdb",
    "primary_citation": "Karpusas, M.; Holland, D.; Remington, S.J. (1991) Biochemistry 30:6024-6031, DOI 10.1021/bi00238a028, PubMed 2043640",
    "source_type": "structural_database_entry",
    "approval_status": "approved",
    "approved_by": "human",
    "approved_date": "2026-08-XX",
    "notes": "VERIFIED at rcsb.org 2026-08-15."
  }
}
```

**`data/citations.json`** (EXISTING — the file the Phase 1 gate reads; schema extended with `source_id` + optional `review_tier`, gate predicate unchanged):

```json
{
  "GLY-PFK-01": {
    "source_id": "LIBRETEXTS-METAB-GLYCOLYSIS",
    "source": "LibreTexts Biological Chemistry / Metabolism / Glycolysis (CC BY-NC-SA 4.0)",
    "claim_text": "Phosphofructokinase-1 catalyzes the committed, rate-limiting step of glycolysis: fructose-6-phosphate + ATP -> fructose-1,6-bisphosphate + ADP.",
    "approval_status": "approved",
    "approved_by": "human",
    "approved_date": "2026-08-XX",
    "review_tier": "routine",
    "inherits_source_approval": true
  },
  "TCA-RNG-CITRATE-PROCHIRALITY-01": {
    "source_id": "LEHNINGER-CH-CITRIC_ACID_CYCLE",
    "source": "Lehninger Principles of Biochemistry (Nelson & Cox), Citric Acid Cycle chapter",
    "claim_text": "Citrate is a prochiral molecule; citrate synthase produces a specific stereoisomer, and aconitase discriminates between citrate's two carboxymethyl groups, so the two carbons derived from acetyl-CoA do not become equivalent until after the first turn of the cycle.",
    "approval_status": "approved",
    "approved_by": "human",
    "approved_date": "2026-08-XX",
    "review_tier": "high-stakes",
    "review_notes": "Grounds the TCA RNG shuffle mechanism. Source backs the MECHANISM; the RNG weight VALUES are a separate game-design claim (TCA-RNG-WEIGHT-XX) approved individually.",
    "inherits_source_approval": false
  },
  "TCA-RNG-WEIGHT-01": {
    "source_id": "LEHNINGER-CH-CITRIC_ACID_CYCLE",
    "source": "Lehninger Principles of Biochemistry (Nelson & Cox), Citric Acid Cycle chapter",
    "claim_text": "In this game, the probability that a given acetyl-CoA carbon exits as CO2 on the first turn of TCA vs the second turn is set to 0.5 / 0.5 (game-design value grounded in the citrate-prochirality mechanism).",
    "approval_status": "approved",
    "approved_by": "human",
    "approved_date": "2026-08-XX",
    "review_tier": "high-stakes",
    "review_notes": "VALUE is a game-design decision; the 0.5/0.5 is grounded in the symmetric-fate mechanism but the human chooses the exact weights for pedagogy. Reviewed individually.",
    "inherits_source_approval": false
  },
  "CAST-PFK-PDB-01": {
    "source_id": "PDB-4PFK",
    "source": "RCSB PDB 4PFK (Geobacillus stearothermophilus phosphofructokinase), 2.40 A",
    "claim_text": "The game's PFK cast structure is RCSB PDB entry 4PFK (2.40 A resolution; Evans, Farrants, Hudson 1981).",
    "approval_status": "approved",
    "approved_by": "human",
    "approved_date": "2026-08-XX",
    "review_tier": "routine",
    "inherits_source_approval": true
  }
}
```

### Why this is backward-compatible with the Phase 1 gate

1. The gate (`tools/check_citations.py`) calls `CitationRegistry.load("data/citations.json")` → `is_approved(claim_id)` → `== "approved"`. The new fields (`source_id`, `review_tier`, `inherits_source_approval`, `review_notes`, `claim_text`) are **ignored by the loader's validation** — `c14/citations.py:87-97` only checks that each entry is a dict and that `approval_status` is in the valid set. So the extended claim records load cleanly.
2. `data/sources.json` is **never opened by the Phase 1 gate** — it is a separate file. So the gate's behavior, exit codes (0/1/2), and the existing test fixtures are all unchanged.
3. The strict-equality predicate (`approval_status == "approved"`, NOT `!= "pending"`, c14/citations.py:100-109) is preserved exactly — a `rejected` claim still fails identically to a `pending` one. No regression on Pitfall 6 (the rejected-claim-passes trap).
4. The duplicate-key hook (`_no_duplicate_keys`, c14/citations.py:29-46) still fires on duplicate `claim_id`s in `data/citations.json`. (If `data/sources.json` is added, its loader should use the same hook for `source_id`s — an implementation detail for the planner.)

### Optional `tools/check_sources.py` (advisory, for options b/c/d)

A second gate that fails the build if any claim's `source_id` does not resolve to an `approved` entry in `data/sources.json`. This catches drift (a source later rejected, but claims still citing it as approved). **Not required for the Phase 1 gate to function**; proposed as a Phase 5 implementation task if the human picks b/c/d. The planner decides whether to build it.

> **NOTE on claim_id naming convention.** This research follows the convention established by the parallel C14-decay research (`05-RESEARCH-c14-decay.md`), which uses `DOMAIN-NUMBER` ids like `C14-HL-01`. For the glucose critical path, this research proposes the prefix families: `GLY-XX-NN` (glycolysis), `PDH-XX-NN` (pyruvate dehydrogenase), `TCA-XX-NN` (TCA cycle), `CAST-XX-PDB-NN` (cast/structure claims), and `TCA-RNG-XX` (TCA RNG-weight claims). The human may rename at approval time; the planner finalizes the convention. The C14-decay research explicitly defers claim `C14-TIME-01` (the respiration-cycle timescale source) to THIS glucose-critical-path batch — see §6 cross-reference.

---

## 3. First Batch: Glucose Critical-Path Sources (candidate sources + PDB IDs)

### The glucose critical path (scope reminder)

- **Glycolysis (10 enzymes):** hexokinase, phosphoglucose isomerase, phosphofructokinase-1, aldolase, triose phosphate isomerase, GAPDH, phosphoglycerate kinase, phosphoglycerate mutase, enolase, pyruvate kinase.
- **Pyruvate dehydrogenase complex (3 enzymes):** E1 (pyruvate dehydrogenase), E2 (dihydrolipoyl transacetylase), E3 (dihydrolipoyl dehydrogenase).
- **TCA cycle (8 enzymes):** citrate synthase, aconitase, isocitrate dehydrogenase, α-ketoglutarate dehydrogenase, succinyl-CoA synthetase, succinate dehydrogenase, fumarase, malate dehydrogenase.

Total = **21 enzymes** for the glucose first batch.

### Candidate batch SOURCES (the few sources that amortize the whole batch)

Each marked `CANDIDATE — needs human approval`. The spec (line 12) leans toward LibreTexts; the print cross-reference is the canonical biochem textbook.

#### S-GLY-1: LibreTexts — Biological Chemistry / Metabolism / Glycolysis — `CANDIDATE — needs human approval` (HIGH confidence the hub exists; MEDIUM on the exact glycolysis subpage URL)

- **Reference:** "Glycolysis," under *Metabolism*, Supplemental Modules (Biological Chemistry), Chemistry LibreTexts.
- **Hub URL (VERIFIED LIVE 2026-08-15):** `https://chem.libretexts.org/Bookshelves/Biological_Chemistry/Supplemental_Modules_(Biological_Chemistry)/Metabolism` — page fetched live; CC BY-NC-SA 4.0; the hub description states "Catabolic processes are ones in which biomolecules are being degraded or oxidized" (exactly glycolysis → pyruvate).
- **What it backs (advisory, ~10 claims fast-tracked):** the 10 glycolysis enzymes' reactions, substrate/product identities, ATP/NADH accounting, and the pathway order.
- **Verification status:** Hub + license + topic-area confirmed by direct webfetch. The **specific glycolysis subpage URL** (one level deeper under Metabolism/) was NOT individually fetched during this research — the human should confirm the exact subpage URL at approval time and confirm it states each glycolysis step.

#### S-GLY-2: LibreTexts — Biological Chemistry / Metabolism / Pyruvate Dehydrogenase & Citric Acid Cycle — `CANDIDATE — needs human approval` (HIGH confidence the hub exists; MEDIUM on the exact subpage URLs)

- **Reference:** "Pyruvate Dehydrogenase" + "Citric Acid Cycle / TCA," under *Metabolism*, Supplemental Modules (Biological Chemistry), Chemistry LibreTexts.
- **Hub URL (VERIFIED LIVE 2026-08-15):** same Metabolism hub as S-GLY-1.
- **What it backs (advisory, ~11 claims fast-tracked):** the PDH complex (3 enzymes, the oxidative decarboxylation of pyruvate → acetyl-CoA + CO2 + NADH — note this is where the carbon body begins to leave as CO2, load-bearing for the soul-jump framing) and the 8 TCA enzymes (citrate synthase → ... → malate dehydrogenase) + the two decarboxylation steps (isocitrate dehydrogenase, α-ketoglutarate dehydrogenase) where more CO2 leaves.
- **Verification status:** Hub confirmed; exact PDH/TCA subpage URLs to be confirmed at approval time.

#### S-GLY-3: Lehninger Principles of Biochemistry (Nelson & Cox) — `CANDIDATE — verify existence + edition + chapter numbers, then human approval` (MEDIUM confidence; NOT web-verified)

- **Reference (provisional):** Nelson, D. L.; Cox, M. M. *Lehninger Principles of Biochemistry.* W. H. Freeman. (The canonical biochemistry textbook; covers glycolysis, the citric acid cycle, and oxidative phosphorylation in dedicated chapters.)
- **What it backs:** the SAME pathway facts as S-GLY-1/S-GLY-2, as a print cross-reference / authoritative backup. Particularly valuable for the TCA carbon-fate / citrate-prochirality mechanism (§4), which Lehninger treats in depth (the Ogston hypothesis, the two-turn equivalence of the acetyl carbons).
- **Honesty flag:** this is a well-known real textbook in my training data, but I did NOT web-verify the edition/ISBN during this research. The no-fabricated-science rule prohibits inventing ISBNs, so none is given. The human should confirm the exact edition + the chapter numbers for Glycolysis / Citric Acid Cycle before approving. If the LibreTexts modules (S-GLY-1/S-GLY-2) cover the needed facts adequately, the Lehninger cross-reference may be approved as a backup-only source (still useful for the citrate-prochirality depth).

### Candidate PDB IDs for the cast (~5–8 structures as a first batch)

> **Cautionary finding (read before trusting any PDB ID here).** During this research I verified PDB IDs by fetching `https://www.rcsb.org/structure/<ID>` directly. Two IDs resolved with full deposited bibliographic data (below, marked VERIFIED). One ID I guessed from training memory — `1HKA`, which I expected to be hexokinase — turned out to be **6-HYDROXYMETHYL-7,8-DIHYDROPTERIN PYROPHOSPHOKINASE (HPPK)**, a folate-pathway enzyme (EC 2.7.6.3), NOT hexokinase at all. This is exactly the trap the no-fabricated-science rule exists to prevent: a confidently-remembered PDB ID that is wrong. **Therefore: only the two VERIFIED IDs below are asserted as real; every other ID in the table is a `CANDIDATE — verify at rcsb.org before approval` and must be re-checked by the human or a follow-up research step before landing in the registry.**

| Enzyme (glucose critical path) | PDB ID candidate | Status | Deposited data (from RCSB page, for VERIFIED entries) |
|----------------------------------|------------------|--------|------------------------------------------------------|
| Phosphofructokinase-1 (glycolysis, committed step) | **4PFK** | **VERIFIED at rcsb.org 2026-08-15** | *G. stearothermophilus*; X-RAY, 2.40 Å; Evans, Farrants, Hudson 1981; PDB DOI 10.2210/pdb4PFK/pdb; primary DOI 10.1098/rstb.1981.0059; PubMed 6115424. EC 2.7.1.11. Homo-4-mer. Bundled-candidate (small, ~2.5 k atoms). |
| Citrate synthase (TCA, entry step; load-bearing for the prochirality mechanism) | **1CSC** | **VERIFIED at rcsb.org 2026-08-15** | *Gallus gallus* (chicken heart); X-RAY, 1.70 Å; Karpusas, Holland, Remington 1991, *Biochemistry* 30:6024–6031; PDB DOI 10.2210/pdb1CSC/pdb; primary DOI 10.1021/bi00238a028; PubMed 2043640. EC 2.3.3.1 (UniProt) / 4.1.3.7 (PDB primary). Homo-2-mer. Bundled-candidate. |
| Hexokinase (glycolysis, step 1) | (no ID asserted) | `CANDIDATE — verify at rcsb.org before approval` | A yeast hexokinase (e.g. the historical 2YHX family) or human glucokinase are commonly cited, but I will NOT assert a specific ID from memory after the 1HKA mistake. The human/follow-up research should pick a hexokinase structure, verify it at rcsb.org, and confirm organism + resolution + deposited citation. |
| Pyruvate kinase (glycolysis, step 10) | (no ID asserted) | `CANDIDATE — verify at rcsb.org before approval` | Cat-muscle pyruvate kinase (historically 1A49 family) and human M1 isoforms exist; verify before use. |
| Pyruvate dehydrogenase (PDH E1) | (no ID asserted) | `CANDIDATE — verify at rcsb.org before approval` | The PDH complex is large; E1 structures from *E. coli* and mammals exist. A glucose first-batch may use a PDH E1 domain structure; verify organism + resolution. May be a bulk-download (large) structure per the hybrid acquisition model (Pitfall 5). |
| Isocitrate dehydrogenase (TCA, decarboxylation step) | (no ID asserted) | `CANDIDATE — verify at rcsb.org before approval` | IDH structures (NAD+- and NADP+-dependent) exist in multiple organisms; verify. |
| α-Ketoglutarate dehydrogenase (TCA, decarboxylation step) | (no ID asserted) | `CANDIDATE — verify at rcsb.org before approval` | The α-KGDH E1 component is a common structure; verify. (Decarboxylation here is load-bearing for carbon fate.) |
| Succinate dehydrogenase / fumarase / malate dehydrogenase | (no ID asserted) | `CANDIDATE — verify at rcsb.org before approval` | Reserve for the next sub-batch once the 5–8 above are confirmed; the first batch need not cover all 21 enzymes as structures. |

**First-batch cast recommendation (advisory):** ~5–8 structures. Two are already VERIFIED (4PFK, 1CSC). The remaining 3–6 should be selected to cover (i) hexokinase (glycolysis entry), (ii) pyruvate kinase (glycolysis exit), (iii) PDH E1 (the carbon-body-starts-leaving-as-CO2 step — load-bearing for the soul-jump framing), and (iv) one or two more TCA enzymes at the human's discretion. **Every PDB ID in the final first batch must be web-verified at rcsb.org (resolution + deposited citation read from the page, not memory) before its `PDB-<ID>` source record is marked `approved` in `data/sources.json`.** This is the discipline the 1HKA finding mandates.

### Sources considered and NOT recommended for this batch

| Source | Why not the lead candidate here |
|--------|----------------------------------|
| **Wikipedia** (Glycolysis / Citric acid cycle articles) | Tertiary — useful to *locate* primary/educational sources but NOT itself an approved source per the no-fabricated-science rule. The human should approve LibreTexts / Lehninger, not Wikipedia. |
| **BRENDA / KEGG** | Excellent enzyme-compendium databases (EC numbers, organism-specific data). Could be a *supplementary* source for EC-number / cofactor lookup claims, but not the lead for pathway-mechanism claims. `CANDIDATE — propose separately if a lookup-claim needs a source`. |
| **MetaCyc / Reactome** | Pathway databases; useful for pathway-order cross-checks but secondary to a textbook for narrative claims. Not the first-batch lead. |

---

## 4. First Batch: TCA RNG Weights Sources (mechanism + isotope-labeling cross-ref)

### What the RNG weights are weights OF (mechanism clarification)

The spec (line 13) calls for "RNG decided stuff for pathways that is known to have some probability shuffle, e.g. in the TCA cycle." The scientifically-grounded interpretation of the TCA shuffle — and the one that connects to the C14 hero — is the **scrambling of the two acetyl-CoA carbons through the cycle's first vs second turn**, which is a direct consequence of **citrate's prochirality**:

1. **Citrate is a prochiral molecule** (the Ogston hypothesis, 1948): although citrate's central carbon has two identical-looking —CH₂COO⁻ arms, the molecule is prochiral, not achiral, because the two arms are distinguishable in 3D. Citrate synthase condenses oxaloacetate + acetyl-CoA to produce ONLY one specific citrate stereoisomer (the *re*-citrate), so the two acetyl-CoA carbons enter at two *specific, distinguishable* positions.
2. **Aconitase discriminates the two arms**: aconitase converts citrate → isocitrate acting on only ONE of citrate's two carboxymethyl groups (stereospecific hydration). This means the carbon from acetyl-CoA that ends up as the CO2 released by isocitrate dehydrogenase on the FIRST turn is determined by which arm aconitase acts on.
3. **Net consequence**: the two acetyl-CoA carbons are NOT equivalent on the first turn of the cycle — one is released as CO2 (by isocitrate dehydrogenase + α-ketoglutarate dehydrogenase) on the first turn, the other is retained and only released on the SECOND turn. After the first turn, the two become statistically equivalent (the cycle has "scrambled" them). **This is the mechanism the RNG weights encode**: the per-turn probability that a given acetyl carbon exits as CO2. (Whether the exact probability is 50/50 or skewed is a function of the stereochemical detail the game chooses to model — see the weight-values caveat below.)
4. **Connection to the C14 hero**: this is precisely why C14 isotope-labeling studies of the TCA cycle (label the acetyl-CoA carbons, trace which CO2 release carries the label on turn 1 vs turn 2) are the experimental evidence for this mechanism. The C14 hero is, narratively, one of those labeled acetyl carbons — so the game's RNG shuffle is literally the isotope-fate question.

### Candidate sources for the mechanism (each `CANDIDATE — needs human approval`)

#### S-TCA-1: Lehninger Principles of Biochemistry — Citric Acid Cycle chapter — `CANDIDATE — needs human approval` (MEDIUM confidence; NOT web-verified)

- **Reference (provisional):** Nelson & Cox, *Lehninger Principles of Biochemistry*, chapter on the Citric Acid Cycle. Lehninger treats citrate prochirality and the "fate of the two acetyl carbons" explicitly (the Ogston hypothesis, the asymmetry of the first turn, the two-turn equivalence).
- **What it backs:** the mechanism claims TCA-RNG-CITRATE-PROCHIRALITY-01 (citrate is prochiral; citrate synthase is stereospecific; aconitase discriminates the two arms; the two acetyl carbons become equivalent only after the first turn).
- **Honesty flag:** textbook candidate; verify edition + chapter before approving. This is the strongest single source for the *mechanism* because Lehninger is the canonical text for this exact concept.

#### S-TCA-2: LibreTexts — Biological Chemistry / Metabolism / Citric Acid Cycle module — `CANDIDATE — needs human approval` (HIGH confidence the hub exists; MEDIUM on the exact subpage + whether it covers prochirality)

- **Reference:** the Metabolism hub (S-GLY-2) — the citric-acid-cycle subpage. **Caveat:** I did NOT verify that the LibreTexts TCA subpage covers citrate prochirality specifically (it may state the pathway reactions but gloss the stereochemistry). The human should confirm at approval time whether the LibreTexts TCA page states the prochirality / two-turn-equivalence fact, or whether S-TCA-1 (Lehninger) is the required source for that specific claim.
- **What it backs:** the TCA enzyme reactions + the two decarboxylation steps (routine claims); possibly the prochirality mechanism (high-stakes claim) — to be confirmed.

#### S-TCA-3: Ogston, A. G. (1948) — the original prochirality hypothesis — `CANDIDATE — verify reference exists, then human approval` (LOW-MEDIUM confidence; NOT web-verified)

- **Reference (provisional):** Ogston, A. G. "Interpretation of experiments on the citric acid cycle," *Nature* 162, 963 (1948). This is the historically primary reference for the citrate-prochirality hypothesis that explains why the two acetyl carbons are distinguishable on the first TCA turn.
- **Honesty flag:** I recall this as the classic primary reference, but I did NOT web-verify the exact citation (volume/page/DOI) during this research. **`CANDIDATE — verify the exact bibliographic details at approval time`**; do NOT cite until verified. If the human prefers a textbook (S-TCA-1) over a 1948 primary paper for an educational game, S-TCA-3 may be unnecessary — but it is the *original* mechanism source.
- **What it backs:** the conceptual origin of the prochirality mechanism; useful as the deepest-layer provenance if the human wants the primary reference.

### Isotope-labeling cross-reference (connects to the C14 hero)

The experimental evidence for the carbon-scrambling mechanism is the **C14 / C13 isotope-labeling studies of the TCA cycle**: label the acetyl-CoA carbons (or the pyruvate carbons upstream), run the cycle, and measure which CO2 release carries the label on turn 1 vs turn 2. This is the direct experimental basis for "the two acetyl carbons become equivalent only after the first turn."

- **S-TCA-4: Isotope-labeling studies of TCA carbon fate — `CANDIDATE — propose primary literature for human approval` (LOW confidence; no specific paper asserted)**
  - I do NOT assert a specific isotope-labeling paper from memory (the no-fabricated-science rule). The classic line of work (Wilcox, Krampitz, and others in the 1950s–60s; modern reviews) establishes the turn-1 vs turn-2 CO2 release pattern. **Recommendation:** if the game's narrative wants to cite the *experimental evidence* (not just the textbook mechanism), the human should commission a follow-up research step to identify a specific citable isotope-labeling study and verify it. For the FIRST batch, S-TCA-1 (Lehninger) is sufficient — Lehninger already summarizes the isotope evidence in its TCA chapter.
  - **Connection to the parallel C14-decay research:** the C14-decay research (`05-RESEARCH-c14-decay.md`) defers claim `C14-TIME-01` ("a single respiration-cycle step represents seconds-to-minutes") to THIS glucose-critical-path source batch. The isotope-labeling timescale is biological (seconds–minutes per step), not nuclear — so C14-TIME-01 belongs to the biochem source family (S-GLY-1/S-GLY-2 or Lehninger), not the nuclear family. **Flag: the TCA RNG-weight mechanism and the C14-decay framing share the biochem timescale source C14-TIME-01; approve it once in this batch and both researches inherit it.**

### The RNG weight VALUES are a separate, high-stakes, human-decided claim

**Critical distinction the human must make explicit:**

- The **mechanism** (citrate prochirality → two acetyl carbons distinguishable on turn 1, equivalent after turn 1) is a sourced scientific claim → `TCA-RNG-CITRATE-PROCHIRALITY-01`, source-backed (S-TCA-1 or S-TCA-3).
- The **RNG weight VALUES** (e.g. "P(acetyl carbon exits as CO2 on turn 1) = 0.5; P(turn 2) = 0.5" — or a skewed split if the game models a specific stereochemical bias) are a **game-design decision grounded in the mechanism**. The source backs *that the two fates are distinguishable and become equivalent*; the human picks the *exact probabilities* for pedagogy. These land as separate claims `TCA-RNG-WEIGHT-01`, `TCA-RNG-WEIGHT-02`, ... — **high-stakes, individually reviewed** (option c), with `review_notes` recording the human's pedagogical choice and the mechanism it's grounded in.

This split is the reason option (c) HYBRID is the advisory recommendation: the mechanism claim can be routine/source-inherited, but the weight-value claims must be individually reviewed — they are game design, not restatements.

---

## 5. SC#5 Operational Check (gate status + what's needed)

**SC#5 text:** "CITE-01's per-claim checkpoint is operational: no scientific claim lands in code/content without a corresponding `approved` entry in the registry (enforced by the Phase 1 pre-ship gate at build time)."

**Gate status — VERIFIED OPERATIONAL this research.** I ran `tools/check_citations.py` directly:

| Test | Command | Result | Confirms |
|------|---------|--------|----------|
| PASS (all approved) | `--story tests/fixtures/story_pass.json --registry tests/fixtures/citations_pass.json` | `CITATION GATE PASSED: 2 claim reference(s) across 2 node(s) -- all approved.` (exit 0) | approved claims pass |
| FAIL-pending | `--story .../story_pass.json --registry .../citations_fail_pending.json` | `CITATION GATE FAILED: 0 missing + 1 unapproved ... [UNAPPROVED] node 'fixture.ending' references claim_id 'placeholder-claim-2' -- status is 'pending'` (exit 1) | pending fails (strict ==) |
| FAIL-missing (empty real registry) | `--story .../story_pass.json --registry data/citations.json` (the real `{}` file) | `CITATION GATE FAILED: 2 missing + 0 unapproved ... [MISSING] node 'fixture.intro' references claim_id 'placeholder-claim-1' -- not in registry` (exit 1) | any referenced claim absent from the real registry fails the build |

The gate's three-way exit codes (0/1/2), the strict-equality predicate (`approval_status == "approved"` in `c14/citations.py:100-109` — a `rejected` claim fails identically to `pending`, no Pitfall 6 regression), and the duplicate-key hook (`c14/citations.py:29-46`) all behave per spec.

**What is needed to FULLY satisfy SC#5 (beyond the gate already working):**

1. **Populate the first batch.** The real `data/citations.json` is `{}` — so ANY story node referencing a real `claim_id` currently fails the gate (missing). SC#5 is about the gate *enforcing* on real data, not just fixtures. Satisfying SC#5 means: once the human approves the first batch (workflow decision + sources from §3/§4), the corresponding `claim_id` entries land in `data/citations.json` with `approval_status: "approved"`, and a real story referencing them passes the gate. **Until the first batch is populated, the gate is operational but has no real approved claims to enforce on.** This is the SC#4↔SC#5 link: SC#4 (agree workflow + approve first batch) is what makes SC#5 meaningful on real content.
2. **Wire the gate into the build/CI.** SC#5 says "enforced by the Phase 1 pre-ship gate at build time." The gate exists and works; the planner should confirm it is invoked at pre-ship (e.g. in the release/CI script) — this is a wiring task, not a gate-correctness gap. (If a pre-ship hook already invokes `tools/check_citations.py`, SC#5 is fully satisfied once the first batch lands; if not, add the invocation.)
3. **(If option b/c/d chosen) add `data/sources.json` + optionally `tools/check_sources.py`.** Per §2, the source registry is a separate file the Phase 1 gate does not read. If the human picks a source-aware workflow, the planner implements the `sources.json` loader + (optional) the second gate. This is an implementation task; the research confirms the Phase 1 gate stays unchanged and backward-compatible.

**Bottom line: SC#5 is already satisfied at the gate-mechanics level (verified this research). The remaining work to fully satisfy SC#5 on real content is the SC#4 deliverable: agree the workflow, approve the first batch, and land the approved claim entries in `data/citations.json`. No gate code change is required for the strict-per-claim (a) or hybrid (c) options.**

---

## 6. Throughput Estimate (Phase 5 approval load)

Grounded in Pitfall 7's "hundreds of claims" estimate and the glucose-critical-path scope:

| Scope | Claim count estimate | Source count (batch-by-source) | Human time (option a / option c) |
|------|----------------------|--------------------------------|----------------------------------|
| **Glucose first batch (this research)** — 21 enzymes × ~3–5 claims (mechanism + substrate/product + cofactor + carbon-fate where relevant) | **~60–105 claims** | ~3–6 sources (LibreTexts glycolysis + LibreTexts PDH/TCA + Lehninger TCA + a PDB-structures batch of ~5–8) | a: ~5–9 h / c: ~1.5 h |
| TCA RNG weights (this research) | ~3–6 high-stakes claims (mechanism + N weight-value claims) | folded into the TCA source (Lehninger) | individual review (high-stakes) |
| **Cross-ref: C14-TIME-01** (deferred from C14-decay research; the respiration-cycle timescale biochem source) | 1 supporting claim | folded into the biochem source family (S-GLY-1/S-GLY-2 or Lehninger) | routine |
| **Parallel: anaerobic sources** (separate research, not yet present) | TBD | TBD | TBD |
| **Parallel: ATP/ETC sources** (separate research, not yet present) | TBD | TBD | TBD |
| **Full content (all 4 tracks)** — Pitfall 7's estimate | **~400 claims** | ~15–25 sources (pathway + structure batches per track) | a: ~33 h / c: ~6–8 h |

**Key throughput insight:** the glucose first batch is **~15–25% of the full-content claim load** and is the right size to validate the chosen workflow before the content marathon (Phases 7–9). If the human picks (c) HYBRID and the glucose batch reviews in ~1.5 h, the full-content approval load drops from Pitfall 7's ~33 h (strict per-claim) to a tractable ~6–8 h — the timeline-dominating risk is materially reduced without sacrificing safety on the load-bearing claims. If the human picks (a) STRICT PER-CLAIM, the glucose batch alone (~5–9 h) is the first real data point on whether Pitfall 7's ~33 h full-content estimate will hold — and is the moment to reconsider (c) if the throughput is untenable.

**Recommendation:** treat the glucose first batch as a **workflow calibration run**: approve it under the chosen option, measure the actual human time per claim, and if (a) proves too slow, switch to (c) before the content marathon. The schema extension (§2) supports both options without rework.

---

## 7. Cross-References to Parallel Research (avoid duplication)

This research focuses on the WORKFLOW + glucose critical-path + TCA-weight sources. Sibling Phase-5 research files cover other source families — the planner must not duplicate.

| Parallel research | Status | Covers | Boundary with THIS research |
|-------------------|--------|--------|------------------------------|
| **`05-RESEARCH-c14-decay.md`** (Pitfall 9) | **EXISTS** (read during this research) | C14 radioactive-decay timescale framing; nuclear-data sources (NUBASE2020, NuDat 3.0, IAEA LiveChart); nuclear-chemistry LibreTexts hub | Defers claim `C14-TIME-01` (the respiration-cycle biochem timescale, seconds–minutes) to THIS glucose-critical-path batch — it belongs to the biochem source family, not the nuclear family. **Approve C14-TIME-01 once here; both researches inherit it.** Uses the same claim_id convention (`C14-XX-NN`) that this research follows. |
| **Anaerobic-pathway sources** (fermentation) | **NOT YET PRESENT** in `.planning/phases/05-*/` at research time | Fermentation sources (lactate → pyruvate branch; the anaerobic framing decision SC#3) | Out of scope here. Note: the Chemistry LibreTexts "Biological Chemistry" bookshelf also contains a dedicated **"Fermentation in Food Chemistry (Graham)"** text (seen on the bookshelf page during this research) — that may be the candidate source for the anaerobic research, NOT this research. Flag to the anaerobic researcher. |
| **ATP / ETC sources** (oxidative phosphorylation) | **NOT YET PRESENT** | Oxidative phosphorylation / ETC / ATP synthase sources (the True-ending soul-jump chemistry; per-claim approval for ETC claims is a Phase 7+ gate per Pitfall 4 resolution) | Out of scope here. The soul-jump framing (Pitfall 4, RESOLVED) means ETC/ATP-synthase *chemistry claims* are approved in Phase 7+, but the *framing decision* is done. Lehninger's oxidative-phosphorylation chapter is the likely source — the ATP/ETC researcher should coordinate with this research's Lehninger source record to avoid duplicate source approvals. |

**Planner note:** the Phase 5 folder currently contains only `05-RESEARCH-c14-decay.md` + this file. When the anaerobic and ATP/ETC research files land, their source records should be added to the SAME `data/sources.json` (one shared source registry, not per-research files) so a source approved once is visible to all. The `source_id` namespace should be globally unique (e.g. `LIBRETEXTS-METAB-GLYCOLYSIS`, `LIBRETEXTS-FERMENTATION-GRAHAM`, `LEHNINGER-CH-OXPHOS`).

---

## 8. Open Questions for the Human

These are the specific decisions the human must make. This research does NOT resolve them.

1. **Which workflow option?** (a) STRICT PER-CLAIM / (b) BATCH-BY-SOURCE / (c) HYBRID ⭐ / (d) PER-SOURCE-RECORD. Advisory lean: (c). See §1 + comparison matrix. The user's currently-recorded choice (PROJECT.md Key Decisions) is per-claim checkpoint (closest to (a)); this research surfaces (c) as the option that preserves the per-claim safety guarantee on load-bearing claims while amortizing the rest.

2. **If (c) HYBRID: which claim categories are "high-stakes" (individual review) vs "routine" (source-inherited)?** Advisory high-stakes list in §1(c): RNG weight values, protonation defaults, carbon-fate claims, anything flagged contested. The human confirms/edits this taxonomy once, upfront.

3. **Is the separate-file schema (§2: `data/sources.json` + extended `data/citations.json`) acceptable, or does the human prefer a same-file `sources` section (which requires a loader change)?** The separate-file approach is zero-risk to the Phase 1 gate; the same-file approach is more compact but needs `c14/citations.py` extended to skip a reserved key. This is an implementation decision for the planner once the human picks the workflow.

4. **Which LibreTexts source to approve — the chem.libretexts.org Biological Chemistry / Metabolism modules (S-GLY-1/S-GLY-2), the bio.libretexts.org library (separate hub, not fetched in this research), or both?** The spec says "biochemistry libretext"; the chem.libretexts.org Metabolism hub is verified and is the natural home for glycolysis/PDH/TCA. There may be a parallel bio.libretexts.org hub with a general biochem text. The human picks the source family; this research recommends the verified chem.libretexts.org Metabolism hub as the primary, with Lehninger as the print cross-reference.

5. **Is Lehninger Principles of Biochemistry (Nelson & Cox) approved as the print cross-reference source?** If yes, the human confirms the edition + the chapter numbers for Glycolysis / Citric Acid Cycle / (later) Oxidative Phosphorylation. No ISBN is asserted here (per no-fabricated-science); the human records it at approval time.

6. **For the TCA RNG weights: does the human approve the MECHANISM (citrate prochirality, two-turn equivalence) as a source-inherited routine claim, and reserve the weight VALUES as individually-reviewed high-stakes claims?** This is the §1(c) / §4 split. The mechanism is sourced (Lehninger S-TCA-1, possibly Ogston S-TCA-3); the values are game design. Confirm the split.

7. **PDB cast for the glucose first batch: which ~5–8 structures?** Two are pre-verified (4PFK, 1CSC). The human picks the remaining 3–6 (hexokinase, pyruvate kinase, PDH E1, + 1–2 more), each web-verified at rcsb.org before its source record is marked approved. **Mandatory: every PDB ID in the final batch must be re-verified at rcsb.org (resolution + deposited citation) — the 1HKA-not-hexokinase finding (§3) shows memory-based PDB IDs are unreliable.**

8. **Should isotope-labeling primary literature (S-TCA-4) be sourced for the TCA-carbon-fate narrative, or is the Lehninger textbook summary sufficient for the first batch?** Advisory: sufficient for the first batch; commission a specific isotope-labeling paper only if the narrative explicitly cites the experimental evidence.

9. **Does the human want the optional `tools/check_sources.py` second gate (options b/c/d) built in Phase 5, or is the single Phase 1 gate enough with the source-registry as a non-enforced record?** Advisory: build it only if option (c)/(d) is chosen AND the human wants drift-detection; otherwise the source registry is documentation, not enforcement.

10. **Cross-dep with C14-decay research: confirm `C14-TIME-01` (respiration-cycle timescale) is approved in THIS batch (biochem source family), so the C14-decay framing inherits it.** The C14-decay research explicitly defers this claim here; approving it once avoids a duplicate.

---

## Sources

### Primary (HIGH confidence — verified live/resolvable during this research)
- **LibreTexts Biological Chemistry / Metabolism hub** — `https://chem.libretexts.org/Bookshelves/Biological_Chemistry/Supplemental_Modules_(Biological_Chemistry)/Metabolism` — **page fetched live 2026-08-15**, CC BY-NC-SA 4.0. Backs the biochem source family for S-GLY-1, S-GLY-2, and the C14-TIME-01 cross-ref. Exact glycolysis/PDH/TCA subpage URLs NOT individually verified — confirm at approval time.
- **RCSB PDB 4PFK** — `https://www.rcsb.org/structure/4PFK` — **page fetched live 2026-08-15**. Phosphofructokinase (*G. stearothermophilus*), 2.40 Å, X-RAY. PDB DOI 10.2210/pdb4PFK/pdb; primary citation Evans/Farrants/Hudson 1981, Philos Trans R Soc London ser B 293:53-62, DOI 10.1098/rstb.1981.0059, PubMed 6115424. Deposited bibliographic data read verbatim from the RCSB page.
- **RCSB PDB 1CSC** — `https://www.rcsb.org/structure/1CSC` — **page fetched live 2026-08-15**. Citrate synthase (*Gallus gallus*), 1.70 Å, X-RAY. PDB DOI 10.2210/pdb1CSC/pdb; primary citation Karpusas/Holland/Remington 1991, Biochemistry 30:6024-6031, DOI 10.1021/bi00238a028, PubMed 2043640.

### Secondary (MEDIUM confidence — real source, details flagged for verification)
- **Lehninger Principles of Biochemistry (Nelson & Cox)** — the canonical biochem textbook; covers glycolysis, PDH, TCA, oxidative phosphorylation. **CANDIDATE — verify edition + chapter numbers before approving. No ISBN asserted (per no-fabricated-science rule).** Backs S-GLY-3, S-TCA-1.

### Tertiary (LOW-MEDIUM confidence — NOT web-verified; flag for human verification)
- **Ogston, A. G. (1948)** — the historically primary reference for citrate prochirality. **CANDIDATE — verify exact bibliographic details (journal/volume/page/DOI) at approval time.** Backs S-TCA-3 if the human wants the primary mechanism source.
- **Isotope-labeling studies of TCA carbon fate** — no specific paper asserted (no-fabricated-science rule). Recommend commissioning a follow-up research step IF the narrative needs to cite the experimental evidence directly. For the first batch, Lehninger's summary is sufficient.

### Used for discovery / verification (NOT approved sources)
- **Wikipedia** — used only to cross-check well-known PDB IDs; NOT an approved source per project rules.
- **RCSB PDB 1HKA** — fetched live 2026-08-15 to test a memory-based PDB-ID guess; turned out to be HPPK (folate pathway), NOT hexokinase. **Documented as a cautionary finding** (§3) validating the verify-before-asserting discipline. NOT a candidate cast structure.

---

## Metadata

**Confidence breakdown:**
- Gate/registry mechanics (SC#5): **HIGH** — `tools/check_citations.py` + `c14/citations.py` read in full and the gate run against fixtures + the empty real registry; all exit codes + the strict-equality predicate confirmed.
- Workflow options (a/b/c/d) + schema extension: **HIGH** — grounded in the actual loader code (`c14/citations.py:80-109`); backward-compatibility argument verified against the loader's validation logic.
- LibreTexts Biological Chemistry / Metabolism hub: **HIGH** (hub + license verified live); exact glycolysis/PDH/TCA subpage URLs: **MEDIUM** (flagged for approval-time verification).
- PDB IDs 4PFK + 1CSC: **HIGH** (verified at rcsb.org, deposited data read from the pages).
- PDB IDs for the remaining cast: **LOW** (NOT asserted; marked CANDIDATE — verify at rcsb.org).
- Lehninger (S-GLY-3 / S-TCA-1): **MEDIUM** (real canonical textbook; edition/chapter not web-verified).
- Ogston 1948 (S-TCA-3): **LOW-MEDIUM** (recalled primary reference; exact citation NOT web-verified).
- TCA carbon-scrambling mechanism: textbook-standard (the science is well-established); the *specific claim text* still needs per-claim human approval.

**Research date:** 2026-08-15
**Valid until:** ~30 days for the workflow/schema design (stable — grounded in the committed gate code); the source candidates (LibreTexts pages, Lehninger edition, PDB entries) should be re-verified at approval time, especially PDB IDs (the 1HKA finding shows memory-based IDs are unreliable).
