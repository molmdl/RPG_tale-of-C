#!/usr/bin/env python3.6
"""tools/render_story_graph.py -- render a story graph skeleton as SVG + ASCII.

Pure Python 3.6 stdlib ONLY (json, os, sys, collections, xml.etree.ElementTree).
NO pymol/PyQt5 imports (the AST import gate scans this directory). NO external
deps (graphviz/mermaid/networkx) -- the layout is a hand-rolled swim-lane grid.

Reads a story bundle (manifest.json + per-file node fragments -- the same shape
``c14.story.graph.StoryGraph.load`` consumes) and produces two visualizations of
the graph:

  1. <output-dir>/<stem>.svg -- a swim-lane SVG (rows by pathway stage,
     color-coded endings, edit-allowed nodes marked, the RNG shuffle as a
     diamond, dashed edges for structural-only paths, a legend box).
  2. <output-dir>/<stem>.txt -- an ASCII diagram (box-drawing chars, grouped
     by stage, with edge arrows and type markers).

Usage::

    python3.6 tools/render_story_graph.py
    python3.6 tools/render_story_graph.py --story-dir data/story/ \\
        --output-dir /tmp/opencode/test-render

Defaults: --story-dir = <repo>/data/story_glucose, --output-dir = <repo>/.planning/
phases/05.1-story-graph-design-glucose-skeleton-integration-contracts/. The
script is CWD-independent (defaults are resolved relative to the script path).
"""

import collections
import json
import os
import sys
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Paths (CWD-independent)
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_STORY_DIR = os.path.join(REPO_ROOT, "data", "story_glucose")
DEFAULT_OUTPUT_DIR = os.path.join(
    REPO_ROOT, ".planning", "phases",
    "05.1-story-graph-design-glucose-skeleton-integration-contracts")

USAGE = (
    "Usage: python3.6 tools/render_story_graph.py "
    "[--story-dir DIR] [--output-dir DIR]\n"
    "  --story-dir   story bundle dir (default: data/story_glucose)\n"
    "  --output-dir  output dir (default: the phase 5.1 planning dir)\n")


# ---------------------------------------------------------------------------
# Stage grouping (swim-lane rows)
# ---------------------------------------------------------------------------

# Ordered list of (stage_key, human label). The renderer lays these out
# top-to-bottom in this order; unknown stages append at the end.
STAGE_ORDER = [
    ("intro", "Intro"),
    ("glycolysis", "Glycolysis"),
    ("pyruvate", "Pyruvate Branch + Anaerobic"),
    ("tca", "TCA Cycle"),
    ("etc", "ETC + ATP (True ending)"),
    ("endings", "Aerobic Endings"),
    ("bad", "Bad Endings + Edit Stub"),
]
STAGE_LABELS = dict(STAGE_ORDER)


def stage_key(node_id, node):
    # type: (str, dict) -> str
    """Return the swim-lane stage key for a node (drives row grouping).

    Grouping is by id prefix (the authoritative topology cue) with a
    stage:tag fallback for ids that don't match a known prefix. Anaerobic
    and pyruvate nodes share a row; end.true lives in the ETC row; bad.*
    and edit.prompt share the last row.
    """
    if node_id == "edit.prompt" or node_id.startswith("bad."):
        return "bad"
    if node_id == "end.true":
        return "etc"
    if node_id.startswith("end."):
        return "endings"
    if node_id.startswith("etc."):
        return "etc"
    if node_id.startswith("tca."):
        return "tca"
    if node_id.startswith("anaer.") or node_id.startswith("pyr."):
        return "pyruvate"
    if node_id.startswith("gly."):
        return "glycolysis"
    if node_id.startswith("intro.") or node_id in ("fa.stub", "alc.stub"):
        return "intro"
    # Fallback: a stage:<name> tag if present.
    for tag in (node.get("tags") or []):
        s = str(tag)
        if s.startswith("stage:"):
            return s.split(":", 1)[1]
    return "other"


# ---------------------------------------------------------------------------
# Node + edge classification (mirrors the 05.1-GRAPH-DIAGRAM.md legend)
# ---------------------------------------------------------------------------

def node_style(node_id, node):
    # type: (str, dict) -> tuple
    """Return (is_ending, is_edit, is_rng, is_stub, has_pdb) for a node.

    - is_ending: None or one of "true"/"good"/"normal"/"bad" (the ending tier).
    - is_edit:   True iff the node has an ``edit:enzyme:<id>`` tag.
    - is_rng:    True iff any choice has a non-None ``weight`` (RNG shuffle).
    - is_stub:   True iff id == "edit.prompt" or id ends with ".stub" or a
                 "stub"/"edit:prompt" tag is present (structural stub).
    - has_pdb:   True iff any on_enter MolAction has op == "load".
    """
    tags = node.get("tags") or []
    is_ending = node.get("is_ending")  # None or tier string
    is_edit = any(str(t).startswith("edit:enzyme:") for t in tags)
    is_rng = any(
        (c.get("weight") is not None) for c in (node.get("choices") or []))
    is_stub = (node_id == "edit.prompt"
               or node_id.endswith(".stub")
               or "stub" in tags
               or "edit:prompt" in tags)
    has_pdb = any(
        (m.get("op") == "load") for m in (node.get("on_enter") or []))
    return is_ending, is_edit, is_rng, is_stub, has_pdb


