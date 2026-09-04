"""Structural edits/cast/pool test battery for the Phase 7.1 editor Data tab
(07.1-14 Task 2).

Covers (over tools/story_editor_assets/50_editscast.js and the emitted page):
- the Data tab is REGISTERED per the 07.1-04 convention:
  EDITOR.view("data", ...) + EDITOR.init(...) present in the asset and
  inlined into the emitted story_editor.html (test_registered,
  test_emitted_page_inlines_editscast_asset)
- SIGNATURE NORMALIZATION is implemented and mirrored from the runtime:
  the trim+lowercase chain on the target (the live normalize preview),
  args values stringified, and the exact-dict-equality duplicate detection
  cited to rpg/edit_router.py:122-149 + rpg/story/model.py:112-126
  (test_signature_normalize)
- POOL RULES: the global bad_ending_pool is never empty (the length guard
  + the empty_bad_ending_pool refusal) while a per-enzyme override may be
  empty (the LEGAL FALLBACK path, rpg/edit_router.py:193-199) -- both code
  paths present (test_pool_rules)
- COVERAGE GUARDS: deleting an edits bucket REFUSES while cast.json still
  lists the id; the cast-add flow surfaces the three B7 requirements
  (bucket >=1 entry / edit:enzyme: tag / claim approved) as live checks
  (test_coverage_guards)
- the RELATIONSHIP PIN is rendered live with set-diff offender chips:
  cast(N) ⊆ edits(M) == tags(K) − {tca.citrate_synthase}
  (test_relationship_pin_display)
- the M5 posture is pinned: the known-wrong explanatory panel exists and
  creating a bad-ending-routing entry REQUIRES the explicit confirmation
  checkbox (test_m5_flag)
- MUTATION SCOPE: every EDITOR.apply names exactly "edits.json" or
  "cast.json" and no node/choice mutator of the state layer appears
  anywhere -- no story-file mutation from this asset
  (test_only_edits_cast_dirty)
- ES5 discipline for the asset (test_es5_discipline)

Python 3.6 stdlib only (unittest/os/re/json/subprocess/tempfile/shutil).
NO pytest (not installed). NO f-strings (.format() / % per repo
convention). NO pymol/PyQt5 imports. The battery greps only THIS plan's
asset, so it stays robust while the parallel Wave-4b agents (43_onenter.js,
07.1-16) are in flight. The committed story_editor.html regeneration is
DEFERRED while a sibling asset is untracked (wave race rule, the
07.1-05/06 precedent) -- the emitted-page class therefore generates its
own copy via --output and never reads the repo-root artifact.
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
ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "50_editscast.js")
EDITS_PATH = os.path.join(REPO_ROOT, "rpg", "data", "edits.json")
CAST_PATH = os.path.join(REPO_ROOT, "rpg", "data", "cast.json")
BAD_ENDINGS_PATH = os.path.join(
    REPO_ROOT, "data", "story_glucose", "bad_endings.json")

# The state layer's node/choice mutation API -- NONE of these may appear
# anywhere in this asset (it mutates ONLY the two top-level registries via
# EDITOR.apply; nodes are read-only inputs for the dropdowns/tag scans).
FORBIDDEN_MUTATORS = [
    "EDITOR.nodeSet", "EDITOR.nodeAdd", "EDITOR.nodeDelete",
    "EDITOR.choiceAdd", "EDITOR.choiceUpdate", "EDITOR.choiceDelete",
]

# The pinned relationship formula (the header comment carries it literally;
# the live render builds it from counts with the same unicode operators).
RELATIONSHIP_FORMULA = (
    "cast(N) \u2286 edits(M) == tags(K) \u2212 {tca.citrate_synthase}")

# The four structural bad endings that carry the known-wrong tags today.
KNOWN_WRONG_BAD_ENDINGS = [
    "bad.active_site_destroyed",
    "bad.substrate_channel_blocked",
    "bad.cofactor_lost",
    "bad.critical_residue_break",
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


class TestEditscastAssetStructure(unittest.TestCase):
    """Structural checks over the Data-tab asset + ONE emitted page."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_editscast_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.asset = _read(ASSET) if os.path.isfile(ASSET) else ""
        cls.edits = {}
        if os.path.isfile(EDITS_PATH):
            with open(EDITS_PATH, "r", encoding="utf-8") as fh:
                cls.edits = json.load(fh)
        cls.cast = {}
        if os.path.isfile(CAST_PATH):
            with open(CAST_PATH, "r", encoding="utf-8") as fh:
                cls.cast = json.load(fh)
        cls.bad_endings = {}
        if os.path.isfile(BAD_ENDINGS_PATH):
            with open(BAD_ENDINGS_PATH, "r", encoding="utf-8") as fh:
                cls.bad_endings = json.load(fh)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _editscast_block(self):
        # type: () -> str
        """Extract the inlined 50_editscast.js <script> block."""
        marker = "/* asset: 50_editscast.js"
        m_start = self.html.find(marker)
        self.assertGreaterEqual(
            m_start, 0,
            "50_editscast.js asset marker missing from emitted HTML")
        block_open = self.html.rfind("<script>", 0, m_start)
        self.assertGreaterEqual(
            block_open, 0, "editscast asset block has no opening <script>")
        block_close = self.html.find("</script>", m_start)
        self.assertGreaterEqual(
            block_close, 0, "editscast asset block is unterminated")
        return self.html[block_open:block_close]

    # ------------------------------------------------------------------
    # 1. Registration (the 07.1-04 contract every later asset follows)
    # ------------------------------------------------------------------

    def test_registered(self):
        """EDITOR.view is called with "data" and a named render function;
        the DOM work registers via EDITOR.init; the asset is a real IIFE,
        not a stub; the must-have requires >= 180 lines of real asset."""
        self.assertIn('EDITOR.view("data"', self.asset,
                      "the Data tab must be registered as "
                      'EDITOR.view("data", ...)')
        self.assertIn("EDITOR.init(initEditsCast)", self.asset,
                      "the Data tab DOM work must register via EDITOR.init")
        self.assertIn("(function () {", self.asset,
                      "asset must be a single IIFE (classic-script style)")
        self.assertIn('"use strict";', self.asset,
                      "asset must use strict mode like the sibling assets")
        self.assertGreaterEqual(
            len(self.asset.splitlines()), 180,
            "the plan's must-have requires >= 180 lines of real asset")
        # The three manifest editors are all present (B4 + B7 + B10).
        for needle in ("renderEditsSection", "renderKnownWrongSection",
                       "renderCastSection", "renderPoolSection"):
            self.assertIn(needle, self.asset,
                          "%s missing (one of the three editors)" % needle)

    # ------------------------------------------------------------------
    # 2. Signature normalization (the runtime-matching semantics)
    # ------------------------------------------------------------------

    def test_signature_normalize(self):
        """The normalize preview (strip + lowercase) and the normalized-dict
        signature equality are implemented near the signature editor: the
        trim chain feeds a .toLowerCase(), args values are stringified, and
        the duplicate detection cites the router semantics
        (rpg/edit_router.py:122-149 + rpg/story/model.py:112-126)."""
        # The trim + lowercase chain (the live normalize preview).
        self.assertIn('replace(/^\\s+|\\s+$/g, "")', self.asset,
                      "the trim chain is missing from the normalize preview")
        m = self.asset.find("function normalizeTargetText(")
        self.assertGreaterEqual(m, 0, "normalizeTargetText is missing")
        body = self.asset[m:self.asset.find("}", m) + 1]
        self.assertIn(".toLowerCase()", body,
                      "the normalize preview must lowercase the stripped "
                      "target (EditIntent.signature semantics)")
        # The normalize preview label renders live + the comment exists.
        self.assertIn("normalize preview", self.asset)
        self.assertIn("normalizeSignature(", self.asset)
        self.assertIn("function normVal(", self.asset)
        self.assertIn("stableStringify(", self.asset)
        # Args values are STRINGIFIED (scalars trimmed, containers
        # stable-stringified) -- the _norm_val mirror.
        nv = self.asset[self.asset.find("function normVal("):]
        nv = nv[:nv.find("}", nv.find("return trimText(")) + 1]
        self.assertIn("stableStringify(v)", nv,
                      "nested args values must be stable-stringified "
                      "(model.py:154-161 _norm_val)")
        self.assertIn("return trimText(v)", nv,
                      "scalar args values must be trimmed")
        # The duplicate detection + its citation.
        self.assertIn("function duplicateOf(", self.asset)
        self.assertIn("duplicate_signature", self.asset)
        self.assertIn("rpg/edit_router.py:122-149", self.asset)
        self.assertIn("rpg/story/model.py:112-126", self.asset)
        # The duplicate check REFUSES the add/update (never a silent pass).
        self.assertIn("Refused: duplicate_signature", self.asset)
        # The emitted page carries the same handling.
        block = self._editscast_block()
        self.assertIn("normalize preview", block)
        self.assertIn(".toLowerCase()", block)
        self.assertIn("duplicate_signature", block)

    # ------------------------------------------------------------------
    # 3. Pool rules (B10: global never empty; per-enzyme empty = legal)
    # ------------------------------------------------------------------

    def test_pool_rules(self):
        """GLOBAL pool: a length guard REFUSES the last removal (the
        empty_bad_ending_pool error + the runtime EditRoutingError).
        PER-ENZYME: an empty override is the LEGAL FALLBACK -- INFO, never
        an error -- and both code paths (empty-override create + override
        key removal) exist. src: rpg/edit_router.py:172-235 + :193-199."""
        # The global-pool guard: both the code and the refusal message.
        self.assertIn("pool.length <= 1", self.asset,
                      "the global-pool length guard is missing")
        self.assertIn("the GLOBAL bad_ending_pool is never empty",
                      self.asset)
        self.assertIn("empty_bad_ending_pool", self.asset)
        self.assertIn("EditRoutingError", self.asset,
                      "the runtime failure mode must be named")
        self.assertIn("rpg/edit_router.py:172-235", self.asset)
        # The per-enzyme legal-fallback path (BOTH branches present).
        self.assertIn("LEGAL FALLBACK", self.asset,
                      "the empty-override legal-fallback label is missing")
        self.assertIn("rpg/edit_router.py:193-199", self.asset)
        self.assertIn("function editsPerPoolCreate(", self.asset,
                      "creating an empty override must be supported")
        self.assertIn("function editsPerPoolRemoveOverride(",
                      self.asset,
                      "removing the override key (fall back) must be "
                      "supported")
        self.assertIn("Create empty override", self.asset)
        self.assertIn("Remove override (fall back to global)", self.asset)
        # The runtime pool is distinguished from edit.prompt's 13
        # structural choices (never player-facing).
        self.assertIn("13 structural", self.asset)
        self.assertIn("RUNTIME pool", self.asset)
        # The emitted page carries the same rules.
        block = self._editscast_block()
        self.assertIn("pool.length <= 1", block)
        self.assertIn("empty_bad_ending_pool", block)
        self.assertIn("LEGAL FALLBACK", block)

    # ------------------------------------------------------------------
    # 4. Coverage guards (B4 delete-refusal + B7 add requirements)
    # ------------------------------------------------------------------

    def test_coverage_guards(self):
        """Deleting an edits bucket REFUSES while cast.json still lists the
        id (the coverage gate). The cast-add flow surfaces the three B7
        requirements as live checks: an edits bucket with >=1 entry, the
        edit:enzyme: tag in the graph (or the explicit acknowledge
        checkbox), and claim_id in the registry AND approved."""
        # Bucket-delete refusal while cast-listed.
        self.assertIn("cast.json still lists", self.asset)
        self.assertIn("rpg/edit_router.py:238-255", self.asset)
        self.assertIn("coverage_uncovered", self.asset)
        self.assertIn("function castListsId(", self.asset)
        # Cast-add: the three live requirement checks.
        self.assertIn("edits bucket with >=1", self.asset)
        self.assertIn("edit:enzyme:", self.asset)
        self.assertIn("claim_id \u2208 registry", self.asset)
        self.assertIn('=== "approved"', self.asset,
                      "the strict approval predicate is missing "
                      "(rpg/citations.py:100-109)")
        self.assertIn("rpg/citations.py:100-109", self.asset)
        # The explicit acknowledge checkbox for the relationship-test
        # update (the tag requirement's sanctioned alternative). The asset
        # builds HTML inside JS strings, so attribute values carry \"
        # escapes in the source (the same form is inlined into the page).
        self.assertIn('data-castnew=\\"ackTag\\"', self.asset)
        self.assertIn("ackTag", self.asset)
        self.assertIn("ACKNOWLEDGE", self.asset)
        # The refusals are explicit, never silent.
        self.assertIn("Refused: no edits.json bucket", self.asset)
        self.assertIn("Refused: no node carries edit:enzyme:", self.asset)
        self.assertIn("an unapproved", self.asset)
        self.assertIn("never lands silently", self.asset)
        # The cast-delete refusal while an edits bucket exists.
        self.assertIn("Refused: an edits.json bucket still exists",
                      self.asset)
        # The emitted page carries the same guards.
        block = self._editscast_block()
        self.assertIn("cast.json still lists", block)
        self.assertIn('=== "approved"', block)
        self.assertIn('data-castnew=\\"ackTag\\"', block)

    # ------------------------------------------------------------------
    # 5. The relationship pin display (live formula + offender chips)
    # ------------------------------------------------------------------

    def test_relationship_pin_display(self):
        """The pinned invariant is rendered live with set-diff chips naming
        offenders. src: tests/test_glucose_content.py:404-449
        (TestManifestRelationships)."""
        # The formula: literal in the header comment + the live build.
        self.assertIn(RELATIONSHIP_FORMULA, self.asset,
                      "the relationship formula string must appear "
                      "(header comment + live render)")
        self.assertIn("\\u2286", self.asset,
                      "the subset operator must be in the live build")
        self.assertIn("\\u2212", self.asset,
                      "the minus operator must be in the live build")
        self.assertIn('STRUCTURAL_TAG_ENZYME = "tca.citrate_synthase"',
                      self.asset)
        self.assertIn("tests/test_glucose_content.py:404-449", self.asset)
        self.assertIn("TestManifestRelationships", self.asset)
        # Set-diff chips naming offenders (each direction of the pin).
        self.assertIn("cast id with NO edits bucket", self.asset)
        self.assertIn("bucket with NO tag carrier", self.asset)
        self.assertIn("tag value with NO bucket", self.asset)
        self.assertIn("bucket with no cast entry (legal)", self.asset)
        self.assertIn("ec-chip-bad", self.asset)
        self.assertIn("function relationshipReport(", self.asset)
        # The live counts feed the formula.
        self.assertIn("cast(", self.asset)
        self.assertIn('\\u2286 edits("', self.asset)
        self.assertIn('") == tags("', self.asset)
        # The emitted page carries the pin.
        block = self._editscast_block()
        self.assertIn(RELATIONSHIP_FORMULA, block)
        self.assertIn("cast id with NO edits bucket", block)

    # ------------------------------------------------------------------
    # 6. The M5 flag (known-wrong posture + confirmation gate)
    # ------------------------------------------------------------------

    def test_m5_flag(self):
        """The M5/known-wrong explanatory panel exists; creating a
        bad-ending-routing entry REQUIRES the explicit confirmation
        checkbox (the save refuses while unticked). The M5 decision:
        STATE 07-01 outcome 4."""
        # The explanatory panel + the M5 citation.
        self.assertGreaterEqual(self.asset.count("M5"), 5,
                                "the M5 reference is too thin")
        self.assertIn("STATE 07-01 outcome 4", self.asset)
        self.assertIn("known-wrong", self.asset)
        self.assertIn("NO known-wrong 1b entries", self.asset)
        # The four structural bad endings are named.
        for nid in KNOWN_WRONG_BAD_ENDINGS:
            self.assertIn(nid, self.asset,
                          "known-wrong candidate ending %s must be named"
                          % nid)
        # The live count of ending-routing entries (the M5 posture holds
        # at zero today -- the panel proves it live).
        self.assertIn("0 entries route", self.asset)
        # The confirmation gate: checkbox + refusal while unticked.
        self.assertIn('data-form-field=\\"m5\\"', self.asset)
        self.assertIn("Tick the M5", self.asset,
                      "the refusal must demand the M5 confirmation")
        self.assertIn("is an ENDING", self.asset)
        # The allowed-fix vs known-wrong difference is labeled.
        self.assertIn("allowed-fix routing", self.asset)
        self.assertIn("known-wrong routing", self.asset)
        # The emitted page carries the gate.
        block = self._editscast_block()
        self.assertIn('data-form-field=\\"m5\\"', block)
        self.assertIn("STATE 07-01 outcome 4", block)

    # ------------------------------------------------------------------
    # 7. Mutation scope: edits.json / cast.json ONLY
    # ------------------------------------------------------------------

    def test_only_edits_cast_dirty(self):
        """Every EDITOR.apply names exactly "edits.json" or "cast.json"; no
        node/choice mutator of the state layer appears anywhere in the
        asset (no story-file mutation from this asset -- nodes are
        read-only inputs for the dropdowns / tag scans)."""
        for token in FORBIDDEN_MUTATORS:
            self.assertNotIn(
                token, self.asset,
                "mutation-scope violation: %r found in 50_editscast.js"
                % token)
        # Every EDITOR.apply call carries one of the two literals.
        apply_calls = self.asset.count("EDITOR.apply({")
        edits_lits = self.asset.count('files: ["edits.json"]')
        cast_lits = self.asset.count('files: ["cast.json"]')
        self.assertGreater(apply_calls, 0, "no mutations wired at all")
        self.assertEqual(
            apply_calls, edits_lits + cast_lits,
            "every EDITOR.apply must name exactly edits.json or "
            "cast.json (found %d applies vs %d+%d literals)"
            % (apply_calls, edits_lits, cast_lits))
        # No OTHER files array form exists anywhere.
        for m in re.finditer(r"files:\s*\[[^\]]*\]", self.asset):
            lit = m.group(0)
            self.assertIn(
                lit, ('files: ["edits.json"]', 'files: ["cast.json"]'),
                "unexpected mutation target in %r" % lit)
        # The dirty targets are the two registries (constants + doc).
        self.assertIn('var EDITS_FNAME = "edits.json";', self.asset)
        self.assertIn('var CAST_FNAME = "cast.json";', self.asset)
        self.assertIn("NO story-file mutation", self.asset)
        # The registry-dirty honesty extension is documented + scoped.
        self.assertIn("REGISTRY DIRTY HONESTY", self.asset)
        self.assertIn("captureRegistryBaselines", self.asset)
        # The emitted block obeys the same scope.
        block = self._editscast_block()
        for token in FORBIDDEN_MUTATORS:
            self.assertNotIn(token, block,
                             "emitted block contains mutator %r" % token)
        block_calls = block.count("EDITOR.apply({")
        self.assertEqual(
            block_calls,
            block.count('files: ["edits.json"]') +
            block.count('files: ["cast.json"]'),
            "emitted block: every EDITOR.apply must name edits.json or "
            "cast.json")

    # ------------------------------------------------------------------
    # 8. ES5 discipline (per-asset pin; page-wide pin lives in the state
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

    # ------------------------------------------------------------------
    # 9. Data reality (the editors' display anchors against the live data)
    # ------------------------------------------------------------------

    def test_data_reality_relationships(self):
        """The live data still satisfies the invariants this tab renders:
        cast ids subset-of edits ids, every global-pool member an existing
        ending, and zero ending-routing (known-wrong) entries -- so the
        displayed '0 entries route to an ending' posture matches reality
        (the full equality pins live in tests/test_glucose_content.py)."""
        edit_ids = set(self.edits.get("enzymes", {}).keys())
        cast_ids = set(e.get("id") for e in self.cast.get("enzymes", []))
        self.assertTrue(
            cast_ids.issubset(edit_ids),
            "data reality drifted: cast ids not a subset of edits ids: %s"
            % sorted(cast_ids - edit_ids))
        pool = self.edits.get("bad_ending_pool", [])
        self.assertGreaterEqual(len(pool), 1,
                                "data reality drifted: empty global pool")
        for nid in pool:
            node = self.bad_endings.get("nodes", {}).get(nid)
            self.assertIsNotNone(
                node, "data reality drifted: pool member %r not in the "
                "graph" % nid)
            self.assertIn("is_ending", node,
                          "data reality drifted: pool member %r is not an "
                          "ending" % nid)
        # Zero known-wrong entries today (the M5 posture the panel shows).
        for eid, bucket in self.edits.get("enzymes", {}).items():
            for entry in bucket.get("edits", []):
                branch = entry.get("branch_node")
                self.assertNotIn(
                    branch, KNOWN_WRONG_BAD_ENDINGS,
                    "data reality drifted: %s routes a known-wrong edit "
                    "to %r -- the M5 panel's zero-count is stale" % (eid,
                                                                     branch))


