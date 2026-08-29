---
phase: 06-qt-ui-minimal-playable-mvp
plan: 13
subsystem: ui
tags: [pymol.Qt, QDialog, QDesktopServices, help, doc-03, json, wiki-links, QScrollArea]

# Dependency graph
requires:
  - phase: 06-RESEARCH-persistence-achievements
    provides: Pattern 6 (help.json schema + HelpDialog spec) + the 3 webfetch-verified wiki links (Alter, H_Add, Fetch)
  - phase: 04-editing-protonation-restore
    provides: the EDIT-01/02/03/05 mechanics the editing pointers describe in plain language (point mutation / substrate edit / protonation change / restore safety net)
  - phase: 01-foundations-citation-gate
    provides: c14.paths.data_path (cwd-independent __file__-relative bundled-data resolver) + tools/check_imports.py AST gate (c14/ui/ in SKIP_DIRS = gate-exempt)
provides:
  - "c14/data/help.json -- curated help content (4 editing pointers + 3 webfetch-verified PyMOL wiki links) for DOC-03"
  - "c14/ui/help_dialog.py -- HelpDialog(QDialog) that renders help.json (editing pointers as rich-text QLabels + wiki links as clickable QPushButtons opening the browser via QtGui.QDesktopServices.openUrl), wrapped in a QScrollArea"
affects: [06-qt-ui-minimal-playable-mvp (06-14 functional human-verify of the help dialog), 09-content-glucose-fatty-acid-alcohol (DOC-01/DOC-02 dramatic cast list + slogan -- separate from DOC-03), 11-documentation-finalization (final docs reflect shipped help content)]

# Tech tracking
tech-stack:
  added: []  # no new deps -- pymol.Qt (PyQt5 via pymol.Qt) + stdlib json, already approved (AGENTS.md)
  patterns:
    - "help-content-as-data: c14/data/help.json holds curated user-facing content; HelpDialog reads + renders it (editable without touching Python -- 06-RESEARCH Pattern 6)"
    - "QDesktopServices.openUrl for cross-platform browser launch inside PyMOL (the Qt way; never os.system/webbrowser)"
    - "default-arg lambda capture for Qt clicked signals in a loop: lambda _=False, u=link['url']: ... avoids the late-binding closure bug; _ takes the clicked() bool signal"

key-files:
  created:
    - c14/data/help.json
    - c14/ui/help_dialog.py
  modified: []

key-decisions:
  - "help.json content is FROZEN-verbatim from 06-RESEARCH-persistence-achievements.md Pattern 6 (4 editing pointers + 3 wiki links) -- no speculative additions (no-fabrication rule)"
  - "Only 3 webfetch-verified wiki links ship (Alter->Iterate, H_Add, Fetch) -- re-confirmed LIVE 2026-08-30 via the webfetch tool; no fabricated URLs (Open Question 3: ship the 3 verified links for Phase 6 MVP; add more only with a live-fetch verification step)"
  - "Help text is READ from help.json in HelpDialog (not hardcoded) so it is editable without touching Python (Pattern 6 scope guard)"
  - "Wiki links open via QtGui.QDesktopServices.openUrl (Qt way, cross-platform inside PyMOL) -- never os.system/webbrowser"
  - "Late-binding closure bug avoided via default-arg lambda capture (u=link['url']); _=False takes the clicked() bool signal arg"
  - "DOC-01/DOC-02 (dramatic cast list + slogan) NOT scoped here -- those are Phase 9 (the cast is not populated yet); help.json is ONLY editing pointers + wiki links (DOC-03)"
  - "c14/ui/help_dialog.py is GATE-EXEMPT (c14/ui/ is in tools/check_imports.py SKIP_DIRS) -- may import pymol.Qt; py_compile is the only WSL-verifiable check (importing fails in WSL with no Qt -- EXPECTED); the functional dialog is human-verify in 06-14"

