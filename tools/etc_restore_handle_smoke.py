#!/usr/bin/env python
# tools/etc_restore_handle_smoke.py -- Phase 7 Plan 07-09: the batch-C (07-04
# Decision 6a / research OQ#4) HEADLESS restore-handle semantics verification
# for the ETC Template-3 restoration arc.
#
# Question under test (07-04-SUMMARY.md Decision 6a + 07-RESEARCH-etc-endings.md
# OQ#4): on a restoration branch node, does MolAction(op="restore") retrieve
# the WT backup (taken when the SOURCE node's pre-edit on_enter applied the
# disease mutation) -- or the player-edit's own backup (taken by the branch
# node's reverse-mutation edit, which fires FIRST in 05.3 Template 3's
# sequence [edit -> restore])?
#
# Code reading (rpg/pymol_layer/edit_ops.py): apply_edit registers
# _handles[object_name] on EVERY call (line 148), so a second apply_edit on
# the same object OVERWRITES the first handle; restore() (line 217-227) reads
# the most recent handle; and take_backup (line 199-203) DELETES the previous
# "_bak_<obj>" object before re-creating it. This smoke determines the
# behavior EMPIRICALLY on the real PyMOL cmd (the 3-tier testability
# contract: unit tests prove mapping, headless smokes prove the real API).
#
# Scenarios (on the bundled _edit_smoke.pdb: resi 1 = ALA, resi 2 = GLY; we
# cast ALA as the "WT identity" at resi 1 and GLY as the "disease allele"):
#   SCENARIO A -- 05.3 Template-3 literal order, branch node on_enter =
#     [edit(reverse mutation), restore]:
#       1. point_mutation(resi 1 -> GLY)  # pre-edit disease application
#       2. point_mutation(resi 1 -> ALA)  # branch node's reverse-mutation edit
#       3. restore("enz_a")               # Template 3's restore op
#     Verdict = the resn at resi 1 after step 3.
#   SCENARIO B -- 05.3 §2 option (ii) restore-ONLY shortcut, branch node
#     on_enter = [restore] (no intervening edit):
#       1. point_mutation(resi 1 -> GLY)  # pre-edit disease application
#       2. restore("enz_b")
#     Verdict = the resn at resi 1 after step 2.
#
# The SMOKE_RESULT sentinel reports MECHANICAL completion (loads/edits/restore
# executed without exceptions and atom counts intact). The analytical outcome
# is reported on OQ4_* lines -- either outcome is a valid finding:
#   OQ4_VERDICT: PASS            # restore retrieves the WT backup in BOTH orders
#   OQ4_VERDICT: FAIL-TEMPLATE3  # edit-then-restore self-undoes (A returns
#                                # the disease state) while restore-only works
# A FAIL-TEMPLATE3 finding is a FLAG for plans 14/17 (they own the branch-node
# on_enter authoring); engine surgery is OUT of Phase 7 scope, so this smoke
# only documents the semantics.
#
# CRITICAL CONTRACT RULES (reused from tools/edit_smoke.py):
#   * Gotcha #1: the process ALWAYS exits 0 through run-conda-pymol.bat --
#     the SMOKE_RESULT stdout sentinel is the ONLY reliable verdict.
#   * Gotcha #2: __file__ resolves to the pymol package's __init__.py -- use
#     os.getcwd() + rpg.paths to locate the bundled fixture.
#   * Gotcha #6: pymol.finish_launching() before any cmd.* call.
#
# Every direct cmd.* call in THIS file carries a `# src:` citation (Phase 3
# convention). EditOps-internal cmd.* calls are cited in edit_ops.py.
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/etc_restore_handle_smoke.py
# Verdict: grep ^SMOKE_RESULT: PASS in the captured stdout (NOT $?).

import os
import sys

# Gotcha #2/#3/#4: cwd = repo root when run via the harness.
sys.path.insert(0, os.getcwd())

import pymol
from pymol import cmd
import rpg.paths
from rpg.pymol_layer.edit_ops import EditOps

pymol.finish_launching()  # Gotcha #6

FAILS = []


