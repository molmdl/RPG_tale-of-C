---
phase: 01-foundations-testability-citation-gate
verified: 2026-08-13T04:06:46Z
status: passed
score: 15/15 must-have truths verified
re_verification: No — initial verification
---

# Phase 1: Foundations — Testability, Citation Gate, Path Resolution — Verification Report

**Phase Goal:** The project's hardest invariants — the pure-Python/UI testability split, the no-fabricated-science citation gate, and WSL/Windows path resolution — are architecturally enforced and unit-tested before any feature code, so no later phase can ship unapproved science or break WSL testability.

**Verified:** 2026-08-13T04:06:46Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Must-haves are consolidated from the `must_haves:` frontmatter of all three PLAN files (01-01, 01-02, 01-03). Each was verified against the ACTUAL codebase on disk — SUMMARY claims were not trusted.

| # | Truth (from PLAN must_haves) | Status | Evidence |
|---|---|---|---|
| 1 | `import c14` succeeds in WSL (python3.6) with zero pymol/PyQt5 dependency | ✓ VERIFIED | `python3.6 -c "import c14; print(c14.__version__)"` → `0.0.1-dev`; `c14/__init__.py` is 9 lines, docstring + `__version__` only, no pymol/PyQt5 imports |
| 2 | `python3.6 tools/check_imports.py` exits 0 when c14/ domain tier is clean | ✓ VERIFIED | Ran: exit 0, stdout `check_imports: clean (no pymol/PyQt5 imports in c14/ domain tier)` |
| 3 | `python3.6 tools/check_imports.py` exits 1 when any scanned c14/ file (excl. pymol_layer/ui) imports pymol.*/PyQt5.* in any form (incl. aliased `import pymol.cmd as c`) | ✓ VERIFIED | Wrote `import pymol.cmd as c` to `c14/_tmp_violation_test.py`; gate exited 1 with `IMPORT BOUNDARY VIOLATIONS (1): _tmp_violation_test.py:1 import pymol.cmd`; temp file removed via `os.remove` |
| 4 | `c14/pymol_layer/` and `c14/ui/` are exempt from the gate | ✓ VERIFIED | Wrote `import pymol.cmd` + `from PyQt5 import QtWidgets` to `c14/pymol_layer/_tmp_exempt_test.py` AND `from pymol.Qt import QtWidgets` + `import PyQt5` to `c14/ui/_tmp_exempt_test.py`; gate exited 0 (`clean`); temp files removed. Gate logic: `SKIP_DIRS = {"pymol_layer", "ui", "__pycache__"}` pruned in-place via `dirnames[:]` in `os.walk` |
| 5 | `3rd_party_lib/` is git-ignored | ✓ VERIFIED | `git check-ignore -v 3rd_party_lib/foo/bar.txt` → exit 0, matched `.gitignore:13:3rd_party_lib/` |
| 6 | `c14.paths.data_path('data','selfcheck.json')` returns absolute pathlib.Path derived from `__file__`, NOT `os.getcwd()` | ✓ VERIFIED | `c14/paths.py` line 23: `_PACKAGE_ROOT = Path(__file__).resolve().parent`; line 43: `return _PACKAGE_ROOT.joinpath(*relative_parts)`. `selfcheck()` printed an absolute `/mnt/c/.../c14/data/selfcheck.json` path |
| 7 | `c14.paths.selfcheck()` resolves bundled fixture and returns absolute path string; raises FileNotFoundError if missing | ✓ VERIFIED | Code lines 56-64: builds fixture path, checks `.is_file()`, raises `FileNotFoundError` with message if missing, else `return str(fixture)`. Behavior confirmed: prints absolute path |
| 8 | `tests/test_paths.py` passes when run from an arbitrary working directory (CWD-independence is the proof) | ✓ VERIFIED | `setUp` does `tempfile.mkdtemp` + real `os.chdir(self._tmp)`; `tearDown` restores. All 3 test methods pass. Cross-verified: `cd /tmp && python3.6 -c "...from c14.paths import selfcheck; print(selfcheck())"` → printed absolute path from foreign CWD |
| 9 | `README.md` has 'Under Development' banner + project description + TBD placeholder sections (Installation, References, Cast) | ✓ VERIFIED | Ran the plan's DOC-04 verification script → `DOC-04 VERIFIED: README.md satisfies all sub-requirements`. README line 6 `> **⚠️ Under Development**`; lines 10-21 Description; lines 33-36 Installation TBD; lines 43-47 References TBD; lines 49-52 Cast TBD. `git diff README.md` empty (no content changes — verification task, as planned). Internal links (`.planning/ROADMAP.md`, `spec.md`, `LICENSE`, `LICENSE_pymol-open-source`) all exist |
| 10 | `CitationRegistry.load(path)` loads + validates; raises ValueError on malformed JSON, non-dict top-level, invalid approval_status, or duplicate claim_id keys | ✓ VERIFIED | `c14/citations.py` lines 80-98: `json.load(..., object_pairs_hook=_no_duplicate_keys)` (dup-key raise line 43), `isinstance(data, dict)` check (line 82), per-entry `isinstance(entry, dict)` (line 88), `status not in _VALID_STATUSES` (line 93). Tests `test_load_malformed_raises`, `test_load_bad_status_raises`, `test_load_duplicate_keys_raises` all pass |
| 11 | `CitationRegistry.is_approved(claim_id)` returns True iff exists AND approval_status == 'approved'; False for missing/pending/rejected | ✓ VERIFIED | `c14/citations.py` line 109: `return entry is not None and entry.get("approval_status") == self.APPROVED` (strict `== "approved"`, NOT `!= "pending"` — Pitfall 6 avoided). Tests `test_load_pending_registry`, `test_load_rejected_registry` assert `is_approved` is False for pending/rejected |
| 12 | `tools/check_citations.py --story X --registry Y` exits 0 when every referenced claim_id is approved | ✓ VERIFIED | Ran with `story_pass.json` + `citations_pass.json` → exit 0, stdout `CITATION GATE PASSED: 2 claim reference(s) across 2 node(s) -- all approved.` |
| 13 | `tools/check_citations.py` exits 1 when any story node references missing claim_id OR pending/rejected | ✓ VERIFIED | Three runs: pending → exit 1 (`[UNAPPROVED] ... status is 'pending'`); missing → exit 1 (`[MISSING] ... not in registry`); rejected → exit 1 (`[UNAPPROVED] ... status is 'rejected'`) |
| 14 | `tools/check_citations.py` exits 2 on config/load errors (malformed JSON, missing file, bad schema) | ✓ VERIFIED | Ran with `citations_malformed.json` (`{ this is not json`) → exit 2, stderr `CITATION GATE ERROR: Expecting property name enclosed in double quotes...` |
| 15 | All fixture data is clearly placeholder (claim text prefixed 'PLACEHOLDER:', source_type 'placeholder', source 'TBD', claim_ids 'placeholder-claim-N') | ✓ VERIFIED | Inspected all 6 fixtures: every `claim` starts with `PLACEHOLDER:`, every `source_type` is `"placeholder"`, every `source` is `"TBD"`, every `claim_id` is `placeholder-claim-N`. `citations_malformed.json` is intentionally invalid JSON (`{ this is not json`). No real science anywhere |

