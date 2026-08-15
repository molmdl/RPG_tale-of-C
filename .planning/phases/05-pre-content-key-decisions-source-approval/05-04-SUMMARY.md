---
phase: 05-pre-content-key-decisions-source-approval
plan: 04
subsystem: data
tags: [sources.json, citations, schema, hybrid-workflow, pending, first-batch]

# Dependency graph
requires:
  - phase: 01 (Foundations & Citation Gate)
    provides: the Phase 1 citation gate (tools/check_citations.py) whose predicate approval_status == "approved" is preserved UNCHANGED; the loader (c14/citations.py:87-97) that ignores unknown fields so the extended schema loads with zero change
  - phase: 05 Plan 05-03
    provides: SC#4 source-approval WORKFLOW decision = option (c) HYBRID + user-requested routine-claim warning flag (the branch this plan implements: CREATE data/sources.json; populate source_id/review_tier/inherits_source_approval/review_notes/claim_text)
  - phase: 05 05-RESEARCH-source-approval.md
    provides: the two-file schema extension (separate data/sources.json the gate never reads + extended data/citations.json) + the exact source_id/claim_id names + reference strings + the 5 first-batch candidate sources + 5 seed claims
provides:
  - data/sources.json (NEW) — the Phase 5+ source registry; 5 PENDING first-batch candidate source records for the glucose critical-path + TCA RNG weights (workflow b/c/d structure; the Phase 1 gate never reads it)
  - data/citations.json (extended) — 5 PENDING seed first-batch claims carrying BOTH the existing README-required fields (claim, source_type, source; pdb_id+resolution_angstrom for PDB) AND the new extended fields (claim_text, source_id, review_tier, inherits_source_approval, review_notes)
  - data/citations.README.md (extended) — schema docs for the new fields + the new sources.json file + the routine-claim warning-flag mechanism + the corrected load-time-validation paragraph + the backward-compat note
  - SC#4 registry STRUCTURE in place + SC#5 enforcement proven on real extended data (gate loads the extended registry + exits 1; seed claims proven pending) — the human's Plan 05 first-batch approval checkpoint is UNBLOCKED
affects: [Plan 05-05, Phase 7, Phase 8, Phase 9]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hybrid source-approval schema (workflow c): separate data/sources.json keyed by source_id (gate never reads it) + extended data/citations.json claims carrying source_id (links to sources.json), review_tier (high-stakes|routine), inherits_source_approval (bool), review_notes (mandatory for high-stakes), claim_text (full assertion coexisting with the claim one-liner). All approval_status=pending until the human approves in Plan 05."
    - "Routine-claim warning flag (user-requested): routine claims carry review_tier='routine' + inherits_source_approval=true so the human can spot-check them at leisure by filtering on review_tier=routine or inherits_source_approval=true. VISIBILITY mechanism, NOT a blocking gate — the Phase 1 gate still passes routine claims via the source's approval."
    - "Backward-compatible schema extension: the loader (c14/citations.py:87-97) ignores the extended fields (only enforces dict + approval_status), so the extended registry loads cleanly with zero loader change; the gate predicate approval_status == 'approved' (strict equality, Pitfall 6) is untouched; data/sources.json is a separate file the gate never opens."

key-files:
  created:
    - data/sources.json
  modified:
    - data/citations.json
    - data/citations.README.md

key-decisions:
  - "Workflow branch taken = (c) HYBRID (per Plan 05-03): data/sources.json CREATED (not skipped — option a would have skipped it). 5 first-batch candidate source records populated, ALL pending."
  - "5 source_ids populated (all pending): LIBRETEXTS-METAB-GLYCOLYSIS, LIBRETEXTS-METAB-TCA, LEHNINGER-CH-CITRIC_ACID_CYCLE, PDB-4PFK, PDB-1CSC. NUBASE2020-C14 ELIMINATED (per Plan 01 DROP — radioactive decay removed as a bad-ending trigger)."
  - "5 claim_ids populated (all pending): GLY-PFK-01 [routine], TCA-RNG-CITRATE-PROCHIRALITY-01 [high-stakes], TCA-RNG-WEIGHT-01 [high-stakes], CAST-PFK-PDB-01 [routine], CAST-CSC-PDB-01 [routine]. C14-TIME-01 ELIMINATED (per Plan 01 DROP)."
  - "Routine-claim warning flag applied: routine claims (GLY-PFK-01, CAST-PFK-PDB-01, CAST-CSC-PDB-01) carry review_tier=routine + inherits_source_approval=true; high-stakes claims (TCA-RNG-CITRATE-PROCHIRALITY-01, TCA-RNG-WEIGHT-01) carry review_tier=high-stakes + inherits_source_approval=false + mandatory review_notes."
  - "NO source or claim auto-approved — every entry is pending; the human approves them in Plan 05's checkpoint."

