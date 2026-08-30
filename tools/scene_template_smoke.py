#!/usr/bin/env python
# tools/scene_template_smoke.py -- Phase 5.4 Plan 03 scene-template +
# cast-reveal headless prototype (SC2+SC3 mechanism).
#
# Pure pymol.cmd.* script (NO Qt) that exercises all 6 scene TYPES + the
# cast-reveal + the 5.3 composition on placeholder fixtures. Each template
# is a MolAction SEQUENCE applied via direct cmd.* (NOT cmd.scene -- session
# state is not save/load-safe). Proves the MECHANISM (rep visible + color
# name + label + named-selection count), NOT real science (placeholder
# structures; real active-site/catalytic/mutant selections are Phase 7
# content).
#
# This smoke calls cmd.* DIRECTLY (NOT via molops.apply). The new-op
# dispatches (op="set_color"/"label"/"set") are deferred to Phase 6 per
# convention 05.4-CONVENTION.md section 2.2 / OQ-1 (mirrors the 5.3
# precedent: 05.3 prototyped cmd.super directly, deferred op="align" to
# Phase 6). This smoke proves the MECHANISM the dispatches will eventually
# wrap (the 3-tier testability pattern: unit tests = mapping logic,
# headless smoke = real cmd.* contract).
#
# ANTI-CONFUSION (hero-identity, from AGENTS.md + PROJECT.md row 107):
#   The cast-reveal shows the ENZYME's health (mutant vs WT), NOT the hero
#   carbon's fate. The 5.3 composition shows the enzyme restored; at
#   pyr.pdh the carbon IS shed as CO2 while the hero's electrons continue
#   (the soul-jump metamorphosis) -- keep enzyme-health and carbon-fate
#   framing SEPARATE. The hero is a CARBON ATOM; C14 is its tracking
#   isotope label, NOT its fate. Do NOT reintroduce claims that the C14
#   carbon itself becomes ATP or enters oxidative phosphorylation --
#   those are scientifically wrong (the carbon body leaves as CO2; only
#   the electrons continue).
#
# CRITICAL CONTRACT RULES (from 03-RESEARCH.md, reused from wt_align_smoke.py):
#   * Gotcha #1: the process ALWAYS exits 0 through run-conda-pymol.bat
#     (`call conda deactivate` overwrites %ERRORLEVEL%; PyMOL swallows
#     exceptions). So we CANNOT use sys.exit/raise/cmd.quit to signal failure --
#     the SMOKE_RESULT: stdout sentinel is the ONLY reliable verdict.
#   * Gotcha #2: __file__ in a PyMOL-run script resolves to the pymol package's
#     __init__.py, NOT this script's path. So we use os.getcwd() (= repo root
#     when run with cwd=repo-root) + import rpg.paths (whose __file__ IS
#     correct) to locate bundled fixtures.
#   * Gotcha #6: pymol.finish_launching() completes PyMOL startup before any
#     cmd.* call.
#
# Every direct cmd.* call in THIS smoke carries a `# src:` citation (Phase 3
# convention; line numbers verified against tmp/pymol-src/modules/pymol/).
# The new-op molops dispatches are deferred to Phase 6 (convention section
# 2.2 / OQ-1); this smoke proves the real cmd.* contract the dispatches wrap.
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/scene_template_smoke.py
# Verdict: grep ^SMOKE_RESULT: PASS in the captured stdout (NOT $?).

import sys
import os

# Gotcha #2/#3/#4: cwd=repo root when run via the harness, so os.getcwd() is
# the workspace and `import rpg` works (sys.path includes '' = cwd). Insert
# cwd explicitly as belt-and-suspenders so this script is robust if sys.path
# lacks ''.
sys.path.insert(0, os.getcwd())

