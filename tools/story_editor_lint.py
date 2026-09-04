#!/usr/bin/env python3.6
"""tools/story_editor_lint.py -- the Python-authoritative story-editor lint.

The pre-save/post-save validator for the Phase 7.1 story-node HTML editor:
green on the untouched live bundle, red on every seeded violation class. This
module is the RULE CATALOG the JS validator (plan 07.1-08, 20_validate.js)
ports 1:1 into the browser -- each ``rule_*`` function below is one stable,
citable rule id; every printed issue carries ``(src: <path:lines>)`` naming
the Python source that owns the rule (the repo's src-citation convention,
tools/api_sanity_smoke.py precedent).

Parity imports (check_citations.py precedent: tools/ importing rpg/ is
sanctioned) -- the lint does NOT reimplement the test-verified algorithms:

    rpg.story.validate.check_reachability  BFS over choice.goto only
                                           (cond/weight ignored; goto edges
                                           to existing nodes only)
    rpg.story.validate.validate_graph      dangling_divert detection
    rpg.edit_router.validate_edits_table   dangling_edit_branch /
                                           dangling_pool_node /
                                           empty_bad_ending_pool (global only
                                           -- per-enzyme empty = legal
                                           fallback) / pool_node_not_ending /
                                           duplicate_signature
    rpg.edit_router.scan_edit_coverage     coverage_uncovered semantics
    rpg.citations.CitationRegistry         the gate's loader (duplicate
                                           claim_id keys rejected via
                                           object_pairs_hook -> schema exit 2)

Exit codes (three-way, check_citations.py:6-11 precedent):

    0 = clean: zero errors (notices OK -- e.g. the sanctioned residual)
    1 = lint errors: at least one seeded violation class detected
    2 = schema-config error: unparseable JSON / missing file / bad schema /
        duplicate registry key (the bundle cannot even be loaded)

Output line format (the JS port mirrors this exactly):

    LINT <KIND>: <node/file> -- <detail> (src: <path:lines>)     [error]
    LINT NOTICE <KIND>: <node/file> -- <detail> (src: <path:lines>)  [notice]
    LINT: N errors, M notices (exit 0|1|2)                       [summary]

The count-shift detector (rule_count_shift) is deliberately NOT a hard
failure (RESEARCH-SAFETY key finding 1 / Pitfall S2): a topology edit that is
otherwise well-formed exits 0 but emits a ``count_shift`` NOTICE reporting
old->new for nodes / endings by tier / edit-allowed ids and naming the pinned
tests + viewer constants as the SAME-COMMIT update obligations. Phase 8
topology work flows through this acknowledgment path.

The sanctioned residual (RESEARCH-SAFETY Pitfall S6) is encoded EXACTLY:
PLACEHOLDER_PHASE8 is permitted only as fa.stub/alc.stub's claim_ids -- and
must be present on exactly those two nodes. Any other node (or any other
PLACEHOLDER*) is a ``placeholder_misuse`` error. Citation gate semantics are
``approval_status == "approved"`` strictly (rpg/citations.py:100-109; a
rejected claim fails identically to a pending one).

Usage (all args default to the real repo paths, resolved from __file__ --
CWD-independent):

    python3.6 tools/story_editor_lint.py [--story-dir DIR] [--registry PATH]
                                         [--edits PATH] [--cast PATH]
                                         [--sources PATH]

``--sources`` (data/sources.json) is loaded for claim source-resolution
CONTEXT only (appended to claim-issue details) -- it is NOT gated; a
malformed/missing sources.json never changes the verdict.

Python 3.6 stdlib ONLY (argparse/json/os/re/sys/collections + the rpg
imports). NO pymol/PyQt5 (this is a tools/ script but keeps the domain-tier
import discipline). NO f-strings (.format() per repo convention). NO
@dataclass (3.7+).
"""
import argparse
import collections
import io
import json
import os
import re
import sys

# Make the rpg package importable when run as a loose script from the repo
# (mirrors tools/check_citations.py:39).
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from rpg.citations import CitationRegistry  # noqa: E402  (sys.path setup above)
from rpg.edit_router import (  # noqa: E402  (sys.path setup above)
    EditsTable, validate_edits_table, scan_edit_coverage,
)
from rpg.story.validate import check_reachability, validate_graph  # noqa: E402


# ---------------------------------------------------------------------------
# Frozen constants -- the rule sources (each cited; the JS port mirrors these)
# ---------------------------------------------------------------------------

# The frozen molops dispatch vocabulary (rpg/pymol_layer/molops.py:140-291):
# any on_enter op outside this set raises NotImplementedError at dispatch.
# src: rpg/pymol_layer/molops.py:140-291
OP_VOCABULARY = frozenset([
    "hide_all", "show", "show_as", "select_focus", "zoom", "color",
    "set_color", "label", "set", "align", "load", "delete", "edit",
    "protonate", "restore",
])

# set_view is NOT dispatchable this phase: accepted (exit stays 0) but
# visibly flagged. src: tools/scene_capture.py (the Phase-10 WARNING
# precedent); rpg/pymol_layer/molops.py:286-291 (unknown op -> raise).
PHASE10_OPS = ("set_view",)

