---
phase: 01-foundations-testability-citation-gate
plan: 03
subsystem: infra
tags: [python36, citation-gate, json-registry, pre-ship-gate, no-fabricated-science, unittest, subprocess, stdlib-only, object_pairs_hook]

# Dependency graph
requires:
  - phase: 01-01
    provides: "c14/ package skeleton (importable in WSL) + AST import-boundary gate (tools/check_imports.py) that scans c14/ and enforces no pymol/PyQt5 imports in the domain tier"
provides:
  - "CitationRegistry loader (c14/citations.py) -- plain class, Python 3.6 stdlib only, with load() (dup-key + status validation), is_approved(), status(), contains(), claim_ids(), __len__"
  - "Pre-ship citation gate (tools/check_citations.py) -- argparse --story + --registry, three-way exit codes (0=pass / 1=missing-or-unapproved / 2=config-error)"
  - "Real registry stub (data/citations.json = {}) + schema docs (data/citations.README.md) -- path convention baked in early; populated Phase 5+ (CITE-01)"
  - "6 fixture files (tests/fixtures/) demonstrating pass + pending-fail + missing-fail + rejected-fail + malformed-error -- all clearly placeholder, no real science"
  - "Test suite (tests/test_citations.py) -- 12 tests: 7 unit (registry load/validate) + 5 subprocess (gate exit codes)"
affects: [phase-2, phase-5, phase-9, phase-10, phase-11, all-story-content, citation-gate-ci]

# Tech tracking
tech-stack:
  added: []  # stdlib only -- json, argparse, os, sys, unittest, subprocess, tempfile
  patterns:
    - "JSON-object registry keyed by join key (claim_id -> record) for O(1) lookup + structural dup-key prevention"
    - "Three-way exit codes for CI gates (0=pass / 1=content-fail / 2=config-error) -- CI distinguishes broken fixtures from unapproved content"
    - "object_pairs_hook duplicate-key detection (raises ValueError on duplicate claim_id -- Pitfall 3, verified on 3.6.9)"
    - "Forward-compatible fixture format (same node shape as real Phase 2 story graph); story-walker isolated in one function for clean Phase 2 refactor"
    - "Strict-equality gate predicate: is_approved == 'approved' (NOT != 'pending' -- Pitfall 6: != 'pending' would let rejected claims pass)"
    - "Repo-root data/ (content source, not bundled) vs c14/data/ (bundled runtime asset) -- distinct directories with distinct roles"

key-files:
  created:
    - c14/citations.py
    - data/citations.json
    - data/citations.README.md
    - tools/check_citations.py
    - tests/fixtures/story_pass.json
    - tests/fixtures/citations_pass.json
    - tests/fixtures/citations_fail_pending.json
    - tests/fixtures/citations_fail_missing.json
    - tests/fixtures/citations_fail_rejected.json
    - tests/fixtures/citations_malformed.json
    - tests/test_citations.py
  modified: []

key-decisions:
  - "Gate predicate is approval_status == 'approved' (strict equality), NOT != 'pending' -- research Pitfall 6: != 'pending' would erroneously pass a 'rejected' claim. A rejected claim fails identically to a pending one (no special case)."
  - "Keep all three approval_status values {pending, approved, rejected} in the enum -- rejected records provenance (why a claim was refused) rather than silently deleting. Phase 1 success criterion (mentions only pending/approved) is fully satisfied by the == 'approved' test."
  - "object_pairs_hook duplicate-key detection included in CitationRegistry.load (~6 lines, HIGH value once two authors edit the registry) -- without it, json.load silently last-wins, clobbering an approval/rejection. Verified on 3.6.9."
  - "Three-way exit codes (0/1/2) over two-way (0/1) -- lets CI distinguish 'broken fixtures/tooling' (exit 2) from 'genuinely unapproved science' (exit 1). Phase 1 success criterion only requires non-zero on fail; the split is a clean-to-have the plan adopted."
  - "data/citations.json lives at REPO ROOT data/ (content source file, read at pre-ship time by the gate), NOT c14/data/ (bundled runtime asset that ships in the plugin zip). Distinct directories with distinct roles -- established early to avoid future confusion."
  - "Plain class (not @dataclass) for CitationRegistry -- @dataclasses is Python 3.7+ and ModuleNotFoundError on python3.6.9 (research Pitfall 1, verified). Plain class on a dict is 3.6-safe."
  - "Story-walker (collect_referenced_claim_ids) isolated in one function in tools/check_citations.py -- Phase 2 swaps it for c14.story.validate.collect_claim_ids('data/story/') with zero changes to the gate's core logic."
  - "Registry shipped as JSON object (data/citations.json), NOT JSONL (data/claims.jsonl) -- research Pitfall 2: O(1) lookup, structural dup-key prevention, matches authoritative ARCHITECTURE.md. The .jsonl references in earlier research are superseded."

