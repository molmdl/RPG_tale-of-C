# Testing Patterns

**Analysis Date:** 2026-09-10

The repo has a mature, working test suite: **43 Python files in `tests/`** (41 test modules + shared helper `tests/script_blocks.py` + `__init__.py`), **~599 `test_*` methods**, plus **12 headless smoke scripts** in `tools/` and **4 release gates**. There is no CI server (no `.github/`) — verification is invoked manually via the exact commands below.

## The Three-Tier Verification Model

Every piece of code is verified at exactly one of three tiers (defined in `AGENTS.md`, implemented across the repo). Know the tier *before* writing code:

**Tier 1 — Pure-Python unit tests (WSL, `python3.6`):**
Everything in `rpg/` except Qt widgets, because PyMOL collaborators are constructor-injected and the import boundary is AST-gated (`tools/check_imports.py`). Includes all of `rpg/story/`, the engine, `rpg/pymol_layer/` dispatch logic, and the Qt-free `rpg/ui/controller.py`. No PyMOL installed — mocks prove dispatch *mapping*; smokes prove the real API.

**Tier 2 — Headless PyMOL smokes (WSL → Windows):**
Pure-`pymol.cmd.*` scripts (NO Qt) run via the WSL→Windows bridge: `tools/run_headless.sh` → `cmd.exe /c "C:\src\run-conda-pymol.bat -cq <script>"`. Prove the REAL `cmd.*` API contract (e.g. `tools/molops_smoke.py`, `tools/edit_smoke.py`, `tools/protonation_smoke.py`).

**Tier 3 — Human-verify (real Windows PyMOL GUI):**
Anything touching `pymol.Qt.*` at runtime (MainWindow, dialogs, `rpg/ui/widgets.py`). CANNOT be automated from WSL (Qt needs a real display). Only `python3.6 -m py_compile` is WSL-verifiable for `rpg/ui/` — importing Qt modules in WSL fails, and that is EXPECTED (`rpg/ui/main_window.py:35-40`). GUI verification is recorded as an explicit human checkpoint in plan summaries.

## Test Framework

**Runner:**
- **stdlib `unittest` ONLY.** NO pytest — explicitly documented ("NO pytest (not installed)", `tests/test_citations.py:15`, `tests/test_validate.py:20`). No pytest fixtures, no `assert`-style tests.
- Interpreter: `python3.6` (3.6.9) in WSL. No config files: no `pytest.ini`, `tox.ini`, `pyproject.toml`, `setup.cfg` — none needed.

**Assertion Library:** `unittest.TestCase` methods (`assertEqual`, `assertNotEqual`, `assertTrue`, `assertIn`, `assertIsInstance`); exceptions via the context-manager form `with self.assertRaises(...)` (32 uses, e.g. `tests/test_imports.py`).

**Run Commands (canonical):**
```bash
# Full suite + import-boundary gate (the canonical Phase-1 chain, check_imports.py:18)
python3.6 tools/check_imports.py && python3.6 -m unittest discover -s tests -v

# Full suite alone
python3.6 -m unittest discover -s tests -v

# One module
python3.6 -m unittest tests.test_rng -v

# Release gates (all three-way exit codes: 0 pass / 1 fail / 2 config error)
python3.6 tools/check_imports.py       # no pymol/PyQt5 in domain tier
python3.6 tools/check_alter_gate.py    # cmd.alter only in rpg/pymol_layer/edit_ops.py
python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json
python3.6 tools/check_edit_coverage.py # every cast.json enzyme has >=1 edits.json entry

# Headless smoke (Tier 2)
bash tools/run_headless.sh tools/molops_smoke.py
```

The post-save gate sequence for story content (also printed in the story editor Help tab, `tests/test_story_editor_boot.py:74-85`): `story_editor_lint` → `python3.6 -m unittest discover -s tests` → `tools/check_citations.py` → `tools/check_edit_coverage.py` → `git diff`.

