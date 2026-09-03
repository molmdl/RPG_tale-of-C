#!/usr/bin/env python3.6
"""tools/story_graph_viewer.py -- self-contained HTML story-graph review viewer.

Read-only generator: loads the Phase 7 glucose story bundle (manifest.json +
per-file node fragments), the citation registry, the cast and the known-edit
manifest, derives node kinds / ending tiers / edit routing, and emits ONE
self-contained HTML file (vanilla JS + SVG, ZERO external libraries, all data
inlined at build time). The output is the review instrument for the Phase 7
story-graph human checkpoint: interactive network (zoom/pan/drag) LEFT, full
two-layer reading panel RIGHT, edit-routing overlay, search/filter/review
order, and live claim-status chips.

Pure Python 3.6 stdlib ONLY (json, os, sys, html). NO pymol/PyQt5 imports
(the AST import gate scans this directory). NO f-strings (suite style:
``.format()`` / ``%`` / concatenation). The script is CWD-independent
(defaults are resolved relative to the script path).

Usage::

    python3.6 tools/story_graph_viewer.py
    python3.6 tools/story_graph_viewer.py --story-dir data/story_glucose \\
        --output-dir /tmp/opencode/test-dist --dump-data /tmp/opencode/data.json

Defaults: --story-dir = <repo>/data/story_glucose, --output-dir = <repo>/dist
(output file: dist/story_graph_viewer.html). On any integrity invariant
violation the generator prints ``VIEWER_FAIL: ...`` and exits 1 WITHOUT
writing the HTML.
"""

import html
import json
import math
import os
import sys

# ---------------------------------------------------------------------------
# Paths (CWD-independent)
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_STORY_DIR = os.path.join(REPO_ROOT, "data", "story_glucose")
DEFAULT_OUTPUT_DIR = os.path.join(REPO_ROOT, "dist")
OUTPUT_NAME = "story_graph_viewer.html"

REGISTRY_PATH = os.path.join(REPO_ROOT, "data", "citations.json")
CAST_PATH = os.path.join(REPO_ROOT, "rpg", "data", "cast.json")
EDITS_PATH = os.path.join(REPO_ROOT, "rpg", "data", "edits.json")

USAGE = (
    "Usage: python3.6 tools/story_graph_viewer.py "
    "[--story-dir DIR] [--output-dir DIR] [--dump-data PATH]\n"
    "  --story-dir   story bundle dir (default: data/story_glucose)\n"
    "  --output-dir  output dir for the HTML (default: <repo>/dist)\n"
    "  --dump-data   also write the derived payload JSON to PATH (debug)\n")

# ---------------------------------------------------------------------------
# Layout constants (deterministic 7-column layered layout)
# ---------------------------------------------------------------------------

NODE_W = 190
NODE_H = 68
X0 = 60
Y0 = 90
COL_PITCH = 280
ROW_PITCH = 96

# Source file -> column. Manifest order drives everything else.
FILE_COL = {
    "intro.json": 0,
    "glycolysis.json": 1,
    "pyruvate_branch.json": 2,
    "tca.json": 3,
    "etc_atp.json": 4,
    "endings.json": 5,
    "bad_endings.json": 5,
}
COL_LABELS = {
    0: "Intro",
    1: "Glycolysis",
    2: "Pyruvate+Anaerobic",
    3: "TCA",
    4: "ETC+ATP",
    5: "Endings + Bad pool",
    6: "Phase-8 stubs",
}
N_COLS = 7

# Special node ids.
EDIT_PROMPT_ID = "edit.prompt"
STUB_IDS = ("fa.stub", "alc.stub")
RESTORED_IDS = ("gly.pfk_restored", "tca.aconitase_restored")
PLACEHOLDER_CLAIM = "PLACEHOLDER_PHASE8"
RNG_NODE_ID = "tca.shuffle"

# Pinned invariants (verified against the live data on 2026-09-03; the
# integrity self-check gates regeneration on them).
EXPECTED_TIER_COUNTS = {"true": 1, "good": 3, "normal": 2, "bad": 15}
EXPECTED_EDIT_ALLOWED = frozenset([
    "gly.pfk", "gly.pyruvate_kinase", "pyr.pdh", "tca.citrate_synthase",
    "tca.aconitase", "tca.shuffle", "tca.isocitrate_dh", "tca.akg_dh",
    "tca.succinyl_coa_synthetase", "tca.fumarase", "tca.malate_dh",
    "etc.complex_i", "etc.complex_ii", "etc.complex_iii", "etc.complex_iv",
])
EXPECTED_NODES = 57


# ---------------------------------------------------------------------------
# Loaders (all read-only)
# ---------------------------------------------------------------------------

def _load_json(path, label):
    # type: (str, str) -> object
    """Load a JSON file, raising ValueError with a clear label on failure."""
    if not os.path.isfile(path):
        raise ValueError("%s not found: %s" % (label, path))
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as e:
        raise ValueError("malformed %s JSON at %s: %s" % (label, path, e))


def load_story(story_dir):
    # type: (str) -> tuple
    """Load manifest + story files into (nodes, file_of, start, manifest).

    ``nodes`` is an ordered dict {id: node-dict-with-id} following the
    manifest file order (Python 3.6 dicts keep insertion order). Raises
    ValueError on a missing manifest, a malformed file, or DUPLICATE node ids
    across files.
    """
    manifest_path = os.path.join(story_dir, "manifest.json")
    if not os.path.isfile(manifest_path):
        raise ValueError("story directory %r has no manifest.json" % story_dir)
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    start = manifest.get("start")
    files = manifest.get("files") or []
    if not files:
        raise ValueError("manifest.json lists no files")
    nodes = {}  # type: dict
    file_of = {}  # type: dict
    for fname in files:
        fpath = os.path.join(story_dir, fname)
        data = _load_json(fpath, "story file %s" % fname)
        file_nodes = (data.get("nodes") or {})
        if not isinstance(file_nodes, dict):
            raise ValueError(
                "story file %s 'nodes' must be an object" % fname)
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


def load_cast(path):
    # type: (str) -> dict
    """Load cast.json into {id: entry}. OPTIONAL (display enrichment only):
    a missing or malformed file degrades to an empty lookup, never a crash."""
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


# ---------------------------------------------------------------------------
# Derivations (pinned rules -- see plan context)
# ---------------------------------------------------------------------------

def derive_kind(nid, tier, rng, edit_allowed):
    # type: (str, object, bool, bool) -> str
    """Color-class for a node; precedence first-match (pinned order):
    ending-<tier> > phase8-stub > edit-prompt > restored > rng >
    edit-allowed > story."""
    if tier is not None:
        return "ending-" + str(tier)
    if nid in STUB_IDS:
        return "phase8-stub"
    if nid == EDIT_PROMPT_ID:
        return "edit-prompt"
    if nid in RESTORED_IDS:
        return "restored"
    if rng:
        return "rng"
    if edit_allowed:
        return "edit-allowed"
    return "story"


def stage_tag_of(tags):
    # type: (list) -> object
    """First ``stage:<name>`` tag value, or None."""
    for t in tags or []:
        s = str(t)
        if s.startswith("stage:"):
            return s.split(":", 1)[1]
    return None


def effects_summary(effects):
    # type: (object) -> str
    """Human-readable one-line summary of a choice ``effects`` dict.
    e.g. {"set": {"anaerobic": true}} -> "set anaerobic=true"."""
    if not isinstance(effects, dict):
        return json.dumps(effects, sort_keys=True)
    parts = []
    for key in sorted(effects.keys()):
        val = effects[key]
        if isinstance(val, dict):
            for sub_key in sorted(val.keys()):
                parts.append("%s %s=%s" % (
                    key, sub_key, json.dumps(val[sub_key], sort_keys=True)))
        else:
            parts.append("%s %s" % (key, json.dumps(val, sort_keys=True)))
    return "; ".join(parts)


def summarize_on_enter(action):
    # type: (dict) -> str
    """Human-readable summary of one on_enter MolAction (pinned mapping).
    Unknown ops fall back to ``op <name> <compact args JSON>`` -- never crash.
    """
    try:
        op = action.get("op") or "?"
        target = action.get("target")
        args = action.get("args") or {}
        if op == "hide_all":
            return "hide all objects"
        if op == "load":
            t = str(target or "")
            for prefix in ("pdb:", "cid:"):
                if t.startswith(prefix):
                    t = t[len(prefix):]
            return "load '%s' as object '%s'" % (t, args.get("object", "?"))
        if op == "set_color":
            rgb = args.get("rgb") or []
            rgb_txt = ", ".join(
                str(int(round(float(v) * 255))) for v in list(rgb)[:3])
            return "define color '%s' = rgb(%s)" % (args.get("name"), rgb_txt)
        if op == "show_as":
            rep = args.get("rep", args.get("value", "?"))
            sele = args.get("sele")
            suffix = " [sele: %s]" % sele if sele else (
                " [%s]" % target if target else "")
            return "show as '%s'%s" % (rep, suffix)
        if op == "color":
            name = args.get("name", args.get("color", args.get("value", "?")))
            return "color '%s' = '%s'" % (target, name)
        if op == "show":
            rep = args.get("rep", args.get("value", "?"))
            sele = args.get("sele")
            suffix = " [sele: %s]" % sele if sele else (
                " [%s]" % target if target else "")
            return "show '%s'%s" % (rep, suffix)
        if op == "set":
            return "set '%s' = '%s'" % (
                args.get("name", "?"), args.get("value", "?"))
        if op == "label":
            return "label '%s' = '%s'" % (target, args.get("text", ""))
        if op == "edit":
            new_res = args.get("new_res", args.get("new_resn", "?"))
            txt = "mutate '%s' -> '%s'" % (target, new_res)
            if args.get("edit_type"):
                txt += " (%s" % args["edit_type"]
                if args.get("sele"):
                    txt += ": %s" % args["sele"]
                txt += ")"
            return txt
        if op == "align":
            mobile = args.get("mobile", target)
            return "align '%s' -> '%s' (method '%s', sele '%s')" % (
                mobile, args.get("reference"), args.get("method"),
                args.get("align_sele"))
        return "op %s %s" % (op, json.dumps(args, sort_keys=True))
    except Exception as e:  # absolute fallback -- summarizing must not crash
        return "op %s (unsummarizable: %s)" % (action.get("op", "?"), e)


