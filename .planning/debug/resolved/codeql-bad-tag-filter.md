---
status: resolved
trigger: "CodeQL flags two py/bad-tag-filter (High) alerts on naive <script>...</script> extraction regexes in test files. Fix the flagged sites, verify with adversarial inputs, and commit marking the alert IDs."
created: 2026-09-08T00:00:00Z
updated: 2026-09-08T00:25:00Z
---

## Current Focus

hypothesis: RESOLVED -- root cause confirmed (naive regex misses browser-executed script shapes), fix applied (stdlib HTMLParser helper), all verification green.
test: n/a (resolved)
expecting: n/a
next_action: archive + commit (alert IDs in message)

## Symptoms

expected: Test suite extracts every script block from the generator's emitted HTML and asserts code-quality invariants on each block (ES5-only syntax; no top-level `import`). Tests should examine EVERY script block a browser would execute.
actual: CodeQL py/bad-tag-filter (High) flags the naive regex `re.findall(r"<script>(.*?)</script>", self.html, re.S)` as circumventable — browsers also treat `<SCRIPT foo="bar">`, `<script type="text/javascript">`, `</script foo="bar">` (attributes on end tags), and uppercase names as script tags, so the tests could silently pass while a browser still executes a missed block.
errors: Static analysis only — no runtime errors. Two alerts:
  - Alert #9: tests/test_story_editor_state.py:149, in `test_no_modules_no_arrow_asi_landmines` (asserts no `=>` / `let` / `const` in every script block; also asserts no `type="module"` at line 148)
  - Alert #8: tests/test_story_editor_generator.py:126, in `test_offline_no_external_refs` (asserts no top-level `import` in any classic script block; separately asserts no `<script src=` / `<link>` / `type="module"` above it)
