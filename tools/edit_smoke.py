#!/usr/bin/env python
# tools/edit_smoke.py -- Phase 4 Plan 04-05 EditOps headless smoke (SC1+SC2).
#
# Pure pymol.cmd.* script (NO Qt) that injects the REAL pymol.cmd into EditOps
# and exercises the REAL cmd.* contract end-to-end:
#   * SC1 (alter->sort trap mitigation): a post-edit `byres` selection returns
#     the expected atoms (NO silent corruption from stale atom ordering).
#   * SC2 (backup/restore round-trip): for each edit type (point_mutation,
#     substrate_remove_group, protonation_change), backup-before-edit +
#     restore returns the object to its pre-edit atom count + residue
#     signature.
#   * BONUS (Pitfall 9 backup independence): mutating the live object does NOT
#     corrupt the backup (cmd.create made an independent copy).
#
# This complements the MockCmd unit tests (tests/test_edit_ops.py) which prove
# the dispatch MAPPING; this smoke proves the REAL PyMOL API behavior (the
# alter->sort trap mitigation, the backup/restore round-trip, the backup
# independence). 3-tier testability: unit tests = mapping logic, headless
# smoke = real cmd.* contract.
#
# CRITICAL CONTRACT RULES (from 03-RESEARCH.md, reused from molops_smoke.py):
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
# This smoke exercises editops.point_mutation / substrate_remove_group /
# protonation_change (the sanctioned apply_edit path -- NO bare cmd.alter in
# this file; the alter gate allowlist stays at edit_ops.py only). The EditOps
# internal cmd.* calls are cited in c14/pymol_layer/edit_ops.py (verified by
# 04-01's test_citations_present_in_source).
#
# Every direct cmd.count_atoms / cmd.load call in THIS smoke carries a `# src:`
# citation (Phase 3 convention). The EditOps internal cmd.* calls are cited in
# edit_ops.py.
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/edit_smoke.py
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
from c14.pymol_layer.edit_ops import EditOps

# Gotcha #6: complete PyMOL startup before any cmd.* call.
pymol.finish_launching()

FAILS = []


