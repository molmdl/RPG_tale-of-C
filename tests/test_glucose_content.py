"""Phase 7 cross-cutting content-invariant suite (Plan 07-16).

Turns the phase's release conditions -- "no fabricated science + no
placeholder residue" -- from a review promise into CI. Eight test groups
per the plan context + the 07-RESEARCH-content-mechanics.md section 10
test-strategy table, all against the REAL bundle (no fixtures):

1. Two-layer text non-empty on every player-facing glucose node
   (STORY-06). The ONLY exemption is ``edit.prompt`` -- a documented
   05.1-DESIGN structural stub (rows 55/138) that is never rendered (the
   controller intercepts ``edit.prompt`` and opens the EditDialog, 06-08).
   NOTE: ``fa.stub``/``alc.stub`` are NOT exempt -- plan 07-04 authored
   honest two-layer Phase-8 notice text on them, so they are ASSERTED
   non-empty here (stricter than the plan's original exemption list).
2. No "TBD" residue in any story text field (same single exemption:
   edit.prompt's text_dramatic IS the documented ``[STRUCTURAL STUB:...]``
   marker; verified the only TBD in the bundle).
3. Claim hygiene: no ``PLACEHOLDER_PHASE7*`` claim_ids anywhere;
   ``PLACEHOLDER_PHASE8`` allowed ONLY on fa.stub/alc.stub (the 07-01-
   sanctioned Phase-8 stubs); no other PLACEHOLDER* ids at all; every
   other referenced claim_id is APPROVED in data/citations.json
   (in-process registry cross-check).
4. Citation gate on the real bundle via subprocess (three-way exit
   contract). SANCTIONED FORM (orchestrator ground truth): the gate
   exits 1 with residual == EXACTLY the 2 documented MISSING lines
   (fa.stub + alc.stub -> PLACEHOLDER_PHASE8) and 0 UNAPPROVED -- the
   "residual-zero-except-documented-stubs" form. Registering
   PLACEHOLDER_PHASE8 as approved is FORBIDDEN (would fabricate
   approval); bare invocation exits 2 (the config-error branch).
5. Edit coverage: tools/check_edit_coverage.py exits 0 (subprocess) +
   ``scan_edit_coverage`` green + ``validate_edits_table`` CLEAN against
   the real 57-node graph.
6. Known-edit round-trip: every one of the 13 edits.json signatures,
   rebuilt as an EditIntent, routes via EditRouter to its recorded
   branch_node -- which must EXIST in the real graph (mock RNG; the
   route is deterministic for known entries).
7. Seeded determinism under design B (07-13): fixed seed -> documented
   shuffle fate. DOCUMENTED FATE (pinned here, engine level):
   seed 42 -> tca.co2_turn2 ("retained aboard"; first draw 0.6394 >
   the 0.5 cumulative threshold). The research section 10 example
   ("seed 42 -> co2_turn1") was an illustrative guess; reality is
   pinned instead. Different seeds vary: over 30 seeds both fates
   occur. The shuffle is the graph's ONLY weighted node (the host-O2
   RNG event from research section 7 was never implemented -- 07-01
   DC-B made pyr.branch an explicit player choice -- so the shuffle
   alone is the determinism surface).
8. Restoration-arc integration: the gly.pfk known signature routes to
   ``gly.pfk_restored`` whose on_enter carries the plan-12 shape
   [edit -> load pdb:4PFK -> align(super) -> show_as], asserted via the
   loaded StoryGraph AND a mock-sink engine dispatch.

Plus the shared-manifest relationship pin (orchestrator ground truth):
cast(12) subset-of edits(13) == distinct edit:enzyme tag values(14) minus
{tca.citrate_synthase} (CS is edit:structural with 0 natural variants, no
edits bucket by design; tca.akg_dh has an edits bucket but NO cast entry --
no approved OGDH cast PDB).

Pattern sources: tests/test_glucose_reachability.py (setUp/StoryGraph.load),
tests/test_citations.py (TestCheckCitationsExitCodes subprocess pattern),
tests/test_edit_router.py (EditIntent/EditRouter + mock sinks).

Python 3.6 stdlib ONLY (unittest/subprocess/os/sys/json). NO pytest (not
installed). subprocess uses stdout/stderr=PIPE + manual .decode() (NOT
capture_output/text -- both 3.7+). NO f-strings (.format() per repo
convention). NO pymol/PyQt5 (the AST gate scans tests/).
"""
import json
import os
import subprocess
import sys
import unittest

