# Feature Landscape

**Domain:** PyMOL 2.5.0 educational RPG plugin teaching cellular respiration (C14 hero through the respiratory pathway)
**Researched:** 2026-08-12
**Overall confidence:** MEDIUM-HIGH (PyMOL plugin conventions + molecular-game landscape HIGH from source/live fetch; educational-game pedagogy MEDIUM from Wikipedia/Barab 2009)

## How to read this document

This project carries a non-negotiable constraint from `spec.md`: **every scientific claim and citation (DOIs, PDB IDs, pathway facts) must be verified against an approved source and explicitly human-approved via per-claim checkpoint before landing in code/content.** Because of that, every feature below carries a **Validation Load** estimate — how many distinct scientific claims the feature will generate that need human approval. This is the single most important planning dimension for this project, more decisive than engineering complexity.

**Complexity key:** S = ~1 day, M = ~2-4 days, L = ~1-2 weeks, XL = ~3+ weeks (for one competent dev on this stack).
**Validation load key:** LOW = design/engineering only, near-zero science claims; MED = a handful of framings to review; HIGH = many per-step claims (PDB IDs, pathway facts, probabilities, protonation states) each needing checkpoint; XL = on the order of dozens-to-hundreds of claims (a content-authoring marathon).

Features are grouped as **Table Stakes** (a PyMOL educational plugin is expected to have these; missing them = the plugin feels broken or unprofessional), **Differentiators** (set this game apart; not expected but valued), and **Anti-Features** (deliberately NOT build — see rationale, each tied to a verified comparator).

---

## Table Stakes

Features users (educators + students) expect. Missing any = the plugin feels incomplete or unprofessional for a PyMOL educational tool.

| # | Feature | Why Expected | Complexity | Dependencies | Validation Load | Notes |
|---|---------|-------------|------------|--------------|-----------------|-------|
| T1 | **Plugin loads via modern `pymol.Qt` + menu entry** | PyMOL 2.5.0 plugin standard; legacy `pmgqt`/Tk is deprecated-looking. `dynoplot.py` shows the canonical form: `from pymol.Qt import QtCore, QtGui, QtWidgets`, `__init_plugin__` + `addmenuitemqt`. | S | none | LOW | Boilerplate. Verified pattern in `Pymol-script-repo/plugins/dynoplot.py` (HIGH). |
| T2 | **In-game help text with editing pointers + PyMOL wiki links** | Any educational plugin must explain itself. `emovie.py` puts a help button + multi-paragraph explanation on *every* dialog. Spec mandates wiki links. | S | UI shell (T1) | LOW | Copywriting + URL curation. PyMOL wiki URLs are stable references, not science claims. |
| T3 | **Save / load buttons persist game state to a file** | Spec-mandated; `emovie.py` demonstrates the pattern (pickle of a storyboard list). Educators need to resume a demo. | M | State model (D1) | LOW | Pure plumbing. Use JSON (human-readable, diff-friendly) not pickle unless carrying Qt objects. |
| T4 | **Multiple-choice text UI drives the story** | Spec-mandated gameplay element. Text MC is the lowest-friction interaction for a teaching tool. | M | Narrative graph (D2) | MED | Each choice's *framing* needs review, but the MC mechanic itself is engineering. |
| T5 | **Show specific residue representations as the game proceeds** | Spec-mandated; the whole point of being *in* PyMOL vs a standalone game. `emovie.py` scene system (`cmd.scene(..., "store"/"recall")`) is the idiomatic pattern. | M | Scene system + PDB cast (T6) | HIGH | Each "which residue, which representation, at which stage, why" is a science claim. This is where the per-claim checkpoint bites hardest. |
| T6 | **Protein "cast" of ~20+ enzymes from the PDB, each with PDB ID + resolution + citation** | Spec-mandated. Reactome (live-fetched, HIGH) shows the provenance model: curated, peer-reviewed, cited. A teaching plugin citing PDB IDs without verification would be malpractice *for this audience*. | L | PDB acquisition (D3) | HIGH (XL edge) | ~20+ proteins × (PDB ID correct + resolution correct + role-in-pathway correct + license/source) = the largest single validation load in the project. |
| T7 | **Small-molecule substrates as 3D models from PubChem or PDB** | Spec-mandated. The C14 hero and intermediates need real coordinates. | M | Molecule loader (D3) | HIGH | Each substrate source + protonation state is a claim. |
| T8 | **Protonation physiological-pH (or reaction-relevant) by default; user-adjustable** | Spec-mandated. Wrong protonation = wrong chemistry = undermines the teaching layer. | M | Molecule loader (D3) | HIGH | Each default protonation state is a claim; "user-adjustable" shifts remaining burden to the user but the *default* still needs approval. |

