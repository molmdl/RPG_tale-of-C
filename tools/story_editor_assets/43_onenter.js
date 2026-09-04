/* ==========================================================================
 * 43_onenter.js — the on_enter (scene) editor: MolAction list + paste-in
 * (07.1-16, Requirement B8).
 *
 * OWNS: the #node-form-onenter sub-section of the shell's #node-form aside
 * (FIXED mount point from 07.1-01's shell.html; this asset NEVER edits
 * another asset's file — the identity/choices/lifecycle sub-sections belong
 * to 40_form.js / 42_choices.js / 45_lifecycle.js). Loads after 00_core.js
 * (EDITOR contract), 05_json.js, 10_load.js, 20_validate.js, 30_graph.js and
 * 40_form.js; registers via EDITOR.view("onenter", renderOnenter) +
 * EDITOR.init(initOnenter) per the 07.1-04 registration convention.
 *
 * REQUIREMENT B8 (roadmap; spec intent "ask the user to copy something, keep
 * it simple, no PyMOL call"): the editor user captures a real PyMOL
 * session's camera/color/representation state with the committed
 * tools/scene_capture.py (07-19), copies its paste-ready jsonc output, and
 * pastes it here. The paste format is FROZEN by scene_capture.py:416-434
 * (render_capture):
 *   1. `//`-header comment lines,
 *   2. ONE JSON array of MolAction dicts ({op, target, args}),
 *   3. `# NOT CAPTURED: ...` note lines (session facts capture could not
 *      map — nothing silently dropped, no invented ops).
 * parseScenePaste() implements that contract exactly (RESEARCH-UI "Paste-in
 * parse", Code Example 5): split lines, drop empty/`//`/`#` lines, take
 * first `[` .. last `]`, JSON.parse, then PER-ENTRY validation: object with
 * a string `op` required; op in the KNOWN vocabulary -> ok; op UNKNOWN ->
 * warn-but-accept (B11 extensibility: "unknown op 'X' (kept)" — never
 * silently dropped, never rejected); `set_view` -> accepted + the VISIBLE
 * Phase-10 flag (scene_capture stdout-WARNING parity; the set_view dispatch
 * lands in Phase 10 — molops.py is FROZEN in Phase 7). Parsed ops render as
 * a PREVIEW list (summarized) before a confirm attaches them via apply()
 * (append AFTER the existing ops — never reorder existing ops of pinned
 * nodes).
 *
 * OP VOCABULARY (RESEARCH-DATA §1.4, the verified arg-shape table + the
 * molops.py:140-291 dispatch): the 10 story-data ops (hide_all, load,
 * show_as, edit, align, set_color, color, show, set, label) + the
 * molops-supported extras (select_focus, zoom, delete, protonate, restore) +
 * set_view (Phase-10-flagged). Every per-op field form below mirrors the
 * §1.4 arg shapes; molops dispatches an unknown op with NotImplementedError
 * (molops.py:286-291), which is why the paste parser warns-but-accepts
 * instead of rejecting (the on-disk validator + the engine own the errors).
 *
 * HUMAN SUMMARIES: summarizeAction() ports the committed viewer's
 * summarize_on_enter mapping rule-for-rule — source: git show
 * HEAD:tools/story_graph_viewer.py:254-312 (incl. the unknown-op fallback
 * "op <name> <compact args JSON>" and the absolute never-crash fallback).
 * The 6 molops-extra ops get editor-side summaries (the viewer mapping
 * predates them and falls through to the generic fallback for them —
 * documented extension, same fallback shape).
 *
 * NO-INVENTION NOTE: `load` and `hide_all` are REPLAY-SIDE ops — the
 * engine's on_enter brings objects in / wipes the scene; scene_capture
 * NEVER emits them (scene_capture.py:21-24). The paste parser ACCEPTS them
 * if hand-written but the preview notes their replay-side semantics.
 *
 * PINNED-SEQUENCE GUARDS (all warns are CONFIRMS, not blocks — the
 * validator (20_validate.js) + the Python gates carry the authoritative
 * errors):
 *   - start nodes (intro.preface / intro.shell_glucose / intro.select):
 *     appending/attaching a `load` with a `pdb:` target hard-warns
 *     (start-shape tests, tests/test_glucose_reachability.py:781-798 —
 *     start nodes use bundled placeholders only); modifying any op of
 *     intro.preface's hero-highlight 6-op ordered subsequence (set_color
 *     hero_cyan -> show_as sticks -> color hero_cyan -> show spheres ->
 *     set sphere_scale -> label YOU, after the hero_atom load) hard-warns
 *     (tests/test_glucose_reachability.py:800-843).
 *   - restored nodes (gly.pfk_restored / tca.aconitase_restored):
 *     modifying/reordering the pinned [edit, load, align, show_as] reveal
 *     warns (restoration pin, tests/test_glucose_reachability.py:391-414).
 *   - `edit` / `restore` / `protonate` ops on NON-restored nodes warn
 *     (the zero-restore-ops invariant verified by 07-17: only the 2
 *     restored nodes carry restore-form ops).
 *
 * MUTATION DISCIPLINE: every change flows through the 00_core mutators
 * (EDITOR.nodeSet on the "on_enter" field — one apply = one undo step +
 * per-file dirty). Each on_enter mutation copies the op ARRAY and copies
 * the touched op dict + its args dict before writing, so the ORIGINAL
 * nested objects are never mutated in place (the undo snapshot is taken
 * inside apply(); in-place edits would corrupt the pre-image). Unknown op
 * KEYS round-trip untouched (op dicts may carry extra keys — never
 * stripped; B11, the same contract the 00_core mutators pin). Absent-vs-
 * empty convention: clearing an optional field/target REMOVES the key
 * (the house data omits absent keys — e.g. hide_all/set_color carry no
 * target key at all), never writes "" or null.
 *
 * STYLE: one classic script, one IIFE, ES5 only (var, no arrow functions,
 * no let/const, no modules) — the emitted-page discipline pinned by
 * tests/test_story_editor_state.py.
 * ========================================================================== */

