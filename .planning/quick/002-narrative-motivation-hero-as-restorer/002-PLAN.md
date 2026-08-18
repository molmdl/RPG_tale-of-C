# Quick Task 002: Narrative Motivation — Hero as "Gifted/Blessed" Restorer of a Sick Host

## Trigger

User decision (2026-08-19) during Phase 5.1 review: the hero needs a motivation
beyond personal destiny. The hero is a "gifted/blessed" carbon with the special
power to edit/restore enzymes; the host organism is sick (enzymes malfunctioning);
the hero journeys to save the host by restoring broken enzymes encountered along
the pathway.

## Scope

Content-layer narrative decision. NO skeleton structure change (Phase 5.1 topology,
RNG, endings, reachability all unchanged). NO code change. NO replan needed.

The edit mechanic (Phase 4 EditRouter) is REFRAMED as a restoration attempt:
- on_enter pre-edit shows the diseased enzyme (load PDB → applyEdit disease mutation)
- player's edit is the restoration attempt (correct reverse-mutation → known-edit
  branch; wrong edit → bad-ending pool; critical-residue break → bad.critical_residue_break)

## Files Updated

| File | Change |
|------|--------|
| `spec.md` | Description NOTE (2026-08-19) — hero motivation narrative |
| `.planning/PROJECT.md` | Core Value updated + Key Decision row 109 added + footer updated |
| `.planning/phases/05.1-.../05.1-DESIGN.md` | SC4 section: restoration narrative frame note added |
| `.planning/STATE.md` | Quick Tasks Completed table: row 002 added |

## Implementation Note

This is a documentation-only quick task. The actual restoration content (disease
mutations, reverse-mutation signatures, on_enter pre-edit sequences, dramatic/teaching
text) is Phase 7 content authoring. The skeleton structure + EditRouter mechanism
(Phase 4) already support this narrative frame with zero changes.

## Geometry Caveat

`cmd.alter` changes residue identity but does not repack side chains or relax
geometry. The "mutated" structure has correct sequence but approximate 3D coordinates.
For a teaching tool showing real PDB structures, `text_teaching` should note this is
a simplified representation. This is a known tradeoff of the runtime pre-edit approach
(Option A from the discussion); the alternative (finding actual mutant PDB structures,
Option B) has inconsistent coverage.
