---
phase: 06-qt-ui-minimal-playable-mvp
plan: 09
subsystem: ui
tags: [pymol.Qt, PyQt5, QDialog, QRadioButton, QButtonGroup, edit-router, EditIntent, curated-options, gate-exempt]

# Dependency graph
requires:
  - phase: 06-06
    provides: "Controller.request_edit (stashes _pending_edit_enzyme_id + gotos edit.prompt) + Controller.build_edit_intent (assembles EditIntent; falls back to _pending_edit_enzyme_id at edit.prompt) + Controller.apply_edit (routes via engine.apply_player_edit -> EditRouter)"
  - phase: 04-02
    provides: "EditRouter (known signature -> branch_node; unknown -> bad-ending pool) + EditsTable.load(c14/data/edits.json) — the curated lookup table this dialog reads"
  - phase: 01-02
    provides: "c14.paths.data_path (cwd-independent edits.json resolver; Pitfall 1 mitigation)"
provides:
  - "EditDialog(QtWidgets.QDialog) — curated edit-options dialog per enzyme (reads c14/data/edits.json known edits + a few plausible wrong options) -> (op, target, args) tuple via selected_edit()"
  - "EditDialog.submit static helper bundling build_edit_intent + apply_edit (the 06-06/06-08 seam convenience)"
affects: [06-qt-ui-minimal-playable-mvp, 06-08-main-window, 06-14-human-verify, phase-07-content-glucose]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Curated-options dialog (NOT free-form entry): reads edits.json known edits + hardcoded plausible wrong options -> EditIntent whose signature() routes via EditRouter (known -> branch, unknown -> bad pool)"
    - "QButtonGroup.addButton(radio, idx) + checkedId() to map radio selection to an options-list index"
    - "Gate-EXEMPT Qt file (c14/ui/ in check_imports.py SKIP_DIRS); py_compile is the only WSL-verifiable check; functional flow is human-verify"

key-files:
  created:
    - c14/ui/edit_dialog.py
  modified: []

key-decisions:
  - "Curated, NOT free-form: the dialog offers a radio list (known edits from edits.json + a few hardcoded plausible wrong options) — free-form residue-entry would always route to the bad-ending pool (unfun + not the curated-table design per PROJECT.md:80)"
  - "Wrong options are generic amino-acid codes (ALA/GLY) — gameplay attempts, NOT fabricated disease mutations (05.4 no-fabricated-science); they route to the existing bad-ending pool via the EditRouter (no new story nodes)"
  - "submit() calls the declared 06-06/06-08 seam verbatim (build_edit_intent + apply_edit); the apply_edit-at-edit.prompt stash-fallback tension is a 06-06 controller concern, NOT 06-09's (Warning 4 file ownership: 06-09 owns only edit_dialog.py)"
  - "Enzyme with no known edits shows an informational message + a single generic wrong option (routes to the bad-ending pool — a valid outcome; Phase 7 fills the real per-enzyme entries)"

patterns-established:
  - "Pattern: curated edit-options dialog reads c14/data/edits.json for known edits + adds plausible wrong options; the player picks one radio -> (op, target, args) -> controller.build_edit_intent -> EditRouter routes. Phase 7 fills edits.json; the dialog structure is the contract Phase 7 fills."

# Metrics
duration: 2 min
completed: 2026-08-30
---

# Phase 6 Plan 09: EditDialog (Curated Edit Options -> EditIntent) Summary

**EditDialog (gate-EXEMPT Qt QDialog) offering curated edit options per enzyme from c14/data/edits.json + plausible wrong options, returning an (op, target, args) tuple the controller assembles into an EditIntent routed by the EditRouter (known -> branch, unknown -> bad-ending pool)**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-08-29T18:20:43Z
- **Completed:** 2026-08-29T18:23:31Z
- **Tasks:** 1
- **Files modified:** 1 (created)

## Accomplishments