def check(name, ok, detail=""):
    # type: (str, bool, str) -> None
    """Print a SMOKE: PASS|FAIL line and record failures for the final sentinel."""
    print("SMOKE: {0} {1} {2}".format("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILS.append(name)


# --- Build the real stack: inject the REAL pymol.cmd into EditOps ---
# EditOps(cmd) -- the 3-tier testability pattern. The unit tests
# (tests/test_edit_ops.py) inject a MockCmd to prove the dispatch MAPPING;
# THIS smoke injects the real pymol.cmd to prove the real API contract.
editops = EditOps(cmd)

# --- Stage 1: load the bundled _edit_smoke.pdb fixture (NO network) ---
# The fixture is a 2-residue ALA-GLY peptide (17 atoms). Use c14.paths to
# resolve the bundled fixture path cwd-independently (Gotcha #2: __file__ in
# a PyMOL-run script is wrong; c14.paths.__file__ IS correct).
fixture_path = str(c14.paths.data_path("data", "assets", "bundled", "_edit_smoke.pdb"))
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(fixture_path, "pep")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_pep = cmd.count_atoms("pep")
    check("load", n_pep > 0, "atoms=%d" % n_pep)
except Exception as e:
    check("load", False, repr(e))

# --- Stage 2: collect the pre-edit residue signature + atom count ---
# The pre-edit signature is a sorted list of (chain, resi, resn) tuples, ONE
# PER ATOM (cmd.iterate runs per-atom). For the 17-atom ALA-GLY fixture:
# 10 x ('A','1','ALA') + 7 x ('A','2','GLY'). The unique-residue SET is
# {('A','1','ALA'), ('A','2','GLY')}; the list length == atom count (17).
try:
    pre_count = cmd.count_atoms("pep")
    pre_sig = editops._collect_residue_signature("pep")
    unique_residues = sorted(set(pre_sig))
    check("pre_signature",
          unique_residues == [("A", "1", "ALA"), ("A", "2", "GLY")]
          and len(pre_sig) == pre_count,
          "count=%d unique=%r" % (pre_count, unique_residues))
except Exception as e:
    check("pre_signature", False, repr(e))

# --- Stage 3: apply a point mutation (SC1 + SC2 backup) ---
# point_mutation("pep", "pep and resi 1", "GLY") -> apply_edit -> backup ->
# alter resn='GLY' on resi 1 -> sort -> rebuild. The handle is registered in
# editops._handles for restore() lookup.
handle = None
try:
    handle = editops.point_mutation("pep", "pep and resi 1", "GLY")
    check("apply_point_mutation", handle is not None, "handle=%r" % handle)
except Exception as e:
    check("apply_point_mutation", False, repr(e))

# --- Stage 4: SC1 -- post-edit byres selection returns expected atoms ---
# The alter->sort trap: WITHOUT cmd.sort, a post-edit byres selection might
# return stale atoms. apply_edit ALWAYS calls cmd.sort + cmd.rebuild, so byres
# should return the correct atoms. Assert:
#   * count_atoms("byres (pep and resi 1)") == 10 (the 10 atoms of resi 1)
#   * count_atoms("pep and resi 1 and resn GLY") > 0 (the swap took)
#   * count_atoms("pep and resi 1 and resn ALA") == 0 (the old resn is gone)
try:
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_byres = cmd.count_atoms("byres (pep and resi 1)")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_gly = cmd.count_atoms("pep and resi 1 and resn GLY")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_ala = cmd.count_atoms("pep and resi 1 and resn ALA")
    check("sc1_byres_post_edit",
          n_byres == 10 and n_gly > 0 and n_ala == 0,
          "byres=%d gly=%d ala=%d" % (n_byres, n_gly, n_ala))
except Exception as e:
    check("sc1_byres_post_edit", False, repr(e))

# --- Stage 5: SC2 -- backup/restore round-trip (point_mutation) ---
# restore_from_handle(handle) -> delete pep -> create pep from _bak_pep ->
# sort -> rebuild -> verify atom count + residue signature. Assert the object
# is restored to its pre-edit state (17 atoms, ALA-GLY signature).
try:
    editops.restore_from_handle(handle)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_restored = cmd.count_atoms("pep")
    sig_restored = editops._collect_residue_signature("pep")
    check("sc2_restore_round_trip",
          n_restored == pre_count and sig_restored == pre_sig,
          "count=%d (want %d) sig=%r (want %r)" % (n_restored, pre_count, sig_restored, pre_sig))
except Exception as e:
    check("sc2_restore_round_trip", False, repr(e))

# --- Stage 6: BONUS -- backup independence (Pitfall 9) ---
# After a fresh take_backup, mutate the LIVE object (point_mutation). The
# backup (_bak_pep) should be UNCHANGED -- cmd.create made an independent
# copy; mutating the live object didn't corrupt the backup. Assert the backup
# still has the pre-edit atom count + residue signature (ALA at resi 1), while
# the live object has the mutation (GLY at resi 1). Then restore the live
# object.
try:
    # Take a fresh manual backup (does NOT register in _handles).
    editops.take_backup("pep")
    # Mutate the live object (apply_edit takes its OWN backup = overwrites
    # _bak_pep with the pre-edit state, then alters pep).
    handle2 = editops.point_mutation("pep", "pep and resi 1", "GLY")
    # The backup should be the pre-edit state (17 atoms, ALA-GLY), NOT the
    # mutated state (GLY-GLY). This proves create made an independent copy.
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_bak = cmd.count_atoms("_bak_pep")
    sig_bak = editops._collect_residue_signature("_bak_pep")
    sig_live = editops._collect_residue_signature("pep")
    check("backup_independence",
          n_bak == pre_count and sig_bak == pre_sig and sig_live != pre_sig,
          "bak_count=%d (want %d) bak_sig=%r live_sig=%r" % (n_bak, pre_count, sig_bak, sig_live))
    # Restore the live object (uses the handle registered by apply_edit).
    editops.restore("pep")
except Exception as e:
    check("backup_independence", False, repr(e))

# --- Stage 7: SC2 -- substrate_remove_group round-trip ---
# Remove the CA atom of GLY at resi 2 -> count decreases. Restore -> count
# restored. Proves SC2 covers substrate edits, not just point mutations.
try:
    handle3 = editops.substrate_remove_group("pep", "pep and resi 2 and name CA")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_after_remove = cmd.count_atoms("pep")
    editops.restore_from_handle(handle3)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_after_restore = cmd.count_atoms("pep")
    check("substrate_remove_group",
          n_after_remove < pre_count and n_after_restore == pre_count,
          "after_remove=%d (want <%d) after_restore=%d (want %d)" % (
              n_after_remove, pre_count, n_after_restore, pre_count))
except Exception as e:
    check("substrate_remove_group", False, repr(e))

# --- Stage 8: SC2 -- protonation_change via EditOps round-trip ---
# A resn rename (ALA -> HID at resi 1) via the protonation_change edit type,
# exercised through EditOps directly (the full ProtonationManager path is the
# protonation_smoke). Assert the resn changed + restore returns the original.
try:
    handle4 = editops.protonation_change("pep", "pep and resi 1", "HID")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_hid = cmd.count_atoms("pep and resi 1 and resn HID")
    editops.restore_from_handle(handle4)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_restored2 = cmd.count_atoms("pep")
    sig_restored2 = editops._collect_residue_signature("pep")
    check("protonation_change_via_editops",
          n_hid > 0 and n_restored2 == pre_count and sig_restored2 == pre_sig,
          "hid=%d restored=%d sig=%r" % (n_hid, n_restored2, sig_restored2))
except Exception as e:
    check("protonation_change_via_editops", False, repr(e))

# --- Final verdict via STDOUT SENTINEL (NOT exit code -- the bat always returns 0) ---
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