def classify_edge(src_id, choice):
    # type: (str, dict) -> tuple
    """Return (dashed, is_trap) for a choice.goto edge.

    SOLID (player-traversed forward path) by default; DASHED (structural-only)
    when any of:

    - goto == "edit.prompt" or the choice carries an ``edit:offer`` tag (the
      EditRouter routes at runtime, not the player picking this choice).
    - the source is the ``edit.prompt`` stub (its choices are structural BFS
      paths to the bad-ending pool).
    - the edge touches a Phase 8 stub (``fa.stub`` / ``alc.stub``) in either
      direction -- these are placeholder characters, not real forward gameplay.
    - the choice carries a ``cycle_trap`` tag (the tca.shuffle over-spin guard
      -- a bad-ending trigger, not a normal forward path). Also marked is_trap
      so the SVG paints it red and the ASCII tags it [TRAP].
    """
    goto = choice.get("goto")
    ctags = choice.get("tags") or []
    is_trap = "cycle_trap" in ctags
    dashed = False
    if goto == "edit.prompt" or "edit:offer" in ctags:
        dashed = True
    if src_id == "edit.prompt":
        dashed = True
    if src_id in ("fa.stub", "alc.stub") or goto in ("fa.stub", "alc.stub"):
        dashed = True
    if is_trap:
        dashed = True
    return dashed, is_trap


def _trunc(s, n):
    # type: (str, int) -> str
    """Truncate ``s`` to ``n`` chars with a ``...`` suffix; flatten newlines."""
    s = s.replace("\n", " ").strip()
    if len(s) <= n:
        return s
    return s[:n - 3] + "..."


def short_desc(node):
    # type: (dict) -> str
    """First 28 chars of text_dramatic with a leading ``TBD -`` prefix stripped."""
    desc = (node.get("text_dramatic") or "").strip()
    if desc.startswith("TBD"):
        rest = desc[3:].lstrip()
        for sep in ("\u2014", "-", "\u2013"):  # em dash, hyphen, en dash
            if rest.startswith(sep):
                rest = rest[len(sep):].lstrip()
                break
        desc = rest
    if not desc:
        for t in (node.get("tags") or []):
            s = str(t)
            if s.startswith("stage:"):
                return s.split(":", 1)[1]
        return ""
    return _trunc(desc, 28)


def edge_label(src_id, choice):
    # type: (str, dict) -> str
    """Compact edge label: weight / cond / edit:offer / structural / TRAP / text."""
    ctags = choice.get("tags") or []
    cond = choice.get("cond")
    weight = choice.get("weight")
    goto = choice.get("goto")
    label = (choice.get("label") or "").strip()
    if "cycle_trap" in ctags:
        return "TRAP"
    if weight is not None:
        return "w=" + str(weight)
    if goto in ("fa.stub", "alc.stub"):
        return "Phase 8 stub"
    if cond:
        return "cond: " + _trunc(cond, 22)
    if "edit:offer" in ctags:
        return "edit:offer"
    if src_id == "edit.prompt":
        return "structural"
    if src_id in ("fa.stub", "alc.stub"):
        return "Back"
    return _trunc(label, 20)


def _ascii_markers(node_id, node):
    # type: (str, dict) -> str
    """Return ASCII type markers for a node (e.g. ' [EDIT] [PDB]')."""
    is_ending, is_edit, is_rng, is_stub, has_pdb = node_style(node_id, node)
    marks = []
    if is_ending:
        marks.append("[" + str(is_ending).upper() + "]")
    if is_rng:
        marks.append("[RNG]")
    if is_edit:
        marks.append("[EDIT]")
    if is_stub:
        marks.append("[STUB]")
    if has_pdb and not is_ending:
        marks.append("[PDB]")
    return (" " + " ".join(marks)) if marks else ""


# ---------------------------------------------------------------------------
# Story loading (standalone -- mirrors c14.story.graph.StoryGraph.load so the
# script has no c14 import dependency and runs from any cwd)
# ---------------------------------------------------------------------------

