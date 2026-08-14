---
phase: 03-pymol-cmd-layer-asset-mgmt
plan: 01
subsystem: infra
tags: [pymol, headless, smoke-test, wsl-windows-bridge, cmd-api, source-citation]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: c14.paths.data_path() — __file__-relative absolute path resolver (cwd-independent); the smoke resolves the bundled fixture + downloaded dir through it
provides:
  - "Headless test harness: tools/run_headless.sh (reusable WSL->Windows PyMOL bridge wrapper)"
  - "SMOKE_RESULT: PASS|FAIL stdout sentinel + bash-grep verdict contract (NOT exit code — the bat ALWAYS returns 0)"
  - "Bundled fixture c14/data/assets/bundled/_smoke.pdb (3-atom PDB, one atom named C1) for load tests"
  - "Source-citation convention: # src: tmp/pymol-src/modules/pymol/<file>.py:<line> cmd.<name> on every cmd.* call (greppable, 22 citations in the smoke)"
  - ".gitignore entry for c14/data/assets/downloaded/ (runtime cache, NOT committed; bundled/ IS committed)"
  - "Empirically-corrected cmd.create pitfall documentation (PITFALLS.md Pitfall 3: 1,1 drops multi-state; self-copy destructive; default-args working)"
affects: [03-02-asset-manager, 03-03-molops, 04-editing-restore, "any future headless PyMOL test"]

# Tech tracking
tech-stack:
  added: []  # no new libraries — pure pymol.cmd.* + bash only (constraint honored)
  patterns:
    - "SMOKE_RESULT: PASS|FAIL stdout sentinel + bash grep ^SMOKE_RESULT: PASS (verdict via stdout, NOT $? — the bat always returns 0 because `call conda deactivate` overwrites %ERRORLEVEL%)"
    - "# src: tmp/pymol-src/modules/pymol/<file>.py:<line> cmd.<name> source-citation comment on every cmd.* call (read-the-source-first convention, machine-greppable)"
    - "wslpath -w for WSL->Windows path conversion (more reliable than \\\\wsl$ UNC paths)"
    - "Bundled (c14/data/assets/bundled/, committed, ships in zip) vs Downloaded (c14/data/assets/downloaded/, gitignored, runtime cache) asset directory split"
    - "os.getcwd() + import c14.paths for path resolution in PyMOL-run scripts (__file__ resolves to pymol's __init__.py, NOT the script)"
    - "?-prefix post-condition for cmd.delete (count_atoms('?'+name)==0; bare count_atoms on deleted object RAISES CmdException)"
    - "Default-args cmd.create(backup, source) for backups (source_state=0, target_state=0 = ALL states; NOT 1,1 which drops multi-state)"

key-files:
  created:
    - "tools/api_sanity_smoke.py — Headless api-sanity smoke exercising every cmd.* call with post-condition assertions + SMOKE_RESULT sentinel"
    - "tools/run_headless.sh — Reusable bash wrapper for the WSL->Windows headless bridge (greps ^SMOKE_RESULT: PASS)"
    - "c14/data/assets/bundled/_smoke.pdb — 3-atom PDB fixture (C1/O1/C2) for the smoke's load test"
  modified:
    - ".gitignore — added c14/data/assets/downloaded/ (runtime cache excluded)"
    - ".planning/research/PITFALLS.md — Pitfall 3 empirically corrected (no-op -> incomplete-multi-state + destructive-self-copy + default-args-working)"

key-decisions:
  - "Verdict via stdout SMOKE_RESULT sentinel, NOT exit code — the bat ALWAYS returns 0 (conda deactivate overwrites %ERRORLEVEL%; PyMOL swallows exceptions). This reinterprets SC #1's 'exit code 0' as 'sentinel present'."
  - "Default-args cmd.create(backup, source) is the working backup form (all states). create(bak,src,1,1) copies ONLY state 1 (incomplete multi-state backup); create(obj,obj) self-copy is DESTRUCTIVE. The prior 'no-op' claim did not reproduce."
  - "delete post-condition MUST use ?-prefix: count_atoms('?smk')==0. Bare count_atoms('smk') on a deleted object RAISES CmdException."
  - "Bundled assets (committed, ship in plugin zip) live in c14/data/assets/bundled/; downloaded assets (runtime cache, gitignored) live in c14/data/assets/downloaded/. Separate dirs = separate roles."
  - "Network fetch stages (fetch_cid, fetch_pdb) report failure but do NOT hard-fail the whole smoke — offline is a real deployment concern (Pitfall 5)."

