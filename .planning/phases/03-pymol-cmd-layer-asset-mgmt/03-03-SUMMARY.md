---
phase: 03-pymol-cmd-layer-asset-mgmt
plan: 03
subsystem: pymol-cmd
tags: [pymol, molops, cmd-dispatch, molaction, headless, mockcmd, mockassets, unit-tests, source-citation, notimplementederror, rep-keyword]

# Dependency graph
requires:
  - phase: 03-pymol-cmd-layer-asset-mgmt (plan 01)
    provides: "Headless harness (tools/run_headless.sh), SMOKE_RESULT sentinel contract, bundled _smoke.pdb fixture, source-citation convention (# src: tmp/pymol-src/...), MockCmd pattern"
  - phase: 03-pymol-cmd-layer-asset-mgmt (plan 02)
    provides: "AssetManager (load_bundled/fetch_pubchem/fetch_pdb with inject-cmd + Pitfall 5 mitigations) -- MolOps `load` op delegates to it"
  - phase: 02-story-engine-core (plan 01)
    provides: "MolAction pure-data carrier (c14/story/model.py -- op/target/args, no pymol import) -- the dispatch target; engine emits per-action to sink (02-04 contract)"
provides:
  - "MolOps class (apply per-action dispatch + apply_all convenience) translating MolAction -> cmd.* (hide_all/show/show_as/select_focus/zoom/color/delete/load)"
  - "Explicit Phase 4 boundary: edit/protonate/restore/unknown ops raise NotImplementedError (no silent no-op)"
  - "MockCmd/MockAssets unit-test pattern for per-op dispatch verification (pure WSL python3.6, no pymol import)"
  - "Headless MolOps smoke (tools/molops_smoke.py) confirming the real cmd.* sequence + the `rep` keyword 'representation visible' post-condition (SC #3)"
  - "7 source-citation comments in molops.py (one per direct self._cmd.* call site -- SC #4)"
affects: [04-editing-restore, 05.2-representation-design, 06-mvp]

# Tech tracking
tech-stack:
  added: []  # no new libraries -- pure pymol.cmd.* + stdlib (c14.story.model.MolAction is pure data) only
  patterns:
    - "Per-action MolAction dispatch (the 02-04 contract): MolOps.apply(action) takes ONE MolAction per call; the Phase 4+ controller calls molops.apply(action) per action (engine emits `for action in actions: sink(action)`)"
    - "Inject cmd + AssetManager (3-tier testability): MolOps module imports only c14.story.model.MolAction (pure data); cmd + asset_manager are constructor-injected so the per-op dispatch logic is unit-testable in pure WSL python3.6 with MockCmd/MockAssets (no pymol import); the real cmd.* calls are verified by the headless smoke"
    - "NotImplementedError boundary for unimplemented ops: edit/protonate/restore (Phase 4) + unknown ops all raise NotImplementedError -- the boundary is explicit so a stray MolAction never silently no-ops"
    - "`rep <name>` selection keyword as the 'representation visible' headless post-condition: count_atoms('obj & rep sticks') > 0 after show(sticks) -- empirically confirmed in 03-RESEARCH.md section 2 (C-backed, unverifiable from source)"
    - "load op delegates to AssetManager (no direct cmd.* call); raises RuntimeError if no AssetManager injected"

key-files:
  created:
    - "c14/pymol_layer/molops.py -- MolOps class (apply per-action dispatch, apply_all convenience); injects cmd + asset_manager; imports MolAction from c14.story.model (pure data, no pymol); 7 # src: citations; NotImplementedError for edit/protonate/restore/unknown; RuntimeError for load-without-AssetManager"
    - "tests/test_molops.py -- 18 MockCmd/MockAssets unit tests (8 dispatch + 5 load delegation + 4 Phase4-boundary + 1 citations present); pure WSL python3.6, no pymol import"
    - "tools/molops_smoke.py -- Headless smoke injecting real pymol.cmd + real AssetManager into MolOps; queues [hide_all,load(bundled),show,zoom,color] -> count_atoms('scene & rep sticks')>0 (SC #3) + 3 bonus stages; SMOKE_RESULT sentinel"
  modified: []

