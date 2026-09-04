#!/usr/bin/env python3.6
"""tools/story_editor.py -- Phase 7.1 story-node editor generator.

Loads the LIVE repo data (nothing is embedded), runs a generation-time
structural sanity gate over it, and emits ONE self-contained offline HTML
page to the COMMITTED REPO ROOT (``story_editor.html``). The emitted page is
a data-free shell: at runtime the inlined JS assets load the story bundle
from sub-directories of the HTML's own directory (``data/story_glucose/``,
``data/citations.json``, ``data/sources.json``, ``rpg/data/edits.json``,
``rpg/data/cast.json``) -- per the binding user directive ("detect sub-dir
in the same dir of the html"; Firefox-first, no File System Access API, no
server, see 07.1-RESEARCH-UI.md "Persistence").

Asset pipeline: every ``*.js`` file dropped into ``tools/story_editor_assets/``
is auto-discovered (sorted by filename) and inlined as its own classic
``<script>`` block into the emitted page -- adding an editor capability NEVER
requires editing this generator. The page skeleton lives in
``tools/story_editor_assets/shell.html``.

Placement is load-bearing: the output MUST be the repo root (committed
territory). NEVER ``dist/`` (git-ignored -- the committed-artifact decision
would silently fail) and never ``tools/`` (the data dirs must be
sub-directories of the HTML's own directory; see 07.1-RESEARCH-UI.md
"Recommended file layout" + Pitfall 5).

Pure Python 3.6 stdlib ONLY (json, os, sys, html, datetime, re). NO
pymol/PyQt5 imports. NO f-strings (suite style: ``.format()`` / ``%`` /
concatenation). CWD-independent paths (SCRIPT_DIR/REPO_ROOT), mirroring the
committed ``tools/story_graph_viewer.py`` discipline (prior art -- consulted
for style, never imported: the viewer pins 57/21/15 counts that Phase 8 may
legitimately change).

Usage::

    python3.6 tools/story_editor.py
    python3.6 tools/story_editor.py --output /tmp/opencode/71/se.html \\
        --story-dir data/story_glucose

Defaults: --story-dir = <repo>/data/story_glucose, --output =
<repo>/story_editor.html.

Structural sanity gate (gates the CURRENT data, embeds NOTHING): JSON parse
errors, missing manifest-listed files, duplicate node ids across files (the
graph.py:76-80 ValueError class), ``choice.goto`` targets not resolving to
nodes, and ``manifest.start`` not in the node set. On any violation the
generator prints ``EDITOR_FAIL: ...`` and exits 1 WITHOUT writing the HTML.
The gate deliberately does NOT pin the 57/21/15 counts -- counts legitimately
change in Phase 8; count-shift detection belongs to the validator plans
(07.1-03 Python lint / 07.1-08 JS mirror).
"""

import datetime
import html
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Paths (CWD-independent)
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_STORY_DIR = os.path.join(REPO_ROOT, "data", "story_glucose")
ASSETS_DIR = os.path.join(SCRIPT_DIR, "story_editor_assets")
SHELL_NAME = "shell.html"
SHELL_PATH = os.path.join(ASSETS_DIR, SHELL_NAME)

DEFAULT_OUTPUT_PATH = os.path.join(REPO_ROOT, "story_editor.html")
OUTPUT_NAME = "story_editor.html"

# Live data targets (loaded ONLY as a generation-time sanity check over the
# current repo state; nothing is embedded into the emitted page).
REGISTRY_PATH = os.path.join(REPO_ROOT, "data", "citations.json")
SOURCES_PATH = os.path.join(REPO_ROOT, "data", "sources.json")
CAST_PATH = os.path.join(REPO_ROOT, "rpg", "data", "cast.json")
EDITS_PATH = os.path.join(REPO_ROOT, "rpg", "data", "edits.json")

USAGE = (
    "Usage: python3.6 tools/story_editor.py [--output PATH] [--story-dir DIR]\n"
    "  --output     emitted HTML path (default: <repo>/story_editor.html --\n"
    "               the committed repo-root artifact; NEVER dist/, it is\n"
    "               git-ignored)\n"
    "  --story-dir  story bundle dir (default: <repo>/data/story_glucose)\n")

