# Codebase Structure

**Analysis Date:** 2026-09-10

## Directory Layout

```
RPG_tale-of-C/
├── AGENTS.md               # Agent environment rules (WSL/Windows split, verification)
├── README.md               # Repo readme (Under Development banner)
├── LICENSE, LICENSE_pymol-open-source
├── spec.md                 # AUTHORITATIVE spec (plot, constraints, citation rules)
├── opencode.json           # Agent permission config (denies rm*, rg*)
├── .gitignore
├── .planning/              # GSD planning area (NOT code) — see below
├── rpg/                    # THE PLUGIN PACKAGE (shipped code)
│   ├── __init__.py         # __init_plugin__ entry (PyMOL menu registration)
│   ├── paths.py            # __file__-relative path resolution + selfcheck
│   ├── engine.py           # GameEngine turn loop (290 lines)
│   ├── state.py            # GameState (the saveable unit)
│   ├── persist.py          # SaveStore (human-readable JSON saves)
│   ├── rng.py              # RngEngine (single seeded PRNG)
│   ├── edit_router.py      # EditRouter + EditsTable + coverage scan
│   ├── achievements.py     # AchievementBoard (collection, user-file persisted)
│   ├── citations.py        # CitationRegistry (approval gate data)
│   ├── protonation_catalog.py  # curated protonation variants (pure data)
│   ├── story/              # story engine domain
│   │   ├── model.py        # Node / Choice / MolAction / EditIntent (329 lines)
│   │   ├── graph.py        # StoryGraph bundle loader
│   │   ├── interpreter.py  # stateless walker (cond/weight/effects/on_enter)
│   │   └── validate.py     # graph validator + reachability BFS (323 lines)
│   ├── pymol_layer/        # cmd.* layer (AST-gate EXEMPT)
│   │   ├── molops.py       # MolAction → cmd.* per-action dispatch (300 lines)
│   │   ├── asset_manager.py    # bundled/fetch asset resolution
│   │   ├── edit_ops.py     # SOLE sanctioned cmd.alter path + backup/restore
│   │   └── protonation.py  # curated-variant dispatcher
│   ├── ui/                 # Qt layer (AST-gate EXEMPT)
│   │   ├── plugin_entry.py # menu registration + lazy window singleton
│   │   ├── main_window.py  # MainWindow + StartDialog (479 lines)
│   │   ├── controller.py   # Qt-free Controller mediator + HeroResolver (767 lines)
│   │   ├── widgets.py      # StoryPanel / ChoicePanel (402 lines)
│   │   ├── edit_dialog.py, save_load_dialogs.py, help_dialog.py,
│   │   ├── achievements_dialog.py, bulk_download.py, bulk_download_dialog.py
│   │   └── __init__.py
│   └── data/               # SHIPPED package data
│       ├── edits.json      # edit-routing lookup table (known-edit signatures)
│       ├── cast.json       # cast manifest (enzyme id → PDB id + claim)
│       ├── help.json, selfcheck.json
│       └── assets/
│           ├── bundled/    # committed PDB fixtures (ship in the zip)
│           └── downloaded/ # runtime fetch cache (gitignored)
├── data/                   # DEV data source of truth (copied into rpg/ at build)
│   ├── story_glucose/      # story bundle: manifest.json + 7 node files (57 nodes)
│   ├── story/              # older minimal story (intro.json only, Phase-2 artifact)
│   ├── citations.json      # claim registry (approval_status per claim)
│   ├── sources.json        # source registry (approved sources)
│   └── citations.README.md
├── tests/                  # 37+ test modules, 599 tests (pure WSL python3.6)
│   ├── fixtures/           # citations_*.json, story_pass.json, edit_routing/
│   └── test_*.py           # test_engine, test_controller, test_story_editor_*, ...
├── tools/                  # gates, smokes, editor, build, viewers
│   ├── check_imports.py    # AST testability gate
│   ├── check_alter_gate.py # AST cmd.alter allowlist gate
│   ├── check_citations.py  # no-fabricated-science gate
│   ├── check_edit_coverage.py
│   ├── story_editor_lint.py, story_editor_json.py  # house serializer + lint
│   ├── story_editor.py     # generates story_editor.html from assets
│   ├── story_editor_assets/  # 15 files: 00_core.js … 90_boot.js + shell.html
│   ├── story_graph_viewer.py   # read-only graph viewer generator
│   ├── build_plugin_zip.sh # dist zip build (Case-1 layout)
│   ├── run_headless.sh     # WSL→Windows PyMOL headless bridge
│   └── *_smoke.py, demo_playthrough.py, render_story_graph.py, …
├── story_editor.html       # GENERATED authoring tool (committed, 17169 lines)
├── dev/                    # dev-only generated artifacts (story_graph_viewer.html)
├── dist/                   # build output (gitignored; rpg-0.0.1-dev.zip present)
├── tmp/                    # gitignored scratch + pymol-src symlink
└── Pymol-script-repo -> ../bioCHEMeleon/Pymol-script-repo  # symlink, gitignored
```

