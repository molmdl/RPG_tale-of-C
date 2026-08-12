# Roadmap: RPG: Tale of C

## Overview

A 13-phase build order (11 integer milestones + 2 INSERTED decimal design phases at 5.1/5.2) that front-loads the project's hardest invariants (testability boundary + no-fabricated-science gate + path resolution), proves the whole architecture end-to-end in WSL on a toy story BEFORE any PyMOL/Qt code, then layers the PyMOL `cmd` molecular layer (headless-testable) and finally the Qt UI (human-verify). The critical path is **engineering on placeholder content racing in parallel** with a **human source-approval + science-framing decision track** (Phase 5) that gates all content authoring. **Two design phases (5.1 Story Graph Design, 5.2 Cast & Hero Representation Design) sit between the Phase 5 decisions and the Phase 6 MVP**: they make the *story graph topology + gameplay-integration contracts* and the *3D visual language* explicit, reviewable artifacts before any Qt UI or cited content is built on top — so Phase 6 implements an already-reviewed design rather than inventing one inside the already-overloaded first-Qt phase. Content is a marathon spanning Phases 7–9 (glucose first, then fatty acid + alcohol, then anaerobic + full ~20+ cast), each phase dominated by per-claim approval throughput rather than engineering difficulty — these phases stay at 3 (not split further) and instead use granular per-pathway-segment plans (see "Content Phase Plan Granularity" below) because the per-claim approval bottleneck is orthogonal to phase structure. Phase 10 is playtest-driven polish (content/engineering finalization); Phase 11 is documentation finalization + verification — the last release gate, ensuring all user-facing docs match the shipped game. Depth = comprehensive.

**Depth:** comprehensive (8–12 phases) — this roadmap has 13 (11 integer + 2 INSERTED decimal design phases; slightly above the comprehensive ceiling — the Phase 11 split is a user-requested separation of documentation verification from polish).
**Parallelization:** enabled — Phase 5 (decisions + source approval) runs in parallel with Phases 2–4 (engineering on placeholder content); the 4 Key Decisions within Phase 5 are independent of each other. Phase 5.1 (Story Graph Design) can start as soon as Phase 2 + the Phase 5 ATP/True-Ending decision are done (potentially before Phase 4 finishes); Phase 5.2 (Representation Design) follows 5.1 + Phase 3. Both 5.1 and 5.2 gate Phase 6. Use the spec.md worktree/branch protocol for parallel plan execution.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundations & Testability Boundary + Citation Gate** — pure-Python plumbing + no-fabricated-science gate + path self-check (WSL-testable, no PyMOL/Qt)
- [ ] **Phase 2: Story Engine Core (Architecture Proof in WSL)** — interpreter + engine + RNG + save/load on a minimal 2-node story with mocked MolActions
- [ ] **Phase 3: PyMOL cmd Layer + Asset Management (Headless)** — AssetManager + MolOps + api-sanity smoke against the real API surface
- [ ] **Phase 4: Editing, Protonation & Restore Safety Net** — the highest technical-risk phase: apply_edit helper, backup/restore, curated protonation, edit routing
- [ ] **Phase 5: Pre-Content Key Decisions & Source Approval** — PARALLEL track: 4 science-framing decisions + batch-by-source approval workflow (gates Phases 6–9 content)
- [ ] **Phase 5.1: Story Graph Design — Glucose Skeleton + Integration Contracts (INSERTED)** — designs the real glucose story graph topology + the MC-choice-point and edit-node integration contracts as reviewable artifacts; validated by the reachability checker
- [ ] **Phase 5.2: Cast & Hero Representation Design — Visual Language + Scene Templates (INSERTED)** — designs the C14 hero highlight convention + per-stage scene templates + cast-reveal convention; headless-prototyped on placeholder structures
- [ ] **Phase 6: Qt UI + Minimal Playable MVP (Glucose + True+Bad)** — FIRST human-verify milestone; UI as thin adapter over proven engine + molecular layer + reviewed design artifacts
- [ ] **Phase 7: Content Expansion I — All Glucose Endings + Full Glucose Path** — 4 endings + TCA RNG weights + real branch points + two-layer text for glucose
- [ ] **Phase 8: Content Expansion II — Fatty Acid + Alcohol Characters** — completes the 3-character roster; all 4 endings reachable per character (v1 success measure)
- [ ] **Phase 9: Anaerobic Pathway + Full Cast + Documentation Completion** — anaerobic framing implemented, ~20+ cast populated + cited, dramatic cast list + slogan in README and in-game
- [ ] **Phase 10: Polish, Playtest & Release Readiness** — playtest-driven table expansion, accessibility, full manual test matrix, pre-ship citation gate green
- [ ] **Phase 11: Documentation Finalization & Verification** — update README + in-game help to match shipped content; final docs verification as the last release gate

## Phase Details

