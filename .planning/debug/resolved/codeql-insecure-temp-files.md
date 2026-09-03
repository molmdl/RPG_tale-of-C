---
status: resolved
trigger: "CodeQL reports 7 High-severity 'Insecure temporary file' alerts across two files on main. Fix them; commit message must mention each alert ID (e.g., 'Fixes CodeQL alert #1 ... #7')."
created: 2026-09-04T00:00:00Z
updated: 2026-09-04T00:20:00Z
---

## Current Focus

hypothesis: CONFIRMED + FIXED + VERIFIED -- all 7 sites were tempfile.mktemp(); replaced with mkdtemp()+join; all verification passed.
test: n/a (resolved)
expecting: n/a
next_action: archive + commit (alert IDs in message)

## Symptoms

expected: CodeQL scan reports no alerts. Temp files created with secure, race-free APIs (tempfile.mkstemp() or NamedTemporaryFile(delete=False)).
actual: 7 High-severity CodeQL alerts "Insecure temporary file":
  - Alert #7: tests/test_controller.py :561
  - Alert #6: tools/controller_integration_smoke.py :512
  - Alert #5: tools/controller_integration_smoke.py :871
  - Alert #4: tools/controller_integration_smoke.py :854
  - Alert #3: tools/controller_integration_smoke.py :838
  - Alert #2: tools/controller_integration_smoke.py :194
  - Alert #1: tools/controller_integration_smoke.py :126
errors: CodeQL static-analysis findings (not runtime errors).
reproduction: CodeQL scan on main branch.
started: Alerts opened 4-5 days ago; files presumably written around then.

## Eliminated

- hypothesis: mkstemp()+close is a drop-in replacement at all 7 sites
  evidence: rpg/achievements.py:130-132 AchievementBoard._load does `if os.path.isfile(path): json.load(...)` with NO try/except -> a pre-created EMPTY mkstemp file raises JSONDecodeError at board construction; board sites require a not-yet-existing path
  timestamp: 2026-09-04T00:02:00Z
- hypothesis: the 3 smoke FAILs (pyr_branch_anaerobic_cond_not_met, bulk_download_missing_empty_placeholder, bulk_download_expected_chars_empty) were caused by the temp-file fix
  evidence: differential run -- stashed the fix, re-ran smoke on unmodified HEAD: identical SMOKE_FAILED_STAGES (pre-existing data drift: real PDB IDs 6WCV/5UPP/5LDW now in the cast; cond data changed); post-fix output is line-identical to pre-fix (72/72 lines) except the intended path-shape change on save_file_exists
  timestamp: 2026-09-04T00:15:00Z

## Evidence

- timestamp: 2026-09-04T00:01:00Z
  checked: all 7 flagged lines + grep for mktemp repo-wide
  found: exactly 7 code sites, all `tempfile.mktemp(suffix=...)` (2 others are prose in .planning docs); mktemp returns a predictable, NOT-yet-created path -> TOCTOU/symlink race (CodeQL py/insecure-temporary-file)
  implication: root cause confirmed at every alert line; no additional code sites
- timestamp: 2026-09-04T00:02:00Z
  checked: rpg/achievements.py:104-151 (AchievementBoard consumer)
  found: `_load()` does `if os.path.isfile(self.path): json.load(...)` with NO try/except -> a pre-created EMPTY file (as tempfile.mkstemp would make) raises JSONDecodeError at board construction
  implication: mkstemp()+close is NOT drop-in for the 5 AchievementBoard sites; the fix must preserve "path does not exist yet" semantics
- timestamp: 2026-09-04T00:03:00Z
  checked: rpg/persist.py:38-52 (SaveStore.save via Controller.save)
  found: save opens `"w"` (overwrites) -> pre-created empty file would be tolerated, but not needed
  implication: one uniform mkdtemp()+join pattern works for all 7 sites
- timestamp: 2026-09-04T00:04:00Z
  checked: repo tempfile conventions
  found: tests/test_controller.py:242-244 already uses `tmpdir = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmpdir); path = os.path.join(tmpdir, "save.json")`; tools/demo_playthrough.py:97 + build_plugin_zip.sh:75 use mkdtemp()+join; python3.6-compatible
  implication: mkdtemp()+join is the established repo convention -- apply it at all 7 sites for consistency
