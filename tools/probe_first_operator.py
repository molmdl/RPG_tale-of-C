# tools/probe_first_operator.py -- empirical probe: does PyMOL 2.5.0 support the
# `first` selection operator, and does it resolve to EXACTLY ONE atom on the
# bundled _smoke.pdb fixture (ETHANOL: C1/O1/C2 -- 2 carbons)?
#
# Context (06-14 fix 2, SC2a bug): HeroResolver's OQ-6 default sele
# "<obj> and elem C" matched BOTH carbons -> both got spheres + "YOU".
# PREFERRED fix: "first (<obj> and elem C)" IF `first` works (03-01 precedent:
# C-backed selectors can't be confirmed from selector.py source -- test
# headlessly). FALLBACK: "<obj> and elem C and index 1".
#
# Pure pymol.cmd.* -- runs headless via: bash tools/run_headless.sh tools/probe_first_operator.py
import os
import sys

sys.path.insert(0, os.getcwd())

from pymol import cmd  # noqa: E402
import pymol  # noqa: E402

import c14.paths  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print("  [%s] %s %s" % (status, name, detail))
    if not cond:
        FAILS.append(name)


pymol.finish_launching()

pdb_path = str(c14.paths.data_path("data", "assets", "bundled", "_smoke.pdb"))
cmd.load(pdb_path, "hero_atom")

# Baseline: the fixture is ETHANOL with 2 carbons.
n_c = cmd.count_atoms("hero_atom and elem C")
check("fixture_has_2_carbons", n_c == 2, "n_C=%d" % n_c)
n_all = cmd.count_atoms("hero_atom")
check("fixture_has_3_atoms", n_all == 3, "n_all=%d" % n_all)

# The BUGGY sele (pre-fix): matches all carbons.
n_buggy = cmd.count_atoms("hero_atom and elem C")
check("buggy_sele_matches_both", n_buggy == 2, "n=%d" % n_buggy)

# The PREFERRED sele: `first` operator.
try:
    n_first = cmd.count_atoms("first (hero_atom and elem C)")
    check("first_operator_supported", True, "count=%d" % n_first)
    check("first_resolves_to_one_atom", n_first == 1, "count=%d" % n_first)
    # Which atom did `first` pick? Iterate names + ids.
    picked = []
    # src: tmp/pymol-src/modules/pymol/completing.py:18-29 -- the iterate
    # atom-namespace property is `ID` (UPPERCASE; lowercase `id` raises
    # NameError). Same list confirms `label` is a property, not a selector.
    cmd.iterate("first (hero_atom and elem C)",
                "picked.append((name, resi, ID))", space={"picked": picked})
    check("first_picked_atom_identity", len(picked) == 1,
          "picked=%r (expect C1 id=1 -- first by internal order)" % (picked,))
    # Sphere + label post-conditions on the first-sele (cheap sanity: the
    # highlight ops target this sele and must not raise).
    cmd.show("spheres", "first (hero_atom and elem C)")
    cmd.set("sphere_scale", "0.3", "first (hero_atom and elem C)")
    cmd.label("first (hero_atom and elem C)", '"YOU"')
    lbls = []
    cmd.iterate("first (hero_atom and elem C)", "lbls.append(label)",
                space={"lbls": lbls})
    check("sphere_and_label_on_first_sele",
          lbls == ["YOU"], "labels=%r" % (lbls,))
    cmd.hide("spheres", "first (hero_atom and elem C)")
    cmd.label("first (hero_atom and elem C)", '""')
except Exception as e:
    check("first_operator_supported", False, "RAISED: %r" % (e,))

# The FALLBACK sele (for comparison): index 1 (C1 in this fixture).
try:
    n_idx = cmd.count_atoms("hero_atom and elem C and index 1")
    check("fallback_index1_resolves_to_one", n_idx == 1, "count=%d" % n_idx)
    picked2 = []
    cmd.iterate("hero_atom and elem C and index 1",
                "picked2.append((name, ID))", space={"picked2": picked2})
    check("fallback_index1_picks_C1", picked2 == [("C1", 1)],
          "picked=%r" % (picked2,))
except Exception as e:
    check("fallback_index1_resolves_to_one", False, "RAISED: %r" % (e,))

cmd.delete("hero_atom")
print("SMOKE_RESULT: {0}".format("FAIL" if FAILS else "PASS"))
if FAILS:
    print("FAILED checks: %r" % (FAILS,))
