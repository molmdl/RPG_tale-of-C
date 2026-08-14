---
phase: 04-editing-protonation-restore-safety-net
plan: 04
subsystem: testing
tags: [ast-gate, alter-gate, coverage-scan, pdb-fixtures, sc1, sc5, enforcement]

# Dependency graph
requires:
  - phase: 04-01
    provides: "c14/pymol_layer/edit_ops.py -- the SOLE allowlisted cmd.alter path (the gate's allowlist target)"
provides:
  - "tools/check_alter_gate.py -- AST gate enforcing *.alter(...) Attribute calls only in edit_ops.py (SC1 machine-checkable)"
  - "tools/check_edit_coverage.py -- per-enzyme min-coverage scan reading cast.json + edits.json (SC5 data-driven)"
  - "tests/test_check_alter_gate.py -- 6-test self-test proving the gate FAILS on a violation + passes on the real repo"
  - "c14/data/cast.json + c14/data/edits.json -- PLACEHOLDER manifests (fixture_enzyme_1; real cast/edits are Phase 5+/9)"
  - "c14/data/assets/bundled/_edit_smoke.pdb -- 2-residue ALA-GLY peptide fixture (SC1+SC2 smoke, 04-05)"
  - "c14/data/assets/bundled/_his_smoke.pdb -- HIS with explicit HD1+HE2 fixture (SC4 protonation smoke, 04-05)"