patterns-established:
  - "Pattern: SMOKE_RESULT stdout sentinel + bash grep verdict for all headless PyMOL tests (Plans 02 + 03 reuse this)"
  - "Pattern: # src: tmp/pymol-src citation on every cmd.* call (Plans 02 + 03 must follow this for AssetManager + MolOps)"
  - "Pattern: tools/run_headless.sh <script.py> as the reusable headless invocation (cwd=repo-root)"
  - "Pattern: bundled/ (committed) vs downloaded/ (gitignored) asset directory split"

# Metrics
duration: 91 min
completed: 2026-08-14
---

# Phase 3 Plan 01: Headless Harness + API-Sanity Smoke + Source-Citation Convention Summary

**Headless WSL->Windows PyMOL bridge proven via api-sanity smoke (10 cmd.* stages all green, SMOKE_RESULT stdout sentinel) + source-citation convention established + cmd.create pitfall empirically corrected**

## Performance

- **Duration:** 91 min
- **Started:** 2026-08-13T23:34:00Z
- **Completed:** 2026-08-14T01:05:13Z
- **Tasks:** 2
- **Files modified:** 5 (3 created, 2 modified)

## Accomplishments
- Proved the WSL->Windows headless bridge works for every `cmd.*` call the game will use: the smoke exercises load, fetch (cid + pdb), hide, show, show_as, select, zoom, color, create-for-backup, and delete — each with a post-condition assertion — and ALL 10 stages print `SMOKE: PASS` (load=3 atoms, fetch_cid=21 atoms aspirin, fetch_pdb=327 atoms crambin, show_rep=3, show_as=3, select=1, zoom, color, create_backup bak=3=smk, delete=?smk->0).
- Established the two contracts every later headless test reuses: (1) the `SMOKE_RESULT: PASS|FAIL` stdout sentinel + bash-grep verdict (because the bat ALWAYS returns exit 0 — `call conda deactivate` overwrites `%ERRORLEVEL%`); (2) the `# src: tmp/pymol-src/modules/pymol/<file>.py:<line> cmd.<name>` source-citation convention (22 citations in the smoke, greppable).
- Delivered `tools/run_headless.sh` — a reusable bash wrapper for the WSL->Windows headless bridge incantation (`wslpath -w` + `timeout 150 cmd.exe /c run-conda-pymol.bat -cq` + grep `^SMOKE_RESULT: PASS`). Plans 02 + 03 call this directly.
- Empirically corrected the `cmd.create` pitfall in PITFALLS.md: the "silent no-op" claim did NOT reproduce for a new-target backup. The real gotchas are (a) `create(bak,src,1,1)` copies only state 1 (incomplete multi-state backup — silent data loss), (b) `create(obj,obj)` self-copy is DESTRUCTIVE (raises + corrupts), (c) default-args `cmd.create(backup, source)` is the working form (all states, matches ARCHITECTURE.md:304). Updated title, What-goes-wrong, Known-traps bullet, Pitfall-to-Phase map, and Sources line.
- Gitignored `c14/data/assets/downloaded/` (runtime cache for fetched structures; machine-specific, regenerable, NOT committed) while keeping `c14/data/assets/bundled/` tracked (committed fixtures ship in the plugin zip). Verified via `git check-ignore`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create the api-sanity smoke + bundled fixture + reusable headless wrapper, run it headless, assert SMOKE_RESULT: PASS** - `d544274` (feat)
2. **Task 2: Gitignore the downloaded-asset dir + correct PITFALLS.md Pitfall 3 wording + verify citation convention** - `5ea70fd` (chore)

**Plan metadata:** (pending — final docs commit below)

