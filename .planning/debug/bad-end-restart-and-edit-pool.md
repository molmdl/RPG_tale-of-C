---
status: diagnosed
trigger: "SYMPTOM 1: 'restarting the game after bad end or reopening after closing, both with the bad end persist all the time.' SYMPTOM 2: 'cant edit anything, attempting edit always bad end it seems. shouldnt we be restoring mutant from our story?' + mandated regression scan of 81b1a48/245f88f/68631dd/bacbb09. Diagnosis ONLY (find_root_cause_only)."
created: 2026-08-30T17:00:00+08:00
updated: 2026-08-30T18:05:00+08:00

## Current Focus

hypothesis: RESOLVED. S1: controller/engine restart is CLEAN (headless-proven); the persistence is TWO Qt-view defects: (1) StoryPanel.render_node never hides the ending banner (widgets.py:107-119; only clear():134-139 hides it and MainWindow never calls it) -> "Ending reached: Bad" survives New Game/Load forever; (2) plugin_entry.py:19-27 re-SHOWS the same hidden MainWindow singleton on window reopen (no closeEvent, no re-render on show) -> the last render (the ending) reappears. S2: shipped rpg/data/edits.json contains ONLY fixture_enzyme_1 -> every real-enzyme edit routes to the global bad-ending pool; MECHANISM PROVEN INTACT headlessly (injected known entry -> branch node). The skeleton has NO restoration branch nodes at all -> Phase 7 content.
test: 3 headless probe scripts (pure WSL python3.6, MockMolOps/MockView, real graph): probe_restart_after_ending.py (A/B/E), probe_edit_routing.py (C1-C4), probe_offer_once_and_return.py (D1-D4) — all PROBE_RESULT: PASS, 0 failures, 42 checks.
expecting: n/a (diagnosed)
next_action: return diagnosis + fix designs (no file changes except this doc)

## Symptoms

expected: (S1) 'Start a new game' on the ending screen restarts the game at intro.preface; closing/reopening the window shows the current game state. (S2) edit attempts route to the story's restoration branches (5.1 disease-mutant reversal branches + 5.3 WT-aligned restore reveal).
actual: (S1) the bad ending view persists after Start-new-game AND after window close/reopen. (S2) every edit attempt lands in a bad-ending-pool node.
errors: none reported (no traceback) for either symptom.
reproduction: (S1) reach a bad ending (edit attempts or cycle-trap) -> Start a new game -> ending persists; close window + reopen -> ending persists. (S2) any edit attempt at any enzyme.
started: after 06-14 re-verify round 2 (81b1a48/245f88f/68631dd) + rename bacbb09; human-verified in real Windows PyMOL.

## Eliminated

- hypothesis: S1 stuck re-entrancy guard (_resolving_shuffle not reset on the trap auto-fire path)
  evidence: controller.py:706-710 sets True + resets in a finally on ALL paths; probe A: guard False immediately after the auto-fired ending AND after the restart; restart on the SAME controller lands intro.preface, finished=None, view re-rendered, state fresh.
  timestamp: 2026-08-30T17:55
- hypothesis: S1 engine-level dirty state on restart
  evidence: engine.py:108-120 start() replaces rng+state wholesale (orchestrator pre-check); probe A/B: visit_counts/edits_history fresh after restart; GameState.new_game resets everything.
  timestamp: 2026-08-30T17:55
- hypothesis: S1 achievement-board corruption / double-fire on a used controller
  evidence: achievements.py fully idempotent (dedupe by id/node/character); probe A: on_turn fired exactly once per start (new_game_calls==2 after 2 starts), endings_found deduped, no raise.
  timestamp: 2026-08-30T17:55
- hypothesis: S1 an exception in the Qt _new_game -> start_game path aborting before _render
  evidence: every step is exception-safe or already proven in the real session: molops dispatch swallowed (Blocker 1 fix c), count_fn try/except (HeroResolver), board idempotent no-write on restart; the real stack's re-entry into intro.preface on_enter after an ending is ALREADY proven by smoke stage 7 (fresh controller, same cmd, hero_atom/aa_cast already loaded from stage 6 -> SMOKE_RESULT: PASS). No plausible raise; the controller ALWAYS calls view.render_turn on restart (probe A: view grew).
  timestamp: 2026-08-30T18:00