patterns-established:
  - "Pattern: help-content-as-data -- a bundled JSON (c14/data/help.json) holds curated user-facing text; the Qt dialog reads + renders it so copy edits need no Python change"
  - "Pattern: default-arg lambda capture for Qt clicked signals wired in a loop -- `lambda _=False, u=value: ...` binds the loop variable per-iteration, avoiding the classic late-binding closure bug"

# Metrics
duration: 4min
completed: 2026-08-30
---

# Phase 6 Plan 13: In-Game Help Dialog (DOC-03) Summary

**HelpDialog (Qt) renders c14/data/help.json -- 4 editing pointers + 3 webfetch-verified PyMOL wiki links opened via QDesktopServices.openUrl -- no fabricated URLs, no DOC-01/02 scope**

## Performance

- **Duration:** 4 min
- **Started:** 2026-08-30T16:29:09Z
- **Completed:** 2026-08-30T16:33:09Z
- **Tasks:** 2
- **Files modified:** 2 (both new)

## Accomplishments
- Created `c14/data/help.json` -- the curated help content for DOC-03: 4 editing pointers (Point mutation / Substrate edit / Protonation change / Restore safety net) describing the Phase 4 EDIT-01/02/03/05 mechanics in plain language + 3 PyMOL wiki links (Alter, H_Add, Fetch). Content is FROZEN-verbatim from 06-RESEARCH-persistence-achievements.md Pattern 6.
- Re-confirmed all 3 wiki URLs resolve LIVE (2026-08-30) via the webfetch tool: Alter (redirects to the Iterate page -- covers alter read-write atom properties + sort-after-altering), H_Add (valence-only hydrogen add, NOT pH-aware), Fetch (PDB/PubChem download, async=0 for scripting). No fabricated URLs; no speculative additions (Show/Select/Sort/etc. NOT added -- would each require their own live-fetch verification per the no-fabrication rule).
- Created `c14/ui/help_dialog.py` -- `HelpDialog(QtWidgets.QDialog)` that reads help.json via `c14.paths.data_path` (cwd-independent), renders the editing pointers as rich-text `QLabel`s and the wiki links as `QPushButton`s that open the user's browser via `QtGui.QDesktopServices.openUrl` (the Qt way, cross-platform inside PyMOL). Content wrapped in a `QScrollArea` for overflow; Close button -> `self.accept()`.
- Avoided the late-binding closure bug in the wiki-link button loop with the default-arg lambda capture `lambda _=False, u=link["url"]: QtGui.QDesktopServices.openUrl(QtCore.QUrl(u))` (`_` takes the `clicked()` bool signal; `u` binds per-iteration). Added `setToolTip(link["note"])` + `label.setWordWrap(True)` for UX.
- Honored the scope guard: DOC-01/DOC-02 (dramatic cast list + slogan) are Phase 9 -- NOT scoped here. help.json is ONLY editing pointers + wiki links.
- WSL-verifiable gates green: `json.load` (4 pointers + 3 links), `py_compile` on help_dialog.py (exit 0), `tools/check_imports.py` AST gate (exit 0 -- c14/ui/ is gate-exempt). Functional dialog (pointers render, links open in browser) deferred to human-verify in plan 06-14.

## Task Commits

