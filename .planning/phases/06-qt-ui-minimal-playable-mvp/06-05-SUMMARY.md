---
phase: 06-qt-ui-minimal-playable-mvp
plan: 05
subsystem: story-graph
tags: [story-graph, cond-syntax, hero-highlight, reachability, pyr-branch, smoke-pdb, flags-get]

# Dependency graph
requires:
  - phase: 05.1-story-graph-design
    provides: FROZEN 55-node / 21-ending glucose skeleton (pyruvate_branch.json + intro.json) that this plan fixes in place
  - phase: 05.4-cast-hero-representation-design
    provides: The 6-call hero-highlight MolAction sequence (section 3.3 of 05.4-CONVENTION.md) inserted into intro.preface on_enter
provides:
  - "Fixed pyr.branch conds (flags.get('host_o2_low') dict-method form) -- SC#3 unblocked: the player can advance aerobically to TCA -> True ending"
  - "Start-node on_enter loads the bundled _smoke.pdb placeholder (no pdb:TBD network fetch, no crash at intro.preface -- Blocker 1 fix b)"
  - "6-call hero-highlight sequence in intro.preface on_enter (set_color hero_cyan + show_as sticks + color elem C + show spheres + set sphere_scale 0.3 + label YOU) -- SC2 human-verifiable at Phase 6"
  - "10 new pure-Python tests (5 runtime-eligibility + 5 start-node shape) in tests/test_glucose_reachability.py"
affects: [06-14-headless-smoke, 06-14-human-verify, phase-7-content, 06-06-controller]

# Tech tracking
tech-stack:
  added: []  # pure data + test edits only; no new libraries
  patterns:
    - "dict-method cond form: flags.get('key') over flags.key (the interpreter exposes flags as a DICT; attribute access raises AttributeError -> caught -> False -> stuck)"
    - "bundled-placeholder start-node loads: _smoke.pdb (a test fixture, NOT a cited PDB) so the game starts instantly with no network fetch (SC4)"
    - "hero-highlight as an on_enter MolAction SEQUENCE (6 peer-primitive ops, NOT a super-op) -- the dispatch is 06-01's molops.py work; this plan authors the DATA"

key-files:
  created: []
  modified:
    - "data/story_glucose/pyruvate_branch.json -- 2 pyr.branch choice conds fixed to flags.get('host_o2_low')"
    - "data/story_glucose/intro.json -- intro.preface + intro.shell_glucose on_enter swapped to _smoke.pdb + 6-call hero-highlight added to preface"
    - "tests/test_glucose_reachability.py -- +2 test classes (TestPyrBranchRuntimeEligibility 5 tests + TestStartNodeOnEnterShape 5 tests)"

key-decisions:
  - "Cond syntax: flags.get('host_o2_low') (dict-method) over flags.host_o2_low (dict-attribute) -- the interpreter._cond exposes flags as state.flags (a DICT); dict-attribute access raises AttributeError -> except -> False -> BOTH choices hidden -> player stuck at pyr.branch -> SC#3 blocked. The dict-method form returns None when unset (not None is True = aerobic eligible; bool(None) is False = anaerobic hidden until a Phase 7 flag-setter exists). Matches tca.shuffle's working sibling cond visits.get('tca.shuffle', 0) > 5."
  - "Start-node placeholders: _smoke.pdb (the bundled 3-atom C1/O1/C2 test fixture at c14/data/assets/bundled/_smoke.pdb, NOT a cited PDB) over pdb:TBD_* (non-existent PDB IDs that would network-fetch-and-crash). _smoke.pdb has 2 carbons -> the OQ-6 HeroResolver (06-06) will prompt '2 carbons, highlight the first?' at runtime (a feature, not a bug -- exercises the confirm gate)."
  - "Regex backtracking fix (Rule 1 bug): the plan's prescribed regression-scan regex flags\\.[a-zA-Z_][a-zA-Z0-9_]*(?!\\() has a greedy-backtracking false-positive -- it matches 'flags.ge' (a prefix of 'flags.get') because the (?!\\() lookahead fails at '(' then the engine backtracks to 'ge' where the next char 't' is not '('. Fixed by adding a (?![a-zA-Z0-9_]) word-boundary BEFORE (?!\\() so the full identifier must match before the '(' check, eliminating the truncation."

patterns-established:
  - "Runtime-eligibility tests: exercise interpreter._cond at RUNTIME (not just structural BFS) to prove conds evaluate correctly -- the reachability tests cover topology (cond ignored); eligibility tests cover playability (cond evaluated)"
  - "Start-node no-network invariant: start nodes load bundled placeholders only (no pdb: target) so the game starts instantly (SC4) -- machine-checked by test_start_nodes_do_not_reference_real_pdb_fetch"

# Metrics
duration: 11min
completed: 2026-08-29
---

# Phase 6 Plan 05: pyr-branch cond fix + start-node _smoke.pdb swap + hero-highlight Summary

