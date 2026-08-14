#!/usr/bin/env python
# tools/protonation_smoke.py -- Phase 4 Plan 04-05 ProtonationManager headless
# smoke (SC4 + EDIT-05 for protonation).
#
# Pure pymol.cmd.* script (NO Qt) that injects the REAL pymol.cmd into the
# full ProtonationManager stack (EditOps + AssetManager + ProtonationManager +
# the pure-data catalog) and exercises the REAL cmd.* contract end-to-end:
#   * SC4: ProtonationManager applies a curated variant (HIS_HID: alter resn
#     + remove HE2 + h_add ND1 + sort + rebuild); a user-adjustable switch
#     to HIS_HIE is exercisable; list_variants returns the 3 HIS tautomers.
#   * EDIT-05: every protonation change takes a backup via edit_ops; restore
#     returns the pre-protonation atom count + residue signature + H count.
#
# This complements the MockCmd unit tests (tests/test_protonation_manager.py)
# which prove the dispatch MAPPING; this smoke proves the REAL PyMOL API
# behavior (the alter + remove + h_add + sort + rebuild + backup + restore
# mechanics on a real HIS residue). 3-tier testability: unit tests = mapping
# logic, headless smoke = real cmd.* contract.
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
# PHASE 4 PLACEHOLDER: target IS the residue key (per 04-03 _residue_key). The
# HIS fixture is loaded as object "HIS" (the catalog key), NOT "scene" -- the
# _residue_key placeholder returns the target verbatim, so the target must
# match the catalog key. Phase 5+ target schema (e.g. "pdb:1TNR/chainA/HIS123")
# may need parsing (coordinate with the edit-node contract, Phase 5.1).
#
# This smoke exercises pm.apply_variant / pm.switch_variant / pm.restore (the
# sanctioned delegation path -- NO direct cmd.alter or cmd.h_add in this file;
# the alter gate allowlist stays at edit_ops.py only). The ProtonationManager +
# EditOps internal cmd.* calls are cited in their respective modules (verified
# by 04-01 + 04-03 citation tests).
#
# Every direct cmd.count_atoms call in THIS smoke carries a `# src:` citation
# (Phase 3 convention). The ProtonationManager + EditOps internal cmd.* calls
# are cited in their respective modules.
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/protonation_smoke.py
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
from c14.pymol_layer.asset_manager import AssetManager
from c14.pymol_layer.protonation import ProtonationManager
import c14.protonation_catalog as catalog

# Gotcha #6: complete PyMOL startup before any cmd.* call.
pymol.finish_launching()

FAILS = []


