"""Structural test battery for the Phase 7.1 story-editor generator
(07.1-01 Task 2).

Covers:
- default emission to the committed repo-root story_editor.html
  (test_emits_repo_root_html)
- zero unresolved __TOKEN__ placeholders, incl. the generic __UPPERCASE__
  residue scan (test_no_token_leaks)
- offline safety: no external src/href references, no <link> tags, no
  ES-module scripts, no top-level JS import statements in the emitted
  script blocks (test_offline_no_external_refs)
- shell structure: boot panel, all 7 tab containers + data-tab buttons,
  node-form sidebar WITH all four fixed sub-sections, status bar, and the
  DOMContentLoaded bootstrap (test_shell_structure)
- asset auto-inlining: a probe *.js dropped into tools/story_editor_assets/
  is inlined as its own classic <script> block AFTER the shell markup and
  BEFORE the bootstrap (test_asset_auto_inline); the probe file is deleted
  in tearDownClass -- it is NEVER committed
- EDITOR_FAIL + exit 1 + no output file on a corrupted story copy
  (test_editor_fail_on_corrupt_copy; fixture-driven minimal manifest)
- generator style pin: no f-string prefixes in tools/story_editor.py
  (test_generator_python36_style; the repo convention is also enforced by
  review -- this pins it)

Pure WSL python3.6 -- stdlib only; the generator is subprocessed once per
test class via setUpClass into a temp dir using --output (same conventions
as tests/test_check_alter_gate.py: REPO_ROOT via __file__, subprocess.run
with PIPE streams -- NOT capture_output, which is Python 3.7+).
"""
import json
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
ASSETS_DIR = os.path.join(REPO_ROOT, "tools", "story_editor_assets")
DEFAULT_EMITTED = os.path.join(REPO_ROOT, "story_editor.html")

PROBE_NAME = "zz_probe.js"
PROBE_MARKER = "/*PROBE_MARKER_71*/"

TAB_IDS = ["graph", "trace", "claims", "data", "save", "diagnostics", "help"]


def json_dumps(obj):
    # type: (dict) -> str
    """Compact deterministic JSON for fixtures (2-space indent, repo style)."""
    return json.dumps(obj, indent=2, sort_keys=False)


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


class TestEmittedShell(unittest.TestCase):
    """Structural checks over ONE emitted page (written to a temp path via
    --output; the generator is subprocessed once in setUpClass)."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_gen_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_generation_succeeds(self):
        """Precondition: the generator exits 0 and emits non-empty HTML."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        self.assertTrue(self.html, "generator emitted no HTML")

    def test_no_token_leaks(self):
        """Zero unresolved tokens: the three named tokens AND any generic
        __UPPERCASE__-pattern residue must be absent from the emitted HTML."""
        for token in ("__TITLE__", "__GENERATED_AT__", "__ASSET_MANIFEST__",
                      "__ASSETS__"):
            self.assertNotIn(token, self.html,
                             "unresolved token %s leaked into the HTML" % token)
        residue = re.search(r"__[A-Z][A-Z0-9_]*__", self.html)
        self.assertIsNone(
            residue,
            "generic __TOKEN__-pattern residue found: %r" % (residue and residue.group(0)))

    def test_offline_no_external_refs(self):
        """Offline-safe: no external script/link references, no ES modules,
        no top-level import statements in the emitted script blocks."""
        # No <script src=...> and no <link ...> tags at all.
        self.assertIsNone(
            re.search(r"<script[^>]*\ssrc=", self.html),
            "external script reference found")
        self.assertIsNone(
            re.search(r"<link\s", self.html),
            "<link> tag found (styles must be inline)")
        # Belt and braces: no http(s) URLs in src/href attributes.
        self.assertNotIn('src="http', self.html)
        self.assertNotIn('href="http', self.html)
        # No ES-module scripts (module scripts fail under file:// CORS).
        self.assertNotIn('type="module"', self.html)
        # No top-level import statements in any classic script block
        # (import is module-only syntax; a bare occurrence would be a
        # SyntaxError at runtime anyway -- this pins the discipline).
        blocks = re.findall(r"<script>(.*?)</script>", self.html, re.S)
        self.assertTrue(
            blocks, "expected at least the DOMContentLoaded bootstrap block")
        for block in blocks:
            self.assertIsNone(
                re.search(r"(?m)^\s*import(?:\s|[\"('\)])", block),
                "top-level import statement found in script block: %r"
                % block[:80])

    def test_shell_structure(self):
        """Boot panel, all 7 tab containers + data-tab buttons, node-form
        sidebar with all four fixed sub-sections, status bar, bootstrap."""
        required_ids = [
            # boot panel + its mounts
            "boot-panel", "boot-probe-status", "boot-pick-mount",
            "boot-checklist", "boot-draft-mount",
            # tab nav + the 7 content containers
            "tabbar", "tab-graph", "tab-trace", "tab-claims", "tab-data",
            "tab-save", "tab-diagnostics", "tab-help",
            # node-form sidebar + the 4 FIXED sub-sections
            "node-form", "node-form-identity", "node-form-choices",
            "node-form-onenter", "node-form-lifecycle",
            # status bar
            "statusbar",
        ]
        for rid in required_ids:
            self.assertIn('id="%s"' % rid, self.html, "missing #%s" % rid)
        for tab in TAB_IDS:
            self.assertIn('data-tab="%s"' % tab, self.html,
                          "missing data-tab button for %s" % tab)
        # The classic DOMContentLoaded bootstrap must be present verbatim-ish.
        self.assertIn("DOMContentLoaded", self.html)
        self.assertIn("EDITOR.runInits", self.html)
        # The static boot-panel copy must document the expected sub-directory
        # layout (the "detect sub-dir" contract).
        for expected in ("data/story_glucose/", "data/citations.json",
                         "data/sources.json", "rpg/data/edits.json",
                         "rpg/data/cast.json"):
            self.assertIn(expected, self.html,
                          "boot-panel copy missing expected path %s" % expected)


