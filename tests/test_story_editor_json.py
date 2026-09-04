#!/usr/bin/env python3.6
"""TDD battery for tools/story_editor_json.py (Phase 7.1 plan 07.1-02).

The module under test is the CANONICAL house-style JSON serializer for the
story-node HTML editor: ``dumps(data) -> str`` must reproduce every data JSON
in this repo BYTE-IDENTICALLY on a no-op save (load -> serialize -> compare),
so that "save edit" produces reviewable, minimal diffs (07-17 precedent: a
byte-identical diff is the gold outcome).

The rule family pinned here was reverse-engineered from the real data files
and VERIFIED 2026-09-04 against the live repo: all 12 data files reproduce
byte-identically with these rules (see TestByteIdenticalNoopOracle):

  constants:  W  = 175  (container inline width)
              SW = 110  (scalar-list inline width)
  R1. Encoding: ensure_ascii=False (non-ASCII stays literal UTF-8); 2-space
      indent; ``dumps`` returns WITHOUT a trailing newline -- the file write
      appends it (contract pinned below).
  R2. Raw floats: ``loads`` wraps every float token in RawFloat(token);
      ``dumps`` emits the token verbatim ("2.40" stays "2.40", never "2.4").
      Key order: insertion order (collections.OrderedDict as the
      object_pairs_hook -- the 3.6-safe guarantee).
  R3. Scalar lists (no dict/list elements): inline iff
      ``indent + len(compact) <= SW``; else one element per line.
  R4. Container arrays (any dict/list element): ALWAYS multiline; each
      element is inlined iff it itself fits (R5) at ``array_indent + 2``.
  R5. Dict inline rule (``fits``): ``indent + len(compact(v)) <= W`` AND the
      dict contains no container-array child (an array containing dicts or
      lists) AND every descendant container fits at its own depth
      (propagation). Multiline dicts render children at +2 and close the
      brace at the parent indent.
  R6. ``edits`` hand-style exception: array elements under the key "edits"
      are ALWAYS multiline dicts (the ``signature`` dict still inlines per
      R5). Without this exception 10/13 edits.json entries would wrongly
      inline and the file would diverge.
  R7. Empty containers ``{}`` and ``[]`` are always inline.

fixture_vectors() (module API, shared with the JS port 07.1-05) returns
``(name, python_object, expected_string)`` triples covering the tricky cases;
the GROUND_TRUTH table below is the independent copy the module table must
match exactly.

RED state: this module fails at import until tools/story_editor_json.py
exists (ImportError) -- that IS the Task-1 red.

Python 3.6 stdlib ONLY (unittest/os/sys/json/re/collections). NO pytest
(not installed). NO f-strings (.format() / % per repo convention). NO
pymol/PyQt5 imports (pure-Python module; the AST import gate scans tests/).
"""
import json
import os
import re
import sys
import unittest
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(HERE, "..")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")

# Make tools/ importable (same pattern as tests/test_check_alter_gate.py).
sys.path.insert(0, TOOLS_DIR)
import story_editor_json  # noqa: E402  (RED: ImportError until Task 2 lands)

RAWFLOAT = story_editor_json.RawFloat

# ---------------------------------------------------------------------------
# The 12 byte-identical no-op oracle targets (Task 1 rule 1).
# ---------------------------------------------------------------------------
ORACLE_TARGETS = [
    ("manifest", ("data", "story_glucose", "manifest.json")),
    ("intro", ("data", "story_glucose", "intro.json")),
    ("glycolysis", ("data", "story_glucose", "glycolysis.json")),
    ("pyruvate_branch", ("data", "story_glucose", "pyruvate_branch.json")),
    ("tca", ("data", "story_glucose", "tca.json")),
    ("etc_atp", ("data", "story_glucose", "etc_atp.json")),
    ("endings", ("data", "story_glucose", "endings.json")),
    ("bad_endings", ("data", "story_glucose", "bad_endings.json")),
    ("citations", ("data", "citations.json")),
    ("sources", ("data", "sources.json")),
    ("edits", ("rpg", "data", "edits.json")),
    ("cast", ("rpg", "data", "cast.json")),
]


