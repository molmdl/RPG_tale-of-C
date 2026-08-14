# Phase 4: Editing, Protonation & Restore Safety Net — Research (Editing Safety & Backup/Restore concern)

**Researched:** 2026-08-15
**Domain:** PyMOL 2.5.0 molecule-editing API (`alter`/`sort`/`create`/`delete`/`fuse`/`remove`) + backup/restore safety net + sanctioned-path enforcement gate
**Confidence:** HIGH (every API claim verified against `tmp/pymol-src/modules/pymol/*.py` with file:line citations; the alter→sort trap is PRIMARY-SOURCE-documented in the `cmd.alter` docstring itself)

## Summary

This is the highest technical-risk concern of the whole project. The good news: the central hazard — the `alter`→`sort` silent-corruption trap — is **explicitly documented in the PyMOL 2.5.0 source itself**. The `cmd.alter` docstring (`editing.py:1457-1460`) warns verbatim: *"You should always issue a `sort` command on an object after modifying any property which might affect canonical atom ordering (names, chains, etc.). Failure to do so will confound subsequent `create` and `byres` operations."* The `cmd.sort` docstring (`editing.py:1261-1264`) confirms it recomputes atom ordering and is "usually only necessary … after an `alter` command which has modified the names of atom properties." The built-in PyMOL menu even follows the idiom `cmd.h_add(sele); cmd.sort(sele + " extend 1")` (`menu.py:751-752`). So the mitigation is not invention — it is mechanical enforcement of a contract PyMOL already documents.

The Phase 4 engineering deliverable is therefore a **single sanctioned helper** `apply_edit` (in a new `c14/pymol_layer/edit_ops.py`) that is the ONLY place in the whole repo allowed to call `cmd.alter`, that ALWAYS calls `cmd.sort` + `cmd.rebuild` after any alter, that takes a `cmd.create` backup (default-args = all states — the empirically-corrected Phase 3 form) before editing, and that returns a `RestoreHandle` whose `.restore()` does `cmd.delete` + `cmd.create`-from-backup. A dedicated AST gate (`tools/check_alter_gate.py`) enforces "no `cmd.alter` outside `edit_ops.py`" so SC1 is machine-checkable. The backup/restore round-trip (atom count + residue signature) and the per-enzyme coverage scan are headlessly testable via the proven `run-conda-pymol.bat -cq` + `SMOKE_RESULT: PASS` sentinel harness, on a small committed peptide fixture — NO real PDB content required (that is Phase 5+).

**Primary recommendation:** Build `c14/pymol_layer/edit_ops.py` with `apply_edit(edit_type, object_name, sele, **kwargs) -> RestoreHandle` as the sole sanctioned `cmd.alter` path; enforce it with `tools/check_alter_gate.py` (AST, allowlist = `{edit_ops.py}`); back up with default-args `cmd.create`; restore with `cmd.delete` + `cmd.create`; verify round-trips with `count_atoms` + an iterate-collected `(chain,resi,resn)` residue signature; demo it all headlessly on a committed 2-residue peptide fixture.

---

## Standard Stack

The established PyMOL 2.5.0 APIs for this domain. Every entry is verified by reading the source at the cited file:line.

### Core (verified from `tmp/pymol-src/modules/pymol/`)

| API | Signature (file:line) | Purpose | Why Standard |
|-----|----------------------|---------|--------------|
| `cmd.alter` | `alter(selection, expression, quiet=1, space=None, _self=cmd)` — `editing.py:1424` | Change atomic properties (resn, resi, chain, name, …) via a per-atom Python expression | The ONLY way to mutate atom metadata in-place. Docstring itself mandates `sort` after (`editing.py:1457-1460`). THIS is the trap-triggering op the gate must contain. |
| `cmd.sort` | `sort(object="", _self=cmd)` — `editing.py:1257` | Recompute canonical atom ordering after `alter` mutated ordering-affecting properties | The REQUIRED antidote to the alter trap (`editing.py:1261-1264`). Calls C-level `_cmd.sort` (`editing.py:1281`). |
| `cmd.rebuild` | `rebuild(selection='all', representation='everything', *, _self=cmd)` — `viewing.py:1791` | Force PyMOL to recreate geometric/representation objects that went out of sync | `alter` docstring: "You may need to issue a `rebuild` in order to update associated representations" (`editing.py:1454-1455`). sort fixes DATA ordering; rebuild fixes DISPLAY sync. Both needed. |
| `cmd.create` | `create(name, selection, source_state=0, target_state=0, discrete=0, zoom=-1, quiet=1, singletons=0, extract=None, copy_properties=False, _self=cmd)` — `creating.py:960` | Create a new independent molecule object from a selection (the BACKUP) | Default-args (`source_state=0, target_state=0` = copy ALL states) is the empirically-correct backup form (Phase 3 `api_sanity_smoke.py:145-159`, STATE.md:84). Makes an independent copy. |
| `cmd.delete` | `delete(name, _self=cmd)` — `commanding.py:496` | Remove whole objects/selections (supports wildcards) | Restore step 1: delete the edited object so `create` into the same name doesn't MERGE. |
| `cmd.count_atoms` | `count_atoms(selection="(all)", quiet=1, state=ALL_STATES, domain='', *, _self=cmd)` — `querying.py:1412` | Return int atom count | Round-trip verification (SC2). Use `?`-prefix (`count_atoms("?obj")`) on possibly-deleted objects (molops_smoke convention; bare form RAISES on deleted). |
| `cmd.iterate` | `iterate(selection, expression, quiet=1, space=None, _self=cmd)` — `editing.py:1490` | Run a per-atom Python expression (read-only) in a namespace exposing `resn/resi/chain/segi/name/…` | Residue-identity signature collection (SC2 "residue identity"). Idiom: `iterate(sele, "stored.list.append((chain,resi,resn))", space={'stored': stored})` — same pattern as `mutagenesis.py:426,440`. Also supports a lambda callback in 2.5 (`editing.py:1512-1515`). |
| `cmd.remove` | `remove(selection, quiet=1, _self=cmd)` — `editing.py:800` | Remove atoms (within objects) — vs `delete` which removes whole objects | Substrate "remove a group" edit type. |
| `cmd.fuse` | `fuse(selection1="(pk1)", selection2="(pk2)", mode=0, recolor=1, move=1, _self=cmd)` — `editing.py:937` | Join two objects by forming a bond; copies object-of-selection-1 into object-of-selection-2 | Substrate "add a group" edit type (fuse a fragment onto the substrate). Single atom per selection (`editing.py:966`). |

### Supporting

