# Architecture

**Analysis Date:** 2026-09-10

## Pattern Overview

**Overall:** Layered plugin architecture with a strict testability boundary, driven by a data-defined story graph. PyMOL 2.5.0 plugin (PyQt5 via `pymol.Qt`) where the game is DATA (story JSON) walked by a pure-Python engine, and PyMOL `cmd.*` access is quarantined behind an injected-dispatch molecular layer.

**Key Characteristics:**
- **Testability boundary enforced by an AST gate** (`tools/check_imports.py`): files under `rpg/` root (domain tier) MUST NOT import `pymol` or `PyQt5`. Only `rpg/pymol_layer/` and `rpg/ui/` are gate-exempt (`SKIP_DIRS = {"pymol_layer", "ui", "__pycache__"}`). All game logic is unit-testable in WSL `python3.6` with no PyMOL installed.
- **Dependency injection at every layer seam:** `cmd`, `AssetManager`, `EditOps`, `ProtonationManager`, `molaction_sink`, `view_provider`/`view_applier`, `prompt_fn`/`count_fn` are all constructor-injected, so each layer is testable with mocks and the real PyMOL behavior is verified by headless smokes (`tools/*_smoke.py` via `tools/run_headless.sh` → Windows `run-conda-pymol.bat -cq`).
- **MolAction = pure-data carrier:** the story emits `MolAction(op, target, args)` dicts (`rpg/story/model.py:26`), never `cmd.*` calls. `rpg/pymol_layer/molops.py` is the sole translator to `cmd.*`.
- **The scene is a pure function of game state** (Anti-Pattern 5 avoidance): saves are human-readable JSON of `GameState` + RNG state; load rebuilds the scene by REPLAYING the current node's `on_enter` MolActions — no `.pse` session is saved (`rpg/persist.py`, `rpg/engine.py:262-284`).
- **Single seeded RNG:** all stochastic draws (weighted choices, bad-ending pool pick) go through one `RngEngine` (`rpg/rng.py`); the raw `random` module is banned (Anti-Pattern 7). Seed + PRNG state persist in saves for reproducibility/teaching.
- **No-fabricated-science gate:** every story node's `claim_ids` must resolve to `approval_status == "approved"` entries in `data/citations.json` (`rpg/citations.py:100-109` strict predicate; enforced by `tools/check_citations.py`).
- **Python 3.6 constraint everywhere:** plain classes (no `@dataclass`), `.format()` strings (no f-strings), stdlib only.

## Layers

**Domain tier (pure Python, AST-gated):**
- Purpose: game rules, story walking, routing, persistence, achievements, citations — zero PyMOL/Qt.
- Location: `rpg/` root + `rpg/story/`
- Contains: `rpg/engine.py` (GameEngine turn loop), `rpg/state.py` (GameState), `rpg/persist.py` (SaveStore), `rpg/rng.py` (RngEngine), `rpg/edit_router.py` (EditRouter/EditsTable), `rpg/achievements.py` (AchievementBoard), `rpg/citations.py` (CitationRegistry), `rpg/protonation_catalog.py` (pure-data variants), `rpg/paths.py` (`__file__`-relative path resolution), `rpg/story/model.py` (Node/Choice/MolAction/EditIntent), `rpg/story/graph.py` (bundle loader), `rpg/story/interpreter.py` (stateless walker), `rpg/story/validate.py` (graph validator + reachability BFS).
- Depends on: stdlib only.
- Used by: pymol_layer, ui, tests.

**Molecular layer (gate-exempt, cmd injected):**
- Purpose: translate MolActions into `cmd.*` calls; own every molecular mutation.
- Location: `rpg/pymol_layer/`
- Contains: `molops.py` (per-action dispatch: load/hide_all/show/show_as/select_focus/zoom/color/delete/set_color/label/set/align/edit/protonate/restore), `asset_manager.py` (bundled/fetched asset resolution; forces `type=`/`async_=0`/`path=` on every `cmd.fetch`), `edit_ops.py` (the SOLE sanctioned `cmd.alter` path in the repo — always `cmd.sort` + `cmd.rebuild`; backup via default-args `cmd.create`; restore = `cmd.delete` then `cmd.create`), `protonation.py` (curated-variant dispatcher; delegates all alter/h_add to EditOps).
- Depends on: injected `cmd` + each other; `rpg.story.model.MolAction` (pure data).
- Used by: `rpg/ui/controller.py`, headless smokes in `tools/`.

