---
phase: 01-foundations-testability-citation-gate
plan: 01
subsystem: infra
tags: [python36, ast, import-gate, testability, pymol-plugin, gitignore, unittest]

# Dependency graph
requires: []
provides:
  - "c14/ package skeleton with 3-tier dirs (domain root, pymol_layer/, ui/, data/)"
  - "AST import-boundary gate (tools/check_imports.py) -- exits 0 clean / 1 on violations"
  - "tests/test_imports.py -- 4-test suite (banned-import detection, no false positives, gate-on-skeleton, py_compile sweep)"
  - "Fixed .gitignore (3rd_party_lib/ ignored, __pycache__/ ignored, dead lines removed)"
  - "Canonical Phase 1 check command: python3.6 tools/check_imports.py && python3.6 -m unittest discover -s tests -v"
affects: [01-02, 01-03, phase-2, phase-3, phase-6, all-domain-modules]

# Tech tracking
tech-stack:
  added: []  # stdlib only -- ast, os, sys, py_compile, unittest, subprocess, tempfile
  patterns:
    - "AST-based import-boundary gate (stdlib ast + os.walk, 3.6-compatible)"
    - "Directory location = tier marker (pymol_layer/ + ui/ gate-excluded)"
    - "__file__-relative ROOT resolution so the gate runs regardless of CWD"
    - "Strict-ban policy: any pymol/PyQt5 Import/ImportFrom in domain tier fails, including TYPE_CHECKING guards"
    - "py_compile + unittest pairing (Pitfall 3: py_compile necessary but not sufficient)"

key-files:
  created:
    - c14/__init__.py
    - c14/pymol_layer/__init__.py
    - c14/ui/__init__.py
    - c14/data/.gitkeep
    - tools/check_imports.py
    - tests/__init__.py
    - tests/test_imports.py
  modified:
    - .gitignore

key-decisions:
  - "AST gate over grep: 0 false positives on comments/strings, catches aliased `import pymol.cmd as c` (research 01-RESEARCH-testability.md)"
  - "Strict-ban policy: flag any pymol/PyQt5 Import/ImportFrom node including inside `if TYPE_CHECKING:` guards -- MolAction-as-pure-data means domain never names a pymol type"
  - "Directory location = tier: c14/ root scanned; pymol_layer/ + ui/ excluded. controller.py will live in c14/ui/ (Phase 6) so the two-dir exclusion is airtight"
  - "c14/__init__.py stays pure-Python in Phase 1; __init_plugin__ deferred to Phase 6 (lazy-delegate to c14/ui/plugin_entry.py)"
  - "Python 3.6 stdlib only: unittest (not pytest -- not installed); subprocess PIPE (not capture_output -- 3.7+)"

patterns-established:
  - "3-tier testability layering: c14/ domain (gate-scanned) -> c14/pymol_layer/ (excluded, may import pymol) -> c14/ui/ (excluded, may import pymol+PyQt5)"
  - "Canonical check command: python3.6 tools/check_imports.py && python3.6 -m unittest discover -s tests -v"
  - "Gate strict-ban: any pymol/PyQt5 Import/ImportFrom in domain tier = fail, no TYPE_CHECKING exceptions"
  - "__file__-relative ROOT resolution (gate finds c14/ regardless of CWD)"

# Metrics
duration: 32min
completed: 2026-08-13
---

# Phase 1 Plan 01: Package Skeleton + AST Testability Gate Summary

**c14/ 3-tier package skeleton with AST-based import-boundary gate enforcing pure-Python testability on Python 3.6 (stdlib only)**

## Performance

- **Duration:** 32 min
- **Started:** 2026-08-13T02:32:56Z
- **Completed:** 2026-08-13T03:05:09Z
- **Tasks:** 2
- **Files modified:** 8 (7 created, 1 modified)

## Accomplishments
- `c14/` package created with 3-tier directory structure (domain root + `pymol_layer/` + `ui/` + `data/`); `import c14` succeeds in WSL on Python 3.6.9 with zero pymol/PyQt5 dependency and prints `0.0.1-dev`
- AST-based import gate (`tools/check_imports.py`) catches all 7 banned static import forms (incl. aliased `import pymol.cmd as c` and `from PyQt5 import QtWidgets as W`), produces 0 false positives on comments/string literals, exempts `pymol_layer/` + `ui/`, flags dynamic imports for review, and exits 0 clean / 1 on violations
- 4-test unittest suite (`tests/test_imports.py`) proving banned-import detection, no false positives, gate-passes-on-clean-skeleton, and a py_compile sweep of all domain `.py` files
- `.gitignore` fixed: broken `./3rd_party_lib/**` -> `3rd_party_lib/` (now ignored), `__pycache__/` added, dead `./Pymol-script-repo/**` line removed
- Canonical Phase 1 check command verified green: `python3.6 tools/check_imports.py && python3.6 -m unittest discover -s tests -v` (exit 0, 4 tests pass)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create c14/ package skeleton + fix .gitignore** - `d5a6e63` (feat)
2. **Task 2: Create AST import gate + tests** - `5a784c0` (feat)

