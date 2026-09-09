# Codebase Concerns

**Analysis Date:** 2026-09-10

> **Context correction:** AGENTS.md describes this repo as "early stage: no plugin code yet." That is **stale**. The actual state (verified 2026-09-10): Phases 1–6 COMPLETE, Phase 7 execution complete pending a human checkpoint, Phase 7.1 at 17/19 plans, **599 unit tests passing** (`python3.6 -m unittest discover -s tests`, 18.4s), ~16.7k lines in `rpg/` + `tools/` plus ~15.7k lines of tests. Concerns below reflect the real codebase, not the greenfield posture in AGENTS.md.

## Tech Debt

**Stale authoritative docs (AGENTS.md, README.md, spec.md, PITFALLS.md):**
- Issue: Three agent-facing docs describe a project that no longer exists.
  - `AGENTS.md` line 3: "no plugin code yet, only spec + reference material" — false (599 tests, 13 rpg modules, Qt UI shipped).
  - `AGENTS.md` line 5 + `.planning/research/PITFALLS.md` lines 102/435: "Pitfall 9 (C14 decay) remains Pending" — stale; **resolved via DROP on 2026-08-15** per `spec.md` line 20 note and `.planning/PROJECT.md` line 115. The two doc sets actively contradict each other.
  - `README.md` lines 7–9/29–30: "early planning stage. No runnable plugin code exists yet… Phase 1 is next… 13-phase roadmap" — actual state is a 17-phase roadmap at Phase 7.1 with a playable MVP.
- Files: `AGENTS.md`, `README.md`, `spec.md`, `.planning/research/PITFALLS.md`
- Impact: Any agent or human onboarding from these docs will (a) misjudge project scope, (b) risk **reintroducing the radioactive-decay bad ending** (the exact anti-confusion failure AGENTS.md was written to prevent), (c) plan against the wrong phase.
- Fix approach: One doc-sync pass — update AGENTS.md repo-status paragraph and Pitfall 9 status, PITFALLS.md Pitfall 9 header, README Status section. Keep the hero-identity anti-confusion note (still correct and load-bearing).

**Stale environment references inside `spec.md` (borrowed from a sibling project):**
- Issue: `spec.md` line 46 instructs "use setenv.bat"; lines 73–133 (the verbatim-borrowed section) reference `setenv.bat`, `wsl2win_cp.sh`, `RPG_tale-of-C/setup_state.py`, and the nested `tmp/RPG_tale-of-C/` staging layout — **none of which exist in this repo**. `spec.md` line 17's Pitfall-4 note ("Pitfall 9 remains separate/pending") also predates the 08-15 DROP resolution.
- Files: `spec.md` (lines 46, 73–133, 17)
- Impact: An agent following spec.md's WORKING ENV verbatim will hunt for scripts that do not exist. The real entry point is `C:\src\run-conda-pymol.bat` (outside the repo, verified working 2026-09-10).
- Fix approach: Annotate the borrowed section in-place (as was already done in `AGENTS.md` line 21 and `.planning/PROJECT.md` line 85), or replace the WORKING ENV block with the verified headless-run recipe.

**Known smoke drift — 3 pre-existing FAILs in `controller_integration_smoke.py` (CONFIRMED still failing 2026-09-10):**
- Issue: Stage-9 expectations no longer match the real story cast. Reproduced today via `run-conda-pymol.bat -cq tools\controller_integration_smoke.py` → `SMOKE_FAILED_STAGES: pyr_branch_anaerobic_cond_not_met, bulk_download_missing_empty_placeholder, bulk_download_expected_chars_empty`. Cause is data drift: real PDB IDs (6WCV/5UPP/5LDW) landed in the cast and cond data changed (07-06 DC-B removed the branch conds).
- Files: `tools/controller_integration_smoke.py` (lines ~390–415, ~950–972); documented open item in `.planning/STATE.md` (Pending Todos, found 2026-09-04 during the CodeQL alert fix)
- Impact: The smoke is red on every run; a *new* regression in those stages would hide inside the known-failure noise. Note the unit suite (599 tests) is green — the smoke is the only surface catching this class.
- Fix approach: Dedicated session to re-align the 3 stage-9 checks with the current 57-node/cast-12 data, per the STATE.md note ("needs its own session").

