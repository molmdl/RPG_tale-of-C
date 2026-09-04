#!/usr/bin/env python3.6
"""Canonical house-style JSON serializer for the story-node editor (07.1-02).

This module is the CANONICAL SPEC for "save edit" serialization in the Phase
7.1 HTML story-node editor: a no-op save (load -> serialize) must reproduce
every data JSON in this repo BYTE-IDENTICALLY, so edits produce reviewable,
minimal diffs instead of whole-file reflows (07-17 precedent). Plan 07.1-05
ports this module 1:1 to JS (EDITOR.housy.stringify) with fixture_vectors()
as the shared self-test table.

VERIFICATION: 12/12 data files byte-identical, verified 2026-09-04 --
data/story_glucose/{manifest,intro,glycolysis,pyruvate_branch,tca,etc_atp,
endings,bad_endings}.json + data/{citations,sources}.json +
rpg/data/{edits,cast}.json all satisfy dumps(loads(raw)) + "\\n" == raw.

Constants: W = 175 (container inline width), SW = 110 (scalar-list inline
width). edits-key multiline exception: array elements under the key "edits"
always render one field per line (the hand style edits.json was authored in;
without the exception 10/13 real entries would wrongly inline). OrderedDict
as the object_pairs_hook is REQUIRED for py3.6 key-order fidelity (plain
dicts only preserve insertion order as a CPython implementation detail).

The rule family (pinned by tests/test_story_editor_json.py):

  R1. Encoding: ensure_ascii=False (non-ASCII stays literal UTF-8); 2-space
      indent; ``dumps`` returns WITHOUT a trailing newline -- the file write
      appends it.
  R2. Raw floats: ``loads`` wraps every float token in RawFloat(token);
      ``dumps`` emits the token verbatim ("2.40" stays "2.40"). Plain Python
      floats (new editor-side values) emit repr(float) -- shortest
      round-trip form. Integers emit str(int).
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
      R5). The flag is a single level: it applies to the direct elements of
      the array stored under that key, not to deeper descendants.
  R7. Empty containers ``{}`` and ``[]`` are always inline, at any depth.

Public API: loads(text), dumps(data) -> str (no trailing newline),
fixture_vectors() -> [(name, python_object, expected_string), ...],
RawFloat. Pure Python 3.6 stdlib (json + collections); NO pymol/PyQt5
imports; no f-strings (repo convention).
"""
import json
from collections import OrderedDict

W = 175   # container inline width (dict fits iff indent + len(compact) <= W)
SW = 110  # scalar-list inline width (list fits iff indent + len(compact) <= SW)

EDITS_FORCE_KEY = "edits"


class RawFloat(object):
    """A JSON float token preserved verbatim ("2.40" stays "2.40").

    ``loads`` wraps every float literal via ``parse_float=RawFloat``;
    ``dumps`` emits ``token`` unchanged. Equality is token-based (a wrapper
    identity, not a numeric value): RawFloat("2.40") != RawFloat("2.4").
    """

    __slots__ = ("token",)

    def __init__(self, token):
        self.token = token

    def __repr__(self):
        return "RawFloat(%r)" % (self.token,)

    def __eq__(self, other):
        if isinstance(other, RawFloat):
            return self.token == other.token
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self):
        return hash(("RawFloat", self.token))


def loads(text):
    """Parse JSON text preserving key order (OrderedDict) + float tokens."""
    return json.loads(text, object_pairs_hook=OrderedDict, parse_float=RawFloat)


# ---------------------------------------------------------------------------
# Rendering primitives
# ---------------------------------------------------------------------------

def scalar_str(v):
    """Render a scalar (non-container) value exactly as the house style."""
    if isinstance(v, RawFloat):
        return v.token
    if isinstance(v, bool):  # before int: bool is an int subclass
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)  # shortest round-trip form, same as json.dumps
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    raise TypeError("unsupported scalar type: %r" % (type(v),))


