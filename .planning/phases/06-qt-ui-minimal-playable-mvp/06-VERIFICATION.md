---
phase: 06-qt-ui-minimal-playable-mvp
verified: 2026-08-30T12:05:29Z
status: passed
score: 5/5 ROADMAP Success Criteria passed (60/60 machine-verifiable must-haves verified; all headline fixes human-confirmed across rounds 1-3; remaining items are documented Phase-7/11/12 queues, not phase gaps)
date: 2026-08-30
re_verification:
  previous_status: human_needed
  previous_score: 60/60 machine-verifiable must-haves (33 artifacts + 27 key links) verified; 4/5 ROADMAP SCs human-PASSED; SC2 fixes pending GUI re-check
  gaps_closed:
    - "SC2a single-hero highlight — fix 389ee3e (`first (obj and elem C)`) human-confirmed 'SC2a pass'; smoke exactly_one_YOU=True re-proven this session"
    - "SC2f edit-dialog crash + empty-stash seam — fixes c2d1008 (3-tuple) + 68631dd (request_edit in pure-MC mode) exercised end-to-end by the human's round-3 play (edits reached edit.prompt and routed through the dialog)"
    - "SC2b orientation — fix 3f483aa (status bar node+stage) shipped and in use across rounds 2-3"
    - "Bad-end banner persistence — fix 8c2d344 human-confirmed: 'ok the bad end banner gone' (+ 33ddbc1 stash clear, 4277a4e smoke stage 6b)"
    - "Symptom 2 (every edit → bad ending) — accepted verdict: Phase-6-EXPECTED content gap, routing mechanism PROVEN; Phase 7 content queue"
    - "Design decisions resolved by the human: cycle-trap auto-fire + soul-jump auto-RNG (81b1a48); fuller inline help deferred to Phase 11 (f413dbb); package rename c14→rpg (bacbb09, machine-proven)"
  gaps_remaining: []
  regressions: []
---

# Phase 6: Qt UI + Minimal Playable MVP — Verification Report

**Phase Goal:** The game is playable end-to-end for the first time in a real Windows PyMOL session — install the plugin, start a glucose game, see the C14 hero highlighted (5.4 convention), make choices (5.1 choice-point contract), edit molecules (5.1 edit-node contract), save/load, reach a True or Bad ending — with the UI as a thin adapter over the proven engine + molecular layer. FIRST human-verify milestone.
**Verified:** 2026-08-30T12:05:29Z (FINAL close-out after 3 re-verify rounds)
**Status:** PASSED — all machine gates green this session; the human confirmed the headline fixes across rounds 1-3 and closed the phase; the remaining items are documented Phase-7/11/12 content queues, not Phase 6 gaps.
**Re-verification:** Yes — final close-out (round-1 report below kept intact for history)

---

## Final close-out (2026-08-30)

### Final machine-gate results (run in THIS session, 2026-08-30T12:05Z)

| Gate | Command | Result |
| --- | --- | --- |
| Unit suite | `python3.6 -m unittest discover -s tests` | **Ran 324 tests … OK** (5.3s) |
| Import gate | `python3.6 tools/check_imports.py` | **clean (no pymol/PyQt5 imports in rpg/ domain tier)**, exit 0 |
| Alter gate | `python3.6 tools/check_alter_gate.py` | **clean (no *.alter(...) outside rpg/pymol_layer/edit_ops.py)**, exit 0 |
| Frozen-skeleton invariants | `python3.6 -m unittest tests.test_glucose_reachability` | **Ran 20 tests … OK** — 55 nodes / 21 endings asserted (test file line 144) |
| Headless integration smoke | `bash tools/run_headless.sh tools/controller_integration_smoke.py` | **SMOKE_RESULT: PASS** — exactly **69** `SMOKE: PASS` checks incl. stage 6b same-controller restart (`restart_returns_intro_preface node='intro.preface'`, `restart_finished_falsy finished=None`, `restart_guard_false guard=False`, `restart_stashes_cleared enzyme=None source=None`) and `exactly_one_YOU=True` |
| Hero highlight smoke | `bash tools/run_headless.sh tools/hero_highlight_smoke.py` | **PASSED** (raw exit=0) |
| Plugin zip | `dist/rpg-0.0.1-dev.zip` via python3.6 zipfile namelist | **EXISTS** — first entry `rpg/__init__.py` (Case-1 PLGN-02 layout), 49 entries, **0** c14 entries |
| Citation gate | `python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json` | **exit 1 — 63 [MISSING], 0 [UNAPPROVED]** — UNCHANGED expected pre-content red (placeholder claim_ids), NOT a regression; must go green by the Phase 10 pre-ship gate |

