# Source: stdlib unittest + the pure-data catalog under c14/protonation_catalog.py.
# Python 3.6 compatible (unittest, re -- all stdlib; NO pymol import).
#
# Pure-WSL unit tests for c14.protonation_catalog. The module under test is
# pure data (NO pymol import; passes the Phase 1 AST gate), so these tests
# run under python3.6 with no pymol installed. Verifies:
#   * Catalog schema: every entry has mode in {"load","alter"}; alter entries
#     have resn + h_ops (list); load entries have source_file; every entry
#     has claim_id + label.
#   * lookup / variants_for / residues behavior + missing-key errors.
#   * Phase 4 boundary guards (the PLACEHOLDER_PHASE5 + no-pKa guards):
#     - test_phase4_placeholder_claim_ids: every claim_id == "PLACEHOLDER_PHASE5"
#       (this test is REMOVED in Phase 5+ when real claim_ids land; for now
#       it FAILS if a real claim_id leaks in).
#     - test_no_pka_values_in_catalog: scans the catalog serialization for
#       pKa/pH/DOI/numeric-pattern claims (regex) -- catches a developer
#       adding "HIS pKa ~6.0" or a DOI to a placeholder entry (Pitfall 5
#       guard -- no fabricated science).
#   * h_ops resn-phase ordering invariant: every remove op's sele contains
#     the OLD residue name (the residue_key); every add op's sele contains
#     the NEW resn (the entry's resn field). Encodes Pitfall 2 as a
#     catalog-level invariant.
"""Unit tests for c14.protonation_catalog (schema, lookup, Phase 4 boundary
guards, h_ops resn-phase ordering).

Pure WSL python3.6 -- NO pymol import. The catalog is pure data; these
tests verify the schema, the lookup/variants_for/residues API, and the
Phase 4 boundary guards (PLACEHOLDER_PHASE5 claim_ids + no fabricated
pKa/DOI values -- the test_no_pka_values_in_catalog + test_phase4_placeholder
_claim_ids guards).
"""
import json
import os
import re
import unittest

import c14.protonation_catalog as catalog


def _catalog_as_string():
    """Serialize the CATALOG to a string for the pKa/DOI regex scan."""
    return json.dumps(catalog.CATALOG, sort_keys=True)