import pymol
from pymol import cmd
import rpg.paths

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
    """Return the named color of the first atom in `sele`, or None.

    Uses the iterate-color-index -> get_color_indices index->name round-trip
    (RESEARCH-api section D.1 / section F Pitfall 4: the color INDEX is
    session-allocated, so assert the NAME, not a hardcoded index). The
    collector `cidx` is NON-colliding (RESEARCH-api section F Pitfall 1: a
    collector named `color` would shadow the atom's `color` property and
    raise AttributeError 'int' object has no attribute 'append').
    """
    try:
        cidx = []
        # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
        cmd.iterate(sele, "cidx.append(color)", space={"cidx": cidx})
        if not cidx:
            return None
        # src: tmp/pymol-src/modules/pymol/querying.py:843 cmd.get_color_indices
        idx2name = {i: n for (n, i) in cmd.get_color_indices(all=1)}
        return idx2name.get(cidx[0])
    except Exception:
        return None


def label_text_for(sele):
    # type: (str) -> str
    """Return the label text of the first atom in `sele`, or None.

    Collector `lbls` is NON-colliding (RESEARCH-api section F Pitfall 1).
    """
    try:
        lbls = []
        # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
        cmd.iterate(sele, "lbls.append(label)", space={"lbls": lbls})
        return lbls[0] if lbls else None
    except Exception:
        return None


# =========================================================================
# Stage 0 -- define the palette (convention section 2.3).
# hero_cyan is a PLACEHOLDER PLACEHOLDER colorblind-safe cyan; gray/green/red/orange/gray80
# are standard PyMOL named colors (no set_color needed for them). The final
# palette + RGB source approval is Phase 7 (RESEARCH-api section I OQ-2;
# spec.md no-fabricated-science).
# =========================================================================
try:
    # src: tmp/pymol-src/modules/pymol/viewing.py:2107 cmd.set_color
    cmd.set_color("hero_cyan", [0.0, 0.75, 0.75])
    # src: tmp/pymol-src/modules/pymol/querying.py:851 cmd.get_color_index
    hg = cmd.get_color_index("hero_cyan")
    # src: tmp/pymol-src/modules/pymol/querying.py:851 cmd.get_color_index
    gn = cmd.get_color_index("green")
    check("t0_palette", hg is not None and gn is not None,
          "hero_cyan=%r green=%r" % (hg, gn))
except Exception as e:
    check("t0_palette", False, repr(e))

# =========================================================================
# Type 1 -- preface (convention section 4.3 Type 1; nodes intro.preface etc).
# The hero atom + the 20-AA cast lineup (here the cast placeholder is the
# 17-atom ALA-GLY _edit_smoke.pdb). Hero is its own single-atom object
# (Strategy A, RESEARCH-api section C.1 -- the hero is a CARBON; C14 is its
# tracking label).
# =========================================================================
try:
    smoke_path = str(rpg.paths.data_path("data", "assets", "bundled", "_smoke.pdb"))
    edit_path = str(rpg.paths.data_path("data", "assets", "bundled", "_edit_smoke.pdb"))
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(smoke_path, "smoke")
    # src: tmp/pymol-src/modules/pymol/creating.py:960 cmd.create  (def line; plan-listed 1001 is inside the body)
    cmd.create("hero_atom", "smoke and name C1")
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(edit_path, "aa_cast")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("sticks", "hero_atom")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("hero_cyan", "hero_atom and elem C")
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show  (ball-and-stick: ADD spheres ON TOP of sticks)
    cmd.show("spheres", "hero_atom")
    # src: tmp/pymol-src/modules/pymol/setting.py:183 cmd.set  (small elegant sphere)
    cmd.set("sphere_scale", 0.3, "hero_atom")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label
    cmd.label("hero_atom", '"YOU"')
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("cartoon", "aa_cast")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("gray", "aa_cast")
    # src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom
    cmd.zoom("all")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_h = cmd.count_atoms("hero_atom")
    check("t1_hero_count_1", n_h == 1, "atoms=%d" % n_h)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_hs = cmd.count_atoms("hero_atom and rep spheres")
    check("t1_hero_spheres", n_hs == 1, "rep-spheres=%d" % n_hs)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_cc = cmd.count_atoms("aa_cast and rep cartoon")
    check("t1_cast_cartoon", n_cc > 0, "rep-cartoon=%d" % n_cc)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_cl = cmd.count_atoms("aa_cast")
    check("t1_cast_loaded", n_cl > 0, "atoms=%d" % n_cl)