**Score:** 15/15 truths verified

### Required Artifacts

Every artifact from every PLAN's `must_haves.artifacts` checked at all three levels (exists → substantive → wired).

| Artifact | Expected | Exists | Substantive | Wired | Details |
|---|---|---|---|---|---|
| `c14/__init__.py` | Minimal pure-Python init, `__version__`, no pymol/PyQt5 | ✓ | ✓ (9 lines, has `__version__`) | ✓ (imported by `import c14`, by test_paths, by test_citations) | Boundary linchpin; no `__init_plugin__` (deferred to Phase 6 as planned) |
| `c14/pymol_layer/__init__.py` | Gate-excluded subpackage marker | ✓ | ✓ (docstring marker) | ✓ (gate `SKIP_DIRS` includes `pymol_layer`) | One-line docstring, no imports |
| `c14/ui/__init__.py` | Gate-excluded subpackage marker | ✓ | ✓ (docstring marker) | ✓ (gate `SKIP_DIRS` includes `ui`) | One-line docstring, no imports |
| `c14/data/.gitkeep` | Bundled-data dir placeholder | ✓ | ✓ (empty file, 0 bytes) | ✓ (dir tracked in git) | Ships in plugin zip |
| `tools/check_imports.py` | AST gate; exports `main`, `violations_in`; contains `ast` | ✓ | ✓ (100 lines) | ✓ (called by test_imports subprocess + py_compile sweep) | `violations_in` catches 7 banned forms + dynamic-import review; `SKIP_DIRS` pruning correct |
| `tests/test_imports.py` | Unit tests for gate + py_compile sweep; contains `unittest` | ✓ | ✓ (116 lines) | ✓ (imports `check_imports`; runs gate subprocess) | 4 tests: banned-imports, no-false-positives, gate-on-clean, py_compile-all-domain |
| `.gitignore` | `3rd_party_lib/` + `__pycache__/`; dead `./Pymol-script-repo/**` + broken `./3rd_party_lib/**` removed | ✓ | ✓ (15 lines, correct) | ✓ (git check-ignore confirms both patterns) | Line 1 `Pymol-script-repo`, line 5 `__pycache__/`, line 13 `3rd_party_lib/`; no `./`-prefixed variants |
| `c14/paths.py` | `data_path(*parts) -> Path` + `selfcheck() -> str`; contains `_PACKAGE_ROOT` | ✓ | ✓ (64 lines) | ✓ (imported by test_paths; `selfcheck()` callable from foreign CWD) | `_PACKAGE_ROOT = Path(__file__).resolve().parent`; pure resolver (no existence check); `selfcheck` raises FileNotFoundError |
| `c14/data/selfcheck.json` | Tiny JSON fixture; contains `purpose` | ✓ | ✓ (1 line, valid JSON) | ✓ (resolved by `selfcheck()`) | `{"purpose": "c14 path-resolution self-check fixture -- do not delete"}` |
| `tests/test_paths.py` | unittest CWD-independence proof; contains `unittest` | ✓ | ✓ (70 lines) | ✓ (`from c14.paths import data_path, selfcheck`; `os.chdir(self._tmp)` in setUp) | 3 tests; real `os.chdir` (not mock) |
| `README.md` | DOC-04: banner + description + TBD sections; contains 'Under Development' | ✓ | ✓ (57 lines) | ✓ (repo-root README, all internal links resolve) | Unchanged (verification task); `git diff` empty |
| `c14/citations.py` | `CitationRegistry` plain class; contains `class CitationRegistry` | ✓ | ✓ (131 lines) | ✓ (imported by check_citations.py + test_citations.py) | Plain class (NOT @dataclass — 3.6 incompatible); `load` with `object_pairs_hook` + status validation; `is_approved` uses `== "approved"` |
| `data/citations.json` | Empty stub `{}` at repo root | ✓ | ✓ (content `{}\n` exactly) | ✓ (loadable by `CitationRegistry.load`, len 0) | Repo-root content file (NOT bundled in plugin zip — distinct from `c14/data/`) |
| `data/citations.README.md` | Schema docs; contains `approval_status` | ✓ | ✓ (81 lines) | ✓ (documents the schema the loader enforces) | Field table, source_type enum, approval_status enum, example entry, dup-key note |
| `tools/check_citations.py` | Pre-ship gate; argparse `--story`/`--registry`; contains `from c14.citations import CitationRegistry` | ✓ | ✓ (150 lines) | ✓ (sys.path insert repo root; imports CitationRegistry; subprocess-tested) | `collect_referenced_claim_ids` isolated for Phase 2 refactor; exit 0/1/2 contract correct |
| `tests/fixtures/story_pass.json` | 2-node fixture story, placeholder claim_ids | ✓ | ✓ (14 lines) | ✓ (consumed by gate + subprocess tests) | `fixture.intro` → `fixture.ending`; forward-compatible node shape |
| `tests/fixtures/citations_pass.json` | Both claims approved → gate exit 0 | ✓ | ✓ (20 lines) | ✓ (used by test_pass) | Clearly placeholder |
| `tests/fixtures/citations_fail_pending.json` | claim-2 pending → gate exit 1 | ✓ | ✓ (18 lines) | ✓ (used by test_fail_pending) | Clearly placeholder |
| `tests/fixtures/citations_fail_missing.json` | claim-2 absent → gate exit 1 | ✓ | ✓ (11 lines) | ✓ (used by test_fail_missing) | Only claim-1 present |
| `tests/fixtures/citations_fail_rejected.json` | claim-2 rejected → gate exit 1 | ✓ | ✓ (18 lines) | ✓ (used by test_fail_rejected) | Proves rejected path (Pitfall 6) |
| `tests/fixtures/citations_malformed.json` | Invalid JSON → gate exit 2 | ✓ | ✓ (1 line) | ✓ (used by test_malformed) | `{ this is not json` |
| `tests/test_citations.py` | Unit + subprocess tests; contains `unittest` | ✓ | ✓ (181 lines) | ✓ (imports CitationRegistry; subprocess check_citations.py) | 12 tests: 7 unit + 5 subprocess exit-code |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `tools/check_imports.py` | `c14/` domain tier | `os.walk(ROOT)` pruning `{pymol_layer, ui, __pycache__}`; `ast.parse` each `.py` | WIRED | `ROOT` resolves to repo `c14/` from `__file__`; `SKIP_DIRS` prune verified empirically (exemption test) |
| `tests/test_imports.py` | `tools/check_imports.py` | `subprocess.run([sys.executable, GATE_SCRIPT])` + assert returncode | WIRED | `test_gate_passes_on_clean_skeleton` asserts exit 0 + "clean" in stdout |
| `tests/test_imports.py` | `c14/` domain modules | `py_compile.compile(full, doraise=True)` walk | WIRED | `test_py_compile_all_domain_modules` walks `c14/` pruning SKIP_DIRS, compiles each `.py` |
| `c14/paths.py` | `c14/__file__` | `Path(__file__).resolve().parent` → `_PACKAGE_ROOT` | WIRED | Verified: returns absolute path; works from foreign CWD (`/tmp`) |
| `tests/test_paths.py` | `c14.paths` | `from c14.paths import data_path, selfcheck` | WIRED | Imports succeed; all 3 tests pass |
| `tests/test_paths.py` | foreign working dir | `os.chdir(self._tmp)` in setUp | WIRED | Real `os.chdir` to `tempfile.mkdtemp` — honest end-to-end CWD-independence proof |
| `tools/check_citations.py` | `c14.citations.CitationRegistry` | `sys.path.insert(0, repo_root); from c14.citations import CitationRegistry` | WIRED | Script runs regardless of CWD; `CitationRegistry.load(registry_path)` called in `run_gate` |
| `tools/check_citations.py` | `tests/fixtures/*.json` | `collect_referenced_claim_ids(story_path)` walks `story['nodes'][*]['claim_ids']` | WIRED | Cross-references via `registry.contains` + `registry.is_approved`; isolated for Phase 2 refactor |
| `tests/test_citations.py` | `tools/check_citations.py` | `subprocess.run([sys.executable, GATE_SCRIPT, --story, --registry])` | WIRED | 5 subprocess tests assert exit 0/1/1/1/2 + stdout/stderr content |
| `tests/test_citations.py` | `c14.citations.CitationRegistry` | `from c14.citations import CitationRegistry` direct unit tests | WIRED | 7 unit tests cover load/is_approved/status/contains + 3 error paths |

