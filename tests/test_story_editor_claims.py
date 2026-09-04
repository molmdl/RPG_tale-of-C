"""Structural claims-browser test battery for the Phase 7.1 editor claims
asset (07.1-12 Task 2).

Covers (over tools/story_editor_assets/70_claims.js and the emitted page):
- the claims view is REGISTERED per the 07.1-04 convention:
  EDITOR.view('claims', ...) + EDITOR.init(...) present in the asset and
  inlined into the emitted story_editor.html (test_claims_registered,
  test_emitted_page_inlines_claims_asset)
- the READ-ONLY CONTRACT is pinned: the asset contains NO mutator call of
  any kind (no EDITOR.apply, no node/choice mutators, no bundle writes) --
  Requirement C is read-and-jump, never edit; approvals are human-gated by
  policy (spec.md non-negotiable) (test_read_only)
- source_id is handled BOTH as a string AND as a list-of-strings (40/77
  registry claims are multi-source; both branches are load-bearing against
  the real data) (test_multi_source)
- the reverse index (claim -> referencing nodes) walks the nodes'
  claim_ids lists and unapproved/unresolved references surface as warning
  chips (test_reverse_index)
- the approval predicate is STRICT: approval_status compared to "approved"
  exactly, with no "not pending" shortcut (rejected must fail identically
  to pending; rpg/citations.py:100-109) (test_status_chips_strict)
- jump-to-node wiring: node chips call EDITOR.select (test_jump_to_node)
- the EDITOR.ui.claimFocus hook consumed from the node form (40_form.js,
  07.1-09) is DEFINED here: it opens the claim and switches to the claims
  tab (test_claim_focus_hook)
- ES5 discipline for the asset: no arrow functions, no let/const, no
  modules (test_es5_discipline)

Pure WSL python3.6 -- stdlib only; the generator is subprocessed once per
test class via setUpClass into a temp dir using --output (same conventions
as tests/test_story_editor_graph.py: REPO_ROOT via __file__,
subprocess.run with PIPE streams -- NOT capture_output, which is 3.7+).
The battery greps only THIS plan's asset, so it stays robust while the
parallel Wave-4 agents (40_form.js / 60_trace.js / 80_save.js) are in
flight. The committed story_editor.html regeneration is DEFERRED while a
sibling asset is untracked (wave race rule) -- the emitted-page class
therefore generates its own copy via --output and never reads the repo-root
artifact.
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
CLAIMS_ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "70_claims.js")
CITATIONS_PATH = os.path.join(REPO_ROOT, "data", "citations.json")

# The state layer's mutation API -- NONE of these may appear anywhere in
# the claims asset (the read-only contract; even a mention in a comment is
# avoided so the grep stays trivially zero).
FORBIDDEN_MUTATORS = [
    "EDITOR.apply",
    "nodeSet", "nodeAdd", "nodeDelete",
    "choiceAdd", "choiceUpdate", "choiceDelete",
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


class TestClaimsAssetStructure(unittest.TestCase):
    """Structural checks over the claims asset + ONE emitted page."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_claims_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.asset = _read(CLAIMS_ASSET) if os.path.isfile(CLAIMS_ASSET) else ""
        cls.citations = {}
        if os.path.isfile(CITATIONS_PATH):
            with open(CITATIONS_PATH, "r", encoding="utf-8") as fh:
                cls.citations = json.load(fh)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _claims_block(self):
        # type: () -> str
        """Extract the inlined 70_claims.js <script> block from the page."""
        marker = "/* asset: 70_claims.js"
        m_start = self.html.find(marker)
        self.assertGreaterEqual(
            m_start, 0, "70_claims.js asset marker missing from emitted HTML")
        block_open = self.html.rfind("<script>", 0, m_start)
        self.assertGreaterEqual(
            block_open, 0, "claims asset block has no opening <script>")
        block_close = self.html.find("</script>", m_start)
        self.assertGreaterEqual(
            block_close, 0, "claims asset block is unterminated")
        return self.html[block_open:block_close]

    # ------------------------------------------------------------------
    # 1. Registration (the 07.1-04 contract every later asset follows)
    # ------------------------------------------------------------------

    def test_claims_registered(self):
        """EDITOR.view is called with 'claims' (single-quoted -- the plan's
        pinned verify string) and a named render function; the DOM work is
        registered via EDITOR.init; the asset is a real IIFE, not a stub."""
        self.assertIn("EDITOR.view('claims'", self.asset,
                      "the claims view must be registered as "
                      "EDITOR.view('claims', ...)")
        self.assertIn("EDITOR.init(initClaims)", self.asset,
                      "claims DOM work must register via EDITOR.init")
        self.assertIn("(function () {", self.asset,
                      "asset must be a single IIFE (classic-script style)")
        self.assertIn('"use strict";', self.asset,
                      "asset must use strict mode like the sibling assets")
        self.assertGreaterEqual(
            len(self.asset.splitlines()), 120,
            "the plan's must-have requires >= 120 lines of real asset")

    # ------------------------------------------------------------------
    # 2. READ-ONLY contract (Requirement C is read-and-jump, never edit)
    # ------------------------------------------------------------------

    def test_read_only(self):
        """The asset contains NO mutator call: no EDITOR.apply, no node/choice
        mutators, no bundle-field writes. Approvals are human-gated by policy
        (spec.md non-negotiable); the claims panel never writes."""
        for token in FORBIDDEN_MUTATORS:
            self.assertNotIn(
                token, self.asset,
                "read-only contract violated: %r found in 70_claims.js" % token)
        # The read-only contract is DOCUMENTED (the header states approvals
        # are human-gated per spec.md).
        self.assertIn("READ-ONLY CONTRACT", self.asset)
        self.assertIn("spec.md", self.asset)
        self.assertIn("HUMAN-GATED", self.asset)
        # No direct bundle mutation either: the asset must never ASSIGN into
        # the bundle object graph (only reads). Allowlist the assignment
        # forms that ARE legitimate (module state / DOM / EDITOR.ui).
        self.assertNotIn("state.bundle.citations", self.asset)
        self.assertNotIn("state.bundle.sources", self.asset)
        self.assertNotIn("bundle.citations =", self.asset)
        self.assertNotIn("bundle.sources =", self.asset)

    # ------------------------------------------------------------------
    # 3. source_id as string AND array (40/77 claims are multi-source)
    # ------------------------------------------------------------------

    def test_multi_source(self):
        """source_id resolution handles BOTH forms: the array branch and the
        string branch. The real registry exercises both (40 of 77 claims
        carry a list source_id), so each branch is load-bearing."""
        # Both branches present in the asset...
        self.assertIn('"[object Array]"', self.asset,
                      "the LIST branch (source_id as array) is missing")
        self.assertIn("typeof sid === \"string\"", self.asset,
                      "the STRING branch (source_id as scalar) is missing")
        # ...and the normalization actually feeds the source resolution.
        self.assertIn("function sourceIds(", self.asset)
        self.assertIn("sourceIds(rec).length", self.asset)
        # The emitted page carries the same handling.
        block = self._claims_block()
        self.assertIn('"[object Array]"', block)
        self.assertIn("typeof sid === \"string\"", block)
        # Data reality: BOTH forms exist in the live registry, so neither
        # branch is dead code.
        list_form = 0
        str_form = 0
        for rec in self.citations.values():
            sid = rec.get("source_id")
            if isinstance(sid, list):
                list_form += 1
            elif isinstance(sid, str):
                str_form += 1
        self.assertGreater(
            list_form, 0,
            "data reality drifted: no multi-source claims remain, the LIST "
            "branch is now dead code")
        self.assertGreater(
            str_form, 0,
            "data reality drifted: no single-source claims remain, the "
            "STRING branch is now dead code")

    # ------------------------------------------------------------------
    # 4. Reverse index + per-node warning chips
    # ------------------------------------------------------------------

    def test_reverse_index(self):
        """The reverse index walks every node's claim_ids (claim -> [node
        ids]); unapproved/unresolved references surface as warning chips
        (display mirror of the lint's claim rules)."""
        # The claim_ids walk is present (twice: index build + warning walk).
        self.assertGreaterEqual(self.asset.count("claim_ids"), 3,
                                "the claim_ids walk is missing/thin")
        self.assertIn("function buildReverseIndex(", self.asset)
        self.assertIn("byClaim[cid].push(wrap.id)", self.asset,
                      "the claim -> [node ids] accumulation is missing")
        # Warning chips for unapproved / unresolved references, with the
        # lint's rule ids mirrored for display.
        for rule in ("claim_missing", "claim_unapproved",
                     "placeholder_misuse"):
            self.assertIn(rule, self.asset,
                          "lint rule id %r missing from the display mirror"
                          % rule)
        self.assertIn("claims-node-chip-warn", self.asset,
                      "the amber warning-chip class is missing")
        # Clicking a warning chip opens the claim (data-open-claim wiring).
        self.assertIn("data-open-claim", self.asset)
        # The emitted page carries the walk.
        block = self._claims_block()
        self.assertIn("claim_ids", block)
        self.assertIn("buildReverseIndex", block)

    # ------------------------------------------------------------------
    # 5. Strict approval semantics (the gate's core predicate)
    # ------------------------------------------------------------------

    def test_status_chips_strict(self):
        """approval_status is compared to "approved" EXACTLY; the erroneous
        "not pending" shortcut (which would wrongly pass rejected claims,
        rpg/citations.py:100-109 Pitfall 6) appears NOWHERE."""
        self.assertIn('rec.approval_status === "approved"', self.asset,
                      "the strict approval predicate is missing")
        self.assertIn("rpg/citations.py:100-109", self.asset,
                      "the strict-semantics source citation is missing")
        # The forbidden shortcut: an INEQUALITY against "pending" used as
        # the approval predicate (== "pending" equality for display counting
        # is fine -- only != / !== would wrongly pass rejected claims).
        self.assertIsNone(
            re.search(r"!==?\s*[\"']pending[\"']", self.asset),
            "found a pending-inequality shortcut -- rejected claims must "
            "fail identically to pending (strict 'approved' only)")
        self.assertIsNone(
            re.search(r"[\"']pending[\"']\s*!==?", self.asset),
            "found a pending-inequality shortcut (reversed form)")
        # The status chip builder derives from approval_status.
        self.assertIn("claims-status-approved", self.asset)
        self.assertIn("claims-status-pending", self.asset)
        self.assertIn("claims-status-rejected", self.asset)

    # ------------------------------------------------------------------
    # 6. Jump-to-node wiring
    # ------------------------------------------------------------------

    def test_jump_to_node(self):
        """Each referencing node id jumps: EDITOR.select(nodeId) + switching
        to the graph tab."""
        self.assertIn("EDITOR.select(", self.asset,
                      "jump-to-node must call EDITOR.select")
        self.assertIn('EDITOR.showTab("graph")', self.asset,
                      "jump-to-node must switch to the graph tab")
        self.assertIn("data-jump-node", self.asset,
                      "node chips must carry the jump attribute")
        # The jump handler is actually wired (delegated listener).
        self.assertIn('"data-jump-node", function', self.asset)

    # ------------------------------------------------------------------
    # 7. The EDITOR.ui.claimFocus hook consumed from the form (07.1-09)
    # ------------------------------------------------------------------

    def test_claim_focus_hook(self):
        """EDITOR.ui.claimFocus(claimId) -- the hook 40_form.js (07.1-09)
        calls when a node-form claim chip is clicked -- is DEFINED by this
        asset: it opens the claim AND switches to the claims tab."""
        self.assertIn("EDITOR.ui = EDITOR.ui || {}", self.asset,
                      "the EDITOR.ui namespace must be created defensively")
        self.assertIn("EDITOR.ui.claimFocus = function", self.asset,
                      "the claimFocus hook must be defined here")
        # The definition opens the claim and switches tabs.
        m = self.asset.find("EDITOR.ui.claimFocus = function")
        self.assertGreaterEqual(m, 0)
        tail = self.asset[m:m + 400]
        self.assertIn("openClaim(", tail,
                      "claimFocus must open the claim (render the detail)")
        self.assertIn('EDITOR.showTab("claims")', tail,
                      "claimFocus must switch to the claims tab")
        # And the hook is documented as the form's consumer.
        self.assertIn("40_form.js", self.asset)
        self.assertIn("07.1-09", self.asset)

    # ------------------------------------------------------------------
    # 8. Degradation paths (citations/sources may not load)
    # ------------------------------------------------------------------

    def test_degrade_paths(self):
        """No bundle / citations.json missing / sources.json missing each
        render a warning panel pointing at the boot checklist -- never a
        silent blank panel."""
        self.assertIn("citations.json did not load", self.asset)
        self.assertIn("sources.json did not load", self.asset)
        self.assertIn("No data loaded", self.asset)
        self.assertIn("boot panel", self.asset,
                      "degrade panels must point at the boot checklist")
        # The registered view guards both degrade cases before rendering.
        self.assertIn("if (!cits) {", self.asset)

    # ------------------------------------------------------------------
    # 9. ES5 discipline (per-asset pin; page-wide pin lives in the state
    #    battery)
    # ------------------------------------------------------------------

    def test_es5_discipline(self):
        """No arrow functions, no let/const declarations, no modules, no
        template literals -- var-style ES5 only."""
        self.assertIsNone(
            re.search(r"=>", self.asset),
            "arrow function found; ES5 var-style is the pinned convention")
        self.assertIsNone(
            re.search(r"\blet\s", self.asset),
            "let declaration found")
        self.assertIsNone(
            re.search(r"\bconst\s", self.asset),
            "const declaration found")
        self.assertNotIn("`", self.asset,
                         "template literal found (ES6)")
        self.assertNotIn('type="module"', self.asset)


