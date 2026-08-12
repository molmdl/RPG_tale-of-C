# Technology Stack

**Project:** C14: Tale of C — PyMOL 2.5.0 respiratory-pathway RPG plugin
**Researched:** 2026-08-12
**Overall confidence:** **HIGH** (core APIs verified line-by-line in `tmp/pymol-src/modules/pymol/`; only the PyMOL-bundled Python minor version and the optional-vendor protonation tools are MEDIUM/LOW)

---

## Verdict (one paragraph)

Build a **package-style PyMOL plugin** (a directory with `__init__.py`) using **only what PyMOL 2.5.0 already ships: PyQt5 via `pymol.Qt`, `pymol.Qt.utils`, numpy, and the `pymol.cmd` API.** No third-party libraries are needed for v1. Every gameplay requirement — text-choice UI, molecule editing, PDB/PubChem fetching, "reveal correct 3D model" restore, RNG-weighted stochastic steps, achievement save/load — is covered by the standard library + PyMOL's built-in API surface. Target **Python 3.6 syntax universally** (it's the WSL test-env constraint *and* guarantees compatibility with PyMOL's bundled interpreter). The single genuine gap is **physiological-pH protonation**: PyMOL's `h_add` is valence-based, not pH-aware — but the spec's lookup-table routing model absorbs this (hardcode reaction-relevant protonation states as lookup-table entries), so no external protonation library is required for v1.

---

## Recommended Stack

### Core Framework (all SHIPPED with PyMOL 2.5.0 — zero installs)

| Technology | Version | Purpose | Why | Conf. |
|------------|---------|---------|-----|-------|
| **PyMOL plugin runtime** | 2.5.0 (pinned by `chemtools-win10` conda env) | Host application + `cmd.*` molecular API | The deploy target is fixed. All molecular ops go through `pymol.cmd`. | HIGH |
| **PyQt5 via `pymol.Qt`** | whatever `pyqt` conda ships with PyMOL 2.5.0 | All GUI (text-choice panels, achievement board, help) | `pymol.Qt` is a wrapper that prefers PyQt5, then falls back to PySide2/PyQt4 (`tmp/pymol-src/modules/pymol/Qt/__init__.py:26-40`). It exports `QtCore`, `QtGui`, `QtWidgets`, and aliases `QtCore.Signal = QtCore.pyqtSignal`, `QtCore.Slot = QtCore.pyqtSlot`. Match `dynoplot.py`'s `from pymol.Qt import QtCore, QtGui, QtWidgets` exactly. | HIGH |
| **`pymol.Qt.utils`** | ships with PyMOL | Reusable Qt helpers (async, dialogs, fonts, .ui loader) | **Key discovery** — see dedicated section below. Provides `AsyncFunc`, `MainThreadCaller`, `PopupOnException`, `getSaveFileNameWithExt`, `getMonospaceFont`, `loadUi`. These cover async PDB download + GUI error handling with zero new deps. | HIGH |
| **numpy** | ships with PyMOL 2.5.0 (1.x-era) | Coordinate math only (centers, distances, RMSD if needed) | Available via `import numpy`. NOT used for RNG (see Decision D4). Version is whatever the conda env provides; we only need basic array ops, so any 1.x is fine. | HIGH |
| **Python stdlib** | 3.6.9 (WSL test env) | `json`, `random`, `os`, `sys`, `typing`, `collections`, `unittest`, `pathlib`, `hashlib`, `io` | Covers save/load (json), RNG (random.choices, 3.6+), testing (unittest). No third-party libs. | HIGH |

### PyMOL `cmd.*` APIs (verified in `tmp/pymol-src/modules/pymol/`)

| API | Source | Purpose | Conf. |
|-----|--------|---------|-------|
| `cmd.fetch(code, type=..., async_=1, path=...)` | `importing.py:1323` | Download PDB / PubChem / ligand dictionary — see D5/D6/D7 | HIGH |
| `cmd.download_chem_comp(resn)` | `internal.py:310` | Internal helper: download PDB Chemical Component Dictionary CIF for a residue name (same source as `fetch(type='cc')`) | HIGH |
| `cmd.load(filename, object, format=...)` | `importing.py:635` | Load local files (pdb/mol/mol2/sdf/xyz auto-detected by extension) | HIGH |
| `cmd.save(filename, selection, format=...)` | `exporting.py:782` | Save structures (pdb/sdf/mol/...) | HIGH |
| `cmd.h_add(selection, state, legacy)` | `editing.py:1216` | Add H by **valence** (NOT pH-aware) — see D7 | HIGH |
| `cmd.h_fill()` | `editing.py:1163` | Replace H on the atom/bond picked for editing (editor mode; for the "limited edits" feature) | HIGH |
| `cmd.show(rep, selection)` / `cmd.hide(rep, selection)` | `viewing.py:491` / `viewing.py:568` | Show/hide representations (the "specific residue representations at game stages" feature) | HIGH |
| `cmd.color(color, selection)` / `cmd.spectrum(...)` | `viewing.py:1858` / `viewing.py:2019` | Color residues/atoms (highlight the C14 hero, found residues, etc.) | HIGH |
| `cmd.get_view()` / `cmd.set_view(view)` | `viewing.py:605` / `viewing.py:705` | Save/restore camera matrix (the "restore correct 3D model" safety net) | HIGH |
| `cmd.delete(name)` / `cmd.alter` / `cmd.iterate` / `cmd.create` / `cmd.sort` | `commanding.py` / `editing.py` / `querying.py` / `creating.py` | Molecule editing, querying atom props, creating objects, re-sorting after edits | HIGH |
| `cmd.extend(name, func)` | `plugins/__init__.py:433` | Register a `cmd.` command from the plugin (optional — exposes game actions on the PyMOL command line) | HIGH |

