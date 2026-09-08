"""Structural state-layer test battery for the Phase 7.1 editor core asset
(07.1-04 Task 2).

Covers:
- the EDITOR core asset (00_core.js) is inlined FIRST -- window.EDITOR is
  defined inside the first asset block, before any later asset begins
  (test_core_inlined_first)
- the required state-layer entry points are present in the core block
  (test_state_entry_points)
- the B11 unknown-key preservation contract comment exists in the asset
  source itself (test_unknown_key_contract_comment)
- emitted-JS ES5 discipline: no arrow functions (=>), no let/const
  declarations, no ES-module scripts -- pins the classic-script style the
  research mandates (modules fail under file:// CORS; ES5 keeps the emitted
  JS reviewable) for EVERY inlined block, present and future
  (test_no_modules_no_arrow_asi_landmines)
- the hooks architecture is defensive: EDITOR.hooks carries the
  rerender/validate/persist arrays and afterChange dispatches every hook in
  its own try/catch, so one broken view never kills the state layer
  (test_hooks_defensive)

Pure WSL python3.6 -- stdlib only; the generator is subprocessed once per
test class via setUpClass into a temp dir using --output (same conventions
as tests/test_story_editor_generator.py: REPO_ROOT via __file__,
subprocess.run with PIPE streams -- NOT capture_output, which is 3.7+).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".."))
GENERATOR = os.path.join(REPO_ROOT, "tools", "story_editor.py")
CORE_ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "00_core.js")

# Make the sibling test helper importable (same sys.path pattern as
# tests/test_story_editor_serializer_js.py's TOOLS_DIR import). The helper
# replaces the old naive <script> extraction regex here (CodeQL
# py/bad-tag-filter alerts #8, #9).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import script_blocks  # noqa: E402  (side-effect-free stdlib helper)

# The state-layer entry points later plans code against (07.1-04 plan).
REQUIRED_SYMBOLS = [
    "EDITOR.apply", "EDITOR.undo", "EDITOR.redo", "EDITOR.setBundle",
    "EDITOR.select", "EDITOR.showTab", "EDITOR.view",
    "fnv1a", "MAX_UNDO", "deriveKind", "endingTier",
]


def run_generator(args):
    """Run tools/story_editor.py with the given CLI args (list)."""
    return subprocess.run(
        [sys.executable, GENERATOR] + list(args),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True)


def _read(path):
    # type: (str) -> str
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestCoreAssetStateLayer(unittest.TestCase):
    """Structural checks over ONE emitted page + the core asset source."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_state_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.core_src = _read(CORE_ASSET) if os.path.isfile(CORE_ASSET) else ""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _core_block(self):
        # type: () -> str
        """Extract the inlined 00_core.js <script> block from the page."""
        marker = "/* asset: 00_core.js"
        m_start = self.html.find(marker)
        self.assertGreaterEqual(
            m_start, 0, "00_core.js asset marker missing from emitted HTML")
        block_open = self.html.rfind("<script>", 0, m_start)
        self.assertGreaterEqual(
            block_open, 0, "core asset block has no opening <script>")
        block_close = self.html.find("</script>", m_start)
        self.assertGreaterEqual(
            block_close, 0, "core asset block is unterminated")
        return self.html[block_open:block_close]

    def test_core_inlined_first(self):
        """The core asset is the FIRST asset block, and window.EDITOR is
        defined inside it before any later asset block begins."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        first_asset = self.html.find("/* asset: ")
        self.assertGreaterEqual(
            first_asset, 0, "no asset blocks inlined at all")
        core_marker = self.html.find("/* asset: 00_core.js")
        self.assertEqual(
            first_asset, core_marker,
            "00_core.js must be the FIRST inlined asset block (it defines "
            "the window.EDITOR contract every later asset consumes)")
        block_open = self.html.rfind("<script>", 0, core_marker)
        block_close = self.html.find("</script>", core_marker)
        editor_def = self.html.find("window.EDITOR", block_open, block_close)
        self.assertGreaterEqual(
            editor_def, 0, "window.EDITOR not defined inside the core block")
        second_asset = self.html.find("/* asset: ", first_asset + 1)
        if second_asset > -1:
            self.assertLess(
                block_close, second_asset,
                "the core <script> block must close before the next asset "
                "block begins")

    def test_state_entry_points(self):
        """All required state-layer symbols are defined in the core block."""
        core_block = self._core_block()
        for symbol in REQUIRED_SYMBOLS:
            self.assertIn(
                symbol, core_block,
                "missing state-layer entry point %s" % symbol)

    def test_unknown_key_contract_comment(self):
        """The B11 unknown-key preservation contract comment exists in the
        asset SOURCE itself: mutators never rebuild nodes from a field
        whitelist, so unknown keys round-trip untouched."""
        self.assertIn(
            "UNKNOWN-KEY PRESERVATION CONTRACT", self.core_src,
            "the contract comment header is missing")
        self.assertIn(
            "round-trip", self.core_src,
            "the contract must state that unknown keys round-trip")
        self.assertIn(
            "whitelist", self.core_src,
            "the contract must forbid whitelist rebuilds")

    def test_no_modules_no_arrow_asi_landmines(self):
        """Emitted JS is ES5-classic in EVERY script block: no arrow
        functions (=>), no let/const declarations (var only), no ES-module
        scripts (type="module" fails under file:// CORS)."""
        self.assertNotIn('type="module"', self.html)
        # Browser-faithful extraction (CodeQL py/bad-tag-filter): the old
        # re.findall(r"<script>(.*?)</script>", ...) silently missed
        # <SCRIPT foo="bar">-style blocks a browser WOULD execute.
        blocks = script_blocks.extract_script_blocks(self.html)
        self.assertTrue(
            blocks, "expected at least one inline script block")
        for i, block in enumerate(blocks):
            self.assertNotEqual(
                (block.attrs.get("type") or "").lower(), "module",
                "script block %d is an ES module (type=module); classic "
                "scripts only (modules fail under file:// CORS)" % i)
            self.assertIsNone(
                re.search(r"=>", block.text),
                "script block %d contains an arrow function (=>); ES5 var-"
                "style is the pinned emitted-JS convention" % i)
            self.assertIsNone(
                re.search(r"\blet\s", block.text),
                "script block %d contains a let declaration" % i)
            self.assertIsNone(
                re.search(r"\bconst\s", block.text),
                "script block %d contains a const declaration" % i)

    def test_hooks_defensive(self):
        """EDITOR.hooks carries the three hook arrays, and afterChange
        dispatches every hook of each kind inside its own try/catch."""
        core_block = self._core_block()
        self.assertIn(
            "EDITOR.hooks = { rerender: [], validate: [], persist: [] }",
            core_block,
            "EDITOR.hooks must define the rerender/validate/persist arrays")
        m = re.search(
            r"EDITOR\.afterChange\s*=\s*function[^{]*\{[\s\S]*?\n  \};",
            core_block)
        self.assertTrue(m, "EDITOR.afterChange function not found")
        body = m.group(0)
        for kind in ("rerender", "validate", "persist"):
            self.assertIn(
                'dispatchHooks("%s")' % kind, body,
                "afterChange must dispatch the %s hooks" % kind)
        # The dispatch loop wraps EACH hook call in its own try/catch.
        self.assertRegexpMatches(
            core_block, r"try\s*\{\s*list\[i\]\(\);\s*\}\s*catch",
            "hook dispatch must iterate in try/catch (one broken hook must "
            "never kill the state layer)")


if __name__ == "__main__":
    unittest.main()