class TestEditscastEmittedPage(unittest.TestCase):
    """The plan's Task-1 verify, pinned mechanically: the emitted page
    contains the Data-tab asset with every string the verify step names."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_editscast_page_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_emitted_page_inlines_editscast_asset(self):
        """The emitted HTML contains the editscast asset block with every
        string the plan's verify step names, ordered after the form asset
        and before the shell bootstrap."""
        html = self.html
        self.assertTrue(html, "generator produced no output file")
        marker = "/* asset: 50_editscast.js"
        m50 = html.find(marker)
        self.assertGreaterEqual(m50, 0,
                                "50_editscast.js not inlined into the page")
        # Plan verify strings.
        for needle in ("bad_ending_pool", "branch_node", "new_res",
                       "normalize preview", "M5", "duplicate_signature",
                       RELATIONSHIP_FORMULA,
                       "STATE 07-01 outcome 4"):
            m = html.find(needle, m50)
            self.assertGreaterEqual(
                m, 0,
                "verify string %r missing from the emitted page after the "
                "editscast asset marker" % needle)
        # Ordering: after 40_form.js (asset order contract), before
        # 60_trace.js and before the shell bootstrap (the last script
        # block). 42_choices.js / 43_onenter.js are sibling assets -- only
        # asserted when present so this battery stays robust while the
        # parallel Wave-4b agents are in flight.
        m40 = html.find("/* asset: 40_form.js")
        self.assertGreater(m40, 0, "40_form.js marker missing")
        self.assertGreater(m50, m40,
                           "50_editscast.js must inline after 40_form.js")
        m60 = html.find("/* asset: 60_trace.js")
        self.assertGreater(m60, 0, "60_trace.js marker missing")
        self.assertLess(m50, m60,
                        "50_editscast.js must inline before 60_trace.js")
        m42 = html.find("/* asset: 42_choices.js")
        if m42 >= 0:
            self.assertGreater(
                m50, m42,
                "50_editscast.js must inline after 42_choices.js")
        m43 = html.find("/* asset: 43_onenter.js")
        if m43 >= 0:
            self.assertGreater(
                m50, m43,
                "50_editscast.js must inline after 43_onenter.js")
        boot = html.rfind("DOMContentLoaded")
        self.assertLess(m50, boot,
                        "the editscast asset must precede the shell "
                        "bootstrap")

    def test_emitted_editscast_block_mutation_scope(self):
        """The mutation scope holds in the EMITTED block too."""
        html = self.html
        marker = "/* asset: 50_editscast.js"
        m_start = html.find(marker)
        block_open = html.rfind("<script>", 0, m_start)
        block_close = html.find("</script>", m_start)
        block = html[block_open:block_close]
        for token in FORBIDDEN_MUTATORS:
            self.assertNotIn(token, block,
                             "emitted block contains mutator %r" % token)
        self.assertEqual(
            block.count("EDITOR.apply({"),
            block.count('files: ["edits.json"]') +
            block.count('files: ["cast.json"]'),
            "emitted block: unexpected mutation target")


if __name__ == "__main__":
    unittest.main()
