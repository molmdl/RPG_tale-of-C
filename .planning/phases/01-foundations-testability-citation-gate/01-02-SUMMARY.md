---
phase: 01-foundations-testability-citation-gate
plan: 02
subsystem: infra
tags: [pathlib, unittest, package-data, cwd-independence, python36, bundled-data]

# Dependency graph
requires:
  - phase: 01-01
    provides: c14/ package skeleton with pymol/PyQt5-free c14/__init__.py (so `from c14.paths import ...` runs cleanly in WSL), tests/__init__.py (so `unittest discover -s tests` works), and the AST import gate (tools/check_imports.py) that this plan's paths.py must pass
provides:
  - "c14.paths.data_path(*parts) -> pathlib.Path: pure __file__-relative resolver for all bundled-data lookups"
  - "c14.paths.selfcheck() -> str: existence-checked fixture resolver; raises FileNotFoundError on broken layout (Pitfall 1 'fail loud on plugin load' mitigation)"
  - "c14/data/selfcheck.json: 1-line bundled fixture that ships inside the PyMOL Plugin Manager zip"
  - "tests/test_paths.py: 3 unittest methods including the real-os.chdir(tempdir) CWD-independence proof"
  - "Verification (not modification) that README.md satisfies DOC-04 (Under Development banner + description + TBD: Installation/References/Cast)"
affects: [all-phases-bundling-data, phase-06-plugin-loader, phase-09-cast, phase-11-docs]

# Tech tracking
tech-stack:
  added: []  # stdlib only — pathlib, os, tempfile, shutil, unittest (all 3.6.9 verified)
  patterns:
    - "__file__-relative package-data resolution (Pitfall 1 mitigation): _PACKAGE_ROOT = Path(__file__).resolve().parent"
    - "Pure resolver vs existence-checked selfcheck separation (data_path computes; selfcheck verifies)"
    - "CWD-independence proof via real os.chdir(tempfile.mkdtemp()) in setUp/tearDown — honest end-to-end, better than mock.patch('os.getcwd')"
    - "Bundled data lives inside c14/data/ (ships in zip); repo-root data/ is for source/registry files only (Plan 03)"

key-files:
  created:
    - c14/paths.py
    - c14/data/selfcheck.json
    - tests/test_paths.py
  modified: []  # README.md was verified but NOT modified (DOC-04 already satisfied)

key-decisions:
  - "Adopted pathlib.Path return type for data_path() (cleaner than os.path; str(path) coerces for PyMOL cmd.* string-path APIs)"
  - "data_path() is a pure resolver (NO existence check) — separation of concerns; callers handle FileNotFoundError naturally; supports 'compute where a future file would go' use cases"
  - "selfcheck() DOES check existence and raises FileNotFoundError — it is the fail-loud layout invariant for plugin load (Pitfall 1 mitigation, Phase 6+ caller)"
  - "CWD-independence proven via real os.chdir(tempfile.mkdtemp()) in setUp — honest end-to-end proof, not mock.patch of os.getcwd (mock only proves the call site, not the behavior)"
  - "README.md treated as verification-only (DOC-04 already satisfied per 01-RESEARCH-paths.md reading the 57-line file in full) — no content changes; respects CITE-01 gate and later-phase content ownership"

patterns-established:
  - "Pattern: __file__-relative bundled-data resolution via c14.paths.data_path() — every later phase MUST use this for any c14/data/* lookup (enforced by convention + the CWD-independence test)"
  - "Pattern: CWD-independence test via real os.chdir(tempdir) in setUp/tearDown — the canonical proof for any path-resolving helper"
  - "Pattern: bundled data lives inside c14/data/ (ships in PyMOL Plugin Manager zip); repo-root data/ is for source/registry files only (Plan 03 owns data/citations.json)"
  - "Pattern: read-only verification tasks produce no commit when the verified artifact already satisfies the criterion (Task 2: README DOC-04)"

# Metrics
duration: 4 min
completed: 2026-08-13
---

# Phase 1 Plan 02: Bundled-Data Path Resolution + CWD-Independence Test Summary

**c14.paths data_path()/selfcheck() with __file__-relative resolution, proven CWD-independent by a real os.chdir(tempdir) unittest; README.md verified (not modified) as DOC-04-compliant**

## Performance

- **Duration:** 4 min
- **Started:** 2026-08-13T03:50:39Z
- **Completed:** 2026-08-13T03:54:30Z
- **Tasks:** 2
- **Files modified:** 3 created, 0 modified (README verified read-only)

## Accomplishments
- Created `c14/paths.py` exposing `data_path(*parts) -> pathlib.Path` (pure `__file__`-relative resolver) and `selfcheck() -> str` (existence-checked, raises FileNotFoundError on broken layout) — the single convention every later phase inherits for bundled-data lookups (Pitfall 1 mitigation baked in on day one)
- Created `c14/data/selfcheck.json` (1-line fixture) inside the package so it ships in the PyMOL Plugin Manager zip — distinct from Plan 03's repo-root `data/citations.json` (a source/registry file, not a bundled runtime asset)
- Created `tests/test_paths.py` with 3 unittest methods; the setUp physically `os.chdir`s into a `tempfile.mkdtemp` foreign dir for every test, so existence-of-the-fixture-from-a-foreign-CWD *is* the CWD-independence proof (a real chdir is the honest end-to-end proof; mock.patch of os.getcwd would only prove the call site)
- Verified (not modified) that the existing 57-line `README.md` satisfies DOC-04 in full: Under Development banner (line 6), project description (lines 10-21), TBD: Installation Instructions (lines 33-36), TBD: References (lines 43-47), TBD: Cast (lines 49-52); internal links `.planning/ROADMAP.md`, `spec.md`, `LICENSE`, `LICENSE_pymol-open-source` all resolve
- AST gate (`tools/check_imports.py`) still exits 0 — paths.py is import-clean; full suite is now 19 tests (4 test_imports + 12 test_citations from parallel Plan 03 + 3 test_paths), all pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create c14/paths.py + c14/data/selfcheck.json + tests/test_paths.py** - `d6d3177` (feat)
2. **Task 2: Verify README.md satisfies DOC-04 (read-only verification, no content changes)** - *no commit* (read-only verification; README.md unchanged, `git diff` empty — DOC-04 was already satisfied per 01-RESEARCH-paths.md, and the plan explicitly instructed "Do NOT edit README.md")