patterns-established:
  - "Citation registry = JSON object keyed by claim_id (dict.get for O(1) is_approved); loader validates enum + detects dup keys at load time"
  - "Pre-ship gate contract: three-way exit (0/1/2) + human-readable report ([MISSING] / [UNAPPROVED] ... status is 'X') + fix-hint line"
  - "All fixture data clearly placeholder: claim text prefixed 'PLACEHOLDER:', source_type 'placeholder', source 'TBD', claim_ids 'placeholder-claim-N' -- no real science in fixtures"
  - "Forward-compatible story node shape: {nodes: {id: {claim_ids: [...]}}} -- gate reads only nodes + claim_ids; Phase 2 real graph reuses the contract"
  - "Repo-root data/ (content source, pre-ship) distinct from c14/data/ (bundled runtime, in-plugin-zip)"

# Metrics
duration: 20min
completed: 2026-08-13
---

# Phase 1 Plan 03: Citation Registry + No-Fabricated-Science Gate Summary

**CitationRegistry loader (c14/citations.py) + three-way pre-ship gate (tools/check_citations.py) with 6 placeholder fixtures + 12-test suite, enforcing spec.md's no-fabricated-science rule architecturally on Python 3.6 stdlib**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-13T03:30:59Z
- **Completed:** 2026-08-13T03:50:37Z
- **Tasks:** 3
- **Files modified:** 11 (all created)

## Accomplishments
- `CitationRegistry` plain class (`c14/citations.py`, Python 3.6 stdlib only -- no `@dataclass`) with `load(path)` (object_pairs_hook dup-key detection + approval_status enum validation), `is_approved(claim_id)` (strict `== "approved"` -- NOT `!= "pending"`, Pitfall 6), `status()`, `contains()`, `claim_ids()`, `__len__`. Import-clean (AST gate stays green); py_compile OK.
- Pre-ship gate `tools/check_citations.py` with argparse `--story` + `--registry`, three-way exit codes (0=pass / 1=missing-or-unapproved / 2=config-load-error), human-readable report (`[MISSING]` / `[UNAPPROVED] ... status is 'X'` + fix-hint). Story-walker isolated in `collect_referenced_claim_ids()` for clean Phase 2 refactor.
- 6 fixture files in `tests/fixtures/` demonstrating all paths: pass (exit 0), pending-fail (exit 1), missing-fail (exit 1), rejected-fail (exit 1), malformed-error (exit 2). All clearly placeholder (`PLACEHOLDER:` prefix, `source_type: "placeholder"`, `source: "TBD"`, `placeholder-claim-N`) -- no real science.
- Real registry stub `data/citations.json` (`{}`) + full schema docs `data/citations.README.md` (field table, enums, example, dup-key note) -- path convention baked in early; populated Phase 5+ (CITE-01).
- 12-test suite `tests/test_citations.py`: 7 unit tests (load pass/pending/missing/rejected, bad status raises, malformed raises, duplicate keys raises) + 5 subprocess exit-code tests (pass=0, pending=1, missing=1, rejected=1, malformed=2). All 16 tests pass (12 new + 4 existing import tests).
- Canonical Phase 1 check verified green: `python3.6 tools/check_imports.py && python3.6 -m unittest discover -s tests -v` (exit 0, 16 tests).