patterns-established:
  - "Two-file source-approval registry: data/sources.json (source records, keyed by source_id, gate-blind) + data/citations.json (claim records, keyed by claim_id, gate-read, extended with source_id linking to sources.json). Future content batches (Phase 7/8/9) add source records to the SAME sources.json (one shared registry) + claims to citations.json using the same schema."
  - "Seed-claim-first-batch pattern: front-load the SOURCE approval + a few representative/seed claims per batch (the full ~60-105 glucose claims get authored in Phase 7 when the content is written); the seed claims demonstrate the schema + ground the load-bearing high-stakes claims (TCA RNG)."

# Metrics
duration: 4min
completed: 2026-08-15
---

# Phase 5 Plan 04: Schema Implementation + First-Batch Population Summary

**Hybrid-workflow (c) source registry created (data/sources.json, 5 pending sources) + extended data/citations.json seeded with 5 pending claims (glucose critical-path + TCA RNG weights); Phase 1 gate backward-compatible (loader ignores extended fields, gate exits 1 on the extended registry, all entries pending for human approval in Plan 05)**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-08-15T15:28:22Z
- **Completed:** 2026-08-15T15:32:32Z
- **Tasks:** 2 (both type=auto, no checkpoints — fully autonomous)
- **Files modified:** 3 (1 created + 2 modified)

## Accomplishments
- Implemented the source-approval schema chosen in Plan 03 (workflow = (c) HYBRID): created `data/sources.json` (NEW — a bare JSON object keyed by `source_id`, the Phase 1 gate never reads it) and extended `data/citations.json` with the new fields (`source_id`, `claim_text`, `review_tier`, `inherits_source_approval`, `review_notes`) — backward-compatible with the Phase 1 gate (the loader `c14/citations.py:87-97` ignores unknown fields; the gate predicate `approval_status == "approved"` is untouched).
- Populated the FIRST BATCH per SC#4 (glucose critical-path + TCA RNG weights): 5 PENDING candidate source records + 5 PENDING seed claims. NO source or claim was auto-approved — every entry is `pending`; the human approves them in Plan 05's checkpoint.
- Documented the new schema in `data/citations.README.md`: a new "data/sources.json — Source Registry (Phase 5+)" section (schema fields + duplicate-key hook convention), the extended per-claim schema table (5 new fields), the corrected load-time-validation paragraph (loader enforces ONLY dict + approval_status, NOT claim/source_type/source), the backward-compat note, and the routine-claim warning-flag mechanism (filter on `review_tier=routine` or `inherits_source_approval=true` for leisure spot-check; NOT a blocking gate).
- Verified SC#5 enforcement on real extended data: the loader loads the extended `data/citations.json` cleanly ("loader OK 5 claims"); the gate `tools/check_citations.py` exits 1 with `[MISSING]` on the fixture's placeholder claims (loads the extended registry WITHOUT a config error — backward-compatible) and still exits 1; the seed claims' pending status is proven by the `all(approval_status=='pending')` assertion. The direct `[UNAPPROVED]`-on-pending-seed-claim proof lands in Plan 05 (which mirrors a seed claim_id into a temp fixture).
- Honored the Plan 01 DROPs: NUBASE2020-C14 (source) and C14-TIME-01 (claim) were NOT populated (radioactive decay was removed as a bad-ending trigger). `tests/fixtures/citations_pass.json` was left UNCHANGED (placeholder claims for gate testing).

## Task Commits

Each task was committed atomically:

1. **Task 1: Create data/sources.json + extend data/citations.README.md schema docs (hybrid workflow)** - `7f501a4` (feat)
2. **Task 2: Populate the PENDING first-batch seed claims in data/citations.json (glucose + TCA RNG)** - `9da0d68` (feat)

**Plan metadata:** `pending` (docs: complete plan — committed after SUMMARY/STATE)

