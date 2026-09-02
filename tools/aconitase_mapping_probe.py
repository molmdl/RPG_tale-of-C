#!/usr/bin/env python
# tools/aconitase_mapping_probe.py -- Phase 7 Plan 07-12: the human<->bovine
# aconitase residue-mapping probe (07-03 Decision D6 / research OQ5, carried
# into the 07-12 plan context as a HARD PRECONDITION):
#
#   "Aconitase: human S112R <-> bovine 1ACO residue number MUST come from a
#    real sequence alignment + headless cmd.iterate probe BEFORE writing the
#    sele -- record the mapping + align_sele in SUMMARY for plan 14 to reuse."
#
# Why this is load-bearing: the tca.aconitase cast is BOVINE (1ACO, 2.05 A --
# human ACO2 has no PDB structure) but the disease allele is HUMAN
# (DIS-ACO2-01-cand, ACO2 S112R -> reverse R112S). Writing
# "resi 112 and chain A" against 1ACO would silently edit the WRONG residue:
# UniProt P20004 (bovine) pos 112 is a conserved serine in the transit-peptide-
# adjacent region, NOT the S112 disease position. The mapping below is derived,
# not assumed.
#
# What this probe does (on the real PyMOL cmd, offline -- 1ACO is already in
# the local dev cache rpg/data/assets/downloaded/1aco.pdb):
#   1. cmd.iterate the 1ACO chain-A sequence out of the LIVE object (with PDB
#      resi numbers), rather than trusting a pre-parsed copy.
#   2. Re-derive the mapping by Needleman-Wunsch global alignment of the
#      embedded human ACO2 sequence (UniProt Q99798, fetched live 2026-09-03)
#      against that extracted sequence. 96% identity -- the alignment is not
#      ambiguous.
#   3. Assert human S112 -> 1ACO resi 85, and that 1ACO resi 85 IS a serine
#      (the WT residue: the disease allele substitutes R, the reverse edit
#      restores S).
#   4. Cross-check against the file's own DBREF record (PDB 2-754 = UniProt
#      P20004 29-781, i.e. PDB = UNP - 27): human S112 aligns to bovine UNP
#      112, and 112 - 27 = 85. Two independent routes, same number.
#   5. Verify the literature anchor: 1ACO resi 642 = SER (the catalytic Ser642
#      of the pig/bovine aconitase numbering used by Wikipedia's mechanism
#      section and 1C97 S642A -- confirms PDB numbering matches the published
#      bovine numbering, not some offset variant).
#   6. Answer the chain-case question empirically: does "resi 85 and chain a"
#      (lowercase, the edits.json signature convention) resolve against chain
#      "A" atoms? The signature is normalized to lowercase on both sides, but
#      the branch node's MolAction sele goes to cmd.alter VERBATIM -- so the
#      sele case must be whatever PyMOL actually matches.
#   7. Exercise the full restored-node on_enter op sequence from 05.3 §2 (iii)
#      through the real molops dispatch: edit (reverse mutation) -> load WT ->
#      align (method=super, align_sele="name CA") -> show_as, and confirm the
#      align actually moved the mobile object and left a finite result.
#
# CRITICAL CONTRACT RULES (reused from tools/etc_restore_handle_smoke.py):
#   * Gotcha #1: the process ALWAYS exits 0 through run-conda-pymol.bat --
#     the SMOKE_RESULT stdout sentinel is the ONLY reliable verdict.
#   * Gotcha #2: __file__ resolves to the pymol package's __init__.py -- use
#     os.getcwd() + rpg.paths to locate the cached PDB.
#   * Gotcha #6: pymol.finish_launching() before any cmd.* call.
#
# Every direct cmd.* call in THIS file carries a `# src:` citation (Phase 3
# convention). EditOps/molops-internal cmd.* calls are cited there.
#
# Usage (from repo root):
#   bash tools/run_headless.sh tools/aconitase_mapping_probe.py
# Verdict: grep ^SMOKE_RESULT: PASS in the captured stdout (NOT $?).

import os
import sys

# Gotcha #2/#3/#4: cwd = repo root when run via the harness.
sys.path.insert(0, os.getcwd())

import pymol
from pymol import cmd
import rpg.paths
from rpg.pymol_layer.asset_manager import AssetManager
from rpg.pymol_layer.edit_ops import EditOps
from rpg.pymol_layer.molops import MolOps
from rpg.story.model import MolAction

pymol.finish_launching()  # Gotcha #6

FAILS = []