# The 07-12 DC-A restoration-branch nodes: entry is ROUTER-ONLY (no incoming
# choice.goto -- engine.apply_player_edit routes known edits directly).
# src: tests/test_glucose_reachability.py:326-452
#      (test_restoration_nodes_reachable_non_ending)
ROUTER_ONLY_NODES = ("gly.pfk_restored", "tca.aconitase_restored")

# The documented structural stub exempt from the two-layer/no-TBD scans (its
# text_dramatic IS the "[STRUCTURAL STUB:" marker -- the bundle's ONLY TBD).
# src: tests/test_glucose_content.py:91-95 + :174-184
DOCUMENTED_STUB_NODES = ("edit.prompt",)

# The 07-01-sanctioned Phase-8 stubs: the ONLY nodes allowed to reference
# PLACEHOLDER_PHASE8 (and the citation gate's ONLY sanctioned residual --
# exactly 2 MISSING + 0 UNAPPROVED).
# src: tests/test_glucose_content.py:97-99 + :213-236
PHASE8_STUB_NODES = ("fa.stub", "alc.stub")
PHASE8_CLAIM = "PLACEHOLDER_PHASE8"

# Start nodes load bundled placeholders ONLY (no network fetch at game
# start). The owning test pins intro.preface/intro.shell_glucose/intro.select
# -- all intro.* -- so the lint derives the set as the manifest start + the
# intro.* prefix. src: tests/test_glucose_reachability.py:868-885
#      (test_start_nodes_do_not_reference_real_pdb_fetch)
START_NODE_PREFIX = "intro."

# tca.shuffle is the graph's ONLY weighted node (the single seeded-RNG
# surface; 0.5/0.5 design B). src: tests/test_glucose_content.py:539-557
SHUFFLE_NODE = "tca.shuffle"

# tca.citrate_synthase is the edit:structural reframe: carries an
# edit:enzyme: tag but deliberately NO edits.json bucket (zero natural
# disease point variants). src: tests/test_glucose_content.py:404-449
STRUCTURAL_TAG_ENZYME = "tca.citrate_synthase"

# The pinned counts, reported as values NOT assertions (the count-shift
# acknowledgment path). Sources: tests/test_glucose_reachability.py:136
# (== 57 nodes), :157 (== 21 endings, 1T+3G+2N+15B), :264 (== 15
# edit-allowed) and the viewer's pinned constants.
# src: tools/story_graph_viewer.py:96-105 (EXPECTED_NODES/EXPECTED_TIER_COUNTS/
#      EXPECTED_EDIT_ALLOWED)
PINNED_NODE_COUNT = 57
PINNED_TIER_COUNTS = {"true": 1, "good": 3, "normal": 2, "bad": 15}
PINNED_EDIT_ALLOWED = frozenset([
    "gly.pfk", "gly.pyruvate_kinase", "pyr.pdh", "tca.citrate_synthase",
    "tca.aconitase", "tca.shuffle", "tca.isocitrate_dh", "tca.akg_dh",
    "tca.succinyl_coa_synthetase", "tca.fumarase", "tca.malate_dh",
    "etc.complex_i", "etc.complex_ii", "etc.complex_iii", "etc.complex_iv",
])
PINNED_TIER_ORDER = ("true", "good", "normal", "bad")

# The broken cond form: <dict>.<attr> attribute access (NOT followed by "(",
# so flags.get(...) -- the MANDATORY dict-method form -- never matches). The
# owning test scans flags.; the lint extends the same broken-form rule to the
# other dict namespaces the interpreter exposes (visits/counters -- identical
# AttributeError -> caught -> choice hidden -> stuck failure mode).
# src: tests/test_glucose_reachability.py:716-752
#      (test_no_broken_dict_attribute_conds_remain)
#      + rpg/story/interpreter.py:101-131 (_cond namespace)
BROKEN_COND_RE = re.compile(
    r"(flags|visits|counters)\.[a-zA-Z_][a-zA-Z0-9_]*(?![a-zA-Z0-9_])(?!\()")

# Default details for rpg-emitted Issue kinds that carry no detail string.
EDIT_TABLE_ISSUE_DETAILS = {
    "empty_bad_ending_pool":
        "the global bad_ending_pool is empty (the ultimate fallback for any "
        "enzyme without a per-enzyme override -- EditRoutingError at runtime)",
    "dangling_pool_node": "pool member not in the story graph",
    "pool_node_not_ending": "pool member exists but is not an ending",
    "dangling_edit_branch": "branch_node not in the story graph",
    "duplicate_signature": "two edits in one bucket share a signature",
}


# ---------------------------------------------------------------------------
# Result + bundle carriers (plain classes -- 3.6 has no dataclasses)
# ---------------------------------------------------------------------------

class LintIssue(object):
    """One lint finding. ``severity`` is "error" (exit 1) or "notice"
    (informational -- never changes the exit code)."""

    def __init__(self, kind, where, detail, src, severity="error"):
        # type: (str, str, str, str, str) -> None
        self.kind = kind
        self.where = where
        self.detail = detail
        self.src = src
        self.severity = severity

    def format(self):
        # type: () -> str
        prefix = "LINT NOTICE" if self.severity == "notice" else "LINT"
        return "{0} {1}: {2} -- {3} (src: {4})".format(
            prefix, self.kind, self.where, self.detail, self.src)