def load_story(story_dir):
    # type: (str) -> tuple
    """Load manifest + files into (nodes dict, node id order list, start id).

    Raises ValueError if manifest.json is missing or a file fails to parse.
    """
    manifest_path = os.path.join(story_dir, "manifest.json")
    if not os.path.isfile(manifest_path):
        raise ValueError(
            "story directory %r has no manifest.json" % story_dir)
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    start = manifest.get("start")
    nodes = {}  # type: dict
    for fname in manifest.get("files", []):
        fpath = os.path.join(story_dir, fname)
        with open(fpath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        for nid, raw in (data.get("nodes") or {}).items():
            if not isinstance(raw, dict):
                raise ValueError("node %r must be an object" % nid)
            raw_with_id = dict(raw)
            raw_with_id["id"] = nid
            nodes[nid] = raw_with_id
    node_order = list(nodes.keys())  # insertion order (Python 3.6 dicts)
    return nodes, node_order, start


def build_edges(nodes, node_order):
    # type: (dict, list) -> list
    """Return a list of (src_id, tgt_id, choice_dict) for every choice.goto +
    every on_enter_divert. Divert edges carry a synthetic choice tagged
    ``auto-divert`` so they classify as structural (dashed)."""
    edges = []
    for nid in node_order:
        node = nodes[nid]
        for choice in (node.get("choices") or []):
            goto = choice.get("goto")
            if goto is not None:
                edges.append((nid, goto, choice))
        divert = node.get("on_enter_divert")
        if divert:
            edges.append((nid, divert, {
                "goto": divert, "label": "auto-divert",
                "tags": ["auto-divert"]}))
    return edges


def group_by_stage(nodes, node_order):
    # type: (dict, list) -> tuple
    """Return (ordered_stage_keys, rows) where rows maps stage_key -> [node_id]."""
    rows = collections.OrderedDict()  # type: collections.OrderedDict
    for nid in node_order:
        key = stage_key(nid, nodes[nid])
        rows.setdefault(key, []).append(nid)
    ordered_keys = [k for k, _ in STAGE_ORDER if k in rows]
    for k in rows:
        if k not in ordered_keys:
            ordered_keys.append(k)
    return ordered_keys, rows


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------

# Layout constants (px).
NODE_W = 170
NODE_H = 52
H_GAP = 48
V_GAP = 96
MARGIN_X = 40
TITLE_H = 70
STAGE_LABEL_H = 22
LEGEND_H = 150

# Tier colors: (fill, stroke, stroke-width).
TIER_COLORS = {
    "true": ("#FFD700", "#B8860B", "3"),
    "good": ("#90EE90", "#228B22", "2"),
    "normal": ("#87CEEB", "#4169E1", "2"),
    "bad": ("#FFB6C1", "#DC143C", "2"),
}


def _svg_node(svg, nid, node, x, y):
    # type: (...) -> None
    is_ending, is_edit, is_rng, is_stub, has_pdb = node_style(nid, node)
    fill = "#FFFFFF"
    stroke = "#666666"
    sw = "1.5"
    dash = None
    rx = "0"
    shape = "rect"

    if is_rng:
        fill = "#E6E6FA"
        # Gold border if the RNG node is also edit-allowed (tca.shuffle),
        # conveying both RNG (purple fill) and edit (gold border).
        stroke = "#DAA520" if is_edit else "#8A2BE2"
        sw = "2"
        shape = "diamond"
    elif is_stub:
        fill = "#D3D3D3"
        stroke = "#696969"
        sw = "1.5"
        dash = "5,3"
    elif is_ending:
        tier = str(is_ending)
        fill, stroke, sw = TIER_COLORS.get(
            tier, ("#FFFFFF", "#666666", "1.5"))
        rx = "10"  # rounded rectangle for endings
    elif is_edit:
        fill = "#FFF8DC"
        stroke = "#DAA520"
        sw = "2"

    attrs = {"fill": fill, "stroke": stroke, "stroke-width": sw}
    if dash:
        attrs["stroke-dasharray"] = dash

    if shape == "diamond":
        cx, cy = x + NODE_W / 2, y + NODE_H / 2
        pts = "%d,%d %d,%d %d,%d %d,%d" % (
            cx, y, x + NODE_W, cy, cx, y + NODE_H, x, cy)
        ET.SubElement(svg, "polygon", dict(attrs, points=pts))
    else:
        a = dict(attrs, x=str(x), y=str(y),
                 width=str(NODE_W), height=str(NODE_H))
        if rx:
            a["rx"] = rx
            a["ry"] = rx
        ET.SubElement(svg, "rect", a)

    # PDB-load corner mark (teal triangle) for non-ending nodes with a load.
    if has_pdb and not is_ending:
        ET.SubElement(svg, "polygon", {
            "points": "%d,%d %d,%d %d,%d" % (
                x + NODE_W - 12, y, x + NODE_W, y, x + NODE_W, y + 12),
            "fill": "#008B8B", "opacity": "0.85"})

    # Two-line label: node id (bold) + short description.
    desc = short_desc(node)
    t1 = ET.SubElement(svg, "text", {
        "x": str(x + NODE_W / 2), "y": str(y + 20),
        "text-anchor": "middle", "font-size": "12",
        "font-weight": "bold", "fill": "#222"})
    t1.text = nid
    t2 = ET.SubElement(svg, "text", {
        "x": str(x + NODE_W / 2), "y": str(y + 38),
        "text-anchor": "middle", "font-size": "10", "fill": "#444"})
    t2.text = desc


def _edge_geometry(sx, sy, tx, ty):
    # type: (int, int, int, int) -> tuple
    """Return (path_d, label_x, label_y) for an edge from src to tgt.

    Forward-down edges: straight line bottom-center -> top-center.
    Forward-right (same row): right-center -> left-center.
    Back-up (cross row, target above): quadratic bezier bowing left.
    Back-left (same row, target to the left): quadratic bezier bowing down.
    """
    src_cx = sx + NODE_W / 2
    src_cy = sy + NODE_H / 2
    tgt_cx = tx + NODE_W / 2
    tgt_cy = ty + NODE_H / 2
    same_row = abs(sy - ty) < 1

    if not same_row and ty > sy:
        # target below: forward down
        x1, y1 = src_cx, sy + NODE_H
        x2, y2 = tgt_cx, ty
        return ("M %d %d L %d %d" % (x1, y1, x2, y2),
                (x1 + x2) / 2, (y1 + y2) / 2)
    if not same_row and ty < sy:
        # target above: back edge, curve bowing left (away from forward flow)
        x1, y1 = src_cx, sy
        x2, y2 = tgt_cx, ty + NODE_H
        ctrl_x = min(x1, x2) - 70
        ctrl_y = (y1 + y2) / 2
        mx = 0.25 * x1 + 0.5 * ctrl_x + 0.25 * x2
        my = 0.25 * y1 + 0.5 * ctrl_y + 0.25 * y2
        return ("M %d %d Q %d %d %d %d" % (x1, y1, ctrl_x, ctrl_y, x2, y2),
                mx, my)
    if same_row and tgt_cx > src_cx:
        # forward right
        x1, y1 = sx + NODE_W, src_cy
        x2, y2 = tx, tgt_cy
        return ("M %d %d L %d %d" % (x1, y1, x2, y2),
                (x1 + x2) / 2, (y1 + y2) / 2)
    # same row, back left: curve bowing down below the row
    x1, y1 = sx, src_cy
    x2, y2 = tx + NODE_W, tgt_cy
    ctrl_y = (y1 + y2) / 2 + 55
    ctrl_x = (x1 + x2) / 2
    mx = 0.25 * x1 + 0.5 * ctrl_x + 0.25 * x2
    my = 0.25 * y1 + 0.5 * ctrl_y + 0.25 * y2
    return ("M %d %d Q %d %d %d %d" % (x1, y1, ctrl_x, ctrl_y, x2, y2), mx, my)


def _svg_edge(svg, src, tgt, choice, positions):
    # type: (...) -> None
    if src not in positions or tgt not in positions:
        return  # skip edges to nonexistent nodes (graceful)
    sx, sy = positions[src]
    tx, ty = positions[tgt]
    dashed, is_trap = classify_edge(src, choice)
    color = "#CC0000" if is_trap else "#555555"
    marker = "arrowtrap" if is_trap else "arrow"
    sw = "2" if is_trap else "1.2"

    d, mx, my = _edge_geometry(sx, sy, tx, ty)
    attrs = {"d": d, "fill": "none", "stroke": color,
             "stroke-width": sw, "marker-end": "url(#%s)" % marker}
    if dashed:
        attrs["stroke-dasharray"] = "5,3"
    ET.SubElement(svg, "path", attrs)

    label = edge_label(src, choice)
    if label:
        lt = ET.SubElement(svg, "text", {
            "x": str(int(mx)), "y": str(int(my) - 2),
            "text-anchor": "middle", "font-size": "9", "fill": color,
            # White halo so the label is readable over crossing lines.
            "paint-order": "stroke", "stroke": "#FFFFFF",
            "stroke-width": "3px", "stroke-linejoin": "round"})
        lt.text = label


def _svg_legend(svg, x, y, w):
    # type: (...) -> None
    ET.SubElement(svg, "rect", {
        "x": str(x), "y": str(y), "width": str(w), "height": str(LEGEND_H - 20),
        "fill": "#FAFAFA", "stroke": "#CCCCCC", "stroke-width": "1", "rx": "6"})
    t = ET.SubElement(svg, "text", {
        "x": str(x + 12), "y": str(y + 20), "font-size": "13",
        "font-weight": "bold", "fill": "#333"})
    t.text = "Legend"

    items = [
        ("rect", "#FFD700", "#B8860B", "True ending"),
        ("rect", "#90EE90", "#228B22", "Good ending"),
        ("rect", "#87CEEB", "#4169E1", "Normal ending"),
        ("rect", "#FFB6C1", "#DC143C", "Bad ending"),
        ("rect", "#FFF8DC", "#DAA520", "Edit-allowed (edit:enzyme:)"),
        ("diamond", "#E6E6FA", "#8A2BE2", "RNG shuffle (weighted)"),
        ("stub", "#D3D3D3", "#696969", "Structural stub (edit.prompt)"),
        ("pdb", "#FFFFFF", "#008B8B", "PDB-load node (corner mark)"),
    ]
    col_w = (w - 24) / 4.0
    row_h = 26
    for i, (shape, fill, stroke, label) in enumerate(items):
        col = i % 4
        row = i // 4
        ix = x + 12 + col * col_w
        iy = y + 36 + row * row_h
        if shape == "diamond":
            cx = ix + 12
            pts = "%d,%d %d,%d %d,%d %d,%d" % (
                cx, iy, ix + 24, iy + 8, cx, iy + 16, ix, iy + 8)
            ET.SubElement(svg, "polygon", {
                "points": pts, "fill": fill, "stroke": stroke,
                "stroke-width": "1.5"})
        elif shape == "stub":
            ET.SubElement(svg, "rect", {
                "x": str(ix), "y": str(iy), "width": "24", "height": "16",
                "fill": fill, "stroke": stroke, "stroke-width": "1.5",
                "stroke-dasharray": "4,2", "rx": "2"})
        elif shape == "pdb":
            ET.SubElement(svg, "rect", {
                "x": str(ix), "y": str(iy), "width": "24", "height": "16",
                "fill": fill, "stroke": stroke, "stroke-width": "1.5", "rx": "2"})
            ET.SubElement(svg, "polygon", {
                "points": "%d,%d %d,%d %d,%d" % (
                    ix + 12, iy, ix + 24, iy, ix + 24, iy + 12),
                "fill": "#008B8B", "opacity": "0.85"})
        else:
            ET.SubElement(svg, "rect", {
                "x": str(ix), "y": str(iy), "width": "24", "height": "16",
                "fill": fill, "stroke": stroke, "stroke-width": "1.5", "rx": "4"})
        lt = ET.SubElement(svg, "text", {
            "x": str(ix + 32), "y": str(iy + 12), "font-size": "11",
            "fill": "#333"})
        lt.text = label

    # Edge-style legend row.
    ey = y + 36 + 2 * row_h + 4
    edge_items = [
        (12, "#555555", "1.2", None, "arrow", "solid = player path"),
        (210, "#555555", "1.2", "5,3", "arrow", "dashed = structural-only"),
        (430, "#CC0000", "2", "5,3", "arrowtrap", "red dashed = RNG cycle-trap"),
    ]
    for off, color, lw, dasharr, marker, label in edge_items:
        ex1 = x + off
        ex2 = x + off + 40
        a = {"d": "M %d %d L %d %d" % (ex1, ey, ex2, ey),
             "stroke": color, "stroke-width": lw, "fill": "none",
             "marker-end": "url(#%s)" % marker}
        if dasharr:
            a["stroke-dasharray"] = dasharr
        ET.SubElement(svg, "path", a)
        lt = ET.SubElement(svg, "text", {
            "x": str(ex2 + 8), "y": str(ey + 4), "font-size": "11",
            "fill": "#333"})
        lt.text = label


def render_svg(nodes, node_order, edges, out_path, title, node_count):
    # type: (...) -> None
    ordered_keys, rows = group_by_stage(nodes, node_order)

    # Compute node positions.
    positions = {}
    y = TITLE_H
    max_row_nodes = 1
    for key in ordered_keys:
        nids = rows[key]
        max_row_nodes = max(max_row_nodes, len(nids))
        y += STAGE_LABEL_H
        for i, _nid in enumerate(nids):
            x = MARGIN_X + i * (NODE_W + H_GAP)
            positions[_nid] = (x, y)
        y += NODE_H + V_GAP
    content_h = y

    width = max(MARGIN_X * 2 + max_row_nodes * (NODE_W + H_GAP), 920)
    height = max(content_h + LEGEND_H + MARGIN_X, 600)

    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "width": str(width),
        "height": str(height),
        "viewBox": "0 0 %d %d" % (width, height),
        "font-family": "DejaVu Sans, Arial, Helvetica, sans-serif",
    })

    # Arrowhead markers (grey + red for traps).
    defs = ET.SubElement(svg, "defs")
    for mid, color in (("arrow", "#555555"), ("arrowtrap", "#CC0000")):
        m = ET.SubElement(defs, "marker", {
            "id": mid, "viewBox": "0 0 10 10", "refX": "9", "refY": "5",
            "markerWidth": "7", "markerHeight": "7",
            "orient": "auto-start-reverse"})
        ET.SubElement(m, "path", {"d": "M 0 0 L 10 5 L 0 10 z", "fill": color})

    # Background.
    ET.SubElement(svg, "rect", {
        "x": "0", "y": "0", "width": str(width), "height": str(height),
        "fill": "#FFFFFF"})

    # Title.
    t = ET.SubElement(svg, "text", {
        "x": str(width / 2), "y": "30", "text-anchor": "middle",
        "font-size": "20", "font-weight": "bold", "fill": "#222222"})
    t.text = title
    t2 = ET.SubElement(svg, "text", {
        "x": str(width / 2), "y": "52", "text-anchor": "middle",
        "font-size": "13", "fill": "#666666"})
    t2.text = ("%d nodes | solid = player path | dashed = structural-only "
               "| red = RNG cycle-trap" % node_count)

    # Stage rows + nodes.
    y_cursor = TITLE_H
    for key in ordered_keys:
        nids = rows[key]
        label = STAGE_LABELS.get(key, key.title())
        sl = ET.SubElement(svg, "text", {
            "x": str(MARGIN_X), "y": str(y_cursor + 16), "font-size": "14",
            "font-weight": "bold", "fill": "#555555"})
        sl.text = "=== %s (%d) ===" % (label, len(nids))
        # Subtle row separator line.
        ET.SubElement(svg, "line", {
            "x1": str(MARGIN_X), "y1": str(y_cursor + 20),
            "x2": str(width - MARGIN_X), "y2": str(y_cursor + 20),
            "stroke": "#EEEEEE", "stroke-width": "1"})
        y_cursor += STAGE_LABEL_H
        for nid in nids:
            nx, ny = positions[nid]
            _svg_node(svg, nid, nodes[nid], nx, ny)
        y_cursor += NODE_H + V_GAP

    # Edges (after nodes so arrows render on top).
    for (src, tgt, choice) in edges:
        _svg_edge(svg, src, tgt, choice, positions)

    # Legend.
    _svg_legend(svg, MARGIN_X, content_h + 20, width - 2 * MARGIN_X)

    tree = ET.ElementTree(svg)
    tree.write(out_path, encoding="UTF-8", xml_declaration=True)