## Task Commits

Each task was committed atomically:

1. **Task 1: Create c14/citations.py + data/citations.json stub + data/citations.README.md** - `4e7815c` (feat)
2. **Task 2: Create tools/check_citations.py + 6 fixture files** - `2ced135` (feat)
3. **Task 3: Create tests/test_citations.py (unit + subprocess exit-code tests)** - `4977771` (test)

**Plan metadata:** `pending` (docs: complete plan -- committed after this summary)

## Files Created/Modified
- `c14/citations.py` - CitationRegistry plain class (3.6 stdlib only); load() with dup-key detection + status validation; is_approved() uses == 'approved'; status/contains/claim_ids/__len__ for gate reporting. Gate-scanned (no pymol/PyQt5).
- `data/citations.json` - Real registry stub (`{}`) at repo root (content source, NOT bundled asset). Populated Phase 5+ (CITE-01).
- `data/citations.README.md` - Full schema docs: field table (12 fields), source_type + approval_status enums, per-source-type required fields, example entry, dup-key + unreferenced-claim notes.
- `tools/check_citations.py` - Pre-ship gate; argparse --story + --registry; collect_referenced_claim_ids() (isolated for Phase 2 refactor); run_gate() (registry load + is_approved cross-ref + report); main() (catches ValueError/OSError -> exit 2). sys.path insertion to import c14.citations from tools/.
- `tests/fixtures/story_pass.json` - 2-node fixture story (fixture.intro -> fixture.ending), each carrying one placeholder claim_id.
- `tests/fixtures/citations_pass.json` - Both claims approved -> exit 0.
- `tests/fixtures/citations_fail_pending.json` - claim-2 pending -> exit 1 [UNAPPROVED].
- `tests/fixtures/citations_fail_missing.json` - claim-2 absent -> exit 1 [MISSING].
- `tests/fixtures/citations_fail_rejected.json` - claim-2 rejected -> exit 1 [UNAPPROVED] (proves Pitfall 6: rejected != approved).
- `tests/fixtures/citations_malformed.json` - Invalid JSON (`{ this is not json`) -> exit 2 [ERROR].
- `tests/test_citations.py` - 12 tests: TestCitationRegistry (7 unit, direct import) + TestCheckCitationsExitCodes (5 subprocess, assert returncode + stdout/stderr).

## Decisions Made
- **`== "approved"` not `!= "pending"` (Pitfall 6):** The gate predicate is strict equality. `!= "pending"` would erroneously pass a `rejected` claim, shipping a refused claim. A rejected claim fails identically to a pending one (no special case). Verified by the rejected fixture (exit 1, status 'rejected').
- **Keep `rejected` in the approval_status enum:** Records provenance (why a claim was refused) via `notes` rather than silently deleting. Deleting a refused claim would make a future re-introduction look like a *new* claim and lose rejection history. The Phase 1 success criterion (names only pending/approved) is fully satisfied by the `== "approved"` test.
- **`object_pairs_hook` duplicate-key detection (Pitfall 3):** Included in `CitationRegistry.load` (~6 lines). Without it, `json.load` silently last-wins on duplicate `claim_id` keys, letting two authors clobber each other's approval/rejection. Verified raising on 3.6.9 via `test_load_duplicate_keys_raises`.
- **Three-way exit codes (0/1/2):** Adopted over two-way (0/1). Lets CI distinguish "broken fixtures/tooling" (exit 2 -- a config/load error a human must fix) from "genuinely unapproved science" (exit 1 -- a content author must approve or remove the claim). The Phase 1 success criterion only requires non-zero on fail; the split is a clean-to-have the plan adopted per research recommendation.
- **`data/citations.json` at repo root (not `c14/data/`):** Repo-root `data/` is a content source file read at pre-ship time by the gate; `c14/data/` (created in Plan 01) is a bundled runtime asset that ships in the plugin zip. Distinct directories with distinct roles -- established early to avoid future confusion.
- **Plain class (not `@dataclass`) (Pitfall 1):** `dataclasses` is Python 3.7+ and `ModuleNotFoundError` on `python3.6.9` (verified in research). `CitationRegistry` is a plain class wrapping a dict -- 3.6-safe.
- **JSON object (not JSONL) (Pitfall 2):** `data/citations.json` is a JSON object keyed by `claim_id`, NOT `data/claims.jsonl`. O(1) lookup, structural dup-key prevention, matches authoritative `ARCHITECTURE.md`. The `.jsonl` references in earlier research are superseded.
- **Story-walker isolated:** `collect_referenced_claim_ids()` is the single function Phase 2 swaps for `c14.story.validate.collect_claim_ids("data/story/")`. The gate's core logic (registry load + is_approved check + report + exit) is unchanged by that refactor.