- hypothesis: S2 signature-shape mismatch between EditDialog options and the table (a NOW seam bug)
  evidence: probe C3/C2 — EditDialog builds (op,target,args) STRAIGHT from the table's signature dict (edit_dialog.py:288-294) so the round-trip is exact BY CONSTRUCTION; EditIntent.signature() canonicalization verified (target strip+lower, args stringified-not-lowered, op case-sensitive); injected known entry routed to the branch node with noise-padded input.
  timestamp: 2026-08-30T18:00
- hypothesis: S2 enzyme_id lookup failure (stashed id vs table keys)
  evidence: probe C1: request_edit('gly.pfk') -> stash 'gly.pfk' -> build_edit_intent enzyme_id 'gly.pfk' -> route() lookup runs correctly; the failure is the TABLE having no 'gly.pfk' key, not the lookup.
  timestamp: 2026-08-30T18:00
- hypothesis: stale c14 plugin copies / duplicate module objects / rename leftovers at runtime
  evidence: zero c14 references in rpg/ tools/ tests/ (grep); no c14/ dir exists; dist/rpg-0.0.1-dev.zip rpg-only; __pycache__ holds only rpg.* (a stale c14 package is unimportable since the dir is gone).
  timestamp: 2026-08-30T17:50

## Evidence

- timestamp: 2026-08-30 (orchestrator)
  checked: %APPDATA%\pymol; engine.py:108-120; smoke stages
  found: only rpg-tale-of-c user data; engine start() replaces rng+state; the smoke NEVER restarts on the same controller (stage 6 ends at the bad ending; stage 7 builds a fresh controller).
  implication: restart bug would escape all tests; stale code ruled out.