**Qt UI tier (gate-exempt, thin adapter):**
- Purpose: render TurnResults, capture player input. NEVER calls `cmd.*` for molecular ops directly.
- Location: `rpg/ui/`
- Contains: `plugin_entry.py` (menu registration, lazy window singleton), `main_window.py` (constructs the molops stack + Controller; wires toolbar/dialogs with DEFERRED imports), `controller.py` (Qt-free mediator: wires events → engine → MolOps dispatch; HeroResolver OQ-6 gate), `widgets.py` (StoryPanel/ChoicePanel), `edit_dialog.py`, `save_load_dialogs.py`, `achievements_dialog.py`, `help_dialog.py`, `bulk_download.py`/`bulk_download_dialog.py` (one-time PDB pre-download).
- Depends on: `rpg.engine`, `rpg.story.*`, `rpg.pymol_layer.*`, `pymol.Qt`.
- Used by: PyMOL plugin host only. Importing `rpg.ui.main_window` in WSL fails (no Qt) — expected; only `py_compile` is WSL-verifiable.

**Content/data tier (JSON, no code):**
- Purpose: the story graph, citation registries, cast/edit lookup tables, bundled molecular assets.
- Location: `data/story_glucose/` (story bundle: `manifest.json` + `intro.json`, `glycolysis.json`, `pyruvate_branch.json`, `tca.json`, `etc_atp.json`, `endings.json`, `bad_endings.json` — 57 nodes), `data/citations.json` + `data/sources.json` (claim/source approval registries), `rpg/data/` (`edits.json` edit-routing table, `cast.json` cast manifest, `help.json`, `selfcheck.json`, `assets/bundled/` committed fixtures, `assets/downloaded/` gitignored runtime fetch cache).
- Consumed by: `StoryGraph.load` / `CitationRegistry` / `EditsTable` / `AssetManager` (all CWD-independent via `rpg/paths.py`).

**Story Editor (offline authoring tool, committed but NOT runtime):**
- Purpose: no-API browser editor for story/citation/cast data (Phase 7.1).
- Location: `tools/story_editor.py` (Python generator, `tools/story_editor_assets/*.js` — 14 ES5 IIFE assets inlined in numeric order into the generated `story_editor.html` at repo root). Registry: `window.EDITOR` core in `tools/story_editor_assets/00_core.js`; parity assets port the Python gates (`20_validate.js` mirrors `rpg/story/validate.py` + `tools/story_editor_lint.py`; `05_json.js` mirrors the house serializer in `tools/story_editor_json.py`).

**Tooling/gates tier:**
- Purpose: enforce architecture invariants pre-ship.
- Location: `tools/`
- Contains: `check_imports.py` (AST testability gate), `check_alter_gate.py` (AST: `cmd.alter` only in `rpg/pymol_layer/edit_ops.py`), `check_citations.py` (approval gate), `check_edit_coverage.py` (every cast enzyme has ≥1 known edit), `story_editor_lint.py` (story-graph lint), `build_plugin_zip.sh` (Plugin-Manager-installable zip; `rpg/__init__.py` first entry, bundles story), `run_headless.sh` (WSL→Windows PyMOL bridge), plus `*_smoke.py` headless verification scripts.

## Data Flow

**Playthrough turn (the core loop):**

