# Technology Stack

**Analysis Date:** 2026-09-10

## Status Note: This Is NOT an Early-Stage Repo

The root `README.md` ("early planning stage. No runnable plugin code exists yet") is **stale** — phases 1–6 are COMPLETE and phase 7 (glucose endings) / 7.1 (story editor) are nearly complete (see `.planning/STATE.md`). Real, tested plugin code exists:

- `rpg/` — the plugin package (~6,500 lines across `rpg/*.py`, `rpg/story/`, `rpg/ui/`, `rpg/pymol_layer/`)
- `tests/` — 599 unit tests, all passing (`python3.6 -m unittest discover -s tests` → OK)
- `tools/` — dev/gate tooling (~17,000 lines including the story-editor JS assets)
- `data/` — story content + citation registries (77 claims, 73 approved / 4 pending)
- `dist/rpg-0.0.1-dev.zip` — built, Plugin-Manager-installable artifact

Everything below documents what **exists**; planned-but-missing items are explicitly marked.

## Languages

**Primary:**
- **Python 3.6** — the entire plugin (`rpg/`), tests (`tests/`), and dev tooling (`tools/*.py`). Syntax is pinned to 3.6.9 (the WSL shell interpreter): **no `@dataclass`** (3.7+; verified `ModuleNotFoundError` on 3.6.9 — see `rpg/citations.py:15`), **no f-strings in `rpg/`** (`.format()` / `%` / concatenation convention; enforced by convention and grepped in story-editor test batteries), **no walrus operator** (3.8+). Every data layer file is pure-stdlib, pure-Python.

**Secondary:**
- **JavaScript ES5** — dev-tool only: `tools/story_editor_assets/*.js` (14 IIFE assets, ~17,000 lines: `00_core.js`, `10_load.js`, `40_form.js`, `42_choices.js`, `45_lifecycle.js`, `80_save.js`, `90_boot.js`, etc.). ES5 discipline is test-enforced (`tests/test_story_editor_*.py` grep for block-scoped ES5). No framework, no bundler, no network — assets are inlined into a single committed `story_editor.html` at repo root by `tools/story_editor.py`.
- **Bash** — build/verification scripts: `tools/build_plugin_zip.sh`, `tools/run_headless.sh`.
- **HTML/CSS** — generated artifacts only: `story_editor.html` (committed, repo root, ~17,000 lines) and `dev/story_graph_viewer.html` (committed review viewer). Both offline, zero-network pages.

## Runtime

