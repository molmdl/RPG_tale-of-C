# Phase 1: Foundations & Testability Boundary + Citation Gate — Research (Paths / Plumbing / README track)

**Researched:** 2026-08-13
**Domain:** Python package-data path resolution (PyMOL plugin), project plumbing, README compliance
**Confidence:** HIGH (overall) — verified empirically against the live repo + stdlib on `python3.6`
**Track scope:** This is ONE of three parallel Phase-1 research tracks. It owns **Success Criterion #3 (path-resolution self-check + unit test, PLGN-03-adjacent)** and **Success Criterion #4 (README, DOC-04)**, plus the project-plumbing assessment those two depend on. It does NOT cover the citation-gate track or the testability-boundary/domain-tier track.

---

## Summary

The repo is greenfield (no `c14/`, no `tests/`, no `setup.py`). Phase 1 must lay down a tiny pure-Python package (`c14/`) whose path-resolution helper derives bundled-data locations from `__file__`, not from `os.getcwd()` — because at runtime the plugin is unzipped into PyMOL's `startup/` dir and the CWD is unpredictable (PyMOL launch dir, last `cd`, etc.). This is the standard Python "package data" pattern; it is also already flagged as Pitfall #1 in `.planning/research/PITFALLS.md` and the #1 breakage mode in `.planning/research/SUMMARY.md`.

The recommendation is a single `c14/paths.py` module exposing `data_path(*parts) -> pathlib.Path` (pure resolver) plus a `selfcheck() -> str` (resolves a known fixture and asserts existence). A `unittest`-based test in `tests/test_paths.py` (stdlib only — **pytest is NOT installed** and installs are forbidden by AGENTS.md) proves CWD-independence by `os.chdir`-ing into a `tempfile.mkdtemp()` and asserting the fixture still resolves to an absolute, existing file. Bundled data lives in `c14/data/` (inside the package) so it ships in the PyMOL Plugin Manager zip.

The README already satisfies DOC-04 in full (verified by reading the 57-line `README.md` at repo root) — the planner should treat DOC-04 as a **verification task, not a creation task**. The one real plumbing bug: `.gitignore` line `./3rd_party_lib/**` does **not** ignore vendored libraries (empirically tested in the real repo — `git check-ignore` returns not-ignored) and must be fixed to `3rd_party_lib/` to satisfy AGENTS.md's "3rd_party_lib/** is git-ignored" rule.

**Primary recommendation:** Create `c14/paths.py` with `data_path()`/`selfcheck()`, a `c14/data/selfcheck.json` fixture, and `tests/test_paths.py` (unittest, chdir-to-tempdir proof). Fix the `.gitignore` `3rd_party_lib` line. Treat the README as already-done. Do NOT add `setup.py`/`pyproject.toml`/`conftest.py`/`pytest.ini` in Phase 1.

---

## Standard Stack

### Core (all stdlib — no installs, Python 3.6.9 verified)

| Module | Version | Purpose | Why Standard |
|--------|---------|---------|--------------|
| `pathlib` | stdlib (≥3.4) | Object-oriented paths; `Path.resolve()` | Available & functional on 3.6 (verified: `python3.6 -c "import pathlib; pathlib.Path('/tmp/x/../../y').resolve()"` works). Cleaner than `os.path` for return values; trivial `str()` coercion for PyMOL `cmd.*` string-path APIs. |
| `os` | stdlib | `os.chdir`, `os.getcwd` (test only) | Required to *prove* CWD-independence by actually changing directory in the test. |
| `tempfile` | stdlib | `tempfile.mkdtemp` (≥2.0) / `TemporaryDirectory` (≥3.2) | Creates a foreign working dir for the test. Verified available on 3.6. |
| `unittest` | stdlib | Test framework | **Mandatory**: `pytest` is NOT installed (`python3.6 -m pytest` → `No module named pytest`), and AGENTS.md forbids installs. `unittest` is the only option. |
| `shutil` | stdlib | `shutil.rmtree(ignore_errors=True)` (test cleanup) | Cleanup of the temp dir. |

### Not in the stack (deliberately excluded)