## Test File Organization

**Location:** centralized in `tests/` (NOT co-located with source). `tests/__init__.py` makes it a package.

**Naming:** `test_<module>.py` mirrors the module under test: `tests/test_molops.py` → `rpg/pymol_layer/molops.py`; `tests/test_engine.py` → `rpg/engine.py`. The browser-based story editor gets a battery family: `tests/test_story_editor_<area>.py` (`_boot`, `_save`, `_json`, `_lifecycle`, `_graph`, ...).

**Shared helpers:** `tests/script_blocks.py` — browser-faithful `<script>`-block extractor (stdlib HTMLParser, replaces naive regex; CodeQL fix). Import it, don't reimplement.

**Structure:**
```
tests/
├── __init__.py
├── script_blocks.py          # shared HTML-tokenizer helper
├── fixtures/edit_routing/    # JSON fixtures (story.json, edits.json, manifest.json)
├── test_<module>.py          # one file per module under test
└── test_story_editor_*.py    # structural batteries for tools/story_editor.py
```

Committed molecular fixtures live in `rpg/data/assets/bundled/` (`_smoke.pdb` etc. — ship in the plugin zip); the runtime download cache `rpg/data/assets/downloaded/` is git-ignored. Story content fixtures are the REAL data files (`data/story_glucose/`, `data/story/`) — tests run against real content, not synthetic copies.

## Test Structure

**Module docstring states: scope, run command, boundary guarantees** (`tests/test_rng.py:1-8`, `tests/test_engine.py:1-11`).

**Suite organization (observed pattern):**
```python
"""Unit tests for rpg.rng.RngEngine. Pure-Python, stdlib only.

Run: ``python3.6 -m unittest tests.test_rng -v``
"""
import json
import unittest

from rpg.rng import RngEngine


class TestRngEngine(unittest.TestCase):

    def test_same_seed_same_sequence(self):
        """Two RngEngine(42) produce identical random() sequences (determinism)."""
        a = RngEngine(42)
        b = RngEngine(42)
        self.assertEqual([a.random() for _ in range(10)],
                         [b.random() for _ in range(10)])


if __name__ == "__main__":
    unittest.main()
```
(`tests/test_rng.py`.)

**Patterns:**
- One TestCase class per concern; every test method has a docstring naming the property under test.
- `setUp`/`tearDown` manage temp resources: track paths/dirs in lists, clean up in `tearDown` with try/except (`tests/test_engine.py:35-52`). `tempfile.mkdtemp`/`NamedTemporaryFile` for filesystem edges.
- CWD-independence invariant: resolve repo paths relative to `__file__`, never `os.getcwd()`:
  ```python
  def _story_dir():
      # type: () -> str
      return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "data", "story_glucose")
  ```
  (`tests/test_controller.py:34-38`.)
- Gate/gate-test invocations use `subprocess` with `stdout/stderr=PIPE` + manual decode (NOT `capture_output=`/`text=` — both 3.7+) and `sys.executable` rather than a hardcoded interpreter (`tests/test_integration.py:26-32`).
- Boundary proof test: after a full playthrough with save/load, assert `'pymol' not in sys.modules` (`tests/test_engine.py` docstring; "Qt-free import" implicit gate in `tests/test_controller.py`).

## Mocking

**Framework:** none — NO `unittest.mock`. All doubles are **hand-rolled recording fakes** defined at the top of the test module. This is deliberate: 3.6-safe, no magic, and each fake mirrors the REAL collaborator's signature.

**Patterns:**

Recording stub via `__getattr__` (for wide APIs like `cmd`):
```python
class MockCmd(object):
    """Records every cmd.* dispatch as (name, args, kwargs); returns 0."""
    def __init__(self):
        self.calls = []
        self._count = 3
    def __getattr__(self, name):
        def f(*a, **k):
            self.calls.append((name, a, k))
            return 0
        return f
    def count_atoms(self, sel="(all)"):   # explicit method bypasses __getattr__
        return self._count
```
(`tests/test_molops.py:54-80`.)

