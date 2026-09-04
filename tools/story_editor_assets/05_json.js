/* =========================================================================
 * 05_json.js -- EDITOR.housy: the house-style JSON serializer (JS port).
 * =========================================================================
 * Owner:   plan 07.1-05 (Phase 7.1 story-node editor, asset wave 2).
 * Spec:    tools/story_editor_json.py (plan 07.1-02) -- the CANONICAL
 *          house-style JSON serializer. This file is a mechanical 1:1 port:
 *          same rule family, same constants, same fixture vectors.
 * Loaded:  after 00_core.js, before all view assets (sorted auto-inline).
 *
 * Constants (identical to the Python module):
 *   W  = 175  container inline width -- a dict may render on one line iff
 *             indent + len(compact) <= W (plus the propagation rules below)
 *   SW = 110  scalar-list inline width -- a scalar-only list renders inline
 *             iff indent + len(compact) <= SW
 *   EDITS_FORCE_KEY = "edits"
 *             array elements stored under the key "edits" are ALWAYS
 *             rendered multiline (the hand style edits.json was authored
 *             in; the flag is single-level -- it applies to the DIRECT
 *             elements of that array only, exactly like Python's ser_keyed).
 *
 * Rule family (R1..R7, pinned by tests/test_story_editor_json.py and the
 * 12-file byte-identical no-op oracle of 07.1-02):
 *   R1 2-space indent; stringify() returns WITHOUT a trailing newline (the
 *      save path appends it).
 *   R2 floats: plain JS numbers emit String(n) (shortest round-trip, like
 *      Python repr); RawFloat wrappers emit their token verbatim.
 *   R3 scalar lists inline iff indent + compact <= SW, else one per line.
 *   R4 container arrays (any dict/list element) are ALWAYS multiline; each
 *      element is inlined iff it fits (R5) at array_indent + 2.
 *   R5 dict inline iff indent + compact <= W AND no container-array child
 *      AND every descendant container fits at its own depth (+2
 *      propagation). Multiline dicts render children at +2 and close the
 *      brace at the parent indent.
 *   R6 the "edits" exception (see EDITS_FORCE_KEY above).
 *   R7 empty containers {} and [] are always inline, at any depth.
 *
 * String escaping: JSON.stringify(s) is used for strings and keys. For the
 * writable-file character set this is EQUIVALENT to the canonical Python
 * json.dumps(s, ensure_ascii=False): both escape backslash, double quote
 * and the C0 controls (same short forms for \b \t \n \f \r, lowercase
 * \u00xx otherwise) and both keep non-ASCII (em-dashes etc.) literal UTF-8.
 *
 * KNOWN LIMITATION (documented, by design -- see 07.1-02): raw float-token
 * preservation ("2.40" stays "2.40") is recoverable on the Python side via
 * json.loads(parse_float=RawFloat). JS JSON.parse has no parse_float hook,
 * so a parsed 2.40 arrives as the number 2.4 and the trailing zero is gone
 * BEFORE this serializer ever sees it. The writable targets (story files,
 * rpg/data/edits.json, rpg/data/cast.json) contain NO float literals at
 * all (0.5-style weights would round-trip fine); the only float-bearing
 * files, data/citations.json + data/sources.json, are READ-ONLY in this
 * editor, so their resolution_angstrom tokens are never re-serialized.
 * Editor code that must emit an exact float token can wrap it explicitly:
 * EDITOR.housy.rawFloat("2.40") stringifies as 2.40.
 *
 * Key order: JS objects preserve string-key insertion order (ES2015+),
 * which is what the data relies on. Integer-like keys would be reordered
 * by the engine -- none exist in the data; the canonical Python side
 * (OrderedDict) would keep them, so do not introduce numeric keys.
 *
 * Non-finite numbers (NaN / Infinity) cannot appear in parsed JSON and
 * would corrupt a save; scalar_str throws on them (the Python canonical
 * would emit invalid-JSON tokens -- unreachable from a real save either
 * way; this port fails loud instead).
 * ========================================================================= */

