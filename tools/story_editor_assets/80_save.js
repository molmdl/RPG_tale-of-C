/* ==========================================================================
 * 80_save.js — the persistence layer: draft + final save + crash copy
 * (plan 07.1-13; Requirement E, save half).
 *
 * OWNS: the #tab-save mount (the shell's fixed slot: "80_save.js: draft +
 * per-file save-edit"). Loads after 00_core.js (EDITOR contract), 05_json.js
 * (EDITOR.housy serializer), 10_load.js (boot/load layer), 20_validate.js
 * (save gate) and 30_graph.js; registers via EDITOR.view("save", render) +
 * EDITOR.init(...) per the 07.1-04 registration convention, and EXTENDS the
 * EDITOR.save namespace that 00_core.js opened (recomputeDirty lives there
 * and is consumed here at the mark-saved path; core's undo/redo call it).
 *
 * BINDING USER DIRECTIVES (verbatim): "i need firefox, should be able to
 * detect sub-dir in the same dir of the html" + "so saving temp/final json
 * could be more simple and universal. no api, no server."
 *
 * THE FILE SYSTEM ACCESS API IS BANNED in this asset (the binding directive
 * rejects it; grep-guarded by tests/test_story_editor_save.py test_no_fsa_api).
 * The ONE save primitive is downloadText(): the universal <a download> +
 * Blob URL pattern (RESEARCH-UI "Persistence — universal no-API model" +
 * Code Example 3). No servers, no POST, no network calls anywhere in this
 * asset — the editor NEVER writes to the repository itself; the human
 * places every downloaded file (display-only destinations below).
 *
 * FILENAME HONESTY (Pitfall 3b): the download attribute's filename is a
 * SUGGESTION (MDN <a>) — browsers adjust it and user settings change the
 * behavior entirely. Every affordance in this panel therefore displays the
 * exact expected filename and destination, and the panel shows the
 * recommended one-time Firefox setting ("Always ask you where to save
 * files") that makes each save land where intended.
 *
 * SOURCES:
 *   - .planning/.../07.1-RESEARCH-UI.md  "Persistence — universal no-API
 *     model", Code Examples 3-4, Pitfalls 3 / 3b / 3c
 *   - .planning/.../07.1-RESEARCH-SAFETY.md  "Save-edit semantics for
 *     multi-file edits" (per-file saves, git as the atomicity layer), the
 *     draft-fingerprint invalidation section, Pitfall S3 (stale draft
 *     clobbers a real save)
 *   - 10_load.js loadDraft (:1073-1124) — the draft-restore bookkeeping this
 *     asset mirrors for the crash-copy restore, and the onDraftLoaded hook
 *     point (:1257) this asset registers into.
 *
 * HOUSE STYLE: every emitted file body (draft doc included) is serialized
 * with EDITOR.housy.stringify (07.1-05's 1:1 port of the canonical
 * house-style serializer, 07.1-02) — NEVER the naive two-argument
 * JSON.stringify pretty-print, whose full-file reflow would bury the
 * intended change in the git diff (RESEARCH-SAFETY Pitfall S1). The body
 * gets one trailing newline appended (tools/story_editor_json.py returns
 * WITHOUT it; the Python file write appends it — same contract here so a
 * downloaded file is a drop-in replacement for a repo data file).
 *
 * KNOWN ROUND-TRIP LIMITATION (documented, flagged for the human): JS
 * JSON.parse has no parse_float hook (07.1-05's documented RawFloat
 * limitation), so X.0-style float tokens lose their ".0" at LOAD time and
 * the re-emitted body shows the shortest form — currently exactly one
 * token in the writable set (intro.json's hero rgb [0.0, 0.75, 0.75]
 * re-emits as [0, 0.75, 0.75]; same numeric value, one noisy diff line).
 * An unedited download of every OTHER story file + edits.json + cast.json
 * is byte-identical to the repo file (runtime-verified headlessly). The
 * full fix (lossless float-token parse) belongs to the load layer —
 * flagged, not attempted here (cross-asset architectural change). The
 * read-only citations.json "2.40" resolution tokens are the same
 * documented class and are never serialized by this save flow.
 *
 * LOCALSTORAGE IS OPTIONAL AND NON-LOAD-BEARING: a guarded, debounced
 * crash-recovery copy only (MDN storageAvailable try/catch; any storage
 * failure is silently swallowed). Nothing in the load/save flow DEPENDS on
 * it — the real draft is the downloaded file (user simplicity directive).
 *
 * STYLE: one classic script, one IIFE, ES5 only (var, no arrow functions,
 * no modules) — the emitted-page discipline pinned by
 * tests/test_story_editor_state.py and re-pinned for this block by
 * tests/test_story_editor_save.py.
 * ========================================================================== */