### Phase 1 Success Criteria (from ROADMAP / verification prompt)

| # | Success Criterion | Status | Evidence |
|---|---|---|---|
| 1 | All pure-Python domain-tier modules pass `py_compile` and import cleanly in WSL with zero pymol/PyQt5 imports (CI AST gate scans `c14/` excluding `pymol_layer/` and `ui/`) | ✓ SATISFIED | `python3.6 -m py_compile` on all 5 domain files OK; AST gate exits 0 clean; `import c14` + `import c14.paths` + `import c14.citations` all succeed; gate exempts pymol_layer/ui (empirically verified) |
| 2 | `tools/check_citations.py` exits non-zero on missing/pending claim_id, zero when all approved (demonstrated with fixture story + citation data) | ✓ SATISFIED | Exit codes verified: pass=0, pending=1, missing=1, rejected=1, malformed=2 (5 fixture combinations) |
| 3 | Path-resolution self-check helper resolves bundled data via `__file__`-relative absolute paths, with a unit test confirming resolution from arbitrary working directory | ✓ SATISFIED | `selfcheck()` uses `Path(__file__).resolve().parent`; `test_paths.py` does real `os.chdir(tempdir)`; cross-verified from `/tmp` |
| 4 | Repo-root README.md with 'Under Development' banner, project description, TBD placeholder sections | ✓ SATISFIED | DOC-04 VERIFIED script passed; banner (line 6), Description (lines 10-21), Installation TBD (33-36), References TBD (43-47), Cast TBD (49-52) |