# ---------------------------------------------------------------------------
# Model build (loaders -> derived per-node dicts -> layout -> edges)
# ---------------------------------------------------------------------------

def build_model(story_dir):
    # type: (str) -> dict
    """Load every source read-only and derive the full viewer payload."""
    nodes_raw, file_of, start, manifest = load_story(story_dir)
    registry = load_registry(REGISTRY_PATH)
    cast_by_id = load_cast(CAST_PATH)
    edits_doc = load_edits(EDITS_PATH)
    buckets = edits_doc.get("enzymes") or {}

    # -- column / row layout -------------------------------------------------
    col_members = {}  # type: dict
    for nid in nodes_raw:
        if nid == EDIT_PROMPT_ID:
            continue  # lifted to the top of column 5 below
        if nid in STUB_IDS:
            col = 6
        else:
            col = FILE_COL.get(file_of[nid], 6)
        col_members.setdefault(col, []).append(nid)
    # edit.prompt: hub the 15 solid edit:offer edges converge on -> row 0 of
    # the endings/bad column; its 13 choice edges fan downward within it.
    col_members.setdefault(5, [])
    if EDIT_PROMPT_ID in nodes_raw:
        col_members[5].insert(0, EDIT_PROMPT_ID)
    elif EDIT_PROMPT_ID not in nodes_raw:
        pass  # integrity check reports the missing hub

    pos = {}  # type: dict
    for col, ids in col_members.items():
        for row, nid in enumerate(ids):
            pos[nid] = (col, row)

    # -- per-node derivation --------------------------------------------------
    nodes_out = {}  # type: dict
    for nid in nodes_raw:
        raw = nodes_raw[nid]
        tags = raw.get("tags") or []
        choices = raw.get("choices") or []
        tier = raw.get("is_ending")  # the FIELD -- never derived from tags
        edit_allowed = any(
            "edit:offer" in (c.get("tags") or []) for c in choices)
        rng = "rng:weighted" in tags
        bucket = buckets.get(nid)
        cast_entry = cast_by_id.get(nid)
        col, row = pos.get(nid, (6, 0))
        node_out = {
            "id": nid,
            "col": col,
            "row": row,
            "x": X0 + col * COL_PITCH,
            "y": Y0 + row * ROW_PITCH,
            "kind": derive_kind(nid, tier, rng, edit_allowed),
            "tier": tier,
            "stage": stage_tag_of(tags),
            "segment": "seg%d" % col,
            "tags": [str(t) for t in tags],
            "text_dramatic": raw.get("text_dramatic") or "",
            "text_teaching": raw.get("text_teaching") or "",
            "claim_ids": [str(c) for c in (raw.get("claim_ids") or [])],
            "on_enter": [
                a for a in (raw.get("on_enter") or []) if isinstance(a, dict)],
            "choices": [
                {
                    "label": c.get("label") or "",
                    "goto": c.get("goto"),
                    "weight": c.get("weight"),
                    "cond": c.get("cond"),
                    "effects": c.get("effects"),
                    "tags": [str(t) for t in (c.get("tags") or [])],
                }
                for c in choices],
            "edit_allowed": edit_allowed,
            "rng": rng,
            "no_bucket": bool(edit_allowed and bucket is None),
            "bucket": None,
            "cast": None,
        }
        if bucket is not None:
            edits_list = []
            for e in (bucket.get("edits") or []):
                sig = e.get("signature") or {}
                sig_args = sig.get("args") or {}
                edits_list.append({
                    "op": sig.get("op"),
                    "target": sig.get("target"),
                    "args": sig_args,
                    "new_res": sig_args.get("new_res",
                                            sig_args.get("new_resn")),
                    "branch_node": e.get("branch_node"),
                    "claim_id": e.get("claim_id"),
                })
            node_out["bucket"] = {"edits": edits_list}
        if cast_entry is not None:
            node_out["cast"] = {
                "label": cast_entry.get("label"),
                "pdb_id": cast_entry.get("pdb_id"),
            }
        nodes_out[nid] = node_out

    # -- solid edges (choice.goto, deduped, merged annotations) ---------------
    solid_edges = _build_solid_edges(nodes_raw, nodes_out, pos)

    # -- dashed edges (known-edit routing) ------------------------------------
    dashed_edges = _build_dashed_edges(nodes_out, buckets)

    # -- review order (pinned 07-18 sequence) ---------------------------------
    review_order = _compute_review_order(col_members, nodes_raw, file_of)

    # -- counts (all DERIVED; printed, and asserted only where pinned) --------
    tier_counts = {"true": 0, "good": 0, "normal": 0, "bad": 0}
    for n in nodes_out.values():
        if n["tier"] in tier_counts:
            tier_counts[n["tier"]] += 1
    edit_allowed_ids = sorted(
        nid for nid, n in nodes_out.items() if n["edit_allowed"])
    pending_ids = sorted(
        cid for cid, rec in registry.items()
        if isinstance(rec, dict) and rec.get("approval_status") == "pending")
    approved_n = sum(
        1 for rec in registry.values()
        if isinstance(rec, dict) and rec.get("approval_status") == "approved")
    claims_payload = {}
    for cid, rec in registry.items():
        if not isinstance(rec, dict):
            continue
        claims_payload[cid] = {
            "claim": rec.get("claim"),
            "claim_text": rec.get("claim_text"),
            "source_id": rec.get("source_id"),
            "review_tier": rec.get("review_tier"),
            "approval_status": rec.get("approval_status"),
        }
    no_bucket_ids = sorted(
        nid for nid, n in nodes_out.items() if n["no_bucket"])

    payload = {
        "title": "RPG: Tale of C \u2014 Glucose Story Graph (Phase 7 review)",
        "start": start,
        "segments": [
            {"key": "seg%d" % col, "label": COL_LABELS[col], "col": col}
            for col in range(N_COLS)],
        "col_labels": [COL_LABELS[col] for col in range(N_COLS)],
        "col_counts": [len(col_members.get(col, []))
                       for col in range(N_COLS)],
        "nodes": nodes_out,
        "order": list(nodes_out.keys()),
        "solid_edges": solid_edges,
        "dashed_edges": dashed_edges,
        "claims": claims_payload,
        "review_order": review_order,
        "counts": {
            "nodes": len(nodes_out),
            "endings": sum(tier_counts.values()),
            "endings_by_tier": tier_counts,
            "edit_allowed": len(edit_allowed_ids),
            "buckets": len(buckets),
            "claims": len(claims_payload),
            "approved": approved_n,
            "pending": len(pending_ids),
            "solid_edges": len(solid_edges),
            "dashed_edges": len(dashed_edges),
        },
    }
    # Diagnostics attached for the integrity check + stdout (not asserted
    # except where the plan pins a hard gate).
    payload["_diag"] = {
        "edit_allowed_ids": edit_allowed_ids,
        "pending_ids": pending_ids,
        "no_bucket_ids": no_bucket_ids,
        "tier_counts": tier_counts,
        "bucket_ids": sorted(buckets.keys()),
    }
    return payload


def _build_solid_edges(nodes_raw, nodes_out, pos):
    # type: (dict, dict, dict) -> list
    """Deduped choice.goto edges with merged choice annotations."""
    pairs = {}  # type: dict
    order = []  # type: list
    for nid in nodes_raw:
        for c in (nodes_raw[nid].get("choices") or []):
            goto = c.get("goto")
            if not goto:
                continue
            key = (nid, goto)
            if key not in pairs:
                pairs[key] = {
                    "src": nid, "dst": goto, "labels": [], "weights": [],
                    "conds": [], "effects": [], "choice_tags": [], "count": 0,
                }
                order.append(key)
            rec = pairs[key]
            rec["count"] += 1
            label = (c.get("label") or "").strip()
            if label and label not in rec["labels"]:
                rec["labels"].append(label)
            if c.get("weight") is not None:
                rec["weights"].append(c["weight"])
            cond = c.get("cond")
            if cond and cond not in rec["conds"]:
                rec["conds"].append(cond)
            if c.get("effects"):
                eff = effects_summary(c.get("effects"))
                if eff and eff not in rec["effects"]:
                    rec["effects"].append(eff)
            for t in (c.get("tags") or []):
                t = str(t)
                if t not in rec["choice_tags"]:
                    rec["choice_tags"].append(t)

    up_counter = {}  # type: dict
    back_count = 0
    out = []
    fan_count = 0
    for key in order:
        rec = pairs[key]
        src, dst = key
        sc, sr = pos[src]
        tc, tr = pos[dst]
        if src == EDIT_PROMPT_ID:
            # edit.prompt hub -> bad-ending pool: route the 13 structural
            # choices through the right gutter (fan) so they stay visible
            # beside the ending boxes they would otherwise run under.
            geo = "fan"
            bow = 1662 + 6 * fan_count
            fan_count += 1
        elif tc > sc:
            geo, bow = "fwd", 0
        elif tc == sc and tr > sr:
            geo, bow = "down", 0
        elif tc == sc:
            geo = "up"
            bow = 46 + 34 * up_counter.get(sc, 0)
            up_counter[sc] = up_counter.get(sc, 0) + 1
        else:
            geo = "back"
            bow = 110 + 55 * back_count
            back_count += 1
        shared_weight = None
        if rec["weights"] and len(set(rec["weights"])) == 1:
            shared_weight = rec["weights"][0]
        rec_out = {
            "src": src,
            "dst": dst,
            "labels": rec["labels"],
            "count": rec["count"],
            "weight": shared_weight,
            "conds": rec["conds"],
            "effects": rec["effects"],
            "choice_tags": rec["choice_tags"],
            "geo": geo,
            "bow": bow,
        }
        out.append(rec_out)
    return out