key-decisions:
  - "Per-action dispatch (02-04 contract): MolOps.apply(action) takes ONE MolAction per call. The engine emits `for action in actions: self.molaction_sink(action)` (engine.py:151-153); the Phase 4+ controller calls molops.apply(action) per action. apply_all(actions) is a thin convenience loop. The unit boundary is per-action apply (matching the 02-04 decision)."
  - "NotImplementedError for edit/protonate/restore -- explicit Phase 4 boundary. These ops are NOT implemented in Phase 3; raising NotImplementedError (rather than silently no-opping) makes the boundary explicit so a stray MolAction with op='edit' fails loudly instead of silently doing nothing. Unknown ops also raise NotImplementedError."
  - "load delegates to AssetManager (no direct cmd.* call in molops for load). MolOps.apply('load') dispatches to self._assets.fetch_pubchem/fetch_pdb/load_bundled per args['source'] (defaults to 'bundled'). The cmd.* citations for load live in asset_manager.py. load without an injected AssetManager raises RuntimeError."
  - "7 source-citation comments on every direct self._cmd.* call site (hide/show/show_as/select/zoom/color/delete) -- SC #4 machine-checkable (grep count = 8 with the module-header convention; 7 call sites)."

patterns-established:
  - "Pattern: per-action MolAction dispatch is the unit boundary (one MolAction per apply call) -- the Phase 4+ controller wires molops.apply to the engine's molaction_sink"
  - "Pattern: NotImplementedError for unimplemented ops makes phase boundaries explicit (Phase 4 will implement edit/protonate/restore by replacing the NotImplementedError branches)"
  - "Pattern: MockCmd + MockAssets for pymol-layer dispatch unit tests (reuses the Plan 02 inject-cmd pattern; MockAssets mirrors AssetManager signatures so `load` delegation is unit-testable with no real cmd/pymol)"
  - "Pattern: headless smoke injects the REAL pymol.cmd + real AssetManager into MolOps (verifies the actual dispatch sequence + the rep-keyword post-condition, not just the MockCmd mapping)"

# Metrics
duration: 9 min
completed: 2026-08-14
---

# Phase 3 Plan 03: MolOps Summary

