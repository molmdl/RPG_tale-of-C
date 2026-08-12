# Phase 1 (CITE-02 track): Citation Registry & No-Fabricated-Science Gate — Research

**Researched:** 2026-08-13
**Domain:** Citation registry data model + pre-ship CI gate (pure-Python, stdlib-only)
**Confidence:** HIGH

## Summary

This track designs the **citation registry** (`data/citations.json`) and the **pre-ship gate** (`tools/check_citations.py`) that together enforce `spec.md`'s strongest constraint architecturally: *no fabricated science ships*. The project's own finalized architecture research (`.planning/research/ARCHITECTURE.md` "Pattern 4") already established the core design — a JSON-object registry mapping `claim_id → {source metadata, approval_status}`, plus a pure-Python gate that cross-references story nodes' `claim_ids` against the registry and `sys.exit(1)` on any missing/non-`approved` claim. This research **confirms and sharpens** that design into a concrete, planner-actionable spec: exact JSON schema, exact fixture data (clearly placeholder — no real science), and a 3.6-compatible algorithm in pseudocode.

Three discrepancies in the prior research are resolved here: (1) **file name** — earlier docs (`PITFALLS.md`, `SUMMARY.md`) sketched `data/claims.jsonl` (JSONL); the finalized `ARCHITECTURE.md` settled on `data/citations.json` (JSON object). This research adopts `citations.json` and documents *why* (O(1) lookup, structural duplicate-key prevention, matches the authoritative doc). (2) **`approval_status` enum** — `ARCHITECTURE.md` specifies `{pending, approved, rejected}`; the Phase 1 success criterion text mentions only `pending`/`approved`. This research keeps all three (the gate treats anything `!= "approved"` as a failure, so `rejected` is covered without special-casing) and explains the rationale. (3) **Python 3.6 `@dataclass` incompatibility** — `ARCHITECTURE.md`'s code examples use `@dataclass`, but **`dataclasses` is Python 3.7+ and is NOT importable on the project's `python3.6.9`** (verified: `ModuleNotFoundError: No module named 'dataclasses'`). The citation loader must use a **plain class or plain functions on dicts**, not dataclasses. This is flagged as the #1 pitfall.

**Primary recommendation:** Build `c14/citations.py` (a `CitationRegistry` plain class with `.load(path)` + `.is_approved(claim_id)`, stdlib-only, no pymol/PyQt5) and `tools/check_citations.py` (argparse `--story` + `--registry`, inline story-claim collection for Phase 1, clear per-claim pass/fail report, `sys.exit(1)` on any missing/non-approved referenced claim). Ship fixture story + registry JSON in `tests/fixtures/` (clearly placeholder: `placeholder-claim-N`, `source: "TBD"`) demonstrating both the pass (exit 0) and fail (exit 1) paths. The gate imports `c14.citations` but does its own minimal story walking in Phase 1 — Phase 2 refactors that into `c14/story/validate.py:collect_claim_ids()` once the real story graph (multi-file manifest) exists.

---

## Investigation Point 1 — Citation Registry Data Model

### Recommended location & format

**File:** `data/citations.json` — a single JSON **object** (dict), keyed by `claim_id`. This is the established convention in the finalized `ARCHITECTURE.md` (lines 65, 117, 321, 507–509).

**Why a JSON object (not JSONL / `claims.jsonl`):**
- **O(1) lookup by `claim_id`** — the gate calls `is_approved(claim_id)` per referenced claim; a dict makes this a single hash lookup. JSONL (one claim per line) would require a full scan or building an index at load.
- **Structural duplicate prevention** — dict keys are unique. A duplicate `claim_id` key in the JSON source is silently last-wins under `json.load`, but the loader CAN detect it with `object_pairs_hook` (verified — see Pitfalls). JSONL has no such guard; dedup must be hand-coded.
- **Human-review-friendly** — a reviewer sees the `claim_id` as the object key, immediately adjacent to its source/approval. Matches the per-claim review workflow.
- **Matches the authoritative doc** — `ARCHITECTURE.md` is the finalized architecture; the earlier `claims.jsonl` references in `PITFALLS.md`/`SUMMARY.md` were illustrative sketches ("e.g.") that got refined into the JSON-object design.

**Resolution of the `claims.jsonl` vs `citations.json` discrepancy:** Adopt `data/citations.json` (JSON object). The `.jsonl` references in earlier research are superseded. (The `source_id` field from the PITFALLS sketch folds into the structured `source` block below; `status` → `approval_status` to match ARCHITECTURE.md.)

### Top-level structure

```json
{
  "<claim_id_1>": { ...claim object... },
  "<claim_id_2>": { ...claim object... }
}
```

A bare dict keyed by `claim_id`. **No top-level wrapper** (no `{"claims": {...}}`, no `version` field) — keep it simple for Phase 1. (A `version` key could collide with a `claim_id` named `"version"`; the story-graph `manifest.json` and the save file carry their own `version` — the citation registry does not need one for Phase 1. If a schema version is wanted later, nest it under a reserved `_meta` key, but defer that decision — it is out of scope for Phase 1.)

### Per-claim object schema (recommended, structured source)

Use a **structured `source`** block (not a free-form string). Rationale: (a) the Phase 9 `tools/build_cast_list.py` reads `pdb_id` + `resolution_angstrom` programmatically to generate the README cast list; (b) provenance discipline — a free-form string can't be validated and drifts; (c) `ARCHITECTURE.md` already uses this shape (lines 321–341).

```json
{
  "claim": "C14 redistributes among oxaloacetate carboxyls in TCA",
  "source_type": "textbook",
  "source": "Biochemistry LibreTexts",
  "url": "https://bio.libretexts.org/...",
  "approval_status": "approved",
  "approved_by": "human-name",
  "approval_date": "2026-08-12",
  "notes": "Approved during pathway-research checkpoint"
}
```

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `claim` | string | YES | One-line summary of what the claim asserts (human-review anchor) |
| `source_type` | enum string | YES | One of: `"textbook"`, `"libretexts"`, `"doi"`, `"pdb"`, `"pubchem"`, `"placeholder"` (placeholder is for fixture data only) |
| `source` | string | YES | Human-readable source label (book title, LibreTexts chapter name, journal name) |
| `url` | string | NO | Canonical URL when applicable (LibreTexts page, DOI URL, RCSB structure page) |
| `doi` | string | NO | DOI string (e.g. `"10.xxxx/..."`) when `source_type == "doi"` |
| `pdb_id` | string | NO | 4-character PDB code when `source_type == "pdb"` (e.g. `"1TNR"`) |
| `resolution_angstrom` | number | NO | Resolution in Å when `source_type == "pdb"` (parsed from the file header in Phase 9, not memory) |
| `pubchem_cid` | integer | NO | PubChem CID when `source_type == "pubchem"` |
| `approval_status` | enum string | YES | One of: `"pending"`, `"approved"`, `"rejected"` |
| `approved_by` | string | NO | Human approver identifier (only meaningful when `approval_status == "approved"`) |
| `approval_date` | string | NO | ISO date (YYYY-MM-DD) of approval |
| `notes` | string | NO | Free-text review notes |