- timestamp: 2026-08-30T17:40
  checked: rpg/ui/widgets.py StoryPanel
  found: render_ending (121-132) shows the gold bold "Ending reached: <tier>" banner; render_node (107-119) sets dramatic/teaching text but NEVER touches the banner; clear() (134-139) hides it but is NEVER called by MainWindow (main_window.py calls _story.render_node/render_ending only; the only .clear() calls are ChoicePanel's: main_window.py:327 + widgets.py:214/243).
  implication: after ANY ending, every later render (new game, load, edit.prompt) keeps the ending banner visible forever. With placeholder intro text ("TBD - ..."), the story panel keeps looking like the ending -> "the bad end persists / the game does not appear to restart". (The choice panel + status bar DO update.)
- timestamp: 2026-08-30T17:42
  checked: rpg/ui/plugin_entry.py (9, 19-27); MainWindow (no closeEvent override anywhere in main_window.py)
  found: module-level singleton _main_window; menu callback = "if None: construct; .show() + .raise_()". Qt default close on a QMainWindow (no closeEvent override, WA_DeleteOnClose off) HIDES the window without destroying it; no re-render happens on show.
  implication: window close -> reopen in the SAME PyMOL process re-shows the SAME instance with whatever was last rendered (the ending) -> "closing the window and reopening -> the bad ending is still showing". A FULL PyMOL restart gives a fresh window ("Ready - click New Game") where an ending cannot show without playing -> the human's "restart" report is then the quick RE-ARRIVAL at a bad ending via S2 (every edit -> pool), not persisted state.
- timestamp: 2026-08-30T17:55
  checked: PROBE A (probe_restart_after_ending.py; pure WSL; MockMolOps/MockView; real glucose graph; prompt auto-confirm; offer declined)
  found: walk to tca.shuffle -> offer declined -> auto-spin (co2_turn2) -> 5x "cycle turns again" -> at entry 6 the trap AUTO-FIRED -> bad.cycle_trap_host_death, finished=True, _resolving_shuffle=False immediately after; the shuffle turn was NEVER rendered; bad ending recorded once. THEN start_game("glucose", 42) on the SAME controller: intro.preface, finished=None, guard False, view turns 20->21 with last=intro.preface, visit_counts fresh (tca.shuffle absent), edits_history [], new_game_calls==2 (no double), characters_tried==['glucose'].
  implication: hypothesis 1 (stuck guard) KILLED; the controller-level restart is fully clean on the trap path.
- timestamp: 2026-08-30T17:55
  checked: PROBE B (same script; edit-path ending)
  found: at gly.pfk: request_edit -> edit.prompt (enzyme+source stashed) -> build_edit_intent(point_mutation, resi 1, {new_res: ALA}) (the dialog's generic wrong option) -> apply_edit -> bad.released_from_host (bad ending), finished=True, both stashes cleared (B1). THEN start_game("glucose", 7) on the SAME controller: intro.preface, finished=None, guard False, view grew.
  implication: the edit-path ending restarts cleanly too -> the S1 mechanism is NOT in the controller on EITHER ending path.
- timestamp: 2026-08-30T17:58
  checked: PROBE E (same script)
  found: request_edit at gly.pfk (stashes set) -> start_game again -> BOTH stashes SURVIVE the restart (enzyme='gly.pfk', source='gly.pfk' from the PREVIOUS game).
  implication: latent stale-stash seam (LOW: unreachable via the current UI — the EditDialog is modal so the toolbar is blocked while open; after Cancel the return button is destroyed by the next render; every request_edit re-stashes) — defense-in-depth fix recommended.
- timestamp: 2026-08-30T18:00
  checked: PROBE C (probe_edit_routing.py)
  found: C4: shipped rpg/data/edits.json enzymes == {fixture_enzyme_1} ONLY; the real graph has 14 edit-allowed nodes / 13 unique enzyme ids (etc.complex_i..iv, gly.pfk, gly.pyruvate_kinase, pyr.pdh, tca.aconitase, tca.citrate_synthase, tca.fumarase, tca.isocitrate_dh, tca.malate_dh, tca.succinyl_coa_synthetase); intersection EMPTY; fixture.branch_1 (the fixture entry's branch_node) does not even exist in the glucose graph; pool == [bad.lost_connection, bad.released_from_host] (both bad endings). C1: at gly.pfk, the dialog's only option (generic wrong) -> routed to the pool, is_ending='bad', game finished. C2: injecting a known gly.pfk entry (point_mutation / resi 479 / {new_res: ARG} -> branch_node gly.fbp_to_pyruvate) -> EXACT signature match (even with '  RESI 479 ' noise) -> routed to the branch node, is_ending=None, game continues, on_enter dispatched; the wrong option still routes to the pool. C3: EditIntent.signature() round-trips the fixture entry exactly; op is CASE-SENSITIVE; target strip+lower; args stringified (str(v).strip()) but NOT case-folded.
  implication: S2 is a CONTENT GAP (Phase 6-EXPECTED), NOT a mechanism bug. The dialog even prints "No known edits for this enzyme yet (Phase 7 content). Your edit will route to the bad-ending pool."
- timestamp: 2026-08-30T18:02
  checked: data/story_glucose/*.json grep (restore|reversal|mutant|edit.<x> nodes) + 05.1 planning docs
  found: ZERO restoration branch nodes in the frozen 55-node skeleton (no *_restored nodes; the only edit-related nodes are edit.prompt + the 1a/1b bad endings). 05.1-RESEARCH-disease-mutants-glycolysis.md:245-259 PROPOSED gly.pfk_restored / gly.pyruvate_kinase_restored / pyr.pdh_restored branch_nodes; 05.1-DESIGN.md:540 describes "known-edit branch node -> 'you restored the enzyme!'"; the 1b known-consequence bad endings (bad.active_site_destroyed / bad.substrate_channel_blocked / bad.cofactor_lost / bad.critical_residue_break) exist as nodes with binding = Phase 7 edits.json content (05.1-15-PLAN.md OQ-BAD-2).
  implication: the human's expected "restoration branches from our story" DO NOT EXIST YET — Phase 7 must add BOTH the edits.json entries AND the restore branch nodes (+ the 5.3 WT-aligned loads in their on_enter). The routing plumbing for them is proven (probe C2).
- timestamp: 2026-08-30T18:03
  checked: PROBE D (probe_offer_once_and_return.py; regression scan)
  found: D1: the shuffle edit-offer fires EXACTLY ONCE (visits==1 on first entry — record_visit bumps 0->1 BEFORE _auto_resolve_shuffle reads it); never again through entry 6 + the trap fire. D2: save/load preserves visit_counts (loaded at co2 with visits=2; the loaded game's return to the shuffle auto-spins with NO re-offer). D3: offer ACCEPTED -> request_edit -> edit.prompt (stash enzyme=tca.aconitase, source=tca.shuffle) -> return_to_edit_source -> goto shuffle -> visits=2 -> NO offer -> auto-spin; guard False; stashes cleared; the shuffle never rendered (no loop). D4: no stash -> returns None.
  implication: the 81b1a48/245f88f auto-resolve + return seams are behaviorally correct on all probed paths.
- timestamp: 2026-08-30T18:04
  checked: rpg/data/cast.json; rename sweep; run_headless.sh
  found: cast.json is placeholder-only (fixture_enzyme_1 + PLACEHOLDER_large_enzyme) — the whole per-enzyme content layer (cast + edits table) is Phase 7 and must keep the shared-manifest invariant (edits.json keys == cast ids == graph edit:enzyme:<id> values). Rename clean (see Eliminated). run_headless.sh = cmd-level harness (SMOKE_RESULT sentinel) — not needed for these two symptoms (both resolved without cmd-level questions; Qt is out of its reach anyway).
  implication: no runtime rename risk; the Phase 7 content work has a precise shape.

## Resolution

root_cause: |
  S1 (bad ending persists across restart): TWO Qt-view defects — the controller/engine restart is CLEAN (proven headlessly on both ending paths). (1) PRIMARY: rpg/ui/widgets.py StoryPanel.render_node (107-119) never hides the ending banner that render_ending (121-132) shows; only clear() (134-139) hides it and MainWindow never calls it (main_window.py renders story via render_node/render_ending only). So after ANY ending, "Ending reached: Bad" stays on screen through New Game/Load/every node — with placeholder intro text the story panel keeps looking like the ending (the choice panel + status bar DO update). (2) SECONDARY: rpg/ui/plugin_entry.py (9, 19-27) re-shows the SAME hidden MainWindow singleton on window reopen (Qt default close = hide; no closeEvent; no re-render on show) -> the last render (the ending) reappears verbatim. A full PyMOL restart cannot show an ending without playing; the human's persistent-bad-end experience across "restarts" is compounded by S2 (every edit -> a bad ending again).
  S2 (every edit -> bad ending): Phase 6-EXPECTED CONTENT GAP, mechanism INTACT (proven). The shipped rpg/data/edits.json contains ONLY the Phase-4/5 placeholder enzyme fixture_enzyme_1 (whose branch_node fixture.branch_1 does not even exist in the glucose graph); NONE of the 13 real enzyme ids (14 edit-allowed nodes) has an entry, so EditDialog._build_options falls to has_known=False (it even shows "No known edits for this enzyme yet (Phase 7 content). Your edit will route to the bad-ending pool." + offers ONE generic wrong option) and EditRouter.route falls to the global pool [bad.lost_connection, bad.released_from_host] -> bad ending every time. The restoration branch nodes the human expects (gly.pfk_restored etc.) were PROPOSED in 05.1 research but were never added to the frozen 55-node skeleton — they are Phase 7 content, together with the table entries and the 5.3 WT-aligned restore loads.
fix: (diagnosis only — see the fix designs in the report)
verification: 42 headless probe checks PASS across 3 scripts (restart on the same controller after BOTH ending kinds; edit routing mechanism + canonicalization; offer-once + save/load visit semantics + return_to_edit_source edges); code-level confirmation for the two Qt defects (banner lifecycle + singleton reopen); all Eliminated hypotheses evidence-backed.
files_changed: []
