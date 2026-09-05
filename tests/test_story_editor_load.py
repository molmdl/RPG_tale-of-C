"""Structural load-layer test battery for the Phase 7.1 editor boot asset
(07.1-07 Task 2; re-pinned by the 07.1-11 fix-forward).

The 07.1-11 human checkpoint verdict was REJECTED: opening the page in
Firefox auto-loaded nothing (no clicks, no graph) and even the folder pick
did nothing at all. Root causes fixed here:

1. The boot probe used fetch(), which CANNOT read file:// URLs in Firefox
   (>= 68) under any policy -- CVE-2019-11730/MFSA 2019-21 removed file:
   URLs from the Fetch API ("The Fetch API can then be used to read the
   contents of any files stored in these directories" was the vulnerability
   being closed). Classic subresource reads are NOT banned:
   security.fileuri.strict_origin_policy (default true) lets a file://
   document read files in the SAME DIRECTORY OR BELOW -- the user's own
   tmp/network_all.html proves a same-dir <iframe src> loads in their
   Firefox. The direct load therefore runs over XMLHttpRequest, so opening
   the page in Firefox auto-loads data/ + rpg/data/ with ZERO clicks.
   (test_direct_probe_then_fallback)
2. The folder-pick handler cleared input.value = "" while still holding the
   LIVE input.files list; in Firefox the captured reference empties with
   the clear, so the handler silently returned before doing anything ("even
   upload not working at all"). The File objects are now snapshotted into a
   plain array BEFORE the clear. (test_pick_snapshot_before_clear)
3. The boot ceremony (long static explanation wall + probe-then-pick
   choreography) is reduced to the simple model the user demanded:
   open-and-go direct load, ONE button in the fallback, minimal copy.
   (test_simplified_boot_copy)

Still pinned from 07.1-07 (unchanged contract):

- the fixed 5-path EXPECTED list appears verbatim, and the story files are
  resolved DYNAMICALLY from the loaded manifest (manifest.files) -- the
  story file names are NEVER hard-listed in the asset (test_expected_paths)
- the "/"-boundary suffix matcher exists (parent-of-repo picks match,
  child-folder picks match nothing by design) (test_suffix_matcher)
- the three security guards (.." / drive letter / leading "/) are present
  and run BEFORE matching in the folder-pick handler; .git is filtered,
  never enumerated into reads (test_security_guards)
- the draft-reload input (accept=".json,application/json") parses the
  {version, saved_at, bundle, dirty, undo_meta, fingerprints} schema and
  exposes the EDITOR.load.onDraftLoaded hook point
  (test_draft_reload_input)
- required-vs-degrade: rpg/data/edits.json is BLOCKING (required edit
  target); citations/sources/cast degrade-with-warning
  (test_required_vs_degrade)
- the registry duplicate-key guard (parseNoDupKeys / collectTopLevelKeys)
  is applied to BOTH read-only registries (test_registry_duplicate_key_guard)
- the load layer is inlined into the emitted HTML after 00_core.js and
  05_json.js, before the shell bootstrap (test_load_layer_inlined)
- ES5 discipline for the load asset itself (var/function only, no arrows,
  no modules) (test_es5_discipline)

Page-wide ES5/no-module discipline is already pinned for EVERY block by
tests/test_story_editor_state.py (07.1-04); this battery scopes its ES5
assertions to the load block so parallel-wave assets never make THIS
battery fail through someone else's in-flight code.

Pure WSL python3.6 -- stdlib only; the generator is subprocessed once per
test class via setUpClass into a temp dir using --output (same conventions
as tests/test_story_editor_state.py: REPO_ROOT via __file__,
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
LOAD_ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "10_load.js")

# The fixed expected-path list (the binding user directive: sub-directories
# of the HTML's own dir). Verbatim per the 07.1-07 plan.
EXPECTED_PATHS = [
    "data/story_glucose/manifest.json",
    "data/citations.json",
    "data/sources.json",
    "rpg/data/edits.json",
    "rpg/data/cast.json",
]

# The manifest's current story files -- the asset must NOT name any of them
# (story files are resolved FROM the loaded manifest, never hard-listed).
STORY_FILE_NAMES = [
    "intro.json", "glycolysis.json", "pyruvate_branch.json", "tca.json",
    "etc_atp.json", "endings.json", "bad_endings.json",
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


def _asset_block(html):
    # type: (str) -> str
    """Extract the inlined 10_load.js <script> block from the page."""
    marker = "/* asset: 10_load.js"
    m_start = html.find(marker)
    assert m_start >= 0, "10_load.js asset marker missing from emitted HTML"
    block_open = html.rfind("<script>", 0, m_start)
    block_close = html.find("</script>", m_start)
    assert block_open >= 0 and block_close > block_open, \
        "load asset block is not a proper classic <script> block"
    return html[block_open:block_close]


class TestLoadAssetStructure(unittest.TestCase):
    """Structural checks over the asset SOURCE + one emitted page."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_load_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.src = _read(LOAD_ASSET) if os.path.isfile(LOAD_ASSET) else ""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. EXPECTED paths + manifest-driven story resolution
    # ------------------------------------------------------------------

    def test_expected_paths(self):
        """The 5 expected paths appear verbatim in the asset, the story
        files are resolved dynamically from manifest.files, and NONE of the
        real story file names are hard-listed anywhere in the asset."""
        for path in EXPECTED_PATHS:
            self.assertIn(
                path, self.src,
                "expected path %s missing from the asset's EXPECTED list"
                % path)
        # Dynamic resolution: the manifest's "files" array drives the
        # story-file list (manifest.files), and story paths are built as
        # STORY_DIR_PREFIX + fname -- never hard-listed before it loads.
        self.assertIn(
            "manifest.files", self.src,
            "the asset must reference manifest.files (dynamic resolution)")
        self.assertIn(
            "function storyPathsOf(", self.src,
            "a story-paths builder from the parsed manifest must exist")
        self.assertIn(
            "storyPathsOf(mres.files)", self.src,
            "the direct auto-load must derive story paths from mres.files")
        self.assertIn(
            "STORY_DIR_PREFIX + fname", self.src,
            "the pick path must build story paths as prefix + manifest name")
        for fname in STORY_FILE_NAMES:
            self.assertNotIn(
                fname, self.src,
                "story file %s must NOT be hard-listed in the asset (story "
                "files resolve FROM the loaded manifest)" % fname)

    # ------------------------------------------------------------------
    # 2. "/"-boundary suffix matcher
    # ------------------------------------------------------------------

    def test_suffix_matcher(self):
        """A suffix-matching helper exists and implements the "/"-boundary
        comparison (exact match OR ends with "/" + expected): a parent of
        the repo matches, a child folder matches nothing by design."""
        self.assertIn(
            "function matchesExpected(", self.src,
            "matchesExpected helper missing")
        self.assertIn(
            "function matchesSuffix(", self.src,
            "the generalized /-boundary suffix matcher missing")
        # The boundary comparison pattern: lastIndexOf + the length checks
        # around a "/" boundary char.
        self.assertIn(
            "lastIndexOf(", self.src,
            "the suffix match must use lastIndexOf (boundary position)")
        self.assertIn(
            "rel.charAt(rel.length - exp.length - 1) === \"/\"",
            self.src,
            "the match must verify the / BOUNDARY character (a parent-of-"
            "repo pick works; a child pick must not match)")
        self.assertIn(
            "rel.length > exp.length",
            self.src,
            "the match must check the length relation before the boundary")
        self.assertIn(
            "repository root", self.src,
            "the child-pick case must tell the user to select the "
            "repository root")

    # ------------------------------------------------------------------
    # 3. Security guards (Pitfall 3c)
    # ------------------------------------------------------------------

    def test_security_guards(self):
        """The three rejections (.., drive letter, leading /) are present,
        they run BEFORE matching in the folder-pick handler, and .git is
        filtered against the expected paths -- never enumerated into reads."""
        self.assertIn(
            'indexOf("..") >= 0', self.src,
            "guard for '..' traversal missing")
        self.assertIn(
            "/^[A-Za-z]:/", self.src,
            "drive-letter guard regex missing")
        self.assertIn(
            'charAt(0) === "/"', self.src,
            "leading-slash guard missing")
        self.assertIn(
            "function pathIsUnsafe(", self.src,
            "the guards must live in one pathIsUnsafe helper")
        # Guard-then-match order inside the pick handler: unsafe paths are
        # rejected BEFORE any matching/reading decision.
        handler_start = self.src.find("function onFolderPicked(")
        self.assertGreaterEqual(handler_start, 0, "pick handler missing")
        guard_i = self.src.find("pathIsUnsafe(rel)", handler_start)
        match_i = self.src.find("matchesExpected(rel)", handler_start)
        self.assertGreater(guard_i, 0, "the guard must run in the handler")
        self.assertGreater(match_i, 0, "the match must run in the handler")
        self.assertLess(
            guard_i, match_i,
            "pathIsUnsafe must reject BEFORE matchesExpected is consulted")
        # .git discipline: filtered against the expected list, never read.
        self.assertIn(
            ".git", self.src,
            "the .git caution must be documented (Pitfall 3c)")
        self.assertRegexpMatches(
            self.src,
            r"\.git[\s\S]{0,200}(never|NEVER)",
            "the .git note must state it is never enumerated into reads")

    # ------------------------------------------------------------------
    # 4. Direct-read-first boot (the 07.1-11 corrected contract)
    # ------------------------------------------------------------------

    def test_direct_probe_then_fallback(self):
        """The direct load runs over XMLHttpRequest (NOT fetch), the probe
        call textually precedes ANY reference to the pick-panel reveal, the
        fallback is wired into the probe-miss path only, a watchdog guards
        against a dead loading state, and the comment carries the
        CORRECTED Firefox file:// policy claim."""
        # Transport: XHR, never fetch (fetch cannot read file:// URLs).
        self.assertIn(
            "new XMLHttpRequest()", self.src,
            "the direct read must use XMLHttpRequest (fetch() cannot read "
            "file:// URLs)")
        self.assertNotIn(
            "fetch(", self.src,
            "no fetch( call may remain in the load asset (the rejected "
            "premise: fetch was read as 'file:// blocks reads' when it "
            "only proved 'fetch cannot do file://')")
        # Probe-then-fallback order: the probe call textually precedes every
        # reference to the reveal function.
        probe_i = self.src.find("xhrText(MANIFEST_PATH")
        self.assertGreaterEqual(probe_i, 0, "the manifest probe is missing")
        reveal_first = self.src.find("showFolderPickPanel")
        self.assertGreaterEqual(reveal_first, 0, "reveal function missing")
        self.assertLess(
            probe_i, reveal_first,
            "the direct-read probe must be invoked before ANY reference to "
            "the pick-panel reveal (probe-then-fallback order)")
        # The fallback sits in the probe-miss callback.
        miss_i = self.src.find("showFolderPickPanel(", probe_i)
        self.assertGreater(
            miss_i, probe_i,
            "the probe-miss path must reveal the pick panel")
        # Never a dead "loading..." state: a probe watchdog reveals the
        # picker if the direct read never settles.
        self.assertIn(
            "setTimeout", self.src,
            "a probe watchdog is required (never a dead loading state)")
        # The corrected policy claim: strict_origin_policy permits
        # same-directory-or-below reads (the user's iframe precedent), and
        # the CVE is cited for what it actually removed (fetch on file://).
        self.assertIn(
            "CVE-2019-11730", self.src,
            "the transport correction must cite CVE-2019-11730")
        self.assertIn(
            "strict_origin_policy", self.src,
            "the corrected claim must name security.fileuri."
            "strict_origin_policy")
        self.assertIn(
            "same directory or below", self.src,
            "the corrected claim must state the permitted scope: same "
            "directory or below")
        # The green auto-load banner survives (the zero-click success state).
        self.assertIn(
            "Data auto-detected in sub-directories", self.src,
            "the zero-click success banner phrase must survive")

    # ------------------------------------------------------------------
    # 4b. The folder-pick live-FileList fix (07.1-11)
    # ------------------------------------------------------------------

    def test_pick_snapshot_before_clear(self):
        """The pick handler snapshots the File objects into a plain array
        BEFORE clearing input.value: setting input.value = "" empties a
        LIVE input.files list, and the original code checked files.length
        after the clear -- silently returning on Firefox (the 'even upload
        not working at all' defect)."""
        handler_start = self.src.find("function onFolderPicked(")
        self.assertGreaterEqual(handler_start, 0, "pick handler missing")
        snap_i = self.src.find("picked.push(files[j])", handler_start)
        self.assertGreater(
            snap_i, 0,
            "the handler must snapshot files[j] into a plain array")
        clear_i = self.src.find('input.value = ""', handler_start)
        self.assertGreater(clear_i, 0, "the input re-pick clear is missing")
        self.assertLess(
            snap_i, clear_i,
            "the snapshot must happen BEFORE input.value is cleared (a "
            "live FileList empties with the clear)")
        # The post-clear iteration must use the snapshot, not the live list.
        loop_i = self.src.find("picked.length", clear_i)
        self.assertGreater(
            loop_i, clear_i,
            "the path walk must iterate the snapshot (picked[...]), not "
            "the possibly-emptied live list")

    # ------------------------------------------------------------------
    # 4c. Simplified boot copy (the 'too much ceremony' verdict)
    # ------------------------------------------------------------------

    def test_simplified_boot_copy(self):
        """The over-engineered boot copy is gone: the long file://-blocked
        explanation sentence is absent, the fallback note is short and
        keeps the two load-bearing phrases (expected + repository root),
        and the static expected-layout wall is hidden at init (the
        checklist rows already state every expected path)."""
        self.assertNotIn(
            "Your browser blocks local file reads from file:// pages",
            self.src,
            "the rejected long file://-blocked explanation sentence must "
            "be gone (the direct load is the primary path now)")
        self.assertIn(
            "expected", self.src,
            "the fallback note must keep the 'expected' honesty clause")
        self.assertIn(
            "repository root", self.src,
            "the fallback note must say to select the repository root")
        # The static help wall is hidden at init (the panel's own subtree).
        self.assertIn(
            'document.getElementById("boot-help-copy")', self.src,
            "the static expected-layout wall must be hidden by the load "
            "layer (open-and-go: no copy wall)")
        hide_i = self.src.find('document.getElementById("boot-help-copy")')
        set_i = self.src.find('setAttribute("hidden", "hidden")', hide_i)
        self.assertGreater(
            set_i, hide_i,
            "the help wall must be hidden via setAttribute('hidden')")

    # ------------------------------------------------------------------
    # 5. Draft reload input
    # ------------------------------------------------------------------

    def test_draft_reload_input(self):
        """A single-file draft input with the accept attribute exists,
        parses the draft schema fields, routes the bundle through
        EDITOR.setBundle, and exposes the onDraftLoaded hook point."""
        self.assertIn(
            'accept", ".json,application/json', self.src,
            'the draft input must carry accept=".json,application/json"')
        self.assertIn(
            "Load draft", self.src,
            "the draft input must be labeled 'Load draft…'")
        for field in ("draft.bundle", "draft.version", "draft.saved_at",
                      "draft.dirty", "draft.fingerprints"):
            self.assertIn(
                field, self.src,
                "the draft loader must read the schema field %s" % field)
        self.assertIn(
            "ED.setBundle(draft.bundle, null)", self.src,
            "the draft bundle must be loaded through EDITOR.setBundle")
        self.assertIn(
            "onDraftLoaded", self.src,
            "the EDITOR.load.onDraftLoaded hook point is required (07.1-13)")
        self.assertIn(
            "underlying files changed since this draft", self.src,
            "the stale-draft warning phrase is required")
        self.assertIn(
            "function compareDraftToFolderRaw(", self.src,
            "the fingerprint comparison helper is required")
        self.assertIn(
            "ED.fnv1a(raw)", self.src,
            "the staleness comparison must use the core FNV-1a fingerprints")
        self.assertIn(
            "undo_meta", self.src,
            "the undo_meta draft field must be acknowledged")

    # ------------------------------------------------------------------
    # 6. Required vs degrade
    # ------------------------------------------------------------------

    def test_required_vs_degrade(self):
        """rpg/data/edits.json is blocking-required; citations/sources/cast
        degrade-with-warning; manifest-listed story files always block."""
        # The severity spec table classifies each expected path.
        self.assertRegexpMatches(
            self.src,
            r"path:\s*\"rpg/data/edits\.json\",\s*severity:\s*\"block\"",
            "edits.json must be classified BLOCK (required edit target)")
        for degraded in ("data/citations.json", "data/sources.json",
                         "rpg/data/cast.json"):
            self.assertRegexpMatches(
                self.src,
                r"path:\s*\"%s\",\s*severity:\s*\"warn\"" % re.escape(degraded),
                "%s must be classified WARN (degrade-with-warning)"
                % degraded)
        self.assertIn(
            "viewer convention", self.src,
            "the cast degrade must cite the viewer convention")
        self.assertIn(
            "claims panel", self.src,
            "the citations/sources degrade must mention the claims panel")
        # The severityFor fallback: manifest-listed story files block.
        self.assertRegexpMatches(
            self.src,
            r'return "block";[^\n]*story',
            "severityFor must default story files to BLOCK")
        # The blocking branch actually fires on edits failure, and the
        # degrade branch pushes warnings for the registries.
        self.assertIn(
            'blockers.push(path + " is missing")', self.src,
            "a block-severity missing file must push a blocker")
        self.assertIn(
            "warnings.push(", self.src,
            "a warn-severity file must push a degrade warning")
        self.assertIn(
            "Editor cannot start", self.src,
            "blocked loads must show an explicit cannot-start banner")

    # ------------------------------------------------------------------
    # 6b. Registry duplicate-key guard (RESEARCH-DATA §3 row 4)
    # ------------------------------------------------------------------

    def test_registry_duplicate_key_guard(self):
        """parseNoDupKeys (JSON.parse + a depth-1 duplicate-key walk) exists,
        is documented as a top-level approximation, and is applied to BOTH
        read-only registries on load."""
        self.assertIn(
            "function parseNoDupKeys(", self.src,
            "parseNoDupKeys missing")
        self.assertIn(
            "function collectTopLevelKeys(", self.src,
            "the depth-1 key collector missing")
        self.assertIn(
            "duplicate top-level key", self.src,
            "the duplicate error must name the duplicated key")
        self.assertIn(
            "APPROXIMATION", self.src,
            "the top-level-only approximation must be documented")
        # Applied to both registries (and ONLY to them -- writable files
        # parse plainly).
        guard_call = ('path === "data/citations.json" || '
                      'path === "data/sources.json"')
        self.assertIn(
            guard_call, self.src,
            "the duplicate-key guard must gate BOTH registries")
        guard_i = self.src.find(guard_call)
        call_i = self.src.find("parseNoDupKeys(text, path)", guard_i)
        self.assertGreater(
            call_i, 0,
            "the registries must be parsed through parseNoDupKeys")

    # ------------------------------------------------------------------
    # 7. Emitted-HTML integration + ES5 discipline
    # ------------------------------------------------------------------

    def test_load_layer_inlined(self):
        """The generator emits the load layer: the 10_load.js block is
        inlined in sorted position (after 00_core.js and 05_json.js, before
        the bootstrap) and carries the plan-mandated load machinery."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        markers = re.findall(r"/\* asset: (\S+) \(", self.html)
        self.assertIn("10_load.js", markers, "load asset not inlined")
        self.assertEqual(
            markers, sorted(markers),
            "asset blocks must inline in sorted order: %r" % (markers,))
        self.assertLess(
            markers.index("00_core.js"), markers.index("10_load.js"),
            "the load asset must come after the core asset (EDITOR contract)")
        block = _asset_block(self.html)
        for needle in ("webkitdirectory", "matchesExpected", "readAsText",
                       "Load draft", ".json,application/json",
                       "XMLHttpRequest"):
            self.assertIn(needle, block,
                          "emitted load block lacks %r" % needle)
        # The block must close before the shell's bootstrap (the LAST
        # classic script block).
        block_close = self.html.find("</script>",
                                     self.html.find("/* asset: 10_load.js"))
        boot_i = self.html.rfind("EDITOR.runInits")
        self.assertLess(
            block_close, boot_i,
            "the load asset block must precede the shell bootstrap")

    def test_es5_discipline(self):
        """The load asset itself stays ES5-classic: var/function only, no
        arrow functions, no let/const, no template literals, no modules,
        and no literal </script (the inlining hazard)."""
        self.assertNotIn("=>", self.src,
                         "arrow function found in the load asset")
        self.assertIsNone(re.search(r"\blet\s", self.src),
                          "let declaration found in the load asset")
        self.assertIsNone(re.search(r"\bconst\s", self.src),
                          "const declaration found in the load asset")
        self.assertNotIn("`", self.src,
                         "template literal found in the load asset")
        self.assertNotIn('type="module"', self.src,
                         "module script found in the load asset")
        self.assertNotIn("</script", self.src,
                         "literal </script would break the inline block")
        self.assertIn('"use strict"', self.src,
                      "the IIFE must run in strict mode")
        self.assertIn("(function () {", self.src,
                      "the asset must be one IIFE (pipeline convention)")
        # Header traceability: ownership + the binding mechanism set.
        self.assertIn("07.1-07", self.src,
                      "the header must cite its owner plan")
        self.assertIn("07.1-11", self.src,
                      "the fix-forward record must cite plan 07.1-11")
        self.assertIn("Persistence", self.src,
                      "the header must cite RESEARCH-UI Persistence")


if __name__ == "__main__":
    unittest.main()