def check(name, ok, detail=""):
    # type: (str, bool, str) -> None
    """Print a SMOKE: PASS|FAIL line and record failures for the final sentinel."""
    print("SMOKE: {0} {1} {2}".format("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILS.append(name)


# --- Build the real stack: inject the REAL pymol.cmd into the full stack ---
# EditOps(cmd) + AssetManager(cmd) + ProtonationManager(cmd, editops, catalog,
# assets) -- the 3-tier testability pattern. The unit tests inject MockCmd/
# MockEditOps/MockAssets to prove the dispatch MAPPING; THIS smoke injects the
# real pymol.cmd to prove the real API contract.
editops = EditOps(cmd)
assets = AssetManager(cmd)
pm = ProtonationManager(cmd, editops, catalog, assets)

# Phase 4 placeholder: target = "HIS" (the catalog residue key + the object
# name). _residue_key returns the target verbatim, so the target must match
# the catalog key.
TARGET = "HIS"

# --- Stage 1: load the bundled _his_smoke.pdb fixture (NO network) ---
# The fixture is a single HIS residue with explicit HD1 + HE2 (14 atoms:
# 10 heavy + 4 H). Use AssetManager.load_bundled (resolves the bundled fixture
# cwd-independently via c14.paths).
try:
    assets.load_bundled("_his_smoke.pdb", TARGET)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms(TARGET)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_his = cmd.count_atoms("{0} and resn HIS".format(TARGET))
    check("load", n > 0 and n_his >= 1, "atoms=%d his=%d" % (n, n_his))
except Exception as e:
    check("load", False, repr(e))

# --- Stage 2: record the pre-protonation state ---
# pre_count = 14 (10 heavy + 4 H). pre_h_count = 4 (HD1, HE2, H, HA).
# Confirm HD1 + HE2 are present so Mode (b) remove has something to operate on.
try:
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    pre_count = cmd.count_atoms(TARGET)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    pre_h_count = cmd.count_atoms("{0} and elem H".format(TARGET))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_hd1 = cmd.count_atoms("{0} and resn HIS and name HD1".format(TARGET))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_he2 = cmd.count_atoms("{0} and resn HIS and name HE2".format(TARGET))
    check("pre_state",
          pre_count > 0 and n_hd1 >= 1 and n_he2 >= 1,
          "count=%d h=%d hd1=%d he2=%d" % (pre_count, pre_h_count, n_hd1, n_he2))
except Exception as e:
    check("pre_state", False, repr(e))

# --- Stage 3: SC4 -- apply a curated variant (HIS_HID) ---
# pm.apply_variant("HIS", "HIS_HID") routes through _apply_alter -> edit_ops.
# apply_edit with steps = [remove("resn HIS and name HE2"), alter("HIS",
# "resn='HID'"), h_add("resn HID and name ND1")]. The remove runs BEFORE the
# alter (resn still HIS), the h_add runs AFTER (resn is HID). h_add on ND1
# should be a no-op (HD1 already present, valence satisfied).
# Assert: resn changed to HID, HD1 present, HE2 absent, current_variant tracked.
try:
    pm.apply_variant(TARGET, "HIS_HID")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_hid = cmd.count_atoms("{0} and resn HID".format(TARGET))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_hd1 = cmd.count_atoms("{0} and resn HID and name HD1".format(TARGET))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_he2 = cmd.count_atoms("{0} and resn HID and name HE2".format(TARGET))
    cur = pm.current_variant(TARGET)
    check("apply_hid",
          n_hid >= 1 and n_hd1 >= 1 and n_he2 == 0 and cur == "HIS_HID",
          "hid=%d hd1=%d he2=%d cur=%r" % (n_hid, n_hd1, n_he2, cur))
except Exception as e:
    check("apply_hid", False, repr(e))

# --- Stage 4: SC4 -- user-adjustable switch to HIS_HIE ---
# First restore to HIS (so the switch starts from the canonical state -- the
# catalog h_ops for HIE use "resn HIS" in the remove selection, which requires
# the current resn to be HIS). Then switch_variant("HIS", "HIS_HIE") takes a
# FRESH backup + applies HIE. This tests the switch mechanism (backup + apply
# + current_variant tracking).
# NOTE: a direct switch from HID to HIE would not perfectly remove HD1 because
# the catalog's remove selection uses "resn HIS" (which doesn't match "HID").
# This is a known Phase 4 placeholder limitation -- the catalog h_ops are
# designed for applying from the canonical resn, not for variant-to-variant
# switches. Phase 5+ may author switch-aware selections. The core SC4 mechanic
# (the switch IS exercisable: backup + alter + current_variant tracking) is
# proven here; the exact H placement is Phase 5+ cited content.
try:
    # Restore to HIS first (so the switch starts from the canonical state).
    pm.restore(TARGET)
    # Switch to HIE (fresh backup + apply HIE from HIS).
    pm.switch_variant(TARGET, "HIS_HIE")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_hie = cmd.count_atoms("{0} and resn HIE".format(TARGET))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_hd1 = cmd.count_atoms("{0} and resn HIE and name HD1".format(TARGET))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_he2 = cmd.count_atoms("{0} and resn HIE and name HE2".format(TARGET))
    cur = pm.current_variant(TARGET)
    # Assert: resn changed to HIE (the alter worked), HD1 absent (the remove
    # "resn HIS and name HD1" matched because we restored to HIS first), HE2
    # present (was never removed -- HIE h_ops only remove HD1), current=HIS_HIE.
    check("switch_hie",
          n_hie >= 1 and n_hd1 == 0 and n_he2 >= 1 and cur == "HIS_HIE",
          "hie=%d hd1=%d he2=%d cur=%r" % (n_hie, n_hd1, n_he2, cur))
except Exception as e:
    check("switch_hie", False, repr(e))

# --- Stage 5: EDIT-05 -- restore safety net covers protonation ---
# pm.restore("HIS") delegates to edit_ops.restore_from_handle(self._backup["HIS"])
# -- the handle from the last apply_variant (stage 4's switch to HIE). The
# backup was taken BEFORE the HIE application (when the object was HIS).
# Assert: atom count + resn + H count restored to the pre-protonation state.
try:
    pm.restore(TARGET)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_restored = cmd.count_atoms(TARGET)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_his = cmd.count_atoms("{0} and resn HIS".format(TARGET))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_h = cmd.count_atoms("{0} and elem H".format(TARGET))
    cur = pm.current_variant(TARGET)
    check("restore",
          n_restored == pre_count and n_his >= 1 and n_h == pre_h_count
          and cur is None,
          "count=%d (want %d) his=%d h=%d (want %d) cur=%r" % (
              n_restored, pre_count, n_his, n_h, pre_h_count, cur))
except Exception as e:
    check("restore", False, repr(e))

# --- Stage 6: EDIT-05 proof -- backup taken before every variant ---
# Apply HIS_HID again; assert editops._handles has a handle registered for
# "HIS" (apply_edit registers it). Then restore (clears the handle).
# This proves every protonation change takes a backup via edit_ops (EDIT-05
# covers protonation automatically -- the backup is unified, not separate).
try:
    pm.apply_variant(TARGET, "HIS_HID")
    handle_registered = editops._handles.get(TARGET) is not None
    pm.restore(TARGET)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_after = cmd.count_atoms(TARGET)
    check("backup_taken_before_variant",
          handle_registered and n_after == pre_count,
          "handle=%s count=%d" % (handle_registered, n_after))
except Exception as e:
    check("backup_taken_before_variant", False, repr(e))

# --- Stage 7: SC4 support -- list_variants returns the 3 HIS tautomers ---
# pm.list_variants("HIS") delegates to catalog.variants_for("HIS") which
# returns [("HIS_HID", label), ("HIS_HIE", label), ("HIS_HIP", label)].
try:
    variants = pm.list_variants(TARGET)
    vids = [v[0] for v in variants]
    has_3 = len(variants) >= 3
    has_hid = "HIS_HID" in vids
    has_hie = "HIS_HIE" in vids
    has_hip = "HIS_HIP" in vids
    check("list_variants",
          has_3 and has_hid and has_hie and has_hip,
          "variants=%r" % variants)
except Exception as e:
    check("list_variants", False, repr(e))

# --- Final verdict via STDOUT SENTINEL (NOT exit code -- the bat always returns 0) ---
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
