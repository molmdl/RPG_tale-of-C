---
phase: 05-pre-content-key-decisions-source-approval
plan: 02
subsystem: decisions
tags: [anaerobic, invariant, framing, etc-o2, fermentation, lactic, mammal]

# Dependency graph
requires:
  - phase: 02 (Story Engine Core)
    provides: StoryGraph/Node/Choice model + reachability checker (validate_graph/check_reachability) that Phase 5.1 graph topology must satisfy
  - phase: 05 Plan 05-01
    provides: SC#1 soul-jump metaphor (metamorphosis) + SC#2 C14-decay DROP + ending-count distribution (1 True + several Normal/Good + many Bad) — the invariant re-wording (i) incorporates the distribution
  - phase: 05 05-RESEARCH-anaerobic.md
    provides: 5 framing options (a-e) + the ETC/O2 finding (True ending biochemically unreachable anaerobically)
provides:
  - SC#3 anaerobic framing decided — option (d) CHOICE-FOR-GLUCOSE + BAD-FOR-FA/ALC (glucose gets a 3-ending anaerobic branch; FA + alcohol get the Bad-ending trigger)
  - Ending-reachability invariant re-worded to aerobic-scoped (option i): aerobically 1 True + several Normal/Good + many Bad per character; anaerobically True unreachable (no O2 → no ETC) and character-specific (glucose 3-ending branch; FA/ALC Bad-trigger only)
  - Host organism micro-decision = mammal/human (lactic fermentation: pyruvate → lactate via LDH; carbon retained → Good)
  - ETC-O2 finding acknowledged (settled chemistry — True ending biochemically unreachable anaerobically)
