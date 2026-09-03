#!/usr/bin/env python
# tools/scene_capture_smoke.py -- Phase 7 Plan 07-19 headless round-trip proof
# for tools/scene_capture.py (user request 2026-08-30).
#
# Mirrors tools/scene_template_smoke.py structure:
#   * pure pymol.cmd.* script (NO Qt), run headlessly via
#       bash tools/run_headless.sh tools/scene_capture_smoke.py
#     (or from the repo root:
#       timeout 90 cmd.exe /c "C:\src\run-conda-pymol.bat -cq
#       tools\scene_capture_smoke.py")
#   * Gotcha #1: the process ALWAYS exits 0 through run-conda-pymol.bat
#     (`call conda deactivate` overwrites %ERRORLEVEL%; PyMOL swallows
#     exceptions) -- the ^SMOKE_RESULT: PASS stdout sentinel is the ONLY
#     verdict (tools/run_headless.sh greps it; the last line of THIS file).
#   * Gotcha #2: __file__ resolves to the pymol package's __init__.py in a
#     PyMOL-run script, so paths derive from os.getcwd() (= repo root when
#     the harness runs with cwd=repo-root).
#   * Gotcha #6: pymol.finish_launching() before any cmd.* call.
#
# PROOF SHAPE: build a scripted scene via direct cmd.* calls (the emitter is
# READ-ONLY -- the scene state is the input fixture), then run
# scene_capture.capture_scene(cmd) and pin the emitted op sequence with
# assertions. The named-selection mapping is pinned to the EMPIRICALLY
# OBSERVED branch (tmp/07-19-probe.py OBS1, PyMOL 2.5.0): get_type(<named
# selection>) returns the type tag 'selection' (querying.py:1199) -- the
# defining expression is NOT recoverable -- so the PINNED branch is the
# NOT-CAPTURED fallback: NO select_focus op, NO zoom op, and the exact camera
# rides home in the single Phase-10-flagged set_view entry. The OBS prints
# below record which path fired on every run.
#
# The scripted scene: load the bundled _smoke.pdb fixture as probe_obj ->
# show_as sticks -> color cyan (NOT in the 5-name game palette -- forces the
# get_color_tuple -> set_color+color rgb branch; get_color_index("hero_cyan")
# == -1 in a fresh session so there is no palette collision) -> uniform label
# "HERO" (quoted-string expression form) -> named selection focus_sele ->
# zoom focus_sele.
#
# Verdict: grep ^SMOKE_RESULT: PASS in stdout (NOT $?).

import sys
import os

# Gotcha #2/#3/#4: cwd=repo root when run via the harness; insert cwd (and
# tools/ -- where scene_capture.py lives) explicitly as belt-and-suspenders
# so this script is robust if sys.path lacks ''.
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))

import pymol
from pymol import cmd

# Gotcha #6: complete PyMOL startup before any cmd.* call.
pymol.finish_launching()

import scene_capture  # tools/scene_capture.py (sys.path above)

FAILS = []


