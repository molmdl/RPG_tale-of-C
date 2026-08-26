#!/usr/bin/env python
# tools/wt_align_smoke.py -- Phase 5.3 Plan 02 WT-aligned structure load
# headless prototype (SC2).
#
# Pure pymol.cmd.* script (NO Qt) that exercises the WT-aligned-load
# MECHANISM on placeholder fixtures: load mutant -> apply correct reverse-
# mutation edit -> load WT -> align WT(mobile) onto edited enzyme(fixed) via
# cmd.super -> verify finite RMSD + matched atoms + mobile coords changed +
# substructure-scoped align. Proves the MECHANISM, NOT real science
# (placeholder coords are arbitrary; a real RMSD-quality gate is Phase 7
# content).
#
# This smoke calls cmd.super DIRECTLY (NOT via molops.apply). The
# op="align" molops dispatch is deferred to Phase 6 per convention
# 05.3-CONVENTION.md section 6 / section 8 Q3. This smoke proves the
# MECHANISM the dispatch will eventually wrap (the 3-tier testability
# pattern: unit tests = mapping logic, headless smoke = real cmd.* contract).
#
# CRITICAL CONTRACT RULES (from 03-RESEARCH.md, reused from edit_smoke.py):
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
# Every direct cmd.* call in THIS smoke carries a `# src:` citation (Phase 3
# convention; line numbers verified against tmp/pymol-src/modules/pymol/).
# The EditOps internal cmd.* calls are cited in c14/pymol_layer/edit_ops.py.
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/wt_align_smoke.py
# Verdict: grep ^SMOKE_RESULT: PASS in the captured stdout (NOT $?).

import sys
import os
import math

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
# EditOps(cmd) -- the 3-tier testability pattern. The unit tests inject a
# MockCmd to prove the dispatch MAPPING; THIS smoke injects the real
# pymol.cmd to prove the real API contract (mirrors tools/edit_smoke.py).
editops = EditOps(cmd)

# =========================================================================
# Stage 1: load the MUTANT placeholder fixture (the "disease" state).
# The fixture is a 2-residue ALA-GLY peptide (17 atoms). Resi 1 = ALA (the
# "disease" residue); resi 2 = GLY. Use c14.paths to resolve the bundled
# fixture path cwd-independently (Gotcha #2: __file__ in a PyMOL-run script
# is wrong; c14.paths.__file__ IS correct).
# =========================================================================
mut_path = str(c14.paths.data_path("data", "assets", "bundled", "_wt_align_mut.pdb"))
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(mut_path, "mut")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_mut = cmd.count_atoms("mut")
    check("load_mutant", n_mut > 0, "atoms=%d" % n_mut)
except Exception as e:
    check("load_mutant", False, repr(e))

# =========================================================================
# Stage 2: apply the CORRECT reverse-mutation edit (the player's restoration).
# The correct edit reverses the disease: ALA(disease) -> GLY(WT identity) at
# resi 1. This reuses the Phase 4 proven edit path (EditOps.point_mutation).
# =========================================================================
try:
    # The correct edit reverses the disease: ALA(disease) -> GLY(WT identity) at resi 1
    handle = editops.point_mutation("mut", "mut and resi 1", "GLY")
    check("apply_correct_edit", handle is not None, "handle=%r" % handle)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_gly = cmd.count_atoms("mut and resi 1 and resn GLY")
    check("edit_took", n_gly > 0, "resi1 GLY atoms=%d" % n_gly)
except Exception as e:
    check("apply_correct_edit", False, repr(e))
    check("edit_took", False, repr(e))

# NOTE: the live `mut` object still has 17 atoms after the alter (cmd.alter
# changes resn, NOT atom count -- the spurious CB/HB atoms from ALA remain).
# This is the "approximate coordinates" caveat the convention section 5
# text_teaching template documents: the restored model has WT residue
# IDENTITY but approximate GEOMETRY (cmd.alter does NOT repack side chains).
# The WT-aligned load (Stage 4) supplies the experimentally-determined
# geometry as the ground-truth reference.

# =========================================================================
# Stage 3: load the WT placeholder fixture (the "healthy" experimental
# structure). A 2-residue GLY-GLY peptide (14 atoms, no CB). Coords are
# OFFSET ~5 A in x from the mutant's GLY region so cmd.super does real work.
# =========================================================================
wt_path = str(c14.paths.data_path("data", "assets", "bundled", "_wt_align_wt.pdb"))
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(wt_path, "wt")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_wt = cmd.count_atoms("wt")
    check("load_wt", n_wt > 0, "atoms=%d" % n_wt)
except Exception as e:
    check("load_wt", False, repr(e))

