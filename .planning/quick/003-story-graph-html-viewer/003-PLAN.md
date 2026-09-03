---
phase: quick-003-story-graph-html-viewer
plan: 003
type: execute
wave: 1
depends_on: []
files_modified:
  - tools/story_graph_viewer.py
  - .gitignore
  - dist/story_graph_viewer.html   # generated output — gitignored, never committed
autonomous: false                  # Task 3 ends in a human-verify checkpoint
must_haves:
  truths:
    - "Running `python3.6 tools/story_graph_viewer.py` regenerates a self-contained HTML at dist/story_graph_viewer.html that opens over file:// with ZERO network/library requests"
    - "All 57 nodes render in 7 deterministic segment columns, color-coded by kind, draggable, with wheel-zoom / background-pan / fit / reset-layout"
    - "Clicking any node shows the FULL two-layer story + tags + choices + on_enter summary + claim chips with registry status + the edit-bucket signature when present"
    - "The 13 known-edit routes render as amber dashed edges, including the 2 restored ROUTER-ONLY nodes placed adjacent to their enzymes"
    - "Search, segment filters, claims toggle, end.true soul-jump shortcut, PLACEHOLDER_PHASE8 stub flags, and the guided review order all function"
    - "Regeneration is deterministic and the built-in integrity self-check gates the output (exit 1 + no file on any invariant violation)"
  artifacts:
    - path: "tools/story_graph_viewer.py"
      provides: "Generator: read-only data -> inlined single-file HTML viewer; python3.6 + stdlib only"
      contains: "VIEWER_OK"
    - path: "dist/story_graph_viewer.html"
      provides: "The review instrument (generated, gitignored)"
    - path: ".gitignore"
      provides: "Explicit ignore rule for the generated viewer"
  key_links:
    - from: "tools/story_graph_viewer.py"
      to: "data/story_glucose/manifest.json + the 7 story files"
      via: "read-only json.load, manifest-driven file order"
      pattern: "story_glucose"
    - from: "tools/story_graph_viewer.py"
      to: "rpg/data/edits.json"
      via: "enzymes[bucket].edits[].branch_node -> dashed edges"
      pattern: "branch_node"
    - from: "tools/story_graph_viewer.py"
      to: "data/citations.json"
      via: "approval_status -> green/amber claim chips"
      pattern: "approval_status"
    - from: "dist/story_graph_viewer.html"
      to: "inline JSON blob"
      via: "<script id=\"story-data\" type=\"application/json\"> (no fetch)"
      pattern: "story-data"
---

# Quick Task 003 — Interactive HTML Story-Graph Viewer (Phase 7 review instrument)

<objective>
Build `tools/story_graph_viewer.py` — a python3.6 stdlib-only generator that reads the Phase 7 story bundle read-only and emits ONE self-contained HTML file (vanilla JS + SVG, zero libraries, zero CDN, all data inlined at build time) for human review of the 57-node glucose story graph: interactive network LEFT (zoom/pan/drag), full two-layer reading panel RIGHT, edit-routing overlay, search/filter/review-order, and live claim-status chips.

Purpose: this viewer IS the review instrument for the PENDING 07-18 Task 2 human batch-content checkpoint. It must make node connections + story readable without playing the game.

Output: `tools/story_graph_viewer.py` (committed) + `dist/story_graph_viewer.html` (generated, gitignored, regenerated on demand).
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>

**HARD SCOPE (non-negotiable):** `tools/story_graph_viewer.py` + `.gitignore` + the generated `dist/story_graph_viewer.html` ONLY. NO `rpg/**` changes, NO `data/**` changes, NO `tools/check_*.py` changes, NO engine changes. The generator is READ-ONLY over data. Do not import `rpg.*` — pure stdlib (`json`, `os`, `sys`, `html`), matching the AST import gate.