def _read(path):
    # type: (str) -> str
    """Read a file as UTF-8 text (the oracle's read/write encoding)."""
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")


# ---------------------------------------------------------------------------
# Fixture-vector ground truth (Task 1 rule 9). The module's fixture_vectors()
# must return EXACTLY this table: same names, same objects, same expected
# strings. The expected strings were derived from the verified rule family
# and are pinned here as the independent ground truth (07.1-05 copies them
# verbatim into the JS self-test table).
# ---------------------------------------------------------------------------
V1_OBJ = OrderedDict([
    ("claim_ids", ["GLY-INTRO-01"]),
    ("tags", ["stage:glycolysis"]),
    ("on_enter", [OrderedDict([("op", "hide_all")])]),
])
V1_EXPECTED = (
    "{\n"
    '  "claim_ids": ["GLY-INTRO-01"],\n'
    '  "tags": ["stage:glycolysis"],\n'
    '  "on_enter": [\n'
    '    {"op": "hide_all"}\n'
    "  ]\n"
    "}"
)

V2_OBJ = OrderedDict([
    ("files", ["intro.json", "glycolysis.json", "pyruvate_branch.json",
               "tca.json", "etc_atp.json", "endings.json", "bad_endings.json"]),
])
V2_EXPECTED = (
    "{\n"
    '  "files": [\n'
    '    "intro.json",\n'
    '    "glycolysis.json",\n'
    '    "pyruvate_branch.json",\n'
    '    "tca.json",\n'
    '    "etc_atp.json",\n'
    '    "endings.json",\n'
    '    "bad_endings.json"\n'
    "  ]\n"
    "}"
)

V3_OBJ = OrderedDict([
    ("on_enter", [
        OrderedDict([("op", "hide_all")]),
        OrderedDict([("op", "show_as"), ("target", "glucose"),
                     ("args", OrderedDict([("rep", "sticks")]))]),
    ]),
])
V3_EXPECTED = (
    "{\n"
    '  "on_enter": [\n'
    '    {"op": "hide_all"},\n'
    '    {"op": "show_as", "target": "glucose", "args": {"rep": "sticks"}}\n'
    "  ]\n"
    "}"
)

V4_OBJ = OrderedDict([
    ("log", [OrderedDict([("msg", "x" * 250), ("n", 1)])]),
])
V4_EXPECTED = (
    "{\n"
    '  "log": [\n'
    "    {\n"
    '      "msg": "' + "x" * 250 + '",\n'
    '      "n": 1\n'
    "    }\n"
    "  ]\n"
    "}"
)

_V5_SIGNATURE = OrderedDict([
    ("op", "point_mutation"),
    ("target", "resi 479"),
    ("args", OrderedDict([("new_res", "ARG")])),
])
V5_OBJ = OrderedDict([
    ("edits", [OrderedDict([
        ("signature", _V5_SIGNATURE),
        ("branch_node", "gly.pyruvate"),
        ("claim_id", "DIS-PKLR-01-cand"),
    ])]),
])
V5_EXPECTED = (
    "{\n"
    '  "edits": [\n'
    "    {\n"
    '      "signature": {"op": "point_mutation", "target": "resi 479",'
    ' "args": {"new_res": "ARG"}},\n'
    '      "branch_node": "gly.pyruvate",\n'
    '      "claim_id": "DIS-PKLR-01-cand"\n'
    "    }\n"
    "  ]\n"
    "}"
)

V6_OBJ = OrderedDict([
    ("text", "y" * 200),
    ("effects", OrderedDict()),
    ("claim_ids", []),
])
V6_EXPECTED = (
    "{\n"
    '  "text": "' + "y" * 200 + '",\n'
    '  "effects": {},\n'
    '  "claim_ids": []\n'
    "}"
)

