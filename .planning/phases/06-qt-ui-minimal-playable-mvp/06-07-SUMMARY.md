---
phase: 06-qt-ui-minimal-playable-mvp
plan: 07
subsystem: ui
tags: [pymol-plugin, qt, addmenuitemqt, zip, packaging, ast-gate, lazy-import, singleton, plugin-entry]

# Dependency graph
requires:
  - phase: 06-02
    provides: user_data_path resolver (the MainWindow constructed lazily by the entry point resolves user data through it; survival across PyMOL restarts)
  - phase: 06-06
    provides: Qt-free Controller + HeroResolver (constructed by the MainWindow on first menu click; the entry point defers all construction to click time)
provides:
  - "__init_plugin__(pmgapp) entry point in c14/__init__.py (PLGN-01): selfcheck() + relative-import delegation to c14.ui.plugin_entry"
  - "c14/ui/plugin_entry.py: init_plugin registers 'RPG: Tale of C' via pymol.plugins.addmenuitemqt; _open_main_window lazily constructs + shows the MainWindow singleton"
  - "tools/build_plugin_zip.sh: produces dist/c14-<version>.zip with Case-1 layout (PLGN-02) — c14/__init__.py at zip root, story_glucose bundled under c14/data/, __pycache__/*.pyc/downloaded/ excluded"
affects: [06-08 (MainWindow -- the deferred-import target of _open_main_window), 06-14 (human-verify install + menu appearance), "Phase 7+ content (ships via the zip)"]

# Tech tracking
tech-stack:
  added: []  # no new dependencies -- python3.6 stdlib zipfile/shutil only
  patterns:
    - "Lazy-delegate plugin entry: pure-Python package root defines __init_plugin__ but imports NO pymol/PyQt5; delegates to gate-exempt c14/ui/ via relative import (the ONLY ast.walk-clean path)"
    - "Lazy singleton construction: register the menu cheaply at plugin load; construct the QMainWindow on first click (not at startup -- matches dynoplot.py:445-447)"
    - "Case-1 zip build via stdlib: bash orchestrator + python3.6 zipfile/shutil for WSL portability (no zip/unzip binary needed; PyMOL's installer is also Python zipfile)"

key-files:
  created:
    - c14/ui/plugin_entry.py
    - tools/build_plugin_zip.sh
  modified:
    - c14/__init__.py
    - .gitignore

key-decisions:
  - "__init_plugin__ delegates via `from .ui import plugin_entry` (relative import) -- gate-forced: ast.walk recurses into function bodies so even a function-local `import pymol` would be flagged; `ui` is not in BANNED_TOP so the relative import is the only gate-clean path"
  - "MainWindow constructed lazily on first menu click (cheap addmenuitemqt registration at load; expensive QMainWindow + widget construction deferred -- avoids slowing every PyMOL startup)"
  - "pmgapp is ignored by the Qt layer (modern plugin convention; passed through to plugin_entry.init_plugin for forward-compat but unused -- matches dynoplot.py/optimize.py/outline.py)"
  - "Metadata `# Version: 0.0.1` (Plugin Manager Info) coexists with `__version__ = \"0.0.1-dev\"`; zip name uses the __version__ string -> dist/c14-0.0.1-dev.zip"
  - "Build uses python3.6 stdlib zipfile/shutil (zip/unzip not installed in WSL; AGENTS.md forbids apt install) -- produces a standard zip PyMOL's installer reads natively"

patterns-established:
  - "Pattern: plugin entry = pure-Python root + gate-exempt ui delegate (c14/__init__.py stays gate-clean; all Qt lives in c14/ui/)"
  - "Pattern: build script = bash orchestrator + python3.6 stdlib for portability (no external zip binary dependency)"

# Metrics
duration: 5 min
completed: 2026-08-30
---

# Phase 6 Plan 7: Plugin Entry Point + Zip Builder Summary

**PyMOL `__init_plugin__` lazy-delegate (AST-gate-clean) + `addmenuitemqt` menu registration + Case-1 Plugin-Manager zip builder (stdlib `zipfile`, story bundled, cache/pyc excluded)**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-08-29T17:59:19Z
- **Completed:** 2026-08-29T18:04:11Z
- **Tasks:** 3
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments
- Made `c14` loadable as a PyMOL 2.5.0 plugin: `c14/__init__.py` defines `__init_plugin__(pmgapp)` that calls `c14.paths.selfcheck()` (fail-loud layout invariant) then delegates to `c14/ui/plugin_entry.py` via a gate-clean relative import. The AST gate (`tools/check_imports.py`) stays GREEN (exit 0) -- the ONE allowed modification to the pure-Python `c14/` root in Phase 6.
- `c14/ui/plugin_entry.py` (gate-EXEMPT) registers the "RPG: Tale of C" menu item via `pymol.plugins.addmenuitemqt` and lazily constructs + re-shows the `MainWindow` singleton on first click. All `pymol.Qt`/`pymol.plugins` imports are deferred to function bodies, so the file `py_compile`s without Qt installed and merely importing `c14` never touches Qt.
- `tools/build_plugin_zip.sh` produces `dist/c14-0.0.1-dev.zip` (46 entries, ~96 KB) with Case-1 layout (`c14/__init__.py` is the first entry), bundles `data/story_glucose/` into `c14/data/story_glucose/`, and excludes `__pycache__`/`*.pyc`/`c14/data/assets/downloaded/` -- installable via PyMOL Plugin Manager (PLGN-02). Built + sanity-checked end-to-end in WSL.

