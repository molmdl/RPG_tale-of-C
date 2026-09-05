/* ==========================================================================
 * 45_lifecycle.js — the node-lifecycle editor: add/delete nodes with
 * reference safety (Requirement B1) + node-type transitions as the
 * DERIVED-KIND recipes (Requirement B2) (07.1-17).
 *
 * OWNERSHIP: this asset belongs to plan 07.1-17 (Wave 5). It fills the
 * FIXED shell mount #node-form-lifecycle and NEVER edits another asset's
 * file (00_core.js = 07.1-04, 40_form.js = 07.1-09 owns #node-form-identity
 * + the #node-form aside listeners, 42_choices.js = 07.1-15, 43_onenter.js
 * = 07.1-16, 50_editscast.js = 07.1-14 owns the Data tab).
 *
 * SURFACES (three, all owned HERE; delegated listeners attach to these
 * containers ONLY — never to the shared #node-form aside, #graph-area or
 * any sibling mount):
 *   1. #node-form-lifecycle — the fixed shell sub-section (node type +
 *      recipe entry points + validator strip + manifest-edit export).
 *   2. #lifecycle-toolbar — a self-created slim bar appended to #tab-graph
 *      (the plan's "toolbar buttons into the graph tab"): the add/delete
 *      entry points stay reachable while the form aside is hidden (40_form
 *      hides #node-form until a node is selected).
 *   3. #lifecycle-overlay — a self-created body-level overlay host for the
 *      add wizard / delete guard / recipe panels / acknowledgment modals
 *      (body-level so a wizard stays visible even when the aside is
 *      hidden; one listener set per container; data-lc-* namespacing keeps
 *      the sibling delegations collision-free).
 *
 * THERE IS NO STORED node_type (RESEARCH-DATA §1.7): node kinds are
 * DERIVED (ending-<tier> > phase8-stub > edit-prompt > restored > rng >
 * edit-allowed > story — the viewer derive_kind precedence ported in
 * 00_core.js deriveKind). "Making a node X" therefore COMPOSES the
 * underlying tag/choice/manifest changes — the §1.7 transition-table
 * recipes — never a field write:
 *
 *   node -> edit-allowed : 1. add the edit:enzyme:<id> tag
 *                          2. add the edit:offer choice (goto edit.prompt,
 *                             tag edit:offer)
 *                          3. create the edits.json bucket <id> (delegates
 *                             to the Data tab with the id prefilled;
 *                             structural cases like tca.citrate_synthase
 *                             skip the bucket with the edit:structural
 *                             note)  4. optional cast.json entry
 *                          (moves test_15_edit_allowed_nodes — count ack)
 *   node -> ending       : set is_ending + suggested ending:<tier> tag +
 *                          stage:* tag + choices []; the BFS runs FIRST —
 *                          an unreachable candidate is BLOCKED with the
 *                          orphan-ending explanation (reachability red
 *                          class) until an inbound edge is added
 *                          (deep-link to a candidate parent's choices).
 *   ending -> non-ending : remove is_ending (absent, never null) + the
 *                          matching ending:<tier> tag; REFUSED while the
 *                          id is in any bad_ending_pool
 *                          (pool_node_not_ending); inbound edges listed.
 *   node -> rng          : weights are added ONLY on tca.shuffle without
 *                          ceremony; on ANY other node the determinism
 *                          acknowledgment is REQUIRED (test 16 breakage:
 *                          test_shuffle_is_the_only_weighted_node pins the
 *                          shuffle node + TestSeededDeterminismDesignB pins
 *                          the seed-42 fate tca.co2_turn2; RESEARCH-DATA
 *                          §1.7 row 4).
 *   node -> starting     : start is a MANIFEST property, not a node
 *                          property — manifest.start is edited via apply()
 *                          with a typed confirmation (the manifest-edit
 *                          acknowledgment flow).
 *
 * ADD NODE (B1): the target-file select offers the 7 manifest files ONLY —
 * a node in an unlisted file does not exist (StoryGraph.load merges
 * manifest.files only; RESEARCH-DATA §1.1). A NEW file is allowed only
 * with the explicit manifest-edit acknowledgment (it appends the file to
 * manifest.files and lands in the viewer's unmapped column 6). The id is
 * validated LIVE: unique across ALL files (duplicate ids across files are
 * the graph.py:76-80 ValueError class) + the dot-convention
 * <seg>.<name> regex ^[a-z0-9_]+\.[a-z0-9_]+$ (warn otherwise). Each
 * initial-type seed composes the recipe fields above; the two-layer
 * validator immediately flags the seeded empty texts — INTENDED (the human
 * fills them next; text_layer_empty surfaces in the strip below).
 *
 * DELETE NODE (B1): the referencing sets are computed FIRST — inbound
 * choice.goto edges, edits.json branch_node targets, cast.json id,
 * edits.json enzyme bucket keyed by the id + the graph edit:enzyme:<id>
 * tag carriers, manifest.start, bad_ending_pool membership (global +
 * per-enzyme) — and the delete is BLOCKED with an itemized explanation
 * list while any exist (the mirror of the integrity gates: dangling_divert
 * rpg/story/validate.py:214-235, dangling_edit_branch / dangling_pool_node
 * rpg/edit_router.py:172-235, coverage rpg/edit_router.py:238-255, the
 * relationship pin tests/test_glucose_content.py:404-449). Offers: re-point
 * the N incoming edges (per-edge target selects, one apply), Data-tab deep
 * links to resolve bucket/cast references first, and — for the manifest
 * start — typing the replacement start id (start + delete land as ONE
 * action). A clean delete runs via apply().
 *
 * COUNT-SHIFT ACKNOWLEDGMENT (Pitfall S2): whenever a pending action moves
 * the pinned counts (nodes 57 / endings 21 / edit-allowed 15), an
 * acknowledgment modal names the exact tests + viewer constants that must
 * be updated in the SAME commit (test_manifest_loads_all_57_nodes,
 * test_reachability_green_all_four_tiers, test_15_edit_allowed_nodes +
 * EXPECTED_NODES / EXPECTED_TIER_COUNTS / EXPECTED_EDIT_ALLOWED,
 * tools/story_graph_viewer.py:96-105) and requires "I understand — allow";
 * the action applies ONLY after that acknowledgment. The 20_validate.js
 * count_shift NOTICE mirrors this post hoc (same trio, same constants).
 * The would-be counts are computed by running the EXACT redo function on a
 * deep clone of the bundle — no second implementation of any mutation.
 *
 * MUTATION DISCIPLINE: every change flows through EDITOR.apply as ONE raw
 * action ({files, redo}) — one undo step + per-file dirty marking —
 * touching ONLY the named fields (the B11 unknown-key contract: the seed
 * shapes are the documented 6-key schema + optional is_ending; tag edits
 * assign the tags field on an edited copy, choice edits mutate the named
 * field in place exactly like the sibling editors). Manifest edits mark
 * "manifest.json" dirty; the Save tab serializes bundle.files + the 4
 * registries only, so THIS panel carries the manifest export (copyable
 * house-style JSON + the exact destination) while the manifest is dirty.
 *
 * STYLE: one classic script, one IIFE, ES5 only (var, no arrow functions,
 * no let/const, no modules) — the emitted-page discipline pinned by
 * tests/test_story_editor_state.py.
 * ========================================================================== */

