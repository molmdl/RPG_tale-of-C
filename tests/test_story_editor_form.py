"""Structural node-form test battery for the Phase 7.1 editor form asset
(07.1-09 Task 2).

Covers (over tools/story_editor_assets/40_form.js and the emitted page):
- the B6 mapping with NO title field: the asset references
  text_dramatic / text_teaching / claim_ids, carries the id-as-title
  mapping comment, and contains NO attempt to write a "title" key (the
  schema has no title field — id-as-title is the mapping; a literal title
  field would be a schema change requiring engine/gate sign-off)
  (test_b6_mapping_no_title_field)
- text-edit granularity: the textareas bind through
  EDITOR.textFieldBindings (commit on change = ONE undo step; the asset
  wires NO input listener of its own — live preview flows through
  EDITOR.livePreview for the character counters, never a bundle write)
  (test_text_commit_granularity)
- claim chips resolve LIVE: bundle.citations + approval_status (strict
  `=== "approved"` semantics) + review_tier, with the MISSING state
  handled for unresolved ids, and the EDITOR.ui.claimFocus hook wired
  (C groundwork; consumed by the claims panel 07.1-12)
  (test_claim_chips_live)
- is_ending ABSENT-not-null: the select handler removes the key entirely
  (delete on the is_ending path) and never writes is_ending: null
  (test_is_ending_absent_not_null)
- the B9 Phase-12 reminder is present and CONDITIONED on endings (rendered
  only when EDITOR.endingTier(node) returns a tier)
  (test_b9_reminder)
- the B11 unknown-key guard: the read-only extra-keys section exists, and
  a SCOPED REVIEW of every `delete` occurrence in the asset passes an
  allowlist — the ONLY executable delete is the plan-mandated is_ending
  key removal; no code path deletes unknown keys
  (test_unknown_keys_guarded)
- ES5 discipline for the asset + the emitted page inlines the form asset
  in pipeline order (after 30_graph.js, before the shell bootstrap) with
  the plan's verify-step strings (test_es5_discipline,
  test_emitted_page_inlines_form_asset)

Markup-attribute greps are ESCAPE-TOLERANT: the asset builds HTML inside
ES5 double-quoted string literals, so attributes may appear either plain
(data-field="x") or JS-escaped (data-field=\"x\") — both spell the same
emitted markup.

Pure WSL python3.6 — stdlib only; the generator is subprocessed once per
test class via setUpClass into a temp dir using --output (same conventions
as tests/test_story_editor_graph.py: REPO_ROOT via __file__,
subprocess.run with PIPE streams — NOT capture_output, which is 3.7+).
The battery greps only THIS plan's asset, so it stays robust while the
parallel Wave-4 agents (60_trace.js / 70_claims.js / 80_save.js) are in
flight.
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
FORM_ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "40_form.js")

# The B9 reminder, as TWO em-dash-free fragments (the asset spells the
# em-dash as the ES5 \u2014 escape, so a whole-sentence grep would be
# escape-fragile; both fragments are verbatim substrings of the source).
B9_REMINDER_HEAD = "Ending CG (cutscene render) is Phase-12 territory"
B9_REMINDER_TAIL = "tracks this as a reminder, not a field (roadmap B9)"


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


def _has_markup(text, attr, value):
    # type: (str, str, str) -> bool
    """Escape-tolerant attribute check: the attribute may appear plain
    (attr="value") or JS-escaped inside a double-quoted string literal
    (attr=\"value\")."""
    plain = '%s="%s"' % (attr, value)
    escaped = '%s=\\"%s\\"' % (attr, value)
    return plain in text or escaped in text


class TestFormAssetStructure(unittest.TestCase):
    """Structural checks over the form asset + ONE emitted page."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_form_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.asset = _read(FORM_ASSET) if os.path.isfile(FORM_ASSET) else ""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _form_block(self):
        # type: () -> str
        """Extract the inlined 40_form.js <script> block from the page."""
        marker = "/* asset: 40_form.js"
        m_start = self.html.find(marker)
        self.assertGreaterEqual(
            m_start, 0, "40_form.js asset marker missing from emitted HTML")
        block_open = self.html.rfind("<script>", 0, m_start)
        self.assertGreaterEqual(
            block_open, 0, "form asset block has no opening <script>")
        block_close = self.html.find("</script>", m_start)
        self.assertGreaterEqual(
            block_close, 0, "form asset block is unterminated")
        return self.html[block_open:block_close]

    def _assert_markup(self, text, attr, value, msg):
        # type: (str, str, str, str) -> None
        self.assertTrue(
            _has_markup(text, attr, value), msg)

    # ------------------------------------------------------------------
    # 1. B6 mapping — id-as-title, NO invented title field
    # ------------------------------------------------------------------

    def test_b6_mapping_no_title_field(self):
        """The form implements the exact B6 mapping: it references
        text_dramatic / text_teaching / claim_ids, documents the id-as-title
        rule, and NEVER writes a "title" key (no nodeSet(..., "title", ...)
        call and no "title": key literal anywhere — the schema has no title
        field and inventing one would be a schema change requiring
        engine/gate sign-off)."""
        # The form is a real implementation (the plan's artifact spec asks
        # for >= 180 lines).
        self.assertGreaterEqual(
            len(self.asset.splitlines()), 180,
            "the node form must be a real implementation (artifact spec "
            "asks for >= 180 lines)")
        # The form is registered in the core's dedicated form slot.
        self.assertIn("EDITOR.setFormRenderer(", self.asset)
        # B6 mapping markers: the three mapped fields + the id-as-title
        # comment.
        self.assertTrue("text_dramatic" in self.asset
                        and "text_teaching" in self.asset
                        and "claim_ids" in self.asset,
                        "the asset must reference the mapped fields "
                        "text_dramatic / text_teaching / claim_ids")
        self.assertIn("id-as-title", self.asset,
                      "the asset must document the id-as-title B6 rule")
        self.assertIn("B6 FIELD MAPPING", self.asset,
                      "the asset must carry the B6 mapping comment block")
        # NO title-field write: no nodeSet(..., "title", ...) and no
        # "title": / 'title': key literal anywhere in the asset.
        self.assertIsNone(
            re.search(r"nodeSet\([^)]*[\"']title[\"']", self.asset),
            "the form must never nodeSet a title field (no such schema "
            "field exists)")
        self.assertIsNone(
            re.search(r"[\"']title[\"']\s*:", self.asset),
            "the form must never write a \"title\" key (id-as-title is "
            "the mapping; a literal title field = schema change)")
        self.assertIsNone(
            re.search(r"\bnode\[.[\"']title[\"'].\]\s*=", self.asset),
            "the form must never assign node.title")

    # ------------------------------------------------------------------
    # 2. Text-commit granularity (one undo step per field commit)
    # ------------------------------------------------------------------

    def test_text_commit_granularity(self):
        """The textareas bind through EDITOR.textFieldBindings (commit on
        change = one undo step; never per-keystroke snapshots). The asset
        wires NO input listener of its own: live preview (character
        counters) flows exclusively through EDITOR.livePreview, which never
        writes the bundle."""
        self.assertIn(
            "EDITOR.textFieldBindings(", self.asset,
            "the textareas must bind via the core's change-commit binding")
        self._assert_markup(
            self.asset, "data-field", "text_dramatic",
            "the dramatic textarea must carry the data-field binding")
        self._assert_markup(
            self.asset, "data-field", "text_teaching",
            "the teaching textarea must carry the data-field binding")
        # No self-wired input listeners: ALL input flow goes through the
        # core binding (change commits via apply) + the livePreview registry
        # (counters only, never a bundle write).
        self.assertNotIn(
            'addEventListener("input"', self.asset,
            "the asset must not wire its own input listener (live preview "
            "belongs to EDITOR.livePreview; commits belong to the core "
            "change binding)")
        self.assertIn(
            "EDITOR.livePreview(", self.asset,
            "character counters must update via the livePreview registry")
        # Live character counters exist for both layers.
        self.assertTrue(
            _has_markup(self.asset, "data-charcount", "text_dramatic")
            and _has_markup(self.asset, "data-charcount", "text_teaching"),
            "both layers must expose live character counters")

    # ------------------------------------------------------------------
    # 3. Claim chips resolve LIVE (C groundwork)
    # ------------------------------------------------------------------

    def test_claim_chips_live(self):
        """Claim chips read bundle.citations + approval_status for the live
        badge (strict approved semantics), handle the MISSING state for
        unresolved ids, show review_tier, and click through the
        EDITOR.ui.claimFocus hook (consumed by the claims panel 07.1-12)."""
        self.assertTrue(
            "citations" in self.asset and "approval_status" in self.asset,
            "chips must resolve against bundle.citations via "
            "approval_status")
        # Strict gate predicate — the same semantics as rpg/citations.py.
        self.assertIn('status === "approved"', self.asset,
                      "approved must be compared EXACTLY (no truthy "
                      "shortcut; rpg/citations.py:100-109)")
        self.assertIn("pending", self.asset)
        self.assertIn("rejected", self.asset)
        # MISSING state handled (e.g. PLACEHOLDER_PHASE8 is not in the
        # registry — the sanctioned residual must render as MISSING).
        self.assertIn("MISSING", self.asset)
        self.assertIn("review_tier", self.asset,
                      "chips must show the claim's review_tier")
        # The claimFocus hook (safe no-op default; 07.1-12 consumes).
        self.assertIn("EDITOR.ui.claimFocus", self.asset)
        # PLACEHOLDER_PHASE8 sanctioned-residual context.
        self.assertTrue(
            "PLACEHOLDER_PHASE8" in self.asset
            and "fa.stub" in self.asset and "alc.stub" in self.asset,
            "the sanctioned residual context (PLACEHOLDER_PHASE8 on "
            "fa.stub / alc.stub only) must be present")

    # ------------------------------------------------------------------
    # 4. is_ending: ABSENT, never null
    # ------------------------------------------------------------------

    def test_is_ending_absent_not_null(self):
        """The select handler removes the is_ending key entirely when set to
        none (the schema keeps is_ending ABSENT on non-endings —
        model.py:250-252) and NEVER writes is_ending: null."""
        # The select exists with the mandated options.
        self._assert_markup(
            self.asset, "data-role", "ending-select",
            "the is_ending select must be present")
        for tier in ("true", "good", "normal", "bad"):
            self.assertIn(
                '"%s"' % tier, self.asset,
                "the ending select must offer tier %s" % tier)
        # The removal: an executable `delete <var>.is_ending` on the
        # is_ending path (the ONLY shape-change allowed, touching ONLY that
        # key per the B11 mutator contract).
        self.assertRegexpMatches(
            self.asset, r"delete\s+\w+\.is_ending",
            "the none option must REMOVE the is_ending key (absent, never "
            "null)")
        # Never a null write.
        self.assertIsNone(
            re.search(r"is_ending[\"']?\s*:\s*null", self.asset),
            "the form must never write is_ending: null")
        self.assertIsNone(
            re.search(r"nodeSet\([^)]*[\"']is_ending[\"']\s*,\s*null",
                      self.asset),
            "the form must never nodeSet is_ending to null")

    # ------------------------------------------------------------------
    # 5. B9 reminder — present and conditioned on endings
    # ------------------------------------------------------------------

    def test_b9_reminder(self):
        """The Phase-12 reminder is present and rendered only for ending
        nodes (gated on the derived tier, never a stored field)."""
        self.assertIn(
            B9_REMINDER_HEAD, self.asset,
            "the B9 reminder sentence head must be present")
        self.assertIn(
            B9_REMINDER_TAIL, self.asset,
            "the B9 reminder sentence tail (with the roadmap B9 citation) "
            "must be present")
        # Conditioning: inside renderIdentityHeader the reminder render sits
        # BEHIND a tier check derived from EDITOR.endingTier (is_ending
        # ONLY). Extract the function body and assert the ordering.
        m = re.search(
            r"function renderIdentityHeader\(node, fname\) \{([\s\S]*?)\n  \}",
            self.asset)
        self.assertTrue(
            m, "renderIdentityHeader not found in the asset")
        body = m.group(1)
        tier_idx = body.find("EDITOR.endingTier(node)")
        banner_idx = body.find("B9_REMINDER_TEXT")
        self.assertGreaterEqual(tier_idx, 0,
                                "the header must derive the tier")
        self.assertGreaterEqual(banner_idx, 0,
                                "the header must render the B9 banner")
        self.assertLess(
            tier_idx, banner_idx,
            "the B9 banner must be gated behind the derived tier "
            "(conditioned on endings)")
        gate_idx = body.find("if (tier)")
        self.assertGreaterEqual(
            gate_idx, 0,
            "the tier check must guard the banner render")

    # ------------------------------------------------------------------
    # 6. B11 unknown-key guard (scoped `delete` review)
    # ------------------------------------------------------------------

    def test_unknown_keys_guarded(self):
        """The read-only extra-keys section exists, and a scoped review of
        EVERY `delete` occurrence passes this allowlist:
          ALLOWED —
            (a) comment lines (* or //): prose like "never deleted" /
                "never removed" is documentation, not code;
            (b) exactly `delete <var>.is_ending;` — the plan-mandated
                is_ending key REMOVAL (absent-not-null, touches only that
                key).
          Anything else (any delete that could remove an unknown key) fails.
        """
        # The guard section exists with the read-only contract markers.
        self.assertIn("Extra keys (B11 guard)", self.asset)
        self.assertIn("KNOWN_NODE_KEYS", self.asset)
        self.assertIn("read-only", self.asset.lower())
        # Detection whitelist covers the full known schema (keys written
        # strict-JSON so the battery can parse the literal).
        for key in ("text_dramatic", "text_teaching", "claim_ids", "tags",
                    "on_enter", "choices", "is_ending"):
            self.assertIn('"%s": true' % key, self.asset,
                          "KNOWN_NODE_KEYS must whitelist %s" % key)
        # Scoped delete review (the allowlist is documented above).
        executable = []
        for line in self.asset.splitlines():
            if not re.search(r"\bdelete\b", line):
                continue
            stripped = line.strip()
            if stripped.startswith("*") or stripped.startswith("//"):
                continue  # (a) comment prose
            if re.search(r"delete\s+\w+\.is_ending\s*;", stripped):
                continue  # (b) the plan-mandated is_ending removal
            executable.append(line)
        self.assertEqual(
            executable, [],
            "found executable delete(s) outside the allowlist — the form "
            "must NEVER delete unknown keys: %r" % executable)

    # ------------------------------------------------------------------
    # 7. ES5 discipline + emitted page inlining
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

    def test_emitted_page_inlines_form_asset(self):
        """The emitted story_editor.html inlines the form asset with the
        plan's verify-step strings, in pipeline order (after 30_graph.js,
        before the shell bootstrap)."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        block = self._form_block()
        # The plan's Task-1 verify strings, all present in the emitted page.
        for required in ("text_dramatic", "text_teaching", "claim_ids",
                         "is_ending", "data-field", "B9_REMINDER_TEXT",
                         "Extra keys (B11 guard)", "EDITOR.ui.claimFocus"):
            self.assertIn(required, block,
                          "emitted form block must contain %r" % required)
        # The data-field bindings + the ending select (escape-tolerant).
        self.assertTrue(
            _has_markup(block, "data-field", "text_dramatic")
            and _has_markup(block, "data-field", "text_teaching"),
            "the emitted page must carry both data-field bindings")
        self.assertTrue(
            _has_markup(block, "data-role", "ending-select"),
            "the emitted page must carry the is_ending select")
        # The exact B9 reminder reached the page (both fragments).
        self.assertIn(B9_REMINDER_HEAD, block)
        self.assertIn(B9_REMINDER_TAIL, block)
        # Pipeline order: 30_graph.js -> 40_form.js -> shell bootstrap.
        graph_idx = self.html.find("/* asset: 30_graph.js")
        form_idx = self.html.find("/* asset: 40_form.js")
        boot_idx = self.html.rfind("EDITOR.runInits();")
        self.assertGreaterEqual(graph_idx, 0)
        self.assertGreaterEqual(form_idx, 0)
        self.assertGreaterEqual(boot_idx, 0)
        self.assertLess(graph_idx, form_idx,
                        "the graph asset must inline before the form")
        self.assertLess(form_idx, boot_idx,
                        "the form asset must inline before the bootstrap")


if __name__ == "__main__":
    unittest.main()
