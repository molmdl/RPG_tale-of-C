# Phase 3: PyMOL cmd Layer + Asset Management (Headless) - Research

**Researched:** 2026-08-14
**Domain:** PyMOL 2.5.0 `pymol.cmd.*` API surface (headless) + WSL→Windows bridge + AssetManager/MolOps design on the existing pure-Python domain tier
**Confidence:** HIGH (every API claim and every bridge behavior below was **empirically verified** by running scripts through `run-conda-pymol.bat -cq` from WSL, and every `file:line` citation was read against `tmp/pymol-src/modules/pymol/` and re-verified after symlink restoration)

## Summary

This is the first phase to touch the real PyMOL 2.5.0 API. The dominant risks going in were (1) whether the WSL→Windows headless bridge actually works with usable exit codes, (2) the two named API pitfalls (`cmd.create(obj,sele,1,1)` and `cmd.fetch` async/CIF defaults), and (3) designing AssetManager + MolOps cleanly on the Phase 1/2 pure-Python domain tier. **I empirically verified the bridge by running 11 probe scripts through the bat** — and in doing so **overturned two documented assumptions** (the `create(…,1,1)` "no-op" claim does not reproduce as stated; `count_atoms` on a deleted object raises rather than returns 0) and **discovered three undocumented gotchas** (the process exit code is ALWAYS 0 through the bat regardless of script outcome; `__file__` in a PyMOL-run script resolves to the pymol package's `__init__.py`, not the script's path; WSL env vars don't reach the Windows PyMOL process). These findings directly reshape the smoke-harness contract and the AssetManager path strategy.

The bridge **works**: `import pymol; pymol.finish_launching()` succeeds under `-cq`, `cmd.load` of a local PDB returns the right `count_atoms`, `cmd.fetch` of PubChem CID 2244 with `type='cid', async_=0, path=<abs dir>` lands the file at that dir with `count_atoms=21`, and network IS available in the Windows env. The `cmd.fetch` pitfalls (CIF default, `path=.` cwd default, async-when-interactive) are all confirmed in source (`importing.py:1346,1379-1381,1382-1383`) and mitigated by always passing `type=, async_=0, path=`. The `cmd.create` pitfall is **empirically corrected**: `create(backup,src,1,1)` is NOT a no-op for a new target — it copies only state 1 (incomplete backup for multi-state objects); `create(obj,obj,1,1)` self-copy is DESTRUCTIVE (raises + corrupts); the working backup is `cmd.create(backup, source)` with default args (all states) — exactly what `ARCHITECTURE.md:304` already recommends.

**Primary recommendation:** Split Phase 3 into 3 plans: (01) headless harness + api-sanity smoke + source-citation convention + `.gitignore` for the downloaded-asset dir [GATE — must land first]; (02) AssetManager (bundle + fetch + path management + headless test); (03) MolOps (MolAction→cmd.* mapping + citations + headless smoke). The smoke harness MUST signal pass/fail via a `SMOKE_RESULT:` stdout sentinel + bash grep — **not** via `$?` (which is always 0 through the bat).

---

## 1. Empirical Headless Verification (HIGHEST PRIORITY — gates everything)

**Status: BRIDGE WORKS.** Verified by 11 probe scripts run from WSL through `run-conda-pymol.bat -cq` (scripts lived in gitignored `tmp/`; cleaned up after; outputs captured to `/tmp/opencode/`).

### The exact working incantation (verified)
```bash
# MUST run with cwd = repo root (so os.getcwd()=workspace and `import c14` works — see gotcha #3)
WIN_SCRIPT=$(wslpath -w "$(pwd)/tools/api_sanity_smoke.py")
timeout 150 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq $WIN_SCRIPT" > /tmp/opencode/smoke_out.txt 2>&1
# verdict: GREP STDOUT (NOT $? — see gotcha #1):
if grep -q "^SMOKE_RESULT: FAIL" /tmp/opencode/smoke_out.txt; then echo "SMOKE FAILED"; else echo "SMOKE PASSED"; fi
```
- `wslpath -w <wsl-path>` converts to a reliable Windows path (AGENTS.md's `\\wsl$\…` form is flakier — use `wslpath -w`).
- `timeout 150` (not 90) for any fetch-bearing script — network fetch needs headroom; 90s is too tight.
- Bash redirect `> file 2>&1` captures PyMOL stdout+stderr (the tracebacks print to stderr).

### What was confirmed works
| Check | Result |
|---|---|
| `import pymol; from pymol import cmd` | OK |
| `pymol.finish_launching()` | OK (call it explicitly; completes startup so `cmd.*` is ready) |
| `-cq` suppresses GUI | OK (no display needed) |
| `cmd.load(<abs pdb>, "probe")` | OK; `cmd.count_atoms("probe") == 3` |
| `cmd.count_atoms` usable | OK (returns int) |
| `cmd.fetch("2244","asp",type="cid",async_=0,path=<abs dir>)` | OK; `count_atoms("asp")==21`; file landed at `<abs dir>/cid_2244.sdf` |
| Network (PubChem) reachable from Windows env | YES |
| stdout/stderr capture | OK |
| `cmd.show("sticks","probe")` + `cmd.count_atoms("probe & rep sticks")` | OK; `rep` selection keyword WORKS (returns 3) |
| `cmd.select("s","probe and name C1")` + `count_atoms("s")==1` | OK |
| `cmd.zoom("probe")` / `cmd.color("green","probe")` | OK (no crash) |
| `cmd.create("bak","probe")` defaults | OK; 3 atoms, all states copied |
| `cmd.delete("probe")` + `count_atoms("?probe")==0` | OK (with `?` prefix) |

### Gotchas discovered (all empirically confirmed — these reshape the design)

**Gotcha #1 — CRITICAL: the process exit code is ALWAYS 0 through the bat, regardless of script outcome.**
- `cmd.exe /c "exit 7"` → `$? = 7` (cmd.exe propagates). But `cmd.exe /c "C:\src\run-conda-pymol.bat -cq <script>"` → `$? = 0` for EVERY one of: clean exit, `sys.exit(1)`, `os._exit(1)`, `cmd.quit(1)`, uncaught `RuntimeError`, uncaught `ZeroDivisionError`, uncaught `pymol.CmdException`. Tracebacks print to stderr, but the process still exits 0.
- **Root cause (read from the bat):** the bat runs `python %ENVPATH%\Lib\site-packages\pymol\__init__.py %*` then `call conda deactivate`. The `call conda deactivate` AFTER python overwrites `%ERRORLEVEL%` to 0, and the bat has no `exit /b %ERRORLEVEL%`. So the final errorlevel is from `conda deactivate`, not python. (PyMOL's own `parsing.run_file` also wraps script exec in a try/except that prints tracebacks and swallows exceptions — so even without the bat, `sys.exit`/`raise` don't propagate.)
- **Implication:** `$?` CANNOT signal assertion pass/fail. The AGENTS.md "exit 0 = clean; nonzero = crash" convention means "PyMOL launched" vs "infra failed (timeout=124, segfault=139, conda-activation fail)". **Success criterion #1 ("passes with exit code 0") must be REINTERPRETED**: the literal exit code is uninformative; the smoke MUST print a `SMOKE_RESULT: PASS|FAIL` stdout sentinel and the bash harness greps for `^SMOKE_RESULT: FAIL`. Exit 0 only confirms the run happened.
- **Do NOT** modify the bat (it's user-owned at `/mnt/c/src/`; AGENTS.md says don't alter the env). Don't try `os._exit`/`cmd.quit` to force a code — they don't escape the bat's `conda deactivate`.

**Gotcha #2 — `__file__` in a PyMOL-run script = the pymol package's `__init__.py`, NOT the script's path.**
- Empirically: `__file__` = `'C:\\Users\\nglok\\.conda\\envs\\chemtools-win10\\Lib\\site-packages\\pymol\\__init__.py'` regardless of where the script lives. PyMOL's runner (`parsing.run_file`/`execfile`) execs the script in the pymol module's globals, so `__file__` is pymol's.
- **Implication:** smoke/asset scripts CANNOT use `__file__` to locate themselves or bundled fixtures (you'd write/read inside `site-packages/pymol/` — which is exactly what happened in an early probe: `_probe.pdb` and `cid_2244.sdf` got written into the conda env's `pymol/` dir). Use `os.getcwd()` (= cmd.exe cwd = repo root when run with `workdir=repo-root`) and `import c14.paths` (whose `__file__` IS correct because c14 is a normally-imported module).

**Gotcha #3 — `os.getcwd()` in the PyMOL process = the cmd.exe cwd = the repo root** when run with `workdir=repo-root. Relative paths in `cmd.load`/`cmd.fetch` resolve against this. **The harness MUST run the smoke with cwd=repo-root.** (This is also why `import c14` works — `sys.path` includes `''` = cwd = repo root.)

**Gotcha #4 — `import c14.paths` works headlessly** (no explicit path manipulation needed when cwd=repo-root, because `sys.path` includes `''`=cwd). Verified: `c14.paths._PACKAGE_ROOT` = `WindowsPath('…/RPG_tale-of-C/c14')`, `data_path()` and `selfcheck()` resolve correctly. Belt-and-suspenders: smoke's first lines `import sys, os; sys.path.insert(0, os.getcwd())`.

**Gotcha #5 — WSL env vars do NOT propagate to the Windows PyMOL process** (`PROBE_EXIT_MODE=clean` was invisible to the script — all 4 modes ran as `clean`). **Don't configure headless scripts via env vars.** Use a separate script per scenario, or a config FILE the script reads, or (untested) command-line args after the script path.

**Gotcha #6 — `pymol.finish_launching()` is needed** (or `-c` handles init; calling it explicitly is safe and recommended — completes PyMOL startup). `-cq` suppresses the GUI.

**Gotcha #7 — `async_=0` DOES block** (sync fetch). Confirmed: `count_atoms` was 21 immediately after `cmd.fetch(..., async_=0, ...)`. Per source `importing.py:1382-1383`, the API default `async_=0` is sync in 2.5.0; the async-by-default behavior is interactive/CLI only (`if async_ < 0: async_ = not quiet`). Still ALWAYS pass `async_=0` explicitly (defense against the interactive default).

---

## 2. API Surface Consolidation (file:line, signature, post-condition, pitfall)

Every signature below was read from `tmp/pymol-src/modules/pymol/` and the cited line re-verified after symlink restoration. Post-conditions were empirically verified unless noted.

### cmd.load — `importing.py:635`
```python
# src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
def load(filename, object='', state=0, format='', finish=1, discrete=-1,
         quiet=1, multiplex=None, zoom=-1, partial=0, mimic=1,
         object_props=None, atom_props=None, *, _self=cmd):
```
- **Path handling:** `filename` is a file path or URL; PyMOL resolves RELATIVE paths against the cmd.exe cwd (Pitfall 1). Always pass an ABSOLUTE path: `str(c14.paths.data_path("data","assets","bundled",<file>.pdb))`.
- **Returns:** `None` on success (empirically `ret=None` even though atoms loaded). **DO NOT rely on the return value** — use `cmd.count_atoms(object)` as the post-condition.
- **Post-condition:** `cmd.count_atoms(object) > 0`.
- **Pitfall:** relative paths break under headless (cwd = cmd.exe cwd). Use c14.paths (absolute).

### cmd.fetch — `importing.py:1323` — THE NAMED PITFALLS (all confirmed in source)
```python
# src: tmp/pymol-src/modules/pymol/importing.py:1323 cmd.fetch
def fetch(code, name='', state=0, finish=1, discrete=-1, multiplex=-2,
          zoom=-1, type='', async_=0, path='', file=None, quiet=1,
          _self=cmd, **kwargs):
```
- **Pitfall 5a — CIF default** (`importing.py:1346`, `_multifetch:1284`): `type=''` → resolves to `get('fetch_type_default')` = `cif` (changed in 1.7.6). MUST pass `type='pdb'` (proteins) or `type='cid'`/`'sid'` (PubChem) explicitly. Code that parses PDB records would silently get CIF.
- **Pitfall 5b — `path` default = `.` (cwd)** (`importing.py:1379-1381`): `if not path: path = _self.get('fetch_path') or '.'`. Downloads land in cwd unless `path=` is explicit. MUST pass `path=<absolute plugin data dir>` for cwd-independence.
- **Pitfall 5c — async default**: API default `async_=0` is SYNC in 2.5.0 (`importing.py:1382-1383`: only `if async_ < 0` does it become `not quiet`). But ALWAYS pass `async_=0` explicitly (the interactive/CLI default differs).
- **Network:** REQUIRED (`importing.py:1367-1368`). PubChem URL: `https://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?{type}={code}&disopt=3DSaveSDF` (`importing.py:1138-1141`). Download filename: `{type}_{code}.sdf` (`importing.py:1181`) → lands at `path/cid_<code>.sdf`. cmd.fetch SKIPS download if the file already exists (`importing.py:1211-1213`) — free idempotent cache.
- **Empirically:** `cmd.fetch("2244","asp",type="cid",async_=0,path=<abs dir>)` → `count_atoms("asp")==21`; `cid_2244.sdf` landed at `<abs dir>/cid_2244.sdf`. Network IS available in the Windows env.
- **Post-condition:** `cmd.count_atoms(name) > 0` AND `os.path.exists(os.path.join(path, "cid_"+str(code)+".sdf"))`.
- **Offline plan:** surface a clear error if fetch fails (Pitfall 5 mitigation: "fetch failed — offline? firewall?"); the api-sanity smoke should report fetch failure but NOT hard-fail the whole smoke (so the non-network stages still validate).

### cmd.show / cmd.hide / cmd.show_as — `viewing.py:491` / `:568` / `:528`
```python
# src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show
def show(representation="wire", selection="", *, _self=cmd):
# src: tmp/pymol-src/modules/pymol/viewing.py:568 cmd.hide
def hide(representation="everything", selection="", *, _self=cmd):
# src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as   (turns ON rep AND off all others)
def show_as(representation="wire", selection="", *, _self=cmd):
```
- **Representation names** (`viewing.py:503-506`): lines, spheres, mesh, ribbon, cartoon, sticks, dots, surface, labels, extent, nonbonded, nb_spheres, slice, dashes, angles, dihedrals, cgo, cell, callback, everything.
- **Post-condition ("representation visible" headless assertion):** `cmd.count_atoms("<obj> & rep <repname>")` — the `rep <name>` selection keyword selects atoms with that representation enabled. **Empirically confirmed:** after `cmd.show("sticks","probe")`, `cmd.count_atoms("probe & rep sticks") == 3`. The `rep` keyword WORKS (it's C-backed; `selector.py` is a 7-line stub, so this was verified empirically, not from source). This is the headless "rep is visible" assertion for success criterion #3.
  - `cmd.show_as` is the cleanest "set the scene's representation" for the game (turns off other reps atomically); prefer it over show+hide pairs when the intent is "show ONLY this rep".

### cmd.select — `selecting.py:48`
```python
# src: tmp/pymol-src/modules/pymol/selecting.py:48 cmd.select
def select(name, selection="", enable=-1, quiet=1, merge=0, state=0, domain='', _self=cmd):
```
- **Selection syntax:** standard PyMOL atom-selection expressions (`"obj and name CA"`, `"chain A"`, `"resi 142 around 5"`, `"obj & rep sticks"`). `selector.process()` is applied internally.
- **Post-condition:** `cmd.count_atoms(name) == <expected>`. (`cmd.select` also returns the count empirically, but `count_atoms(name)` is the clean assertion.)

### cmd.zoom — `viewing.py:65`
```python
# src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom
def zoom(selection="all", buffer=0.0, state=0, complete=0, animate=0, *, _self=cmd):
```
- **No headless-assertable post-condition** (modifies the view; no display). Assert "doesn't crash" (wrap in try/except).

### cmd.color — `viewing.py:1858`
```python
# src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
def color(color, selection="(all)", quiet=1, flags=0, *, _self=cmd):
```
- **Color:** name (green, cyan, yellow, red, blue, white, carbon, …) or number; resolved via `_self._interpret_color` (`viewing.py:1895`).
- **No headless-assertable post-condition** (could verify via `cmd.get_object_color_index` `querying.py:819` or `cmd.iterate` on color, but overkill). Assert "doesn't crash".

### cmd.delete — `commanding.py:496`
```python
# src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete
def delete(name, _self=cmd):
```
- **Post-condition: `cmd.count_atoms("?" + name) == 0`** — MUST use the `?` prefix. **Empirically:** `cmd.count_atoms("deleted_obj")` (no `?`) RAISES `pymol.CmdException('Invalid selection name "deleted_obj"')`; `cmd.count_atoms("?deleted_obj")` returns 0 (safe). The `?` is PyMOL's "existing-objects-only" selector prefix (used throughout the source, e.g. `creating.py:1001 count_states('?' + name)`).
  - Alternative: `name not in cmd.get_names("objects")` (`querying.py:1148`).
- **PITFALL:** bare `count_atoms(name)` on a deleted/nonexistent object RAISES (does NOT return 0). This overturned my initial assumption.

### cmd.create (backup) — `creating.py:960` — THE NAMED PITFALL (EMPIRICALLY CORRECTED)
```python
# src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create
def create(name, selection, source_state=0, target_state=0, discrete=0,
           zoom=-1, quiet=1, singletons=0, extract=None,
           copy_properties=False, _self=cmd):
```
- **EMPIRICALLY CORRECTED PITFALL.** `PITFALLS.md`/`SUMMARY.md` claim `cmd.create(obj,sele,1,1)` is a "silent no-op" (citing a "prior spike" + `creating.py:960`). **This did NOT reproduce for the backup use case (new target object):**
  - `cmd.create("bak_nop", "src", 1, 1)` on a single-state source → **3 atoms** (WORKS, not a no-op).
- **The ACTUAL gotchas (confirmed empirically with a 2-state source):**
  1. **`create(backup, src, 1, 1)` copies ONLY state 1 → loses states 2+ (incomplete backup).** Verified: `cmd.create("bak_11","multi",1,1)` → `count_states==1`; `cmd.create("bak_def","multi")` (defaults) → `count_states==2`. Both have 3 atoms, but `1,1` silently drops the extra states. For a multi-state structure this is silent data loss — the "restore" safety net would then restore an incomplete object.
  2. **`create(obj, obj, 1, 1)` (self-copy, target name == source object) is DESTRUCTIVE** — RAISES `CmdException('Failed to Create Object')` AND corrupts/deletes the source object (`count_atoms("src")` then raises 'Invalid selection name'). NEVER use the same name for target and source.
- **WORKING backup invocation (confirmed):** `cmd.create(backup_name, source_name)` with DEFAULT args (`source_state=0, target_state=0` = copy ALL states). This is exactly what `ARCHITECTURE.md:304` recommends: `cmd.create(f"_c14_backup_{key}", object_name)  # NOTE: default args = all states`. Restore = `cmd.delete(object); cmd.create(object, backup_name)` (`ARCHITECTURE.md:308`).
- **Post-condition:** `cmd.count_atoms(backup_name) == cmd.count_atoms(source_name)` AND (for multi-state sources) `cmd.count_states(backup_name) == cmd.count_states(source_name)` (`cmd.count_states` at `querying.py:703`).
- **Confidence:** HIGH on the empirical behavior (multi-state loss + self-copy destructiveness + default-args working — all reproduced). MEDIUM that this is "the same pitfall" the prior docs meant (the docs said "no-op"; the real behavior is "incomplete backup + destructive self-copy"). **Action: the planner should UPDATE `PITFALLS.md` Pitfall 3 and `SUMMARY.md` to reflect the corrected, empirically-verified behavior.**
- `copy_properties` is unsupported in open-source PyMOL (`creating.py:1002-1003` prints a warning) — don't use it.

### cmd.count_atoms — `querying.py:1412` (the universal post-condition tool)
```python
# src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
def count_atoms(selection="(all)", quiet=1, state=ALL_STATES, domain='', *, _self=cmd):
```
- Returns int. Impl (`querying.py:1426-1432`): creates a temp `_count_tmp` selection, returns the count, deletes temp.
- **PITFALL:** on a nonexistent object, `count_atoms("deleted_obj")` RAISES `CmdException('Invalid selection name')` (empirically confirmed). Use `count_atoms("?" + name)` for a safe 0-return on nonexistent objects.
- Siblings: `cmd.count_states` (`querying.py:703`) for backup state-count verification; `cmd.get_names("objects")` (`querying.py:1148`) for "object exists/deleted" membership assertions; `cmd.identify` (`querying.py:1269`) for atom-ID lists.

---

## 3. AssetManager Design

- **Bundled PDB resolution:** `cmd.load(str(c14.paths.data_path("data","assets","bundled","<file>.pdb")), object_name)`. `c14.paths.data_path` is `__file__`-relative (cwd-independent, Phase 1 proven; `paths.py:43`). Post-condition: `cmd.count_atoms(object_name) > 0`.
- **PubChem substrate fetch:** `cmd.fetch(str(cid), object_name, type="cid", async_=0, path=str(c14.paths.data_path("data","assets","downloaded")))`. **Confirmed cwd-independent:** downloads land at the absolute `path` dir regardless of cwd (the Phase 1 cwd-independence invariant extends to fetch as long as `path=` is absolute). Post-condition: `cmd.count_atoms(object_name) > 0` AND `os.path.exists(path/cid_<cid>.sdf)`.
  - PDB-protein fetch (Phase 9 cast, not Phase 3 core — but `AssetManager` should expose it): `cmd.fetch(code, name, type="pdb", async_=0, path=<downloaded dir>)`.
- **Where bundled vs downloaded live (recommend + justify):**
  - **Bundled:** `c14/data/assets/bundled/` — COMMITTED to the repo (ships in the plugin zip). Per `ARCHITECTURE.md:360` and the 01-02 decision (bundled data lives inside `c14/data/`, ships in zip). Small/critical structures per spec.
  - **Downloaded:** `c14/data/assets/downloaded/` — GITIGNORED (fetched at runtime; NOT committed). **Phase 3 MUST add `c14/data/assets/downloaded/` to `.gitignore`** — it is currently MISSING (confirmed: my probe's fetched `cid_2244.sdf` showed as untracked `?? c14/data/assets/`). This is a required Plan-01 deliverable.
  - **Why split:** bundled ships with the plugin (offline-ready, per spec "bundle small"); downloaded is a runtime cache (machine-specific, regenerable, possibly large). Separate dirs let `git add c14/data/assets/bundled/` commit fixtures while `downloaded/` stays out. Matches `ARCHITECTURE.md:360` ("data/assets/bundled/ for committed, data/assets/downloaded/ for fetched").
  - **Note:** `c14.paths.data_path()` does NOT check existence (pure resolver, Phase 1 decision) — AssetManager must `os.makedirs(dir, exist_ok=True)` the `downloaded/` dir before fetch (empirically `os.makedirs` worked; cmd.fetch expects the dir to exist).
- **Interface sketch** (thin; lives in `c14/pymol_layer/asset_manager.py`, gate-excluded via `tools/check_imports.py` `SKIP_DIRS`):
  ```python
  # c14/pymol_layer/asset_manager.py
  import os
  import c14.paths

  class AssetManager(object):
      """Resolves asset keys to local files and loads/fetches them into PyMOL objects.

      Inject ``cmd`` so the path/arg logic is unit-testable in pure WSL python3.6
      with a MockCmd (the real cmd.* calls are verified by the headless smoke, not
      unit tests). All fetch calls force type=, async_=0, path= (Pitfall 5).
      """
      def __init__(self, cmd):
          self._cmd = cmd

      def _download_dir(self):
          d = str(c14.paths.data_path("data", "assets", "downloaded"))
          if not os.path.isdir(d):
              os.makedirs(d, exist_ok=True)
          return d

      def load_bundled(self, filename, object_name):
          # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
          p = str(c14.paths.data_path("data", "assets", "bundled", filename))
          self._cmd.load(p, object_name)
          if self._cmd.count_atoms(object_name) <= 0:
              raise RuntimeError("load_bundled: {0} produced no atoms".format(filename))
          return object_name

      def fetch_pubchem(self, cid, object_name, kind="cid"):
          # src: tmp/pymol-src/modules/pymol/importing.py:1323 cmd.fetch
          d = self._download_dir()
          self._cmd.fetch(str(cid), object_name, type=kind, async_=0, path=d)
          if self._cmd.count_atoms(object_name) <= 0:
              raise RuntimeError("fetch_pubchem: cid {0} produced no atoms (offline?)".format(cid))
          return object_name

      def fetch_pdb(self, code, object_name, ftype="pdb"):
          # src: tmp/pymol-src/modules/pymol/importing.py:1323 cmd.fetch
          d = self._download_dir()
          self._cmd.fetch(str(code), object_name, type=ftype, async_=0, path=d)
          if self._cmd.count_atoms(object_name) <= 0:
              raise RuntimeError("fetch_pdb: {0} produced no atoms".format(code))
          return object_name
  ```
  - **Inject `cmd`** (per the 3-tier testability + MolOps pattern) so dispatch/path/arg logic is unit-testable with a mock; the real `cmd.*` calls are verified via the headless smoke.
  - **Keep it THIN** — no manifest/caching beyond "fetch lands in `downloaded/`; cmd.fetch skips download if file exists (`importing.py:1211-1213`)". A later phase can add `data/assets.json` manifest + bulk-download prompt; Phase 3 just proves the resolve+load/fetch+post-condition pattern.

---

## 4. MolOps Design

- **MolAction(op, target, args) → cmd.* mapping table** (`MolAction` from `c14/story/model.py:26`; ops listed in its docstring `model.py:36-38`):
  | op | cmd.* sequence MolOps.apply(action) executes | notes |
  |---|---|---|
  | `hide_all` | `cmd.hide("everything", "all")` | clear the scene |
  | `load` | `self._assets.load_bundled(args["file"], args.get("object", target))` (or `fetch_pubchem`/`fetch_pdb` per `args["source"]`) | target = asset key; object name from args |
  | `show` | `cmd.show(args["rep"], args.get("sele", target))` | rep ∈ sticks/spheres/cartoon/lines/... |
  | `show_as` (suggested addition) | `cmd.show_as(args["rep"], args.get("sele", target))` | turns off other reps atomically — cleaner for scene setup |
  | `select_focus` | `cmd.select(args.get("name","focus"), args["sele"])` | named selection for focus/highlight |
  | `zoom` | `cmd.zoom(args.get("sele", target or "all"))` | no-op assertion (no crash) |
  | `color` | `cmd.color(args["color"], args.get("sele", target))` | color name |
  | `delete` | `cmd.delete(target)` | post: `count_atoms("?"+target)==0` (MolOps itself needn't assert; the smoke does) |
  | `restore` (Phase 4 precursor — backup made on load) | `cmd.delete(object); cmd.create(object, backup_name)` | from `_c14_backup_<key>`; **default-args** create (all states) |
  | `edit` / `protonate` (Phase 4) | `cmd.alter`+`cmd.sort` / `cmd.h_add` | **NOT Phase 3** — `apply` should `raise NotImplementedError` for these so the boundary is explicit |
- **Per-action dispatch contract (CONFIRMED correct, from `02-04-SUMMARY.md`):** `molops.apply(action)` receives ONE MolAction per call. Phase 2 engine emits `for action in actions: self.molaction_sink(action)` (`engine.py:151-153`). So the Phase 4+ controller calls `molops.apply(action)` per action. Phase 3's `MolOps.apply` takes a single MolAction. (Optionally add `molops.apply_all(actions)` as a convenience loop, but the unit boundary is per-action.)
- **MolOps stays out of the domain tier:** lives in `c14/pymol_layer/molops.py`, excluded from `tools/check_imports.py` via `SKIP_DIRS = {"pymol_layer","ui","__pycache__"}` (`check_imports.py:33`). The domain tier (`c14/story`, `c14/engine`) NEVER imports molops — it only emits `MolAction` data. (Verified: `model.py` and `engine.py` have no pymol import; the gate enforces this.)
- **Testability — inject `cmd` (and `asset_manager`):**
  ```python
  # c14/pymol_layer/molops.py
  from c14.story.model import MolAction  # MolAction is pure data (no pymol) -- OK to import here

  class MolOps(object):
      """Translates MolAction -> cmd.* calls. Inject ``cmd`` (and an AssetManager)
      so the dispatch logic is unit-testable in pure WSL python3.6 with a MockCmd;
      the real cmd.* calls are verified by the headless smoke.
      """
      def __init__(self, cmd, asset_manager=None):
          self._cmd = cmd
          self._assets = asset_manager  # may be None if no 'load' ops are dispatched

      def apply(self, action):
          op = action.op
          if op == "hide_all":
              # src: tmp/pymol-src/modules/pymol/viewing.py:568 cmd.hide
              self._cmd.hide("everything", "all")
          elif op == "show":
              # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show
              self._cmd.show(action.args["rep"], action.args.get("sele", action.target))
          elif op == "show_as":
              # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
              self._cmd.show_as(action.args["rep"], action.args.get("sele", action.target))
          elif op == "zoom":
              # src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom
              self._cmd.zoom(action.args.get("sele", action.target or "all"))
          elif op == "color":
              # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
              self._cmd.color(action.args["color"], action.args.get("sele", action.target))
          elif op == "select_focus":
              # src: tmp/pymol-src/modules/pymol/selecting.py:48 cmd.select
              self._cmd.select(action.args.get("name", "focus"), action.args["sele"])
          elif op == "load":
              if self._assets is None:
                  raise RuntimeError("molops.load requires an AssetManager")
              src = action.args.get("source", "bundled")
              if src == "cid":
                  self._assets.fetch_pubchem(action.args["cid"], action.args.get("object", action.target))
              elif src == "pdb":
                  self._assets.fetch_pdb(action.args["code"], action.args.get("object", action.target))
              else:
                  self._assets.load_bundled(action.args["file"], action.args.get("object", action.target))
          elif op == "delete":
              # src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete
              self._cmd.delete(action.target)
          else:
              raise NotImplementedError("molops: unknown op {!r} (edit/protonate/restore are Phase 4)".format(op))
  ```
  - Each `cmd.*` call carries a `# src: tmp/pymol-src/modules/pymol/<file>.py:<line> cmd.<name>` comment (see §6).
  - **`from c14.story.model import MolAction`** in molops.py is ALLOWED: MolAction is pure data (no pymol import), and molops.py is in the gate-excluded `pymol_layer/` dir. The gate only bans pymol/PyQt5 in the DOMAIN tier (`c14/` excluding `pymol_layer/`+`ui/`).

---

## 5. API-Sanity Smoke Script Design

- **Location:** `tools/api_sanity_smoke.py` (per `STACK.md:299` pattern). It's pure `pymol.cmd.*` (no Qt) — headless. Commit it (it's a tool, not gitignored).
- **Structure** (one section per cmd.* call; each prints a `SMOKE: PASS|FAIL <name>` line; final `SMOKE_RESULT:` sentinel):
  ```python
  # tools/api_sanity_smoke.py
  import sys, os
  sys.path.insert(0, os.getcwd())  # so `import c14.paths` works (cwd=repo root; __file__ is NOT the script -- see research)
  import pymol
  from pymol import cmd
  import c14.paths
  pymol.finish_launching()

  FAILS = []
  def check(name, ok, detail=""):
      print("SMOKE: {0} {1} {2}".format("PASS" if ok else "FAIL", name, detail))
      if not ok:
          FAILS.append(name)

  # --- load (bundled fixture) ---
  try:
      p = str(c14.paths.data_path("data", "assets", "bundled", "_smoke.pdb"))
      cmd.load(p, "smk")                                  # src: importing.py:635
      check("load", cmd.count_atoms("smk") > 0, "atoms=%d" % cmd.count_atoms("smk"))
  except Exception as e: check("load", False, repr(e))

  # --- fetch cid (NETWORK) -- report but don't hard-fail the whole smoke if offline ---
  try:
      d = str(c14.paths.data_path("data", "assets", "downloaded")); os.makedirs(d, exist_ok=True)
      cmd.fetch("2244", "asp", type="cid", async_=0, path=d)  # src: importing.py:1323
      check("fetch_cid", cmd.count_atoms("asp") > 0, "atoms=%d" % cmd.count_atoms("asp"))
  except Exception as e: check("fetch_cid", False, "NETWORK? %r" % e)

  # --- show/hide + rep keyword (the "rep visible" assertion) ---
  try:
      cmd.hide("everything", "smk"); cmd.show("sticks", "smk")  # src: viewing.py:568 / :491
      check("show_rep", cmd.count_atoms("smk & rep sticks") > 0,
            "rep-sticks=%d" % cmd.count_atoms("smk & rep sticks"))
  except Exception as e: check("show_rep", False, repr(e))

  # --- select ---
  try:
      cmd.select("sc1", "smk and name C1"); check("select", cmd.count_atoms("sc1") == 1, "n=%d" % cmd.count_atoms("sc1"))
  except Exception as e: check("select", False, repr(e))

  # --- zoom / color (no-crash) ---
  try: cmd.zoom("smk"); check("zoom", True)                       # src: viewing.py:65
  except Exception as e: check("zoom", False, repr(e))
  try: cmd.color("green", "smk"); check("color", True)             # src: viewing.py:1858
  except Exception as e: check("color", False, repr(e))

  # --- create backup (default args; multi-state if feasible) ---
  try:
      cmd.delete("bak"); cmd.create("bak", "smk")                 # src: creating.py:960 (default args = all states)
      check("create_backup", cmd.count_atoms("bak") == cmd.count_atoms("smk"),
            "bak=%d smk=%d" % (cmd.count_atoms("bak"), cmd.count_atoms("smk")))
  except Exception as e: check("create_backup", False, repr(e))

  # --- delete + ?-prefix post-condition ---
  try:
      cmd.delete("smk"); check("delete", cmd.count_atoms("?smk") == 0, "post=?smk->%d" % cmd.count_atoms("?smk"))
  except Exception as e: check("delete", False, repr(e))

  print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
  if FAILS: print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
  ```
- **Running it** (the exact incantation from §1):
  ```bash
  # MUST run with cwd = repo root
  WIN=$(wslpath -w "$(pwd)/tools/api_sanity_smoke.py")
  timeout 150 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq $WIN" > /tmp/opencode/smoke.txt 2>&1
  # verdict via STDOUT GREP (NOT $?):
  grep -q "^SMOKE_RESULT: FAIL" /tmp/opencode/smoke.txt && { echo "SMOKE FAILED"; cat /tmp/opencode/smoke.txt; exit 1; } || echo "SMOKE PASSED"
  ```
- **Fixtures:** a tiny bundled PDB `c14/data/assets/bundled/_smoke.pdb` (3-atom ETH, ~3 lines — the exact PDB the probes used) committed to the repo as the smoke's load fixture (avoids network for the core load test). The fetch test uses PubChem CID 2244 (aspirin, 21 atoms) — network-required, reported but not hard-failing the whole smoke if offline (per Pitfall 5). A real Phase 9 cast PDB is NOT needed for Phase 3.
- **Exit-code caveat (prominent):** the smoke CANNOT use `sys.exit`/`cmd.quit`/`os._exit` to signal failure (always exits 0 through the bat — see §1 Gotcha #1). Use the `SMOKE_RESULT:` stdout sentinel + bash grep. **This reinterprets success criterion #1.**

---

## 6. Source-Citation Comment Convention

- **Format:** `# src: tmp/pymol-src/modules/pymol/<file>.py:<line> cmd.<name>` — e.g. `# src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete`. Place directly ABOVE each `cmd.*` call in `molops.py` / `asset_manager.py` (see code sketches in §3/§4).
- **Greppable:** `grep -rn "# src: tmp/pymol-src" c14/pymol_layer/` lists every cited call. A verification step (a test or a `tools/` script) can assert every `self._cmd.`/`cmd.` call site has a neighboring `# src:` comment — this is the "read the source first" convention from `STACK.md`/`PITFALLS.md` made machine-checkable.
- **Satisfies success criterion #4:** every `cmd.*` call introduced carries a `file:line` source-citation referencing `tmp/pymol-src/modules/pymol/`.
- **Caveat:** line numbers are pinned to PyMOL 2.5.0 (verified — see Metadata). If PyMOL is upgraded, citations need re-verification.

---

## 7. Test Strategy (3-tier)

| Tier | What | How | Examples |
|---|---|---|---|
| **Pure-WSL python3.6 unit tests** (no pymol import) | dispatch logic, path resolution, arg construction | inject a `MockCmd` (records calls); assert the right `cmd.*` called with right args; assert paths are absolute c14.paths strings | `tests/test_molops.py`: `MolOps(mock).apply(MolAction("show","o",{"rep":"sticks"}))` → `mock.show` called with `("sticks","o")`. `tests/test_asset_manager.py`: `AssetManager(mock).load_bundled("f.pdb","o")` → `mock.load` called with `str(c14.paths.data_path("data","assets","bundled","f.pdb"))`, `"o"`. Plus a source-citation-presence test (grep `c14/pymol_layer/*.py` for `cmd.` calls lacking `# src:`). |
| **Headless-bridge tests** (via `run-conda-pymol.bat -cq`) | the real `cmd.*` calls + `count_atoms`/`count_states` post-conditions | `tools/api_sanity_smoke.py` (success criterion #1) + a MolOps smoke (success criterion #3) + an AssetManager smoke (success criterion #2). Print `SMOKE_RESULT:` sentinel; bash greps. | MolOps smoke: queue `[MolAction("hide_all"), MolAction("load","_smoke",{"object":"scene"}), MolAction("show","scene",{"rep":"sticks"}), MolAction("zoom","scene"), MolAction("color","scene",{"color":"green"})]`, `MolOps(pymol.cmd, AssetManager(pymol.cmd)).apply(each)`, assert `count_atoms("scene & rep sticks") > 0`. |
| **Human-verify (Qt/GUI)** | none in Phase 3 | n/a | Phase 3 is FULLY headless. Qt/GUI starts in Phase 6. |
- **Keeping pure-Python testable:** inject `cmd` (+ `asset_manager`) into `MolOps`/`AssetManager` constructors. The dispatch + path + arg logic is pure Python and unit-testable; only the real `cmd.*` calls need the headless bridge. This is the 3-tier testability pattern (`ARCHITECTURE.md` Pattern 1) carried into the pymol layer.
- **MockCmd sketch** (for unit tests):
  ```python
  class MockCmd(object):
      def __init__(self): self.calls = []
      def __getattr__(self, name):
          def f(*a, **k): self.calls.append((name, a, k)); return 0
          return f
      # count_atoms returns a configurable int for post-condition tests:
      # set mock.count_atoms = lambda sel: 3  (override the __getattr__ fallback)
  ```

---

## 8. Plan-Split Recommendation

The user explicitly asked to "split to more plans so each plan is focused." Recommend **3 plans** (the headless bridge gates everything; then AssetManager and MolOps build on it; the create-for-backup pitfall test lives in the api-sanity smoke — no 4th plan needed; alter/sort/restore is Phase 4).

### Plan 01: Headless test harness + api-sanity smoke + source-citation convention [GATE]
- **Objective:** Prove the WSL→Windows headless bridge works for every `cmd.*` the game uses; establish the stdout-sentinel harness contract (since `$?` is always 0) and the `# src: tmp/pymol-src/…` citation convention; ship `tools/api_sanity_smoke.py` + a minimal bundled fixture + the `.gitignore` entry for the downloaded-asset dir. Also: surface + document the corrected `cmd.create` pitfall and the `?`-prefix delete post-condition (and propose a `PITFALLS.md` wording fix).
- **Files:** `tools/api_sanity_smoke.py` (new), `c14/data/assets/bundled/_smoke.pdb` (new), `.gitignore` (edit — add `c14/data/assets/downloaded/`), optionally `tools/run_headless.sh` (a documented bash helper wrapping the incantation). A note/issue proposing the `PITFALLS.md` Pitfall 3 correction.
- **Depends on:** Phase 1 (`c14.paths`). Does NOT need Phase 2's MolAction (the api-sanity smoke exercises `cmd.*` directly).
- **Delivers:** success criterion #1 (api-sanity headless smoke with post-condition assertions, "passes" via stdout sentinel), #4 (source-citation convention established), and the empirical bridge/harness findings that every later headless test reuses.
- **Why GATE:** every later headless test reuses the incantation, the sentinel contract, the bundled fixture, and the gitignore. Must land first.

### Plan 02: AssetManager (bundle + fetch + path management + headless test)
- **Objective:** `c14/pymol_layer/asset_manager.py` with `load_bundled` + `fetch_pubchem` (+ `fetch_pdb`), injecting `cmd`, resolving paths via `c14.paths.data_path`, with `async_=0/type=/path=` pitfall mitigations baked in (Pitfall 5); pure-Python unit tests (MockCmd) + a headless smoke (load bundled + fetch CID, assert `count_atoms>0` and file-landed, cwd-independent).
- **Files:** `c14/pymol_layer/asset_manager.py` (new), `tests/test_asset_manager.py` (new), `tools/asset_smoke.py` (new) or fold its stages into `tools/api_sanity_smoke.py` (edit).
- **Depends on:** Plan 01 (harness + citation convention + bundled fixture + gitignore).
- **Delivers:** success criterion #2 (AssetManager resolves a bundled PDB and a fetched PubChem substrate to non-empty PyMOL objects, cwd-independent).

### Plan 03: MolOps (MolAction→cmd.* mapping + source citations + headless smoke)
- **Objective:** `c14/pymol_layer/molops.py` with `apply(action)` per-action dispatch for `hide_all`/`load`/`show`/`show_as`/`select_focus`/`zoom`/`color`/`delete` (+ `NotImplementedError` for `edit`/`protonate`/`restore` — Phase 4 boundary), injecting `cmd` + `AssetManager`; every `cmd.*` call cited; pure-Python unit tests (MockCmd asserting the mapping) + a headless smoke queueing `[hide_all, load, show, zoom, color]` and asserting `count_atoms("scene & rep sticks") > 0`.
- **Files:** `c14/pymol_layer/molops.py` (new), `tests/test_molops.py` (new), `tools/molops_smoke.py` (new) or fold into the api-sanity smoke (edit).
- **Depends on:** Plan 01 (harness + citation convention) + Plan 02 (`AssetManager`, since MolOps `load` delegates to it). Could parallelize with Plan 02 if MolOps stubs `load` delegation, but cleanest after Plan 02.
- **Delivers:** success criterion #3 (MolOps translates a queued MolAction list to the right `cmd.*` sequence; headless smoke confirms the shown rep visible) + #4 (citations on every molops `cmd.*` call).

---

## State of the Art / Pitfall Corrections

| Old claim (PITFALLS.md / SUMMARY.md / AGENTS.md) | Empirically-corrected current behavior | Impact |
|---|---|---|
| `cmd.create(obj,sele,1,1)` is a "silent no-op" (Pitfall 3) | NOT a no-op for a new-target backup (gives full atoms single-state). Real gotchas: (a) `1,1` copies only state 1 → incomplete backup for multi-state; (b) `create(obj,obj,1,1)` self-copy is DESTRUCTIVE (raises + corrupts). Working backup = `cmd.create(backup, source)` default args (all states). | Planner UPDATE Pitfall 3 wording; Phase 4 restore uses default-args create (already per `ARCHITECTURE.md:304`). |
| `count_atoms("deleted")` returns 0 (my assumption) | RAISES `CmdException('Invalid selection name')`. Use `count_atoms("?"+name)` or `get_names` membership. | delete post-condition must use `?` prefix. |
| "exit code 0 = pass" (AGENTS.md; success criterion #1) | Exit code is ALWAYS 0 through the bat (`conda deactivate` overwrites errorlevel; PyMOL swallows exceptions). Use stdout sentinel + grep. | Smoke harness greps `SMOKE_RESULT:`, not `$?`. Reinterprets success criterion #1. |
| `__file__` finds the script's dir | `__file__` = pymol package's `__init__.py` in a PyMOL-run script. Use `os.getcwd()` + `import c14.paths`. | Smoke/asset scripts must not rely on `__file__`; import c14 for paths. |
| `cmd.fetch` async-by-default races (Pitfall 5c) | API default `async_=0` IS sync in 2.5.0 (`importing.py:1382-1383`); async-by-default is interactive/CLI only. Still pass `async_=0` explicitly. | Mitigation unchanged (always `async_=0`), but the "race" is less likely via the API than docs imply. |
| `cmd.fetch` defaults to CIF (Pitfall 5a) | CONFIRMED — `type=''` → `cif` (`importing.py:1346`). Always pass `type=`. | Mitigation unchanged. |
| `cmd.fetch` `path` defaults to cwd (Pitfall 5b) | CONFIRMED — `path` defaults to `get('fetch_path') or '.'` (`importing.py:1379-1381`). Always pass absolute `path=`. | Mitigation unchanged; empirically confirmed cwd-independence with absolute `path=`. |

**Deprecated/outdated to fix in `PITFALLS.md`:** Pitfall 3's "no-op" wording (replace with the empirically-verified "incomplete-backup + destructive-self-copy" description + the default-args working form).

---

## Open Questions

1. **PDB-type fetch reliability for the Phase 9 protein cast.** Phase 3 tests only `type='cid'` (CAST-02 substrates). PDB fetch (large proteins) is Phase 9's concern. RECOMMENDED: Plan 01's api-sanity smoke include a non-critical `type='pdb'` fetch of a SMALL PDB (network) to confirm the `type='pdb', async_=0, path=` mitigation works for PDB too — but don't hard-fail the smoke if it's slow/offline.
2. **WSL env vars don't reach the Windows PyMOL process** (confirmed). If a later phase needs to parameterize a headless run, use a config FILE the script reads (or separate scripts), not env vars. Low impact for Phase 3.
3. **The `tmp/pymol-src` symlink target changed.** During research I accidentally deleted the symlink (via `git clean -fdX tmp/`) and restored it to point at the conda env's `site-packages/pymol/` — content-identical to the 2.5.0 open-source checkout (line numbers verified: `commanding.py:496`, `importing.py:635`, `creating.py:960`, `querying.py:1412` all match). Functionally equivalent for citation purposes. If the user wants the original git-checkout symlink restored, they can repoint `tmp/pymol-src/modules/pymol`. **Flag for awareness.**
4. **Stray scratch files left in the conda env** (`site-packages/pymol/_probe.pdb`, `cid_2244.sdf`) from an early probe writing via the wrong `__file__`/`here`. Harmless (not in the repo; `rm` is denied by policy so I couldn't clean them). The user may remove them from `…\chemtools-win10\Lib\site-packages\pymol\`. **Flag for awareness.**

---

## Sources

### Primary (HIGH confidence — read from source + empirically verified)
- `tmp/pymol-src/modules/pymol/importing.py` — `load` (L635), `fetch` (L1323), `_fetch` (L1149), `_multifetch` (L1266), hostPaths (L1115-1147), CIF default (L1346), `path` default (L1379-1381), async default (L1382-1383), skip-if-exists (L1211-1213), cid/sid filename (L1181).
- `tmp/pymol-src/modules/pymol/creating.py` — `create` (L960), default-args all-states behavior (L989-992 NOTES), `?`-prefix usage (L1001), `copy_properties` unsupported (L1002-1003).
- `tmp/pymol-src/modules/pymol/commanding.py` — `delete` (L496), `quit` (L462), `sync` (L367), `do` (L426), `reinitialize` (L345).
- `tmp/pymol-src/modules/pymol/viewing.py` — `zoom` (L65), `show` (L491), `show_as` (L528), `hide` (L568), rep names (L503-506), `color` (L1858).
- `tmp/pymol-src/modules/pymol/selecting.py` — `select` (L48).
- `tmp/pymol-src/modules/pymol/querying.py` — `count_atoms` (L1412), `count_states` (L703), `get_names` (L1148), `identify` (L1269), `get_object_color_index` (L819).
- `tmp/pymol-src/modules/pymol/editing.py` — `alter` (L1424), `sort` (L1257), `iterate` (L1490), alter→sort WARNING (L1457-1460) — Phase 4 forward reference.
- **Empirical (11 probe scripts run via `run-conda-pymol.bat -cq`)** — bridge works; exit-code-always-0; `__file__`=pymol package; `os.getcwd()`=workspace; `import c14.paths` headless; fetch cid + absolute-path cwd-independence; `rep` keyword; `?`-prefix; `create` multi-state loss + self-copy destructiveness + default-args working.
- `c14/paths.py` (Phase 1), `c14/story/model.py` (Phase 2 — MolAction), `c14/engine.py` (Phase 2 — per-action dispatch), `tools/check_imports.py` (gate `SKIP_DIRS`), `c14/pymol_layer/__init__.py` (placeholder). Phase summaries `01-02-SUMMARY.md`, `02-04-SUMMARY.md`.

### Secondary (MEDIUM confidence — project research, cross-referenced)
- `.planning/research/STACK.md` (cmd.fetch/load/create signatures, line-verified), `.planning/research/PITFALLS.md` (Pitfalls 3, 5, 6 — Pitfall 3 wording now empirically corrected), `.planning/research/ARCHITECTURE.md` (3-tier layering, MolAction carrier, AssetManager/MolOps design, default-args `cmd.create` backup at L304/L308), `.planning/research/SUMMARY.md` (P3/P5/P6 pitfall summaries).
- `run-conda-pymol.bat` (read to root-cause the exit-code-always-0 behavior: `call conda deactivate` after python overwrites errorlevel).

### Tertiary (LOW confidence — none; all claims verified against source or empirically)

---

## Metadata

**Confidence breakdown:**
- Headless bridge working: **HIGH** — 11 probe scripts run successfully; every behavior reproduced.
- Exit-code-always-0 finding: **HIGH** — root-caused to the bat's `conda deactivate`; tested sys.exit/os._exit/cmd.quit/raise → all exit 0.
- `__file__`/`os.getcwd()`/`import c14` findings: **HIGH** — empirically verified.
- `cmd.create` pitfall correction: **HIGH** on the empirical behavior (multi-state loss + self-copy destructiveness + default-args working, all reproduced); **MEDIUM** that it's "the same pitfall" the prior docs meant (wording differs).
- `count_atoms`-on-deleted raises + `?`-prefix idiom: **HIGH** — empirically verified.
- `cmd.fetch` cid + absolute-`path=` cwd-independence: **HIGH** — empirically verified (file landed at the absolute dir, count_atoms=21).
- `rep` selection keyword: **HIGH** — empirically verified (C-backed, couldn't read from source).
- API signatures + `file:line` citations: **HIGH** — read from `tmp/pymol-src` and re-verified after symlink restoration.
- AssetManager/MolOps design: **HIGH** — builds on verified API + existing `ARCHITECTURE.md` patterns; inject-`cmd` testability pattern proven by Phase 1/2 precedent.
- Network availability in the Windows env: **HIGH** for PubChem (verified); but offline-classroom is a real deployment concern (Pitfall 5) — fetch failures must be surfaced, not crash.

**Research date:** 2026-08-14
**Valid until:** 2026-09-13 (stable — PyMOL 2.5.0 API is fixed; the bridge/bat behavior is environment-specific but stable). Re-verify if PyMOL is upgraded (line-number citations would shift) or if `run-conda-pymol.bat` is modified (the exit-code-always-0 root cause is the bat's `conda deactivate` line).
