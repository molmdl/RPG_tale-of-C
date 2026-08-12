# Phase 1: Foundations & Testability Boundary — Research Track: Pure-Python/UI Testability Split (PLGN-03)

**Researched:** 2026-08-13
**Domain:** Python package architecture / import-boundary enforcement / Python 3.6 compatibility
**Confidence:** HIGH (all claims empirically verified on the actual `python3.6.9` test env, or read directly from PyMOL 2.5.0 source at `tmp/pymol-src/modules/pymol/plugins/__init__.py`)

## Summary

This track answers: *what does the planner need to know to enforce the 3-tier testability split architecturally, with a CI grep gate, on Python 3.6?* The 3-tier layering itself (pure-Python domain → `pymol.cmd` headless layer → `pymol.Qt` human-verify layer) is already established at HIGH confidence in `.planning/research/ARCHITECTURE.md` as a direct consequence of AGENTS.md. This document fills the gaps that ARCHITECTURE.md left under-specified and corrects two traps in the prior research that would cause `py_compile`/import failures on 3.6.9.

The five highest-value findings the planner must act on:

1. **`c14/__init__.py` is the linchpin of the whole boundary.** PyMOL's plugin loader (`plugins/__init__.py:277` `__import__(self.mod_name, level=0)`) **runs `c14/__init__.py` on plugin load**, and Python **also runs `c14/__init__.py` before `import c14.engine` in WSL** (package-init semantics). So any top-level `import pymol` in `c14/__init__.py` breaks WSL testability. `__init_plugin__` must be a real top-level attribute of `c14/__init__.py` (PEP 562 module `__getattr__` is 3.7+ — confirmed unavailable at runtime on 3.6.9). The correct pattern: define `__init_plugin__(app)` in `c14/__init__.py` but have it **lazily delegate** to `c14/ui/plugin_entry.py` (our own module) which does the real `from pymol import cmd` / `from pymol.Qt import ...`. Then `c14/__init__.py` has ZERO `pymol`/`PyQt5` imports anywhere and passes the gate naturally.
2. **`c14/controller.py` must live INSIDE `c14/ui/`**, not at `c14/` root as ARCHITECTURE.md line 107/155 shows. `controller.py` imports `pymol.Qt` + `pymol.cmd`; if it sits at `c14/` root, the gate (which scans `c14/` excluding only `pymol_layer/` and `ui/`) flags it. Moving it to `c14/ui/controller.py` makes the directory location = the tier, and the gate's two-dir exclusion set is sufficient and airtight.
3. **`dataclasses` is BANNED on 3.6.9** (confirmed: `import dataclasses` → `ModuleNotFoundError`). ARCHITECTURE.md's `c14/story/model.py` example (lines 164-173) uses `@dataclass` for `MolAction` — **the planner must NOT copy that example verbatim**. Use `typing.NamedTuple` (defaults work on 3.6.9, verified) with `Optional[dict] = None` + `args or {}` for mutable defaults, or a plain `__init__` class. Note: `collections.namedtuple(defaults=...)` is 3.7+ (confirmed unavailable) — only `typing.NamedTuple` supports defaults on 3.6.
4. **`py_compile` is necessary but NOT sufficient.** Confirmed: PEP 604 union annotations (`x: int | None = None`) **pass `py_compile`** on 3.6.9 (parsed as a bitwise-or expression) but **raise `TypeError: unsupported operand type(s) for |` at import**. So the success criterion's "import cleanly" requirement does real work `py_compile` alone cannot. The gate must therefore be TWO checks: (a) `python3.6 -m py_compile` per file, AND (b) an actual `import` smoke of each domain module (or the unittest suite, which imports them).
5. **`pytest` is NOT installed** in the WSL env (`python3.6 -m pytest` → `No module named pytest`; confirmed). ARCHITECTURE.md/STACK.md/SUMMARY.md all say "runnable with `python3.6 -m pytest`" — **this is wrong**. The planner MUST specify `python3.6 -m unittest` (stdlib, present). Do not propose installing pytest (AGENTS.md forbids installs).

**Primary recommendation:** Implement the gate as an **AST-based** `tools/check_imports.py` (stdlib `ast` + `os.walk`, 3.6-compatible — empirically tested: catches all static `pymol.*`/`PyQt5.*` imports incl. aliased `import pymol.cmd as c`, flags dynamic `importlib.import_module('pymol...')` for review, and produces **zero false positives** on comments/string literals). Exclusion set = `{"pymol_layer", "ui"}`. Pair it with `python3.6 -m py_compile` (syntax) + `python3.6 -m unittest` (import + behavior) for pure-Python domain modules. Use the directory location AS the tier marker so the two-dir exclusion is complete.

