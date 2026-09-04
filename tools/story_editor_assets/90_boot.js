/* ==========================================================================
 * 90_boot.js — the editor's chrome: status bar + Diagnostics + Help
 * (plan 07.1-18, Wave 5).
 *
 * OWNERSHIP: this asset belongs to plan 07.1-18. It owns the always-visible
 * #statusbar, the #tab-diagnostics panel and the #tab-help panel. It sorts
 * LAST (90_ prefix), so the generator inlines it as the FINAL asset block —
 * every earlier asset's API already exists when this file evaluates. It
 * extends the window.EDITOR namespace from its own file only (never edit
 * another plan's asset; 00_core.js = 07.1-04 owns the core, 05_json.js the
 * serializer, 10_load.js the boot/load layer, 20_validate.js the validator).
 *
 * WHAT SHIPS HERE (the self-explaining chrome):
 *   1. STATUS BAR (rerender hook): loaded node/file counts, dirty-file
 *      count (click opens the Save tab), undo depth, the validator summary
 *      (click opens Diagnostics), the selected node id, and the B9 chip
 *      ("CG → Phase 12") whenever an ending node is selected. The bar is
 *      rebuilt on every rerender; the 05_json.js canary span
 *      (#statusbar-serializer) is captured before each rebuild and
 *      re-appended, so the serializer self-test line survives.
 *   2. DIAGNOSTICS TAB — the in-page verification surface (no DevTools
 *      needed): (a) the serializer self-test (EDITOR.selfTestSerializer,
 *      pass/fail table; auto-runs once on the first open of this tab);
 *      (b) the validator report (EDITOR.validateCurrent / the cached
 *      EDITOR._lastValidation: errors + notices with rule ids and src
 *      citations, plus the pinned-count shift report); (c) build info: the
 *      generator's inline asset-manifest head comment parsed at boot (asset
 *      list + byte sizes), the editor version, and the per-file FNV-1a data
 *      fingerprints for support/debug.
 *   3. HELP TAB — the human's operating manual (static content): what the
 *      tool is; the folder layout + why file:// fetch is blocked
 *      (CVE-2019-11730) + the folder-pick normal path + the draft-reload
 *      flow; the Firefox "Always ask you where to save files" one-time
 *      setting, the filename-is-a-suggestion caveat and the post-save
 *      Python gate commands; editing semantics (structural vs text halves,
 *      the derived-kind model, pinned-count acknowledgment, undo); the B11
 *      extensibility posture (unknown keys/ops round-trip, warn-but-accept);
 *      the B9 Phase-12 note; the offline statement.
 *
 * STYLE: one classic script, one IIFE, ES5 only (var, no arrow functions,
 * no let/const, no modules) — the page-wide emitted-JS discipline pinned by
 * tests/test_story_editor_state.py. Dynamic values rendered into HTML go
 * through EDITOR.esc; the Help tab is static authored prose (no data
 * interpolation), built once and left alone.
 * ========================================================================== */

