#!/usr/bin/env python3.6
"""Parity pins: the Python-authoritative lint (07.1-03) vs the JS validator
(07.1-08, tools/story_editor_assets/20_validate.js).

tools/story_editor_lint.py is the RULE CATALOG the browser validator ports
1:1 — same rule ids, same severity split (error vs notice), same BFS
semantics (goto edges only, cond/weight ignored, on_enter_divert never
followed), and the sanctioned citation residual encoded EXACTLY
(PLACEHOLDER_PHASE8 only on fa.stub/alc.stub; approval_status === "approved"
STRICTLY — rpg/citations.py:100-109 Pitfall 6, never a not-equal-pending
shortcut). The editor must catch what the suite would catch BEFORE the
human saves (RESEARCH-SAFETY Pitfall S4: each JS rule cites its Python
source line, same as the repo's "# src:" convention).

What THIS battery pins mechanically from WSL (the runtime equivalence is
proven in-browser by the human-verify checkpoints and by the 47-check
headless-JS smoke recorded in the 07.1-08 summary):

  1. RULE-ID PARITY — the rule ids asserted by tests/test_story_editor_lint.py
     (parsed live: every "LINT <kind>:" / "LINT NOTICE <kind>:" marker) plus
     the plan's embedded fallback catalog (the full contract; the lint
     battery's markers do not cover offer_without_tag) must ALL appear in
     the JS asset. The parsed set must be a subset of the embedded catalog
     (a new lint id without a port is drift detected loudly).
  2. SANCTIONED RESIDUAL EXACT — PLACEHOLDER_PHASE8 / fa.stub / alc.stub
     co-occur in the asset; the strict comparison
     "approval_status === \"approved\"" is present IN CODE; no
     not-equal-pending shortcut exists anywhere in the asset.
  3. BFS PARITY COMMENTS — the asset cites rpg/story/validate.py for the
     BFS, states the goto-only/cond-weight-ignored semantics, and the
     dormant on_enter_divert string appears ONLY on "never followed"
     comment lines (never as followed code).
  4. GATING API — EDITOR.validate / validateCurrent / saveBlocked /
     bfsReachable exist; the hooks.validate registration (via EDITOR.init)
     is present; the count_shift notice names the pinned-test trio + the
     viewer's pinned constants; the countShifts struct is shaped.
  5. ASSET INLINED — regenerating the editor emits the 20_validate.js
     asset block in sorted order (after 10_load.js when present, before
     30_graph.js when present) and before the shell's DOMContentLoaded
     bootstrap, with the validator needles present in the emitted HTML.
  6. ES5 DISCIPLINE — var/function only: no arrow functions, no let/const,
     no template literals, no ES-module markers (same pins as the
     07.1-04/07.1-05 batteries).

Python 3.6 stdlib ONLY (unittest/os/re/sys/subprocess/tempfile/shutil).
NO pytest (not installed). NO f-strings (.format() / % per repo
convention). NO pymol/PyQt5 imports (the AST import gate scans tests/).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
GENERATOR = os.path.join(REPO_ROOT, "tools", "story_editor.py")
ASSET = os.path.join(REPO_ROOT, "tools", "story_editor_assets",
                     "20_validate.js")
LINT_BATTERY = os.path.join(REPO_ROOT, "tests", "test_story_editor_lint.py")
LINT_MODULE = os.path.join(REPO_ROOT, "tools", "story_editor_lint.py")

# "LINT <kind>: ..." / "LINT NOTICE <kind>: ..." markers in the lint's own
# battery — the ids the Python tests mechanically assert (the frozen port
# contract, tests/test_story_editor_lint.py header).
LINT_ID_RE = re.compile(r'LINT (?:NOTICE )?([a-z_]+):')

# The plan's embedded fallback catalog (07.1-08-PLAN.md Task 1) — the FULL
# rule-id contract. The lint battery's LINT markers miss offer_without_tag
# (the lint's rule_edit_offer_tag emits it; no seeded test asserts the id),
# so the embedded list is the authoritative full catalog and the parsed
# markers must be a SUBSET of it.
EMBEDDED_ERROR_IDS = [
    "dangling_divert", "unreachable_ending", "router_only_incoming",
    "single_continue", "text_layer_empty", "tbd_text", "claim_missing",
    "claim_unapproved", "placeholder_misuse", "offer_without_tag",
    "weight_outside_shuffle", "cond_attribute_form", "empty_bad_ending_pool",
    "pool_node_not_ending", "dangling_pool_node", "duplicate_signature",
    "dangling_edit_branch", "coverage_uncovered", "relationship_pin",
    "start_node_pdb_load", "unknown_op",
]
EMBEDDED_NOTICE_IDS = [
    "count_shift", "sanctioned_residual", "set_view_phase10",
]
# Plan-mandated JS-only notices (07.1-08 Task 1): the per-enzyme-empty-pool
# fallback info and the hero-highlight ordered-subsequence WARNING — both
# notice severity (never gate a save; the Python lint has no rule there).
JS_ONLY_NOTICE_IDS = ["per_enzyme_pool_empty", "hero_highlight_sequence"]

# The count_shift same-commit obligations (exact pinned-test names + the
# viewer's pinned constants).
COUNT_SHIFT_TESTS = [
    "test_manifest_loads_all_57_nodes",
    "test_reachability_green_all_four_tiers",
    "test_15_edit_allowed_nodes",
]
COUNT_SHIFT_CONSTANTS = [
    "EXPECTED_NODES", "EXPECTED_TIER_COUNTS", "EXPECTED_EDIT_ALLOWED",
]

# Every rule's Python source of truth must be cited in the asset (the
# repo's "# src:" convention, ported as "src: <path:line>" comments).
REQUIRED_SRC_CITATIONS = [
    "rpg/story/validate.py:167-207",    # BFS (check_reachability)
    "rpg/story/validate.py:214-235",    # validate_graph (dangling_divert)
    "rpg/edit_router.py:172-235",       # validate_edits_table family
    "rpg/edit_router.py:238-255",       # scan_edit_coverage
    "rpg/edit_router.py:193-199",       # per-enzyme fallback semantics
    "rpg/citations.py:100-109",         # is_approved strict predicate
    "tools/check_citations.py:44-95",   # the citation gate
    "rpg/pymol_layer/molops.py:140-291",  # the op vocabulary
    "tools/story_graph_viewer.py:96-105",  # the viewer's pinned constants
    "tests/test_glucose_reachability.py:326-452",  # router-only nodes
    "tests/test_glucose_reachability.py:716-752",  # cond attribute form
    "tests/test_glucose_reachability.py:800-843",  # hero highlight
    "tests/test_glucose_reachability.py:868-885",  # start-node pdb rule
    "tests/test_glucose_content.py:126-184",  # two-layer text
    "tests/test_glucose_content.py:187-257",  # claim hygiene
    "tests/test_glucose_content.py:213-236",  # sanctioned residual scope
    "tests/test_glucose_content.py:404-449",  # relationship pin
    "tests/test_glucose_content.py:539-557",  # shuffle-only weights
]


def _read(path):
    # type: (str) -> str
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class TestRuleIdParity(unittest.TestCase):
    """Rule 1: every lint rule id (parsed live + the embedded full
    catalog) appears in the JS asset; the parsed set is a subset of the
    embedded catalog."""

    def test_parsed_ids_subset_of_embedded_catalog(self):
        parsed = sorted(set(LINT_ID_RE.findall(_read(LINT_BATTERY))))
        embedded = set(EMBEDDED_ERROR_IDS) | set(EMBEDDED_NOTICE_IDS)
        self.assertTrue(
            parsed, "no LINT markers parsed from the lint battery")
        strays = [i for i in parsed if i not in embedded]
        self.assertEqual(
            strays, [],
            "the lint battery asserts rule id(s) missing from this test's "
            "embedded catalog -- the JS-port contract moved; update "
            "EMBEDDED_*_IDS AND the JS asset in the same commit")

    def test_every_rule_id_in_asset(self):
        src = _read(ASSET)
        for rid in EMBEDDED_ERROR_IDS + EMBEDDED_NOTICE_IDS:
            self.assertIn(
                rid, src, "rule id %r missing from the JS validator "
                "asset (the 1:1 port contract)" % rid)

    def test_lint_battery_ids_in_asset(self):
        src = _read(ASSET)
        parsed = sorted(set(LINT_ID_RE.findall(_read(LINT_BATTERY))))
        for rid in parsed:
            self.assertIn(rid, src,
                          "lint-battery rule id %r missing from the asset"
                          % rid)

    def test_js_only_notices_present(self):
        src = _read(ASSET)
        for rid in JS_ONLY_NOTICE_IDS:
            self.assertIn(rid, src,
                          "plan-mandated JS-only notice %r missing" % rid)

    def test_every_src_citation_present(self):
        src = _read(ASSET)
        missing = [s for s in REQUIRED_SRC_CITATIONS if s not in src]
        self.assertEqual(
            missing, [],
            "missing src: citation(s) in the asset (Pitfall S4: every JS "
            "rule cites its Python source line)")

    def test_rule_function_per_catalog_shape(self):
        """One function per rule family, mirroring the lint's def rule_*
        contract: at least 15 rule functions exist (the lint has 15)."""
        src = _read(ASSET)
        count = len(re.findall(r"\n  function rule[A-Za-z]+\(", src))
        self.assertGreaterEqual(
            count, 15,
            "expected >=15 rule functions (the lint's 15 def rule_* "
            "functions), found %d" % count)

    def test_header_cites_parity_source(self):
        src = _read(ASSET)
        self.assertIn("tools/story_editor_lint.py", src)
        self.assertIn("07.1-08", src)


class TestSanctionedResidualEncoding(unittest.TestCase):
    """Rule 2: the residual is encoded EXACTLY and the approval predicate
    is STRICT (Pitfall S6 + rpg/citations.py:100-109 Pitfall 6)."""

    def test_strict_approved_comparison_in_code(self):
        src = _read(ASSET)
        # The canonical predicate, in CODE (not only prose):
        self.assertIn('record.approval_status === "approved"', src,
                      "the strict approval_status === \"approved\" "
                      "comparison must appear in the asset's code")
        self.assertIn("rpg/citations.py:100-109", src)

    def test_no_not_pending_shortcut(self):
        src = _read(ASSET)
        # The FORBIDDEN shortcut (Pitfall 6): a not-equal-pending check
        # would erroneously pass REJECTED claims. Must be absent in any
        # quoting style, comments included.
        self.assertNotIn('!== "pending"', src)
        self.assertNotIn("!== 'pending'", src)
        self.assertNotIn('!= "pending"', src)
        self.assertNotIn("!= 'pending'", src)

    def test_stub_pair_cooccurs_with_claim(self):
        src = _read(ASSET)
        self.assertIn("PLACEHOLDER_PHASE8", src)
        self.assertIn('"fa.stub"', src)
        self.assertIn('"alc.stub"', src)
        # The scoping prose: the claim is sanctioned ONLY on the stub pair.
        self.assertIn("sanctioned ONLY on", src)

    def test_bidirectional_residual_guard(self):
        """A sanctioned stub LOSING its reference must be an error too
        (the gate's pinned 2-MISSING form breaks in that direction)."""
        src = _read(ASSET)
        self.assertIn("exactly once", src)


class TestBfsParityComments(unittest.TestCase):
    """Rule 3: the BFS cites the Python source, states the goto-only
    semantics, and never follows the dormant on_enter_divert."""

    def test_bfs_cites_check_reachability(self):
        src = _read(ASSET)
        self.assertIn("rpg/story/validate.py:167-207", src)

    def test_goto_only_semantics_stated(self):
        src = _read(ASSET)
        self.assertIn("choice.goto edges ONLY", src)
        self.assertIn("cond/weight", src)
        self.assertIn("IGNORED", src)

    def test_on_enter_divert_never_followed(self):
        """The dormant field may appear ONLY inside 'never followed'
        comment lines -- never as followed code (RESEARCH-SAFETY
        'Don't Hand-Roll': following it would disagree with the Python
        gate -> false green/red)."""
        src = _read(ASSET)
        self.assertIn("on_enter_divert", src)
        for line in src.splitlines():
            if "on_enter_divert" in line:
                self.assertIn(
                    "never followed", line.lower(),
                    "on_enter_divert appears outside a never-followed "
                    "comment: %r" % line.strip())


class TestGatingApi(unittest.TestCase):
    """Rule 4: the validator + gating API + hook registration + the
    count_shift acknowledgment payload."""

    def test_entry_points_present(self):
        src = _read(ASSET)
        for needle in ("EDITOR.validate", "EDITOR.validateCurrent",
                       "EDITOR.saveBlocked", "EDITOR.bfsReachable",
                       "EDITOR._lastValidation"):
            self.assertIn(needle, src, "missing gating entry point %s"
                          % needle)

    def test_hooks_validate_registered_via_init(self):
        src = _read(ASSET)
        self.assertIn("EDITOR.hooks.validate.push", src,
                      "the validator must register into hooks.validate "
                      "(00_core dispatches it after every mutation)")
        self.assertIn("EDITOR.init(", src,
                      "the hook registration is added via EDITOR.init")

    def test_count_shift_notice_names_pinned_trio(self):
        src = _read(ASSET)
        for name in COUNT_SHIFT_TESTS:
            self.assertIn(name, src,
                          "count_shift notice must name %s" % name)
        for const in COUNT_SHIFT_CONSTANTS:
            self.assertIn(const, src,
                          "count_shift notice must name %s" % const)

    def test_count_shifts_struct_shaped(self):
        src = _read(ASSET)
        self.assertIn("countShifts", src)
        self.assertIn("changed:", src)
        self.assertIn("added:", src)
        self.assertIn("removed:", src)

    def test_result_shape_fields(self):
        src = _read(ASSET)
        # errors/notices entries carry {kind, node, detail, src, severity}.
        self.assertIn("kind:", src)
        self.assertIn("severity:", src)


class TestAssetInlining(unittest.TestCase):
    """Rule 5: regenerating the editor inlines the validator after the
    load asset (10_) and before the view assets (30_+), sorted, and
    before the shell bootstrap."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_validate_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = subprocess.run(
            [sys.executable, GENERATOR, "--output", cls.out_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _markers(self):
        # type: () -> list
        return re.findall(r"/\* asset: (\S+) \(", self.html)

    def test_generation_succeeds(self):
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        self.assertTrue(self.html, "generator emitted no HTML")

    def test_validator_asset_inlined(self):
        self.assertIn("/* asset: 20_validate.js (", self.html)
        for needle in ("EDITOR.validate", "bfsReachable",
                       "EDITOR.saveBlocked", "PLACEHOLDER_PHASE8",
                       "test_manifest_loads_all_57_nodes",
                       "test_reachability_green_all_four_tiers",
                       "test_15_edit_allowed_nodes", "count_shift",
                       'approval_status === "approved"'):
            self.assertIn(needle, self.html,
                          "emitted HTML lacks %r from the validator asset"
                          % needle)

    def test_order_between_load_and_view_assets(self):
        markers = self._markers()
        self.assertIn("20_validate.js", markers)
        self.assertEqual(markers, sorted(markers),
                         "asset markers not in sorted order: %r"
                         % (markers,))
        if "10_load.js" in markers:
            self.assertLess(
                markers.index("10_load.js"), markers.index("20_validate.js"),
                "the validator must inline AFTER the load asset")
        if "30_graph.js" in markers:
            self.assertGreater(
                markers.index("30_graph.js"), markers.index("20_validate.js"),
                "the validator must inline BEFORE the graph view assets")
        if "00_core.js" in markers:
            self.assertLess(
                markers.index("00_core.js"), markers.index("20_validate.js"),
                "the validator must inline AFTER the core asset")

    def test_block_closes_before_bootstrap(self):
        i_open = self.html.find("/* asset: 20_validate.js")
        i_close = self.html.find("</script>", i_open)
        i_bootstrap = self.html.rfind("<script>")
        self.assertLess(
            i_close, i_bootstrap,
            "the validator asset block must come before the bootstrap "
            "script block")


class TestAssetEs5Discipline(unittest.TestCase):
    """Rule 6: the asset stays ES5 (var/function only) -- same discipline
    the 07.1-04/07.1-05 batteries pin for the emitted page."""

    def test_no_arrow_functions(self):
        src = _read(ASSET)
        self.assertNotIn("=>", src, "arrow function found in the asset")

    def test_no_let_const(self):
        src = _read(ASSET)
        self.assertIsNone(re.search(r"\blet\s", src),
                          "let declaration found in the asset")
        self.assertIsNone(re.search(r"\bconst\s", src),
                          "const declaration found in the asset")

    def test_no_template_literals(self):
        src = _read(ASSET)
        self.assertNotIn("`", src, "backtick template literal found")

    def test_no_modules_no_top_level_import(self):
        src = _read(ASSET)
        self.assertIsNone(
            re.search(r"(?m)^\s*import(?:\s|[\"('\)])", src),
            "top-level import statement found in the asset")

    def test_lint_module_untouched_contract(self):
        """The lint is 07.1-03's file: this plan must NOT have added a
        RULE_IDS constant or any other edit to it (the rule ids are parsed
        from the battery + embedded here instead)."""
        lint_src = _read(LINT_MODULE)
        self.assertNotIn("RULE_IDS", lint_src,
                         "the lint must stay byte-untouched by 07.1-08")


if __name__ == "__main__":
    unittest.main()
