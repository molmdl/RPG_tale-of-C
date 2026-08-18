# RPG: Tale of C — A PyMOL Respiratory-Pathway RPG

## What This Is

A PyMOL 2.5.0 plugin (PyQt5 via `pymol.Qt`) that turns cellular respiration into a
role-playing game. The player controls a C14 atom — the hero — choosing a starting
"character" (glucose, fatty acid, or alcohol) and guiding it through the respiratory
pathway via text-based multiple choice, limited molecule editing, and visual
representation of real protein structures sourced from the PDB. Branching storylines,
RNG-weighted stochastic steps (e.g. TCA cycle shuffles), and four ending tiers
(True / Good / Normal / Bad) yield many possible fates for the hero. Built for
biochemistry educators and students: dramatic enough to engage, scientifically
rigorous enough to teach.

## Core Value

The player experiences cellular respiration as a story with consequences — every
choice and edit on the C14 hero either advances them toward a destiny (ATP [the hero's electrons harvested into energy via the ETC], storage,
CO2, or catastrophe) or diverts them into a branch, with real PDB proteins as the
cast and scientifically validated chemistry as the plot. The hero is "gifted/blessed"
— a carbon with the special power to edit/restore enzymes — journeying through a sick
host whose enzymes are malfunctioning, attempting to save the host by restoring each
broken enzyme encountered along the pathway.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Plugin loads in PyMOL 2.5.0 via the modern `pymol.Qt` interface (PyQt5); no legacy `pmgqt`/Tk
- [ ] Player can start a new game choosing one of 3 characters: glucose, fatty acid, alcohol
- [ ] Anaerobic pathway is represented in the game structure (design pending research — see Key Decisions)
- [ ] All 4 ending tiers reachable for each character: True (hero's electrons/"soul" harvested into ATP via ETC after the RNG-weighted TCA path — carbon body released as CO2), Good (carbon body retained pre-oxidation — fatty-acid storage / amino acid / etc.), Normal (CO2 released without the full electron-harvest destiny arc), Bad (lost connection / released from host / host death / radioactive decay / cycle-trapped)
- [ ] RNG-weighted stochastic steps for pathways known to shuffle (e.g. TCA cycle) — reproducible-seedable for teaching
- [ ] Text-based multiple-choice gameplay drives the story forward
- [ ] Limited molecule editing: player can make point mutations, substrate edits, and protonation-state changes
- [ ] Edit routing via lookup table: known edits map to defined branches; unknown edits fall through to a bad-ending pool ("lost connection" / "released from host")
- [ ] "Reveal correct 3D model" / "restore" safety net so gameplay stays smooth after edits
- [ ] Specific residue representations are shown as the game proceeds to relevant stages
- [ ] Protein "cast" of ~20+ enzymes sourced from the PDB, each with PDB ID + resolution + citation
- [ ] Small-molecule substrates are 3D models from PubChem or PDB
- [ ] Protonation is physiological-pH or reaction-relevant by default; user-adjustable
- [ ] PDB acquisition is hybrid: small/critical structures bundled with the plugin; large structures fetched via a one-time bulk download prompt before first play
- [ ] Achievement board with a limited set of unlockable achievements and a limited collection of starting points / endings; persisted to a file the user can revisit
- [ ] Save/load buttons persist game progress/state to a file; load restores a saved session
- [ ] README (repo root) and in-game help text include a dramatic cast list (protein name, PDB ID, resolution) and a dramatic slogan (e.g. "featuring high-resolution, real protein models in our cast")
- [ ] In-game help includes molecule-editing pointers (and/or PyMOL wiki links)
- [ ] Every scientific claim and citation (DOIs, PDB IDs, pathway facts) is verified against an approved source and explicitly human-approved via per-claim checkpoint before landing in code/content

### Out of Scope

- **Stat/XP/leveling system** — deferred to v2. The scientifically-sound framing is "luck that affects host condition" rather than energy (since the True ending is the hero's electrons being harvested into ATP, energy can't double as XP). v1 focuses on the already-comprehensive content scope.
- **Real-time / multiplayer modes** — single-player turn-based only
- **Non-respiratory pathways** (e.g. photosynthesis, urea cycle) — out of scope for this game's theme
- **Full molecular-dynamics simulation** — representations are static/visual, not simulated trajectories
- **Automated chemistry-correctness engine for edits** — replaced by the lookup-table + bad-ending-fallback model (see Active requirements)
- **Mobile / web port** — PyMOL desktop plugin only
- **Legacy `pmgqt` / Tk interface** — modern `pymol.Qt` only

## Context

**Source material.** `spec.md` is the authoritative spec (plot, constraints, "do not install / do not make up citations" rules). The repo is in early stage: no plugin code yet, only spec + reference material. Read `spec.md` first for any plot/science question.

**Reference sources (read-only, gitignored / symlinked):**
- `tmp/pymol-src/` — symlink to PyMOL 2.5.0 open-source Python modules. Read API signatures here when a citation behaves differently than expected. Key modules: `creating.py` (create/fuse), `editing.py` (alter/alter_state/iterate/remove/sort), `querying.py` (identify/count_atoms/iterate), `viewing.py` (show/hide), `commanding.py` (delete/fetch), `wizard/`.
- `Pymol-script-repo/` — symlink to 31 3rd-party PyMOL plugins in `plugins/`. Use as idiomatic reference for plugin structure and PyQt conventions (e.g. `plugins/dynoplot.py` shows the modern `from pymol.Qt import QtCore, QtGui, QtWidgets` style).
- `LICENSE_pymol-open-source` — license for the bundled/derived PyMOL source. Keep attribution when borrowing patterns.

**Audience.** Biochemistry educators + students. Text must work on two layers: a dramatic layer (the C14 hero's journey, plain-language stakes) and a teaching layer (correct terminology, pathway logic, editable residues explained). Educators may run it in class, so the RNG should be seedable for reproducible demos.

**Ending semantics (from spec.md, in story-like framing without bare scientific jargon):**
- True ending — the hero's electrons (the narrative "soul") are fully harvested into ATP via the ETC → ATP synthase after completing the RNG-weighted TCA path (destiny fulfilled). The carbon body was released as CO2; the soul lives on as ATP energy. (Soul-jump reframing — resolves Pitfall 4; the C14 is a tracking label, not a fate determinant.)
- Good ending — the carbon body is diverted to a productive fate (fatty-acid storage, amino acid synthesis, or similar) BEFORE oxidation, so the carbon itself is retained (no soul-jump needed)
- Normal ending — the carbon is oxidized to CO2 and released WITHOUT the full electron-harvest / destiny arc (the unremarkable exit)
- Bad ending — failure to reach a destination, RNG traps the hero in a cycle long enough for the host to die, radioactive decay of C14 (Pitfall 9 — framing still pending), or the player breaks an important residue/enzyme and the host cannot survive

**Edit-routing model (settled during questioning).** The "limited edits" feature does NOT require a chemistry-correctness engine. The game holds a curated lookup table of known edits per enzyme/substrate context. A player edit that matches a known entry routes to the corresponding defined branch. A player edit that doesn't match falls through to the bad-ending pool ("lost connection" / "randomly released from host"). This keeps the validation logic tractable and the gameplay smooth.

## Constraints

- **Tech stack**: PyQt5 via `pymol.Qt` + numpy only (what `pymol-open-source` ships). Any other library requires written list + explicit user approval; user installs or agent vendors under `./3rd_party_lib/` (gitignored) with license noted — never `pip install` silently.
- **Environment (WSL/Windows split)**: Dev shell is WSL Ubuntu with `python3.6` (3.6.9) for syntax checks / pure-Python unit tests ONLY. PyMOL 2.5.0 runs in a Windows conda env (`chemtools-win10`), NOT WSL. A WSL agent CANNOT launch the interactive GUI and CANNOT exercise `pymol.Qt.*` at runtime. Headless PyMOL CAN be run from WSL via `C:\src\run-conda-pymol.bat` (pass `-cq` for no-GUI quiet) for pure-`pymol.cmd.*` scripts. Qt/GUI tests remain human-verify checkpoints. `setenv.bat` / `wsl2win_cp.sh` referenced in `spec.md` do NOT exist in this repo — `run-conda-pymol.bat` at `/mnt/c/src/` is the real entry point.
- **Verification**: Pure-Python modules → `python3.6 -m py_compile` + `unittest`/`pytest` if tests exist. Pure-`pymol.cmd.*` scripts → headless via `run-conda-pymol.bat -cq` wrapped in `timeout`. Qt/GUI code → human-verify in a real Windows PyMOL session.
- **No fabricated science**: ALL claims and citations (DOIs, PDB IDs, pathway facts) MUST be verified against a source and explicitly approved by the human via per-claim checkpoint before use. Seek approval before using any source.
- **Protonation**: physiological pH or reaction-relevant by default, or user-adjustable.
- **Code quality**: efficient, traceable, clean, safe; repo structured. UI simple and user-friendly with clear in-game explanation.
- **Git hygiene**: `Pymol-script-repo`, `tmp`, `3rd_party_lib/**`, `*.env`, `*.npy`/`*.npz`, and secrets are git-ignored — do not commit them.
- **Plugin conventions**: match `Pymol-script-repo/plugins/` style (`from pymol.Qt import QtCore, QtGui, QtWidgets`). Never reach into PyMOL internals when a `cmd.` API exists — verify against `tmp/pymol-src/modules/pymol/` first.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| v1 ships 3 characters (glucose, fatty acid, alcohol) + anaerobic path | User confirmed scope; covers the main respiratory entry points. Host organism = mammal/human (lactic fermentation: pyruvate → lactate via LDH; carbon retained → Good). LDH enters the cast in Phase 9. | — Pending (host = mammal/human, resolved 2026-08-15) |
| All 4 ending tiers reachable for every character (even single-character v1) | Branching + multiple endings are core to the game, not a v2 feature | RESOLVED (2026-08-15): re-worded to 'Aerobically, 1 True + several Normal/Good + many Bad endings are reachable per character. Anaerobically, the True ending (soul-jump via ETC) is NOT reachable (no O2 → no ETC); the reachable endings are a subset (Normal/Good/Bad only) — and are character-specific: glucose reaches the 3-ending fermentation branch (lactic=Good, ethanolic=Normal, crisis=Bad) while FA + alcohol reach only the Bad-ending trigger (no viable anaerobic catabolic path).' (per the anaerobic ETC/O2 finding + the user-confirmed ending-count distribution documented in Plan 01 / PROJECT.md Key Decisions + the framing-d character-specific anaerobic reachability the user confirmed). |
| RNG-weighted stochastic steps (e.g. TCA shuffle) are v1 | Spec-mandated; user confirmed even single-character v1 needs RNG | — Pending |
| Anaerobic path framing (5 research options: host-condition branch / separate scenario / bad-ending trigger / choice-for-glucose+bad-for-FA-ALC / anaerobic-respiration host) | RESOLVED 2026-08-15 via option (d) CHOICE-FOR-GLUCOSE + BAD-FOR-FA/ALC. Tradeoff (educator-fit vs scope vs story-graph-disruption): best teaching artifact (fermentation taught as a real reachable glucose fate with distinct ending semantics), reuses roster (adds an anaerobic branch to the glucose graph, no 4th character), scientifically honest. Glucose gets a 3-ending anaerobic branch (lactic=Good/retained, ethanolic=Normal/CO2, crisis=Bad); FA + alcohol get the Bad-ending trigger (O2-depletion energy crisis). Invariant preserved aerobically for all 3 chars. See 05-RESEARCH-anaerobic.md §Framing Options. | RESOLVED via option (d) CHOICE-FOR-GLUCOSE + BAD-FOR-FA/ALC — glucose gets a 3-ending anaerobic branch (lactic=Good/retained, ethanolic=Normal/CO2, crisis=Bad); FA + alcohol get the Bad-ending trigger (O2-depletion energy crisis). Best pedagogical fit (fermentation taught as a real reachable glucose fate). Reuses the glucose graph (adds an anaerobic branch, no 4th character). Invariant preserved aerobically for all 3 chars. (2026-08-15) |
| Edit routing = lookup table + bad-ending fallback (not a chemistry engine) | Player-suggested simplification: unknown edits → "lost connection" / "released from host" bad endings; known edits → defined branches. Removes the hardest validation problem. | — Pending |
| Stat/XP/leveling deferred to v2 | The True ending is the hero's electrons ("soul") harvested into ATP, so energy can't double as the XP currency; "luck that affects host condition" is the candidate model but needs scientific grounding. v1 already comprehensive. | — Pending |
| PDB acquisition = hybrid (bundle small/critical, one-time bulk download for large) | Balances plugin install size against not hitting the network on every encounter | — Pending |
| Audience = educators + students | Drives two-layer text (dramatic + teaching) and seedable RNG for classroom reproducibility | — Pending |
| Source approval = per-claim checkpoint | User chose the safest of three options; slowest but eliminates fabricated-science risk. Refined in row 106: per-claim checkpoint retained for HIGH-STAKES claims (RNG-weights, protonation-defaults, carbon-fate, contested); routine claims source-inherited (hybrid option c) with a warning flag for leisure spot-check. | Refined by row 106 (hybrid workflow, 2026-08-15) |
| Success measure for v1 = all endings reachable for all characters | User confirmed the most ambitious of three options | — Pending |
| ATP/True-Ending carbon-fate reframing | RESOLVED 2026-08-13 via the **soul-jump reframing**: the hero's *electrons* (the narrative "soul") are harvested into ATP via the ETC → ATP synthase after the RNG-weighted TCA path, while the carbon body is released as CO2. This preserves the dramatic True=ATP arc with scientific accuracy (a labeled carbon ≠ ATP carbon; electrons → proton pumping → ATP synthesis). Tied to the RNG TCA shuffle (the soul reaches ATP only via the RNG-weighted path). Good = carbon retained pre-oxidation; Normal = CO2 without full harvest; Bad = failure/cycle-trap/host-death/critical-residue-break. C14 is a tracking label, not a fate determinant. See PITFALLS.md Pitfall 4. (The spec's original "become ATP" line is annotated in-place in spec.md; the actual ETC/ATP-synthase chemistry claims still require per-claim citation approval in Phase 7+.) **Narrative metaphor (decided 2026-08-15; option b sense-moves-with-electron, REFRAMED as metamorphosis):** the hero is the carbon; rather than 'dying' as CO2, the carbon undergoes a METAMORPHOSIS — like a caterpillar turning into a butterfly, the carbon body is shed as CO2 (the chrysalis stage) while the narrative POV/sense follows the electrons onward (legacy/influence framing — 'my electrons power the cell'). The hero transforms, not dies. The 'soul' is the narrative attention that moves with the electrons, not a physical identity. | — Resolved (soul-jump; metaphor = metamorphosis) |
| C14-decay timescale framing | RESOLVED via DROP — radioactive decay is DROPPED as a bad-ending trigger. The cycle-trap-until-host-death trigger (spec.md line 18: 'RNG stay in a cycle long enough for the host organism passed') is the sole timescale-based bad-ending. No radioactive-decay citation (NUBASE2020) needed. No C14-TIME-01 claim needed. Spec deviation (spec.md line 18 lists 'radioactive decay' — dropped, documented here). Phase 5.1 reachability checker must confirm ≥1 Bad-ending trigger remains reachable per character without decay. Rationale: User indicated dropping decay in favor of cycle-trap-until-host-death (scientifically cleaner — no decay-timescale problem). Confirmed 2026-08-15. | — Resolved via DROP (2026-08-15) |
| Batch-by-source vs strict per-claim approval | Research (Pitfall 7) flagged per-claim approval as the timeline-dominating risk (~33h for full content). Options surfaced: (a) strict per-claim, (b) batch-by-source, (c) hybrid, (d) per-source-record. RESOLVED 2026-08-15 via option (c) HYBRID — honors BOTH the per-claim safety guarantee on load-bearing claims AND Pitfall 7's timeline risk. Sources approved up front (batch); high-stakes claims get individual per-claim review; routine claims get source-inherited fast-track + a warning flag for leisure spot-check. | RESOLVED via option (c) HYBRID — sources approved up front (batch), high-stakes claims individually reviewed. HIGH-STAKES taxonomy (individual per-claim review): RNG-weights, protonation-defaults, carbon-fate, contested. ROUTINE (source-inherited fast-track): enzyme-catalyzes-reaction-X, enzyme name/EC/cofactor, PDB existence/resolution/citation, pathway ordering. ENHANCEMENT (user-requested): routine/source-inherited claims are FLAGGED with `review_tier: "routine"` + `inherits_source_approval: true` in the registry so the human can spot-check them at leisure ('when i have time') — this is a VISIBILITY/FLAG mechanism, NOT a blocking gate; the Phase 1 gate still passes routine claims via the source's approval. The human can filter routine claims by `review_tier=routine` or `inherits_source_approval=true` to review them at any time. Phase 1 gate (tools/check_citations.py) UNCHANGED — predicate approval_status == 'approved' preserved (strict equality, c14/citations.py:109, Pitfall 6 preserved); the loader (c14/citations.py:87-97) ignores the extended fields (source_id, review_tier, inherits_source_approval, review_notes, claim_text) so they load cleanly with zero loader change; data/sources.json is a separate file the gate never reads (verified). Throughput estimate: glucose first batch (c) ~1.5h; full content (c) ~6-8h. (2026-08-15) |
| Ending distribution: 1 True, several Normal/Good, many Bad | User confirmed asymmetric ending distribution — 1 True (soul-jump/legacy fulfilled via metamorphosis), several Normal+Good (different carbon fates), many Bad (largest pool — cycle-trap → host death, critical-residue-break, lost-connection, released-from-host, etc.). Replaces the flat 'all 4 reachable' with '1 True + several Normal/Good + many Bad reachable per character'. Affects Phase 5.1 graph topology (1 True node, several Normal/Good nodes, many Bad nodes per character). | — Resolved (user-confirmed 2026-08-15) |
| Anaerobic / True-ending ETC-O2 finding | The True ending (soul-jump via ETC) is biochemically unreachable anaerobically (no O2 → no ETC → no ATP synthase); verified against LibreTexts Electron Transport Chain + Biological Oxidation pages (fetched live 2026-08-15). This is settled chemistry, not a framing choice. See 05-RESEARCH-anaerobic.md. | Acknowledged (informs the invariant re-wording + framing-d anaerobic reachability) |
| Narrative motivation: hero as "gifted/blessed" restorer of a sick host | RESOLVED 2026-08-19 (user decision). The hero is a carbon with a special power beyond an ordinary carbon: the ability to edit/restore enzymes. The host organism is sick — enzymes are malfunctioning (mutated/diseased). The hero's journey through the respiratory pathway is motivated not only by personal destiny (the ending tiers) but by the mission to save the host by restoring the broken enzymes encountered at edit-allowed nodes. This REFRAMES the existing edit mechanic (Phase 4 EditRouter) as a restoration attempt: (1) the enzyme is shown in its DISEASED state via `on_enter` pre-edit MolActions (load PDB → applyEdit point_mutation to the disease allele); (2) the player's edit is the hero's restoration attempt — correct reverse-mutation matches `edits.json` known-edit signature → known-edit branch node ("you restored it!"); wrong edit → bad-ending pool ("you made it worse"); break a critical residue → `bad.critical_residue_break`. NO skeleton structure change (Phase 5.1 topology, RNG, endings, reachability all unchanged) — this is a CONTENT-LAYER narrative frame implemented in Phase 7 via: (a) `text_dramatic`/`text_teaching` (the restoration framing + disease description), (b) `edits.json` signatures (the reverse-mutation = the known "correct fix"), (c) `on_enter` pre-edit MolActions (load wild-type PDB → apply disease mutation → player sees the broken enzyme). Each disease mutation requires a real source (what mutation? what disease?) — additional per-claim approval work in Phase 7. Scope: not ALL ~6 edit-allowed nodes need a restoration subplot; 1-2 key enzymes (e.g. PFK, aconitase — both already have approved claims) can carry the restoration arc while the rest stay "exploration" editing. The `apply_edit` helper (Phase 4) already supports the on_enter pre-edit mechanism (load → alter → sort → rebuild). Geometry caveat: `cmd.alter` changes residue identity but does not repack side chains or relax geometry — the "mutated" structure has correct sequence but approximate 3D coordinates; `text_teaching` should note this is a simplified representation. See spec.md Description NOTE (2026-08-19). | Resolved (2026-08-19) — narrative motivation decided; content-layer implementation in Phase 7; no skeleton replan needed |

---
*Last updated: 2026-08-19 — Narrative motivation decided: hero as "gifted/blessed" restorer of a sick host (reframes editing as restoration; content-layer, no skeleton replan). Prior (2026-08-15): Source-approval workflow resolved via option (c) HYBRID + routine-claim warning flag; high-stakes taxonomy confirmed; see Key Decisions. Anaerobic framing resolved via option (d) + invariant re-worded to aerobic-scoped (i) + host = mammal/human; Pitfall 9 (C14-decay) resolved via DROP; soul-jump metaphor decided (metamorphosis/sense-moves-with-electron); ending distribution confirmed; see Key Decisions*
