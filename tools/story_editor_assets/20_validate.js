/* ==========================================================================
 * 20_validate.js — the pre-save validator: the rule-for-rule JS mirror of
 * tools/story_editor_lint.py (07.1-08).
 *
 * OWNERSHIP: this asset belongs to plan 07.1-08 (Wave 3). It extends the
 * window.EDITOR namespace from its own file (00_core.js = 07.1-04 owns the
 * core; never edit another plan's asset).
 *
 * PARITY SOURCE (Pitfall S4 drift-guard): every rule below ports ONE rule
 * function of tools/story_editor_lint.py 1:1 — same rule id, same severity
 * (error vs notice), same BFS semantics, same sanctioned-residual encoding.
 * Each rule's code comment carries "src: <python path:line>" naming the
 * Python source that owns the rule (the repo's "# src:" convention). The
 * lint itself imports the test-verified rpg validators instead of
 * reimplementing them (rpg/story/validate.py, rpg/edit_router.py,
 * rpg/citations.py) — this asset ports THOSE semantics, never a novel JS
 * design (07.1-RESEARCH-SAFETY "Don't Hand-Roll": a divergent JS
 * reimplementation would create two sources of truth).
 *
 * BFS PARITY (load-bearing): bfsReachable follows choice.goto edges ONLY.
 * cond/weight are IGNORED (the Python gate's BFS is structural-only,
 * rpg/story/validate.py:198-202) and on_enter_divert is NEVER followed
 * (dormant per 05.1-DESIGN — no story file uses it; a JS BFS that followed
 * conds or diverts would disagree with the Python gate and report false
 * green/red, RESEARCH-SAFETY "Don't Hand-Roll" last row + Pitfall S4).
 *
 * API (consumed by the save panel, plan 07.1-13, and the status bar):
 *   EDITOR.validate(bundle)      -> {errors, notices, countShifts, blocked}
 *                                   errors/notices: [{kind, node, detail,
 *                                   src, severity}]
 *   EDITOR.validateCurrent()     -> validate(EDITOR.state.bundle), cached
 *                                   in EDITOR._lastValidation
 *   EDITOR.saveBlocked()         -> true iff the live bundle has >=1 error
 *                                   (the save panel refuses while true)
 *   EDITOR.bfsReachable(bundle)  -> {start, reachable, order, endings,
 *                                   reachableEndings, unreachableEndings}
 *   EDITOR.hooks.validate        -> this asset registers the re-validation
 *                                   hook via EDITOR.init (00_core dispatches
 *                                   every hook in its own try/catch, so
 *                                   validation runs after every mutation
 *                                   and one broken hook never kills the
 *                                   state layer).
 *
 * RESULT SEVERITY CONTRACT (mirrors the lint's exit contract): errors gate
 * the save (saveBlocked() === true); notices NEVER block — the sanctioned
 * residual and the count_shift acknowledgment path are notices by design
 * (lint exit 0 with notices is a green run).
 *
 * STYLE: one classic script, one IIFE, ES5 only (var, no arrow functions,
 * no let/const, no modules) — same discipline 00_core.js/05_json.js pin.
 * ========================================================================== */