reproduction: Open GitHub Security tab → CodeQL alerts #8 and #9 on repo molmdl/RPG_tale-of-C (main branch), rule py/bad-tag-filter.
started: Alerts opened 4 days ago (#8) and 3 days ago (#9) — i.e., when these two test files landed. Never clean.

## Eliminated

- hypothesis: stdlib html.parser.HTMLParser (3.6.9) is browser-faithful for script extraction out of the box
  evidence: probe /tmp/opencode/probe_htmlparser.py -- 3 divergences found: (E) `<!-- c --!><SCRIPT>alert(1)</SCRIPT>-->` parses as ONE comment (`' c --!><SCRIPT>alert(1)</SCRIPT>'`), the live script is swallowed; (F) `<script/>` fires handle_startendtag and never enters CDATA mode, so following content is not captured as script (browsers open the script there); (H) unterminated `<script>alert(1)` at EOF delivers NO trailing data (parser drops it in CDATA mode). Confirmed GOOD natively: uppercase+attributed open tags (A), attrs preserved (B/M), whitespace forms (C), raw CDATA content undecoded (I), stray end tag ignored (J), script inside real comment not collected (K).
  timestamp: 2026-09-08T00:10:00Z
- hypothesis: `</script foo="bar">` end tag needs special handling to avoid a miss
  evidence: probe cases D/L -- 3.6 treats an attributed end tag as raw DATA and continues CDATA until the next bare `</script>` (or EOF), so the collected block text is a SUPERSET of what the browser executes (merged blob). Over-inclusive = safe direction for scan-for-bad-pattern tests; cannot cause a miss. No fix needed, only documentation.
  timestamp: 2026-09-08T00:11:00Z

- timestamp: 2026-09-08T00:14:00Z
  checked: probe2 /tmp/opencode/probe_helper.py -- helper candidate vs OLD regex on 21 adversarial cases; rawdata-after-close check
  found: OLD regex returns [] (silent pass) on every cited bypass shape (A uppercase+attrs, B type attr, C whitespace forms, E --!> then live script, F <script/>, L full end-tag-attrs shape); NEW helper catches all of them. rawdata after close() confirmed to hold the unconsumed tail ('alert(1)', 'alert(1)</SCRIPT foo="bar">') -> EOF flush design works. Real generator shape (S) byte-identical OLD vs NEW -> zero regression for the actual pipeline. NEW more precise than OLD on non-executing regions (K script-in-comment, O CDATA section -> correctly excluded, browsers do not execute them). R case ('</ script>' = literal text in browsers) stays ONE block thanks to the narrowed interesting regex -> no under-inclusive miss. N1/N2 abrupt comments <!-->/<!--->: Python treats them as data, script after collected -- matches browsers, no preprocess needed. G: '--!>' inside script text becomes '-->' (1-char, cannot affect the scanned JS patterns). P ('>' in quoted attr) handled.
  implication: helper verified; the 3 stdlib gaps (startendtag, --!>, EOF tail) plus the interesting-regex narrowing are all load-bearing and probed
- timestamp: 2026-09-08T00:15:00Z
  checked: repo-wide scan for other script-tag regex/strfind extraction sites (scope discipline)
  found: exactly 2 regex tag-extraction sites repo-wide = the 2 flagged ones. All other `<script` uses are plain str.rfind/str.find position lookups for KNOWN asset blocks (state.py:87-93, boot/choices/claims/editscast/form/graph/lifecycle/load/onenter/save/trace) -- several explicitly assert the block is a bare classic `<script>` (generator.py:254-256). One non-flagged absence-assert regex remains: generator.py:113 `re.search(r"<script[^>]*\ssrc=", ...)` (asserts an external ref is ABSENT; not a content extraction; CodeQL did not flag it).
  implication: fix ONLY the 2 flagged sites; all others recorded here as observed-not-flagged, left alone (possible follow-up)
- timestamp: 2026-09-08T00:20:00Z
  checked: py_compile (4 files) + NEW helper battery (22 tests) + AFTER run of both modified modules + full story_editor family + differential on the REAL generator output
  found: py_compile clean; helper 22/22 OK; modified modules 13/13 OK (same count as BEFORE); family 232/232 OK. Differential on real output: 15 blocks both; OLD[1:] == NEW[1:] byte-identical; OLD[0] == comment-junk + NEW[0] -- the emitted page's template comment ("<!-- ASSET SLOT: ... one classic inline <script> block per ... -->") contains literal `<script>` text, so the OLD regex merged comment prose with the entire 00_core.js into its "block 0". NEW extracts 15 clean real blocks (14 assets + bootstrap), attrs all {} (classic), none module.
  implication: fix makes the tests strictly MORE correct on the real page (every real block examined as its own unit); zero regression on the real pipeline
- timestamp: 2026-09-08T00:22:00Z
  checked: post-fix repo grep for remaining tag-extraction regexes
  found: only prose mentions of the old regex inside comments/docstrings (script_blocks.py:4, test_script_blocks.py:3, comment lines in the two test files) -- not code expressions, not CodeQL-flaggable
  implication: both flagged sites are gone from code; residual CodeQL risk limited to the helper's internal CDATA scanner `re.compile(r"</%s" % elem)` (an open-ended end-tag prefix inside a parser subclass, not a tag-shape extraction filter -- low re-flag risk; noted for triage if a future run disagrees)

- timestamp: 2026-09-08T00:05:00Z
  checked: flagged sites (state.py:149, generator.py:126) + prior-art session + prior fix commit 65bcc2d
  found: both sites use `re.findall(r"<script>(.*?)</script>", self.html, re.S)` exactly as reported; prior session uses same file structure + Per-Alert table; commit 65bcc2d format: `fix(security): ... (Fixes CodeQL alerts #1, ..., #7)` with Root cause / Alerts fixed / Fix / Verification body sections
  implication: diagnosis matches report; follow the same session + commit conventions
- timestamp: 2026-09-08T00:06:00Z
  checked: BEFORE test run `python3.6 -m unittest tests.test_story_editor_state tests.test_story_editor_generator -v`
  found: 13/13 OK in 2.672s (green) -- confirms alerts are static-analysis-only, no runtime failures
  implication: fix must keep this suite green; regression baseline established
- timestamp: 2026-09-08T00:07:00Z
  checked: repo conventions (tests/__init__.py, sys.path precedent, no .github/workflows)
  found: tests/__init__.py is EMPTY; test files already use `sys.path.insert(0, DIR); import module  # noqa: E402` to import siblings (test_story_editor_serializer_js.py:64, test_story_editor_json.py:62); no CI workflow dir
  implication: helper as tests/script_blocks.py + sys.path.insert(HERE) + plain `import script_blocks` matches established precedent and works under both `python3.6 -m unittest tests.X` and direct-file execution
- timestamp: 2026-09-08T00:10:00Z
  checked: adversarial probe of python3.6.9 html.parser (12 cases, see Eliminated for divergences)
  found: HTMLParser handles uppercase/attributed/whitespace open tags, CDATA raw text, comment-wrapped scripts natively; 3 gaps to patch: `--!>` comment end (preprocess), `<script/>` (manual set_cdata_mode), EOF tail flush (rawdata after close)
  implication: helper = HTMLParser subclass + `--!>` preprocess + startendtag override + close() flush; feasible on 3.6.9

## Resolution

root_cause: Both tests extracted script blocks with `re.findall(r"<script>(.*?)</script>", html, re.S)`, which only matches bare lowercase `<script>`...`</script>` pairs. Browsers also execute `<SCRIPT foo="bar">`, `<script type="text/javascript">`, `<script/>`, scripts after a `--!>` comment end, and unterminated scripts at EOF -- so the tests could silently pass (blocks list == []) while a browser executed an unexamined block (CodeQL py/bad-tag-filter #8, #9). Bonus finding: the old regex was ALSO imprecise on the real emitted page -- its "block 0" was template-comment prose (containing literal `<script>` text) merged with the whole 00_core.js block.
fix: New stdlib-only helper `tests/script_blocks.py`: `extract_script_blocks(html) -> [ScriptBlock(attrs, text)]` built on `html.parser.HTMLParser` (script is a CDATA element -> content arrives raw). Verified against Python 3.6.9 by adversarial probe and patched for the 4 stdlib gaps: (1) `handle_startendtag` re-opens CDATA for `<script/>`; (2) `--!>` preprocessed to `-->` so comment ends match browsers; (3) narrowed CDATA scanner regex `</script` (no `\s*` after `</`) so `</ script>` (literal JS text for browsers) can never close a region early and drop executed content; (4) `close()` flushes the unconsumed `rawdata` tail (browsers execute an unterminated script to EOF; 3.6 drops it). End tags with attributes merge into a superset blob (over-inclusive = safe direction, documented). Both flagged tests now use the helper and additionally assert `(attrs.get("type") or "").lower() != "module"` per block (catches TYPE=MODULE / unquoted / entity-encoded variants), keeping their existing assertion messages and per-block regexes over `block.text`. New battery `tests/test_script_blocks.py` (22 tests) pins every bypass shape + precision cases (comments/CDATA sections excluded; real generator shape byte-stable).
verification: (1) py_compile clean on all 4 touched files (python3.6). (2) BEFORE run recorded: 13/13 OK; AFTER run: 13/13 OK on the two modified modules. (3) New helper battery 22/22 OK -- includes the exact regression the alerts were about (`<SCRIPT foo="bar">`-style blocks the old regex silently missed). (4) Full story_editor family 232/232 OK. (5) Differential on the REAL generator output: 15/15 blocks, attrs all classic, none module; blocks 1-14 byte-identical to the old regex, block 0 now clean (old merged comment junk + 00_core.js). (6) Adversarial old-vs-new probe table recorded below: OLD returns [] (silent pass) on every cited bypass; NEW extracts the block each time.
files_changed: ["tests/script_blocks.py", "tests/test_script_blocks.py", "tests/test_story_editor_state.py", "tests/test_story_editor_generator.py"]

## Adversarial Probe Record (old regex vs new helper)

Verified on python3.6.9 (probes at /tmp/opencode/probe_htmlparser.py, probe_helper.py -- NOT committed):

| Input shape | OLD `re.findall(r"<script>(.*?)</script>")` | NEW helper |
|---|---|---|
| `<SCRIPT foo="bar">alert(1)</SCRIPT>` | `[]` (silent pass) | 1 block, attrs {foo: bar}, text `alert(1)` |
| `<script type="text/javascript">alert(1)</script>` | `[]` (silent pass) | 1 block, attrs {type: text/javascript} |
| `<script >x</script >` / `<script\n type=module>y</script >` | `[]` (silent pass) | 1 block each, attrs preserved |
| `<script/>alert(1)</script>` | `[]` (silent pass) | 1 block, text `alert(1)` |
| `<!-- c --!><SCRIPT>alert(1)</SCRIPT>-->` | `[]` (silent pass) | 1 block, text `alert(1)` |
| `<SCRIPT foo="bar">alert(1)</SCRIPT foo="bar">` | `[]` (silent pass) | 1 block, text superset containing `alert(1)` |
| `<script>alert(1)` (unterminated at EOF) | `[]` (silent pass) | 1 block, text `alert(1)` (rawdata tail flushed) |
| `<script>a</script foo="bar">b</script>` | `['a</script foo="bar">b']` | identical superset (merge; safe direction) |
| `<script>a</ script>alert(1)</script>` | `['a</ script>alert(1)']` | identical superset (region stays open) |
| `<!-- <script>alert(1)</script> -->` | `['alert(1)']` (over-scan) | `[]` (does not execute; precise) |
| `<![CDATA[<script>alert(1)</script>]]>` | `['alert(1)']` (over-scan) | `[]` (bogus comment; precise) |
| real generator shape (bare classic tags) | 15 blocks | 15 blocks, texts 1-14 byte-identical, block 0 clean (OLD block 0 was comment junk + 00_core.js) |

## Scope: observed, not flagged by CodeQL, left alone

- Plain `str.rfind("<script>")` / `str.find("</script>")` position lookups for KNOWN asset blocks in: test_story_editor_state.py:87-93, -boot.py:112, -choices.py:119, -claims.py:110, -editscast.py:137+551, -form.py:121, -graph.py:108, -lifecycle.py:160, -load.py:115, -onenter.py:140, -save.py:126, -trace.py:125 (not regexes; not extraction filters)
- generator.py:113 `re.search(r"<script[^>]*\ssrc=", ...)` -- absence-assert for external refs, not a content extraction (CodeQL did not flag it)

## Per-Alert Tracking

| Alert | File:Line | Flagged pattern | Replacement applied | Verified |
|-------|-----------|-----------------|---------------------|----------|
| #9 | tests/test_story_editor_state.py:149 | `re.findall(r"<script>(.*?)</script>", self.html, re.S)` in `test_no_modules_no_arrow_asi_landmines` | `script_blocks.extract_script_blocks(self.html)` + per-block module-attr check; per-block ES5 regexes now run on `block.text` | py_compile + 13/13 module + 22/22 helper battery + 232/232 family |
| #8 | tests/test_story_editor_generator.py:126 | `re.findall(r"<script>(.*?)</script>", self.html, re.S)` in `test_offline_no_external_refs` | `script_blocks.extract_script_blocks(self.html)` + per-block module-attr check; import-statement regex now runs on `block.text` | py_compile + 13/13 module + 22/22 helper battery + 232/232 family |
