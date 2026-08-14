# Phase 4: Editing, Protonation & Restore Safety Net — Research Track: Edit Routing (EDIT-04 / SC3)

**Researched:** 2026-08-15
**Domain:** Pure-Python domain logic — edit-intent → story-branch routing (lookup table + bad-ending fallback)
**Confidence:** HIGH (all claims verified against the built `c14/` code contract read in full, and empirically tested on `python3.6.9`)

## Summary

This track answers: *what does the planner need to know to implement the EditRouter — known-edit → defined story branch, unknown-edit → bad-ending pool — such that an executor can build it with zero interpretation?* The edit-routing model is settled (PROJECT.md Key Decisions: lookup table + bad-ending fallback; the automated chemistry-correctness engine is explicitly OUT OF SCOPE). This document fills the implementation gap: the exact `EditIntent` data shape, the `edits.json` schema + deterministic matching algorithm, the `EditRouter` API + integration into the existing `GameEngine` turn loop, the bad-ending pool mechanics (single-`RngEngine` reproducibility), the validation hook, and the pure-Python unittest that satisfies SC3.

The five highest-value findings the planner must act on:

1. **`EditIntent` is a NEW plain class, NOT a `MolAction` variant.** `MolAction` is the *execution* carrier (engine → pymol_layer, the molops dispatch unit with ops `edit`/`protonate`/`restore`). `EditIntent` is the *routing input* (player → router) and needs an `enzyme_id` lookup key that `MolAction` doesn't carry. Conflating them couples routing to execution and breaks the clean directionality of the data flow. `EditIntent` lives in `c14/story/model.py` alongside `MolAction` (pure data, 3.6-safe plain class, `from_dict`/`to_dict`/`__eq__` matching the existing precedent).
2. **Matching is EXACT dict equality on a normalized signature — zero chemistry, zero fuzzy logic.** The `EditIntent.signature()` method produces a canonical dict `{"op","target","args"}`; each `edits.json` entry authors the SAME canonical shape in its `signature` field; the router compares with `==`. Python dict equality is order-independent on 3.6.9 (empirically verified) and JSON round-trip preserves equality (verified), so signatures authored in JSON match in-memory intents. The signature is a CONTRACT between the UI (produces `EditIntent`s) and the table (authors signatures) — both use the identical normalization; the router never infers.
3. **The EditRouter lives at `c14/edit_router.py` (pure-Python domain tier, AST-gate-clean) and takes the single injected `RngEngine` per `route()` call** — matching the `StoryInterpreter` precedent (stateless across playthroughs; `rng` passed per call). Bad-ending pool selection goes through `rng.weighted_pick(pool, [1.0]*len(pool))` (uniform, reproducible). NEVER `import random` in `edit_router.py` (Anti-Pattern 7: all stochastic draws through the single seeded engine; verified same-seed reproducible).
4. **Integration = one new `GameEngine.apply_player_edit(edit_intent, enzyme_id)` method** that calls `router.route(...)` → records the edit in the EXISTING `GameState.edits_history` (via the existing `state.add_edit()` helper — do NOT hand-roll) → calls the EXISTING `self._enter(node_id)`. The routed branch/bad-ending's `on_enter` MolActions flow through the EXISTING `molaction_sink` (no new dispatch path). The edit *application* (backup + alter + sort + rebuild) is the apply_edit helper's job (the OTHER Phase 4 concern, pymol_layer) — NOT the EditRouter's. The EditRouter is pure routing: `EditIntent` in → `node_id` out.
5. **SC3 "demonstrated headlessly with fixture edit intents" = a pure-Python `tests/test_edit_router.py` unittest, NOT the `run-conda-pymol.bat` bridge.** This is the testability win: the routing logic needs no PyMOL. The fixture is a placeholder `edits.json` + a minimal story graph (start + 1 branch + 2 bad-endings) under `tests/fixtures/edit_routing/`. Phase 4 ships PLACEHOLDER content (fake enzyme ids, placeholder claim_ids); the real cited `edits.json` entries are Phase 5+ content (Phase 5.1 SC4 defines the real edit-node contract on the real skeleton).

**Primary recommendation:** Build `c14/edit_router.py` (`EditRouter` + `EditsTable` loader + `validate_edits_table`), add `EditIntent` to `c14/story/model.py`, add `GameEngine.apply_player_edit()`, and prove SC3 with `tests/test_edit_router.py` over a `tests/fixtures/edit_routing/` bundle — all pure-Python, `python3.6 -m unittest`, AST gate stays clean.

## Standard Stack

This track is pure-Python domain logic — stdlib only by mandate (AGENTS.md: assume only what `pymol-open-source` ships; the domain tier imports no pymol). No external libraries.

### Core (stdlib — all already used by the existing `c14/` code)
| Module | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `json` (stdlib) | 3.6.9 | Load `edits.json`; `EditIntent.to_dict`/`from_dict` round-trip | Already used by `c14/story/graph.py`, `c14/persist.py`. JSON is the established content format. |
| `os` (stdlib) | 3.6.9 | `os.path.join` for CWD-independent path resolution in `EditsTable.load` | Matches `StoryGraph.load(story_dir)` precedent (CWD-independent via explicit path arg). |
| `unittest` (stdlib) | 3.6.9 | `python3.6 -m unittest tests.test_edit_router` — the SC3 demo | **The only available test runner** — pytest is NOT installed (confirmed in Phase 1 research + still true). |

### Supporting (existing `c14/` modules the EditRouter REUSES — do not reimplement)
| Module | Purpose | How Reused |
|---------|---------|------------|
| `c14/story/model.py` `MolAction` | The execution carrier (op `edit`/`protonate`/`restore`) | The routed branch's `on_enter` carries `MolAction("edit",...)` for known edits (the apply_edit plan implements the molops handler). EditRouter does NOT produce MolActions — it produces a node id. |
| `c14/rng.py` `RngEngine` | The single seeded PRNG | `route(edit_intent, enzyme_id, rng)` takes it per call; `rng.weighted_pick(pool, [1.0]*len(pool))` for bad-ending selection. Verified same-seed reproducible. |
| `c14/state.py` `GameState.add_edit` / `edits_history` | Edit-history recording (already built in Phase 2) | `GameEngine.apply_player_edit` calls `state.add_edit({"enzyme":..., "intent":..., "route":...})`. Do NOT hand-roll edit history. |
| `c14/story/graph.py` `StoryGraph.all_nodes()` | The `{id: Node}` dict for cross-validation | `validate_edits_table(edits_table, graph.all_nodes())` checks every `branch_node` + pool node id exists in the graph. |
| `c14/story/validate.py` `Issue` | The validation-issue value type | New `validate_edits_table` returns `list[Issue]` with new `kind` strings (reuses the class; duck-typed on nodes). |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New `EditIntent` class | Reuse `MolAction` as the edit-intent carrier | REJECTED — `MolAction` has no `enzyme_id` field; it's the execution output (engine→molops), not the routing input (player→router). Conflating them couples routing to execution and breaks data-flow directionality. Use a separate `EditIntent`. |
| Fuzzy/signature-similarity matching | A chemistry-aware matcher (e.g. "is this residue in the active site?") | REJECTED by the settled decision — that's the chemistry engine, explicitly OUT OF SCOPE. Use exact dict equality on a normalized signature. |
| `random.choice(pool)` for bad-ending pick | The single `RngEngine` | REJECTED — Anti-Pattern 7: bypasses the seeded engine, breaks classroom repro + save/load. Use `rng.weighted_pick`. |
| Separate bad-ending graph (not story nodes) | Story-graph bad-ending nodes (Phase 2 `is_ending="bad"`) | REJECTED — the pool nodes ARE story graph nodes (Phase 2 already has `intro.ending_bad`). Referencing them by id keeps one graph and lets `interpreter.enter_node` mark the playthrough finished. |

