---
phase: quick-001
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - spec.md
  - .planning/PROJECT.md
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
  - .planning/STATE.md
  - .planning/research/PITFALLS.md
  - .planning/research/SUMMARY.md
  - .planning/research/FEATURES.md
autonomous: true

must_haves:
  truths:
    - "A reader of PROJECT.md Key Decisions sees Pitfall 4 = RESOLVED via soul-jump (electrons-as-soul harvested into ATP via ETC/ATP synthase after RNG-weighted TCA path), with Pitfall 9 (C14 decay) still Pending"
    - "A reader of the ending semantics sees: True = soul (electrons) harvested into ATP; Good = carbon body retained pre-oxidation; Normal = CO2 without full harvest; Bad = failure/cycle-trap/host-death/critical-residue-break"
    - "No planning doc ASSERTS the C14 carbon itself becomes ATP or enters oxidative phosphorylation (matches only allowed in clearly-marked pitfall/resolution provenance context)"
    - "C14 is treated as a tracking label, not a fate determinant, in ending-fate claims"
    - "spec.md prose is preserved (minimal HTML-comment annotation only); the resolution is documented canonically in PROJECT.md Key Decisions"
    - "Pitfall 9 (C14 decay timescale) remains Pending — NOT resolved by this task"
  artifacts:
    - path: ".planning/PROJECT.md"
      provides: "Canonical Key Decisions record marking Pitfall 4 Resolved + rewritten ending semantics"
      contains: "Resolved (soul-jump)"
    - path: ".planning/research/PITFALLS.md"
      provides: "Pitfall 4 RESOLVED provenance note (original text retained)"
      contains: "RESOLVED (2026-08-13)"
    - path: ".planning/REQUIREMENTS.md"
      provides: "STORY-02 reframed to soul-jump"
      contains: "soul"
    - path: ".planning/ROADMAP.md"
      provides: "Phase 5 criterion + 07-04 label updated"
      contains: "soul-jump"
  key_links:
    - from: ".planning/PROJECT.md (Key Decisions table)"
      to: ".planning/STATE.md (Blocker line 74)"
      via: "Blocker must reflect Pitfall 4 RESOLVED, Pitfall 9 still Pending"
      pattern: "RESOLVED.*soul-jump"
    - from: ".planning/PROJECT.md (ending semantics)"
      to: ".planning/REQUIREMENTS.md (STORY-02)"
      via: "ending-tier descriptions must align"
      pattern: "electrons.*ATP"
    - from: ".planning/research/PITFALLS.md (Pitfall 4)"
      to: ".planning/research/SUMMARY.md (lines 16/100/120/160)"
      via: "both must show RESOLVED marker"
      pattern: "RESOLVED"
---

<objective>
Resolve Pitfall 4 (the C14/ATP carbon-fate science conflict) across all planning docs by adopting the **soul-jump reframing** (electrons-as-soul tied to the RNG TCA shuffle) and cleaning up every assertion that the C14 carbon itself becomes ATP or enters oxidative phosphorylation.

Purpose: The spec's "True ending = become ATP" conflates energy yield with carbon fate — a labeled carbon in respiration is oxidized to CO2 (via PDH + TCA decarboxylations); only its ELECTRONS continue into the ETC → ATP synthase. The human has LOCKED the resolution: the hero's **electrons** are the narrative "soul," harvested into ATP via the ETC after the RNG-weighted TCA path (True ending). This preserves the dramatic True=ATP arc with scientific accuracy. This plan propagates that decision into every planning doc and removes/annotates the wrong claims.

Output: 8 documentation files updated (no source code, no tests, no fixtures). Pitfall 4 marked RESOLVED; Pitfall 9 (C14 decay) left Pending.
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/PROJECT.md
@.planning/REQUIREMENTS.md
@.planning/ROADMAP.md
@.planning/research/PITFALLS.md
@.planning/research/SUMMARY.md
@.planning/research/FEATURES.md
@spec.md
@README.md