(function () {
  "use strict";

  // -------------------------------------------------------------------------
  // Constants.
  // -------------------------------------------------------------------------

  // The Phase-10 flag text (visible badge + parse warning; scene_capture
  // prints a stdout WARNING for the same fact — molops.py is FROZEN in
  // Phase 7 and the set_view dispatch lands in Phase 10).
  var PHASE10_FLAG_TEXT =
    "Phase-10 flag: camera rides home until the set_view dispatch lands";

  // The op vocabulary: the 10 story-data ops (RESEARCH-DATA §1.4 verified
  // arg shapes) + the molops-supported extras (molops.py:65-115, 240-291)
  // + the Phase-10-flagged set_view. Field entries: key, optional flag,
  // csv (array-of-N-numbers fields rendered as one comma-separated input),
  // def (skeleton default drawn from the §1.4 verified examples), ph
  // (placeholder). Op names written as plain double-quoted strings so the
  // structural battery can grep the literal vocabulary.
  var OP_VOCAB = [
    { op: "hide_all", target: false, fields: [] },
    { op: "load", target: true, fields: [
      { key: "object", ph: "object name, e.g. hero_atom" }
    ] },
    { op: "show_as", target: true, fields: [
      { key: "rep", def: "sticks", ph: "sticks | cartoon | spheres" },
      { key: "sele", optional: true, ph: "optional selection" }
    ] },
    { op: "edit", target: true, fields: [
      { key: "edit_type", def: "point_mutation",
        select: ["point_mutation", "substrate_remove_group",
                 "substrate_add_group", "protonation_change"] },
      { key: "sele", ph: "e.g. resi 209 and chain A" },
      { key: "new_resn", ph: "e.g. GLY" }
    ] },
    { op: "align", target: true, fields: [
      { key: "reference", ph: "the FIXED (edited) object" },
      { key: "method", def: "super", select: ["super", "align", "cealign"] },
      { key: "align_sele", def: "name CA", ph: "e.g. name CA" }
    ] },
    { op: "set_color", target: false, fields: [
      { key: "name", ph: "e.g. hero_cyan" },
      { key: "rgb", csv: 3, ph: "3 floats, e.g. 0.0, 0.75, 0.75" }
    ] },
    { op: "color", target: true, fields: [
      { key: "color", ph: "color name or captured_<idx>" },
      { key: "sele", optional: true, ph: "optional selection" }
    ] },
    { op: "show", target: true, fields: [
      { key: "rep", ph: "rep turned ON, e.g. spheres" },
      { key: "sele", optional: true, ph: "optional selection" }
    ] },
    { op: "set", target: true, fields: [
      { key: "name", ph: "setting name, e.g. sphere_scale" },
      { key: "value", ph: "e.g. 0.3" },
      { key: "sele", optional: true, ph: "optional selection" }
    ] },
    { op: "label", target: true, fields: [
      { key: "sele", optional: true, ph: "optional selection" },
      { key: "text", ph: "label text (molops quotes it, e.g. YOU)" }
    ] },
    { op: "select_focus", target: false, fields: [
      { key: "name", optional: true, def: "focus", ph: "selection name" },
      { key: "sele", ph: "defining selection expression" }
    ] },
    { op: "zoom", target: false, fields: [
      { key: "sele", optional: true, ph: "optional selection (default all)" }
    ] },
    { op: "set_view", target: false, fields: [
      { key: "view", csv: 18,
        ph: "18 comma-separated floats (cmd.get_view)" }
    ] },
    { op: "delete", target: true, fields: [] },
    { op: "protonate", target: true, fields: [
      { key: "variant_id", ph: "protonation variant id" }
    ] },
    { op: "restore", target: true, fields: [] }
  ];

  var OP_NAMES = (function () {
    var out = [];
    for (var i = 0; i < OP_VOCAB.length; i++) out.push(OP_VOCAB[i].op);
    return out;
  })();

  // Pinned-node ids (mirrors of the 00_core/committed-viewer constants).
  var START_NODE_IDS = {
    "intro.preface": true,
    "intro.shell_glucose": true,
    "intro.select": true
  };
  var RESTORED_IDS = {
    "gly.pfk_restored": true,
    "tca.aconitase_restored": true
  };

  // -------------------------------------------------------------------------
  // Module state.
  // -------------------------------------------------------------------------

  var refs = { section: null };
  // Paste state survives unrelated re-renders (the user may paste the
  // scene_capture blob, edit something else, and come back): the textarea
  // text is harvested before every rebuild; the parsed preview re-renders
  // from pasteState.parsed.
  var pasteState = { text: "", parsed: null, error: "" };
  // Transient inline note (declared mutations / parse hints); lives until
  // the next successful mutation re-render.
  var transientNote = "";

  // -------------------------------------------------------------------------
  // Small helpers.
  // -------------------------------------------------------------------------

  function esc(s) {
    return EDITOR.esc(s);
  }

  function warn(msg) {
    try {
      if (typeof console !== "undefined" && console && console.warn) {
        console.warn(msg);
      }
    } catch (e) { /* never warn about failing to warn */ }
  }

  function selectedNode() {
    var nid = EDITOR.state.sel;
    if (!nid || !EDITOR.state.bundle) return null;
    return EDITOR.nodeById(nid);
  }

  function selectedFile() {
    var nid = EDITOR.state.sel;
    return nid ? EDITOR.fileOfNode(nid) : null;
  }

  function asOpList(node) {
    return (node && Object.prototype.toString.call(node.on_enter) ===
            "[object Array]") ? node.on_enter : [];
  }

  function vocabEntry(opName) {
    for (var i = 0; i < OP_VOCAB.length; i++) {
      if (OP_VOCAB[i].op === opName) return OP_VOCAB[i];
    }
    return null;
  }

  // Keep JSON round-trip types stable (same semantics as the core's
  // coerceLike): if the arg already held a number and the committed text
  // parses as a finite number, commit a number; else commit the string.
  function coerceLike(oldValue, text) {
    if (typeof oldValue === "number" && String(text).trim() !== "") {
      var n = Number(text);
      if (isFinite(n)) return n;
    }
    return text;
  }

  // "a, b, c" -> [na, nb, nc] (all finite numbers) or null on failure.
  function parseCsvNumbers(text, n) {
    var parts = String(text == null ? "" : text).split(",");
    if (parts.length !== n) return null;
    var out = [];
    for (var i = 0; i < parts.length; i++) {
      var v = parseFloat(parts[i].trim());
      if (!isFinite(v)) return null;
      out.push(v);
    }
    return out;
  }

  // Compact args JSON with SORTED keys — the unknown-op fallback format of
  // the viewer's summarize_on_enter (json.dumps(args, sort_keys=True)).
  function sortedKeysJson(obj) {
    try {
      var keys = Object.keys(obj || {}).sort();
      var parts = [];
      for (var i = 0; i < keys.length; i++) {
        parts.push(JSON.stringify(keys[i]) + ": " +
                   JSON.stringify(obj[keys[i]]));
      }
      return "{" + parts.join(", ") + "}";
    } catch (e2) {
      return "{}";
    }
  }

  // -------------------------------------------------------------------------
  // summarizeAction — the human summary of one MolAction. Port of the
  // committed viewer's summarize_on_enter mapping (git show
  // HEAD:tools/story_graph_viewer.py:254-312): the 10 data ops rule-for-rule
  // (incl. the unknown-op fallback "op <name> <compact args JSON>" and the
  // absolute never-crash fallback); the 6 molops-extra ops are an editor-side
  // extension (the viewer mapping falls through to the generic fallback for
  // them — same fallback shape, documented in the header).
  // -------------------------------------------------------------------------

  function summarizeAction(action) {
    try {
      var op = (action && action.op) ? String(action.op) : "?";
      var target = action ? action.target : null;
      var args = (action && action.args && typeof action.args === "object")
        ? action.args : {};
      if (op === "hide_all") return "hide all objects";
      if (op === "load") {
        var t = String(target || "");
        if (t.indexOf("pdb:") === 0) t = t.slice(4);
        else if (t.indexOf("cid:") === 0) t = t.slice(4);
        return "load '" + t + "' as object '" +
          (args.object != null ? args.object : "?") + "'";
      }
      if (op === "set_color") {
        var rgb = args.rgb || [];
        var parts = [];
        for (var i = 0; i < rgb.length && i < 3; i++) {
          var f = parseFloat(rgb[i]);
          parts.push(String(Math.round((isFinite(f) ? f : 0) * 255)));
        }
        return "define color '" + (args.name != null ? args.name : "?") +
          "' = rgb(" + parts.join(", ") + ")";
      }
      if (op === "show_as" || op === "show") {
        var rep = (args.rep != null) ? args.rep
          : ((args.value != null) ? args.value : "?");
        var suffix = args.sele
          ? (" [sele: " + args.sele + "]")
          : (target ? (" [" + target + "]") : "");
        return (op === "show_as" ? "show as '" : "show '") + rep + "'" +
          suffix;
      }
      if (op === "color") {
        var cname = (args.name != null) ? args.name
          : ((args.color != null) ? args.color
            : ((args.value != null) ? args.value : "?"));
        return "color '" + target + "' = '" + cname + "'";
      }
      if (op === "set") {
        return "set '" + (args.name != null ? args.name : "?") +
          "' = '" + (args.value != null ? args.value : "?") + "'";
      }
      if (op === "label") {
        return "label '" + target + "' = '" +
          (args.text != null ? args.text : "") + "'";
      }
      if (op === "edit") {
        var newRes = (args.new_res != null) ? args.new_res
          : ((args.new_resn != null) ? args.new_resn : "?");
        var txt = "mutate '" + target + "' -> '" + newRes + "'";
        if (args.edit_type) {
          txt += " (" + args.edit_type;
          if (args.sele) txt += ": " + args.sele;
          txt += ")";
        }
        return txt;
      }
      if (op === "align") {
        var mobile = (args.mobile != null) ? args.mobile : target;
        return "align '" + mobile + "' -> '" + args.reference +
          "' (method '" + args.method + "', sele '" + args.align_sele + "')";
      }
      // --- editor-side extension (molops-supported extras; the viewer's
      // mapping falls through to the generic fallback for these) ---------
      if (op === "select_focus") {
        return "select '" + (args.name != null ? args.name : "focus") +
          "' = '" + (args.sele != null ? args.sele : "?") + "'";
      }
      if (op === "zoom") {
        return "zoom '" + (args.sele != null ? args.sele
          : (target || "all")) + "'";
      }
      if (op === "delete") return "delete object '" + target + "'";
      if (op === "protonate") {
        return "protonate '" + target + "' -> variant '" +
          (args.variant_id != null ? args.variant_id : "?") + "'";
      }
      if (op === "restore") {
        return "restore '" + target + "' (the pre-edit backup safety net)";
      }
      if (op === "set_view") {
        return "set camera view (18 floats) [Phase-10-flagged]";
      }
      // --- unknown-op fallback (viewer-faithful) --------------------------
      return "op " + op + " " + sortedKeysJson(args);
    } catch (e) { // absolute fallback -- summarizing must not crash
      return "op " + ((action && action.op) || "?") +
        " (unsummarizable: " + e + ")";
    }
  }

  // -------------------------------------------------------------------------
  // parseScenePaste — the B8 paste contract (scene_capture.py:416-434,
  // render_capture format; RESEARCH-UI Code Example 5). Returns
  // { ops, warnings, noteLines } or throws Error. The single intentional
  // delta vs Code Example 5: warnings are COLLECTED (returned) instead of
  // only console.warn'd, so the preview can render them; KNOWN is the plan's
  // 16-op molops vocabulary — a SUPERSET of Code Example 5's viewer-observed
  // 13 (the molops extras delete/protonate/restore are dispatched ops, so
  // they are KNOWN here and policed by the zero-restore-ops pinned guard
  // instead of the unknown-op path).
  // -------------------------------------------------------------------------

  function parseScenePaste(text) {
    var lines = String(text == null ? "" : text).split(/\r?\n/);
    var kept = [];
    var warnings = [];
    var noteLines = 0;
    for (var i = 0; i < lines.length; i++) {
      var s = lines[i].trim();
      if (s === "") continue;              // blank lines dropped
      if (s.indexOf("//") === 0) continue; // jsonc `//` header comments
      // "# NOT CAPTURED: ..." note lines (scene_capture's unmappable-fact
      // annotations) are dropped from the parse but COUNTED, so the preview
      // can tell the user which session facts the capture could not map.
      if (s.indexOf("#") === 0) { noteLines++; continue; }
      kept.push(lines[i]);
    }
    var body = kept.join("\n");
    var a = body.indexOf("[");
    var b = body.lastIndexOf("]");
    if (a < 0 || b < 0) throw new Error("no JSON array found in paste");
    var ops = JSON.parse(body.slice(a, b + 1));
    if (Object.prototype.toString.call(ops) !== "[object Array]") {
      throw new Error("the paste's [...] region did not parse into a JSON array");
    }
    for (var j = 0; j < ops.length; j++) {
      var op = ops[j];
      // Per-entry validation: object with a string op required.
      if (!op || typeof op.op !== "string") {
        throw new Error("entry " + j + ": missing op");
      }
      // Warn-but-accept (B11 extensibility): unknown ops are KEPT — never
      // silently dropped, never rejected (the validator/dispatch own the
      // authoritative errors).
      if (OP_NAMES.indexOf(op.op) < 0) {
        warnings.push("entry " + j + ": unknown op '" + op.op + "' (kept)");
      }
      if (op.op === "set_view") {
        warnings.push("entry " + j + ": " + PHASE10_FLAG_TEXT);
      }
      // No-invention note: load/hide_all never appear in scene_capture
      // OUTPUT (replay-side) — accepted if hand-written, semantics noted.
      if (op.op === "load" || op.op === "hide_all") {
        warnings.push("entry " + j + ": '" + op.op +
          "' is a replay-side op -- scene_capture NEVER emits it (hand-" +
          "written entry); the engine's on_enter " +
          (op.op === "load" ? "brings objects in" : "wipes the scene"));
      }
    }
    return { ops: ops, warnings: warnings, noteLines: noteLines };
  }

  // -------------------------------------------------------------------------
  // Pinned-sequence guards. Every guard returns a message string list; the
  // caller turns them into ONE window.confirm (warns are confirms, not
  // blocks — the validator carries the authoritative errors).
  // -------------------------------------------------------------------------

  // The hero-highlight ordered subsequence of intro.preface's on_enter:
  // the hero_atom load first, then the 6 highlight ops IN ORDER (ordered-
  // subsequence walk mirroring tests/test_glucose_reachability.py:800-843).
  // Returns the guarded indices, or [] when the sequence is not intact.
  function heroHighlightIndices(onEnter) {
    var out = [];
    if (!onEnter) return out;
    var heroLoad = -1;
    for (var i = 0; i < onEnter.length; i++) {
      var m = onEnter[i];
      if (m && m.op === "load" && m.args && m.args.object === "hero_atom") {
        heroLoad = i;
        break;
      }
    }
    if (heroLoad < 0) return out;
    out.push(heroLoad); // the load precedes (and carries) the highlight
    var seq = [
      ["set_color", function (a) { return a.args && a.args.name === "hero_cyan"; }],
      ["show_as", function (a) { return a.args && a.args.rep === "sticks"; }],
      ["color", function (a) { return a.args && a.args.color === "hero_cyan"; }],
      ["show", function (a) { return a.args && a.args.rep === "spheres"; }],
      ["set", function (a) { return a.args && a.args.name === "sphere_scale"; }],
      ["label", function (a) { return a.args && a.args.text === "YOU"; }]
    ];
    var idx = heroLoad + 1;
    for (var s = 0; s < seq.length; s++) {
      var found = -1;
      while (idx < onEnter.length) {
        var a2 = onEnter[idx];
        var hit = a2 && a2.op === seq[s][0] && seq[s][1](a2);
        idx++;
        if (hit) { found = idx - 1; break; }
      }
      if (found < 0) return []; // sequence not intact -> nothing to guard
      out.push(found);
    }
    return out;
  }

  // kind: "edit" | "delete" | "move" | "retype" | "add" | "attach".
  // index: the touched op index (-1 for whole-list actions). newOp: the
  // incoming op dict (add/attach/retype), else null.
  function pinnedGuardMessages(node, kind, index, newOp) {
    var msgs = [];
    if (!node || !node.id) return msgs;
    var nid = node.id;
    var isStart = START_NODE_IDS[nid] === true;
    var isRestored = RESTORED_IDS[nid] === true;
    var newOpName = newOp ? String(newOp.op || "") : "";

    // Guard A — start-shape: start nodes must NOT load pdb: targets
    // (bundled placeholders only; test_glucose_reachability.py:781-798).
    if (isStart && newOp && newOpName === "load" &&
        String(newOp.target || "").indexOf("pdb:") === 0) {
      msgs.push("start-shape: start nodes must NOT load a pdb: target " +
        "(bundled placeholders only -- test_glucose_reachability.py:" +
        "781-798)");
    }
    // Guard B — the hero-highlight 6-op ordered subsequence on
    // intro.preface (test_glucose_reachability.py:800-843).
    if (nid === "intro.preface" &&
        (kind === "edit" || kind === "delete" || kind === "move" ||
         kind === "retype") && typeof index === "number" && index >= 0) {
      var guarded = heroHighlightIndices(asOpList(node));
      if (guarded.length && guarded.indexOf(index) >= 0) {
        msgs.push("hero-highlight: op #" + index + " is part of " +
          "intro.preface's pinned 6-op hero-highlight sequence (set_color " +
          "hero_cyan -> show_as sticks -> color hero_cyan -> show spheres " +
          "-> set sphere_scale -> label YOU, after the hero_atom load; " +
          "test_glucose_reachability.py:800-843)");
      }
    }
    // Guard C — the restoration reveal (test_glucose_reachability.py:
    // 391-414): the [edit, load, align, show_as] sequence is pinned in
    // order; ANY modification/reordering/append warns.
    if (isRestored) {
      msgs.push("restoration reveal: " + nid + "'s on_enter is the pinned " +
        "[edit, load, align, show_as] sequence, in order " +
        "(test_glucose_reachability.py:391-414) -- this " + kind +
        " modifies it");
    }
    // Guard D — zero-restore-ops on non-restored nodes (07-17 invariant:
    // only the 2 restored nodes carry restore-form ops).
    if (!isRestored && newOp &&
        (newOpName === "edit" || newOpName === "restore" ||
         newOpName === "protonate")) {
      msgs.push("zero-restore-ops: '" + newOpName +
        "' ops exist ONLY on the 2 restored nodes (gly.pfk_restored / " +
        "tca.aconitase_restored; 07-17 invariant) -- adding one to a " +
        "non-restored node");
    }
    return msgs;
  }

  // Run a mutation through ONE confirm when guards fire (cancel aborts).
  function applyWithGuards(fname, nid, kind, index, newOp, mutateFn) {
    var node = EDITOR.nodeGet(fname, nid);
    if (!node) return;
    var msgs = pinnedGuardMessages(node, kind, index, newOp);
    if (msgs.length) {
      var ok = window.confirm(msgs.join("\n") +
        "\n\nProceed anyway? (All warns are confirms, not blocks -- the " +
        "validator carries the authoritative errors.)");
      if (!ok) return;
    }
    mutateFn();
  }

  // -------------------------------------------------------------------------
  // Mutations — ALL through EDITOR.nodeSet on the "on_enter" field (one
  // apply = one undo step + per-file dirty). The touched op dict + its args
  // dict are COPIED before writing (unknown op keys preserved on round-trip,
  // B11; the original nested objects are never mutated in place).
  // -------------------------------------------------------------------------

  function applyOpMutation(fname, nid, index, mutate) {
    var node = EDITOR.nodeGet(fname, nid);
    if (!node) return;
    var list = asOpList(node);
    if (index < 0 || index >= list.length) return;
    var src = list[index];
    if (!src || typeof src !== "object") return;
    var copy = {};
    var k;
    for (k in src) {
      if (Object.prototype.hasOwnProperty.call(src, k)) copy[k] = src[k];
    }
    var srcArgs = (src.args && typeof src.args === "object") ? src.args : {};
    var copyArgs = {};
    for (var a in srcArgs) {
      if (Object.prototype.hasOwnProperty.call(srcArgs, a)) {
        copyArgs[a] = srcArgs[a];
      }
    }
    var hadArgs = Object.prototype.hasOwnProperty.call(src, "args");
    var changed = mutate(copy, copyArgs);
    if (changed === false) return;
    var hasArgs = false;
    for (var c in copyArgs) {
      if (Object.prototype.hasOwnProperty.call(copyArgs, c)) {
        hasArgs = true;
        break;
      }
    }
    if (hadArgs || hasArgs) copy.args = copyArgs;
    var newList = list.slice(0);
    newList[index] = copy;
    EDITOR.nodeSet(fname, nid, "on_enter", newList);
  }

  function setOpArg(fname, nid, index, key, csvN, rawText) {
    var node = EDITOR.nodeGet(fname, nid);
    if (!node) return;
    var list = asOpList(node);
    if (index < 0 || index >= list.length) return;
    var src = list[index] || {};
    var srcArgs = (src.args && typeof src.args === "object") ? src.args : {};
    if (csvN) {
      var arr = parseCsvNumbers(rawText, csvN);
      if (!arr) {
        showNote("\"" + key + "\" must be exactly " + csvN +
          " comma-separated numbers (e.g. the view's 18 floats from " +
          "cmd.get_view) -- nothing committed.");
        return;
      }
      applyWithGuards(fname, nid, "edit", index, null, function () {
        applyOpMutation(fname, nid, index, function (copy, copyArgs) {
          copyArgs[key] = arr;
        });
      });
      return;
    }
    var text = String(rawText == null ? "" : rawText);
    if (text === "") {
      // Absent-vs-empty convention: clearing an optional field REMOVES the
      // key (the house data omits absent keys; never "" / null).
      applyWithGuards(fname, nid, "edit", index, null, function () {
        applyOpMutation(fname, nid, index, function (copy, copyArgs) {
          delete copyArgs[key];
        });
      });
      return;
    }
    var value = coerceLike(srcArgs[key], text);
    applyWithGuards(fname, nid, "edit", index, null, function () {
      applyOpMutation(fname, nid, index, function (copy, copyArgs) {
        copyArgs[key] = value;
      });
    });
  }

  function setOpTarget(fname, nid, index, raw) {
    var text = String(raw == null ? "" : raw);
    applyWithGuards(fname, nid, "edit", index, null, function () {
      applyOpMutation(fname, nid, index, function (copy) {
        if (text === "") delete copy.target; // absent, never empty/null
        else copy.target = text;
      });
    });
  }

  function retypeOp(fname, nid, index, newOpName) {
    var node = EDITOR.nodeGet(fname, nid);
    if (!node) return;
    var list = asOpList(node);
    if (index < 0 || index >= list.length) return;
    var skeleton = skeletonFor(newOpName);
    applyWithGuards(fname, nid, "retype", index, skeleton, function () {
      // Retype replaces the op dict with the new op's skeleton (the old
      // args belonged to the old op shape; undo restores everything).
      var newList = list.slice(0);
      newList[index] = skeleton;
      EDITOR.nodeSet(fname, nid, "on_enter", newList);
    });
  }

  function deleteOp(fname, nid, index) {
    var node = EDITOR.nodeGet(fname, nid);
    if (!node) return;
    var list = asOpList(node);
    if (index < 0 || index >= list.length) return;
    var victim = list[index];
    if (!window.confirm("Delete on_enter op #" + index + " (" +
        summarizeAction(victim) + ") from " + nid + "?")) {
      return;
    }
    applyWithGuards(fname, nid, "delete", index, null, function () {
      var newList = list.slice(0);
      newList.splice(index, 1);
      EDITOR.nodeSet(fname, nid, "on_enter", newList);
    });
  }

  function moveOp(fname, nid, from, dir) {
    var node = EDITOR.nodeGet(fname, nid);
    if (!node) return;
    var list = asOpList(node);
    var to = from + dir;
    if (from < 0 || from >= list.length) return;
    if (to < 0 || to >= list.length) return;
    if (!window.confirm("Reorder on_enter op #" + from + " -> #" + to +
        " on " + nid + "? Order is load-bearing: ops replay in order, and " +
        "pinned sequences (start-shape / hero-highlight / restoration " +
        "reveal) must keep their order.")) {
      return;
    }
    applyWithGuards(fname, nid, "move", from, null, function () {
      var newList = list.slice(0);
      var moved = newList.splice(from, 1)[0];
      newList.splice(to, 0, moved);
      EDITOR.nodeSet(fname, nid, "on_enter", newList);
    });
  }

  function appendOp(fname, nid, opName) {
    var node = EDITOR.nodeGet(fname, nid);
    if (!node) return;
    var skeleton = skeletonFor(opName);
    applyWithGuards(fname, nid, "add", -1, skeleton, function () {
      var fresh = EDITOR.nodeGet(fname, nid);
      var list = asOpList(fresh).slice(0);
      list.push(skeleton);
      EDITOR.nodeSet(fname, nid, "on_enter", list);
    });
  }

  // Fresh op skeleton for the vocabulary select (defaults drawn from the
  // §1.4 verified examples; the target key stays ABSENT until typed).
  function skeletonFor(opName) {
    var entry = vocabEntry(opName);
    var op = { op: opName };
    var args = {};
    if (entry) {
      for (var i = 0; i < entry.fields.length; i++) {
        var f = entry.fields[i];
        if (f.def !== undefined) args[f.key] = f.def;
      }
    }
    var hasArgs = false;
    for (var k in args) {
      if (Object.prototype.hasOwnProperty.call(args, k)) {
        hasArgs = true;
        break;
      }
    }
    if (hasArgs) op.args = args;
    return op;
  }

  // -------------------------------------------------------------------------
  // Paste flow: parse -> PREVIEW (summarized) -> confirm -> attach (append
  // after the existing ops; never reorder existing ops of pinned nodes).
  // -------------------------------------------------------------------------

  function parseAndPreview() {
    var section = refs.section;
    var ta = section && section.querySelector
      ? section.querySelector("textarea[data-oe-paste]") : null;
    if (ta) pasteState.text = ta.value;
    transientNote = "";
    if (!pasteState.text.replace(/\s/g, "")) {
      pasteState.parsed = null;
      pasteState.error = "Nothing to parse -- paste the scene_capture " +
        "output (the jsonc block with the // headers, the JSON array and " +
        "the # NOT CAPTURED notes) first.";
      renderOnenter();
      return;
    }
    try {
      pasteState.parsed = parseScenePaste(pasteState.text);
      pasteState.error = "";
    } catch (e) {
      pasteState.parsed = null;
      pasteState.error = e && e.message ? String(e.message) : String(e);
    }
    renderOnenter();
  }

  function confirmAttach(fname, nid) {
    var parsed = pasteState.parsed;
    if (!parsed || !parsed.ops || !parsed.ops.length) {
      showNote("Nothing parsed yet -- paste the scene_capture output and " +
        "press Parse & preview first.");
      return;
    }
    var node = EDITOR.nodeGet(fname, nid);
    if (!node) return;
    var ops = parsed.ops;
    var isRestored = RESTORED_IDS[nid] === true;
    var msgs = [];
    if (isRestored) {
      msgs.push("restoration reveal: " + nid + "'s on_enter is the pinned " +
        "[edit, load, align, show_as] sequence, in order " +
        "(test_glucose_reachability.py:391-414) -- attaching appends " +
        "AFTER it (existing ops are never reordered)");
    }
    for (var i = 0; i < ops.length; i++) {
      var o = ops[i];
      if (!o || typeof o.op !== "string") continue; // parseScenePaste threw already
      if (START_NODE_IDS[nid] === true && o.op === "load" &&
          String(o.target || "").indexOf("pdb:") === 0) {
        msgs.push("start-shape: pasted op " + i + " loads a pdb: target on " +
          "a start node (bundled placeholders only -- " +
          "test_glucose_reachability.py:781-798)");
      }
      if (!isRestored &&
          (o.op === "edit" || o.op === "restore" || o.op === "protonate")) {
        msgs.push("zero-restore-ops: pasted op " + i + " is '" + o.op +
          "' -- restore-form ops exist ONLY on the 2 restored nodes " +
          "(07-17 invariant)");
      }
    }
    var question = "Attach " + ops.length + " parsed op(s) to " + nid +
      ".on_enter (appended after the existing " + asOpList(node).length + ")?";
    var full = msgs.length
      ? (msgs.join("\n") + "\n\n" + question +
        "\n\nProceed anyway? (warns are confirms, not blocks -- the " +
        "validator carries the authoritative errors.)")
      : question;
    if (!window.confirm(full)) return;
    var newList = asOpList(node).slice(0).concat(ops);
    EDITOR.nodeSet(fname, nid, "on_enter", newList);
    pasteState.parsed = null;
    pasteState.text = "";
    pasteState.error = "";
    transientNote = "";
  }

  // -------------------------------------------------------------------------
  // Renderers.
  // -------------------------------------------------------------------------

  function pinnedBannerHtml(node) {
    var nid = node.id;
    var lines = [];
    if (START_NODE_IDS[nid] === true) {
      lines.push("start node -- on_enter shape pinned: no pdb: loads " +
        "(bundled placeholders only; test_glucose_reachability.py:781-798)" +
        (nid === "intro.preface"
          ? "; and the 6-op hero-highlight sequence must stay intact " +
            "(:800-843)"
          : ""));
    }
    if (RESTORED_IDS[nid] === true) {
      lines.push("restoration node -- on_enter is the pinned [edit, load, " +
        "align, show_as] reveal, in order (test_glucose_reachability.py:" +
        "391-414)");
    }
    if (!lines.length) return "";
    return "<div class=\"oe-note oe-note-info\">Pinned sequence: " +
      esc(lines.join("; ")) + ". All warns are confirms, not blocks -- " +
      "the validator carries the authoritative errors.</div>";
  }

  function phase10Badge() {
    return " <span class=\"oe-badge-phase10\">" + esc(PHASE10_FLAG_TEXT) +
      "</span>";
  }

  // Per-op row: numbered, human summary in the <summary>, expandable
  // per-op fields (op select / target / args per the §1.4 shapes).
  function opRowHtml(i, op, openIdx) {
    var opName = (op && op.op != null) ? String(op.op) : "?";
    var entry = vocabEntry(opName);
    var isUnknown = !entry;
    var args = (op && op.args && typeof op.args === "object") ? op.args : {};
    var html = "";
    html += "<details class=\"oe-row\" data-oe-row=\"" + i + "\"" +
      (openIdx[String(i)] ? " open" : "") + ">";
    html += "<summary class=\"oe-summary\">" +
      "<span class=\"oe-num\">#" + i + "</span> " +
      "<span class=\"oe-opname\">" + esc(opName) + "</span> " +
      esc(summarizeAction(op));
    if (opName === "set_view") html += phase10Badge();
    if (isUnknown) {
      html += " <span class=\"oe-badge-unknown\">unknown op (kept)</span>";
    }
    html += "</summary>";
    // Row actions (buttons live inside the summary; the delegated click
    // handler preventDefaults so the row does not toggle).
    html += "<div class=\"oe-btns\">" +
      "<button type=\"button\" class=\"oe-btn\" data-oe-act=\"move-up\" " +
      "data-oe-i=\"" + i + "\" title=\"move up (order matters)\">&#9650; up</button>" +
      "<button type=\"button\" class=\"oe-btn\" data-oe-act=\"move-down\" " +
      "data-oe-i=\"" + i + "\" title=\"move down (order matters)\">&#9660; down</button>" +
      "<button type=\"button\" class=\"oe-btn oe-btn-del\" " +
      "data-oe-act=\"delete\" data-oe-i=\"" + i + "\">&#10005; delete</button>" +
      "</div>";
    // op select (the KNOWN vocabulary; an unknown current op gets an extra
    // selected option so the value round-trips visually).
    html += "<label class=\"oe-field\"><span>op</span>" +
      "<select data-oe-opselect=\"" + i + "\">";
    for (var v = 0; v < OP_VOCAB.length; v++) {
      html += "<option value=\"" + esc(OP_VOCAB[v].op) + "\"" +
        (OP_VOCAB[v].op === opName ? " selected" : "") + ">" +
        esc(OP_VOCAB[v].op) + "</option>";
    }
    if (isUnknown) {
      html += "<option value=\"" + esc(opName) + "\" selected>" +
        esc(opName) + " (unknown)</option>";
    }
    html += "</select></label>";
    // target (hidden for ops without a target: hide_all / set_color /
    // select_focus / zoom / set_view carry none in the data).
    var hasTarget = entry ? entry.target === true : true;
    if (hasTarget) {
      var tv = (op && op.target != null) ? String(op.target) : "";
      html += "<label class=\"oe-field\"><span>target</span>" +
        "<input type=\"text\" data-oe-target=\"" + i + "\" value=\"" +
        esc(tv) + "\" placeholder=\"e.g. pdb:4PFK | _smoke.pdb | obj name\">" +
        "</label>";
    }
    // args fields per the §1.4 shapes.
    var fields = entry ? entry.fields : [];
    for (var f = 0; f < fields.length; f++) {
      var fd = fields[f];
      var val;
      if (fd.csv) {
        var arr = args[fd.key];
        val = (Object.prototype.toString.call(arr) === "[object Array]")
          ? arr.join(", ") : "";
      } else {
        val = (args[fd.key] != null) ? String(args[fd.key]) : "";
      }
      var optionalTxt = fd.optional ? " (optional)" : "";
      if (fd.select) {
        html += "<label class=\"oe-field\"><span>" + esc(fd.key) +
          optionalTxt + "</span><select data-oe-arg=\"" + i +
          "\" data-oe-key=\"" + esc(fd.key) + "\">";
        for (var sv = 0; sv < fd.select.length; sv++) {
          html += "<option value=\"" + esc(fd.select[sv]) + "\"" +
            (String(args[fd.key]) === fd.select[sv] ? " selected" : "") +
            ">" + esc(fd.select[sv]) + "</option>";
        }
        html += "</select></label>";
      } else {
        html += "<label class=\"oe-field\"><span>" + esc(fd.key) +
          optionalTxt + "</span>" +
          "<input type=\"text\" data-oe-arg=\"" + i + "\" data-oe-key=\"" +
          esc(fd.key) + "\"" +
          (fd.csv ? " data-oe-csv=\"" + fd.csv + "\"" : "") +
          " value=\"" + esc(val) + "\"" +
          (fd.ph ? " placeholder=\"" + esc(fd.ph) + "\"" : "") +
          "></label>";
      }
    }
    // B11: preserved extra keys (top-level beyond op/target/args, and args
    // keys outside the vocabulary field shapes) — read-only here, NEVER
    // removed; they round-trip untouched through every mutation.
    var extras = [];
    var knownTop = { op: true, target: true, args: true };
    for (var tk in op) {
      if (Object.prototype.hasOwnProperty.call(op, tk) && !knownTop[tk]) {
        extras.push({ where: "", key: tk, val: op[tk] });
      }
    }
    var knownArgKeys = {};
    for (var fk = 0; fk < fields.length; fk++) {
      knownArgKeys[fields[fk].key] = true;
    }
    for (var ak in args) {
      if (Object.prototype.hasOwnProperty.call(args, ak) &&
          !knownArgKeys[ak] && args[ak] !== undefined) {
        extras.push({ where: "args.", key: ak, val: args[ak] });
      }
    }
    for (var ex = 0; ex < extras.length; ex++) {
      var shown = "";
      try { shown = JSON.stringify(extras[ex].val); } catch (e3) {
        shown = String(extras[ex].val);
      }
      if (shown.length > 90) shown = shown.slice(0, 87) + "...";
      html += "<div class=\"oe-extra\">preserved extra key: <code>" +
        esc(extras[ex].where + extras[ex].key) + "</code> = <code>" +
        esc(shown) + "</code> (round-trips untouched -- B11)</div>";
    }
    html += "</details>";
    return html;
  }

  function previewHtml() {
    var parsed = pasteState.parsed;
    if (!parsed) return "";
    var html = "";
    html += "<div class=\"oe-preview\">";
    html += "<div class=\"oe-preview-head\">Parsed " + parsed.ops.length +
      " op(s)" + (parsed.noteLines
        ? (" &middot; " + parsed.noteLines + " \"# NOT CAPTURED\" note " +
           "line(s) in the paste (informational -- capture could not map " +
           "those session facts; nothing was silently dropped)")
        : "") + "</div>";
    html += "<ol class=\"oe-preview-list\">";
    for (var i = 0; i < parsed.ops.length; i++) {
      var o = parsed.ops[i];
      html += "<li>" + esc(summarizeAction(o));
      if (o && o.op === "set_view") html += phase10Badge();
      if (o && (o.op === "load" || o.op === "hide_all")) {
        html += " <span class=\"oe-badge-replay\">replay-side op (never " +
          "emitted by scene_capture)</span>";
      }
      html += "</li>";
    }
    html += "</ol>";
    if (parsed.warnings && parsed.warnings.length) {
      html += "<div class=\"oe-preview-warn\">";
      for (var w = 0; w < parsed.warnings.length; w++) {
        html += "&#9888; " + esc(parsed.warnings[w]) +
          (w < parsed.warnings.length - 1 ? "<br>" : "");
      }
      html += "</div>";
    }
    html += "<div class=\"oe-preview-actions\">" +
      "<button type=\"button\" class=\"oe-btn oe-btn-primary\" " +
      "data-oe-act=\"confirm-attach\">Confirm attach (" +
      parsed.ops.length + ")</button>" +
      "<button type=\"button\" class=\"oe-btn\" " +
      "data-oe-act=\"cancel-preview\">Cancel</button>" +
      "</div>";
    html += "</div>";
    return html;
  }

  function renderOnenter() {
    var section = refs.section;
    if (!section) return;
    var node = selectedNode();
    var fname = selectedFile();
    if (!EDITOR.state.bundle || !node || !fname) {
      section.innerHTML = "";
      return;
    }
    // Harvest in-progress state BEFORE the rebuild: open rows (by index)
    // and the paste textarea text (paste + preview survive unrelated
    // re-renders).
    var openIdx = {};
    if (section.querySelectorAll) {
      var rows = section.querySelectorAll("details[data-oe-row]");
      for (var r = 0; r < rows.length; r++) {
        if (rows[r].hasAttribute("open")) {
          openIdx[String(rows[r].getAttribute("data-oe-row"))] = true;
        }
      }
      var ta = section.querySelector("textarea[data-oe-paste]");
      if (ta) pasteState.text = ta.value;
    }
    var ops = asOpList(node);
    var html = "";
    html += "<h3>on_enter (scene)</h3>";
    html += pinnedBannerHtml(node);
    if (transientNote) {
      html += "<div class=\"oe-note oe-note-info\">" + esc(transientNote) +
        "</div>";
    }
    if (!Object.prototype.hasOwnProperty.call(node, "on_enter")) {
      html += "<div class=\"oe-note oe-note-warn\">no on_enter array on " +
        "this node (unusual -- every node carries one); Add/attach below " +
        "creates it.</div>";
    }
    html += "<div class=\"oe-list\">";
    for (var i = 0; i < ops.length; i++) {
      html += opRowHtml(i, ops[i], openIdx);
    }
    if (!ops.length) {
      html += "<div class=\"oe-none\">no on_enter ops</div>";
    }
    html += "</div>";
    // Add row (append at the end; order matters -- move buttons reposition).
    html += "<div class=\"oe-addrow\">" +
      "<select data-oe-addselect>";
    for (var v = 0; v < OP_VOCAB.length; v++) {
      html += "<option value=\"" + esc(OP_VOCAB[v].op) + "\">" +
        esc(OP_VOCAB[v].op) + "</option>";
    }
    html += "</select>" +
      "<button type=\"button\" class=\"oe-btn\" data-oe-act=\"add-op\">" +
      "+ Add op</button></div>";
    // Paste-in (B8 core): scene_capture jsonc -> parse -> preview -> attach.
    html += "<div class=\"oe-paste-block\">" +
      "<h4>Paste a scene_capture block</h4>" +
      "<div class=\"oe-paste-help\">Run <code>tools/scene_capture.py</code> " +
      "in a real PyMOL session, copy its output (the jsonc block: " +
      "<code>//</code> headers, ONE JSON array of ops, " +
      "<code># NOT CAPTURED</code> notes) and paste it below. Unknown ops " +
      "are warn-but-accepted (kept); a <code>set_view</code> entry is " +
      "accepted with the Phase-10 flag.</div>" +
      "<textarea class=\"json-area oe-paste-area\" rows=\"7\" " +
      "data-oe-paste=\"1\" placeholder=\"// scene-capture: found N molecule object(s)...&#10;[&#10;  {&quot;op&quot;: ...}&#10;]&#10;# NOT CAPTURED: ...\">" +
      esc(pasteState.text) + "</textarea>" +
      "<div class=\"oe-paste-actions\">" +
      "<button type=\"button\" class=\"oe-btn\" data-oe-act=\"parse-paste\">" +
      "Parse &amp; preview</button></div>" +
      (pasteState.error
        ? "<div class=\"oe-note oe-note-err\">&#9888; " +
          esc(pasteState.error) + "</div>"
        : "") +
      previewHtml() +
      "</div>";
    section.innerHTML = html;
  }

  // -------------------------------------------------------------------------
  // Transient note (declined mutations / parse hints; lives until the next
  // successful mutation re-render).
  // -------------------------------------------------------------------------

  function showNote(text) {
    transientNote = String(text == null ? "" : text);
    renderOnenter();
  }

  // -------------------------------------------------------------------------
  // Event wiring — delegated on the STABLE #node-form-onenter section (one
  // listener per concern; survives every innerHTML rebuild). My inputs use
  // data-oe-* attributes (never data-field / data-role), so the sibling
  // listeners on the parent aside (40_form's text bindings + ending select)
  // ignore them.
  // -------------------------------------------------------------------------

  function wireOnenter() {
    var section = refs.section;
    if (!section) return;

    EDITOR.delegate(section, "click", "data-oe-act", function (el, ev) {
      // Buttons live inside <summary>: cancel the default toggle so the
      // row does not open/close when an action button is clicked.
      if (ev && ev.preventDefault) {
        var p = el.parentNode;
        while (p && p !== section) {
          if (p.tagName && String(p.tagName).toLowerCase() === "summary") {
            ev.preventDefault();
            break;
          }
          p = p.parentNode;
        }
      }
      var nid = EDITOR.state.sel;
      var fname = nid ? EDITOR.fileOfNode(nid) : null;
      if (!nid || !fname) return;
      var act = el.getAttribute("data-oe-act");
      var idxAttr = el.getAttribute("data-oe-i");
      var idx = (idxAttr === null || idxAttr === "") ? -1
        : parseInt(idxAttr, 10);
      if (act === "move-up") {
        moveOp(fname, nid, idx, -1);
      } else if (act === "move-down") {
        moveOp(fname, nid, idx, 1);
      } else if (act === "delete") {
        deleteOp(fname, nid, idx);
      } else if (act === "add-op") {
        var sel = section.querySelector("select[data-oe-addselect]");
        appendOp(fname, nid, sel ? sel.value : "hide_all");
      } else if (act === "parse-paste") {
        parseAndPreview();
      } else if (act === "confirm-attach") {
        confirmAttach(fname, nid);
      } else if (act === "cancel-preview") {
        pasteState.parsed = null;
        pasteState.error = "";
        renderOnenter();
      }
    });

    // Field commits (change = one apply step per commit, like the form's
    // text fields; never per keystroke).
    section.addEventListener("change", function (ev) {
      var el = ev.target;
      if (!el || !el.getAttribute) return;
      var nid = EDITOR.state.sel;
      var fname = nid ? EDITOR.fileOfNode(nid) : null;
      if (!nid || !fname) return;
      var opAttr = el.getAttribute("data-oe-opselect");
      if (opAttr !== null) {
        retypeOp(fname, nid, parseInt(opAttr, 10), el.value);
        return;
      }
      var tAttr = el.getAttribute("data-oe-target");
      if (tAttr !== null) {
        setOpTarget(fname, nid, parseInt(tAttr, 10), el.value);
        return;
      }
      var aAttr = el.getAttribute("data-oe-arg");
      if (aAttr !== null) {
        var csvAttr = el.getAttribute("data-oe-csv");
        setOpArg(fname, nid, parseInt(aAttr, 10),
                 el.getAttribute("data-oe-key"),
                 csvAttr !== null ? parseInt(csvAttr, 10) : 0,
                 el.value);
      }
    });
  }

  // -------------------------------------------------------------------------
  // Asset CSS (injected at runtime per the pipeline's per-feature CSS rule).
  // -------------------------------------------------------------------------

  EDITOR.injectCss(
    "/* injected by 43_onenter.js (07.1-16): on_enter editor styles */\n" +
    "#node-form-onenter h3 { margin: 0 0 6px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #888888; }\n" +
    "#node-form-onenter h4 { margin: 8px 0 4px; font-size: 12.5px; color: #333333; }\n" +
    "#node-form-onenter .oe-row { border: 1px solid #dde3ec; border-radius: 4px; margin: 4px 0; background: #fbfcfe; }\n" +
    "#node-form-onenter .oe-row[open] { background: #ffffff; }\n" +
    "#node-form-onenter .oe-summary { cursor: pointer; padding: 5px 7px; font-size: 12px; list-style: none; }\n" +
    "#node-form-onenter .oe-summary::-webkit-details-marker { display: none; }\n" +
    "#node-form-onenter .oe-summary::before { content: '\\25B8 '; color: #999999; }\n" +
    "#node-form-onenter .oe-row[open] .oe-summary::before { content: '\\25BE '; }\n" +
    "#node-form-onenter .oe-num { font-family: Consolas, monospace; color: #888888; font-size: 10.5px; }\n" +
    "#node-form-onenter .oe-opname { font-family: Consolas, monospace; font-weight: bold; color: #2b3a55; margin-right: 4px; }\n" +
    "#node-form-onenter .oe-badge-phase10 { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 8px; border: 1px solid #b8860b; background: #fdf6e3; color: #6b4508; }\n" +
    "#node-form-onenter .oe-badge-unknown { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 8px; border: 1px dashed #b22222; background: #fdeeea; color: #7a1616; }\n" +
    "#node-form-onenter .oe-badge-replay { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 8px; border: 1px dotted #4682b4; background: #eef4fb; color: #2b4a68; }\n" +
    "#node-form-onenter .oe-btns { display: flex; gap: 4px; padding: 0 7px 5px; }\n" +
    "#node-form-onenter .oe-btn { font-size: 11px; padding: 2px 8px; border: 1px solid #6d7f9b; background: #e9eef7; border-radius: 4px; cursor: pointer; }\n" +
    "#node-form-onenter .oe-btn:hover { background: #dbe4f2; }\n" +
    "#node-form-onenter .oe-btn-del { border-color: #c26a5a; background: #fdf0ed; color: #8c2f1f; }\n" +
    "#node-form-onenter .oe-btn-del:hover { background: #f6d9d2; }\n" +
    "#node-form-onenter .oe-btn-primary { border-color: #2e8b57; background: #eef7ee; color: #1d5c38; font-weight: bold; }\n" +
    "#node-form-onenter .oe-btn-primary:hover { background: #dff2df; }\n" +
    "#node-form-onenter .oe-field { display: flex; align-items: center; gap: 6px; margin: 3px 7px; font-size: 11.5px; }\n" +
    "#node-form-onenter .oe-field > span { flex: none; width: 92px; color: #555555; font-family: Consolas, monospace; font-size: 11px; }\n" +
    "#node-form-onenter .oe-field input, #node-form-onenter .oe-field select { flex: 1 1 auto; min-width: 0; font-family: Consolas, monospace; font-size: 11.5px; padding: 3px 6px; border: 1px solid #aab3c0; border-radius: 4px; background: #ffffff; }\n" +
    "#node-form-onenter .oe-extra { margin: 3px 7px; padding: 3px 6px; border: 1px dashed #d9a544; background: #fdf9ee; color: #6b4508; font-size: 10.5px; border-radius: 4px; }\n" +
    "#node-form-onenter .oe-extra code { font-size: 10px; word-break: break-all; }\n" +
    "#node-form-onenter .oe-note { margin: 6px 0; padding: 6px 8px; border-radius: 4px; font-size: 11.5px; }\n" +
    "#node-form-onenter .oe-note-info { border: 1px solid #9db4cc; border-left: 4px solid #4682b4; background: #eef4fb; color: #2b4a68; }\n" +
    "#node-form-onenter .oe-note-warn { border: 1px solid #d9a544; border-left: 4px solid #b8860b; background: #fdf6e3; color: #6b4508; }\n" +
    "#node-form-onenter .oe-note-err { border: 1px solid #d98c7a; border-left: 4px solid #b22222; background: #fdeeea; color: #7a1616; }\n" +
    "#node-form-onenter .oe-none { font-size: 11.5px; color: #888888; font-style: italic; margin: 3px 0; }\n" +
    "#node-form-onenter .oe-addrow { display: flex; gap: 5px; margin: 8px 0 4px; }\n" +
    "#node-form-onenter .oe-addrow select { flex: 1 1 auto; min-width: 0; font-family: Consolas, monospace; font-size: 11.5px; padding: 3px 5px; border: 1px solid #aab3c0; border-radius: 4px; background: #ffffff; }\n" +
    "#node-form-onenter .oe-paste-block { margin-top: 10px; padding-top: 8px; border-top: 1px solid #e0e0e0; }\n" +
    "#node-form-onenter .oe-paste-help { font-size: 11px; color: #555555; margin: 4px 0; }\n" +
    "#node-form-onenter .oe-paste-help code, #node-form-onenter .oe-paste-block code { font-family: Consolas, monospace; font-size: 10.5px; background: #f4f6f9; padding: 0 3px; border-radius: 3px; }\n" +
    "#node-form-onenter .oe-paste-area { min-height: 110px; font-size: 11px; }\n" +
    "#node-form-onenter .oe-paste-actions { margin: 5px 0; }\n" +
    "#node-form-onenter .oe-preview { margin: 8px 0; padding: 7px 9px; border: 1px solid #9db4cc; border-left: 4px solid #4682b4; border-radius: 4px; background: #f4f8fc; }\n" +
    "#node-form-onenter .oe-preview-head { font-size: 11.5px; font-weight: bold; color: #2b4a68; margin-bottom: 4px; }\n" +
    "#node-form-onenter .oe-preview-list { margin: 4px 0; padding-left: 22px; font-size: 11.5px; }\n" +
    "#node-form-onenter .oe-preview-list li { margin: 2px 0; }\n" +
    "#node-form-onenter .oe-preview-warn { margin: 5px 0; padding: 5px 7px; border: 1px solid #d9a544; background: #fdf6e3; color: #6b4508; font-size: 11px; border-radius: 4px; }\n" +
    "#node-form-onenter .oe-preview-actions { display: flex; gap: 5px; margin-top: 6px; }\n"
  );

  // -------------------------------------------------------------------------
  // Init: locate the mount, wire the events, first render. Runs once from
  // the shell bootstrap (EDITOR.runInits).
  // -------------------------------------------------------------------------

  function initOnenter() {
    refs.section = document.getElementById("node-form-onenter");
    if (!refs.section) {
      warn("EDITOR on_enter editor (43_onenter.js): #node-form-onenter " +
           "mount missing -- on_enter editor disabled.");
      return;
    }
    wireOnenter();
    renderOnenter();
  }

  // Registration per the 07.1-04 convention: the renderer registers as a
  // view (re-renders on EDITOR.select + after every afterChange via the
  // core's rerender dispatcher); the DOM work runs from the shell
  // bootstrap. (The node-form aside's dedicated setFormRenderer slot is
  // 40_form.js's -- this asset owns only its own sub-section.)
  EDITOR.view("onenter", renderOnenter);
  EDITOR.init(initOnenter);

  // Expose the paste contract for the diagnostics tab (07.1-19) and tests:
  // a guarded extension of the EDITOR namespace owned by THIS asset.
  if (!EDITOR.onenter) EDITOR.onenter = {};
  EDITOR.onenter.parseScenePaste = parseScenePaste;
  EDITOR.onenter.summarizeAction = summarizeAction;
  EDITOR.onenter.OP_NAMES = OP_NAMES;
  EDITOR.onenter.PHASE10_FLAG_TEXT = PHASE10_FLAG_TEXT;

})();
