---
status: diagnosed
trigger: "Edit dialog fails with RuntimeError: cannot build EditIntent: current node 'edit.prompt' has no edit:enzyme:<id> tag and no pending enzyme_id stash — reached via generic choose(i) path at widgets.py:316 instead of request_edit seam"
created: 2026-08-30T16:20:53+08:00
updated: 2026-08-30T16:33:00+08:00

## Current Focus

hypothesis: CONFIRMED + empirically reproduced headlessly (probe in /tmp/opencode). Root cause: the edit:offer->request_edit routing exists only in ChoicePanel._render_mixed; pure-MC edit-allowed nodes (gly.pfk etc.) route the edit choice through the generic choose(i) lambda, so edit.prompt is entered via engine.choose with the stash never set.
test: probe script reproduced the exact RuntimeError + verified request_edit works at the same node
expecting: n/a
next_action: return diagnosis (find_root_cause_only mode — no fix applied)

## Symptoms

expected: clicking the edit affordance on the first enzyme opens the EditDialog
actual: RuntimeError from controller.build_edit_intent — node 'edit.prompt' has no edit:enzyme tag and no pending stash
errors: RuntimeError at controller.py:442 raised through main_window.py:432 <- 319 <- controller.py:559 <- controller.py:347 <- widgets.py:316 lambda
reproduction: start glucose game, advance to first enzyme shown, click edit affordance — 100% repro in real Windows PyMOL
started: human-verified in real Windows PyMOL session (reproducible)

## Eliminated

- hypothesis: engine.choose could land on edit:offer at the MIXED tca.shuffle node
  evidence: interpreter.pick_choice (interpreter.py:60-73) RNG-picks among weighted-only when any weighted eligible; probe: 40 seeds, choose(0)/choose(1) at shuffle always landed on co2_turn1/turn2, never edit.prompt
  timestamp: 2026-08-30T16:33
- hypothesis: _pending_edit_enzyme_id is cleared somewhere / lost
  evidence: grep + read of controller.py — stash written only at request_edit (controller.py:417), never cleared; probe shows it stays None when request_edit was never called
  timestamp: 2026-08-30T16:33

## Evidence

- timestamp: 2026-08-30T16:25
  checked: c14/ui/widgets.py ChoicePanel.render_turn/_render_pure/_render_mixed
  found: edit:offer->request_edit special-case exists ONLY in _render_mixed (widgets.py:269-278), gated on controller.is_mixed_weighted_node(node) (widgets.py:215-218). _render_pure (widgets.py:288-319) routes EVERY eligible choice of a pure-MC node through generic choose(i) lambda at widgets.py:316 — including an edit:offer choice with goto edit.prompt.
  implication: on a pure non-weighted edit-allowed node, the edit button advances via choose(), never calling request_edit, so the stash is never set.
- timestamp: 2026-08-30T16:25
  checked: data/story_glucose/glycolysis.json + grep edit.prompt across story JSONs
  found: gly.pfk (glycolysis.json:30-42) is the first enzyme node on the glucose path that loads a PDB (pdb:4PFK) and offers an edit choice: {"label": "Try to edit PFK's active site", "goto": "edit.prompt", "tags": ["edit:offer"]} (line 41) — NO weight field. Its node tags carry edit:enzyme:gly.pfk (line 34). 15 nodes across the story offer edit via goto edit.prompt; ALL are pure non-weighted EXCEPT tca.shuffle (tca.json:44-57, mixed: 2 weighted 0.5/0.5 + edit:offer + cond-gated cycle-trap).
  implication: user tested gly.pfk (first enzyme shown in viewer). is_mixed_weighted_node(gly.pfk) == False (no weighted choices) -> _render_pure -> generic choose(i) -> engine.choose lands on edit.prompt with empty stash.
