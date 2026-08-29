---
phase: 06-qt-ui-minimal-playable-mvp
plan: 01
subsystem: api
tags: [pymol, molops, molaction, dispatch, headless-smoke, mockcmd, unittest, align, set-color, label, load-target-prefix]

# Dependency graph
requires:
  - phase: 05.4-cast-hero-representation-design
    provides: the FROZEN set_color/label/set convention (05.4-CONVENTION.md §2.1) + hero_highlight_smoke that proved the cmd.* mechanism
  - phase: 05.3-wt-aligned-structure-load-convention
    provides: the FROZEN align convention (05.3-CONVENTION.md §6) + wt_align_smoke that proved cmd.super
  - phase: 03-pymol-cmd-layer
    provides: MolOps.apply + the inject-cmd testability pattern + the source-citation convention
provides:
  - 4 new molops dispatches (set_color/label/set/align) wrapping cmd.* via FROZEN-verbatim elif branches (no new constructor param, no new dependency)
  - load branch target-prefix fallback parsing action.target (pdb:/cid:/sid:/bare-filename) when no source/file/code/cid keys present -- fixes the KeyError on the 5.1 skeleton on_enter form
  - 22 MockCmd unit tests (14 op-dispatch + 8 load target-prefix/backward-compat)
  - headless regression smoke (molops_deferred_dispatch_smoke.py) proving the dispatches reproduce the direct-cmd smokes' post-conditions
affects: [06-06-controller, 06-qt-ui-minimal-playable-mvp, 07-glucose-content, 08-fatty-acid-content, 09-anaerobic-content]

# Tech tracking
tech-stack:
  added: []  # uses self._cmd already injected (Phase 3); no new dependency
  patterns:
    - "FROZEN-verbatim elif branch: copy the convention's pseudocode EXACTLY into MolOps.apply (no paraphrase) -- the smokes pre-proved the cmd.* calls"
    - "Target-prefix fallback: check 'file' in args FIRST (backward-compat) then fall back to parsing action.target -- avoids KeyError on the skeleton form"
    - "Headless smoke dispatches via molops.apply (NOT cmd.* directly) to prove the dispatch wrappers reproduce the direct-cmd smokes' post-conditions"

key-files:
  created:
    - tools/molops_deferred_dispatch_smoke.py
  modified:
    - c14/pymol_layer/molops.py
    - tests/test_molops.py

key-decisions:
  - "4 new ops as minimal peer-primitive wrappers (NOT a composite hero_highlight super-op) -- mirrors 5.3/5.4 convention; set_color/label/set from 5.4, align from 5.3"
  - "label dispatch encapsulates the quoted-string footgun ('\"YOU\"' not bare YOU) at the dispatch layer"
  - "align dispatch normalizes cealign's REVERSED arg order (target,mobile) so callers always pass (mobile,reference); composes align_sele for BOTH mobile+ref"
  - "load target-prefix fallback parses action.target (pdb:/cid:/sid:/bare) when no source/file/code/cid keys present -- the 5.1 skeleton on_enter form -- preserving the explicit-source backward-compat path"
  - "Left commit 524362a as-is after a parallel-staging race bundled 2 concurrent 06-02/06-05 test files (precedent: 05.1-14 -- do not rewrite history while parallel agents active)"

patterns-established:
  - "FROZEN-verbatim elif dispatch: the convention's pseudocode IS the implementation (the smokes pre-proved the cmd.* calls; the dispatch just wraps them)"
  - "Backward-compat-preserving branch extension: new fallback path checks the old-form key FIRST ('file' in args) before the new target-prefix logic"
  - "Dispatch-proving smoke: a smoke that calls molops.apply (the dispatch under test) instead of cmd.* directly, asserting the SAME post-conditions the direct-cmd smoke proved"

# Metrics
duration: 11min
completed: 2026-08-29
---

# Phase 6 Plan 01: Deferred MolOps Dispatches Summary