- timestamp: 2026-09-04T00:10:00Z
  checked: python3.6 -m py_compile on both fixed files; python3.6 -m unittest tests.test_controller -v
  found: both compile clean; 33/33 tests OK including test_load_clears_pending_edit_stashes (the alert-#7 test)
  implication: syntax + unit-level verification passed
- timestamp: 2026-09-04T00:12:00Z
  checked: headless PyMOL run of the full smoke (bash tools/run_headless.sh tools/controller_integration_smoke.py via C:\src\run-conda-pymol.bat)
  found: all 69 checks around the fixed sites PASS -- AchievementBoard sites construct + unlock (ach_bad_ending/ach_true_ending), save/load round-trip passes with save path now `...\Temp\tmpXXXXXXXX\_smoke_save.json` (unpredictable mkdtemp dir); SMOKE lines byte-identical to pre-fix except that path shape
  implication: runtime behavior preserved for alerts #1-#6
- timestamp: 2026-09-04T00:15:00Z
  checked: differential run on unmodified HEAD (git stash -> rerun -> stash pop)
  found: identical 3 pre-existing FAILs + identical SMOKE_FAILED_STAGES; PASS count 66=66
  implication: fix introduces zero behavioral regressions; smoke FAILs are pre-existing data drift (out of scope for this alert fix)

## Resolution

root_cause: All 7 CodeQL "Insecure temporary file" alerts are `tempfile.mktemp(suffix=...)` calls -- mktemp returns a predictable filename WITHOUT creating the file, so another local user can win a TOCTOU race (pre-place a symlink at the guessed path; the subsequent board/save write follows it). 
fix: Replaced with `tempfile.mkdtemp()` (unpredictable 0700 dir, created atomically) + `os.path.join(dir, fixed_name)` inside it -- race-free, python3.6-safe, and the repo's established convention (demo_playthrough.py:97, test_controller.py:242-244). Smoke file gained a `_secure_temp_path(name)` helper (all 6 sites use it); test file uses the inline mkdtemp+addCleanup idiom. Cleanup upgraded from os.remove(file) to shutil.rmtree(dir) where cleanup already existed (smoke final cleanup + stage-8 save; test addCleanup). Preserves the not-yet-existing-path semantics AchievementBoard requires.
verification: (1) python3.6 -m py_compile: both files clean. (2) python3.6 -m unittest tests.test_controller: 33/33 OK (incl. the alert-#7 test). (3) Full headless PyMOL smoke run: all fixed-site checks PASS; output identical to pre-fix except the intended path-shape change. (4) Differential on HEAD: the 3 smoke FAILs are pre-existing and unrelated.
files_changed: ["tests/test_controller.py", "tools/controller_integration_smoke.py"]

## Per-Alert Tracking

| Alert | File:Line | Insecure pattern found | Replacement applied | Verified |
|-------|-----------|------------------------|---------------------|----------|
| #1 | tools/controller_integration_smoke.py:126 | `tempfile.mktemp(suffix="_smoke_ach.json")` | `_secure_temp_path("_smoke_ach.json")` (mkdtemp+join) | py_compile + headless smoke PASS (ach board constructs/unlocks) |
| #2 | tools/controller_integration_smoke.py:194 | `tempfile.mktemp(suffix="_smoke_ach.json")` | `_secure_temp_path("_smoke_ach.json")` | py_compile + headless smoke PASS |
| #3 | tools/controller_integration_smoke.py:838 | `tempfile.mktemp(suffix="_smoke_ach_s.json")` | `_secure_temp_path("_smoke_ach_s.json")` | py_compile + headless smoke PASS (stage-8 board) |
| #4 | tools/controller_integration_smoke.py:854 | `tempfile.mktemp(suffix="_smoke_save.json")` | `_secure_temp_path("_smoke_save.json")` + rmtree cleanup | py_compile + headless smoke PASS (save/load round-trip, path under mkdtemp dir) |
| #5 | tools/controller_integration_smoke.py:871 | `tempfile.mktemp(suffix="_smoke_ach_l.json")` | `_secure_temp_path("_smoke_ach_l.json")` | py_compile + headless smoke PASS (load-side board) |
| #6 | tools/controller_integration_smoke.py:512 | `tempfile.mktemp(suffix="_smoke_ach_d.json")` | `_secure_temp_path("_smoke_ach_d.json")` | py_compile + headless smoke PASS (determinism board) |
| #7 | tests/test_controller.py:561 | `tempfile.mktemp(suffix="_ctrl_stash_save.json")` | `tempfile.mkdtemp()` + `addCleanup(shutil.rmtree)` + `os.path.join(tmpdir, "ctrl_stash_save.json")` | py_compile + unittest 33/33 OK (its own test passes) |