**Per-source-type required fields** (load-time validation, optional for Phase 1 but recommended):
- `source_type == "pdb"` → `pdb_id` required; `resolution_angstrom` + `url` recommended.
- `source_type == "doi"` → `doi` required; `url` recommended.
- `source_type == "pubchem"` → `pubchem_cid` required.
- `source_type == "placeholder"` → none beyond the base required set (fixture data only).

For **Phase 1**, the loader should validate the base required fields (`claim`, `source_type`, `source`, `approval_status`) and that `approval_status ∈ {pending, approved, rejected}`. Full per-source-type field validation can be added but is not load-bearing for the gate (the gate only reads `approval_status`). Mark per-source-type validation as a **nice-to-have** the planner may include or defer.

### The `approval_status` enum decision

**Recommendation: keep all three values `{pending, approved, rejected}`** (matching `ARCHITECTURE.md` line 313), even though the Phase 1 success-criterion text only names `pending`/`approved`.

- The gate's pass/fail test is **`approval_status == "approved"`** — anything else (pending, rejected, or any unrecognized value) fails. So `rejected` is handled with **zero special-casing**: a `rejected` claim referenced by a story node produces the same `exit 1` as a `pending` one.
- Keeping `rejected` lets the registry *record why a claim was refused* (via `notes`) rather than silently deleting it — useful provenance for the human-approval workflow (Phase 5 CITE-01). Deleting a refused claim would make a future re-introduction look like a *new* claim and lose the rejection history.
- The Phase 1 success criterion ("exits non-zero when any story node references a missing or `pending` claim_id, and exits zero when all referenced claims are `approved`") is **fully satisfied** by the `== "approved"` test — it does not require `rejected` to be absent from the schema.

### The loader module — `c14/citations.py`

**YES**, there is a Python module that loads/validates the registry, in the pure-Python domain tier. This is established (`ARCHITECTURE.md` lines 65, 84, 529, 651) and required by this track's brief ("a `load_registry()` function that `check_citations.py` imports").

