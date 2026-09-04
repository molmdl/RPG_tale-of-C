/* ==========================================================================
 * 40_form.js — the node form: identity, texts, claims, tags, ending (07.1-09).
 *
 * OWNS: the #node-form-identity sub-section of the shell's #node-form aside
 * (the shell's FIXED mount point; the choices/on_enter/lifecycle sub-sections
 * belong to 42_choices.js / 43_onenter.js / 45_lifecycle.js — never touched
 * here). Loads after 00_core.js (EDITOR contract), 05_json.js, 10_load.js,
 * 20_validate.js (validator whose verdicts this form surfaces inline) and
 * 30_graph.js (whose click-select feeds EDITOR.select -> this form).
 *
 * ============================================================================
 * B6 FIELD MAPPING (research-pinned schema fact — 07.1-RESEARCH-UI "Standard
 * Stack" + 07.1-RESEARCH-DATA §1.3; the engine + the 5.4 conformance battery
 * consume this exact 6-key node schema):
 *
 *     title            = THE NODE ID (displayed large; NOT an editable field)
 *     story            = text_dramatic
 *     science          = text_teaching
 *     reference/links  = claim_ids, resolved LIVE through
 *                        bundle.citations[claim_id] -> source_id ->
 *                        bundle.sources (url) — full panel = 07.1-12
 *
 * THERE IS NO "title" FIELD IN THE SCHEMA AND NONE IS INVENTED HERE. The
 * data carries exactly: text_dramatic, text_teaching, claim_ids, tags,
 * on_enter, choices (+ is_ending on the 21 endings — present ONLY on
 * endings, ABSENT — never null — elsewhere). A literal editable title field
 * would be a SCHEMA CHANGE requiring engine + gate sign-off — OUT OF SCOPE
 * for this editor; flagged to the human in the plan SUMMARY (07.1-09).
 * ============================================================================
 *
 * WHAT THE FORM RENDERS (selection-driven editing — RESEARCH-UI structural
 * choice 4: one form panel covers the identity/content half of B2 + B6):
 *   1. Identity header — node id AS the title (B6a) + derived-kind badge(s)
 *      (EDITOR.deriveKind port; kinds are DERIVED, never stored) + tier chip
 *      (from is_ending ONLY — the 3 anaerobic endings carry is_ending but no
 *      ending:* tag, 07.1-RESEARCH-DATA §1.5) + file placement.
 *   2. Text editors (B6b/c) — two textareas bound data-field="text_dramatic"
 *      / "text_teaching" through EDITOR.textFieldBindings: commit on change
 *      = ONE undo step per field commit (never per keystroke); live preview
 *      on input updates only the character counters. The validator asset
 *      (20_validate.js) re-runs after every commit; text_layer_empty /
 *      tbd_text errors for this node surface inline under the fields.
 *   3. Claim chips + claim_ids editor (B6d + C groundwork) — one chip per
 *      claim_id with a LIVE approval badge from bundle.citations (approved =
 *      green, pending = amber, rejected = red, unresolved = MISSING red;
 *      strict `approval_status === "approved"` semantics, rpg/citations.py:
 *      100-109) + review_tier tag. Clicking a chip calls the
 *      EDITOR.ui.claimFocus(claimId) hook — consumed by the claims panel
 *      (70_claims.js, 07.1-12); a safe no-op until it lands. An add-input +
 *      a remove ✕ per chip mutate claim_ids through the 00_core mutators
 *      (nodeSet with an edited COPY — order preserved). PLACEHOLDER_PHASE8
 *      is the sanctioned residual, allowed ONLY on fa.stub / alc.stub; a
 *      violation surfaces as the validator's placeholder_misuse error inline.
 *   4. Tags editor (B2 partial) — chip list + add-input + quick-add
 *      suggestions for the KNOWN vocabulary (counts documented from
 *      07.1-RESEARCH-DATA §1.5, verified against the live data 2026-09-05);
 *      add/remove run through the mutators; the validator's tag-rule errors
 *      (offer_without_tag etc.) surface inline.
 *   5. is_ending select (B2) — none/true/good/normal/bad. "none" REMOVES the
 *      key (absent, never null — model.py:250-252); a tier value sets it.
 *      An inline note reminds that the ending convention wants the matching
 *      ending:<tier> + stage:* tags, empty choices and reachability — the
 *      validator surfaces the real errors (unreachable_ending,
 *      pool_node_not_ending, ...). Router-only / restored / stub nodes show
 *      an informational note when their special shape is touched.
 *   6. B9 reminder — when the node is an ending, a pinned info banner:
 *      the Phase-12 cutscene-render reminder (a reminder, NOT a field).
 *   7. Unknown-key safety (B11) — any key outside the known schema renders
 *      in a read-only "extra keys" list with a warning icon: NEVER editable
 *      here, NEVER deleted — unknown keys must round-trip untouched through
 *      every edit (the engine tolerates them; the 00_core mutators touch
 *      only named fields).
 *
 * MUTATION DISCIPLINE: this form NEVER writes the bundle directly — every
 * change flows through EDITOR.nodeSet / EDITOR.apply (one undo step each,
 * per-file dirty marking, afterChange fan-out). Listeners are DELEGATED on
 * the stable #node-form aside (one listener per concern — event delegation,
 * RESEARCH-UI structural choice 2): the container survives re-renders, only
 * the identity sub-section's innerHTML is rebuilt.
 *
 * VALIDATOR INTEGRATION: reads EDITOR._lastValidation (cached by the
 * 20_validate.js hook after every mutation) and shows this node's errors
 * inline, bucketed to the section that owns the rule (text / claims / tags
 * / ending / other). Read-only consumption — the validator is never invoked
 * with mutated state from here.
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

  // B9 reminder (roadmap B9): endings want a cutscene render that is Phase-12
  // territory — the editor tracks it as a REMINDER, never a field.
  var B9_REMINDER_TEXT =
    "Ending CG (cutscene render) is Phase-12 territory \u2014 the editor " +
    "tracks this as a reminder, not a field (roadmap B9).";

  // The known node schema (07.1-RESEARCH-DATA §1.3): every node carries
  // exactly these 6 keys; the 21 endings add is_ending. Anything else is an
  // unknown key -> the read-only B11 guard section. (The node "id" the core
  // stamps is a NON-enumerable property — invisible to for-in, so it never
  // shows up here either.)
  var KNOWN_NODE_KEYS = {
    text_dramatic: true,
    text_teaching: true,
    claim_ids: true,
    tags: true,
    on_enter: true,
    choices: true,
    is_ending: true
  };

  var ENDING_TIERS = ["true", "good", "normal", "bad"];

  // The sanctioned Phase-8 residual claim (allowed ONLY on fa.stub/alc.stub;
  // 07.1-08 validator placeholder_misuse rule + test_glucose_content.py).
  var PLACEHOLDER_CLAIM = "PLACEHOLDER_PHASE8";
  var SANCTIONED_STUB_IDS = { "fa.stub": true, "alc.stub": true };

  // Known tag vocabulary (07.1-RESEARCH-DATA §1.5; counts verified against
  // the committed data 2026-09-05). Literal quick-add candidates + the
  // documented counts legend. edit:enzyme:<id> is parameterized — its
  // concrete candidates come from bundle.edits.enzymes at render time
  // (13 buckets; 14 distinct tag values — tca.citrate_synthase carries the
  // tag without an edits.json bucket).
  var TAG_VOCAB = [
    { tag: "stage:intro", count: "5 nodes" },
    { tag: "stage:glycolysis", count: "7 nodes" },
    { tag: "stage:pyruvate", count: "2 nodes" },
    { tag: "stage:anaerobic", count: "5 nodes" },
    { tag: "stage:tca", count: "15 nodes" },
    { tag: "stage:etc", count: "8 nodes" },
    { tag: "edit:enzyme:<id>", count: "15 nodes, 14 distinct values (the edits.json buckets + tca.citrate_synthase)" },
    { tag: "edit:structural", count: "1 node (tca.citrate_synthase)" },
    { tag: "edit:prompt", count: "1 node (edit.prompt)" },
    { tag: "edit:known", count: "3 nodes" },
    { tag: "edit:known_critical", count: "1 node" },
    { tag: "edit:unknown", count: "9 nodes" },
    { tag: "ending:true", count: "1 node" },
    { tag: "ending:good", count: "2 nodes" },
    { tag: "ending:normal", count: "1 node" },
    { tag: "ending:bad", count: "14 nodes" },
    { tag: "rng:weighted", count: "1 node (tca.shuffle — the only weighted node)" },
    { tag: "preface", count: "2 nodes" },
    { tag: "char:glucose", count: "1 node" },
    { tag: "cycle_trap", count: "1 node (bad.cycle_trap_host_death)" }
  ];

  // Validator error kinds -> the form section that owns the rule (used to
  // bucket the inline flags). Kinds not listed fall into "other".
  var ISSUE_SECTION = {
    text_layer_empty: "text",
    tbd_text: "text",
    claim_missing: "claims",
    claim_unapproved: "claims",
    placeholder_misuse: "claims",
    offer_without_tag: "tags",
    unreachable_ending: "ending",
    pool_node_not_ending: "ending",
    dangling_pool_node: "ending",
    empty_bad_ending_pool: "ending"
  };

  // -------------------------------------------------------------------------
  // Module state.
  // -------------------------------------------------------------------------

  var refs = { form: null, identity: null };
  // The last special-shape touch (set when is_ending changes on a
  // router-only / restored / stub node; cleared when another node is
  // selected) — drives the "special shape touched" informational note.
  var lastTouch = null;

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

  // Incoming-choice count (router-only detection): a node with zero
  // incoming choice.goto edges is entered ONLY via the edit router (the
  // restored-node pattern, 07-12) or is simply orphaned (validator flags).
  function incomingCount(nid) {
    var all = EDITOR.allNodes();
    var count = 0;
    for (var i = 0; i < all.length; i++) {
      var node = all[i].node;
      var choices = (node && Object.prototype.toString.call(node.choices) ===
                     "[object Array]") ? node.choices : null;
      if (!choices) continue;
      for (var j = 0; j < choices.length; j++) {
        var c = choices[j];
        if (c && typeof c === "object" && c.goto === nid) count++;
      }
    }
    return count;
  }

  // The node's special structural shape, as display facts ("" if none).
  function specialFacts(node) {
    var kind = EDITOR.deriveKind(node);
    var facts = [];
    if (kind === "phase8-stub") {
      facts.push("Phase-8 stub (returns in Phase 8; sanctioned " +
                 "PLACEHOLDER_PHASE8 residual)");
    }
    if (kind === "edit-prompt") {
      facts.push("the edit.prompt hub (the intercepted structural stub the " +
                 "edit router routes through)");
    }
    if (kind === "restored") {
      facts.push("a restoration node (known-edit reveal; on_enter sequence " +
                 "pinned: edit, load, align, show_as)");
    }
    if (node && node.id && incomingCount(node.id) === 0) {
      facts.push("router-only entry (no incoming choice.goto edge — the " +
                 "engine routes known edits directly to it)");
    }
    return facts.join("; ");
  }

  // -------------------------------------------------------------------------
  // The EDITOR.ui extension point. claimFocus is the C-groundwork hook: the
  // claims panel (70_claims.js, 07.1-12) REPLACES/EXTENDS it to switch to
  // the claims tab and open the claim. Until that asset lands this default
  // is a SAFE NO-OP (a console info, never an error).
  // -------------------------------------------------------------------------

  if (!EDITOR.ui) EDITOR.ui = {};
  if (typeof EDITOR.ui.claimFocus !== "function") {
    EDITOR.ui.claimFocus = function (claimId) {
      try {
        if (typeof console !== "undefined" && console && console.info) {
          console.info("EDITOR.ui.claimFocus(\"" + String(claimId) +
                       "\"): claims panel not loaded yet (70_claims.js, " +
                       "07.1-12) — no-op.");
        }
      } catch (e) { /* safe no-op */ }
    };
  }

  // -------------------------------------------------------------------------
  // Mutations — ALL through the 00_core mutators (B11 contract: touch only
  // the named field; unknown keys round-trip untouched). claim_ids/tags are
  // edited on a COPY so order is preserved and one apply = one undo step.
  // -------------------------------------------------------------------------

  function mutateList(fname, nid, field, mutate) {
    var node = EDITOR.nodeGet(fname, nid);
    if (!node) return;
    var list = Object.prototype.toString.call(node[field]) ===
      "[object Array]" ? node[field].slice(0) : [];
    var result = mutate(list);
    if (result === false) return; // mutation declined (duplicate/no-op)
    EDITOR.nodeSet(fname, nid, field, list);
  }

  function addClaim(fname, nid, rawId) {
    var claimId = String(rawId == null ? "" : rawId).replace(/^\s+|\s+$/g, "");
    if (!claimId) return;
    var node = EDITOR.nodeGet(fname, nid);
    var current = (node && Object.prototype.toString.call(node.claim_ids) ===
                   "[object Array]") ? node.claim_ids : [];
    for (var i = 0; i < current.length; i++) {
      if (current[i] === claimId) {
        showNote("Claim \"" + esc(claimId) +
                 "\" is already referenced by this node.");
        return;
      }
    }
    mutateList(fname, nid, "claim_ids", function (list) {
      list.push(claimId); // order preserved: appended at the end
      return list;
    });
  }

  function removeClaim(fname, nid, index) {
    mutateList(fname, nid, "claim_ids", function (list) {
      if (index >= 0 && index < list.length) list.splice(index, 1);
      return list;
    });
  }

  function addTag(fname, nid, rawTag) {
    var tag = String(rawTag == null ? "" : rawTag).replace(/^\s+|\s+$/g, "");
    if (!tag) return;
    var node = EDITOR.nodeGet(fname, nid);
    var current = (node && Object.prototype.toString.call(node.tags) ===
                   "[object Array]") ? node.tags : [];
    for (var i = 0; i < current.length; i++) {
      if (current[i] === tag) {
        showNote("Tag \"" + esc(tag) + "\" is already on this node.");
        return;
      }
    }
    mutateList(fname, nid, "tags", function (list) {
      list.push(tag); // order preserved: appended at the end
      return list;
    });
  }

  function removeTag(fname, nid, index) {
    mutateList(fname, nid, "tags", function (list) {
      if (index >= 0 && index < list.length) list.splice(index, 1);
      return list;
    });
  }

  // is_ending set/unset. "none" REMOVES the key entirely — the schema keeps
  // is_ending ABSENT (never null) on non-endings (model.py:250-252; the key
  // removal below is the ONLY allowed shape-change here and touches only
  // that one key per the B11 mutator contract). A tier value sets the key.
  function applyEnding(fname, nid, value) {
    var node = EDITOR.nodeGet(fname, nid);
    if (!node) return;
    var tier = String(value == null ? "" : value);
    // Remember a special-shape touch for the informational note (rendered
    // after the mutation's re-render).
    var facts = specialFacts(node);
    lastTouch = facts ? { id: nid, facts: facts } : null;

    if (tier === "") {
      if (Object.prototype.hasOwnProperty.call(node, "is_ending")) {
        EDITOR.apply({
          files: [fname],
          redo: function (b) {
            var n = (b && b.files && b.files[fname] && b.files[fname].nodes)
              ? b.files[fname].nodes[nid] : null;
            if (n) {
              // is_ending removal: the key becomes ABSENT (never null) —
              // B11-safe: this touches ONLY the is_ending key.
              delete n.is_ending;
            }
          }
        });
      }
    } else {
      EDITOR.nodeSet(fname, nid, "is_ending", tier);
    }
  }

  // -------------------------------------------------------------------------
  // Validator consumption (read-only): this node's errors, bucketed by the
  // section that owns the rule. EDITOR._lastValidation is refreshed by the
  // 20_validate.js hook after every mutation; defensively re-run it if the
  // cache is cold (e.g. the validator asset landed but no mutation happened
  // since load).
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

  function renderIssues(errors, section) {
    var html = "";
    for (var i = 0; i < errors.length; i++) {
      var err = errors[i];
      if (ISSUE_SECTION[err.kind] !== section) continue;
      html += "<div class=\"form-issue\">\u26a0 <b>" + esc(err.kind) +
        "</b> \u2014 " + esc(err.detail || "") + "</div>";
    }
    return html;
  }

  function otherIssues(errors) {
    var html = "";
    for (var i = 0; i < errors.length; i++) {
      var err = errors[i];
      if (ISSUE_SECTION[err.kind]) continue; // bucketed to its own section
      html += "<div class=\"form-issue\">\u26a0 <b>" + esc(err.kind) +
        "</b> \u2014 " + esc(err.detail || "") + "</div>";
    }
    return html;
  }

  // -------------------------------------------------------------------------
  // Claim chip badge — LIVE resolution against bundle.citations. Strict
  // `approval_status === "approved"` semantics (rpg/citations.py:100-109);
  // an unresolved id renders MISSING (red) — PLACEHOLDER_PHASE8 is exactly
  // this state on the sanctioned stubs.
  // -------------------------------------------------------------------------

  function claimBadge(claimId) {
    var b = EDITOR.state.bundle;
    var cits = (b && b.citations) ? b.citations : {};
    var rec = Object.prototype.hasOwnProperty.call(cits, claimId)
      ? cits[claimId] : null;
    if (!rec || typeof rec !== "object") {
      return { cls: "claim-badge-missing", label: "MISSING", tier: "" };
    }
    var status = rec.approval_status;
    var tier = rec.review_tier ? String(rec.review_tier) : "";
    if (status === "approved") {
      return { cls: "claim-badge-approved", label: "approved", tier: tier };
    }
    if (status === "pending") {
      return { cls: "claim-badge-pending", label: "pending", tier: tier };
    }
    if (status === "rejected") {
      return { cls: "claim-badge-rejected", label: "rejected", tier: tier };
    }
    return { cls: "claim-badge-missing", label: "MISSING", tier: tier };
  }

  function placeholderNote(node) {
    var claims = (node && Object.prototype.toString.call(node.claim_ids) ===
                  "[object Array]") ? node.claim_ids : [];
    for (var i = 0; i < claims.length; i++) {
      if (claims[i] === PLACEHOLDER_CLAIM) {
        var sanctioned = node.id && SANCTIONED_STUB_IDS[node.id];
        if (sanctioned) {
          return "<div class=\"form-note form-note-ok\">" +
            "PLACEHOLDER_PHASE8 is the sanctioned residual \u2014 allowed " +
            "ONLY on fa.stub / alc.stub (validator rule " +
            "<b>placeholder_misuse</b>).</div>";
        }
        return "<div class=\"form-note form-note-warn\">" +
          "PLACEHOLDER_PHASE8 here is a \u26a0 violation: the sanctioned " +
          "residual is allowed ONLY on fa.stub / alc.stub (validator rule " +
          "<b>placeholder_misuse</b>).</div>";
      }
    }
    return "";
  }

  // -------------------------------------------------------------------------
  // Section renderers (return HTML strings; everything data-derived goes
  // through esc()).
  // -------------------------------------------------------------------------

  function kindChipHtml(node) {
    var kind = EDITOR.deriveKind(node);
    return "<span class=\"form-kind-chip form-kind-" +
      esc(kind.replace(/[^a-z0-9-]/g, "-")) + "\">" + esc(kind) + "</span>";
  }

  function tierChipHtml(node) {
    var tier = EDITOR.endingTier(node);
    if (!tier) return "";
    return "<span class=\"form-tier-chip\">tier: " + esc(tier) + "</span>";
  }

  function renderIdentityHeader(node, fname) {
    var html = "";
    var tier = EDITOR.endingTier(node);
    if (tier) {
      // B9 reminder — PINNED at the top of the form whenever the node is an
      // ending (is_ending set). A reminder, never a field.
      html += "<div class=\"form-b9-banner\">\u2139 " +
        esc(B9_REMINDER_TEXT) + "</div>";
    }
    // B6a: the node id IS the title (id-as-title). Rendered LARGE,
    // read-only — never an editable field (there is NO title field in the
    // schema; see the header comment's B6 mapping + schema-change rule).
    html += "<div class=\"form-id-line\">" +
      "<span class=\"form-id-name\">" + esc(node.id) + "</span>" +
      kindChipHtml(node) + tierChipHtml(node) + "</div>";
    html += "<div class=\"form-id-file\">in " + esc(fname) +
      " &middot; B6 mapping: title = id &middot; story = text_dramatic " +
      "&middot; science = text_teaching &middot; reference/links = " +
      "claim_ids (live-resolved)</div>";
    var facts = specialFacts(node);
    if (facts) {
      html += "<div class=\"form-note form-note-info\">\u2139 Special " +
        "shape: " + esc(facts) + ". Structural conventions are pinned by " +
        "the gates \u2014 the validator re-checks every change.</div>";
    }
    return html;
  }

  function renderTexts(node, errors) {
    var dramatic = (typeof node.text_dramatic === "string")
      ? node.text_dramatic : "";
    var teaching = (typeof node.text_teaching === "string")
      ? node.text_teaching : "";
    var nid = esc(node.id);
    var fname = esc(selectedFile() || "");
    var html = "";
    html += "<h4>Story (dramatic layer) <span class=\"form-char-count\" " +
      "data-charcount=\"text_dramatic\">" + dramatic.length + " chars</span></h4>";
    html += "<textarea class=\"json-area form-textarea\" rows=\"4\" " +
      "data-field=\"text_dramatic\" data-node=\"" + nid +
      "\" data-file=\"" + fname + "\">" + esc(dramatic) + "</textarea>";
    html += "<h4>Science (teaching layer) <span class=\"form-char-count\" " +
      "data-charcount=\"text_teaching\">" + teaching.length + " chars</span></h4>";
    html += "<textarea class=\"json-area form-textarea\" rows=\"4\" " +
      "data-field=\"text_teaching\" data-node=\"" + nid +
      "\" data-file=\"" + fname + "\">" + esc(teaching) + "</textarea>";
    html += renderIssues(errors, "text");
    return html;
  }

  function renderClaims(node, errors) {
    var nid = esc(node.id);
    var fname = esc(selectedFile() || "");
    var claims = (node && Object.prototype.toString.call(node.claim_ids) ===
                  "[object Array]") ? node.claim_ids : [];
    var html = "";
    html += "<h4>References &amp; claims (claim_ids)</h4>";
    if (!claims.length) {
      html += "<div class=\"form-none\">no claim_ids \u2014 this node " +
        "makes no citation claims</div>";
    }
    html += "<div class=\"form-chip-list\">";
    for (var i = 0; i < claims.length; i++) {
      var claimId = String(claims[i]);
      var badge = claimBadge(claimId);
      // The chip and its remove button are SIBLINGS (never nested) so a
      // click on the ✕ never also triggers the chip's claimFocus hook.
      html += "<span class=\"form-chip-row\">" +
        "<span class=\"form-claim-chip " + badge.cls + "\" " +
        "data-claim-chip=\"" + esc(claimId) + "\">" + esc(claimId) +
        " <span class=\"form-claim-status\">" + esc(badge.label) +
        "</span>" +
        (badge.tier ? " <span class=\"form-tier-tag\">" +
          esc(badge.tier) + "</span>" : "") +
        "</span>" +
        "<button type=\"button\" class=\"form-chip-x\" " +
        "data-claim-remove=\"" + i + "\" data-node=\"" + nid +
        "\" data-file=\"" + fname + "\" aria-label=\"remove claim " +
        esc(claimId) + ">\u2715</button></span>";
    }
    html += "</div>";
    html += "<div class=\"form-add-row\">" +
      "<input type=\"text\" class=\"form-add-input\" " +
      "data-role=\"add-claim-input\" data-node=\"" + nid +
      "\" data-file=\"" + fname + "\" placeholder=\"add claim_id&hellip;\">" +
      "<button type=\"button\" class=\"form-add-btn\" " +
      "data-role=\"add-claim-btn\" data-node=\"" + nid +
      "\" data-file=\"" + fname + "\">+ Add</button></div>";
    html += placeholderNote(node);
    html += renderIssues(errors, "claims");
    return html;
  }

  // Quick-add candidates: the literal vocabulary + the concrete
  // edit:enzyme:<bucket> ids from the loaded edits.json (if present).
  function quickAddCandidates(node) {
    var current = (node && Object.prototype.toString.call(node.tags) ===
                   "[object Array]") ? node.tags : [];
    var have = {};
    for (var i = 0; i < current.length; i++) have[current[i]] = true;
    var out = [];
    function offer(tag) {
      if (have[tag] || tag === "edit:enzyme:<id>") return;
      for (var j = 0; j < out.length; j++) {
        if (out[j] === tag) return;
      }
      out.push(tag);
    }
    for (var v = 0; v < TAG_VOCAB.length; v++) {
      if (TAG_VOCAB[v].tag === "edit:enzyme:<id>") {
        // Parameterized: offer the concrete edits.json bucket ids.
        var b = EDITOR.state.bundle;
        var enzymes = (b && b.edits && b.edits.enzymes) ? b.edits.enzymes : {};
        for (var key in enzymes) {
          if (Object.prototype.hasOwnProperty.call(enzymes, key)) {
            offer("edit:enzyme:" + key);
          }
        }
        continue;
      }
      offer(TAG_VOCAB[v].tag);
    }
    return out;
  }

  function renderTags(node, errors) {
    var nid = esc(node.id);
    var fname = esc(selectedFile() || "");
    var tags = (node && Object.prototype.toString.call(node.tags) ===
                "[object Array]") ? node.tags : [];
    var html = "";
    html += "<h4>Tags</h4>";
    if (!tags.length) {
      html += "<div class=\"form-none\">no tags on this node</div>";
    }
    html += "<div class=\"form-chip-list\">";
    for (var i = 0; i < tags.length; i++) {
      html += "<span class=\"form-chip-row\">" +
        "<span class=\"form-tag-chip\">" + esc(String(tags[i])) +
        "</span>" +
        "<button type=\"button\" class=\"form-chip-x\" " +
        "data-tag-remove=\"" + i + "\" data-node=\"" + nid +
        "\" data-file=\"" + fname + "\" aria-label=\"remove tag " +
        esc(String(tags[i])) + ">\u2715</button></span>";
    }
    html += "</div>";
    html += "<div class=\"form-add-row\">" +
      "<input type=\"text\" class=\"form-add-input\" " +
      "data-role=\"add-tag-input\" data-node=\"" + nid +
      "\" data-file=\"" + fname + "\" placeholder=\"add tag&hellip;\">" +
      "<button type=\"button\" class=\"form-add-btn\" " +
      "data-role=\"add-tag-btn\" data-node=\"" + nid +
      "\" data-file=\"" + fname + "\">+ Add</button></div>";
    var candidates = quickAddCandidates(node);
    if (candidates.length) {
      html += "<div class=\"form-quickadd-label\">quick-add (known " +
        "vocabulary):</div><div class=\"form-quickadd\">";
      for (var c = 0; c < candidates.length; c++) {
        html += "<button type=\"button\" class=\"form-quickadd-chip\" " +
          "data-tag-quick=\"" + esc(candidates[c]) + "\" data-node=\"" +
          nid + "\" data-file=\"" + fname + "\">+" +
          esc(candidates[c]) + "</button>";
      }
      html += "</div>";
    }
    html += "<details class=\"form-vocab\"><summary>Known tag vocabulary " +
      "(07.1-RESEARCH-DATA \u00a71.5, counts documented)</summary><ul>";
    for (var t = 0; t < TAG_VOCAB.length; t++) {
      html += "<li><b>" + esc(TAG_VOCAB[t].tag) + "</b> \u2014 " +
        esc(TAG_VOCAB[t].count) + "</li>";
    }
    html += "</ul></details>";
    html += renderIssues(errors, "tags");
    return html;
  }

  function renderEnding(node, errors) {
    var nid = esc(node.id);
    var fname = esc(selectedFile() || "");
    var tier = EDITOR.endingTier(node);
    var html = "";
    html += "<h4>Ending type (is_ending)</h4>";
    html += "<select class=\"form-select\" data-role=\"ending-select\" " +
      "data-node=\"" + nid + "\" data-file=\"" + fname + "\">";
    html += "<option value=\"\"" + (tier ? "" : " selected") +
      ">(none \u2014 not an ending)</option>";
    for (var i = 0; i < ENDING_TIERS.length; i++) {
      var t = ENDING_TIERS[i];
      html += "<option value=\"" + t + "\"" +
        (tier === t ? " selected" : "") + ">" + t + "</option>";
    }
    html += "</select>";
    // The ending-convention reminder: what a data change to an ending
    // actually requires (07.1-RESEARCH-DATA §1.7 type-transition recipes);
    // the validator surfaces the REAL errors — this is guidance, not a gate.
    html += "<div class=\"form-note form-note-info\">Ending convention: " +
      "an ending wants the matching <b>ending:" + esc(tier || "&lt;tier&gt;") +
      "</b> + <b>stage:*</b> tags, <b>empty choices</b>, and reachability " +
      "via some choice.goto \u2014 the validator surfaces the real errors " +
      "(unreachable_ending, pool_node_not_ending, &hellip;).</div>";
    // Special-shape touched note (router-only / restored / stub).
    if (lastTouch && lastTouch.id === node.id) {
      html += "<div class=\"form-note form-note-warn\">\u26a0 Special " +
        "shape touched: " + esc(lastTouch.facts) + ". This node's shape " +
        "is pinned by structural conventions \u2014 run the Python gates " +
        "after saving.</div>";
    }
    html += renderIssues(errors, "ending");
    return html;
  }

  // B11 unknown-key guard: read-only rendering of any key outside the
  // known schema. NEVER editable, NEVER removed here — unknown keys must
  // survive every edit untouched (round-trip contract).
  function extraKeys(node) {
    var out = [];
    for (var k in node) {
      if (Object.prototype.hasOwnProperty.call(node, k) &&
          !KNOWN_NODE_KEYS[k]) {
        out.push(k);
      }
    }
    return out;
  }

  function renderExtraKeys(node) {
    var keys = extraKeys(node);
    var html = "";
    html += "<h4>Extra keys (B11 guard)</h4>";
    if (!keys.length) {
      html += "<div class=\"form-none form-extrakeys-none\">none \u2014 " +
        "node is schema-exact (6 keys + optional is_ending)</div>";
      return html;
    }
    html += "<div class=\"form-extrakeys\">";
    for (var i = 0; i < keys.length; i++) {
      var value = "";
      try { value = JSON.stringify(node[keys[i]]); } catch (e) {
        value = String(node[keys[i]]);
      }
      if (value && value.length > 120) value = value.slice(0, 117) + "...";
      html += "<div class=\"form-extrakey\">\u26a0 unknown key <b>" +
        esc(String(keys[i])) + "</b>: <code>" + esc(value) + "</code> " +
        "\u2014 preserved on round-trip; read-only here, never removed " +
        "(B11 extensibility).</div>";
    }
    html += "</div>";
    return html;
  }

  // Transient inline note (set by declined no-op mutations like duplicate
  // adds; lives in the DOM until the next re-render — no mutation, so no
  // re-render happens and the note stays visible).
  function showNote(text) {
    if (!refs.identity) return;
    var el = document.getElementById("form-transient-note");
    if (!el) {
      el = document.createElement("div");
      el.id = "form-transient-note";
      el.className = "form-note form-note-info";
      refs.identity.insertBefore(el, refs.identity.firstChild);
    }
    el.textContent = text;
  }

  // -------------------------------------------------------------------------
  // The form renderer — registered via EDITOR.setFormRenderer (the core's
  // dedicated node-form slot). Runs on every EDITOR.select (selection-driven
  // editing) and after every afterChange (mutation fan-out).
  // -------------------------------------------------------------------------

  function renderForm() {
    var form = refs.form;
    var identity = refs.identity;
    if (!form || !identity) return;
    var node = selectedNode();
    var fname = selectedFile();
    if (!EDITOR.state.bundle || !node || !fname) {
      form.hidden = true; // nothing selected — the panel stays out of the way
      return;
    }
    if (lastTouch && lastTouch.id !== node.id) lastTouch = null;
    form.hidden = false;
    var errors = nodeIssues(node.id);
    var html = renderIdentityHeader(node, fname) +
      "<div class=\"form-section\">" +
      renderTexts(node, errors) + "</div>" +
      "<div class=\"form-section\">" + renderClaims(node, errors) + "</div>" +
      "<div class=\"form-section\">" + renderTags(node, errors) + "</div>" +
      "<div class=\"form-section\">" + renderEnding(node, errors) + "</div>" +
      "<div class=\"form-section\">" + renderExtraKeys(node) + "</div>" +
      "<div class=\"form-section\">" + otherIssues(errors) + "</div>";
    identity.innerHTML = html;
  }

  // -------------------------------------------------------------------------
  // Event wiring — ONE delegated listener per concern on the STABLE
  // #node-form aside (survives innerHTML replacement of the identity
  // sub-section). The textareas' change/input events are handled EXCLUSIVELY
  // by EDITOR.textFieldBindings (commit on change = one undo step; input =
  // live preview only, never a bundle write).
  // -------------------------------------------------------------------------

  function currentIds(el) {
    var nid = el.getAttribute("data-node") || EDITOR.state.sel;
    return { nid: nid, fname: EDITOR.fileOfNode(nid) };
  }

  function wireForm() {
    var form = refs.form;
    if (!form) return;

    // Commit-on-change for the schema text fields (core binding).
    EDITOR.textFieldBindings(form);

    // Chip + button clicks (delegated once).
    EDITOR.delegate(form, "click", "data-claim-chip", function (el) {
      EDITOR.ui.claimFocus(el.getAttribute("data-claim-chip"));
    });
    EDITOR.delegate(form, "click", "data-claim-remove", function (el) {
      var ids = currentIds(el);
      if (ids.fname) {
        removeClaim(ids.fname, ids.nid, parseInt(el.getAttribute("data-claim-remove"), 10));
      }
    });
    EDITOR.delegate(form, "click", "data-tag-remove", function (el) {
      var ids = currentIds(el);
      if (ids.fname) {
        removeTag(ids.fname, ids.nid, parseInt(el.getAttribute("data-tag-remove"), 10));
      }
    });
    EDITOR.delegate(form, "click", "data-tag-quick", function (el) {
      var ids = currentIds(el);
      if (ids.fname) addTag(ids.fname, ids.nid, el.getAttribute("data-tag-quick"));
    });
    EDITOR.delegate(form, "click", "data-role", function (el) {
      var role = el.getAttribute("data-role");
      var ids = currentIds(el);
      if (!ids.fname) return;
      if (role === "add-claim-btn") {
        var input = form.querySelector("input[data-role=\"add-claim-input\"]");
        if (input) {
          addClaim(ids.fname, ids.nid, input.value);
          input.value = "";
        }
      } else if (role === "add-tag-btn") {
        var tagInput = form.querySelector("input[data-role=\"add-tag-input\"]");
        if (tagInput) {
          addTag(ids.fname, ids.nid, tagInput.value);
          tagInput.value = "";
        }
      }
    });

    // Enter in an add-input commits the add (keydown delegation).
    form.addEventListener("keydown", function (ev) {
      var el = ev.target;
      if (!el || !el.getAttribute) return;
      var role = el.getAttribute("data-role");
      if (role !== "add-claim-input" && role !== "add-tag-input") return;
      if (ev.keyCode !== 13 && ev.key !== "Enter") return;
      ev.preventDefault();
      var ids = currentIds(el);
      if (!ids.fname) return;
      if (role === "add-claim-input") {
        addClaim(ids.fname, ids.nid, el.value);
        el.value = "";
      } else {
        addTag(ids.fname, ids.nid, el.value);
        el.value = "";
      }
    });

    // The is_ending select (change delegation; NOT a data-field element, so
    // the core's text-binding change listener ignores it).
    form.addEventListener("change", function (ev) {
      var el = ev.target;
      if (!el || !el.getAttribute) return;
      if (el.getAttribute("data-role") !== "ending-select") return;
      var ids = currentIds(el);
      if (ids.fname) applyEnding(ids.fname, ids.nid, el.value);
    });

    // Live character counts (input events — never a bundle write; the undo
    // pre-image stays the true pre-edit value per the 00_core contract).
    EDITOR.livePreview(function (info) {
      if (info.field !== "text_dramatic" && info.field !== "text_teaching") {
        return;
      }
      var span = refs.identity
        ? refs.identity.querySelector("span[data-charcount=\"" +
            info.field + "\"]")
        : null;
      if (span) span.textContent = String(info.value.length) + " chars";
    });
  }

  // -------------------------------------------------------------------------
  // Asset CSS (injected at runtime per the pipeline's per-feature CSS rule).
  // -------------------------------------------------------------------------

  EDITOR.injectCss(
    "/* injected by 40_form.js (07.1-09): node form styles */\n" +
    "#node-form-identity .form-b9-banner { margin: 4px 0 8px; padding: 7px 9px; border: 1px solid #b8860b; border-left: 4px solid #b8860b; border-radius: 4px; background: #fdf6e3; color: #6b5308; font-size: 12.5px; }\n" +
    "#node-form-identity .form-id-line { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin: 4px 0 2px; }\n" +
    "#node-form-identity .form-id-name { font-family: Consolas, monospace; font-size: 19px; font-weight: bold; color: #1a1a1a; word-break: break-all; }\n" +
    "#node-form-identity .form-kind-chip { font-size: 10.5px; padding: 1px 7px; border-radius: 8px; border: 1px solid #999999; background: #eef1f5; color: #444444; }\n" +
    "#node-form-identity .form-tier-chip { font-size: 10.5px; padding: 1px 7px; border-radius: 8px; border: 1px solid #b8860b; background: #fdf3d7; color: #6b5308; }\n" +
    "#node-form-identity .form-id-file { font-size: 11.5px; color: #777777; margin: 2px 0 8px; }\n" +
    "#node-form-identity .form-section { padding: 2px 0 4px; }\n" +
    "#node-form-identity h4 { margin: 8px 0 4px; font-size: 12.5px; color: #333333; }\n" +
    "#node-form-identity .form-char-count { font-weight: normal; font-size: 11px; color: #888888; margin-left: 6px; }\n" +
    "#node-form-identity .form-textarea { min-height: 84px; font-size: 12px; }\n" +
    "#node-form-identity .form-chip-list { display: flex; flex-wrap: wrap; gap: 5px; margin: 4px 0; }\n" +
    "#node-form-identity .form-chip-row { display: inline-flex; align-items: center; gap: 3px; }\n" +
    "#node-form-identity .form-claim-chip { display: inline-block; padding: 2px 7px; border-radius: 9px; border: 1px solid #aab3c0; background: #f2f4f8; font-family: Consolas, monospace; font-size: 11.5px; cursor: pointer; }\n" +
    "#node-form-identity .form-claim-chip:hover { text-decoration: underline; }\n" +
    "#node-form-identity .form-claim-status { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10px; padding: 0 5px; border-radius: 7px; border: 1px solid transparent; }\n" +
    "#node-form-identity .claim-badge-approved .form-claim-status { background: #dff2df; border-color: #2e8b57; color: #1d5c38; }\n" +
    "#node-form-identity .claim-badge-pending .form-claim-status { background: #fdf3d7; border-color: #b8860b; color: #6b5308; }\n" +
    "#node-form-identity .claim-badge-rejected .form-claim-status { background: #fbe0dc; border-color: #b22222; color: #7a1616; }\n" +
    "#node-form-identity .claim-badge-missing .form-claim-status { background: #fbe0dc; border-color: #b22222; color: #7a1616; }\n" +
    "#node-form-identity .form-tier-tag { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10px; color: #555555; border: 1px dotted #999999; border-radius: 7px; padding: 0 5px; }\n" +
    "#node-form-identity .form-tag-chip { display: inline-block; padding: 2px 7px; border-radius: 9px; border: 1px solid #8ea3c0; background: #e9eef7; font-family: Consolas, monospace; font-size: 11.5px; color: #2b3a55; }\n" +
    "#node-form-identity .form-chip-x { border: 1px solid #c26a5a; background: #fdf0ed; color: #8c2f1f; border-radius: 50%; width: 17px; height: 17px; line-height: 1; font-size: 10px; cursor: pointer; padding: 0; }\n" +
    "#node-form-identity .form-chip-x:hover { background: #f6d9d2; }\n" +
    "#node-form-identity .form-add-row { display: flex; gap: 5px; margin: 6px 0 2px; }\n" +
    "#node-form-identity .form-add-input { flex: 1 1 auto; min-width: 0; font-family: Consolas, monospace; font-size: 11.5px; padding: 3px 6px; border: 1px solid #aab3c0; border-radius: 4px; }\n" +
    "#node-form-identity .form-add-btn { flex: none; font-size: 11.5px; padding: 3px 9px; border: 1px solid #6d7f9b; background: #e9eef7; border-radius: 4px; cursor: pointer; }\n" +
    "#node-form-identity .form-add-btn:hover { background: #dbe4f2; }\n" +
    "#node-form-identity .form-quickadd-label { font-size: 11px; color: #777777; margin-top: 7px; }\n" +
    "#node-form-identity .form-quickadd { display: flex; flex-wrap: wrap; gap: 4px; margin: 3px 0; }\n" +
    "#node-form-identity .form-quickadd-chip { font-family: Consolas, monospace; font-size: 10px; padding: 1px 6px; border: 1px dashed #8ea3c0; background: #f7f9fc; color: #2b3a55; border-radius: 8px; cursor: pointer; }\n" +
    "#node-form-identity .form-quickadd-chip:hover { background: #e9eef7; }\n" +
    "#node-form-identity .form-vocab { font-size: 11px; color: #555555; margin: 6px 0; }\n" +
    "#node-form-identity .form-vocab summary { cursor: pointer; color: #666666; }\n" +
    "#node-form-identity .form-vocab ul { margin: 5px 0; padding-left: 17px; }\n" +
    "#node-form-identity .form-vocab li { margin: 2px 0; }\n" +
    "#node-form-identity .form-select { font-family: Consolas, monospace; font-size: 12px; padding: 3px 5px; border: 1px solid #aab3c0; border-radius: 4px; background: #ffffff; }\n" +
    "#node-form-identity .form-note { margin: 6px 0; padding: 6px 8px; border-radius: 4px; font-size: 11.5px; }\n" +
    "#node-form-identity .form-note-info { border: 1px solid #9db4cc; border-left: 4px solid #4682b4; background: #eef4fb; color: #2b4a68; }\n" +
    "#node-form-identity .form-note-ok { border: 1px solid #7aa87a; border-left: 4px solid #2e8b57; background: #eef7ee; color: #1d5c38; }\n" +
    "#node-form-identity .form-note-warn { border: 1px solid #d9a544; border-left: 4px solid #b8860b; background: #fdf6e3; color: #6b4508; }\n" +
    "#node-form-identity .form-issue { margin: 4px 0; padding: 4px 8px; border-left: 4px solid #b22222; background: #fdeeea; color: #7a1616; font-size: 11.5px; border-radius: 0 4px 4px 0; }\n" +
    "#node-form-identity .form-none { font-size: 11.5px; color: #888888; font-style: italic; margin: 3px 0; }\n" +
    "#node-form-identity .form-extrakeys { margin: 4px 0; }\n" +
    "#node-form-identity .form-extrakey { margin: 4px 0; padding: 4px 8px; border: 1px dashed #d9a544; background: #fdf9ee; color: #6b4508; font-size: 11px; border-radius: 4px; }\n" +
    "#node-form-identity .form-extrakey code { font-size: 10.5px; word-break: break-all; }\n"
  );

  // -------------------------------------------------------------------------
  // Init: locate the mounts, wire the events, first render. Runs once from
  // the shell bootstrap (EDITOR.runInits).
  // -------------------------------------------------------------------------

  function initForm() {
    refs.form = document.getElementById("node-form");
    refs.identity = document.getElementById("node-form-identity");
    if (!refs.form || !refs.identity) {
      warn("EDITOR form (40_form.js): #node-form / #node-form-identity " +
           "mounts missing — form disabled.");
      return;
    }
    wireForm();
    renderForm();
  }

  // Registration per the 07.1-04 convention: the renderer goes into the
  // dedicated form slot (re-renders on EDITOR.select + after every
  // afterChange via the core's rerender dispatcher); the DOM work runs from
  // the shell bootstrap.
  EDITOR.setFormRenderer(renderForm);
  EDITOR.init(initForm);

})();
