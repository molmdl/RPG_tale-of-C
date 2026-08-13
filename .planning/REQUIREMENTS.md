# Requirements: RPG: Tale of C

**Defined:** 2026-08-12
**Core Value:** The player experiences cellular respiration as a story with consequences — every choice and edit on the C14 hero either advances them toward a destiny (ATP, storage, CO2, or catastrophe) or diverts them into a branch, with real PDB proteins as the cast and scientifically validated chemistry as the plot.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases. Cross-checked against spec.md §4 (gameplay elements) — all covered except stat/XP (deferred v2).

### Plugin Foundation

- [ ] **PLGN-01**: Plugin loads in PyMOL 2.5.0 via the modern `pymol.Qt` interface (PyQt5) with a menu entry, using the `__init_plugin__` + `addmenuitemqt` pattern (no legacy `pmgqt`/Tk)
- [ ] **PLGN-02**: Plugin is installable via Plugin Manager (package dir → .zip → startup/) and bundles small/critical PDB structures within the package
- [x] **PLGN-03**: Plugin code targets Python 3.6 syntax universally (WSL test env = 3.6.9; pure-Python modules stay import-clean of `pymol`/`PyQt5` for unit testability) ✓ Phase 1

### Characters & Starting Points

- [ ] **CHAR-01**: Player can start a new game choosing one of 3 characters: glucose, fatty acid, or alcohol
- [ ] **CHAR-02**: The C14 hero is identified/highlighted in the loaded 3D structure at game start so the player can see "their" atom

### Pathway & Story

