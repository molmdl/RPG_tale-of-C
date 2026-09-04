#!/usr/bin/env python3.6
"""Parity pins: canonical Python serializer (07.1-02) vs JS port (07.1-05).

The canonical spec is tools/story_editor_json.py (plan 07.1-02): a no-op save
must reproduce every data JSON byte-identically (07-17 gold-diff precedent,
RESEARCH-SAFETY Pitfall S1). Plan 07.1-05 ports it to the emitted page as
tools/story_editor_assets/05_json.js (EDITOR.housy.stringify) and embeds the
SAME fixture_vectors() table as the in-browser self-test (SELFTEST_VECTORS +
EDITOR.selfTestSerializer(), run at boot as a silent Canary).

What THIS battery pins mechanically from WSL (the runtime equivalence is
proven in-browser by the boot self-test at the human-verify checkpoints):

  1. VECTOR PARITY -- every fixture_vectors() (name, object, expected)
     triple has its counterpart in the asset's SELFTEST_VECTORS table, in
     the same order, with the expected string embedded EXACTLY. Mechanism
     note ("appears VERBATIM"): the asset embeds each expected string as an
     ES5 double-quoted JS string constant (concatenation pieces allowed,
     mirroring the Python battery's own adjacent-literal style) -- a
     multi-line string constant necessarily escapes its newlines, so the
     verbatim pin is enforced by decoding the constant with the STDLIB JSON
     parser (the asset is pinned to the JSON-compatible escape subset:
     anything else fails loudly here) and asserting
     decoded_constant == fixture_vectors() expected, i.e. verbatim once
     JS-literal-decoded. The asset side of the same equality is what the
     boot canary checks in-browser.
  2. CONSTANTS SURVIVE THE PORT -- W=175, SW=110 and the "edits" force key
     are present; the naive pretty-printer is NOT: the asset must contain
     no `null, 2` / `null,2` occurrence (and no JSON.stringify call with a
     null second argument at all) -- the save path (07.1-13) must call
     EDITOR.housy.stringify, never the naive form.
  3. BOOT CANARY -- the self-test init is registered (EDITOR.init receives
     a hook that calls selfTestSerializer()) and writes the one-line
     "serializer self-test N/N pass" status.
  4. ASSET INLINED -- regenerating the editor emits the 05_json.js asset
     block after 00_core.js (when present) and before the shell's
     DOMContentLoaded bootstrap, with the asset markers in sorted order.
  5. ES5 DISCIPLINE -- the asset uses var/function only: no arrow
     functions, no let/const, no backtick template literals, no ES-module
     markers, no top-level import (same discipline 07.1-04 pins for the
     emitted page; the port must stay reviewable in the same style).

Python 3.6 stdlib ONLY (unittest/os/re/json/sys/subprocess/tempfile/shutil).
NO pytest (not installed). NO f-strings (.format() / % per repo convention).
NO pymol/PyQt5 imports (pure-Python module; the AST import gate scans
tests/). Importing story_editor_json is side-effect-free (verified 07.1-02).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(HERE, "..")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
GENERATOR = os.path.join(REPO_ROOT, "tools", "story_editor.py")
ASSET = os.path.join(REPO_ROOT, "tools", "story_editor_assets", "05_json.js")

# Make tools/ importable (same pattern as tests/test_story_editor_json.py).
sys.path.insert(0, TOOLS_DIR)
import story_editor_json  # noqa: E402  (side-effect-free canonical module)


def _read(path):
    # type: (str) -> str
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# JS string-literal extraction helpers.
#
# The asset's SELFTEST_VECTORS table embeds each expected string as one or
# more adjacent double-quoted ES5 string constants joined by "+" (exactly
# the Python battery's own style for long literals). A piece may NOT
# contain a raw newline (that would be invalid JS) -- the charset below
# excludes one, so a raw newline in a constant fails the pin loudly.
# ---------------------------------------------------------------------------
_JS_STR_PIECE = r'"(?:[^"\\\n]|\\.)*"'
EXPECTED_CHAIN_RE = re.compile(
    r'expected:\s*(' + _JS_STR_PIECE + r'(?:\s*\+\s*' + _JS_STR_PIECE + r')*)')
NAME_RE = re.compile(r'name:\s*"([^"]+)"')
TABLE_CLOSE_RE = re.compile(r"\n\s*];")


def _table_region(src):
    # type: (str) -> str
    """The source text of the SELFTEST_VECTORS table (declaration line
    through its closing bracket line). Scoping keeps the extraction immune
    to any other string constants elsewhere in the asset."""
    start = src.index("var SELFTEST_VECTORS")
    close = TABLE_CLOSE_RE.search(src, start)
    if close is None:
        raise AssertionError("SELFTEST_VECTORS table has no closing ]; line")
    return src[start:close.end()]


def _decode_chain(chain):
    # type: (str) -> str
    """Decode a JS string-constant chain to its runtime value.

    Each piece is decoded with the STDLIB JSON parser: the asset is pinned
    to the JSON-compatible escape subset (double-quoted constants; \\n,
    \\", \\\\, \\uXXXX ...), so json.loads IS the JS string decoder for this
    charset -- no hand-rolled unescaper to drift. Any non-JSON escape
    raises JSONDecodeError and fails the pin loudly.
    """
    pieces = re.findall(_JS_STR_PIECE, chain)
    out = []
    for piece in pieces:
        inner = piece[1:-1]  # strip the surrounding quotes
        out.append(json.loads('"' + inner + '"'))
    return "".join(out)


class TestFixtureVectorParity(unittest.TestCase):
    """Rule 1: every fixture_vectors() expected string is embedded in the
    JS asset's SELFTEST_VECTORS, name-for-name, order-for-order, with the
    decoded constant equal to the canonical expected string."""

    def test_all_fixture_vectors_embedded_verbatim(self):
        vectors = story_editor_json.fixture_vectors()
        self.assertEqual(
            len(vectors), 11,
            "fixture_vectors() count changed -- update the JS port table "
            "AND this battery in the same commit")
        src = _read(ASSET)
        region = _table_region(src)
        names = NAME_RE.findall(region)
        chains = EXPECTED_CHAIN_RE.findall(region)
        self.assertEqual(
            len(names), len(vectors),
            "asset SELFTEST_VECTORS entry count (%d) != fixture_vectors() "
            "count (%d)" % (len(names), len(vectors)))
        self.assertEqual(
            len(chains), len(vectors),
            "asset expected-constant count (%d) != fixture_vectors() count "
            "(%d)" % (len(chains), len(vectors)))
        for (py_name, _py_obj, py_expected), js_name, chain in zip(
                vectors, names, chains):
            self.assertEqual(
                js_name, py_name,
                "asset vector name %r != canonical %r (order or spelling "
                "drift)" % (js_name, py_name))
            js_expected = _decode_chain(chain)
            self.assertEqual(
                js_expected, py_expected,
                "vector %r: the embedded JS expected constant diverges from "
                "the canonical fixture output" % (py_name,))

    def test_asset_header_cites_the_canonical_spec(self):
        """Traceability: the asset names its owner plan and spec module."""
        src = _read(ASSET)
        self.assertIn("tools/story_editor_json.py", src)
        self.assertIn("07.1-05", src)
        self.assertIn("EDITOR.housy", src)


class TestConstantsSurvivePort(unittest.TestCase):
    """Rule 2: W=175 / SW=110 / the edits force key survived; the naive
    pretty-printer did not."""

    def test_width_constants_present(self):
        src = _read(ASSET)
        self.assertIn("175", src)
        self.assertIn("110", src)
        # The precise constant declarations (not incidental numbers).
        self.assertRegex(src, r"var W\s*=\s*175\s*;")
        self.assertRegex(src, r"var SW\s*=\s*110\s*;")

    def test_edits_force_key_present(self):
        src = _read(ASSET)
        self.assertTrue(
            ("'edits'" in src) or ('"edits"' in src),
            "the edits force key literal is missing from the asset")
        self.assertIn("EDITS_FORCE_KEY", src)

    def test_no_naive_pretty_print_callsite(self):
        src = _read(ASSET)
        # JSON.stringify IS used -- for string/key escaping (R2), the same
        # role json.dumps(s, ensure_ascii=False) plays in Python.
        self.assertIn("JSON.stringify(", src)
        # The plan's zero-occurrence grep: the two-argument pretty-print
        # form must not appear anywhere (comment included).
        self.assertNotIn("null, 2", src)
        self.assertNotIn("null,2", src)
        # And no JSON.stringify call may carry a null second argument at
        # all (any spacing variant).
        self.assertIsNone(
            re.search(r"JSON\.stringify\([^()]*,\s*null", src),
            "naive pretty-print call found in the asset")


class TestBootCanary(unittest.TestCase):
    """Rule 3: the self-test init registration exists and reports."""

    def test_self_test_init_registered(self):
        src = _read(ASSET)
        self.assertIn("function bootSelfTest", src)
        self.assertIn("EDITOR.init(bootSelfTest)", src)
        # The selfTestSerializer() call must sit INSIDE the registered boot
        # hook (between its definition and its registration).
        start = src.index("function bootSelfTest")
        end = src.index("EDITOR.init(bootSelfTest)")
        body = src[start:end]
        self.assertIn("selfTestSerializer()", body)

    def test_status_line_and_own_status_span(self):
        src = _read(ASSET)
        self.assertIn("EDITOR: serializer self-test", src)
        # Own status span: the canary never writes into another plan's
        # status spans.
        self.assertIn("statusbar-serializer", src)
        # Defensive: the boot hook is try/catch wrapped (a serializer bug
        # must be visible, never fatal).
        self.assertIn("try {", src)


class TestAssetInlining(unittest.TestCase):
    """Rule 4: regenerating the editor inlines the housy asset after core
    (when present) and before the shell bootstrap (markers sorted)."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_parity_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = subprocess.run(
            [sys.executable, GENERATOR, "--output", cls.out_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _markers(self):
        # type: () -> list
        return re.findall(r"/\* asset: (\S+) \(", self.html)

    def test_generation_succeeds(self):
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        self.assertTrue(self.html, "generator emitted no HTML")

    def test_housy_asset_inlined(self):
        for needle in ("EDITOR.housy", "SELFTEST_VECTORS",
                       "selfTestSerializer"):
            self.assertIn(needle, self.html,
                          "emitted HTML lacks %r from the housy asset" % needle)
        self.assertIn("/* asset: 05_json.js (", self.html)

    def test_order_after_core_before_bootstrap(self):
        markers = self._markers()
        self.assertIn("05_json.js", markers)
        # Sorted inlining contract: the marker list is the sorted file list.
        self.assertEqual(markers, sorted(markers),
                         "asset markers not in sorted order: %r" % (markers,))
        if "00_core.js" in markers:
            self.assertLess(
                markers.index("00_core.js"), markers.index("05_json.js"),
                "the housy asset must inline AFTER the core asset")
        # The asset block must close before the shell's DOMContentLoaded
        # bootstrap block (the LAST classic script block).
        i_05_open = self.html.find("/* asset: 05_json.js")
        i_05_close = self.html.find("</script>", i_05_open)
        i_bootstrap = self.html.rfind("<script>")
        self.assertLess(
            i_05_close, i_bootstrap,
            "the housy asset block must come before the bootstrap script")


class TestAssetEs5Discipline(unittest.TestCase):
    """Rule 5: the asset stays ES5 (var/function only) -- same discipline
    the emitted-page state-layer battery (07.1-04) pins; the port must be
    reviewable in the same style and safe on every browser the editor
    targets."""

    def test_no_arrow_functions(self):
        src = _read(ASSET)
        self.assertNotIn("=>", src, "arrow function found in the asset")

    def test_no_let_const(self):
        src = _read(ASSET)
        self.assertIsNone(re.search(r"\blet\s", src),
                          "let declaration found in the asset")
        self.assertIsNone(re.search(r"\bconst\s", src),
                          "const declaration found in the asset")

    def test_no_template_literals(self):
        src = _read(ASSET)
        self.assertNotIn("`", src, "backtick template literal found")

    def test_no_modules_no_top_level_import(self):
        src = _read(ASSET)
        self.assertNotIn('type="module"', src)
        self.assertIsNone(
            re.search(r"(?m)^\s*import(?:\s|[\"('\)])", src),
            "top-level import statement found in the asset")


if __name__ == "__main__":
    unittest.main()