## Files Created/Modified
- `data/sources.json` (CREATED) — the Phase 5+ source registry; 5 PENDING first-batch candidate source records keyed by `source_id` (LIBRETEXTS-METAB-GLYCOLYSIS, LIBRETEXTS-METAB-TCA, LEHNINGER-CH-CITRIC_ACID_CYCLE, PDB-4PFK, PDB-1CSC); bare JSON object; fields: reference, url, license, source_type, pdb_doi (PDB only), approval_status (all "pending"), notes; no approved_by/approved_date yet.
- `data/citations.json` (MODIFIED — was `{}`) — 5 PENDING seed first-batch claims keyed by `claim_id` (GLY-PFK-01, TCA-RNG-CITRATE-PROCHIRALITY-01, TCA-RNG-WEIGHT-01, CAST-PFK-PDB-01, CAST-CSC-PDB-01); each carries both existing README-required fields (claim, source_type, source; pdb_id+resolution_angstrom for PDB) AND the new extended fields (claim_text, source_id, review_tier, inherits_source_approval, review_notes for high-stakes); all approval_status="pending".
- `data/citations.README.md` (MODIFIED) — extended with: (a) new "data/sources.json — Source Registry (Phase 5+)" section + source record schema table + duplicate-key hook convention; (b) 5 new rows in the per-claim schema table (source_id, claim_text, review_tier, inherits_source_approval, review_notes); (c) corrected load-time-validation paragraph (loader enforces ONLY dict + approval_status); (d) backward-compat note (extended fields ignored by loader, c14/citations.py:87-97); (e) routine-claim warning-flag mechanism section (hybrid workflow c); (f) "Per-source-type required fields" header relabeled "(recommended, NOT load-time-enforced)" for internal consistency; (g) See also extended to reference data/sources.json + the Phase 5 research file.

## Decisions Made

- **Workflow branch = (c) HYBRID (per Plan 05-03):** `data/sources.json` was CREATED (option a would have skipped it; b/c/d create it). This is the branch the plan's Task 1 took based on the human's Plan 03 decision. Rationale: documented in 05-03-SUMMARY — honors both the per-claim safety guarantee on load-bearing claims AND Pitfall 7's timeline risk.
- **5 source_ids populated (all pending):** LIBRETEXTS-METAB-GLYCOLYSIS, LIBRETEXTS-METAB-TCA, LEHNINGER-CH-CITRIC_ACID_CYCLE, PDB-4PFK, PDB-1CSC. These are the candidate sources from `05-RESEARCH-source-approval.md` §3 (glucose critical-path) + §4 (TCA RNG weights). The 2 PDB IDs (4PFK, 1CSC) were web-verified at rcsb.org 2026-08-15 (resolution + primary citation read from the RCSB page); the LibreTexts hubs were verified live 2026-08-15 (exact subpage URLs flagged for approval-time confirmation); Lehninger is a CANDIDATE (human to confirm edition + chapter). NUBASE2020-C14 was ELIMINATED per Plan 01 DROP.
- **5 claim_ids populated (all pending):** GLY-PFK-01 [routine, libretexts], TCA-RNG-CITRATE-PROCHIRALITY-01 [high-stakes, textbook — grounds the TCA shuffle MECHANISM], TCA-RNG-WEIGHT-01 [high-stakes, textbook — game-design 0.5/0.5 RNG weight VALUE], CAST-PFK-PDB-01 [routine, pdb], CAST-CSC-PDB-01 [routine, pdb]. These are the SEED entries demonstrating the schema; the full ~60-105 glucose claims get authored in Phase 7. C14-TIME-01 was ELIMINATED per Plan 01 DROP.
- **Routine-claim warning flag applied:** routine claims (GLY-PFK-01, CAST-PFK-PDB-01, CAST-CSC-PDB-01) carry `review_tier="routine"` + `inherits_source_approval=true` (the user-requested warning flag — the human spot-checks these at leisure; NOT a blocking gate); high-stakes claims (TCA-RNG-CITRATE-PROCHIRALITY-01, TCA-RNG-WEIGHT-01) carry `review_tier="high-stakes"` + `inherits_source_approval=false` + mandatory `review_notes` (individual per-claim review in Plan 05).
- **No gate/loader code changed:** `c14/citations.py` and `tools/check_citations.py` were NOT modified (the loader already ignores unknown fields; the gate is unchanged). `tools/check_sources.py` was NOT created (deferred optional/advisory work). The change is data + docs only — backward-compatible by construction.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed an internally-inconsistent README header for full documentation accuracy**
- **Found during:** Task 1 (extending data/citations.README.md)
- **Issue:** The existing "Per-source-type required fields" section header said "(load-time validation, recommended)" which was inconsistent with the corrected load-time-validation paragraph (the loader does NOT enforce per-source-type fields at load time — it only enforces dict + approval_status). The plan's Task 1 explicitly instructed to "correct the existing README line 44 (which inaccurately claims the loader validates claim/source_type/source)"; the section header was part of the same inaccurate framing.
- **Fix:** Relabeled the header to "(recommended, NOT load-time-enforced)" so the README is internally consistent.
- **Files modified:** data/citations.README.md
- **Verification:** README reads coherently; the corrected paragraph + the relabeled header now agree.
- **Committed in:** 7f501a4 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 documentation-accuracy fix)
**Impact on plan:** Trivial documentation consistency fix fully within the plan's "correct the existing README" instruction. No scope creep; no code change; no behavioral impact.

## Issues Encountered