# ---------------------------------------------------------------------------
# ASCII rendering
# ---------------------------------------------------------------------------

def _ascii_summary(nodes, node_order):
    # type: (dict, list) -> str
    tiers = collections.Counter()
    edit_n = rng_n = 0
    for nid in node_order:
        is_ending, is_edit, is_rng, _is_stub, _has_pdb = node_style(
            nid, nodes[nid])
        if is_ending:
            tiers[str(is_ending)] += 1
        if is_edit:
            edit_n += 1
        if is_rng:
            rng_n += 1
    tier_str = "/".join(
        "%d%s" % (tiers.get(t, 0), t[0].upper())
        for t in ("true", "good", "normal", "bad") if tiers.get(t))
    ending_total = sum(tiers.values())
    return ("Summary: %d nodes | %d endings (%s) | %d edit-allowed | %d RNG"
            % (len(node_order), ending_total, tier_str or "0", edit_n, rng_n))


# --- Spatial ASCII layout engine --------------------------------------------

class _CharBuf(object):
    """2D character buffer for drawing connected-box ASCII flowcharts."""

    def __init__(self):
        self.grid = []  # list of list of chars, grows as needed

    def _ensure(self, x, y):
        while len(self.grid) <= y:
            self.grid.append([])
        for row in self.grid:
            while len(row) <= x:
                row.append(' ')

    def put(self, x, y, ch):
        # type: (int, int, str) -> None
        self._ensure(x, y)
        if 0 <= y < len(self.grid) and 0 <= x < len(self.grid[y]):
            self.grid[y][x] = ch

    def put_text(self, x, y, text):
        # type: (int, int, str) -> None
        for i, ch in enumerate(text):
            self.put(x + i, y, ch)

    def hline(self, x1, x2, y, ch='\u2500'):
        # type: (int, int, int, str) -> None
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.put(x, y, ch)

    def vline(self, x, y1, y2, ch='\u2502'):
        # type: (int, int, int, str) -> None
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.put(x, y, ch)

    def to_lines(self):
        # type: () -> list
        return [''.join(row).rstrip() for row in self.grid]