from rpg.story.graph import StoryGraph
from rpg.story.model import EditIntent
from rpg.rng import RngEngine
from rpg.engine import GameEngine
from rpg.citations import CitationRegistry
from rpg.edit_router import (
    EditsTable, EditRouter, validate_edits_table, scan_edit_coverage,
)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(HERE, "..")
STORY_DIR = os.path.join(REPO_ROOT, "data", "story_glucose")
REGISTRY_PATH = os.path.join(REPO_ROOT, "data", "citations.json")
EDITS_PATH = os.path.join(REPO_ROOT, "rpg", "data", "edits.json")
CAST_PATH = os.path.join(REPO_ROOT, "rpg", "data", "cast.json")
GATE_SCRIPT = os.path.join(REPO_ROOT, "tools", "check_citations.py")
COVERAGE_SCRIPT = os.path.join(REPO_ROOT, "tools", "check_edit_coverage.py")

# The 05.1-DESIGN-documented structural stub (rows 55/138): never rendered
# (the controller intercepts edit.prompt -> EditDialog, 06-08); its
# text_dramatic IS the "[STRUCTURAL STUB:...]" marker. The ONLY node in the
# bundle with empty/placeholder text.
DOCUMENTED_STUB_NODES = ("edit.prompt",)

# The 07-01-sanctioned Phase-8 stubs: the ONLY nodes allowed to reference
# PLACEHOLDER_PHASE8 (and the gate's ONLY sanctioned residual).
PHASE8_STUB_NODES = ("fa.stub", "alc.stub")

# The design-B documented fate (07-13): seed 42 -> the carbon is RETAINED
# aboard (first draw 0.6394... > the 0.5 cumulative threshold -> the second
# weighted choice, tca.co2_turn2). See module docstring point 7.
SHUFFLE_SEED = 42
SHUFFLE_EXPECTED_FATE = "tca.co2_turn2"
SHUFFLE_OTHER_FATE = "tca.co2_turn1"


def _load_graph():
    # type: () -> StoryGraph
    return StoryGraph.load(STORY_DIR)


def _load_edits():
    # type: () -> EditsTable
    return EditsTable.load(EDITS_PATH)


def _load_cast_ids():
    # type: () -> list
    with open(CAST_PATH, "r", encoding="utf-8") as fh:
        cast = json.load(fh)
    return [entry["id"] for entry in cast["enzymes"]]


class TestTwoLayerText(unittest.TestCase):
    """Groups 1+2: STORY-06 two-layer completion, machine-checked."""

    def setUp(self):
        self._graph = _load_graph()

    def test_two_layer_text_nonempty_on_all_player_facing_nodes(self):
        """Every node EXCEPT the documented edit.prompt structural stub has
        non-empty text_dramatic AND text_teaching (both after strip).
        fa.stub/alc.stub are asserted WITH the rest: plan 07-04 authored
        honest two-layer Phase-8 notice text on them (they are player-facing
        -- choosing them returns to character select), so they must stay
        authored. 56 asserted / 57 total."""
        empty = []
        for nid, node in self._graph.all_nodes().items():
            if nid in DOCUMENTED_STUB_NODES:
                continue
            with self.subTest(node=nid):
                for field in ("text_dramatic", "text_teaching"):
                    value = getattr(node, field)
                    if not isinstance(value, str) or not value.strip():
                        empty.append((nid, field))
        self.assertEqual(
            empty, [],
            "every player-facing node needs BOTH text layers non-empty "
            "(STORY-06 two-layer invariant; edit.prompt exempt as the "
            "documented structural stub); empty fields=%s" % empty)

    def test_no_tbd_residue_in_story_text(self):
        """No "TBD" substring in any story text field (text_dramatic,
        text_teaching) or choice label, EXCEPT edit.prompt's documented
        stub-marker text (the single TBD occurrence in the bundle)."""
        offenders = []
        for nid, node in self._graph.all_nodes().items():
            if nid in DOCUMENTED_STUB_NODES:
                continue
            for field in ("text_dramatic", "text_teaching"):
                value = getattr(node, field) or ""
                if "TBD" in value:
                    offenders.append((nid, field))
            for choice in node.choices:
                if "TBD" in (choice.label or ""):
                    offenders.append((nid, "choice.label:" + choice.label))
        self.assertEqual(
            offenders, [],
            "no TBD residue in story text (STORY-06 completion scan; "
            "edit.prompt's stub marker exempt); offenders=%s" % offenders)

    def test_edit_prompt_stub_marker_is_honest(self):
        """The single exemption is self-documenting: edit.prompt's
        text_dramatic carries the [STRUCTURAL STUB: marker explaining that
        the EditRouter owns real branching (05.1-DESIGN rows 55/138). If the
        marker is removed the stub must be authored like any other node and
        the two-layer/TBD exemptions above must be lifted with it."""
        node = self._graph.get_node("edit.prompt")
        self.assertIn(
            "[STRUCTURAL STUB:", node.text_dramatic or "",
            "edit.prompt's exemption from the two-layer/TBD scans holds "
            "only while its stub-marker text is present")