## Task Commits

Each task was committed atomically (path-scoped -- only the task's files staged):

1. **Task 1: Create c14/ui/plugin_entry.py (init_plugin + addmenuitemqt + lazy singleton)** -- `f223c8f` (feat)
2. **Task 2: Add __init_plugin__ to c14/__init__.py (selfcheck + relative-import delegation)** -- `cd44ecd` (feat)
3. **Task 3: Create tools/build_plugin_zip.sh (Case-1 zip + story copy + exclusions)** -- `e914e78` (feat)
4. **Deviation: gitignore dist/ build output** -- `c7f31b8` (chore)

**Plan metadata:** (this commit) `docs(06-07): complete plugin-entry-point plan`

## Files Created/Modified
- `c14/ui/plugin_entry.py` (created) -- Qt plugin entry point; `init_plugin(pmgapp)` registers the menu via `addmenuitemqt`; `_open_main_window()` lazily constructs/shows the `MainWindow` singleton; all pymol imports deferred to function bodies (gate-exempt dir).
- `c14/__init__.py` (modified) -- added `# Version/Author/Citation-Required` metadata block (top of file; parsed by `PluginInfo.get_metadata`) + `__init_plugin__(pmgapp)` (selfcheck + relative-import delegation); AST gate stays clean.
- `tools/build_plugin_zip.sh` (created) -- bash build script producing `dist/c14-<version>.zip` (Case-1 layout, story bundled, cache/pyc excluded, post-build sanity check); WSL-runnable via python3.6 stdlib.
- `.gitignore` (modified) -- added `dist/` (build-output dir; regenerable, not committed).

## Decisions Made
- **Lazy-delegate via relative import (gate-forced).** `__init_plugin__`'s body contains ONLY `from .paths import selfcheck` / `selfcheck()` / `from .ui import plugin_entry` / `plugin_entry.init_plugin(pmgapp)`. Verified: the only `ast.Import`/`ast.ImportFrom` nodes in `c14/__init__.py` are the two relative `ImportFrom` (modules `paths` + `ui`, both non-BANNED); no dynamic-import lines. The FROZEN-verbatim docstring intentionally mentions `pymol`/`PyQt5` as documentation TEXT (e.g. "All pymol/PyQt5 imports are deferred...") -- this is fine because the real gate scans import NODES + `__import__`/`import_module` lines, not docstring text; gate exits 0.
- **Lazy singleton construction.** Menu registration is one cheap `addmenuitemqt` call at plugin load; the `MainWindow` (molops stack + Controller + widgets) is constructed only on first click -- matches `dynoplot.py:445-447`. This plan can execute BEFORE 06-08 (MainWindow) because the `from .main_window import MainWindow` import is inside `_open_main_window` (click-time); `plugin_entry.py` `py_compile`s even when `main_window.py` does not yet exist.
- **`pmgapp` passed through but ignored.** Modern Qt plugins ignore `pmgapp` (named `self`/`app`/`app=None` in the 3 reference plugins); `addmenuitemqt` does not need it. Passed through to `plugin_entry.init_plugin(pmgapp)` for forward-compat; if a parent window is ever needed, use `from pymol.gui import get_qtwindow` (06-RESEARCH-qt-packaging.md Open Question 1).
- **Metadata vs `__version__`.** Added `# Version: 0.0.1` metadata (shown in Plugin Manager Info via `get_version`, which prefers the metadata field) while keeping `__version__ = "0.0.1-dev"`. The zip name uses the `__version__` string (per the plan's "prefer __version__") -> `dist/c14-0.0.1-dev.zip`.
- **Build via python3.6 stdlib (not zip/unzip CLIs).** `zip`/`unzip` are not installed in this WSL shell and AGENTS.md forbids `apt install`; the build script uses `shutil.copytree`/`shutil.rmtree`/`zipfile.ZipFile` instead. PyMOL's own installer (`plugins/installation.py:extract_zipfile`) is also Python `zipfile`, so the produced zip is installer-native. No new dependencies.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] zip/unzip CLIs not installed in WSL -> build uses python3.6 stdlib zipfile/shutil**
- **Found during:** Task 3 (build_plugin_zip.sh)
- **Issue:** The plan prescribed `zip -r` (build) and `unzip -l` (post-build sanity check), but `which zip` and `which unzip` both exit 1 (binaries not present in the WSL dev shell). AGENTS.md forbids `pip`/`apt`/`conda` installs, so the CLIs cannot be added.
- **Fix:** `tools/build_plugin_zip.sh` is a bash orchestrator that delegates staging + zipping + the post-build sanity check to `python3.6` stdlib (`shutil.copytree`/`shutil.rmtree`/`zipfile.ZipFile`). Produces a standard `.zip` (Case-1 layout, story bundled, `__pycache__`/`*.pyc`/`downloaded/` excluded) that PyMOL's installer reads natively (it is itself Python `zipfile`). The script's internal sanity check mirrors the plan's `unzip -l` assertions (`names[0] == "c14/__init__.py"`, required entries present, no forbidden entries, single top-level `c14/` dir).
- **Files modified:** tools/build_plugin_zip.sh
- **Verification:** `bash tools/build_plugin_zip.sh` exits 0; independent `python3.6 zipfile` re-check confirms all 5 plan verify conditions (first file `c14/__init__.py`, 0 `downloaded/`, 0 `.pyc`, `c14/data/story_glucose/manifest.json` present, `c14/ui/plugin_entry.py` present).
- **Committed in:** e914e78 (Task 3 commit)

**2. [Rule 2 - Missing Critical] dist/ was untracked -> added to .gitignore**
- **Found during:** Task 3 (post-build)
- **Issue:** `dist/` (the zip build-output dir) was NOT gitignored (`git check-ignore` exit 1), so `git status` showed `?? dist/`. With 3 parallel executor sessions active (06-08/09/11), a future `git add .` could accidentally commit the ~96 KB zip artifact.
- **Fix:** Added `dist/` to `.gitignore` (5-line additive block with a comment) -- standard build-output convention. `git check-ignore dist/` now exits 0.
- **Files modified:** .gitignore
- **Verification:** `git check-ignore dist/c14-0.0.1-dev.zip` exits 0; `git status --short` no longer lists `dist/`.
- **Committed in:** c7f31b8 (separate chore commit, scoped to .gitignore -- kept Task 3's feat commit scoped to exactly the plan's files_modified)

---

**Total deviations:** 2 auto-fixed (1 Rule 3 blocking, 1 Rule 2 missing critical)
**Impact on plan:** Both auto-fixes necessary for WSL-runnable build + clean working tree during parallel execution. No scope creep -- the deliverables (Case-1 zip, story bundle, exclusions, post-build sanity) match the plan exactly; only the implementation mechanism changed (stdlib vs CLI). `.gitignore` is a 1-line-convention supporting change.

## Issues Encountered
None beyond the two deviations above. The CRITICAL AST-gate constraint (c14/__init__.py must stay gate-clean) was satisfied on the first attempt -- the FROZEN-verbatim `__init_plugin__` body uses only relative imports (`paths`, `ui` -- both non-BANNED), and the docstring's textual mentions of `pymol`/`PyQt5` are not flagged by the real gate (which scans import nodes + `__import__`/`import_module` lines, not docstrings).

## User Setup Required
None -- no external service configuration. The plugin is installed locally via PyMOL's Plugin Manager (no API keys / env vars).

## Next Phase Readiness
- **Plugin entry + zip builder ready.** `c14` is now loadable as a PyMOL 2.5.0 plugin; `dist/c14-0.0.1-dev.zip` is installable via Plugin Manager.
- **06-08 (MainWindow) is the deferred-import target.** `_open_main_window` does `from .main_window import MainWindow` at click time; this plan executed before 06-08 and `plugin_entry.py` `py_compile`s regardless. Once 06-08 delivers `MainWindow`, clicking the menu constructs the window (molops stack + Controller + widgets).
- **Human-verify (06-14):** install `dist/c14-0.0.1-dev.zip` via PyMOL Plugin Manager (Plugin -> Plugin Manager -> Install New Plugin -> pick zip), restart PyMOL, confirm a "RPG: Tale of C" menu item appears (PLGN-01), click it, confirm the MainWindow opens. Qt paths are NOT exercisable in WSL (no display) -- `plugin_entry.py` is `py_compile`-only in WSL; the real menu/window is human-verify only (AGENTS.md).
- **No blockers.** AST gate GREEN; py_compile GREEN; build GREEN; `import c14` works in pure WSL without touching Qt.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-30*
