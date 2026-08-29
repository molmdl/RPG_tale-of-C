# Phase 6: Qt UI + Minimal Playable MVP — Research (Qt Plugin PACKAGING + ENTRY-POINT)

**Researched:** 2026-08-29
**Domain:** PyMOL 2.5.0 plugin loading, menu registration, and Plugin Manager packaging (PLGN-01, PLGN-02)
**Confidence:** HIGH (every API signature verified against `tmp/pymol-src/modules/pymol/` with file:line citations; entry-point pattern corroborated by 3 reference plugins)
**Scope note:** This is ONE of three parallel Phase-6 research efforts. It covers ONLY the plugin install / menu-registration / packaging architecture (PLGN-01, PLGN-02). It does NOT cover the UI-as-adapter architecture or persistence/achievements — those are sibling research docs. Do not duplicate their work.

## Summary

Phase 6 must make `c14` loadable as a PyMOL 2.5.0 plugin: PyMOL imports the package, calls a single `__init_plugin__(pmgapp)` function, and that function registers a "RPG: Tale of C" menu item via `addmenuitemqt`. The entire contract is already implemented inside PyMOL's open-source plugin engine (`tmp/pymol-src/modules/pymol/plugins/`); the project's job is to match the contract, not to invent one.

Three findings dominate the design and are HIGH confidence:

1. **The entry-point contract is fixed.** PyMOL's `PluginInfo.legacyinit` (`plugins/__init__.py:302-324`) calls `mod.__init_plugin__(pmgapp)` if present (else falls back to a `__init__(pmgapp)` of type `FunctionType`). The argument `pmgapp` is the PMGApp instance; **modern Qt plugins ignore it** and register through `addmenuitemqt` instead. This is corroborated verbatim by `dynoplot.py:445-447`, `optimize.py:29-31`, and `outline.py:29-31`.

2. **The lazy-delegation pattern is FORCED by the AST gate, not optional.** `tools/check_imports.py` scans `c14/__init__.py` (it lives at the `c14/` root, which is NOT in `SKIP_DIRS`). The gate uses `ast.walk`, which recurses into function bodies — so EVEN a function-local `import pymol.plugins` inside `c14/__init__.py` is flagged (verified empirically: count=1). The ONLY gate-clean way for `c14/__init__.py` to reach the Qt layer is a **relative import** `from .ui import plugin_entry` (the name `ui` is not in `BANNED_TOP`; verified not flagged). This is exactly what the Phase-1 docstring anticipated ("lazily delegate to `c14/ui/plugin_entry.py`"), and `c14/ui/` is gate-exempt (`SKIP_DIRS = {"pymol_layer", "ui", "__pycache__"}`).

3. **PLGN-02's "package dir → .zip → startup/" model is real and exactly specified.** `installation.py:90-143` (`extract_zipfile`) and `installation.py:186-345` (`installPluginFromFile`) define the zip layout contract precisely: the zip must contain exactly one package directory with `__init__.py` at its root (Case 1: `c14/__init__.py`), optionally wrapped in a version dir (Case 2: `c14-0.0.1/c14/__init__.py`). The installer extracts to a tempdir, then `shutil.copytree`'s the package dir into the user's startup path (`~/.pymol/startup` on Linux, `%APPDATA%\pymol\startup` on Windows). The package becomes importable as `<startup>.c14`.

**Primary recommendation:** Implement `__init_plugin__(pmgapp)` in `c14/__init__.py` as a pure-Python function that (a) calls `c14.paths.selfcheck()` (fail-loud layout invariant, Pitfall 1), then (b) delegates via `from .ui import plugin_entry; plugin_entry.init_plugin(pmgapp)`. Put all `pymol.Qt` / `pymol.plugins` imports inside `c14/ui/plugin_entry.py` (gate-exempt), matching the `dynoplot.py` / `optimize.py` lazy-import style. Ship the plugin as a zip of the `c14/` directory (excluding `__pycache__`, `*.pyc`, and the gitignored `c14/data/assets/downloaded/` runtime cache). Add a `tools/build_plugin_zip.sh` script — none exists yet.

## Standard Stack

The established libraries/tools for this domain. The "stack" here is the PyMOL plugin engine itself — there are no third-party libraries to add (PROJECT.md constraint: PyQt5 via `pymol.Qt` + numpy ONLY).

### Core

| Component | Version / Location | Purpose | Why Standard |
|-----------|--------------------|---------|--------------|
| `pymol.plugins` | PyMOL 2.5.0, `tmp/pymol-src/modules/pymol/plugins/__init__.py` | Plugin loader: discovers, imports, and `legacyinit`s plugins; provides `addmenuitemqt` | This IS the engine PyMOL ships; there is no alternative. PLGN-01 mandates it. |
| `pymol.plugins.addmenuitemqt` | `plugins/__init__.py:100-108` | Register a menu item in the modern Qt "Plugin" menu | The modern Qt equivalent of the legacy `menuBar.addmenuitem`. PLGN-01 mandates the `addmenuitemqt` pattern. |
| `pymol.plugins.installation` | `plugins/installation.py` | Installs a `.py` / `.zip` / `.tar.gz` plugin into the user's startup path | The Plugin Manager's install backend. PLGN-02's "package dir → .zip → startup/" model IS this code. |
| `pymol.Qt` (PyQt5) | `from pymol.Qt import QtCore, QtGui, QtWidgets` | The Qt bindings PyMOL ships | AGENTS.md: "Use the modern Qt interface (`pymol.Qt`, not legacy `pmgqt`/`Tk`)". Matches `dynoplot.py:21`. |
| `pmg_tk.startup` | `legacysupport.py:17` (`from pmg_tk import startup`) | The package under which installed plugins become importable | A plugin dir `c14/` in the startup path is imported as `startup.c14` (the `__name__` prefix may be `pmg_tk.startup`; relative imports still resolve correctly). |

### Supporting