| API | Signature (file:line) | Purpose | When to Use |
|-----|----------------------|---------|-------------|
| `cmd.alter_state` | `alter_state(state, selection, expression, quiet=1, space=None, atomic=1, _self=cmd)` — `editing.py:1535` | Change per-state coordinates/flags | NOT needed for Phase 4 (no coordinate edits); listed for completeness. The mutagenesis wizard uses it for geometry (`mutagenesis.py:497,519`). |
| `cmd.attach` | `attach(element, geometry, valence, name='', quiet=1, _self=cmd)` — `editing.py:919` | Add a single atom to the picked atom (`pk1`) | NOT headless-friendly (needs `pk1`); prefer `fuse` for substrate add. |
| `cmd.refresh` | `refresh(_self=cmd)` — `viewing.py:1704` | Redraw the current frame | NOT needed headless; `rebuild` is the data-level fix. |
| `cmd.get_unused_name` | (stdlib PyMOL cmd) | Generate a unique temp name | Backup-object naming to avoid collisions (mutagenesis.py uses fixed `_tmp_*` names + delete-in-clear; `get_unused_name("_bak")` is the collision-safe alternative). |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `cmd.alter` resn for point mutation | `cmd.wizard("mutagenesis")` / `Mutagenesis` wizard (`wizard/mutagenesis.py:38`) | **Wizard is NOT headless-friendly**: needs `pk1` atom-picking (`mutagenesis.py:211,715-730`), `os.environ['PYMOL_DATA']/chempy/sidechains/*.pkl` rotamer libraries (`mutagenesis.py:58-59,223`), `cmd.refresh_wizard`, `cmd.push_undo`, `cmd.frame`. Even the wizard calls `cmd.alter` internally (`mutagenesis.py:346,474-475`). Use `alter` resn for Phase 4 mechanics; defer rotamer-correct sidechain geometry to Phase 5+ content. |
| `cmd.create` for backup | `cmd.copy` / session save | `create` is the decided mechanism (default-args = all states, independent copy, empirically verified Phase 3). `copy` is a thinner alias; `create` is the documented primitive. Session save is too heavyweight + not headless-verifiable per-field. |
| `cmd.delete`+`cmd.create` for restore | `cmd.push_undo`/`cmd.pop_undo` | Undo stack is GUI/wizard-oriented (`mutagenesis.py:390` uses `push_undo`) and not reliably headless-controllable. delete+create is explicit, verifiable, and decided. |

**Installation:** None. All APIs ship in `pymol-open-source` (PyMOL 2.5.0). No new dependencies. numpy/PyQt5 already present. **Do NOT add RDKit or any external editor** (spec.md no-new-dependencies rule).

---

## Architecture Patterns

### Recommended Placement (3-tier testability layering — NON-NEGOTIABLE)

```
c14/
├── story/model.py            # MolAction (pure data: op/target/args) — NO pymol import (AST-gated)
├── pymol_layer/              # GATE-EXEMPT (check_imports.py SKIP_DIRS) — cmd.* lives here
│   ├── molops.py             # Per-action MolAction->cmd.* dispatcher (Phase 3, 8 ops done)
│   ├── asset_manager.py      # Load/fetch resolver (Phase 3)
│   └── edit_ops.py           # *** NEW (Phase 4) *** apply_edit + take_backup + restore + RestoreHandle
└── ...                       # domain tier (AST-gated: NO pymol/PyQt5)
tools/
├── check_imports.py          # existing AST gate (bans pymol/PyQt5 in c14/ root)
├── check_alter_gate.py       # *** NEW (Phase 4) *** AST gate: cmd.alter ONLY in edit_ops.py
├── check_edit_coverage.py    # *** NEW (Phase 4) *** per-enzyme coverage scan (SC5)
├── run_headless.sh           # existing WSL->Windows bridge (SMOKE_RESULT sentinel)
├── edit_smoke.py             # *** NEW (Phase 4) *** headless apply_edit+backup/restore smoke (SC1,SC2)
└── molops_smoke.py           # existing (Phase 3) — extend to dispatch edit/restore via molops
c14/data/
├── assets/bundled/
│   ├── _smoke.pdb            # existing 3-atom ETH fixture (Phase 3)
│   └── _edit_smoke.pdb       # *** NEW (Phase 4) *** 2-residue peptide fixture (committed, no network)
├── cast.json                 # *** NEW (Phase 4, placeholder) *** enzymes represented so far
└── edits.json                # *** NEW (Phase 4, placeholder) *** known-edit entries per enzyme
```

### Pattern 1: Inject `cmd` (the Phase 3 testability pattern — REUSE, do not reinvent)
**What:** `edit_ops.py` injects `cmd` via the constructor (exactly like `molops.py:80` and `asset_manager.py:63`), so the dispatch/sequence logic is unit-testable in pure WSL python3.6 with a `MockCmd` recording `alter/sort/rebuild/create/delete/count_atoms` calls. The REAL cmd.* contract is verified by `tools/edit_smoke.py` headlessly.
**When to use:** ALWAYS for any `c14/pymol_layer/` module. The AST gate bans pymol imports in `c14/` root; the injected-cmd pattern lets the pymol_layer modules be unit-tested without pymol installed.
**Example (mirrors molops.py:80):**
```python
# c14/pymol_layer/edit_ops.py
class EditOps(object):
    def __init__(self, cmd):
        self._cmd = cmd  # INJECTED -- unit-testable with MockCmd; real cmd via edit_smoke.py

    def apply_edit(self, edit_type, object_name, sele, **kwargs):
        handle = self._take_backup(object_name)
        if edit_type == "point_mutation":
            # src: tmp/pymol-src/modules/pymol/editing.py:1424 cmd.alter
            self._cmd.alter(sele, "resn='{0}'".format(kwargs["new_resn"]))
        elif edit_type == "protonation_change":
            # src: tmp/pymol-src/modules/pymol/editing.py:1424 cmd.alter
            self._cmd.alter(sele, "resn='{0}'".format(kwargs["new_resn"]))
        elif edit_type == "substrate_remove_group":
            # src: tmp/pymol-src/modules/pymol/editing.py:800 cmd.remove
            self._cmd.remove(kwargs["group_sele"])
        elif edit_type == "substrate_add_group":
            # src: tmp/pymol-src/modules/pymol/editing.py:937 cmd.fuse
            self._cmd.fuse(kwargs["frag_atom_sele"], kwargs["target_atom_sele"])
        else:
            raise ValueError("unknown edit_type {!r}".format(edit_type))
        # ALWAYS sort + rebuild after any alter/remove/fuse (the alter->sort trap mitigation)
        # src: tmp/pymol-src/modules/pymol/editing.py:1257 cmd.sort
        self._cmd.sort(object_name)
        # src: tmp/pymol-src/modules/pymol/viewing.py:1791 cmd.rebuild
        self._cmd.rebuild(object_name)
        return handle
```