**Style contract (match the suite — see `tools/render_story_graph.py` as the model):**
- Shebang `#!/usr/bin/env python3.6`; module docstring with Usage block; CWD-independent paths resolved from `SCRIPT_DIR`/`REPO_ROOT`.
- **NO f-strings** (suite style: `.format()` / concatenation). No dataclasses, no argparse — manual `sys.argv` parsing like `render_story_graph.py`.
- Python must pass `python3.6 -m py_compile` AND keep `python3.6 tools/check_imports.py` clean (stdlib imports only).

**Data sources (all verified to exist — read-only):**

1. `data/story_glucose/manifest.json` → `{"version":1,"default_seed":0,"start":"intro.preface","files":["intro.json","glycolysis.json","pyruvate_branch.json","tca.json","etc_atp.json","endings.json","bad_endings.json"]}`. Each file = `{"nodes": {id: node}}` (dict, insertion order = row order). 57 unique ids total.
2. Node shape (all 57 have): `text_dramatic`, `text_teaching`, `claim_ids` (list), `tags` (list), `on_enter` (list of MolAction dicts `{op, target?, args?}`), `choices` (list of `{label, goto, tags?, weight?, cond?, effects?}`). 21 nodes additionally have `is_ending` (string tier).
3. **Tier derivation (CRITICAL — verified against live data):** the ending tier comes from the **`is_ending` node FIELD** (`"true"|"good"|"normal"|"bad"`), NOT the `ending:*` node tag. Verified counts via the field: true=1, good=3, normal=2, bad=15 → 21. (The `ending:*` tags under-count: `anaer.lactic`, `anaer.ethanolic`, `anaer.crisis` carry the field but no tag → tag-based counting gives 18 ≠ 21. Do NOT derive tier from tags.)
4. **Edit-allowed derivation:** a node is edit-allowed iff ≥1 of its choices has `"edit:offer"` in that choice's `tags` (it is a CHOICE tag, not a node tag). Exactly 15 nodes: gly.pfk, gly.pyruvate_kinase, pyr.pdh, tca.citrate_synthase, tca.aconitase, tca.shuffle, tca.isocitrate_dh, tca.akg_dh, tca.succinyl_coa_synthetase, tca.fumarase, tca.malate_dh, etc.complex_i, etc.complex_ii, etc.complex_iii, etc.complex_iv.
5. RNG: node tag `"rng:weighted"` → exactly `tca.shuffle` (its two weighted choices carry weight 0.5/0.5 + choice tag `rng:weighted`; one more choice has `cond: "visits.get('tca.shuffle', 0) > 5"` + tag `cycle_trap`).
6. `rpg/data/edits.json` → `{"version":…, "bad_ending_pool":…, "enzymes": {bucket_id: {"edits": [{"signature": {"op":"point_mutation","target":"resi N[ and chain X]","args":{"new_res":"AA"}},"branch_node":"<node id>","claim_id":"<id>"}]}}}` — exactly 13 buckets. Dashed-edge table (verified): gly.pfk→gly.pfk_restored; gly.pyruvate_kinase→gly.pyruvate; pyr.pdh→**tca.entry** (crosses columns!); tca.aconitase→tca.aconitase_restored; tca.isocitrate_dh→tca.akg_dh; tca.akg_dh→tca.succinyl_coa_synthetase; tca.succinyl_coa_synthetase→tca.fumarase; tca.fumarase→tca.malate_dh; tca.malate_dh→tca.divert_to_good; etc.complex_i→etc.complex_ii; etc.complex_ii→etc.complex_iii; etc.complex_iii→etc.complex_iv; etc.complex_iv→etc.atp_synthase. The 11 exploration enzymes route to their main-path successors → their dashed edges will OVERLAP solid edges (by design, 07-14 convention) — curvature offset required. `tca.citrate_synthase` has an `edit:enzyme:` node tag but deliberately NO bucket (14 graph tags − 1 = 13 buckets).
7. `data/citations.json` → flat dict claim_id → `{claim, claim_text, source_type, source, source_id, review_tier, inherits_source_approval, approval_status: "approved"|"pending", approved_by?, approved_date?}`. 77 claims, 4 pending (BAD-AGGREG-01, BAD-INHIB-01, BAD-MISFOLD-01, BAD-PH-01 — count dynamically, do NOT hard-assert 4; the 07-18 checkpoint may flip them).
8. `rpg/data/cast.json` → `{"version":…, "enzymes": [ {id, label, source, pdb_id, character, claim_id}, … ]}` — LIST of 12, keyed for lookup by `id`. Used only as display enrichment (label + pdb_id in reading panel).
9. Sanctioned stubs: `fa.stub` + `alc.stub` (in intro.json, choices from intro.select) carry `claim_ids: ["PLACEHOLDER_PHASE8"]` — PLACEHOLDER_PHASE8 is NOT in the registry; render it as a special grey "placeholder" chip. It is the ONLY allowed non-registry claim id.