def check(name, ok, detail=""):
    print("CHECK {0}: {1} {2}".format(name, "PASS" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(name)


def residue_resn(obj, resi):
    """Read the resn of one residue via cmd.iterate (the stored-list form)."""
    stored = type("S", (), {"list": []})()
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
    # (space= is MANDATORY -- without it the expression namespace cannot see
    # the stored object; mirrors edit_ops.py:268-273.)
    cmd.iterate("{0} and resi {1}".format(obj, resi),
                "stored.list.append(resn)", space={"stored": stored})
    return sorted(set(stored.list))


# --- Stage 1: load the fixture twice (independent objects) ---
FIXTURE = rpg.paths.data_path("data", "assets", "bundled", "_edit_smoke.pdb")
# src: tmp/pymol-src/modules/pymol/commanding.py:606 cmd.load
cmd.load(FIXTURE, "enz_a")
# src: tmp/pymol-src/modules/pymol/commanding.py:606 cmd.load
cmd.load(FIXTURE, "enz_b")
# src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
n_a = cmd.count_atoms("enz_a")
# src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
n_b = cmd.count_atoms("enz_b")
check("load_fixture_x2", n_a == 17 and n_b == 17,
      "enz_a={0} enz_b={1}".format(n_a, n_b))
check("fixture_wt_identity", residue_resn("enz_a", 1) == ["ALA"],
      "resi1={0}".format(residue_resn("enz_a", 1)))

eo_a = EditOps(cmd)
eo_b = EditOps(cmd)

# --- Stage 2: SCENARIO A -- Template-3 literal order [edit, restore] ---
# 2a. Pre-edit disease application (the SOURCE node's on_enter under
#     approach (a)): backup1 = WT (ALA) is registered in eo_a._handles.
try:
    h1 = eo_a.point_mutation("enz_a", "enz_a and resi 1", "GLY")
    check("A_preedited_disease_applied", residue_resn("enz_a", 1) == ["GLY"],
          "resi1={0}".format(residue_resn("enz_a", 1)))
except Exception as e:
    h1 = None
    check("A_preedited_disease_applied", False, repr(e))

# 2b. Branch node's reverse-mutation edit (fires FIRST in Template 3):
#     backup2 = the DISEASE state; it OVERWRITES eo_a._handles["enz_a"] AND
#     take_backup deletes the previous "_bak_enz_a" object.
try:
    h2 = eo_a.point_mutation("enz_a", "enz_a and resi 1", "ALA")
    check("A_reverse_edit_applied", residue_resn("enz_a", 1) == ["ALA"],
          "resi1={0}".format(residue_resn("enz_a", 1)))
except Exception as e:
    h2 = None
    check("A_reverse_edit_applied", False, repr(e))

# 2c. Template 3's restore op -- WHICH state comes back?
a_resn = None
try:
    eo_a.restore("enz_a")
    a_resn = residue_resn("enz_a", 1)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    check("A_restore_atom_count_intact", cmd.count_atoms("enz_a") == 17,
          "count={0}".format(cmd.count_atoms("enz_a")))
except Exception as e:
    check("A_restore_executes", False, repr(e))

print("OQ4_SCENARIO_A (Template-3 literal [edit, restore]) restored resn: "
      "{0}".format(a_resn))
if a_resn is not None:
    if a_resn == ["ALA"]:
        print("OQ4_SCENARIO_A_RESULT: PASS -- restore retrieved the WT backup")
    else:
        print("OQ4_SCENARIO_A_RESULT: FAIL -- restore retrieved the "
              "player-edit's own backup (the disease state); the reverse "
              "mutation was UNDONE")

# --- Stage 3: SCENARIO B -- restore-ONLY shortcut (05.3 §2 option ii) ---
b_resn = None
try:
    eo_b.point_mutation("enz_b", "enz_b and resi 1", "GLY")
    pre = residue_resn("enz_b", 1)
    check("B_preedited_disease_applied", pre == ["GLY"], "resi1={0}".format(pre))
    eo_b.restore("enz_b")
    b_resn = residue_resn("enz_b", 1)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    check("B_restore_atom_count_intact", cmd.count_atoms("enz_b") == 17,
          "count={0}".format(cmd.count_atoms("enz_b")))
except Exception as e:
    check("B_restore_executes", False, repr(e))

print("OQ4_SCENARIO_B (restore-ONLY shortcut) restored resn: {0}".format(b_resn))
if b_resn is not None:
    if b_resn == ["ALA"]:
        print("OQ4_SCENARIO_B_RESULT: PASS -- restore retrieved the WT backup")
    else:
        print("OQ4_SCENARIO_B_RESULT: FAIL -- restore did not retrieve the WT")

# --- Final verdicts ---
# MECHANICAL sentinel: the smoke ran to completion (loads/edits/restores all
# executed; atom counts intact). NOT an OQ4 verdict.
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))

# ANALYTICAL OQ#4 verdict (the reason this smoke exists):
if a_resn == ["ALA"] and b_resn == ["ALA"]:
    print("OQ4_VERDICT: PASS -- restore retrieves the WT pre-edit backup in "
          "both orderings; Template-3 [edit, restore] is safe as written")
elif a_resn == ["ALA"] and b_resn is not None:
    print("OQ4_VERDICT: PASS-WITH-NOTE -- restore-only works; see scenario A")
elif b_resn == ["ALA"] and a_resn is not None:
    print("OQ4_VERDICT: FAIL-TEMPLATE3 -- restore-only retrieves the WT "
          "backup, but the Template-3 [edit, restore] order self-undoes "
          "(the reverse mutation is reverted by restore). FLAG for plans "
          "14/17: ETC restoration branch nodes must use the restore-ONLY "
          "form (or place restore BEFORE any same-object edit); engine "
          "surgery is out of Phase 7 scope")
else:
    print("OQ4_VERDICT: INCONCLUSIVE -- see CHECK failures above")