### Pattern 2: MolOps delegates edit/protonate/restore to EditOps (the Phase 4 boundary)
**What:** `molops.py`'s `edit`/`protonate`/`restore` branches currently `raise NotImplementedError` (`molops.py:118-119`) — the explicit Phase 4 boundary. Phase 4 replaces these by delegating to an injected `EditOps`. MolOps stays the per-action MolAction→cmd dispatcher; EditOps holds the sanctioned alter path.
**When to use:** The MolAction `edit` op carries `edit_type` in `args`; molops reads it and calls `editops.apply_edit(...)`. MolAction stays pure-data (no pymol type named).
**Example:**
```python
# molops.py Phase 4 additions (replace the NotImplementedError branches)
elif op == "edit":
    # MolAction("edit", target, args={edit_type, sele, new_resn/group_sele/...})
    self._editops.apply_edit(
        action.args["edit_type"], action.target, action.args["sele"],
        **{k: v for k, v in action.args.items() if k not in ("edit_type", "sele")})
elif op == "restore":
    # MolAction("restore", target, args={backup_name}) -- or via RestoreHandle
    self._editops.restore(action.target, action.args["backup_name"])
elif op == "protonate":
    # researcher C owns protonation content; the resn-alter routes through apply_edit
    self._editops.apply_edit("protonation_change", action.target,
                             action.args["sele"], new_resn=action.args["new_resn"])
```

### Pattern 3: Backup BEFORE edit, restore = delete + create-from-backup
**What:** `take_backup(obj)` = `delete(bak)` (idempotent) + `create(bak, obj)` (default-args = all states) + assert `count_atoms(bak) == count_atoms(obj)`. `restore(obj, bak)` = `delete(obj)` + `create(obj, bak)` (default-args) + assert atom count + residue signature match.
**When to use:** Before EVERY edit (SC2: "a backup snapshot is taken before the edit … for each edit type").

### Anti-Patterns to Avoid
- **Bare `cmd.alter` outside `edit_ops.py`:** defeats the gate (SC1). Mitigation: `tools/check_alter_gate.py` AST gate.
- **`alter` without `sort`:** the silent-corruption trap. Mitigation: `apply_edit` ALWAYS sorts (unit-test asserts sort follows every alter).
- **`create(bak, src, 1, 1)`:** copies ONLY state 1 → silent multi-state data loss. Mitigation: default-args `create(bak, src)` only (Phase 3 empirical correction).
- **`create(obj, obj)` self-copy:** DESTRUCTIVE (raises + corrupts). Mitigation: never; backup uses a distinct name.
- **Restore without `delete` first:** `create` into an existing name MERGES (`creating.py` docstring: "create states in an existing object"). Mitigation: restore = `delete` THEN `create`.
- **Residue-identity check by resn alone:** a resn swap is invisible if you only compare resn counts. Mitigation: full `(chain, resi, resn)` sorted signature.

---

## Don't Hand-Roll