| Component | Location | Purpose | When to Use |
|-----------|----------|---------|-------------|
| `PluginInfo.get_metadata` | `plugins/__init__.py:193-210` | Parses a `# Key: Value` hash-comment block at the top of the plugin file (Version, Citation-Required, etc.) | Optional but recommended — add `# Version: 0.0.1` etc. to `c14/__init__.py` top so the Plugin Manager "Info" dialog shows it. |
| `pymol.plugins.addmenuitem` | `plugins/__init__.py:111-128` | Lower-level menu adder; `addmenuitemqt` delegates to this. Splits `label` on `\|` for cascading submenus. | Use `addmenuitemqt` directly; only reach for `addmenuitem` if you need a non-Plugin menu (you do not). |
| `tools/run_headless.sh` | `tools/run_headless.sh` (exists, 2030 bytes) | Runs a pure-`pymol.cmd.*` script headlessly via `run-conda-pymol.bat -cq` | Verifying cmd-only paths from WSL. CANNOT exercise Qt (no display). |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `__init_plugin__` | `__init__` (module-level function) | `legacyinit` falls back to `__init__` if `__init_plugin__` is absent (`plugins/__init__.py:322-324`). `__init__` is the LEGACY name; `__init_plugin__` is what the 2024-era Qt ports use (`optimize.py:29`, `outline.py:29`). PLGN-01 mandates `__init_plugin__` — DO NOT use `__init__`. |
| `addmenuitemqt` | Legacy `self.menuBar.addmenuitem('Plugin', ...)` | The legacy form (`annocryst.py:44`, `apbsplugin.py:338`) is Tk/PMGApp-based and explicitly forbidden by PLGN-01 ("no legacy `pmgqt`/Tk"). |
| Single-file `.py` plugin | Package dir plugin (`c14/` with `__init__.py`) | A single-file plugin cannot ship bundled data (PDBs, JSON) — PLGN-02 requires bundling small/critical PDBs. The package form is mandatory for this project. |

**Installation (NO `pip install`):** No packages to install. The plugin ships its OWN zip; the user installs it via PyMOL's Plugin Manager (Plugin → Plugin Manager → Install → point at the zip). The only "build" tool to add is a bash script that zips `c14/`:

```bash
# tools/build_plugin_zip.sh  (NEW — planner must create; none exists yet)
# Produces dist/c14-<version>.zip with c14/__init__.py at the zip root (Case 1 layout).
```

## Architecture Patterns

### Recommended Project Structure (the packaging-relevant slice)

```
c14/
├── __init__.py            # PURE-PYTHON (AST-gate-scanned). Defines __init_plugin__(pmgapp)
│                          #   -> selfcheck() + delegate to c14.ui.plugin_entry
├── paths.py               # PURE-PYTHON. data_path()/selfcheck() — __file__-relative resolver
├── data/
│   ├── selfcheck.json     # fail-loud layout invariant (Pitfall 1)
│   ├── cast.json          # ships in zip
│   ├── edits.json         # ships in zip
│   └── assets/
│       ├── bundled/       # SHIPS in zip (small/critical PDBs) — NOT gitignored
│       └── downloaded/     # GITIGNORED runtime cache — MUST be excluded from zip
├── pymol_layer/           # gate-EXEMPT (cmd-only wrappers, headless-testable) — Phases 3/4
└── ui/                    # gate-EXEMPT (Qt layer) — Phase 6 lives here
    ├── __init__.py        # exists (docstring only)
    └── plugin_entry.py    # NEW in Phase 6: init_plugin(pmgapp) + addmenuitemqt
```

The two gate-exempt dirs are `c14/pymol_layer/` and `c14/ui/` (`tools/check_imports.py:33`: `SKIP_DIRS = {"pymol_layer", "ui", "__pycache__"}`). **All Qt code MUST live under `c14/ui/`.** The `c14/` root (where `__init__.py`, `paths.py`, `engine.py`, etc. live) is STRICTLY pymol/PyQt5-free.

### Pattern 1: The `__init_plugin__` entry-point contract (PLGN-01)

**What:** PyMOL discovers the plugin, imports it, and calls exactly one function to initialize it.
**When to use:** Always — this is the only entry point.

**The loader contract** (verified, `plugins/__init__.py:302-324`):

```python
# Source: tmp/pymol-src/modules/pymol/plugins/__init__.py:302-324
def legacyinit(self, pmgapp):
    '''Call the __init__ or __init_plugin__ function which takes the PMGApp
    instance as argument (usually adds menu items).'''
    import types
    mod = self.module
    if mod is None:
        raise RuntimeError('not loaded')
    if hasattr(mod, '__init_plugin__'):
        mod.__init_plugin__(pmgapp)          # <-- PREFERRED, called first
    elif hasattr(mod, '__init__'):
        if isinstance(mod.__init__, types.FunctionType):
            mod.__init__(pmgapp)              # <-- legacy fallback
```

Key facts:
- The function receives ONE argument: `pmgapp` (the PMGApp instance).
- `__init_plugin__` is checked FIRST; if present, `__init__` is never called.
- For modern Qt plugins, `pmgapp` is **ignored** — registration goes through `addmenuitemqt`.
- `legacyinit` is called AFTER `__import__` (`plugins/__init__.py:277` then `:280`), so by the time `__init_plugin__` runs, the module body has executed and the GUI is up.

**Reference plugins (verbatim modern pattern):**

```python
# Source: Pymol-script-repo/plugins/dynoplot.py:445-447  (PyQt5-ported 2024 by Thomas Holder)
def __init_plugin__(self):
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('Rama Plot', lambda: DynoRamaObject('(enabled)'))

# Source: Pymol-script-repo/plugins/optimize.py:29-31
def __init_plugin__(app=None) -> None:
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('OpenBabel Optimize', run_plugin_gui)

# Source: Pymol-script-repo/plugins/outline.py:29-31
def __init_plugin__(app=None) -> None:
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('Outliner', run_plugin_gui)
```

Note three conventions: (1) the `pymol.plugins` import is **lazy** (inside the function body); (2) the `pmgapp` argument is ignored (named `self`/`app`/`app=None`); (3) the menu callback is a **zero-argument** callable (a function or lambda).

### Pattern 2: Menu registration via `addmenuitemqt`

**What:** Adds a labeled item to PyMOL's modern Qt "Plugin" menu; clicking it calls a no-arg callback.
**When to use:** Once, inside `__init_plugin__`.

**The API** (verified, `plugins/__init__.py:100-128`):

```python
# Source: tmp/pymol-src/modules/pymol/plugins/__init__.py:100-108
def addmenuitemqt(label, command=None, menuName='PluginQt'):
    '''
    Adds plugin menu item to main 'Plugin' menu.
    Intended for plugins which open a PyQt window.
    '''
    if not HAVE_QT:
        raise QtNotAvailableError()
    addmenuitem(label, command, menuName)

# Source: tmp/pymol-src/modules/pymol/plugins/__init__.py:111-128
def addmenuitem(label, command=None, menuName='Plugin'):
    '''Generic replacement for MegaWidgets menu item adding'''
    labels1 = [menuName] + label.split('|')      # <-- '|' makes a cascading SUBMENU
    ...
    pmgapp.menuBar.addmenuitem(labels2[-1], 'command', label=labels1[-1], command=command)
```

