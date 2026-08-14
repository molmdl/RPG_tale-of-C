#!/usr/bin/env python
# tools/api_sanity_smoke.py -- Phase 3 api-sanity headless smoke (Plan 03-01 GATE).
#
# Pure pymol.cmd.* script (NO Qt) that exercises every cmd.* call the game will
# use, with post-condition assertions, and prints a SMOKE_RESULT: PASS|FAIL
# stdout sentinel as the LAST line. The bash harness (tools/run_headless.sh)
# greps for ^SMOKE_RESULT: PASS to determine the verdict.
#
# CRITICAL CONTRACT RULES (from 03-RESEARCH.md):
#   * Gotcha #1: the process ALWAYS exits 0 through run-conda-pymol.bat
#     (`call conda deactivate` overwrites %ERRORLEVEL%; PyMOL swallows
#     exceptions). So we CANNOT use sys.exit/raise/cmd.quit to signal failure --
#     the SMOKE_RESULT: stdout sentinel is the ONLY reliable verdict.
#   * Gotcha #2: __file__ in a PyMOL-run script resolves to the pymol package's
#     __init__.py, NOT this script's path. So we use os.getcwd() (= repo root
#     when run with cwd=repo-root) + import c14.paths (whose __file__ IS
#     correct) to locate bundled fixtures.
#   * Gotcha #6: pymol.finish_launching() completes PyMOL startup before any
#     cmd.* call.
#
# Every cmd.* call carries a `# src: tmp/pymol-src/modules/pymol/<file>.py:<line>
# cmd.<name>` comment on the line directly above it -- the source-citation
# convention established by this plan (success criterion #4). Line numbers are
# pinned to PyMOL 2.5.0 (verified 2026-08-14 against tmp/pymol-src/modules/pymol/).
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/api_sanity_smoke.py
# Verdict: grep ^SMOKE_RESULT: PASS in the captured stdout (NOT $?).

import sys
import os

# Gotcha #2/#3/#4: cwd=repo root when run via the harness, so os.getcwd() is the
# workspace and `import c14` works (sys.path includes '' = cwd). Insert cwd
# explicitly as belt-and-suspenders so this script is robust if sys.path lacks ''.
sys.path.insert(0, os.getcwd())

import pymol
from pymol import cmd
import c14.paths

# Gotcha #6: complete PyMOL startup before any cmd.* call.
pymol.finish_launching()

FAILS = []


def check(name, ok, detail=""):
    # type: (str, bool, str) -> None
    """Print a SMOKE: PASS|FAIL line and record failures for the final sentinel."""
    print("SMOKE: {0} {1} {2}".format("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILS.append(name)


# --- load (bundled fixture) ---
try:
    p = str(c14.paths.data_path("data", "assets", "bundled", "_smoke.pdb"))
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(p, "smk")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("smk")
    check("load", n > 0, "atoms=%d" % n)
except Exception as e:
    check("load", False, repr(e))

# --- fetch cid (NETWORK) -- report but do NOT hard-fail the whole smoke if offline ---
# Pitfall 5: offline is a real deployment concern; the non-network stages still
# validate. cmd.fetch skips download if the file already exists (idempotent cache).
try:
    d = str(c14.paths.data_path("data", "assets", "downloaded"))
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    # src: tmp/pymol-src/modules/pymol/importing.py:1323 cmd.fetch
    cmd.fetch("2244", "asp", type="cid", async_=0, path=d)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("asp")
    check("fetch_cid", n > 0, "atoms=%d" % n)
except Exception as e:
    check("fetch_cid", False, "NETWORK? %r" % e)

# --- fetch pdb (NETWORK, non-critical -- 03-RESEARCH.md Open Question #1) ---
# Confirms the type='pdb', async_=0, path= mitigation works for PDB too. Does
# NOT hard-fail (small PDB fetch; may be slow/offline).
try:
    d = str(c14.paths.data_path("data", "assets", "downloaded"))
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    # src: tmp/pymol-src/modules/pymol/importing.py:1323 cmd.fetch
    cmd.fetch("1crn", "crn", type="pdb", async_=0, path=d)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("crn")
    check("fetch_pdb", n > 0, "atoms=%d" % n)
except Exception as e:
    check("fetch_pdb", False, "NETWORK? (non-critical) %r" % e)

# --- show_rep: hide everything then show sticks; assert rep visible via `rep` keyword ---
try:
    # src: tmp/pymol-src/modules/pymol/viewing.py:568 cmd.hide
    cmd.hide("everything", "smk")
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show
    cmd.show("sticks", "smk")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("smk & rep sticks")
    check("show_rep", n > 0, "rep-sticks=%d" % n)
except Exception as e:
    check("show_rep", False, repr(e))

# --- show_as (bonus): turns ON the rep AND off all others atomically -- cleanest for scene setup ---
try:
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("lines", "smk")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("smk & rep lines")
    check("show_as", n > 0, "rep-lines=%d" % n)
except Exception as e:
    check("show_as", False, repr(e))

# --- select: named selection of the atom named C1 (the smoke fixture's required atom) ---
try:
    # src: tmp/pymol-src/modules/pymol/selecting.py:48 cmd.select
    cmd.select("sc1", "smk and name C1")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("sc1")
    check("select", n == 1, "n=%d" % n)
except Exception as e:
    check("select", False, repr(e))

# --- zoom (no-crash; no headless-assertable post-condition -- modifies view) ---
try:
    # src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom
    cmd.zoom("smk")
    check("zoom", True)
except Exception as e:
    check("zoom", False, repr(e))

# --- color (no-crash; no headless-assertable post-condition) ---
try:
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("green", "smk")
    check("color", True)
except Exception as e:
    check("color", False, repr(e))

# --- create_backup: DEFAULT args (source_state=0, target_state=0 = copy ALL states) ---
# NOT 1,1 -- the 03-RESEARCH.md empirical correction. create(backup,src,1,1)
# copies ONLY state 1 -> loses states 2+ (incomplete backup for multi-state
# objects). create(obj,obj) self-copy is DESTRUCTIVE. The working backup is
# default-args cmd.create (matches ARCHITECTURE.md:304).
try:
    # src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete
    cmd.delete("bak")
    # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create
    cmd.create("bak", "smk")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    bak_n = cmd.count_atoms("bak")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    smk_n = cmd.count_atoms("smk")
    check("create_backup", bak_n == smk_n, "bak=%d smk=%d" % (bak_n, smk_n))
except Exception as e:
    check("create_backup", False, repr(e))

# --- delete: MUST use the `?` prefix post-condition ---
# 03-RESEARCH.md §2 cmd.delete: bare count_atoms("smk") on a DELETED object
# RAISES CmdException('Invalid selection name'); count_atoms("?smk") returns 0
# (safe). The `?` is PyMOL's existing-objects-only selector prefix.
try:
    # src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete
    cmd.delete("smk")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("?smk")
    check("delete", n == 0, "post=?smk->%d" % n)
except Exception as e:
    check("delete", False, repr(e))

# --- Final verdict via STDOUT SENTINEL (NOT exit code -- the bat always returns 0) ---
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