### UI / Qt Building Blocks

| Component | Source | Purpose | Conf. |
|-----------|--------|---------|-------|
| `QtWidgets.QWidget` subclasses (hand-coded) | `dynoplot.py:28` | Main game window, panels | HIGH |
| `QtWidgets.QMainWindow` / `QDialog` | stdlib PyQt5 | Achievement board, save/load dialogs | HIGH |
| `QtWidgets.QListWidget` / `QComboBox` / `QPushButton` / `QTextEdit` | stdlib PyQt5 | Text-choice list, character select, action buttons, story text area | HIGH |
| `QtWidgets.QMessageBox` | stdlib PyQt5 / `pymol.Qt.utils.PopupOnException` | Endings, errors, confirmations | HIGH |
| `QtWidgets.QFileDialog` + `utils.getSaveFileNameWithExt` | `Qt/utils.py:227` | Save/load file pickers (auto-append extension) | HIGH |
| `utils.getMonospaceFont(size)` | `Qt/utils.py:247` | Monospaced text for PDB IDs / residue codes in the cast list | HIGH |
| `utils.loadUi(uifile, widget)` | `Qt/utils.py:267` | **Optional** Qt Designer `.ui` loading — use ONLY if you want visual layout; hand-coded QWidget is the dominant pattern in `Pymol-script-repo/plugins/` | HIGH |

### Data & I/O

| Technology | Purpose | Why | Conf. |
|------------|---------|-----|-------|
| **JSON** (`json` stdlib) | Save/load game state + achievement board | Human-readable, stdlib, 3.6-compatible, diff-friendly. The `.gitignore` already rules out `*.npy`/`*.npz` (binary numpy dumps) — see D2. | HIGH |
| **Bundled PDB/CIF files** in `data/pdb/` | Small/critical structures shipped with the plugin (spec: "hybrid: bundle small, bulk-download large") | Avoids network on every encounter; kept under plugin package dir; loaded via `cmd.load()`. | HIGH |
| **`cmd.fetch(type='pdb'/'cif')`** | Large structures: one-time bulk download prompt before first play | `async_=1` for non-blocking download; caches to `fetch_path`. | HIGH |

### RNG & State

| Technology | Purpose | Why | Conf. |
|------------|---------|-----|-------|
| **`random.Random(seed)` + `random.choices(weights=...)`** | RNG-weighted stochastic steps (TCA shuffle, etc.); seedable for classroom reproducibility | stdlib, **`random.choices` was added in Python 3.6** — exactly our test-env version. No numpy needed. See D4. | HIGH |

### Dev & Test Tooling (WSL side — no installs allowed)

| Tool | Purpose | Why | Conf. |
|------|---------|-----|-------|
| `python3.6 -m py_compile <file>` | Syntax check pure-Python modules | AGENTS.md-mandated; runs in WSL without PyMOL | HIGH |
| `python3.6 -m unittest` / `python3.6 -m pytest` | Unit-test pure-Python (non-PyMOL) modules | Only for modules that do NOT import `pymol`/`pymol.Qt` at module load | HIGH |
| `C:\src\run-conda-pymol.bat -cq <script.py>` (via `cmd.exe`, wrapped in `timeout 90 ... \| tail -50`) | Headless smoke-test pure-`cmd.*` scripts | Closes the WSL/Windows gap for command-only paths; `-cq` = no GUI quiet. Stage scripts to a `/mnt/c/...` path first (PyMOL resolves relative paths against cmd.exe cwd). | HIGH |
| `git` (allowed in `opencode.json`) | Version control | — | HIGH |

---

## Plugin Packaging & Install Mechanism  *(critical — addresses "how does a user actually install this plugin?")*

**Source of truth: `tmp/pymol-src/modules/pymol/plugins/__init__.py` + `installation.py` + `managergui_qt.py`.**