**Table-stakes total validation load is dominated by T5/T6/T7/T8** — these are the features that turn "a game" into "a *scientifically correct* game," and they are where the per-claim checkpoint will spend most of its cycles.

---

## Differentiators

Features that set this game apart from (a) reference tools like Reactome and (b) molecular games like Foldit. These are the project's competitive advantage and its pedagogical thesis.

| # | Feature | Value Proposition | Complexity | Dependencies | Validation Load | Notes |
|---|---------|-------------------|------------|--------------|-----------------|-------|
| D1 | **C14 hero identification + 3-character selection (glucose / fatty acid / alcohol)** | "Conceptual play" + "empathetic embodiment" (Barab 2009, cited in Wikipedia MEDIUM): projection into a character role in a fictional problem context drives learning. The C14-as-protagonist framing is what makes this an RPG, not a quiz. | M | Narrative graph (D2) | MED | Starting-molecule science must be approved; the *identification* mechanic is design. |
| D2 | **Branching narrative graph of pathway choice points** | "Risk-free experimentation with consequences" (Wikipedia MEDIUM): mistakes in a safe virtual world teach awareness of consequentiality. Branching = replay value + coverage of the pathway space. | L | none (foundational) | HIGH | Each node/edge is a pathway-fact claim. Model as a DAG (directed acyclic graph) of narrative nodes to keep validation tractable — avoid free-form text generation. |
| D3 | **Four ending tiers (True = hero's electrons/"soul" harvested into ATP via ETC after RNG-weighted TCA path / Good = carbon body retained pre-oxidation (storage or amino acid) / Normal = CO2 released without full electron harvest / Bad = lost-released-host-death-decay-cycle-trap)** | "Awareness of consequentiality" (Wikipedia MEDIUM). Multiple endings per character = the branching payoff. Spec mandates all 4 reachable for every character. Pitfall 4 resolved via the soul-jump reframing (2026-08-13): the carbon body exits as CO2; the electrons ("soul") reach ATP via the ETC. | L | Narrative graph (D2) | HIGH | Each ending's *chemistry* must be correct (e.g., "stored as fatty acid" must be a real fate, not invented). Story-like framing is design; the underlying fate is a claim. |
| D4 | **RNG-weighted stochastic steps (TCA cycle shuffle), seedable for teaching** | Real biochemistry: a given C14 does not always exit as CO2 in one TCA turn; it can cycle multiple times. Seedable RNG = **reproducible classroom demos** (educator sets seed → every student sees the same fate → discussable). This is the single most important differentiator for the *educator* audience. | M | Pathway model (D2) | HIGH | The branching *probabilities* must be scientifically grounded (not invented numbers). Seedability is pure engineering (stdlib `random` with explicit seed). Provide both a "fixed seed (demo)" mode and a "random (play)" mode. |
| D5 | **Limited molecule editing: point mutations, substrate edits, protonation changes** | Hands-on manipulation is what makes being *in PyMOL* meaningful vs a passive animation. Maps to Foldit's "tools to manipulate the structure" pattern (HIGH, live-fetched). | L | PDB/molecule ops (T6/T7/T8) | MED | The *edit operations* are PyMOL `cmd.*` features (engineering). The validation load is in *which edits are recognized* — see D6. |
| D6 | **Edit routing via lookup table + bad-ending fallback** (unknown edit → "lost connection" / "released from host" pool) | Settled during questioning. Replaces a full chemistry-correctness engine with a tractable curated table. Keeps validation bounded: only *known* edit→branch mappings need approval; the fallback pool is design. | L | Edit UI (D5) + narrative (D2) | HIGH (bounded) | Each known mapping (enzyme-context × edit → defined branch) is a claim, but the set is *finite and enumerable*, unlike an open-ended correctness engine. The fallback pool itself carries LOW validation (it's narrative). |
| D7 | **"Reveal correct 3D model" / restore safety net** | Keeps gameplay smooth after a student makes a broken edit — they can recover without restarting. Foldit has the equivalent "reset puzzle" affordance. | S | Edit feature (D5) | LOW | Pure plumbing: stash a pre-edit snapshot, restore on demand. |
| D8 | **Achievement board (limited unlocks + limited collection of starting points/endings), persisted to file** | Spec-mandated. Collection-style achievements (find all endings, try all 3 characters) > performance-style (high score) because **collection encourages exploration of the content space**, which is the pedagogical goal. Persisted so educators can see what a class has explored. | M | Ending detection (D3) | LOW | Achievement *names* that reference science need a light review, but the mechanic is design. **Deliberately a board, not a leaderboard** — see Anti-Feature A5. |
| D9 | **Dramatic cast list (protein name, PDB ID, resolution) in README + in-game, plus dramatic slogan** | Spec-mandated. Mirrors a film cast list (name + role + credential); the PDB ID is the "credential." Gives credit + credibility + the "real data" frisson. Foldit/Reactome both surface provenance; this is the game-flavored version. | S | Cast data (T6) | LOW | Copywriting; the PDB IDs cited must be correct (already covered by T6's load). |
| D10 | **Two-layer text: dramatic layer (C14 hero's journey, plain-language stakes) + teaching layer (correct terminology, pathway logic, editable residues explained)** | The spec's "story-like without saying the exact scientific word" requirement *plus* the educator audience demand both layers. A student reads the drama; an educator reads the science. Single-layer text serves neither audience. | M | Narrative graph (D2) | MED-HIGH | The dramatic layer is design; the teaching layer must be scientifically correct. Each narrative node carries both. |
| D11 | **Anaerobic pathway representation** (framing deferred to deeper research — see PROJECT.md Key Decisions) | Covers the non-O2 exit (e.g., pyruvate → lactate / fermentation). Spec includes anaerobic in scope. | M | Pathway model (D2) | HIGH | Anaerobic chemistry must be approved. *How* it's framed (host-condition branch / separate scenario / bad-ending trigger) is an open design question flagged for phase research. |
| D12 | **Hybrid PDB acquisition: bundle small/critical structures; one-time bulk download prompt for large ones** | Balances plugin install size against hitting the network on every encounter. Spec acknowledges large proteins need a download step. | M | PDB cast (T6) | LOW | Engineering. Bundled PDBs need a license/source check (PDB is public-domain/CC0; good to note) but no science-claim review. |

---

## Anti-Features

Features to **explicitly NOT build**. Each is a real pattern from a verified comparator that we deliberately reject, with a reason.

| # | Anti-Feature | Why Avoid (with verified comparator) | What to Do Instead |
|---|--------------|---------------------------------------|-------------------|
| A1 | **Full molecular dynamics simulation** | Spec already settled this (OUT OF SCOPE). MD requires heavy deps beyond `pymol-open-source` (e.g., OpenMM) — violates the "no new deps silently" constraint — and visual/representational states are sufficient for teaching pathway *logic*. | Static/visual representations at each stage (T5). A trajectory is not needed to teach *which branch the carbon takes*. |
| A2 | **Automated chemistry-correctness engine for edits** | Replaced by D6 (settled during questioning). A real correctness engine needs a reaction-prediction library (e.g., RDKit + curated reaction rules) beyond the allowed stack, and an *unbounded* validation load (any edit, any molecule). Foldit's score function is the analog — it took a research lab years to build. | Lookup table of known edit→branch mappings + bad-ending fallback pool (D6). Validation is finite and enumerable. |
| A3 | **Stat / XP / leveling system** | Spec defers to v2. The True ending is the hero's electrons harvested into ATP (soul-jump reframing), so energy cannot double as the XP currency (double-meaning collision). The candidate model ("luck that affects host condition") needs scientific grounding not yet available. | v1: no XP. The "progress" is which endings/characters you've *collected* (D8 achievement board). v2 may revisit if "luck-affects-host" gets a grounded source. |
| A4 | **Real-time / multiplayer modes** | Spec OUT OF SCOPE. Single-player turn-based only. Multiplayer would complicate the educator reproducibility story (seedable RNG, D4) and the PyMOL single-session runtime. | Single-player, turn-based, seedable (D4). Classroom reproducibility is served by fixed-seed demos, not by multiplayer. |
| A5 | **Scoring leaderboard (group + individual rankings)** | Foldit (HIGH, live-fetched) uses leaderboards + group high-scores to drive *competition* for citizen-science output. That model optimizes for optimization/performance. Our model optimizes for *exploration* of the pathway space — competition discourages the slow exploration that teaching needs (a student who optimizes will rush to the ATP ending and miss the storage/CO2/bad branches). | Achievement **board** (D8): collection-based, not ranked. "You found all 4 endings" ≠ "you scored highest." This is the right pedagogical choice for a *teaching* game vs a *citizen-science* game. |
| A6 | **Non-respiratory pathways (photosynthesis, urea cycle, etc.)** | Spec OUT OF SCOPE. Theme is cellular respiration; scope discipline keeps the cast and validation load bounded. | v1: respiratory pathway only (aerobic + anaerobic). v2 may expand. |
| A7 | **Mobile / web port** | Spec OUT OF SCOPE. PyMOL is a desktop application; the plugin is the platform. Porting would mean re-implementing the molecular viewer — a different project. | PyMOL desktop plugin only. |
| A8 | **Legacy `pmgqt` / Tk interface** | Spec constraint + `dynoplot.py` (HIGH) shows the modern `pymol.Qt` form. `emovie.py` is the cautionary tale — it's still Tkinter, and it shows its age (Python 2/3 compat shims, `tkSimpleDialog`). | Modern `pymol.Qt` (PyQt5) only. Match `dynoplot.py`'s import style. |
| A9 | **Fabricated or unverified science** | The hard constraint from `spec.md`: "Do NOT make up anything. ALL claims and citations MUST BE VERIFIED against a source and explicitly approved." This isn't a feature, it's a *non-feature* — the temptation to fill content gaps with plausible-sounding chemistry must be resisted. | Per-claim checkpoint (already in the workflow). Every PDB ID, pathway fact, probability, and protonation state lands only after human approval. |

---

## Feature Dependencies

```
T1 Plugin shell ──────────────────────────────────┐
T2 In-game help ──────────────────────────────────┤  (UI foundation)
T3 Save/load ─────────────────────────────────────►│  needs: state model
                                                   │
D2 Branching narrative graph ◄── foundational ──────┤
  ├──► D1 C14 hero + 3-character selection
  ├──► D3 Four ending tiers (needs D2 + pathway model)
  ├──► D4 RNG-weighted stochastic steps (needs D2; seedable)
  ├──► D10 Two-layer text (each node carries both layers)
  └──► D11 Anaerobic pathway (needs D2; framing TBD)

T6 PDB cast (~20+ enzymes) ──┐
T7 Small-molecule substrates ─┤──► D3 PDB acquisition (D12 hybrid)
T8 Protonation defaults ──────┘
                              │
D5 Limited molecule editing ◄─┤  needs: T6/T7/T8 loaded + cmd.* ops
  ├──► D6 Edit routing lookup table + bad-ending fallback
  └──► D7 Reveal-correct / restore safety net

T5 Show specific residue representations at stages ◄── needs: scene system + T6

D8 Achievement board ◄── needs: ending detection (D3) + character selection (D1)

D9 Dramatic cast list + slogan ◄── needs: cast data (T6); copywriting on top
```

**Build order implication:** D2 (narrative graph) and T6 (PDB cast) are the two foundational pillars. T6 has the higher validation load; D2 has the higher design load. They can be developed in parallel, but **content authoring (D2 nodes + T6 cast) cannot race ahead of source approval** — that is the project's critical path.

---

## MVP Recommendation

For MVP, prioritize:

1. **T1 Plugin shell + menu** (S) — without this, nothing runs.
2. **T6 PDB cast (start with ~5-6 critical-path enzymes, not all 20+)** (L but *sliceable*) — pick the enzymes on the single shortest True-ending path (e.g., hexokinase → … → pyruvate dehydrogenase → TCA cycle → ETC → ATP synthase) and validate *those* first. The soul-jump path (hero's electrons → ETC → ATP synthase) is what defines the True ending; the carbon body is released as CO2 at PDH/TCA. Defer the long tail to later slices.
3. **D2 Branching narrative graph (single character = glucose, single True + single Bad ending first)** (L but *sliceable*) — prove the branching mechanic on the minimal loop before fanning out.
4. **D4 RNG-weighted stochastic steps (seedable)** — implement early because it determines whether the narrative graph is deterministic or replayable; retrofitting it later is expensive.
5. **T5 Show residue representations at stages** — the core "you are in PyMOL" payoff.
6. **D5 + D6 + D7 Edit → lookup → reveal/restore loop** — the second core payoff (hands-on + safety net).
7. **T3 Save/load + T2 In-game help** — needed for the educator demo loop.
8. **D8 Achievement board** — light; adds the collection payoff.
9. **D9 Dramatic cast list + slogan** — copywriting polish that's cheap once T6 exists.
10. **T7 Small-molecule substrates + T8 Protonation** — needed for the C14 hero and intermediates; validation-heavy.

**Defer to post-MVP slices (still v1, just later in the roadmap):**
- **D1 remaining 2 characters** (fatty acid, alcohol) — once the glucose loop + edit/lookup/RNG/ending machinery is proven, replicating to 2 more characters is mostly content authoring + validation, not engineering.
- **D3 the Good + Normal endings** — once True + Bad are reachable, add the middle tiers.
- **D11 Anaerobic pathway** — framing still needs phase research (PROJECT.md Key Decisions); safest to slot after the aerobic core is solid.
- **D10 two-layer text polish** — the dramatic layer can start minimal and be enriched once the science (teaching layer) is approved.
- **T6 the long tail of the ~20+ cast** — fill out after the critical-path enzymes are validated.

**Why this order:** It front-loads the two foundational pillars (D2 + T6) and the riskiest-removing feature (D4 RNG, because retrofitting determinism is costly), validates the per-claim checkpoint on a *small* set of enzymes first (so the approval workflow itself gets tested before the content marathon), and defers the content-volume work (more characters, more endings, more cast) to slices that are mostly authoring + validation rather than engineering.

---

## Educational-Game Patterns Surfaced (per quality gate)

### How other tools teach metabolic pathways interactively
- **Reactome (HIGH, live-fetched 2026-08-12):** the reference-tool model — curated, peer-reviewed pathway *browser* with citations, review-status flags, and provenance. It teaches by *letting you navigate* correct, cited content. It is NOT a game. **Our differentiator framing:** we add a narrative + consequence + identification layer *on top of* the kind of curated content Reactome exemplifies. The PDB cast + per-claim approval (T6 + A9) is our provenance discipline; the C14 hero + 4 endings (D1 + D3) is our game layer Reactome deliberately lacks.
- **Foldit (HIGH, live-fetched 2026-08-12):** the molecular-game model — *tutorials* on simple structures, then *puzzles* on real proteins, with *tools* to manipulate, a *score* per modification, and *leaderboards*. It optimizes for citizen-science *output*. **Pattern to borrow:** scaffolded tutorials → real content (start the player on a simplified/intro path before full branching). **Pattern to reject:** score + leaderboard (see A5) — we are teaching, not crowdsourcing.
- **Companion molecular games (HIGH, from Foldit's See-also):** EteRNA (RNA), Eyewire (neurons), Quantum Moves (physics), Rosetta@home / Folding@home (screensaver-style). These confirm the "human-based computation game" genre exists and is respected, but *all* lean citizen-science; none are teaching-RPGs over a curated pathway. That gap is where this project lives.

### Branching-narrative patterns that work in education games
- **"Conceptual play" + "empathetic embodiment"** (Barab 2009, cited via Wikipedia MEDIUM): projection into a character role in a partly-fictional problem context, applying conceptual understanding to transform it. The C14 hero *is* conceptual play. The character selection (D1) *is* empathetic embodiment.
- **"Risk-free experimentation with consequences"** (Wikipedia MEDIUM): mistakes in a safe virtual world. Our edit-routing + bad-ending fallback (D6) is the mechanic; the 4 endings (D3) are the consequences.
- **"Awareness of consequentiality"** (Wikipedia MEDIUM): choices have visible outcomes. The 4 ending tiers make the pathway's branch points *matter*.
- **Model the narrative as a DAG, not free text.** Each node = a choice point mapped to a real pathway branch. This keeps the validation load finite and the graph testable. (Engineering recommendation, not a pedagogical source — but it follows directly from the per-claim constraint.)
- **Map choice points to real pathway branch points** (e.g., pyruvate → acetyl-CoA vs → lactate). The drama is *in* the biochemistry; we don't invent branches, we surface real ones.

### Achievement systems in educational contexts
- **Collection > performance for teaching.** Collection achievements ("found all 4 endings", "tried all 3 characters", "discovered the anaerobic branch") reward *exploring the content space* — exactly what we want students to do. Performance achievements ("highest score", "fastest run") reward *optimization*, which for a teaching game means rushing to the "best" ending and missing the rest.
- **Persist to file** so educators can see what a class has explored and so a single student's progress survives across sessions (T3 + D8).
- **Limited unlocks** (spec says "limited number"): keep the board small (~10-20 achievements). Inflation dilutes the signal and the motivation. Each achievement should map to a genuinely distinct discovery, not a grind.
- **Deliberately not a leaderboard** (A5): Foldit's leaderboard is right for *its* goal (citizen-science competition) and wrong for *ours* (teaching exploration). A class leaderboard would discourage the slow, exploratory play that learning requires.

### What makes a "cast list" engaging
- **Dramatic framing** (spec slogan: "featuring high-resolution, real protein models in our cast"). The *real* is the hook — students recognize enzymes from their textbook (hexokinase, citrate synthase, ATP synthase) and get the frisson of "this is the actual structure."
- **Each entry: protein name + PDB ID + resolution** mirrors a film cast list (name + role + credential). The PDB ID is the credential — it's verifiable, it's provenance, it's the "this is real data" signal. Reactome's curated-provenance model (HIGH) is the scientific analog; our dramatic cast list is the game-flavored analog.
- **Engagement driver:** recognition + credibility. The cast list is also the *answer key* — it tells an educator exactly which structures are being used and where to verify them.

### How RNG is used pedagogically (seedable demos)
- **TCA cycle shuffles are real** — a given carbon does not always exit as CO2 in one turn; it can cycle multiple times before leaving. This is genuine biochemistry, not a game contrivance. The RNG models a real stochastic process.
- **Seedable RNG = reproducible classroom demos.** An educator sets the seed; every student sees the same fate; the class can *discuss why* that fate occurred. This is the single most important feature for the educator audience (D4).
- **Two modes:**
  - **Fixed-seed (demo) mode** — deterministic, for classroom reproducibility. Default for educators.
  - **Random (play) mode** — exploratory, shows the genuine stochastic reality. Default for student free-play.
- **The probabilities must be scientifically grounded** (HIGH validation load, D4). We do not invent "30% chance to branch" — we find the real kinetic/regulatory basis and translate it into a defensible weight, then get it approved. Marking which step is RNG-weighted and *why* is itself a teaching moment (the two-layer text, D10, can surface this).

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| PyMOL plugin feature conventions (table stakes T1/T2/T3/T5) | HIGH | Verified against actual plugin source in `Pymol-script-repo/plugins/` (`dynoplot.py`, `emovie.py`). |
| Molecular-game feature landscape (Foldit/Reactome comparators) | HIGH | Live-fetched 2026-08-12 from official/authoritative pages. |
| Educational-game pedagogy patterns (branching/identification/consequences) | MEDIUM | Wikipedia article citing Barab 2009 etc.; article itself flagged for style/citation issues, but the underlying concepts (conceptual play, empathetic embodiment, risk-free experimentation) are well-established in the GBL literature. |
| Specific competitor game feature lists beyond Foldit (e.g., Meta!Blast, Biochem Tetris) | LOW / not asserted | I deliberately did NOT name unverified specific metabolism games to avoid fabrication. The pattern-level claims are grounded; specific-game claims are left for phase-specific research if a deeper competitor analysis is wanted. |
| Complexity & validation-load estimates | MEDIUM | Complexity estimates are relative-judgment heuristics for one dev on this stack; validation-load estimates follow directly from the spec's per-claim constraint and are high-confidence as *relative* rankings. |
| Achievement-as-collection vs leaderboard reasoning | MEDIUM-HIGH | The Foldit comparator (HIGH) confirms leaderboards exist and what they optimize for; the pedagogical argument for collection-over-leaderboard is well-grounded but is ultimately a *design recommendation*, not a measured fact. |

## Gaps to Address

- **Anaerobic framing (D11)** is explicitly an open design question (PROJECT.md Key Decisions): host-condition branch vs separate scenario vs bad-ending trigger. This needs phase-specific storyline + research before the feature is built — flagged for the roadmap.
- **Specific competitor analysis** beyond Foldit/Reactome: if the roadmap wants a deeper "what do existing metabolism teaching games do" scan, that's a separate research task. This document deliberately stayed at the *pattern* level to avoid fabricating specific-game claims.
- **The TCA RNG probability values** (D4) are not specified here — they are a content-research task per pathway step, gated by the per-claim approval. The roadmap should treat "define + approve RNG weights" as a content slice, not an engineering slice.
- **The exact ~20+ cast list** (T6) is not enumerated here — that is a content-research task (which enzymes, which PDB IDs, which resolution), gated by approval. The roadmap should treat cast enumeration as a content slice with its own research flag.
- **Stat/XP v2 model** (A3): "luck that affects host condition" needs a scientifically-grounded source before it can be designed. Flagged as a v2 research prerequisite, not a v1 gap.

## Sources

- `Pymol-script-repo/plugins/dynoplot.py` — modern `pymol.Qt` plugin conventions (HIGH, local source, PyMOL 2.5.0-compatible, ported to PyQt 2024 by Thomas Holder).
- `Pymol-script-repo/plugins/emovie.py` — game-like storyboard plugin: save/load (pickle), scene system, in-context help buttons on every dialog, action-sequence model (HIGH for conventions; legacy Tk — used as the cautionary anti-pattern A8).
- `spec.md` + `.planning/PROJECT.md` — authoritative feature set, ending semantics, edit-routing model, constraints (HIGH, project-defined).
- Reactome, https://reactome.org — fetched live 2026-08-12 (HIGH). Confirms the curated/provenance/citation model for teaching metabolism interactively; v97 released 2026-06-30; 2,883 human pathways, 16,423 reactions.
- Foldit, https://en.wikipedia.org/wiki/Foldit — fetched live 2026-08-12 (HIGH). Confirms tutorials→puzzles→tools→score→leaderboard→citizen-science model; the comparator that justifies Anti-Feature A5 and the scaffolded-tutorial pattern.
- Educational game, https://en.wikipedia.org/wiki/Educational_game — fetched live 2026-08-12 (MEDIUM; article flagged for style/citation issues). Confirms "conceptual play"/"empathetic embodiment" (Barab 2009), "risk-free experimentation with consequences," "awareness of consequentiality" patterns.