class TestClaimHygiene(unittest.TestCase):
    """Group 3: no placeholder residue; registry cross-check on real data."""

    def setUp(self):
        self._graph = _load_graph()
        self._registry = CitationRegistry.load(REGISTRY_PATH)

    def _iter_claims(self):
        # type: () -> list
        """Return [(node_id, claim_id)] for every claim reference in the
        bundle (walks the loaded graph's claim_ids lists)."""
        refs = []
        for nid, node in self._graph.all_nodes().items():
            for cid in (node.claim_ids or []):
                refs.append((nid, cid))
        return refs

    def test_no_placeholder_phase7_claim_ids_anywhere(self):
        """Zero PLACEHOLDER_PHASE7* claim_ids remain in any story node (the
        07-13 sweep completed the swap; this pins it)."""
        residue = [(nid, cid) for nid, cid in self._iter_claims()
                   if cid.startswith("PLACEHOLDER_PHASE7")]
        self.assertEqual(
            residue, [],
            "no PLACEHOLDER_PHASE7* claim_ids may remain; found %s" % residue)

    def test_placeholder_phase8_only_on_documented_stubs(self):
        """PLACEHOLDER_PHASE8 is allowed ONLY on fa.stub/alc.stub (the
        07-01-sanctioned Phase-8 stubs), and NOWHERE else; no other
        PLACEHOLDER* prefix exists at all (catches PHASE5/6 residue)."""
        offenders = []
        for nid, cid in self._iter_claims():
            if cid == "PLACEHOLDER_PHASE8":
                if nid not in PHASE8_STUB_NODES:
                    offenders.append((nid, cid))
            elif cid.startswith("PLACEHOLDER"):
                offenders.append((nid, cid))
        self.assertEqual(
            offenders, [],
            "PLACEHOLDER_PHASE8 is sanctioned only on %s; any other "
            "PLACEHOLDER* residue is a content gap; offenders=%s"
            % (PHASE8_STUB_NODES, offenders))
        # The sanctioned stubs are actually present (the residual the gate
        # reports is exactly these 2, no fewer).
        stub_refs = sorted(nid for nid, cid in self._iter_claims()
                           if cid == "PLACEHOLDER_PHASE8")
        self.assertEqual(
            stub_refs, sorted(PHASE8_STUB_NODES),
            "the 2 documented Phase-8 stubs reference PLACEHOLDER_PHASE8 "
            "(the gate's sanctioned residual); got %s" % stub_refs)

    def test_all_other_claims_approved_in_registry(self):
        """In-process registry cross-check (the subprocess gate's twin):
        every claim referenced OUTSIDE the Phase-8 stubs exists in
        data/citations.json AND is approved. PLACEHOLDER_PHASE8 must NOT be
        in the registry (registering it would fabricate approval -- the
        no-fabricated-science guard)."""
        unapproved = []
        for nid, cid in self._iter_claims():
            if nid in PHASE8_STUB_NODES:
                continue
            if not self._registry.is_approved(cid):
                unapproved.append((nid, cid, self._registry.status(cid)))
        self.assertEqual(
            unapproved, [],
            "every non-stub claim reference must be approved in the "
            "registry; offenders=%s" % unapproved)
        self.assertFalse(
            self._registry.contains("PLACEHOLDER_PHASE8"),
            "PLACEHOLDER_PHASE8 must NOT be a registry entry (registering "
            "it would fabricate approval of a Phase-8 placeholder)")