**Installation:** NONE. Everything is stdlib or existing `c14/` modules. (Hard constraint — do not propose `pip install`.)

## Architecture Patterns

### Recommended Project Structure (additions to the existing `c14/` tree)
```
c14/
├── edit_router.py            # NEW (Phase 4). EditRouter + EditsTable + validate_edits_table.
│                             # Pure-Python domain tier (AST-gate-clean). Maps EditIntent -> node_id.
├── story/
│   └── model.py              # EXTEND (Phase 4). Add EditIntent class (plain, 3.6-safe) next to MolAction.
├── engine.py                 # EXTEND (Phase 4). Add GameEngine.apply_player_edit(edit_intent, enzyme_id).
│                             # Reuses _enter() + state.add_edit() + the existing molaction_sink.
└── ...
tests/
├── test_edit_router.py       # NEW (Phase 4). SC3 demo: known->branch, unknown->pool, RNG determinism,
│                             #   validation. Pure-Python unittest (NO run-conda-pymol.bat bridge).
└── fixtures/
    └── edit_routing/         # NEW (Phase 4). Placeholder bundle for the SC3 demo.
        ├── edits.json        # Placeholder enzyme + 1 known edit + bad_ending_pool (placeholder claim_ids).
        ├── manifest.json     # Minimal story graph: start + 1 branch + 2 bad-endings.
        └── story.json        # The nodes for ^.
data/
└── edits.json                # NOT created in Phase 4 (real cited content = Phase 5+). Phase 4 uses the
                              #   tests/fixtures/ bundle to prove the mechanics. (Optional: a placeholder
                              #   data/edits.json can mirror the fixture for an end-to-end demo, clearly
                              #   marked PLACEHOLDER.)
```

### Pattern 1: EditIntent is routing INPUT; MolAction is execution OUTPUT (directionality)
**What:** The data flow has two directions. The player's edit intent flows IN (`EditIntent` → `EditRouter` → `node_id`). The story's molecular actions flow OUT (`Node.on_enter` → `MolAction` list → `molaction_sink` → `molops.apply`). `EditIntent` and `MolAction` are DIFFERENT types crossing the boundary in opposite directions.
**When to use:** Always. Never reuse `MolAction` as the edit-intent carrier.
**Why:** `MolAction` is the molops dispatch unit (ops `edit`/`protonate`/`restore`/`show`/...). `EditIntent` needs an `enzyme_id` lookup key + a finer `op` granularity (`point_mutation`/`substrate_edit`/`protonation_change` — the EDIT-01/02/03 categories) for table matching. Conflating them would force `MolAction` to carry routing metadata it doesn't need.

### Pattern 2: EditRouter is stateless across playthroughs (mirrors StoryInterpreter)
**What:** `EditRouter(edits_table)` holds only the immutable parsed table. `route(edit_intent, enzyme_id, rng)` takes the `RngEngine` per call (the same instance the `GameEngine` owns). The router holds no per-playthrough state.
**When to use:** Always — matches the `StoryInterpreter.pick_choice(node, state, rng)` / `enter_node(node, state, rng)` precedent exactly.
**Why:** A single router instance can serve any number of playthroughs; the `rng` (the only per-playthrough stochastic unit) is explicit at the call site; save/load reproducibility follows from the engine's existing RNG-state sync (the bad-ending pick advances the same PRNG stream that's saved/restored).

### Pattern 3: The routed node's `on_enter` does the molecular work; the EditRouter only routes
**What:** `route()` returns a `node_id` (a string). The `GameEngine` then calls `_enter(node_id)`, which runs the node's `on_enter` MolActions through the EXISTING `molaction_sink` (no new dispatch path). For a KNOWN edit, the branch's `on_enter` carries `MolAction("edit", target, args)` (the canonical edit, applied via the apply_edit helper in molops — backup + alter + sort + rebuild). For an UNKNOWN edit, the bad-ending node's `on_enter` does NOT carry an edit MolAction (the edit is "unmodeled" — the bad-ending narrates; the player can restore via EDIT-05).
**When to use:** Always.
**Why:** Keeps the EditRouter pure-Python (it never applies edits, never names pymol). The edit-application concern (backup + alter + sort + the `alter`→`sort` silent-corruption trap, Pitfall 6) is the apply_edit helper's job — a SEPARATE Phase 4 plan. The EditRouter plan and the apply_edit plan are decoupled: the EditRouter is unit-testable in WSL with zero PyMOL; the apply_edit helper is headless-tested via `run-conda-pymol.bat`.

### Anti-Patterns to Avoid
- **`import random` in `edit_router.py`:** bypasses the single seeded `RngEngine` (Anti-Pattern 7), breaks classroom repro + save/load. Use the injected `rng`.
- **`import pymol` / `import pymol.cmd` in `edit_router.py`:** fails the AST gate (`tools/check_imports.py` bans `pymol`/`PyQt5` in `c14/` root). The router returns node-id STRINGS, never pymol objects.
- **Fuzzy/substring/similarity matching:** smuggles in the chemistry engine (OUT OF SCOPE). Use exact dict equality on the normalized signature.
- **Reusing `MolAction` as the edit-intent carrier:** couples routing to execution; lacks `enzyme_id`. Use a separate `EditIntent`.
- **`EditRouter` owning the `RngEngine`:** couples the router to a playthrough; breaks the stateless-interpreter precedent. Pass `rng` per `route()` call.
- **Applying the edit inside `route()`:** forces PyMOL into the domain tier. `route()` returns a string; the edit is applied by the branch's `on_enter` MolAction (molops), orchestrated by the controller.
- **A separate bad-ending graph (not story nodes):** fragments the graph; the pool nodes wouldn't get `is_ending` detection. The pool nodes ARE story graph `is_ending="bad"` nodes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Edit-history recording | A new edit-log field + append logic | `GameState.add_edit(edit_record)` + `edits_history` (already built, Phase 2) | Already exists, already saved/loaded, already bumps `counters["edits_made"]`. Reusing keeps one edit-history. |
| Bad-ending stochastic pick | `random.choice(pool)` / `random.randint` | `RngEngine.weighted_pick(pool, [1.0]*len(pool))` | Anti-Pattern 7: all draws through the single seeded engine (reproducible, save/load-safe). |
| Story-graph loading | A new loader in `edit_router.py` | `StoryGraph.load(story_dir)` + `graph.all_nodes()` (Phase 2) | Already CWD-independent, already merges manifest+files. The EditRouter cross-validates against `all_nodes()`. |
| Validation issue type | A new result class | `c14/story/validate.py` `Issue` (Phase 2) | Already has `kind`/`node_id`/`detail` + `__eq__`. Add new `kind` strings for edit-table issues. |
| Node-existence checking | `graph.get_node(id)` with try/except | `node_id in graph.all_nodes()` (`StoryGraph.__contains__` exists) | `__contains__` is built (graph.py:121). Use it for validation. |
| MolAction dispatch | A new dispatch path for edit on_enter | The EXISTING `molaction_sink` + `_enter()` | `apply_player_edit` reuses `_enter(node_id)`; the branch's on_enter flows through the same sink as every other node. |