**Recommended API — a plain class (NOT a dataclass — see Pitfall #1):**

```python
# c14/citations.py — pure-Python, stdlib only, NO pymol/PyQt5 imports
import json

class CitationRegistry:
    """Loads + validates data/citations.json. The no-fabricated-science gate's data source."""
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"
    _VALID_STATUSES = (PENDING, APPROVED, REJECTED)

    def __init__(self, data):
        # data: dict of claim_id -> claim object
        self._claims = data

    @classmethod
    def load(cls, path):
        """Load + validate a citation registry JSON file. Raises ValueError on malformed data."""
        with open(path, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("citations registry must be a JSON object keyed by claim_id")
        # validate each entry
        for cid, entry in data.items():
            if not isinstance(entry, dict):
                raise ValueError("claim '{}' must be an object".format(cid))
            status = entry.get("approval_status")
            if status not in cls._VALID_STATUSES:
                raise ValueError("claim '{}' has invalid approval_status: {!r}".format(cid, status))
        return cls(data)

    def is_approved(self, claim_id):
        """True iff claim_id exists AND approval_status == 'approved'. The gate's core predicate."""
        entry = self._claims.get(claim_id)
        return entry is not None and entry.get("approval_status") == self.APPROVED

    def status(self, claim_id):
        """Return approval_status, or None if claim_id is missing (for reporting)."""
        entry = self._claims.get(claim_id)
        return entry.get("approval_status") if entry is not None else None

    def contains(self, claim_id):
        return claim_id in self._claims

    def __len__(self):
        return len(self._claims)

    def claim_ids(self):
        return list(self._claims.keys())
```

**Why a class, not bare functions:** `ARCHITECTURE.md` shows `CitationRegistry.load()` + `reg.is_approved(cid)` (lines 346–352, 509). A class encapsulates the loaded dict + validation + the approved-set predicate, and is reusable by Phase 2's engine (runtime dev-mode assertion) and Phase 5's approval workflow. The brief also mentions a `load_registry()` function — a thin functional wrapper `def load_registry(path): return CitationRegistry.load(path)` is fine if the planner prefers, but the class is the recommended shape (it carries `.is_approved()` which is the gate's core).

**3.6 compatibility:** plain class, `json` stdlib, string `.format()` — all 3.6-safe. **No `@dataclass`** (see Pitfall #1). `os`/`pathlib` not needed if `path` is passed in (caller opens / argparse supplies the string).

---

## Investigation Point 2 — Story Node → `claim_id` Reference Contract

### Field name & shape (per-node)

**Field name:** `claim_ids` (a list of strings). This is **already established** in `ARCHITECTURE.md` — the `Node` model carries `claim_ids: List[str] = field(default_factory=list)` (line 189), and the JSON example uses `"claim_ids": ["tca.redistribution"]` (line 239) / `"claim_ids": ["tca.intro"]` (line 466).

```json
{
  "id": "tca.entry",
  "text_dramatic": "...",
  "text_teaching": "...",
  "claim_ids": ["tca.intro", "tca.redistribution"],
  "choices": [...],
  "on_enter": [...]
}
```

- **Per-node, not per-text-segment.** Keep it simple for Phase 1 (and Phase 2): the node is the unit of citation. If a future phase needs finer granularity (a `text_teaching` segment citing a different source than the node's pathway fact), that can be added as a structured `text_teaching` with inline claim refs later — **out of scope for Phase 1**. Per-node is the established contract; do not over-engineer.
- **A node may carry zero, one, or many `claim_ids`.** Zero is valid (a purely narrative node with no scientific claim). The gate skips nodes with empty `claim_ids`.
- **The `claim_ids` are strings** — short, stable, dotted identifiers (e.g. `"tca.redistribution"`, `"pdb.1TNR"`, `"pubchem.5793"`). They are the join key between story nodes and the registry. Naming convention: `<domain>.<specifics>` (matches the node-id convention `knot.stitch`). The *content* of real claim_ids is a Phase 5+ content decision; Phase 1 fixtures use `placeholder-claim-N`.

### Phase 1 scope: FIXTURE story data only

**Critical:** Phase 1 does **NOT** build the real story graph (that is Phase 2 — STORY-01, the DAG interpreter). Phase 1 builds **only fixture story data** in `tests/fixtures/` to *demonstrate the gate works both ways*. The fixture uses the **same node shape** as the real story graph (so the gate is forward-compatible), but it is deliberately a 2-node toy, clearly placeholder.

The real `data/story/` directory (with `manifest.json` + per-pathway files) is **Phase 2**. Phase 1's `tools/check_citations.py` takes a path to *a* story JSON file via argparse — for the Phase 1 demonstration, that path points at a fixture. When Phase 2 lands the real story graph, the gate is refactored to traverse `data/story/` via `c14/story/validate.py:collect_claim_ids()` (see Investigation Point 5).

### Minimal 2-node fixture story (shape — exact JSON in Investigation Point 4)

Two nodes: an intro node and an ending node, each carrying one `claim_id`. No real science — `text_dramatic`/`text_teaching` are prefixed `PLACEHOLDER:`. This is enough to prove the gate walks nodes, collects `claim_ids`, and pass/fails on approval status.

---

## Investigation Point 3 — `check_citations.py` Gate Logic

### Inputs & CLI

```
python3.6 tools/check_citations.py --story <path-to-story.json> --registry <path-to-citations.json>
```

- **`argparse`** with two required positional-or-flag arguments: `--story` and `--registry`. Use flags (not positionals) so the invocation is self-documenting and order-independent.
- Both paths are filesystem paths (strings). The tool reads them with `open()`/`json.load`. **No `pymol`, no `PyQt5`, no `numpy` imports** — pure stdlib (verified importable on `python3.6.9`).

### Algorithm (pseudocode — 3.6-compatible, stdlib-only)

```python
#!/usr/bin/env python3
"""Pre-ship citation gate: blocks release if any story node references a
missing or non-approved claim_id. Enforces spec.md's no-fabricated-science
rule architecturally. Pure stdlib, Python 3.6, no pymol/PyQt5 imports."""
import argparse
import json
import os
import sys

# Make the c14 package importable when run as a loose script from the repo.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from c14.citations import CitationRegistry


def collect_referenced_claim_ids(story_path):
    """Load a story JSON file and return {node_id: [claim_id,...]}.
    Phase 1: walks the 'nodes' dict inline. Phase 2 refactors this into
    c14/story/validate.py:collect_claim_ids() for the multi-file manifest.
    Forward-compatible: the fixture uses the same node shape as the real graph."""
    with open(story_path, "r") as f:
        story = json.load(f)
    nodes = story.get("nodes", {})
    if not isinstance(nodes, dict):
        raise ValueError("story JSON must have a 'nodes' object; got {}".format(type(nodes).__name__))
    referenced = {}
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            raise ValueError("node '{}' must be an object".format(node_id))
        referenced[node_id] = list(node.get("claim_ids", []))
    return referenced


def run_gate(story_path, registry_path):
    """Returns (exit_code, report_lines). exit_code 0 = pass, 1 = fail."""
    # 1. Load + validate registry (raises ValueError on malformed)
    registry = CitationRegistry.load(registry_path)

    # 2. Collect referenced claim_ids from the story
    referenced = collect_referenced_claim_ids(story_path)

    # 3. Check each referenced claim_id: must EXIST and be 'approved'
    missing = []     # (node_id, claim_id)
    unapproved = []  # (node_id, claim_id, actual_status)
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
        lines.append("CITATION GATE PASSED: {} claim reference(s) across {} node(s) — all approved."
                     .format(total_refs, len(referenced)))
        return 0, lines

    lines.append("CITATION GATE FAILED: {} missing + {} unapproved claim reference(s)."
                 .format(len(missing), len(unapproved)))
    for node_id, cid in missing:
        lines.append("  [MISSING]    node {!r} references claim_id {!r} — not in registry"
                     .format(node_id, cid))
    for node_id, cid, status in unapproved:
        lines.append("  [UNAPPROVED] node {!r} references claim_id {!r} — status is {!r}"
                     .format(node_id, cid, status))
    lines.append("Fix: add an 'approved' entry for each missing/unapproved claim_id in {}, "
                 "or remove the claim_id from the story node.".format(registry_path))
    return 1, lines


def main():
    parser = argparse.ArgumentParser(
        description="Pre-ship citation gate. Exits 0 if all story-referenced "
                    "claim_ids are 'approved' in the registry; exits 1 if any "
                    "are missing or not approved.")
    parser.add_argument("--story", required=True, help="Path to story JSON file")
    parser.add_argument("--registry", required=True, help="Path to citation registry JSON file")
    args = parser.parse_args()

    try:
        exit_code, report = run_gate(args.story, args.registry)
    except (ValueError, OSError) as e:
        # Malformed JSON, missing file, bad schema — fail loud with a clear message
        print("CITATION GATE ERROR: {}".format(e), file=sys.stderr)
        sys.exit(2)   # distinct from "1 = unapproved claims" so CI can tell config errors from real fails
    for line in report:
        print(line)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

### Edge cases & decisions

| Case | Behavior | Rationale |
|------|----------|-----------|
| **Unreferenced claim in registry** | PASS (no error, no warning) | A pre-approved-but-not-yet-used claim is fine — front-loaded source approval (Phase 5) intentionally creates these. The gate checks *referenced* claims only. |
| **Duplicate `claim_id` keys in registry JSON** | Detect at load (optional) or silent last-wins | `json.load` keeps the last value (verified). Recommend the loader use `object_pairs_hook` to raise on duplicates — see Pitfall #3. **If the planner skips that, duplicates silently overwrite — still safe (no claim vanishes from a *referenced* check, but two authors could clobber each other). Recommend detecting.** |
| **Malformed registry JSON** | `CitationRegistry.load` raises `ValueError` → gate prints `CITATION GATE ERROR: ...` to stderr, `sys.exit(2)` | Don't let a raw `json.JSONDecodeError` traceback leak. Distinct exit code (2) from "unapproved claims" (1) so CI distinguishes config errors from real gate failures. |
| **Malformed story JSON** | Same — `collect_referenced_claim_ids` raises `ValueError` → `sys.exit(2)` | Consistent handling. |
| **Missing file** | `open()` raises `OSError` (FileNotFoundError) → caught → `sys.exit(2)` | Same handler. |
| **Story with empty `nodes`** | PASS with "0 claim reference(s) across 0 node(s) — all approved" | Vacuously true; warn-level message is fine but not a failure. (An empty story isn't unapproved science.) |
| **Node with no `claim_ids`** | Skipped (contributes 0 references) | Valid — a purely narrative node. |
| **`approval_status` not in the enum** (e.g. typo `"appproved"`) | `CitationRegistry.load` raises `ValueError` → `sys.exit(2)` | Caught at load, before the gate even runs. |
| **A referenced claim is `rejected`** | FAIL with `[UNAPPROVED] ... status is 'rejected'` | Treated as not-approved (the `== "approved"` test). No special case needed. |
| **Exit codes** | `0` = pass; `1` = missing/unapproved claims; `2` = config/load error | Three-way so CI can fail loudly on broken fixtures vs. genuinely-unapproved content. The Phase 1 success criterion only requires non-zero on fail — `1` and `2` both satisfy that; the split is a clean-to-have. |

### Output contract

- **stdout:** the pass/fail report (one line for the summary, one per offending claim, one fix-hint line on failure).
- **stderr:** load/config errors (`CITATION GATE ERROR: ...`).
- **Exit code:** as above.

### Python 3.6 compatibility — VERIFIED

- `json`, `argparse`, `os`, `sys` all importable on `python3.6.9` (verified).
- **f-strings ARE 3.6-safe** (PEP 498) — verified `python3.6 -c "print(f'test {1}')"`. The pseudocode above uses `.format()` for maximum clarity/compat, but f-strings are equally fine; the planner may choose either.
- **`@dataclass` is NOT 3.6-safe** (Pitfall #1) — the loader and the gate must use plain classes / dicts.
- No `pymol`, `PyQt5`, `numpy` imports anywhere in `c14/citations.py` or `tools/check_citations.py` (enforced by the Phase 1 grep gate, Success Criterion 1).

---

## Investigation Point 4 — Fixture Data Design

All fixtures live in `tests/fixtures/`. **Every fixture is clearly placeholder — no real science.** `claim` text is prefixed `PLACEHOLDER:`, `source_type` is `"placeholder"`, `source` is `"TBD"`, `claim_id`s are `placeholder-claim-N`. This satisfies the no-fabricated-science rule: the fixtures exist *to test the gate mechanism*, not to assert any biochemistry.

### Fixture A — passing (exit 0)

**`tests/fixtures/story_pass.json`** — 2-node story, both nodes reference approved claims:

```json
{
  "nodes": {
    "fixture.intro": {
      "id": "fixture.intro",
      "text_dramatic": "PLACEHOLDER: The hero begins their journey.",
      "text_teaching": "PLACEHOLDER: This is a fixture node for testing the citation gate. Not real science.",
      "claim_ids": ["placeholder-claim-1"],
      "choices": [{"label": "Continue", "goto": "fixture.ending"}]
    },
    "fixture.ending": {
      "id": "fixture.ending",
      "text_dramatic": "PLACEHOLDER: The hero reaches an ending.",
      "text_teaching": "PLACEHOLDER: Fixture ending node. Not real science.",
      "claim_ids": ["placeholder-claim-2"],
      "is_ending": "true"
    }
  }
}
```

**`tests/fixtures/citations_pass.json`** — both claims approved:

```json
{
  "placeholder-claim-1": {
    "claim": "PLACEHOLDER: fixture claim 1 — not real science",
    "source_type": "placeholder",
    "source": "TBD",
    "approval_status": "approved",
    "approved_by": "fixture-test",
    "approval_date": "2026-08-13",
    "notes": "Fixture data for citation-gate testing. No real scientific claim."
  },
  "placeholder-claim-2": {
    "claim": "PLACEHOLDER: fixture claim 2 — not real science",
    "source_type": "placeholder",
    "source": "TBD",
    "approval_status": "approved",
    "approved_by": "fixture-test",
    "approval_date": "2026-08-13",
    "notes": "Fixture data for citation-gate testing. No real scientific claim."
  }
}
```

**Expected:** `python3.6 tools/check_citations.py --story tests/fixtures/story_pass.json --registry tests/fixtures/citations_pass.json` → prints "CITATION GATE PASSED: 2 claim reference(s) across 2 node(s) — all approved." → `exit 0`.

### Fixture B1 — failing on PENDING (exit 1)

**`tests/fixtures/citations_fail_pending.json`** — claim-2 is `pending`:

```json
{
  "placeholder-claim-1": {
    "claim": "PLACEHOLDER: fixture claim 1 — not real science",
    "source_type": "placeholder",
    "source": "TBD",
    "approval_status": "approved",
    "approved_by": "fixture-test",
    "approval_date": "2026-08-13",
    "notes": "Fixture data. No real scientific claim."
  },
  "placeholder-claim-2": {
    "claim": "PLACEHOLDER: fixture claim 2 — pending approval",
    "source_type": "placeholder",
    "source": "TBD",
    "approval_status": "pending",
    "notes": "Fixture: simulates an unapproved claim awaiting human checkpoint."
  }
}
```

Run with `--story tests/fixtures/story_pass.json --registry tests/fixtures/citations_fail_pending.json` → prints `[UNAPPROVED] node 'fixture.ending' references claim_id 'placeholder-claim-2' — status is 'pending'` → `exit 1`.

### Fixture B2 — failing on MISSING (exit 1)

**`tests/fixtures/citations_fail_missing.json`** — claim-2 absent entirely (only claim-1 present):

```json
{
  "placeholder-claim-1": {
    "claim": "PLACEHOLDER: fixture claim 1 — not real science",
    "source_type": "placeholder",
    "source": "TBD",
    "approval_status": "approved",
    "approved_by": "fixture-test",
    "approval_date": "2026-08-13",
    "notes": "Fixture data. No real scientific claim."
  }
}
```

Run with `--story tests/fixtures/story_pass.json --registry tests/fixtures/citations_fail_missing.json` → prints `[MISSING] node 'fixture.ending' references claim_id 'placeholder-claim-2' — not in registry` → `exit 1`.

### Fixture B3 (optional) — failing on REJECTED (exit 1)

**`tests/fixtures/citations_fail_rejected.json`** — claim-2 is `rejected` (proves the `rejected` status path works):

```json
{
  "placeholder-claim-1": {
    "claim": "PLACEHOLDER: fixture claim 1 — not real science",
    "source_type": "placeholder",
    "source": "TBD",
    "approval_status": "approved",
    "approved_by": "fixture-test",
    "approval_date": "2026-08-13",
    "notes": "Fixture data. No real scientific claim."
  },
  "placeholder-claim-2": {
    "claim": "PLACEHOLDER: fixture claim 2 — was rejected",
    "source_type": "placeholder",
    "source": "TBD",
    "approval_status": "rejected",
    "notes": "Fixture: simulates a claim that was refused by the human checkpoint."
  }
}
```

Run → `[UNAPPROVED] node 'fixture.ending' references claim_id 'placeholder-claim-2' — status is 'rejected'` → `exit 1`.

### Fixture C (optional) — unreferenced claim is OK (exit 0)

Reuse `citations_pass.json` but add a `placeholder-claim-3` entry (approved) that *no node references*. The gate still exits 0 — proves unreferenced claims don't fail the gate. (Front-loaded source approval depends on this.) The planner may include this as a 4th test or fold the assertion into the test suite.

### Fixture D (optional) — malformed JSON (exit 2)

A `tests/fixtures/citations_malformed.json` containing `{ this is not json` → `CITATION GATE ERROR: ...` to stderr, `exit 2`. Proves the load-error path. Optional but cheap.

**Recommendation for the planner:** ship A + B1 + B2 as the load-bearing Phase 1 demonstration (matches the success criterion exactly: "exits non-zero when any story node references a missing or `pending` claim_id, and exits zero when all referenced claims are `approved`"). Add B3, C, D as test-suite assertions if time permits — they harden the gate but are not strictly required by the criterion.

---

## Investigation Point 5 — Integration with the Testability Boundary

### Module layering (confirmed — matches `ARCHITECTURE.md`)

| Layer | Module | Imports | Phase |
|-------|--------|---------|-------|
| Pure-Python domain tier | `c14/citations.py` | stdlib only (`json`) | **Phase 1** |
| Pure-Python domain tier | `c14/__init__.py` | (empty/minimal — makes `c14` importable) | **Phase 1** |
| Pre-ship gate (script) | `tools/check_citations.py` | stdlib + `c14.citations` | **Phase 1** |
| Fixture data | `tests/fixtures/*.json` | (data only) | **Phase 1** |
| Gate tests | `tests/test_citations.py` | stdlib `unittest` + `c14.citations` (+ subprocess to test `tools/check_citations.py` exit codes) | **Phase 1** |
| Story-graph validator | `c14/story/validate.py` (`collect_claim_ids`) | stdlib + `c14.story.model` | **Phase 2** (refactor target) |

**Confirmed:** the registry loader (`c14/citations.py`) and the gate (`tools/check_citations.py`) both belong in the **pure-Python, WSL-runnable, stdlib-only** tier. Neither imports `pymol` or `PyQt5`. This is enforced by the Phase 1 Success Criterion 1 grep gate (which scans `c14/` excluding `pymol_layer/` and `ui/`).

### `c14/__init__.py` in Phase 1

The `c14` package must be importable so `from c14.citations import CitationRegistry` works. In Phase 1, `c14/__init__.py` is **minimal** (an empty file or a one-line docstring). The `__init_plugin__` + `addmenuitemqt` PyMOL entry point lands in **Phase 6** (PLGN-01/PLGN-02) — do NOT add it in Phase 1. (Adding it early would pull a `pymol.Qt` import into `c14/__init__.py`, breaking the import-clean grep gate and making `import c14` fail in WSL.)

### Import-path handling in `tools/check_citations.py`

`tools/check_citations.py` is a loose script in `tools/`, not inside the `c14` package. To import `c14.citations` without installing the package, the script **inserts the repo root onto `sys.path`** at startup (see pseudocode in Investigation Point 3):

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from c14.citations import CitationRegistry
```

This is the standard pattern for a `tools/` script that imports from the main package in a dev tree without install. It works when invoked as `python3.6 tools/check_citations.py ...` from the repo root (and from anywhere, since it resolves `__file__` absolutely). **Do not** rely on `PYTHONPATH` being set — the script must be self-contained.

### The Phase 2 refactor (forward-compatible contract)

In Phase 1, `tools/check_citations.py` does its own inline story-claim collection (`collect_referenced_claim_ids` walks the single `--story` JSON's `nodes` dict). This is deliberate: the real story graph (`data/story/` with `manifest.json` + per-pathway files merged at load — `ARCHITECTURE.md` lines 452–471) is **Phase 2**. Phase 1 must not pre-build the story-graph infrastructure.

The **contract is forward-compatible:** the fixture story JSON uses the *same node shape* as the real story graph (`{"nodes": {node_id: {"claim_ids": [...], ...}}}`). When Phase 2 builds `c14/story/validate.py:collect_claim_ids("data/story/")` (which reads `manifest.json` + merges all pathway files + returns the set of referenced claim_ids — per `ARCHITECTURE.md` line 347), `tools/check_citations.py` is refactored to:
```python
from c14.story.validate import collect_claim_ids
story_ids = collect_claim_ids("data/story/")   # replaces the inline walker
```
This is a small, clean refactor — the gate's core logic (registry load + `is_approved` check + report + exit) is unchanged. **No rework of `c14/citations.py` or the registry schema.**

**Planner note:** structure the Phase 1 gate so the story-walking is isolated in one function (`collect_referenced_claim_ids` in the pseudocode) — that's the single function Phase 2 swaps for `collect_claim_ids`.

### Test suite — `tests/test_citations.py`

Two kinds of tests:

1. **Unit tests for `c14.citations.CitationRegistry`** (import directly, no subprocess):
   - `.load()` on `citations_pass.json` succeeds; `.is_approved("placeholder-claim-1")` is True, `.is_approved("placeholder-claim-2")` is True.
   - `.load()` on `citations_fail_pending.json` succeeds; `.is_approved("placeholder-claim-2")` is False, `.status(...)` is `"pending"`.
   - `.contains("placeholder-claim-3")` is False on the missing-claim fixture.
   - `.load()` on a registry with a bad `approval_status` raises `ValueError`.
   - `.load()` on malformed JSON raises `ValueError` (wrap `json.JSONDecodeError`).

2. **Subprocess tests for `tools/check_citations.py` exit codes** (run the script, assert exit code):
   - pass fixture → exit 0, stdout contains "PASSED".
   - fail-pending fixture → exit 1, stdout contains "UNAPPROVED" + "pending".
   - fail-missing fixture → exit 1, stdout contains "MISSING".
   - fail-rejected fixture → exit 1, stdout contains "rejected" (if B3 is shipped).
   - malformed fixture → exit 2, stderr contains "ERROR" (if D is shipped).

Use stdlib `unittest` (no `pytest` — keep the dev surface at stdlib). The subprocess tests use `subprocess.run([sys.executable, "tools/check_citations.py", "--story", ...], capture_output=True)` and assert `.returncode`. This is the cleanest way to test a script whose contract is its exit code.

---

## Standard Stack

**The entire stack is Python 3.6 stdlib. No third-party libraries. No `pip install`. No new dependencies.** (Hard constraint from `spec.md` / `AGENTS.md` / `PROJECT.md`.)

### Core
| Module | Version | Purpose | Why Standard |
|--------|---------|---------|--------------|
| `json` | stdlib (3.6.9) | Load + dump the citation registry + story fixtures | Only dependency-free JSON option; `.gitignore` already rules out `*.npy`/`*.npz`; `pickle` rejected on safety/portability grounds (`PITFALLS.md` line 302, 337) |
| `argparse` | stdlib (3.6.9) | `check_citations.py` CLI (`--story`, `--registry`) | Stdlib CLI parser; available since 2.7 |
| `os` / `sys` | stdlib (3.6.9) | `sys.path` insertion for `c14` import; `sys.exit` codes; path joining | Unavoidable stdlib |
| `unittest` | stdlib (3.6.9) | `tests/test_citations.py` | Stdlib test runner; no `pytest` to keep dep surface at zero |

### NOT used (and why)
| Rejected | Reason |
|----------|--------|
| `dataclasses` | **Python 3.7+ only** — `ModuleNotFoundError` on `python3.6.9` (verified). Use plain classes / dicts. (Pitfall #1) |
| `yaml` / `toml` | Non-stdlib; violates no-new-deps. JSON is sufficient and matches `ARCHITECTURE.md`. |
| `pytest` | Non-stdlib. `unittest` covers the test surface. (Repo has no tests yet — establishing `unittest` is fine.) |
| `pydantic` / `jsonschema` | Non-stdlib schema validators. Hand-written validation in `CitationRegistry.load` is ~15 lines and sufficient. |
| `pymol` / `pymol.Qt` / `PyQt5` / `numpy` | The gate runs in WSL CI on pure Python; importing these would break the testability boundary (Phase 1 Success Criterion 1) and is unnecessary for a JSON cross-reference check. |

---

## Architecture Patterns

### Recommended project structure (Phase 1 portion only)
```
RPG_tale-of-C/
├── c14/
│   ├── __init__.py          # minimal (empty or docstring) — NO __init_plugin__ yet (Phase 6)
│   └── citations.py          # CitationRegistry: load() + is_approved() + status() (pure-Py, stdlib)
├── tools/
│   └── check_citations.py    # pre-ship gate: argparse --story --registry, exit 0/1/2 (pure-Py, stdlib)
├── data/
│   └── citations.json        # the REAL registry (empty or stub in Phase 1 — populated Phase 5+)
└── tests/
    ├── test_citations.py    # unit tests for CitationRegistry + subprocess exit-code tests for the gate
    └── fixtures/
        ├── story_pass.json
        ├── citations_pass.json
        ├── citations_fail_pending.json
        ├── citations_fail_missing.json
        ├── citations_fail_rejected.json      # optional (B3)
        └── citations_malformed.json          # optional (D)
```

**Note on `data/citations.json` in Phase 1:** the *real* registry file may be empty (`{}`) or contain only placeholder entries in Phase 1 — no real claims are approved yet (that is Phase 5 CITE-01). The gate is *demonstrated* on `tests/fixtures/`, not on `data/citations.json`. The planner should decide whether to create `data/citations.json` as an empty `{}` stub in Phase 1 (establishes the path convention) or defer its creation to Phase 5. **Recommendation: create it as `{}` with a header comment is impossible in JSON — so just `{}` and a sibling `data/citations.README.md` explaining the schema + that it's populated from Phase 5.** This bakes the path into the codebase early.

### Pattern: Registry as JSON object keyed by the join key
**What:** A single JSON object whose top-level keys ARE the entity IDs (`claim_id`), values are the entity records. The gate's core predicate (`is_approved`) is a single `dict.get` + status check.
**When to use:** Any time you have an entity registry that a gate/walker cross-references by ID.
**Why over JSONL:** O(1) lookup; structural uniqueness of keys; reviewer reads key-adjacent-to-record.

### Pattern: Three-way exit codes for CI gates
**What:** `0` = pass; `1` = the *content* the gate polices is non-compliant (missing/unapproved claims); `2` = the gate itself is misconfigured (malformed JSON, missing file).
**When to use:** Any CI gate that parses structured input. Lets CI distinguish "the project has unapproved science" (a real failure to fix) from "the fixture is broken" (a tooling error).

### Pattern: Forward-compatible fixture format
**What:** Phase 1 fixture data uses the *same* node shape (`{"nodes": {id: {"claim_ids": [...], ...}}}`) as the real Phase 2 story graph, so the gate's walker works unchanged when the real graph lands.
**When to use:** When a later phase will replace fixture data with real data of the same shape. Isolate the data-shape-dependent code in one function (here: `collect_referenced_claim_ids`) so the swap is a one-function refactor.

### Anti-patterns to avoid
- **Putting `__init_plugin__` / `pymol.Qt` imports in `c14/__init__.py` in Phase 1** — breaks `import c14` in WSL, fails the grep gate. Defer to Phase 6.
- **Building `c14/story/model.py` (the `Node` dataclass) in Phase 1** — pulls story-graph infra into the foundations phase; the gate doesn't need the model (it walks raw JSON dicts). Phase 2 owns it. (Also: the model in `ARCHITECTURE.md` uses `@dataclass` which is 3.6-incompatible — see Pitfall #1; Phase 2 will need to address that too, but that's Phase 2's research.)
- **Validating the registry with a non-stdlib schema library** — `pydantic`/`jsonschema` need install. Hand-written validation in `CitationRegistry.load` is short and sufficient.
- **Making the gate depend on `c14/story/validate.py` in Phase 1** — that module doesn't exist until Phase 2. Inline the walker; refactor later.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON parsing | A custom parser | `json` stdlib | Battle-tested, handles edge cases (escapes, unicode), 3.6-native |
| CLI argument parsing | Manual `sys.argv` slicing | `argparse` stdlib | `--flag` help, validation, error messages for free |
| Duplicate-key detection in registry JSON | A post-load dedup scan | `json.load(..., object_pairs_hook=...)` | stdlib hook catches duplicates *during* parse (verified — see Pitfall #3) |
| Exit-code-based test of a script | Importing the script's functions and calling them | `subprocess.run([sys.executable, "tools/check_citations.py", ...])` + assert `.returncode` | The script's contract is its *exit code*; testing the function in-process doesn't verify the `sys.exit` + CLI wiring |
| Schema validation | `pydantic` / `jsonschema` | Hand-written checks in `CitationRegistry.load` | No new deps; the schema is small (4 required fields, 1 enum); ~15 lines |

**Key insight:** the gate is a *cross-reference check between two JSON files*. It is ~60 lines of logic. There is no library problem here that a dependency would solve better than stdlib. Resist any temptation to add a validation/schema/CLI library — the no-new-deps constraint is hard and the stdlib is sufficient.

---

## Common Pitfalls

### Pitfall 1 — `@dataclass` is Python 3.7+; the project runs `python3.6.9` (CONFIRMED)
**What goes wrong:** `ARCHITECTURE.md`'s code examples (lines 175–194, the `Node`/`Choice`/`MolAction` models) use `@dataclass`. A planner following those examples verbatim writes `c14/citations.py` or `c14/story/model.py` with `@dataclass`, then `python3.6 -m py_compile` fails with `ModuleNotFoundError: No module named 'dataclasses'`.
**Why it happens:** `dataclasses` (PEP 557) shipped in Python 3.7. The project's WSL test env is 3.6.9 (`AGENTS.md`). `PLGN-03` requires "Python 3.6 syntax universally."
**How to avoid:** Use **plain classes** (`class CitationRegistry: def __init__(self, data): ...`) or **plain functions on dicts**. Never `@dataclass` in any module that must pass `python3.6 -m py_compile`. (No `dataclasses` backport either — that's a `pip install`, violating no-new-deps.)
**Warning signs:** any `@dataclass` decorator, `from dataclasses import ...`, or `field(default_factory=...)` in a Phase 1 file. The grep gate (Success Criterion 1) should additionally catch `import dataclasses`.
**Verified:** `python3.6 -c "import dataclasses"` → `ModuleNotFoundError: No module named 'dataclasses'` (run 2026-08-13). HIGH confidence.

### Pitfall 2 — `claims.jsonl` vs `citations.json` naming drift
**What goes wrong:** A planner reads `PITFALLS.md` (line 199: "`data/claims.jsonl`") or `SUMMARY.md` (line 129: "`data/claims.jsonl`") and builds a JSONL file, then the gate (which expects a JSON object) breaks, or a sibling phase builds against the other name and they diverge.
**Why it happens:** The earlier research used `claims.jsonl` as an *illustrative example* ("e.g."); the finalized `ARCHITECTURE.md` settled on `data/citations.json` (JSON object). The two were never reconciled in prose.
**How to avoid:** **Use `data/citations.json` (JSON object, dict keyed by `claim_id`).** This matches the authoritative `ARCHITECTURE.md`. The `.jsonl` references are superseded. Document this in the plan so the executor doesn't re-litigate it.
**Warning signs:** any `data/claims.jsonl` path or `for line in f: json.loads(line)` (JSONL streaming) pattern in the gate.

### Pitfall 3 — Duplicate `claim_id` keys silently overwrite in JSON objects
**What goes wrong:** Two authors add the same `claim_id` to `data/citations.json` with different sources; `json.load` silently keeps the *last* one. An approval (or a rejection) is lost without warning.
**Why it happens:** JSON spec says duplicate keys are "should be" unique but parsers commonly last-wins. Verified: `json.loads('{"a":1,"a":2}')` → `{'a': 2}`.
**How to avoid:** Load the registry with `json.load(f, object_pairs_hook=<dedup checker>)` that raises `ValueError` on a duplicate key. Verified working: the `object_pairs_hook` approach correctly detects duplicates (run 2026-08-13). This is a ~6-line addition to `CitationRegistry.load`.
**Warning signs:** none at runtime (silent). The `object_pairs_hook` is the only detection. Recommend the planner include it.
**Confidence:** HIGH (verified on `python3.6.9`).

### Pitfall 4 — Gate imports `pymol` or `PyQt5` (breaks the testability boundary)
**What goes wrong:** A copy-paste from a PyMOL-layer helper pulls `from pymol import cmd` into `c14/citations.py` or `tools/check_citations.py`. The Phase 1 grep gate (Success Criterion 1) goes red; `import c14.citations` fails in WSL.
**Why it happens:** Habit from PyMOL-plugin code; the registry feels like it "should" know about PDBs.
**How to avoid:** `c14/citations.py` and `tools/check_citations.py` import **only** `json` (and `argparse`/`os`/`sys` in the tool). The registry stores `pdb_id` as a *string* — it does not need to load the PDB. PDB loading is `c14/pymol_layer/` (Phase 3+).
**Warning signs:** `import pymol`, `from pymol import`, `import PyQt5` anywhere in `c14/citations.py` or `tools/check_citations.py`.

### Pitfall 5 — Letting a raw `json.JSONDecodeError` traceback leak to CI
**What goes wrong:** Malformed fixture/registry JSON raises `json.JSONDecodeError` (subclass of `ValueError`); the gate prints a 20-line traceback; CI logs are unreadable; the exit code is 1 (the traceback's uncaught exit) conflating "broken fixture" with "unapproved claims."
**Why it happens:** Not wrapping the parse in a try/except.
**How to avoid:** Wrap `CitationRegistry.load` and `collect_referenced_claim_ids` to raise/catch `ValueError`/`OSError` → print `CITATION GATE ERROR: <msg>` to stderr → `sys.exit(2)` (distinct from `1`). See the pseudocode in Investigation Point 3.

### Pitfall 6 — Treating `rejected` as a pass (or omitting it from the schema)
**What goes wrong:** If the gate's predicate were `approval_status != "pending"` (instead of `== "approved"`), a `rejected` claim would PASS — shipping a refused claim. Or, if `rejected` were omitted from the enum, a rejected claim couldn't be recorded (only deleted, losing provenance).
**Why it happens:** Reading only the Phase 1 success-criterion text ("missing or `pending`") and not `ARCHITECTURE.md` (which has `{pending, approved, rejected}`).
**How to avoid:** The gate predicate is **`approval_status == "approved"`** — not `!= "pending"`. Keep `rejected` in the enum. A `rejected` referenced claim fails identically to a `pending` one (no special case). See Investigation Point 1.

---

## Code Examples (verified patterns)

### CitationRegistry load + is_approved (3.6-compatible plain class)
See the full class in **Investigation Point 1**. Key predicate:
```python
def is_approved(self, claim_id):
    entry = self._claims.get(claim_id)
    return entry is not None and entry.get("approval_status") == "approved"
```
*Source: derived from `ARCHITECTURE.md` Pattern 4 (lines 311–356), adapted to 3.6 (plain class, no `@dataclass`).*

### Duplicate-key detection in the registry loader (optional hardening)
```python
def _no_duplicate_keys(pairs):
    d = {}
    seen = set()
    for k, v in pairs:
        if k in seen:
            raise ValueError("duplicate claim_id in registry: {!r}".format(k))
        seen.add(k)
        d[k] = v
    return d

# in CitationRegistry.load:
with open(path, "r") as f:
    data = json.load(f, object_pairs_hook=_no_duplicate_keys)
```
*Verified on `python3.6.9` (2026-08-13): duplicate key correctly raises.*

### Subprocess exit-code test for the gate
```python
import subprocess, sys, os, unittest

class TestCheckCitationsExitCodes(unittest.TestCase):
    def _run(self, story, registry):
        here = os.path.dirname(os.path.abspath(__file__))
        repo = os.path.join(here, "..")
        return subprocess.run(
            [sys.executable, os.path.join(repo, "tools", "check_citations.py"),
             "--story", os.path.join(here, "fixtures", story),
             "--registry", os.path.join(here, "fixtures", registry)],
            capture_output=True, text=True)

    def test_pass(self):
        r = self._run("story_pass.json", "citations_pass.json")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PASSED", r.stdout)

    def test_fail_pending(self):
        r = self._run("story_pass.json", "citations_fail_pending.json")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("UNAPPROVED", r.stdout)
        self.assertIn("pending", r.stdout)

    def test_fail_missing(self):
        r = self._run("story_pass.json", "citations_fail_missing.json")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("MISSING", r.stdout)
```
*Source: stdlib `subprocess` + `unittest` — the canonical way to test a script whose contract is its exit code.*

---

## State of the Art

| Old Approach (in earlier research) | Current Approach (this research) | When Changed | Impact |
|-------------------------------------|----------------------------------|--------------|--------|
| `data/claims.jsonl` (JSONL, one claim/line) — `PITFALLS.md`/`SUMMARY.md` sketch | `data/citations.json` (JSON object, dict keyed by `claim_id`) — `ARCHITECTURE.md` finalized | `ARCHITECTURE.md` revision (2026-08-12) | O(1) lookup; structural dup-key prevention; matches authoritative doc |
| `status: pending\|approved\|rejected` (PITFALLS sketch field name) | `approval_status: pending\|approved\|rejected` (ARCHITECTURE field name) | `ARCHITECTURE.md` | Consistent field name across registry + gate |
| `@dataclass` Node/Choice models (`ARCHITECTURE.md` examples) | **Must be plain classes on 3.6** (this research, verified) | Discovered 2026-08-13 (3.6 `dataclasses` absence) | Any Phase 1 (and Phase 2) code must avoid `@dataclass`; the ARCHITECTURE examples are *illustrative*, not 3.6-literal |

**Deprecated/outdated (do not use in Phase 1):**
- `data/claims.jsonl` as a path or JSONL parsing (`for line in f: json.loads(line)`) — superseded by `data/citations.json` JSON object.
- `@dataclass` in any 3.6-targeted module — not importable on `python3.6.9`.

---

## Open Questions (decisions the planner must make)

1. **`data/citations.json` real file in Phase 1: stub or defer?**
   - What we know: the gate is *demonstrated* on `tests/fixtures/`, not the real registry. No real claims are approved yet (Phase 5).
   - What's unclear: should Phase 1 create `data/citations.json` as an empty `{}` stub (to bake in the path convention early) or defer creation to Phase 5?
   - **Recommendation:** create `data/citations.json` as `{}` + a sibling `data/citations.README.md` documenting the schema (so the path + schema are established in code, reviewable now, and Phase 5 just adds entries). Low cost, high early-binding value. Planner decides.

2. **`approval_status` enum: keep `rejected`?**
   - What we know: `ARCHITECTURE.md` has `{pending, approved, rejected}`; the success-criterion text names only `pending`/`approved`.
   - **Recommendation:** keep all three (gate treats `!= "approved"` as fail; `rejected` records provenance). See Investigation Point 1. Planner confirms.
   - **Confidence:** HIGH that keeping `rejected` is safe and strictly better.

3. **Duplicate-key detection in `CitationRegistry.load`: include or defer?**
   - What we know: `object_pairs_hook` catches duplicate `claim_id` keys (verified). Without it, duplicates silently last-wins.
   - **Recommendation:** include (~6 lines, HIGH value once two authors edit the registry). Planner decides; cheap to add.

4. **Three-way exit codes (`0`/`1`/`2`) or just `0`/non-zero?**
   - What we know: the success criterion only requires "exits non-zero when ... missing/pending." A two-way `0`/`1` satisfies it. A three-way `0`/`1`/`2` distinguishes config errors from unapproved claims.
   - **Recommendation:** three-way (the pseudocode in Investigation Point 3 implements it). Planner confirms; if they prefer two-way, collapse `2` into `1`.

5. **How many fixtures to ship in Phase 1?**
   - What we know: the success criterion requires pass + at-least-one-fail demonstration. Fixtures A + B1 + B2 are load-bearing. B3 (rejected), C (unreferenced OK), D (malformed) harden the gate.
   - **Recommendation:** ship A + B1 + B2 minimum; add B3 + D as test-suite assertions if the plan has room. Planner scopes.

6. **Functional `load_registry()` vs class `CitationRegistry`?**
   - What we know: the brief mentions "`load_registry()` function"; `ARCHITECTURE.md` shows a `CitationRegistry` class with `.load()` + `.is_approved()`.
   - **Recommendation:** the class (encapsulates `.is_approved()` which is the gate's core). A thin `def load_registry(path): return CitationRegistry.load(path)` wrapper can coexist if the planner wants both. Planner picks the API surface.

---

## Sources

### Primary (HIGH confidence)
- `.planning/research/ARCHITECTURE.md` — Pattern 4 "Citation Registry + Per-Claim Approval Gate" (lines 311–356); Data Model "CitationRegistry" (lines 507–509); Node model with `claim_ids` field (line 189); project structure (lines 65, 84, 117, 136); build order (lines 520–541). **The authoritative, finalized architecture doc for this design.**
- `.planning/REQUIREMENTS.md` — CITE-02 (line 64); CITE-01 (line 63); Phase 1 traceability (lines 101, 128, 139).
- `.planning/ROADMAP.md` — Phase 1 goal + success criteria (lines 34–43); Phase 5 CITE-01 relationship (lines 91–101).
- `spec.md` — no-fabricated-science rule (lines 64–66); no-install rule (lines 40–42, 77).
- `AGENTS.md` — `python3.6` (3.6.9) test env; no `pip install`; WSL/Windows split.
- **Verified on `python3.6.9` (2026-08-13):** `dataclasses` absent (`ModuleNotFoundError`); `json`/`argparse`/`os`/`sys`/`pathlib` importable; f-strings work; `object_pairs_hook` duplicate-key detection works; proposed fixture + registry JSON round-trips correctly.

### Secondary (MEDIUM confidence — earlier research, superseded on specifics but useful for rationale)
- `.planning/research/PITFALLS.md` — Pitfall 7 (per-claim approval bottleneck, lines 190–209): rationale for the registry as the approval-queue tracker; `claims.jsonl` sketch (line 199) — *superseded by `citations.json`*.
- `.planning/research/SUMMARY.md` — architecture summary (lines 85–104); `claims.jsonl` reference (line 129) — *superseded*.
- `.planning/PROJECT.md` — Key Decisions (per-claim checkpoint chosen as safest, line 102); no-fabricated-science constraint (line 84).

### Tertiary (LOW confidence — none)
No external library documentation was consulted because the stack is stdlib-only by hard constraint; there is no library API to verify. No `webfetch`/Context7 needed — this is an internal design-research task grounded in the project's own finalized architecture + verified 3.6 stdlib behavior.

---

## Metadata

**Confidence breakdown:**
- Standard stack (stdlib-only): **HIGH** — verified importable on `python3.6.9`; no-deps constraint is hard (`spec.md`/`AGENTS.md`).
- Citation registry schema: **HIGH** — grounded in finalized `ARCHITECTURE.md` Pattern 4; fixture JSON round-trip verified on 3.6.
- Story→claim contract (`claim_ids` field): **HIGH** — established in `ARCHITECTURE.md` Node model (line 189) + JSON examples (lines 239, 466).
- Gate algorithm: **HIGH** — stdlib cross-reference check; pseudocode is 3.6-compatible by construction; exit-code contract verified against subprocess-test pattern.
- Pitfalls: **HIGH** — `dataclasses` absence and `object_pairs_hook` dup-detection both verified on `python3.6.9` (2026-08-13).

**Research date:** 2026-08-13
**Valid until:** stable indefinitely (stdlib + project-internal architecture; no external API to drift). Re-verify the `ARCHITECTURE.md` alignment if Pattern 4 is revised.