| Tool | Why excluded |
|------|--------------|
| `pytest` | Not installed; installs forbidden. Use `unittest`. |
| `setuptools` / `setup.py` / `pyproject.toml` | The plugin ships via PyMOL Plugin Manager (zip the package dir → `startup/`), NOT via `pip install`. A build-system file is premature in Phase 1 and would imply build tooling. Defer to Phase 11 packaging. Tests run from repo root with `c14` importable via sys.path — no install needed. |
| `conftest.py` / `pytest.ini` | pytest-only artifacts. Using `unittest` → none needed. |
| `pkg_resources` / `importlib.resources` | `importlib.resources` is **3.7+** (verified 2026-08-13: `python3.6 -c "import importlib.resources"` → `ModuleNotFoundError`; `dir(importlib)` has no resource attrs). We're on 3.6, installs forbidden → no backport. `__file__`-relative resolution is the dependency-free alternative and is sufficient for a single-package plugin. |

**Installation:** none. `python3.6 -m unittest discover -s tests -v` from repo root is the entire test command.

---

## Architecture Patterns

### Recommended Project Structure (Phase 1 scope only)

```
RPG_tale-of-C/
├── README.md                  # ALREADY EXISTS — DOC-04 compliant (verified)
├── .gitignore                 # EXISTS but has ONE bug (3rd_party_lib line — see Plumbing)
├── c14/                       # NEW — the plugin package (shipped in the .zip)
│   ├── __init__.py            # NEW — minimal, pymol/PyQt5-FREE (PLGN-03 import-cleanliness)
│   ├── paths.py               # NEW — path-resolution helper (pure-Python domain tier)
│   └── data/                  # NEW — bundled data files (inside package so they ship)
│       └── selfcheck.json     # NEW — tiny fixture for the self-check
└── tests/                     # NEW — tests live OUTSIDE the package (don't ship in zip)
    └── test_paths.py          # NEW — unittest proving CWD-independent resolution
```

**Why this layout:**
- `c14/data/` is **inside** the package → it is included when PyMOL Plugin Manager zips `c14/` and extracts into `startup/`. Data at repo root would NOT ship. This is the single most important structural decision.
- `tests/` is **outside** `c14/` → tests don't bloat the shipped plugin zip, and test infra is decoupled from the package. Running `python3.6 -m unittest discover -s tests` from repo root finds `test_paths.py` (default pattern `test*.py`); `c14` is importable because repo root is on `sys.path`.
- `c14/__init__.py` must be **pymol/PyQt5-free in Phase 1**: importing `c14.paths` (which the test does) runs `c14/__init__.py` first; if that imported `pymol.Qt`, the WSL unit test would crash (Qt needs a display). The full PyMOL plugin `__init__(self)` entry point arrives in a later phase.

### Pattern 1: `__file__`-relative resolution (the core invariant)

**What:** Derive bundled-data paths from the package's own `__file__` location, never from `os.getcwd()`.
**When to use:** Always, for any file bundled inside `c14/`.
**Why:** When PyMOL Plugin Manager extracts the zip into `startup/`, the runtime CWD is PyMOL's launch directory (or wherever the user's shell was) — unrelated to where the plugin lives. `os.getcwd()`-relative paths silently break; `__file__`-relative paths always work. This is Pitfall #1 in `.planning/research/PITFALLS.md` ("resolve every path via `os.path.dirname(__file__)` joined to the data dir") and the #1 breakage mode in `.planning/research/SUMMARY.md`.

**Proposed `c14/paths.py` (prescriptive — planner may adopt near-verbatim):**

