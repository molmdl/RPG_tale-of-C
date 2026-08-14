#!/usr/bin/env python
# tools/asset_smoke.py -- Phase 3 Plan 03-02 AssetManager headless smoke.
#
# Pure pymol.cmd.* script (NO Qt) that exercises the REAL AssetManager
# (injecting the real pymol.cmd) to verify the actual cmd.load/cmd.fetch
# calls + count_atoms post-conditions against the PyMOL 2.5.0 API. This
# complements the MockCmd unit tests (tests/test_asset_manager.py) which
# prove the dispatch/path/arg LOGIC; this smoke proves the real API contract
# (3-tier testability: unit tests = logic, headless smoke = real cmd.*).
#
# CRITICAL CONTRACT RULES (from 03-RESEARCH.md, reused from Plan 03-01):
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
# STAGES:
#   * load_bundled (NO network -- uses the committed Plan 01 fixture
#     c14/data/assets/bundled/_smoke.pdb): MUST pass (count_atoms > 0).
#   * fetch_pubchem (NETWORK -- PubChem CID 2244 aspirin): if offline, reports
#     failure but does NOT block the plan (the unit tests prove the logic).
#     Also asserts the file landed in the downloaded dir (cwd-independence --
#     SC #2, Pitfall 5b mitigation).
#   * fetch_pdb (NETWORK, non-critical -- PDB 1crn crambin): confirms the
#     type='pdb' mitigation; reports failure if offline.
#
# Every direct cmd.* call in THIS smoke (the count_atoms post-conditions)
# carries a `# src:` citation. The AssetManager's internal cmd.load/cmd.fetch
# calls are cited in c14/pymol_layer/asset_manager.py (verified by the unit
# test test_citations_present_in_source).
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/asset_smoke.py
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
from c14.pymol_layer.asset_manager import AssetManager

# Gotcha #6: complete PyMOL startup before any cmd.* call.
pymol.finish_launching()

FAILS = []


def check(name, ok, detail=""):
    # type: (str, bool, str) -> None
    """Print a SMOKE: PASS|FAIL line and record failures for the final sentinel."""
    print("SMOKE: {0} {1} {2}".format("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILS.append(name)


# --- load_bundled (NO network -- uses the committed Plan 01 fixture) ---
# AssetManager.load_bundled resolves the ABSOLUTE bundled path via
# c14.paths.data_path (cwd-independent) and calls cmd.load; the count_atoms
# post-condition (inside load_bundled) raises if the object is empty. This
# stage MUST pass -- it uses the committed _smoke.pdb fixture, no network.
try:
    am = AssetManager(cmd)
    am.load_bundled("_smoke.pdb", "bund")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("bund")
    check("load_bundled", n > 0, "atoms=%d" % n)
except Exception as e:
    check("load_bundled", False, repr(e))

# --- fetch_pubchem (NETWORK -- PubChem CID 2244 aspirin) ---
# AssetManager.fetch_pubchem forces type="cid", async_=0, path=<abs downloaded
# dir> (Pitfall 5 mitigations). On success: count_atoms > 0 AND the file lands
# at <downloaded>/cid_2244.sdf (cwd-independence -- SC #2). On offline/network
# failure: report but do NOT hard-fail the whole smoke (the unit tests prove
# the dispatch/path/arg logic; this stage confirms the real cmd.fetch when
# network is available).
try:
    am.fetch_pubchem("2244", "asp")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("asp")
    check("fetch_pubchem", n > 0, "atoms=%d" % n)
except Exception as e:
    check("fetch_pubchem", False, "NETWORK? %r" % e)

# --- fetch_pubchem_file_landed (cwd-independence -- SC #2, Pitfall 5b) ---
# cmd.fetch lands the file at path/cid_<code>.sdf (importing.py:1181). Assert
# the file exists at the ABSOLUTE downloaded dir regardless of cwd. If the
# fetch above failed (offline), this may still pass if the file was
# previously cached (cmd.fetch skips download if the file exists --
# importing.py:1211-1213, free idempotent cache).
try:
    f = os.path.join(
        str(c14.paths.data_path("data", "assets", "downloaded")),
        "cid_2244.sdf",
    )
    check("fetch_pubchem_file_landed", os.path.exists(f), "path=%s" % f)
except Exception as e:
    check("fetch_pubchem_file_landed", False, repr(e))

# --- fetch_pdb (NETWORK, non-critical -- PDB 1crn crambin) ---
# AssetManager.fetch_pdb forces type="pdb" (NOT the CIF default -- Pitfall
# 5a), async_=0, path=<abs downloaded dir>. Confirms the type='pdb' mitigation
# works for PDB proteins too (03-RESEARCH.md Open Question #1). Non-critical:
# reports failure if offline but does NOT block the plan.
try:
    am.fetch_pdb("1crn", "crn")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n = cmd.count_atoms("crn")
    check("fetch_pdb", n > 0, "atoms=%d" % n)
except Exception as e:
    check("fetch_pdb", False, "NETWORK? (non-critical) %r" % e)

# --- Final verdict via STDOUT SENTINEL (NOT exit code -- the bat always returns 0) ---
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
