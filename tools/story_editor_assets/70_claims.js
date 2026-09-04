/* ==========================================================================
 * 70_claims.js — the claims/references browser, Requirement C (07.1-12).
 *
 * OWNS: the #tab-claims panel (the shell's fixed mount — the whole panel
 * is this asset's territory). Loads after 00_core.js (EDITOR contract),
 * 05_json.js, 10_load.js (bundle), 20_validate.js, 30_graph.js. Registers
 * via EDITOR.view('claims', renderClaims) + EDITOR.init(initClaims) per
 * the 07.1-04 registration convention (the single-quoted view name is the
 * plan's pinned verify string).
 *
 * READ-ONLY CONTRACT (load-bearing): this panel is read-and-jump, never
 * edit. Approvals are HUMAN-GATED by policy — spec.md non-negotiable
 * ("No fabricated science ... explicitly approved by the human") — so this
 * asset performs NO bundle mutation of any kind (the state layer's
 * mutation API is never invoked here) and citations.json / sources.json
 * are never written. src: 07.1-RESEARCH-UI "Reference/source checking (C)":
 * "The editor must NOT write citations.json/sources.json ... C is
 * read-and-jump, not edit."
 *
 * DATA (07.1-RESEARCH-DATA §1.10 registry schemas + §1.11 panel spec):
 *   bundle.citations — FLAT dict claim_id → record: claim (short),
 *     claim_text (full approved wording), source_type, source (human
 *     string), source_id (STR OR LIST-OF-STR — 40/77 claims are
 *     multi-source), review_tier (routine | high-stakes),
 *     inherits_source_approval, approval_status (approved | pending |
 *     rejected), optional approved_by / approved_date / review_notes /
 *     pdb_id / resolution_angstrom.
 *   bundle.sources — FLAT dict source_id → record: reference, url?,
 *     pdb_doi?, license?, source_type, approval_status, approved_by?,
 *     approved_date?, notes?.
 *   The citation gate NEVER reads sources.json — provenance context only.
 *   Either registry may be null when the load layer (10_load.js) degraded;
 *   every access path below handles that (warning panel -> boot checklist).
 *
 * STRICT APPROVAL SEMANTICS (display mirrors the gate): a claim counts as
 * approved iff approval_status === "approved" EXACTLY — a "rejected"
 * claim fails identically to a "pending" one. There is deliberately NO
 * "not pending" shortcut anywhere below.
 * src: rpg/citations.py:100-109 (is_approved — the gate's core predicate,
 * including the Pitfall-6 note about the erroneous "!= pending" form).
 *
 * SANCTIONED RESIDUAL: PLACEHOLDER_PHASE8 on exactly fa.stub / alc.stub is
 * the citation gate's sanctioned residual — a NOTICE, never an error —
 * rendered here as an annotated info case, not an alarm. The same id
 * anywhere else (or any other PLACEHOLDER* id) is placeholder_misuse —
 * an alarm. src: tools/story_editor_lint.py rule_claims;
 * tests/test_glucose_content.py:213-236.
 *
 * REVERSE INDEX: claim_id → [node ids], built by walking every node's
 * claim_ids list (≤ 3 ids each, 57 nodes — trivial; §1.10 cross-links:
 * 70/77 claims referenced, 8 free pool). Shown in the claim detail and as
 * per-node warning chips for unapproved / unresolved references (display
 * mirror of the lint's claim rules; clicking a chip opens the claim).
 *
 * HOOK CONSUMED: EDITOR.ui.claimFocus(claimId) — the node form (40_form.js,
 * 07.1-09) calls it when a claim chip is clicked. Defined here (defensively
 * creating the EDITOR.ui namespace if an earlier asset has not): switches
 * to the claims tab + opens the claim.
 *
 * STYLE: one classic script, one IIFE, ES5 only (var, no arrow functions,
 * no modules) — the emitted-page discipline pinned page-wide by
 * tests/test_story_editor_state.py.
 * ========================================================================== */