- Signature: `addmenuitemqt(label, command=None, menuName='PluginQt')`.
- `label` is the visible text. The `|` character creates a submenu cascade (e.g. `'RPG|New Game'`). A colon in the label is fine — only `|` is special.
- `command` is the no-arg callback fired on click.
- `menuName` defaults to `'PluginQt'` (the modern Qt Plugin menu) — DO NOT override it.
- If `HAVE_QT` is False (headless), it raises `QtNotAvailableError`, which `PluginInfo.load` catches (`plugins/__init__.py:287-288`) and reports as `"Plugin '%s' only available with PyQt GUI."` — the plugin load is not marked as crashed, but the menu is not registered. This is the expected headless behavior.

**For this project:**
```python
addmenuitemqt('RPG: Tale of C', _open_main_window)   # single top-level item, no '|'
```

### Pattern 3: The lazy-delegation from `c14/__init__.py` → `c14/ui/plugin_entry.py` (CRITICAL)

**What:** The pure-Python package root defines `__init_plugin__` but does NOT import pymol/PyQt5; it delegates to the gate-exempt `c14/ui/` layer.
**When to use:** Always — this is FORCED by the AST gate.

**Why it's forced (verified empirically):** `tools/check_imports.py` scans `c14/__init__.py` (it is at the `c14/` root, NOT in `SKIP_DIRS`). The gate uses `ast.walk(tree)`, which recurses into function bodies. Therefore EVEN a function-local `import pymol.plugins` inside `c14/__init__.py` is flagged:

```
$ python3.6 -c "...ast.walk on 'def f(): import pymol.plugins'..."
function-local import pymol -> AST gate flags it: True (count=1)
relative from .ui import -> AST gate flags it: False
```

The ONLY gate-clean way to reach the Qt layer from `c14/__init__.py` is a **relative import** whose module name is not in `BANNED_TOP = ("pymol", "PyQt5")`. `from .ui import plugin_entry` qualifies (module name `'ui'`). `__import__`/`importlib.import_module` would ALSO be flagged by the gate's secondary dynamic-import scan (`tools/check_imports.py:72-73`) if the line literally contains `pymol`/`pyqt5`, so dynamic imports are NOT an escape hatch — relative import is the answer.

**Verbatim code sketch:**

```python
# c14/__init__.py  (AST-gate-SCANNED; MUST stay free of pymol/PyQt5 imports)
"""c14 -- RPG: Tale of C PyMOL plugin package.

Pure-Python at module top so the domain tier stays unit-testable in WSL
(AST gate: tools/check_imports.py). The PyMOL entry point __init_plugin__
lazily delegates to c14/ui/plugin_entry.py (gate-exempt, may import
pymol.Qt). See 06-RESEARCH-qt-packaging.md Pattern 3.
"""
__version__ = "0.0.1-dev"


def __init_plugin__(pmgapp):
    # type: (object) -> None
    """PyMOL 2.5.0 plugin entry point.

    Called by pymol.plugins.PluginInfo.legacyinit after this module is
    imported (plugins/__init__.py:320-321). ``pmgapp`` is the PMGApp
    instance; modern Qt plugins IGNORE it and register via
    addmenuitemqt (dynoplot.py:445-447).

    All pymol/PyQt5 imports are deferred to c14/ui/plugin_entry.py
    (gate-exempt) so THIS file passes tools/check_imports.py.
    """
    # 1. Fail loud if the bundled data layout is broken (Phase 1 Pitfall 1).
    #    c14.paths is pure-Python -> safe + gate-clean to import here.
    from .paths import selfcheck
    selfcheck()

    # 2. Delegate menu registration + window construction to the Qt layer.
    #    Relative import resolves against c14's __package__ whether PyMOL
    #    imports us as 'startup.c14' or 'pmg_tk.startup.c14'.  The name 'ui'
    #    is NOT in BANNED_TOP, so the AST gate allows this line.
    from .ui import plugin_entry
    plugin_entry.init_plugin(pmgapp)
```

```python
# c14/ui/plugin_entry.py  (AST-gate-EXEMPT: c14/ui/ is in SKIP_DIRS)
"""Qt plugin entry point -- called by c14/__init__.py.__init_plugin__.

Gate-exempt: may import pymol.Qt / pymol.plugins
(tools/check_imports.py SKIP_DIRS = {"pymol_layer", "ui", "__pycache__"}).
"""
# Defer pymol imports to INSIDE init_plugin so merely importing
# c14/__init__.py (during PyMOL's __import__ phase) does NOT touch Qt
# before the GUI is ready.  Matches dynoplot.py:445-447 + optimize.py:29-31.
_main_window = None  # singleton; constructed lazily on first menu click


def init_plugin(pmgapp):
    # type: (object) -> None
    """Register the 'RPG: Tale of C' menu item. Called once on plugin load."""
    from pymol.plugins import addmenuitemqt            # plugins/__init__.py:100
    addmenuitemqt('RPG: Tale of C', _open_main_window)  # label, no-arg callback


def _open_main_window():
    """Menu callback: construct (or re-show) the main game window."""
    global _main_window
    from pymol.Qt import QtWidgets                     # Qt is ready at click time
    from .main_window import MainWindow                # c14/ui/main_window.py (Phase 6)
    if _main_window is None:
        _main_window = MainWindow()
    _main_window.show()
    _main_window.raise_()
```

**Why the singleton + lazy construction:** Registering the menu is cheap (one `addmenuitemqt` call); constructing a `QMainWindow` with all the panels is expensive and should happen only when the user actually clicks the menu. Building the window eagerly inside `__init_plugin__` would slow every PyMOL startup and would construct Qt widgets before the user wants them. The `dynoplot` callback `lambda: DynoRamaObject('(enabled)')` follows the same lazy-construction idea.

### Pattern 4: Plugin Manager packaging — the zip layout contract (PLGN-02)

**What:** A zip containing exactly one package directory (`<name>/__init__.py` at its root) is installable via Plugin Manager.
**When to use:** This is the ONLY supported way to ship a multi-file plugin with bundled data.

**The installer contract** (verified, `plugins/installation.py:90-143` and `:186-345`):

```python
# Source: tmp/pymol-src/modules/pymol/plugins/installation.py:90-143 (extract_zipfile)
# case 1: zip/<name>/__init__.py
names = [(name,) for name in namedict if '__init__.py' in namedict[name]]
if len(names) == 0:
    # case 2: zip/<name>-<version>/<name>/__init__.py
    names = [(pname, name) for (pname, pdict) in namedict.items()
                            for name in pdict
                            if '__init__.py' in pdict[name]]
if len(names) == 0:
    raise BadInstallationFile('Missing __init__.py')
if len(names) > 1:
    names = [n for n in names if n[-1] != 'tests']   # a top-level tests/ dir is tolerated
if len(names) > 1:
    raise BadInstallationFile('Archive must contain a single package.')
check_valid_name(names[0][-1])                       # no dots in the package name

# Source: plugins/installation.py:282-295 (installPluginFromFile, zip branch)
tempdir, dirnames = extract_zipfile(ofile, ext)
name = dirnames[-1]                                  # the package name, e.g. 'c14'
odir = os.path.join(tempdir, *dirnames)              # tempdir/c14  (Case 1)
mod_dir = os.path.join(plugdir, name)                # ~/.pymol/startup/c14
shutil.copytree(odir, mod_dir)                      # <-- copies c14/ into startup/
mod_file = os.path.join(mod_dir, '__init__.py')
```