def _build_dashed_edges(nodes_out, buckets):
    # type: (dict, dict) -> list
    """One dashed edge per edits.json edit entry: enzyme -> branch_node."""
    out = []
    for bucket_id in buckets:
        bucket = buckets[bucket_id] or {}
        for e in (bucket.get("edits") or []):
            sig = e.get("signature") or {}
            sig_args = sig.get("args") or {}
            new_res = sig_args.get("new_res", sig_args.get("new_resn"))
            branch = e.get("branch_node")
            sig_txt = "%s %s -> %s" % (sig.get("op"), sig.get("target"),
                                       new_res)
            out.append({
                "src": bucket_id,
                "dst": branch,
                "op": sig.get("op"),
                "target": sig.get("target"),
                "new_res": new_res,
                "claim_id": e.get("claim_id"),
                "sig_text": sig_txt,
            })
    return out


def _compute_review_order(col_members, nodes_raw, file_of):
    # type: (dict, dict, dict) -> list
    """Pinned 07-18 review sequence:
    col0 intro (3) -> col1 glycolysis (7) -> col2 pyruvate/anaerobic (7)
    -> col3 TCA (13) -> col4 ETC (7, end.true last) -> endings.json (3)
    -> edit.prompt -> bad pool (14, file order) -> Phase-8 stubs (2) = 57."""
    order = []
    for col in (0, 1, 2, 3, 4):
        order.extend(col_members.get(col, []))
    endings = [nid for nid in col_members.get(5, [])
               if file_of.get(nid) == "endings.json"]
    bad_pool = [nid for nid in col_members.get(5, [])
                if file_of.get(nid) == "bad_endings.json"
                and nid != EDIT_PROMPT_ID]
    order.extend(endings)
    if EDIT_PROMPT_ID in nodes_raw:
        order.append(EDIT_PROMPT_ID)
    order.extend(bad_pool)
    order.extend(col_members.get(6, []))
    return order


# ---------------------------------------------------------------------------
# Integrity self-check (hard gates; exit 1 + no HTML on ANY violation)
# ---------------------------------------------------------------------------

def check_integrity(model):
    # type: (dict) -> list
    """Return a list of numbered failure strings (empty == all gates pass)."""
    failures = []  # type: list
    nodes = model["nodes"]
    diag = model["_diag"]

    # 1. Node count + uniqueness (loader already raises on duplicates).
    if len(nodes) != EXPECTED_NODES:
        failures.append("(1) expected %d nodes, derived %d" % (
            EXPECTED_NODES, len(nodes)))

    # 2. Ending tiers come from the is_ending FIELD (never from tags).
    tier_counts = diag["tier_counts"]
    if tier_counts != EXPECTED_TIER_COUNTS:
        failures.append(
            "(2) is_ending tier counts mismatch: expected %s, derived %s"
            % (EXPECTED_TIER_COUNTS, tier_counts))

    # 3. Edit-allowed set == the 15 pinned ids.
    ea = set(diag["edit_allowed_ids"])
    if ea != set(EXPECTED_EDIT_ALLOWED):
        missing = sorted(set(EXPECTED_EDIT_ALLOWED) - ea)
        extra = sorted(ea - set(EXPECTED_EDIT_ALLOWED))
        failures.append(
            "(3) edit-allowed set mismatch (missing=%s, unexpected=%s)"
            % (missing, extra))

    # 4. Exactly one RNG node == tca.shuffle.
    rng_ids = sorted(nid for nid, n in nodes.items() if n["rng"])
    if rng_ids != [RNG_NODE_ID]:
        failures.append(
            "(4) expected exactly one rng node %r, derived %s"
            % (RNG_NODE_ID, rng_ids))

    # 5. Every goto / branch_node / bucket id resolves.
    bad_goto = []
    for e in model["solid_edges"]:
        if e["dst"] not in nodes:
            bad_goto.append("%s -> %s" % (e["src"], e["dst"]))
    if bad_goto:
        failures.append(
            "(5a) choice.goto targets not resolving to nodes: %s" % bad_goto)
    bad_branch = []
    for e in model["dashed_edges"]:
        if e["dst"] not in nodes:
            bad_branch.append("%s -> %s" % (e["src"], e["dst"]))
    if bad_branch:
        failures.append(
            "(5b) edits.json branch_node targets not resolving: %s"
            % bad_branch)
    bad_bucket = sorted(
        bid for bid in model["_diag"]["bucket_ids"] if bid not in nodes)
    if bad_bucket:
        failures.append(
            "(5c) edits.json bucket ids not resolving to enzyme nodes: %s"
            % bad_bucket)

    # 6. Claim resolution + PLACEHOLDER_PHASE8 pairing (fa.stub / alc.stub).
    bad_claims = []
    for nid, n in nodes.items():
        for cid in n["claim_ids"]:
            if cid != PLACEHOLDER_CLAIM and cid not in model["claims"]:
                bad_claims.append("%s: %s" % (nid, cid))
    if bad_claims:
        failures.append(
            "(6a) node claim_ids missing from the registry: %s" % bad_claims)
    ph_nodes = sorted(
        nid for nid, n in nodes.items()
        if PLACEHOLDER_CLAIM in n["claim_ids"])
    if sorted(STUB_IDS) != ph_nodes:
        failures.append(
            "(6b) %s must appear on exactly %s, found on %s"
            % (PLACEHOLDER_CLAIM, sorted(STUB_IDS), ph_nodes))
    if PLACEHOLDER_CLAIM in model["claims"]:
        failures.append(
            "(6c) %s must NOT exist in the citation registry"
            % PLACEHOLDER_CLAIM)

    # 7. Buckets (13) subset of edit:enzyme:* tag ids (14);
    #    difference == {tca.citrate_synthase}.
    tag_ids = set()
    for n in nodes.values():
        for t in n["tags"]:
            if t.startswith("edit:enzyme:"):
                tag_ids.add(t.split(":", 2)[2])
    bucket_ids = set(model["_diag"]["bucket_ids"])
    if not bucket_ids.issubset(tag_ids):
        failures.append(
            "(7a) bucket ids lacking an edit:enzyme: tag: %s"
            % sorted(bucket_ids - tag_ids))
    diff = tag_ids - bucket_ids
    if diff != {"tca.citrate_synthase"}:
        failures.append(
            "(7b) edit:enzyme: tag ids minus buckets expected "
            "{'tca.citrate_synthase'}, got %s" % sorted(diff))

    # 8. cast ids subset of bucket ids.
    cast_ids = set(
        n["id"] for n in nodes.values() if n["cast"] is not None)
    if not cast_ids.issubset(bucket_ids):
        failures.append(
            "(8) cast entries without an edits.json bucket: %s"
            % sorted(cast_ids - bucket_ids))

    # 9. Restored nodes: ROUTER-ONLY invariant -- zero incoming choice.goto.
    incoming = {}
    for e in model["solid_edges"]:
        incoming[e["dst"]] = incoming.get(e["dst"], 0) + 1
    for rid in RESTORED_IDS:
        if rid in nodes and incoming.get(rid, 0) != 0:
            failures.append(
                "(9) restored node %r has %d incoming choice.goto edge(s); "
                "router-only invariant requires 0" % (rid, incoming[rid]))

    # 10. Approval statuses well-formed; the approved/pending split is
    #     PRINTED by the caller, never asserted (07-18 may flip BAD-*).
    bad_status = sorted(
        cid for cid, rec in model["claims"].items()
        if rec.get("approval_status") not in ("approved", "pending"))
    if bad_status:
        failures.append(
            "(10) claims with an approval_status outside "
            "{'approved','pending'}: %s" % bad_status)

    return failures


# ---------------------------------------------------------------------------
# Static SVG rendering (nodes + edges are generated server-side so the HTML
# carries the 57 data-node-id groups even before JS boots; the inlined JS
# only adds interactivity: pan/zoom/drag, reading panel, search/filter/
# review-order. Edge geometry here is mirrored EXACTLY by the JS.)
# ---------------------------------------------------------------------------

def _esc(text):
    # type: (object) -> str
    """XML-escape dynamic text for embedding in the SVG markup."""
    return html.escape(str(text), quote=True)


def _trunc_id(nid):
    # type: (str) -> str
    """Node label: full id, truncated >22 chars with an ellipsis."""
    if len(nid) <= 22:
        return nid
    return nid[:21] + "\u2026"


def _flat_110(text):
    # type: (str) -> str
    """Whitespace-flattened first ~110 chars of a story text (tooltip)."""
    flat = " ".join(str(text).split())
    if len(flat) <= 110:
        return flat
    return flat[:110] + "\u2026"


def render_svg_defs():
    # type: () -> str
    """Arrowhead markers (grey solid / amber dashed) + the stub hatch."""
    return (
        '<defs>'
        '<marker id="arrow-solid" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#666666"/></marker>'
        '<marker id="arrow-amber" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#d97706"/></marker>'
        '<pattern id="hatch" width="8" height="8" '
        'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="8" height="8" fill="#cccccc"/>'
        '<line x1="0" y1="0" x2="0" y2="8" stroke="#a8a8a8" '
        'stroke-width="3"/></pattern>'
        '</defs>')