## Standard Stack

This track is architectural, not library-oriented. The "stack" is stdlib-only by mandate (AGENTS.md: assume only what `pymol-open-source` ships; do not install anything).

### Core (the boundary-enforcement tooling)
| Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `ast` (stdlib) | 3.6.9 | Parse `.py` files and walk `Import`/`ImportFrom` nodes to detect banned imports precisely | Stdlib; no false positives on comments/strings; catches aliased submodule imports (`import pymol.cmd as c`) that anchored grep misses. Empirically verified. |
| `os.walk` (stdlib) | 3.6.9 | Recurse `c14/`, prune `pymol_layer/` + `ui/` in-place | Stdlib; trivial dir-name exclusion |
| `py_compile` (stdlib) | 3.6.9 | `python3.6 -m py_compile <file>` — syntax check | AGENTS.md-mandated; runs in WSL without PyMOL |
| `unittest` (stdlib) | 3.6.9 | `python3.6 -m unittest discover -s tests` — import + behavior tests for pure-Python domain | **The only available test runner** — pytest is NOT installed (confirmed) |

### Supporting (domain-tier data types replacing banned 3.7+ features)
| Construct | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `typing.NamedTuple` | 3.6.1+ (verified on 3.6.9) | Immutable value types with defaults — the `@dataclass` replacement | For `MolAction`, `Node`, `Choice`, `Claim`, etc. Defaults via `field: Optional[T] = None`. |
| plain `class` with `__init__` + `__slots__` | all | Mutable or complex objects; clean mutable-default handling | When a type needs `default_factory`-style behavior (NamedTuple has none) |
| `collections.OrderedDict` | all | Save-file field ordering that must not depend on dict-order | For any JSON-serialized state where key order matters for stable diffs (3.6 dict order is impl-detail, NOT guaranteed — 3.7+ guarantee) |
| `typing.TYPE_CHECKING` + string annotations | 3.5.3+ (verified) | Reference a type in annotations WITHOUT importing it at runtime | Escape hatch if a domain module ever needs to name a pymol type for type-checkers only (see Open Questions) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| AST-based gate | anchored `grep -rnE "^(import\|from) (pymol\|PyQt5)"` | Grep is a one-liner and fine as a fast pre-commit hook, but misses aliased submodule imports? — actually anchored grep catches `import pymol.cmd as c` (substring `import pymol`), but DOES false-positive on unanchored use and CANNOT distinguish a real import from a string/comment without anchoring. AST has none of these problems. **Use AST as primary; grep as optional fast pre-commit.** |
| `typing.NamedTuple` | plain `class` | NamedTuple = immutable + tuple-unpackable + zero boilerplate; plain class = mutable-default safety + `__slots__`. Pick per type. For `MolAction` (pure intent data, emitted & consumed) → NamedTuple. |
| `python3.6 -m unittest` | `python3.6 -m pytest` | pytest is NOT installed and cannot be (AGENTS.md). unittest is the only option. |

**Installation:** NONE. Everything is stdlib, already present in the 3.6.9 env. (This is a hard constraint — do not propose `pip install`.)

## Architecture Patterns

### Recommended Project Structure (refined from ARCHITECTURE.md — two corrections)

