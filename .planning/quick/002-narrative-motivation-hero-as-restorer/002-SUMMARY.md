# Quick Task 002: Summary — Narrative Motivation Decided

**Date:** 2026-08-19
**Commit:** (this commit)
**Directory:** `.planning/quick/002-narrative-motivation-hero-as-restorer/`

## What was decided

The hero is a "gifted/blessed" carbon — beyond an ordinary carbon atom, the hero
has the special power to edit/restore enzymes. The host organism is sick (enzymes
malfunctioning/mutated). The hero's journey through the respiratory pathway is
motivated not only by personal destiny (the ending tiers) but by the mission to
save the host by restoring the broken enzymes encountered at edit-allowed nodes.

## What changed

This is a **content-layer narrative decision** — NO skeleton structure change,
NO code change, NO replan. The Phase 5.1 skeleton topology, RNG shuffle, endings,
reachability, and edit-node contract (SC4) mechanism are all unchanged. The
EditRouter (Phase 4) already supports this frame:

| Player action | EditRouter outcome | Narrative frame |
|---------------|-------------------|-----------------|
| Correct reverse-mutation (matches `edits.json` signature) | known → branch node | "You restored the enzyme!" |
| Wrong mutation (no match) | unknown → bad-ending pool | "You made it worse." |
| Break a critical residue | → `bad.critical_residue_break` | "You destroyed the active site." |

The new element is the **on_enter pre-edit**: the enzyme is shown in its diseased
state when the player arrives (load wild-type PDB → applyEdit disease mutation).
The player sees the broken enzyme and attempts to fix it.

## Files updated

1. **spec.md** — Description NOTE (2026-08-19): hero motivation narrative annotated
   in-place under the Description heading.
2. **.planning/PROJECT.md** — Core Value paragraph updated to include the restoration
   frame; Key Decision row 109 added recording the decision + implementation path;
   footer updated.
3. **.planning/phases/05.1-story-graph-design-glucose-skeleton-integration-contracts/05.1-DESIGN.md**
   — SC4 (edit-node contract) section: restoration narrative frame note added at the
   top of §5, documenting the two uses (diseased-state display via on_enter pre-edit
   + restoration attempt via EditRouter) + the geometry caveat + the scope note
   (not all edit-allowed nodes need a restoration subplot).
4. **.planning/STATE.md** — Quick Tasks Completed table: row 002 added.

## Why no replan

- The Phase 5.1 skeleton is **structure** (node topology, edges, contracts,
  reachability). The narrative motivation lives in **content** (spec.md plot,
  `text_dramatic`/`text_teaching`, `edits.json` signatures, `on_enter` pre-edit
  MolActions). The skeleton is already 100% compatible.
- The edit-node contract (SC4) already routes: known edit → branch node, unknown
  edit → bad ending. With the restoration frame, "known" = the correct
  reverse-mutation (restoration), "unknown" = a wrong fix. Same mechanism, different
  interpretation.
- The `on_enter` MolActions can already chain `load pdb:X` → `edit(point_mutation)`
  to show the diseased state (Phase 7 implements this per-enzyme; the `apply_edit`
  helper from Phase 4 supports it).
- The node topology, RNG shuffle, endings, reachability — all unchanged.

## Downstream impact

- **Phase 7** (content authoring): authors the actual restoration text + `edits.json`
  reverse-mutation signatures + `on_enter` pre-edit sequences. Each disease mutation
  needs a real source (what mutation? what disease?) — additional per-claim approval.
- **Scope discipline:** not ALL ~6 edit-allowed nodes need a restoration subplot.
  1-2 key enzymes (e.g. PFK, aconitase — both already have approved claims) can
  carry the arc while the rest stay "exploration" editing.
- **Geometry caveat:** `cmd.alter` changes residue identity but does not repack
  side chains. The "mutated" structure has correct sequence but approximate 3D
  coordinates. `text_teaching` should note this is a simplified representation.
