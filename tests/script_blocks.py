"""Browser-faithful <script> block extraction for emitted-HTML tests.

CodeQL py/bad-tag-filter (alerts #8, #9): the naive
``re.findall(r"<script>(.*?)</script>", html, re.S)`` only matches bare,
lowercase tags, while browsers also execute ``<SCRIPT foo="bar">``,
``<script type="text/javascript">`` and friends -- tests built on such a
regex can silently pass while a browser executes an unexamined block.
This module replaces the regex with the stdlib HTML tokenizer
(html.parser.HTMLParser; script is a CDATA element, so block content
arrives as raw text, never entity-decoded).

Behavior verified against Python 3.6.9 by adversarial probe (recorded in
.planning/debug/resolved/codeql-bad-tag-filter.md); divergences from
browser tokenization and why each remaining one is safe:

- Open tags: any case, any attributes, any intra-tag whitespace are
  captured (HTMLParser lowercases tag/attr names). Browser-faithful.
- ``<script/>``: browsers treat this as an OPEN script tag (script is
  not a void element); Python 3.6 takes the XHTML self-closing branch
  and never enters CDATA mode. We re-enter CDATA mode manually.
- End tags with attributes (``</script foo="bar">``): browsers close the
  block there; Python 3.6 treats the tag text as raw content and keeps
  scanning until the next bare ``</script>`` (or EOF). The collected
  text is a SUPERSET of what the browser executes (adjacent regions
  merge) -- over-inclusive, the safe direction for scan-for-bad-pattern
  tests: it can never cause a miss.
- Unterminated script at EOF: browsers execute the content; Python 3.6
  drops the trailing CDATA text. We flush the unconsumed rawdata tail.
- ``--!>`` comment-end-bang: browsers end a comment there; Python 3.6
  does not, and would swallow a live script following it. We preprocess
  ``--!>`` to ``-->``. (Also touches ``--!>`` inside script text by
  dropping one ``!`` -- it cannot create or destroy any of the JS
  patterns the tests scan for: =>, let, const, top-level import.)
- A script inside a real comment is NOT collected (it does not execute).

Pinned to Python 3.6.9 (the repo's test interpreter): the helper relies
on html.parser's CDATA-mode methods (set_cdata_mode) and rawdata
retention after close(), both stable in the 3.6 line.
"""
import collections
import html.parser
import re

# One script region: opening-tag attrs (names lowercased, values entity-
# decoded -- matching browsers) + raw unentity-decoded text content.
ScriptBlock = collections.namedtuple("ScriptBlock", ["attrs", "text"])


class _ScriptCollector(html.parser.HTMLParser):
    """Collects every <script> region as ScriptBlock(attrs, raw text)."""

    def __init__(self):
        # type: () -> None
        html.parser.HTMLParser.__init__(self)
        self.blocks = []    # type: list
        self._attrs = None  # type: object  # dict while inside a script
        self._parts = []    # type: list

    # -- script open ------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if tag == "script" and self._attrs is None:
            self._open(attrs)

    def handle_startendtag(self, tag, attrs):
        # Browsers: <script/> OPENS a script element (script is not a
        # void element, the stray "/" is ignored); Python 3.6 takes the
        # XHTML self-closing branch and never enters CDATA mode, so the
        # following raw text would not be captured. Re-enter CDATA mode
        # ourselves -- exactly what parse_starttag does for an open tag.
        if tag == "script" and self._attrs is None:
            self._open(attrs)
            self.set_cdata_mode(tag)

    def _open(self, attrs):
        self._attrs = dict(attrs)
        self._parts = []

    # -- content ----------------------------------------------------------
    def handle_data(self, data):
        if self._attrs is not None:
            self._parts.append(data)

    # -- script close -----------------------------------------------------
    def handle_endtag(self, tag):
        if tag == "script" and self._attrs is not None:
            self._close()

    def _close(self):
        self.blocks.append(
            ScriptBlock(self._attrs, "".join(self._parts)))
        self._attrs = None
        self._parts = []

    def set_cdata_mode(self, elem):
        # Python 3.6's default CDATA scanner is r'</\s*%s' -- it would
        # also end the region at "</ script>", which browsers treat as
        # literal JS text (an HTML5 end tag must have an ASCII alpha
        # directly after "</"). Narrowing to r'</%s' keeps the region
        # open there; a premature close could DROP browser-executed
        # content (the under-inclusive direction we must never risk).
        self.cdata_elem = elem.lower()
        self.interesting = re.compile(r"</%s" % self.cdata_elem, re.I)

    def close(self):
        # HTMLParser.close() runs the end-of-feed pass; afterwards
        # self.rawdata holds whatever it could not consume -- for an
        # unterminated <script> that is the browser-executed remainder
        # (Python 3.6 drops it in CDATA mode; browsers run it). Flush it
        # as content so the block text is a superset, never a subset.
        html.parser.HTMLParser.close(self)
        if self._attrs is not None:
            if self.rawdata:
                self._parts.append(self.rawdata)
            self._close()


def extract_script_blocks(html_text):
    # type: (str) -> list
    """Return every <script> region a browser would execute, in document
    order, as ScriptBlock(attrs, text) with RAW (unentity-decoded) text.

    See the module docstring for the verified tokenizer divergences and
    why each remaining one is safe (over-inclusive) for scan-style tests.
    """
    # Python 3.6's tokenizer does not know the HTML5 comment-end-bang
    # "--!>"; browsers DO end a comment there and a script following it
    # is live. Normalize so the tokenizer sees the same comment ends.
    collector = _ScriptCollector()
    collector.feed(html_text.replace("--!>", "-->"))
    collector.close()
    return collector.blocks