class TestProtonationCatalog(unittest.TestCase):
    """Schema + lookup + variants_for + residues + Phase 4 boundary guards."""

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def test_catalog_schema_every_entry_has_required_fields(self):
        """Every entry has mode in {"load","alter"}; alter entries have resn +
        h_ops (list); load entries have source_file; every entry has claim_id
        + label."""
        for res_key, group in catalog.CATALOG.items():
            self.assertIsInstance(group, dict,
                                  "group for {!r} must be a dict".format(res_key))
            for vid, spec in group.items():
                self.assertIn(spec.get("mode"), ("load", "alter"),
                              "{}/{}: mode must be load|alter".format(res_key, vid))
                self.assertIn("claim_id", spec,
                              "{}/{}: missing claim_id".format(res_key, vid))
                self.assertIn("label", spec,
                              "{}/{}: missing label".format(res_key, vid))
                if spec["mode"] == "alter":
                    self.assertIn("resn", spec,
                                  "{}/{}: alter entry missing resn".format(res_key, vid))
                    self.assertIsInstance(spec.get("h_ops", []), list,
                                         "{}/{}: h_ops must be a list".format(res_key, vid))
                elif spec["mode"] == "load":
                    self.assertIn("source_file", spec,
                                  "{}/{}: load entry missing source_file".format(res_key, vid))

    # ------------------------------------------------------------------
    # lookup
    # ------------------------------------------------------------------
    def test_lookup_found(self):
        """lookup("HIS","HIS_HID") returns the spec with mode=alter, resn=HID;
        lookup("ASP","ASP_ASH") returns resn=ASH."""
        hid = catalog.lookup("HIS", "HIS_HID")
        self.assertEqual(hid["mode"], "alter")
        self.assertEqual(hid["resn"], "HID")
        ash = catalog.lookup("ASP", "ASP_ASH")
        self.assertEqual(ash["mode"], "alter")
        self.assertEqual(ash["resn"], "ASH")

    def test_lookup_missing_residue_raises(self):
        """lookup("XXX","...") raises KeyError with 'unknown residue'."""
        with self.assertRaises(KeyError) as ctx:
            catalog.lookup("XXX", "XXX_FOO")
        self.assertIn("unknown residue", str(ctx.exception))

    def test_lookup_missing_variant_raises(self):
        """lookup("HIS","HIS_XXX") raises KeyError with 'unknown variant'."""
        with self.assertRaises(KeyError) as ctx:
            catalog.lookup("HIS", "HIS_XXX")
        self.assertIn("unknown variant", str(ctx.exception))

    # ------------------------------------------------------------------
    # variants_for
    # ------------------------------------------------------------------
    def test_variants_for_returns_labels(self):
        """variants_for("HIS") returns a list including (HIS_HID, <label>),
        (HIS_HIE, <label>), (HIS_HIP, <label>)."""
        variants = catalog.variants_for("HIS")
        self.assertIsInstance(variants, list)
        vids = [v[0] for v in variants]
        self.assertIn("HIS_HID", vids)
        self.assertIn("HIS_HIE", vids)
        self.assertIn("HIS_HIP", vids)
        # Each tuple is (variant_id, label) and label is a non-empty string.
        for vid, label in variants:
            self.assertIsInstance(label, str)
            self.assertTrue(len(label) > 0,
                            "label for {!r} must be non-empty".format(vid))
        # Spot-check the HID label contains "Histidine" + "delta".
        hid_label = dict(variants)["HIS_HID"]
        self.assertIn("Histidine", hid_label)
        self.assertIn("delta", hid_label)

    def test_variants_for_unknown_residue_returns_empty(self):
        """variants_for("XXX") returns [] (no raise)."""
        self.assertEqual(catalog.variants_for("XXX"), [])

    # ------------------------------------------------------------------
    # residues
    # ------------------------------------------------------------------
    def test_residues_returns_sorted_keys(self):
        """residues() returns a sorted list of the catalog's residue keys."""
        keys = catalog.residues()
        self.assertIsInstance(keys, list)
        self.assertEqual(keys, sorted(keys))
        # All six placeholder residues are present.
        for expected in ("ASP", "CYS", "GLU", "HIS", "LYS", "TYR"):
            self.assertIn(expected, keys,
                          "missing residue {!r} in catalog".format(expected))

    # ------------------------------------------------------------------
    # Phase 4 boundary guards
    # ------------------------------------------------------------------
    def test_phase4_placeholder_claim_ids(self):
        """Every catalog entry's claim_id == "PLACEHOLDER_PHASE5".

        Phase 4 boundary guard -- this test is REMOVED in Phase 5+ when real
        claim_ids land; for now it FAILS if a real claim_id leaks in (catches
        a developer adding a cited claim_id to a placeholder entry before the
        Phase 5 per-claim approval gate has run).
        """
        for res_key, group in catalog.CATALOG.items():
            for vid, spec in group.items():
                self.assertEqual(
                    spec["claim_id"], "PLACEHOLDER_PHASE5",
                    "{}/{}: claim_id must be PLACEHOLDER_PHASE5 in Phase 4 "
                    "(got {!r})".format(res_key, vid, spec["claim_id"]))

    def test_no_pka_values_in_catalog(self):
        """Scan the catalog serialization for pKa/pH/numeric-pattern/DOI
        claims; assert none present (Pitfall 5 guard -- no fabricated science).

        Catches a developer adding "HIS pKa ~6.0" or "doi:..." to a
        placeholder entry. The Phase 4 catalog ships MECHANICS + standard
        nomenclature labels ONLY; pKa values + DOIs are Phase 5+ cited
        content (CITE-01).
        """
        blob = _catalog_as_string().lower()
        # Banned patterns: pKa (any case), pH<digit>, ~<float> (approx-numeric
        # values), doi: or DOI in any form.
        banned_patterns = [
            r"pka",            # pKa / pka (any case)
            r"ph\s*[0-9]",     # pH 6, pH6, ph7, etc.
            r"~\d+\.\d+",      # ~6.0, ~3.14 (approximate numeric values)
            r"doi\s*:",        # doi: ... / DOI: ...
        ]
        for pat in banned_patterns:
            matches = re.findall(pat, blob)
            self.assertEqual(
                matches, [],
                "Pitfall 5 guard: banned pattern {!r} found in catalog: {}"
                .format(pat, matches))

    # ------------------------------------------------------------------
    # h_ops resn-phase ordering invariant (Pitfall 2)
    # ------------------------------------------------------------------
    def test_h_ops_remove_uses_old_resn_add_uses_new_resn(self):
        """For each alter entry with h_ops, every op='remove' entry's sele
        contains the OLD residue name (the residue_key, e.g. 'HIS') and every
        op='add' entry's sele contains the NEW resn (the entry's resn field,
        e.g. 'HID'). Encodes the Pitfall 2 ordering convention as a
        catalog-level invariant."""
        for res_key, group in catalog.CATALOG.items():
            for vid, spec in group.items():
                if spec.get("mode") != "alter":
                    continue
                new_resn = spec.get("resn")
                for h in spec.get("h_ops", []):
                    sele = h.get("sele", "")
                    if h["op"] == "remove":
                        # remove uses the OLD resn (the residue_key).
                        self.assertIn(
                            "resn {}".format(res_key), sele,
                            "{}/{}: remove op sele must reference OLD resn "
                            "{!r}, got {!r}".format(res_key, vid, res_key, sele))
                    elif h["op"] == "add":
                        # add uses the NEW resn (the entry's resn field).
                        self.assertIn(
                            "resn {}".format(new_resn), sele,
                            "{}/{}: add op sele must reference NEW resn "
                            "{!r}, got {!r}".format(res_key, vid, new_resn, sele))


if __name__ == "__main__":
    unittest.main()
