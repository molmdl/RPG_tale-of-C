---
phase: 07-content-expansion-i-glucose
plan: 12
subsystem: story-graph
tags: [restoration-topology, story-json, edits-json-contract, sequence-alignment, headless-pymol-probe, reachability-invariants, aconitase, pfk]

# Dependency graph
requires:
  - phase: 07-content-expansion-i-glucose (07-01)
    provides: "DC-A outcome = ADD the 2 restored nodes (the ONLY sanctioned topology change, 55→57); OQ-K = plan 12 owns the count-test updates in the SAME plan"
  - phase: 07-content-expansion-i-glucose (07-02, 07-03, 07-04, 07-05)
    provides: "PFK text-only fallback (no 4PFK applyEdit); D6 = 1ACO bovine cast + the owed S112 mapping; 05.3 align op convention (op=align, method=super); approved -cand registry ids"
  - phase: 05.3-wt-aligned-structure-load-convention
    provides: "The restoration-reveal on_enter op vocabulary: edit → load WT → align → present"
provides:
  - "gly.pfk_restored + tca.aconitase_restored — the two FIXED branch_node targets every restoration edit routes to (plan 14 binds edits.json against these ids)"
  - "The DERIVED human↔bovine aconitase mapping: human ACO2 S112 (UniProt Q99798) ↔ bovine 1ACO chain A resi 85 (SER) — plan 14's edits.json sele"
  - "Empirical chain-case rule: PyMOL matches 'chain A' (uppercase) only — MolAction seles are uppercase; edits.json signature round-trip is case-independent (signature() lowercases both sides)"
  - "57-node / 21-ending invariants green (325 tests; 20→21 reachability tests)"
affects: [plan 14 (edits.json branch_node + signatures), plans 08/13 (restored-node text + claim swaps), plan 15 (TBD_ACONITASE→1ACO + scenes), plan 16 (final 57/21 re-pin), plan 17 (human-verify the reveals)]

# Tech tracking
tech-stack:
  added: []   # no new dependencies — pure stdlib (NW alignment) + existing PyMOL cmd
  patterns:
    - "Restoration-branch node shape: router-only entry (NO incoming choice.goto edge — the EditRouter routes known edits directly to branch_node), non-ending, not edit-allowed, claim_ids [] until the text plan lands, 05.3 §2 (iii) on_enter [edit → load WT → align → show_as] + 2 choices back to the main path"
    - "Residue-mapping precondition: human↔cast-PDB mapping MUST come from a real sequence alignment + headless cmd.iterate probe BEFORE any sele is written (the OQ5/D6 rule, now demonstrated end-to-end)"
    - "Chain-case empirics: selection matching is case-sensitive in PyMOL 2.5.0 — 'chain a' resolves to nothing on chain-A atoms"

key-files:
  created:
    - "tools/aconitase_mapping_probe.py (headless mapping probe — SMOKE_RESULT: PASS)"
  modified:
    - "data/story_glucose/glycolysis.json (gly.pfk_restored)"
    - "data/story_glucose/tca.json (tca.aconitase_restored)"
    - "tests/test_glucose_reachability.py (57/21 invariants + new restoration test)"
    - ".planning/phases/05.1-.../05.1-DESIGN.md (branch-node rows + addenda)"
    - ".planning/phases/05.1-.../05.1-GRAPH-DIAGRAM.md + 05.1-graph.svg/.txt (regenerated)"

key-decisions:
  - "Aconitase mapping DERIVED: human S112 → 1ACO chain A resi 85 (SER) — Needleman-Wunsch 96.4% identity vs the cmd.iterate-extracted 1ACO sequence, DBREF cross-check (PDB = UNP P20004 − 27; 112−27=85), catalytic Ser642 anchor"
  - "MolAction seles use UPPERCASE 'chain A' (empirically the only resolving form); edits.json signature targets may be written the same way (EditIntent.signature() lowercases both sides — round-trip safe either way)"
  - "PFK restored-node edit sele = 'resi 209 and chain A' → GLY as the RECORDED game-design framing (07-02 batch A: text-only fallback; no bacterial mapping asserted — 4PFK resi 209 is actually HIS; honesty lives in plan 08's teaching text)"
  - "Restored nodes carry claim_ids [] (structure only; plans 08/13 own the claim swaps with their text)"
  - "align_sele = 'name CA' (the 05.3 §4 default) for both nodes — no source-approved stable-core selection exists"