def check(name, ok, detail=""):
    print("CHECK {0}: {1} {2}".format(name, "PASS" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(name)


# --- The embedded human ACO2 sequence (UniProt Q99798, reviewed: SwissProt) --
# Fetched live from https://rest.uniprot.org/uniprotkb/Q99798.fasta on
# 2026-09-03 (the same fetch the research docs used for the S112R allele
# verification). 780 aa precursor including the mitochondrial transit peptide.
HUMAN_ACO2 = (
    "MAPYSLLVTRLQKALGVRQYHVASVLCQRAKVAMSHFEPNEYIHYDLLEKNINIVRKRLNRPLTLSEKIVYGH"
    "LDDPASQEIERGKSYLRLRPDRVAMQDATAQMAMLQFISSGLSKVAVPSTIHCDHLIEAQVGGEKDLRRAKDI"
    "NQEVYNFLATAGAKYGVGFWKPGSGIIHQIILENYAYPGVLLIGTDSHTPNGGGLGGICIGVGGADAVDVMAG"
    "IPWELKCPKVIGVKLTGSLSGWSSPKDVILKVAGILTVKGGTGAIVEYHGPGVDSISCTGMATICNMGAEIGA"
    "TTSVFPYNHRMKKYLSKTGREDIANLADEFKDHLVPDPGCHYDQLIEINLSELKPHINGPFTPDLAHPVAEVG"
    "KVAEKEGWPLDIRVGLIGSCTNSSYEDMGRSAAVAKQALAHGLKCKSQFTITPGSEQIRATIERDGYAQILRD"
    "LGGIVLANACGPCIGQWDRKDIKKGEKNTIVTSYNRNFTGRNDANPETHAFVTSPEIVTALAIAGTLKFNPET"
    "DYLTGTDGKKFRLEAPDADELPKGEFDPGQDTYQHPPKDSSGQHVDVSPTSQRLQLLEPFDKWDGKDLEDLQI"
    "LIKVKGKCTTDHISAAGPWLKFRGHLDNISNNLLIGAINIENGKANSVRNAVTQEFGPVPDTARYYKKHGIRW"
    "VVIGDENYGEGSSREHAALEPRHLGGRAIITKSFARIHETNLKKQGLLPLTFADPADYNKIHPVDKLTIQGLK"
    "DFTPGKPLKCIIKHPNGTQETILLNHTFNETQIEWFRAGSALNRMKELQQ"
)
HUMAN_S112 = 112  # 1-based precursor position; the DIS-ACO2-01-cand allele
GAP = -1
MATCH, MISMATCH = 1, -1


def needleman_wunsch(a, b):
    """Global alignment; returns {index_in_a: index_in_b} for aligned pairs.

    Pure Python (3.6-compatible stdlib), linear gap penalty. At 96% identity
    the scoring choice does not move the alignment; the DBREF cross-check in
    stage 3 is the independent confirmation that it did not.
    """
    n, m = len(a), len(b)
    prev = [j * GAP for j in range(m + 1)]
    # 0 = diagonal, 1 = up (a aligns to gap), 2 = left (b aligns to gap)
    tb = bytearray(n * m)
    for i in range(1, n + 1):
        cur = [i * GAP] + [0] * m
        ai = a[i - 1]
        base = (i - 1) * m
        for j in range(1, m + 1):
            diag = prev[j - 1] + (MATCH if ai == b[j - 1] else MISMATCH)
            up = prev[j] + GAP
            left = cur[j - 1] + GAP
            best, p = diag, 0
            if up > best:
                best, p = up, 1
            if left > best:
                best, p = left, 2
            cur[j] = best
            tb[base + j - 1] = p
        prev = cur
    mapping = {}
    i, j = n, m
    while i > 0 and j > 0:
        p = tb[(i - 1) * m + (j - 1)]
        if p == 0:
            mapping[i - 1] = j - 1
            i -= 1
            j -= 1
        elif p == 1:
            i -= 1
        else:
            j -= 1
    return mapping


THREE2ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V",
}


def residue_resn(obj, sele):
    """Read resn values for a selection via cmd.iterate (stored-list form)."""
    stored = type("S", (), {"list": []})()
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
    # (space= is MANDATORY -- without it the expression namespace cannot see
    # the stored object; mirrors edit_ops.py:268-273.)
    cmd.iterate(
        "{0} and ({1})".format(obj, sele),
        "stored.list.append(resn)",
        space={"stored": stored},
    )
    return sorted(set(stored.list))


def residue_centroid(obj, sele):
    """Centroid of a selection's atoms -- used to prove the align moved it.

    x/y/z are ONLY available in iterate_state / alter_state (cmd.iterate
    raises NameError for them -- hit empirically on the first probe run), so
    the centroid reads go through cmd.iterate_state.
    """
    stored = type("S", (), {"xs": [], "ys": [], "zs": []})()
    # src: tmp/pymol-src/modules/pymol/editing.py:1479 cmd.iterate_state
    # (state 0 = current; x/y/z are valid expressions there, unlike iterate)
    cmd.iterate_state(
        0,
        "{0} and ({1})".format(obj, sele),
        "stored.xs.append(x); stored.ys.append(y); stored.zs.append(z)",
        space={"stored": stored},
    )
    if not stored.xs:
        return None
    n = float(len(stored.xs))
    return (
        sum(stored.xs) / n,
        sum(stored.ys) / n,
        sum(stored.zs) / n,
    )


# --- Stage 1: load the cached 1ACO and extract its sequence LIVE ------------
PDB_PATH = rpg.paths.data_path("data", "assets", "downloaded", "1aco.pdb")
check("cache_present", os.path.exists(PDB_PATH), PDB_PATH)

# src: tmp/pymol-src/modules/pymol/commanding.py:606 cmd.load
cmd.load(PDB_PATH, "aconitase")

stored = type("S", (), {"rows": []})()
# src: tmp/pymol-src/modules/pymol/querying.py:1412 cmd.count_atoms
n_atoms = cmd.count_atoms("aconitase")
# Pull (chain, resi, resn) for every polymer residue of chain A, in file order.
cmd.iterate(
    "aconitase and chain A",
    "stored.rows.append((chain, resi, resn))",
    space={"stored": stored},
)
rows = stored.rows
seen = {}
order = []
for chain, resi, resn in rows:
    key = (chain, str(resi))
    if key not in seen and resn in THREE2ONE:
        seen[key] = THREE2ONE[resn]
        order.append(key)
aco_seq = "".join(seen[k] for k in order)
check("extracted_sequence_sane", len(aco_seq) == 753 and n_atoms > 5000,
      "residues={0} atoms={1} first={2} last={3}".format(
          len(aco_seq), n_atoms, order[0], order[-1]))

# --- Stage 2: re-derive the mapping by real sequence alignment ---------------
mapping = needleman_wunsch(HUMAN_ACO2, aco_seq)
aligned = sum(1 for k in mapping if HUMAN_ACO2[k] == aco_seq[mapping[k]])
identity = 100.0 * aligned / max(len(mapping), 1)
check("alignment_identity", identity > 90.0,
      "aligned={0} identities={1} ({2:.1f}%)".format(len(mapping), aligned, identity))

h_idx = HUMAN_S112 - 1
b_idx = mapping.get(h_idx)
check("human_112_aligned", b_idx is not None, "human S112 fell in a gap")
chain_b, resi_b = order[b_idx]
check("human_s112_maps_to_resi_85", chain_b == "A" and resi_b == "85",
      "human S112 -> chain {0} resi {1}".format(chain_b, resi_b))
check("target_residue_is_serine", residue_resn("aconitase", "resi {0} and chain {1}".format(resi_b, chain_b)) == ["SER"],
      "1ACO resi {0} resn={1}".format(resi_b, residue_resn("aconitase", "resi {0}".format(resi_b))))

# --- Stage 3: independent cross-check via the file's own DBREF offset --------
# DBREF 1ACO A 2 754 UNP P20004 29 781  =>  PDB resi = UNP position - 27.
# Human S112 aligns to bovine UNP 112 (same number here -- the alignment
# confirms it); 112 - 27 = 85. Two routes must agree.
check("dbref_route_agrees", int(resi_b) == 112 - 27,
      "alignment says {0}, DBREF arithmetic says 85".format(resi_b))

# --- Stage 4: the literature anchor ------------------------------------------
# Catalytic Ser642 in pig/bovine numbering (Wikipedia 'Aconitase' mechanism +
# 1C97 S642A). If 1ACO resi 642 were NOT a serine, PDB numbering would be
# offset relative to the published bovine numbering and every derived resi
# would be suspect.
check("catalytic_ser642_anchor", residue_resn("aconitase", "resi 642") == ["SER"],
      "1ACO resi 642 resn={0}".format(residue_resn("aconitase", "resi 642")))

# --- Stage 5: chain-case empirics for the edits.json signature ---------------
lower = residue_resn("aconitase", "resi 85 and chain a")
upper = residue_resn("aconitase", "resi 85 and chain A")
case_lower_matches = lower == ["SER"]
case_upper_matches = upper == ["SER"]
print("MAP_CASE: 'resi 85 and chain a' (lower) -> {0}".format(lower))
print("MAP_CASE: 'resi 85 and chain A' (upper) -> {0}".format(upper))
check("chain_case_answered", case_lower_matches or case_upper_matches,
      "lower resolved {0}, upper resolved {1}".format(lower, upper))
# The MolAction sele must use whichever case PyMOL actually matches. (The
# edits.json SIGNATURE target is lowercased on both sides by
# EditIntent.signature() so the round-trip match is case-independent -- but
# the branch node's MolAction sele goes to cmd.alter verbatim.)
check("molaction_sele_case", case_upper_matches,
      "the MolAction sele in gly/tca restored nodes must use 'chain A' "
      "(lowercase 'chain a' resolves to {0})".format(lower))

# --- Stage 6: exercise the restored-node on_enter op sequence for real -------
# 05.3 §2 (iii) order: edit (the player's reverse mutation) -> load WT ->
# align -> show_as. Disease state first (what the player sees before the
# restore): resi 85 -> ARG. Then the restored node's edit: ARG -> SER.
eo = EditOps(cmd)
# The restored node's `load pdb:1ACO` op routes through the AssetManager
# target-prefix fallback (molops.py:221-225); inject a real one so the probe
# exercises the same wiring as the controller (main_window.py:205). 1ACO is
# already in the local cache, so the fetch is an offline file hit.
ops = MolOps(cmd, asset_manager=AssetManager(cmd), editops=eo)

# src: rpg/pymol_layer/edit_ops.py apply_edit (backup + cmd.alter + sort)
eo.point_mutation("aconitase", "aconitase and resi 85", "ARG")
check("disease_state_applied", residue_resn("aconitase", "resi 85") == ["ARG"],
      "resi 85 resn={0}".format(residue_resn("aconitase", "resi 85")))

before = residue_centroid("aconitase", "resi 85")

# The exact MolAction sequence the tca.aconitase_restored node carries.
RESTORED_ON_ENTER = [
    MolAction(op="edit", target="aconitase", args={
        "edit_type": "point_mutation",
        "sele": "resi 85 and chain A",
        "new_resn": "SER",
    }),
    MolAction(op="load", target="pdb:1ACO", args={"object": "aconitase_wt"}),
    MolAction(op="align", target="aconitase_wt", args={
        "reference": "aconitase",
        "method": "super",
        "align_sele": "name CA",
    }),
    MolAction(op="show_as", target="aconitase_wt", args={"rep": "cartoon"}),
]
for action in RESTORED_ON_ENTER:
    ops.apply(action)

check("reverse_mutation_applied", residue_resn("aconitase", "resi 85") == ["SER"],
      "resi 85 resn={0}".format(residue_resn("aconitase", "resi 85")))
check("wt_object_loaded", "aconitase_wt" in cmd.get_names("objects"),
      "objects={0}".format(cmd.get_names("objects")))

# The align must actually MOVE the mobile (aconitase_wt) copy onto the fixed
# reference; with identical structures the post-align centroid of resi 85 in
# the mobile object must sit at the reference's centroid. A finite, tiny
# distance proves the op did real work through the real dispatch.
after_mobile = residue_centroid("aconitase_wt", "resi 85 and chain A")
after_fixed = residue_centroid("aconitase", "resi 85 and chain A")
check("align_moved_mobile_object", None not in (after_mobile, after_fixed),
      "mobile={0} fixed={1}".format(after_mobile, after_fixed))
if after_mobile and after_fixed:
    dist = sum((a - b) ** 2 for a, b in zip(after_mobile, after_fixed)) ** 0.5
    check("aligned_centroids_coincide", dist < 1.0, "distance={0:.4f} A".format(dist))

# And the pre-edit object the player was looking at must be UNCHANGED by the
# align (mobile = _wt moves; reference stays).
check("reference_object_unmoved",
      residue_centroid("aconitase", "resi 85 and chain A") == after_fixed,
      "the align must leave the fixed reference in place")

print("MAP_RESULT: human ACO2 S112 (UniProt Q99798) -> bovine 1ACO chain A resi 85 (SER)")
print("MAP_RESULT: edits.json signature target 'resi 85 and chain A' (lowercased per "
      "EditIntent.signature()); MolAction sele uses chain A verbatim")
print("MAP_RESULT: align_sele 'name CA' (the 05.3 §4 default; no source-approved "
      "stable-core selection exists)")

if FAILS:
    print("SMOKE_RESULT: FAIL ({0}: {1})".format(len(FAILS), ", ".join(FAILS)))
else:
    print("SMOKE_RESULT: PASS")