**Fixed the SC#3 pyr.branch cond-syntax bug (flags.get dict-method form) + swapped the start-node crashing pdb:TBD_* loads for the bundled _smoke.pdb placeholder + added the 6-call hero-highlight sequence to intro.preface on_enter so SC2 is human-verifiable at Phase 6 -- all content/data edits, NO topology change (55 nodes / 21 endings preserved).**

## Performance

- **Duration:** 11 min
- **Started:** 2026-08-29T16:08:26Z
- **Completed:** 2026-08-29T16:20:09Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Fixed the pyr.branch cond-syntax bug (SC#3 Blocker A): both choice conds now use `flags.get('host_o2_low')` (dict-method form) instead of `flags.host_o2_low` (dict-attribute -> AttributeError -> both choices hidden -> player stuck -> could not reach TCA -> could not reach a True ending). The aerobic path now runs at runtime (player can proceed to pyr.pdh -> TCA -> True ending).
- Swapped the start-node crashing `pdb:TBD_*` load targets for the bundled `_smoke.pdb` placeholder (Blocker 1 fix b): intro.preface (hero_atom + aa_cast) + intro.shell_glucose (glucose) now load the bundled 3-atom test fixture with NO network fetch, so the game does not crash the moment the first on_enter load dispatches.
- Added the 6-call hero-highlight sequence (05.4-CONVENTION.md section 3.3) to intro.preface on_enter AFTER the hero_atom load: set_color hero_cyan + show_as sticks + color hero_cyan on elem C + show spheres + set sphere_scale 0.3 + label YOU -- so SC2 ("Starting a glucose game highlights the C14 hero atom") is human-verifiable at Phase 6. No fabricated science (_smoke.pdb is a test fixture, NOT a cited PDB).
- Added 10 new pure-Python tests (5 runtime-eligibility + 5 start-node shape) -- all green; the 9 existing reachability tests stay green (no topology regression); 258-test full suite green.

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix the 2 pyr.branch conds to dict-method form (flags.get)** - `cdafb3b` (fix)
2. **Task 2: Add 5 runtime-eligibility tests** - `0887fc7` (test)
3. **Task 3: Swap start-node TBD_* loads for _smoke.pdb + hero-highlight + 5 shape tests** - `492dd15` (fix)

**Plan metadata:** pending (docs commit after STATE.md update)

## Files Created/Modified
- `data/story_glucose/pyruvate_branch.json` - 2 choice conds fixed: `flags.host_o2_low` -> `flags.get('host_o2_low')` (aerobic + anaerobic); no other change (topology/weights/effects/labels untouched)
- `data/story_glucose/intro.json` - intro.preface on_enter: 2 `pdb:TBD_*` loads -> `_smoke.pdb` + 6-call hero-highlight sequence inserted after the hero_atom load; intro.shell_glucose on_enter: `pdb:TBD_GLUCOSE` -> `_smoke.pdb` (no hero-highlight here); no topology change (only on_enter edited)
- `tests/test_glucose_reachability.py` - +2 imports (re, StoryInterpreter, GameState); +TestPyrBranchRuntimeEligibility (5 tests exercising interpreter._cond at runtime); +TestStartNodeOnEnterShape (5 tests asserting the start-node on_enter shape + topology-unchanged regression guard)

## Decisions Made
- **Cond syntax = dict-method form.** `flags.get('host_o2_low')` over `flags.host_o2_low`. Rationale: interpreter._cond (interpreter.py:124-133) exposes `flags` as `state.flags` (a DICT); dict-attribute access raises `AttributeError` (dicts have no attribute `host_o2_low`) -> the `except Exception: return False` swallows it -> BOTH choices hidden -> stuck. The dict-method form returns `None` when unset -> `not None` is `True` (aerobic eligible); `bool(None)` is `False` (anaerobic hidden until a Phase 7 flag-setter exists). This matches the working sibling cond `visits.get('tca.shuffle', 0) > 5` in tca.json (same interpreter, same dict-method form).
- **Start-node placeholder = _smoke.pdb (bundled test fixture).** Over real PDB IDs (no fabricated science) and over the crashing `pdb:TBD_*` targets. `_smoke.pdb` is the 3-atom C1/O1/C2 fixture at `c14/data/assets/bundled/_smoke.pdb` (the same fixture `tools/asset_smoke.py` + `tools/molops_smoke.py` use). The 06-01 molops.load bare-filename target path routes `_smoke.pdb` -> `load_bundled` -> NO network. The 2 carbons in `_smoke.pdb` exercise the OQ-6 HeroResolver confirm-gate (06-06) at the start node -- a feature, not a bug.
- **No host_o2_low flag-setter added.** Phase 6 only fixes the cond SYNTAX so the aerobic path runs; the anaerobic branch becomes reachable when Phase 7 adds a mechanism to set `host_o2_low` (the anaerobic choice's `effects: {set: {anaerobic: true}}` sets `anaerobic`, NOT `host_o2_low` -- that is a Phase 7 content question, intentionally left untouched).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed regex backtracking false-positive in the regression-scan test**
- **Found during:** Task 2 (test_no_broken_dict_attribute_conds_remain)
- **Issue:** The plan's prescribed regex `flags\.[a-zA-Z_][a-zA-Z0-9_]*(?!\()` is meant to flag the broken `flags.<attr>` dict-attribute form while allowing the good `flags.get(...)` method-call form. But the greedy `[a-zA-Z0-9_]*` matches `get`, the `(?!\()` lookahead fails at `(`, then the engine BACKTRACKS to `ge` where the next char `t` is not `(` -> the lookahead succeeds -> a FALSE match on `flags.ge`. This caused the test to flag the CORRECT `flags.get('host_o2_low')` conds as broken (test failed).
- **Fix:** Added a `(?![a-zA-Z0-9_])` word-boundary assertion BEFORE `(?!\()` so the full identifier must match completely before the `(` check: `flags\.[a-zA-Z_][a-zA-Z0-9_]*(?![a-zA-Z0-9_])(?!\()`. Verified on 5 cases (good method-call -> no match; bad attribute-access -> match; sibling visits.get -> no match).
- **Files modified:** tests/test_glucose_reachability.py
- **Verification:** `python3.6 -m unittest tests.test_glucose_reachability -v` -- all 19 tests green including the fixed regression scan
- **Committed in:** 0887fc7 (Task 2 commit)

**2. [Rule 3 - Blocking] Parallelization race swept 06-03's staged c14/engine.py into Task 1's commit**
- **Found during:** Task 1 (commit cdafb3b)
- **Issue:** 06-05 runs in parallel with 06-01/06-02/06-03. The parallel 06-03 agent had staged `c14/engine.py` (its `view_provider`/`view_applier` work) in the git index BEFORE my `git add data/story_glucose/pyruvate_branch.json`. My `git commit` then committed the entire index -- sweeping 06-03's in-progress `c14/engine.py` (51 insertions: the view-matrix injection into save/load) into my 06-05 Task 1 commit alongside my pyruvate_branch.json change. The parallel agents (06-02, 06-01) then committed ON TOP of my commit, so rewriting history would be destructive.
- **Fix:** Followed the 05.1-14 precedent (STATE.md): did NOT rewrite git history (parallel agents active + had built on top). Verified the bundled c14/engine.py changes are sound (full suite 237 -> 253 -> 258 tests green throughout). Guarded Tasks 2 + 3 against a repeat by checking `git diff --cached --name-only` before each commit and unstaging any non-mine files (both subsequent commits were clean -- 1 and 2 files respectively, only mine). My actual deliverable (pyruvate_branch.json cond fix) is correctly in the commit; the bundled c14/engine.py is 06-03's complete + tested deliverable, just mis-attributed.
- **Files affected:** c14/engine.py (bundled into cdafb3b; 06-03's work, not mine)
- **Verification:** full suite green (258 tests); the bundled engine.py is 06-03's tested view-matrix injection
- **Committed in:** cdafb3b (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking/parallel-race)
**Impact on plan:** Both auto-fixes necessary for correctness + clean execution. No scope creep. The regex fix makes the regression-scan test actually work; the race is documented (not rewritten) per the established 05.1-14 parallel-agent precedent.

## Issues Encountered
None beyond the deviations above. The plan's prescribed JSON for both on_enter blocks matched the 05.4-CONVENTION.md section 3.3 6-call sequence exactly (verified against the convention source). The cond fix is a 2-char-per-cond content edit with no structural impact.

## User Setup Required

None - no external service configuration required. This plan is pure story-graph JSON data + pure-Python tests (WSL-testable, no PyMOL/Qt needed for the verify steps).

## Next Phase Readiness
- **SC#3 unblocked at runtime:** the player can now advance past pyr.branch aerobically (pyr.pdh -> TCA -> True ending). The structural reachability was always green (BFS ignores cond); this plan makes the FROZEN topology actually PLAYABLE.
- **Blocker 1 fix b (start-node no-crash):** intro.preface + intro.shell_glucose load the bundled _smoke.pdb placeholder -> the 06-14 headless smoke + human-verify can START at intro.preface without crashing on the first load MolAction.
- **SC2 verifiable at Phase 6:** the 6-call hero-highlight sequence is in intro.preface on_enter -> the 06-14 human-verify will see the cyan hero + "YOU" label + ball-and-stick (dispatched via 06-01's molops set_color/label/set/show/show_as/color ops, which 06-01 delivered in parallel).
- **Integration with 06-01:** this plan authored the DATA (MolAction sequences in JSON referencing op names set_color/label/set/load); 06-01 authored the MECHANISM (molops.py dispatches). The integration is proven when 06-14 runs the headless smoke starting at intro.preface. 06-05 does NOT need 06-01's code to edit the JSON.
- **Phase 7 follow-up:** the anaerobic branch needs a host_o2_low flag-setter (currently the anaerobic choice is hidden at runtime until Phase 7 adds the mechanism). The TBD text_dramatic/text_teaching + claim_ids stay as PLACEHOLDER_PHASE7 (Phase 7 authors the real text + real structures).

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-29*
