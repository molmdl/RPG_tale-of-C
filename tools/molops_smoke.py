#!/usr/bin/env python
# tools/molops_smoke.py -- Phase 3 Plan 03-03 MolOps headless smoke.
#
# Pure pymol.cmd.* script (NO Qt) that exercises the REAL MolOps (injecting
# the real pymol.cmd + real AssetManager) to verify the actual MolAction ->
# cmd.* dispatch sequence + the `rep` keyword "representation visible"
# post-condition (SC #3). This complements the MockCmd/MockAssets unit tests
# (tests/test_molops.py) which prove the per-op dispatch MAPPING; this smoke
# proves the real API contract + the shown-rep post-condition (3-tier
# testability: unit tests = mapping logic, headless smoke = real cmd.*).
#
# CRITICAL CONTRACT RULES (from 03-RESEARCH.md, reused from Plan 03-01/02):
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
# SC #3 CORE SEQUENCE (MUST pass -- uses the committed Plan 01 fixture, NO
# network): queue [hide_all, load(bundled), show(sticks), zoom, color] as
# MolActions and dispatch per-action via molops.apply(a); assert the resulting
# object "scene" has the sticks representation visible
# (count_atoms("scene & rep sticks") > 0 -- the `rep` keyword, empirically
# confirmed in 03-RESEARCH.md section 2) AND is non-empty (count_atoms > 0).
#
# BONUS stages (also reported; wrap in try/except so an unexpected raise does
# not crash the smoke -- they test well-established PyMOL behaviors already
# proven by the api-sanity smoke):
#   * hide_all_cleared: after hide_all + show(sticks), rep lines == 0 (only
#     sticks visible -- confirms hide_all worked; show does NOT turn off
#     other reps).
#   * show_as_atomic: show_as(lines) turns ON lines AND turns OFF sticks
#     atomically (count_atoms("scene & rep lines") > 0 AND
#     count_atoms("scene & rep sticks") == 0).
#   * delete_post: molops.apply(MolAction("delete","scene")) ->
#     count_atoms("?scene") == 0 (the ?-prefix post-condition -- 03-RESEARCH.md
#     section 2 cmd.delete; bare count_atoms on a deleted object RAISES).
#     This is the LAST stage (destroys the scene object).
#
# Every direct cmd.count_atoms call in THIS smoke carries a `# src:` citation.
# The MolOps internal cmd.* calls are cited in c14/pymol_layer/molops.py
# (verified by the unit test test_citations_present_in_source).
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/molops_smoke.py
# Verdict: grep ^SMOKE_RESULT: PASS in the captured stdout (NOT $?).

import sys
import os

# Gotcha #2/#3/#4: cwd=repo root when run via the harness, so os.getcwd() is
# the workspace and `import c14` works (sys.path includes '' = cwd). Insert
# cwd explicitly as belt-and-suspenders so this script is robust if sys.path
# lacks ''.
sys.path.insert(0, os.getcwd())

import pymol
from pymol import cmd
import c14.paths
from c14.story.model import MolAction
from c14.pymol_layer.asset_manager import AssetManager
from c14.pymol_layer.molops import MolOps

# Gotcha #6: complete PyMOL startup before any cmd.* call.
pymol.finish_launching()

FAILS = []


