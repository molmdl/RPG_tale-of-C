#!/usr/bin/env python3.6
"""TDD battery for tools/story_editor_lint.py (Phase 7.1 plan 07.1-03).

The lint is the Python-authoritative pre-save/post-save validator for the
story-node HTML editor: green on the REAL bundle, red on every seeded
violation class. The rule ids asserted here are the FROZEN CONTRACT the JS
validator (plan 07.1-08) ports 1:1 into the browser -- each rule id must stay
stable and citable (the (src: <path:lines>) citation in every lint line is
part of that contract).

Structure (per the plan's Task 1):
- ``real_bundle_clean`` lints the LIVE repo data and demands zero errors,
  exit 0, with the sanctioned residual (exactly the fa.stub/alc.stub
  PLACEHOLDER_PHASE8 pair) reported as a NOTICE, never an error.
- Every other test DEEP-COPIES the real bundle into a per-test temp dir
  (shutil.copytree -- the on-disk deep copy), mutates ONE aspect, runs the
  lint CLI via subprocess, and asserts the specific issue kind appears and
  the exit code is 1 (or 0 for the count_shift/set_view NOTICE cases).
  The real registry/edits/cast/sources are used read-only unless the test
  itself copies them (pool/signature/coverage cases mutate edits.json /
  cast.json in the temp dir).

Seeded rule catalog (one seeded case per rule id; ids == the JS port's
contract, mirroring the plan's 18-item list):

 1. real_bundle_clean            (exit 0; exactly the sanctioned-residual notice)
 2. dangling_goto                -> dangling_divert
 3. orphan_ending                -> unreachable_ending (+ reachability not_ok)
 4. router_only_edge             -> router_only_incoming
 5. single_continue              -> single_continue
 6. two_layer_blank              -> text_layer_empty ; tbd_text -> tbd_text
 7. claim_unapproved / missing   -> claim_unapproved / claim_missing
 8. sanctioned_residual_scope    -> placeholder_misuse
 9. edit_offer_tag_mismatch      -> offer_without_tag
10. pool_empty / not_ending / dangling -> empty_bad_ending_pool /
    pool_node_not_ending / dangling_pool_node
11. signature_duplicate          -> duplicate_signature ; branch_dangling ->
    dangling_edit_branch
12. weight_outside_shuffle       -> weight_outside_shuffle
13. cond_attribute_form          -> cond_attribute_form
14. cast_without_bucket          -> coverage_uncovered ; relationship pin
    broken                       -> relationship_pin
15. start_node_pdb_load          -> start_node_pdb_load
16. unknown_op                   -> unknown_op ; set_view -> NOTICE (not error)
17. count_shift_notice           -> count_shift NOTICE (exit 0) naming the
    pinned tests + viewer constants
18. exit_code_contract           errors -> 1; unparseable JSON / schema /
    duplicate registry key -> 2; clean -> 0

Python 3.6 stdlib ONLY (unittest/subprocess/os/sys/json/shutil/tempfile/
importlib). NO pytest (not installed). subprocess uses stdout/stderr=PIPE +
manual .decode() (NOT capture_output/text -- both 3.7+). NO f-strings
(.format() per repo convention). NO pymol/PyQt5 (the AST gate scans tests/).
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(HERE, "..")
STORY_DIR = os.path.join(REPO_ROOT, "data", "story_glucose")
REGISTRY_PATH = os.path.join(REPO_ROOT, "data", "citations.json")
EDITS_PATH = os.path.join(REPO_ROOT, "rpg", "data", "edits.json")
CAST_PATH = os.path.join(REPO_ROOT, "rpg", "data", "cast.json")
SOURCES_PATH = os.path.join(REPO_ROOT, "data", "sources.json")
LINT_SCRIPT = os.path.join(REPO_ROOT, "tools", "story_editor_lint.py")

MANIFEST_FILES = [
    "intro.json", "glycolysis.json", "pyruvate_branch.json", "tca.json",
    "etc_atp.json", "endings.json", "bad_endings.json",
]


def _run_lint(story_dir, registry=None, edits=None, cast=None, sources=None):
    # type: (str, str, str, str, str) -> tuple
    """Run the lint CLI via subprocess. Returns (returncode, stdout_text).

    Uses stdout/stderr=PIPE + manual decode (3.6-safe; mirrors
    test_glucose_content.py's subprocess pattern). Unset args fall back to
    the REAL repo paths (the lint's own defaults) -- read-only.
    """
    cmd = [sys.executable, LINT_SCRIPT, "--story-dir", story_dir]
    if registry is not None:
        cmd += ["--registry", registry]
    if edits is not None:
        cmd += ["--edits", edits]
    if cast is not None:
        cmd += ["--cast", cast]
    if sources is not None:
        cmd += ["--sources", sources]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.decode("utf-8")


class _BundleCopyTestCase(unittest.TestCase):
    """Shared fixture: a fresh deep copy of the real story bundle per test.

    The copy lives in a per-test temp dir (shutil.copytree = the on-disk
    deep copy), so mutations never touch the real data files. Registry /
    edits / cast / sources default to the REAL repo paths (read-only);
    tests that mutate edits.json/cast.json copy those files too and pass
    the temp paths explicitly.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lint_test_")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.story_dir = os.path.join(self.tmp, "story")
        shutil.copytree(STORY_DIR, self.story_dir)

    def _mutate_story(self, filename, mutate_fn):
        # type: (str, object) -> None
        """Load one story file from the temp copy, apply mutate_fn, dump."""
        path = os.path.join(self.story_dir, filename)
        with open(path, "r") as fh:
            data = json.load(fh)
        mutate_fn(data)
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)

    def _copy_support(self, repo_path, label):
        # type: (str, str) -> str
        """Copy a supporting manifest (edits/cast/registry) into the temp dir."""
        dest = os.path.join(self.tmp, label)
        shutil.copy2(repo_path, dest)
        return dest


class TestRealBundleClean(unittest.TestCase):
    """Rule 1: the untouched live bundle lints GREEN (exit 0, zero errors),
    with the sanctioned residual reported as a NOTICE, never an error."""

    def test_real_bundle_clean(self):
        """The lint on the live repo data must exit 0 with ZERO errors and
        exactly ONE notice: the sanctioned-residual notice naming the
        fa.stub/alc.stub -> PLACEHOLDER_PHASE8 pair (RESEARCH-SAFETY
        Pitfall S6: the residual is encoded EXACTLY -- more stubs, fewer
        stubs, or a misplaced PLACEHOLDER is an error, not a notice)."""
        code, out = _run_lint(STORY_DIR)
        self.assertEqual(
            code, 0,
            "lint on the untouched live bundle must exit 0\nstdout=%r" % out)
        self.assertIn("LINT: 0 errors,", out,
                      "summary line must report zero errors\nstdout=%r" % out)
        self.assertIn("(exit 0)", out)
        # The ONLY notice is the sanctioned residual.
        self.assertEqual(
            out.count("LINT NOTICE"), 1,
            "exactly one notice expected (the sanctioned residual)\n"
            "stdout=%r" % out)
        self.assertIn("LINT NOTICE sanctioned_residual:", out)
        self.assertIn("fa.stub", out)
        self.assertIn("alc.stub", out)
        self.assertIn("PLACEHOLDER_PHASE8", out)
        # No error lines of any kind.
        for kind in ("dangling_divert", "unreachable_ending",
                     "router_only_incoming", "single_continue",
                     "text_layer_empty", "tbd_text", "claim_missing",
                     "claim_unapproved", "placeholder_misuse",
                     "offer_without_tag", "weight_outside_shuffle",
                     "cond_attribute_form", "coverage_uncovered",
                     "relationship_pin", "start_node_pdb_load",
                     "unknown_op"):
            self.assertNotIn(
                "LINT " + kind + ":", out,
                "clean bundle must not raise " + kind)


class TestSeededViolations(_BundleCopyTestCase):
    """Rules 2-17: one seeded violation class per rule id.

    Every test asserts the SPECIFIC rule id appears in the lint output and
    the exit code is 1 (except the two NOTICE-only cases: set_view and
    count_shift, which must stay exit 0). These ids are the JS-port
    contract (07.1-08) -- renaming one breaks the port.
    """

    def test_dangling_goto(self):
        """Rule 2: retarget a choice.goto to a missing node -> the rpg
        validate_graph parity rule fires (dangling_divert)."""
        def mutate(data):
            ch = data["nodes"]["intro.preface"]["choices"]
            ch[1]["goto"] = "lint.missing.node"
        self._mutate_story("intro.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(code, 1, "dangling goto is an error\nstdout=%r" % out)
        self.assertIn("LINT dangling_divert:", out)
        self.assertIn("lint.missing.node", out)

    def test_orphan_ending(self):
        """Rule 3: add an ending node with no inbound edge -> unreachable_ending
        (the reachability report must ALSO be not_ok -- the rpg
        check_reachability parity is load-bearing)."""
        def mutate(data):
            data["nodes"]["end.orphan.lint"] = {
                "text_dramatic": "An orphaned ending seeded by the lint test.",
                "text_teaching": "An orphaned ending seeded by the lint test.",
                "claim_ids": [],
                "tags": ["ending:bad"],
                "on_enter": [{"op": "hide_all"}],
                "is_ending": "bad",
                "choices": [],
            }
        self._mutate_story("endings.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(code, 1, "orphan ending is an error\nstdout=%r" % out)
        self.assertIn("LINT unreachable_ending:", out)
        self.assertIn("end.orphan.lint", out)

    def test_router_only_edge(self):
        """Rule 4: add a choice.goto INTO gly.pfk_restored -> router_only_incoming
        (the restored nodes' entry is router-only; tests/
        test_glucose_reachability.py:326 pins zero incoming edges)."""
        def mutate(data):
            data["nodes"]["gly.fbp_to_pyruvate"]["choices"].append(
                {"label": "Go to the restored enzyme", "goto": "gly.pfk_restored"})
        self._mutate_story("glycolysis.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 1, "edge into a router-only node is an error\nstdout=%r" % out)
        self.assertIn("LINT router_only_incoming:", out)
        self.assertIn("gly.pfk_restored", out)

    def test_single_continue(self):
        """Rule 5: reduce a 2-choice non-ending node to one Continue ->
        single_continue (the Continue-to-MC invariant,
        tests/test_glucose_reachability.py:245)."""
        def mutate(data):
            data["nodes"]["gly.start"]["choices"] = [
                {"label": "Continue", "goto": "gly.g6p"}]
        self._mutate_story("glycolysis.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(code, 1, "single-Continue node is an error\nstdout=%r" % out)
        self.assertIn("LINT single_continue:", out)
        self.assertIn("gly.start", out)

    def test_two_layer_blank(self):
        """Rule 6a: blank a text_teaching -> text_layer_empty (STORY-06
        two-layer invariant; edit.prompt is the ONLY exempt node)."""
        def mutate(data):
            data["nodes"]["intro.preface"]["text_teaching"] = ""
        self._mutate_story("intro.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(code, 1, "blank text layer is an error\nstdout=%r" % out)
        self.assertIn("LINT text_layer_empty:", out)
        self.assertIn("intro.preface", out)

    def test_tbd_text(self):
        """Rule 6b: insert "TBD" into a choice label -> tbd_text (the
        no-TBD completion scan; edit.prompt's stub marker is the only
        sanctioned TBD)."""
        def mutate(data):
            data["nodes"]["gly.start"]["choices"][0]["label"] = "Continue (TBD)"
        self._mutate_story("glycolysis.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(code, 1, "TBD residue is an error\nstdout=%r" % out)
        self.assertIn("LINT tbd_text:", out)

    def test_claim_unapproved(self):
        """Rule 7a: point a node's claim_ids at a PENDING registry claim ->
        claim_unapproved (approval_status == "approved" strictly -- a
        pending claim is not approved, tools/check_citations.py semantics)."""
        def mutate(data):
            data["nodes"]["tca.entry"]["claim_ids"] = ["BAD-MISFOLD-01"]
        self._mutate_story("tca.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 1, "pending claim reference is an error\nstdout=%r" % out)
        self.assertIn("LINT claim_unapproved:", out)
        self.assertIn("BAD-MISFOLD-01", out)

    def test_claim_missing(self):
        """Rule 7b: point a node's claim_ids at an id absent from the
        registry -> claim_missing."""
        def mutate(data):
            data["nodes"]["tca.entry"]["claim_ids"] = ["LINT-FAKE-CLAIM-01"]
        self._mutate_story("tca.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 1, "missing claim reference is an error\nstdout=%r" % out)
        self.assertIn("LINT claim_missing:", out)
        self.assertIn("LINT-FAKE-CLAIM-01", out)

    def test_sanctioned_residual_scope(self):
        """Rule 8: the sanctioned residual is scoped EXACTLY. (a)
        PLACEHOLDER_PHASE8 on any node other than fa.stub/alc.stub ->
        placeholder_misuse. (b) Any other PLACEHOLDER* id anywhere ->
        placeholder_misuse (catches PHASE5/6/9 residue)."""
        def mutate_misplaced(data):
            data["nodes"]["gly.start"]["claim_ids"].append("PLACEHOLDER_PHASE8")
        self._mutate_story("glycolysis.json", mutate_misplaced)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 1, "misplaced PLACEHOLDER_PHASE8 is an error\nstdout=%r" % out)
        self.assertIn("LINT placeholder_misuse:", out)
        self.assertIn("gly.start", out)

        # Fresh copy for the second sub-case (any other PLACEHOLDER*).
        self.setUp()
        def mutate_other(data):
            data["nodes"]["gly.start"]["claim_ids"].append("PLACEHOLDER_PHASE9")
        self._mutate_story("glycolysis.json", mutate_other)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 1, "any other PLACEHOLDER* is an error\nstdout=%r" % out)
        self.assertIn("LINT placeholder_misuse:", out)
        self.assertIn("PLACEHOLDER_PHASE9", out)

    def test_pool_empty(self):
        """Rule 10a: empty the GLOBAL bad_ending_pool -> empty_bad_ending_pool
        (the rpg validate_edits_table parity rule; a per-enzyme empty pool
        would be legal fallback semantics -- only the GLOBAL pool is an
        error)."""
        edits = self._copy_support(EDITS_PATH, "edits.json")

        def mutate(data):
            data["bad_ending_pool"] = []
        path = os.path.join(self.tmp, "edits.json")
        with open(path, "r") as fh:
            data = json.load(fh)
        mutate(data)
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
        code, out = _run_lint(self.story_dir, edits=edits)
        self.assertEqual(code, 1, "empty global pool is an error\nstdout=%r" % out)
        self.assertIn("LINT empty_bad_ending_pool:", out)

    def test_pool_not_ending(self):
        """Rule 10b: point the global pool at an existing NON-ending node ->
        pool_node_not_ending."""
        edits = self._copy_support(EDITS_PATH, "edits.json")
        path = os.path.join(self.tmp, "edits.json")
        with open(path, "r") as fh:
            data = json.load(fh)
        data["bad_ending_pool"] = ["gly.start"]
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
        code, out = _run_lint(self.story_dir, edits=edits)
        self.assertEqual(
            code, 1, "non-ending pool member is an error\nstdout=%r" % out)
        self.assertIn("LINT pool_node_not_ending:", out)
        self.assertIn("gly.start", out)

    def test_dangling_pool(self):
        """Rule 10c: point the global pool at a missing node ->
        dangling_pool_node."""
        edits = self._copy_support(EDITS_PATH, "edits.json")
        path = os.path.join(self.tmp, "edits.json")
        with open(path, "r") as fh:
            data = json.load(fh)
        data["bad_ending_pool"] = ["bad.lint_missing"]
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
        code, out = _run_lint(self.story_dir, edits=edits)
        self.assertEqual(
            code, 1, "dangling pool node is an error\nstdout=%r" % out)
        self.assertIn("LINT dangling_pool_node:", out)
        self.assertIn("bad.lint_missing", out)

    def test_signature_duplicate(self):
        """Rule 11a: duplicate a signature within one edits.json bucket ->
        duplicate_signature (json.dumps sort_keys dedup semantics, exactly
        rpg/edit_router.validate_edits_table)."""
        edits = self._copy_support(EDITS_PATH, "edits.json")
        path = os.path.join(self.tmp, "edits.json")
        with open(path, "r") as fh:
            data = json.load(fh)
        entry = data["enzymes"]["gly.pfk"]["edits"][0]
        data["enzymes"]["gly.pfk"]["edits"].append(json.loads(json.dumps(entry)))
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
        code, out = _run_lint(self.story_dir, edits=edits)
        self.assertEqual(
            code, 1, "duplicate signature is an error\nstdout=%r" % out)
        self.assertIn("LINT duplicate_signature:", out)
        self.assertIn("gly.pfk", out)

    def test_branch_dangling(self):
        """Rule 11b: point an edit entry's branch_node at a missing node ->
        dangling_edit_branch."""
        edits = self._copy_support(EDITS_PATH, "edits.json")
        path = os.path.join(self.tmp, "edits.json")
        with open(path, "r") as fh:
            data = json.load(fh)
        data["enzymes"]["gly.pfk"]["edits"][0]["branch_node"] = "gly.lint_missing"
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
        code, out = _run_lint(self.story_dir, edits=edits)
        self.assertEqual(
            code, 1, "dangling branch_node is an error\nstdout=%r" % out)
        self.assertIn("LINT dangling_edit_branch:", out)
        self.assertIn("gly.lint_missing", out)

    def test_weight_outside_shuffle(self):
        """Rule 12: add a weight to a non-shuffle choice -> weight_outside_shuffle
        (tca.shuffle is the graph's ONLY weighted node --
        tests/test_glucose_content.py:539)."""
        def mutate(data):
            data["nodes"]["gly.start"]["choices"][0]["weight"] = 0.5
        self._mutate_story("glycolysis.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 1, "weight outside tca.shuffle is an error\nstdout=%r" % out)
        self.assertIn("LINT weight_outside_shuffle:", out)
        self.assertIn("gly.start", out)

    def test_cond_attribute_form(self):
        """Rule 13: write a cond in the broken dict-ATTRIBUTE form ->
        cond_attribute_form (the dict-method form flags.get(...) is
        mandatory -- tests/test_glucose_reachability.py:716; the attribute
        form raises AttributeError at runtime -> choice hidden -> stuck)."""
        def mutate(data):
            for c in data["nodes"]["tca.shuffle"]["choices"]:
                if c.get("cond") is not None:
                    c["cond"] = "flags.host_o2_low"
        self._mutate_story("tca.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 1, "attribute-form cond is an error\nstdout=%r" % out)
        self.assertIn("LINT cond_attribute_form:", out)
        self.assertIn("tca.shuffle", out)

    def test_cast_without_bucket(self):
        """Rule 14a: add a cast entry with no edits.json bucket ->
        coverage_uncovered (the check_edit_coverage / scan_edit_coverage
        parity rule)."""
        cast = self._copy_support(CAST_PATH, "cast.json")
        path = os.path.join(self.tmp, "cast.json")
        with open(path, "r") as fh:
            data = json.load(fh)
        data["enzymes"].append({
            "id": "lint.new_enzyme", "label": "Lint probe enzyme",
            "source": "download", "pdb_id": "000L",
            "character": "glucose", "claim_id": "LINT-FAKE-CLAIM-01",
        })
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
        code, out = _run_lint(self.story_dir, cast=cast)
        self.assertEqual(
            code, 1, "cast entry without an edits bucket is an error\n"
            "stdout=%r" % out)
        self.assertIn("LINT coverage_uncovered:", out)
        self.assertIn("lint.new_enzyme", out)

    def test_relationship_pin(self):
        """Rule 14b: break the shared-manifest relationship pin -- add an
        edit:enzyme:<id> tag carrier whose <id> has NO edits.json bucket
        (tags - {tca.citrate_synthase} must == the edits.json key set;
        tests/test_glucose_content.py:404)."""
        def mutate(data):
            data["nodes"]["tca.entry"]["tags"].append(
                "edit:enzyme:lint.new_enzyme")
        self._mutate_story("tca.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 1, "broken cast/edits/tags relationship is an error\n"
            "stdout=%r" % out)
        self.assertIn("LINT relationship_pin:", out)
        self.assertIn("lint.new_enzyme", out)

    def test_start_node_pdb_load(self):
        """Rule 15: add a pdb: load to intro.preface's on_enter ->
        start_node_pdb_load (start nodes use bundled placeholders ONLY --
        no network fetch at game start; tests/test_glucose_reachability.py
        :868-885)."""
        def mutate(data):
            data["nodes"]["intro.preface"]["on_enter"].append(
                {"op": "load", "target": "pdb:1ACO",
                 "args": {"object": "lint_probe"}})
        self._mutate_story("intro.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 1, "pdb: load on a start node is an error\nstdout=%r" % out)
        self.assertIn("LINT start_node_pdb_load:", out)
        self.assertIn("intro.preface", out)

    def test_unknown_op(self):
        """Rule 16a: add an on_enter op outside the frozen molops
        vocabulary -> unknown_op (a stray op raises NotImplementedError at
        dispatch -- fails loudly by design)."""
        def mutate(data):
            data["nodes"]["gly.start"]["on_enter"].append(
                {"op": "teleport", "target": "nowhere"})
        self._mutate_story("glycolysis.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(code, 1, "unknown op is an error\nstdout=%r" % out)
        self.assertIn("LINT unknown_op:", out)
        self.assertIn("teleport", out)

    def test_set_view_is_notice_not_error(self):
        """Rule 16b: a set_view op is a NOTICE, never an error (the
        scene_capture Phase-10 precedent: accepted but visibly flagged) --
        so the run stays exit 0."""
        def mutate(data):
            data["nodes"]["gly.start"]["on_enter"].append(
                {"op": "set_view", "args": {"view": [0.5] * 18}})
        self._mutate_story("glycolysis.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 0, "set_view is flagged as a NOTICE, not an error\n"
            "stdout=%r" % out)
        self.assertIn("LINT NOTICE set_view_phase10:", out)
        self.assertIn("Phase 10", out)

    def test_count_shift_notice(self):
        """Rule 17: a well-formed extra node+edge (everything else stays
        green) must NOT be a hard error -- exit 0 BUT a count_shift NOTICE
        reporting old->new and naming the pinned tests + viewer constants
        as the same-commit update obligations (RESEARCH-SAFETY key finding
        1: pinned-count movement is an explicit acknowledgment event)."""
        def mutate(data):
            data["nodes"]["lint.extra_node"] = {
                "text_dramatic": "A well-formed extra node seeded by the lint test.",
                "text_teaching": "A well-formed extra node seeded by the lint test.",
                "claim_ids": [],
                "tags": ["stage:intro"],
                "on_enter": [{"op": "hide_all"}],
                "choices": [
                    {"label": "Continue", "goto": "intro.select"},
                    {"label": "Observe", "goto": "intro.select",
                     "tags": ["mc:observe"]},
                ],
            }
            data["nodes"]["intro.preface"]["choices"][0]["goto"] = "lint.extra_node"
        self._mutate_story("intro.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 0,
            "a well-formed topology addition is exit 0 (the count_shift "
            "acknowledgment path, never a silent pass or a hard error)\n"
            "stdout=%r" % out)
        self.assertIn("LINT NOTICE count_shift:", out)
        self.assertIn("nodes 57 -> 58", out)
        # The exact same-commit update obligations (the pinned trio + the
        # viewer's pinned constants) must be named in the notice.
        self.assertIn("test_manifest_loads_all_57_nodes", out)
        self.assertIn("test_reachability_green_all_four_tiers", out)
        self.assertIn("test_15_edit_allowed_nodes", out)
        self.assertIn("EXPECTED_NODES", out)
        self.assertIn("EXPECTED_TIER_COUNTS", out)
        self.assertIn("EXPECTED_EDIT_ALLOWED", out)
        self.assertIn("LINT: 0 errors,", out)


class TestExitCodeContract(_BundleCopyTestCase):
    """Rule 18: the three-way exit contract (check_citations.py precedent):
    0 = clean (notices OK) / 1 = lint errors / 2 = schema-config error."""

    def test_clean_is_exit_0(self):
        code, out = _run_lint(self.story_dir)
        self.assertEqual(code, 0)
        self.assertIn("LINT: 0 errors,", out)

    def test_errors_are_exit_1(self):
        def mutate(data):
            data["nodes"]["intro.preface"]["choices"][1]["goto"] = "lint.missing"
        self._mutate_story("intro.json", mutate)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(code, 1)
        self.assertIn("LINT: 1 errors,", out)
        self.assertIn("(exit 1)", out)

    def test_unparseable_story_json_is_exit_2(self):
        """Unparseable story JSON -> schema-config exit 2 (distinct from
        exit 1 = genuine lint errors)."""
        broken = os.path.join(self.story_dir, "broken.json")
        with open(broken, "w") as fh:
            fh.write('{"nodes": {')  # truncated JSON
        manifest_path = os.path.join(self.story_dir, "manifest.json")
        with open(manifest_path, "r") as fh:
            manifest = json.load(fh)
        manifest["files"] = MANIFEST_FILES + ["broken.json"]
        with open(manifest_path, "w") as fh:
            json.dump(manifest, fh, indent=2)
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 2, "unparseable story JSON is a schema error\nstdout=%r" % out)

    def test_missing_story_manifest_is_exit_2(self):
        """A story dir with no manifest.json -> schema-config exit 2."""
        os.remove(os.path.join(self.story_dir, "manifest.json"))
        code, out = _run_lint(self.story_dir)
        self.assertEqual(
            code, 2, "missing manifest is a schema error\nstdout=%r" % out)

    def test_duplicate_registry_key_is_exit_2(self):
        """A registry JSON with a duplicate claim_id key -> schema-config
        exit 2 (the object_pairs_hook rejection, rpg/citations.py precedent:
        without it json.load silently last-wins and clobbers an approval)."""
        reg = self._copy_support(REGISTRY_PATH, "registry.json")
        path = os.path.join(self.tmp, "registry.json")
        entry = ('"LINT-DUP-KEY": {"claim": "dup probe", '
                 '"approval_status": "approved"}')
        with open(path, "a") as fh:  # splice a duplicate key before the close
            fh.seek(0)
            body = fh.read().rstrip().rstrip("}")
            fh.seek(0)
            fh.truncate()
            fh.write(body.rstrip().rstrip(",") + ",\n" + entry + ",\n" + entry + "\n}\n")
        code, out = _run_lint(self.story_dir, registry=path)
        self.assertEqual(
            code, 2, "duplicate registry key is a schema error\nstdout=%r" % out)


class TestLintLoader(unittest.TestCase):
    """The lint's OWN loader (mirroring the viewer's committed loaders):
    manifest + files -> ordered node dict + file_of map; duplicate ids
    raise. The tests load the REAL bundle through it."""

    def _load_module(self):
        # type: () -> object
        spec = importlib.util.spec_from_file_location(
            "story_editor_lint_under_test", LINT_SCRIPT)
        self.assertIsNotNone(
            spec, "tools/story_editor_lint.py must exist to be loadable")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_loader_loads_real_bundle_ordered(self):
        """load_bundle on the REAL data returns the merged 57-node graph in
        manifest file order, with the file_of map covering all 7 files and
        intro.preface (the manifest start) first."""
        mod = self._load_module()
        bundle = mod.load_bundle(STORY_DIR)
        self.assertEqual(len(bundle.nodes), 57)
        self.assertEqual(bundle.start, "intro.preface")
        first_id = list(bundle.nodes.keys())[0]
        self.assertEqual(first_id, "intro.preface")
        self.assertEqual(
            set(bundle.file_of.values()), set(MANIFEST_FILES),
            "the file_of map must attribute every node to one of the 7 "
            "manifest files")
        self.assertEqual(bundle.file_of["intro.preface"], "intro.json")
        self.assertEqual(bundle.file_of["end.true"], "etc_atp.json")
        self.assertEqual(bundle.file_of["edit.prompt"], "bad_endings.json")

    def test_loader_duplicate_id_raises(self):
        """A duplicate node id across files raises ValueError (mirrors
        StoryGraph.load / the viewer's load check) -- the CLI maps it to
        the schema-config exit 2."""
        mod = self._load_module()
        tmp = tempfile.mkdtemp(prefix="lint_loader_dup_")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        dest = os.path.join(tmp, "story")
        shutil.copytree(STORY_DIR, dest)
        path = os.path.join(dest, "glycolysis.json")
        with open(path, "r") as fh:
            data = json.load(fh)
        # Re-define intro.preface (already in intro.json) -> duplicate id.
        data["nodes"]["intro.preface"] = {
            "text_dramatic": "dup", "text_teaching": "dup",
            "claim_ids": [], "tags": [], "on_enter": [], "choices": [],
        }
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)
        self.assertRaises(ValueError, mod.load_bundle, dest)

    def test_module_imports_pure_no_pymol(self):
        """The lint stays in the pure-Python tier: importing it must NOT
        import pymol/PyQt5 (it runs in WSL python3.6; only rpg.* validators
        are imported -- the check_citations.py precedent)."""
        mod = self._load_module()
        self.assertNotIn("pymol", sys.modules)
        self.assertNotIn("PyQt5", sys.modules)
        self.assertTrue(hasattr(mod, "run_lint"),
                        "the lint exposes a run_lint entry point")


if __name__ == "__main__":
    unittest.main()
