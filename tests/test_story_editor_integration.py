#!/usr/bin/env python3.6
"""Capstone cross-asset integration battery for the Phase 7.1 HTML story
editor (07.1-19 Task 1, Part A).

One setUpClass run of the generator (temp path, --output) yields the FULL
emitted editor page; every test below either scopes to that emitted artifact
or subprocesses the live repo gates:

- test_asset_order_complete: ALL 14 assets inlined, in sorted order, each
  block carrying its owning capability signature (the whole page, end to end)
- test_committed_artifact_fresh: regenerating reproduces the committed
  repo-root story_editor.html modulo the generated-at timestamp
- test_capability_matrix: every B1-B11/C/D/E capability entry point present
  in the emitted HTML -- one assertion row per requirement id in the table
  comment for traceability
- test_offline_clean: no external src/href, no ES modules, no top-level
  import statements, and at most one documented fetch site (the 10_load.js
  probe; currently ZERO -- the fetch transport was removed in 10_load.js
  v0.2.0 per the corrected 07.1-11 policy record)
- test_no_token_leaks: zero unresolved __TOKEN__ regions in the emitted page
- test_serializer_vectors_embedded: the emitted 05_json block embeds every
  tools/story_editor_json.py fixture_vectors() (name, expected) pair VERBATIM
  (decoded via the same shared JS-string-constant decoder as
  test_story_editor_serializer_js.py)
- test_validator_rule_parity: all 21 error rule ids + the 3 lint notice ids
  + the 2 plan-mandated JS-only notices are present in the emitted 20_validate
  block (the kind harvest from tools/story_editor_lint.py is a subset guard)
- test_lint_green_and_generator_green: the suite-level gate pairing --
  subprocess python3.6 tools/story_editor_lint.py -> exit 0 on the live repo;
  subprocess generator re-run -> exit 0

Pure WSL python3.6 -- stdlib only; generator subprocessed with PIPE streams
(same conventions as tests/test_story_editor_boot.py /
test_story_editor_generator.py -- NOT capture_output, which is 3.7+).
The committed-HTML-freshness check reads the repo-root story_editor.html
(the 07.1-01 placement pin: committed, never dist/).
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
LINT = os.path.join(REPO_ROOT, "tools", "story_editor_lint.py")
ASSETS_DIR = os.path.join(REPO_ROOT, "tools", "story_editor_assets")
COMMITTED_HTML = os.path.join(REPO_ROOT, "story_editor.html")

# Sibling test modules are importable (tests/ is a package; the batteries
# follow the same sys.path convention as tests/test_check_alter_gate.py).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import script_blocks  # noqa: E402  (browser-faithful <script> extraction)
import test_story_editor_serializer_js as sej  # noqa: E402  (shared JS decoder)

# The 14 landed editor assets in sorted (pipeline) order.
ASSET_ORDER = [
    "00_core.js", "05_json.js", "10_load.js", "20_validate.js",
    "30_graph.js", "40_form.js", "42_choices.js", "43_onenter.js",
    "45_lifecycle.js", "50_editscast.js", "60_trace.js", "70_claims.js",
    "80_save.js", "90_boot.js",
]

# One capability signature per asset (verified against the landed sources).
ASSET_SIGNATURES = {
    "00_core.js": "EDITOR.apply =",
    "05_json.js": "EDITOR.housy",
    "10_load.js": "onDrop",
    "20_validate.js": "EDITOR.validate =",
    "30_graph.js": "renderGraph",
    "40_form.js": "text_dramatic",
    "42_choices.js": "goto dropdown",
    "43_onenter.js": "parseScenePaste",
    "45_lifecycle.js": "EDITOR.lifecycle",
    "50_editscast.js": "bad_ending_pool",
    "60_trace.js": "traceWalk",
    "70_claims.js": "reverse index",
    "80_save.js": "downloadText",
    "90_boot.js": "statusbar",
}

# The B1--B11/C/D/E capability matrix (07.1 road-map requirements).
# row = (requirement, owning asset, needles that PROVE the entry point).
# The needles were verified present in the landed asset sources when this
# battery was authored; an assertion here fails loudly on capability
# removal, rename, or an asset silently falling out of the pipeline.
CAPABILITY_MATRIX = [
    # id      asset             needles (every entry must appear)
    ("B1/B2 lifecycle add/delete/recipes",
     "45_lifecycle.js", ["EDITOR.lifecycle", "checkId", "computeReferences",
                         "SEED_TYPES", "COUNT_SHIFT"]),
    ("B3/B5 choices + goto connection dropdown",
     "42_choices.js", ["goto dropdown", "optgroup", "data-ch-"]),
    ("B4/B7/B10 data tab (bad_ending_pool + cast editors)",
     "50_editscast.js", ["bad_ending_pool", 'EDITOR.view("data"']),
    ("B6 node form (story/science text fields)",
     "40_form.js", ["text_dramatic", "text_teaching", "textFieldBindings"]),
    ("B8 on_enter paste",
     "43_onenter.js", ["function parseScenePaste", "OP_NAMES"]),
    ("B9 ending-CG reminder chip",
     "90_boot.js", ["CG \u2192 Phase 12"]),
    ("C claims reverse index",
     "70_claims.js", ["reverse index", "EDITOR.view("]),
    ("D trace with cycle guard",
     "60_trace.js", ["function traceWalk", "already shown"]),
    ("E save (downloadText + draftDoc)",
     "80_save.js", ["function downloadText", "draftDoc",
                    "story_editor_draft.json"]),
    ("E undo/redo (EDITOR.apply/undo/redo)",
     "00_core.js", ["EDITOR.apply =", "EDITOR.undo =", "EDITOR.redo =",
                    "MAX_UNDO"]),
    ("B11 extensibility posture (unknown-key round-trip)",
     "00_core.js", ["EDITOR.nodeSet", "EDITOR.nodeAdd", "EDITOR.nodeDelete"]),
]

# The canonical validator rule ids (source of truth: tools/story_editor_lint.py
# + the parity imports rpg/story/validate.py + rpg/edit_router.py; the JS
# port contract is FROZEN per 07.1-03/07.1-08).
ERROR_RULE_IDS = [
    "dangling_divert", "unreachable_ending", "router_only_incoming",
    "single_continue", "text_layer_empty", "tbd_text", "claim_missing",
    "claim_unapproved", "placeholder_misuse", "offer_without_tag",
    "weight_outside_shuffle", "cond_attribute_form", "empty_bad_ending_pool",
    "pool_node_not_ending", "dangling_pool_node", "duplicate_signature",
    "dangling_edit_branch", "coverage_uncovered", "relationship_pin",
    "start_node_pdb_load", "unknown_op",
]
NOTICE_RULE_IDS = ["count_shift", "sanctioned_residual", "set_view_phase10"]
# The 2 plan-mandated JS-only notices (not Python-portable: browse-only
# context). src: tests/test_glucose_reachability.py:800-843 (hero); the
# per-enzyme empty pool is a legal per-bucket fallback (07.1-08 catalog).
JS_ONLY_NOTICES = ["per_enzyme_pool_empty", "hero_highlight_sequence"]


def run_generator(args):
    # type: (list) -> subprocess.CompletedProcess
    return subprocess.run(
        [sys.executable, GENERATOR] + list(args),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True)


def _read(path):
    # type: (str) -> str
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _asset_block(html, asset_name):
    # type: (str, str) -> str
    """The emitted <script> block text for the named asset (from its
    /* asset: NAME marker through the block's closing tag)."""
    marker = "/* asset: " + asset_name
    start = html.find(marker)
    assert start >= 0, "asset marker %r missing from emitted HTML" % asset_name
    close = html.find("</script>", start)
    assert close > start, "%s block missing its closing tag" % asset_name
    return html[start:close]


class TestCrossAssetIntegration(unittest.TestCase):
    """The capstone battery over ONE generator run (temp-dir output)."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_integration_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. Asset order + completeness.
    # ------------------------------------------------------------------

    def test_asset_order_complete(self):
        """The emitted HTML inlines ALL 14 editor assets in sorted pipeline
        order, each block carrying its owning capability signature."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        positions = []
        for name in ASSET_ORDER:
            marker = "/* asset: " + name
            pos = self.html.find(marker)
            self.assertGreaterEqual(
                pos, 0, "asset %r is NOT inlined in the emitted page" % name)
            positions.append((pos, name))
        for (pos_a, name_a), (pos_b, name_b) in zip(positions,
                                                    positions[1:]):
            self.assertLess(
                pos_a, pos_b,
                "asset %r is inlined after %r (pipeline order = sorted "
                "order)" % (name_a, name_b))
        # No UNEXPECTED asset marker either (an asset removed from the
        # expected list is discovered; one ADDED is also caught here).
        all_markers = re.findall(r"/\* asset: ([a-zA-Z0-9_]+\.js)", self.html)
        self.assertEqual(
            all_markers, ASSET_ORDER,
            "the inlined asset set differs from the expected 14-asset set: "
            "%r" % (all_markers,))
        # Per-asset capability signature, scoped to its own block.
        for name, sig in ASSET_SIGNATURES.items():
            block = _asset_block(self.html, name)
            self.assertIn(
                sig, block,
                "asset %r block lacks its capability signature %r"
                % (name, sig))

    def test_committed_artifact_fresh(self):
        """Regenerating NOW reproduces the committed repo-root
        story_editor.html modulo the generated-at timestamp (the committed
        artifact = current assets; a stale committed page fails loudly)."""
        self.assertEqual(self.proc.returncode, 0)
        committed = _read(COMMITTED_HTML)
        stamp_re = re.compile(r"generated \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
        norm_committed = stamp_re.sub("generated <STAMP>", committed)
        norm_fresh = stamp_re.sub("generated <STAMP>", self.html)
        self.assertEqual(
            norm_fresh, norm_committed,
            "the committed story_editor.html is STALE vs current assets -- "
            "run tools/story_editor.py and commit the artifact")

    # ------------------------------------------------------------------
    # 2. The B1--B11/C/D/E capability matrix.
    # ------------------------------------------------------------------

    def test_capability_matrix(self):
        """Every capability entry point of the 7.1 requirement set is
        present in the emitted HTML, scoped to the OWNING asset block."""
        self.assertEqual(self.proc.returncode, 0)
        for label, asset, needles in CAPABILITY_MATRIX:
            block = _asset_block(self.html, asset)
            for needle in needles:
                self.assertIn(
                    needle, block,
                    "capability [%s]: entry point %r missing from the "
                    "emitted %s block" % (label, needle, asset))

    # ------------------------------------------------------------------
    # 3. Offline cleanliness.
    # ------------------------------------------------------------------

    def test_offline_clean(self):
        """No external src/href, no ES modules, no top-level imports, and
        at most one documented fetch site (in 10_load.js; currently ZERO
        since the 07.1-11 fetch transport removal)."""
        self.assertEqual(self.proc.returncode, 0)
        self.assertIsNone(
            re.search(r"<script[^>]*\ssrc=", self.html),
            "external script reference found")
        self.assertIsNone(
            re.search(r"<link\s", self.html), "<link> tag found")
        self.assertNotIn('src="http', self.html)
        self.assertNotIn('href="http', self.html)
        self.assertNotIn('type="module"', self.html)
        blocks = script_blocks.extract_script_blocks(self.html)
        self.assertTrue(blocks, "expected at least one script block")
        for block in blocks:
            self.assertNotEqual(
                (block.attrs.get("type") or "").lower(), "module",
                "ES-module script block found")
            self.assertIsNone(
                re.search(r"(?m)^\s*import(?:\s|[\"('\)])", block.text),
                "top-level import statement found in a script block")
        # fetch() sites: the 07.1-11 policy record pins ZERO fetch sites in
        # the load asset (XHR transport). Bound at <= 1 so a welcomed probe
        # re-introduction would need this pin re-justified.
        fetch_hits = []
        for name in ASSET_ORDER:
            block = _asset_block(self.html, name)
            count = block.count("fetch(")
            if count:
                fetch_hits.append((name, count))
        self.assertLessEqual(
            len(fetch_hits), 1,
            "fetch() call-sites found in multiple asset blocks: %r -- the "
            "documented probe must be the ONLY fetch site" % (fetch_hits,))
        if fetch_hits:
            name, count = fetch_hits[0]
            self.assertEqual(
                name, "10_load.js",
                "a fetch() call-site exists outside 10_load.js (%s) -- "
                "violates the corrected transport record" % name)
            self.assertLessEqual(
                count, 1,
                "more than one fetch() call-site in 10_load.js (%d)" % count)

    # ------------------------------------------------------------------
    # 4. Token leaks.
    # ------------------------------------------------------------------

    def test_no_token_leaks(self):
        """Zero unresolved __TOKEN__ regions in the emitted page."""
        self.assertEqual(self.proc.returncode, 0)
        for token in ("__TITLE__", "__GENERATED_AT__", "__ASSET_MANIFEST__",
                      "__ASSETS__"):
            self.assertNotIn(
                token, self.html,
                "unresolved token %s leaked into the HTML" % token)
        residue = re.search(r"__[A-Z][A-Z0-9_]*__", self.html)
        self.assertIsNone(
            residue,
            "generic __TOKEN__-pattern residue: %r"
            % (residue and residue.group(0)))

    # ------------------------------------------------------------------
    # 5. Serializer fixture vectors embedded (emitted block, verbatim).
    # ------------------------------------------------------------------

    def test_serializer_vectors_embedded(self):
        """Every tools/story_editor_json.py fixture_vectors() (name,
        expected) pair is embedded VERBATIM in the emitted 05_json block's
        SELFTEST_VECTORS (decoded with the shared sibling-battery decoder --
        the emitted block is the asset verbatim per the inlining pin)."""
        self.assertEqual(self.proc.returncode, 0)
        block = _asset_block(self.html, "05_json.js")
        vectors = sej.story_editor_json.fixture_vectors()
        self.assertEqual(len(vectors), 11,
                         "fixture_vectors() count changed -- update this "
                         "battery in the same commit")
        region = sej._table_region(block)
        names = sej.NAME_RE.findall(region)
        chains = sej.EXPECTED_CHAIN_RE.findall(region)
        self.assertEqual(len(names), len(vectors),
                         "emitted SELFTEST_VECTORS entry count differs")
        self.assertEqual(len(chains), len(vectors),
                         "emitted expected-constant count differs")
        for (py_name, _py_obj, py_expected), js_name, chain in zip(
                vectors, names, chains):
            self.assertEqual(
                js_name, py_name,
                "vector-name drift: %r != %r" % (js_name, py_name))
            self.assertEqual(
                sej._decode_chain(chain), py_expected,
                "vector %r: embedded JS expected constant diverges from the "
                "canonical fixture output" % py_name)

    # ------------------------------------------------------------------
    # 6. Validator rule parity.
    # ------------------------------------------------------------------

    def test_validator_rule_parity(self):
        """All 21 error rule ids + 3 notice ids + the 2 JS-only notices are
        quoted in the emitted 20_validate block; the Python kind harvest
        from story_editor_lint.py is a subset (drift guard)."""
        self.assertEqual(self.proc.returncode, 0)
        block = _asset_block(self.html, "20_validate.js")
        for rid in ERROR_RULE_IDS + NOTICE_RULE_IDS + JS_ONLY_NOTICES:
            self.assertTrue(
                ('"%s"' % rid) in block or ("'%s'" % rid) in block,
                "rule id %r missing from the emitted validator block" % rid)
        self.assertEqual(
            len(ERROR_RULE_IDS), 21,
            "the error-rule list no longer matches the frozen 07.1-03 "
            "catalog (21 ids)")
        self.assertEqual(len(NOTICE_RULE_IDS), 3)
        # Dynamic harvest from the Python catalog: every kind recorded by a
        # LintIssue(...) must be covered by ONE of the three id lists.
        lint_src = _read(LINT)
        harvested = set(re.findall(
            r'LintIssue\(\s*\n?\s*"([a-z0-9_]+)"', lint_src))
        known = set(ERROR_RULE_IDS + NOTICE_RULE_IDS + JS_ONLY_NOTICES)
        orphan = sorted(harvested - known)
        self.assertEqual(
            orphan, [],
            "story_editor_lint.py records kinds not in the frozen parity "
            "lists: %r -- extend this battery in the same commit" % orphan)


class TestGatesPairing(unittest.TestCase):
    """The suite-level gate pairing (07.1-19 Task 1 test spec #5)."""

    def test_lint_green_and_generator_green(self):
        """Subprocess python3.6 tools/story_editor_lint.py -> exit 0 on the
        live repo; generator re-run -> exit 0 (the suite's own two shell
        commands remain green while the browser round trip is exercised in
        the human checkpoint)."""
        lint = subprocess.run(
            [sys.executable, LINT], cwd=REPO_ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        self.assertEqual(
            lint.returncode, 0,
            "story_editor_lint.py returned %d on the live repo\n"
            "stdout: %s\nstderr: %s"
            % (lint.returncode, lint.stdout, lint.stderr))
        tmpdir = tempfile.mkdtemp(prefix="story_editor_gate_")
        try:
            out = os.path.join(tmpdir, "story_editor.html")
            gen = run_generator(["--output", out])
            self.assertEqual(
                gen.returncode, 0,
                "generator re-run returned %d\nstdout: %s\nstderr: %s"
                % (gen.returncode, gen.stdout, gen.stderr))
            self.assertTrue(os.path.isfile(out),
                            "generator exit 0 but no output written")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
