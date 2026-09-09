# Coding Conventions

**Analysis Date:** 2026-09-10

These are the *observed, enforced* conventions of the `rpg/` package (~6,500 lines across `rpg/`, plus `tools/` and `tests/`). The repo is past the spec-only stage: Phases 1–7.1 shipped a working plugin (engine, story graph, PyMOL layer, Qt UI, story editor). Every convention below is backed by a real file and, where noted, by a machine-checkable gate.

## Binding Rules from spec.md (non-negotiable)

These are constraints first; code style second. Violations fail gates or require human approval:

- **No fabricated science.** Every claim, citation (DOI/PDB ID), and pathway fact must be verified against a source AND explicitly human-approved before use. Enforced architecturally: story JSON references `claim_id`s that must resolve in `data/citations.json` with `approval_status == "approved"` — checked by `tools/check_citations.py` (exit 1 blocks release). The predicate is strict equality, never `!= "pending"` (a `rejected` claim must fail — see `rpg/citations.py:100-109`).
- **No new dependencies silently.** Only what `pymol-open-source` ships: PyQt5 via `pymol.Qt`, numpy. Everything else is **stdlib only, Python 3.6-compatible**. If another lib is needed: write the list to a file, seek explicit user approval, then either the user installs it or the agent vendors it under `./3rd_party_lib/` (git-ignored) with license noted.
- **Modern Qt interface only:** `from pymol.Qt import QtCore, QtGui, QtWidgets` (see `rpg/ui/main_window.py:60`). Never legacy `pmgqt`/Tk.
- **Protonation** must be physiological pH, reaction-relevant, or user-adjustable (`rpg/protonation_catalog.py` defaults `protonation_pref` to `"physiological"` — `rpg/state.py:121`).
- **Efficient, traceable, clean, safe; structured repo.** Traceability is concretely implemented as: plan references in headers, `# src:` PyMOL source citations (below), and story content kept as data (`data/story_glucose/*.json`) separate from code.
- **Never commit:** `Pymol-script-repo`, `tmp`, `3rd_party_lib/**`, `*.env`, `*.npy`/`*.npz`, secrets, `rpg/data/assets/downloaded/` (runtime fetch cache), `dist/` (build output), `__pycache__/` (see `.gitignore`).
- **PyMOL API use:** all molecular operations go through `pymol.cmd.*`; never reach into PyMOL internals when a `cmd.` API exists. Verify signatures against `tmp/pymol-src/modules/pymol/` before citing them (see the `# src:` convention below).

## Naming Patterns

**Files:**
- Modules: `snake_case.py` (`edit_router.py`, `protonation_catalog.py`, `main_window.py`).
- Unit tests: `test_<module_under_test>.py` in `tests/` (`tests/test_molops.py` ↔ `rpg/pymol_layer/molops.py`); editor batteries use `test_story_editor_<area>.py`.
- Headless smokes: `<feature>_smoke.py` in `tools/` (`tools/molops_smoke.py`, `tools/edit_smoke.py`).
- Gates: `check_<invariant>.py` in `tools/` (`tools/check_imports.py`, `tools/check_alter_gate.py`, `tools/check_citations.py`, `tools/check_edit_coverage.py`).
- Shell tools: `snake_case.sh` (`tools/run_headless.sh`, `tools/build_plugin_zip.sh`).

**Classes:** PascalCase, always with explicit `(object)` base (Python 3.6 style): `RngEngine` (`rpg/rng.py:29`), `MolOps` (`rpg/pymol_layer/molops.py:120`), `GameEngine`, `StoryGraph`, `CitationRegistry`.

**Functions/methods:** `snake_case`. Private/internal: single leading underscore (`_open_main_window` in `rpg/ui/plugin_entry.py:19`, `_resolve_story_dir` in `rpg/ui/main_window.py:74`). Test methods: `test_<behavior>` (`test_same_seed_same_sequence`).