class Bundle(object):
    """A loaded story bundle: ordered nodes + per-node file attribution.

    Attributes:
        nodes: collections.OrderedDict {node_id: raw node dict} in manifest
            file order (the viewer's loader shape).
        file_of: {node_id: filename} -- which manifest file defined the node.
        start: the manifest's start node id.
        manifest: the raw manifest dict.
    """

    def __init__(self, nodes, file_of, start, manifest):
        # type: (collections.OrderedDict, dict, str, dict) -> None
        self.nodes = nodes
        self.file_of = file_of
        self.start = start
        self.manifest = manifest


# ---------------------------------------------------------------------------
# Loaders (mirroring the viewer's committed loaders; schema errors -> exit 2)
# ---------------------------------------------------------------------------

def _load_json(path, label):
    # type: (str, str) -> object
    """Load a JSON file, raising ValueError with a clear label on malformed
    JSON / missing file (the caller maps ValueError/OSError to exit 2)."""
    if not os.path.isfile(path):
        raise ValueError("{0} not found: {1}".format(label, path))
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as e:
        raise ValueError(
            "malformed {0} JSON at {1}: {2}".format(label, path, e))


def load_bundle(story_dir):
    # type: (str) -> Bundle
    """Load a story bundle: manifest + the listed files -> ordered nodes.

    Mirrors the viewer's committed loader (tools/story_graph_viewer.py
    load section) and ``StoryGraph.load`` (rpg/story/graph.py:50-88):

    - reads ``manifest.json`` (version/default_seed/start/files);
    - merges every listed file's ``nodes`` dict IN MANIFEST FILE ORDER into
      an OrderedDict, recording ``file_of[node_id] = filename``;
    - raises ``ValueError`` on a duplicate node id across files (the loader
      contract -- silently last-wins would clobber a node), a non-dict
      ``nodes`` object, a non-dict node entry, a missing/invalid manifest,
      or unparseable JSON (caller maps all of these to schema exit 2).
    """
    if not os.path.isdir(story_dir):
        raise ValueError(
            "story dir not found (not a directory): {0}".format(story_dir))
    manifest = _load_json(os.path.join(story_dir, "manifest.json"), "story manifest")
    if not isinstance(manifest, dict):
        raise ValueError("story manifest must be a JSON object")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("story manifest 'files' must be a non-empty list")
    start = manifest.get("start")
    if not isinstance(start, str) or not start:
        raise ValueError("story manifest 'start' must be a non-empty string")

    nodes = collections.OrderedDict()
    file_of = {}
    for filename in files:
        data = _load_json(os.path.join(story_dir, filename),
                          "story file {0}".format(filename))
        if not isinstance(data, dict):
            raise ValueError(
                "story file {0} must be a JSON object".format(filename))
        raw_nodes = data.get("nodes", {})
        if not isinstance(raw_nodes, dict):
            raise ValueError(
                "story file {0} must have a 'nodes' object; got {1}".format(
                    filename, type(raw_nodes).__name__))
        for node_id, raw in raw_nodes.items():
            if node_id in nodes:
                raise ValueError(
                    "Duplicate node id {0!r} in story file {1!r} "
                    "(already defined in an earlier file)".format(
                        node_id, file_of.get(node_id, "?")))
            if not isinstance(raw, dict):
                raise ValueError(
                    "node {0!r} in {1} must be an object; got {2}".format(
                        node_id, filename, type(raw).__name__))
            nodes[node_id] = raw
            file_of[node_id] = filename
    return Bundle(nodes, file_of, start, manifest)


def _load_edits_table(edits_path):
    # type: (str) -> EditsTable
    """Load edits.json with explicit schema checks, then wrap it in the
    rpg EditsTable (validate_edits_table/scan_edit_coverage consume it)."""
    raw = _load_json(edits_path, "edits")
    if not isinstance(raw, dict):
        raise ValueError("edits.json must be a JSON object")
    enzymes = raw.get("enzymes", {})
    if not isinstance(enzymes, dict):
        raise ValueError(
            "edits.json 'enzymes' must be an object; got {0}".format(
                type(enzymes).__name__))
    return EditsTable(raw)


def _load_cast_ids(cast_path):
    # type: (str) -> list
    """Load cast.json -> the ordered list of enzyme ids (schema checks
    mirror tools/check_edit_coverage.py:74-104)."""
    raw = _load_json(cast_path, "cast")
    if not isinstance(raw, dict):
        raise ValueError("cast.json must be a JSON object")
    enzymes = raw.get("enzymes")
    if not isinstance(enzymes, list):
        raise ValueError(
            "cast.json 'enzymes' must be a list; got {0}".format(
                type(enzymes).__name__))
    ids = []
    for entry in enzymes:
        if not isinstance(entry, dict) or "id" not in entry:
            raise ValueError(
                "cast.json 'enzymes' entry missing 'id': {0!r}".format(entry))
        ids.append(entry["id"])
    return ids