class TestCitationGateRealBundle(unittest.TestCase):
    """Group 4: the gate on the REAL bundle via subprocess (three-way exit
    contract). Sanctioned form: exit 1 with residual == EXACTLY the 2
    documented Phase-8 stub MISSING lines, 0 UNAPPROVED."""

    def _run_gate(self, extra_args):
        # type: (list) -> object
        """Run tools/check_citations.py with the given extra args. Uses
        stdout/stderr=PIPE + manual decode (3.6-safe; mirrors
        test_citations.py TestCheckCitationsExitCodes)."""
        return subprocess.run(
            [sys.executable, GATE_SCRIPT] + extra_args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def test_gate_residual_exactly_two_documented_stubs(self):
        """The real bundle's gate report is the residual-zero-except-
        documented-stubs form: exit 1, summary '2 missing + 0 unapproved',
        exactly 2 [MISSING] lines (fa.stub + alc.stub, both
        PLACEHOLDER_PHASE8), and ZERO [UNAPPROVED] lines. Any third MISSING
        line, any UNAPPROVED line, or a different summary means a REAL
        content gap (or a fabricated approval)."""
        r = self._run_gate(["--story", STORY_DIR, "--registry", REGISTRY_PATH])
        stdout = r.stdout.decode("utf-8")
        self.assertEqual(
            r.returncode, 1,
            "expected exit 1 (the sanctioned 2-stub residual)\nstdout=%r"
            % stdout)
        self.assertIn("CITATION GATE FAILED", stdout)
        self.assertIn("2 missing + 0 unapproved claim reference(s).", stdout)
        self.assertEqual(
            stdout.count("[MISSING]"), 2,
            "exactly the 2 documented stub MISSING lines expected\nstdout=%r"
            % stdout)
        self.assertNotIn("[UNAPPROVED]", stdout,
                         "0 unapproved claim references expected\nstdout=%r"
                         % stdout)
        for stub in PHASE8_STUB_NODES:
            self.assertIn(
                "node '%s' references claim_id 'PLACEHOLDER_PHASE8'" % stub,
                stdout,
                "the sanctioned residual is %s -> PLACEHOLDER_PHASE8"
                % stub)

    def test_gate_bare_invocation_exit_2(self):
        """The three-way contract's config-error branch on the real tool:
        bare invocation (required --story/--registry absent) exits 2 with
        usage (argparse), NOT 0/1."""
        r = self._run_gate([])
        self.assertEqual(
            r.returncode, 2,
            "bare invocation exits 2 (config/usage error -- the three-way "
            "exit contract); got %d" % r.returncode)


class TestEditCoverageRealData(unittest.TestCase):
    """Group 5: coverage + validation of rpg/data/edits.json against the
    real cast + the real 57-node graph."""

    def setUp(self):
        self._graph = _load_graph()
        self._table = _load_edits()
        self._cast_ids = _load_cast_ids()

    def test_coverage_tool_exit_0(self):
        """tools/check_edit_coverage.py (hardcoded rpg/data paths,
        CWD-independent via __file__) exits 0: every cast.json enzyme has
        >=1 edits.json entry (12/12 after 07-15)."""
        r = subprocess.run(
            [sys.executable, COVERAGE_SCRIPT],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout = r.stdout.decode("utf-8")
        self.assertEqual(
            r.returncode, 0,
            "expected exit 0 (12/12 cast enzymes covered)\nstdout=%r\n"
            "stderr=%r" % (stdout, r.stderr.decode("utf-8")))
        self.assertIn("EDIT COVERAGE PASSED", stdout)
        self.assertEqual(
            stdout.count("[COVERED]"), len(self._cast_ids),
            "one [COVERED] line per cast enzyme (%d)" % len(self._cast_ids))

    def test_scan_edit_coverage_green(self):
        """scan_edit_coverage(table, cast_ids) == [] (the in-process SC5
        helper over the real manifests)."""
        self.assertEqual(
            scan_edit_coverage(self._table, self._cast_ids), [],
            "every cast enzyme must have >=1 edits.json entry")

    def test_validate_edits_table_clean_vs_real_graph(self):
        """validate_edits_table(edits, real 57-node graph) == [] -- no
        dangling branch_node / dangling pool node / empty pool / duplicate
        signature (the fixture entry would have failed the dangling check;
        the real 13 buckets pass)."""
        issues = validate_edits_table(self._table, self._graph.all_nodes())
        self.assertEqual(
            issues, [],
            "edits.json must validate clean against the real graph; "
            "issues=%s" % issues)


class TestKnownEditRoundTrip(unittest.TestCase):
    """Group 6: every edits.json signature, rebuilt as an EditIntent, routes
    to its recorded branch_node -- which must exist in the real graph."""

    def test_every_signature_routes_to_existing_branch(self):
        """Round-trip identity proof: signature -> EditIntent ->
        EditRouter.route -> the SAME branch_node the table records (and
        that node exists). 13 signatures, one per edits.json bucket. This
        is the contract the EditDialog relies on: the offered known-fix
        (op, target, args) reproduces the table signature EXACTLY, so the
        player's known edit routes by construction."""
        graph = _load_graph()
        table = _load_edits()
        router = EditRouter(table)
        raw = table.to_dict().get("enzymes", {})
        checked = 0
        for enzyme_id, bucket in raw.items():
            for entry in bucket.get("edits", []):
                sig = entry["signature"]
                branch = entry["branch_node"]
                with self.subTest(enzyme=enzyme_id, target=sig.get("target")):
                    intent = EditIntent(
                        sig["op"], sig["target"],
                        dict(sig.get("args", {})), enzyme_id)
                    # Known entries match on the normalized signature, so
                    # the pick is deterministic: the RngEngine is never
                    # consulted (injected anyway per the route() contract).
                    dest = router.route(intent, enzyme_id, RngEngine(0))
                    self.assertEqual(
                        dest, branch,
                        "rebuilt EditIntent must route to the recorded "
                        "branch_node")
                    self.assertIn(
                        branch, graph.all_nodes(),
                        "branch_node %r must exist in the real graph "
                        "(no dangling branches)" % branch)
                checked += 1
        self.assertEqual(
            checked, 13,
            "all 13 edits.json signatures round-trip (one per bucket "
            "after the 07-13 tca.akg_dh 13th bucket); checked %d" % checked)


class TestManifestRelationships(unittest.TestCase):
    """The shared-manifest invariant (orchestrator ground truth): the three
    manifest sets relate EXACTLY as the post-07-15 design intends."""

    def test_cast_edits_tag_relationships(self):
        """cast(12) subset-of edits(13) == distinct edit:enzyme tag
        values(14) minus {tca.citrate_synthase}.
        - tca.citrate_synthase: edit:structural reframe (NO disease point
          mutant, 0 natural variants) -- tag but deliberately NO edits
          bucket.
        - tca.akg_dh: edits bucket (the 07-13 D5 promotion) but NO cast
          entry (no approved OGDH cast PDB).
        - The global bad_ending_pool members are all endings."""
        graph = _load_graph()
        table = _load_edits()
        cast_ids = set(_load_cast_ids())
        edit_ids = set(table.to_dict().get("enzymes", {}).keys())
        tag_values = set()
        for node in graph.all_nodes().values():
            for tag in node.tags:
                if str(tag).startswith("edit:enzyme:"):
                    tag_values.add(str(tag)[len("edit:enzyme:"):])
        self.assertEqual(len(cast_ids), 12, "cast.json has 12 enzyme ids")
        self.assertEqual(len(edit_ids), 13,
                         "edits.json has 13 buckets")
        self.assertEqual(len(tag_values), 14,
                         "the graph carries 14 DISTINCT edit:enzyme tag "
                         "values across 15 edit-allowed nodes (tca.aconitase "
                         "is shared by tca.aconitase + tca.shuffle)")
        self.assertTrue(cast_ids.issubset(edit_ids),
                        "cast(12) subset-of edits(13); missing=%s"
                        % sorted(cast_ids - edit_ids))
        self.assertEqual(
            edit_ids, tag_values - {"tca.citrate_synthase"},
            "edits(13) == tags(14) - {tca.citrate_synthase} (CS is "
            "edit:structural, no edits bucket by design); diff=%s"
            % (edit_ids ^ (tag_values - {"tca.citrate_synthase"})))
        self.assertEqual(
            cast_ids, edit_ids - {"tca.akg_dh"},
            "cast(12) == edits(13) - {tca.akg_dh} (no approved OGDH cast "
            "PDB yet); diff=%s" % (cast_ids ^ (edit_ids - {"tca.akg_dh"})))
        for pool_node in table.global_pool:
            self.assertIsNotNone(
                graph.get_node(pool_node).is_ending,
                "global bad_ending_pool member %r must be an ending"
                % pool_node)


def _walk_to_shuffle(engine, max_steps=40):
    # type: (GameEngine, int) -> int
    """Walk the engine from the start node to tca.shuffle via choice[0]
    (every node on the aerobic main path is pure-MC; choice[0] is the
    Continue choice). Returns the step count; fails the walk (AssertionError
    via the caller's cap check) if the shuffle is not reached."""
    steps = 0
    while engine.state.current_node != "tca.shuffle":
        engine.choose(0)
        steps += 1
        if steps > max_steps:
            break
    return steps


class TestSeededDeterminismDesignB(unittest.TestCase):
    """Group 7: design-B seeded determinism at the tca.shuffle wheel
    (07-13). Engine level: GameEngine + its StoryInterpreter pick over the
    shuffle node's real weighted choices (0.5/0.5) via the single seeded
    RngEngine. The controller is NOT involved (Phase-6 UI layer)."""

    def setUp(self):
        self._graph = _load_graph()
        self._table = _load_edits()

    def _engine(self, seed):
        # type: (int) -> GameEngine
        eng = GameEngine(
            self._graph, molaction_sink=[].append,
            edit_router=EditRouter(self._table))
        eng.start("glucose", seed)
        return eng

    def test_seed42_shuffle_fate_is_documented_retained(self):
        """DOCUMENTED FATE (design B, pinned): a fresh seed-42 playthrough,
        walked choice[0] along the aerobic main path to the shuffle, then
        wheel-spun, lands on tca.co2_turn2 -- 'your carbon is retained
        aboard' (first draw 0.6394... > the 0.5 cumulative threshold). The
        full walk ALSO proves the main path consumes ZERO RNG draws before
        the shuffle (the fate equals the fresh-draw fate)."""
        eng = self._engine(SHUFFLE_SEED)
        steps = _walk_to_shuffle(eng)
        self.assertLessEqual(
            steps, 40,
            "choice[0] walk must reach tca.shuffle in <=40 steps; "
            "stuck at %r after %d" % (eng.state.current_node, steps))
        tr = eng.choose(0)  # weighted: the RNG decides; index ignored
        self.assertEqual(
            tr.node.id, SHUFFLE_EXPECTED_FATE,
            "seed %d -> the documented design-B fate %r ('retained "
            "aboard'); got %r" % (SHUFFLE_SEED, SHUFFLE_EXPECTED_FATE,
                                  tr.node.id))

    def test_same_seed_reproducible_at_engine_level(self):
        """Two independent seed-42 engines, identical walks -> the identical
        shuffle fate (classroom reproducibility, Anti-Pattern 7's single
        seeded engine)."""
        fates = []
        for _ in range(2):
            eng = self._engine(SHUFFLE_SEED)
            _walk_to_shuffle(eng)
            fates.append(eng.choose(0).node.id)
        self.assertEqual(
            fates, [SHUFFLE_EXPECTED_FATE, SHUFFLE_EXPECTED_FATE],
            "same seed -> same fate, twice; got %s" % fates)

    def test_different_seeds_yield_both_fates(self):
        """Over 30 fresh engines (seeds 0..29), BOTH weighted outcomes occur
        (observed 15/15): the 0.5/0.5 wheel genuinely varies with the seed
        while staying reproducible per seed. Uses engine.goto(tca.shuffle)
        -- the controller's real entry for non-weighted choices at a mixed
        node -- then choose() for the weighted pick."""
        fates = {}
        for seed in range(30):
            eng = self._engine(seed)
            eng.goto("tca.shuffle")
            fate = eng.choose(0).node.id
            fates[fate] = fates.get(fate, 0) + 1
            self.assertIn(
                fate, (SHUFFLE_EXPECTED_FATE, SHUFFLE_OTHER_FATE),
                "seed %d produced a non-weighted-choice fate %r" % (seed,
                                                                    fate))
        self.assertEqual(
            set(fates.keys()),
            {SHUFFLE_EXPECTED_FATE, SHUFFLE_OTHER_FATE},
            "both design-B outcomes occur across seeds; tally=%s" % fates)

    def test_shuffle_is_the_only_weighted_node(self):
        """The tca.shuffle wheel is the graph's ONLY weighted-choice node --
        the entire RNG surface (and thus the whole seeded-determinism
        scope). The host-O2 RNG event from research section 7 was never
        implemented (07-01 DC-B: pyr.branch is an explicit player choice),
        so any NEW weighted node appearing elsewhere is a design-B contract
        change that must update this pin + the documented fate."""
        weighted_nodes = {}
        for nid, node in self._graph.all_nodes().items():
            weighted = [c for c in node.choices if c.weight is not None]
            if weighted:
                weighted_nodes[nid] = [(c.goto, c.weight)
                                       for c in weighted]
        self.assertEqual(
            weighted_nodes,
            {"tca.shuffle": [("tca.co2_turn1", 0.5),
                             ("tca.co2_turn2", 0.5)]},
            "tca.shuffle is the only weighted node (0.5/0.5 design B); "
            "got %s" % weighted_nodes)


class TestRestorationArcIntegration(unittest.TestCase):
    """Group 8: the restoration arc end-to-end at gly.pfk -- the known
    signature routes to gly.pfk_restored, whose on_enter carries the
    plan-12 [edit -> load -> align -> show_as] reveal, delivered to a mock
    sink exactly as the controller would dispatch it."""

    def setUp(self):
        self._graph = _load_graph()
        self._table = _load_edits()

    def test_pfk_restored_node_on_enter_shape(self):
        """Graph-level: gly.pfk_restored's on_enter is the 05.3 restoration-
        reveal sequence [edit, load, align, show_as] with the plan-12
        details (reverse mutation resi 209 -> GLY; WT cast pdb:4PFK as
        pfk_wt; super alignment of pfk_wt onto the edited pfk)."""
        node = self._graph.get_node("gly.pfk_restored")
        ops = [m.op for m in node.on_enter]
        self.assertEqual(
            ops, ["edit", "load", "align", "show_as"],
            "gly.pfk_restored on_enter must be the plan-12 reveal "
            "sequence; got %s" % ops)
        edit_m = node.on_enter[0]
        self.assertEqual(edit_m.target, "pfk")
        self.assertEqual(edit_m.args.get("edit_type"), "point_mutation")
        self.assertEqual(edit_m.args.get("sele"), "resi 209 and chain A")
        self.assertEqual(edit_m.args.get("new_resn"), "GLY")
        load_m = node.on_enter[1]
        self.assertEqual(load_m.target, "pdb:4PFK")
        self.assertEqual(load_m.args.get("object"), "pfk_wt")
        align_m = node.on_enter[2]
        self.assertEqual(align_m.target, "pfk_wt",
                         "align mobile = the WT object (it MOVES)")
        self.assertEqual(align_m.args.get("reference"), "pfk",
                         "align reference (FIXED) = the edited enzyme")
        self.assertEqual(align_m.args.get("method"), "super",
                         "op=align dispatches cmd.super (07-04 batch C)")

    def test_pfk_known_edit_routes_and_dispatches_reveal(self):
        """Engine-level with a mock sink: the player's gly.pfk known fix
        (built verbatim from the edits.json signature) routes to
        gly.pfk_restored, records ONE edit in edits_history, and the sink
        receives the 4 reveal MolActions in order."""
        sink = []
        eng = GameEngine(
            self._graph, molaction_sink=sink.append,
            edit_router=EditRouter(self._table))
        eng.start("glucose", SHUFFLE_SEED)
        sig = self._table.enzyme("gly.pfk")["edits"][0]["signature"]
        intent = EditIntent(sig["op"], sig["target"],
                            dict(sig["args"]), "gly.pfk")
        # The sink is cumulative (start() already dispatched intro.preface's
        # on_enter); isolate the dispatch under test.
        del sink[:]
        tr = eng.apply_player_edit(intent, "gly.pfk")
        self.assertEqual(
            tr.node.id, "gly.pfk_restored",
            "the gly.pfk known signature routes to the restoration node")
        self.assertEqual(
            len(eng.state.edits_history), 1,
            "apply_player_edit records the edit")
        self.assertEqual(
            [a.op for a in sink], ["edit", "load", "align", "show_as"],
            "the mock sink received the reveal sequence in order; "
            "got %s" % [a.op for a in sink])
        self.assertEqual(
            len(sink), 4,
            "exactly the 4 reveal MolActions dispatched (per-action "
            "dispatch contract)")
        # The routed node's TurnResult molactions == what the sink got.
        self.assertEqual(
            [a.to_dict() for a in tr.molactions],
            [a.to_dict() for a in sink],
            "TurnResult molactions mirror the sink dispatch")


if __name__ == "__main__":
    unittest.main()