**The contract, stated prescriptively:**

1. The zip MUST contain exactly ONE package directory with `__init__.py` at its root. For this project: `c14/__init__.py` at the zip root (Case 1). This is produced by `cd <repo> && zip -r dist/c14-0.0.1.zip c14/` (with exclusions — see Pitfall 4).
2. A top-level `tests/` directory alongside `c14/` is tolerated by the filter at `installation.py:132-133` BUT is NOT copied into startup (only the package dir is `copytree`'d), so tests do not ship. Still, the cleaner build zips ONLY `c14/`.
3. Absolute paths in the zip are rejected (`installation.py:106-107`).
4. The package name must be a valid Python module name — no dots (`check_valid_name`, `installation.py:87-88`). `c14` is valid. Names starting with `.` or `_` are SKIPPED by `findPlugins` (`plugins/__init__.py:385`) — `c14` starts with a letter, fine.
5. After extraction, the package dir is `shutil.copytree`'d into the user's startup path. The user's startup path defaults to `~/.pymol/startup` (Linux) or `%APPDATA%\pymol\startup` (Windows) (`installation.py:22-29`).
6. The installed module name is `<startup>.__name__ + '.' + name` (`installation.py:339-340`). The plugin is then imported with `__import__(mod_name, level=0)` (`plugins/__init__.py:277`) and `legacyinit`'d.

**Supported install formats** (`installation.py:13-14`): `.py`, `.zip`, `.tar.gz`. Use `.zip`.

**Installed layout** (what the user ends up with):
```
~/.pymol/startup/c14/__init__.py            <- __init_plugin__ lives here
~/.pymol/startup/c14/ui/plugin_entry.py      <- Qt entry
~/.pymol/startup/c14/paths.py
~/.pymol/startup/c14/data/selfcheck.json     <- selfcheck() looks here
~/.pymol/startup/c14/data/cast.json
~/.pymol/startup/c14/data/edits.json
~/.pymol/startup/c14/data/assets/bundled/*.pdb  <- small/critical PDBs
```
Because `c14.paths.data_path()` uses `Path(__file__).resolve().parent` (`c14/paths.py:23`), the bundled data resolves correctly INSIDE the installed location — `__file__` is `~/.pymol/startup/c14/paths.py`, so `data_path("data","selfcheck.json")` → `~/.pymol/startup/c14/data/selfcheck.json`. The resolver is install-location-agnostic by design (Phase 1 Pitfall 1 mitigation).

### Pattern 5: Optional plugin metadata block

**What:** A `# Key: Value` hash-comment block at the very top of the plugin file is parsed by `PluginInfo.get_metadata` (`plugins/__init__.py:193-210`) and shown in the Plugin Manager's "Info" dialog.
**When to use:** Recommended — gives the user version + author info in the manager UI.

```python
# c14/__init__.py  (top of file, BEFORE the module docstring is fine —
#                   get_metadata reads consecutive '#' lines, stops at first non-'#' line)
# Version: 0.0.1
# Author: RPG Tale of C contributors
# Citation-Required: No
"""c14 -- RPG: Tale of C PyMOL plugin package. ..."""
```
`get_version` prefers the `Version` metadata field, else falls back to `__version__` (`plugins/__init__.py:212-221`). `get_citation_required` reads `Citation-Required: Yes/No` (`:223-228`). Keep `Citation-Required: No` (this is an educational game, not a method to cite).

### Anti-Patterns to Avoid

- **Putting `import pymol.Qt` at the top of `c14/__init__.py`** — INSTANT AST-gate failure (`tools/check_imports.py` exits 1). Even inside `if TYPE_CHECKING:` the gate flags it (STRICT-BAN, `tools/check_imports.py:10-14`).
- **Putting `import pymol.plugins` inside `c14/__init__.py`'s `__init_plugin__` body** — STILL flagged (ast.walk recurses into function bodies; verified empirically). Use the relative `from .ui import plugin_entry` delegation instead.
- **Using `__import__('pymol.plugins')` or `importlib.import_module('pymol.plugins')` in `c14/__init__.py` to "hide" the import** — the gate's secondary scan (`tools/check_imports.py:72-73`) flags any line containing `__import__`/`import_module` AND `pymol`/`pyqt5`. This is NOT an escape hatch.
- **Defining a module-level `__init__(pmgapp)` function** — it's the LEGACY name; `__init_plugin__` is the modern one PLGN-01 mandates. (Also, a stray `__init__` could be called as a fallback if `__init_plugin__` were ever removed — don't leave both.)
- **Using `self.menuBar.addmenuitem('Plugin', ...)`** — that's the legacy Tk/PMGApp path (`annocryst.py:44`). PLGN-01 forbids it. Use `addmenuitemqt`.
- **Eagerly constructing the main `QMainWindow` inside `__init_plugin__`** — slows every PyMOL startup and builds widgets before the user asks. Construct lazily in the menu callback (Pattern 3).
- **Shipping `c14/data/assets/downloaded/` in the zip** — it's a gitignored runtime cache (`.gitignore:20`, verified `git check-ignore` exit 0). The zip build script MUST exclude it. Only `c14/data/assets/bundled/` ships (NOT gitignored, verified exit 1).
- **Shipping `__pycache__/` or `*.pyc` in the zip** — `.gitignore:4-5`. Exclude them in the build script.

## Don't Hand-Roll

