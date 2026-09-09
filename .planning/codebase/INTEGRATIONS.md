# External Integrations

**Analysis Date:** 2026-09-10

## APIs & External Services

**Structural data downloads (the only runtime network usage):**

All network access is delegated to PyMOL's own downloader — `cmd.fetch` inside PyMOL 2.5.0. Project code contains **zero direct HTTP calls** (verified: no `urllib`/`requests`/`urlopen` anywhere in `rpg/` or `tools/`; the only URL strings in the repo are inside the gitignored PyMOL reference source and one probe comment).

- **RCSB PDB** — protein structures (the enzyme "cast").
  - Client: `rpg/pymol_layer/asset_manager.py:fetch_pdb(code, object_name)` → `self._cmd.fetch(str(code), object_name, type="pdb", async_=0, path=<abs downloaded dir>)` (`asset_manager.py:114-126`).
  - Upstream URL (PyMOL internal, `tmp/pymol-src/modules/pymol/importing.py:1124`): `https://files.rcsb.org/download/{code}.{type}.gz`
  - Auth: none (public). No API key.
  - Pitfall mitigations baked in: `type=` explicit (cmd.fetch defaults to CIF), `async_=0` sync, `path=` absolute dir (default is cwd). Post-condition: `count_atoms(...) <= 0` → `RuntimeError`.
- **PubChem** — small-molecule 3D models (the hero/intermediates as SDF).
  - Client: `rpg/pymol_layer/asset_manager.py:fetch_pubchem(cid, object_name, kind="cid")` (`asset_manager.py:97-112`), `kind` ∈ `"cid"`/`"sid"`.
  - Upstream URL (PyMOL internal, `importing.py:1139`): `https://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?{type}={code}&disopt=3DSaveSDF`
  - Auth: none (public).
  - Offline behavior: raises `RuntimeError("fetch_pubchem: cid {0} produced no atoms (offline?)")` — callers treat this as an expected failure mode.
- **Bulk download of large PDBs** (one-time prompt before first play):
  - `rpg/ui/bulk_download.py` — Qt-free runner: `missing_large_pdbs(cmd)` diffs expected codes (from `rpg/data/cast.json`) against the local cache; `run_bulk_download(...)` loops `AssetManager.fetch_pdb` once per code with `on_progress`/`on_cancel_check` callbacks. Per-file progress via `QApplication.processEvents()` BETWEEN fetches (`cmd.fetch` is sync/blocking with no per-byte callback — `bulk_download.py:9-14`).
  - `cmd.fetch` skips already-downloaded files (`importing.py:1211-1213`), so retry is an idempotent cache refill.
  - Offline fallback: `characters_to_lock(failed, cast_path)` returns the set of character ids to lock on character-select (computed from failed downloads; `bulk_download.py:61-64`). The QDialog wrapper is `rpg/ui/bulk_download_dialog.py`.
  - Current content caveat: `rpg/data/cast.json` download-enzyme PDB IDs are real and approved (4PFK, 7FS3, 6CFO, 1ACO, 1OCC, 1BGY, 5GRE/5GRF, 1ZOY, 4WLU, 3CSC/1CSC etc.); the bundled small set ships in `rpg/data/assets/bundled/` and the rest download on first play.

**Reference-only (no runtime calls):**
- **UniProt REST** — `tools/aconitase_mapping_probe.py:86-89` embeds a human ACO2 FASTA (Q99798) that was fetched once from `https://rest.uniprot.org/uniprotkb/Q99798.fasta` (2026-09-03) and pasted into the probe as a literal. No runtime dependency; do not add one without the dependency-approval workflow.
- **Biochemistry LibreTexts / textbooks** — citation sources only, resolved from `data/sources.json` (`source_id` → url/license/approval metadata). Never fetched at runtime.

## Data Storage

**Databases:**
- None. No SQL, no embedded DB, no server. All persistence is **JSON files via the Python stdlib `json` module**.

**File Storage (local filesystem only):**
- **Shipped/committed data** (inside the package, resolved via `rpg/paths.py:data_path()`):
  - Story content: `data/story_glucose/*.json` (repo) → `rpg/data/story_glucose/` (bundled into the zip by `tools/build_plugin_zip.sh:101-103`).
  - Registries: `data/citations.json`, `data/sources.json`, `rpg/data/cast.json`, `rpg/data/edits.json`, `rpg/data/help.json`, `rpg/data/selfcheck.json`.
  - Bundled structures: `rpg/data/assets/bundled/*.pdb` (committed; small/critical fixtures incl. smoke PDBs and the wt/mut align pair `_wt_align_*.pdb`).
- **Runtime download cache** (regenerable, gitignored): `rpg/data/assets/downloaded/` — created on demand by `AssetManager._download_dir()` (`asset_manager.py:66-77`), explicitly passed as `cmd.fetch path=` so downloads never land in cwd. Currently holds fetched PDBs (1aco, 1bgy, 1occ, 4pfk, ...) and one PubChem SDF (`cid_2244.sdf`).
- **User data** (survives PyMOL restarts AND plugin reinstalls; resolved via `rpg/paths.py:user_data_path()`, `paths.py:68-92`):
  - Linux/Mac: `~/.pymol/rpg-tale-of-c/`
  - Windows: `%APPDATA%/pymol/rpg-tale-of-c/`
  - Contains e.g. `achievements.json` (achievement board persistence, ACH-02). Sits BESIDE the plugin install dir so a delete+re-unzip of `startup/` never wipes it.