class TestDefaultPathEmission(unittest.TestCase):
    """test_emits_repo_root_html: the DEFAULT invocation (no --output) writes
    the committed repo-root story_editor.html.

    NOTE (deviation from the plan's literal wording, recorded in the plan
    summary): the plan says "delete the emitted file in tearDown to keep the
    worktree clean" -- but story_editor.html is a COMMITTED artifact, so
    deleting it would leave the worktree dirty after every suite run. This
    test instead snapshots the pre-test bytes and RESTORES them in tearDown
    (delete only if the file did not exist before -- the fresh-clone case),
    which keeps the worktree byte-identical to pre-test in both worlds.
    """

    def setUp(self):
        self._had_file = os.path.isfile(DEFAULT_EMITTED)
        self._saved = None
        if self._had_file:
            with open(DEFAULT_EMITTED, "rb") as fh:
                self._saved = fh.read()

    def tearDown(self):
        if self._had_file and self._saved is not None:
            with open(DEFAULT_EMITTED, "wb") as fh:
                fh.write(self._saved)
        elif not self._had_file and os.path.isfile(DEFAULT_EMITTED):
            os.remove(DEFAULT_EMITTED)

    def test_emits_repo_root_html(self):
        proc = run_generator([])
        self.assertEqual(
            proc.returncode, 0,
            "default invocation failed\nstdout: %s\nstderr: %s"
            % (proc.stdout, proc.stderr))
        self.assertTrue(
            os.path.isfile(DEFAULT_EMITTED),
            "default invocation did not write %s" % DEFAULT_EMITTED)
        html = _read(DEFAULT_EMITTED)
        self.assertTrue(html.startswith("<!doctype html>"),
                        "emitted file is not an HTML document")
        self.assertIn("Story Node Editor", html,
                      "emitted file lacks the editor title")


