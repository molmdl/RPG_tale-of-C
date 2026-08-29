#!/usr/bin/env python
# tools/molops_deferred_dispatch_smoke.py -- Phase 6 Plan 06-01 headless
# regression smoke for the 4 deferred molops dispatches + the load
# target-prefix fallback.
#
# Pure pymol.cmd.* script (NO Qt) that dispatches the 6-call hero-highlight
# sequence + an align + a target-prefix load VIA molops.apply(MolAction(...))
# (the per-action dispatch contract from 02-04) and asserts the SAME post-
# conditions the DIRECT-cmd smokes already proved (hero_highlight_smoke.py +
# wt_align_smoke.py). It is the regression target: after the dispatches land
# in molops.py (06-01 Task 1), dispatching the same sequence via molops.apply
# MUST yield the same results calling cmd.* directly got.
#
# Why this smoke exists (the 3-tier testability pattern):
#   * Unit tests (Task 2, tests/test_molops.py) prove the per-op dispatch
#     MAPPING (MockCmd records the right cmd.* name+args). They do NOT exercise
#     the REAL cmd.* contract.
#   * THIS smoke injects the REAL pymol.cmd into MolOps and proves the 4 new
#     dispatches (set_color/label/set/align) + the load target-prefix fallback
#     reproduce the smokes' post-conditions against the real PyMOL 2.5.0 API.
#   * The direct-cmd smokes (hero_highlight_smoke 29/29 + wt_align_smoke 8/8 +
#     scene_template_smoke 37/37) PROVED the cmd.* MECHANISMS. This smoke proves
#     the DISPATCH WRAPPERS around those mechanisms are correct (right arg
#     order, right selection composition, no KeyError on the skeleton load form).
#
# This smoke does NOT call cmd.set_color/label/set/super DIRECTLY (that would
# duplicate hero_highlight_smoke.py -- the point is to test the DISPATCH via
# molops.apply). The only direct cmd.* calls are the SETUP (load/create) and
# the POST-CONDITION probes (count_atoms/iterate/iterate_state) -- each cited.
#
# CRITICAL CONTRACT RULES (from 03-RESEARCH.md, reused from hero_highlight +
# wt_align smokes):
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
# Every direct cmd.* call in THIS smoke (the load/create/count_atoms/iterate/
# iterate_state setup + post-condition probes -- NOT the molops.apply calls,
# which are the dispatch under test) carries a `# src:` citation (Phase 3
# convention; line numbers verified against tmp/pymol-src/modules/pymol/).
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/molops_deferred_dispatch_smoke.py
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
from c14.pymol_layer.molops import MolOps
from c14.pymol_layer.asset_manager import AssetManager
from c14.story.model import MolAction

# Gotcha #6: complete PyMOL startup before any cmd.* call.
pymol.finish_launching()

FAILS = []