- **Game saves:** arbitrary user-chosen path via `rpg/persist.py:SaveStore` — human-readable JSON (`indent=2`, trailing newline, parents auto-created). NOT a `.pse` PyMOL session; on load the engine replays the current node's `on_enter` MolActions to rebuild the molecular scene (scene = pure function of game state; `persist.py:1-22`).

**Caching:**
- Structure cache: the `downloaded/` dir + PyMOL's fetch skip-if-exists behavior (described above). No other caching layer.

## JSON Integrity Conventions (project-specific)

- `rpg/citations.py:29-46` — duplicate-key rejection via `json.load(..., object_pairs_hook=_no_duplicate_keys)`; a duplicated `claim_id` raises `ValueError` instead of silently last-winning. Apply the same hook when loading any registry where duplicates are dangerous.
- Approval predicate is strict equality `approval_status == "approved"` — NEVER `!= "pending"` (rejected claims must fail too; `rpg/citations.py:58-61`, `:100-109`).
- Save format: keys absent, never null (`is_ending` removal deletes the key; `rpg/story/model.py:250-252` precedent) — match this when writing new serializers.

## Authentication & Identity

**Auth Provider:** None. No user accounts, no login, no API keys, no tokens, no OAuth. All upstream services (RCSB, PubChem) are anonymous public endpoints. `*.env`/`**/secrets.toml`/`**/auth.json` are gitignored purely as precaution — no secrets exist in this repo.

## Monitoring & Observability

**Error Tracking:** None (no Sentry/rollbar/etc.).

**Logs:**
- Dev tools print to stdout with sentinel conventions: headless smokes print `SMOKE_RESULT: PASS` / `FAIL` (the verdict mechanism for `tools/run_headless.sh`, since the .bat always exits 0); gates (`check_imports.py`, `check_citations.py`, `story_editor_lint.py`) exit nonzero on violation; the story-editor generator prints `EDITOR_FAIL: ...` and exits 1 without writing.
- Runtime (plugin): errors surface as Qt dialogs (`QtWidgets.QMessageBox.warning/question` in `rpg/ui/main_window.py`, `rpg/ui/plugin_entry.py`) and `RuntimeError` raises from the pymol_layer post-conditions. There is no logging framework — do not introduce one without approval.

## CI/CD & Deployment

**Hosting:** Desktop application plugin — no server, no hosting.

**CI Pipeline:** None. No `.github/`, no `.gitlab-ci.yml`, no CI config in the repo. Verification is a documented command ladder run by agents/humans:
1. `python3.6 -m py_compile <file>` — syntax (pure-Python modules)
2. `python3.6 tools/check_imports.py` — purity gate (no pymol/PyQt5 in domain tier)
3. `python3.6 -m unittest discover -s tests -v` — 599 tests
4. `python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json` — no-fabricated-science gate
5. `bash tools/run_headless.sh <smoke>.py` — headless PyMOL cmd-layer smokes (Windows bridge)
6. Human-verify in a real Windows PyMOL session — anything touching `pymol.Qt` at runtime (GUI/prompt flows) cannot be automated from WSL.

**Distribution:** `dist/rpg-<version>.zip` (built by `tools/build_plugin_zip.sh`), installed via PyMOL → Plugin → Plugin Manager → Install New Plugin. Dev installs skip the zip via `PYMOL_GIT_MOD`/plugin-directories.

**Dev-tool distribution:** `story_editor.html` (committed at repo root) is opened directly in Firefox from the repo root — it auto-loads `data/story_glucose/`, `data/citations.json`, `data/sources.json`, `rpg/data/edits.json`, `rpg/data/cast.json` as same-directory-or-below `file://` XHR reads (Firefox blocks `fetch()` on `file://` — CVE-2019-11730 — hence XHR; the editor is explicitly zero-server, zero-network, no File System Access API). Output must stay at repo root so those relative reads resolve.

## Environment Configuration

**Required env vars:** None for the plugin.

**Optional / dev-only:**
- `PYMOL_GIT_MOD=<repo-root>` — dev plugin-path install (no zip rebuild per change).
- `APPDATA` — implicitly selects Windows user-data root (`rpg/paths.py:88-91`).

**Secrets location:** None exist. Gitignore guards `*.env`, `**/secrets.toml`, `**/auth.json` as hygiene only.

## Webhooks & Callbacks

**Incoming:** None. (The plugin registers exactly one GUI entry: menu item "RPG: Tale of C" → `_open_main_window`, `rpg/ui/plugin_entry.py:12-16`.)

**Outgoing:** None. No HTTP callbacks, no telemetry. The only outbound traffic is the `cmd.fetch` downloads described above, initiated by explicit user action (game start / bulk-download dialog).

## Approval-Gated Sources (project-specific constraint)

spec.md forbids fabricated science: any new scientific claim (DOI, PDB ID, pathway fact, RNG weight, protonation default) must be added to `data/citations.json` + `data/sources.json` and explicitly human-approved (`approval_status: "approved"`) BEFORE it lands in code/content. `tools/check_citations.py` + `rpg/citations.py` enforce this at pre-ship time. Any new external service or dependency goes through the same explicit-approval workflow (see STACK.md → Dependency-Approval Workflow).

---

*Integration audit: 2026-09-10*