except Exception as e:
    check("t1_exception", False, repr(e))

# =========================================================================
# Type 2 -- substrate-traversal (convention section 4.3 Type 2; nodes
# gly.start etc). The substrate is present (sticks, gray); the hero is
# highlighted as gold spheres on the hero sub-sele (per-atom scoping: show_as
# spheres on `substrate and name C1` turns OFF sticks on C1 only, leaves
# O1/C2 as sticks -- RESEARCH-api section A.1).
# =========================================================================
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(smoke_path, "substrate")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("sticks", "substrate")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (ALL carbons cyan -- the hero is one of them)
    cmd.color("hero_cyan", "substrate and elem C")
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show  (ball-and-stick: ADD spheres ON TOP of sticks for hero only)
    cmd.show("spheres", "substrate and name C1")
    # src: tmp/pymol-src/modules/pymol/setting.py:183 cmd.set  (small elegant sphere)
    cmd.set("sphere_scale", 0.3, "substrate and name C1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label
    cmd.label("substrate and name C1", '"YOU"')
    # src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom
    cmd.zoom("substrate")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_st = cmd.count_atoms("substrate and rep sticks")
    check("t2_substrate_sticks", n_st > 0, "rep-sticks=%d" % n_st)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_hs2 = cmd.count_atoms("substrate and name C1 and rep spheres")
    check("t2_hero_spheres", n_hs2 == 1, "rep-spheres=%d" % n_hs2)
    check("t2_hero_color",
          color_name_for("substrate and name C1") == "hero_cyan",
          "color=%r" % color_name_for("substrate and name C1"))
except Exception as e:
    check("t2_exception", False, repr(e))

# =========================================================================
# Type 3 -- active-site-reveal = cast-reveal, DISEASE-MUTANT variant
# (convention section 5.2; nodes gly.pfk etc). The cast-reveal sequence:
#   full gray cartoon -> zoom active site -> WT catalytic green sticks ->
#   mutant red SPHERES (rep redundancy = colorblind-safe) -> nameplate label.
# `cmd.show` (NOT show_as) ADDS sticks/spheres on top of cartoon (show turns
# ON only; show_as would turn OFF cartoon -- RESEARCH-api section A.1).
# NOTE: the cast-reveal shows the ENZYME's health (mutant vs WT), NOT the
# hero carbon's fate (ANTI-CONFUSION, header note).
# =========================================================================
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(edit_path, "enzyme")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("cartoon", "enzyme")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("gray", "enzyme")
    # src: tmp/pymol-src/modules/pymol/selecting.py:48 cmd.select  (placeholder active-site = resi 1)
    cmd.select("enzyme_activesite", "enzyme and resi 1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom
    cmd.zoom("enzyme_activesite")
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show  (ADDS sticks on top of cartoon)
    cmd.show("sticks", "enzyme and resi 2")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("green", "enzyme and resi 2")
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show  (ADDS spheres on top of cartoon)
    cmd.show("spheres", "enzyme and resi 1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("magenta", "enzyme and resi 1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label  (ONE nameplate label per anchor CA; Pitfall 2 quoted-string)
    cmd.label("enzyme and resi 2 and name CA", '"ENZ"')
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_ec = cmd.count_atoms("enzyme and rep cartoon")
    check("t3_enzyme_cartoon", n_ec > 0, "rep-cartoon=%d" % n_ec)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_as = cmd.count_atoms("enzyme_activesite")
    check("t3_activesite_nonempty", n_as > 0, "activesite=%d" % n_as)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_ms = cmd.count_atoms("enzyme and resi 1 and rep spheres")
    check("t3_mutant_spheres", n_ms > 0, "rep-spheres=%d" % n_ms)
    check("t3_mutant_color_magenta",
          color_name_for("enzyme and resi 1 and name CA") == "magenta",
          "color=%r" % color_name_for("enzyme and resi 1 and name CA"))
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_cs = cmd.count_atoms("enzyme and resi 2 and rep sticks")
    check("t3_catalytic_sticks", n_cs > 0, "rep-sticks=%d" % n_cs)
    check("t3_catalytic_color_green",
          color_name_for("enzyme and resi 2 and name CA") == "green",
          "color=%r" % color_name_for("enzyme and resi 2 and name CA"))
    check("t3_nameplate_label",
          label_text_for("enzyme and resi 2 and name CA") == "ENZ",
          "label=%r" % label_text_for("enzyme and resi 2 and name CA"))
except Exception as e:
    check("t3_exception", False, repr(e))

# =========================================================================
# Type 3b -- active-site-reveal, STRUCTURAL variant (convention section 5.2;
# node tca.citrate_synthase, NO mutant). The SAME sequence MINUS the mutant-
# spheres step (the enzyme is NOT diseased). Reset the `enzyme` object:
# hide everything -> cartoon gray -> catalytic green sticks -> nameplate.
# (hide everything turns OFF the Type-3 spheres so the no-mutant-spheres
# post-condition holds.)
# =========================================================================
try:
    # src: tmp/pymol-src/modules/pymol/viewing.py:568 cmd.hide
    cmd.hide("everything", "enzyme")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("cartoon", "enzyme")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("gray", "enzyme")
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show
    cmd.show("sticks", "enzyme and resi 2")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("green", "enzyme and resi 2")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label
    cmd.label("enzyme and resi 2 and name CA", '"CS"')
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_ecb = cmd.count_atoms("enzyme and rep cartoon")
    check("t3b_enzyme_cartoon", n_ecb > 0, "rep-cartoon=%d" % n_ecb)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_nms = cmd.count_atoms("enzyme and resi 1 and rep spheres")
    check("t3b_no_mutant_spheres", n_nms == 0, "rep-spheres=%d" % n_nms)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_csb = cmd.count_atoms("enzyme and resi 2 and rep sticks")
    check("t3b_catalytic_sticks", n_csb > 0, "rep-sticks=%d" % n_csb)
except Exception as e:
    check("t3b_exception", False, repr(e))

# =========================================================================
# Type 4 -- branch-point (convention section 4.3 Type 4; nodes pyr.branch
# etc). Show the current state + HINT the alternative destiny. The
# `alt_destiny` is colored hero_cyan = the "where you could go" signal.
# 5.4 specs the 2-object data-level shape; the viewport SPLIT is deferred
# to Phase 6 (OQ-8).
# =========================================================================
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(smoke_path, "current")
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(edit_path, "alt_destiny")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("sticks", "current")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("gray", "current")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("sticks", "alt_destiny")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("hero_cyan", "alt_destiny")
    # src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom
    cmd.zoom("current")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_cur = cmd.count_atoms("current and rep sticks")
    check("t4_current_sticks", n_cur > 0, "rep-sticks=%d" % n_cur)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_alt = cmd.count_atoms("alt_destiny and rep sticks")
    check("t4_alt_sticks", n_alt > 0, "rep-sticks=%d" % n_alt)
    check("t4_alt_color_hero_cyan",
          color_name_for("alt_destiny and name CA") == "hero_cyan",
          "color=%r" % color_name_for("alt_destiny and name CA"))
    check("t4_current_color_gray",
          color_name_for("current and name C1") == "gray",
          "color=%r" % color_name_for("current and name C1"))
except Exception as e:
    check("t4_exception", False, repr(e))

# =========================================================================
# Type 5 -- rng-shuffle (convention section 4.3 Type 5; node tca.shuffle --
# the SOLE stochastic node). The symmetric citrate + the prochiral pair (the
# 2 candidate carbons the RNG resolves 0.5/0.5 -- a STRUCTURAL fact, Phase 7
# source-approved via TCA-RNG-CITRATE-PROCHIRALITY-01). The selection is
# scoped to `citrate` via parentheses so `name C2` does NOT leak to the other
# `_smoke.pdb`-derived objects loaded earlier (current/substrate also have a
# C2 atom) -- a bare `citrate and name C1 or name C2` would parse as
# `(citrate and name C1) or (name C2)` and select C2 atoms across ALL objects.
# =========================================================================
try:
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(smoke_path, "citrate")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("sticks", "citrate")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("gray", "citrate")
    # src: tmp/pymol-src/modules/pymol/selecting.py:48 cmd.select  (parenthesized so name C2 is scoped to citrate only)
    cmd.select("prochiral_pair", "citrate and (name C1 or name C2)")
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show  (ADDS spheres on top of sticks)
    cmd.show("spheres", "prochiral_pair")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("hero_cyan", "prochiral_pair")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label
    cmd.label("prochiral_pair", '"? (RNG)"')
    # src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom
    cmd.zoom("prochiral_pair")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_cl5 = cmd.count_atoms("citrate")
    check("t5_citrate_loaded", n_cl5 > 0, "atoms=%d" % n_cl5)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_pp = cmd.count_atoms("prochiral_pair")
    check("t5_prochiral_pair_count_2", n_pp == 2, "prochiral=%d" % n_pp)
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_ps = cmd.count_atoms("prochiral_pair and rep spheres")
    check("t5_prochiral_spheres", n_ps > 0, "rep-spheres=%d" % n_ps)
    check("t5_prochiral_color_hero_cyan",
          color_name_for("prochiral_pair") == "hero_cyan",
          "color=%r" % color_name_for("prochiral_pair"))
except Exception as e:
    check("t5_exception", False, repr(e))

# =========================================================================
# Type 6 -- ending (4 tier-templates; convention section 4.3 Type 6). One
# template per tier: true (victory / ATP soul-jump), good (storage / C
# retained), normal (release / CO2), bad (catastrophe).
# =========================================================================
try:
    # --- true tier (the soul-jump climax) ---
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(smoke_path, "atp")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("sticks", "atp")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("hero_cyan", "atp")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label
    cmd.label("atp", '"YOU - soul"')
    # src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom
    cmd.zoom("atp")
    # ANTI-CONFUSION: the gold on `atp` represents the hero's ELECTRONS (the
    # soul), NOT the carbon. The carbon body was shed as CO2 at TCA. This is
    # the metamorphosis (PROJECT.md row 107). Do NOT claim the carbon becomes
    # ATP -- scientifically wrong; only the electrons continue.
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_ts = cmd.count_atoms("atp and rep sticks")
    check("t6_true_atp_sticks", n_ts > 0, "rep-sticks=%d" % n_ts)
    check("t6_true_color_hero_cyan",
          color_name_for("atp") == "hero_cyan",
          "color=%r" % color_name_for("atp"))
    check("t6_true_label",
          label_text_for("atp") == "YOU - soul",
          "label=%r" % label_text_for("atp"))
except Exception as e:
    check("t6_true_exception", False, repr(e))

try:
    # --- good tier (C retained) ---
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(smoke_path, "product")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("sticks", "product")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("hero_cyan", "product")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label
    cmd.label("product", '"retained"')
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_gs = cmd.count_atoms("product and rep sticks")
    check("t6_good_sticks", n_gs > 0, "rep-sticks=%d" % n_gs)
    check("t6_good_color_hero_cyan",
          color_name_for("product") == "hero_cyan",
          "color=%r" % color_name_for("product"))
except Exception as e:
    check("t6_good_exception", False, repr(e))

try:
    # --- normal tier (CO2 release -- the everyday exit) ---
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(smoke_path, "release")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("sticks", "release")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("gray", "release")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label
    cmd.label("release", '"CO2"')
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_ns = cmd.count_atoms("release and rep sticks")
    check("t6_normal_sticks", n_ns > 0, "rep-sticks=%d" % n_ns)
    check("t6_normal_color_gray",
          color_name_for("release") == "gray",
          "color=%r" % color_name_for("release"))
except Exception as e:
    check("t6_normal_exception", False, repr(e))

try:
    # --- bad tier (catastrophe -- the danger/death signal) ---
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(edit_path, "broken")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("cartoon", "broken")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("red", "broken")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1332 cmd.label
    cmd.label("broken and name CA", '"catastrophe"')
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_bc = cmd.count_atoms("broken and rep cartoon")
    check("t6_bad_cartoon", n_bc > 0, "rep-cartoon=%d" % n_bc)
    check("t6_bad_color_red",
          color_name_for("broken and name CA") == "red",
          "color=%r" % color_name_for("broken and name CA"))
except Exception as e:
    check("t6_bad_exception", False, repr(e))

# =========================================================================
# Stage 7 -- the 5.3 composition (convention section 5.4 -- the BEFORE/AFTER
# arc color contract).
# BEFORE (5.4 owns): the disease-mutant red spheres. Type 3b reset the
# `enzyme` object (hide everything -> cartoon gray, no spheres), so we
# RE-ESTABLISH the BEFORE (disease) state here to demonstrate the 5.4 BEFORE
# that the 5.3 AFTER restores.
# AFTER (5.3 owns; this smoke demonstrates the COLOR contract 5.4 fills):
# load the pre-built _wt_align_wt.pdb fixture as `enzyme_wt` (the "restored
# WT" -- the 5.3 align MECHANISM is NOT run here, just the color contract).
# The 5.3 composition: 5.4 OWNS the BEFORE (mutant red spheres); 5.3 OWNS
# the AFTER (WT-aligned reveal, colored green via 5.4's <wt_color> contract).
# This smoke proves the COLOR contract coheres (red -> green = broken ->
# restored); the 5.3 align MECHANISM is proven in tools/wt_align_smoke.py.
# =========================================================================
try:
    # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show  (re-establish the BEFORE mutant red spheres)
    cmd.show("spheres", "enzyme and resi 1")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
    cmd.color("magenta", "enzyme and resi 1")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_before = cmd.count_atoms("enzyme and resi 1 and rep spheres")
    check("comp_before_mutant_magenta_spheres",
          n_before > 0 and color_name_for("enzyme and resi 1 and name CA") == "magenta",
          "spheres=%d color=%r" % (n_before, color_name_for("enzyme and resi 1 and name CA")))
    # AFTER: load the pre-built WT fixture as `enzyme_wt` (the restored WT).
    wt_path = str(rpg.paths.data_path("data", "assets", "bundled", "_wt_align_wt.pdb"))
    # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
    cmd.load(wt_path, "enzyme_wt")
    # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
    cmd.show_as("cartoon", "enzyme_wt")
    # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color  (the <wt_color> 5.4 fills per convention section 5.4)
    cmd.color("green", "enzyme_wt")
    # src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
    n_after = cmd.count_atoms("enzyme_wt and rep cartoon")
    check("comp_after_wt_green",
          n_after > 0 and color_name_for("enzyme_wt and name CA") == "green",
          "cartoon=%d color=%r" % (n_after, color_name_for("enzyme_wt and name CA")))
except Exception as e:
    check("comp_exception", False, repr(e))

# --- Final verdict via STDOUT SENTINEL (NOT exit code -- the bat always returns 0) ---
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("SMOKE_FAILED_STAGES: " + ", ".join(FAILS))
