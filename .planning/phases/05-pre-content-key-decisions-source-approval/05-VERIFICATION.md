---
phase: 05-pre-content-key-decisions-source-approval
verified: 2026-08-15T18:21:28Z
status: passed
score: 5/5 success criteria verified
re_verification: false
---

# Phase 5: Pre-Content Key Decisions + Source Approval — Verification Report

**Phase Goal:** The four science-framing decisions that block content authoring are resolved by the human, the per-claim approval workflow is operationalized (batch-by-source agreed), and the first set of sources for the glucose critical-path + TCA weights is pre-approved — unblocking the content phases. This is a PARALLEL track that runs alongside Phases 2–4 (engineering on placeholder content) and gates Phases 6–9 content.

**Verified:** 2026-08-15T18:21:28Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Phase 5 Success Criteria)

| # | Truth (Success Criterion) | Status | Evidence |
|---|---------------------------|--------|----------|
| 1 | ATP/True-Ending carbon-fate reframing is RESOLVED via the soul-jump reframing + documented metaphor (metamorphosis/sense-moves-with-electron) in PROJECT.md Key Decisions | ✓ VERIFIED | PROJECT.md row 104: "RESOLVED 2026-08-13 via the **soul-jump reframing**" + "Narrative metaphor (decided 2026-08-15; option b sense-moves-with-electron, REFRAMED as metamorphosis): ...caterpillar turning into a butterfly, the carbon body is shed as CO2 (the chrysalis stage) while the narrative POV/sense follows the electrons onward ('my electrons power the cell'). The hero transforms, not dies." Outcome = "— Resolved (soul-jump; metaphor = metamorphosis)". grep confirmed `metaphor = metamorphosis` + `sense-moves-with-electron`. |
| 2 | C14 radioactive-decay bad-ending timescale framing is RESOLVED via DROP (radioactive decay removed; cycle-trap-until-host-death retained) + documented | ✓ VERIFIED | PROJECT.md row 105: "RESOLVED via DROP — radioactive decay is DROPPED as a bad-ending trigger. The cycle-trap-until-host-death trigger (spec.md line 18: 'RNG stay in a cycle long enough for the host organism passed') is the sole timescale-based bad-ending. No radioactive-decay citation (NUBASE2020) needed. No C14-TIME-01 claim needed." Outcome = "— Resolved via DROP (2026-08-15)". spec.md line 18 carries the in-place `<!-- Pitfall 9 NOTE (2026-08-15): Resolved via DROP ... -->` HTML-comment annotation (prose preserved verbatim per the annotation convention; grep confirmed). NUBASE2020-C14 absent from data/sources.json; C14-TIME-01 absent from data/citations.json (DROPPED entries eliminated — python3.6 confirmed). |
| 3 | Anaerobic-pathway framing is RESOLVED (option d) + documented in PROJECT.md Key Decisions; invariant re-worded; STORY-02/STORY-05 updated | ✓ VERIFIED | PROJECT.md row 97: "RESOLVED via option (d) CHOICE-FOR-GLUCOSE + BAD-FOR-FA/ALC — glucose gets a 3-ending anaerobic branch (lactic=Good/retained, ethanolic=Normal/CO2, crisis=Bad); FA + alcohol get the Bad-ending trigger (O2-depletion energy crisis)." PROJECT.md row 95: invariant re-worded to "Aerobically, 1 True + several Normal/Good + many Bad endings are reachable per character. Anaerobically, the True ending (soul-jump via ETC) is NOT reachable (no O2 → no ETC)..." (grep confirmed `Aerobically, 1 True`). spec.md line 14 carries the in-place `<!-- Phase 5 NOTE (2026-08-15): Anaerobic framing resolved via option (d)... -->` annotation. REQUIREMENTS.md STORY-02 (line 24): v1-scope parenthetical appended (aerobic reachability + character-specific anaerobic reachability + ETC/O2 finding). REQUIREMENTS.md STORY-05 (line 27): "framing = (d) choice-for-glucose + bad-for-FA/ALC (resolved Phase 5); host = mammal/human (lactic fermentation)" (grep confirmed both). PROJECT.md row 108: ETC-O2 finding acknowledged. |
| 4 | Batch-by-source vs strict per-claim approval is RESOLVED via option (c) HYBRID + high-stakes taxonomy + routine-claim warning flag; registry holds the first batch of approved sources (glucose critical-path + TCA RNG weights) | ✓ VERIFIED | PROJECT.md row 106: "RESOLVED via option (c) HYBRID — sources approved up front (batch), high-stakes claims individually reviewed. HIGH-STAKES taxonomy (individual per-claim review): RNG-weights, protonation-defaults, carbon-fate, contested. ROUTINE (source-inherited fast-track): enzyme-catalyzes-reaction-X, enzyme name/EC/cofactor, PDB existence/resolution/citation, pathway ordering. ENHANCEMENT (user-requested): routine/source-inherited claims are FLAGGED with `review_tier: \"routine\"` + `inherits_source_approval: true`..." (grep confirmed). **data/sources.json** (python3.6 count): 5 total → **4 approved** (LIBRETEXTS-METAB-GLYCOLYSIS, LIBRETEXTS-METAB-TCA, PDB-4PFK, PDB-1CSC) + 1 rejected (LEHNINGER-CH-CITRIC_ACID_CYCLE, per license concern) + 0 pending. **data/citations.json** (python3.6 count): 5 total → **5 approved** (GLY-PFK-01, TCA-RNG-CITRATE-PROCHIRALITY-01, TCA-RNG-WEIGHT-01, CAST-PFK-PDB-01, CAST-CSC-PDB-01) + 0 rejected + 0 pending. review_tier correctly split: 2 high-stakes (TCA-RNG-*) with inherits_source_approval=false; 3 routine (GLY-PFK-01, CAST-*-PDB-01) with inherits_source_approval=true. The 2 high-stakes claims' source_id was swapped LEHNINGER → LIBRETEXTS-METAB-TCA (Jakubowski Ch 16) after the Lehninger rejection; review_notes document the honest caveat. |
| 5 | CITE-01's per-claim checkpoint is operational: no scientific claim lands in code/content without a corresponding `approved` entry (enforced by the Phase 1 pre-ship gate at build time) | ✓ VERIFIED | **Runtime proof (fresh temp fixture, not the SUMMARY's):** created `/tmp/opencode/verifier_sc5_fixture.json` (2 nodes referencing all 5 approved claim_ids), ran `python3.6 tools/check_citations.py --story <temp> --registry data/citations.json` → **exit 0** + `CITATION GATE PASSED: 5 claim reference(s) across 2 node(s) -- all approved.` **Regression check (no Pitfall 6 regression):** ran the gate against `tests/fixtures/story_pass.json --registry data/citations.json` → **exit 1** + `[MISSING]` (placeholder-claim-1/2 absent from real registry — unchanged pre-Phase-5 behavior). **Pitfall 6 predicate preserved:** `c14/citations.py:109` confirms `entry is not None and entry.get("approval_status") == self.APPROVED` (strict equality, NOT `!= "pending"` — a rejected claim fails identically to a pending one). **Unit tests:** 12/12 citation tests pass (test_fail_rejected confirms the rejected=pending-fail behavior; test_pass/test_fail_missing/test_fail_pending/test_malformed + 6 loader tests all green). The gate loads the extended registry (with source_id/review_tier/inherits_source_approval/review_notes/claim_text) cleanly — backward-compatible (loader ignores unknown fields, c14/citations.py:87-97 only checks dict + approval_status). |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.planning/PROJECT.md` Key Decisions rows 104, 105, 95, 97, 106, 107, 108 | 4 framing decisions RESOLVED + ending distribution + ETC-O2 finding + workflow decision | ✓ VERIFIED | All rows present with RESOLVED outcomes (read full file; grep-confirmed). Row 104 (metaphor=metamorphosis), 105 (DROP), 95 (invariant re-worded), 97 (anaerobic option d), 106 (workflow option c HYBRID + taxonomy + warning flag), 107 (ending distribution), 108 (ETC-O2 finding). Footer updated 2026-08-15. |
| `spec.md` line 14, 15, 18 annotations | Phase 5 NOTE (line 14), Pitfall 4 NOTE (line 15), Pitfall 9 NOTE (line 18) — in-place HTML comments, prose untouched | ✓ VERIFIED | All 3 annotations present (grep confirmed). Line 14 = Phase 5 NOTE (anaerobic framing d + invariant re-wording). Line 15 = Pitfall 4 NOTE (soul-jump, pre-existing). Line 18 = Pitfall 9 NOTE (DROP). Prose preserved verbatim per the annotation convention. |
| `.planning/REQUIREMENTS.md` STORY-02, STORY-05 | STORY-02 v1-scope parenthetical appended; STORY-05 framing=(d) | ✓ VERIFIED | STORY-02 (line 24): aerobic/anaerobic reachability + ETC/O2 finding parenthetical appended. STORY-05 (line 27): "framing = (d) choice-for-glucose + bad-for-FA/ALC (resolved Phase 5); host = mammal/human (lactic fermentation)". Footer updated 2026-08-15. |
| `data/sources.json` | First-batch source registry; ≥1 approved source for glucose critical-path + TCA | ✓ VERIFIED | 5 records: 4 approved + 1 rejected. Approved: LIBRETEXTS-METAB-GLYCOLYSIS, LIBRETEXTS-METAB-TCA, PDB-4PFK, PDB-1CSC. Rejected: LEHNINGER-CH-CITRIC_ACID_CYCLE (license concern; provenance retained). NUBASE2020-C14 absent (DROPPED). Bare JSON object keyed by source_id. 50 lines. |
| `data/citations.json` | First-batch seed claims; ≥1 approved claim; extended schema fields present | ✓ VERIFIED | 5 records, all approved. Each carries both README-required fields (claim, source_type, source; pdb_id+resolution_angstrom for PDB) AND extended fields (source_id, claim_text, review_tier, inherits_source_approval, review_notes for high-stakes). review_tier: 2 high-stakes (TCA-RNG-*, inherits=false) + 3 routine (GLY-PFK-01, CAST-*-PDB-01, inherits=true). C14-TIME-01 absent (DROPPED). 68 lines. |
| `data/citations.README.md` | Extended schema docs (sources.json section + 5 new per-claim fields + warning-flag mechanism + backward-compat note) | ✓ VERIFIED | 137 lines. Documents: sources.json source registry section + source record schema table + duplicate-key hook convention; 5 new per-claim fields (source_id, claim_text, review_tier, inherits_source_approval, review_notes); corrected load-time-validation paragraph (loader enforces ONLY dict + approval_status); backward-compat note; routine-claim warning-flag mechanism section (hybrid workflow c). |
| `tools/check_citations.py` | Pre-ship gate; exits 0 on approved, 1 on missing/unapproved, 2 on config error | ✓ VERIFIED | 123 lines. Unchanged from Phase 1 (no modifications in Phase 5 — backward-compatible by construction). Imports CitationRegistry.load + collect_claim_ids. Three-way exit codes. Runtime-proven on real approved data (exit 0) + placeholder fixture (exit 1 [MISSING]). |
| `c14/citations.py` | Loader; strict equality predicate (Pitfall 6); ignores unknown fields (backward-compat) | ✓ VERIFIED | 131 lines. Unchanged from Phase 1. Line 109: `entry is not None and entry.get("approval_status") == self.APPROVED` (strict equality). Lines 87-97: load-time validation checks ONLY dict + approval_status (ignores source_id/review_tier/inherits_source_approval/review_notes/claim_text). Duplicate-key hook (_no_duplicate_keys) present. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| Story fixture (claim_ids) | data/citations.json (registry) | `tools/check_citations.py --story <fixture> --registry data/citations.json` | WIRED | Runtime-proven: exit 0 "CITATION GATE PASSED: 5 claim reference(s) across 2 node(s) -- all approved" on the 5 approved claim_ids; exit 1 [MISSING] on placeholder fixture. |
| Gate | Loader | `from c14.citations import CitationRegistry` (tools/check_citations.py:40) | WIRED | Gate imports + calls CitationRegistry.load(); loader returns registry; gate calls .contains()/.is_approved()/.status(). All wired + exercised at runtime. |
| Loader | data/citations.json | `CitationRegistry.load(path)` → `json.load(f, object_pairs_hook=_no_duplicate_keys)` | WIRED | Loader opens the real extended registry (5 claims with extended fields), validates dict + approval_status, ignores extended fields. Runtime-proven (gate ran successfully on the real file). |
| Claims (citations.json) | Sources (sources.json) | `source_id` field links claim → source record | WIRED | Each of the 5 claims carries a `source_id` matching a key in data/sources.json (GLY-PFK-01→LIBRETEXTS-METAB-GLYCOLYSIS; TCA-RNG-*→LIBRETEXTS-METAB-TCA; CAST-PFK-PDB-01→PDB-4PFK; CAST-CSC-PDB-01→PDB-1CSC). The gate never reads sources.json (process-convention only) — verified. |
| PROJECT.md Key Decisions | spec.md annotations | In-place HTML comments link "See .planning/PROJECT.md Key Decisions row N" | WIRED | spec.md line 14 (Phase 5 NOTE) → PROJECT.md Key Decisions; line 18 (Pitfall 9 NOTE) → "row 105"; line 15 (Pitfall 4 NOTE) → PROJECT.md Key Decisions. All cross-references resolve. |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| CITE-01 (Every scientific claim/citation is verified against an approved source + explicitly human-approved via per-claim checkpoint before landing in code/content) | ✓ OPERATIONALIZED (Phase 5 scope) | None. CITE-01's traceability row in REQUIREMENTS.md remains "Pending" — this is CORRECT: the full requirement (every claim in ALL content) is satisfied across Phases 5-9 as content is authored. Phase 5's SC#5 role was to operationalize the per-claim checkpoint (the gate, proven on real data) + approve the first batch (5 claims + 4 sources approved). The gate now blocks any story referencing an unapproved/missing claim. Content phases (7-9) author claims into the same registry + run the same gate. No blocker. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `data/citations.README.md` | 25, 47, 73, 77, 79 | "placeholder" | ℹ️ Info | Legitimate — refers to the `source_type: "placeholder"` enum value (fixture-data-only) + the example placeholder entry. Documentation, not a stub. |
| `data/story/intro.json` | 6, 9, 18, 19, 28, 29 | "placeholder" (placeholder-intro, placeholder:structure, placeholder-good/bad-ending) | ℹ️ Info | Phase 2's known placeholder story nodes (explicit placeholder content for architecture testing). NOT a Phase 5 artifact — Phase 5.1 (Story Graph Design) will replace these. Out of Phase 5 scope. |
| `.planning/PROJECT.md` | 75 | "radioactive decay of C14 (Pitfall 9 — framing still pending)" | ⚠️ Warning | Stale descriptive prose in the "Ending semantics" section. Says "framing still pending" when Key Decisions row 105 records RESOLVED via DROP (2026-08-15). The authoritative Key Decisions table is correct; only the descriptive prose is stale. Could mildly confuse a future reader. Recommend updating in a Phase 10/11 docs-consistency pass. NOT a goal-achievement gap (the decision IS authoritatively documented in row 105 + spec.md line 18 annotation). |
| `.planning/PROJECT.md` | 33 | "Bad (...radioactive decay / cycle-trapped)" in Active requirements | ⚠️ Warning | Same staleness — descriptive requirement prose still lists "radioactive decay" in the Bad ending enumeration. The v1-scope reality (DROP) is in Key Decisions row 105. Cosmetic consistency issue. |
| `.planning/REQUIREMENTS.md` | 24 | STORY-02 Bad ending lists "radioactive decay" | ⚠️ Warning | The appended v1-scope parenthetical correctly captures the aerobic/anaerobic re-wording, but the original Bad-ending enumeration still lists "radioactive decay". Consistency issue only — the authoritative decision is in PROJECT.md row 105. |

**No blocker anti-patterns found.** The ⚠️ warnings are documentation-consistency issues in descriptive prose (the authoritative Key Decisions table + spec.md annotations are all correct). They do not block any success criterion.

### Human Verification Required

None blocking. The automated verification covers all 5 success criteria against the actual codebase/planning artifacts. Notes for the human:

1. **Scientific accuracy of the approved claims** — the human is the recorded approver (`approved_by: "human"`, `approved_date: "2026-08-15"`) for all 5 claims + 4 sources. The honest caveat on the 2 high-stakes TCA RNG claims (the LibreTexts Jakubowski 16.02 page covers the prochirality MECHANISM — citrate synthase (S)-citryl-CoA + aconitase 180-degree flip — but does NOT explicitly use "prochiral" for citrate, nor state the 0.5/0.5 first-turn-vs-second-turn probability) is documented in both claims' `review_notes` for Phase 7 reconsideration if a more explicit source is desired. This is a non-blocking note, not a gap.

2. **The "build time" enforcement model** — the gate is a manual pre-ship check (consistent with Phase 1's design for this PyMOL-plugin project, which has no CI pipeline). It is operational (proven on real data) and exits non-zero on any unapproved/missing claim. Wiring it into an automated CI/build step is a future concern, not a Phase 5 gap.

### Gaps Summary

**No gaps found.** All 5 Phase 5 success criteria are verified against the actual codebase/planning artifacts (not SUMMARY claims):

- **SC#1** (ATP/True-Ending reframing + metaphor): PROJECT.md row 104 RESOLVED with metamorphosis/sense-moves-with-electron. ✓
- **SC#2** (C14-decay framing): PROJECT.md row 105 RESOLVED via DROP + spec.md line 18 Pitfall 9 NOTE annotation. NUBASE2020-C14 + C14-TIME-01 eliminated. ✓
- **SC#3** (Anaerobic framing): PROJECT.md row 97 RESOLVED via option (d) + row 95 invariant re-worded ("Aerobically, 1 True...") + spec.md line 14 Phase 5 NOTE + REQUIREMENTS STORY-02/STORY-05 updated. ✓
- **SC#4** (Source-approval workflow + first batch): PROJECT.md row 106 RESOLVED via option (c) HYBRID + high-stakes taxonomy + routine-claim warning flag. data/sources.json: 4 approved sources. data/citations.json: 5 approved claims with correct review_tier/inherits_source_approval. ✓
- **SC#5** (Per-claim gate operational on real data): Runtime-proven — gate exits 0 "CITATION GATE PASSED" on the 5 approved claims; exits 1 [MISSING] on placeholder fixture (no Pitfall 6 regression); 12/12 unit tests pass; strict-equality predicate preserved at c14/citations.py:109. ✓

The 3 ⚠️ warnings (stale descriptive prose in PROJECT.md lines 33/75 + REQUIREMENTS.md line 24 still mentioning "radioactive decay") are documentation-consistency issues — the authoritative Key Decisions table + spec.md annotations are all correct. Recommended for a Phase 10/11 docs-consistency pass but NOT blocking.

Phase 5 unblocks Phases 5.1 (Story Graph Design), 6 (Qt UI MVP), and 7-9 (content authoring). The per-claim gate is operational on real approved data; the first batch of glucose critical-path + TCA RNG sources/claims is approved; the 4 science-framing decisions are resolved + documented.

---

_Verified: 2026-08-15T18:21:28Z_
_Verifier: OpenCode (gsd-verifier)_
