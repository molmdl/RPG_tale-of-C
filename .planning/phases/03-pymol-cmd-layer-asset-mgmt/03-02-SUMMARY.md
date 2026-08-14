---
phase: 03-pymol-cmd-layer-asset-mgmt
plan: 02
subsystem: pymol-cmd
tags: [pymol, asset-manager, cmd-fetch, cmd-load, headless, mockcmd, unit-tests, pitfall-5]

# Dependency graph
requires:
  - phase: 03-pymol-cmd-layer-asset-mgmt (plan 01)
    provides: "Headless harness (tools/run_headless.sh), SMOKE_RESULT sentinel contract, bundled _smoke.pdb fixture, source-citation convention (# src: tmp/pymol-src/...), .gitignore for c14/data/assets/downloaded/"
  - phase: 01-foundation
    provides: "c14.paths.data_path() — __file__-relative absolute path resolver (cwd-independent); AssetManager resolves bundled fixture + downloaded dir through it"
provides:
  - "AssetManager class (load_bundled/fetch_pubchem/fetch_pdb) with inject-cmd testability + Pitfall 5 mitigations (type=/async_=0/path=<abs dir>) baked in"
  - "MockCmd unit-test pattern for the pymol layer (pure-WSL dispatch/path/arg verification, no pymol import — reusable by Plan 03 MolOps)"
  - "Headless AssetManager smoke (tools/asset_smoke.py) confirming real cmd.* calls + count_atoms post-conditions when network is available"
  - "3 source-citation comments in asset_manager.py (importing.py:635 cmd.load + importing.py:1323 cmd.fetch x2)"
affects: [03-03-molops, 04-editing-restore, 06-mvp, 09-cast]

# Tech tracking
tech-stack:
  added: []  # no new libraries — pure pymol.cmd.* + stdlib (os, c14.paths) only
  patterns:
    - "Inject-cmd testability for the pymol layer: AssetManager constructor takes cmd; module imports only os + c14.paths (importable in pure WSL python3.6 with no pymol); MockCmd unit tests verify dispatch/path/args; headless smoke verifies real cmd.*"
    - "Pitfall 5 mitigations baked into every fetch call: type= (NOT the CIF default — Pitfall 5a), async_=0 (sync — Pitfall 5c defense), path=<abs downloaded dir> (NOT cwd — Pitfall 5b)"
    - "count_atoms > 0 post-condition on every load/fetch (cmd.load returns None — importing.py:635 — never rely on the return value)"
    - "MockCmd with explicit count_atoms method overriding __getattr__ fallback (post-condition probe NOT recorded in calls; calls[0] is always the load/fetch dispatch)"

key-files:
  created:
    - "c14/pymol_layer/asset_manager.py — AssetManager class (load_bundled/fetch_pubchem/fetch_pdb/_download_dir); injects cmd; imports only os+c14.paths; 3 # src: citations; Pitfall 5 mitigations"
    - "tests/test_asset_manager.py — 8 MockCmd unit tests (dispatch/path/args + RuntimeError on empty + citation presence); pure WSL python3.6, no pymol import"
    - "tools/asset_smoke.py — Headless smoke injecting real pymol.cmd into AssetManager; 4 stages via SMOKE_RESULT sentinel"
  modified: []

key-decisions:
  - "Inject cmd (3-tier testability): AssetManager module imports only os + c14.paths; cmd is constructor-injected so the dispatch/path/arg logic is unit-testable in pure WSL python3.6 with a MockCmd (no pymol import). The real cmd.* calls are verified by the headless smoke."
  - "Pitfall 5 mitigations baked in: every fetch call passes type= (NOT the CIF default), async_=0 (sync — defense against the interactive default), path=<abs downloaded dir> (NOT cwd)."
  - "count_atoms > 0 post-condition on every load/fetch: cmd.load returns None (importing.py:635), so count_atoms is the only reliable non-empty assertion."
  - "MockCmd.count_atoms is an explicit method (NOT __getattr__ fallback) so the post-condition probe is not recorded in self.calls — calls[0] is always the dispatched load/fetch op."