# =========================================================================
# Stage 4: align WT (MOBILE, moved) onto the edited enzyme (FIXED, stays) --
# the core restoration-reveal mechanism.
# cmd.super(mobile, target) -- mobile MOVED, target FIXED (convention section
# 4 argument-order gotcha). mobile=`wt` (the WT slides into the edited
# enzyme's frame so the camera doesn't jump); target=`mut` (the edited enzyme
# the player is looking at, stays fixed).
# =========================================================================
# Capture the WT CA coordinate BEFORE align. NOTE: x/y/z are only available
# in iterate_state (NOT cmd.iterate -- which exposes name/chain/resi/resn but
# NOT coordinates); iterate_state(1, ...) reads the first (and only) state's
# coords into the space namespace.
before = []
try:
    # src: tmp/pymol-src/modules/pymol/editing.py:1578 cmd.iterate_state  (x/y/z available here, NOT in cmd.iterate)
    cmd.iterate_state(1, "wt and name CA", "before.append((x, y, z))", space={"before": before})
    before_x = before[0][0] if before else None

    # src: tmp/pymol-src/modules/pymol/fitting.py:242 cmd.super  (mobile MOVED, target FIXED)
    ret = cmd.super("wt", "mut")

    # Verify the return is a finite tuple with matched atoms > 0 (RESEARCH-
    # pymol-align-api section A/D post-condition; ret is a tuple
    # (RMSD, natoms, ...)).
    ok_ret = (isinstance(ret, tuple) and len(ret) >= 2
              and math.isfinite(float(ret[0])) and int(ret[1]) > 0)
    check("super_returns_finite_tuple", ok_ret,
          "type=%s ret[0]=%r ret[1]=%r" % (
              type(ret).__name__,
              ret[0] if isinstance(ret, tuple) and len(ret) > 0 else None,
              ret[1] if isinstance(ret, tuple) and len(ret) > 1 else None))

    # Capture the WT CA coordinate AFTER align + assert it CHANGED (proves
    # transform=1 moved the mobile object). Use iterate_state (NOT iterate)
    # because x/y/z are only in the state namespace -- empirically confirmed:
    # cmd.iterate(..., "x, y, z") raises NameError('x/y/z only available in
    # iterate_state and alter_state'); cmd.iterate_state(1, ...) reads the
    # first (and only) state's coords into the space namespace.
    after = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1578 cmd.iterate_state  (x/y/z available here, NOT in cmd.iterate)
    cmd.iterate_state(1, "wt and name CA", "after.append((x, y, z))", space={"after": after})
    after_x = after[0][0] if after else None
    check("super_moved_mobile",
          before_x is not None and after_x is not None
          and abs(after_x - before_x) > 1e-6,
          "before_x=%r after_x=%r" % (before_x, after_x))
except Exception as e:
    check("super_returns_finite_tuple", False, repr(e))
    check("super_moved_mobile", False, repr(e))

# =========================================================================
# Stage 5: substructure-scoped align (the domain-shift mechanism; convention
# section 4). Re-offset the WT so the scoped align does real work (otherwise
# Stage 4 already aligned it and Stage 5 would be a no-op). Align on `name CA`
# only; transform=1 (default) moves the WHOLE `wt` object (empirically
# confirmed in RESEARCH-pymol-align-api section A.5 / section C).
# =========================================================================
try:
    # Re-offset the WT by +5 A in x so the scoped align does real work.
    # src: tmp/pymol-src/modules/pymol/editing.py:1610 cmd.translate
    cmd.translate([5.0, 0.0, 0.0], "wt")

    # Capture before-scoped coord (reuse the iterate_state pattern -- x/y/z
    # require iterate_state, NOT cmd.iterate; see the Stage 4 NOTE above).
    before_scoped = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1578 cmd.iterate_state
    cmd.iterate_state(1, "wt and name CA", "before_scoped.append((x, y, z))",
                space={"before_scoped": before_scoped})
    before_scoped_x = before_scoped[0][0] if before_scoped else None

    # Run the scoped alignment -- align on `name CA` only; transform=1
    # (default) moves the WHOLE `wt` object.
    # src: tmp/pymol-src/modules/pymol/fitting.py:242 cmd.super  (scoped: mobile MOVED, target FIXED; transform=1 moves whole object)
    ret2 = cmd.super("wt and name CA", "mut and name CA")

    # Verify ret2 is a tuple with matched CA atoms > 0.
    ok_ret2 = (isinstance(ret2, tuple) and len(ret2) >= 2 and int(ret2[1]) > 0)
    check("scoped_super_matched_ca", ok_ret2,
          "ret2[1]=%r" % (ret2[1] if isinstance(ret2, tuple) and len(ret2) > 1 else None))

    # Capture after-scoped coord + assert CHANGED (proves the scoped
    # superposition transformed the whole WT object, not just the matched CA
    # selection -- the domain-shift pedagogical mechanism).
    after_scoped = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1578 cmd.iterate_state
    cmd.iterate_state(1, "wt and name CA", "after_scoped.append((x, y, z))",
                space={"after_scoped": after_scoped})
    after_scoped_x = after_scoped[0][0] if after_scoped else None
    check("scoped_super_moved_whole_wt",
          before_scoped_x is not None and after_scoped_x is not None
          and abs(after_scoped_x - before_scoped_x) > 1e-6,
          "before_scoped_x=%r after_scoped_x=%r" % (before_scoped_x, after_scoped_x))
except Exception as e:
    check("scoped_super_matched_ca", False, repr(e))
    check("scoped_super_moved_whole_wt", False, repr(e))

# --- Final verdict via STDOUT SENTINEL (NOT exit code -- the bat always returns 0) ---
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