V7_OBJ = OrderedDict([("resolution_angstrom", RAWFLOAT("2.40"))])
V7_EXPECTED = '{"resolution_angstrom": 2.40}'

V8_OBJ = OrderedDict([("text", "the road \u2014 em-dash \u2014 stays literal")])
V8_EXPECTED = '{"text": "the road \u2014 em-dash \u2014 stays literal"}'

V9_OBJ = OrderedDict([("s", 'say "hi" \\ done')])
V9_EXPECTED = '{"s": "say \\"hi\\" \\\\ done"}'

# compact({"k": "a"*166}) = 7 + 166 + 2 = 175 == W -> inline (<= inclusive).
V10_OBJ = OrderedDict([("k", "a" * 166)])
V10_EXPECTED = '{"k": "' + "a" * 166 + '"}'

V11_OBJ = OrderedDict([("k", ["a" * 11] * 8)])
V11_EXPECTED = (
    "{\n"
    '  "k": [\n'
    '    "aaaaaaaaaaa",\n'
    '    "aaaaaaaaaaa",\n'
    '    "aaaaaaaaaaa",\n'
    '    "aaaaaaaaaaa",\n'
    '    "aaaaaaaaaaa",\n'
    '    "aaaaaaaaaaa",\n'
    '    "aaaaaaaaaaa",\n'
    '    "aaaaaaaaaaa"\n'
    "  ]\n"
    "}"
)

# name -> (python_object, expected_string)
GROUND_TRUTH = OrderedDict([
    ("inline_scalar_list", (V1_OBJ, V1_EXPECTED)),
    ("multiline_long_scalar_list", (V2_OBJ, V2_EXPECTED)),
    ("container_array_inline_elements", (V3_OBJ, V3_EXPECTED)),
    ("long_element_breaks", (V4_OBJ, V4_EXPECTED)),
    ("edits_style_entry", (V5_OBJ, V5_EXPECTED)),
    ("nested_empty_dict_list", (V6_OBJ, V6_EXPECTED)),
    ("raw_float", (V7_OBJ, V7_EXPECTED)),
    ("non_ascii_string", (V8_OBJ, V8_EXPECTED)),
    ("string_with_quotes_and_backslashes", (V9_OBJ, V9_EXPECTED)),
    ("dict_fits_exactly_at_width", (V10_OBJ, V10_EXPECTED)),
    ("propagation_child_list_too_long", (V11_OBJ, V11_EXPECTED)),
])

# The 9 categories the plan mandates fixture_vectors() to cover (rule 9).
REQUIRED_VECTOR_NAMES = set([
    "inline_scalar_list",
    "multiline_long_scalar_list",
    "container_array_inline_elements",
    "long_element_breaks",
    "edits_style_entry",
    "nested_empty_dict_list",
    "raw_float",
    "non_ascii_string",
    "string_with_quotes_and_backslashes",
])


class TestByteIdenticalNoopOracle(unittest.TestCase):
    """Task 1 rule 1: the acceptance oracle over the 12 real data files."""

    def test_oracle_covers_exactly_12_targets(self):
        self.assertEqual(len(ORACLE_TARGETS), 12)

    def test_all_12_data_files_round_trip_byte_identically(self):
        for label, parts in ORACLE_TARGETS:
            with self.subTest(target=label):
                path = os.path.join(REPO_ROOT) + os.sep + os.path.join(*parts)
                raw = _read(path)
                # The trailing newline is added by the FILE WRITE (R1):
                # every real data file carries one.
                self.assertTrue(
                    raw.endswith("\n"),
                    "expected trailing newline in %s (part of the house style)" % (path,),
                )
                data = story_editor_json.loads(raw)
                out = story_editor_json.dumps(data)
                # dumps returns WITHOUT the trailing newline (contract):
                self.assertFalse(
                    out.endswith("\n"),
                    "dumps() must not append the trailing newline (file write adds it)",
                )
                # The no-op-save oracle: serialize(loaded) + "\n" == raw bytes.
                self.assertEqual(
                    out + "\n", raw,
                    "no-op save diverged for %s -- a house-style rule is "
                    "missing or wrong" % (path,),
                )