def _load_context(sources_path):
    # type: (str) -> dict
    """Best-effort load of data/sources.json for claim source-resolution
    CONTEXT only. NOT gated: any load failure yields {} and never changes
    the verdict."""
    try:
        data = _load_json(sources_path, "sources")
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def _load_raw_registry(registry_path):
    # type: (str) -> dict
    """Best-effort re-read of the registry for claim source-resolution
    CONTEXT only (CitationRegistry keeps records private). NOT gated."""
    try:
        data = _load_json(registry_path, "registry")
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def _source_context(cid, raw_registry, sources):
    # type: (str, dict, dict) -> str
    """Human-readable provenance suffix for a claim issue (context only --
    sources.json is never gated)."""
    record = raw_registry.get(cid)
    if not isinstance(record, dict):
        return ""
    source_ids = record.get("source_id")
    if source_ids is None:
        return ""
    if not isinstance(source_ids, list):
        source_ids = [source_ids]
    parts = []
    for sid in source_ids:
        srec = sources.get(sid)
        status = srec.get("approval_status") if isinstance(srec, dict) else "?"
        parts.append("{0} ({1})".format(sid, status))
    return " sources: " + ", ".join(parts)


# ---------------------------------------------------------------------------
# The rule catalog -- one function per rule id (the JS port's contract).
# Each rule appends LintIssue objects; error severity -> exit 1.
# ---------------------------------------------------------------------------

def rule_dangling_divert(nodes, issues):
    # type: (dict, list) -> None
    """dangling_divert: a choice.goto pointing at a nonexistent node.
    Exact parity via rpg validate_graph. src: rpg/story/validate.py:214-235
    (validate_graph); tests/test_glucose_reachability.py (the 345-suite pin)."""
    for issue in validate_graph(nodes):
        detail = issue.detail or "choice -> missing node"
        issues.append(LintIssue(
            issue.kind, issue.node_id, detail, "rpg/story/validate.py:214-235"))


def rule_unreachable_ending(nodes, start, issues):
    # type: (dict, str, list) -> None
    """unreachable_ending: an ending orphaned from the start node (the
    reachability report must be not_ok). Exact parity via rpg
    check_reachability. src: rpg/story/validate.py:167-207
    (check_reachability -- BFS over choice.goto only, cond/weight ignored)."""
    report = check_reachability(nodes, start)
    if report.is_ok:
        return
    for ending_id in report.unreachable_endings:
        issues.append(LintIssue(
            "unreachable_ending", ending_id,
            "ending not reachable from {0!r} via choice.goto chains "
            "(BFS ignores cond/weight; router-only entries are exempt by "
            "being non-endings)".format(start),
            "rpg/story/validate.py:167-207"))


def rule_router_only_incoming(nodes, issues):
    # type: (dict, list) -> None
    """router_only_incoming: any choice.goto INTO a router-only restored
    node (their entry is engine.apply_player_edit -- zero incoming edges is
    load-bearing). src: tests/test_glucose_reachability.py:326-452
    (test_restoration_nodes_reachable_non_ending, router-only assertion)."""
    for restored_id in ROUTER_ONLY_NODES:
        if restored_id not in nodes:
            continue  # a deleted restored node surfaces as dangling_edit_branch
        for nid, node in nodes.items():
            for choice in node.get("choices", []):
                if choice.get("goto") == restored_id:
                    issues.append(LintIssue(
                        "router_only_incoming", nid,
                        "choice {0!r} -> {1!r}: restored nodes are ROUTER-ONLY "
                        "(engine.apply_player_edit routes known edits "
                        "directly; no incoming choice.goto edge may "
                        "exist)".format(choice.get("label"), restored_id),
                        "tests/test_glucose_reachability.py:326-452"))


def rule_single_continue(nodes, issues):
    # type: (dict, list) -> None
    """single_continue: a node with exactly one choice labeled "Continue"
    (a linear click-through; the Continue-to-MC invariant). Exact parity
    with the owning test's predicate. src:
    tests/test_glucose_reachability.py:245-262 (test_no_single_continue_choice)."""
    for nid, node in nodes.items():
        choices = node.get("choices", [])
        if len(choices) == 1 and choices[0].get("label") == "Continue":
            issues.append(LintIssue(
                "single_continue", nid,
                "node has a single 'Continue' choice (the Continue-to-MC "
                "invariant requires >=2 choices or an ending/stub shape)",
                "tests/test_glucose_reachability.py:245-262"))


def rule_two_layer_text(nodes, issues):
    # type: (dict, list) -> None
    """text_layer_empty + tbd_text: both text layers non-empty (after
    strip) and no "TBD" residue in text/choice labels. The ONLY exempt node
    is edit.prompt (its text_dramatic IS the [STRUCTURAL STUB: marker).
    src: tests/test_glucose_content.py:126-184 (TestTwoLayerText)."""
    for nid, node in nodes.items():
        if nid in DOCUMENTED_STUB_NODES:
            continue
        for field in ("text_dramatic", "text_teaching"):
            value = node.get(field)
            if not isinstance(value, str) or not value.strip():
                issues.append(LintIssue(
                    "text_layer_empty", nid,
                    "{0} is empty or blank (STORY-06 two-layer invariant; "
                    "edit.prompt is the only exempt node)".format(field),
                    "tests/test_glucose_content.py:126-184"))
            elif "TBD" in value:
                issues.append(LintIssue(
                    "tbd_text", nid,
                    "{0} contains 'TBD' residue (the bundle's only sanctioned "
                    "TBD is edit.prompt's stub marker)".format(field),
                    "tests/test_glucose_content.py:126-184"))
        for choice in node.get("choices", []):
            label = choice.get("label") or ""
            if "TBD" in label:
                issues.append(LintIssue(
                    "tbd_text", nid,
                    "choice label {0!r} contains 'TBD' residue".format(label),
                    "tests/test_glucose_content.py:126-184"))


