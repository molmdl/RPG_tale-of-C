"""Structural on_enter-editor test battery for the Phase 7.1 editor asset
(07.1-16 Task 2).

Covers (over tools/story_editor_assets/43_onenter.js and the emitted page):
- the B8 paste contract: parseScenePaste implements the frozen
  scene_capture.py:416-434 render_capture format exactly -- split lines,
  drop empty/`//`/`#` lines (the `# NOT CAPTURED` notes counted), take
  first `[` .. last `]`, JSON.parse, then PER-ENTRY validation: object
  with a string `op` required (test_paste_contract)
- warn-but-accept extensibility (B11): the unknown-op path KEEPS the
  entry -- a warnings.push, never a throw/splice/reject
  (test_warn_but_accept)
- set_view is accepted WITH the visible Phase-10 flag (scene_capture
  stdout-WARNING parity; the dispatch lands in Phase 10)
  (test_set_view_flag)
- the op vocabulary: the KNOWN list carries the 10 story-data ops
  (RESEARCH-DATA section 1.4) + the molops extras select_focus / zoom /
  delete / protonate / restore + set_view (test_op_vocabulary)
- the pinned-sequence guards: start-node pdb-load warning
  (tests/test_glucose_reachability.py:781-798), the hero-highlight 6-op
  ordered subsequence warning (:800-843), the restored
  [edit, load, align, show_as] reveal warning (:391-414), and the
  zero-restore-ops warning (07-17 invariant) -- all as CONFIRMS, never
  blocks (test_pinned_guards)
- reorder/attach are never silent: confirm dialogs sit in the move /
  delete / attach paths (test_no_reorder_silent)
- the no-invention rule: load/hide_all are replay-side ops scene_capture
  NEVER emits -- accepted if hand-written, semantics noted in the preview
  (test_no_invention_rule)
- ES5 discipline for the asset (test_es5_discipline) + the emitted page
  inlines the asset with the plan's verify-step strings in pipeline order
  (test_emitted_page_inlines_onenter_asset)

Greps target ONLY this plan's asset block, so the battery stays robust
while parallel Wave-4/5 agents are in flight (07.1-09/12/13 precedent).
Runtime behavior is machine-proven separately by the 66/66 headless-Chrome
smoke (tmp/opencode-0716 harness, gitignored) -- this battery pins the
STRUCTURE.

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
ONENTER_ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "43_onenter.js")

# The Phase-10 flag text (plan Task-1 wording, verbatim).
PHASE10_FLAG = ("Phase-10 flag: camera rides home until the set_view "
                "dispatch lands")

# The op vocabulary the plan pins (10 story ops + molops extras + set_view).
EXPECTED_OPS = [
    "hide_all", "load", "show_as", "edit", "align", "set_color", "color",
    "show", "set", "label",
    "select_focus", "zoom", "delete", "protonate", "restore", "set_view"
]

# Per-op arg field names from RESEARCH-DATA section 1.4 (verified shapes).
EXPECTED_ARG_KEYS = [
    "object", "rep", "sele", "edit_type", "new_resn", "reference",
    "method", "align_sele", "rgb", "color", "name", "value", "text",
    "view", "variant_id"
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


def _function_body(src, name):
    # type: (str, str) -> str
    """Extract a `function <name>(...) { ... }` body by brace matching
    (good enough for this asset's flat top-level functions)."""
    m = re.search(r"function\s+%s\s*\([^)]*\)\s*\{" % re.escape(name), src)
    if not m:
        return ""
    depth = 0
    i = m.end() - 1
    while i < len(src):
        ch = src[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[m.start():i + 1]
        i += 1
    return src[m.start():]


class TestOnenterAssetStructure(unittest.TestCase):
    """Structural checks over the on_enter asset + ONE emitted page."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_onenter_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.asset = _read(ONENTER_ASSET) if os.path.isfile(ONENTER_ASSET) else ""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _onenter_block(self):
        # type: () -> str
        """Extract the inlined 43_onenter.js <script> block from the page."""
        marker = "/* asset: 43_onenter.js"
        m_start = self.html.find(marker)
        self.assertGreaterEqual(
            m_start, 0,
            "43_onenter.js asset marker missing from emitted HTML")
        block_open = self.html.rfind("<script>", 0, m_start)
        self.assertGreaterEqual(
            block_open, 0, "on_enter asset block has no opening <script>")
        block_close = self.html.find("</script>", m_start)
        self.assertGreaterEqual(
            block_close, 0, "on_enter asset block is unterminated")
        return self.html[block_open:block_close]

    # ------------------------------------------------------------------
    # 1. The paste contract (scene_capture.py:416-434 render_capture format)
    # ------------------------------------------------------------------

    def test_paste_contract(self):
        """parseScenePaste implements the frozen jsonc chain: split lines,
        strip empty/`//`/`#` lines, first `[` .. last `]`, JSON.parse --
        each stage present, IN ORDER; per-entry op-string validation with
        the missing-op throw; the `# NOT CAPTURED` handling present."""
        body = _function_body(self.asset, "parseScenePaste")
        self.assertTrue(
            body, "parseScenePaste function not found in the asset")
        # The strip/parse chain, in order (grep the sequence per the plan).
        chain = [
            (r"split\(/\\r\?\\n/\)", "line split"),
            (r'indexOf\("//"\) === 0', "the `//` header strip"),
            (r'indexOf\("#"\) === 0', "the `# NOT CAPTURED` strip"),
            (r'indexOf\("\["\)', "first `[`"),
            (r'lastIndexOf\("\]"\)', "last `]`"),
            (r"JSON\.parse\(body\.slice\(a, b \+ 1\)\)", "JSON.parse slice"),
        ]
        last = -1
        for pattern, what in chain:
            m = re.search(pattern, body)
            self.assertTrue(
                m, "parseScenePaste missing the %s stage (%r)" % (what, pattern))
            self.assertGreater(
                m.start(), last,
                "parseScenePaste chain out of order at stage: %s" % what)
            last = m.start()
        # Per-entry validation: object with a string op required.
        self.assertIn('typeof op.op !== "string"', body,
                      "per-entry validation must require a string op")
        self.assertIn('"entry " + j + ": missing op"', body,
                      "the missing-op entry error must be thrown")
        # The `# NOT CAPTURED` handling: the notes are counted, not silently
        # dropped (scene_capture's unmappable-fact annotations).
        self.assertIn("NOT CAPTURED", body,
                      "the # NOT CAPTURED handling comment/counter missing")
        self.assertIn("noteLines", body,
                      "the NOT-CAPTURED note lines must be counted for the "
                      "preview")

    # ------------------------------------------------------------------
    # 2. Warn-but-accept (B11 extensibility)
    # ------------------------------------------------------------------

    def test_warn_but_accept(self):
        """The unknown-op path KEEPS the entry: it is a warnings.push of
        "unknown op 'X' (kept)" -- never a throw, splice or reject. The
        ONLY throw in the per-entry loop is the missing-op contract
        check."""
        body = _function_body(self.asset, "parseScenePaste")
        self.assertTrue(body, "parseScenePaste not found")
        self.assertIn(
            'unknown op \'" + op.op + "\' (kept)', body,
            "the warn-but-accept message \"unknown op 'X' (kept)\" missing")
        # The unknown-op line is a push, never a throw (comment prose
        # exempt -- the sibling batteries' scoped-review convention).
        for line in body.splitlines():
            if "unknown op" not in line:
                continue
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            self.assertIn("push", line,
                          "the unknown-op path must KEEP the entry "
                          "(warnings.push)")
            self.assertNotIn("throw", line,
                             "the unknown-op path must never throw")
        # No splice/reject anywhere in the per-entry validation loop.
        self.assertNotIn("splice", body,
                         "parseScenePaste must never drop entries (B11: "
                         "warn-but-accept, never reject)")
        # The missing-op throw stays scoped to the contract check.
        throw_lines = [ln for ln in body.splitlines() if "throw" in ln]
        self.assertEqual(
            len(throw_lines), 3,
            "expected exactly 3 throws (no-array, non-array, missing op); "
            "got %r" % throw_lines)
        for ln in throw_lines:
            self.assertTrue(
                "no JSON array found in paste" in ln or
                "did not parse into a JSON array" in ln or
                "missing op" in ln,
                "unexpected throw in parseScenePaste: %r" % ln.strip())

    # ------------------------------------------------------------------
    # 3. set_view accepted WITH the Phase-10 flag
    # ------------------------------------------------------------------

    def test_set_view_flag(self):
        """set_view entries are accepted and flagged: the plan's Phase-10
        badge text is present (parse warning + the op-row badge) and
        scene_capture stdout-warning parity is cited."""
        self.assertIn("set_view", self.asset)
        self.assertIn(
            PHASE10_FLAG, self.asset,
            "the Phase-10 flag text must be present verbatim")
        # Parse-side warning parity + render-side badge.
        body = _function_body(self.asset, "parseScenePaste")
        self.assertIn('op.op === "set_view"', body,
                      "the parse warning must special-case set_view")
        self.assertRegexpMatches(
            self.asset, r'function phase10Badge\(',
            "the visible Phase-10 badge renderer must exist")
        # scene_capture parity citation (stdout WARNING, molops FROZEN).
        self.assertIn("Phase 10", self.asset)
        self.assertIn("scene_capture", self.asset)

    # ------------------------------------------------------------------
    # 4. The op vocabulary
    # ------------------------------------------------------------------

    def test_op_vocabulary(self):
        """The KNOWN list contains the 10 story ops (RESEARCH-DATA section
        1.4) + select_focus/zoom/delete/protonate/restore/set_view; every
        per-op arg field from the section 1.4 table is present (incl.
        new_resn, align_sele, and sphere_scale via set{name:...})."""
        # The vocabulary literal: op names as plain double-quoted strings.
        for op in EXPECTED_OPS:
            self.assertIn(
                '{ op: "%s"' % op, self.asset,
                "OP_VOCAB must carry the op %r as a literal entry" % op)
        # The parser validates against the SAME vocabulary (OP_NAMES).
        body = _function_body(self.asset, "parseScenePaste")
        self.assertIn("OP_NAMES.indexOf(op.op) < 0", body,
                      "the paste validation must check the shared vocabulary")
        # Per-op arg field names (section 1.4 shapes).
        for key in EXPECTED_ARG_KEYS:
            self.assertIn('key: "%s"' % key, self.asset,
                          "the arg field %r missing from the per-op forms"
                          % key)
        # sphere_scale enters via the set op's name placeholder (the plan's
        # verify names it "sphere_scale via set{name:...}").
        self.assertIn("sphere_scale", self.asset,
                      "the set{name:...} sphere_scale example must be "
                      "visible in the form")
        # Target-less ops hide the target field (data fact: hide_all /
        # set_color carry NO target key).
        for no_target in ("hide_all", "set_color", "set_view"):
            m = re.search(
                r'\{ op: "%s", target: false' % no_target, self.asset)
            self.assertTrue(
                m, "op %r must declare target: false (the data omits the "
                "target key)" % no_target)

    # ------------------------------------------------------------------
    # 5. The pinned-sequence guards
    # ------------------------------------------------------------------

    def test_pinned_guards(self):
        """All four pinned guards exist as CONFIRMS (never blocks), each
        citing its owning test:
        - start-shape pdb-load (test_glucose_reachability.py:781-798)
        - hero-highlight 6-op ordered subsequence (:800-843)
        - restoration reveal [edit, load, align, show_as] (:391-414)
        - zero-restore-ops on non-restored nodes (07-17 invariant)."""
        # (a) start-shape: the 3 start ids + the pdb: guard + citation.
        for nid in ("intro.preface", "intro.shell_glucose", "intro.select"):
            self.assertIn('"%s"' % nid, self.asset,
                          "START_NODE_IDS must carry %s" % nid)
        self.assertIn("start-shape", self.asset,
                      "the start-node pdb-load guard message missing")
        self.assertIn("781-798", self.asset,
                      "the start-shape guard must cite its owning test lines")
        # (b) hero-highlight: the ordered-subsequence walk + citation.
        self.assertIn("function heroHighlightIndices(", self.asset,
                      "the hero-highlight subsequence walk missing")
        self.assertIn("hero-highlight", self.asset,
                      "the hero-highlight guard message missing")
        self.assertIn("800-843", self.asset,
                      "the hero-highlight guard must cite its owning test")
        # (c) restoration reveal: the 2 restored ids + the pinned order.
        for nid in ("gly.pfk_restored", "tca.aconitase_restored"):
            self.assertIn('"%s"' % nid, self.asset,
                          "RESTORED_IDS must carry %s" % nid)
        self.assertIn("restoration reveal", self.asset,
                      "the restoration-reveal guard message missing")
        self.assertIn("[edit, load, align, show_as]", self.asset,
                      "the pinned reveal order must be named")
        self.assertIn("391-414", self.asset,
                      "the restoration guard must cite its owning test")
        # (d) zero-restore-ops on NON-restored nodes (07-17).
        self.assertIn("zero-restore-ops", self.asset,
                      "the zero-restore-ops guard message missing")
        guards_body = _function_body(self.asset, "pinnedGuardMessages")
        for op_name in ("edit", "restore", "protonate"):
            self.assertIn(
                '"%s"' % op_name, guards_body,
                "the zero-restore guard must police %r" % op_name)
        # All warns are CONFIRMS, not blocks -- the validator carries the
        # authoritative errors.
        self.assertIn("confirms, not blocks", self.asset,
                      "the warns-are-confirms posture must be stated")
        agw_body = _function_body(self.asset, "applyWithGuards")
        self.assertIn("window.confirm(", agw_body,
                      "guards must route through window.confirm")
        self.assertIn("if (!ok) return;", agw_body,
                      "a declined confirm must ABORT (confirm, not block, "
                      "but never apply without consent)")

    # ------------------------------------------------------------------
    # 6. Reorder/attach are never silent
    # ------------------------------------------------------------------

    def test_no_reorder_silent(self):
        """Confirm dialogs sit in the move, delete AND attach paths: a
        reorder/deletion/attach always asks first (order is load-bearing;
        the pinned nodes additionally get the guard confirms)."""
        move_body = _function_body(self.asset, "moveOp")
        self.assertIn("window.confirm(", move_body,
                      "move must confirm (reorder is a structural change)")
        self.assertIn("Order is load-bearing", move_body,
                      "the move confirm must say why order matters")
        delete_body = _function_body(self.asset, "deleteOp")
        self.assertIn("window.confirm(", delete_body,
                      "delete must confirm (destructive)")
        attach_body = _function_body(self.asset, "confirmAttach")
        self.assertIn("window.confirm(", attach_body,
                      "attach must confirm (the preview-then-confirm flow)")
        self.assertIn("Attach ", attach_body,
                      "the attach confirm must state the op count")
        # Append-only: attach CONCATS after the existing ops -- it never
        # reorders them (pinned nodes keep their sequence positions).
        self.assertIn("concat(ops)", attach_body,
                      "attach must append via concat (never reorder)")

    # ------------------------------------------------------------------
    # 7. The no-invention rule (load/hide_all replay-side)
    # ------------------------------------------------------------------

    def test_no_invention_rule(self):
        """load/hide_all are replay-side ops scene_capture NEVER emits --
        the parser accepts them if hand-written but the preview notes
        their replay-side semantics (nothing invented, nothing dropped)."""
        self.assertIn("replay-side", self.asset,
                      "the replay-side semantics note missing")
        self.assertIn("NEVER emits", self.asset,
                      "the scene_capture never-emits fact must be stated")
        body = _function_body(self.asset, "parseScenePaste")
        self.assertIn('op.op === "load" || op.op === "hide_all"', body,
                      "the parser must note hand-written load/hide_all")
        # The preview renders the replay-side badge for those ops.
        preview_body = _function_body(self.asset, "previewHtml")
        self.assertIn("replay-side op", preview_body,
                      "the preview must badge replay-side ops")

    # ------------------------------------------------------------------
    # 8. ES5 discipline
    # ------------------------------------------------------------------

    def test_es5_discipline(self):
        """The asset is ES5-classic: no arrow functions, no let/const, no
        module markers, no ES6 String.prototype.startsWith (modules fail
        under file:// CORS; var-style keeps the emitted JS reviewable)."""
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
        self.assertNotIn(".startsWith(", self.asset,
                         "startsWith is ES6 -- use indexOf(...) === 0")
        # The B11 mutation discipline is documented in-source: op dicts are
        # COPIED before every write so unknown keys round-trip and the undo
        # pre-image stays honest.
        self.assertIn("round-trip", self.asset,
                      "the B11 unknown-key round-trip contract must be "
                      "documented")
        self.assertIn("applyOpMutation", self.asset,
                      "op mutations must flow through the copy-then-write "
                      "helper")

    # ------------------------------------------------------------------
    # 9. Emitted page inlines the asset (plan verify strings, pipeline order)
    # ------------------------------------------------------------------

    def test_emitted_page_inlines_onenter_asset(self):
        """The emitted story_editor.html inlines the on_enter asset with the
        plan's verify-step strings, in pipeline order (after 40_form.js,
        before 60_trace.js, before the shell bootstrap)."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        block = self._onenter_block()
        # The plan's Task-1 verify strings, all present in the emitted page.
        for required in ("parseScenePaste", "NOT CAPTURED", PHASE10_FLAG,
                         "new_resn", "align_sele", "sphere_scale",
                         "start-shape", "restoration reveal",
                         "zero-restore-ops", "heroHighlightIndices",
                         "OP_VOCAB", "replay-side"):
            self.assertIn(required, block,
                          "emitted on_enter block must contain %r" % required)
        # The shell mount is consumed (the asset owns #node-form-onenter).
        self.assertIn('getElementById("node-form-onenter")', block)
        # Pipeline order: 40_form.js -> 43_onenter.js -> 60_trace.js ->
        # shell bootstrap (42_choices.js may sit between 40 and 43 --
        # sibling-owned, not asserted here).
        form_idx = self.html.find("/* asset: 40_form.js")
        onenter_idx = self.html.find("/* asset: 43_onenter.js")
        trace_idx = self.html.find("/* asset: 60_trace.js")
        boot_idx = self.html.rfind("EDITOR.runInits();")
        self.assertGreaterEqual(form_idx, 0)
        self.assertGreaterEqual(onenter_idx, 0)
        self.assertGreaterEqual(trace_idx, 0)
        self.assertGreaterEqual(boot_idx, 0)
        self.assertLess(form_idx, onenter_idx,
                        "the form asset must inline before the on_enter "
                        "editor")
        self.assertLess(onenter_idx, trace_idx,
                        "the on_enter editor must inline before the trace "
                        "tab")
        self.assertLess(onenter_idx, boot_idx,
                        "the on_enter editor must inline before the "
                        "bootstrap")
        # The EDITOR.onenter extension exposes the paste contract for the
        # diagnostics tab (07.1-19).
        self.assertIn("EDITOR.onenter.parseScenePaste", block)


if __name__ == "__main__":
    unittest.main()