**Environment (critical operational split — the #1 way to break things):**
- **Dev shell: WSL Ubuntu.** `python3.6` (3.6.9) is the ONLY interpreter used for syntax checks and unit tests. **Do NOT install anything, do NOT create conda envs, do NOT `pip install`** (spec.md §WORKING ENV; `opencode.json` denies `rm*`/`rg*` and gates pip/apt/conda/python behind "ask").
- **Runtime host: PyMOL 2.5.0 (open-source, Anaconda) in a Windows conda env** (`chemtools-win10`), NOT WSL. A WSL agent cannot launch the interactive GUI and cannot execute `pymol.Qt.*` at runtime (Qt needs a real display).
- **Headless bridge:** WSL CAN run pure-`pymol.cmd.*` scripts headlessly via `tools/run_headless.sh` → `cmd.exe /c "C:\src\run-conda-pymol.bat -cq <winpath>"` (150s timeout; verdict from a `^SMOKE_RESULT: PASS` stdout sentinel because the .bat always exits 0 — see `tools/run_headless.sh:42-52`). `C:\src\run-conda-pymol.bat` lives OUTSIDE the repo and is the real, verified entry point (`setenv.bat`/`wsl2win_cp.sh` referenced in old spec text do NOT exist).
- **Consequence for code structure:** pure-Python modules must stay importable without pymol/PyQt5 (enforced by the AST gate `tools/check_imports.py`, which bans `pymol.*`/`PyQt5.*` imports in `rpg/` excluding `rpg/pymol_layer/` + `rpg/ui/`). PyMOL-touching modules receive `cmd` via **constructor injection** so they unit-test with MockCmd in WSL (pattern used by `rpg/pymol_layer/asset_manager.py`, `rpg/pymol_layer/molops.py`, `rpg/ui/bulk_download.py`).

**Package Manager:**
- None. No `setup.py`, no `pyproject.toml`, no `requirements.txt`, no lockfile, no conda recipe. Dependencies are constrained by policy (only what `pymol-open-source` ships) rather than declared. New deps require a written list + explicit user approval (spec.md §Constraints); approved extras get vendored under `./3rd_party_lib/` (git-ignored) — directory does not exist yet.

## Frameworks

**Core:**
- **PyMOL 2.5.0 plugin API** — host application. Plugin entry: `rpg/__init__.py.__init_plugin__` → `rpg/ui/plugin_entry.py` using the modern `pymol.plugins.addmenuitemqt` pattern (`plugin_entry.py:15-16`; cited to `plugins/__init__.py:100`). All molecular operations through `pymol.cmd` — never internals. Every `cmd.*` call in `rpg/pymol_layer/` carries a `# src: tmp/pymol-src/modules/pymol/<file>.py:<line>` citation comment pinned to PyMOL 2.5.0 line numbers.
- **PyQt5 via `pymol.Qt`** — GUI layer only (`rpg/ui/*.py`: `main_window.py`, `plugin_entry.py`, dialogs). Import form is exactly `from pymol.Qt import QtCore, QtGui, QtWidgets` (matching `Pymol-script-repo/plugins/dynoplot.py`). Legacy `pmgqt`/Tk is banned (REQUIREMENTS.md Out-of-Scope). Qt imports are deferred to click-time (`plugin_entry.py:19-27`) so plugin load never touches Qt before the GUI is ready.

**Testing:**
- **unittest (stdlib)** — `python3.6 -m unittest discover -s tests -v`. 599 tests, ~22s, all green (verified 2026-09-10). No pytest, no coverage tooling. Qt/GUI behavior is human-verified in a real Windows PyMOL session (cannot be automated from WSL).

**Build/Dev:**
- `tools/build_plugin_zip.sh` — packaging via python3.6 stdlib `shutil` + `zipfile` (the `zip`/`unzip` CLIs are absent in WSL and cannot be installed). Produces `dist/rpg-<version>.zip` with the Case-1 layout (`rpg/__init__.py` first entry; per `tmp/pymol-src/modules/pymol/plugins/installation.py:90-143`), bundling `data/story_glucose/` into `rpg/data/story_glucose/` and excluding `__pycache__`/`*.pyc`/`downloaded/`.
- `tools/story_editor.py` — generator that reads live repo data and inlines `tools/story_editor_assets/*.js` (sorted by filename) + `shell.html` into committed `story_editor.html`. Runs a structural sanity gate (duplicate ids, dangling `goto`, bad `manifest.start`) and exits nonzero without writing on violation.
- `tools/check_imports.py` — AST gate enforcing the pure-Python testability boundary.
- `tools/check_citations.py` — pre-ship gate blocking on any non-`approved` claim (data from `rpg/citations.py`).
- `tools/story_editor_lint.py`, `tools/check_edit_coverage.py`, `tools/check_alter_gate.py` — content/data lints.
- `tools/run_headless.sh` — the WSL→Windows headless PyMOL bridge (see Runtime).
- `tools/scene_capture.py` — read-only capture of a live PyMOL session into MolAction JSON (runs INSIDE PyMOL, emitted paste-ready for `on_enter` node ops).
- Canonical gate command (from `tools/check_imports.py` docstring): `python3.6 tools/check_imports.py && python3.6 -m unittest discover -s tests -v`

## Key Dependencies

**Critical:**
- **pymol-open-source 2.5.0** — the host app and entire molecular API surface. Vendored reference source at `tmp/pymol-src/` (symlink to PyMOL 2.5.0 modules; **read-only, gitignored reference, NOT project code**). Key modules for API verification: `modules/pymol/importing.py` (load/fetch), `creating.py`, `editing.py`, `querying.py`, `viewing.py`, `commanding.py`, `wizard/`, `plugins/` (installation + menu registration).
- **PyQt5** (shipped with pymol-open-source, accessed only via `pymol.Qt`) — all plugin UI.

**Infrastructure:**
- **numpy** — allowed by spec.md ("assume only what pymol-open-source ships"), but **currently imported by NO project code** (verified by grep across `rpg/` and `tools/`). Do not assume it is in use.
- **Python stdlib only, otherwise** — `json`, `os`, `sys`, `random`, `secrets`, `pathlib`, `ast`, `collections`, `datetime`, `re`, `html`, `shutil`, `zipfile`. No requests/urllib usage in project code (all network goes through `cmd.fetch`, see INTEGRATIONS.md).
- **`Pymol-script-repo/`** — symlink to 31 third-party single-file plugins (`plugins/dynoplot.py` etc.); **read-only, gitignored idiom reference**, never imported or shipped.

**Explicitly rejected / out of scope** (REQUIREMENTS.md Out-of-Scope table): RDKit or any chemistry engine (edit correctness is a lookup table + bad-ending fallback), OpenMM / molecular dynamics, web frameworks, File System Access API in the story editor (banned; download-based saves instead), legacy pmgqt/Tk.

## Configuration

**Environment variables:**
- None required at runtime by the plugin.
- Optional dev-install: `PYMOL_GIT_MOD=<repo-root>` (or Plugin Manager → Settings → Plugin Directories) makes PyMOL load `rpg/` straight from source with no zip rebuild — see `tools/build_plugin_zip.sh:25-36`.
- `APPDATA` presence selects the Windows user-data root in `rpg/paths.py:88-91` (`%APPDATA%/pymol/rpg-tale-of-c/` vs `~/.pymol/rpg-tale-of-c/`).

**Key config/data files (all JSON, all shipped or committed):**
- `data/story_glucose/manifest.json` — story manifest (file list, start node); story nodes in `glycolysis.json`, `tca.json`, `pyruvate_branch.json`, `etc_atp.json`, `endings.json`, `bad_endings.json`, `intro.json`.
- `data/citations.json` — claim registry (77 claims; `approval_status` ∈ pending/approved/rejected; 73 approved / 4 pending as of 2026-09-10).
- `data/sources.json` — source registry (LibreTexts chapters, PDB entries, DOIs) resolved by `source_id` from claims.
- `rpg/data/cast.json` — enzyme cast (id, label, pdb_id, character, claim_id, `source`: bundled|download).
- `rpg/data/edits.json` — edit-routing table (per-enzyme buckets, signatures, branch nodes, bad-ending pool).
- `rpg/data/help.json`, `rpg/data/selfcheck.json` — in-game help + package-layout self-check fixture.
- `rpg/paths.py` — the ONLY sanctioned path resolver: `data_path()` (`__file__`-relative, cwd-independent) and `user_data_path()` (user-writable, survives plugin reinstall).

**Build:**
- No build config files. Version lives in `rpg/__init__.py.__version__` ("0.0.1-dev") and is grepped out by `tools/build_plugin_zip.sh:56`.
- `.gitignore` — critical exclusions: `Pymol-script-repo`, `tmp/`, `3rd_party_lib/`, `rpg/data/assets/downloaded/` (runtime fetch cache), `dist/` (build output), `*.env`, `*.npy`/`*.npz`, `__pycache__/`, secrets. Bundled fixtures in `rpg/data/assets/bundled/` ARE committed and ship in the zip.

## Platform Requirements

**Development (WSL):**
- Ubuntu (WSL), `python3.6` = 3.6.9 on PATH. No installs. Windows access via `/mnt/c/...` paths (Windows PyMOL can read these; `\\wsl$` paths work but are flakier — `tools/run_headless.sh:22` uses `wslpath -w`).
- `opencode.json` — AI-agent permission config for this dev shell (deny `rm`/`rg`; ask for pip/apt/conda/python/mv/wget/curl; allow git except push/pull/merge/rebase/reset/checkout).

**Production (player machine):**
- Windows (primary verified target) with PyMOL 2.5.0 + PyQt5. Install via Plugin Manager (`dist/rpg-*.zip`) or plugin-directory dev mode. User data accumulates in `%APPDATA%/pymol/rpg-tale-of-c/`.
- Network required on first play for large PDB downloads (bulk-download prompt; offline fallback locks affected characters — see INTEGRATIONS.md).
- Linux/macOS PyMOL should work by construction (`user_data_path` handles both; Qt interface is cross-platform) but only Windows is human-verified.

## Dependency-Approval Workflow (non-negotiable)

Per spec.md §Constraints: to add any library beyond pymol-open-source's payload, (1) write the list to a file, (2) seek explicit user approval, (3) user installs it OR it gets vendored under `./3rd_party_lib/` (git-ignored, license noted), stating whether a Linux env is needed or the WSL-calls-cmd approach suffices. Never `pip install` silently.

---

*Stack analysis: 2026-09-10*