Problems that look simple but PyMOL already ships a solution for:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Plugin discovery + import + init call | A custom loader / entry-point scanner | PyMOL's plugin engine (`pymol.plugins`) — just put `c14/` in the startup path | `plugins/__init__.py:365-431` already does findPlugins + PluginInfo.load + legacyinit. Re-implementing risks subtle incompatibility. |
| Menu item registration | Direct Qt menubar manipulation | `pymol.plugins.addmenuitemqt(label, callback)` | `addmenuitemqt` routes through PyMOL's menu system (`plugins/__init__.py:100-108`); touching the QMenuBar directly breaks across PyMOL versions. |
| Plugin install / zip extraction | A custom installer | PyMOL's Plugin Manager (Plugin → Plugin Manager → Install → pick zip) | `installation.py:186-345` handles zip layout validation, tempdir extraction, copytree into startup, reinstall version-checking. |
| Path resolution for bundled data | `os.getcwd()`-relative or hardcoded paths | `c14.paths.data_path(*parts)` (already built in Phase 1) | `__file__`-relative resolution is install-location-agnostic (Pitfall 1). `os.getcwd()`-relative paths SILENTLY break inside an installed plugin (`c14/paths.py` docstring). |
| Startup-path location lookup | Guessing `~/.pymol/startup` vs `%APPDATA%` | `installation.get_default_user_plugin_path()` (`installation.py:22-29`) | Cross-platform; the installer already uses it. (For the build script you don't need this — the USER's Plugin Manager handles placement.) |

**Key insight:** The packaging surface is 95% "match the contract PyMOL already enforces." The project's only build-side deliverable is a zip script that produces the Case-1 layout with the right exclusions. Everything else is the user clicking "Install" in Plugin Manager.

## Common Pitfalls

### Pitfall 1: AST gate flags pymol imports ANYWHERE in `c14/__init__.py` (including inside functions)

**What goes wrong:** `tools/check_imports.py` exits 1 with `IMPORT BOUNDARY VIOLATIONS`, blocking the Phase-1 gate and any CI/CD.
**Why it happens:** `ast.walk(tree)` recurses into function bodies, so a function-local `import pymol.plugins` is an `ast.Import` node that `_banned` matches. Verified empirically (`count=1`).
**How to avoid:** `c14/__init__.py`'s `__init_plugin__` delegates via the RELATIVE import `from .ui import plugin_entry` (name `ui` ∉ BANNED_TOP). All pymol/PyQt5 imports live in `c14/ui/plugin_entry.py` (gate-exempt). Never use `__import__`/`importlib` with a literal `pymol`/`pyqt5` string in `c14/__init__.py` either — the secondary scan catches those.
**Warning signs:** `tools/check_imports.py` prints `c14/__init__.py:N import pymol...` or `... REVIEW dynamic import: ... pymol ...`.

### Pitfall 2: Zip layout not matching Case 1 / Case 2 → `BadInstallationFile: Missing __init__.py`

**What goes wrong:** Plugin Manager reports "Unable to install plugin ... Missing __init__.py" or "Archive must contain a single package."
**Why it happens:** `extract_zipfile` (`installation.py:90-143`) only accepts (Case 1) `<name>/__init__.py` at zip root, or (Case 2) `<name>-<ver>/<name>/__init__.py`. A zip with `__init__.py` loose at the root (no wrapping dir), or with two package dirs, or with the package nested 3 levels deep, is rejected.
**How to avoid:** Build with `cd <repo> && zip -r dist/c14-0.0.1.zip c14/` so the zip's first entry is `c14/__init__.py`. Verify with `unzip -l dist/c14-0.0.1.zip | head` — the first non-directory entry MUST be `c14/__init__.py`.
**Warning signs:** The zip's namelist does not start with `c14/`.

### Pitfall 3: Forgetting `__init__.py` in a subpackage → `ImportError` on plugin load