### Anti-Patterns Found

Scanned all 10 code files (`c14/*.py`, `c14/pymol_layer/__init__.py`, `c14/ui/__init__.py`, `tools/*.py`, `tests/test_*.py`) for `TODO|FIXME|XXX|HACK|not implemented|coming soon|will be here|lorem ipsum|return null|return undefined`.

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| (none) | — | — | — | No anti-patterns found in any code file |

Note: `PLACEHOLDER:` appears in fixture JSON files (intentional — the plan explicitly requires fixture data to be clearly placeholder to avoid fabricating science). This is correct behavior, not a stub.

### Boundary / Scope Checks

| Check | Expected | Status | Evidence |
|---|---|---|---|
| No `setup.py` / `pyproject.toml` / `conftest.py` / `pytest.ini` created | NOT present | ✓ | `ls` confirms none exist (Phase 1 ships via PyMOL Plugin Manager zip, not pip; tests use stdlib unittest) |
| No `data/claims.jsonl` created | NOT present | ✓ | `ls data/claims.jsonl` → No such file (JSONL superseded by JSON object — research Pitfall 2) |
| No `c14/story/model.py` created | NOT present | ✓ | `ls c14/story/model.py` → No such file (Phase 2 owns the Node dataclass) |
| Phase-1 files tracked in git | tracked | ✓ | `git ls-files` shows all 23 phase-1 files tracked; 8 commits in `git log` for phase 01 |
| `__pycache__/` git-ignored | ignored | ✓ | `git check-ignore -v c14/__pycache__/x.pyc` → exit 0, matches `.gitignore:5:__pycache__/` |
| Full test suite passes | 19 tests, exit 0 | ✓ | `python3.6 -m unittest discover -s tests -v` → `Ran 19 tests in 0.601s` → `OK` (4 import + 3 paths + 12 citations) |

