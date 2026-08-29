# Phase 6: Qt UI Minimal Playable MVP — Research (UI-as-Adapter Architecture track)

**Researched:** 2026-08-29
**Domain:** PyQt5 (via `pymol.Qt`) thin-adapter UI over the proven pure-Python `GameEngine` + `pymol.cmd` molecular layer; the 4 deferred molops dispatches; the OQ-6 warn+confirm Qt prompt.
**Confidence:** HIGH (the engine/molops/model contracts are READ IN FULL + verified against source; the 4 cmd.* dispatch signatures verified at exact `tmp/pymol-src` lines; the deferred-dispatch pseudocode is FROZEN verbatim in the 5.3/5.4 conventions; the plugin entry-point pattern verified against a bundled PyMOL 2.5.0 startup plugin).
**Scope:** ONE of three parallel Phase-6 research tracks. THIS track covers the controller/mediator architecture, the 4 deferred dispatches, the OQ-6 prompt separation, the testability split, and the main-window layout. It does NOT cover plugin packaging/install (separate track) or persistence/achievements (separate track) — those are flagged as out-of-scope where they touch this track's surface.

## Summary

Phase 6 is the FIRST human-verify milestone. The good news for the UI track: **almost everything the UI does is already built and proven.** The pure-Python `GameEngine` (`c14/engine.py`) owns the turn loop and already emits `on_enter` MolActions **per-action to an injected `molaction_sink` callable** (`engine.py:187-189`). The `MolOps.apply(action)` dispatch (`c14/pymol_layer/molops.py:112-196`) already translates 8 ops to `cmd.*` calls, plus 3 delegated ops (edit/restore/protonate). The `AssetManager` + `EditOps` + `EditRouter` are all done and unit-tested. The 5.3/5.4 conventions have FROZEN the exact `on_enter` MolAction sequences + the named-color palette + the cast-reveal template, and the headless smokes (`hero_highlight_smoke.py` 29/29 PASS, `scene_template_smoke.py` 37/37 PASS, `wt_align_smoke.py` 8/8 PASS) have PROVEN the `cmd.*` mechanisms the dispatches will wrap.

**The UI is genuinely a thin adapter.** The controller's job is narrow: (1) construct `GameEngine(graph, molaction_sink=<dispatch>, edit_router=router)`, (2) on each UI event call `engine.choose(index)` / `engine.apply_player_edit(intent, enzyme_id)` / `engine.save(path)` / `engine.load(path)`, (3) render the returned `TurnResult` (node text + eligible choices) into QtWidgets, (4) build an `EditIntent` from the player's edit-UI input whose `signature()` matches `edits.json`. The engine + molops do ALL the molecular work; the UI never calls `cmd.*` directly except through molops (the testability boundary).

**Phase 6 owes exactly 4 deferred molops dispatches** (the convention phases 5.3/5.4 deliberately deferred these to keep themselves 0-code design phases): `op="set_color"`, `op="label"`, `op="set"` (5.4 §2.1, OQ-1) + `op="align"` (5.3 §6, Q3). All 4 are **direct `cmd.*` calls** (no new injected dependency — they use the already-injected `self._cmd`, like `show`/`color`/`delete`). The exact `action.op` names, args schema, and verbatim dispatch pseudocode are FROZEN in the conventions (cited below) and reproduced in §Architecture Patterns. The `cmd.*` signatures are verified at exact `tmp/pymol-src` lines (HIGH confidence).

**The OQ-6 multi-C hero-fallback gate is a Qt prompt that must stay OUT of molops.** molops dispatch stays PURE (`cmd.*` only — no Qt, no prompts). The prompt lives in the controller layer via an **injected `prompt_fn` callback** (dependency injection, mirroring how molops injects `cmd`). For Phase 6 placeholder content (known-by-construction selectors), the gate is a no-op pass-through; it is WIRED + unit-tested with a mock prompt but not triggered by shipped content. Phase 7 real multi-C structures without authored selectors trigger it.

**Primary recommendation:** Split `c14/ui/` into a **Qt-free `controller.py`** (the mediator glue: engine wiring, node-tag reading, EditIntent building, hero-selector pre-validation, OQ-6 prompt-via-callback — all unit-testable in WSL python3.6 with mocks) + **QtWidgets widgets** (`main_window.py`, `widgets.py` — human-verify). The AST gate exempts `c14/ui/` entirely (`check_imports.py:33` `SKIP_DIRS = {"pymol_layer","ui","__pycache__"}`), so Qt imports ARE allowed there — but keeping the pure logic Qt-free maximizes testability and matches the 3-tier pattern the repo has used since Phase 1.

## Standard Stack

The stack is LOCKED by `PROJECT.md:84` ("PyQt5 via `pymol.Qt` + numpy only"). NO new dependencies. NO `pip install`. This is not a research finding — it is a constraint verified against `PROJECT.md` + `AGENTS.md`.

### Core (already proven — the UI adapts over these)
| Component | Location | Role in the UI adapter | Status |
|-----------|----------|------------------------|--------|
| `GameEngine` | `c14/engine.py` | The turn loop. Constructor takes `molaction_sink` (the controller wires this to its dispatch coordinator) + `edit_router`. API: `start/choose/apply_player_edit/save/load` → `TurnResult(node, molactions, eligible_choices)`. | DONE (Phase 2) |
| `MolOps` | `c14/pymol_layer/molops.py` | `apply(action)` → `cmd.*`. 8 ops + 3 delegated ops done; **4 deferred ops (set_color/label/set/align) owed in Phase 6**. | 11/15 ops done |
| `AssetManager` | `c14/pymol_layer/asset_manager.py` | `load_bundled/fetch_pubchem/fetch_pdb`. Injected into MolOps. | DONE (Phase 3) |
| `EditOps` | `c14/pymol_layer/edit_ops.py` | `apply_edit` (sole sanctioned `cmd.alter` path) + backup/restore. Injected into MolOps. | DONE (Phase 4) |
| `EditRouter` | `c14/edit_router.py` | `route(intent, enzyme_id, rng)` → node id. Injected into GameEngine. | DONE (Phase 4) |
| `MolAction` / `EditIntent` / `Node` / `Choice` | `c14/story/model.py` | The data shapes the UI renders + the edit routing carrier. Pure data, no pymol import. | DONE (Phase 2) |

