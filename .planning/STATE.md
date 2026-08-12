# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-12)

**Core value:** The player experiences cellular respiration as a story with consequences — every choice and edit on the C14 hero either advances them toward a destiny (ATP, storage, CO2, or catastrophe) or diverts them into a branch, with real PDB proteins as the cast and scientifically validated chemistry as the plot.
**Current focus:** Phase 1 — Foundations & Testability Boundary + Citation Gate

## Current Position

Phase: 1 of 13 (Foundations & Testability Boundary + Citation Gate)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-08-12 — Roadmap revised (split documentation finalization + verification OUT of Phase 10 into Phase 11; Phase 10 keeps polish/playtest/accessibility/test-matrix/citation-gate; Phase 11 owns docs update + final docs verification as last release gate; 13 phases total, 32 v1 requirements mapped, coverage unchanged)

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: —
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 12-phase comprehensive build order (10 integer milestones + 2 INSERTED decimal design phases at 5.1/5.2); Phase 5 (Key Decisions + source approval) runs parallel with Phases 2–4 and gates all content (Phases 6–9).
- [Roadmap]: Architecture = 3-tier testability layering (pure-Python domain → pymol.cmd headless layer → pymol.Qt human-verify layer); ink-inspired story graph as JSON we own; edit routing via lookup table + bad-ending fallback; citation registry as architectural no-fabricated-science gate.
- [Roadmap]: Two INSERTED design phases (5.1 Story Graph Design, 5.2 Cast & Hero Representation Design) sit between Phase 5 decisions and Phase 6 MVP — they make the story graph topology + MC-choice/edit-node integration contracts and the 3D visual language explicit, reviewable artifacts before any Qt UI or cited content is built. Both own 0 requirements (design phases, per Phase 10 precedent); they enable downstream delivery.
- [Roadmap]: Content is a marathon across Phases 7–9 (glucose → fatty acid + alcohol → anaerobic + full cast), dominated by per-claim approval throughput (Pitfall 7), not engineering difficulty.
- [Roadmap]: Content phases 7/8/9 are NOT split into more phases despite the heavy per-claim citation load. Instead each uses granular per-pathway-segment plans (5–7 for P7, 4–6 for P8, 4–5 for P9). Rationale: (a) per-claim approval is orthogonal to phase structure — the human approves claims individually regardless; (b) already at top of comprehensive depth (12 phases), splitting would exceed range; (c) content segments are sequential (continuity), so phases buy no parallelism; (d) phase-level verifier marginal value is low for content (citation gate already enforced at build time); (e) plans give the per-segment review cadence the user wants with less ceremony. See ROADMAP.md "Content Phase Plan Granularity".
- [Roadmap]: Phase 11 (Documentation Finalization & Verification) split OUT of Phase 10 per user feedback. Phase 10 keeps polish, playtest-driven edit-table expansion, accessibility, full manual GUI test matrix, pre-ship citation gate. Phase 11 owns: update README + in-game help to match final shipped content (cast list, slogan, PDB IDs + resolutions), verify all docs reflect shipped game, final docs verification as the last release gate. Phase 11 owns 0 new requirements (verifies/updates DOC-01, DOC-02 created in Phase 9, per the Phase 10 0-requirement precedent). Phase 11 depends on Phase 10 (content polish settled before docs finalization) — it is the LAST release gate before ship.

### Pending Todos

None yet.

### Blockers/Concerns

Issues that affect future work:

- [Phase 5]: 4 science-framing Key Decisions (ATP/True-Ending carbon-fate reframing — Pitfall 4; C14-decay timescale — Pitfall 9; anaerobic framing; batch-vs-per-claim approval) gate content authoring. The roadmapper has NOT resolved these (they are HOW decisions for the human). They are flagged as Phase 5 tasks. Start this track early — it is the timeline-domininating risk (Pitfall 7). The ATP/True-Ending + anaerobic decisions specifically gate Phase 5.1 (Story Graph Design).
- [Phase 5.1 / 5.2 (INSERTED)]: Two design phases gate Phase 6. Phase 5.1 (Story Graph Design) needs Phase 2 + the Phase 5 ATP decision; it produces the glucose skeleton + MC-choice/edit-node integration contracts (resolves the user's story-design / MC-vs-editing / editing↔story concerns). Phase 5.2 (Representation Design) needs Phase 3 + 5.1; it produces the hero-highlight + scene-template convention (resolves the user's cast/hero-representation concern). Both are review-checkpoints, not requirement-delivery phases.
- [Phase 4]: Highest technical-risk phase — the `alter`→`sort` silent-corruption trap (Pitfall 6) and `cmd.create` no-op trap (Pitfall 3) bite here. Address on day one of Phase 4 with the `apply_edit` helper + backup-snapshot pattern.
- [Phase 6]: First human-verify milestone — Qt/GUI cannot be exercised from WSL (Pitfall 2). Manual GUI test matrix begins here. Now implements the reviewed Phase 5.1 + 5.2 design artifacts rather than inventing them inline.
- [Phase 11]: Documentation finalization + verification is the LAST release gate, after Phase 10's content polish. It depends on Phase 10 being complete (playtest-driven content changes settled) so docs reflect final shipped content. It owns 0 new requirements — verifies/updates DOC-01, DOC-02 against shipped reality.
- [Coverage]: REQUIREMENTS.md previously stated "34 total" v1 requirements; actual enumerated v1 set is 32 (PATH-01, STAT-01 are v2). Traceability uses 32. The 5.1/5.2/11 phases own 0 requirements — coverage unchanged at 32/32.

## Session Continuity

Last session: 2026-08-12 (roadmap creation)
Stopped at: Roadmap created; ready to plan Phase 1
Resume file: None