# Locked decision (do NOT re-derive — implement exactly this):
# - True ending = hero's electrons ("soul") fully harvested into ATP via ETC/ATP synthase
#   after completing the RNG-weighted TCA path. Carbon body released as CO2; soul lives on as ATP energy.
# - Good ending = carbon diverted to productive fate (fatty-acid storage, amino acid) BEFORE oxidation (carbon retained, no soul-jump).
# - Normal ending = carbon oxidized to CO2 and released WITHOUT full electron harvest / destiny arc.
# - Bad ending = failure to reach destination, RNG cycle-trap, host death, or player breaks critical residue/enzyme.
# - C14 = tracking label only, NOT a fate determinant.
# - Pitfall 9 (C14 decay timescale) = still Pending; DO NOT resolve it here.
# - The soul-jump is tied to RNG (TCA shuffle gates whether electrons reach ETC → ATP).
# - Actual ETC/ATP-synthase chemistry claims still get per-claim citation approval in Phase 7+.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Declare the soul-jump resolution in canonical docs (PROJECT.md + spec.md)</name>
  <files>.planning/PROJECT.md, spec.md</files>
  <action>
  This task declares the resolution canonically. PROJECT.md is the single source of truth for Key Decisions (per STATE.md). Make these EXACT edits:

  **spec.md (line 15)** — minimal HTML-comment annotation (do NOT rewrite the human's prose):
  - OLD: `       * the true end is end up as ATP`
  - NEW: `       * the true end is end up as ATP  <!-- Pitfall 4 NOTE (2026-08-13): Resolved via the "soul-jump" reframing — the hero's ELECTRONS (not the carbon body) are harvested into ATP via the ETC after the RNG-weighted TCA path. See .planning/PROJECT.md Key Decisions. The carbon body is released as CO2. Pitfall 9 (C14 decay) remains separate/pending. -->`

  **.planning/PROJECT.md (line 18, Core Value)** — clarify ATP = electrons harvested:
  - OLD: `choice and edit on the C14 hero either advances them toward a destiny (ATP, storage,`
  - NEW: `choice and edit on the C14 hero either advances them toward a destiny (ATP [the hero's electrons harvested into energy via the ETC], storage,`

  **.planning/PROJECT.md (line 33, 4-ending-tiers active requirement)** — reframe True tier:
  - OLD: `- [ ] All 4 ending tiers reachable for each character: True (ATP), Good (fatty-acid storage / amino acid / etc.), Normal (CO2), Bad (lost connection / released from host / host death / radioactive decay / cycle-trapped)`
  - NEW: `- [ ] All 4 ending tiers reachable for each character: True (hero's electrons/"soul" harvested into ATP via ETC after the RNG-weighted TCA path — carbon body released as CO2), Good (carbon body retained pre-oxidation — fatty-acid storage / amino acid / etc.), Normal (CO2 released without the full electron-harvest destiny arc), Bad (lost connection / released from host / host death / radioactive decay / cycle-trapped)`

  **.planning/PROJECT.md (line 52, Out-of-Scope Stat/XP rationale)** — reword for soul framing:
  - OLD: `- **Stat/XP/leveling system** — deferred to v2. The scientifically-sound framing is "luck that affects host condition" rather than energy (since ATP is the True ending, energy can't double as XP). v1 focuses on the already-comprehensive content scope.`
  - NEW: `- **Stat/XP/leveling system** — deferred to v2. The scientifically-sound framing is "luck that affects host condition" rather than energy (since the True ending is the hero's electrons being harvested into ATP, energy can't double as XP). v1 focuses on the already-comprehensive content scope.`

  **.planning/PROJECT.md (lines 72-75, Ending semantics block)** — rewrite to soul-jump framing:
  - OLD:
    ```
    - True ending — hero becomes ATP (the canonical "destiny fulfilled")
    - Good ending — hero is stored (fatty acid), built into amino acid, or similar productive fates
    - Normal ending — hero is released as CO2 (the unremarkable exit)
    - Bad ending — failure to reach a destination, RNG traps hero in a cycle long enough for the host to die, radioactive decay of C14, or the player breaks an important residue/enzyme and the host cannot survive
    ```
  - NEW:
    ```
    - True ending — the hero's electrons (the narrative "soul") are fully harvested into ATP via the ETC → ATP synthase after completing the RNG-weighted TCA path (destiny fulfilled). The carbon body was released as CO2; the soul lives on as ATP energy. (Soul-jump reframing — resolves Pitfall 4; the C14 is a tracking label, not a fate determinant.)
    - Good ending — the carbon body is diverted to a productive fate (fatty-acid storage, amino acid synthesis, or similar) BEFORE oxidation, so the carbon itself is retained (no soul-jump needed)
    - Normal ending — the carbon is oxidized to CO2 and released WITHOUT the full electron-harvest / destiny arc (the unremarkable exit)
    - Bad ending — failure to reach a destination, RNG traps the hero in a cycle long enough for the host to die, radioactive decay of C14 (Pitfall 9 — framing still pending), or the player breaks an important residue/enzyme and the host cannot survive
    ```

  **.planning/PROJECT.md (line 99, Key Decisions table — Stat/XP row rationale)** — reword for soul framing:
  - OLD: `| Stat/XP/leveling deferred to v2 | ATP is the True ending so energy can't be the XP currency; "luck that affects host condition" is the candidate model but needs scientific grounding. v1 already comprehensive. | — Pending |`
  - NEW: `| Stat/XP/leveling deferred to v2 | The True ending is the hero's electrons ("soul") harvested into ATP, so energy can't double as the XP currency; "luck that affects host condition" is the candidate model but needs scientific grounding. v1 already comprehensive. | — Pending |`

  **.planning/PROJECT.md (line 104, Key Decisions table — ATP/True-Ending row)** — mark RESOLVED:
  - OLD: `| ATP/True-Ending carbon-fate reframing | Research (Pitfall 4) flagged a science conflict: a carbon atom in respiration exits as CO2, not as ATP carbon. The spec's "True ending = become ATP" needs reconciliation (e.g. hero *enables* ATP synthesis vs hero *is* ATP) before narrative authoring. Resolve at content-research phase. | — Pending |`
  - NEW: `| ATP/True-Ending carbon-fate reframing | RESOLVED 2026-08-13 via the **soul-jump reframing**: the hero's *electrons* (the narrative "soul") are harvested into ATP via the ETC → ATP synthase after the RNG-weighted TCA path, while the carbon body is released as CO2. This preserves the dramatic True=ATP arc with scientific accuracy (a labeled carbon ≠ ATP carbon; electrons → proton pumping → ATP synthesis). Tied to the RNG TCA shuffle (the soul reaches ATP only via the RNG-weighted path). Good = carbon retained pre-oxidation; Normal = CO2 without full harvest; Bad = failure/cycle-trap/host-death/critical-residue-break. C14 is a tracking label, not a fate determinant. See PITFALLS.md Pitfall 4. (The spec's original "become ATP" line is annotated in-place in spec.md; the actual ETC/ATP-synthase chemistry claims still require per-claim citation approval in Phase 7+.) | — Resolved (soul-jump) |`

  **.planning/PROJECT.md (line 105, Key Decisions table — C14-decay row)** — DO NOT change (leave Pending). Verify only that it remains `— Pending`.

  Update the "Last updated" footer line (line 109) from `*Last updated: 2026-08-12 after research synthesis*` to `*Last updated: 2026-08-13 — Pitfall 4 (ATP/True-Ending carbon-fate) resolved via soul-jump reframing; see Key Decisions*`.
  </action>
  <verify>
  Read back .planning/PROJECT.md and confirm:
  1. Key Decisions table row "ATP/True-Ending carbon-fate reframing" contains "Resolved (soul-jump)" (NOT "Pending").
  2. Key Decisions table row "C14-decay timescale framing" still contains "Pending" (unchanged).
  3. Ending semantics block (lines ~72-75) contains "soul" and "electrons" and does NOT contain the bare assertion "hero becomes ATP".
  4. spec.md line 15 still contains the original text "the true end is end up as ATP" AND now contains the HTML comment "Pitfall 4 NOTE" + "soul-jump".
  </verify>
  <done>PROJECT.md Key Decisions marks Pitfall 4 Resolved (soul-jump) and Pitfall 9 still Pending; ending-semantics block rewritten to soul-jump framing; spec.md annotated with a minimal HTML-comment note pointing to the resolution (human's prose preserved).</done>
</task>

<task type="auto">
  <name>Task 2: Propagate the reframing across downstream planning docs (REQUIREMENTS.md, ROADMAP.md, STATE.md, FEATURES.md)</name>
  <files>.planning/REQUIREMENTS.md, .planning/ROADMAP.md, .planning/STATE.md, .planning/research/FEATURES.md</files>
  <action>
  Propagate the soul-jump resolution into the downstream planning docs so they align with the canonical PROJECT.md record. Make these EXACT edits:

  **.planning/REQUIREMENTS.md (line 4, Core Value)** — clarify ATP:
  - OLD: `**Core Value:** The player experiences cellular respiration as a story with consequences — every choice and edit on the C14 hero either advances them toward a destiny (ATP, storage, CO2, or catastrophe) or diverts them into a branch, with real PDB proteins as the cast and scientifically validated chemistry as the plot.`
  - NEW: `**Core Value:** The player experiences cellular respiration as a story with consequences — every choice and edit on the C14 hero either advances them toward a destiny (ATP [the hero's electrons harvested into energy via the ETC], storage, CO2, or catastrophe) or diverts them into a branch, with real PDB proteins as the cast and scientifically validated chemistry as the plot.`

  **.planning/REQUIREMENTS.md (line 24, STORY-02)** — reframe True tier to soul-jump:
  - OLD: `- [ ] **STORY-02**: All 4 ending tiers are reachable for each character: True (ATP), Good (fatty-acid storage / amino acid / etc.), Normal (CO2), Bad (lost connection / released from host / host death / cycle-trapped / radioactive decay)`
  - NEW: `- [ ] **STORY-02**: All 4 ending tiers are reachable for each character: True (hero's electrons/"soul" harvested into ATP via the ETC after the RNG-weighted TCA path — carbon body released as CO2), Good (carbon body retained pre-oxidation — fatty-acid storage / amino acid / etc.), Normal (CO2 released without the full electron-harvest destiny arc), Bad (lost connection / released from host / host death / cycle-trapped / radioactive decay)`

  **.planning/ROADMAP.md (line 102, Phase 5 success criterion 1)** — update to reflect RESOLVED:
  - OLD: `  1. The ATP/True-Ending carbon-fate reframing is resolved (one option chosen from the Pitfall 4 options) and documented in PROJECT.md Key Decisions, with the chosen framing's carbon-fate claim entered into \`data/citations.json\` as \`approved\``
  - NEW: `  1. The ATP/True-Ending carbon-fate reframing is RESOLVED via the soul-jump reframing (the hero's electrons/"soul" are harvested into ATP via the ETC after the RNG-weighted TCA path; the carbon body is released as CO2) and documented in PROJECT.md Key Decisions. The framing decision is DONE. (The actual ETC/ATP-synthase chemistry claims still require per-claim citation approval in Phase 7+ — that is a separate, later gate; this criterion is about the framing decision, which is complete.)`

  **.planning/ROADMAP.md (line 171, 07-04 plan label)** — reframe to soul-jump:
  - OLD: `- [ ] 07-04: TBD — likely ETC / oxidative phosphorylation: True-ending carbon fate`
  - NEW: `- [ ] 07-04: TBD — likely ETC / oxidative phosphorylation: True-ending soul-jump (hero's electrons → ATP via ETC/ATP synthase)`

  **.planning/STATE.md (line 7, Core value)** — clarify ATP (same phrasing as REQUIREMENTS.md/PROJECT.md):
  - OLD: `**Core value:** The player experiences cellular respiration as a story with consequences — every choice and edit on the C14 hero either advances them toward a destiny (ATP, storage, CO2, or catastrophe) or diverts them into a branch, with real PDB proteins as the cast and scientifically validated chemistry as the plot.`
  - NEW: `**Core value:** The player experiences cellular respiration as a story with consequences — every choice and edit on the C14 hero either advances them toward a destiny (ATP [the hero's electrons harvested into energy via the ETC], storage, CO2, or catastrophe) or diverts them into a branch, with real PDB proteins as the cast and scientifically validated chemistry as the plot.`

  **.planning/STATE.md (line 74, Blocker)** — update to reflect Pitfall 4 RESOLVED, Pitfall 9 still Pending:
  - OLD: `- [Phase 5]: 4 science-framing Key Decisions (ATP/True-Ending carbon-fate reframing — Pitfall 4; C14-decay timescale — Pitfall 9; anaerobic framing; batch-vs-per-claim approval) gate content authoring. The roadmapper has NOT resolved these (they are HOW decisions for the human). They are flagged as Phase 5 tasks. Start this track early — it is the timeline-domininating risk (Pitfall 7). The ATP/True-Ending + anaerobic decisions specifically gate Phase 5.1 (Story Graph Design).`
  - NEW: `- [Phase 5]: 4 science-framing Key Decisions gate content authoring. Pitfall 4 (ATP/True-Ending carbon-fate reframing) is now RESOLVED (2026-08-13, via the soul-jump reframing — electrons-as-soul harvested into ATP via ETC after the RNG-weighted TCA path; carbon body released as CO2; see PROJECT.md Key Decisions). The remaining 3 are HOW decisions for the human, still Pending: C14-decay timescale (Pitfall 9); anaerobic framing; batch-vs-per-claim approval. They are flagged as Phase 5 tasks. Start this track early — it is the timeline-domininating risk (Pitfall 7). The anaerobic decision now specifically gates Phase 5.1 (Story Graph Design); the ATP/True-Ending decision (resolved) no longer blocks it.`

  **.planning/STATE.md (line 75, Phase 5.1 blocker)** — note ATP decision resolved:
  - OLD: `- [Phase 5.1 / 5.2 (INSERTED)]: Two design phases gate Phase 6. Phase 5.1 (Story Graph Design) needs Phase 2 + the Phase 5 ATP decision; it produces the glucose skeleton + MC-choice/edit-node integration contracts (resolves the user's story-design / MC-vs-editing / editing↔story concerns). Phase 5.2 (Representation Design) needs Phase 3 + 5.1; it produces the hero-highlight + scene-template convention (resolves the user's cast/hero-representation concern). Both are review-checkpoints, not requirement-delivery phases.`
  - NEW: `- [Phase 5.1 / 5.2 (INSERTED)]: Two design phases gate Phase 6. Phase 5.1 (Story Graph Design) needs Phase 2 + the Phase 5 ATP decision [now RESOLVED via soul-jump — electrons-as-soul → ATP via ETC after RNG-weighted TCA path; True-ending node = electron harvest, NOT carbon-becomes-ATP]; it produces the glucose skeleton + MC-choice/edit-node integration contracts (resolves the user's story-design / MC-vs-editing / editing↔story concerns). Phase 5.2 (Representation Design) needs Phase 3 + 5.1; it produces the hero-highlight + scene-template convention (resolves the user's cast/hero-representation concern). Both are review-checkpoints, not requirement-delivery phases.`

  **.planning/research/FEATURES.md (line 45, D3 row)** — reframe True=ATP to soul-jump:
  - OLD: `| D3 | **Four ending tiers (True=ATP / Good=storage or amino acid / Normal=CO2 / Bad=lost-released-host-death-decay-cycle-trap)** | "Awareness of consequentiality" (Wikipedia MEDIUM). Multiple endings per character = the branching payoff. Spec mandates all 4 reachable for every character. | L | Narrative graph (D2) | HIGH | Each ending's *chemistry* must be correct (e.g., "stored as fatty acid" must be a real fate, not invented). Story-like framing is design; the underlying fate is a claim. |`
  - NEW: `| D3 | **Four ending tiers (True = hero's electrons/"soul" harvested into ATP via ETC after RNG-weighted TCA path / Good = carbon body retained pre-oxidation (storage or amino acid) / Normal = CO2 released without full electron harvest / Bad = lost-released-host-death-decay-cycle-trap)** | "Awareness of consequentiality" (Wikipedia MEDIUM). Multiple endings per character = the branching payoff. Spec mandates all 4 reachable for every character. Pitfall 4 resolved via the soul-jump reframing (2026-08-13): the carbon body exits as CO2; the electrons ("soul") reach ATP via the ETC. | L | Narrative graph (D2) | HIGH | Each ending's *chemistry* must be correct (e.g., "stored as fatty acid" must be a real fate, not invented). Story-like framing is design; the underlying fate is a claim. |`

  **.planning/research/FEATURES.md (line 66, A3 row)** — reword for soul framing:
  - OLD: `| A3 | **Stat / XP / leveling system** | Spec defers to v2. ATP is the True ending, so energy cannot double as the XP currency (double-meaning collision). The candidate model ("luck that affects host condition") needs scientific grounding not yet available. | v1: no XP. The "progress" is which endings/characters you've *collected* (D8 achievement board). v2 may revisit if "luck-affects-host" gets a grounded source. |`
  - NEW: `| A3 | **Stat / XP / leveling system** | Spec defers to v2. The True ending is the hero's electrons harvested into ATP (soul-jump reframing), so energy cannot double as the XP currency (double-meaning collision). The candidate model ("luck that affects host condition") needs scientific grounding not yet available. | v1: no XP. The "progress" is which endings/characters you've *collected* (D8 achievement board). v2 may revisit if "luck-affects-host" gets a grounded source. |`

  **.planning/research/FEATURES.md (line 114, MVP cast path)** — clarify the path includes ETC/ATP synthase for the soul-jump:
  - OLD: `2. **T6 PDB cast (start with ~5-6 critical-path enzymes, not all 20+)** (L but *sliceable*) — pick the enzymes on the single shortest True-ending path (e.g., hexokinase → … → ATP synthase) and validate *those* first. Defer the long tail to later slices.`
  - NEW: `2. **T6 PDB cast (start with ~5-6 critical-path enzymes, not all 20+)** (L but *sliceable*) — pick the enzymes on the single shortest True-ending path (e.g., hexokinase → … → pyruvate dehydrogenase → TCA cycle → ETC → ATP synthase) and validate *those* first. The soul-jump path (hero's electrons → ETC → ATP synthase) is what defines the True ending; the carbon body is released as CO2 at PDH/TCA. Defer the long tail to later slices.`
  </action>
  <verify>
  Read back the 4 files and confirm:
  1. REQUIREMENTS.md STORY-02 (line 24) contains "soul" and "electrons" — no longer says bare "True (ATP)".
  2. ROADMAP.md line 102 contains "RESOLVED via the soul-jump reframing" (no longer says "one option chosen from the Pitfall 4 options").
  3. ROADMAP.md line 171 contains "soul-jump" (no longer says "True-ending carbon fate").
  4. STATE.md line 74 contains "RESOLVED" for Pitfall 4 AND "still Pending" for the remaining 3 (including Pitfall 9).
  5. FEATURES.md D3 row (line 45) contains "soul" — no longer says bare "True=ATP".
  6. FEATURES.md A3 row (line 66) says "electrons harvested into ATP (soul-jump reframing)" — no longer says bare "ATP is the True ending".
  7. None of these 4 files contain the assertion "hero becomes ATP" or "carbon becomes ATP".
  </verify>
  <done>REQUIREMENTS.md, ROADMAP.md, STATE.md, and FEATURES.md all reflect the soul-jump reframing; STATE.md blocker shows Pitfall 4 Resolved + Pitfall 9 Pending; ROADMAP Phase 5 criterion + 07-04 label updated; no bare "True (ATP)" / "hero becomes ATP" assertions remain in these 4 files.</done>
</task>

<task type="auto">
  <name>Task 3: Mark RESOLVED in research provenance (PITFALLS.md, SUMMARY.md) + verify README.md + grep re-scan</name>
  <files>.planning/research/PITFALLS.md, .planning/research/SUMMARY.md, README.md</files>
  <action>
  Add RESOLVED provenance markers to the research docs (preserving original text for traceability), verify README.md needs no change, and run the final grep re-scan.

  **.planning/research/PITFALLS.md (Pitfall 4, after line 98 heading)** — insert a RESOLVED note BEFORE the "What goes wrong:" paragraph (line 102), keeping ALL original pitfall text intact for provenance:
  Insert this block immediately after line 98 (`### Pitfall 4: The spec's "true ending = become ATP" conflicts with carbon-fate biochemistry`) and the blank line, BEFORE `**Severity:**`:
  ```
  > **✅ RESOLVED (2026-08-13) via the soul-jump reframing.** The human adopted: the hero's *electrons* (the narrative "soul") are harvested into ATP via the ETC → ATP synthase after the RNG-weighted TCA path, while the carbon body is released as CO2 (via pyruvate dehydrogenase + TCA decarboxylations). This preserves the dramatic True=ATP arc with scientific accuracy — a labeled carbon never enters oxidative phosphorylation or becomes ATP carbon; only its electrons continue. Tied to the RNG TCA shuffle (the soul reaches ATP only via the RNG-weighted path). Ending semantics: True = soul (electrons) harvested into ATP; Good = carbon body retained pre-oxidation (fatty-acid/amino-acid); Normal = CO2 without full electron harvest; Bad = failure/cycle-trap/host-death/critical-residue-break. C14 is treated as a tracking label only, not a fate determinant. See PROJECT.md Key Decisions. The original pitfall text below is retained for provenance. **Pitfall 9 (C14 decay timescale) remains Pending and is NOT resolved here.**
  ```
  Leave the rest of Pitfall 4 (lines 100-123) UNCHANGED.

  **.planning/research/SUMMARY.md (line 16, executive summary paragraph)** — add RESOLVED marker. The sentence currently ends: `...must be resolved by the human *before* True-Ending narrative authoring (Pitfall 4). Two related science-framing decisions...`
  - OLD: `this conflates energy yield with carbon fate and must be resolved by the human *before* True-Ending narrative authoring (Pitfall 4). Two related science-framing decisions`
  - NEW: `this conflates energy yield with carbon fate and must be resolved by the human *before* True-Ending narrative authoring (Pitfall 4). **[RESOLVED 2026-08-13 via the soul-jump reframing — the hero's electrons ("soul") are harvested into ATP via the ETC after the RNG-weighted TCA path; the carbon body is released as CO2. See PROJECT.md Key Decisions + PITFALLS.md Pitfall 4. Pitfall 9 (C14 decay) remains Pending.]** Two related science-framing decisions`

  **.planning/research/SUMMARY.md (line 100, Pitfall 4 bullet in Key Findings)** — add RESOLVED marker at the end of the bullet. The bullet currently ends: `...make the dramatic layer explicitly about *energy* not *carbon*. **Do NOT silently pick.**"`
  - OLD: `(c) keep ATP framing but make dramatic layer explicitly about *energy* not *carbon*. **Do NOT silently pick.**`
  - NEW: `(c) keep ATP framing but make dramatic layer explicitly about *energy* not *carbon*. **Do NOT silently pick.** **[RESOLVED 2026-08-13 — the human adopted the soul-jump reframing (a variant of option c): the hero's electrons ("soul") are harvested into ATP via the ETC after the RNG-weighted TCA path; the carbon body is released as CO2. See PROJECT.md Key Decisions + PITFALLS.md Pitfall 4.]**`

  **.planning/research/SUMMARY.md (line 120, Critical Pre-Content Decisions list item 1)** — mark RESOLVED:
  - OLD: `1. **ATP / True-Ending carbon-fate reframing** (Pitfall 4) — pick option (a), (b), or (c). Blocks True-Ending narrative. May expand scope (option b → PPP enzymes in cast) or change reachability.`
  - NEW: `1. **ATP / True-Ending carbon-fate reframing** (Pitfall 4) — ~~pick option (a), (b), or (c)~~ **RESOLVED 2026-08-13 via the soul-jump reframing** (electrons-as-soul harvested into ATP via ETC after the RNG-weighted TCA path; carbon body released as CO2; tied to RNG TCA shuffle). No longer blocks True-Ending narrative. See PROJECT.md Key Decisions.`

  **.planning/research/SUMMARY.md (line 160, Gaps to Address list item 1)** — mark RESOLVED:
  - OLD: `1. **ATP / True-Ending carbon-fate reframing** — science decision the human must make before Phase 4 content. Three options on the table (Pitfall 4).`
  - NEW: `1. **ATP / True-Ending carbon-fate reframing** — ~~science decision the human must make before Phase 4 content~~ **RESOLVED 2026-08-13** via the soul-jump reframing (Pitfall 4). The hero's electrons ("soul") are harvested into ATP via the ETC after the RNG-weighted TCA path; the carbon body is released as CO2. See PROJECT.md Key Decisions.`

  **README.md** — VERIFY ONLY, no edit expected. Read README.md and confirm: (a) line 13 "controls a C14 atom — the hero" is fine (C14 as tracking label, not a fate claim); (b) there is NO assertion that the C14 carbon becomes ATP or enters oxidative phosphorylation. If (and only if) you find such an assertion, add a brief clarifying note; otherwise make NO change to README.md.

  **Final grep re-scan (verification — run these commands):**
  Run these from the repo root to confirm no ASSERTIONS of the wrong claim remain (provenance/RESOLVED-context matches are expected and acceptable):
  - `grep -rn "become ATP\|becomes ATP\|end up as ATP" --include="*.md" .` — expected matches: spec.md line 15 (human's prose, annotated), PITFALLS.md Pitfall 4 (original provenance text, with RESOLVED note), SUMMARY.md (provenance, marked RESOLVED). Should NOT match PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, or FEATURES.md as bare assertions.
  - `grep -rn "enters oxidative phosphorylation" --include="*.md" .` — expected: ZERO matches (the only prior match was ROADMAP.md line 171, now reframed to "soul-jump"). Acceptable: a match inside the PITFALLS.md RESOLVED note (which says "never enters oxidative phosphorylation" — that's the CORRECT claim, not a wrong one).
  - `grep -rn "carbon.*becomes.*ATP\|C14.*ATP carbon" --include="*.md" .` — expected matches only in PITFALLS.md provenance (original text explaining why it's wrong) and the RESOLVED note (which says the carbon does NOT become ATP carbon). No bare assertion elsewhere.
  - Manual read-back: confirm PROJECT.md Key Decisions table shows Pitfall 4 = "Resolved (soul-jump)" and Pitfall 9 (C14-decay) = "Pending".
  </action>
  <verify>
  1. PITFALLS.md Pitfall 4 has a RESOLVED note block at the top (contains "✅ RESOLVED (2026-08-13)" and "soul-jump") AND the original pitfall text below is intact (still contains "The hero is a **C14 atom**").
  2. SUMMARY.md has RESOLVED markers at lines ~16, ~100, ~120, ~160 (each contains "RESOLVED 2026-08-13" and "soul-jump").
  3. README.md is UNCHANGED (no ATP-becomes claim found; C14-as-tracking-label framing intact).
  4. grep re-scan results match the expected-match profile above (no bare assertions in PROJECT/REQUIREMENTS/ROADMAP/STATE/FEATURES).
  5. PROJECT.md Key Decisions: Pitfall 4 = Resolved, Pitfall 9 = Pending (manual read-back).
  </verify>
  <done>PITFALLS.md Pitfall 4 carries a RESOLVED provenance note (original text retained); SUMMARY.md's 4 ATP-conflict references all marked RESOLVED; README.md verified clean (no change); grep re-scan confirms no wrong assertions remain outside clearly-marked provenance/RESOLVED context; Pitfall 9 confirmed still Pending.</done>
</task>

</tasks>

<verification>
After all 3 tasks complete, the resolution is verified by:
1. **No wrong assertions remain** — grep re-scan (Task 3) shows "become ATP"/"end up as ATP" only in: spec.md (human's prose, HTML-comment-annotated), PITFALLS.md (provenance, RESOLVED note at top), SUMMARY.md (provenance, marked RESOLVED). No bare assertions in PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, FEATURES.md, or README.md.
2. **No "enters oxidative phosphorylation" wrong claim** — grep returns zero matches asserting labeled C enters OXPHOS (the only acceptable match is the RESOLVED note saying it does NOT).
3. **Pitfall 4 = Resolved, Pitfall 9 = Pending** — manual read-back of PROJECT.md Key Decisions table confirms the status split.
4. **Ending semantics consistent across docs** — PROJECT.md ending-semantics block, REQUIREMENTS.md STORY-02, FEATURES.md D3, and STATE.md all describe True = electrons/soul harvested into ATP (not carbon-becomes-ATP).
5. **C14 = tracking label** — no doc treats the C14 isotope as a fate determinant in ending-fate claims.
6. **spec.md prose preserved** — the human's original "the true end is end up as ATP" line is intact, with only an HTML-comment annotation added.
</verification>

<success_criteria>
- Pitfall 4 is marked RESOLVED (2026-08-13, soul-jump reframing) in PROJECT.md Key Decisions, PITFALLS.md, and SUMMARY.md.
- Pitfall 9 (C14 decay timescale) remains Pending everywhere — NOT resolved by this task.
- The soul-jump reframing (electrons-as-soul → ATP via ETC after RNG-weighted TCA path; carbon body → CO2) is consistently reflected across PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, FEATURES.md.
- Ending semantics (True/Good/Normal/Bad) are consistent across all docs: True = soul harvested into ATP; Good = carbon retained pre-oxidation; Normal = CO2 without full harvest; Bad = failure/cycle-trap/host-death/critical-residue-break.
- No planning doc ASSERTS the C14 carbon itself becomes ATP or enters oxidative phosphorylation (provenance/RESOLVED-context references are acceptable and clearly marked).
- spec.md prose is preserved (minimal HTML-comment annotation only).
- README.md verified clean (no change needed).
- 8 documentation files updated; 0 source code / test / fixture files touched.
</success_criteria>

<output>
After completion, create `.planning/quick/001-resolve-pitfall-4-c14-atp-carbon-fate-co/001-SUMMARY.md` documenting: (a) which files were edited and the nature of each edit, (b) the grep re-scan results confirming no wrong assertions remain, (c) confirmation that Pitfall 4 = Resolved and Pitfall 9 = Pending, (d) any deviations from the planned edits (e.g., if README.md unexpectedly needed a change).
</output>