**Key insight:** The EditRouter is a THIN lookup + fallback over EXISTING machinery. It adds: one data type (`EditIntent`), one loader (`EditsTable`), one router (`EditRouter.route`), one validator (`validate_edits_table`), one engine method (`apply_player_edit`). Everything else (graph, RNG, state, sink, interpreter, molops) is reused as-is.

## Common Pitfalls

### Pitfall 1: Matching slips into chemistry logic
**What goes wrong:** A "smart" matcher (substring on residue name, "is this in the active site", similarity scores) silently becomes the chemistry-correctness engine that was explicitly removed.
**Why it happens:** Exact matching feels brittle; developers reach for fuzzy matching to be "forgiving."
**How to avoid:** EXACT dict equality on a normalized signature. The signature is a CONTRACT: the UI produces `EditIntent`s whose `signature()` matches the table; the table author writes the identical canonical form; the router compares with `==`. No inference. If an edit doesn't EXACTLY match, it's unknown → bad-ending (by design).
**Warning signs:** `re.match` / `difflib` / Levenshtein / "contains" in `edit_router.py`; a matcher that "accepts close-enough" edits.

### Pitfall 2: Empty bad-ending pool → crash on unknown edit
**What goes wrong:** An enzyme with no per-enzyme pool + a missing/empty global pool → `route()` does `rng.weighted_pick([], [])` → `IndexError` (or `random.choices` on empty) → crash on the very first unknown edit.
**Why it happens:** The global pool is optional in the schema; an author forgets it; the table loads fine but crashes at runtime.
**How to avoid:** (a) `validate_edits_table` flags any empty pool (global + per-enzyme) at load — run it before play. (b) `route()` raises a clear `EditRoutingError("bad-ending pool is empty for enzyme {!r}")` (NOT a bare `IndexError`) if the pool is empty — defensive, fail-loud-with-context.
**Warning signs:** `IndexError` from `weighted_pick` during a playtest; a table with `"bad_ending_pool": []`.

### Pitfall 3: Non-deterministic RNG bypasses the single RngEngine
**What goes wrong:** `route()` uses `random.choice(pool)` or `random.random()` → two playthroughs with the same seed pick different bad-endings → classroom repro breaks + save/load desync (the bad-ending pick isn't part of the saved PRNG stream).
**Why it happens:** `random.choice` is the "obvious" one-liner; the developer doesn't realize the engine owns a single seeded `RngEngine` for exactly this reason.
**How to avoid:** ALL pool picks via the injected `rng` (`rng.weighted_pick(pool, [1.0]*len(pool))`). NEVER `import random` in `edit_router.py` (the AST gate doesn't ban `random`, but Anti-Pattern 7 does — enforce by review + a test that asserts same-seed reproducibility).
**Warning signs:** `import random` at the top of `edit_router.py`; a determinism test that fails.

### Pitfall 4: Dangling node refs (branch_node / pool node not in the story graph)
**What goes wrong:** `edits.json` references `branch_node: "hexokinase.h57a"` but the story graph has no such node → `engine._enter("hexokinase.h57a")` → `KeyError` at runtime (mid-playthrough).
**Why it happens:** The edits table and story graph are authored/loaded separately; a typo or a renamed node drifts.
**How to avoid:** `validate_edits_table(edits_table, graph.all_nodes())` checks EVERY `branch_node` + every pool node id exists in the graph (`node_id in nodes`). Run it at load (the `EditRouter` constructor or a `validate_edit_setup(graph, router)` call before `start()`). Returns `Issue(kind="dangling_edit_branch" / "dangling_pool_node", ...)`.
**Warning signs:** `KeyError` from `graph.get_node` during `apply_player_edit`; a validate report with dangling issues.

### Pitfall 5: AST-gate violation (`import pymol` in edit_router.py)
**What goes wrong:** `tools/check_imports.py` exits 1 → the canonical Phase-1 check command fails → CI red.
**Why it happens:** A developer reaches for `pymol.cmd` to "check the current selection" during routing, or copies a pattern from a reference plugin.
**How to avoid:** `edit_router.py` imports ONLY stdlib (`json`, `os`) + `c14` modules (`c14.story.model`, `c14.story.validate`, `c14.rng` types for docstrings — no runtime pymol). The router returns node-id STRINGS. The molecular work is in `c14/pymol_layer/` (gate-excluded), triggered by the branch's `on_enter` MolActions.
**Warning signs:** `check_imports.py` reports `edit_router.py:LINE import pymol...`.

### Pitfall 6: Signature normalization breaks replay determinism
**What goes wrong:** The same `EditIntent` produces different signatures across runs (e.g. dict-key-order-dependent serialization, float formatting) → same intent → different route → non-reproducible.
**Why it happens:** Using `str(dict)` (order-dependent on 3.6 impl-detail) or float comparison in the signature.
**How to avoid:** The signature is a plain dict compared with `==` (Python dict equality is order-independent on 3.6.9 — empirically verified). All signature values are STRINGS (selectors lowercased/trimmed per a fixed rule; no floats). The `EditIntent.signature()` method is pure + deterministic. JSON round-trip preserves equality (verified).
**Warning signs:** A determinism test (`same intent + same seed → same route`) fails intermittently.

### Pitfall 7: Pool nodes not marked `is_ending="bad"`
**What goes wrong:** A pool node is a non-ending story node → `interpreter.enter_node` doesn't call `state.mark_finished` → the player reaches a "bad ending" but the game doesn't end → stuck with no choices.
**Why it happens:** The author adds a pool node but forgets `is_ending`.
**How to avoid:** `validate_edits_table` checks every pool node `is_ending == "bad"` (duck-typed via the existing `_is_ending` helper). Returns `Issue(kind="pool_node_not_ending", ...)`.
**Warning signs:** A playthrough reaches a pool node but `state.finished` stays `None`.

### Pitfall 8: Conflating "player applies edit" with "branch applies edit" (double-edit / backup corruption)
**What goes wrong:** The player manually mutates a residue in PyMOL, THEN the branch's `on_enter` re-applies `MolAction("edit",...)` → the apply_edit helper backs up the ALREADY-MUTATED state (wrong backup) → restore restores the mutated state, not the pre-edit state.
**Why it happens:** Ambiguity over whether the EditIntent IS the edit (player did it) or TRIGGERS the edit (branch does it canonically).
**How to avoid:** RECOMMEND: the player's `EditIntent` is a CHOICE (the UI offers modeled edits; the player selects one), NOT a free-form PyMOL mutation. The branch's `on_enter` applies the canonical edit (via `MolAction("edit",...)` → apply_edit helper → backup PRE-edit state → alter → sort → rebuild). The backup is then clean. Free-form edits (not in the table) → bad-ending (no edit applied; the player can restore). This makes "limited edits" truly limited (modeled only) and the backup deterministic. Flag the final decision for the Phase 5.1 edit-node contract (SC4) — but Phase 4's mechanics support this cleanly.
**Warning signs:** Restore after a known edit returns the mutated state, not the pre-edit state.

## Data Schemas

### `EditIntent` (new, in `c14/story/model.py`) — plain class, 3.6-safe

```python
# Source: c14/story/model.py (EXTEND, matching the MolAction/Choice/Node precedent)
class EditIntent(object):
    """A player's edit intent — the routing INPUT (player -> EditRouter).

    Pure data, like MolAction, but a SEPARATE type: MolAction is the execution
    carrier (engine -> molops); EditIntent is the routing carrier (player ->
    router) and carries the enzyme_id lookup key MolAction lacks.

    Attributes:
        op: edit category. One of "point_mutation" | "substrate_edit" |
            "protonation_change" (the EDIT-01/02/03 categories -- FINER than
            MolAction's single "edit" op, because the lookup table matches on
            these categories).
        target: residue/atom selector or object name (e.g. "resi 57 and chain A"
            for a point mutation; "substrate" for a substrate edit). Matched
            verbatim against the table signature after normalization.
        args: op-specific parameters (e.g. {"new_res": "ALA"} for a point
            mutation; {"group": "-OH", "action": "add"} for a substrate edit;
            {"resn": "HIP"} for a protonation change). Defaults to {}.
        enzyme_id: the enzyme/substrate context id for lookup (e.g.
            "hexokinase" or "pdb:1TNR"). The current story node determines this
            (Phase 5.1 edit-node contract); the controller passes it.
    """
    def __init__(self, op, target=None, args=None, enzyme_id=None):
        self.op = op
        self.target = target
        self.args = args if args is not None else {}
        self.enzyme_id = enzyme_id

    def signature(self):
        """Return the canonical match dict: {"op","target","args"}.

        Deterministic: target is whitespace-stripped + lowercased; args values
        are stringified; keys are the raw op/target/args (no enzyme_id -- the
        enzyme_id is the lookup BUCKET, not part of the per-edit signature).
        Compared with == against edits.json "signature" entries (dict equality
        is order-independent on 3.6.9 -- verified).
        """
        return {
            "op": self.op,
            "target": (self.target or "").strip().lower(),
            "args": {k: _norm_val(v) for k, v in (self.args or {}).items()},
        }

    # from_dict / to_dict / __eq__ / __repr__ matching the MolAction precedent
```

**Normalization rules (FIXED, deterministic, no chemistry):**
- `op`: verbatim string (must be one of the 3 categories).
- `target`: `.strip().lower()` (selectors are case-insensitive in practice for resi/chain; lowercasing is safe + deterministic). Author the table signature in the same lowercased form.
- `args`: each value stringified via `_norm_val` (`str(v).strip()` for scalars; for nested dicts/lists, `json.dumps(v, sort_keys=True)`). Keys verbatim.
- `enzyme_id`: NOT part of the signature — it's the lookup BUCKET (which enzyme's edits to search). Two edits on different enzymes with the same op/target/args are DIFFERENT routes (different buckets).

**How the player's edit becomes an EditIntent:** Phase 6 UI constructs it (from the mutagenesis wizard / edit panel — the player's selection maps to op/target/args/enzyme_id). Phase 4 defines the CONTRACT (the class + constructor); Phase 4's fixtures construct `EditIntent`s directly in tests. Phase 5.1 SC4 specifies which story nodes allow edits + what EditIntent each player-edit-action generates.

