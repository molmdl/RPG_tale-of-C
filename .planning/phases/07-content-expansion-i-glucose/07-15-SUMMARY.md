---
phase: 07-content-expansion-i-glucose
plan: 15
subsystem: cast-assets
tags: [cast-json, bulk-download, pdb-pipeline, edits-coverage, claim-traceability, rcsb, offline-prepopulation]

# Dependency graph
requires:
  - phase: 07-content-expansion-i-glucose (07-14)
    provides: "the 12 edits.json enzyme buckets (the cast roster target set; subset invariant cast-ids ⊆ edits-keys)"
  - phase: 07-content-expansion-i-glucose (07-05 registry landing)
    provides: "the approved CAST-* claims with pdb_id fields + the DIS-* claims whose review_notes bind 6WCV/5UPP/5LDW/1ZOY/1BGY/1OCC"
  - phase: 07-content-expansion-i-glucose (07-02/07-03/07-04 approval batches)
    provides: "D6→1ACO, D3→5GRE, D8→4WLU recorded outcomes + batch-B SUCLG1/FH cast records + batch-C Decision 1 ETC PDB set"
provides:
  - "Final rpg/data/cast.json: 12 real enzyme entries (id/label/source/pdb_id/character/claim_id), fixture + PLACEHOLDER gone — the bulk-download list pre-fetches every entry on fresh installs"
  - "check_edit_coverage exit 0 (was exit 1 on the 2 placeholders since plan 14) — the §4.5 coverage invariant is GREEN"
  - "Verified download split for fresh installs: 7 to-fetch (5GRE, 6WCV, 5UPP, 4WLU, 5LDW, 1ZOY, 1BGY) / 5 dev-cached (1ACO, 1OCC, 4PFK, 6CFO, 7FS3); downloaded/ cache untouched in git"
  - "Hermetic real-cast bulk-list test pinning the exact 12-id set + PLACEHOLDER-guard regression test"
