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
| `source_id` | string | NO (Phase 5+) | References a `source_id` key in `data/sources.json` (workflow b/c/d). Links this claim to its source record for source-inherited approval. |
| `claim_text` | string | NO (Phase 5+) | Full claim text to be approved — more detailed than the `claim` one-liner. The two **coexist** (`claim` = one-liner summary, `claim_text` = full assertion; neither replaces the other). |
| `review_tier` | enum string | NO (hybrid c) | One of: `"high-stakes"`, `"routine"`. Used by hybrid workflow (c) to flag individually-reviewed vs source-inherited claims. |
| `inherits_source_approval` | bool | NO (b/c/d) | `true` if the claim fast-tracks via an approved source (routine claims); `false` if it requires individual per-claim review (high-stakes). |
| `review_notes` | string | NO (hybrid c) | Free-text review notes. **Mandatory for `review_tier: "high-stakes"` claims** under hybrid workflow (c); optional for routine. |

### Per-source-type required fields (recommended, NOT load-time-enforced)

- `source_type == "pdb"` → `pdb_id` required; `resolution_angstrom` + `url` recommended.
- `source_type == "doi"` → `doi` required; `url` recommended.
- `source_type == "pubchem"` → `pubchem_cid` required.
- `source_type == "placeholder"` → none beyond the base required set (fixture data only).

### Load-time validation vs documented-required (Phase 1 + Phase 5+)

The loader (`c14/citations.py:87-97`) enforces ONLY two things at load time: (1) each entry is a **dict**, and (2) `approval_status ∈ {pending, approved, rejected}`. It does **NOT** validate `claim`, `source_type`, or `source` at load time — those remain **documented-required** fields (authors must include them for human-review consistency; the Phase 5 seed entries include them), but they are NOT load-time-enforced. Per-source-type field validation can be added later (the gate only reads `approval_status`).

**Backward compatibility (Phase 5+):** the extended fields (`source_id`, `review_tier`, `claim_text`, `inherits_source_approval`, `review_notes`) are **ignored by the loader** — `c14/citations.py:87-97` only checks `dict` + `approval_status`, so the extended claim records load cleanly with zero loader change. The Phase 1 gate (`tools/check_citations.py`) is UNCHANGED: its predicate `approval_status == "approved"` (strict equality, NOT `!= "pending"` — research Pitfall 6 preserved) is untouched, and `data/sources.json` (below) is a separate file the gate never opens.

### Routine-claim warning flag (hybrid workflow c)

The project uses the **hybrid workflow (c)** decided in Phase 5 Plan 03: sources are approved up front (batch), **high-stakes** claims get individual per-claim review, and **routine** claims are source-inherited (fast-track). Per the user's enhancement ("(c) plus a warning on auto-stuff so i can check when i have time"), routine claims carry **`review_tier: "routine"` + `inherits_source_approval: true`** in the registry. This is a **VISIBILITY mechanism, NOT a blocking gate** — the Phase 1 gate still passes routine claims via the source's approval (`approval_status == "approved"`); the flag just lets the human spot-check routine claims at leisure.

To spot-check routine claims, filter the registry on either:
- `review_tier == "routine"`, or
- `inherits_source_approval == true`.

High-stakes claims carry **`review_tier: "high-stakes"` + `inherits_source_approval: false`** + a non-empty `review_notes` (mandatory for high-stakes); these get individual per-claim review in the human approval checkpoint. The advisory taxonomy: HIGH-STAKES = [RNG-weights, protonation-defaults, carbon-fate, contested]; ROUTINE = [enzyme-catalyzes-reaction-X, enzyme name/EC/cofactor, PDB existence/resolution/citation, pathway ordering].

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

## `data/sources.json` — Source Registry (Phase 5+)

A **separate** registry file holding candidate **source** records (one per approved-citable source), introduced in Phase 5 for the batch-by-source (b) / hybrid (c) / per-source-record (d) workflows. **The Phase 1 gate NEVER reads this file** — `tools/check_citations.py` opens only `data/citations.json`; `data/sources.json` is a process-convention registry the gate is blind to (verified in `05-RESEARCH-source-approval.md` §2). The file exists ONLY when the workflow is (b)/(c)/(d); it is NOT created for strict per-claim (a).

### Top-level shape

A bare JSON object keyed by `source_id` (mirrors the `citations.json` shape — no top-level wrapper). Each `source_id` maps to a source record.

```json
{
  "<source_id_1>": { ...source record... },
  "<source_id_2>": { ...source record... }
}
```

### Source record schema

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `reference` | string | YES | Human-readable source label (book title + chapter, LibreTexts module name, RCSB entry description) |
| `url` | string | NO | Canonical URL when applicable (LibreTexts hub/page, RCSB structure page) |
| `license` | string | NO | Open license when applicable (e.g. `"CC BY-NC-SA 4.0"` for LibreTexts) |
| `source_type` | enum string | YES | One of: `"educational_open_textbook"`, `"print_textbook"`, `"structural_database_entry"`, `"primary_literature"`, `"nuclear_database"`. (This enum is DISTINCT from the `citations.json` `source_type` enum.) |
| `pdb_doi` | string | NO | PDB DOI (e.g. `"10.2210/pdbXXXX/pdb"`) when `source_type == "structural_database_entry"` |
| `approval_status` | enum string | YES | One of: `"pending"`, `"approved"`, `"rejected"`. The human approves sources in a batch (Phase 5 checkpoint); routine claims then inherit via their `source_id`. |
| `approved_by` | string | NO | Human approver identifier (only meaningful when `approval_status == "approved"` — omit until approved) |
| `approved_date` | string | NO | ISO date (YYYY-MM-DD) of approval (omit until approved) |
| `notes` | string | NO | Free-text notes (verification date, subpage-URL-to-confirm flags, primary citation string for PDB entries, etc.) |

> **Note on `approved_by` / `approved_date`.** These are OMITTED while a source is `pending` (the Phase 5 first batch ships with all sources `pending`); they are populated when the human flips a source to `approved` in the Plan 05 checkpoint.

### Duplicate-key hook convention

`data/sources.json` is not yet opened by any loader (the Phase 1 gate does not read it; an optional `tools/check_sources.py` drift-detection gate is deferred advisory work). When a `sources.json` loader is eventually built, it MUST use the same `object_pairs_hook` convention as `c14/citations.py` (`_no_duplicate_keys`) to reject duplicate `source_id` keys at load time rather than silently last-wins. (Two authors adding the same `source_id` with different references would otherwise clobber each other with no warning.)

## See also

- `c14/citations.py` — the loader (`CitationRegistry.load()` + `.is_approved()`).
- `tools/check_citations.py` — the pre-ship gate (`--story` + `--registry`, exits 0/1/2).
- `data/sources.json` — the Phase 5+ source registry (separate file; the Phase 1 gate never reads it; used by the batch/hybrid/per-source workflows to approve sources up front).
- `tests/fixtures/` — fixture data demonstrating pass + fail paths.
- `.planning/phases/01-foundations-testability-citation-gate/01-RESEARCH-citations.md` — full design rationale + verified 3.6 patterns.
- `.planning/phases/05-pre-content-key-decisions-source-approval/05-RESEARCH-source-approval.md` — Phase 5 source-approval workflow options + the two-file schema extension.