Each task was committed atomically (path-scoped -- only the task's own file staged + committed; the stray untracked `opencode.json.1` was NOT swept in):

1. **Task 1: Create c14/data/help.json (editing pointers + webfetch-verified wiki links)** -- `cbafb49` (feat)
2. **Task 2: Create c14/ui/help_dialog.py -- HelpDialog (renders help.json + clickable wiki links)** -- `96dcc1a` (feat)

**Plan metadata:** (this SUMMARY + STATE update -- committed separately, path-scoped)

## Files Created/Modified
- `c14/data/help.json` -- Curated help content: `version`, `editing_pointers` (4: point mutation / substrate edit / protonation change / restore safety net), `wiki_links` (3: Alter, H_Add, Fetch -- each with label/url/note). 2-space indent matching the repo's existing JSON style (cast.json, edits.json).
- `c14/ui/help_dialog.py` -- `HelpDialog(QtWidgets.QDialog)`: loads help.json via `c14.paths.data_path("data", "help.json")`, builds a QVBoxLayout inside a QScrollArea with the editing pointers (rich-text QLabels, word-wrapped) + wiki link buttons (QDesktopServices.openUrl, late-binding-safe lambda, tooltip = note) + Close button. Gate-exempt (imports `pymol.Qt`); py_compile clean; Python 3.6 compatible (no f-strings, `.format()`).

## Decisions Made
- **help.json content frozen verbatim from research Pattern 6** -- the plan explicitly required FROZEN-verbatim content (lines 434-456 of 06-RESEARCH-persistence-achievements.md); reproduced exactly (4 pointers + 3 links), no additions.
- **Only the 3 pre-verified wiki links ship** -- Open Question 3 of the research says "ship the 3 verified links for Phase 6 MVP; the planner adds more only with a live-fetch verification step." Re-confirmed all 3 live (2026-08-30); did NOT add speculative links (Show/Select/Sort/Stereo/etc.) because each would require its own live-fetch verification, which is out of scope for this plan.
- **QScrollArea always wraps the content** -- the plan said "wrap the content in a QScrollArea if it overflows"; a QScrollArea inherently handles overflow (scrollbars appear only when needed), so always-wrapping is the cleanest interpretation and future-proofs the dialog for when help text grows in Phase 9.
- **wordWrap=True + tooltip added** -- minor UX niceties (long pointer bodies wrap; the wiki link note shows on hover) consistent with AGENTS.md's "UI simple and user-friendly"; not behavior changes, not deviations.
- **Direct indexing `self.data["editing_pointers"]` / `self.data["wiki_links"]`** -- matches the research Pattern 6 example; fails loud (KeyError) on a broken help.json rather than silently showing an empty dialog (help.json is a bundled asset validated at build time, so direct access is safe and a loud failure is preferable to silent degradation).

## Deviations from Plan

None -- plan executed exactly as written. Both tasks produced exactly the files specified in their `<files>` elements; no auto-fixes (Rules 1-3), no architectural changes (Rule 4), no authentication gates. The two minor UX additions (`label.setWordWrap(True)` and the QScrollArea's `setFrameShape(NoFrame)` + `resize(540, 480)` initial sizing) are within the plan's "UI simple and user-friendly" latitude and the explicit "Wrap the content in a QScrollArea if it overflows" guidance -- not behavior-changing deviations.

## Issues Encountered
None. The WSL clock returned 2026-08-29 while the environment date is 2026-08-30 (a known WSL time-drift); the SUMMARY uses the environment-authoritative date (2026-08-30) for the `completed` field and the WSL-measured time-of-day for Started/Completed ISO timestamps; the 4-min duration is epoch-based and accurate regardless.

## User Setup Required
None -- no external service configuration required. The wiki links open in the user's default browser via Qt (no API keys, no env vars, no dashboard config).

## Next Phase Readiness
- **Ready for 06-14**: the HelpDialog is built and py_compile-clean; plan 06-14 (per the plan's `<verification>` note: "The functional help dialog (editing pointers show, wiki links open in browser) is human-verify in 06-14") will exercise the real Qt dialog in a Windows PyMOL session (WSL cannot run Qt -- AGENTS.md).
- **Ready for the main-window controller (06-06+)**: the controller can construct `HelpDialog(parent=main_window)` and wire a "Help" menu/button to it; HelpDialog is self-contained (loads its own data, no constructor args beyond `parent`).
- **Ready for Phase 9 (DOC-01/DOC-02)**: help.json's schema (`version` + `editing_pointers` + `wiki_links`) is independent of the dramatic cast list / slogan -- those Phase-9 additions will be separate (a `cast` section in README / a separate cast dialog, NOT appended to help.json per the scope guard).
- **Blockers/concerns**: none. The functional human-verify (links actually open in the user's browser, pointers render readably) remains pending 06-14 -- this is by design (Qt is not WSL-runnable).

---
*Phase: 06-qt-ui-minimal-playable-mvp*
*Completed: 2026-08-30*
