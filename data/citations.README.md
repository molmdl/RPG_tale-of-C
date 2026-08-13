# `data/citations.json` — Citation Registry Schema

Citation registry for the no-fabricated-science gate. Each `claim_id` maps to a source + `approval_status`. Populated from Phase 5 (CITE-01); Phase 1 ships an empty stub (`{}`) to bake the path convention into the codebase early.

The pre-ship gate (`tools/check_citations.py`) cross-references story nodes' `claim_ids` against this registry and exits non-zero on any missing or non-`approved` claim. **This file is a repo-root content source file** (NOT a bundled plugin runtime asset — that lives in `c14/data/`); it is read at pre-ship time by the gate, not at plugin runtime.

## Top-level shape

A bare JSON object keyed by `claim_id`. No top-level wrapper (no `{"claims": {...}}`, no `version` field) — keeps the registry a flat lookup table. (If a schema version is wanted later, nest it under a reserved `_meta` key; deferred — out of scope for Phase 1.)

```json
{
  "<claim_id_1> { ...claim record... },
  "<claim_id_2>": { ...claim record... }
}
```

Duplicate `claim_id` keys are rejected at load time (`object_pairs_hook` in `c14/citations.py`). The loader raises `ValueError("duplicate claim_id in registry: ...")` rather than silently last-wins.

## Per-claim record schema

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `claim` | string | YES | One-line summary of what the claim asserts (human-review anchor) |
| `source_type` | enum string | YES | One of: `"textbook"`, `"libretexts"`, `"doi"`, `"pdb"`, `"pubchem"`, `"placeholder"` (`placeholder` is for fixture data only) |
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

### Per-source-type required fields (load-time validation, recommended)

- `source_type == "pdb"` → `pdb_id` required; `resolution_angstrom` + `url` recommended.
- `source_type == "doi"` → `doi` required; `url` recommended.
- `source_type == "pubchem"` → `pubchem_cid` required.
- `source_type == "placeholder"` → none beyond the base required set (fixture data only).

For Phase 1, the loader validates the base required fields (`claim`, `source_type`, `source`, `approval_status`) and that `approval_status ∈ {pending, approved, rejected}`. Per-source-type field validation can be added later (the gate only reads `approval_status`).

## The `approval_status` enum

The gate predicate is **`approval_status == "approved"`**. A `rejected` claim fails identically to a `pending` one (no special case). Keeping `rejected` records provenance (why a claim was refused) rather than silently deleting — deleting a refused claim would make a future re-introduction look like a *new* claim and lose the rejection history.

- `pending` — claim is queued for human review (Phase 5 CITE-01). Gate fails.
- `approved` — human approved the claim against its source. Gate passes.
- `rejected` — human refused the claim (recorded for provenance via `notes`). Gate fails.

## Example entry (clearly placeholder — no real science)

```json
{
  "placeholder-claim-1": {
    "claim": "PLACEHOLDER: fixture claim 1 — not real science",
    "source_type": "placeholder",
    "source": "TBD",
    "approval_status": "approved",
    "approved_by": "fixture-test",
    "approval_date": "2026-08-13",
    "notes": "PLACEHOLDER fixture data for citation-gate testing. No real scientific claim."
  }
}
```

## Notes

- **Duplicate `claim_id` keys are rejected at load time** (`object_pairs_hook` in `c14/citations.py`). Two authors adding the same `claim_id` will get a clear `ValueError` instead of silent last-wins clobbering.
- **Unreferenced claims are OK.** A pre-approved-but-not-yet-used claim does not fail the gate — front-loaded source approval (Phase 5) intentionally creates these. The gate checks *referenced* claims only.
- **Phase 1 ships an empty stub (`{}`).** The gate is demonstrated on `tests/fixtures/`, not on this file. Real claims land in Phase 5+ (CITE-01).

## See also

- `c14/citations.py` — the loader (`CitationRegistry.load()` + `.is_approved()`).
- `tools/check_citations.py` — the pre-ship gate (`--story` + `--registry`, exits 0/1/2).
- `tests/fixtures/` — fixture data demonstrating pass + fail paths.
- `.planning/phases/01-foundations-testability-citation-gate/01-RESEARCH-citations.md` — full design rationale + verified 3.6 patterns.