def _box_size(nid, node):
    # type: (str, dict) -> tuple
    """Return (width, height, inner) for a node box that fits content (no truncation)."""
    markers = _ascii_markers(nid, node)
    desc = short_desc(node)
    title = nid + markers
    # inner = content area; fit the longest line, min 16
    inner = max(len(title) + 2, len(desc) + 2 if desc else 0, 16)
    width = inner + 2  # +2 for borders
    is_ending, _a, _b, _c, _d = node_style(nid, node)
    lines = 2  # top + bottom borders
    lines += 1  # title line
    if desc:
        lines += 1
    if len(title) > inner - 2 and markers:
        # id + markers don't fit on one line; markers get their own line
        lines += 1
    return width, lines, inner


def _draw_box_simple(nid, node, width, inner):
    # type: (str, dict, int, int) -> list
    """Return box lines as a list of strings (for the loose-nodes section)."""
    markers = _ascii_markers(nid, node)
    desc = short_desc(node)
    title = nid + markers
    out = []
    out.append('  \u250c' + '\u2500' * inner + '\u2510')
    row = '\u2502'
    if len(title) > inner - 2 and markers:
        row += nid + ' ' * (inner - len(nid))
    else:
        row += title + ' ' * (inner - len(title))
    row += '\u2502'
    out.append('  ' + row)
    if len(title) > inner - 2 and markers:
        m = markers.strip()
        out.append('  \u2502' + m + ' ' * (inner - len(m)) + '\u2502')
    if desc:
        d = desc[:inner] + ' ' * (inner - min(len(desc), inner))
        out.append('  \u2502' + d + '\u2502')
    out.append('  \u2514' + '\u2500' * inner + '\u2518')
    return out


