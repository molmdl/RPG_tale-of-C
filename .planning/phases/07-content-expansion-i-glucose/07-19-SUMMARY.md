---
phase: 07-content-expansion-i-glucose
plan: 19
subsystem: tools
tags: [pymol, scene-capture, molaction, json, headless-smoke, read-only-introspection, py36]

# Dependency graph
requires:
  - phase: 07-content-expansion-i-glucose (plan 17)
    provides: the 5.4 template-fill verification + 5.3 reveal wiring (the scene vocabulary the capture must round-trip)
  - phase: 05.4-cast-hero-representation-design
    provides: the FROZEN MolAction op vocabulary + {op,target,args} on_enter shape (05.4-CONVENTION.md:370-380) and the named-color palette
  - phase: 06-qt-ui-minimal-playable-mvp
    provides: molops.py dispatch (set_color/label/set landed Phase 6) — the frozen dispatch vocabulary capture emits against
provides:
  - tools/scene_capture.py — read-only PyMOL-session capture emitting a paste-ready on_enter MolAction JSON sequence (per-object reps/colors/labels + named selections + camera) using ONLY the frozen dispatch vocabulary (+ one Phase-10-flagged set_view)
  - tools/scene_capture_smoke.py — headless round-trip proof: 10 pinned assertions, SMOKE_RESULT: PASS sentinel
  - empirically pinned PyMOL 2.5.0 read-API facts (get_type-on-selection returns type tag only; s.sphere_scale via iterate; hero_cyan == -1 fresh)
affects: [phase-10 camera/palette (set_view dispatch + full palette), phase-11 docs (tool usage), user workflow (GUI-authored scenes -> engine JSON)]

# Tech tracking
tech-stack:
  added: [] # no new dependencies — stdlib json/sys + pymol only (spec.md constraint held)
  patterns:
    - "read-only introspection emitter: every read cmd.* call carries a '# src:' citation; never mutates session state"
    - "NOT-CAPTURED protocol: observed-but-unmappable features become '# NOT CAPTURED: <desc>' comment lines — nothing silently dropped, no invented ops"
    - "empirical-pin-then-emit: pre-implementation probe (tmp/07-19-probe.py, gitignored) pins ambiguous API behavior before the mapping is written; smoke asserts the observed branch"

key-files:
  created:
    - tools/scene_capture.py
    - tools/scene_capture_smoke.py
  modified: []

key-decisions:
  - "Selection-expression recovery pinned to the NOT-CAPTURED fallback: cmd.get_type(<named selection>) empirically returns the bare type tag 'selection' on PyMOL 2.5.0 (probe OBS1; the session entry stores resolved atom indices, not the expression — OBS4), so NO select_focus and NO zoom op are emitted; the exact camera rides home in the single flagged set_view entry"
  - "set_color generated name 'captured_<idx>' (idx = capture session's atom color index): deterministic within capture, arbitrary-but-unique in replay (set_color defines it idempotently before the paired color op consumes it)"
  - "zoom is emitted ONLY when a select_focus was emitted — never under the fallback (a zoom referencing a selection the replay never creates would be an invented op)"
  - "Per-atom settings (sphere_scale) are OBSERVED but NOT emitted (NOT-CAPTURED comment) — the frozen vocabulary's set op is excluded from capture per the 07-19 plan"
  - "main() guard is __name__ in ('__main__', 'pymol'): PyMOL's run executes scripts in the pymol package's global namespace (parsing.py:424 namespace='global' -> run_file(path, ns_pymol, ns_pymol)) where __name__ == 'pymol', NOT '__main__'; plain import stays side-effect-free"

patterns-established:
  - "scene-capture: GUI-authored sessions convert back into the engine's frozen op vocabulary via read-only cmd.* introspection"
  - "the NOT-CAPTURED comment protocol for capture tools (mirror for any future introspection utilities)"
  - "pymol-namespace main() guard for PyMOL-runnable tools that are also importable modules"

# Metrics
duration: 15 min
completed: 2026-09-03
---

# Phase 7 Plan 19: Scene-capture tool Summary