- Built `c14/ui/edit_dialog.py` — the SC1 "edit interface" + EDIT-01/02/03 UI surface. `EditDialog(QtWidgets.QDialog)` offers a CURATED radio list of edit options per enzyme (NOT free-form residue-entry): known edits read from `c14/data/edits.json` (labeled "Restore <target> to <new_res> (the correct fix)") + a few plausible wrong options hardcoded for Phase 6 (generic point mutations `resi 1 -> ALA` / `resi 2 -> GLY` that don't match the table -> bad-ending pool).
- `selected_edit()` returns the selected `(op, target, args)` tuple (or None on cancel); the controller assembles the `EditIntent` via `build_edit_intent(op, target, args)` and routes it via `apply_edit` -> `engine.apply_player_edit` -> `EditRouter` (known signature match -> `branch_node`; unknown -> bad-ending pool).
- `submit(controller, enzyme_id, parent=None)` static helper bundles the declared 06-06/06-08 seam: opens the dialog, on accept calls `build_edit_intent` + `apply_edit`, returns the TurnResult (or None on cancel).
- Enzyme with NO known edits in `edits.json` (Phase 7 fills them) shows an informational message ("No known edits for this enzyme yet (Phase 7 content). Your edit will route to the bad-ending pool.") + a single generic wrong option so the player can still attempt an edit (routes to the bad-ending pool — a valid game outcome). The Phase 6 placeholder `fixture_enzyme_1` (1 known edit: point_mutation `resi 1 -> GLY`) is handled.
- WARNING 4 file ownership honored: 06-09 owns ONLY `c14/ui/edit_dialog.py`; it CONSUMES the 06-06 (`request_edit` + `_pending_edit_enzyme_id` + `build_edit_intent` + `apply_edit`) and 06-08 (`render_turn` detects `edit.prompt` -> opens EditDialog) seam without modifying `controller.py` or `main_window.py` (3 parallel wave-4 plans, non-overlapping files).

## Task Commits

Each task was committed atomically:

1. **Task 1: Create c14/ui/edit_dialog.py — EditDialog (curated edit options -> EditIntent)** - `d6aec19` (feat)

**Plan metadata:** (to be committed after this SUMMARY)

## Files Created/Modified

- `c14/ui/edit_dialog.py` — `EditDialog(QtWidgets.QDialog)` (curated edit options per enzyme from `edits.json` + plausible wrong options -> `(op, target, args)` via `selected_edit()`; `submit()` static helper bundles `build_edit_intent` + `apply_edit`). Gate-EXEMPT (`c14/ui/` in `check_imports.py` SKIP_DIRS); reads `c14/data/edits.json` via `c14.paths.data_path` (cwd-independent).

## Decisions Made

- **Curated radio list, NOT free-form entry.** PROJECT.md:80 settles the edit-routing model as a curated lookup table + bad-ending fallback (NOT a chemistry-correctness engine). The dialog offers a radio list of curated options (known edits + plausible wrongs); free-form residue-entry would produce `EditIntent`s whose `signature()` matches nothing and always routes to the bad-ending pool (a valid but unfun outcome). The curated list makes the edit a meaningful choice.
- **Wrong options are generic amino-acid codes (ALA/GLY), NOT fabricated disease mutations.** Per 05.4-CONVENTION.md no-fabricated-science, the wrong options are standard amino-acid codes used as gameplay attempts (the player tries an edit; if it doesn't match the table, the game routes to the bad-ending pool — "your edit didn't restore the enzyme"). No real PDB IDs, no fabricated disease mutations. The known edit (`resi 1 -> GLY`) is the placeholder fixture in `edits.json` (claim_id `PLACEHOLDER_PHASE5`).
- **`submit()` calls the declared seam verbatim.** The plan's `submit` helper calls `controller.build_edit_intent(op, target, args)` + `controller.apply_edit(intent)` as specified. 06-06's `apply_edit` reads the enzyme_id from the CURRENT node's `edit:enzyme:<id>` tag and raises `RuntimeError` when that node has no such tag (e.g. at `edit.prompt`). The 06-08 seam calls `apply_edit` at `edit.prompt`; for it to succeed there, 06-06's `apply_edit` must also fall back to `_pending_edit_enzyme_id` (or use `edit_intent.enzyme_id`). That fix is in 06-06's file (`controller.py`) — OUT OF SCOPE for 06-09 (Warning 4 file ownership: 06-09 owns only `edit_dialog.py`). This helper calls the declared seam verbatim; the integration is verified in 06-14.
- **Forward-compatible labels for all 3 EDIT op types.** `_label_for_known` handles `point_mutation` / `substrate_edit` / `protonation_change` (EDIT-01/02/03). For Phase 6 only `point_mutation` is used (`fixture_enzyme_1`); the substrate_edit / protonation_change branches are forward-compatible for Phase 7.

## Deviations from Plan

None - plan executed exactly as written. (The `apply_edit`-at-`edit.prompt` seam tension is a pre-existing cross-plan design concern between 06-06 and 06-08, documented under Decisions + Next Phase Readiness; it is NOT a 06-09 deviation — 06-09 consumed the seam as declared and did not modify `controller.py` per Warning 4 file ownership.)

## Issues Encountered

- **Seam tension (06-06 `apply_edit` at `edit.prompt`):** 06-06's `Controller.apply_edit` reads the enzyme_id from the current node's `edit:enzyme:<id>` tag and raises `RuntimeError` when the current node has no such tag (test_controller.py test #6 `test_apply_edit_raises_when_no_enzyme_tag` confirms this at `intro.preface`). The 06-08/06-09 seam calls `apply_edit` at `edit.prompt` (which has tag `edit:prompt`, not `edit:enzyme:<id>`), so `apply_edit` would raise there. `build_edit_intent` DOES fall back to `_pending_edit_enzyme_id` at `edit.prompt` (test #17 confirms), but `apply_edit` does NOT. This is a cross-plan seam inconsistency between 06-06 (controller) and 06-08/06-09 (the edit.prompt seam). Resolving it requires a one-line fix in 06-06's `controller.py` (`apply_edit` falls back to `_pending_edit_enzyme_id` or uses `edit_intent.enzyme_id` when `_current_enzyme_id()` is None) — OUT OF SCOPE for 06-09 per Warning 4 file ownership. Documented here for 06-06/06-08 integration + 06-14 human-verify. Not a 06-09 code defect (06-09's `submit` calls the declared seam verbatim; the dialog + `selected_edit` API are correct).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **06-09 delivers the EditDialog API** (`EditDialog(controller, enzyme_id, parent)` + `selected_edit()` + `submit()`). 06-08 (main_window.py) wires it: `render_turn` detects `turn.node.id == "edit.prompt"` -> opens `EditDialog(self._controller, self._controller._pending_edit_enzyme_id, self)` -> on accept `controller.build_edit_intent(...)` + `controller.apply_edit(intent)` (or calls `EditDialog.submit(...)`).
- **Seam to resolve before 06-14 human-verify:** 06-06's `Controller.apply_edit` should fall back to `_pending_edit_enzyme_id` (or use `edit_intent.enzyme_id`) when the current node has no `edit:enzyme:<id>` tag, so the edit.prompt -> EditDialog -> apply_edit flow succeeds. This is a one-line fix in `c14/ui/controller.py` (06-06's file). Until then, the 06-08 MainWindow can either (a) call `apply_edit` at the edit-allowed SOURCE node before `request_edit` (Flow A — works with the current 06-06 controller), or (b) rely on the 06-06 fix. The 06-09 EditDialog + `selected_edit` + `submit` API is correct either way.
- **Functional human-verify in 06-14:** the curated options render (known "correct fix" + plausible wrongs), a selection builds an EditIntent whose `signature()` routes via the EditRouter (known -> `fixture.branch_1`; unknown -> bad-ending pool `bad.lost_connection`/`bad.released_from_host`), and the routed node's `on_enter` plays. py_compile is the only WSL-verifiable check here (importing `pymol.Qt` fails in WSL — EXPECTED for a gate-EXEMPT Qt file).
- **Phase 7 fills `edits.json`** with the real per-enzyme known edits; the EditDialog auto-renders them (no code change — it reads `edits.json` at construction). The wrong-options list is the Phase 6 hardcoded placeholder; Phase 7 may expand it per enzyme (the `_plausible_wrong_options` static method is the single point of contact).

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-30*