### ROADMAP Success Criteria — final score: 5/5 PASSED

| SC | Verdict | Evidence |
| --- | --- | --- |
| SC1 install/menu/window | **PASS** | Human PASS (round 1, real session). Post-rename menu re-check was queued, but the rename is machine-proven this session: zip first entry `rpg/__init__.py` + zero c14 entries + entry point `rpg/__init__.py __init_plugin__ → plugin_entry.init_plugin → addmenuitemqt('RPG: Tale of C', …)` + both headless smokes import rpg.* end-to-end on real Windows PyMOL; user data migrated to %APPDATA%\pymol\rpg-tale-of-c. Human accepted the closure. |
| SC2 hero highlight + scenes | **PASS** (mechanism; content queued) | Hero highlight human-PASSED after the first-operator fix (human: "SC2a pass"); `exactly_one_YOU=True` re-proven in this session's smoke; status-bar node+stage orientation shipped (3f483aa). Scene/representation CONTENT is placeholder-by-design: the start node bundles `_smoke.pdb`, and per-node content = Phase 7 filling the FROZEN 5.4 scene templates. |
| SC3 True+Bad endings + save/load | **PASS** | Human PASS (round 1: both endings reachable, save/load restores story position + RNG + camera). Colors/reps rebuild via on_enter replay (by design, documented — 06-03 view = CAMERA-only). Round-3 banner-reset fix machine-verified (smoke stage 6b) + human-confirmed ("ok the bad end banner gone"). |
| SC4 bulk-download | **PASS** (mechanism; real list queued) | Human PASS (round 1: glucose starts instantly on bundled assets). Mechanism headless-verified (runner/progress/cancel/retry/per-character lock in unit tests + smoke stages); the prompt correctly does NOT fire for the placeholder cast (PLACEHOLDER guard). Real large-PDB list = Phase 7. |
| SC5 achievements + help | **PASS** | Human PASS (round 1: unlocks + cross-session persistence + wiki links). ACH-02 persistence to user_data_path; fuller inline help deferred to Phase 11 per the human decision (visible placeholder pointer card shipped in help.json). |

### Three-round verification history (symptom → root cause → fix → human verdict)