### Phase 1: Foundations & Testability Boundary + Citation Gate
**Goal**: The project's hardest invariants — the pure-Python/UI testability split, the no-fabricated-science citation gate, and WSL/Windows path resolution — are architecturally enforced and unit-tested before any feature code, so no later phase can ship unapproved science or break WSL testability.
**Depends on**: Nothing (first phase)
**Requirements**: PLGN-03, CITE-02, DOC-04
**Success Criteria** (what must be TRUE):
  1. All pure-Python domain-tier modules pass `python3.6 -m py_compile` and import cleanly in WSL with zero `pymol`/`PyQt5` imports (enforced by a CI grep gate that scans `c14/` excluding `pymol_layer/` and `ui/`)
  2. `tools/check_citations.py` exits non-zero when any story node references a missing or `pending` claim_id, and exits zero when all referenced claims are `approved` (demonstrated with fixture story + citation data)
  3. A path-resolution self-check helper resolves bundled data files via `__file__`-relative absolute paths, with a unit test confirming resolution succeeds from an arbitrary working directory
  4. The repo root has a minimal README.md with an "Under Development" banner, a project description, and TBD placeholder sections (Installation Instructions, References, etc.)
**Plans**: 3 plans in 2 waves

Plans:
- [ ] 01-01-PLAN.md — Package skeleton + AST testability gate + .gitignore fix (Wave 1)
- [ ] 01-02-PLAN.md — Path resolution (c14/paths.py) + README DOC-04 verification (Wave 2)
- [ ] 01-03-PLAN.md — Citation registry (c14/citations.py) + pre-ship gate (tools/check_citations.py) + fixtures + tests (Wave 2)

### Phase 2: Story Engine Core (Architecture Proof in WSL)
**Goal**: The entire game architecture is proven end-to-end in WSL — a minimal 2-node story is playable (intro → weighted choice → ending) with mocked MolActions, RNG determinism is verified, and save/load round-trips — before any PyMOL/Qt code is written. This is the architecture proof point that de-risks everything downstream.
**Depends on**: Phase 1 (domain tier + path conventions)
**Requirements**: STORY-01, STORY-04, SAVE-01, SAVE-02
**Success Criteria** (what must be TRUE):
  1. A minimal story graph (intro node → weighted choice → ending node) loads and the StoryInterpreter walks it, presenting choices and advancing to an ending — all in pure Python with a mocked MolAction sink (no PyMOL import)
  2. The RngEngine produces identical outcomes given the same seed across two runs and different outcomes given a different seed; both "fixed-seed (demo)" and "random (play)" modes are exercisable (unit-tested)
  3. A save serializes GameState (current node, character, flags, RNG seed + state, visit counts, edit history) to a human-readable JSON file, and load restores an identical session by replaying the current node's on_enter MolActions
  4. A reachability checker (pure Python) runs on the toy graph and reports which endings are reachable — green on a well-formed graph, red on one with an orphaned ending — establishing the "all endings reachable" invariant as a verifiable check
**Plans**: TBD (likely 3–4 plans)

Plans:
- [ ] 02-01: TBD

### Phase 3: PyMOL cmd Layer + Asset Management (Headless)
**Goal**: The molecular layer is proven against the real PyMOL 2.5.0 API headlessly — structures load/fetch correctly, MolActions translate to the right `cmd.*` calls, and the known API pitfalls (the `cmd.create(obj,sele,1,1)` no-op, `cmd.fetch` async/CIF defaults) are surfaced and mitigated before any editing or UI code depends on them.
**Depends on**: Phase 1 (path conventions); Phase 2 (MolAction model)
**Requirements**: CAST-02
**Success Criteria** (what must be TRUE):
  1. An api-sanity headless smoke (via `run-conda-pymol.bat -cq`) exercises each `cmd.*` call the game will use (load, fetch, show, hide, select, zoom, color, delete, create-for-backup) with post-condition assertions (e.g. `count_atoms > 0` after load) and passes with exit code 0
  2. AssetManager resolves a bundled PDB and a fetched PubChem substrate (`cmd.fetch` with `type='cid'`, `async_=0`, explicit `path=<plugin data dir>`) to local files, loading each into a non-empty PyMOL object (verified by `count_atoms`) — downloads land in the plugin data dir regardless of cwd
  3. MolOps translates a queued MolAction list (hide_all, load, show, zoom, color) to the correct `cmd.*` sequence, and a headless smoke confirms the resulting object has the expected representation visible (asserted via `count_atoms` on the shown selection)
  4. Every `cmd.*` call introduced carries a `file:line` source-citation comment referencing `tmp/pymol-src/modules/pymol/` (the "read the source first" convention is established)
**Plans**: TBD (likely 2–3 plans; `/gsd-research-phase` NOT needed — APIs verified line-by-line in STACK.md)

Plans:
- [ ] 03-01: TBD