**Read-only PyMOL-session capture (tools/scene_capture.py) that converts GUI-authored scenes back into the frozen on_enter MolAction vocabulary — + a 10-assertion headless round-trip smoke (SMOKE_RESULT: PASS) pinning the empirically-observed selection fallback and the Phase-10-flagged set_view camera entry.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-03T05:30:57Z
- **Completed:** 2026-09-03T05:46:43Z
- **Tasks:** 2
- **Files modified:** 2 (both new, tools/ only)

## Accomplishments
- `capture_scene(cmd)` reads a live session via READ-ONLY cmd.* introspection ONLY (get_names/get_type/count_states/count_atoms/iterate/get_color_index/get_color_tuple/get_selection_state/get/get_view — every call `# src:`-cited) and emits ONLY op names dispatched by molops.py:140-170: set_color / show_as / color / show / label / select_focus / zoom (+ the single flagged set_view). `load`/`hide_all` are replay-side and never emitted; the `set` op is excluded per plan.
- Deterministic emission order pinned: `//` header comments → per molecule object in alpha order (set_color defs → show_as → color → show → label, primary-rep precedence sticks > cartoon > spheres, extras layered via `show`) → named selections (alpha) → zoom-when-focused → exactly ONE `set_view` (18 floats) LAST, with a stdout WARNING that its dispatch lands in Phase 10.
- Every observed-but-unmappable feature surfaces as a `# NOT CAPTURED: <desc>` comment (multi-state objects, mixed colors/labels, per-atom sphere_scale overrides, non-molecule objects, unrecoverable selection expressions, zoom-under-fallback) — nothing silently dropped, no invented ops.
- Headless smoke proves the round-trip with 10 assertions (>= 6 required), including the no-invented-ops invariant, the single set_view with 18 numbers, and the full pinned emission order `['set_color','show_as','color','label','set_view']`; sentinel `^SMOKE_RESULT: PASS` as the last line.

## Task Commits

Each task was committed atomically:

1. **Task 1: tools/scene_capture.py — read-only session capture emitting MolAction JSON** - `988e093` (feat)
2. **Task 2: tools/scene_capture_smoke.py — headless round-trip proof** - `5d1f822` (feat)

## Files Created/Modified
- `tools/scene_capture.py` — the emitter (458 lines): `capture_scene(cmd)` + read-only probes + `render_capture()` + CLI `main()` with `--out`; pymol/json/sys imports only; python3.6-parseable; no rpg.* imports.
- `tools/scene_capture_smoke.py` — the headless proof (223 lines): scene build + emitter call + 10 `check()` assertions + OBS lines + the SMOKE_RESULT sentinel last.