def _edge_geometry(n_src, n_dst, geo, bow, dashed):
    # type: (dict, dict, str, float, bool) -> tuple
    """Return (path_d, label_x, label_y, label_anchor) for an edge.

    Mirrored by edgeD()/labelPos() in the template JS so drag/redraw and
    Reset layout reproduce the generator geometry:
    - down: same column, target below -> straight vertical spine.
    - fwd:  target column to the right -> horizontal bezier,
            src right-center -> dst left-center (pinned form).
    - up:   same column, target above -> right-side bow (cycle back-edges;
            bow = extra x offset, incremented per column).
    - fan:  edit.prompt hub -> right-gutter fan down to each bad ending
            (bow = absolute gutter x; keeps the 13 structural edges visible
            beside the ending boxes they would otherwise run under).
    - back: target column to the left -> wide arc over the top (bow = lift).
    Dashed (known-edit) edges carry a +56px perpendicular curvature offset so
    the 11 dashed/solid overlapping pairs stay visible (07-14 convention).
    """
    w = float(NODE_W)
    h = float(NODE_H)
    sx = float(n_src["x"])
    sy = float(n_src["y"])
    tx = float(n_dst["x"])
    ty = float(n_dst["y"])
    scx = sx + w / 2.0
    scy = sy + h / 2.0
    tcx = tx + w / 2.0
    tcy = ty + h / 2.0
    k = 45.0
    if geo == "down":
        x1 = scx
        y1 = sy + h
        x2 = tcx
        y2 = ty
        ym = (y1 + y2) / 2.0
        if dashed:
            d = "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" % (
                x1 + 18, y1, x1 + 58, ym, x2 + 58, ym, x2 + 42, y2)
            return d, x1 + 52, ym, "start"
        d = "M %.1f %.1f L %.1f %.1f" % (x1, y1, x2, y2)
        return d, x1 + 12, ym + 4, "start"
    if geo == "fwd":
        x1 = sx + w
        y1 = scy
        x2 = tx
        y2 = tcy
        dx = x2 - x1
        dy = y2 - y1
        ln = math.sqrt(dx * dx + dy * dy) or 1.0
        ux = dx / ln
        uy = dy / ln
        if dashed:
            px = uy * 56.0
            py = -ux * 56.0
            cx1 = x1 + k * ux + px
            cy1 = y1 + k * uy + py
            cx2 = x2 - k * ux + px
            cy2 = y2 - k * uy + py
            d = "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" % (
                x1, y1, cx1, cy1, cx2, cy2, x2, y2)
            mx = (x1 + 3 * cx1 + 3 * cx2 + x2) / 8.0
            my = (y1 + 3 * cy1 + 3 * cy2 + y2) / 8.0
            return d, mx, my - 4, "middle"
        d = "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" % (
            x1, y1, x1 + k, y1, x2 - k, y2, x2, y2)
        return d, (x1 + x2) / 2.0, (y1 + y2) / 2.0 - 6, "middle"
    if geo == "up":
        x1 = sx + w
        y1 = scy
        x2 = tx + w
        y2 = tcy
        d = "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" % (
            x1, y1, x1 + bow, y1, x2 + bow, y2, x2, y2)
        return d, (x1 + x2) / 2.0 + bow * 0.75, (y1 + y2) / 2.0 - 4, "middle"
    if geo == "fan":
        gx = float(bow)
        d = "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" % (
            sx + w, scy, gx, scy, gx, tcy, tx + w, tcy)
        return d, gx, (scy + tcy) / 2.0, "middle"
    # "back": wide arc over the top of the canvas.
    yc = min(sy, ty) - bow
    d = "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" % (
        scx, sy, scx, yc, tcx, yc, tcx, ty)
    return d, (scx + tcx) / 2.0, yc - 4, "middle"


def _dashed_geo(model, e):
    # type: (dict, dict) -> str
    """Geometry class for a dashed edge (same rules as solid; the pair may
    coincide with a solid edge -- those are the 11 overlap pairs)."""
    src = model["nodes"][e["src"]]
    dst = model["nodes"][e["dst"]]
    if dst["col"] > src["col"]:
        return "fwd"
    if dst["col"] == src["col"] and dst["row"] > src["row"]:
        return "down"
    if dst["col"] == src["col"]:
        return "up"
    return "back"


def _solid_title(e):
    # type: (dict) -> str
    """Tooltip for a deduped solid edge (merged choice annotations)."""
    lines = ["%s -> %s" % (e["src"], e["dst"]),
             "choices (%d): %s" % (e["count"], " | ".join(e["labels"]))]
    if e["weight"] is not None:
        lines.append("weight: %g (all merged choices)" % e["weight"])
    if e["conds"]:
        lines.append("cond: %s" % " AND ".join(e["conds"]))
    if e["effects"]:
        lines.append("effects: %s" % "; ".join(e["effects"]))
    if e["choice_tags"]:
        lines.append("choice tags: %s" % ", ".join(e["choice_tags"]))
    return "\n".join(lines)


def render_svg_edges(model):
    # type: (dict) -> str
    """Solid choice.goto edges + amber dashed known-edit routes + labels.
    Rendered BEFORE the nodes group so edges sit UNDER the nodes."""
    nodes = model["nodes"]
    parts = []
    n_solid = len(model["solid_edges"])
    for i, e in enumerate(model["solid_edges"]):
        d, lx, ly, anchor = _edge_geometry(
            nodes[e["src"]], nodes[e["dst"]], e["geo"], e["bow"], False)
        parts.append(
            '<path class="edge-solid" data-eidx="%d" d="%s" '
            'marker-end="url(#arrow-solid)"><title>%s</title></path>'
            % (i, d, _esc(_solid_title(e))))
        label = None
        if e["weight"] is not None:
            label = "w=%g" % e["weight"]
        elif e["conds"]:
            label = "cond"
        if label:
            parts.append(
                '<text class="edge-midlabel%s" data-eidx="%d" x="%.1f" '
                'y="%.1f" text-anchor="%s">%s</text>'
                % (" cond-label" if label == "cond" else "",
                   i, lx, ly, anchor, _esc(label)))
    for j, e in enumerate(model["dashed_edges"]):
        d, lx, ly, anchor = _edge_geometry(
            nodes[e["src"]], nodes[e["dst"]], _dashed_geo(model, e), 0, True)
        title = "known edit: %s | claim %s | routes to %s" % (
            e["sig_text"].replace(" -> ", " \u2192 "),
            e["claim_id"] or "\u2014", e["dst"])
        parts.append(
            '<path class="edge-dashed" data-eidx="%d" d="%s" '
            'marker-end="url(#arrow-amber)"><title>%s</title></path>'
            % (n_solid + j, d, _esc(title)))
    return "\n".join(parts)


def _node_pending(n, claims):
    # type: (dict, dict) -> bool
    """True iff the node carries >=1 registry claim whose approval_status
    is pending (PLACEHOLDER_PHASE8 never counts)."""
    for cid in n["claim_ids"]:
        if cid == PLACEHOLDER_CLAIM:
            continue
        rec = claims.get(cid) or {}
        if rec.get("approval_status") == "pending":
            return True
    return False


