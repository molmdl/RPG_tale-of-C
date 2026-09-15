---
status: resolved
trigger: "story-editor-file-load: committed repo-root story_editor.html does not auto-load via file:// in Firefox (and Chrome); boot panel shows 'No data loaded' state"
created: 2026-09-15
updated: 2026-09-15
symptoms_prefilled: true
goal: find_and_fix
verdict: RESOLVED — root cause CONFIRMED empirically on the user's own Firefox 155.0.1; fix landed + verified headlessly
---

## Current Focus

COMPLETE. Root cause confirmed → fix landed (10_load.js v0.3.0 + shell copy + battery re-pin + regenerated HTML) → all gates green (suite 600 OK, lint 0, headless Chrome r3-plain/r3-allow/r3-drop, Firefox-155 real-page screenshot) → committed. Remaining: the user's ONE-GESTURE re-verification (double-click → drag RPG_tale-of-C folder onto the drop zone).

## Symptoms

expected: Double-clicking repo-root story_editor.html in Firefox auto-loads data sub-directories and renders the 57-node graph with zero clicks.
actual: Boot panel shows "No data loaded — the graph needs the story bundle. Load data first: use the boot panel at the top of the page (silent probe or folder pick)" in Firefox; Chrome also fails ("well chrome not working too").
errors: none provided yet
reproduction: open the file in Firefox (file://) → boot panel appears; same in Chrome
started: never worked for the user across BOTH checkpoint rounds (round 1: fetch-probe premise + dead pick; round 2: XHR fix landed but auto-load still fails). User's same-dir iframe proof (tmp/network_all.html) demonstrates their Firefox permits same-dir subresource loads.

## Eliminated

- hypothesis: XHR status-0 not accepted as success on file://
  evidence: tools/story_editor_assets/10_load.js lines 449-472: xhrText() accepts `xhr.status === 0` (line 461) alongside 200-299, provided responseText is a non-empty string. The prior prompt explicitly flags this simple hypothesis as already refuted.
  timestamp: 2026-09-15

## Evidence

- timestamp: 2026-09-15
  checked: tools/story_editor_assets/10_load.js (lines 1-1286)
  found: EXPECTED paths = data/story_glucose/manifest.json (block), data/citations.json (warn), data/sources.json (warn), rpg/data/edits.json (block), rpg/data/cast.json (warn). boot() probes MANIFEST_PATH via xhrText; on success reads fixed + manifest-listed story files via xhrMany, then completeFromTexts(texts,"direct"). On manifest miss -> showFolderPickPanel(). Watchdog reveals pick panel after 4s if probe unsettled. Boot-panel hide = collapseBootPanel() (adds class boot-loaded, unhides head row, collapses details) called from finishLoad() after ED.setBundle.
  found: shell boot: DOMContentLoaded -> EDITOR.runInits() (shell.html line 147-149). The user-visible text "No data loaded — the graph needs the story bundle..." does NOT match shell.html's #boot-probe-status ("Probing this folder…") nor 10_load.js strings — likely emitted by another asset (graph/empty state) or a stale/different committed HTML. MUST diff committed story_editor.html vs regenerated assets.
  implication: two distinct failure families still live: (a) probe never runs / never succeeds, (b) probe succeeds but UI never shows loaded state. The reported message wording mismatch hints committed HTML may be stale vs assets, or the visible "boot panel" text comes from a different asset than 10_load.js.

## Eliminated (round 2)

- hypothesis: H1 wrong probe paths vs real disk layout (committed HTML stale, or EXPECTED list mismatch)
  evidence: data/story_glucose/manifest.json + all 7 manifest.files + data/citations.json + data/sources.json + rpg/data/edits.json + rpg/data/cast.json all exist at EXACTLY the EXPECTED paths. `python3.6 tools/story_editor.py` regeneration = byte-identical to committed story_editor.html except generated-at timestamp → committed HTML ships the current fixed 10_load.js. AND the allowfiles headless run loaded all 12 files through the real probe paths.
  timestamp: 2026-09-15
- hypothesis: H2 probe never fires (init-registry exception / gating bug / earlier-asset crash / runInits not failure-isolated)
  evidence: 00_core.js runInits wraps EACH init in try/catch (lines 73-81) — one broken init cannot kill boot(). 10_load.js registers a single EDITOR.init(mount…; boot()) at its end; shell fires runInits on DOMContentLoaded. Real-headless-Chrome allowfiles run: probe status transitioned "Looking for the data files…" → "Data files found — auto-loading…" and completed — the probe fires. In the plain run the probe also fired (CORS error logged) and correctly fell back.
  timestamp: 2026-09-15
- hypothesis: H3 success path broken (setBundle not wired / panel never hides / graph tab needs tab-switch)
  evidence: real-XHR headless run --allow-file-access-from-files on the REAL committed story_editor.html (no stub, no simulation of code — only the documented permission flag): #boot-panel gained class "boot-loaded"; 57 [data-node-id] SVG groups rendered; pick wrap stayed hidden; summary "Loaded 7 story file(s)…"; zero console errors (only 05_json serializer self-test info). The only console line in the plain (no-flag) run: CORS block on the manifest XHR → probe correctly settled to "Direct reads are blocked here — use the folder picker below (one click).", pick wrap revealed, no uncaught errors. Entire success AND fallback flows proven live in Chrome-Chromium engine.
  timestamp: 2026-09-15

## Evidence (round 2)

- timestamp: 2026-09-15
  checked: committed artifact freshness
  found: regeneration diff = generated-at timestamp only → committed story_editor.html == current assets. User tests the fixed code.
  implication: cannot blame staleness; the runtime behavior difference is browser-side.
- timestamp: 2026-09-15
  checked: headless Chrome (Windows, real binary) — plain and --allow-file-access-from-files, --dump-dom, virtual-time-budget 12s (harness tmp/opencode-debug-fileload/, gitignored)
  found: allowfiles: AUTOLOAD end-to-end OK (boot-loaded, 57 nodes, 7 files). plain: correct designed fallback (CORS rejection → pick reveal; probe text visible). Both 0 uncaught errors.
  implication: the page's own XHR code + completion path + graph wiring are CORRECT. The only variable left is the file:// permission model of the user's actual Firefox (H4). Chrome file:// failing is by-design (expected); the pick fallback is present and reachable live.
- timestamp: 2026-09-15
  checked: environment / browser inventory (read-only)
  found: Firefox EXISTS on the user's Windows: HKLM App Paths firefox.exe = C:\Program Files\Mozilla Firefox\firefox.exe; registered handlers FirefoxHTML-308046B0AF4A39CB. WSL2 localhost-forwarding to Windows is OFF here (server-based http testing unavailable + user vetoed servers anyway).
  implication: I CAN exercise the real Firefox headlessly: firefox.exe --headless --screenshot on file:// — decisive H4 test without a human click.

## Evidence (round 3 — decisive, all on the user's own machine)

- timestamp: 2026-09-15
  checked: headless Firefox 155.0.1 (C:\Program Files\Mozilla Firefox\firefox.exe; user's own install — registered handler FirefoxHTML-308046B0AF4A39CB), fresh default profile, file:// screenshot probes with diag overlays (tmp/opencode-debug-fileload/, gitignored)
  found: v3 sync-XHR matrix: SYNC manifest THROWS NetworkError; SYNC citations THROWS; SYNC edits THROWS; SYNC missing-file THROWS; SYNC above-dir THROWS — identical errors for EXISTING and missing files (policy denies the read, not the existence). v4: iframe.contentDocument=null for SAME-DIR json AND subdir/2-level json AND above-dir.
  implication: default FF155 = no programmatic file reads from file:// pages, any direction. Async questions were isolated from screenshot-timing artifacts via synchronous probes + load-event waits.
- timestamp: 2026-09-15
  checked: pref matrix (4 headless profiles with injected user.js): A defaults / B privacy.file_unique_origin=false / C security.fileuri.strict_origin_policy=false / D both
  found: A(=B): NetworkError + iframe null (file_unique_origin IRRELEVANT). C(=D): SYNC manifest OK status=200 len=234, same-dir json OK len=45, subdir AND 2-level iframe HTML DOMs READABLE (incl. reading the story editor itself).
  implication: strict_origin_policy is THE controlling switch; the legacy same-directory-or-below read window survives only under =false. Honest nuance v. round-2: the 07.1-11 premise was true for its era but is false in FF155 defaults.
- timestamp: 2026-09-15
  checked: user's REAL profile prefs (read-only): AppData\Roaming\Mozilla\Firefox\Profiles\{8dqobjre.default,o8tbar6h.default-release}\prefs.js+user.js; installs.ini Default=o8tbar6h.default-release (Locked=1, currently running)
  found: NO fileuri/file_unique_origin overrides in either profile.
  implication: the headless fresh-profile verdict transfers verbatim to the user's interactive browser — their boot() XHR probe must fail, revealing the fallback. Matches "not working" + the graph empty-state quote exactly.
- timestamp: 2026-09-15
  checked: post-fix runtime gates
  found: suite 600 OK; lint 0/1-notice exit 0; headless-Chrome r3-plain (fallback reveal ✓), r3-allow (auto-load 57 nodes ✓ regression), r3-drop synthetic-DND 9/9 ✓ incl. decoy-discipline; Firefox-155 real-page screenshot (probe miss → one-gesture panel with drop zone) ✓.
  implication: fix verified end-to-end everywhere reachable from WSL; only the genuine OS drag gesture remains with the user.

## Resolution

root_cause: |
  CONFIRMED on the user's own Firefox (155.0.1, fresh default profile, headless):
  file:// XHR throws NetworkError for EVERY local read — same-dir, subdir,
  2-level, even existing files behave identically to missing files — when
  security.fileuri.strict_origin_policy has its DEFAULT (true). The
  "same-directory-or-below reads permitted under strict_origin_policy"
  premise (round-2 fix basis, MFSA 2019-21-era) NO LONGER HOLDS for
  programmatic reads: file: pages get NO XHR content (status nevers arrives;
  sync XHR proven THROWING NetworkError synchronously) and NO iframe
  contentDocument access (contentDocument=null for same-dir AND subdir
  documents). iframes still DISPLAY (the user's network_all.html proof is
  display-only — never content access). With strict_origin_policy=false
  (prefC profile): sync XHR OK status=200 len=234 (manifest), same-dir json
  OK, subdir/2-level iframe DOMs READABLE — the single controlling switch.
  privacy.file_unique_origin=false: no effect (prefB == prefA).
  The user's real profile (o8tbar6h.default-release, installs.ini Default,
  currently Locked=1/running) contains NO fileuri pref overrides → defaults
  apply to the user interactively.
  CONSEQUENCE: zero-click auto-load of subdir JSON from file:// is
  IMPOSSIBLE on default current Firefox AND Chrome (Chrome blocks by
  design). The boot probe therefore always falls back in the user's
  browsers; round-2's XHR fix could never have worked. (Headless-Chrome
  with --allow-file-access-from-files DID auto-load end-to-end: the page's
  completion path is correct.)