## Decisions Made
- **Selection fallback pinned (the plan's key empirical question):** pre-implementation probe `tmp/07-19-probe.py` (gitignored, real Windows PyMOL 2.5.0 headless) observed `cmd.get_type("focus_sele")` → `'selection'` (a type tag only) and that the session entry stores resolved atom indices, not the expression (OBS1/OBS4). The plan's "recoverable → select_focus(name, expr)" path is therefore unreachable on this build; the NOT-CAPTURED fallback is the pinned branch (recoverable path retained as a documented seam in `_selection_expression`, which returns None honestly). The smoke asserts the fallback and prints which path fired.
- **zoom-under-fallback:** since no select_focus is ever emitted on 2.5.0, NO zoom op is emitted either — the camera NOT-CAPTURED comment + the exact set_view carry the framing. The smoke pins both branches (fallback active; recoverable branch kept verbatim for a future read API).
- **set_color naming `captured_<idx>`:** deterministic within a capture; the name is arbitrary-but-unique in the replay session because set_color defines it idempotently before the paired `color` op consumes it (documented in the header).
- **Per-atom sphere_scale detection via `iterate s.sphere_scale`:** setting.py:351's docstring documents the `s.` atom-setting namespace; probe OBS12/OBS14 confirmed readable values ([1.0,1.0,1.0] default; [0.3,1.0,1.0] after cmd.set). Any value ≠ global baseline (cmd.get, float('1.00000') = 1.0) → NOT-CAPTURED comment.
- **Fresh-session palette facts:** `get_color_index("hero_cyan") == -1` in a fresh session (OBS6) — the 5-name palette probe (hero_cyan/gray/green/magenta/orange) cannot collide with a custom session-allocated index; the smoke's cyan (idx 5) correctly forces the rgb branch.
- **pymol-namespace main() guard** (deviation, Rule 3 — see below): `if __name__ in ("__main__", "pymol")` so `run tools/scene_capture.py` fires the CLI while `import scene_capture` (the smoke) stays side-effect-free.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] CLI main() never fired under PyMOL `run` (`__name__ == 'pymol'`)**
- **Found during:** Task 2 (post-smoke CLI validation of the run-friendly path)
- **Issue:** The initial `if __name__ == "__main__": main()` guard never fired: PyMOL's `cmd.run()` executes scripts in the pymol package's global namespace (`parsing.py:424 run(namespace='global')` → `run_file(path, ns_pymol, ns_pymol)`), where `__name__ == 'pymol'`, not `'__main__'` — a headless run of tools/scene_capture.py printed nothing.
- **Fix:** Guard widened to `__name__ in ("__main__", "pymol")` with the parsing.py:424 citation; verified `import scene_capture` (smoke path) remains side-effect-free and the headless CLI run now prints the render (empty session degrades gracefully: header + single flagged set_view).
- **Files modified:** tools/scene_capture.py
- **Verification:** headless `run-conda-pymol.bat -cq tools\scene_capture.py` prints the paste-ready render; smoke re-run still SMOKE_RESULT: PASS (no import side-effects)
- **Committed in:** 988e093 (Task 1 commit, pre-Task-2-commit fix)

**2. [Observation, no code change] Smoke checks 5/6 pinned to the observed fallback branch (as the plan anticipated)**
- **Found during:** Task 2 (first headless run)
- **Issue:** The plan's check 5 explicitly allowed either branch ("run once, observe which get_type branch fires... pin the assertion to that observed branch"); observation resolved it to the fallback.
- **Fix:** c5 asserts the NOT-CAPTURED comment naming focus_sele + no select_focus op; c6 asserts no zoom op + the camera NOT-CAPTURED comment (the recoverable branch's zoom assertion retained verbatim in the else-path). No check weakened; the mapping was never "fixed" because the plan's fallback IS the observed reality.
- **Files modified:** tools/scene_capture_smoke.py (assertions as written)
- **Verification:** 10/10 checks PASS headlessly
- **Committed in:** 5d1f822

---

**Total deviations:** 1 auto-fixed blocking issue + 1 observation-pinned branch (both within the plan's own anticipation clauses).
**Impact on plan:** The fix was required for the plan's own "CLI-runnable via `run tools/scene_capture.py`" requirement. No scope creep; molops.py / engine.py / rpg/** byte-untouched (git status showed ONLY the two tools/ files pre-commit).

## Issues Encountered
- None beyond the deviation above. The `index.lock` coordination risk with the parallel 07-18 agent did not materialize (no retries needed).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- This was the last autonomous plan of Phase 7; 07-18 (final gates + human checkpoint) runs in parallel and owns the human review. Phase 7 closes after 07-18's checkpoint.
- Ready for Phase 10: the emitted `{"op":"set_view","args":{"view":[18 floats]}}` entry defines the exact dispatch shape Phase 10 must implement in molops.py (currently raises NotImplementedError by design — flagged with a stdout WARNING on every capture).
- Tool usage for users (Phase 11 docs): in a real PyMOL session, build the scene, then `run tools/scene_capture.py` (prints jsonc: `//` headers + one paste-ready JSON array + `# NOT CAPTURED` annotations) or `--out <path>` to write it.
- Known capture scope (documented in the tool header): object-level reps for the game's three reps (sticks/cartoon/spheres); per-atom rep scoping and non-game reps are beyond the frozen vocabulary and outside capture scope.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-03*