def rule_claims(nodes, registry, raw_registry, sources, issues):
    # type: (dict, CitationRegistry, dict, dict, list) -> None
    """claim_missing + claim_unapproved + placeholder_misuse + the
    sanctioned_residual NOTICE. Citation-gate semantics: every story-
    referenced claim_id must exist AND be approval_status == "approved"
    strictly -- EXCEPT the sanctioned residual: PLACEHOLDER_PHASE8 on
    exactly fa.stub/alc.stub (reported as a notice; anywhere else, or any
    other PLACEHOLDER*, is a placeholder_misuse error).
    src: tools/check_citations.py:44-95 (the gate);
         rpg/citations.py:100-109 (is_approved, strict == "approved");
         tests/test_glucose_content.py:187-257 (TestClaimHygiene)."""
    stub_refs = []
    for nid, node in nodes.items():
        for cid in node.get("claim_ids", []) or []:
            if not isinstance(cid, str):
                issues.append(LintIssue(
                    "claim_missing", nid,
                    "non-string claim_id {0!r} (claim_ids must be strings)"
                    .format(cid),
                    "tests/test_glucose_content.py:187-257"))
                continue
            if cid == PHASE8_CLAIM:
                if nid in PHASE8_STUB_NODES:
                    stub_refs.append(nid)  # sanctioned residual
                else:
                    issues.append(LintIssue(
                        "placeholder_misuse", nid,
                        "{0!r} is sanctioned ONLY on {1} (the Phase-8 stub "
                        "pair) -- a new node may never use it".format(
                            cid, list(PHASE8_STUB_NODES)),
                        "tests/test_glucose_content.py:213-236"))
                continue
            if cid.startswith("PLACEHOLDER"):
                issues.append(LintIssue(
                    "placeholder_misuse", nid,
                    "{0!r}: no PLACEHOLDER* residue is allowed anywhere "
                    "except PLACEHOLDER_PHASE8 on {1}".format(
                        cid, list(PHASE8_STUB_NODES)),
                    "tests/test_glucose_content.py:213-236"))
                continue
            if not registry.contains(cid):
                issues.append(LintIssue(
                    "claim_missing", nid,
                    "references claim_id {0!r} -- not in the registry".format(cid),
                    "tools/check_citations.py:44-95"))
            elif not registry.is_approved(cid):
                issues.append(LintIssue(
                    "claim_unapproved", nid,
                    "references claim_id {0!r} -- approval_status is {1!r}, "
                    "not 'approved' (rejected fails identically to pending)"
                    .format(cid, registry.status(cid))
                    + _source_context(cid, raw_registry, sources),
                    "tools/check_citations.py:44-95"))
    # The sanctioned residual must be EXACTLY the stub pair (no fewer --
    # a stub losing its reference breaks the gate's pinned 2-MISSING form).
    if sorted(stub_refs) == sorted(PHASE8_STUB_NODES):
        issues.append(LintIssue(
            "sanctioned_residual", ", ".join(PHASE8_STUB_NODES),
            "PLACEHOLDER_PHASE8 present on exactly the sanctioned Phase-8 "
            "stubs (the citation gate's sanctioned residual: exit 1 = 2 "
            "MISSING + 0 UNAPPROVED) -- reported as a notice, never an error",
            "tests/test_glucose_content.py:213-236", severity="notice"))
    else:
        for stub in PHASE8_STUB_NODES:
            if stub_refs.count(stub) != 1:
                issues.append(LintIssue(
                    "placeholder_misuse", stub,
                    "sanctioned stub must carry {0!r} exactly once (the "
                    "citation-gate residual is EXACTLY the stub pair); "
                    "found {1}".format(PHASE8_CLAIM, stub_refs.count(stub)),
                    "tests/test_glucose_content.py:213-236"))


def rule_edit_offer_tag(nodes, issues):
    # type: (dict, list) -> None
    """offer_without_tag: a node offering an edit (a choice tagged
    edit:offer OR whose goto IS edit.prompt -- the ChoicePanel's DUAL
    predicate) without carrying an edit:enzyme:<id> tag.
    src: tests/test_glucose_reachability.py:462-499
         (test_edit_offer_nodes_carry_edit_enzyme_tag)."""
    for nid, node in nodes.items():
        offers = [c for c in node.get("choices", [])
                  if "edit:offer" in (c.get("tags") or [])
                  or c.get("goto") == "edit.prompt"]
        if not offers:
            continue
        has_tag = any(str(t).startswith("edit:enzyme:")
                      for t in node.get("tags") or [])
        if not has_tag:
            issues.append(LintIssue(
                "offer_without_tag", nid,
                "node offers {0} edit choice(s) but carries no "
                "edit:enzyme:<id> tag (the controller's _current_enzyme_id() "
                "would be None -> request_edit RuntimeError)".format(
                    len(offers)),
                "tests/test_glucose_reachability.py:462-499"))


