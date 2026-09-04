/* ==========================================================================
 * 30_graph.js — the SVG graph view: layout, render, interactions (07.1-06).
 *
 * OWNS: the #tab-graph mount's #graph-area sub-section (the shell's fixed
 * mount point). Loads after 00_core.js (EDITOR contract) and 05_json.js;
 * sorts before 40_form.js etc. Registers via EDITOR.view("graph", render)
 * + EDITOR.init(...) per the 07.1-04 registration convention.
 *
 * WHAT IT RENDERS: the full manifest-derived 7-column layered layout --
 * column = the node's source file (FILE_COL below), row = insertion order
 * within the column -- with derived kind/ending-level coloring, solid
 * choice.goto edges + amber dashed overlay edges (edits.json branch routes
 * and bad_ending_pool membership), zoom/pan, and click-to-select feeding
 * EDITOR.select (the node form, 40_form.js, listens to selection).
 *
 * LAYOUT PRIOR ART (ported, not invented): the committed viewer
 * tools/story_graph_viewer.py derives the exact same layout with NO stored
 * coordinates (the data has no x/y fields -- RESEARCH-UI anti-pattern 3).
 * Constants + FILE_COL + the edit.prompt hub lift + the edge geometry
 * classes are ported from `git show HEAD:tools/story_graph_viewer.py`:
 *   - layout constants ............ :57-64   (NODE_W/NODE_H/X0/Y0/pitches)
 *   - FILE_COL mapping ............ :66-75   (file -> column)
 *   - COL_LABELS .................. :76-84   (column captions)
 *   - build_model layout section .. :329-360 (col_members, edit.prompt lift
 *                                             to column-5 row 0, stubs ->
 *                                             column 6, pos = col x row)
 *   - _build_solid_edges .......... :494-568 (deduped goto pairs with
 *                                             merged labels/weights/conds/
 *                                             tags; fan/fwd/down/up/back)
 *   - _edge_geometry .............. :835-925 (path math per geometry class;
 *                                             dashed pairs get a +56px
 *                                             perpendicular offset so the
 *                                             dashed/solid overlap pairs
 *                                             stay visible)
 *   - _build_dashed_edges ......... :569-591 (enzyme -> branch_node)
 *   - _dashed_geo ................. :928-937 (same rules as solid)
 *   - palette .................... template CSS (ending true/good/normal/
 *                                             bad = gold/green/steel/red,
 *                                             restored purple, edit-prompt
 *                                             amber, stub hatch, rng teal,
 *                                             edit-allowed violet, story
 *                                             grey-blue) -- hexes ported
 *                                             verbatim.
 * The node VISUAL adds two editor-specific marks on top of the viewer's
 * language: a left color stripe (the ending-level color for endings, the
 * kind stroke color otherwise) and a kind badge chip (edit / wheel /
 * restored / stub / prompt). Node boxes whose file is dirty get a small
 * dot marker (reads EDITOR.state.dirty -- view only, never a mutation).
 *
 * VIEW STATE: zoom/pan live in a module-level transform ({tx, ty, scale})
 * that SURVIVES every rerender (RESEARCH-UI structural choice 3) -- the
 * render rebuilds the SVG contents and re-applies the same transform.
 * Wheel zoom is bounded to 0.4x-2.5x; "Reset view" restores the identity
 * transform. Node drag is deliberately NOT implemented (view-only pan is
 * the plan's requirement; any drag persistence would violate the no-stored-
 * coordinates rule).
 *
 * BUNDLE ACCESS: READ-ONLY. The renderer reads EDITOR.state.bundle (and
 * EDITOR.state.dirty) and NEVER writes to the bundle -- every mutation
 * belongs to the 00_core mutators (nodeSet/choiceUpdate/...), so undo
 * snapshots and dirty tracking stay truthful. The computed layout (pos,
 * edges) is a local view model rebuilt on every render and never persisted.
 *
 * STYLE: one classic script, one IIFE, ES5 only (var, no arrow functions,
 * no let/const, no modules) -- the emitted-page discipline pinned by
 * tests/test_story_editor_state.py.
 * ========================================================================== */

