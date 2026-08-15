---
phase: 05-pre-content-key-decisions-source-approval
plan: 01
subsystem: decisions
tags: [soul-jump, c14-decay, ending-distribution, metaphor]

# Dependency graph
requires:
  - phase: 01 (Citation Gate)
    provides: no-fabricated-science gate + data/citations.json registry shape
  - phase: 02 (Story Engine Core)
    provides: StoryGraph/Node/Choice model + reachability checker (validate_graph/check_reachability) that Phase 5.1 graph topology must satisfy
provides:
  - SC#1 soul-jump METAPHOR decided (option b sense-moves-with-electron, reframed as metamorphosis — caterpillar→butterfly)
  - SC#2 C14-decay framing RESOLVED via DROP (radioactive decay removed as bad-ending trigger; cycle-trap-until-host-death is the sole timescale bad-ending)
  - Ending-count distribution documented (1 True + several Normal/Good + many Bad per character)
  - NUBASE2020 half-life citation + C14-TIME-01 claim ELIMINATED from downstream plans
affects: [Phase 5.1, Phase 5.2, Phase 6, Phase 7, Plan 05-02, Plan 05-04, Plan 05-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "In-place HTML comment annotations on spec.md deviation lines (Pitfall 4 NOTE on line 15; Pitfall 9 NOTE on line 18) — keeps spec.md as the living source while recording resolved deviations inline + linking to PROJECT.md Key Decisions"

key-files:
  created: []
  modified:
    - .planning/PROJECT.md (Key Decisions row 104 metaphor appended; row 105 RESOLVED via DROP; new ending-distribution row; footer date 2026-08-15)
    - spec.md (line 18 in-place Pitfall 9 NOTE annotation)

key-decisions:
  - "SC#1 metaphor = option (b) sense-moves-with-electron, REFRAMED as metamorphosis (caterpillar→butterfly): the hero is the carbon and transforms (carbon body shed as CO2 = chrysalis stage), not dies; narrative POV/sense follows the electrons onward ('my electrons power the cell'). The 'soul' is narrative attention, not a physical identity."
  - "SC#2 C14-decay DROP confirmed (drop=yes): radioactive decay removed as a bad-ending trigger; cycle-trap-until-host-death (spec.md line 18) is the sole timescale-based bad-ending. No NUBASE2020 half-life citation needed. No C14-TIME-01 claim needed."
  - "Ending distribution = 1 True + several Normal/Good + many Bad per character (asymmetric, user-confirmed 2026-08-15). Replaces the flat 'all 4 reachable' framing. Affects Phase 5.1 graph topology."

patterns-established:
  - "Spec-deviation annotation convention: when a settled Key Decision deviates from a spec.md line, add an in-place HTML comment `<!-- Pitfall N NOTE (date): ... See .planning/PROJECT.md Key Decisions row M. -->` on that line (mirrors the Pitfall 4 line-15 precedent)."

# Metrics
duration: 2min
completed: 2026-08-15
---

# Phase 5 Plan 01: SC#1 Metaphor + SC#2 Decay-DROP + Ending Distribution Summary

**SC#1 soul-jump metaphor decided as metamorphosis (sense-moves-with-electron, caterpillar→butterfly); SC#2 C14-decay DROPPED as a bad-ending trigger; ending distribution confirmed as 1 True + several Normal/Good + many Bad**

## Performance

- **Duration:** ~2 min (continuation segment — Task 3 only; Task 1 was a prior-agent read-only verification, Task 2 was the human checkpoint:decision)
- **Started:** 2026-08-15T13:02:04Z (continuation segment)
- **Completed:** 2026-08-15T13:04:28Z
- **Tasks:** 3 (1 auto-verify [prior agent] + 1 checkpoint:decision [human] + 1 auto-document [this agent])
- **Files modified:** 2 (.planning/PROJECT.md, spec.md)

## Accomplishments
- SC#1 carbon-fate SCIENCE confirmed documented and settled across all 3 artifacts (PROJECT.md row 104, PITFALLS.md Pitfall 4, spec.md line 15) — NOT reopened (AGENTS.md constraint honored)
- SC#1 soul-jump METAPHOR decided by the human and documented: option (b) sense-moves-with-electron, REFRAMED as metamorphosis (the hero transforms like a caterpillar→butterfly; carbon body shed as CO2 = chrysalis stage; narrative POV follows the electrons — "my electrons power the cell"; the hero transforms, not dies)
- SC#2 C14-decay framing RESOLVED via DROP — radioactive decay removed as a bad-ending trigger; cycle-trap-until-host-death (spec.md line 18) is the sole timescale-based bad-ending; no half-life citation (NUBASE2020) or C14-TIME-01 claim needed
- Ending-count distribution documented as a new PROJECT.md Key Decisions row: 1 True + several Normal/Good + many Bad per character (asymmetric, user-confirmed)
- NUBASE2020-C14 source and C14-TIME-01 claim ELIMINATED from downstream plans (Plan 04/05)

## Task Commits

Each task was committed atomically:

1. **Task 1: Verify SC#1 carbon-fate SCIENCE is documented** - `d6a9a3b` (docs — read-only verification; 0 files modified) — prior agent
2. **Task 2: SC#1 soul-jump METAPHOR decision + SC#2 C14-decay DROP confirm** - `—` (checkpoint:decision — human chose metaphor=b-sense-moves REFRAMED as metamorphosis; drop=yes)
3. **Task 3: Document SC#1 metaphor + SC#2 DROP + ending distribution** - `5db075c` (docs)

**Plan metadata:** `pending` (docs: complete plan — committed after SUMMARY/STATE)

## Files Created/Modified
- `.planning/PROJECT.md` — Key Decisions row 104 (ATP/True-Ending carbon-fate reframing): appended the metamorphosis metaphor specification (option b sense-moves-with-electron, reframed as caterpillar→butterfly; carbon shed as CO2 = chrysalis stage; narrative POV follows electrons; hero transforms not dies; status → "Resolved (soul-jump; metaphor = metamorphosis)"). Row 105 (C14-decay timescale framing): changed "— Pending" to "RESOLVED via DROP" with full rationale. NEW row added: "Ending distribution: 1 True, several Normal/Good, many Bad". Footer last-updated → 2026-08-15.
- `spec.md` — line 18 (bad-ending bullet): added in-place `<!-- Pitfall 9 NOTE (2026-08-15) -->` HTML comment annotation recording the decay DROP + linking to PROJECT.md Key Decisions row 105.

## Decisions Made

- **SC#1 metaphor (human, via checkpoint:decision):** Option (b) sense-moves-with-electron, with the human's IMPORTANT REFRAMING. The human's exact words: "the dies as co2 isnt that good, frame like how a Caterpillar turns into butterfly? together wit the sense/pov move". Interpreted and documented as: the hero does NOT "die as CO2" (emotionally not good). Instead, the True ending is a METAMORPHOSIS — like a caterpillar turning into a butterfly. The carbon body is shed as CO2 (the chrysalis/cocoon stage), and the narrative POV/sense follows the electrons onward (legacy/influence framing — "my electrons power the cell"). The hero transforms, not dies. The "soul" is the narrative attention that moves with the electrons, not a physical identity. The carbon-fate SCIENCE (electrons → ETC → ATP; carbon → CO2) is UNCHANGED — only the narrative metaphor was added.
- **SC#2 C14-decay DROP (human, via checkpoint:decision):** drop=yes confirmed. Radioactive decay is DROPPED as a bad-ending trigger. The cycle-trap-until-host-death trigger (spec.md line 18: "RNG stay in a cycle long enough for the host organism passed") is the sole timescale-based bad-ending. No half-life citation (NUBASE2020) needed. No C14-TIME-01 claim needed. This is a spec deviation (spec.md line 18 lists "radioactive decay") — documented in-place via the Pitfall 9 NOTE annotation and in PROJECT.md row 105. Chosen because it is scientifically cleaner (no decay-timescale problem).
- **Ending-count distribution (human, pre-confirmed):** 1 True + several Normal/Good + many Bad per character (asymmetric). The True ending = soul-jump/legacy fulfilled via metamorphosis. Several Normal+Good = different carbon fates (fatty acid storage, amino acid, CO2-without-full-harvest, carbon-retained-pre-oxidation). Many Bad = the largest pool (cycle-trap → host death, critical-residue-break, lost-connection, released-from-host, etc.). This replaces the flat "all 4 reachable" framing with "1 True + several Normal/Good + many Bad reachable per character" and affects Phase 5.1 graph topology.

## Deviations from Plan

None — plan executed exactly as written, with the human's checkpoint:decision choices applied. The metamorphosis reframe is the human's chosen interpretation of option (b) (sense-moves-with-electron); it was applied verbatim to the row 104 outcome as the human specified. No auto-fixes were needed (all edits were documentation-only and applied cleanly on the first try).

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. (This plan records framing decisions only; no source was auto-approved — source/claim approval is deferred to Plan 05.)

## Next Phase Readiness

**Ready for downstream Phase 5 plans.** The framing decisions are documented and unblock:

- **Phase 5.1 (Story Graph Design):** reachability checker must confirm ≥1 Bad-ending trigger remains reachable per character WITHOUT decay (the bad-ending triggers are now: cycle-trap → host death, critical-residue-break, lost-connection, released-from-host — decay removed). Graph topology = 1 True node + several Normal/Good nodes + many Bad nodes per character (per the ending-distribution decision). The True-ending node text should use the metamorphosis framing (caterpillar→butterfly / chrysalis → "my electrons power the cell"), NOT "the hero dies as CO2".
- **Phase 5.2 (Representation Design):** no direct dependency on this plan, but the metamorphosis framing may inform the True-ending visual cue.
- **Plan 05-02 (invariant re-wording):** the ending-count distribution (1 True + several Normal/Good + many Bad) must be incorporated into the reachability/story-graph invariant re-wording — the flat "all 4 reachable" invariant no longer holds.
- **Plan 05-04 (registry population):** NUBASE2020-C14 source + C14-TIME-01 claim are ELIMINATED — do NOT populate them in `data/citations.json`. The cycle-trap-until-host-death trigger needs no half-life citation.
- **Plan 05-05 (review list):** remove NUBASE2020-C14 + C14-TIME-01 from the source/claim review list.
- **Phase 7+ content:** the True-ending dramatic text should be authored with the metamorphosis framing; the actual ETC/ATP-synthase chemistry claims still require per-claim citation approval (separate, later gate — NOT part of this plan).

**Blockers/concerns:** None from this plan. The remaining Phase 5 decisions (anaerobic framing; batch-vs-per-claim approval) are still Pending and are handled by later plans in this phase. Pitfall 4 (soul-jump science) and Pitfall 9 (C14-decay) are both now RESOLVED.

---
*Phase: 05-pre-content-key-decisions-source-approval*
*Completed: 2026-08-15*