### Discovery (how PyMOL finds plugins)
- On startup, `plugins.initialize()` scans `startup.__path__` for (a) `.py` files and (b) directories containing `__init__.py`. Names starting with `.` or `_` are skipped (`__init__.py:384-385`).
- For each found module, `PluginInfo.load()` does `__import__(mod_name)` then calls **`__init_plugin__(pmgapp)`** if present, else `__init__(pmgapp)` if it's a plain function (`__init__.py:320-324`).
- **Modern contract:** define `def __init_plugin__(self):` at module top level; inside it call `from pymol.plugins import addmenuitemqt; addmenuitemqt('C14: Tale of C', launch_callback)`. This is exactly `dynoplot.py:445-447`.

### Install paths (where the plugin lives)
- **Linux:** `~/.pymol/startup/`
- **Windows:** `%APPDATA%\pymol\startup\`
- Plus a non-user path from `$PYMOL_DATA/startup`.
- (`installation.py:22-29`)

### Install formats supported (`installation.py`)
1. **Single `.py` file** → copied to `<plugdir>/<name>.py`. (Fine for tiny plugins; **NOT us** — we have multiple modules + bundled PDB data.)
2. **`.zip` / `.tar.gz` containing a package** with `<name>/__init__.py` → extracted to `<plugdir>/<name>/`. **← This is our shape.**
3. **Directory with `__init__.py`** → copied as a package.

### How a user installs THIS plugin (the real answer)
1. Package the plugin as a directory `c14_tale_of_c/` whose top-level `__init__.py` defines `__init_plugin__`. Bundle submodules (`story/`, `game/`, `data/pdb/`, ...) inside it.
2. Zip it as `c14_tale_of_c.zip` (zip must contain exactly one package dir with `__init__.py`; `installation.py:118-136` enforces "single package" — filter out `tests/` dirs if needed).
3. In PyMOL GUI: **Plugin → Plugin Manager → "Install New" tab → "Browse..." (`b_local`) → select `c14_tale_of_c.zip`**. PyMOL extracts it to the user startup dir and calls `info.load(force=1)` (`managergui_qt.py:45`, `installation.py:342`).
4. Menu item **"C14: Tale of C"** appears under the **Plugin** menu. Restart PyMOL if it doesn't show immediately.
5. **Developer shortcut (no zip):** copy/symlink the `c14_tale_of_c/` directory directly into `~/.pymol/startup/` (or `%APPDATA%\pymol\startup\`). PyMOL auto-discovers it on next launch. Best for iteration.

### Plugin metadata (optional but recommended)
`PluginInfo.get_metadata()` (`__init__.py:193-210`) parses a `# Key: Value` header block at the top of the file. Add:
```python
# Title: C14: Tale of C
# Version: 0.1.0
# Author: <name>
# Citation-Required: No
```
This shows in the Plugin Manager "Info" dialog and enables version-compare on reinstall (`installation.py:254-273`).

### Naming constraint
Module/package name must be a valid Python identifier with **no dots** (`installation.py:83-87`). Use `c14_tale_of_c` (or `tale_of_c`), **not** `C14.Tale.of.C`.

---

## Python 3.6 Compatibility Rules  *(critical — confirmed by sibling-project lessons)*

**Target Python 3.6 syntax universally.** This is the WSL test-env version (3.6.9) AND guarantees compatibility with PyMOL's bundled interpreter (whatever it is). The conda-forge `pymol-open-source-feedstock` `meta.yaml` does **not** pin a Python version (it uses the conda env's default), so the bundled version is env-determined. PyMOL 2.5.0 is a 2021-era release; its conda builds typically bundle Python 3.8-3.9, but **this is unverified from WSL** (MEDIUM confidence — the `chemtools-win10` env's exact interpreter can't be queried without running the Windows .bat). Targeting 3.6 is safe regardless.

**Allowed (3.6+):** f-strings, `typing.List`/`Optional`/`Tuple`/`Dict`, `from __future__ import annotations` (PEP 563, 3.7+ — AVOID), `random.choices` (3.6+), `secrets` module, `pathlib`, `os.fspath` (3.6+), dict insertion-order (3.6 implementation detail, 3.7 guarantee — see below).

**AVOID (3.7+/3.8+ syntax — confirmed failure mode):**
- **Walrus operator `:=`** (3.8+) — a sibling PyMOL-plugin project hit this exact failure (`:=` rejected by 3.6.9 during `py_compile`). Hard rule.
- **f-string self-documenting `=`** (e.g. `f"{x=}"`) (3.8+).
- **Positional-only params `/`** (3.8+).
- **`from __future__ import annotations`** (3.7+) — not needed; just use `typing` string forms if worried.
- **`dataclasses`** (3.7+) — use plain classes or `typing.NamedTuple` (3.6+ works) / `collections.namedtuple` instead.
- **`dict` insertion-order as a *language guarantee*** — it's only an *implementation detail* in 3.6 (guaranteed in 3.7). If order matters for save-file stability, use `collections.OrderedDict` explicitly (a sibling project did exactly this for its registry store, to make the contract explicit on 3.6).