### Phase 4: Editing, Protonation & Restore Safety Net
**Goal**: The highest technical-risk feature — limited molecule editing with a restore safety net — works headlessly: the `alter`→`sort` silent-corruption trap is mitigated by a single sanctioned helper, backups/restore survive any edit, protonation defaults are curated variants (no pH engine), and edit routing (known→branch, unknown→bad-ending pool) is demonstrable end-to-end.
**Depends on**: Phase 3 (cmd layer); Phase 2 (edit_router logic, bad-ending nodes)
**Requirements**: EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-05, CAST-03
**Success Criteria** (what must be TRUE):
  1. The `apply_edit` helper is the only sanctioned alter path (grep finds no bare `cmd.alter` outside it); it always calls `cmd.sort` + `cmd.rebuild`, and a headless unit test confirms a post-edit `byres` selection returns the expected atoms (no silent corruption)
  2. For each edit type (point mutation, substrate edit, protonation change), a backup snapshot is taken before the edit (default-args `cmd.create`, verified by `count_atoms`) and "restore" (`cmd.delete` + `cmd.create` from backup) returns the object to its pre-edit atom count and residue identity
  3. EditRouter routes a known edit (matching an `edits.json` entry) to its defined story branch, and routes an unknown edit to the bad-ending pool — demonstrated headlessly with fixture edit intents
  4. ProtonationManager applies a curated protonation variant (load pre-built structure OR `cmd.alter` resn + targeted `h_add`/`remove`) for at least one approved example, and a user-adjustable switch between curated variants is exercisable
  5. A per-enzyme minimum-coverage scan asserts every cast enzyme represented so far has ≥1 known-edit entry + the restore path (scan is green on the current enzyme set)
**Plans**: TBD (likely 3–4 plans; `/gsd-research-phase` recommended for per-residue protonation variant sets + edit-table coverage criteria)

Plans:
- [ ] 04-01: TBD

### Phase 5: Pre-Content Key Decisions & Source Approval
**Goal**: The four science-framing decisions that block content authoring are resolved by the human, the per-claim approval workflow is operationalized (batch-by-source agreed), and the first set of sources for the glucose critical-path + TCA weights is pre-approved — unblocking the content phases. This is a PARALLEL track that runs alongside Phases 2–4 (engineering on placeholder content) and gates Phases 6–9 content.
**Depends on**: Nothing content-specific (runs in parallel with Phases 2–4); gates Phases 6–9
**Requirements**: CITE-01
**Success Criteria** (what must be TRUE):
  1. The ATP/True-Ending carbon-fate reframing is resolved (one option chosen from the Pitfall 4 options) and documented in PROJECT.md Key Decisions, with the chosen framing's carbon-fate claim entered into `data/citations.json` as `approved`
  2. The C14 radioactive-decay bad-ending timescale framing is resolved (drop / time-compress / reframe as teaching moment) and documented; if decay is kept, the half-life citation is approved
  3. The anaerobic-pathway framing is resolved (host-condition branch / separate scenario / bad-ending trigger) and documented in PROJECT.md Key Decisions
  4. The batch-by-source vs strict per-claim approval process is agreed with the human and documented; the claims registry holds the first batch of approved sources for the glucose critical-path enzymes + TCA RNG weights (front-loaded source approval)
  5. CITE-01's per-claim checkpoint is operational: no scientific claim lands in code/content without a corresponding `approved` entry in the registry (enforced by the Phase 1 pre-ship gate at build time)
**Plans**: TBD (likely 2–4 plans, one per decision + the workflow setup; the 4 decisions are independent and can be resolved in parallel by the human)

Plans:
- [ ] 05-01: TBD