1. Player clicks a choice button in `rpg/ui/widgets.py` → `MainWindow` calls ONE `Controller` method (`start_game` / `choose` / `take_choice` / `request_edit` / `apply_edit` — `rpg/ui/controller.py:204+`).
2. Controller calls the matching `GameEngine` method (`rpg/engine.py`: `choose()` resolves via `StoryInterpreter.pick_choice` — cond filter, then RNG-weighted pick or player index selection).
3. Interpreter applies choice effects to `GameState`, and `_enter()` (`rpg/engine.py:211`) sets `current_node`, emits the node's `on_enter` MolActions one-by-one to the injected `molaction_sink` (`Controller._dispatch_molaction`, `rpg/ui/controller.py:319`), records the visit, syncs `state.rng_state`, detects endings.
4. Controller's `_dispatch_molaction` runs `HeroResolver.resolve` (OQ-6 multi-carbon warn+confirm gate) then forwards each action to `MolOps.apply(action)` (`rpg/pymol_layer/molops.py`) wrapped in defensive try/except — a failed load (offline fetch) logs and continues rather than crashing the game.
5. `MolOps` dispatches: `load` → `AssetManager`, `edit`/`restore` → `EditOps`, `protonate` → `ProtonationManager`, everything else → direct injected `cmd.*` calls.
6. Controller updates `AchievementBoard.on_turn(...)` and calls back `view.render_turn(turn)` → `MainWindow` re-renders story text/choices; ending nodes with `edit.prompt` id open `EditDialog` (the edit-prompt seam, `rpg/ui/main_window.py:24-31`).
7. Player edits flow the reverse way: `EditDialog` builds an `EditIntent` → `Controller.build_edit_intent` → `GameEngine.apply_player_edit` → `EditRouter.route` (exact normalized-signature match against `rpg/data/edits.json`; known → `branch_node`, unknown → bad-ending pool via seeded RNG) → routed node entered as a normal turn; the actual molecular mutation happens later as the routed branch's `on_enter` MolAction("edit", …).

**State Management:**
- `GameState` (`rpg/state.py`) is the single saveable unit: current node, character, flags, counters, visit counts, edit history, seed + serialized RNG state, protonation pref, captured view (18 floats), ending.
- `RngEngine` is rebuilt from `(seed, rng_state)` on load (`rpg/engine.py:274`); the live PRNG position is synced into state after every node entry so a save anywhere is reproducible.
- Scene reconstruction on load = replay current node's `on_enter` with `record_visit=False`, then apply the saved view AFTER the replay so the saved camera wins over any node `zoom` (`rpg/engine.py:262-284`).

**Save/Load:** `SaveStore` (`rpg/persist.py`) — human-readable `indent=2` JSON; parent dirs auto-created; load errors (malformed JSON, missing file) propagate to the caller.

## Key Abstractions

**MolAction:**
- Purpose: pure-data molecular intent (op/target/args) crossing the domain→pymol_layer boundary.
- Example: `rpg/story/model.py:26-79`; dispatched in `rpg/pymol_layer/molops.py`.
- Pattern: data-carrier + per-action dispatch table; unknown ops raise `NotImplementedError` (fail loud).

**Node / Choice (story graph):**
- Purpose: declarative story content; `choices` are the graph edges (`goto`), with optional `cond` (state expression: `flags.get('x')` / `visits.get('x', 0)`), `weight` (RNG), `effects` (set/incr), `tags`, `claim_ids`, `is_ending` tier (`true|good|normal|bad`), `on_enter` MolAction list.
- Example: `rpg/story/model.py` (Node/Choice with `from_dict`/`to_dict`), data in `data/story_glucose/*.json`.
- Pattern: ink-inspired walker (`StoryInterpreter` is stateless; state passed in); optional fields are ABSENT, never null.

**EditIntent + EditRouter:**
- Purpose: routing carrier (op/target/args/enzyme_id) and the lookup-table router — known signature → defined branch, unknown → bad-ending pool.
- Example: `rpg/story/model.py:82+` (`signature()` normalization), `rpg/edit_router.py` (`EditsTable`, `EditRouter`, `validate_edits_table`, `scan_edit_coverage`).
- Pattern: exact dict equality on a normalized signature — zero fuzzy/chemistry logic (out of scope per PROJECT.md).

**EditOps (sole sanctioned alter path):**
- Purpose: mitigate the `alter`→`sort` silent-corruption trap (PyMOL `editing.py:1457-1460`).
- Example: `rpg/pymol_layer/edit_ops.py`; enforced repo-wide by the `tools/check_alter_gate.py` AST allowlist.
- Pattern: backup via default-args `cmd.create` (all states) → alter → `cmd.sort` + `cmd.rebuild`; restore = `cmd.delete` + `cmd.create` from backup.

**RngEngine:**
- Purpose: the only source of randomness; seedable, serializable state, reproducible demos.
- Example: `rpg/rng.py` (`get_state`/`from_state`).

**CitationRegistry / claim gate:**
- Purpose: no fabricated science — story nodes reference `claim_ids`; gate fails unless every claim is `approved`.
- Example: `rpg/citations.py` (strict `approval_status == "approved"`), `data/citations.json` + `data/sources.json`, `tools/check_citations.py`.

## Entry Points