**Two-interpreter reality (design implication):** Pure-Python modules (no `import pymol`) are unit-tested in WSL on 3.6.9. Modules importing `pymol`/`pymol.Qt` only run inside PyMOL's bundled interpreter and are **human-verify checkpoints** (Qt needs a real display; WSL cannot run the GUI). Structure the code so the **pure logic (story graph, RNG, lookup table, save/load schema, achievements) is import-clean of `pymol`** and testable; the **PyMOL-coupled layer (fetch/load/show/edit) is thin and human-verified**.

---

## Decision Deep-Dives (downstream consumer's explicit questions)

### D1 — UI library: PyQt5 via `pymol.Qt`. Why not Tkinter / Pmw / pmgqt?
**Decision:** `from pymol.Qt import QtCore, QtGui, QtWidgets` — exactly as `dynoplot.py:21`. Hand-code `QtWidgets.QWidget` subclasses.

**Why:** `pymol.Qt/__init__.py` is the supported, version-flexible wrapper (PyQt5 → PySide2 → PyQt4 fallback). The spec **mandates** the modern Qt interface. `Pymol-script-repo/plugins/rendering_plugin.py` and `resicolor_plugin.py` are **anti-examples**: they use the legacy `def __init__(self):` + `self.menuBar.addmenuitem(...)` + Tkinter/Pmw pattern. Do NOT copy them. `dynoplot.py` (ported to PyQt 2024 by Thomas Holder, the plugins-engine author) is the canonical modern template.

**Why not Tkinter/Pmw directly:** (a) forbidden by spec; (b) the Plugin Manager and modern PyMOL GUI are Qt-based — a Tk plugin window is a second toolkit running alongside Qt, fragile; (c) `pymol.Qt.utils` helpers (async, dialogs) only exist for Qt.

### D2 — Save format: JSON. Why not .pse / .npy / pickle?
**Decision:** `json` (stdlib) for game state + achievements. `cmd.get_view()`/`set_view()` for camera; re-fetch + re-apply reps for the 3D scene (store the *recipe* in JSON, not a binary blob).

**Why JSON:**
- Stdlib, 3.6-compatible, no dep.
- Human-readable + diff-friendly (educators can inspect a saved game).
- The `.gitignore` already excludes `*.npy`/`*.npz` (binary numpy dumps) — a strong signal that the repo owner expects non-binary save artifacts.
- Cross-version safe (unlike `pickle`, which breaks across Python/numpy versions — a real risk given the two-interpreter reality).

**Why not `.pse` (PyMOL session file):** `.pse` is a binary, PyMOL-version-specific dump of the whole scene. It's not for *game* state (story node, RNG seed, achievements), it's huge, and it couples saves to the exact PyMOL version. Use it only as an optional "export current view" convenience, never as the primary save format.

**Why not `pickle`:** breaks across Python 3.6↔3.8/3.9 and across numpy versions; security risk loading untrusted saves. JSON + explicit schema is safe and portable.

**Schema sketch (in JSON):** `version`, `character`, `story_node_id`, `rng_seed`, `rng_state` (Random.getstate() is picklable but serialize its tuple form into JSON-compatible lists), `achievements` (list), `visited_nodes` (list), `edit_history` (list), `current_view` (list from `cmd.get_view()`), `loaded_objects` (list of `{pdb_id, reps, colors}` so a load can re-fetch + re-apply).

### D3 — Async / non-freezing GUI: shipped `pymol.Qt.utils`, no external async lib
**Key discovery (`Qt/utils.py`):** PyMOL ships utilities that remove the need for any third-party async/concurrency library:
- **`AsyncFunc(func, returnslot, finishslot)`** (`utils.py:98`) — decorator/QThread to run a function off the GUI thread. **Use this for the one-time bulk PDB download prompt** so the GUI doesn't freeze. Signals: `returned(result)`, `finished(result, exception)`.
- **`MainThreadCaller`** (`utils.py:145`) — call a GUI function from a worker thread (blocks until the main thread executes it). **Use this when the async download worker needs to touch Qt widgets.**
- **`PopupOnException`** (`utils.py:311`) — context manager / decorator that shows a `QMessageBox` on any exception. Wrap risky `cmd.*` call sequences for clean user-facing errors.
- **`UpdateLock`** (`utils.py:4`) — prevent circular Qt signal/slot update loops (relevant if multiple widgets react to the same game state).

Additionally, `cmd.fetch(..., async_=1)` itself downloads in the background (`importing.py:1382-1387`). So the bulk-download flow = `cmd.fetch(list_of_codes, async_=1, path=bundle_dir)` + an `AsyncFunc` wrapper for progress UI.

### D4 — RNG: stdlib `random`, NOT numpy
**Decision:** `random.Random(seed)` with `random.choices(population, weights=weights, k=1)`.