None. All Task 1 + Task 2 verifications passed on the first run (sources.json loads with 5 pending records; citations.json loads with 5 pending claims; loader loads the extended registry cleanly; gate exits 1 with [MISSING] on the fixture's placeholder claims — exactly as the plan predicted; TCA-RNG-CITRATE-PROCHIRALITY-01 present; NUBASE2020-C14 + C14-TIME-01 absent; fixtures unchanged). The 13 citation unit tests (loader + gate exit codes) still pass — no regression (data + docs only; no code touched).

## User Setup Required

None - no external service configuration required. (This plan creates the registry structure + populates pending entries; no source was approved — that is Plan 05's job. No schema code was written — the loader already handles the extended fields.)

## Next Phase Readiness

**Ready for Plan 05-05 (human first-batch approval checkpoint) + content phases (7-9).** The SC#4 registry structure is in place and SC#5 enforcement is proven on real extended data.

### Flag for Plan 05 — the exact list of entries the human needs to review + approve (the first batch)

**5 sources to approve (batch — the source-level approval that routine claims inherit):**
1. `LIBRETEXTS-METAB-GLYCOLYSIS` — LibreTexts Biological Chemistry / Metabolism / Glycolysis (CC BY-NC-SA 4.0; hub verified live 2026-08-15; confirm exact glycolysis subpage URL)
2. `LIBRETEXTS-METAB-TCA` — LibreTexts Biological Chemistry / Metabolism / Pyruvate Dehydrogenase + Citric Acid Cycle (CC BY-NC-SA 4.0; hub verified; confirm subpage URLs)
3. `LEHNINGER-CH-CITRIC_ACID_CYCLE` — Lehninger Principles of Biochemistry (Nelson & Cox), Citric Acid Cycle chapter (CANDIDATE — confirm edition + exact chapter number; no ISBN asserted)
4. `PDB-4PFK` — RCSB PDB 4PFK (phosphofructokinase, G. stearothermophilus, 2.40 Å; verified at rcsb.org 2026-08-15; Evans/Farrants/Hudson 1981)
5. `PDB-1CSC` — RCSB PDB 1CSC (citrate synthase, Gallus gallus, 1.70 Å; verified at rcsb.org 2026-08-15; Karpusas/Holland/Remington 1991)

**5 claims to approve (high-stakes individually; routine via source inheritance + leisure spot-check):**

| claim_id | review_tier | inherits_source_approval | source_id | approval sequence |
|----------|-------------|--------------------------|-----------|-------------------|
| `TCA-RNG-CITRATE-PROCHIRALITY-01` | high-stakes | false | LEHNINGER-CH-CITRIC_ACID_CYCLE | Approve INDIVIDUALLY (grounds the TCA shuffle MECHANISM) |
| `TCA-RNG-WEIGHT-01` | high-stakes | false | LEHNINGER-CH-CITRIC_ACID_CYCLE | Approve INDIVIDUALLY (game-design 0.5/0.5 RNG weight VALUE — human chooses exact weights for pedagogy) |
| `GLY-PFK-01` | routine | true | LIBRETEXTS-METAB-GLYCOLYSIS | Source-inherited (fast-track once the source is approved); spot-check at leisure (warning flag) |
| `CAST-PFK-PDB-01` | routine | true | PDB-4PFK | Source-inherited; spot-check at leisure (warning flag) |
| `CAST-CSC-PDB-01` | routine | true | PDB-1CSC | Source-inherited; spot-check at leisure (warning flag) |

**Recommended Plan 05 approval order:** (1) approve the 5 SOURCES first (batch); (2) approve the 2 HIGH-STAKES claims individually (TCA-RNG-CITRATE-PROCHIRALITY-01, TCA-RNG-WEIGHT-01); (3) spot-check the 3 ROUTINE claims at leisure (GLY-PFK-01, CAST-PFK-PDB-01, CAST-CSC-PDB-01 — these auto-approve via the source's approval but are FLAGGED with `review_tier=routine` + `inherits_source_approval=true` for the human to filter + review when they have time). Also confirm the direct `[UNAPPROVED]`-on-pending-seed-claim proof (Plan 05 Task 2 step 5 mirrors a seed claim_id into a temp fixture). Do NOT create/approve NUBASE2020-C14 or C14-TIME-01 (DROPPED in Plan 05-01).

**Blockers/concerns:** None. The Phase 1 gate is backward-compatible (verified: loader ignores extended fields; gate loads the extended registry + exits 1; the 13 citation unit tests pass — no regression). All entries are pending; no source or claim was auto-approved. The anaerobic/ATP-soul-jump/C14-decay sources are NOT in this batch (they're candidate sources for Phase 7/9 — keeps this plan within context budget and matches SC#4's stated scope).

---
*Phase: 05-pre-content-key-decisions-source-approval*
*Completed: 2026-08-15*