(function () {
  "use strict";

  // Defensive: without the core asset there is nothing to chrome onto.
  if (typeof window === "undefined" || !window.EDITOR ||
      typeof window.EDITOR !== "object") {
    try {
      if (typeof console !== "undefined" && console && console.warn) {
        console.warn("90_boot: window.EDITOR missing — chrome disabled");
      }
    } catch (e) { /* nothing more we can do */ }
    return;
  }

  var EDITOR = window.EDITOR;

  // -------------------------------------------------------------------------
  // Module state + tiny DOM helpers.
  // -------------------------------------------------------------------------

  var diagOpened = false;       // "first open" flag for the auto self-test
  var diagSelfTest = null;      // cached serializer self-test result
  var diagSelfTestRan = false;
  var manifestEntries = null;   // [{name, bytes}] parsed once from the page
  var manifestTotal = 0;
  var helpBuilt = false;

  function esc(s) {
    return EDITOR.esc(s);
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  }

  function clearChildren(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function trunc(s, limit) {
    s = String(s == null ? "" : s);
    var n = (typeof limit === "number") ? limit : 400;
    if (s.length <= n) return s;
    return s.slice(0, n - 3) + "...";
  }

  // =========================================================================
  // 1. STATUS BAR — always visible; rebuilt on every rerender.
  // =========================================================================

  function nodeCount() {
    var b = EDITOR.state.bundle;
    if (!b || !b.files) return 0;
    return EDITOR.allNodes().length;
  }

  function fileCount() {
    var b = EDITOR.state.bundle;
    if (!b || !b.files) return 0;
    return Object.keys(b.files).length;
  }

  // Validator summary for the status field. Prefers the cached verdict the
  // 20_validate.js hook refreshes after every mutation; falls back to one
  // fresh validateCurrent() if no verdict exists yet. Never throws.
  function validationCounts() {
    var b = EDITOR.state.bundle;
    if (!b) return null;
    var v = EDITOR._lastValidation;
    if (!v && typeof EDITOR.validateCurrent === "function") {
      try { v = EDITOR.validateCurrent(); } catch (e) { v = null; }
    }
    if (!v) return null;
    return {
      errors: (v.errors && v.errors.length) ? v.errors.length : 0,
      notices: (v.notices && v.notices.length) ? v.notices.length : 0,
      blocked: !!v.blocked,
      result: v
    };
  }

  function selectedNode() {
    var sel = EDITOR.state.sel;
    if (!sel) return null;
    var n = EDITOR.nodeById(sel);
    return (n && typeof n === "object") ? n : null;
  }

  function renderStatusBar() {
    var bar = document.getElementById("statusbar");
    if (!bar) return;
    // 05_json.js (07.1-05) appends its boot-canary span to this same bar;
    // capture it BEFORE the rebuild and re-append after — the canary line
    // ("EDITOR: serializer self-test 11/11 pass") must survive every rerender.
    var serSpan = document.getElementById("statusbar-serializer");

    var b = EDITOR.state.bundle;
    var vc = validationCounts();
    var selNode = selectedNode();
    var tier = selNode ? EDITOR.endingTier(selNode) : null;

    var loadedTxt = b
      ? ("loaded: " + nodeCount() + " nodes / " + fileCount() + " files")
      : "loaded: not loaded";
    var dirtyN = EDITOR.dirtyFiles().length;
    var dirtyTxt = "dirty: " + dirtyN + (dirtyN === 1 ? " file" : " files");
    var undoTxt = "undo: " + EDITOR.undoDepth();
    var validateTxt = vc
      ? ("validate: " + vc.errors + " errors / " + vc.notices + " notices")
      : "validate: \u2014";
    var selTxt = "selected: " + (EDITOR.state.sel ? EDITOR.state.sel : "\u2014");

    var parts = [];
    parts.push('<span id="sb-loaded" title="loaded story bundle">' +
      esc(loadedTxt) + "</span>");
    parts.push('<span id="sb-dirty" class="sb-jump' +
      (dirtyN > 0 ? " editor-dirty" : "") +
      '" data-sb-jump="save" title="dirty files — click to open the Save tab">' +
      esc(dirtyTxt) + "</span>");
    parts.push('<span id="sb-undo" title="undo depth (redo ' +
      EDITOR.redoDepth() + ') — one step per logical action">' +
      esc(undoTxt) + "</span>");
    parts.push('<span id="sb-validate" class="sb-jump' +
      (vc && vc.errors > 0 ? " sb-validate-bad" : "") +
      '" data-sb-jump="diagnostics" title="validator summary — click to open the Diagnostics tab">' +
      esc(validateTxt) + "</span>");
    parts.push('<span id="sb-selected" title="selected node id">' +
      esc(selTxt) + "</span>");
    // B9 chip (roadmap insertion :285/:296): ending CG is Phase-12 territory;
    // the editor shows a REMINDER only. Shown whenever an ending is selected.
    if (tier) {
      parts.push('<span id="sb-b9" class="sb-b9-chip" data-sb-jump="help" ' +
        'title="B9 reminder: ending CG (cutscene graphics) is Phase-12 territory — this editor shows the reminder only. Click for the Help note.">' +
        esc("B9: CG → Phase 12") + "</span>");
    }
    bar.innerHTML = parts.join("");
    if (serSpan) bar.appendChild(serSpan);
  }

  function statusBarClick(target) {
    var dest = target.getAttribute("data-sb-jump");
    if (!dest) return;
    EDITOR.showTab(dest);
    if (dest === "diagnostics") onDiagnosticsOpened();
  }

  function initStatusBar() {
    var bar = document.getElementById("statusbar");
    if (!bar) return;
    EDITOR.delegate(bar, "click", "data-sb-jump", statusBarClick);
    EDITOR.hooks.rerender.push(renderStatusBar);
    renderStatusBar();
  }

  // =========================================================================
  // 2. DIAGNOSTICS TAB — serializer self-test + validator report + build
  //    info. The one-click health report (no DevTools needed).
  // =========================================================================

  // The generator bakes the inline manifest into a head comment of the
  // emitted page ("inlined assets (sorted): name (N bytes) | ...").
  // Parse it once at boot; fall back to scanning the page HTML.
  var MANIFEST_MARKER = "inlined assets";

  function parseAssetManifest() {
    if (manifestEntries) return manifestEntries;
    manifestEntries = [];
    manifestTotal = 0;
    var hay = "";
    try {
      var head = document.head ||
        document.getElementsByTagName("head")[0];
      if (head && head.childNodes) {
        for (var i = 0; i < head.childNodes.length; i++) {
          var n = head.childNodes[i];
          if (n.nodeType === 8 && n.nodeValue) {
            hay += n.nodeValue + "\n";
          }
        }
      }
      if (hay.indexOf(MANIFEST_MARKER) < 0 && document.documentElement &&
          document.documentElement.innerHTML) {
        hay += document.documentElement.innerHTML;
      }
    } catch (e) {
      hay = "";
    }
    var re = /([A-Za-z0-9_.\-]+\.js)\s*\((\d+)\s*bytes\)/g;
    var m = re.exec(hay);
    while (m !== null) {
      var size = parseInt(m[2], 10);
      manifestEntries.push({ name: m[1], bytes: size });
      manifestTotal += size;
      m = re.exec(hay);
    }
    return manifestEntries;
  }

  function generatedAtText() {
    var n = document.getElementById("generated-at");
    return n ? n.textContent : "";
  }

  function runSelfTestOnce() {
    diagSelfTestRan = true;
    try {
      diagSelfTest = EDITOR.selfTestSerializer();
    } catch (e) {
      diagSelfTest = {
        pass: false, passed: 0, total: 0, results: [],
        error: (e && e.message) ? e.message : String(e)
      };
    }
    return diagSelfTest;
  }

  // First open of the Diagnostics tab (tab click OR the status-bar jump):
  // the serializer self-test auto-runs ONCE; later visits reuse the cache
  // (the button re-runs on demand).
  function onDiagnosticsOpened() {
    if (diagOpened) return;
    diagOpened = true;
    runSelfTestOnce();
    renderDiagnostics();
  }

  function renderSelfTestSection(sec) {
    sec.appendChild(el("h3", null, "Serializer self-test"));
    sec.appendChild(el("p", "diag-muted",
      "Runs every embedded house-style serializer vector (EDITOR." +
      "selfTestSerializer) and compares against the canonical expected " +
      "strings shared with the Python fixture battery (07.1-02/05). " +
      "Green here means the save-path serializer is the verified port."));
    var row = el("div", "diag-btn-row");
    var btn = el("button", "diag-btn",
      diagSelfTestRan ? "Re-run self-test" : "Run self-test");
    btn.type = "button";
    btn.setAttribute("data-diag-action", "selftest");
    row.appendChild(btn);
    sec.appendChild(row);

    var out = el("div");
    out.id = "diag-selftest-result";
    if (!diagSelfTestRan) {
      out.appendChild(el("p", "diag-muted",
        "Not run yet — the self-test runs automatically the first time " +
        "this tab opens (it also runs at every page boot; see the " +
        "status-bar canary)."));
    } else if (diagSelfTest) {
      if (diagSelfTest.error) {
        out.appendChild(el("p", "diag-bad",
          "self-test ERROR: " + diagSelfTest.error));
      }
      out.appendChild(el("p", diagSelfTest.pass ? "diag-ok" : "diag-bad",
        "serializer self-test: " + (diagSelfTest.pass ? "PASS" : "FAIL") +
        " (" + diagSelfTest.passed + "/" + diagSelfTest.total +
        " vectors)"));
      var table = el("table", "diag-table");
      var thead = el("thead");
      var hrow = el("tr");
      hrow.appendChild(el("th", null, "vector"));
      hrow.appendChild(el("th", null, "result"));
      thead.appendChild(hrow);
      table.appendChild(thead);
      var tbody = el("tbody");
      var results = diagSelfTest.results || [];
      for (var i = 0; i < results.length; i++) {
        var r = results[i];
        var tr = el("tr");
        tr.appendChild(el("td", null, r.name));
        tr.appendChild(el("td", r.ok ? "diag-ok" : "diag-bad",
          r.ok ? "ok" : "FAIL"));
        tbody.appendChild(tr);
        if (!r.ok) {
          var tr2 = el("tr");
          var td = el("td");
          td.setAttribute("colspan", "2");
          var pre = el("pre", "diag-pre");
          pre.textContent = "want: " + trunc(r.expected) +
            "\ngot:  " + trunc(r.got);
          td.appendChild(pre);
          tr2.appendChild(td);
          tbody.appendChild(tr2);
        }
      }
      table.appendChild(tbody);
      out.appendChild(table);
    }
    sec.appendChild(out);
  }

  function tiersText(tiers) {
    if (!tiers || typeof tiers !== "object") return "{}";
    var parts = [];
    for (var k in tiers) {
      if (Object.prototype.hasOwnProperty.call(tiers, k)) {
        parts.push(k + ": " + tiers[k]);
      }
    }
    return "{" + parts.join(", ") + "}";
  }

  function renderCountShiftBox(out, cs) {
    if (!cs) return;
    var box;
    if (!cs.changed) {
      box = el("div", "diag-banner diag-banner-ok",
        "Pinned counts unchanged — nodes " + cs.nodes.old +
        ", endings by tier " + tiersText(cs.tiers.old) +
        ", edit-allowed " + cs.editAllowed.old.length + ".");
    } else {
      box = el("div", "diag-banner diag-banner-warn");
      box.appendChild(el("strong", null,
        "Pinned counts moved — this is the designed acknowledgment path, " +
        "not an error. Same-commit update obligations:"));
      var ul = el("ul");
      if (cs.nodes.old !== cs.nodes.new) {
        ul.appendChild(el("li", null,
          "nodes " + cs.nodes.old + " → " + cs.nodes.new));
      }
      if (cs.tiers.changed) {
        ul.appendChild(el("li", null,
          "endings by tier " + tiersText(cs.tiers.old) + " → " +
          tiersText(cs.tiers.new)));
      }
      if (cs.editAllowed.changed) {
        ul.appendChild(el("li", null,
          "edit-allowed " + cs.editAllowed.old.length + " → " +
          cs.editAllowed.new.length +
          ((cs.editAllowed.added && cs.editAllowed.added.length)
            ? " (added: " + cs.editAllowed.added.join(", ") + ")" : "") +
          ((cs.editAllowed.removed && cs.editAllowed.removed.length)
            ? " (removed: " + cs.editAllowed.removed.join(", ") + ")" : "")));
      }
      var tests = (cs.pinnedTests || []).join(", ");
      if (tests) ul.appendChild(el("li", null, "pinned tests: " + tests));
      var consts = (cs.viewerConstants || []).join(" / ");
      if (consts) {
        ul.appendChild(el("li", null,
          "viewer pinned constants: " + consts +
          " (tools/story_graph_viewer.py)"));
      }
      box.appendChild(ul);
    }
    out.appendChild(box);
  }

  function renderIssueList(out, title, items, emptyText) {
    out.appendChild(el("h4", null, title));
    if (!items || !items.length) {
      out.appendChild(el("p", "diag-muted", emptyText));
      return;
    }
    var ul = el("ul", "diag-issue-list");
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      var li = el("li");
      var head = it.kind + (it.node ? " — " + it.node : "") + ": " +
        it.detail;
      li.appendChild(document.createTextNode(head));
      if (it.src) {
        var srcSpan = el("span", "diag-src", "  [src: " + it.src + "]");
        li.appendChild(srcSpan);
      }
      ul.appendChild(li);
    }
    out.appendChild(ul);
  }

  function renderValidatorSection(sec) {
    sec.appendChild(el("h3", null, "Validator report"));
    sec.appendChild(el("p", "diag-muted",
      "Runs the full pre-save validator (EDITOR.validateCurrent — the " +
      "rule-for-rule port of tools/story_editor_lint.py) or shows the " +
      "verdict the validate hook refreshed after the last edit. Errors " +
      "block the save; notices never do (the sanctioned residual and the " +
      "count-shift acknowledgment path are notices by design)."));
    var row = el("div", "diag-btn-row");
    var btn = el("button", "diag-btn", "Run validator now");
    btn.type = "button";
    btn.setAttribute("data-diag-action", "validate");
    row.appendChild(btn);
    sec.appendChild(row);

    var out = el("div");
    out.id = "diag-validator-result";
    var v = EDITOR._lastValidation;
    if (!v) {
      out.appendChild(el("p", "diag-muted",
        "No verdict yet — load data (the validator re-runs after every " +
        "edit) or press the button above."));
    } else {
      var errors = v.errors || [];
      var notices = v.notices || [];
      out.appendChild(el("p", errors.length ? "diag-bad" : "diag-ok",
        errors.length + " errors / " + notices.length + " notices — " +
        (v.blocked ? "save BLOCKED while errors exist"
                   : "save allowed (drafts and save-edits)")));
      renderIssueList(out, "Errors (" + errors.length + ")", errors,
        "none — the graph is structurally clean.");
      renderIssueList(out, "Notices (" + notices.length + ")", notices,
        "none.");
      renderCountShiftBox(out, v.countShifts);
    }
    sec.appendChild(out);
  }

  function renderBuildSection(sec) {
    sec.appendChild(el("h3", null, "Build info"));
    var entries = parseAssetManifest();
    var head = el("p", null);
    head.appendChild(document.createTextNode("editor version: " +
      EDITOR.version));
    var gen = generatedAtText();
    if (gen) head.appendChild(document.createTextNode(" — " + gen));
    sec.appendChild(head);

    if (!entries.length) {
      sec.appendChild(el("p", "diag-warn",
        "Asset manifest not found in this page (the generator's inline " +
        "asset-manifest comment is missing — was this HTML emitted " +
        "by tools/story_editor.py?)"));
    } else {
      sec.appendChild(el("p", null, entries.length + " asset(s) inlined, " +
        manifestTotal + " bytes total:"));
      var table = el("table", "diag-table");
      var tbody = el("tbody");
      for (var i = 0; i < entries.length; i++) {
        var tr = el("tr");
        tr.appendChild(el("td", null, entries[i].name));
        tr.appendChild(el("td", null, entries[i].bytes + " bytes"));
        tbody.appendChild(tr);
      }
      table.appendChild(tbody);
      sec.appendChild(table);
    }

    // Per-file FNV-1a fingerprints (captured from the raw text at load
    // time): the support/debug identity of the loaded bundle — also the
    // stale-draft drift detector (07.1-13).
    sec.appendChild(el("h4", null,
      "Data fingerprints (FNV-1a, per loaded file)"));
    var fp = EDITOR.state.fingerprints || {};
    var names = [];
    for (var fname in fp) {
      if (Object.prototype.hasOwnProperty.call(fp, fname)) {
        names.push(fname);
      }
    }
    names.sort();
    if (!names.length) {
      sec.appendChild(el("p", "diag-muted",
        "No data loaded — fingerprints appear here after a folder pick " +
        "(or fetch) load; a downloaded draft carries them for the " +
        "stale-draft warning."));
    } else {
      var fpTable = el("table", "diag-table");
      var fpBody = el("tbody");
      for (var f = 0; f < names.length; f++) {
        var tr2 = el("tr");
        tr2.appendChild(el("td", null, names[f]));
        tr2.appendChild(el("td", null, String(fp[names[f]])));
        fpBody.appendChild(tr2);
      }
      fpTable.appendChild(fpBody);
      sec.appendChild(fpTable);
    }
  }

  function renderDiagnostics() {
    var panel = document.getElementById("tab-diagnostics");
    if (!panel) return;
    clearChildren(panel);

    var head = el("div", "diag-section diag-head");
    head.appendChild(el("h2", null, "Diagnostics"));
    head.appendChild(el("p", "diag-muted",
      "One-click health report — serializer self-test, the full pre-save " +
      "validator, and this page's build info. Everything runs locally in " +
      "this tab; no developer tools needed."));
    panel.appendChild(head);

    var s1 = el("div", "diag-section");
    renderSelfTestSection(s1);
    panel.appendChild(s1);

    var s2 = el("div", "diag-section");
    renderValidatorSection(s2);
    panel.appendChild(s2);

    var s3 = el("div", "diag-section");
    renderBuildSection(s3);
    panel.appendChild(s3);
  }

  function diagAction(target) {
    var action = target.getAttribute("data-diag-action");
    if (action === "selftest") {
      runSelfTestOnce();
      renderDiagnostics();
    } else if (action === "validate") {
      if (typeof EDITOR.validateCurrent === "function") {
        try { EDITOR.validateCurrent(); } catch (e) { /* keep old verdict */ }
      }
      renderDiagnostics();
    }
  }

  // =========================================================================
  // 3. HELP TAB — the human's operating manual (static, built once).
  // =========================================================================

  function helpSection(title, innerHtml) {
    var sec = el("div", "help-section");
    sec.appendChild(el("h2", null, title));
    var body = el("div");
    body.innerHTML = innerHtml; // static authored prose — no data interpolation
    sec.appendChild(body);
    return sec;
  }

  var HELP_WHAT = (
    "<p><strong>What this tool is.</strong> An authoring editor for the " +
    "RPG: Tale of C story data — the files under " +
    "<code>data/story_glucose/</code> (the manifest plus the story-node " +
    "files it lists) and the two game-data manifests " +
    "<code>rpg/data/edits.json</code> and <code>rpg/data/cast.json</code>. " +
    "It is a committed development tool living at the repository root, and " +
    "it is deliberately never bundled into the plugin zip (the build script " +
    "stages only <code>rpg/</code> and <code>data/story_glucose</code>), so " +
    "it can never ship inside the game. Teachers may use it to inspect or " +
    "propose story edits; it is NOT runtime game code — the game never " +
    "reads it and never needs it.</p>"
  );

  var HELP_LOADING = (
    "<p>The expected folder layout (the data directories must sit below " +
    "the folder that contains this HTML file):</p>" +
    "<pre>story_editor.html            &lt;- this file, at the repository root\n" +
    "data/story_glucose/*.json    manifest.json + the story files it lists\n" +
    "data/citations.json          approved-claims registry (read-only here)\n" +
    "data/sources.json            source provenance records (read-only here)\n" +
    "rpg/data/edits.json          known-edit buckets + bad_ending_pool\n" +
    "rpg/data/cast.json           the protein cast</pre>" +
    "<p><strong>Why the folder pick is the normal path.</strong> Your " +
    "browser blocks local file reads from a <code>file://</code> page on " +
    "purpose. Since Firefox 68 every local file is its own opaque origin " +
    "(CVE-2019-11730 / MFSA 2019-21 — same-directory Fetch access was the " +
    "vulnerability being closed), and the old escape-hatch preferences are " +
    "gone or unsupported. The editor therefore probes quietly first and " +
    "auto-loads only when an environment permits it (for example a locally " +
    "served folder); on the default <code>file://</code> open it asks you " +
    "to pick the repository folder once — that single click grants access " +
    "to exactly the files you selected, and nothing beyond them is ever " +
    "read.</p>" +
    "<p><strong>Draft reload.</strong> “Save draft” (Save tab) downloads " +
    "one self-contained <code>story_editor_draft.json</code> — the edited " +
    "bundle plus the dirty set, the undo depth and the per-file " +
    "fingerprints. “Load draft…” in the load panel restores it without a " +
    "folder re-pick. If the underlying files changed since the draft was " +
    "saved (a real save landed, or another agent edited the data), the " +
    "editor compares fingerprints and warns loudly before restoring — you " +
    "choose to load anyway, discard, or re-check.</p>"
  );

  var HELP_SAVING = (
    "<p><strong>Recommended one-time Firefox setting.</strong> Settings → " +
    "General → Files → check “Always ask you where to save files”. Then " +
    "every download button opens a save dialog where YOU pick the exact " +
    "name and location: the draft lands in <code>tmp/</code> as " +
    "<code>tmp/story_editor_draft.json</code> (the folder is git-ignored, " +
    "so the draft never touches git), and save-edit files overwrite their " +
    "displayed <code>data/</code> destinations in place. Without this " +
    "setting, browsers drop files into Downloads and may rename them.</p>" +
    "<p><strong>The filename is a suggestion, not a guarantee.</strong> " +
    "The <code>download</code> attribute only <em>suggests</em> a name — " +
    "browsers may adjust it (for example <code>tca(1).json</code> when " +
    "Downloads already holds a <code>tca.json</code>) and your settings " +
    "change the behavior entirely. That is why every save affordance " +
    "displays the exact expected filename and its repo-relative " +
    "destination — check what you actually saved before placing it.</p>" +
    "<p><strong>Save edit</strong> lists one row per dirty file — " +
    "<code>[Download tca.json] → save over data/story_glucose/tca.json</code> " +
    "— and refuses while the validator reports errors (drafts stay " +
    "available as the escape hatch). <strong>After placing the downloaded " +
    "files over their repo destinations, run the Python gates — the editor " +
    "cannot see the filesystem; the gates are the only authoritative " +
    "post-save check:</strong></p>" +
    "<ul class=\"help-cmd-list\">" +
    "<li>python3.6 tools/story_editor_lint.py</li>" +
    "<li>python3.6 -m unittest discover -s tests</li>" +
    "<li>python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json</li>" +
    "<li>python3.6 tools/check_edit_coverage.py</li>" +
    "<li>git diff  (review — only the intended lines may change)</li>" +
    "</ul>"
  );

  var HELP_EDITING = (
    "<p><strong>Two halves, different risk.</strong> Text edits — the " +
    "dramatic and teaching layers, choice labels — are the low-risk half: " +
    "they round-trip byte-stably and the gates check them for emptiness. " +
    "Structural edits — choices and their goto targets, on_enter scene " +
    "ops, tags, is_ending, the edits/cast manifests — change what the " +
    "engine executes and what the pinned test battery counts. The " +
    "validator re-runs after every edit, and the Save tab refuses while " +
    "any error exists.</p>" +
    "<p><strong>There is no node_type field.</strong> What a node “is” is " +
    "DERIVED: the ending tier comes from <code>is_ending</code>, " +
    "edit-allowed from the <code>edit:enzyme:</code> tag, the RNG node from " +
    "weighted choices, and so on. “Changing a node's type” is therefore a " +
    "recipe of underlying edits, never a dropdown: making a node " +
    "edit-allowed means adding the tag + an edits.json bucket (+ cast " +
    "entry + an edit:offer choice); making it an ending means setting " +
    "<code>is_ending</code> (plus reachability and the tier counts); " +
    "making it the RNG node means weighted choices inside " +
    "<code>tca.shuffle</code>. The lifecycle editor composes these recipes " +
    "for you.</p>" +
    "<p><strong>Pinned counts are a designed tripwire.</strong> The test " +
    "suite pins 57 nodes, 21 endings (1 true + 3 good + 2 normal + 15 " +
    "bad) and 15 edit-allowed nodes. An add/delete or type change that " +
    "moves them is not an editor error — it raises a visible " +
    "acknowledgment naming the exact pinned tests " +
    "(test_manifest_loads_all_57_nodes, test_reachability_green_all_four_tiers, " +
    "test_15_edit_allowed_nodes) and the viewer's pinned constants that " +
    "must be updated in the same commit.</p>" +
    "<p><strong>Undo.</strong> One undo step per logical action (a field " +
    "commit, a choice add, a paste). Typing commits on change (blur), " +
    "never per keystroke, so the undo pre-image stays the true pre-edit " +
    "value. Undo/redo re-derive the dirty map from the load-time " +
    "baseline. Undo history resets when you reload a draft — the draft " +
    "itself records the undo depth it was saved with, for reference.</p>"
  );

  var HELP_B11 = (
    "<p><strong>B11 — the editor preserves what it does not understand.</strong> " +
    "Unknown keys on nodes and choices, unknown tags, and unknown " +
    "on_enter ops all round-trip untouched through every edit, undo/redo " +
    "and save: the editor never rebuilds a node from a whitelist of known " +
    "fields, so data written by future phases — new node types, new op " +
    "shapes — survives editing here byte-stably and reaches the engine " +
    "exactly as authored. When you paste scene ops, an op the editor does " +
    "not know is accepted with a visible warn-but-accept chip — never " +
    "silently dropped, never rejected. Extending the editor itself (new " +
    "fields, new vocabulary) is a code change in a new asset, not a data " +
    "workaround: keep unknown things unknown; the engine owns their " +
    "meaning.</p>"
  );

  var HELP_B9 = (
    "<p><strong>B9 — ending CG is Phase-12 territory.</strong> The " +
    "editor's ending support stops at the reminder: when an ending node " +
    "is selected, the status bar shows the “CG → Phase 12” chip. Adding, " +
    "deleting or updating the CG (cutscene graphics) of endings belongs " +
    "to Phase 12 (Ending Cutscene Rendering) — nothing you do here " +
    "replaces that milestone, and this editor will not pretend " +
    "otherwise.</p>"
  );

  var HELP_OFFLINE = (
    "<p><strong>Offline by construction.</strong> Zero servers, zero " +
    "frameworks, zero network requests: this page is one self-contained " +
    "HTML file with inlined vanilla ES5 JavaScript and no dependencies. " +
    "Load it from disk, work from disk, save to disk — it behaves " +
    "identically with networking disabled.</p>"
  );

  function renderHelp() {
    if (helpBuilt) return;
    var panel = document.getElementById("tab-help");
    if (!panel) return;
    helpBuilt = true;
    clearChildren(panel);

    panel.appendChild(helpSection("What this tool is", HELP_WHAT));
    panel.appendChild(helpSection("Loading the data", HELP_LOADING));
    panel.appendChild(helpSection("Saving your work", HELP_SAVING));
    panel.appendChild(helpSection("Editing semantics", HELP_EDITING));
    panel.appendChild(helpSection(
      "B11 — extensibility posture", HELP_B11));
    panel.appendChild(helpSection(
      "B9 — ending CG (a reminder, not a feature)", HELP_B9));
    panel.appendChild(helpSection("Offline statement", HELP_OFFLINE));
  }

  // =========================================================================
  // Registration + per-asset CSS.
  // =========================================================================

  EDITOR.injectCss(
    "/* 90_boot.js (07.1-18): status-bar chrome + diagnostics + help */\n" +
    "#statusbar .sb-jump { cursor: pointer; text-decoration: underline; " +
    "text-decoration-style: dotted; }\n" +
    "#statusbar .sb-jump:hover { color: #111111; }\n" +
    "#statusbar .sb-validate-bad { color: #b5442d; font-weight: bold; }\n" +
    "#statusbar .sb-b9-chip { background: #fff3cd; border: 1px solid " +
    "#b8860b; color: #7a5a00; border-radius: 9px; padding: 0 8px; " +
    "cursor: pointer; font-weight: bold; }\n" +
    ".diag-section { border: 1px solid #dde3ec; border-radius: 6px; " +
    "padding: 10px 12px; margin: 10px 14px; background: #ffffff; }\n" +
    ".diag-section h2 { margin: 0 0 4px; font-size: 17px; }\n" +
    ".diag-section h3 { margin: 0 0 6px; font-size: 13px; " +
    "text-transform: uppercase; letter-spacing: 0.06em; color: #555555; }\n" +
    ".diag-section h4 { margin: 10px 0 4px; font-size: 12.5px; " +
    "color: #444444; }\n" +
    ".diag-muted { color: #666666; font-size: 12.5px; margin: 4px 0; }\n" +
    ".diag-btn { padding: 4px 12px; font-size: 12.5px; border: 1px solid " +
    "#9aa3b2; border-radius: 4px; background: #e8ecf3; cursor: pointer; }\n" +
    ".diag-btn-row { margin: 6px 0; }\n" +
    ".diag-table { border-collapse: collapse; font-family: Consolas, " +
    "monospace; font-size: 12px; margin: 6px 0; width: 100%; }\n" +
    ".diag-table th, .diag-table td { border: 1px solid #dde3ec; " +
    "padding: 3px 8px; text-align: left; vertical-align: top; }\n" +
    ".diag-ok { color: #1e5c1e; }\n" +
    ".diag-bad { color: #b5442d; font-weight: bold; }\n" +
    ".diag-issue-list { font-size: 12.5px; margin: 4px 0; " +
    "padding-left: 20px; }\n" +
    ".diag-issue-list li { margin: 3px 0; }\n" +
    ".diag-src { color: #777777; font-family: Consolas, monospace; " +
    "font-size: 11px; }\n" +
    ".diag-pre { font-family: Consolas, monospace; font-size: 11.5px; " +
    "background: #f4f6f9; border: 1px solid #dde3ec; border-radius: 4px; " +
    "padding: 5px 7px; margin: 4px 0; overflow-x: auto; " +
    "white-space: pre-wrap; }\n" +
    ".diag-banner { border-radius: 4px; padding: 6px 9px; margin: 6px 0; " +
    "font-size: 12.5px; }\n" +
    ".diag-banner-ok { background: #e7f4e7; border: 1px solid #3d8b3d; }\n" +
    ".diag-banner-warn { background: #fdf3df; border: 1px solid #b8860b; " +
    "color: #4a3a10; }\n" +
    ".diag-banner ul { margin: 4px 0 2px; padding-left: 20px; }\n" +
    "#tab-help { max-width: 1000px; }\n" +
    ".help-section { padding: 12px 16px 4px; }\n" +
    ".help-section h2 { font-size: 16px; margin: 0 0 8px; " +
    "border-bottom: 1px solid #e0e0e0; padding-bottom: 4px; }\n" +
    ".help-section p, .help-section li { font-size: 13.5px; margin: 6px 0; }\n" +
    ".help-section ul { padding-left: 24px; }\n" +
    ".help-section code, .diag-section code { font-family: Consolas, " +
    "monospace; font-size: 12px; background: #f4f6f9; border: 1px solid " +
    "#dde3ec; border-radius: 3px; padding: 0 4px; }\n" +
    ".help-section pre { font-family: Consolas, monospace; font-size: " +
    "12px; background: #f4f6f9; border: 1px solid #dde3ec; " +
    "border-radius: 4px; padding: 8px 10px; overflow-x: auto; }\n" +
    ".help-cmd-list { font-family: Consolas, monospace; font-size: " +
    "12.5px; }\n"
  );

  // Views: both panels re-render through the core dispatcher (renderHelp is
  // idempotent — built once); the diagnostics panel stays fresh with the
  // latest validation verdict + fingerprints after every mutation.
  EDITOR.view("diagnostics", renderDiagnostics);
  EDITOR.view("help", renderHelp);

  EDITOR.init(function () {
    initStatusBar();

    var panel = document.getElementById("tab-diagnostics");
    if (panel) {
      EDITOR.delegate(panel, "click", "data-diag-action", diagAction);
    }

    // First-open detection for the auto self-test: the core wires the tab
    // bar's showTab; THIS listener additionally notices the Diagnostics
    // click (both listeners receive the event — they compose).
    var tabbar = document.getElementById("tabbar");
    if (tabbar) {
      EDITOR.delegate(tabbar, "click", "data-tab", function (target) {
        if (target.getAttribute("data-tab") === "diagnostics") {
          onDiagnosticsOpened();
        }
      });
    }
  });

})();
