#!/usr/bin/env python
# tools/hero_highlight_smoke.py -- Phase 5.4 Plan 02 C14 hero highlight
# headless prototype (SC1 mechanism).
#
# Pure pymol.cmd.* script (NO Qt) that exercises the hero-highlight MECHANISM
# on placeholder fixtures across the 3 structural cases (hero-alone /
# hero-in-substrate / hero-at-enzyme-cast) + the CO2-shed soul-transfer
# climax. Proves the MECHANISM (select -> count==1 -> elem C -> all-C cyan
# sticks -> hero ball-and-stick small sphere -> label "YOU" -> color-name
# round-trip), NOT real science (placeholder coords are arbitrary; real
# hero-selectors are Phase 7 content).
#
# OQ-3 OVERRIDE design (Plan 04 checkpoint): ALL carbons in the hero-bearing
# molecule are colored hero_cyan sticks (the hero is "one of them" -- a
# carbon among carbons). The hero is distinguished by ball-and-stick (sticks
# + a SMALL sphere, sphere_scale=0.3) + the "YOU" label. Non-carbons keep
# their element colors (NOT dimmed -- the old scoped-dim was REMOVED).
#
# This smoke calls cmd.set_color / cmd.label / cmd.show_as / cmd.show /
# cmd.color / cmd.set DIRECTLY (NOT via molops.apply). The op="set_color" /
# op="label" / op="set" molops dispatches are deferred to Phase 6 per
# convention 05.4-CONVENTION.md section 2.2 / OQ-1. This smoke proves the
# MECHANISM the dispatches will eventually wrap (the 3-tier testability
# pattern: unit tests = mapping logic, headless smoke = real cmd.* contract
# -- mirrors how tools/wt_align_smoke.py calls cmd.super directly per
# 05.3-CONVENTION.md section 6).
#
# CRITICAL CONTRACT RULES (from 03-RESEARCH.md, reused from wt_align_smoke.py):
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
# HERO-IDENTITY ANTI-CONFUSION (from AGENTS.md + PROJECT.md row 107; the
# MANDATORY anti-confusion block -- restated inline at the Stage 4 transfer):
#   The hero is a CARBON ATOM; "C14" is its isotope tracking LABEL, not its
#   fate. The carbon body is shed as CO2; its electrons (the "soul") flow via
#   NADH/FADH2 -> ETC -> ATP. The CO2-shed soul-transfer stages below are a
#   NARRATIVE/VISUAL DEVICE -- they do NOT assert the carbon becomes NADH or
#   ATP (scientifically WRONG). The highlight on the NADH/ATP placeholder
#   represents the ELECTRONS (the soul), not the carbon. C14-decay was DROPPED
#   (PROJECT.md row 108; the sole timescale bad-ending is the cycle-trap).
#
# Every direct cmd.* call in THIS smoke carries a `# src:` citation (Phase 3
# convention; line numbers verified against tmp/pymol-src/modules/pymol/).
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/hero_highlight_smoke.py
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
    """
    cidx = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate  (read atom props; collector `cidx` avoids the `color` collision)
    cmd.iterate(sele, "cidx.append(color)", space={"cidx": cidx})
    if not cidx:
        return None
    # src: tmp/pymol-src/modules/pymol/querying.py:843 cmd.get_color_indices  (all=1 -> ALL colors incl. standard extended like gray80; all=0 omits gray80/gray10..gray90 -- empirically gray80 idx=4236 is only in all=1)
    idx2name = {i: n for (n, i) in cmd.get_color_indices(all=1)}
    return idx2name.get(cidx[0])


# =========================================================================
# Stage 0: define the hero_cyan named color (convention section 2.3 palette +
# section 3.3 step 1). Colorblind-safe cyan [0.0, 0.75, 0.75] (PLACEHOLDER RGB
# pending Phase 7 source approval -- OQ-3 OVERRIDE). Idempotent overwrite
# (re-running on on_enter replay / re-init is safe).
# =========================================================================
# src: tmp/pymol-src/modules/pymol/viewing.py:2107 cmd.set_color  (DEFINE a named RGB color; auto 0-1/0-255 range)
cmd.set_color("hero_cyan", [0.0, 0.75, 0.75])

# Verify the named color round-trips: get_color_index(name) -> index, then
# get_color_indices() -> {index: name}, assert the name round-trips. This is
# the RESEARCH-api section D.3 robustness rule (do NOT assert a hardcoded
# index; assert the NAME).
# src: tmp/pymol-src/modules/pymol/querying.py:851 cmd.get_color_index  (name -> int index)
hc_idx = cmd.get_color_index("hero_cyan")
# src: tmp/pymol-src/modules/pymol/querying.py:843 cmd.get_color_indices  (all=1 -> ALL colors incl. extended; build idx2name)
_idx2name_stage0 = {i: n for (n, i) in cmd.get_color_indices(all=1)}
check("hero_cyan_defined",
      hc_idx is not None and hc_idx in _idx2name_stage0
      and _idx2name_stage0[hc_idx] == "hero_cyan",
      "idx=%r name=%r" % (hc_idx, _idx2name_stage0.get(hc_idx)))

# =========================================================================
# Stage 1: Case 1 hero-alone (the intro.preface pattern; RESEARCH-api
# section C.1 Strategy A -- the hero as its OWN single-atom object).
# Load the bundled _smoke.pdb (3 atoms C1/O1/C2) as `mol`, then extract the
# hero (name C1) as a dedicated 1-atom object `hero_atom` via cmd.create.
# Apply the hero-highlight sequence (convention section 3.3 -- the NEW
# OQ-3 OVERRIDE sequence: all-C cyan sticks + ball-and-stick + "YOU" label;
# no scoped-dim).
# =========================================================================
smoke_path = str(c14.paths.data_path("data", "assets", "bundled", "_smoke.pdb"))
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load  (load a structure file into a named object)
    cmd.load(smoke_path, "mol")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    check("load_smoke", cmd.count_atoms("mol") == 3, "atoms=%d" % cmd.count_atoms("mol"))

    # Extract the hero as its OWN single-atom object (RESEARCH-api section
    # C.1: empirically confirmed -- create("hero_atom", "mol and name C1")
    # makes a 1-atom object). NEVER cmd.create("mol","mol") (self-copy is
    # destructive); always a NEW name from a sele of a DIFFERENT object.
    # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create  (new object from a selection)
    cmd.create("hero_atom", "mol and name C1")

    # --- The hero-highlight sequence (convention section 3.3, OQ-3 OVERRIDE; 6 calls) ---
    # Step 1 (set_color) already done in Stage 0 (idempotent -- safe to skip).
    # Step 2: show_as sticks (base rep -- ALL atoms get sticks)
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (atomic ON+OFF per-atom; sticks on hero_atom)
    cmd.show_as("sticks", "hero_atom")
    # Step 3: color hero_cyan on elem C (ALL carbons cyan -- the hero is one of them)
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (apply named color to selection)
    cmd.color("hero_cyan", "hero_atom and elem C")
    # Step 5: show spheres ON TOP of sticks (ball-and-stick; NOT show_as -- sticks stay)
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show  (ADDS rep on top; turns ON only)
    cmd.show("spheres", "hero_atom")
    # Step 6: set sphere_scale 0.3 (SMALL elegant sphere, NOT the giant default 1.0)
    # src: tmp/pymol-src/modules/pymol/setting.py:183 cmd.set  (per-atom setting: sphere_scale on hero_atom)
    cmd.set("sphere_scale", 0.3, "hero_atom")
    # Step 7: label "YOU" (the player-facing identity label -- OQ-4 OVERRIDE)
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (quoted-string expression '"YOU"'; bare "YOU" would eval atom prop -- Pitfall 2)
    cmd.label("hero_atom", '"YOU"')

    # --- Post-conditions (convention section 3 + RESEARCH-api section D.1) ---
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (exactly one atom)
    check("case1_count_1", cmd.count_atoms("hero_atom") == 1,
          "atoms=%d" % cmd.count_atoms("hero_atom"))

    elems = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate  (read elem; collector `elems` avoids collision)
    cmd.iterate("hero_atom", "elems.append(elem)", space={"elems": elems})
    check("case1_elem_C", elems == ["C"], "elems=%r" % elems)

    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (the `rep <name>` keyword = headless "rep visible" primitive)
    check("case1_rep_spheres", cmd.count_atoms("hero_atom and rep spheres") == 1,
          "rep-spheres=%d" % cmd.count_atoms("hero_atom and rep spheres"))

    # Ball-and-stick: the hero has BOTH sticks AND spheres
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (rep keyword -- sticks assigned too)
    check("case1_rep_sticks", cmd.count_atoms("hero_atom and rep sticks") == 1,
          "rep-sticks=%d" % cmd.count_atoms("hero_atom and rep sticks"))

    check("case1_color_hero_cyan", color_name_for("hero_atom") == "hero_cyan",
          "color=%r" % color_name_for("hero_atom"))

    lbls = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate  (read label text; collector `lbls` avoids collision)
    cmd.iterate("hero_atom", "lbls.append(label)", space={"lbls": lbls})
    check("case1_label_YOU", lbls == ["YOU"], "labels=%r" % lbls)
except Exception as e:
    check("load_smoke", False, repr(e))
    check("case1_count_1", False, repr(e))
    check("case1_elem_C", False, repr(e))
    check("case1_rep_spheres", False, repr(e))
    check("case1_rep_sticks", False, repr(e))
    check("case1_color_hero_cyan", False, repr(e))
    check("case1_label_YOU", False, repr(e))

# =========================================================================
# Stage 2: Case 2 hero-in-substrate (the intro.shell_glucose / gly.start
# pattern; RESEARCH-api section C.1 Strategy B + section A.1 per-atom
# scoping). The hero is `name C1` IN the multi-atom `mol` object (a
# deterministic sub-sele). The NEW OQ-3 OVERRIDE hero-highlight: ALL carbons
# in mol are colored hero_cyan sticks; the hero (C1) is ball-and-stick
# (sticks + small sphere); non-carbons (O1) keep their element colors (NOT
# dimmed -- the old scoped-dim gray80 was REMOVED).
# =========================================================================
try:
    # --- The hero-highlight sequence on mol (convention section 3.3, OQ-3 OVERRIDE) ---
    # Step 2: show_as sticks (ALL atoms in mol -> sticks base rep)
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (ALL atoms -> sticks)
    cmd.show_as("sticks", "mol")
    # Step 3: color hero_cyan on ALL carbons (the hero is one of them)
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (hero_cyan on elem C)
    cmd.color("hero_cyan", "mol and elem C")
    # Step 4: non-carbons RETAIN element colors (NO color call -- O1 keeps "oxygen")
    # Step 5: show spheres ON TOP of sticks for the hero (ball-and-stick)
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show  (ADDS spheres on C1 only; sticks stay)
    cmd.show("spheres", "mol and name C1")
    # Step 6: set sphere_scale 0.3 (SMALL elegant sphere)
    # src: tmp/pymol-src/modules/pymol/setting.py:183 cmd.set  (per-atom sphere_scale on the hero sub-sele)
    cmd.set("sphere_scale", 0.3, "mol and name C1")
    # Step 7: label "YOU" (the player-facing identity label)
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (quoted-string expression on the hero sub-sele)
    cmd.label("mol and name C1", '"YOU"')

    # --- Post-conditions ---
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    check("case2_hero_count_1", cmd.count_atoms("mol and name C1") == 1,
          "hero=%d" % cmd.count_atoms("mol and name C1"))

    elems2 = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
    cmd.iterate("mol and name C1", "elems2.append(elem)", space={"elems2": elems2})
    check("case2_hero_elem_C", elems2 == ["C"], "elems=%r" % elems2)

    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (rep keyword)
    check("case2_hero_rep_spheres",
          cmd.count_atoms("mol and name C1 and rep spheres") == 1,
          "rep-spheres=%d" % cmd.count_atoms("mol and name C1 and rep spheres"))

    # Ball-and-stick: hero has BOTH sticks AND spheres
    check("case2_hero_rep_sticks",
          cmd.count_atoms("mol and name C1 and rep sticks") == 1,
          "rep-sticks=%d" % cmd.count_atoms("mol and name C1 and rep sticks"))

    check("case2_hero_color_hero_cyan",
          color_name_for("mol and name C1") == "hero_cyan",
          "color=%r" % color_name_for("mol and name C1"))

    lbls2 = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
    cmd.iterate("mol and name C1", "lbls2.append(label)", space={"lbls2": lbls2})
    check("case2_hero_label_YOU", lbls2 == ["YOU"], "labels=%r" % lbls2)

    # --- ALL carbons cyan PROOF (OQ-3 OVERRIDE: the hero is "one of them") ---
    # C2 (the OTHER carbon) is also hero_cyan -- ALL carbons are cyan sticks.
    check("case2_all_carbons_cyan",
          color_name_for("mol and name C2") == "hero_cyan",
          "c2-color=%r" % color_name_for("mol and name C2"))

    # --- non-carbon keeps element color PROOF (NOT dimmed) ---
    # O1 retains its element color "oxygen" (NOT gray80 -- the old scoped-dim
    # was REMOVED per OQ-3 OVERRIDE; non-carbons keep element colors).
    check("case2_noncarbon_element_color",
          color_name_for("mol and name O1") == "oxygen",
          "o1-color=%r" % color_name_for("mol and name O1"))

    # --- per-atom scoping PROOF (RESEARCH-api section A.1) ---
    # O1/C2 did NOT get spheres -- the show spheres was scoped to `mol and name C1`.
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (rep keyword on non-hero)
    check("case2_others_not_spheres",
          cmd.count_atoms("mol and not name C1 and rep spheres") == 0,
          "others-spheres=%d" % cmd.count_atoms("mol and not name C1 and rep spheres"))

    # --- all carbons have sticks (the base rep) ---
    check("case2_all_carbons_sticks",
          cmd.count_atoms("mol and elem C and rep sticks") == 2,
          "c-sticks=%d" % cmd.count_atoms("mol and elem C and rep sticks"))
except Exception as e:
    check("case2_hero_count_1", False, repr(e))
    check("case2_hero_elem_C", False, repr(e))
    check("case2_hero_rep_spheres", False, repr(e))
    check("case2_hero_rep_sticks", False, repr(e))
    check("case2_hero_color_hero_cyan", False, repr(e))
    check("case2_hero_label_YOU", False, repr(e))
    check("case2_all_carbons_cyan", False, repr(e))
    check("case2_noncarbon_element_color", False, repr(e))
    check("case2_others_not_spheres", False, repr(e))
    check("case2_all_carbons_sticks", False, repr(e))

# =========================================================================
# Stage 3: Case 3 hero-at-enzyme-cast (the gly.pfk / pyr.pdh pattern;
# RESEARCH-hero-highlight section A case 3a co-load). Load a placeholder
# enzyme (the cast member) shown as cartoon gray; co-load a small substrate
# containing the hero (case 3a); highlight the hero in the substrate while
# the enzyme keeps its cast cartoon gray (the all-C-cyan applies to the
# SUBSTRATE only, NOT the enzyme -- convention section 3.3 critical scoping).
# =========================================================================
edit_smoke_path = str(c14.paths.data_path("data", "assets", "bundled", "_edit_smoke.pdb"))
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load  (the placeholder enzyme/cast: 17-atom ALA-GLY)
    cmd.load(edit_smoke_path, "enzyme")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    check("case3_load_enzyme", cmd.count_atoms("enzyme") > 0,
          "enzyme=%d" % cmd.count_atoms("enzyme"))

    # Apply the cast representation (convention section 5 -- the enzyme keeps
    # its OWN color, NOT colored cyan). show_as cartoon lights up all 17 atoms.
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (cartoon for the cast/enzyme)
    cmd.show_as("cartoon", "enzyme")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (gray -- the enzyme is the STAGE, recedes)
    cmd.color("gray", "enzyme")

    # Co-load the substrate (case 3a): reuse the C1 from Stage 1's `mol` -- a
    # 1-atom substrate containing the hero.
    # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create  (new substrate object from mol's C1)
    cmd.create("substrate", "mol and name C1")

    # Apply the hero-highlight on the substrate's hero (convention section 3.3
    # OQ-3 OVERRIDE -- the all-C-cyan applies to the SUBSTRATE, NOT the enzyme).
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (sticks base rep on the 1-atom substrate)
    cmd.show_as("sticks", "substrate")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (hero_cyan on the substrate carbon)
    cmd.color("hero_cyan", "substrate and elem C")
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show  (ball-and-stick: ADD spheres ON TOP of sticks)
    cmd.show("spheres", "substrate")
    # src: tmp/pymol-src/modules/pymol/setting.py:183 cmd.set  (small elegant sphere)
    cmd.set("sphere_scale", 0.3, "substrate")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (the player-facing identity label)
    cmd.label("substrate", '"YOU"')

    # --- Post-conditions ---
    # The enzyme keeps its cast cartoon (NOT affected by the substrate highlight).
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (rep keyword on enzyme)
    check("case3_enzyme_rep_cartoon",
          cmd.count_atoms("enzyme and rep cartoon") > 0,
          "enzyme-cartoon=%d" % cmd.count_atoms("enzyme and rep cartoon"))

    # The enzyme is NOT colored cyan -- the all-C-cyan is scoped to the substrate only
    # (convention section 3.3 critical scoping note). Verify via a CA atom.
    check("case3_enzyme_color_gray",
          color_name_for("enzyme and name CA") == "gray",
          "enzyme-ca-color=%r" % color_name_for("enzyme and name CA"))

    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (hero is one carbon in the substrate)
    check("case3_hero_in_substrate",
          cmd.count_atoms("substrate and elem C") == 1,
          "substrate-C=%d" % cmd.count_atoms("substrate and elem C"))

    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (rep keyword on substrate)
    check("case3_hero_spheres",
          cmd.count_atoms("substrate and rep spheres") == 1,
          "substrate-spheres=%d" % cmd.count_atoms("substrate and rep spheres"))

    check("case3_hero_color_hero_cyan",
          color_name_for("substrate") == "hero_cyan",
          "substrate-color=%r" % color_name_for("substrate"))

    lbls3 = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
    cmd.iterate("substrate", "lbls3.append(label)", space={"lbls3": lbls3})
    check("case3_hero_label_YOU", lbls3 == ["YOU"], "labels=%r" % lbls3)
except Exception as e:
    check("case3_load_enzyme", False, repr(e))
    check("case3_enzyme_rep_cartoon", False, repr(e))
    check("case3_enzyme_color_gray", False, repr(e))
    check("case3_hero_in_substrate", False, repr(e))
    check("case3_hero_spheres", False, repr(e))
    check("case3_hero_color_hero_cyan", False, repr(e))
    check("case3_hero_label_YOU", False, repr(e))

# =========================================================================
# Stage 4: the CO2-shed soul-transfer climax (convention section 3.5; the
# dramatic peak). Build a placeholder `co2` object (the departing carbon body
# -- the "chrysalis"); show it with the hero highlight ONE final time; FADE
# the carbon body (the cyan leaves the CO2); TRANSFER the soul to the NADH /
# electron carrier (the cyan APPEARS on a NEW object -- the electrons, NOT
# the carbon).
#
# ANTI-CONFUSION (convention section 3.6; restated inline at the transfer
# step below): the cyan on `nadh` represents the hero's ELECTRONS (the
# narrative "soul"), NOT the carbon atom. The carbon body (co2) was shed +
# faded. This is a narrative device; the carbon does NOT become NADH or ATP.
# =========================================================================
try:
    # --- The chrysalis: the departing carbon body highlighted one last time ---
    # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create  (placeholder co2 from mol's C1)
    cmd.create("co2", "mol and name C1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (sticks on the departing carbon)
    cmd.show_as("sticks", "co2")
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show  (ball-and-stick: add spheres)
    cmd.show("spheres", "co2")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (hero_cyan one final time)
    cmd.color("hero_cyan", "co2")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (the farewell label)
    cmd.label("co2", '"YOU (farewell)"')
    check("climax_co2_highlighted", color_name_for("co2") == "hero_cyan",
          "co2-color=%r" % color_name_for("co2"))

    # --- FADE the carbon body (the cyan leaves the CO2; the chrysalis is shed) ---
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (gray80 -- the fade)
    cmd.color("gray80", "co2")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (empty expression "" clears the label -- RESEARCH-api section A.4)
    cmd.label("co2", '""')
    check("climax_co2_faded", color_name_for("co2") == "gray80",
          "co2-faded-color=%r" % color_name_for("co2"))

    lbls_co2 = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate  (verify label cleared -> [""])
    cmd.iterate("co2", "lbls_co2.append(label)", space={"lbls_co2": lbls_co2})
    check("climax_co2_label_cleared", lbls_co2 == [""], "labels=%r" % lbls_co2)

    # --- TRANSFER the soul to the NADH / electron carrier (the cyan appears) ---
    # ANTI-CONFUSION: the cyan on `nadh` represents the hero's ELECTRONS (the
    # narrative "soul"), NOT the carbon atom. The carbon body (co2) was shed +
    # faded. This is a narrative device; the carbon does NOT become NADH or
    # ATP (scientifically WRONG -- the carbon body leaves as CO2; only the
    # electrons continue via NADH/FADH2 -> ETC -> ATP synthase).
    # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create  (placeholder nadh/electron-carrier from mol's C1)
    cmd.create("nadh", "mol and name C1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (spheres on the electron carrier)
    cmd.show_as("spheres", "nadh")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (hero_cyan APPEARS -- the soul transfer)
    cmd.color("hero_cyan", "nadh")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (the soul/electrons label)
    cmd.label("nadh", '"soul (electrons)"')
    check("climax_nadh_highlighted", color_name_for("nadh") == "hero_cyan",
          "nadh-color=%r" % color_name_for("nadh"))
except Exception as e:
    check("climax_co2_highlighted", False, repr(e))
    check("climax_co2_faded", False, repr(e))
    check("climax_co2_label_cleared", False, repr(e))
    check("climax_nadh_highlighted", False, repr(e))

# --- Final verdict via STDOUT SENTINEL (NOT exit code -- the bat always returns 0) ---
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
