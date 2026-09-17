"""Structural load-layer test battery for the Phase 7.1 editor boot asset
(07.1-07 Task 2; re-pinned by the 07.1-11 fix-forward; re-pinned again by
the round-3 file:// policy correction -- debug session
.planning/debug/story-editor-file-load.md -- and once more by the round-4
fix-forward: the one-click folder PICK removed per the user verdict
"drag-and-drop working, upload button not working ... maybe better remove
the upload button").

Root causes fixed across the rounds:

1. (07.1-11) The boot probe used fetch(), which CANNOT read file:// URLs
   in Firefox at all -- CVE-2019-11730/MFSA 2019-21 removed file: URLs
   from the Fetch API. The probe moved to XMLHttpRequest.
   (test_direct_probe_then_fallback)
1b. (round 3) The 07.1-11 premise "classic reads stay permitted same
   directory or below under security.fileuri.strict_origin_policy
   (default true)" is DEAD in current Firefox. VERIFIED EMPIRICALLY on
   the user's own Firefox 155.0.1 (fresh default profile, headless sync
   XHR + iframe probes; the user's real profile carries no fileuri
   override): with defaults, a file:// page permits NO programmatic file
   reads at all (sync XHR throws NetworkError on EXISTING same-dir,
   subdir and 2-level files; iframe documents DISPLAY -- the user's
   network_all.html proof was display-only -- but
   iframe.contentDocument is null). strict_origin_policy=false restores
   classic reads (sync XHR status 200 + readable iframe DOMs);
   privacy.file_unique_origin is irrelevant; Chrome needs
   --allow-file-access-from-files (verified end-to-end auto-load on the
   real page with that flag). Consequence: the XHR probe stays (it is
   correct wherever reads are permitted -- http(s) serving, the Chrome
   flag, a pref flip), and the DEFAULT path is the ONE-GESTURE fallback.
   (test_direct_probe_then_fallback, test_dragdrop_folder_zone)
2. The round-3 ONE-GESTURE fallback: a drag-and-drop folder zone
   (DataTransferItem.webkitGetAsEntry recursive traversal -- readEntries
   BATCHES discipline; File objects fetched ONLY for the WANTED paths;
   .git enumerated by name only); a document-level dragover/drop
   canceler keeps stray drops from navigating the page away.
   (test_dragdrop_folder_zone)
3. (round 4) The one-click folder pick (the round-2 snapshot-before-clear
   repair included) was user-verified DEAD in the real browser across
   three repair rounds while drag-and-drop loaded the same tree in both
   Firefox and Chrome -- REMOVED per the user directive ("maybe better
   remove the upload button"). (test_pick_path_removed)
4. The boot ceremony (long static explanation wall + probe-then-fallback
   choreography) is reduced to the simple model the user demanded; the
   copy now tells the truth about the default (auto reads blocked,
   one gesture loads everything). (test_simplified_boot_copy)

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
        # Guard-then-match order inside the drop handler (the flat-fallback
        # branch): unsafe paths are rejected BEFORE any matching/reading
        # decision.
        handler_start = self.src.find("function onDrop(")
        self.assertGreaterEqual(handler_start, 0, "drop handler missing")
        guard_i = self.src.find("pathIsUnsafe(rel2)", handler_start)
        match_i = self.src.find("matchesExpected(rel2)", handler_start)
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
        # The corrected policy record: the CVE is cited for what it
        # actually removed (fetch on file://), the controlling pref is
        # named, the legacy read window is described (and marked CLOSED by
        # default), and the round-3 empirical verdict is pinned: current
        # default Firefox permits NO programmatic file reads from file://.
        self.assertIn(
            "CVE-2019-11730", self.src,
            "the transport correction must cite CVE-2019-11730")
        self.assertIn(
            "strict_origin_policy", self.src,
            "the corrected claim must name security.fileuri."
            "strict_origin_policy")
        self.assertIn(
            "same directory or below", self.src,
            "the record must describe the legacy read window (now closed "
            "by default): same directory or below")
        self.assertIn(
            "NO programmatic file reads", self.src,
            "the round-3 empirical verdict must be pinned: default "
            "Firefox 155 permits NO programmatic file reads from file://")
        self.assertIn(
            'version: "0.4.0"', self.src,
            "the round-4 pick-removal rework must bump EDITOR.load to 0.4.0")
        # The green auto-load banner survives (the zero-click success state
        # where reads ARE permitted: http(s), the Chrome flag, a pref flip).
        self.assertIn(
            "Data auto-detected in sub-directories", self.src,
            "the zero-click success banner phrase must survive")

    # ------------------------------------------------------------------
    # 4d. The drag-and-drop ONE-GESTURE fallback (round 3)
    # ------------------------------------------------------------------

    def test_dragdrop_folder_zone(self):
        """The drop path: a mounted #boot-drop-zone wired to onDrop; the
        recursive webkitGetAsEntry traversal observes the readEntries
        BATCHES discipline and applies the same pathIsUnsafe guards; File
        objects are fetched ONLY for the WANTED paths (the whole tree is
        enumerated by name only); the drop completes through the SAME
        pickFlow with pickSource "drop" (dropped-folder wording); the
        fallback is mounted at init; and a document-level dragover/drop
        canceler keeps stray drops from navigating away."""
        # The zone + its wiring, mounted at init with the fallback panel.
        self.assertIn(
            "boot-drop-zone", self.src,
            "the drag-and-drop zone element is missing")
        self.assertIn(
            "function mountDropZone(", self.src,
            "the zone mount is missing")
        self.assertIn(
            "function onDrop(", self.src,
            "the drop handler is missing")
        self.assertIn(
            "function installGlobalDropGuard(", self.src,
            "the stray-drop navigation guard is missing")
        init_i = self.src.find("ED.init(function () {")
        self.assertGreaterEqual(init_i, 0, "the load init is missing")
        self.assertGreater(
            self.src.find("mountFolderPick();", init_i), init_i,
            "the fallback panel wrap must still be mounted at init")
        mount_i = self.src.find("mountDropZone();", init_i)
        guard_i = self.src.find("installGlobalDropGuard();", init_i)
        self.assertGreater(
            mount_i, init_i,
            "the drop zone must be mounted at init")
        self.assertGreater(
            guard_i, mount_i,
            "the global drop guard must be installed at init")
        boot_i = self.src.find("boot();", init_i)
        self.assertGreater(
            boot_i, guard_i,
            "the direct probe still runs after the mounts (probe-first)")
        # Document-level stray-drop cancels (navigation would lose the page).
        self.assertIn(
            'addEventListener("dragover"', self.src,
            "dragover cancel missing (a stray drop would navigate away)")
        self.assertIn(
            'addEventListener("drop"', self.src,
            "drop cancel missing (a stray drop would navigate away)")
        # The recursive entry traversal + batch discipline.
        self.assertIn(
            "webkitGetAsEntry", self.src,
            "the drop must walk DataTransferItems via webkitGetAsEntry")
        self.assertIn(
            "function traverseEntry(", self.src,
            "the recursive directory walker is missing")
        self.assertIn(
            "readEntries", self.src,
            "the directory reader must use readEntries")
        self.assertIn(
            "BATCHES", self.src,
            "the readEntries BATCHES discipline must be documented (a "
            "single call silently truncates big folders)")
        self.assertIn(
            "empty batch", self.src,
            "the walker must re-call readEntries until an empty batch")
        trav_i = self.src.find("function traverseEntry(")
        guard2_i = self.src.find("pathIsUnsafe(rel)", trav_i)
        self.assertGreater(
            guard2_i, trav_i,
            "the drop walker must apply the same pathIsUnsafe guards")
        # File objects are materialized ONLY for the WANTED paths (never
        # the whole dropped tree).
        self.assertIn(
            "ONLY for the WANTED paths", self.src,
            "the wanted-paths-only File discipline must be documented")
        self.assertIn(
            "function getFileAt(", self.src,
            "the File/FileSystemEntry normalizer is missing")
        self.assertIn(
            "function materializeFiles(", self.src,
            "the wanted-files materializer is missing")
        # The drop completes through the same pickFlow (source "drop").
        drop_i = self.src.find("function onDrop(")
        flow_i = self.src.find("pickFlow();", drop_i)
        self.assertGreater(
            flow_i, drop_i,
            "the drop must complete through the shared pickFlow")
        self.assertIn(
            'bootState.pickSource = "drop"', self.src,
            "the drop must mark pickSource (dropped-folder wording)")
        self.assertIn(
            "Data loaded from the dropped folder", self.src,
            "the dropped-folder success banner phrase is required")
        self.assertIn(
            "you dropped", self.src,
            "the checklist blocked-copy must name the dropped gesture "
            "('expected under the folder you dropped...')")

    # ------------------------------------------------------------------
    # 4b. The one-click folder pick is GONE (round-4 fix-forward)
    # ------------------------------------------------------------------

    def test_pick_path_removed(self):
        """The one-click folder pick (including its round-2 snapshot fix)
        was removed per the user verdict -- 'drag-and-drop working, upload
        button not working ... maybe better remove the upload button'.
        The pick path is unrecoverable by accident: no directory-select
        file input, no pick handler, no pick-side machinery tokens, and
        the drop path is the ONLY gesture beside the direct probe."""
        self.assertNotIn(
            "webkitdirectory", self.src,
            "no directory-select file input may remain (the pick is gone)")
        self.assertNotIn(
            "onFolderPicked", self.src,
            "the pick change handler must be gone")
        self.assertNotIn(
            "boot-folder-input", self.src,
            "the pick input element id must be gone")
        self.assertNotIn(
            "Select your repository folder", self.src,
            "the pick label copy must be gone")
        self.assertNotIn(
            "Data loaded from the picked folder", self.src,
            "the picked-folder banner phrase must be gone")
        self.assertNotIn(
            'bootState.pickSource = "pick"', self.src,
            "no code path may mark the source 'pick'")
        # The drop path is intact as the one gesture.
        self.assertIn(
            "Drag your repository folder here", self.src,
            "the drop zone affordance must survive the pick removal")
        self.assertIn(
            "Data loaded from the dropped folder", self.src,
            "the dropped-folder banner phrase must survive")

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
        for needle in ("boot-drop-zone", "matchesExpected", "readAsText",
                       "Load draft", ".json,application/json",
                       "XMLHttpRequest", "webkitGetAsEntry"):
            self.assertIn(needle, block,
                          "emitted load block lacks %r" % needle)
        self.assertNotIn("webkitdirectory", block,
                         "the pick input must be gone from the emitted "
                         "load block too")
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