### UI layer (Phase 6 builds this — gate-exempt, may import pymol.Qt)
| Component | Proposed location | Qt? | Testability |
|-----------|-------------------|-----|-------------|
| `controller.py` (the mediator) | `c14/ui/controller.py` | **NO QtWidgets import** (Qt-free) | Unit-testable in WSL python3.6 with mocks (the AST gate exempts `c14/ui/` but this file imports neither pymol nor PyQt5 — keeps the mediator logic testable) |
| `DispatchCoordinator` / `HeroResolver` | `c14/ui/controller.py` (or a sibling Qt-free module) | NO Qt (prompt via injected callback) | Unit-testable with mock `prompt_fn` + mock `count_fn` |
| `main_window.py` (QMainWindow) | `c14/ui/main_window.py` | YES `pymol.Qt` | Human-verify (Qt can't run in WSL) |
| `widgets.py` (story panel, choice panel, edit dialog) | `c14/ui/widgets.py` | YES `pymol.Qt` | Human-verify |
| `plugin_entry.py` (`__init_plugin__` + menu registration) | `c14/ui/__init__.py` or `plugin_entry.py` | YES `pymol.Qt` | Human-verify (packaging details are the OTHER researcher's track) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff — RECOMMENDATION |
|------------|-----------|---------------------------|
| Qt-free `controller.py` + Qt `main_window.py` split | One monolithic `main_window.py` with all logic | The split keeps the mediator logic unit-testable in WSL (matches the repo's 3-tier testability discipline). A monolith forces 100% human-verify. **Use the split.** |
| Injected `prompt_fn` callback for OQ-6 | `QMessageBox` call directly inside molops/dispatch | Putting Qt inside molops breaks its purity + testability (molops is currently unit-tested with MockCmd in pure python3.6). The injected callback mirrors how molops already injects `cmd`. **Use the injected callback.** |
| Pre-scan target node's `on_enter` for hero-resolution | Intercept hero ops inside the molaction_sink wrapper | Pre-scan is cleaner (the controller can `graph.get_node(choice.goto).on_enter` before the engine enters). The sink-wrapper interception requires hero-op detection heuristics. **Use pre-scan for choice.goto targets; for edit-routed nodes the branch `on_enter` is the WT-reveal (not hero-highlight) so no gate needed there.** See §Architecture Patterns. |

**Installation:** NONE. The stack ships with `pymol-open-source` (PyQt5 via `pymol.Qt` + numpy). No `npm`/`pip`. The plugin is loaded by PyMOL's Plugin Manager (packaging is the other researcher's track).

## Architecture Patterns

### Pattern 1: The controller/mediator — the UI is a thin adapter over the engine + molops

**What:** A single `Controller` class (Qt-free, in `c14/ui/controller.py`) owns the `GameEngine` instance and is the ONLY thing that talks to the engine. The QtWidgets widgets talk ONLY to the controller (never to the engine/molops/cmd directly). The controller constructs the engine with `molaction_sink=<its own dispatch method>` and `edit_router=<injected EditRouter>`, then on each UI event calls one engine method and renders the `TurnResult`.

**When to use:** Always — this IS the Phase 6 UI architecture. The thin-adapter property comes from the engine already owning the turn loop + the per-action molaction dispatch.

**The wiring (verified against `engine.py:83-89,163-194`):**

```python
# c14/ui/controller.py -- Qt-FREE (no QtWidgets import; AST-gate-exempt dir but
# kept pure for unit-testability). The mediator. Imports ONLY c14.* domain + the
# injected molops/edit_router/cmd handle (all passed in, never imported at top).
from c14.engine import GameEngine, TurnResult  # pure-Python (no pymol) -- OK
from c14.story.model import EditIntent, MolAction  # pure data -- OK


class Controller(object):
    """The mediator: wires QtWidgets events -> GameEngine -> MolOps dispatch.

    Qt-free: holds NO QtWidgets reference. The widgets call controller methods;
    the controller calls back into the widgets via an injected `view` interface
    (a thin protocol the main_window implements). This keeps the mediator logic
    unit-testable in WSL python3.6 with a MockView + MockMolOps + mock prompt.
    """

    def __init__(self, graph, molops, edit_router, cmd, view=None,
                 prompt_fn=None, count_fn=None):
        # molops: the MolOps instance (real in prod; MockMolOps in tests).
        # cmd: the pymol.cmd handle (for the hero-selector count pre-check).
        # view: the MainWindow (implements render_turn(turn_result), etc.).
        # prompt_fn: the OQ-6 warn+confirm callback (QtMessageBox in prod; mock
        #   in tests). None => OQ-6 gate disabled (Phase 6 placeholder content
        #   uses known-by-construction selectors, so the gate is a no-op).
        # count_fn: wraps cmd.count_atoms (injectable for tests).
        self._molops = molops
        self._cmd = cmd
        self._view = view
        self._prompt_fn = prompt_fn
        self._count_fn = count_fn or (lambda sele: cmd.count_atoms(sele))
        # The engine's molaction_sink = THIS controller's dispatch method.
        # The engine emits `for action in actions: sink(action)` (engine.py:188);
        # our dispatch forwards each to molops.apply (the 02-04 per-action contract).
        self._engine = GameEngine(
            graph,
            molaction_sink=self._dispatch_molaction,
            edit_router=edit_router)

    # ---- the molaction_sink the engine calls (engine.py:187-189) ----
    def _dispatch_molaction(self, action):
        # Pure forward to molops. The OQ-6 hero gate runs as a PRE-PASS before
        # the engine enters a node (see _resolve_hero_for_node), NOT here --
        # molops stays pure (cmd.* only). This method is the testability seam:
        # tests assert the controller forwarded each MolAction to molops.apply.
        self._molops.apply(action)

    # ---- UI event handlers (called by the QtWidgets widgets) ----
    def start_game(self, character="glucose", seed=None):
        turn = self._engine.start(character, seed)
        self._render(turn)

    def choose(self, index):
        # OQ-6 hero pre-check: read the TARGET node's on_enter BEFORE the engine
        # enters it (choice.goto is readable). Resolve the hero selector; prompt
        # if multi-C-no-selector. See Pattern 3.
        self._resolve_hero_for_target(self._target_node_id_for_choice(index))
        turn = self._engine.choose(index)
        self._render(turn)

    def apply_edit(self, edit_intent):
        # The edit-allowed node's enzyme_id is read from its tags (edit:enzyme:<id>).
        # The routed branch node's on_enter is the WT-reveal (5.3), NOT a hero-
        # highlight -- so no OQ-6 gate here. The hero-highlight fires at substrate
        # traversal nodes reached via choice.goto (handled in choose()).
        enzyme_id = self._current_enzyme_id()  # reads current node's edit:enzyme tag
        turn = self._engine.apply_player_edit(edit_intent, enzyme_id)
        self._render(turn)

    def save(self, path):
        self._engine.save(path)  # Pattern 6: scene rebuilds on load via on_enter replay

    def load(self, path):
        turn = self._engine.load(path)  # replays current node's on_enter -> molops
        self._render(turn)

    # ---- render the TurnResult into the view (the widgets) ----
    def _render(self, turn):
        if self._view is not None:
            self._view.render_turn(turn)
```

**Why this is a thin adapter:** the controller adds ~6 event-handler methods + 1 dispatch forwarder. The engine does the turn loop; molops does the molecular work; the controller just routes. The `TurnResult` (`engine.py:43-64`) carries exactly what the UI needs: `node` (text_dramatic/text_teaching/choices/is_ending), `molactions` (already dispatched — the UI doesn't re-dispatch), `eligible_choices` (the buttons to render).

**Qt-free vs Qt-required split (the testability boundary):**

| Lives in `c14/ui/controller.py` (Qt-FREE, unit-testable) | Lives in `c14/ui/main_window.py` + `widgets.py` (Qt, human-verify) |
|----------------------------------------------------------|-------------------------------------------------------------------|
| Engine construction + wiring (`molaction_sink=self._dispatch`) | QMainWindow layout (character select, story panel, choice panel, toolbar) |
| `choose/apply_edit/save/load` event handlers (call engine, render result) | `render_turn(turn)` — populate the story text + choice buttons from the TurnResult |
| EditIntent construction from edit-UI input (the `signature()` must match edits.json) | The edit dialog widgets (residue picker, mutation chooser, protonation selector) |
| `enzyme_id` extraction from node tags (`edit:enzyme:<id>` — `05.1-DESIGN.md:619-623`) | Signal/slot connections (button.clicked -> controller.choose) |
| OQ-6 hero-selector pre-validation (`HeroResolver` + injected `prompt_fn`/`count_fn`) | The actual `QMessageBox.question` prompt implementation (passed AS `prompt_fn`) |
| Choice-goto target lookup for the hero pre-pass | The character-select combo box / start dialog |

The controller is unit-testable: inject a `MockMolOps` (records `apply` calls), a `MockView` (records `render_turn` calls), a `mock prompt_fn`, and a `mock count_fn`. Assert the controller built the right `EditIntent`, called `engine.choose(index)`, forwarded each `MolAction` to `molops.apply`, and rendered the `TurnResult`. This mirrors exactly how `tests/test_engine.py:64` uses `molaction_sink=sink.append` as the mock sink.

### Pattern 2: The 4 deferred molops dispatches (CRITICAL — this is owed work from 5.3/5.4)

Phase 6 MUST add 4 `elif` branches to `MolOps.apply` (`c14/pymol_layer/molops.py:112-196`). The conventions FROZE the exact op names + args schema + dispatch pseudocode; the smokes PROVED the `cmd.*` mechanisms. **All 4 are direct `self._cmd.*` calls — NO new injected dependency** (unlike `load`→AssetManager, `edit`→EditOps). `apply` returns `None` for all 4 (consistent with all ops); the `cmd.*` return values (C status ints / RMSD tuples) are discarded at runtime.

#### 2a. `op="set_color"` (5.4 §2.1, OQ-1 — deferred dispatch #1)

**Args schema (FROZEN, `05.4-CONVENTION.md:58-62`):**
```jsonc
{"op": "set_color", "target": null,
 "args": {"name": "hero_cyan",            // the named color to define (idempotent overwrite)
          "rgb": [0.0, 0.75, 0.75]}}       // [r,g,b] in 0.0-1.0 OR 0-255 (auto-detected; PLACEHOLDER pending Phase 7)
```

**Dispatch (FROZEN verbatim, `05.4-CONVENTION.md:125-127`):**
```python
elif op == "set_color":
    # src: tmp/pymol-src/modules/pymol/viewing.py:2107 cmd.set_color
    self._cmd.set_color(action.args["name"], action.args["rgb"])
```

**Verified cmd signature** (`tmp/pymol-src/modules/pymol/viewing.py:2107`): `def set_color(name, rgb, mode=0, quiet=1, *, _self=cmd)` — confirms `cmd.set_color(name, rgb)` positional call. Idempotent overwrite (re-running on `on_enter` replay / re-init is safe — `_invalidate_color_sc` refreshes the cache, `viewing.py:2161`). Auto-detects 0-1 vs 0-255 RGB range (`viewing.py:2155-2156`). **HIGH confidence.**

#### 2b. `op="label"` (5.4 §2.1, OQ-1 — deferred dispatch #2)

**Args schema (FROZEN, `05.4-CONVENTION.md:66-71`):**
```jsonc
{"op": "label", "target": "hero_atom",
 "args": {"sele": null,                   // optional explicit sele; defaults to target
          "text": "YOU"}}                 // the player-facing identity label (dispatch wraps as '"YOU"')
// clear: {"op":"label","target":"hero_atom","args":{"text":""}}
```

**Dispatch (FROZEN verbatim, `05.4-CONVENTION.md:128-135`):**
```python
elif op == "label":
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label
    # Wrap text as a quoted-string expression: '"YOU"' (the label expression
    # is a Python expression; a bare "YOU" would evaluate the atom property `YOU`).
    text = action.args.get("text", "")
    sele = action.args.get("sele", action.target)
    expr = '"{0}"'.format(text.replace('"', '\\"'))  # quote the literal string
    self._cmd.label(sele, expr)
```

**Verified cmd signature** (`tmp/pymol-src/modules/pymol/viewing.py:1332`): `def label(selection="(all)", expression="", quiet=1, *, _self=cmd)` — confirms `cmd.label(sele, expr)` (selection first, expression second). The **quoted-string footgun** (RESEARCH-api §F Pitfall 2): a bare `"YOU"` would try to evaluate the atom property `YOU` and fail; `'"YOU"'` → iterate `label`==`'YOU'` (empirically confirmed in `hero_highlight_smoke.py:167,194`). The dispatch wraps this footgun so story authors never hit it. **HIGH confidence.**

#### 2c. `op="set"` (5.4 §2.1, OQ-1 — deferred dispatch #3)

**Args schema (FROZEN, `05.4-CONVENTION.md:75-80`):**
```jsonc
{"op": "set", "target": "hero_atom",
 "args": {"name": "sphere_scale",         // the per-atom setting name
           "value": 0.3,                   // SMALL elegant sphere (NOT the giant default 1.0)
           "sele": null}}                  // optional explicit sele; defaults to target
```

**Dispatch (FROZEN verbatim, `05.4-CONVENTION.md:136-139`):**
```python
elif op == "set":
    # src: tmp/pymol-src/modules/pymol/setting.py:183 cmd.set
    self._cmd.set(action.args["name"], action.args["value"],
                  action.args.get("sele", action.target))
```

**Verified cmd signature** (`tmp/pymol-src/modules/pymol/setting.py:183`): `def set(name, value=1, selection='', state=0, updates=1, log=0, quiet=1, _self=cmd)` — confirms `cmd.set(name, value, selection)` (selection is 3rd positional). `sphere_scale` is a per-atom setting that `show_as`/`color` don't cover; a generic `op="set"` (name/value/sele) is reusable beyond `sphere_scale` (future `transparency`, `sphere_transparency`). **HIGH confidence.**

#### 2d. `op="align"` (5.3 §6, Q3 — deferred dispatch #4)

**Args schema (FROZEN, `05.3-CONVENTION.md:220-229`):**
```jsonc
// on_enter entry -- align the WT (mobile, moved) onto the edited enzyme (fixed, stays)
{"op": "align",
 "target": "<enzyme>_wt",                       // the MOBILE object (MOVED)
 "args": {
   "reference": "<enzyme>",                      // the FIXED object (STAYS) -- named "reference" NOT "target"
   "method": "super",                            // "super"(default) | "align" | "cealign"
   "align_sele": "name CA"                       // optional substructure scope; default "name CA"; None => whole object
 }}
```

**Dispatch (FROZEN verbatim, `05.3-CONVENTION.md:240-258`):**
```python
elif op == "align":
    method = action.args.get("method", "super")
    reference = action.args["reference"]
    sele = action.args.get("align_sele")  # None => whole object
    mobile = action.target if sele is None else "{0} and {1}".format(action.target, sele)
    ref = reference if sele is None else "{0} and {1}".format(reference, sele)
    if method == "super":
        # src: tmp/pymol-src/modules/pymol/fitting.py:242 cmd.super  (mobile MOVED, target FIXED)
        self._cmd.super(mobile, ref)
    elif method == "align":
        # src: tmp/pymol-src/modules/pymol/fitting.py:306 cmd.align  (mobile MOVED, target FIXED)
        self._cmd.align(mobile, ref)
    elif method == "cealign":
        # src: tmp/pymol-src/modules/pymol/fitting.py:27 cmd.cealign  NOTE: arg order is (target, mobile) -- REVERSED
        self._cmd.cealign(ref, mobile)  # dispatch normalizes the reversal: ref=target(fixed) first, mobile second
    else:
        raise ValueError("molops.align: unknown method {!r}".format(method))
```

**Verified cmd signature** (`tmp/pymol-src/modules/pymol/fitting.py:242`): `def super(mobile, target, cutoff=2.0, cycles=5, ..., transform=1, ..., *, _self=cmd)` — confirms `cmd.super(mobile, target)` (mobile first, target=fixed second; `transform=1` default moves the WHOLE mobile object using the substructure-derived transform — empirically confirmed in `wt_align_smoke.py` + `05.3-RESEARCH-pymol-align-api.md §A.5`). The dispatch **encapsulates 2 API footguns** so story authors never hit them: (1) the `cealign` reversed arg order `(target, mobile)` (`fitting.py:27`), (2) the `target=fixed` naming collision (PyMOL's `target` arg means FIXED, NOT "thing aimed at" — `05.3-CONVENTION.md:141-151`). **HIGH confidence.**

#### The 6-call hero-highlight sequence the dispatches enable (5.4 §3.3 — FROZEN)

Once the 3 new ops (2a/2b/2c) land, the hero-highlight is authored as a 6-MolAction `on_enter` sub-sequence (NOT a super-op — `05.4-CONVENTION.md:91-118` resolved this). This is the SC1 (CHAR-02) contract Phase 6 implements:

```jsonc
// The hero-highlight sequence (6 peer-primitive MolActions, NOT a super-op)
{"op": "set_color", "target": null, "args": {"name": "hero_cyan", "rgb": [0.0, 0.75, 0.75]}},
{"op": "show_as", "target": "<hero_obj>", "args": {"rep": "sticks", "sele": "<hero_obj>"}},
{"op": "color", "target": "<hero_obj>", "args": {"color": "hero_cyan", "sele": "<hero_obj> and elem C"}},
{"op": "show", "target": "<hero_obj>", "args": {"rep": "spheres", "sele": "<hero_sele>"}},
{"op": "set", "target": "<hero_obj>", "args": {"name": "sphere_scale", "value": 0.3, "sele": "<hero_sele>"}},
{"op": "label", "target": "<hero_obj>", "args": {"sele": "<hero_sele>", "text": "YOU"}}
```

This is EXACTLY what `tools/hero_highlight_smoke.py:154-167` proved headlessly (calling `cmd.*` directly — the dispatches will wrap the same calls). The smokes are the regression target: after the 4 dispatches land, a `molops_hero_dispatch_smoke.py` should dispatch the SAME sequence via `molops.apply(MolAction(...))` and assert the same post-conditions (count==1 / elem C / rep spheres+sticks / color-name round-trip `hero_cyan` / label `"YOU"`).

### Pattern 3: The OQ-6 warn+confirm Qt prompt — clean separation (molops stays pure)

**The problem (`05.4-CONVENTION.md:171-186`, OQ-6 OVERRIDE):** the hero-selection rule has 3 cases: (1) authored `hero_selector` metadata → use it; (2) single-C object → auto-derive the unique carbon; (3) multi-C object WITHOUT `hero_selector` → auto-pick a DEFAULT carbon + WARN + require a yes/no CONFIRM. The confirm IS the no-fabricated-science guard — silently highlighting the wrong carbon is a science error (the hero-identity is load-bearing for the whole narrative). **This is a Phase 6 UI behavior** (`05.4-CONVENTION.md:183`); the smokes use known-by-construction selectors and do NOT exercise the warn+confirm path.

**The constraint:** molops dispatch MUST stay pure (`cmd.*` only — no Qt, no prompts). The existing `tests/test_molops.py` injects a `MockCmd` in pure python3.6; putting a `QMessageBox` inside molops would break that.

**The clean separation (RECOMMENDED):** the OQ-6 gate lives in the **controller layer**, driven by an **injected `prompt_fn` callback** (dependency injection, mirroring how molops injects `cmd`). The gate runs as a **PRE-PASS before the engine enters the target node**, NOT inside the molaction_sink (which would require hero-op detection heuristics mid-dispatch).

```python
# c14/ui/controller.py -- the OQ-6 gate (Qt-free; prompt via injected callback)

class HeroResolver(object):
    """Resolve the hero selector for a node's on_enter hero-highlight sequence.

    Qt-free: the prompt is an injected callback. Pure logic is unit-testable
    with a mock prompt_fn + mock count_fn. Implements 05.4-CONVENTION.md §3.1
    rule steps 1-3 (authored selector / single-C auto-derive / multi-C default
    + warn + confirm).
    """

    def __init__(self, count_fn, prompt_fn):
        # count_fn(sele) -> int  (wraps cmd.count_atoms; injectable for tests)
        # prompt_fn(message) -> bool  (QtMessageBox.question in prod; mock in tests)
        self._count_fn = count_fn
        self._prompt_fn = prompt_fn

    def resolve(self, on_enter_actions):
        """Return the (possibly rewritten) on_enter actions with the hero
        selector resolved. If a hero-highlight sequence targets a multi-C
        object with no authored selector, prompt; on confirm, inject the
        default selector (first C by resi); on reject, leave the sequence
        unchanged (the highlight will apply to the authored sele as-is).

        For Phase 6 placeholder content (authored known-by-construction
        selectors resolving to exactly 1 atom), this is a no-op pass-through
        -- the gate is wired + unit-tested but NOT triggered by shipped content.
        """
        # Detect the hero-highlight sequence: a `label` op with text "YOU" (the
        # OQ-4 hero marker) whose sele is a hero-bearing object. The hero ops
        # are show_as/color/show/set/label on the same <hero_obj> target.
        # (Detection by the "YOU" label is robust -- it's the frozen hero marker.)
        for action in on_enter_actions:
            if (action.op == "label"
                    and action.args.get("text") == "YOU"):
                hero_sele = action.args.get("sele", action.target)
                hero_obj = action.target
                # Case 1/2: authored selector or single-C -- count the sele.
                n = self._count_fn(hero_sele)
                if n == 1:
                    return on_enter_actions  # deterministic -- no prompt
                # Case 3: multi-C, ambiguous. Pick a default (first C by resi)
                # + warn + confirm (OQ-6 OVERRIDE).
                default_sele = "{0} and elem C and first resi".format(hero_obj)
                # Actually pick: the first carbon atom. A robust default:
                # cmd.iterate to get the first C's (chain,resi,name), then build
                # a sele. For the MVP, "elem C" scoped to the object + take the
                # first via count+iterate. (Phase 7 authors real selectors, so
                # this default is a safety net only.)
                confirmed = self._prompt_fn(
                    "This structure has {0} carbons. The hero (C14) is ambiguous. "
                    "Highlight the first carbon as the hero?".format(n))
                if confirmed:
                    return self._rewrite_hero_sele(on_enter_actions, default_sele)
                return on_enter_actions  # rejected -- leave as-is
        return on_enter_actions  # no hero-highlight in this on_enter -- no-op
```

**How the controller invokes it (the PRE-PASS):**

```python
# In Controller (c14/ui/controller.py):

def _resolve_hero_for_target(self, target_node_id):
    """OQ-6 pre-pass: read the TARGET node's on_enter BEFORE the engine enters
    it, resolve the hero selector, and cache the resolution so the engine's
    per-action dispatch (which calls _dispatch_molaction -> molops.apply) uses
    the resolved selector.

    For choice.goto targets the controller can read the target ahead of time.
    For edit-routed nodes the branch on_enter is the WT-reveal (5.3 align), NOT
    a hero-highlight -- so no gate needed there.
    """
    if target_node_id is None or self._hero_resolver is None:
        return
    target = self._engine.graph.get_node(target_node_id)
    # The resolver may rewrite the on_enter (inject the default selector).
    # The rewritten actions are stashed; _dispatch_molaction uses them INSTEAD
    # of the engine's originals. (Implementation detail: the controller can
    # monkey-patch the node's on_enter for this entry, or maintain a pending-
    # actions queue the sink drains. The simplest: a pending_rewrites dict
    # keyed by node_id that _dispatch_molaction consults.)
    resolved = self._hero_resolver.resolve(target.on_enter)
    self._pending_on_enter = resolved  # _dispatch_molaction drains this
```

**Why this is clean:**
1. **molops stays pure** — no Qt, no prompts. The 4 new dispatches are `cmd.*` only.
2. **The controller is Qt-free** — `prompt_fn` is injected (a `QMessageBox.question` wrapper in prod, a mock in tests). The `HeroResolver` is unit-testable: inject a `mock count_fn` returning 3 + a `mock prompt_fn` returning True, assert the resolver rewrote the hero sele to the default.
3. **The pre-pass runs before dispatch** — no mid-dispatch interception heuristics inside the molaction_sink. The controller reads `graph.get_node(choice.goto).on_enter` (the graph is readable), resolves, then `engine.choose(index)` dispatches the (possibly rewritten) actions.
4. **Phase 6 placeholder content doesn't trigger it** — the smokes use known-by-construction selectors (`name C1` resolving to exactly 1 atom). The gate is WIRED + unit-tested with mocks but is a no-op for shipped content. Phase 7 real multi-C structures without authored selectors trigger it.

**Open implementation detail for the planner:** the engine generates `on_enter` actions internally inside `_enter` (`engine.py:176-177`) and dispatches them in the same call. The controller's pre-pass rewrites the target node's `on_enter` — but the engine reads `node.on_enter` fresh each entry. The cleanest implementation: the controller's `_dispatch_molaction` sink drains a `self._pending_on_enter` queue (set by the pre-pass) INSTEAD of forwarding the engine's original actions when a rewrite exists. OR (simpler): the controller monkey-patches `target_node.on_enter = resolved` before `engine.choose` (the Node is mutable — `model.py:268` `on_enter` is a plain list). The planner should pick the approach that keeps `tests/test_engine.py` green (the engine tests use fixture nodes whose `on_enter` is read-only-ish — verify the mutation doesn't leak across turns; the engine re-reads `node.on_enter` each `_enter` so a one-shot mutation + restore is safe).

### Pattern 4: Two-layer text rendering (dramatic + teaching)

**What:** `Node` carries `text_dramatic` (in-character prose) + `text_teaching` (the scientific "what's really happening") (`model.py:244-245`). `PROJECT.md:72` requires both layers; `PROJECT.md:84` requires "UI simple and user-friendly."

**Recommendation: stacked, not tabbed.** Show `text_dramatic` prominently (larger font, top of the story panel) and `text_teaching` directly below in a smaller/dimmed font or a collapsible "Show science" expander. Rationale: tabs hide the teaching layer (students may skip it); stacking shows both at once (the educator audience benefits from simultaneous view). A `QLabel` (dramatic, wrapped) + a `QTextEdit`/`QLabel` (teaching, smaller) inside a `QVBoxLayout` is ~10 lines. Keep it simple — no rich-text markdown rendering (plain text + maybe bold for terms; `PROJECT.md` says simple).

```python
# c14/ui/widgets.py -- the story panel (Qt, human-verify)
class StoryPanel(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        self._dramatic = QtWidgets.QLabel()
        self._dramatic.setWordWrap(True)
        self._dramatic.setStyleSheet("font-size: 14pt;")  # prominent
        self._teaching = QtWidgets.QLabel()
        self._teaching.setWordWrap(True)
        self._teaching.setStyleSheet("font-size: 10pt; color: gray;")  # dimmed
        layout.addWidget(self._dramatic)
        layout.addWidget(self._teaching)

    def render_node(self, node):
        self._dramatic.setText(node.text_dramatic)
        self._teaching.setText(node.text_teaching)
```

### Pattern 5: Choice panel + the edit interface (curated, not free-form chemistry)

**Choice panel:** `TurnResult.eligible_choices` (`engine.py:193`) is the list of `Choice` objects. Render each `Choice.label` as a `QPushButton` in a `QVBoxLayout`. On click → `controller.choose(index)`. For weighted (RNG) choices (`tca.shuffle`), the engine's `choose` ignores the index (the RNG picks — `engine.py:121-131`); the UI can render a single "Spin the wheel" button or show both weighted labels with a note. **`05.1-DESIGN.md:488-489` flags this as a UI/UX open question for Plan 06** — the planner should decide how the player triggers `edit:offer` vs the RNG shuffle when both are eligible.

**Edit interface — CURATED, not free-form chemistry** (`PROJECT.md:80`: "The game holds a curated lookup table of known edits per enzyme/substrate context"). The edit routing is a lookup table (`c14/data/edits.json`): the player's `EditIntent.signature()` (`model.py:112-126`) is matched with `==` against `edits.json` `signature` entries (`edit_router.py:142`). So the UI must produce an `EditIntent` whose `signature()` EXACTLY matches a known entry (else it routes to the bad-ending pool — which is a valid game outcome, but the UI should offer the curated "correct fix" + a few plausible wrong options).

**The edit UI produces an `EditIntent(op, target, args, enzyme_id)`** where:
- `op` ∈ `{"point_mutation", "substrate_edit", "protonation_change"}` (`model.py:91-93`).
- `target` = residue/atom selector (e.g. `"resi 57 and chain A"` for a point mutation).
- `args` = op-specific (`{"new_res": "ALA"}` / `{"group": "-OH", "action": "add"}` / `{"resn": "HIP"}`).
- `enzyme_id` = the current node's `edit:enzyme:<id>` tag (`05.1-DESIGN.md:619-623`): `enzyme_id = next((t.split(":", 2)[2] for t in node.tags if t.startswith("edit:enzyme:")), None)`.

**Recommendation: the edit dialog offers a CURATED list of edit options per enzyme** (read from `edits.json` for the current `enzyme_id` + a few wrong options). The player picks one (radio buttons / a combo), the controller builds the `EditIntent` from the selection, calls `engine.apply_player_edit(intent, enzyme_id)`. NO free-form residue-entry / free-form mutation-text — that would produce `EditIntent`s whose `signature()` matches nothing and always routes to the bad-ending pool (a valid but unfun outcome). The curated list makes the edit a meaningful choice. The `edits.json` for Phase 6 is the placeholder fixture (`c14/data/edits.json`: 1 enzyme `fixture_enzyme_1` with 1 known edit); Phase 7 fills the real per-enzyme entries.

```python
# c14/ui/controller.py -- building an EditIntent from the edit dialog (Qt-free, testable)
def build_edit_intent(self, op, target, args):
    """Build an EditIntent whose signature() must match edits.json. The edit
    dialog (Qt) collects op/target/args from the curated options; the controller
    assembles the EditIntent + reads the enzyme_id from the current node's tags.
    """
    enzyme_id = self._current_enzyme_id()  # reads current node's edit:enzyme:<id> tag
    if enzyme_id is None:
        raise RuntimeError("current node is not edit-allowed (no edit:enzyme tag)")
    return EditIntent(op, target, args, enzyme_id)
```

### Pattern 6: Scene reconstruction on load (ALREADY PROVEN — the UI just calls engine.load)

**What:** `engine.load(path)` replays the current node's `on_enter` MolActions to reconstruct the 3D scene (Pattern 6, `engine.py:20-22,203-213`). NO `.pse` is saved (`c14/persist.py:50-51` writes ONLY `GameState` JSON). The molecular scene is a **pure function of game state** — re-derived from the deterministic `on_enter` sequence every time the node is entered (on `start`, `choose`, `apply_player_edit`, AND `load`).

**The UI/controller does NOTHING special for scene reconstruction on load.** It just calls `engine.load(path)`; the engine's `_enter` (`engine.py:163-194`) runs `on_enter` → dispatches each MolAction to `self.molaction_sink` (the controller's `_dispatch_molaction` → `molops.apply` → `cmd.*`). The scene rebuilds automatically. This was PROVEN in Phase 2/3 (the engine tests + the molops smoke). The hero-highlight (5.4 §3.4) is likewise a pure function of `on_enter` — it re-applies on load with no runtime marker needed (a `cmd.flag`/`alter` set once would be LOST on load; the `on_enter` replay is the persistence mechanism).

**Implication for the UI:** the Save/Load buttons just call `controller.save(path)` / `controller.load(path)`. No scene-serialization code. No `.pse` management. This is the Anti-Pattern 5 avoidance (`engine.py:21`) — the UI benefits from it for free.

### Pattern 7: The main window layout (Success Criterion #1)

**What:** SC1 (`ROADMAP.md:204`) requires "the main window opens with character selection, story text, choice panel, and cast/help/save/load/achievement controls."

**Recommended layout (keep simple per `PROJECT.md:84`):**

```
QMainWindow
├── QMenuBar (Help, maybe Cast)
├── QToolBar OR top row of QPushButtons: [New Game] [Save] [Load] [Achievements] [Help]
└── central QWidget (QVBoxLayout)
    ├── StoryPanel (Pattern 4: dramatic + teaching, stacked)
    ├── ChoicePanel (Pattern 5: one QPushButton per eligible Choice)
    └── status bar (current node id / character / seed -- helps demos + debugging)
```

Character selection: a start dialog (modal `QDialog` with 3 radio buttons: Glucose / Fatty acid [Phase 8] / Alcohol [Phase 8]) OR a combo box in the toolbar that calls `controller.start_game(character)`. For Phase 6 only Glucose is playable (FA/Alc are `fa.stub`/`alc.stub` per `05.1-DESIGN.md`). A start dialog is cleaner (matches the "begin a new game" RPG feel).

**Reference patterns:** `Pymol-script-repo/plugins/dynoplot.py:21` shows the modern `from pymol.Qt import QtCore, QtGui, QtWidgets` import style (the repo convention per `AGENTS.md`). The plugin entry point is `__init_plugin__` + `plugins.addmenuitemqt(label, callback)` (verified against the bundled `lightingsettings_gui/__init__.py:13-15` + `pymol/plugins/__init__.py:100,320-321`). The callback creates + shows the `QMainWindow`. **Plugin packaging/install (the .zip structure, `install_modules`, Plugin Manager registration) is the OTHER researcher's track** — this track only needs the entry point to launch the main window.

## Don't Hand-Roll

The engine + molops + edit_router already provide these — the UI must NOT reimplement them:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| The turn loop (advance node, apply effects, emit on_enter, detect ending) | A controller-owned turn loop | `GameEngine.start/choose/apply_player_edit` (`engine.py:92-161`) | Already built + unit-tested (Phase 2). The controller just calls these. |
| MolAction → cmd.* translation | Direct `cmd.*` calls in the UI | `MolOps.apply(action)` (`molops.py:112-196`) | The testability boundary. The UI forwards MolActions to molops, never calls `cmd.*` directly (except the hero count pre-check, which uses the injected `count_fn`). |
| Per-action dispatch (one MolAction per apply) | A batch dispatch | `engine.py:187-189` `for action in actions: self.molaction_sink(action)` — the engine ALREADY dispatches per-action | The 02-04 contract. The controller's sink receives ONE MolAction per call (mirrors `tests/test_engine.py:64` `sink.append`). |
| Scene reconstruction on load | `.pse` save/load or manual scene re-application | `engine.load(path)` (`engine.py:203-213`) replays `on_enter` → molops → cmd.* | Pattern 6, proven Phase 2/3. Anti-Pattern 5. The UI just calls `engine.load`. |
| Edit routing (known → branch, unknown → bad pool) | A chemistry-correctness engine or fuzzy matching | `EditRouter.route(intent, enzyme_id, rng)` (`edit_router.py:122-149`) — exact dict-equality on `signature()` | `PROJECT.md:80` settled this: lookup table + bad-ending fallback. The UI builds the `EditIntent`; the router routes. |
| Hero-selector resolution logic | A new selector-heuristic in molops | The `HeroResolver` (controller layer, Pattern 3) + the authored `hero_selector` metadata (Phase 7) | molops stays pure. The 5.4 §3.1 rule is a controller concern (it may prompt). |
| RGB color parsing / named-color cache | Custom color management | `cmd.set_color(name, rgb)` (auto-detects 0-1 vs 0-255; idempotent) | `viewing.py:2107,2155-2156`. The `op="set_color"` dispatch wraps this. |
| Label expression quoting | Manual string escaping | The `op="label"` dispatch wraps `text` as `'"YOU"'` | The quoted-string footgun (RESEARCH-api §F Pitfall 2). Authors pass `text="YOU"`; the dispatch quotes it. |
| Align arg-order / method selection | Custom alignment code | The `op="align"` dispatch normalizes `cealign` reversal + `target=fixed` | `05.3-CONVENTION.md:155`. `cmd.super`/`align`/`cealign` are built-in; the dispatch encapsulates the 2 footguns. |

**Key insight:** the UI's value-add is PRESENTATION (rendering text/choices, collecting edit input, the OQ-6 prompt) + WIRING (engine ↔ molops ↔ widgets). It adds NO domain logic. Every molecular operation goes through `MolOps.apply`; every turn advancement goes through `GameEngine`. This is what makes the UI a thin adapter.

## Common Pitfalls

### Pitfall 1: Qt can't run in WSL — design for the testability split from day one
**What goes wrong:** putting ALL controller logic inside `main_window.py` (a QtWidgets class) makes 100% of the UI logic human-verify-only. WSL `python3.6` can't import `pymol.Qt` (no display, no PyQt5 in the WSL env — `AGENTS.md` "WSL/Windows split").
**Why it happens:** it's tempting to put the engine-wiring logic in the QMainWindow class (it's where the buttons live).
**How to avoid:** the `controller.py` (Qt-free) + `main_window.py` (Qt) split (Pattern 1). The controller holds the engine + molops + the event handlers; the widgets are dumb renderers. Unit-test the controller with `MockMolOps` + `MockView` in WSL `python3.6`; human-verify only the Qt rendering.
**Warning signs:** a `python3.6 -m py_compile c14/ui/main_window.py` succeeds but `python3.6 -c "import c14.ui.main_window"` fails with `ModuleNotFoundError: No module named 'pymol'` — that's EXPECTED for the Qt files (gate-exempt), but the controller.py MUST import cleanly in pure python3.6.

### Pitfall 2: The OQ-6 multi-C confirm gate — don't put it in molops, and don't skip wiring it
**What goes wrong:** (a) putting the `QMessageBox` inside `molops.apply` breaks molops's purity + the MockCmd unit tests; OR (b) skipping the gate entirely ("placeholder content uses known selectors, ship without it") leaves the no-fabricated-science guard unimplemented when Phase 7 loads real multi-C structures.
**Why it happens:** the gate is a UI behavior (`05.4-CONVENTION.md:183`) and the smokes don't exercise it, so it's easy to defer.
**How to avoid:** wire the `HeroResolver` + injected `prompt_fn` (Pattern 3) in Phase 6. Unit-test it with a mock `count_fn` returning 3 + mock `prompt_fn` returning True/False. The shipped placeholder content won't trigger it (known selectors → count==1 → no prompt), but the gate IS implemented + tested for Phase 7.
**Warning signs:** `tests/test_controller.py` has no test for the multi-C prompt path.

### Pitfall 3: Scene reconstruction on load — don't save a .pse, don't re-apply scene manually
**What goes wrong:** (a) saving a `.pse` via `cmd.save` and loading it on `engine.load` — breaks the pure-function-of-state invariant (Anti-Pattern 5, `engine.py:21`) + the `.pse` doesn't round-trip the hero-highlight reliably; OR (b) the controller manually re-applying `on_enter` MolActions after `engine.load` — double-dispatch (the engine ALREADY replays them in `_enter`).
**Why it happens:** it feels like "load should restore the scene" — and it does, but via the engine's `on_enter` replay, not via a saved session.
**How to avoid:** `controller.load(path)` just calls `engine.load(path)` (Pattern 6). The engine's `_enter` replays `on_enter` → `molaction_sink` → `molops.apply` → `cmd.*`. The scene rebuilds automatically. Verify with a save-mid-game-then-load test asserting the same node + the same visible reps.
**Warning signs:** the controller has a `_rebuild_scene` method that calls `molops.apply_all` — that's a double-dispatch bug.

### Pitfall 4: The `edit:offer` vs RNG-shuffle UI ambiguity at `tca.shuffle`
**What goes wrong:** `tca.shuffle` (`05.1-DESIGN.md:473`) has 2 weighted choices (turn1=0.5, turn2=0.5) + 2 non-weighted (edit:offer, cycle-trap). When weighted choices are eligible, the engine's `choose` has the RNG pick among the weighted ones (`engine.py:121-131`) — the non-weighted edit/cycle-trap are NOT separately player-pickable while a weighted choice is eligible. The UI must clarify how the player triggers the edit vs the RNG spin.
**Why it happens:** the eligible_choices list contains all 4, but the engine's resolution depends on whether any has a weight.
**How to avoid:** `05.1-DESIGN.md:488-489` flags this as a UI/UX open question for Plan 06. The controller should detect weighted choices (any `choice.weight is not None`) and render the UI accordingly: if weighted choices exist, show a "Spin the wheel" button (the RNG picks) + a separate "Edit aconitase" button (the edit:offer) + the cycle-trap as a conditional button. The planner should resolve this explicitly.
**Warning signs:** the choice panel renders all 4 choices as equal buttons and the player clicking "edit" does nothing (the RNG already picked a weighted choice).

### Pitfall 5: The `pyr.branch` cond-syntax — runtime eligibility vs structural reachability
**What goes wrong:** `05.1-DESIGN.md` (STATE.md note) flags that `pyr.branch`'s cond `"not flags.host_o2_low"` uses dict-attribute access which the interpreter's `_cond` evaluates to fail-safe False on `AttributeError` → both choices hidden at runtime. The BFS reachability is unaffected (cond is ignored structurally), but at RUNTIME the player can't advance.
**Why it happens:** the skeleton uses `flags.host_o2_low` (attribute access) but `_cond` exposes `flags` as a dict — `flags.host_o2_low` raises `AttributeError` → False.
**How to avoid:** the controller (or Phase 7 content) should refine the cond to `flags.get('host_o2_low')` (dict-method form). This is a RUNTIME concern for Phase 6 (the player must be able to advance past `pyr.branch`). The planner should verify the interpreter's `_cond` actually evaluates the skeleton's conds correctly, or fix the cond syntax.
**Warning signs:** at `pyr.branch`, no choices are clickable (all conds evaluate False).

### Pitfall 6: The `c14/ui/` AST-gate exemption — it's permissive, don't abuse it
**What goes wrong:** `check_imports.py:33` `SKIP_DIRS = {"pymol_layer","ui","__pycache__"}` exempts ALL of `c14/ui/` from the pymol/PyQt5 import ban. So `c14/ui/controller.py` COULD import `pymol.Qt` and still pass the gate — but that destroys the testability split.
**Why it happens:** the exemption exists so the QtWidgets widgets CAN import `pymol.Qt`; it's not a license to put Qt everywhere.
**How to avoid:** self-discipline: `c14/ui/controller.py` imports NEITHER pymol NOR PyQt5 (only `c14.*` domain modules + injected handles). Add a project-specific check (or a comment convention) so the controller stays pure. The `c14/ui/__init__.py` docstring already says "gate-excluded (may import pymol/PyQt5)" — the controller opts OUT of that permission for testability.
**Warning signs:** `python3.6 -c "import c14.ui.controller"` fails with `ModuleNotFoundError: No module named 'pymol'` — the controller has leaked a pymol import.

## Code Examples

### The controller's molaction_sink wiring (the testability seam)
```python
# Source: c14/engine.py:83-89,187-189 (the contract) + this research (the wiring)
# The engine constructor takes molaction_sink (a callable taking ONE MolAction).
# The controller passes ITS OWN dispatch method as the sink.
self._engine = GameEngine(
    graph,
    molaction_sink=self._dispatch_molaction,  # engine calls this per-action
    edit_router=edit_router)

def _dispatch_molaction(self, action):
    # Pure forward to molops. Unit-testable: inject MockMolOps, assert the
    # controller forwarded each MolAction the engine emitted.
    self._molops.apply(action)
```

### The 4 deferred dispatches (verbatim from FROZEN conventions — drop into molops.apply)
```python
# Source: 05.4-CONVENTION.md:125-139 (set_color/label/set) + 05.3-CONVENTION.md:240-258 (align)
# All 4 use self._cmd (already injected, molops.py:106-110) -- NO new dependency.
elif op == "set_color":
    # src: tmp/pymol-src/modules/pymol/viewing.py:2107 cmd.set_color
    self._cmd.set_color(action.args["name"], action.args["rgb"])
elif op == "label":
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label
    text = action.args.get("text", "")
    sele = action.args.get("sele", action.target)
    expr = '"{0}"'.format(text.replace('"', '\\"'))  # quoted-string footgun guard
    self._cmd.label(sele, expr)
elif op == "set":
    # src: tmp/pymol-src/modules/pymol/setting.py:183 cmd.set
    self._cmd.set(action.args["name"], action.args["value"],
                  action.args.get("sele", action.target))
elif op == "align":
    method = action.args.get("method", "super")
    reference = action.args["reference"]
    sele = action.args.get("align_sele")  # None => whole object
    mobile = action.target if sele is None else "{0} and {1}".format(action.target, sele)
    ref = reference if sele is None else "{0} and {1}".format(reference, sele)
    if method == "super":
        # src: tmp/pymol-src/modules/pymol/fitting.py:242 cmd.super  (mobile MOVED, target FIXED)
        self._cmd.super(mobile, ref)
    elif method == "align":
        # src: tmp/pymol-src/modules/pymol/fitting.py:306 cmd.align
        self._cmd.align(mobile, ref)
    elif method == "cealign":
        # src: tmp/pymol-src/modules/pymol/fitting.py:27 cmd.cealign  NOTE: (target, mobile) REVERSED
        self._cmd.cealign(ref, mobile)
    else:
        raise ValueError("molops.align: unknown method {!r}".format(method))
```

### The enzyme_id extraction (the edit-node binding — `05.1-DESIGN.md:619-623`)
```python
# Source: 05.1-DESIGN.md:619-623 (the controller extracts the enzyme_id from node tags)
def _current_enzyme_id(self):
    node = self._engine.graph.get_node(self._engine.state.current_node)
    return next((t.split(":", 2)[2] for t in node.tags
                 if t.startswith("edit:enzyme:")), None)
```

### The plugin entry point (the menu registration — packaging is the other track)
```python
# Source: bundled pymol-src/.../lightingsettings_gui/__init__.py:13-15 (verified pattern)
# + pymol/plugins/__init__.py:100 (addmenuitemqt) + :320-321 (__init_plugin__ call)
def __init_plugin__(self=None):
    from pymol import plugins
    plugins.addmenuitemqt('RPG: Tale of C', run)

def run():
    # Construct the molops stack (inject real cmd + AssetManager + EditOps +
    # ProtonationManager), the EditRouter, the Controller, the MainWindow; show it.
    # The packaging (.zip structure, install_modules) is the OTHER researcher's track.
    ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Legacy `pmgqt`/Tk plugin UI | Modern `pymol.Qt` (PyQt5) | PyMOL 2.x | `AGENTS.md` mandates `from pymol.Qt import QtCore, QtGui, QtWidgets` (matches `Pymol-script-repo/plugins/dynoplot.py:21`). NO `pmgqt`/Tk. |
| `addmenuitem` (legacy Tk) | `addmenuitemqt` (modern Qt) | PyMOL 2.x | `pymol/plugins/__init__.py:100,111`. The bundled `lightingsettings_gui` uses `addmenuitemqt`. |
| `cmd.scene` keys for scene templates | MolAction `on_enter` sequences | Phase 5.4 (`05.4-CONVENTION.md:335-343`) | `cmd.scene` is session state (LOST on save/load — no `.pse` saved). MolAction sequences replay on load. Phase 6 MAY add `cmd.scene` as a performance cache but the MolAction sequence is the source of truth. |
| Composite `op="hero_highlight"` super-op | 3 minimal peer-primitive ops (set_color/label/set) + sequences | Phase 5.4 OQ-1 (`05.4-CONVENTION.md:91-118`) | Keeps molops dispatch minimal + per-step testable + mirrors the 5.3 precedent. Phase 6 implements the 3 minimal ops. |
| `op="align"` deferred (5.3 design phase) | `op="align"` dispatch lands in Phase 6 | Phase 5.3 Q3 (`05.3-CONVENTION.md:368-371`) | The dispatch is FROZEN verbatim; Phase 6 just adds the `elif`. |
| Scoped-dim hero highlight (gray80 on non-hero) | All-C-cyan + ball-and-stick + "YOU" label (OQ-3 OVERRIDE) | Phase 5.4 OQ-3 (`05.4-CONVENTION.md:682`) | Non-carbons keep element colors (NOT dimmed). The hero is distinguished by ball-and-stick + label, NOT by dimming. The smokes were re-run with the new palette (29/29 + 37/37 PASS). |

**Deprecated/outdated:**
- `setenv.bat` / `wsl2win_cp.sh` (referenced in `spec.md` but DO NOT exist in this repo — `AGENTS.md`). Use `run-conda-pymol.bat` at `/mnt/c/src/` for headless `cmd.*` smokes.
- `pmgqt` / Tk interface (`PROJECT.md:61`). Modern `pymol.Qt` only.
- `cmd.scene` as the scene-template primitive (`05.4-CONVENTION.md:335-343`). Optional Phase 6 performance cache ONLY; MolAction sequences are the source of truth.

## Open Questions

1. **The `edit:offer` vs RNG-shuffle UI at `tca.shuffle`**
   - What we know: `tca.shuffle` has 2 weighted (turn1=0.5, turn2=0.5) + 2 non-weighted (edit:offer, cycle-trap) choices. When weighted choices are eligible, the engine's RNG picks among them; the non-weighted aren't separately player-pickable (`engine.py:121-131`).
   - What's unclear: how should the UI present this so the player can meaningfully choose "edit aconitase" vs "let the RNG spin"? `05.1-DESIGN.md:488-489` flags this as a Plan 06 UI/UX open question.
   - Recommendation: the planner resolves this explicitly — likely a "Spin" button (RNG) + a separate "Edit" button (edit:offer) + a conditional "The cycle has spun too long" button (cycle-trap, gated by visit count).

2. **The hero-selector rewrite mechanism (Pattern 3 implementation detail)**
   - What we know: the OQ-6 pre-pass rewrites the target node's `on_enter` to inject the default hero selector. The engine re-reads `node.on_enter` each `_enter`.
   - What's unclear: should the controller monkey-patch `target_node.on_enter` (mutable list, `model.py:268`) before `engine.choose`, or maintain a pending-actions queue the sink drains? The monkey-patch is simpler but mutates shared graph state (could leak across turns if not restored).
   - Recommendation: the planner picks the approach that keeps `tests/test_engine.py` green. A one-shot mutate + restore (save the original `on_enter`, swap in the resolved, restore after `_enter` completes) is safe. OR the sink-drains-pending-queue approach (no graph mutation). The sink approach is cleaner but requires the engine's per-action dispatch to consult the controller's queue — verify the engine's `for action in actions: sink(action)` (`engine.py:188`) can be intercepted by having the sink ignore the engine's actions and drain its own queue (fragile — the sink receives the engine's originals).

3. **The `pyr.branch` cond-syntax runtime fix (Pitfall 5)**
   - What we know: the skeleton's cond `"not flags.host_o2_low"` uses attribute access; the interpreter's `_cond` exposes `flags` as a dict → `AttributeError` → False → both choices hidden at runtime.
   - What's unclear: does Phase 6 fix the cond syntax (a content/skeleton change) or the interpreter's `_cond` (a code change)? STATE.md says "Phase 6 (controller) should refine to `flags.get('host_o2_low')`."
   - Recommendation: the planner verifies whether this is a skeleton-JSON fix (Phase 7 content) or a controller/interpreter fix (Phase 6). If the player can't advance past `pyr.branch` in the Phase 6 MVP, it blocks SC3 (reach a True/Bad ending). This is a Phase 6 blocker to verify.

4. **Whether the controller should call `c14.paths.selfcheck()` at startup**
   - What we know: STATE.md (`[Phase 6]` note) says "Plugin loader should also call `c14.paths.selfcheck()` at startup (Pitfall 1 mitigation — fail loud on broken bundled layout)."
   - What's unclear: is this the controller's job or the plugin_entry's job?
   - Recommendation: the plugin_entry (`__init_plugin__` / `run`) calls `c14.paths.selfcheck()` before constructing the controller (fail loud before the UI opens). This is a 1-line addition; the planner includes it in the entry-point task.

## Recommendations for the Planner

Split Phase 6 into focused plans. The UI-adapter track suggests this ordering (the packaging + persistence researchers will add their own plans):

1. **Plan 06-A: The 4 deferred molops dispatches** (the owed 5.3/5.4 work — do this FIRST; it's pure molops, no Qt, fully unit-testable + headless-smokeable).
   - Add the 4 `elif` branches to `c14/pymol_layer/molops.py` (verbatim from §Code Examples).
   - Add MockCmd unit tests in `tests/test_molops.py` for each new op (verify `cmd.set_color`/`label`/`set`/`super`/`align`/`cealign` arg order + the `align_sele` scoping composition + the label quoted-string wrapping).
   - Add a headless smoke `tools/molops_deferred_dispatch_smoke.py` (mirrors `molops_smoke.py` + `hero_highlight_smoke.py`): dispatch the 6-call hero-highlight sequence + an align via `molops.apply(MolAction(...))` and assert the same post-conditions the direct-cmd smokes proved (color-name round-trip / label text / rep visible / finite RMSD). This is the regression target proving the dispatches reproduce the smokes.
   - NO Qt. NO controller. This plan is WSL-unit-testable + headless-smokeable (no human-verify). It unblocks the controller (which needs the dispatches to exist).

2. **Plan 06-B: The Qt-free controller + HeroResolver** (the mediator, unit-testable in WSL).
   - `c14/ui/controller.py`: `Controller` class (Pattern 1) + `HeroResolver` (Pattern 3). NO QtWidgets import.
   - Unit tests `tests/test_controller.py`: inject `MockMolOps` + `MockView` + mock `prompt_fn`/`count_fn`. Assert: engine wiring (molaction_sink = controller's dispatch), `choose` calls `engine.choose` + renders, `apply_edit` builds the right `EditIntent` + reads `enzyme_id` from tags, `load` calls `engine.load`, the OQ-6 gate prompts on multi-C + no-op on single-C, the hero-selector rewrite.
   - NO Qt. WSL-unit-testable. The `c14/ui/__init__.py` already says "gate-excluded" — the controller opts OUT of importing Qt for testability.

3. **Plan 06-C: The QtWidgets main window + widgets** (human-verify — Qt can't run in WSL).
   - `c14/ui/main_window.py` (`QMainWindow` — Pattern 7) + `c14/ui/widgets.py` (`StoryPanel` Pattern 4, `ChoicePanel` Pattern 5, the edit dialog).
   - The `render_turn(turn)` method populates the story text + choice buttons from the `TurnResult`.
   - The `prompt_fn` implementation: a `QMessageBox.question` wrapper passed to the controller.
   - Human-verify: the main window opens, character select works, story text renders, choices are clickable, the edit dialog builds an EditIntent, save/load round-trips. This is SC1/SC2/SC3.
   - This plan DEPENDS on 06-A (dispatches) + 06-B (controller). It's the human-verify milestone.

4. **Plan 06-D: The plugin entry point + integration** (the `__init_plugin__` + menu registration + `c14.paths.selfcheck()`).
   - `c14/ui/plugin_entry.py` (or `c14/ui/__init__.py`): `__init_plugin__` + `addmenuitemqt` + `run` (constructs the molops stack + EditRouter + Controller + MainWindow, shows it). Calls `c14.paths.selfcheck()` first.
   - The packaging (.zip structure, `install_modules`, Plugin Manager install) is the OTHER researcher's track — coordinate so this plan's entry point matches their packaging plan.
   - Human-verify: on PyMOL restart, the "RPG: Tale of C" menu item appears (SC1).

**Cross-cutting for the planner:**
- The 4 deferred dispatches (06-A) are the ONLY owed production-code work from 5.3/5.4. They are FROZEN verbatim — no design decisions, just implementation + tests + smoke.
- The controller (06-B) is the testability linchpin: get it right and ~70% of the UI logic is WSL-unit-testable.
- The `edit:offer` vs RNG-shuffle UI (Open Question 1) + the `pyr.branch` cond fix (Open Question 3 / Pitfall 5) are Phase 6 BLOCKERS for SC3 (reach a True/Bad ending) — the planner must resolve them, not defer.
- Coordinate with the packaging researcher: the entry point (06-D) must match their packaging plan's install structure. Coordinate with the persistence/achievements researcher: the save/load (Pattern 6) + achievement board (SC5) touch the controller's `save`/`load` + a new achievements module — agree on the seam (the controller calls `engine.save`/`engine.load`; the achievements module is a separate concern the controller reads/writes).

## Sources

### Primary (HIGH confidence)
- `c14/engine.py` (read in full, 219 lines) — the turn loop + the `molaction_sink` per-action dispatch contract (`:83-89,163-194,203-213`).
- `c14/story/model.py` (read in full, 329 lines) — `MolAction`/`EditIntent`/`Node`/`Choice` data shapes + `EditIntent.signature()` (`:112-126`).
- `c14/pymol_layer/molops.py` (read in full, 205 lines) — the 11 implemented ops + the 4 deferred-op insertion point (`:112-196`).
- `c14/pymol_layer/asset_manager.py` (read in full, 127 lines) + `c14/pymol_layer/edit_ops.py` (read in full, 273 lines) + `c14/edit_router.py` (read in full, 255 lines) — the injected collaborators.
- `.planning/phases/05.4-cast-hero-representation-design/05.4-CONVENTION.md` (read in full, 766 lines, FROZEN) — the 3 new-op shapes (`:54-82`), the dispatch pseudocode (`:124-140`), the hero-highlight sequence (`:233-243`), the OQ-6 selection rule (`:171-186`), the §6.1 Phase-6 contract (`:611-617`).
- `.planning/phases/05.3-wt-aligned-structure-load-convention/05.3-CONVENTION.md` (read in full, 415 lines) — the `op="align"` shape (`:220-229`) + dispatch pseudocode (`:240-258`) + the §7.2 Phase-6 contract (`:283-288`).
- `.planning/phases/05.1-story-graph-design-glucose-skeleton-integration-contracts/05.1-DESIGN.md` — the edit-node contract (`:565-655`) + the `edit:enzyme:<id>` binding (`:607-643`) + the `tca.shuffle` UI ambiguity (`:473-489`).
- `tools/hero_highlight_smoke.py` (read in full, 444 lines) — the 6-call hero-highlight sequence proved headlessly (29/29 PASS) + the `color_name_for()` round-trip helper + the quoted-string label footguard.
- `tools/molops_smoke.py` (read in full, 180 lines) — the established molops headless-smoke pattern (the SMOKE_RESULT sentinel, the per-action dispatch, the `rep` keyword post-condition).
- `tools/check_imports.py` (read in full, 100 lines) — the AST gate `SKIP_DIRS = {"pymol_layer","ui","__pycache__"}` (`:33`) confirms `c14/ui/` is exempt.
- `tmp/pymol-src/modules/pymol/viewing.py:2107` (`set_color(name, rgb, ...)`), `:1332` (`label(selection, expression, ...)`) — verified cmd signatures.
- `tmp/pymol-src/modules/pymol/setting.py:183` (`set(name, value, selection, ...)`) — verified cmd signature.
- `tmp/pymol-src/modules/pymol/fitting.py:242` (`super(mobile, target, ..., transform=1, ...)`) — verified cmd signature + the mobile-moves/target-fixed semantics.
- `tmp/pymol-src/modules/pymol/plugins/__init__.py:100,320-321` + `tmp/pymol-src/modules/pymol/pymol_path/data/startup/lightingsettings_gui/__init__.py:13-15` — the modern `__init_plugin__` + `addmenuitemqt` entry-point pattern.
- `Pymol-script-repo/plugins/dynoplot.py:21` — the modern `from pymol.Qt import QtCore, QtGui, QtWidgets` import style (the repo convention).
- `.planning/ROADMAP.md:199-209` — the Phase 6 goal + 5 success criteria.
- `.planning/STATE.md:184` — "Next: Phase 6 (Qt UI MVP — implements the 3 deferred set_color/label/set dispatches + the 5.3 align dispatch + the OQ-6 warn+confirm Qt prompt)."

### Secondary (MEDIUM confidence)
- `tools/scene_template_smoke.py` (skimmed) — the 6 scene-type + cast-reveal + 4 ending-tier MolAction sequences proved headlessly (37/37 PASS); confirms the dispatches must reproduce these exact `cmd.*` sequences.

### Tertiary (LOW confidence)
- None. All findings trace to source code or FROZEN conventions.

## Metadata

**Confidence breakdown:**
- The 4 deferred dispatches (op names, args schema, dispatch pseudocode, cmd signatures): **HIGH** — FROZEN verbatim in 5.3/5.4 conventions + cmd signatures verified at exact `tmp/pymol-src` lines + smokes PASS.
- The controller/mediator architecture: **HIGH** — the engine's `molaction_sink` contract is read in full; the wiring is direct (sink = controller's dispatch method).
- The OQ-6 prompt separation: **MEDIUM** — the clean-separation principle (molops pure + injected prompt_fn) is sound and matches the repo's DI pattern, but the hero-selector rewrite mechanism (Open Question 2) has 2 viable implementations the planner must choose between.
- The main window layout: **MEDIUM** — the layout is a straightforward QtWidgets composition (SC1 requirements are clear), but the `edit:offer` vs RNG-shuffle UI (Open Question 1) + the `pyr.branch` cond fix (Pitfall 5) are unresolved Phase 6 blockers.
- The testability split: **HIGH** — the AST-gate exemption is verified (`check_imports.py:33`); the controller-stays-Qt-free discipline is a direct application of the repo's 3-tier pattern.

**Research date:** 2026-08-29
**Valid until:** 2026-09-29 (30 days — stable; the conventions are FROZEN, the engine/molops contracts are shipped code. The only drift risk is the 2 Open Questions the planner resolves.)