```
RPG_tale-of-C/
├── c14/                              # Plugin package (the installable unit)
│   ├── __init__.py                   # PURE-PYTHON. __version__, package metadata,
│   │                                 #   def __init_plugin__(app): from c14.ui.plugin_entry
│   │                                 #   import bootstrap; bootstrap(app)
│   │                                 #   NO pymol/PyQt5 import anywhere (top OR nested).
│   │                                 #   Passes the gate naturally.
│   ├── engine.py                     # GameEngine turn loop (pure-Py)
│   ├── state.py                      # GameState + JSON round-trip (pure-Py)
│   ├── rng.py                        # Seedable RngEngine: random.Random(seed) (pure-Py)
│   ├── edit_router.py                # Edit-intent -> branch routing (pure-Py)
│   ├── citations.py                  # CitationRegistry + approval gate logic (pure-Py)
│   ├── assets.py                     # AssetManifest loader (pure-Py)
│   ├── persist.py                    # SaveStore (pure-Py)
│   ├── achievements.py               # Achievement evaluator (pure-Py)
│   ├── paths.py                      # __file__-relative path resolver + self-check (pure-Py)
│   ├── story/
│   │   ├── __init__.py               # PURE-PYTHON (story is domain tier — scanned by gate)
│   │   ├── model.py                  # Node/Choice/MolAction as typing.NamedTuple (pure-Py)
│   │   ├── interpreter.py            # StoryInterpreter: walk graph, eval conds, RNG (pure-Py)
│   │   └── validate.py               # Graph validator: dangling diverts, unknown claims (pure-Py)
│   ├── pymol_layer/                  # ← GATE-EXCLUDED. ALL pymol.cmd imports live here.
│   │   ├── __init__.py               # (excluded from gate; may import pymol)
│   │   ├── assets.py                 # AssetManager: cmd.fetch/load
│   │   ├── molops.py                 # MolAction -> cmd.show/hide/select/zoom/delete
│   │   ├── protonation.py            # Curated variant application
│   │   └── edits.py                  # EditApplier + restore-safety-net (cmd.create backup)
│   └── ui/                           # ← GATE-EXCLUDED. ALL pymol.Qt + pymol.cmd imports here.
│       ├── __init__.py               # (excluded)
│       ├── plugin_entry.py           # bootstrap(app): real `from pymol import cmd`,
│       │                             #   `from pymol.Qt import ...`, addmenuitemqt, cmd.extend
│       ├── controller.py             # ← MOVED from c14/ root. Wires UI<->Engine<->pymol_layer.
│       ├── main_window.py            # C14MainWindow(QtWidgets.QMainWindow)
│       ├── choice_panel.py           # ChoicePanel(QWidget)
│       ├── cast_dialog.py            # CastListDialog(QDialog)
│       ├── help_dialog.py            # HelpDialog(QDialog)
│       ├── achievement_board.py      # AchievementBoard(QWidget)
│       └── save_load.py              # Save/Load buttons + file dialogs
├── data/                             # JSON content (story, edits, citations, assets, achievements)
├── tests/                            # Pure-Python unittests (WSL, `python3.6 -m unittest`)
│   ├── test_state.py
│   ├── test_interpreter.py
│   ├── test_edit_router.py
│   ├── test_citations.py
│   ├── test_rng.py
│   ├── test_validate.py
│   ├── test_assets_manifest.py
│   └── test_paths.py                 # __file__-relative path self-check
├── smoke/                            # Headless PyMOL smoke tests (run-conda-pymol.bat -cq)
├── tools/
│   ├── check_imports.py              # ← THE GATE (AST-based, this research track)
│   └── check_citations.py            # (citation-gate track, not this one)
├── spec.md
├── README.md
└── .planning/
```

**Two corrections vs ARCHITECTURE.md lines 79/107/155:**
- `c14/controller.py` → `c14/ui/controller.py` (it imports Qt+pymol; must be inside the excluded `ui/` dir).
- `c14/__init__.py` does NOT directly call `addmenuitemqt`/import pymol; it delegates to `c14/ui/plugin_entry.py:bootstrap` via a lazy import of our own submodule. (See Pattern 1.)

### Pattern 1: The `__init__.py` lazy-delegation pattern (the boundary linchpin)