**4 FROZEN-verbatim molops dispatches (set_color/label/set/align) + a load target-prefix fallback, with 22 MockCmd unit tests + a headless smoke proving the dispatches reproduce the direct-cmd smokes' post-conditions against the real PyMOL 2.5.0 API**

## Performance

- **Duration:** 11 min
- **Started:** 2026-08-29T16:03:42Z
- **Completed:** 2026-08-29T16:15:37Z
- **Tasks:** 3
- **Files modified:** 3 (molops.py, test_molops.py, molops_deferred_dispatch_smoke.py)

## Accomplishments

- 4 new `elif` branches in `MolOps.apply` (set_color/label/set/align) -- FROZEN-verbatim from 05.4-CONVENTION.md:125-139 + 05.3-CONVENTION.md:240-258, using `self._cmd` already injected (NO new constructor param, NO new dependency)
- `label` dispatch encapsulates the quoted-string footgun (`'"YOU"'`, not a bare `YOU` that would eval the atom property); `align` normalizes cealign's REVERSED arg order (target,mobile) so callers always pass (mobile,reference) + composes `align_sele` for BOTH mobile+ref; unknown align method raises ValueError
- `load` branch extended with a target-prefix fallback (pdb:/cid:/sid:/bare-filename) parsing `action.target` when no source/file/code/cid keys are present -- fixes the KeyError on the 5.1 skeleton on_enter form -- while preserving the explicit-source backward-compat path (test_molops.py:220-251 stay green)
- 22 MockCmd unit tests green (14 op-dispatch + 8 load target-prefix/backward-compat) covering arg order, quoted-string label, cealign reversal, align_sele composition, ValueError on unknown method, target-prefix parsing, no-object-stripped-code default, + a backward-compat regression guard
- Headless smoke PASS (13/13 stage checks): dispatching the 6-call hero-highlight + an align + a target-prefix load via `molops.apply` reproduces the direct-cmd smokes' post-conditions (count=1/elem C/rep spheres+sticks/color hero_cyan/label YOU; align moved mobile wt 8.85->1.46; load bare-filename->load_bundled hero2=3 NO KeyError; load pdb:->fetch_pdb mock NO network)

## Task Commits

Each task was committed atomically:

1. **Task 1: add 4 deferred molops dispatches + load target-prefix fallback** -- `caa1d40` (feat)
2. **Task 2: add MockCmd unit tests for 4 new ops + load target-prefix** -- `ff78d5b` (test)
3. **Task 3: add headless regression smoke for deferred dispatches** -- `524362a` (feat) [bundled 2 parallel 06-02/06-05 test files -- see Deviations]

## Files Created/Modified

- `c14/pymol_layer/molops.py` -- +4 elif branches (set_color/label/set/align) with `# src:` citations + extended `load` branch (target-prefix fallback) + module docstring Phase 6 subsection + top-of-file comment
- `tests/test_molops.py` -- +2 test classes (TestMolOpsDeferredDispatch 14 tests + TestMolOpsLoadTargetPrefix 8 tests); existing classes untouched
- `tools/molops_deferred_dispatch_smoke.py` -- headless smoke dispatching the 6-call hero-highlight + an align + a target-prefix load via `molops.apply` (13 stage checks, SMOKE_RESULT sentinel)

## Decisions Made

- **4 minimal peer-primitive ops, NOT a composite super-op** -- mirrors 5.3/5.4 convention (5.4 §2.2 REJECTED the composite `hero_highlight` super-op; 5.3 §6 added ONE focused `align` op). Each new op wraps ONE cmd.* family; keeps dispatch minimal + per-step testable.
- **label quoted-string encapsulation at the dispatch layer** -- the footgun (bare `YOU` evals the atom property) is hidden inside `molops.apply`; callers pass `{"text":"YOU"}` and the dispatch emits `'"YOU"'`.
- **align cealign arg-order normalization** -- `cmd.cealign(target, mobile)` is REVERSED vs `cmd.super/align(mobile, target)`; the dispatch swaps for cealign only so callers always pass `(mobile, reference)` uniformly.
- **load target-prefix fallback preserves backward-compat** -- the new path checks `"file" in args` FIRST (the existing explicit-source/no-source+file form), then falls back to parsing `action.target`. The existing `src == "cid"/"pdb"` branches are UNCHANGED.
- **Left 524362a as-is after the parallel-staging race** -- see Deviations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Parallel-staging race bundled 2 concurrent test files into the Task 3 commit**

