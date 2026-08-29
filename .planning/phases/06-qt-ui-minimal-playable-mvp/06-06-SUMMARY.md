---
phase: 06-qt-ui-minimal-playable-mvp
plan: 06
subsystem: ui
tags: [qt-free-controller, hero-resolver, engine-goto, oq-6-gate, tca-shuffle-routing, edit-prompt-seam, dependency-injection, defensive-dispatch]

# Dependency graph
requires:
  - phase: 06-03
    provides: view_provider/view_applier injection (the controller forwards these to the engine for save/load view-matrix capture/restore)
  - phase: 06-04
    provides: AchievementBoard.on_turn(turn, character, is_new_game) (the controller calls it after each start/choose/take_choice/apply_edit/request_edit)
  - phase: 06-05
    provides: intro.preface 6-call hero-highlight on_enter + bundled _smoke.pdb (2 carbons -> the HeroResolver multi-C prompt path is exercised) + pyr.branch cond fix (SC#3 aerobic unblock)
  - phase: 02-04
    provides: GameEngine per-action molaction_sink dispatch contract (the controller wires itself as the sink)
  - phase: 04-02
    provides: EditRouter + EditIntent.signature() (the controller builds EditIntents + routes via apply_player_edit)
provides:
  - Qt-free Controller (mediator): wires QtWidgets events -> GameEngine -> MolOps; importable in pure WSL python3.6 (no pymol/PyQt5)
  - HeroResolver (OQ-6 multi-C warn+confirm gate): no-op on single-C, prompts via injected prompt_fn on multi-C, rewrites hero sele to first-C on confirm
  - GameEngine.goto(node_id) + choice_cond_met(choice) -- additive public methods (Phase 2 tests stay green)
  - SC#3 Blocker B fix: tca.shuffle non-weighted choices (edit:offer, cycle-trap) routed via engine.goto (NOT choose, which RNG-pre-empts) -> Bad ending (cycle-trap) + edit.prompt reachable
  - Warning 4 edit-prompt seam: request_edit stashes enzyme_id + gotos edit.prompt; build_edit_intent falls back to _pending_edit_enzyme_id at edit.prompt (no edit:enzyme: tag there)
  - Blocker 1 fix c: _dispatch_molaction defensive try/except -- a failed molops.apply (offline pdb:XXX load) logs + continues to the next on_enter action (graceful degradation)
  - is_mixed_weighted_node helper: detects tca.shuffle so the view (06-08) renders Spin + Edit/conditional buttons vs one-button-per-choice
affects: [06-08 (MainWindow consumes TurnResult + _pending_edit_enzyme_id + is_mixed_weighted_node), 06-09 (EditDialog calls build_edit_intent/apply_edit), 06-14 (integration human-verify), Phase 7 (content uses the controller)]

# Tech tracking
tech-stack:
  added: []  # Qt-free; stdlib sys + c14.* domain only (NO new deps)
  patterns:
    - "Qt-free controller in gate-EXEMPT c14/ui/ dir (opts OUT of the pymol.Qt permission for testability -- 06-RESEARCH Pitfall 6)"
    - "Controller as the SOLE engine caller (widgets talk only to the controller; the controller is the sole molaction_sink)"
    - "Monkey-patch+restore hero pre-pass (one-shot mutate target.on_enter = resolved, restore in finally -- Open Question 2 recommended)"
    - "Injected prompt_fn/count_fn for OQ-6 separation (molops stays pure cmd.*; the prompt is a callback)"
    - "Defensive per-action try/except in _dispatch_molaction (graceful degradation: one failed load doesn't crash the game)"
    - "engine.goto for non-weighted routing at mixed weighted+non-weighted nodes (tca.shuffle Blocker B)"

key-files:
  created:
    - c14/ui/controller.py  # Controller (mediator) + HeroResolver (OQ-6 gate), Qt-free
    - tests/test_controller.py  # 18 unit tests with MockMolOps + MockView + mock prompt/count
  modified:
    - c14/engine.py  # +goto +choice_cond_met (additive public methods)
    - tests/test_engine.py  # +TestEngineGoto (6 new tests)

key-decisions:
  - "Monkey-patch+restore over pending-queue (06-RESEARCH Open Question 2): save original on_enter, swap in resolved, call engine.choose/goto, restore in finally. One-shot mutate is safe (the engine re-reads node.on_enter each _enter); avoids the pending-queue complexity."
  - "Hero op rewrite scope: label/show-spheres/set-sphere_scale sele rewritten to default first-C; show_as sticks + color KEEP object-wide sele (sticks show ALL carbons, color scopes to elem C already per 05.4 convention)."
  - "count_fn counts atoms in hero_sele but the prompt message says 'carbons' (plan literal; test 10 injects count_fn=3 + checks '3 carbons'). Production count_fn wraps cmd.count_atoms; Phase 7 may scope to elem C."
  - "take_choice/request_edit call engine.goto directly (bypass choice resolution) for non-weighted choices at mixed nodes -- choose() stays for pure-MC nodes."
  - "_target_node_id_for_choose returns None for weighted nodes (RNG picks; target unknown ahead of time) -- no weighted-choice target in the current skeleton has a hero highlight, so skipping the pre-pass is safe."

patterns-established:
  - "Pattern: Qt-free controller opts out of the c14/ui/ gate exemption (python3.6 -c 'import c14.ui.controller' must succeed in pure WSL -- the testability discipline)"
  - "Pattern: bound-method equality for sink wiring assertion (assertEqual not assertIs -- bound methods are fresh objects per access; == compares __self__ + __func__)"
  - "Pattern: controller-driven achievement recording (board.on_turn called after each engine turn; is_new_game=True only on start_game; the engine stays pure-domain)"

# Metrics
duration: 11 min
completed: 2026-08-30
---

# Phase 6 Plan 06: Qt-free Controller + HeroResolver Summary

**Qt-free Controller mediator + HeroResolver (OQ-6 gate) + additive engine.goto/choice_cond_met, fixing SC#3 Blocker B (tca.shuffle routing), the Warning 4 edit-prompt seam, and Blocker 1 fix c (defensive molops dispatch) -- 24 new tests green, full suite 308 green**

## Performance

- **Duration:** ~11 min
- **Started:** 2026-08-29T17:34:34Z
- **Completed:** 2026-08-29T17:45:33Z
- **Tasks:** 3
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments
- **Qt-free Controller (mediator)** -- the testability linchpin (~70% of UI logic WSL-unit-testable here). Wires GameEngine(molaction_sink=self._dispatch_molaction, edit_router, view_provider/applier) + forwards each MolAction the engine emits to molops.apply. Imports ONLY c14.* domain modules + stdlib sys (NO pymol/PyQt5) -- importable in pure WSL python3.6 (the controller opts OUT of the c14/ui/ gate exemption, 06-RESEARCH Pitfall 6).
- **SC#3 Blocker B fixed** -- tca.shuffle mixes 2 weighted RNG + 2 non-weighted (edit:offer, cycle-trap). The engine's choose() pre-empts the non-weighted (the RNG picks). New additive engine.goto(node_id) lets the controller's take_choice(choice) route non-weighted choices directly (bypass choice resolution) -- making the Bad ending (cycle-trap -> bad.cycle_trap_host_death) + edit.prompt reachable. choice_cond_met(choice) exposes the interpreter's _cond so the controller can enable/disable cond-gated buttons (the cycle-trap's visits>5) without re-implementing cond eval.
- **Warning 4 edit-prompt seam** -- request_edit(enzyme_id) stashes the enzyme_id from the edit-allowed SOURCE node + gotos edit.prompt directly. The MainWindow (06-08) reads _pending_edit_enzyme_id when render_turn sees turn.node.id == "edit.prompt" to open the EditDialog (06-09) with the right enzyme. build_edit_intent falls back to _pending_edit_enzyme_id at edit.prompt (which has no edit:enzyme: tag).
- **Blocker 1 fix c** -- _dispatch_molaction wraps the molops.apply forward in a defensive try/except. A failed load (network fetch of a real pdb:XXX target, a missing bundled fixture, any molops error) logs to stderr + continues to the next on_enter action rather than crashing the game (per-action swallow; the start node is safe via 06-05's bundled _smoke.pdb; mid-game real pdb:XXX loads can fail offline -- degrade gracefully).
- **HeroResolver (OQ-6 gate)** -- default+warn+confirm for multi-C structures. Detects the hero-highlight sequence via the `label` op with text "YOU" (OQ-4 marker). Single-C (count==1) is a deterministic no-op; multi-C (count!=1) prompts via the injected prompt_fn + on confirm rewrites the hero ops' sele to the first carbon (default_sele = "<hero_obj> and elem C"). The confirm IS the no-fabricated-science guard. Monkey-patch+restore pre-pass (one-shot mutate target.on_enter, restore in finally). Qt-free (prompt via injected callback; molops stays pure).
- **is_mixed_weighted_node helper** -- detects tca.shuffle (>=1 weighted + >=1 non-weighted eligible choice) so the view (06-08) renders a Spin button (RNG) + separate Edit/conditional buttons (non-weighted via take_choice/request_edit) vs one-button-per-choice (pure-MC via choose).

## Task Commits

Each task was committed atomically:

1. **Task 1: Add GameEngine.goto + choice_cond_met (additive)** -- `f013734` (feat)
2. **Task 2: Create c14/ui/controller.py (Controller + HeroResolver, Qt-free)** -- `3a8080a` (feat)
3. **Task 3: Add tests/test_controller.py (18 unit tests)** -- `92a8e6d` (test)

**Plan metadata:** (pending -- committed after this SUMMARY)

## Files Created/Modified
- `c14/engine.py` - +goto(node_id) directly enters a node bypassing choice resolution (Blocker B); +choice_cond_met(choice) exposes interpreter._cond (additive; Phase 2 tests stay green)
- `c14/ui/controller.py` - Qt-free Controller (mediator) + HeroResolver (OQ-6 gate); wires engine/molops/view/achievements; choose/take_choice/apply_edit/request_edit/save/load/start_game routing; _dispatch_molaction defensive swallow; is_mixed_weighted_node; monkey-patch+restore hero pre-pass
- `tests/test_engine.py` - +TestEngineGoto (6 new tests: enters/records-visit/ending/cond-none/delegates/before-start)
- `tests/test_controller.py` - 18 new tests: engine wiring, start/choose/take_choice/apply_edit/request_edit/save/load routing, tca.shuffle goto, request_edit seam, build_edit_intent fallback, _dispatch_molaction swallow, achievement calls, HeroResolver 4 cases, is_mixed_weighted_node, Qt-free import

## Decisions Made
- **Monkey-patch+restore over pending-queue** (06-RESEARCH Open Question 2): the controller saves `original = target.on_enter`, swaps in the resolved list, calls engine.choose/goto, restores in finally. One-shot mutate is safe (the engine re-reads node.on_enter each _enter via `list(node.on_enter)`). Avoids the pending-queue complexity (which would require the sink to drain a stash instead of forwarding the engine's actions -- fragile).
- **Hero op rewrite scope**: the per-hero-atom ops (label "YOU", show spheres, set sphere_scale) get their sele rewritten to the default first-C; the object-wide ops (show_as sticks, color) KEEP their sele (sticks show ALL carbons by design; color scopes to "elem C" already per the 05.4 convention). hide_all/load/set_color are not hero ops (copied unchanged).
- **count_fn counts atoms, message says "carbons"**: the plan's HeroResolver uses `n = count_fn(hero_sele)` + prints "{n} carbons" in the prompt. For intro.preface, hero_sele = "hero_atom" (the whole object) -> counts all atoms (3 in _smoke.pdb: 2 C + 1 O). The message says "3 carbons" -- a simplification (production count_fn could scope to elem C). Test 10 injects count_fn=3 + checks "3 carbons" (the plan's literal contract). Followed the plan exactly.
- **take_choice/request_edit use engine.goto directly** (not choose): for non-weighted choices at mixed nodes, the controller bypasses choice resolution entirely. choose() stays for pure-MC nodes. This is the Blocker B fix.
- **_target_node_id_for_choose returns None for weighted nodes**: the RNG picks the target; the controller can't know it ahead of time. No weighted-choice target in the current skeleton has a hero highlight, so skipping the hero pre-pass is safe. Phase 7 hero highlights at choice targets would be non-weighted (substrate-traversal), so the controller resolves them.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_engine_wiring_molaction_sink used assertIs instead of assertEqual**
- **Found during:** Task 3 (test_controller.py)
- **Issue:** Bound methods are fresh objects per access in Python (`instance.method` creates a new bound method each time). `assertIs(c._engine.molaction_sink, c._dispatch_molaction)` failed because they're different objects even though they wrap the same `__self__` + `__func__`.
- **Fix:** Changed to `assertEqual` (bound method `__eq__` compares `__self__` + `__func__`) + added belt-and-braces `__func__`/`__self__` identity assertions.
- **Files modified:** tests/test_controller.py
- **Verification:** test_engine_wiring_molaction_sink passes; all 18 controller tests green.
- **Committed in:** 92a8e6d (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Trivial test-assertion fix (Python bound-method semantics). No scope creep; no behavior change.

## Issues Encountered
None beyond the bound-method assertion fix above.

## User Setup Required
None - no external service configuration required. The controller is pure-Python (Qt-free); no PyMOL/Qt needed for the unit tests.

## Next Phase Readiness
- **Controller (06-06) COMPLETE** -- the Qt-free mediator is the testability linchpin. The QtWidgets widgets (06-08 MainWindow, 06-09 EditDialog) are now dumb renderers that talk ONLY to the controller.
- **06-08 (MainWindow) unblocked** -- consumes TurnResult via the injected view (render_turn); reads _pending_edit_enzyme_id when turn.node.id == "edit.prompt" to open the EditDialog; uses is_mixed_weighted_node to render Spin + Edit/conditional buttons at tca.shuffle. Calls controller.choose/take_choice/request_edit/save/load/start_game.
- **06-09 (EditDialog) unblocked** -- calls controller.build_edit_intent(op, target, args) + controller.apply_edit(intent). The curated edit options come from edits.json (Phase 7 fills the real per-enzyme entries).
- **06-14 (integration human-verify) unblocked** -- the controller + engine + molops stack is wired + unit-tested; the human-verify milestone can assemble the MainWindow + run a real playthrough.
- **SC#3 fully unblocked** -- 06-05 fixed the aerobic path (pyr.branch cond -> True ending reachable); 06-06 fixed the Bad path (tca.shuffle cycle-trap -> bad.cycle_trap_host_death reachable via engine.goto). Both True + Bad endings now reachable.
- **No blockers** -- the controller is Qt-free + WSL-unit-tested; the remaining Phase 6 plans (06-08/09/14) are Qt widgets (human-verify) that consume the controller's API.

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-30*