fix: |
  10_load.js v0.3.0: corrected policy record in-source; probe-first kept
  (works over http / --allow-file-access-from-files); on miss -> reveal a
  ONE-GESTURE panel: drag-and-drop folder zone (DataTransferItem
  .webkitGetAsEntry() recursive traversal with readEntries batch loop;
  only matched files become File objects — .git enumerated by name only)
  + the existing one-click webkitdirectory pick (round-2 snapshot fix
  preserved). Document-level dragover/drop preventDefault so a missed drop
  never navigates the page away. shell.html copy made honest. Advanced
  about:config note documented but NOT promoted.
verification: |
  1. Structural: suite 600 OK (baseline 577; load battery re-pinned incl.
     new test_dragdrop_folder_zone); lint 0 errors / 1 sanctioned notice
     (exit 0); story_editor.html regenerated (14 assets, 730,506 bytes);
     ES5 greps clean (no arrows/let/const/template/module/literal-close).
  2. Headless Chrome on the REAL regenerated page (no code simulation):
     - r3-plain (stock file://): probe misses -> status "Direct reads are
       blocked here — drag the repository folder onto the zone below, or
       pick it (one click)."; pick wrap revealed WITH the drop zone;
       zero uncaught errors. [the designed default-browser path]
     - r3-allow (--allow-file-access-from-files): ".Data files found —
       auto-loading…", #boot-panel.boot-loaded, 57 [data-node-id] groups,
       pick wrap stays hidden. [probe path regression-safe]
     - r3-drop (synthetic drop on #boot-drop-zone with mock
       webkitGetAsEntry tree + 3-item readEntries batches): 9/9 PASS —
       bundle loaded, 7 files, 57 nodes, "Data loaded from the dropped
       folder" banner, pickSource "drop", boot-loaded, 12 ✓ rows, and
       the .git/config + README.md decoy entries' .file() NEVER called
       (wanted-paths-only materialization proven); zero uncaught errors.
       [same evidence class as the 07.1-11 synthetic-pick smoke; the OS
       drag gesture itself is the remaining human step]
  3. Firefox 155.0.1 (user's own install, headless screenshot of the REAL
       regenerated page): probe runs, misses, and the one-gesture panel
       renders exactly as designed — status line + honest note + dashed
       "Drag your repository folder here" zone + Browse pick + draft input.
  4. Honest limit: the real drag gesture + real folder contents complete
       the loop in the user's interactive browser — ONE-STEP user
       re-verification prepared in the report.
files_changed:
  - tools/story_editor_assets/10_load.js (v0.3.0: corrected policy record, DND zone + traversal + guards, pickSource "drop", getFileAt/materializeFiles, global drop guard, honest copy)
  - tools/story_editor_assets/shell.html (honest help/statusbar copy; ids + expected paths preserved for generator pins)
  - tests/test_story_editor_load.py (docstring record correction + policy pins + test_dragdrop_folder_zone + inlined needle)
  - story_editor.html (regenerated, committed)
  - .planning/STATE.md (brief round-3 entry)
