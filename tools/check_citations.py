#!/usr/bin/env python3.6
"""Pre-ship citation gate. Blocks release if any story node references a
missing or non-approved claim_id. Enforces spec.md's no-fabricated-science
rule architecturally. Pure stdlib, Python 3.6, no pymol/PyQt5.

Exit codes (three-way so CI distinguishes broken fixtures from unapproved
content -- research Investigation Point 3):

    0 = PASS: every story-referenced claim_id exists and is 'approved'
    1 = FAIL: at least one referenced claim_id is missing OR not approved
    2 = ERROR: config/load error (malformed JSON, missing file, bad schema)

Usage::

    python3.6 tools/check_citations.py --story <path> --registry <path>

The gate imports ``c14.citations.CitationRegistry`` (the loader) via a
``sys.path`` insertion of the repo root -- the script lives in ``tools/``,
not in ``c14/``, so it must put the repo root on ``sys.path`` to import the
package without install.

Phase 1 scope: the story walker (``collect_referenced_claim_ids``) is inline
and walks a single ``--story`` JSON's ``nodes`` dict. Phase 2 refactors this
single function into ``c14.story.validate.collect_claim_ids("data/story/")``
once the real multi-file story graph lands. The gate's core logic (registry
load + is_approved check + report + exit) is unchanged by that refactor.

See .planning/phases/01-foundations-testability-citation-gate/01-RESEARCH-citations.md
Investigation Point 3 for the full reference design.
"""
import argparse
import json
import os
import sys

# Make the c14 package importable when run as a loose script from the repo.
# Resolves repo root from __file__ so the script runs regardless of CWD.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from c14.citations import CitationRegistry  # noqa: E402  (sys.path setup above)


def collect_referenced_claim_ids(story_path):
    """Load a story JSON file and return ``{node_id: [claim_id, ...]}``.

    Phase 1: walks the ``nodes`` dict inline. Phase 2 refactors this into
    ``c14.story.validate.collect_claim_ids("data/story/")`` for the
    multi-file manifest. Forward-compatible: the fixture uses the same node
    shape (``{"nodes": {id: {"claim_ids": [...]}}}``) as the real graph.

    Raises ``ValueError`` on bad schema (non-dict nodes, non-dict node entry)
    or malformed JSON (``json.JSONDecodeError`` is a ``ValueError`` subclass).
    Nodes with no ``claim_ids`` key contribute an empty list (valid -- a
    purely narrative node).
    """
    with open(story_path, "r") as f:
        story = json.load(f)
    nodes = story.get("nodes", {})
    if not isinstance(nodes, dict):
        raise ValueError(
            "story JSON must have a 'nodes' object; got {}".format(type(nodes).__name__)
        )
    referenced = {}
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            raise ValueError(
                "node {!r} must be an object; got {}".format(node_id, type(node).__name__)
            )
        referenced[node_id] = list(node.get("claim_ids", []))
    return referenced


def run_gate(story_path, registry_path):
    """Run the citation gate. Returns ``(exit_code, report_lines)``.

    exit_code 0 = pass; 1 = missing/unapproved claims.
    Raises ``ValueError``/``OSError`` on config/load errors (caller maps to
    exit 2).
    """
    # 1. Load + validate registry (raises ValueError on malformed/bad schema)
    registry = CitationRegistry.load(registry_path)

    # 2. Collect referenced claim_ids from the story
    referenced = collect_referenced_claim_ids(story_path)

    # 3. Check each referenced claim_id: must EXIST and be 'approved'
    missing = []     # list of (node_id, claim_id)
    unapproved = []  # list of (node_id, claim_id, actual_status)
    for node_id, claim_ids in referenced.items():
        for cid in claim_ids:
            if not registry.contains(cid):
                missing.append((node_id, cid))
            elif not registry.is_approved(cid):
                unapproved.append((node_id, cid, registry.status(cid)))

    # 4. Build a human-readable report
    lines = []
    total_refs = sum(len(v) for v in referenced.values())
    if not missing and not unapproved:
        lines.append(
            "CITATION GATE PASSED: {} claim reference(s) across {} node(s) -- all approved."
            .format(total_refs, len(referenced))
        )
        return 0, lines

    lines.append(
        "CITATION GATE FAILED: {} missing + {} unapproved claim reference(s)."
        .format(len(missing), len(unapproved))
    )
    for node_id, cid in missing:
        lines.append(
            "  [MISSING]    node {!r} references claim_id {!r} -- not in registry"
            .format(node_id, cid)
        )
    for node_id, cid, status in unapproved:
        lines.append(
            "  [UNAPPROVED] node {!r} references claim_id {!r} -- status is {!r}"
            .format(node_id, cid, status)
        )
    lines.append(
        "Fix: add an 'approved' entry for each missing/unapproved claim_id in {}, "
        "or remove the claim_id from the story node.".format(registry_path)
    )
    return 1, lines


def main():
    parser = argparse.ArgumentParser(
        description="Pre-ship citation gate. Exits 0 if all story-referenced "
                    "claim_ids are 'approved' in the registry; exits 1 if any "
                    "are missing or not approved; exits 2 on config/load errors."
    )
    parser.add_argument("--story", required=True, help="Path to story JSON file")
    parser.add_argument("--registry", required=True, help="Path to citation registry JSON file")
    args = parser.parse_args()

    try:
        exit_code, report = run_gate(args.story, args.registry)
    except (ValueError, OSError) as e:
        # Malformed JSON, missing file, bad schema -- fail loud with a clear
        # message. Distinct exit 2 from "1 = unapproved claims" so CI can tell
        # config errors (broken fixtures) from real gate failures.
        print("CITATION GATE ERROR: {}".format(e), file=sys.stderr)
        sys.exit(2)
    for line in report:
        print(line)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
