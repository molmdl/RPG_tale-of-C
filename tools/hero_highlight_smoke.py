#!/usr/bin/env python
# tools/hero_highlight_smoke.py -- Phase 5.4 Plan 02 C14 hero highlight
# headless prototype (SC1 mechanism).
#
# Pure pymol.cmd.* script (NO Qt) that exercises the hero-highlight MECHANISM
# on placeholder fixtures across the 3 structural cases (hero-alone /
# hero-in-substrate / hero-at-enzyme-cast) + the CO2-shed soul-transfer
# climax. Proves the MECHANISM (select -> count==1 -> elem C -> spheres ->
# hero_gold -> label C14 -> color-name round-trip), NOT real science
# (placeholder coords are arbitrary; real hero-selectors are Phase 7 content).
#
# This smoke calls cmd.set_color / cmd.label / cmd.show_as / cmd.color /
# cmd.set DIRECTLY (NOT via molops.apply). The op="set_color" / op="label" /
# op="set" molops dispatches are deferred to Phase 6 per convention
# 05.4-CONVENTION.md section 2.2 / OQ-1. This smoke proves the MECHANISM the
# dispatches will eventually wrap (the 3-tier testability pattern: unit tests
# = mapping logic, headless smoke = real cmd.* contract -- mirrors how
# tools/wt_align_smoke.py calls cmd.super directly per 05.3-CONVENTION.md
# section 6).
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
    # src: tmp/pymol-src/modules/pymol/querying.py:843 cmd.get_color_indices  (returns [(name, index), ...])
    idx2name = {i: n for (n, i) in cmd.get_color_indices()}
    return idx2name.get(cidx[0])


# =========================================================================
# Stage 0: define the hero_gold named color (convention section 2.3 palette +
# section 3.3 step 1). Okabe-Ito orange [0.90, 0.62, 0.0] (PLACEHOLDER RGB
# pending Phase 7 source approval -- RESEARCH-api section I OQ-2). Idempotent
# overwrite (re-running on on_enter replay / re-init is safe).
# =========================================================================
# src: tmp/pymol-src/modules/pymol/viewing.py:2107 cmd.set_color  (DEFINE a named RGB color; auto 0-1/0-255 range)
cmd.set_color("hero_gold", [0.90, 0.62, 0.0])

# Verify the named color round-trips: get_color_index(name) -> index, then
# get_color_indices() -> {index: name}, assert the name round-trips. This is
# the RESEARCH-api section D.3 robustness rule (do NOT assert a hardcoded
# index; assert the NAME).
# src: tmp/pymol-src/modules/pymol/querying.py:851 cmd.get_color_index  (name -> int index)
hg_idx = cmd.get_color_index("hero_gold")
# src: tmp/pymol-src/modules/pymol/querying.py:843 cmd.get_color_indices  ([(name,index),...]; build idx2name)
_idx2name_stage0 = {i: n for (n, i) in cmd.get_color_indices()}
check("hero_gold_defined",
      hg_idx is not None and hg_idx in _idx2name_stage0
      and _idx2name_stage0[hg_idx] == "hero_gold",
      "idx=%r name=%r" % (hg_idx, _idx2name_stage0.get(hg_idx)))

# =========================================================================
# Stage 1: Case 1 hero-alone (the intro.preface pattern; RESEARCH-api
# section C.1 Strategy A -- the hero as its OWN single-atom object).
# Load the bundled _smoke.pdb (3 atoms C1/O1/C2) as `mol`, then extract the
# hero (name C1) as a dedicated 1-atom object `hero_atom` via cmd.create.
# Apply the hero-highlight sequence (convention section 3.3 -- the section
# 3.3 step 5 dim OMITTED: a single atom has no non-hero atoms).
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

    # --- The hero-highlight sequence (convention section 3.3, 5 calls; no dim) ---
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (atomic ON+OFF per-atom; spheres on hero_atom)
    cmd.show_as("spheres", "hero_atom")
    # src: tmp/pymol-src/modules/pymol/setting.py:183 cmd.set  (per-atom setting: sphere_scale on hero_atom)
    cmd.set("sphere_scale", 1.0, "hero_atom")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (apply named color to selection)
    cmd.color("hero_gold", "hero_atom")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (quoted-string expression '"C14"'; bare "C14" would eval atom prop C14 -- Pitfall 2)
    cmd.label("hero_atom", '"C14"')

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

    check("case1_color_hero_gold", color_name_for("hero_atom") == "hero_gold",
          "color=%r" % color_name_for("hero_atom"))

    lbls = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate  (read label text; collector `lbls` avoids collision)
    cmd.iterate("hero_atom", "lbls.append(label)", space={"lbls": lbls})
    check("case1_label_C14", lbls == ["C14"], "labels=%r" % lbls)