patterns-established:
  - "Restoration-node pinning test pattern: existence + non-ending + not-edit-allowed + on_enter op order + router-only entry + forward-walk-to-an-ending + full reachability green (test_restoration_nodes_reachable_non_ending)"

# Metrics
duration: 87 min (includes an inter-session resume; active work ~60 min)
completed: 2026-09-02
---

# Phase 7 Plan 12: Restoration Topology (gly.pfk_restored + tca.aconitase_restored) Summary

**The two DC-A restoration branch nodes added as fixed EditRouter targets (55→57, the phase's only sanctioned topology change), with the aconitase human↔bovine S112↔1ACO-resi-85 mapping derived by a real sequence alignment + headless probe BEFORE the sele was written — 57/21 invariants green, DESIGN + diagram synced.**

## Performance

- **Duration:** 87 min wall (inter-session resume included; ~60 min active)
- **Started:** 2026-09-02T18:19:21Z
- **Completed:** 2026-09-02T19:46:13Z
- **Tasks:** 2 of 2
- **Files modified:** 7 (2 story JSON, 1 test, 1 tool, 3 planning docs + 2 regenerated diagram outputs)

## Accomplishments

- **Both restored nodes exist with the 05.3 shape.** `gly.pfk_restored` (glycolysis.json) + `tca.aconitase_restored` (tca.json): non-ending, NOT edit-allowed, `claim_ids: []`, on_enter = `[edit(point_mutation) → load <enzyme>_wt → align(method=super, align_sele="name CA") → show_as cartoon]`, 2 choices (Continue + mc:observe) re-entering the main path (`gly.fbp_to_pyruvate` / `tca.shuffle`). Source nodes byte-identical (verified vs HEAD) — the runtime wiring arrives via plan 14's `branch_node`.
- **The aconitase mapping is established before the sele** (the plan's hard precondition, satisfying 07-03 D6 / OQ5): human ACO2 **S112** (UniProt Q99798 precursor, the DIS-ACO2-01-cand allele S112R) ↔ bovine **1ACO chain A resi 85** (SER — the WT residue the R112S reverse edit restores).
- **Counts updated in the SAME plan (OQ-K honored):** 57 nodes / 21 endings (1T+3G+2N+15B) / 14 edit-allowed / 1 RNG; suite 325 OK (324 + 1 new test); both AST gates clean.
- **DESIGN + diagram in sync:** §5 branch-node rows filled with the fixed ids; Plan 07-12 addendum documents the on_enter shape, the mapping, the chain-case empirics, and the plan-14 signature contract; diagram regenerated ("Summary: 57 nodes | 21 endings (1T/3G/2N/15B) | 14 edit-allowed | 1 RNG").

## THE ACONITASE MAPPING (for plan 14 to reuse)

| Item | Value |
|---|---|
| Human disease allele | ACO2 **S112R** (UniProt Q99798 precursor numbering; ICRD — `DIS-ACO2-01-cand`) |
| Bovine cast position | **1ACO chain A resi 85** — SER in the WT structure (the reverse edit restores R→S) |
| Method | Needleman-Wunsch global alignment (pure-Python, in the probe) of human Q99798 (fetched live 2026-09-03) vs the 1ACO ATOM-record sequence extracted via `cmd.iterate` from the live PyMOL object — **96.4% identity** (725/752) |
| Independent cross-check | 1ACO's own DBREF record: `PDB 2-754 = UniProt P20004 29-781` ⇒ PDB = UNP − 27; human S112 aligns to bovine UNP 112; 112 − 27 = **85** ✓ |
| Literature anchor | 1ACO resi 642 = SER (catalytic Ser642 of the pig/bovine numbering per Wikipedia mechanism + 1C97 S642A) — confirms PDB numbering matches the published bovine numbering |
| edits.json signature (plan 14) | `{"op":"point_mutation","target":"resi 85 and chain A","args":{"new_res":"SER"}}`, `branch_node: "tca.aconitase_restored"` (signature target is lowercased on both sides by `EditIntent.signature()` — case-independent match; the MolAction sele uses `chain A` verbatim) |
| PFK signature (plan 14) | `{"op":"point_mutation","target":"resi 209 and chain A","args":{"new_res":"GLY"}}`, `branch_node: "gly.pfk_restored"` — RECORDED FRAMING ONLY (4PFK resi 209 is HIS; no bacterial mapping asserted) |
| align_sele (both nodes) | `"name CA"` (the 05.3 §4 default; no source-approved stable-core selection exists) |
| Probe evidence | `tools/aconitase_mapping_probe.py` — `SMOKE_RESULT: PASS`, 17/17 checks, incl. the full restored-node op sequence dispatched through real MolOps+AssetManager+EditOps (align moved the mobile WT copy onto the fixed reference; identical structures ⇒ 0.0000 Å centroid distance) |

## Task Commits

Each task was committed atomically:

1. **Task 1: Add both restored nodes + wire main-path re-entry** — `4d3f6b8` (feat; includes the probe tool + json-ok verify + zero-drift proof vs HEAD)
2. **Task 2: Update count invariants + DESIGN + diagram** — `1ae2753` (test; 325 OK + AST gates + diagram header 57 nodes)

**Plan metadata:** committed separately (docs(07-12)).

## Files Created/Modified

- `data/story_glucose/glycolysis.json` — `gly.pfk_restored` (structure only; text = "TBD — Phase 7 text (plan 08)")
- `data/story_glucose/tca.json` — `tca.aconitase_restored` (structure only; text = "TBD — Phase 7 text (plan 13)")
- `tools/aconitase_mapping_probe.py` — the mapping probe (headless, SMOKE_RESULT: PASS)
- `tests/test_glucose_reachability.py` — 57/21 invariants; `test_manifest_loads_all_55_nodes` → `test_manifest_loads_all_57_nodes`; NEW `test_restoration_nodes_reachable_non_ending`; topology test 55→57; 14-edit-allowed test unchanged
- `05.1-DESIGN.md` — §5 branch-node rows + Plan 07-12 addendum + §1 inventory addendum
- `05.1-GRAPH-DIAGRAM.md` + `05.1-graph.svg` + `05.1-graph.txt` — regenerated (57 nodes; restored nodes shown in the structural/unreached section — router-only entry)

## Decisions Made

- **Chain case (empirical, load-bearing):** PyMOL selection matching is case-sensitive — `resi 85 and chain a` resolves to NOTHING on chain-"A" atoms; `chain A` resolves. All MolAction seles use uppercase. Plan 14's edits.json signature targets are written in the same `chain A` form for clarity (the signature round-trip is case-independent either way — `EditIntent.signature()` lowercases both sides).
- **Restored-node claim_ids = []** (structure only): the text plans (08/13) own the claim swaps together with the restored-node text; empty lists add zero citation-gate references.
- **`show_as cartoon` reveal op included** (within the 05.3 op vocabulary + the plan's "...reveal ops" shape); scene enrichment stays with the scene plan (15).
- **tca.aconitase_restored re-enters at tca.shuffle** (per the plan), meaning the restored player rides the RNG wheel again — consistent with the cycle's loop-back structure.
- **PFK edit sele `resi 209 and chain A` → GLY** used as instructed by the plan (the recorded game-design framing); the probe + local 4PFK parse document that 4PFK resi 209 is HIS (the framing asserts nothing bacterial — plan 08's teaching text owns the honesty).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `cmd.iterate` cannot read x/y/z (probe bug)**
- **Found during:** Task 1 (aconitase mapping probe, first headless run)
- **Issue:** the probe's centroid helper used `x/y/z` expressions inside `cmd.iterate`; PyMOL raises `NameError: x/y/z only available in iterate_state and alter_state`
- **Fix:** switched the centroid reads to `cmd.iterate_state(0, ...)` (cite: editing.py:1479)
- **Files modified:** tools/aconitase_mapping_probe.py
- **Verification:** probe re-run — `SMOKE_RESULT: PASS`
- **Committed in:** 4d3f6b8

**2. [Rule 1 - Bug] MolOps needs explicit EditOps/AssetManager injection (probe bug)**
- **Found during:** Task 1 (probe, second headless run)
- **Issue:** `MolOps(cmd)` dispatches `op="edit"` with `RuntimeError: molops.edit requires an EditOps (editops=None)`; the `load pdb:` op likewise needs an AssetManager
- **Fix:** `MolOps(cmd, asset_manager=AssetManager(cmd), editops=eo)` — the same wiring the controller uses (main_window.py:205), making the probe's op-sequence test controller-faithful
- **Files modified:** tools/aconitase_mapping_probe.py
- **Verification:** probe re-run — full on_enter sequence (edit → load 1ACO → align super → show_as) dispatched cleanly
- **Committed in:** 4d3f6b8

**3. [Rule 3 - Blocking] Mermaid doc edit slip (self-inflicted, fixed immediately)**
- **Found during:** Task 2 (GRAPH-DIAGRAM.md edit)
- **Issue:** an edit anchor accidentally deleted the `GF -->|"Observe (mc:observe)"| GPK` edge line instead of inserting the restoration edges
- **Fix:** restored the edge + inserted the restoration edges with explanatory comments in two clean edits
- **Files modified:** 05.1-GRAPH-DIAGRAM.md
- **Verification:** re-read of the edited region + suite green
- **Committed in:** 1ae2753

---

**Total deviations:** 3 auto-fixed (2 probe bugs, 1 doc-edit slip)
**Impact on plan:** None on the shipped topology — all three were within-task fixes; the probe now runs clean end-to-end.

## Issues Encountered

- **Runtime-reachability semantics of the restored nodes (documented, not a defect):** the restored nodes have NO incoming `choice.goto` edge — `engine.apply_player_edit` routes a KNOWN edit directly to `branch_node`, bypassing choices. The BFS therefore neither reaches nor needs them (they are non-endings; full-graph reachability stays GREEN). This is the same structural-vs-runtime distinction as the `edit.prompt` stub, and is why the new test pins the nodes directly (existence, non-ending, not-edit-allowed, on_enter op order, router-only entry, forward-walk-to-an-ending) instead of via the BFS. In the regenerated diagram they appear in the "Unreached nodes (19) — structural" section, as expected.
- **Inter-session resume:** the executor was interrupted once between the probe authoring and its first run; on resume, `git log`/`git status` confirmed no duplicate work existed and execution continued from the probe write. No work was redone.

## User Setup Required

None — no external service configuration required. (The probe uses the already-cached `rpg/data/assets/downloaded/1aco.pdb`; 1ACO and 4PFK are both in the local dev cache, so the restored nodes' `pdb:` loads are offline-replayable in dev. Fresh installs get them via the bulk-download prompt once cast.json lists them — plans 02/14's territory.)

## Next Phase Readiness

- **Plan 14 (edits.json) is unblocked** with exact, verified values: `branch_node` = `gly.pfk_restored` / `tca.aconitase_restored`; signature targets `resi 209 and chain A` → `new_res GLY` and `resi 85 and chain A` → `new_res SER` (recorded in §5 addendum + the mapping table above).
- **Plans 08/13 own the restored-node text + claim swaps** (both DIS claims are APPROVED in the registry — DIS-PFKM-01-cand, DIS-ACO2-01-cand); the TBD markers are the only placeholders left in the two new nodes.
- **Plan 15** still owns `TBD_ACONITASE` → `pdb:1ACO` on the SOURCE node (tca.aconitase) — until then the aconitase cast load fails offline-safe at runtime (the Phase 6 defensive swallow), while the restored node's own `pdb:1ACO` load is already real.
- **Watch items:** plan 16 re-pins 57/21 (now the live counts); plan 17 human-verifies the reveals in a real PyMOL session (Qt/scene behavior is human-verify per AGENTS.md). The probe's chain-case finding applies to ALL future edits.json authoring (plan 14): seles against 4PFK/1ACO/1CSC chain-"A" casts must use uppercase `chain A`.

---
*Phase: 07-content-expansion-i-glucose*
*Completed: 2026-09-02*