**Plan metadata:** `pending` (docs: complete plan -- committed after this summary)

## Files Created/Modified
- `c14/__init__.py` - Pure-Python package marker; `__version__ = "0.0.1-dev"`; zero pymol/PyQt5 imports (boundary linchpin)
- `c14/pymol_layer/__init__.py` - Gate-excluded subpackage marker (may import pymol; docstring only)
- `c14/ui/__init__.py` - Gate-excluded subpackage marker (may import pymol/PyQt5; docstring only)
- `c14/data/.gitkeep` - Bundled-data directory placeholder (Plan 02 adds selfcheck.json)
- `tools/check_imports.py` - AST import-boundary gate; walks c14/ pruning {pymol_layer, ui, __pycache__}; exports `main` + `violations_in`
- `tests/__init__.py` - Package marker (required for `unittest discover -s tests` on Python 3.6)
- `tests/test_imports.py` - 4 unittest methods (banned-import catch, no false positives, gate-on-skeleton, py_compile sweep)
- `.gitignore` - Fixed `3rd_party_lib/` + added `__pycache__/` + removed dead `./Pymol-script-repo/**`

## Decisions Made
- **AST gate over grep:** Per research (01-RESEARCH-testability.md), AST produces 0 false positives on comments/strings and catches aliased submodule imports that anchored grep cannot reliably distinguish. Adopted the verified reference design near-verbatim.
- **Strict-ban policy (incl. TYPE_CHECKING):** Per research Open Question 1, the gate flags ANY pymol/PyQt5 Import/ImportFrom node including inside `if TYPE_CHECKING:` guards. The MolAction-as-pure-data architecture means the domain tier never needs to name a pymol type, so a strict ban keeps the boundary airtight and the gate trivial.
- **Directory location = tier:** `c14/` root is gate-scanned; `pymol_layer/` + `ui/` are excluded. This makes the two-dir exclusion set complete (the controller, which imports Qt+pymol, will live in `c14/ui/` in Phase 6).
- **c14/__init__.py stays pure-Python in Phase 1:** `__init_plugin__` deferred to Phase 6 per citations-research Investigation Point 5. When it arrives, it must lazy-delegate to `c14/ui/plugin_entry.py` (Pattern 1).
- **Python 3.6 stdlib only:** unittest (pytest not installed, confirmed); subprocess uses `stdout/stderr=PIPE` not `capture_output` (3.7+).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed subprocess `capture_output` (Python 3.7+) for 3.6 compatibility**
- **Found during:** Task 2 (verification of test suite)
- **Issue:** `test_gate_passes_on_clean_skeleton` used `subprocess.run(..., capture_output=True)`, but `capture_output` was added in Python 3.7. On 3.6.9 it raises `TypeError: __init__() got an unexpected keyword argument 'capture_output'`. The plan mandates Python 3.6 syntax/API only.
- **Fix:** Replaced `capture_output=True` with `stdout=subprocess.PIPE, stderr=subprocess.PIPE` (the 3.6-compatible equivalent), with an inline comment noting the version constraint.
- **Files modified:** tests/test_imports.py
- **Verification:** Re-ran `python3.6 -m unittest discover -s tests -v` -- all 4 tests pass (exit 0).
- **Committed in:** `5a784c0` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minimal -- a 3.6-compatibility fix to the test harness, caught and resolved during verification. No scope creep. The gate itself (adopted near-verbatim from the empirically-verified research reference design) worked first try.

## Issues Encountered
None beyond the `capture_output` fix above. The gate, skeleton, and `.gitignore` fix all worked as designed on first execution.

## User Setup Required
None - no external service configuration required. Everything is stdlib, already present in the Python 3.6.9 WSL env. No installs needed (AGENTS.md constraint honored).

## Next Phase Readiness
- **Ready for Wave 2 (Plans 02 + 03):** The `c14/` package skeleton and gate are in place. Plan 02 (`c14/paths.py` + README DOC-04) and Plan 03 (`c14/citations.py` + `tools/check_citations.py` + fixtures + tests) can build directly on this skeleton. Any domain module they add will be automatically gate-enforced (must stay pymol/PyQt5-free) and py_compile-checked by the test suite.
- **Ready for Phase 2+:** The testability boundary is now architecturally enforced -- no later phase can break WSL testability by sneaking a `pymol` import into the domain tier without the gate catching it.
- **Blockers/concerns:** None. The `c14/data/` directory (bundled runtime assets, ships in plugin zip) is distinct from the repo-root `data/` directory that Plan 03 creates for `data/citations.json` (content/registry source file) -- the plan explicitly notes this distinction to avoid future confusion.

---
*Phase: 01-foundations-testability-citation-gate*
*Completed: 2026-08-13*
