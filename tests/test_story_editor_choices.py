"""Structural choices-editor test battery for the Phase 7.1 editor choices
asset (07.1-15 Task 2).

Covers (over tools/story_editor_assets/42_choices.js and the emitted page):
- the goto dropdown IS the B5 connection/direction editor: a select over
  ALL node ids grouped by file (manifest order via bundle.order, optgroup
  per file) with the current target preselected, the "(none — invalid)"
  empty option (an empty target is invalid BY DESIGN — dangling_divert
  fires and stays visible), and a visible dangling-target group; goto
  edits commit through EDITOR.choiceUpdate with the field name "goto"
  (test_goto_dropdown_grouped_connection_editor)
- the cond landmine guard: the dict-method hint text (dict-method form
  only — flags.get('x') / visits.get('x', 0); the attribute form silently
  hides the choice at runtime) is present, and the client-side attribute-
  form regex check (the 20_validate.js BROKEN_COND_RE pattern) exists so
  cond_attribute_form surfaces on the row (test_cond_warning)
- the weight determinism pin: weight inputs are gated on the node carrying
  rng:weighted or any choice already carrying weight, the lock note names
  tca.shuffle + the determinism pin, and the weight_outside_shuffle
  defense note exists (test_weight_restriction)
- the single-Continue guard: delete-confirm warns BEFORE a delete would
  leave <2 choices on a non-ending non-stub node, and the live count hint
  names the single_continue rule with the "Continue" label check
  (test_single_continue_guard)
- the effects editor is STRUCTURED (a set/incr key/value list editor, not
  a free-JSON textarea — the asset contains no <textarea> at all) and
  commits through the named-field mutator choiceUpdate(..., "effects",
  ...) with JSON-literal value parsing (test_effects_editor_structured)
- the B11 unknown-key contract: all mutations flow through the 00_core
  mutators (choiceAdd / choiceUpdate / choiceDelete) or local apply()
  mutators that touch only named fields (removeChoiceField deletes one
  named key; choiceMove is splice-only reorder) — the asset NEVER rebuilds
  the choices array through nodeSet (no whitelist rebuild)
  (test_unknown_choice_keys_b11)
- ES5 discipline for the asset + the emitted page inlines the choices
  asset in pipeline order (after 40_form.js, before the shell bootstrap)
  with the plan's verify-step strings: goto / cond / weight / effects,
  the choice-tag vocabulary, the dict-method hint, and the reorder
  controls (test_es5_discipline,
  test_emitted_page_inlines_choices_asset)

Markup-attribute greps are ESCAPE-TOLERANT: the asset builds HTML inside
ES5 double-quoted string literals, so attributes may appear either plain
(data-ch-act="up") or JS-escaped (data-ch-act=\"up\") — both spell the
same emitted markup.

Pure WSL python3.6 — stdlib only; the generator is subprocessed once per
test class via setUpClass into a temp dir using --output (same conventions
as tests/test_story_editor_form.py: REPO_ROOT via __file__,
subprocess.run with PIPE streams — NOT capture_output, which is 3.7+).
The battery greps only THIS plan's asset, so it stays robust while the
parallel Wave-4b agents (43_onenter.js / 50_editscast.js) are in flight.
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
CHOICES_ASSET = os.path.join(
    REPO_ROOT, "tools", "story_editor_assets", "42_choices.js")


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


class TestChoicesAssetStructure(unittest.TestCase):
    """Structural checks over the choices asset + ONE emitted page."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="story_editor_choices_")
        cls.out_path = os.path.join(cls.tmpdir, "story_editor.html")
        cls.proc = run_generator(["--output", cls.out_path])
        cls.html = ""
        if os.path.isfile(cls.out_path):
            cls.html = _read(cls.out_path)
        cls.asset = _read(CHOICES_ASSET) if os.path.isfile(CHOICES_ASSET) else ""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _choices_block(self):
        # type: () -> str
        """Extract the inlined 42_choices.js <script> block from the page."""
        marker = "/* asset: 42_choices.js"
        m_start = self.html.find(marker)
        self.assertGreaterEqual(
            m_start, 0, "42_choices.js asset marker missing from emitted HTML")
        block_open = self.html.rfind("<script>", 0, m_start)
        self.assertGreaterEqual(
            block_open, 0, "choices asset block has no opening <script>")
        block_close = self.html.find("</script>", m_start)
        self.assertGreaterEqual(
            block_close, 0, "choices asset block is unterminated")
        return self.html[block_open:block_close]

    def _assert_markup(self, text, attr, value, msg):
        # type: (str, str, str, str) -> None
        self.assertTrue(
            _has_markup(text, attr, value), msg)

    # ------------------------------------------------------------------
    # 1. The goto dropdown = the B5 connection/direction editor
    # ------------------------------------------------------------------

    def test_goto_dropdown_grouped_connection_editor(self):
        """A select over ALL node ids, grouped by file (manifest order),
        drives goto edits — choices ARE the graph's edges, so this dropdown
        is the connection editor and edge direction is inherent (B5). The
        empty option '(none — invalid)' makes a none-target INVALID by
        design (dangling_divert fires), and a dangling current target gets
        its own visible preselected group."""
        # The asset is a real implementation (the plan's artifact spec asks
        # for >= 150 lines).
        self.assertGreaterEqual(
            len(self.asset.splitlines()), 150,
            "the choices editor must be a real implementation (artifact "
            "spec asks for >= 150 lines)")
        # Header ownership + citations (plan Task 1: ownership 07.1-15;
        # cite the 1.6 schema + the cond/warning sources).
        self.assertIn("07.1-15", self.asset,
                      "the asset header must carry its plan ownership")
        self.assertIn("07.1-RESEARCH-DATA", self.asset,
                      "the asset must cite the 1.6 choice-schema research")
        self.assertIn("interpreter.py:101-135", self.asset,
                      "the asset must cite the cond interpreter source "
                      "(rpg/story/interpreter.py:101-135 via RESEARCH-DATA)")
        # The grouping logic: one <select> over optgroups per file, driven
        # by manifest order (bundle.order), ids through esc().
        self.assertIn("<select", self.asset,
                      "goto editing must be a select dropdown")
        self.assertIn("<optgroup", self.asset,
                      "the goto options must be grouped (per-file optgroups)")
        self.assertIn("b.order", self.asset,
                      "the grouping must iterate manifest order (bundle.order)")
        self._assert_markup(self.asset, "data-ch-field", "goto",
                            "the goto select must bind data-ch-field=goto")
        # The empty option — "(none — invalid)" (the source spells the
        # em-dash as the ES5 \u2014 escape).
        self.assertIn("(none", self.asset)
        self.assertIn(r"(none \u2014 invalid)", self.asset,
                      "the empty option must be spelled '(none — invalid)'")
        # A dangling current target is VISIBLE (its own preselected group).
        self.assertIn("dangling", self.asset,
                      "a dangling goto target must render visibly")
        # goto edits commit through the named-field core mutator.
        self.assertIn('field === "goto"', self.asset,
                      "the change handler must dispatch on the goto field")
        self.assertIn("EDITOR.choiceUpdate(", self.asset,
                      "goto edits must go through EDITOR.choiceUpdate")
        # Add scaffolds {label: "New choice", goto: <first other node>}.
        self.assertIn('"New choice"', self.asset)
        self.assertIn("firstOtherNodeId", self.asset)

    # ------------------------------------------------------------------
    # 2. The cond landmine guard (dict-method mandate)
    # ------------------------------------------------------------------

    def test_cond_warning(self):
        """The dict-method hint text is present and shown with the cond
        field, and the attribute-form regex check (the 20_validate.js
        BROKEN_COND_RE pattern) exists client-side so the Phase-6 SC#3 bug
        class (attribute-form conds silently hide choices) surfaces on the
        row."""
        self.assertIn("dict-method form only", self.asset,
                      "the mandatory dict-method hint text must be present")
        self.assertIn("flags.get('x')", self.asset,
                      "the hint must show the dict-method form flags.get")
        self.assertIn("visits.get('x', 0)", self.asset,
                      "the hint must show the dict-method form visits.get")
        self.assertIn("silently hides the", self.asset,
                      "the hint must state the silent-hiding runtime effect")
        # The client-side attribute-form regex check (same pattern as
        # 20_validate.js BROKEN_COND_RE).
        self.assertIn("BROKEN_COND_RE", self.asset,
                      "the asset must carry the attribute-form check regex")
        self.assertIsNotNone(
            re.search(r"\(flags\|visits\|counters\)\\", self.asset),
            "the regex must detect the (flags|visits|counters).x attribute "
            "form")
        # The violation surfaces as a row chip naming the validator rule.
        self.assertIn("cond_attribute_form", self.asset,
                      "the cond_attribute_form rule id must be surfaced")

    # ------------------------------------------------------------------
    # 3. The weight determinism pin
    # ------------------------------------------------------------------

    def test_weight_restriction(self):
        """Weight inputs are visible ONLY when the node carries rng:weighted
        or any choice already carries weight; otherwise a lock note explains
        that weighted choices exist only on tca.shuffle (the determinism
        pin). The outside-shuffle defense note names weight_outside_shuffle."""
        # The gate: node tag OR existing choice weight.
        self.assertIn("rng:weighted", self.asset,
                      "the gate must check the rng:weighted node tag")
        self.assertIn("weight !== undefined", self.asset,
                      "the gate must check whether any choice carries weight")
        self.assertIn("weightedContext", self.asset,
                      "the weight gating must be a named context check")
        # The lock note (determinism pin).
        self.assertIn("weighted choices exist only", self.asset,
                      "the lock note must state the tca.shuffle-only rule")
        self.assertIn("determinism pin", self.asset,
                      "the lock note must name the determinism pin")
        self.assertIn("tca.shuffle", self.asset,
                      "the lock note must name the single weighted node")
        # The weight input, when unlocked, is a number input on the weight
        # field (escape-tolerant).
        self._assert_markup(self.asset, "data-ch-field", "weight",
                            "the weight input must bind data-ch-field=weight")
        self.assertTrue(
            'type="number"' in self.asset or 'type=\\"number\\"' in self.asset,
            "the weight input must be a number input")
        # Clearing the weight removes the key (absent, never null).
        self.assertIn("removeChoiceField", self.asset,
                      "clearing cond/weight must remove the optional key")
        # Defense-in-depth: a weight outside tca.shuffle names the rule.
        self.assertIn("weight_outside_shuffle", self.asset,
                      "the outside-shuffle note/chip must name the rule")

    # ------------------------------------------------------------------
    # 4. The single-Continue guard
    # ------------------------------------------------------------------

    def test_single_continue_guard(self):
        """Delete-confirm warns BEFORE the delete when it would leave <2
        choices on a non-ending non-stub node (single_continue), and the
        live count hint surfaces the same rule with the 'Continue' label
        check."""
        # Delete with confirm + the <2 warning.
        self.assertIn("window.confirm", self.asset,
                      "delete must confirm before mutating")
        self.assertIn("remaining < 2", self.asset,
                      "the warning must fire when <2 choices would remain")
        self.assertIn("non-ending", self.asset,
                      "the warning must be scoped to non-ending nodes")
        self.assertIn("phase8-stub", self.asset,
                      "the warning must be scoped to non-stub nodes")
        self.assertIn("single_continue", self.asset,
                      "the warning/hint must name the single_continue rule")
        # The live hint checks the exact "Continue" label.
        self.assertIn('label === "Continue"', self.asset,
                      "the hint must detect the single 'Continue' choice")
        self.assertIn("player-facing selection", self.asset,
                      "the hint must state that order is the player-facing "
                      "selection order")

    # ------------------------------------------------------------------
    # 5. The structured effects editor (NOT a free-JSON textarea)
    # ------------------------------------------------------------------

    def test_effects_editor_structured(self):
        """The effects editor is a structured set/incr key/value list
        editor: per-entry rows with key/value inputs, add/remove buttons,
        JSON-literal value parsing — and NO <textarea> anywhere (a raw
        JSON textarea would be the free-JSON anti-pattern the plan bans).
        Commits flow through the named-field mutator."""
        self.assertNotIn("<textarea", self.asset,
                         "effects must NOT be a free-JSON textarea (no "
                         "textarea may exist in the structured editor)")
        # The set/incr structure.
        self.assertIn('"set"', self.asset,
                      "the effects editor must handle the set bucket")
        self.assertIn('"incr"', self.asset,
                      "the effects editor must handle the incr bucket")
        self._assert_markup(self.asset, "data-ch-efs-row", "1",
                            "effects entries must render as structured rows")
        self.assertIn("data-ch-efs-key", self.asset,
                      "each effects row must have a key input")
        self.assertIn("data-ch-efs-val", self.asset,
                      "each effects row must have a value input")
        self.assertIn('"efs-add"', self.asset,
                      "the editor must have add-entry buttons")
        self.assertIn('"efs-remove"', self.asset,
                      "the editor must have per-entry remove buttons")
        # JSON-literal value parsing (true/false/null/number/string).
        self.assertIn("parseEffectValue", self.asset)
        self.assertIn('"true"', self.asset)
        self.assertIn('"false"', self.asset)
        # Commits through the named-field mutator.
        self.assertIn('choiceUpdate(fname, nid, idx, "effects"', self.asset,
                      "effects edits must go through EDITOR.choiceUpdate "
                      "with the named effects field")
        # Schema citation (interpreter.py:137-154 applies effects).
        self.assertIn("interpreter.py:137-154", self.asset)

    # ------------------------------------------------------------------
    # 6. The B11 unknown-key contract
    # ------------------------------------------------------------------

    def test_unknown_choice_keys_b11(self):
        """Mutators touch ONLY named fields: all mutations flow through the
        core choiceAdd/choiceUpdate/choiceDelete or local apply() mutators
        (splice-only reorder; single named-key removal). The asset NEVER
        rebuilds the choices array through nodeSet — no whitelist rebuild
        anywhere, so unknown choice keys round-trip untouched."""
        # The core mutators are used.
        self.assertIn("EDITOR.choiceUpdate(", self.asset)
        self.assertIn("EDITOR.choiceAdd(", self.asset)
        self.assertIn("EDITOR.choiceDelete(", self.asset)
        # NO whole-array rebuild: the asset must never nodeSet the choices
        # array (that would be a whitelist rebuild dropping unknown keys).
        self.assertIsNone(
            re.search(r"nodeSet\([^)]*[\"']choices[\"']", self.asset),
            "the asset must never nodeSet the choices array (B11: no "
            "whitelist rebuild — unknown choice keys must round-trip)")
        # The B11 contract is documented in-source.
        self.assertIn("B11", self.asset)
        self.assertIn("whitelist", self.asset,
                      "the no-whitelist-rebuild contract must be documented")
        self.assertIn("unknown", self.asset)
        # The local mutators are scoped: named-key removal + splice-only
        # reorder.
        self.assertIn("delete c[field]", self.asset,
                      "removeChoiceField must delete ONLY the named key")
        self.assertIn("splice(from, 1)", self.asset,
                      "choiceMove must reorder by splice (no rebuild)")
        self.assertIn("splice(to, 0", self.asset,
                      "choiceMove must reinsert by splice (no rebuild)")

    # ------------------------------------------------------------------
    # 7. ES5 discipline
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
    # 8. Emitted page: pipeline order + the plan's verify strings
    # ------------------------------------------------------------------

    def test_emitted_page_inlines_choices_asset(self):
        """The emitted story_editor.html inlines the choices asset with the
        plan's verify-step strings — goto / cond / weight / effects, the
        choice-tag vocabulary strings, the dict-method hint, and the
        reorder controls — in pipeline order (after 40_form.js, before the
        shell bootstrap)."""
        self.assertEqual(
            self.proc.returncode, 0,
            "generator failed (rc=%d)\nstdout: %s\nstderr: %s"
            % (self.proc.returncode, self.proc.stdout, self.proc.stderr))
        block = self._choices_block()
        # The plan's Task-1 verify strings, all present in the emitted block.
        for required in ("goto", "cond", "weight", "effects",
                         "dict-method form only", "determinism pin",
                         "single_continue", "endings have no choices"):
            self.assertIn(required, block,
                          "emitted choices block must contain %r" % required)
        # The choice-tag vocabulary (07.1-RESEARCH-DATA 1.5).
        for tag in ("mc:observe", "edit:offer", "edit:unknown", "edit:known",
                    "edit:known_critical", "rng:weighted", "branch:aerobic",
                    "branch:anaerobic", "char:glucose", "char:alc", "char:fa",
                    "cycle_trap", "divert:amino_acid", "divert:fatty_acid",
                    "fermentation:lactic", "fermentation:ethanolic",
                    "fermentation:crisis", "etc:enter", "ending:normal",
                    "stub"):
            self.assertIn(tag, block,
                          "emitted choices block must carry the choice-tag "
                          "vocabulary entry %r" % tag)
        # The reorder controls + add/delete (escape-tolerant).
        self._assert_markup(block, "data-ch-act", "up",
                            "the emitted page must carry move-up controls")
        self._assert_markup(block, "data-ch-act", "down",
                            "the emitted page must carry move-down controls")
        self._assert_markup(block, "data-ch-act", "delete",
                            "the emitted page must carry delete controls")
        self._assert_markup(block, "data-ch-act", "add-choice",
                            "the emitted page must carry the add control")
        # Pipeline order: 40_form.js -> 42_choices.js -> shell bootstrap.
        form_idx = self.html.find("/* asset: 40_form.js")
        choices_idx = self.html.find("/* asset: 42_choices.js")
        boot_idx = self.html.rfind("EDITOR.runInits();")
        self.assertGreaterEqual(form_idx, 0, "40_form.js asset missing")
        self.assertGreaterEqual(choices_idx, 0)
        self.assertGreater(
            choices_idx, form_idx,
            "42_choices.js must inline after 40_form.js (sorted pipeline)")
        self.assertGreater(
            boot_idx, choices_idx,
            "42_choices.js must inline before the shell bootstrap")


if __name__ == "__main__":
    unittest.main()