def check(name, ok, detail=""):
    # type: (str, bool, str) -> None
    """Print a SMOKE: PASS|FAIL line and record failures for the final sentinel."""
    print("SMOKE: {0} {1} {2}".format("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILS.append(name)


def color_name_for(sele):
    # type: (str) -> str
    """Return the PyMOL named color applied to the first atom in `sele`, or None.

    Uses cmd.iterate to read the atom's color INDEX, then maps the index back
    to its NAME via cmd.get_color_indices (RESEARCH-api section A.2 / D.1 /
    Pitfall 4: do NOT assert a hardcoded index -- the index is session-
    allocated; assert the NAME). The collector key `cidx` is chosen to NOT
    collide with any atom-property name (RESEARCH-api section F Pitfall 1: a
    collector named `color` would shadow the atom's `color` field and raise
    `AttributeError: 'int' object has no attribute 'append'`).

    Copied verbatim from tools/hero_highlight_smoke.py:84-103 (the helper is
    pure cmd.iterate + cmd.get_color_indices; no molops dependency).
    """
    cidx = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate  (read atom props; collector `cidx` avoids the `color` collision)
    cmd.iterate(sele, "cidx.append(color)", space={"cidx": cidx})
    if not cidx:
        return None
    # src: tmp/pymol-src/modules/pymol/querying.py:843 cmd.get_color_indices  (all=1 -> ALL colors incl. standard extended like gray80; all=0 omits gray80/gray10..gray90 -- empirically gray80 idx=4236 is only in all=1)
    idx2name = {i: n for (n, i) in cmd.get_color_indices(all=1)}
    return idx2name.get(cidx[0])


class MockAssets(object):
    """Records every AssetManager delegation WITHOUT touching the network.

    Mirrors tests/test_molops.py:83-105 MockAssets (load_bundled /
    fetch_pubchem / fetch_pdb record their salient args). Used in Stage 5 to
    prove the `pdb:` target-prefix parses to fetch_pdb WITHOUT a real network
    fetch (the mock intercepts; no cmd.fetch call). Pure Python, no cmd.
    """

    def __init__(self):
        self.calls = []

    def load_bundled(self, filename, object_name):
        self.calls.append(("load_bundled", filename, object_name))
        return object_name

    def fetch_pubchem(self, cid, object_name, kind="cid"):
        self.calls.append(("fetch_pubchem", cid, object_name, kind))
        return object_name

    def fetch_pdb(self, code, object_name, ftype="pdb"):
        self.calls.append(("fetch_pdb", code, object_name, ftype))
        return object_name


# =========================================================================
# Stage 1: setup. Load the bundled _smoke.pdb (3-atom C1/O1/C2) as `mol` and
# extract the hero (name C1) as a dedicated 1-atom object `hero_atom` via
# cmd.create (hero_highlight_smoke.py Stage 1 Strategy A). The hero-highlight
# sequence (Stage 2) is then dispatched VIA molops.apply (NOT cmd.* directly).
# =========================================================================
smoke_path = str(c14.paths.data_path("data", "assets", "bundled", "_smoke.pdb"))
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load  (load a structure file into a named object)
    cmd.load(smoke_path, "mol")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    check("setup_load_mol", cmd.count_atoms("mol") == 3,
          "atoms=%d" % cmd.count_atoms("mol"))

    # Extract the hero as its OWN single-atom object (RESEARCH-api section
    # C.1: create("hero_atom", "mol and name C1") makes a 1-atom object).
    # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create  (new object from a selection)
    cmd.create("hero_atom", "mol and name C1")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    check("setup_hero_atom_1", cmd.count_atoms("hero_atom") == 1,
          "atoms=%d" % cmd.count_atoms("hero_atom"))
except Exception as e:
    check("setup_load_mol", False, repr(e))
    check("setup_hero_atom_1", False, repr(e))

# The molops instance for Stages 2-4 (the 4 new ops + align -- NO AssetManager
# needed; only `load` requires assets, and that's Stage 5 with its own MolOps).
molops = MolOps(cmd)

# =========================================================================
# Stage 2: dispatch the 6-call hero-highlight sequence VIA molops.apply
# (05.4-CONVENTION.md:237-243 -- the FROZEN OQ-3 OVERRIDE sequence). This is
# the SAME sequence hero_highlight_smoke.py applied via direct cmd.* -- here
# it goes through the per-action dispatch (the 06-01 wrappers), proving the
# dispatches reproduce the direct-cmd smoke's post-conditions.
# =========================================================================
# Stage 3 (post-conditions) is folded into this try block (mirrors
# hero_highlight_smoke.py Stage 1: dispatch + assert in one try/except).
try:
    # --- The 6-call hero-highlight sequence via molops.apply (NOT cmd.*) ---
    # Step 1: set_color (the 5.4 hero_cyan palette; idempotent named-RGB define).
    molops.apply(MolAction(
        "set_color", None, {"name": "hero_cyan", "rgb": [0.0, 0.75, 0.75]}))
    # Step 2: show_as sticks (base rep -- ALL atoms get sticks).
    molops.apply(MolAction(
        "show_as", "hero_atom", {"rep": "sticks", "sele": "hero_atom"}))
    # Step 3: color hero_cyan on elem C (ALL carbons cyan -- the hero is one of them).
    molops.apply(MolAction(
        "color", "hero_atom", {"color": "hero_cyan", "sele": "hero_atom and elem C"}))
    # Step 4: show spheres ON TOP of sticks (ball-and-stick; NOT show_as).
    molops.apply(MolAction(
        "show", "hero_atom", {"rep": "spheres", "sele": "hero_atom"}))
    # Step 5: set sphere_scale 0.3 (SMALL elegant sphere, NOT the giant default 1.0).
    molops.apply(MolAction(
        "set", "hero_atom", {"name": "sphere_scale", "value": 0.3, "sele": "hero_atom"}))
    # Step 6: label "YOU" (the player-facing identity label -- OQ-4 OVERRIDE).
    molops.apply(MolAction(
        "label", "hero_atom", {"sele": "hero_atom", "text": "YOU"}))

    # --- Post-conditions (same as hero_highlight_smoke.py Stage 1) ---
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (exactly one atom)
    check("hero_count_1", cmd.count_atoms("hero_atom") == 1,
          "atoms=%d" % cmd.count_atoms("hero_atom"))

    elems = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate  (read elem; collector `elems` avoids collision)
    cmd.iterate("hero_atom", "elems.append(elem)", space={"elems": elems})
    check("hero_elem_C", elems == ["C"], "elems=%r" % elems)

    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (the `rep <name>` keyword = headless "rep visible" primitive)
    check("hero_rep_spheres",
          cmd.count_atoms("hero_atom and rep spheres") == 1,
          "rep-spheres=%d" % cmd.count_atoms("hero_atom and rep spheres"))

    # Ball-and-stick: the hero has BOTH sticks AND spheres.
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (rep keyword -- sticks assigned too)
    check("hero_rep_sticks",
          cmd.count_atoms("hero_atom and rep sticks") == 1,
          "rep-sticks=%d" % cmd.count_atoms("hero_atom and rep sticks"))

    check("hero_color_hero_cyan",
          color_name_for("hero_atom") == "hero_cyan",
          "color=%r" % color_name_for("hero_atom"))

    lbls = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate  (read label text; collector `lbls` avoids collision)
    cmd.iterate("hero_atom", "lbls.append(label)", space={"lbls": lbls})
    check("hero_label_YOU", lbls == ["YOU"], "labels=%r" % lbls)
except Exception as e:
    check("hero_count_1", False, repr(e))
    check("hero_elem_C", False, repr(e))
    check("hero_rep_spheres", False, repr(e))
    check("hero_rep_sticks", False, repr(e))
    check("hero_color_hero_cyan", False, repr(e))
    check("hero_label_YOU", False, repr(e))

# =========================================================================
# Stage 4: dispatch an align VIA molops.apply (05.3-CONVENTION.md section 6 --
# the WT-aligned structure load op deferred from 5.3). Load the existing 05.3
# fixtures (`_wt_align_mut.pdb` as `mut` + `_wt_align_wt.pdb` as `wt`), then
# dispatch `MolAction("align", "wt", {"reference":"mut","method":"super",
# "align_sele":"name CA"})` and assert the mobile (`wt`) MOVED (the dispatch
# called cmd.super with mobile=`wt and name CA`, ref=`mut and name CA`).
# Mirrors wt_align_smoke.py Stage 4 (capture pre/post x via iterate_state --
# x/y/z are only in the iterate_state namespace, NOT cmd.iterate).
# =========================================================================
mut_path = str(c14.paths.data_path("data", "assets", "bundled", "_wt_align_mut.pdb"))
wt_path = str(c14.paths.data_path("data", "assets", "bundled", "_wt_align_wt.pdb"))
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load  (the mutant fixture: 17-atom ALA-GLY)
    cmd.load(mut_path, "mut")
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load  (the WT fixture: 14-atom GLY-GLY, offset ~5 A in x)
    cmd.load(wt_path, "wt")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    check("align_load_mut", cmd.count_atoms("mut") > 0,
          "mut=%d" % cmd.count_atoms("mut"))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    check("align_load_wt", cmd.count_atoms("wt") > 0,
          "wt=%d" % cmd.count_atoms("wt"))

    # Capture the WT CA coordinate BEFORE align. NOTE: x/y/z are only
    # available in iterate_state (NOT cmd.iterate -- which exposes
    # name/chain/resi/resn but NOT coordinates); iterate_state(1, ...) reads
    # the first state's coords into the space namespace (wt_align_smoke.py).
    before = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1578 cmd.iterate_state  (x/y/z available here, NOT in cmd.iterate)
    cmd.iterate_state(1, "wt and name CA", "before.append((x, y, z))",
                      space={"before": before})
    before_x = before[0][0] if before else None

    # Dispatch the align via molops.apply (the 06-01 align wrapper). The
    # dispatch composes mobile="wt and name CA" + ref="mut and name CA" and
    # calls cmd.super(mobile, ref) (mobile MOVED, ref FIXED). The return
    # (RMSD tuple) is discarded by the dispatch; we verify via the
    # post-condition that the mobile MOVED.
    molops.apply(MolAction(
        "align", "wt",
        {"reference": "mut", "method": "super", "align_sele": "name CA"}))

    # Capture the WT CA coordinate AFTER align + assert it CHANGED (proves
    # the dispatch called super with the right arg order -- mobile MOVED).
    after = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1578 cmd.iterate_state  (x/y/z available here, NOT in cmd.iterate)
    cmd.iterate_state(1, "wt and name CA", "after.append((x, y, z))",
                      space={"after": after})
    after_x = after[0][0] if after else None
    check("align_moved_mobile",
          before_x is not None and after_x is not None
          and abs(after_x - before_x) > 1e-6,
          "before_x=%r after_x=%r" % (before_x, after_x))
except Exception as e:
    check("align_load_mut", False, repr(e))
    check("align_load_wt", False, repr(e))
    check("align_moved_mobile", False, repr(e))

# =========================================================================
# Stage 5: dispatch a load via the target-prefix fallback (the 06-01
# load-branch extension). Proves the skeleton's
# `{"op":"load","target":"_smoke.pdb","args":{"object":"hero2"}}` form works
# against the real API, NOT a KeyError (Blocker 1 fix).
#
# Two sub-checks:
#   (a) bare-filename target with a REAL AssetManager -> load_bundled actually
#       loads the bundled fixture into `hero2` (count_atoms > 0). Uses the
#       real API (bundled, no network).
#   (b) `pdb:1XXX` target with a MOCK AssetManager -> the prefix parses to
#       fetch_pdb WITHOUT a network call (the mock intercepts; records
#       ("fetch_pdb", "1XXX", "o", "pdb")). NO real cmd.fetch (CI-safe).
# =========================================================================
# (a) bare-filename path with the REAL AssetManager.
try:
    real_assets = AssetManager(cmd)
    molops_load = MolOps(cmd, real_assets)
    # Dispatch the bare-filename load via molops.apply (the 06-01 target-prefix
    # fallback -- no source/file/code/cid keys; target="_smoke.pdb" parses to
    # load_bundled). This MUST NOT raise KeyError (the Blocker 1 fix).
    molops_load.apply(MolAction("load", "_smoke.pdb", {"object": "hero2"}))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (the bundled fixture loaded into hero2)
    check("load_target_bundled_real",
          cmd.count_atoms("hero2") > 0,
          "hero2=%d" % cmd.count_atoms("hero2"))
except Exception as e:
    check("load_target_bundled_real", False, repr(e))

# (b) pdb: prefix path with a MOCK AssetManager (NO network).
try:
    mock_assets = MockAssets()
    mock_molops = MolOps(cmd, mock_assets)
    # Dispatch the pdb: prefix load via molops.apply (the 06-01 target-prefix
    # fallback -- target="pdb:1XXX" parses to fetch_pdb with the stripped
    # code "1XXX"). The mock intercepts; NO real cmd.fetch (CI-safe).
    mock_molops.apply(MolAction("load", "pdb:1XXX", {"object": "o"}))
    expected_call = ("fetch_pdb", "1XXX", "o", "pdb")
    ok = (len(mock_assets.calls) == 1 and mock_assets.calls[0] == expected_call)
    check("load_target_pdb_prefix_mock", ok,
          "calls=%r" % (mock_assets.calls,))
except Exception as e:
    check("load_target_pdb_prefix_mock", False, repr(e))

# --- Final verdict via STDOUT SENTINEL (NOT exit code -- the bat always returns 0) ---
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
