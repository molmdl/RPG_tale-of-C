/* ==========================================================================
 * 60_trace.js — the Trace tab: path tracing as a nested list (07.1-10).
 *
 * OWNS: the #tab-trace panel (the shell's fixed mount). Registers via
 * EDITOR.view("trace", renderTrace) + EDITOR.init(...) per the 07.1-04
 * registration convention. This is Requirement D: "a tab/button/panel to
 * trace a path and show the traced flow as a nested list, to view as a
 * full story" (07.1-RESEARCH-UI "Path tracing (D)").
 *
 * THE WALK IS GOTO-ONLY, BY DESIGN: traceWalk follows choice.goto edges in
 * choice order and consults NOTHING else about a choice — cond gates
 * runtime eligibility and weight picks RNG outcomes, but neither alters
 * graph STRUCTURE, so the trace must ignore them both. This mirrors the
 * reachability BFS exactly (check_reachability, rpg/story/validate.py:167;
 * follow rule :198-200 — existing targets only, each node once), so the
 * traced node set always AGREES with the Python gate: whatever the trace
 * renders as reachable is exactly what validate.py counts as reachable.
 * The walk lives in a named, isolated function as a TEST CONTRACT:
 * tests/test_story_editor_trace.py pins that the traceWalk body contains
 * no weight/cond tokens (weight/cond appear only in the DISPLAY layer
 * below, as row annotations).
 *
 * CYCLE GUARD (required once editors can create arbitrary edges): a global
 * visited set bounds the DFS — a node reached a second time renders a
 * "↩ already shown" marker instead of recursing. No cycles exist in the
 * current data (the restored nodes have 0 incoming choice edges), but the
 * editor can create arbitrary goto edges, so the guard is mandatory
 * (07.1-RESEARCH-UI "Path tracing (D)").
 *
 * CONTROLS: start-node select (every node id, grouped by source file;
 * default = manifest.start, i.e. intro.preface), "Trace from selected
 * graph node" (consumes EDITOR.state.sel as set by the graph's
 * click-select), "Copy as text" (indented plain text via a fallback-safe
 * clipboard path — file:// pages may have clipboard writes restricted, so
 * navigator.clipboard falls back to execCommand and finally to a
 * select-a-textarea manual copy), and "Collapse all / Expand all".
 *
 * EXPAND/COLLAPSE: branches with children render as <details>/<summary>;
 * open/closed state persists across rerenders in a module map keyed by
 * node id (harvested from the live DOM before each rebuild, re-applied
 * after). The trace re-runs on every afterChange (view registration), so
 * in-progress edits reflect immediately.
 *
 * BUNDLE ACCESS: READ-ONLY (same contract as 30_graph.js) — the tracer
 * never writes the bundle; every mutation belongs to the 00_core mutators.
 *
 * STYLE: one classic script, one IIFE, ES5 only (var, no arrow functions,
 * no let/const, no modules) — pinned page-wide by
 * tests/test_story_editor_state.py and per-asset by the trace battery.
 * ========================================================================== */

