/* ==========================================================================
 * 50_editscast.js — the Data tab: the edits.json table editor (B4), the
 * cast.json editor (B7), and the bad-ending random pool editor (B10)
 * (plan 07.1-14).
 *
 * OWNS: the #tab-data panel (the shell's fixed mount — the whole panel is
 * this asset's territory). Loads after 00_core.js (EDITOR contract),
 * 05_json.js, 10_load.js (bundle), 20_validate.js, 30_graph.js, 40_form.js;
 * sorts before 60_trace.js / 70_claims.js / 80_save.js. Registers via
 * EDITOR.view("data", renderData) + EDITOR.init(initData) per the 07.1-04
 * registration convention.
 *
 * REQUIREMENTS (07.1-RESEARCH-DATA §1.8 edits.json + §1.9 cast.json + pool
 * semantics; 07.1-RESEARCH-SAFETY breakage map B4/B7/B10):
 *   B4  add/delete/update the mutation allowed / known to be wrong
 *       (edits.json enzyme buckets + signature entries).
 *   B7  the PDB used as the cast (cast.json entries).
 *   B10 the nodes in the random pool of bad endings (global pool +
 *       optional per-enzyme overrides).
 *
 * SET-RELATIONSHIP AWARENESS (machine-pinned by the suite — the editor
 * warns live when an edit would break it):
 *   cast(N) ⊆ edits(M) == tags(K) − {tca.citrate_synthase}
 *   (tca.citrate_synthase is the edit:structural reframe — tag but
 *   deliberately NO edits bucket; tca.akg_dh is the inverse — bucket but
 *   no approved cast PDB yet.)
 *   src: tests/test_glucose_content.py:404-449 (TestManifestRelationships);
 *        rpg/edit_router.py:238-255 (scan_edit_coverage — the coverage
 *        gate: every cast id needs >=1 edits.json entry).
 *
 * SIGNATURE MATCHING SEMANTICS (load-bearing, mirrored from the runtime):
 * matching is EXACT dict equality on the NORMALIZED signature — target
 * stripped + lowercased, args values stringified (scalars trimmed;
 * nested containers stable-stringified with sorted keys).
 *   src: rpg/edit_router.py:122-149 (route() — "EXACT dict equality");
 *        rpg/story/model.py:112-126 (EditIntent.signature + _norm_val).
 * Two entries in one bucket whose NORMALIZED signatures collide would
 * collide at route() (one entry silently unreachable) — the JS validator
 * flags them pre-save as duplicate_signature; this editor detects the
 * collision LIVE in the entry form and refuses the add/update, and the
 * validator's duplicate_signature error surfaces inline on existing data.
 *
 * KNOWN-WRONG MUTATIONS + THE M5 DECISION:
 * known-wrong entries WOULD be edits.json entries whose branch_node points
 * at a bad ending. ZERO such entries exist today by the M5 decision
 * (STATE 07-01 outcome 4: "NO known-wrong 1b entries in Phase 7" — avoids
 * the EditDialog "correct fix" mislabel). The four structural bad endings
 * bad.active_site_destroyed / bad.substrate_channel_blocked /
 * bad.cofactor_lost / bad.critical_residue_break carry the edit:known /
 * edit:known_critical tags today (on the edit.prompt choices + the nodes)
 * as the structural BFS marker — that is where a known-wrong route WOULD
 * land. This editor SUPPORTS creating one (any entry whose branch_node
 * resolves to an is_ending node is badged "known-wrong routing") but
 * REQUIRES explicit confirmation (a checkbox citing M5) before the
 * mutation lands.
 *
 * POOL SEMANTICS (B10): the global bad_ending_pool is the RUNTIME
 * unknown-edit roulette — NEVER empty (empty_bad_ending_pool is the
 * validator's error; an empty effective pool raises EditRoutingError at
 * runtime). A per-enzyme bad_ending_pool OVERRIDE, when present and
 * non-empty, replaces the global pool (OVERRIDE, no merge); an ABSENT or
 * EMPTY per-enzyme pool is the LEGAL FALLBACK to the global pool — INFO,
 * never an error.
 *   src: rpg/edit_router.py:151-166 (bad_ending_pool override semantics);
 *        rpg/edit_router.py:193-199 (per-enzyme empty = legal fallback);
 *        rpg/edit_router.py:172-235 (validate_edits_table + _check_pool).
 * This RUNTIME pool is NOT edit.prompt's 13 structural choices (the
 * intercepted stub's choice list — never player-facing as a menu;
 * 07.1-RESEARCH-DATA §5). The two are labeled differently below.
 *
 * MUTATION DISCIPLINE: every change flows through EDITOR.apply — one
 * snapshot = one undo step — marking exactly "edits.json" or "cast.json"
 * dirty. This asset performs NO story-file mutation of any kind (no node
 * or choice mutator of the state layer is ever invoked here; nodes are
 * READ-ONLY inputs for the dropdowns / tag scans). The validator re-runs
 * after every change via the hooks.validate registration (20_validate.js;
 * 00_core dispatches hooks defensively after every mutation).
 *
 * REGISTRY DIRTY HONESTY (editor-owned extension, no other asset edited):
 * the four registries live at the bundle's TOP LEVEL, so 00_core's
 * recomputeDirty (which compares bundle.files members only) cannot
 * re-derive their dirty state across undo/redo — this asset captures its
 * own per-registry JSON baselines at setBundle time and extends
 * EDITOR.save.recomputeDirty + EDITOR.save.markSaved (wrapped, never
 * rewritten) so undo/redo honestly un-dirties edits.json / cast.json and
 * a mark-saved confirm resets the baseline. Story-file dirty semantics
 * are untouched.
 *
 * CLAIM LINTS (two different criticalities — labeled as such):
 *   edits.json claim_id: the citation GATE does not scan edits.json —
 *   registry membership + approval are enforced here as an EDITOR-ONLY
 *   LINT, LOW criticality, flagged as such (amber chip + note; the
 *   mutation is not refused).
 *   cast.json claim_id: B7 requires claim_id ∈ registry AND approved —
 *   the cast-add flow REFUSES an unapproved/missing claim (never silent;
 *   spec.md: no fabricated or unapproved science).
 *   src: 07.1-RESEARCH-SAFETY breakage map B4/B7; rpg/citations.py:100-109
 *   (is_approved — the strict "approved" predicate; rejected fails
 *   identically to pending).
 *
 * STYLE: one classic script, one IIFE, ES5 only (var, no arrow functions,
 * no let/const, no modules) — the emitted-page discipline pinned page-wide
 * by tests/test_story_editor_state.py.
 * ========================================================================== */

