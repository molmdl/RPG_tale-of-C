---
phase: 06-qt-ui-minimal-playable-mvp
verified: 2026-08-30T00:00:00Z
status: human_needed
score: 60/60 machine-verifiable must-haves (33 artifacts + 27 key links) verified; 4/5 ROADMAP SCs human-PASSED; SC2 fixes machine-verified, GUI re-check pending
date: 2026-08-30
re_verification: null
human_verification:
  - test: "Start a new glucose game in a real Windows PyMOL session (after the OQ-6 warn+confirm prompt)."
    expected: "EXACTLY ONE carbon on hero_atom has the sphere + 'YOU' label (cyan); the other carbon(s) are cyan sticks only — NOT two 'YOU' spheres."
    why_human: "Qt/GUI rendering cannot be exercised from WSL (AGENTS.md); the fix is headless-proven (probe 9/9 + smoke exactly_one_YOU=True) but not yet re-confirmed in a live session."
  - test: "At an edit-allowed node, click 'Edit enzyme' → pick an option → OK."
    expected: "The EditDialog opens, OK does NOT crash (no ValueError), and the story routes to a branch or bad ending."
    why_human: "Qt dialog interaction; the selected_edit 3-tuple fix is code-verified (edit_dialog.py:193 returns self._selected[1:]) but the click-through is GUI-only."
  - test: "Advance a node or two and glance at the status bar."
    expected: "It shows node=<id> (and stage=<tag> where the node carries one), e.g. 'node=gly.start  stage=glycolysis  character=glucose  seed=42'."
    why_human: "Qt status-bar display; wiring is code-verified (main_window.py:333-335) but the on-screen result is GUI-only."
---

# Phase 6: Qt UI + Minimal Playable MVP — Verification Report

**Phase Goal:** The game is playable end-to-end for the first time in a real Windows PyMOL session — install the plugin, start a glucose game, see the C14 hero highlighted (5.4 convention), make choices (5.1 choice-point contract), edit molecules (5.1 edit-node contract), save/load, reach a True or Bad ending — with the UI as a thin adapter over the proven engine + molecular layer. FIRST human-verify milestone.
**Verified:** 2026-08-30
**Status:** human_needed (all machine checks green; 4/5 SCs already human-PASSED in the real session; the 3 SC2 fixes are machine-verified headlessly and need ONE quick GUI re-check to close)
**Re-verification:** No — initial verification (no previous VERIFICATION.md existed)

---

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