| Round | Symptom | Root cause | Fix (commit) | Human verdict |
| --- | --- | --- | --- | --- |
| 1 | SC2a: BOTH carbons highlighted as "YOU" | Default sele `<obj> and elem C` matched ALL carbons on the 2-carbon `_smoke.pdb` | `389ee3e` — sele → `first (obj and elem C)`; empirically probed on real PyMOL (tools/probe_first_operator.py, 9/9); smoke strengthened to exactly-one-YOU | **"SC2a pass"** (confirmed in the round-2 session) |
| 1 | SC2f: clicking "Edit enzyme" crashed (`ValueError: too many values to unpack (expected 3)` at main_window.py:413) | `EditDialog.selected_edit()` returned the raw stored 4-tuple `(label, op, target, args)` instead of the documented 3-tuple | `c2d1008` — `selected_edit()` returns `self._selected[1:]` | Exercised by the human's subsequent playthroughs (edits opened + routed) |
| 1 | SC2b: orientation — "not sure which point it is" | Status bar showed only character + seed (no node/stage) | `3f483aa` — status bar shows `node=<id>  stage=<tag>  character=<c>  seed=<s>` | In use across rounds 2-3 |
| 2 | SC2f (round 2): edit affordance at the first enzyme (gly.pfk) → `RuntimeError: … 'edit.prompt' has no edit:enzyme:<id> tag and no pending enzyme_id stash` | edit:offer→request_edit routing existed ONLY in ChoicePanel._render_mixed; the 5.1 replan added edit:offer to 13 PURE-MC enzyme nodes which routed via generic choose(i), never setting the stash (debug session: .planning/debug/edit-prompt-empty-stash.md) | `68631dd` — _render_pure dual-predicate special-case → request_edit at the SOURCE node + graph-invariant test + 4 smoke checks at gly.pfk | Exercised end-to-end by the human's round-3 play; phase closure confirmed |
| 2 | Design: cycle-trap felt like it should HAPPEN (a RESULT), not be chosen; soul-jump should not be a decision | Open design decision from round 1 | `81b1a48` — controller auto-resolve at the _render choke point: trap AUTO-FIRES at visits>5, one-time aconitase edit offer on first entry, else AUTO-SPIN (engine RNG picks among weighted only; NO skeleton/weights change) | **Human decision "auto fire"** — implemented as decided |
| 2 | Latent seam: stale edit stash could survive; Cancel stranded the player at edit.prompt | Stash never cleared after apply; no return path from edit.prompt | `245f88f` — stashes cleared after successful apply; Cancel → "Return to the enzyme" (controller.return_to_edit_source, controller-side source stash; NO skeleton change) | Used in the human's round-3 play |
| 2 | Design: fuller inline help | User preference (round 1) vs docs-finalization scope | `f413dbb` — DEFERRED to Phase 11 per the human; visible placeholder pointer card added to help.json (zero code change) | **Human decision "defer to 11"** — closed |
| rename | c14 → rpg package rename (user-approved quick task) | PEP8 lowercase package name; code-only scope | `bacbb09` — 513 replacements / 71 files; gates updated; zip → dist/rpg-0.0.1-dev.zip; user data migrated to %APPDATA%\pymol\rpg-tale-of-c | Machine-proven (this session: zip first entry rpg/__init__.py, 0 c14 entries, all gates identical); menu re-check accepted by the human at closure |
| 3 | S1: bad ending persisted after New Game AND after window close/reopen | Controller/engine restart PROVEN CLEAN (42/42 probes); PRIMARY: StoryPanel.render_node never reset the "Ending reached" banner (only clear() hides it, never called); SECONDARY: plugin_entry re-shows the same hidden MainWindow singleton on reopen | `8c2d344` — render_node blanks+hides the banner first, render_ending reordered (render_node then set+show; identical final state) + `33ddbc1` — both edit stashes cleared on start_game/load (+2 tests) + `4277a4e` — smoke stage 6b same-controller restart (9 checks) | **"ok the bad end banner gone."** (debug session: .planning/debug/bad-end-restart-and-edit-pool.md) |
| 3 | S2: every edit attempt → bad ending ("shouldnt we be restoring mutant from our story?") | Phase-6-EXPECTED CONTENT GAP — rpg/data/edits.json has zero real-enzyme entries (fixture only); routing MECHANISM PROVEN (injected known gly.pfk entry → restoration branch, even with noised input); restoration branch nodes DO NOT EXIST in the frozen skeleton | No code fix — Phase 7 citation-gated content (edits.json entries + restoration branch nodes + 5.3 WT-aligned reveals); the dialog already prints the Phase-7 notice | Verdict accepted; Phase 7 queue |

### Design decisions applied (all human-made)