(function () {
  "use strict";

  // -------------------------------------------------------------------------
  // Constants.
  // -------------------------------------------------------------------------

  // The only two files this asset may mutate (dirty targets). Every
  // EDITOR.apply below names one of these two literals — nothing else.
  var EDITS_FNAME = "edits.json";
  var CAST_FNAME = "cast.json";

  // The edit:structural reframe: carries an edit:enzyme: tag but
  // deliberately NO edits.json bucket (zero natural disease point
  // variants). Excluded from the "tags − edits" offender set.
  // src: tests/test_glucose_content.py:404-449.
  var STRUCTURAL_TAG_ENZYME = "tca.citrate_synthase";

  // The four structural bad endings that carry the known-wrong tags today
  // (edit:known on the first three, edit:known_critical on the last) — the
  // structural BFS marker naming where a known-wrong route WOULD land.
  // src: 07.1-RESEARCH-DATA §1.5 tag vocabulary + §1.8 known-wrong note.
  var KNOWN_WRONG_BAD_ENDINGS = [
    "bad.active_site_destroyed",
    "bad.substrate_channel_blocked",
    "bad.cofactor_lost",
    "bad.critical_residue_break"
  ];

  // The frozen op vocabulary observed in edits.json signatures (every
  // entry today is a point_mutation; EditIntent.op is free-form, so a
  // foreign value stays selectable but is warned on).
  var KNOWN_OPS = ["point_mutation"];

  // Cast source vocabulary (06-10 cast schema: bundled | download).
  var CAST_SOURCES = ["download", "bundled"];

  // Validator issue kinds THIS tab owns (surfaced inline in the strip).
  var MANIFEST_ISSUE_KINDS = {
    duplicate_signature: true,
    dangling_edit_branch: true,
    dangling_pool_node: true,
    pool_node_not_ending: true,
    empty_bad_ending_pool: true,
    coverage_uncovered: true,
    relationship_pin: true
  };
  var MANIFEST_NOTICE_KINDS = { per_enzyme_pool_empty: true };

  // -------------------------------------------------------------------------
  // Module state.
  // -------------------------------------------------------------------------

  var refs = { panel: null, built: false };

  // The entry-form draft (survives rerenders — the bundle is NEVER written
  // by form field events, only by the explicit save button, so the undo
  // pre-image stays the true pre-edit value; same granularity contract as
  // the core's textFieldBindings).
  var formState = null;

  // The cast-add form draft + its acknowledge checkbox state.
  var castNewState = null;

  // The new-bucket id draft.
  var bucketNewId = "";

  // The last selected ending in the global-pool add select (survives
  // rerenders so the dropdown does not reset while the picker is open).
  var poolSel = "";

  // Two-step arm/confirm state for destructive buttons (the armed action
  // key; any other action disarms).
  var armed = null;

  // Per-registry JSON baselines captured at setBundle time — the dirty
  // re-derivation source for the two top-level registries (see the header
  // note "REGISTRY DIRTY HONESTY").
  var registryBaseline = {};

  // -------------------------------------------------------------------------
  // Small ES5 helpers.
  // -------------------------------------------------------------------------

  function hasOwn(obj, key) {
    return Object.prototype.hasOwnProperty.call(obj, key);
  }

  function asArray(value) {
    return Object.prototype.toString.call(value) === "[object Array]"
      ? value : [];
  }

  function isEnding(node) {
    // src: rpg/story/validate.py:150-160 (_is_ending) — is_ending not None.
    return !!node && node.is_ending !== undefined && node.is_ending !== null;
  }

  function trimText(value) {
    return String(value === undefined || value === null ? "" : value)
      .replace(/^\s+|\s+$/g, "");
  }

  function esc(s) {
    return EDITOR.esc(s);
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

  function describe(e) {
    return (e && e.message) ? String(e.message) : String(e);
  }

  function editorWarn(msg) {
    try {
      if (typeof console !== "undefined" && console && console.warn) {
        console.warn(msg);
      }
    } catch (e) { /* never warn about failing to warn */ }
  }

  // -------------------------------------------------------------------------
  // stableStringify — json.dumps(x, sort_keys=True) equivalent (recursively
  // sorted keys), the same rendering the JS validator uses for the
  // duplicate_signature dedup key and _norm_val's nested containers.
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
  // SIGNATURE NORMALIZATION — the exact semantics the runtime router
  // applies before its dict-equality match. The normalize preview in the
  // entry form shows this transformation live while typing.
  //
  // normalize preview: strip + lowercase the target; stringify the args
  // (scalars trimmed, nested containers stable-stringified).
  //   src: rpg/story/model.py:112-126 (EditIntent.signature: op verbatim,
  //        target stripped + lowercased, args through _norm_val);
  //        rpg/edit_router.py:122-149 (route() — "EXACT dict equality" on
  //        the normalized signature; a collision means one entry is
  //        silently unreachable at route time — the duplicate_signature
  //        rule flags it pre-save).
  // -------------------------------------------------------------------------

  function normVal(v) {
    // src: rpg/story/model.py:154-161 (_norm_val): scalars -> str(v).strip();
    // nested dicts/lists -> sorted-key JSON (the stableStringify form).
    var t = Object.prototype.toString.call(v);
    if (t === "[object Array]" || (v && typeof v === "object")) {
      return stableStringify(v);
    }
    return trimText(v);
  }

  // The normalize preview chain the entry form applies to the target field
  // LIVE while typing: trim first, then lowercase (EditIntent.signature
  // lowercases the stripped target — rpg/story/model.py:112-126).
  function normalizeTargetText(v) {
    return String(v === undefined || v === null ? "" : v)
      .replace(/^\s+|\s+$/g, "")
      .toLowerCase();
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
      target: normalizeTargetText(sig.target),
      args: args
    });
  }

  // -------------------------------------------------------------------------
  // Claim status badge — STRICT approval semantics (display mirror of the
  // citation gate): approved iff approval_status === "approved" EXACTLY;
  // rejected fails identically to pending.
  //   src: rpg/citations.py:100-109 (is_approved, the Pitfall-6 note).
  // -------------------------------------------------------------------------

  function claimBadge(claimId) {
    var b = EDITOR.state.bundle;
    var cits = (b && b.citations && typeof b.citations === "object")
      ? b.citations : {};
    var rec = hasOwn(cits, claimId) ? cits[claimId] : null;
    if (!rec || typeof rec !== "object") {
      return { cls: "ec-chip-bad", label: "MISSING", tier: "" };
    }
    var status = rec.approval_status;
    var tier = rec.review_tier ? String(rec.review_tier) : "";
    if (status === "approved") {
      return { cls: "ec-chip-ok", label: "approved", tier: tier };
    }
    if (status === "pending") {
      return { cls: "ec-chip-warn", label: "pending", tier: tier };
    }
    if (status === "rejected") {
      return { cls: "ec-chip-bad", label: "rejected", tier: tier };
    }
    return { cls: "ec-chip-bad", label: "MISSING", tier: tier };
  }

  function claimChipHtml(claimId) {
    var id = trimText(claimId);
    if (!id) {
      return "<span class=\"ec-chip ec-chip-warn\">no claim_id</span>";
    }
    var badge = claimBadge(id);
    return "<span class=\"ec-chip " + badge.cls + "\">" + esc(id) +
      " = " + esc(badge.label) +
      (badge.tier ? " (" + esc(badge.tier) + ")" : "") + "</span>";
  }

  // -------------------------------------------------------------------------
  // REGISTRY DIRTY HONESTY — wrappers (never rewrites) around the core's
  // setBundle / save.recomputeDirty and the save layer's markSaved. The
  // two registries live at the bundle's TOP LEVEL (not bundle.files), so
  // the core's recomputeDirty cannot see them; these wrappers give
  // edits.json / cast.json the same honest dirty re-derivation the story
  // files already have (undo/redo un-dirties reverted content; a
  // mark-saved confirm resets the baseline). Installed without editing any
  // other plan's asset.
  // -------------------------------------------------------------------------

  function registryContentOf(fname) {
    var b = EDITOR.state.bundle;
    if (!b) return null;
    if (fname === EDITS_FNAME) {
      return (b.edits === undefined) ? null : b.edits;
    }
    if (fname === CAST_FNAME) {
      return (b.cast === undefined) ? null : b.cast;
    }
    return null;
  }

  function captureRegistryBaselines(bundle) {
    registryBaseline = {};
    if (!bundle || typeof bundle !== "object") return;
    registryBaseline[EDITS_FNAME] =
      JSON.stringify(bundle.edits === undefined ? null : bundle.edits);
    registryBaseline[CAST_FNAME] =
      JSON.stringify(bundle.cast === undefined ? null : bundle.cast);
  }

  // setBundle wrapper (installed at IIFE time — every load path calls
  // EDITOR.setBundle later, after the boot probe / folder pick resolves).
  var coreSetBundle = EDITOR.setBundle;
  EDITOR.setBundle = function (bundle, rawTexts) {
    coreSetBundle(bundle, rawTexts);
    captureRegistryBaselines(bundle);
  };

  // recomputeDirty wrapper: after the core re-derives the story files,
  // re-derive the two registries against the captured baselines.
  var coreRecomputeDirty = EDITOR.save.recomputeDirty;
  EDITOR.save.recomputeDirty = function () {
    var dirty = coreRecomputeDirty();
    var b = EDITOR.state.bundle;
    if (!b) return dirty;
    var members = {};
    members[EDITS_FNAME] = (b.edits === undefined) ? null : b.edits;
    members[CAST_FNAME] = (b.cast === undefined) ? null : b.cast;
    for (var fname in members) {
      if (!hasOwn(members, fname)) continue;
      if (!hasOwn(registryBaseline, fname)) continue; // nothing loaded yet
      if (JSON.stringify(members[fname]) !== registryBaseline[fname]) {
        dirty[fname] = true;
      } else {
        delete dirty[fname];
      }
    }
    return dirty;
  };

  // -------------------------------------------------------------------------
  // Data reads (bundle.edits / bundle.cast are top-level members; cast
  // degrades to null — viewer convention — and the cast editor renders a
  // warning panel instead).
  // -------------------------------------------------------------------------

  function theBundle() {
    return EDITOR.state.bundle;
  }

  function editsBundle() {
    var b = theBundle();
    return (b && b.edits && typeof b.edits === "object") ? b.edits : null;
  }

  function castBundle() {
    var b = theBundle();
    return (b && b.cast && typeof b.cast === "object") ? b.cast : null;
  }

  function enzymeMap() {
    var e = editsBundle();
    return (e && e.enzymes && typeof e.enzymes === "object")
      ? e.enzymes : {};
  }

  function enzymeIds() {
    return Object.keys(enzymeMap());
  }

  function enzymeOf(id) {
    var map = enzymeMap();
    return hasOwn(map, id) ? map[id] : null;
  }

  function bucketEntries(id) {
    var e = enzymeOf(id);
    return e ? asArray(e.edits) : [];
  }

  function castEntries() {
    var c = castBundle();
    return c ? asArray(c.enzymes) : [];
  }

  function castIdSet() {
    var set = {};
    var list = castEntries();
    for (var i = 0; i < list.length; i++) {
      var entry = list[i];
      if (entry && typeof entry === "object" && entry.id !== undefined) {
        set[entry.id] = true;
      }
    }
    return set;
  }

  function editsIdSet() {
    var set = {};
    var ids = enzymeIds();
    for (var i = 0; i < ids.length; i++) set[ids[i]] = true;
    return set;
  }

  // Distinct edit:enzyme:<id> tag values across the graph, mapped to their
  // carrier node ids (read-only — the tag vocabulary lives on the nodes).
  function tagCarriers() {
    var carriers = {};
    var all = EDITOR.allNodes();
    for (var i = 0; i < all.length; i++) {
      var wrap = all[i];
      var tags = asArray(wrap.node ? wrap.node.tags : null);
      for (var t = 0; t < tags.length; t++) {
        var tag = String(tags[t]);
        if (tag.indexOf("edit:enzyme:") === 0) {
          var value = tag.slice(12);
          if (!carriers[value]) carriers[value] = [];
          carriers[value].push(wrap.id);
        }
      }
    }
    return carriers;
  }

  function tagCarrierIds(carriers, enzymeId) {
    return (carriers && carriers[enzymeId]) ? carriers[enzymeId] : [];
  }

  // Duplicate detection WITHIN a bucket: exact normalized-dict equality
  // (the runtime route() semantics), skipping the entry being edited.
  function duplicateOf(enzymeId, sig, exceptIndex) {
    var list = bucketEntries(enzymeId);
    var norm = normalizeSignature(sig);
    for (var i = 0; i < list.length; i++) {
      if (i === exceptIndex) continue;
      var entry = list[i];
      var other = (entry && typeof entry === "object")
        ? entry.signature : null;
      if (normalizeSignature(other) === norm) return i;
    }
    return -1;
  }

  // -------------------------------------------------------------------------
  // MUTATORS — every mutation flows through EDITOR.apply (one snapshot =
  // one undo step) naming exactly "edits.json" or "cast.json". This asset
  // performs NO story-file mutation of any kind.
  // -------------------------------------------------------------------------

  function editsEntryAdd(enzymeId, entry) {
    EDITOR.apply({
      files: ["edits.json"],
      redo: function (b) {
        var e = (b && b.edits && b.edits.enzymes)
          ? b.edits.enzymes[enzymeId] : null;
        if (!e) return;
        if (Object.prototype.toString.call(e.edits) !== "[object Array]") {
          e.edits = [];
        }
        e.edits.push(entry); // order preserved: appended at the end
      }
    });
  }

  // Update touches ONLY the named fields on the existing entry (the same
  // unknown-key preservation contract as the core's mutators): any extra
  // key on the entry, on the signature dict, or inside args round-trips
  // untouched — never a whitelist rebuild.
  function editsEntryUpdate(enzymeId, index, form) {
    EDITOR.apply({
      files: ["edits.json"],
      redo: function (b) {
        var e = (b && b.edits && b.edits.enzymes)
          ? b.edits.enzymes[enzymeId] : null;
        var list = e ? asArray(e.edits) : [];
        var entry = (index >= 0 && index < list.length) ? list[index] : null;
        if (!entry || typeof entry !== "object") return;
        if (!entry.signature || typeof entry.signature !== "object") {
          entry.signature = {};
        }
        entry.signature.op = form.op;
        entry.signature.target = form.target;
        if (!entry.signature.args ||
            typeof entry.signature.args !== "object") {
          entry.signature.args = {};
        }
        entry.signature.args.new_res = form.newRes;
        entry.branch_node = form.branch;
        entry.claim_id = form.claim;
      }
    });
  }

  function editsEntryDelete(enzymeId, index) {
    EDITOR.apply({
      files: ["edits.json"],
      redo: function (b) {
        var e = (b && b.edits && b.edits.enzymes)
          ? b.edits.enzymes[enzymeId] : null;
        var list = e ? asArray(e.edits) : [];
        if (index >= 0 && index < list.length) list.splice(index, 1);
      }
    });
  }

  function editsBucketAdd(enzymeId) {
    EDITOR.apply({
      files: ["edits.json"],
      redo: function (b) {
        if (!b || !b.edits || typeof b.edits !== "object") return;
        if (!b.edits.enzymes || typeof b.edits.enzymes !== "object") {
          b.edits.enzymes = {};
        }
        if (!hasOwn(b.edits.enzymes, enzymeId)) {
          b.edits.enzymes[enzymeId] = { edits: [] };
        }
      }
    });
  }

  // Bucket deletion REFUSES while cast.json still lists the id (the
  // coverage gate: every cast id needs >=1 edits.json entry — deleting the
  // bucket under a cast id is the coverage_uncovered error).
  //   src: rpg/edit_router.py:238-255 (scan_edit_coverage);
  //        tools/check_edit_coverage.py:65-126 (the CLI gate).
  function castListsId(enzymeId) {
    return hasOwn(castIdSet(), enzymeId);
  }

  function editsBucketDelete(enzymeId) {
    if (castListsId(enzymeId)) {
      showStatus("Refused: cast.json still lists \"" + enzymeId +
        "\" — every cast id needs >=1 edits.json entry (the coverage " +
        "gate; deleting the bucket under a cast id is the " +
        "coverage_uncovered error). Delete the cast entry first — this " +
        "editor refuses while the coverage relationship would break. " +
        "src: rpg/edit_router.py:238-255.");
      return false;
    }
    EDITOR.apply({
      files: ["edits.json"],
      redo: function (b) {
        if (b && b.edits && b.edits.enzymes) {
          delete b.edits.enzymes[enzymeId];
        }
      }
    });
    return true;
  }

  // --- B10 pool mutators ---------------------------------------------------

  function editsGlobalPoolAdd(nodeId) {
    EDITOR.apply({
      files: ["edits.json"],
      redo: function (b) {
        if (!b || !b.edits || typeof b.edits !== "object") return;
        if (Object.prototype.toString.call(b.edits.bad_ending_pool) !==
            "[object Array]") {
          b.edits.bad_ending_pool = [];
        }
        if (b.edits.bad_ending_pool.indexOf(nodeId) < 0) {
          b.edits.bad_ending_pool.push(nodeId);
        }
      }
    });
  }

  // The GLOBAL pool is never empty: removing its last member is REFUSED
  // (empty_bad_ending_pool — the ultimate fallback for every enzyme
  // without a per-enzyme override; an empty effective pool raises
  // EditRoutingError at runtime).
  //   src: rpg/edit_router.py:172-235 (validate_edits_table/_check_pool);
  //        rpg/edit_router.py:144-149 (EditRoutingError on empty).
  function editsGlobalPoolRemove(index) {
    var e = editsBundle();
    var pool = (e && Object.prototype.toString.call(e.bad_ending_pool) ===
                "[object Array]") ? e.bad_ending_pool : [];
    if (pool.length <= 1) {
      showStatus("Refused: the GLOBAL bad_ending_pool is never empty " +
        "(empty_bad_ending_pool) — it is the ultimate fallback for any " +
        "enzyme without a per-enzyme override, and an empty effective " +
        "pool raises EditRoutingError at runtime. Add another member " +
        "first. src: rpg/edit_router.py:172-235.");
      return false;
    }
    EDITOR.apply({
      files: ["edits.json"],
      redo: function (b) {
        var p = (b && b.edits &&
                 Object.prototype.toString.call(b.edits.bad_ending_pool) ===
                 "[object Array]") ? b.edits.bad_ending_pool : null;
        if (p && index >= 0 && index < p.length) p.splice(index, 1);
      }
    });
    return true;
  }

  function editsPerPoolCreate(enzymeId) {
    EDITOR.apply({
      files: ["edits.json"],
      redo: function (b) {
        var e = (b && b.edits && b.edits.enzymes)
          ? b.edits.enzymes[enzymeId] : null;
        if (e && !hasOwn(e, "bad_ending_pool")) {
          e.bad_ending_pool = []; // empty override = legal fallback (INFO)
        }
      }
    });
  }

  function editsPerPoolAdd(enzymeId, nodeId) {
    EDITOR.apply({
      files: ["edits.json"],
      redo: function (b) {
        var e = (b && b.edits && b.edits.enzymes)
          ? b.edits.enzymes[enzymeId] : null;
        if (!e) return;
        if (Object.prototype.toString.call(e.bad_ending_pool) !==
            "[object Array]") {
          e.bad_ending_pool = [];
        }
        if (e.bad_ending_pool.indexOf(nodeId) < 0) {
          e.bad_ending_pool.push(nodeId);
        }
      }
    });
  }

  function editsPerPoolRemove(enzymeId, index) {
    EDITOR.apply({
      files: ["edits.json"],
      redo: function (b) {
        var e = (b && b.edits && b.edits.enzymes)
          ? b.edits.enzymes[enzymeId] : null;
        var p = (e && Object.prototype.toString.call(e.bad_ending_pool) ===
                 "[object Array]") ? e.bad_ending_pool : null;
        if (p && index >= 0 && index < p.length) p.splice(index, 1);
      }
    });
  }

  // Removing the override KEY entirely reverts the enzyme to the global
  // fallback — the other legal path (an empty remaining [] override is
  // ALSO legal — INFO, never an error).
  function editsPerPoolRemoveOverride(enzymeId) {
    EDITOR.apply({
      files: ["edits.json"],
      redo: function (b) {
        var e = (b && b.edits && b.edits.enzymes)
          ? b.edits.enzymes[enzymeId] : null;
        if (e) delete e.bad_ending_pool;
      }
    });
  }

  // --- B7 cast mutators ----------------------------------------------------

  function castFieldSet(index, field, value) {
    EDITOR.apply({
      files: ["cast.json"],
      redo: function (b) {
        var list = (b && b.cast && Object.prototype.toString.call(
                      b.cast.enzymes) === "[object Array]")
          ? b.cast.enzymes : null;
        var entry = (list && index >= 0 && index < list.length)
          ? list[index] : null;
        if (entry && typeof entry === "object") entry[field] = value;
      }
    });
  }

  function castEntryAdd(entry) {
    EDITOR.apply({
      files: ["cast.json"],
      redo: function (b) {
        if (!b || !b.cast || typeof b.cast !== "object") return;
        if (Object.prototype.toString.call(b.cast.enzymes) !==
            "[object Array]") {
          b.cast.enzymes = [];
        }
        b.cast.enzymes.push(entry); // order preserved: appended at the end
      }
    });
  }

  // Cast deletion REFUSES while an edits bucket exists for the id (the
  // pinned relationship test expects cast(M) == edits(N) − {tca.akg_dh}
  // EXACTLY — deleting the cast entry under a live bucket desyncs the
  // sets and would owe a same-commit test update; remove the bucket
  // first).
  //   src: tests/test_glucose_content.py:404-449
  //        (TestManifestRelationships).
  function editsBucketExistsFor(enzymeId) {
    var e = enzymeOf(enzymeId);
    return !!(e && asArray(e.edits).length > 0);
  }

  function castEntryDelete(index) {
    var list = castEntries();
    var entry = (index >= 0 && index < list.length) ? list[index] : null;
    var id = (entry && entry.id !== undefined) ? String(entry.id) : "";
    if (id && hasOwn(enzymeMap(), id)) {
      showStatus("Refused: an edits.json bucket still exists for \"" + id +
        "\" — the pinned relationship cast(M) == edits(N) − {tca.akg_dh} " +
        "holds exactly (tests/test_glucose_content.py:404-449); delete " +
        "the edits bucket first (it is not cast-listed after that, so " +
        "the bucket deletion is allowed).");
      return false;
    }
    EDITOR.apply({
      files: ["cast.json"],
      redo: function (b) {
        var l = (b && b.cast && Object.prototype.toString.call(
                   b.cast.enzymes) === "[object Array]")
          ? b.cast.enzymes : null;
        if (l && index >= 0 && index < l.length) l.splice(index, 1);
      }
    });
    return true;
  }

  // -------------------------------------------------------------------------
  // Relationship report — the live pin. Offenders are named as chips.
  //   src: tests/test_glucose_content.py:404-449
  //        (TestManifestRelationships);
  //        rpg/edit_router.py:238-255 (scan_edit_coverage).
  // -------------------------------------------------------------------------

  function relationshipReport() {
    var carriers = tagCarriers();
    var tagSet = {};
    for (var k in carriers) {
      if (hasOwn(carriers, k)) tagSet[k] = true;
    }
    var tagCount = sortedKeys(tagSet).length;
    var editsSet = editsIdSet();
    var castSet = castIdSet();
    var expected = {};
    for (var t in tagSet) {
      if (hasOwn(tagSet, t) && t !== STRUCTURAL_TAG_ENZYME) {
        expected[t] = true;
      }
    }
    return {
      tagCount: tagCount,
      castCount: sortedKeys(castSet).length,
      editsCount: sortedKeys(editsSet).length,
      // buckets with no edit:enzyme: tag carrier (relationship_pin half 1)
      editsNoTag: setDifference(editsSet, tagSet),
      // tag values (minus the structural reframe) with no bucket
      tagNoEdits: setDifference(expected, editsSet),
      // cast ids with no bucket (coverage gate + relationship_pin half 2)
      castNoEdits: setDifference(castSet, editsSet),
      // buckets with no cast entry — INFORMATIONAL (the pinned state has
      // exactly one: tca.akg_dh — no approved OGDH cast PDB yet)
      editsNoCast: setDifference(editsSet, castSet),
      structural: hasOwn(tagSet, STRUCTURAL_TAG_ENZYME)
    };
  }

  // -------------------------------------------------------------------------
  // Render helpers.
  // -------------------------------------------------------------------------

  function chip(cls, text) {
    return "<span class=\"ec-chip " + cls + "\">" + esc(text) + "</span>";
  }

  function dirtyDot(fname) {
    var dirty = EDITOR.state.dirty;
    return (dirty && dirty[fname])
      ? " <span class=\"ec-dirty\" title=\"unsaved changes\">&#9679; dirty</span>"
      : "";
  }

  // Node dropdown options grouped by story file (branch_node must exist in
  // the graph — the dropdown lists ONLY existing nodes).
  function nodeOptionsGrouped(selectedId, endingsOnly) {
    var b = theBundle();
    if (!b || !b.files) return "";
    var order = (Object.prototype.toString.call(b.order) ===
                 "[object Array]" && b.order.length)
      ? b.order : Object.keys(b.files);
    var html = "";
    for (var i = 0; i < order.length; i++) {
      var fname = order[i];
      var file = b.files[fname];
      var nodes = (file && file.nodes && typeof file.nodes === "object")
        ? file.nodes : null;
      if (!nodes) continue;
      var opts = "";
      for (var nid in nodes) {
        if (!Object.prototype.hasOwnProperty.call(nodes, nid)) continue;
        var node = nodes[nid];
        if (endingsOnly && !isEnding(node)) continue;
        var kind = EDITOR.deriveKind(node);
        var tier = EDITOR.endingTier(node);
        var label = nid + "  [" + kind +
          (tier ? " " + tier : "") + "]";
        opts += "<option value=\"" + esc(nid) + "\"" +
          (nid === selectedId ? " selected" : "") + ">" +
          esc(label) + "</option>";
      }
      if (opts) {
        html += "<optgroup label=\"" + esc(fname) + "\">" + opts +
          "</optgroup>";
      }
    }
    return html;
  }

  // -------------------------------------------------------------------------
  // Status line (inline feedback — never a blocking modal).
  // -------------------------------------------------------------------------

  var statusMessage = null;

  function showStatus(text) {
    statusMessage = { text: text, at: new Date().toISOString() };
    renderData(); // re-render with the message visible
  }

  // -------------------------------------------------------------------------
  // Section 1 — the edits.json table editor (B4).
  // -------------------------------------------------------------------------

  function entryFormHtml(enzymeId) {
    var st = formState;
    var isEdit = st.index >= 0;
    var node = st.branch ? EDITOR.nodeById(st.branch) : null;
    var endingRoute = isEnding(node);
    var opOptions = "";
    var ops = KNOWN_OPS.slice();
    if (st.op && ops.indexOf(st.op) < 0) ops.push(st.op);
    for (var i = 0; i < ops.length; i++) {
      opOptions += "<option value=\"" + esc(ops[i]) + "\"" +
        (st.op === ops[i] ? " selected" : "") + ">" + esc(ops[i]) +
        "</option>";
    }
    // A foreign op stays selectable but is warned on (the chip below the
    // select renders whenever KNOWN_OPS misses the current value).

    var html = "";
    html += "<div class=\"ec-entryform\" data-ec-form=\"1\">";
    html += "<div class=\"ec-formtitle\">" +
      (isEdit ? "Edit entry #" + st.index : "Add entry") +
      " in bucket <b>" + esc(enzymeId) + "</b>" +
      " <button type=\"button\" class=\"ec-btn\" " +
      "data-ec-action=\"entry-cancel\">Cancel</button></div>";

    // signature.op
    html += "<div class=\"ec-row\"><label>signature.op</label>" +
      "<select data-form-field=\"op\">" + opOptions + "</select>" +
      (KNOWN_OPS.indexOf(st.op) < 0
        ? " " + chip("ec-chip-warn",
            "non-point_mutation op — outside the current data vocabulary " +
            "(every edits.json entry today is a point_mutation); " +
            "EditIntent.op is free-form, verify before landing")
        : "") +
      "</div>";

    // signature.target (+ the live normalize preview)
    html += "<div class=\"ec-row\"><label>signature.target</label>" +
      "<input type=\"text\" data-form-field=\"target\" " +
      "value=\"" + esc(st.target) + "\" placeholder=\"resi 209 and chain a\">" +
      "<span class=\"ec-live\" data-ec-live=\"preview\"></span></div>";

    // signature.args.new_res
    html += "<div class=\"ec-row\"><label>signature.args.new_res</label>" +
      "<input type=\"text\" data-form-field=\"new_res\" " +
      "value=\"" + esc(st.newRes) + "\" placeholder=\"GLY\">" +
      "<span class=\"ec-live\" data-ec-live=\"sig\"></span></div>";

    // branch_node (dropdown of node ids grouped by file — must exist)
    html += "<div class=\"ec-row\"><label>branch_node</label>" +
      "<select data-form-field=\"branch\">" +
      "<option value=\"\">(select a node…)</option>" +
      nodeOptionsGrouped(st.branch, false) +
      "</select>" +
      "<span class=\"ec-live\" data-ec-live=\"route\"></span></div>";

    // M5 confirmation — visible only when the routing target is an ending.
    if (endingRoute) {
      html += "<div class=\"ec-m5row\">" +
        "<label><input type=\"checkbox\" data-form-field=\"m5\"" +
        (st.m5 ? " checked" : "") + "> " +
        "I understand this routes a known-wrong edit to the BAD ENDING " +
        esc(st.branch) + " — zero such entries exist today by the M5 " +
        "decision (STATE 07-01 outcome 4); creating one is a deliberate " +
        "departure that the EditDialog would present as the \u201ccorrect " +
        "fix\u201d.</label></div>";
    }

    // claim_id (+ live status chip; the editor-only lint note)
    html += "<div class=\"ec-row\"><label>claim_id</label>" +
      "<input type=\"text\" data-form-field=\"claim_id\" " +
      "value=\"" + esc(st.claim) + "\" placeholder=\"DIS-...-cand\">" +
      "<span class=\"ec-live\" data-ec-live=\"claim\"></span></div>" +
      "<div class=\"ec-note\">Editor-only lint, LOW criticality: the " +
      "citation gate does NOT scan edits.json (story nodes only) — " +
      "registry membership + approval_status === \u201capproved\u201d are " +
      "flagged here as a courtesy lint, never a silent pass. " +
      "src: rpg/citations.py:100-109.</div>";

    html += "<div class=\"ec-row ec-actions\">" +
      "<button type=\"button\" class=\"ec-btn ec-btn-primary\" " +
      "data-ec-action=\"entry-save\">" +
      (isEdit ? "Save entry" : "Add entry") + "</button>" +
      "<span class=\"ec-live\" data-ec-live=\"formmsg\"></span></div>";

    html += "</div>";
    return html;
  }

  function entryRowHtml(enzymeId, entry, index, dupWith) {
    var sig = (entry && typeof entry === "object") ? entry.signature : null;
    var op = sig ? sig.op : undefined;
    var target = sig ? sig.target : "";
    var newRes = (sig && sig.args && sig.args.new_res !== undefined)
      ? sig.args.new_res : "";
    var branch = entry ? entry.branch_node : "";
    var claim = entry ? entry.claim_id : "";
    var node = branch ? EDITOR.nodeById(branch) : null;
    var knownWrong = isEnding(node);
    var isDup = dupWith >= 0;

    var html = "";
    html += "<div class=\"ec-entry" + (isDup ? " ec-entry-dup" : "") +
      (knownWrong ? " ec-entry-knownwrong" : "") + "\">";
    html += "<div class=\"ec-entryhead\">";
    html += "<b>#" + index + "</b> ";
    if (knownWrong) {
      html += chip("ec-chip-warn",
        "known-wrong routing \u2192 " + branch + " (an ENDING \u2014 M5)");
    } else if (node) {
      html += chip("ec-chip-ok",
        "allowed-fix routing \u2192 " + branch + " (restored/branch node)");
    } else {
      html += chip("ec-chip-bad",
        "dangling_edit_branch \u2192 " + branch + " (not in the graph)");
    }
    if (isDup) {
      html += " " + chip("ec-chip-bad",
        "duplicate_signature: exact normalized-dict equality with #" +
        dupWith + " (one entry would be silently unreachable at " +
        "route())");
    }
    html += "<span class=\"ec-entrybtns\">" +
      "<button type=\"button\" class=\"ec-btn\" " +
      "data-ec-action=\"entry-open-edit:" + esc(enzymeId) + ":" + index +
      "\">Edit</button> " +
      "<button type=\"button\" class=\"ec-btn\" " +
      "data-ec-action=\"entry-delete:" + esc(enzymeId) + ":" + index +
      "\">Delete</button></span>";
    html += "</div>";
    html += "<div class=\"ec-entrybody\">op: <code>" +
      esc(op === undefined || op === null ? "(none)" : op) +
      "</code> &middot; target: <code>" + esc(target) +
      "</code> &middot; args.new_res: <code>" + esc(newRes) +
      "</code> &middot; normalized: <code>" +
      esc(normalizeSignature(sig)) + "</code><br>" +
      "claim_id: " + claimChipHtml(claim);
    if (node && isEnding(node)) {
      var tags = asArray(node.tags);
      var knownTag = tags.indexOf("edit:known") >= 0;
      var critTag = tags.indexOf("edit:known_critical") >= 0;
      if (knownTag || critTag) {
        html += " " + chip("ec-chip-info",
          "routing target carries " +
          (critTag ? "edit:known_critical" : "edit:known") +
          " (the structural BFS marker)");
      }
    }
    html += "</div></div>";
    return html;
  }

  function bucketHtml(enzymeId, carriers) {
    var entries = bucketEntries(enzymeId);
    var carrierIds = tagCarrierIds(carriers, enzymeId);
    var isCast = castListsId(enzymeId);
    var perPool = enzymeOf(enzymeId)
      ? enzymeOf(enzymeId).bad_ending_pool : undefined;
    var hasOverride = perPool !== undefined && perPool !== null;

    var html = "";
    html += "<div class=\"ec-bucket\">";
    html += "<div class=\"ec-buckethead\">" +
      "<b class=\"ec-enzyme\">" + esc(enzymeId) + "</b>" +
      " " + chip("ec-chip-info", entries.length + " entr" +
        (entries.length === 1 ? "y" : "ies")) +
      (isCast
        ? " " + chip("ec-chip-ok", "cast-listed (coverage)")
        : " " + chip("ec-chip-info", "not in cast.json"));
    if (carrierIds.length) {
      html += " " + chip("ec-chip-ok",
        "edit:enzyme:" + enzymeId + " on " + carrierIds.join(", "));
    } else {
      html += " " + chip("ec-chip-bad",
        "no edit:enzyme:" + enzymeId + " tag carrier (relationship_pin: " +
        "a bucket needs a tag carrier \u2014 add the tag via the node " +
        "form)");
    }
    html += "<span class=\"ec-entrybtns\">" +
      "<button type=\"button\" class=\"ec-btn\" " +
      "data-ec-action=\"entry-open-add:" + esc(enzymeId) +
      "\">+ Add entry</button> " +
      "<button type=\"button\" class=\"ec-btn ec-btn-danger\" " +
      "data-ec-action=\"bucket-delete:" + esc(enzymeId) + "\">" +
      (armed === "bucket-delete:" + enzymeId ? "Confirm delete bucket?"
        : "Delete bucket") + "</button></span>";
    html += "</div>";

    if (!entries.length) {
      html += "<div class=\"ec-note\">No entries yet. A cast id covered " +
        "by an empty bucket still fails the coverage gate (every cast id " +
        "needs >=1 edits.json entry).</div>";
    }
    for (var i = 0; i < entries.length; i++) {
      var dupWith = duplicateOf(enzymeId,
        entries[i] ? entries[i].signature : null, i);
      html += entryRowHtml(enzymeId, entries[i], i, dupWith);
    }
    if (formState && formState.open && formState.enzyme === enzymeId) {
      html += entryFormHtml(enzymeId);
    }
    html += "</div>";
    return html;
  }

  function renderEditsSection(carriers) {
    var e = editsBundle();
    var html = "";
    html += "<h2>Edits table \u2014 rpg/data/edits.json (B4: mutations " +
      "allowed / known to be wrong)" + dirtyDot(EDITS_FNAME) + "</h2>";
    if (!e) {
      html += "<div class=\"ec-warnbox\">edits.json did not load \u2014 " +
        "the load layer blocks without it (severity: block). Check the " +
        "boot panel's found/missing checklist at the top of the page.</div>";
      return html;
    }
    var ids = enzymeIds();
    html += "<div class=\"ec-note\">" + ids.length + " enzyme bucket(s). " +
      "A bucket key IS the enzyme id = the node id carrying the " +
      "edit:enzyme:&lt;id&gt; tag. Entries match a player's edit by EXACT " +
      "dict equality on the normalized signature (target strip+lowercase, " +
      "args stringified) \u2014 rpg/edit_router.py:122-149.</div>";

    // new bucket row
    html += "<div class=\"ec-row ec-newbucket\">" +
      "<label>New bucket (enzyme id)</label>" +
      "<input type=\"text\" data-form-field=\"bucket-new-id\" " +
      "value=\"" + esc(bucketNewId) + "\" placeholder=\"tca.new_enzyme\">" +
      "<button type=\"button\" class=\"ec-btn\" " +
      "data-ec-action=\"bucket-add\">Add bucket</button>" +
      "<span class=\"ec-note\">After adding, a node must carry the " +
      "edit:enzyme:&lt;id&gt; tag (node form \u2192 tags) or the " +
      "relationship_pin error fires \u2014 the save panel stays blocked " +
      "until the tag lands.</span></div>";

    html += "<div data-ec-buckets>";
    for (var i = 0; i < ids.length; i++) {
      html += bucketHtml(ids[i], carriers);
    }
    html += "</div>";
    return html;
  }

  // -------------------------------------------------------------------------
  // Section 2 — the known-wrong mutations panel (B4 second half) + M5.
  // -------------------------------------------------------------------------

  function renderKnownWrongSection() {
    var ids = enzymeIds();
    var knownWrongEntries = [];
    for (var i = 0; i < ids.length; i++) {
      var entries = bucketEntries(ids[i]);
      for (var j = 0; j < entries.length; j++) {
        var entry = entries[j];
        var branch = (entry && typeof entry === "object")
          ? entry.branch_node : null;
        var node = branch ? EDITOR.nodeById(branch) : null;
        if (isEnding(node)) {
          knownWrongEntries.push(ids[i] + " #" + j + " \u2192 " + branch);
        }
      }
    }

    var html = "";
    html += "<h2>Known-wrong mutations \u2014 where they WOULD live " +
      "(B4 second half)</h2>";
    html += "<div class=\"ec-note\">A known-wrong mutation WOULD be an " +
      "edits.json entry whose branch_node points at a BAD ENDING. The " +
      "four structural bad endings " +
      esc(KNOWN_WRONG_BAD_ENDINGS.join(" / ")) +
      " carry the edit:known / edit:known_critical tags today (on the " +
      "edit.prompt choices + the nodes) as the structural BFS marker \u2014 " +
      "that is where such a route WOULD land.</div>";
    html += "<div class=\"ec-m5panel\">" +
      "<b>M5 status:</b> ZERO known-wrong entries exist today by the M5 " +
      "decision (STATE 07-01 outcome 4: \u201cNO known-wrong 1b entries " +
      "in Phase 7\u201d \u2014 it avoids the EditDialog mislabeling a " +
      "wrong edit as the \u201ccorrect fix\u201d). This editor SUPPORTS " +
      "creating one: any entry whose branch_node resolves to an " +
      "is_ending node is badged \u201cknown-wrong routing\u201d \u2014 " +
      "but creating one REQUIRES the explicit M5 confirmation checkbox " +
      "in the entry form.</div>";
    html += "<div class=\"ec-note\">The difference, labeled everywhere: " +
      "<b>allowed-fix</b> \u2192 routes to a restored/branch node " +
      "(non-ending; e.g. gly.pfk_restored) \u2014 the player's mutation " +
      "is REPAIRED; <b>known-wrong</b> \u2192 routes to a bad ending \u2014 " +
      "the mutation is a documented WRONG edit that plays out its " +
      "consequence.</div>";
    if (knownWrongEntries.length) {
      html += "<div class=\"ec-warnbox\">\u26a0 " +
        knownWrongEntries.length + " entr" +
        (knownWrongEntries.length === 1 ? "y routes" : "ies route") +
        " to an ending today (M5 departure): " +
        esc(knownWrongEntries.join("; ")) + "</div>";
    } else {
      html += "<div class=\"ec-note ec-note-ok\">\u2713 0 entries route " +
        "to an ending \u2014 the M5 posture holds (no known-wrong " +
        "entries).</div>";
    }
    return html;
  }

  // -------------------------------------------------------------------------
  // Section 3 — the cast.json editor (B7) + the live relationship pin.
  // -------------------------------------------------------------------------

  function relationshipHtml() {
    var rep = relationshipReport();
    // The live formula: cast(N) ⊆ edits(M) == tags(K) − {tca.citrate_synthase}
    var formula = "cast(" + rep.castCount + ") \u2286 edits(" +
      rep.editsCount + ") == tags(" + rep.tagCount + ") \u2212 {" +
      STRUCTURAL_TAG_ENZYME + "}";
    var html = "";
    html += "<div class=\"ec-relpin\">";
    html += "<div class=\"ec-relformula\"><code>" + esc(formula) +
      "</code> <span class=\"ec-note\">(the shared-manifest invariant, " +
      "rendered live \u2014 src: tests/test_glucose_content.py:404-449, " +
      "TestManifestRelationships)</span></div>";
    var chips = "";
    var i;
    if (rep.castNoEdits.length) {
      for (i = 0; i < rep.castNoEdits.length; i++) {
        chips += chip("ec-chip-bad", "cast id with NO edits bucket: " +
          rep.castNoEdits[i] + " (coverage gate exit 1)");
      }
    }
    if (rep.editsNoTag.length) {
      for (i = 0; i < rep.editsNoTag.length; i++) {
        chips += chip("ec-chip-bad", "bucket with NO tag carrier: " +
          rep.editsNoTag[i] + " (relationship_pin)");
      }
    }
    if (rep.tagNoEdits.length) {
      for (i = 0; i < rep.tagNoEdits.length; i++) {
        chips += chip("ec-chip-bad", "tag value with NO bucket: " +
          rep.tagNoEdits[i] + " (relationship_pin)");
      }
    }
    for (i = 0; i < rep.editsNoCast.length; i++) {
      chips += chip("ec-chip-info", "bucket with no cast entry (legal): " +
        rep.editsNoCast[i]);
    }
    if (rep.structural) {
      chips += chip("ec-chip-info", STRUCTURAL_TAG_ENZYME +
        ": edit:structural \u2014 tag by design, deliberately NO bucket");
    }
    if (!chips) {
      chips = chip("ec-chip-ok",
        "\u2713 all three sets relate exactly as pinned");
    }
    html += "<div class=\"ec-relchips\">" + chips + "</div>";
    html += "</div>";
    return html;
  }

  function castAddChecksHtml() {
    var st = castNewState;
    var id = trimText(st.id);
    var rows = "";
    var ok1 = false;
    var ok2 = false;
    var ok3 = false;
    if (id) {
      var e = enzymeOf(id);
      ok1 = !!(e && asArray(e.edits).length > 0);
      rows += "<div class=\"ec-check" + (ok1 ? " ec-check-ok" : "") +
        "\">" + (ok1 ? "\u2713" : "\u2717") + " edits bucket with >=1 " +
        "entry " + (ok1 ? "exists" : "MISSING \u2014 add the bucket first " +
        "(the coverage gate; adding the cast id without it fires " +
        "coverage_uncovered and the save panel refuses)") + "</div>";
      var carriers = tagCarriers();
      var carrierIds = tagCarrierIds(carriers, id);
      ok2 = carrierIds.length > 0;
      rows += "<div class=\"ec-check" + (ok2 ? " ec-check-ok" : "") +
        "\">" + (ok2 ? "\u2713" : "\u2717") + " edit:enzyme:" + esc(id) +
        " tag in the graph " +
        (ok2 ? "carried by " + esc(carrierIds.join(", "))
          : "MISSING \u2014 either add the tag via the node form, or " +
            "acknowledge the relationship-test update below") + "</div>";
      if (st.claim) {
        var badge = claimBadge(st.claim);
        ok3 = badge.label === "approved";
        rows += "<div class=\"ec-check" + (ok3 ? " ec-check-ok" : "") +
          "\">" + (ok3 ? "\u2713" : "\u2717") + " claim_id \u2208 registry " +
          "AND approved \u2014 " + esc(st.claim) + " = " +
          esc(badge.label) + (ok3 ? "" : " (B7: an unapproved claim_id " +
          "never lands silently)") + "</div>";
      } else {
        rows += "<div class=\"ec-check\">\u2717 claim_id \u2208 registry " +
          "AND approved \u2014 no claim_id typed yet</div>";
      }
    } else {
      rows += "<div class=\"ec-check\">\u2717 type the enzyme id first" +
        "</div>";
    }
    return rows;
  }

  function renderCastSection() {
    var c = castBundle();
    var html = "";
    html += "<h2>Cast \u2014 rpg/data/cast.json (B7: the PDB used as the " +
      "cast)" + dirtyDot(CAST_FNAME) + "</h2>";
    if (!c) {
      html += "<div class=\"ec-warnbox\">cast.json did not load \u2014 " +
        "optional-degrade with a warning (viewer convention). The edits " +
        "and pool editors above still work; the relationship pin cannot " +
        "check the cast half. Check the boot panel's checklist.</div>";
      return html;
    }
    html += relationshipHtml();

    var list = castEntries();
    html += "<div class=\"ec-note\">" + list.length + " cast entr" +
      (list.length === 1 ? "y" : "ies") + ". Fields commit on change " +
      "(one undo step each); the relationship pin above re-checks live " +
      "after every change.</div>";

    html += "<div data-ec-castlist>";
    for (var i = 0; i < list.length; i++) {
      var entry = list[i];
      var id = entry && entry.id !== undefined ? String(entry.id) : "";
      var bucketLive = hasOwn(enzymeMap(), id);
      var delLabel = (armed === "cast-delete:" + i)
        ? "Confirm delete?" : "Delete";
      html += "<div class=\"ec-entry\">";
      html += "<div class=\"ec-entryhead\"><b>" + esc(id) + "</b>" +
        (bucketLive
          ? " " + chip("ec-chip-ok", "edits bucket present")
          : " " + chip("ec-chip-bad",
              "NO edits bucket (coverage_uncovered)")) +
        "<span class=\"ec-entrybtns\">" +
        "<button type=\"button\" class=\"ec-btn ec-btn-danger\" " +
        "data-ec-action=\"cast-delete:" + i + "\">" + delLabel +
        "</button></span></div>";
      html += "<div class=\"ec-castgrid\">" +
        "<label>id<input type=\"text\" data-cast-idx=\"" + i + "\" " +
        "data-cast-field=\"id\" value=\"" + esc(entry.id) + "\"></label>" +
        "<label>label<input type=\"text\" data-cast-idx=\"" + i + "\" " +
        "data-cast-field=\"label\" value=\"" + esc(entry.label) + "\"></label>" +
        "<label>source<select data-cast-idx=\"" + i + "\" " +
        "data-cast-field=\"source\">";
      for (var s = 0; s < CAST_SOURCES.length; s++) {
        var src = CAST_SOURCES[s];
        html += "<option value=\"" + esc(src) + "\"" +
          (String(entry.source) === src ? " selected" : "") + ">" +
          esc(src) + "</option>";
      }
      html += "</select></label>" +
        "<label>pdb_id<input type=\"text\" data-cast-idx=\"" + i + "\" " +
        "data-cast-field=\"pdb_id\" value=\"" + esc(entry.pdb_id) +
        "\"></label>" +
        "<label>character<input type=\"text\" data-cast-idx=\"" + i + "\" " +
        "data-cast-field=\"character\" value=\"" + esc(entry.character) +
        "\"></label>" +
        "<label>claim_id<input type=\"text\" data-cast-idx=\"" + i + "\" " +
        "data-cast-field=\"claim_id\" value=\"" + esc(entry.claim_id) +
        "\"> " + claimChipHtml(entry.claim_id) + "</label>" +
        "</div></div>";
    }
    html += "</div>";

    // cast-add form
    if (castNewState && castNewState.open) {
      var st = castNewState;
      var id = trimText(st.id);
      var carriers = tagCarriers();
      var tagMissing = id ? tagCarrierIds(carriers, id).length === 0 : false;
      html += "<div class=\"ec-entryform\">";
      html += "<div class=\"ec-formtitle\">Add cast entry " +
        "<button type=\"button\" class=\"ec-btn\" " +
        "data-ec-action=\"cast-add-toggle\">Cancel</button></div>";
      html += "<div class=\"ec-castgrid\">" +
        "<label>id<input type=\"text\" data-castnew=\"id\" value=\"" +
        esc(st.id) + "\" placeholder=\"tca.new_enzyme\"></label>" +
        "<label>label<input type=\"text\" data-castnew=\"label\" value=\"" +
        esc(st.label) + "\"></label>" +
        "<label>source<select data-castnew=\"source\">";
      for (var s2 = 0; s2 < CAST_SOURCES.length; s2++) {
        var src2 = CAST_SOURCES[s2];
        html += "<option value=\"" + esc(src2) + "\"" +
          (st.source === src2 ? " selected" : "") + ">" + esc(src2) +
          "</option>";
      }
      html += "</select></label>" +
        "<label>pdb_id<input type=\"text\" data-castnew=\"pdb_id\" value=\"" +
        esc(st.pdb_id) + "\" placeholder=\"XXXX\"></label>" +
        "<label>character<input type=\"text\" data-castnew=\"character\" " +
        "value=\"" + esc(st.character) + "\"></label>" +
        "<label>claim_id<input type=\"text\" data-castnew=\"claim_id\" " +
        "value=\"" + esc(st.claim) + "\"> " +
        (st.claim ? claimChipHtml(st.claim) : "") + "</label>" +
        "</div>";
      html += "<div data-ec-castchecks>" + castAddChecksHtml() + "</div>";
      if (tagMissing) {
        html += "<div class=\"ec-m5row\"><label>" +
          "<input type=\"checkbox\" data-castnew=\"ackTag\"" +
          (st.ackTag ? " checked" : "") + "> " +
          "ACKNOWLEDGE: the enzyme id carries NO edit:enzyme: tag in the " +
          "graph \u2014 the pinned relationship test " +
          "(tests/test_glucose_content.py:404-449) will need updating in " +
          "the SAME commit (tags(K) moves; the count-shift notice names " +
          "the obligations).</label></div>";
      }
      html += "<div class=\"ec-row ec-actions\">" +
        "<button type=\"button\" class=\"ec-btn ec-btn-primary\" " +
        "data-ec-action=\"cast-add\">Add cast entry</button>" +
        "<span class=\"ec-live\" data-ec-live=\"castmsg\"></span></div>";
      html += "</div>";
    } else {
      html += "<div class=\"ec-row\">" +
        "<button type=\"button\" class=\"ec-btn\" " +
        "data-ec-action=\"cast-add-toggle\">+ Add cast entry</button>" +
        "<span class=\"ec-note\">Add requires: an edits bucket with >=1 " +
        "entry; the edit:enzyme: tag in the graph (or an explicit " +
        "acknowledge checkbox for the relationship-test update); " +
        "claim_id \u2208 registry AND approved.</span></div>";
    }
    return html;
  }

  // -------------------------------------------------------------------------
  // Section 4 — the bad-ending pool editor (B10).
  // -------------------------------------------------------------------------

  function poolMemberRows(pool, removeActionPrefix, enzymeId) {
    var html = "";
    var nodesSeen = {};
    for (var i = 0; i < pool.length; i++) {
      var nid = pool[i];
      var node = nid ? EDITOR.nodeById(nid) : null;
      var tier = EDITOR.endingTier(node);
      var bad = false;
      if (!node) {
        bad = true;
      } else if (!isEnding(node)) {
        bad = true;
      }
      var seenKey = enzymeId + ">" + nid;
      if (nodesSeen[seenKey]) {
        bad = true; // duplicate member — flag (the router would double-weight)
      }
      nodesSeen[seenKey] = true;
      html += "<div class=\"ec-poolrow\">" +
        (bad
          ? chip("ec-chip-bad", !node ? "dangling_pool_node: " + nid
              : "pool_node_not_ending: " + nid)
          : chip("ec-chip-ok", nid + (tier ? " [" + tier + "]" : ""))) +
        " <button type=\"button\" class=\"ec-btn\" data-ec-action=\"" +
        removeActionPrefix + ":" + (enzymeId ? esc(enzymeId) + ":" : "") +
        i + "\">Remove</button></div>";
    }
    return html;
  }

  function renderPoolSection() {
    var e = editsBundle();
    var html = "";
    html += "<h2>Bad-ending random pool (B10: the nodes in the random " +
      "pool of bad endings)" + dirtyDot(EDITS_FNAME) + "</h2>";
    if (!e) {
      html += "<div class=\"ec-warnbox\">edits.json did not load \u2014 " +
        "no pool to edit.</div>";
      return html;
    }
    html += "<div class=\"ec-note\"><b>This is the RUNTIME pool</b> \u2014 " +
      "the roulette the EditRouter spins when a player's edit matches no " +
      "known signature (uniform pick via rng.weighted_pick; " +
      "rpg/edit_router.py:151-166). It is NOT edit.prompt's 13 structural " +
      "choices \u2014 that intercepted stub's choice list is never " +
      "player-facing as a menu (07.1-RESEARCH-DATA \u00a75). The two are " +
      "different mechanisms and are labeled differently on purpose.</div>";

    // Global pool
    var pool = (Object.prototype.toString.call(e.bad_ending_pool) ===
                "[object Array]") ? e.bad_ending_pool : [];
    html += "<div class=\"ec-bucket\"><div class=\"ec-buckethead\">" +
      "<b>Global bad_ending_pool</b> " +
      chip("ec-chip-info", pool.length + " member(s)") +
      " " + chip("ec-chip-ok", "length >= 1 enforced") + "</div>";
    html += "<div class=\"ec-note\">NEVER empty: the global pool is the " +
      "ultimate fallback for every enzyme without a per-enzyme override " +
      "\u2014 empty_bad_ending_pool is a validator ERROR and an empty " +
      "effective pool raises EditRoutingError at runtime. Members must be " +
      "existing endings. src: rpg/edit_router.py:172-235.</div>";
    html += poolMemberRows(pool, "pool-global-remove", null);
    html += "<div class=\"ec-row\"><label>Add member (endings only)</label>" +
      "<select data-form-field=\"pool-global-add-select\">" +
      "<option value=\"\">(select an ending…)</option>" +
      nodeOptionsGrouped(poolSel, true) +
      "</select>" +
      "<button type=\"button\" class=\"ec-btn\" " +
      "data-ec-action=\"pool-global-add\">Add to global pool</button></div>";
    html += "</div>";

    // Per-enzyme overrides
    var ids = enzymeIds();
    html += "<div class=\"ec-bucket\"><div class=\"ec-buckethead\">" +
      "<b>Per-enzyme override pools</b> " +
      chip("ec-chip-info", "OVERRIDE semantics \u2014 no merge") + "</div>";
    html += "<div class=\"ec-note\">A per-enzyme bad_ending_pool, when " +
      "present and non-empty, REPLACES the global pool for that enzyme " +
      "(override, no merge). An ABSENT or EMPTY per-enzyme pool is the " +
      "LEGAL FALLBACK to the global pool \u2014 INFO, never an error. " +
      "src: rpg/edit_router.py:193-199.</div>";
    var anyOverride = false;
    for (var i = 0; i < ids.length; i++) {
      var enzymeId = ids[i];
      var enz = enzymeOf(enzymeId);
      if (!enz || !hasOwn(enz, "bad_ending_pool")) continue;
      anyOverride = true;
      var perPool = asArray(enz.bad_ending_pool);
      html += "<div class=\"ec-override\">";
      html += "<div class=\"ec-buckethead\"><b>" + esc(enzymeId) +
        "</b> " + chip("ec-chip-info", perPool.length + " member(s)") +
        "<span class=\"ec-entrybtns\">" +
        "<button type=\"button\" class=\"ec-btn\" " +
        "data-ec-action=\"pool-per-remove-override:" + esc(enzymeId) +
        "\">Remove override (fall back to global)</button></span></div>";
      if (!perPool.length) {
        html += "<div class=\"ec-note ec-note-ok\">Empty override = " +
          "LEGAL FALLBACK to the global pool \u2014 INFO, not an error " +
          "(rpg/edit_router.py:193-199). Add members to make it a real " +
          "override.</div>";
      }
      html += poolMemberRows(perPool, "pool-per-remove", enzymeId);
      html += "<div class=\"ec-row\"><label>Add member (endings only)" +
        "</label><select data-form-field=\"pool-per-add-select:" +
        esc(enzymeId) + "\"><option value=\"\">(select an ending…)</option>" +
        nodeOptionsGrouped(null, true) + "</select>" +
        "<button type=\"button\" class=\"ec-btn\" data-ec-action=\"" +
        "pool-per-add:" + esc(enzymeId) + "\">Add</button></div>";
      html += "</div>";
    }
    if (!anyOverride) {
      html += "<div class=\"ec-note\">No per-enzyme overrides \u2014 every " +
        "bucket falls back to the global pool (the validator reports this " +
        "as the per_enzyme_pool_empty INFO notice).</div>";
    }
    html += "<div class=\"ec-row ec-newbucket\">" +
      "<label>Create an override for</label>" +
      "<select data-form-field=\"pool-create-select\">" +
      "<option value=\"\">(select a bucket…)</option>";
    for (var j = 0; j < ids.length; j++) {
      var enz2 = enzymeOf(ids[j]);
      if (enz2 && hasOwn(enz2, "bad_ending_pool")) continue;
      html += "<option value=\"" + esc(ids[j]) + "\">" + esc(ids[j]) +
        "</option>";
    }
    html += "</select>" +
      "<button type=\"button\" class=\"ec-btn\" " +
      "data-ec-action=\"pool-create\">Create empty override</button>" +
      "<span class=\"ec-note\">Starts empty = legal fallback until you " +
      "add members.</span></div>";
    html += "</div>";
    return html;
  }

  // -------------------------------------------------------------------------
  // Validator strip — the manifest-owned rules surface inline.
  // -------------------------------------------------------------------------

  function renderValidatorStrip() {
    var v = EDITOR._lastValidation;
    if (!v && typeof EDITOR.validateCurrent === "function") {
      try { v = EDITOR.validateCurrent(); } catch (e) { v = null; }
    }
    var html = "";
    html += "<h2>Validator \u2014 manifest rules (re-runs after every " +
      "change)</h2>";
    if (!v || !v.ran) {
      html += "<div class=\"ec-note\">No validation verdict yet \u2014 " +
        "load data first.</div>";
      return html;
    }
    var shown = 0;
    var other = 0;
    var i;
    for (i = 0; i < v.errors.length; i++) {
      var err = v.errors[i];
      if (err && MANIFEST_ISSUE_KINDS[err.kind]) {
        shown++;
        html += "<div class=\"ec-issue\">\u26a0 <b>" + esc(err.kind) +
          "</b> \u2014 " + esc(err.detail || "") + " <span class=\"ec-note\">" +
          esc(err.src || "") + "</span></div>";
      } else {
        other++;
      }
    }
    var noticeCount = 0;
    for (i = 0; i < v.notices.length; i++) {
      var nt = v.notices[i];
      if (nt && MANIFEST_NOTICE_KINDS[nt.kind]) {
        noticeCount++;
        html += "<div class=\"ec-noticeinfo\">\u2139 <b>" + esc(nt.kind) +
          "</b> \u2014 " + esc(nt.detail || "") + "</div>";
      }
    }
    if (!shown && !other) {
      html += "<div class=\"ec-note ec-note-ok\">\u2713 0 validator " +
        "errors \u2014 the manifests are clean.</div>";
    }
    if (other) {
      html += "<div class=\"ec-note\">+ " + other +
        " non-manifest validator error(s) (story nodes \u2014 see the " +
        "node form / the save tab).</div>";
    }
    if (v.blocked) {
      html += "<div class=\"ec-warnbox\">The save panel REFUSES while " +
        "validator errors exist (EDITOR.saveBlocked()).</div>";
    }
    return html;
  }

  // -------------------------------------------------------------------------
  // The entry form's live previews (updated on input — the bundle is
  // never written by field events).
  // -------------------------------------------------------------------------

  function liveEl(name) {
    if (!refs.panel) return null;
    return refs.panel.querySelector("[data-ec-live=\"" + name + "\"]");
  }

  // Find a form select by its data-form-field value via ATTRIBUTE
  // comparison (enzyme ids are data — data never goes into a CSS selector
  // string, which would be an injection-shaped construction).
  function selectByFormField(value) {
    if (!refs.panel) return null;
    var selects = refs.panel.querySelectorAll("select[data-form-field]");
    for (var i = 0; i < selects.length; i++) {
      if (selects[i].getAttribute("data-form-field") === value) {
        return selects[i];
      }
    }
    return null;
  }

  function refreshEntryLive() {
    var st = formState;
    if (!st || !st.open || !refs.panel) return;
    var preview = liveEl("preview");
    var sigEl = liveEl("sig");
    var routeEl = liveEl("route");
    var claimEl = liveEl("claim");
    var msgEl = liveEl("formmsg");
    var normTarget = normalizeTargetText(st.target);
    if (preview) {
      preview.textContent = "normalize preview: \"" + normTarget + "\"";
    }
    var sig = {
      op: st.op,
      target: st.target,
      args: { new_res: st.newRes }
    };
    if (sigEl) {
      sigEl.textContent = "normalized signature: " + normalizeSignature(sig);
    }
    if (routeEl) {
      var node = st.branch ? EDITOR.nodeById(st.branch) : null;
      if (!st.branch) {
        routeEl.textContent = "";
      } else if (!node) {
        routeEl.textContent = "dangling: branch_node not in the graph " +
          "(dangling_edit_branch)";
      } else if (isEnding(node)) {
        routeEl.textContent = "known-wrong routing \u2192 " + st.branch +
          " (an ENDING \u2014 M5 confirmation required below)";
      } else {
        routeEl.textContent = "allowed-fix routing \u2192 " + st.branch +
          " (restored/branch node \u2014 non-ending)";
      }
    }
    if (claimEl) {
      var id = trimText(st.claim);
      claimEl.innerHTML = id ? claimChipHtml(id) : "";
    }
    if (msgEl) msgEl.textContent = "";
  }

  function refreshCastAddLive() {
    if (!castNewState || !castNewState.open || !refs.panel) return;
    var checks = refs.panel.querySelector("[data-ec-castchecks]");
    if (checks) checks.innerHTML = castAddChecksHtml();
  }

  // -------------------------------------------------------------------------
  // Actions.
  // -------------------------------------------------------------------------

  function openEntryForm(enzymeId, index) {
    var st = {
      open: true,
      enzyme: enzymeId,
      index: (typeof index === "number") ? index : -1,
      op: "point_mutation",
      target: "",
      newRes: "",
      branch: "",
      claim: "",
      m5: false
    };
    if (st.index >= 0) {
      var entry = bucketEntries(enzymeId)[st.index];
      if (entry && typeof entry === "object") {
        var sig = (entry.signature && typeof entry.signature === "object")
          ? entry.signature : {};
        st.op = (sig.op === undefined || sig.op === null)
          ? "point_mutation" : String(sig.op);
        st.target = (sig.target === undefined || sig.target === null)
          ? "" : String(sig.target);
        st.newRes = (sig.args && sig.args.new_res !== undefined &&
                     sig.args.new_res !== null)
          ? String(sig.args.new_res) : "";
        st.branch = (entry.branch_node === undefined ||
                     entry.branch_node === null)
          ? "" : String(entry.branch_node);
        st.claim = (entry.claim_id === undefined || entry.claim_id === null)
          ? "" : String(entry.claim_id);
      }
    }
    formState = st;
    renderData();
  }

  function closeEntryForm() {
    formState = null;
    renderData();
  }

  function saveEntry() {
    if (!formState || !formState.open) return;
    var st = formState;
    var enzymeId = st.enzyme;
    var target = trimText(st.target);
    var newRes = trimText(st.newRes);
    var branch = trimText(st.branch);
    var claim = trimText(st.claim);
    var op = trimText(st.op) || "point_mutation";

    if (!hasOwn(enzymeMap(), enzymeId)) {
      showStatus("The bucket \"" + enzymeId + "\" no longer exists.");
      return;
    }
    if (!target) {
      showStatus("signature.target is required (the normalized target " +
        "is what the router matches).");
      return;
    }
    if (!newRes) {
      showStatus("signature.args.new_res is required.");
      return;
    }
    if (!branch) {
      showStatus("branch_node is required \u2014 it must exist in the " +
        "graph (dangling_edit_branch otherwise).");
      return;
    }
    var node = EDITOR.nodeById(branch);
    if (!node) {
      showStatus("branch_node \"" + branch + "\" is not in the graph " +
        "(dangling_edit_branch) \u2014 pick an existing node.");
      return;
    }
    // Duplicate detection WITHIN the bucket: exact normalized-dict
    // equality (target strip+lowercase, args stringified) — the same
    // semantics the router applies at route() (rpg/edit_router.py:122-149)
    // and the JS validator flags as duplicate_signature. REFUSED here so
    // one entry can never become silently unreachable.
    var sig = { op: op, target: target, args: { new_res: newRes } };
    var dup = duplicateOf(enzymeId, sig, st.index);
    if (dup >= 0) {
      showStatus("Refused: duplicate_signature \u2014 exact " +
        "normalized-dict equality with entry #" + dup + " in this bucket " +
        "(normalize: target strip+lowercase, args stringified; " +
        "rpg/edit_router.py:122-149). Two colliding entries would leave " +
        "one silently unreachable at route().");
      return;
    }
    // Known-wrong routing REQUIRES the M5 confirmation.
    if (isEnding(node) && !st.m5) {
      showStatus("Refused: \u201c" + branch + "\u201d is an ENDING \u2014 " +
        "this entry would be a known-wrong routing (zero exist today by " +
        "the M5 decision, STATE 07-01 outcome 4). Tick the M5 " +
        "confirmation checkbox to proceed deliberately.");
      return;
    }
    var entry = {
      signature: sig,
      branch_node: branch,
      claim_id: claim
    };
    if (st.index >= 0) {
      editsEntryUpdate(enzymeId, st.index, {
        op: op, target: target, newRes: newRes,
        branch: branch, claim: claim
      });
    } else {
      editsEntryAdd(enzymeId, entry);
    }
    if (isEnding(node)) {
      showStatus("KNOWN-WRONG entry landed (M5 departure): " + enzymeId +
        " \u2192 " + branch + ". The M5 decision (STATE 07-01 outcome 4) " +
        "kept zero such entries in Phase 7 \u2014 this is a deliberate, " +
        "confirmed change.");
    }
    formState = null;
    renderData();
  }

  function addBucket() {
    var id = trimText(bucketNewId);
    if (!id) {
      showStatus("Type the new bucket's enzyme id first.");
      return;
    }
    if (hasOwn(enzymeMap(), id)) {
      showStatus("A bucket named \"" + id + "\" already exists.");
      return;
    }
    editsBucketAdd(id);
    bucketNewId = "";
  }

  function addCastEntry() {
    if (!castNewState || !castNewState.open) return;
    var st = castNewState;
    var id = trimText(st.id);
    var label = trimText(st.label);
    var pdb = trimText(st.pdb_id);
    var character = trimText(st.character);
    var claim = trimText(st.claim);
    if (!id) {
      showStatus("Cast entry id is required.");
      return;
    }
    if (hasOwn(castIdSet(), id)) {
      showStatus("A cast entry with id \"" + id + "\" already exists " +
        "(cast ids are set members \u2014 duplicates would corrupt the " +
        "relationship pin).");
      return;
    }
    // B7 requirement (a): an edits bucket with >=1 entry. Adding the cast
    // id without it fires the validator's coverage_uncovered error and
    // the save panel refuses — the editor refuses at the source instead.
    if (!editsBucketExistsFor(id)) {
      showStatus("Refused: no edits.json bucket with >=1 entry exists " +
        "for \"" + id + "\" \u2014 the coverage gate requires every cast " +
        "id to have one (coverage_uncovered). Add the bucket + its first " +
        "entry first (the Edits table above does both). " +
        "src: rpg/edit_router.py:238-255.");
      return;
    }
    // B7 requirement (b): the edit:enzyme: tag in the graph — or the
    // explicit acknowledge checkbox for the relationship-test update.
    var carriers = tagCarriers();
    if (!tagCarrierIds(carriers, id).length && !st.ackTag) {
      showStatus("Refused: no node carries edit:enzyme:" + id + " in the " +
        "graph. Add the tag via the node form, or tick the explicit " +
        "acknowledge checkbox (the pinned relationship test " +
        "tests/test_glucose_content.py:404-449 needs updating in the " +
        "same commit).");
      return;
    }
    // B7 requirement (c): claim_id ∈ registry AND approved — never silent.
    var badge = claimBadge(claim);
    if (!claim || badge.label !== "approved") {
      showStatus("Refused: claim_id must be IN the registry AND approved " +
        "(got: " + (!claim ? "none" : badge.label) + "). CAST-* claims " +
        "are approved via the human approval flow; an unapproved " +
        "claim_id never lands silently. src: rpg/citations.py:100-109.");
      return;
    }
    var entry = {
      id: id,
      label: label,
      source: st.source,
      pdb_id: pdb,
      character: character,
      claim_id: claim
    };
    castEntryAdd(entry);
    castNewState = null;
    renderData();
  }

  // -------------------------------------------------------------------------
  // The view + wiring.
  // -------------------------------------------------------------------------

  function renderData() {
    if (!refs.panel || !refs.built) return; // initEditsCast has not run yet
    var b = theBundle();
    if (!b || !b.files) {
      refs.panel.innerHTML =
        "<div class=\"ec-section\">" +
        "<h2>Data tab</h2>" +
        "<div class=\"ec-warnbox\">No data loaded \u2014 the Data tab " +
        "edits rpg/data/edits.json + rpg/data/cast.json from the loaded " +
        "bundle. Load data first: use the boot panel at the top of the " +
        "page (silent probe or folder pick).</div></div>";
      return;
    }
    var carriers = tagCarriers();
    var html = "";
    if (statusMessage) {
      html += "<div class=\"ec-status\" data-ec-status>" +
        esc(statusMessage.text) +
        " <button type=\"button\" class=\"ec-btn\" " +
        "data-ec-action=\"status-dismiss\">Dismiss</button></div>";
    }
    html += "<div class=\"ec-section\">" + renderValidatorStrip() + "</div>";
    html += "<div class=\"ec-section\">" +
      renderKnownWrongSection() + "</div>";
    html += "<div class=\"ec-section\">" + renderEditsSection(carriers) +
      "</div>";
    html += "<div class=\"ec-section\">" + renderCastSection() + "</div>";
    html += "<div class=\"ec-section\">" + renderPoolSection() + "</div>";
    refs.panel.innerHTML = html;
    if (formState && formState.open) refreshEntryLive();
  }

  function formFieldFromEl(t) {
    return t.getAttribute("data-form-field");
  }

  function initEditsCast() {
    refs.panel = document.getElementById("tab-data");
    if (!refs.panel) {
      editorWarn("50_editscast: #tab-data mount missing");
      return;
    }
    refs.built = true;

    // The mark-saved wrapper is installed HERE (init time) because the
    // save layer's asset sorts after this one — by init time its
    // EDITOR.save.markSaved definition exists. Baseline reset BEFORE the
    // wrapped call so its own recomputeDirty (this asset's wrapper) sees
    // current == baseline and the confirmed file stays clean.
    if (EDITOR.save && typeof EDITOR.save.markSaved === "function") {
      var coreMarkSaved = EDITOR.save.markSaved;
      EDITOR.save.markSaved = function (fname) {
        if (fname === EDITS_FNAME || fname === CAST_FNAME) {
          var content = registryContentOf(fname);
          if (content !== null && content !== undefined) {
            registryBaseline[fname] = JSON.stringify(content);
          }
        }
        return coreMarkSaved(fname);
      };
    }

    // clicks — delegated ONCE on the stable panel (survives every
    // innerHTML rebuild).
    EDITOR.delegate(refs.panel, "click", "data-ec-action", function (elx) {
      var action = elx.getAttribute("data-ec-action");
      var wasArmed = armed;
      armed = null;
      if (action === "status-dismiss") {
        statusMessage = null;
        renderData();
        return;
      }
      if (action.indexOf("entry-open-add:") === 0) {
        // The attribute carries the enzyme id after the prefix (ids
        // contain dots, never colons — the suffix split is unambiguous).
        var enzymeId = action.slice("entry-open-add:".length);
        openEntryForm(enzymeId, -1);
        return;
      }
      if (action.indexOf("entry-open-edit:") === 0) {
        var rest = action.slice("entry-open-edit:".length);
        var ci = rest.lastIndexOf(":");
        openEntryForm(rest.slice(0, ci),
          parseInt(rest.slice(ci + 1), 10));
        return;
      }
      if (action === "entry-cancel") {
        closeEntryForm();
        return;
      }
      if (action === "entry-save") {
        saveEntry();
        return;
      }
      if (action.indexOf("entry-delete:") === 0) {
        var rest2 = action.slice("entry-delete:".length);
        var ci2 = rest2.lastIndexOf(":");
        editsEntryDelete(rest2.slice(0, ci2),
          parseInt(rest2.slice(ci2 + 1), 10));
        return;
      }
      if (action.indexOf("bucket-delete:") === 0) {
        var bid = action.slice("bucket-delete:".length);
        if (wasArmed !== "bucket-delete:" + bid) {
          armed = "bucket-delete:" + bid; // two-step arm/confirm
          renderData();
          return;
        }
        editsBucketDelete(bid);
        return;
      }
      if (action === "bucket-add") {
        addBucket();
        return;
      }
      if (action === "cast-add-toggle") {
        castNewState = (castNewState && castNewState.open)
          ? null
          : { open: true, id: "", label: "", source: "download",
              pdb_id: "", character: "glucose", claim_id: "",
              ackTag: false };
        renderData();
        return;
      }
      if (action === "cast-add") {
        addCastEntry();
        return;
      }
      if (action.indexOf("cast-delete:") === 0) {
        var cidx = parseInt(action.slice("cast-delete:".length), 10);
        if (wasArmed !== "cast-delete:" + cidx) {
          armed = "cast-delete:" + cidx;
          renderData();
          return;
        }
        castEntryDelete(cidx);
        return;
      }
      if (action.indexOf("pool-global-remove:") === 0) {
        var gidx = parseInt(action.slice("pool-global-remove:".length), 10);
        editsGlobalPoolRemove(gidx);
        return;
      }
      if (action === "pool-global-add") {
        var sel = selectByFormField("pool-global-add-select");
        var nid = sel ? sel.value : "";
        if (!nid) {
          showStatus("Select an ending node to add to the global pool.");
          return;
        }
        editsGlobalPoolAdd(nid);
        return;
      }
      if (action.indexOf("pool-per-add:") === 0) {
        var pid = action.slice("pool-per-add:".length);
        // Attribute-value comparison (never a quoted CSS selector —
        // enzyme ids are data, and data never goes into selectors).
        var psel = selectByFormField(
          "pool-per-add-select:" + pid);
        var pnid = psel ? psel.value : "";
        if (!pnid) {
          showStatus("Select an ending node to add to the override pool.");
          return;
        }
        editsPerPoolAdd(pid, pnid);
        return;
      }
      if (action.indexOf("pool-per-remove:") === 0) {
        var rest3 = action.slice("pool-per-remove:".length);
        var ci3 = rest3.lastIndexOf(":");
        editsPerPoolRemove(rest3.slice(0, ci3),
          parseInt(rest3.slice(ci3 + 1), 10));
        return;
      }
      if (action.indexOf("pool-per-remove-override:") === 0) {
        editsPerPoolRemoveOverride(
          action.slice("pool-per-remove-override:".length));
        return;
      }
      if (action === "pool-create") {
        var csel = selectByFormField("pool-create-select");
        var cid = csel ? csel.value : "";
        if (!cid) {
          showStatus("Select the bucket to create the override for.");
          return;
        }
        editsPerPoolCreate(cid);
        return;
      }
    });

    // form field changes (selects + checkbox) — LOCAL state only; the
    // bundle is written exclusively by the explicit action buttons. One
    // shared handler for BOTH input and change (selects/checkboxes fire
    // change everywhere and input in every current browser — handling
    // both keeps text/select/checkbox updates symmetric).
    function handleFormFieldEvent(t, evType) {
      var f = formFieldFromEl(t);
      if (f && formState && formState.open) {
        if (f === "op") {
          formState.op = t.value;
          refreshEntryLive();
        } else if (f === "branch") {
          if (evType === "change") {
            formState.branch = t.value;
            formState.m5 = false; // re-confirm on every target change
            renderData();
          }
        } else if (f === "m5") {
          formState.m5 = !!t.checked;
        } else if (evType === "input") {
          // text fields: LOCAL draft state + live previews only (never a
          // bundle write — the undo pre-image stays the true pre-edit
          // value, the same granularity contract as the core's
          // textFieldBindings).
          if (f === "target") {
            formState.target = t.value;
            refreshEntryLive();
          } else if (f === "new_res") {
            formState.newRes = t.value;
            refreshEntryLive();
          } else if (f === "claim_id") {
            formState.claim = t.value;
            refreshEntryLive();
          }
        }
        return;
      }
      if (evType === "change") {
        var cf = t.getAttribute("data-cast-field");
        if (cf !== null && cf !== undefined &&
            t.getAttribute("data-cast-idx") !== null) {
          // Inline cast field commit: change = ONE undo step per field
          // (the apply triggers afterChange -> hooks -> rerender, which
          // refreshes the claim chips + relationship pin).
          castFieldSet(parseInt(t.getAttribute("data-cast-idx"), 10),
            cf, t.value);
          return;
        }
      }
      if (f === "pool-global-add-select") {
        poolSel = t.value; // survives rerenders while the picker is open
        return;
      }
      if (f === "bucket-new-id") {
        bucketNewId = t.value;
        return;
      }
      var cn = t.getAttribute("data-castnew");
      if (cn && castNewState && castNewState.open) {
        if (cn === "ackTag") {
          castNewState.ackTag = !!t.checked;
        } else {
          castNewState[cn] = t.value;
        }
        refreshCastAddLive();
      }
    }

    refs.panel.addEventListener("change", function (ev) {
      var t = ev.target;
      if (t && t.getAttribute) handleFormFieldEvent(t, "change");
    });
    refs.panel.addEventListener("input", function (ev) {
      var t = ev.target;
      if (t && t.getAttribute) handleFormFieldEvent(t, "input");
    });

    renderData();
  }

  EDITOR.view("data", renderData);
  EDITOR.init(initEditsCast);

  // -------------------------------------------------------------------------
  // Per-asset CSS (the shell carries structural layout ONLY — each asset
  // injects its own styles at runtime; 00_core's injectCss primitive).
  // -------------------------------------------------------------------------
  EDITOR.injectCss(
    "/* co-owned by 50_editscast.js (07.1-14): the Data tab */\n" +
    ".ec-section { border: 1px solid #d5dbe5; border-radius: 6px; " +
    "margin: 10px 14px; padding: 10px 12px; background: #ffffff; }\n" +
    ".ec-section h2 { font-size: 15px; margin: 0 0 6px; " +
    "border-bottom: 1px solid #e0e4ec; padding-bottom: 4px; }\n" +
    ".ec-note { font-size: 12.5px; color: #555555; margin: 4px 0; }\n" +
    ".ec-note-ok { color: #2d6a2d; }\n" +
    ".ec-warnbox { border: 1px solid #d9a441; background: #fdf6e3; " +
    "border-radius: 4px; padding: 6px 8px; font-size: 12.5px; " +
    "margin: 6px 0; }\n" +
    ".ec-status { border: 1px solid #6a8fc9; background: #eef4fc; " +
    "border-radius: 4px; padding: 6px 8px; font-size: 12.5px; " +
    "margin: 0 14px; }\n" +
    ".ec-bucket { border: 1px solid #e0e4ec; border-radius: 4px; " +
    "margin: 8px 0; padding: 6px 8px; }\n" +
    ".ec-buckethead { margin: 2px 0 6px; }\n" +
    ".ec-enzyme { font-family: Consolas, monospace; font-size: 13px; }\n" +
    ".ec-entry { border: 1px solid #eceff4; border-radius: 4px; " +
    "margin: 6px 0; padding: 5px 8px; background: #fbfcfe; }\n" +
    ".ec-entry-dup { border-color: #c0392b; background: #fdf0ee; }\n" +
    ".ec-entry-knownwrong { border-color: #d9a441; }\n" +
    ".ec-entryhead { margin: 1px 0 4px; }\n" +
    ".ec-entrybody { font-size: 12.5px; color: #444444; }\n" +
    ".ec-entrybtns { float: right; }\n" +
    ".ec-btn { padding: 2px 8px; font-size: 12px; cursor: pointer; }\n" +
    ".ec-btn-primary { background: #2e3440; color: #ffffff; " +
    "border: 1px solid #2e3440; }\n" +
    ".ec-btn-danger { border: 1px solid #b5442d; color: #b5442d; " +
    "background: #ffffff; }\n" +
    ".ec-chip { display: inline-block; border-radius: 9px; " +
    "padding: 0 7px; font-size: 11px; margin: 1px 2px 1px 0; " +
    "white-space: nowrap; }\n" +
    ".ec-chip-ok { background: #e3f2e3; color: #2d6a2d; " +
    "border: 1px solid #9fc99f; }\n" +
    ".ec-chip-warn { background: #fdf3dd; color: #8a6d1a; " +
    "border: 1px solid #d9a441; }\n" +
    ".ec-chip-bad { background: #fdeceb; color: #a12611; " +
    "border: 1px solid #d98880; }\n" +
    ".ec-chip-info { background: #eef1f6; color: #4a5568; " +
    "border: 1px solid #b9c2d0; }\n" +
    ".ec-row { margin: 5px 0; display: flex; align-items: center; " +
    "gap: 8px; flex-wrap: wrap; }\n" +
    ".ec-row label { min-width: 170px; font-size: 12px; color: #666666; }\n" +
    ".ec-row input[type=\"text\"], .ec-row select { font-size: 12.5px; " +
    "padding: 2px 4px; }\n" +
    ".ec-live { font-family: Consolas, monospace; font-size: 11.5px; " +
    "color: #555555; }\n" +
    ".ec-entryform { border: 1px dashed #9aa3b2; border-radius: 4px; " +
    "margin: 8px 0; padding: 8px 10px; background: #f7f9fc; }\n" +
    ".ec-formtitle { margin-bottom: 6px; }\n" +
    ".ec-m5row { border: 1px solid #d9a441; background: #fdf6e3; " +
    "border-radius: 4px; padding: 6px 8px; margin: 6px 0; " +
    "font-size: 12.5px; }\n" +
    ".ec-m5row label { min-width: 0; }\n" +
    ".ec-m5panel { border: 1px solid #d9a441; background: #fdf6e3; " +
    "border-radius: 4px; padding: 6px 8px; margin: 6px 0; " +
    "font-size: 12.5px; }\n" +
    ".ec-relpin { border: 2px solid #3a3f4b; border-radius: 4px; " +
    "padding: 6px 8px; margin: 8px 0; background: #f5f6f8; }\n" +
    ".ec-relformula { font-size: 13px; }\n" +
    ".ec-relchips { margin-top: 5px; }\n" +
    ".ec-check { font-size: 12.5px; margin: 2px 0; color: #a12611; }\n" +
    ".ec-check-ok { color: #2d6a2d; }\n" +
    ".ec-issue { font-size: 12.5px; color: #a12611; margin: 2px 0; }\n" +
    ".ec-noticeinfo { font-size: 12.5px; color: #4a5568; margin: 2px 0; }\n" +
    ".ec-poolrow { margin: 3px 0; font-size: 12.5px; }\n" +
    ".ec-override { border: 1px solid #e0e4ec; border-radius: 4px; " +
    "margin: 6px 0; padding: 5px 8px; }\n" +
    ".ec-castgrid { display: grid; grid-template-columns: 1fr 1fr; " +
    "gap: 4px 14px; margin: 4px 0; }\n" +
    ".ec-castgrid label { font-size: 11px; color: #888888; " +
    "display: flex; flex-direction: column; gap: 2px; }\n" +
    ".ec-dirty { color: #b5442d; font-weight: bold; font-size: 12px; }\n" +
    "code { font-family: Consolas, monospace; font-size: 12px; }\n"
  );

})();
