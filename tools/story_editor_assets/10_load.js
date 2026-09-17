/* ==========================================================================
 * 10_load.js — the boot/load layer: DIRECT read on boot (open-and-go where
 * the environment permits) -> ONE-GESTURE fallback (drag the repo folder
 * onto the panel) -> checklist -> EDITOR.setBundle, plus the single-file
 * draft reload. Owner plan 07.1-07; direct-load rework = the 07.1-11
 * fix-forward; transport-policy correction + drag-and-drop fallback = the
 * 07.1-11 round-3 fix-forward (debug session
 * .planning/debug/story-editor-file-load.md); the one-click folder PICK
 * was REMOVED in the round-4 fix-forward (user verdict: drag-and-drop
 * works, "upload button not working ... maybe better remove the upload
 * button" — drag-and-drop covers BOTH Firefox and Chrome).
 *
 * FILE OWNERSHIP: this asset belongs to plan 07.1-07. It owns #boot-panel.
 * Never edit another plan's asset (00_core.js = 07.1-04, 05_json.js =
 * 07.1-05, 20_validate.js = 07.1-08, 30_graph.js = 07.1-06, ...); extend
 * the EDITOR namespace from your own file instead.
 *
 * THE BINDING USER DIRECTIVE (verbatim): Firefox + "detect sub-dir in the
 * same dir of the html ... try to make it simple and no need to request
 * this much work". The policy-verified model (v0.3.0):
 *
 *   1. DIRECT READ ON BOOT (zero clicks WHERE PERMITTED). The editor
 *      probes data/story_glucose/manifest.json and the rest of the
 *      expected set off the disk and renders the graph immediately — the
 *      green "Data auto-detected in sub-directories" banner. All expected
 *      paths sit BELOW the HTML's own directory (data/... and
 *      rpg/data/... under the repo root).
 *   2. TRANSPORT + POLICY RECORD (07.1-11, CORRECTED round 3). The
 *      original layer probed with the Fetch API; the Fetch API cannot
 *      read file:// URLs in Firefox at all (CVE-2019-11730 / MFSA 2019-21
 *      removed file: URLs from fetch — "The Fetch API can then be used
 *      to read the contents of any files stored in these directories"
 *      named the closed hole). 07.1-11 then moved the probe to
 *      XMLHttpRequest on the premise that
 *      security.fileuri.strict_origin_policy (default true) still lets a
 *      file:// document read files in the same directory or below.
 *      ROUND-3 EMPIRICAL CORRECTION (verified 2026-09-15 ON THE USER'S
 *      OWN Firefox 155.0.1, fresh default profile AND their real profile
 *      — their prefs carry no fileuri override — via headless sync-XHR
 *      and iframe probes, see the debug session):
 *        - With strict_origin_policy at its DEFAULT (true), a file://
 *          page permits NO programmatic file reads at all: sync XHR
 *          throws NetworkError on EXISTING same-dir, subdir and 2-level
 *          files exactly as on missing files; iframe documents still
 *          DISPLAY (the user's tmp/network_all.html same-dir iframe
 *          "proof" was display-only — it never read content) but
 *          iframe.contentDocument is null even same-dir; fetch remains
 *          unusable (the CVE fix). The old "same directory or below"
 *          permission window for READS is closed in current Firefox.
 *        - strict_origin_policy = false DOES restore the classic
 *          behavior (verified: sync XHR status 200 with content,
 *          subdir/2-level iframe DOMs readable) — but flipping a global
 *          security pref is NOT a load path we ask of users.
 *        - privacy.file_unique_origin is irrelevant here (verified).
 *        - Chrome blocks file:// XHR by design; only
 *          --allow-file-access-from-files relaxes it (verified: the
 *          whole auto-load flow then works end-to-end on the real page).
 *      CONSEQUENCE: zero-click auto-load exists only where reads are
 *      permitted — serving the repo over http(s), Chrome with
 *      --allow-file-access-from-files, or a pref flip. On stock
 *      Firefox/Chrome double-click, the probe misses in milliseconds and
 *      the ONE-GESTURE panel below is the path. The XHR transport stays:
 *      it is exactly right wherever reads ARE permitted, costs nothing
 *      where they are not, and the watchdog still guards hangs.
 *   3. ONE GESTURE FALLBACK (the default on stock browsers). On a probe
 *      miss the editor reveals ONE panel with ONE gesture:
 *        DRAG-AND-DROP: drag the repository folder (or any parent of it)
 *        onto the drop zone. DataTransferItem.webkitGetAsEntry()
 *        recursion builds the relative-path index (readEntries returns
 *        BATCHES — it is re-called until an empty batch). File objects
 *        are fetched ONLY for the WANTED paths via entry.file() — the
 *        whole dropped tree (.git included) is enumerated by NAME only,
 *        never materialized or read. The "/"-boundary suffix matcher
 *        treats entry.fullPath exactly like a pick's
 *        File.webkitRelativePath (a dropped parent of the repo works; a
 *        child folder matches nothing by design — the checklist then
 *        says "select the repository root"). A document-level
 *        dragover/drop canceler keeps a stray drop from navigating the
 *        page away. (The one-click directory-select file INPUT — the
 *        OTHER half of this fallback in v0.3.0 — was REMOVED
 *        in the round-4 fix-forward: user-verified dead in their real
 *        browser after three repair rounds, and drag-and-drop covers the
 *        same ground in both Firefox and Chrome; the round-2
 *        snapshot-before-clear fix rides with it.)
 *   4. FOUND/MISSING CHECKLIST. One row per expected path with ✓/✗ and the
 *      friendly hint; the story-file rows are derived FROM the loaded
 *      manifest (manifest.files — never hard-listed before it loads).
 *      Required files missing: the editor blocks; citations/sources/cast
 *      degrade with warnings. The checklist stays available (collapsible)
 *      after load.
 *   5. DRAFT RELOAD. A single <input type="file" accept=".json,...">
 *      restores a downloaded draft bundle {version, saved_at, bundle,
 *      dirty, undo_meta, fingerprints} via EDITOR.setBundle —
 *      self-contained, no folder re-pick needed. When dropped-folder raw
 *      texts are also available, the draft's stored per-file fingerprints
 *      are compared against them (32-bit FNV-1a — a drift DETECTOR, not
 *      security) and a mismatch warns "underlying files changed since
 *      this draft". The full stale-draft UX lives in 07.1-13's save
 *      layer; this asset provides the load + the
 *      EDITOR.load.onDraftLoaded hook point.
 *
 * SECURITY GUARDS (Pitfall 3c): a dropped/picked folder hands the editor
 * the ENTIRE tree including .git — paths are filtered against the fixed
 * expected list and only matched files are read; any path that contains
 * "..", a drive letter, or a leading "/" is rejected outright. .git and
 * sibling files are never enumerated into reads.
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
    pickedIndex: null,    // last drop: [{rel, file}] or [{rel, entry}]
    pickSource: null,     // "drop" — the gesture that built the index
                          // (the one-click "pick" was REMOVED round 4)
    lastPickMatched: 0,   // how many of the 5 expected paths the drop matched
    folderRawByFname: null, // last DROP-completed {fname: rawText} — the
                            // fingerprint baseline for draft staleness
    draft: null,          // the active draft object (if any)
    draftActive: false,   // the session bundle came from a draft file
    loaded: false,        // a bundle reached EDITOR.setBundle
    collapsed: false,     // boot panel details collapsed (after load)
    lastSource: null      // "direct" | "drop" | "draft"
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
  // Manifest parsing (shared by the direct-read path and the drop path).
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
  // FileReader helpers (the drop path) — ES5 callbacks, no async/await.
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
      "Automatic folder reads are blocked by default in current Firefox " +
      "and Chrome — that is expected for a locally opened page. One " +
      "gesture loads everything: drag the repository root folder (or any " +
      "parent of it) onto the zone below; the editor matches the " +
      "expected data paths itself.");
  }

  // Reveals the fallback panel (idempotent). Called ONLY after the
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
    return "expected under the folder you dropped; did you " +
           "select the repository root?";
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
    if (source === "drop" && bootState.lastPickMatched === 0) {
      extra = " No expected file matched the dropped folder — a " +
              "sub-folder (like data/) matches nothing by design: " +
              "select the repository root.";
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
      // the drop zone is the universal self-service fix, reveal it too.
      revealPickPanel("Some data files are missing or unreadable from " +
                      "this location — drag the repository folder onto " +
                      "the zone below instead.");
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
    if (source === "drop") {
      // The fresh folder texts become the fingerprint baseline for the
      // draft staleness comparison.
      bootState.folderRawByFname = rawByFname;
    }

    if (bootState.draftActive && source === "drop") {
      // A draft session is active: the re-drop must NOT silently discard it
      // (RESEARCH-UI step 4 — "if the folder is also re-picked, fingerprint
      // comparison warns"). Refresh the baseline, compare, warn; reload the
      // page to start over from the dropped folder instead.
      var stale = compareDraftToFolderRaw();
      var items = [{
        text: "Folder dropped — still showing the loaded draft. Reload " +
              "the page to start from the dropped folder instead.",
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
      msg = "Data loaded from the dropped folder";
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
                 : "the dropped folder") +
               (warnings.length
                  ? " — " + warnings.length + " warning(s)"
                  : "") + ".");
    collapseBootPanel();
  }

  // -------------------------------------------------------------------------
  // BOOT SEQUENCE — direct read FIRST (open-and-go where permitted), the
  // one-gesture panel only on a real miss.
  //
  // Why XMLHttpRequest and not fetch: the Fetch API cannot read file:// URLs
  // in Firefox at all — CVE-2019-11730 / MFSA 2019-21 ("Same-origin policy
  // treats all files in a directory as having the same-origin") closed the
  // "Fetch API can read files in these directories" hole by removing file:
  // URLs from fetch. XHR is the remaining classic transport; whether it
  // actually READS a file:// subresource depends on the policy era:
  // ROUND-3 verification on the user's own Firefox 155.0.1 (defaults) shows
  // the legacy same-directory-or-below read window is CLOSED by default
  // (security.fileuri.strict_origin_policy=true now denies EVERY file://
  // XHR — sync probes thrown NetworkError on existing files — and hides
  // iframe DOMs). So on stock Firefox/Chrome double-click the probe misses
  // in milliseconds and the drag-and-drop panel takes over — expected,
  // never an error state, never silent. Where reads ARE
  // permitted (http(s) serving, Chrome --allow-file-access-from-files —
  // verified end-to-end — or a strict_origin_policy=false flip), the
  // direct read succeeds with ZERO clicks and the green banner.
  // -------------------------------------------------------------------------
  function boot() {
    if (bootState.booted) return; // idempotent (EDITOR.init runs once, but
                                  // EDITOR.load.boot stays re-run-safe)
    bootState.booted = true;
    setProbeStatus("Looking for the data files in this folder…");
    if (typeof XMLHttpRequest === "undefined") {
      fallbackToPickPanel(
        "This browser exposes no XMLHttpRequest — using the drag-and-drop " +
        "zone as the load path.");
      return;
    }
    // Never a dead "loading…" state: if the direct read has not settled
    // within 4 s (a hung handler), reveal the fallback anyway.
    bootState.watchdog = window.setTimeout(function () {
      bootState.watchdog = null;
      if (!bootState.probeSettled) {
        revealPickPanel("The automatic check is taking unusually long — " +
                        "drag the repository folder onto the zone below " +
                        "instead of waiting.");
      }
    }, 4000);

    xhrText(MANIFEST_PATH, function (manifestText) {
      settleProbe();
      if (manifestText == null) {
        showFolderPickPanel(); // direct reads blocked here — the expected
        return;                // path on stock browsers
      }
      // Direct read SUCCESS: auto-load the full set and complete (the
      // shared completion path — same as the drop path).
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

  // The direct read missed: reveal the one-gesture panel (the
  // drag-and-drop zone). THE expected path on stock Firefox/Chrome
  // double-click (file:// reads are blocked by default in both — see the
  // header record). Never an error state, never silent.
  function showFolderPickPanel() {
    setProbeStatus("Direct reads are blocked here — drag the repository " +
                   "folder onto the zone below (one gesture).");
    revealPickPanel(null);
  }

  // Guard-path wrapper (no XMLHttpRequest): defined after boot so the
  // probe textually precedes every reference to the panel reveal.
  function fallbackToPickPanel(reason) {
    setProbeStatus(reason);
    revealPickPanel(null);
  }

  // -------------------------------------------------------------------------
  // The fallback panel wrap (#boot-pick-wrap): the note + the drag-and-drop
  // zone (mounted into it by mountDropZone below). THE expected path on
  // stock Firefox AND Chrome file:// — both block programmatic reads by
  // default (see the header record). The one-click folder PICK input
  // (a directory-select file input) used to live here — REMOVED in
  // the round-4 fix-forward per the user verdict ("upload button not
  // working... maybe better remove the upload button"): user-verified dead
  // in their real browser across three repair rounds while drag-and-drop
  // loads the same tree in both Firefox and Chrome.
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

    wrap.appendChild(note);
    mount.appendChild(wrap);
  }

  function findItem(path) {
    var index = bootState.pickedIndex || [];
    for (var i = 0; i < index.length; i++) {
      if (matchesSuffix(index[i].rel, path)) return index[i];
    }
    return null;
  }

  // An index item carries EITHER file (a File from the picker / a flat
  // drop) OR entry (a FileSystemFileEntry from a folder drop). getFileAt
  // normalizes both to a File via cb — entry.file() is async and is the
  // ONLY place File objects are fetched for dropped entries (File objects
  // are fetched ONLY for the WANTED paths, never for the whole tree).
  function getFileAt(item, cb) {
    if (!item) {
      cb(null);
      return;
    }
    if (item.file) {
      cb(item.file);
      return;
    }
    try {
      item.entry.file(function (f) { cb(f); }, function () { cb(null); });
    } catch (e) {
      cb(null);
    }
  }

  // Resolves wanted index items to {expectedPath: File} (null-tolerant:
  // an unresolvable entry simply lands in the map as null-derived and the
  // checklist reports the miss).
  function materializeFiles(items, cb) {
    var out = {};
    var pending = items.length;
    if (!pending) {
      cb(out);
      return;
    }
    for (var i = 0; i < items.length; i++) {
      (function (it) {
        getFileAt(it.item, function (f) {
          if (f) out[it.path] = f;
          pending--;
          if (pending === 0) cb(out);
        });
      })(items[i]);
    }
  }

  // The shared completion flow: resolve the manifest, derive the story
  // paths from it, materialize File objects for the WANTED paths only,
  // read them, and hand the texts to completeFromTexts.
  // bootState.pickSource ("drop") drives the user-facing wording.
  function pickFlow() {
    var source = bootState.pickSource || "drop";
    var manifestItem = findItem(MANIFEST_PATH);
    if (!manifestItem) {
      // No manifest in the gesture: the story files are unknown without
      // it — complete with everything missing (the checklist + blocker
      // explain).
      completeFromTexts({}, source);
      return;
    }
    getFileAt(manifestItem, function (manifestFile) {
      if (!manifestFile) {
        completeFromTexts({}, source);
        return;
      }
      readText(manifestFile, function (manifestText) {
        var texts = {};
        texts[MANIFEST_PATH] = manifestText;
        var mres = parseManifest(manifestText);
        var wanted = [];        // expected paths in the map
        var wantedItems = [];   // [{path, item}]
        var fixed = EXPECTED.slice(1);
        var fnames = mres.error ? [] : mres.files;
        var i;
        for (i = 0; i < fixed.length; i++) {
          var f = findItem(fixed[i]);
          if (f) {
            wanted.push(fixed[i]);
            wantedItems.push({ path: fixed[i], item: f });
          }
        }
        for (var s = 0; s < fnames.length; s++) {
          var p = storyPathOf(fnames[s]);
          var sf = findItem(p);
          if (sf) {
            wanted.push(p);
            wantedItems.push({ path: p, item: sf });
          }
        }
        materializeFiles(wantedItems, function (fileMap) {
          readMany(fileMap, wanted, function (readTexts) {
            mergeInto(texts, readTexts);
            completeFromTexts(texts, source);
          });
        });
      });
    });
  }

  // -------------------------------------------------------------------------
  // DRAG-AND-DROP folder load (the ONE-GESTURE fallback, works on file://
  // in BOTH current Firefox and Chrome — the gesture grants the access, no
  // policy involved). The drop hands us DataTransferItems; each folder
  // item's webkitGetAsEntry() yields a FileSystemDirectoryEntry that is
  // walked recursively. readEntries returns BATCHES (typically <= 100) and
  // MUST be re-called until an empty batch before the directory counts as
  // drained. Only the NAMES travel the tree; File objects are fetched
  // ONLY for the WANTED paths later (getFileAt) — .git and every
  // unrelated file are enumerated by name only, never materialized or
  // read (the same Pitfall 3c discipline as the pick).
  // -------------------------------------------------------------------------

  function mountDropZone() {
    var wrap = document.getElementById("boot-pick-wrap");
    if (!wrap) return;
    var zone = document.createElement("div");
    zone.id = "boot-drop-zone";
    zone.className = "boot-drop-zone";
    zone.textContent = "Drag your repository folder here";
    zone.addEventListener("dragover", function (ev) {
      ev.preventDefault(); // mark the zone as a drop target
      zone.classList.add("boot-drop-hot");
    });
    zone.addEventListener("dragleave", function () {
      zone.classList.remove("boot-drop-hot");
    });
    zone.addEventListener("drop", onDrop);
    wrap.insertBefore(zone, wrap.firstChild.nextSibling); // after the note
  }

  // rel path for a dropped entry: entry.fullPath begins with "/" and
  // carries the dropped folder's own name as its first segment
  // ("/RPG_tale-of-C/data/..."). Stripping the leading "/" yields exactly
  // the same shape as File.webkitRelativePath, so matchesSuffix treats a
  // dropped parent-of-repo just like a picked one.
  function relOfEntry(entry) {
    var p = String(entry.fullPath || entry.name || "");
    return p.charAt(0) === "/" ? p.slice(1) : p;
  }

  // Recursive walker. pending counts undrained directories; done fires
  // when every directory has been fully read. The batch rule is the
  // load-bearing detail: readEntries returns BATCHES — re-call until an
  // empty batch (a single call silently truncates big folders).
  function traverseEntry(entry, index, pending, done) {
    if (entry.isFile) {
      var rel = relOfEntry(entry);
      if (pathIsUnsafe(rel)) return; // same guards as the pick path
      index.push({ rel: rel, entry: entry });
      return;
    }
    if (!entry.isDirectory) return;
    pending.count++;
    var reader = entry.createReader();
    var readBatch = function () {
      reader.readEntries(function (batch) {
        if (!batch || !batch.length) {
          pending.count--;
          if (pending.count === 0) done();
          return;
        }
        for (var i = 0; i < batch.length; i++) {
          traverseEntry(batch[i], index, pending, done);
        }
        readBatch(); // drain the NEXT batch (BATCHES rule above)
      }, function () {
        // An unreadable directory behaves like an empty one — never hang.
        pending.count--;
        if (pending.count === 0) done();
      });
    };
    readBatch();
  }

  function onDrop(ev) {
    ev.preventDefault();
    var zone = document.getElementById("boot-drop-zone");
    if (zone) zone.classList.remove("boot-drop-hot");
    var dt = ev.dataTransfer;
    var items = (dt && dt.items) ? dt.items : null;
    var entries = [];
    if (items) {
      for (var i = 0; i < items.length; i++) {
        var ent = null;
        try {
          ent = items[i].webkitGetAsEntry
            ? items[i].webkitGetAsEntry() : null;
        } catch (e) {
          ent = null;
        }
        if (ent) entries.push(ent);
      }
    }
    if (entries.length) {
      // Entry path: recursive NAME-ONLY traversal; File objects come
      // later, for wanted paths only. pending is a GLOBAL counter: every
      // directory +1 once and -1 once (on its empty/error batch); done
      // fires exactly once when the count returns to 0 — i.e. when EVERY
      // dropped directory has drained. readEntries callbacks are always
      // deferred, so the synchronous top-level loop finishes counting #
      // dirs before any drain can decrement.
      var index = [];
      var pending = { count: 0 };
      var done = function () {
        var matched = 0;
        for (var k = 0; k < index.length; k++) {
          if (matchesExpected(index[k].rel)) matched++;
        }
        bootState.pickedIndex = index;
        bootState.pickSource = "drop";
        bootState.lastPickMatched = matched;
        pickFlow();
      };
      var anyDir = false;
      for (var t = 0; t < entries.length; t++) {
        if (entries[t].isDirectory) anyDir = true;
        traverseEntry(entries[t], index, pending, done);
      }
      // All top-level entries were plain files (nothing async pending):
      // finalize synchronously — done only ever fires from a dir drain.
      if (!anyDir) done();
      return;
    }
    // No entry API (rare): flat fallback — treat dt.files exactly like a
    // pick (root-level files only; a folder drop will match nothing and
    // the checklist says to select the repository root).
    var picked = [];
    var flat = (dt && dt.files) ? dt.files : null;
    if (flat) {
      for (var j = 0; j < flat.length; j++) picked.push(flat[j]);
    }
    if (!picked.length) return;
    var index2 = [];
    var matched2 = 0;
    for (var m = 0; m < picked.length; m++) {
      var fl = picked[m];
      var rel2 = (fl && fl.webkitRelativePath)
        ? fl.webkitRelativePath
        : ((fl && fl.name) || "");
      if (pathIsUnsafe(rel2)) continue;
      index2.push({ rel: rel2, file: fl });
      if (matchesExpected(rel2)) matched2++;
    }
    bootState.pickedIndex = index2;
    bootState.pickSource = "drop";
    bootState.lastPickMatched = matched2;
    pickFlow();
  }

  // A stray drop anywhere OUTSIDE the zone must NOT navigate the page
  // away (browsers open dropped files by default — losing the editor).
  function installGlobalDropGuard() {
    function cancel(ev) {
      ev.preventDefault();
    }
    document.addEventListener("dragover", cancel, false);
    document.addEventListener("drop", cancel, false);
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
      "#boot-panel .boot-drop-zone { margin: 8px 0 10px; padding: 18px " +
      "14px; border: 2px dashed #6b7690; border-radius: 6px; " +
      "background: #f4f7fd; color: #31405e; font-size: 14px; " +
      "text-align: center; }\n" +
      "#boot-panel .boot-drop-zone.boot-drop-hot { border-color: " +
      "#2e6b2e; background: #e7f4e7; color: #1e5c1e; }\n" +
      "#boot-panel .boot-draft-label { font-size: 13px; " +
      "margin-right: 8px; }\n" +
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
    version: "0.4.0", // 0.4.0 = round-4: the one-click folder PICK removed per the user verdict (drag-and-drop is the one gesture); probe + drop unchanged
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
  // the fallback panel is revealed only by the miss path).
  // -------------------------------------------------------------------------

  ED.init(function () {
    mountChrome();
    injectLoadCss();
    mountFolderPick();
    mountDropZone();
    installGlobalDropGuard();
    mountDraftInput();
    boot();
  });

})();