**Variables/constants:** `UPPER_SNAKE` for module constants (`BANNED_TOP`, `SKIP_DIRS` in `tools/check_imports.py:33-34`; `APPROVED/PENDING/REJECTED` in `rpg/citations.py:58-60`). Instance attributes `snake_case`, private ones underscore-prefixed (`self._cmd`, `self._rng`, `self._claims`).

**Data identifiers:** JSON keys `snake_case` (`approval_status`, `source_id`). Story node ids are lowercase dotted (`intro.start`, `edit.prompt`, `tca.shuffle`); citation claim ids are SCREAMING-KEBAB (`GLY-PFK-01` in `data/citations.json`).

## Code Style

**Python version discipline (the most important style rule):**
Target is **Python 3.6 (3.6.9, the WSL test interpreter)**. Explicitly banned repo-wide (repeated in module headers, e.g. `rpg/pymol_layer/molops.py:38-40`, `rpg/rng.py:14`):
- NO f-strings — use `"...".format(...)` (often positional `{0}`) or `%` formatting. Verified: zero f-strings in `rpg/`, `tools/`, `tests/`.
- NO `@dataclass` (3.7+; verified missing on 3.6.9) — plain classes on instance attributes.
- NO walrus operator, NO `capture_output=`/`text=` kwargs in `subprocess.run` (3.7+; see `tests/test_integration.py:26-29`), NO 3.7+ stdlib modules.
- `pathlib` IS allowed (3.4+) — used in `rpg/paths.py`.
- `random.choices(..., weights=...)` (3.6+) allowed.

**Type annotations:** comment-style, on the line below the signature:
```python
def weighted_pick(self, items, weights):
    # type: (list, list) -> object
```
(`rpg/rng.py:71-72`). Used on most functions; not mechanically enforced.

**Line length:** ~100 chars max; a handful reach 108 (`rpg/engine.py`). No tooling enforces this.

**Formatting:** No formatter/linter config exists (no black/flake8/pre-commit — none may be installed anyway). Style is by convention, kept consistent by review + AST gates. Indentation 4 spaces; data JSON files use 2-space indent (see Data Conventions).

**Module layout (header comment + docstring):**
1. `#!` shebang only in `tools/*.py` scripts (`#!/usr/bin/env python3.6`).
2. A `#`-comment header block capturing: owning plan/phase (e.g. "Phase 4 Plan 04-01"), design rationale, gate-exemption status, gotchas, and 3.6 constraints — e.g. `rpg/pymol_layer/edit_ops.py:1-35`, `rpg/ui/main_window.py:1-43`.
3. A module docstring describing the public API/contract (reST-ish `:meth:`/`` `` `` cross-references).
4. Imports.
5. Code.

**PyMOL source citations (machine-checked):** EVERY direct `cmd.*` call carries a citation comment on the line directly above, pinned to PyMOL 2.5.0 line numbers:
```python
# src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show
self._cmd.show(action.args["rep"], action.args.get("sele", action.target))
```
(`rpg/pymol_layer/molops.py:146-147`). Presence is asserted by unit tests (`test_citations_present_in_source` in `tests/test_molops.py`) and smokes carry their own citations (`tools/molops_smoke.py:45-47`).

**Plan traceability:** headers and comments reference owning plans and frozen conventions, e.g. "Phase 6 (06-01): FROZEN-verbatim from 05.4-CONVENTION.md:125-139" (`rpg/pymol_layer/molops.py:161`). When changing frozen code, keep or update these references.

## Import Organization

**Order (no `__all__` anywhere; no formatter sorting — this is the observed grouping):**
1. Stdlib imports (`import json`, `import unittest`).
2. Blank line.
3. `rpg.*` imports — relative inside the package (`from .paths import selfcheck` in `rpg/__init__.py:27`), absolute across tiers (`from rpg.story.model import MolAction`).

**The testability boundary (AST-gated):** files under `rpg/` root (domain tier) MUST NOT import `pymol` or `PyQt5` — any form, including inside `if TYPE_CHECKING:`. Enforced by `tools/check_imports.py` (`SKIP_DIRS = {"pymol_layer", "ui", "__pycache__"}`); tested by `tests/test_imports.py`. Only `rpg/pymol_layer/` (molecular ops) and `rpg/ui/` (Qt) may import pymol/PyQt5.