## Files Created/Modified
- `tools/api_sanity_smoke.py` (created) — Headless api-sanity smoke; pure `pymol.cmd.*` (no Qt); 10 stages with post-condition assertions; `SMOKE_RESULT:` sentinel; 22 `# src:` citations; uses `os.getcwd()` + `import c14.paths` (NOT `__file__` which resolves to pymol's `__init__.py`)
- `tools/run_headless.sh` (created) — Reusable bash wrapper; `wslpath -w` path conversion; `timeout 150`; greps `^SMOKE_RESULT: PASS` (presence=pass, absence=fail); exit code only for infra-failure detection (124=timeout, 139=segfault)
- `c14/data/assets/bundled/_smoke.pdb` (created) — 3-atom PDB fixture (C1, O1, C2 + END); the smoke's load-test fixture; committed (ships in plugin zip)
- `.gitignore` (modified) — Added `c14/data/assets/downloaded/` (runtime cache excluded); `bundled/` stays tracked
- `.planning/research/PITFALLS.md` (modified) — Pitfall 3 empirically corrected (no-op -> incomplete-multi-state + destructive-self-copy + default-args-working); 5 targeted edits (title, What-goes-wrong, Known-traps bullet, Pitfall-to-Phase map, Sources line)

## Decisions Made
- **Verdict via stdout sentinel, NOT exit code.** The bat ALWAYS returns 0 (`call conda deactivate` overwrites `%ERRORLEVEL%`; PyMOL's `parsing.run_file` swallows exceptions). SC #1's "exit code 0" is reinterpreted as "SMOKE_RESULT: PASS sentinel present". The harness greps `^SMOKE_RESULT: PASS` (presence = pass; absence = fail — stricter than grepping for FAIL, which would falsely pass if the smoke crashes before printing the sentinel).
- **Default-args `cmd.create` for backups.** `create(bak,src,1,1)` copies only state 1 (incomplete for multi-state); `create(obj,obj)` self-copy is DESTRUCTIVE. Default args (`source_state=0, target_state=0` = all states) is the working form. This is the empirically-corrected behavior documented in PITFALLS.md Pitfall 3.
- **`?`-prefix for delete post-condition.** Bare `count_atoms("deleted_obj")` RAISES `CmdException`; `count_atoms("?deleted_obj")` returns 0 (safe). The `?` is PyMOL's existing-objects-only selector prefix.
- **Network stages don't hard-fail.** `fetch_cid` and `fetch_pdb` report failure but do NOT fail the whole smoke — offline is a real deployment concern (Pitfall 5). The core non-network stages (load, show, select, zoom, color, create_backup, delete) MUST pass.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The `Write` tool could not create `tools/run_headless.sh` directly because the bash content contains backslash sequences (`\\wsl$`, `C:\\src\\`) that conflict with JSON string encoding. Resolved by writing the file via a bash heredoc (`cat > file <<'EOF'`) — a pragmatic choice when the file content's escaping conflicts with the Write tool's JSON transport. No impact on the final file content (verified byte-identical to the plan's specification; executable bit set via `chmod +x`).

## User Setup Required

None - no external service configuration required. The headless bridge uses the existing `C:\src\run-conda-pymol.bat` (user-owned, unmodified) and the existing Windows conda env `chemtools-win10`.

## Next Phase Readiness
- **Plan 03-02 (AssetManager)** is unblocked: it reuses `tools/run_headless.sh`, the `SMOKE_RESULT:` sentinel contract, the bundled `_smoke.pdb` fixture, the `c14/data/assets/downloaded/` gitignore, and the `# src:` citation convention. AssetManager's `load_bundled`/`fetch_pubchem`/`fetch_pdb` methods follow the same `cmd.load`/`cmd.fetch` patterns the smoke already validated (absolute paths via `c14.paths`, `async_=0`/`type=`/`path=` pitfall mitigations).
- **Plan 03-03 (MolOps)** is unblocked: it reuses the same harness + citation convention. MolOps' `MolAction -> cmd.*` dispatch follows the patterns the smoke validated (show/show_as/select/zoom/color/delete/create), and the `create_backup` + `delete` `?`-prefix post-conditions are proven.
- **Phase 4 (editing + restore)** benefits from the corrected `cmd.create` documentation: the restore safety net uses default-args `cmd.create` (all states), NOT `1,1` — the pitfall is now accurately documented before Phase 4 depends on it.
- **No blockers.** The smoke's network stages passed (PubChem + PDB reachable), confirming the Windows env has network access for fetch-based tests.
- **Awareness flag:** stray scratch files (`_probe.pdb`, `cid_2244.sdf`) remain inside the conda env's `site-packages/pymol/` dir from the research probes (harmless; `rm` is policy-denied; not in the repo). The user may remove them manually if desired.

---
*Phase: 03-pymol-cmd-layer-asset-mgmt*
*Completed: 2026-08-14*