patterns-established:
  - "Pattern: inject-cmd + MockCmd for pymol-layer unit tests (Plan 03 MolOps reuses this — MolOps(cmd, asset_manager) takes the same injected cmd)"
  - "Pattern: headless smoke injects the REAL pymol.cmd into the class under test (verifies the actual API contract, not just the MockCmd dispatch logic)"
  - "Pattern: _download_dir() creates the gitignored downloaded/ dir via os.makedirs(exist_ok=True) before cmd.fetch (fetch expects path to exist)"

# Metrics
duration: 18 min
completed: 2026-08-14
---

# Phase 3 Plan 02: AssetManager Summary

**AssetManager (load_bundled/fetch_pubchem/fetch_pdb) with inject-cmd testability + Pitfall 5 mitigations, verified by MockCmd unit tests (8) + headless smoke (4/4 stages PASS with network)**

## Performance

- **Duration:** ~18 min (wall clock excludes context-loading gap; execution = file creation + tests + headless smoke + commits)
- **Started:** 2026-08-14T01:10:45Z
- **Completed:** 2026-08-14T04:46:36Z
- **Tasks:** 2
- **Files modified:** 3 (all created)

## Accomplishments
- Created `c14/pymol_layer/asset_manager.py` — a thin AssetManager that resolves a bundled PDB and a fetched PubChem/PDB substrate to local files and loads each into a non-empty PyMOL object, with the `cmd.fetch` pitfalls (CIF default, `path=.` cwd default, async interactive default) mitigated by ALWAYS passing `type=, async_=0, path=<abs dir>`. The `cmd` object is constructor-injected (NOT imported at module top) so the module is importable in pure WSL python3.6 with no pymol installed — the dispatch/path/arg logic is unit-testable with a MockCmd.
- Created `tests/test_asset_manager.py` — 8 pure-WSL MockCmd unit tests (no pymol import) verifying: load_bundled resolves an ABSOLUTE bundled/ path (cwd-independent); fetch_pubchem/fetch_pdb pass type=/async_=0/path=<abs downloaded dir>; count_atoms <= 0 post-condition raises RuntimeError; and the source-citation comments are present (SC #4 machine-checkable).
- Created `tools/asset_smoke.py` — a headless smoke injecting the REAL `pymol.cmd` into AssetManager, with 4 stages via the `SMOKE_RESULT:` stdout sentinel. ALL 4 stages PASSED with network available: `load_bundled atoms=3` (bundled fixture, no network), `fetch_pubchem atoms=21` (PubChem CID 2244 aspirin), `fetch_pubchem_file_landed` (file at absolute downloaded dir — cwd-independence, SC #2), `fetch_pdb atoms=327` (PDB 1crn crambin, type='pdb' mitigation).
- Confirmed the 3-tier testability pattern carries into the pymol layer: unit tests (MockCmd) prove the dispatch/path/arg logic; headless smoke proves the real cmd.* API contract; Qt/GUI is deferred to Phase 6.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create AssetManager (inject cmd, Pitfall 5 mitigations, source citations) + MockCmd unit tests** - `62e4f0c` (feat)
2. **Task 2: Create the AssetManager headless smoke + run it (real cmd.* + count_atoms post-conditions)** - `4031617` (feat)

**Plan metadata:** (pending — final docs commit below)

## Files Created/Modified
- `c14/pymol_layer/asset_manager.py` (created) — AssetManager class with `load_bundled`, `fetch_pubchem`, `fetch_pdb`, `_download_dir`; injects `cmd`; imports only `os` + `c14.paths` (NO pymol at top level — importable in pure WSL); 3 `# src:` citations (importing.py:635 cmd.load + importing.py:1323 cmd.fetch x2); every fetch call passes `type=, async_=0, path=<abs dir>` (Pitfall 5 mitigations); count_atoms > 0 post-condition on every load/fetch.
- `tests/test_asset_manager.py` (created) — 8 MockCmd unit tests in 4 test classes (TestAssetManagerLoadBundled, TestAssetManagerFetchPubchem, TestAssetManagerFetchPdb, TestSourceCitationsPresent); pure WSL python3.6 (no pymol import); MockCmd records dispatch (name/args/kwargs) with explicit count_atoms returning configurable _count for post-condition branches.
- `tools/asset_smoke.py` (created) — Headless smoke injecting real `pymol.cmd` into AssetManager; 4 stages (load_bundled + fetch_pubchem + fetch_pubchem_file_landed + fetch_pdb) via `SMOKE_RESULT:` sentinel; reuses `tools/run_headless.sh` harness from Plan 01; every direct cmd.count_atoms call carries a `# src:` citation.

## Decisions Made
- **Inject cmd (3-tier testability).** The AssetManager module imports only `os` + `c14.paths`; `cmd` is constructor-injected (`def __init__(self, cmd): self._cmd = cmd`). This keeps the module importable in pure WSL python3.6 with no pymol installed, so the dispatch/path/arg logic is unit-testable with a MockCmd. The real `cmd.*` calls are verified by the headless smoke (`tools/asset_smoke.py` injects the real `pymol.cmd`). This is the 3-tier testability pattern (pure-Python domain → pymol.cmd headless → pymol.Qt human-verify) carried into the pymol layer.
- **Pitfall 5 mitigations baked in.** Every `self._cmd.fetch(...)` call passes `type=` (NOT the CIF default — Pitfall 5a), `async_=0` (sync — Pitfall 5c defense against the interactive default), `path=<abs downloaded dir>` (NOT cwd — Pitfall 5b). Downloads land in `c14/data/assets/downloaded/` regardless of cwd (the absolute `path=` mitigation — confirmed by the headless smoke's `fetch_pubchem_file_landed` stage).
- **count_atoms > 0 post-condition.** `cmd.load` returns `None` (importing.py:635) — never rely on the return value. `count_atoms(object_name) > 0` is the only reliable non-empty assertion. On failure (e.g. offline fetch), the post-condition raises `RuntimeError`.
- **MockCmd.count_atoms is explicit (not __getattr__ fallback).** The explicit `count_atoms` method bypasses `__getattr__`, so the post-condition probe is NOT recorded in `self.calls` — `calls[0]` is always the dispatched load/fetch op. Set `mock._count = 0` to exercise the RuntimeError branch; `mock._count = 3` for the success path.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- None. The headless smoke ran cleanly with network available — all 4 stages PASSED (load_bundled=3 atoms, fetch_pubchem=21 atoms, fetch_pubchem_file_landed=abs path, fetch_pdb=327 atoms). No offline fallback was needed.

## User Setup Required

None - no external service configuration required. The headless bridge uses the existing `C:\src\run-conda-pymol.bat` (user-owned, unmodified) and the existing Windows conda env `chemtools-win10`.

## Next Phase Readiness
- **Plan 03-03 (MolOps)** is unblocked: MolOps delegates its `load` op to AssetManager (`self._assets.load_bundled/fetch_pubchem/fetch_pdb`). MolOps follows the same inject-cmd pattern (`MolOps(cmd, asset_manager)`) and the same source-citation convention. The MockCmd unit-test pattern is reusable for MolOps dispatch tests. The headless smoke pattern (inject real `pymol.cmd`) is reusable for the MolOps smoke.
- **Phase 4 (editing + restore)** benefits from AssetManager being in place: the `load` op (via MolOps → AssetManager) is the entry point for structures that Phase 4's `apply_edit`/backup/restore operate on.
- **No blockers.** All fetch calls pass `type=, async_=0, path=<abs dir>` (Pitfall 5 mitigations unit-tested + headless-verified). The `load_bundled` stage (no network) MUST pass and did. Network was available for the fetch stages (PubChem + PDB reachable).

---
*Phase: 03-pymol-cmd-layer-asset-mgmt*
*Completed: 2026-08-14*