1. **Cycle-trap auto-fire + soul-jump auto-RNG** (`81b1a48`) — human verbatim "decision 1 auto fire. also the soul jump shouldnt be a decision too, its rng jump success or keep on loop or out as CO2." Implemented in the controller at the _render choke point; NO new RNG outcomes/weights; NO skeleton JSON change (55 nodes / 21 endings untouched).
2. **Fuller inline help DEFERRED to Phase 11** (`f413dbb`) — human decision 2026-08-30; placeholder pointer card shipped in help.json.
3. **Package rename c14 → rpg** (`bacbb09`) — user-approved; machine-proven; historical planning docs keep their c14 references by design.
4. **One-time edit offer on first shuffle entry** — part of the 81b1a48 auto-resolve design (visit_counts==1; survives save/load via GameState).
5. **Cancel returns to the source enzyme** (`245f88f`) — controller-side source stash; FROZEN skeleton untouched.

### Phase-7 / 11 / 12 queue (recorded at close-out; NOT Phase 6 gaps)

- **Phase 7 (citation-gated content):** the 5.1 restoration branch nodes + known-edit signatures (real-enzyme edits.json entries, keeping the shared-manifest invariant edits.json keys == cast ids == graph edit:enzyme:<id> values) + the 5.3 WT-aligned reveal; shuffle→CO2 outcome (needs an approved RNG weight); citrate-synthase dimer (biological assembly) loading (cast convention); per-node scene/representation content filling the FROZEN 5.4 templates; real bulk-download large-PDB list; approved TCA RNG weights (may add the shuffle→end.normal.co2 early-exit edge considered and rejected this round).
- **Phase 11:** fuller inline step-by-step help (placeholder pointer card shipped in its place).
- **Phase 12:** ending cutscene/CG rendering.

### Residual risks (accepted at close-out)

1. **plugin_entry refresh-on-show (P2) deferred** — close→reopen in the SAME PyMOL process re-shows the same hidden MainWindow singleton with the last render (no closeEvent, no re-render on show). Per the debugger's recommendation, revisit only if the human still finds close→reopen confusing after the banner fix (a full PyMOL restart cannot show an ending without playing).
2. **Qt behaviors are permanently human-only from WSL** (AGENTS.md) — dialog modality, prompt flow, link-opening, visual rendering can never be machine-verified in this environment; future GUI regressions will always need a human session.
3. **Citation gate is red until Phase 7 content lands** (63 MISSING placeholder claim_ids) — expected pre-content state by design (no-fabricated-science gate working as intended); must be green before any release (Phase 10 pre-ship gate).
4. **dist/rpg-0.0.1-dev.zip is a gitignored build artifact** — verified against the current tree this session (first entry rpg/__init__.py, zero c14 entries); rebuild before any reinstall after future edits.
5. **The OQ-6 hero prompt fires on every new game** (the hero object never exists at pre-pass time) — correct per the 5.4 override; noted as a Phase 7 polish candidate.
6. **Status-bar `stage=` is omitted for nodes without a `stage:<x>` tag** — per Fix-3 design; Phase 7 content adds the tags.

### Close-out justification

1. Every machine gate is green on the actual codebase in this session (324 unit tests, both AST gates, 20/20 reachability invariants, 69-check integration smoke incl. the round-3 restart stage, hero smoke, zip layout) — and the citation gate's exit-1 red is the EXPECTED pre-content placeholder state, unchanged and documented, not a regression.
2. The human — the only authority for the Qt layer per AGENTS.md — played the game end-to-end across three rounds, confirmed each headline fix verbatim ("SC2a pass", "ok the bad end banner gone"), resolved both open design decisions, accepted the Phase-7 content-gap verdict, and closed the phase.
3. All remaining work items are routed to Phase 7/11/12 queues with named owners and gating (citation approval), matching the ROADMAP's own scoping of those phases — there is no missing, stubbed, or unwired Phase 6 artifact.

---

## Round-1 verification report (kept intact for history)

## Goal Assessment

The goal is **substantively achieved**: every plan's artifacts exist, are substantive (no stubs), and are wired; the full machine-check battery passes on the actual codebase; and the human already exercised the game end-to-end in a real Windows PyMOL 2.5.0 session (SC1/SC3/SC4/SC5 PASS). The two SC2 bugs the human found are fixed in code (commits c2d1008, 389ee3e, 3f483aa) and machine-verified headlessly, but the GUI re-check of those fixes is pending — so the last inch of SC2 cannot be declared closed without a human. Status is therefore `human_needed`, not `gaps_found`: nothing is missing or broken; one short re-check remains.

