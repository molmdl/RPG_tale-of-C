/* ==========================================================================
 * 10_load.js — the boot/load layer: DIRECT read on boot (open-and-go) ->
 * one-button folder-pick fallback -> checklist -> EDITOR.setBundle, plus
 * the single-file draft reload. Owner plan 07.1-07; direct-load rework =
 * the 07.1-11 fix-forward (rejected human checkpoint verdict: "not
 * working, even upload not working at all ... try to make it simple").
 *
 * FILE OWNERSHIP: this asset belongs to plan 07.1-07. It owns #boot-panel.
 * Never edit another plan's asset (00_core.js = 07.1-04, 05_json.js =
 * 07.1-05, 20_validate.js = 07.1-08, 30_graph.js = 07.1-06, ...); extend
 * the EDITOR namespace from your own file instead.
 *
 * THE BINDING USER DIRECTIVE (verbatim): Firefox + "detect sub-dir in the
 * same dir of the html ... try to make it simple and no need to request
 * this much work". The simple model:
 *
 *   1. DIRECT READ ON BOOT (primary, zero clicks). The editor reads
 *      data/story_glucose/manifest.json and the rest of the expected set
 *      straight off the disk and renders the graph immediately — the green
 *      "Data auto-detected in sub-directories" banner. All expected paths
 *      sit BELOW the HTML's own directory (data/... and rpg/data/... under
 *      the repo root).
 *   2. TRANSPORT CORRECTION (07.1-11). The original layer probed with
 *      the Fetch API and treated its file:// rejection as "Firefox blocks local
 *      reads" (CVE-2019-11730). That premise was WRONG, and the rejected
 *      checkpoint proved it: the Fetch API cannot read file:// URLs in Firefox
 *      at all — CVE-2019-11730 / MFSA 2019-21 ("Same-origin policy treats
 *      all files in a directory as having the same-origin") named the
 *      Fetch API as the exfiltration primitive ("The Fetch API can then
 *      be used to read the contents of any files stored in these
 *      directories"), and removing file: URLs from fetch was the fix.
 *      Classic subresource reads are NOT banned: Firefox's
 *      security.fileuri.strict_origin_policy (default TRUE) permits a
 *      file:// document to read files in the same directory or below it
 *      (i.e. the SAME DIRECTORY OR BELOW — the user's own living proof
 *      is tmp/network_all.html, whose
 *      same-directory <iframe src="network_ibp_mode_0.pdb_ali.html">
 *      loads fine in their Firefox. The fetch rejection only ever proved
 *      "fetch cannot do file://", never "reads are blocked" — so the
 *      direct load now uses XMLHttpRequest (the same policy class as the
 *      iframe), and on Firefox file:// the page is open-and-go with ZERO
 *      clicks. Chrome (and any environment that truly blocks local
 *      reads) takes the fallback.
 *   3. ONE-BUTTON FOLDER PICK (fallback only). If the direct read actually
 *      fails, the editor shows ONE control: <input type="file"
 *      webkitdirectory multiple>. File.webkitRelativePath is matched
 *      against the fixed EXPECTED path list via a "/"-boundary suffix
 *      match. Picking a parent of the repo works; picking a child folder
 *      (e.g. data/) matches nothing by design — the checklist then says
 *      "select the repository root".
 *   4. FOUND/MISSING CHECKLIST. One row per expected path with ✓/✗ and the
 *      friendly hint; the story-file rows are derived FROM the loaded
 *      manifest (manifest.files — never hard-listed before it loads).
 *      Required files missing: the editor blocks; citations/sources/cast
 *      degrade with warnings. The checklist stays available (collapsible)
 *      after load.
 *   5. DRAFT RELOAD. A single <input type="file" accept=".json,...">
 *      restores a downloaded draft bundle {version, saved_at, bundle,
 *      dirty, undo_meta, fingerprints} via EDITOR.setBundle —
 *      self-contained, no folder re-pick needed. When folder-picked raw
 *      texts are also available, the draft's stored per-file fingerprints
 *      are compared against them (32-bit FNV-1a — a drift DETECTOR, not
 *      security) and a mismatch warns "underlying files changed since
 *      this draft". The full stale-draft UX lives in 07.1-13's save
 *      layer; this asset provides the load + the
 *      EDITOR.load.onDraftLoaded hook point.
 *
 * PICK-HANDLER FIX (07.1-11, the "even upload not working at all"
 * defect): the original handler cleared input.value = "" while still
 * holding the LIVE input.files list. Clearing the selection empties a
 * live list, so the captured reference read length 0 and the handler
 * silently returned before doing anything — the pick appeared completely
 * dead on Firefox. The File objects are now snapshotted into a plain
 * array BEFORE the clear (File objects themselves stay valid).
 *
 * SECURITY GUARDS (Pitfall 3c): the folder pick hands the editor the
 * ENTIRE picked tree including .git — paths are filtered against the
 * fixed expected list and only matched files are read; any path that
 * contains "..", a drive letter, or a leading "/" is rejected outright.
 * .git and sibling files are never enumerated into reads.
 *
 * STYLE: one classic script, one IIFE, ES5 only (module scripts fail
 * under file:// CORS). Zero dependencies: FileReader + XMLHttpRequest
 * are browser built-ins.
 * ========================================================================== */