Signature-mirroring fakes (for narrow collaborators):
```python
class MockAssets(object):
    def __init__(self):
        self.calls = []
    def load_bundled(self, filename, object_name):
        self.calls.append(("load_bundled", filename, object_name))
        return object_name
```
(`tests/test_molops.py:83-105`; same pattern for `MockEditOps`, `MockProtonationManager`, `MockMolOps`, `MockView` in `tests/test_controller.py`.)

Callable seams get plain functions/lambda: `prompt_fn` (QMessageBox.question replacement), `count_fn` (cmd.count_atoms replacement), and the engine's `molaction_sink` (often just a plain list's `.append`, `tests/test_engine.py:8-10`). Failing-collaborator tests: fakes accept `fail_indices` to raise on configured call numbers (`tests/test_controller.py` `MockMolOps`).

**What to mock:**
- `pymol.cmd` (always — Tier 1 has no PyMOL).
- Qt surfaces: `prompt_fn`, `view_provider`/`view_applier` — never real Qt in WSL.
- Filesystem edges (temp dirs for saves/loads).
- Time/entropy: use fixed-seed `RngEngine(42)` for determinism, never patch `random`.

**What NOT to mock:**
- The story graph, engine, interpreter, persist, EditRouter — tests run against the REAL data (`data/story_glucose/`, `rpg/data/edits.json`).
- Content correctness: byte-identical no-op serialization is asserted against the real data files (`tests/test_story_editor_json.py` "ByteIdenticalNoopOracle"); citation/edit gates run on the real registries.
- PyMOL's real API behavior — that is Tier 2's job (smokes), not something to fake more precisely.

## Headless Smoke Scripts (Tier 2)