Independent-verification note: this report is built from grep/read evidence and commands run in this session — NOT from SUMMARY claims. Where a claim could not be machine-checked (Qt runtime behavior), it is marked human-verifiable.

## Must-Haves Table (per plan)

Legend: ✓ = verified in code this session (file:line or command). All 33 plan artifacts + 27 key links verified; none missing, none stubbed, none orphaned.

| Plan | Must-have artifacts / key links | Status | Evidence |
| --- | --- | --- | --- |
| 06-01 | molops 4 dispatches (set_color/label/set/align) + load target-prefix fallback | ✓ | molops.py:160-196 (elif branches, `self._cmd.set_color/label/set/super/align/cealign` at 163/173/177/189/192/195; cealign reversal normalized at 195); load fallback pdb:/cid:/sid:/bare-filename at molops.py:219-235; tests/test_molops.py:413 test_set_color_dispatch; smoke ran SMOKE_RESULT: PASS |
| 06-02 | `user_data_path` resolver + tests | ✓ | paths.py:68-91 (APPDATA → %APPDATA%/pymol/c14-tale-of-c, else ~/.pymol/c14-tale-of-c; pure resolver, os.environ+expanduser, no getcwd); tests/test_paths.py:70-130 (platform + CWD-independence tests, suite green) |
| 06-03 | GameState `view` field + engine view_provider/view_applier | ✓ | state.py:71 (init), :98 (to_dict), :125 (from_dict .get default None); engine.py:97/103-104 (ctor), :255-257 (save captures via `_view_provider`), :279-281 (load applies view AFTER `_enter` replay); engine stdlib-only (AST gate clean) |
| 06-04 | AchievementBoard + catalog + persistence | ✓ | achievements.py:72 ACHIEVEMENT_CATALOG_V1, :87 TIER_ACHIEVEMENT_ID, :95 class, :111 default `user_data_path("achievements.json")`, :153 `_unlock`; board.on_turn called from controller.py:552; tests/test_achievements.py:59 TestAchievementBoard |
| 06-05 | pyr.branch cond fix + intro _smoke.pdb swap + 6-call hero sequence | ✓ | pyruvate_branch.json:12-13 (`not flags.get('host_o2_low')` / `flags.get('host_o2_low')` — dict-method form); intro.json:10-16 (load `_smoke.pdb` hero_atom + set_color hero_cyan + show_as sticks + color all-C + show spheres + set sphere_scale 0.3 + label YOU — the full sequence); intro.json:46-48 (intro.shell_glucose bundled glucose); test_glucose_reachability 19/19 OK |
| 06-06 | Controller + HeroResolver + engine.goto/choice_cond_met + request_edit seam + defensive dispatch | ✓ | controller.py:70 HeroResolver, :153 default sele `"first ({0} and elem C)"` (Fix 2), :204 Controller, :277 `molaction_sink=self._dispatch_molaction`, :291-310 `_dispatch_molaction` → `self._molops.apply(action)` in try/except (Blocker 1 fix c), :402 request_edit stashes `_pending_edit_enzyme_id` (:417), :427 build_edit_intent falls back to the stash (:438-440), :465 is_mixed_weighted_node, :483 _current_enzyme_id (`edit:enzyme:` tag); engine.py:179 goto, :195 choice_cond_met; tests/test_controller.py:88 TestController; tests/test_engine.py:433-455 test_goto_* |
| 06-07 | Plugin entry + __init_plugin__ + build_plugin_zip.sh | ✓ | c14/__init__.py:15 `__init_plugin__` → selfcheck (:27-28) → `from .ui import plugin_entry` (:32-33) — gate-clean; plugin_entry.py:13-16 `addmenuitemqt('RPG: Tale of C', _open_main_window)`; :20-27 lazy `from .main_window import MainWindow` + singleton; dist/c14-0.0.1-dev.zip EXISTS (gitignored) — inspected: first entry `c14/__init__.py` (Case-1), story_glucose bundled, help.json+cast.json present, ZERO forbidden entries (__pycache__/*.pyc/downloaded) |
| 06-08 | MainWindow + StartDialog + StoryPanel + ChoicePanel | ✓ | main_window.py:99 StartDialog, :177 MainWindow, :215 AchievementBoard(), :239 `Controller(`, :246 `_build_toolbar` (New/Save/Load/Achievements/Help :259-267), :288 render_turn, :226 prompt_fn QMessageBox.question wrapper (OQ-6 gate), :366/:376 save/load routing, :394 _open_edit_dialog → :431 `op, target, args = dlg.selected_edit()`; widgets.py:64 StoryPanel, :142 ChoicePanel, :182 new_game_requested signal, clicked.connect → choose(0) (:260/:306), request_edit (:276-278), take_choice (:282-284), choose(i) (:315-317) |
| 06-09 | EditDialog curated options + 3-tuple contract | ✓ | edit_dialog.py:80 class, :174 selected_edit, :193 `return self._selected[1:]` (Fix 1 — the documented (op, target, args) 3-tuple), :196 submit() → :236 `controller.build_edit_intent(op, target, args)`; reads edits.json (docstring :43) |
| 06-10 | Bulk-download runner + dialog + cast.json schema | ✓ | bulk_download.py:120 missing_large_pdbs (PLACEHOLDER guard), :181 run_bulk_download, :229 delegates to `assets.fetch_pdb` (never cmd.fetch); bulk_download_dialog.py:45 QProgressDialog + processEvents BETWEEN fetches (:50-51) + on_cancel_check (:85); cast.json has `source`/`pdb_id`/`character` fields; tests/test_bulk_download.py TestBulkDownloadRunner (suite green) |
| 06-11 | Save/Load dialogs → user_data_path('saves') → controller.save/load | ✓ | save_load_dialogs.py:56 import, :59 _saves_dir, :77 ask_save_path (default `user_data_path("saves")/save.json`), :96 ask_load_path; wired at main_window.py:366 (`controller.save(path)`) + :376 (`controller.load(path)`) |
| 06-12 | AchievementsDialog reads board.data | ✓ | achievements_dialog.py:59 class, :86-90 reads `board.data` (characters_tried/endings_found/branches_discovered/achievements_unlocked), :46 imports ACHIEVEMENT_CATALOG_V1 for cross-reference; no file I/O of its own |
| 06-13 | help.json + HelpDialog + QDesktopServices | ✓ | help.json: 4 editing_pointers + 3 wiki_links (Alter/H_Add/Fetch, live-verified notes); help_dialog.py:56 `data_path("data","help.json")`, :87 `QtGui.QDesktopServices.openUrl(QtCore.QUrl(u))` |
| 06-14 | Headless integration smoke | ✓ | tools/controller_integration_smoke.py (786 lines) ran in THIS session: `SMOKE_RESULT: PASS`, raw line 11: `hero_you_label_dispatched exactly_one_YOU=True labels=['YOU', '', '']` |

**Score:** 60/60 machine-verifiable must-haves verified (33 artifacts at exists+substantive+wired, 27 key links wired). Human-only items: the 3 SC2 fix re-checks + the already-passed SC1/SC3/SC4/SC5 GUI verdicts.

## Machine Check Results (run in THIS session)

| Check | Command | Result |
| --- | --- | --- |
| Unit tests | `python3.6 -m unittest discover -s tests` | **Ran 309 tests … OK** (10.6s) |
| Import gate | `python3.6 tools/check_imports.py` | **clean (no pymol/PyQt5 imports in c14/ domain tier)**, exit 0 |
| Headless integration smoke | `bash tools/run_headless.sh tools/controller_integration_smoke.py` | **SMOKE_RESULT: PASS** (raw output line 66; line 11: `hero_you_label_dispatched exactly_one_YOU=True labels=['YOU', '', '']`) |
| py_compile (all Phase 6 sources) | `python3.6 -m py_compile` over 18 files (c14/ui/*.py, c14/__init__.py, paths/achievements/state/engine, molops, both smoke/probe tools) | **ALL EXIT 0** |
| Plugin zip | dist/ inspected (already built; dist/ is gitignored) | **dist/c14-0.0.1-dev.zip exists**: first entry `c14/__init__.py` (Case-1 PLGN-02 layout), story_glucose bundled into `c14/data/story_glucose/`, help.json + cast.json included, zero `__pycache__`/`.pyc`/`downloaded` entries |
| Frozen skeleton invariants | `python3.6 -m unittest tests.test_glucose_reachability` | **Ran 19 tests … OK** — includes the 55-node assertion (test file:113-114 `assertEqual(len(nodes), 55)`) and the 21-ending count (test file:144 "exactly 21 ending nodes, 1T+3G+2N+15B"); pyr.branch aerobic/anaerobic eligibility + start-node no-TBD-fetch tests all ok |

## Human-Verify Verdict Summary (recorded 2026-08-30, real Windows PyMOL 2.5.0 session)

| SC | Verdict | Notes |
| --- | --- | --- |
| SC1 install/menu/window | **PASS** (human) | Plugin Manager install + "RPG: Tale of C" menu + main window (toolbar/story/choices/status bar) all work |
| SC2 hero highlight + scenes | **Findings → FIXED in code; GUI re-check pending** | (a) BOTH carbons labeled YOU → default sele now `first (obj and elem C)` (controller.py:153; empirically probed 9/9 on real PyMOL via tools/probe_first_operator.py; smoke asserts exactly one YOU). (b) orientation ("not sure which point") → status bar shows node+stage (main_window.py:333-335). (f) EditDialog crash `ValueError: too many values to unpack` → `selected_edit()` returns the documented 3-tuple (edit_dialog.py:193). Fix commits: 389ee3e, 3f483aa, c2d1008 (+ docs f1c4ac5) — all present in git log |
| SC3 True+Bad endings + save/load | **PASS** (human) | Both endings reachable; save/load restores the session; camera restores. Manual color/rep tweaks before a save intentionally do NOT restore — BY DESIGN: the 06-03 `view` field is CAMERA-only (18 floats); the scene rebuilds from the node's on_enter replay. Not a bug |
| SC4 bulk-download | **PASS** (human; placeholders expected) | Glucose starts instantly on bundled assets; the prompt does not fire for the placeholder cast (`missing_large_pdbs` returns [] — PLACEHOLDER guard, verified headlessly Stage 9). Mechanism (progress/cancel/retry/per-character lock) is headless-verified in unit tests; real large-PDB list = Phase 7 |
| SC5 achievements + help | **PASS** (human) | Unlocks + cross-session persistence work; 4 editing pointers + 3 clickable wiki links. User prefers FULLER INLINE help — OPEN decision (help.json untouched) |

Also verified-correct in session (not bugs): the `molops.apply failed … pdb:TBD_ACONITASE` console lines are the 06-06 Blocker-1-fix-c defensive swallow — correct until Phase 7 fills real structures; PyMOL's own `Error-fetch` print is deliberately not silenced.

## Findings Classification

### (a) FIXED this pass — needs ONE quick human GUI re-check
1. **SC2a double "YOU"** — fixed via `first (obj and elem C)`; headless probe 9/9 + smoke `exactly_one_YOU=True`. Re-check: exactly one cyan sphere+YOU after the OQ-6 prompt.
2. **SC2f EditDialog crash** — fixed via 3-tuple return (code-verified); re-check: open → pick → OK → story routes, no crash.
3. **SC2b orientation** — fixed via node+stage status bar (code-verified); re-check: status bar shows the node id.

### (b) EXPECTED / later-phase (not Phase 6 gaps)
- **tbd_aconitase + other pdb:TBD_*/pdb:XXX load errors** — placeholder targets; real structures are filled in **Phase 7** (content). The defensive swallow is correct behavior.
- **Placeholder story text / not-story-like glucose content** — **Phase 7** (real glucose + two-layer text).
- **Citrate synthase dimer (biological assembly) loading** — **Phase 7** cast convention (placeholder cast is by design; no fabricated PDB IDs allowed).
- **Per-node default color/focus (5.4 scene templates not visibly differentiated)** — templates are FROZEN design; **Phase 7** fills them per node.
- **Manual color/rep tweaks not restored on load** — by design (06-03 view = camera-only; scene = on_enter replay). If the user wants more, that is a new requirement, not a defect.
- **Ending cutscene/CG** — **Phase 12** (per ROADMAP).

### (c) OPEN design decisions for the USER (do not resolve unilaterally)
1. **Cycle-trap: OPTION vs RESULT.** The trap at tca.shuffle is currently presented as a choice button (greyed until visits > 5), but the user expected it to happen as a RESULT (the cycle simply keeps turning). Question: keep it as an option (current FROZEN topology, 55 nodes / 21 endings unchanged) or re-frame as a forced result? Options: (i) keep as-is, (ii) re-frame presentation (text/UI) without topology change, (iii) re-open the frozen skeleton (costly — reachability invariants re-validated).
2. **Help: fuller inline guidance vs links-only.** User prefers fuller inline help inside the GUI. Question: expand help.json + dialogs now, or defer to Phase 11 (docs finalization)? Options: (i) expand now (small Phase 6.1-style insert), (ii) defer to Phase 11 where help must match shipped content anyway.

## Remaining Risks

1. **The 3 SC2 fixes are machine-verified but not yet re-confirmed in a live GUI session.** The `first` operator was probed on real headless PyMOL 2.5.0 (same runtime the GUI uses), and the smoke asserts exactly one YOU — risk is low, but the phase's own contract (human-verify milestone) is only satisfied once re-checked.
2. **Qt dialog behaviors are inherently human-only** from this WSL environment (AGENTS.md): prompt flow, dialog modality, link-opening — all relied on the human session + code reading.
3. **The OQ-6 prompt now fires on every new game** (by design): the HeroResolver pre-pass count runs BEFORE the on_enter load, the hero object never exists yet, the count fails → treated as ambiguous → warn+confirm. The human confirmed the prompt fires; this is correct per the 5.4 OQ-6 override but means the "skip prompt on single-C" optimization effectively never triggers at game start. Acceptable; noted for Phase 7 polish.
4. **Status-bar `stage=` only shows when a node carries a `stage:<x>` tag** — omitted silently otherwise (per Fix 3 design). Some nodes may lack the tag until Phase 7 content.
5. **dist/ zip is a build artifact (gitignored)** — the verified zip matches the current tree, but a stale zip could diverge after future edits; rebuild before any reinstall.

## Re-Verify Checklist for the Human (short — only the fixed GUI items + 2 decisions)

1. Reinstall/reload the plugin (or dev-install) with the current tree, start PyMOL.
2. **SC2a:** New Game (glucose) → after the OQ-6 warn+confirm prompt, verify **exactly ONE** carbon has the sphere + "YOU" (the other carbon is cyan sticks, unlabeled).
3. **SC2f:** reach an edit-allowed node → click "Edit enzyme" → pick an option → OK → confirm NO crash and the story routes to a branch/bad ending.
4. **SC2b:** confirm the status bar shows `node=<id>` (+ `stage=<tag>` where present).
5. **Decision 1 (cycle-trap):** Should the cycle-trap stay a selectable OPTION at tca.shuffle, be re-presented as a forced RESULT (presentation-only), or re-open the frozen skeleton?
6. **Decision 2 (help):** Expand the inline help now (Phase 6 addendum) or defer to Phase 11 docs finalization?

If 2-4 pass, Phase 6 is fully closed; proceed to the user decisions + Phase 7 planning.

---

_Verified: 2026-08-30_
_Verifier: OpenCode (gsd-verifier) — independent; no code modified; nothing committed_