**Lazy imports in the Qt layer:** `pymol.Qt`/`pymol.plugins` imports go INSIDE functions, not at module top, so plugin import never touches Qt before the GUI is ready (`rpg/ui/plugin_entry.py:15,22`; matches `Pymol-script-repo/plugins/dynoplot.py` precedent). Sibling dialogs are imported lazily inside handlers so a missing sibling doesn't break `py_compile` (`rpg/ui/main_window.py:19-22`).

**Third-party imports:** none. Stdlib only.

**No path aliases.** Scripts in `tools/` that import `rpg.*` insert the repo root on `sys.path` first, with `# noqa: E402` on the import (`tools/check_citations.py:30-33`).

## Error Handling

**Fail loud, at the boundary, with a typed exception.** Observed raise counts across `rpg/`: ValueError 16, RuntimeError 13, NotImplementedError 4, plus FileNotFoundError, KeyError, IndexError, and one custom domain error.

**Patterns (use the same ones):**
- `ValueError` — invalid input values / unknown enum keys: unknown edit_type (`rpg/pymol_layer/molops.py:267`), unknown align method (`molops.py:197`), malformed registry schema (`rpg/citations.py:83-97`).
- `RuntimeError` — a required collaborator was not injected: `"molops.load requires an AssetManager"` (`molops.py:200`).
- `NotImplementedError` — genuinely unknown op, so a stray op fails loudly (`molops.py:290`).
- `FileNotFoundError` — missing bundled data, with a message that explains the likely cause (`rpg/paths.py` `selfcheck()`).
- Custom domain exceptions sparingly: `EditRoutingError` (`rpg/edit_router.py`).

**JSON loading must reject duplicate keys:** loaders use `object_pairs_hook` raising `ValueError` on duplicates — `json.load` silently last-wins otherwise (`rpg/citations.py:29-46`, `_no_duplicate_keys`).

**Strict-equality gate predicates:** `approval_status == "approved"`, never `!= "pending"` (`rpg/citations.py:109`) — so `rejected` claims cannot pass.

**Graceful degradation only where specified:** the Controller swallows a failing MolAction dispatch and continues (`rpg/ui/controller.py`, "Blocker 1 fix c", tested in `tests/test_controller.py`); smoke-script bonus stages wrap each stage in `try/except` and record the failure instead of crashing (`tools/molops_smoke.py:104-108`).

**Fail loud at plugin load:** `rpg/__init__.py:26-28` calls `paths.selfcheck()` before registering the menu — a broken bundled-data layout aborts startup.

**Pure resolvers:** path helpers never check existence; resolve only, let callers open/handle (`rpg/paths.py` `data_path()` docstring). Exception: `selfcheck()` exists precisely to verify layout at load.

## Logging

**Framework:** none. No `logging`/`getLogger` anywhere in `rpg/` or `tools/` — plain `print()` to stdout.

**Patterns:**
- Unit-test-visible verdicts use structured stdout sentinels: `"SMOKE: {PASS|FAIL} <name> <detail>"` per stage and a final `"SMOKE_RESULT: PASS"` sentinel (`tools/molops_smoke.py:75-80,178`). The sentinel is the *only* reliable headless verdict (the Windows bat wrapper always exits 0 — see TESTING.md).
- Gate scripts print human-readable reports to stdout/stderr and communicate verdicts via three-way exit codes (0 pass / 1 fail / 2 config error) — the Phase 1 convention defined in `tools/check_citations.py:9-12`.

## Comments

**When to comment (observed norms):**
- Design rationale and *why*, not *what* — especially pitfall mitigations ("Anti-Pattern 7 mitigation", `rpg/rng.py:4`).
- Plan/phase traceability in module headers.
- `# src:` PyMOL API citations on every direct `cmd.*` call.
- Gotchas with provenance: "Gotcha #2: `__file__` in a PyMOL-run script resolves to the pymol package's `__init__.py`" (`tools/molops_smoke.py:17-20`).
- Empirical corrections: notes where a cited API behaved unexpectedly and how it was verified (e.g. the `cealign` argument-order note, `molops.py:194-195`).