- **Found during:** Task 3 (commit step)
- **Issue:** `tests/test_engine.py` (+176 lines) and `tests/test_state.py` (+29 lines) were already STAGED in the git index by a concurrent plan (06-02/06-05 -- visible in `git log`: `2dfdabb docs(06-02)`, `cdafb3b fix(06-05)`, `e5823b2 docs(06-02)`) when I ran `git add tools/molops_deferred_dispatch_smoke.py && git commit`. `git commit` (without `--only`) commits ALL staged files, so the 2 parallel test files were bundled into my `524362a` commit alongside the smoke file.
- **Fix:** Left `524362a` as-is (did NOT rewrite history). Rationale: parallel agents (06-02, 06-05) are actively committing; `git reset --soft` risks orphaning a parallel commit (precedent: STATE.md 05.1-14, where a `reset --soft HEAD~1` accidentally undid a parallel Plan 15 commit because HEAD had moved via parallel commits). The bundled files are legitimate parallel test content (test_engine.py, test_state.py), just mis-attributed; no data loss, no incorrect code. My 06-01 deliverable (the smoke file, +335 lines) is correctly in the commit. Going forward I will use `git commit -- <file>` (path-limited) to avoid sweeping pre-staged files, but `git commit --only` is the safer form for future task commits in a parallel repo.
- **Files modified:** none (the bundled files are parallel work, untouched by me)
- **Verification:** full suite 253 tests green (237 from 06-01 + 16 from the bundled parallel test files); the smoke file content is mine and verified PASS; the parallel test files pass too (no regression).
- **Committed in:** `524362a`

---

**Total deviations:** 1 auto-fixed (1 blocking parallel-race)
**Impact on plan:** Attribution noise only. All 06-01 deliverables are correctly committed + verified. No scope creep; the 4 dispatches + load extension + tests + smoke are exactly what the plan specified.

## Issues Encountered

None. (The parallel-staging race is documented under Deviations -- it's unplanned work handled via the deviation rules, not a planned-work problem.)

## User Setup Required

None -- no external service configuration required. Uses only `self._cmd` already injected (Phase 3); no new dependency.

## Next Phase Readiness

- The 4 deferred dispatches + the load target-prefix fallback are PROVEN against the real PyMOL 2.5.0 API (headless smoke SMOKE_RESULT: PASS, 13/13 stage checks) + unit-tested (22 MockCmd tests, 47 test_molops total). The controller (06-06) can now forward MolActions to `molops.apply` for SC2 (the hero highlight) + the 5.3 WT-aligned reveal + the skeleton on_enter load form (`{"op":"load","target":"pdb:XXX",...}` no longer KeyErrors).
- **Blockers/concerns:** parallel agents (06-02, 06-05) are concurrently modifying `c14/engine.py`, `c14/state.py`, `tests/test_engine.py`, `tests/test_state.py`; my 06-01 work is purely additive (no overlap with their files). The bundled-commit attribution noise (`524362a` contains 2 parallel test files) should be cross-referenced if the 06-02/06-05 SUMMARYs list those test files under their own plan IDs.
- **Success criteria met:** 4 FROZEN-verbatim elif branches with `# src:` citations; load target-prefix fallback preserving backward-compat (no KeyError; test_molops.py:220-251 green); 22 MockCmd unit tests green; headless smoke PASS reproducing the direct-cmd smokes' post-conditions; AST gate clean; full suite green (no regression); no new dependency; no super-op; no pymol import at module top.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-29*