class TestEncodingBasics(unittest.TestCase):
    """Task 1 rule 2: ensure_ascii=False, 2-space indent, newline contract."""

    def test_dumps_returns_without_trailing_newline(self):
        shapes = [
            OrderedDict(),
            [],
            OrderedDict([("a", 1)]),
            OrderedDict([("k", ["a" * 300])]),      # multiline parent
            OrderedDict([("k", ["a" * 11] * 8)]),   # multiline list
        ]
        for obj in shapes:
            self.assertFalse(
                story_editor_json.dumps(obj).endswith("\n"),
                "dumps() output must not end with a newline",
            )

    def test_non_ascii_stays_literal_utf8(self):
        out = story_editor_json.dumps(OrderedDict([("s", "caf\u00e9 \u2014 ok")]))
        self.assertIn("caf\u00e9 \u2014 ok", out)
        self.assertNotIn("\\u", out)

    def test_key_order_is_insertion_order(self):
        obj = OrderedDict([("zeta", 1), ("alpha", 2), ("mid", 3)])
        self.assertEqual(story_editor_json.dumps(obj), '{"zeta": 1, "alpha": 2, "mid": 3}')

    def test_scalar_emission_forms(self):
        obj = OrderedDict([("t", True), ("f", False), ("n", None),
                           ("i", 42), ("fl", 0.5)])
        self.assertEqual(
            story_editor_json.dumps(obj),
            '{"t": true, "f": false, "n": null, "i": 42, "fl": 0.5}',
        )

    def test_multiline_rendering_uses_two_space_indent(self):
        # A dict that must break (compact 176 > W) renders children at +2 and
        # closes the brace at the parent indent.
        out = story_editor_json.dumps(OrderedDict([("k", "a" * 167)]))
        self.assertEqual(
            out,
            "{\n" '  "k": "' + "a" * 167 + '"\n' "}",
        )

    def test_loads_preserves_order_and_wraps_floats(self):
        d = story_editor_json.loads('{"b": 1, "a": 2.40}')
        self.assertEqual(list(d.keys()), ["b", "a"])  # OrderedDict, insertion order
        self.assertIsInstance(d["a"], RAWFLOAT)
        self.assertEqual(d["a"].token, "2.40")
        self.assertEqual(d["b"], 1)


class TestRawFloat(unittest.TestCase):
    """Task 1 rule 3: float literals round-trip without losing trailing zeros."""

    def test_loads_wraps_float_token(self):
        d = story_editor_json.loads('{"r": 2.40}')
        self.assertIsInstance(d["r"], RAWFLOAT)
        self.assertEqual(d["r"].token, "2.40")

    def test_dumps_emits_raw_token_verbatim(self):
        out = story_editor_json.dumps(OrderedDict([("r", RAWFLOAT("2.40"))]))
        self.assertEqual(out, '{"r": 2.40}')

    def test_dumps_does_not_reformat_float_tokens(self):
        # 1.70 and 2.70 carry meaningful trailing zeros in the real registry;
        # the token must be emitted EXACTLY (repr would emit "1.7" / "2.7").
        for token in ("1.70", "2.40", "2.70", "0.50"):
            out = story_editor_json.dumps(OrderedDict([("r", RAWFLOAT(token))]))
            self.assertEqual(out, '{"r": ' + token + '}')

    def test_raw_float_equality_is_token_based(self):
        self.assertEqual(RAWFLOAT("2.40"), RAWFLOAT("2.40"))
        self.assertNotEqual(RAWFLOAT("2.40"), RAWFLOAT("2.4"))
        self.assertNotEqual(RAWFLOAT("2.40"), 2.40)  # wrapper, not a float value

    def test_plain_python_float_uses_repr(self):
        # Objects built in Python (editor-side new values) emit repr(float):
        # shortest round-trip form ("0.5", "0.3").
        self.assertEqual(story_editor_json.dumps(OrderedDict([("w", 0.5)])),
                         '{"w": 0.5}')

    def test_real_registry_resolution_tokens_round_trip(self):
        raw = _read(os.path.join(REPO_ROOT, "data", "citations.json"))
        data = story_editor_json.loads(raw)
        found = []

        def walk(v):
            if isinstance(v, dict):
                for k, cv in v.items():
                    if k == "resolution_angstrom":
                        found.append(cv)
                    else:
                        walk(cv)
            elif isinstance(v, list):
                for cv in v:
                    walk(cv)

        walk(data)
        self.assertEqual(len(found), 10)
        for value in found:
            self.assertIsInstance(value, RAWFLOAT)
        # Every RawFloat token must equal the literal in the source text.
        literals = re.findall(r'"resolution_angstrom": ([0-9][0-9.]*)', raw)
        self.assertEqual(sorted(t.token for t in found), sorted(literals))
        self.assertIn("2.40", literals)  # the plan's named case