### Human Verification Required

None. This is a pure-Python/WSL phase with no Qt/GUI components. All must-haves were verified programmatically by running the actual commands, reading the actual files, and checking actual behavior (gate exit codes, test results, CWD-independence, gitignore, fixture content). No item requires human verification.

### Gaps Summary

No gaps found. Every must-have truth (15/15) is verified against the actual codebase:

- **Testability split (Plan 01-01):** The AST gate is real and airtight — it catches aliased `import pymol.cmd as c` (exit 1) and correctly exempts `pymol_layer/` + `ui/` (exit 0 with pymol/PyQt5 imports inside those dirs). `.gitignore` is fixed (`3rd_party_lib/` + `__pycache__/` ignore; dead `./`-prefixed lines removed).
- **Path resolution (Plan 01-02):** `data_path()`/`selfcheck()` derive paths from `__file__`, proven CWD-independent by a real `os.chdir(tempdir)` in `setUp` and cross-verified from `/tmp`. README satisfies DOC-04 unchanged.
- **Citation gate (Plan 01-03):** The three-way exit contract (0/1/2) works exactly as specified across all 5 fixture combinations. `is_approved` uses strict `== "approved"` (Pitfall 6 avoided). Duplicate-key detection via `object_pairs_hook` is tested. All fixture data is clearly placeholder — no fabricated science.
- **Phase boundaries respected:** No `setup.py`/`pyproject.toml`/`conftest.py`/`pytest.ini`, no `data/claims.jsonl`, no `c14/story/model.py`.

The phase goal — architecturally enforcing the three hardest invariants before any feature code — is achieved. No later phase can ship unapproved science (the gate blocks it) or break WSL testability (the AST gate blocks pymol/PyQt5 in the domain tier).

---

_Verified: 2026-08-13T04:06:46Z_
_Verifier: OpenCode (gsd-verifier)_
