/* ==========================================================================
 * 42_choices.js — the choices editor: B3 (choice contents CRUD) + B5
 * (connection + direction editing) (07.1-15).
 *
 * OWNERSHIP: this asset belongs to plan 07.1-15 (Wave 4b). It fills the
 * FIXED shell mount #node-form-choices and NEVER edits another asset's
 * file (00_core.js = 07.1-04, 40_form.js = 07.1-09 owns the sibling
 * #node-form-identity section, 43_onenter.js = 07.1-16, 45_lifecycle.js).
 *
 * WHAT THIS EDITS (07.1-RESEARCH-DATA §1.6 choice schema — verified
 * inventory over the live bundle's 95 choices):
 *     { label, goto, cond?, weight?, effects?, tags? }
 *   (Choice.from_dict, rpg/story/model.py:193-204; label/goto present
 *   95/95, tags 62/95, effects key 4 (one non-empty:
 *   {"set": {"anaerobic": true}}), weight 2 (tca.shuffle 0.5/0.5),
 *   cond 1 (tca.shuffle cycle trap, visits.get('tca.shuffle', 0) > 5).)
 *
 * B5 = CONNECTION + DIRECTION EDITOR: choices ARE the graph's edges. The
 * goto dropdown (every node id, grouped by file in manifest order) is the
 * unambiguous, keyboard-accessible connection editor; edge direction is
 * INHERENT (src = the parent node, dst = the selected goto). Click-source-
 * click-target canvas wiring is explicitly NOT needed (07.1-RESEARCH-UI
 * "Graph editing UX"). An empty goto renders/commits as the "(none —
 * invalid)" option BY DESIGN: an empty string target is not a node id, so
 * the validator's dangling_divert rule fires and the dangling state is
 * VISIBLE, never silently dropped.
 *
 * RUNTIME LANDMINES GUARDED HERE (the plan's mandate):
 *   1. cond — a restricted-namespace Python expression evaluated against
 *      {flags, char, counters, visits} with NO builtins; ANY exception is
 *      caught and the choice is SILENTLY HIDDEN at runtime
 *      (rpg/story/interpreter.py:101-135, cited via 07.1-RESEARCH-DATA
 *      §1.6). The dict-ATTRIBUTE form (flags.x) raises AttributeError ->
 *      hidden -> stuck: the Phase-6 SC#3 bug class. The DICT-METHOD form
 *      (flags.get('x') / visits.get('x', 0)) is mandatory. The cond field
 *      therefore always shows the dict-method warning, and a client-side
 *      regex check (same pattern as 20_validate.js's BROKEN_COND_RE, the
 *      JS port of the reachability scan
 *      tests/test_glucose_reachability.py:716-752) surfaces the
 *      cond_attribute_form violation on the row live.
 *   2. weight — a weighted choice makes the node RNG-decided via the
 *      single RngEngine (interpreter.py:43-73). tca.shuffle is the ONLY
 *      weighted node in the graph, pinned verbatim by
 *      tests/test_glucose_content.py:539-557 — the determinism pin. The
 *      weight inputs are therefore LOCKED (a lock note instead) unless the
 *      node carries the rng:weighted tag or one of its choices already
 *      carries weight; a weight committed anywhere else surfaces the
 *      validator's weight_outside_shuffle error.
 *
 * VALIDATION: per-row error chips are mapped from EDITOR.validate (the
 * 20_validate.js rule-for-rule port, cached in EDITOR._lastValidation)
 * onto the row that owns them (dangling_divert by goto target,
 * router_only_incoming when the target is a restored node,
 * cond_attribute_form via the client-side regex, tbd_text on the label,
 * weight_outside_shuffle by label), plus live client-side checks that
 * work even before the next apply/validate cycle. The choice count vs the
 * zero-single-Continue rule (test_no_single_continue_choice,
 * tests/test_glucose_reachability.py:245-262 — >=2 choices or an
 * ending/stub shape) shows as a live hint, and delete-confirm warns
 * BEFORE a delete would leave <2 choices on a non-ending non-stub node.
 *
 * MUTATION DISCIPLINE (B11 unknown-key contract): every change flows
 * through the 00_core mutators (choiceAdd / choiceUpdate / choiceDelete)
 * or a local apply() mutator that touches ONLY the named field / only
 * reorders (choiceMove splices; removeChoiceField deletes one named key).
 * Nothing ever rebuilds a choice from a field whitelist, so unknown
 * choice keys round-trip untouched through every edit, undo/redo and
 * save. commit-on-change = ONE undo step per field commit (the
 * 00_core.textFieldBindings granularity, applied to choice fields);
 * `input` events are display-only (live row chips), never a bundle write.
 *
 * EVENTS: listeners are DELEGATED on the stable #node-form-choices mount
 * (one listener per concern; the section's innerHTML is rebuilt on every
 * rerender). Attributes are namespaced data-ch-* so the sibling form
 * asset's data-role / data-field delegation (40_form.js) and the core's
 * textFieldBindings never collide.
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

  // The cond landmine (see header): attribute-form detection, identical
  // pattern to 20_validate.js BROKEN_COND_RE (07.1-08's JS port of
  // test_no_broken_dict_attribute_conds_remain, reachability :716-752).
  var BROKEN_COND_RE =
    /(flags|visits|counters)\.[a-zA-Z_][a-zA-Z0-9_]*(?![a-zA-Z0-9_])(?!\()/;

  // The mandatory-form hint, verbatim fragments from the plan (the warning
  // shown under EVERY cond input).
  var COND_HINT = "dict-method form only: flags.get('x') / " +
    "visits.get('x', 0). The attribute form (flags.x) raises " +
    "AttributeError inside the interpreter and silently hides the " +
    "choice at runtime \u2014 the Phase-6 SC#3 bug class " +
    "(rpg/story/interpreter.py:101-135).";

  // The weight determinism pin (see header). Shown as a LOCK note whenever
  // the weight inputs are hidden.
  var WEIGHT_LOCK_NOTE = "Weight is locked: weighted choices exist only " +
    "on tca.shuffle (determinism pin \u2014 one seeded-RNG surface, " +
    "test_glucose_content.py:539-557).";

  // Defense-in-depth when weighting IS unlocked but the node is not
  // tca.shuffle (possible only mid-edit, e.g. after adding the rng:weighted
  // tag on another node): the commit still lands, the validator flags it.
  var WEIGHT_OUTSIDE_NOTE = "This node is NOT tca.shuffle \u2014 committing " +
    "a weight here fires the validator rule weight_outside_shuffle (the " +
    "graph's only weighted node is pinned by test_glucose_content.py:539-557).";

  // Router-only restored nodes: zero incoming choice.goto edges is
  // load-bearing (engine.apply_player_edit routes known edits directly).
  // Mirror of 20_validate.js ROUTER_ONLY_NODES.
  // src: tests/test_glucose_reachability.py:326-452
  var ROUTER_ONLY_IDS = ["gly.pfk_restored", "tca.aconitase_restored"];

  // The single seeded-RNG node (weight_outside_shuffle rule owner).
  var SHUFFLE_NODE = "tca.shuffle";

  // Choice-tag vocabulary (07.1-RESEARCH-DATA §1.5 "Choice tags", counts
  // verified against the committed data 2026-09-05). Shown as the
  // quick-add palette + a documented legend.
  var CHOICE_TAG_VOCAB = [
    { tag: "mc:observe", count: "19 choices" },
    { tag: "edit:offer", count: "15 choices" },
    { tag: "edit:unknown", count: "9 choices" },
    { tag: "edit:known", count: "3 choices" },
    { tag: "edit:known_critical", count: "1 choice" },
    { tag: "rng:weighted", count: "2 choices (tca.shuffle's 0.5/0.5 wheel)" },
    { tag: "branch:aerobic", count: "1 choice" },
    { tag: "branch:anaerobic", count: "1 choice" },
    { tag: "char:glucose", count: "1 choice" },
    { tag: "char:alc", count: "1 choice" },
    { tag: "char:fa", count: "1 choice" },
    { tag: "cycle_trap", count: "1 choice" },
    { tag: "divert:amino_acid", count: "1 choice" },
    { tag: "divert:fatty_acid", count: "1 choice" },
    { tag: "fermentation:lactic", count: "1 choice" },
    { tag: "fermentation:ethanolic", count: "1 choice" },
    { tag: "fermentation:crisis", count: "1 choice" },
    { tag: "etc:enter", count: "1 choice" },
    { tag: "ending:normal", count: "1 choice" },
    { tag: "stub", count: "2 choices (edit.prompt's stub edges)" }
  ];

  // Validator error kinds that map onto a single choice row (everything
  // else this node owns renders in the section-level list).
  var ROW_ERROR_KINDS = {
    dangling_divert: true,
    router_only_incoming: true,
    cond_attribute_form: true,
    tbd_text: true,
    weight_outside_shuffle: true
  };

  // -------------------------------------------------------------------------
  // Module state + tiny helpers.
  // -------------------------------------------------------------------------

  var refs = { section: null };

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

  function hasOwn(obj, key) {
    return Object.prototype.hasOwnProperty.call(obj, key);
  }

  function asArray(v) {
    return Object.prototype.toString.call(v) === "[object Array]" ? v : [];
  }

  function trimText(v) {
    return String(v == null ? "" : v).replace(/^\s+|\s+$/g, "");
  }

  // The selection this section edits: the form is selection-driven (the
  // whole #node-form aside shows EDITOR.state.sel), handlers run
  // synchronously between renders, so state is always the live truth.
  function selectedIds() {
    var nid = EDITOR.state.sel;
    if (!nid || !EDITOR.state.bundle) return null;
    var fname = EDITOR.fileOfNode(nid);
    if (!fname) return null;
    return { nid: nid, fname: fname };
  }

  function choiceAt(node, idx) {
    var choices = node ? asArray(node.choices) : [];
    var c = (idx >= 0 && idx < choices.length) ? choices[idx] : null;
    return (c && typeof c === "object") ? c : null;
  }

  function nodeHasTag(node, tag) {
    var tags = node ? asArray(node.tags) : [];
    for (var i = 0; i < tags.length; i++) {
      if (tags[i] === tag) return true;
    }
    return false;
  }

  function nodeExists(id) {
    return EDITOR.nodeById(id) !== null;
  }

  // First node id (manifest order via EDITOR.allNodes) that is NOT the
  // given node — the add-scaffold's default goto (a self-loop would be a
  // legal but useless default; "first other node" per the plan).
  function firstOtherNodeId(nid) {
    var all = EDITOR.allNodes();
    for (var i = 0; i < all.length; i++) {
      if (all[i].id !== nid) return all[i].id;
    }
    return null;
  }

  // Weight context gate: the weight inputs appear ONLY when the node
  // carries rng:weighted or any choice already carries weight (otherwise
  // the lock note renders — the determinism pin).
  function weightedContext(node) {
    if (nodeHasTag(node, "rng:weighted")) return true;
    var choices = asArray(node ? node.choices : null);
    for (var i = 0; i < choices.length; i++) {
      var c = choices[i];
      if (c && typeof c === "object" && c.weight !== undefined &&
          c.weight !== null) {
        return true;
      }
    }
    return false;
  }

  function findAncestor(el, attr) {
    var section = refs.section;
    var cur = el;
    while (cur && cur !== section) {
      if (cur.hasAttribute && cur.hasAttribute(attr)) return cur;
      cur = cur.parentNode;
    }
    return null;
  }

  // -------------------------------------------------------------------------
  // Mutators — ALL through EDITOR.apply (one undo step each, per-file
  // dirty, afterChange fan-out). B11: mutators touch ONLY the named field;
  // nothing rebuilds a choice from a whitelist, so unknown choice keys
  // round-trip untouched (the engine and the 5.4 conformance battery
  // consume this exact schema).
  // -------------------------------------------------------------------------

  // Reorder (up/down): splice-only — the order IS the player-facing
  // selection order for non-weighted nodes. No key is touched, no choice
  // is rebuilt.
  function choiceMove(fname, nid, from, to) {
    if (to < 0) return;
    EDITOR.apply({
      files: [fname],
      redo: function (b) {
        var file = (b && b.files && b.files[fname]) ? b.files[fname] : null;
        var node = (file && file.nodes) ? file.nodes[nid] : null;
        var choices = node ? asArray(node.choices) : null;
        if (!choices || from < 0 || from >= choices.length ||
            to >= choices.length) {
          return;
        }
        var moved = choices.splice(from, 1)[0];
        choices.splice(to, 0, moved);
      }
    });
  }

  // Key REMOVAL for the optional choice fields (cond / weight): the schema
  // keeps them ABSENT (never null) when unused — same shape rule as
  // is_ending (model.py:250-252 for the node-level precedent). B11-safe:
  // deletes ONLY the named key on the named choice.
  function removeChoiceField(fname, nid, idx, field) {
    EDITOR.apply({
      files: [fname],
      redo: function (b) {
        var file = (b && b.files && b.files[fname]) ? b.files[fname] : null;
        var node = (file && file.nodes) ? file.nodes[nid] : null;
        var c = choiceAt(node, idx);
        if (c) delete c[field];
      }
    });
  }

  // Commit-on-change dispatch for the per-choice field inputs (label /
  // goto / cond / weight). One commit = ONE apply = one undo step.
  function commitChoiceField(fname, nid, idx, field, raw) {
    var node = EDITOR.nodeGet(fname, nid);
    if (!choiceAt(node, idx)) return;
    if (field === "label" || field === "goto") {
      // goto "" = the "(none — invalid)" option: an empty target is not a
      // node id, so dangling_divert fires and the state stays VISIBLE.
      EDITOR.choiceUpdate(fname, nid, idx, field, String(raw == null ? "" : raw));
      return;
    }
    if (field === "cond") {
      var cond = trimText(raw);
      if (cond === "") {
        removeChoiceField(fname, nid, idx, "cond"); // optional: absent, never null
      } else {
        EDITOR.choiceUpdate(fname, nid, idx, "cond", cond);
      }
      return;
    }
    if (field === "weight") {
      var text = trimText(raw);
      if (text === "") {
        removeChoiceField(fname, nid, idx, "weight"); // optional: absent, never null
        return;
      }
      var n = Number(text);
      // Finite -> number (schema type float); nonsense stays a string so
      // the operator sees exactly what they typed and the gates judge it.
      EDITOR.choiceUpdate(fname, nid, idx, "weight", isFinite(n) ? n : text);
      return;
    }
  }

  // Add: appends {label: "New choice", goto: <first other node>} (plan
  // spec). A null target (single-node bundle) lands as "" — dangling and
  // visible, per the goto contract above.
  function addChoice(fname, nid) {
    var target = firstOtherNodeId(nid);
    EDITOR.choiceAdd(fname, nid, {
      label: "New choice",
      goto: (target === null) ? "" : target
    });
  }

  // Delete with confirm — warns BEFORE the delete when it would leave <2
  // choices on a non-ending non-stub node (the single_continue rule,
  // test_no_single_continue_choice).
  function deleteChoice(fname, nid, idx) {
    var node = EDITOR.nodeGet(fname, nid);
    var choices = node ? asArray(node.choices) : [];
    var c = choiceAt(node, idx);
    if (!c) return;
    var label = (c.label === undefined) ? "(no label)" : String(c.label);
    var remaining = choices.length - 1;
    var msg = "Delete choice #" + idx + " ('" + label + "')?\n\n" +
      "One undo step (the editor's Undo restores it).";
    var isEnding = EDITOR.endingTier(node) !== null;
    var isStub = EDITOR.deriveKind(node) === "phase8-stub";
    if (remaining < 2 && !isEnding && !isStub) {
      msg += "\n\nWARNING: this leaves " + remaining + " choice(s) on a " +
        "non-ending, non-stub node \u2014 the validator rule " +
        "single_continue fires (a node needs >=2 choices or an " +
        "ending/stub shape).";
    }
    if (typeof window !== "undefined" && window.confirm && !window.confirm(msg)) {
      return; // declined — no mutation, no re-render, note stays honest
    }
    EDITOR.choiceDelete(fname, nid, idx);
  }

  // Choice tags: edited on a COPY (order preserved), committed through the
  // named-field mutator. Duplicate add = declined with a transient note.
  function addChoiceTag(fname, nid, idx, rawTag) {
    var tag = trimText(rawTag);
    if (!tag) return;
    var node = EDITOR.nodeGet(fname, nid);
    var c = choiceAt(node, idx);
    if (!c) return;
    var current = asArray(c.tags);
    for (var i = 0; i < current.length; i++) {
      if (current[i] === tag) {
        showNote("Choice tag \"" + tag + "\" is already on this choice.");
        return;
      }
    }
    var next = current.slice(0);
    next.push(tag);
    EDITOR.choiceUpdate(fname, nid, idx, "tags", next);
  }

  function removeChoiceTag(fname, nid, idx, tagIdx) {
    var node = EDITOR.nodeGet(fname, nid);
    var c = choiceAt(node, idx);
    if (!c) return;
    var current = asArray(c.tags);
    if (tagIdx < 0 || tagIdx >= current.length) return;
    var next = current.slice(0);
    next.splice(tagIdx, 1);
    EDITOR.choiceUpdate(fname, nid, idx, "tags", next);
  }

  // -------------------------------------------------------------------------
  // Effects editor — a STRUCTURED {set: {flag: val}, "incr": {counter:
  // delta}} key/value list editor (rpg/story/interpreter.py:137-154), NOT
  // a free-JSON textarea. Every edit is computed from the BUNDLE (never a
  // DOM rebuild of the whole sub-object) and committed as ONE named-field
  // apply: blur-commit ordering guarantees the DOM inputs equal the bundle
  // between events (each input's change fires on its own blur, and every
  // apply re-renders the section from the bundle), so a bundle-based
  // computation is always consistent and each action is exactly one undo
  // step.
  // -------------------------------------------------------------------------

  // Literal parse for effect values: true/false/null keywords and finite
  // numbers commit as their JSON types; anything else stays a string (the
  // live data's set-value is boolean: {"anaerobic": true}). Round-trip
  // stable: displayValue(parseEffectValue(displayValue(v))) === v for
  // string/number/boolean values.
  function parseEffectValue(text) {
    var t = trimText(text);
    if (t === "true") return true;
    if (t === "false") return false;
    if (t === "null") return null;
    if (t !== "" && isFinite(Number(t))) return Number(t);
    return t;
  }

  function displayValue(v) {
    if (v === undefined || v === null) return "";
    if (typeof v === "string") return v;
    try {
      return JSON.stringify(v);
    } catch (e) {
      return String(v);
    }
  }

  function uniqueScaffoldKey(obj, base) {
    var k = base;
    var i = 2;
    while (hasOwn(obj, k)) {
      k = base + "_" + i;
      i++;
    }
    return k;
  }

  function plainEffects(v) {
    return (v && typeof v === "object" &&
            Object.prototype.toString.call(v) !== "[object Array]")
      ? v : null;
  }

  function bucketCopy(v) {
    var src = plainEffects(v) || {};
    var out = {};
    for (var k in src) {
      if (hasOwn(src, k)) out[k] = src[k];
    }
    return out;
  }

  // The effects skeleton: canonical key order set, incr, then unknown
  // sub-keys (§1.6 schema order; reordering on edit is a legitimate
  // effects edit). Presence semantics: a "set"/"incr" key that existed on
  // the choice stays (even emptied); a key that never existed is only
  // created by the add buttons / first entry. Unknown sub-keys on effects
  // are preserved (B11 spirit — nothing ever whitelists the effects
  // object away).
  function baseEffects(cur, forceKind) {
    var out = {};
    if (hasOwn(cur, "set") || forceKind === "set") out.set = bucketCopy(cur.set);
    if (hasOwn(cur, "incr") || forceKind === "incr") {
      out.incr = bucketCopy(cur.incr);
    }
    for (var k in cur) {
      if (hasOwn(cur, k) && k !== "set" && k !== "incr") out[k] = cur[k];
    }
    return out;
  }

  // One effects entry changed (key renamed or value edited; clearing the
  // key removes the entry). ONE apply through the named-field mutator.
  // The row's data-ch-efs-orig stamps the key the row was rendered with,
  // so a rename deletes the ORIGINAL bucket key (with a duplicate guard —
  // renaming onto an existing key is declined with a transient note).
  function setEffectsEntry(fname, nid, idx, kind, origKey, newKey, newVal) {
    if (kind !== "set" && kind !== "incr") return;
    var node = EDITOR.nodeGet(fname, nid);
    var c = choiceAt(node, idx);
    if (!c) return;
    var cur = plainEffects(c.effects) || {};
    var out = baseEffects(cur, null);
    var bucket = out[kind];
    var renamed = (origKey !== null && origKey !== "" &&
                   hasOwn(bucket, origKey) && origKey !== newKey);
    if (renamed) {
      if (newKey !== "" && hasOwn(bucket, newKey)) {
        showNote("Effect key \"" + newKey + "\" already exists in " +
                 kind + " — rename declined.");
        return;
      }
      delete bucket[origKey];
    }
    if (newKey === "") {
      if (renamed) {
        EDITOR.choiceUpdate(fname, nid, idx, "effects", out); // entry removed
      }
      return; // clearing an already-empty key is a no-op
    }
    bucket[newKey] = newVal;
    EDITOR.choiceUpdate(fname, nid, idx, "effects", out);
  }

  // Remove one effects entry (the row's ✕). The container key stays even
  // when emptied — empty {} containers are schema-legal and inline in the
  // house style; removing the whole effects key is a raw-data operation.
  function removeEffectsEntry(fname, nid, idx, kind, origKey) {
    if ((kind !== "set" && kind !== "incr") || !origKey) return;
    var node = EDITOR.nodeGet(fname, nid);
    var c = choiceAt(node, idx);
    if (!c) return;
    var cur = plainEffects(c.effects) || {};
    var bucket = plainEffects(cur[kind]);
    if (!bucket || !hasOwn(bucket, origKey)) return;
    var out = baseEffects(cur, null);
    delete out[kind][origKey];
    EDITOR.choiceUpdate(fname, nid, idx, "effects", out);
  }

  // The add buttons commit a scaffold entry immediately (commit-based
  // staging: re-renders from the bundle can never wipe an uncommitted
  // row). ONE apply: the kind's container is forced into existence and
  // gets a unique placeholder key the operator renames in place.
  function addEffectsEntry(fname, nid, idx, kind) {
    if (kind !== "set" && kind !== "incr") return;
    var node = EDITOR.nodeGet(fname, nid);
    var c = choiceAt(node, idx);
    if (!c) return;
    var cur = plainEffects(c.effects) || {};
    var out = baseEffects(cur, kind);
    var bucket = out[kind];
    bucket[uniqueScaffoldKey(bucket,
      kind === "set" ? "flag_name" : "counter_name")] =
      (kind === "set") ? true : 1;
    EDITOR.choiceUpdate(fname, nid, idx, "effects", out);
  }

  // -------------------------------------------------------------------------
  // Validator consumption (read-only), mirroring 40_form.js's pattern:
  // EDITOR._lastValidation is refreshed by the 20_validate.js hook after
  // every mutation; defensively re-run if the cache is cold.
  // -------------------------------------------------------------------------

  function nodeIssues(nid) {
    var v = EDITOR._lastValidation;
    if (!v && typeof EDITOR.validateCurrent === "function") {
      try { v = EDITOR.validateCurrent(); } catch (e) { v = null; }
    }
    var out = [];
    if (v && Object.prototype.toString.call(v.errors) === "[object Array]") {
      for (var i = 0; i < v.errors.length; i++) {
        var err = v.errors[i];
        if (err && err.node === nid) out.push(err);
      }
    }
    return out;
  }

  // Does a validator error's detail reference THIS choice? The detail
  // formats are pinned by 20_validate.js's issue builders (same repo,
  // same-phase contract).
  function errorMatchesChoice(err, c) {
    var detail = String(err.detail || "");
    var label = (c.label === undefined) ? "(no label)" : String(c.label);
    var gotoTarget = (c.goto === undefined || c.goto === null)
      ? "" : String(c.goto);
    if (err.kind === "dangling_divert") {
      return detail === "choice -> " + gotoTarget;
    }
    if (err.kind === "router_only_incoming") {
      return detail.indexOf("choice '" + label + "' -> '" + gotoTarget) === 0;
    }
    if (err.kind === "cond_attribute_form") {
      return detail.indexOf("choice '" + label + "' cond") === 0;
    }
    if (err.kind === "tbd_text") {
      return detail.indexOf("choice label '" + label + "'") === 0;
    }
    if (err.kind === "weight_outside_shuffle") {
      return detail.indexOf("choice '" + label + "' carries weight") === 0;
    }
    return false;
  }

  // Per-row error chips: live client-side checks FIRST (they work even
  // before the next apply/validate cycle — mid-edit feedback), then the
  // validator's mapped errors for kinds the client checks did not already
  // chip. overrides = {label?, cond?, goto?} for display-only live
  // refresh while typing (never a bundle write).
  function rowChips(c, nid, overrides) {
    var ov = overrides || {};
    var label = (ov.label !== undefined) ? ov.label
      : (c.label === undefined ? "" : String(c.label));
    var gotoTarget = (ov.goto !== undefined) ? ov.goto
      : (c.goto === undefined || c.goto === null ? "" : String(c.goto));
    var cond = (ov.cond !== undefined) ? ov.cond
      : (c.cond === undefined || c.cond === null ? "" : String(c.cond));
    var chips = [];
    var seen = {};

    function chip(kind, msg) {
      if (seen[kind]) return;
      seen[kind] = true;
      chips.push({ kind: kind, msg: msg });
    }

    if (gotoTarget !== "" && !nodeExists(gotoTarget)) {
      chip("dangling_divert", "dangling goto \u2192 " + gotoTarget +
        " \u2014 no node with this id exists (validator rule " +
        "dangling_divert)");
    }
    for (var r = 0; r < ROUTER_ONLY_IDS.length; r++) {
      if (gotoTarget === ROUTER_ONLY_IDS[r]) {
        chip("router_only_incoming", "restored nodes are ROUTER-ONLY: " +
          "no incoming choice edges may exist (validator rule " +
          "router_only_incoming)");
      }
    }
    if (cond !== "" && BROKEN_COND_RE.test(cond)) {
      chip("cond_attribute_form", "cond uses the broken dict-ATTRIBUTE " +
        "form \u2014 it silently hides the choice at runtime; use " +
        "flags.get('...') / visits.get('...', 0) (validator rule " +
        "cond_attribute_form)");
    }
    if (String(label).indexOf("TBD") >= 0) {
      chip("tbd_text", "label contains 'TBD' residue (validator rule " +
        "tbd_text)");
    }
    var errors = nodeIssues(nid);
    for (var i = 0; i < errors.length; i++) {
      var err = errors[i];
      if (!err || !ROW_ERROR_KINDS[err.kind]) continue;
      if (seen[err.kind]) continue; // the client check already chipped it
      if (!errorMatchesChoice(err, c)) continue;
      chip(err.kind, err.kind + " \u2014 " + String(err.detail || ""));
    }
    return chips;
  }

  function chipsHtml(chips) {
    var html = "";
    for (var i = 0; i < chips.length; i++) {
      html += "<div class=\"ch-row-issue\">\u26a0 <b>" + esc(chips[i].kind) +
        "</b> \u2014 " + esc(chips[i].msg) + "</div>";
    }
    return html;
  }

  // The live choice-count hint (the 0-single-Continue rule). overrides
  // feed the display-only live refresh while a label is being typed.
  function continueHintHtml(node, overrides) {
    var choices = asArray(node ? node.choices : null);
    var n = choices.length;
    var single = false;
    if (n === 1) {
      var c = choices[0];
      var label = (overrides && overrides.label !== undefined)
        ? overrides.label
        : (c && typeof c === "object" && c.label !== undefined
            ? String(c.label) : "");
      single = (label === "Continue");
    }
    var cls = single ? "ch-hint ch-hint-bad" : "ch-hint";
    var text = n + " choice" + (n === 1 ? "" : "s") + " on this node \u2014 " +
      "a node needs >=2 choices or an ending/stub shape (validator rule " +
      "single_continue); choice order is the player-facing selection " +
      "order (non-weighted nodes).";
    if (single) {
      text += " \u26a0 single 'Continue' choice: the single_continue " +
        "rule fires.";
    }
    return "<div id=\"ch-count-hint\" class=\"" + cls + "\">" + esc(text) +
      "</div>";
  }

  // Section-level list: this node's validator errors that are NOT
  // row-mapped and NOT single_continue (that one lives in the hint).
  function otherIssuesHtml(nid) {
    var errors = nodeIssues(nid);
    var html = "";
    for (var i = 0; i < errors.length; i++) {
      var err = errors[i];
      if (!err || ROW_ERROR_KINDS[err.kind] || err.kind === "single_continue") {
        continue;
      }
      html += "<div class=\"ch-issue\">\u26a0 <b>" + esc(err.kind) +
        "</b> \u2014 " + esc(err.detail || "") + "</div>";
    }
    return html;
  }

  // -------------------------------------------------------------------------
  // Renderers (HTML string builders; every data-derived value goes through
  // esc()).
  // -------------------------------------------------------------------------

  function gotoSelectHtml(c, idx) {
    var b = EDITOR.state.bundle;
    var order = (b && Object.prototype.toString.call(b.order) ===
                 "[object Array]" && b.order.length)
      ? b.order
      : (b && b.files ? Object.keys(b.files) : []);
    var cur = (c.goto === undefined || c.goto === null)
      ? "" : String(c.goto);
    var known = {};
    var html = "<select class=\"ch-goto\" data-ch-field=\"goto\" " +
      "data-ch-idx=\"" + idx + "\">";
    // The empty option: an empty/none target is INVALID by design —
    // committing it makes dangling_divert fire so the state stays visible.
    html += "<option value=\"\"" + (cur === "" ? " selected" : "") +
      ">(none \u2014 invalid)</option>";
    // Grouped by file, manifest order (bundle.order; insertion order for
    // node ids within a file). This dropdown IS the B5 connection editor.
    for (var i = 0; i < order.length; i++) {
      var fname = order[i];
      var file = (b && b.files) ? b.files[fname] : null;
      var nodes = (file && file.nodes) ? file.nodes : null;
      if (!nodes) continue;
      html += "<optgroup label=\"" + esc(fname) + "\">";
      for (var nid in nodes) {
        if (!hasOwn(nodes, nid)) continue;
        known[nid] = true;
        html += "<option value=\"" + esc(nid) + "\"" +
          (cur === nid ? " selected" : "") + ">" + esc(nid) + "</option>";
      }
      html += "</optgroup>";
    }
    // A dangling current target gets its own visible group (preselected),
    // so the broken state is readable straight off the dropdown.
    if (cur !== "" && !known[cur]) {
      html += "<optgroup label=\"(dangling \u2014 invalid target)\">" +
        "<option value=\"" + esc(cur) + "\" selected>\u26a0 " +
        esc(cur) + "</option></optgroup>";
    }
    html += "</select>";
    return html;
  }

  function renderEffects(c, idx) {
    var fx = (c.effects && typeof c.effects === "object" &&
              Object.prototype.toString.call(c.effects) !==
              "[object Array]") ? c.effects : null;
    var html = "<div class=\"ch-efs\"><span class=\"ch-sub-label\">" +
      "effects</span> <span class=\"ch-efs-schema\">applied on choose " +
      "&#123;&quot;set&quot;: &#123;flag: val&#125;, &quot;incr&quot;: " +
      "&#123;counter: delta&#125;&#125; (rpg/story/interpreter.py:137-154)" +
      "</span>";
    var any = false;
    var kinds = ["set", "incr"];
    for (var k = 0; k < kinds.length; k++) {
      var kind = kinds[k];
      if (!fx || !hasOwn(fx, kind)) continue;
      var entries = (fx[kind] && typeof fx[kind] === "object" &&
                     Object.prototype.toString.call(fx[kind]) !==
                     "[object Array]") ? fx[kind] : {};
      for (var key in entries) {
        if (!hasOwn(entries, key)) continue;
        any = true;
        html += "<div class=\"ch-efs-row\" data-ch-efs-row=\"1\" " +
          "data-ch-efskind=\"" + kind + "\" data-ch-efs-orig=\"" +
          esc(key) + "\">" +
          "<span class=\"ch-efs-kind\">" + kind + "</span>" +
          "<input type=\"text\" class=\"ch-efs-key\" data-ch-efs-key=\"1\" " +
          "value=\"" + esc(key) + "\" aria-label=\"effects " + kind +
          " key\">" +
          "<input type=\"text\" class=\"ch-efs-val\" data-ch-efs-val=\"1\" " +
          "value=\"" + esc(displayValue(entries[key])) +
          "\" aria-label=\"effects " + kind + " value\">" +
          "<button type=\"button\" class=\"ch-btn ch-btn-x\" " +
          "data-ch-act=\"efs-remove\" aria-label=\"remove effects " +
          kind + " entry " + esc(key) + "\">\u2715</button>" +
          "</div>";
      }
    }
    if (!any) {
      html += "<span class=\"ch-none\">no effects</span>";
    }
    html += "<span class=\"ch-efs-add\">" +
      "<button type=\"button\" class=\"ch-btn\" data-ch-act=\"efs-add\" " +
      "data-ch-efskind=\"set\">+ set</button>" +
      "<button type=\"button\" class=\"ch-btn\" data-ch-act=\"efs-add\" " +
      "data-ch-efskind=\"incr\">+ incr</button>" +
      "<span class=\"ch-efs-note\">values parse as JSON literals: " +
      "true / false / null / numbers; anything else is a string</span></span>";
    html += "</div>";
    return html;
  }

  function renderChoiceTags(c, idx) {
    var tags = asArray(c.tags);
    var html = "<div class=\"ch-tags\"><span class=\"ch-sub-label\">tags" +
      "</span>";
    if (!tags.length) {
      html += "<span class=\"ch-none\">no tags</span>";
    }
    html += "<span class=\"ch-tag-list\">";
    for (var i = 0; i < tags.length; i++) {
      html += "<span class=\"ch-tag-row\">" +
        "<span class=\"ch-tag-chip\">" + esc(String(tags[i])) + "</span>" +
        "<button type=\"button\" class=\"ch-btn ch-btn-x\" " +
        "data-ch-act=\"tag-remove\" data-ch-idx=\"" + idx +
        "\" data-ch-tag-idx=\"" + i + "\" aria-label=\"remove choice tag " +
        esc(String(tags[i])) + "\">\u2715</button></span>";
    }
    html += "</span>";
    html += "<span class=\"ch-tag-add\"><input type=\"text\" " +
      "class=\"ch-tag-input\" data-ch-role=\"tag-input\" " +
      "data-ch-idx=\"" + idx + "\" placeholder=\"add choice tag&hellip;\">" +
      "<button type=\"button\" class=\"ch-btn\" data-ch-act=\"tag-add-btn\" " +
      "data-ch-idx=\"" + idx + "\">+ Add</button></span>";
    // Quick-add palette: the known vocabulary minus what the choice
    // already carries.
    var have = {};
    for (var t = 0; t < tags.length; t++) have[String(tags[t])] = true;
    var palette = "";
    for (var v = 0; v < CHOICE_TAG_VOCAB.length; v++) {
      var tag = CHOICE_TAG_VOCAB[v].tag;
      if (have[tag]) continue;
      palette += "<button type=\"button\" class=\"ch-quick\" " +
        "data-ch-act=\"tag-add\" data-ch-idx=\"" + idx +
        "\" data-ch-tag=\"" + esc(tag) + "\">+" + esc(tag) + "</button>";
    }
    if (palette) {
      html += "<span class=\"ch-quick-list\">" + palette + "</span>";
    }
    html += "</div>";
    return html;
  }

  function renderRow(c, idx, node) {
    var weighted = weightedContext(node);
    var cond = (c.cond === undefined || c.cond === null)
      ? "" : String(c.cond);
    var label = (c.label === undefined) ? "" : String(c.label);
    var weight = (c.weight === undefined || c.weight === null)
      ? "" : displayValue(c.weight);
    var html = "";
    html += "<div class=\"ch-row\" data-ch-row=\"" + idx + "\">";
    // Head: index badge + reorder + delete (order = player-facing
    // selection order for non-weighted nodes).
    html += "<div class=\"ch-row-head\">" +
      "<span class=\"ch-idx\">#" + idx + "</span>" +
      "<button type=\"button\" class=\"ch-btn\" data-ch-act=\"up\" " +
      "data-ch-idx=\"" + idx + "\" aria-label=\"move choice " + idx +
      " up\"" + (idx === 0 ? " disabled" : "") + ">\u2191</button>" +
      "<button type=\"button\" class=\"ch-btn\" data-ch-act=\"down\" " +
      "data-ch-idx=\"" + idx + "\" aria-label=\"move choice " + idx +
      " down\"" + (idx === asArray(node.choices).length - 1
        ? " disabled" : "") + ">\u2193</button>" +
      "<button type=\"button\" class=\"ch-btn ch-btn-x\" " +
      "data-ch-act=\"delete\" data-ch-idx=\"" + idx +
      "\" aria-label=\"delete choice " + idx + "\">\u2715 delete</button>" +
      "</div>";
    // label
    html += "<div class=\"ch-field\"><label>label</label>" +
      "<input type=\"text\" class=\"ch-label\" data-ch-field=\"label\" " +
      "data-ch-idx=\"" + idx + "\" value=\"" + esc(label) + "\"></div>";
    // goto — the B5 connection/direction editor (grouped dropdown).
    html += "<div class=\"ch-field\"><label>goto <span class=\"ch-field-hint\">" +
      "(connection + direction: this node \u2192 target; grouped by file)" +
      "</span></label>" + gotoSelectHtml(c, idx) + "</div>";
    // cond — ALWAYS with the dict-method landmine warning.
    html += "<div class=\"ch-field\"><label>cond</label>" +
      "<input type=\"text\" class=\"ch-cond\" data-ch-field=\"cond\" " +
      "data-ch-idx=\"" + idx + "\" value=\"" + esc(cond) + "\">" +
      "<div class=\"ch-cond-warn\">\u26a0 " + esc(COND_HINT) + "</div></div>";
    // weight — visible ONLY in the weighted context (determinism pin).
    if (weighted) {
      html += "<div class=\"ch-field\"><label>weight</label>" +
        "<input type=\"number\" step=\"any\" class=\"ch-weight\" " +
        "data-ch-field=\"weight\" data-ch-idx=\"" + idx +
        "\" value=\"" + esc(weight) + "\"></div>";
    }
    html += renderEffects(c, idx);
    html += renderChoiceTags(c, idx);
    html += "<div class=\"ch-row-errors\">" +
      chipsHtml(rowChips(c, node.id, null)) + "</div>";
    html += "</div>";
    return html;
  }

  function addBtnHtml() {
    return "<button type=\"button\" class=\"ch-btn ch-add-btn\" " +
      "data-ch-act=\"add-choice\">+ Add choice</button>";
  }

  // -------------------------------------------------------------------------
  // The section renderer — runs on every rerender (registered into
  // EDITOR.hooks.rerender after the core's dispatcher, so the identity
  // form renders first and this section second).
  // -------------------------------------------------------------------------

  function renderChoices() {
    var section = refs.section;
    if (!section) return;
    var ids = selectedIds();
    if (!ids) {
      section.innerHTML = ""; // the aside is hidden by 40_form.js anyway
      return;
    }
    var node = EDITOR.nodeGet(ids.fname, ids.nid);
    if (!node) {
      section.innerHTML = "";
      return;
    }
    var choices = asArray(node.choices);
    var isEnding = EDITOR.endingTier(node) !== null;
    var html = "";
    html += "<h3>Choices</h3>";
    html += continueHintHtml(node, null);
    if (choices.length === 0) {
      if (isEnding) {
        // The pinned ending shape (all 21 endings carry choices: []).
        html += "<div class=\"ch-none ch-ending-empty\">" +
          esc("endings have no choices (pinned)") + "</div>";
      } else {
        html += "<div class=\"ch-none\">no choices on this node \u2014 " +
          "the validator wants >=2 choices or an ending/stub shape " +
          "(single_continue)</div>";
        html += addBtnHtml();
      }
    } else {
      for (var i = 0; i < choices.length; i++) {
        var c = choices[i];
        html += (c && typeof c === "object")
          ? renderRow(c, i, node)
          : "<div class=\"ch-issue\">\u26a0 choice #" + i +
            " is not an object \u2014 shown read-only; fix in the raw " +
            "data</div>";
      }
      if (isEnding) {
        html += "<div class=\"ch-issue\">\u26a0 this node is an ending " +
          "but carries choices \u2014 the pinned convention is empty " +
          "choices on endings (choices: [])</div>";
      }
      html += addBtnHtml();
    }
    // Weight gating notes (determinism pin).
    if (!weightedContext(node)) {
      html += "<div class=\"ch-lock\">\u2696 " + esc(WEIGHT_LOCK_NOTE) +
        "</div>";
    } else if (ids.nid !== SHUFFLE_NODE) {
      html += "<div class=\"ch-issue\">\u26a0 " + esc(WEIGHT_OUTSIDE_NOTE) +
        "</div>";
    }
    html += otherIssuesHtml(ids.nid);
    section.innerHTML = html;
  }

  // -------------------------------------------------------------------------
  // Transient inline note (declined no-op mutations like duplicate tag
  // adds; lives in the DOM until the next re-render — no mutation, so no
  // re-render happens and the note stays visible).
  // -------------------------------------------------------------------------

  function showNote(text) {
    var section = refs.section;
    if (!section) return;
    var el = document.getElementById("ch-transient-note");
    if (!el || el.parentNode !== section) {
      el = document.createElement("div");
      el.id = "ch-transient-note";
      el.className = "ch-note";
      section.insertBefore(el, section.firstChild);
    }
    el.textContent = text;
  }

  // -------------------------------------------------------------------------
  // Event wiring — delegated on the STABLE #node-form-choices mount
  // (survives every innerHTML rebuild). Attributes are data-ch-*
  // namespaced: the core's textFieldBindings (data-field) and 40_form.js's
  // data-role delegation never match them.
  // -------------------------------------------------------------------------

  function onSectionClick(el) {
    var act = el.getAttribute("data-ch-act");
    var ids = selectedIds();
    if (!act || !ids) return;
    var idx = parseInt(el.getAttribute("data-ch-idx"), 10);
    if (isNaN(idx)) idx = -1;
    if (act === "add-choice") {
      addChoice(ids.fname, ids.nid);
      return;
    }
    if (act === "delete") {
      deleteChoice(ids.fname, ids.nid, idx);
      return;
    }
    if (act === "up") {
      choiceMove(ids.fname, ids.nid, idx, idx - 1);
      return;
    }
    if (act === "down") {
      choiceMove(ids.fname, ids.nid, idx, idx + 1);
      return;
    }
    if (act === "tag-remove") {
      removeChoiceTag(ids.fname, ids.nid, idx,
        parseInt(el.getAttribute("data-ch-tag-idx"), 10));
      return;
    }
    if (act === "tag-add") {
      addChoiceTag(ids.fname, ids.nid, idx, el.getAttribute("data-ch-tag"));
      return;
    }
    if (act === "tag-add-btn") {
      var input = refs.section.querySelector("input[data-ch-role=\"tag-input\"]");
      if (input) {
        addChoiceTag(ids.fname, ids.nid, idx, input.value);
        input.value = "";
      }
      return;
    }
    if (act === "efs-add") {
      var choiceRow = findAncestor(el, "data-ch-row");
      if (choiceRow) {
        addEffectsEntry(ids.fname, ids.nid,
          parseInt(choiceRow.getAttribute("data-ch-row"), 10),
          el.getAttribute("data-ch-efskind"));
      }
      return;
    }
    if (act === "efs-remove") {
      var efsRow = findAncestor(el, "data-ch-efs-row");
      var holderRow = findAncestor(el, "data-ch-row");
      if (efsRow && holderRow) {
        removeEffectsEntry(ids.fname, ids.nid,
          parseInt(holderRow.getAttribute("data-ch-row"), 10),
          efsRow.getAttribute("data-ch-efskind"),
          efsRow.getAttribute("data-ch-efs-orig"));
      }
      return;
    }
  }

  // An effects key/value input committed (change on blur): recompute the
  // entry from the BUNDLE + this row's live inputs (see the effects
  // editor comment for why the live sibling reads are consistent).
  function onEfsInputChange(el) {
    var efsRow = findAncestor(el, "data-ch-efs-row");
    var choiceRow = findAncestor(el, "data-ch-row");
    var ids = selectedIds();
    if (!efsRow || !choiceRow || !ids) return;
    var keyInput = efsRow.querySelector("[data-ch-efs-key]");
    var valInput = efsRow.querySelector("[data-ch-efs-val]");
    setEffectsEntry(ids.fname, ids.nid,
      parseInt(choiceRow.getAttribute("data-ch-row"), 10),
      efsRow.getAttribute("data-ch-efskind"),
      efsRow.getAttribute("data-ch-efs-orig"),
      keyInput ? trimText(keyInput.value) : "",
      parseEffectValue(valInput ? valInput.value : ""));
  }

  function onSectionChange(ev) {
    var el = ev.target;
    if (!el || !el.getAttribute) return;
    var ids = selectedIds();
    if (!ids) return;
    var field = el.getAttribute("data-ch-field");
    if (field) {
      commitChoiceField(ids.fname, ids.nid,
        parseInt(el.getAttribute("data-ch-idx"), 10), field, el.value);
      return;
    }
    if (el.hasAttribute("data-ch-efs-key") ||
        el.hasAttribute("data-ch-efs-val")) {
      onEfsInputChange(el);
    }
  }

  // Display-only live feedback while typing (input events NEVER write the
  // bundle — the 00_core granularity contract): the cond/label client-side
  // row chips and the single-Continue hint refresh per keystroke with the
  // typed value as an override.
  function onSectionInput(ev) {
    var el = ev.target;
    if (!el || !el.getAttribute) return;
    var field = el.getAttribute("data-ch-field");
    if (field !== "cond" && field !== "label") return;
    var ids = selectedIds();
    if (!ids) return;
    var node = EDITOR.nodeGet(ids.fname, ids.nid);
    var choiceRow = findAncestor(el, "data-ch-row");
    if (!node || !choiceRow) return;
    var idx = parseInt(choiceRow.getAttribute("data-ch-row"), 10);
    var c = choiceAt(node, idx);
    if (!c) return;
    var overrides = {};
    overrides[field] = el.value;
    var errorsEl = choiceRow.querySelector(".ch-row-errors");
    if (errorsEl) errorsEl.innerHTML = chipsHtml(rowChips(c, node.id, overrides));
    if (field === "label") {
      // The single-Continue hint depends on the label being typed.
      var hintEl = document.getElementById("ch-count-hint");
      if (hintEl) {
        var tmp = document.createElement("div");
        tmp.innerHTML = continueHintHtml(node, overrides);
        if (tmp.firstChild) hintEl.parentNode.replaceChild(tmp.firstChild, hintEl);
      }
    }
  }

  // Enter in the tag add-input commits the add.
  function onSectionKeydown(ev) {
    var el = ev.target;
    if (!el || !el.getAttribute) return;
    if (el.getAttribute("data-ch-role") !== "tag-input") return;
    if (ev.keyCode !== 13 && ev.key !== "Enter") return;
    ev.preventDefault();
    var ids = selectedIds();
    if (!ids) return;
    var idx = parseInt(el.getAttribute("data-ch-idx"), 10);
    addChoiceTag(ids.fname, ids.nid, idx, el.value);
    el.value = "";
  }

  // -------------------------------------------------------------------------
  // Asset CSS (runtime-injected per the pipeline's per-feature CSS rule).
  // -------------------------------------------------------------------------

  EDITOR.injectCss(
    "/* injected by 42_choices.js (07.1-15): choices editor styles */\n" +
    "#node-form-choices .ch-hint { margin: 2px 0 8px; padding: 5px 8px; border: 1px solid #9db4cc; border-left: 4px solid #4682b4; background: #eef4fb; color: #2b4a68; font-size: 11px; border-radius: 4px; }\n" +
    "#node-form-choices .ch-hint-bad { border-color: #d9a544; border-left-color: #b8860b; background: #fdf6e3; color: #6b4508; }\n" +
    "#node-form-choices .ch-row { border: 1px solid #d5dae3; border-radius: 5px; padding: 6px 8px 8px; margin: 6px 0; background: #fbfcfe; }\n" +
    "#node-form-choices .ch-row-head { display: flex; align-items: center; gap: 4px; margin-bottom: 5px; }\n" +
    "#node-form-choices .ch-idx { font-family: Consolas, monospace; font-size: 11px; font-weight: bold; color: #4a5a75; margin-right: 3px; }\n" +
    "#node-form-choices .ch-btn { font-size: 11px; padding: 1px 7px; border: 1px solid #6d7f9b; background: #e9eef7; border-radius: 4px; cursor: pointer; }\n" +
    "#node-form-choices .ch-btn:hover { background: #dbe4f2; }\n" +
    "#node-form-choices .ch-btn[disabled] { opacity: 0.4; cursor: default; }\n" +
    "#node-form-choices .ch-btn-x { border-color: #c26a5a; background: #fdf0ed; color: #8c2f1f; }\n" +
    "#node-form-choices .ch-btn-x:hover { background: #f6d9d2; }\n" +
    "#node-form-choices .ch-add-btn { margin: 4px 0 8px; }\n" +
    "#node-form-choices .ch-field { margin: 4px 0; }\n" +
    "#node-form-choices .ch-field label { display: block; font-size: 11px; color: #555555; margin-bottom: 1px; }\n" +
    "#node-form-choices .ch-field-hint { font-weight: normal; color: #888888; }\n" +
    "#node-form-choices .ch-field input, #node-form-choices .ch-goto { width: 100%; font-family: Consolas, monospace; font-size: 11.5px; padding: 3px 6px; border: 1px solid #aab3c0; border-radius: 4px; background: #ffffff; }\n" +
    "#node-form-choices .ch-cond-warn { margin: 3px 0 0; padding: 4px 7px; border: 1px solid #d9a544; border-left: 4px solid #b8860b; background: #fdf6e3; color: #6b4508; font-size: 10.5px; border-radius: 4px; }\n" +
    "#node-form-choices .ch-sub-label { font-size: 11px; color: #555555; font-weight: bold; margin-right: 4px; }\n" +
    "#node-form-choices .ch-efs { margin: 6px 0 2px; padding: 5px 6px; border: 1px dashed #b9c3d3; border-radius: 4px; }\n" +
    "#node-form-choices .ch-efs-schema { font-size: 10px; color: #888888; }\n" +
    "#node-form-choices .ch-efs-row { display: flex; align-items: center; gap: 4px; margin: 3px 0; }\n" +
    "#node-form-choices .ch-efs-kind { font-family: Consolas, monospace; font-size: 10.5px; color: #2b3a55; background: #e9eef7; border-radius: 7px; padding: 0 6px; }\n" +
    "#node-form-choices .ch-efs-key, #node-form-choices .ch-efs-val { flex: 1 1 auto; min-width: 0; font-family: Consolas, monospace; font-size: 11px; padding: 2px 5px; border: 1px solid #aab3c0; border-radius: 4px; }\n" +
    "#node-form-choices .ch-efs-add { display: flex; align-items: center; gap: 4px; margin-top: 3px; flex-wrap: wrap; }\n" +
    "#node-form-choices .ch-efs-note { font-size: 10px; color: #888888; }\n" +
    "#node-form-choices .ch-tags { margin: 6px 0 2px; }\n" +
    "#node-form-choices .ch-tag-list { display: inline-flex; flex-wrap: wrap; gap: 4px; vertical-align: middle; }\n" +
    "#node-form-choices .ch-tag-row { display: inline-flex; align-items: center; gap: 2px; }\n" +
    "#node-form-choices .ch-tag-chip { display: inline-block; padding: 1px 6px; border-radius: 8px; border: 1px solid #8ea3c0; background: #e9eef7; font-family: Consolas, monospace; font-size: 10.5px; color: #2b3a55; }\n" +
    "#node-form-choices .ch-tag-add { display: flex; gap: 4px; margin: 4px 0; }\n" +
    "#node-form-choices .ch-tag-input { flex: 1 1 auto; min-width: 0; font-family: Consolas, monospace; font-size: 11px; padding: 2px 6px; border: 1px solid #aab3c0; border-radius: 4px; }\n" +
    "#node-form-choices .ch-quick-list { display: flex; flex-wrap: wrap; gap: 3px; margin: 3px 0; }\n" +
    "#node-form-choices .ch-quick { font-family: Consolas, monospace; font-size: 9.5px; padding: 1px 5px; border: 1px dashed #8ea3c0; background: #f7f9fc; color: #2b3a55; border-radius: 8px; cursor: pointer; }\n" +
    "#node-form-choices .ch-quick:hover { background: #e9eef7; }\n" +
    "#node-form-choices .ch-row-issue { margin: 3px 0; padding: 3px 7px; border-left: 4px solid #b22222; background: #fdeeea; color: #7a1616; font-size: 10.5px; border-radius: 0 4px 4px 0; }\n" +
    "#node-form-choices .ch-issue { margin: 4px 0; padding: 4px 8px; border-left: 4px solid #b22222; background: #fdeeea; color: #7a1616; font-size: 11.5px; border-radius: 0 4px 4px 0; }\n" +
    "#node-form-choices .ch-lock { margin: 8px 0 4px; padding: 6px 8px; border: 1px solid #b8860b; border-left: 4px solid #b8860b; background: #fdf6e3; color: #6b5308; font-size: 11.5px; border-radius: 4px; }\n" +
    "#node-form-choices .ch-none { font-size: 11.5px; color: #888888; font-style: italic; margin: 3px 0; }\n" +
    "#node-form-choices .ch-ending-empty { padding: 6px 8px; border: 1px solid #7aa87a; border-left: 4px solid #2e8b57; background: #eef7ee; color: #1d5c38; border-radius: 4px; }\n" +
    "#node-form-choices .ch-note { margin: 4px 0; padding: 5px 8px; border: 1px solid #9db4cc; border-left: 4px solid #4682b4; background: #eef4fb; color: #2b4a68; font-size: 11.5px; border-radius: 4px; }\n"
  );

  // -------------------------------------------------------------------------
  // Init: locate the mount, wire the delegated listeners, first render.
  // Runs once from the shell bootstrap (EDITOR.runInits).
  // -------------------------------------------------------------------------

  function initChoices() {
    refs.section = document.getElementById("node-form-choices");
    if (!refs.section) {
      warn("EDITOR choices (42_choices.js): #node-form-choices mount " +
           "missing \u2014 choices editor disabled.");
      return;
    }
    var section = refs.section;
    section.addEventListener("click", function (ev) {
      var el = ev.target;
      while (el && el !== section) {
        if (el.hasAttribute && el.hasAttribute("data-ch-act")) {
          onSectionClick(el);
          return;
        }
        el = el.parentNode;
      }
    });
    section.addEventListener("change", onSectionChange);
    section.addEventListener("input", onSectionInput);
    section.addEventListener("keydown", onSectionKeydown);
    renderChoices();
  }

  // Registration per the 07.1-04 convention: the DOM work runs from the
  // shell bootstrap (EDITOR.init); the section renderer is a RERENDER
  // REACTION (hooks.rerender) — it re-runs on EDITOR.select and after
  // every afterChange fan-out, after the core dispatcher has rendered the
  // identity form.
  EDITOR.init(initChoices);
  EDITOR.hooks.rerender.push(renderChoices);

})();