Problems that look simple but PyMOL already solves — use the cmd.* API, do not reimplement.

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Mutate a residue name | String-replace in PDB text / re-parse | `cmd.alter(sele, "resn='X'")` + `cmd.sort` (`editing.py:1424,1257`) | alter is the in-place primitive; sort fixes the ordering trap PyMOL itself warns about. |
| Snapshot an object | Manual atom-copy / numpy buffer | `cmd.create(bak, obj)` default-args (`creating.py:960`) | create is a C-level deep copy of all states + bonds; verified independent (Phase 3). |
| Restore a snapshot | Re-load the PDB / re-fetch | `cmd.delete(obj)` + `cmd.create(obj, bak)` (`commanding.py:496`, `creating.py:960`) | Avoids network reload; preserves whatever the backup captured. |
| Count atoms | Iterate + len() | `cmd.count_atoms(sele)` (`querying.py:1412`) | C-level, returns int, no Python list allocation. |
| Collect residue identity | Parse PDB lines | `cmd.iterate(sele, expr, space=...)` (`editing.py:1490`) | Works on the live object state (post-edit), not stale file text. |
| Add a group to a substrate | Manually splice coordinates | `cmd.fuse(frag_atom, target_atom)` (`editing.py:937`) | Forms the bond + merges objects in one C-level call. |
| Remove a group | `cmd.delete` (that's whole objects) | `cmd.remove(sele)` (`editing.py:800`) | remove drops atoms WITHIN an object; delete drops whole objects. |
| Refresh representations after alter | Re-issue show/hide | `cmd.rebuild(obj)` (`viewing.py:1791`) | rebuild recreates out-of-sync geometry in one call. |

**Key insight:** Every edit primitive the game needs already exists as a `cmd.*` call. Phase 4's job is **enveloping** them in a safe helper (backup + sort + rebuild + gate), NOT inventing new editing logic. The chemistry-correctness is explicitly out of scope (lookup-table routing, owned by another researcher).

---

## Common Pitfalls

### Pitfall 1: The alter→sort silent-corruption trap (THE central hazard)
**What goes wrong:** After `cmd.alter` changes an ordering-affecting property (resn, resi, chain, name), a subsequent `byres <sele>` selection or `cmd.create` returns the WRONG atoms — silently, with no error. The `byres` keyword (`cmd.py:350`, `helping.py:560`) expands a selection to whole residues using the canonical atom ordering; that ordering is stale until `sort` recomputes it.
**Why it happens:** `cmd.alter` mutates atom properties in place but does NOT recompute the canonical atom ordering. `cmd.sort` (`editing.py:1281`, C-level `_cmd.sort`) is what reorders the atom list. The `cmd.alter` docstring documents this verbatim (`editing.py:1457-1460`); the `cmd.sort` docstring confirms (`editing.py:1261-1264`).
**How to avoid:** `apply_edit` ALWAYS calls `cmd.sort(object_name)` immediately after any `cmd.alter`/`remove`/`fuse`. Enforce with a unit test asserting the MockCmd call sequence ends with sort+rebuild after every alter.
**Warning signs:** A post-edit `byres` selection returns an unexpected atom count; `create` after alter produces a mismatched object. **Minimal reproduce (documented, not gated):** load a multi-residue object → `cmd.alter("resi 5", "resn='ALA'")` (NO sort) → `cmd.count_atoms("byres resi 5")` may return atoms from the stale residue boundary → `cmd.sort("obj")` → re-query returns correct atoms. (Do NOT put a bare-alter reproduce in a gated file; document it in `edit_ops.py`'s docstring instead.)
**Confidence:** HIGH — primary-source (`editing.py:1457-1460`, `editing.py:1261-1264`) + idiom confirmed in `menu.py:751-752`.

### Pitfall 2: `cmd.create(bak, src, 1, 1)` drops multi-state data
**What goes wrong:** `source_state=1, target_state=1` copies ONLY state 1. For a multi-state object, states 2+ are lost — the backup is silently incomplete.
**Why it happens:** The `1,1` form looks intuitive but `source_state=0, target_state=0` means ALL states (`creating.py:979-992`).
**How to avoid:** Backup uses default-args `cmd.create(bak, src)` ONLY. Empirically corrected in Phase 3 (`api_sanity_smoke.py:145-159`, STATE.md:84).
**Warning signs:** `count_atoms(bak) == count_atoms(src)` passes for single-state but multi-state restore is incomplete. Mitigation: round-trip smoke also checks state count if multi-state fixtures are added later.
**Confidence:** HIGH — empirically verified Phase 3.

### Pitfall 3: `cmd.create(obj, obj)` self-copy is DESTRUCTIVE
**What goes wrong:** Creating an object from itself raises `CmdException` and can corrupt the source.
**How to avoid:** Backup ALWAYS uses a distinct name (`_bak_<obj>` or `cmd.get_unused_name("_bak")`). Never `create(obj, obj)`.
**Confidence:** HIGH — empirically verified Phase 3 (STATE.md:84).

### Pitfall 4: Restore without `delete` first MERGES instead of replacing
**What goes wrong:** `cmd.create(obj, bak)` when `obj` still exists appends/merges states into the existing object (`creating.py:963-967` "create a new molecule object … can also be used to create states in an existing object") instead of replacing it. Atom count balloons.
**How to avoid:** Restore = `cmd.delete(obj)` THEN `cmd.create(obj, bak)`. Always. Assert `count_atoms(obj) == count_atoms(bak)` after.
**Confidence:** HIGH — `creating.py` docstring + standard semantics.

### Pitfall 5: `count_atoms("obj")` RAISES on a deleted object
**What goes wrong:** After `cmd.delete(obj)`, `count_atoms("obj")` raises `CmdException('Invalid selection name')` rather than returning 0.
**How to avoid:** Use the `?`-prefix for possibly-deleted objects: `count_atoms("?obj")` returns 0 safely (the `?` = existing-objects-only selector). Established in Phase 3 (`molops_smoke.py:172`, `api_sanity_smoke.py:171`). After restore the object exists again, so `count_atoms("obj")` is fine — but the "delete worked" check must use `?`.
**Confidence:** HIGH — empirically verified Phase 3.

### Pitfall 6: Backup object name collision
**What goes wrong:** A stale `_bak_obj` from a previous edit lingers; `create("_bak_obj", obj)` into the existing name merges stale + new atoms.
**How to avoid:** `take_backup` does `cmd.delete(bak_name)` (idempotent) BEFORE `cmd.create(bak_name, obj)`. Or use `cmd.get_unused_name("_bak")` for a fresh name each time. The mutagenesis wizard uses fixed `_tmp_*` names + deletes them in `clear()` (`mutagenesis.py:313-324`) — same principle.
**Confidence:** HIGH.

### Pitfall 7: Residue-identity check by resn alone misses the mutation
**What goes wrong:** SC2 says restore returns "residue identity". If you verify only `resn` counts, a point mutation (ALA→GLY) that you then restored would look identical to the post-mutation state if you don't capture the FULL signature including the swap.
**How to avoid:** Define residue identity = sorted list of `(chain, resi, resn)` tuples collected via `cmd.iterate(obj, "stored.list.append((chain,resi,resn))", space={'stored': stored})`. Compare the PRE-edit signature (captured in the RestoreHandle at backup time) with the POST-restore signature. They must be byte-identical.
**Confidence:** HIGH — iterate idiom from `mutagenesis.py:426,440`.

### Pitfall 8: Restore does NOT preserve representation/scene state
**What goes wrong:** `delete` + `create` drops the object's show/hide/color/zoom settings (representations are object-attached; a freshly-created object has defaults).
**How to avoid:** Accept this as by-design. The scene is re-established by re-emitting the node's `on_enter` MolActions (show/hide/color/zoom) via molops — that is Phase 6's controller job (the GameEngine already emits on_enter per-action; STATE.md confirms on_enter replay is the established scene-rebuild mechanism). Phase 4's restore only owes ATOM-COUNT + RESIDUE-IDENTITY fidelity (SC2), NOT representation fidelity. Document this boundary explicitly so the planner doesn't over-build.
**Confidence:** HIGH — `create` makes a new object with default reps; standard semantics.

### Pitfall 9: Mutating the backup
**What goes wrong:** If `apply_edit`'s alter selection accidentally overlaps the backup object, the backup is corrupted and restore fails.
**How to avoid:** The alter `sele` MUST target `object_name` (the live object), never the `bak_name`. Use namespaced selections like `"{0} and resi {1}".format(object_name, resi)`. The round-trip smoke should ALSO mutate the live object after backup and assert the backup's count/signature is UNCHANGED (empirically confirms `create` independence).
**Confidence:** HIGH.

---

## API Signatures (verified, copy-paste-ready)

All pinned to PyMOL 2.5.0. Cite these `# src:` comments above each call (the Phase 3 convention, `molops.py:33-37`).

```python
# src: tmp/pymol-src/modules/pymol/editing.py:1424 cmd.alter
cmd.alter(selection, expression, quiet=1, space=None)
# expression is a Python string evaluated per-atom with resn/resi/chain/segi/name/elem/... in scope.
# space defaults to pymol.__dict__; pass space={'stored': stored_obj} for accumulator pattern.
# WARNING (editing.py:1457-1460): ALWAYS cmd.sort(obj) after alter that changes names/chains/resn/resi.

# src: tmp/pymol-src/modules/pymol/editing.py:1257 cmd.sort
cmd.sort(object="")           # recompute canonical atom ordering. No-arg = all objects.

# src: tmp/pymol-src/modules/pymol/viewing.py:1791 cmd.rebuild
cmd.rebuild(selection='all', representation='everything')  # recreate out-of-sync representations

# src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create
cmd.create(name, selection, source_state=0, target_state=0, discrete=0,
           zoom=-1, quiet=1, singletons=0, extract=None, copy_properties=False)
# BACKUP: cmd.create("_bak_obj", "obj")           # default-args = ALL states (correct)
# WRONG:   cmd.create("_bak_obj", "obj", 1, 1)    # copies ONLY state 1 (silent multi-state loss)
# WRONG:   cmd.create("obj", "obj")               # self-copy DESTRUCTIVE

# src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete
cmd.delete(name)             # whole objects/selections; supports wildcards. Bare count_atoms after -> RAISES.

# src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
cmd.count_atoms(selection="(all)", quiet=1, state=ALL_STATES, domain='')
# Returns int. Use count_atoms("?obj") for possibly-deleted (safe, returns 0).

# src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
cmd.iterate(selection, expression, quiet=1, space=None)
# Residue signature idiom:
#   stored = pymol.Scratch_Storage(); stored.list = []
#   cmd.iterate("obj", "stored.list.append((chain,resi,resn))", space={'stored': stored})
#   sig = sorted(stored.list)

# src: tmp/pymol-src/modules/pymol/editing.py:800 cmd.remove
cmd.remove(selection, quiet=1)   # remove atoms WITHIN objects (substrate "remove group")

# src: tmp/pymol-src/modules/pymol/editing.py:937 cmd.fuse
cmd.fuse(selection1, selection2, mode=0, recolor=1, move=1)
# Single atom per selection. Copies obj-of-sele1 into obj-of-sele2, forms a bond. (substrate "add group")
```

---

## Proposed Design

### A. `apply_edit` — the sole sanctioned alter path

**Location:** `c14/pymol_layer/edit_ops.py` (NEW module, gate-exempt like molops.py/asset_manager.py).

**Class + signature (Python 3.6 plain class, injected cmd — mirrors `molops.py:80`):**
```python
class RestoreHandle(object):
    """Opaque restore handle returned by apply_edit. Carries the backup name +
    pre-edit atom count + pre-edit residue signature so restore() can verify
    the round-trip (SC2). Plain class (3.6-compatible, no @dataclass)."""
    def __init__(self, object_name, backup_name, pre_atom_count, pre_residue_signature):
        self.object_name = object_name
        self.backup_name = backup_name
        self.pre_atom_count = pre_atom_count
        self.pre_residue_signature = pre_residue_signature  # sorted [(chain,resi,resn), ...]

class EditOps(object):
    def __init__(self, cmd):
        self._cmd = cmd

    def apply_edit(self, edit_type, object_name, sele, **kwargs):
        # 1. BACKUP (default-args create = all states) + capture pre-edit signature
        handle = self._take_backup(object_name)
        # 2. THE EDIT (alter / remove / fuse -- the ONLY place cmd.alter is called)
        # 3. ALWAYS sort + rebuild (the alter->sort trap mitigation)
        # 4. return RestoreHandle
        ...

    def _take_backup(self, object_name):
        bak = "_bak_" + object_name
        # src: commanding.py:496 cmd.delete   (idempotent clear of stale backup)
        self._cmd.delete(bak)
        # src: creating.py:960 cmd.create     (default-args = ALL states)
        self._cmd.create(bak, object_name)
        # src: querying.py:1412 cmd.count_atoms
        n = self._cmd.count_atoms(object_name)
        if self._cmd.count_atoms(bak) != n:
            raise RuntimeError("backup atom-count mismatch")
        sig = self._collect_residue_signature(object_name)
        return RestoreHandle(object_name, bak, n, sig)

    def restore(self, object_name, backup_name, pre_atom_count=None, pre_residue_signature=None):
        # src: commanding.py:496 cmd.delete   (MUST delete first -- create into existing name MERGES)
        self._cmd.delete(object_name)
        # src: creating.py:960 cmd.create     (from backup)
        self._cmd.create(object_name, backup_name)
        # src: editing.py:1257 cmd.sort + viewing.py:1791 cmd.rebuild
        self._cmd.sort(object_name)
        self._cmd.rebuild(object_name)
        # VERIFY round-trip (SC2)
        if pre_atom_count is not None and self._cmd.count_atoms(object_name) != pre_atom_count:
            raise RuntimeError("restore atom-count mismatch")
        if pre_residue_signature is not None:
            if self._collect_residue_signature(object_name) != pre_residue_signature:
                raise RuntimeError("restore residue-identity mismatch")
        return object_name

    def restore_from_handle(self, handle):
        return self.restore(handle.object_name, handle.backup_name,
                            handle.pre_atom_count, handle.pre_residue_signature)

    def _collect_residue_signature(self, object_name):
        stored = type("S", (), {"list": []})()
        # src: editing.py:1490 cmd.iterate
        self._cmd.iterate(object_name, "stored.list.append((chain,resi,resn))",
                          space={"stored": stored})
        return sorted(stored.list)
```

**Edit op taxonomy** (the `edit_type` arg + the `cmd.*` sequence each translates to):

| edit_type | args | cmd.* sequence (all inside apply_edit) | Maps to requirement |
|-----------|------|----------------------------------------|---------------------|
| `point_mutation` | `sele` (e.g. `"obj and resi 12"`), `new_resn` | backup → `cmd.alter(sele, "resn='NEW'")` → `sort` → `rebuild` | EDIT-01 |
| `substrate_remove_group` | `group_sele` (e.g. `"obj and resn ETH and name O1"`) | backup → `cmd.remove(group_sele)` → `sort` → `rebuild` | EDIT-02 |
| `substrate_add_group` | `frag_atom_sele`, `target_atom_sele` | backup → `cmd.fuse(frag_atom_sele, target_atom_sele)` → `sort` → `rebuild` | EDIT-02 |
| `protonation_change` | `sele`, `new_resn` (e.g. HIS→HID) | backup → `cmd.alter(sele, "resn='HID'")` → `sort` → `rebuild` | EDIT-02 (protonation edit TYPE; researcher C owns the variant content) |

**Point mutation — alter vs wizard:** Phase 4 uses `cmd.alter` resn (the trap-triggering op the safety net must protect). The rotamer-correct `Mutagenesis` wizard (`wizard/mutagenesis.py:38`) is NOT headless-friendly (needs `pk1` picking + `PYMOL_DATA` rotamer `.pkl` files + `refresh_wizard`/`push_undo`/`frame`). Real sidechain-geometry rebuild is a Phase 5+ content concern. This keeps Phase 4 demonstrable headlessly while exercising the EXACT trap the safety net mitigates.

**Note on protonation H-placement:** `cmd.alter` resn only relabels. Actual H placement (`cmd.h_add`/`cmd.remove` of H) is researcher C's concern — but `h_add` ALSO needs a sort afterward (the built-in menu does `cmd.h_add(sele); cmd.sort(sele+" extend 1")`, `menu.py:751-752`). RECOMMEND (coordinate with researcher C): H-placement ops also route through an `edit_ops` helper (or a sibling sanctioned sort-after path) so the alter→sort discipline is uniform. The SC1 gate itself is on `cmd.alter` only; `h_add` is not `alter`, but the same trap discipline applies.

### B. Backup/Restore flow (verified mechanics)

```
take_backup(obj):
  delete("_bak_obj")          # idempotent (Pitfall 6)
  create("_bak_obj", "obj")   # default-args = ALL states (Pitfalls 2,3)
  assert count_atoms("_bak_obj") == count_atoms("obj")
  sig = sorted(iterate-collected (chain,resi,resn) tuples of "obj")
  return RestoreHandle(obj, "_bak_obj", count, sig)

apply_edit(...):
  handle = take_backup(obj)
  alter/remove/fuse            # THE edit (only place cmd.alter lives)
  sort(obj); rebuild(obj)      # ALWAYS (Pitfall 1)
  return handle

restore(handle):
  delete(obj)                  # MUST delete first (Pitfall 4)
  create(obj, "_bak_obj")      # default-args from backup
  sort(obj); rebuild(obj)
  assert count_atoms(obj) == handle.pre_atom_count          # SC2 atom count
  assert collect_residue_signature(obj) == handle.pre_residue_signature  # SC2 residue identity
```

**Does delete+create preserve the object NAME?** YES — `create(obj, ...)` creates an object named `obj`. The name is restored; the atom content is restored. **Does it preserve representation/scene?** NO (Pitfall 8) — by design; scene replay is Phase 6's job via on_enter MolActions.

### C. The sanctioned-alter gate (SC1) — `tools/check_alter_gate.py`

**Rule:** `cmd.alter` (any `*.alter(...)` Attribute call) may appear ONLY in `c14/pymol_layer/edit_ops.py`. Nowhere else in `c14/` or `tools/`.

**Mechanism:** AST-based (extends the `check_imports.py:44-74` AST pattern). Scan ALL `.py` under `c14/` (INCLUDING `pymol_layer/` — unlike check_imports which skips it) AND `tools/`. For each `ast.Call` whose `func` is an `ast.Attribute` with `attr == "alter"`, record it UNLESS the file path == `c14/pymol_layer/edit_ops.py`. (AST on `Attribute(attr='alter')` is precise — it catches `cmd.alter`, `self._cmd.alter`, `pymol.cmd.alter` uniformly, and won't false-positive on the word "alter" in comments/strings.)

**Allowlist:** exactly one file — `c14/pymol_layer/edit_ops.py`. (Protonation's resn-alter ALSO routes through `apply_edit`, so protonation code does NOT need its own alter call — keeping the allowlist to ONE module, per the objective's constraint.)

**Exit codes (Phase 1 convention, `check_citations.py:6-11`):** `0` = clean, `1` = violation (bare alter outside edit_ops.py), `2` = ERROR (AST parse failure / config).

**Grep alternative (lighter):** A `rg "\.alter\(" c14/ tools/` with the allowlist is simpler but AST is more robust (the project already has the AST precedent in `check_imports.py`). **Recommend the AST form** for airtightness; the grep form is acceptable as a faster CI pre-check. Either way, the gate starts GREEN from day one — confirmed: NO `cmd.alter` exists anywhere in the repo yet (`rg "cmd\.alter|\.alter\("` in c14/+tools/ returns nothing).

**Trap demo placement:** Do NOT reproduce the bare-alter trap in a gated file (it would violate the gate). Document the trap in `edit_ops.py`'s module docstring + this RESEARCH.md. The SC1 headless test proves the MITIGATION (apply_edit → post-edit byres returns expected atoms), not the trap.

### D. Per-enzyme minimum-coverage scan (SC5) — `tools/check_edit_coverage.py` + headless round-trip

SC5 has two parts: (a) manifest coverage (pure-Python, WSL, fast CI gate) and (b) restore round-trip (headless smoke).

**Data files (Phase 4 = PLACEHOLDERS; real content is Phase 5+):**
- `c14/data/cast.json` — enzymes represented so far. Phase 4 placeholder: `{"enzymes": [{"id": "fixture_enzyme_1", "fixture": "_edit_smoke.pdb"}]}`. Grows in Phase 9 (real cast).
- `c14/data/edits.json` — known-edit entries per enzyme. Phase 4 placeholder: one demo entry per enzyme: `{"fixture_enzyme_1": [{"edit_type": "point_mutation", "sele": "resi 1", "new_resn": "GLY"}]}`.

**(a) `tools/check_edit_coverage.py` (pure-Python, WSL, mirrors `check_citations.py` structure):**
- Load `cast.json` + `edits.json`.
- For each enzyme in `cast.json`: assert it has ≥1 entry in `edits.json`.
- Exit codes (Phase 1 convention): `0` = PASS (all enzymes have ≥1 known-edit entry), `1` = FAIL (some enzyme missing), `2` = ERROR (malformed JSON / missing file).
- Stays green as cast grows: data-driven from `cast.json` — add an enzyme → scan picks it up → FAILS until `edits.json` has an entry (forces coverage discipline).

**(b) Headless round-trip smoke (`tools/edit_smoke.py` via `run_headless.sh`):**
- For each enzyme with a fixture: load fixture → `take_backup` → `apply_edit` (the edit_type from `edits.json`) → assert post-edit `byres` selection returns expected atoms (SC1) → `restore` → assert `count_atoms` + residue signature == pre-edit (SC2) → print `SMOKE_RESULT: PASS`.

### E. Integration with the built contract (Phase 3)

- `molops.py:118-119` `NotImplementedError` branches for `edit`/`protonate`/`restore` → Phase 4 replaces with delegation to an injected `EditOps` (constructor gains an `editops` arg, mirroring the `asset_manager` arg at `molops.py:80`).
- `MolAction` (`model.py:26`) stays pure-data: the `edit` op carries `edit_type`/`sele`/`new_resn`/`group_sele`/... in `args`. NO pymol type named in `c14/` root (AST gate stays green).
- The `# src:` citation convention (`molops.py:33-37`) extends to every `cmd.alter/sort/rebuild/create/delete/remove/fuse/iterate/count_atoms` call in `edit_ops.py`. The existing `test_molops.py:206-229` citation test pattern extends to `tests/test_edit_ops.py`.
- The `SMOKE_RESULT: PASS` sentinel + `run_headless.sh` harness (`run_headless.sh:46`) is reused verbatim — `edit_smoke.py` follows the `molops_smoke.py` shape (`molops_smoke.py:53-180`).

---

## Headless Test Strategy

### Pure-Python unit tests (`tests/test_edit_ops.py`, WSL python3.6, NO pymol) — MockCmd pattern

Extends the `test_molops.py:39-65` MockCmd pattern. A `RecordingCmd` records `(name, args, kwargs)` for `alter/sort/rebuild/create/delete/remove/fuse/iterate`; `count_atoms` returns a configurable int.

| Test | Asserts |
|------|---------|
| `test_apply_edit_point_mutation_calls` | apply_edit("point_mutation",...) calls create(bak,obj) → alter(sele,resn=) → sort(obj) → rebuild(obj), IN ORDER. |
| `test_apply_edit_always_sorts_after_alter` | For EVERY edit_type, the call sequence has sort+rebuild immediately after the mutating call. (SC1 unit-level.) |
| `test_apply_edit_takes_backup_first` | create("_bak_obj","obj") appears BEFORE any alter/remove/fuse. |
| `test_take_backup_uses_default_args_create` | create called with NO source_state/target_state (default-args = all states). Asserts NOT (1,1). |
| `test_take_backup_deletes_stale_backup_first` | delete("_bak_obj") called before create("_bak_obj",...). |
| `test_restore_deletes_before_create` | restore() calls delete(obj) BEFORE create(obj,bak) (Pitfall 4). |
| `test_restore_verifies_atom_count` | restore() raises when post-restore count != pre-restore count (mock returns mismatched count). |
| `test_restore_verifies_residue_signature` | restore() raises when post-restore signature != pre-restore signature. |
| `test_restore_handle_carries_signature` | RestoreHandle.pre_residue_signature is the sorted (chain,resi,resn) list. |
| `test_unknown_edit_type_raises` | apply_edit("bogus",...) raises ValueError. |
| `test_citations_present_in_source` | Every cmd.* call in edit_ops.py carries a `# src:` comment (extends `test_molops.py:206-229`). |
| `test_molops_edit_delegates_to_editops` | molops.apply(MolAction("edit",...)) calls editops.apply_edit (Phase 4 boundary replacement). |

### Headless smoke (`tools/edit_smoke.py` via `bash tools/run_headless.sh tools/edit_smoke.py`)

Follows `molops_smoke.py:53-180` shape. Uses a NEW committed 2-residue peptide fixture `c14/data/assets/bundled/_edit_smoke.pdb` (e.g. ALA-GLY, ~10-15 atoms — enough that a resn swap + byres + restore are all meaningful; network-independent).

**Stages (each prints `SMOKE: PASS|FAIL <name>`; final `SMOKE_RESULT: PASS` iff no fails):**
```
1. load:           cmd.load(_edit_smoke.pdb, "pep")          # count_atoms("pep") > 0
2. backup:         editops._take_backup("pep")               # count_atoms("_bak_pep") == count_atoms("pep")
3. pre_signature:  collect residue signature of "pep"        # [(A,1,ALA),(A,2,GLY)] (sorted)
4. SC1 byres:      editops.apply_edit("point_mutation","pep","pep and resi 1",new_resn="GLY")
                   # post-edit: count_atoms("byres (pep and resi 1)") == expected (NO silent corruption)
                   # count_atoms("pep and resi 1 and resn GLY") > 0  (the swap took)
5. SC2 restore:    editops.restore_from_handle(handle)
                   # count_atoms("pep") == pre_atom_count
                   # collect_residue_signature("pep") == pre_signature  (residue identity restored)
6. backup_independence: (BONUS) after backup, alter the LIVE obj; assert _bak_pep count+sig UNCHANGED
7. substrate_remove: apply_edit("substrate_remove_group","pep",group_sele="pep and resi 2 and name CA")
                   # count_atoms decreased; restore returns original
8. protonation_change: apply_edit("protonation_change","pep","pep and resi 1",new_resn="HID")
                   # resn changed; restore returns original
9. final:          print SMOKE_RESULT: PASS (iff no FAILS)
```

**Critical harness rules (reuse from `molops_smoke.py:12-22`):**
- The bat ALWAYS exits 0 (`run-conda-pymol.bat`; `run_headless.sh:8-12`) → verdict from `^SMOKE_RESULT: PASS` stdout sentinel, NOT `$?`.
- `__file__` in a PyMOL-run script resolves to pymol's `__init__.py` (`molops_smoke.py:17-20`) → use `os.getcwd()` (= repo root) + `import c14.paths` to locate the fixture.
- `pymol.finish_launching()` before any `cmd.*` call (`molops_smoke.py:70`).
- Inject the REAL `pymol.cmd` into `EditOps` (the smoke proves the real API contract; unit tests prove the dispatch logic).
- Run from repo root: `bash tools/run_headless.sh tools/edit_smoke.py`. Timeout 150s (`run_headless.sh:27`).

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `cmd.create(bak, src, 1, 1)` for backup | `cmd.create(bak, src)` default-args (all states) | Phase 3 empirical correction (STATE.md:84) | Phase 4 MUST use default-args; `1,1` silently drops multi-state data. |
| "cmd.create is a no-op" (PITFALLS.md Pitfall 3 original claim) | EMPIRICALLY CORRECTED — create is NOT a no-op for a new target; real gotchas are `1,1`-drops-multi-state + destructive-self-copy | Phase 3 (STATE.md:84) | Phase 4 backup is straightforward default-args create; no no-op workaround needed. |
| Mutagenesis wizard for point mutation | `cmd.alter` resn (Phase 4 mechanics); wizard deferred | Phase 4 boundary decision | Headless-demonstrable; rotamer geometry is Phase 5+ content. |

**Deprecated/outdated for this project:**
- `setenv.bat` / `wsl2win_cp.sh` (spec.md references) — DO NOT EXIST (AGENTS.md). Use `run-conda-pymol.bat` only.
- Legacy `pmgqt`/Tk — modern `pymol.Qt` only (Phase 6).
- `cmd.alter` without `cmd.sort` — never sanctioned (SC1 gate).

---

## Phase 4 Boundary (DELIVERS vs DEFERS)

**Phase 4 DELIVERS (engineering mechanics + placeholder fixtures, headlessly demonstrable):**
- `c14/pymol_layer/edit_ops.py`: `EditOps.apply_edit` (4 edit types) + `take_backup` + `restore` + `RestoreHandle` — the sole sanctioned `cmd.alter` path, always sort+rebuild.
- `tools/check_alter_gate.py`: AST gate enforcing "no `cmd.alter` outside edit_ops.py" (SC1).
- `tools/check_edit_coverage.py`: per-enzyme manifest coverage scan, exit 0/1/2 (SC5 part a).
- `tools/edit_smoke.py`: headless apply_edit + backup/restore round-trip smoke (SC1 byres + SC2 round-trip).
- `c14/data/assets/bundled/_edit_smoke.pdb`: committed 2-residue peptide fixture (no network).
- `c14/data/cast.json` + `c14/data/edits.json`: PLACEHOLDER manifests (one demo enzyme + one demo edit entry).
- `tests/test_edit_ops.py`: MockCmd unit tests (dispatch order, sort-after-alter, backup-first, delete-before-create, citation presence).
- `molops.py`: `edit`/`protonate`/`restore` branches delegate to `EditOps` (replace `NotImplementedError`).

**Phase 4 DEFERS to Phase 5+ (do NOT build now):**
- Real cited enzyme content / real PDB IDs (CITE-01 per-claim approval — Phase 5+/9).
- Real per-enzyme edit-table entries with scientifically-correct residues (Phase 5.1 edit-node contract + Phase 9 cast).
- Rotamer-correct sidechain geometry rebuild (the `Mutagenesis` wizard / `cmd.fragment`+`fuse` path) — Phase 4's point mutation is a resn relabel; real geometry is content-phase.
- Real curated protonation variant sets (researcher C owns; Phase 4 only proves backup/restore works for the protonation_change edit TYPE).
- Scene/representation replay after restore (Phase 6 controller re-emits on_enter MolActions).
- The edit-routing lookup logic (known→branch, unknown→bad-ending pool) — another researcher owns routing; Phase 4 owns the SAFE EDIT application + backup/restore mechanics only.

**Citation gate boundary:** Phase 4 builds MECHANICS on placeholder/example fixtures (a dummy 2-residue peptide). Real per-claim content approval (CITE-01) is Phase 5+. Phase 4 must be demonstrable headlessly with fixtures, NOT blocked on real PDB approval.

---

## Open Questions

1. **`substrate_add_group` (fuse) headless robustness**
   - What we know: `cmd.fuse` (`editing.py:937`) needs a single-atom selection in each of two objects. The fragment must be loaded as its own object first.
   - What's unclear: whether `fuse` headless (no `pk1`) reliably bonds when given explicit single-atom selections (it's documented for `pk1`/`pk2` defaults but accepts arbitrary selections). The mutagenesis wizard uses `fuse` indirectly via `bond`+`create` (`mutagenesis.py:356-362`).
   - Recommendation: the `edit_smoke.py` should include ONE `substrate_add_group` stage; if fuse proves flaky headless, fall back to documenting substrate_add as "load fragment + fuse" and exercising only `substrate_remove_group` + `point_mutation` + `protonation_change` as the three SC2 edit types (remove + alter cover the trap; add is a bonus). LOW confidence on fuse headless reliability until the smoke runs.

2. **Multi-state fixtures**
   - What we know: default-args `create` copies ALL states; `1,1` drops them.
   - What's unclear: Phase 4 fixtures are single-state (a peptide). The multi-state pitfall (Pitfall 2) is verified but not re-exercised on a multi-state backup in Phase 4.
   - Recommendation: keep Phase 4 fixtures single-state; add a multi-state round-trip test only if/when a multi-state structure enters the cast (Phase 9). Document the default-args rule as the standing mitigation.

3. **Protonation H-placement routing**
   - What we know: `cmd.alter` resn (HIS→HID) is the protonation_change edit; `cmd.h_add`/`cmd.remove` H need a sort too (`menu.py:751-752`).
   - What's unclear: whether researcher C's ProtonationManager routes H-placement through `edit_ops` or a sibling sanctioned sort-after path.
   - Recommendation: coordinate with researcher C — the SC1 gate is on `cmd.alter` only, but RECOMMEND H-placement also go through an `edit_ops` helper so the sort discipline is uniform. The allowlist stays at ONE module (`edit_ops.py`).

---

## Sources

### Primary (HIGH confidence — PyMOL 2.5.0 source, read directly)
- `tmp/pymol-src/modules/pymol/editing.py:1424` — `cmd.alter` def + docstring; **:1457-1460** the alter→sort WARNING (the trap, primary-source).
- `tmp/pymol-src/modules/pymol/editing.py:1257` — `cmd.sort` def + docstring (recomputes ordering after alter).
- `tmp/pymol-src/modules/pymol/editing.py:1490` — `cmd.iterate` def (residue-signature collection).
- `tmp/pymol-src/modules/pymol/editing.py:800` — `cmd.remove` def (substrate remove group).
- `tmp/pymol-src/modules/pymol/editing.py:937` — `cmd.fuse` def (substrate add group).
- `tmp/pymol-src/modules/pymol/editing.py:919` — `cmd.attach` def (single-atom add; needs pk1).
- `tmp/pymol-src/modules/pymol/editing.py:1535` — `cmd.alter_state` def (coordinate edits; not Phase 4).
- `tmp/pymol-src/modules/pymol/editing.py:47` — `_iterate_prepare_args` (alter/iterate namespace/space mechanism).
- `tmp/pymol-src/modules/pymol/creating.py:960` — `cmd.create` def + docstring (backup; default-args = all states; "create states in an existing object" = MERGE pitfall).
- `tmp/pymol-src/modules/pymol/commanding.py:496` — `cmd.delete` def (restore step 1; supports wildcards).
- `tmp/pymol-src/modules/pymol/querying.py:1412` — `cmd.count_atoms` def (round-trip verify; `?`-prefix safe form).
- `tmp/pymol-src/modules/pymol/viewing.py:1791` — `cmd.rebuild` def (representation sync after alter).
- `tmp/pymol-src/modules/pymol/viewing.py:1704` — `cmd.refresh` def (redraw; not needed headless).
- `tmp/pymol-src/modules/pymol/wizard/mutagenesis.py:38` — `Mutagenesis` wizard (NOT headless: pk1 + PYMOL_DATA rotamer pkls + refresh_wizard/push_undo/frame; uses cmd.alter internally at :346,:474-475).
- `tmp/pymol-src/modules/pymol/menu.py:751-752` — built-in idiom `cmd.h_add(sele); cmd.sort(sele+" extend 1")` (confirms sort-after-alter discipline).
- `tmp/pymol-src/modules/pymol/cmd.py:350` + `helping.py:560` — `byres` selection keyword (relies on canonical ordering = the trap victim).

### Secondary (HIGH confidence — this repo's built contract + empirical Phase 3 findings)
- `c14/pymol_layer/molops.py:80,118-119` — MolOps inject-cmd pattern + the `NotImplementedError` Phase 4 boundary.
- `c14/story/model.py:26` — MolAction pure-data contract (op/target/args; no pymol import).
- `c14/pymol_layer/asset_manager.py:63` — AssetManager inject-cmd precedent.
- `tools/check_imports.py:44-74` — AST-gate precedent to extend for the alter gate.
- `tools/check_citations.py:6-11` — Phase 1 three-way exit-code convention (0/1/2).
- `tools/run_headless.sh:46` — `SMOKE_RESULT: PASS` sentinel harness (bat always exits 0).
- `tools/molops_smoke.py:53-180` — headless smoke shape to mirror.
- `tools/api_sanity_smoke.py:145-159` — empirical `create` backup verification (default-args correct; `1,1` drops multi-state; self-copy destructive).
- `.planning/STATE.md:84` — Phase 3 empirical correction of the `cmd.create` pitfall.
- `tests/test_molops.py:39-65,206-229` — MockCmd + citation-test patterns to extend.
- `rg "cmd\.alter|\.alter\("` over c14/+tools/ — confirms NO bare alter exists yet (gate starts green).

### Tertiary (LOW confidence — needs smoke-run validation)
- `cmd.fuse` headless reliability with explicit (non-`pk1`) single-atom selections — Open Question 1; validate in `edit_smoke.py`.

---

## Metadata

**Confidence breakdown:**
- Standard stack (APIs + signatures): **HIGH** — every API read at file:line in PyMOL 2.5.0 source.
- alter→sort trap: **HIGH** — primary-source documented in the `cmd.alter` docstring (`editing.py:1457-1460`) + `cmd.sort` docstring + `menu.py` idiom.
- Backup/restore mechanics: **HIGH** — `create`/`delete` semantics from source + Phase 3 empirical verification; Pitfalls 2-6 empirically grounded.
- apply_edit design + op taxonomy: **HIGH** — direct extension of the proven Phase 3 inject-cmd + molops-dispatch pattern.
- Sanctioned-alter gate (SC1): **HIGH** — AST precedent exists (`check_imports.py`); no bare alter exists yet (gate starts green).
- Per-enzyme coverage scan (SC5): **HIGH** — mirrors `check_citations.py` structure + Phase 1 exit-code convention.
- Headless test strategy: **HIGH** for unit tests + SC1/SC2 smokes; **LOW** for `substrate_add_group` (fuse) headless reliability (Open Question 1).
- Point-mutation alter-vs-wizard: **HIGH** — wizard source confirms it's GUI/rotamer-bound; alter resn is the headless-appropriate Phase 4 form.

**Research date:** 2026-08-15
**Valid until:** 2026-09-14 (stable — PyMOL 2.5.0 APIs are frozen; the only drift risk is the Phase 5+ real-content layering, which this research explicitly defers).