(function () {
  "use strict";

  // -------------------------------------------------------------------------
  // Constants — the sanctioned-residual pair (mirror of the lint).
  // -------------------------------------------------------------------------

  var PHASE8_CLAIM = "PLACEHOLDER_PHASE8";
  var PHASE8_STUB_NODES = { "fa.stub": true, "alc.stub": true };

  // -------------------------------------------------------------------------
  // Module state: DOM refs + view state. The toolbar/table/detail DOM is
  // built ONCE in initClaims; re-renders only refresh the dynamic parts so
  // the filter inputs never lose focus or value while typing.
  // -------------------------------------------------------------------------

  var refs = {
    panel: null, built: false,
    toolbar: null, search: null, statusSel: null, tierSel: null,
    refSel: null, resetBtn: null, count: null,
    tableWrap: null, tbody: null,
    detail: null, warnings: null, empty: null
  };

  var selectedClaim = null;                       // claim_id or null
  var filter = { status: "all", tier: "all", ref: "all", text: "" };
  var lastIndex = { byClaim: {} };                // rebuilt on every data render

  // -------------------------------------------------------------------------
  // Small DOM helpers (ES5; every dynamic string passes through
  // textContent — never innerHTML with data).
  // -------------------------------------------------------------------------

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = String(text);
    return n;
  }

  function clearEl(n) {
    if (!n) return;
    while (n.firstChild) n.removeChild(n.firstChild);
  }

  function hasOwn(obj, key) {
    return Object.prototype.hasOwnProperty.call(obj, key);
  }

  // -------------------------------------------------------------------------
  // Data access — pure reads of EDITOR.state.bundle (see the READ-ONLY
  // CONTRACT in the header; nothing below writes to the bundle).
  // -------------------------------------------------------------------------

  function theBundle() {
    return EDITOR.state.bundle;
  }

  function citationsMap() {
    var b = theBundle();
    return (b && b.citations && typeof b.citations === "object")
      ? b.citations : null;
  }

  function sourcesMap() {
    var b = theBundle();
    return (b && b.sources && typeof b.sources === "object")
      ? b.sources : null;
  }

  function claimRecord(cid) {
    var cits = citationsMap();
    if (!cits || typeof cid !== "string" || !hasOwn(cits, cid)) return null;
    var rec = cits[cid];
    return (rec && typeof rec === "object") ? rec : null;
  }

  // STRICT gate predicate (display mirror of the citation gate): approved
  // iff approval_status === "approved" EXACTLY — rejected fails identically
  // to pending. src: rpg/citations.py:100-109 (is_approved).
  function isApproved(rec) {
    return !!(rec && rec.approval_status === "approved");
  }

  function statusOf(rec) {
    if (!rec || !rec.approval_status) return "missing";
    return String(rec.approval_status);
  }

  // source_id is a STRING or a LIST-OF-STRINGS (40/77 claims are
  // multi-source — §1.10). Normalized to an array here, once, so every
  // consumer below can iterate the same way; junk tolerated as [].
  function sourceIds(rec) {
    if (!rec) return [];
    var sid = rec.source_id;
    if (Object.prototype.toString.call(sid) === "[object Array]") {
      return sid.slice(); // LIST branch
    }
    if (typeof sid === "string" && sid) {
      return [sid];       // STRING branch
    }
    return [];
  }

  // Only http(s) URLs become anchors: a tampered sources.json must never be
  // able to inject a javascript: href into the panel. Navigation is
  // display-only — a file:// page may open an https target in a new tab;
  // that is a browser navigation, never a resource load into this page
  // (07.1-RESEARCH-UI, Requirement C "offline-safe" wording).
  function safeHttpUrl(u) {
    if (typeof u !== "string") return null;
    return /^https?:\/\//i.test(u) ? u : null;
  }

  // -------------------------------------------------------------------------
  // Claim-issue classification — a DISPLAY mirror of the lint's claim rules
  // (tools/story_editor_lint.py rule_claims): claim_missing /
  // claim_unapproved / placeholder_misuse, plus the sanctioned residual.
  // Purely informational here (the authoritative verdict is the Python
  // lint; 20_validate.js re-runs it in-browser — this panel only annotates).
  // -------------------------------------------------------------------------

  // Returns null for a clean reference, else
  //   { kind: "claim_missing" | "claim_unapproved" | "placeholder_misuse" |
  //           "sanctioned_residual",
  //     note: human string, sanctioned: bool }
  function claimIssue(cid, nodeId) {
    if (typeof cid !== "string") {
      return {
        kind: "claim_missing",
        note: "non-string claim_id (claim_ids must be strings)",
        sanctioned: false
      };
    }
    if (cid === PHASE8_CLAIM) {
      if (nodeId && PHASE8_STUB_NODES[nodeId]) {
        // The sanctioned residual: PLACEHOLDER_PHASE8 on exactly the
        // Phase-8 stub pair — a notice, never an error (annotated info
        // case below, deliberately NOT styled as an alarm).
        return {
          kind: "sanctioned_residual",
          note: "sanctioned residual \u2014 Phase-8 stub pair " +
                "(fa.stub / alc.stub); the citation gate reports this as " +
                "a notice, never an error",
          sanctioned: true
        };
      }
      return {
        kind: "placeholder_misuse",
        note: PHASE8_CLAIM + " is sanctioned ONLY on fa.stub/alc.stub \u2014 " +
              "a new node may never use it",
        sanctioned: false
      };
    }
    if (cid.indexOf("PLACEHOLDER") === 0) {
      return {
        kind: "placeholder_misuse",
        note: "no PLACEHOLDER* residue is allowed anywhere except " +
              PHASE8_CLAIM + " on the sanctioned stubs",
        sanctioned: false
      };
    }
    var rec = claimRecord(cid);
    if (!rec) {
      return {
        kind: "claim_missing",
        note: "references claim_id not in the registry",
        sanctioned: false
      };
    }
    if (!isApproved(rec)) {
      // Strict comparison above; pending and rejected both land here.
      return {
        kind: "claim_unapproved",
        note: "approval_status is " + JSON.stringify(rec.approval_status || null) +
              ", not 'approved'",
        sanctioned: false
      };
    }
    return null;
  }

  // -------------------------------------------------------------------------
  // Reverse index: claim_id → [node ids]. Walks every node's claim_ids
  // (≤ 3 ids each, 57 nodes — trivial per §1.10). Rebuilt on every data
  // render: claim_ids is editable in the node form (07.1-09), so a stale
  // index would lie after every edit.
  // -------------------------------------------------------------------------

  function buildReverseIndex() {
    var byClaim = {};
    var nodes = (typeof EDITOR.allNodes === "function") ? EDITOR.allNodes() : [];
    for (var i = 0; i < nodes.length; i++) {
      var wrap = nodes[i];
      var node = wrap.node;
      var ids = (node && Object.prototype.toString.call(node.claim_ids) ===
                 "[object Array]") ? node.claim_ids : [];
      for (var j = 0; j < ids.length; j++) {
        var cid = ids[j];
        if (typeof cid !== "string") continue; // surfaced by renderWarnings
        if (!hasOwn(byClaim, cid)) byClaim[cid] = [];
        byClaim[cid].push(wrap.id);
      }
    }
    lastIndex.byClaim = byClaim;
    return lastIndex;
  }

  function referencingNodes(cid) {
    return hasOwn(lastIndex.byClaim, cid) ? lastIndex.byClaim[cid] : [];
  }

  // -------------------------------------------------------------------------
  // Chip builders.
  // -------------------------------------------------------------------------

  function statusChip(rec) {
    var st = statusOf(rec);
    var label = (st === "missing") ? "MISSING" : st;
    return el("span", "claims-chip claims-status-" + st, label);
  }

  function tierBadge(rec) {
    var tier = (rec && rec.review_tier) ? String(rec.review_tier) : "\u2014";
    var cls = (tier === "high-stakes")
      ? "claims-tier claims-tier-high"
      : "claims-tier claims-tier-routine";
    return el("span", cls, tier);
  }

  // A referencing-node chip (jump-to-node). warn=true gives the amber
  // warning style (unapproved / unresolved reference).
  function nodeChip(nid, warn) {
    var c = el("button",
      "claims-node-chip" + (warn ? " claims-node-chip-warn" : ""), String(nid));
    c.type = "button";
    c.setAttribute("data-jump-node", String(nid));
    c.title = "Jump to node " + nid + " in the graph";
    return c;
  }

  // -------------------------------------------------------------------------
  // Filtering.
  // -------------------------------------------------------------------------

  function claimMatchesFilters(cid, rec, refCount) {
    if (filter.status !== "all" && statusOf(rec) !== filter.status) {
      return false;
    }
    if (filter.tier !== "all") {
      var tier = (rec && rec.review_tier) ? String(rec.review_tier) : "";
      if (tier !== filter.tier) return false;
    }
    if (filter.ref === "referenced" && refCount === 0) return false;
    if (filter.ref === "unreferenced" && refCount > 0) return false;
    if (filter.text) {
      var hay = (
        cid + "\n" +
        ((rec && rec.claim) ? rec.claim : "") + "\n" +
        ((rec && rec.claim_text) ? rec.claim_text : "")
      ).toLowerCase();
      if (hay.indexOf(filter.text) === -1) return false;
    }
    return true;
  }

  // -------------------------------------------------------------------------
  // Render: count line.
  // -------------------------------------------------------------------------

  function renderCount(cits) {
    var ids = Object.keys(cits);
    var approved = 0, pending = 0, rejected = 0;
    for (var i = 0; i < ids.length; i++) {
      var st = statusOf(cits[ids[i]]);
      if (st === "approved") approved++;
      else if (st === "pending") pending++;
      else if (st === "rejected") rejected++;
    }
    var referenced = 0;
    for (var cid in lastIndex.byClaim) {
      if (hasOwn(lastIndex.byClaim, cid) && hasOwn(cits, cid)) referenced++;
    }
    refs.count.textContent = ids.length + " claims | " + approved +
      " approved | " + pending + " pending | " + rejected + " rejected | " +
      referenced + " referenced by nodes | " + (ids.length - referenced) +
      " unreferenced (free pool)";
  }

  // -------------------------------------------------------------------------
  // Render: claim table (filters applied).
  // -------------------------------------------------------------------------

  function renderTable(cits) {
    clearEl(refs.tbody);
    var ids = Object.keys(cits);
    var shown = 0;
    for (var i = 0; i < ids.length; i++) {
      var cid = ids[i];
      var rec = cits[cid];
      var refList = referencingNodes(cid);
      if (!claimMatchesFilters(cid, rec, refList.length)) continue;
      shown++;

      var tr = el("tr", "claims-row" +
        (cid === selectedClaim ? " claims-row-selected" : ""));
      tr.setAttribute("data-claim-id", cid);

      var tdId = el("td", "claims-cell-id", cid);
      var tdStatus = el("td");
      tdStatus.appendChild(statusChip(rec));
      var tdTier = el("td");
      tdTier.appendChild(tierBadge(rec));
      var tdClaim = el("td", "claims-cell-claim",
        (rec && rec.claim) ? rec.claim : "");
      var tdSources = el("td", "claims-cell-num",
        String(sourceIds(rec).length));
      var tdRefs = el("td", "claims-cell-num", String(refList.length));

      tr.appendChild(tdId);
      tr.appendChild(tdStatus);
      tr.appendChild(tdTier);
      tr.appendChild(tdClaim);
      tr.appendChild(tdSources);
      tr.appendChild(tdRefs);
      refs.tbody.appendChild(tr);
    }
    if (!shown) {
      var tr2 = el("tr", "claims-row-empty");
      var td2 = el("td", null,
        "No claims match the current filters.");
      td2.setAttribute("colspan", "6");
      tr2.appendChild(td2);
      refs.tbody.appendChild(tr2);
    }
  }

  // -------------------------------------------------------------------------
  // Render: claim detail (full record + sources + reverse index).
  // -------------------------------------------------------------------------

  function metaRow(label, valueText) {
    var row = el("div", "claims-source-row");
    row.appendChild(el("span", "claims-source-key", label));
    row.appendChild(document.createTextNode(String(valueText)));
    return row;
  }

  function renderSourceCard(sid, srec) {
    var card = el("div", "claims-source");
    card.appendChild(el("div", "claims-cell-id", String(sid)));
    if (!srec) {
      card.appendChild(el("div", "claims-source-missing",
        "source_id not present in sources.json (dangling source reference)"));
      return card;
    }
    if (srec.reference) card.appendChild(metaRow("reference", srec.reference));
    if (srec.source_type) {
      card.appendChild(metaRow("source_type", srec.source_type));
    }
    var url = safeHttpUrl(srec.url);
    if (url) {
      var row = el("div", "claims-source-row");
      row.appendChild(el("span", "claims-source-key", "url"));
      var a = document.createElement("a");
      a.href = url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = srec.url;
      a.title = "Opens in a new tab (display-only navigation \u2014 " +
                "nothing is loaded into this page)";
      row.appendChild(a);
      card.appendChild(row);
    } else if (srec.url) {
      card.appendChild(metaRow("url", srec.url + " (not linked \u2014 " +
        "only http/https URLs become links)"));
    }
    if (srec.pdb_doi) card.appendChild(metaRow("pdb_doi", srec.pdb_doi));
    if (srec.license) card.appendChild(metaRow("license", srec.license));
    var stRow = el("div", "claims-source-row");
    stRow.appendChild(el("span", "claims-source-key", "approval_status"));
    stRow.appendChild(statusChip(srec));
    if (srec.approved_by) {
      stRow.appendChild(document.createTextNode(
        " by " + srec.approved_by +
        (srec.approved_date ? " on " + srec.approved_date : "")));
    }
    card.appendChild(stRow);
    if (srec.notes) card.appendChild(metaRow("notes", srec.notes));
    return card;
  }

  function renderDetail() {
    clearEl(refs.detail);
    if (!selectedClaim) {
      refs.detail.appendChild(el("p", "claims-detail-placeholder",
        "Click a claim row to inspect its full text, sources and the " +
        "nodes that reference it."));
      return;
    }
    var rec = claimRecord(selectedClaim);
    if (!rec) {
      // A referenced-but-missing claim id (the lint's claim_missing) --
      // degrade to an annotated card instead of crashing.
      var miss = el("div", "claims-source");
      miss.appendChild(el("div", "claims-cell-id", selectedClaim));
      miss.appendChild(el("div", "claims-source-missing",
        "This claim_id is not in the registry (citations.json) \u2014 the " +
        "citation gate reports it as claim_missing on every node that " +
        "references it. See the warnings section below."));
      refs.detail.appendChild(miss);
      renderReverseIndexSection(null);
      return;
    }

    // Header: id + status chip + tier badge.
    var head = el("div", "claims-detail-head");
    head.appendChild(el("span", "claims-cell-id claims-detail-id",
      selectedClaim));
    head.appendChild(statusChip(rec));
    head.appendChild(tierBadge(rec));
    if (rec.approved_by) {
      head.appendChild(el("span", "claims-detail-approved",
        "approved by " + rec.approved_by +
        (rec.approved_date ? " on " + rec.approved_date : "")));
    }
    refs.detail.appendChild(head);

    // Full approved wording (the claim_text is the APPROVED TEXT -- the
    // wording every story reference must stay inside).
    refs.detail.appendChild(el("h4", "claims-section-title",
      "claim_text (approved wording)"));
    var quote = el("div", "claims-claim-text",
      rec.claim_text || "(no claim_text recorded)");
    refs.detail.appendChild(quote);

    // Meta block.
    var meta = el("div", "claims-meta");
    if (rec.claim) meta.appendChild(metaRow("claim (short)", rec.claim));
    if (rec.source_type) {
      meta.appendChild(metaRow("source_type", rec.source_type));
    }
    if (rec.source) meta.appendChild(metaRow("source", rec.source));
    if (rec.review_tier) {
      meta.appendChild(metaRow("review_tier", rec.review_tier));
    }
    if (rec.inherits_source_approval !== undefined) {
      meta.appendChild(metaRow("inherits_source_approval",
        String(rec.inherits_source_approval)));
    }
    if (rec.pdb_id) meta.appendChild(metaRow("pdb_id", rec.pdb_id));
    if (rec.resolution_angstrom !== undefined &&
        rec.resolution_angstrom !== null) {
      meta.appendChild(metaRow("resolution_angstrom",
        String(rec.resolution_angstrom)));
    }
    if (meta.childNodes.length) refs.detail.appendChild(meta);

    // review_notes (approval provenance), when present.
    if (rec.review_notes) {
      refs.detail.appendChild(el("h4", "claims-section-title",
        "review_notes"));
      refs.detail.appendChild(
        el("div", "claims-review-notes", rec.review_notes));
    }

    // Sources -- source_id may be a single string or a list (40/77
    // multi-source); sourceIds() normalized both to an array.
    var sids = sourceIds(rec);
    refs.detail.appendChild(el("h4", "claims-section-title",
      "Sources (" + sids.length + ")"));
    var sm = sourcesMap();
    if (!sm) {
      refs.detail.appendChild(el("div", "claims-source-missing",
        "sources.json did not load \u2014 source records are unavailable " +
        "in this session. Check the boot panel's found/missing checklist " +
        "and re-pick the repository root."));
    } else if (!sids.length) {
      refs.detail.appendChild(el("div", "claims-detail-approved",
        "No source_id recorded on this claim."));
    } else {
      for (var i = 0; i < sids.length; i++) {
        var sid = sids[i];
        var srec = (sm && hasOwn(sm, sid) && sm[sid] &&
                    typeof sm[sid] === "object") ? sm[sid] : null;
        refs.detail.appendChild(renderSourceCard(sid, srec));
      }
    }

    renderReverseIndexSection(rec);
  }

  // The reverse-index block of the detail: every referencing node as a
  // jump chip; the chips go amber when the claim itself is not approved.
  function renderReverseIndexSection(rec) {
    var refList = referencingNodes(selectedClaim);
    refs.detail.appendChild(el("h4", "claims-section-title",
      "Referenced by nodes (" + refList.length + ")"));
    if (!refList.length) {
      refs.detail.appendChild(el("div", "claims-detail-approved",
        "Not referenced by any node \u2014 free pool (available for " +
        "Phase 7-9 authoring)."));
      return;
    }
    var issue = claimIssue(selectedClaim, null);
    var warnChips = !!(issue && !issue.sanctioned);
    var box = el("div", "claims-node-chips");
    for (var i = 0; i < refList.length; i++) {
      box.appendChild(nodeChip(refList[i], warnChips));
    }
    refs.detail.appendChild(box);
    if (warnChips) {
      refs.detail.appendChild(el("div", "claims-warn-note",
        "Amber chips: these nodes reference a claim whose approval_status " +
        "is not 'approved' (strict \u2014 the citation gate flags every " +
        "one of them)."));
    }
  }

  // -------------------------------------------------------------------------
  // Render: per-node warning chips -- the display mirror of the lint's
  // claim rules. One row per (node, claim) reference that is missing /
  // unapproved / placeholder misuse; the sanctioned residual renders as an
  // annotated info case, not an alarm. Clicking a chip opens the claim.
  // -------------------------------------------------------------------------

  function renderWarnings() {
    clearEl(refs.warnings);
    refs.warnings.appendChild(el("h3", "claims-section-title",
      "Per-node claim warnings (display mirror of the lint's claim rules)"));

    var nodes = (typeof EDITOR.allNodes === "function")
      ? EDITOR.allNodes() : [];
    var rows = [];
    var sanctionedSeen = [];
    for (var i = 0; i < nodes.length; i++) {
      var wrap = nodes[i];
      var ids = (wrap.node && Object.prototype.toString.call(wrap.node.claim_ids) ===
                 "[object Array]") ? wrap.node.claim_ids : [];
      for (var j = 0; j < ids.length; j++) {
        var issue = claimIssue(ids[j], wrap.id);
        if (!issue) continue;
        if (issue.sanctioned) {
          if (sanctionedSeen.indexOf(wrap.id) === -1) {
            sanctionedSeen.push(wrap.id);
          }
          continue; // rendered as the annotated info line below
        }
        rows.push({ nid: wrap.id, cid: ids[j], issue: issue });
      }
    }

    // The sanctioned residual as an annotated special case (never an alarm).
    if (sanctionedSeen.length) {
      var info = el("div", "claims-sanctioned-info");
      info.appendChild(el("span", "claims-chip claims-status-pending",
        "sanctioned residual"));
      info.appendChild(document.createTextNode(
        " PLACEHOLDER_PHASE8 on " + sanctionedSeen.join(" + ") +
        " \u2014 expected Phase-8 stub state (the citation gate's pinned " +
        "2-MISSING + 0-UNAPPROVED form; a notice, never an error)."));
      refs.warnings.appendChild(info);
    }

    if (!rows.length) {
      refs.warnings.appendChild(el("div", "claims-allclean",
        sanctionedSeen.length
          ? "No claim issues beyond the sanctioned residual above."
          : "No claim issues: every node reference resolves to an " +
            "approved claim."));
      return;
    }

    for (var r = 0; r < rows.length; r++) {
      var row = rows[r];
      var chip = el("button",
        "claims-node-chip claims-node-chip-warn claims-warn-chip",
        "\u26a0 " + row.nid + " \u2192 " + row.cid);
      chip.type = "button";
      chip.setAttribute("data-open-claim", String(row.cid));
      chip.title = row.issue.kind + " \u2014 " + row.issue.note +
        " (click to open the claim)";
      var line = el("div", "claims-warn-row");
      line.appendChild(chip);
      line.appendChild(el("span", "claims-warn-kind",
        row.issue.kind + " \u2014 " + row.issue.note));
      refs.warnings.appendChild(line);
    }
  }

  // -------------------------------------------------------------------------
  // Degradation / empty state: no bundle, or the registry did not load --
  // a warning panel pointing at the boot checklist (10_load.js fills it),
  // never a silent blank panel.
  // -------------------------------------------------------------------------

  function showEmpty(msg, hint) {
    if (msg === null) {
      if (refs.empty) refs.empty.style.display = "none";
      refs.toolbar.style.display = "flex";
      refs.tableWrap.style.display = "";
      refs.detail.style.display = "";
      refs.warnings.style.display = "";
      return;
    }
    // Rebuilt fresh on every show (content differs per degrade reason);
    // the "Show boot panel" button is recreated with it.
    if (!refs.empty) {
      refs.empty = el("div", "claims-empty");
      refs.panel.appendChild(refs.empty);
    }
    clearEl(refs.empty);
    refs.empty.appendChild(el("p", null, msg));
    refs.empty.appendChild(el("p", null, hint));
    var btn = el("button", null, "Show boot panel");
    btn.type = "button";
    btn.addEventListener("click", function () {
      var boot = document.getElementById("boot-panel");
      if (boot && boot.scrollIntoView) boot.scrollIntoView();
    });
    refs.empty.appendChild(btn);
    refs.empty.style.display = "flex";
    refs.toolbar.style.display = "none";
    refs.tableWrap.style.display = "none";
    refs.detail.style.display = "none";
    refs.warnings.style.display = "none";
  }

  // -------------------------------------------------------------------------
  // Interactions.
  // -------------------------------------------------------------------------

  function openClaim(cid) {
    selectedClaim = (cid == null) ? null : String(cid);
    renderClaims();
    // Bring the row/detail into view (only meaningful when the tab is
    // active; harmless otherwise).
    try {
      var row = refs.tbody.querySelector(
        'tr[data-claim-id="' + selectedClaim + '"]');
      if (row && row.scrollIntoView) row.scrollIntoView();
    } catch (e) { /* querySelector on a odd id is impossible -- ids are
                     plain strings; keep the guard anyway */ }
  }

  // Jump-to-node (Requirement C): select the node + switch to the graph
  // tab, where 30_graph.js renders the selection highlight.
  function jumpToNode(nid) {
    EDITOR.select(nid);
    EDITOR.showTab("graph");
  }

  // -------------------------------------------------------------------------
  // The registered view. Guarded so pre-init calls are no-ops; the
  // re-render refreshes ONLY the dynamic parts (filters keep focus/value).
  // -------------------------------------------------------------------------

  function renderClaims() {
    if (!refs.panel || !refs.built) return; // initClaims has not run yet
    var b = theBundle();
    if (!b || !b.files) {
      showEmpty(
        "No data loaded \u2014 the claims browser reads the loaded bundle.",
        "Load data first: use the boot panel at the top of the page " +
        "(silent probe or folder pick).");
      return;
    }
    var cits = citationsMap();
    if (!cits) {
      showEmpty(
        "citations.json did not load \u2014 the claims browser has no " +
        "registry to show.",
        "Check the boot panel's found/missing checklist at the top of " +
        "the page and re-pick the repository root.");
      return;
    }
    showEmpty(null);
    buildReverseIndex();
    renderCount(cits);
    renderTable(cits);
    renderDetail();
    renderWarnings();
  }

  // -------------------------------------------------------------------------
  // Init: build the static DOM ONCE, wire events, first render.
  // -------------------------------------------------------------------------

  function initClaims() {
    var panel = document.getElementById("tab-claims");
    if (!panel) return; // no claims mount in this shell (never in this repo)
    refs.panel = panel;

    var wrap = el("div", "claims-wrap");

    // Toolbar: text search + status / tier / referenced filters + reset.
    var toolbar = el("div", "claims-toolbar");
    refs.search = el("input");
    refs.search.type = "text";
    refs.search.placeholder =
      "Search claim id / short claim / claim_text\u2026";
    refs.search.setAttribute("data-claims-search", "1");
    toolbar.appendChild(refs.search);

    toolbar.appendChild(el("span", "claims-tool-label", "status"));
    refs.statusSel = el("select");
    var stOpts = ["all", "approved", "pending", "rejected"];
    for (var i = 0; i < stOpts.length; i++) {
      var o1 = el("option", null, stOpts[i]);
      o1.value = stOpts[i];
      refs.statusSel.appendChild(o1);
    }
    toolbar.appendChild(refs.statusSel);

    toolbar.appendChild(el("span", "claims-tool-label", "tier"));
    refs.tierSel = el("select");
    var tierOpts = ["all", "routine", "high-stakes"];
    for (var t = 0; t < tierOpts.length; t++) {
      var o2 = el("option", null, tierOpts[t]);
      o2.value = tierOpts[t];
      refs.tierSel.appendChild(o2);
    }
    toolbar.appendChild(refs.tierSel);

    toolbar.appendChild(el("span", "claims-tool-label", "references"));
    refs.refSel = el("select");
    var refOpts = [
      { v: "all", label: "all" },
      { v: "referenced", label: "referenced only" },
      { v: "unreferenced", label: "unreferenced (free pool)" }
    ];
    for (var r = 0; r < refOpts.length; r++) {
      var o3 = el("option", null, refOpts[r].label);
      o3.value = refOpts[r].v;
      refs.refSel.appendChild(o3);
    }
    toolbar.appendChild(refs.refSel);

    refs.resetBtn = el("button", null, "Reset filters");
    refs.resetBtn.type = "button";
    toolbar.appendChild(refs.resetBtn);

    refs.count = el("span", "claims-count", "");
    toolbar.appendChild(refs.count);
    refs.toolbar = toolbar;
    wrap.appendChild(toolbar);

    // Claim table.
    refs.tableWrap = el("div", "claims-table-wrap");
    var table = el("table");
    table.id = "claims-table";
    var thead = el("thead");
    var hrow = el("tr");
    var heads = ["claim_id", "status", "review_tier", "claim", "sources",
                 "nodes"];
    for (var h = 0; h < heads.length; h++) {
      hrow.appendChild(el("th", null, heads[h]));
    }
    thead.appendChild(hrow);
    table.appendChild(thead);
    refs.tbody = el("tbody");
    table.appendChild(refs.tbody);
    refs.tableWrap.appendChild(table);
    wrap.appendChild(refs.tableWrap);

    // Detail + warnings.
    refs.detail = el("div", "claims-detail");
    wrap.appendChild(refs.detail);
    refs.warnings = el("div", "claims-warnings");
    wrap.appendChild(refs.warnings);

    panel.appendChild(wrap);

    // Filter events: direct listeners (four controls, rebuilt never).
    refs.search.addEventListener("input", function () {
      filter.text = refs.search.value.replace(/^\s+|\s+$/g, "").toLowerCase();
      var cits = citationsMap();
      if (cits) renderTable(cits);
    });
    refs.statusSel.addEventListener("change", function () {
      filter.status = refs.statusSel.value;
      var cits = citationsMap();
      if (cits) renderTable(cits);
    });
    refs.tierSel.addEventListener("change", function () {
      filter.tier = refs.tierSel.value;
      var cits = citationsMap();
      if (cits) renderTable(cits);
    });
    refs.refSel.addEventListener("change", function () {
      filter.ref = refs.refSel.value;
      var cits = citationsMap();
      if (cits) renderTable(cits);
    });
    refs.resetBtn.addEventListener("click", function () {
      filter.status = "all";
      filter.tier = "all";
      filter.ref = "all";
      filter.text = "";
      refs.statusSel.value = "all";
      refs.tierSel.value = "all";
      refs.refSel.value = "all";
      refs.search.value = "";
      var cits = citationsMap();
      if (cits) renderTable(cits);
    });

    // Row click -> open the claim (ONE delegated listener per container,
    // RESEARCH-UI structural choice 2).
    EDITOR.delegate(refs.tableWrap, "click", "data-claim-id",
      function (target) {
        openClaim(target.getAttribute("data-claim-id"));
      });
    // Node chip -> jump to the node in the graph (delegated on the panel:
    // chips live in both the detail and the warnings sections).
    EDITOR.delegate(panel, "click", "data-jump-node", function (target) {
      jumpToNode(target.getAttribute("data-jump-node"));
    });
    // Warning chip -> open the claim it flags.
    EDITOR.delegate(panel, "click", "data-open-claim", function (target) {
      openClaim(target.getAttribute("data-open-claim"));
    });

    refs.built = true;
    renderClaims();
  }

  // -------------------------------------------------------------------------
  // EDITOR.ui.claimFocus -- the hook the node form (40_form.js, 07.1-09)
  // calls when a claim chip is clicked. Defined HERE (the claims panel owns
  // claim focus); the EDITOR.ui namespace is created defensively if no
  // earlier asset made one. Switches to the claims tab + opens the claim.
  // -------------------------------------------------------------------------

  EDITOR.ui = EDITOR.ui || {};
  EDITOR.ui.claimFocus = function (claimId) {
    openClaim(claimId);
    EDITOR.showTab("claims");
  };

  // -------------------------------------------------------------------------
  // Registration (07.1-04 convention). The single-quoted view name is the
  // plan's pinned verify string (emitted HTML must contain
  // "EDITOR.view('claims'").
  // -------------------------------------------------------------------------

  EDITOR.view('claims', renderClaims);
  EDITOR.init(initClaims);

  // -------------------------------------------------------------------------
  // Asset CSS (per-feature CSS injected at runtime per the pipeline rule).
  // -------------------------------------------------------------------------

  EDITOR.injectCss(
    "/* injected by 70_claims.js (07.1-12): claims browser styles */\n" +
    "#tab-claims { padding: 10px 14px 24px; }\n" +
    ".claims-wrap { display: flex; flex-direction: column; gap: 10px; }\n" +
    ".claims-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 6px 8px; background: #f5f6f8; border: 1px solid #dde3ec; border-radius: 6px; font-size: 12.5px; }\n" +
    ".claims-toolbar input[type=\"text\"] { flex: 1 1 220px; min-width: 160px; padding: 4px 6px; border: 1px solid #b9c2d0; border-radius: 4px; font-size: 12.5px; }\n" +
    ".claims-toolbar select { padding: 3px 4px; border: 1px solid #b9c2d0; border-radius: 4px; background: #ffffff; font-size: 12.5px; }\n" +
    ".claims-toolbar button { padding: 3px 10px; border: 1px solid #9aa3b2; border-radius: 4px; background: #e8ecf3; cursor: pointer; font-size: 12px; }\n" +
    ".claims-tool-label { color: #555555; font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.05em; }\n" +
    ".claims-count { flex: 1 1 100%; color: #666666; font-family: Consolas, monospace; font-size: 11.5px; }\n" +
    ".claims-table-wrap { overflow-x: auto; }\n" +
    "#claims-table { width: 100%; border-collapse: collapse; font-size: 12.5px; background: #ffffff; }\n" +
    "#claims-table th, #claims-table td { border: 1px solid #dde3ec; padding: 4px 8px; text-align: left; vertical-align: top; }\n" +
    "#claims-table thead th { background: #eef1f6; position: sticky; top: 0; z-index: 1; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #555555; }\n" +
    ".claims-row { cursor: pointer; }\n" +
    ".claims-row:hover { background: #f2f6fc; }\n" +
    ".claims-row-selected, .claims-row-selected:hover { background: #e3edfb; outline: 2px solid #1f6feb; outline-offset: -2px; }\n" +
    ".claims-row-empty td { color: #777777; font-style: italic; }\n" +
    ".claims-cell-id { font-family: Consolas, monospace; font-size: 12px; white-space: nowrap; }\n" +
    ".claims-cell-claim { color: #333333; }\n" +
    ".claims-cell-num { text-align: right; font-family: Consolas, monospace; }\n" +
    ".claims-chip { display: inline-block; padding: 1px 8px; border-radius: 9px; font-size: 11px; font-weight: bold; border: 1px solid; }\n" +
    ".claims-status-approved { color: #1d6b3c; background: #e2f4e8; border-color: #7fc49a; }\n" +
    ".claims-status-pending { color: #8a5a00; background: #fdf0d5; border-color: #e0b35a; }\n" +
    ".claims-status-rejected { color: #8f1d1d; background: #fbe2e2; border-color: #d98a8a; }\n" +
    ".claims-status-missing, .claims-status-unknown { color: #666666; background: #eeeeee; border-color: #bbbbbb; }\n" +
    ".claims-tier { display: inline-block; padding: 1px 7px; border-radius: 3px; font-size: 11px; border: 1px solid #b9c2d0; background: #eef1f6; color: #33415c; }\n" +
    ".claims-tier-high { background: #f3e8fd; border-color: #b48ad6; color: #5d2e86; }\n" +
    ".claims-detail { border: 1px solid #dde3ec; border-radius: 6px; padding: 10px 12px 14px; background: #ffffff; }\n" +
    ".claims-detail-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 6px; }\n" +
    ".claims-detail-id { font-size: 13px; font-weight: bold; }\n" +
    ".claims-detail-approved { font-size: 12px; color: #557744; }\n" +
    ".claims-section-title { margin: 10px 0 4px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #888888; }\n" +
    ".claims-claim-text { background: #f6f9f4; border-left: 4px solid #2e8b57; margin: 6px 0; padding: 6px 10px; white-space: pre-wrap; font-size: 13px; }\n" +
    ".claims-meta { font-size: 12px; color: #444444; margin: 4px 0; }\n" +
    ".claims-review-notes { white-space: pre-wrap; background: #f4f6f9; border: 1px solid #dde3ec; border-radius: 4px; padding: 6px 8px; font-size: 12px; color: #444444; }\n" +
    ".claims-source { border: 1px solid #dde3ec; border-radius: 4px; padding: 6px 8px; margin: 6px 0; background: #fbfcfe; }\n" +
    ".claims-source-row { font-size: 12px; margin: 2px 0; color: #333333; }\n" +
    ".claims-source-key { color: #777777; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.05em; margin-right: 6px; }\n" +
    ".claims-source a { color: #1f6feb; word-break: break-all; }\n" +
    ".claims-source-missing { color: #8f1d1d; font-size: 12px; margin: 4px 0; }\n" +
    ".claims-node-chips { display: flex; flex-wrap: wrap; gap: 2px; }\n" +
    ".claims-node-chip { display: inline-block; margin: 2px 4px 2px 0; padding: 2px 9px; border: 1px solid #9aa3b2; border-radius: 10px; background: #eef1f6; font-family: Consolas, monospace; font-size: 11.5px; cursor: pointer; color: #222222; }\n" +
    ".claims-node-chip:hover { background: #e3edfb; }\n" +
    ".claims-node-chip-warn { border-color: #d98a2b; background: #fdf0d5; color: #8a5a00; }\n" +
    ".claims-warn-note, .claims-warn-kind { font-size: 11.5px; color: #8a5a00; margin: 2px 0 0 6px; }\n" +
    ".claims-warn-row { display: flex; align-items: baseline; margin: 3px 0; }\n" +
    ".claims-sanctioned-info { display: flex; align-items: baseline; gap: 6px; background: #f4f6f9; border: 1px solid #dde3ec; border-radius: 4px; padding: 6px 8px; margin: 4px 0; font-size: 12px; color: #555555; }\n" +
    ".claims-allclean { font-size: 12px; color: #557744; }\n" +
    ".claims-detail-placeholder { color: #777777; font-style: italic; margin: 4px 0; }\n" +
    ".claims-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; padding: 40px 10px; color: #555555; font-size: 14px; text-align: center; }\n" +
    ".claims-empty p { margin: 2px 0; }\n" +
    ".claims-empty button { margin-top: 10px; padding: 5px 14px; border: 1px solid #9aa3b2; border-radius: 4px; background: #e8ecf3; cursor: pointer; }\n"
  );

})();