(function () {
  "use strict";

  var ED = window.EDITOR;
  if (!ED) {
    // The core asset (00_core.js) did not run — nothing to attach to.
    // Surface it loudly but non-fatally; the shell still renders.
    try {
      if (typeof console !== "undefined" && console && console.warn) {
        console.warn("EDITOR.load: window.EDITOR missing — 00_core.js did " +
                     "not run; the load layer is disabled");
      }
    } catch (e) { /* never warn about failing to warn */ }
    return;
  }

  // -------------------------------------------------------------------------
  // The fixed EXPECTED path list — sub-directories of the HTML's own dir
  // (the directive; placement at repo root is load-bearing). The story
  // files themselves are resolved FROM the loaded manifest (manifest.files)
  // and are NEVER hard-listed here before it loads.
  //
  // severity: "block" = the editor cannot start without it;
  //           "warn"  = degrade-with-warning (claims panel / cast lookup).
  // -------------------------------------------------------------------------
  var MANIFEST_PATH = "data/story_glucose/manifest.json";
  var STORY_DIR_PREFIX = "data/story_glucose/";

  var EXPECTED_SPEC = [
    { path: MANIFEST_PATH,
      severity: "block",
      role: "the manifest — every story file is resolved from manifest.files" },
    { path: "data/citations.json",
      severity: "warn",
      role: "claim registry (read-only; the claims panel degrades)" },
    { path: "data/sources.json",
      severity: "warn",
      role: "source registry (read-only; provenance degrades)" },
    { path: "rpg/data/edits.json",
      severity: "block",
      role: "known-edit buckets — a required edit target" },
    { path: "rpg/data/cast.json",
      severity: "warn",
      role: "cast — optional-degrade with a warning (viewer convention)" }
  ];

  var EXPECTED = [];
  var SEVERITY = {};
  var DEGRADE_NOTE = {
    "data/citations.json":
      "the claims panel will be limited (claim registry unavailable)",
    "data/sources.json":
      "source provenance will be limited (source registry unavailable)",
    "rpg/data/cast.json":
      "the cast lookup degrades to empty (viewer convention)"
  };
  (function buildExpected() {
    for (var i = 0; i < EXPECTED_SPEC.length; i++) {
      EXPECTED.push(EXPECTED_SPEC[i].path);
      SEVERITY[EXPECTED_SPEC[i].path] = EXPECTED_SPEC[i].severity;
    }
  })();

  function severityFor(path) {
    if (Object.prototype.hasOwnProperty.call(SEVERITY, path)) {
      return SEVERITY[path];
    }
    // Manifest-listed story files (data/story_glucose/<fname>):
    return "block"; // the story itself — always required, never degraded
  }

  // -------------------------------------------------------------------------
  // Module state.
  // -------------------------------------------------------------------------
  var bootState = {
    booted: false,        // boot() ran (idempotent)
    probeSettled: false,  // the direct-read probe settled (ok or miss)
    watchdog: null,       // probe-hang timer (never a dead "loading…" state)
    pickRevealed: false,  // the folder-pick panel is visible
    pickNoteSet: false,
    pickedIndex: null,    // last folder pick: [{rel, file}] (safe paths only)
    lastPickMatched: 0,   // how many of the 5 expected paths the pick matched
    folderRawByFname: null, // last PICK-completed {fname: rawText} — the
                            // fingerprint baseline for draft staleness
    draft: null,          // the active draft object (if any)
    draftActive: false,   // the session bundle came from a draft file
    loaded: false,        // a bundle reached EDITOR.setBundle
    collapsed: false,     // boot panel details collapsed (after load)
    lastSource: null      // "direct" | "pick" | "draft"
  };

  var draftLoadedFns = [];

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
  // Path matching + security guards (RESEARCH-UI Code Example 1 / Pitfall 3c).
  // -------------------------------------------------------------------------

  // "/"-boundary suffix match: the picked path must EQUAL the expected path
  // or END WITH "/" + expected — so picking a PARENT of the repo also works,
  // while picking a child folder (e.g. data/) matches nothing by design
  // (the checklist then says "select the repository root"). Case-sensitive
  // throughout: repo paths are lowercase, exactly as committed.
  function matchesSuffix(relPath, expected) {
    var rel = String(relPath == null ? "" : relPath);
    var exp = String(expected == null ? "" : expected);
    if (rel === exp) return true;
    return rel.length > exp.length &&
      rel.charAt(rel.length - exp.length - 1) === "/" &&
      rel.lastIndexOf(exp) === rel.length - exp.length;
  }

  // Returns the EXPECTED path matched by relPath, or null.
  function matchesExpected(relPath) {
    for (var i = 0; i < EXPECTED.length; i++) {
      if (matchesSuffix(relPath, EXPECTED[i])) return EXPECTED[i];
    }
    return null;
  }

  // SECURITY GUARDS: reject any path containing "..", a drive letter
  // (C: style), or a leading "/". webkitRelativePath should never carry
  // these, but nothing stops sloppy matching — the guards make it
  // impossible to act on one.
  function pathIsUnsafe(rel) {
    var s = String(rel == null ? "" : rel);
    return s.indexOf("..") >= 0 ||
           /^[A-Za-z]:/.test(s) ||
           s.charAt(0) === "/";
  }

  function fnameOfPath(path) {
    var s = String(path == null ? "" : path);
    return s.slice(s.lastIndexOf("/") + 1);
  }

  function storyPathOf(fname) {
    return STORY_DIR_PREFIX + fname;
  }

  function storyPathsOf(files) {
    var out = [];
    for (var i = 0; i < files.length; i++) out.push(storyPathOf(files[i]));
    return out;
  }

  // -------------------------------------------------------------------------
  // Manifest parsing (shared by the direct-read path and the pick path).
  // -------------------------------------------------------------------------

  function parseManifest(text) {
    if (text == null) {
      return { manifest: null, files: null, error: "missing" };
    }
    var m;
    try {
      m = JSON.parse(text);
    } catch (e) {
      return { manifest: null, files: null,
               error: "malformed JSON: " + describe(e) };
    }
    if (!m || typeof m !== "object" ||
        Object.prototype.toString.call(m) === "[object Array]") {
      return { manifest: null, files: null,
               error: "manifest.json must be a JSON object" };
    }
    var files = m.files;
    if (Object.prototype.toString.call(files) !== "[object Array]" ||
        !files.length) {
      return { manifest: null, files: null,
               error: 'manifest.json lists no "files" array' };
    }
    for (var i = 0; i < files.length; i++) {
      if (typeof files[i] !== "string" || !files[i]) {
        return { manifest: null, files: null,
                 error: "manifest.files[" + i + "] must be a file-name string" };
      }
    }
    return { manifest: m, files: files, error: null };
  }

  // -------------------------------------------------------------------------
  // Registry duplicate-key guard (parseNoDupKeys).
  //
  // JSON.parse silently KEEPS THE LAST duplicate key, so a duplicated
  // claim_id/source_id would silently drop records (RESEARCH-DATA §3 row 4;
  // the Python lint treats duplicate registries as a schema error). A
  // JSON.parse reviver CANNOT detect duplicates — they are already collapsed
  // before the reviver runs — so the raw text is pre-scanned with a tiny
  // DEPTH-1 STRUCTURAL WALK (regex-free): it tracks only strings/escapes/
  // container depth and records the keys of the TOP-LEVEL object.
  //
  // APPROXIMATION (documented per plan): both registries are FLAT maps
  // (claim_id -> record, source_id -> record), so the top level is exactly
  // where a duplicate claim_id would appear; duplicate keys in NESTED
  // objects are not detected. JSON.parse itself still rejects malformed
  // JSON — this walk only ADDS the duplicate check.
  // -------------------------------------------------------------------------

  function collectTopLevelKeys(text) {
    var s = String(text == null ? "" : text);
    var keys = [];
    var depth = 0;
    var inStr = false;
    var esc = false;
    var keyStart = -1;     // opening quote index of a possible top-level key
    var awaitingColon = false;
    var candidate = null;
    var lastSig = "";      // last significant (non-space, outside-string) char
    var i, c;

    for (i = 0; i < s.length; i++) {
      c = s.charAt(i);
      if (inStr) {
        if (esc) {
          esc = false;
        } else if (c === "\\") {
          esc = true;
        } else if (c === '"') {
          inStr = false;
          if (depth === 1 && keyStart >= 0) {
            candidate = s.slice(keyStart + 1, i);
            awaitingColon = true;
            keyStart = -1;
          }
        }
        continue;
      }
      if (c === '"') {
        inStr = true;
        // A string at KEY position in the top-level object starts right
        // after "{" or "," (at depth 1). Value strings start after ":" and
        // are ignored; nested keys sit at depth > 1 and are ignored too.
        if (depth === 1 && (lastSig === "{" || lastSig === ",")) {
          keyStart = i;
        }
        continue;
      }
      if (c === " " || c === "\t" || c === "\n" || c === "\r") {
        continue;
      }
      if (awaitingColon) {
        if (c === ":") {
          keys.push(candidate);
        }
        awaitingColon = false;
        candidate = null;
      }
      if (c === "{" || c === "[") {
        depth++;
      } else if (c === "}" || c === "]") {
        depth--;
      }
      lastSig = c;
    }
    return keys;
  }

  // JSON.parse + duplicate-key detection over the top-level object.
  // Throws Error('duplicate top-level key "K" in <label> ...') on a repeat.
  function parseNoDupKeys(text, label) {
    var obj = JSON.parse(text); // malformed JSON still fails here, loudly
    var keys = collectTopLevelKeys(text);
    var seen = {};
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      if (Object.prototype.hasOwnProperty.call(seen, k)) {
        throw new Error('duplicate top-level key "' + k + '" in ' + label +
                        " (JSON.parse would keep the last duplicate " +
                        "silently — every registry key must be unique)");
      }
      seen[k] = true;
    }
    return obj;
  }

  // -------------------------------------------------------------------------
  // FileReader helpers (the pick path) — ES5 callbacks, no async/await.
  // -------------------------------------------------------------------------

  function readText(file, cb) {
    var reader = new FileReader();
    reader.onload = function () {
      cb(String(reader.result == null ? "" : reader.result));
    };
    reader.onerror = function () {
      cb(null);
    };
    try {
      reader.readAsText(file); // <— the plan-mandated load primitive
    } catch (e) {
      cb(null);
    }
  }

  // fileMap: {key: File}; keys: [key, ...]; done(texts: {key: text|null}).
  function readMany(fileMap, keys, done) {
    var out = {};
    var pending = keys.length;
    if (!pending) {
      done(out);
      return;
    }
    function one(k) {
      readText(fileMap[k], function (text) {
        out[k] = text;
        pending--;
        if (pending === 0) done(out);
      });
    }
    for (var i = 0; i < keys.length; i++) {
      one(keys[i]);
    }
  }

  function mergeInto(dst, src) {
    for (var k in src) {
      if (Object.prototype.hasOwnProperty.call(src, k)) {
        dst[k] = src[k];
      }
    }
  }

  function copyOwn(obj) {
    var out = {};
    for (var k in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, k)) {
        out[k] = obj[k];
      }
    }
    return out;
  }

  // -------------------------------------------------------------------------
  // XHR transport — the DIRECT-READ path (07.1-11 correction).
  //
  // XMLHttpRequest is used instead of fetch because the Fetch API cannot read
  // file:// URLs in Firefox at all (CVE-2019-11730 removed file: URLs from
  // the Fetch API; see the header). XHR is a classic subresource read and
  // follows security.fileuri.strict_origin_policy (default true): a
  // file:// document may read files in the SAME DIRECTORY OR BELOW — which
  // covers every expected path (data/... and rpg/data/... sit below the
  // HTML's directory). On file:// a successful read reports status 0; over
  // http(s) it reports 200. Both count as success when text came back.
  // -------------------------------------------------------------------------

  // Reads one file relative to the document. cb(text|null): null = not
  // reachable (a per-file miss must NOT abort the whole set — the
  // checklist reports it, and the block/warn severities decide the
  // outcome). The settled guard keeps the callback single-shot: on file://
  // failures both onerror and onreadystatechange(4) can fire.
  function xhrText(path, cb) {
    var settled = false;
    function finish(text) {
      if (settled) return;
      settled = true;
      cb(text);
    }
    try {
      var xhr = new XMLHttpRequest();
      xhr.open("GET", path, true);
      xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) return;
        var ok = (xhr.status === 0 ||
                  (xhr.status >= 200 && xhr.status < 300)) &&
                 typeof xhr.responseText === "string" &&
                 xhr.responseText !== "";
        finish(ok ? xhr.responseText : null);
      };
      xhr.onerror = function () { finish(null); };
      xhr.send(null);
    } catch (e) {
      finish(null);
    }
  }

  // Reads many paths in parallel; done({path: text|null}).
  function xhrMany(paths, done) {
    var out = {};
    var pending = paths.length;
    if (!pending) {
      done(out);
      return;
    }
    for (var i = 0; i < paths.length; i++) {
      (function (p) {
        xhrText(p, function (t) {
          out[p] = t;
          pending--;
          if (pending === 0) done(out);
        });
      })(paths[i]);
    }
  }

  // -------------------------------------------------------------------------
  // Boot-panel DOM helpers (this asset OWNS #boot-panel).
  // -------------------------------------------------------------------------

  function setProbeStatus(text) {
    var el = document.getElementById("boot-probe-status");
    if (el) el.textContent = text;
  }

  function showBanners(items) {
    var box = document.getElementById("boot-banners");
    if (!box) return;
    while (box.firstChild) box.removeChild(box.firstChild);
    for (var i = 0; i < items.length; i++) {
      var d = document.createElement("div");
      d.className = "boot-banner boot-banner-" + items[i].kind;
      d.textContent = items[i].text;
      box.appendChild(d);
    }
  }

  function banner(text, kind) {
    showBanners([{ text: text, kind: kind || "ok" }]);
  }

  function setSummary(text) {
    var el = document.getElementById("boot-summary");
    if (el) el.textContent = text;
  }

  function setCollapsed(collapsed) {
    bootState.collapsed = !!collapsed;
    // The static expected-layout wall (boot-help-copy) is NOT in this list:
    // it is hidden for good at mount (open-and-go — the checklist rows
    // already state every expected path; the user rejected the copy wall).
    var ids = ["boot-checklist", "boot-pick-wrap", "boot-draft-wrap",
               "boot-probe-status"];
    for (var i = 0; i < ids.length; i++) {
      // The pick wrap stays hidden until the probe rejection reveals it —
      // expanding must not pre-reveal it (probe-then-fallback discipline).
      if (ids[i] === "boot-pick-wrap" && !bootState.pickRevealed) continue;
      var el = document.getElementById(ids[i]);
      if (!el) continue;
      if (collapsed) {
        el.setAttribute("hidden", "hidden");
      } else {
        el.removeAttribute("hidden");
      }
    }
    var toggle = document.getElementById("boot-toggle");
    if (toggle) {
      toggle.textContent = collapsed ? "Show details" : "Hide details";
    }
  }

  function collapseBootPanel() {
    var panel = document.getElementById("boot-panel");
    if (panel) panel.classList.add("boot-loaded");
    var head = document.getElementById("boot-head-row");
    if (head) head.removeAttribute("hidden");
    setCollapsed(true);
  }

  function setPickNote(note) {
    bootState.pickNoteSet = true;
    var el = document.getElementById("boot-pick-note");
    if (!el) return;
    el.textContent = note || (
      "Direct reads are blocked in this browser — that is expected when " +
      "a locally opened page is not allowed to read files here. Click " +
      "below and select the repository root folder (or any parent of it); " +
      "the editor matches the expected data paths itself.");
  }

  // Reveals the folder-pick panel (idempotent). Called ONLY after the
  // direct-read probe has settled — the reveal is the fallback, never the
  // first move.
  function revealPickPanel(note) {
    bootState.pickRevealed = true;
    var wrap = document.getElementById("boot-pick-wrap");
    if (wrap) wrap.removeAttribute("hidden");
    if (note) {
      setPickNote(note);
    } else if (!bootState.pickNoteSet) {
      setPickNote(null); // the short fallback explanation
    }
  }

  // -------------------------------------------------------------------------
  // Checklist rendering — one row per expected path with ✓/✗ and the
  // friendly hint (RESEARCH-UI Persistence step 3). textContent only —
  // no HTML injection surface.
  // -------------------------------------------------------------------------

  function missingNote(source) {
    if (source === "direct") {
      return "missing (not reachable from this location)";
    }
    return "expected under the folder you picked; did you select the " +
           "repository root?";
  }

  function renderChecklist(rows) {
    var ul = document.getElementById("boot-checklist");
    if (!ul) return;
    while (ul.firstChild) ul.removeChild(ul.firstChild);
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      var li = document.createElement("li");
      var cls = "boot-row ";
      if (r.ok) {
        cls += "boot-ok";
      } else if (r.severity === "block") {
        cls += "boot-block";
      } else {
        cls += "boot-warn";
      }
      li.className = cls;
      var mark = r.ok ? "✓ " : "✗ ";
      var text = mark + r.path + (r.note ? " — " + r.note : "");
      li.textContent = text;
      ul.appendChild(li);
    }
  }

  // -------------------------------------------------------------------------
  // Completion: turn a {expectedPath: rawText|null} map into checklist rows,
  // parse everything, and either assemble the bundle -> EDITOR.setBundle or
  // block with the missing/malformed report. Shared by BOTH load paths.
  // -------------------------------------------------------------------------

  function completeFromTexts(texts, source) {
    var rows = [];
    var blockers = [];
    var warnings = [];
    var parsedFiles = {};   // fname -> parsed story-file object
    var rawByFname = {};    // fname -> raw text (fingerprints / staleness)
    var parsed = {
      manifest: null, citations: null, sources: null,
      edits: null, cast: null
    };

    // --- the manifest first: everything keys off it (manifest.files) ---
    var mres = parseManifest(texts[MANIFEST_PATH]);
    if (mres.error) {
      rows.push({ path: MANIFEST_PATH, ok: false, severity: "block",
                  note: mres.error === "missing"
                    ? missingNote(source) : mres.error });
      blockers.push(MANIFEST_PATH + " " +
                    (mres.error === "missing" ? "is missing" : mres.error));
      finishBlocked(rows, blockers, warnings, source);
      return;
    }
    parsed.manifest = mres.manifest;
    rows.push({ path: MANIFEST_PATH, ok: true, severity: "block", note: "" });

    // --- the fixed remaining expected paths ---
    function collectExpected(path) {
      var sev = severityFor(path);
      var fname = fnameOfPath(path);
      var text = texts[path];
      if (text == null) {
        rows.push({ path: path, ok: false, severity: sev,
                    note: missingNote(source) });
        if (sev === "block") {
          blockers.push(path + " is missing");
        } else {
          warnings.push(path + " is missing — " +
                        (DEGRADE_NOTE[path] || "degraded") + ".");
        }
        return;
      }
      var obj = null;
      var err = null;
      try {
        // The two read-only REGISTRIES get the duplicate-key guard (a
        // duplicated claim_id/source_id must be detected on load —
        // RESEARCH-DATA §3 row 4); writable files parse plainly.
        if (path === "data/citations.json" || path === "data/sources.json") {
          obj = parseNoDupKeys(text, path);
        } else {
          obj = JSON.parse(text);
        }
      } catch (e) {
        err = e;
      }
      if (err) {
        rows.push({ path: path, ok: false, severity: sev,
                    note: describe(err) });
        if (sev === "block") {
          blockers.push(path + " could not be parsed: " + describe(err));
        } else {
          warnings.push(path + " could not be parsed — " +
                        (DEGRADE_NOTE[path] || "degraded") + " (" +
                        describe(err) + ")");
        }
        return;
      }
      rows.push({ path: path, ok: true, severity: sev, note: "" });
      rawByFname[fname] = text;
      parsed[fname.replace(/\.json$/, "")] = obj;
    }

    // --- story files resolved FROM the loaded manifest (manifest.files) ---
    function collectStory(fname) {
      var path = storyPathOf(fname);
      var text = texts[path];
      if (text == null) {
        rows.push({ path: path, ok: false, severity: "block",
                    note: missingNote(source) + " (listed in manifest.files)" });
        blockers.push(path + " is missing (listed in manifest.files)");
        return;
      }
      var obj = null;
      var err = null;
      try {
        obj = JSON.parse(text);
      } catch (e) {
        err = e;
      }
      if (err || !obj || typeof obj !== "object" ||
          !obj.nodes || typeof obj.nodes !== "object") {
        var why = err ? describe(err) : 'no "nodes" object';
        rows.push({ path: path, ok: false, severity: "block", note: why });
        blockers.push(path + " is unusable: " + why);
        return;
      }
      rows.push({ path: path, ok: true, severity: "block", note: "" });
      rawByFname[fname] = text;
      parsedFiles[fname] = obj;
    }

    for (var i = 1; i < EXPECTED.length; i++) {
      collectExpected(EXPECTED[i]);
    }
    var files = mres.files;
    for (var s = 0; s < files.length; s++) {
      collectStory(files[s]);
    }

    renderChecklist(rows);

    if (blockers.length) {
      finishBlocked(rows, blockers, warnings, source);
      return;
    }
    finishLoad(parsed, parsedFiles, rawByFname, files, source, warnings);
  }

  function finishBlocked(rows, blockers, warnings, source) {
    renderChecklist(rows);
    bootState.loaded = false;
    var extra = "";
    if (source === "pick" && bootState.lastPickMatched === 0) {
      extra = " No expected file matched the picked folder — a sub-folder " +
              "pick (like data/) matches nothing by design: select the " +
              "repository root.";
    }
    var items = [{
      text: "Editor cannot start — " + blockers.length +
            " required file(s) missing or unreadable: " +
            blockers.join("; ") + "." + extra,
      kind: "error"
    }];
    for (var i = 0; i < warnings.length; i++) {
      items.push({ text: warnings[i], kind: "warn" });
    }
    showBanners(items);
    if (source === "direct") {
      // Direct reads reach the folder but the data is broken/absent there —
      // the picker is the universal self-service fix, reveal it too.
      revealPickPanel("Some data files are missing or unreadable from " +
                      "this location — you can pick the repository " +
                      "folder instead.");
    }
  }

  function finishLoad(parsed, parsedFiles, rawByFname, manifestFiles,
                      source, warnings) {
    var order = manifestFiles.slice(); // manifest order == bundle.order
    var files = {};
    for (var i = 0; i < order.length; i++) {
      files[order[i]] = parsedFiles[order[i]];
    }
    var bundle = {
      files: files,          // {fname: {nodes: {id: node}, ...}}
      manifest: parsed.manifest,
      citations: parsed.citations,  // null on degrade (claims panel degrades)
      sources: parsed.sources,      // null on degrade
      edits: parsed.edits,          // REQUIRED — never null here (blocks)
      cast: parsed.cast,            // null on degrade (viewer convention)
      order: order
    };
    if (source === "pick") {
      // The fresh folder texts become the fingerprint baseline for the
      // draft staleness comparison (both pick orders are supported).
      bootState.folderRawByFname = rawByFname;
    }

    if (bootState.draftActive && source === "pick") {
      // A draft session is active: the re-pick must NOT silently discard it
      // (RESEARCH-UI step 4 — "if the folder is also re-picked, fingerprint
      // comparison warns"). Refresh the baseline, compare, warn; reload the
      // page to start over from the picked folder instead.
      var stale = compareDraftToFolderRaw();
      var items = [{
        text: "Folder picked — still showing the loaded draft. Reload the " +
              "page to start from the picked folder instead.",
        kind: "ok"
      }];
      if (stale.length) {
        items.push({
          text: "WARNING: underlying files changed since this draft: " +
                stale.join(", "),
          kind: "warn"
        });
      } else {
        items.push({
          text: "Fingerprints match — the underlying files are unchanged " +
                "since this draft.",
          kind: "ok"
        });
      }
      showBanners(items);
      fireDraftLoaded({
        draft: bootState.draft,
        sourceName: null,
        staleFiles: stale,
        recheckedAgainstFolder: true
      });
      collapseBootPanel();
      return;
    }

    ED.setBundle(bundle, rawByFname);
    bootState.loaded = true;
    bootState.draftActive = false; // direct/pick data replaces any draft
    bootState.draft = null;
    bootState.lastSource = source;

    var msg;
    if (source === "direct") {
      msg = "Data auto-detected in sub-directories"; // the green banner
    } else {
      msg = "Data loaded from the picked folder";
    }
    msg += " — " + order.length + " story file(s) + manifest + edits" +
      (parsed.citations ? " + citations" : "") +
      (parsed.sources ? " + sources" : "") +
      (parsed.cast ? " + cast" : "") + ".";
    var items = [{ text: msg, kind: "ok" }];
    for (var w = 0; w < warnings.length; w++) {
      items.push({ text: warnings[w], kind: "warn" });
    }
    showBanners(items);
    setSummary("Loaded " + order.length + " story file(s) from " +
               (source === "direct"
                 ? "direct reads (sub-directories detected)"
                 : "the picked folder") +
               (warnings.length
                 ? " — " + warnings.length + " warning(s)"
                 : "") + ".");
    collapseBootPanel();
  }

  // -------------------------------------------------------------------------
  // BOOT SEQUENCE — direct read FIRST (open-and-go), pick only on a real
  // miss (07.1-11 corrected contract).
  //
  // Why XMLHttpRequest and not fetch: the Fetch API cannot read file:// URLs in
  // Firefox at all — CVE-2019-11730 / MFSA 2019-21 ("Same-origin policy
  // treats all files in a directory as having the same-origin") closed the
  // "Fetch API can read files in these directories" hole by removing file:
  // URLs from fetch. Classic subresource reads were NOT removed:
  // security.fileuri.strict_origin_policy (default TRUE) lets a file://
  // document read files in the SAME DIRECTORY OR BELOW — the user's own
  // tmp/network_all.html proves a same-dir iframe loads in their Firefox.
  // Every expected path (data/story_glucose/..., data/..., rpg/data/...)
  // sits below the HTML's directory, so the direct read is permitted on
  // Firefox file:// and the page loads with ZERO clicks. Environments that
  // genuinely block local reads (Chrome file://) fail the direct read and
  // get the one-button folder pick — expected, never an error state,
  // never silent.
  // -------------------------------------------------------------------------
  function boot() {
    if (bootState.booted) return; // idempotent (EDITOR.init runs once, but
                                  // EDITOR.load.boot stays re-run-safe)
    bootState.booted = true;
    setProbeStatus("Looking for the data files in this folder…");
    if (typeof XMLHttpRequest === "undefined") {
      fallbackToPickPanel(
        "This browser exposes no XMLHttpRequest — using the folder picker " +
        "as the load path.");
      return;
    }
    // Never a dead "loading…" state: if the direct read has not settled
    // within 4 s (a hung handler), reveal the picker anyway.
    bootState.watchdog = window.setTimeout(function () {
      bootState.watchdog = null;
      if (!bootState.probeSettled) {
        revealPickPanel("The automatic check is taking unusually long — " +
                        "use the folder picker below instead of waiting.");
      }
    }, 4000);

    xhrText(MANIFEST_PATH, function (manifestText) {
      settleProbe();
      if (manifestText == null) {
        showFolderPickPanel(); // direct reads blocked here — expected in
        return;                // environments without the same-dir policy
      }
      // Direct read SUCCESS: auto-load the full set and complete (the
      // shared completion path — same as the pick path).
      setProbeStatus("Data files found — auto-loading…");
      var texts = {};
      texts[MANIFEST_PATH] = manifestText;
      var mres = parseManifest(manifestText);
      var fixed = EXPECTED.slice(1);
      var story = mres.error ? [] : storyPathsOf(mres.files);
      xhrMany(fixed.concat(story), function (rest) {
        mergeInto(texts, rest);
        completeFromTexts(texts, "direct");
      });
    });
  }

  function settleProbe() {
    bootState.probeSettled = true;
    if (bootState.watchdog) {
      window.clearTimeout(bootState.watchdog);
      bootState.watchdog = null;
    }
  }

  // The direct read missed: reveal the pick panel. Expected in
  // environments that block local reads (Chrome file://); on Firefox
  // file:// the same-dir-or-below policy normally makes this unreachable.
  // Never an error state, never silent.
  function showFolderPickPanel() {
    setProbeStatus("Direct reads are blocked here — use the folder " +
                   "picker below (one click).");
    revealPickPanel(null);
  }

  // Guard-path wrapper (no XMLHttpRequest): defined after boot so the
  // probe textually precedes every reference to the pick-panel reveal.
  function fallbackToPickPanel(reason) {
    setProbeStatus(reason);
    revealPickPanel(null);
  }

  // -------------------------------------------------------------------------
  // The folder pick: <input type="file" webkitdirectory multiple> — the
  // one-button FALLBACK for environments that truly block local reads
  // (e.g. Chrome file://). On Firefox file:// the direct read normally
  // succeeds and this is never needed.
  // -------------------------------------------------------------------------

  function mountFolderPick() {
    var mount = document.getElementById("boot-pick-mount");
    if (!mount) return;
    var wrap = document.createElement("div");
    wrap.id = "boot-pick-wrap";
    wrap.setAttribute("hidden", "hidden"); // revealed ONLY on probe rejection

    var note = document.createElement("p");
    note.id = "boot-pick-note";
    note.className = "boot-pick-note";

    var label = document.createElement("label");
    label.className = "boot-pick-label";
    label.setAttribute("for", "boot-folder-input");
    label.textContent = "Select your repository folder:";

    var input = document.createElement("input");
    input.type = "file";
    input.id = "boot-folder-input";
    input.setAttribute("webkitdirectory", "webkitdirectory");
    input.setAttribute("multiple", "multiple");
    input.addEventListener("change", onFolderPicked);

    wrap.appendChild(note);
    wrap.appendChild(label);
    wrap.appendChild(input);
    mount.appendChild(wrap);
  }

  function findByPath(path) {
    var index = bootState.pickedIndex || [];
    for (var i = 0; i < index.length; i++) {
      if (matchesSuffix(index[i].rel, path)) return index[i].file;
    }
    return null;
  }

  function onFolderPicked(ev) {
    var input = ev.target;
    var files = (input && input.files) ? input.files : null;
    // SNAPSHOT FIRST (07.1-11 fix — the "even upload not working at all"
    // defect): clearing the input's value (to allow re-picking the same
    // folder later) empties the selection, and in browsers where
    // input.files is a LIVE list the captured reference empties with it.
    // The original code cleared the input and THEN checked files.length —
    // which silently returned on Firefox, so the picked folder appeared
    // completely dead. Snapshot the File objects into a plain array
    // BEFORE the clear; the File objects themselves stay valid afterwards.
    var picked = [];
    if (files) {
      for (var j = 0; j < files.length; j++) picked.push(files[j]);
    }
    if (input) input.value = ""; // allow re-picking the same folder later
    if (!picked.length) return;
    // SECURITY (Pitfall 3c): the FileList contains the ENTIRE picked tree
    // including .git. We compare PATHS against the fixed expected list and
    // read ONLY matched files with FileReader — .git and sibling files are
    // never enumerated into reads. Unsafe path shapes are rejected outright.
    var index = [];
    var matched = 0;
    for (var i = 0; i < picked.length; i++) {
      var f = picked[i];
      var rel = (f && f.webkitRelativePath)
        ? f.webkitRelativePath
        : ((f && f.name) || "");
      if (pathIsUnsafe(rel)) continue;
      index.push({ rel: rel, file: f });
      if (matchesExpected(rel)) matched++;
    }
    bootState.pickedIndex = index;
    bootState.lastPickMatched = matched;
    pickFlow();
  }

  function pickFlow() {
    var manifestFile = findByPath(MANIFEST_PATH);
    if (!manifestFile) {
      // No manifest in the pick: the story files are unknown without it —
      // complete with everything missing (the checklist + blocker explain).
      completeFromTexts({}, "pick");
      return;
    }
    readText(manifestFile, function (manifestText) {
      var texts = {};
      texts[MANIFEST_PATH] = manifestText;
      var mres = parseManifest(manifestText);
      var fileMap = {};
      var wanted = [];
      var fixed = EXPECTED.slice(1);
      var fnames = mres.error ? [] : mres.files;
      var i;
      for (i = 0; i < fixed.length; i++) {
        var f = findByPath(fixed[i]);
        if (f) {
          fileMap[fixed[i]] = f;
          wanted.push(fixed[i]);
        }
      }
      for (var s = 0; s < fnames.length; s++) {
        var p = storyPathOf(fnames[s]);
        var sf = findByPath(p);
        if (sf) {
          fileMap[p] = sf;
          wanted.push(p);
        }
      }
      readMany(fileMap, wanted, function (readTexts) {
        mergeInto(texts, readTexts);
        completeFromTexts(texts, "pick");
      });
    });
  }

  // -------------------------------------------------------------------------
  // Draft reload: a single <input type="file" accept=".json,application/json">
  // restores a downloaded draft bundle (RESEARCH-UI Persistence step 4).
  // -------------------------------------------------------------------------

  function mountDraftInput() {
    var mount = document.getElementById("boot-draft-mount");
    if (!mount) return;
    var wrap = document.createElement("div");
    wrap.id = "boot-draft-wrap";

    var label = document.createElement("label");
    label.className = "boot-draft-label";
    label.setAttribute("for", "boot-draft-input");
    label.textContent = "Load draft…";

    var input = document.createElement("input");
    input.type = "file";
    input.id = "boot-draft-input";
    input.setAttribute("accept", ".json,application/json");
    input.addEventListener("change", onDraftPicked);

    var hint = document.createElement("span");
    hint.className = "boot-draft-hint";
    hint.textContent =
      " — restores a downloaded draft bundle (the save layer writes " +
      "story_editor_draft.json, meant for the repo's tmp/ folder); " +
      "self-contained, no folder re-pick needed.";

    wrap.appendChild(label);
    wrap.appendChild(input);
    wrap.appendChild(hint);
    mount.appendChild(wrap);
  }

  function onDraftPicked(ev) {
    var input = ev.target;
    var f = (input && input.files && input.files.length)
      ? input.files[0] : null;
    if (input) input.value = ""; // allow re-loading the same draft file
    if (!f) return;
    readText(f, function (text) {
      if (text == null) {
        banner("The draft file could not be read.", "error");
        return;
      }
      var draft;
      try {
        draft = JSON.parse(text);
      } catch (e) {
        banner("Draft is not valid JSON: " + describe(e), "error");
        return;
      }
      if (!draft || typeof draft !== "object" ||
          Object.prototype.toString.call(draft) === "[object Array]" ||
          !draft.bundle || typeof draft.bundle !== "object") {
        banner('Not a story-editor draft: expected an object with a ' +
               '"bundle" member (draft schema: {version, saved_at, bundle, ' +
               'dirty, undo_meta, fingerprints}).', "error");
        return;
      }
      loadDraft(draft, f.name || "draft file");
    });
  }

  function loadDraft(draft, srcName) {
    // The draft bundle IS the session (self-contained — "no folder re-pick
    // is needed"). setBundle resets undo/redo (a reloaded draft starts with
    // fresh undo history) and captures the draft bundle as the per-file
    // originals baseline.
    ED.setBundle(draft.bundle, null);
    // Restore the draft's own bookkeeping VERBATIM:
    // - fingerprints: per-file FNV-1a of the raw repo texts at draft-save
    //   time — the staleness baseline for the folder comparison below;
    // - dirty: the draft's per-file dirty set ("intact dirty-state",
    //   RESEARCH-UI step 4). undo_meta is acknowledged but intentionally
    //   unused here (fresh stacks).
    // NOTE for 07.1-13 (full stale-draft UX): EDITOR._originals now hold
    // the DRAFT bundle's snapshots, so recomputeDirty() re-derives against
    // the draft baseline; reconciling that with the repo files is 07.1-13's
    // job — this plan restores the bookkeeping and fires the hook below.
    if (draft.fingerprints && typeof draft.fingerprints === "object") {
      ED.state.fingerprints = copyOwn(draft.fingerprints);
    }
    if (draft.dirty && typeof draft.dirty === "object") {
      for (var k in draft.dirty) {
        if (Object.prototype.hasOwnProperty.call(draft.dirty, k)) {
          ED.state.dirty[k] = true;
        }
      }
    }
    bootState.draft = draft;
    bootState.draftActive = true;
    bootState.loaded = true;
    bootState.lastSource = "draft";

    var stale = compareDraftToFolderRaw();
    var msg = "Draft loaded from " + srcName +
      (draft.saved_at ? " (saved " + draft.saved_at + ")" : "") +
      (draft.version === 1 || draft.version == null
        ? ""
        : " — unknown draft version " + draft.version + " (loading anyway)");
    if (stale.length) {
      msg += " — WARNING: underlying files changed since this draft: " +
             stale.join(", ");
    }
    banner(msg, stale.length ? "warn" : "ok");
    setSummary("Loaded draft from " + srcName +
               (stale.length ? " — underlying files changed" : "") + ".");
    fireDraftLoaded({
      draft: draft,
      sourceName: srcName,
      staleFiles: stale,
      recheckedAgainstFolder: false
    });
    collapseBootPanel();
  }

  // Fingerprint comparison (drift DETECTOR, not security — 32-bit FNV-1a
  // per 00_core.js): the draft stores per-file fingerprints of the raw repo
  // texts as they were at draft-save time; the last COMPLETED folder pick
  // provides the current raw texts. Common keys are compared; keys without
  // a folder counterpart are simply not comparable. Returns the stale list.
  function compareDraftToFolderRaw() {
    var draft = bootState.draft;
    var folder = bootState.folderRawByFname;
    if (!draft || !draft.fingerprints || !folder) return [];
    var stale = [];
    for (var key in draft.fingerprints) {
      if (!Object.prototype.hasOwnProperty.call(draft.fingerprints, key)) {
        continue;
      }
      var raw = folder[key];
      if (typeof raw !== "string") continue; // not comparable
      if (ED.fnv1a(raw) !== draft.fingerprints[key]) {
        stale.push(key);
      }
    }
    return stale;
  }

  function fireDraftLoaded(info) {
    for (var i = 0; i < draftLoadedFns.length; i++) {
      try {
        draftLoadedFns[i](info);
      } catch (e) {
        editorWarn("EDITOR.load onDraftLoaded hook " + i + " failed: " +
                   describe(e));
      }
    }
  }

  // -------------------------------------------------------------------------
  // Asset-owned CSS (per-feature styling lives with its feature, never in
  // the shell — the shell carries structural layout ONLY).
  // -------------------------------------------------------------------------

  function injectLoadCss() {
    ED.injectCss(
      "/* owned by 10_load.js (07.1-07): boot panel states */\n" +
      "#boot-panel .boot-banner { margin: 6px 0 0; padding: 6px 10px; " +
      "border-radius: 4px; font-size: 13px; }\n" +
      "#boot-panel .boot-banner + .boot-banner { margin-top: 4px; }\n" +
      "#boot-panel .boot-banner-ok { background: #e7f4e7; " +
      "border: 1px solid #3d8b3d; color: #1e5c1e; }\n" +
      "#boot-panel .boot-banner-warn { background: #fdf3df; " +
      "border: 1px solid #b8860b; color: #7a5a00; }\n" +
      "#boot-panel .boot-banner-error { background: #fdeae6; " +
      "border: 1px solid #b5442d; color: #8a2f1d; }\n" +
      "#boot-panel .boot-head-row { display: flex; align-items: baseline; " +
      "gap: 10px; margin: 2px 0 4px; }\n" +
      "#boot-panel .boot-summary { font-size: 13px; color: #1e5c1e; }\n" +
      "#boot-panel .boot-toggle { font-size: 12px; padding: 2px 8px; }\n" +
      "#boot-panel .boot-row.boot-ok { color: #1e5c1e; }\n" +
      "#boot-panel .boot-row.boot-warn { color: #7a5a00; }\n" +
      "#boot-panel .boot-row.boot-block { color: #8a2f1d; }\n" +
      "#boot-panel .boot-pick-note { font-size: 12.5px; color: #555555; " +
      "margin: 4px 0; }\n" +
      "#boot-panel .boot-pick-label, #boot-panel .boot-draft-label " +
      "{ font-size: 13px; margin-right: 8px; }\n" +
      "#boot-panel .boot-draft-hint { font-size: 12px; color: #666666; " +
      "margin-left: 8px; }\n" +
      "#boot-panel.boot-loaded { background: #f7fbf7; }\n");
  }

  // -------------------------------------------------------------------------
  // Boot-panel chrome: banner box + the collapsible header row (summary +
  // toggle). The checklist STAYS available after load — collapsed behind
  // the toggle, one click away (plan: "stays visible (collapsible)").
  // -------------------------------------------------------------------------

  function mountChrome() {
    var panel = document.getElementById("boot-panel");
    if (!panel) return;
    var h2 = panel.getElementsByTagName("h2")[0] || null;

    // The static expected-layout copy is the over-engineered wall the user
    // rejected ("make it simple and no need to request this much work"):
    // the checklist rows already state every expected path, and the
    // fallback pick note says the one thing that matters. Hide it for
    // good (open-and-go: the panel shows one status line, nothing else).
    var help = document.getElementById("boot-help-copy");
    if (help) help.setAttribute("hidden", "hidden");

    var head = document.createElement("div");
    head.id = "boot-head-row";
    head.className = "boot-head-row";
    head.setAttribute("hidden", "hidden"); // shown once data is loaded
    var summary = document.createElement("span");
    summary.id = "boot-summary";
    summary.className = "boot-summary";
    var toggle = document.createElement("button");
    toggle.id = "boot-toggle";
    toggle.type = "button";
    toggle.className = "boot-toggle";
    toggle.addEventListener("click", function () {
      setCollapsed(!bootState.collapsed);
    });
    head.appendChild(summary);
    head.appendChild(toggle);
    if (h2 && h2.nextSibling) {
      panel.insertBefore(head, h2.nextSibling);
    } else {
      panel.insertBefore(head, panel.firstChild);
    }

    var banners = document.createElement("div");
    banners.id = "boot-banners";
    var probe = document.getElementById("boot-probe-status");
    if (probe && probe.nextSibling) {
      panel.insertBefore(banners, probe.nextSibling);
    } else {
      panel.appendChild(banners);
    }
  }

  // -------------------------------------------------------------------------
  // The EDITOR.load namespace — the surface later plans code against
  // (07.1-13 registers EDITOR.load.onDraftLoaded for the full stale-draft
  // UX; the structural tests pin the matcher/guards).
  // -------------------------------------------------------------------------

  ED.load = {
    version: "0.2.0", // 0.2.0 = the 07.1-11 direct-load rework (XHR primary)
    MANIFEST_PATH: MANIFEST_PATH,
    STORY_DIR_PREFIX: STORY_DIR_PREFIX,
    EXPECTED: EXPECTED,                    // the fixed expected-path list
    matchesExpected: matchesExpected,      // "/"-boundary suffix matcher
    matchesSuffix: matchesSuffix,
    pathIsUnsafe: pathIsUnsafe,            // ".." / drive letter / leading "/"
    severityFor: severityFor,              // "block" vs "warn" classification
    collectTopLevelKeys: collectTopLevelKeys,
    parseNoDupKeys: parseNoDupKeys,        // registry duplicate-key guard
    boot: boot,                            // the direct read (re-run-safe)
    // Draft-loaded hook point: fn({draft, sourceName, staleFiles,
    // recheckedAgainstFolder}) — 07.1-13 builds the full stale-draft UX on
    // this. Hooks fire defensively (one broken hook never breaks loading).
    onDraftLoaded: function (fn) {
      if (typeof fn === "function") draftLoadedFns.push(fn);
    },
    state: bootState
  };

  // -------------------------------------------------------------------------
  // Init: mount the chrome + inputs, then run the direct read (probe FIRST;
  // the pick panel is revealed only by the miss path).
  // -------------------------------------------------------------------------

  ED.init(function () {
    mountChrome();
    injectLoadCss();
    mountFolderPick();
    mountDraftInput();
    boot();
  });

})();
