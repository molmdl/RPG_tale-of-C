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
    for key in order:
        rec = pairs[key]
        src, dst = key
        sc, sr = pos[src]
        tc, tr = pos[dst]
        if tc > sc:
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

    print("VIEWER_OK nodes={nodes} endings={endings} "
          "edit_allowed={edit_allowed} buckets={buckets} "
          "claims={claims} pending={pending} "
          "solid_edges={solid_edges} dashed_edges={dashed_edges}".format(
              **counts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