**Why stdlib `random`:**
- **`random.choices` was added in Python 3.6.0** — exactly our test env. It's the precise API for weighted stochastic choice (TCA shuffle, branch rolls).
- Seedable + reproducible: `rng = random.Random(seed)`; persist/restore via `rng.getstate()`/`rng.setstate()`. Perfect for "seedable for classroom reproducibility."
- No dep, no numpy-version coupling.
- The game does **discrete story-step rolls**, not bulk numerical simulation — numpy's vectorized RNG is overkill and adds a version-coupling surface (numpy 1.x `RandomState` vs 1.17+ `default_rng`).

**When numpy RNG would be appropriate:** only if we later add bulk statistical analytics (e.g., "simulate 10k TCA runs"). Not in v1 scope.

**Seed handling:** store the seed in the JSON save (D2) and re-seed on load for reproducible replay. For "classroom mode," expose a seed field in the New Game dialog.

### D5 — PDB acquisition: `cmd.fetch` (hybrid bundle + bulk-download)
**Decision:** Bundle small/critical structures in `data/pdb/` (loaded via `cmd.load`); large structures via `cmd.fetch(codes, type='pdb'|'cif', async_=1)` triggered by a one-time prompt.

**Verified API (`importing.py:1323`, `importing.py:1115-1147`):**
- `cmd.fetch(code, name, type='pdb', async_=1, path=fetch_path)` — downloads from `https://files.rcsb.org/download/{code}.{type}.gz` (RCSB) by default; `type='cif'` (default since 1.7.6) for mmCIF; supports a **list** of codes; supports **5-letter single-chain codes** like `'1a00A'`; **caches to `path`** (skips download if file exists, `importing.py:1211-1213`).
- `async_=1` runs the download off the command line (`importing.py:1386-1387`); combine with `AsyncFunc` (D3) for progress UI.
- Set `cmd.set('fetch_path', <bundle_dir>)` so downloads land next to the bundled files (and persist across sessions).

**Bulk-download prompt flow:**
1. On first launch (or first New Game), check `data/pdb/bulk/` for the required large-structure files.
2. If missing, show a `QMessageBox`/dialog: "This game needs ~X MB of PDB structures. Download now? (one-time)".
3. On confirm, `cmd.fetch(big_list, async_=1, path=bulk_dir)` wrapped in `AsyncFunc` with a progress bar.
4. Gate gameplay start on the `finished` signal.

**Why `cmd.fetch` and not `requests`/`urllib`:** `cmd.fetch` already handles RCSB/PDBe/PDBj hosts, gzip, caching, async, and PyMOL's internal locking. Writing our own HTTP would duplicate all of that and risk breaking PyMOL's thread model. `requests` isn't shipped anyway (would need vendoring).

### D6 — Small molecules from PubChem: `cmd.fetch(code, type='cid')` (built-in!)
**Verified (`importing.py:1138-1140`, `importing.py:1179-1181`):** `cmd.fetch('5793', type='cid')` downloads the 3D SDF from `https://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?cid=5793&disopt=3DSaveSDF` and loads it as a PyMOL object named `cid_5793`. `type='sid'` fetches by PubChem Substance ID. No external library.

**Decision:** Use `cmd.fetch(<pubchem_cid>, type='cid')` for PubChem-sourced small molecules; `cmd.load(local.sdf)` for any pre-bundled SDF/MOL. `cmd.save(..., format='sdf')` can export if needed.