def _draw_box(buf, x, y, nid, node, width, inner):
    # type: (_CharBuf, int, int, str, dict, int, int) -> tuple
    """Draw a node box at char position (x, y). Returns (center_x, bottom_y, top_y)."""
    markers = _ascii_markers(nid, node)
    is_ending, _a, _b, _c, _d = node_style(nid, node)
    desc = short_desc(node)
    title = nid + markers
    top = '\u250c' + '\u2500' * inner + '\u2510'
    bot = '\u2514' + '\u2500' * inner + '\u2518'
    buf.put_text(x, y, top)
    row = y + 1
    if len(title) > inner - 2 and markers:
        # id on first line, markers on second
        t1 = nid + ' ' * (inner - len(nid))
        buf.put_text(x, row, '\u2502' + t1 + '\u2502')
        row += 1
        t2 = markers.strip() + ' ' * (inner - len(markers.strip()))
        buf.put_text(x, row, '\u2502' + t2 + '\u2502')
        row += 1
    else:
        t1 = title + ' ' * (inner - len(title))
        buf.put_text(x, row, '\u2502' + t1 + '\u2502')
        row += 1
    if desc:
        d = desc[:inner] + ' ' * (inner - min(len(desc), inner))
        buf.put_text(x, row, '\u2502' + d + '\u2502')
        row += 1
    buf.put_text(x, row, bot)
    center_x = x + width // 2
    return center_x, row, y  # center_x, bottom_y, top_y