(function () {
  "use strict";

  // -------------------------------------------------------------------------
  // Module view-state (survives rerenders; never persisted anywhere).
  //   expandedById — node id -> boolean (details open state); ids absent
  //                  from the map default to expanded.
  //   lastTraceText — the plain-text rendering of the CURRENT trace, rebuilt
  //                  on every render and consumed by "Copy as text".
  // -------------------------------------------------------------------------

  var expandedById = {};
  var lastTraceText = null;

  // -------------------------------------------------------------------------
  // Small DOM helpers (ES5; text nodes only for user-visible strings so no
  // escaping holes exist; EDITOR.esc is reserved for attribute values).
  // -------------------------------------------------------------------------

  function clearEl(el) {
    while (el.firstChild) {
      el.removeChild(el.firstChild);
    }
  }

  function makeSpan(cls, text) {
    var s = document.createElement("span");
    s.className = cls;
    s.appendChild(document.createTextNode(text));
    return s;
  }

  function makeButton(id, text, title, handler) {
    var btn = document.createElement("button");
    btn.id = id;
    btn.type = "button";
    btn.className = "trace-btn";
    btn.setAttribute("title", title);
    btn.appendChild(document.createTextNode(text));
    btn.addEventListener("click", handler);
    return btn;
  }

  function setMsg(text, isOk) {
    var el = document.getElementById("trace-msg");
    if (!el) return;
    clearEl(el);
    el.appendChild(document.createTextNode(text));
    if (el.classList) {
      if (isOk) {
        el.classList.add("trace-msg-ok");
      } else {
        el.classList.remove("trace-msg-ok");
      }
    }
  }

  // -------------------------------------------------------------------------
  // Bundle indexing (READ-ONLY). EDITOR.allNodes() returns [{id, file, node}]
  // in bundle order; the tracer works off a local id -> entry map rebuilt on
  // every render. No bundle field is ever written.
  // -------------------------------------------------------------------------

  function nodeIndex() {
    var idx = {};
    var list = EDITOR.allNodes();
    for (var i = 0; i < list.length; i++) {
      idx[list[i].id] = list[i];
    }
    return idx;
  }

  function bundleFileOrder(b) {
    if (b && Object.prototype.toString.call(b.order) === "[object Array]" &&
        b.order.length) {
      return b.order;
    }
    return (b && b.files) ? Object.keys(b.files) : [];
  }

  // The default trace root: manifest.start (intro.preface in the live data).
  // Defensive fallback: the first node of the first file in bundle order —
  // the loader and the Python gates pin manifest.start valid, so this branch
  // only fires on hand-built or broken bundles.
  function defaultStartId(b, idx) {
    if (b && b.manifest && typeof b.manifest.start === "string" &&
        idx[b.manifest.start]) {
      return b.manifest.start;
    }
    var order = bundleFileOrder(b);
    for (var i = 0; i < order.length; i++) {
      var file = (b && b.files) ? b.files[order[i]] : null;
      var nodes = (file && file.nodes) ? file.nodes : null;
      if (!nodes) continue;
      for (var nid in nodes) {
        if (Object.prototype.hasOwnProperty.call(nodes, nid) && idx[nid]) {
          return nid;
        }
      }
    }
    return null;
  }

  // -------------------------------------------------------------------------
  // THE WALK — traceWalk: the goto-only DFS. Named + isolated so the
  // structural battery can pin its body (tests/test_story_editor_trace.py):
  // it reads choice.goto and NOTHING else about a choice. Shape mirror of
  // check_reachability (rpg/story/validate.py:167): start at the chosen
  // root, iterate each node's choices in choice order, follow goto edges to
  // EXISTING nodes only (a goto pointing at a missing node is not traversed
  // here — flagging dangling diverts is the validator's job, validate.py
  // :198-200), each node visited once (global visited set = the cycle
  // guard). The DISPLAY layer (annotationSpans) is where choice metadata
  // surfaces; the walk itself is structure-only.
  //
  // Returns the tree model:
  //   { id, file, node, choice, cycle, children: [model...] }
  // where `choice` is the INCOMING choice (null for the root) — kept for
  // the display layer; `cycle` marks a revisit (rendered as a leaf marker,
  // never recursed into); `children` preserves choice order.
  // -------------------------------------------------------------------------

  function traceWalk(startId, nodeIdx) {
    var visited = {}; // the cycle guard: every id rendered anywhere so far
    function step(id, incoming) {
      var entry = nodeIdx[id] || null;
      if (visited[id]) {
        // Revisit: emit the marker leaf and STOP — no recursion, so the
        // depth is bounded by the node count no matter what edges exist.
        return {
          id: id,
          file: entry ? entry.file : null,
          node: entry ? entry.node : null,
          choice: incoming,
          cycle: true,
          children: []
        };
      }
      visited[id] = true;
      var kids = [];
      var choices = (entry && entry.node &&
        Object.prototype.toString.call(entry.node.choices) ===
        "[object Array]") ? entry.node.choices : [];
      for (var i = 0; i < choices.length; i++) {
        var ch = choices[i];
        if (!ch || typeof ch !== "object") continue;
        var g = ch.goto;
        if (typeof g !== "string" || !g) continue;
        if (!nodeIdx[g]) continue; // dangling target: not traversed
        kids.push(step(g, ch));
      }
      return {
        id: id,
        file: entry ? entry.file : null,
        node: entry ? entry.node : null,
        choice: incoming,
        cycle: false,
        children: kids
      };
    }
    if (!nodeIdx[startId]) return null;
    return step(startId, null);
  }

  // -------------------------------------------------------------------------
  // DISPLAY layer — the ONLY place choice metadata (weight / cond / tags)
  // is consulted. Everything here is presentation: the structure above is
  // already fixed by traceWalk before any of this runs.
  // -------------------------------------------------------------------------

  function annotationSpans(c) {
    var out = [];
    if (!c || typeof c !== "object") return out;
    var tags = Object.prototype.toString.call(c.tags) === "[object Array]"
      ? c.tags : [];
    for (var i = 0; i < tags.length; i++) {
      if (tags[i] === "edit:offer") {
        out.push(makeSpan("trace-ann trace-offer", "wrench"));
        break; // one wrench chip is enough even if the tag repeats
      }
    }
    if (c.weight !== undefined && c.weight !== null) {
      out.push(makeSpan("trace-ann trace-weight",
        "\u2696 weight " + String(c.weight)));
    }
    if (typeof c.cond === "string" && c.cond !== "") {
      out.push(makeSpan("trace-ann trace-cond", "\u2317 cond " + c.cond));
    }
    return out;
  }

  // One node row: [incoming-choice label →] [annotations] [kind chip] [id].
  // The choice label that leads INTO this node reads as "Continue →
  // gly.g6p" (label, arrow, then this row's node id).
  function buildRow(tnode, kindText) {
    var row = document.createElement("span");
    row.className = "trace-row";
    var c = tnode.choice;
    if (c && typeof c === "object") {
      var label = (typeof c.label === "string" && c.label !== "")
        ? c.label : "(unlabeled)";
      row.appendChild(makeSpan("trace-edge", label + " \u2192 "));
      var anns = annotationSpans(c);
      for (var i = 0; i < anns.length; i++) {
        row.appendChild(anns[i]);
      }
    }
    row.appendChild(makeSpan("trace-chip k-" + kindText, kindText));
    row.appendChild(makeSpan("trace-id", tnode.id));
    return row;
  }

  // -------------------------------------------------------------------------
  // Tree rendering. Branches with children are <details>/<summary> (the
  // native toggle affordance); leaves and cycle markers are plain rows.
  // -------------------------------------------------------------------------

  function buildKidsUl(kids) {
    var ul = document.createElement("ul");
    ul.className = "trace-sub";
    for (var i = 0; i < kids.length; i++) {
      ul.appendChild(buildLi(kids[i]));
    }
    return ul;
  }

  function buildLi(tnode) {
    var li = document.createElement("li");
    if (tnode.cycle) {
      li.className = "trace-cycle-row";
      li.appendChild(makeSpan("trace-cycle",
        "\u21A9 already shown (" + tnode.id + ")"));
      return li;
    }
    var kind = tnode.node ? EDITOR.deriveKind(tnode.node) : "story";
    if (tnode.children && tnode.children.length) {
      var details = document.createElement("details");
      details.className = "trace-branch";
      details.setAttribute("data-branch", tnode.id);
      var summary = document.createElement("summary");
      summary.appendChild(buildRow(tnode, kind));
      details.appendChild(summary);
      details.appendChild(buildKidsUl(tnode.children));
      li.appendChild(details);
    } else {
      var row = buildRow(tnode, kind);
      row.className = "trace-row trace-leaf";
      li.appendChild(row);
    }
    return li;
  }

  // Expand/collapse state persistence: harvested from the live DOM before
  // each rebuild, re-applied after. Ids absent from the map default open.
  function harvestExpandState(container) {
    if (!container || !container.querySelectorAll) return;
    var ds = container.querySelectorAll("details[data-branch]");
    for (var i = 0; i < ds.length; i++) {
      expandedById[ds[i].getAttribute("data-branch")] = !!ds[i].open;
    }
  }

  function applyExpandState(container) {
    if (!container || !container.querySelectorAll) return;
    var ds = container.querySelectorAll("details[data-branch]");
    for (var i = 0; i < ds.length; i++) {
      ds[i].open = (expandedById[ds[i].getAttribute("data-branch")] !== false);
    }
  }

  function setAllBranches(open) {
    var tree = document.getElementById("trace-tree");
    if (!tree) return;
    var ds = tree.querySelectorAll("details[data-branch]");
    for (var i = 0; i < ds.length; i++) {
      ds[i].open = open;
      expandedById[ds[i].getAttribute("data-branch")] = open;
    }
    setMsg(open ? "all branches expanded" : "all branches collapsed", true);
  }

  // -------------------------------------------------------------------------
  // Copy-as-text: an indented plain-text rendering of the CURRENT trace
  // (2 spaces per level, "- [tier] node id — choice label"), consumed from
  // lastTraceText (rebuilt on every render — never scraped from the DOM).
  // Clipboard writes on file:// pages may be restricted, so the copy path
  // degrades gracefully: navigator.clipboard.writeText, then the legacy
  // execCommand("copy") on a scratch textarea, then leave that textarea
  // selected in the page for a manual Ctrl+C.
  // -------------------------------------------------------------------------

  function modelToLines(tnode, depth, lines) {
    var pad = "";
    for (var p = 0; p < depth; p++) {
      pad += "  "; // 2 spaces per level
    }
    if (tnode.cycle) {
      lines.push(pad + "- \u21A9 already shown (" + tnode.id + ")");
      return;
    }
    var kind = tnode.node ? EDITOR.deriveKind(tnode.node) : "story";
    var c = tnode.choice;
    var label = (c && typeof c === "object" &&
      typeof c.label === "string" && c.label !== "") ? c.label : null;
    var line = pad + "- [" + kind + "] " + tnode.id;
    if (label !== null) {
      line += " \u2014 " + label;
    }
    if (c && typeof c === "object") {
      if (c.weight !== undefined && c.weight !== null) {
        line += " (\u2696 weight " + String(c.weight) + ")";
      }
      if (typeof c.cond === "string" && c.cond !== "") {
        line += " (\u2317 cond " + c.cond + ")";
      }
    }
    lines.push(line);
    for (var i = 0; i < tnode.children.length; i++) {
      modelToLines(tnode.children[i], depth + 1, lines);
    }
  }

  function buildCopyText(root) {
    var lines = [];
    if (root) {
      modelToLines(root, 0, lines);
    }
    return lines.join("\n");
  }

  function legacyCopy(text) {
    var host = document.getElementById("trace-tree");
    if (!host) return;
    var ta = document.createElement("textarea");
    ta.className = "json-area trace-copy-ta";
    ta.setAttribute("readonly", "readonly");
    ta.setAttribute("aria-label", "Traced story as plain text");
    ta.value = text;
    host.appendChild(ta);
    ta.focus();
    ta.select();
    var ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (e) {
      ok = false;
    }
    if (ok) {
      setMsg("copied \u2713", true);
      host.removeChild(ta);
    } else {
      // Clipboard write denied: leave the textarea in place, still
      // selected, so the user can press Ctrl+C themselves.
      setMsg("clipboard blocked \u2014 the text is selected below; " +
             "press Ctrl+C to copy");
    }
  }

  function copyAsText() {
    if (!lastTraceText) {
      setMsg("nothing to copy \u2014 no data loaded yet");
      return;
    }
    if (typeof navigator !== "undefined" && navigator.clipboard &&
        typeof navigator.clipboard.writeText === "function") {
      try {
        var p = navigator.clipboard.writeText(lastTraceText);
        if (p && typeof p.then === "function") {
          p.then(function () {
            setMsg("copied \u2713", true);
          }, function () {
            legacyCopy(lastTraceText);
          });
        } else {
          setMsg("copied \u2713", true);
        }
        return;
      } catch (e) {
        // fall through to the legacy path
      }
    }
    legacyCopy(lastTraceText);
  }

  // -------------------------------------------------------------------------
  // Controls wiring.
  // -------------------------------------------------------------------------

  function traceFromSelection() {
    var b = EDITOR.state.bundle;
    if (!b || !b.files) {
      setMsg("no data loaded yet");
      return;
    }
    var sel = EDITOR.state.sel;
    if (!sel) {
      setMsg("no node selected \u2014 click a node in the Graph tab first");
      return;
    }
    var idx = nodeIndex();
    if (!idx[sel]) {
      setMsg("the selected node no longer exists: " + sel);
      return;
    }
    var selectEl = document.getElementById("trace-start");
    if (selectEl) {
      selectEl.value = sel;
    }
    setMsg("tracing from selection: " + sel, true);
    renderTrace();
  }

  function onStartChange() {
    var selectEl = document.getElementById("trace-start");
    if (selectEl && selectEl.value) {
      setMsg("tracing from " + selectEl.value, true);
    }
    renderTrace();
  }

  function buildUi(host) {
    clearEl(host);

    var controls = document.createElement("div");
    controls.id = "trace-controls";

    var lbl = document.createElement("label");
    lbl.className = "trace-start-label";
    lbl.setAttribute("for", "trace-start");
    lbl.appendChild(document.createTextNode("Start node:"));
    controls.appendChild(lbl);

    var selectEl = document.createElement("select");
    selectEl.id = "trace-start";
    selectEl.className = "json-area";
    selectEl.setAttribute("title",
      "The node the trace starts from \u2014 defaults to manifest.start " +
      "(intro.preface in the live data)");
    selectEl.addEventListener("change", onStartChange);
    controls.appendChild(selectEl);

    controls.appendChild(makeButton(
      "trace-from-sel", "Trace from selected graph node",
      "Start the trace at the node currently selected in the Graph tab",
      traceFromSelection));
    controls.appendChild(makeButton(
      "trace-copy", "Copy as text",
      "Copy the traced story as indented plain text",
      copyAsText));
    controls.appendChild(makeButton(
      "trace-collapse", "Collapse all",
      "Collapse every branch of the traced tree",
      function () { setAllBranches(false); }));
    controls.appendChild(makeButton(
      "trace-expand", "Expand all",
      "Expand every branch of the traced tree",
      function () { setAllBranches(true); }));

    var msg = document.createElement("span");
    msg.id = "trace-msg";
    controls.appendChild(msg);

    host.appendChild(controls);

    var tree = document.createElement("div");
    tree.id = "trace-tree";
    host.appendChild(tree);
  }

  // -------------------------------------------------------------------------
  // Start-node select population: every node id, grouped by source file via
  // <optgroup> (bundle order; node ids in insertion order within each file).
  // -------------------------------------------------------------------------

  function populateOptions(selectEl, b, idx) {
    clearEl(selectEl);
    var order = bundleFileOrder(b);
    for (var i = 0; i < order.length; i++) {
      var fname = order[i];
      var file = (b && b.files) ? b.files[fname] : null;
      var nodes = (file && file.nodes) ? file.nodes : null;
      if (!nodes) continue;
      var og = document.createElement("optgroup");
      og.setAttribute("label", fname);
      for (var nid in nodes) {
        if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
        if (!idx[nid]) continue;
        var opt = document.createElement("option");
        opt.setAttribute("value", nid);
        opt.appendChild(document.createTextNode(nid));
        og.appendChild(opt);
      }
      if (og.firstChild) {
        selectEl.appendChild(og);
      }
    }
  }

  function showPlaceholder(tree, text) {
    clearEl(tree);
    var p = document.createElement("div");
    p.className = "trace-placeholder";
    p.appendChild(document.createTextNode(text));
    tree.appendChild(p);
  }

  // -------------------------------------------------------------------------
  // The view renderer — registered via EDITOR.view("trace", renderTrace), so
  // the core dispatcher re-runs it on every afterChange (and select()):
  // in-progress edits reflect immediately. Idempotent: it builds the controls
  // once, then rebuilds only the tree.
  // -------------------------------------------------------------------------

  function renderTrace() {
    var host = document.getElementById("tab-trace");
    if (!host) return;
    if (!document.getElementById("trace-controls")) {
      buildUi(host);
    }
    var tree = document.getElementById("trace-tree");
    var selectEl = document.getElementById("trace-start");
    if (!tree || !selectEl) return;

    var b = EDITOR.state.bundle;
    if (!b || !b.files) {
      harvestExpandState(tree);
      lastTraceText = null;
      clearEl(selectEl);
      showPlaceholder(tree,
        "No story data loaded yet \u2014 load it from the boot panel above " +
        "(auto-detect or folder pick), then trace any path from any node " +
        "to view the full story as a nested list.");
      setMsg("");
      return;
    }

    var idx = nodeIndex();
    var prevVal = selectEl.value;
    populateOptions(selectEl, b, idx);
    var rootId = (prevVal && idx[prevVal]) ? prevVal : defaultStartId(b, idx);
    if (rootId) {
      selectEl.value = rootId;
    }
    if (!rootId) {
      harvestExpandState(tree);
      lastTraceText = null;
      showPlaceholder(tree, "The loaded bundle contains no nodes to trace.");
      return;
    }

    var model = traceWalk(rootId, idx);
    harvestExpandState(tree);
    if (!model) {
      lastTraceText = null;
      showPlaceholder(tree,
        "The start node could not be traced (it vanished from the bundle).");
      return;
    }
    clearEl(tree);
    var ul = document.createElement("ul");
    ul.className = "trace-tree";
    ul.appendChild(buildLi(model));
    tree.appendChild(ul);
    applyExpandState(tree);
    lastTraceText = buildCopyText(model);
  }

  // -------------------------------------------------------------------------
  // Registration (the 07.1-04 convention) + this asset's own CSS.
  // -------------------------------------------------------------------------

  EDITOR.view("trace", renderTrace);

  EDITOR.init(function () {
    renderTrace();
  });

  EDITOR.injectCss(
    "/* 60_trace.js (07.1-10): the path tracer */\n" +
    "#trace-controls { display: flex; flex-wrap: wrap; align-items: " +
    "center; gap: 8px; padding: 8px 14px; border-bottom: 1px solid " +
    "#e0e0e0; background: #f7f8fa; }\n" +
    "#trace-start { font-family: Consolas, monospace; font-size: 12.5px; " +
    "max-width: 320px; }\n" +
    ".trace-btn { padding: 4px 10px; font-size: 12.5px; cursor: pointer; }\n" +
    "#trace-msg { font-size: 12px; color: #555555; }\n" +
    "#trace-msg.trace-msg-ok { color: #1e7d32; }\n" +
    "#trace-tree { padding: 10px 16px 20px; overflow-x: auto; }\n" +
    ".trace-placeholder { color: #777777; font-style: italic; padding: 8px 0; }\n" +
    "ul.trace-tree, ul.trace-sub { list-style: none; margin: 0; " +
    "padding-left: 0; }\n" +
    "ul.trace-sub { padding-left: 26px; margin-left: 8px; border-left: " +
    "1px dotted #b8c2cf; }\n" +
    "ul.trace-tree > li, ul.trace-sub > li { margin: 2px 0; }\n" +
    ".trace-row { display: inline-flex; align-items: center; gap: 6px; " +
    "padding: 1px 2px; }\n" +
    "details.trace-branch > summary { cursor: pointer; }\n" +
    "details.trace-branch > summary:hover { background: #eef2f7; }\n" +
    ".trace-edge { color: #1f4e79; font-weight: bold; }\n" +
    ".trace-id { font-family: Consolas, monospace; font-size: 12.5px; }\n" +
    ".trace-ann { font-size: 11px; border-radius: 3px; padding: 0 4px; " +
    "border: 1px solid; white-space: nowrap; }\n" +
    ".trace-offer { color: #8a5a00; border-color: #d9a441; background: #fdf3dd; }\n" +
    ".trace-weight { color: #005959; border-color: #4b9b9b; background: #e2f3f3; }\n" +
    ".trace-cond { color: #5b3d8f; border-color: #a08cc0; background: #f0eafb; }\n" +
    ".trace-cycle { color: #8a6d3b; font-style: italic; }\n" +
    ".trace-cycle-row { color: #8a6d3b; }\n" +
    ".trace-chip { font-size: 10.5px; font-weight: bold; border-radius: 3px; " +
    "padding: 0 5px; color: #ffffff; letter-spacing: 0.02em; " +
    "white-space: nowrap; }\n" +
    ".k-ending-true { background: #c9a227; }\n" +
    ".k-ending-good { background: #2e8b57; }\n" +
    ".k-ending-normal { background: #4682b4; }\n" +
    ".k-ending-bad { background: #b22222; }\n" +
    ".k-phase8-stub { background: #777777; }\n" +
    ".k-edit-prompt { background: #b8860b; }\n" +
    ".k-restored { background: #6a3d9a; }\n" +
    ".k-rng { background: #008080; }\n" +
    ".k-edit-allowed { background: #6a5acd; }\n" +
    ".k-story { background: #708090; }\n" +
    "textarea.trace-copy-ta { min-height: 240px; margin-top: 8px; }\n"
  );

})();