**MolOps (MolAction -> cmd.* per-action dispatch) with inject-cmd+AssetManager testability, NotImplementedError Phase 4 boundary, verified by MockCmd/MockAssets unit tests (18) + headless smoke (6/6 stages PASS, rep-sticks=3 proves SC #3)**

## Performance

- **Duration:** ~9 min (wall clock; execution = file creation + tests + headless smoke + 2 commits + summary)
- **Started:** 2026-08-14T04:52:24Z
- **Completed:** 2026-08-14T05:01:21Z
- **Tasks:** 2
- **Files modified:** 3 (all created)

## Accomplishments
- Created `c14/pymol_layer/molops.py` -- the MolOps class that translates a `MolAction` (the pure-data carrier from `c14/story/model.py`) into the right `cmd.*` call, per-action (ONE MolAction per `apply()` call, per the 02-04 dispatch contract). Implements 8 ops: `hide_all` -> `cmd.hide("everything","all")`; `show`/`show_as` -> `cmd.show`/`cmd.show_as(rep, sele)`; `select_focus` -> `cmd.select(name, sele)`; `zoom` -> `cmd.zoom(sele)`; `color` -> `cmd.color(color, sele)`; `load` -> delegates to `AssetManager` (`fetch_pubchem`/`fetch_pdb`/`load_bundled` per `args["source"]`, default `bundled`); `delete` -> `cmd.delete(target)`. `edit`/`protonate`/`restore`/unknown ops raise `NotImplementedError` (explicit Phase 4 boundary). `load` without an AssetManager raises `RuntimeError`. Injects `cmd` + `asset_manager` so the dispatch logic is unit-testable in pure WSL python3.6; imports `MolAction` from `c14.story.model` (pure data -- allowed in the gate-excluded `pymol_layer/` dir).
- Created `tests/test_molops.py` -- 18 pure-WSL MockCmd/MockAssets unit tests (no pymol import) verifying the per-op dispatch mapping (8 ops), `load` delegation to AssetManager (bundled/cid/pdb + default-source + no-AssetManager-runtime-error), the Phase 4 `NotImplementedError` boundary (edit/protonate/restore/unknown), and the source-citation presence (SC #4 machine-checkable).
- Created `tools/molops_smoke.py` -- a headless smoke injecting the REAL `pymol.cmd` + real `AssetManager` into MolOps, queuing `[hide_all, load(bundled), show(sticks), zoom, color]` and dispatching per-action via `molops.apply(a)`. ALL 6 stages PASSED: `molops_scene_loaded` (atoms=3), `molops_scene_rep_visible` (rep-sticks=3 -- SC #3 proven headlessly via the `rep` keyword), `molops_hide_all_cleared` (rep-lines=0), `molops_show_as_atomic` (rep-lines=3, rep-sticks=0 -- show_as turns off other reps atomically), `molops_delete_post` (?scene->0). Uses the committed bundled fixture (NO network) so it MUST pass regardless of network availability.
- Confirmed the 3-tier testability pattern completes for Phase 3: unit tests (MockCmd/MockAssets) prove the per-op dispatch mapping; headless smoke (real pymol.cmd + real AssetManager) proves the real cmd.* sequence + the `rep` keyword "representation visible" post-condition; Qt/GUI is deferred to Phase 6. Phase 3 SC #3 + SC #4 are both delivered; with SC #1 (Plan 01) + SC #2 (Plan 02) already complete, the phase is ready for verification.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create MolOps (per-action dispatch, inject cmd+AssetManager, citations, NotImplementedError for Phase 4 ops) + MockCmd unit tests** - `dcdcd6f` (feat)
2. **Task 2: Create the MolOps headless smoke (queue [hide_all,load,show,zoom,color] -> rep visible) + run it** - `0c346cb` (feat)

**Plan metadata:** (pending -- final docs commit below)

## Files Created/Modified
- `c14/pymol_layer/molops.py` (created) -- MolOps class with `apply(action)` per-action dispatch + `apply_all(actions)` convenience. Constructor injects `cmd` + `asset_manager` (asset_manager may be None). Imports `MolAction` from `c14.story.model` (pure data -- allowed; gate-excluded dir). 8 implemented ops (hide_all, show, show_as, select_focus, zoom, color, load, delete); edit/protonate/restore/unknown raise `NotImplementedError`; load without AssetManager raises `RuntimeError`; load delegates to AssetManager (fetch_pubchem/fetch_pdb/load_bundled per args["source"], default "bundled"). 7 `# src:` citations (one per direct self._cmd.* call site). Python 3.6 plain-class syntax (no @dataclass/walrus).
- `tests/test_molops.py` (created) -- 18 MockCmd/MockAssets unit tests in 4 test classes (TestMolOpsDispatch, TestMolOpsLoad, TestMolOpsPhase4Boundary, TestSourceCitationsPresent). Pure WSL python3.6 (no pymol import). MockCmd records every cmd.* dispatch (name/args/kwargs) with explicit count_atoms method; MockAssets records every AssetManager delegation (load_bundled/fetch_pubchem/fetch_pdb). Verifies the per-op MolAction -> cmd.* mapping, load delegation per source, the Phase 4 NotImplementedError boundary, and the citation presence (SC #4).
- `tools/molops_smoke.py` (created) -- Headless smoke injecting real `pymol.cmd` + real `AssetManager` into MolOps. Queues [hide_all, load(bundled), show(sticks), zoom, color] as MolActions and dispatches per-action via `molops.apply(a)` (the 02-04 contract). 6 stages via `SMOKE_RESULT:` sentinel: molops_scene_loaded (atoms=3), molops_scene_rep_visible (rep-sticks=3 -- SC #3), molops_hide_all_cleared (rep-lines=0), molops_show_as_atomic (rep-lines=3, rep-sticks=0), molops_delete_post (?scene->0). Reuses `tools/run_headless.sh` harness from Plan 01; every direct cmd.count_atoms call carries a `# src:` citation. Uses the committed bundled fixture (NO network).

## Decisions Made
- **Per-action dispatch (02-04 contract).** `MolOps.apply(action)` takes ONE MolAction per call. The engine emits `for action in actions: self.molaction_sink(action)` (`engine.py:151-153`); the Phase 4+ controller calls `molops.apply(action)` per action. `apply_all(actions)` is a thin convenience loop. The unit boundary is per-action `apply` -- matching the 02-04 decision (the plan's key_links prose conflicted with its tests; the tests won; this plan honors the resolved contract).
- **NotImplementedError for edit/protonate/restore -- explicit Phase 4 boundary.** These ops are NOT implemented in Phase 3. Raising `NotImplementedError` (rather than silently no-opping) makes the boundary explicit so a stray MolAction with `op="edit"` fails loudly. Unknown ops also raise `NotImplementedError`. Phase 4 will implement these by replacing the `NotImplementedError` branches with the `apply_edit` helper + backup/restore + `cmd.alter`+`cmd.sort` + `cmd.h_add` patterns.
- **load delegates to AssetManager (no direct cmd.* call in molops for load).** `MolOps.apply("load")` dispatches to `self._assets.fetch_pubchem`/`fetch_pdb`/`load_bundled` per `args["source"]` (defaults to `"bundled"`). The cmd.* citations for load live in `asset_manager.py` (verified by the Plan 02 unit tests). `load` without an injected AssetManager raises `RuntimeError("molops.load requires an AssetManager")`.
- **7 source-citation comments on every direct self._cmd.* call site.** hide (viewing.py:568), show (viewing.py:491), show_as (viewing.py:528), select (selecting.py:48), zoom (viewing.py:65), color (viewing.py:1858), delete (commanding.py:496) -- 7 call sites, grep count = 8 with the module-header convention. SC #4 machine-checkable (the unit test `test_citations_present_in_source` asserts all 7 are present).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- None. The headless smoke ran cleanly on the first run -- all 6 stages PASSED. The core sequence (hide_all, load bundled, show, zoom, color -> rep visible) uses the committed `_smoke.pdb` fixture (NO network), so it passed regardless of network availability. The 3 bonus stages (hide_all_cleared, show_as_atomic, delete_post) also passed, confirming the hide_all + show_as + delete dispatch works against the real PyMOL 2.5.0 API.

## User Setup Required

None - no external service configuration required. The headless bridge uses the existing `C:\src\run-conda-pymol.bat` (user-owned, unmodified) and the existing Windows conda env `chemtools-win10`.

## Next Phase Readiness
- **Phase 3 is COMPLETE.** All 4 success criteria are delivered: SC #1 (Plan 01 -- api-sanity smoke + SMOKE_RESULT sentinel), SC #2 (Plan 02 -- AssetManager resolves bundled + fetched substrates), SC #3 (Plan 03 -- MolOps translates a queued MolAction list to the correct cmd.* sequence; headless smoke confirms the resulting object has the expected representation visible via `count_atoms("scene & rep sticks") > 0`), SC #4 (Plan 01/02/03 -- source-citation convention on every cmd.* call). The phase is ready for verification.
- **Phase 4 (editing + restore)** is unblocked: MolOps is the dispatch target the Phase 4+ controller wires to the engine's `molaction_sink`. Phase 4 implements edit/protonate/restore by replacing the `NotImplementedError` branches with the `apply_edit` helper + backup/restore (default-args `cmd.create`) + `cmd.alter`+`cmd.sort` + `cmd.h_add` patterns. The `alter`->`sort` silent-corruption trap (Pitfall 6) is the highest technical-risk item; address on day one of Phase 4. The empirically-corrected `cmd.create` pitfall (Plan 01) and the `?`-prefix delete post-condition (Plans 01/03) are already documented and proven.
- **Phase 5.2 (Representation Design)** benefits from MolOps being in place: the scene-template library (one MolAction sequence per stage type) can be headless-prototyped via `molops.apply_all(actions)` on placeholder/bundled structures, with the `rep` keyword post-condition (proven here) as the assertion.
- **No blockers.** All 8 implemented ops dispatch correctly (unit-tested + headless-verified); the Phase 4 boundary is explicit (NotImplementedError); the 3-tier testability pattern holds (inject cmd+AssetManager; MockCmd/MockAssets unit tests; headless smoke with real cmd.*). 123 tests pass (105 prior + 18 molops); AST gate clean.

---
*Phase: 03-pymol-cmd-layer-asset-mgmt*
*Completed: 2026-08-14*