class TestScalarLists(unittest.TestCase):
    """Task 1 rule 4: scalar lists inline iff indent + compact <= 110."""

    def _list_obj(self, elem):
        # A multiline parent (long text sibling) so the list renders as a
        # dict VALUE at indent 2 -- the real claim_ids/files situation.
        return OrderedDict([("text", "p" * 300), ("k", [elem])])

    def test_inline_at_exactly_110_total(self):
        # compact(["a"*104]) = 108; at indent 2 -> 110 <= SW -> inline.
        obj = self._list_obj("a" * 104)
        expected = "{\n" '  "text": "' + "p" * 300 + '",\n' '  "k": ["' + "a" * 104 + '"]\n' "}"
        self.assertEqual(story_editor_json.dumps(obj), expected)

    def test_multiline_at_111_total(self):
        # compact(["a"*105]) = 109; at indent 2 -> 111 > SW -> one per line.
        obj = self._list_obj("a" * 105)
        expected = (
            "{\n"
            '  "text": "' + "p" * 300 + '",\n'
            '  "k": [\n'
            '    "' + "a" * 105 + '"\n'
            "  ]\n"
            "}"
        )
        self.assertEqual(story_editor_json.dumps(obj), expected)

    def test_manifest_style_files_list_is_multiline(self):
        # The real manifest case: compact 121 at indent 2 -> 123 > 110.
        out = story_editor_json.dumps(V2_OBJ)
        self.assertEqual(out, V2_EXPECTED)
        self.assertIn('  "files": [\n', out)


class TestContainerArrays(unittest.TestCase):
    """Task 1 rule 5: container arrays always multiline; elements iff fits."""

    def test_container_array_breaks_even_with_one_tiny_element(self):
        out = story_editor_json.dumps(OrderedDict([("wrap", [OrderedDict([("op", "x")])])]))
        self.assertEqual(
            out,
            "{\n"
            '  "wrap": [\n'
            '    {"op": "x"}\n'
            "  ]\n"
            "}",
        )

    def test_elements_inline_iff_they_fit(self):
        self.assertEqual(story_editor_json.dumps(V3_OBJ), V3_EXPECTED)

    def test_long_element_breaks_multiline(self):
        self.assertEqual(story_editor_json.dumps(V4_OBJ), V4_EXPECTED)

    def test_multiline_element_shape(self):
        out = story_editor_json.dumps(V4_OBJ)
        lines = out.split("\n")
        # element opens at indent 4, fields at 6, closes at 4
        self.assertEqual(lines[2], "    {")
        self.assertTrue(lines[3].startswith('      "msg": "'))
        self.assertEqual(lines[5], "    }")

    def test_mixed_scalar_and_dict_elements(self):
        # Any dict/list element makes the array a container array (R4) --
        # even when most elements are scalars.
        obj = OrderedDict([("m", [1, OrderedDict([("a", 2)])])])
        self.assertEqual(
            story_editor_json.dumps(obj),
            "{\n"
            '  "m": [\n'
            "    1,\n"
            '    {"a": 2}\n'
            "  ]\n"
            "}",
        )

    def test_list_of_scalar_lists_renders_inner_inline(self):
        # Outer = container array (contains lists) -> multiline; inner scalar
        # lists fit at their own depth -> inline.
        obj = OrderedDict([("m", [[1, 2], [3, 4]])])
        self.assertEqual(
            story_editor_json.dumps(obj),
            "{\n"
            '  "m": [\n'
            "    [1, 2],\n"
            "    [3, 4]\n"
            "  ]\n"
            "}",
        )


