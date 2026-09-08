"""Unit battery for tests/script_blocks.py -- the browser-faithful <script>
block extractor that replaced the naive
``re.findall(r"<script>(.*?)</script>", html, re.S)`` in the emitted-HTML
tests (CodeQL py/bad-tag-filter alerts #8 and #9).

Every expectation below was pinned by an adversarial probe against
Python 3.6.9's html.parser (recorded in
.planning/debug/resolved/codeql-bad-tag-filter.md). The load-bearing
contract: the helper extracts EVERY script region a browser would
execute, and NEVER drops browser-executed content -- where Python 3.6's
tokenizer merges regions (attributed end tags, "</ script>" literal
text), the collected text is a SUPERSET, which is the safe direction for
scan-for-bad-pattern tests.

Pure WSL python3.6 -- stdlib only, hand-built HTML strings. The real
generator emits bare classic tags (pinned elsewhere); these tests pin
the adversarial shapes the old regex silently missed.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import script_blocks  # noqa: E402  (tests sibling helper)

extract = script_blocks.extract_script_blocks


class TestCitedBypassesCaptured(unittest.TestCase):
    """The CodeQL-cited shapes: the old regex returned [] (silent pass)
    on every one of these; the helper must extract the block."""

    def test_uppercase_attributed_open_tag(self):
        blocks = extract('<SCRIPT foo="bar">alert(1)</SCRIPT>')
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].attrs, {"foo": "bar"})
        self.assertEqual(blocks[0].text, "alert(1)")

    def test_type_attribute_open_tag(self):
        blocks = extract('<script type="text/javascript">alert(1)</script>')
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].attrs, {"type": "text/javascript"})
        self.assertEqual(blocks[0].text, "alert(1)")

    def test_whitespace_inside_open_tag(self):
        blocks = extract("<script >x</script >")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].attrs, {})
        self.assertEqual(blocks[0].text, "x")

    def test_newline_and_unquoted_module_attr(self):
        blocks = extract("<script\n type=module>y</script >")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].attrs, {"type": "module"})
        self.assertEqual(blocks[0].text, "y")

    def test_self_closing_slash_opens_region(self):
        # Browsers open the script at <script/> (script is not a void
        # element); Python 3.6 needs the handle_startendtag override.
        blocks = extract("<script/>alert(1)</script>")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].text, "alert(1)")

    def test_comment_end_bang_then_live_script(self):
        # --!> ends a comment for browsers; Python 3.6's tokenizer needs
        # the "--!>" -> "-->" preprocess (the old regex scanned one big
        # comment and found nothing: silent pass).
        blocks = extract("<!-- c --!><SCRIPT>alert(1)</SCRIPT>-->")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].text, "alert(1)")

    def test_end_tag_with_attributes_overcaptures(self):
        # Browsers close at </script foo="bar">; Python 3.6 treats the
        # tag text as raw content and keeps scanning until the next bare
        # </script>. Collected text is a SUPERSET (merge) -- the safe
        # direction: browser-executed code is never dropped.
        blocks = extract('<script>a</script foo="bar">b</script>')
        self.assertEqual(len(blocks), 1)
        self.assertIn("a", blocks[0].text)
        self.assertIn("b", blocks[0].text)

    def test_cited_end_tag_attrs_full_shape(self):
        blocks = extract('<SCRIPT foo="bar">alert(1)</SCRIPT foo="bar">')
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].attrs, {"foo": "bar"})
        self.assertIn("alert(1)", blocks[0].text)

    def test_unterminated_script_flushed_at_eof(self):
        # Browsers execute to EOF; Python 3.6 drops the trailing CDATA
        # text. The helper must flush the unconsumed rawdata tail.
        blocks = extract("<script>alert(1)")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].text, "alert(1)")

    def test_end_tag_space_form_never_drops_content(self):
        # "</ script>" is literal JS text for browsers (an HTML5 end tag
        # needs an ASCII alpha directly after "</"); the region must
        # stay open so the executed text is never dropped.
        blocks = extract("<script>a</ script>alert(1)</script>")
        self.assertEqual(len(blocks), 1)
        self.assertIn("alert(1)", blocks[0].text)


class TestExtractionPrecision(unittest.TestCase):
    """Regions a browser does NOT execute must not be collected, and the
    real generator shape must round-trip unchanged."""

    def test_stray_end_tag_ignored(self):
        self.assertEqual(extract("</script>alert(1)"), [])

    def test_script_inside_real_comment_not_collected(self):
        # A commented-out script does not execute; collecting it would
        # only be over-scanning -- the helper is precise here.
        self.assertEqual(
            extract("<!-- <script>alert(1)</script> -->"), [])

    def test_cdata_section_script_not_collected(self):
        # <![CDATA[ is a bogus comment in text/html; the script inside
        # never executes.
        self.assertEqual(
            extract("<![CDATA[<script>alert(1)</script>]]>"), [])

    def test_raw_cdata_content_undecoded(self):
        src = "<script>if (a < b && c > d) alert(1);</script>"
        blocks = extract(src)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].text, "if (a < b && c > d) alert(1);")

    def test_gt_inside_quoted_attr_value(self):
        blocks = extract('<script data-x="a>b">alert(1)</script>')
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].attrs, {"data-x": "a>b"})
        self.assertEqual(blocks[0].text, "alert(1)")

    def test_bare_lt_in_preceding_text(self):
        blocks = extract("1 < 2 <script>alert(1)</script>")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].text, "alert(1)")

    def test_dashes_in_script_content_untouched(self):
        # JS decrement/operators with dashes must survive verbatim.
        src = "<script>i--; if (i-->0) alert(1);</script>"
        blocks = extract(src)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].text, "i--; if (i-->0) alert(1);")

    def test_multiple_bare_blocks_in_order(self):
        # The real generator's shape: bare lowercase classic tags.
        src = ("<p>hi</p>\n<script>\nwindow.x = 1;\n</script>\n"
               "<script>y</script>")
        blocks = extract(src)
        self.assertEqual([b.text for b in blocks],
                         ["\nwindow.x = 1;\n", "y"])
        self.assertEqual([b.attrs for b in blocks], [{}, {}])


class TestModuleAttrIdiom(unittest.TestCase):
    """The consumer tests detect module scripts via
    (attrs.get("type") or "").lower() == "module"; pin that idiom
    against the case variants HTMLParser reports (attr NAMES are
    lowercased by the tokenizer, VALUES keep their raw case)."""

    def test_module_variants_detected_case_insensitively(self):
        blocks = extract("<script TYPE=MODULE>x</script>"
                         "<script type=module>y</script>")
        self.assertEqual(len(blocks), 2)
        for block in blocks:
            self.assertEqual(
                (block.attrs.get("type") or "").lower(), "module")

    def test_entity_encoded_module_value_decoded(self):
        # Browsers entity-decode attribute values; the tokenizer does
        # too, so an obfuscated type value must still be detected.
        blocks = extract("<script type=&#109;odule>x</script>")
        self.assertEqual(
            (blocks[0].attrs.get("type") or "").lower(), "module")

    def test_classic_type_not_flagged_as_module(self):
        blocks = extract('<script type="text/javascript">x</script>')
        self.assertNotEqual(
            (blocks[0].attrs.get("type") or "").lower(), "module")

    def test_missing_type_attr_defaults_to_classic(self):
        blocks = extract("<script>x</script>")
        self.assertEqual((blocks[0].attrs.get("type") or "").lower(), "")


if __name__ == "__main__":
    unittest.main()