**Restored nodes (07-12 ROUTER-ONLY invariant — the viewer must show it):** `gly.pfk_restored` + `tca.aconitase_restored` have ZERO incoming `choice.goto` edges (engine routes known edits directly to them). The dashed edit edges are their ONLY incoming arcs in the viewer. Enforce/verify this in the integrity check.

**on_enter op vocabulary actually present in the data (57 nodes):** hide_all(55), load(16), set_color(1), show_as(7), color(1), show(1), set(1), label(1), edit(2), align(2). Nothing else — but the unknown-op fallback must never crash.

</context>

<tasks>

<task type="auto">
  <name>Task 1: Generator engine — data model, derivations, deterministic layout, integrity self-check</name>
  <files>tools/story_graph_viewer.py</files>
  <action>
Create `tools/story_graph_viewer.py` with the loader/derivation/layout/self-check half (Task 2 adds the HTML template + `render_html`). Suite style per the context block: python3.6, stdlib only, `.format()` not f-strings, CWD-independent defaults, module docstring with Usage.

**Structure:**

```
SCRIPT_DIR / REPO_ROOT / DEFAULT_STORY_DIR = <repo>/data/story_glucose
DEFAULT_OUTPUT_DIR = <repo>/dist ; OUTPUT_NAME = "story_graph_viewer.html"
STORY_FILES = manifest["files"] order (drive everything off the manifest)
COL_ORDER = ["intro", "glycolysis", "pyruvate/anaerobic", "tca", "etc", "endings+bad", "phase8-stubs"]
```

**Loaders:** `load_story(dir)` → ordered node dict following manifest file order, erroring on duplicate ids; `load_registry(path)` / `load_cast(path)` / `load_edits(path)` (paths: `data/citations.json`, `rpg/data/cast.json`, `rpg/data/edits.json`, resolved from REPO_ROOT; tolerate absence of cast.json gracefully — enrichment only — but citations.json and edits.json are REQUIRED).

**Per-node derivation (build a plain dict per node):**
- `tier`: `node["is_ending"]` field or None (NEVER from tags).
- `edit_allowed`: any choice tagged `edit:offer`.
- `rng`: `"rng:weighted"` in node tags.
- `kind` (color class), precedence first-match:
  1. tier is not None → `ending-<tier>` (4 classes)
  2. id in {"fa.stub","alc.stub"} → `phase8-stub`
  3. id == "edit.prompt" → `edit-prompt`
  4. id in {"gly.pfk_restored","tca.aconitase_restored"} → `restored`
  5. rng → `rng`
  6. edit_allowed → `edit-allowed`
  7. else → `story`
- `bucket`: edits.json `enzymes[id]` when present; else if edit_allowed → mark `no_bucket=True` (exactly tca.citrate_synthase expected).
- `cast`: cast.json entry by id (label + pdb_id) or None.