(function () {
  "use strict";

  /* window.EDITOR is created by 00_core.js (inlined first). Defensive
   * fallback: if the core asset ever fails to load, this serializer must
   * still be reachable and the boot canary below must not crash the page. */
  var EDITOR = window.EDITOR;
  if (!EDITOR) {
    EDITOR = window.EDITOR = {};
  }

  var W = 175;            /* container inline width (R5) */
  var SW = 110;           /* scalar-list inline width (R3) */
  var EDITS_FORCE_KEY = "edits";  /* R6: hand-style exception key */

  /* ------------------------------------------------------------------ *
   * RawFloat -- a JSON float token preserved verbatim ("2.40" -> 2.40).  *
   * Python-side this wrapper is also installed by loads(); in JS it is   *
   * opt-in for editor code (JSON.parse cannot be taught token recovery). *
   * ------------------------------------------------------------------ */
  function RawFloat(token) {
    this.token = String(token);
  }

  function isRawFloat(v) {
    return v instanceof RawFloat;
  }

  /* A container is a plain object or an array (RawFloat is a scalar). */
  function isContainer(v) {
    if (v === null || typeof v !== "object") {
      return false;
    }
    return !isRawFloat(v);
  }

  function ownKeys(v) {
    var keys = [];
    for (var k in v) {
      if (Object.prototype.hasOwnProperty.call(v, k)) {
        keys.push(k);
      }
    }
    return keys;
  }

  function repeat(s, n) {
    var out = "";
    for (var i = 0; i < n; i++) {
      out += s;
    }
    return out;
  }

  /* R2 -- render a scalar exactly as the house style does. */
  function scalarStr(v) {
    if (isRawFloat(v)) {
      return v.token;
    }
    if (typeof v === "boolean") {
      return v ? "true" : "false";
    }
    if (v === null) {
      return "null";
    }
    if (typeof v === "number") {
      if (!isFinite(v)) {
        throw new Error(
          "housy.stringify: non-finite number cannot be serialized (value " +
          String(v) + ")");
      }
      return String(v); /* shortest round-trip, same as Python repr(float) */
    }
    if (typeof v === "string") {
      return JSON.stringify(v);
    }
    throw new Error(
      "housy.stringify: unsupported scalar type: " + typeof v +
      " (undefined values must never reach the serializer)");
  }

  /* The one-line form: {"a": 1, "b": [2, 3]} / [1, 2] (", " + ": " sep). */
  function compact(v) {
    if (Array.isArray(v)) {
      var parts = [];
      for (var i = 0; i < v.length; i++) {
        parts.push(compact(v[i]));
      }
      return "[" + parts.join(", ") + "]";
    }
    if (isContainer(v)) {
      var kv = [];
      var keys = ownKeys(v);
      for (var j = 0; j < keys.length; j++) {
        kv.push(JSON.stringify(keys[j]) + ": " + compact(v[keys[j]]));
      }
      return "{" + kv.join(", ") + "}";
    }
    return scalarStr(v);
  }

  /* R3 shape: a list with NO dict/list elements. */
  function isScalarList(v) {
    for (var i = 0; i < v.length; i++) {
      if (isContainer(v[i])) {
        return false;
      }
    }
    return true;
  }

  /* R3 + R7: a list may inline iff scalar-only and it fits within SW. */
  function fitsList(v, indent) {
    if (v.length === 0) {
      return true; /* empty containers are always inline (R7) */
    }
    if (isScalarList(v)) {
      return indent + compact(v).length <= SW;
    }
    return false; /* container arrays are always multiline (R4) */
  }

  /* R5 + R7: a dict may inline iff it fits within W, holds no
   * container-array child, and every descendant container fits at its own
   * depth (propagation). */
  function fitsDict(v, indent) {
    var keys = ownKeys(v);
    if (keys.length === 0) {
      return true; /* empty containers are always inline (R7) */
    }
    if (indent + compact(v).length > W) {
      return false;
    }
    for (var i = 0; i < keys.length; i++) {
      var cv = v[keys[i]];
      if (Array.isArray(cv) && !isScalarList(cv)) {
        return false; /* container-array child forbids inline (R5) */
      }
    }
    return descendantsFit(v, indent);
  }

  /* R5 propagation: children sit at indent + 2 if this dict broke, so each
   * descendant container must fit at ITS own depth. */
  function descendantsFit(v, indent) {
    var keys = ownKeys(v);
    for (var i = 0; i < keys.length; i++) {
      var cv = v[keys[i]];
      if (isContainer(cv)) {
        if (Array.isArray(cv)) {
          if (!fitsList(cv, indent + 2)) {
            return false;
          }
        } else if (!fitsDict(cv, indent + 2)) {
          return false;
        }
      }
    }
    return true;
  }

  /* R6 -- render a dict child under the given key: sets the edits force
   * flag. */
  function serKeyed(v, indent, key) {
    var force = (key === EDITS_FORCE_KEY && Array.isArray(v));
    return ser(v, indent, force);
  }

  /* Render a value at the given indent. The force flag marks this value as
   * a direct
   * array element under the "edits" key (R6): a dict so flagged renders
   * multiline even when it fits. Empty containers stay inline regardless
   * (R7). */
  function ser(v, indent, force) {
    var pad = repeat(" ", indent);
    if (isContainer(v)) {
      if (Array.isArray(v)) {
        if (v.length === 0) {
          return "[]";
        }
        if (isScalarList(v)) {
          if (indent + compact(v).length <= SW) {
            return compact(v);
          }
          return serScalarListMultiline(v, indent);
        }
        /* Container array: ALWAYS multiline (R4); elements inherit the
         * force flag (they are the direct "edits" elements when set). */
        var lines = ["["];
        for (var i = 0; i < v.length; i++) {
          var piece = pad + "  " + ser(v[i], indent + 2, force);
          if (i < v.length - 1) {
            piece += ",";
          }
          lines.push(piece);
        }
        lines.push(pad + "]");
        return lines.join("\n");
      }
      /* dict */
      var keys = ownKeys(v);
      if (keys.length === 0) {
        return "{}";
      }
      if (!force && fitsDict(v, indent)) {
        return compact(v);
      }
      return serDictMultiline(v, indent);
    }
    return scalarStr(v);
  }

  /* R5 multiline dict: children at +2, close brace at the parent indent. */
  function serDictMultiline(v, indent) {
    var pad = repeat(" ", indent);
    var childIndent = indent + 2;
    var lines = ["{"];
    var keys = ownKeys(v);
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      var piece = repeat(" ", childIndent) + JSON.stringify(k) + ": ";
      piece += serKeyed(v[k], childIndent, k);
      if (i < keys.length - 1) {
        piece += ",";
      }
      lines.push(piece);
    }
    lines.push(pad + "}");
    return lines.join("\n");
  }

  /* R3 multiline scalar list: one element per line at +2. */
  function serScalarListMultiline(v, indent) {
    var pad = repeat(" ", indent);
    var lines = ["["];
    for (var i = 0; i < v.length; i++) {
      var piece = pad + "  " + scalarStr(v[i]);
      if (i < v.length - 1) {
        piece += ",";
      }
      lines.push(piece);
    }
    lines.push(pad + "]");
    return lines.join("\n");
  }

  /* House-style serializer. Returns WITHOUT a trailing newline -- the save
   * path appends it (R1; the no-op-save oracle is
   * stringify(parsed(raw)) + "\n" === raw). 07.1-13's save path must call
   * EDITOR.housy.stringify -- never the naive pretty-printer (the
   * two-argument space-indented JSON.stringify form) directly. */
  function stringify(obj) {
    return ser(obj, 0, false);
  }

  var housy = {
    stringify: stringify,
    RawFloat: RawFloat,
    rawFloat: function (token) { return new RawFloat(token); },
    W: W,
    SW: SW,
    EDITS_FORCE_KEY: EDITS_FORCE_KEY
  };
  EDITOR.housy = housy;

  /* ==================================================================== *
   * SELFTEST_VECTORS -- the shared spec table.                           *
   *                                                                      *
   * These are the SAME 11 (name, object, expected) triples as the        *
   * canonical Python fixture_vectors() in tools/story_editor_json.py,    *
   * mirrored verbatim from the GROUND_TRUTH table in                     *
   * tests/test_story_editor_json.py (which 07.1-02 pinned against the    *
   * module outputs). The expected strings are embedded as ES5            *
   * double-quoted string constants (the same escaping Python uses, since *
   * both share the JSON escape subset);                                  *
   * tests/test_story_editor_serializer_js.py decodes them and pins them  *
   * equal to fixture_vectors() -- mechanical WSL-side parity. Runtime    *
   * equivalence is proven right here by selfTestSerializer() at boot.    *
   * ==================================================================== */
  var SELFTEST_VECTORS = [
    {
      name: "inline_scalar_list",
      input: {
        claim_ids: ["GLY-INTRO-01"],
        tags: ["stage:glycolysis"],
        on_enter: [{ op: "hide_all" }]
      },
      expected: "{\n" +
        "  \"claim_ids\": [\"GLY-INTRO-01\"],\n" +
        "  \"tags\": [\"stage:glycolysis\"],\n" +
        "  \"on_enter\": [\n" +
        "    {\"op\": \"hide_all\"}\n" +
        "  ]\n" +
        "}"
    },
    {
      name: "multiline_long_scalar_list",
      input: {
        files: ["intro.json", "glycolysis.json", "pyruvate_branch.json",
          "tca.json", "etc_atp.json", "endings.json", "bad_endings.json"]
      },
      expected: "{\n" +
        "  \"files\": [\n" +
        "    \"intro.json\",\n" +
        "    \"glycolysis.json\",\n" +
        "    \"pyruvate_branch.json\",\n" +
        "    \"tca.json\",\n" +
        "    \"etc_atp.json\",\n" +
        "    \"endings.json\",\n" +
        "    \"bad_endings.json\"\n" +
        "  ]\n" +
        "}"
    },
    {
      name: "container_array_inline_elements",
      input: {
        on_enter: [
          { op: "hide_all" },
          { op: "show_as", target: "glucose", args: { rep: "sticks" } }
        ]
      },
      expected: "{\n" +
        "  \"on_enter\": [\n" +
        "    {\"op\": \"hide_all\"},\n" +
        "    {\"op\": \"show_as\", \"target\": \"glucose\", \"args\": {\"rep\": \"sticks\"}}\n" +
        "  ]\n" +
        "}"
    },
    {
      name: "long_element_breaks",
      input: {
        log: [{ msg: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", n: 1 }]
      },
      expected: "{\n" +
        "  \"log\": [\n" +
        "    {\n" +
        "      \"msg\": \"" + "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" + "\",\n" +
        "      \"n\": 1\n" +
        "    }\n" +
        "  ]\n" +
        "}"
    },
    {
      name: "edits_style_entry",
      input: {
        edits: [{
          signature: { op: "point_mutation", target: "resi 479",
            args: { new_res: "ARG" } },
          branch_node: "gly.pyruvate",
          claim_id: "DIS-PKLR-01-cand"
        }]
      },
      expected: "{\n" +
        "  \"edits\": [\n" +
        "    {\n" +
        "      \"signature\": {\"op\": \"point_mutation\", \"target\": \"resi 479\", \"args\": {\"new_res\": \"ARG\"}},\n" +
        "      \"branch_node\": \"gly.pyruvate\",\n" +
        "      \"claim_id\": \"DIS-PKLR-01-cand\"\n" +
        "    }\n" +
        "  ]\n" +
        "}"
    },
    {
      name: "nested_empty_dict_list",
      input: {
        text: "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
        effects: {},
        claim_ids: []
      },
      expected: "{\n" +
        "  \"text\": \"" + "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy" + "\",\n" +
        "  \"effects\": {},\n" +
        "  \"claim_ids\": []\n" +
        "}"
    },
    {
      name: "raw_float",
      input: { resolution_angstrom: housy.rawFloat("2.40") },
      expected: "{\"resolution_angstrom\": 2.40}"
    },
    {
      name: "non_ascii_string",
      input: { text: "the road \u2014 em-dash \u2014 stays literal" },
      expected: "{\"text\": \"the road \u2014 em-dash \u2014 stays literal\"}"
    },
    {
      name: "string_with_quotes_and_backslashes",
      input: { s: "say \"hi\" \\ done" },
      expected: "{\"s\": \"say \\\"hi\\\" \\\\ done\"}"
    },
    {
      name: "dict_fits_exactly_at_width",
      input: { k: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" },
      expected: "{\"k\": \"" + "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" + "\"}"
    },
    {
      name: "propagation_child_list_too_long",
      input: { k: ["aaaaaaaaaaa", "aaaaaaaaaaa", "aaaaaaaaaaa", "aaaaaaaaaaa", "aaaaaaaaaaa", "aaaaaaaaaaa", "aaaaaaaaaaa", "aaaaaaaaaaa"] },
      expected: "{\n" +
        "  \"k\": [\n" +
        "    \"aaaaaaaaaaa\",\n" +
        "    \"aaaaaaaaaaa\",\n" +
        "    \"aaaaaaaaaaa\",\n" +
        "    \"aaaaaaaaaaa\",\n" +
        "    \"aaaaaaaaaaa\",\n" +
        "    \"aaaaaaaaaaa\",\n" +
        "    \"aaaaaaaaaaa\",\n" +
        "    \"aaaaaaaaaaa\"\n" +
        "  ]\n" +
        "}"
    }
  ];
  housy.SELFTEST_VECTORS = SELFTEST_VECTORS;

  /* ==================================================================== *
   * Boot-time self-test (the silent Canary).                             *
   * ==================================================================== */

  /* Run every vector through the serializer and compare with the embedded
   * canonical expected strings. Returns
   * {pass: bool, passed: int, total: int, results: [{name, ok, got, expected}]}. */
  function selfTestSerializer() {
    var results = [];
    var passCount = 0;
    for (var i = 0; i < SELFTEST_VECTORS.length; i++) {
      var vec = SELFTEST_VECTORS[i];
      var ok = false;
      var got;
      try {
        got = EDITOR.housy.stringify(vec.input);
        ok = (got === vec.expected);
      } catch (err) {
        got = "ERROR: " + (err && err.message ? err.message : String(err));
      }
      if (ok) {
        passCount += 1;
      }
      results.push({ name: vec.name, ok: ok, got: got, expected: vec.expected });
    }
    return {
      pass: passCount === SELFTEST_VECTORS.length,
      passed: passCount,
      total: SELFTEST_VECTORS.length,
      results: results
    };
  }
  EDITOR.selfTestSerializer = selfTestSerializer;

  function truncate(s, n) {
    var limit = (typeof n === "number") ? n : 120;
    if (s.length <= limit) {
      return s;
    }
    return s.slice(0, limit - 3) + "...";
  }

  function oneLine(v) {
    try {
      return JSON.stringify(v);
    } catch (err) {
      return String(v);
    }
  }

  /* Display helper: a compact pass/fail table (used by the Diagnostics tab
   * in 07.1-18; safe to call from the console before that plan lands). */
  function selfTestSerializerReport(result) {
    var r = result || selfTestSerializer();
    var lines = [];
    lines.push("serializer self-test: " +
      (r.pass ? "PASS" : "FAIL") + " (" + r.passed + "/" + r.total + " vectors)");
    for (var i = 0; i < r.results.length; i++) {
      var res = r.results[i];
      lines.push("  " + (res.ok ? "ok  " : "FAIL") + " " + res.name);
      if (!res.ok) {
        lines.push("       want: " + truncate(oneLine(res.expected)));
        lines.push("       got:  " + truncate(oneLine(res.got)));
      }
    }
    return lines.join("\n");
  }
  EDITOR.selfTestSerializerReport = selfTestSerializerReport;

  /* The one-line boot canary, written to the status area (a span of our own
   * -- #statusbar-serializer -- so no other plan's status span is touched)
   * and to the console. On failure the report follows on the console. */
  function logSelfTestLine(line, result) {
    try {
      var bar = document.getElementById("statusbar");
      if (bar) {
        var span = document.getElementById("statusbar-serializer");
        if (!span) {
          span = document.createElement("span");
          span.id = "statusbar-serializer";
          bar.appendChild(span);
        }
        span.textContent = line;
      }
    } catch (err) {
      /* status area may not exist (core absent / odd DOM) -- console below */
    }
    try {
      console.log(line);
      if (!result.pass) {
        console.log(selfTestSerializerReport(result));
      }
    } catch (err2) {
      /* console unavailable -- nothing more we can do */
    }
  }

  /* Init hook (registered below): runs the self-test once at boot.
   * Defensive try/catch -- a serializer bug must be VISIBLE, never fatal. */
  function bootSelfTest() {
    try {
      var result = selfTestSerializer();
      logSelfTestLine(
        "EDITOR: serializer self-test " + result.passed + "/" + result.total +
        (result.pass ? " pass" : " FAIL"),
        result);
    } catch (err) {
      try {
        console.log("EDITOR: serializer self-test ERROR: " + String(err));
      } catch (err2) {
        /* nothing more we can do */
      }
    }
  }

  /* Registration: use the core init registry when present (00_core.js
   * exposes EDITOR.init + EDITOR.runInits, run from the shell's
   * DOMContentLoaded bootstrap); otherwise run on DOMContentLoaded
   * ourselves so the canary fires even if the core asset is broken. */
  if (typeof EDITOR.init === "function") {
    EDITOR.init(bootSelfTest);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootSelfTest);
  } else {
    bootSelfTest();
  }
})();