def check(name, ok, detail=""):
    # type: (str, bool, str) -> None
    """Print a SMOKE: PASS|FAIL line and record failures for the final sentinel."""
    print("SMOKE: {0} {1} {2}".format("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILS.append(name)


# =========================================================================
# Stage 0 -- build the scripted scene (direct cmd.* calls; the emitter only
# READS this state).
# =========================================================================
try:
    scene_path = os.path.join(os.getcwd(), "rpg", "data", "assets",
                              "bundled", "_smoke.pdb")
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(scene_path, "probe_obj")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("sticks", "probe_obj")
    # src: tmp/pymol-src/modules/pymol/querying.py:851 cmd.get_color_index
    cyan_idx = cmd.get_color_index("cyan")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (cyan is
    # NOT in the 5-name palette -> forces the set_color+color rgb branch)
    cmd.color("cyan", "probe_obj")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (quoted-
    # string expression form -> uniform label text "HERO")
    cmd.label("probe_obj", '"HERO"')
    # src: tmp/pymol-src/modules/pymol/selecting.py:48 cmd.select
    cmd.select("focus_sele", "probe_obj and name C1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom
    cmd.zoom("focus_sele")
    # Expected rgb for the applied color (the emitter is read-only, so the
    # session is identical before/after capture).
    # src: tmp/pymol-src/modules/pymol/querying.py:825 cmd.get_color_tuple
    expected_rgb = [float(v) for v in cmd.get_color_tuple(cyan_idx)]
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_atoms = cmd.count_atoms("probe_obj")
    check("t0_scene_built", n_atoms == 3, "atoms={0}".format(n_atoms))
except Exception as e:
    check("t0_exception", False, repr(e))

# =========================================================================
# Stage 1 -- run the emitter (READ-ONLY) and split the returned entries.
# =========================================================================
ops = []
notes = []
try:
    entries = scene_capture.capture_scene(cmd)
    ops = [e for e in entries if isinstance(e, dict)]
    notes = [e for e in entries if isinstance(e, str)]
    print("OBS emitted op sequence: {0}".format(
        [o.get("op") for o in ops]))
    print("OBS emitted comment lines ({0}):".format(len(notes)))
    for n in notes:
        print("OBS   {0}".format(n))
except Exception as e:
    check("t1_capture_exception", False, repr(e))

fallback_path = not any(o.get("op") == "select_focus" for o in ops)
print("OBS select_focus mapping path: {0}".format(
    "NOT-CAPTURED fallback (pinned: get_type returns the type tag only,"
    " tmp/07-19-probe.py OBS1)" if fallback_path
    else "recoverable -> select_focus emitted"))

# The ONLY ops the frozen vocabulary permits (molops.py:140-170 dispatch +
# the one Phase-10-flagged set_view).
ALLOWED_OPS = frozenset(("set_color", "show_as", "color", "show", "label",
                         "select_focus", "zoom", "set_view"))

# =========================================================================
# Stage 2 -- the pinned assertions (>=6; each via check()).
# =========================================================================

# 1. Replay-side ops never emitted (load/hide_all bring objects in / wipe
#    the scene -- the engine's on_enter owns them).
op_names = [o.get("op") for o in ops]
check("c1_no_load_no_hide_all",
      bool(ops) and not any(n in ("load", "hide_all") for n in op_names),
      "ops={0}".format(op_names))

# 2. show_as sticks on probe_obj (the scripted base rep).
sa = [o for o in ops if o.get("op") == "show_as"]
check("c2_show_as_sticks_probe_obj",
      len(sa) == 1 and sa[0].get("target") == "probe_obj"
      and sa[0].get("args", {}).get("rep") == "sticks",
      "show_as={0}".format(sa))

# 3. set_color + color rgb pair (cyan is NOT in the named palette):
#    rgb == get_color_tuple of the applied color, exactly 3 floats, and the
#    color op consumes the set_color-generated name.
sc = [o for o in ops if o.get("op") == "set_color"]
co = [o for o in ops if o.get("op") == "color"]
sc_rgb = sc[0].get("args", {}).get("rgb") if len(sc) == 1 else None
check("c3_set_color_color_rgb_pair",
      len(sc) == 1 and len(co) == 1
      and isinstance(sc_rgb, list) and len(sc_rgb) == 3
      and sc_rgb == expected_rgb
      and co[0].get("args", {}).get("color")
      == sc[0].get("args", {}).get("name"),
      "set_color={0} expected_rgb={1}".format(sc, expected_rgb))

# 4. label with the BARE-STRING text (molops.py:164-170 wraps it as the
#    quoted expression on dispatch).
lb = [o for o in ops if o.get("op") == "label"]
check("c4_label_bare_string_hero",
      len(lb) == 1 and lb[0].get("args", {}).get("text") == "HERO",
      "label={0}".format(lb))

# 5. PINNED select_focus branch (observed on PyMOL 2.5.0, tmp/07-19-probe.py
#    OBS1): get_type(<selection>) returns the type tag 'selection' -- the
#    defining expression is NOT recoverable -- so NO select_focus op is
#    emitted and a NOT-CAPTURED comment names focus_sele instead.
nc_sel = [n for n in notes
          if n.startswith("# NOT CAPTURED") and "focus_sele" in n]
check("c5_select_focus_fallback_pinned",
      fallback_path and len(nc_sel) >= 1,
      "fallback={0} matching_notes={1}".format(fallback_path, nc_sel))

# 6. zoom semantics under the pinned fallback: NO zoom op (a zoom referencing
#    a selection the replay never creates would be an invented op) and the
#    camera NOT-CAPTURED comment is present (the exact camera rides home in
#    set_view). Under a future recoverable branch the pinned assertion flips
#    to: exactly one zoom op with args.sele == "focus_sele".
zoom_ops = [o for o in ops if o.get("op") == "zoom"]
nc_zoom = [n for n in notes if n.startswith("# NOT CAPTURED")
           and "zoom" in n and "set_view" in n]
if fallback_path:
    check("c6_zoom_fallback_camera_via_set_view",
          len(zoom_ops) == 0 and len(nc_zoom) >= 1,
          "zoom_ops={0} matching_notes={1}".format(zoom_ops, nc_zoom))
else:
    check("c6_zoom_follows_recovered_focus",
          len(zoom_ops) == 1
          and zoom_ops[0].get("args", {}).get("sele") == "focus_sele",
          "zoom_ops={0}".format(zoom_ops))

# 7. exactly ONE set_view entry; args.view = a list of 18 numbers (the
#    Phase-10 flag; the camera round-trips exactly).
sv = [o for o in ops if o.get("op") == "set_view"]
view = sv[0].get("args", {}).get("view") if len(sv) == 1 else None
check("c7_single_set_view_18_numbers",
      len(sv) == 1 and isinstance(view, list) and len(view) == 18
      and all(isinstance(v, (int, float)) and not isinstance(v, bool)
              for v in view),
      "set_view={0}".format(sv))

# 8. no invented ops: every emitted op is in the frozen vocabulary.
check("c8_no_invented_ops",
      bool(ops) and all(n in ALLOWED_OPS for n in op_names),
      "ops={0}".format(op_names))

# 9. the full PINNED emission order for this scene (deterministic grouping:
#    set_color defs -> show_as -> color -> label, then the trailing
#    set_view; no show/zoom/select_focus ops under this scene's observed
#    branches).
check("c9_pinned_emission_order",
      op_names == ["set_color", "show_as", "color", "label", "set_view"],
      "ops={0}".format(op_names))

# --- Final verdict via STDOUT SENTINEL (NOT exit code -- the bat always
# returns 0). The sentinel is the ONLY verdict and MUST be the last line.
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