(function () {
  "use strict";

  var SVG_NS = "http://www.w3.org/2000/svg";

  // -------------------------------------------------------------------------
  // Layout constants -- ported VERBATIM from the committed viewer
  // (tools/story_graph_viewer.py:57-64). The plan's approximate numbers
  // ("box ~180x64, gaps ~24/~220") are superseded by the viewer's exact
  // values: the must-have is that the editor's layout derivation MATCHES
  // the committed viewer so the human's mental model transfers 1:1.
  // -------------------------------------------------------------------------

  var NODE_W = 190;   // node box width
  var NODE_H = 68;    // node box height
  var X0 = 60;        // first column x
  var Y0 = 90;        // first row y
  var COL_PITCH = 280; // column stride (box + gutter)
  var ROW_PITCH = 96;  // row stride (box + gap)
  var N_COLS = 7;

  // Source file -> column. Manifest order drives everything else (viewer
  // :66-75). endings.json AND bad_endings.json share column 5; intro.json
  // is column 0.
  var FILE_COL = {
    "intro.json": 0,
    "glycolysis.json": 1,
    "pyruvate_branch.json": 2,
    "tca.json": 3,
    "etc_atp.json": 4,
    "endings.json": 5,
    "bad_endings.json": 5
  };

  // Column captions with the Phase-8 stubs fallback (viewer :76-84).
  var COL_LABELS = {
    0: "Intro",
    1: "Glycolysis",
    2: "Pyruvate+Anaerobic",
    3: "TCA",
    4: "ETC+ATP",
    5: "Endings + Bad pool",
    6: "Phase-8 stubs"
  };

  // Unmapped ids -> column 6: the Phase-8 stub special ids (fa.stub /
  // alc.stub live in intro.json but belong in the stubs column) and any
  // node whose file is not in FILE_COL (future Phase-8 files). Mirrors the
  // viewer's `if nid in STUB_IDS: col = 6` + `FILE_COL.get(file_of, 6)`.
  var UNMAPPED_COL = 6;

  // Special node ids (viewer :87-89).
  var EDIT_PROMPT_ID = "edit.prompt";
  var STUB_IDS = { "fa.stub": true, "alc.stub": true };

  // Zoom bounds (plan: 0.4x-2.5x) + wheel step.
  var ZOOM_MIN = 0.4;
  var ZOOM_MAX = 2.5;
  var ZOOM_STEP = 1.1;

  // -------------------------------------------------------------------------
  // Derived-kind palette -- hexes ported verbatim from the committed
  // viewer's CSS (kind-ending-true/good/normal/bad, restored, edit-prompt,
  // phase8-stub, rng, edit-allowed, story). Kinds come from
  // EDITOR.deriveKind (the DERIVED precedence -- there is NO stored kind
  // field to read). The stripe uses the kind stroke color; endings carry
  // their ending-level color in BOTH box and stripe.
  // -------------------------------------------------------------------------

  var KIND_STYLE = {
    "ending-true": { fill: "#c9a227", stroke: "#8a6d1a" },
    "ending-good": { fill: "#2e8b57", stroke: "#1d5c3a" },
    "ending-normal": { fill: "#4682b4", stroke: "#2f5a7d" },
    "ending-bad": { fill: "#b22222", stroke: "#7a1717" },
    "restored": { fill: "#e6e0f5", stroke: "#6a4fc1", badge: "restored" },
    "edit-prompt": { fill: "#f5c16c", stroke: "#a8791f", badge: "prompt" },
    "phase8-stub": { fill: "url(#graph-hatch)", stroke: "#888888", badge: "stub" },
    "rng": { fill: "#17a2b8", stroke: "#0e6d78", badge: "wheel" },
    "edit-allowed": { fill: "#f0e6ff", stroke: "#8a2be2", badge: "edit" },
    "story": { fill: "#dfe7ef", stroke: "#9fb2c4" }
  };

  var STORY_FALLBACK_STYLE = KIND_STYLE["story"];

  // Ending-level colors -- the plan's palette (true=gold, good=green,
  // normal=steel, bad=red), keyed by the is_ending VALUE (via
  // EDITOR.endingTier, never a stored kind field). Same hexes as the
  // committed viewer's tier badges/boxes.
  var LEVEL_STYLE = {
    "true": "#c9a227",
    "good": "#2e8b57",
    "normal": "#4682b4",
    "bad": "#b22222"
  };

  // -------------------------------------------------------------------------
  // Module view state. The zoom/pan transform SURVIVES rerender (it is NOT
  // part of the SVG contents the render rebuilds); the bundle is never
  // touched here.
  // -------------------------------------------------------------------------

  var viewState = { tx: 0, ty: 0, scale: 1 };
  var dragState = null;      // { px, py, tx0, ty0 } while the mouse is down
  var panJustHappened = false; // suppress the click-selection right after a pan

  // Cached DOM refs (assigned by initGraph).
  var refs = {
    area: null,
    toolbar: null,
    svg: null,
    world: null,
    heads: null,
    edges: null,
    nodes: null,
    empty: null,
    canvasW: 2000,
    canvasH: 1900
  };

  // -------------------------------------------------------------------------
  // Small ES5 helpers.
  // -------------------------------------------------------------------------

  function svgEl(tag) {
    return document.createElementNS(SVG_NS, tag);
  }

  function clearEl(el) {
    if (!el) return;
    while (el.firstChild) {
      el.removeChild(el.firstChild);
    }
  }

  function isArr(v) {
    return Object.prototype.toString.call(v) === "[object Array]";
  }

  function truncId(nid) {
    // Viewer _trunc_id: full id, truncated past 22 chars with an ellipsis.
    var s = String(nid == null ? "" : nid);
    if (s.length <= 22) return s;
    return s.slice(0, 21) + "\u2026";
  }

  function flatText(text, cap) {
    // Viewer _flat_110: whitespace-flattened prefix for tooltips.
    var flat = String(text == null ? "" : text).split(/\s+/).join(" ");
    if (flat.length <= cap) return flat;
    return flat.slice(0, cap) + "\u2026";
  }

  function fileOrderOf(b) {
    if (b && isArr(b.order) && b.order.length) return b.order;
    return (b && b.files) ? Object.keys(b.files) : [];
  }

  function nodesOfFile(b, fname) {
    var f = (b && b.files) ? b.files[fname] : null;
    return (f && f.nodes && typeof f.nodes === "object") ? f.nodes : {};
  }

  // -------------------------------------------------------------------------
  // Layout derivation -- the port of build_model's layout section
  // (viewer :329-360). NO stored coordinates exist in the data; everything
  // is derived from the manifest's file order + insertion order per render.
  // -------------------------------------------------------------------------

  function pushId(colMembers, col, nid) {
    if (!colMembers[col]) colMembers[col] = [];
    colMembers[col].push(nid);
  }

  function computeLayout(b) {
    var order = fileOrderOf(b);
    var colMembers = {};   // col -> [ids in insertion order]
    var fileOf = {};       // id -> fname
    var nodeIds = [];      // file-order ids (edge-merge iteration, viewer parity)
    var i, j, col, nid;

    for (i = 0; i < order.length; i++) {
      var fname = order[i];
      var nodes = nodesOfFile(b, fname);
      for (nid in nodes) {
        if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
        var n = nodes[nid];
        if (!n || typeof n !== "object") continue;
        fileOf[nid] = fname;
        nodeIds.push(nid);
        if (nid === EDIT_PROMPT_ID) {
          continue; // lifted to column-5 row 0 below (viewer build_model)
        }
        if (STUB_IDS[nid]) {
          col = UNMAPPED_COL;
        } else {
          col = (FILE_COL[fname] !== undefined) ? FILE_COL[fname] : UNMAPPED_COL;
        }
        pushId(colMembers, col, nid);
      }
    }

    // edit.prompt: the hub the 15 solid edit:offer edges converge on ->
    // row 0 of the endings/bad column (viewer :337-345).
    if (fileOf[EDIT_PROMPT_ID] !== undefined) {
      if (!colMembers[5]) colMembers[5] = [];
      colMembers[5].unshift(EDIT_PROMPT_ID);
    }

    // pos = (col, row) -> pixel box origin. LOCAL view model only.
    var pos = {};
    var maxRows = 0;
    for (col = 0; col < N_COLS; col++) {
      var list = colMembers[col] || [];
      if (list.length > maxRows) maxRows = list.length;
      for (var r = 0; r < list.length; r++) {
        pos[list[r]] = {
          col: col,
          row: r,
          x: X0 + col * COL_PITCH,
          y: Y0 + r * ROW_PITCH
        };
      }
    }

    var layout = {
      pos: pos,
      fileOf: fileOf,
      order: [],
      solidEdges: [],
      dashedEdges: [],
      colCounts: {},
      canvasW: X0 + N_COLS * COL_PITCH + 90,
      canvasH: Y0 + maxRows * ROW_PITCH + 60
    };
    for (i = 0; i < nodeIds.length; i++) {
      if (pos[nodeIds[i]]) layout.order.push(nodeIds[i]);
    }
    for (col = 0; col < N_COLS; col++) {
      layout.colCounts[col] = (colMembers[col] || []).length;
    }

    buildSolidEdges(b, layout);
    buildDashedEdges(b, layout);
    return layout;
  }

  // -------------------------------------------------------------------------
  // Solid edges: deduped choice.goto pairs with merged choice annotations
  // (port of _build_solid_edges, viewer :494-568). Direction is inherent
  // src -> dst; the arrowhead marker carries it.
  // -------------------------------------------------------------------------

  function buildSolidEdges(b, layout) {
    var pos = layout.pos;
    var pairs = {};
    var pairOrder = [];
    var i;

    for (i = 0; i < layout.order.length; i++) {
      var nid = layout.order[i];
      var node = (b.files[layout.fileOf[nid]] && b.files[layout.fileOf[nid]].nodes)
        ? b.files[layout.fileOf[nid]].nodes[nid] : null;
      if (!node) continue;
      var choices = isArr(node.choices) ? node.choices : [];
      for (var c = 0; c < choices.length; c++) {
        var ch = choices[c];
        if (!ch || typeof ch !== "object") continue;
        var goto_ = ch.goto;
        if (!goto_) continue;
        var key = nid + "\u0001" + goto_;
        var rec = pairs[key];
        if (!rec) {
          rec = {
            src: nid, dst: goto_, labels: [], weights: [], conds: [],
            choiceTags: [], count: 0
          };
          pairs[key] = rec;
          pairOrder.push(key);
        }
        rec.count += 1;
        var label = (ch.label == null) ? "" : String(ch.label).replace(/^\s+|\s+$/g, "");
        if (label && rec.labels.indexOf(label) < 0) rec.labels.push(label);
        if (ch.weight !== undefined && ch.weight !== null) {
          rec.weights.push(ch.weight);
        }
        var cond = ch.cond;
        if (cond && rec.conds.indexOf(cond) < 0) rec.conds.push(cond);
        var tags = isArr(ch.tags) ? ch.tags : [];
        for (var t = 0; t < tags.length; t++) {
          var tv = String(tags[t]);
          if (rec.choiceTags.indexOf(tv) < 0) rec.choiceTags.push(tv);
        }
      }
    }

    // Geometry class per pair (viewer :526-556): fan for the edit.prompt
    // hub's structural choices through the right gutter; fwd / down straight;
    // up = right-side bow per column; back = wide arc over the top.
    var upCounter = {};
    var backCount = 0;
    var fanCount = 0;

    for (i = 0; i < pairOrder.length; i++) {
      rec = pairs[pairOrder[i]];
      var s = pos[rec.src];
      var d = pos[rec.dst];
      var geo, bow;
      if (!d) {
        // Dangling goto: keep the edge (the validator reports it); draw it
        // collapsing into the source cell so the render never crashes.
        d = s;
      }
      if (rec.src === EDIT_PROMPT_ID) {
        geo = "fan";
        bow = 1662 + 6 * fanCount;
        fanCount += 1;
      } else if (d.col > s.col) {
        geo = "fwd"; bow = 0;
      } else if (d.col === s.col && d.row > s.row) {
        geo = "down"; bow = 0;
      } else if (d.col === s.col) {
        geo = "up";
        bow = 46 + 34 * (upCounter[s.col] || 0);
        upCounter[s.col] = (upCounter[s.col] || 0) + 1;
      } else {
        geo = "back";
        bow = 110 + 55 * backCount;
        backCount += 1;
      }
      var sharedWeight = null;
      if (rec.weights.length) {
        var same = true;
        for (var w = 1; w < rec.weights.length; w++) {
          if (rec.weights[w] !== rec.weights[0]) { same = false; break; }
        }
        if (same) sharedWeight = rec.weights[0];
      }
      layout.solidEdges.push({
        src: rec.src, dst: rec.dst, labels: rec.labels, count: rec.count,
        weight: sharedWeight, conds: rec.conds, choiceTags: rec.choiceTags,
        geo: geo, bow: bow, dashed: false
      });
    }
  }

  // -------------------------------------------------------------------------
  // Dashed overlay edges (amber, viewer parity):
  //   (1) known-edit routes: edits.json enzyme bucket -> branch_node
  //       (port of _build_dashed_edges, viewer :569-591)
  //   (2) bad_ending_pool membership: edit.prompt -> each global pool
  //       member, plus any per-enzyme pool override (schema-supported;
  //       the current data carries only the global 2-member pool)
  // -------------------------------------------------------------------------

  function buildDashedEdges(b, layout) {
    var pos = layout.pos;
    var edits = (b && b.edits && typeof b.edits === "object") ? b.edits : {};
    var buckets = (edits.enzymes && typeof edits.enzymes === "object")
      ? edits.enzymes : {};
    var bucketId, e, i;

    for (bucketId in buckets) {
      if (!Object.prototype.hasOwnProperty.call(buckets, bucketId)) continue;
      var bucket = buckets[bucketId];
      if (!bucket || typeof bucket !== "object") continue;
      var list = isArr(bucket.edits) ? bucket.edits : [];
      for (i = 0; i < list.length; i++) {
        e = list[i];
        if (!e || typeof e !== "object") continue;
        var branch = e.branch_node;
        if (!branch) continue;
        var sig = (e.signature && typeof e.signature === "object")
          ? e.signature : {};
        var args = (sig.args && typeof sig.args === "object") ? sig.args : {};
        var newRes = (args.new_res !== undefined) ? args.new_res
          : (args.new_resn !== undefined ? args.new_resn : "?");
        layout.dashedEdges.push({
          src: bucketId,
          dst: branch,
          geo: dashedGeoClass(pos, bucketId, branch),
          sigText: sig.op + " " + sig.target + " -> " + newRes,
          claimId: e.claim_id,
          note: "known edit"
        });
      }
    }

    // Global bad_ending_pool membership: the edit.prompt hub owns the pool
    // picks (unknown edits land here), so membership edges run FROM the hub.
    if (pos[EDIT_PROMPT_ID]) {
      var pool = isArr(edits.bad_ending_pool) ? edits.bad_ending_pool : [];
      for (i = 0; i < pool.length; i++) {
        var member = pool[i];
        if (!member || !pos[member]) continue;
        layout.dashedEdges.push({
          src: EDIT_PROMPT_ID,
          dst: member,
          geo: dashedGeoClass(pos, EDIT_PROMPT_ID, member),
          sigText: "bad_ending_pool member",
          claimId: null,
          note: "pool"
        });
      }
    }

    // Per-enzyme pool overrides (none in the current data; the schema
    // allows them -- render them so the view stays honest if they appear).
    for (bucketId in buckets) {
      if (!Object.prototype.hasOwnProperty.call(buckets, bucketId)) continue;
      var bkt = buckets[bucketId];
      if (!bkt || typeof bkt !== "object") continue;
      var bp = isArr(bkt.bad_ending_pool) ? bkt.bad_ending_pool : [];
      for (i = 0; i < bp.length; i++) {
        var m2 = bp[i];
        if (!m2 || !pos[m2] || !pos[bucketId]) continue;
        layout.dashedEdges.push({
          src: bucketId,
          dst: m2,
          geo: dashedGeoClass(pos, bucketId, m2),
          sigText: "per-enzyme bad_ending_pool override",
          claimId: null,
          note: "pool"
        });
      }
    }
  }

  // Geometry class for a dashed edge -- same rules as solid
  // (port of _dashed_geo, viewer :928-937).
  function dashedGeoClass(pos, src, dst) {
    var s = pos[src];
    var d = pos[dst];
    if (!s || !d) return "fwd";
    if (d.col > s.col) return "fwd";
    if (d.col === s.col && d.row > s.row) return "down";
    if (d.col === s.col) return "up";
    return "back";
  }

  // -------------------------------------------------------------------------
  // Edge path math -- port of _edge_geometry (viewer :835-925), including
  // the +56px perpendicular curvature offset for dashed edges so a
  // dashed/solid overlapping pair stays visible, and the mid-label anchor
  // for weight/cond captions. Returns {d, lx, ly, anchor}.
  // -------------------------------------------------------------------------

  function edgeGeometry(s, d, geo, bow, dashed) {
    var w = NODE_W;
    var h = NODE_H;
    var scx = s.x + w / 2;
    var scy = s.y + h / 2;
    var tcx = d.x + w / 2;
    var tcy = d.y + h / 2;
    var k = 45;
    var x1, y1, x2, y2, ym, dx, dy, ln, ux, uy, px, py;
    var cx1, cy1, cx2, cy2, mx, my;

    if (geo === "down") {
      x1 = scx; y1 = s.y + h; x2 = tcx; y2 = d.y;
      ym = (y1 + y2) / 2;
      if (dashed) {
        return {
          d: "M " + (x1 + 18) + " " + y1 +
             " C " + (x1 + 58) + " " + ym + " " + (x2 + 58) + " " + ym +
             " " + (x2 + 42) + " " + y2,
          lx: x1 + 52, ly: ym, anchor: "start"
        };
      }
      return {
        d: "M " + x1 + " " + y1 + " L " + x2 + " " + y2,
        lx: x1 + 12, ly: ym + 4, anchor: "start"
      };
    }
    if (geo === "fwd") {
      x1 = s.x + w; y1 = scy; x2 = d.x; y2 = tcy;
      dx = x2 - x1; dy = y2 - y1;
      ln = Math.sqrt(dx * dx + dy * dy) || 1;
      ux = dx / ln; uy = dy / ln;
      if (dashed) {
        px = uy * 56;
        py = -ux * 56;
        cx1 = x1 + k * ux + px; cy1 = y1 + k * uy + py;
        cx2 = x2 - k * ux + px; cy2 = y2 - k * uy + py;
        mx = (x1 + 3 * cx1 + 3 * cx2 + x2) / 8;
        my = (y1 + 3 * cy1 + 3 * cy2 + y2) / 8;
        return {
          d: "M " + x1 + " " + y1 + " C " + cx1 + " " + cy1 + " " +
             cx2 + " " + cy2 + " " + x2 + " " + y2,
          lx: mx, ly: my - 4, anchor: "middle"
        };
      }
      return {
        d: "M " + x1 + " " + y1 + " C " + (x1 + k) + " " + y1 + " " +
           (x2 - k) + " " + y2 + " " + x2 + " " + y2,
        lx: (x1 + x2) / 2, ly: (y1 + y2) / 2 - 6, anchor: "middle"
      };
    }
    if (geo === "up") {
      x1 = s.x + w; y1 = scy; x2 = d.x + w; y2 = tcy;
      return {
        d: "M " + x1 + " " + y1 + " C " + (x1 + bow) + " " + y1 + " " +
           (x2 + bow) + " " + y2 + " " + x2 + " " + y2,
        lx: (x1 + x2) / 2 + bow * 0.75, ly: (y1 + y2) / 2 - 4, anchor: "middle"
      };
    }
    if (geo === "fan") {
      var gx = bow;
      return {
        d: "M " + (s.x + w) + " " + scy + " C " + gx + " " + scy + " " +
           gx + " " + tcy + " " + (d.x + w) + " " + tcy,
        lx: gx, ly: (scy + tcy) / 2, anchor: "middle"
      };
    }
    // "back": wide arc over the top of the canvas.
    var yc = Math.min(s.y, d.y) - bow;
    return {
      d: "M " + scx + " " + s.y + " C " + scx + " " + yc + " " +
         tcx + " " + yc + " " + tcx + " " + d.y,
      lx: (scx + tcx) / 2, ly: yc - 4, anchor: "middle"
    };
  }

  function edgeTooltip(e) {
    var lines = [e.src + " -> " + e.dst,
                 "choices (" + e.count + "): " + (e.labels.join(" | ") || "-")];
    if (e.weight !== null && e.weight !== undefined) {
      lines.push("weight: " + e.weight + " (all merged choices)");
    }
    if (e.conds.length) lines.push("cond: " + e.conds.join(" AND "));
    if (e.choiceTags.length) {
      lines.push("choice tags: " + e.choiceTags.join(", "));
    }
    return lines.join("\n");
  }

  // -------------------------------------------------------------------------
  // Render. Registered as EDITOR.view("graph", renderGraph) so the core's
  // rerender dispatcher (hooks.rerender[0]) re-runs it after every
  // mutation, selection change and undo/redo. Rebuilds the SVG contents
  // and RE-APPLIES the surviving view transform.
  // -------------------------------------------------------------------------

  function setAttr(el, name, value) {
    el.setAttribute(name, String(value));
  }

  function applyTransform() {
    if (!refs.world) return;
    setAttr(refs.world, "transform",
            "translate(" + viewState.tx + "," + viewState.ty + ") " +
            "scale(" + viewState.scale + ")");
  }

  function resetView() {
    viewState.tx = 0;
    viewState.ty = 0;
    viewState.scale = 1;
    applyTransform();
  }

  function renderGraph() {
    if (!refs.svg) return; // initGraph has not run yet
    clearEl(refs.heads);
    clearEl(refs.edges);
    clearEl(refs.nodes);

    var b = EDITOR.state.bundle; // READ-ONLY access (see header)
    if (!b || !b.files) {
      showEmptyState(true);
      return;
    }
    showEmptyState(false);

    var layout = computeLayout(b);
    refs.canvasW = layout.canvasW;
    refs.canvasH = layout.canvasH;
    setAttr(refs.svg, "viewBox", "0 0 " + layout.canvasW + " " + layout.canvasH);

    renderHeaders(layout);
    renderEdges(layout);
    renderNodes(layout);
    applyTransform();
  }

  function renderHeaders(layout) {
    for (var col = 0; col < N_COLS; col++) {
      var t = svgEl("text");
      setAttr(t, "class", "col-header");
      setAttr(t, "x", X0 + col * COL_PITCH);
      setAttr(t, "y", 64);
      t.textContent = COL_LABELS[col] + " (" + (layout.colCounts[col] || 0) + ")";
      refs.heads.appendChild(t);
    }
  }

  function renderEdges(layout) {
    var pos = layout.pos;
    var i, g, geo;

    for (i = 0; i < layout.solidEdges.length; i++) {
      var e = layout.solidEdges[i];
      var s = pos[e.src];
      var d = pos[e.dst] || s;
      geo = edgeGeometry(s, d, e.geo, e.bow, false);
      var p = svgEl("path");
      setAttr(p, "class", "edge-solid");
      setAttr(p, "d", geo.d);
      setAttr(p, "marker-end", "url(#arrow-solid)");
      var tip = svgEl("title");
      tip.textContent = edgeTooltip(e);
      p.appendChild(tip);
      refs.edges.appendChild(p);
      // RNG-weight / conditional mid-labels (viewer parity).
      var label = null;
      var condLabel = false;
      if (e.weight !== null && e.weight !== undefined) {
        label = "w=" + e.weight;
      } else if (e.conds.length) {
        label = "cond";
        condLabel = true;
      }
      if (label) {
        var lt = svgEl("text");
        setAttr(lt, "class", "edge-midlabel" + (condLabel ? " cond-label" : ""));
        setAttr(lt, "x", geo.lx);
        setAttr(lt, "y", geo.ly);
        setAttr(lt, "text-anchor", geo.anchor);
        lt.textContent = label;
        refs.edges.appendChild(lt);
      }
    }

    for (i = 0; i < layout.dashedEdges.length; i++) {
      var de = layout.dashedEdges[i];
      var ds = pos[de.src];
      var dd = pos[de.dst] || ds;
      if (!ds) continue;
      geo = edgeGeometry(ds, dd, de.geo, 0, true);
      var dp = svgEl("path");
      setAttr(dp, "class", "edge-dashed");
      setAttr(dp, "d", geo.d);
      setAttr(dp, "marker-end", "url(#arrow-amber)");
      var dtip = svgEl("title");
      dtip.textContent = de.note + ": " + de.sigText.replace(/ -> /g, " \u2192 ") +
        (de.claimId ? (" | claim " + de.claimId) : "") +
        " | routes to " + de.dst;
      dp.appendChild(dtip);
      refs.edges.appendChild(dp);
    }
  }

  function nodeTooltip(id, node, kind, layout) {
    var file = layout.fileOf[id] || "?";
    var p = layout.pos[id] || { col: -1, row: -1 };
    var lines = [
      id,
      "kind: " + kind + " | file: " + file + " | col " + p.col + " row " + p.row
    ];
    // Cast entry (if any) -- read-only provenance for the tooltip.
    var castDoc = (EDITOR.state.bundle && EDITOR.state.bundle.cast) || null;
    if (castDoc && isArr(castDoc.enzymes)) {
      for (var i = 0; i < castDoc.enzymes.length; i++) {
        var ce = castDoc.enzymes[i];
        if (ce && ce.id === id && ce.pdb_id) {
          lines.push("cast: " + (ce.label || id) + " [" + ce.pdb_id + "]");
          break;
        }
      }
    }
    lines.push(flatText(node && node.text_dramatic, 110));
    return lines.join("\n");
  }

  function renderNodes(layout) {
    var b = EDITOR.state.bundle;
    var dirty = EDITOR.state.dirty || {};
    var sel = EDITOR.state.sel;

    for (var i = 0; i < layout.order.length; i++) {
      var id = layout.order[i];
      var file = layout.fileOf[id];
      var node = (b.files[file] && b.files[file].nodes) ? b.files[file].nodes[id] : null;
      if (!node) continue;
      var kind = EDITOR.deriveKind(node); // DERIVED kind -- never a stored field
      var style = KIND_STYLE[kind] || STORY_FALLBACK_STYLE;
      var p = layout.pos[id];
      // Ending level comes from EDITOR.endingTier (is_ending ONLY -- never
      // the ending:* tag: the 3 anaerobic endings carry no ending:* tag).
      var level = EDITOR.endingTier(node);
      var levelColor = (level && LEVEL_STYLE[level]) ? LEVEL_STYLE[level] : null;
      var boxFill = levelColor || style.fill;
      var stripeColor = levelColor || style.stroke;

      var g = svgEl("g");
      setAttr(g, "class", "node kind-" + kind +
              (sel === id ? " selected" : ""));
      setAttr(g, "data-node-id", id);
      setAttr(g, "transform", "translate(" + p.x + "," + p.y + ")");

      if (kind === "restored") {
        // Double-border effect for the router-only restored nodes
        // (viewer render_svg_nodes).
        var outer = svgEl("rect");
        setAttr(outer, "class", "node-outer");
        setAttr(outer, "x", -5);
        setAttr(outer, "y", -5);
        setAttr(outer, "width", NODE_W + 10);
        setAttr(outer, "height", NODE_H + 10);
        setAttr(outer, "rx", 11);
        setAttr(outer, "stroke", style.stroke);
        g.appendChild(outer);
      }

      var box = svgEl("rect");
      setAttr(box, "class", "node-box");
      setAttr(box, "width", NODE_W);
      setAttr(box, "height", NODE_H);
      setAttr(box, "rx", 8);
      setAttr(box, "fill", boxFill);
      setAttr(box, "stroke", style.stroke);
      g.appendChild(box);

      // Left color stripe: the ending-level color for endings, the kind
      // accent otherwise.
      var stripe = svgEl("rect");
      setAttr(stripe, "class", "node-stripe");
      setAttr(stripe, "x", 0);
      setAttr(stripe, "y", 0);
      setAttr(stripe, "width", 6);
      setAttr(stripe, "height", NODE_H);
      setAttr(stripe, "fill", stripeColor);
      g.appendChild(stripe);

      var label = svgEl("text");
      setAttr(label, "class", "node-label");
      setAttr(label, "x", NODE_W / 2);
      setAttr(label, "y", NODE_H / 2 + 5);
      label.textContent = truncId(id);
      g.appendChild(label);

      if (style.badge) {
        var chipW = 14 + style.badge.length * 6;
        var chip = svgEl("rect");
        setAttr(chip, "class", "node-badge-chip");
        setAttr(chip, "x", NODE_W - chipW - 6);
        setAttr(chip, "y", NODE_H - 18);
        setAttr(chip, "width", chipW);
        setAttr(chip, "height", 14);
        setAttr(chip, "rx", 7);
        g.appendChild(chip);
        var chipText = svgEl("text");
        setAttr(chipText, "class", "node-badge-text");
        setAttr(chipText, "x", NODE_W - chipW - 6 + chipW / 2);
        setAttr(chipText, "y", NODE_H - 18 + 10.5);
        chipText.textContent = style.badge;
        g.appendChild(chipText);
      }

      // Dirty hint: a subtle dot on nodes whose file has changes
      // (reads EDITOR.state.dirty -- presence-of-key per file; view only).
      if (dirty[file]) {
        var dot = svgEl("circle");
        setAttr(dot, "class", "node-dirty-dot");
        setAttr(dot, "cx", NODE_W - 10);
        setAttr(dot, "cy", 10);
        setAttr(dot, "r", 4);
        g.appendChild(dot);
      }

      var tip = svgEl("title");
      tip.textContent = nodeTooltip(id, node, kind, layout);
      g.appendChild(tip);

      refs.nodes.appendChild(g);
    }
  }

  // -------------------------------------------------------------------------
  // Empty state: no bundle -> a placeholder pointing at the boot panel
  // (the load layer, 10_load.js, fills the boot panel's mounts).
  // -------------------------------------------------------------------------

  function showEmptyState(show) {
    if (!refs.area) return;
    if (show) {
      if (!refs.empty) {
        refs.empty = document.createElement("div");
        refs.empty.id = "graph-empty-state";
        var t = document.createElement("p");
        t.textContent = "No data loaded \u2014 the graph needs the story bundle.";
        var t2 = document.createElement("p");
        t2.textContent = "Load data first: use the boot panel at the top of " +
          "the page (silent probe or folder pick).";
        var btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = "Show boot panel";
        btn.addEventListener("click", function () {
          var boot = document.getElementById("boot-panel");
          if (boot && boot.scrollIntoView) boot.scrollIntoView();
        });
        refs.empty.appendChild(t);
        refs.empty.appendChild(t2);
        refs.empty.appendChild(btn);
        refs.area.appendChild(refs.empty);
      }
      refs.empty.style.display = "flex";
      refs.svg.style.display = "none";
      refs.toolbar.style.display = "none";
    } else {
      if (refs.empty) refs.empty.style.display = "none";
      refs.svg.style.display = "block";
      refs.toolbar.style.display = "flex";
    }
  }

  // -------------------------------------------------------------------------
  // Zoom / pan (view-only transforms; RESEARCH-UI structural choice 3).
  // Pointer coordinates map client px -> viewBox units through the "meet"
  // scaling (uniform k + centering offsets) so zoom-at-cursor is exact.
  // -------------------------------------------------------------------------

  function viewBoxPoint(ev) {
    var rect = refs.svg.getBoundingClientRect();
    var kx = rect.width > 0 ? refs.canvasW / rect.width : 1;
    var ky = rect.height > 0 ? refs.canvasH / rect.height : 1;
    var k = Math.min(kx, ky);
    var ox = (rect.width - refs.canvasW * k) / 2;
    var oy = (rect.height - refs.canvasH * k) / 2;
    return {
      x: (ev.clientX - rect.left - ox) / (k || 1),
      y: (ev.clientY - rect.top - oy) / (k || 1)
    };
  }

  function onWheel(ev) {
    if (!refs.svg) return;
    if (ev.preventDefault) ev.preventDefault();
    var pt = viewBoxPoint(ev);
    var factor = (ev.deltaY < 0) ? ZOOM_STEP : 1 / ZOOM_STEP;
    var next = viewState.scale * factor;
    if (next < ZOOM_MIN) next = ZOOM_MIN;
    if (next > ZOOM_MAX) next = ZOOM_MAX;
    if (next === viewState.scale) return;
    var ratio = next / viewState.scale;
    viewState.tx = pt.x - (pt.x - viewState.tx) * ratio;
    viewState.ty = pt.y - (pt.y - viewState.ty) * ratio;
    viewState.scale = next;
    applyTransform();
  }

  function onMouseDown(ev) {
    if (!refs.svg || ev.button !== 0) return;
    if (ev.preventDefault) ev.preventDefault();
    dragState = { px: ev.clientX, py: ev.clientY, tx0: viewState.tx, ty0: viewState.ty };
    refs.svg.className = "panning";
  }

  function onMouseMove(ev) {
    if (!dragState) return;
    var dx = ev.clientX - dragState.px;
    var dy = ev.clientY - dragState.py;
    viewState.tx = dragState.tx0 + dx;
    viewState.ty = dragState.ty0 + dy;
    applyTransform();
  }

  function onMouseUp() {
    if (!dragState) return;
    var moved = (viewState.tx !== dragState.tx0) || (viewState.ty !== dragState.ty0);
    dragState = null;
    if (refs.svg) refs.svg.className = "";
    if (moved) {
      // A pan just happened: swallow the trailing click so a drag does not
      // also flip the selection.
      panJustHappened = true;
      setTimeout(function () { panJustHappened = false; }, 0);
    }
  }

  function onSelectClick(el) {
    if (panJustHappened) return;
    EDITOR.select(el.getAttribute("data-node-id"));
  }

  // Double-click: select AND bring the node form into view (the form panel
  // renders into the sibling #node-form aside; 40_form.js owns its content).
  function onDblClick(el) {
    EDITOR.select(el.getAttribute("data-node-id"));
    var form = document.getElementById("node-form");
    if (form && !form.hidden) {
      if (form.scrollIntoView) form.scrollIntoView();
      var field = form.querySelector("input, textarea, select");
      if (field && field.focus) {
        try { field.focus(); } catch (e) { /* non-focusable is fine */ }
      }
    }
  }

  // -------------------------------------------------------------------------
  // SVG defs: arrowhead markers (grey solid / amber dashed) + the stub
  // hatch pattern -- port of render_svg_defs (viewer :792-815).
  // -------------------------------------------------------------------------

  function buildDefs() {
    var defs = svgEl("defs");

    var mSolid = svgEl("marker");
    setAttr(mSolid, "id", "arrow-solid");
    setAttr(mSolid, "viewBox", "0 0 10 10");
    setAttr(mSolid, "refX", 9);
    setAttr(mSolid, "refY", 5);
    setAttr(mSolid, "markerWidth", 7);
    setAttr(mSolid, "markerHeight", 7);
    setAttr(mSolid, "orient", "auto-start-reverse");
    var pSolid = svgEl("path");
    setAttr(pSolid, "d", "M 0 0 L 10 5 L 0 10 z");
    setAttr(pSolid, "fill", "#666666");
    mSolid.appendChild(pSolid);
    defs.appendChild(mSolid);

    var mAmber = svgEl("marker");
    setAttr(mAmber, "id", "arrow-amber");
    setAttr(mAmber, "viewBox", "0 0 10 10");
    setAttr(mAmber, "refX", 9);
    setAttr(mAmber, "refY", 5);
    setAttr(mAmber, "markerWidth", 7);
    setAttr(mAmber, "markerHeight", 7);
    setAttr(mAmber, "orient", "auto-start-reverse");
    var pAmber = svgEl("path");
    setAttr(pAmber, "d", "M 0 0 L 10 5 L 0 10 z");
    setAttr(pAmber, "fill", "#d97706");
    mAmber.appendChild(pAmber);
    defs.appendChild(mAmber);

    var hatch = svgEl("pattern");
    setAttr(hatch, "id", "graph-hatch");
    setAttr(hatch, "width", 8);
    setAttr(hatch, "height", 8);
    setAttr(hatch, "patternUnits", "userSpaceOnUse");
    setAttr(hatch, "patternTransform", "rotate(45)");
    var hRect = svgEl("rect");
    setAttr(hRect, "width", 8);
    setAttr(hRect, "height", 8);
    setAttr(hRect, "fill", "#cccccc");
    hatch.appendChild(hRect);
    var hLine = svgEl("line");
    setAttr(hLine, "x1", 0);
    setAttr(hLine, "y1", 0);
    setAttr(hLine, "x2", 0);
    setAttr(hLine, "y2", 8);
    setAttr(hLine, "stroke", "#a8a8a8");
    setAttr(hLine, "stroke-width", 3);
    hatch.appendChild(hLine);
    defs.appendChild(hatch);

    return defs;
  }

  // -------------------------------------------------------------------------
  // Init: build the static DOM (toolbar + svg + groups), wire the events,
  // and register the renderer. Runs once from the shell bootstrap.
  // -------------------------------------------------------------------------

  function initGraph() {
    var area = document.getElementById("graph-area");
    if (!area) return;
    refs.area = area;

    // Toolbar: hint + reset-view (the plan's "reset view" button).
    var bar = document.createElement("div");
    bar.id = "graph-toolbar";
    var hint = document.createElement("span");
    hint.className = "graph-hint";
    hint.textContent = "wheel = zoom (0.4\u00d7\u20132.5\u00d7) \u00b7 drag = pan \u00b7 " +
      "click = select \u00b7 double-click = open the node form";
    var resetBtn = document.createElement("button");
    resetBtn.type = "button";
    resetBtn.id = "graph-reset-view";
    resetBtn.textContent = "Reset view";
    resetBtn.addEventListener("click", resetView);
    bar.appendChild(hint);
    bar.appendChild(resetBtn);
    area.appendChild(bar);
    refs.toolbar = bar;

    // SVG skeleton: defs + world( headers, edges, nodes ).
    var svg = svgEl("svg");
    svg.setAttribute("id", "graph-svg");
    svg.appendChild(buildDefs());
    var world = svgEl("g");
    world.setAttribute("id", "graph-world");
    var heads = svgEl("g");
    heads.setAttribute("id", "graph-headers");
    var edges = svgEl("g");
    edges.setAttribute("id", "graph-edges");
    var nodes = svgEl("g");
    nodes.setAttribute("id", "graph-nodes");
    world.appendChild(heads);
    world.appendChild(edges);
    world.appendChild(nodes);
    svg.appendChild(world);
    area.appendChild(svg);
    refs.svg = svg;
    refs.world = world;
    refs.heads = heads;
    refs.edges = edges;
    refs.nodes = nodes;

    // Events: ONE listener per concern (event delegation, RESEARCH-UI
    // structural choice 2 -- never per-node listeners).
    svg.addEventListener("wheel", onWheel, false);
    svg.addEventListener("mousedown", onMouseDown, false);
    window.addEventListener("mousemove", onMouseMove, false);
    window.addEventListener("mouseup", onMouseUp, false);
    EDITOR.delegate(svg, "click", "data-node-id", onSelectClick);
    EDITOR.delegate(svg, "dblclick", "data-node-id", onDblClick);

    // First render for whatever state exists at boot (typically empty).
    renderGraph();
  }

  // Registration: the view + the init (07.1-04 contract).
  EDITOR.view("graph", renderGraph);
  EDITOR.init(initGraph);

  // -------------------------------------------------------------------------
  // Asset CSS (injected at runtime per the pipeline's per-feature CSS rule):
  // svg sizing, node/edge styles, badges, toolbar, empty state.
  // -------------------------------------------------------------------------

  EDITOR.injectCss(
    "/* injected by 30_graph.js (07.1-06): graph view styles */\n" +
    "#graph-area { position: relative; display: flex; flex-direction: column; overflow: hidden; }\n" +
    "#graph-toolbar { flex: none; display: flex; align-items: center; gap: 10px; padding: 6px 10px; font-size: 12px; color: #555555; background: #f5f6f8; border-bottom: 1px solid #dde3ec; }\n" +
    "#graph-toolbar .graph-hint { flex: 1; }\n" +
    "#graph-svg { flex: 1 1 auto; width: 100%; height: 100%; display: block; cursor: grab; background: #fbfcfe; }\n" +
    "#graph-svg.panning { cursor: grabbing; }\n" +
    ".node { cursor: pointer; }\n" +
    ".node.selected .node-box { stroke: #1f6feb; stroke-width: 3.5; }\n" +
    ".node-label { font: 11px Consolas, monospace; text-anchor: middle; fill: #1a1a1a; paint-order: stroke; stroke: #ffffff; stroke-width: 3px; stroke-linejoin: round; pointer-events: none; }\n" +
    ".node-badge-chip { fill: #ffffff; fill-opacity: 0.85; stroke: #999999; stroke-width: 0.5; pointer-events: none; }\n" +
    ".node-badge-text { font: 9px 'Segoe UI', Arial, sans-serif; fill: #555555; text-anchor: middle; pointer-events: none; }\n" +
    ".node-stripe { pointer-events: none; }\n" +
    ".node-outer { fill: none; stroke-width: 3; pointer-events: none; }\n" +
    ".node-dirty-dot { fill: #e25822; stroke: #ffffff; stroke-width: 1; pointer-events: none; }\n" +
    ".col-header { font: bold 14px 'Segoe UI', Arial, sans-serif; fill: #444444; }\n" +
    ".edge-solid { stroke: #666666; stroke-width: 1.5; fill: none; }\n" +
    ".edge-dashed { stroke: #d97706; stroke-width: 2; stroke-dasharray: 7 5; fill: none; }\n" +
    ".edge-midlabel { font: 10px 'Segoe UI', Arial, sans-serif; fill: #444444; paint-order: stroke; stroke: #ffffff; stroke-width: 3px; stroke-linejoin: round; pointer-events: none; }\n" +
    ".edge-midlabel.cond-label { fill: #aa3333; }\n" +
    "#graph-empty-state { flex: 1 1 auto; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; color: #555555; font-size: 14px; }\n" +
    "#graph-empty-state p { margin: 2px 0; }\n"
  );

})();