### `edits.json` schema (the lookup table)

```json
{
  "version": 1,
  "bad_ending_pool": ["bad.lost_connection", "bad.released_from_host"],
  "enzymes": {
    "hexokinase": {
      "edits": [
        {
          "signature": {"op": "point_mutation", "target": "resi 57 and chain a", "args": {"new_res": "ALA"}},
          "branch_node": "hexokinase.h57a_branch",
          "claim_id": "edit-hexokinase-h57a"
        }
      ],
      "bad_ending_pool": ["bad.hexokinase_broken"]
    }
  }
}
```

**Field semantics:**
- `version` (int): schema version (forward-compat, like `manifest.json`'s `version`).
- `bad_ending_pool` (list[str], top-level): the GLOBAL fallback pool. Used when (a) `enzyme_id` is not in `enzymes` at all, OR (b) the enzyme has no per-enzyme `bad_ending_pool`. Every id MUST exist in the story graph + be `is_ending="bad"` (validated).
- `enzymes` (dict): per-enzyme lookup. Key = `enzyme_id` (matches the `EditIntent.enzyme_id` + the cast registry's enzyme ids — the SHARED manifest for SC5).
- `enzymes[id].edits` (list): the known edits. Each entry:
  - `signature` (dict): the canonical match key (IDENTICAL shape to `EditIntent.signature()`). Compared with `==`.
  - `branch_node` (str): the story graph node id to route to on match. MUST exist in the graph (validated).
  - `claim_id` (str): the citation claim backing this edit (Phase 5+ real content; Phase 4 fixtures use `"placeholder-..."` claim_ids).
- `enzymes[id].bad_ending_pool` (list[str], optional): per-enzyme pool OVERRIDE. If present + non-empty, used for THIS enzyme's unknown edits (the global pool is NOT merged — override semantics, simpler + deterministic). If absent/empty, fall back to the global pool.

**Matching algorithm (deterministic, no fuzzy/chemistry) — the EXACT `route()` logic:**
```
route(edit_intent, enzyme_id, rng) -> node_id:
  1. sig = edit_intent.signature()
  2. enzyme = table["enzymes"].get(enzyme_id)
  3. if enzyme is not None:
       for entry in enzyme["edits"]:
         if entry["signature"] == sig:           # EXACT dict equality
           return entry["branch_node"]            # KNOWN -> branch
  4. # unknown (no enzyme, or no matching signature) -> bad-ending pool
  5. pool = (enzyme.get("bad_ending_pool") if enzyme else None)
  6. if not pool: pool = table["bad_ending_pool"]  # global fallback
  7. if not pool: raise EditRoutingError(...)      # Pitfall 2: fail loud
  8. return rng.weighted_pick(pool, [1.0]*len(pool))  # uniform, reproducible
```

**Coexistence with the story graph:** `edits.json` is a SEPARATE file, loaded by a SEPARATE loader (`EditsTable.load(path)`), NOT part of `manifest.json`'s `files` list (those are story-node files). The two are CROSS-VALIDATED: every `branch_node` + every pool node id in `edits.json` must exist in `graph.all_nodes()`. The `StoryGraph.load(story_dir)` is UNCHANGED. This keeps the story graph clean (nodes only) and the edit table clean (routing only); the cross-reference is by node-id STRING.

### Bad-ending pool structure
- **Location:** in `edits.json` (global `bad_ending_pool` + optional per-enzyme `bad_ending_pool`).
- **Contents:** node-id STRINGS referencing story graph nodes with `is_ending="bad"`.
- **Phase 2 coordination:** Phase 2 already has `intro.ending_bad` (`is_ending="bad"`). Phase 4 fixtures add `bad.lost_connection` + `bad.released_from_host` (`is_ending="bad"`) to the fixture story graph — these are the spec's "lost connection" / "released from host" bad endings (PROJECT.md Key Decisions). The EditRouter references them by id.
- **Selection:** uniform via `rng.weighted_pick(pool, [1.0]*len(pool))`. Reproducible (same seed → same pick — verified for `RngEngine.weighted_pick`). Per-enzyme pool overrides global; empty per-enzyme → global fallback; both empty → `EditRoutingError` (validated against at load).

## API Signatures

### `c14/edit_router.py` (NEW)

```python
class EditRoutingError(Exception):
    """Raised when edit routing cannot proceed (e.g. empty bad-ending pool)."""


class EditsTable(object):
    """The parsed edits.json lookup table (immutable data)."""
    def __init__(self, table):
        # type: (dict) -> None
        self._table = table

    @classmethod
    def load(cls, edits_path):
        # type: (str) -> EditsTable
        """Load + json.load edits.json from edits_path (CWD-independent)."""
        ...

    @property
    def global_pool(self):
        # type: () -> list
        ...

    def enzyme(self, enzyme_id):
        # type: (str) -> dict or None
        ...

    def to_dict(self):
        # type: () -> dict
        ...


class EditRouter(object):
    """Routes an EditIntent to a story node id (known -> branch; unknown -> pool).

    Stateless across playthroughs (mirrors StoryInterpreter): holds only the
    immutable EditsTable; the RngEngine is passed per route() call.
    """
    def __init__(self, edits_table):
        # type: (EditsTable) -> None
        self._table = edits_table

    def route(self, edit_intent, enzyme_id, rng):
        # type: (EditIntent, str, RngEngine) -> str
        """Return the node id to enter (a branch_node for known edits; a
        bad-ending pool node for unknown edits). Raises EditRoutingError if
        the bad-ending pool is empty (Pitfall 2)."""
        ...

    def bad_ending_pool(self, enzyme_id):
        # type: (str) -> list
        """Return the effective pool for enzyme_id (per-enzyme override, else
        global). Empty list if both are empty (callers/validators check)."""
        ...


def validate_edits_table(edits_table, story_nodes):
    # type: (EditsTable, dict) -> list
    """Cross-validate an EditsTable against a {id: Node} story graph.

    Returns a list of c14.story.validate.Issue (empty = valid). Checks:
      - dangling_edit_branch:   a branch_node not in story_nodes.
      - dangling_pool_node:     a pool node id not in story_nodes.
      - empty_bad_ending_pool:  the global pool OR a per-enzyme pool is empty.
      - pool_node_not_ending:   a pool node exists but is_ending != "bad".
      - duplicate_signature:    two edits in one enzyme share a signature.
    Duck-types on story_nodes (Node objects OR raw dicts) via the existing
    _is_ending helper.
    """
    ...


def scan_edit_coverage(edits_table, cast_enzyme_ids):
    # type: (EditsTable, list) -> list
    """SC5 helper: every cast enzyme has >=1 known-edit entry. Returns a list
    of Issue(kind="missing_edit_coverage", node_id=<enzyme_id>) for enzymes in
    cast_enzyme_ids with no edits entry. (Phase 4: green on placeholder cast;
    Phase 9+: green on the real cast.) The SHARED manifest = enzyme_id keys in
    edits.json MUST match the cast registry's enzyme ids.
    """
    ...
```

### `c14/engine.py` (EXTEND — one new method)

```python
class GameEngine(object):
    def __init__(self, graph, molaction_sink=None, edit_router=None):
        # EXTEND: optional edit_router (None = edit-routing disabled; start/choose
        # still work for non-edit playthroughs). Backward-compatible default.
        self.graph = graph
        self.interpreter = StoryInterpreter()
        self.molaction_sink = molaction_sink
        self.edit_router = edit_router        # NEW
        self.state = None
        self.rng = None

    def apply_player_edit(self, edit_intent, enzyme_id):
        # type: (EditIntent, str) -> TurnResult
        """Route a player edit + enter the routed node (the SC3 entry point).

        1. node_id = self.edit_router.route(edit_intent, enzyme_id, self.rng)
        2. self.state.add_edit({                            # reuse existing helper
               "enzyme": enzyme_id,
               "intent": edit_intent.to_dict(),
               "route": node_id,
           })
        3. return self._enter(node_id)   # reuse existing _enter (on_enter -> sink)

        The edit APPLICATION (backup + alter + sort + rebuild) is NOT done here
        -- it's the apply_edit helper's job (pymol_layer), triggered by the
        routed branch's on_enter MolAction("edit",...). This method is pure
        routing + entry; it stays WSL-unit-testable (no PyMOL).

        Raises RuntimeError if no edit_router was injected. Raises
        EditRoutingError if the bad-ending pool is empty.
        """
        if self.edit_router is None:
            raise RuntimeError("GameEngine has no edit_router; cannot apply edits")
        node_id = self.edit_router.route(edit_intent, enzyme_id, self.rng)
        self.state.add_edit({
            "enzyme": enzyme_id,
            "intent": edit_intent.to_dict(),
            "route": node_id,
        })
        return self._enter(node_id)
```

**Backward compatibility:** `edit_router=None` default keeps every existing Phase 2 test green (the constructor signature widens with a defaulted arg; `start`/`choose`/`save`/`load` are unchanged). The new method is purely additive.

## Proposed Design

### The EditRouter class + matching algorithm (reference implementation)

```python
# Source: c14/edit_router.py (NEW, pure-Python, AST-gate-clean)
# Verified patterns: dict == order-independent (3.6.9), RngEngine.weighted_pick
# same-seed reproducible, json round-trip preserves dict equality.
import json
import os

from c14.story.model import EditIntent
from c14.story.validate import Issue, _is_ending


class EditRoutingError(Exception):
    pass


class EditsTable(object):
    def __init__(self, table):
        self._table = table

    @classmethod
    def load(cls, edits_path):
        with open(edits_path, "r", encoding="utf-8") as fh:
            return cls(json.load(fh))

    @property
    def global_pool(self):
        return list(self._table.get("bad_ending_pool", []))

    def enzyme(self, enzyme_id):
        return self._table.get("enzymes", {}).get(enzyme_id)

    def to_dict(self):
        return self._table


class EditRouter(object):
    def __init__(self, edits_table):
        self._table = edits_table

    def route(self, edit_intent, enzyme_id, rng):
        sig = edit_intent.signature()
        enzyme = self._table.enzyme(enzyme_id)
        if enzyme is not None:
            for entry in enzyme.get("edits", []):
                if entry.get("signature") == sig:        # EXACT dict equality
                    return entry["branch_node"]           # KNOWN -> branch
        pool = self.bad_ending_pool(enzyme_id)
        if not pool:
            raise EditRoutingError(
                "bad-ending pool is empty for enzyme {!r} (no per-enzyme pool "
                "and no/empty global pool)".format(enzyme_id))
        return rng.weighted_pick(list(pool), [1.0] * len(pool))  # uniform, reproducible

    def bad_ending_pool(self, enzyme_id):
        enzyme = self._table.enzyme(enzyme_id)
        if enzyme is not None:
            per = enzyme.get("bad_ending_pool")
            if per:                                      # per-enzyme override
                return list(per)
        return self._table.global_pool                   # global fallback


def validate_edits_table(edits_table, story_nodes):
    issues = []
    table = edits_table.to_dict()
    # Global pool checks
    gpool = table.get("bad_ending_pool", [])
    issues.extend(_check_pool(gpool, "global", story_nodes))
    # Per-enzyme checks
    for eid, e in table.get("enzymes", {}).items():
        per_pool = e.get("bad_ending_pool", [])
        issues.extend(_check_pool(per_pool, eid, story_nodes))
        seen = set()
        for entry in e.get("edits", []):
            bn = entry.get("branch_node")
            if bn is not None and bn not in story_nodes:
                issues.append(Issue("dangling_edit_branch", bn,
                                    detail="enzyme {} branch_node".format(eid)))
            sig = json.dumps(entry.get("signature", {}), sort_keys=True)
            if sig in seen:
                issues.append(Issue("duplicate_signature", eid,
                                    detail="signature {}".format(sig)))
            seen.add(sig)
    return issues


def _check_pool(pool, label, story_nodes):
    out = []
    if not pool:
        out.append(Issue("empty_bad_ending_pool", label))
    for nid in pool:
        if nid not in story_nodes:
            out.append(Issue("dangling_pool_node", nid, detail="pool {}".format(label)))
        elif not _is_ending(story_nodes[nid]):
            out.append(Issue("pool_node_not_ending", nid, detail="pool {}".format(label)))
    return out
```

### Integration data flow (the full edit turn)

```
Player selects a modeled edit (Phase 6 UI)
  -> controller builds EditIntent(op, target, args, enzyme_id)
  -> controller calls engine.apply_player_edit(edit_intent, enzyme_id)
       1. engine.edit_router.route(edit_intent, enzyme_id, engine.rng) -> node_id
            (KNOWN: signature match -> branch_node; UNKNOWN: rng.weighted_pick(pool))
       2. engine.state.add_edit({"enzyme":..,"intent":..,"route":node_id})  # reuse
       3. engine._enter(node_id)                                            # reuse
            -> interpreter.enter_node(node, state, rng) -> on_enter MolActions
            -> state.rng_state = rng.get_state()                            # RNG sync (reuse)
            -> for action in actions: molaction_sink(action)                # reuse (sink)
       4. returns TurnResult(node, molactions, eligible_choices)
  -> controller dispatches the TurnResult.molactions to molops.apply(action) per action
       (KNOWN branch's on_enter includes MolAction("edit",..) -> apply_edit helper:
        backup PRE-edit state -> alter -> sort -> rebuild. UNKNOWN/bad-ending on_enter
        has NO edit MolAction -> the bad-ending narrates; player can restore via EDIT-05.)
```

**Phase 4 SC3 demo (headless, NO PyMOL):** steps 1-4 run with a MOCK sink (`list.append`) — proving routing + entry + RNG determinism. The `molops.apply` step (the apply_edit helper) is NOT exercised by SC3 (it's the apply_edit plan's headless smoke). SC3 = pure-Python routing only.

### Validation hook (load-time safety)
Before `engine.start()` (or right after constructing the `EditRouter`), call:
```python
issues = validate_edits_table(router._table, graph.all_nodes())
if issues: raise ValueError("edits table invalid: {}".format(issues))
```
This catches dangling node refs, empty pools, non-ending pool nodes, and duplicate signatures BEFORE any playthrough. It reuses the `Issue` type + the `_is_ending` duck-typed helper (works on `Node` objects from `graph.all_nodes()`).

## Test Strategy

### SC3 demo: `tests/test_edit_router.py` (pure-Python, `python3.6 -m unittest`)

**Fixture bundle** under `tests/fixtures/edit_routing/`:

`edits.json` (PLACEHOLDER — clearly marked, no real science):
```json
{
  "version": 1,
  "bad_ending_pool": ["bad.lost_connection", "bad.released_from_host"],
  "enzymes": {
    "placeholder_enzyme": {
      "edits": [
        {
          "signature": {"op": "point_mutation", "target": "resi 57 and chain a", "args": {"new_res": "ALA"}},
          "branch_node": "edit.placeholder_branch",
          "claim_id": "placeholder-edit-1"
        }
      ]
    }
  }
}
```

`manifest.json`:
```json
{"version": 1, "default_seed": 0, "start": "edit.start", "files": ["story.json"]}
```

`story.json` (minimal: start + 1 branch + 2 bad-endings):
```json
{
  "nodes": {
    "edit.start": {
      "text_dramatic": "You stand before a placeholder enzyme.",
      "claim_ids": ["placeholder-start"],
      "on_enter": [{"op": "hide_all"}],
      "choices": []
    },
    "edit.placeholder_branch": {
      "text_dramatic": "Your modeled edit takes effect.",
      "claim_ids": ["placeholder-edit-1"],
      "on_enter": [{"op": "edit", "target": "resi 57 and chain A", "args": {"new_res": "ALA"}}],
      "is_ending": "good",
      "choices": []
    },
    "bad.lost_connection": {
      "text_dramatic": "Lost connection to the host.",
      "claim_ids": ["placeholder-bad-lost"],
      "on_enter": [{"op": "hide_all"}],
      "is_ending": "bad",
      "choices": []
    },
    "bad.released_from_host": {
      "text_dramatic": "Released from the host.",
      "claim_ids": ["placeholder-bad-released"],
      "on_enter": [{"op": "hide_all"}],
      "is_ending": "bad",
      "choices": []
    }
  }
}
```

**Tests (each maps to an SC3 sub-claim):**
```python
class TestEditRouter(unittest.TestCase):
    # a) KNOWN edit -> defined branch
    def test_known_edit_routes_to_branch(self):
        router = EditRouter(EditsTable.load(fixture_edits_path))
        intent = EditIntent("point_mutation", "resi 57 and chain A",
                            {"new_res": "ALA"}, "placeholder_enzyme")
        node_id = router.route(intent, "placeholder_enzyme", RngEngine(0))
        self.assertEqual(node_id, "edit.placeholder_branch")  # SC3 (known -> branch)

    # b) UNKNOWN edit -> bad-ending pool
    def test_unknown_edit_routes_to_bad_ending_pool(self):
        router = EditRouter(EditsTable.load(fixture_edits_path))
        intent = EditIntent("point_mutation", "resi 999",
                            {"new_res": "TRP"}, "placeholder_enzyme")  # not in table
        node_id = router.route(intent, "placeholder_enzyme", RngEngine(0))
        self.assertIn(node_id, ["bad.lost_connection", "bad.released_from_host"])  # SC3

    # c) RNG determinism (same seed -> same bad-ending pick)
    def test_rng_determinism_same_seed_same_pool_pick(self):
        intent = EditIntent("point_mutation", "resi 999", {"new_res": "TRP"}, "placeholder_enzyme")
        r1 = EditRouter(EditsTable.load(p)).route(intent, "placeholder_enzyme", RngEngine(42))
        r2 = EditRouter(EditsTable.load(p)).route(intent, "placeholder_enzyme", RngEngine(42))
        self.assertEqual(r1, r2)  # reproducible
        # different seed -> (likely) different pick (statistical, not strict)
        r3 = EditRouter(EditsTable.load(p)).route(intent, "placeholder_enzyme", RngEngine(7))
        # don't assert r1 != r3 (could collide); assert both are valid pool members
        self.assertIn(r3, ["bad.lost_connection", "bad.released_from_host"])

    # d) unknown ENZYME (not in table) -> global pool
    def test_unknown_enzyme_falls_through_to_global_pool(self):
        router = EditRouter(EditsTable.load(p))
        intent = EditIntent("point_mutation", "resi 57", {"new_res": "ALA"}, "no_such_enzyme")
        node_id = router.route(intent, "no_such_enzyme", RngEngine(0))
        self.assertIn(node_id, ["bad.lost_connection", "bad.released_from_host"])

    # e) empty pool -> EditRoutingError (Pitfall 2, fail-loud)
    def test_empty_pool_raises_edit_routing_error(self):
        bad_table = EditsTable({"version":1, "bad_ending_pool": [], "enzymes":{}})
        router = EditRouter(bad_table)
        with self.assertRaises(EditRoutingError):
            router.route(EditIntent("point_mutation","x",{},"e"), "e", RngEngine(0))

    # f) validation: dangling branch_node / pool_node / empty pool / non-ending pool / duplicate sig
    def test_validate_edits_table_dangling_branch(self): ...
    def test_validate_edits_table_dangling_pool_node(self): ...
    def test_validate_edits_table_empty_pool(self): ...
    def test_validate_edits_table_pool_node_not_ending(self): ...
    def test_validate_edits_table_duplicate_signature(self): ...
    def test_validate_edits_table_clean(self): ...  # the fixture bundle -> []

class TestGameEngineEditIntegration(unittest.TestCase):
    # The full SC3 end-to-end: apply_player_edit routes + enters the node +
    # emits on_enter MolActions to the sink (pure-Python, NO PyMOL).
    def test_apply_player_edit_known_enters_branch_emits_on_enter(self):
        graph = StoryGraph.load(fixture_story_dir)
        sink = []
        router = EditRouter(EditsTable.load(fixture_edits_path))
        eng = GameEngine(graph, molaction_sink=sink.append, edit_router=router)
        eng.start("glucose", 0)
        intent = EditIntent("point_mutation", "resi 57 and chain A",
                            {"new_res": "ALA"}, "placeholder_enzyme")
        tr = eng.apply_player_edit(intent, "placeholder_enzyme")
        self.assertEqual(tr.node.id, "edit.placeholder_branch")
        self.assertTrue(any(a.op == "edit" for a in tr.molactions))  # branch on_enter has the edit
        self.assertEqual(len(eng.state.edits_history), 1)            # add_edit recorded it
        self.assertTrue(eng.state.finished)                          # branch is_ending="good"

    def test_apply_player_edit_unknown_enters_bad_ending(self):
        eng = _make_engine(seed=42)
        intent = EditIntent("point_mutation", "resi 999", {"new_res":"TRP"}, "placeholder_enzyme")
        tr = eng.apply_player_edit(intent, "placeholder_enzyme")
        self.assertIn(tr.node.id, ["bad.lost_connection", "bad.released_from_host"])
        self.assertEqual(eng.state.ending_tier, "bad")

    def test_apply_player_edit_rng_reproducible(self):
        # two engines, same seed, same unknown intent -> same bad-ending node
        ...
```

**Run command (the SC3 evidence):**
```bash
python3.6 tools/check_imports.py && python3.6 -m unittest tests.test_edit_router -v
```
(Plus the full suite still passes: `python3.6 -m unittest discover -s tests` — the new tests are additive; existing 123 tests stay green.)

## Phase 4 Boundary (fixture placeholders now vs real cited edits.json Phase 5+)

| Aspect | Phase 4 (THIS research) | Phase 5+ (out of scope) |
|--------|------------------------|-------------------------|
| `edits.json` content | PLACEHOLDER fixture (`tests/fixtures/edit_routing/edits.json`) — fake `placeholder_enzyme`, placeholder `claim_id`s. Proves the routing MECHANICS end-to-end. | Real `data/edits.json` with real enzyme ids, real signatures, real `claim_id`s (each human-approved per CITE-01). |
| `EditIntent` content | Contract defined (op/target/args/enzyme_id + signature()). Fixtures construct intents directly. | Phase 5.1 SC4 specifies which story nodes allow edits + what EditIntent each player-edit-action generates (the edit-node contract). Phase 6 UI constructs intents from the player's selection. |
| Bad-ending pool | Placeholder `bad.lost_connection` / `bad.released_from_host` (spec framing) in the fixture graph. | Real bad-ending nodes in the real glucose skeleton (Phase 5.1/7), with explanatory teaching-layer text (Phase 10 SC3: "not punitive"). |
| `claim_id`s | `"placeholder-..."` (not cited). | Real claim_ids, each passing the citation gate (Phase 7+). |
| Edit application | NOT in this research (the apply_edit helper is a separate Phase 4 plan). SC3 proves ROUTING only (mock sink). | The apply_edit helper (backup + alter + sort + rebuild) + molops `edit`/`protonate`/`restore` handlers (Phase 4, separate plan) + ProtonationManager (Phase 4 SC4). |
| SC5 (per-enzyme min-coverage) | `scan_edit_coverage` function DEFINED; green on placeholder cast. | Green on the real ~20+ cast (Phase 9 SC2). The SHARED manifest = `enzyme_id` keys in edits.json match the cast registry. |

**Citation-gate boundary (explicit):** Phase 4 builds routing MECHANICS + fixture edit intents (placeholder enzymes/edits/claims). NO real cited content lands in Phase 4. The real `edits.json` entries (with `claim_id`s for real enzyme edits) are Phase 5+ content, each passing the per-claim checkpoint (CITE-01). The `claim_id` field EXISTS in the Phase 4 schema (forward-compat) but holds `"placeholder-..."` values.

## Open Questions

1. **Does the branch RE-APPLY the edit canonically, or trust the player's manual edit?**
   - What we know: The EditRouter is pure routing (returns a node id). The edit application is the apply_edit helper's job (pymol_layer). The branch's `on_enter` MAY carry `MolAction("edit",...)` (canonical re-apply) or may not (trust the player's manual edit).
   - Recommendation: **Branch re-applies canonically** (the player's `EditIntent` is a CHOICE among modeled edits, not a free-form PyMOL mutation; the UI offers modeled edits). This keeps the backup clean (apply_edit backs up the PRE-edit state) and the scene deterministic + cited. Flag for the Phase 5.1 edit-node contract (SC4) to finalize.
   - Phase 4 impact: NONE on the EditRouter (it routes regardless). The Phase 4 apply_edit plan + the fixture branch's `on_enter` choose; the fixture above uses the canonical-re-apply form.

2. **Should `enzyme_id` come from the current node's metadata (e.g. a `tags` entry like `"enzyme:hexokinase"`) or be passed explicitly by the controller?**
   - What we know: The controller (Phase 6) knows the current node + its enzyme context. Phase 5.1 SC4 specifies which nodes allow edits + their enzyme_id.
   - Recommendation: The controller passes `enzyme_id` explicitly to `apply_player_edit` (derived from the current node's metadata). The EditRouter doesn't read node metadata (keeps it pure). Phase 5.1 defines the node→enzyme_id mapping.
   - Phase 4 impact: NONE — the fixture passes `enzyme_id` directly.

3. **Per-enzyme pool: override or merge with global?**
   - Recommendation: **Override** (simpler, deterministic). If a per-enzyme pool is present + non-empty, use it; else fall back to global. (Merge would need de-duplication + ordering rules — unnecessary complexity for v1.)
   - Phase 4 impact: The `route()` algorithm above implements override semantics.

## Sources

### Primary (HIGH confidence — code-read + empirically verified)
- **`c14/story/model.py`** (read in full): `MolAction`(op/target/args, `from_dict`/`to_dict`/`__eq__`), `Choice`, `Node` — the plain-class + `from_dict`/`to_dict` precedent `EditIntent` follows. MolAction ops include `edit`/`protonate`/`restore` (the molops dispatch keys).
- **`c14/story/graph.py`** (read in full): `StoryGraph.load(story_dir)` (manifest + merge, CWD-independent), `all_nodes()` → `{id: Node}`, `__contains__` (line 121) — the cross-validation target.
- **`c14/story/interpreter.py`** (read in full): `StoryInterpreter.pick_choice(node, state, rng)` / `enter_node(node, state, rng, record_visit)` — the stateless + rng-per-call precedent `EditRouter` mirrors. `_cond` restricted-eval pattern.
- **`c14/story/validate.py`** (read in full): `Issue`(kind/node_id/detail), `validate_graph`, `check_reachability`, `_is_ending` duck-typed helper, `collect_claim_ids` — the `validate_edits_table` reuses `Issue` + `_is_ending`.
- **`c14/engine.py`** (read in full): `GameEngine.__init__(graph, molaction_sink)`, `start`/`choose`/`_enter(node_id, record_visit)`/`save`/`load` — the `_enter` + `molaction_sink` reuse path for `apply_player_edit`.
- **`c14/rng.py`** (read in full): `RngEngine.random()` / `weighted_pick(items, weights)` / `from_state` — the single injected PRNG for bad-ending picks.
- **`c14/state.py`** (read in full): `GameState.edits_history`, `add_edit(edit_record)`, `counters["edits_made"]` (already built) — reused for edit-history recording.
- **`c14/pymol_layer/molops.py`** (read in full): `MolOps.apply(action)` per-action dispatch; `edit`/`protonate`/`restore` raise `NotImplementedError` (explicit Phase 4 boundary — the apply_edit plan replaces these).
- **`tools/check_imports.py`** (read in full): AST gate, `SKIP_DIRS={"pymol_layer","ui","__pycache__"}`, `BANNED_TOP=("pymol","PyQt5")`, dynamic-import review. `c14/edit_router.py` must pass (imports only `json`/`os` + `c14.*`).
- **`python3.6` (3.6.9) empirical probes** (run 2026-08-15): dict `==` order-independent ✓; JSON round-trip preserves dict equality ✓; `random.Random.choices` reproducible ✓; `RngEngine.weighted_pick` + `random()` same-seed reproducible ✓; `dataclasses` BANNED ✓. Baseline: 123 tests pass, AST gate clean.

### Secondary (MEDIUM confidence — planning docs)
- `.planning/PROJECT.md` Key Decisions: edit-routing = lookup table + bad-ending fallback (settled); bad-ending pool = "lost connection" / "released from host".
- `.planning/REQUIREMENTS.md` EDIT-04: edit routing uses a lookup table; unknown → bad-ending pool.
- `.planning/ROADMAP.md` Phase 4 SC3 (verbatim): "EditRouter routes a known edit (matching an `edits.json` entry) to its defined story branch, and routes an unknown edit to the bad-ending pool — demonstrated headlessly with fixture edit intents." Phase 5.1 SC4: the edit-node contract (downstream).
- `.planning/research/SUMMARY.md`: planned `c14/edit_router.py` (pure-Python domain) + `data/edits.json`; P10 (define "known edit" categories + per-enzyme minimum coverage + bad-endings explanatory not punitive).
- `spec.md` §1 (bad ending): "if a player make change to an important residue in the enzyme breaking the important pathway and the host cannot survive." §4 (limited edits + restore for smooth gameplay).
- `data/story/manifest.json` + `intro.json` (read in full): the existing story-graph fixture shape (manifest + nodes-with-on_enter + `is_ending="bad"` node) the Phase 4 fixture mirrors.

### Tertiary (LOW confidence)
- None. All findings are code-read or empirically verified.

## Metadata

**Confidence breakdown:**
- Standard stack (stdlib + reuse): **HIGH** — code-read + empirically verified.
- Architecture (EditRouter location, stateless pattern, integration via `_enter`+`add_edit`): **HIGH** — code-read; the integration reuses existing methods verbatim.
- Data schemas (`EditIntent` + `edits.json` + matching algorithm): **HIGH** — verified dict-equality + JSON round-trip on 3.6.9; the algorithm is fully specified above.
- Pitfalls: **HIGH** — each verified against the code contract (AST gate, RngEngine, GameState, validate) or empirically.
- Phase 4 boundary (placeholder vs real content): **HIGH** — ROADMAP + REQUIREMENTS explicit.

**Research date:** 2026-08-15
**Valid until:** 2027-02-15 (stable — the `c14/` code contract is built + read in full; the only drift risk is if the planner chooses a different `EditIntent` shape, which this research prescribes against).

**Decisions the planner must make (flagged):**
1. Confirm `EditIntent` is a new plain class in `c14/story/model.py` (recommend: YES — separate from `MolAction`).
2. Confirm matching = exact dict equality on `signature()` (recommend: YES — no fuzzy/chemistry).
3. Confirm bad-ending pool pick via `rng.weighted_pick` (recommend: YES — Anti-Pattern 7).
4. Confirm per-enzyme pool = override (not merge) (recommend: YES — simpler).
5. Confirm the branch re-applies the edit canonically (Open Question 1) (recommend: YES — flag for Phase 5.1 SC4 to finalize; Phase 4 mechanics support it either way).
6. Confirm `GameEngine.__init__` gains an optional `edit_router=None` (recommend: YES — backward-compatible).
7. Confirm the SC3 fixture lives in `tests/fixtures/edit_routing/` (recommend: YES — keeps `data/` for real Phase 5+ content).