## Directory Purposes

**`rpg/` (package root):**
- Purpose: domain tier — everything WSL-unit-testable. AST gate bans pymol/PyQt5 imports here (`tools/check_imports.py`, SKIP_DIRS excludes `pymol_layer/` + `ui/` only).
- Key files: `rpg/engine.py`, `rpg/state.py`, `rpg/edit_router.py`, `rpg/paths.py`.

**`rpg/story/`:**
- Purpose: story-graph domain model + walking + validation. All pure data + stdlib.
- Key files: `rpg/story/model.py` (MolAction/EditIntent are the boundary carriers), `rpg/story/interpreter.py`, `rpg/story/validate.py`.

**`rpg/pymol_layer/`:**
- Purpose: the ONLY place `cmd.*` is translated. `cmd` is constructor-injected in every module (MockCmd-testable); real API verified by headless smokes.
- Key files: `rpg/pymol_layer/molops.py`, `rpg/pymol_layer/edit_ops.py` (the repo's sole `cmd.alter` allowlist entry).

**`rpg/ui/`:**
- Purpose: Qt UI as a thin adapter. `main_window.py` never calls molecular `cmd.*` directly (only injected `count_fn`/view callbacks + `QMessageBox` prompt).
- Key files: `rpg/ui/controller.py` (Qt-free — importable in WSL; the mediator), `rpg/ui/plugin_entry.py` (entry).

**`data/`:**
- Purpose: dev-time source of truth for story + citation registries. `tools/build_plugin_zip.sh` copies `data/story_glucose/` into `rpg/data/story_glucose/` at zip-build time.
- Key files: `data/story_glucose/manifest.json` (start node + file list), `data/citations.json`.

**`rpg/data/`:**
- Purpose: shipped package data resolved via `rpg.paths.data_path()`. `assets/bundled/` is committed; `assets/downloaded/` is the gitignored runtime fetch cache.

**`tools/`:**
- Purpose: architecture gates (must stay green), headless smokes, the story editor, build scripts. Not shipped.
- Key files: `tools/check_imports.py`, `tools/check_citations.py`, `tools/story_editor.py` + `tools/story_editor_assets/`.

**`tests/`:**
- Purpose: pure-WSL unittest suite (599 tests) + `tests/fixtures/` for gate/router fixtures.

**`.planning/` (project-planning area, NOT code):**
- Purpose: GSD workflow docs — `PROJECT.md` (requirements + Key Decisions incl. soul-jump reframing), `ROADMAP.md` (17-phase build order), `STATE.md` (progress log; phases 1–6 COMPLETE, Phase 7 18/19 + Phase 7.1 17/19 done), `phases/` (per-phase PLAN/SUMMARY/RESEARCH docs), `research/` (PITFALLS.md etc.), `codebase/` (these docs), `quick/`, `debug/`.

## Key File Locations

**Entry Points:**
- `rpg/__init__.py`: `__init_plugin__(pmgapp)` — PyMOL plugin load; selfcheck + lazy delegate.
- `rpg/ui/plugin_entry.py`: menu registration + window singleton.
- `rpg/ui/main_window.py:MainWindow`: the game window (constructs molops stack + Controller).

**Configuration:**
- `data/story_glucose/manifest.json`: story bundle manifest (version, default_seed, start, files).
- `rpg/data/edits.json`: edit-routing table (bad_ending_pool + per-enzyme signatures).
- `rpg/data/cast.json`: cast manifest (enzyme → PDB id, claim_id).
- `data/citations.json` / `data/sources.json`: citation approval registries.
- `tools/check_imports.py`: the testability-boundary config (BANNED_TOP, SKIP_DIRS).

**Core Logic:**
- `rpg/engine.py`: turn loop + save/load replay.
- `rpg/story/interpreter.py`: cond evaluation, weighted RNG picks, effects, on_enter emission.
- `rpg/edit_router.py`: known/unknown edit routing.
- `rpg/pymol_layer/molops.py`: MolAction→cmd.* dispatch.
- `rpg/pymol_layer/edit_ops.py`: sanctioned alter + backup/restore.

**Testing:**
- `tests/test_*.py` (co-located fixtures in `tests/fixtures/`); run `python3.6 -m unittest discover -s tests -v`.
- Headless PyMOL smokes: `tools/*_smoke.py` via `bash tools/run_headless.sh`.

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (`edit_router.py`, `asset_manager.py`).
- Tests: `test_<module>.py` mirroring the module name (`test_engine.py`, `test_edit_router.py`).
- Tools: verbs — `check_*.py` (gates), `*_smoke.py` (headless verification), `*_probe.py`, `render_*.py`.
- Story-editor JS assets: numeric prefix = inline order (`00_core.js`, `05_json.js`, `10_load.js`, `20_validate.js`, `30_graph.js`, `40_form.js`, `42_choices.js`, `43_onenter.js`, `45_lifecycle.js`, `50_editscast.js`, `60_trace.js`, `70_claims.js`, `80_save.js`, `90_boot.js`).

**Identifiers:**
- Node ids: dot-namespaced `<path>.<name>` (`intro.preface`, `gly.pfk`, `tca.shuffle`, `bad.lost_connection`, `gly.pfk_restored`).
- Enzyme/cast ids: same dot convention (`tca.aconitase`, `etc.complex_i`).
- Claim ids: `<PREFIX>-<NAME>-NN` (`GLY-PFK-01`, `TCA-RNG-WEIGHT-01`, `DIS-PFKM-01-cand` — `-cand` suffix = pending approval).

**Data conventions:**
- Optional JSON fields are ABSENT, never null (`is_ending`, `cond`, `weight`).
- House-style serializer (`tools/story_editor_json.py`, width 175/sub 110) — the story editor's `EDITOR.housy.stringify` is a 1:1 JS port.
- Every direct `cmd.*` call cites `# src: tmp/pymol-src/...:<line>` directly above.

## Where to Add New Code

**New story content (nodes/choices/endings):**
- Primary data: `data/story_glucose/<file>.json` (register new files in `manifest.json` `files`).
- Preferred path: the story editor (`story_editor.html` → download per-file → save over the repo file), or hand-edit then run gates.
- MUST then pass: `python3.6 tools/story_editor_lint.py`, `python3.6 -m unittest discover -s tests` (reachability/content pins: node/ending/edit-allowed counts are pinned in `tests/test_glucose_reachability.py` + `tests/test_glucose_content.py` — update the pinned counts in the SAME commit), `python3.6 tools/check_citations.py --story --registry`, `python3.6 tools/check_edit_coverage.py`.
- New claims: add to `data/citations.json` with `approval_status: "approved"` ONLY after human approval (spec.md non-negotiable).

**New MolAction op:**
- Dispatch: `rpg/pymol_layer/molops.py` `apply()` (with `# src:` citation on each direct cmd call).
- Tests: `tests/test_molops.py` (MockCmd dispatch mapping) + a `tools/<name>_smoke.py` headless proof.
- Also update: the story editor op vocabulary in `tools/story_editor_assets/43_onenter.js` (OP_VOCAB) and the viewer summary in `tools/story_graph_viewer.py`.

**New molecular operation (alter-family):**
- Implementation: `rpg/pymol_layer/edit_ops.py` ONLY — `cmd.alter` is AST-gated to this single file (`tools/check_alter_gate.py`).
- Tests: `tests/test_edit_ops.py` + headless smoke.

**New domain module (pure logic):**
- Location: `rpg/` root or `rpg/story/`. Must pass `python3.6 tools/check_imports.py` (no pymol/PyQt5), use `.format()` not f-strings, plain classes not `@dataclass`.
- Tests: `tests/test_<module>.py`.

**New Qt dialog/panel:**
- Implementation: `rpg/ui/` (gate-exempt). Wire from `rpg/ui/main_window.py` via DEFERRED import inside the handler (parallel-development convention).
- Controller logic goes in `rpg/ui/controller.py` and MUST stay Qt-free (imports only `rpg.*` + stdlib) — `python3.6 -c "import rpg.ui.controller"` must succeed in WSL.
- Qt behavior is human-verify only (WSL cannot run Qt).

**New gate/check:**
- Location: `tools/check_<topic>.py`; wire into the canonical gate command sequence (see `tools/check_imports.py` docstring).

**New story-editor capability:**
- Implementation: a new `tools/story_editor_assets/NN_<name>.js` ES5 IIFE (numeric prefix = inline order; register `EDITOR.view(...)` + `EDITOR.init` per `00_core.js` convention; own DOM mount; `data-<xx>-*` attribute namespacing).
- Regenerate: `python3.6 tools/story_editor.py` (rebuilds committed `story_editor.html`).
- Tests: structural battery `tests/test_story_editor_<topic>.py` (Python 3.6 stdlib greps — no JS runtime in WSL).

**New bundled asset:**
- Location: `rpg/data/assets/bundled/` (committed, ships in zip). Fetched structures land in `rpg/data/assets/downloaded/` (gitignored) via `AssetManager`.

**Utilities:**
- Shared path helpers: `rpg/paths.py` (`data_path`, `user_data_path` — never compute paths elsewhere).
- Shared pure-data catalogs: module-level in `rpg/protonation_catalog.py` style.

## Special Directories

**`tmp/`:**
- Purpose: scratch + `tmp/pymol-src/` symlink (READ-ONLY PyMOL 2.5.0 source for API citation verification — `modules/pymol/creating.py`, `editing.py`, `querying.py`, `viewing.py`, `commanding.py`, `wizard/`).
- Generated: mixed. Committed: NO (gitignored). Never commit; also `tmp/opencode-*` scratch lives here.

**`Pymol-script-repo/` (symlink → `../bioCHEMeleon/Pymol-script-repo`):**
- Purpose: READ-ONLY reference — 31 idiomatic single-file PyMOL plugins in `plugins/` (e.g. `plugins/dynoplot.py` for the modern `pymol.Qt` style). Not project code.
- Committed: NO (gitignored symlink).

**`rpg/data/assets/downloaded/`:**
- Purpose: runtime cache for `cmd.fetch`-downloaded structures (PDB/PubChem).
- Generated: Yes (at runtime). Committed: NO (gitignored).

**`dist/`:**
- Purpose: build output of `tools/build_plugin_zip.sh`.
- Generated: Yes. Committed: NO (gitignored; a stale `rpg-0.0.1-dev.zip` is present locally).

**`dev/`:**
- Purpose: dev-only generated artifacts (read-only story-graph viewer HTML). Regenerate via `python3.6 tools/story_graph_viewer.py`. Not shipped to players.

**`story_editor.html` (repo root):**
- Purpose: GENERATED, COMMITTED authoring tool — the single generated artifact in the repo root. Regenerate after ANY change to `tools/story_editor_assets/` (auto-inlines every `*.js` in numeric order between core and the bootstrap).

**`rpg/__pycache__/` (and all `__pycache__/`):**
- Generated: Yes. Committed: NO.

---

*Structure analysis: 2026-09-10*
