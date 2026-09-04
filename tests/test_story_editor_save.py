#!/usr/bin/env python3.6
"""Structural persistence-layer test battery for the Phase 7.1 editor save
asset (07.1-13 Task 2).

Pins Requirement E's save half to the BINDING user directive model
("saving temp/final json could be more simple and universal. no api, no
server") exactly as 07.1-RESEARCH-UI.md "Persistence — universal no-API
model" + Code Examples 3-4 + Pitfalls 3 / 3b / 3c and 07.1-RESEARCH-SAFETY
"Save-edit semantics" + Pitfall S3 prescribe:

- the FILE SYSTEM ACCESS API is BANNED: the asset contains NONE of the
  showSaveFilePicker / showOpenFilePicker / showDirectoryPicker /
  FileSystemHandle symbols, and the ban is documented in the header
  (test_no_fsa_api)
- every file-body serialization goes through EDITOR.housy.stringify (the
  07.1-05 house-style port); the naive two-argument pretty-print form has
  ZERO occurrences; bodies carry the trailing newline the Python file
  write appends (test_house_style_only)
- the display-only destination map lists all four non-story targets plus
  the data/story_glucose/ story prefix, and save rows render the file
  name with its exact repo-relative destination (test_destinations_displayed)
- the draft doc is self-contained: version / saved_at / bundle / dirty /
  undo_meta / fingerprints, downloaded as story_editor_draft.json with the
  git-ignored tmp/ guidance; dirty is emitted as an OBJECT MAP because the
  landed 10_load.js loadDraft restores maps (an array would corrupt the
  dirty state -- documented deviation, test_draft_doc_shape)
- the post-save gate reminder names the lint, the suite, the citation gate
  and the git diff review verbatim (test_gate_reminder)
- stale-draft detection: EDITOR.save.staleCheck compares fingerprints
  against the load layer's folder raw texts via the core FNV-1a; the loud
  warning + Load-anyway / Discard / Re-check options are present, wired to
  10_load.js's onDraftLoaded hook point (test_stale_check)
- localStorage is the OPTIONAL guarded crash copy only: the MDN
  storageAvailable try/catch pattern, an 800 ms debounced hooks.persist
  write, a boot restore/dismiss banner, failures silently swallowed, and
  an explicit non-load-bearing statement (test_local_storage_guarded)
- the save gate (EDITOR.saveBlocked refusal + error list), the per-row
  mark-saved arm/confirm (dirty cleared ONLY on explicit confirm, git as
  the atomicity layer) and the sequential ~400 ms batch
  (test_save_gate_and_rows)
- the save asset is inlined into the emitted page in sorted position with
  the plan-mandated needles, before the shell bootstrap
  (test_save_layer_inlined)
- ES5 discipline for the save asset itself (var/function only, no arrows,
  no modules) (test_es5_discipline)

Page-wide ES5/no-module discipline is already pinned for EVERY block by
tests/test_story_editor_state.py (07.1-04); this battery scopes its ES5
assertions to the save block so parallel-wave assets never make THIS
battery fail through someone else's in-flight code.

Runtime behavior (panel render, byte-identity of the downloadable bodies,
the mark-saved flow, discard rebuild, crash copy) is proven by the
48-check headless-Chrome smoke recorded in the 07.1-13 summary (07.1-08
harness precedent); this battery pins the structure mechanically.

Pure WSL python3.6 -- stdlib only; the generator is subprocessed once per
test class via setUpClass into a temp dir using --output (same conventions
as tests/test_story_editor_load.py: REPO_ROOT via __file__,
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
SAVE_ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "80_save.js")

# The banned File System Access API symbols (the binding user directive
# rejects the API outright; grep-guarded here so it can never creep in).
FSA_SYMBOLS = [
    "showSaveFilePicker",
    "showOpenFilePicker",
    "showDirectoryPicker",
    "FileSystemHandle",
]

# The display-only destination map (RESEARCH-UI Code Example 4).
DEST_ENTRIES = [
    '"citations.json": "data/citations.json"',
    '"sources.json": "data/sources.json"',
    '"edits.json": "rpg/data/edits.json"',
    '"cast.json": "rpg/data/cast.json"',
]
STORY_PREFIX = 'var STORY_DIR_PREFIX = "data/story_glucose/"'

# The post-save gate commands (RESEARCH-UI Pitfall 3 + RESEARCH-SAFETY save
# sequence: the editor cannot see the filesystem -- the Python gates are
# the only authoritative post-save check).
GATE_COMMANDS = [
    "python3.6 tools/story_editor_lint.py",
    "python3.6 -m unittest discover -s tests",
    "python3.6 tools/check_citations.py --story data/story_glucose "
    "--registry data/citations.json",
    "git diff",
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
    """Extract the inlined 80_save.js <script> block from the page."""
    marker = "/* asset: 80_save.js"
    m_start = html.find(marker)
    assert m_start >= 0, "80_save.js asset marker missing from emitted HTML"
    block_open = html.rfind("<script>", 0, m_start)
    block_close = html.find("</script>", m_start)
    assert block_open >= 0 and block_close > block_open, \
        "save asset block is not a proper classic <script> block"
    return html[block_open:block_close]


class TestSaveAssetStructure(unittest.TestCase):
    """Structural checks over the asset SOURCE + one emitted page."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_save_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.src = _read(SAVE_ASSET) if os.path.isfile(SAVE_ASSET) else ""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. The File System Access API is BANNED (binding user directive)
    # ------------------------------------------------------------------

    def test_no_fsa_api(self):
        """NONE of the FSA symbols may appear anywhere in the asset (the
        user directive bans the API outright: "no api, no server"), the
        ban must be documented in the header, and the emitted save block
        carries the same absence."""
        for sym in FSA_SYMBOLS:
            self.assertNotIn(
                sym, self.src,
                "the File System Access API is BANNED by the binding user "
                "directive: symbol %s found in the save asset" % sym)
        block = _asset_block(self.html)
        for sym in FSA_SYMBOLS:
            self.assertNotIn(
                sym, block,
                "emitted save block contains the banned symbol %s" % sym)
        # The ban is documented (so the intent survives review), and the
        # binding directive is cited verbatim.
        self.assertIn(
            "FILE SYSTEM ACCESS API IS BANNED", self.src,
            "the header must state the FSA ban explicitly")
        self.assertIn(
            "no api, no server", self.src,
            "the binding user directive must be cited verbatim")
        self.assertIn(
            "test_no_fsa_api", self.src,
            "the header must name the grep-guard that enforces the ban")

    # ------------------------------------------------------------------
    # 2. House style only (RESEARCH-SAFETY Pitfall S1)
    # ------------------------------------------------------------------

    def test_house_style_only(self):
        """Every file-body serialization calls EDITOR.housy.stringify; the
        naive two-argument pretty-print form has ZERO occurrences; the
        body carries the trailing newline the Python file write appends."""
        self.assertIn(
            "EDITOR.housy.stringify", self.src,
            "the save asset must serialize through the house-style port")
        # Both body paths: the draft doc AND the per-file row body.
        self.assertIn(
            'EDITOR.housy.stringify(draftDoc())', self.src,
            "the draft download must serialize the draftDoc house-style")
        self.assertIn(
            "function serializeBody(content) {\n"
            "    return EDITOR.housy.stringify(content) + \"\\n\";\n"
            "  }",
            self.src,
            "the row body must be housy-serialized + the trailing newline "
            "the Python file write appends")
        self.assertNotIn(
            "null, 2", self.src,
            "the naive JSON.stringify(x, null, 2) pretty-print is banned "
            "(it would reflow whole files -- Pitfall S1)")
        self.assertIsNone(
            re.search(r"JSON\.stringify\([^)]*,\s*null", self.src),
            "no two-argument JSON.stringify with a null spacer may appear "
            "anywhere in the save asset")

    # ------------------------------------------------------------------
    # 3. Display-only destinations on every save row (Pitfall 3)
    # ------------------------------------------------------------------

    def test_destinations_displayed(self):
        """The destination map lists all four non-story targets plus the
        story prefix; save rows render the file name AND its exact
        repo-relative destination; the editor never writes (display-only
        is stated)."""
        for entry in DEST_ENTRIES:
            self.assertIn(
                entry, self.src,
                "destination map entry missing: %s" % entry)
        self.assertIn(
            STORY_PREFIX, self.src,
            "the story-file destination prefix must be declared")
        self.assertIn(
            "function destFor(", self.src,
            "the dest lookup helper missing")
        self.assertIn(
            "save over ", self.src,
            "save rows must render 'save over <destination>'")
        # The row builder must emit BOTH the fname and its destination.
        row_i = self.src.find("function renderSaveRow(")
        self.assertGreaterEqual(row_i, 0, "renderSaveRow missing")
        row_body = self.src[row_i:self.src.find("function renderSave(")]
        self.assertIn("def.fname", row_body,
                      "the row must render the file name")
        self.assertIn("def.dest", row_body,
                      "the row must render the destination")
        self.assertIn(
            "DISPLAY-ONLY", self.src,
            "the map must be documented as display-only (the editor never "
            "writes)")
        self.assertIn(
            "NEVER writes to the repository", self.src,
            "the no-write guarantee must be stated")

    # ------------------------------------------------------------------
    # 4. Self-contained draft doc (ROADMAP E, tmp/ guidance)
    # ------------------------------------------------------------------

    def test_draft_doc_shape(self):
        """draftDoc carries version / saved_at / bundle / dirty / undo_meta
        / fingerprints; the download is story_editor_draft.json with the
        git-ignored tmp/ guidance; dirty is an OBJECT MAP matching the
        landed loader's restore semantics (documented deviation)."""
        fn_i = self.src.find("function draftDoc(")
        self.assertGreaterEqual(fn_i, 0, "draftDoc missing")
        fn_body = self.src[fn_i:self.src.find("EDITOR.save.draftDoc")]
        for field in ("version: 1", "saved_at:", "bundle:",
                      "dirty:", "undo_meta:", "fingerprints:"):
            self.assertIn(
                field, fn_body,
                "draftDoc must carry the %s field" % field.rstrip(":"))
        self.assertIn(
            "undo_depth", fn_body,
            "undo_meta must record the undo depth")
        self.assertIn(
            "redo_depth", fn_body,
            "undo_meta must record the redo depth")
        self.assertIn(
            'var DRAFT_FILENAME = "story_editor_draft.json";', self.src,
            "the draft download name must be the pinned constant")
        self.assertIn(
            "tmp/", self.src,
            "the draft guidance must name the repo's tmp/ folder")
        self.assertIn(
            "git-ignored", self.src,
            "the draft guidance must state tmp/ is git-ignored")
        # The dirty-map deviation: the landed loader restores maps.
        self.assertIn(
            "OBJECT MAP", self.src,
            "the dirty-map deviation must be documented in-source")
        self.assertIn(
            "loadDraft", self.src,
            "the deviation must cite the landed loader (10_load.js "
            "loadDraft)")

    # ------------------------------------------------------------------
    # 5. Post-save gate reminder (the only authoritative check)
    # ------------------------------------------------------------------

    def test_gate_reminder(self):
        """The reminder names the lint command, the unittest suite, the
        citation gate and the git diff review verbatim."""
        for cmd in GATE_COMMANDS:
            self.assertIn(
                cmd, self.src,
                "post-save gate command missing verbatim: %s" % cmd)
        self.assertIn(
            "renderReminder", self.src,
            "the reminder box builder missing")
        self.assertIn(
            "cannot see the filesystem", self.src,
            "the reminder must state why the Python gates are the only "
            "authoritative post-save check")

    # ------------------------------------------------------------------
    # 6. Stale-draft detection (Pitfall S3)
    # ------------------------------------------------------------------

    def test_stale_check(self):
        """EDITOR.save.staleCheck compares fingerprints against the load
        layer's folder raw texts via the core FNV-1a; the loud warning and
        the Load-anyway / Discard / Re-check options are present; the hook
        point is 10_load.js's onDraftLoaded."""
        self.assertIn(
            "EDITOR.save.staleCheck = function (fingerprints)", self.src,
            "the staleCheck API must live at the 07.1-13-expected path")
        self.assertIn(
            "folderRawByFname", self.src,
            "staleCheck must compare against the load layer's folder raw "
            "texts")
        self.assertIn(
            "EDITOR.fnv1a(raw)", self.src,
            "the comparison must use the core FNV-1a drift detector")
        self.assertIn(
            "Data changed since this draft was saved — loading may clobber "
            "newer changes",
            self.src,
            "the loud warning phrase is required (Pitfall S3)")
        self.assertIn(
            "Load anyway", self.src, "the Load-anyway option is required")
        self.assertIn(
            "Discard", self.src, "the Discard option is required")
        self.assertIn(
            "Re-check against folder", self.src,
            "the re-check-after-re-pick button is required")
        self.assertIn(
            "EDITOR.load.onDraftLoaded", self.src,
            "the save layer must register the 07.1-07 onDraftLoaded hook "
            "point")
        # Discard is work-protected: it refuses while in-session edits
        # exist (undo/redo depths non-zero) instead of destroying work.
        discard_i = self.src.find("function discardDraft(")
        self.assertGreaterEqual(discard_i, 0, "discardDraft missing")
        discard_body = self.src[discard_i:discard_i + 3000]
        self.assertIn(
            "EDITOR.undoDepth() !== 0", discard_body,
            "discard must check the undo depth before rebuilding")
        self.assertIn(
            "EDITOR.redoDepth() !== 0", discard_body,
            "discard must check the redo depth before rebuilding")
        self.assertIn(
            "rebuildBundleFromRaws", self.src,
            "the folder-baseline rebuild helper is required")

    # ------------------------------------------------------------------
    # 7. localStorage: optional guarded crash copy ONLY
    # ------------------------------------------------------------------

    def test_local_storage_guarded(self):
        """The MDN storageAvailable try/catch pattern is present, the
        debounced (800 ms) hooks.persist write stores the draft doc, the
        boot banner offers restore/dismiss, failures are silently
        swallowed, and the copy is explicitly non-load-bearing."""
        self.assertIn(
            "function storageAvailable(type)", self.src,
            "the MDN storageAvailable feature-detect is required")
        # The try/catch guard shape (browsers expose the property but
        # throw on use -- never a bare truthiness check).
        guard_i = self.src.find("function storageAvailable(type)")
        guard_body = self.src[guard_i:self.src.find("function downloadText(")]
        self.assertIn("try {", guard_body,
                      "storageAvailable must try/catch (MDN pattern)")
        self.assertIn("setItem(x, x)", guard_body,
                      "storageAvailable must probe with a real write")
        self.assertIn(
            '"rpg_story_editor_crash_draft"', self.src,
            "the crash-copy localStorage key must be pinned")
        self.assertIn(
            "CRASH_DEBOUNCE_MS = 800", self.src,
            "the crash copy is debounced 800 ms after the last mutation")
        self.assertIn(
            "EDITOR.hooks.persist.push(scheduleCrashCopy)", self.src,
            "the crash copy must ride the persist hook (07.1-04 contract)")
        self.assertIn(
            "non-load-bearing", self.src,
            "the crash copy must be documented as non-load-bearing")
        self.assertIn(
            "silently swallowed", self.src,
            "storage failures must be documented as silently swallowed")
        self.assertIn(
            "found — restore?", self.src,
            "the boot banner must offer the crash-copy restore")
        self.assertIn(
            '"crash-dismiss"', self.src,
            "the banner must offer the dismiss action")

    # ------------------------------------------------------------------
    # 8. Save gate + mark-saved + sequential batch
    # ------------------------------------------------------------------

    def test_save_gate_and_rows(self):
        """Saves are refused while EDITOR.saveBlocked() (the error list is
        shown instead); mark-saved clears dirty ONLY via the explicit
        arm/confirm and re-derives through core's recomputeDirty; the
        opt-in batch fires rows sequentially with ~400 ms gaps."""
        self.assertIn(
            "EDITOR.saveBlocked()", self.src,
            "the save panel must gate on the validator (07.1-08 contract)")
        gate_i = self.src.find("if (blocked) {")
        self.assertGreaterEqual(gate_i, 0, "the blocked branch missing")
        gate_body = self.src[gate_i:gate_i + 2000]
        self.assertIn(
            "Save blocked", gate_body,
            "the blocked state must be announced loudly")
        self.assertIn(
            "EDITOR.validateCurrent()", gate_body,
            "the blocked state must list the validator errors")
        # mark-saved: arm/confirm + explicit-only + baseline reset
        self.assertIn(
            '"mark saved"', self.src, "the mark-saved control is required")
        self.assertIn(
            '"mark-confirm"', self.src,
            "the explicit confirm step is required")
        self.assertIn(
            "confirm: file placed over ", self.src,
            "the confirm step must name the destination")
        mark_i = self.src.find("function markSaved(")
        self.assertGreaterEqual(mark_i, 0, "markSaved missing")
        mark_body = self.src[mark_i:self.src.find("EDITOR.save.markSaved")]
        self.assertIn(
            "EDITOR.save.recomputeDirty()", mark_body,
            "markSaved must re-derive dirty through core's recomputeDirty")
        self.assertIn(
            "EDITOR._originals[fname]", mark_body,
            "markSaved must reset the per-file dirty baseline")
        # Sequential opt-in batch with ~400 ms gaps (Pitfall 3).
        self.assertIn(
            "var BATCH_GAP_MS = 400;", self.src,
            "the batch gap constant must be 400 ms")
        self.assertIn(
            "~400 ms gaps", self.src,
            "the batch must document the ~400 ms gaps")
        self.assertIn(
            "setTimeout(next, BATCH_GAP_MS)", self.src,
            "the batch must fire rows sequentially via setTimeout")
        self.assertIn(
            "Download all (", self.src,
            "the opt-in batch button is required")

    # ------------------------------------------------------------------
    # 9. Emitted-HTML integration
    # ------------------------------------------------------------------

    def test_save_layer_inlined(self):
        """The generator emits the save asset: the 80_save.js block is
        inlined in sorted position, carries the plan-mandated needles, and
        closes before the shell bootstrap."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        markers = re.findall(r"/\* asset: (\S+) \(", self.html)
        self.assertIn("80_save.js", markers, "save asset not inlined")
        self.assertEqual(
            markers, sorted(markers),
            "asset blocks must inline in sorted order: %r" % (markers,))
        block = _asset_block(self.html)
        for needle in ("downloadText", "draftDoc", "story_editor_draft.json",
                       "tmp/", "data/story_glucose/", "rpg/data/",
                       "storageAvailable", "~400 ms gaps", "story_editor_lint",
                       "unittest discover", "git diff",
                       "save over ", "mark saved",
                       "Always ask you where to save files",
                       "Data changed since this draft was saved"):
            self.assertIn(needle, block,
                          "emitted save block lacks %r" % needle)
        # The block must close before the shell's bootstrap (the LAST
        # classic script block).
        block_close = self.html.find("</script>",
                                     self.html.find("/* asset: 80_save.js"))
        boot_i = self.html.rfind("EDITOR.runInits")
        self.assertLess(
            block_close, boot_i,
            "the save asset block must precede the shell bootstrap")

    # ------------------------------------------------------------------
    # 10. ES5 discipline + header traceability
    # ------------------------------------------------------------------

    def test_es5_discipline(self):
        """The save asset itself stays ES5-classic: var/function only, no
        arrow functions, no let/const, no template literals, no modules,
        and no literal </script (the inlining hazard)."""
        self.assertNotIn("=>", self.src,
                         "arrow function found in the save asset")
        self.assertIsNone(re.search(r"\blet\s", self.src),
                          "let declaration found in the save asset")
        self.assertIsNone(re.search(r"\bconst\s", self.src),
                          "const declaration found in the save asset")
        self.assertNotIn("`", self.src,
                         "template literal found in the save asset")
        self.assertNotIn('type="module"', self.src,
                         "module script found in the save asset")
        self.assertNotIn("</script", self.src,
                         "literal </script would break the inline block")
        self.assertIn('"use strict"', self.src,
                      "the IIFE must run in strict mode")
        self.assertIn("(function () {", self.src,
                      "the asset must be one IIFE (pipeline convention)")
        # Header traceability: ownership + the binding mechanism set.
        self.assertIn("07.1-13", self.src,
                      "the header must cite its owner plan")
        self.assertIn("Persistence", self.src,
                      "the header must cite RESEARCH-UI Persistence")
        self.assertIn("RESEARCH-SAFETY", self.src,
                      "the header must cite RESEARCH-SAFETY")
        self.assertIn("Pitfall 3b", self.src,
                      "the filename-is-a-suggestion pitfall must be cited")
        # The registration convention (07.1-04).
        self.assertIn('EDITOR.view("save", renderSave)', self.src,
                      "the save view must be registered")
        self.assertIn("EDITOR.init(", self.src,
                      "the asset must register its DOM init")


if __name__ == "__main__":
    unittest.main()