**Column + row layout (deterministic; verified counts in parentheses):**
- Column assignment, first-match rules:
  1. id == "edit.prompt" → col 5 row 0 (top of the endings/bad column — it is the hub 15 solid edit:offer edges converge on; its 13 choice edges fan downward within the column).
  2. id in {"fa.stub","alc.stub"} → col 6 ("Phase-8 stubs").
  3. restored ids → col of their enzyme (glycolysis=1 / tca=3), directly after the enzyme in row order (file order already yields this — glycolysis.json order is start, g6p, pfk, pfk_restored, fbp_to_pyruvate, pyruvate_kinase, pyruvate; tca.json order has aconitase_restored right after aconitase).
  4. else → column by SOURCE FILE: intro.json minus the 2 stubs → col 0 (intro.preface, intro.select, intro.shell_glucose = 3); glycolysis.json → col 1 (7); pyruvate_branch.json → col 2 "pyruvate/anaerobic" (7); tca.json → col 3 (13); etc_atp.json → col 4 (7, end.true last); endings.json (3: end.good.fatty_acid, end.good.amino_acid, end.normal.co2) then bad_endings.json (14 bad.* in file order, edit.prompt already lifted to row 0) → col 5 (18).
  Total 3+7+7+13+7+18+2 = 57. Assert it.
- Coordinates: `x = 60 + col * 280`, `y = 90 + row * 96`; node box 190×68, rx 8. Max rows = 18 (col 5) → canvas ≈ 2100×1900.