affects: [Phase 5.1, Phase 9, Phase 6, Phase 7, Plan 05-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "In-place HTML comment annotation on spec.md line 14 (Phase 5 NOTE) — sibling to the Plan 01 Pitfall 9 NOTE on line 18 and the Pitfall 4 NOTE on line 15; spec prose untouched"

key-files:
  created: []
  modified:
    - .planning/PROJECT.md (row 94 host note; row 95 invariant re-worded; row 97 framing resolved via d; new ETC-O2 finding row 108; footer 2026-08-15)
    - .planning/REQUIREMENTS.md (STORY-02 v1-scope parenthetical appended; STORY-05 framing = (d); footer)
    - spec.md (line 14 Phase 5 NOTE annotation appended; prose untouched)

key-decisions:
  - "SC#3 framing = option (d) CHOICE-FOR-GLUCOSE + BAD-FOR-FA/ALC: glucose gets a 3-ending anaerobic branch (lactic=Good/retained, ethanolic=Normal/CO2, crisis=Bad); FA + alcohol get the Bad-ending trigger (O2-depletion energy crisis). Best pedagogical fit — fermentation taught as a real reachable glucose fate; reuses the glucose graph (no 4th character); invariant preserved aerobically for all 3 chars."
  - "Invariant = option (i) re-word-aerobic: combines the human's (1) aerobic universal reachability [1 True + several Normal/Good + many Bad per character] AND (2) anaerobic character-specific reality [True unreachable (no O2/ETC); glucose reaches the 3-ending fermentation branch; FA + alcohol reach only the Bad-trigger]."
  - "Host organism = mammal/human (lactic fermentation: pyruvate → lactate via LDH; carbon retained → Good). LDH enters the cast in Phase 9. (Human typed 'human'; interpreted as mammal — humans are mammals; lactic fermentation in human muscle cells.)"
  - "ETC-O2 finding acknowledged: the True ending (soul-jump via ETC) is biochemically unreachable anaerobically (no O2 → no ETC → no ATP synthase); verified against LibreTexts Electron Transport Chain + Biological Oxidation pages (fetched live 2026-08-15). Settled chemistry, not a framing choice."

patterns-established:
  - "Key Decisions row resolution pattern: when a deferred row is resolved by a checkpoint:decision, update the Decision column (expand option list if research surfaced more), the Rationale column (the chosen tradeoff), and the Outcome column (the RESOLVED status + one-line description)."

# Metrics
duration: 4min
completed: 2026-08-15
---

# Phase 5 Plan 02: SC#3 Anaerobic Framing + Invariant Re-wording Summary

**SC#3 anaerobic framing resolved via option (d) CHOICE-FOR-GLUCOSE + BAD-FOR-FA/ALC; ending-reachability invariant re-worded to aerobic-scoped (i); host organism = mammal/human (lactic fermentation)**

## Performance

- **Duration:** ~4 min (continuation segment — Task 2 only; Task 1 was the prior-agent checkpoint:decision that the orchestrator resolved with the human)
- **Started:** 2026-08-15T14:03:14Z (continuation segment)
- **Completed:** 2026-08-15T14:06:51Z
- **Tasks:** 2 (1 checkpoint:decision [human, prior agent] + 1 auto-document [this agent])
- **Files modified:** 3 (.planning/PROJECT.md, .planning/REQUIREMENTS.md, spec.md)

## Accomplishments
- SC#3 anaerobic framing decided by the human and documented across PROJECT.md, REQUIREMENTS.md, and spec.md — option (d) CHOICE-FOR-GLUCOSE + BAD-FOR-FA/ALC (best pedagogical fit: glucose gets a 3-ending anaerobic branch with distinct ending semantics [lactic=Good, ethanolic=Normal, crisis=Bad]; FA + alcohol get the Bad-ending trigger [O2-depletion energy crisis])
- Ending-reachability invariant RE-WORDed to aerobic-scoped (option i) — combines the human's (1) aerobic universal reachability [1 True + several Normal/Good + many Bad per character] with (2) anaerobic character-specific reality [True unreachable without O2/ETC; glucose reaches the 3-ending fermentation branch; FA + alcohol reach only the Bad-trigger]
- Host organism micro-decision recorded = mammal/human (lactic fermentation: pyruvate → lactate via LDH; carbon retained → Good) — LDH enters the cast in Phase 9
- ETC-O2 finding acknowledged as settled chemistry (True ending biochemically unreachable anaerobically) — no fabricated anaerobic True ending
- spec.md line 14 annotated with the Phase 5 NOTE (in-place HTML comment; prose untouched; sibling to the Plan 01 Pitfall 9 NOTE on line 18 and Pitfall 4 NOTE on line 15)

## Task Commits

Each task was committed atomically:

1. **Task 1: SC#3 anaerobic framing decision + invariant re-wording + host-organism (checkpoint:decision)** - `—` (human chose framing=d-choice-glucose, invariant=i-reword-aerobic, host=mammal/human)
2. **Task 2: Document SC#3 anaerobic decision + invariant re-wording** - `9b1c20c` (docs)

**Plan metadata:** `pending` (docs: complete plan — committed after SUMMARY/STATE)

## Files Created/Modified
- `.planning/PROJECT.md` — Key Decisions row 94 (v1 ships 3 chars + anaerobic): appended host-organism note (mammal/human, lactic fermentation, LDH in Phase 9) to Outcome. Row 95 (all 4 ending tiers reachable): re-worded the invariant to aerobic-scoped (i) — Outcome now records "Aerobically, 1 True + several Normal/Good + many Bad... Anaerobically, the True ending is NOT reachable... character-specific: glucose reaches the 3-ending fermentation branch... FA + alcohol reach only the Bad-ending trigger". Row 97 (anaerobic framing): Decision expanded to list all 5 research options; Rationale updated to the chosen tradeoff (educator-fit vs scope vs story-graph-disruption); Outcome → "RESOLVED via option (d) CHOICE-FOR-GLUCOSE + BAD-FOR-FA/ALC". NEW row 108 (Anaerobic / True-ending ETC-O2 finding): acknowledged — True unreachable anaerobically (no O2 → no ETC → no ATP synthase), verified against LibreTexts ETC + Biological Oxidation pages. Footer last-updated → 2026-08-15.
- `.planning/REQUIREMENTS.md` — STORY-02: appended the v1-scope parenthetical (aerobic-scoped reachability + character-specific anaerobic reachability + ETC/O2 finding + ending distribution provenance). STORY-05: parenthetical updated from "framing pending research" to "framing = (d) choice-for-glucose + bad-for-FA/ALC (resolved Phase 5); host = mammal/human (lactic fermentation)". Footer updated.
- `spec.md` — line 14 (4-ending-tier definition): appended an in-place `<!-- Phase 5 NOTE (2026-08-15) -->` HTML comment recording the anaerobic framing (d) + invariant re-wording (i) + host (mammal/human) + ETC-O2 finding, linking to PROJECT.md Key Decisions. Prose untouched. Line 15 (Pitfall 4 NOTE) and line 18 (Pitfall 9 NOTE) preserved untouched.

## Decisions Made

- **SC#3 framing (human, via checkpoint:decision):** Option (d) CHOICE-FOR-GLUCOSE + BAD-FOR-FA/ALC. The human's exact signal: "framing=d-choice-glucose". This is a hybrid: glucose gets a 3-ending anaerobic branch (lactic=Good/retained, ethanolic=Normal/CO2, crisis=Bad); FA + alcohol get the Bad-ending trigger (O2-depletion energy crisis). Rationale (educator-fit vs scope vs story-graph-disruption tradeoff): best pedagogical fit — fermentation taught as a real reachable glucose fate with distinct ending semantics; reuses the glucose graph (adds an anaerobic branch, no 4th character); scientifically honest; invariant preserved aerobically for all 3 chars.
- **SC#3 invariant (human, via checkpoint:decision):** Option (i) RE-WORD to aerobic-scoped. The human asked a clarifying question — "would it be easier if (1) all characters has 1 true ending + several good/normal + many bad (2) accept some endings only reachable by specific character?" — and the orchestrator interpreted this as the recommended combination: option (i) IS the aerobic invariant (1), and framing (d) naturally produces the anaerobic character-specific reality (2). The human confirmed. The invariant is now: "Aerobically, 1 True + several Normal/Good + many Bad endings are reachable per character. Anaerobically, the True ending (soul-jump via ETC) is NOT reachable (no O2 → no ETC); the reachable endings are a subset (Normal/Good/Bad only) — and are character-specific: glucose reaches the 3-ending fermentation branch while FA + alcohol reach only the Bad-ending trigger."
- **SC#3 host-organism (human, via checkpoint:decision):** The human typed "human". Interpreted as **mammal** (humans are mammals; lactic fermentation in human muscle cells). Lactic fermentation: pyruvate → lactate via LDH; carbon retained → Good. LDH enters the cast in Phase 9.
- **ETC-O2 finding (acknowledged, not decided):** The True ending (soul-jump via ETC) is biochemically unreachable anaerobically (no O2 → no ETC → no ATP synthase → no soul-jump). Verified against LibreTexts Electron Transport Chain + Biological Oxidation pages (fetched live 2026-08-15). This is settled chemistry, not a framing choice — it INFORMS the invariant re-wording (i) and the framing (d) character-specific anaerobic reachability. No fabricated anaerobic True ending.

## Deviations from Plan

None — plan executed exactly as written, with the human's checkpoint:decision choices applied. The PROJECT.md row edits matched the orchestrator's exact prescribed text (rows 94/95/97 + new ETC-O2 row + footer). The spec.md line 14 annotation was appended as a sibling to the existing Plan 01 annotations (line 15 Pitfall 4 NOTE, line 18 Pitfall 9 NOTE) without overwriting either. No auto-fixes were needed (all edits were documentation-only and applied cleanly on the first try).

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. (This plan records framing decisions only; no source was auto-approved — anaerobic content sources are a later batch in Phase 9, separate per-claim gate.)

## Next Phase Readiness

**Ready for downstream Phase 5 plans + Phase 5.1.** The SC#3 framing decision is documented and unblocks:

- **Phase 5.1 (Story Graph Design):** the reachability checker must be configured with the aerobic-scoped invariant (1 True + several Normal/Good + many Bad reachable per character AEROBICALLY) AND the anaerobic sub-graph must reach exactly the endings the science permits — DO NOT fabricate an anaerobic True ending. The anaerobic sub-graph topology: glucose gets a 3-ending anaerobic branch (lactic=Good/retained, ethanolic=Normal/CO2, crisis=Bad) appended to the glucose graph; FA + alcohol get only the Bad-ending trigger (O2-depletion energy crisis — distinguish its text from the C14-decay Bad-ending: "host died from O2-depletion energy crisis" [anaerobic] vs "nucleus transmuted into N" [decay — though decay is now DROPPED, so only the O2-depletion + cycle-trap + critical-residue-break Bad-endings remain]). The True-ending node remains AEROBIC-ONLY (no O2/ETC → unreachable). Host = mammal/human.
- **Phase 9 (Anaerobic Pathway implementation):** anaerobic content + cast impact — +1 enzyme LDH (lactate dehydrogenase, mammal/human lactic fermentation: pyruvate → lactate); pyruvate decarboxylase is NOT needed since host = mammal (not yeast — ethanolic fermentation's pyruvate decarboxylase step is yeast-specific); ADH (alcohol dehydrogenase) is reused for the alcohol character's aerobic path only (not the anaerobic ethanolic branch, since the host is mammal). The ethanolic=Normal anaerobic ending for glucose is taught as a comparative cross-reference (yeast fermentation) rather than a host-cast enzyme. The 5 verified LibreTexts pages (Fermentation, Glycolysis, Biological Oxidation, Beta-Oxidation, Electron Transport Chain) are CANDIDATE sources for a LATER batch (Phase 9 anaerobic content per-claim approval) — NOT approved by this plan.
- **Plan 05-03:** the remaining 2 Pending Phase 5 decisions (batch-vs-per-claim approval; any other framing) — anaerobic is now RESOLVED, so the pending count drops from 2 → 1 (batch-vs-per-claim approval only).
- **Phase 7 (All Glucose Endings):** the glucose graph must include the aerobic endings (1 True + several Normal/Good + many Bad) AND the anaerobic 3-ending branch (lactic=Good, ethanolic=Normal, crisis=Bad) as a reachable sub-graph from the pyruvate branch point under O2-depletion conditions.

**Blockers/concerns:** None from this plan. The anaerobic framing + invariant re-wording + host-organism + ETC-O2 finding are all RESOLVED/acknowledged. The remaining Phase 5 decision is batch-vs-per-claim approval (Plan 05-03). Pitfall 4 (soul-jump) was NOT reopened (AGENTS.md constraint honored — this plan took it as settled context). No source was auto-approved (anaerobic content sources land in Phase 9 per-claim gate).

---
*Phase: 05-pre-content-key-decisions-source-approval*
*Completed: 2026-08-15*