def rule_edits_table(edits_table, nodes, issues):
    # type: (EditsTable, dict, list) -> None
    """dangling_edit_branch / dangling_pool_node / empty_bad_ending_pool /
    pool_node_not_ending / duplicate_signature. Exact parity via rpg
    validate_edits_table (per-enzyme empty pool = legal fallback, never
    flagged). src: rpg/edit_router.py:172-235 (validate_edits_table)."""
    for issue in validate_edits_table(edits_table, nodes):
        detail = issue.detail or EDIT_TABLE_ISSUE_DETAILS.get(
            issue.kind, "see rpg/edit_router.validate_edits_table")
        issues.append(LintIssue(
            issue.kind, issue.node_id, detail, "rpg/edit_router.py:172-235"))


def rule_coverage(edits_table, cast_ids, issues):
    # type: (EditsTable, list, list) -> None
    """coverage_uncovered: a cast enzyme with no edits.json bucket (or an
    empty edits list). Exact parity via rpg scan_edit_coverage.
    src: rpg/edit_router.py:238-255 (scan_edit_coverage);
         tools/check_edit_coverage.py:65-126 (the CLI gate)."""
    for issue in scan_edit_coverage(edits_table, cast_ids):
        issues.append(LintIssue(
            "coverage_uncovered", issue.node_id,
            "cast enzyme has no edits.json bucket (or 0 edits) -- every "
            "cast id needs >=1 known-edit entry (check_edit_coverage "
            "semantics)",
            "rpg/edit_router.py:238-255"))


def rule_relationship_pin(nodes, edits_ids, cast_ids, issues):
    # type: (dict, set, set, list) -> None
    """relationship_pin: the shared-manifest invariant cast(ids) subset-of
    edits(ids) AND edits(ids) == distinct edit:enzyme: tag values minus
    {tca.citrate_synthase}. CS is edit:structural (tag, no bucket by
    design). src: tests/test_glucose_content.py:404-449
    (TestManifestRelationships)."""
    tag_values = set()
    for node in nodes.values():
        for tag in node.get("tags") or []:
            tag = str(tag)
            if tag.startswith("edit:enzyme:"):
                tag_values.add(tag[len("edit:enzyme:"):])
    expected = tag_values - {STRUCTURAL_TAG_ENZYME}
    extra = sorted(set(edits_ids) - expected)
    missing = sorted(expected - set(edits_ids))
    if extra or missing:
        issues.append(LintIssue(
            "relationship_pin", "edits.json <-> graph tags",
            "edits({0}) != edit:enzyme tag values({1}) - "
            "{{{2}}}; bucket(s) with no tag carrier: {3}; tag value(s) "
            "with no bucket: {4}".format(
                len(edits_ids), len(tag_values), STRUCTURAL_TAG_ENZYME,
                extra, missing),
            "tests/test_glucose_content.py:404-449"))
    uncovered = sorted(set(cast_ids) - set(edits_ids))
    if uncovered:
        issues.append(LintIssue(
            "relationship_pin", "cast.json -> edits.json",
            "cast({0}) is not a subset of edits({1}): cast id(s) with no "
            "edits.json bucket: {2}".format(
                len(cast_ids), len(edits_ids), uncovered),
            "tests/test_glucose_content.py:404-449"))


def rule_weight_outside_shuffle(nodes, issues):
    # type: (dict, list) -> None
    """weight_outside_shuffle: a weighted choice on any node other than
    tca.shuffle (the graph's ONLY weighted node -- the whole seeded-RNG
    surface). src: tests/test_glucose_content.py:539-557
    (test_shuffle_is_the_only_weighted_node)."""
    for nid, node in nodes.items():
        if nid == SHUFFLE_NODE:
            continue
        for choice in node.get("choices", []):
            if choice.get("weight") is not None:
                issues.append(LintIssue(
                    "weight_outside_shuffle", nid,
                    "choice {0!r} carries weight {1!r} -- only "
                    "tca.shuffle may carry weights (the single seeded-RNG "
                    "surface; a new weighted node is a design-B contract "
                    "change)".format(choice.get("label"),
                                     choice.get("weight")),
                    "tests/test_glucose_content.py:539-557"))


def rule_cond_attribute_form(nodes, issues):
    # type: (dict, list) -> None
    """cond_attribute_form: a choice cond using the broken dict-ATTRIBUTE
    form (flags.x / visits.x / counters.x) instead of the mandatory
    dict-METHOD form (flags.get('x')). Attribute access raises
    AttributeError inside _cond -> caught -> choice silently hidden ->
    potentially stuck. src: tests/test_glucose_reachability.py:716-752
    (test_no_broken_dict_attribute_conds_remain);
     rpg/story/interpreter.py:101-131 (the _cond namespace)."""
    for nid, node in nodes.items():
        for choice in node.get("choices", []):
            cond = choice.get("cond")
            if cond is None:
                continue
            match = BROKEN_COND_RE.search(cond)
            if match:
                issues.append(LintIssue(
                    "cond_attribute_form", nid,
                    "choice {0!r} cond {1!r} uses the broken dict-attribute "
                    "form {2!r} -- use the dict-METHOD form "
                    "flags.get('...')/visits.get('...', 0)".format(
                        choice.get("label"), cond, match.group(0)),
                    "tests/test_glucose_reachability.py:716-752"))