def render_svg_nodes(model):
    # type: (dict) -> str
    """One <g class="node kind-... has-claims ..." data-node-id=...> per
    node, in layout order. Claims-outline classes are baked in statically
    from the generation-time registry."""
    claims = model["claims"]
    parts = []
    for nid in model["order"]:
        n = model["nodes"][nid]
        kind = n["kind"]
        has_claims = bool(n["claim_ids"])
        pending = _node_pending(n, claims)
        title = "\n".join([
            nid,
            "kind: %s | tier: %s | col %d row %d" % (
                kind, n["tier"] if n["tier"] else "\u2014",
                n["col"], n["row"]),
            _flat_110(n["text_dramatic"])])
        chunks = [
            '<g class="node kind-%s%s%s" data-node-id="%s" '
            'transform="translate(%d,%d)">' % (
                kind,
                " has-claims" if has_claims else "",
                " pending-yes" if pending else "",
                _esc(nid), n["x"], n["y"])]
        if kind == "restored":
            # Double-border effect (router-only restored nodes).
            chunks.append(
                '<rect class="node-outer" x="-5" y="-5" width="%d" '
                'height="%d" rx="11"/>' % (NODE_W + 10, NODE_H + 10))
        chunks.append(
            '<rect class="node-box" width="%d" height="%d" rx="8"/>' % (
                NODE_W, NODE_H))
        if kind == "phase8-stub":
            chunks.append(
                '<text class="node-label" x="%d" y="34">%s</text>'
                % (NODE_W // 2, _esc(_trunc_id(nid))))
            chunks.append(
                '<text class="node-badge" x="%d" y="56" '
                'text-anchor="middle">Phase-8 stub</text>'
                % (NODE_W // 2))
        else:
            chunks.append(
                '<text class="node-label" x="%d" y="%d">%s</text>'
                % (NODE_W // 2, NODE_H // 2 + 5, _esc(_trunc_id(nid))))
        chunks.append("<title>%s</title>" % _esc(title))
        chunks.append("</g>")
        parts.append("".join(chunks))
    return "\n".join(parts)


def render_svg_headers(model):
    # type: (dict) -> str
    """Column header captions with derived counts."""
    parts = []
    for col in range(N_COLS):
        parts.append(
            '<text class="col-header" x="%d" y="64">%s (%d)</text>'
            % (X0 + col * COL_PITCH, _esc(COL_LABELS[col]),
               model["col_counts"][col]))
    return "\n".join(parts)




# ---------------------------------------------------------------------------
# HTML assembly (template + inlined payload; str.replace ONLY -- .format
# would explode on the JS/CSS braces)
# ---------------------------------------------------------------------------

def render_html(model):
    # type: (dict) -> str
    """Substitute the tokens and return the self-contained HTML string.

    The payload is inlined as <script id="story-data" type="application/
    json"> with ensure_ascii=True (7-bit safe over file://) and every '</'
    escaped to '<\\/' so a '</script>' sequence inside story text can never
    break out of the data block.
    """
    data_json = json.dumps(model, ensure_ascii=True).replace("</", "<\\/")
    return (HTML_TEMPLATE
            .replace("__TITLE__", _esc(model["title"]))
            .replace("__SVG_DEFS__", render_svg_defs())
            .replace("__SVG_EDGES__", render_svg_edges(model))
            .replace("__SVG_NODES__", render_svg_nodes(model))
            .replace("__SVG_HEADERS__", render_svg_headers(model))
            .replace("__STORY_DATA_JSON__", data_json))


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; height: 100%; font-family: "Segoe UI", Arial, Helvetica, sans-serif; font-size: 14px; color: #222; }
body { display: flex; flex-direction: column; }
header { padding: 8px 14px 6px; border-bottom: 2px solid #3a3f4b; background: #f5f6f8; flex: none; }
#title-row { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
h1 { font-size: 19px; margin: 0; }
#counts-badge { font-size: 12px; background: #2e3440; color: #fff; padding: 3px 10px; border-radius: 12px; }
#desc { margin: 4px 0 6px; font-size: 12.5px; color: #555; }
#controls-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
#search { width: 250px; padding: 4px 8px; font-size: 13px; border: 1px solid #b9c0cc; border-radius: 4px; }
#match-count { font-size: 12px; color: #666; min-width: 80px; }
button { padding: 4px 10px; font-size: 12.5px; border: 1px solid #9aa3b2; background: #fff; border-radius: 4px; cursor: pointer; }
button:hover { background: #e8ecf3; }
button.active { background: #2e3440; color: #fff; border-color: #2e3440; }
.seg-label { font-size: 12px; color: #666; margin-left: 6px; }
#legend { display: flex; flex-wrap: wrap; gap: 4px 14px; margin-top: 7px; font-size: 11.5px; align-items: center; color: #444; }
.leg-item { display: inline-flex; align-items: center; gap: 5px; }
.swatch { display: inline-block; width: 20px; height: 13px; border-radius: 3px; border: 1px solid #888; }
.leg-line { display: inline-block; width: 30px; height: 0; border-top: 2px solid #666; }
.leg-line.dashed { border-top: 2px dashed #d97706; }
#main { flex: 1; display: flex; min-height: 0; }
#graph-wrap { flex: 1; position: relative; min-width: 0; background: #fbfcfe; overflow: hidden; }
#graph { width: 100%; height: 100%; display: block; cursor: grab; }
#graph.panning { cursor: grabbing; }
#reading-panel { width: 380px; flex: none; border-left: 2px solid #3a3f4b; background: #fff; overflow-y: auto; padding: 10px 12px 16px; }
#panel-head { border-bottom: 1px solid #ddd; padding-bottom: 6px; margin-bottom: 8px; }
#rp-id { font: bold 15px Consolas, monospace; word-break: break-all; }
.badge { display: inline-block; font-size: 11px; padding: 2px 7px; border-radius: 9px; margin: 4px 4px 0 0; background: #e8ecf3; color: #444; }
.badge.tier-true { background: #c9a227; color: #fff; }
.badge.tier-good { background: #2e8b57; color: #fff; }
.badge.tier-normal { background: #4682b4; color: #fff; }
.badge.tier-bad { background: #b22222; color: #fff; }
.badge.kind-badge { background: #3a3f4b; color: #fff; }
.sec-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #888; margin: 12px 0 4px; border-bottom: 1px solid #eee; padding-bottom: 2px; }
.muted { color: #999; font-size: 12px; }
#rp-dramatic { font-size: 13.5px; line-height: 1.5; border-left: 4px solid #c9a227; background: #fdf9ee; margin: 8px 0; padding: 8px 10px; font-style: italic; }
#rp-teaching { font-size: 13px; line-height: 1.55; color: #333; margin: 8px 0; }
.tag-chip, .mini-chip { display: inline-block; font: 11px Consolas, monospace; background: #eef1f6; border: 1px solid #ccd3de; border-radius: 3px; padding: 1px 5px; margin: 2px 3px 2px 0; }
.mini-chip { background: #f6f2fb; border-color: #d8c9ee; color: #5b3a8e; }
.choice-row { margin: 7px 0; padding: 6px 8px; background: #f7f9fc; border: 1px solid #e3e8f0; border-radius: 5px; font-size: 12.5px; }
.choice-row a, .bucket-table a, .bucket-route a { color: #1f6feb; font-family: Consolas, monospace; font-size: 12px; cursor: pointer; }
.choice-ann { display: inline-block; font-size: 11px; color: #4a7a2a; margin-right: 6px; font-family: Consolas, monospace; }
.choice-ann.cond-ann { color: #a33; }
.onenter-list { margin: 2px 0; padding-left: 18px; font-size: 12px; font-family: Consolas, monospace; color: #445; }
.onenter-list li { margin: 2px 0; }
.claim-chip { display: inline-block; font: 11px Consolas, monospace; border-radius: 10px; padding: 2px 9px; margin: 2px 4px 2px 0; cursor: pointer; }
.claim-approved { background: #e2f4e8; border: 1px solid #2e8b57; color: #1d5c3a; }
.claim-pending { background: #fdf0dd; border: 1px solid #d97706; color: #8a4b06; }
.claim-placeholder { background: #eee; border: 1px dashed #999; color: #666; }
.claim-detail { display: none; font-size: 12px; background: #f4f6f9; border: 1px solid #dde3ec; border-radius: 4px; padding: 6px 8px; margin: 4px 0; line-height: 1.45; }
.claim-detail.open { display: block; }
.bucket-table { border-collapse: collapse; font-size: 11.5px; width: 100%; }
.bucket-table th, .bucket-table td { border: 1px solid #d8dde6; padding: 3px 6px; text-align: left; }
.bucket-table th { background: #eef1f6; }
.bucket-route { font-size: 12px; color: #8a4b06; margin-top: 4px; }
.no-bucket-note { font-size: 12px; color: #666; background: #f4f6f9; padding: 6px 8px; border-radius: 4px; }
.cast-line { font-size: 12.5px; color: #2f5a7d; margin-top: 4px; }
.stub-note { font-size: 12px; color: #666; background: #f1f1f1; border: 1px dashed #999; padding: 5px 8px; border-radius: 4px; margin: 6px 0; }
#panel-nav { position: sticky; bottom: 0; background: #fff; border-top: 2px solid #3a3f4b; padding: 8px 0 2px; display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 14px; }
#panel-pos { font: 12px Consolas, monospace; color: #555; }
.col-header { font: bold 14px "Segoe UI", Arial, sans-serif; fill: #444; }
.node { cursor: pointer; }
.node-label { font: 11px Consolas, monospace; text-anchor: middle; fill: #1a1a1a; paint-order: stroke; stroke: #fff; stroke-width: 3px; stroke-linejoin: round; }
.node-badge { font: 9px "Segoe UI", Arial, sans-serif; fill: #555; text-anchor: middle; }
.kind-ending-true .node-box { fill: #c9a227; stroke: #8a6d1a; }
.kind-ending-good .node-box { fill: #2e8b57; stroke: #1d5c3a; }
.kind-ending-normal .node-box { fill: #4682b4; stroke: #2f5a7d; }
.kind-ending-bad .node-box { fill: #b22222; stroke: #7a1717; }
.kind-restored .node-box { fill: #e6e0f5; stroke: #6a4fc1; stroke-width: 1.5; }
.kind-restored .node-outer { fill: none; stroke: #6a4fc1; stroke-width: 3; }
.kind-edit-prompt .node-box { fill: #f5c16c; stroke: #a8791f; }
.kind-phase8-stub .node-box { fill: url(#hatch); stroke: #888; }
.kind-rng .node-box { fill: #17a2b8; stroke: #0e6d78; }
.kind-edit-allowed .node-box { fill: #f0e6ff; stroke: #8a2be2; stroke-width: 2; }
.kind-story .node-box { fill: #dfe7ef; stroke: #9fb2c4; }
.kind-ending-true .node-label, .kind-ending-good .node-label, .kind-ending-normal .node-label, .kind-ending-bad .node-label, .kind-rng .node-label { fill: #fff; stroke: rgba(0,0,0,0.35); }
.node.selected .node-box { stroke: #1f6feb; stroke-width: 3.5; }
.node.review-current .node-box { stroke: #e25822; stroke-width: 4.5; }
.node.review-current .node-outer { stroke: #e25822; }
.node.dimmed { opacity: 0.15; }
.node.review-dim { opacity: 0.3; }
.edge-solid { stroke: #666666; stroke-width: 1.5; fill: none; }
.edge-dashed { stroke: #d97706; stroke-width: 2; stroke-dasharray: 7 5; fill: none; }
.edge-midlabel { font: 10px "Segoe UI", Arial, sans-serif; fill: #444; paint-order: stroke; stroke: #fff; stroke-width: 3px; stroke-linejoin: round; }
.edge-midlabel.cond-label { fill: #a33; }
.edge-dim { opacity: 0.15; }
svg.claims-on .node.has-claims .node-box { stroke: #1e9e50; stroke-width: 2.5; }
svg.claims-on .node.pending-yes .node-box { stroke: #d97706; stroke-width: 3.5; }
</style>
</head>
<body>
<header>
  <div id="title-row">
    <h1>__TITLE__</h1>
    <span id="counts-badge"></span>
  </div>
  <p id="desc">Interactive review of the Phase 7 glucose story graph &mdash; solid = choice.goto, amber dashed = known-edit routing (edits.json), click a node for the full two-layer story.</p>
  <div id="controls-row">
    <input id="search" type="text" placeholder="Search id / story text / tags (Esc clears)">
    <span id="match-count"></span>
    <span class="seg-label">Segment:</span>
    <button class="seg-btn active" data-seg="all">All</button>
    <button class="seg-btn" data-seg="seg0">Intro</button>
    <button class="seg-btn" data-seg="seg1">Glycolysis</button>
    <button class="seg-btn" data-seg="seg2">Pyruvate+Anaerobic</button>
    <button class="seg-btn" data-seg="seg3">TCA</button>
    <button class="seg-btn" data-seg="seg4">ETC</button>
    <button class="seg-btn" data-seg="seg5">Endings+Bad pool</button>
    <button class="seg-btn" data-seg="seg6">Phase-8 stubs</button>
    <button id="btn-review" title="Walk the pinned 07-18 review order">Review order</button>
    <button id="btn-claims" title="Outline claim-bearing nodes (green) / pending-claim nodes (amber)">Claims</button>
    <button id="btn-endtrue" title="Jump to the True ending (soul-jump)">end.true</button>
    <button id="btn-fit">Fit view</button>
    <button id="btn-reset">Reset layout</button>
  </div>
  <div id="legend">
    <span class="leg-item"><span class="swatch" style="background:#c9a227"></span>ending-true</span>
    <span class="leg-item"><span class="swatch" style="background:#2e8b57"></span>ending-good</span>
    <span class="leg-item"><span class="swatch" style="background:#4682b4"></span>ending-normal</span>
    <span class="leg-item"><span class="swatch" style="background:#b22222"></span>ending-bad</span>
    <span class="leg-item"><span class="swatch" style="background:#e6e0f5; border:2px double #6a4fc1"></span>restored (router-only)</span>
    <span class="leg-item"><span class="swatch" style="background:#f5c16c"></span>edit.prompt hub</span>
    <span class="leg-item"><span class="swatch" style="background:repeating-linear-gradient(45deg,#cccccc,#cccccc 3px,#b6b6b6 3px,#b6b6b6 6px)"></span>Phase-8 stub</span>
    <span class="leg-item"><span class="swatch" style="background:#17a2b8"></span>RNG shuffle</span>
    <span class="leg-item"><span class="swatch" style="background:#f0e6ff; border-color:#8a2be2"></span>edit-allowed</span>
    <span class="leg-item"><span class="swatch" style="background:#dfe7ef"></span>story</span>
    <span class="leg-item"><span class="leg-line"></span>solid = player choice</span>
    <span class="leg-item"><span class="leg-line dashed"></span>amber dashed = known-edit route (restored nodes are reached ONLY this way)</span>
    <span class="leg-item"><b>w=0.5</b>&nbsp;= RNG-weighted</span>
    <span class="leg-item"><b>cond</b>&nbsp;= conditional choice</span>
  </div>
</header>
<div id="main">
  <div id="graph-wrap">
    <svg id="graph" width="2000" height="1900" xmlns="http://www.w3.org/2000/svg">
      __SVG_DEFS__
      <g id="world" transform="translate(0,0) scale(1)">
        <g id="colheads">__SVG_HEADERS__</g>
        <g id="edges">__SVG_EDGES__</g>
        <g id="nodes">__SVG_NODES__</g>
      </g>
    </svg>
  </div>
  <aside id="reading-panel">
    <div id="panel-body"><div class="muted">Click any node to read its full two-layer story.</div></div>
    <div id="panel-nav">
      <button id="btn-prev">&larr; Prev</button>
      <span id="panel-pos">&mdash; / 57</span>
      <button id="btn-next">Next &rarr;</button>
    </div>
  </aside>
</div>
<script id="story-data" type="application/json">__STORY_DATA_JSON__</script>
<script>
(function () {
  'use strict';
  var DATA = JSON.parse(document.getElementById('story-data').textContent);
  var NODES = DATA.nodes;
  var CLAIMS = DATA.claims;
  var PH = 'PLACEHOLDER_PHASE8';
  var svg = document.getElementById('graph');
  var world = document.getElementById('world');
  var panelBody = document.getElementById('panel-body');
  var searchInput = document.getElementById('search');
  var matchCount = document.getElementById('match-count');
  var btnReview = document.getElementById('btn-review');
  var btnClaims = document.getElementById('btn-claims');
  var W = 190, H = 68;

  var state = { tx: 0, ty: 0, scale: 1 };
  var pos = {};          // id -> live {x, y}; in-memory only, Reset restores
  var nodeEls = {};      // id -> node group element
  var edgeEls = [];      // {path, rec, dashed, labels}
  var selectedId = null;
  var searchQ = '';
  var seg = 'all';
  var reviewMode = false;
  var reviewPos = 0;
  var reviewList = DATA.review_order;
  var reviewIdxById = {};
  var drag = null;
  var animReq = null;
  var litMap = {};

  function esc(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function fmt(v) { return Math.round(v * 100) / 100; }

  // ---- indexes -----------------------------------------------------------
  Object.keys(NODES).forEach(function (id) {
    var n = NODES[id];
    pos[id] = { x: n.x, y: n.y };
    n.blob = (id + ' ' + n.text_dramatic + ' ' + n.text_teaching + ' ' +
              n.tags.join(' ')).toLowerCase();
  });
  reviewList.forEach(function (id, i) { reviewIdxById[id] = i; });

  Array.prototype.forEach.call(svg.querySelectorAll('g.node'), function (g) {
    nodeEls[g.getAttribute('data-node-id')] = g;
  });
  Array.prototype.forEach.call(svg.querySelectorAll('path.edge-solid'),
      function (p, i) {
    edgeEls.push({ path: p, rec: DATA.solid_edges[i], dashed: false, labels: [] });
  });
  Array.prototype.forEach.call(svg.querySelectorAll('path.edge-dashed'),
      function (p, i) {
    edgeEls.push({ path: p, rec: DATA.dashed_edges[i], dashed: true, labels: [] });
  });
  Array.prototype.forEach.call(svg.querySelectorAll('.edge-midlabel'),
      function (t) {
    var eidx = parseInt(t.getAttribute('data-eidx'), 10);
    if (edgeEls[eidx]) edgeEls[eidx].labels.push(t);
  });

  // ---- pan / zoom / drag ---------------------------------------------------
  function applyTransform() {
    world.setAttribute('transform',
      'translate(' + state.tx + ',' + state.ty + ') scale(' + state.scale + ')');
  }

  function edgeD(rec, dashed) {
    // Mirror of the Python _edge_geometry (same constants).
    var s = pos[rec.src], t = pos[rec.dst];
    var scx = s.x + W / 2, scy = s.y + H / 2, tcx = t.x + W / 2, tcy = t.y + H / 2;
    var g = rec.geo, bow = rec.bow || 0, k = 45;
    if (g === 'down') {
      var x1 = scx, y1 = s.y + H, x2 = tcx, y2 = t.y, ym = (y1 + y2) / 2;
      if (dashed) {
        return 'M ' + fmt(x1 + 18) + ' ' + fmt(y1) + ' C ' + fmt(x1 + 58) + ' ' +
          fmt(ym) + ' ' + fmt(x2 + 58) + ' ' + fmt(ym) + ' ' + fmt(x2 + 42) + ' ' +
          fmt(y2);
      }
      return 'M ' + fmt(x1) + ' ' + fmt(y1) + ' L ' + fmt(x2) + ' ' + fmt(y2);
    }
    if (g === 'fwd') {
      var fx1 = s.x + W, fy1 = scy, fx2 = t.x, fy2 = tcy;
      var dx = fx2 - fx1, dy = fy2 - fy1;
      var ln = Math.sqrt(dx * dx + dy * dy) || 1, ux = dx / ln, uy = dy / ln;
      if (dashed) {
        var px = uy * 56, py = -ux * 56;
        return 'M ' + fmt(fx1) + ' ' + fmt(fy1) + ' C ' +
          fmt(fx1 + k * ux + px) + ' ' + fmt(fy1 + k * uy + py) + ' ' +
          fmt(fx2 - k * ux + px) + ' ' + fmt(fy2 - k * uy + py) + ' ' +
          fmt(fx2) + ' ' + fmt(fy2);
      }
      return 'M ' + fmt(fx1) + ' ' + fmt(fy1) + ' C ' + fmt(fx1 + k) + ' ' +
        fmt(fy1) + ' ' + fmt(fx2 - k) + ' ' + fmt(fy2) + ' ' + fmt(fx2) + ' ' +
        fmt(fy2);
    }
    if (g === 'up') {
      var bx1 = s.x + W, by1 = scy, bx2 = t.x + W, by2 = tcy;
      return 'M ' + fmt(bx1) + ' ' + fmt(by1) + ' C ' + fmt(bx1 + bow) + ' ' +
        fmt(by1) + ' ' + fmt(bx2 + bow) + ' ' + fmt(by2) + ' ' + fmt(bx2) + ' ' +
        fmt(by2);
    }
    if (g === 'fan') {
      return 'M ' + fmt(s.x + W) + ' ' + fmt(scy) + ' C ' + fmt(bow) + ' ' +
        fmt(scy) + ' ' + fmt(bow) + ' ' + fmt(tcy) + ' ' + fmt(t.x + W) + ' ' +
        fmt(tcy);
    }
    var yc = Math.min(s.y, t.y) - bow;
    return 'M ' + fmt(s.x + W / 2) + ' ' + fmt(s.y) + ' C ' +
      fmt(s.x + W / 2) + ' ' + fmt(yc) + ' ' + fmt(t.x + W / 2) + ' ' +
      fmt(yc) + ' ' + fmt(t.x + W / 2) + ' ' + fmt(t.y);
  }

  function labelPos(rec, dashed) {
    var s = pos[rec.src], t = pos[rec.dst];
    var scx = s.x + W / 2, scy = s.y + H / 2, tcy = t.y + H / 2;
    if (rec.geo === 'down') {
      var ym = (s.y + H + t.y) / 2;
      return dashed ? { x: scx + 52, y: ym, a: 'start' }
                    : { x: scx + 12, y: ym + 4, a: 'start' };
    }
    if (rec.geo === 'fwd') {
      var x1 = s.x + W, y1 = scy, x2 = t.x, y2 = tcy;
      if (dashed) {
        var dx = x2 - x1, dy = y2 - y1;
        var ln = Math.sqrt(dx * dx + dy * dy) || 1, ux = dx / ln, uy = dy / ln;
        var px = uy * 56, py = -ux * 56;
        var cx1 = x1 + 45 * ux + px, cy1 = y1 + 45 * uy + py;
        var cx2 = x2 - 45 * ux + px, cy2 = y2 - 45 * uy + py;
        return { x: (x1 + 3 * cx1 + 3 * cx2 + x2) / 8,
                 y: (y1 + 3 * cy1 + 3 * cy2 + y2) / 8 - 4, a: 'middle' };
      }
      return { x: (x1 + x2) / 2, y: (y1 + y2) / 2 - 6, a: 'middle' };
    }
    if (rec.geo === 'up') {
      return { x: (s.x + W + t.x + W) / 2 + (rec.bow || 0) * 0.75,
               y: (scy + tcy) / 2 - 4, a: 'middle' };
    }
    if (rec.geo === 'fan') {
      return { x: rec.bow || 0, y: (scy + tcy) / 2, a: 'middle' };
    }
    var yc = Math.min(s.y, t.y) - (rec.bow || 0);
    return { x: (s.x + W / 2 + t.x + W / 2) / 2, y: yc - 4, a: 'middle' };
  }

  function repathEdge(ee) {
    ee.path.setAttribute('d', edgeD(ee.rec, ee.dashed));
    if (ee.labels.length) {
      var lp = labelPos(ee.rec, ee.dashed);
      ee.labels.forEach(function (t) {
        t.setAttribute('x', fmt(lp.x));
        t.setAttribute('y', fmt(lp.y));
        t.setAttribute('text-anchor', lp.a);
      });
    }
  }
  function repathTouching(id) {
    edgeEls.forEach(function (ee) {
      if (ee.rec.src === id || ee.rec.dst === id) repathEdge(ee);
    });
  }

  svg.addEventListener('mousedown', function (e) {
    if (e.button !== 0) return;
    var g = e.target.closest ? e.target.closest('g.node') : null;
    if (g) {
      var id = g.getAttribute('data-node-id');
      drag = { mode: 'node', id: id, mx: e.clientX, my: e.clientY,
               ox: pos[id].x, oy: pos[id].y, moved: 0 };
    } else {
      drag = { mode: 'pan', mx: e.clientX, my: e.clientY,
               otx: state.tx, oty: state.ty, moved: 0 };
      svg.classList.add('panning');
    }
    e.preventDefault();
  });
  window.addEventListener('mousemove', function (e) {
    if (!drag) return;
    var dx = e.clientX - drag.mx, dy = e.clientY - drag.my;
    drag.moved = Math.max(drag.moved, Math.abs(dx) + Math.abs(dy));
    if (drag.mode === 'node') {
      var nx = drag.ox + dx / state.scale, ny = drag.oy + dy / state.scale;
      pos[drag.id].x = nx;
      pos[drag.id].y = ny;
      nodeEls[drag.id].setAttribute('transform',
        'translate(' + nx + ',' + ny + ')');
      repathTouching(drag.id);
    } else {
      state.tx = drag.otx + dx;
      state.ty = drag.oty + dy;
      applyTransform();
    }
  });
  window.addEventListener('mouseup', function () {
    if (!drag) return;
    svg.classList.remove('panning');
    if (drag.mode === 'node' && drag.moved < 4) selectNode(drag.id, false);
    drag = null;
  });
  svg.addEventListener('wheel', function (e) {
    e.preventDefault();
    var rect = svg.getBoundingClientRect();
    var mx = e.clientX - rect.left, my = e.clientY - rect.top;
    var factor = Math.exp(-e.deltaY * 0.0012);
    var ns = Math.max(0.25, Math.min(3, state.scale * factor));
    var wx = (mx - state.tx) / state.scale, wy = (my - state.ty) / state.scale;
    state.tx = mx - wx * ns;
    state.ty = my - wy * ns;
    state.scale = ns;
    applyTransform();
  }, { passive: false });

  // ---- camera ---------------------------------------------------------------
  function tween(target) {
    if (animReq && window.cancelAnimationFrame) {
      window.cancelAnimationFrame(animReq);
    }
    var from = { tx: state.tx, ty: state.ty };
    var t0 = null;
    function step(ts) {
      if (t0 === null) t0 = ts;
      var k = Math.min(1, (ts - t0) / 280);
      var e = 1 - Math.pow(1 - k, 3);
      state.tx = from.tx + (target.tx - from.tx) * e;
      state.ty = from.ty + (target.ty - from.ty) * e;
      applyTransform();
      if (k < 1) animReq = requestAnimationFrame(step);
      else animReq = null;
    }
    animReq = requestAnimationFrame(step);
  }
  function centerOn(id, animate) {
    var p = pos[id];
    var rect = svg.getBoundingClientRect();
    var target = {
      tx: rect.width / 2 - (p.x + W / 2) * state.scale,
      ty: rect.height / 2 - (p.y + H / 2) * state.scale
    };
    if (animate) tween(target);
    else { state.tx = target.tx; state.ty = target.ty; applyTransform(); }
  }
  function fitView() {
    var bbox = world.getBBox();
    var rect = svg.getBoundingClientRect();
    if (!bbox.width || !bbox.height || !rect.width) return;
    var s = Math.min((rect.width - 80) / bbox.width,
                     (rect.height - 80) / bbox.height);
    s = Math.max(0.25, Math.min(3, s));
    state.scale = s;
    state.tx = (rect.width - bbox.width * s) / 2 - bbox.x * s;
    state.ty = (rect.height - bbox.height * s) / 2 - bbox.y * s;
    applyTransform();
  }
  function resetLayout() {
    Object.keys(NODES).forEach(function (id) {
      var n = NODES[id];
      pos[id] = { x: n.x, y: n.y };
      nodeEls[id].setAttribute('transform',
        'translate(' + n.x + ',' + n.y + ')');
    });
    edgeEls.forEach(repathEdge);
    fitView();
  }

  // ---- reading panel ----------------------------------------------------------
  function summarizeOp(m) {
    var op = m.op || '?', t = m.target, a = m.args || {};
    try {
      if (op === 'hide_all') return 'hide all objects';
      if (op === 'load') {
        var lt = String(t || '').replace(/^pdb:/, '').replace(/^cid:/, '');
        return "load '" + lt + "' as object '" +
          (a.object !== undefined ? a.object : '?') + "'";
      }
      if (op === 'set_color') {
        var rgb = (a.rgb || []).map(function (v) { return Math.round(v * 255); });
        return "define color '" + a.name + "' = rgb(" + rgb.join(', ') + ")";
      }
      if (op === 'show_as') {
        var rep2 = a.rep !== undefined ? a.rep : a.value;
        var suf2 = a.sele ? ' [sele: ' + a.sele + ']' : (t ? ' [' + t + ']' : '');
        return "show as '" + rep2 + "'" + suf2;
      }
      if (op === 'color') {
        var cname = a.name !== undefined ? a.name :
          (a.color !== undefined ? a.color : a.value);
        return "color '" + t + "' = '" + cname + "'";
      }
      if (op === 'show') {
        var rep3 = a.rep !== undefined ? a.rep : a.value;
        var suf3 = a.sele ? ' [sele: ' + a.sele + ']' : (t ? ' [' + t + ']' : '');
        return "show '" + rep3 + "'" + suf3;
      }
      if (op === 'set') return "set '" + a.name + "' = '" + a.value + "'";
      if (op === 'label') return "label '" + t + "' = '" + a.text + "'";
      if (op === 'edit') {
        var nr = a.new_res !== undefined ? a.new_res : a.new_resn;
        var et = "mutate '" + t + "' -> '" + nr + "'";
        if (a.edit_type) {
          et += ' (' + a.edit_type + (a.sele ? ': ' + a.sele : '') + ')';
        }
        return et;
      }
      if (op === 'align') {
        return "align '" + (a.mobile !== undefined ? a.mobile : t) + "' -> '" +
          a.reference + "' (method '" + a.method + "', sele '" +
          a.align_sele + "')";
      }
      return 'op ' + op + ' ' + JSON.stringify(a);
    } catch (err) {
      return 'op ' + op + ' (unsummarizable)';
    }
  }
  function effectsText(eff) {
    if (!eff || typeof eff !== 'object') return JSON.stringify(eff);
    var parts = [];
    Object.keys(eff).sort().forEach(function (k) {
      var v = eff[k];
      if (v && typeof v === 'object' && !Array.isArray(v)) {
        Object.keys(v).sort().forEach(function (k2) {
          parts.push(k + ' ' + k2 + '=' + JSON.stringify(v[k2]));
        });
      } else parts.push(k + ' ' + JSON.stringify(v));
    });
    return parts.join('; ');
  }

  function populatePanel(id) {
    var n = NODES[id];
    var h = [];
    h.push('<div id="panel-head"><div id="rp-id">' + esc(id) + '</div>');
    h.push('<span class="badge">' + esc(n.stage || '\u2014') + '</span>');
    h.push('<span class="badge' + (n.tier ? ' tier-' + esc(n.tier) : '') +
      '">' + (n.tier ? esc(n.tier) : 'tier \u2014') + '</span>');
    h.push('<span class="badge kind-badge">' + esc(n.kind) + '</span></div>');
    if (n.kind === 'phase8-stub') {
      h.push('<div class="stub-note">(Phase 8 \u2014 sanctioned placeholder; ' +
        'claim PLACEHOLDER_PHASE8 is not in the registry)</div>');
    }
    h.push('<div class="sec-title">Tags</div>');
    h.push(n.tags.length
      ? n.tags.map(function (t) {
          return '<span class="tag-chip">' + esc(t) + '</span>';
        }).join('')
      : '<span class="muted">\u2014</span>');
    h.push('<div class="sec-title">Story \u2014 dramatic layer</div>');
    h.push('<blockquote id="rp-dramatic">' + esc(n.text_dramatic) + '</blockquote>');
    h.push('<div class="sec-title">Teaching layer</div>');
    h.push('<p id="rp-teaching">' + esc(n.text_teaching) + '</p>');
    h.push('<div class="sec-title">Choices (' + n.choices.length + ')</div>');
    if (n.choices.length) {
      n.choices.forEach(function (c) {
        h.push('<div class="choice-row"><div>' + esc(c.label || '(unlabeled)') +
          ' \u2192 ' + (c.goto
            ? '<a data-goto="' + esc(c.goto) + '">' + esc(c.goto) + '</a>'
            : '\u2014') + '</div>');
        if (c.weight !== null && c.weight !== undefined) {
          h.push('<span class="choice-ann">w=' + esc(c.weight) + '</span>');
        }
        if (c.cond) {
          h.push('<span class="choice-ann cond-ann">cond: ' + esc(c.cond) + '</span>');
        }
        if (c.effects) {
          h.push('<span class="choice-ann">effects: ' +
            esc(effectsText(c.effects)) + '</span>');
        }
        if (c.tags && c.tags.length) {
          h.push('<div>' + c.tags.map(function (t) {
            return '<span class="mini-chip">' + esc(t) + '</span>';
          }).join('') + '</div>');
        }
        h.push('</div>');
      });
    } else {
      h.push('<div class="muted">terminal node \u2014 no choices</div>');
    }
    h.push('<div class="sec-title">on_enter (' + n.on_enter.length + ')</div>');
    h.push('<ul class="onenter-list">' + n.on_enter.map(function (m) {
      return '<li>' + esc(summarizeOp(m)) + '</li>';
    }).join('') + '</ul>');
    h.push('<div class="sec-title">Claims (' + n.claim_ids.length + ')</div>');
    if (!n.claim_ids.length) h.push('<span class="muted">\u2014</span>');
    n.claim_ids.forEach(function (cid) {
      if (cid === PH) {
        h.push('<span class="claim-chip claim-placeholder" ' +
          'title="Phase-8 sanctioned placeholder \u2014 not in the registry">' +
          'PLACEHOLDER_PHASE8: placeholder</span>');
        return;
      }
      var rec = CLAIMS[cid] || {};
      var st = rec.approval_status || 'unknown';
      var cls = st === 'approved' ? 'claim-approved'
        : (st === 'pending' ? 'claim-pending' : 'claim-placeholder');
      h.push('<span class="claim-chip ' + cls + '" data-claim="' + esc(cid) +
        '" title="' + esc(rec.claim_text || '') + '">' + esc(cid) + ': ' +
        esc(st) + '</span>');
      h.push('<div class="claim-detail" id="detail-' + esc(cid) + '">' +
        '<b>claim:</b> ' + esc(rec.claim || '') + '<br><b>text:</b> ' +
        esc(rec.claim_text || '') + '<br><b>source_id:</b> ' +
        esc(rec.source_id || '\u2014') + ' &nbsp; <b>review_tier:</b> ' +
        esc(rec.review_tier || '\u2014') + '</div>');
    });
    h.push('<div class="sec-title">Known-edit bucket</div>');
    if (n.bucket) {
      h.push('<table class="bucket-table"><tr><th>op</th><th>target</th>' +
        '<th>new_res</th><th>branch_node</th><th>claim_id</th></tr>');
      n.bucket.edits.forEach(function (e2) {
        h.push('<tr><td>' + esc(e2.op) + '</td><td>' + esc(e2.target) +
          '</td><td>' + esc(e2.new_res) + '</td><td><a data-goto="' +
          esc(e2.branch_node) + '">' + esc(e2.branch_node) + '</a></td><td>' +
          esc(e2.claim_id) + '</td></tr>');
      });
      h.push('</table>');
      n.bucket.edits.forEach(function (e2) {
        h.push('<div class="bucket-route">dashed route \u2192 <a data-goto="' +
          esc(e2.branch_node) + '">' + esc(e2.branch_node) + '</a></div>');
      });
    } else if (n.edit_allowed && n.no_bucket) {
      h.push('<div class="no-bucket-note">edit-allowed \u2014 no known-fix ' +
        'bucket in rpg/data/edits.json</div>');
    } else {
      h.push('<span class="muted">\u2014</span>');
    }
    if (n.cast) {
      h.push('<div class="cast-line">' + esc(n.cast.label) + ' \u2014 PDB ' +
        esc(n.cast.pdb_id) + '</div>');
    }
    panelBody.innerHTML = h.join('');
    updatePanelPos();
  }

  function updatePanelPos() {
    var idx = (selectedId !== null && reviewIdxById[selectedId] !== undefined)
      ? reviewIdxById[selectedId] + 1 : 0;
    document.getElementById('panel-pos').textContent =
      (idx ? idx : '\u2014') + ' / ' + reviewList.length;
  }

  // ---- visibility (search x segment x review compose) ---------------------------
  function applyVisibility() {
    var q = searchQ.trim().toLowerCase();
    var current = reviewMode ? reviewList[reviewPos - 1] : null;
    var lit = 0;
    Object.keys(NODES).forEach(function (id) {
      var n = NODES[id];
      var ok = true;
      if (q) ok = n.blob.indexOf(q) >= 0;
      if (ok && seg !== 'all') ok = (n.segment === seg);
      if (reviewMode) ok = (id === current);
      litMap[id] = ok;
      if (ok) lit++;
      var el = nodeEls[id];
      el.classList.toggle('dimmed', !reviewMode && !ok);
      el.classList.toggle('review-dim', reviewMode && id !== current);
      el.classList.toggle('review-current', reviewMode && id === current);
    });
    edgeEls.forEach(function (ee) {
      var eOk = litMap[ee.rec.src] && litMap[ee.rec.dst];
      ee.path.classList.toggle('edge-dim', !eOk);
      ee.labels.forEach(function (t) {
        t.classList.toggle('edge-dim', !eOk);
      });
    });
    if (q) matchCount.textContent = lit + ' matches';
    else if (seg !== 'all') matchCount.textContent = lit + ' shown';
    else matchCount.textContent = '';
  }

  function setSelected(id) {
    if (selectedId && nodeEls[selectedId]) {
      nodeEls[selectedId].classList.remove('selected');
    }
    selectedId = id;
    nodeEls[id].classList.add('selected');
    if (reviewIdxById[id] !== undefined) reviewPos = reviewIdxById[id] + 1;
  }
  function selectNode(id, doCenter) {
    setSelected(id);
    populatePanel(id);
    if (reviewMode) applyVisibility();
    if (doCenter) centerOn(id, true);
  }

  // ---- review order mode ---------------------------------------------------------
  function applyReviewStep() {
    var id = reviewList[reviewPos - 1];
    setSelected(id);
    populatePanel(id);
    centerOn(id, true);
    applyVisibility();
  }
  function reviewStep(delta) {
    var n = reviewList.length;
    reviewPos = ((reviewPos - 1 + delta) % n + n) % n + 1;
    if (reviewMode) applyReviewStep();
    else {
      setSelected(reviewList[reviewPos - 1]);
      populatePanel(selectedId);
      centerOn(selectedId, true);
      applyVisibility();
    }
  }

  // ---- wiring ----------------------------------------------------------------------
  document.getElementById('btn-fit').addEventListener('click', fitView);
  document.getElementById('btn-reset').addEventListener('click', resetLayout);
  btnClaims.addEventListener('click', function () {
    var on = svg.classList.toggle('claims-on');
    btnClaims.classList.toggle('active', on);
  });
  btnReview.addEventListener('click', function () {
    reviewMode = !reviewMode;
    btnReview.classList.toggle('active', reviewMode);
    if (reviewMode) {
      if (reviewPos < 1) reviewPos = 1;
      applyReviewStep();
    } else {
      applyVisibility();
      updatePanelPos();
    }
  });
  document.getElementById('btn-endtrue').addEventListener('click', function () {
    reviewMode = false;
    btnReview.classList.remove('active');
    selectNode('end.true', true);
  });
  document.getElementById('btn-prev').addEventListener('click', function () {
    reviewStep(-1);
  });
  document.getElementById('btn-next').addEventListener('click', function () {
    reviewStep(1);
  });
  Array.prototype.forEach.call(document.querySelectorAll('.seg-btn'),
      function (b) {
    b.addEventListener('click', function () {
      seg = b.getAttribute('data-seg');
      Array.prototype.forEach.call(document.querySelectorAll('.seg-btn'),
          function (o) {
        o.classList.toggle('active', o === b);
      });
      applyVisibility();
    });
  });
  searchInput.addEventListener('input', function () {
    searchQ = searchInput.value;
    applyVisibility();
  });
  searchInput.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      searchInput.value = '';
      searchQ = '';
      applyVisibility();
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && searchQ) {
      searchInput.value = '';
      searchQ = '';
      applyVisibility();
    }
  });
  panelBody.addEventListener('click', function (e) {
    var link = e.target.closest ? e.target.closest('a[data-goto]') : null;
    if (link) {
      selectNode(link.getAttribute('data-goto'), true);
      return;
    }
    var chip = e.target.closest ? e.target.closest('.claim-chip[data-claim]') : null;
    if (chip) {
      var d = document.getElementById('detail-' + chip.getAttribute('data-claim'));
      if (d) d.classList.toggle('open');
    }
  });

  // ---- boot ---------------------------------------------------------------------------
  var c = DATA.counts, tb = c.endings_by_tier;
  document.getElementById('counts-badge').textContent =
    c.nodes + ' nodes / ' + c.endings + ' endings (' + tb['true'] + 'T+' +
    tb.good + 'G+' + tb.normal + 'N+' + tb.bad + 'B) / ' + c.edit_allowed +
    ' edit-allowed / ' + c.claims + ' claims (' + c.approved + ' approved, ' +
    c.pending + ' pending)';
  fitView();
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv):
    # type: (list) -> tuple
    story_dir = DEFAULT_STORY_DIR
    output_dir = DEFAULT_OUTPUT_DIR
    dump_path = None
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
        elif arg == "--dump-data":
            i += 1
            if i >= len(argv):
                sys.stderr.write("--dump-data requires an argument\n")
                sys.exit(2)
            dump_path = argv[i]
        elif arg in ("-h", "--help"):
            sys.stdout.write(USAGE)
            sys.exit(0)
        else:
            sys.stderr.write("Unknown argument: %s\n\n%s" % (arg, USAGE))
            sys.exit(2)
        i += 1
    return story_dir, output_dir, dump_path


def main(argv):
    # type: (list) -> int
    story_dir, output_dir, dump_path = parse_args(argv)
    try:
        model = build_model(story_dir)
    except ValueError as e:
        sys.stderr.write("VIEWER_FAIL: %s\n" % e)
        return 1

    failures = check_integrity(model)
    if failures:
        sys.stderr.write(
            "VIEWER_FAIL: integrity self-check found %d violation(s):\n"
            % len(failures))
        for line in failures:
            sys.stderr.write("  %s\n" % line)
        return 1

    counts = model["counts"]
    diag = model["_diag"]

    # Informational prints (anti-fragility: the pending split is PRINTED,
    # never asserted -- the 07-18 review may legitimately flip BAD-* claims).
    print("Story bundle : %s" % os.path.abspath(story_dir))
    print("Column layout: %s" % " / ".join(
        "%s(%d)" % (COL_LABELS[c], model["col_counts"][c])
        for c in range(N_COLS)))
    print("Ending tiers : %s" % diag["tier_counts"])
    print("No-bucket set: %s" % (diag["no_bucket_ids"] or "(empty)"))
    print("Claim status : %d approved, %d pending %s" % (
        counts["approved"], counts["pending"], diag["pending_ids"]))

    if dump_path:
        dump_dir = os.path.dirname(os.path.abspath(dump_path))
        if not os.path.isdir(dump_dir):
            os.makedirs(dump_dir)
        with open(dump_path, "w", encoding="utf-8") as fh:
            json.dump(model, fh, ensure_ascii=True, indent=1, sort_keys=False)
        print("Payload dump : %s" % os.path.abspath(dump_path))

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    out_path = os.path.join(output_dir, OUTPUT_NAME)
    page = render_html(model)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("Viewer HTML  : %s" % os.path.abspath(out_path))

    print("VIEWER_OK nodes={nodes} endings={endings} "
          "edit_allowed={edit_allowed} buckets={buckets} "
          "claims={claims} pending={pending} "
          "solid_edges={solid_edges} dashed_edges={dashed_edges}".format(
              **counts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