**What goes wrong:** `from .ui import plugin_entry` raises `ImportError: No module named 'c14.ui.plugin_entry'` (or `c14.ui` is not a package) when `__init_plugin__` runs.
**Why it happens:** A package directory is only importable if it has `__init__.py` AT EVERY LEVEL. `c14/ui/__init__.py` already exists (docstring only) — KEEP it. Any new subpackage under `c14/ui/` (e.g. `c14/ui/panels/`) MUST also have an `__init__.py`.
**How to avoid:** Every directory under `c14/` that contains `.py` files MUST have an `__init__.py`. The zip build must include all `__init__.py` files (they're not gitignored).
**Warning signs:** `unzip -l` shows `c14/ui/plugin_entry.py` but no `c14/ui/__init__.py`.

### Pitfall 4: Shipping the gitignored runtime cache (`downloaded/`) or `__pycache__` in the zip

**What goes wrong:** The zip balloons in size with machine-specific downloaded PDBs (1crn.pdb 49KB, cid_2244.sdf 4KB currently — but this grows at runtime) and stale `.pyc` files that can mask source changes.
**Why it happens:** `c14/data/assets/downloaded/` IS gitignored (`.gitignore:20`, verified `git check-ignore` exit 0) but a naive `zip -r c14.zip c14/` includes it. `__pycache__/` and `*.pyc` are also gitignored (`.gitignore:4-5`) but present on disk after running tests.
**How to avoid:** The build script excludes them:
```bash
cd <repo>
zip -r dist/c14-"$(grep -m1 __version__ c14/__init__.py | sed 's/.*"\(.*\)".*/\1/')".zip c14/ \
    -x 'c14/__pycache__/*' 'c14/**/__pycache__/*' \
    -x 'c14/*.pyc' 'c14/**/*.pyc' \
    -x 'c14/data/assets/downloaded/*'
```
**Warning signs:** `unzip -l` shows `c14/data/assets/downloaded/` entries or any `.pyc`.

### Pitfall 5: Relative imports breaking because `c14` is imported under a different name

**What goes wrong:** `from .ui import plugin_entry` raises `ImportError` or `SystemError: Parent module '' not loaded, cannot perform relative import`.
**Why it happens:** PyMOL imports the plugin as `<startup>.c14` (e.g. `pmg_tk.startup.c14` — `plugins/__init__.py:427` builds `mod_name = parent.__name__ + '.' + name`). Relative imports use `__package__`, which Python sets correctly as long as the module is imported as part of a package (which it is). The risk arises ONLY if someone tries to import `c14` directly outside the startup package (e.g. `import c14` from a script with `c14/` on `sys.path`) — then `__package__` is `''` and relative imports fail.
**How to avoid:** Rely on PyMOL's loader (it imports via the startup package). For WSL unit tests of `c14/__init__.py`'s pure-Python parts, import via the package: `python3.6 -c "import c14"` from the repo root (where `c14/` is a top-level package) — this sets `__package__='c14'` and relative imports work. DO NOT test by importing the file as a loose script.
**Warning signs:** `SystemError: Parent module '' not loaded` or `ImportError: attempted relative import with no known parent package`.

### Pitfall 6: `__init_plugin__` exceptions are SWALLOWED (not crashed) by the loader

**What goes wrong:** A bug in `__init_plugin__` (e.g. selfcheck fails, a typo in `addmenuitemqt`) is caught by `PluginInfo.load`'s broad `except:` (`plugins/__init__.py:289-298`) and only PRINTS `"Unable to initialize plugin 'c14' (<mod_name>)."` — PyMOL keeps running, the menu never appears, and the user may not see the console message.
**Why it happens:** The loader deliberately does not crash PyMOL on a plugin error (one bad plugin shouldn't take down the session).
**How to avoid:** (a) Call `c14.paths.selfcheck()` FIRST in `__init_plugin__` so a broken layout failsloudly at load (console error + no menu) rather than silently at first click. (b) For Qt-level init errors that the user should SEE, show a `QtWidgets.QMessageBox.critical(...)` from inside `plugin_entry.init_plugin` BEFORE raising — but the pure-Python selfcheck is the primary loud guard. (c) Document the "check the PyMOL console" step in the human-verify checklist.
**Warning signs:** Menu item never appears after install; "Unable to initialize plugin 'c14'" in the PyMOL console.

### Pitfall 7: `addmenuitemqt` raising `QtNotAvailableError` in headless mode is EXPECTED, not a bug

**What goes wrong:** Running the plugin in headless PyMOL (`-cq`) prints `"Plugin 'c14' only available with PyQt GUI."` and the plugin is not loaded.
**Why it happens:** `addmenuitemqt` raises `QtNotAvailableError` when `HAVE_QT` is False (`plugins/__init__.py:105-106`); the loader catches it and warns (`:287-288`). This is BY DESIGN — a Qt plugin is meaningless headless.
**How to avoid:** Don't try to make the plugin load headlessly. Headless verification is for `pymol.cmd.*` paths (via `tools/run_headless.sh`), NOT for the Qt entry. The Qt entry is human-verify ONLY (AGENTS.md). Do NOT treat this warning as a failure in the headless smoke.
**Warning signs:** Tests trying to assert the plugin loads under `-cq` — they should not.

### Pitfall 8: Plugin name collision with an existing `c14` in startup

**What goes wrong:** Re-installing over an old version works (the installer handles it — `check_reinstall` at `installation.py:254-274` + `remove_if_exists`), but a LEFTOVER `c14/` from a broken prior install with stale data can cause confusing behavior.
**Why it happens:** `findPlugins` (`plugins/__init__.py:365-405`) registers the FIRST `c14` it finds in `startup.__path__`; if there are multiple startup paths, an old copy can shadow the new one.
**How to avoid:** The Plugin Manager uninstall (`plugins/__init__.py:326-363`) does `shutil.rmtree` on the package dir for a clean remove. For manual cleanup, check `get_startup_path()` (all startup dirs, not just the user one). Document in the install help: "if the menu doesn't update after reinstall, uninstall the old 'c14' from Plugin Manager first."
**Warning signs:** Installed plugin's `__version__` (shown in Plugin Manager Info) doesn't match the freshly-built zip's version.

## Code Examples

Verified patterns from PyMOL source + reference plugins.

### Example 1: Minimal `__init_plugin__` (the entire entry surface)

```python
# Source: synthesized from dynoplot.py:445-447 + optimize.py:29-31 + this project's gate constraint
# c14/__init__.py
def __init_plugin__(pmgapp):
    from .paths import selfcheck
    selfcheck()                          # fail-loud layout invariant (Pitfall 1)
    from .ui import plugin_entry         # relative import; gate-clean
    plugin_entry.init_plugin(pmgapp)     # delegate to gate-exempt Qt layer
```

### Example 2: `addmenuitemqt` with a submenu cascade (if a submenu is ever wanted)

```python
# Source: plugins/__init__.py:115 (label.split('|')) — '|' creates a cascade
def init_plugin(pmgapp):
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('RPG: Tale of C|New Game', _new_game)         # submenu "New Game"
    addmenuitemqt('RPG: Tale of C|Continue', _continue_game)   # submenu "Continue"
# For Phase 6 MVP, prefer a SINGLE top-level item: addmenuitemqt('RPG: Tale of C', _open_main_window)
```

### Example 3: Verifying the zip layout (build-script post-check)

```bash
# Source: derived from installation.py:118-135 (Case 1) + this project's exclusions
# After building dist/c14-0.0.1.zip:
unzip -l dist/c14-0.0.1.zip | head -n 15
# EXPECTED first entries:
#   c14/
#   c14/__init__.py          <-- Case 1: __init__.py directly under c14/
#   c14/paths.py
#   c14/ui/
#   c14/ui/__init__.py       <-- subpackage __init__ present (Pitfall 3)
#   c14/ui/plugin_entry.py
#   c14/data/
#   c14/data/selfcheck.json
#   c14/data/cast.json
#   c14/data/edits.json
#   c14/data/assets/bundled/<small PDBs>
# MUST NOT contain:
#   c14/data/assets/downloaded/   (gitignored runtime cache — Pitfall 4)
#   any __pycache__/ or *.pyc     (Pitfall 4)
```

### Example 4: The full load sequence (what PyMOL does, end-to-end)

```python
# Source: reconstructed from plugins/__init__.py + installation.py
# 1. User: Plugin Manager -> Install -> picks dist/c14-0.0.1.zip
# 2. installation.installPluginFromFile(ofile):
#    extract_zipfile -> tempdir/c14/__init__.py  (Case 1)
#    shutil.copytree(tempdir/c14, ~/.pymol/startup/c14)
#    PluginInfo(name='c14', mod_file='~/.pymol/startup/c14/__init__.py',
#               mod_name='<startup>.c14').load(force=1)
# 3. PluginInfo.load:
#    __import__('<startup>.c14', level=0)         # runs c14/__init__.py body
#                                               # (defines __init_plugin__, does NOT call it)
#    legacyinit(pmgapp):
#      mod.__init_plugin__(pmgapp)                # OUR function runs here
#        -> c14.paths.selfcheck()                # raises if data/ missing
#        -> from .ui import plugin_entry         # imports c14/ui/plugin_entry.py
#        -> plugin_entry.init_plugin(pmgapp)
#             -> addmenuitemqt('RPG: Tale of C', _open_main_window)
# 4. Menu "RPG: Tale of C" appears under Plugin. User clicks it:
#    _open_main_window() -> constructs MainWindow (lazy), shows it.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `__init__(pmgapp)` as the entry point | `__init_plugin__(pmgapp)` (preferred) | PyMOL plugin engine has supported both for years; 2024-era Qt ports (`optimize.py`, `outline.py`) use `__init_plugin__` | Use `__init_plugin__` (PLGN-01 mandates it). The loader still falls back to `__init__` but that's the legacy name. |
| Tk / `pmgqt` / `Pmw` GUIs (`annocryst.py`, `apbsplugin.py`, `autodock_plugin.py` — `self.menuBar.addmenuitem('Plugin', ...)`) | `pymol.Qt` (PyQt5) + `addmenuitemqt` (`dynoplot.py:21`, `optimize.py:25`) | `dynoplot.py` ported to PyQt 2024 (per its header comment) | PLGN-01 forbids the legacy interface. Match `dynoplot.py`'s `from pymol.Qt import QtCore, QtGui, QtWidgets`. |
| Single-file `.py` plugins | Package-dir plugins (with bundled data) | Always supported (`findPlugins` handles both, `plugins/__init__.py:388-401`) | PLGN-02's bundled-PDB requirement forces the package form. |

**Deprecated/outdated (do NOT use):**
- `self.menuBar.addmenuitem('Plugin', 'command', ...)` — legacy Tk/PMGApp API (seen in `annocryst.py:44`, `apbsplugin.py:338`, `autodock_plugin.py:106`). Replaced by `pymol.plugins.addmenuitemqt`.
- `Pmw.Group` / `Tkinter.Button` GUIs (seen in `apbsplugin.py:1936+`) — replaced by `pymol.Qt` QtWidgets.
- Module-level `__init__(pmgapp)` as the entry name — superseded by `__init_plugin__`.

## Open Questions

1. **Does `pmgapp` need to be passed through to `plugin_entry.init_plugin` at all?**
   - What we know: All 3 modern reference plugins IGNORE `pmgapp` (named `self`/`app`/`app=None`). `addmenuitemqt` does not need it. The fake-PMGApp path (`legacysupport.py:113-127 createlegacypmgapp`) gives a no-op `menuBar` for legacy callers.
   - What's unclear: Whether any Phase-6 Qt window-construction API (e.g. getting the PyMOL main window as a parent) wants `pmgapp` vs `pymol.gui.get_qtwindow()` (used in `managergui_qt.py:1`).
   - Recommendation: Pass `pmgapp` through to `plugin_entry.init_plugin(pmgapp)` for forward-compatibility, but `plugin_entry` should ignore it and use `from pymol.gui import get_qtwindow` if a parent window is needed (the modern pattern, `managergui_qt.py:1,40`). LOW confidence on the parent-window API — flag for the UI-adapter researcher to confirm against `pymol.gui`.

2. **Where exactly should `selfcheck()` failure surface — console-only or Qt dialog?**
   - What we know: An exception in `__init_plugin__` is caught by `PluginInfo.load` (`plugins/__init__.py:289`) and printed as "Unable to initialize plugin 'c14'". No Qt dialog is shown by the loader.
   - What's unclear: Whether a Qt dialog (via `QtWidgets.QMessageBox.critical`) is reachable at `__init_plugin__` time (Qt IS up by then, since `legacyinit` runs after the GUI launches — `legacysupport.py:90-111 initializePlugins`).
   - Recommendation: Primary guard = `selfcheck()` in `c14/__init__.py`'s `__init_plugin__` (pure-Python, fail-loud, console error + no menu). Optional enhancement = `plugin_entry.init_plugin` ALSO calls selfcheck and shows a Qt dialog on failure. Decide in planning based on how loud "loud" needs to be. MEDIUM confidence.

3. **Should the zip build script live at `tools/build_plugin_zip.sh` or a `Makefile` target?**
   - What we know: No build tool exists yet (`tools/` has smokes + gates but no zip script). The repo uses bash scripts for tooling.
   - What's unclear: User preference for build invocation.
   - Recommendation: `tools/build_plugin_zip.sh` (matches the `tools/*.sh` convention; `run_headless.sh` is the precedent). Output to `dist/c14-<version>.zip`. LOW confidence on naming only.

4. **Story-graph JSON data location for the zip** (out of packaging scope, flagged for the UI-adapter researcher):
   - What we know: `c14/data/` currently ships `selfcheck.json`, `cast.json`, `edits.json`, and `assets/bundled/` (5 smoke PDBs, NOT real cast structures). The Phase-5.1 glucose skeleton JSON lives in `.planning/` (not under `c14/`), so it does NOT yet ship with the plugin.
   - What's unclear: Where the engine loads story data from at runtime (the UI-adapter researcher owns this).
   - Recommendation for PACKAGING: whatever JSON the engine needs must be under `c14/data/` (resolved via `c14.paths.data_path()`) so it ships in the zip and resolves correctly when installed. The build script zips all of `c14/` minus the exclusions — so any data added under `c14/data/` ships automatically.

## Recommendations for the Planner

1. **One plan owns the plugin entry surface.** Create `c14/ui/plugin_entry.py` (`init_plugin` + `_open_main_window` + lazy singleton) and MODIFY `c14/__init__.py` to add `__init_plugin__(pmgapp)` per Pattern 3. This is the ONE allowed modification to the pure-Python `c14/` root in Phase 6 — verify `tools/check_imports.py` still exits 0 after the change (it must — only relative imports + `selfcheck`).

2. **Add `tools/build_plugin_zip.sh` (NEW).** Produces `dist/c14-<version>.zip` with Case-1 layout (`c14/__init__.py` at zip root) and the Pitfall-4 exclusions (`__pycache__`, `*.pyc`, `c14/data/assets/downloaded/`). Add a post-build `unzip -l | head` sanity check to the script.

3. **Add optional metadata to `c14/__init__.py` top** (Pattern 5): `# Version:`, `# Author:`, `# Citation-Required: No`. Cheap, shows in Plugin Manager Info.

4. **Verify PLGN-02 with a real install in the human-verify checkpoint.** Success Criterion 1 requires "installs via Plugin Manager ... and on PyMOL restart a 'RPG: Tale of C' menu item appears." This is a HUMAN-VERIFY step (Qt; cannot be automated from WSL per AGENTS.md). The plan must include a human-verify task: build the zip, install via Plugin Manager in a real Windows PyMOL, restart, confirm the menu appears, click it, confirm the window opens. Document the exact click path (Plugin → Plugin Manager → Install New Plugin → pick zip → restart PyMOL → look for "RPG: Tale of C" under the Plugin menu).

5. **Verify the entry point does not regress the AST gate.** Add an assertion (or a test) that `python3.6 tools/check_imports.py` exits 0 AFTER `c14/__init__.py` gains `__init_plugin__`. The function body must contain ONLY: `from .paths import selfcheck`, `selfcheck()`, `from .ui import plugin_entry`, `plugin_entry.init_plugin(pmgapp)`. No `pymol`/`PyQt5` literal anywhere in the file.

6. **Confirm `c14/ui/__init__.py` stays a (docstring) package marker.** It already exists. Do NOT delete it. Any new `c14/ui/*.py` (plugin_entry, main_window, panels) is fine; any new subpackage under `c14/ui/` needs its own `__init__.py` (Pitfall 3).

7. **Bundle small/critical PDBs into `c14/data/assets/bundled/` for the MVP.** Currently only smoke-test PDBs live there (`_edit_smoke.pdb`, `_his_smoke.pdb`, `_smoke.pdb`, `_wt_align_mut.pdb`, `_wt_align_wt.pdb`). For PLGN-02 ("bundles small/critical PDB structures"), the MVP needs the glucose critical-path small structures placed here (PDB IDs come from already-approved Phase-5 content — do NOT invent PDB IDs; AGENTS.md "no fabricated science"). Large structures are fetched on first play (CAST-04 — that's the UI-adapter / asset-management researcher's concern, not packaging). The build script ships `bundled/` automatically (NOT gitignored).

8. **Do not attempt to unit-test `__init_plugin__` end-to-end in WSL.** It imports `c14.ui.plugin_entry`, which imports `pymol.Qt` — un-runnable without a display. The testable surface is: (a) `python3.6 -m py_compile c14/__init__.py c14/ui/plugin_entry.py` (syntax); (b) `python3.6 tools/check_imports.py` (gate stays green); (c) import `c14` pure-Pythonically to confirm `__init_plugin__` is defined and callable WITHOUT calling it (`python3.6 -c "import c14; assert callable(c14.__init_plugin__)"` — this works because merely importing `c14` does NOT import `c14.ui.plugin_entry` lazily... **WAIT — caveat**: importing `c14` runs `c14/__init__.py`'s module body, which only DEFININES `__init_plugin__` (does not call it), so `pymol.Qt` is never touched. Safe.). The actual menu + window is human-verify only.

9. **Coordinate with the two sibling researchers.** The UI-adapter researcher owns `c14/ui/main_window.py` (the `MainWindow` class that `_open_main_window` constructs) and the panel/controller split. The persistence researcher owns save/load + achievements. This packaging research owns `c14/__init__.py`'s `__init_plugin__`, `c14/ui/plugin_entry.py`, and `tools/build_plugin_zip.sh`. The hand-off contract is the `_open_main_window()` callback in `plugin_entry.py` — it imports `from .main_window import MainWindow` (the UI-adapter researcher delivers `MainWindow`).

## Sources

### Primary (HIGH confidence)
- `tmp/pymol-src/modules/pymol/plugins/__init__.py` — the plugin engine: `legacyinit` (lines 302-324, the `__init_plugin__`/`__init__` contract), `addmenuitemqt` (100-108) + `addmenuitem` (111-128, the `|`-split cascade), `PluginInfo.load` (248-300, the import + legacyinit + exception handling), `findPlugins` (365-405, the dir/`__init__.py` discovery + `.`/`_` skip rule), `PluginInfo.get_metadata` (193-210, the `# Key: Value` block).
- `tmp/pymol-src/modules/pymol/plugins/installation.py` — the installer: `extract_zipfile` (90-143, Case 1 / Case 2 zip layout + `Missing __init__.py` / `single package` rules), `installPluginFromFile` (186-345, the zip → tempdir → copytree → startup flow), `get_default_user_plugin_path` (22-29, `~/.pymol/startup` vs `%APPDATA%\pymol\startup`), `zip_extensions` (13, `['zip','tar.gz']`).
- `tmp/pymol-src/modules/pymol/plugins/legacysupport.py` — `installPlugin` (52-68, the file-dialog entry), `initializePlugins` (90-111), `createlegacypmgapp` (113-127, the fake-PMGApp no-op menuBar), `get_pmgapp` (26-31, `pymol.gui.get_pmgapp()`), `from pmg_tk import startup` (17).
- `tmp/pymol-src/modules/pymol/plugins/managergui_qt.py` — the Qt Plugin Manager: `from pymol.gui import get_qtwindow` (1, the modern parent-window accessor), `installplugin` (301-304), `install_repo_plugins` (134-156).
- `Pymol-script-repo/plugins/dynoplot.py:445-447` — verbatim modern `__init_plugin__` + `addmenuitemqt` (PyQt5-ported 2024).
- `Pymol-script-repo/plugins/optimize.py:29-31` and `outline.py:29-31` — independent corroboration of the `__init_plugin__(app=None)` + lazy `addmenuitemqt` pattern.
- `tools/check_imports.py` — the AST gate: `SKIP_DIRS` (33), `BANNED_TOP` (34), `ast.walk` recursion + `_banned` (44-66), the dynamic-import secondary scan (72-73). Empirically verified: function-local `import pymol` is flagged (count=1); relative `from .ui import ...` is not.
- `c14/__init__.py`, `c14/ui/__init__.py`, `c14/paths.py` — the current Phase-1 state (pure-Python root, empty gate-exempt `ui/`, `__file__`-relative `data_path`/`selfcheck`).
- `.gitignore:20` + `git check-ignore` — `c14/data/assets/downloaded/` IS ignored (exit 0); `c14/data/assets/bundled/` is NOT ignored (exit 1).

### Secondary (MEDIUM confidence)
- `Pymol-script-repo/plugins/show_contacts.py:329-332` — uses the legacy `__init__` name but with the modern `addmenuitemqt` (confirms `addmenuitemqt` works regardless of which entry name is used; `__init_plugin__` is still preferred).
- `tmp/pymol-src/modules/pymol/plugins/managergui.py` — the legacy Tk Plugin Manager (referenced for contrast only; not used).

### Tertiary (LOW confidence)
- The parent-window API (`pymol.gui.get_qtwindow` / `get_pmgapp`) for giving the main `QMainWindow` a proper Qt parent — flagged in Open Question 1 for the UI-adapter researcher to confirm. `managergui_qt.py:1,40` uses `get_qtwindow()` but the c14 main window may not need an explicit parent.

## Metadata

**Confidence breakdown:**
- Entry-point contract (`__init_plugin__`): HIGH — verified in `plugins/__init__.py:302-324` + 3 reference plugins.
- Menu registration (`addmenuitemqt`): HIGH — verified in `plugins/__init__.py:100-128` + 3 reference plugins.
- Lazy-delegation pattern (AST gate): HIGH — empirically verified (function-local `import pymol` flagged; relative `from .ui` not).
- Zip layout (PLGN-02): HIGH — verified in `installation.py:90-143` + `:186-345`.
- Bundled-asset shipping: HIGH — `git check-ignore` verified; `c14/paths.py` `__file__`-relative resolution confirmed.
- Python 3.6 constraints: HIGH — repo already targets 3.6 (AGENTS.md, `tools/check_imports.py` shebang `python3.6`).
- Parent-window Qt API for `MainWindow`: LOW — flagged for UI-adapter researcher (Open Question 1).

**Research date:** 2026-08-29
**Valid until:** 2026-09-29 (stable — PyMOL 2.5.0 plugin engine is not changing; re-verify if PyMOL upgrades to a new major version)