affects: [plan 16 (durable cast/edits invariants — the claim_id CAST-gap below), plan 17 (human-verify the bulk-download prompt + reveals), plan 18 (final gates), 07-13 (owns the tca.json TBD_ACONITASE→1ACO + 5GRF→5GRE load swaps)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "cast.json claim_id = the approved registry claim binding that pdb_id: CAST-* claim where one exists; otherwise the approved DIS-* claim whose review_notes bind the pdb (never a fabricated id)"
    - "Hermetic real-manifest test pattern: real cast.json via explicit cast_path + monkeypatched data_path temp root, so the gitignored dev cache can never influence the assertion"

key-files:
  created: []
  modified:
    - "rpg/data/cast.json (7 lines → 17 lines; 2 placeholders → 12 real entries)"
    - "tests/test_bulk_download.py (placeholder premise → hermetic real-cast pin + guard regression)"

key-decisions:
  - "Cast = EXACTLY the 12 edits.json buckets (per plan Resolution + orchestrator): tca.citrate_synthase (1CSC) and etc.atp_synthase (1E79) stay OUT — 1CSC loads via tca.json on_enter (loads need no cast membership); 1E79 is a teaching beat only (07-09 kept [hide_all], never a load). LDH 5W8J also out (anaer.ldh is not edit-allowed → no edits bucket)."
  - "NO 2VGG, NO 6CER, NO 1ZP0 cast entries (clarification #2): 2VGG bound text-only (07-08 dormant-mutant precedent), 6CER approved-but-dormant (07-02 DC-5a), 1ZP0 source still PENDING (07-11 declined the load)."
  - "pdb_id per recorded outcomes: gly.pfk→4PFK, gly.pyruvate_kinase→7FS3, pyr.pdh→6CFO, tca.aconitase→1ACO (D6), tca.isocitrate_dh→5GRE (D3), tca.succinyl_coa_synthetase→6WCV (DIS-SUCLG1-01-cand review_notes: 'Human SUCLG1 cast record = PDB 6WCV'), tca.fumarase→5UPP (DIS-FH-01-cand review_notes: 'Human FH cast record = PDB 5UPP'), tca.malate_dh→4WLU (D8), etc.complex_i→5LDW, complex_ii→1ZOY, complex_iii→1BGY, complex_iv→1OCC (batch-C Decision 1 approved set)."
  - "claim_id binding: 6 enzymes have a real CAST-* claim (CAST-PFK-PDB-01, CAST-PKLR-PDB-01, CAST-PDH-WT-PDB-01-cand, CAST-ACO2-PDB-01-cand, CAST-IDH3-PDB-01-cand, CAST-MDH2-PDB-01-cand — all approved); the other 6 (6WCV/5UPP/5LDW/1ZOY/1BGY/1OCC) have NO CAST-* claim in the registry, so claim_id points at the approved DIS-* claim that binds that pdb_id in its review_notes — no claim id invented (per orchestrator rule); the CAST-gap is flagged for plan 16/17 below."
  - "Labels are machine-clean human-readable enzyme names only (clarification #6) — bovine/porcine/human species honesty stays in story text (already authored by 07-06/08/09)."

patterns-established:
  - "cast.json claim_id dual convention: CAST-* slot where the registry has one, DIS-* review-notes binding where it does not (both resolvable to an APPROVED registry claim; verified for all 12)"

# Metrics
duration: 11 min
completed: 2026-09-03
---

# Phase 7 Plan 15: Cast + assets (real enzyme entries) Summary

**cast.json rewritten to the 12 real mutable enzymes (fixture + PLACEHOLDER gone) with recorded-outcome pdb_ids and approved-claim claim_ids; the edit-coverage gate flipped to exit 0; the bulk-download list verified metadata-only — 7 PDBs to pre-fetch on fresh installs, 5 already dev-cached, cache never staged.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-03T03:42:13Z
- **Completed:** 2026-09-03T03:53:28Z
- **Tasks:** 2 of 2 (Task 2 verification-only — no file changes, no commit; same precedent as 07-14 Task 2)
- **Files modified:** 2 (rpg/data/cast.json, tests/test_bulk_download.py)

## Accomplishments

- **The cast is the real story roster.** 12 entries, one per edits.json bucket, in pathway order (gly → pyr → tca → etc): `gly.pfk`/4PFK, `gly.pyruvate_kinase`/7FS3, `pyr.pdh`/6CFO, `tca.aconitase`/1ACO (D6 — the TBD_ACONITASE resolution recorded here), `tca.isocitrate_dh`/5GRE (D3), `tca.succinyl_coa_synthetase`/6WCV, `tca.fumarase`/5UPP, `tca.malate_dh`/4WLU (D8), `etc.complex_i`/5LDW, `etc.complex_ii`/1ZOY, `etc.complex_iii`/1BGY, `etc.complex_iv`/1OCC. All `source:"download"`, all `character:"glucose"`. `fixture_enzyme_1` + `PLACEHOLDER_large_enzyme` are GONE (M3 disposal complete).
- **Coverage invariant GREEN for the first time this phase.** `tools/check_edit_coverage.py` exits 0 — 12/12 enzymes covered (it had been exit 1 on exactly the 2 placeholders since plan 14, as forecast). Verified `cast-ids ⊆ edits-keys` with ZERO edits-only keys at execution time (the recorded 12-key state; the 13th bucket `tca.akg_dh` had not landed from 07-13 by run end — subset holds either way).
- **The bulk-download list is real and pre-fetchable.** `missing_large_pdbs()` returns 12 entries, every `pdb_id` a real 4-char RCSB id (no PLACEHOLDER). Fresh-install split (dev cache is gitignored, per-user): **to-fetch = 5GRE, 6WCV, 5UPP, 4WLU, 5LDW, 1ZOY, 1BGY (7)**; **already in the dev cache = 1ACO, 1OCC, 4PFK, 6CFO, 7FS3 (5)** (1crn/5grf/cid_2244.sdf also cached but irrelevant: 1crn is the Phase-5 fixture, 5grf is the REJECTED idh3 cast replaced by 5GRE). `expected_download_characters()` = {glucose}.
- **No fabricated science, verified mechanically:** every cast `claim_id` resolves to an APPROVED `data/citations.json` claim, and for the 6 DIS-bound entries the pdb_id appears verbatim inside the claim record (machine-checked). The bulk-download VERIFICATION was metadata-only per the plan — zero network fetches performed; the cache pre-population is a runtime concern (list above).
- **Suite green:** 326 tests OK (325 + 1 net: the replaced placeholder test became two — a real-cast pin and a guard regression). check_imports + check_alter_gate clean. Cache untouched: `git status rpg/data/assets/` empty; `git check-ignore` confirms downloaded/ stays gitignored.

## THE CAST TABLE (verified against the registry at execution time)

| # | enzyme_id | pdb_id | claim_id (approved) | binding basis | resolution (registry) |
|---|-----------|--------|---------------------|---------------|----------------------|
| 1 | gly.pfk | 4PFK | CAST-PFK-PDB-01 | CAST claim pdb_id field | 2.4 Å |
| 2 | gly.pyruvate_kinase | 7FS3 | CAST-PKLR-PDB-01 | CAST claim pdb_id field | 1.66 Å |
| 3 | pyr.pdh | 6CFO | CAST-PDH-WT-PDB-01-cand | CAST claim pdb_id field | 2.7 Å |
| 4 | tca.aconitase | 1ACO | CAST-ACO2-PDB-01-cand | CAST claim pdb_id field (D6) | 2.05 Å |
| 5 | tca.isocitrate_dh | 5GRE | CAST-IDH3-PDB-01-cand | CAST claim pdb_id field (D3) | 2.65 Å |
| 6 | tca.succinyl_coa_synthetase | 6WCV | DIS-SUCLG1-01-cand | review_notes: "Human SUCLG1 cast record = PDB 6WCV" | 1.52 Å (source record) |
| 7 | tca.fumarase | 5UPP | DIS-FH-01-cand | review_notes: "Human FH cast record = PDB 5UPP (1.8 A)" | 1.8 Å (source record) |
| 8 | tca.malate_dh | 4WLU | CAST-MDH2-PDB-01-cand | CAST claim pdb_id field (D8) | 2.14 Å |
| 9 | etc.complex_i | 5LDW | DIS-NDUFS8-01-cand | review_notes: "PDB 5LDW chain I resi 68" + batch-C Decision 1 | 4.27 Å cryo-EM (source record) |
| 10 | etc.complex_ii | 1ZOY | DIS-SDHA-01-cand | review_notes: "PDB 1ZOY chain A resi 512" + batch-C Decision 1 | 2.4 Å (source record) |
| 11 | etc.complex_iii | 1BGY | DIS-CYC1-01-cand | review_notes: "PDB 1BGY chain D resi 131" + batch-C Decision 1 | 3.0 Å (source record) |
| 12 | etc.complex_iv | 1OCC | DIS-COX4I1-01-cand | review_notes: "PDB 1OCC chain D resi 130" + batch-C Decision 1 | 2.8 Å (source record) |

**Excluded BY DESIGN (documented per orchestrator clarifications #1–#2):** `tca.citrate_synthase` (1CSC — loads via tca.json on_enter; loads do not require cast membership; would VIOLATE the subset invariant since CS has no edits entry) · `etc.atp_synthase` (1E79 — teaching beat only, 07-09 kept [hide_all], never promoted to a load) · 2VGG (bound text-only via CAST-PKLR-MUTANT-PDB-01, 07-08 dormant precedent) · 6CER (approved-but-DORMANT, 07-02 DC-5a) · 1ZP0 (source PENDING, 07-11 declined the load) · 5W8J/LDH (anaer.ldh is not edit-allowed → not an edits bucket → outside the exactly-12 rule).

## Task Commits

1. **Task 1: Fill cast.json with real entries** — `76e2aa2` (feat; includes the blocking test update — see Deviations)
2. **Task 2: Verify bulk-download list + coverage** — verification-only (no file changes; nothing to commit). Evidence: coverage exit 0 (12/12 COVERED); download list = 12 real ids / 7 to-fetch / 5 cached; cache gitignored + untracked.

## Files Created/Modified

- `rpg/data/cast.json` — 12 real enzyme entries; fixture + PLACEHOLDER removed (the plan's sole data artifact)
- `tests/test_bulk_download.py` — `TestMissingLargePdbsPlaceholder` (real-cast → `[]` premise, dead the moment the cast filled) replaced by `TestRealCastBulkList` (hermetic: real cast via explicit cast_path + monkeypatched temp data_path; pins the exact 12-id bulk list, 4-char alnum hygiene, object_name==enzyme_id, character=glucose) + `test_missing_large_pdbs_skips_placeholder_pdb_id` (Phase-6 guard contract kept as a temp-cast regression test)

## Decisions Made

- **Cast = exactly the 12 edits.json buckets** (plan Resolution sentence + orchestrator clarification #1, authoritative over the plan context's broader candidate list which mentioned 5W8J/1CSC). Consequence documented below: 1CSC and 5W8J story loads are NOT bulk-prefetched.
- **complex_i's 5LDW cast membership: IN** (documented call, per clarification #4). Batch-C Decision 1 approved 5LDW as-is in the ETC PDB set, and STATE.md names 07-17 the "template-fill owner for any 5LDW/1E79 display" — so the cryo-EM note structure may yet be shown. 5LDW (~large, 4.27 Å) will pre-fetch even though complex_i keeps [hide_all] in story today; cast membership is a separate question from story loads (recorded as such).
- **6WCV/5UPP pdb_ids are recorded outcomes, not inventions** (clarification #4's resolution path): the plan flagged "no approved cast PDB was recorded for SUCLG1 — check the registry". Registry check found the batch-B verdicts landed in the DIS claims' review_notes ("Human SUCLG1 cast record = PDB 6WCV", "Human FH cast record = PDB 5UPP") + approved `PDB-6WCV`/`PDB-5UPP` source records. The 07-03 §D9 outcome ("SUCLG1/FH cast record, routine tier") is thereby honored with zero new science.
- **claim_id dual convention** (see the CAST-gap flag below): CAST-* where the registry has one; otherwise the approved DIS-* claim binding that pdb_id. Nothing invented; all 12 resolve to approved claims (machine-verified).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Rewrote the Phase-6 placeholder premise test in tests/test_bulk_download.py**

- **Found during:** Task 1 (pre-commit verification run)
- **Issue:** `TestMissingLargePdbsPlaceholder.test_missing_large_pdbs_skips_placeholder` called `missing_large_pdbs(None)` against the REAL bundled cast and asserted `[]` + empty lock set — true only while the cast held `PLACEHOLDER_large_enzyme`. With the real cast, 7 of 12 PDBs are absent from the gitignored dev cache → the call returns 7 entries → the test fails, breaking the plan's own "suite green" success criterion.
- **Fix:** Replaced with `TestRealCastBulkList` — hermetic (real cast.json via explicit `cast_path`, `rpg.paths.data_path` monkeypatched to a temp root so the environment-dependent dev cache can never influence the result) and STRONGER: pins the exact 12-id bulk set, 4-char alnum non-PLACEHOLDER hygiene per id, `object_name == enzyme_id`, `character == "glucose"`, `expected_download_characters == {"glucose"`. Kept the Phase-6 guard contract alive as a dedicated temp-cast regression test (`test_missing_large_pdbs_skips_placeholder_pdb_id`) since the real cast no longer exercises the PLACEHOLDER guard path. Same-plan test updates are the phase precedent (07-06, 07-12).
- **Files modified:** tests/test_bulk_download.py
- **Verification:** `python3.6 -m unittest tests.test_bulk_download` → 12 OK; full suite 326 OK
- **Committed in:** 76e2aa2 (Task 1 commit — cast + test together so every commit is green)

---

**Total deviations:** 1 auto-fixed (1 blocking test update). No scope creep; no engine files, story JSONs, edits.json, or registry files touched.

## Issues Encountered

- **CAST-* claim gap for 6 cast PDBs (FLAGGED for plan 16/17 — the plan's forecast confirmed):** no `CAST-*` claim exists in `data/citations.json` for 6WCV, 5UPP, 5LDW, 1ZOY, 1BGY, 1OCC (research §5.4's "every load-bearing PDB needs a CAST-* claim" was fully applied only to the batch-A/B CAST claims). The structures ARE approved — via `PDB-*` source records (all approved) + the DIS-* claims' review_notes — and cast.json's claim_id points there, so traceability holds. **Owed decision for plan 16/17:** either (a) land six `CAST-<NAME>-PDB-01` claims (routine tier, pdb_id/resolution fields, matching the CAST-PFK-PDB-01 precedent) and re-point the six cast claim_ids, or (b) ratify the DIS-binding convention as-is. No claim was invented here per the orchestrator's explicit rule.
- **tca.json transient inconsistency (07-13's scope, in flight — NOT touched by this plan):** at execution time tca.json still carries `pdb:TBD_ACONITASE` (tca.aconitase on_enter) and `pdb:5GRF` (tca.isocitrate_dh on_enter) while cast.json now records 1ACO/5GRE. 07-13 (TCA content, running in parallel) owns both load swaps per 07-03's downstream obligations ("Plan 13: 5GRE swap; 1ACO cast"); 07-12's note assigning the source-node swap to plan 15 conflicts with this plan's file scope (`files_modified: [rpg/data/cast.json]` + Task 1's "Do NOT touch story JSONs") — recorded here so the orchestrator can confirm 07-13 lands them. Until then, first-run on a fresh install would attempt a `TBD_ACONITASE`/`5GRF` fetch at those nodes; the bulk list itself is correct.
- **1CSC + 5W8J story loads are not bulk-prefetched (by-design consequence of the exactly-12 rule):** both load via on_enter `pdb:` targets (tca.citrate_synthase, anaer.ldh) → on fresh installs they network-fetch lazily at first node entry rather than in the pre-play prompt. Harmless when online (cmd.fetch + local-cache reuse); if offline-first coverage of these two is ever wanted, that is a recorded roster decision for a later plan (would require adding non-edit-allowed entries to cast.json, which the current check_edit_coverage contract would reject — tool change needed).
- **Stale docstrings (cosmetic, untouched):** rpg/ui/bulk_download.py module docstring (lines 66-70) and tools/check_edit_coverage.py header still narrate the Phase-6 placeholder cast; tools/controller_integration_smoke.py:926 comment likewise. Engine files were off-limits per Task 1; behavior is unaffected. Plan 16/17 may sweep the comments.
- **Watch item for 07-17/18 human-verify:** `missing_large_pdbs` sets `object_name = enzyme_id` (e.g. `tca.aconitase` — contains a dot). The runner + this naming are pre-existing Phase-6 code (never exercised with real data — the placeholder guard kept the prompt silent). Whether `cmd.fetch(code, "tca.aconitase")` accepts/sanitizes a dotted object name in the real Windows PyMOL session must be confirmed when the prompt first fires; engine file → not fixable in this plan.

## Verification (reproduced)

```
python3.6 -c subset probe (plan Task 1 verify)        → subset-ok 12 (cast 12 ⊆ edits 12; edits-only keys: [])
registry cross-check (throwaway python3.6 -c)         → all 12 claim_ids resolve to APPROVED citations.json claims;
                                                        the 6 DIS bindings each contain their pdb_id verbatim; all
                                                        pdb_ids 4-char alnum non-PLACEHOLDER; source=download; char=glucose
python3.6 tools/check_edit_coverage.py                → EDIT COVERAGE PASSED: 12 enzyme(s) covered — exit 0
missing_large_pdbs(None) + expected_download_characters → 12 entries; FETCH 5GRE/6WCV/5UPP/4WLU/5LDW/1ZOY/1BGY (7);
                                                        cached 1ACO/1OCC/4PFK/6CFO/7FS3 (5); lock-universe {glucose}
git check-ignore rpg/data/assets/downloaded/1aco.pdb  → rc 0 (gitignored); git status rpg/data/assets/ → empty
python3.6 -m py_compile tests/test_bulk_download.py   → OK
python3.6 -m unittest discover -s tests               → Ran 326 tests — OK
python3.6 tools/check_imports.py                      → clean
python3.6 tools/check_alter_gate.py                   → clean
```

No network fetches were performed (metadata-only verification per the plan/AGENTS.md); the 7-file pre-population list above is the runtime concern it documents.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Plan 16 (durable tests):** cast-side invariants are now testable the way 07-14's were — suggest adding `validate`-style durable checks: cast-ids ⊆ edits-keys (will become == when 07-13's 13th bucket + its cast decision land — see below), every cast pdb_id 4-char alnum (already pinned hermetically in test_bulk_download), and the CAST-gap decision (option (a) land six CAST-* claims / option (b) ratify DIS-binding) executed + pinned.
- **07-13 coordination (in flight):** when it adds the `tca.akg_dh` edits bucket, the shared-manifest question resurfaces: an OGDH cast entry needs an approved cast PDB — none was recorded (tca.akg_dh is narrative-only; DIS-OGDH-01-cand binds no structure). If 07-13 adds the bucket WITHOUT a cast entry, the roster becomes subset-form (13 edits keys ⊇ 12 cast ids) and stays tool-green; if equality is wanted, the human must first approve an OGDH cast structure. This plan's subset invariant holds either way.
- **Plan 17 (human-verify):** first play on a fresh install now fires the bulk-download prompt with 7 files — verify the prompt + per-file progress + the dotted-object-name fetch behavior (watch item above); also confirm the tca.json load swaps landed (TBD_ACONITASE/5GRF must be gone).
- **Plan 18 (final gates):** coverage gate is now permanently in the green set (exit 0); citation-gate residual unchanged by this plan (cast.json is not gate-scanned; observed in-flight tca residue belongs to 07-13).

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-03*