**Note:** PubChem CID lookups require knowing the CID for each substrate (e.g., glucose CID 5793, ethanol 702). These must be **human-verified per-claim** (spec's no-fabricated-science rule) before going into the lookup table — flag every CID + name mapping for the per-claim checkpoint.

### D7 — Protonation: built-in `h_add` + PDB CCD + lookup table (NO external lib for v1)
**The real situation (`editing.py:1216-1241`):** PyMOL's `cmd.h_add(selection)` adds hydrogens **based on current bond valences**. Its own docstring warns: *"PDB files do not normally contain bond valences for ligands and other nonstandard components, it may be necessary to manually correct ligand conformations before adding hydrogens."* It is **NOT pH-aware** — it does not compute His tautomers, Asp/Glu charge states, or pH-dependent protonation. `cmd.h_fix` is explicitly "unsupported" (`editing.py:1195-1202`). There is **no physiological-pH protonation engine in pymol-open-source.**

**Decision (meets the spec's "physiological pH or reaction-relevant, or user-adjustable" without a new dep):**
1. **Default for small-molecule substrates:** `cmd.fetch(resname, type='cc')` — fetches the **PDB Chemical Component Dictionary** idealized ligand from `https://files.rcsb.org/ligands/download/{code}.cif` (`importing.py:1143-1146`; also `cmd.download_chem_comp(resn)` at `internal.py:310`). The CCD provides the **canonical/standard protonation state** for each ligand — the most authoritative built-in source. This satisfies "physiological/reaction-relevant by default" for substrates.
2. **Default for proteins:** most PDB structures lack H entirely; `cmd.h_add` adds them by valence for visual completeness. Acceptable for an educational visualization (not a pKa study).
3. **Reaction-relevant protonation:** hardcode the specific protonation states that matter for each enzymatic step as **lookup-table entries** — the spec's edit-routing model is already a lookup table, so protonation states are just more entries. This sidesteps needing a pH-protonation engine.
4. **User-adjustable:** the spec's "limited edits" feature already lists "protonation-state changes" as an edit type — expose `cmd.h_add`/`cmd.h_fill`/`cmd.remove` on the picked atom via the existing edit mechanism. This is the "user-adjustable" path.

**If higher-fidelity pH protonation becomes necessary later (v1.5/v2):** the candidates to **vendor** under `./3rd_party_lib/` (gitignored) are:
- **PROPKA** (pKa prediction) — pure Python; **license and 3.6-compatibility UNVERIFIED — LOW confidence, needs a dedicated research task when that phase is planned.**
- **Dimorphite-DL** (rule-based pH protonation, ~lightweight) — same caveat.
- **RDKit** — heavy C++ dep; **avoid** (see "What NOT to use").

**Do NOT vendor any of these in v1.** The lookup-table approach is sufficient, scientifically safer (hardcoded states are human-verified per-claim, satisfying the no-fabricated-science rule), and keeps the plugin install trivial.

### D8 — "Reveal correct 3D model" / restore safety net
**Decision:** A JSON "scene recipe" per story node: `{pdb_id, chain, focus_selection, show_reps: [...], hide_reps: [...], colors: {...}, view: cmd.get_view()}`. **Restore** = `cmd.fetch`/`cmd.load` the structure (or re-use the already-loaded object) → `cmd.hide('everything', obj)` → re-apply `show`/`color` → `cmd.set_view(view)`. Verified APIs: `show`/`hide`/`color`/`get_view`/`set_view` (all in `viewing.py`, line-cited above).

**Why a recipe not a binary snapshot:** reproducible across PyMOL versions, human-auditable, and small. The "limited edits" the player made are simply discarded by re-applying the canonical recipe — exactly the "restore correct 3D model for smooth gameplay" the spec asks for.

---

## What NOT to Use (and why)

| Don't use | Why not | Use instead |
|-----------|--------|-------------|
| **Tkinter / Pmw / `pmgqt` / legacy `def __init__(self)`** | Spec-forbidden legacy; `rendering_plugin.py`/`resicolor_plugin.py` are anti-examples. Modern PyMOL GUI is Qt. | `pymol.Qt` (`QtCore`/`QtGui`/`QtWidgets`) + `__init_plugin__` + `addmenuitemqt` (per `dynoplot.py`) |
| **`requests` / `urllib` for PDB/PubChem** | Not shipped; duplicates `cmd.fetch`'s host/caching/async/locking logic; risks breaking PyMOL's thread model. | `cmd.fetch(type='pdb'/'cif'/'cid'/'cc', async_=1)` |
| **`pickle` for saves** | Breaks across Python 3.6↔3.8/3.9 + numpy versions; unsafe loading untrusted saves. | `json` (D2) |
| **`.pse` as primary save** | Binary, PyMOL-version-specific, huge; not for game state. | JSON for game state; `.pse` only as optional "export view" |
| **`*.npy`/`*.npz` saves** | Gitignored (`.gitignore`); binary + numpy-version-coupled. | JSON |
| **numpy RNG for story steps** | Overkill for discrete weighted choice; adds numpy-version surface; `random.choices` (3.6+) is the exact fit. | `random.Random(seed).choices(weights=...)` |
| **Walrus `:=`, f-string `=`, positional-only `/`, `dataclasses`, `from __future__ import annotations`** | 3.7+/3.8+ syntax — confirmed to fail `py_compile` on 3.6.9 (sibling-project failure). | `typing.NamedTuple`/`namedtuple`, plain classes, `typing.List[...]` |
| **RDKit (vendored or otherwise)** | Heavy C++ dep; overkill for v1 (no cheminformatics needed — the lookup table replaces a chemistry engine); huge vendoring burden. | Lookup table + `cmd.fetch(type='cc')` for canonical ligand protonation (D7) |
| **Any web framework / server** | Desktop PyMOL plugin, not a web app. `pymol.rpc`/`pymolhttpd` exist but are irrelevant. | — |
| **`pymol.Qt.utils.loadUi` + Qt Designer `.ui` files** as the *primary* UI approach | Works, but the dominant plugin pattern is hand-coded `QtWidgets.QWidget` (see all of `Pymol-script-repo/plugins/`). `.ui` adds a toolchain dependency. | Hand-code QWidget subclasses; reach for `loadUi` only if a complex form warrants visual layout. |
| **`pip install` anything silently** | Spec + AGENTS.md forbid; `opencode.json` makes `pip*` ask. | Anything beyond stdlib + `pymol.Qt` + numpy → write to a file, get human approval, user installs or agent vendors under `./3rd_party_lib/` (gitignored) with license noted. **Not needed for v1.** |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why not |
|----------|-------------|-------------|---------|
| GUI toolkit | PyQt5 via `pymol.Qt` | PySide2 via `pymol.Qt` | `pymol.Qt` prefers PyQt5 first; PyMOL 2.5.0 conda ships `pyqt`. Pinning to PyQt5 (the wrapper's first choice) matches `dynoplot.py`. |
| RNG | stdlib `random` | numpy `RandomState`/`default_rng` | Discrete story rolls don't need vectorized RNG; stdlib removes a version surface. |
| Save format | JSON | pickle / .pse / .npy | Portability, safety, gitignore rules (D2). |
| PDB download | `cmd.fetch` | `requests`+`urllib` | Duplicates built-in; not shipped; thread-unsafe w.r.t. PyMOL. |
| PubChem | `cmd.fetch(type='cid')` | PubChem REST + own parser | Built-in already hits PubChem's SDF endpoint; no parser to maintain. |
| Protonation (v1) | `h_add` + CCD + lookup table | PROPKA / Dimorphite-DL / RDKit | No dep; scientifically safer (human-verified hardcoded states); install stays trivial. Revisit in v1.5/v2 if needed. |
| Async | `pymol.Qt.utils.AsyncFunc`/`MainThreadCaller` + `cmd.fetch(async_=1)` | third-party async lib | Shipped utilities cover the GUI-non-freeze use case; no dep. |
| Plugin shape | package dir + zip install | single `.py` file | We have multiple modules + bundled PDB data → package is the supported shape (`installation.py`). |
| UI build | hand-coded QWidget | Qt Designer `.ui` + `loadUi` | Dominant plugin pattern is hand-coded; avoids Designer toolchain. |

---

## Installation  *(note: we do NOT `pip install` — this is the plugin install path + the optional-vendor path)*

### Plugin install (end user)
```bash
# Developer iteration (no zip): drop/symlink the package into the user startup dir
# Linux:
ln -s /abs/path/to/c14_tale_of_c ~/.pymol/startup/c14_tale_of_c
# Windows (from cmd or explorer): copy c14_tale_of_c -> %APPDATA%\pymol\startup\c14_tale_of_c

# Distributable: zip the package (must contain exactly one top-level dir with __init__.py)
cd /abs/path/to
zip -r c14_tale_of_c.zip c14_tale_of_c -x 'c14_tale_of_c/tests/*'
# Then in PyMOL: Plugin -> Plugin Manager -> Install New -> Browse -> c14_tale_of_c.zip
```

### Optional dependency (ONLY if a future phase proves a real need)
Per AGENTS.md/spec, do NOT `pip install`. If a library becomes necessary:
1. Write the candidate + license + 3.6-compat note to a file (e.g., `3RD_PARTY_REQUESTS.md`).
2. Get explicit human approval.
3. User installs in `chemtools-win10`, OR agent vendors a local copy under `./3rd_party_lib/` (gitignored per `.gitignore` line 13) with its LICENSE copied in.
4. State whether the user needs a Linux env or can keep the "WSL calls cmd.exe" headless approach.

**v1 needs none of this** — stdlib + `pymol.Qt` + `pymol.Qt.utils` + numpy + `pymol.cmd` cover every requirement.

---

## WSL/Windows Verification Path (built into the stack choices)

Every stack choice above respects the three verification tiers from AGENTS.md:

| Tier | What | Tooling chosen |
|------|------|----------------|
| **Pure-Python** (no `pymol` import) | story graph, RNG, lookup table, save schema, achievements | `python3.6 -m py_compile` + `unittest` in WSL — stdlib only (json, random, typing) makes this clean |
| **Pure `pymol.cmd.*`** (no Qt) | fetch/load/show/color/h_add scripts | `timeout 90 cmd.exe /c "C:\src\run-conda-pymol.bat -cq staged\script.py" 2>&1 \| tail -50` (stage to `/mnt/c/...` first). `cmd.fetch(async_=0)` for deterministic headless runs. |
| **Qt / GUI** | the plugin window, dialogs, achievement board | human-verify in a real Windows PyMOL session — **cannot be automated from WSL**. `pymol.Qt.utils.PopupOnException` + `AsyncFunc` are chosen specifically because they're the supported way to do this in a Qt plugin. |

**Implication for stack:** no choice above requires running Qt from WSL. The pure-Python/logic tier is deliberately import-clean of `pymol` so it's fully unit-testable on 3.6.9.

---

## Sources (with confidence levels)

| Source | Used for | Confidence |
|--------|----------|------------|
| `tmp/pymol-src/modules/pymol/plugins/__init__.py` (PyMOL 2.5.0 source) | plugin discovery, `__init_plugin__`, `addmenuitemqt`, `PluginInfo`, autoload | **HIGH** (read in full) |
| `tmp/pymol-src/modules/pymol/plugins/installation.py` | install paths, zip/package/single-file install, metadata, name validation | **HIGH** (read in full) |
| `tmp/pymol-src/modules/pymol/plugins/managergui_qt.py` | Plugin Manager UI buttons (`b_local`→install), confirm-network dialog | **HIGH** (read lines 1-90) |
| `tmp/pymol-src/modules/pymol/Qt/__init__.py` | `pymol.Qt` wrapper: PyQt5-first, exports, Signal/Slot aliases | **HIGH** (read in full) |
| `tmp/pymol-src/modules/pymol/Qt/utils.py` | `AsyncFunc`, `MainThreadCaller`, `PopupOnException`, `getSaveFileNameWithExt`, `getMonospaceFont`, `loadUi`, `UpdateLock` | **HIGH** (read in full) |
| `tmp/pymol-src/modules/pymol/importing.py:1323` (`fetch`) + `:1115-1147` (hosts) + `:1149-1230` (`_fetch`) | `cmd.fetch` signature, RCSB/PDBe/PDBj/PubChem/CCD URLs, `cid`/`sid`/`cc` types, async, caching | **HIGH** (line-verified) |
| `tmp/pymol-src/modules/pymol/internal.py:310` (`download_chem_comp`) | CCD CIF download helper | **HIGH** (read in full) |
| `tmp/pymol-src/modules/pymol/importing.py:635` (`load`) | `cmd.load` formats (pdb/mol/mol2/sdf/xyz) | **HIGH** (line-verified) |
| `tmp/pymol-src/modules/pymol/exporting.py:782,991,994` (`save`, `get_str`) | `cmd.save` formats incl. sdf/mol | **HIGH** |
| `tmp/pymol-src/modules/pymol/editing.py:1163,1216,1195` (`h_fill`,`h_add`,`h_fix`) | protonation APIs + their valence-based limitation (h_add docstring) | **HIGH** (line-verified) |
| `tmp/pymol-src/modules/pymol/viewing.py:491,568,605,705,1858,2019` | show/hide/get_view/set_view/color/spectrum | **HIGH** (line-verified) |
| `Pymol-script-repo/plugins/dynoplot.py` | canonical modern-Qt plugin template (`__init_plugin__`+`addmenuitemqt`+`pymol.Qt`+hand-coded QWidget) | **HIGH** (read in full) |
| `Pymol-script-repo/plugins/rendering_plugin.py`, `resicolor_plugin.py` | legacy Tk/Pmw anti-examples | **HIGH** (read in full) |
| `.gitignore` | confirms `3rd_party_lib/**`, `tmp`, `*.npy`/`*.npz` gitignored → JSON save, vendoring path | **HIGH** |
| `conda-forge/pymol-open-source-feedstock` `meta.yaml` (current = v3.1.0) | PyMOL conda runtime deps = `pyqt` + `pmw` + numpy; **no pinned Python** (env-determined) | **MEDIUM** (feedstock is latest, not 2.5.0; but dep shape is stable) |
| Sibling project "bioCHEMeleon" tool-output logs (in shared opencode tool-output dir) | corroboration of 3.6.9 syntax constraints (walrus/f-string=/positional-only failures), WSL/Windows verification tiers, `py_compile`+`unittest`+headless-`run-conda-pymol.bat` pattern | **MEDIUM** (not primary docs; cross-session logs — used only to corroborate AGENTS.md, not as sole source) |
| PyMOL 2.5.0 bundled Python version | "2021-era conda build, likely 3.8-3.9; unverified from WSL" | **MEDIUM** (inferred from release era; not directly queried) |
| PROPKA / Dimorphite-DL license + 3.6-compat | candidates for v1.5/v2 protonation vendoring | **LOW** (not investigated; flagged for a dedicated research task when that phase is planned) |

---

## Gaps to Address Later (flagged for phase-specific research)

- **PROPKA / Dimorphite-DL / PDB2PQR**: license terms, Python 3.6 compatibility, vendoring footprint — **only if a phase proves the lookup-table protonation model is insufficient.** Not needed for v1.
- **Exact Python minor version in `chemtools-win10`**: confirm in a real Windows session (`import sys; print(sys.version_info)` inside PyMOL) during the first human-verify checkpoint. Doesn't change the 3.6-syntax recommendation but removes the MEDIUM-uncertainty.
- **PubChem CID → molecule-name mapping**: every CID used must pass the human per-claim science-approval checkpoint (spec's no-fabricated-science rule). The stack supports it; the *content* is a research/approval task, not a stack task.
- **PDB cast list (~20+ structures)**: which PDB IDs, resolutions, and citations — content research with human approval, not stack research. The stack (`cmd.fetch`/`cmd.load` + bundled `data/pdb/`) supports whatever list is approved.