```python
# Source: standard Python package-data pattern; corroborated by
# .planning/research/PITFALLS.md Pitfall 1 ("resolve every path via
# os.path.dirname(__file__) joined to the data dir").
# pathlib.Path is available on Python 3.6 (verified 2026-08-13).

"""Path resolution for the c14 plugin package.

Pure-Python (no pymol / PyQt5 imports) so it is unit-testable in WSL
without a display. All bundled-data lookups must go through data_path()
so they work regardless of the current working directory.
"""
from pathlib import Path

# Package root = the directory containing THIS file (c14/paths.py -> c14/).
# .resolve() makes it absolute and dereferences the repo symlink during dev.
_PACKAGE_ROOT = Path(__file__).resolve().parent


def data_path(*relative_parts: str) -> Path:
    """Resolve a bundled data file path relative to the package root.

    Returns an absolute Path derived from __file__, NOT from os.getcwd().
    Does NOT check existence -- callers should call .exists() or handle
    FileNotFoundError when opening. Returns Path (use str() for PyMOL
    cmd.* APIs that take string paths, e.g. cmd.load(str(data_path(...)))).

    Example:
        p = data_path("data", "story", "glucose.json")  # -> /abs/.../c14/data/story/glucose.json
    """
    return _PACKAGE_ROOT.joinpath(*relative_parts)


def selfcheck() -> str:
    """Resolve a known bundled fixture and verify it exists.

    Returns the fixture's absolute path as a string. Raises
    FileNotFoundError if the package data layout is broken (e.g. the
    data/ dir wasn't shipped). Intended to be called both by the unit
    test (to prove CWD-independence) and, in a later phase, by the plugin
    loader at startup (Pitfall 1 mitigation: "fail loud on plugin load").
    """
    fixture = data_path("data", "selfcheck.json")
    if not fixture.is_file():
        raise FileNotFoundError(
            "c14 path self-check failed: bundled fixture not found at "
            f"{fixture}. The package data/ directory may be missing."
        )
    return str(fixture)
```

**Design decisions (each flagged for planner confirmation):**

| Decision | Recommendation | Rationale |
|----------|----------------|-----------|
| Module name | `c14/paths.py` (NOT `_paths.py`) | Public utility imported by the rest of the package and by tests; leading underscore would signal internal-only. |
| Return type | `pathlib.Path` | Supports `.exists()`, `.read_text()`, `.is_file()` directly; `str(path)` coerces for PyMOL `cmd.*`. The `os.path` equivalent (`os.path.join(os.path.dirname(__file__), ...)`) is equally valid and matches PITFALLS.md's literal wording -- planner may pick either; pathlib is cleaner and type-friendlier. |
| Existence checking in `data_path()` | NO -- pure resolver only | Separation of concerns; callers open files and handle `FileNotFoundError` naturally. A resolver that raises couples path arithmetic to filesystem state and breaks "compute where a future file would go" use cases. |
| Existence checking in `selfcheck()` | YES -- raises `FileNotFoundError` | The "self-check" is explicitly about confirming the layout works; existence is its whole point. |
| Package name | `c14` | Short, matches the "C14" hero. **Planner/user to confirm** -- affects every import project-wide. |
| Fixture file | `c14/data/selfcheck.json` (content: a 1-line note) | Tiny, intentional, self-documenting; `.json` matches future story/citation JSON use. A hidden `.placeholder` also works -- planner's choice, minor. |

### Pattern 2: CWD-independence proof via real `os.chdir`

**What:** The unit test physically changes into an unrelated temp directory, then calls the helper. Existence-of-the-fixture-from-a-foreign-CWD *is* the proof: if the helper were cwd-relative, the file would not be found.
**When to use:** This is the exact pattern success criterion #3 demands ("resolution succeeds from an arbitrary working directory").
**Why not `mock.patch('os.getcwd')`:** mocking proves the helper doesn't call `getcwd`, but doesn't prove it doesn't use some *other* cwd-relative trick. A real `chdir` is the honest, end-to-end proof.

### Anti-Patterns to Avoid

- **`os.getcwd()`-relative data paths:** silently breaks on install. The reference plugins in `Pymol-script-repo/plugins/` actually do this wrong (e.g. `autodock_plugin.py:910` uses `os.path.abspath(os.curdir)`). Do NOT copy reference-plugin path handling -- see "Reference check" below.
- **Repo-root-relative data:** data outside `c14/` won't ship in the PyMOL zip. Bundled data MUST live under `c14/`.
- **`c14/__init__.py` importing pymol/PyQt5 in Phase 1:** would make `from c14.paths import data_path` trigger a Qt import → WSL unit tests crash. Keep `c14/__init__.py` pymol-free until the plugin-loader phase.
- **A resolver that raises on missing files:** couples path arithmetic to FS state; makes `data_path("data", "future", "file.json")` unusable for "compute where it would go" use cases. Resolve-only; let callers open.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Absolute path from package location | Custom `os.path` string surgery per call site | A single `data_path(*parts)` helper | One convention, enforced everywhere; Pitfall 1 says "bake it in on day one so every later phase inherits it." |
| "Does the bundled layout work?" check | Scattered `.exists()` asserts in feature code | `selfcheck()` called at plugin load + by the test | Centralizes the layout invariant; fail-loud at startup (Pitfall 1 mitigation). |
| Test working-directory isolation | Reimplementing cwd save/restore per test | `unittest` `setUp`/`tearDown` + `tempfile.mkdtemp` | Stdlib, idiomatic, handles cleanup. |
| CWD-independence assertion | `mock.patch` of `os.getcwd` | Real `os.chdir(tempdir)` + existence assert | End-to-end honest proof (mock only proves the call site, not the behavior). |