class TestAssetAutoInline(unittest.TestCase):
    """test_asset_auto_inline: any *.js dropped into tools/story_editor_assets/
    is auto-inlined (sorted) with NO generator edit. A probe file proves the
    pipeline; it is deleted in tearDownClass and never committed."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_probe_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.probe_path = os.path.join(ASSETS_DIR, PROBE_NAME)
        with open(cls.probe_path, "w", encoding="utf-8") as fh:
            fh.write(PROBE_MARKER + "\n")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)

    @classmethod
    def tearDownClass(cls):
        # NEVER leave the probe file behind (it must not be committed).
        try:
            os.remove(cls.probe_path)
        except OSError:
            pass
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_asset_auto_inline(self):
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed with the probe asset\nstdout: %s\nstderr: %s"
            % (self.proc.stdout, self.proc.stderr))
        idx = self.html.find(PROBE_MARKER)
        self.assertGreater(idx, -1,
                           "probe marker missing from the emitted HTML")
        # The marker must sit INSIDE a classic <script> block: the nearest
        # opening <script> before it must come after the nearest closing
        # </script> before it.
        open_tag = self.html.rfind("<script>", 0, idx)
        prior_close = self.html.rfind("</script>", 0, idx)
        self.assertGreaterEqual(open_tag, 0, "no <script> before the marker")
        self.assertGreater(
            open_tag, prior_close,
            "probe marker is not inside a <script> block")
        self.assertEqual(self.html[open_tag:open_tag + len("<script>")],
                         "<script>",
                         "the asset must be a CLASSIC script (no attributes)")
        # The asset block must come AFTER the shell markup (status bar is the
        # last structural element) and BEFORE the DOMContentLoaded bootstrap.
        statusbar_idx = self.html.find('id="statusbar"')
        self.assertGreater(
            idx, statusbar_idx,
            "asset block must be inlined after the shell markup")
        close_tag = self.html.find("</script>", idx)
        self.assertGreaterEqual(close_tag, 0, "unterminated script block")
        bootstrap_idx = self.html.find("DOMContentLoaded")
        self.assertGreater(
            bootstrap_idx, close_tag,
            "the bootstrap script must come after the asset blocks")


class TestEditorFailOnCorruptCopy(unittest.TestCase):
    """test_editor_fail_on_corrupt_copy: a minimal corrupted manifest copy
    (a goto pointing at a nonexistent node) must produce EDITOR_FAIL + exit 1
    and NO output file."""

    def test_editor_fail_on_corrupt_copy(self):
        tmp = tempfile.mkdtemp(prefix="story_editor_corrupt_")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        story_dir = os.path.join(tmp, "story_glucose")
        os.makedirs(story_dir)
        manifest = {
            "version": 1, "default_seed": 0, "start": "a.start",
            "files": ["broken.json"],
        }
        with open(os.path.join(story_dir, "manifest.json"), "w",
                  encoding="utf-8") as fh:
            fh.write(json_dumps(manifest))
        broken = {
            "nodes": {
                "a.start": {
                    "text_dramatic": "dramatic", "text_teaching": "teaching",
                    "claim_ids": [], "tags": [], "on_enter": [],
                    "choices": [{"label": "Continue", "goto": "a.missing"}],
                },
            },
        }
        with open(os.path.join(story_dir, "broken.json"), "w",
                  encoding="utf-8") as fh:
            fh.write(json_dumps(broken))
        out_path = os.path.join(tmp, "should_not_exist.html")
        proc = run_generator(["--story-dir", story_dir, "--output", out_path])
        self.assertEqual(
            proc.returncode, 1,
            "corrupt copy must exit 1\nstdout: %s\nstderr: %s"
            % (proc.stdout, proc.stderr))
        combined = proc.stdout + proc.stderr
        self.assertIn("EDITOR_FAIL", combined,
                      "failure output must carry the EDITOR_FAIL sentinel")
        self.assertIn("a.missing", combined,
                      "the failing goto target should be named in the reason")
        self.assertFalse(
            os.path.isfile(out_path),
            "no output file may be written when the gate fails")


class TestGeneratorPython36Style(unittest.TestCase):
    """test_generator_python36_style: tools/story_editor.py must contain no
    f-string prefixes (the repo convention is also enforced by review; this
    pins it)."""

    def test_generator_python36_style(self):
        src = _read(GENERATOR)
        self.assertNotIn('f"', src,
                         'f-string prefix f" found in tools/story_editor.py')
        self.assertNotIn("f'", src,
                         "f-string prefix f' found in tools/story_editor.py")


if __name__ == "__main__":
    unittest.main()