class TestClaimsEmittedPage(unittest.TestCase):
    """The plan's Task-1 verify, pinned mechanically: the emitted page
    contains the claims asset with the registry-browser strings."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_claims_page_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_emitted_page_inlines_claims_asset(self):
        """The emitted HTML contains the claims asset block with every
        string the plan's verify step names, ordered after the graph asset
        and before the shell bootstrap."""
        html = self.html
        self.assertTrue(html, "generator produced no output file")
        marker = "/* asset: 70_claims.js"
        m70 = html.find(marker)
        self.assertGreaterEqual(m70, 0,
                                "70_claims.js not inlined into the page")
        # Plan verify strings (the single-quoted registration is pinned).
        for needle in ("EDITOR.view('claims'", "claim_text", "review_tier",
                       "source_id", "pdb_doi", "license", "claim_ids"):
            m = html.find(needle, m70)
            self.assertGreaterEqual(
                m, 0,
                "verify string %r missing from the emitted page after the "
                "claims asset marker" % needle)
        # Ordering: after 30_graph.js (asset order contract), before the
        # shell bootstrap (the bootstrap is the last script block).
        m30 = html.find("/* asset: 30_graph.js")
        self.assertGreater(m30, 0, "30_graph.js marker missing")
        self.assertGreater(m70, m30,
                           "70_claims.js must inline after 30_graph.js")
        boot = html.rfind("DOMContentLoaded")
        self.assertLess(m70, boot,
                        "the claims asset must precede the shell bootstrap")

    def test_emitted_claims_block_read_only(self):
        """The read-only contract holds in the EMITTED block too."""
        marker = "/* asset: 70_claims.js"
        m_start = self.html.find(marker)
        block_open = self.html.rfind("<script>", 0, m_start)
        block_close = self.html.find("</script>", m_start)
        block = self.html[block_open:block_close]
        for token in FORBIDDEN_MUTATORS:
            self.assertNotIn(token, block,
                             "emitted claims block contains mutator %r"
                             % token)


if __name__ == "__main__":
    unittest.main()