def compact(v):
    """The one-line form: {"a": 1, "b": [2, 3]} / [1, 2] (", " + ": " sep)."""
    if isinstance(v, list):
        return "[" + ", ".join(compact(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(
            json.dumps(k, ensure_ascii=False) + ": " + compact(cv)
            for k, cv in v.items()
        ) + "}"
    return scalar_str(v)


def is_scalar_list(v):
    """True when v is a list with NO dict/list elements (R3 shape)."""
    return all(not isinstance(x, (dict, list)) for x in v)


def fits_list(v, indent):
    """R3 + R7: a list may inline iff scalar-only and it fits within SW."""
    if not v:
        return True  # empty containers are always inline (R7)
    if is_scalar_list(v):
        return indent + len(compact(v)) <= SW
    return False  # container arrays are always multiline (R4)


def fits_dict(v, indent):
    """R5 + R7: a dict may inline iff it fits within W, holds no
    container-array child, and every descendant container fits at its own
    depth (propagation)."""
    if not v:
        return True  # empty containers are always inline (R7)
    if indent + len(compact(v)) > W:
        return False
    for cv in v.values():
        if isinstance(cv, list) and not is_scalar_list(cv):
            return False  # container-array child forbids inline (R5)
    return descendants_fit(v, indent)


def descendants_fit(v, indent):
    """R5 propagation: children sit at indent + 2 if this dict broke, so
    each descendant container must fit at ITS own depth."""
    for cv in v.values():
        if isinstance(cv, dict):
            if not fits_dict(cv, indent + 2):
                return False
        elif isinstance(cv, list):
            if not fits_list(cv, indent + 2):
                return False
    return True


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def ser_keyed(v, indent, key):
    """Render a dict child under ``key`` -- sets the R6 edits force flag."""
    force = (key == EDITS_FORCE_KEY and isinstance(v, list))
    return ser(v, indent, force)


def ser(v, indent, force=False):
    """Render a value at ``indent``.

    ``force`` marks this value as a direct array element under the "edits"
    key (R6): a dict so flagged renders multiline even when it fits. Empty
    containers stay inline regardless (R7).
    """
    pad = " " * indent
    if isinstance(v, dict):
        if not v:
            return "{}"
        if not force and fits_dict(v, indent):
            return compact(v)
        return ser_dict_multiline(v, indent)
    if isinstance(v, list):
        if not v:
            return "[]"
        if is_scalar_list(v):
            if indent + len(compact(v)) <= SW:
                return compact(v)
            return ser_scalar_list_multiline(v, indent)
        # Container array: ALWAYS multiline (R4); elements inherit the
        # force flag (they are the direct "edits" elements when set).
        lines = ["["]
        for i, x in enumerate(v):
            piece = pad + "  " + ser(x, indent + 2, force)
            if i < len(v) - 1:
                piece += ","
            lines.append(piece)
        lines.append(pad + "]")
        return "\n".join(lines)
    return scalar_str(v)


def ser_dict_multiline(v, indent):
    """R5 multiline dict: children at +2, close brace at the parent indent."""
    pad = " " * indent
    lines = ["{"]
    child_indent = indent + 2
    items = list(v.items())
    for i, (k, cv) in enumerate(items):
        piece = " " * child_indent + json.dumps(k, ensure_ascii=False) + ": "
        piece += ser_keyed(cv, child_indent, k)
        if i < len(items) - 1:
            piece += ","
        lines.append(piece)
    lines.append(pad + "}")
    return "\n".join(lines)


def ser_scalar_list_multiline(v, indent):
    """R3 multiline scalar list: one element per line at +2."""
    pad = " " * indent
    lines = ["["]
    for i, x in enumerate(v):
        piece = pad + "  " + scalar_str(x)
        if i < len(v) - 1:
            piece += ","
        lines.append(piece)
    lines.append(pad + "]")
    return "\n".join(lines)


def dumps(data):
    """Serialize to the house style. Returns WITHOUT a trailing newline --
    the file write appends it (R1; the no-op oracle is
    dumps(loads(raw)) + "\\n" == raw)."""
    return ser(data, 0, False)


# ---------------------------------------------------------------------------
# Fixture vectors -- the shared spec for the JS port (07.1-05)
# ---------------------------------------------------------------------------

def _od(*pairs):
    return OrderedDict(pairs)


def fixture_vectors():
    """(name, python_object, expected_string) triples covering the tricky
    house-style cases. The JS port (07.1-05) embeds the SAME table as its
    serializer self-test; the expected strings are canonical outputs, pinned
    independently in tests/test_story_editor_json.py (GROUND_TRUTH)."""
    return [
        ("inline_scalar_list",
         _od(("claim_ids", ["GLY-INTRO-01"]),
             ("tags", ["stage:glycolysis"]),
             ("on_enter", [_od(("op", "hide_all"))])),
         "{\n"
         '  "claim_ids": ["GLY-INTRO-01"],\n'
         '  "tags": ["stage:glycolysis"],\n'
         '  "on_enter": [\n'
         '    {"op": "hide_all"}\n'
         "  ]\n"
         "}"),
        ("multiline_long_scalar_list",
         _od(("files", ["intro.json", "glycolysis.json", "pyruvate_branch.json",
                        "tca.json", "etc_atp.json", "endings.json",
                        "bad_endings.json"])),
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
         "}"),
        ("container_array_inline_elements",
         _od(("on_enter", [
             _od(("op", "hide_all")),
             _od(("op", "show_as"), ("target", "glucose"),
                 ("args", _od(("rep", "sticks")))),
         ])),
         "{\n"
         '  "on_enter": [\n'
         '    {"op": "hide_all"},\n'
         '    {"op": "show_as", "target": "glucose", "args": {"rep": "sticks"}}\n'
         "  ]\n"
         "}"),
        ("long_element_breaks",
         _od(("log", [_od(("msg", "x" * 250), ("n", 1))])),
         "{\n"
         '  "log": [\n'
         "    {\n"
         '      "msg": "' + "x" * 250 + '",\n'
         '      "n": 1\n'
         "    }\n"
         "  ]\n"
         "}"),
        ("edits_style_entry",
         _od(("edits", [_od(
             ("signature", _od(("op", "point_mutation"), ("target", "resi 479"),
                               ("args", _od(("new_res", "ARG"))))),
             ("branch_node", "gly.pyruvate"),
             ("claim_id", "DIS-PKLR-01-cand"),
         )])),
         "{\n"
         '  "edits": [\n'
         "    {\n"
         '      "signature": {"op": "point_mutation", "target": "resi 479",'
         ' "args": {"new_res": "ARG"}},\n'
         '      "branch_node": "gly.pyruvate",\n'
         '      "claim_id": "DIS-PKLR-01-cand"\n'
         "    }\n"
         "  ]\n"
         "}"),
        ("nested_empty_dict_list",
         _od(("text", "y" * 200), ("effects", _od()), ("claim_ids", [])),
         "{\n"
         '  "text": "' + "y" * 200 + '",\n'
         '  "effects": {},\n'
         '  "claim_ids": []\n'
         "}"),
        ("raw_float",
         _od(("resolution_angstrom", RawFloat("2.40"))),
         '{"resolution_angstrom": 2.40}'),
        ("non_ascii_string",
         _od(("text", "the road \u2014 em-dash \u2014 stays literal")),
         '{"text": "the road \u2014 em-dash \u2014 stays literal"}'),
        ("string_with_quotes_and_backslashes",
         _od(("s", 'say "hi" \\ done')),
         '{"s": "say \\"hi\\" \\\\ done"}'),
        ("dict_fits_exactly_at_width",
         _od(("k", "a" * 166)),
         '{"k": "' + "a" * 166 + '"}'),
        ("propagation_child_list_too_long",
         _od(("k", ["a" * 11] * 8)),
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
         "}"),
    ]
