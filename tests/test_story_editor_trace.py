"""Structural trace test battery for the Phase 7.1 editor trace asset
(07.1-10 Task 2) -- Requirement D: "trace a path and show the traced flow
as a nested list, to view as a full story".

Covers (over tools/story_editor_assets/60_trace.js and the emitted page):
- the trace view is REGISTERED per the 07.1-04 convention:
  EDITOR.view("trace", renderTrace) + EDITOR.init(...) present in the asset
  and inlined into the emitted story_editor.html (test_registered,
  test_emitted_page_inlines_trace_asset)
- the CYCLE GUARD is real: the walk carries a visited set and a revisit
  renders the arrow-marker leaf instead of recursing (test_cycle_guard)
- THE WALK IS GOTO-ONLY (the load-bearing pin): the named traceWalk
  function reads choice.goto and NEVER consults weight/cond for structure
  -- its body contains no weight/cond tokens at all (weight/cond live only
  in the display layer, which runs after the walk). This is what makes the
  traced node set agree with the Python gate's reachability BFS
  (rpg/story/validate.py:167) (test_goto_only_walk)
- the DEFAULT trace root is manifest.start (intro.preface in the live
  data), not a hardcoded id (test_start_default)
- the copy-as-text helper exists WITH a fallback path (clipboard ->
  execCommand -> select-a-textarea) (test_copy_helper)
- nested-list MARKUP: the renderer builds ul/li trees with details/summary
  branches and an indented plain-text formatter (test_nested_list_markup)
- the controls row exists: start select, trace-from-selection, copy,
  collapse/expand all, feedback span (test_controls)
- the not-loaded placeholder exists (test_placeholder)
- ES5 discipline for the asset (test_es5_discipline)

Pure WSL python3.6 -- stdlib only; the generator is subprocessed once per
test class via setUpClass into a temp dir using --output (same conventions
as tests/test_story_editor_graph.py: REPO_ROOT via __file__,
subprocess.run with PIPE streams -- NOT capture_output, which is 3.7+).
The battery greps only THIS plan's asset (60_trace.js), so it stays robust
while the parallel Wave-4 agents (40_form.js / 70_claims.js / 80_save.js)
are in flight.
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
TRACE_ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "60_trace.js")
MANIFEST_PATH = os.path.join(
    REPO_ROOT, "data", "story_glucose", "manifest.json")


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


def _extract_fn(source, name):
    # type: (str, str) -> str
    """Extract a named function's full text (header through balanced close
    brace) by brace counting -- precise enough to pin the BODY of the walk
    without depending on formatting."""
    marker = "function " + name
    i = source.find(marker)
    if i < 0:
        return ""
    j = source.find("{", i)
    if j < 0:
        return ""
    depth = 0
    k = j
    while k < len(source):
        ch = source[k]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[i:k + 1]
        k += 1
    return source[i:]


class TestTraceAssetStructure(unittest.TestCase):
    """Structural checks over the trace asset + ONE emitted page."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_trace_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.asset = _read(TRACE_ASSET) if os.path.isfile(TRACE_ASSET) else ""
        cls.manifest = {}
        if os.path.isfile(MANIFEST_PATH):
            with open(MANIFEST_PATH, "r", encoding="utf-8") as fh:
                cls.manifest = json.load(fh)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _trace_block(self):
        # type: () -> str
        """Extract the inlined 60_trace.js <script> block from the page."""
        marker = "/* asset: 60_trace.js"
        m_start = self.html.find(marker)
        self.assertGreaterEqual(
            m_start, 0, "60_trace.js asset marker missing from emitted HTML")
        block_open = self.html.rfind("<script>", 0, m_start)
        self.assertGreaterEqual(
            block_open, 0, "trace asset block has no opening <script>")
        block_close = self.html.find("</script>", m_start)
        self.assertGreaterEqual(
            block_close, 0, "trace asset block is unterminated")
        return self.html[block_open:block_close]

    # ------------------------------------------------------------------
    # 1. Registration (the 07.1-04 contract every later asset follows)
    # ------------------------------------------------------------------

    def test_registered(self):
        """EDITOR.view is called with 'trace' and a named render function;
        the DOM work is registered via EDITOR.init; the asset is a real
        implementation (the plan's artifact spec asks for >= 100 lines)."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        self.assertRegexpMatches(
            self.asset,
            r'EDITOR\.view\(\s*["\']trace["\']\s*,\s*renderTrace\s*\)',
            "the asset must register its renderer: "
            'EDITOR.view("trace", renderTrace)')
        self.assertIn(
            "function renderTrace", self.asset,
            "the named render function must exist in the asset")
        self.assertIn(
            "EDITOR.init(", self.asset,
            "the asset must register its DOM work via EDITOR.init")
        self.assertGreaterEqual(
            len(self.asset.splitlines()), 100,
            "the trace renderer must be a real implementation (the plan's "
            "artifact spec asks for >= 100 lines)")

    # ------------------------------------------------------------------
    # 2. Cycle guard (visited set + the arrow marker instead of recursion)
    # ------------------------------------------------------------------

    def test_cycle_guard(self):
        """The walk maintains a visited set and a revisit renders the
        marker leaf ('already shown') instead of recursing -- REQUIRED once
        editors can create arbitrary goto edges (RESEARCH-UI "Path tracing
        (D)"; no cycles exist in the current data)."""
        walk = _extract_fn(self.asset, "traceWalk")
        self.assertTrue(walk, "the traceWalk function must exist")
        self.assertIn(
            "visited", walk,
            "the walk must maintain a visited set (the cycle guard)")
        # The arrow marker: the literal arrow character or its JS escape,
        # with the 'already shown' wording -- rendered for a revisit.
        has_marker = ("\u21a9" in self.asset or
                      "\\u21A9" in self.asset or "\\u21a9" in self.asset)
        self.assertTrue(
            has_marker,
            "the cycle marker (the arrow character) must be present")
        self.assertIn(
            "already shown", self.asset,
            "a revisit must render an 'already shown' marker leaf")
        # The marker path must NOT recurse: the cycle branch returns a
        # leaf (children: []) BEFORE the recursive step() calls below it.
        self.assertRegexpMatches(
            walk,
            r"if\s*\(\s*visited\[id\]\s*\)[\s\S]*?children:\s*\[\]",
            "the revisit branch must return a leaf with no children "
            "(guard BEFORE recursion)")

    # ------------------------------------------------------------------
    # 3. Goto-only walk (the agreement-with-the-Python-gate pin)
    # ------------------------------------------------------------------

    def test_goto_only_walk(self):
        """The named traceWalk body reads choice.goto and contains NO
        weight/cond tokens anywhere -- structure comes from goto edges
        ONLY, mirroring check_reachability's BFS (rpg/story/validate.py:167,
        follow rule :198-200) so the traced node set always agrees with the
        Python gate. weight/cond appear ONLY in display code paths, which
        run after the walk."""
        walk = _extract_fn(self.asset, "traceWalk")
        self.assertTrue(walk, "the traceWalk function must exist")
        self.assertRegexpMatches(
            walk, r"\.goto\b",
            "the walk must follow choice.goto edges")
        self.assertIsNone(
            re.search(r"\bweight\b", walk),
            "the walk body must contain no 'weight' token (weights are "
            "runtime RNG picks, never structure)")
        self.assertIsNone(
            re.search(r"\bcond\b", walk),
            "the walk body must contain no 'cond' token (conds are runtime "
            "eligibility gates, never structure)")
        self.assertIn(
            "visited", walk,
            "the walk must bound depth with the visited set")
        # weight/cond DO exist somewhere -- as DISPLAY annotations, outside
        # the walk (the trace shows them per row).
        self.assertRegexpMatches(
            self.asset, r"\bweight\b",
            "weighted choices must be DISPLAYED (annotation, not structure)")
        self.assertRegexpMatches(
            self.asset, r"\bcond\b",
            "conditional choices must be DISPLAYED (annotation, not "
            "structure)")
        # The display layer is a separate function from the walk.
        self.assertIn(
            "function annotationSpans", self.asset,
            "choice annotations must live in a display-layer function "
            "separate from traceWalk")

    # ------------------------------------------------------------------
    # 4. Start default (manifest.start, not a hardcoded id)
    # ------------------------------------------------------------------

    def test_start_default(self):
        """The default trace root is manifest.start (intro.preface in the
        live data) -- read from the bundle at runtime, never hardcoded."""
        self.assertEqual(
            self.manifest.get("start"), "intro.preface",
            "precondition: the live manifest's start is intro.preface")
        default_fn = _extract_fn(self.asset, "defaultStartId")
        self.assertTrue(default_fn, "a defaultStartId helper must exist")
        self.assertIn(
            "manifest.start", default_fn,
            "the default root must come from manifest.start")
        self.assertRegexpMatches(
            self.asset, r"defaultStartId\(",
            "renderTrace must use the defaultStartId helper")
        # The trace-from-selection path consumes the graph's selection.
        self.assertIn(
            "EDITOR.state.sel", self.asset,
            "the 'trace from selected graph node' action must consume "
            "EDITOR.state.sel")

    # ------------------------------------------------------------------
    # 5. Copy-as-text helper (with a fallback path)
    # ------------------------------------------------------------------

    def test_copy_helper(self):
        """A copy-as-text function exists with a fallback-safe clipboard
        path: navigator.clipboard, then execCommand('copy'), then leave a
        textarea selected for a manual Ctrl+C (file:// pages may have
        clipboard writes restricted)."""
        self.assertIn(
            "function copyAsText", self.asset,
            "a named copyAsText function must exist")
        self.assertIn(
            "clipboard.writeText", self.asset,
            "the primary path should use navigator.clipboard.writeText")
        self.assertIn(
            "execCommand", self.asset,
            "the fallback path must use execCommand('copy')")
        self.assertIn(
            "function legacyCopy", self.asset,
            "the legacy (execCommand) fallback must be a real branch")
        self.assertIn(
            "textarea", self.asset,
            "the final fallback must expose a select-a-textarea manual copy")
        # The text format: indented lines, '- [tier] node id' with a
        # choice label after an em dash.
        self.assertIn(
            'buildCopyText', self.asset,
            "the copy text must be built from the trace model")
        self.assertRegexpMatches(
            self.asset, r'"- \[" \+ kind',
            "each plain-text line must start with '- [tier]'")

    # ------------------------------------------------------------------
    # 6. Nested-list markup (ul/li tree + details/summary branches)
    # ------------------------------------------------------------------

    def test_nested_list_markup(self):
        """The renderer builds a nested <ul>/<li> tree; branches with
        children are <details>/<summary> toggles keyed by data-branch;
        node rows carry a derived-kind chip and the incoming choice
        label."""
        self.assertIn('createElement("ul")', self.asset)
        self.assertIn('createElement("li")', self.asset)
        self.assertIn('createElement("details")', self.asset)
        self.assertIn('createElement("summary")', self.asset)
        self.assertIn('createElement("optgroup")', self.asset)
        self.assertIn("data-branch", self.asset,
                      "branch toggles must be keyed by data-branch")
        # Kind chips are DERIVED (never a stored field) + the incoming
        # choice label renders as 'label ->' on the child row.
        self.assertIn("EDITOR.deriveKind", self.asset,
                      "the row chip must use the shared derived-kind port")
        self.assertRegexpMatches(
            self.asset, r'" \\u2192 "',
            "the incoming choice label must render with an arrow before "
            "the child node id")
        # Expand state persists across rerenders (module map keyed by id).
        self.assertIn("expandedById", self.asset,
                      "expand/collapse state must persist across rerenders")

    # ------------------------------------------------------------------
    # 7. Controls row (start select, from-selection, copy, collapse/expand)
    # ------------------------------------------------------------------

    def test_controls(self):
        """The controls exist: the start-node select (#trace-start),
        trace-from-selection / copy / collapse / expand buttons, the tree
        mount (#trace-tree) and the feedback span (#trace-msg)."""
        for dom_id in ("trace-start", "trace-from-sel", "trace-copy",
                       "trace-collapse", "trace-expand", "trace-tree",
                       "trace-msg"):
            self.assertIn(
                '"%s"' % dom_id, self.asset,
                "the trace UI must contain the %s element" % dom_id)
        self.assertIn(
            "Trace from selected graph node", self.asset,
            "the from-selection button label must be present")
        self.assertIn(
            "Copy as text", self.asset,
            "the copy button label must be present")
        self.assertIn(
            "Collapse all", self.asset,
            "the collapse-all button label must be present")
        self.assertIn(
            "Expand all", self.asset,
            "the expand-all button label must be present")

    # ------------------------------------------------------------------
    # 8. Not-loaded placeholder
    # ------------------------------------------------------------------

    def test_placeholder(self):
        """Without a loaded bundle the tab shows a placeholder instead of
        an empty panel; the placeholder clears once data arrives (the
        render branches on EDITOR.state.bundle)."""
        self.assertRegexpMatches(
            self.asset,
            r"if\s*\(\s*!b\s*\|\|\s*!b\.files\s*\)",
            "renderTrace must branch on the loaded bundle")
        self.assertIn(
            "No story data loaded yet", self.asset,
            "the not-loaded placeholder text must be present")

    # ------------------------------------------------------------------
    # 9. ES5 discipline (the emitted-JS convention, per-asset pin)
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
    # 10. Emitted page: inlining + the plan's verify-step strings
    # ------------------------------------------------------------------

    def test_emitted_page_inlines_trace_asset(self):
        """The emitted story_editor.html inlines the trace asset with the
        registration, the visited-set guard, the manifest.start default and
        the copy helper -- in pipeline order (after 30_graph.js, before the
        shell bootstrap)."""
        block = self._trace_block()
        self.assertIn('EDITOR.view("trace", renderTrace)', block)
        self.assertIn("function traceWalk", block)
        self.assertIn("visited", block)
        self.assertIn("manifest.start", block)
        self.assertIn("execCommand", block)
        # Pipeline order: 00_core.js first (defines EDITOR), then
        # 05_json.js, then the graph asset, then the trace asset, then the
        # shell bootstrap (the LAST "EDITOR.runInits()" occurrence -- the
        # core asset CONTAINS the definition text early in the page, so a
        # plain find() would anchor on the wrong one).
        core_idx = self.html.find("/* asset: 00_core.js")
        json_idx = self.html.find("/* asset: 05_json.js")
        graph_idx = self.html.find("/* asset: 30_graph.js")
        trace_idx = self.html.find("/* asset: 60_trace.js")
        boot_idx = self.html.rfind("EDITOR.runInits();")
        for label, idx in (("core", core_idx), ("json", json_idx),
                           ("graph", graph_idx), ("trace", trace_idx),
                           ("bootstrap", boot_idx)):
            self.assertGreaterEqual(
                idx, 0, "the %s anchor is missing from the emitted page"
                % label)
        self.assertLess(core_idx, trace_idx,
                        "the core must inline before the trace asset")
        self.assertLess(graph_idx, trace_idx,
                        "the graph asset must inline before the trace")
        self.assertLess(trace_idx, boot_idx,
                        "the trace asset must inline before the bootstrap")


if __name__ == "__main__":
    unittest.main()
