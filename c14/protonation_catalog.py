"""c14/protonation_catalog.py -- Phase 4 Plan 04-03 protonation variant catalog.

PLACEHOLDER catalog -- standard AMBER nomenclature only; NO pKa values, NO
DOIs; the reaction-relevant choice per enzyme is Phase 5+ cited content
(CITE-01). This module is pure DATA (which variants exist, which claim_id
backs each); the MECHANISM (how to apply a variant via cmd.*) lives in
``c14/pymol_layer/protonation.py`` (the ProtonationManager -- gate-exempt
tier). Splitting data from mechanism keeps this module unit-testable in pure
WSL python3.6 with NO pymol import (passes the Phase 1 AST import gate).

Schema (per 04-RESEARCH-protonation.md "Pattern 2: Catalog Split")::

    CATALOG[residue_key][variant_id] = {
        "mode": "load" | "alter",     # (a) load pre-built | (b) alter resn + h_ops
        "resn": "<new resn>",          # (b): the new residue name (e.g. "HID")
        "h_ops": [                      # (b): ordered H add/remove ops
            {"op": "remove", "sele": "<OLD-resn selection>"},
            {"op": "add",    "sele": "<NEW-resn selection>"},
        ],
        "source_file": "<bundled .pdb>", # (a): the pre-built structure filename
        "claim_id": "PLACEHOLDER_PHASE5", # CITE-01; real claim_id is Phase 5+
        "label": "<human label>",        # for the Phase 6 UI switch
    }

CRITICAL h_ops ordering convention (Pitfall 2 mitigation): In each h_ops
list, ``op="remove"`` entries use the OLD resn in their selection (e.g.
"resn HIS and name HE2") and MUST run BEFORE the alter step; ``op="add"``
entries use the NEW resn (e.g. "resn HID and name ND1") and MUST run AFTER
the alter step. The ProtonationManager._apply_alter (04-03 Task 2) partitions
h_ops by op and reorders: removes -> alter -> adds. This catalog encodes
that invariant at the data level -- the catalog author writes the selections
with the correct resn phase (remove=old resn, add=new resn).

Python 3.6 stdlib only: plain module, no @dataclass, .format() strings.
"""
# noqa: E501  (long docstring lines are intentional reference material)


CATALOG = {
    # ---- Histidine (HIS): HID / HIE / HIP standard AMBER tautomers ----
    "HIS": {
        "HIS_HID": {
            "mode": "alter",
            "resn": "HID",
            "h_ops": [
                {"op": "remove", "sele": "resn HIS and name HE2"},
                {"op": "add", "sele": "resn HID and name ND1"},
            ],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Histidine - delta-protonated (Nd-H, Ne-free)",
        },
        "HIS_HIE": {
            "mode": "alter",
            "resn": "HIE",
            "h_ops": [
                {"op": "remove", "sele": "resn HIS and name HD1"},
                {"op": "add", "sele": "resn HIE and name NE2"},
            ],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Histidine - epsilon-protonated (Ne-H, Nd-free)",
        },
        "HIS_HIP": {
            "mode": "alter",
            "resn": "HIP",
            "h_ops": [
                {"op": "add", "sele": "resn HIP and name ND1"},
                {"op": "add", "sele": "resn HIP and name NE2"},
            ],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Histidine - doubly protonated (cationic, both N-H)",
        },
    },
    # ---- Aspartate (ASP): ASP / ASH standard AMBER protonation states ----
    "ASP": {
        "ASP_ASP": {
            "mode": "alter",
            "resn": "ASP",
            "h_ops": [],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Aspartate - deprotonated (carboxylate, standard)",
        },
        "ASP_ASH": {
            "mode": "alter",
            "resn": "ASH",
            "h_ops": [
                {"op": "add", "sele": "resn ASH and name HD1"},
            ],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Aspartate - protonated (carboxylic acid)",
        },
    },
    # ---- Glutamate (GLU): GLU / GLH standard AMBER protonation states ----
    "GLU": {
        "GLU_GLU": {
            "mode": "alter",
            "resn": "GLU",
            "h_ops": [],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Glutamate - deprotonated (carboxylate, standard)",
        },
        "GLU_GLH": {
            "mode": "alter",
            "resn": "GLH",
            "h_ops": [
                {"op": "add", "sele": "resn GLH and name HE1"},
            ],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Glutamate - protonated (carboxylic acid)",
        },
    },
    # ---- Lysine (LYS): LYS / LYN standard AMBER protonation states ----
    "LYS": {
        "LYS_LYS": {
            "mode": "alter",
            "resn": "LYS",
            "h_ops": [],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Lysine - protonated (ammonium, standard)",
        },
        "LYS_LYN": {
            "mode": "alter",
            "resn": "LYN",
            "h_ops": [
                {"op": "remove", "sele": "resn LYS and name HZ1"},
            ],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Lysine - deprotonated (amine)",
        },
    },
    # ---- Cysteine (CYS): CYS / CYM standard AMBER protonation states ----
    "CYS": {
        "CYS_CYS": {
            "mode": "alter",
            "resn": "CYS",
            "h_ops": [],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Cysteine - protonated (thiol, standard)",
        },
        "CYS_CYM": {
            "mode": "alter",
            "resn": "CYM",
            "h_ops": [
                {"op": "remove", "sele": "resn CYS and name HG"},
            ],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Cysteine - deprotonated (thiolate)",
        },
    },
    # ---- Tyrosine (TYR): TYR / TYM standard AMBER protonation states ----
    "TYR": {
        "TYR_TYR": {
            "mode": "alter",
            "resn": "TYR",
            "h_ops": [],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Tyrosine - protonated (phenol, standard)",
        },
        "TYR_TYM": {
            "mode": "alter",
            "resn": "TYM",
            "h_ops": [
                {"op": "remove", "sele": "resn TYR and name HH"},
            ],
            "claim_id": "PLACEHOLDER_PHASE5",
            "label": "Tyrosine - deprotonated (phenolate)",
        },
    },
}


def lookup(residue_key, variant_id):
    # type: (str, str) -> dict
    """Return the variant spec dict for (residue_key, variant_id).

    Raises KeyError with a clear message if the residue_key is unknown or
    the variant_id is not registered under that residue. The ProtonationManager
    (04-03 Task 2) delegates here; the KeyError propagates so a missing-variant
    request fails loudly at the catalog boundary.
    """
    group = CATALOG.get(residue_key)
    if group is None:
        raise KeyError(
            "protonation_catalog: unknown residue {!r}".format(residue_key))
    spec = group.get(variant_id)
    if spec is None:
        raise KeyError(
            "protonation_catalog: unknown variant {!r} for residue {!r}".format(
                variant_id, residue_key))
    return spec


def variants_for(residue_key):
    # type: (str) -> list
    """Return a list of (variant_id, label) tuples for ``residue_key``.

    Returns an empty list if the residue_key is not in the catalog (no raise
    -- lets the UI iterate an unknown residue gracefully). The label defaults
    to the variant_id if missing (defensive, though every entry sets it).
    """
    group = CATALOG.get(residue_key, {})
    out = []
    for vid, spec in group.items():
        out.append((vid, spec.get("label", vid)))
    return out


def residues():
    # type: () -> list
    """Return a sorted list of residue keys in the catalog (for UI / coverage)."""
    return sorted(CATALOG.keys())
