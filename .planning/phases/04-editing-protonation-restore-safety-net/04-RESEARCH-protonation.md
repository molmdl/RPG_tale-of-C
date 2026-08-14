# Phase 4: Editing, Protonation & Restore Safety Net — ProtonationManager Research

**Researched:** 2026-08-15
**Domain:** PyMOL 2.5.0 `cmd.h_add` / `cmd.alter` / `cmd.remove` / `cmd.sort` / `cmd.rebuild` API surface for curated-variant protonation (NO pH engine); 3-tier testability; sanctioned-alter gate coordination; backup/restore safety net integration
**Confidence:** HIGH — every `cmd.*` signature below was read against `tmp/pymol-src/modules/pymol/` (file:line pinned to PyMOL 2.5.0); the `h_add` valence-only behavior is confirmed by its own docstring; the absence of `cmd.h_remove` and of any bundled propka/pKa/pH module was verified by exhaustive grep of `tmp/pymol-src/modules/pymol/`. The curated-variant *model* and the sanctioned-alter coordination are design recommendations (MEDIUM — depend on the editing-safety researcher's `edit_ops.py` contract landing in the same wave).

## Summary

Phase 4 Protonation is **mechanics, not chemistry**. The settled decision (CAST-03, PROJECT.md) is that the game ships **curated protonation variants** — NOT a pH/pKa engine. This research confirms the underlying PyMOL reality that forces that decision: `cmd.h_add` (`editing.py:1216`) is **explicitly valence-only** ("adds hydrogens onto a molecule based on current valences" — its own docstring), there is **NO `cmd.h_remove`** in PyMOL 2.5.0 (use `cmd.remove` `editing.py:800` with an H-targeted selection), and there is **NO bundled propka/pKa/pH module** (exhaustive grep of `tmp/pymol-src/modules/pymol/` returned nothing for `propka|pka|pH|protonat` except the unrelated `pkat` mouse-action keyword in `controlling.py`). So physiological-pH protonation MUST be achieved either by (a) loading a pre-built correctly-protonated structure, or (b) `cmd.alter` resn-rename to a protonation-state variant + targeted `cmd.h_add`/`cmd.remove` of specific atoms — exactly as CAST-03 specifies.

Two modes are required and both are reachable with the verified API. **Mode (a) load pre-built**: `AssetManager.load_bundled` (already built, Phase 3) loads a curated `.pdb` whose residues already carry the desired protonation; replace the current object via `cmd.delete` (`commanding.py:496`) + `load_bundled`. **Mode (b) alter + targeted H ops**: the canonical PyMOL idiom is `cmd.h_add(sele); cmd.sort(sele + " extend 1")` (verified at `menu.py:751` — PyMOL's own "add hydrogens" menu item does exactly this); for resn rename, `cmd.alter(sele, "resn='HID'")` (`editing.py:1424`) **requires** `cmd.sort` afterward (the `alter` docstring at `editing.py:1457-1460` warns: "You should always issue a `sort` command on an object after modifying any property which might affect canonical atom ordering") and `cmd.rebuild` (`viewing.py:1791`) to refresh geometry.

**Sanctioned-alter coordination (SC1):** RECOMMEND ProtonationManager routes ALL its `cmd.alter` (resn rename) AND its `cmd.h_add` (which needs `sort`+`rebuild`) THROUGH `edit_ops.py`'s sanctioned helper — keeping the alter gate allowlist at **exactly ONE module** (`edit_ops.py`). This is cleaner than allowlisting two modules because (1) it keeps the gate trivial, (2) it guarantees `sort`+`rebuild`+`backup` run for every protonation change (not just every edit), and (3) protonation IS an edit (EDIT-03 classifies it as such) so it belongs in the edit pipeline. ProtonationManager lives at `c14/pymol_layer/protonation.py` (gate-exempt `pymol_layer/`), holds the variant→ops dispatch + the curate-variant lookup, but **delegates the actual `cmd.alter`/`cmd.h_add`/`cmd.sort`/`cmd.rebuild` calls to `edit_ops.py`** so the sanctioned-alter site stays singular and the backup/restore safety net (EDIT-05) covers protonation changes automatically.

**Primary recommendation:** Build `c14/pymol_layer/protonation.py` (`ProtonationManager` — variant dispatch + catalog lookup + mode-a/b routing + switch state) + `c14/protonation_catalog.py` (pure-data variant table, AST-gate-clean domain tier) + a new histidine-containing bundled fixture (`c14/data/assets/bundled/_his_smoke.pdb`) for the headless smoke. ProtonationManager calls `edit_ops.apply_edit(...)` (or a shared `_sanctioned_alter` helper) for every variant application so the alter gate, sort+rebuild, and backup are all guaranteed. Phase 4 ships the MECHANICS + a placeholder HID/HIE/HIP histidine example; the real per-enzyme curated variant sets (with claim_ids) are Phase 5+ content approval (CITE-01).

---

## standard_stack

### Core PyMOL 2.5.0 APIs (verified, file:line pinned)

| API | file:line | Signature | Purpose in ProtonationManager |
|-----|-----------|----------|-------------------------------|
| `cmd.h_add` | `tmp/pymol-src/modules/pymol/editing.py:1216` | `h_add(selection="(all)", quiet=1, state=0, legacy=0, _self=cmd)` | Add H atoms to satisfy current valence. **Valence-only, NOT pH-aware** (confirmed by docstring line 1220: "adds hydrogens onto a molecule based on current valences"; line 1234-1236 notes PDB files lack bond valences for ligands). Mode (b) H-add step. |
| `cmd.h_fill` | `tmp/pymol-src/modules/pymol/editing.py:1163` | `h_fill(quiet=1, _self=cmd)` | Remove/replace H on the **picked** atom only (not selection-based). Niche — use only for picked-atom fix-ups; NOT the general H-add path. |
| `cmd.h_fix` | `tmp/pymol-src/modules/pymol/editing.py:1195` | `h_fix(selection="", quiet=1, _self=cmd)` | **UNSUPPORTED** (docstring line 1199: "unsupported command that may have something to do with repositioning hydrogen atoms"). DO NOT USE. |
| `cmd.remove` | `tmp/pymol-src/modules/pymol/editing.py:800` | `remove(selection, quiet=1, _self=cmd)` | Remove atoms by selection. **This is the "h_remove"** — there is NO `cmd.h_remove` in PyMOL 2.5.0 (grep-confirmed). Target specific H atoms via selection e.g. `cmd.remove("resn HID and name HD1")`. Mode (b) H-remove step. |
| `cmd.alter` | `tmp/pymol-src/modules/pymol/editing.py:1424` | `alter(selection, expression, quiet=1, space=None, _self=cmd)` | Change atomic properties via a Python expression per atom. **Resn rename**: `cmd.alter("resi 123 and chain A", "resn='HID'")`. Alterable symbols (line 1446-1449): `name, resn, resi, resv, chain, segi, elem, ...`. **REQUIRES `cmd.sort` afterward** (warning at line 1457-1460). |
| `cmd.sort` | `tmp/pymol-src/modules/pymol/editing.py:1257` | `sort(object="", _self=cmd)` | Reorder atoms after `alter` changes names/resn/etc. **MANDATORY after `alter`** (alter docstring line 1457-1460); also idiomatic after `h_add` (`menu.py:751`). |
| `cmd.rebuild` | `tmp/pymol-src/modules/pymol/viewing.py:1791` | `rebuild(selection='all', representation='everything', *, _self=cmd)` | Force PyMOL to recreate geometry. Run after alter+h_add so representations refresh. |
| `cmd.iterate` | `tmp/pymol-src/modules/pymol/editing.py:1490` | `iterate(selection, expression, quiet=1, space=None, _self=cmd)` | Read-only traversal per atom (cannot mutate). Used to **verify** post-protonation state: `cmd.iterate("resi 123", "stored.append(resn)")` to confirm resn changed; `cmd.iterate("resn HID and name HD1", "stored.append(name)")` to confirm H present. (Also: `cmd.iterate` accepts a Python callback in 2.5 — line 1512-1515.) |
| `cmd.count_atoms` | `tmp/pymol-src/modules/pymol/querying.py:1412` | `count_atoms(selection="(all)", quiet=1, state=ALL_STATES, domain='', *, _self=cmd)` | Post-condition: H count after protonation. `cmd.count_atoms("resi 123 and elem H")` to verify H added/removed. The Phase 3 SMOKE pattern uses `count_atoms` for all post-conditions. |
| `cmd.create` | `tmp/pymol-src/modules/pymol/creating.py:960` | `create(name, selection, source_state=0, target_state=0, discrete=0, zoom=-1, quiet=1, singletons=0, extract=None, copy_properties=False, _self=cmd)` | **Backup**: `cmd.create(backup_name, object_name)` with default args = **all-states copy** (Phase 3 empirically confirmed — `1,1` drops multi-state, default args are the safe backup). Used by `apply_edit` for the EDIT-05 restore safety net. |
| `cmd.delete` | `tmp/pymol-src/modules/pymol/commanding.py:496` | `delete(name, _self=cmd)` | Delete an object. **Restore sequence** = `cmd.delete(obj)` THEN `cmd.create(obj, backup)` (delete first — creating into an existing name MERGES; Phase 3 empirically corrected). Also the Mode-(a) object-replace step. |

### Supporting (already built, reuse)

| Module | Purpose | Reuse point |
|--------|---------|-------------|
| `c14/pymol_layer/asset_manager.py` (Phase 3) | `AssetManager.load_bundled(filename, object)` resolves a bundled `.pdb` cwd-independently and asserts non-empty. | Mode (a) load pre-built protonated structure. `load_bundled` is the entry point. |
| `c14/pymol_layer/molops.py` (Phase 3) | `MolOps.apply(MolAction)` per-action dispatch. The `protonate` branch currently `raise NotImplementedError` (line 118-119) — **THIS IS THE PHASE 4 BOUNDARY**. Implement the branch to delegate to `ProtonationManager`. | Story-graph `on_enter` protonation MolActions route through `molops.apply` → `ProtonationManager.apply_variant`. |
| `c14/story/model.py` (Phase 2) | `MolAction(op, target, args)` pure-data carrier. | `MolAction("protonate", target, {"variant_id": "HIS_HID"})` for story-graph; direct `ProtonationManager.switch_variant(target, vid)` for Phase 6 UI. |
| `tools/check_imports.py` (Phase 1) | AST gate bans pymol/PyQt5 in `c14/` root; `SKIP_DIRS = {"pymol_layer", "ui", "__pycache__}`. | `c14/pymol_layer/protonation.py` is exempt (lives in `pymol_layer/`); `c14/protonation_catalog.py` (pure-data) MUST stay in `c14/` root with NO pymol import. |
| `tools/run_headless.sh` (Phase 3) | WSL→Windows headless bridge; `SMOKE_RESULT:` stdout sentinel (NOT `$?` — the bat always returns 0). | Protonation smoke harness: `bash tools/run_headless.sh tools/protonation_smoke.py`. |
| `tools/molops_smoke.py` (Phase 3) | Reference SMOKE harness pattern: `pymol.finish_launching()`; `check(name, ok, detail)`; `SMOKE_RESULT: PASS|FAIL` sentinel; `?obj` prefix for deleted-object `count_atoms`. | Copy this structure verbatim for `tools/protonation_smoke.py`. |

### Alternatives Considered (and REJECTED per settled decisions)

| Instead of | Could Use | Tradeoff / Why REJECTED |
|------------|-----------|-------------------------|
| Curated variants | PropKa / PDB2PQR / a pKa engine | REJECTED by CAST-03 + PROJECT.md. No new deps (spec.md); no bundled propka in PyMOL 2.5.0 (grep-confirmed); pKa calculation is a cited-scientific-claim minefield (CITE-01). Curated variants sidestep all of it. |
| `cmd.h_add` for physiological pH | A pH-aware H-add | **Does not exist** in PyMOL 2.5.0. `h_add` is valence-only (docstring-confirmed). This is the pitfall that forces curated variants. |
| `cmd.h_fix` / `cmd.h_fill` for general H ops | — | `h_fix` is unsupported (docstring line 1199); `h_fill` is picked-atom-only (line 1167). Neither is the general path. Use `h_add` + `remove`. |

### Installation

**NO new packages.** Everything is `pymol-open-source` (PyMOL 2.5.0 ships `cmd.h_add`, `cmd.alter`, `cmd.remove`, `cmd.sort`, `cmd.rebuild`, `cmd.iterate`, `cmd.count_atoms`, `cmd.create`, `cmd.delete`) + stdlib (`json` for the catalog, `os` for paths). Python 3.6 syntax only (no `@dataclass`, no walrus — matches Phase 1/2/3 precedent).

---

## architecture_patterns

### Recommended Project Structure (Phase 4 additions)

```
c14/
├── protonation_catalog.py      # NEW — pure-data variant table (domain tier, AST-gate-clean)
│                                #   {residue_key: {variant_id: {mode, resn, h_ops, claim_id, ...}}}
│                                #   NO pymol import. Unit-tested in tests/test_protonation_catalog.py.
├── pymol_layer/                 # (gate-exempt — pymol imports OK here)
│   ├── asset_manager.py         # existing (Phase 3) — Mode (a) load pre-built
│   ├── molops.py                # existing (Phase 3) — add `protonate` branch -> delegate to ProtonationManager
│   ├── edit_ops.py              # NEW (editing-safety researcher's plan) — sanctioned alter + apply_edit + backup
│   └── protonation.py           # NEW — ProtonationManager: variant dispatch + switch state + mode-a/b routing
│                                #   DELEGATES cmd.alter/cmd.h_add/cmd.sort/cmd.rebuild to edit_ops.apply_edit
├── data/assets/bundled/
│   ├── _smoke.pdb               # existing (ethanol, 3 atoms — NOT histidine)
│   └── _his_smoke.pdb           # NEW — minimal histidine fixture for the protonation smoke (placeholder example)
└── tests/
    ├── test_protonation_catalog.py  # NEW — pure-Python: catalog schema, variant lookup, missing-variant errors
    └── test_protonation_manager.py  # NEW — pure-Python: MockCmd dispatch mapping, switch state, reversibility
tools/
├── check_alter_gate.py          # NEW (editing-safety) — AST gate: cmd.alter allowed in exactly ONE module
└── protonation_smoke.py          # NEW — headless smoke: load HIS fixture -> backup -> HID -> HIE -> restore
```

### Pattern 1: 3-Tier Testability (inject cmd) — REUSE Phase 3 precedent

**What:** `ProtonationManager.__init__(self, cmd, edit_ops, catalog, assets)` injects `cmd`, the `edit_ops` sanctioned-helper, the pure-data `catalog`, and the `AssetManager`. NO module-top `import pymol`. The dispatch/switch-state/routing logic is unit-testable in pure WSL python3.6 with a `MockCmd`/`MockEditOps`/`MockCatalog`/`MockAssets` (mirrors `MolOps` + `AssetManager` Phase 3 pattern exactly).

**When to use:** ALWAYS for `c14/pymol_layer/` modules (the gate-exempt tier). The domain tier (`c14/protonation_catalog.py`) stays pure-data with no injection.

**Example:**
```python
# c14/pymol_layer/protonation.py — ProtonationManager (gate-exempt tier)
# Inject cmd + edit_ops + catalog + assets so dispatch is unit-testable with mocks.
class ProtonationManager(object):
    def __init__(self, cmd, edit_ops, catalog, assets):
        self._cmd = cmd              # the real pymol.cmd (or MockCmd in unit tests)
        self._edit = edit_ops        # edit_ops.apply_edit — the ONE sanctioned-alter site
        self._catalog = catalog      # c14.protonation_catalog — pure data
        self._assets = assets        # AssetManager (Mode a)
        self._current = {}           # target -> variant_id (switch state)

    def apply_variant(self, target, variant_id):
        spec = self._catalog.lookup(target, variant_id)  # pure-data lookup
        if spec["mode"] == "load":
            return self._apply_load(target, spec)
        return self._apply_alter(target, spec)  # routes through edit_ops.apply_edit
```

### Pattern 2: Catalog Split — pure-data domain tier vs cmd-calling pymol_layer tier

**What:** The variant CATALOG (residue → list of variants, each with mode/resn/h_ops/claim_id) lives in `c14/protonation_catalog.py` — pure Python, stdlib only, NO `pymol` import (passes the AST gate). The ProtonationManager (which calls `cmd.*`) lives in `c14/pymol_layer/protonation.py` (gate-exempt). The catalog is a lookup table; the manager is the dispatch.

**Why:** The catalog is the *data* (which variants exist, which claim_id backs each — Phase 5 approval attaches here); the manager is the *mechanism* (how to apply a variant via cmd.*). Splitting them keeps the catalog unit-testable in pure WSL and keeps the claim_id audit trail in the domain tier (where CITE-01 lives).

**Example catalog schema:**
```python
# c14/protonation_catalog.py — pure data, NO pymol import (AST-gate-clean)
# Schema: CATALOG[residue_key][variant_id] = {
#     "mode": "load" | "alter",      # Mode (a) load pre-built | Mode (b) alter resn + h_ops
#     "resn": "<new resn>",          # Mode (b): the new residue name (e.g. "HID")
#     "h_ops": [                     # Mode (b): ordered H add/remove ops on specific atoms
#         {"op": "remove", "selection": "<atom selection>"},
#         {"op": "add", "selection": "<atom selection>"},
#     ],
#     "source_file": "<bundled .pdb>",# Mode (a): the pre-built structure filename
#     "claim_id": "<cite id>",       # CITE-01: backs the physiological-pH/reaction-relevance claim
#     "label": "<human label>",      # for the UI switch (Phase 6)
# }
CATALOG = {
    # PLACEHOLDER EXAMPLE — standard histidine tautomer nomenclature (AMBER), NOT a cited claim.
    # The reaction-relevant tautomer PER ENZYME is a Phase 5+ cited claim (CITE-01).
    "HIS": {
        "HIS_HID": {
            "mode": "alter", "resn": "HID",
            "h_ops": [
                {"op": "remove", "selection": "resn HIS and name HE2"},
                {"op": "add", "selection": "resn HID and name ND1"},
            ],
            "claim_id": "PLACEHOLDER_PHASE5",  # real claim_id Phase 5+
            "label": "Histidine — δ-protonated (Nδ-H, Nε-free)",
        },
        "HIS_HIE": {
            "mode": "alter", "resn": "HIE",
            "h_ops": [
                {"op": "remove", "selection": "resn HIS and name HD1"},
                {"op": "add", "selection": "resn HIE and name NE2"},
            ],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Histidine — ε-protonated (Nε-H, Nδ-free)",
        },
        "HIS_HIP": {
            "mode": "alter", "resn": "HIP",
            "h_ops": [
                {"op": "add", "selection": "resn HIP and name ND1"},
                {"op": "add", "selection": "resn HIP and name NE2"},
            ],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Histidine — doubly protonated (cationic, both N-H)",
        },
    },
    # ... ASP/GLU/LYS/CYS/TYR placeholder entries follow the same schema ...
}

def lookup(residue_key, variant_id):
    """Return the variant spec dict. Raise KeyError with a clear message if missing."""
    group = CATALOG.get(residue_key)
    if group is None:
        raise KeyError("protonation_catalog: unknown residue {!r}".format(residue_key))
    spec = group.get(variant_id)
    if spec is None:
        raise KeyError("protonation_catalog: unknown variant {!r} for residue {!r}".format(
            variant_id, residue_key))
    return spec

def variants_for(residue_key):
    """Return a list of (variant_id, label) pairs available for a residue."""
    group = CATALOG.get(residue_key, {})
    return [(vid, s.get("label", vid)) for vid, s in group.items()]
```

### Pattern 3: Sanctioned-Alter Coordination — route THROUGH edit_ops (RECOMMENDED)

**What:** `ProtonationManager` does NOT call `cmd.alter` or `cmd.h_add` directly. It calls `edit_ops.apply_edit(target, edit_spec)` (or a shared `_sanctioned_alter` helper) which is the **single** module where `cmd.alter` is allowed. The alter gate (`tools/check_alter_gate.py`) allowlists exactly ONE module: `edit_ops.py`.

**RECOMMENDED: ONE module (edit_ops.py).** Reasons:
1. **Gate stays trivial.** A one-module allowlist is a single string check; a two-module allowlist is a set check that invites creep ("just add one more").
2. **sort+rebuild guaranteed for protonation too.** `cmd.h_add` needs `cmd.sort` afterward (the `menu.py:751` idiom `h_add; sort`) and `cmd.alter` needs `sort`+`rebuild` (alter docstring `editing.py:1457-1460`). Routing H-placement through `edit_ops.apply_edit` guarantees these run for protonation, not just for point mutations.
3. **Backup/restore covers protonation automatically (EDIT-05).** `apply_edit` takes a backup via `cmd.create(backup, obj)` (default args = all-states copy) BEFORE any alter. So every protonation variant change is automatically restorable via the same safety net as point mutations. Protonation IS an edit (EDIT-03) — it belongs in the edit pipeline.
4. **Single alter site = single audit point.** When a future reviewer asks "where does the code mutate `resn`?", the answer is "edit_ops.py, and only there."

**The gate rule (state for the editing-safety researcher):**
```
tools/check_alter_gate.py:
  ALLOWLIST = {"c14/pymol_layer/edit_ops.py"}   # EXACTLY ONE module
  # ProtonationManager (c14/pymol_layer/protonation.py) calls edit_ops.apply_edit,
  # NOT cmd.alter directly. So protonation.py is NOT in the allowlist.
```

**Coordination requirement (state for planner):** The editing-safety researcher's `edit_ops.py` MUST expose an entry point that ProtonationManager can call for a **multi-step protonation edit** (resn rename + targeted h_add + targeted remove + sort + rebuild, all under one backup). Proposed signature (coordinate this with the editing-safety plan — it is their contract to expose):
```python
# c14/pymol_layer/edit_ops.py — the editing-safety researcher's module
def apply_edit(target, edit_steps, backup_name=None):
    """Apply a sequence of edit steps to `target` under a single backup.

    edit_steps: list of dicts, each {"op": "alter"|"h_add"|"remove", ...}
                — ProtonationManager passes the variant's [alter] + h_ops as steps.
    backup_name: if None, auto-generated as f"_bak_{target}"; the backup is a
                 default-args cmd.create (all-states copy).
    Returns: backup_name (so ProtonationManager can track it for switch-reversal).
    Contract: cmd.create(backup, target) -> for step: dispatch -> cmd.sort -> cmd.rebuild.
    """
```

### Anti-Patterns to Avoid

- **Anti-pattern: ProtonationManager calls `cmd.alter` directly.** Violates the sanctioned-alter gate (SC1). Route through `edit_ops.apply_edit`.
- **Anti-pattern: ProtonationManager calls `cmd.h_add` without `cmd.sort`.** `h_add` changes atom count/order; the `menu.py:751` idiom is `h_add; sort`. Omitting sort confounds subsequent `byres`/`create` ops (alter docstring `editing.py:1457-1460`). Route through `edit_ops.apply_edit` which guarantees sort.
- **Anti-pattern: Two-module alter allowlist (edit_ops.py + protonation.py).** Invites creep; loses the "protonation IS an edit" unification. Keep it ONE module.
- **Anti-pattern: ProtonationManager takes its own backup (bypasses apply_edit's backup).** Either protonation is double-backed-up (wasteful) or the restore safety net doesn't know about it (EDIT-05 leak). Route through `apply_edit` so the backup is unified.
- **Anti-pattern: `cmd.create(obj, obj, 1, 1)` self-copy for backup.** Phase 3 empirically corrected: `1,1` drops multi-state; self-copy is destructive. Use default-args `cmd.create(backup, obj)` (all-states copy).
- **Anti-pattern: Restore by `cmd.create(obj, backup)` without `cmd.delete(obj)` first.** Creating into an existing name MERGES (Phase 3 empirically corrected). Restore = `cmd.delete(obj)` THEN `cmd.create(obj, backup)`.
- **Anti-pattern: Fabricate pKa values / cite papers in Phase 4.** CITE-01 violation. Phase 4 ships MECHANICS + placeholder `claim_id="PLACEHOLDER_PHASE5"`. Real curated sets are Phase 5+.
- **Anti-pattern: Compute "which tautomer" by pH.** There is no pH engine (settled). The variant is chosen by the curated catalog (Phase 5+ content) or by the user (the switch). ProtonationManager only APPLIES a chosen variant.
- **Anti-pattern: Bare `count_atoms(obj)` after `cmd.delete(obj)`.** RAISES (Phase 3 empirically confirmed). Use the `?` prefix: `count_atoms("?obj") == 0`.

---

## dont_hand_roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Add H atoms to satisfy valence | Custom valence calculator | `cmd.h_add(sele)` (`editing.py:1216`) | PyMOL's C-level `_cmd.h_add` reads bond orders + geometry; a Python reimplementation would be slower and wrong on edge cases. |
| Remove specific H atoms | Custom atom-removal loop | `cmd.remove(sele)` (`editing.py:800`) with an H-targeted selection | `cmd.remove` is the C-level remover; there is NO `cmd.h_remove` (grep-confirmed), so `cmd.remove("resn HID and name HD1")` IS the h-remove primitive. |
| Rename a residue (resn) | Custom PDB rewriting | `cmd.alter(sele, "resn='HID'")` (`editing.py:1424`) + `cmd.sort` (`editing.py:1257`) + `cmd.rebuild` (`viewing.py:1791`) | `alter` mutates in-place; the sort+rebuild is mandatory (alter docstring warning). Hand-rolling a PDB rewrite loses PyMOL's object state. |
| Backup before an edit | Manual `cmd.create` calls scattered | `edit_ops.apply_edit(target, steps)` — takes the backup internally | Centralizes the backup at the sanctioned-alter site; ProtonationManager doesn't reimplement backup. |
| Restore an edit | Manual delete+create scattered | `edit_ops.restore(target, backup_name)` (or the same `apply_edit` with a restore flag) | Centralizes the delete-then-create restore sequence (Phase 3 corrected: delete FIRST). |
| pKa / pH-based protonation | A pKa engine, PropKa, PDB2PQR | The curated `c14/protonation_catalog.py` table | REJECTED by CAST-03 + PROJECT.md. No new deps (spec.md); no bundled propka (grep-confirmed); pKa calc is a CITE-01 minefield. The catalog is the curated, human-approved source of truth. |
| Decide which tautomer is "reaction-relevant" | A rule engine / heuristics | The catalog's `claim_id` (Phase 5+ content approval) | The reaction-relevant choice PER ENZYME is a cited scientific claim (CITE-01). No engine — just a human-approved table entry. |
| Verify post-protonation state | Custom PDB parsing | `cmd.iterate` (`editing.py:1490`) + `cmd.count_atoms` (`querying.py:1412`) | `iterate` reads resn/name/elem per atom in PyMOL's state; `count_atoms` is the post-condition primitive (Phase 3 precedent). |

**Key insight:** ProtonationManager is a **thin dispatcher**, not a chemistry engine. It looks up a variant in the pure-data catalog, hands the ops to `edit_ops.apply_edit` (which does the backup + alter + h_add + sort + rebuild), and tracks the switch state. The "science" lives in the catalog's `claim_id` (Phase 5+); the "mechanics" live in `edit_ops` + `cmd.*`. ProtonationManager itself does almost no computation — it routes.

---

## common_pitfalls

### Pitfall 1: `cmd.h_add` is VALENCE-ONLY, NOT pH-aware (THE settled-decision trigger)
**What goes wrong:** A developer assumes `cmd.h_add` produces physiological-pH protonation. It does not — it adds H to satisfy current valence (geometry + bond orders), with no pH/pKa model. Applying `h_add` to a histidine gives a valence-satisfied tautomer, NOT the physiologically-relevant one.
**Why it happens:** The function name suggests "add the right hydrogens." The docstring (`editing.py:1220`) says "adds hydrogens onto a molecule based on current valences" — valence, not pH. There is no pH/pKa module bundled (grep-confirmed: no propka, no pka, no pH module in `tmp/pymol-src/modules/pymol/`).
**How to avoid:** This is exactly why CAST-03 mandates CURATED VARIANTS. ProtonationManager never relies on `h_add` alone for "physiological" protonation — it either loads a pre-built correctly-protonated structure (Mode a) or `alter`s resn to a named tautomer + does TARGETED `h_add`/`remove` of specific atoms (Mode b). The variant (HID vs HIE vs HIP) is chosen by the CATALOG, not computed.
**Warning signs:** A smoke that just calls `cmd.h_add("all")` and asserts "H count == X" without asserting resn == the expected tautomer. The H count can be right while the tautomer is wrong.

### Pitfall 2: Over-protonation after `alter` resn-rename (valence changed)
**What goes wrong:** `cmd.alter(sele, "resn='HID'")` renames the residue but does NOT add/remove atoms. A subsequent `cmd.h_add("resn HID")` then adds H to satisfy HID's valence — which may DOUBLE-add an H that was already there (if the original HIS already had it) or add to the wrong nitrogen.
**Why it happens:** `alter` changes the resn label only; the atom set is unchanged. `h_add` recomputes valence from the new resn's bond template, which can disagree with the existing H atoms.
**How to avoid:** Mode (b) MUST follow the ordered sequence: (1) `cmd.remove` the specific H atoms that should NOT be present in the target tautomer (e.g. `remove("resn HIS and name HE2")` before becoming HID); (2) `cmd.alter(sele, "resn='HID'")`; (3) `cmd.sort`; (4) targeted `cmd.h_add` on the specific atom that should gain an H (e.g. `h_add("resn HID and name ND1")`); (5) `cmd.sort` again; (6) `cmd.rebuild`. The catalog's `h_ops` list encodes this order explicitly (remove before alter, add after). **Verify with `count_atoms("resn HID and elem H")` — assert the EXACT expected H count, not just "> 0".**
**Warning signs:** H count after protonation is HIGHER than the tautomer's expected count. Always assert the exact count per tautomer (HID=1 H on ring, HIE=1 H on ring, HIP=2 H on ring — standard nomenclature, see residue_nomenclature).

### Pitfall 3: Missing `cmd.sort` after `alter` / `h_add` (confounds downstream ops)
**What goes wrong:** After `cmd.alter` (resn rename) or `cmd.h_add` (atom count change), subsequent `byres` / `create` / `iterate` selections return wrong atoms because the canonical atom ordering is stale.
**Why it happens:** `alter` docstring (`editing.py:1457-1460`) explicitly warns: "You should always issue a `sort` command on an object after modifying any property which might affect canonical atom ordering (names, chains, etc.). Failure to do so will confound subsequent `create` and `byres` operations." The `menu.py:751` idiom confirms `h_add` also needs `sort` (`h_add; sort`).
**How to avoid:** Route ALL alter/h_add through `edit_ops.apply_edit`, which guarantees `cmd.sort` after every alter/h_add step and `cmd.rebuild` at the end. ProtonationManager never calls `cmd.alter` or `cmd.h_add` directly, so this can't be forgotten.
**Warning signs:** A `byres` selection after protonation returns the wrong residue, or `cmd.iterate` reports a stale resn. Always `sort` then re-`iterate`.

### Pitfall 4: Non-reversible protonation switch (EDIT-05 leak)
**What goes wrong:** The user switches HIS_HID → HIS_HIE, then tries to switch back to HIS_HID, but the second switch doesn't fully undo the first (leftover H, wrong resn) because no backup was taken before the switch.
**Why it happens:** Each variant change is itself an edit. If ProtonationManager applies a variant without a backup, the restore safety net (EDIT-05) doesn't cover it — the user can't "reveal correct 3D model" after a protonation switch.
**How to avoid:** Route every `apply_variant` through `edit_ops.apply_edit`, which takes a backup (default-args `cmd.create`) BEFORE the alter/h_ops. Track the backup name per target so the switch is reversible: `switch_variant(target, new_vid)` → `apply_edit(target, new_steps, backup_name=self._backup[target])` (or a fresh backup each switch — coordinate with editing-safety). The switch state (`self._current[target]`) tracks the active variant; restoring = `edit_ops.restore(target, backup)`.
**Warning signs:** After switch A → B → A, `count_atoms("resn HID and elem H")` != the original count. Always assert round-trip equality in the smoke.

### Pitfall 5: Fabricating pKa values or citing papers in Phase 4 (CITE-01 violation)
**What goes wrong:** A developer, trying to make the placeholder "feel real," adds a pKa value (e.g. "HIS pKa ~6.0") or a citation (e.g. "doi:...") to the catalog. This is fabricated science — unapproved.
**Why it happens:** The temptation to fill content gaps with plausible-sounding chemistry (PROJECT.md calls this out as the temptation to resist).
**How to avoid:** Phase 4 catalog entries use `claim_id="PLACEHOLDER_PHASE5"` and the standard nomenclature label ONLY (e.g. "Histidine — δ-protonated"). NO pKa numbers, NO DOIs, NO "reaction-relevant for enzyme X" claims. The reaction-relevant choice PER ENZYME is Phase 5+ content approval (CITE-01). The residue_nomenclature section below marks exactly what is "standard nomenclature" (not a claim) vs what needs Phase 5 approval.
**Warning signs:** A catalog entry with a real `claim_id` (not `PLACEHOLDER_PHASE5`), a pKa number, or a "this is the active-site tautomer for PDB X" comment. All of these belong in Phase 5+.

### Pitfall 6: `cmd.create(obj, obj, 1, 1)` self-copy for backup (DESTRUCTIVE)
**What goes wrong:** A backup via `cmd.create(backup, obj, 1, 1)` drops multi-state data; a `cmd.create(obj, obj, 1, 1)` self-copy is destructive (raises + corrupts).
**Why it happens:** The `1,1` args look like "copy state 1 to state 1." Phase 3 empirically corrected this: default args (no `1,1`) = all-states copy; `1,1` = only state 1 (incomplete); self-copy with `1,1` = destructive.
**How to avoid:** Use `cmd.create(backup_name, obj)` with DEFAULT args for backups (Phase 3 confirmed). `edit_ops.apply_edit` does this internally. NEVER pass `1,1` for a backup.
**Warning signs:** A multi-state object loses states after a backup-then-restore round-trip.

### Pitfall 7: Restore by `cmd.create(obj, backup)` without `cmd.delete(obj)` first (MERGES)
**What goes wrong:** Restoring an object by `cmd.create(obj, backup)` (into the existing `obj` name) MERGES atoms instead of replacing — the user sees double the atoms.
**Why it happens:** `cmd.create` into an existing name appends/merges (Phase 3 empirically corrected). The intuitive "create overwrites" assumption is wrong.
**How to avoid:** Restore sequence = `cmd.delete(obj)` THEN `cmd.create(obj, backup)` (delete first). `edit_ops.restore` does this internally. For Mode (a) object-replace, same sequence: `cmd.delete(obj)` + `load_bundled` (or `cmd.create`).
**Warning signs:** `count_atoms(obj)` after restore is 2× the original.

### Pitfall 8: Bare `count_atoms(obj)` after `cmd.delete(obj)` (RAISES)
**What goes wrong:** Asserting `count_atoms(obj) == 0` after deleting `obj` RAISES `CmdException` (the object doesn't exist).
**Why it happens:** Phase 3 empirically confirmed: bare `count_atoms` on a deleted object raises. The `?` prefix makes it safe (returns 0).
**How to avoid:** Use `count_atoms("?obj") == 0` for deleted-object post-conditions (Phase 3 precedent in `tools/molops_smoke.py`). For existing objects, bare `count_atoms(obj)` is fine.
**Warning signs:** The smoke crashes with `CmdException` on the post-delete assertion.

### Pitfall 9: `cmd.h_fix` / `cmd.h_fill` used as general H ops (WRONG)
**What goes wrong:** A developer reaches for `cmd.h_fix` (looks like "fix hydrogens") or `cmd.h_fill` for general protonation. `h_fix` is **unsupported** (docstring `editing.py:1199`: "unsupported command"); `h_fill` is picked-atom-only (`editing.py:1167`), not selection-based.
**How to avoid:** Use `cmd.h_add` (general, selection-based) for H-add and `cmd.remove` (selection-based) for H-remove. Document this in the ProtonationManager docstring so no future dev reaches for `h_fix`/`h_fill`.
**Warning signs:** `h_fix`/`h_fill` appearing anywhere in `protonation.py` or `edit_ops.py`.

---

## api_signatures (verified, PyMOL 2.5.0)

All signatures read directly from `tmp/pymol-src/modules/pymol/`. Line numbers pinned to 2.5.0.

```python
# tmp/pymol-src/modules/pymol/editing.py:1216
cmd.h_add(selection="(all)", quiet=1, state=0, legacy=0, _self=cmd)
# Adds H based on CURRENT VALENCES (NOT pH). Docstring line 1220.
# Idiom: cmd.h_add(sele); cmd.sort(sele + " extend 1")  (menu.py:751)

# tmp/pymol-src/modules/pymol/editing.py:1163
cmd.h_fill(quiet=1, _self=cmd)
# Removes/replaces H on the PICKED atom only. NOT selection-based. Niche.

# tmp/pymol-src/modules/pymol/editing.py:1195
cmd.h_fix(selection="", quiet=1, _self=cmd)
# UNSUPPORTED (docstring line 1199). DO NOT USE.

# tmp/pymol-src/modules/pymol/editing.py:800
cmd.remove(selection, quiet=1, _self=cmd)
# Removes atoms in selection. THIS IS THE h_remove primitive (no cmd.h_remove exists).
# Example: cmd.remove("resn HIS and name HE2")

# tmp/pymol-src/modules/pymol/editing.py:1424
cmd.alter(selection, expression, quiet=1, space=None, _self=cmd)
# Mutates atomic properties per atom via a Python expression.
# Example: cmd.alter("resi 123 and chain A", "resn='HID'")
# Alterable symbols (line 1446-1449): name, resn, resi, resv, chain, segi, elem, alt, q, b, vdw, type, partial_charge, formal_charge, elec_radius, text_type, label, numeric_type, model*, state*, index*, ID, rank, color, ss, cartoon, flags
# REQUIRES cmd.sort afterward (warning line 1457-1460).

# tmp/pymol-src/modules/pymol/editing.py:1257
cmd.sort(object="", _self=cmd)
# Reorders atoms. MANDATORY after alter (and idiomatic after h_add).

# tmp/pymol-src/modules/pymol/viewing.py:1791
cmd.rebuild(selection='all', representation='everything', *, _self=cmd)
# Forces geometry recreation. Run after alter+h_add so reps refresh.

# tmp/pymol-src/modules/pymol/editing.py:1490
cmd.iterate(selection, expression, quiet=1, space=None, _self=cmd)
# Read-only per-atom traversal. Verify post-protonation state.
# Example: stored=[]; cmd.iterate("resi 123", "stored.append((resn,name,elem))")
# 2.5 callback form (line 1512): cmd.iterate("all", lambda atom: names.append(atom.name))

# tmp/pymol-src/modules/pymol/querying.py:1412
cmd.count_atoms(selection="(all)", quiet=1, state=ALL_STATES, domain='', *, _self=cmd)
# Post-condition primitive. Use "?obj" prefix for deleted objects (bare raises).

# tmp/pymol-src/modules/pymol/creating.py:960
cmd.create(name, selection, source_state=0, target_state=0, discrete=0, zoom=-1,
           quiet=1, singletons=0, extract=None, copy_properties=False, _self=cmd)
# Backup: cmd.create(backup, obj) with DEFAULT args = all-states copy (Phase 3 confirmed).
# DO NOT pass 1,1 for backups (drops multi-state; self-copy destructive).

# tmp/pymol-src/modules/pymol/commanding.py:496
cmd.delete(name, _self=cmd)
# Delete object. Restore = cmd.delete(obj) THEN cmd.create(obj, backup) (delete first).
```

**No-bundled-pH confirmation:** Exhaustive grep of `tmp/pymol-src/modules/pymol/` for `propka|pka|pH|protonat` returned ONLY the unrelated `pkat` mouse-action keyword in `controlling.py` (lines 71, 313, 328, 342, 372, 386, 402, 417, 431, 445, 468, 487, 529). There is NO `cmd.h_remove`, NO propka module, NO pKa calculation, NO pH-aware H-add in PyMOL 2.5.0. (HIGH confidence — direct source grep.)

---

## proposed_design

### ProtonationManager (`c14/pymol_layer/protonation.py`)

```python
# c14/pymol_layer/protonation.py — Phase 4 ProtonationManager (gate-exempt tier).
#
# Curated-variant protonation (CAST-03). NO pH engine. The variant table lives in
# c14/protonation_catalog.py (pure data, domain tier); this module is the
# MECHANISM: look up a variant, route to Mode (a) load or Mode (b) alter+h_ops,
# delegate the actual cmd.alter/cmd.h_add/cmd.remove/cmd.sort/cmd.rebuild to
# edit_ops.apply_edit (the ONE sanctioned-alter site), and track the switch
# state so the user-adjustable switch is reversible (EDIT-05).
#
# DESIGN — 3-tier testability (inject cmd + edit_ops + catalog + assets):
#   * All four deps injected via __init__ — unit-testable in pure WSL python3.6
#     with MockCmd/MockEditOps/MockCatalog/MockAssets (mirrors MolOps Phase 3).
#   * The REAL cmd.* sequence is verified by tools/protonation_smoke.py (headless).
#
# SANCTIONED-ALTER COORDINATION: ProtonationManager does NOT call cmd.alter or
# cmd.h_add directly. It calls edit_ops.apply_edit(target, steps), which is the
# single module where cmd.alter is allowed (tools/check_alter_gate.py allowlist
# = {"c14/pymol_layer/edit_ops.py"}). This guarantees:
#   (1) the alter gate stays ONE module;
#   (2) cmd.sort + cmd.rebuild run for every protonation change (not just edits);
#   (3) a backup is taken before every variant change (EDIT-05 covers protonation);
#   (4) the switch is reversible (restore = edit_ops.restore(target, backup)).
#
# PYTHON 3.6 ONLY: plain class, .format() strings, NO @dataclass / walrus.

class ProtonationManager(object):
    """Curated-variant protonation. NO pH engine (CAST-03).

    apply_variant(target, variant_id) looks up the variant in the catalog and
    routes to Mode (a) load pre-built (AssetManager) or Mode (b) alter+h_ops
    (edit_ops.apply_edit). switch_variant is the user-adjustable SC4 entry;
    current_variant / list_variants support the Phase 6 UI. Every application
    takes a backup via edit_ops.apply_edit so the switch is reversible (EDIT-05).
    """

    def __init__(self, cmd, edit_ops, catalog, assets):
        # type: (cmd, EditOps, module, AssetManager) -> None
        self._cmd = cmd
        self._edit = edit_ops          # the ONE sanctioned-alter site
        self._catalog = catalog        # c14.protonation_catalog (pure data)
        self._assets = assets          # AssetManager (Mode a)
        self._current = {}             # target -> variant_id (switch state)
        self._backup = {}              # target -> backup_name (for restore)

    def list_variants(self, target):
        """Return [(variant_id, label), ...] for the target's residue key.

        `target` carries the residue key (e.g. "HIS") — see MolAction contract.
        Delegates to catalog.variants_for(residue_key).
        """
        return self._catalog.variants_for(self._residue_key(target))

    def current_variant(self, target):
        """Return the currently-applied variant_id for `target`, or None."""
        return self._current.get(target)

    def apply_variant(self, target, variant_id):
        """Apply a curated variant to `target`. Takes a backup first (EDIT-05).

        Mode (a) `load`: cmd.delete(target) + AssetManager.load_bundled(
            spec["source_file"], target). No alter needed (the .pdb is pre-built).
        Mode (b) `alter`: edit_ops.apply_edit(target, [alter_step] + h_ops_steps)
            -> backup + alter resn + targeted h_add/remove + sort + rebuild.

        Records the active variant + backup name for switch reversal.
        Raises KeyError if (residue_key, variant_id) not in catalog.
        """
        spec = self._catalog.lookup(self._residue_key(target), variant_id)
        if spec["mode"] == "load":
            self._apply_load(target, spec)
        else:
            self._apply_alter(target, spec)
        self._current[target] = variant_id
        return variant_id

    def switch_variant(self, target, variant_id):
        """User-adjustable switch (SC4). Equivalent to apply_variant — every
        switch takes a fresh backup so it's reversible. (Alias for apply_variant;
        kept as a distinct name so the SC4 mapping is explicit in the UI.)"""
        return self.apply_variant(target, variant_id)

    def restore(self, target):
        """Restore the pre-protonation state (EDIT-05). Delegates to
        edit_ops.restore(target, self._backup[target]). Clears switch state."""
        bak = self._backup.get(target)
        if bak is None:
            raise RuntimeError("protonation: no backup for {!r}".format(target))
        self._edit.restore(target, bak)
        self._current.pop(target, None)
        self._backup.pop(target, None)

    def _residue_key(self, target):
        """Derive the catalog residue key from `target`. For a MolAction target
        like 'pdb:1TNR/chainA/HIS123' the key is 'HIS' (coordinate with the
        target-schema convention the editing-safety researcher settles). For
        Phase 4 placeholder smoke, target is just 'HIS' or 'scene'."""
        # Phase 4 placeholder: target IS the residue key. Phase 5+ target schema
        # may need parsing (coordinate with editing-safety + asset targeting).
        return target

    def _apply_load(self, target, spec):
        # Mode (a): replace the object with a pre-built protonated structure.
        # src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete
        self._cmd.delete(target)
        self._assets.load_bundled(spec["source_file"], target)
        self._backup[target] = None  # no in-place backup needed (the .pdb IS the source of truth)

    def _apply_alter(self, target, spec):
        # Mode (b): build the edit_steps list and delegate to edit_ops.apply_edit.
        steps = [{"op": "alter", "selection": target, "expression": "resn='{}'".format(spec["resn"])}]
        for h in spec.get("h_ops", []):
            steps.append({"op": h["op"], "selection": h["selection"].replace("resn HIS", "resn {}".format(target))})
        bak = self._edit.apply_edit(target, steps)
        self._backup[target] = bak
```

### Variant_id scheme

Format: `<RESN>_<TAUTOMER>` for tautomers (e.g. `HIS_HID`, `HIS_HIE`, `HIS_HIP`) and `<RESN>_<PROTONATION_STATE>` for acid/base pairs (e.g. `ASP_deprot`, `ASP_prot`, `LYS_prot`, `LYS_deprot`). The residue key (the catalog's top-level key) is the standard residue name (`HIS`, `ASP`, `GLU`, `LYS`, `CYS`, `TYR`); the variant_id is `<RESN>_<STATE>`. The `label` field carries the human-readable string for the Phase 6 UI switch.

### Catalog schema (recap)

```python
# c14/protonation_catalog.py
CATALOG = {
    "<RESN>": {
        "<RESN>_<STATE>": {
            "mode": "load" | "alter",        # (a) or (b)
            "resn": "<new resn>",            # (b): e.g. "HID"
            "h_ops": [                       # (b): ordered; remove before alter, add after
                {"op": "remove", "selection": "..."},
                {"op": "add", "selection": "..."},
            ],
            "source_file": "<bundled .pdb>", # (a): the pre-built structure
            "claim_id": "<cite id>",          # CITE-01; "PLACEHOLDER_PHASE5" for Phase 4
            "label": "<human label>",         # Phase 6 UI
        },
    },
}
```

### Two modes (CAST-03) — when to use each

| Mode | When | Mechanism | Pros | Cons |
|------|------|-----------|------|------|
| (a) Load pre-built | Whole-structure protonation (e.g. a substrate whose entire protonation state is curated). The `.pdb` ships with the right H atoms. | `AssetManager.load_bundled` (Phase 3) after `cmd.delete`. | No alter/sort/rebuild complexity; the `.pdb` IS the source of truth; no valence-trap (Pitfall 2). | One `.pdb` per variant (storage cost); replaces the whole object (no partial). |
| (b) alter + targeted h_ops | Single-residue (or few-residue) protonation change on an already-loaded structure (e.g. switch one active-site HIS tautomer). | `edit_ops.apply_edit(target, [alter] + h_ops)` — alter resn + targeted `remove`/`h_add` + sort + rebuild, under one backup. | In-place (keeps the rest of the structure); one catalog entry per tautomer; reversible via the backup. | Must order remove-before-alter-add (Pitfall 2); must sort+rebuild (Pitfall 3). |

**Phase 4 placeholder example uses Mode (b)** (a single histidine residue in `_his_smoke.pdb`) because it exercises the full alter+h_ops+sort+rebuild+backup+restore pipeline — the riskiest path. Mode (a) is a thin `delete + load_bundled` (mostly already built in Phase 3); a smoke for it is a nice-to-have but the alter path is the one that needs proving.

### User-adjustable switch (SC4) — two entry points

**MolAction contract (story-graph `on_enter`):**
```python
# A protonation change as a MolAction (emitted by the story interpreter on node entry).
MolAction("protonate", target="scene", args={"variant_id": "HIS_HID"})
# molops.apply(action) dispatches to ProtonationManager.apply_variant(target, variant_id).
```
This is how the story graph applies a curated protonation on entering a node (e.g. "the active-site histidine is in the HID tautomer for this step"). The `protonate` op is the Phase 4 branch in `molops.py` (currently `raise NotImplementedError` at line 118-119 — THIS is the boundary).

**Direct API (Phase 6 UI buttons):**
```python
# Phase 6 UI "protonation switch" buttons call ProtonationManager directly:
variants = pm.list_variants("scene")         # [("HIS_HID", "..."), ("HIS_HIE", "..."), ...]
pm.switch_variant("scene", "HIS_HIE")        # user picked HIE
pm.current_variant("scene")                  # -> "HIS_HIE"
pm.restore("scene")                          # "reveal correct 3D model" button (EDIT-05)
```

**Both paths route through `apply_variant` → `edit_ops.apply_edit` → backup + alter + h_ops + sort + rebuild.** The switch is reversible because every application takes a backup (EDIT-05).

### `molops.py` Phase 4 branch (the boundary)

```python
# c14/pymol_layer/molops.py — add the `protonate` branch (currently NotImplementedError at line 118)
elif op == "protonate":
    if self._protonation is None:
        raise RuntimeError("molops.protonate requires a ProtonationManager")
    self._protonation.apply_variant(
        action.target, action.args["variant_id"])
```
`MolOps.__init__` gains an optional `protonation=None` param (mirrors `asset_manager`). The Phase 4 controller injects a real `ProtonationManager`; unit tests inject a `MockProtonationManager`.

---

## residue_nomenclature

### Standard protonation-state nomenclature (NOT cited claims — standard AMBER naming)

The following are **standard residue protonation-state nomenclature conventions** (the AMBER force field naming scheme, used by PyMOL's residue templates). These are naming conventions, NOT scientific claims — they say "this is what we call a histidine with H on Nδ" not "this is the active tautomer for enzyme X." No `claim_id` is needed for the nomenclature itself; the reaction-relevant CHOICE per enzyme is the cited claim (see Phase 5 boundary below).

| Residue | Standard name | Protonation-state variants (standard nomenclature) | Atoms that differ |
|---------|---------------|---------------------------------------------------|-------------------|
| Histidine | `HIS` | `HID` (δ-protonated: H on Nδ1, Nε2 free) / `HIE` (ε-protonated: H on Nε2, Nδ1 free) / `HIP` (doubly protonated: H on both Nδ1 and Nε2, cationic) | `HD1` (Nδ1-H), `HE2` (Nε2-H) |
| Aspartate | `ASP` | `ASP` (deprotonated, carboxylate — standard PDB) / `ASH` (protonated, carboxylic acid) | `HD1`/`HD2` (the carboxyl H) |
| Glutamate | `GLU` | `GLU` (deprotonated — standard PDB) / `GLH` (protonated, carboxylic acid) | `HE1`/`HE2` (the carboxyl H) |
| Lysine | `LYS` | `LYS` (protonated, ammonium — standard PDB) / `LYN` (deprotonated, amine) | `HZ1`/`HZ2`/`HZ3` (the Nζ Hs) |
| Cysteine | `CYS` | `CYS` (thiol, protonated) / `CYM` (thiolate, deprotonated) | `HG` (the Sγ-H) |
| Tyrosine | `TYR` | `TYR` (protonated phenol — standard PDB) / `TYM` (deprotonated phenolate) | `HH` (the Oη-H) |

**Confidence: HIGH for the nomenclature itself** (this is AMBER/standard force-field naming, verifiable in any computational chemistry reference; PyMOL recognizes `HID`/`HIE`/`HIP` as resn values for `alter`). **No `claim_id` is needed for the NAMES.**

### What NEEDS Phase 5+ approval (CITE-01 — cited scientific claims)

The following are **NOT** in Phase 4 — they are cited scientific claims requiring per-claim human approval (CITE-01):

| Claim type | Example (do NOT include in Phase 4) | Why it needs approval |
|------------|-------------------------------------|------------------------|
| Which tautomer is "the active-site one" for a specific enzyme | "PDB 1TNR's His57 is in the HIE tautomer because ..." | A reaction-mechanism claim tied to a specific PDB + residue + mechanism. |
| A pKa value | "His pKa ≈ 6.0" | A quantitative chemistry claim; pKa varies by microenvironment. |
| Which protonation state is "physiological" for a specific residue in a specific enzyme | "Asp102 in PDB X is deprotonated at pH 7.4 because ..." | A context-dependent claim tied to a specific structure. |
| A DOI / paper citation backing a protonation choice | `claim_id: "doi:10.1021/..."` | CITE-01 — every citation must be human-approved. |
| "This protonation is reaction-relevant for the catalytic mechanism of enzyme X" | any such statement | The core CAST-03 "reaction-relevant" claim. |

**Phase 4 boundary (explicit):** Phase 4 ships the MECHANICS (ProtonationManager + catalog schema + Mode a/b + switch + backup/restore) and a PLACEHOLDER example using the standard HID/HIE/HIP nomenclature with `claim_id="PLACEHOLDER_PHASE5"`. The placeholder demonstrates the MECHANICS work headlessly; it does NOT assert that any particular tautomer is "the right one" for any real enzyme. The real curated per-enzyme variant sets — with real `claim_id`s, real pKa justification where applicable, and the reaction-relevant choice per catalytic residue — are Phase 5+ content approval (CITE-01). Phase 4's `claim_id="PLACEHOLDER_PHASE5"` is explicitly a "to be replaced" marker so the citation gate (`tools/check_citations.py`) can flag any catalog entry that still has a placeholder at ship time.

---

## test_strategy

### Headless smoke (`tools/protonation_smoke.py`) — SC4 exercise

Reuses the Phase 3 SMOKE harness pattern (`tools/molops_smoke.py`): `pymol.finish_launching()`; `check(name, ok, detail)`; `SMOKE_RESULT: PASS|FAIL` stdout sentinel (the bat always returns 0, so `$?` is unreliable — Phase 3 Gotcha #1). Run via `bash tools/run_headless.sh tools/protonation_smoke.py`.

**New bundled fixture required:** `c14/data/assets/bundled/_his_smoke.pdb` — a minimal histidine residue (or a di-/tri-peptide containing HIS). The existing `_smoke.pdb` is ethanol (3 atoms, no N) — useless for protonation. The fixture MUST:
- Contain one HIS residue with a resn PyMOL recognizes as `HIS` (so `alter` to `HID`/`HIE`/`HIP` works).
- Have explicit H atoms on the ring so Mode (b) remove/add has something to operate on.
- Be small (one residue is enough) for fast headless runs.
- **Be a PLACEHOLDER fixture** — NOT a real catalytic-residue extract (no `claim_id`; just "a histidine for mechanics testing"). Note this in a header comment.

**Smoke sequence (the SC4 exercise):**
```
1. load _his_smoke.pdb into "scene" (AssetManager.load_bundled)
2. backup (edit_ops.apply_edit or explicit cmd.create("_bak_scene", "scene"))
3. apply_variant("scene", "HIS_HID")  -> alter resn=HID + remove HE2 + add HD1 + sort + rebuild
4. assert: cmd.count_atoms("resn HID") >= 1
           AND cmd.iterate("resn HID") -> resn == "HID"
           AND cmd.count_atoms("resn HID and name HD1") >= 1   # the Ndelta-H present
           AND cmd.count_atoms("resn HID and name HE2") == 0  # the Nepsilon-H absent
5. switch_variant("scene", "HIS_HIE")  -> the user-adjustable switch (SC4)
6. assert: cmd.count_atoms("resn HIE") >= 1
           AND cmd.count_atoms("resn HIE and name HE2") >= 1
           AND cmd.count_atoms("resn HIE and name HD1") == 0
7. restore("scene")  -> EDIT-05 restore safety net
8. assert: cmd.count_atoms("resn HIS") >= 1   # back to original resn
           AND H count matches the pre-protonation H count (round-trip equality)
9. print SMOKE_RESULT: PASS (or FAIL with SMOKE_FAILED_STAGES list)
```

**Verdict:** `grep "^SMOKE_RESULT: PASS" /tmp/opencode/protonation_smoke.txt` (via `tools/run_headless.sh`, which already does this).

**Every `cmd.*` call in the smoke carries a `# src:` citation** (Phase 3 convention). The ProtonationManager's internal `cmd.*` calls are cited in `c14/pymol_layer/protonation.py` (verified by a unit test `test_citations_present_in_source`, mirroring Phase 3).

### Pure-Python unit tests (no PyMOL) — `tests/test_protonation_catalog.py` + `tests/test_protonation_manager.py`

**Catalog tests (`test_protonation_catalog.py` — pure data, no pymol):**
- `test_catalog_schema_load_entries`: every entry has `mode` in `{"load","alter"}`; `alter` entries have `resn` + `h_ops`; `load` entries have `source_file`; every entry has `claim_id` + `label`.
- `test_lookup_found`: `lookup("HIS", "HIS_HID")` returns the spec dict; `lookup("HIS", "HIS_HIE")` etc.
- `test_lookup_missing_residue_raises`: `lookup("XXX", "...")` raises `KeyError` with "unknown residue".
- `test_lookup_missing_variant_raises`: `lookup("HIS", "HIS_XXX")` raises `KeyError` with "unknown variant".
- `test_variants_for_returns_labels`: `variants_for("HIS")` returns a list of `(variant_id, label)` tuples including `HIS_HID`, `HIS_HIE`, `HIS_HIP`.
- `test_phase4_placeholder_claim_ids`: every catalog entry's `claim_id == "PLACEHOLDER_PHASE5"` (Phase 4 boundary — no real claims land yet). This test is REMOVED in Phase 5+ when real claim_ids land.
- `test_no_pka_values_in_catalog`: scan the catalog for numeric pKa patterns (e.g. `pKa`, `~6.`, `pH`); assert none present (Pitfall 5 guard — no fabricated science).

**Manager tests (`test_protonation_manager.py` — inject MockCmd/MockEditOps/MockCatalog/MockAssets):**
- `test_apply_variant_alter_routes_through_edit_ops`: `apply_variant("HIS", "HIS_HID")` calls `mock_edit.apply_edit("HIS", steps)` with the right steps (alter + h_ops in order); does NOT call `mock_cmd.alter` directly (sanctioned-alter gate test).
- `test_apply_variant_load_routes_through_assets`: `apply_variant(<load target>, <load vid>)` calls `mock_cmd.delete` then `mock_assets.load_bundled`; does NOT call `mock_edit.apply_edit`.
- `test_switch_variant_records_state`: after `switch_variant("scene", "HIS_HIE")`, `current_variant("scene") == "HIS_HIE"`.
- `test_restore_clears_state`: after `apply_variant` then `restore`, `current_variant(target) is None` and the backup name is cleared.
- `test_apply_variant_unknown_residue_raises`: `apply_variant("XXX", "...")` raises `KeyError` (delegated to catalog).
- `test_apply_variant_unknown_variant_raises`: `apply_variant("HIS", "HIS_XXX")` raises `KeyError`.
- `test_list_variants_delegates_to_catalog`: `list_variants("HIS")` returns `mock_catalog.variants_for("HIS")`.
- `test_citations_present_in_source`: assert `protonation.py` has `# src: tmp/pymol-src/...` comments for every `self._cmd.*` call (Phase 3 convention).

### AST gate (no new gate for protonation specifically — the alter gate is the editing-safety researcher's)

- `tools/check_imports.py` (Phase 1, existing): `c14/protonation_catalog.py` MUST pass (no pymol import — it's pure data in the domain tier). `c14/pymol_layer/protonation.py` is exempt (in `pymol_layer/`).
- `tools/check_alter_gate.py` (editing-safety, NEW): allowlist = `{"c14/pymol_layer/edit_ops.py"}` ONLY. ProtonationManager is NOT in the allowlist (it routes through edit_ops). A test asserts `protonation.py` does NOT contain a bare `cmd.alter(` call.

### Human-verify checkpoints (NOT automatable from WSL)

- The Phase 6 UI buttons (list_variants / switch_variant / restore) — Qt, untestable from WSL (AGENTS.md). Phase 6 human-verify.
- The visual correctness of a protonation change (does the H actually appear on the right N in the viewer?) — the smoke asserts atom counts + resn, but a human confirms the geometry looks right. Phase 6 human-verify.

---

## phase4_boundary (mechanics now vs content Phase 5+)

### Phase 4 ships (the MECHANICS + a placeholder example)

1. `c14/pymol_layer/protonation.py` — `ProtonationManager` (apply_variant, switch_variant, current_variant, list_variants, restore; Mode a/b routing; delegates to edit_ops).
2. `c14/protonation_catalog.py` — the catalog schema + PLACEHOLDER entries for HIS (HID/HIE/HIP) and optionally ASP/GLU/LYS/CYS/TYR, all with `claim_id="PLACEHOLDER_PHASE5"`.
3. `c14/pymol_layer/molops.py` — the `protonate` branch (currently `NotImplementedError` at line 118) implemented to delegate to `ProtonationManager`.
4. `c14/data/assets/bundled/_his_smoke.pdb` — a minimal histidine PLACEHOLDER fixture (no `claim_id`; for mechanics testing only).
5. `tools/protonation_smoke.py` — the headless SC4 exercise (load → backup → HID → HIE → restore; SMOKE_RESULT sentinel).
6. `tests/test_protonation_catalog.py` + `tests/test_protonation_manager.py` — pure-Python unit tests (catalog schema + MockCmd dispatch).
7. Coordinated with the editing-safety researcher: `edit_ops.apply_edit` exposes the multi-step entry point ProtonationManager needs; the alter gate allowlist = `{"c14/pymol_layer/edit_ops.py"}` ONLY.

### Phase 5+ ships (the real curated CONTENT — cited claims, CITE-01)

1. Real `claim_id`s in the catalog (each backed by an approved source, per the CITE-01 per-claim checkpoint).
2. The reaction-relevant tautomer/protonation choice per catalytic residue per enzyme (e.g. "PDB 1TNR His57 is HIE because [approved source]").
3. Per-enzyme curated variant sets (the catalog grows from the placeholder HIS example to the full cast's catalytic residues).
4. pKa justification where applicable (only if a source is approved; never fabricated).
5. Mode (a) pre-built protonated `.pdb` files for whole-structure protonation (with their own `claim_id`s + SOURCES.md entries).
6. The `test_phase4_placeholder_claim_ids` test is REMOVED (real claim_ids replace `PLACEHOLDER_PHASE5`).

### Boundary enforcement (so Phase 4 doesn't leak fabricated science)

- `test_phase4_placeholder_claim_ids`: every catalog `claim_id == "PLACEHOLDER_PHASE5"`. Fails if a real claim_id lands in Phase 4.
- `test_no_pka_values_in_catalog`: scan for pKa/pH/numeric-pattern claims; assert none. Fails if fabricated pKa lands.
- The citation gate (`tools/check_citations.py`, Phase 1) blocks ship on any `pending`/missing `claim_id` — and `PLACEHOLDER_PHASE5` is treated as `pending` for ship-gate purposes (coordinate: the gate's claim registry treats `PLACEHOLDER_*` as `pending`).

---

## Sources

### Primary (HIGH confidence — direct source read)
- `tmp/pymol-src/modules/pymol/editing.py:1216` — `cmd.h_add` signature + docstring ("adds hydrogens onto a molecule based on current valences" — valence-only confirmation).
- `tmp/pymol-src/modules/pymol/editing.py:1163` — `cmd.h_fill` (picked-atom only).
- `tmp/pymol-src/modules/pymol/editing.py:1195` — `cmd.h_fix` (unsupported).
- `tmp/pymol-src/modules/pymol/editing.py:800` — `cmd.remove` (the h-remove primitive).
- `tmp/pymol-src/modules/pymol/editing.py:1424` — `cmd.alter` signature + symbols + sort warning (line 1457-1460).
- `tmp/pymol-src/modules/pymol/editing.py:1257` — `cmd.sort`.
- `tmp/pymol-src/modules/pymol/editing.py:1490` — `cmd.iterate` (+ 2.5 callback form line 1512).
- `tmp/pymol-src/modules/pymol/viewing.py:1791` — `cmd.rebuild`.
- `tmp/pymol-src/modules/pymol/querying.py:1412` — `cmd.count_atoms`.
- `tmp/pymol-src/modules/pymol/creating.py:960` — `cmd.create` (default args = all-states copy).
- `tmp/pymol-src/modules/pymol/commanding.py:496` — `cmd.delete`.
- `tmp/pymol-src/modules/pymol/menu.py:751` — the canonical `h_add; sort` idiom.
- Exhaustive grep of `tmp/pymol-src/modules/pymol/` for `propka|pka|pH|protonat` → only `pkat` mouse keyword (no pH engine bundled). HIGH confidence.
- Exhaustive grep for `h_remove` → no matches (no `cmd.h_remove` in 2.5.0). HIGH confidence.

### Secondary (MEDIUM confidence — built-code contract, read)
- `c14/pymol_layer/molops.py` (Phase 3) — `protonate` branch at line 118 raises `NotImplementedError` (the Phase 4 boundary).
- `c14/pymol_layer/asset_manager.py` (Phase 3) — `AssetManager.load_bundled` (Mode a entry point).
- `c14/story/model.py` (Phase 2) — `MolAction(op, target, args)` pure-data carrier.
- `tools/check_imports.py` (Phase 1) — `SKIP_DIRS = {"pymol_layer", "ui", "__pycache__}`, `BANNED_TOP = ("pymol", "PyQt5")`.
- `tools/molops_smoke.py` + `tools/run_headless.sh` (Phase 3) — SMOKE_RESULT sentinel pattern (the bat always returns 0).
- `.planning/phases/03-pymol-cmd-layer-asset-mgmt/03-RESEARCH.md` — `cmd.create(obj,sele,1,1)` is NOT a no-op for new target (copies only state 1); default args = all-states copy; `count_atoms` on deleted object raises (use `?` prefix); restore = delete then create.

### Tertiary (LOW confidence — design recommendations, depend on editing-safety contract)
- The `edit_ops.apply_edit(target, steps, backup_name=None)` signature is a PROPOSAL — the editing-safety researcher's plan settles the actual signature. Coordinate in the planner.
- The alter gate allowlist = `{"c14/pymol_layer/edit_ops.py"}` is the RECOMMENDATION — the editing-safety researcher's `tools/check_alter_gate.py` settles the actual allowlist. Coordinate.

## Metadata

**Confidence breakdown:**
- Standard stack (PyMOL API signatures): HIGH — every signature read from `tmp/pymol-src/`, line numbers pinned to 2.5.0.
- h_add valence-only / no-pH-engine / no-cmd.h_remove: HIGH — confirmed by docstring + exhaustive grep.
- Architecture (ProtonationManager + catalog split + 3-tier): HIGH — reuses Phase 3 precedent directly.
- Sanctioned-alter coordination (route through edit_ops): MEDIUM — the recommendation is sound but depends on the editing-safety researcher's `edit_ops.apply_edit` exposing the multi-step entry point ProtonationManager needs. Coordinate in the planner.
- Backup/restore integration: MEDIUM — `cmd.create` default-args backup + delete-then-create restore is HIGH (Phase 3 confirmed); the ProtonationManager-calls-apply_edit integration is MEDIUM (depends on the editing-safety contract).
- Residue nomenclature: HIGH for the names (standard AMBER); the reaction-relevant choice per enzyme is explicitly Phase 5+ (not a Phase 4 claim).
- Test strategy: HIGH — reuses the Phase 3 SMOKE harness + unit-test patterns verbatim.

**Research date:** 2026-08-15
**Valid until:** 2026-09-14 (30 days — stable; the PyMOL 2.5.0 API and the settled curated-variant decision are not expected to change)