- timestamp: 2026-08-30T16:25
  checked: c14/ui/controller.py request_edit/build_edit_intent/_current_enzyme_id/_render; c14/ui/main_window.py render_turn/_open_edit_dialog; c14/ui/edit_dialog.py
  found: _pending_edit_enzyme_id is set ONLY in request_edit (controller.py:417); never cleared. build_edit_intent (controller.py:438-445) reads current node's edit:enzyme tag (edit.prompt has none — bad_endings.json:161 tags:["edit:prompt"]) -> falls back to stash -> RuntimeError at controller.py:442. MainWindow.render_turn detects node.id=="edit.prompt" (main_window.py:312) -> _open_edit_dialog (line 319) opens EditDialog even with enzyme_id=None (header "Edit None", generic wrong option default-checked) -> on OK, build_edit_intent raises exactly the reported RuntimeError at main_window.py:432.
  implication: mechanism fully confirmed end-to-end. engine.choose (engine.py:122-149) happily follows choice.goto="edit.prompt" via _enter — nothing in the engine or controller guards edit.prompt against being entered via choose().
- timestamp: 2026-08-30T16:30
  checked: history of the seam: 06-06-PLAN.md:133, 06-08-SUMMARY.md, tests/test_glucose_reachability.py:203-262
  found: the 06-06 seam was specified when tca.shuffle was the ONLY edit-offering node (a mixed node). The Phase 5.1 disease-mutant replan (05.1-07/08/09) later added edit:offer choices to 13 more nodes — all pure-MC — with a reachability test enforcing them (test_glucose_reachability.py:253-262), but the ChoicePanel was never extended.
  implication: content/UI drift — the UI seam assumption (edit:offer only ever appears at a mixed node) silently became false.
- timestamp: 2026-08-30T16:33
  checked: EMPIRICAL probe (pure-WSL python3.6, MockMolOps/MockView, real glucose graph) — /tmp/opencode/probe_edit_prompt_bug.py
  found: walk to gly.pfk; is_mixed_weighted_node=False; edit choice at eligible index 1; choose(1) -> node edit.prompt with stash None; build_edit_intent raises EXACTLY "cannot build EditIntent: current node 'edit.prompt' has no edit:enzyme:<id> tag and no pending enzyme_id stash". Control: request_edit(_current_enzyme_id()) at gly.pfk -> stash 'gly.pfk' -> build_edit_intent returns enzyme_id 'gly.pfk'.
  implication: root cause REPRODUCED + the designed seam VERIFIED working at the same node.
- timestamp: 2026-08-30T16:35
  checked: EMPIRICAL probe 2 (tca.shuffle semantics) — /tmp/opencode/probe_tca_shuffle_semantics.py
  found: 40 seeds: choose(0) at tca.shuffle landed ONLY on tca.co2_turn1 (19x) / tca.co2_turn2 (21x) — the RNG picks among weighted-only, index ignored. take_choice(trap) at visits=1 -> cond False (correct); forced trap via goto -> bad.cycle_trap_host_death ending; trap entry does NOT bump tca.shuffle visits (only the target's); rng_state synced.
  implication: the proposed auto-spin (engine.choose(0)) + auto-fire (take_choice/goto) mechanics are semantically safe for the SC2f design.

## Resolution

root_cause: The ChoicePanel's edit:offer->request_edit routing exists ONLY in the mixed-weighted rendering mode (widgets.py:269-278, gated by is_mixed_weighted_node at widgets.py:215-218). The user's node — gly.pfk, the first enzyme on the glucose path — is a PURE non-weighted (pure-MC) node, so its "Try to edit PFK's active site" choice (glycolysis.json:41, goto edit.prompt, tag edit:offer, no weight) renders through _render_pure's generic per-choice lambda (widgets.py:316) -> controller.choose(1) (controller.py:331-348) -> engine.choose follows choice.goto and _enter("edit.prompt") (engine.py:137-149). request_edit — the ONLY writer of _pending_edit_enzyme_id (controller.py:417) — never ran, so at edit.prompt (no edit:enzyme tag, bad_endings.json:161) build_edit_intent (controller.py:438-445) finds both sources None and raises RuntimeError at controller.py:442. Origin: the Warning-4 seam was designed when tca.shuffle was the only edit-offering node (mixed); the Phase 5.1 replan added edit:offer choices to 13 pure-MC nodes without extending the UI.
fix: (diagnosis only — see report for recommended SC2f design: route edit:offer/goto-edit.prompt choices through request_edit in _render_pure, matching _render_mixed)
verification: headless probe reproduced the exact RuntimeError and verified the designed seam works at gly.pfk; user traceback matches line-for-line.
files_changed: []
