# Phase 6: Qt UI + Minimal Playable MVP — Research (Persistence / Achievements / Help / Bulk-Download)

**Researched:** 2026-08-29
**Domain:** PyMOL 2.5.0 user-data persistence + `cmd.fetch` bulk-download UX + achievement board + in-game help (one of three parallel Phase-6 research efforts; this one owns CAST-04, ACH-01, ACH-02, DOC-03, and the save/load UI integration)
**Confidence:** HIGH (every PyMOL-API claim below is read from `tmp/pymol-src/modules/pymol/` and cited `file:line`; every "proven layer" claim is read from the actual repo source; the three PyMOL-wiki links were fetched live 2026-08-29)

## Summary

Phase 6 must deliver four loosely-coupled user-facing subsystems on top of the proven Phase 2/3/4 layers: (1) a one-time bulk-download prompt for large PDB structures (CAST-04), (2) a cross-session achievement board persisted to a user-writable file (ACH-01, ACH-02), (3) a Qt save/load dialog wired to the existing `GameEngine.save/load` (SAVE-01/02 integration), and (4) an in-game help dialog with molecule-editing pointers + verified PyMOL wiki links (DOC-03). The dominant technical finding is that **`cmd.fetch` with `async_=0` is synchronous AND blocking with NO progress callback** (`importing.py:1382-1393` calls `_multifetch` directly; the `_fetch` download loop at `importing.py:1215-1245` has no per-byte callback hook). This means a Qt progress bar CANNOT show real per-file download progress during a single `fetch` — the UI thread is blocked inside the fetch. The pragmatic UX is a modal dialog that updates BETWEEN fetches in a Python loop, with `QApplication.processEvents()` between each file so the label/cancel button stay live. Cancel aborts the loop (not a mid-fetch interrupt); retry re-runs the loop (cmd.fetch's free idempotent cache at `importing.py:1211-1213` skips already-downloaded files, so retry costs only the missing ones).

The second dominant finding is a **gap in the Phase 2 save format**: `GameState` (state.py:27-64) carries seed/rng_state/current_node/character/flags/counters/visit_counts/edits_history/protonation_pref/started_at/finished/ending_tier but **NO view matrix**. Roadmap Phase 6 SC#3 demands "load restores the exact session (story position + RNG state + loaded structures + **view**)". PyMOL exposes the view as 18 floats via `cmd.get_view()` (`viewing.py:605,702` → `r = r[0:3]+r[4:7]+r[8:11]+r[16:25]`) and restores via `cmd.set_view(view)` (`viewing.py:705`). Capturing/restoring the view is **NEW work beyond Phase 2's SaveStore** — `GameState` needs a `view` field + the controller needs to call `cmd.get_view()` before save and `cmd.set_view()` after the on_enter replay on load. Flag this clearly to the planner.

The third finding resolves the cross-cutting "where do achievements + saves live?" question: PyMOL's own user-dir convention is `~/.pymol/` on Linux/Mac and `%APPDATA%\pymol\` on Windows (`plugins/installation.py:22-29` `get_default_user_plugin_path`). There is **NO `cmd.get_user_path` API** (searched; the closest is `invocation.get_user_config()` at `invocation.py:211` which finds pymolrc *files*, not a data dir). The recommendation is a new pure-Python `c14.paths.user_data_path(*parts)` that mirrors the PyMOL convention (`~/.pymol/c14-tale-of-c/` or `%APPDATA%/pymol/c14-tale-of-c/`) — lives OUTSIDE the plugin install dir so it survives plugin reinstalls, pure-`os`/`pathlib` so it stays WSL-unit-testable.

**Primary recommendation:** Build the four subsystems on a shared `user_data_path()` resolver; bulk-download = sync-fetch loop with between-fetch `processEvents()` + per-file `AssetManager.fetch_pdb` (raises `RuntimeError` on failure = retry signal); achievement board = a small JSON file at `user_data_path("achievements.json")` updated by the controller when it reads `TurnResult.node.is_ending`; save/load = `QFileDialog` → `engine.save/load` + a NEW `view` field on `GameState` (capture `cmd.get_view()` pre-save, `cmd.set_view()` post-load-replay).

---

## Standard Stack

The established libraries/tools for this domain (all already approved — no new deps):

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyQt5 via `pymol.Qt` | shipped with PyMOL 2.5.0 | All UI: bulk-download modal, achievement board dialog, save/load `QFileDialog`, help dialog | Spec-mandated modern interface; `Pymol-script-repo/plugins/dynoplot.py` (ported 2024) confirms `from pymol.Qt import QtCore, QtGui, QtWidgets` is the current idiom. No `pmgqt`/Tk. |
| `pymol.cmd.*` | 2.5.0 | `cmd.fetch` (bulk download), `cmd.get_view`/`cmd.set_view` (save view matrix) | Already wrapped by `c14/pymol_layer/asset_manager.py` + `molops.py` (Phase 3/4 proven). View-matrix APIs verified at `viewing.py:605,705`. |
| Python stdlib `json` / `os` / `pathlib` | 3.6.9 | Achievement JSON, save JSON, user-path resolution | Already used by `c14/persist.py` (SaveStore) + `c14/paths.py`. No `@dataclass` (3.7+); plain classes + `.format()` (repo convention). |
| `c14.paths` | in-repo Phase 1 | Pure `__file__`-relative path resolver — to be EXTENDED with `user_data_path()` | Proven cwd-independent (`paths.py:26-43`). The new `user_data_path` mirrors its design (pure resolver, no existence check, no pymol import). |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `c14.pymol_layer.asset_manager.AssetManager` | in-repo Phase 3 | `fetch_pdb(code, object_name)` — the per-file bulk-download primitive | The bulk-download loop calls this once per large PDB code. Its `RuntimeError` on `count_atoms <= 0` (`asset_manager.py:108-111,123-126`) is the per-file failure signal for the retry/lock decision. |
| `c14.persist.SaveStore` | in-repo Phase 2 | `save(state, path)` / `load(path)` — JSON (de)serialization | The Qt save/load dialog calls `engine.save(path)` (which calls `SaveStore.save`) / `engine.load(path)`. SaveStore already handles `makedirs` + `indent=2` + trailing newline (`persist.py:38-65`). |
| `c14.engine.GameEngine` | in-repo Phase 2 | `save(path)` / `load(path)` — syncs RNG state + replays on_enter MolActions | `engine.py:196-213`. `load` re-enters the current node with `record_visit=False` and dispatches on_enter MolActions to `molaction_sink` (the controller's molops). This IS the "scene auto-rebuilds on load" mechanism — already proven, the UI just calls it. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Sync fetch loop + `processEvents()` between files | `async_=1` fetch (deferred to PyMOL event loop) | `async_=1` keeps the UI live during ONE fetch, but you can't easily know when each fetch completes (no callback) — so you can't sequence "fetch N files, lock the ones that failed". Sync loop is predictable + sequences naturally. Recommend sync. |
| Sync fetch loop | QThread running the fetch loop | PyMOL `cmd.*` is NOT thread-safe (uses `_self.lockcm` locks, e.g. `viewing.py:660`). Calling `cmd.fetch` from a non-main thread risks deadlocks/corruption. **Do not** run `cmd.*` off the main thread. Stay sync-loop-on-main + `processEvents()`. |
| `~/.pymol/c14-tale-of-c/` user-data dir | Inside-plugin `c14/data/assets/downloaded/` | Downloaded/ is INSIDE the plugin install dir (`~/.pymol/startup/<plugin>/`), so a plugin reinstall (delete + re-unzip) WIPES achievements + saves. The whole point of ACH-02 is cross-session + cross-reinstall persistence. Must live OUTSIDE the plugin dir. |
| `~/.pymol/c14-tale-of-c/` user-data dir | `os.path.expanduser('~/c14-tale-of-c/')` (not under .pymol) | Putting it under `~/.pymol/` matches PyMOL's own convention (plugins + pymolrc live there) and is tidier (one app-data tree). Either works; recommend the PyMOL-convention path. |
| Achievement JSON at `user_data_path("achievements.json")` | Qt `QSettings` (registry/ini) | `QSettings` is overkill for a small collection board + isn't human-readable/diff-friendly (spec favors human-readable JSON for saves — same spirit). A plain JSON file matches `SaveStore`'s `indent=2` style + is trivially inspectable. Recommend JSON. |

**Installation:**
```bash
# NO new packages. Everything ships with pymol-open-source (PyQt5 via pymol.Qt) + stdlib.
# The only "install" is: the plugin zip goes to ~/.pymol/startup/ (or %APPDATA%/pymol/startup/)
# — the packaging researcher owns this; this research only depends on it being true.
```

---

## Architecture Patterns

### Recommended Project Structure (additions for this research's scope)
```
c14/
├── paths.py                    # ADD: user_data_path(*parts) — pure-Python user-writable resolver
├── state.py                    # EDIT: add `view` field (list of 18 floats or None) to GameState
├── persist.py                  # EDIT: SaveStore already serializes to_dict/from_dict — view field
│                               #       flows through automatically once state.py carries it (no SaveStore change)
├── engine.py                   # EDIT: save() captures cmd.get_view() via injected view-callback;
│                               #       load() restores via cmd.set_view() after on_enter replay
├── achievements.py             # NEW (domain tier, pure-Python): AchievementBoard + JSON schema + unlock logic
├── data/
│   ├── cast.json               # EDIT: add "source": "bundled"|"download" + "pdb_id" fields per enzyme
│   └── help.json               # NEW: curated help content (editing pointers + verified wiki links)
└── ui/                         # (gate-excluded — may import pymol.Qt)
    ├── bulk_download_dialog.py # NEW: QDialog — sync-fetch loop + processEvents + cancel/retry
    ├── achievements_dialog.py # NEW: QDialog — shows unlocks from achievements.json
    ├── save_load_dialogs.py    # NEW: thin QFileDialog wrappers -> engine.save/load
    └── help_dialog.py          # NEW: QDialog — renders help.json (text + clickable links)
# User-writable, OUTSIDE the repo + outside the plugin install dir:
#   ~/.pymol/c14-tale-of-c/achievements.json   (Linux/Mac)
#   %APPDATA%/pymol/c14-tale-of-c/achievements.json   (Windows)
#   ~/.pymol/c14-tale-of-c/saves/<chosen-name>.json   (default save dir)
#   ~/.pymol/c14-tale-of-c/.bulk_download_state.json  (flag/marker for the prompt)
```

> **Scope boundary:** the `ui/__init__.py` is currently a 1-line placeholder; the `c14/ui/` files above are NEW. The "UI-as-adapter" researcher owns the main window + controller + plugin entry (`__init_plugin__`/`addmenuitemqt`); the packaging researcher owns the zip/startup install. This research owns ONLY the four dialogs above + the `achievements.py` domain module + the `paths.py`/`state.py`/`engine.py`/`cast.json`/`help.json` edits. Coordinate so the main-window "cast/help/save/load/achievement controls" buttons (SC#1) route to these dialogs.

### Pattern 1: Bulk-Download Flow (CAST-04) — sync-fetch loop with between-file UI updates

**What:** On first play, before entering the first story node that needs a large structure, the controller checks which large PDBs are missing and, if any, shows a modal `QDialog` that loops `AssetManager.fetch_pdb` once per missing code, updating a label + value-bar between files.

**When to use:** Triggered by the controller when the player starts a game (or selects a character) — NOT at plugin load. Detection: "any expected large-PDB file missing in `c14/data/assets/downloaded/`". Use the cast manifest's `"source": "download"` + `"pdb_id"` fields to know the expected list; check `os.path.exists(downloaded_dir / (pdb_id.lower() + ".pdb"))` per code (the file is lowercased — see Pitfall 3).

**Why sync:** `cmd.fetch(..., async_=0)` runs `_multifetch` synchronously on the calling thread (`importing.py:1386-1393`), and `_fetch`'s download loop (`importing.py:1215-1245`) has NO progress callback — it calls `_self.file_read(url)` (blocking) then writes the file. The UI thread is blocked inside each fetch. `processEvents()` between files is the only way to keep the cancel button live WITHOUT spawning a thread (which is unsafe — `cmd.*` is not thread-safe; see Alternatives). Per-file granularity is the natural progress unit.

**Example:**
```python
# c14/ui/bulk_download_dialog.py (gate-excluded; may import pymol.Qt + pymol.cmd)
from pymol.Qt import QtCore, QtGui, QtWidgets
from c14.paths import data_path, user_data_path
from c14.pymol_layer.asset_manager import AssetManager
import os, json

class BulkDownloadDialog(QtWidgets.QProgressDialog):
    """Modal sync-fetch bulk-download. Updates BETWEEN fetches (cmd.fetch is
    blocking with no progress callback -- see 06-RESEARCH-persistence-achievements
    Pattern 1). Cancel aborts the LOOP (not a mid-fetch interrupt); re-run = retry.
    """
    def __init__(self, cmd, missing_codes, parent=None):
        # missing_codes: list of (pdb_id, object_name, enzyme_id) to fetch
        super().__init__("Downloading structures...", "Cancel", 0, len(missing_codes), parent)
        self.setWindowTitle("RPG: Tale of C — One-time Structure Download")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self._cmd = cmd
        self._assets = AssetManager(cmd)
        self._missing = missing_codes
        self._failed = []      # (pdb_id, enzyme_id) -- for offline lock
        self._canceled = False
        self.canceled.connect(self._on_cancel)

    def _on_cancel(self):
        self._canceled = True   # the loop checks this BETWEEN fetches (not mid-fetch)

    def run(self):
        downloaded = str(data_path("data", "assets", "downloaded"))
        if not os.path.isdir(downloaded):
            os.makedirs(downloaded, exist_ok=True)
        for i, (pdb_id, obj_name, enzyme_id) in enumerate(self._missing):
            if self._canceled:
                break
            self.setLabelText("Downloading {0} ({1} of {2})...".format(
                pdb_id, i + 1, len(self._missing)))
            self.setValue(i)
            QtWidgets.QApplication.processEvents()   # keep cancel button + label live
            try:
                self._assets.fetch_pdb(pdb_id, obj_name)   # raises RuntimeError on count_atoms<=0
            except Exception as e:                       # offline / 404 / corrupt
                self._failed.append((pdb_id, enzyme_id, str(e)))
            QtWidgets.QApplication.processEvents()   # again, between files
        self.setValue(len(self._missing))
        return {"failed": self._failed, "canceled": self._canceled,
                "completed": len(self._missing) - len(self._failed)}
```

**Key UX constraints (document to the human-verify checkpoint):**
- The bar advances per FILE, not per byte (blocking fetch forbids per-byte progress). Label must say "Downloading 4PFK (3 of 12)..." so the player sees movement.
- Cancel = abort the loop after the current fetch finishes (cannot interrupt a blocking `file_read`). This is acceptable; document it.
- Retry = re-run the loop. `cmd.fetch` SKIPS download if the file exists (`importing.py:1211-1213`), so retry only re-fetches the failed/missing ones — free idempotent cache.
- Offline fallback (see Pattern 2) = lock only the characters whose structures failed, NOT the whole game.

### Pattern 2: Offline Fallback — per-character lock (CAST-04)

**What:** If `BulkDownloadDialog` returns `failed` entries (no network / 404 / corrupt), the controller marks ONLY those characters as unavailable on the character-selection screen. Glucose's bundled small/critical structures (loaded via `AssetManager.load_bundled`, no network) mean glucose is ALWAYS playable.

**When to use:** After the bulk-download dialog completes with `failed` non-empty.

**Example:**
```python
# in the controller (UI-as-adapter researcher's domain), after BulkDownloadDialog.run():
result = dialog.run()
if result["failed"]:
    # Lock only the characters whose large structures didn't download.
    # The mapping "which character needs which PDB" comes from cast.json
    # (each enzyme has "character" or is reachable from a character's start node).
    locked_characters = set()
    for pdb_id, enzyme_id, err in result["failed"]:
        # resolve enzyme_id -> owning character(s) via the story graph / cast manifest
        for ch in self._characters_needing(enzyme_id):
            locked_characters.add(ch)
    self._character_select.set_locked(locked_characters, reason="structure unavailable (offline)")
# Glucose's bundled structures (load_bundled) need no network -> never locked.
```

**Lock mechanism:** a `set()` of locked character ids on the character-selection widget; locked entries are greyed-out + show "Unavailable (download failed — Retry?)" with a Retry button that re-opens `BulkDownloadDialog` for just the missing files. This honors SC#4's "locks only affected characters". The lock state is IN-MEMORY per session (no need to persist — re-detecting on next start via the missing-file check is cleaner and self-healing if the network returns).

### Pattern 3: Achievement Board schema + unlock detection (ACH-01, ACH-02)

**What:** A small JSON file at `user_data_path("achievements.json")` holding a collection-based board (endings found, characters tried, branches discovered) — explicitly NOT a ranked leaderboard (REQUIREMENTS.md ACH-01). A pure-Python `AchievementBoard` domain module owns the schema + unlock logic; the controller calls it when it reads `TurnResult`.

**Schema (v1 minimal — glucose MVP, per SC#5 "glucose tried + endings found so far"):**
```json
{
  "version": 1,
  "characters_tried": ["glucose"],
  "endings_found": [
    {"node_id": "tca.true_ending", "tier": "true", "character": "glucose", "date": "2026-08-29T12:00:00Z"},
    {"node_id": "bad.critical_residue_break", "tier": "bad", "character": "glucose", "date": "2026-08-29T12:05:00Z"}
  ],
  "branches_discovered": ["intro.preface", "gly.start", "tca.shuffle"],
  "achievements_unlocked": [
    {"id": "first_game",       "name": "First Steps",        "description": "Started your first playthrough", "date": "2026-08-29T11:55:00Z"},
    {"id": "glucose_tried",    "name": "Glucose",            "description": "Began a playthrough as glucose",  "date": "2026-08-29T11:55:00Z"},
    {"id": "true_ending",      "name": "Soul Harvested",    "description": "Reached a True ending (electrons -> ATP via ETC)", "date": "2026-08-29T12:00:00Z"},
    {"id": "bad_ending",       "name": "Lost Connection",    "description": "Reached a Bad ending",            "date": "2026-08-29T12:05:00Z"}
  ]
}
```

**Collection-based, not leaderboard:** the board records WHAT was found (sets + lists), not a score or rank. "Limited set" (ACH-01) = the `achievements_unlocked` list is a fixed catalog the player fills in; "limited collection of starting points/endings" = `characters_tried` (3 max) + `endings_found` (one entry per unique `node_id`). The v1 catalog is 4 achievements (above); Phase 7-9 expand it. **Cap deferred to content/UI phase** (ACH-02) — for Phase 6 ship the 4-achievement v1 set + the open `endings_found`/`branches_discovered` collections (no cap yet).

**Where unlock detection lives:** the CONTROLLER, after each `engine.choose`/`apply_player_edit`/`start` returns a `TurnResult`. The controller reads `TurnResult.node` (`engine.py:54-55`) and checks:
- `turn_result.node.is_ending is not None` → an ending was reached → append to `endings_found` (dedupe by `node_id`) + unlock the tier achievement (`true`→"Soul Harvested", `bad`→"Lost Connection", `good`→"Retained", `normal`→"Released"). `Node.is_ending` is `"true"|"good"|"normal"|"bad"` or None (`model.py:251-252,310-314`).
- `engine.start(character)` was just called → add `character` to `characters_tried` (dedupe) + unlock `first_game` + `<character>_tried`.
- On every node entry → add `turn_result.node.id` to `branches_discovered` (dedupe). "Branches discovered" = unique nodes visited (a proxy for "how much of the graph you've explored").

**Example (pure-Python domain module — unit-testable in WSL):**
```python
# c14/achievements.py -- pure-Python, stdlib only (json, os, datetime). NO pymol/PyQt5.
import json, os, datetime
from c14.paths import user_data_path

ACHIEVEMENT_CATALOG_V1 = [
    ("first_game",    "First Steps",     "Started your first playthrough"),
    ("glucose_tried", "Glucose",         "Began a playthrough as glucose"),
    ("true_ending",   "Soul Harvested",  "Reached a True ending (electrons -> ATP via ETC)"),
    ("bad_ending",    "Lost Connection", "Reached a Bad ending"),
    ("good_ending",   "Retained",        "Reached a Good ending (carbon body retained)"),
    ("normal_ending", "Released",        "Reached a Normal ending (CO2 released)"),
]
TIER_ACHIEVEMENT_ID = {"true": "true_ending", "good": "good_ending",
                       "normal": "normal_ending", "bad": "bad_ending"}

class AchievementBoard(object):
    """Collection-based achievement board persisted to a user-writable JSON.

    Pure data + unlock logic. The controller calls on_turn(turn_result, is_new_game)
    after each engine turn; this module diffs + persists. The Qt dialog reads the
    JSON (or this object) to render unlocks.
    """
    def __init__(self, path=None):
        self.path = path or str(user_data_path("achievements.json"))
        self.data = {"version": 1, "characters_tried": [], "endings_found": [],
                      "branches_discovered": [], "achievements_unlocked": []}
        self._load()

    def _load(self):
        if os.path.isfile(self.path):
            with open(self.path, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            for k in self.data:                      # forward-compatible .get merge
                self.data[k] = loaded.get(k, self.data[k])

    def _save(self):
        parent = os.path.dirname(self.path)
        if parent: os.makedirs(parent, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2)
            fh.write("\n")

    def _unlock(self, achievement_id):
        if any(a["id"] == achievement_id for a in self.data["achievements_unlocked"]):
            return
        for aid, name, desc in ACHIEVEMENT_CATALOG_V1:
            if aid == achievement_id:
                self.data["achievements_unlocked"].append({
                    "id": aid, "name": name, "description": desc,
                    "date": datetime.datetime.utcnow().isoformat() + "Z"})
                return

    def on_turn(self, turn_result, character, is_new_game=False):
        """Called by the controller after each engine turn. Idempotent (dedupe by id)."""
        changed = False
        if is_new_game:
            self._unlock("first_game")
            if character and character not in self.data["characters_tried"]:
                self.data["characters_tried"].append(character)
                changed = True
            self._unlock(character + "_tried")   # e.g. glucose_tried (catalog has it for v1)
        node = turn_result.node
        if node.id not in self.data["branches_discovered"]:
            self.data["branches_discovered"].append(node.id)
            changed = True
        if node.is_ending is not None:
            entry = {"node_id": node.id, "tier": node.is_ending,
                      "character": character,
                      "date": datetime.datetime.utcnow().isoformat() + "Z"}
            if not any(e["node_id"] == node.id for e in self.data["endings_found"]):
                self.data["endings_found"].append(entry)
                changed = True
            self._unlock(TIER_ACHIEVEMENT_ID.get(node.is_ending))
        if changed or self.data["achievements_unlocked"]:   # _unlock may have appended
            self._save()
```

> **Note on `<character>_tried` for non-glucose characters:** the v1 catalog above only defines `glucose_tried` (Phase 6 = glucose MVP). Phase 8 adds `fatty_acid_tried` + `alcohol_tried`. `_unlock` no-ops on unknown ids (the catalog lookup misses) — safe for future expansion; document this so the planner doesn't ship a half-broken "alcohol_tried" in Phase 6.

### Pattern 4: Save/Load UI integration + the NEW view-matrix field (SAVE-01/02 + SC#3)

**What:** A Qt `QFileDialog` (save) → `engine.save(path)`; a `QFileDialog` (load) → `engine.load(path)` → the on_enter MolActions dispatch via `molaction_sink` rebuilds the scene (Pattern 6, already proven `engine.py:203-213`). Default save dir = `user_data_path("saves")`.

**The view-matrix gap (FLAG TO PLANNER):** SC#3 says "load restores the exact session (story position + RNG state + loaded structures + **view**)". Phase 2's `GameState` has NO view field (`state.py:46-64`). PyMOL exposes the view as 18 floats: `cmd.get_view()` returns `r[0:3]+r[4:7]+r[8:11]+r[16:25]` (`viewing.py:702`) — a plain tuple/list of 18 floats, JSON-serializable as-is. `cmd.set_view(view)` accepts a string-or-sequence (`viewing.py:705`). So:

**Edits required (NEW work beyond Phase 2):**
1. `c14/state.py`: add `view=None` field to `GameState.__init__`, `to_dict`, `from_dict` (default None for forward-compat with old saves).
2. `c14/engine.py`: `save(path)` — before `SaveStore.save`, capture the view via an injected `view_provider` callable (default `None` → don't capture; the controller injects `lambda: list(cmd.get_view())`). `load(path)` — after the on_enter replay (which rebuilds structures + reps), call an injected `view_applier` callable (`lambda v: cmd.set_view(v)`) if `state.view is not None`.

**Why a callback, not a direct `cmd` import in engine.py:** `engine.py` is in the domain tier (gate-scanned — NO pymol import; `engine.py:24-32` confirms stdlib only). The controller (UI layer) injects the `view_provider`/`view_applier` closures, exactly as it injects `molaction_sink`. This preserves the testability boundary — `engine.py` stays WSL-unit-testable with mock view callbacks.

**Example:**
```python
# c14/engine.py edits (minimal diff to Phase 2):
class GameEngine(object):
    def __init__(self, graph, molaction_sink=None, edit_router=None,
                 view_provider=None, view_applier=None):   # NEW
        # ...existing...
        self._view_provider = view_provider    # callable() -> list[18 floats] or None
        self._view_applier = view_applier      # callable(list[18 floats]) -> None

    def save(self, path):
        self.state.rng_state = self.rng.get_state()
        if self._view_provider is not None:                # NEW
            try:
                self.state.view = list(self._view_provider())   # cmd.get_view() -> 18 floats
            except Exception:
                self.state.view = None                       # don't block save on view capture
        SaveStore.save(self.state, path)

    def load(self, path):
        self.state = SaveStore.load(path)
        self.rng = RngEngine.from_state(self.state.seed, self.state.rng_state)
        result = self._enter(self.state.current_node, record_visit=False)  # rebuilds scene
        if self._view_applier is not None and self.state.view is not None:  # NEW -- AFTER replay
            try:
                self._view_applier(self.state.view)          # cmd.set_view(18 floats)
            except Exception:
                pass                          # don't block load on view restore
        return result
```
```python
# c14/state.py edits (add view field, 3 sites):
def __init__(self, ..., ending_tier=None, view=None, version=1):  # NEW view
    # ...
    self.view = view
def to_dict(self):
    return {..., "ending_tier": self.ending_tier, "view": self.view}  # NEW
@classmethod
def from_dict(cls, d):
    return cls(..., ending_tier=d.get("ending_tier"), view=d.get("view"))  # NEW (default None)
```
```python
# controller wiring (UI layer):
engine = GameEngine(graph, molaction_sink=molops.apply,
                    view_provider=lambda: list(cmd.get_view()),     # src: viewing.py:605
                    view_applier=lambda v: cmd.set_view(v))           # src: viewing.py:705
```

**Save/load UI (thin Qt):**
```python
# c14/ui/save_load_dialogs.py (gate-excluded)
from pymol.Qt import QtWidgets
from c14.paths import user_data_path
import os

def ask_save_path(parent, default_name="save.json"):
    default_dir = str(user_data_path("saves"))
    if not os.path.isdir(default_dir):
        os.makedirs(default_dir, exist_ok=True)
    path, _ = QtWidgets.QFileDialog.getSaveFileName(
        parent, "Save RPG: Tale of C Game",
        os.path.join(default_dir, default_name), "RPG Save (*.json)")
    return path or None

def ask_load_path(parent):
    default_dir = str(user_data_path("saves"))
    path, _ = QtWidgets.QFileDialog.getOpenFileName(
        parent, "Load RPG: Tale of C Game",
        default_dir, "RPG Save (*.json)")
    return path or None
# Controller: engine.save(ask_save_path(self)) / engine.load(ask_load_path(self))
```

**Confirm load reconstructs the scene:** yes — `engine.load` (`engine.py:203-213`) calls `_enter(current_node, record_visit=False)` which runs the node's `on_enter` MolActions through `molaction_sink` (= `molops.apply`), re-firing `hide_all`/`load`/`show`/`zoom`/`color` etc. (Phase 3 `molops.py` dispatch). The molaction_sink dispatches on_enter MolActions to molops — exactly Pattern 6. This is ALREADY proven in Phase 2 with a mock sink + Phase 3 with real molops. The view is restored AFTER the replay (so the replay's `zoom` doesn't override the saved view). Note: if a node's on_enter includes a `zoom` MolAction, it will fire during replay and THEN `set_view` overrides it — this is the desired behavior (the saved view wins, matching "exact session").

### Pattern 5: Cross-cutting user-writable path strategy

**What:** ONE pure-Python resolver for both achievements + saves + the bulk-download marker, matching PyMOL's own user-dir convention.

**The PyMOL convention (verified in source):**
- `tmp/pymol-src/modules/pymol/plugins/installation.py:22-29` `get_default_user_plugin_path()`:
  - Linux/Mac: `~/.pymol/startup`
  - Windows: `%APPDATA%\pymol\startup`
- `tmp/pymol-src/modules/pymol/_gui.py:984`: uses `os.path.expanduser('~/.pymol')`
- `tmp/pymol-src/modules/pymol/plugins/__init__.py:18`: `~/.pymolpluginsrc.py`
- **There is NO `cmd.get_user_path` API** (searched `get_user_path|expfolder|user_dir` — only `invocation.get_user_config()` at `invocation.py:211` which finds pymolrc files, not a data dir).

**Recommended resolver (pure-Python, unit-testable in WSL):**
```python
# ADD to c14/paths.py (pure-Python, no pymol import -- stays WSL-unit-testable)
import os
from pathlib import Path

def user_data_path(*relative_parts):
    # type: (*str) -> Path
    """Resolve a user-writable path that survives PyMOL restarts AND plugin reinstalls.

    Matches PyMOL's own user-dir convention (plugins/installation.py:22-29
    get_default_user_plugin_path): ~/.pymol/ on Linux/Mac, %APPDATA%/pymol/ on
    Windows. Appends a 'c14-tale-of-c/' subfolder so game data sits BESIDE (not
    inside) the plugin install dir (~/.pymol/startup/<plugin>/) -- a plugin
    reinstall (delete + re-unzip startup/) does NOT wipe this data.

    Pure-Python (os + pathlib), NO pymol import -- importable in pure WSL python3.6
    for unit tests (set/monkeypatch APPDATA / HOME to assert the split). Does NOT
    check existence -- callers makedirs as needed (matches data_path's pure-resolver
    design, paths.py:26-43). Returns Path (use str() for open()).

    Example:
        p = user_data_path("achievements.json")
        # -> ~/.pymol/c14-tale-of-c/achievements.json  (Linux/Mac)
        # -> %APPDATA%/pymol/c14-tale-of-c/achievements.json  (Windows)
    """
    if 'APPDATA' in os.environ:   # Windows -- matches installation.py:27
        base = os.path.join(os.environ['APPDATA'], 'pymol', 'c14-tale-of-c')
    else:                         # Linux/Mac -- matches installation.py:29
        base = os.path.join(os.path.expanduser('~'), '.pymol', 'c14-tale-of-c')
    return Path(base).joinpath(*relative_parts)
```

**How the three subsystems use it:**
| Subsystem | Path | Created by |
|-----------|------|------------|
| Achievements | `user_data_path("achievements.json")` | `AchievementBoard._save` (`os.makedirs(parent, exist_ok=True)`) |
| Saves | `user_data_path("saves", "<name>.json")` | `SaveStore.save` already does `makedirs` (`persist.py:47-49`) — works unchanged once given the path |
| Bulk-download marker | `user_data_path(".bulk_download_state.json")` | controller (optional — see Open Questions) |

**Keeping the resolver pure (no `cmd.*`):** the resolver uses only `os.environ` + `os.path.expanduser` — no `pymol` import, so `c14/paths.py` stays gate-clean (Phase 1 AST gate) and WSL-unit-testable. The Qt/controller layer just calls `str(user_data_path(...))` and passes the string to `AchievementBoard(path=...)` / `engine.save(path)` / `SaveStore`. **No `cmd.*` needed to resolve the path** — the PyMOL convention is filesystem-only.

### Pattern 6: In-game Help dialog (DOC-03) — curated, verified links

**What:** A `QDialog` showing (a) molecule-editing pointers in plain language (point mutation / substrate edit / protonation — the Phase 4 EDIT-01/02/03 mechanics) + (b) a small curated list of PyMOL wiki links, opened in the user's browser via `QtGui.QDesktopServices.openUrl`.

**Scope guard:** DOC-01/DOC-02 (dramatic cast list + slogan) are Phase 9 — **do NOT scope those in**. Phase 6's DOC-03 is ONLY editing pointers + wiki links.

**Content lives in `c14/data/help.json`** (so it's editable without touching Python + can carry claim_ids for any science claim if needed; the editing pointers themselves describe mechanics, not science, so no citation gate concern — but the pointer text should NOT make chemistry claims beyond what Phase 4 already cited).

**Example help.json:**
```json
{
  "version": 1,
  "editing_pointers": [
    {"title": "Point mutation",
     "body": "Swap one residue in an enzyme's active site. Use the edit panel to pick a residue + a new identity. A known reverse-mutation (matching a disease allele) routes the story to a 'you restored it' branch; an unknown edit falls through to a bad ending."},
    {"title": "Substrate edit",
     "body": "Add or remove a group on the small molecule (the C14 hero or an intermediate). Pick the substrate + the group change in the edit panel."},
    {"title": "Protonation change",
     "body": "Switch a catalytic residue's or substrate's protonation state between curated variants (e.g. HIP/HIE/HID for histidine). Defaults are physiological pH; you can adjust."},
    {"title": "Restore safety net",
     "body": "If an edit goes wrong, 'Reveal correct 3D model' restores the pre-edit snapshot without restarting (keeps gameplay smooth)."}
  ],
  "wiki_links": [
    {"label": "alter (residue editing)", "url": "https://pymolwiki.org/index.php/Alter",
     "note": "Read-write atom properties; sort after altering identifiers. Verified live 2026-08-29 (redirects to Iterate)."},
    {"label": "h_add (protonation)",      "url": "https://pymolwiki.org/index.php/H_Add",
     "note": "Valence-only hydrogen add (NOT pH-aware) -- why the game uses curated variants. Verified live 2026-08-29."},
    {"label": "fetch (loading structures)", "url": "https://pymolwiki.org/index.php/Fetch",
     "note": "Downloads from PDB/PubChem; async=0 for scripting. Verified live 2026-08-29."}
  ]
}
```

**Only 3 wiki links are listed because only 3 were verified live 2026-08-29** (Alter→Iterate, H_Add, Fetch — all fetched, all real PyMOL wiki pages). The planner may add more (e.g. `Show`, `Select`, `Sort`) but MUST webfetch-verify each before ship (no-fabrication rule). Do NOT add speculative links like `https://pymolwiki.org/index.php/Stereo` without a live fetch.

**Example dialog (gate-excluded):**
```python
# c14/ui/help_dialog.py
import json
from pymol.Qt import QtCore, QtGui, QtWidgets
from c14.paths import data_path

class HelpDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RPG: Tale of C — Help")
        self.setMinimumWidth(520)
        with open(str(data_path("data", "help.json")), "r", encoding="utf-8") as fh:
            self.data = json.load(fh)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("<b>Molecule editing</b>"))
        for p in self.data["editing_pointers"]:
            layout.addWidget(QtWidgets.QLabel("<b>{0}</b><br/>{1}".format(p["title"], p["body"])))
        layout.addWidget(QtWidgets.QLabel("<b>PyMOL wiki references</b>"))
        for link in self.data["wiki_links"]:
            btn = QtWidgets.QPushButton(link["label"])
            btn.clicked.connect(lambda _=False, u=link["url"]: QtGui.QDesktopServices.openUrl(QtCore.QUrl(u)))
            layout.addWidget(btn)
        close = QtWidgets.QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close)
```

### Anti-Patterns to Avoid
- **Hand-rolling a download loop that calls `cmd.fetch` directly** — bypasses `AssetManager`'s Pitfall-5 mitigations (`type=`/`async_=0`/`path=<abs>`). Use `AssetManager.fetch_pdb` so the CIF-default + cwd-default + async-default pitfalls stay mitigated (03-02-SUMMARY key-decisions). The bulk-download dialog should hold an `AssetManager` instance, not call `cmd.fetch` raw.
- **Per-byte progress bar during a fetch** — impossible (blocking `file_read`, no callback). Don't attempt it; you'll freeze the UI and confuse the human-verify reviewer. Use per-file progress.
- **Persisting achievements/saves INSIDE the plugin dir** (`c14/data/assets/downloaded/` or anywhere under `~/.pymol/startup/<plugin>/`) — a plugin reinstall wipes them. Use `user_data_path()` (outside the plugin dir).
- **Storing the view matrix as a 4x4 / numpy array** — `cmd.get_view` returns 18 scalars in a specific layout (`viewing.py:632-644`); store as a plain JSON list of 18 floats. `cmd.set_view` accepts a sequence. No numpy needed.
- **Making the achievement board a leaderboard** — ACH-01 explicitly says collection-based, NOT ranked. Don't add scores/ranks/timestamps-as-scores.
- **Fabricating PyMOL wiki URLs** — only ship links webfetch-verified live (3 verified 2026-08-29; see Open Questions for the rest).

---

## Don't Hand-Roll

Problems that look simple but already have a proven solution in the repo:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Download a PDB into a PyMOL object with path/type/async pitfalls mitigated | A custom `cmd.fetch` wrapper | `AssetManager.fetch_pdb(code, object_name)` (`asset_manager.py:114-127`) | Already bakes in `type='pdb'` (not CIF default), `async_=0` (sync), `path=<abs downloaded dir>` (not cwd), `count_atoms>0` post-condition raising `RuntimeError` on failure — the exact retry/failure signal the bulk-download loop needs. |
| Resolve a bundled structure's path cwd-independently | `os.path.join(os.getcwd(), ...)` | `c14.paths.data_path("data", "assets", "bundled", filename)` (`paths.py:26-43`) | Phase 1 proven cwd-independent (`__file__`-relative). |
| Serialize/restore GameState to human-readable JSON | A custom JSON writer | `SaveStore.save/load` (`persist.py:38-65`) | Already does `indent=2` + trailing newline + `makedirs` + `GameState.from_dict` round-trip. The new `view` field flows through automatically (it's in `to_dict`/`from_dict`). |
| Rebuild the molecular scene on load | A `.pse` session save | `engine.load(path)` → on_enter MolAction replay (Pattern 6, `engine.py:203-213`) | Pattern 6 is proven: the scene is a pure function of game state, re-fired through `molaction_sink` (= `molops.apply`). Don't save a `.pse` (Anti-Pattern 5 — `persist.py:1-9` docstring). |
| Capture/restore the PyMOL view | Manual matrix math / numpy | `cmd.get_view()` + `cmd.set_view(view)` (`viewing.py:605,705`) | PyMOL's own API; returns/accepts 18 floats. Just store the list in GameState.view. |
| Detect an ending / its tier | Parsing node text | `TurnResult.node.is_ending` (`model.py:251-252,310-314`) | `None` = non-ending; `"true"`/`"good"`/`"normal"`/`"bad"` = ending tier. The controller reads this directly. |
| Resolve a user-writable path | `os.getcwd()` / hardcode `~` | NEW `c14.paths.user_data_path(*parts)` (Pattern 5) | Matches PyMOL's `~/.pymol` / `%APPDATA%/pymol` convention; pure-Python (WSL-testable); survives reinstalls. |

**Key insight:** the download/persistence domain is almost entirely served by existing Phase 2/3/4 building blocks. The NEW work is narrow: (a) the `user_data_path()` resolver, (b) the `view` field on GameState + the two callbacks on GameEngine, (c) the four Qt dialogs, (d) the `AchievementBoard` domain module, (e) `cast.json` schema extension + `help.json`. Do not re-solve download/save/scene-rebuild — wrap them.

---

## Common Pitfalls

### Pitfall 1: Blocking fetch forbids per-byte/per-file-during-fetch progress (HIGH — will trip the human-verify)
**What goes wrong:** A developer assumes `QProgressBar` can show real download progress during `cmd.fetch` and builds a `downloaded/total bytes` bar. The bar never moves; the UI freezes for the duration of each fetch; the human-verify reviewer sees a "hung" dialog.
**Why it happens:** `cmd.fetch(..., async_=0)` calls `_multifetch` synchronously on the calling thread (`importing.py:1386-1393`); `_fetch`'s loop (`importing.py:1215-1245`) calls `_self.file_read(url)` (blocking) with NO progress callback. The Qt event loop is NOT running during the fetch, so the bar can't repaint.
**How to avoid:** Per-FILE progress only. Update the label + value between fetches via `QApplication.processEvents()`. Document this loudly in the dialog docstring + the human-verify checklist ("bar advances per file, not per byte — this is correct").
**Warning signs:** A progress bar that sits at 0% then jumps to 100% per file; an "Application Not Responding" OS banner during a long fetch.

### Pitfall 2: The view matrix is NOT in Phase 2's SaveStore (HIGH — SC#3 gap)
**What goes wrong:** The planner assumes `engine.save/load` already restores the view (it restores story+RNG+scene). The human-verify loads a save and the camera snaps to a default view, not the saved one → SC#3 ("load restores the exact session ... + view") fails.
**Why it happens:** Phase 2's `GameState` (`state.py:46-64`) has no `view` field; `SaveStore` only serializes what `to_dict` returns. "Loaded structures" (the scene) IS restored (Pattern 6 replay) but the CAMERA ANGLE/ZOOM is not.
**How to avoid:** Add `view=None` to `GameState` (3 sites: `__init__`/`to_dict`/`from_dict`); inject `view_provider`/`view_applier` callbacks into `GameEngine` (Pattern 4); capture `cmd.get_view()` (18 floats, `viewing.py:702`) before save, `cmd.set_view(view)` after the on_enter replay on load (AFTER, so a node's `zoom` MolAction doesn't override the saved view).
**Warning signs:** A save/load round-trip where the view differs; the test plan asserting "exact session" without a view-matrix assertion.

### Pitfall 3: Per-character offline lock vs whole-game lock (MEDIUM — SC#4 precision)
**What goes wrong:** A download failure disables the whole game ("structures unavailable, cannot play") instead of just the affected characters. The player can't play glucose even though glucose's structures are bundled.
**Why it happens:** The bulk-download result's `failed` list isn't mapped back to SPECIFIC characters; a generic "download failed" gate blocks all entry.
**How to avoid:** Map each failed `(pdb_id, enzyme_id)` to the character(s) whose pathway needs it (via `cast.json` + the story graph), and lock ONLY those characters on the selection screen (Pattern 2). Glucose's bundled structures (loaded via `AssetManager.load_bundled`, no network) keep glucose always playable. SC#4 says "locks only affected characters" — read it literally.
**Warning signs:** A "Retry" button that blocks the whole game; a character-select screen where ALL characters are greyed out after one fetch fails.

### Pitfall 4: Wrong filename case in the "missing file" check (MEDIUM — defeats the idempotent cache)
**What goes wrong:** The "is this large PDB already downloaded?" check uses the UPPERCASE code (`os.path.exists(downloaded + "/4PFK.pdb")`), but `cmd.fetch` writes the LOWERCASE filename (`4pfk.pdb` — `importing.py:1200` lowercases the code, `1206` builds the filename AFTER). The check always returns False → the prompt re-shows every session + re-downloads every time, defeating the free cache.
**Why it happens:** `importing.py:1200` `if bioType not in ['cc']: code = code.lower()` runs BEFORE `nameFmt.format` at line 1206. So `cmd.fetch("4PFK", type="pdb")` → file `path/4pfk.pdb`. (On Windows the filesystem is case-insensitive so this hides; on Linux/WSL it bites. The downloaded/ dir is on the Windows side so Windows-case-insensitive, but matching PyMOL's exact casing is safer + clearer.)
**How to avoid:** `os.path.exists(os.path.join(downloaded_dir, pdb_id.lower() + ".pdb"))`. Or — simpler + more robust — DON'T pre-check; just call `AssetManager.fetch_pdb` for each expected code and let `cmd.fetch`'s own skip-if-exists (`importing.py:1211-1213`) handle it. The "should I show the prompt at all?" gate can be a flag file OR a single "any file missing?" loop using the lowercased name.
**Warning signs:** The bulk-download prompt re-appears on every game start despite a successful prior download.

### Pitfall 5: Persisting user data inside the plugin dir (MEDIUM — ACH-02 regression)
**What goes wrong:** Achievements/saves are written under `c14/data/` (the plugin install dir) and survive PyMOL restarts but NOT plugin reinstalls — a delete-and-reinstall wipes the player's progress + achievement board.
**Why it happens:** `c14/data/assets/downloaded/` is the obvious "writable data" spot, but it's INSIDE the plugin zip target.
**How to avoid:** `user_data_path()` lives at `~/.pymol/c14-tale-of-c/` (Linux/Mac) or `%APPDATA%/pymol/c14-tale-of-c/` (Windows) — OUTSIDE `~/.pymol/startup/`. A plugin reinstall only touches `startup/`, not the sibling `c14-tale-of-c/`.
**Warning signs:** A save file path that starts with the plugin's install dir; an achievement file that disappears after a plugin upgrade.

### Pitfall 6: `engine.py` importing `pymol` for the view callbacks (HIGH — testability gate regression)
**What goes wrong:** A developer adds `from pymol import cmd` to `engine.py` to call `cmd.get_view`/`set_view` directly → the Phase 1 AST gate (`tools/check_imports.py`) fails on `c14/engine.py` → all pure-WSL unit tests break.
**Why it happens:** The view capture/restore needs `cmd.*`, and `engine.py` is where save/load live.
**How to avoid:** Inject `view_provider`/`view_applier` as constructor callables (closures), exactly as `molaction_sink` is injected (`engine.py:83-88`). The controller (UI layer) provides `lambda: list(cmd.get_view())` / `lambda v: cmd.set_view(v)`. `engine.py` stays stdlib-only + gate-clean.
**Warning signs:** `check_imports.py` exiting non-zero; `python3.6 -m pytest tests/test_engine.py` failing to import.

### Pitfall 7: Cancel that promises mid-fetch interrupt (LOW — UX honesty)
**What goes wrong:** The Cancel button implies "stop immediately" but actually waits for the current fetch to finish (you can't interrupt a blocking `file_read`).
**Why it happens:** Sync fetch is atomic from the caller's view; there's no interrupt hook.
**How to avoid:** Label the button "Cancel (after current file)" OR set expectations in the dialog text ("Cancel stops the download after the current file completes"). The loop checks `self._canceled` BETWEEN fetches (Pattern 1).
**Warning signs:** A Cancel button that doesn't respond for 10+ seconds during a large fetch; a reviewer reporting "Cancel doesn't work".

---

## Code Examples

### Verified: `cmd.get_view` returns 18 floats; `cmd.set_view` accepts a sequence
```python
# Source: tmp/pymol-src/modules/pymol/viewing.py:605-703 (get_view), :705-734 (set_view)
# get_view returns (line 702): r = r[0:3]+r[4:7]+r[8:11]+r[16:25]  -> 3+3+3+9 = 18 floats
# Layout (viewing.py:632-644):
#   0-8:   column-major 3x3 rotation (model -> camera)
#   9-11:  origin of rotation (camera space)
#   12-14: origin of rotation (model space)
#   15:    front clip plane distance
#   16:    rear clip plane distance
#   17:    orthoscopic flag / field of view
view = list(cmd.get_view())          # 18 floats, JSON-serializable as a list
# ...later, on load, AFTER on_enter replay:
cmd.set_view(view)                   # accepts string-or-sequence (viewing.py:729)
```

### Verified: `cmd.fetch` is sync + blocking, skips if file exists, lowercases the filename
```python
# Source: tmp/pymol-src/modules/pymol/importing.py:1323-1394 (fetch), :1149-1264 (_fetch)
# fetch(async_=0) -> _multifetch synchronously (importing.py:1386-1393); no progress callback
# _fetch skip-if-exists (importing.py:1211-1213): elif os.path.exists(file): url_list = []
# Filename: type='pdb' -> nameFmt='{code}.{type}' (importing.py:1172); code lowercased at :1200
#   -> cmd.fetch("4PFK", type="pdb", path=D) writes D/4pfk.pdb
#   -> cmd.fetch("2244", type="cid", path=D) writes D/cid_2244.sdf  (nameFmt '{type}_{code}.sdf', :1181)
# Failure signal: AssetManager.fetch_pdb raises RuntimeError on count_atoms<=0 (asset_manager.py:123-126)
```

### Verified: Node ending detection
```python
# Source: c14/story/model.py:251-252, 310-314
# Node.is_ending is None (non-ending) or one of "true"|"good"|"normal"|"bad"
# TurnResult.node is the current node (c14/engine.py:54-55)
turn = engine.choose(index)
if turn.node.is_ending is not None:
    tier = turn.node.is_ending      # "true" / "good" / "normal" / "bad"
    node_id = turn.node.id          # specific ending, e.g. "tca.true_ending"
    # -> achievement board: record ending + unlock tier achievement
```

### Verified: PyMOL user-data dir convention
```python
# Source: tmp/pymol-src/modules/pymol/plugins/installation.py:22-29
# def get_default_user_plugin_path():
#     if 'APPDATA' in os.environ:
#         return os.path.join(os.environ['APPDATA'], 'pymol', 'startup')   # Windows
#     return os.path.expanduser('~/.pymol/startup')                        # Linux/Mac
# -> user data (NOT plugin install) goes one level up + in a c14-tale-of-c/ subfolder:
#    ~/.pymol/c14-tale-of-c/   (Linux/Mac)   |   %APPDATA%/pymol/c14-tale-of-c/   (Windows)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `cmd.fetch` async-by-default (race) | `async_=0` sync by API default since PyMOL 2.3 | PyMOL 2.3.0 (wiki Fetch ChangeLog) | Sync fetch is the API default; still pass `async_=0` explicitly (defense). Bulk-download loop is sync + predictable. |
| `cmd.fetch` type default = pdb | type default = cif | PyMOL 1.8.0 (wiki Fetch ChangeLog) | Must pass `type='pdb'` for proteins (AssetManager already does — `asset_manager.py:122`). |
| `pmgqt`/Tk plugin UI | `pymol.Qt` (PyQt5) | PyMOL 2.x; `dynoplot.py` ported 2024 | All Phase 6 UI uses `from pymol.Qt import QtCore, QtGui, QtWidgets` (dynoplot.py:21). No Tk. |
| Plugin install = ??? | `~/.pymol/startup/` (Linux/Mac) / `%APPDATA%/pymol/startup/` (Windows) | `installation.py:22-29` | User data goes beside (not inside) the plugin install dir for reinstall survival. |

**Deprecated/outdated (do NOT use):**
- `pmgqt` / `Tkinter` imports — use `pymol.Qt` (spec + dynoplot.py:21).
- `cmd.create(obj, obj, 1, 1)` self-copy — destructive (03-RESEARCH.md §2; not relevant here but don't reinvent backup).
- Saving a `.pse` session for game state — Anti-Pattern 5 (`persist.py:1-9`); use JSON + on_enter replay.
- Hand-rolled `cmd.fetch` (bypassing AssetManager) — loses Pitfall-5 mitigations.

---

## Open Questions

1. **`cast.json` schema for "large vs bundled"** — the current `cast.json` is a 1-entry placeholder (`c14/data/cast.json`: a single `fixture_enzyme_1` with a `fixture` field). Phase 6 needs the schema extended to mark each enzyme's PDB as `"source": "bundled"` (small/critical, ships in zip) or `"source": "download"` (large, fetched via the bulk-download prompt) + a `"pdb_id"` field. The actual large-PDB list is NOT populated until Phase 7-9 (content phases). **Recommendation:** Phase 6 builds the bulk-download MECHANISM + the cast.json schema extension + the help cast-list read, but the real large-PDB list stays minimal/placeholder for the MVP (glucose needs only what Phase 7 populates). The planner should coordinate with the content phases so the schema is right before content lands.

2. **Bulk-download trigger: flag file vs missing-file check** — two viable detection strategies: (a) a marker file `user_data_path(".bulk_download_state.json")` written after the first successful bulk-download, or (b) per-file `os.path.exists(downloaded/pdb_id.lower()+".pdb")` check. **Recommendation:** prefer (b) — it's self-healing (if files are deleted, re-prompt), needs no marker to keep in sync, and re-runs are free (cmd.fetch skips existing). Use (a) ONLY if you need a "user dismissed the prompt" flag (e.g. "Don't ask again" — defer to Phase 10 polish). For Phase 6 MVP, (b) alone suffices.

3. **Additional PyMOL wiki links for DOC-03** — only 3 verified live 2026-08-29 (Alter→Iterate, H_Add, Fetch). Likely-useful additional links (Show, Select, Sort, Load, Scene) follow the standard `https://pymolwiki.org/index.php/<Title>` pattern but **MUST be webfetch-verified before ship** (no-fabrication rule). **Recommendation:** ship the 3 verified links for Phase 6 MVP; the planner adds more only with a live-fetch verification step in the plan. Mark unverified links "verify before use" — do NOT ship them on assumption.

4. **"Branches discovered" granularity** — ACH-01 says "branches discovered" as a collection. The current proposal records every unique `node.id` visited (a fine proxy). Alternative: record only CHOICE nodes visited (the actual "branches"). **Recommendation:** record all visited node ids (simpler, more complete); the achievement unlocked threshold (e.g. "explored 10 nodes") can be tuned in Phase 10. Flag the precise definition to the planner — it affects the schema's `branches_discovered` semantics.

5. **View-matrix capture timing** — capturing `cmd.get_view()` in `engine.save` captures the view AT SAVE TIME (mid-node). On load, the on_enter replay fires (which may include a `zoom` MolAction), THEN `cmd.set_view` overrides. This is correct (saved view wins). But if a node's on_enter changes the scene dramatically (e.g. loads a new structure that doesn't fit the old view), the restored view may frame empty space. **Recommendation:** acceptable for MVP — the saved view is what the player saw; document as a known limitation. Phase 10 polish could re-zoom-after-set_view for nodes whose on_enter has a zoom. Flag to the planner.

6. **`AchievementBoard` vs engine coupling** — the board is updated by the controller reading `TurnResult`, NOT by the engine (the engine stays pure-Python domain, no achievement concept). This keeps the engine WSL-testable. Confirm the controller (UI-as-adapter researcher's domain) calls `board.on_turn(turn, character, is_new_game)` after every `start`/`choose`/`apply_player_edit`. The exact call site is in the controller — coordinate so it's not missed (e.g. forgetting `is_new_game=True` on `engine.start` would miss the `first_game` + `glucose_tried` unlocks).

---

## Sources

### Primary (HIGH confidence — read from source + verified)
- `tmp/pymol-src/modules/pymol/importing.py` — `fetch` (L1323-1394), `_multifetch` (L1266-1321), `_fetch` (L1149-1264), sync `async_=0` path (L1386-1393), skip-if-exists (L1211-1213), `nameFmt` for pdb/cid (L1172,1181), code-lowercasing (L1200), filename build (L1206). Confirms blocking-fetch + no-progress-callback + idempotent-cache + lowercase-filename findings.
- `tmp/pymol-src/modules/pymol/viewing.py` — `get_view` (L605-703, return at L702 = 18 floats), `set_view` (L705-734, accepts string-or-sequence). Confirms view-matrix capture/restore + the SC#3 gap.
- `tmp/pymol-src/modules/pymol/plugins/installation.py` — `get_default_user_plugin_path` (L22-29): `~/.pymol/startup` (Linux/Mac) / `%APPDATA%\pymol\startup` (Windows). Confirms the user-data-dir convention + the "beside the plugin" recommendation.
- `tmp/pymol-src/modules/pymol/_gui.py` — L984 `os.path.expanduser('~/.pymol')`. Corroborates the `~/.pymol` convention.
- `tmp/pymol-src/modules/pymol/plugins/__init__.py` — L18 `~/.pymolpluginsrc.py`. Corroborates.
- `tmp/pymol-src/modules/pymol/invocation.py` — `get_user_config` (L211), `get_personal_folder` (L200-209). Confirms NO `cmd.get_user_path` API exists; the user-dir convention is filesystem-only.
- `Pymol-script-repo/plugins/dynoplot.py` — L21 `from pymol.Qt import QtCore, QtGui, QtWidgets` (ported 2024). Confirms the modern Qt plugin idiom.
- `c14/pymol_layer/asset_manager.py` (Phase 3) — `fetch_pdb` (L114-127) with Pitfall-5 mitigations + `RuntimeError` on `count_atoms<=0`. The bulk-download primitive.
- `c14/paths.py` (Phase 1) — `data_path` (L26-43) pure-resolver design; the model for `user_data_path`.
- `c14/persist.py` (Phase 2) — `SaveStore.save/load` (L38-65) + `makedirs` + `indent=2`. Confirms save/load is proven; the `view` field flows through `to_dict`/`from_dict` once added.
- `c14/engine.py` (Phase 2) — `GameEngine.__init__` injects `molaction_sink` (L83-88); `save`/`load` (L196-213) with on_enter replay (Pattern 6). Confirms where to inject `view_provider`/`view_applier` + that load rebuilds the scene.
- `c14/state.py` (Phase 2) — `GameState` fields (L46-64) + `to_dict`/`from_dict` (L66-114). Confirms the missing `view` field (SC#3 gap).
- `c14/story/model.py` (Phase 2) — `Node.is_ending` (L251-252,310-314), `TurnResult.node` (engine.py L54-55). Confirms achievement-unlock detection source.
- `.planning/phases/03-pymol-cmd-layer-asset-mgmt/03-RESEARCH.md` + `03-02-SUMMARY.md` — Phase 3 verified facts (Pitfall 5 mitigations, `async_=0` sync, count_atoms post-condition, downloaded/ gitignored).
- `.gitignore` — `c14/data/assets/downloaded/` confirmed gitignored (runtime cache, not committed).

### Secondary (MEDIUM confidence — webfetch verified live 2026-08-29)
- `https://pymolwiki.org/index.php/Alter` (redirects to Iterate) — verified live 2026-08-29; confirms `alter` + `sort` pattern (matches Phase 4 apply_edit mitigation).
- `https://pymolwiki.org/index.php/H_Add` — verified live 2026-08-29; confirms `h_add` is valence-only (NOT pH-aware) — grounds the curated-variant protonation approach.
- `https://pymolwiki.org/index.php/Fetch` — verified live 2026-08-29; confirms `async=0` default since PyMOL 2.3, `type=cif` default since 1.8.0, `fetch_path` defaults to cwd.

### Tertiary (LOW confidence — none; all claims traced to source or live-fetch)
- None. All PyMOL-API claims are `file:line`-cited; all wiki links are live-fetched.

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — all in-repo / PyMOL-source-verified; no new deps.
- Bulk-download flow (blocking fetch + sync loop): **HIGH** — `importing.py:1386-1393` + `:1215-1245` read directly; no progress callback confirmed by reading `_fetch`.
- View-matrix gap: **HIGH** — `state.py:46-64` (no view field) + `viewing.py:605,702` (18-float get_view) + `viewing.py:705` (set_view) all read directly.
- User-data path strategy: **HIGH** — `installation.py:22-29` read directly; `~/.pymol` convention corroborated by `_gui.py:984` + `plugins/__init__.py:18`.
- Achievement schema + unlock detection: **HIGH** — `Node.is_ending` + `TurnResult.node` read directly; schema is a design decision on verified types.
- PyMOL wiki links: **HIGH** for the 3 shipped (live-fetched 2026-08-29); additional links flagged "verify before use" (LOW until fetched).
- `cast.json` schema extension: **MEDIUM** — the need is clear (CAST-04 hybrid model) but the real large-PDB list lands in Phase 7-9, not Phase 6.

**Research date:** 2026-08-29
**Valid until:** 2026-09-28 (30 days — stable; PyMOL 2.5.0 API is fixed. Re-verify wiki links before ship (URLs can rot). Re-verify `cmd.fetch` behavior only if PyMOL is upgraded — line citations would shift.)

---

## Recommendations for the Planner

1. **Split the NEW work into ~3 focused plans** (wave structure TBD by planner):
   - **Plan A (foundation):** `c14/paths.user_data_path()` (pure-Python + WSL unit test) + `c14/state.py` `view` field (3 sites) + `c14/engine.py` `view_provider`/`view_applier` injection (backward-compatible: default `None` = no view capture, so Phase 2 tests stay green) + `c14/achievements.py` (pure-Python + WSL unit tests covering on_turn for each unlock type). NO Qt in this plan — keeps the testability boundary clean + lands the domain logic first.
   - **Plan B (UI dialogs):** the four `c14/ui/` dialogs (`bulk_download_dialog.py`, `achievements_dialog.py`, `save_load_dialogs.py`, `help_dialog.py`) + `c14/data/help.json` + `c14/data/cast.json` schema extension (`source` + `pdb_id` fields). Human-verify only (Qt can't run in WSL). Coordinate with the UI-as-adapter researcher's main-window plan so the "cast/help/save/load/achievement" buttons (SC#1) route to these dialogs.
   - **Plan C (integration + smokes):** controller wiring (inject `view_provider`/`view_applier`, call `board.on_turn` after each turn, bulk-download trigger on first play) + a headless smoke for the bulk-download loop's per-file logic (mock the network via a MockCmd that returns configured counts) + the human-verify checklist.

2. **Make the `view` field backward-compatible:** default `view=None` in `GameState.from_dict` so old Phase-2 saves load without crashing. Bump `version` to 2 if you want a migration marker, but `.get`-with-default is enough.

3. **Keep `engine.py` gate-clean:** inject view callbacks; do NOT import `pymol` in `engine.py`. The Phase 1 AST gate is non-negotiable. This is the same pattern as `molaction_sink` — no new precedent.

4. **Bulk-download UX docstring + human-verify checklist must state:** "progress is per-file (blocking fetch forbids per-byte); Cancel stops after the current file; Retry re-runs and skips already-downloaded files." This prevents a human-verify reviewer from flagging the per-file bar as a bug.

5. **Ship only the 3 verified wiki links** in `help.json` for Phase 6. Add a plan task "webfetch-verify any additional wiki links before commit" if the content phases want more. Do NOT let the plan ship unverified URLs.

6. **Coordinate with the parallel researchers:**
   - **Packaging researcher:** owns the plugin zip / `__init_plugin__` / `addmenuitemqt` / `~/.pymol/startup/` install. This research DEPENDS on the plugin being installed under `~/.pymol/startup/<plugin>/` (so `user_data_path` at `~/.pymol/c14-tale-of-c/` is a sibling, surviving reinstalls). Confirm the install location with them.
   - **UI-as-adapter researcher:** owns the main window + controller + the `molaction_sink` wiring. This research needs the controller to (a) inject `view_provider`/`view_applier` when constructing `GameEngine`, (b) call `board.on_turn(turn, character, is_new_game=True)` after `engine.start` and `is_new_game=False` after `choose`/`apply_player_edit`, (c) trigger the bulk-download dialog on first play, (d) route the cast/help/save/load/achievement buttons to these dialogs. Hand them the exact call-site contracts in Patterns 3 + 4.

7. **Don't scope DOC-01/DOC-02** (dramatic cast list + slogan) — those are Phase 9. Phase 6's `help.json` is ONLY editing pointers + wiki links (DOC-03). Resist the temptation to add a cast list now (the cast isn't populated yet — `cast.json` is a placeholder).

8. **Flag the view-matrix limitation to the human-verify reviewer:** a save/load round-trip restores the saved view, but if a node's on_enter loads a new structure, the restored view may frame empty space for that transition. Acceptable for MVP; Phase 10 polish can re-zoom.