class TestDictFitsRule(unittest.TestCase):
    """Task 1 rule 6: the dict inline (fits) rule incl. propagation."""

    def test_dict_inline_at_exactly_175(self):
        # compact({"k": "a"*166}) = 7 + 166 + 2 = 175 == W -> inline
        # (<= is inclusive).
        self.assertEqual(story_editor_json.dumps(V10_OBJ), V10_EXPECTED)

    def test_dict_breaks_at_176(self):
        out = story_editor_json.dumps(OrderedDict([("k", "a" * 167)]))
        self.assertEqual(out, "{\n" '  "k": "' + "a" * 167 + '"\n' "}")

    def test_container_array_child_forbids_dict_inline(self):
        # {"wrap": [{"op": "x"}]} fits width-wise (compact 21 <= 175) but the
        # child is a container array -> the dict must render multiline.
        out = story_editor_json.dumps(OrderedDict([("wrap", [OrderedDict([("op", "x")])])]))
        self.assertTrue(out.startswith("{\n"))

    def test_propagation_child_list_too_long_forces_multiline(self):
        # compact(root) = 127 <= 175, but the child scalar list at its own
        # depth (indent 2) is 122 > 110 -> the parent may NOT inline.
        self.assertEqual(story_editor_json.dumps(V11_OBJ), V11_EXPECTED)

    def test_cast_entry_at_real_boundary_still_inlines(self):
        # The longest real cast entry (tca.succinyl_coa_synthetase) measures
        # compact 171 at indent 4 -> exactly 175 -> inline (verified against
        # rpg/data/cast.json by the oracle; pinned here structurally).
        cast = story_editor_json.loads(
            _read(os.path.join(REPO_ROOT, "rpg", "data", "cast.json")))
        out = story_editor_json.dumps(cast)
        self.assertIn(
            '    {"id": "tca.succinyl_coa_synthetase", "label": "Succinyl-CoA'
            ' synthetase", "source": "download", "pdb_id": "6WCV",'
            ' "character": "glucose", "claim_id": "DIS-SUCLG1-01-cand"}',
            out,
        )


class TestEditsKeyException(unittest.TestCase):
    """Task 1 rule 7: elements under the "edits" key are ALWAYS multiline."""

    def test_edits_element_forced_multiline_despite_fitting(self):
        # The element's compact form is 152 at indent 4 -> 156 <= 175: it
        # WOULD inline without the exception. The "edits" key forces the
        # hand style (each field on its own line; signature stays inline).
        self.assertEqual(story_editor_json.dumps(V5_OBJ), V5_EXPECTED)

    def test_same_content_under_other_key_inlines(self):
        obj = OrderedDict([("edits_list", [
            OrderedDict([
                ("signature", _V5_SIGNATURE),
                ("branch_node", "gly.pyruvate"),
                ("claim_id", "DIS-PKLR-01-cand"),
            ]),
        ])])
        self.assertEqual(
            story_editor_json.dumps(obj),
            "{\n"
            '  "edits_list": [\n'
            '    {"signature": {"op": "point_mutation", "target": "resi 479",'
            ' "args": {"new_res": "ARG"}}, "branch_node": "gly.pyruvate",'
            ' "claim_id": "DIS-PKLR-01-cand"}\n'
            "  ]\n"
            "}",
        )

    def test_real_edits_json_shape_preserved(self):
        # Structural spot-check independent of the byte oracle: the edit
        # element opens on its own line under "edits".
        edits = story_editor_json.loads(
            _read(os.path.join(REPO_ROOT, "rpg", "data", "edits.json")))
        out = story_editor_json.dumps(edits)
        self.assertIn('      "edits": [\n', out)
        self.assertIn("        {\n", out)
        self.assertIn('          "signature": {"op": "point_mutation",', out)


