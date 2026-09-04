#!/usr/bin/env python3.6
"""Structural chrome test battery for the Phase 7.1 editor boot asset
(07.1-18 Task 2).

Pins the editor's self-explaining chrome — tools/story_editor_assets/
90_boot.js (status bar + Diagnostics + Help), inlined LAST by the sorted
pipeline — to the 07.1-18 plan contract:

- the chrome asset is the LAST inlined block, closing before the shell
  bootstrap (test_boot_inlined_last)
- the status bar field set renders at all times: loaded / dirty / undo /
  validate / selected plus the B9 ending chip ("CG → Phase 12"), with the
  click-jumps (dirty row → Save tab, validate row → Diagnostics) and the
  05_json.js canary span (#statusbar-serializer) preserved across rebuilds
  (test_status_bar_fields)
- the Diagnostics tab wires the in-page verification surface: the serializer
  self-test entry point (EDITOR.selfTestSerializer, auto-run once on first
  open + on-demand button), the validator entry points (EDITOR.validateCurrent
  / the cached EDITOR._lastValidation), and the build info (the generator's
  __ASSET_MANIFEST__ comment parsed at boot + the per-file FNV-1a data
  fingerprints) (test_diagnostics_entry_points)
- the Help tab carries the whole operating procedure verbatim: the Firefox
  "Always ask you where to save files" recommendation, the git-ignored tmp/
  draft destination, the post-save gate commands (story_editor_lint /
  unittest discover / check_citations / check_edit_coverage / git diff),
  the B9 Phase-12 note, and the offline statement
  (test_help_completeness)
- the B11 extensibility posture paragraph exists: the editor preserves what
  it does not understand — unknown keys/ops round-trip, unknown pasted ops
  are warn-but-accept, never a whitelist rebuild (test_b11_posture)
- ES5 discipline scoped to the chrome block itself: no arrow functions, no
  let/const, no ES modules (test_es5_discipline)
- the asset source header names its owning plan (test_ownership_header)

Page-wide ES5/no-module discipline is already pinned for EVERY block by
tests/test_story_editor_state.py (07.1-04); this battery scopes its ES5
assertions to the boot block so parallel-wave assets never make THIS
battery fail through someone else's in-flight code.

Pure WSL python3.6 -- stdlib only; the generator is subprocessed once per
test class via setUpClass into a temp dir using --output (same conventions
as tests/test_story_editor_save.py: REPO_ROOT via __file__,
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
BOOT_ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "90_boot.js")

# The status-bar field set (07.1-18 must-have: load state, dirty-file
# count, undo depth, validation summary, selection — at all times).
STATUS_FIELDS = ["loaded: ", "dirty: ", "undo: ", "validate: ", "selected: "]

# The B9 chip label (roadmap :285/:296 — ending CG is Phase-12 territory;
# the editor shows a reminder only).
B9_CHIP = "CG \u2192 Phase 12"

# The Help-tab verbatim greps (07.1-18 Task 2 test spec #3): the Firefox
# save-settings recommendation, the draft destination, the post-save gate
# commands, the B9 note, and the offline statement.
HELP_GREPS = [
    "Always ask you where to save files",
    "tmp/",
    "story_editor_lint",
    "unittest discover",
    "check_citations",
    "check_edit_coverage",
    "git diff",
    "story_editor_draft.json",
]

# The post-save gate commands in full (the editor cannot see the
# filesystem — the Python gates are the only authoritative post-save check).
GATE_COMMANDS = [
    "python3.6 tools/story_editor_lint.py",
    "python3.6 -m unittest discover -s tests",
    "python3.6 tools/check_citations.py --story data/story_glucose "
    "--registry data/citations.json",
    "python3.6 tools/check_edit_coverage.py",
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


def _boot_block(html):
    # type: (str) -> str
    """Extract the inlined 90_boot.js <script> block from the page."""
    marker = "/* asset: 90_boot.js"
    m_start = html.find(marker)
    assert m_start >= 0, "90_boot.js asset marker missing from emitted HTML"
    block_open = html.rfind("<script>", 0, m_start)
    block_close = html.find("</script>", m_start)
    assert block_open >= 0 and block_close > block_open, \
        "boot asset block is not a proper classic <script> block"
    return html[block_open:block_close]


class TestBootChromeStructure(unittest.TestCase):
    """Structural checks over the asset SOURCE + one emitted page."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_boot_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.src = _read(BOOT_ASSET) if os.path.isfile(BOOT_ASSET) else ""
        cls.block = _boot_block(cls.html)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Pipeline position: the chrome is the LAST inlined asset.
    # ------------------------------------------------------------------

    def test_boot_inlined_last(self):
        """90_boot.js is the LAST asset block in the emitted page, closing
        before the shell's DOMContentLoaded bootstrap script."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        last_marker = self.html.rfind("/* asset: ")
        self.assertEqual(
            self.html.find("/* asset: 90_boot.js"), last_marker,
            "90_boot.js must be the LAST inlined asset block (the chrome "
            "loads after every capability asset)")
        m = self.html.find("/* asset: 90_boot.js")
        block_close = self.html.find("</script>", m)
        bootstrap = self.html.find(
            "window.addEventListener('DOMContentLoaded'")
        self.assertGreater(bootstrap, 0, "shell bootstrap script missing")
        self.assertLess(
            block_close, bootstrap,
            "the chrome block must close before the shell bootstrap begins")

    # ------------------------------------------------------------------
    # 1. Status bar.
    # ------------------------------------------------------------------

    def test_status_bar_fields(self):
        """The status bar renders the full field set (loaded / dirty / undo
        / validate / selected) plus the B9 ending chip, wired with the
        click-jumps and the canary-span preservation."""
        for field in STATUS_FIELDS:
            self.assertIn(
                field, self.block,
                "status bar field %r missing from the chrome block" % field)
        # The B9 chip: shown when an ending node is selected.
        self.assertIn(B9_CHIP, self.block,
                      "the B9 'CG -> Phase 12' ending chip is missing")
        self.assertIn("sb-b9-chip", self.block, "B9 chip class missing")
        # Click targets: dirty row opens the Save tab, validate row opens
        # the Diagnostics tab, the B9 chip opens Help.
        self.assertIn('data-sb-jump="save"', self.block,
                      "the dirty indicator must jump to the Save tab")
        self.assertIn('data-sb-jump="diagnostics"', self.block,
                      "the validate indicator must jump to Diagnostics")
        self.assertIn('data-sb-jump="help"', self.block,
                      "the B9 chip must jump to the Help tab")
        self.assertIn("EDITOR.showTab", self.block,
                      "the click-jumps must go through EDITOR.showTab")
        # The bar updates through the rerender hook and never destroys the
        # 05_json.js serializer canary span.
        self.assertIn("hooks.rerender.push(renderStatusBar)", self.block,
                      "the status bar must re-render via hooks.rerender")
        self.assertIn("statusbar-serializer", self.block,
                      "the 05_json canary span must be preserved across "
                      "status-bar rebuilds")

    # ------------------------------------------------------------------
    # 2. Diagnostics entry points.
    # ------------------------------------------------------------------

    def test_diagnostics_entry_points(self):
        """The Diagnostics tab wires the serializer self-test and the full
        validator on demand, and renders the inlined asset manifest plus
        the per-file data fingerprints."""
        # (a) Serializer self-test: invoked, with the auto-run-once first
        # open + the on-demand button.
        self.assertIn("EDITOR.selfTestSerializer", self.block,
                      "the diagnostics self-test must call "
                      "EDITOR.selfTestSerializer")
        self.assertIn("runSelfTestOnce", self.block,
                      "the once-only auto-run wrapper is missing")
        self.assertIn('setAttribute("data-diag-action", "selftest")',
                      self.block, "the self-test button is missing")
        # (b) Validator report: runs EDITOR.validateCurrent and consumes
        # the cached verdict from the validate hook.
        self.assertIn("EDITOR.validateCurrent", self.block,
                      "the diagnostics validator must call "
                      "EDITOR.validateCurrent")
        self.assertIn("EDITOR._lastValidation", self.block,
                      "the validator report must reuse the cached hook "
                      "verdict")
        self.assertIn('setAttribute("data-diag-action", "validate")',
                      self.block, "the run-validator button is missing")
        # Errors AND notices with rule ids, plus the count-shift report.
        self.assertIn("countShifts", self.block,
                      "the count-shift acknowledgment report is missing")
        self.assertIn("notices", self.block,
                      "the validator report must render notices, not just "
                      "errors")
        # (c) Build info: the generator's inline manifest parsed at boot.
        # (The literal generator token name is grepped-banned from the
        # emitted page by the generator battery's test_no_token_leaks, so
        # the parse step is pinned by its function name instead.)
        self.assertIn("parseAssetManifest", self.block,
                      "the manifest parse must exist as a named boot step")
        self.assertIn("inlined assets", self.block,
                      "the manifest parse marker is missing")
        self.assertIn("EDITOR.version", self.block,
                      "the build info must show the editor version")
        self.assertIn("fingerprints", self.block,
                      "the per-file FNV-1a fingerprint list is missing")
        self.assertIn("FNV-1a", self.block,
                      "the fingerprint list must name its hash function")

    # ------------------------------------------------------------------
    # 3. Help completeness.
    # ------------------------------------------------------------------

    def test_help_completeness(self):
        """The Help tab contains the whole operating procedure: the Firefox
        save-setting recommendation, the tmp/ draft destination, the
        post-save gate commands, the B9 Phase-12 note, and the offline
        statement."""
        for needle in HELP_GREPS:
            self.assertIn(
                needle, self.block,
                "help content %r missing from the chrome block" % needle)
        # The B9 note (either hyphenated or spaced form).
        self.assertTrue(
            ("Phase-12" in self.block) or ("Phase 12" in self.block),
            "the B9 Phase-12 note is missing from the help content")
        # The offline statement (zero servers / frameworks / requests).
        self.assertIn("Zero servers, zero", self.block,
                      "the offline statement is missing")
        self.assertIn("network requests", self.block,
                      "the offline statement must cover network requests")
        # The full post-save gate commands, verbatim.
        for cmd in GATE_COMMANDS:
            self.assertIn(
                cmd, self.block,
                "post-save gate command %r missing" % cmd)
        # The one honest file:// paragraph with its CVE reference.
        self.assertIn("CVE-2019-11730", self.block,
                      "the file:// origin-policy paragraph must cite "
                      "CVE-2019-11730")
        # The filename-is-a-suggestion caveat (Pitfall 3b).
        self.assertIn("suggestion", self.block,
                      "the download filename caveat is missing")

    # ------------------------------------------------------------------
    # 4. B11 extensibility posture.
    # ------------------------------------------------------------------

    def test_b11_posture(self):
        """The unknown-keys/ops round-trip paragraph exists: the editor
        preserves what it does not understand (round-trip language, the
        warn-but-accept paste rule, never a whitelist rebuild)."""
        self.assertIn("B11", self.block,
                      "the B11 posture section label is missing")
        for word in ("preserve", "round-trip", "warn"):
            self.assertIn(
                word, self.block,
                "the B11 paragraph must use %r language" % word)
        self.assertIn("whitelist", self.block,
                      "the B11 paragraph must state the no-whitelist rule")
        self.assertIn("on_enter", self.block,
                      "the B11 paragraph must cover unknown on_enter ops")

    # ------------------------------------------------------------------
    # 5. ES5 discipline (scoped to the chrome block).
    # ------------------------------------------------------------------

    def test_es5_discipline(self):
        """The chrome block is ES5-classic: no arrow functions, no
        let/const declarations, no ES-module scripts."""
        self.assertIsNone(
            re.search(r"=>", self.block),
            "90_boot.js contains an arrow function (=>); ES5 var-style is "
            "the pinned emitted-JS convention")
        self.assertIsNone(
            re.search(r"\blet\s", self.block),
            "90_boot.js contains a let declaration")
        self.assertIsNone(
            re.search(r"\bconst\s", self.block),
            "90_boot.js contains a const declaration")
        self.assertNotIn('type="module"', self.html)


class TestBootAssetSource(unittest.TestCase):
    """Checks over the asset source file itself."""

    @classmethod
    def setUpClass(cls):
        cls.src = _read(BOOT_ASSET) if os.path.isfile(BOOT_ASSET) else ""

    def test_ownership_header(self):
        """The asset header names its owning plan and its three surfaces."""
        self.assertIn("07.1-18", self.src,
                      "the header must record the owning plan")
        for owned in ("statusbar", "tab-diagnostics", "tab-help"):
            self.assertIn(
                owned, self.src,
                "the header must declare ownership of #%s" % owned)

    def test_source_help_matches_page(self):
        """The asset source carries the same help/gate needles the emitted
        page does (the generator inlines assets verbatim)."""
        for needle in HELP_GREPS[:5]:
            self.assertIn(needle, self.src)
        self.assertIn(B9_CHIP, self.src)


if __name__ == "__main__":
    unittest.main()