# ---------------------------------------------------------------------------
# Tokens + title (substitution is str.replace ONLY -- .format() would explode
# on the shell's JS/CSS braces; assets are inlined RAW and are never
# token-substituted, so a later asset may use braces/braces freely)
# ---------------------------------------------------------------------------

TITLE = "RPG: Tale of C \u2014 Story Node Editor"

TOKEN_TITLE = "__TITLE__"
TOKEN_GENERATED_AT = "__GENERATED_AT__"
TOKEN_ASSET_MANIFEST = "__ASSET_MANIFEST__"
# The asset slot in the shell is wrapped in an HTML comment so the raw shell
# is still valid, renderable HTML before generation; the generator replaces
# the FULL marker (comment included) with the concatenated <script> blocks.
ASSET_MARKER = "<!--/*__ASSETS__*/-->"


def _esc(text):
    # type: (object) -> str
    """HTML-escape an interpolated constant (tokens never carry story data,
    but the escape discipline is kept anyway per the viewer's practice)."""
    return html.escape(str(text), quote=True)


# ---------------------------------------------------------------------------
# Loaders (all read-only; every failure raises ValueError with a clear label
# so main() can print EDITOR_FAIL and exit 1 without writing HTML)
# ---------------------------------------------------------------------------

def _load_json(path, label):
    # type: (str, str) -> object
    """Load a JSON file, raising ValueError on a missing file or a parse
    error (both are gate classes: 'missing manifest-listed file' and
    'JSON parse errors')."""
    if not os.path.isfile(path):
        raise ValueError("%s not found: %s" % (label, path))
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as e:
        raise ValueError("malformed %s JSON at %s: %s" % (label, path, e))


def load_shell(path):
    # type: (str) -> str
    """Read the page skeleton template (REQUIRED -- without it there is
    nothing to emit)."""
    if not os.path.isfile(path):
        raise ValueError("shell template not found: %s" % path)
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def load_story(story_dir):
    # type: (str) -> tuple
    """Load manifest + story files into (nodes, file_of, start, manifest).

    ``nodes`` is an ordered dict {id: node-dict-with-id} following the
    manifest file order (Python 3.6 dicts keep insertion order). Raises
    ValueError on a missing manifest, a missing/malformed manifest-listed
    file, or DUPLICATE node ids across files (the graph.py:76-80 ValueError
    class).
    """
    manifest_path = os.path.join(story_dir, "manifest.json")
    if not os.path.isfile(manifest_path):
        raise ValueError("story directory %r has no manifest.json" % story_dir)
    try:
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except ValueError as e:
        raise ValueError("malformed manifest JSON at %s: %s" % (manifest_path, e))
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must be a JSON object")
    start = manifest.get("start")
    files = manifest.get("files") or []
    if not files:
        raise ValueError("manifest.json lists no files")
    nodes = {}  # type: dict
    file_of = {}  # type: dict
    for fname in files:
        fpath = os.path.join(story_dir, fname)
        data = _load_json(fpath, "story file %s" % fname)
        file_nodes = (data.get("nodes") or {}) if isinstance(data, dict) else None
        if not isinstance(file_nodes, dict):
            raise ValueError("story file %s 'nodes' must be an object" % fname)
        for nid, raw in file_nodes.items():
            if nid in nodes:
                raise ValueError(
                    "duplicate node id %r (in %s; first seen in %s)"
                    % (nid, fname, file_of[nid]))
            if not isinstance(raw, dict):
                raise ValueError("node %r must be an object" % nid)
            raw_with_id = dict(raw)
            raw_with_id["id"] = nid
            nodes[nid] = raw_with_id
            file_of[nid] = fname
    return nodes, file_of, start, manifest


def load_registry(path):
    # type: (str) -> dict
    """Load the citation registry (claim_id -> record). REQUIRED."""
    data = _load_json(path, "citations registry")
    if not isinstance(data, dict):
        raise ValueError("citations registry must be a JSON object")
    return data