**Docstrings:** every public class and method carries one; test methods each carry a one-line docstring stating the property under test (`tests/test_rng.py`). Module docstrings state scope + run command + boundary guarantees.

## Function Design

**Size:** small, single-purpose methods; per-action dispatch via `if/elif` chains over an `op` string (`MolOps.apply`, `rpg/pymol_layer/molops.py:140-291`) — follow this pattern for new ops rather than adding new translation layers.

**Dependency injection at every seam (THE core pattern):** anything PyMOL/Qt/environment-specific is a constructor parameter, never a module import in testable code:
```python
def __init__(self, cmd, asset_manager=None, editops=None, protonation=None):
    self._cmd = cmd
```
(`rpg/pymol_layer/molops.py:134-138`). Same pattern for `AssetManager(cmd)`, `EditOps(cmd)`, the Controller's `molaction_sink`/`view_provider`/`view_applier`/`prompt_fn`/`count_fn` (`rpg/ui/controller.py`, `rpg/ui/main_window.py:10-16`). This is what makes the domain + dispatch logic unit-testable in WSL with no PyMOL installed.

**Parameters:** keyword-ish dicts inside data carriers (`MolAction.args`), `.get()` with defaults for optional keys, required keys via `[]` so a missing key raises loudly.

**Return values:** plain dicts for JSON-serializable state (`RngEngine.get_state`), `Path` objects from path helpers (callers `str()` them for `cmd.*` APIs — `rpg/paths.py:26-43`), `collections.namedtuple` for small immutable records (`ScriptBlock` in `tests/script_blocks.py:46`).

**One MolAction per `apply()` call** (the 02-04 contract): engines emit `for action in actions: sink(action)`; batch convenience methods are thin loops over the single-action path (`molops.apply_all`, `molops.py:293-300`).

## Module Design

**Exports:** plain classes + module-level functions; no `__all__`, no barrel re-exports. `rpg/pymol_layer/__init__.py` and `rpg/ui/__init__.py` are empty (1 line); `rpg/story/__init__.py` (15 lines) is the only subpackage init with content. The plugin entry is `rpg/__init__.py.__init_plugin__` → delegate to `rpg/ui/plugin_entry.py` (never import pymol/Qt in `rpg/__init__.py` itself).

**Layer placement (where code goes):**
- Domain/pure logic → `rpg/` root or `rpg/story/` (no pymol/PyQt5 — gate-enforced).
- Anything calling `cmd.*` → `rpg/pymol_layer/`. `cmd.alter` may appear ONLY in `rpg/pymol_layer/edit_ops.py` (allowlist enforced by `tools/check_alter_gate.py`; `edit_ops.py` always pairs alter/h_add with `cmd.sort` + `cmd.rebuild` per the alter→sort corruption trap).
- Qt/UI → `rpg/ui/` (controller is deliberately Qt-free; dialogs/panels are QtWidgets).

**Data conventions:** data JSON is 2-space indent, `ensure_ascii=False`, trailing newline on file write; the canonical serializer is `tools/story_editor_json.py` (`dumps()` returns without trailing newline) and no-op saves must be byte-identical so diffs stay reviewable (rule family pinned in `tests/test_story_editor_json.py`). Content lives in `data/` (dev) and is bundled into `rpg/data/` at zip-build time by `tools/build_plugin_zip.sh`.

## Git / Commit Conventions

Observed from history (`git log`): Conventional-Commit-ish with plan/area scope — `feat(07.1-17): node-lifecycle editor ...`, `fix(security): ...`, `test(07.1-18): structural chrome battery ... (8 tests)`, `docs(07.1-11): complete ... plan`, `chore: track oc stats`. TDD granularity is preserved: separate `test(...)` (RED) commits precede `feat(...)` (GREEN) commits per task. Do not commit gitignored paths (top of this doc).

---

*Convention analysis: 2026-09-10*