def _compute_ascii_layout(nodes, node_order, edges):
    # type: (dict, list, list) -> tuple
    """BFS layout: assign (level, col) to each node.

    Returns (positions, spatial_edges, note_edges).
    - spatial_edges: (src, tgt, [labels]) drawn as L-shaped connector lines.
      Labels from ALL solid choices to that target are merged (e.g. Continue
      + Observe both going to gly.g6p -> one connector with 2 labels).
    - note_edges: {src: [(tgt, label, is_dashed, is_trap)]} drawn as text
      annotations. ONLY actually-dashed/trap/back-edge edges are notes.
      Same-target solid duplicates are NOT notes (labels merged into spatial).
    """
    edges_by_src = collections.defaultdict(list)
    for (src, tgt, choice) in edges:
        edges_by_src[src].append((tgt, choice))

    positions = {}  # node_id -> (level, col)
    spatial_edges = []  # (src, tgt, [labels])
    note_edges = collections.defaultdict(list)  # src -> [(tgt, label, dashed, is_trap)]
    occupied = collections.defaultdict(set)  # level -> set of cols

    start = None
    for nid in node_order:
        if nid.startswith('intro.') or nid == node_order[0]:
            start = nid
            break
    if not start:
        start = node_order[0]

    from collections import deque
    queue = deque([start])
    positions[start] = (0, 0)
    occupied[0].add(0)

    while queue:
        nid = queue.popleft()
        level, col = positions[nid]
        outs = edges_by_src.get(nid, [])
        child_level = level + 1

        # Group solid edges by target (merge same-target labels)
        solid_by_tgt = collections.OrderedDict()  # tgt -> [choices]
        notes = []
        for (tgt, choice) in outs:
            dashed, is_trap = classify_edge(nid, choice)
            if dashed or is_trap:
                notes.append((tgt, edge_label(nid, choice), True, is_trap))
            elif tgt in positions and positions[tgt][0] <= level:
                # back-edge / already placed -> note (solid but can't draw spatially)
                notes.append((tgt, edge_label(nid, choice), False, False))
            else:
                solid_by_tgt.setdefault(tgt, []).append(choice)

        spatial_children = list(solid_by_tgt.keys())  # distinct targets
        n = len(spatial_children)
        if n == 0:
            pass
        elif n == 1:
            tgt = spatial_children[0]
            cc = col
            if cc in occupied[child_level]:
                off = 1
                while True:
                    if col + off not in occupied[child_level]:
                        cc = col + off
                        break
                    if col - off not in occupied[child_level]:
                        cc = col - off
                        break
                    off += 1
            if tgt not in positions:
                positions[tgt] = (child_level, cc)
                occupied[child_level].add(cc)
                queue.append(tgt)
            labels = [edge_label(nid, c) for c in solid_by_tgt[tgt]]
            spatial_edges.append((nid, tgt, labels))
        else:
            for i, tgt in enumerate(spatial_children):
                cc = col + (i - (n - 1) // 2)
                while cc < 0:
                    cc += 1
                if cc in occupied[child_level]:
                    off = 1
                    while True:
                        if col + (i - (n - 1) // 2) + off not in occupied[child_level]:
                            cc = col + (i - (n - 1) // 2) + off
                            break
                        if col + (i - (n - 1) // 2) - off not in occupied[child_level]:
                            cc = col + (i - (n - 1) // 2) - off
                            break
                        off += 1
                if tgt not in positions:
                    positions[tgt] = (child_level, cc)
                    occupied[child_level].add(cc)
                    queue.append(tgt)
                labels = [edge_label(nid, c) for c in solid_by_tgt[tgt]]
                spatial_edges.append((nid, tgt, labels))

        note_edges[nid] = notes

    return positions, spatial_edges, note_edges


def render_ascii(nodes, node_order, edges, out_path, title, node_count):
    # type: (...) -> None
    """Render a spatial multi-column connected-box ASCII flowchart.

    Nodes are placed on a 2D character grid via BFS layout (branches spread
    into separate columns side-by-side). Boxes are connected by L-shaped
    lines (vertical + horizontal + arrow). Dashed/structural edges
    (edit:offer, trap, stubs, cycle back-edges) are drawn as text notes
    beside the source box, not as spatial lines (they would tangle).
    Endings are terminal boxes. No text truncation -- boxes grow to fit.
    """
    positions, spatial_edges, note_edges = _compute_ascii_layout(
        nodes, node_order, edges)

    # Box dimensions
    box_info = {}  # nid -> (width, height, inner)
    for nid in positions:
        w, h, inner = _box_size(nid, nodes[nid])
        box_info[nid] = (w, h, inner)

    # Column x-positions
    cols = sorted(set(pos[1] for pos in positions.values()))
    col_w = {}
    for nid, (lv, c) in positions.items():
        col_w[c] = max(col_w.get(c, 0), box_info[nid][0])
    col_gap = 8
    col_x = {}
    x_cursor = 4
    for c in cols:
        col_x[c] = x_cursor
        x_cursor += col_w.get(c, 24) + col_gap
    total_w = x_cursor + 4

    # Level y-positions
    max_level = max(pos[0] for pos in positions.values()) if positions else 0
    level_h = {}
    for nid, (lv, c) in positions.items():
        level_h[lv] = max(level_h.get(lv, 0), box_info[nid][1])
    connector_h = 5
    level_y = {}
    y_cursor = 6  # leave room for legend
    for lv in range(max_level + 1):
        level_y[lv] = y_cursor
        y_cursor += level_h.get(lv, 3) + connector_h
    total_h = y_cursor + 4

    buf = _CharBuf()

    # Draw boxes
    box_geo = {}  # nid -> (center_x, top_y, bottom_y, x_left)
    for nid, (lv, c) in positions.items():
        bx = col_x[c] + (col_w.get(c, 0) - box_info[nid][0]) // 2
        by = level_y[lv]
        cx, bot_y, top_y = _draw_box(
            buf, bx, by, nid, nodes[nid], box_info[nid][0], box_info[nid][2])
        box_geo[nid] = (cx, top_y, bot_y, bx)

    # Draw spatial connectors (L-shaped: down from src center, across, down to tgt top)
    for (src, tgt, labels) in spatial_edges:
        if src not in box_geo or tgt not in box_geo:
            continue
        sx, _st, s_bot, _sx_left = box_geo[src]
        tx, t_top, _t_bot, _tx_left = box_geo[tgt]
        lab = ' / '.join(labels) if labels else ''
        mid_y = s_bot + (t_top - s_bot) // 2
        if mid_y <= s_bot:
            mid_y = s_bot + 2
        if sx != tx:
            # L-shaped: vertical down to mid_y-1, horizontal at mid_y, vertical to target
            buf.vline(sx, s_bot + 1, mid_y - 1)
            buf.hline(min(sx, tx), max(sx, tx), mid_y)
            buf.put(sx, mid_y, '\u252c')  # T-down at source side
            buf.put(tx, mid_y, '\u252c')  # T-down at target side
            buf.vline(tx, mid_y + 1, t_top - 1)
        else:
            # straight vertical
            buf.vline(sx, s_bot + 1, t_top - 1)
        buf.put(tx, t_top - 1, '\u25bc')
        # label placed near the arrowhead, to the right of ▼
        if lab:
            buf.put_text(tx + 2, t_top - 1, lab)

    # Draw note edges (dashed/structural/trap/cycle) as text annotations
    for nid, notes in note_edges.items():
        if not notes or nid not in box_geo:
            continue
        _cx, _top, bot, x_left = box_geo[nid]
        note_y = bot + 1
        for (tgt, lab, is_dashed, is_trap) in notes:
            if is_trap:
                txt = '  \u2504\u2504\u25ba %s \u2500\u2500\u25ba %s  [TRAP]' % (lab, tgt)
            elif is_dashed:
                txt = '  \u2504\u2504\u25ba %s \u2500\u2500\u25ba %s' % (lab, tgt)
            else:
                # solid back-edge/cycle: use solid arrow, not dashed
                txt = '  \u2500\u2500\u25ba %s \u2500\u2500\u25ba %s' % (lab, tgt)
            buf.put_text(x_left, note_y, txt)
            note_y += 1

    # Convert buffer to lines
    grid_lines = buf.to_lines()

    # Unreached nodes (only reachable via dashed/structural edges — not in BFS)
    unreached = [nid for nid in node_order if nid not in positions]
    loose_lines = []
    if unreached:
        loose_lines.append('')
        loose_lines.append('-' * min(total_w, 100))
        loose_lines.append('=== Unreached nodes (%d) — structural/bad-ending pool ===' % len(unreached))
        loose_lines.append('-' * min(total_w, 100))
        loose_lines.append('')
        edges_by_src_loose = collections.defaultdict(list)
        for (src, tgt, choice) in edges:
            edges_by_src_loose[src].append((tgt, choice))
        for nid in unreached:
            node = nodes[nid]
            w, h, inner = _box_size(nid, node)
            box = _draw_box_simple(nid, node, w, inner)
            loose_lines.extend(box)
            outs = edges_by_src_loose.get(nid, [])
            for (tgt, choice) in outs:
                dashed, is_trap = classify_edge(nid, choice)
                lab = edge_label(nid, choice)
                marker = '  [TRAP]' if is_trap else ''
                arr = '\u2504\u2504\u25ba' if dashed else '\u2500\u2500\u25ba'
                loose_lines.append('  %s %s%s \u2500\u2500\u25ba %s' % (arr, lab, marker, tgt))
            loose_lines.append('')

    # Build header (legend + summary)
    header = [
        '=' * min(total_w, 100),
        title,
        'Legend: \u2502\u25bc\u2500 = player path (spatial)  |  '
        '\u2504\u2504\u25ba = edit:offer/structural/cycle (note)  |  '
        '[TRAP] = RNG cycle-trap',
        '        [EDIT] = edit-allowed (14)  |  [PDB] = PDB load  |  '
        '[TRUE/GOOD/NORMAL/BAD] = ending tier',
        _ascii_summary(nodes, node_order),
        '=' * min(total_w, 100),
        '',
    ]

    # Merge header + grid + loose
    all_lines = header + grid_lines + loose_lines

    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(all_lines) + '\n')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv):
    # type: (list) -> tuple
    story_dir = DEFAULT_STORY_DIR
    output_dir = DEFAULT_OUTPUT_DIR
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg == "--story-dir":
            i += 1
            if i >= len(argv):
                sys.stderr.write("--story-dir requires an argument\n")
                sys.exit(2)
            story_dir = argv[i]
        elif arg == "--output-dir":
            i += 1
            if i >= len(argv):
                sys.stderr.write("--output-dir requires an argument\n")
                sys.exit(2)
            output_dir = argv[i]
        elif arg in ("-h", "--help"):
            sys.stdout.write(USAGE)
            sys.exit(0)
        else:
            sys.stderr.write("Unknown argument: %s\n\n%s" % (arg, USAGE))
            sys.exit(2)
        i += 1
    return story_dir, output_dir


def main(argv):
    # type: (list) -> int
    story_dir, output_dir = parse_args(argv)
    nodes, node_order, _start = load_story(story_dir)
    edges = build_edges(nodes, node_order)
    node_count = len(nodes)

    base = os.path.basename(os.path.normpath(story_dir))
    if base == "story_glucose":
        stem = "05.1-graph"
    else:
        stem = base + "-graph"

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    svg_path = os.path.join(output_dir, stem + ".svg")
    txt_path = os.path.join(output_dir, stem + ".txt")

    if base == "story_glucose":
        title = "Glucose Story Graph Skeleton (Phase 5.1)"
    else:
        title = "Story Graph: %s" % base

    render_svg(nodes, node_order, edges, svg_path, title, node_count)
    render_ascii(nodes, node_order, edges, txt_path, title, node_count)

    print("Rendered %d nodes, %d edges" % (node_count, len(edges)))
    print("  SVG : %s" % svg_path)
    print("  TXT : %s" % txt_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