def check(name, ok, detail=""):
    # type: (str, bool, str) -> None
    """Print a SMOKE: PASS|FAIL line and record failures for the final sentinel."""
    print("SMOKE: {0} {1} {2}".format("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILS.append(name)


# --- Build the real stack: inject the REAL pymol.cmd + real AssetManager ---
# MolOps(cmd, asset_manager) -- the 3-tier testability pattern. The unit tests
# (tests/test_molops.py) inject a MockCmd/MockAssets to prove the dispatch
# MAPPING; THIS smoke injects the real pymol.cmd to prove the real API contract.
am = AssetManager(cmd)
molops = MolOps(cmd, am)

# --- SC #3 CORE SEQUENCE: queue the MolAction list + dispatch per-action ---
# The 02-04 per-action contract: molops.apply(action) takes ONE MolAction per
# call (the engine emits `for action in actions: sink(action)`; the Phase 4+
# controller calls molops.apply(action) per action). We dispatch the queued
# list one action at a time -- exactly as the Phase 4+ controller will.
# This sequence uses the committed bundled fixture (NO network) so it MUST
# pass regardless of network availability.
actions = [
    MolAction("hide_all"),
    MolAction("load", "_smoke", {"source": "bundled", "file": "_smoke.pdb", "object": "scene"}),
    MolAction("show", "scene", {"rep": "sticks"}),
    MolAction("zoom", "scene"),
    MolAction("color", "scene", {"color": "green"}),
]
try:
    for a in actions:
        molops.apply(a)
except Exception as e:
    check("molops_dispatch_sequence", False, "dispatch raised: %r" % e)

# --- molops_scene_loaded: the object is non-empty (count_atoms > 0) ---
try:
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("scene")
    check("molops_scene_loaded", n > 0, "atoms=%d" % n)
except Exception as e:
    check("molops_scene_loaded", False, repr(e))

# --- molops_scene_rep_visible: SC #3 -- the sticks representation is visible ---
# The `rep <name>` selection keyword selects atoms with that representation
# enabled. After hide_all + show(sticks), the "scene" object has sticks
# visible -- count_atoms("scene & rep sticks") > 0. This is the SC #3
# "representation visible" headless assertion (empirically confirmed in
# 03-RESEARCH.md section 2; the api-sanity smoke already proved the rep keyword
# returns 3 for a 3-atom object).
try:
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("scene & rep sticks")
    check("molops_scene_rep_visible", n > 0, "rep-sticks=%d" % n)
except Exception as e:
    check("molops_scene_rep_visible", False, repr(e))

# --- BONUS: molops_hide_all_cleared (rep lines == 0 after hide_all + show sticks) ---
# hide_all turns OFF every rep; show(sticks) turns ON only sticks. So after the
# core sequence, lines should NOT be visible (count_atoms("scene & rep lines")
# == 0). This confirms hide_all worked -- show does NOT turn off other reps,
# so without hide_all the default lines rep would still be visible.
try:
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("scene & rep lines")
    check("molops_hide_all_cleared", n == 0, "rep-lines=%d" % n)
except Exception as e:
    check("molops_hide_all_cleared", False, repr(e))

# --- BONUS: molops_show_as_atomic (show_as turns ON lines AND OFF sticks) ---
# show_as is the cleanest "set the scene's representation" for the game: it
# turns ON the named rep AND turns OFF all others atomically. After
# show_as("lines"), count_atoms("scene & rep lines") > 0 AND
# count_atoms("scene & rep sticks") == 0 (sticks turned OFF by show_as).
try:
    molops.apply(MolAction("show_as", "scene", {"rep": "lines"}))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_lines = cmd.count_atoms("scene & rep lines")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_sticks = cmd.count_atoms("scene & rep sticks")
    check(
        "molops_show_as_atomic",
        n_lines > 0 and n_sticks == 0,
        "rep-lines=%d rep-sticks=%d" % (n_lines, n_sticks),
    )
except Exception as e:
    check("molops_show_as_atomic", False, repr(e))

# --- BONUS: molops_delete_post (delete op + ?-prefix post-condition) ---
# molops.apply(MolAction("delete","scene")) -> cmd.delete("scene"). The
# post-condition MUST use the ?-prefix: count_atoms("?scene") == 0 (safe).
# Bare count_atoms("scene") on a DELETED object RAISES CmdException
# (03-RESEARCH.md section 2 cmd.delete). This is the LAST stage -- it
# destroys the scene object.
try:
    molops.apply(MolAction("delete", "scene"))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("?scene")
    check("molops_delete_post", n == 0, "post=?scene->%d" % n)
except Exception as e:
    check("molops_delete_post", False, repr(e))

# --- Final verdict via STDOUT SENTINEL (NOT exit code -- the bat always returns 0) ---
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