def load_sources(path):
    # type: (str) -> dict
    """Load data/sources.json (source provenance records). REQUIRED."""
    data = _load_json(path, "sources registry")
    if not isinstance(data, dict):
        raise ValueError("sources registry must be a JSON object")
    return data


def load_edits(path):
    # type: (str) -> dict
    """Load rpg/data/edits.json (known-edit buckets). REQUIRED."""
    data = _load_json(path, "edits manifest")
    if not isinstance(data, dict):
        raise ValueError("edits manifest must be a JSON object")
    enzymes = data.get("enzymes")
    if not isinstance(enzymes, dict):
        raise ValueError("edits.json 'enzymes' must be an object")
    return data


def load_cast(path):
    # type: (str) -> dict
    """Load cast.json into {id: entry}. OPTIONAL (display enrichment only):
    a missing or malformed file degrades to an empty lookup, never a crash
    (same discipline as the committed viewer's load_cast)."""
    try:
        data = _load_json(path, "cast")
    except ValueError:
        return {}
    entries = data.get("enzymes") if isinstance(data, dict) else None
    by_id = {}  # type: dict
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and entry.get("id"):
                by_id[str(entry["id"])] = entry
    return by_id


# ---------------------------------------------------------------------------
# Generation-time structural sanity gate
# ---------------------------------------------------------------------------

def check_structure(nodes, start):
    # type: (dict, object) -> list
    """Return a list of failure strings (empty == the gate passes).

    Exactly the plan's gate classes -- NOTHING is pinned (no node counts, no
    tier counts, no edit-allowed set): those belong to the validator plans
    (07.1-03 lint / 07.1-08 JS mirror). The loaders above already raise
    ValueError for JSON parse errors, missing files, and duplicate ids.
    """
    failures = []  # type: list

    # choice.goto targets must resolve to nodes.
    bad_goto = []  # type: list
    for nid, node in nodes.items():
        choices = node.get("choices")
        if not isinstance(choices, list):
            continue
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            target = choice.get("goto")
            if isinstance(target, str) and target and target not in nodes:
                bad_goto.append("%s -> %s" % (nid, target))
    if bad_goto:
        failures.append(
            "choice.goto targets not resolving to nodes: %s" % bad_goto)

    # manifest.start must be in the node set.
    if not start:
        failures.append('manifest.json has no "start" node id')
    elif start not in nodes:
        failures.append("manifest.start %r not in the node set" % start)

    return failures


# ---------------------------------------------------------------------------
# Asset pipeline (auto-discovery + inlining; adding a capability = dropping
# a .js file, never editing this generator)
# ---------------------------------------------------------------------------

def discover_asset_paths(assets_dir):
    # type: (str) -> list
    """Return the sorted paths of every *.js file directly inside
    assets_dir (shell.html is handled separately; sub-directories are not
    scanned). Missing assets dir == zero assets (the shell is emitted
    alone)."""
    if not os.path.isdir(assets_dir):
        return []
    names = []
    for name in os.listdir(assets_dir):
        path = os.path.join(assets_dir, name)
        if name.endswith(".js") and os.path.isfile(path):
            names.append(name)
    return [os.path.join(assets_dir, name) for name in sorted(names)]


def build_asset_blocks(asset_paths):
    # type: (list) -> tuple
    """Read each JS asset and build the concatenated inline blocks.

    Returns (blocks_html, manifest_text, total_asset_bytes). Each asset
    becomes its own classic <script> block (sorted order preserved), preceded
    by a traceability comment. A literal ``</script`` inside an asset (a JS
    string or comment) would terminate the block early, so it is rewritten to
    ``<\\/script`` -- semantics-preserving in JS string literals ("\\/" is an
    identity escape) and in regex literals alike.
    """
    blocks = []  # type: list
    manifest_parts = []  # type: list
    total = 0
    for path in asset_paths:
        name = os.path.basename(path)
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
        size = len(content.encode("utf-8"))
        total += size
        safe = re.sub(r"</script", lambda _m: "<\\/script", content,
                      flags=re.IGNORECASE)
        blocks.append(
            "<script>\n/* asset: %s (%d bytes) */\n%s\n</script>"
            % (name, size, safe))
        manifest_parts.append("%s (%d bytes)" % (name, size))
    if manifest_parts:
        blocks_html = "\n".join(blocks)
        manifest_text = "inlined assets (sorted): " + " | ".join(manifest_parts)
    else:
        blocks_html = (
            "<!-- (no JS assets discovered in tools/story_editor_assets/ "
            "yet -- the shell is emitted alone) -->")
        manifest_text = "inlined assets: (none yet)"
    return blocks_html, manifest_text, total