**Plan metadata:** `pending` (docs: complete plan — created after this section)

## Files Created/Modified
- `c14/paths.py` — path-resolution helper: `data_path(*parts) -> Path` (pure `__file__`-relative resolver) + `selfcheck() -> str` (existence-checked, fail-loud). Pure-Python, no pymol/PyQt5 — import-clean per AST gate.
- `c14/data/selfcheck.json` — 1-line bundled fixture `{"purpose": "c14 path-resolution self-check fixture -- do not delete"}`. Ships inside the plugin zip (inside `c14/`, not at repo root).
- `tests/test_paths.py` — 3 unittest methods (`test_selfcheck_resolves_from_arbitrary_cwd`, `test_data_path_returns_absolute_path`, `test_data_path_does_not_raise_for_nonexistent_file`); setUp/tearDown do real `os.chdir(tempfile.mkdtemp(...))` so every test runs from a foreign CWD.
- `README.md` — *read and verified, NOT modified*; satisfies DOC-04 (banner + description + TBD: Installation/References/Cast); `git diff` empty.

## Decisions Made
- **pathlib.Path return type for data_path()** — cleaner than `os.path` string surgery; `str(path)` coerces for PyMOL `cmd.*` string-path APIs (e.g. `cmd.load(str(data_path(...)))`). The `os.path.dirname(__file__)` form (PITFALLS.md's literal wording) is equally valid; pathlib is the modern equivalent and is type-friendlier.
- **data_path() is a pure resolver (NO existence check)** — separation of concerns; callers open files and handle `FileNotFoundError` naturally; a resolver that raises couples path arithmetic to filesystem state and breaks "compute where a future file would go" use cases (e.g. `data_path("data", "future", "file.json")`).
- **selfcheck() DOES check existence and raises FileNotFoundError** — the "self-check" is explicitly about confirming the layout works; existence is its whole point. Designed so a later phase (Phase 6+ plugin loader) can call `c14.paths.selfcheck()` at plugin load to "fail loud" (Pitfall 1 mitigation).
- **CWD-independence proven via real `os.chdir(tempfile.mkdtemp())`** — a real chdir is the honest end-to-end proof that resolution is `__file__`-relative (not cwd-relative or some other cwd-derived trick); `mock.patch('os.getcwd')` would only prove the helper doesn't call `getcwd`, not that it doesn't use some other cwd-relative trick.
- **README.md treated as verification-only (no content changes)** — 01-RESEARCH-paths.md already read the 57-line file in full and confirmed every DOC-04 sub-requirement present; the plan explicitly instructed "Do NOT edit README.md" and "Do NOT add real scientific citations, real cast data, or any real content" (gated by CITE-01 and later phases). Verification confirmed: banner, description, TBD: Installation/References/Cast all present; internal links resolve. No edits needed.
- **Python 3.6 stdlib only** — pathlib, os, tempfile, shutil, unittest all verified available on 3.6.9. Deliberately excluded `importlib.resources` (3.7+, confirmed unavailable) and `pkg_resources` (setuptools). `__file__`-relative resolution is the dependency-free fallback and is sufficient for a single-package plugin.

## Deviations from Plan

None — plan executed exactly as written. Both tasks followed the prescriptive reference designs from 01-RESEARCH-paths.md near-verbatim, and the README verification confirmed (as the research predicted) that DOC-04 was already satisfied with no edits needed.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. Pure-Python stdlib only; no installs, no env vars, no config files.

## Next Phase Readiness
- **Ready for Plan 03 (Wave 2 parallel) to merge its citation-gate work** — both Wave 2 plans touch disjoint files (this plan: c14/paths.py, c14/data/selfcheck.json, tests/test_paths.py, README.md; Plan 03: c14/citations.py, data/citations.json, data/citations.README.md, tools/check_citations.py, tests/fixtures/*, tests/test_citations.py). The 19-test suite (4 + 12 + 3) already passes with both plans' work in the working tree.
- **Ready for Phase 2 (Story Domain)** — `data_path()` is the convention all future bundled-data lookups (story JSON, etc.) must use; the CWD-independence test pattern is established for any new path-resolving helper.
- **Flag for Phase 6 (Plugin Loader)** — `c14.paths.selfcheck()` is designed to be called at plugin load to "fail loud" if the bundled layout is broken (Pitfall 1 mitigation). The Phase 1 *test* is the first caller; the plugin-loader phase is the second.
- **No blockers.** The path-resolution convention + CWD-independence proof + DOC-04 verification together satisfy Phase 1 success criteria #3 and #4.

---
*Phase: 01-foundations-testability-citation-gate*
*Completed: 2026-08-13*