(function () {
  "use strict";

  // -------------------------------------------------------------------------
  // Frozen constants — ported 1:1 from tools/story_editor_lint.py (each
  // cites its Python source; the JS port mirrors these exactly).
  // -------------------------------------------------------------------------

  // The frozen molops dispatch vocabulary: the 10 ops present in story data
  // (hide_all, load, show_as, edit, align, set_color, color, show, set,
  // label) + the molops extras the editor may paste (select_focus, zoom,
  // delete, protonate, restore). Any on_enter op outside this set raises
  // NotImplementedError at dispatch. src: rpg/pymol_layer/molops.py:140-291
  var OP_VOCABULARY = {
    "hide_all": true, "show": true, "show_as": true, "select_focus": true,
    "zoom": true, "color": true, "set_color": true, "label": true,
    "set": true, "align": true, "load": true, "delete": true, "edit": true,
    "protonate": true, "restore": true
  };
  // Sorted rendering for the unknown_op detail (str(sorted(frozenset)) in
  // the Python lint).
  var OP_VOCABULARY_SORTED = [
    "align", "color", "delete", "edit", "hide_all", "label", "load",
    "protonate", "restore", "select_focus", "set", "set_color", "show",
    "show_as", "zoom"
  ];

  // set_view is NOT dispatchable this phase: accepted (never an error) but
  // visibly flagged. src: tools/scene_capture.py (the Phase-10 WARNING
  // precedent); rpg/pymol_layer/molops.py:286-291 (unknown op raise).
  var PHASE10_OPS = { "set_view": true };

  // The 07-12 DC-A restoration-branch nodes: entry is ROUTER-ONLY (no
  // incoming choice.goto — engine.apply_player_edit routes known edits
  // directly; zero incoming edges is load-bearing).
  // src: tests/test_glucose_reachability.py:326-452
  //      (test_restoration_nodes_reachable_non_ending)
  var ROUTER_ONLY_NODES = ["gly.pfk_restored", "tca.aconitase_restored"];

  // The documented structural stub exempt from the two-layer/no-TBD scans
  // (its text_dramatic IS the "[STRUCTURAL STUB:" marker — the bundle's
  // only sanctioned TBD). src: tests/test_glucose_content.py:91-95 + 174-184
  var DOCUMENTED_STUB_NODES = { "edit.prompt": true };

  // The 07-01-sanctioned Phase-8 stubs: the ONLY nodes allowed to reference
  // PLACEHOLDER_PHASE8 (and the citation gate's ONLY sanctioned residual —
  // exactly 2 MISSING + 0 UNAPPROVED). ENCODED EXACTLY (Pitfall S6):
  // PLACEHOLDER_PHASE8 elsewhere, any other PLACEHOLDER*, or a sanctioned
  // stub LOSING its reference is a placeholder_misuse error.
  // src: tests/test_glucose_content.py:97-99 + 213-236
  var PHASE8_STUB_NODES = ["fa.stub", "alc.stub"];
  var PHASE8_CLAIM = "PLACEHOLDER_PHASE8";

  // Start nodes load bundled placeholders ONLY (no network fetch at game
  // start). The owning test pins intro.preface / intro.shell_glucose /
  // intro.select — all intro.* — so the rule derives the start set as the
  // manifest start + the intro.* prefix.
  // src: tests/test_glucose_reachability.py:868-885
  //      (test_start_nodes_do_not_reference_real_pdb_fetch)
  var START_NODE_PREFIX = "intro.";

  // tca.shuffle is the graph's ONLY weighted node (the single seeded-RNG
  // surface; 0.5/0.5 design B). src: tests/test_glucose_content.py:539-557
  var SHUFFLE_NODE = "tca.shuffle";

  // tca.citrate_synthase is the edit:structural reframe: carries an
  // edit:enzyme: tag but deliberately NO edits.json bucket (zero natural
  // disease point variants). src: tests/test_glucose_content.py:404-449
  var STRUCTURAL_TAG_ENZYME = "tca.citrate_synthase";

  // The pinned counts, reported as values NOT assertions (the count_shift
  // acknowledgment path). Sources: tests/test_glucose_reachability.py:136
  // (== 57 nodes), :157 (== 21 endings, 1T+3G+2N+15B), :264 (== 15
  // edit-allowed) and the viewer's pinned constants.
  // src: tools/story_graph_viewer.py:96-105 (EXPECTED_NODES /
  //      EXPECTED_TIER_COUNTS / EXPECTED_EDIT_ALLOWED)
  var PINNED_NODE_COUNT = 57;
  var PINNED_TIER_COUNTS = { "true": 1, "good": 3, "normal": 2, "bad": 15 };
  var PINNED_EDIT_ALLOWED = [
    "gly.pfk", "gly.pyruvate_kinase", "pyr.pdh", "tca.citrate_synthase",
    "tca.aconitase", "tca.shuffle", "tca.isocitrate_dh", "tca.akg_dh",
    "tca.succinyl_coa_synthetase", "tca.fumarase", "tca.malate_dh",
    "etc.complex_i", "etc.complex_ii", "etc.complex_iii", "etc.complex_iv"
  ];
  var PINNED_TIER_ORDER = ["true", "good", "normal", "bad"];

  // The same-commit obligations the count_shift notice names (the exact
  // pinned-test names + the viewer's pinned constants).
  var COUNT_SHIFT_TESTS = [
    "test_manifest_loads_all_57_nodes",
    "test_reachability_green_all_four_tiers",
    "test_15_edit_allowed_nodes"
  ];
  var COUNT_SHIFT_CONSTANTS = [
    "EXPECTED_NODES", "EXPECTED_TIER_COUNTS", "EXPECTED_EDIT_ALLOWED"
  ];

  // The broken cond form: <dict>.<attr> attribute access (NOT followed by
  // "(", so flags.get(...) — the MANDATORY dict-method form — never
  // matches). The owning test scans flags.; the lint (and this port)
  // extend the same broken-form rule to the other dict namespaces the
  // interpreter exposes (visits/counters — identical AttributeError ->
  // caught -> choice hidden -> stuck failure mode).
  // src: tests/test_glucose_reachability.py:716-752
  //      (test_no_broken_dict_attribute_conds_remain)
  //      + rpg/story/interpreter.py:101-131 (_cond namespace)
  var BROKEN_COND_RE =
    /(flags|visits|counters)\.[a-zA-Z_][a-zA-Z0-9_]*(?![a-zA-Z0-9_])(?!\()/;

  // -------------------------------------------------------------------------
  // Small ES5 helpers.
  // -------------------------------------------------------------------------

  function hasOwn(obj, key) {
    return !!obj && Object.prototype.hasOwnProperty.call(obj, key);
  }

  function asArray(value) {
    return Object.prototype.toString.call(value) === "[object Array]"
      ? value : [];
  }

  function isEnding(node) {
    // src: rpg/story/validate.py:150-160 (_is_ending) — is_ending not None.
    return !!node && node.is_ending !== undefined && node.is_ending !== null;
  }

  function getGoto(choice) {
    // src: rpg/story/validate.py:137-147 (_goto) — None means a leaf choice.
    return (choice && typeof choice === "object") ? choice.goto : null;
  }

  function trimText(value) {
    return String(value === undefined || value === null ? "" : value)
      .replace(/^\s+|\s+$/g, "");
  }

  function sortedKeys(setObj) {
    var keys = [];
    for (var k in setObj) {
      if (Object.prototype.hasOwnProperty.call(setObj, k)) keys.push(k);
    }
    keys.sort();
    return keys;
  }

  function setDifference(aSet, bSet) {
    var out = [];
    var keys = sortedKeys(aSet);
    for (var i = 0; i < keys.length; i++) {
      if (!hasOwn(bSet, keys[i])) out.push(keys[i]);
    }
    return out;
  }

  function renderList(arr) {
    // Deterministic JS-ish list rendering for detail strings (the Python
    // lint renders str(list) — cosmetics only; ids and counts are pinned,
    // prose is not).
    var parts = [];
    for (var i = 0; i < arr.length; i++) parts.push(JSON.stringify(arr[i]));
    return "[" + parts.join(", ") + "]";
  }

  function issue(kind, node, detail, src, severity) {
    return {
      kind: kind,
      node: (node === undefined || node === null) ? null : node,
      detail: detail,
      src: src,
      severity: severity || "error"
    };
  }

  // -------------------------------------------------------------------------
  // stableStringify — the js equivalent of json.dumps(x, sort_keys=True)
  // (recursively sorted object keys; Python's default ", " / ": "
  // separators so rendered signature details read the same as the lint's).
  // Used for the duplicate_signature dedup key (rpg/edit_router.py:207)
  // and for _norm_val's nested-dict branch (rpg/story/model.py:154-161).
  // -------------------------------------------------------------------------

  function stableStringify(value) {
    var t = Object.prototype.toString.call(value);
    var i;
    var parts;
    if (t === "[object Array]") {
      parts = [];
      for (i = 0; i < value.length; i++) parts.push(stableStringify(value[i]));
      return "[" + parts.join(", ") + "]";
    }
    if (value && typeof value === "object") {
      var keys = sortedKeys(value);
      var kv = [];
      for (i = 0; i < keys.length; i++) {
        kv.push(JSON.stringify(keys[i]) + ": " + stableStringify(value[keys[i]]));
      }
      return "{" + kv.join(", ") + "}";
    }
    if (typeof value === "number") {
      return isFinite(value) ? String(value) : "null";
    }
    if (typeof value === "boolean") return value ? "true" : "false";
    if (value === null || value === undefined) return "null";
    return JSON.stringify(String(value));
  }

  // -------------------------------------------------------------------------
  // Signature normalization — the plan's "normalized-dict equality: target
  // strip+lowercase, args stringify". Port of EditIntent.signature()
  // (rpg/story/model.py:112-126: op verbatim, target stripped+lowercased,
  // args values through _norm_val) — the matching semantics the router
  // applies at route time (rpg/edit_router.py:122-149). Two edits.json
  // entries whose NORMALIZED signatures collide would collide at route()
  // (one entry silently unreachable) — the editor flags them pre-save.
  // -------------------------------------------------------------------------

  function normVal(v) {
    // src: rpg/story/model.py:154-161 (_norm_val): scalars -> str(v).strip();
    // nested dicts/lists -> sorted-key JSON.
    var t = Object.prototype.toString.call(v);
    if (t === "[object Array]" || (v && typeof v === "object")) {
      return stableStringify(v);
    }
    return trimText(v);
  }

  function normalizeSignature(sig) {
    if (!sig || typeof sig !== "object") return "{}";
    var rawArgs = (sig.args && typeof sig.args === "object") ? sig.args : {};
    var args = {};
    for (var k in rawArgs) {
      if (Object.prototype.hasOwnProperty.call(rawArgs, k)) {
        args[k] = normVal(rawArgs[k]);
      }
    }
    return stableStringify({
      op: (sig.op === undefined || sig.op === null) ? null : sig.op,
      target: trimText(sig.target).toLowerCase(),
      args: args
    });
  }

  // -------------------------------------------------------------------------
  // Bundle flattening — the editor bundle (00_core.js shape: files -> nodes
  // per manifest-listed file, order = manifest file order) -> one ordered
  // {id: node} dict, mirroring the lint's load_bundle merge
  // (tools/story_editor_lint.py:245-298: manifest file order, per-file
  // insertion order preserved). Duplicate ids across files are the LOADER's
  // contract (10_load, 07.1-07; StoryGraph.load raises) — this merge is
  // last-wins purely so validation can still run on a degraded bundle.
  // -------------------------------------------------------------------------

  function flattenNodes(bundle) {
    var nodes = {};
    if (!bundle || !bundle.files) return nodes;
    var order = (Object.prototype.toString.call(bundle.order) ===
                 "[object Array]" && bundle.order.length)
      ? bundle.order : Object.keys(bundle.files);
    for (var i = 0; i < order.length; i++) {
      var file = bundle.files[order[i]];
      var fnodes = (file && file.nodes && typeof file.nodes === "object")
        ? file.nodes : null;
      if (!fnodes) continue;
      for (var nid in fnodes) {
        if (Object.prototype.hasOwnProperty.call(fnodes, nid)) {
          nodes[nid] = fnodes[nid];
        }
      }
    }
    return nodes;
  }

  function castIdList(bundle) {
    var ids = [];
    var cast = bundle ? bundle.cast : null;
    var enzymes = (cast && typeof cast === "object") ? cast.enzymes : null;
    var list = asArray(enzymes);
    for (var i = 0; i < list.length; i++) {
      var entry = list[i];
      if (entry && typeof entry === "object" && entry.id !== undefined) {
        ids.push(entry.id);
      }
    }
    return ids;
  }

  // -------------------------------------------------------------------------
  // BFS — the reachability engine. PARITY IS LOAD-BEARING: goto edges ONLY;
  // cond/weight IGNORED; on_enter_divert NEVER followed (dormant,
  // 05.1-DESIGN — following it in JS would disagree with the Python gate).
  // src: rpg/story/validate.py:167-207 (check_reachability — BFS over
  //      choice.goto only, cond/weight ignored, edges to existing nodes
  //      only; a missing start yields every ending unreachable, graceful).
  // -------------------------------------------------------------------------

  function bfs(nodes, start) {
    var report = {
      start: (start === undefined) ? null : start,
      reachable: {},
      order: [],
      endings: [],
      reachableEndings: [],
      unreachableEndings: []
    };
    var nid;
    for (nid in nodes) {
      if (Object.prototype.hasOwnProperty.call(nodes, nid) &&
          isEnding(nodes[nid])) {
        report.endings.push(nid);
      }
    }
    if (report.start === null || !Object.prototype.hasOwnProperty.call(nodes, report.start)) {
      // Graceful (rpg/story/validate.py:187-189): a missing start leaves
      // every ending orphaned — the checker reports, it never crashes.
      report.unreachableEndings = report.endings.slice();
      return report;
    }
    var queue = [report.start];
    report.reachable[report.start] = true;
    while (queue.length) {
      var cur = queue.shift();
      report.order.push(cur);
      var node = nodes[cur];
      var choices = asArray(node ? node.choices : null);
      for (var i = 0; i < choices.length; i++) {
        var gotoTarget = getGoto(choices[i]);
        // PARITY: choice.goto edges ONLY. cond/weight are IGNORED here
        // exactly as rpg/story/validate.py:198-202 ignores them; the
        // dormant on_enter_divert is NEVER followed (a JS BFS that
        // followed conds or diverts would disagree with the Python gate
        // -> false green/red, RESEARCH-SAFETY Pitfall S4).
        if (gotoTarget !== null && gotoTarget !== undefined &&
            Object.prototype.hasOwnProperty.call(nodes, gotoTarget) &&
            !report.reachable[gotoTarget]) {
          report.reachable[gotoTarget] = true;
          queue.push(gotoTarget);
        }
      }
    }
    for (var e = 0; e < report.endings.length; e++) {
      var ending = report.endings[e];
      if (report.reachable[ending]) {
        report.reachableEndings.push(ending);
      } else {
        report.unreachableEndings.push(ending);
      }
    }
    return report;
  }

  // Public BFS parity surface (the plan names bfsReachable(bundle)):
  // follows choice.goto edges ONLY, cond/weight ignored, on_enter_divert
  // never followed, start = manifest.start.
  EDITOR.bfsReachable = function (bundle) {
    var nodes = flattenNodes(bundle);
    var start = (bundle && bundle.manifest && bundle.manifest.start !== undefined)
      ? bundle.manifest.start : null;
    return bfs(nodes, start);
  };

  // =========================================================================
  // THE RULE CATALOG — one function per rule id (the JS port's contract,
  // mirroring tools/story_editor_lint.py rule-for-rule). Each appends to
  // the errors/notices lists; errors gate the save, notices never do.
  // =========================================================================

  // dangling_divert: a choice.goto pointing at a nonexistent node.
  // Exact parity with rpg validate_graph (every choice, goto non-null and
  // not in nodes). src: rpg/story/validate.py:214-235 (validate_graph).
  function ruleDanglingDivert(nodes, errors) {
    for (var nid in nodes) {
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
      var choices = asArray(nodes[nid] ? nodes[nid].choices : null);
      for (var i = 0; i < choices.length; i++) {
        var gotoTarget = getGoto(choices[i]);
        if (gotoTarget !== null && gotoTarget !== undefined &&
            !Object.prototype.hasOwnProperty.call(nodes, gotoTarget)) {
          errors.push(issue(
            "dangling_divert", nid,
            "choice -> " + gotoTarget,
            "rpg/story/validate.py:214-235"));
        }
      }
    }
  }

  // unreachable_ending: an ending orphaned from the start node (the
  // reachability report must be is_ok). Exact parity with rpg
  // check_reachability — the BFS follows goto edges ONLY.
  // src: rpg/story/validate.py:167-207 (check_reachability — BFS over
  //      choice.goto only, cond/weight ignored).
  function ruleUnreachableEnding(nodes, start, errors) {
    var report = bfs(nodes, start);
    for (var i = 0; i < report.unreachableEndings.length; i++) {
      var endingId = report.unreachableEndings[i];
      errors.push(issue(
        "unreachable_ending", endingId,
        "ending not reachable from '" + (start === null ? "(missing)" : start) +
        "' via choice.goto chains (BFS ignores cond/weight; router-only " +
        "entries are exempt by being non-endings)",
        "rpg/story/validate.py:167-207"));
    }
  }

  // router_only_incoming: any choice.goto INTO a router-only restored node
  // (their entry is engine.apply_player_edit — zero incoming edges is
  // load-bearing). A deleted restored node surfaces as dangling_edit_branch
  // instead (the edits.json branch_node check), so a missing id is skipped
  // here exactly as the lint does. src: tests/test_glucose_reachability.py
  // :326-452 (test_restoration_nodes_reachable_non_ending, router-only).
  function ruleRouterOnlyIncoming(nodes, errors) {
    for (var r = 0; r < ROUTER_ONLY_NODES.length; r++) {
      var restoredId = ROUTER_ONLY_NODES[r];
      if (!Object.prototype.hasOwnProperty.call(nodes, restoredId)) {
        continue; // a deleted restored node surfaces as dangling_edit_branch
      }
      for (var nid in nodes) {
        if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
        var choices = asArray(nodes[nid] ? nodes[nid].choices : null);
        for (var i = 0; i < choices.length; i++) {
          var c = choices[i];
          if (c && typeof c === "object" && c.goto === restoredId) {
            errors.push(issue(
              "router_only_incoming", nid,
              "choice '" + (c.label === undefined ? "None" : c.label) +
              "' -> '" + restoredId + "': restored nodes are ROUTER-ONLY " +
              "(engine.apply_player_edit routes known edits directly; no " +
              "incoming choice.goto edge may exist)",
              "tests/test_glucose_reachability.py:326-452"));
          }
        }
      }
    }
  }

  // single_continue: a node with exactly one choice labeled "Continue"
  // (a linear click-through; the Continue-to-MC invariant). Exact parity
  // with the owning test's predicate. src: tests/test_glucose_reachability
  // .py:245-262 (test_no_single_continue_choice).
  function ruleSingleContinue(nodes, errors) {
    for (var nid in nodes) {
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
      var choices = asArray(nodes[nid] ? nodes[nid].choices : null);
      if (choices.length === 1 && choices[0] &&
          choices[0].label === "Continue") {
        errors.push(issue(
          "single_continue", nid,
          "node has a single 'Continue' choice (the Continue-to-MC " +
          "invariant requires >=2 choices or an ending/stub shape)",
          "tests/test_glucose_reachability.py:245-262"));
      }
    }
  }

  // text_layer_empty + tbd_text: both text layers non-empty (after strip)
  // and no "TBD" residue in text/choice labels. The ONLY exempt node is
  // edit.prompt (its text_dramatic IS the [STRUCTURAL STUB: marker).
  // src: tests/test_glucose_content.py:126-184 (TestTwoLayerText).
  function ruleTwoLayerText(nodes, errors) {
    var fields = ["text_dramatic", "text_teaching"];
    for (var nid in nodes) {
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
      if (DOCUMENTED_STUB_NODES[nid]) continue;
      var node = nodes[nid];
      for (var f = 0; f < fields.length; f++) {
        var field = fields[f];
        var value = node ? node[field] : undefined;
        if (typeof value !== "string" || trimText(value) === "") {
          errors.push(issue(
            "text_layer_empty", nid,
            field + " is empty or blank (STORY-06 two-layer invariant; " +
            "edit.prompt is the only exempt node)",
            "tests/test_glucose_content.py:126-184"));
        } else if (value.indexOf("TBD") >= 0) {
          errors.push(issue(
            "tbd_text", nid,
            field + " contains 'TBD' residue (the bundle's only sanctioned " +
            "TBD is edit.prompt's stub marker)",
            "tests/test_glucose_content.py:126-184"));
        }
      }
      var choices = asArray(node ? node.choices : null);
      for (var i = 0; i < choices.length; i++) {
        var label = (choices[i] && typeof choices[i] === "object" &&
                     choices[i].label) ? choices[i].label : "";
        if (String(label).indexOf("TBD") >= 0) {
          errors.push(issue(
            "tbd_text", nid,
            "choice label '" + label + "' contains 'TBD' residue",
            "tests/test_glucose_content.py:126-184"));
        }
      }
    }
  }

  // Human-readable provenance suffix for a claim issue (context only —
  // sources.json is never gated). Port of the lint's _source_context
  // (tools/story_editor_lint.py:360-377): source_id may be a string or a
  // list; each source renders "<sid> (<approval_status>)".
  function sourceContext(cid, citations, sources) {
    var record = hasOwn(citations, cid) ? citations[cid] : null;
    if (!record || typeof record !== "object") return "";
    var sourceIds = record.source_id;
    if (sourceIds === undefined || sourceIds === null) return "";
    if (Object.prototype.toString.call(sourceIds) !== "[object Array]") {
      sourceIds = [sourceIds];
    }
    var parts = [];
    for (var i = 0; i < sourceIds.length; i++) {
      var sid = sourceIds[i];
      var srec = (sources && hasOwn(sources, sid) &&
                  typeof sources[sid] === "object") ? sources[sid] : null;
      var status = srec ? srec.approval_status : "?";
      parts.push(sid + " (" + status + ")");
    }
    return " sources: " + parts.join(", ");
  }

  // claim_missing + claim_unapproved + placeholder_misuse + the
  // sanctioned_residual NOTICE. Citation-gate semantics: every story-
  // referenced claim_id must exist AND be approval_status == "approved"
  // STRICTLY — never a not-equal-pending shortcut (a rejected claim fails
  // identically to a pending one; rpg/citations.py:100-109 documents the
  // Pitfall 6 rationale) — EXCEPT the sanctioned residual: PLACEHOLDER_PHASE8
  // on exactly fa.stub/alc.stub (reported as a notice; anywhere else, or any
  // other PLACEHOLDER*, is a placeholder_misuse error, bidirectionally: a
  // sanctioned stub LOSING its reference is also an error).
  // src: tools/check_citations.py:44-95 (the gate);
  //      rpg/citations.py:100-109 (is_approved, strict);
  //      tests/test_glucose_content.py:187-257 (TestClaimHygiene);
  //      tests/test_glucose_content.py:213-236 (the residual scope).
  function ruleClaims(nodes, citations, sources, errors, notices) {
    var stubRefs = [];
    var nid;
    var i;
    for (nid in nodes) {
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
      var node = nodes[nid];
      var claimIds = asArray(node ? node.claim_ids : null);
      for (i = 0; i < claimIds.length; i++) {
        var cid = claimIds[i];
        if (typeof cid !== "string") {
          errors.push(issue(
            "claim_missing", nid,
            "non-string claim_id " + JSON.stringify(cid) +
            " (claim_ids must be strings)",
            "tests/test_glucose_content.py:187-257"));
          continue;
        }
        if (cid === PHASE8_CLAIM) {
          if (PHASE8_STUB_NODES.indexOf(nid) >= 0) {
            stubRefs.push(nid); // the sanctioned residual
          } else {
            errors.push(issue(
              "placeholder_misuse", nid,
              "'" + cid + "' is sanctioned ONLY on " +
              renderList(PHASE8_STUB_NODES) + " (the Phase-8 stub pair) -- " +
              "a new node may never use it",
              "tests/test_glucose_content.py:213-236"));
          }
          continue;
        }
        if (cid.indexOf("PLACEHOLDER") === 0) {
          errors.push(issue(
            "placeholder_misuse", nid,
            "'" + cid + "': no PLACEHOLDER* residue is allowed anywhere " +
            "except PLACEHOLDER_PHASE8 on " + renderList(PHASE8_STUB_NODES),
            "tests/test_glucose_content.py:213-236"));
          continue;
        }
        if (!hasOwn(citations, cid)) {
          errors.push(issue(
            "claim_missing", nid,
            "references claim_id '" + cid + "' -- not in the registry",
            "tools/check_citations.py:44-95"));
        } else {
          var record = citations[cid];
          var status = (record && typeof record === "object")
            ? record.approval_status : undefined;
          // THE STRICT COMPARISON (load-bearing, cited): approval_status
          // === "approved". A rejected claim fails identically to a
          // pending one (rpg/citations.py:100-109, Pitfall 6) — a
          // not-equal-pending shortcut would erroneously pass rejected
          // claims and is FORBIDDEN here.
          if (status !== "approved") {
            errors.push(issue(
              "claim_unapproved", nid,
              "references claim_id '" + cid + "' -- approval_status is " +
              JSON.stringify(status === undefined ? null : status) +
              ", not 'approved' (rejected fails identically to pending)" +
              sourceContext(cid, citations, sources),
              "tools/check_citations.py:44-95"));
          }
        }
      }
    }
    // The sanctioned residual must be EXACTLY the stub pair (no fewer —
    // a stub losing its reference breaks the gate's pinned 2-MISSING form).
    var sortedRefs = stubRefs.slice().sort();
    var sortedStubs = PHASE8_STUB_NODES.slice().sort();
    var exact = sortedRefs.length === sortedStubs.length;
    if (exact) {
      for (i = 0; i < sortedRefs.length; i++) {
        if (sortedRefs[i] !== sortedStubs[i]) { exact = false; break; }
      }
    }
    if (exact) {
      notices.push(issue(
        "sanctioned_residual", PHASE8_STUB_NODES.join(", "),
        "PLACEHOLDER_PHASE8 present on exactly the sanctioned Phase-8 " +
        "stubs (the citation gate's sanctioned residual: exit 1 = 2 " +
        "MISSING + 0 UNAPPROVED) -- reported as a notice, never an error",
        "tests/test_glucose_content.py:213-236", "notice"));
    } else {
      for (i = 0; i < PHASE8_STUB_NODES.length; i++) {
        var stub = PHASE8_STUB_NODES[i];
        var count = 0;
        for (var s = 0; s < stubRefs.length; s++) {
          if (stubRefs[s] === stub) count++;
        }
        if (count !== 1) {
          errors.push(issue(
            "placeholder_misuse", stub,
            "sanctioned stub must carry '" + PHASE8_CLAIM + "' exactly once " +
            "(the citation-gate residual is EXACTLY the stub pair); " +
            "found " + count,
            "tests/test_glucose_content.py:213-236"));
        }
      }
    }
  }

  // offer_without_tag: a node offering an edit (a choice tagged edit:offer
  // OR whose goto IS edit.prompt — the ChoicePanel's DUAL predicate) without
  // carrying an edit:enzyme:<id> tag. src: tests/test_glucose_reachability
  // .py:462-499 (test_edit_offer_nodes_carry_edit_enzyme_tag).
  function ruleEditOfferTag(nodes, errors) {
    for (var nid in nodes) {
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
      var node = nodes[nid];
      var choices = asArray(node ? node.choices : null);
      var offers = 0;
      for (var i = 0; i < choices.length; i++) {
        var c = choices[i];
        if (!c || typeof c !== "object") continue;
        var tags = asArray(c.tags);
        if (tags.indexOf("edit:offer") >= 0 || c.goto === "edit.prompt") {
          offers++;
        }
      }
      if (!offers) continue;
      var hasTag = false;
      var nodeTags = asArray(node ? node.tags : null);
      for (var t = 0; t < nodeTags.length; t++) {
        if (String(nodeTags[t]).indexOf("edit:enzyme:") === 0) {
          hasTag = true;
          break;
        }
      }
      if (!hasTag) {
        errors.push(issue(
          "offer_without_tag", nid,
          "node offers " + offers + " edit choice(s) but carries no " +
          "edit:enzyme:<id> tag (the controller's _current_enzyme_id() " +
          "would be None -> request_edit RuntimeError)",
          "tests/test_glucose_reachability.py:462-499"));
      }
    }
  }

  // Shared pool checker — port of rpg _check_pool
  // (rpg/edit_router.py:216-235): an EMPTY pool is the empty_bad_ending_pool
  // issue; a member not in the graph is dangling_pool_node; a member that
  // exists but is not an ending is pool_node_not_ending. NOTE the caller's
  // gating (below): the global pool is ALWAYS checked (emptiness is an
  // error there — it is the ultimate fallback); a per-enzyme pool is only
  // validated when non-empty (empty = legal fallback, never flagged).
  // src: rpg/edit_router.py:172-235 (validate_edits_table + _check_pool).
  function checkPool(pool, label, nodes, errors) {
    if (!pool || !pool.length) {
      errors.push(issue(
        "empty_bad_ending_pool", label,
        "the " + (label === "global" ? "global bad_ending_pool" : label +
          " bad_ending_pool") + " is empty (the ultimate fallback for any " +
        "enzyme without a per-enzyme override -- EditRoutingError at runtime)",
        "rpg/edit_router.py:172-235"));
      return;
    }
    for (var i = 0; i < pool.length; i++) {
      var nid = pool[i];
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) {
        errors.push(issue(
          "dangling_pool_node", nid,
          "pool " + label,
          "rpg/edit_router.py:172-235"));
      } else if (!isEnding(nodes[nid])) {
        errors.push(issue(
          "pool_node_not_ending", nid,
          "pool " + label,
          "rpg/edit_router.py:172-235"));
      }
    }
  }

  // dangling_edit_branch / dangling_pool_node / empty_bad_ending_pool /
  // pool_node_not_ending / duplicate_signature (+ the per-enzyme-empty-pool
  // info notice). Exact parity with rpg validate_edits_table: the GLOBAL
  // pool is always checked (empty global = error); a per-enzyme pool is
  // checked ONLY when non-empty — an absent/empty per-enzyme pool means
  // "fall back to the global pool" (OVERRIDE semantics) and is NEVER an
  // error (the plan-mandated info notice reports it, keyed
  // per_enzyme_pool_empty). Signatures dedup on the NORMALIZED form (see
  // normalizeSignature above). src: rpg/edit_router.py:172-235
  // (validate_edits_table, per-enzyme fallback semantics at :193-199).
  function ruleEditsTable(edits, nodes, errors, notices) {
    var enzymes = (edits && typeof edits === "object" &&
                   edits.enzymes && typeof edits.enzymes === "object")
      ? edits.enzymes : {};
    var gpool = (edits && typeof edits === "object" &&
                 Object.prototype.toString.call(edits.bad_ending_pool) ===
                 "[object Array]") ? edits.bad_ending_pool : [];
    checkPool(gpool, "global", nodes, errors);
    var fallbackBuckets = [];
    var bucketCount = 0;
    for (var eid in enzymes) {
      if (!Object.prototype.hasOwnProperty.call(enzymes, eid)) continue;
      var enzyme = enzymes[eid];
      if (!enzyme || typeof enzyme !== "object") continue;
      bucketCount++;
      var perPool = enzyme.bad_ending_pool;
      if (perPool) {
        // Non-empty per-enzyme override -> validate its nodes.
        checkPool(asArray(perPool), eid, nodes, errors);
      } else {
        // Legal fallback (absent or empty per-enzyme pool) — info only.
        fallbackBuckets.push(eid);
      }
      var seen = {};
      var editsList = asArray(enzyme.edits);
      for (var i = 0; i < editsList.length; i++) {
        var entry = editsList[i];
        if (!entry || typeof entry !== "object") continue;
        var bn = entry.branch_node;
        if (bn !== undefined && bn !== null &&
            !Object.prototype.hasOwnProperty.call(nodes, bn)) {
          errors.push(issue(
            "dangling_edit_branch", bn,
            "enzyme " + eid + " branch_node",
            "rpg/edit_router.py:172-235"));
        }
        var sig = normalizeSignature(entry.signature);
        if (hasOwn(seen, sig)) {
          errors.push(issue(
            "duplicate_signature", eid,
            "signature " + sig,
            "rpg/edit_router.py:172-235"));
        }
        seen[sig] = true;
      }
    }
    if (fallbackBuckets.length) {
      notices.push(issue(
        "per_enzyme_pool_empty", "edits.json",
        fallbackBuckets.length + " of " + bucketCount + " enzyme bucket(s) " +
        "carry no per-enzyme bad_ending_pool and fall back to the global " +
        "pool (legal fallback semantics -- a per-enzyme empty pool is " +
        "NEVER an error; only the GLOBAL pool may raise " +
        "empty_bad_ending_pool): " + renderList(sortedKeysSet(fallbackBuckets)),
        "rpg/edit_router.py:193-199", "notice"));
    }
  }

  function sortedKeysSet(arr) {
    var set = {};
    for (var i = 0; i < arr.length; i++) set[arr[i]] = true;
    return sortedKeys(set);
  }

  // coverage_uncovered: a cast enzyme with no edits.json bucket (or an
  // empty edits list). Exact parity with rpg scan_edit_coverage.
  // src: rpg/edit_router.py:238-255 (scan_edit_coverage);
  //      tools/check_edit_coverage.py:65-126 (the CLI gate).
  function ruleCoverage(edits, castIds, errors) {
    var enzymes = (edits && typeof edits === "object" &&
                   edits.enzymes && typeof edits.enzymes === "object")
      ? edits.enzymes : {};
    for (var i = 0; i < castIds.length; i++) {
      var eid = castIds[i];
      var e = hasOwn(enzymes, eid) ? enzymes[eid] : null;
      var editCount = e ? asArray(e.edits).length : 0;
      if (e === null || editCount === 0) {
        errors.push(issue(
          "coverage_uncovered", eid,
          "cast enzyme has no edits.json bucket (or 0 edits) -- every " +
          "cast id needs >=1 known-edit entry (check_edit_coverage " +
          "semantics)",
          "rpg/edit_router.py:238-255"));
      }
    }
  }

  // relationship_pin: the shared-manifest invariant cast(ids) subset-of
  // edits(ids) AND edits(ids) == distinct edit:enzyme: tag values minus
  // {tca.citrate_synthase}. CS is edit:structural (tag, no bucket by
  // design). src: tests/test_glucose_content.py:404-449
  // (TestManifestRelationships).
  function ruleRelationshipPin(nodes, editsIds, castIds, errors) {
    var tagValues = {};
    for (var nid in nodes) {
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
      var tags = asArray(nodes[nid] ? nodes[nid].tags : null);
      for (var t = 0; t < tags.length; t++) {
        var tag = String(tags[t]);
        if (tag.indexOf("edit:enzyme:") === 0) {
          tagValues[tag.slice(12)] = true;
        }
      }
    }
    var expected = {};
    for (var k in tagValues) {
      if (Object.prototype.hasOwnProperty.call(tagValues, k) &&
          k !== STRUCTURAL_TAG_ENZYME) {
        expected[k] = true;
      }
    }
    var editsSet = {};
    for (var e = 0; e < editsIds.length; e++) editsSet[editsIds[e]] = true;
    var extra = setDifference(editsSet, expected);
    var missing = setDifference(expected, editsSet);
    if (extra.length || missing.length) {
      errors.push(issue(
        "relationship_pin", "edits.json <-> graph tags",
        "edits(" + editsIds.length + ") != edit:enzyme tag values(" +
        sortedKeys(tagValues).length + ") - " + STRUCTURAL_TAG_ENZYME +
        "; bucket(s) with no tag carrier: " + renderList(extra) +
        "; tag value(s) with no bucket: " + renderList(missing),
        "tests/test_glucose_content.py:404-449"));
    }
    var castSet = {};
    for (var c = 0; c < castIds.length; c++) castSet[castIds[c]] = true;
    var uncovered = setDifference(castSet, editsSet);
    if (uncovered.length) {
      errors.push(issue(
        "relationship_pin", "cast.json -> edits.json",
        "cast(" + castIds.length + ") is not a subset of edits(" +
        editsIds.length + "): cast id(s) with no edits.json bucket: " +
        renderList(uncovered),
        "tests/test_glucose_content.py:404-449"));
    }
  }

  // weight_outside_shuffle: a weighted choice on any node other than
  // tca.shuffle (the graph's ONLY weighted node — the whole seeded-RNG
  // surface). src: tests/test_glucose_content.py:539-557
  // (test_shuffle_is_the_only_weighted_node).
  function ruleWeightOutsideShuffle(nodes, errors) {
    for (var nid in nodes) {
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
      if (nid === SHUFFLE_NODE) continue;
      var choices = asArray(nodes[nid] ? nodes[nid].choices : null);
      for (var i = 0; i < choices.length; i++) {
        var c = choices[i];
        if (c && typeof c === "object" && c.weight !== undefined &&
            c.weight !== null) {
          errors.push(issue(
            "weight_outside_shuffle", nid,
            "choice '" + (c.label === undefined ? "None" : c.label) +
            "' carries weight " + JSON.stringify(c.weight) +
            " -- only tca.shuffle may carry weights (the single seeded-RNG " +
            "surface; a new weighted node is a design-B contract change)",
            "tests/test_glucose_content.py:539-557"));
        }
      }
    }
  }

  // cond_attribute_form: a choice cond using the broken dict-ATTRIBUTE
  // form (flags.x / visits.x / counters.x) instead of the mandatory
  // dict-METHOD form (flags.get('x')). Attribute access raises
  // AttributeError inside _cond, is caught, and silently hides the choice
  // -> potentially stuck. src: tests/test_glucose_reachability.py:716-752
  // (test_no_broken_dict_attribute_conds_remain);
  // rpg/story/interpreter.py:101-131 (the _cond namespace).
  function ruleCondAttributeForm(nodes, errors) {
    for (var nid in nodes) {
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
      var choices = asArray(nodes[nid] ? nodes[nid].choices : null);
      for (var i = 0; i < choices.length; i++) {
        var c = choices[i];
        if (!c || typeof c !== "object") continue;
        var cond = c.cond;
        if (cond === undefined || cond === null) continue;
        var match = BROKEN_COND_RE.exec(String(cond));
        if (match) {
          errors.push(issue(
            "cond_attribute_form", nid,
            "choice '" + (c.label === undefined ? "None" : c.label) +
            "' cond '" + cond + "' uses the broken dict-attribute form '" +
            match[0] + "' -- use the dict-METHOD form " +
            "flags.get('...')/visits.get('...', 0)",
            "tests/test_glucose_reachability.py:716-752"));
        }
      }
    }
  }

  // hero-highlight ordered-subsequence drift check (plan 07.1-08 addition,
  // WARNING/notice severity — the Python lint has no rule here, so this
  // never gates a save): intro.preface's on_enter must contain the 6-call
  // hero-highlight sequence from 05.4-CONVENTION.md section 3.3
  // (set_color hero_cyan + show_as sticks + color hero_cyan on elem C +
  // show spheres + set sphere_scale 0.3 + label YOU), IN ORDER, AFTER the
  // hero_atom load — an ordered SUBSEQUENCE walk exactly like the owning
  // test. src: tests/test_glucose_reachability.py:800-843
  // (test_preface_on_enter_has_hero_highlight_sequence).
  function heroHighlightCheck(nodes, notices) {
    var node = hasOwn(nodes, "intro.preface") ? nodes["intro.preface"] : null;
    if (!node || typeof node !== "object") return;
    var onEnter = asArray(node.on_enter);
    var heroLoadIdx = -1;
    for (var i = 0; i < onEnter.length; i++) {
      var m = onEnter[i];
      if (m && typeof m === "object" && m.op === "load" && m.args &&
          m.args.object === "hero_atom") {
        heroLoadIdx = i;
        break;
      }
    }
    if (heroLoadIdx < 0) {
      notices.push(issue(
        "hero_highlight_sequence", "intro.preface",
        "on_enter loads no hero_atom before the highlight (the SC2 " +
        "6-call hero-highlight sequence must follow the hero_atom load)",
        "tests/test_glucose_reachability.py:800-843", "notice"));
      return;
    }
    var seq = [
      ["set_color", function (a) { return a && a.name === "hero_cyan"; }],
      ["show_as", function (a) { return a && a.rep === "sticks"; }],
      ["color", function (a) { return a && a.color === "hero_cyan"; }],
      ["show", function (a) { return a && a.rep === "spheres"; }],
      ["set", function (a) { return a && a.name === "sphere_scale"; }],
      ["label", function (a) { return a && a.text === "YOU"; }]
    ];
    var idx = heroLoadIdx + 1;
    var missing = [];
    for (var s = 0; s < seq.length; s++) {
      var opName = seq[s][0];
      var pred = seq[s][1];
      var found = false;
      while (idx < onEnter.length) {
        var action = onEnter[idx];
        idx++;
        if (action && typeof action === "object" && action.op === opName &&
            pred(action.args)) {
          found = true;
          break;
        }
      }
      if (!found) missing.push(opName);
    }
    if (missing.length) {
      notices.push(issue(
        "hero_highlight_sequence", "intro.preface",
        "on_enter hero-highlight ordered subsequence missing op(s) " +
        renderList(missing) + " after the hero_atom load (the SC2 6-call " +
        "sequence: set_color hero_cyan -> show_as sticks -> color " +
        "hero_cyan -> show spheres -> set sphere_scale 0.3 -> label YOU, " +
        "IN ORDER)",
        "tests/test_glucose_reachability.py:800-843", "notice"));
    }
  }

  // start_node_pdb_load: a start node's on_enter loading a "pdb:" target
  // (start nodes use bundled placeholders ONLY — no network fetch at game
  // start). The start set = the manifest start + the intro.* prefix (the
  // owning test pins intro.preface/intro.shell_glucose/intro.select — all
  // intro.*). Plus the plan-mandated hero-highlight ordered-subsequence
  // WARNING (heroHighlightCheck above). src: tests/test_glucose_reachability
  // .py:868-885 (test_start_nodes_do_not_reference_real_pdb_fetch).
  function ruleStartNodePdbLoad(bundle, nodes, errors, notices) {
    var start = (bundle && bundle.manifest && bundle.manifest.start !== undefined)
      ? bundle.manifest.start : null;
    var startIds = {};
    if (start !== null && start !== undefined) startIds[start] = true;
    for (var nid in nodes) {
      if (Object.prototype.hasOwnProperty.call(nodes, nid) &&
          nid.indexOf(START_NODE_PREFIX) === 0) {
        startIds[nid] = true;
      }
    }
    var keys = sortedKeys(startIds);
    for (var i = 0; i < keys.length; i++) {
      var sid = keys[i];
      var node = hasOwn(nodes, sid) ? nodes[sid] : null;
      if (!node || typeof node !== "object") continue;
      var actions = asArray(node.on_enter);
      for (var a = 0; a < actions.length; a++) {
        var action = actions[a];
        if (!action || typeof action !== "object" || action.op !== "load") {
          continue;
        }
        var target = action.target;
        if (typeof target === "string" && target.indexOf("pdb:") === 0) {
          errors.push(issue(
            "start_node_pdb_load", sid,
            "start node on_enter loads '" + target + "' -- start nodes use " +
            "bundled placeholders only (an instant-start game must not " +
            "network-fetch at game start)",
            "tests/test_glucose_reachability.py:868-885"));
        }
      }
    }
    heroHighlightCheck(nodes, notices);
  }

  // unknown_op + the set_view_phase10 NOTICE: every on_enter op must be in
  // the frozen molops dispatch vocabulary (a stray op raises
  // NotImplementedError at dispatch); set_view is NOT dispatchable this
  // phase but is accepted with a visible NOTICE (the scene_capture
  // Phase-10 precedent), never an error.
  // src: rpg/pymol_layer/molops.py:140-291 (the dispatch vocabulary;
  //      unknown op -> raise at :286-291); tools/scene_capture.py (the
  //      Phase-10 set_view WARNING precedent).
  function ruleOnEnterOps(nodes, errors, notices) {
    for (var nid in nodes) {
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
      var actions = asArray(nodes[nid] ? nodes[nid].on_enter : null);
      for (var i = 0; i < actions.length; i++) {
        var action = actions[i];
        var op = (action && typeof action === "object") ? action.op : undefined;
        if (op !== undefined && op !== null && hasOwn(PHASE10_OPS, op)) {
          notices.push(issue(
            "set_view_phase10", nid,
            "op '" + op + "' is Phase-10-flagged (camera ops land in " +
            "Phase 10) -- accepted with this visible notice, per the " +
            "scene_capture.py precedent",
            "rpg/pymol_layer/molops.py:286-291", "notice"));
        } else if (op === undefined || op === null || !hasOwn(OP_VOCABULARY, op)) {
          errors.push(issue(
            "unknown_op", nid,
            "on_enter op " + JSON.stringify(op === undefined ? null : op) +
            " is outside the frozen molops vocabulary " +
            renderList(OP_VOCABULARY_SORTED) + " -- it would raise " +
            "NotImplementedError at dispatch",
            "rpg/pymol_layer/molops.py:140-291"));
        }
      }
    }
  }

  function copyTiers(tierCounts) {
    var out = {};
    for (var t in tierCounts) {
      if (Object.prototype.hasOwnProperty.call(tierCounts, t)) {
        out[t] = tierCounts[t];
      }
    }
    return out;
  }

  function tiersEqual(a, b) {
    var ka = sortedKeys(a);
    var kb = sortedKeys(b);
    if (ka.length !== kb.length) return false;
    for (var i = 0; i < ka.length; i++) {
      if (ka[i] !== kb[i] || a[ka[i]] !== b[kb[i]]) return false;
    }
    return true;
  }

  function formatTiers(tierCounts) {
    // Deterministic tier-count rendering: {true: N, good: N, normal: N,
    // bad: N} (unknown tiers appended sorted) — the lint's _format_tiers.
    var parts = [];
    for (var i = 0; i < PINNED_TIER_ORDER.length; i++) {
      var t = PINNED_TIER_ORDER[i];
      parts.push(t + ": " + (hasOwn(tierCounts, t) ? tierCounts[t] : 0));
    }
    var unknown = sortedKeys(tierCounts);
    for (var u = 0; u < unknown.length; u++) {
      if (PINNED_TIER_ORDER.indexOf(unknown[u]) < 0) {
        parts.push(unknown[u] + ": " + tierCounts[unknown[u]]);
      }
    }
    return "{" + parts.join(", ") + "}";
  }

  function countShiftsShell() {
    return {
      changed: false,
      nodes: { old: PINNED_NODE_COUNT, new: PINNED_NODE_COUNT },
      tiers: {
        old: copyTiers(PINNED_TIER_COUNTS),
        new: copyTiers(PINNED_TIER_COUNTS),
        changed: false
      },
      editAllowed: {
        old: PINNED_EDIT_ALLOWED.slice().sort(),
        new: PINNED_EDIT_ALLOWED.slice().sort(),
        added: [],
        removed: [],
        changed: false
      },
      pinnedTests: COUNT_SHIFT_TESTS.slice(),
      viewerConstants: COUNT_SHIFT_CONSTANTS.slice()
    };
  }

  // count_shift NOTICE (never an error): compare the live counts against
  // the pinned trio — nodes / endings by tier / edit-allowed ids — and
  // report old->new, naming the pinned tests + the viewer's pinned
  // constants as the SAME-COMMIT update obligations. This is the
  // acknowledgment path (RESEARCH-SAFETY key finding 1 / Pitfall S2):
  // pinned-count movement is an explicit event, not a silent pass and not
  // a hard error. src: tests/test_glucose_reachability.py:136-155
  // (test_manifest_loads_all_57_nodes), :157-189
  // (test_reachability_green_all_four_tiers), :264-324
  // (test_15_edit_allowed_nodes); tools/story_graph_viewer.py:96-105
  // (EXPECTED_NODES / EXPECTED_TIER_COUNTS / EXPECTED_EDIT_ALLOWED).
  function ruleCountShift(nodes, notices, countShifts) {
    var moved = [];
    var liveNodes = 0;
    var nid;
    for (nid in nodes) {
      if (Object.prototype.hasOwnProperty.call(nodes, nid)) liveNodes++;
    }
    countShifts.nodes.new = liveNodes;
    if (liveNodes !== PINNED_NODE_COUNT) {
      moved.push("nodes " + PINNED_NODE_COUNT + " -> " + liveNodes);
    }

    var liveTiers = {};
    for (nid in nodes) {
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
      var tier = nodes[nid] ? nodes[nid].is_ending : undefined;
      if (tier !== undefined && tier !== null) {
        liveTiers[tier] = (hasOwn(liveTiers, tier) ? liveTiers[tier] : 0) + 1;
      }
    }
    countShifts.tiers.new = copyTiers(liveTiers);
    countShifts.tiers.changed = !tiersEqual(liveTiers, PINNED_TIER_COUNTS);
    if (countShifts.tiers.changed) {
      moved.push("endings by tier " + formatTiers(PINNED_TIER_COUNTS) +
        " -> " + formatTiers(liveTiers));
    }

    var liveEditSet = {};
    for (nid in nodes) {
      if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
      var tags = asArray(nodes[nid] ? nodes[nid].tags : null);
      for (var t = 0; t < tags.length; t++) {
        if (String(tags[t]).indexOf("edit:enzyme:") === 0) {
          liveEditSet[nid] = true;
          break;
        }
      }
    }
    var liveEditAllowed = sortedKeys(liveEditSet);
    var pinnedEditSet = {};
    for (var p = 0; p < PINNED_EDIT_ALLOWED.length; p++) {
      pinnedEditSet[PINNED_EDIT_ALLOWED[p]] = true;
    }
    var added = setDifference(liveEditSet, pinnedEditSet);
    var removed = setDifference(pinnedEditSet, liveEditSet);
    countShifts.editAllowed.new = liveEditAllowed;
    countShifts.editAllowed.added = added;
    countShifts.editAllowed.removed = removed;
    countShifts.editAllowed.changed =
      (added.length > 0) || (removed.length > 0);
    if (countShifts.editAllowed.changed) {
      moved.push("edit-allowed nodes " + PINNED_EDIT_ALLOWED.length + " -> " +
        liveEditAllowed.length + " (added " + renderList(added) +
        "; removed " + renderList(removed) + ")");
    }

    countShifts.changed = moved.length > 0;
    if (!moved.length) return;
    notices.push(issue(
      "count_shift", "bundle counts",
      moved.join("; ") +
      " -- SAME-COMMIT update obligations: " + COUNT_SHIFT_TESTS.join(", ") +
      " + the viewer's pinned constants " +
      COUNT_SHIFT_CONSTANTS.join(" / ") +
      " (tools/story_graph_viewer.py:96-105). The pinned tests will fail " +
      "until their counts are updated in the same change -- that failure " +
      "is the designed signal.",
      "tests/test_glucose_reachability.py:136,157,264 + " +
      "tools/story_graph_viewer.py:96-105", "notice"));
  }

  // =========================================================================
  // Orchestration — the run_lint port (tools/story_editor_lint.py:820-861):
  // every rule runs in the SAME order; errors gate (exit 1), notices never
  // do (exit 0 with notices is green — the sanctioned residual IS a notice).
  // =========================================================================

  EDITOR.validate = function (bundle) {
    var countShifts = countShiftsShell();
    var result = {
      errors: [],
      notices: [],
      countShifts: countShifts,
      blocked: false,
      ran: false
    };
    if (!bundle || !bundle.files) return result;
    result.ran = true;

    var nodes = flattenNodes(bundle);
    var manifest = (bundle.manifest && typeof bundle.manifest === "object")
      ? bundle.manifest : {};
    var start = (manifest.start !== undefined) ? manifest.start : null;
    var citations = (bundle.citations && typeof bundle.citations === "object")
      ? bundle.citations : {};
    var sources = (bundle.sources && typeof bundle.sources === "object")
      ? bundle.sources : {};
    var edits = (bundle.edits && typeof bundle.edits === "object")
      ? bundle.edits : {};
    var castIds = castIdList(bundle);
    var editsIds = (edits.enzymes && typeof edits.enzymes === "object")
      ? Object.keys(edits.enzymes) : [];

    // Same rule order as the lint's run_lint (tools/story_editor_lint.py
    // :837-853) — deterministic output, rule-for-rule.
    ruleDanglingDivert(nodes, result.errors);
    ruleUnreachableEnding(nodes, start, result.errors);
    ruleRouterOnlyIncoming(nodes, result.errors);
    ruleSingleContinue(nodes, result.errors);
    ruleTwoLayerText(nodes, result.errors);
    ruleClaims(nodes, citations, sources, result.errors, result.notices);
    ruleEditOfferTag(nodes, result.errors);
    ruleEditsTable(edits, nodes, result.errors, result.notices);
    ruleCoverage(edits, castIds, result.errors);
    ruleRelationshipPin(nodes, editsIds, castIds, result.errors);
    ruleWeightOutsideShuffle(nodes, result.errors);
    ruleCondAttributeForm(nodes, result.errors);
    ruleStartNodePdbLoad(bundle, nodes, result.errors, result.notices);
    ruleOnEnterOps(nodes, result.errors, result.notices);
    ruleCountShift(nodes, result.notices, result.countShifts);

    result.blocked = result.errors.length > 0;
    return result;
  };

  // Validate the LIVE bundle (the hook + the save panel's entry point).
  // The result is cached in EDITOR._lastValidation for any consumer that
  // wants the last verdict without re-running (07.1-13 save panel).
  EDITOR.validateCurrent = function () {
    var b = EDITOR.state.bundle;
    if (!b) {
      EDITOR._lastValidation = null;
      return null;
    }
    var result = EDITOR.validate(b);
    EDITOR._lastValidation = result;
    return result;
  };

  // The gating API (07.1-13's save panel refuses while true): ALWAYS
  // fresh — the live bundle is re-validated on every call, so a verdict is
  // never stale even if a hook dispatch was missed.
  EDITOR.saveBlocked = function () {
    if (!EDITOR.state.bundle) return false;
    var result = EDITOR.validateCurrent();
    return !!(result && result.blocked);
  };

  // -------------------------------------------------------------------------
  // Hook registration (added via init; 00_core iterates hooks defensively
  // in its own try/catch per hook — one broken validate hook never kills
  // the state layer). After EVERY mutation (EDITOR.apply -> afterChange)
  // the full validation re-runs on the live bundle and the verdict is
  // cached for EDITOR.saveBlocked() / the 07.1-13 save panel.
  // -------------------------------------------------------------------------

  EDITOR.init(function () {
    EDITOR.hooks.validate.push(function () {
      EDITOR.validateCurrent();
    });
  });

})();
