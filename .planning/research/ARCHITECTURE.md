# Architecture Research

**Domain:** PyMOL-plugin branching-narrative RPG (scientific game + molecular visualization)
**Researched:** 2026-08-12
**Confidence:** HIGH for PyMOL plugin / Qt structure (verified against `tmp/pymol-src/modules/pymol/` 2.5.0 source + 31 reference plugins); HIGH for story-graph model (verified against Inkle/ink official docs); MEDIUM for edit-routing details (design-driven, validated against `editing.py`/`editor.py` API surface).

## Standard Architecture

### System Overview

The plugin is a **layered single-process application** running inside PyMOL's Python interpreter. The hard constraint is testability: pure-Python game logic must run in WSL with `python3.6` (no PyMOL, no Qt), while PyMOL-cmd code runs headlessly via `run-conda-pymol.bat -cq`, and Qt/GUI code is human-verified only. This forces a strict dependency-direction rule: **the game layer never imports PyMOL or Qt; the molecular layer adapts game intents to `cmd.*`; the UI layer adapts game state to Qt widgets.**

```
┌──────────────────────────────────────────────────────────────────────┐
│  Qt UI Layer            (pymol.Qt — QtWidgets)  [HUMAN-VERIFY ONLY]    │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────────┐    │
│  │ Main Dialog  │ │ Choice Panel │ │ Cast/Help  │ │ Achievement  │    │
│  │ (QMainWindow │ │ (QListWidget │ │ Board      │ │ Board Widget │    │
│  │  + QTabWidget)│ │  + buttons) │ │ (read-only)│ │              │    │
│  └──────┬───────┘ └──────┬───────┘ └─────┬──────┘ └──────┬───────┘    │
├─────────┴──────────────┴─────────────────┴──────────────┴────────────┤
│  Controller / Orchestrator   (pure-Python, importable)               │
│  wires UI events → Engine calls; Engine events → PyMOL-layer calls    │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ GameEngine  (turn loop: present node → await choice → advance)  │   │
│  └────┬─────────────────────┬────────────────────┬───────────────┬─┘   │
├───────┴─────────────────────┴────────────────────┴───────────────┴─────┤
│  Pure-Python Domain Layer   (NO pymol, NO Qt — unit-testable in WSL)  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────┐│
│  │ StoryGraph │ │ StoryInterp│ │ GameState │ │ RngEngine  │ │EditRtr││
│  │ (JSON data)│ │ (walker)   │ │ (dict+ser)│ │ (seedable) │ │(table)││
│  └────┬───────┘ └─────┬──────┘ └─────┬──────┘ └─────┬─────┘ └───┬───┘│
│       │               │              │               │           │    │
│  ┌────┴───────────────┴──────────────┴───────────────┴───────────┴──┐ │
│  │ CitationRegistry + AssetManifest + SaveStore (pure data/JSON)   │ │
│  └─────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│  PyMOL Molecular Layer   (pymol.cmd.* only — headless-testable)        │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐ ┌─────────────────┐   │
│  │ AssetMgr   │ │ MolOps     │ │ Protonation  │ │ EditApplier     │   │
│  │ (cache/fech│ │ (show/hide │ │ (curated var)│ │ (lookup-driven)  │   │
│  │  /bundle)  │ │  /select)  │ │              │ │                 │   │
│  └────────────┘ └────────────┘ └──────────────┘ └─────────────────┘   │
├──────────────────────────────────────────────────────────────────────┤
│  Persistence (filesystem JSON)                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│  │ saves/   │ │ achv.json│ │ citations.js│ │ assets/ (pdb cache)  │  │
│  └──────────┘ └──────────┘ └──────────────┘ └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

**Dependency direction (inviolable):** Qt → Controller → Engine → Pure-Python Domain. PyMOL Layer is called *by* the Controller/Engine via a narrow interface, never the reverse. Domain layer imports nothing from `pymol` or `pymol.Qt`.

### Component Responsibilities

| Component | Responsibility | Lives In | Testable In WSL? |
|-----------|----------------|----------|------------------|
| **Qt UI Layer** | Render game text, choices, cast list, achievement board; route button clicks to Controller | `c14/__init__.py` + `c14/ui/` | NO (human-verify) |
| **GameEngine** | Turn loop: pull current node, present to UI, receive choice, apply effects, advance, emit `MolAction` hooks | `c14/engine.py` (pure-Py, no pymol import) | YES (mock MolAction sink) |
| **StoryGraph** | The story data: nodes (knots/stitches), choices, diverts, tags, per-node PyMOL action hooks | `data/story/*.json` (pure data) | YES (data validation) |
| **StoryInterpreter** | Walk the graph: evaluate choice conditions, resolve diverts, pick weighted (RNG) branches, expand text alternatives (sequences/cycles/shuffles) | `c14/story/interpreter.py` | YES |
| **GameState** | Mutable per-playthrough state: current node id, character, flags, counters, RNG seed, history, protonation prefs | `c14/state.py` | YES (JSON round-trip) |
| **RngEngine** | Seedable PRNG (stdlib `random.Random(seed)`) for TCA shuffles etc.; deterministic for classroom repro | `c14/rng.py` | YES |
| **EditRouter** | Map player edit-intent → known branch OR bad-ending pool, via lookup table | `c14/edit_router.py` + `data/edits.json` | YES (table lookups) |
| **CitationRegistry** | Map claim_id → source metadata (DOI, PDB ID, URL, title, year, approval_status, approved_by, approval_date); block unapproved claims | `c14/citations.py` + `data/citations.json` | YES |
| **AssetManifest** | Declare all ~20+ proteins + small molecules: PDB ID, size class (bundle/download), resolution, source, license, checksum | `c14/assets.py` + `data/assets.json` | YES |
| **SaveStore** | Serialize/restore GameState + achievement unlocks to user-writable JSON | `c14/persist.py` | YES |
| **AssetManager (PyMOL)** | Resolve asset key → local file (cache or fetch via `cmd.fetch` async_=0, or bundle); load into PyMOL object | `c14/pymol_layer/assets.py` | Headless (cmd-only) |
| **MolOps (PyMOL)** | Translate `MolAction` hooks → `cmd.show/hide/select/zoom/orient/color/delete` | `c14/pymol_layer/molops.py` | Headless (cmd-only) |
| **ProtonationManager (PyMOL)** | Apply curated protonation variant (load pre-built structure OR `cmd.alter` resn + `cmd.h_add`/`cmd.remove` hydrogens) | `c14/pymol_layer/protonation.py` | Headless (cmd-only) |
| **EditApplier (PyMOL)** | Apply known edits: load pre-built variant OR minimal `cmd.alter`/`cmd.remove`/`cmd.h_add`; keep clean backup for restore | `c14/pymol_layer/edits.py` | Headless (cmd-only) |
| **Achievement system** | Evaluate unlock conditions against GameState history; persist limited unlocks | `c14/achievements.py` | YES |

## Recommended Project Structure

```
RPG_tale-of-C/
├── c14/                              # Plugin package (the installable unit)
│   ├── __init__.py                   # __init_plugin__(app) -> addmenuitemqt('C14: Tale of C', ...)
│   ├── engine.py                     # GameEngine turn loop (pure-Py)
│   ├── state.py                      # GameState + JSON (de)serialization (pure-Py)
│   ├── rng.py                        # Seedable RngEngine (pure-Py)
│   ├── edit_router.py                # Edit-intent -> branch routing (pure-Py)
│   ├── citations.py                  # CitationRegistry + approval gate (pure-Py)
│   ├── assets.py                     # AssetManifest loader (pure-Py)
│   ├── persist.py                    # SaveStore (pure-Py)
│   ├── achievements.py               # Achievement evaluator (pure-Py)
│   ├── story/
│   │   ├── __init__.py
│   │   ├── interpreter.py            # StoryInterpreter: walk graph, eval conds, RNG branches (pure-Py)
│   │   ├── model.py                  # Dataclasses: Node, Choice, Tag, MolAction (pure-Py)
│   │   └── validate.py               # Graph validator: dangling diverts, unknown claim_ids (pure-Py)
│   ├── pymol_layer/                  # ALL pymol.cmd imports live here, nowhere else
│   │   ├── __init__.py
│   │   ├── assets.py                 # AssetManager: cache/fetch/bundle -> cmd.load
│   │   ├── molops.py                 # MolAction -> cmd.show/hide/select/zoom/orient/color/delete
│   │   ├── protonation.py            # Curated variant application
│   │   └── edits.py                  # EditApplier + restore-safety-net (backup via cmd.create)
│   ├── ui/                           # ALL pymol.Qt imports live here, nowhere else
│   │   ├── __init__.py
│   │   ├── main_window.py            # C14MainWindow(QtWidgets.QMainWindow)
│   │   ├── choice_panel.py           # ChoicePanel(QWidget)
│   │   ├── cast_dialog.py            # CastListDialog(QDialog) — PDB ID + resolution
│   │   ├── help_dialog.py            # HelpDialog(QDialog) — edit pointers, slogan
│   │   ├── achievement_board.py      # AchievementBoard(QWidget)
│   │   └── save_load.py              # Save/Load buttons + file dialogs
│   └── controller.py                 # Wires UI <-> Engine <-> PyMOL-layer (imports Qt+pymol; thin)
├── data/
│   ├── story/
│   │   ├── manifest.json             # Story bundle index (lists node files, version, default seed)
│   │   ├── intro.json                # Nodes for intro / character-select
│   │   ├── glycolysis.json           # Nodes for glycolysis path
│   │   ├── tca.json                  # Nodes for TCA (RNG-weighted shuffles)
│   │   ├── etc...                    # One file per pathway/scene (keeps diffs reviewable)
│   │   └── endings.json              # True/Good/Normal/Bad ending nodes
│   ├── edits.json                    # Edit-router lookup table
│   ├── citations.json                # CitationRegistry data (claim_id -> source + approval)
│   ├── assets.json                   # AssetManifest (PDB IDs, size class, resolution, source)
│   ├── achievements.json             # Achievement definitions + unlock conditions
│   └── assets/                       # PDB cache (gitignored except bundled-small subset)
│       ├── bundled/                  # Small/critical structures committed with plugin
│       └── downloaded/               # One-time bulk-download landing (gitignored)
├── tests/
│   ├── test_state.py                 # GameState JSON round-trip
│   ├── test_interpreter.py           # Story walking, conditions, RNG determinism
│   ├── test_edit_router.py           # Known/unknown edit routing
│   ├── test_citations.py             # Approval gate blocks unapproved
│   ├── test_rng.py                   # Seed reproducibility
│   ├── test_validate.py              # Graph validator (dangling diverts etc.)
│   └── test_assets_manifest.py       # Manifest schema + checksums
├── smoke/                            # Headless PyMOL smoke tests (run-conda-pymol.bat -cq)
│   ├── assets_smoke.py               # AssetManager fetch+load
│   ├── molops_smoke.py               # MolAction -> cmd.* round-trip
│   └── protonation_smoke.py          # Protonation variant load
├── tools/
│   ├── check_citations.py            # Pre-commit gate: every claim_id in story has approved citation
│   └── build_cast_list.py            # Generates README cast + in-game help from assets.json
├── spec.md                           # Authoritative spec (read-only)
├── README.md                         # Dramatic cast list + slogan + install instructions
└── .planning/                        # GSD planning artifacts
```

### Structure Rationale

- **`c14/` as a package (not single-file):** The 31 reference plugins in `Pymol-script-repo/plugins/` are single-file, but they max out around 1000–9000 lines for far less logic than this game. A package with `__init__.py` is the PyMOL-supported alternative (`plugins/__init__.py:findPlugins` discovers dirs with `__init__.py` — verified in source). The single `__init_plugin__` entry in `c14/__init__.py` keeps install identical to single-file plugins.
- **`pymol_layer/` and `ui/` isolation:** Every `import pymol` or `from pymol.Qt import ...` is banned outside these two folders. This is the testability boundary: `import c14.engine` in WSL must not transitively import `pymol`. Enforce with a CI grep gate (see Anti-Patterns).
- **`data/story/` split per pathway:** One JSON file per pathway/scene. Reasons: (a) per-claim citation review is line-by-line against a source — small diffable files make approval tractable; (b) parallel authoring of pathways without merge conflicts; (c) the validator can load the bundle via `manifest.json`.
- **`data/assets/bundled/` vs `downloaded/`:** Bundled small/critical PDBs are committed (e.g. a key TCA enzyme under 5 MB); large structures live in `downloaded/` after a one-time prompt. Both are addressed by the same `AssetManager` API; the manifest marks each entry's `class`.
- **`smoke/` vs `tests/`:** `tests/` are pure-Python unittests runnable with `python3.6 -m pytest` in WSL. `smoke/` are cmd-only scripts run headlessly via `run-conda-pymol.bat -cq` wrapped in `timeout`. Qt is never exercised by either — human-verify only.

## Architectural Patterns

### Pattern 1: Testability-First Layering (the WSL/Windows split made architectural)

**What:** Three import tiers with a one-way dependency rule. Domain tier (`c14/engine.py`, `c14/story/*`, `c14/state.py`, `c14/rng.py`, `c14/edit_router.py`, `c14/citations.py`, `c14/assets.py`, `c14/persist.py`, `c14/achievements.py`) imports **only** stdlib + numpy. PyMOL tier (`c14/pymol_layer/*`) imports `pymol.cmd`. UI tier (`c14/ui/*`, `c14/controller.py`) imports `pymol.Qt` + `pymol.cmd`.

**When to use:** Always — this is the project's hardest constraint. A WSL agent cannot import `pymol.Qt` (no display) and should not need `pymol.cmd` to test game logic.

**Trade-offs:** Slight verbosity (a `MolAction` data type carries intent from engine to pymol_layer instead of a direct `cmd.show(...)` call). Worth it: ~70% of the codebase (story logic, RNG, edits, citations, save/load, achievements) becomes unit-testable in WSL with zero mocking of PyMOL.

**Example:**
```python
# c14/story/model.py  — pure-Python, no pymol import
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class MolAction:
    """A molecular-layer intent emitted by the story interpreter.
    The PyMOL layer translates this to cmd.* calls. Pure data -> unit-testable."""
    op: str                          # "load" | "hide_all" | "show" | "select_focus" | "zoom" | "color" | "delete" | "protonate" | "edit" | "restore"
    target: Optional[str] = None     # asset key e.g. "pdb:1TNR" or object name
    args: dict = field(default_factory=dict)

@dataclass
class Choice:
    label: str
    goto: Optional[str] = None       # divert target "knot.stitch"
    cond: Optional[str] = None       # expression on GameState, e.g. "not seen_tca and char=='glucose'"
    weight: Optional[float] = None   # if set, this is an RNG-weighted branch
    effects: dict = field(default_factory=dict)   # {"set": {...}, "incr": {...}}
    tags: List[str] = field(default_factory=list)

@dataclass
class Node:
    id: str                          # "knot.stitch" address
    text_dramatic: str = ""
    text_teaching: str = ""
    claim_ids: List[str] = field(default_factory=list)   # citations for this node's science
    choices: List[Choice] = field(default_factory=list)
    on_enter: List[MolAction] = field(default_factory=list)  # PyMOL hooks fired on entry
    is_ending: Optional[str] = None   # "true"|"good"|"normal"|"bad"
    tags: List[str] = field(default_factory=list)
```

```python
# c14/pymol_layer/molops.py  — the ONLY place that calls cmd.show/hide/etc.
from pymol import cmd
from c14.story.model import MolAction

def apply(action: MolAction) -> None:
    if action.op == "hide_all":
        cmd.hide("everything")
    elif action.op == "show":
        cmd.show(action.args.get("rep", "cartoon"), action.args.get("sele", "all"))
    elif action.op == "load":
        # delegates to AssetManager for cache/fetch/bundle resolution
        ...
```

### Pattern 2: Ink-Inspired Story Graph (nodes + diverts + choices + tags + seeded RNG)

**What:** Model the branching narrative on [Inkle's **ink** language data model](https://github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md) — the field's reference design for branching narrative — but store it as JSON owned by us and interpreted by a small pure-Python walker. We do **not** depend on the ink runtime (C#) or `inkpy` (external Python dep requiring user approval per `spec.md`). We borrow the *model*, not the *engine*.

**When to use:** Always for this project. Ink's primitives map 1:1 onto our requirements:

| Ink concept | Our JSON equivalent | Why it fits C14 |
|-------------|---------------------|-----------------|
| **Knot** (`=== knot ===`) | `nodes["knot.stitch"]` key | Named scene/step in a pathway |
| **Stitch** (`= stitch`) | dotted address `knot.stitch` | Sub-step within a pathway (e.g. `tca.step3`) |
| **Divert** (`-> target`) | `choice.goto` / `node.on_enter_divert` | Advance C14 to next step |
| **Choice** (`*` once-only / `+` sticky) | `Choice` with `cond` | Multiple-choice gameplay |
| **Gather** (`-`) | a node that several `goto`s target | Branching-and-joining (rejoin after a choice) — matches pathway topology |
| **Condition** (`{flag}`) | `choice.cond` expression | Gate choices on prior state (e.g. only show "anaerobic" if host O2 low) |
| **Alternatives: sequence/cycle/shuffle** (`{\|}`/`&`/`~`) | `node.text_variants` + RNG pick | **TCA cycle shuffles** — exactly the spec's RNG requirement |
| **Tags** (`#tag`) | `node.tags` / `choice.tags` | Game-side hooks: `stage:tca`, `pymol:load:pdb:1TNR`, `rng:shuffle` |
| **`SEED_RANDOM(235)`** | `RngEngine(seed)` per playthrough | **Classroom reproducibility** — the spec's seedable-RNG requirement |
| **Read counts** on knots | `state.visit_counts[node_id]` | "seen this scene N times" conditions + cycle-trap detection (bad ending) |
| **Variables / logic** | `GameState.flags` + `cond` evaluator | Track character, host condition, edits made |

**Trade-offs:** We write ~200 lines of interpreter (conditions, divert resolution, weighted pick, variant expansion). Cheaper than vetting+approving+porting an external runtime, and keeps the dep surface at stdlib-only. The cost is we don't get ink's authoring syntax — authors write JSON. Mitigation: a tiny validator (`c14/story/validate.py`) + the per-file pathway split keeps JSON authorable.

**Example (TCA shuffle node, JSON):**
```json
{
  "id": "tca.shuffle",
  "text_dramatic": "The great wheel spins. Where will our hero be flung?",
  "text_teaching": "TCA cycle intermediates are rearranged by aconitase/isocitrate dehydrogenase; the C14 atom is redistributed among the four carboxyls of oxaloacetate with known probabilities.",
  "claim_ids": ["tca.redistribution"],
  "tags": ["stage:tca", "rng:shuffle"],
  "on_enter": [
    {"op": "hide_all"},
    {"op": "load", "target": "pdb:1TNR", "args": {"object": "1TNR"}},
    {"op": "show", "args": {"rep": "cartoon"}},
    {"op": "show", "args": {"rep": "sticks", "sele": "active_site"}}
  ],
  "choices": [
    {"label": "Continue (luck decides)", "weight": 1.0, "goto": "tca.resolve", "tags": ["rng:weighted"]},
    {"label": "Try to edit the enzyme", "goto": "edit.prompt", "tags": ["edit:offer"]}
  ]
}
```
```python
# c14/story/interpreter.py — pure-Python, no pymol
import random
from c14.story.model import Node, Choice, MolAction

class StoryInterpreter:
    def pick_choice(self, node: Node, state, rng: random.Random) -> Choice:
        eligible = [c for c in node.choices if self._cond(c.cond, state)]
        weighted = [c for c in eligible if c.weight is not None]
        if weighted:
            # RNG-weighted branch (TCA shuffle). Deterministic given seed.
            total = sum(c.weight for c in weighted)
            r = rng.random() * total
            upto = 0.0
            for c in weighted:
                upto += c.weight
                if r <= upto:
                    return c
        # non-weighted: present all eligible to player (UI picks)
        return eligible  # caller (UI) presents, player selects
```

### Pattern 3: Edit Routing via Lookup Table + Bad-Ending Fallback

**What:** Player edits are recorded as a structured `EditIntent` (op, target, params). The `EditRouter` consults `data/edits.json`: if the intent matches a known entry (keyed by enzyme context + op signature), it routes to the corresponding story branch *and* the PyMOL `EditApplier` applies the edit (load pre-built variant, or minimal `cmd.alter`/`cmd.remove`/`cmd.h_add`). If no match, it routes to the bad-ending pool (`"lost connection"` / `"released from host"`) — no chemistry-correctness engine needed.

**When to use:** Always. This is the user-confirmed simplification (PROJECT.md Key Decisions). It removes the hardest validation problem (is this edit chemically valid?) and replaces it with a curated table.

**Trade-offs:** The table must be hand-curated for each "editable" enzyme context. That's acceptable because edits are *limited* (the spec says "limited edits") and the set of enzymes is fixed (~20+). The "reveal correct 3D model / restore" safety net is just `EditApplier.restore()`, which reloads the clean structure from the AssetManager (kept as a `cmd.create` backup named `_c14_backup_<key>` on load).

**Example:**
```json
// data/edits.json
{
  "edits": [
    {
      "context": "tca.aconitase",
      "match": {"op": "point_mutation", "resi": "His101", "to": "Ala"},
      "route": "edit.aconitase_h101a_branch",
      "apply": {"op": "load_variant", "target": "pdb:1TNR_H101A"}
    }
  ],
  "fallback_pool": ["bad.lost_connection", "bad.released_from_host", "bad.host_death"]
}
```
```python
# c14/pymol_layer/edits.py — runs in PyMOL (headless-testable)
from pymol import cmd

class EditApplier:
    def backup(self, key: str, object_name: str) -> None:
        cmd.create(f"_c14_backup_{key}", object_name)  # NOTE: default args = all states (see Pitfalls)

    def restore(self, key: str, object_name: str) -> None:
        cmd.delete(object_name)
        cmd.create(object_name, f"_c14_backup_{key}")
```

### Pattern 4: Citation Registry + Per-Claim Approval Gate (the no-fabricated-science rule, architected)

**What:** Every scientific claim in the story (a node's `text_teaching`, a pathway fact, a PDB ID, a protonation rule) carries one or more `claim_ids`. The `CitationRegistry` (`data/citations.json`) maps each `claim_id` to full source metadata and an `approval_status` ∈ `{pending, approved, rejected}` with `approved_by` + `approval_date`. A validator (`tools/check_citations.py`, run pre-ship and as a CI gate) refuses to build/ship if any referenced `claim_id` is missing or not `approved`.

**When to use:** Always — this is `spec.md`'s strongest constraint ("ALL claims and citations MUST BE VERIFIED and explicitly approved by human"). The architecture must make fabrication impossible-by-construction, not a matter of discipline.

**Trade-offs:** Slower content authoring (every claim needs an approval checkpoint). The user explicitly chose the slowest/safest of three options (PROJECT.md). The gate is the payoff: a CI red on `pending` means no merge.

**Example:**
```json
// data/citations.json
{
  "tca.redistribution": {
    "claim": "C14 redistributes among oxaloacetate carboxyls in TCA",
    "source_type": "textbook",
    "source": "Biochemistry LibreTexts",
    "url": "https://bio.libretexts.org/...",
    "approval_status": "approved",
    "approved_by": "human-name",
    "approval_date": "2026-08-12",
    "notes": "Approved during pathway-research checkpoint"
  },
  "pdb.1TNR": {
    "claim": "PDB 1TNR is a suitable cast member for TCA aconitase",
    "source_type": "pdb",
    "pdb_id": "1TNR",
    "resolution_angstrom": 2.05,
    "url": "https://www.rcsb.org/structure/1TNR",
    "approval_status": "pending"
  }
}
```
```python
# tools/check_citations.py — pre-ship gate (pure-Python, runs in WSL CI)
import json, sys
from c14.citations import CitationRegistry
from c14.story.validate import collect_claim_ids

reg = CitationRegistry.load("data/citations.json")
story_ids = collect_claim_ids("data/story/")          # all claim_ids referenced by nodes
missing = [cid for cid in story_ids if cid not in reg]
unapproved = [cid for cid in story_ids if not reg.is_approved(cid)]
if missing or unapproved:
    print(f"BLOCKED: {len(missing)} missing, {len(unapproved)} unapproved citations")
    sys.exit(1)
```

### Pattern 5: Hybrid Asset Management (bundle small, bulk-download large)

**What:** `data/assets.json` declares every protein/small-molecule with a `class` ∈ `{bundled, download}`. `AssetManager.resolve(key)` checks the local cache (`data/assets/bundled/` for committed, `data/assets/downloaded/` for fetched); on miss, it either reads the bundled file or, for `download` class, calls `cmd.fetch(code, type='pdb'|'cif', async_=0, path=...)` (sync, `async_=0` is critical for headless — verified in `importing.py:1323`). On first play, if any `download`-class assets are missing, the UI shows a one-time bulk-download prompt (sums the manifest's `size_mb` fields).

**When to use:** For all ~20+ PDB structures + PubChem small molecules. Matches `spec.md` ("may need to prompt a data download step before the first time the user play a game").

**Trade-offs:** Bundled assets bloat the repo; downloading hits the network on first play. The hybrid split balances install size vs first-run latency. Concretely: bundle anything under ~3 MB that's critical to the opening scene (so the game starts instantly); bulk-download the rest on a one-time prompt.

**PyMOL API notes (verified against `tmp/pymol-src/modules/pymol/importing.py:1323`):**
- `cmd.fetch(code, name, type, async_=0, path=...)` — `async_=0` forces sync (blocks until loaded). Essential for headless correctness; default in 2.5.0 is async-when-interactive.
- `cmd.fetch` accepts a list of codes for bulk download.
- `type` ∈ `{cif (default), pdb, pdb1, 2fofc, fofc, emd, cid, sid}` — use `pdb`/`cif` for proteins, `cid` for PubChem small molecules.

### Pattern 6: Save/Load as Game-State JSON (not a PyMOL session)

**What:** `SaveStore` serializes `GameState` (current node id, character, flags, counters, RNG seed, visit counts, edits-made history, protonation prefs, achievement unlocks) to a user-writable JSON file. On load, the engine reconstructs the PyMOL scene by replaying the current node's `on_enter` `MolAction`s against the AssetManager — it does NOT save a `.pse` PyMOL session. The molecular scene is a pure function of the game state.

**When to use:** Always. A `.pse` session is opaque, large, and not diff/review-friendly. Game-state JSON is small, inspectable, and lets a saved game survive PyMOL version changes.

**Trade-offs:** Loading a save re-fetches/re-loads structures (a few seconds) rather than instant `.pse` restore. Acceptable: keeps saves portable and small (KB not MB), and the bundled/cache path makes re-load fast.

## Data Flow

### Playthrough Walkthrough (one full turn, end to end)

```
1. USER clicks choice "Continue" in ChoicePanel (Qt)
   ↓ (Qt signal)
2. controller.on_choice_clicked(index)
   ↓
3. engine.choose(index)
   ↓
4. story_interpreter.resolve_choice(current_node, state, rng, index)
   ├─ evaluate cond on Choice (GameState flags)
   ├─ if Choice.weight is set: RNG pick (deterministic via RngEngine(seed))
   ├─ apply Choice.effects -> GameState (set flags, incr counters, record edit)
   └─ return goto node_id ("tca.shuffle")
   ↓
5. engine.advance("tca.shuffle")
   ↓
6. story_interpreter.enter_node("tca.shuffle", state)
   ├─ run node.on_enter MolActions (pure data list) -> queued for PyMOL layer
   ├─ expand text variants (sequence/cycle/shuffle via RngEngine)
   ├─ record visit_count[node_id] += 1  (for conditions + cycle-trap detection)
   └─ if node.is_ending: mark GameState.finished + unlock achievement
   ↓
7. controller.dispatches MolAction queue to pymol_layer.molops.apply(action)
   ├─ AssetManager.resolve("pdb:1TNR") -> cached file or cmd.fetch(async_=0)
   ├─ cmd.load(path, "1TNR")
   ├─ EditApplier.backup("1TNR", "1TNR")  # safety net for later restore
   ├─ cmd.hide("everything")
   ├─ cmd.show("cartoon")
   ├─ cmd.show("sticks", "active_site")   # active_site is a named selection
   └─ cmd.zoom("1TNR")
   ↓
8. controller presents new node to UI:
   ├─ main_window.set_text(node.text_dramatic, node.text_teaching)
   ├─ choice_panel.set_choices(eligible_choices)  # UI picks for non-weighted
   └─ cast_dialog may update current cast member
   ↓
9. UI renders; awaits next user click → back to step 1
```

**Data-flow invariants:**
- **Domain → PyMOL:** only via `MolAction` data (never `cmd.*` calls in domain layer).
- **PyMOL → Domain:** only via return values / exceptions to the controller (the PyMOL layer never mutates `GameState` directly).
- **UI → Domain:** only via `engine.choose(index)` / `engine.start(character, seed)` / `engine.save()` / `engine.load(path)`.
- **RNG:** only the `RngEngine` instance (seeded at `engine.start`) is used for *all* stochastic choice — never `random.random()` ad-hoc. This is the reproducibility guarantee.

### Edit-Flow Walkthrough (player edits a residue)

```
1. USER opens edit panel, picks residue His101, chooses "mutate to Ala"
   ↓
2. controller.on_edit_submitted(EditIntent(op="point_mutation", resi="His101", to="Ala"))
   ↓
3. edit_router.route(context="tca.aconitase", intent)
   ├─ look up data/edits.json
   ├─ MATCH FOUND -> route = "edit.aconitase_h101a_branch", apply = {load_variant: pdb:1TNR_H101A}
   └─ NO MATCH -> route = random pick from fallback_pool (bad.lost_connection / bad.released_from_host)
   ↓
4. engine.advance(route)
   ├─ if apply spec present: controller dispatches EditApplier.apply_variant -> cmd.load(variant)
   └─ story_interpreter.enter_node(route) — branch may be a bad ending
   ↓
5. (safety net) USER clicks "Reveal correct model / Restore"
   ↓
6. controller.on_restore() -> EditApplier.restore("1TNR", "1TNR") -> cmd.delete + cmd.create from backup
```

## Data Model

### Story Graph (the central data structure)

A **dict-of-dicts** of `Node` objects, keyed by dotted `knot.stitch` address. Stored as one JSON file per pathway (`data/story/<pathway>.json`), indexed by `manifest.json`. Each file is a fragment of the global `nodes` dict; the interpreter merges them at load. Rationale: per-file diffability for per-claim citation review; parallel pathway authoring.

```json
// data/story/manifest.json
{
  "version": 1,
  "default_seed": 0,
  "files": ["intro.json", "glycolysis.json", "pdh.json", "tca.json", "etc.json", "etc.json_oxphos.json", "fatty_acid.json", "alcohol.json", "anaerobic.json", "endings.json", "edits_branch.json", "bad_endings.json"]
}
```
```json
// data/story/tca.json (fragment — the global nodes dict is the merge of all files)
{
  "nodes": {
    "tca.entry": { "id": "tca.entry", "text_dramatic": "...", "text_teaching": "...", "claim_ids": ["tca.intro"], "on_enter": [{"op":"hide_all"}, {"op":"load","target":"pdb:1TNR"}], "choices": [{"label":"Enter the cycle","goto":"tca.shuffle"}]},
    "tca.shuffle": { "...": "(see Pattern 2 example)" },
    "tca.resolve": { "id": "tca.resolve", "choices": [{"label":"...","goto":"tca.exit"}] }
  }
}
```

### GameState (the saveable unit)

```json
{
  "version": 1,
  "seed": 235,
  "character": "glucose",
  "current_node": "tca.resolve",
  "flags": {"seen_tca": true, "host_o2_low": false, "broken_enzyme": false},
  "counters": {"turns": 12, "edits_made": 1},
  "visit_counts": {"tca.entry": 1, "tca.shuffle": 3, "tca.resolve": 1},
  "edits_history": [{"context": "tca.aconitase", "intent": {"op":"point_mutation","resi":"His101","to":"Ala"}, "route":"edit.aconitase_h101a_branch"}],
  "protonation_pref": "physiological",
  "started_at": "2026-08-12T06:00:00Z",
  "finished": null,
  "ending_tier": null
}
```
Serialized by `c14/persist.py` via stdlib `json` to `~/.c14_saves/<name>.json` (or user-chosen path).

### AssetManifest

```json
{
  "assets": {
    "pdb:1TNR": {"class": "bundled", "pdb_id": "1TNR", "resolution": 2.05, "size_mb": 0.8, "role": "aconitase (TCA cast)", "claim_id": "pdb.1TNR", "license": "PDB"},
    "pdb:1BG5": {"class": "download", "pdb_id": "1BG5", "resolution": 2.5, "size_mb": 12, "role": "PDH (large)", "claim_id": "pdb.1BG5", "license": "PDB"},
    "pubchem:5793": {"class": "download", "pubchem_cid": 5793, "role": "glucose substrate", "claim_id": "pubchem.5793", "license": "PubChem"}
  },
  "bulk_download_size_mb": 47,
  "checksums": {"pdb:1TNR": "sha256:..."}
}
```

### CitationRegistry

See Pattern 4 example. One entry per `claim_id`. `is_approved(cid)` is the gate.

### EditRouter table

See Pattern 3 example. Keyed by `context` (the enzyme/substrate node the player is at) + intent signature.

## Build Order (dependencies between components)

The dependency graph dictates what must exist before X can be built. This is the input to roadmap phase ordering.

```
PHASE-0 (no deps):
  c14/rng.py                      # stdlib only
  c14/state.py                    # stdlib + numpy only
  c14/story/model.py              # dataclasses, stdlib only
  data/citations.json (schema)
  data/assets.json (schema)
  tools/check_citations.py        # depends on schemas only

PHASE-1 (needs PHASE-0):
  c14/citations.py                # loads citations.json
  c14/assets.py                   # loads assets.json
  c14/story/validate.py           # needs model.py
  c14/story/interpreter.py        # needs model.py, rng.py, state.py
  tests/test_rng.py, test_state.py, test_validate.py

PHASE-2 (needs PHASE-1):
  c14/edit_router.py               # needs state.py
  c14/achievements.py              # needs state.py
  c14/persist.py                   # needs state.py
  c14/engine.py                    # needs interpreter, state, rng, edit_router, citations
  data/story/{intro,manifest}.json (minimal 2-node story to drive engine)
  tests/test_interpreter.py, test_edit_router.py, test_citations.py

PHASE-3 (needs PHASE-2; introduces pymol.cmd):
  c14/pymol_layer/assets.py        # needs assets.py; uses cmd.fetch/load
  c14/pymol_layer/molops.py        # needs story/model.py; uses cmd.show/hide/...
  smoke/assets_smoke.py, smoke/molops_smoke.py   # headless via run-conda-pymol.bat -cq

PHASE-4 (needs PHASE-3):
  c14/pymol_layer/protonation.py  # needs assets.py; uses cmd.alter/h_add/remove
  c14/pymol_layer/edits.py        # needs assets.py, edit_router; uses cmd.create/delete
  smoke/protonation_smoke.py
  data/assets.json (real entries; PDB IDs subject to per-claim approval)

PHASE-5 (needs PHASE-2..4; introduces pymol.Qt — human-verify only):
  c14/controller.py               # wires engine <-> ui <-> pymol_layer
  c14/ui/{main_window,choice_panel,cast_dialog,help_dialog,achievement_board,save_load}.py
  c14/__init__.py (__init_plugin__ + addmenuitemqt)
  data/story/*.json (full content; per-claim approval checkpoints)
  README.md (cast list + slogan; generated from assets.json)
  tools/build_cast_list.py
```

**Build-order rationale (roadmap implications):**
- **PHASE-0 + PHASE-1 are pure-Python and fully unit-testable in WSL** — they should be the first execution phases. They deliver the testability boundary *and* the citation gate early, so no later phase can ship unapproved science.
- **PHASE-2 (engine) is the proof point** — a minimal 2-node story (intro → one choice → ending) playable end-to-end in WSL with mocked MolActions. This de-risks the whole architecture before any PyMOL/Qt code is written.
- **PHASE-3 + PHASE-4 are headless-PyMOL** — testable via `run-conda-pymol.bat -cq`. They prove the molecular layer against the real API surface (and surface the `cmd.create` no-op pitfall early).
- **PHASE-5 (Qt) is last and human-verify-only** — the riskiest layer to build, but by then the engine and molecular layer are solid and the UI is a thin adapter.
- **Citation approval is on the critical path of content**: `data/story/*.json` cannot land until each `claim_id` passes the gate. This is the slowest stream and should start in parallel with PHASE-0 (the user approving sources while the agent builds plumbing).

## Scaling Considerations

This is a desktop educational plugin, not a web service. "Scaling" here means **content scaling** (more pathways, more PDBs) and **runtime scaling** (load time, memory with 20+ structures loaded).

| Concern | At ~5 structures | At ~20+ structures | At ~50+ structures (v2) |
|---------|------------------|--------------------|--------------------------|
| First-play download | bundle all | bulk-download prompt (spec) | background fetch + progress UI |
| Memory (all loaded) | trivial | load only the current scene's structures; `cmd.delete` on node exit | strict one-scene-at-a-time + LRU cache |
| Asset cache hit | always (bundled) | cache after first fetch | checksum-verified cache; periodic re-fetch on staleness |
| Story graph size | one file | one file per pathway (this design) | sharded by pathway + lazy-load fragments |
| Save file size | <5 KB | <20 KB | unchanged (game state only, not molecules) |

### Scaling Priorities

1. **First bottleneck: first-play network download of large PDBs.** Mitigation: the one-time bulk-download prompt (Pattern 5) with a size estimate from the manifest. Bundling the opening scene's small structures avoids a black screen on first launch.
2. **Second bottleneck: memory if many structures loaded simultaneously.** Mitigation: `MolAction` discipline — every scene's `on_enter` ends with the previous scene's structures deleted (`cmd.delete`); only the current cast member is loaded. The AssetManager cache (files on disk) makes re-load cheap.

## Anti-Patterns

### Anti-Pattern 1: Importing `pymol` or `pymol.Qt` from the domain layer

**What people do:** Call `cmd.show(...)` directly inside `engine.py` or a story node's handler "because it's convenient".
**Why it's wrong:** Breaks the testability boundary — `import c14.engine` in WSL now requires PyMOL, so `python3.6 -m pytest` fails. Qt imports additionally require a display. This collapses ~70% of the testable surface into human-verify-only.
**Do this instead:** Emit `MolAction` data from the domain layer; translate to `cmd.*` only in `c14/pymol_layer/`. Enforce with a CI grep: `grep -rn "import pymol\|from pymol" c14/ --exclude-dir=pymol_layer --exclude-dir=ui` must return nothing.

### Anti-Pattern 2: `cmd.create(obj, sele, 1, 1)` for a backup copy

**What people do:** Use `cmd.create(backup, sele, 1, 1)` to snapshot a structure before an edit, borrowing a common snippet.
**Why it's wrong:** In PyMOL 2.5.0 `cmd.create`'s `source_state`/`target_state` are 1-indexed-then-converted-to-0-indexed; `create(obj, sele, 1, 1)` is a **no-op** for state copying (the AGENTS.md Phase-5 spike documented this; verified against `creating.py:960`). The backup silently fails; `restore()` then deletes the only copy.
**Do this instead:** `cmd.create(backup_name, selection)` with default args (copies all states). Verify the backup atom count with `cmd.count_atoms` before mutating.

### Anti-Pattern 3: Assuming `cmd.h_add` gives physiological-pH protonation

**What people do:** Call `cmd.h_add(sele)` and assume the result is pH-7-correct.
**Why it's wrong:** `h_add` adds hydrogens based on **valence only**, not pH (verified — there is no pH setting in PyMOL 2.5.0; `editing.py:1216` docstring confirms "based on current valences"). Histidine tautomer, ASP/GLU protonation state, termini charges — all wrong-by-default for a biochemistry game.
**Do this instead:** Treat protonation as a **curated content concern**. Maintain named variants (`ASP`/`ASPH`, `HID`/`HIE`/`HIP`, `LYS`/`LYSN`) in the AssetManifest (pre-built structures) or apply via `cmd.alter` resn + targeted `cmd.h_add`/`cmd.remove` on specific atoms per a curated rule table (`c14/pymol_layer/protonation.py`). The user-adjustable pref is a switch between curated variants, not a magic pH dial.

### Anti-Pattern 4: Using the mutagenesis wizard for programmatic point mutations

**What people do:** Instantiate `pymol.wizard.mutagenesis.Mutagenesis` to mutate a residue programmatically.
**Why it's wrong:** The wizard is interactive/GUI-driven and depends on `$PYMOL_DATA/chempy/sidechains/sc_bb_ind.pkl` (verified in `wizard/mutagenesis.py:58`). It's not designed for headless scripted use and will surface display/state assumptions.
**Do this instead:** For "limited edits" with the lookup-table model (Pattern 3), prefer **pre-built variant PDBs** loaded by the EditApplier when an edit matches a known branch. For cosmetic-only mutations (e.g. showing the player "your edit" visually), `cmd.alter sele, resn='ALA'` + `cmd.sort()` is far simpler and headless-safe. Real chemistry-correct mutations are out of scope (the lookup table routes known edits to pre-built variants; unknown edits go to the bad-ending pool).

### Anti-Pattern 5: Saving game state as a `.pse` PyMOL session

**What people do:** `cmd.save("savegame.pse")` and call it a save file.
**Why it's wrong:** `.pse` is an opaque binary session (verified format list in `exporting.py:782`). It's large, not diff-reviewable, breaks across PyMOL versions, and couples the save to the exact loaded-state rather than the game state. Restoring an old save after a content update may resurrect stale structures.
**Do this instead:** Save `GameState` as JSON (Pattern 6). Reconstruct the molecular scene by replaying the current node's `on_enter` MolActions on load.

### Anti-Pattern 6: Single-file plugin for a project this size

**What people do:** Follow the 31 reference plugins in `Pymol-script-repo/plugins/` literally and put everything in one `c14.py`.
**Why it's wrong:** Those plugins are 1–9k lines for far less logic. A game with a story graph, RNG, edits, citations, assets, achievements, save/load, and a multi-tab UI will be 5–10× that. A single file breaks the testability boundary (you can't `import` the engine without importing Qt) and makes the citation review of story content (which lives in code) impossible.
**Do this instead:** A `c14/` package with `__init__.py` (PyMOL discovers package plugins — verified in `plugins/__init__.py:findPlugins` which checks for `__init__.py` in directories). Keep `__init_plugin__` in `c14/__init__.py` so install is identical to single-file.

### Anti-Pattern 7: Ad-hoc `random.random()` for stochastic steps

**What people do:** Scatter `random.random()` calls in story-branch decisions.
**Why it's wrong:** Breaks classroom reproducibility (the spec's seedable-RNG requirement). Two students with the same "luck" see different outcomes.
**Do this instead:** One `RngEngine` instance per playthrough, seeded at `engine.start(seed)`. All stochastic picks (weighted choices, text-variant shuffles, TCA redistribution) draw from this single instance. The seed is part of `GameState` and saved with the game.

## Integration Points

### External Services

| Service | Integration Pattern | Notes / Gotchas |
|---------|---------------------|-----------------|
| **RCSB PDB** (`rcsb.org`) | `cmd.fetch(code, type='pdb'\|'cif', async_=0, path=...)` | Use `async_=0` for headless correctness (default is async-when-interactive — `importing.py:1323`). Bulk-download on first play via a list of codes. Network firewall may block — surface a clear error. |
| **PubChem** | `cmd.fetch(str(cid), type='cid', ...)` | `type='cid'` for PubChem small molecules (`importing.py:1323` type list). CIDs must be strings. |
| **Filesystem (saves)** | stdlib `json` to user-writable dir | `~/.c14_saves/` default; user-chosen path via QFileDialog. Never write inside the plugin install dir (may be read-only). |
| **Filesystem (PDB cache)** | `data/assets/{bundled,downloaded}/` | Bundled committed to git; downloaded gitignored. AssetManager is the only writer to `downloaded/`. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| UI ↔ Controller | Qt signals/slots + direct method calls | Controller owns the `GameEngine` instance; UI is stateless view over `GameState` snapshots. |
| Controller ↔ Engine | direct method calls (`engine.choose(idx)`, `engine.start(...)`) | Engine returns `TurnResult` (text, choices, molactions); Controller dispatches molactions to pymol_layer. |
| Engine ↔ StoryInterpreter | direct calls | Engine delegates graph walking to interpreter; holds `GameState` and `RngEngine`. |
| Engine ↔ PyMOL layer | `MolAction` data list (out); return values/exceptions (in) | Engine never imports `pymol`; the controller does the handoff so the engine stays pure-Python. |
| Engine ↔ Persistence | `GameState` (de)serialization | `SaveStore.to_json(state)` / `from_json(dict)`. |
| All ↔ Citations | `claim_id` strings + `CitationRegistry.is_approved(cid)` | The validator (`tools/check_citations.py`) is the hard gate; runtime also asserts on load in dev mode. |

## Sources

- **PyMOL 2.5.0 source (HIGHEST confidence, version-exact)** — `tmp/pymol-src/modules/pymol/`:
  - `plugins/__init__.py:100,130,149,248,320,365,407` — plugin discovery, `addmenuitemqt`, `findPlugins` (package plugins via `__init__.py`), `PluginInfo.load`/`legacyinit` (calls `__init_plugin__`).
  - `importing.py:635` (`load` signature), `:1323` (`fetch` signature — `async_=0` for sync, `type` list incl. `cid`/`pdb`/`cif`).
  - `viewing.py:491` (`show`), `:528` (`show_as`), `:568` (`hide`), `:65` (`zoom`), `:281` (`orient`).
  - `editing.py:1424` (`alter` — symbols: name/resn/resi/chain/segi/elem/formal_charge/partial_charge/...), `:1490` (`iterate` + new lambda form `:1514`), `:1216` (`h_add` — **valence-only, not pH**), `:1257` (`sort` — required after `alter` on names/order), `:800` (`remove`), `:937` (`fuse`), `:1288` (`replace`).
  - `creating.py:929` (`fragment` — **amino-acid library only**, docstring "currently pretty meager"), `:960` (`create` — **`create(obj,sele,1,1)` is a no-op**; use default args for full copy).
  - `commanding.py:496` (`delete`).
  - `exporting.py:782` (`save` — format list incl. `pdb`/`mol2`/`sdf`/`pse`/`pkl`/`pkla`).
  - `querying.py:131` (`get_object_list`), `:1148` (`get_names`).
  - `wizard/mutagenesis.py:38,58` — interactive mutagenesis; depends on `$PYMOL_DATA/chempy/sidechains/sc_bb_ind.pkl`; not headless-friendly. `_rot_type_xref` lists protonation-variant resnames (`HID`/`HIE`/`HIP`/`ASPH`/`GLUH`/`ARGN`/`LYSN`).
- **Reference plugins (Pymol-script-repo/plugins/, MEDIUM-HIGH for conventions)**:
  - `dynoplot.py:21,445` — modern `from pymol.Qt import QtCore, QtGui, QtWidgets`; `__init_plugin__` + `addmenuitemqt` pattern; `cmd.extend` for commands.
  - `outline.py:29,311` — modern `QtWidgets.QDialog` plugin with `QComboBox`/`QPushButton`/`QSlider`; `__init_plugin__(app=None)` signature; global `dialog` ref to avoid GC.
  - `optimize.py:29,53,73` — `QtWidgets.QDialog` + `QtWidgets.QTabWidget` for multi-tab UI.
  - `show_contacts.py:280,321,331` — `QtWidgets.QDialog` + `QDialogButtonBox`; `addmenuitemqt`.
  - `rendering_plugin.py` — legacy Tk/Pmw (anti-reference; confirms we must use the `pymol.Qt` form, not this).
- **Inkle/ink narrative model (HIGH for story-graph design; the field's reference)**:
  - `github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md` — knots/stitches/diverts/choices/gathers/conditions/alternatives(sequence/cycle/shuffle)/tags/`SEED_RANDOM`/read-counts/variables. We borrow the **data model**, not the runtime (no external dep).
- **Project context (HIGHEST for constraints)**:
  - `spec.md` — plot, RNG, endings, edit model, citation rule, protonation rule, hybrid asset acquisition, no-install rule.
  - `.planning/PROJECT.md` — confirmed scope, key decisions (edit routing = lookup table + bad-ending fallback; stat/XP deferred; per-claim approval checkpoint).
  - `AGENTS.md` — WSL/Windows split, `run-conda-pymol.bat -cq` headless pattern, `cmd.create(obj,seg,1,1)` no-op pitfall, verification tiers.

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| PyMOL plugin entry/discovery | HIGH | Verified against `plugins/__init__.py` 2.5.0 source + 5 reference plugins |
| PyMOL cmd API surface (load/fetch/show/hide/alter/iterate/create/save) | HIGH | Signatures read from 2.5.0 source; key pitfall (`create` no-op) confirmed by prior spike + source |
| Protonation limitation (valence-only, no pH) | HIGH | Source + docstring; no pH setting found in keywords/settings |
| Story-graph data model (ink-inspired) | HIGH | Official ink docs; well-established design; we own the interpreter so no version risk |
| Pure-Python/PyMOL/Qt testability split | HIGH | Direct consequence of AGENTS.md environment constraints; verified import tiers are achievable |
| Edit-routing + bad-ending fallback | MEDIUM | Design-driven (user-confirmed in PROJECT.md); API surface for EditApplier verified, but the exact set of "known edits" is content (needs per-claim approval) |
| Asset management (bundle/download) | HIGH for mechanism (fetch/load API verified); MEDIUM for the exact bundle-vs-download split (content decision per PDB, pending approval) |
| Citation gate architecture | HIGH | Direct implementation of spec.md's strongest constraint; pure-Python, no external dependency |
| Mutagenesis wizard unsuitability | HIGH | Source confirms interactive + data-file dependency |

## Gaps to Address (phase-specific research later)

- **Exact PDB ID list for the cast** (~20+): needs pathway-by-pathway research + per-claim approval. The architecture is ready; the content is not. Flag the first content phase for deep research.
- **Bundled vs download split per PDB**: needs the PDB list + size measurements. AssetManifest schema is ready; populate during the first asset phase.
- **Anaerobic path framing** (host-condition branch / separate scenario / bad-ending trigger): PROJECT.md marks this Pending. Architecture supports all three as story-graph branches; the choice is content, not architecture.
- **Edit-router table contents**: the lookup table is architecture-ready; curating which edits are "known" per enzyme is a content/research task per enzyme.
- **Protonation variant set**: which residues need named variants per structure is a per-structure content decision.
- **Stat/XP model** (deferred to v2): if "luck that affects host condition" is validated scientifically, the architecture accommodates it as additional `GameState.flags` + `cond` expressions — no structural change needed.

---
*Architecture research for: PyMOL-plugin branching-narrative RPG (C14: Tale of C)*
*Researched: 2026-08-12*