**What:** `c14/__init__.py` stays 100% pure-Python (no `pymol`/`PyQt5` import at any scope) so that `import c14.engine` works in WSL. The plugin entry point `__init_plugin__` is defined here (PyMOL's loader requires `c14.__init_plugin__` as a real top-level attribute — PEP 562 module `__getattr__` is 3.7+, unavailable on 3.6.9) but delegates the real PyMOL/Qt wiring to `c14/ui/plugin_entry.py` via a lazy import of **our own** submodule (the gate only bans `pymol`/`PyQt5`, not `c14.ui`).

**Why it's forced:** PyMOL's plugin loader (`tmp/pymol-src/modules/pymol/plugins/__init__.py`):
- `findPlugins` (line 396): a directory plugin maps to `<dir>/__init__.py`.
- `load` (line 277): `__import__(self.mod_name, level=0)` imports the package → **runs `c14/__init__.py`**.
- `legacyinit` (line 320-321): `if hasattr(mod, '__init_plugin__'): mod.__init_plugin__(pmgapp)`.

So `c14/__init__.py` runs in BOTH contexts: WSL (`import c14.engine` triggers it) and PyMOL (plugin load). Top-level `import pymol` there breaks WSL. And `__init_plugin__` must be a top-level name on 3.6.

**Example (reference design — verified pattern):**
```python
# c14/__init__.py  — PURE-PYTHON. Gate passes (no pymol/PyQt5 anywhere).
__version__ = "0.1.0"

def __init_plugin__(app=None):
    # Lazy import of OUR submodule (not pymol). Runs only when PyMOL loads the plugin.
    # c14/ui/ is gate-excluded, so the pymol/Qt imports inside plugin_entry are allowed.
    from c14.ui.plugin_entry import bootstrap
    bootstrap(app)
```
```python
# c14/ui/plugin_entry.py  — GATE-EXCLUDED (inside ui/). Real PyMOL/Qt wiring lives here.
def bootstrap(app=None):
    from pymol import cmd
    from pymol.Qt import QtWidgets
    from c14.ui.main_window import C14MainWindow
    from c14.ui.controller import Controller

    def _launch():
        ctrl = Controller()
        C14MainWindow(ctrl).show()
    # addmenuitemqt raises QtNotAvailableError if no Qt (plugins/__init__.py:105-106),
    # so it must be called here (PyMOL-with-Qt only), never in c14/__init__.py.
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('RPG: Tale of C', _launch)
```

### Pattern 2: 3-tier one-way dependency (domain → pymol_layer ← controller ← ui)

**What:** Domain tier imports only stdlib (+ numpy if needed). It emits `MolAction` **data** (pure value). The PyMOL layer translates `MolAction` → `cmd.*`. The UI/controller calls the engine and dispatches `MolAction`s to `pymol_layer`. **Domain never imports pymol; pymol_layer never imports ui; ui may import both.**

**Boundary rule:** `import c14.engine` (and every domain module) must transitively import NOTHING from `pymol`/`PyQt5`. This is what the gate enforces structurally.

### Pattern 3: Dependency injection at the boundary (no hidden pymol coupling)

**What:** The domain tier expresses molecular intent as the `MolAction` value type. The controller (in `ui/`) is the ONLY place that hands `MolAction`s to `pymol_layer.molops.apply(action)`. The engine accepts an injectable `MolAction` sink (a callable) so unit tests pass a mock sink — the engine never knows pymol exists.

**Why:** Keeps the engine pure-Python AND testable without monkeypatching `pymol.cmd`. The testability boundary is enforced by type (data crosses; no live pymol objects cross into domain).

### Anti-Patterns to Avoid
- **`import pymol` at top of `c14/__init__.py`:** breaks `import c14.engine` in WSL. Use Pattern 1.
- **`@dataclass` in domain modules:** `dataclasses` is 3.7+; `import` fails on 3.6.9 (confirmed). Use `typing.NamedTuple` or a plain class.
- **`from __future__ import annotations`:** 3.7+ future; `py_compile` fails on 3.6.9 ("future feature annotations is not defined" — confirmed). Do not use.
- **PEP 604 union annotations (`x: int | None`):** compile-OK on 3.6 but raise `TypeError` at import (confirmed). Use `Optional[int]`.
- **`c14/controller.py` at `c14/` root:** gate flags it (imports Qt+pymol). Move to `c14/ui/controller.py`.
- **Mutable default in `typing.NamedTuple` (`args: dict = {}`):** shared-dict bug, and NamedTuple has no `default_factory`. Use `args: Optional[dict] = None` + `action.args or {}`.
- **`collections.namedtuple(..., defaults=())`:** `defaults` kwarg is 3.7+ (confirmed `TypeError` on 3.6). Only `typing.NamedTuple` supports defaults on 3.6.
- **Relying on `dict` insertion order for save-file stability:** guaranteed only 3.7+; 3.6 order is impl-detail. Use `OrderedDict` for any order-sensitive serialization.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detect banned imports in `.py` files | Regex/grep with hand-crafted patterns | `ast` module: walk `Import`/`ImportFrom` nodes | Grep false-positives on comments/strings and needs many patterns; AST is exact, handles aliases (`import pymol.cmd as c`), and is stdlib. Empirically tested: 7/7 violations caught, 0 false positives. |
| Test runner for pure-Python domain | A custom test harness, or assume pytest | `python3.6 -m unittest discover -s tests` | pytest is NOT installed (confirmed); unittest is stdlib and present. |
| Syntax validation | Custom parser | `python3.6 -m py_compile <file>` | Stdlib, AGENTS.md-mandated. (But pair with an import check — see Pitfall 3.) |
| Mutable default values for data types | A `default_factory` reimplementation | `Optional[T] = None` + `x or default` idiom, or a plain `__init__` class | NamedTuple has no `default_factory`; the idiom is the 3.6-idiomatic equivalent. |
| Ordered key-value serialization | Relying on 3.7+ dict order | `collections.OrderedDict` | 3.6 dict order is not guaranteed. |

**Key insight:** The boundary is enforced structurally (directory location = tier) + mechanically (AST gate over the two non-domain dirs excluded). Don't try to enforce it by convention or code review alone — the gate is the guarantee.

## Common Pitfalls

### Pitfall 1: Top-level `import pymol` in `c14/__init__.py` silently breaks all WSL tests
**What goes wrong:** `import c14.engine` in WSL raises `ModuleNotFoundError: No module named 'pymol'` even though `engine.py` itself is pure-Python.
**Why it happens:** Python runs the package's `__init__.py` before any submodule. PyMOL's loader ALSO runs it (`plugins/__init__.py:277`). Developers naturally put `from pymol import cmd` + `addmenuitemqt` at the top of `__init__.py` (matching the single-file reference plugins), which is fine for PyMOL but fatal for WSL.
**How to avoid:** Pattern 1 — `c14/__init__.py` is pure-Python; `__init_plugin__` delegates to `c14/ui/plugin_entry.py` via lazy import of our own submodule.
**Warning signs:** `import c14.engine` fails in WSL with `ModuleNotFoundError: pymol`; the gate flags `c14/__init__.py`.

### Pitfall 2: `@dataclass` / `from __future__ import annotations` fail on 3.6.9
**What goes wrong:** `python3.6 -m py_compile c14/story/model.py` fails (`future feature annotations is not defined`) or `import c14.story.model` fails (`No module named 'dataclasses'`).
**Why it happens:** Both are 3.7+. ARCHITECTURE.md's `model.py` example (lines 164-173) uses `@dataclass` — copying it verbatim is a trap.
**How to avoid:** `typing.NamedTuple` (defaults verified on 3.6.9) or plain classes. Never `from __future__ import annotations`.
**Warning signs:** `py_compile` SyntaxError on a future import; `ModuleNotFoundError: dataclasses` at import.

### Pitfall 3: `py_compile` passes but `import` fails (PEP 604, missing modules)
**What goes wrong:** A domain module passes `python3.6 -m py_compile` but raises at `import` time.
**Why it happens:** `py_compile` checks SYNTAX only. PEP 604 `x: int | None = None` is syntactically a bitwise-or expression (compiles) but raises `TypeError` when the annotation is evaluated at import (confirmed). Likewise `import dataclasses` compiles but fails at import. The success criterion requires BOTH "pass `py_compile`" AND "import cleanly" — the second is not implied by the first.
**How to avoid:** The gate/CI runs BOTH `py_compile` AND an import smoke (the `unittest` suite imports every domain module; or add an explicit `import c14.X` smoke step). Treat them as two distinct checks.
**Warning signs:** `py_compile` green, tests red with `TypeError`/`ModuleNotFoundError`.

### Pitfall 4: `c14/controller.py` at `c14/` root defeats the two-dir exclusion
**What goes wrong:** The gate (scan `c14/` excluding `pymol_layer/` + `ui/`) flags `c14/controller.py` because it imports `pymol.Qt`/`pymol.cmd`.
**Why it happens:** ARCHITECTURE.md places `controller.py` at `c14/` root but classifies it as UI-tier (imports Qt+pymol). The exclusion list doesn't cover it.
**How to avoid:** Move `controller.py` → `c14/ui/controller.py`. Then directory location = tier and the two-dir exclusion is complete.
**Warning signs:** Gate reports violations in `c14/controller.py`.

### Pitfall 5: `collections.namedtuple(defaults=...)` is 3.7+
**What goes wrong:** `TypeError: namedtuple() got an unexpected keyword argument 'defaults'` on 3.6.9 (confirmed).
**Why it happens:** The `defaults` kwarg was added in 3.7. Tutorials/examples often show it.
**How to avoid:** Use `typing.NamedTuple` (supports defaults on 3.6.1+, verified) — NOT `collections.namedtuple` — for any named tuple needing default field values.

### Pitfall 6: Documenting "run with pytest" when pytest isn't installed
**What goes wrong:** A plan/README says `python3.6 -m pytest` and it fails (`No module named pytest`).
**Why it happens:** Prior research docs (ARCHITECTURE.md line 149, STACK.md lines 74) say "runnable with `python3.6 -m pytest`". This was never verified — pytest is not installed and cannot be (AGENTS.md).
**How to avoid:** Specify `python3.6 -m unittest discover -s tests -v` everywhere.

## Code Examples

Verified patterns (empirically tested on 3.6.9 unless noted). These are REFERENCE DESIGNS for the planner/executor — not final code.

### The gate: `tools/check_imports.py` (AST-based, stdlib, 3.6-compatible) — TESTED

Empirically verified against a synthetic tree: catches all 7 static violations in a `leaky.py` (incl. `import pymol.cmd as c`, `from pymol.cgo import CGO`, `import PyQt5.QtCore`, `from PyQt5 import QtWidgets as W`), flags dynamic `importlib.import_module('pymol.cmd')` for review, and produces **0 false positives** on a file whose comments/string literals mention `import pymol`. Correctly skips `pymol_layer/` and `ui/`.

```python
#!/usr/bin/env python3.6
"""tools/check_imports.py — enforce the pure-Python testability boundary.

Scans all .py under c14/ EXCLUDING c14/pymol_layer/ and c14/ui/.
Fails (exit 1) if any scanned file imports pymol.* or PyQt5.* (any form:
`import pymol`, `from pymol.Qt import ...`, `import pymol.cmd as c`, etc.).
Also flags dynamic imports (__import__/importlib) naming pymol/PyQt5 for review.

Pure stdlib. Python 3.6 compatible. Invoke:
    python3.6 tools/check_imports.py
Exit 0 = clean; 1 = violations.
"""
import ast
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "c14")
SKIP_DIRS = {"pymol_layer", "ui", "__pycache__"}
BANNED_TOP = ("pymol", "PyQt5")


def _banned(module_name):
    if not module_name:
        return False
    return module_name.split(".", 1)[0] in BANNED_TOP


def violations_in(path, rel):
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as e:
        return ["%s:%d SyntaxError (py_compile would fail): %s" % (rel, e.lineno or 0, e.msg)]
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _banned(alias.name):
                    out.append("%s:%d import %s" % (rel, node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if _banned(node.module):
                names = ", ".join(a.name for a in node.names)
                out.append("%s:%d from %s import %s" % (rel, node.lineno, node.module, names))
    # Secondary: dynamic imports of banned modules (AST can't see these as Import nodes)
    for i, line in enumerate(src.splitlines(), 1):
        s = line.strip()
        if s.startswith("#"):
            continue
        if ("__import__" in s or "import_module" in s) and ("pymol" in s.lower() or "pyqt5" in s.lower()):
            out.append("%s:%d REVIEW dynamic import: %s" % (rel, i, s))
    return out


def main():
    bad = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]  # prune in-place
        for fn in sorted(filenames):
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT)
            bad.extend(violations_in(full, rel))
    if bad:
        sys.stderr.write("IMPORT BOUNDARY VIOLATIONS (%d):\n" % len(bad))
        for b in sorted(bad):
            sys.stderr.write("  " + b + "\n")
        sys.stderr.write("Domain-tier files must not import pymol/PyQt5. "
                         "Move the import into c14/pymol_layer/ or c14/ui/.\n")
        return 1
    print("check_imports: clean (no pymol/PyQt5 imports in c14/ domain tier)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Optional fast pre-commit (grep one-liner) — NOT a replacement for the AST gate:**
```bash
grep -rnE "^[[:space:]]*(import|from)[[:space:]]+(pymol|PyQt5)(\.|[[:space:]])" c14/ \
  --exclude-dir=pymol_layer --exclude-dir=ui && echo "VIOLATION" || echo "clean"
```
Caveat: anchored grep is fairly safe but cannot distinguish aliased submodule imports as precisely as AST and offers no dynamic-import review. Use AST as the CI gate of record.

### `MolAction` as `typing.NamedTuple` (the `@dataclass` replacement) — TESTED on 3.6.9

```python
# c14/story/model.py  — pure-Python, no pymol import. Gate passes.
from typing import NamedTuple, Optional

class MolAction(NamedTuple):
    """Molecular-layer intent emitted by the engine. Pure data -> unit-testable.
    The pymol_layer translates this to cmd.* calls. Domain never imports pymol."""
    op: str                              # "load"|"show"|"hide"|"select_focus"|"zoom"|"color"|"delete"|"protonate"|"edit"|"restore"
    target: Optional[str] = None         # asset key e.g. "pdb:1TNR" or object name
    args: Optional[dict] = None          # caller does `action.args or {}` (no mutable default)

# Verified on 3.6.9: defaults work; two instances do not share a dict.
```

### Engine with injectable `MolAction` sink (dependency injection at the boundary)

```python
# c14/engine.py  — pure-Python. Gate passes.
from typing import Callable, List, Optional
from c14.story.model import MolAction

class GameEngine:
    def __init__(self, story, rng, mol_sink=None):
        # mol_sink is a callable accepting List[MolAction]; tests pass a mock.
        # In production, the controller (ui/) passes pymol_layer.molops.apply_all.
        self._mol_sink = mol_sink or (lambda actions: None)
    # ... turn loop emits actions via self._mol_sink([...]) ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-file PyMOL plugin | Package plugin (`c14/` + `__init__.py`) | PyMOL 2.x (`plugins/__init__.py:findPlugins` discovers dirs with `__init__.py`) | A package keeps the testability boundary (import engine without Qt). Single-file can't. |
| `pmgqt`/Tk plugin UI | `from pymol.Qt import QtCore, QtGui, QtWidgets` | PyMOL 2.x; all 30 reference plugins ported 2024 | Modern Qt only — confirmed no `pmgqt`/`Tkinter` in any current reference plugin. |
| `dataclasses` for value types | `typing.NamedTuple` (3.6-compatible) | dataclasses is 3.7+ | Required on 3.6.9 test env. |
| `pytest` for unit tests | `unittest` (stdlib) | pytest not installed in WSL env | Only `python3.6 -m unittest` is available. |
| Regex/grep import checks | `ast`-based import checks | always available (stdlib) | No false positives; catches aliased submodule imports. |

**Deprecated/outdated in prior research docs (corrected here):**
- ARCHITECTURE.md line 149 / STACK.md line 74 / SUMMARY.md: "`python3.6 -m pytest`" → **WRONG, pytest not installed; use `python3.6 -m unittest`**.
- ARCHITECTURE.md lines 164-173 `model.py` example using `@dataclass` → **BANNED on 3.6.9; use `typing.NamedTuple`**.
- ARCHITECTURE.md line 107/155 `c14/controller.py` at `c14/` root → **must be `c14/ui/controller.py`** for the gate to hold.

## Open Questions

1. **Should domain modules ever reference pymol types via `TYPE_CHECKING` + string annotations?**
   - What we know: `if TYPE_CHECKING: from pymol import cmd` (inside the guard) is NOT executed at runtime (TYPE_CHECKING is `False` at runtime — verified), so it doesn't break WSL import. String annotations (`def f(x: 'pymol.cmd.Cmd')`) are stored unevaluated (verified) — safe.
   - What's unclear: should the gate ALLOW `TYPE_CHECKING`-guarded pymol imports, or BAN them too? An AST gate sees the `Import` node inside the `if` block and flags it regardless of the guard.
   - Recommendation: **BAN them (strict).** The architecture (MolAction = pure data) means domain never needs to name a pymol type. A strict ban keeps the gate trivial (any `pymol`/`PyQt5` Import/ImportFrom = fail) and the boundary airtight. If a future phase genuinely needs type-cross-references, reconsider then (the gate would need TYPE_CHECKING-awareness — more complex). **Planner decision: confirm the strict policy.**

2. **Should `tests/` also be gate-scanned?**
   - What we know: The success criterion scopes the gate to `c14/` only. `tests/` lives at repo root, outside `c14/`. Pure-Python tests in `tests/` should also be import-clean (they test domain modules), but smoke/Qt tests (if any lived there) might legitimately import pymol.
   - Recommendation: Keep the gate scoped to `c14/` (matches the criterion). Separately, `tests/` should contain ONLY pure-Python unittests (no pymol imports); put any cmd-exercising scripts in `smoke/`. The planner can add a one-line note that `tests/` follows the same import-clean discipline, enforced by review rather than the gate.

3. **Exact CI invocation mechanism.**
   - What we know: The gate must run in CI (per "CI grep gate"). There is no CI config in the repo yet (no `.github/`, no `Makefile`).
   - Recommendation: The planner should specify a `make check` or a documented `python3.6 tools/check_imports.py && python3.6 -m py_compile ... && python3.6 -m unittest discover -s tests` command sequence as the canonical local+CI check. Whether to wire GitHub Actions is a separate (out-of-track) decision — flag for the user.

## Sources

### Primary (HIGH confidence — empirical or source-verified)
- **`python3.6` (3.6.9) empirical probes** (run 2026-08-13 in the actual WSL test env):
  - `compile()`/`exec()` tests of every banned/allowed syntax feature (walrus, f-string `=`, positional-only `/`, `match`, `from __future__ import annotations`, PEP 604 `|`, dataclasses, contextvars, importlib.metadata, `typing.NamedTuple` defaults, `collections.namedtuple(defaults=)`, `TYPE_CHECKING`, `random.choices`, string forward-ref annotations).
  - AST-gate prototype tested against a synthetic good/bad tree (7/7 violations, 0 false positives, correct dir-exclusion).
  - `python3.6 -m pytest --version` → `No module named pytest` (confirms unittest-only).
- **PyMOL 2.5.0 plugin loader source** (`tmp/pymol-src/modules/pymol/plugins/__init__.py`):
  - `findPlugins` (line 365-405): directory plugin → `<dir>/__init__.py` (line 396).
  - `load` (line 248-300): `__import__(self.mod_name, level=0)` (line 277) runs the package `__init__.py`.
  - `legacyinit` (line 302-324): `hasattr(mod, '__init_plugin__')` → `mod.__init_plugin__(pmgapp)` (line 320-321).
  - `addmenuitemqt` (line 100-108): raises `QtNotAvailableError` if no Qt (line 105-106).
- **Reference plugins** (`Pymol-script-repo/plugins/*.py`, 30 files): import-pattern survey — PyQt5 is ALWAYS via `pymol.Qt` (zero direct `import PyQt5`/`from PyQt5`); `from pymol import cmd` dominates; zero legacy `pmgqt`/`Tkinter`. Confirms the modern convention.

### Secondary (MEDIUM confidence — corroborating)
- `.planning/research/ARCHITECTURE.md` — 3-tier layering, `c14/` structure, `MolAction` concept (used as baseline; two corrections noted above).
- `.planning/research/STACK.md` — Python 3.6 compatibility rules (walrus/f-string=/positional-only bans corroborated empirically here).
- `.planning/research/SUMMARY.md` — `from __future__ import annotations` ban (corroborated empirically: "future feature annotations is not defined" on 3.6.9).

### Tertiary (LOW confidence)
- None. All findings are empirically or source-verified.

## Metadata

**Confidence breakdown:**
- 3-tier layout & `__init__.py` pattern: **HIGH** — PyMOL source-verified + Python import semantics.
- CI gate design (AST): **HIGH** — empirically tested on 3.6.9.
- Python 3.6 syntax constraints: **HIGH** — every claim empirically tested on the actual 3.6.9 env.
- Import-cleanliness strategy: **HIGH** — `TYPE_CHECKING`/string-annotation behavior empirically verified; strict-ban recommendation is design-driven (MEDIUM) but architecturally sound.
- Reference plugin conventions: **HIGH** — directly observed across 30 files.

**Research date:** 2026-08-13
**Valid until:** 2027-02-13 (stable — stdlib + PyMOL 2.5.0 source are fixed; the only drift risk is if the user changes the test-env Python version, which AGENTS.md pins to 3.6.9)

**Decisions the planner must make (flagged):**
1. Confirm strict-ban policy on `TYPE_CHECKING`-guarded pymol imports in domain tier (recommend: BAN).
2. Confirm `c14/controller.py` → `c14/ui/controller.py` (recommend: YES).
3. Confirm `c14/__init__.py` lazy-delegation pattern (recommend: YES — it's forced by the loader + 3.6).
4. Confirm `MolAction` = `typing.NamedTuple` (recommend: YES; plain class acceptable for types needing mutable defaults).
5. Confirm test runner = `python3.6 -m unittest` (recommend: YES — pytest unavailable).
6. Confirm gate = AST-based `tools/check_imports.py`, exclusions `{"pymol_layer","ui"}` (recommend: YES).