(function () {
  "use strict";

  // -------------------------------------------------------------------------
  // Frozen constants.
  // -------------------------------------------------------------------------

  // tca.shuffle is the graph's ONLY weighted node (the single seeded-RNG
  // surface, 0.5/0.5 design B). Weights anywhere else = the determinism
  // contract break (test 16). src: tests/test_glucose_content.py:539-557
  var SHUFFLE_NODE = "tca.shuffle";

  // The pinned counts + the same-commit obligations — the SAME trio the
  // 20_validate.js count_shift notice names (one source of truth for the
  // acknowledgment text). src: tests/test_glucose_reachability.py:136,157,264
  // + tools/story_graph_viewer.py:96-105.
  var PINNED_NODES = 57;
  var PINNED_ENDINGS = 21;
  var PINNED_EDIT_ALLOWED = 15;
  var COUNT_SHIFT_TESTS = [
    "test_manifest_loads_all_57_nodes",
    "test_reachability_green_all_four_tiers",
    "test_15_edit_allowed_nodes"
  ];
  var COUNT_SHIFT_CONSTANTS = [
    "EXPECTED_NODES", "EXPECTED_TIER_COUNTS", "EXPECTED_EDIT_ALLOWED"
  ];

  // Router-only restored nodes: zero incoming choice.goto edges is
  // load-bearing — re-point targets exclude them (a re-point INTO them
  // would fire router_only_incoming).
  // src: tests/test_glucose_reachability.py:326-452
  var ROUTER_ONLY_NODES = {
    "gly.pfk_restored": true, "tca.aconitase_restored": true
  };

  // The edit:structural reframe (tag, deliberately NO edits.json bucket).
  // src: tests/test_glucose_content.py:404-449
  var STRUCTURAL_TAG_ENZYME = "tca.citrate_synthase";

  // Live id validation: uniqueness is the graph.py:76-80 ValueError class;
  // the dot-convention regex mirrors the existing id style (warn, not
  // block). src: rpg/story/graph.py:76-80 (duplicate id load error);
  // RESEARCH-DATA §1.1.
  var ID_RE = /^[a-z0-9_]+\.[a-z0-9_]+$/;
  var NEWFILE_RE = /^[a-z0-9_]+\.json$/;

  // The manifest files + their file-aligned stage tags (the ending recipe's
  // suggested stage:* tag). endings.json reuses the parent path's stage
  // (not derivable here) and bad_endings nodes carry NO stage tag (verified
  // against the live data) — both default to "(none)".
  // src: RESEARCH-DATA §1.5 (stage vocabulary + counts).
  var FILE_STAGE_MAP = {
    "intro.json": "stage:intro",
    "glycolysis.json": "stage:glycolysis",
    "pyruvate_branch.json": "stage:pyruvate",
    "tca.json": "stage:tca",
    "etc_atp.json": "stage:etc",
    "endings.json": null,
    "bad_endings.json": null
  };
  var STAGE_OPTIONS = [
    "stage:intro", "stage:glycolysis", "stage:pyruvate",
    "stage:anaerobic", "stage:tca", "stage:etc"
  ];
  var TIERS = ["true", "good", "normal", "bad"];

  // The Save tab cannot serialize the manifest (it saves bundle.files +
  // the 4 registries — 80_save.js fileContentOf); the manifest export box
  // carries the bytes while "manifest.json" is dirty.
  var MANIFEST_FNAME = "manifest.json";
  var MANIFEST_DEST = "data/story_glucose/manifest.json";

  // -------------------------------------------------------------------------
  // Small helpers.
  // -------------------------------------------------------------------------

  function hasOwn(obj, key) {
    return !!obj && Object.prototype.hasOwnProperty.call(obj, key);
  }

  function asArray(value) {
    return Object.prototype.toString.call(value) === "[object Array]"
      ? value : [];
  }

  function trimText(value) {
    return String(value === undefined || value === null ? "" : value)
      .replace(/^\s+|\s+$/g, "");
  }

  function isEndingNode(node) {
    return !!node && node.is_ending !== undefined && node.is_ending !== null;
  }

  function warn(msg) {
    try {
      if (typeof console !== "undefined" && console && console.warn) {
        console.warn(msg);
      }
    } catch (e) { /* never warn about failing to warn */ }
  }

  // -------------------------------------------------------------------------
  // Bundle access (read-only views over EDITOR.state.bundle).
  // -------------------------------------------------------------------------

  function theBundle() {
    var b = EDITOR.state.bundle;
    return (b && b.files) ? b : null;
  }

  function bundleOrder(b) {
    return (b && Object.prototype.toString.call(b.order) ===
      "[object Array]" && b.order.length)
      ? b.order
      : (b && b.files ? Object.keys(b.files) : []);
  }

  function editsEnzymes(b) {
    return (b && b.edits && b.edits.enzymes &&
            typeof b.edits.enzymes === "object") ? b.edits.enzymes : {};
  }

  function castEntries(b) {
    return asArray(b && b.cast && b.cast.enzymes);
  }

  function fileNodeCount(b, fname) {
    var file = b.files ? b.files[fname] : null;
    var nodes = (file && file.nodes && typeof file.nodes === "object")
      ? file.nodes : null;
    var n = 0;
    for (var k in nodes) {
      if (Object.prototype.hasOwnProperty.call(nodes, k)) n++;
    }
    return n;
  }

  function idExists(id) {
    return !!EDITOR.nodeById(id);
  }

  // Non-enumerable id stamp — the same contract as 00_core.js nodeAdd /
  // stampIds: the created node gets a working .id (deriveKind, the node
  // form's id-as-title) while staying JSON-invisible (saved bytes never
  // change; snapshots re-stamp on restore).
  function stampNodeId(n, id) {
    try {
      Object.defineProperty(n, "id", {
        value: id,
        enumerable: false,
        configurable: true,
        writable: true
      });
    } catch (e) { /* display-only degradation; never blocks the edit */ }
  }

  // First existing node id (bundle order) other than `notId` — the scaffold
  // goto default (42_choices's add-scaffold convention: a real target, so
  // the seeded edge never dangles silently).
  function firstOtherId(notId) {
    var b = theBundle();
    if (!b) return "";
    var order = bundleOrder(b);
    for (var i = 0; i < order.length; i++) {
      var file = b.files[order[i]];
      var nodes = (file && file.nodes && typeof file.nodes === "object")
        ? file.nodes : null;
      if (!nodes) continue;
      for (var nid in nodes) {
        if (Object.prototype.hasOwnProperty.call(nodes, nid) &&
            nid !== notId) {
          return nid;
        }
      }
    }
    return "";
  }

  // -------------------------------------------------------------------------
  // B1 — live id validation (the add wizard's per-keystroke check).
  // -------------------------------------------------------------------------

  function checkId(raw) {
    var id = trimText(raw);
    if (!id) {
      return { ok: false, level: "error", id: id, msg: "id required" };
    }
    if (idExists(id)) {
      return { ok: false, level: "error", id: id,
               msg: "DUPLICATE \u2014 already exists in " +
                    EDITOR.fileOfNode(id) +
                    " (duplicate ids across files are the graph.py:76-80 " +
                    "ValueError class)" };
    }
    if (!ID_RE.test(id)) {
      return { ok: true, level: "warn", id: id,
               msg: "unique, but NOT the <seg>.<name> dot-convention " +
                    "(^[a-z0-9_]+\\.[a-z0-9_]+$) \u2014 allowed with this " +
                    "warning" };
    }
    return { ok: true, level: "ok", id: id,
             msg: "unique across all files + dot-convention" };
  }

  // -------------------------------------------------------------------------
  // B1 — delete referencing sets (computed BEFORE any delete; the blocked
  // list is itemized per class). Classes: inbound goto / edits.json
  // branch_node / bad_ending_pool membership / cast.json id / edits.json
  // enzyme bucket + graph edit:enzyme:<id> tag carriers / manifest.start.
  // -------------------------------------------------------------------------

  function computeReferences(id) {
    var b = theBundle();
    var refs = {
      id: id,
      goto: [], branch: [], pool: [], cast: [],
      enzymeBucket: false, tagCarriers: [], start: false,
      total: 0
    };
    if (!b || !id) return refs;

    // 1. inbound choice.goto edges (the dangling_divert class).
    var all = EDITOR.allNodes();
    for (var i = 0; i < all.length; i++) {
      var w = all[i];
      var choices = asArray(w.node ? w.node.choices : null);
      for (var j = 0; j < choices.length; j++) {
        var c = choices[j];
        if (c && typeof c === "object" && c.goto === id) {
          refs.goto.push({ src: w.id, file: w.file, idx: j,
                           label: (c.label === undefined ? "" : c.label) });
        }
      }
    }

    var enzymes = editsEnzymes(b);

    // 2. edits.json branch_node targets (the dangling_edit_branch class).
    for (var eid in enzymes) {
      if (!hasOwn(enzymes, eid)) continue;
      var list = asArray(enzymes[eid] ? enzymes[eid].edits : null);
      for (var k = 0; k < list.length; k++) {
        var entry = list[k];
        if (entry && typeof entry === "object" &&
            entry.branch_node === id) {
          refs.branch.push({ enzyme: eid, idx: k });
        }
      }
    }

    // 3. bad_ending_pool membership, global + per-enzyme (the
    //    dangling_pool_node class).
    var gpool = asArray(b.edits ? b.edits.bad_ending_pool : null);
    if (gpool.indexOf(id) >= 0) refs.pool.push({ pool: "global" });
    for (eid in enzymes) {
      if (!hasOwn(enzymes, eid)) continue;
      var ppool = asArray(enzymes[eid] ? enzymes[eid].bad_ending_pool : null);
      if (ppool.indexOf(id) >= 0) refs.pool.push({ pool: eid });
    }

    // 4. cast.json id (the coverage / relationship classes).
    var cast = castEntries(b);
    for (var m = 0; m < cast.length; m++) {
      if (cast[m] && typeof cast[m] === "object" && cast[m].id === id) {
        refs.cast.push({ idx: m, label: cast[m].label });
      }
    }

    // 5. the edits.json enzyme bucket keyed by the id + the graph
    //    edit:enzyme:<id> tag carriers (the relationship-pin class).
    if (hasOwn(enzymes, id)) refs.enzymeBucket = true;
    var tagValue = "edit:enzyme:" + id;
    for (var a = 0; a < all.length; a++) {
      var tags = asArray(all[a].node ? all[a].node.tags : null);
      if (tags.indexOf(tagValue) >= 0) refs.tagCarriers.push(all[a].id);
    }

    // 6. manifest.start (the graph entry point — a manifest property).
    refs.start = !!(b.manifest && b.manifest.start === id);

    refs.total = refs.goto.length + refs.branch.length + refs.pool.length +
      refs.cast.length + (refs.enzymeBucket ? 1 : 0) +
      refs.tagCarriers.length + (refs.start ? 1 : 0);
    return refs;
  }

  function idInAnyPool(id) {
    var b = theBundle();
    if (!b) return [];
    var hits = [];
    var gpool = asArray(b.edits ? b.edits.bad_ending_pool : null);
    if (gpool.indexOf(id) >= 0) hits.push("global");
    var enzymes = editsEnzymes(b);
    for (var eid in enzymes) {
      if (!hasOwn(enzymes, eid)) continue;
      var pp = asArray(enzymes[eid] ? enzymes[eid].bad_ending_pool : null);
      if (pp.indexOf(id) >= 0) hits.push(eid);
    }
    return hits;
  }

  // -------------------------------------------------------------------------
  // Seeds — the minimal-per-type node shapes (the plan's §1.7 recipe
  // fields; the 6-key schema + optional is_ending; empty texts are
  // EXPECTED and surface as text_layer_empty until the human fills them).
  // -------------------------------------------------------------------------

  function seedNode(type, opts) {
    var o = opts || {};
    var node = {
      text_dramatic: "",
      text_teaching: "",
      claim_ids: [],
      tags: [],
      on_enter: [{ op: "hide_all" }],
      choices: []
    };
    var other = o.otherId || "";
    if (type === "multiple-choices") {
      node.choices = [
        { label: "New choice A", goto: other },
        { label: "New choice B", goto: other }
      ];
    } else if (type === "mutation") {
      // The edit-allowed recipe fields: the tag + the edit:offer choice
      // (goto edit.prompt, tag edit:offer). The edits.json bucket is the
      // post-create handoff (Data tab, id prefilled); structural reframes
      // skip it (the edit:structural note).
      node.tags = ["edit:enzyme:" + (o.id || "")];
      node.choices = [
        { label: "Continue", goto: other },
        { label: "Try to edit " + (o.id || ""), goto: "edit.prompt",
          tags: ["edit:offer"] }
      ];
    } else if (type === "ending") {
      // Endings: choices [] + is_ending + the suggested ending:<tier> tag
      // (+ the file-aligned stage:* tag when one is suggested). Tier comes
      // from is_ending ONLY (the 3 anaerobic endings carry no ending:* tag
      // — the suggested tag is convention, the field is the truth).
      node.is_ending = o.tier || "bad";
      node.tags = ["ending:" + (o.tier || "bad")];
      if (o.stage) node.tags.push(o.stage);
    } else if (type === "rng") {
      // Weighted pair (the tca.shuffle shape: both weighted choices carry
      // rng:weighted). ANY new node is non-shuffle -> the determinism
      // acknowledgment fires at apply time.
      node.choices = [
        { label: "Wheel outcome A", weight: 0.5, goto: other,
          tags: ["rng:weighted"] },
        { label: "Wheel outcome B", weight: 0.5, goto: other,
          tags: ["rng:weighted"] }
      ];
    }
    // type "story": the bare base (the human wires choices next via the
    // Choices section — 0 choices is a legal shape; the single-Continue
    // rule only fires on exactly one "Continue" choice).
    return node;
  }

  // -------------------------------------------------------------------------
  // Count simulation — the EXACT redo function runs on a deep clone, then
  // the pinned trio is recounted. No second implementation of any mutation
  // (the acknowledgment preview can never drift from what applies).
  // -------------------------------------------------------------------------

  function countsOf(b) {
    var nodes = {};
    var order = bundleOrder(b);
    for (var i = 0; i < order.length; i++) {
      var file = b.files ? b.files[order[i]] : null;
      var fnodes = (file && file.nodes && typeof file.nodes === "object")
        ? file.nodes : null;
      if (!fnodes) continue;
      for (var nid in fnodes) {
        if (Object.prototype.hasOwnProperty.call(fnodes, nid)) {
          nodes[nid] = fnodes[nid];
        }
      }
    }
    var nodeCount = 0;
    var tiers = {};
    var editAllowed = {};
    for (var id in nodes) {
      if (!hasOwn(nodes, id)) continue;
      nodeCount++;
      var n = nodes[id];
      if (n && isEndingNode(n)) {
        var t = String(n.is_ending);
        tiers[t] = (hasOwn(tiers, t) ? tiers[t] : 0) + 1;
      }
      var tags = asArray(n ? n.tags : null);
      for (var k = 0; k < tags.length; k++) {
        if (String(tags[k]).indexOf("edit:enzyme:") === 0) {
          editAllowed[id] = true;
          break;
        }
      }
    }
    var endings = 0;
    for (var t2 in tiers) {
      if (hasOwn(tiers, t2)) endings += tiers[t2];
    }
    return { nodes: nodeCount, tiers: tiers, endings: endings,
             editAllowed: editAllowed };
  }

  function tierMapsDiffer(a, b) {
    var ka = Object.keys(a);
    var kb = Object.keys(b);
    if (ka.length !== kb.length) return true;
    for (var i = 0; i < ka.length; i++) {
      if (!hasOwn(b, ka[i]) || a[ka[i]] !== b[ka[i]]) return true;
    }
    return false;
  }

  function idSetsDiffer(a, b) {
    var ka = Object.keys(a);
    var kb = Object.keys(b);
    if (ka.length !== kb.length) return true;
    for (var i = 0; i < ka.length; i++) {
      if (!hasOwn(b, ka[i])) return true;
    }
    return false;
  }

  function simulateCounts(action) {
    var b = theBundle();
    if (!b) return { changed: false };
    var before = countsOf(b);
    var clone;
    try {
      clone = JSON.parse(JSON.stringify({ files: b.files,
                                          manifest: b.manifest }));
    } catch (e) {
      return { changed: false, error: "clone failed: " + String(e) };
    }
    try {
      action.redo(clone);
    } catch (e) {
      return { changed: false, error: "preview failed: " + String(e) };
    }
    var after = countsOf(clone);
    var changed = before.nodes !== after.nodes ||
      before.endings !== after.endings ||
      tierMapsDiffer(before.tiers, after.tiers) ||
      idSetsDiffer(before.editAllowed, after.editAllowed);
    var added = [];
    var removed = [];
    var id;
    for (id in after.editAllowed) {
      if (hasOwn(after.editAllowed, id) && !hasOwn(before.editAllowed, id)) {
        added.push(id);
      }
    }
    for (id in before.editAllowed) {
      if (hasOwn(before.editAllowed, id) &&
          !hasOwn(after.editAllowed, id)) {
        removed.push(id);
      }
    }
    return {
      changed: changed,
      nodes: { old: before.nodes, new: after.nodes },
      endings: { old: before.endings, new: after.endings },
      tiers: { old: before.tiers, new: after.tiers },
      editAllowed: { oldCount: Object.keys(before.editAllowed).length,
                     newCount: Object.keys(after.editAllowed).length,
                     added: added, removed: removed }
    };
  }

  // -------------------------------------------------------------------------
  // Orphan guard (the make-ending recipe): the BFS runs on the WOULD-BE
  // state BEFORE anything applies — an unreachable candidate ending is
  // BLOCKED (reachability red class) until an inbound edge is added.
  // Semantics mirror EDITOR.bfsReachable exactly (goto edges ONLY; cond and
  // weight ignored — the Python gate parity, rpg/story/validate.py:167-207).
  // -------------------------------------------------------------------------

  function endingWouldBeOrphan(fname, id, tier) {
    var b = theBundle();
    if (!b) return { orphan: false };
    var clone = JSON.parse(JSON.stringify({ files: b.files,
                                            manifest: b.manifest }));
    var file = clone.files ? clone.files[fname] : null;
    var node = (file && file.nodes) ? file.nodes[id] : null;
    if (!node) return { orphan: false };
    node.is_ending = tier;
    node.choices = [];
    var before = (typeof EDITOR.bfsReachable === "function")
      ? EDITOR.bfsReachable(b) : null;
    var after = (typeof EDITOR.bfsReachable === "function")
      ? EDITOR.bfsReachable(clone) : null;
    if (!after) return { orphan: false };
    var orphan = !hasOwn(after.reachable, id);
    // Downstream impact: endings newly unreachable because this node's
    // outbound choices were cleared (informational — the validator flags
    // them post hoc; the plan's BLOCK is about the candidate itself).
    var newly = [];
    if (after.unreachableEndings && after.unreachableEndings.length) {
      var beforeUn = {};
      if (before) {
        for (var i = 0; i < before.unreachableEndings.length; i++) {
          beforeUn[before.unreachableEndings[i]] = true;
        }
      }
      for (var j = 0; j < after.unreachableEndings.length; j++) {
        var eid = after.unreachableEndings[j];
        if (!hasOwn(beforeUn, eid) && eid !== id) newly.push(eid);
      }
    }
    return { orphan: orphan, newlyUnreachable: newly };
  }

  // Candidate parents for the orphan deep-link: currently reachable,
  // non-ending nodes (adding an inbound choice from one of them makes the
  // candidate ending reachable).
  function candidateParents(excludeId) {
    var b = theBundle();
    if (!b || typeof EDITOR.bfsReachable !== "function") return [];
    var rep = EDITOR.bfsReachable(b);
    var out = [];
    var all = EDITOR.allNodes();
    for (var i = 0; i < all.length; i++) {
      var w = all[i];
      if (w.id === excludeId) continue;
      if (!hasOwn(rep.reachable, w.id)) continue;
      if (isEndingNode(w.node)) continue;
      out.push(w.id);
    }
    out.sort();
    return out;
  }

  // -------------------------------------------------------------------------
  // Module state (transient UI bookkeeping; the raw bundle stays the only
  // source of truth — every state here rebuilds from it or dies with the
  // overlay).
  // -------------------------------------------------------------------------

  var refs = { section: null, toolbar: null, overlay: null, built: false };
  var wizardState = null;
  // {open, file, newFile, newFileAck, id, seed, tier, stage, orphanAck}
  var deleteState = null;
  // {open, id, fname, refs, repoint, startReplacement}
  var recipeState = null;
  // {kind: edit | ending | start | rng | unending, ...}
  var ackState = null;      // {label, action, shifts, determinism, after}
  var handoff = null;       // {bucketId} — the post-recipe Data-tab handoff
  var resultNote = null;    // transient section note

  // -------------------------------------------------------------------------
  // The ONE mutation gate: applyWithAck routes EVERY lifecycle action —
  // count-moving actions and weights-outside-shuffle REQUIRE the
  // acknowledgment modal; the action applies ONLY from the modal's
  // "I understand — allow" handler (ackAllow).
  // -------------------------------------------------------------------------

  function applyWithAck(action, label, opts) {
    var needDet = !!(opts && opts.determinism);
    var shifts = simulateCounts(action);
    if (!shifts.changed && !needDet) {
      EDITOR.apply(action);
      return true;
    }
    ackState = { label: label, action: action, shifts: shifts,
                 determinism: needDet };
    renderLifecycle();
    return false;
  }

  function ackAllow() {
    if (!ackState) return;
    var st = ackState;
    ackState = null;
    EDITOR.apply(st.action);
    if (typeof st.after === "function") {
      st.after();
    }
    renderLifecycle();
  }

  function ackCancel() {
    ackState = null;
    renderLifecycle();
  }

  // -------------------------------------------------------------------------
  // Selection + rendering helpers.
  // -------------------------------------------------------------------------

  function selectedNode() {
    var id = EDITOR.state.sel;
    if (!id) return null;
    var fname = EDITOR.fileOfNode(id);
    var node = EDITOR.nodeById(id);
    return (fname && node) ? { id: id, fname: fname, node: node } : null;
  }

  function esc(s) {
    return EDITOR.esc(s);
  }

  function validatorStripHtml() {
    var v = EDITOR._lastValidation;
    if (!v && typeof EDITOR.validateCurrent === "function") {
      try { v = EDITOR.validateCurrent(); } catch (e) { v = null; }
    }
    if (!v) return "";
    var html = "<div class=\"lc-strip\">" +
      "validator: <b>" + v.errors.length + "</b> error(s), <b>" +
      v.notices.length + "</b> notice(s)";
    for (var i = 0; i < v.notices.length; i++) {
      if (v.notices[i] && v.notices[i].kind === "count_shift") {
        html += " <span class=\"lc-chip lc-chip-warn\" title=\"" +
          esc(v.notices[i].detail) + "\">count_shift: pinned counts " +
          "moved \u2014 the acknowledgment obligations apply</span>";
      }
    }
    html += " <span class=\"lc-strip-note\">empty-text errors on a freshly " +
      "seeded node are EXPECTED \u2014 fill the two layers in the Identity " +
      "section above</span></div>";
    return html;
  }

  function manifestNoticeHtml() {
    var b = theBundle();
    if (!b || !EDITOR.state.dirty[MANIFEST_FNAME]) return "";
    var text = "";
    if (typeof EDITOR.housy !== "undefined" &&
        typeof EDITOR.housy.stringify === "function") {
      text = EDITOR.housy.stringify(b.manifest);
    } else {
      text = JSON.stringify(b.manifest, null, 2);
    }
    var html = "<div class=\"lc-manifest\">" +
      "<b>manifest.json has in-memory edits.</b> The Save tab serializes " +
      "the story files + the 4 registries only \u2014 the manifest row " +
      "will read \u201cNo in-memory content found\u201d. Copy the new " +
      "manifest below and place it over <code>" + esc(MANIFEST_DEST) +
      "</code> (the dirty dot stays until the next folder re-pick / " +
      "reload \u2014 the core dirty re-derivation re-marks files it " +
      "cannot re-diff)." +
      "<textarea class=\"lc-manifest-ta\" readonly " +
      "data-lc-manifest=\"1\">" + esc(text) + "</textarea>" +
      "<button type=\"button\" class=\"lc-btn\" " +
      "data-lc-act=\"manifest-copy\">Copy manifest JSON</button> " +
      "<span class=\"lc-live\" data-lc-live=\"manifest-copy-msg\"></span>" +
      "</div>";
    return html;
  }

  function nodeTypeSectionHtml(sel) {
    var node = sel.node;
    var kind = EDITOR.deriveKind(node);
    var tier = EDITOR.endingTier(node);
    var b = theBundle();
    var start = (b && b.manifest && b.manifest.start !== undefined)
      ? b.manifest.start : null;
    var html = "<div class=\"lc-kind\">node type (DERIVED \u2014 there is " +
      "NO stored node_type field): <b>" + esc(kind) + "</b>" +
      (tier ? " <span class=\"lc-chip\">tier " + esc(tier) +
        " (from is_ending)</span>" : "") +
      (start === sel.id
        ? " <span class=\"lc-chip lc-chip-start\">manifest.start</span>" : "") +
      "</div>";
    if (kind === "phase8-stub" || kind === "edit-prompt" ||
        kind === "restored") {
      html += "<div class=\"lc-note\">Special shape (" + esc(kind) +
        ") \u2014 the derived kind is pinned by special id; type " +
        "transitions are not offered. Edit the fields via the sections " +
        "above.</div>";
      return html;
    }
    html += "<div class=\"lc-recipes\">";
    html += "<div class=\"lc-recipes-title\">Node type recipes " +
      "(RESEARCH-DATA \u00A71.7 \u2014 transitions COMPOSE the underlying " +
      "tag/choice/manifest changes):</div>";
    if (kind !== "edit-allowed" && !tier) {
      html += "<button type=\"button\" class=\"lc-btn\" " +
        "data-lc-act=\"recipe-edit\">Make edit-allowed (mutation node)" +
        "</button>";
    }
    if (!tier) {
      html += "<button type=\"button\" class=\"lc-btn\" " +
        "data-lc-act=\"recipe-ending\">Make ending</button>";
    } else {
      html += "<button type=\"button\" class=\"lc-btn\" " +
        "data-lc-act=\"recipe-unending\">Un-make ending</button>";
    }
    html += "<button type=\"button\" class=\"lc-btn\" " +
      "data-lc-act=\"recipe-start\">Make starting node</button>";
    if (kind !== "rng") {
      html += "<button type=\"button\" class=\"lc-btn\" " +
        "data-lc-act=\"recipe-rng\">Make rng (weighted)</button>";
    } else if (sel.id === SHUFFLE_NODE) {
      html += "<span class=\"lc-note-inline\">This IS " + SHUFFLE_NODE +
        " \u2014 add/adjust weights in the Choices section above (no " +
        "ceremony on the shuffle node).</span>";
    }
    html += "</div>";
    if (handoff) {
      html += "<div class=\"lc-handoff\"><b>Next step:</b> create the " +
        "edits.json bucket <code>" + esc(handoff.bucketId) + "</code> " +
        "(the tag now needs a bucket \u2014 the relationship pin fires " +
        "until it exists). " +
        "<button type=\"button\" class=\"lc-btn\" data-lc-act=\"data-bucket:" +
        esc(handoff.bucketId) + "\">Open the Data tab \u2014 bucket id " +
        "prefilled</button> " +
        "<span class=\"lc-note-inline\">Structural reframe (no disease " +
        "point mutant)? Skip the bucket and add the edit:structural tag " +
        "instead \u2014 the " + STRUCTURAL_TAG_ENZYME + " precedent.</span>" +
        " <button type=\"button\" class=\"lc-btn lc-btn-small\" " +
        "data-lc-act=\"handoff-dismiss\">dismiss</button></div>";
    }
    return html;
  }

  function renderSection() {
    var section = refs.section;
    if (!section) return;
    var b = theBundle();
    if (!b) {
      section.innerHTML = "";
      return;
    }
    var sel = selectedNode();
    var html = "";
    html += "<h3>Lifecycle</h3>";
    html += validatorStripHtml();
    html += manifestNoticeHtml();
    if (resultNote) {
      html += "<div class=\"lc-note lc-note-ok\">" + esc(resultNote) +
        "</div>";
    }
    if (sel) {
      html += nodeTypeSectionHtml(sel);
    } else {
      html += "<div class=\"lc-note\">Select a node in the graph for the " +
        "delete guard + the type recipes \u2014 or add a node from the " +
        "toolbar.</div>";
    }
    section.innerHTML = html;
  }

  function renderToolbar() {
    var bar = refs.toolbar;
    if (!bar) return;
    var b = theBundle();
    if (!b) {
      bar.innerHTML = "";
      bar.style.display = "none";
      return;
    }
    bar.style.display = "";
    var sel = selectedNode();
    var html = "<div class=\"lc-toolbar-title\">Lifecycle</div>";
    html += "<button type=\"button\" class=\"lc-btn lc-btn-primary\" " +
      "data-lc-act=\"add-open\" title=\"Add a node (B1) \u2014 file " +
      "select, live id validation, type seed\">\uFF0B node</button>";
    if (sel) {
      html += "<button type=\"button\" class=\"lc-btn lc-btn-danger\" " +
        "data-lc-act=\"delete-open\" title=\"Delete " + esc(sel.id) +
        " (B1 \u2014 reference-guarded)\">\u2715 delete</button>";
      html += "<button type=\"button\" class=\"lc-btn\" " +
        "data-lc-act=\"recipe-menu\" title=\"Type recipes for " +
        esc(sel.id) + " (B2) \u2014 scroll to the node form\">type " +
        "\u25B8</button>";
      html += "<div class=\"lc-toolbar-sel\">" + esc(sel.id) + "</div>";
    } else {
      html += "<div class=\"lc-toolbar-hint\">select a node in the graph " +
        "for delete + recipes</div>";
    }
    bar.innerHTML = html;
  }

  // -------------------------------------------------------------------------
  // Overlay renderers: wizard / delete guard / recipe panels / ack modal.
  // The ack modal renders INSTEAD of everything (highest priority).
  // -------------------------------------------------------------------------

  function dialogFrame(title, inner, extraClass) {
    return "<div class=\"lc-dialog " + (extraClass || "") + "\">" +
      "<div class=\"lc-dialog-head\"><span class=\"lc-dialog-title\">" +
      esc(title) + "</span>" +
      "<button type=\"button\" class=\"lc-btn lc-btn-small\" " +
      "data-lc-act=\"overlay-close\" title=\"Close\">\u2715</button></div>" +
      inner + "</div>";
  }

  function fileOptions(selected) {
    var b = theBundle();
    var order = bundleOrder(b);
    var html = "";
    for (var i = 0; i < order.length; i++) {
      var fname = order[i];
      html += "<option value=\"" + esc(fname) + "\"" +
        (fname === selected ? " selected" : "") + ">" + esc(fname) +
        " (" + fileNodeCount(b, fname) + " nodes)</option>";
    }
    html += "<option value=\"__newfile__\"" +
      (selected === "__newfile__" ? " selected" : "") +
      ">(new file \u2014 manifest edit required)</option>";
    return html;
  }

  function seedOptions(selected) {
    var types = [
      ["story", "story (bare beat \u2014 wire choices next)"],
      ["multiple-choices", "multiple-choices (2 scaffolds)"],
      ["mutation", "mutation (edit-allowed recipe seed)"],
      ["ending", "ending (is_ending + tier/stage tags)"],
      ["rng", "rng (weighted pair \u2014 determinism ack)"]
    ];
    var html = "";
    for (var i = 0; i < types.length; i++) {
      html += "<option value=\"" + types[i][0] + "\"" +
        (types[i][0] === selected ? " selected" : "") + ">" +
        esc(types[i][1]) + "</option>";
    }
    return html;
  }

  function tierOptions(selected) {
    var html = "";
    for (var i = 0; i < TIERS.length; i++) {
      html += "<option value=\"" + TIERS[i] + "\"" +
        (TIERS[i] === selected ? " selected" : "") + ">" + TIERS[i] +
        "</option>";
    }
    return html;
  }

  function stageOptions(fname, selected) {
    var suggested = hasOwn(FILE_STAGE_MAP, fname) ? FILE_STAGE_MAP[fname]
      : null;
    var html = "<option value=\"\"" +
      (!selected ? " selected" : "") + ">(none)</option>";
    for (var i = 0; i < STAGE_OPTIONS.length; i++) {
      var s = STAGE_OPTIONS[i];
      html += "<option value=\"" + s + "\"" +
        (s === selected ? " selected" : "") + ">" + s +
        (s === suggested ? " (suggested for " + esc(fname) + ")" : "") +
        "</option>";
    }
    return html;
  }

  function idVerdictText(w) {
    var v = checkId(w.id);
    if (v.level === "ok") return "\u2713 " + v.msg;
    if (v.level === "warn") return "\u26A0 " + v.msg;
    return "\u2717 " + v.msg;
  }

  function createBlocked(w) {
    var v = checkId(w.id);
    if (!v.ok) return true;
    if (w.file === "__newfile__") {
      if (!w.newFileAck) return true;
      var nf = trimText(w.newFile);
      if (!NEWFILE_RE.test(nf)) return true;
      var b = theBundle();
      if (b && b.files && hasOwn(b.files, nf)) return true;
    }
    if (w.seed === "ending" && !w.orphanAck) return true;
    return false;
  }

  function wizardOverlayHtml() {
    var w = wizardState;
    var inner = "";
    inner += "<div class=\"lc-field\"><label>Target file</label>" +
      "<select data-lc-field=\"file\">" + fileOptions(w.file) + "</select>" +
      "<div class=\"lc-hint\">The 7 manifest files only \u2014 a node in " +
      "an unlisted file does not exist (StoryGraph.load merges " +
      "manifest.files only; RESEARCH-DATA \u00A71.1).</div></div>";
    if (w.file === "__newfile__") {
      inner += "<div class=\"lc-field\"><label>New file name</label>" +
        "<input type=\"text\" data-lc-field=\"newfile\" value=\"" +
        esc(w.newFile) + "\" placeholder=\"new_segment.json\">" +
        "<div class=\"lc-hint\">A NEW file needs a manifest edit and lands " +
        "in the viewer's UNMAPPED column 6 (the Phase-8 stubs column) " +
        "\u2014 RESEARCH-DATA \u00A71.1.</div>" +
        "<label class=\"lc-ack\"><input type=\"checkbox\" " +
        "data-lc-field=\"newfile-ack\"" +
        (w.newFileAck ? " checked" : "") + "> I understand: this appends " +
        "the file to manifest.files (a manifest edit) and the viewer maps " +
        "it to unmapped column 6.</label></div>";
    }
    inner += "<div class=\"lc-field\"><label>Node id</label>" +
      "<input type=\"text\" data-lc-field=\"id\" value=\"" + esc(w.id) +
      "\" placeholder=\"tca.new_node\">" +
      "<div class=\"lc-live\" data-lc-live=\"idverdict\">" +
      esc(idVerdictText(w)) + "</div></div>";
    inner += "<div class=\"lc-field\"><label>Initial type seed</label>" +
      "<select data-lc-field=\"seed\">" +
      seedOptions(w.seed) + "</select>" +
      "<div class=\"lc-hint\">There is NO stored node_type \u2014 the seed " +
      "COMPOSES the \u00A71.7 recipe fields (tags / choices / is_ending). " +
      "The seeded empty texts surface as text_layer_empty errors \u2014 " +
      "intended; fill them next.</div></div>";
    if (w.seed === "ending") {
      inner += "<div class=\"lc-field\"><label>Ending tier</label>" +
        "<select data-lc-field=\"tier\">" + tierOptions(w.tier) +
        "</select></div>";
      inner += "<div class=\"lc-field\"><label>Stage tag</label>" +
        "<select data-lc-field=\"stage\">" + stageOptions(w.file, w.stage) +
        "</select>" +
        "<div class=\"lc-hint\">bad_endings nodes carry NO stage tag; " +
        "endings.json reuses the parent path's stage (not derivable) " +
        "\u2014 both default to (none).</div></div>";
      inner += "<label class=\"lc-ack\"><input type=\"checkbox\" " +
        "data-lc-field=\"orphan-ack\"" +
        (w.orphanAck ? " checked" : "") + "> I understand: a brand-new " +
        "ending has NO inbound edge yet \u2014 the reachability gate goes " +
        "RED (unreachable_ending) until a parent choice points here. Wire " +
        "the parent next (the Make-ending recipe on an EXISTING reachable " +
        "node hard-blocks instead).</label>";
    }
    if (w.seed === "mutation") {
      inner += "<div class=\"lc-hint\">Seeds the edit-allowed recipe: the " +
        "edit:enzyme:&lt;id&gt; tag + the edit:offer choice (goto " +
        "edit.prompt). After create: build the edits.json bucket (Data " +
        "tab, id prefilled) \u2014 the relationship pin stays RED until " +
        "the bucket exists. Structural reframe? Skip the bucket, add " +
        "edit:structural (the " + STRUCTURAL_TAG_ENZYME +
        " precedent).</div>";
    }
    if (w.seed === "rng") {
      inner += "<div class=\"lc-hint\">Seeds a 0.5/0.5 weighted pair. ANY " +
        "new node is not " + SHUFFLE_NODE + " \u2014 the determinism " +
        "acknowledgment (test 16) fires at create.</div>";
    }
    if (w.seed === "multiple-choices") {
      inner += "<div class=\"lc-hint\">Seeds two scaffold choices into the " +
        "first existing node \u2014 retarget them in the Choices section " +
        "after create.</div>";
    }
    inner += "<div class=\"lc-dialog-actions\">" +
      "<button type=\"button\" class=\"lc-btn lc-btn-primary\" " +
      "data-lc-act=\"create\"" +
      (createBlocked(w) ? " disabled" : "") + ">Create node</button>" +
      "<button type=\"button\" class=\"lc-btn\" " +
      "data-lc-act=\"overlay-close\">Cancel</button></div>";
    return "<div class=\"lc-overlay\">" +
      dialogFrame("Add node", inner) + "</div>";
  }

  // -------------------------------------------------------------------------
  // Delete overlay.
  // -------------------------------------------------------------------------

  function repointOptions(selected) {
    var all = EDITOR.allNodes();
    var html = "<option value=\"\">(choose target)</option>";
    var deletedId = deleteState ? deleteState.id : null;
    for (var i = 0; i < all.length; i++) {
      var nid = all[i].id;
      if (nid === deletedId) continue;
      if (ROUTER_ONLY_NODES[nid]) continue; // router-only: no incoming edges
      html += "<option value=\"" + esc(nid) + "\"" +
        (nid === selected ? " selected" : "") + ">" + esc(nid) +
        (isEndingNode(all[i].node) ? " [ending]" : "") + "</option>";
    }
    return html;
  }

  function repointReady(d) {
    if (!d.refs.goto.length) return false;
    for (var i = 0; i < d.refs.goto.length; i++) {
      var g = d.refs.goto[i];
      var target = d.repoint[g.src + ":" + g.idx];
      if (!target || !idExists(target) || target === d.id) return false;
    }
    return true;
  }

  function startVerdictText(d) {
    var typed = trimText(d.startReplacement);
    if (!typed) return "";
    if (typed === d.id) {
      return "\u2717 the replacement cannot be the node being deleted";
    }
    if (!idExists(typed)) return "\u2717 not an existing node id";
    return "\u2713 will become manifest.start";
  }

  function deleteUnblocked(d) {
    var r = d.refs;
    if (r.goto.length) return false;
    if (r.branch.length) return false;
    if (r.pool.length) return false;
    if (r.cast.length) return false;
    if (r.enzymeBucket) return false;
    if (r.tagCarriers.length) return false;
    if (r.start) {
      var typed = trimText(d.startReplacement);
      if (!typed || typed === d.id || !idExists(typed)) return false;
    }
    return true;
  }

  function deleteOverlayHtml() {
    var d = deleteState;
    var r = d.refs;
    var inner = "";
    if (r.total === 0) {
      inner += "<div class=\"lc-note lc-note-ok\">\u2713 No references " +
        "\u2014 a clean delete. Removing any node moves the pinned " +
        "57-count, so the count-shift acknowledgment fires at apply.</div>" +
        "<div class=\"lc-dialog-actions\">" +
        "<button type=\"button\" class=\"lc-btn lc-btn-danger\" " +
        "data-lc-act=\"delete-confirm\">Delete " + esc(d.id) + "</button>" +
        "<button type=\"button\" class=\"lc-btn\" " +
        "data-lc-act=\"overlay-close\">Cancel</button></div>";
      return "<div class=\"lc-overlay\">" +
        dialogFrame("Delete node \u2014 " + d.id, inner) + "</div>";
    }

    inner += "<div class=\"lc-note lc-note-err\">BLOCKED \u2014 " + r.total +
      " reference(s) point at <b>" + esc(d.id) + "</b>. Resolve them first " +
      "(the mirrors of the integrity gates: dangling_divert, " +
      "dangling_edit_branch, dangling_pool_node, coverage, the " +
      "relationship pin):</div><ul class=\"lc-reflist\">";

    if (r.goto.length) {
      inner += "<li><b>Inbound choice.goto (" + r.goto.length +
        ")</b> \u2014 deleting would fire dangling_divert " +
        "(rpg/story/validate.py:214-235):";
      for (var i = 0; i < r.goto.length; i++) {
        var g = r.goto[i];
        inner += "<div class=\"lc-refrow\">" + esc(g.src) +
          " choice #" + g.idx +
          (g.label ? " (\u201C" + esc(g.label) + "\u201D)" : "") +
          " \u2192 re-point to <select data-lc-field=\"repoint:" +
          esc(g.src) + ":" + g.idx + "\">" +
          repointOptions(d.repoint[g.src + ":" + g.idx]) + "</select></div>";
      }
      inner += "</li>";
    }
    if (r.branch.length) {
      inner += "<li><b>edits.json branch_node (" + r.branch.length +
        ")</b> \u2014 deleting would fire dangling_edit_branch " +
        "(rpg/edit_router.py:172-235): ";
      var parts = [];
      for (var k = 0; k < r.branch.length; k++) {
        parts.push(esc(r.branch[k].enzyme) + " entry #" + r.branch[k].idx);
      }
      inner += parts.join("; ") + " \u2014 re-point or delete the entry " +
        "in the <b>Data tab</b> first.</li>";
    }
    if (r.pool.length) {
      inner += "<li><b>bad_ending_pool membership (" + r.pool.length +
        ")</b> \u2014 deleting would fire dangling_pool_node: ";
      var pools = [];
      for (var p = 0; p < r.pool.length; p++) {
        pools.push(r.pool[p].pool === "global" ? "the GLOBAL pool"
                                               : r.pool[p].pool);
      }
      inner += pools.join(", ") + " \u2014 remove the id from the pool in " +
        "the <b>Data tab</b> first.</li>";
    }
    if (r.cast.length) {
      inner += "<li><b>cast.json id (" + r.cast.length + ")</b> \u2014 the " +
        "cast entry would dangle the coverage gate: ";
      for (var c = 0; c < r.cast.length; c++) {
        inner += "entry #" + r.cast[c].idx +
          (r.cast[c].label ? " (" + esc(r.cast[c].label) + ")" : "");
      }
      inner += " \u2014 delete the cast entry in the <b>Data tab</b> " +
        "first (its bucket delete refuses while cast lists the id).</li>";
    }
    if (r.enzymeBucket) {
      inner += "<li><b>edits.json bucket</b> keyed <code>" + esc(d.id) +
        "</code> \u2014 the enzyme id IS this node id. Delete the bucket " +
        "in the <b>Data tab</b> first (it refuses while cast.json still " +
        "lists the id \u2014 coverage).</li>";
    }
    if (r.tagCarriers.length) {
      inner += "<li><b>edit:enzyme:" + esc(d.id) + " tag carriers (" +
        r.tagCarriers.length + ")</b>: " +
        r.tagCarriers.map(esc).join(", ") + " \u2014 the relationship pin " +
        "(cast \u2286 edits == tags \u2212 {" + STRUCTURAL_TAG_ENZYME +
        "}) needs tag/bucket/cast consistent. Remove the tag on the " +
        "carrier node(s) via the Identity section first: ";
      for (var t = 0; t < r.tagCarriers.length; t++) {
        inner += "<button type=\"button\" class=\"lc-btn lc-btn-small\" " +
          "data-lc-act=\"select-node:" + esc(r.tagCarriers[t]) + "\">" +
          esc(r.tagCarriers[t]) + "</button> ";
      }
      inner += "</li>";
    }
    if (r.start) {
      inner += "<li><b>manifest.start</b> \u2014 <code>" + esc(d.id) +
        "</code> IS the graph entry point (a manifest property, not a " +
        "node property). Type the replacement start id; start-change + " +
        "delete land as ONE action: <input type=\"text\" " +
        "data-lc-field=\"start-replacement\" value=\"" +
        esc(d.startReplacement) + "\" placeholder=\"intro.preface\">" +
        "<span class=\"lc-live\" data-lc-live=\"startverdict\">" +
        esc(startVerdictText(d)) + "</span></li>";
    }
    inner += "</ul>";
    inner += "<div class=\"lc-hint\">Or delete the pointing CHOICE itself " +
      "in the parent's Choices section (edges are choices).</div>";
    inner += "<div class=\"lc-dialog-actions\">" +
      "<button type=\"button\" class=\"lc-btn\" data-lc-act=\"data-tab\">" +
      "Open the Data tab (buckets / cast / pools)</button>" +
      "<button type=\"button\" class=\"lc-btn lc-btn-primary\" " +
      "data-lc-act=\"repoint-apply\"" +
      (repointReady(d) ? "" : " disabled") + ">" +
      "Re-point " + r.goto.length + " incoming edge(s) \u2192</button>" +
      "<button type=\"button\" class=\"lc-btn lc-btn-danger\" " +
      "data-lc-act=\"delete-confirm\"" +
      (deleteUnblocked(d) ? "" : " disabled") + ">Delete</button>" +
      "<button type=\"button\" class=\"lc-btn\" " +
      "data-lc-act=\"overlay-close\">Cancel</button></div>";
    return "<div class=\"lc-overlay\">" +
      dialogFrame("Delete node \u2014 " + d.id, inner) + "</div>";
  }

  // -------------------------------------------------------------------------
  // Recipe overlays (B2) + their verdict helpers.
  // -------------------------------------------------------------------------

  function tagVerdictText(r) {
    var tagId = trimText(r.tagId);
    if (!tagId) return "\u2717 tag id required";
    var enzymes = editsEnzymes(theBundle());
    if (hasOwn(enzymes, tagId)) {
      return "\u25CB binding to the EXISTING bucket " + tagId +
        " (legal \u2014 the relationship pin already holds)";
    }
    return "\u25CB new bucket id " + tagId +
      " \u2014 the relationship pin stays RED (tag with no bucket) until " +
      "the bucket is created in the Data tab";
  }

  function editRecipeHtml(r) {
    var sel = selectedNode();
    var inner = "";
    inner += "<div class=\"lc-hint\">The \u00A71.7 edit-allowed recipe " +
      "\u2014 steps 1+2 apply as ONE action (tag + edit:offer choice); " +
      "step 3 (the edits.json bucket) hands off to the Data tab; step 4 " +
      "(cast entry) is optional there too.</div>";
    inner += "<div class=\"lc-field\"><label>edit:enzyme:&lt;id&gt; tag " +
      "value (defaults to the node id \u2014 the tca.shuffle \u2192 " +
      "tca.aconitase re-binding precedent allows an existing bucket " +
      "id)</label>" +
      "<input type=\"text\" data-lc-field=\"tag-id\" value=\"" +
      esc(r.tagId) + "\">" +
      "<div class=\"lc-live\" data-lc-live=\"tagverdict\">" +
      esc(tagVerdictText(r)) + "</div></div>";
    if (r.error) {
      inner += "<div class=\"lc-note lc-note-err\">" + esc(r.error) +
        "</div>";
    }
    inner += "<div class=\"lc-dialog-actions\">" +
      "<button type=\"button\" class=\"lc-btn lc-btn-primary\" " +
      "data-lc-act=\"recipe-edit-apply\"" +
      (r.error ? " disabled" : "") + ">Apply: add tag + edit:offer " +
      "choice</button>" +
      "<button type=\"button\" class=\"lc-btn\" " +
      "data-lc-act=\"overlay-close\">Cancel</button></div>";
    return "<div class=\"lc-overlay\">" +
      dialogFrame("Make edit-allowed \u2014 " + (sel ? sel.id : ""), inner) +
      "</div>";
  }

  function endingRecipeHtml(r) {
    var inner = "";
    if (r.blocked) {
      inner += "<div class=\"lc-note lc-note-err\">ORPHAN-ENDING BLOCK: " +
        esc(r.id) + " would be UNREACHABLE from manifest.start (the BFS " +
        "follows choice.goto only \u2014 rpg/story/validate.py:167-207). " +
        "The reachability gate is RED (unreachable_ending) until an " +
        "inbound edge is added. Wire a parent choice first \u2014 " +
        "candidate parents (reachable, non-ending):</div><div " +
        "class=\"lc-parents\">";
      var caps = r.candidates.slice(0, 12);
      for (var i = 0; i < caps.length; i++) {
        inner += "<button type=\"button\" class=\"lc-btn lc-btn-small\" " +
          "data-lc-act=\"pick-parent:" + esc(caps[i]) + "\">" +
          esc(caps[i]) + "</button> ";
      }
      if (r.candidates.length > caps.length) {
        inner += "<span class=\"lc-note-inline\">+" +
          (r.candidates.length - caps.length) + " more (select any " +
          "reachable node in the graph)</span>";
      }
      inner += "</div><div class=\"lc-dialog-actions\">" +
        "<button type=\"button\" class=\"lc-btn\" " +
        "data-lc-act=\"overlay-close\">Close</button></div>";
      return "<div class=\"lc-overlay\">" +
        dialogFrame("Make ending \u2014 blocked", inner) + "</div>";
    }
    inner += "<div class=\"lc-hint\">Sets is_ending + the suggested " +
      "ending:&lt;tier&gt; tag + the stage:* tag, and clears choices [] " +
      "(all 21 endings carry choices: []). The BFS runs FIRST \u2014 an " +
      "unreachable candidate is BLOCKED.</div>";
    inner += "<div class=\"lc-field\"><label>Ending tier (is_ending \u2014 " +
      "the tier TRUTH; the ending:* tag is convention)</label>" +
      "<select data-lc-field=\"tier\">" + tierOptions(r.tier) +
      "</select></div>";
    inner += "<div class=\"lc-field\"><label>Stage tag</label>" +
      "<select data-lc-field=\"stage\">" + stageOptions(r.fname, r.stage) +
      "</select></div>";
    if (r.clearCount > 0) {
      inner += "<div class=\"lc-note lc-note-warn\">" + r.clearCount +
        " existing choice(s) will be CLEARED (endings carry choices []) " +
        "\u2014 a browser confirm asks before the action is built.</div>";
    }
    if (r.newlyUnreachable && r.newlyUnreachable.length) {
      inner += "<div class=\"lc-note lc-note-warn\">Downstream impact: " +
        "clearing this node's choices makes " + r.newlyUnreachable.length +
        " existing ending(s) unreachable (" +
        r.newlyUnreachable.map(esc).join(", ") +
        ") \u2014 the validator flags unreachable_ending post hoc; " +
        "rewire them or pick a different anchor.</div>";
    }
    inner += "<div class=\"lc-dialog-actions\">" +
      "<button type=\"button\" class=\"lc-btn lc-btn-primary\" " +
      "data-lc-act=\"recipe-ending-apply\">Apply: make ending</button>" +
      "<button type=\"button\" class=\"lc-btn\" " +
      "data-lc-act=\"overlay-close\">Cancel</button></div>";
    return "<div class=\"lc-overlay\">" +
      dialogFrame("Make ending \u2014 " + r.id, inner) + "</div>";
  }

  function startCandidates(selected) {
    var all = EDITOR.allNodes();
    var html = "";
    for (var i = 0; i < all.length; i++) {
      var nid = all[i].id;
      html += "<option value=\"" + esc(nid) + "\"" +
        (nid === selected ? " selected" : "") + ">" + esc(nid) + "  [" +
        esc(EDITOR.deriveKind(all[i].node)) + "]</option>";
    }
    return html;
  }

  function startRecipeVerdict(r, current) {
    var typed = trimText(r.typed);
    if (!typed) return "";
    if (!idExists(typed)) return "\u2717 not an existing node id";
    if (typed === current) return "\u2717 already the start";
    if (typed !== trimText(r.candidate)) {
      return "\u2717 must match the selected candidate exactly";
    }
    return "\u2713 typed confirmation matches";
  }

  function startReady(r, current) {
    var typed = trimText(r.typed);
    return !!typed && idExists(typed) && typed !== current &&
      typed === trimText(r.candidate);
  }

  function startRecipeHtml(r) {
    var b = theBundle();
    var current = (b && b.manifest && b.manifest.start !== undefined)
      ? b.manifest.start : null;
    var inner = "";
    inner += "<div class=\"lc-hint\">start is a MANIFEST property, not a " +
      "node property \u2014 this edits manifest.start via apply() with a " +
      "typed confirmation (the manifest-edit acknowledgment flow). The " +
      "manifest lands in the export box below the recipes while dirty.</div>";
    inner += "<div class=\"lc-note\">current manifest.start: <code>" +
      esc(current === null ? "(none)" : current) + "</code></div>";
    inner += "<div class=\"lc-field\"><label>New start node</label>" +
      "<select data-lc-field=\"start-candidate\">" +
      startCandidates(r.candidate) + "</select></div>";
    inner += "<div class=\"lc-field\"><label>Type the id to confirm</label>" +
      "<input type=\"text\" data-lc-field=\"start-typed\" value=\"" +
      esc(r.typed) + "\"><div class=\"lc-live\" " +
      "data-lc-live=\"startrecipe-verdict\">" +
      esc(startRecipeVerdict(r, current)) + "</div></div>";
    if (r.warning) {
      inner += "<div class=\"lc-note lc-note-warn\">" + esc(r.warning) +
        "</div>";
    }
    inner += "<div class=\"lc-dialog-actions\">" +
      "<button type=\"button\" class=\"lc-btn lc-btn-primary\" " +
      "data-lc-act=\"recipe-start-apply\"" +
      (startReady(r, current) ? "" : " disabled") +
      ">Apply: set manifest.start</button>" +
      "<button type=\"button\" class=\"lc-btn\" " +
      "data-lc-act=\"overlay-close\">Cancel</button></div>";
    return "<div class=\"lc-overlay\">" +
      dialogFrame("Make starting node", inner) + "</div>";
  }

  function rngRecipeHtml(r) {
    var sel = selectedNode();
    var inner = "";
    if (sel && sel.id === SHUFFLE_NODE) {
      inner += "<div class=\"lc-note lc-note-ok\">This IS " + SHUFFLE_NODE +
        " \u2014 weights are allowed here WITHOUT ceremony (the single " +
        "seeded-RNG surface). Add/adjust the weights in the Choices " +
        "section above.</div><div class=\"lc-dialog-actions\">" +
        "<button type=\"button\" class=\"lc-btn\" " +
        "data-lc-act=\"overlay-close\">Close</button></div>";
      return "<div class=\"lc-overlay\">" +
        dialogFrame("Make rng \u2014 " + sel.id, inner) + "</div>";
    }
    inner += "<div class=\"lc-note lc-note-warn\">DETERMINISM " +
      "ACKNOWLEDGMENT REQUIRED \u2014 weights outside " + SHUFFLE_NODE +
      " are a design-B contract change: test_shuffle_is_the_only_weighted_" +
      "node pins " + SHUFFLE_NODE + " as the graph's ONLY weighted node, " +
      "and TestSeededDeterminismDesignB pins the seed-42 fate " +
      "(tca.co2_turn2). A new weighted node changes seeded fates and " +
      "needs a documented fate update in the same change. (RESEARCH-DATA " +
      "\u00A71.7 row 4; tests/test_glucose_content.py:539-557.)</div>";
    if (r.error) {
      inner += "<div class=\"lc-note lc-note-err\">" + esc(r.error) +
        "</div>";
    }
    inner += "<div class=\"lc-dialog-actions\">" +
      "<button type=\"button\" class=\"lc-btn lc-btn-primary\" " +
      "data-lc-act=\"recipe-rng-apply\"" +
      (r.error ? " disabled" : "") + ">Add weighted pair (0.5 / 0.5)" +
      "</button>" +
      "<button type=\"button\" class=\"lc-btn\" " +
      "data-lc-act=\"overlay-close\">Cancel</button></div>";
    return "<div class=\"lc-overlay\">" +
      dialogFrame("Make rng (weighted) \u2014 " + (sel ? sel.id : ""),
                  inner) + "</div>";
  }

  function unendingRecipeHtml(r) {
    var inner = "";
    if (r.pools && r.pools.length) {
      inner += "<div class=\"lc-note lc-note-err\">REFUSED \u2014 " +
        esc(r.id) + " is in a bad_ending_pool (" +
        r.pools.map(esc).join(", ") + "): un-making it would fire " +
        "pool_node_not_ending (rpg/edit_router.py:172-235). Remove the id " +
        "from the pool in the <b>Data tab</b> first.</div>" +
        "<div class=\"lc-dialog-actions\">" +
        "<button type=\"button\" class=\"lc-btn\" data-lc-act=\"data-tab\">" +
        "Open the Data tab</button>" +
        "<button type=\"button\" class=\"lc-btn\" " +
        "data-lc-act=\"overlay-close\">Close</button></div>";
      return "<div class=\"lc-overlay\">" +
        dialogFrame("Un-make ending \u2014 refused", inner) + "</div>";
    }
    inner += "<div class=\"lc-hint\">Removes is_ending (ABSENT, never " +
      "null \u2014 model.py:250-252) + the matching ending:&lt;tier&gt; " +
      "tag. Choices stay as they are (a 0-choice non-ending is legal but " +
      "dead \u2014 add outbound choices next).</div>";
    var inbound = [];
    var all = EDITOR.allNodes();
    for (var i = 0; i < all.length; i++) {
      var choices = asArray(all[i].node ? all[i].node.choices : null);
      for (var j = 0; j < choices.length; j++) {
        var c = choices[j];
        if (c && typeof c === "object" && c.goto === r.id) {
          inbound.push(all[i].id + " #" + j);
        }
      }
    }
    if (inbound.length) {
      inner += "<div class=\"lc-note lc-note-warn\">RETARGET NEEDS \u2014 " +
        inbound.length + " inbound edge(s) still point here (" +
        esc(inbound.join(", ")) + "): the node is no longer an ending, so " +
        "players passing through need outbound choices; retarget or " +
        "remove these edges as the story requires (\u00A71.7 row 3).</div>";
    }
    inner += "<div class=\"lc-dialog-actions\">" +
      "<button type=\"button\" class=\"lc-btn lc-btn-primary\" " +
      "data-lc-act=\"recipe-unending-apply\">Apply: remove is_ending" +
      "</button>" +
      "<button type=\"button\" class=\"lc-btn\" " +
      "data-lc-act=\"overlay-close\">Cancel</button></div>";
    return "<div class=\"lc-overlay\">" +
      dialogFrame("Un-make ending \u2014 " + r.id, inner) + "</div>";
  }

  function recipeOverlayHtml() {
    var r = recipeState;
    if (!r) return "";
    if (r.kind === "edit") return editRecipeHtml(r);
    if (r.kind === "ending") return endingRecipeHtml(r);
    if (r.kind === "start") return startRecipeHtml(r);
    if (r.kind === "rng") return rngRecipeHtml(r);
    if (r.kind === "unending") return unendingRecipeHtml(r);
    return "";
  }

  // -------------------------------------------------------------------------
  // The count-shift + determinism acknowledgment modal (Pitfall S2). The
  // action applies ONLY from the allow handler (ackAllow).
  // -------------------------------------------------------------------------

  function ackOverlayHtml() {
    var st = ackState;
    var inner = "";
    if (st.shifts && st.shifts.changed) {
      var s = st.shifts;
      inner += "<div class=\"lc-note lc-note-warn\">" +
        "Pinned counts will change: nodes " + s.nodes.old + " \u2192 " +
        s.nodes.new + " (pinned: " + PINNED_NODES + "), endings " +
        s.endings.old + " \u2192 " + s.endings.new + " (pinned: " +
        PINNED_ENDINGS + "), edit-allowed " + s.editAllowed.oldCount +
        " \u2192 " + s.editAllowed.newCount + " (pinned: " +
        PINNED_EDIT_ALLOWED + ").";
      if (s.editAllowed.added.length || s.editAllowed.removed.length) {
        inner += " Edit-allowed set: +" +
          s.editAllowed.added.map(esc).join(", ") +
          (s.editAllowed.added.length && s.editAllowed.removed.length
            ? "; " : "") +
          (s.editAllowed.removed.length
            ? "\u2212" + s.editAllowed.removed.map(esc).join(", ") : "") +
          ".";
      }
      inner += "</div>";
      inner += "<div class=\"lc-note\">These tests + viewer constants " +
        "must be updated in the SAME commit: <b>" +
        COUNT_SHIFT_TESTS.join(", ") + "</b> + the viewer pinned " +
        "constants <b>" + COUNT_SHIFT_CONSTANTS.join(" / ") +
        "</b> (tools/story_graph_viewer.py:96-105). The pinned tests " +
        "will fail until their counts are updated in the same change " +
        "\u2014 that failure is the DESIGNED signal. (The validator's " +
        "count_shift notice mirrors this.)</div>";
    }
    if (st.determinism) {
      inner += "<div class=\"lc-note lc-note-warn\">Weights outside " +
        SHUFFLE_NODE + " break the determinism pins: " +
        "test_shuffle_is_the_only_weighted_node + " +
        "TestSeededDeterminismDesignB (seed 42 \u2192 tca.co2_turn2). A " +
        "documented fate update is owed in the same change.</div>";
    }
    inner += "<div class=\"lc-note lc-note-dim\">Action: " + esc(st.label) +
      "</div>";
    inner += "<div class=\"lc-dialog-actions\">" +
      "<button type=\"button\" class=\"lc-btn lc-btn-danger\" " +
      "data-lc-act=\"ack-allow\">I understand \u2014 allow</button>" +
      "<button type=\"button\" class=\"lc-btn\" " +
      "data-lc-act=\"ack-cancel\">Cancel</button></div>";
    return "<div class=\"lc-overlay\">" +
      dialogFrame("Acknowledgment required", inner, "lc-dialog-ack") +
      "</div>";
  }

  function renderOverlay() {
    var host = refs.overlay;
    if (!host) return;
    var html = "";
    if (ackState) {
      html = ackOverlayHtml();
    } else if (wizardState && wizardState.open) {
      html = wizardOverlayHtml();
    } else if (deleteState && deleteState.open) {
      html = deleteOverlayHtml();
    } else if (recipeState) {
      html = recipeOverlayHtml();
    }
    host.innerHTML = html;
  }

  function renderLifecycle() {
    renderSection();
    renderToolbar();
    renderOverlay();
  }

  // -------------------------------------------------------------------------
  // Actions — add wizard.
  // -------------------------------------------------------------------------

  function openWizard() {
    var b = theBundle();
    if (!b) return;
    var order = bundleOrder(b);
    wizardState = {
      open: true,
      file: order.length ? order[0] : "",
      newFile: "",
      newFileAck: false,
      id: "",
      seed: "story",
      tier: "bad",
      stage: "",
      orphanAck: false
    };
    renderLifecycle();
  }

  function closeOverlays() {
    wizardState = null;
    deleteState = null;
    recipeState = null;
    ackState = null;
    renderLifecycle();
  }

  // createBlocked / repointOptions / repointReady / startVerdictText /
  // deleteUnblocked live with the renderers (lc renderer section above —
  // single definitions, no duplicates).

  function doCreate() {
    var w = wizardState;
    var b = theBundle();
    if (!w || !b || createBlocked(w)) return;
    var v = checkId(w.id);
    if (!v.ok) return;
    var id = v.id;
    var other = firstOtherId(id);
    var seed = seedNode(w.seed, {
      id: id, tier: w.tier, stage: w.stage, otherId: other
    });
    var isNewFile = (w.file === "__newfile__");
    var nf = isNewFile ? trimText(w.newFile) : w.file;
    var files = isNewFile ? [MANIFEST_FNAME, nf] : [w.file];
    var label = "add node " + id + (isNewFile ? " (new file " + nf + ")"
                                              : " into " + w.file);
    var action = {
      files: files,
      redo: function (bb) {
        if (isNewFile) {
          if (bb.manifest &&
              Object.prototype.toString.call(bb.manifest.files) ===
                "[object Array]" &&
              bb.manifest.files.indexOf(nf) < 0) {
            bb.manifest.files.push(nf);
          }
          if (Object.prototype.toString.call(bb.order) ===
                "[object Array]" && bb.order.indexOf(nf) < 0) {
            bb.order.push(nf);
          }
          if (!bb.files || typeof bb.files !== "object") bb.files = {};
          if (!hasOwn(bb.files, nf)) bb.files[nf] = { nodes: {} };
        }
        var file = bb.files ? bb.files[nf] : null;
        if (!file) return;
        if (!file.nodes || typeof file.nodes !== "object") file.nodes = {};
        file.nodes[id] = seed;
        stampNodeId(seed, id);
      }
    };
    var applied = applyWithAck(action, label, {
      determinism: (w.seed === "rng")
    });
    if (!applied) return; // the ack modal owns it from here
    wizardState = null;
    handoff = (w.seed === "mutation") ? { bucketId: id } : null;
    resultNote = "created " + id +
      (w.seed === "mutation"
        ? " \u2014 now create the edits.json bucket (button below)"
        : "") +
      (w.seed === "ending"
        ? " \u2014 wire a parent choice next (the reachability gate is " +
          "RED until then)"
        : "") +
      ". The empty-text errors are expected \u2014 fill both layers in " +
      "the Identity section.";
    EDITOR.select(id);
    renderLifecycle();
  }

  // -------------------------------------------------------------------------
  // Actions — delete guard + re-point.
  // -------------------------------------------------------------------------

  function openDelete() {
    var sel = selectedNode();
    if (!sel) return;
    deleteState = {
      open: true,
      id: sel.id,
      fname: sel.fname,
      refs: computeReferences(sel.id),
      repoint: {},
      startReplacement: ""
    };
    renderLifecycle();
  }

  function doRepoint() {
    var d = deleteState;
    if (!d || !repointReady(d)) return;
    var filesByFname = {};
    var moves = [];
    for (var i = 0; i < d.refs.goto.length; i++) {
      var g = d.refs.goto[i];
      var target = d.repoint[g.src + ":" + g.idx];
      if (!target || !idExists(target) || target === d.id) continue;
      moves.push({ file: g.file, src: g.src, idx: g.idx, target: target });
      filesByFname[g.file] = true;
    }
    if (!moves.length) return;
    var files = Object.keys(filesByFname);
    EDITOR.apply({
      files: files,
      redo: function (bb) {
        for (var m = 0; m < moves.length; m++) {
          var mv = moves[m];
          var file = bb.files ? bb.files[mv.file] : null;
          var n = (file && file.nodes) ? file.nodes[mv.src] : null;
          var choices = (n && Object.prototype.toString.call(n.choices) ===
                         "[object Array]") ? n.choices : null;
          var c = (choices && mv.idx >= 0 && mv.idx < choices.length)
            ? choices[mv.idx] : null;
          // Touches ONLY the goto field (the B11 contract, per edge).
          if (c && typeof c === "object") c.goto = mv.target;
        }
      }
    });
    d.refs = computeReferences(d.id);
    d.repoint = {};
    resultNote = "re-pointed " + moves.length + " incoming edge(s) away " +
      "from " + d.id + ".";
    renderLifecycle();
  }

  function doDelete() {
    var d = deleteState;
    if (!d || !deleteUnblocked(d)) return;
    var typed = trimText(d.startReplacement);
    var files = (d.refs.start) ? [d.fname, MANIFEST_FNAME] : [d.fname];
    var label = "delete node " + d.id +
      (d.refs.start ? " + manifest.start \u2192 " + typed : "");
    var action = {
      files: files,
      redo: function (bb) {
        var file = bb.files ? bb.files[d.fname] : null;
        if (file && file.nodes) {
          delete file.nodes[d.id];
        }
        if (d.refs.start && bb.manifest && typed) {
          bb.manifest.start = typed;
        }
      }
    };
    var applied = applyWithAck(action, label);
    if (!applied) return;
    deleteState = null;
    resultNote = "deleted " + d.id +
      (d.refs.start ? "; manifest.start is now " + typed : "") +
      " \u2014 update the pinned tests + viewer constants in the SAME " +
      "commit (see the count_shift notice).";
    if (EDITOR.state.sel === d.id) {
      EDITOR.select(null);
    }
    renderLifecycle();
  }

  // -------------------------------------------------------------------------
  // Actions — manifest export copy + Data-tab handoff prefill.
  // -------------------------------------------------------------------------

  function doManifestCopy() {
    var b = theBundle();
    var section = refs.section;
    if (!b || !section) return;
    var ta = section.querySelector("textarea[data-lc-manifest]");
    var msg = section.querySelector(
      "[data-lc-live=\"manifest-copy-msg\"]");
    if (!ta) return;
    var text = ta.value;
    var done = function () {
      if (msg) {
        msg.textContent = "copied \u2713 \u2192 paste over " + MANIFEST_DEST;
      }
    };
    var legacy = function () {
      ta.focus();
      ta.select();
      var ok = false;
      try {
        ok = document.execCommand("copy");
      } catch (e) {
        ok = false;
      }
      if (msg) {
        msg.textContent = ok
          ? "copied \u2713 \u2192 paste over " + MANIFEST_DEST
          : "clipboard blocked \u2014 the text is selected; press Ctrl+C";
      }
    };
    if (typeof navigator !== "undefined" && navigator.clipboard &&
        typeof navigator.clipboard.writeText === "function") {
      try {
        var p = navigator.clipboard.writeText(text);
        if (p && typeof p.then === "function") {
          p.then(done, legacy);
        } else {
          done();
        }
        return;
      } catch (e) {
        // fall through to the legacy path
      }
    }
    legacy();
  }

  // The Data-tab handoff: switches to the Data tab and prefills the new
  // bucket input by firing the SAME change event a human keystroke would
  // (50_editscast.js's own delegated handler updates its module state —
  // no sibling file is touched; a missing input degrades to the manual
  // note). Trigger: data-lc-act="data-bucket:<id>".
  function dataBucketPrefill(bucketId) {
    EDITOR.showTab("data");
    var panel = document.getElementById("tab-data");
    if (!panel) return;
    var input = panel.querySelector(
      "input[data-form-field=\"bucket-new-id\"]");
    if (!input) {
      resultNote = "Data tab open \u2014 type \u201C" + bucketId +
        "\u201D into \u201CNew bucket (enzyme id)\u201D and click Add " +
        "bucket.";
      renderLifecycle();
      return;
    }
    input.value = bucketId;
    try {
      var ev = document.createEvent("HTMLEvents");
      ev.initEvent("change", true, false);
      input.dispatchEvent(ev);
    } catch (e) {
      warn("45_lifecycle: bucket prefill dispatch failed: " + String(e));
    }
  }

  // -------------------------------------------------------------------------
  // Recipe actions (B2 — the §1.7 transition-table recipes).
  // -------------------------------------------------------------------------

  function openRecipe(kind) {
    var sel = selectedNode();
    if (!sel) return;
    if (kind === "edit") {
      recipeState = { kind: "edit", tagId: sel.id, error: null };
    } else if (kind === "ending") {
      var stage = hasOwn(FILE_STAGE_MAP, sel.fname)
        ? FILE_STAGE_MAP[sel.fname] : null;
      recipeState = {
        kind: "ending", id: sel.id, fname: sel.fname,
        tier: "bad", stage: stage || "",
        clearCount: asArray(sel.node.choices).length,
        blocked: false, candidates: [], newlyUnreachable: [],
        confirmedClear: false
      };
    } else if (kind === "start") {
      recipeState = { kind: "start", candidate: sel.id, typed: "",
                      warning: null };
    } else if (kind === "rng") {
      recipeState = { kind: "rng", error: null };
    } else if (kind === "unending") {
      recipeState = { kind: "unending", id: sel.id, fname: sel.fname,
                      pools: idInAnyPool(sel.id) };
    }
    renderLifecycle();
  }

  function applyRecipeEdit() {
    var r = recipeState;
    var sel = selectedNode();
    if (!r || r.kind !== "edit" || !sel) return;
    var tagId = trimText(r.tagId);
    if (!tagId) {
      r.error = "tag id required";
      renderLifecycle();
      return;
    }
    var node = sel.node;
    var tags = asArray(node.tags);
    for (var i = 0; i < tags.length; i++) {
      if (String(tags[i]).indexOf("edit:enzyme:") === 0) {
        r.error = "this node already carries " + tags[i] +
          " \u2014 it is already edit-allowed (remove the tag via the " +
          "Identity section first)";
        renderLifecycle();
        return;
      }
    }
    if (isEndingNode(node)) {
      r.error = "endings cannot offer edits (choices [] by convention)";
      renderLifecycle();
      return;
    }
    var fname = sel.fname;
    var nid = sel.id;
    var newTag = "edit:enzyme:" + tagId;
    var action = {
      files: [fname],
      redo: function (bb) {
        var n = (bb.files && bb.files[fname] && bb.files[fname].nodes)
          ? bb.files[fname].nodes[nid] : null;
        if (!n) return;
        var t = asArray(n.tags).slice();
        if (t.indexOf(newTag) < 0) t.push(newTag);
        n.tags = t;
        if (Object.prototype.toString.call(n.choices) !==
              "[object Array]") {
          n.choices = [];
        }
        n.choices.push({
          label: "Try to edit " + tagId,
          goto: "edit.prompt",
          tags: ["edit:offer"]
        });
      }
    };
    var applied = applyWithAck(action,
      "edit-allowed recipe on " + nid + " (tag edit:enzyme:" + tagId +
      " + edit:offer choice)");
    if (!applied) return;
    recipeState = null;
    handoff = { bucketId: tagId };
    resultNote = "edit-allowed recipe applied on " + nid + " \u2014 now " +
      "create the edits.json bucket " + tagId + " (button below; the " +
      "relationship pin stays RED until it exists).";
    renderLifecycle();
  }

  function applyRecipeEnding() {
    var r = recipeState;
    var sel = selectedNode();
    if (!r || r.kind !== "ending" || !sel) return;
    var tier = r.tier;
    // THE ORPHAN GUARD runs on the WOULD-BE state BEFORE anything applies.
    var check = endingWouldBeOrphan(r.fname, r.id, tier);
    if (check.orphan) {
      r.blocked = true;
      r.candidates = candidateParents(r.id);
      renderLifecycle();
      return;
    }
    var hasChoices = asArray(sel.node.choices).length > 0;
    if (hasChoices && !r.confirmedClear) {
      if (typeof window !== "undefined" && window.confirm &&
          !window.confirm("Make ending: " + r.clearCount +
            " existing choice(s) will be CLEARED (endings carry choices " +
            "[]). Proceed?")) {
        return;
      }
      r.confirmedClear = true;
    }
    var stageTag = r.stage;
    var fname = r.fname;
    var nid = r.id;
    var tierTag = "ending:" + tier;
    var action = {
      files: [fname],
      redo: function (bb) {
        var n = (bb.files && bb.files[fname] && bb.files[fname].nodes)
          ? bb.files[fname].nodes[nid] : null;
        if (!n) return;
        n.is_ending = tier;
        n.choices = [];
        var t = asArray(n.tags).slice();
        if (t.indexOf(tierTag) < 0) t.push(tierTag);
        if (stageTag && t.indexOf(stageTag) < 0) t.push(stageTag);
        n.tags = t;
      }
    };
    var applied = applyWithAck(action,
      "make ending on " + nid + " (is_ending " + tier + " + tags + " +
      "choices [])");
    if (!applied) return;
    recipeState = null;
    resultNote = nid + " is now an ending (tier " + tier + ") \u2014 the " +
      "ending CG (cutscene render) is Phase-12 territory (roadmap B9).";
    renderLifecycle();
  }

  function applyRecipeStart() {
    var r = recipeState;
    var b = theBundle();
    if (!r || r.kind !== "start" || !b || !b.manifest) return;
    var current = (b.manifest.start !== undefined) ? b.manifest.start : null;
    if (!startReady(r, current)) return;
    var next = trimText(r.typed);
    var candNode = EDITOR.nodeById(next);
    var warnText = null;
    if (candNode && (isEndingNode(candNode) ||
        EDITOR.deriveKind(candNode) === "phase8-stub")) {
      warnText = "the new start is an ending/stub \u2014 the BFS root " +
        "change may orphan most of the graph (the validator flags " +
        "unreachable_ending)";
    }
    EDITOR.apply({
      files: [MANIFEST_FNAME],
      redo: function (bb) {
        if (bb.manifest) bb.manifest.start = next;
      }
    });
    recipeState = null;
    resultNote = "manifest.start \u2192 " + next +
      (warnText ? " (" + warnText + ")" : "") +
      " \u2014 reachability re-runs from the new root; export the " +
      "manifest from the box below and place it over " + MANIFEST_DEST + ".";
    renderLifecycle();
  }

  function applyRecipeRng() {
    var r = recipeState;
    var sel = selectedNode();
    if (!r || r.kind !== "rng" || !sel) return;
    if (sel.id === SHUFFLE_NODE) {
      recipeState = null;
      resultNote = sel.id + " IS the shuffle node \u2014 add weights via " +
        "the Choices section (no ceremony there).";
      renderLifecycle();
      return;
    }
    var other = firstOtherId(sel.id);
    var fname = sel.fname;
    var nid = sel.id;
    var action = {
      files: [fname],
      redo: function (bb) {
        var n = (bb.files && bb.files[fname] && bb.files[fname].nodes)
          ? bb.files[fname].nodes[nid] : null;
        if (!n) return;
        if (Object.prototype.toString.call(n.choices) !==
              "[object Array]") {
          n.choices = [];
        }
        n.choices.push({
          label: "Wheel outcome A", weight: 0.5, goto: other,
          tags: ["rng:weighted"]
        });
        n.choices.push({
          label: "Wheel outcome B", weight: 0.5, goto: other,
          tags: ["rng:weighted"]
        });
      }
    };
    var applied = applyWithAck(action,
      "weighted pair on " + nid + " (outside " + SHUFFLE_NODE + ")",
      { determinism: true });
    if (!applied) return;
    recipeState = null;
    resultNote = "weighted pair added on " + nid + " \u2014 the " +
      "determinism pins (test 16) are now owed a documented fate update " +
      "in the same change.";
    renderLifecycle();
  }

  function applyRecipeUnending() {
    var r = recipeState;
    var sel = selectedNode();
    if (!r || r.kind !== "unending" || !sel) return;
    var pools = idInAnyPool(r.id);
    if (pools.length) {
      r.pools = pools;
      renderLifecycle();
      return;
    }
    var fname = r.fname;
    var nid = r.id;
    var tier = EDITOR.endingTier(sel.node);
    var tierTag = tier ? ("ending:" + tier) : null;
    var action = {
      files: [fname],
      redo: function (bb) {
        var n = (bb.files && bb.files[fname] && bb.files[fname].nodes)
          ? bb.files[fname].nodes[nid] : null;
        if (!n) return;
        // is_ending becomes ABSENT (never null) — model.py:250-252; the
        // ONLY executable delete here is this key (+ the matching tier
        // tag removed on an edited copy).
        delete n.is_ending;
        if (tierTag) {
          var t = asArray(n.tags).slice();
          var idx = t.indexOf(tierTag);
          if (idx >= 0) t.splice(idx, 1);
          n.tags = t;
        }
      }
    };
    var applied = applyWithAck(action,
      "un-make ending on " + nid + " (remove is_ending" +
      (tierTag ? " + " + tierTag : "") + ")");
    if (!applied) return;
    recipeState = null;
    resultNote = nid + " is no longer an ending \u2014 add outbound " +
      "choices (players passing through need them) and review the " +
      "inbound edges listed in the panel.";
    renderLifecycle();
  }

  // -------------------------------------------------------------------------
  // Event wiring — delegated listeners on MY THREE containers only (the
  // section, the toolbar, the overlay host). data-lc-* namespacing keeps
  // the sibling delegations (40_form data-role/data-field on the aside,
  // 42 data-ch-*, 43 data-oe-*) collision-free.
  // -------------------------------------------------------------------------

  function handleAct(el) {
    var act = el.getAttribute("data-lc-act") || "";
    if (act === "add-open") { openWizard(); return; }
    if (act === "overlay-close") { closeOverlays(); return; }
    if (act === "create") { doCreate(); return; }
    if (act === "delete-open") { openDelete(); return; }
    if (act === "delete-confirm") { doDelete(); return; }
    if (act === "repoint-apply") { doRepoint(); return; }
    if (act === "data-tab") {
      closeOverlays();
      EDITOR.showTab("data");
      return;
    }
    if (act === "manifest-copy") { doManifestCopy(); return; }
    if (act === "handoff-dismiss") {
      handoff = null;
      renderLifecycle();
      return;
    }
    if (act === "ack-allow") { ackAllow(); return; }
    if (act === "ack-cancel") { ackCancel(); return; }
    // The -apply forms are matched BEFORE the generic recipe openers.
    if (act === "recipe-edit-apply") { applyRecipeEdit(); return; }
    if (act === "recipe-ending-apply") { applyRecipeEnding(); return; }
    if (act === "recipe-start-apply") { applyRecipeStart(); return; }
    if (act === "recipe-rng-apply") { applyRecipeRng(); return; }
    if (act === "recipe-unending-apply") { applyRecipeUnending(); return; }
    if (act.indexOf("select-node:") === 0) {
      closeOverlays();
      EDITOR.select(act.slice("select-node:".length));
      return;
    }
    if (act.indexOf("pick-parent:") === 0) {
      recipeState = null;
      resultNote = "add the inbound choice to the candidate ending from " +
        "this parent's Choices section, then re-run Make ending.";
      EDITOR.select(act.slice("pick-parent:".length));
      return;
    }
    if (act.indexOf("data-bucket:") === 0) {
      dataBucketPrefill(act.slice("data-bucket:".length));
      return;
    }
    if (act === "recipe-menu") {
      // The "type ▸" toolbar button: scroll to the section (the recipes
      // are selection-scoped and live on the node form).
      closeOverlays();
      if (refs.section && refs.section.scrollIntoView) {
        refs.section.scrollIntoView();
      }
      return;
    }
    // Generic recipe openers (matched last).
    if (act.indexOf("recipe-") === 0) {
      var kind = act.slice("recipe-".length);
      if (kind === "edit" || kind === "ending" || kind === "start" ||
          kind === "rng" || kind === "unending") {
        openRecipe(kind);
        return;
      }
    }
  }

  function wireContainer(container) {
    if (!container || !container.addEventListener) return;

    EDITOR.delegate(container, "click", "data-lc-act", function (el) {
      handleAct(el);
    });

    container.addEventListener("input", function (ev) {
      var el = ev.target;
      if (!el || !el.getAttribute) return;
      var field = el.getAttribute("data-lc-field");
      if (!field) return;
      if (field === "id" && wizardState) {
        wizardState.id = el.value;
        liveWizardVerdict();
      } else if (field === "newfile" && wizardState) {
        wizardState.newFile = el.value;
      } else if (field === "tag-id" && recipeState) {
        recipeState.tagId = el.value;
        liveTagVerdict();
      } else if (field === "start-typed" && recipeState) {
        recipeState.typed = el.value;
        liveStartRecipeVerdict();
      } else if (field === "start-replacement" && deleteState) {
        deleteState.startReplacement = el.value;
        liveStartReplacementVerdict();
      }
    });

    container.addEventListener("change", function (ev) {
      var el = ev.target;
      if (!el || !el.getAttribute) return;
      var field = el.getAttribute("data-lc-field");
      if (!field) return;
      if (wizardState) {
        if (field === "file") {
          wizardState.file = el.value;
          wizardState.stage = defaultStageFor(wizardState.file);
          renderLifecycle();
          return;
        }
        if (field === "newfile-ack") {
          wizardState.newFileAck = !!el.checked;
          renderLifecycle();
          return;
        }
        if (field === "seed") {
          wizardState.seed = el.value;
          renderLifecycle();
          return;
        }
        if (field === "tier") {
          wizardState.tier = el.value;
          return;
        }
        if (field === "stage") {
          wizardState.stage = el.value;
          return;
        }
        if (field === "orphan-ack") {
          wizardState.orphanAck = !!el.checked;
          renderLifecycle();
          return;
        }
      }
      if (deleteState && field.indexOf("repoint:") === 0) {
        deleteState.repoint[field.slice("repoint:".length)] = el.value;
        renderLifecycle();
        return;
      }
      if (recipeState) {
        if (field === "tier" && recipeState.kind === "ending") {
          recipeState.tier = el.value;
          return;
        }
        if (field === "stage" && recipeState.kind === "ending") {
          recipeState.stage = el.value;
          return;
        }
        if (field === "start-candidate" && recipeState.kind === "start") {
          recipeState.candidate = el.value;
          renderLifecycle();
          return;
        }
      }
    });
  }

  function defaultStageFor(fname) {
    if (fname === "__newfile__") return "";
    return hasOwn(FILE_STAGE_MAP, fname) ? (FILE_STAGE_MAP[fname] || "") : "";
  }

  // Live per-keystroke verdicts update DIRECTLY (no rerender — focus and
  // caret survive; never a bundle write).
  function liveWizardVerdict() {
    var host = refs.overlay;
    if (!host || !wizardState) return;
    var span = host.querySelector("[data-lc-live=\"idverdict\"]");
    if (span) span.textContent = idVerdictText(wizardState);
    var btn = host.querySelector("[data-lc-act=\"create\"]");
    if (btn) btn.disabled = createBlocked(wizardState);
  }

  function liveTagVerdict() {
    var host = refs.overlay;
    if (!host || !recipeState) return;
    var span = host.querySelector("[data-lc-live=\"tagverdict\"]");
    if (span) span.textContent = tagVerdictText(recipeState);
  }

  function liveStartRecipeVerdict() {
    var b = theBundle();
    var host = refs.overlay;
    if (!host || !recipeState) return;
    var current = (b && b.manifest && b.manifest.start !== undefined)
      ? b.manifest.start : null;
    var span = host.querySelector(
      "[data-lc-live=\"startrecipe-verdict\"]");
    if (span) span.textContent = startRecipeVerdict(recipeState, current);
    var btn = host.querySelector("[data-lc-act=\"recipe-start-apply\"]");
    if (btn) btn.disabled = !startReady(recipeState, current);
  }

  function liveStartReplacementVerdict() {
    var host = refs.overlay;
    if (!host || !deleteState) return;
    var span = host.querySelector("[data-lc-live=\"startverdict\"]");
    if (span) span.textContent = startVerdictText(deleteState);
    var btn = host.querySelector("[data-lc-act=\"delete-confirm\"]");
    if (btn) btn.disabled = !deleteUnblocked(deleteState);
  }

  // -------------------------------------------------------------------------
  // Init + registration (07.1-04 convention).
  // -------------------------------------------------------------------------

  function buildSurfaces() {
    refs.section = document.getElementById("node-form-lifecycle");
    if (!refs.section) {
      warn("45_lifecycle: #node-form-lifecycle mount missing \u2014 " +
           "lifecycle section disabled.");
    }
    var graphTab = document.getElementById("tab-graph");
    if (graphTab) {
      refs.toolbar = document.getElementById("lifecycle-toolbar");
      if (!refs.toolbar) {
        refs.toolbar = document.createElement("div");
        refs.toolbar.id = "lifecycle-toolbar";
        graphTab.appendChild(refs.toolbar);
      }
    } else {
      warn("45_lifecycle: #tab-graph missing \u2014 lifecycle toolbar " +
           "disabled.");
    }
    refs.overlay = document.getElementById("lifecycle-overlay");
    if (!refs.overlay) {
      refs.overlay = document.createElement("div");
      refs.overlay.id = "lifecycle-overlay";
      document.body.appendChild(refs.overlay);
    }
    refs.built = true;
  }

  function initLifecycle() {
    buildSurfaces();
    wireContainer(refs.section);
    wireContainer(refs.toolbar);
    wireContainer(refs.overlay);
    renderLifecycle();
  }

  EDITOR.view("lifecycle", renderLifecycle);
  EDITOR.init(initLifecycle);

  // Exports for the diagnostics tab (07.1-19) + the structural battery: a
  // guarded extension of the EDITOR namespace owned by THIS asset.
  if (!EDITOR.lifecycle) EDITOR.lifecycle = {};
  EDITOR.lifecycle.checkId = checkId;
  EDITOR.lifecycle.computeReferences = computeReferences;
  EDITOR.lifecycle.seedNode = seedNode;
  EDITOR.lifecycle.simulateCounts = simulateCounts;
  EDITOR.lifecycle.countsOf = countsOf;
  EDITOR.lifecycle.idInAnyPool = idInAnyPool;
  EDITOR.lifecycle.endingWouldBeOrphan = endingWouldBeOrphan;
  EDITOR.lifecycle.COUNT_SHIFT_TESTS = COUNT_SHIFT_TESTS;
  EDITOR.lifecycle.COUNT_SHIFT_CONSTANTS = COUNT_SHIFT_CONSTANTS;
  EDITOR.lifecycle.COUNT_SHIFT_PINNED = {
    nodes: PINNED_NODES, endings: PINNED_ENDINGS,
    editAllowed: PINNED_EDIT_ALLOWED
  };
  EDITOR.lifecycle.SHUFFLE_NODE = SHUFFLE_NODE;
  EDITOR.lifecycle.FILE_STAGE_MAP = FILE_STAGE_MAP;
  EDITOR.lifecycle.SEED_TYPES = [
    "story", "multiple-choices", "mutation", "ending", "rng"
  ];

  // -------------------------------------------------------------------------
  // Asset CSS (per-asset injection per the pipeline rule; scoped to MY
  // three containers + the overlay).
  // -------------------------------------------------------------------------

  EDITOR.injectCss(
    "/* co-owned by 45_lifecycle.js (07.1-17): the lifecycle editor */\n" +
    "#lifecycle-toolbar { flex: none; width: 128px; padding: 8px 6px; " +
    "border-left: 2px solid #3a3f4b; background: #f0f2f6; display: flex; " +
    "flex-direction: column; gap: 6px; overflow-y: auto; }\n" +
    "#lifecycle-toolbar .lc-toolbar-title { font-size: 10px; " +
    "text-transform: uppercase; letter-spacing: 0.08em; color: #888888; }\n" +
    "#lifecycle-toolbar .lc-toolbar-sel { font-family: Consolas, " +
    "monospace; font-size: 10px; color: #4a5a75; word-break: break-all; }\n" +
    "#lifecycle-toolbar .lc-toolbar-hint { font-size: 10px; color: #888888; }\n" +
    "#lifecycle-overlay { position: fixed; top: 0; left: 0; right: 0; " +
    "bottom: 0; z-index: 60; }\n" +
    "#lifecycle-overlay:empty { display: none; }\n" +
    "#node-form-lifecycle .lc-strip, #node-form-lifecycle .lc-note, " +
    "#node-form-lifecycle .lc-manifest, #node-form-lifecycle .lc-handoff " +
    "{ font-size: 11.5px; border-radius: 4px; padding: 5px 7px; " +
    "margin: 5px 0; }\n" +
    "#node-form-lifecycle .lc-strip { border: 1px solid #b9c2d0; " +
    "background: #f4f6f9; color: #4a5568; }\n" +
    "#node-form-lifecycle .lc-strip-note { color: #888888; " +
    "font-size: 10.5px; }\n" +
    "#node-form-lifecycle .lc-note { border: 1px solid #9db4cc; " +
    "border-left: 4px solid #4682b4; background: #eef4fb; color: #2b4a68; }\n" +
    "#node-form-lifecycle .lc-note-ok, .lc-dialog .lc-note-ok { " +
    "border: 1px solid #9fc99f; border-left: 4px solid #2d6a2d; " +
    "background: #e3f2e3; color: #2d6a2d; }\n" +
    "#node-form-lifecycle .lc-note-warn, .lc-dialog .lc-note-warn { " +
    "border: 1px solid #d9a544; border-left: 4px solid #b8860b; " +
    "background: #fdf6e3; color: #6b4508; }\n" +
    "#node-form-lifecycle .lc-note-err, .lc-dialog .lc-note-err { " +
    "border: 1px solid #d98c7a; border-left: 4px solid #b22222; " +
    "background: #fdeeea; color: #7a1616; }\n" +
    "#node-form-lifecycle .lc-note-dim, .lc-dialog .lc-note-dim { " +
    "border: 1px solid #d5dbe5; background: #f7f8fa; color: #666666; }\n" +
    "#node-form-lifecycle .lc-note-inline { border: none; background: " +
    "none; padding: 0; margin: 0; color: #6b4508; font-size: 10.5px; }\n" +
    "#node-form-lifecycle .lc-kind { font-size: 11.5px; color: #444444; " +
    "margin: 4px 0; }\n" +
    "#node-form-lifecycle .lc-recipes { display: flex; flex-direction: " +
    "column; gap: 4px; margin: 4px 0 8px; align-items: flex-start; }\n" +
    "#node-form-lifecycle .lc-recipes-title { font-size: 10.5px; " +
    "color: #888888; }\n" +
    "#node-form-lifecycle .lc-handoff { border: 1px solid #d9a544; " +
    "background: #fdf6e3; color: #6b4508; }\n" +
    "#node-form-lifecycle .lc-manifest { border: 1px solid #d9a544; " +
    "background: #fdf9ee; color: #6b4508; }\n" +
    "#node-form-lifecycle .lc-manifest-ta { width: 100%; min-height: 90px; " +
    "font-family: Consolas, monospace; font-size: 10.5px; margin: 4px 0; " +
    "border: 1px solid #aab3c0; border-radius: 4px; background: #ffffff; " +
    "box-sizing: border-box; }\n" +
    "#node-form-lifecycle .lc-chip, .lc-dialog .lc-chip { display: " +
    "inline-block; font-size: 10px; padding: 0 6px; border-radius: 8px; " +
    "border: 1px solid #9db4cc; background: #eef4fb; color: #2b4a68; }\n" +
    "#node-form-lifecycle .lc-chip-warn { border-color: #d9a544; " +
    "background: #fdf6e3; color: #6b4508; }\n" +
    "#node-form-lifecycle .lc-chip-start { border-color: #2e8b57; " +
    "background: #eef7ee; color: #1d5c38; }\n" +
    ".lc-btn { font-size: 11px; padding: 2px 8px; border: 1px solid " +
    "#6d7f9b; background: #e9eef7; border-radius: 4px; cursor: pointer; }\n" +
    ".lc-btn:hover { background: #dbe4f2; }\n" +
    ".lc-btn[disabled] { opacity: 0.4; cursor: default; }\n" +
    ".lc-btn-primary { border-color: #2e8b57; background: #eef7ee; " +
    "color: #1d5c38; font-weight: bold; }\n" +
    ".lc-btn-primary:hover { background: #dff2df; }\n" +
    ".lc-btn-danger { border-color: #c26a5a; background: #fdf0ed; " +
    "color: #8c2f1f; }\n" +
    ".lc-btn-danger:hover { background: #f6d9d2; }\n" +
    ".lc-btn-small { font-size: 10px; padding: 1px 6px; }\n" +
    ".lc-overlay { position: absolute; top: 0; left: 0; right: 0; " +
    "bottom: 0; background: rgba(20, 24, 32, 0.55); display: flex; " +
    "align-items: flex-start; justify-content: center; padding: 40px 12px; " +
    "overflow-y: auto; }\n" +
    ".lc-dialog { background: #ffffff; border: 1px solid #3a3f4b; " +
    "border-radius: 8px; max-width: 560px; width: 100%; padding: 12px 14px; " +
    "box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35); box-sizing: border-box; }\n" +
    ".lc-dialog-head { display: flex; align-items: center; " +
    "justify-content: space-between; margin-bottom: 8px; gap: 8px; }\n" +
    ".lc-dialog-title { font-weight: bold; font-size: 13px; color: #2e3440; }\n" +
    ".lc-dialog .lc-field { margin: 8px 0; }\n" +
    ".lc-dialog .lc-field label { display: block; font-size: 11px; " +
    "color: #555555; margin-bottom: 2px; }\n" +
    ".lc-dialog .lc-ack { display: block; font-size: 11px; color: #6b4508; " +
    "margin: 6px 0; }\n" +
    ".lc-dialog .lc-ack input { margin-right: 4px; }\n" +
    ".lc-dialog .lc-field input[type=\"text\"], .lc-dialog .lc-field " +
    "select { width: 100%; box-sizing: border-box; font-family: Consolas, " +
    "monospace; font-size: 11.5px; padding: 3px 6px; border: 1px solid " +
    "#aab3c0; border-radius: 4px; background: #ffffff; }\n" +
    ".lc-dialog .lc-hint { font-size: 11px; color: #666666; margin: 4px 0; }\n" +
    ".lc-dialog .lc-live { font-size: 11px; margin-top: 3px; }\n" +
    ".lc-dialog .lc-reflist { margin: 6px 0; padding-left: 18px; " +
    "font-size: 11.5px; color: #444444; }\n" +
    ".lc-dialog .lc-reflist li { margin: 5px 0; }\n" +
    ".lc-dialog .lc-refrow { margin: 3px 0 3px 10px; }\n" +
    ".lc-dialog .lc-refrow select { font-family: Consolas, monospace; " +
    "font-size: 11px; max-width: 240px; }\n" +
    ".lc-dialog .lc-parents { margin: 6px 0; }\n" +
    ".lc-dialog .lc-dialog-actions { display: flex; gap: 6px; margin-top: " +
    "10px; flex-wrap: wrap; }\n" +
    "code { font-family: Consolas, monospace; font-size: 10.5px; " +
    "background: #f4f6f9; padding: 0 3px; border-radius: 3px; }\n"
  );

})();
