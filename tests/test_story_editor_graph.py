"""Structural graph-view test battery for the Phase 7.1 editor graph asset
(07.1-06 Task 2).

Covers (over tools/story_editor_assets/30_graph.js and the emitted page):
- the graph view is REGISTERED per the 07.1-04 convention:
  EDITOR.view("graph", render) + EDITOR.init(...) present in the asset and
  inlined into the emitted story_editor.html (test_graph_registered,
  test_emitted_page_inlines_graph_asset)
- the LAYOUT CONSTANTS are pinned to the manifest order: the FILE_COL
  literal is extracted from the asset, parsed with the stdlib JSON parser
  (the literal is written strict-JSON), and asserted equal to the
  7-file manifest mapping (intro=0 .. etc=4, endings+bad_endings=5), plus
  the column-6 stub fallback for unmapped ids (test_layout_constants)
- the renderer uses DERIVED kinds -- EDITOR.deriveKind /
  EDITOR.endingTier -- and NEVER reads a stored node_type/tier field
  (no such field exists; RESEARCH-DATA 1.7) (test_derived_kinds_used)
- selection is WIRED: the delegated click handler calls EDITOR.select
  (test_selection_wiring)
- NO PERSISTED COORDINATES: the renderer only READS the bundle; it never
  writes state.bundle or any node/choice field (layout coords are a local
  view model; mutations belong to the 00_core mutators)
  (test_no_persisted_coords)
- ES5 discipline for the asset: no arrow functions, no let/const (pins
  the emitted-JS convention per-asset) (test_es5_discipline)

Pure WSL python3.6 -- stdlib only; the generator is subprocessed once per
test class via setUpClass into a temp dir using --output (same conventions
as tests/test_story_editor_state.py: REPO_ROOT via __file__,
subprocess.run with PIPE streams -- NOT capture_output, which is 3.7+).
The battery greps only THIS plan's asset, so it stays robust while the
parallel Wave-3 agents (10_load.js / 20_validate.js) are in flight.
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
GRAPH_ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "30_graph.js")
MANIFEST_PATH = os.path.join(
    REPO_ROOT, "data", "story_glucose", "manifest.json")

# The 7-column layout mapping (committed viewer FILE_COL, viewer :66-75;
# manifest file order drives everything else). endings.json AND
# bad_endings.json share column 5.
EXPECTED_FILE_COL = {
    "intro.json": 0,
    "glycolysis.json": 1,
    "pyruvate_branch.json": 2,
    "tca.json": 3,
    "etc_atp.json": 4,
    "endings.json": 5,
    "bad_endings.json": 5,
}


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


class TestGraphAssetStructure(unittest.TestCase):
    """Structural checks over the graph asset + ONE emitted page."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_graph_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.asset = _read(GRAPH_ASSET) if os.path.isfile(GRAPH_ASSET) else ""
        cls.manifest = {}
        if os.path.isfile(MANIFEST_PATH):
            with open(MANIFEST_PATH, "r", encoding="utf-8") as fh:
                cls.manifest = json.load(fh)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _graph_block(self):
        # type: () -> str
        """Extract the inlined 30_graph.js <script> block from the page."""
        marker = "/* asset: 30_graph.js"
        m_start = self.html.find(marker)
        self.assertGreaterEqual(
            m_start, 0, "30_graph.js asset marker missing from emitted HTML")
        block_open = self.html.rfind("<script>", 0, m_start)
        self.assertGreaterEqual(
            block_open, 0, "graph asset block has no opening <script>")
        block_close = self.html.find("</script>", m_start)
        self.assertGreaterEqual(
            block_close, 0, "graph asset block is unterminated")
        return self.html[block_open:block_close]

    # ------------------------------------------------------------------
    # 1. Registration (the 07.1-04 contract every later asset follows)
    # ------------------------------------------------------------------

    def test_graph_registered(self):
        """EDITOR.view is called with 'graph' and a named render function;
        the DOM work is registered via EDITOR.init; the asset is a real
        renderer (>= 150 lines)."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        self.assertRegexpMatches(
            self.asset,
            r'EDITOR\.view\(\s*"graph"\s*,\s*renderGraph\s*\)',
            "the asset must register its renderer: "
            'EDITOR.view("graph", renderGraph)')
        self.assertIn(
            "function renderGraph", self.asset,
            "the named render function must exist in the asset")
        self.assertIn(
            "EDITOR.init(", self.asset,
            "the asset must register its DOM work via EDITOR.init")
        self.assertGreaterEqual(
            len(self.asset.splitlines()), 150,
            "the graph renderer must be a real implementation (the plan's "
            "artifact spec asks for >= 150 lines)")

    # ------------------------------------------------------------------
    # 2. Layout constants (manifest order -> 7-column FILE_COL mapping)
    # ------------------------------------------------------------------

    def test_layout_constants(self):
        """The FILE_COL mapping matches the manifest's file order exactly,
        and the column-6 stub fallback is present."""
        m = re.search(r"var FILE_COL = \{([\s\S]*?)\};", self.asset)
        self.assertTrue(
            m, "the FILE_COL literal is missing from the asset")
        # The literal is written strict-JSON (quoted keys, no trailing
        # comma) so the stdlib parser can decode it.
        try:
            mapping = json.loads("{" + m.group(1) + "}")
        except ValueError as e:
            self.fail("FILE_COL literal is not strict JSON: %s" % e)
        self.assertEqual(
            mapping, EXPECTED_FILE_COL,
            "FILE_COL must match the committed viewer's mapping exactly "
            "(intro=0 .. etc=4; endings AND bad_endings share column 5)")
        # The mapping must cover exactly the manifest's file list.
        self.assertEqual(
            sorted(mapping.keys()),
            sorted(self.manifest.get("files", [])),
            "FILE_COL must cover exactly the files the manifest lists")
        # Column-6 fallback: unmapped files AND the Phase-8 stub special
        # ids land in the stubs column (viewer build_model).
        self.assertRegexpMatches(
            self.asset, r"UNMAPPED_COL\s*=\s*6",
            "the unmapped-id fallback must be column 6 (Phase-8 stubs)")
        self.assertIn(
            "Phase-8 stubs", self.asset,
            "the stubs column caption must be present")
        self.assertIn(
            '"fa.stub"', self.asset,
            "the Phase-8 stub special ids must be lifted to column 6")
        self.assertIn(
            '"alc.stub"', self.asset,
            "the Phase-8 stub special ids must be lifted to column 6")
        # The edit.prompt hub lift (row 0 of the endings column) is part
        # of the viewer's layout derivation.
        self.assertIn(
            '"edit.prompt"', self.asset,
            "the edit.prompt hub lift must be ported")

    # ------------------------------------------------------------------
    # 3. Derived kinds (never a stored node_type/tier field)
    # ------------------------------------------------------------------

    def test_derived_kinds_used(self):
        """The renderer derives kinds via EDITOR.deriveKind and the ending
        level via EDITOR.endingTier, and NEVER reads a node_type or tier
        field (none exists in the schema; kinds are computed, RESEARCH-DATA
        1.7)."""
        self.assertIn(
            "EDITOR.deriveKind", self.asset,
            "the renderer must use the shared derived-kind port")
        self.assertIn(
            "EDITOR.endingTier", self.asset,
            "the renderer must use the shared ending-level port")
        self.assertIsNone(
            re.search(r"node_type", self.asset),
            "the renderer must not reference a node_type field (it does "
            "not exist; kinds are DERIVED)")
        self.assertIsNone(
            re.search(r"\.tier\b", self.asset),
            "the renderer must not read a .tier property (the ending level "
            "comes from EDITOR.endingTier)")
        self.assertIsNone(
            re.search(r"\[\s*['\"]tier['\"]\s*\]", self.asset),
            "the renderer must not read a ['tier'] key")
        self.assertNotIn('"tier"', self.asset)
        self.assertNotIn("'tier'", self.asset)

    # ------------------------------------------------------------------
    # 4. Selection wiring (graph click -> shared state -> node form)
    # ------------------------------------------------------------------

    def test_selection_wiring(self):
        """The delegated node click calls EDITOR.select (feeding the node
        form + status bar), and double-click opens the form focus."""
        self.assertIn(
            "EDITOR.select(", self.asset,
            "the click handler must call EDITOR.select with the node id")
        self.assertRegexpMatches(
            self.asset,
            r'EDITOR\.delegate\(\s*svg\s*,\s*"click"\s*,\s*"data-node-id"',
            "selection must be ONE delegated click listener on the svg "
            "container keyed by data-node-id (never per-node listeners)")
        self.assertRegexpMatches(
            self.asset,
            r'EDITOR\.delegate\(\s*svg\s*,\s*"dblclick"\s*,\s*"data-node-id"',
            "double-click must be delegated too (form focus)")

    # ------------------------------------------------------------------
    # 5. No persisted coordinates (read-only bundle access)
    # ------------------------------------------------------------------

    def test_no_persisted_coords(self):
        """The renderer never writes back into the bundle: no
        state.bundle assignment, no node/choice field writes. Layout
        coordinates are a LOCAL view model rebuilt per render; every
        mutation belongs to the 00_core mutators (one apply step each)."""
        self.assertIsNone(
            re.search(r"EDITOR\.state\.bundle\s*=", self.asset),
            "the renderer must never assign state.bundle")
        self.assertIsNone(
            re.search(r"EDITOR\.state\.bundle\.[A-Za-z_$][\w$]*\s*=[^=]",
                      self.asset),
            "the renderer must never mutate a bundle sub-field")
        self.assertIsNone(
            re.search(r"\bnodes\s*\[[^\]]+\]\s*=[^=]", self.asset),
            "the renderer must never write a node (mutators only)")
        self.assertIsNone(
            re.search(r"\bnode\.[A-Za-z_$][\w$]*\s*=[^=]", self.asset),
            "the renderer must never write a node field (mutators only)")
        # The read-only contract is documented in the asset header.
        self.assertIn(
            "READ-ONLY", self.asset,
            "the header must document the read-only bundle access")

    # ------------------------------------------------------------------
    # 6. ES5 discipline (the emitted-JS convention, per-asset pin)
    # ------------------------------------------------------------------

    def test_es5_discipline(self):
        """The asset is ES5-classic: no arrow functions, no let/const, no
        module markers (modules fail under file:// CORS; var-style keeps
        the emitted JS reviewable)."""
        self.assertIsNone(
            re.search(r"=>", self.asset),
            "arrow functions are forbidden (ES5 var-style is the pinned "
            "emitted-JS convention)")
        self.assertIsNone(
            re.search(r"\blet\s", self.asset),
            "let declarations are forbidden")
        self.assertIsNone(
            re.search(r"\bconst\s", self.asset),
            "const declarations are forbidden")
        self.assertNotIn('type="module"', self.asset)

    # ------------------------------------------------------------------
    # 7. Emitted page: inlining + the plan's verify-step strings
    # ------------------------------------------------------------------

    def test_emitted_page_inlines_graph_asset(self):
        """The emitted story_editor.html inlines the graph asset with the
        registration, the FILE_COL literal, the arrowhead marker defs and
        the zoom handler -- in pipeline order (after 05_json.js, before the
        shell bootstrap)."""
        block = self._graph_block()
        self.assertIn('EDITOR.view("graph", renderGraph)', block)
        self.assertIn("var FILE_COL", block)
        # Arrowhead marker defs (grey solid + amber dashed) + marker-end
        # references on the edge paths.
        self.assertIn('"arrow-solid"', block)
        self.assertIn('"arrow-amber"', block)
        self.assertIn("marker-end", block)
        # Zoom handler (wheel) + the bounded zoom constants.
        self.assertIn('"wheel"', block)
        self.assertIn("ZOOM_MIN", block)
        self.assertIn("ZOOM_MAX", block)
        # Pipeline order: 00_core.js first (defines EDITOR), then
        # 05_json.js, then 30_graph.js, then the shell bootstrap. The
        # bootstrap anchor is the LAST "EDITOR.runInits()" occurrence --
        # the core asset CONTAINS the definition text early in the page,
        # so a plain find() would anchor on the wrong one (the same
        # ambiguity 07.1-04's Rule-3 fix resolved for DOMContentLoaded).
        core_idx = self.html.find("/* asset: 00_core.js")
        json_idx = self.html.find("/* asset: 05_json.js")
        graph_idx = self.html.find("/* asset: 30_graph.js")
        boot_idx = self.html.rfind("EDITOR.runInits();")
        self.assertGreaterEqual(core_idx, 0)
        self.assertGreaterEqual(json_idx, 0)
        self.assertGreaterEqual(graph_idx, 0)
        self.assertGreaterEqual(boot_idx, 0)
        self.assertLess(core_idx, graph_idx,
                        "the core must inline before the graph asset")
        self.assertLess(json_idx, graph_idx,
                        "the serializer asset must inline before the graph")
        self.assertLess(graph_idx, boot_idx,
                        "the graph asset must inline before the bootstrap")


if __name__ == "__main__":
    unittest.main()