affects: [04-05 (headless smokes load the fixtures), Phase 9 (real cast replaces placeholder cast.json)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AST-precise gate on ast.Call.func ast.Attribute attr=='alter' (catches cmd.alter/self._cmd.alter/pymol.cmd.alter uniformly; no false positives on strings/comments/dict-values)"
    - "Data-driven coverage scan (reads cast.json + edits.json at runtime; add enzyme -> FAILS until edits.json has an entry)"
    - "Testable-core extraction (find_violations(roots, allowlist) -> main(); mirrors check_citations.py:run_gate)"
    - "Hand-written PDB fixtures (deterministic, no network, no cmd.fab dependency; valid enough for load+alter+byres+count)"

key-files:
  created:
    - "tools/check_alter_gate.py"
    - "tools/check_edit_coverage.py"
    - "tests/test_check_alter_gate.py"
    - "c14/data/cast.json"
    - "c14/data/edits.json"
    - "c14/data/assets/bundled/_edit_smoke.pdb"
    - "c14/data/assets/bundled/_his_smoke.pdb"
  modified: []

key-decisions:
  - "AST over grep for the alter gate: AST on Attribute(attr=='alter') is precise -- catches cmd.alter/self._cmd.alter/pymol.cmd.alter uniformly and does NOT false-positive on 'alter' in comments/strings/dict-values (c14/protonation_catalog.py has {\"mode\":\"alter\"} as ast.Str, correctly ignored). A grep on .alter( would false-positive on those."
  - "Hand-written PDB fixtures over cmd.fab: deterministic, no network, no fragment-library dependency. cmd.fab uses one-letter codes (HIS would be 3 residues H+I+S); hand-writing gives full control over atom names (esp. HD1/HE2 needed for the SC4 protonation smoke). Geometry is approximate but valid enough for PyMOL load+alter+byres+count."
  - "find_violations(roots, allowlist) extracted as testable core so the exit-1 path is unit-testable in a temp dir without subprocess (mirrors check_citations.py:run_gate). main() is a thin caller with hardcoded SCAN_ROOTS + ALLOWLIST."
  - "check_edit_coverage.py does its own inline JSON loading (no c14.edit_router import) -- keeps 04-04's depends_on:['04-01'] honest (needs only edit_ops.py + the two JSON files, not the 04-02 router module). Matches check_citations.py does-its-own-loading precedent."
  - "The alter gate scans c14/ + tools/ INCLUDING pymol_layer/ + ui/ (unlike check_imports.py which SKIP_DIRS them) -- the alter gate must see every .py in the repo; only edit_ops.py is allowlisted."

patterns-established:
  - "AST-precise enforcement gate: use ast.Call + ast.Attribute attr matching for API-call invariants that grep cannot reliably check (false positives on string literals). Extends the check_imports.py AST precedent."
  - "Data-driven manifest coverage scan: read cast + edits at runtime so the gate stays green as the cast grows and FAILS when coverage lapses (forces discipline without per-entry hardcoding)."
  - "Three-way exit codes (0=pass / 1=violation / 2=ERROR) for enforcement gates -- distinguishes 'broken tooling/fixtures' (exit 2) from 'genuine violation' (exit 1), matching the check_citations.py convention."

# Metrics
duration: 3h 9m
completed: 2026-08-14
---

# Phase 4 Plan 04: Alter Gate + Coverage Scan + Smoke Fixtures Summary

**AST gate making SC1 ("no bare cmd.alter outside apply_edit") a machine-checkable invariant, a data-driven per-enzyme coverage scan (SC5), and two committed headless-smoke PDB fixtures (ALA-GLY + HIS-with-HD1/HE2) ready for 04-05**

## Performance

- **Duration:** 3h 9m (wall-clock incl. context loading + headless PyMOL invocations)
- **Started:** 2026-08-14T19:24:59Z
- **Completed:** 2026-08-14T22:34:44Z
- **Tasks:** 2
- **Files modified:** 7 (all new)

## Accomplishments
- **SC1 is now machine-checkable, not just unit-tested.** `tools/check_alter_gate.py` is an AST gate that walks every `.py` under `c14/` (including `pymol_layer/` + `ui/`) and `tools/`, flagging any `*.alter(...)` Attribute CALL outside the allowlist `{c14/pymol_layer/edit_ops.py}`. AST on `Attribute(attr=="alter")` catches `cmd.alter`/`self._cmd.alter`/`pymol.cmd.alter` uniformly and does NOT false-positive on `"alter"` in comments, docstrings, or dict-values (`c14/protonation_catalog.py`'s `{"mode":"alter"}` is an `ast.Str`, correctly ignored). Exit 0=clean / 1=violation / 2=ERROR (SyntaxError). Gate is GREEN on the current repo (the only `.alter(` call is `edit_ops.py:129` inside `apply_edit`).
- **SC5 is a data-driven coverage scan.** `tools/check_edit_coverage.py` reads `c14/data/cast.json` + `c14/data/edits.json` at runtime; every cast enzyme must have >=1 edits.json entry. Add an enzyme to cast.json -> scan FAILS until edits.json has an entry (forces coverage discipline). GREEN on the placeholder cast (fixture_enzyme_1 has 1 edit). Exit 0/1/2. Does its own inline JSON loading (no c14.edit_router import) so 04-04 stays independent of 04-02.
- **6-test self-test proves the gate's exit-1 path.** `tests/test_check_alter_gate.py` tests: (a) all 3 alter Attribute forms caught, (b) no false positives on strings/comments, (c) allowlisted alter in edit_ops.py NOT flagged, (d) stray alter in molops.py FLAGGED, (e) SyntaxError -> errors (exit 2) not violations, (f) real repo exits 0.
- **Two committed PDB fixtures ready for 04-05's headless smokes.** `_edit_smoke.pdb` (ALA-GLY, 17 atoms, 2 residues) for SC1+SC2 (resn swap + byres + restore round-trip). `_his_smoke.pdb` (HIS with explicit HD1+HE2, 14 atoms) for SC4 (protonation remove/add). Both verified headlessly (load + count_atoms > 0 + expected residues/H atoms; SMOKE_RESULT: PASS).
- **Placeholder manifests establish the schema.** `cast.json` (enzymes list with id/label/fixture/claim_id) + `edits.json` (per-enzyme edits dict with signature/branch_node/claim_id + global bad_ending_pool). Phase 9 replaces placeholders with the real ~20+ cast; Phase 5+ adds real per-enzyme known-edit entries with real claim_ids.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create alter gate + coverage scan + alter gate tests** - `66c6eae` (feat)
2. **Task 2: Create placeholder manifests + smoke fixtures** - `0e5efb8` (feat)

**Plan metadata:** (pending final commit)

## Files Created/Modified
- `tools/check_alter_gate.py` - AST gate enforcing *.alter(...) only in edit_ops.py (SC1); ALLOWLIST + find_violations() testable core; exit 0/1/2
- `tools/check_edit_coverage.py` - per-enzyme min-coverage scan reading cast.json + edits.json (SC5); inline JSON loading; exit 0/1/2
- `tests/test_check_alter_gate.py` - 6-test self-test (3 alter forms caught, no false positives, allowlist honored, stray flagged, SyntaxError->errors, real repo exit 0)
- `c14/data/cast.json` - PLACEHOLDER cast manifest (1 demo enzyme: fixture_enzyme_1)
- `c14/data/edits.json` - PLACEHOLDER edits manifest (1 demo edit entry + global bad_ending_pool)
- `c14/data/assets/bundled/_edit_smoke.pdb` - 2-residue ALA-GLY peptide (17 atoms) for SC1+SC2 smoke
- `c14/data/assets/bundled/_his_smoke.pdb` - HIS with HD1+HE2 (14 atoms) for SC4 protonation smoke

## Decisions Made
- **AST over grep for the alter gate.** The plan offered grep as a "lighter" alternative, but AST was chosen (and recommended by the plan) because `c14/protonation_catalog.py` contains `{"mode": "alter"}` as a dict-value string — a grep on `.alter(` would false-positive on it (it's a string literal, not a call). AST on `ast.Call.func ast.Attribute attr=="alter"` correctly ignores string literals, comments, and docstrings. Verified by `test_alter_calls_in_ignores_strings_and_comments`.
- **Hand-written PDB fixtures over `cmd.fab`.** The plan recommended `cmd.fab("AG","pep")` + `cmd.fab("HIS","his")` with a hand-write fallback. `cmd.fab` uses one-letter amino-acid codes, so "HIS" would build 3 residues (H=His, I=Ile, S=Ser) — not the single HIS residue needed. More importantly, the SC4 smoke requires explicit HD1 + HE2 atoms, whose presence after `cmd.h_add` is protonation-state-dependent and not guaranteed. Hand-writing the PDB ATOM records gives full deterministic control over atom names + counts. Geometry is approximate (valid enough for PyMOL load + alter resn + byres + count) — the fixtures are mechanics-test structures, not real catalytic-residue extracts.
- **`find_violations(roots, allowlist)` extracted as testable core.** The plan's self-test requirement (prove the gate FAILS on a violation) needed the exit-1 path testable in isolation. Rather than subprocess + a temp repo (fragile), the scan loop was extracted into `find_violations(roots, allowlist)` returning `(violations, errors)`, mirroring the `check_citations.py:run_gate` testable-core pattern. `main()` is a thin caller. Tests monkey-patch `REPO_ROOT` to a temp dir so rel-path computation matches.
- **`check_edit_coverage.py` does inline JSON loading (no `c14.edit_router` import).** The plan specified this to keep 04-04's `depends_on: ["04-01"]` honest — the scan needs only the two JSON files (Task 2) + edit_ops.py (04-01, the allowlist target), NOT the 04-02 router module. Matches the `check_citations.py` does-its-own-loading precedent.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- **SyntaxError message differs on Python 3.6.** The alter gate test initially asserted the error string contains "SyntaxError", but on Python 3.6 `SyntaxError.msg` is "invalid syntax" (the exception type name isn't in `e.msg`). Fixed the assertion to check for the filename ("broken.py") instead — the reliable marker. This is a test-only fix, not a gate-logic change.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- **04-05 (molops delegation + headless smokes) is unblocked.** The two committed fixtures (`_edit_smoke.pdb` + `_his_smoke.pdb`) are validated headlessly and ready for 04-05's SC1+SC2+SC4 smokes. The alter gate + coverage scan are GREEN and ready to run as part of 04-05's verification (and every future CI run).
- **SC1 is now a hard invariant.** Any future plan that introduces a `cmd.alter` outside `edit_ops.py` will fail the gate (exit 1) — including 04-05's molops delegation (must route edits through `EditOps.apply_edit`, not call `cmd.alter` directly).
- **SC5 stays green as the cast grows.** Phase 9's real cast (~20+ enzymes) will require a matching `edits.json` entry per enzyme — the scan enforces this automatically.
- **Phase 4 boundary respected.** The manifests use PLACEHOLDER enzyme ids + `PLACEHOLDER_PHASE5` claim_ids. Real cast (CAST-01, real PDB IDs + citations) is Phase 9; real per-enzyme edits with real claim_ids are Phase 5+. The fixtures are NOT real catalytic-residue extracts (no claim_id) — they are minimal mechanics-test structures.
- **No blockers.** Phase 4 is now 4/5 complete (04-01, 04-02, 04-03, 04-04 done; 04-05 is the integration + headless-smoke finale).

---
*Phase: 04-editing-protonation-restore-safety-net*
*Completed: 2026-08-14*
