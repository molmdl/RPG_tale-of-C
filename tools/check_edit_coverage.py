#!/usr/bin/env python3.6
"""tools/check_edit_coverage.py -- per-enzyme minimum-coverage scan (SC5).

Data-driven scan: loads ``c14/data/cast.json`` (enzymes represented so far) +
``c14/data/edits.json`` (known-edit entries per enzyme). For each enzyme id in
cast.json, asserts it has >=1 entry in edits.json's ``enzymes`` dict (i.e.
``enzyme_id in edits["enzymes"]`` AND
``len(edits["enzymes"][enzyme_id].get("edits", [])) >= 1``).

Stays green as the cast grows: add an enzyme to cast.json -> the scan picks it
up -> FAILS until edits.json has an entry (forces coverage discipline). Phase 4
placeholder: both manifests have ONE demo enzyme (fixture_enzyme_1) with ONE
demo edit entry -> scan is GREEN. Real cast (~20+ enzymes with real PDB IDs +
citations) is Phase 9; real edits.json (per-enzyme known-edit entries with real
claim_ids) is Phase 5+.

This scan re-implements the coverage check INLINE (does NOT import
c14.edit_router) so it stays independent of c14.edit_router, matching the
check_citations.py does-its-own-loading precedent. This keeps 04-04's
``depends_on: ["04-01"]`` honest -- the scan needs only the two JSON files
(Task 2), not the router module (04-02).

Exit codes (Phase 1 three-way convention, check_citations.py:6-11):

    0 = PASS (all cast enzymes have >=1 known-edit entry)
    1 = FAIL (some enzyme in cast.json has no edits.json entry)
    2 = ERROR (malformed JSON / missing file / bad schema)

Usage::

    python3.6 tools/check_edit_coverage.py

Pure stdlib. Python 3.6 compatible. Importable in pure WSL python3.6 (no pymol).
"""
import json
import os
import sys

# Repo root resolved from __file__ (mirrors check_citations.py:39).
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAST_PATH = os.path.join(REPO_ROOT, "c14", "data", "cast.json")
EDITS_PATH = os.path.join(REPO_ROOT, "c14", "data", "edits.json")


def _load_json(path, label):
    # type: (str, str) -> dict
    """Load + sanity-check a JSON manifest. Raises ``ValueError`` on malformed
    JSON / missing file / bad schema (caller maps to exit 2)."""
    if not os.path.isfile(path):
        raise ValueError("{} manifest not found: {}".format(label, path))
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, OSError) as e:
        # ValueError covers JSON decode errors (json.JSONDecodeError subclasses
        # ValueError on 3.5+); re-raise with a clear label.
        raise ValueError("malformed {} JSON at {}: {}".format(label, path, e))
    if not isinstance(data, dict):
        raise ValueError(
            "{} manifest must be a JSON object, got {}".format(
                label, type(data).__name__))
    return data


def run_scan(cast_path, edits_path):
    """Run the coverage scan. Returns ``(exit_code, report_lines)``.

    exit_code 0 = pass; 1 = uncovered enzyme(s). Raises ``ValueError`` on
    config/load errors (caller maps to exit 2).
    """
    cast = _load_json(cast_path, "cast")
    edits = _load_json(edits_path, "edits")

    # Schema checks (-> exit 2 on bad schema, distinct from exit 1 = uncovered).
    cast_enzymes = cast.get("enzymes")
    if not isinstance(cast_enzymes, list):
        raise ValueError(
            "cast.json 'enzymes' must be a list, got {}".format(
                type(cast_enzymes).__name__))
    edits_enzymes = edits.get("enzymes")
    if not isinstance(edits_enzymes, dict):
        raise ValueError(
            "edits.json 'enzymes' must be an object, got {}".format(
                type(edits_enzymes).__name__))

    covered = []   # list of (enzyme_id, n_edits)
    missing = []   # list of (enzyme_id, reason)
    for entry in cast_enzymes:
        if not isinstance(entry, dict) or "id" not in entry:
            raise ValueError(
                "cast.json 'enzymes' entry missing 'id': {!r}".format(entry))
        eid = entry["id"]
        rec = edits_enzymes.get(eid)
        if rec is None:
            missing.append((eid, "no edits.json entry for this enzyme"))
            continue
        if not isinstance(rec, dict):
            missing.append((eid, "edits.json entry is not an object"))
            continue
        n = len(rec.get("edits", []) or [])
        if n < 1:
            missing.append((eid, "edits.json entry has 0 edits"))
            continue
        covered.append((eid, n))

    lines = []
    if not missing:
        lines.append(
            "EDIT COVERAGE PASSED: {n} enzyme(s) covered -- each has >=1 "
            "edits.json entry.".format(n=len(covered)))
        for eid, n in covered:
            lines.append("  [COVERED]  {eid} ({n} edit(s))".format(eid=eid, n=n))
        return 0, lines

    lines.append(
        "EDIT COVERAGE FAILED: {m} enzyme(s) missing edits.json coverage "
        "({c} covered).".format(m=len(missing), c=len(covered)))
    for eid, n in covered:
        lines.append("  [COVERED]  {eid} ({n} edit(s))".format(eid=eid, n=n))
    for eid, reason in missing:
        lines.append("  [MISSING]  {eid} -- {reason}".format(
            eid=eid, reason=reason))
    lines.append(
        "Fix: add an 'edits' entry for each missing enzyme in {}, or remove "
        "the enzyme from {}.".format(edits_path, cast_path))
    return 1, lines


def main():
    # type: () -> int
    try:
        exit_code, report = run_scan(CAST_PATH, EDITS_PATH)
    except ValueError as e:
        # Malformed JSON, missing file, bad schema -> exit 2 (config error),
        # distinct from exit 1 (genuinely uncovered enzyme).
        sys.stderr.write("EDIT COVERAGE ERROR: {}\n".format(e))
        return 2
    for line in report:
        print(line)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