**Edges:**
- Solid (choice.goto): iterate nodes/choices in order; dedupe exact (src,dst) pairs (e.g. the restored nodes have 2 choices → same target; gly.pfk has Continue → gly.fbp_to_pyruvate which is ALSO tca-malate_dh's dashed target — fine). Each deduped edge carries: merged choice labels (for tooltip), `weight` when ALL merged choices share a weight (render mid-label "w=0.5"), `cond` flag (render mid-label "cond" + full cond in tooltip), `effects` summary (e.g. "set anaerobic=true") in tooltip, and choice tags (edit:offer / mc:observe / branch:* / cycle_trap / divert:* etc.) in tooltip.
- Dashed (edit routing): for each bucket, for each edit: (enzyme_id → branch_node). Amber, dasharray, larger perpendicular curvature (+56px) so overlapping solid pairs stay visible. Tooltip: "known edit: point_mutation resi 209 and chain a → GLY | claim DIS-PFKM-01-cand | routes to gly.pfk_restored". Exactly 13 dashed edges.

**`check_integrity(model)` — hard assertions, exit 1 with a numbered failure message on ANY violation:**
1. 57 nodes; no duplicate ids across files.
2. is_ending field counts == {true:1, good:3, normal:2, bad:15} (total 21).
3. edit-allowed set == the 15 pinned ids (from context §4).
4. Exactly one rng node == "tca.shuffle".
5. Every choice.goto resolves to a node id; every edits.json branch_node resolves; every bucket id resolves to an enzyme node.
6. Every node claim_id resolves in the registry OR is exactly "PLACEHOLDER_PHASE8" (only on fa.stub/alc.stub — assert that pairing too).
7. Bucket ids (13) ⊆ `edit:enzyme:*` tag ids (14); difference == {"tca.citrate_synthase"}.
8. cast ids (12) ⊆ bucket ids.
9. Restored nodes have ZERO incoming choice.goto edges (router-only invariant).
10. Every claim's approval_status ∈ {"approved","pending"} (informational counts only — pending may legitimately change if the human approves BAD-* during 07-18; print, never assert, the split).

**CLI:** `main(argv)` manual parse: `--story-dir DIR` (default data/story_glucose), `--output-dir DIR` (default `<repo>/dist`), `--dump-data PATH` (debug: write the payload JSON to PATH too). Exit 0 on success; print sentinel line `VIEWER_OK nodes=57 endings=21 edit_allowed=15 buckets=13 claims=<N> pending=<P> solid_edges=<S> dashed_edges=13` with DERIVED numbers (.format). On integrity failure print `VIEWER_FAIL: <reason>` and exit 1 WITHOUT writing the HTML.
  </action>
  <verify>
```
python3.6 -m py_compile tools/story_graph_viewer.py && python3.6 tools/check_imports.py && python3.6 tools/story_graph_viewer.py --dump-data /tmp/opencode/003-data.json; echo "exit=$?"
```
Expect exit=0 and a `^VIEWER_OK nodes=57 endings=21 edit_allowed=15 buckets=13` line. Then:
```
python3.6 - <<'EOF'
import json
d = json.load(open('/tmp/opencode/003-data.json'))
assert len(d['nodes']) == 57, len(d['nodes'])
assert sum(1 for n in d['nodes'].values() if n['tier']) == 21
assert len(d['dashed_edges']) == 13
assert [n for n in d['nodes'].values() if n['id'] == 'gly.pfk_restored'][0]['kind'] == 'restored'
print('DATA_OK')
EOF
```
  </verify>
  <done>Generator loads all sources read-only, derives tier/edit-allowed/kind/bucket exactly per the pinned rules, passes all 10 integrity assertions, prints the VIEWER_OK sentinel with derived counts, and dumps the payload JSON.</done>
</task>

<task type="auto">
  <name>Task 2: Self-contained HTML viewer — template, SVG graph, top bar, reading panel, review-order</name>
  <files>tools/story_graph_viewer.py, .gitignore</files>
  <action>
Add the rendering half to `tools/story_graph_viewer.py` and the output wiring.

**Template plumbing:** module-level `HTML_TEMPLATE = r"""..."""` containing tokens `__TITLE__` and `__STORY_DATA_JSON__`; substitute via `str.replace` ONLY (no `.format` — JS/CSS braces would explode). Payload embedded as `<script id="story-data" type="application/json">` with `json.dumps(payload, ensure_ascii=True).replace("</", "<\\/")` (prevents `</script>` breakout; ensure_ascii makes it 7-bit safe for file://). `render_html(payload, title) -> str`; `main` writes `dist/story_graph_viewer.html` (create dir if needed) ONLY after check_integrity passes.

**Document skeleton:** `<!doctype html>` + `<style>` + top bar + legend + `<div id="main">` holding `<svg id="graph">` (left, flexible) + `<aside id="reading-panel">` (right, fixed ~380px, scrollable) + the data script + one `<script>` block. Vanilla JS (ES5-safe is NOT required — modern browsers fine), zero external refs: no `<script src=`, no `<link href=`, no fetch/XHR. The ONLY `http` string allowed is the SVG xmlns.

**SVG graph (left):**
- Root `<g id="world">` transform for pan/zoom (state: `tx, ty, scale`). Wheel = zoom about the pointer (clamp 0.25–3); background drag = pan; node drag = move that node (update its `transform="translate(x,y)"`, positions persist in-memory ONLY); "Reset layout" reapplies the generator's initial x/y; "Fit view" computes the node bbox and sets transform to fit with 40px margin.
- Nodes: `<g class="node kind-<kind>" data-node-id="<id>" transform=...>` containing `<rect width=190 height=68 rx=8>` + `<text>` short label (full id; truncate >22 chars with "…"; 11px monospace) + `<title>` tooltip = id + tier/kind line + first ~110 chars of text_dramatic. Fill palette (define in CSS, document in legend): ending-true #c9a227 gold; ending-good #2e8b57; ending-normal #4682b4; ending-bad #b22222; restored #e6e0f5 fill + double-border effect (outer stroke #6a4fc1 3px); edit-prompt #f5c16c; phase8-stub #cccccc hatched/flagged; rng #17a2b8; edit-allowed #8a2be2-tinted fill + solid purple 2px stroke; story #dfe7ef. PLACEHOLDER_PHASE8 stubs additionally render a small "Phase-8 stub" badge text.
- Edges UNDER nodes (`<g id="edges">` before `<g id="nodes">`): solid = cubic bezier src right-center → dst left-center, stroke #666 1.5px, shared arrowhead `<marker>`; dashed edit routes = stroke #d97706 2px, `stroke-dasharray: 7 5`, +56px perpendicular curvature offset, amber arrowhead, `<title>` = the known-edit signature line. Mid-labels: "w=0.5" on the two shuffle edges; "cond" on the cycle_trap edge.

**Top bar:** h1 "RPG: Tale of C — Glucose Story Graph (Phase 7 review)"; description line ("Interactive review of the Phase 7 glucose story graph — solid = choice.goto, amber dashed = known-edit routing (edits.json), click a node for the full two-layer story."); counts badge rendered from DERIVED data ("57 nodes / 21 endings (1T+3G+2N+15B) / 15 edit-allowed / 77 claims (73 approved, 4 pending)"); search `<input id="search">`; segment filter buttons (All / Intro / Glycolysis / Pyruvate+Anaerobic / TCA / ETC / Endings+Bad pool / Phase-8 stubs); buttons: "Review order" (toggle), "Claims" (toggle), "end.true" (soul-jump), "Fit view", "Reset layout".

**Legend (top, second row):** one swatch per kind (all 9 classes) + line samples: solid = player choice; amber dashed = known-edit route (restored nodes are reached ONLY this way); "w=0.5" = RNG-weighted; "cond" = conditional choice.

**Reading panel (right) — on node click populate ALL of, in order:**
1. Header: id (monospace) + badges: stage tag, tier (or "—"), kind.
2. Tags: all node tags as chips.
3. text_dramatic — FULL, blockquote-styled. 4. text_teaching — FULL, prose.
5. Choices: each row = label + "→ target" (target is a clickable link that selects+centers the target node) + annotations: weight, cond expression, effects ("set anaerobic=true"), choice tags as mini-chips (edit:offer, mc:observe, branch:aerobic, …).
6. on_enter summary — human-readable per op, from this pinned mapping (unknown op → `op <name> <compact JSON of args>`, never crash): hide_all→"hide all objects"; load→"load `<target>` as object `<args.object>`" (note stripped pdb:/cid: prefixes); set_color→"define color `<name>` = rgb(r,g,b)"; show_as→"show as `<args.rep|value>` [sele]"; color→"color `<target>` = `<args.name|value>`"; show→"show `<args.rep|value>` [sele]"; set→"set `<key>` = `<val>`"; label→"label `<target>` = '<text>'"; edit→"mutate `<target>` → `<args.new_res>`"; align→"align `<args.mobile|target>` → `<args.reference>` (method `<args.method>`, sele `<args.align_sele>`)".
7. Claims: chip per claim_id — green "approved" / amber "pending" (status + claim_text + source_id + review_tier read from the EMBEDDED registry, i.e. current-at-generation); grey "placeholder" chip for PLACEHOLDER_PHASE8; hover shows claim_text, click expands the full claim_text + source_id + review_tier.
8. Edit bucket (when node is an edits.json bucket): table op / target / new_res / branch_node / claim_id + line "dashed route → <branch_node>". When `edit_allowed && no_bucket` (exactly tca.citrate_synthase): note "edit-allowed — no known-fix bucket (tca.citrate_synthase excluded by design)".
9. Cast line (when cast entry exists): "<label> — PDB <pdb_id>" (e.g. "Phosphofructokinase-1 — PDB 4PFK").
10. Prev / Next buttons + position "n / 57" walking the review order.

**Search:** on input (case-insensitive) match against id + text_dramatic + text_teaching + tags joined; non-matching nodes+edges fade to opacity 0.15; show "n matches"; empty/Esc clears.

**Segment filter:** dim (not hide) nodes outside the selected segment (same 0.15 rule) incl. their edges; All resets. Filter state composes with search (both apply).

**Claims toggle:** nodes with non-empty claim_ids get a green outline; nodes carrying ≥1 pending claim get an amber outline; re-click clears.

**end.true soul-jump button:** selects end.true, centers it, opens its panel (the 07-18 checklist checks the soul-jump wording here).

**Review order mode:** pinned sequence = col0 intro (3) → col1 glycolysis (7) → col2 pyruvate/anaerobic (7) → col3 TCA (13) → col4 ETC (7, end.true last) → endings.json (3) → edit.prompt → bad pool (14) → Phase-8 stubs (2) = 57. Active mode: current node thick outline + gentle center-on-current, others dimmed, reading panel auto-populated, Prev/Next (also the panel's n/57 buttons) step through; toggling off exits. Stubs are the final stops, labeled "(Phase 8 — sanctioned placeholder)".

**.gitignore:** append (dist/ is already ignored; this explicit rule is self-documenting per the task constraint):
```
# Interactive story-graph review viewer (built by tools/story_graph_viewer.py).
# NOT committed -- regenerable on demand: python3.6 tools/story_graph_viewer.py
dist/story_graph_viewer.html
```
  </action>
  <verify>
```
python3.6 -m py_compile tools/story_graph_viewer.py && python3.6 tools/check_imports.py && python3.6 tools/story_graph_viewer.py
python3.6 - <<'EOF'
html = open('dist/story_graph_viewer.html').read()
assert html.count('data-node-id=') == 57, html.count('data-node-id=')
for token in ('id="story-data"', 'id="reading-panel"', 'id="search"', 'Review order',
              'end.true', 'Reset layout', 'Fit view', 'legend', 'branch_node', 'approval_status',
              'text_teaching', 'PLACEHOLDER_PHASE8'):
    assert token in html, token
assert '<script src=' not in html and 'fetch(' not in html and 'XMLHttpRequest' not in html
import re
ext = [u for u in re.findall(r'https?://[^"\\s<)]+', html) if 'w3.org' not in u]
assert not ext, ext
print('HTML_OK')
EOF
git check-ignore -v dist/story_graph_viewer.html
```
Expect `DATA`/`HTML_OK`, the VIEWER_OK sentinel, and git reporting the file ignored.
  </verify>
  <done>The generator emits one self-contained HTML carrying all 57 nodes inline; every UI element id from the spec is present; zero external references; output lands under a gitignore rule; all Task 1 integrity gates still pass.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 3: Full gate battery, commit, and human browser verification</name>
  <files>.planning/quick/003-story-graph-html-viewer/003-SUMMARY.md</files>
  <action>
**Automated gate battery (run all, record results in the SUMMARY):**
1. `python3.6 -m py_compile tools/story_graph_viewer.py` — exit 0.
2. `python3.6 tools/check_imports.py` — exit 0 (AST gate untouched and clean).
3. `python3.6 tools/story_graph_viewer.py` — exit 0 + `^VIEWER_OK nodes=57 endings=21 edit_allowed=15 buckets=13` sentinel.
4. The Task 2 `HTML_OK` python assertion block — all tokens found, zero external refs.
5. `python3.6 -m unittest discover -s tests` — 345 tests OK (nothing outside tools/ touched; suite must be unaffected).
6. `git status --porcelain` — only `tools/story_graph_viewer.py`, `.gitignore`, and the plan/SUMMARY docs appear; `dist/story_graph_viewer.html` does NOT appear (ignored). Then commit:
   `git add tools/story_graph_viewer.py .gitignore && git commit -m "feat(quick-003): self-contained HTML story-graph review viewer"`

**checkpoint:human-verify — what was built:** the interactive viewer at
`C:\Users\nglok\Desktop\WORKDIR\molmdl\RPG_tale-of-C\dist\story_graph_viewer.html`
(regenerate any time with `python3.6 tools/story_graph_viewer.py` from the repo root).

**How to verify (open the file in any browser — double-click works; ~10 minutes):**
1. Page loads with title, description, counts badge "57 nodes / 21 endings … / 15 edit-allowed / 77 claims", legend row, and 7 color-grouped columns left→right: Intro(3), Glycolysis(7), Pyruvate+Anaerobic(7), TCA(13), ETC(7), Endings+Bad pool(18), Phase-8 stubs(2). No blank boxes, no console errors (F12).
2. Wheel-zoom about the cursor, drag background to pan, drag `gly.pfk` somewhere, then "Reset layout" restores it; "Fit view" frames everything.
3. Click `gly.pfk`: reading panel shows FULL dramatic + teaching text, tags (stage:glycolysis, edit:enzyme:gly.pfk), 3 choices (Continue / edit:offer → edit.prompt), the on_enter load line, 3 GREEN claim chips (GLY-PFK-01, CAST-PFK-PDB-01, DIS-PFKM-01-cand — hover for claim_text), the edit-bucket table (resi 209 and chain a → GLY, branch gly.pfk_restored), and cast line "Phosphofructokinase-1 — PDB 4PFK".
4. Amber DASHED edge gly.pfk → gly.pfk_restored is visible and separate from solid edges; gly.pfk_restored + tca.aconitase_restored sit adjacent to their enzymes with double borders and NO solid incoming edges (router-only).
5. Hover a dashed edge → tooltip shows the point_mutation signature + claim id; pyr.pdh's dashed edge visibly crosses to tca.entry (different column).
6. Click `bad.proton_leak` → its claim chip is AMBER (BAD-* pending) with generic wording visible in the text; click `tca.shuffle` → both outgoing edges show "w=0.5", the third edge shows "cond", node is RNG-colored.
7. Search "aconitase" → only the aconitase family stays bright + match count; segment button "TCA" dims everything else; "All" + clear restore.
8. "Claims" toggle → green outlines on claim-bearing nodes, amber outlines only in the bad pool; "end.true" button → jumps to the True ending, panel shows the soul-jump dramatic text (electrons/soul → ATP, carbon shed as CO2).
9. fa.stub / alc.stub render grey+hatched with "Phase-8 stub" badges.
10. "Review order" → intro.preface highlighted, panel open, position 1/57; Next walks intro → glycolysis → … → bad pool → stubs in order; Prev/Next and position update correctly; toggle off exits the mode.

**resume-signal:** Type "approved" or describe issues (issues → fix + regenerate + re-verify).
  </action>
  <verify>All 6 automated gates recorded PASS in the SUMMARY + commit exists + human returns a verdict on the 10 browser checks.</verify>
  <done>The 07-18 reviewer has a working, regenerable, self-contained review instrument; tool committed; output gitignored; human verdict recorded.</done>
</task>

</tasks>

<verification>
- `python3.6 -m py_compile tools/story_graph_viewer.py` exit 0
- `python3.6 tools/check_imports.py` exit 0
- `python3.6 tools/story_graph_viewer.py` exit 0 with `^VIEWER_OK nodes=57 endings=21 edit_allowed=15 buckets=13` sentinel
- Task 2 HTML_OK assertion block passes (57 data-node-id, all UI tokens, zero external refs)
- `python3.6 -m unittest discover -s tests` → 345 OK (no regression outside the new tool)
- `git check-ignore -v dist/story_graph_viewer.html` → ignored; `git status` clean of unintended paths
- Human 10-point browser checklist verdict recorded
</verification>

<success_criteria>
The Phase 7 reviewer can open `dist/story_graph_viewer.html` over file:// and, without the game or any network access: see all 57 nodes in deterministic segment columns with the legend explaining every color/edge style; click any node to read the FULL two-layer story with tags, choices, on_enter summary, and claim chips whose green/amber state matches data/citations.json; trace all 13 known-edit routes as dashed edges including the 2 router-only restored nodes; search/filter/walk the graph in the 07-18 review order; and regenerate the whole thing on demand with one python3.6 command gated by an integrity self-check.
</success_criteria>

<output>
After completion, create `.planning/quick/003-story-graph-html-viewer/003-SUMMARY.md` with: the 6 gate results, the derived counts line, commit hash(es), and the human verdict on the 10-point checklist.
</output>