**Template — follow `tools/molops_smoke.py` exactly:**
1. Header comment: owning plan, purpose, contract rules (Gotcha #1/#2/#6).
2. `sys.path.insert(0, os.getcwd())` — repo root cwd makes `import rpg` work (`tools/molops_smoke.py:60`).
3. `import pymol; from pymol import cmd`; then `pymol.finish_launching()` BEFORE any `cmd.*` call (`:70`).
4. `check(name, ok, detail)` helper printing `"SMOKE: PASS|FAIL <name> <detail>"` and appending to a `FAILS` list (`:75-80`).
5. Each stage wrapped in `try/except` recording a FAIL instead of crashing (`:104-116`).
6. Every direct `cmd.*` call carries a `# src:` citation (`:112`).
7. Final verdict is a **stdout sentinel, NOT the exit code**: `print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))` (`:178`).

**Why the sentinel:** through `run-conda-pymol.bat` the process ALWAYS exits 0 (conda deactivate overwrites `%ERRORLEVEL%`; PyMOL's `parsing.run_file` swallows exceptions — Gotcha #1, `tools/molops_smoke.py:12-16`). `tools/run_headless.sh` therefore greps `^SMOKE_RESULT: PASS` (presence = pass), uses exit codes only for infra failures (124 = timeout after 150s), and captures output to `/tmp/opencode/<script>.txt`. Always `timeout 90/150 cmd.exe /c ...` from a Windows-readable path (`/mnt/c/...`).

## Fixtures and Factories

**Test data (observed patterns):**
- Real content files: tests load `data/story_glucose/` via the `__file__`-relative `_story_dir()` helper.
- Committed binary/molecular fixtures: `rpg/data/assets/bundled/*.pdb` (referenced via `rpg.paths.data_path(...)` so they resolve CWD-independently and in the installed plugin).
- JSON fixtures: `tests/fixtures/edit_routing/{story.json,edits.json,manifest.json}` for `tests/test_edit_router.py`.
- No factory library. Builders are small module-level helper functions or inline literals (`MolAction("load", "_smoke", {"source": "bundled", ...})`, `tools/molops_smoke.py:97-103`).
- Determinism fixture: `RngEngine(seed)` — same seed ⇒ identical sequence (`tests/test_rng.py`).

**Location:** `tests/fixtures/` for synthetic JSON; `rpg/data/assets/bundled/` for molecular fixtures that must ship; real `data/` for content.

## Coverage

**Requirements:** none enforced — no coverage tooling (nothing may be installed). Code coverage is by *design*: the AST gates make the untestable surface tiny. DATA coverage IS gated: `tools/check_edit_coverage.py` fails if a `cast.json` enzyme lacks an `edits.json` entry; `tools/check_citations.py` fails on any unapproved claim.

**View coverage:** not available (no coverage.py; do not install).

## Test Types

**Unit tests (Tier 1):** per-module, mocked collaborators, real data content. 41 modules covering domain, dispatch, routing, persistence, content, and editor batteries.

**Integration tests:** `tests/test_integration.py` — full-stack playthrough in pure Python: engine + interpreter + graph + RNG + save/load round-trip + reachability + citation gate, mock MolAction sink, `'pymol' not in sys.modules` proof. `tests/test_controller.py` wires Controller over the REAL glucose graph with mocked molops/view seams.

**Headless smokes (Tier 2):** 12 scripts, `tools/*_smoke.py` — real PyMOL API contract; verdict via `SMOKE_RESULT` sentinel through `tools/run_headless.sh`.

**E2E/GUI (Tier 3):** human-verify in Windows PyMOL. Not automatable; recorded as checkpoints (e.g. plan 06-14 verified the functional window: story renders, choices clickable, save/load dialogs).

**Structural batteries (Tier 1 variant):** the story editor's emitted HTML is tested by running the generator via `subprocess`, then scanning the output — ES5 discipline (no arrow functions/`let`/`const`/modules, `tests/test_story_editor_state.py`), boot-chrome contracts (`tests/test_story_editor_boot.py`), and browser-faithful script-block extraction via `tests/script_blocks.py`.

## Common Patterns

**Error testing:**
```python
with self.assertRaises(ValueError):
    molops.apply(MolAction("align", "obj", {"method": "bogus", "reference": "ref"}))
```
(context-manager form; assert the type, message checks via `assertRaisesRegex` are rare).

**Gate testing (subprocess, 3.6-safe):**
```python
proc = subprocess.run([sys.executable, GATE_SCRIPT], stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE)   # NO capture_output=/text= (3.7+)
out = proc.stdout.decode("utf-8")
```
(`tests/test_integration.py:26-29` pattern.)

**Citation-presence testing:** tests read the source file and assert every direct `cmd.*` call has the `# src:` comment above it (`tests/test_molops.py` — SC #4 machine-checkable).

**3.6 discipline in tests:** no f-strings, no `subTest` reliance observed, `unittest.main()` guard at bottom; helper functions annotated with `# type:` comments.

## Adding New Verification (checklist)

1. New pure logic in `rpg/` (or injected-collaborator logic in `pymol_layer/`/`ui/controller.py`) → unit tests in `tests/test_<module>.py` (Tier 1) with hand-rolled fakes; run via `python3.6 -m unittest tests.test_<module> -v`.
2. New `cmd.*` translation in `rpg/pymol_layer/` → unit tests prove dispatch mapping (MockCmd) + a `tools/<feature>_smoke.py` proving the real API (Tier 2), run via `bash tools/run_headless.sh tools/<feature>_smoke.py`.
3. New Qt widget/dialog (Tier 3) → `py_compile` only in WSL; record a human-verify checkpoint for a real Windows PyMOL session.
4. New story content → add `claim_id`s to `data/citations.json` (human-approved) and keep `tools/check_citations.py` + `tools/check_edit_coverage.py` green; run the full post-save gate sequence.
5. Never introduce a test dependency (no pytest, no mock libs) — stdlib `unittest` only, Python 3.6 compatible.

---

*Testing analysis: 2026-09-10*