def render_html(shell, generated_at, asset_paths):
    # type: (str, str, list) -> tuple
    """Substitute the tokens and return the self-contained HTML string.

    Order matters: the shell-only tokens are replaced FIRST, then the asset
    marker is replaced with the raw asset blocks -- asset JS is never scanned
    for tokens. Returns (page, total_asset_bytes).
    """
    blocks_html, manifest_text, asset_bytes = build_asset_blocks(asset_paths)
    page = (shell
            .replace(TOKEN_TITLE, _esc(TITLE))
            .replace(TOKEN_GENERATED_AT, _esc(generated_at))
            .replace(TOKEN_ASSET_MANIFEST, manifest_text)
            .replace(ASSET_MARKER, blocks_html))
    return page, asset_bytes


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _usage_error(msg):
    # type: (str) -> None
    sys.stderr.write("story_editor: %s\n%s" % (msg, USAGE))


def parse_args(argv):
    # type: (list) -> tuple
    """Parse [--output PATH] [--story-dir DIR]. Returns
    (story_dir, output_path) or None on a usage error (usage already
    printed)."""
    story_dir = DEFAULT_STORY_DIR
    output_path = DEFAULT_OUTPUT_PATH
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg == "--output":
            if i + 1 >= len(argv):
                _usage_error("--output requires a PATH argument")
                return None
            i += 1
            output_path = argv[i]
        elif arg == "--story-dir":
            if i + 1 >= len(argv):
                _usage_error("--story-dir requires a DIR argument")
                return None
            i += 1
            story_dir = argv[i]
        else:
            _usage_error("unknown argument %r" % arg)
            return None
        i += 1
    return story_dir, output_path


def main(argv):
    # type: (list) -> int
    if any(a in ("-h", "--help") for a in argv[1:]):
        sys.stdout.write(USAGE)
        return 0
    parsed = parse_args(argv)
    if parsed is None:
        return 2
    story_dir, output_path = parsed

    try:
        shell = load_shell(SHELL_PATH)
        # The data loads ARE the parse/shape sanity gate: a missing or
        # malformed file fails generation loudly (EDITOR_FAIL + exit 1,
        # nothing written). Nothing here is embedded into the page.
        nodes, file_of, start, manifest = load_story(story_dir)
        load_registry(REGISTRY_PATH)
        load_sources(SOURCES_PATH)
        load_edits(EDITS_PATH)
        if not os.path.isfile(CAST_PATH):
            sys.stderr.write(
                "editor: WARNING optional %s not found -- continuing with an "
                "empty cast lookup (the runtime editor degrades the same way)\n"
                % CAST_PATH)
        load_cast(CAST_PATH)
    except (ValueError, OSError) as e:
        sys.stderr.write("EDITOR_FAIL: %s\n" % e)
        return 1

    failures = check_structure(nodes, start)
    if failures:
        sys.stderr.write(
            "EDITOR_FAIL: structural sanity gate found %d violation(s):\n"
            % len(failures))
        for line in failures:
            sys.stderr.write("  %s\n" % line)
        return 1

    generated_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    asset_paths = discover_asset_paths(ASSETS_DIR)
    page, asset_bytes = render_html(shell, generated_at, asset_paths)

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    total_bytes = len(page.encode("utf-8"))
    print("story_editor: emitted %s (%d JS asset(s) inlined, %d asset bytes, "
          "%d total bytes)"
          % (os.path.abspath(output_path), len(asset_paths), asset_bytes,
             total_bytes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