class TestEmptyContainers(unittest.TestCase):
    """Task 1 rule 8: {} and [] always inline."""

    def test_empty_containers_inline_as_values(self):
        out = story_editor_json.dumps(OrderedDict([("a", OrderedDict()), ("b", [])]))
        self.assertEqual(out, '{"a": {}, "b": []}')

    def test_empty_containers_inline_when_nested(self):
        obj = OrderedDict([("outer", OrderedDict([
            ("effects", OrderedDict()), ("claim_ids", []),
        ]))])
        self.assertEqual(story_editor_json.dumps(obj),
                         '{"outer": {"effects": {}, "claim_ids": []}}')

    def test_empty_containers_inline_inside_multiline_parent(self):
        self.assertEqual(story_editor_json.dumps(V6_OBJ), V6_EXPECTED)

    def test_empty_root_containers(self):
        self.assertEqual(story_editor_json.dumps(OrderedDict()), "{}")
        self.assertEqual(story_editor_json.dumps([]), "[]")


class TestFixtureVectors(unittest.TestCase):
    """Task 1 rule 9: the shared fixture table (the 07.1-05 JS-port spec)."""

    def _vectors(self):
        return story_editor_json.fixture_vectors()

    def test_vectors_match_ground_truth_table(self):
        vectors = self._vectors()
        self.assertEqual(len(vectors), len(GROUND_TRUTH))
        by_name = {}
        for entry in vectors:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
            name, obj, expected = entry
            self.assertIsInstance(name, str)
            self.assertIsInstance(obj, dict)
            self.assertIsInstance(expected, str)
            self.assertNotIn(name, by_name, "duplicate vector name %r" % (name,))
            by_name[name] = (obj, expected)
        self.assertEqual(sorted(by_name.keys()), sorted(GROUND_TRUTH.keys()))
        for name, (gt_obj, gt_expected) in GROUND_TRUTH.items():
            obj, expected = by_name[name]
            self.assertEqual(expected, gt_expected,
                             "vector %r expected string diverged" % (name,))
            self.assertEqual(obj, gt_obj,
                             "vector %r object diverged" % (name,))

    def test_required_vector_categories_present(self):
        names = set(v[0] for v in self._vectors())
        missing = REQUIRED_VECTOR_NAMES - names
        self.assertEqual(missing, set(),
                         "fixture_vectors() missing required categories: %r" % (sorted(missing),))

    def test_each_vector_dumps_equals_expected(self):
        for name, obj, expected in self._vectors():
            with self.subTest(vector=name):
                self.assertEqual(story_editor_json.dumps(obj), expected)

    def test_each_vector_round_trips(self):
        for name, obj, expected in self._vectors():
            with self.subTest(vector=name):
                loaded = story_editor_json.loads(expected)
                self.assertEqual(loaded, obj)
                self.assertEqual(story_editor_json.dumps(loaded), expected)

    def test_each_vector_expected_is_valid_json(self):
        for name, _obj, expected in self._vectors():
            with self.subTest(vector=name):
                json.loads(expected)  # must parse with the stdlib parser

    def test_raw_float_vector_carries_rawfloat_instance(self):
        for name, obj, _expected in self._vectors():
            if name == "raw_float":
                self.assertIsInstance(obj["resolution_angstrom"], RAWFLOAT)
                self.assertEqual(obj["resolution_angstrom"].token, "2.40")
                return
        self.fail("raw_float vector missing")


if __name__ == "__main__":
    unittest.main()