### Phase 5.1: Story Graph Design — Glucose Skeleton + Integration Contracts (INSERTED)
**Goal**: The real glucose story graph is designed as a reviewable JSON skeleton — every node, edge, choice point (mapped to a real pathway branch point), RNG-weighted node, edit-allowed node (with routing target), and ending attachment is specified and validated — AND the two integration contracts that connect the story to gameplay are defined: (a) the **choice-point contract** (how a text multiple-choice selection maps to a graph edge) and (b) the **edit-node contract** (which story nodes allow edits, what EditIntent each player-edit-action generates, and how the EditRouter's known/unknown outcome routes back into the graph). This de-risks Phases 6–7 by making the story structure + gameplay integration explicit design artifacts before any UI or cited content is built on top — directly resolving the user's concerns about story design, the MC-vs-editing distinction, and how editing relates to the story.
**Depends on**: Phase 2 (engine + reachability checker to validate the skeleton); Phase 5 (ATP/True-Ending framing + anaerobic framing resolved — these determine the True-ending node and the anaerobic branch topology). Can start as soon as Phase 2 + the Phase 5 ATP decision are done (potentially before Phase 4 finishes).
**Requirements**: (none owned — design phase; enables STORY-01, STORY-03, STORY-06, STORY-07, EDIT-04 delivery in Phases 6–7)
**Success Criteria** (what must be TRUE):
  1. A glucose story graph skeleton JSON exists with every node typed (`story` / `choice` / `rng-shuffle` / `edit-allowed` / `ending`), every choice point annotated with the real pathway branch point it maps to (e.g. pyruvate → acetyl-CoA vs → lactate), and all four ending tiers attached — no invented branches (human-review the mapping against spec.md + approved sources)
  2. The Phase 2 reachability checker runs **green** on the glucose skeleton (all four ending tiers reachable from the glucose start node) and **red** on a deliberately-orphaned variant — the checker now guards real content, not just the toy graph
  3. The **choice-point contract** is documented: for each choice node, the skeleton specifies the player-facing options, the edge each selects, and the MolActions fired on traversal — making the "text MC → graph edge" integration an explicit, reviewable spec (not implicit in interpreter code)
  4. The **edit-node contract** is documented: the skeleton marks which story nodes allow edits, the EditIntent each player-edit-action generates, and the branch/bad-ending node the EditRouter routes to (known → defined branch node, unknown → bad-ending pool node) — making the "editing ↔ story" integration an explicit, reviewable spec
  5. Every node is explicitly classified as MC-choice, edit-allowed, both, or neither — resolving the "which is multiple choice, which is editing" question as a per-node design decision, not an emergent property of the implementation
**Plans**: TBD (likely 2–3 plans; `/gsd-research-phase` NOT needed — design on already-resolved framings, but human review of the branch-point mapping against spec.md is required)

Plans:
- [ ] 05.1-01: TBD

### Phase 5.2: Cast & Hero Representation Design — Visual Language + Scene Templates (INSERTED)
**Goal**: The 3D representation language is designed as a reviewable artifact — the C14 hero highlight convention (how the player sees "their" atom in any structure), the per-stage-type scene templates (which residues are shown, in what representation, with what zoom/color), and the cast-reveal convention (how an enzyme appears when first encountered) — headless-prototyped on placeholder/bundled structures, so Phase 6 implements an already-reviewed visual design rather than inventing it inside the overloaded first-Qt phase. This directly resolves the user's concern about cast representation and hero representation.
**Depends on**: Phase 3 (cmd layer — structures loadable headlessly for prototyping); Phase 5.1 (story stages defined — to know which stage types need scene templates)
**Requirements**: (none owned — design phase; enables CHAR-02, CAST-05 delivery in Phase 6; CAST-01 delivery in Phase 9)
**Success Criteria** (what must be TRUE):
  1. A **C14 hero highlight convention** is specified (selection rule + color + label + persistence across MolAction replay) and headless-prototyped: a loaded structure has the hero atom highlighted per the convention, verified by `cmd.iterate` on the hero selection (count == 1, expected element) — the "how is the hero represented" question is an explicit, reviewable spec
  2. A **scene-template library** exists (one MolAction sequence per stage type: e.g. "enzyme active-site reveal", "substrate approach", "product release", "branch-point comparison"), each headless-prototyped on a bundled/placeholder structure with post-condition assertions (expected representation visible, expected residue count in selection) — the "cast representation at stages" question is an explicit, reviewable spec
  3. A **cast-reveal convention** is specified (how a new enzyme first appears: full structure vs active-site-focused, labeling, color scheme) and documented for review — the visual design language is consistent across the cast, not ad-hoc per node
  4. The convention is **human-reviewed for clarity** (can a player actually see the hero + the relevant residues at each stage?) — this is a design-review checkpoint, not yet the in-game human-verify (that's Phase 6)
**Plans**: TBD (likely 1–2 plans; `/gsd-research-phase` NOT needed — visual design on placeholder structures; real cast PDBs land in Phase 6/9)

Plans:
- [ ] 05.2-01: TBD

### Phase 6: Qt UI + Minimal Playable MVP (Glucose + True+Bad)
**Goal**: The game is playable end-to-end for the first time in a real Windows PyMOL session — a player installs the plugin, starts a glucose game, sees the C14 hero highlighted (per the reviewed Phase 5.2 convention), makes choices (per the reviewed Phase 5.1 choice-point contract), edits molecules (per the reviewed Phase 5.1 edit-node contract), sees real structures at the relevant stages (per the reviewed Phase 5.2 scene templates), saves/loads, and reaches a True or Bad ending — with the UI as a thin adapter over the already-proven engine + molecular layer + already-reviewed design artifacts. This is the FIRST human-verify milestone.
**Depends on**: Phases 2, 3, 4 (engine + molecular layer); Phase 5 (approved glucose content + resolved Key Decisions); Phase 5.1 (glucose story graph skeleton + integration contracts); Phase 5.2 (hero/cast representation convention + scene templates)
**Requirements**: PLGN-01, PLGN-02, CHAR-02, CAST-04, CAST-05, DOC-03, ACH-01, ACH-02
**Success Criteria** (what must be TRUE):
  1. The plugin installs via Plugin Manager (package dir → .zip → startup/) and on PyMOL restart a "RPG: Tale of C" menu item appears; the main window opens with character selection, story text, choice panel, and cast/help/save/load/achievement controls (human-verify)
  2. Starting a glucose game highlights the C14 hero atom in the loaded 3D structure (color + label), and as the player advances, specific residue representations appear at the relevant pathway stages (human-verify)
  3. The player can reach a True ending and a Bad ending for glucose via text multiple-choice; a save mid-game and load restores the exact session (story position + RNG state + loaded structures + view) (human-verify)
  4. On first play, a one-time bulk-download prompt fetches the large structures needed (with progress + cancel + retry + offline fallback that locks only affected characters); small/critical structures are bundled so the game starts instantly (human-verify)
  5. The achievement board shows unlocks (glucose tried + endings found so far) and persists across PyMOL sessions to a user-writable file; in-game help includes molecule-editing pointers + PyMOL wiki links (human-verify)
**Plans**: TBD (likely 5–7 plans — this is the first Qt-bearing phase; `/gsd-research-phase` recommended: ATP/True-Ending reframing MUST be resolved before this phase's content, critical-path cast PDB IDs + resolutions + citations, TCA RNG weight values)

Plans:
- [ ] 06-01: TBD

### Phase 7: Content Expansion I — All Glucose Endings + Full Glucose Pathway
**Goal**: The glucose character's complete pathway is authored with all four ending tiers reachable, RNG-weighted TCA steps using approved weights, real pathway branch points (no invented branches), and two-layer (dramatic + teaching) text on every glucose node — proving the full content model on one character before replicating to others.
**Depends on**: Phase 6 (MVP loop proven); Phase 5 (approved sources + weights); Phase 5.1 (glucose skeleton + branch-point mapping — fleshed out with cited text here)
**Requirements**: STORY-03, STORY-06, STORY-07
**Success Criteria** (what must be TRUE):
  1. The glucose pathway graph includes all four ending tiers (True, Good, Normal, Bad) and the reachability checker confirms all four are reachable from the glucose start node (pure-Python test, green)
  2. TCA-cycle shuffle nodes use RNG-weighted stochastic steps with weights drawn from approved sources (claim_ids approved in the registry); a seeded run produces a documented, reproducible fate (determinism test)
  3. Every choice point in the glucose path maps to a real pathway branch point (e.g. pyruvate → acetyl-CoA vs → lactate), with no invented branches — each mapping carrying an approved claim_id
  4. Every glucose story node carries both a dramatic-layer text (plain-language stakes) and a teaching-layer text (correct terminology, pathway logic, editable residues explained), both passing the per-claim citation gate
**Plans**: 5–7 plans — one per pathway segment + its citations (see "Content Phase Plan Granularity" below). `/gsd-research-phase` for glucose pathway branch enumeration + ending-fate citations.

Plans:
- [ ] 07-01: TBD — likely glycolysis segment (glucose → pyruvate): nodes + branch points + citations + two-layer text
- [ ] 07-02: TBD — likely pyruvate transition branch (→ acetyl-CoA vs → lactate): the key STORY-07 branch point
- [ ] 07-03: TBD — likely TCA cycle: RNG-weighted stochastic nodes (STORY-03), weights approved per-claim
- [ ] 07-04: TBD — likely ETC / oxidative phosphorylation: True-ending carbon fate
- [ ] 07-05: TBD — likely glucose bad-endings pool + edit-routing tie-ins
- [ ] 07-06: TBD — likely two-layer text pass + reachability green (4/4 endings) + citation gate green

### Phase 8: Content Expansion II — Fatty Acid + Alcohol Characters
**Goal**: The fatty acid and alcohol characters are authored with all four ending tiers each, completing the three-character roster — every character can reach every ending, fulfilling the v1 success measure ("all endings reachable for all characters").
**Depends on**: Phase 7 (content model proven on glucose)
**Requirements**: CHAR-01, STORY-02
**Success Criteria** (what must be TRUE):
  1. The new-game screen offers all three characters (glucose, fatty acid, alcohol); selecting each starts a distinct pathway with character-specific entry nodes and C14-hero identification (human-verify)
  2. The reachability checker confirms all four ending tiers are reachable for each of the three characters (12 assertions, green) — the v1 success measure is met
  3. Fatty acid and alcohol pathway content (nodes, branch points, two-layer text, ending fates) passes the per-claim citation gate (no unapproved claims ship)
  4. A save/load round-trip works for fatty acid and alcohol playthroughs (RNG state + story position + scene restored) — human-verify at least one ending per character
**Plans**: 4–6 plans — one per character × segment + its citations (see "Content Phase Plan Granularity" below). `/gsd-research-phase` for fatty acid / alcohol pathway branches + ending fates.

Plans:
- [ ] 08-01: TBD — likely fatty acid entry + beta-oxidation path: nodes + citations + two-layer text
- [ ] 08-02: TBD — likely fatty acid all 4 endings (True/Good/Normal/Bad) + reachability for FA
- [ ] 08-03: TBD — likely alcohol entry + ADH/ALDH path: nodes + citations + two-layer text
- [ ] 08-04: TBD — likely alcohol all 4 endings + reachability for alcohol
- [ ] 08-05: TBD — likely cross-character reachability green (3 chars × 4 endings = 12 assertions) + citation gate green

### Phase 9: Anaerobic Pathway + Full Cast + Documentation Completion
**Goal**: The anaerobic pathway is represented per the chosen Phase 5 framing, the full ~20+ enzyme cast is populated with verified citations, and the dramatic cast list + slogan appear in both the README and in-game help — the content scope is complete.
**Depends on**: Phase 8 (3 aerobic characters complete); Phase 5 (anaerobic framing decision)
**Requirements**: STORY-05, CAST-01, DOC-01, DOC-02
**Success Criteria** (what must be TRUE):
  1. The anaerobic pathway is represented in the game structure per the approved framing (from Phase 5), reachable in-game, with approved two-layer text and citations (human-verify the path is playable)
  2. The cast registry contains ~20+ enzymes, each with a verified PDB ID + resolution (parsed from the actual file header, not memory) + approved citation; the per-enzyme minimum edit-coverage scan is green for the full cast
  3. The repo-root README includes the full dramatic cast list (protein name, PDB ID, resolution) + dramatic slogan, generated from the cast manifest (`tools/build_cast_list.py`)
  4. In-game help displays the same dramatic cast list + slogan (not just the README) — human-verify
**Plans**: 4–5 plans — separated by content concern (anaerobic path / cast / docs), not pathway segment (see "Content Phase Plan Granularity" below). `/gsd-research-phase` for full ~20+ cast enumeration + citations + anaerobic-path content once framing decided.

Plans:
- [ ] 09-01: TBD — likely anaerobic pathway content (per Phase 5 framing): nodes + citations + two-layer text + reachability
- [ ] 09-02: TBD — likely full ~20+ cast enumeration: PDB IDs + resolutions (parsed from file headers) + citations (CAST-01)
- [ ] 09-03: TBD — likely README dramatic cast list + slogan generated from cast manifest (DOC-01)
- [ ] 09-04: TBD — likely in-game help cast list + slogan (DOC-02)
- [ ] 09-05: TBD — likely full reachability + per-enzyme edit-coverage scan + citation gate green

### Phase 10: Polish, Playtest & Release Readiness
**Goal**: The game is playtested end-to-end, the edit-routing table is expanded based on session logs of unknown edits, accessibility (colorblind-safe palette, glossary/tooltips) is in place, and the full manual GUI test matrix + pre-ship citation gate pass — the plugin's content and engineering are polished and ready for documentation finalization. (This phase owns no new requirement; it completes and verifies all prior content/engineering requirements. Documentation finalization + verification is Phase 11.)
**Depends on**: Phase 9 (content complete)
**Requirements**: (none owned — polish/release-gate phase completing prior requirements)
**Success Criteria** (what must be TRUE):
  1. The pre-ship citation gate (`tools/check_citations.py`) passes with zero missing/unapproved claims across all story content — no fabricated science ships
  2. A full manual GUI test matrix run (start game per character, make each edit type, trigger each ending tier, save/load, open achievement board, open help, bulk-download retry) passes on a real Windows PyMOL session
  3. The edit-routing table is expanded for the most-common unknown edits discovered in playtest (session logs reviewed), and bad-endings carry explanatory teaching-layer text (not punitive)
  4. Accessibility is in place: a colorblind-safe palette toggle is available, and jargon terms have glossary/tooltip explanations on first use (human-verify)
  5. The full reachability checker is green for all content (3 chars × 4 endings + anaerobic), and a seeded demo run reproduces a documented playthrough
**Plans**: TBD (likely 2–4 plans)

Plans:
- [ ] 10-01: TBD

### Phase 11: Documentation Finalization & Verification
**Goal**: All user-facing documentation — README, in-game help text, any tutorials — is updated to accurately reflect the final shipped game content (dramatic cast list, slogan, cast PDB IDs + resolutions matching the shipped cast from Phase 9; content changes from Phase 10's playtest-driven polish reflected), and a final documentation verification pass confirms docs are accurate, complete, and consistent with the shipped game. This is the last release gate before ship.
**Depends on**: Phase 9 (initial docs created — DOC-01, DOC-02); Phase 10 (content polish complete — playtest-driven changes settled, so docs reflect final content)
**Requirements**: (none owned — finalization/verification phase updating + verifying DOC-01, DOC-02 against shipped reality, per the Phase 10 0-requirement precedent)
**Success Criteria** (what must be TRUE):
  1. The repo-root README's dramatic cast list (protein name, PDB ID, resolution) matches the final shipped cast manifest exactly — every enzyme in the game is listed with its correct PDB ID + resolution (parsed from the actual file header), and no listed enzyme is missing from the game (human-verify README against cast manifest)
  2. In-game help text displays the same dramatic cast list + slogan as the README, and both match the shipped game content (human-verify in a real PyMOL session)
  3. All documentation reflects Phase 10's playtest-driven content changes (edit-table expansion, accessibility glossary/tooltip additions, bad-ending teaching text) — no stale documentation (human-verify)
  4. Final documentation verification gate passes: README, in-game help, and any tutorials are accurate, complete, and consistent with the shipped game (human sign-off as the last release gate)
**Plans**: TBD (likely 1–2 plans)

Plans:
- [ ] 11-01: TBD — likely README + in-game help update to match final shipped cast + content
- [ ] 11-02: TBD — likely final documentation verification pass (release gate)

## Content Phase Plan Granularity (Phases 7–9)

**Decision:** Content phases (7, 8, 9) are NOT split into more phases. Instead, each content phase uses **granular plans — one per pathway segment + its citations** (5–7 plans for Phase 7; 4–6 for Phase 8; 4–5 for Phase 9). This keeps the roadmap within the comprehensive depth range (12 phases) while giving the human a per-segment review cadence that matches the per-claim approval bottleneck.

**Why plans-within-phases, not more phases:**

1. **Per-claim approval is orthogonal to phase structure.** The timeline-dominating bottleneck (Pitfall 7) is the human approving individual citations as they're researched. This happens at *claim* granularity regardless of how phases are sliced. Splitting phases adds phase-completion checkpoints, not claim-approval checkpoints — the human is already the per-claim verifier for content.
2. **Already at the top of comprehensive depth (12 phases).** Splitting glucose into 2–3 sub-phases + FA/Alc into 2 + anaerobic/cast/docs would push to 15–17 phases, exceeding the comprehensive range — a structural signal of over-fragmentation.
3. **Content segments are largely sequential, not parallel.** Pathway continuity (TCA text depends on glycolysis branch decisions) means splitting phases doesn't unlock parallelism that plans-within-phase doesn't already offer. The phase boundary buys no scheduling benefit.
4. **Phase-level verifier marginal value is low for content.** Content verification = the citation gate, already enforced architecturally at build time (Phase 1's `check_citations.py`). The verifier's highest value is on engineering phases (does the architecture hold?); for content, per-claim human approval is the real gate. More phases = more verifier runs on content for little marginal assurance.
5. **Plans provide the granularity with less ceremony.** One plan per pathway segment gives the human a natural review cadence ("this plan = glycolysis authored + cited, review before next plan") *without* the `/gsd-plan-phase` ceremony overhead each new phase would add. Plans are sequenced; per-plan review is preserved.

**Plan granularity axis (the split that lives inside each phase):**
- **Phase 7 (glucose):** by pathway segment — glycolysis / pyruvate-branch / TCA (RNG) / ETC / bad-endings / text+reachability pass.
- **Phase 8 (FA + alcohol):** by character × endings — FA path / FA endings / alcohol path / alcohol endings / cross-char reachability pass.
- **Phase 9 (anaerobic + cast + docs):** by content concern — anaerobic path / cast enumeration / README / in-game help / final gate. (Here the natural axis is concern-type, not pathway segment, because the requirements are heterogeneous: STORY-05, CAST-01, DOC-01, DOC-02.)

**What the human gets at each plan boundary:** a pathway segment (or character ending set, or cast batch) with its citations entered as `approved` in the registry, two-layer text written, and the reachability checker re-run green on the increment. This is the meaningful review checkpoint — it lives at plan granularity, not phase granularity.

## Parallelization Notes

- **Phase 5 (Decisions + Source Approval) is the parallel track.** It runs alongside Phases 2–4 (engineering on `UNAPPROVED_PLACEHOLDER` content). The critical path is: *engineering races ahead while the human resolves science framings and approves sources in parallel.* Phase 5's four Key Decisions are independent of each other and can be resolved in parallel by the human.
- **Phase 5.1 (Story Graph Design) can start early.** It depends on Phase 2 (engine + reachability checker) and the Phase 5 ATP/True-Ending decision only — so it can begin as soon as those two are ready, potentially before Phase 4 finishes. It designs the real glucose skeleton + the MC-choice and edit-node integration contracts, and gates Phase 6.
- **Phase 5.2 (Representation Design) follows 5.1 + Phase 3.** It prototypes the hero-highlight + scene-template convention headlessly on placeholder structures. It gates Phase 6's visual implementation but not its engineering.
- **Both 5.1 and 5.2 are design phases (0 requirements owned).** They produce reviewable artifacts (story graph skeleton JSON + integration-contract docs; representation convention + headless-prototyped scene templates) that Phase 6 implements and Phases 7–9 extend. They de-risk the overloaded first-Qt phase by making story structure and visual language explicit *before* UI code.
- **Content phases (7–9) are sequential** for a solo developer (each builds on the content model of the prior), but the per-file pathway split in `data/story/` means different pathways *could* be authored in parallel worktrees if additional capacity exists. Phase 7 fleshes out the Phase 5.1 glucose skeleton with cited two-layer text.
- **Worktree/branch protocol** (per spec.md): parallel plan execution should use separate git worktrees/branches to avoid conflicts, especially when Phase 5 (content research/approval) overlaps with Phases 2–4 (engineering).
- **Engineering never blocks on content approval**: Phases 2–4 ship on placeholder content; the citation gate (Phase 1) blocks only at ship time, not at dev time.

## Research Flags (phases that should run `/gsd-research-phase` before planning)

| Phase | Research needed? | Why |
|-------|------------------|-----|
| 1 Foundations | No | Stdlib + ink data model — well-documented |
| 2 Engine Core | No | Ink patterns verified; architecture owns the interpreter |
| 3 PyMOL cmd Layer | No | APIs verified line-by-line in STACK.md |
| 4 Editing + Protonation | **Yes** | Per-residue protonation variant set per structure; edit-table coverage criteria (HIGH validation load) |
| 5 Key Decisions | **Yes (heaviest human-approval load)** | ATP/True-Ending reframing, C14-decay framing, anaerobic framing, batch-vs-per-claim approval — these ARE research/approval tasks |
| 5.1 Story Graph Design (INSERTED) | No | Design on already-resolved framings; human review of branch-point mapping against spec.md, not new research |
| 5.2 Representation Design (INSERTED) | No | Visual design prototyped headlessly on placeholder structures; real cast PDBs land in Phase 6/9 |
| 6 MVP | **Yes** | ATP/True-Ending reframing MUST be resolved before this phase's content; critical-path cast PDB IDs + resolutions + citations; TCA RNG weight values |
| 7 Glucose content | **Yes** | Glucose pathway branch enumeration + ending-fate citations |
| 8 Fatty acid + alcohol | **Yes** | Fatty acid / alcohol pathway branches + ending fates |
| 9 Anaerobic + cast | **Yes** | Full ~20+ cast enumeration + citations; anaerobic-path content once framing decided |
| 10 Polish | No | Playtest-driven iteration on existing content |
| 11 Docs Finalization | No | Docs update + verification against shipped content — no new research |

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 5.1 → 5.2 → 6 → 7 → 8 → 9 → 10 → 11. Phase 5 runs in PARALLEL with Phases 2–4 and must be complete (at least the ATP/True-Ending + anaerobic decisions) before Phase 5.1 begins. Phase 5.1 and 5.2 (INSERTED design phases) gate Phase 6. Phase 11 (documentation finalization + verification) is the last release gate, after Phase 10's content polish is complete.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundations & Citation Gate | 0/TBD | Not started | - |
| 2. Story Engine Core | 0/TBD | Not started | - |
| 3. PyMOL cmd Layer | 0/TBD | Not started | - |
| 4. Editing + Protonation + Restore | 0/TBD | Not started | - |
| 5. Pre-Content Key Decisions (parallel) | 0/TBD | Not started | - |
| 5.1 Story Graph Design (INSERTED) | 0/TBD | Not started | - |
| 5.2 Representation Design (INSERTED) | 0/TBD | Not started | - |
| 6. Qt UI + MVP (Glucose + True+Bad) | 0/TBD | Not started | - |
| 7. Content I: All Glucose Endings | 0/TBD | Not started | - |
| 8. Content II: Fatty Acid + Alcohol | 0/TBD | Not started | - |
| 9. Anaerobic + Full Cast + Docs | 0/TBD | Not started | - |
| 10. Polish, Playtest & Release | 0/TBD | Not started | - |
| 11. Documentation Finalization & Verification | 0/TBD | Not started | - |

---

*Roadmap created: 2026-08-12 · Revised: 2026-08-12 (inserted Phases 5.1 + 5.2 — story graph design + representation design — per user feedback on story/editing/representation concerns) · Revised: 2026-08-12 (content phases 7/8/9 kept at 3 — not split further; per-pathway-segment plan granularity documented in "Content Phase Plan Granularity" section, per user feedback on content-authoring citation load) · Revised: 2026-08-12 (split documentation finalization + verification OUT of Phase 10 into Phase 11 — Phase 10 keeps polish/playtest/accessibility/test-matrix/citation-gate; Phase 11 owns docs update + final docs verification as the last release gate, per user feedback)*
*Depth: comprehensive (13 phases: 11 integer + 2 INSERTED decimal design phases — slightly above the 8–12 comprehensive ceiling; the Phase 11 split is a user-requested separation of documentation verification from polish) · Coverage: 32/32 v1 requirements mapped ✓ (5.1 + 5.2 + 11 own 0 requirements — design/finalization phases enabling/verifying downstream delivery, per the Phase 10 0-requirement precedent)*
*Note: REQUIREMENTS.md previously stated "34 total" v1 requirements; the actual enumerated v1 set is 32 (PATH-01 and STAT-01 are v2). Traceability below uses the actual count of 32.*