**Key insight:** The whole point of Phase 1 is to make the path convention a *convention enforced once*, so no later phase can get it wrong. One helper + one test is the entire enforcement mechanism.

---

## Common Pitfalls

### Pitfall 1: CWD-relative paths break on plugin install
**What goes wrong:** Code uses `"data/foo.pdb"` or `os.path.join(os.getcwd(), "data", ...)`. In dev (run from repo root) it works. After PyMOL Plugin Manager extracts the zip into `startup/`, the runtime CWD is PyMOL's launch dir → the relative path points nowhere → silent `FileNotFoundError` or empty structures.
**Why it happens:** Dev runs from repo root, so cwd-relative "works" during development, hiding the bug.
**How to avoid:** All bundled-data lookups go through `data_path()` (derived from `__file__`). The Phase 1 test proves this by chdir-ing away from repo root.
**Warning signs:** Feature works when you run `python -m` from repo root, fails when run from `~` or from inside PyMOL.

### Pitfall 2: `c14/__init__.py` imports Qt, breaking WSL unit tests
**What goes wrong:** A later phase adds the PyMOL plugin `__init__(self)` entry to `c14/__init__.py` and imports `pymol.Qt` at module top. Then `from c14.paths import data_path` (run by the test) executes `c14/__init__.py` first → Qt import → crash in headless WSL (no display).
**Why it happens:** Python imports the package's `__init__.py` before a submodule. Any top-level Qt import there poisons every pure-Python submodule import.
**How to avoid:** Keep `c14/__init__.py` minimal (docstring + `__version__`) and pymol/PyQt5-free in Phase 1. When the loader phase arrives, guard Qt imports behind the `__init__(self)` function (function-local import) or a lazy-import pattern, never module-top-level.
**Warning signs:** `python3.6 -m unittest` fails with a Qt/display error despite `paths.py` having no Qt imports.

### Pitfall 3: Data dir outside the package doesn't ship
**What goes wrong:** Data placed at repo-root `data/` (sibling of `c14/`) for "tidiness". PyMOL Plugin Manager zips `c14/` only → `data/` is left behind → `selfcheck()` raises at runtime on a user's machine but passed in dev (because dev cwd = repo root).
**How to avoid:** Bundled data lives under `c14/data/`. Period.

### Pitfall 4: `.gitignore` `./`-prefix patterns silently fail (FOUND IN THIS REPO)
**What goes wrong:** A line like `./3rd_party_lib/**` *looks* like it ignores vendored libs but does NOTHING. Vendored libraries get committed by accident.
**Why it happens:** gitignore patterns with a leading `./` only match that exact relative form and don't behave like the plain pattern. (Empirically verified 2026-08-13 in the real repo: `git check-ignore -v 3rd_party_lib/foo/bar.txt` → exit 1 = NOT ignored; the bare form `3rd_party_lib/` → ignored. Also confirmed in an isolated scratch repo: `./3rd_party_lib/**` fails, `3rd_party_lib/**` works.)
**How to avoid:** Drop the `./` prefix. See "Project plumbing assessment" for the exact fix.

---

## Code Examples

### The unit test (`tests/test_paths.py`) — prescriptive, adopt near-verbatim