def rule_start_node_pdb_load(bundle, issues):
    # type: (Bundle, list) -> None
    """start_node_pdb_load: a start node's on_enter loading a ``pdb:``
    target (start nodes use bundled placeholders ONLY -- no network fetch
    at game start). The start set = the manifest start + the intro.* prefix
    (the owning test pins intro.preface/intro.shell_glucose/intro.select --
    all intro.*). src: tests/test_glucose_reachability.py:868-885
    (test_start_nodes_do_not_reference_real_pdb_fetch)."""
    start_ids = set([bundle.start])
    start_ids.update(nid for nid in bundle.nodes
                     if nid.startswith(START_NODE_PREFIX))
    for nid in start_ids:
        node = bundle.nodes.get(nid)
        if node is None:
            continue
        for action in node.get("on_enter", []):
            if action.get("op") != "load":
                continue
            target = action.get("target")
            if isinstance(target, str) and target.startswith("pdb:"):
                issues.append(LintIssue(
                    "start_node_pdb_load", nid,
                    "start node on_enter loads {0!r} -- start nodes use "
                    "bundled placeholders only (an instant-start game must "
                    "not network-fetch at game start)".format(target),
                    "tests/test_glucose_reachability.py:868-885"))


def rule_on_enter_ops(nodes, issues):
    # type: (dict, list) -> None
    """unknown_op + the set_view_phase10 NOTICE: every on_enter op must be
    in the frozen molops dispatch vocabulary (a stray op raises
    NotImplementedError at dispatch); set_view is NOT dispatchable this
    phase but is accepted with a visible NOTICE (the scene_capture
    Phase-10 precedent), never an error.
    src: rpg/pymol_layer/molops.py:140-291 (the dispatch vocabulary;
         unknown op -> raise at :286-291); tools/scene_capture.py
         (the Phase-10 set_view WARNING precedent)."""
    for nid, node in nodes.items():
        for action in node.get("on_enter", []):
            op = action.get("op")
            if op in PHASE10_OPS:
                issues.append(LintIssue(
                    "set_view_phase10", nid,
                    "op {0!r} is Phase-10-flagged (camera ops land in "
                    "Phase 10) -- accepted with this visible notice, per "
                    "the scene_capture.py precedent".format(op),
                    "rpg/pymol_layer/molops.py:286-291", severity="notice"))
            elif op not in OP_VOCABULARY:
                issues.append(LintIssue(
                    "unknown_op", nid,
                    "on_enter op {0!r} is outside the frozen molops "
                    "vocabulary {1} -- it would raise NotImplementedError "
                    "at dispatch".format(op, sorted(OP_VOCABULARY)),
                    "rpg/pymol_layer/molops.py:140-291"))


def _format_tiers(tier_counts):
    # type: (dict) -> str
    """Deterministic tier-count rendering: {true: N, good: N, normal: N,
    bad: N} (unknown tiers appended sorted)."""
    parts = ["{0}: {1}".format(t, tier_counts.get(t, 0))
             for t in PINNED_TIER_ORDER]
    for t in sorted(tier_counts):
        if t not in PINNED_TIER_ORDER:
            parts.append("{0}: {1}".format(t, tier_counts[t]))
    return "{" + ", ".join(parts) + "}"