- [ ] **STORY-01**: A branching narrative graph (DAG of nodes) drives the story forward via text-based multiple choice at each pathway branch point
- [ ] **STORY-02**: All 4 ending tiers are reachable for each character: True (ATP), Good (fatty-acid storage / amino acid / etc.), Normal (CO2), Bad (lost connection / released from host / host death / cycle-trapped / radioactive decay)
- [ ] **STORY-03**: RNG-weighted stochastic steps are implemented for pathways known to shuffle (e.g. TCA cycle), with scientifically grounded (not invented) weights approved via per-claim checkpoint
- [ ] **STORY-04**: RNG is seedable for classroom reproducibility: a fixed-seed (demo) mode and a random (play) mode are both available
- [ ] **STORY-05**: Anaerobic pathway is represented in the game structure (framing pending research — see PROJECT.md Key Decisions)
- [ ] **STORY-06**: Every story node carries two-layer text: a dramatic layer (C14 hero's journey, plain-language stakes) and a teaching layer (correct terminology, pathway logic, editable residues explained)
- [ ] **STORY-07**: Choice points map to real pathway branch points (e.g. pyruvate → acetyl-CoA vs → lactate), not invented branches

### Molecule Editing

- [ ] **EDIT-01**: Player can make point mutations (swap one residue in an enzyme's active site)
- [ ] **EDIT-02**: Player can make substrate edits (add/remove a group on the small molecule)
- [ ] **EDIT-03**: Player can change protonation state of catalytic residues / substrate
- [ ] **EDIT-04**: Edit routing uses a lookup table: known edits map to defined branches; unknown edits fall through to the bad-ending pool ("lost connection" / "released from host")
- [ ] **EDIT-05**: "Reveal correct 3D model" / restore safety net lets the player recover a pre-edit snapshot without restarting (keeps gameplay smooth)

### Molecular Cast & Representation

- [ ] **CAST-01**: Protein "cast" of ~20+ enzymes sourced from the PDB, each with PDB ID + resolution + citation, verified via per-claim checkpoint
- [ ] **CAST-02**: Small-molecule substrates (the C14 hero + intermediates) are 3D models from PubChem (via `cmd.fetch type='cid'/'sid'`) or PDB (via `cmd.fetch type='pdb'`)
- [ ] **CAST-03**: Protonation defaults to physiological pH or reaction-relevant states; user-adjustable (curated variants via `cmd.alter` resn + targeted H add/remove, since `h_add` is valence-only not pH-aware)
- [ ] **CAST-04**: Large PDB structures are fetched via a one-time bulk download prompt before first play (hybrid bundle-small + bulk-download-large model)
- [ ] **CAST-05**: Specific residue representations are shown as the game proceeds to relevant stages (using `cmd.show`/`cmd.hide`/`cmd.select` scene pattern)

### Persistence & Achievements

- [ ] **SAVE-01**: Save button persists game progress/state to a JSON file (human-readable, diff-friendly)
- [ ] **SAVE-02**: Load button restores a saved session (game state JSON; molecular scene reconstructed by replaying current node's MolActions)
- [ ] **ACH-01**: Achievement board with a limited set of unlockable achievements (collection-based: endings found, characters tried, branches discovered — not a ranked leaderboard) and a limited collection of starting points/endings
- [ ] **ACH-02**: Achievement board persists to a file so the user can revisit it across sessions; cap deferred to content/UI phase (depends on story and UI — see PROJECT.md Key Decisions)

### Documentation & Help

- [ ] **DOC-01**: Repo-root README includes a dramatic cast list (protein name, PDB ID, resolution) and a dramatic slogan (e.g. "featuring high-resolution, real protein models in our cast")
- [ ] **DOC-02**: In-game help text includes the dramatic cast list + slogan
- [ ] **DOC-03**: In-game help includes molecule-editing pointers and/or PyMOL wiki links
- [x] **DOC-04**: Initial minimal README.md with "Under Development" banner, description, and TBD placeholder sections (Installation Instructions, References, etc.) ✓ Phase 1

### Scientific Integrity

- [ ] **CITE-01**: Every scientific claim and citation (DOIs, PDB IDs, pathway facts, RNG weights, protonation defaults) is verified against an approved source and explicitly human-approved via per-claim checkpoint before landing in code/content
- [x] **CITE-02**: A citation registry maps each claim_id to source + approval_status; a pre-ship check blocks release on any `pending`/missing claim (no-fabricated-science rule enforced architecturally, not by discipline) ✓ Phase 1

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Stat / XP / Leveling

- **STAT-01**: Minimal stat/XP growing feature that unlocks additional options, with a scientifically correct model (candidate: "luck that affects host condition" — needs scientific grounding before design can begin)

### Non-Respiratory Pathways

- **PATH-01**: Additional pathways (photosynthesis, urea cycle, etc.) — theme expansion for v2+

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time / multiplayer modes | Single-player turn-based only; multiplayer complicates educator reproducibility (seedable RNG) and the PyMOL single-session runtime |
| Non-respiratory pathways (v1) | Scope discipline; keeps cast and validation load bounded |
| Full molecular dynamics simulation | Heavy deps beyond pymol-open-source (e.g. OpenMM) violate "no new deps silently"; visual representations sufficient to teach pathway *logic* |
| Automated chemistry-correctness engine for edits | Replaced by lookup-table + bad-ending-fallback model (EDIT-04); a real engine needs RDKit + curated rules beyond allowed stack and unbounded validation load |
| Scoring leaderboard (ranked) | Collection-based achievement board (ACH-01) is the right pedagogical choice for a teaching game; leaderboards optimize for optimization, discouraging the slow exploration teaching needs |
| Mobile / web port | PyMOL desktop plugin only; porting = re-implementing the molecular viewer |
| Legacy `pmgqt` / Tk interface | Modern `pymol.Qt` (PyQt5) only; match `dynoplot.py` import style |
| Fabricated or unverified science | Hard constraint from spec.md; per-claim checkpoint (CITE-01) — the temptation to fill content gaps with plausible-sounding chemistry must be resisted |

## Traceability

Which phases cover which requirements. Updated during roadmap creation (2026-08-12). See `.planning/ROADMAP.md` for phase goals + success criteria.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PLGN-01 | Phase 6 — Qt UI + MVP | Pending |
| PLGN-02 | Phase 6 — Qt UI + MVP | Pending |
| PLGN-03 | Phase 1 — Foundations & Citation Gate | Complete |
| CHAR-01 | Phase 8 — Fatty Acid + Alcohol Characters | Pending |
| CHAR-02 | Phase 6 — Qt UI + MVP | Pending |
| STORY-01 | Phase 2 — Story Engine Core | Pending |
| STORY-02 | Phase 8 — Fatty Acid + Alcohol Characters | Pending |
| STORY-03 | Phase 7 — All Glucose Endings | Pending |
| STORY-04 | Phase 2 — Story Engine Core | Pending |
| STORY-05 | Phase 9 — Anaerobic + Full Cast | Pending |
| STORY-06 | Phase 7 — All Glucose Endings | Pending |
| STORY-07 | Phase 7 — All Glucose Endings | Pending |
| EDIT-01 | Phase 4 — Editing + Protonation + Restore | Pending |
| EDIT-02 | Phase 4 — Editing + Protonation + Restore | Pending |
| EDIT-03 | Phase 4 — Editing + Protonation + Restore | Pending |
| EDIT-04 | Phase 4 — Editing + Protonation + Restore | Pending |
| EDIT-05 | Phase 4 — Editing + Protonation + Restore | Pending |
| CAST-01 | Phase 9 — Anaerobic + Full Cast | Pending |
| CAST-02 | Phase 3 — PyMOL cmd Layer | Pending |
| CAST-03 | Phase 4 — Editing + Protonation + Restore | Pending |
| CAST-04 | Phase 6 — Qt UI + MVP | Pending |
| CAST-05 | Phase 6 — Qt UI + MVP | Pending |
| SAVE-01 | Phase 2 — Story Engine Core | Pending |
| SAVE-02 | Phase 2 — Story Engine Core | Pending |
| ACH-01 | Phase 6 — Qt UI + MVP | Pending |
| ACH-02 | Phase 6 — Qt UI + MVP | Pending |
| DOC-01 | Phase 9 — Anaerobic + Full Cast | Pending |
| DOC-02 | Phase 9 — Anaerobic + Full Cast | Pending |
| DOC-03 | Phase 6 — Qt UI + MVP | Pending |
| DOC-04 | Phase 1 — Foundations & Citation Gate | Complete |
| CITE-01 | Phase 5 — Pre-Content Key Decisions (parallel) | Pending |
| CITE-02 | Phase 1 — Foundations & Citation Gate | Complete |

**Coverage:**
- v1 requirements: 32 total (previously stated as 34 — corrected: PATH-01 and STAT-01 are v2, not v1)
- Mapped to phases: 32 ✓
- Unmapped: 0 ✓
- No orphans, no duplicates ✓

**Per-phase load:**
- Phase 1: 3 reqs (PLGN-03, CITE-02, DOC-04)
- Phase 2: 4 reqs (STORY-01, STORY-04, SAVE-01, SAVE-02)
- Phase 3: 1 req (CAST-02)
- Phase 4: 6 reqs (EDIT-01..05, CAST-03)
- Phase 5: 1 req (CITE-01) — parallel track
- Phase 5.1: 0 reqs (INSERTED design phase — story graph skeleton + MC-choice/edit-node integration contracts; enables STORY-01/03/06/07 + EDIT-04 downstream)
- Phase 5.2: 0 reqs (INSERTED design phase — hero highlight + scene templates + cast-reveal convention; enables CHAR-02/CAST-05 downstream)
- Phase 6: 8 reqs (PLGN-01, PLGN-02, CHAR-02, CAST-04, CAST-05, DOC-03, ACH-01, ACH-02)
- Phase 7: 3 reqs (STORY-03, STORY-06, STORY-07)
- Phase 8: 2 reqs (CHAR-01, STORY-02)
- Phase 9: 4 reqs (STORY-05, CAST-01, DOC-01, DOC-02)
- Phase 10: 0 reqs (polish phase completing prior content/engineering requirements; documentation finalization moved to Phase 11)
- Phase 11: 0 reqs (documentation finalization/verification phase updating + verifying DOC-01, DOC-02 against shipped reality, per the Phase 10 0-requirement precedent)
- Total mapped: 32 ✓ (across 14 phase rows; Phases 5.1, 5.2, 10, and 11 own 0 requirements — design/polish/finalization phases, per the established precedent)

**Design-phase note (Phases 5.1 + 5.2):** These INSERTED phases own no requirements but produce reviewable design artifacts that Phases 6–9 implement/extend. They were added in revision (2026-08-12) to make the story graph topology + gameplay-integration contracts (5.1) and the 3D visual language (5.2) explicit before the overloaded first-Qt phase (Phase 6), directly addressing user concerns about story design, the MC-vs-editing distinction, editing↔story integration, and cast/hero representation.

**Finalization-phase note (Phase 11):** Phase 11 owns no requirements but verifies + updates DOC-01, DOC-02 (created in Phase 9) against the final shipped game content. It was added in revision (2026-08-12) to separate documentation finalization + verification from Phase 10's content polish, making the docs-accuracy release gate an explicit phase rather than implicit in the polish phase. It is the LAST release gate before ship.

---
*Requirements defined: 2026-08-12*
*Last updated: 2026-08-13 after Phase 1 completion (PLGN-03, CITE-02, DOC-04 marked Complete — 3/32 v1 requirements delivered)*
