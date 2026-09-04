/* ==========================================================================
 * 00_core.js — the editor's state layer + shared UI primitives (07.1-04).
 *
 * ASSET ORDER CONTRACT: this file sorts FIRST (00_ prefix), so the generator
 * inlines it as the FIRST asset <script> block in the emitted page. It
 * defines window.EDITOR — the contract every later asset codes against:
 *
 *   state + bundle      EDITOR.state, EDITOR.setBundle(bundle, rawTexts),
 *                       EDITOR.loadBundleForTest(obj)
 *   mutations           EDITOR.apply(action) — full-bundle snapshot for undo,
 *                       redo tail cleared, per-file dirty, afterChange()
 *                       EDITOR.nodeGet / nodeSet / nodeAdd / nodeDelete
 *                       EDITOR.choiceAdd / choiceUpdate / choiceDelete
 *   history             EDITOR.undo / EDITOR.redo / EDITOR.MAX_UNDO (200)
 *                       EDITOR.undoDepth() / EDITOR.redoDepth()
 *   dirty + fingerprints  EDITOR.state.dirty (fname present == dirty),
 *                       EDITOR.state.fingerprints (fname → FNV-1a 32-bit hex
 *                       of the raw file text), EDITOR.save.recomputeDirty()
 *   hooks               EDITOR.hooks = { rerender: [], validate: [],
 *                       persist: [] } — iterated defensively (try/catch each)
 *                       by EDITOR.afterChange(); the core registers its own
 *                       rerender dispatcher in hooks.rerender, the validator
 *                       (07.1-08) registers into hooks.validate, the
 *                       draft-scheduler (07.1-13) into hooks.persist.
 *   views + tabs        EDITOR.view(name, fn), EDITOR.rerender(),
 *                       EDITOR.setFormRenderer(fn), EDITOR.select(id|null),
 *                       EDITOR.showTab(name) — tab-bar clicks wired here.
 *   text fields         EDITOR.textFieldBindings(container) — commit on
 *                       change (ONE undo step per field commit, never per
 *                       keystroke), live preview on input (never snapshots);
 *                       EDITOR.livePreview(fn) registers preview consumers.
 *   primitives          EDITOR.init(fn) / EDITOR.runInits(),
 *                       EDITOR.injectCss(css), EDITOR.delegate(container,
 *                       evType, attr, fn), EDITOR.esc(s), EDITOR.nodeById,
 *                       EDITOR.fileOfNode, EDITOR.allNodes,
 *                       EDITOR.deriveKind, EDITOR.endingTier, EDITOR.fnv1a.
 *
 * FILE OWNERSHIP: this asset belongs to plan 07.1-04. Later plans own their
 * own files (05_json.js = 07.1-05, 10_load.js = 07.1-07, 30_graph.js =
 * 07.1-06, 40_form.js = 07.1-09, ...) — never edit another plan's asset;
 * extend the EDITOR namespace from your own file instead.
 *
 * STYLE: one classic script, one IIFE, ES5 only (var, no arrow functions,
 * no let/const, no modules): module scripts fail under file:// CORS
 * (07.1-RESEARCH-UI "Anti-patterns") and the ES5 discipline keeps the
 * emitted JS reviewable — test-enforced by tests/test_story_editor_state.py.
 * ========================================================================== */