```python
# Source: stdlib unittest pattern; CWD-independence proof via real os.chdir.
# Python 3.6 compatible (tempfile.mkdtemp, pathlib, unittest all stdlib).

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from c14.paths import data_path, selfcheck


class TestPathResolution(unittest.TestCase):
    """Prove bundled-data resolution is CWD-independent (Phase 1 SC #3)."""

    def setUp(self):
        # Run EVERY test from a foreign working directory so CWD-independence
        # is proven for free on every assertion, not just one named test.
        self._orig_cwd = os.getcwd()
        self._tmp = tempfile.mkdtemp(prefix="c14_pathtest_")
        os.chdir(self._tmp)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_selfcheck_resolves_from_arbitrary_cwd(self):
        # If resolution were cwd-relative, the fixture would not be found
        # from this temp dir -> selfcheck() would raise. Existence here IS
        # the proof of __file__-relative (not cwd-relative) resolution.
        resolved = selfcheck()  # raises FileNotFoundError if missing
        p = Path(resolved)
        self.assertTrue(p.is_absolute(), f"{p} is not absolute")
        self.assertTrue(p.is_file(), f"{p} does not exist from cwd={os.getcwd()}")
        # And it must NOT be under the temp cwd (belt-and-suspenders):
        self.assertNotEqual(p.resolve().parent, Path(self._tmp).resolve())

    def test_data_path_returns_absolute_path(self):
        p = data_path("data", "selfcheck.json")
        self.assertTrue(p.is_absolute(), f"{p} is not absolute")
        # The resolved path's root must be the package dir, derived from __file__:
        pkg_root = Path(__file__).resolve().parent.parent / "c14"
        self.assertEqual(p.resolve().parent, (pkg_root / "data").resolve())

    def test_data_path_does_not_raise_for_nonexistent_file(self):
        # Resolver must NOT raise for a not-yet-present path; it just resolves.
        p = data_path("data", "does-not-exist-yet.json")
        self.assertTrue(p.is_absolute())
        self.assertFalse(p.exists())


if __name__ == "__main__":
    unittest.main()
```

**Run it (no installs, no config):**
```bash
python3.6 -m unittest discover -s tests -v
# or single-file:
python3.6 -m unittest tests.test_paths -v
```

### The fixture (`c14/data/selfcheck.json`)
```json
{"purpose": "c14 path-resolution self-check fixture -- do not delete"}
```

### The minimal `c14/__init__.py` (Phase 1)
```python
"""c14 -- RPG: Tale of C PyMOL plugin package.

Phase 1: minimal, pymol/PyQt5-FREE so pure-Python submodules (paths.py)
stay unit-testable in WSL. The PyMOL plugin __init__(self) entry point
arrives in a later phase; when it does, Qt imports must be function-local,
never module-top-level (see 01-RESEARCH-paths.md Pitfall 2).
"""
__version__ = "0.0.1-dev"
```

---

## Project Plumbing Assessment

### `.gitignore` review (existing 15-line file at repo root)

| Line | Entry | Status | Action |
|------|-------|--------|--------|
| 1 | `Pymol-script-repo` | OK (ignores the symlinked dir; `git check-ignore` confirms ignored) | Keep. |
| 2 | `./Pymol-script-repo/**` | Redundant + broken-form, but harmless (line 1 already covers it) | Optional: delete (dead line). |
| 3 | (blank) | — | — |
| 4 | `*.env` | OK | Keep. |
| 5 | `*.pyc` | OK-ish; catches compiled files but not the `__pycache__/` dir idiom | Recommend: also add `__pycache__/` (standard idiom; catches `*.pyo` too). |
| 6 | `*.npy` | OK | Keep. |
| 7 | `*.npz` | OK | Keep. |
| 8 | (blank) | — | — |
| 9 | `**/secrets.toml` | OK | Keep. |
| 10 | `**/auth.json` | OK | Keep. |
| 12 | `#./dev_env_note.txt` | Comment, harmless | Keep. |
| 13 | `./3rd_party_lib/**` | **BROKEN — does not ignore** (verified). NO bare fallback exists. AGENTS.md requires `3rd_party_lib/**` git-ignored → **non-compliant.** | **MUST FIX:** replace with `3rd_party_lib/` (or `3rd_party_lib/**`). |
| 14 | `tmp` | OK (ignores dir; covers `tmp/pymol-src/` symlink target) | Keep. (Could write `tmp/` for clarity — equivalent.) |
| 15 | `biochemeleon.zip` | OK (sibling-project artifact) | Keep. |

