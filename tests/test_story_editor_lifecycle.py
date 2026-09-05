"""Structural lifecycle test battery for the Phase 7.1 editor's node-
lifecycle asset (07.1-17 Task 2).

Covers (over tools/story_editor_assets/45_lifecycle.js and the emitted
page), per the plan's B1 + B2 contract (RESEARCH-DATA §1.7 transition
table + RESEARCH-SAFETY breakage map B1/B2 + Pitfall S2):

- id validation: LIVE uniqueness across all files (the graph.py:76-80
  ValueError class) + the dot-convention regex, warn-not-block
  (test_id_validation)
- delete blocklist: ALL SIX reference classes (inbound choice.goto /
  edits.json branch_node / bad_ending_pool membership / cast.json id /
  edits.json bucket + graph edit:enzyme: tag carriers / manifest.start)
  are computed BEFORE any delete, with the itemized block list + the
  re-point offer (test_delete_blocklist)
- recipes NOT fields: there is NO stored node_type write anywhere; the
  edit-allowed recipe COMPOSES tag + edit:offer choice + the edits.json
  bucket handoff; the ending recipe sets is_ending + ending:* tag +
  choices [] (test_recipes_not_fields, test_seed_shapes)
- count-shift acknowledgment: the modal names the three pinned tests +
  the viewer EXPECTED_* constants, and the action applies ONLY from the
  "I understand - allow" handler (test_count_shift_modal)
- rng acknowledgment: weights outside tca.shuffle require the determinism
  acknowledgment (test 16 breakage) (test_rng_acknowledgment)
- orphan guard: making an ending runs the BFS on the WOULD-BE state and
  BLOCKS when unreachable, with candidate-parent deep links
  (test_orphan_guard)
- ES5 discipline, own-container-only delegation, the scoped delete
  allowlist, bracket balance, and emitted-page inlining in pipeline order
  (test_es5_discipline, test_own_container_delegation,
  test_scoped_delete_allowlist, test_bracket_balance,
  test_emitted_page_inlines_lifecycle_asset)

Markup-attribute greps are ESCAPE-TOLERANT (attributes may appear plain or
JS-escaped inside double-quoted string literals — the sibling-battery
convention). Pure WSL python3.6 — stdlib only; the generator is
subprocessed once per test class via setUpClass into a temp dir using
--output (same conventions as tests/test_story_editor_form.py: REPO_ROOT
via __file__, subprocess.run with PIPE streams — NOT capture_output,
which is 3.7+). The battery greps only THIS plan's asset, so it stays
robust while parallel wave agents are in flight.
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
LIFECYCLE_ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "45_lifecycle.js")

# The pinned trio + viewer constants (the SAME strings 20_validate.js's
# count_shift notice names — the acknowledgment modal must carry them).
PINNED_TESTS = [
    "test_manifest_loads_all_57_nodes",
    "test_reachability_green_all_four_tiers",
    "test_15_edit_allowed_nodes",
]
PINNED_CONSTANTS = [
    "EXPECTED_NODES", "EXPECTED_TIER_COUNTS", "EXPECTED_EDIT_ALLOWED",
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


def _strip_js(src):
    # type: (str) -> str
    """Blank out string/char literals and comments so bracket counts and
    token greps see CODE only (a cheap structural parse — WSL has no JS
    runtime; runtime behavior belongs to the Firefox human-verify
    checkpoints). Regex literals are left as-is: their contents are
    bracket-balanced by construction in this asset."""
    out = []
    i, n = 0, len(src)
    mode = None  # None | "'" | '"' | 'line' | 'block'
    while i < n:
        c = src[i]
        if mode is None:
            if c in ("'", '"'):
                mode = c
                out.append(" ")
            elif c == "/" and i + 1 < n and src[i + 1] == "/":
                mode = "line"
                out.append(" ")
            elif c == "/" and i + 1 < n and src[i + 1] == "*":
                mode = "block"
                out.append(" ")
            else:
                out.append(c)
        elif mode in ("'", '"'):
            if c == "\\":
                i += 2
                continue
            if c == mode:
                mode = None
            out.append(" ")
        elif mode == "line":
            if c == "\n":
                mode = None
                out.append("\n")
            else:
                out.append(" ")
        else:  # block
            if c == "*" and i + 1 < n and src[i + 1] == "/":
                mode = None
                i += 2
                out.append("  ")
                continue
            out.append(" ")
        i += 1
    return "".join(out)


class TestLifecycleAssetStructure(unittest.TestCase):
    """Structural checks over the lifecycle asset + ONE emitted page."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_lifecycle_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.asset = _read(LIFECYCLE_ASSET) if os.path.isfile(
            LIFECYCLE_ASSET) else ""
        cls.code = _strip_js(cls.asset)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _lifecycle_block(self):
        # type: () -> str
        """Extract the inlined 45_lifecycle.js <script> block."""
        marker = "/* asset: 45_lifecycle.js"
        m_start = self.html.find(marker)
        self.assertGreaterEqual(
            m_start, 0,
            "45_lifecycle.js asset marker missing from emitted HTML")
        block_open = self.html.rfind("<script>", 0, m_start)
        self.assertGreaterEqual(
            block_open, 0, "lifecycle asset block has no opening <script>")
        block_close = self.html.find("</script>", m_start)
        self.assertGreaterEqual(
            block_close, 0, "lifecycle asset block is unterminated")
        return self.html[block_open:block_close]

    # ------------------------------------------------------------------
    # 1. Id validation (B1 — live, per keystroke)
    # ------------------------------------------------------------------

    def test_id_validation(self):
        """The add wizard validates the id LIVE: unique across ALL files
        (the graph.py:76-80 duplicate-id ValueError class) + the
        dot-convention regex ^[a-z0-9_]+\\.[a-z0-9_]+$ (warn otherwise,
        never a silent pass)."""
        # Real implementation gate (the artifact spec asks >= 180 lines).
        self.assertGreaterEqual(
            len(self.asset.splitlines()), 180,
            "the lifecycle asset must be a real implementation (artifact "
            "spec asks for >= 180 lines)")
        # The uniqueness check: a duplicate refuses (checkId + idExists
        # over EDITOR.nodeById), citing the graph.py:76-80 class.
        self.assertIn("function checkId(", self.asset,
                      "the live id check must exist as a named function")
        self.assertIn("function idExists(", self.asset)
        self.assertIn("EDITOR.nodeById(", self.asset,
                      "uniqueness must walk the loaded bundle (all files)")
        self.assertIn("graph.py:76-80", self.asset,
                      "the duplicate-id rule must cite its Python source")
        self.assertIn("DUPLICATE", self.asset,
                      "a duplicate id must surface an explicit refusal")
        # The dot-convention regex, verbatim, with the warn path.
        self.assertIn("/^[a-z0-9_]+\\.[a-z0-9_]+$/", self.asset,
                      "the dot-convention regex must be present verbatim")
        self.assertIn("dot-convention", self.asset)
        # Warn, not block: the regex failure keeps ok=true with a warning.
        m = re.search(
            r"function checkId\([^)]*\) \{([\s\S]*?)\n  \}", self.asset)
        self.assertTrue(m, "checkId body not found")
        body = m.group(1)
        self.assertIn('level: "warn"', body,
                      "a non-dot-convention id must WARN (allowed), not "
                      "silently pass or hard-fail")
        self.assertIn('level: "error"', body,
                      "duplicates must be a hard error")
        # The wizard's verdict line + create gate consume the check live.
        self.assertTrue(
            _has_markup(self.asset, "data-lc-live", "idverdict"),
            "the wizard must render the live id verdict")
        self.assertIn("createBlocked(", self.asset)
        # The checkId export (the diagnostics tab + this battery's contract).
        self.assertIn("EDITOR.lifecycle.checkId = checkId", self.asset)

    # ------------------------------------------------------------------
    # 2. Delete blocklist (B1 — six reference classes + re-point offer)
    # ------------------------------------------------------------------

    def test_delete_blocklist(self):
        """Delete computes the referencing sets FIRST and blocks with an
        itemized list while ANY of the six classes exist: inbound goto /
        edits.json branch_node / bad_ending_pool membership / cast.json id
        / edits.json bucket + graph edit:enzyme: tag carriers /
        manifest.start — with the re-point offer for incoming edges."""
        self.assertIn("function computeReferences(", self.asset,
                      "the referencing sets must be a named pre-computation")
        self.assertIn("EDITOR.allNodes()", self.asset)
        # Class 1: inbound choice.goto (the dangling_divert class).
        self.assertTrue(
            re.search(r"c\.goto === id", self.asset),
            "inbound choice.goto must be collected")
        self.assertIn("dangling_divert", self.asset)
        # Class 2: edits.json branch_node (dangling_edit_branch).
        self.assertTrue(
            re.search(r"entry\.branch_node === id", self.asset),
            "edits.json branch_node targets must be collected")
        self.assertIn("dangling_edit_branch", self.asset)
        # Class 3: bad_ending_pool membership, global + per-enzyme
        # (dangling_pool_node).
        self.assertIn("bad_ending_pool", self.asset)
        self.assertIn("dangling_pool_node", self.asset)
        self.assertIn('"global"', self.asset,
                      "the GLOBAL pool must be checked, not just overrides")
        # Class 4: cast.json id (coverage).
        self.assertTrue(
            re.search(r"cast\[m\]\.id === id|cast\.id === id", self.asset) or
            re.search(r"\.id === id", self.asset),
            "the cast.json id class must be collected")
        self.assertIn("castEntries(", self.asset)
        # Class 5: the edits.json bucket keyed by the id + the graph
        # edit:enzyme:<id> tag carriers (the relationship-pin class).
        self.assertIn("enzymeBucket", self.asset)
        self.assertTrue(
            re.search(r"\"edit:enzyme:\" \+ id", self.asset),
            "the graph edit:enzyme:<id> tag carriers must be collected")
        self.assertIn("tagCarriers", self.asset)
        self.assertIn("relationship pin", self.asset)
        # Class 6: manifest.start.
        self.assertTrue(
            re.search(r"manifest\.start === id", self.asset),
            "manifest.start must be checked")
        # The block + the offers: itemized BLOCKED list, re-point with
        # per-edge selects, Data-tab deep link, typed start replacement.
        self.assertIn("BLOCKED", self.asset,
                      "the delete must render an itemized block list")
        self.assertIn("re-point", self.asset,
                      "the re-point-N-edges offer must be present")
        self.assertIn("repoint-apply", self.asset)
        self.assertTrue(
            # The select is built by concatenation, so the attribute value
            # is an escaped-open-quote prefix (no closing quote on this
            # fragment): data-lc-field=\"repoint:<src>:<idx>.
            ('data-lc-field="repoint:' in self.asset or
             'data-lc-field=\\"repoint:' in self.asset),
            "per-edge re-point selects must be rendered")
        self.assertIn("data-tab", self.asset,
                      "the Data-tab deep link must be offered")
        self.assertIn("start-replacement", self.asset,
                      "the start deletion must require a typed replacement")
        self.assertIn("deleteUnblocked(", self.asset,
                      "the delete button must be gated on the reference set")
        # The re-point action touches ONLY the goto field (per edge).
        self.assertIn("c.goto = mv.target", self.asset,
                      "re-point must mutate ONLY the goto field (B11)")

    # ------------------------------------------------------------------
    # 3. Recipes, NOT fields (B2 — there is no stored node_type)
    # ------------------------------------------------------------------

    def test_recipes_not_fields(self):
        """NO node_type write anywhere. The edit-allowed recipe COMPOSES:
        the edit:enzyme:<id> tag + the edit:offer choice (goto edit.prompt,
        tag edit:offer) + the edits.json bucket handoff (Data tab, id
        prefilled). The ending recipe sets is_ending + the ending:<tier>
        tag + choices []."""
        # The negative pin: node_type appears ONLY as prose ("there is NO
        # stored node_type"), never as a key write.
        for line in self.asset.splitlines():
            if "node_type" not in line:
                continue
            stripped = line.strip()
            is_comment = (stripped.startswith("*") or
                          stripped.startswith("//") or
                          stripped.startswith("/*"))
            writes_key = re.search(
                r"[\"']node_type[\"']\s*[:=]|nodeSet\([^)]*node_type",
                stripped)
            self.assertFalse(
                writes_key and not is_comment,
                "node_type must never be WRITTEN (kinds are derived): %r"
                % stripped)
        self.assertIn("NO stored node_type", self.asset,
                      "the derived-kind contract must be documented")
        # Edit-allowed recipe: the three composed steps.
        self.assertIn("\"edit:offer\"", self.asset,
                      "step 2: the edit:offer choice tag")
        self.assertIn("goto: \"edit.prompt\"", self.asset,
                      "step 2: the offer choice routes to edit.prompt")
        self.assertIn("edit:enzyme:", self.asset,
                      "step 1: the edit:enzyme:<id> tag")
        self.assertIn("dataBucketPrefill", self.asset,
                      "step 3: the edits.json bucket handoff")
        self.assertIn("bucket-new-id", self.asset,
                      "the handoff prefills the Data tab's bucket input")
        self.assertIn("edit:structural", self.asset,
                      "the structural-skip note (tca.citrate_synthase "
                      "precedent) must be present")
        # Ending recipe: is_ending set + tier tag + choices [].
        self.assertIn("n.is_ending = tier;", self.asset,
                      "the ending recipe sets is_ending")
        self.assertIn("n.choices = [];", self.asset,
                      "the ending recipe clears choices (all endings carry "
                      "choices: [])")
        self.assertTrue(
            re.search(r"\"ending:\" \+ tier", self.asset),
            "the ending recipe adds the suggested ending:<tier> tag")
        self.assertIn("stage", self.asset,
                      "the ending recipe suggests the stage:* tag")
        # Un-make ending: is_ending REMOVAL (absent, never null) + the
        # pool refusal.
        self.assertTrue(
            re.search(r"delete\s+n\.is_ending", self.asset),
            "un-make ending must REMOVE the is_ending key (absent, never "
            "null)")
        self.assertIsNone(
            re.search(r"is_ending[\"']?\s*:\s*null", self.asset),
            "is_ending must never be written as null")
        self.assertIn("pool_node_not_ending", self.asset,
                      "un-make ending must refuse while the id is in any "
                      "bad_ending_pool")
        self.assertIn("idInAnyPool(", self.asset)
        # Make-start: a manifest edit with typed confirmation, NOT a node
        # field.
        self.assertIn("bb.manifest.start = next", self.asset,
                      "make-start edits manifest.start via apply()")
        self.assertIn("start-typed", self.asset,
                      "the typed confirmation input must exist")
        self.assertIn("startReady(", self.asset)
        self.assertIn("MANIFEST_FNAME", self.asset,
                      "the manifest edit marks manifest.json dirty")

    def test_seed_shapes(self):
        """The add-wizard seeds compose the recipe fields minimal-per-type:
        endings seed choices [] + is_ending + the suggested ending:<tier>
        tag (+ stage); the base shape is the documented 6-key schema."""
        self.assertIn("function seedNode(", self.asset)
        for key in ("text_dramatic", "text_teaching", "claim_ids", "tags",
                    "on_enter", "choices"):
            self.assertIn(key, self.asset,
                          "the seed base shape must carry %s" % key)
        self.assertIn('{ op: "hide_all" }', self.asset,
                      "every seed starts with the hide_all op (the data's "
                      "uniform first op)")
        # Ending seed: choices [] + is_ending + ending:<tier>.
        m = re.search(
            r"else if \(type === \"ending\"\) \{([\s\S]*?)\n    \}", self.asset)
        self.assertTrue(m, "the ending seed branch not found")
        body = m.group(1)
        self.assertIn("node.is_ending = o.tier", body)
        self.assertIn("\"ending:\"", body)
        # Seed types offered by the wizard.
        for t in ("story", "multiple-choices", "mutation", "ending", "rng"):
            self.assertIn(t, self.asset,
                          "the seed select must offer %s" % t)
        self.assertIn("EDITOR.lifecycle.SEED_TYPES", self.asset)

    # ------------------------------------------------------------------
    # 4. Count-shift acknowledgment (Pitfall S2)
    # ------------------------------------------------------------------

    def test_count_shift_modal(self):
        """The acknowledgment modal names the three pinned tests + the
        viewer EXPECTED_* constants, and the action applies ONLY from the
        "I understand - allow" handler (ackAllow) — never before."""
        # The modal text names the exact trio + constants.
        for t in PINNED_TESTS:
            self.assertIn(t, self.asset,
                          "the modal must name %s" % t)
        for c in PINNED_CONSTANTS:
            self.assertIn(c, self.asset,
                          "the modal must name the viewer constant %s" % c)
        self.assertIn("SAME commit", self.asset,
                      "the same-commit obligation must be stated")
        self.assertIn("I understand", self.asset,
                      "the explicit acknowledgment affordance")
        self.assertIn("ack-allow", self.asset)
        # The trio mirrors 20_validate.js's count_shift notice (one source
        # of truth for the acknowledgment).
        self.assertIn("count_shift", self.asset,
                      "the validator's count_shift notice mirror must be "
                      "surfaced")
        # The GATE: applyWithAck holds the action when counts move; ONLY
        # the ack-allow handler applies it.
        self.assertIn("function applyWithAck(", self.asset)
        m = re.search(
            r"function applyWithAck\(([\s\S]*?)\n  \}", self.asset)
        self.assertTrue(m, "applyWithAck body not found")
        body = m.group(1)
        self.assertIn("simulateCounts(", body,
                      "the would-be counts must be simulated")
        self.assertIn("ackState = ", body,
                      "a count-moving action must be HELD in ackState")
        self.assertIn("return false", body,
                      "applyWithAck must report not-applied while held")
        # The allow handler is the ONLY path that applies a held action.
        m2 = re.search(r"function ackAllow\(\) \{([\s\S]*?)\n  \}", self.asset)
        self.assertTrue(m2, "ackAllow (the gate's apply path) not found")
        body2 = m2.group(1)
        self.assertIn("EDITOR.apply(", body2,
                      "the held action must apply from the allow handler")
        # The simulation runs the EXACT redo on a clone (no second
        # implementation of any mutation).
        self.assertIn("action.redo(clone)", self.asset,
                      "the preview must run the EXACT redo function")
        # The PINNED values are named (57 / 21 / 15).
        self.assertIn("PINNED_NODES = 57", self.asset)
        self.assertIn("PINNED_ENDINGS = 21", self.asset)
        self.assertIn("PINNED_EDIT_ALLOWED = 15", self.asset)
        self.assertIn("EDITOR.lifecycle.COUNT_SHIFT_TESTS", self.asset)

    # ------------------------------------------------------------------
    # 5. RNG acknowledgment (weights outside tca.shuffle)
    # ------------------------------------------------------------------

    def test_rng_acknowledgment(self):
        """Weights on ANY node other than tca.shuffle require the
        determinism acknowledgment (test 16 breakage: the shuffle-only pin
        + the seed-42 fate)."""
        self.assertIn('SHUFFLE_NODE = "tca.shuffle"', self.asset)
        self.assertIn("test_shuffle_is_the_only_weighted_node", self.asset,
                      "the determinism modal must name the owning test")
        self.assertIn("TestSeededDeterminismDesignB", self.asset,
                      "the determinism modal must name the seeded-fate "
                      "test")
        self.assertIn("tca.co2_turn2", self.asset,
                      "the seed-42 fate pin must be cited")
        # The shuffle node itself is exempt ("without ceremony").
        self.assertIn("no ceremony", self.asset,
                      "tca.shuffle weight edits must be ceremony-free")
        # The recipe routes the determinism flag through the ack gate.
        self.assertIn("determinism: true", self.asset,
                      "the rng recipe must request the determinism "
                      "acknowledgment")
        m = re.search(
            r"function applyWithAck\(action, label, opts\) \{", self.asset)
        self.assertTrue(m, "applyWithAck must accept the determinism flag")
        self.assertIn("needDet", self.asset,
                      "the determinism flag must gate the modal")
        self.assertIn("determinism: (w.seed === \"rng\")", self.asset,
                      "the wizard's rng seed must request the "
                      "acknowledgment at create")

    # ------------------------------------------------------------------
    # 6. Orphan guard (make-ending BFS pre-check)
    # ------------------------------------------------------------------

    def test_orphan_guard(self):
        """Making an ending runs the BFS on the WOULD-BE state and BLOCKS
        when the candidate is unreachable, with candidate-parent deep
        links (the reachability red class)."""
        self.assertIn("function endingWouldBeOrphan(", self.asset)
        self.assertIn("EDITOR.bfsReachable(", self.asset,
                      "the guard must reuse the validator's BFS (goto-only "
                      "parity), never a second BFS")
        # The apply path consults the guard BEFORE building the action.
        m = re.search(
            r"function applyRecipeEnding\(\) \{([\s\S]*?)\n  \}", self.asset)
        self.assertTrue(m, "applyRecipeEnding not found")
        body = m.group(1)
        guard_idx = body.find("endingWouldBeOrphan(")
        apply_idx = body.find("applyWithAck(")
        self.assertGreaterEqual(guard_idx, 0,
                                "the ending apply must run the orphan guard")
        self.assertGreater(apply_idx, guard_idx,
                           "the guard must run BEFORE the apply")
        self.assertIn("if (check.orphan)", body,
                      "an orphaned candidate must BLOCK")
        # The block explanation + the deep links.
        self.assertIn("ORPHAN-ENDING BLOCK", self.asset,
                      "the orphan explanation must render")
        self.assertIn("unreachable_ending", self.asset,
                      "the reachability red class must be named")
        self.assertIn("function candidateParents(", self.asset)
        self.assertIn("pick-parent:", self.asset,
                      "candidate-parent deep links must be offered")
        self.assertIn("EDITOR.select(", self.asset,
                      "the deep link selects the parent (its Choices "
                      "editor)")

    # ------------------------------------------------------------------
    # 7. ES5 discipline + own-container delegation + delete allowlist
    # ------------------------------------------------------------------

    def test_es5_discipline(self):
        """The asset is ES5-classic: no arrow functions, no let/const, no
        module markers; no </script breakout sequence."""
        self.assertIsNone(
            re.search(r"=>", self.asset),
            "arrow functions are forbidden (ES5 var-style is the pinned "
            "emitted-JS convention)")
        self.assertIsNone(
            re.search(r"\blet\s", self.asset), "let is forbidden")
        self.assertIsNone(
            re.search(r"\bconst\s", self.asset), "const is forbidden")
        self.assertNotIn('type="module"', self.asset)
        self.assertNotIn("</script", self.asset,
                         "a literal </script would break the inline block")

    def test_own_container_delegation(self):
        """All delegated listeners attach to the asset's OWN containers
        only: the #node-form-lifecycle mount, the self-created
        #lifecycle-toolbar, the self-created #lifecycle-overlay — never
        the shared #node-form aside or any sibling mount."""
        self.assertIn("node-form-lifecycle", self.asset,
                      "the fixed shell mount must be owned")
        self.assertIn("lifecycle-toolbar", self.asset)
        self.assertIn("lifecycle-overlay", self.asset)
        self.assertIn("tab-graph", self.asset,
                      "the toolbar appends into the graph tab")
        # Every EDITOR.delegate call targets the wireContainer parameter
        # (ONE call site in wireContainer, invoked per owned container at
        # init: section, toolbar, overlay).
        delegates = re.findall(r"EDITOR\.delegate\(\s*(\w+)\s*,", self.asset)
        self.assertEqual(
            delegates, ["container"],
            "all delegation must flow through wireContainer(container); "
            "got %r" % delegates)
        # Every addEventListener call targets the container parameter
        # (the input + change listeners inside wireContainer).
        listeners = re.findall(r"(\w+)\.addEventListener\(", self.asset)
        self.assertEqual(
            listeners, ["container", "container"],
            "raw listeners must attach ONLY to the wireContainer "
            "parameter; got %r" % listeners)
        # No sibling mount references IN CODE (the header's ownership
        # prose may NAME sibling mounts — comments are stripped first) —
        # EXCEPT the sanctioned read-only Data-tab handoff (the
        # bucket-new-id prefill inside #tab-data).
        code = self.code
        for sibling in ("node-form-identity", "node-form-choices",
                        "node-form-onenter", "graph-area", "graph-toolbar"):
            self.assertNotIn(
                sibling, code,
                "the lifecycle asset must not reference the %s mount in "
                "code (sibling ownership)" % sibling)
        self.assertIn("bucket-new-id", self.asset,
                      "the Data-tab prefill is the sanctioned cross-mount "
                      "read")
        # data-lc-* namespacing (sibling delegation collision-freedom).
        self.assertIn("data-lc-act", self.asset)
        self.assertIn("data-lc-field", self.asset)

    def test_scoped_delete_allowlist(self):
        """A scoped review of EVERY executable `delete` passes an
        allowlist of exactly two named-key removals: the deleted node's
        dict key (delete file.nodes[id]) and the is_ending key removal
        (absent-not-null). No code path can delete an unknown key. The
        scan runs on the string/comment-stripped code so the word
        "delete" inside UI copy can never false-positive."""
        code = self.code
        allowed = [
            re.compile(r"delete\s+file\.nodes\[d\.id\]\s*;"),
            re.compile(r"delete\s+n\.is_ending\s*;"),
        ]
        offenders = []
        for m in re.finditer(r"\bdelete\b[^\n;]*;?", code):
            stmt = " ".join(m.group(0).split())
            if any(a.search(stmt) for a in allowed):
                continue
            offenders.append(stmt)
        self.assertEqual(
            offenders, [],
            "found executable delete(s) outside the allowlist — the "
            "lifecycle editor must never delete unknown keys: %r"
            % offenders)
        # The dirty-map MUTATION is the core's job — reading it (the
        # manifest-dirty notice) is fine; writing/deleting keys is not.
        self.assertIsNone(
            re.search(r"dirty\[[^\]]*\]\s*=", code),
            "dirty-map writes belong to the core/save layer")
        self.assertIsNone(
            re.search(r"delete\s+[\w.]*dirty", code),
            "dirty-map deletes belong to the core/save layer")

    def test_bracket_balance(self):
        """A cheap structural parse (WSL has no JS runtime): string- and
        comment-stripped brackets must balance exactly."""
        code = self.code
        self.assertEqual(code.count("{"), code.count("}"),
                         "curly braces unbalanced")
        self.assertEqual(code.count("("), code.count(")"),
                         "parentheses unbalanced")
        self.assertEqual(code.count("["), code.count("]"),
                         "square brackets unbalanced")

    # ------------------------------------------------------------------
    # 8. Emitted page inlining (pipeline order + verify strings)
    # ------------------------------------------------------------------

    def test_emitted_page_inlines_lifecycle_asset(self):
        """The emitted story_editor.html inlines the lifecycle asset with
        the plan's verify-step strings, in pipeline order (43_onenter.js
        < 45_lifecycle.js < 50_editscast.js, before the shell bootstrap)."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        block = self._lifecycle_block()
        # The plan's Task-1 verify strings, all present in the emitted page.
        for required in (
            "DUPLICATE",                      # the id-uniqueness check
            "BLOCKED",                        # the delete blocking list
            "re-point",                       # the re-point offer
            "Make edit-allowed",              # the recipe buttons
            "Make ending",
            "Make starting node",
            "Make rng",
            "test_manifest_loads_all_57_nodes",
            "test_reachability_green_all_four_tiers",
            "test_15_edit_allowed_nodes",
            "EXPECTED_NODES",
            "I understand",
        ):
            self.assertIn(required, block,
                          "emitted lifecycle block must contain %r"
                          % required)
        # The count-shift modal names the full pinned trio + constants.
        for t in PINNED_TESTS:
            self.assertIn(t, block)
        for c in PINNED_CONSTANTS:
            self.assertIn(c, block)
        # Pipeline order: 43_onenter.js -> 45_lifecycle.js ->
        # 50_editscast.js -> shell bootstrap.
        onenter_idx = self.html.find("/* asset: 43_onenter.js")
        lifecycle_idx = self.html.find("/* asset: 45_lifecycle.js")
        data_idx = self.html.find("/* asset: 50_editscast.js")
        boot_idx = self.html.rfind("EDITOR.runInits();")
        self.assertGreaterEqual(onenter_idx, 0)
        self.assertGreaterEqual(lifecycle_idx, 0)
        self.assertGreaterEqual(data_idx, 0)
        self.assertGreaterEqual(boot_idx, 0)
        self.assertLess(onenter_idx, lifecycle_idx,
                        "the on_enter asset must inline before lifecycle")
        self.assertLess(lifecycle_idx, data_idx,
                        "the lifecycle asset must inline before the Data "
                        "tab (its handoff prefill targets 50_editscast's "
                        "DOM)")
        self.assertLess(data_idx, boot_idx,
                        "all assets must inline before the bootstrap")
        # The EDITOR.lifecycle export block reached the page.
        self.assertIn("EDITOR.lifecycle.checkId", block)


def _has_markup(text, attr, value):
    # type: (str, str, str) -> bool
    """Escape-tolerant attribute check (plain or JS-escaped spelling)."""
    plain = '%s="%s"' % (attr, value)
    escaped = '%s=\\"%s\\"' % (attr, value)
    return plain in text or escaped in text


if __name__ == "__main__":
    unittest.main()