**Test-count drift in `.planning/STATE.md`:**
- Issue: STATE.md progress line says "suite 577 OK"; the actual suite is **599 tests** (ran 2026-09-10).
- Files: `.planning/STATE.md` line 17
- Impact: Minor; future plans that pin "suite N OK" baselines will anchor to a stale number.
- Fix approach: Update the progress line at the next STATE.md touch (no dedicated effort needed).

**Dual story directories (`data/story/` vs `data/story_glucose/`):**
- Issue: `data/story/` is the Phase-1/2 toy skeleton (1 file, `intro.start`) still referenced by `tests/test_engine.py`, `tests/test_integration.py`, `tests/test_interpreter.py`, `tools/render_story_graph.py` docs, and `rpg/story/graph.py` docstrings. The real game data lives in `data/story_glucose/`.
- Files: `data/story/`, `rpg/story/graph.py:8-9`, `tests/test_engine.py:26`
- Impact: Intentional (hermetic small-fixture tests) but confusing to newcomers; `tools/render_story_graph.py --story-dir data/story/` renders a 1-node graph that looks broken.
- Fix approach: Leave as-is; add one sentence to the eventual README/CONTRIBUTING explaining the fixture role (Phase 11 docs pass).

**Committed generated artifact `story_editor.html` (718 KB at repo root):**
- Issue: A generated file (built by `tools/story_editor.py` from `tools/story_editor_assets/*.js`, currently 14 inlined assets, generated-at 2026-09-05T20:06:28) is committed at repo root and must be regenerated + re-committed after every asset change. STATE.md records a recurring deferral dance where parallel waves left the committed HTML temporarily stale (07.1-09/12/13 deferrals, healed by later regen chores).
- Files: `story_editor.html`, `tools/story_editor.py`, `tools/story_editor_assets/`
- Impact: Drift risk — editing an asset without regenerating (or committing a regen that bakes a sibling's untracked asset) produces an editor page that diverges from the source assets. Mitigations already exist: FNV-1a fingerprint table in the Diagnostics tab, byte-identity tests, the post-save gate list.
- Fix approach: Keep the existing convention (regen chore committed in the same or immediately-following plan; generator battery already pins asset order and token hygiene). A build-check test that regenerates and diffs against the committed file would close the gap mechanically.

**Gitignored reference material is not self-contained (portability):**
- Issue: `.gitignore` excludes `Pymol-script-repo` (a **symlink** to `../bioCHEMeleon/Pymol-script-repo` — a sibling repo *outside* this one), `tmp/` (where `tmp/pymol-src/` holds the PyMOL 2.5.0 source — a **real directory**, not a symlink as `AGENTS.md` line 25 claims), and `3rd_party_lib/`. A fresh clone or a parallel worktree has neither; `spec.md` line 93 already documents "NOT present in parallel-execution worktrees."
- Files: `.gitignore`, `Pymol-script-repo` (symlink), `tmp/pymol-src/` (directory), `AGENTS.md` lines 23–27
- Impact: Repo is not portable/self-contained: API-verification material (`tmp/pymol-src/modules/pymol/`) and idiomatic plugin references vanish on clone/worktree; the relative symlink breaks if the sibling `bioCHEMeleon` repo moves or is renamed. Also `AGENTS.md`'s "symlink" description of `tmp/pymol-src/` is inaccurate (harmless, but part of the stale-docs cluster).
- Fix approach: Document the expected sibling layout in AGENTS.md (one line), or swap `tmp/pymol-src/` to a symlink like `Pymol-script-repo` for symmetry. Do NOT commit the material (license + size constraints in `LICENSE_pymol-open-source` / spec.md).

**Parallel-execution shared-index commit races:**
- Issue: When ≥2 GSD plans run in parallel, executors share a git index; concurrent `git add`/`commit` sweep in each other's staged files. Happened in Phase 4 Wave 1 (~3 Rule-3 collision fixes) and forced the regeneration-deferral dance throughout Phase 7.1 waves.
- Files: `spec.md` lines 105–133 (worktree protocol), `.planning/quick/001-*` (rationale)
- Impact: Chore overhead per wave; mis-attributed commits; deferred regenerations that must be healed later.
- Fix approach: The worktree-per-parallel-plan protocol is already documented and correct — the debt is that it is *documented in `spec.md`'s borrowed section* and easily missed. It is enforced by orchestrator discipline only; consider copying the protocol into `.planning/PROJECT.md` so it survives any future spec.md cleanup.

## Known Bugs

**Story-editor direct-load checkpoint verdict REJECTED — fix landed, one-step Firefox re-verification pending:**
- Symptoms: The 07.1-11 human checkpoint rejected the editor ("not working, even upload not working at all") in Firefox.
- Files: `tools/story_editor_assets/10_load.js` (fix f8990bb), `tests/test_story_editor_load.py` (re-pin 8b6424b)
- Trigger: D1 — boot probe used `fetch()`, which cannot read `file://` URLs in Firefox (CVE-2019-11730/MFSA 2019-21); replaced with XHR. D2 — `onFolderPicked` cleared `input.value` while holding the live `FileList`, silently no-op'ing the upload; files now snapshotted before clear.
- Workaround: None needed post-fix; the pending action is human verification only — open `story_editor.html` in Firefox and confirm the 57-node graph renders with zero clicks (recorded as gate-re-opened in `.planning/STATE.md` 07.1-11 update).

**Documented cosmetic wording drift in the editor (no behavioral dependency):**
- Symptoms: `90_boot.js` Help tab still says "the folder pick is the normal path"; 30/50/70 status strings still say "(silent probe or folder pick)" — both superseded by the direct-XHR-first default from the 07.1-11 fix.
- Files: `tools/story_editor_assets/90_boot.js`, `30_graph.js`, `50_editscast.js`, `70_claims.js`
- Trigger: Sibling wording drift documented (not fixed) in the 07.1-11 fix-forward.
- Workaround: Grep-verified zero behavioral dependency; fix opportunistically at the next editor asset touch + regeneration.

**Phase-6 deferred defect — plugin close→reopen does not re-render:**
- Symptoms: `plugin_entry` re-shows the same hidden MainWindow singleton on close→reopen with no re-render.
- Files: `rpg/ui/plugin_entry.py` (fix deferred per `.planning/debug/bad-end-restart-and-edit-pool.md`, P2)
- Trigger: Close the plugin window, reopen from the PyMOL menu.
- Workaround: Full PyMOL restart, or the ending banner self-clears on next render (8c2d344). Explicitly DEFERRED — "do NOT schedule" unless the user reports the confusion again.

**JS-side float token loss in the editor (Rule-4 flag, recorded not fixed):**
- Symptoms: `data/story_glucose/intro.json` hero rgb `[0.0, 0.75, 0.75]` re-serializes as `[0, 0.75, 0.75]` when saved through the editor (JS `JSON.parse` has no parse_float hook; the 05_json RawFloat limitation applies to a *writable* file, contradicting its "writable targets are float-free" note).
- Files: `tools/story_editor_assets/05_json.js`, `tools/story_editor_assets/10_load.js` (fix belongs to the load layer), `data/story_glucose/intro.json`
- Trigger: Open editor → save `intro.json` → git diff shows one noisy line. Same numeric value; LOW impact.
- Workaround: Accept the one-line diff or hand-restore the token. A lossless float-token parse is a recorded cross-asset architectural change owed to the human (STATE.md 07.1-13, Pending Todos).

## Security Considerations

**`eval()` on story condition expressions:**
- Risk: `rpg/story/interpreter.py:124` evaluates `cond` strings from story JSON via `eval` with `{"__builtins__": {}}` and a namespace of `flags`/`char`/`counters`/`visits`. Python eval sandboxes are not security boundaries — a hostile author can escape via attribute-walking (`().__class__` chains).
- Files: `rpg/story/interpreter.py:101-135`
- Current mitigation: Documented trust model in-source ("story content is TRUSTED — bundled JSON authored by the team, not user input"); content is gated by the citation gate (`tools/check_citations.py`), the lint (`tools/story_editor_lint.py`, `cond_attribute_form` rule), and the test batteries. Failure mode is fail-safe: any exception → choice silently disabled (`False`).
- Recommendations: Keep the trust boundary documented. If story files ever become user-editable/downloadable content, replace `eval` with a restricted expression AST walker (the `cond_attribute_form` lint rule already constrains the shape to `flags.get(...)`/`visits.get(..., n)` dict-method form, so a small whitelist AST evaluator is feasible). Not urgent for v1.

**Resolved CodeQL alerts — keep the pattern:**
- Risk: Two past alerts (insecure temp files #8/#9; a tag-filter issue) were fixed in commit `b280c39` and `.planning/debug/resolved/codeql-insecure-temp-files.md`, `.planning/debug/resolved/codeql-bad-tag-filter.md`.
- Files: `tools/` (temp-file creation sites fixed)
- Current mitigation: Fixes landed + differential-run proof the smoke FAILs were pre-existing.
- Recommendations: Re-run CodeQL after Phase 8/9 tool additions.

**Story editor browser surface (local file:// tool):**
- Risk: The editor reads arbitrary picked files via XHR/FileReader and renders content as HTML (`innerHTML` rebuilds).
- Files: `tools/story_editor_assets/10_load.js` (path guards: `..` substring, drive-letter regex, leading `/`; `.git` filtered from reads), `70_claims.js` (`safeHttpUrl` http(s)-only — no `javascript:` hrefs; `target=_blank rel=noopener`)
- Current mitigation: Fixed 5-path expected list; no server, no network, no filesystem writes (FSA API banned and grep-guarded by `test_no_fsa_api`); duplicate-key structural guard on registries.
- Recommendations: None beyond keeping the existing guards pinned by the batteries.

**Python 3.6 runtime is EOL:**
- Risk: The enforced dev/test interpreter (`python3.6`, 3.6.9) and the PyMOL 2.5.0 bundled Python are EOL (3.6 EOL 2021-12). No security patches; constrains library choices to stdlib.
- Files: environment constraint (AGENTS.md, `spec.md` lines 38–50); enforced by tests via the no-f-string pin on `tools/story_editor.py` and stdlib-only imports (`tools/check_imports.py`)
- Current mitigation: Domain layer is pure stdlib (`json`, `os`, `random`, `re`, `ast`); no third-party deps beyond what PyMOL ships (PyQt5 via `pymol.Qt`, numpy per spec).
- Recommendations: Accept for v1 (PyMOL 2.5 pins the interpreter); re-evaluate if PyMOL upgrades to a newer bundled Python.

## Performance Bottlenecks

**None observed in the domain/runtime layers.**
- The pure-Python suite runs 599 tests in 18.4s on python3.6; the engine/interpreter operate on a 57-node graph (trivial); `rpg/story/validate.py` BFS is O(nodes+edges).
- The heavy paths are PyMOL-side (`cmd.fetch`/`align`/`super` on real PDBs) and are inherently bound by PyMOL/network, already mitigated by: bundled fixtures for instant start (`rpg/data/assets/bundled/`), the one-time bulk-download prompt (`rpg/ui/bulk_download.py`, `bulk_download_dialog.py`) for large structures, and a gitignored download cache (`rpg/data/assets/downloaded/`).
- Improvement path: none needed now. If playtesting (Phase 10) shows slow scene rebuilds, the per-node `on_enter` replay (scene = pure function of state, `rpg/story/interpreter.py:75-99`) is the place to cache.

## Fragile Areas

**The pinned-count invariant cluster (57 nodes / 21 endings / 15 edit-allowed / 13 edit buckets / 12 cast ids):**
- Files: `tests/test_glucose_reachability.py`, `tests/test_glucose_content.py`, `tests/test_manifest_loads_all_57_nodes` (naming), `tools/story_graph_viewer.py:96-105` (EXPECTED_* constants), `tools/story_editor_lint.py` (count_shift notice), `tools/check_edit_coverage.py`
- Why fragile: Every Phase 8/9 content addition (new nodes, endings, edit buckets, cast entries) trips these pins by design; the count-shift acknowledgment flow (editor `applyWithAck` modal + same-plan test updates) is mandatory per change.
- Safe modification: Always update the pinned tests + viewer constants + lint notices **in the same plan** as the data change (the 07-13 D5 14→15 promotion is the canonical precedent). Never hand-edit counts in one place only.
- Test coverage: Excellent — this is the most-tested area of the repo (the fragility is intentional tripwire behavior, not a gap).

**The eval-cond contract between data and interpreter:**
- Files: `rpg/story/interpreter.py:101-135`, `data/story_glucose/*.json` (`cond` fields), `tools/story_editor_lint.py` (`cond_attribute_form`), `tools/story_editor_assets/20_validate.js:159` (client-side mirror)
- Why fragile: A cond written in the wrong form (attribute access instead of dict-method) silently hides its choice at runtime (fail-safe `False`) — the Phase-6 SC#3 bug class. Three layers (lint, editor JS, tests) guard it, but a new cond author must know the convention.
- Safe modification: Author conds only as `flags.get('x')` / `visits.get('id', 0)` / `char == 'glucose'`; run `tools/story_editor_lint.py` after any data change.
- Test coverage: Good (`tests/test_interpreter.py`, content tests); the runtime-silently-hidden failure mode is covered by the lint, not by unit tests — that is the residual gap.

**Frozen vocabulary boundaries (`molops.py` dispatch + `edits.json` signatures):**
- Files: `rpg/pymol_layer/molops.py:140-291` (FROZEN op set), `rpg/data/edits.json` (13 buckets, canonical lowercase signatures), `rpg/edit_router.py:122-149` (route semantics), `rpg/story/model.py:112-126` (EditIntent.signature)
- Why fragile: `tools/scene_capture.py` and the editor's `OP_VOCAB` must stay in lockstep with the dispatcher; a new op added on one side silently breaks capture/editor parity unless all four surfaces update.
- Safe modification: Treat `molops.py` as frozen through Phase 7 (per the 07-19 constraint); when it thaws (Phase 10+), update `scene_capture.py`, the editor `OP_VOCAB`, and the smoke in the same plan.
- Test coverage: Good (dispatch unit tests + headless smokes), though see the smoke-drift bug above — the integration smoke is currently red and must be trusted only for non-stage-9 stages.

**Case-sensitive PyMOL selection semantics:**
- Files: `rpg/data/edits.json` (sele strings, e.g. `resi 85 and chain A`), `rpg/pymol_layer/edit_ops.py`
- Why fragile: Empirically pinned in 07-12: PyMOL matching is case-sensitive — `'resi 85 and chain a'` resolves to NOTHING while `EditIntent.signature()` lowercases both sides, so a round-tripping signature can produce a no-op edit on the wrong case.
- Safe modification: Always author sele strings with uppercase chain IDs matching the PDB; never "normalize" case in `edit_ops.py`.
- Test coverage: The 07-12 empirical probe + restored-node headless replay cover the shipped seles; new Phase 8/9 seles need the same probe-before-authoring discipline.

## Scaling Limits

**Per-claim human approval throughput is the project's binding constraint:**
- Current capacity: 77 claims / 81 sources approved through Phase 7 in ~4 approval batches (~07-02/03/04/05, each a dedicated checkpoint session).
- Limit: `.planning/research/PITFALLS.md` (Pitfall 7) estimated full-content approval at ~6–8h human time under the adopted HYBRID scheme; Phases 8–9 (FA + alcohol characters, anaerobic path, ~20+ cast) are explicitly "dominated by per-claim approval throughput" (`ROADMAP.md` line 5).
- Scaling path: The HYBRID taxonomy (source-batch approval + per-claim review only for high-stakes: RNG weights, protonation defaults, carbon fate, contested) + `review_tier: routine` fast-track flags is the mechanism; keep batches per pathway segment rather than per claim. **Currently BLOCKING: 07-18 Task 2 human batch content review gates Phase 7 close.**

**Bulk PDB download at first play:**
- Current capacity: 5 of 12 cast PDBs require fetch on fresh installs (5GRE, 6WCV, 5UPP, 4WLU, 5LDW, 1ZOY, 1BGY per 07-15); 5 are dev-cached.
- Limit: Phase 9's ~20+ cast will grow the first-run download; PDB fetch failures degrade gracefully (defensive swallow, `rpg/ui/controller.py:41-44`) but leave placeholder scenes.
- Scaling path: The bulk-download prompt + gitignored cache (`rpg/data/assets/downloaded/`) is designed for this; re-verify prompt UX at Phase 9 scale.

## Dependencies at Risk

**External, out-of-repo runtime entry point:**
- Package: `C:\src\run-conda-pymol.bat` (Windows conda env `chemtools-win10`)
- Risk: The verified headless verification path lives **outside the repo** on the user's machine; not versioned, not reproducible from a clone.
- Impact: All headless PyMOL verification (smokes, probes, stage replays) depends on it.
- Migration plan: None needed for this single-machine project; document its role (done in AGENTS.md) and do not reference the phantom `setenv.bat`/`wsl2win_cp.sh` alternatives.

**PyMOL 2.5.0 + PyQt5 via `pymol.Qt` (pinned, correct choice):**
- Risk: Version-pinned by the installed anaconda PyMOL; the modern Qt interface is a spec constraint. `cmd.create` NO-OP surprise (Phase 5 05-06 spike) shows API citations can diverge from behavior — mitigated by `tmp/pymol-src/` verification (itself gitignored, see portability above).
- Impact: Low; constrained environment is stable.
- Migration plan: None for v1.

**Sibling symlink `Pymol-script-repo` → `../bioCHEMeleon/Pymol-script-repo`:**
- Risk: Relative symlink into a sibling repo — breaks on sibling move/rename/reclone.
- Impact: Loss of idiomatic reference material only (nothing runtime depends on it).
- Migration plan: Re-create the symlink, or vendor needed excerpts with license attribution (`LICENSE_pymol-open-source`).

## Missing Critical Features

*(Planned work per `.planning/ROADMAP.md` Phases 8–12 — listed because they are intentional gaps that tests/data currently pin as "known-empty," not defects.)*

**Fatty-acid + alcohol characters are stubs:**
- Problem: `data/story_glucose/intro.json` `fa.stub`/`alc.stub` nodes carry `PLACEHOLDER_PHASE8` claim_ids; the citation gate's sanctioned residual (verified 2026-09-10: exit 1, exactly "2 missing + 0 unapproved") is pinned to them.
- Blocks: v1 success measure "all 4 endings reachable for all 3 characters" (Phase 8).

**Zero known-wrong edit entries (M5):**
- Problem: `rpg/data/edits.json` has 13 enzyme buckets but zero known-wrong (`edit:known*`) routing entries — every player edit currently falls to the global bad-ending pool. M5 zero-count is pinned live by tests and the editor's Known-Wrong panel (07-01 decision #4: NO known-wrong entries in Phase 7).
- Blocks: The "wrong edit → bad-ending pool" spec element has only the fallback path, not the curated per-enzyme wrong-answer branches (Phase 8/9 content).

**Known gaps deferred by recorded user decision (do NOT treat as defects):**
- Fuller inline help: `rpg/data/help.json` carries the Phase-11 placeholder ("More detailed step-by-step guidance is planned for a later update (Phase 11…)").
- Real 20-AA cast: deferred to Phase 9 (07-01 decision #6); `introduction` teaching text references placeholder stand-ins.
- Numeric P/O yields: banned (07-04 Decision 8, no-ROS-v1); a contested-tier + modern-source path is documented for the future.
- Citrate-synthase biological-assembly (dimer) load: flagged, never implemented (D7).
- Dormant PDBs (2VGG/6CER/1ZP0): approved-but-unloaded, documented per-node.
- Ending CG cutscenes: Phase 12.

## Test Coverage Gaps

**Qt/GUI code has zero automated runtime coverage (inherent, by design):**
- What's not tested: Every `pymol.Qt.*` code path — `rpg/ui/main_window.py`, `rpg/ui/widgets.py`, `rpg/ui/edit_dialog.py`, `rpg/ui/save_load_dialogs.py`, `rpg/ui/achievements_dialog.py`, `rpg/ui/help_dialog.py`, `rpg/ui/bulk_download_dialog.py`, `rpg/ui/plugin_entry.py`.
- Files: `rpg/ui/` (all Qt classes)
- Risk: A Qt regression ships unnoticed until a human plays; three Phase-6 human-verify rounds were needed to catch 5 real bugs (banner persistence, single-carbon sele, edit-dialog tuple, edit-prompt stash, restart stash).
- Priority: **High (structural)** — mitigate by keeping the controller choke point (`rpg/ui/controller.py`) thin and fully unit-tested (767 lines, MockCmd-injected, the one human-untestable-free surface), and by preserving the per-phase human-verify checkpoint discipline.

**Story-editor JS runtime is never executed in WSL:**
- What's not tested: Actual browser execution of `tools/story_editor_assets/*.js` — only structural batteries (ES5 pins, greps, emitted-page order) run under python3.6; headless-Chrome smokes ran once per plan from gitignored `tmp/opencode-*/` sessions with an honest Chrome≠Firefox limitation.
- Files: `tools/story_editor_assets/`, `story_editor.html`
- Risk: Proven material — the 07.1-11 REJECTED verdict was exactly a runtime-only failure (`fetch()` vs `file://` in Firefox) that all structural tests passed through.
- Priority: **High for Phase 7.1 close** — the one-step Firefox re-verification (pending) is the current mitigation; after it, runtime verification of later editor assets should ride the same human checkpoint pattern.

**Integration smoke not wired into any gate:**
- What's not tested: Nothing prevents `tools/controller_integration_smoke.py` from staying red — the 3 documented FAILs have persisted since 2026-09-04 while all unit gates stay green.
- Files: `tools/controller_integration_smoke.py`
- Risk: Known-regression camouflage (see Tech Debt entry).
- Priority: **Medium** — fix the 3 stage-9 expectations in a dedicated session; consider adding a SMOKE_RESULT parse check to the plan-close checklist.

**Save/load camera-only semantics are a documented product limitation, not a bug:**
- What's not tested/restored: Manual color/rep changes made before a save intentionally do NOT restore (scene rebuilds from the node's `on_enter` replay; saved view is CAMERA-only per 06-03).
- Files: `rpg/ui/controller.py` (save/load), `rpg/state.py`
- Risk: User surprise; document in Phase 11 help text.
- Priority: Low (documentation task).

---

## Open Human Checkpoints (blocking state, 2026-09-10)

1. **Phase 7 close:** 07-18 Task 2 — human batch content review of all Phase 7 content (BLOCKING; gate battery ALL GREEN).
2. **Phase 7.1:** 07.1-11 one-step Firefox re-verification of the direct-XHR load fix (gate re-opened pending verdict).
3. **Pitfall 9 (C14 decay):** RESOLVED via DROP 2026-08-15 — no half-life citation needed; radioactive decay removed as a bad-ending trigger. **Doc conflict remains** between AGENTS.md/PITFALLS.md ("pending") and spec.md/PROJECT.md ("resolved") — the stale-docs tech-debt entry above.

---

*Concerns audit: 2026-09-10*