**PyMOL plugin load:**
- Location: `rpg/__init__.py` → `__init_plugin__(pmgapp)` (called by `pymol.plugins.PluginInfo.legacyinit`).
- Responsibilities: run `rpg.paths.selfcheck()` (fail loud if bundled data layout broken), then lazy-delegate to `rpg/ui/plugin_entry.py:init_plugin` (registers `addmenuitemqt('RPG: Tale of C', _open_main_window)`; Qt imported only at click time — `rpg/ui/plugin_entry.py:12-27`).

**Main window (menu click):**
- Location: `rpg/ui/main_window.py:MainWindow` (lazy singleton in `rpg/ui/plugin_entry.py:19-27`).
- Responsibilities: construct molops stack (real `cmd` + AssetManager + EditOps + ProtonationManager + MolOps + EditRouter + AchievementBoard) + Controller; resolve story dir (shipped `rpg/data/story_glucose` first, dev fallback `data/story_glucose`, `rpg/ui/main_window.py:74-90`); render turns.

**Verification harnesses (dev entry points):**
- `python3.6 tools/check_imports.py` — AST testability gate.
- `python3.6 tools/check_citations.py --story --registry` — citation gate.
- `python3.6 -m unittest discover -s tests -v` — 599-test suite (WSL, pure Python).
- `bash tools/run_headless.sh <script>` — headless PyMOL smoke via Windows bridge (grep `SMOKE_RESULT: PASS` sentinel; the bat always returns 0, so the sentinel is authoritative).
- `python3.6 tools/story_editor.py` — regenerates `story_editor.html` from `tools/story_editor_assets/`.
- `bash tools/build_plugin_zip.sh` — builds `dist/rpg-<version>.zip`.

## Error Handling

**Strategy:** fail loud at the gates (authoring/load time), degrade gracefully at runtime (UI dispatch time).

**Patterns:**
- **Fail loud on plugin load:** `rpg/paths.py:selfcheck()` raises `FileNotFoundError` if bundled data is missing (`rpg/__init__.py:27-28`).
- **Fail loud on unknown ops:** `MolOps.apply` raises `NotImplementedError` for unknown MolAction ops (`rpg/pymol_layer/molops.py`); `EditRouter` raises `EditRoutingError` on empty bad-ending pool; `StoryGraph` raises `ValueError` on duplicate node ids.
- **Degrade at runtime:** `Controller._dispatch_molaction` wraps each MolOps forward in try/except — a failed load (offline fetch) logs and continues to the next on_enter action (`rpg/ui/controller.py:40-46`).
- **Failure-tolerant view capture/restore:** save does not block if `cmd.get_view()` raises; load does not block if `cmd.set_view` fails (`rpg/engine.py:254-260, 279-283`).
- **Validator/lint surface:** `rpg/story/validate.py` + `tools/check_edit_coverage.py` + `tools/story_editor_lint.py` catch dangling diverts, unreachable endings, router-only incoming, empty pools, duplicate signatures at authoring time (mirrored client-side in `tools/story_editor_assets/20_validate.js`).

## Cross-Cutting Concerns

**Logging:** no logging framework — `sys.stderr` prints in controller degrade paths; verification is test/gate/smoke-based, not log-based.

**Validation:** three enforcement layers — AST gates (`tools/check_imports.py`, `tools/check_alter_gate.py`), data gates (`tools/check_citations.py`, `check_edit_coverage.py`, `rpg/story/validate.py`, `story_editor_lint.py`), and the unittest suite (`tests/`, 599 tests, pure-WSL).

**Authentication:** none (desktop plugin, no network auth). Network access is limited to PDB/PubChem fetches via `cmd.fetch` with explicit `type=`/`async_=0`/absolute `path=` (`rpg/pymol_layer/asset_manager.py`).

**Source-citation convention:** every direct `cmd.*` call carries `# src: tmp/pymol-src/modules/pymol/<file>.py:<line> cmd.<name>` directly above it (established Phase 3; pinned to PyMOL 2.5.0).

**Path resolution:** all bundled-data lookups go through `rpg/paths.py:data_path()` (`__file__`-relative, never `os.getcwd()`); user-writable data (saves, achievements) through `user_data_path()` → `~/.pymol/rpg-tale-of-c/` or `%APPDATA%/pymol/rpg-tale-of-c/` (survives plugin reinstall).

---

*Architecture analysis: 2026-09-10*