## Deviations from Plan

None - plan executed exactly as written. All three tasks completed as specified, all verifications passed on first execution. The reference designs in `01-RESEARCH-citations.md` (which had already been verified on `python3.6.9`) were adopted near-verbatim, so no debugging was needed.

## Issues Encountered
None. The loader, gate, fixtures, and tests all worked on first execution. The Python 3.6 subprocess compatibility lesson from Plan 01-01 (`stdout/stderr=PIPE` + manual `.decode()`, NOT `capture_output=True`/`text=True` which are 3.7+) was applied proactively in `tests/test_citations.py` matching the verified pattern in `tests/test_imports.py` -- no repeat of that bug.

## User Setup Required
None - no external service configuration required. Everything is Python 3.6 stdlib, already present in the WSL env. No installs needed (AGENTS.md constraint honored).

## Next Phase Readiness
- **Ready for Phase 2 (STORY-01):** The gate's story-walker (`collect_referenced_claim_ids` in `tools/check_citations.py`) is isolated in one function and forward-compatible with the real story graph shape (`{nodes: {id: {claim_ids: [...]}}}`). Phase 2 refactors it into `c14.story.validate.collect_claim_ids("data/story/")` -- a one-function swap with zero changes to the gate's core logic or the registry schema.
- **Ready for Phase 5 (CITE-01):** The registry schema (`data/citations.README.md`) is documented and the loader validates it. Phase 5 populates `data/citations.json` with real claims; the approval workflow (pending -> approved/rejected) is already modeled by the enum + gate predicate. The `approved_by`/`approval_date`/`notes` fields support the per-claim human-approval checkpoint.
- **Ready for Phase 9 (DOC-01 cast list) + Phase 10 (pre-ship gate):** `tools/check_citations.py` IS the pre-ship citation gate (Phase 10 success criterion). The structured `source` block (`pdb_id`, `resolution_angstrom`, `pubchem_cid`) is ready for Phase 9's `tools/build_cast_list.py` to read programmatically.
- **Blockers/concerns:** None. The gate is architecturally enforced -- no story node can ship referencing a missing or unapproved claim. Real claims land in Phase 5+; until then `data/citations.json` stays an empty stub and the gate is demonstrated on `tests/fixtures/`.
- **Note on parallel execution:** This plan (01-03) ran in parallel with Plan 01-02 (paths + README). The two plans touched disjoint files (01-02: `c14/paths.py`, `c14/data/selfcheck.json`, `tests/test_paths.py`, `README.md`; 01-03: `c14/citations.py`, `data/`, `tools/check_citations.py`, `tests/fixtures/`, `tests/test_citations.py`). Both depend only on 01-01 (complete).

---
*Phase: 01-foundations-testability-citation-gate*
*Completed: 2026-08-13*