(function () {
  "use strict";

  // -------------------------------------------------------------------------
  // Constants.
  // -------------------------------------------------------------------------

  // The draft file (ROADMAP E "tmp file (git-ignored)"): ONE self-contained
  // JSON downloaded into the repo's tmp/ folder.
  var DRAFT_FILENAME = "story_editor_draft.json";

  // localStorage key for the OPTIONAL guarded crash copy (non-load-bearing;
  // Pitfall 1: storage on file:// is not portable — failures are swallowed).
  var CRASH_KEY = "rpg_story_editor_crash_draft";

  // Debounce for the crash copy: 800 ms after the last mutation
  // (RESEARCH-UI "Draft autosave cadence": after the last mutation, never
  // per keystroke, never on an idle timer).
  var CRASH_DEBOUNCE_MS = 800;

  // Opt-in "Download all" fires rows SEQUENTIALLY with ~400 ms gaps
  // (Pitfall 3: browsers may prompt once for multiple downloads; per-file
  // buttons are the default precisely so this never matters).
  var BATCH_GAP_MS = 400; // ~400 ms gaps between sequential downloads

  // Display-only destination map (RESEARCH-UI Code Example 4): fname to
  // repo-relative destination. Story files (and the manifest) live under
  // data/story_glucose/; the four non-story targets are listed explicitly.
  // DISPLAY-ONLY: the editor never writes to the repository — the human
  // places each downloaded file over its destination (no API, no server).
  var DEST_MAP = {
    "citations.json": "data/citations.json",
    "sources.json": "data/sources.json",
    "edits.json": "rpg/data/edits.json",
    "cast.json": "rpg/data/cast.json"
  };
  var STORY_DIR_PREFIX = "data/story_glucose/"; // default for story files

  function destFor(fname) {
    if (Object.prototype.hasOwnProperty.call(DEST_MAP, fname)) {
      return DEST_MAP[fname];
    }
    return STORY_DIR_PREFIX + fname;
  }

  // -------------------------------------------------------------------------
  // Small helpers.
  // -------------------------------------------------------------------------

  function describe(e) {
    return (e && e.message) ? String(e.message) : String(e);
  }

  function hasOwn(obj, key) {
    return Object.prototype.hasOwnProperty.call(obj, key);
  }

  function copyOwn(obj) {
    var out = {};
    if (!obj || typeof obj !== "object") return out;
    for (var k in obj) {
      if (hasOwn(obj, k)) out[k] = obj[k];
    }
    return out;
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  }

  function codeEl(text) {
    return el("code", "save-cmd", text);
  }

  function clearChildren(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  // MDN storageAvailable pattern (Web Storage API docs): browsers expose the
  // property but THROW on use (private mode, opaque origins, disabled
  // storage) — never feature-detect with a bare truthiness check.
  function storageAvailable(type) {
    var storage;
    try {
      storage = window[type];
      var x = "__storage_test__";
      storage.setItem(x, x);
      storage.removeItem(x);
      return true;
    } catch (e) {
      return false;
    }
  }

  // -------------------------------------------------------------------------
  // THE save primitive (RESEARCH-UI Code Example 3): Blob URL to a temp
  // <a download> to click to revoke. Zero APIs, works offline and on
  // file:// in every browser (MDN <a>: download applies to blob: URLs).
  // NOTE (Pitfall 3b): a.download is a SUGGESTION — the panel always
  // displays the exact expected name + destination next to every button.
  // -------------------------------------------------------------------------

  function downloadText(filename, text) {
    try {
      if (typeof URL === "undefined" || typeof URL.createObjectURL !==
          "function" || typeof Blob === "undefined") {
        setStatus("error", "This browser cannot create downloads (Blob or " +
                  "URL.createObjectURL missing).");
        return false;
      }
      var a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([text], {
        type: "application/json"
      }));
      a.download = filename; // SUGGESTION only — see the browser note below
      document.body.appendChild(a);
      a.click();
      a.parentNode.removeChild(a);
      setTimeout(function () {
        try {
          URL.revokeObjectURL(a.href);
        } catch (e2) { /* revoke is best-effort */ }
      }, 1000);
      return true;
    } catch (e) {
      setStatus("error", "Download failed: " + describe(e));
      return false;
    }
  }

  // -------------------------------------------------------------------------
  // Content lookup + serialization. Dirty fnames are story files in practice
  // (the mutators only touch bundle.files), but a restored draft may mark
  // one of the four registries dirty — those live at the bundle's top level,
  // not inside bundle.files.
  // -------------------------------------------------------------------------

  function fileContentOf(fname) {
    var b = EDITOR.state.bundle;
    if (!b) return null;
    if (fname === "citations.json") return (b.citations === undefined) ? null : b.citations;
    if (fname === "sources.json") return (b.sources === undefined) ? null : b.sources;
    if (fname === "edits.json") return (b.edits === undefined) ? null : b.edits;
    if (fname === "cast.json") return (b.cast === undefined) ? null : b.cast;
    if (b.files && hasOwn(b.files, fname)) return b.files[fname];
    return null;
  }

  // The downloaded body: house-style serialization + ONE trailing newline
  // (the repo files end with a newline; tools/story_editor_json.py's
  // stringify returns WITHOUT it and the file write appends it).
  function serializeBody(content) {
    return EDITOR.housy.stringify(content) + "\n";
  }

  // -------------------------------------------------------------------------
  // draftDoc — the self-contained draft (RESEARCH-UI Code Example 3):
  // bundle + dirty set + undo metadata + per-file fingerprints.
  //
  // SHAPE NOTE (deviation from the plan's "dirty: [fnames]" list form,
  // auto-fixed): the LANDED loader (10_load.js loadDraft :1092-1098)
  // restores draft.dirty as an OBJECT MAP ("for k in draft.dirty:
  // state.dirty[k] = true") — a for-in over an ARRAY would restore index
  // strings ("0", "1", ...) as dirty file names and corrupt the dirty
  // state. The dirty MAP carries exactly the same information (its keys
  // ARE the fname list) and round-trips through the landed consumer.
  // -------------------------------------------------------------------------

  function draftDoc() {
    var dirtyMap = {};
    var fnames = Object.keys(EDITOR.state.dirty);
    for (var i = 0; i < fnames.length; i++) {
      dirtyMap[fnames[i]] = true;
    }
    return {
      version: 1,
      saved_at: new Date().toISOString(),
      bundle: EDITOR.state.bundle,
      dirty: dirtyMap,
      undo_meta: {
        undo_depth: EDITOR.undoDepth(),
        redo_depth: EDITOR.redoDepth()
      },
      fingerprints: copyOwn(EDITOR.state.fingerprints)
    };
  }
  EDITOR.save.draftDoc = draftDoc; // exposed for the 07.1-18 diagnostics tab

  // -------------------------------------------------------------------------
  // Save draft — the explicit "Save draft" action. Drafts are ALWAYS
  // allowed, even while the validator blocks final saves: the draft is the
  // escape hatch that carries unsaved work out of a broken session.
  // -------------------------------------------------------------------------

  function saveDraft() {
    var b = EDITOR.state.bundle;
    if (!b) return;
    var text = EDITOR.housy.stringify(draftDoc()) + "\n";
    if (downloadText(DRAFT_FILENAME, text)) {
      setStatus("ok", DRAFT_FILENAME + " downloaded — save it into the " +
                "repo's tmp/ folder (git-ignored). Reload it any time via " +
                "'Load draft…' in the load panel above.");
    }
  }

  // -------------------------------------------------------------------------
  // Stale-draft detection (Pitfall S3: a stale draft must never silently
  // clobber a real save). staleCheck(fingerprints) compares the given
  // per-file fingerprints against the last completed FOLDER PICK's raw
  // texts (EDITOR.load.state.folderRawByFname — refreshed by every re-pick)
  // via the core FNV-1a drift detector. Keys without a folder counterpart
  // are simply not comparable. Returns the stale fname list.
  // (The fetch boot path keeps no raw copies, so nothing is comparable
  // there; the folder pick is the primary universal load path.)
  // -------------------------------------------------------------------------

  EDITOR.save.staleCheck = function (fingerprints) {
    var ls = (EDITOR.load && EDITOR.load.state) ? EDITOR.load.state : null;
    var raws = ls ? ls.folderRawByFname : null;
    var stale = [];
    if (!fingerprints || typeof fingerprints !== "object" || !raws) {
      return stale;
    }
    for (var fname in fingerprints) {
      if (!hasOwn(fingerprints, fname)) continue;
      var raw = raws[fname];
      if (typeof raw !== "string") continue; // not comparable (never picked)
      if (EDITOR.fnv1a(raw) !== fingerprints[fname]) {
        stale.push(fname);
      }
    }
    return stale;
  };

  // -------------------------------------------------------------------------
  // mark-saved (RESEARCH-SAFETY save sequence): the dirty bit is cleared
  // ONLY on the human's explicit confirm (the two-step arm + confirm row
  // control below) — git remains the atomicity layer. Marking saved resets
  // the per-file baseline to the CURRENT in-memory content and refreshes
  // the fingerprint + folder-text baselines to the downloaded body (the
  // same explicit confirm asserts the file was placed over the repo copy
  // verbatim; the next folder re-pick re-derives the true fingerprints).
  // Also persists the crash copy immediately so it never trails a
  // confirmed save (RESEARCH-SAFETY: a draft older than the last save of
  // the same files must never resurrect old content).
  // -------------------------------------------------------------------------

  function markSaved(fname) {
    var b = EDITOR.state.bundle;
    if (!b) return false;
    var content = fileContentOf(fname);
    if (content === null || content === undefined) return false;
    var body = serializeBody(content);
    if (b.files && hasOwn(b.files, fname)) {
      // Story files: reset the dirty baseline (recomputeDirty then keeps
      // the file clean until the next edit; undo re-dirties honestly).
      EDITOR._originals[fname] = JSON.stringify(b.files[fname]);
    }
    // NOTE: the four registries are not bundle.files members, so
    // recomputeDirty (which compares bundle.files only) re-marks them dirty
    // on the next undo/redo re-derivation. No current mutator can dirty
    // them — a registry dirty flag can only arrive from a restored draft,
    // and the delete below clears it for the session.
    EDITOR.state.fingerprints[fname] = EDITOR.fnv1a(body);
    var ls = (EDITOR.load && EDITOR.load.state) ? EDITOR.load.state : null;
    if (ls && ls.folderRawByFname) {
      ls.folderRawByFname[fname] = body; // same explicit confirm
    }
    delete EDITOR.state.dirty[fname];
    EDITOR.save.recomputeDirty();
    persistCrashCopy();
    return true;
  }
  EDITOR.save.markSaved = markSaved;

  // -------------------------------------------------------------------------
  // OPTIONAL guarded localStorage crash copy (non-load-bearing; user
  // simplicity directive). Debounced 800 ms after the last mutation via the
  // hooks.persist registration; restored only via the explicit banner
  // ("draft from earlier session found — restore? / dismiss"). ANY storage
  // failure is silently swallowed and nothing else changes behavior.
  // -------------------------------------------------------------------------

  function persistCrashCopy() {
    try {
      if (!storageAvailable("localStorage")) return;
      if (!EDITOR.state.bundle) return;
      localStorage.setItem(CRASH_KEY, EDITOR.housy.stringify(draftDoc()));
    } catch (e) {
      // silently swallowed — the crash copy is optional, never load-bearing
    }
  }

  function scheduleCrashCopy() {
    if (crashTimer) {
      clearTimeout(crashTimer);
    }
    crashTimer = setTimeout(function () {
      crashTimer = null;
      persistCrashCopy();
    }, CRASH_DEBOUNCE_MS);
  }

  function findCrashCopy() {
    try {
      if (!storageAvailable("localStorage")) return null;
      var raw = localStorage.getItem(CRASH_KEY);
      if (!raw || typeof raw !== "string") return null;
      var doc = JSON.parse(raw);
      if (!doc || typeof doc !== "object" ||
          Object.prototype.toString.call(doc) === "[object Array]" ||
          !doc.bundle || typeof doc.bundle !== "object") {
        return null;
      }
      return doc;
    } catch (e) {
      return null; // any storage failure is silently swallowed
    }
  }

  function clearCrashCopy() {
    try {
      if (storageAvailable("localStorage")) {
        localStorage.removeItem(CRASH_KEY);
      }
    } catch (e) { /* silently swallowed */ }
  }

  // Restore = the same bookkeeping as 10_load.js loadDraft (setBundle with
  // the draft bundle, then fingerprints + dirty restored verbatim) plus
  // handing the session to the load layer's draft state so a later folder
  // re-pick runs its staleness flow against THIS restored copy.
  function restoreCrashCopy() {
    var doc = crashState.found;
    crashState.found = null;
    crashState.hidden = true;
    if (!doc) return;
    EDITOR.setBundle(doc.bundle, null);
    if (doc.fingerprints && typeof doc.fingerprints === "object") {
      EDITOR.state.fingerprints = copyOwn(doc.fingerprints);
    }
    if (doc.dirty && typeof doc.dirty === "object") {
      for (var k in doc.dirty) {
        if (hasOwn(doc.dirty, k)) EDITOR.state.dirty[k] = true;
      }
    }
    var ls = (EDITOR.load && EDITOR.load.state) ? EDITOR.load.state : null;
    if (ls) {
      ls.draft = doc;
      ls.draftActive = true; // the restored copy IS a draft session
      ls.loaded = true;
      ls.lastSource = "draft";
    }
    clearCrashCopy(); // the session owns the content now; re-persisted on
                      // the next mutation by the debounced hook
    staleState.hasInfo = true;
    staleState.files = doc.fingerprints ? EDITOR.save.staleCheck(doc.fingerprints) : [];
    staleState.ack = false;
    setStatus("ok", "Crash-copy draft restored (saved " +
              (doc.saved_at || "unknown time") + "). Save it properly via " +
              "the actions below.");
    EDITOR.rerender();
  }

  // -------------------------------------------------------------------------
  // Discard draft (the Pitfall S3 "Discard" option): return the session to
  // the picked-folder baseline. Only offered when it cannot destroy work:
  // a folder baseline exists, every needed raw text is present, and NO
  // in-session edits have happened since the draft loaded (undo + redo
  // stacks empty — setBundle resets them at draft load, so any depth means
  // the human edited after loading). Otherwise explicit guidance is shown
  // instead (reload the page and pick the repository folder).
  // -------------------------------------------------------------------------

  function rebuildBundleFromRaws(raws) {
    if (!raws || typeof raws !== "object") return null;
    var manifestText = raws["manifest.json"];
    if (typeof manifestText !== "string") return null;
    var manifest = JSON.parse(manifestText);
    var flist = (manifest && Object.prototype.toString.call(manifest.files) ===
                 "[object Array]") ? manifest.files : null;
    if (!flist || !flist.length) return null;
    var files = {};
    var i;
    for (i = 0; i < flist.length; i++) {
      var fname = flist[i];
      var t = raws[fname];
      if (typeof t !== "string") return null; // incomplete baseline — refuse
      files[fname] = JSON.parse(t);
    }
    return {
      files: files,
      manifest: manifest,
      citations: parseMemberRaws(raws, "citations.json"),
      sources: parseMemberRaws(raws, "sources.json"),
      edits: parseMemberRaws(raws, "edits.json"),
      cast: parseMemberRaws(raws, "cast.json"),
      order: flist.slice()
    };
  }

  function parseMemberRaws(raws, fname) {
    var t = raws[fname];
    if (typeof t !== "string") return null; // degraded member (load-layer rule)
    try {
      return JSON.parse(t);
    } catch (e) {
      return null;
    }
  }

  function discardDraft() {
    var ls = (EDITOR.load && EDITOR.load.state) ? EDITOR.load.state : null;
    if (!ls || !ls.folderRawByFname) {
      discardGuidance = "The loaded draft replaced the session and no " +
        "folder baseline is in memory (data arrived via the direct-read " +
        "probe). Reload the page and pick the repository folder to " +
        "return to the folder data.";
      staleState.ack = true;
      renderSave();
      return;
    }
    if (EDITOR.undoDepth() !== 0 || EDITOR.redoDepth() !== 0) {
      discardGuidance = "You have made edits since this draft loaded — " +
        "discarding here would destroy them. Reload the page and pick " +
        "the repository folder instead (the browser discards the " +
        "in-memory session).";
      staleState.ack = true;
      renderSave();
      return;
    }
    var rebuilt = null;
    try {
      rebuilt = rebuildBundleFromRaws(ls.folderRawByFname);
    } catch (e) {
      rebuilt = null;
    }
    if (!rebuilt) {
      discardGuidance = "The folder baseline could not be rebuilt from the " +
        "picked raw texts. Reload the page and pick the repository " +
        "folder instead.";
      staleState.ack = true;
      renderSave();
      return;
    }
    ls.draft = null;
    ls.draftActive = false;
    ls.lastSource = "pick";
    EDITOR.setBundle(rebuilt, ls.folderRawByFname); // fingerprints recomputed
    staleState.hasInfo = false;
    staleState.files = [];
    staleState.ack = false;
    discardGuidance = null;
    setStatus("ok", "Draft discarded — the session now shows the picked " +
              "folder data (fingerprints recomputed from the folder).");
    EDITOR.rerender();
  }

  // -------------------------------------------------------------------------
  // onDraftLoaded — the 07.1-07 hook point (fires after a draft load AND
  // after a folder re-pick while a draft is active). Runs the stale check
  // for the draft's stored fingerprints and shows the LOUD warning with
  // Load-anyway / Discard options on any mismatch (Pitfall S3). The first
  // detection per session also switches to the Save tab so the warning is
  // actually seen (the load layer's own boot banner stays in its panel).
  // -------------------------------------------------------------------------

  function onDraftLoaded(info) {
    crashState.hidden = true; // a draft supersedes the crash-copy banner
    var draft = (info && info.draft) ? info.draft : null;
    staleState.hasInfo = !!draft;
    staleState.ack = false;
    discardGuidance = null;
    staleState.files = (draft && draft.fingerprints)
      ? EDITOR.save.staleCheck(draft.fingerprints)
      : [];
    staleState.rechecked = !!(info && info.recheckedAgainstFolder);
    if (staleState.files.length && !staleState.everAuto) {
      staleState.everAuto = true; // auto-switch once per session
      try {
        EDITOR.showTab("save");
      } catch (e) { /* tab switching is best-effort */ }
    }
    renderSave();
  }

  // -------------------------------------------------------------------------
  // Module state (transient UI bookkeeping; never persisted except through
  // the crash copy's draftDoc).
  // -------------------------------------------------------------------------

  var crashTimer = null;
  var crashState = {
    found: null,      // the parsed crash-copy draftDoc (checked once at init)
    hidden: false,    // superseded by a draft / restored
    dismissed: false  // dismissed for this session (the copy is KEPT — it
                      // may be the only copy of unsaved work)
  };
  var staleState = {
    hasInfo: false,   // a draft session is known to this panel
    files: [],        // stale fnames from the last check
    ack: false,       // "Load anyway" acknowledged
    rechecked: false, // last check ran after a folder re-pick
    everAuto: false   // the one-time auto tab switch fired
  };
  var discardGuidance = null;
  var armed = {};     // fname -> true (mark-saved arm step)
  var statusMsg = null; // { kind: "ok" | "warn" | "error", text: "..." }

  function setStatus(kind, text) {
    statusMsg = { kind: kind, text: text };
  }

  // -------------------------------------------------------------------------
  // Rendering. The panel is ONE persistent #save-panel container inside
  // #tab-save; every render rebuilds its children (full rerender strategy,
  // trivial at this scale). All clicks funnel through ONE delegated
  // listener on the container (data-action attributes).
  // -------------------------------------------------------------------------

  var panel = null;

  function ensurePanel() {
    if (panel) return panel;
    var host = document.getElementById("tab-save");
    if (!host) return null;
    panel = el("div");
    panel.id = "save-panel";
    host.appendChild(panel);
    EDITOR.delegate(panel, "click", "data-action", onSaveAction);
    return panel;
  }

  function bannerBox(kind, text) {
    var box = el("div", "save-banner save-banner-" + kind);
    box.appendChild(el("span", null, text));
    return box;
  }

  function renderCrashMount(parent) {
    var ls = (EDITOR.load && EDITOR.load.state) ? EDITOR.load.state : null;
    var draftActive = ls ? ls.draftActive : false;
    if (!crashState.found || crashState.hidden || crashState.dismissed ||
        draftActive) {
      return;
    }
    var box = el("div", "save-banner save-banner-warn");
    box.appendChild(el("strong", null,
      "Draft from an earlier session found — restore? "));
    box.appendChild(el("span", "save-muted",
      "(optional browser-storage crash copy — never load-bearing; the real " +
      "draft is the downloaded file. It was saved " +
      (crashState.found.saved_at || "at an unknown time") + ".)"));
    var row = el("div", "save-btn-row");
    row.appendChild(btn("Restore it", "crash-restore", null, "save-btn"));
    row.appendChild(btn("Dismiss", "crash-dismiss", null, "save-btn save-btn-secondary"));
    box.appendChild(row);
    parent.appendChild(box);
  }

  function renderStaleMount(parent, draft) {
    if (!staleState.hasInfo) return;

    if (staleState.files.length && !staleState.ack) {
      var box = el("div", "save-banner save-banner-error");
      box.appendChild(el("strong", null,
        "Data changed since this draft was saved — loading may clobber newer changes."));
      box.appendChild(el("div", "save-muted",
        "Stale files (fingerprints mismatch against the last picked " +
        "folder): " + staleState.files.join(", ") + "."));
      box.appendChild(el("div", "save-muted",
        staleState.rechecked
          ? "Re-checked against the freshly picked folder."
          : "Checked when the draft was loaded. Re-pick the repository " +
            "folder in the load panel above, then re-check here."));
      var row = el("div", "save-btn-row");
      row.appendChild(btn("Load anyway (draft wins)", "stale-ack", null,
        "save-btn"));
      row.appendChild(btn("Discard draft (return to the picked folder)",
        "stale-discard", null, "save-btn"));
      row.appendChild(btn("Re-check against folder", "stale-recheck", null,
        "save-btn save-btn-secondary"));
      box.appendChild(row);
      if (discardGuidance) {
        box.appendChild(el("div", "save-guidance", discardGuidance));
      }
      parent.appendChild(box);
      return;
    }

    if (staleState.files.length && staleState.ack) {
      var ackBox = el("div", "save-banner save-banner-warn");
      ackBox.appendChild(el("span", null,
        "Stale-draft warning acknowledged ('draft wins'): " +
        staleState.files.join(", ") + " changed in the repository after " +
        "this draft was saved. Discarding is still possible while no " +
        "edits have been made in this session."));
      var ackRow = el("div", "save-btn-row");
      ackRow.appendChild(btn("Re-check against folder", "stale-recheck", null,
        "save-btn save-btn-secondary"));
      ackBox.appendChild(ackRow);
      if (discardGuidance) {
        ackBox.appendChild(el("div", "save-guidance", discardGuidance));
      }
      parent.appendChild(ackBox);
      return;
    }

    var okBox = el("div", "save-banner save-banner-ok");
    okBox.appendChild(el("span", null,
      "Fingerprints match — the underlying files are unchanged since this " +
      "draft was saved" + (staleState.rechecked ?
        " (re-checked against the freshly picked folder)." : ".")));
    var okRow = el("div", "save-btn-row");
    okRow.appendChild(btn("Re-check against folder", "stale-recheck", null,
      "save-btn save-btn-secondary"));
    okBox.appendChild(okRow);
    parent.appendChild(okBox);
  }

  function saveRowDef(fname) {
    var content = fileContentOf(fname);
    if (content === null || content === undefined) return null;
    return {
      fname: fname,
      dest: destFor(fname),
      text: serializeBody(content)
    };
  }

  function renderSaveRow(parent, def) {
    var row = el("div", "save-row");
    row.setAttribute("data-fname", def.fname);

    var main = el("div", "save-row-main");
    main.appendChild(btn("Download " + def.fname, "download", def.fname,
      "save-btn"));
    main.appendChild(el("span", "save-arrow", " \u2192 save over "));
    main.appendChild(codeEl(def.dest));
    row.appendChild(main);

    var actions = el("div", "save-row-actions");
    if (armed[def.fname]) {
      actions.appendChild(el("span", "save-confirm-text",
        "confirm: file placed over " + def.dest + "?"));
      actions.appendChild(btn("\u2713 yes — mark saved", "mark-confirm",
        def.fname, "save-btn save-btn-confirm"));
      actions.appendChild(btn("\u2717 cancel", "mark-cancel", def.fname,
        "save-btn save-btn-secondary"));
    } else {
      actions.appendChild(btn("mark saved", "mark", def.fname,
        "save-btn save-btn-secondary"));
      actions.appendChild(el("span", "save-muted",
        "clears the dirty bit ONLY on your explicit confirm (git remains " +
        "the atomicity layer)"));
    }
    row.appendChild(actions);
    parent.appendChild(row);
  }

  function renderSave() {
    var p = ensurePanel();
    if (!p) return;
    clearChildren(p);

    var b = EDITOR.state.bundle;
    var ls = (EDITOR.load && EDITOR.load.state) ? EDITOR.load.state : null;
    var draftActive = !!(ls && ls.draftActive);
    var draft = (ls && ls.draft) ? ls.draft : null;

    var head = el("div", "save-section");
    head.appendChild(el("h2", null, "Save"));
    head.appendChild(el("p", "save-muted",
      "Universal no-API persistence: every save is a download " +
      "(<a download> + Blob). This editor NEVER writes to the repository " +
      "itself — no API, no server; you place each downloaded file."));
    p.appendChild(head);

    // Browser note (Pitfall 3b): the download filename is a SUGGESTION —
    // every affordance displays the exact expected name + destination, and
    // the recommended Firefox setting makes each save land where intended.
    var note = el("div", "save-section save-browser-note");
    note.appendChild(el("p", null,
      "The downloaded filename is a SUGGESTION (MDN): browsers may adjust " +
      "it, and user settings change the behavior entirely — every button " +
      "in this panel displays the exact expected filename and " +
      "destination."));
    note.appendChild(el("p", null,
      "Recommended one-time Firefox setting: Settings, General, Files, " +
      "\u201cAlways ask you where to save files\u201d. Then every download " +
      "opens a save dialog where you pick the exact name and location — " +
      "the draft lands in tmp/, final files overwrite their displayed " +
      "data/ destinations in place."));
    note.appendChild(el("p", "save-muted",
      "Known serializer note: X.0-style float tokens are re-emitted in " +
      "their shortest form by the browser's JSON parser (currently only " +
      "intro.json's hero rgb line [0.0, 0.75, 0.75], downloaded as " +
      "[0, 0.75, 0.75] — the same numeric value, but that line will show " +
      "in the git diff alongside your edit). Review the git diff as " +
      "instructed below; the Python gates re-verify everything."));
    p.appendChild(note);

    renderCrashMount(p);

    if (!b) {
      p.appendChild(el("p", "save-empty",
        "No data loaded — load the story data first (the load panel " +
        "above), or restore the crash-copy draft if one is offered."));
      renderStatus(p);
      return;
    }

    // --- Draft section (ALWAYS available — also while saves are blocked) ---
    var draftSec = el("div", "save-section");
    draftSec.appendChild(el("h2", null, "Save draft"));
    draftSec.appendChild(el("p", null,
      "One self-contained draft JSON (edited bundle + dirty set + undo " +
      "metadata + per-file fingerprints). Save it into the repo's tmp/ " +
      "folder (git-ignored); reload it any time via 'Load draft…' in the " +
      "load panel above."));
    var draftBtns = el("div", "save-btn-row");
    draftBtns.appendChild(btn("Save draft (downloads " + DRAFT_FILENAME + ")",
      "save-draft", null, "save-btn"));
    if (draftActive) {
      draftBtns.appendChild(btn("Re-check against folder", "stale-recheck",
        null, "save-btn save-btn-secondary"));
    }
    draftSec.appendChild(draftBtns);
    renderStaleMount(draftSec, draft);
    p.appendChild(draftSec);

    // --- Save edit (final): only dirty files, gated by the validator ---
    var editSec = el("div", "save-section");
    editSec.appendChild(el("h2", null, "Save edit (final) — only dirty files"));

    var blocked = (typeof EDITOR.saveBlocked === "function")
      ? EDITOR.saveBlocked() : false;

    if (blocked) {
      var errBox = el("div", "save-banner save-banner-error");
      errBox.appendChild(el("strong", null,
        "Save blocked — the validator reports errors. Fix them before " +
        "saving (the draft above remains available)."));
      var result = (typeof EDITOR.validateCurrent === "function")
        ? EDITOR.validateCurrent() : null;
      if (result && result.errors && result.errors.length) {
        var list = el("ul", "save-error-list");
        for (var i = 0; i < result.errors.length; i++) {
          var e2 = result.errors[i];
          list.appendChild(el("li", null,
            e2.kind + (e2.node ? " — " + e2.node : "") + ": " + e2.detail));
        }
        errBox.appendChild(list);
      }
      editSec.appendChild(errBox);
      p.appendChild(editSec);
      renderStatus(p);
      return;
    }

    var dirtyList = Object.keys(EDITOR.state.dirty).sort();
    if (!dirtyList.length) {
      editSec.appendChild(el("p", "save-muted",
        "Nothing to save — no files are dirty."));
      p.appendChild(editSec);
      renderStatus(p);
      return;
    }

    var defs = [];
    var missing = [];
    for (var d = 0; d < dirtyList.length; d++) {
      var def = saveRowDef(dirtyList[d]);
      if (def) {
        defs.push(def);
      } else {
        missing.push(dirtyList[d]);
      }
    }
    if (missing.length) {
      editSec.appendChild(bannerBox("warn",
        "No in-memory content found for: " + missing.join(", ") +
        " — cannot serialize what is not loaded."));
    }

    var rows = el("div", null);
    rows.id = "save-rows";
    for (var r = 0; r < defs.length; r++) {
      renderSaveRow(rows, defs[r]);
    }
    editSec.appendChild(rows);

    var allRow = el("div", "save-btn-row");
    allRow.appendChild(btn("Download all (" + defs.length + ")",
      "download-all", null, "save-btn save-btn-secondary"));
    allRow.appendChild(el("span", "save-muted",
      "opt-in: fires the rows sequentially with ~400 ms gaps — per-file " +
      "buttons are the default (browsers may prompt for multiple " +
      "downloads)."));
    editSec.appendChild(allRow);

    editSec.appendChild(renderReminder());
    p.appendChild(editSec);
    renderStatus(p);
  }

  // The post-save reminder (RESEARCH-UI Pitfall 3 / RESEARCH-SAFETY save
  // sequence): the editor cannot see the filesystem — the Python gates are
  // the only authoritative post-save check.
  function renderReminder() {
    var box = el("div", "save-reminder");
    box.appendChild(el("strong", null,
      "After placing the downloaded files over their repo destinations, " +
      "run the Python gates:"));
    var ul = el("ul", "save-cmd-list");
    var cmds = [
      "python3.6 tools/story_editor_lint.py",
      "python3.6 -m unittest discover -s tests",
      "python3.6 tools/check_citations.py --story data/story_glucose --registry data/citations.json",
      "git diff"
    ];
    for (var i = 0; i < cmds.length; i++) {
      var li = el("li");
      li.appendChild(codeEl(cmds[i]));
      ul.appendChild(li);
    }
    box.appendChild(ul);
    box.appendChild(el("div", "save-muted",
      "Review the diff before committing — the gates are the only " +
      "authoritative post-save check (the editor cannot see the " +
      "filesystem)."));
    return box;
  }

  function renderStatus(parent) {
    if (!statusMsg) return;
    parent.appendChild(bannerBox(statusMsg.kind, statusMsg.text));
  }

  function btn(label, action, fname, cls) {
    var b = el("button", cls || "save-btn", label);
    b.type = "button";
    b.setAttribute("data-action", action);
    if (fname) b.setAttribute("data-fname", fname);
    return b;
  }

  // -------------------------------------------------------------------------
  // ONE delegated click handler for every action in the panel.
  // -------------------------------------------------------------------------

  function onSaveAction(el2) {
    var action = el2.getAttribute("data-action");
    var fname = el2.getAttribute("data-fname");

    if (action === "save-draft") {
      saveDraft();
      renderSave();
      return;
    }
    if (action === "download") {
      var def = fname ? saveRowDef(fname) : null;
      if (def && downloadText(def.fname, def.text)) {
        setStatus("ok", "Downloaded " + def.fname + " — place it over " +
                  def.dest + " in the repository, then use 'mark saved' " +
                  "on its row.");
      }
      renderSave();
      return;
    }
    if (action === "download-all") {
      downloadAll();
      return;
    }
    if (action === "mark") {
      if (fname) armed[fname] = true;
      renderSave();
      return;
    }
    if (action === "mark-cancel") {
      if (fname) delete armed[fname];
      renderSave();
      return;
    }
    if (action === "mark-confirm") {
      var dest = destFor(fname);
      if (fname && markSaved(fname)) {
        delete armed[fname];
        setStatus("ok", "Marked " + fname + " saved over " + dest +
                  " — dirty bit cleared on your explicit confirm (git " +
                  "remains the atomicity layer). Run the gates below.");
      } else {
        setStatus("error", "Could not mark " + fname +
                  " saved (no in-memory content).");
      }
      EDITOR.rerender();
      return;
    }
    if (action === "stale-ack") {
      staleState.ack = true;
      renderSave();
      return;
    }
    if (action === "stale-discard") {
      discardDraft();
      return;
    }
    if (action === "stale-recheck") {
      recheckAgainstFolder();
      return;
    }
    if (action === "crash-restore") {
      restoreCrashCopy();
      return;
    }
    if (action === "crash-dismiss") {
      crashState.dismissed = true; // the copy is KEPT (may be the only copy)
      renderSave();
      return;
    }
  }

  function recheckAgainstFolder() {
    var ls = (EDITOR.load && EDITOR.load.state) ? EDITOR.load.state : null;
    var draft = (ls && ls.draft) ? ls.draft : null;
    if (!draft || !draft.fingerprints) {
      setStatus("warn", "No draft session to re-check.");
      renderSave();
      return;
    }
    staleState.hasInfo = true;
    staleState.ack = false;
    staleState.rechecked = true;
    staleState.files = EDITOR.save.staleCheck(draft.fingerprints);
    if (staleState.files.length) {
      setStatus("warn", "Re-check: data changed since this draft was " +
                "saved (" + staleState.files.join(", ") + ").");
    } else {
      setStatus("ok", "Re-check: fingerprints match the picked folder.");
    }
    renderSave();
  }

  // Opt-in sequential batch (Pitfall 3): rows fire one at a time with
  // ~400 ms gaps; per-file buttons remain the default.
  function downloadAll() {
    var dirtyList = Object.keys(EDITOR.state.dirty).sort();
    var defs = [];
    for (var i = 0; i < dirtyList.length; i++) {
      var def = saveRowDef(dirtyList[i]);
      if (def) defs.push(def);
    }
    if (!defs.length) {
      renderSave();
      return;
    }
    var idx = 0;
    function next() {
      if (idx >= defs.length) {
        setStatus("ok", "Batch finished: " + defs.length +
                  " download(s) fired sequentially with ~400 ms gaps — " +
                  "place each file over its displayed destination, then " +
                  "'mark saved' per row.");
        renderSave();
        return;
      }
      var def = defs[idx];
      idx++;
      downloadText(def.fname, def.text);
      setStatus("ok", "Batch: downloaded " + def.fname + " (" + idx + "/" +
                defs.length + ") — place it over " + def.dest + ".");
      renderSave();
      setTimeout(next, BATCH_GAP_MS); // ~400 ms gaps (Pitfall 3)
    }
    next();
  }

  // -------------------------------------------------------------------------
  // Registration (07.1-04 convention) + init.
  // -------------------------------------------------------------------------

  EDITOR.view("save", renderSave);

  // The optional crash-copy persist hook: after EVERY mutation (apply ->
  // afterChange) the debounced 800 ms crash copy is re-scheduled. Registered
  // defensively — hooks dispatch is core's job and never load-bearing here.
  if (EDITOR.hooks && EDITOR.hooks.persist) {
    EDITOR.hooks.persist.push(scheduleCrashCopy);
  }

  // The 07.1-07 draft-loaded hook point: full stale-draft UX (Pitfall S3).
  if (EDITOR.load && typeof EDITOR.load.onDraftLoaded === "function") {
    EDITOR.load.onDraftLoaded(onDraftLoaded);
  }

  EDITOR.init(function () {
    injectSaveCss();
    crashState.found = findCrashCopy(); // once per session, at boot
    renderSave();
  });

  // -------------------------------------------------------------------------
  // Asset CSS (per-feature styling lives with its feature, never in the
  // shell — the shell carries structural layout ONLY).
  // -------------------------------------------------------------------------

  function injectSaveCss() {
    EDITOR.injectCss(
      "/* injected by 80_save.js (07.1-13): save panel styles */\n" +
      "#save-panel { padding: 10px 14px 24px; max-width: 860px; }\n" +
      "#save-panel h2 { margin: 14px 0 6px; font-size: 15px; }\n" +
      "#save-panel .save-section { margin-bottom: 10px; }\n" +
      "#save-panel p { margin: 4px 0; }\n" +
      "#save-panel .save-muted { color: #666666; font-size: 12.5px; }\n" +
      "#save-panel .save-empty { color: #555555; }\n" +
      "#save-panel .save-btn-row { display: flex; align-items: center; " +
      "gap: 8px; flex-wrap: wrap; margin: 6px 0; }\n" +
      "#save-panel .save-btn { padding: 4px 10px; font-size: 13px; " +
      "cursor: pointer; }\n" +
      "#save-panel .save-btn-secondary { background: #eef1f6; }\n" +
      "#save-panel .save-btn-confirm { background: #e7f4e7; }\n" +
      "#save-panel .save-row { border: 1px solid #dde3ec; border-radius: " +
      "4px; padding: 6px 10px; margin: 6px 0; background: #fbfcfe; }\n" +
      "#save-panel .save-row-main { display: flex; align-items: center; " +
      "gap: 6px; flex-wrap: wrap; }\n" +
      "#save-panel .save-row-actions { display: flex; align-items: " +
      "center; gap: 8px; flex-wrap: wrap; margin-top: 4px; }\n" +
      "#save-panel .save-arrow { color: #555555; }\n" +
      "#save-panel .save-confirm-text { font-size: 12.5px; color: #1e5c1e; }\n" +
      "#save-panel .save-cmd { font-family: Consolas, monospace; " +
      "font-size: 12px; background: #f4f6f9; border: 1px solid #dde3ec; " +
      "border-radius: 3px; padding: 1px 5px; }\n" +
      "#save-panel .save-banner { margin: 6px 0; padding: 8px 10px; " +
      "border-radius: 4px; font-size: 13px; }\n" +
      "#save-panel .save-banner-ok { background: #e7f4e7; border: 1px " +
      "solid #3d8b3d; color: #1e5c1e; }\n" +
      "#save-panel .save-banner-warn { background: #fdf3df; border: 1px " +
      "solid #b8860b; color: #7a5a00; }\n" +
      "#save-panel .save-banner-error { background: #fdeae6; border: 1px " +
      "solid #b5442d; color: #8a2f1d; }\n" +
      "#save-panel .save-guidance { margin-top: 6px; font-size: 12.5px; " +
      "color: #7a5a00; }\n" +
      "#save-panel .save-error-list { margin: 6px 0 0; padding-left: 18px; " +
      "font-family: Consolas, monospace; font-size: 12px; }\n" +
      "#save-panel .save-reminder { margin-top: 10px; padding: 8px 10px; " +
      "border: 1px dashed #b8860b; border-radius: 4px; background: #fffdf5; " +
      "font-size: 13px; }\n" +
      "#save-panel .save-cmd-list { margin: 6px 0; padding-left: 18px; }\n" +
      "#save-panel .save-cmd-list li { margin: 3px 0; }\n"
    );
  }

})();
