---
phase: quick-003-story-graph-html-viewer
plan: 003
subsystem: tools
tags: [story-graph, html-viewer, svg, vanilla-js, review-instrument, phase-7, glucose]

# Dependency graph
requires:
  - phase: 07-glucose-story-content (frozen 57-node bundle)
    provides: data/story_glucose manifest + 7 story files (read-only source of truth)
  - phase: 05/06 edits + citations manifests
    provides: rpg/data/edits.json (13 buckets), data/citations.json (77 claims), rpg/data/cast.json (12 enzymes)
  - phase: quick-002 (07-18 review instrument context)
    provides: the pending human batch-content checkpoint this viewer serves
provides:
  - tools/story_graph_viewer.py: python3.6 stdlib-only, read-only generator with 10-gate integrity self-check (exit 1 + no output on violation)
  - dist/story_graph_viewer.html: self-contained review viewer (vanilla JS + SVG, zero external refs, works over file://), regenerable on demand, gitignored
  - .gitignore explicit rule for the generated HTML
  - pinned 07-18 review order embedded in the viewer (intro -> glycolysis -> pyruvate/anaerobic -> TCA -> ETC (end.true last) -> endings -> edit.prompt -> bad pool -> stubs)
affects: [07-18 human batch-content review, phase-8 stubs (PLACEHOLDER_PHASE8 chips), any future story-graph viewer for new pathways]

# Tech tracking
tech-stack:
  added: []  # stdlib only (json, os, sys, html, math) per spec
  patterns:
    - "server-side SVG + client-side JS enhancement: the HTML carries all 57 data-node-id groups statically (greppable/verify-able without a browser); JS only wires interactivity"
    - "token substitution via str.replace ONLY (__TITLE__/__SVG_*/__STORY_DATA_JSON__) so JS/CSS braces never collide with .format"
    - "JSON inlined as <script id=story-data type=application/json> with '</' -> '<\\/' escaping (no fetch, file:// safe, 7-bit via ensure_ascii)"
    - "generator/JS geometry mirroring: edgeD()/labelPos() in the page replicate the Python _edge_geometry constants exactly, so drag/reset reproduce generator layout"
    - "anti-fragility: pending-claim counts and the no-bucket set are PRINTED, never asserted; integrity gates assert only the plan-pinned invariants"

key-files:
  created:
    - tools/story_graph_viewer.py
    - .planning/quick/003-story-graph-html-viewer/003-SUMMARY.md
  modified:
    - .gitignore
  generated (gitignored, never committed):
    - dist/story_graph_viewer.html

key-decisions:
  - "Ending tiers derived from the is_ending FIELD only (21 = 1T+3G+2N+15B); ending:* tags under-count (18) because anaer.lactic/ethanolic/crisis carry the field without a tag"
  - "Edit-allowed = node with >=1 choice tagged edit:offer (15 nodes, pinned set asserted); distinct from edit:enzyme:* node tags (14) and from edits.json buckets (13)"
  - "no_bucket is computed dynamically: live data yields {tca.citrate_synthase, tca.shuffle} (both edit-allowed, neither in edits.json) -- the plan expected only citrate_synthase; trusted the data, printed not asserted"
  - "edit.prompt's 13 structural bad-pool edges routed through the right gutter (geo=fan) instead of straight verticals so they stay visible beside the ending boxes they would run under"
  - "Fit view uses the world bbox (nodes + edges + headers) rather than a bare node bbox so the 2 over-the-top stub back-edges are never clipped"
  - "Pending-claim status (BAD-AGGREG-01/BAD-INHIB-01/BAD-MISFOLD-01/BAD-PH-01 = 4 today) is printed and drives chip/outline coloring dynamically; never hard-asserted"

patterns-established:
  - "Read-only review-instrument generator: loads game data without importing rpg.*, passes the AST import gate"
  - "Integrity self-check gates output: 10 numbered hard gates; dangling goto/branch_node reported via VIEWER_FAIL (numbered), exit 1, zero files written (negative-tested)"

# Metrics
duration: 6h 28min (wall clock incl. orchestrator interleaving; hands-on ~4h)
completed: 2026-09-04
---

# Quick Task 003: Interactive HTML Story-Graph Viewer Summary

**Self-contained, integrity-gated HTML review instrument for the frozen 57-node glucose story graph: 7 deterministic columns, 76 solid + 13 amber-dashed edit routes, full two-layer reading panel with live claim-status chips, and the pinned 07-18 review order -- regenerable with one python3.6 command, zero dependencies, zero network.**

## Performance

- **Duration:** ~6h 28min wall (started 2026-09-03T20:18Z, completed 2026-09-04T02:46Z)
- **Tasks:** 3/3 (Task 3's human-verify checkpoint: all automatable parts done; visual pass handed to the human)
- **Commits:** 3 (53f9622 engine, 85a1711 viewer, c7aee68 fail-closed fix)

## Gate Results (Task 3 battery)

| # | Gate | Result |
|---|------|--------|
| 1 | `python3.6 -m py_compile tools/story_graph_viewer.py` | PASS (exit 0) |
| 2 | `python3.6 tools/check_imports.py` | PASS (clean, stdlib only) |
| 3 | `python3.6 tools/story_graph_viewer.py` sentinel | PASS: `VIEWER_OK nodes=57 endings=21 edit_allowed=15 buckets=13 claims=77 pending=4 solid_edges=76 dashed_edges=13` |
| 4 | Task 2 HTML_OK assertion block | PASS (57 data-node-id, all UI tokens, zero external refs; SVG subtree XML-well-formed; JSON round-trips) |
| 5 | `python3.6 -m unittest discover -s tests` | PASS: **Ran 345 tests - OK** (suite untouched) |
| 6 | `git status --porcelain` | PASS: only tools/story_graph_viewer.py + .gitignore + planning docs; `dist/story_graph_viewer.html` ignored (`.gitignore:25`); rpg/** and data/** byte-untouched |

**Extra robustness probes (beyond the plan battery):**
- Deterministic regeneration: two consecutive runs -> identical MD5 (7a8a99cc353e2db07afaae986ed32e47).
- Fail-closed negative test: doctored bundle with a dangling goto -> `VIEWER_FAIL: ... (5a) choice.goto targets not resolving to nodes: ['intro.preface -> no.such_node']`, exit 1, **zero files written**.

## Deviations from Plan

### Data-vs-plan conflicts (trusted the data per quick-mode Rule 1)

1. **Pending BAD-\* claims are NOT attached to any story node.** The plan's human checklist item 6 expected `bad.proton_leak` to show an AMBER pending chip. Live data: `bad.proton_leak` carries `ETC-UCP-01` which is **approved** (green). The 4 pending claims (BAD-AGGREG-01, BAD-INHIB-01, BAD-MISFOLD-01, BAD-PH-01) exist in the registry but no node references them. The viewer therefore shows zero amber chips/outlines today -- by design it lights up amber dynamically the moment a pending claim is attached or a claim flips to pending. **Checklist item 6 for the human is adjusted accordingly** (see Human Verification Checklist below). Nothing invented; registry state printed, never asserted.

2. **no_bucket set is 2 nodes, not 1.** Plan: "`edit_allowed && no_bucket` (exactly tca.citrate_synthase expected)". Live data: both `tca.citrate_synthase` AND `tca.shuffle` are edit-allowed (choice-tag `edit:offer`) and neither has an edits.json bucket. Implementation computes no_bucket dynamically and prints it; the reading-panel note uses generic wording ("edit-allowed -- no known-fix bucket in rpg/data/edits.json") since "excluded by design" is only documented for citrate_synthase. Integrity gates 7a/7b (tag-vs-bucket diff == {tca.citrate_synthase}) still hold and pass.

### Implementation refinements (within plan intent, no data impact)

3. **Edge geometry is adaptive, not uniformly right-center->left-center.** The plan pinned "solid = cubic bezier src right-center -> dst left-center"; 63 of 76 deduped solid edges flow DOWNWARD within a column, where that form would double back on itself. Implemented: straight vertical spine for same-column down edges (the plan's own "13 choice edges fan downward" wording implies this), the pinned right->left bezier for cross-column edges, right-side bows for the 3 cycle back-edges, over-the-top arcs for the 2 stub back edges. The +56px perpendicular curvature offset for the 11 overlapping dashed pairs is implemented exactly as pinned.
4. **edit.prompt's 13 structural edges routed through the right gutter** (geo=fan) so they don't disappear under the ending boxes sitting between the hub and the bad pool.
5. **Node drag re-routes connected edges live** (JS mirror of the generator geometry; Reset layout restores generator positions + re-paths). The plan only required moving the node; dangling edges would read as a bug to the reviewer.
6. **Fit view fits the world bbox** (nodes + edges + headers), not just nodes, so the 2 over-the-top stub back-edges stay in frame.
7. **Legend renders 10 kind swatches**, not the plan's "9 classes" -- the kind derivation defines 10 (4 ending tiers + restored + edit-prompt + phase8-stub + rng + edit-allowed + story); the legend must explain every color.
8. **Static server-side SVG** (tokens `__SVG_DEFS__/__SVG_EDGES__/__SVG_NODES__/__SVG_HEADERS__` added alongside the pinned `__TITLE__`/`__STORY_DATA_JSON__`): required so the HTML literally carries 57 `data-node-id=` occurrences as the Task 2 verify demands.

### Auto-fixed bug (Rule 1)

9. **Dangling goto crashed with a raw KeyError instead of the pinned VIEWER_FAIL.** Found by the fail-closed negative probe; `_build_solid_edges` now keeps unresolvable edges in the model so integrity gate 5a reports them by number. Commit c7aee68. Verified: exit 1, zero files, clean numbered message; real-bundle output byte-identical.

## Human Verification Checklist (07-18 reviewer -- Task 3 checkpoint, visual pass)

Open `C:\Users\nglok\Desktop\WORKDIR\molmdl\RPG_tale-of-C\dist\story_graph_viewer.html` in any browser (double-click works; regenerate anytime with `python3.6 tools/story_graph_viewer.py`). ~10 minutes; F12 console should stay clean.

1. Page loads: title, description, counts badge "57 nodes / 21 endings (1T+3G+2N+15B) / 15 edit-allowed / 77 claims (73 approved, 4 pending)", legend row (10 kind swatches + 4 edge samples), 7 columns: Intro(3), Glycolysis(7), Pyruvate+Anaerobic(7), TCA(13), ETC+ATP(7), Endings+Bad pool(18), Phase-8 stubs(2).
2. Wheel-zoom about cursor (0.25x-3x), drag background to pan, drag `gly.pfk` (its edges follow), "Reset layout" restores, "Fit view" frames everything.
3. Click `gly.pfk`: FULL dramatic + teaching text, tag chips (stage:glycolysis, edit:enzyme:gly.pfk), 3 choices (Continue / Examine / edit:offer -> edit.prompt), on_enter lines (`hide all objects`, `load '4PFK' as object 'pfk'`), 3 GREEN claim chips (GLY-PFK-01, CAST-PFK-PDB-01, DIS-PFKM-01-cand; click a chip to expand claim_text + source_id + review_tier), edit-bucket table (point_mutation, resi 209 and chain a, GLY, gly.pfk_restored, DIS-PFKM-01-cand) + "dashed route -> gly.pfk_restored", cast line "Phosphofructokinase-1 -- PDB 4PFK".
4. Amber DASHED edge gly.pfk -> gly.pfk_restored visible; gly.pfk_restored + tca.aconitase_restored sit beside their enzymes with double borders and NO solid incoming edges (router-only).
5. Hover a dashed edge -> tooltip "known edit: point_mutation ... | claim ... | routes to ..."; pyr.pdh's dashed edge visibly crosses into the TCA column to tca.entry.
6. **(adjusted per deviation 1)** Click `bad.proton_leak`: its single claim chip is GREEN (ETC-UCP-01 approved). NO node shows an amber chip today -- the 4 pending BAD-* registry claims are unreferenced by story nodes; if that changes, chips/outlines turn amber automatically. Click `tca.shuffle`: both outgoing edges show "w=0.5", the cycle_trap edge shows "cond", node is teal (RNG).
7. Search "aconitase" -> only the aconitase family stays bright + "n matches"; segment button "TCA" dims everything else; "All" + Esc restore.
8. "Claims" toggle -> green outlines on claim-bearing nodes (NO amber outlines today, see #6); "end.true" button -> jumps to the True ending; panel shows the soul-jump dramatic text (electrons/soul -> ATP, carbon body shed as CO2).
9. fa.stub / alc.stub render grey + hatched with "Phase-8 stub" badges; their back edges arc over the top to intro.select.
10. "Review order" -> intro.preface highlighted + panel open at "1 / 57"; Next walks intro -> glycolysis -> pyruvate/anaerobic -> TCA -> ETC (end.true 37/57) -> endings -> edit.prompt (41/57) -> bad pool -> stubs "(Phase 8 -- sanctioned placeholder)"; Prev/Next wrap; toggle off exits.

**resume-signal:** reply "approved" or describe issues (issues -> fix + regenerate + re-verify).

## Authentication Gates

None -- pure offline stdlib tooling.

## Next Steps

- Human visual pass (checklist above) records the 07-18 verdict.
- The 4 pending BAD-* claims remain a registry-level decision for the 07-18 checkpoint ( Pitfall 9 C14-timescale decision also still pending at PROJECT level).
- If story content changes, rerun `python3.6 tools/story_graph_viewer.py` -- the 10 integrity gates re-verify every pinned invariant before any HTML is written.