(function () {
  "use strict";

  var MAX_UNDO = 200;

  // Derived-kind special ids (mirror of the committed viewer constants).
  var STUB_IDS = { "fa.stub": true, "alc.stub": true };
  var EDIT_PROMPT_ID = "edit.prompt";
  var RESTORED_IDS = { "gly.pfk_restored": true, "tca.aconitase_restored": true };

  // -------------------------------------------------------------------------
  // Namespace + init registry (the shell's end-of-body bootstrap calls
  // EDITOR.runInits once the document is ready — every asset registers its
  // DOM work via EDITOR.init).
  // -------------------------------------------------------------------------

  window.EDITOR = {
    version: "0.1.0",
    _inits: [],
    init: function (fn) {
      if (typeof fn === "function") {
        window.EDITOR._inits.push(fn);
      }
    },
    runInits: function () {
      for (var i = 0; i < window.EDITOR._inits.length; i++) {
        try {
          window.EDITOR._inits[i]();
        } catch (e) {
          editorWarn("EDITOR init " + i + " failed: " + describe(e));
        }
      }
    }
  };

  function editorWarn(msg) {
    try {
      if (typeof console !== "undefined" && console && console.warn) {
        console.warn(msg);
      }
    } catch (e) { /* never warn about failing to warn */ }
  }

  function describe(e) {
    return (e && e.message) ? String(e.message) : String(e);
  }

  // -------------------------------------------------------------------------
  // injectCss — per-asset CSS co-ownership. The shell carries structural
  // layout ONLY; each asset injects its own styles at runtime.
  // -------------------------------------------------------------------------

  EDITOR.injectCss = function (css) {
    var style = document.createElement("style");
    style.type = "text/css";
    style.appendChild(document.createTextNode(String(css == null ? "" : css)));
    var head = document.head ||
      document.getElementsByTagName("head")[0] ||
      document.documentElement;
    head.appendChild(style);
    return style;
  };

  // -------------------------------------------------------------------------
  // State. The RAW bundle is the source of truth (ordered objects — JS
  // preserves string-key insertion order, so per-file node order survives
  // every round-trip); the display model re-derives after each mutation.
  //
  //   bundle = { files: { fname: { nodes: { id: node } } },
  //              manifest, citations, sources, edits, cast, order: [fnames] }
  //
  //   dirty  = { fname: true }  (a file is dirty iff its key is present)
  //   fingerprints = { fname: "<8-hex FNV-1a of the raw file text>" }
  // -------------------------------------------------------------------------

  EDITOR.state = {
    bundle: null,
    dirty: {},
    fingerprints: {},
    sel: null,
    loadedAt: null
  };

  // Original per-file JSON snapshots captured at setBundle time — the
  // baseline every dirty recomputation (undo/redo) compares against.
  EDITOR._originals = {};
  EDITOR._undoStack = [];
  EDITOR._redoStack = [];
  EDITOR._views = {};
  EDITOR._formRender = null;
  EDITOR._liveFns = [];
  EDITOR.MAX_UNDO = MAX_UNDO;

  EDITOR.hooks = { rerender: [], validate: [], persist: [] };

  // -------------------------------------------------------------------------
  // FNV-1a 32-bit (drift DETECTOR for draft staleness, not security —
  // 07.1-RESEARCH-UI Code Example 3 note). 32-bit modular math is emulated
  // with shifts: the FNV prime 16777619 = 2^24 + 2^8 + 2^7 + 2^4 + 2^1 + 2^0
  // and JS bitwise ops coerce through ToInt32, so every intermediate stays
  // exact in float64 and the modular result is exact.
  // -------------------------------------------------------------------------

  EDITOR.fnv1a = function (text) {
    var h = 0x811c9dc5;
    var s = String(text == null ? "" : text);
    for (var i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h += (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24);
    }
    // >>> 0 makes it uint32; pad to 8 hex chars for stable display/diff.
    return ("00000000" + (h >>> 0).toString(16)).slice(-8);
  };

  // -------------------------------------------------------------------------
  // Node id stamping. Nodes in the raw bundle must stay PRISTINE (an extra
  // enumerable "id" key would corrupt the saved JSON), but every consumer
  // needs node.id (deriveKind, selection, form binding). The stamp is a
  // NON-enumerable property: invisible to JSON.stringify, Object.keys and
  // for-in, so the saved bytes never change. Snapshots (JSON round-trips)
  // drop it — restoreFromSnapshot re-stamps.
  // -------------------------------------------------------------------------

  function stampIds(bundle) {
    if (!bundle || !bundle.files) return;
    var fnames = Object.keys(bundle.files);
    for (var i = 0; i < fnames.length; i++) {
      var nodes = bundle.files[fnames[i]].nodes;
      if (!nodes || typeof nodes !== "object") continue;
      for (var nid in nodes) {
        if (Object.prototype.hasOwnProperty.call(nodes, nid) &&
            nodes[nid] && typeof nodes[nid] === "object") {
          Object.defineProperty(nodes[nid], "id", {
            value: nid,
            enumerable: false,
            configurable: true,
            writable: true
          });
        }
      }
    }
  }

  // -------------------------------------------------------------------------
  // setBundle / loadBundleForTest
  // -------------------------------------------------------------------------

  EDITOR.setBundle = function (bundle, rawTexts) {
    EDITOR.state.bundle = bundle || null;
    EDITOR.state.dirty = {};
    EDITOR.state.fingerprints = {};
    EDITOR.state.sel = null;
    EDITOR.state.loadedAt = bundle ? new Date().toISOString() : null;
    EDITOR._undoStack.length = 0;
    EDITOR._redoStack.length = 0;
    EDITOR._originals = {};
    if (bundle && bundle.files) {
      stampIds(bundle);
      var fnames = Object.keys(bundle.files);
      for (var i = 0; i < fnames.length; i++) {
        var f = fnames[i];
        EDITOR._originals[f] = JSON.stringify(bundle.files[f]);
      }
      if (rawTexts) {
        for (var rf in rawTexts) {
          if (Object.prototype.hasOwnProperty.call(rawTexts, rf)) {
            EDITOR.state.fingerprints[rf] = EDITOR.fnv1a(rawTexts[rf]);
          }
        }
      }
    }
    EDITOR.afterChange();
  };

  // Test fixture loader: drive the page from an injected object (used by
  // later diagnostics/self-tests; harmless in production — it only replaces
  // state). No rawTexts available, so no fingerprints are computed.
  EDITOR.loadBundleForTest = function (obj) {
    EDITOR.setBundle(obj || null, null);
  };

  // -------------------------------------------------------------------------
  // Undo/redo — snapshot stacks (RESEARCH-UI Code Example 2). One undo entry
  // = JSON.stringify of the whole bundle (57 nodes ≈ 92 KB raw → snapshots
  // are trivially cheap); MAX_UNDO caps memory; a new action clears the redo
  // tail. Undo/redo RE-DERIVE the dirty map by comparing the restored
  // per-file JSON against the ORIGINAL loaded snapshots (EDITOR._originals).
  // -------------------------------------------------------------------------

  function restoreFromSnapshot(jsonText) {
    EDITOR.state.bundle = JSON.parse(jsonText);
    stampIds(EDITOR.state.bundle); // snapshots are plain JSON — re-stamp ids
  }

  // Every mutation flows through apply(): full-bundle snapshot pushed for
  // undo, the redo tail cleared, the action's files marked dirty, then
  // afterChange() fans out to the rerender dispatcher + validator +
  // draft-persist hooks (each defensively try/catch'd).
  // action = { files: [fname, ...], redo: function (bundle) }.
  EDITOR.apply = function (action) {
    var b = EDITOR.state.bundle;
    if (!b) {
      editorWarn("EDITOR.apply ignored: no bundle loaded");
      return;
    }
    if (!action || typeof action.redo !== "function") {
      editorWarn("EDITOR.apply ignored: action.redo function missing");
      return;
    }
    EDITOR._undoStack.push(JSON.stringify(b));
    if (EDITOR._undoStack.length > MAX_UNDO) {
      EDITOR._undoStack.shift();
    }
    action.redo(b);
    if (action.files && action.files.length) {
      for (var i = 0; i < action.files.length; i++) {
        EDITOR.state.dirty[action.files[i]] = true;
      }
    }
    EDITOR._redoStack.length = 0;
    EDITOR.afterChange();
  };

  EDITOR.undo = function () {
    if (!EDITOR._undoStack.length || !EDITOR.state.bundle) return false;
    EDITOR._redoStack.push(JSON.stringify(EDITOR.state.bundle));
    restoreFromSnapshot(EDITOR._undoStack.pop());
    EDITOR.save.recomputeDirty();
    EDITOR.afterChange();
    return true;
  };

  EDITOR.redo = function () {
    if (!EDITOR._redoStack.length || !EDITOR.state.bundle) return false;
    EDITOR._undoStack.push(JSON.stringify(EDITOR.state.bundle));
    restoreFromSnapshot(EDITOR._redoStack.pop());
    EDITOR.save.recomputeDirty();
    EDITOR.afterChange();
    return true;
  };

  // Depth accessors for the status bar (undo N / redo M).
  EDITOR.undoDepth = function () { return EDITOR._undoStack.length; };
  EDITOR.redoDepth = function () { return EDITOR._redoStack.length; };
  EDITOR.dirtyFiles = function () { return Object.keys(EDITOR.state.dirty); };

  // Dirty recomputation against the ORIGINAL load-time snapshots. Lives on
  // EDITOR.save (07.1-13 extends this namespace with staleCheck + friends).
  // A file is dirty iff its current per-file JSON differs from the original.
  EDITOR.save = {
    recomputeDirty: function () {
      var b = EDITOR.state.bundle;
      var dirty = EDITOR.state.dirty;
      var names = {};
      var fnames = (b && b.files) ? Object.keys(b.files) : [];
      var i;
      for (i = 0; i < fnames.length; i++) names[fnames[i]] = true;
      var onames = Object.keys(EDITOR._originals);
      for (i = 0; i < onames.length; i++) names[onames[i]] = true;
      var all = Object.keys(names);
      for (i = 0; i < all.length; i++) {
        var f = all[i];
        var cur = (b && b.files && b.files[f])
          ? JSON.stringify(b.files[f]) : null;
        if (cur === null || cur !== EDITOR._originals[f]) {
          dirty[f] = true;
        } else {
          delete dirty[f];
        }
      }
      return dirty;
    }
  };

  // -------------------------------------------------------------------------
  // afterChange — the mutation fan-out. Dispatches every registered hook of
  // each kind inside its own try/catch so one broken view/hook NEVER kills
  // the state layer (07.1-RESEARCH-UI; pinned by the structural test).
  // -------------------------------------------------------------------------

  function dispatchHooks(kind) {
    var list = EDITOR.hooks[kind] || [];
    for (var i = 0; i < list.length; i++) {
      try {
        list[i]();
      } catch (e) {
        editorWarn("EDITOR " + kind + " hook " + i + " failed: " + describe(e));
      }
    }
  }

  EDITOR.afterChange = function () {
    dispatchHooks("rerender");  // views + subscribers (core dispatcher inside)
    dispatchHooks("validate");  // validator re-run (07.1-08 registers)
    dispatchHooks("persist");   // draft-scheduler (07.1-13 registers)
  };

  // -------------------------------------------------------------------------
  // UNKNOWN-KEY PRESERVATION CONTRACT (B11 extensibility):
  // mutators touch ONLY the named field and NEVER rebuild a node from a
  // field whitelist — unknown keys on nodes AND choices round-trip untouched
  // through every mutation, snapshot, undo/redo and save (the engine and the
  // 5.4 conformance battery consume this exact schema; 07.1-RESEARCH-UI
  // anti-pattern 4). All mutations below flow through EDITOR.apply so each
  // is ONE undo step with per-file dirty marking.
  // -------------------------------------------------------------------------

  function fileRef(bundle, fname) {
    return (bundle && bundle.files && bundle.files[fname])
      ? bundle.files[fname] : null;
  }

  function nodeRef(bundle, fname, id) {
    var file = fileRef(bundle, fname);
    var n = (file && file.nodes) ? file.nodes[id] : null;
    return (n && typeof n === "object") ? n : null;
  }

  EDITOR.nodeGet = function (fname, id) {
    return nodeRef(EDITOR.state.bundle, fname, id);
  };

  // Touches ONLY the named field (see the contract comment above).
  EDITOR.nodeSet = function (fname, id, field, value) {
    EDITOR.apply({
      files: [fname],
      redo: function (b) {
        var node = nodeRef(b, fname, id);
        if (node) node[field] = value;
      }
    });
  };

  EDITOR.nodeAdd = function (fname, id, nodeObj) {
    EDITOR.apply({
      files: [fname],
      redo: function (b) {
        var file = fileRef(b, fname);
        if (!file) return;
        if (!file.nodes || typeof file.nodes !== "object") file.nodes = {};
        var n = (nodeObj && typeof nodeObj === "object") ? nodeObj : {};
        file.nodes[id] = n;
        Object.defineProperty(n, "id", {
          value: id,
          enumerable: false,
          configurable: true,
          writable: true
        });
      }
    });
  };

  EDITOR.nodeDelete = function (fname, id) {
    EDITOR.apply({
      files: [fname],
      redo: function (b) {
        var file = fileRef(b, fname);
        if (file && file.nodes) delete file.nodes[id];
      }
    });
  };

  EDITOR.choiceAdd = function (fname, id, choice) {
    EDITOR.apply({
      files: [fname],
      redo: function (b) {
        var node = nodeRef(b, fname, id);
        if (!node) return;
        if (Object.prototype.toString.call(node.choices) !== "[object Array]") {
          node.choices = [];
        }
        node.choices.push(choice || {});
      }
    });
  };

  // Touches ONLY the named field on the choice (same B11 contract as nodes:
  // unknown choice keys round-trip untouched).
  EDITOR.choiceUpdate = function (fname, id, index, field, value) {
    EDITOR.apply({
      files: [fname],
      redo: function (b) {
        var node = nodeRef(b, fname, id);
        var c = (node && Object.prototype.toString.call(node.choices) ===
                 "[object Array]") ? node.choices[index] : null;
        if (c && typeof c === "object") c[field] = value;
      }
    });
  };

  EDITOR.choiceDelete = function (fname, id, index) {
    EDITOR.apply({
      files: [fname],
      redo: function (b) {
        var node = nodeRef(b, fname, id);
        var choices = (node && Object.prototype.toString.call(node.choices) ===
                       "[object Array]") ? node.choices : null;
        if (choices && index >= 0 && index < choices.length) {
          choices.splice(index, 1);
        }
      }
    });
  };

  // -------------------------------------------------------------------------
  // Text-edit granularity: delegated field bindings. `change` (blur/commit)
  // = ONE undo step per field commit via apply() — never per keystroke;
  // `input` = live-preview notification ONLY (no snapshot, no bundle write,
  // so the undo pre-image stays the true pre-edit value).
  // -------------------------------------------------------------------------

  // Keep JSON round-trip types stable: if the field already held a number
  // and the committed text parses as a finite number, commit a number;
  // otherwise commit the string as typed (text fields stay strings).
  function coerceLike(oldValue, text) {
    if (typeof oldValue === "number" && String(text).trim() !== "") {
      var n = Number(text);
      if (isFinite(n)) return n;
    }
    return text;
  }

  function fieldEventInfo(el) {
    var tag = (el.tagName || "").toLowerCase();
    if (tag !== "input" && tag !== "textarea") return null;
    var field = el.getAttribute("data-field");
    if (!field) return null;
    var nid = el.getAttribute("data-node") || EDITOR.state.sel;
    if (!nid) return null;
    var file = el.getAttribute("data-file") || EDITOR.fileOfNode(nid);
    if (!file) return null;
    return { node: nid, file: file, field: field, el: el };
  }

  EDITOR.textFieldBindings = function (container) {
    if (!container || !container.addEventListener) return;
    container.addEventListener("change", function (ev) {
      var el = ev.target;
      if (!el || !el.getAttribute) return;
      var info = fieldEventInfo(el);
      if (!info || !EDITOR.state.bundle) return;
      var value = el.value;
      EDITOR.apply({
        files: [info.file],
        redo: function (b) {
          var node = nodeRef(b, info.file, info.node);
          if (node) node[info.field] = coerceLike(node[info.field], value);
        }
      });
    });
    container.addEventListener("input", function (ev) {
      var el = ev.target;
      if (!el || !el.getAttribute) return;
      var info = fieldEventInfo(el);
      if (!info) return;
      for (var i = 0; i < EDITOR._liveFns.length; i++) {
        try {
          EDITOR._liveFns[i]({
            node: info.node, file: info.file, field: info.field,
            value: el.value, el: el
          });
        } catch (e) {
          editorWarn("EDITOR live-preview hook " + i + " failed: " +
                     describe(e));
        }
      }
    });
  };

  // Register a live-preview consumer (receives {node, file, field, value, el}
  // per keystroke; must not mutate the bundle or snapshot).
  EDITOR.livePreview = function (fn) {
    if (typeof fn === "function") EDITOR._liveFns.push(fn);
  };

  // -------------------------------------------------------------------------
  // Selection + tabs + views.
  // -------------------------------------------------------------------------

  EDITOR.select = function (nodeId) {
    EDITOR.state.sel = (nodeId == null) ? null : String(nodeId);
    dispatchHooks("rerender");
  };

  EDITOR.showTab = function (name) {
    var btns = document.querySelectorAll("#tabbar .tab-btn");
    for (var i = 0; i < btns.length; i++) {
      if (btns[i].getAttribute("data-tab") === name) {
        btns[i].classList.add("active");
      } else {
        btns[i].classList.remove("active");
      }
    }
    var panels = document.querySelectorAll("#tab-panels .tab-panel");
    for (var j = 0; j < panels.length; j++) {
      if (panels[j].id === "tab-" + name) {
        panels[j].classList.add("active");
      } else {
        panels[j].classList.remove("active");
      }
    }
  };

  // Register a per-view renderer (name is informational; registration order
  // drives rerender order). Later plans register 'graph', 'save', etc.
  EDITOR.view = function (name, renderFn) {
    if (typeof renderFn === "function") {
      EDITOR._views[name] = renderFn;
    } else {
      delete EDITOR._views[name];
    }
  };

  // The node-form hook (separate slot from views: the form re-renders for
  // state.sel on every rerender). Registered by 40_form.js (07.1-09).
  EDITOR.setFormRenderer = function (fn) {
    EDITOR._formRender = (typeof fn === "function") ? fn : null;
  };

  EDITOR.rerender = function () {
    for (var name in EDITOR._views) {
      if (Object.prototype.hasOwnProperty.call(EDITOR._views, name)) {
        try {
          EDITOR._views[name]();
        } catch (e) {
          editorWarn("EDITOR view '" + name + "' failed: " + describe(e));
        }
      }
    }
    if (typeof EDITOR._formRender === "function") {
      try {
        EDITOR._formRender();
      } catch (e) {
        editorWarn("EDITOR form render failed: " + describe(e));
      }
    }
  };

  // The core's own rerender dispatcher lives in hooks.rerender[0]: every
  // afterChange() (and select()) re-renders the registered views + form.
  EDITOR.hooks.rerender.push(EDITOR.rerender);

  // -------------------------------------------------------------------------
  // Shared helpers.
  // -------------------------------------------------------------------------

  EDITOR.esc = function (s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  };

  // Event delegation by data-* attribute — ONE listener per container
  // (RESEARCH-UI structural choice 2; never per-row listeners).
  EDITOR.delegate = function (container, evType, attr, fn) {
    if (!container || !container.addEventListener) return;
    container.addEventListener(evType, function (ev) {
      var el = ev.target;
      while (el && el !== container) {
        if (el.hasAttribute && el.hasAttribute(attr)) {
          fn(el, ev);
          return;
        }
        el = el.parentNode;
      }
      if (el === container && el.hasAttribute && el.hasAttribute(attr)) {
        fn(el, ev);
      }
    });
  };

  function fileOrder(bundle) {
    if (bundle && Object.prototype.toString.call(bundle.order) ===
        "[object Array]" && bundle.order.length) {
      return bundle.order;
    }
    return (bundle && bundle.files) ? Object.keys(bundle.files) : [];
  }

  EDITOR.nodeById = function (id) {
    var b = EDITOR.state.bundle;
    var order = fileOrder(b);
    for (var i = 0; i < order.length; i++) {
      var file = fileRef(b, order[i]);
      var nodes = (file && file.nodes) ? file.nodes : null;
      if (nodes && Object.prototype.hasOwnProperty.call(nodes, id)) {
        var n = nodes[id];
        return (n && typeof n === "object") ? n : null;
      }
    }
    return null;
  };

  EDITOR.fileOfNode = function (id) {
    var b = EDITOR.state.bundle;
    var order = fileOrder(b);
    for (var i = 0; i < order.length; i++) {
      var file = fileRef(b, order[i]);
      var nodes = (file && file.nodes) ? file.nodes : null;
      if (nodes && Object.prototype.hasOwnProperty.call(nodes, id)) {
        return order[i];
      }
    }
    return null;
  };

  // Iterator over every node: returns [{id, file, node}] wrappers in
  // bundle.order order (node insertion order within each file). The wrapper
  // is a VIEW — mutations must go through the mutators, never the wrapper.
  EDITOR.allNodes = function () {
    var b = EDITOR.state.bundle;
    var out = [];
    var order = fileOrder(b);
    for (var i = 0; i < order.length; i++) {
      var fname = order[i];
      var file = fileRef(b, fname);
      var nodes = (file && file.nodes) ? file.nodes : null;
      if (!nodes) continue;
      for (var nid in nodes) {
        if (Object.prototype.hasOwnProperty.call(nodes, nid)) {
          out.push({ id: nid, file: fname, node: nodes[nid] });
        }
      }
    }
    return out;
  };

  // -------------------------------------------------------------------------
  // Derived node kinds — DERIVED, never stored (there is no node_type field).
  //
  // deriveKind is a port of the committed viewer's derive_kind precedence
  // (first-match): ending-<tier> > phase8-stub > edit-prompt > restored >
  // rng > edit-allowed > story.
  // Source: git show HEAD:tools/story_graph_viewer.py:206-228
  //   (special-id constants: fa.stub / alc.stub = STUB_IDS, edit.prompt =
  //   EDIT_PROMPT_ID, gly.pfk_restored / tca.aconitase_restored =
  //   RESTORED_IDS).
  // -------------------------------------------------------------------------

  // Tier comes from is_ending ONLY — NEVER from the ending:* tag: the 3
  // anaerobic endings (anaer.lactic / anaer.ethanolic / anaer.crisis) carry
  // is_ending but NO ending:* tag (07.1-RESEARCH-DATA Pitfall 15).
  EDITOR.endingTier = function (node) {
    if (node && node.is_ending !== undefined && node.is_ending !== null) {
      return String(node.is_ending);
    }
    return null;
  };

  function isRngNode(node) {
    var choices = node.choices;
    if (Object.prototype.toString.call(choices) !== "[object Array]") {
      return false;
    }
    for (var i = 0; i < choices.length; i++) {
      var c = choices[i];
      if (c && typeof c === "object" && c.weight !== undefined &&
          c.weight !== null) {
        return true;
      }
    }
    return false;
  }

  function isEditAllowedNode(node) {
    var tags = node.tags;
    if (Object.prototype.toString.call(tags) !== "[object Array]") {
      return false;
    }
    for (var i = 0; i < tags.length; i++) {
      if (typeof tags[i] === "string" &&
          tags[i].indexOf("edit:enzyme:") === 0) {
        return true;
      }
    }
    return false;
  }

  EDITOR.deriveKind = function (node) {
    if (!node || typeof node !== "object") return "story";
    var tier = EDITOR.endingTier(node);
    if (tier) return "ending-" + tier;
    var id = node.id; // non-enumerable stamp (see stampIds above)
    if (id && STUB_IDS[id]) return "phase8-stub";
    if (id === EDIT_PROMPT_ID) return "edit-prompt";
    if (id && RESTORED_IDS[id]) return "restored";
    if (isRngNode(node)) return "rng";
    if (isEditAllowedNode(node)) return "edit-allowed";
    return "story";
  };

  // -------------------------------------------------------------------------
  // Core-owned CSS (co-owned here per the shell's "structural layout ONLY"
  // rule): status-bar niceties + the tab active states, re-asserted so the
  // core is self-sufficient if the shell evolves. The .editor-dirty class is
  // the shared dirty-highlight any later asset may reuse.
  // -------------------------------------------------------------------------

  EDITOR.injectCss(
    "/* co-owned by 00_core.js (07.1-04): status bar + tab active states */\n" +
    "#statusbar span { white-space: nowrap; }\n" +
    "#statusbar .editor-dirty { color: #b5442d; font-weight: bold; }\n" +
    ".tab-btn.active { background: #2e3440; border-color: #2e3440; " +
    "color: #ffffff; }\n"
  );

  // -------------------------------------------------------------------------
  // Core init: wire the tab bar with ONE delegated listener.
  // -------------------------------------------------------------------------

  EDITOR.init(function () {
    var tabbar = document.getElementById("tabbar");
    if (tabbar) {
      EDITOR.delegate(tabbar, "click", "data-tab", function (el) {
        EDITOR.showTab(el.getAttribute("data-tab"));
      });
    }
  });

})();