def rule_count_shift(nodes, issues):
    # type: (dict, list) -> None
    """count_shift NOTICE (never an error): compare the live counts against
    the pinned trio -- nodes / endings by tier / edit-allowed ids -- and
    report old->new, naming the pinned tests + the viewer's pinned
    constants as the SAME-COMMIT update obligations. This is the
    acknowledgment path (RESEARCH-SAFETY key finding 1 / Pitfall S2):
    pinned-count movement is an explicit event, not a silent pass and not a
    hard error. src: tests/test_glucose_reachability.py:136-155
    (test_manifest_loads_all_57_nodes), :157-189
    (test_reachability_green_all_four_tiers), :264-324
    (test_15_edit_allowed_nodes); tools/story_graph_viewer.py:96-105
    (EXPECTED_NODES / EXPECTED_TIER_COUNTS / EXPECTED_EDIT_ALLOWED)."""
    moved = []
    live_nodes = len(nodes)
    if live_nodes != PINNED_NODE_COUNT:
        moved.append("nodes {0} -> {1}".format(PINNED_NODE_COUNT, live_nodes))

    live_tiers = {}
    for node in nodes.values():
        tier = node.get("is_ending")
        if tier is not None:
            live_tiers[tier] = live_tiers.get(tier, 0) + 1
    if live_tiers != PINNED_TIER_COUNTS:
        moved.append("endings by tier {0} -> {1}".format(
            _format_tiers(PINNED_TIER_COUNTS), _format_tiers(live_tiers)))

    live_edit_allowed = set()
    for nid, node in nodes.items():
        for tag in node.get("tags") or []:
            if str(tag).startswith("edit:enzyme:"):
                live_edit_allowed.add(nid)
                break
    if live_edit_allowed != PINNED_EDIT_ALLOWED:
        moved.append(
            "edit-allowed nodes {0} -> {1} (added {2}; removed {3})".format(
                len(PINNED_EDIT_ALLOWED), len(live_edit_allowed),
                sorted(live_edit_allowed - PINNED_EDIT_ALLOWED),
                sorted(PINNED_EDIT_ALLOWED - live_edit_allowed)))

    if not moved:
        return
    issues.append(LintIssue(
        "count_shift", "bundle counts",
        "; ".join(moved)
        + " -- SAME-COMMIT update obligations: test_manifest_loads_all_57_nodes, "
        "test_reachability_green_all_four_tiers, test_15_edit_allowed_nodes "
        "+ the viewer's pinned constants EXPECTED_NODES / "
        "EXPECTED_TIER_COUNTS / EXPECTED_EDIT_ALLOWED "
        "(tools/story_graph_viewer.py:96-105). The pinned tests will fail "
        "until their counts are updated in the same change -- that failure "
        "is the designed signal.",
        "tests/test_glucose_reachability.py:136,157,264 + "
        "tools/story_graph_viewer.py:96-105",
        severity="notice"))


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_lint(story_dir, registry_path, edits_path, cast_path, sources_path):
    # type: (str, str, str, str, str) -> tuple
    """Run every rule. Returns ``(exit_code, report_lines)``.

    exit_code 0 = zero errors (notices OK); 1 = >=1 error;
    Raises ValueError/OSError on schema-config errors (the caller maps
    them to exit 2) -- INCLUDING the registry's duplicate-claim_id
    rejection via CitationRegistry's object_pairs_hook.
    """
    bundle = load_bundle(story_dir)                 # ValueError/OSError -> 2
    registry = CitationRegistry.load(registry_path)  # dup keys -> ValueError -> 2
    edits_table = _load_edits_table(edits_path)
    cast_ids = _load_cast_ids(cast_path)
    sources = _load_context(sources_path)
    raw_registry = _load_raw_registry(registry_path)

    issues = []  # type: list
    rule_dangling_divert(bundle.nodes, issues)
    rule_unreachable_ending(bundle.nodes, bundle.start, issues)
    rule_router_only_incoming(bundle.nodes, issues)
    rule_single_continue(bundle.nodes, issues)
    rule_two_layer_text(bundle.nodes, issues)
    rule_claims(bundle.nodes, registry, raw_registry, sources, issues)
    rule_edit_offer_tag(bundle.nodes, issues)
    rule_edits_table(edits_table, bundle.nodes, issues)
    rule_coverage(edits_table, cast_ids, issues)
    rule_relationship_pin(bundle.nodes,
                          set(edits_table.to_dict().get("enzymes", {}).keys()),
                          set(cast_ids), issues)
    rule_weight_outside_shuffle(bundle.nodes, issues)
    rule_cond_attribute_form(bundle.nodes, issues)
    rule_start_node_pdb_load(bundle, issues)
    rule_on_enter_ops(bundle.nodes, issues)
    rule_count_shift(bundle.nodes, issues)

    errors = [i for i in issues if i.severity == "error"]
    notices = [i for i in issues if i.severity == "notice"]
    exit_code = 1 if errors else 0
    lines = [i.format() for i in errors] + [i.format() for i in notices]
    lines.append("LINT: {0} errors, {1} notices (exit {2})".format(
        len(errors), len(notices), exit_code))
    return exit_code, lines


def _utf8_stdout():
    # type: () -> None
    """Guarantee UTF-8 stdout (the report carries em-dashes/unicode from
    the data); a cp1252/cp850 console would otherwise raise
    UnicodeEncodeError mid-report."""
    encoding = getattr(sys.stdout, "encoding", "") or ""
    if encoding.lower().replace("-", "") != "utf8" and hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace",
            line_buffering=True)


def main(argv=None):
    # type: (list) -> int
    parser = argparse.ArgumentParser(
        description="Story-editor lint: the Python-authoritative pre-save/"
                    "post-save validator (green on the live bundle, red on "
                    "seeded violations). Exit 0 = clean (notices OK), "
                    "1 = lint errors, 2 = schema-config error.")
    parser.add_argument("--story-dir", default=os.path.join(REPO_ROOT, "data",
                                                            "story_glucose"),
                        help="Story bundle directory (manifest.json + files)")
    parser.add_argument("--registry", default=os.path.join(REPO_ROOT, "data",
                                                           "citations.json"),
                        help="Citation registry JSON (duplicate keys rejected)")
    parser.add_argument("--edits", default=os.path.join(REPO_ROOT, "rpg",
                                                        "data", "edits.json"),
                        help="edits.json lookup table")
    parser.add_argument("--cast", default=os.path.join(REPO_ROOT, "rpg",
                                                       "data", "cast.json"),
                        help="cast.json manifest")
    parser.add_argument("--sources", default=os.path.join(REPO_ROOT, "data",
                                                          "sources.json"),
                        help="sources.json -- context only, NOT gated")
    args = parser.parse_args(argv)
    _utf8_stdout()
    try:
        exit_code, report = run_lint(args.story_dir, args.registry,
                                     args.edits, args.cast, args.sources)
    except (ValueError, OSError) as e:
        # Malformed JSON, missing file, bad schema, duplicate registry key --
        # fail loud with a clear message. Distinct exit 2 from "1 = lint
        # errors" so callers tell broken config from real violations.
        sys.stderr.write("LINT SCHEMA ERROR: {0}\n".format(e))
        return 2
    for line in report:
        print(line)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