except Exception as e:
    check("load_smoke", False, repr(e))
    check("case1_count_1", False, repr(e))
    check("case1_elem_C", False, repr(e))
    check("case1_rep_spheres", False, repr(e))
    check("case1_color_hero_gold", False, repr(e))
    check("case1_label_C14", False, repr(e))

# =========================================================================
# Stage 2: Case 2 hero-in-substrate (the intro.shell_glucose / gly.start
# pattern; RESEARCH-api section C.1 Strategy B + section A.1 per-atom
# scoping). The hero is `name C1` IN the multi-atom `mol` object (a
# deterministic sub-sele). The hero-highlight applies on the SUB-SELE; the
# per-atom scoping leaves O1/C2 untouched (empirically confirmed RESEARCH-api
# section A.1 / A.6). The scoped dim (convention section 3.3 step 5) dims the
# non-hero atoms IN the hero-bearing object only.
# =========================================================================
try:
    # --- The hero-highlight sequence on the sub-sele (convention section 3.3) ---
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (per-atom: only C1 -> spheres; O1/C2 keep existing rep)
    cmd.show_as("spheres", "mol and name C1")
    # src: tmp/pymol-src/modules/pymol/setting.py:183 cmd.set  (per-atom sphere_scale on the hero sub-sele)
    cmd.set("sphere_scale", 1.0, "mol and name C1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (hero_gold on the hero sub-sele)
    cmd.color("hero_gold", "mol and name C1")
    # The scoped dim (convention section 3.3 step 5): dim O1+C2 -- the non-hero
    # atoms IN the hero-bearing object (NOT the cast/enzyme; critical scoping).
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (gray80 dim scoped to non-hero in mol)
    cmd.color("gray80", "mol and not name C1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (quoted-string expression on the hero sub-sele)
    cmd.label("mol and name C1", '"C14"')

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

    check("case2_hero_color_hero_gold",
          color_name_for("mol and name C1") == "hero_gold",
          "color=%r" % color_name_for("mol and name C1"))

    lbls2 = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
    cmd.iterate("mol and name C1", "lbls2.append(label)", space={"lbls2": lbls2})
    check("case2_hero_label_C14", lbls2 == ["C14"], "labels=%r" % lbls2)

    # --- per-atom scoping PROOF (RESEARCH-api section A.1) ---
    # O1/C2 did NOT get spheres -- the show_as was scoped to `mol and name C1`.
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (rep keyword on non-hero)
    check("case2_others_not_spheres",
          cmd.count_atoms("mol and not name C1 and rep spheres") == 0,
          "others-spheres=%d" % cmd.count_atoms("mol and not name C1 and rep spheres"))

    # --- scoped dim PROOF ---
    # O1/C2 dimmed gray80 (the scoped spotlight within the hero-bearing object).
    check("case2_dim_gray80",
          color_name_for("mol and not name C1") == "gray80",
          "dim-color=%r" % color_name_for("mol and not name C1"))
except Exception as e:
    check("case2_hero_count_1", False, repr(e))
    check("case2_hero_elem_C", False, repr(e))
    check("case2_hero_rep_spheres", False, repr(e))
    check("case2_hero_color_hero_gold", False, repr(e))
    check("case2_hero_label_C14", False, repr(e))
    check("case2_others_not_spheres", False, repr(e))
    check("case2_dim_gray80", False, repr(e))

# =========================================================================
# Stage 3: Case 3 hero-at-enzyme-cast (the gly.pfk / pyr.pdh pattern;
# RESEARCH-hero-highlight section A case 3a co-load). Load a placeholder
# enzyme (the cast member) shown as cartoon gray; co-load a small substrate
# containing the hero (case 3a); highlight the hero in the substrate while
# the enzyme keeps its cast cartoon gray (the dim is scoped to the SUBSTRATE
# only, NOT the enzyme -- convention section 3.3 critical scoping note).
# =========================================================================
edit_smoke_path = str(c14.paths.data_path("data", "assets", "bundled", "_edit_smoke.pdb"))
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load  (the placeholder enzyme/cast: 17-atom ALA-GLY)
    cmd.load(edit_smoke_path, "enzyme")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    check("case3_load_enzyme", cmd.count_atoms("enzyme") > 0,
          "enzyme=%d" % cmd.count_atoms("enzyme"))

    # Apply the cast representation (convention section 5 -- the enzyme keeps
    # its OWN color, NOT dimmed). show_as cartoon lights up all 17 atoms
    # (RESEARCH-api section A.6: rep cartoon=17 on a 2-residue peptide).
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (cartoon for the cast/enzyme)
    cmd.show_as("cartoon", "enzyme")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (gray -- the enzyme is the STAGE, recedes)
    cmd.color("gray", "enzyme")

    # Co-load the substrate (case 3a): reuse the C1 from Stage 1's `mol` -- a
    # 1-atom substrate containing the hero.
    # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create  (new substrate object from mol's C1)
    cmd.create("substrate", "mol and name C1")

    # Apply the hero-highlight on the substrate's hero (convention section 3.3
    # -- the dim scoped to the SUBSTRATE, NOT the enzyme).
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (spheres on the 1-atom substrate)
    cmd.show_as("spheres", "substrate")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (hero_gold on the substrate)
    cmd.color("hero_gold", "substrate")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (quoted-string expression)
    cmd.label("substrate", '"C14"')

    # --- Post-conditions ---
    # The enzyme keeps its cast cartoon (NOT affected by the substrate highlight).
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms  (rep keyword on enzyme)
    check("case3_enzyme_rep_cartoon",
          cmd.count_atoms("enzyme and rep cartoon") > 0,
          "enzyme-cartoon=%d" % cmd.count_atoms("enzyme and rep cartoon"))

    # The enzyme is NOT dimmed -- the dim is scoped to the substrate only
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

    check("case3_hero_color_hero_gold",
          color_name_for("substrate") == "hero_gold",
          "substrate-color=%r" % color_name_for("substrate"))

    lbls3 = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
    cmd.iterate("substrate", "lbls3.append(label)", space={"lbls3": lbls3})
    check("case3_hero_label_C14", lbls3 == ["C14"], "labels=%r" % lbls3)
except Exception as e:
    check("case3_load_enzyme", False, repr(e))
    check("case3_enzyme_rep_cartoon", False, repr(e))
    check("case3_enzyme_color_gray", False, repr(e))
    check("case3_hero_in_substrate", False, repr(e))
    check("case3_hero_spheres", False, repr(e))
    check("case3_hero_color_hero_gold", False, repr(e))
    check("case3_hero_label_C14", False, repr(e))

# =========================================================================
# Stage 4: the CO2-shed soul-transfer climax (convention section 3.5; the
# dramatic peak). Build a placeholder `co2` object (the departing carbon body
# -- the "chrysalis"); show it with the hero highlight ONE final time; FADE
# the carbon body (the gold leaves the CO2); TRANSFER the soul to the NADH /
# electron carrier (the gold APPEARS on a NEW object -- the electrons, NOT
# the carbon).
#
# ANTI-CONFUSION (convention section 3.6; restated inline at the transfer
# step below): the gold on `nadh` represents the hero's ELECTRONS (the
# narrative "soul"), NOT the carbon atom. The carbon body (co2) was shed +
# faded. This is a narrative device; the carbon does NOT become NADH or ATP.
# =========================================================================
try:
    # --- The chrysalis: the departing carbon body highlighted one last time ---
    # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create  (placeholder co2 from mol's C1)
    cmd.create("co2", "mol and name C1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (spheres on the departing carbon)
    cmd.show_as("spheres", "co2")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (hero_gold one final time)
    cmd.color("hero_gold", "co2")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (the farewell label)
    cmd.label("co2", '"C14 (farewell)"')
    check("climax_co2_highlighted", color_name_for("co2") == "hero_gold",
          "co2-color=%r" % color_name_for("co2"))

    # --- FADE the carbon body (the gold leaves the CO2; the chrysalis is shed) ---
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

    # --- TRANSFER the soul to the NADH / electron carrier (the gold appears) ---
    # ANTI-CONFUSION: the gold on `nadh` represents the hero's ELECTRONS (the
    # narrative "soul"), NOT the carbon atom. The carbon body (co2) was shed +
    # faded. This is a narrative device; the carbon does NOT become NADH or
    # ATP (scientifically WRONG -- the carbon body leaves as CO2; only the
    # electrons continue via NADH/FADH2 -> ETC -> ATP synthase).
    # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create  (placeholder nadh/electron-carrier from mol's C1)
    cmd.create("nadh", "mol and name C1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as  (spheres on the electron carrier)
    cmd.show_as("spheres", "nadh")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (hero_gold APPEARS -- the soul transfer)
    cmd.color("hero_gold", "nadh")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (the soul/electrons label)
    cmd.label("nadh", '"soul (electrons)"')
    check("climax_nadh_highlighted", color_name_for("nadh") == "hero_gold",
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