**The one must-fix:** line 13. Exact edit:

```diff
-./3rd_party_lib/**
+3rd_party_lib/
```

(Rationale for trailing-slash form `3rd_party_lib/` over `3rd_party_lib/**`: the dir form is the idiomatic gitignore for "ignore this directory and everything under it" and is unambiguous. Either works once the `./` prefix is removed; the trailing-slash form is shortest and clearest.)

**Optional cleanups** (low priority, planner's call):
- Add `__pycache__/` (line 5 area) — standard hygiene; Phase 1 creates `c14/__pycache__/` and `tests/__pycache__/` when tests run.
- Delete the dead `./Pymol-script-repo/**` line 2.
- Consider adding `.eggs/`, `*.egg-info`, `build/`, `dist/` ONLY if/when a `setup.py` is introduced (not in Phase 1).
- `.pytest_cache/` not needed (we use unittest).

**Verification command for the planner/verifier:**
```bash
git check-ignore -v 3rd_party_lib/foo/bar.txt && echo "FIXED (ignored)" || echo "STILL BROKEN"
```

### `setup.py` / `pyproject.toml` — NOT needed in Phase 1

**Recommendation: do NOT add either in Phase 1.** Rationale:
- The plugin ships via PyMOL Plugin Manager (zip the package dir → `startup/`), NOT via `pip install`. A build-system file is premature and would imply setuptools/build tooling (friction with AGENTS.md's "no new dependencies silently" rule).
- Tests run from repo root; `c14` is importable because the repo root is on `sys.path` when invoking `python3.6 -m unittest` from there. No install step is needed for the test to do `from c14.paths import data_path`.
- Defer packaging metadata to Phase 11 (documentation/packaging finalization) when the plugin is actually ready to ship.

### `conftest.py` / `pytest.ini` — NOT needed

Using `unittest` (stdlib), not pytest. `python3.6 -m unittest discover -s tests` needs no config file. HIGH confidence.

### `__init__.py` needs

| Location | Needed in Phase 1? | Content |
|----------|--------------------|---------|
| `c14/__init__.py` | **YES** (makes `c14` a package; required for `from c14.paths import ...`) | Minimal: docstring + `__version__`. **MUST be pymol/PyQt5-free** (Pitfall 2). |
| `tests/__init__.py` | NO | `unittest discover` finds `tests/test_paths.py` via the `test*.py` pattern without it. Adding it is harmless but unnecessary. Recommend omitting. |
| Repo-root `__init__.py` | **NO** (would make the repo root a package — wrong) | Do not add. |

### Test-run command (the canonical verification for SC #3)

```bash
# From repo root. Exit 0 = all tests pass = SC #3 satisfied.
python3.6 -m unittest discover -s tests -v
```
No environment variables, no installs, no config files. This is the entire CI surface for Phase 1's path criterion.

---

## README Assessment (Success Criterion #4 — DOC-04)

**DOC-04 requirement (from `.planning/REQUIREMENTS.md` line 59):** "Initial minimal README.md with 'Under Development' banner, description, and TBD placeholder sections (Installation Instructions, References, etc.)."

**The repo root already has a `README.md` (57 lines).** Read in full on 2026-08-13. Compliance checklist:

| DOC-04 requirement | Existing README location | Status |
|--------------------|--------------------------|--------|
| (a) "Under Development" banner | Line 6: `> **⚠️ Under Development**` (with context line 7-8) | **MET** |
| (b) Project description | Lines 10-21: full description (PyMOL 2.5.0 plugin, C14 hero, respiration RPG, branching storylines, educator audience) | **MET** |
| (c) TBD: Installation Instructions | Lines 33-36: `**TBD** — will be provided once the plugin is built and packaged...` | **MET** |
| (c) TBD: Requirements | Lines 38-41: `**TBD** — PyMOL 2.5.0 with PyQt5...` | **MET** |
| (c) TBD: References | Lines 43-47: `**TBD** — scientific sources... cited per the project's no-fabricated-science rule.` | **MET** |
| (c) TBD: Cast (etc.) | Lines 49-52: `**TBD** — a dramatic cast list... (Phase 9).` | **MET** |

**Conclusion: DOC-04 is ALREADY SATISFIED.** HIGH confidence (read the file directly). The README actually *exceeds* the minimum — it also has a "Featuring" cast slogan (spec.md requirement, line 25), a "Status" section, and a License section.

**Planner guidance for DOC-04:** Treat as a **verification task, NOT a creation task.** Suggested plan action: "Verify `README.md` exists at repo root with (a) 'Under Development' banner, (b) description, (c) TBD sections for Installation/References/Cast." No content changes needed.

**Constraints respected (do NOT change):**
- Do NOT add real scientific citations — gated by CITE-01 (separate track) and later phases.
- Do NOT add real cast data (PDB IDs, resolutions) — Phase 9.
- The README must stay TBD for science content. It already does. Leave it.

**Bonus check — internal links resolve:** README references `.planning/ROADMAP.md` (lines 8, 31) — exists ✓. `spec.md` (line 30) — exists ✓. `LICENSE` / `LICENSE_pymol-open-source` (lines 56-57) — exist ✓. No broken links.

---

## Reference Check (Pymol-script-repo/plugins/)

Investigated whether the 31 single-file reference plugins model bundled-data path resolution. Findings:

- **Zero reference plugins use `__file__` for bundled data.** `grep -ln "__file__" *.py` across all 31 plugins returned **no matches**. The reference repo does NOT provide a bundled-data path pattern to copy.
- **Only `outline.py` uses `pathlib`** (1 of 31), and only for a rename-path operation (`new_path = Path(new_name)`), not for bundled package data.
- **Plugins that handle data files** (`Caver2_1_2.py`, `annocryst.py`, `autodock_plugin.py`, `emovie.py`, `mole.py`, `msms.py`, `vina.py`) reference data via **external tool paths** (`PYMOL_GIT_MOD`, `PYMOL_PATH` env vars), **user home-dir configs** (`os.path.join(home, '.ADplugin')`), or **CWD** (`os.path.abspath(os.curdir)` in `autodock_plugin.py:910` — the exact anti-pattern Pitfall 1 warns against). None bundle data inside their own package.
- **`dynoplot.py`** (the modern-Qt reference flagged in AGENTS.md: `from pymol.Qt import QtCore, QtGui, QtWidgets`) is a pure single-file plot widget with no bundled data and no `__file__` usage. It confirms the Qt import *style* to match, but not data-path handling.

**Implication:** The `__file__`-relative package-data pattern must be implemented from standard Python packaging practice, not copied from the reference repo. The reference repo actively demonstrates the *wrong* pattern (CWD-relative) in `autodock_plugin.py`. This research's `c14/paths.py` design stands on the standard Python convention + `.planning/research/PITFALLS.md` Pitfall 1, not on reference-plugin precedent. This is a useful negative finding: "don't look to reference plugins for bundled-data paths."

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os.path.dirname(__file__)` string surgery | `pathlib.Path(__file__).resolve().parent` | pathlib stable since 3.4 | Cleaner, returns Path objects; `os.path` form still 100% valid. Both work on 3.6. |
| `pkg_resources.resource_string` (setuptools) | `importlib.resources` (stdlib) | 3.7 (stdlib) | **Not available on 3.6** (verified) — we cannot use either cleanly. `__file__`-relative resolution is the dependency-free fallback and is correct for a single-package plugin. |
| CWD-relative data paths (reference plugins) | `__file__`-relative (package data) | Python packaging best practice | Mandatory for any plugin that bundles data and is installed into an arbitrary CWD (exactly our case). |

**Deprecated/outdated for this project:**
- `importlib.resources` / `pkg_resources`: unavailable (3.6) or heavy (setuptools). Use `__file__`-relative.
- Any CWD-derived path: deprecated by Pitfall 1.

---

## Open Questions / Decisions for the Planner

1. **Package name `c14`** — recommended (short, matches the hero). Affects every import project-wide. **Needs planner/user confirmation.** If the user prefers a different name (e.g. `tale_of_c`, `c14rpg`), swap it everywhere in this research's code examples.
2. **`pathlib.Path` vs `os.path`** for the resolver — recommend `pathlib` (cleaner, Path return type). `os.path.dirname(__file__)` (PITFALLS.md's literal wording) is equally valid; planner picks. The test's `Path(...)` assertions work either way if the helper returns `str`.
3. **Fixture file** — recommend `c14/data/selfcheck.json` (1-line note). A hidden `c14/data/.placeholder` is equally fine. Minor; planner's choice.
4. **`setup.py`/`pyproject.toml` in Phase 1** — recommend NONE (defer to Phase 11). Confirm the planner agrees; if a minimal `setup.py` is desired for dev-install ergonomics, add `.eggs/`/`*.egg-info`/`build/`/`dist/` to `.gitignore`.
5. **`selfcheck()` scope** — recommend it live in `c14/paths.py` (this research). Alternative: a separate `c14/_selfcheck.py`. Co-locating with the resolver is simpler; recommend keeping together.
6. **When does the plugin loader call `selfcheck()`?** — Out of Phase 1 scope (no loader yet). The helper is designed so a later phase can call `c14.paths.selfcheck()` at plugin load to "fail loud" (Pitfall 1 mitigation). The Phase 1 *test* is the first caller. Flag for the plugin-loader phase.

---

## Sources

### Primary (HIGH confidence)
- **Live repo inspection (2026-08-13):** `README.md` (57 lines, read in full), `.gitignore` (15 lines, read in full), `spec.md`, `.planning/REQUIREMENTS.md` (PLGN-03 / DOC-04 wording), `.planning/ROADMAP.md` (Phase 1 SC #3 wording, line 41), `.planning/config.json` (`commit_docs: true`), `.planning/research/PITFALLS.md` (Pitfall 1), `.planning/research/SUMMARY.md` (#1 breakage mode).
- **Empirical verification on `python3.6` (3.6.9):** `pathlib.Path(...).resolve()` works; `tempfile.mkdtemp` available; `unittest` stdlib; `pytest` NOT installed (`No module named pytest`); `importlib.resources` NOT available (`ModuleNotFoundError`, `dir(importlib)` has no resource attrs).
- **Empirical `.gitignore` verification (real repo + isolated scratch repo):** `./3rd_party_lib/**` → NOT ignored (exit 1); `3rd_party_lib/` / `3rd_party_lib/**` → ignored (exit 0). `git check-ignore -v` on `Pymol-script-repo`, `tmp`, `*.env`, `*.npy`, `*.npz`, `secrets.toml`, `auth.json` → all ignored.
- **Reference plugin scan:** `grep -ln "__file__" Pymol-script-repo/plugins/*.py` → 0 matches; `grep -ln "pathlib"` → only `outline.py`; `autodock_plugin.py:910` uses `os.path.abspath(os.curdir)` (the anti-pattern); `dynoplot.py:18-21` confirms modern Qt import style.

### Secondary (MEDIUM confidence)
- `.planning/research/PITFALLS.md` & `SUMMARY.md` prior research asserting `os.path.dirname(__file__)` as the mitigation — consistent with this research's recommendation (pathlib is the modern equivalent).

### Tertiary (LOW confidence)
- None. All findings verified against the live repo or stdlib.

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — stdlib availability empirically verified on 3.6; pytest absence confirmed; importlib.resources absence confirmed.
- Architecture (path helper + layout): **HIGH** — `__file__`-relative is standard Python; corroborated by prior PITFALLS.md research; layout driven by PyMOL Plugin Manager packaging model (zip the package dir).
- Unit test pattern: **HIGH** — unittest is the only available framework; chdir-to-tempdir is the canonical CWD-independence proof; all APIs verified on 3.6.
- `.gitignore` 3rd_party_lib bug: **HIGH** — empirically reproduced in the real repo AND an isolated scratch repo (two independent confirmations).
- README DOC-04 compliance: **HIGH** — read the file in full; every sub-requirement present.
- setup.py deferral: **MEDIUM** — judgment call (defensible; planner/user may prefer a minimal setup.py for dev ergonomics).

**Research date:** 2026-08-13
**Valid until:** 2027-02-13 (stable: stdlib + gitignore semantics don't drift; re-verify only if Python target version or PyMOL packaging model changes).
