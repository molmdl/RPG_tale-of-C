# Research Summary — RPG: Tale of C

**Project:** RPG: Tale of C — A PyMOL 2.5.0 Respiratory-Pathway RPG Plugin
**Synthesized:** 2026-08-12
**Inputs:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md (4 parallel research passes)
**Overall confidence:** **HIGH** for engineering/architecture/API claims (source-verified against `tmp/pymol-src/`); **MEDIUM-HIGH** for feature landscape (verified comparators); **MEDIUM** for educational pedagogy; **gated** for all scientific content (every claim pending human per-claim approval per spec.md).

---

## Executive Summary

RPG: Tale of C is a **PyMOL 2.5.0 desktop plugin** that teaches cellular respiration as a branching-narrative RPG. The player projects into a C14 atom (one of 3 starting characters: glucose, fatty acid, or alcohol — plus an anaerobic path) and navigates real pathway branch points toward 4 ending tiers (True / Good / Normal / Bad), with RNG-weighted stochastic steps (TCA shuffle) that are **seedable for classroom reproducibility**. The game's pedagogical thesis is *conceptual play + empathetic embodiment + risk-free experimentation with consequences* (Barab 2009 via Wikipedia MEDIUM), and its competitive gap is the **narrative + consequence + identification layer on top of curated, cited PDB content** — neither Reactome (a curated browser, not a game) nor Foldit (a citizen-science optimization game with leaderboards) occupies this space.

**The recommended approach is `stdlib + pymol.Qt + pymol.Qt.utils + numpy + pymol.cmd` — ZERO new dependencies for v1.** Every gameplay requirement (text MC, molecule editing, PDB/PubChem fetch, scene restore, seedable RNG, JSON save/load, achievement board) is covered by what PyMOL 2.5.0 already ships. The standout discovery is `pymol.Qt.utils` (`AsyncFunc`, `MainThreadCaller`, `PopupOnException`, `getMonospaceFont`, `loadUi`) — shipped utilities that remove any need for a third-party async/concurrency library. Physiological-pH protonation is the one genuine gap (PyMOL's `h_add` is valence-only, not pH-aware), but the spec's **lookup-table edit-routing model absorbs it**: hardcode reaction-relevant protonation states as lookup-table entries (human-verified per-claim) instead of vendoring a protonation engine. This keeps the install trivial AND is scientifically safer than an automated pH engine. The architecture is a strict **3-tier testability layering** (pure-Python domain → `pymol.cmd` molecular layer → `pymol.Qt` UI layer) so ~70% of the codebase is unit-testable in WSL on Python 3.6.9, the `pymol.cmd` layer is headless-testable via `run-conda-pymol.bat -cq`, and only the Qt layer is human-verify-only.

**The dominant risks are not engineering — they are process and science.** The single biggest timeline risk is the per-claim human-approval gate (Pitfall 7: hundreds of claims × per-claim review = ~30+ hours of human review at 5 min/claim); batch-approval-by-source is the recommended mitigation (confirm with human upfront). The single biggest science risk is a **spec-level conflict**: the True Ending is defined as "become ATP," but a carbon atom tracing respiration exits as CO2, not ATP — this conflates energy yield with carbon fate and must be resolved by the human *before* True-Ending narrative authoring (Pitfall 4). **[RESOLVED 2026-08-13 via the soul-jump reframing — the hero's electrons ("soul") are harvested into ATP via the ETC after the RNG-weighted TCA path; the carbon body is released as CO2. See PROJECT.md Key Decisions + PITFALLS.md Pitfall 4. Pitfall 9 (C14 decay) remains Pending.]** Two related science-framing decisions (C14 radioactive-decay bad-ending at gameplay timescales — Pitfall 9; anaerobic path framing — 3 options pending) also block their respective content slices. The architecture is built to make these the *only* blockers — engineering can race ahead on placeholder content while the human resolves science framings and approves sources in parallel.

---

## Key Findings

### From STACK.md — the stack is "use what ships"

| Decision | Recommendation | Why | Conf. |
|----------|----------------|-----|-------|
| **GUI toolkit** | `from pymol.Qt import QtCore, QtGui, QtWidgets` (PyQt5-first wrapper) | Spec-mandated modern Qt; `dynoplot.py` is the canonical template; `pymol.Qt` falls back to PySide2/PyQt4 if needed | HIGH |
| **Async / non-freezing GUI** | `pymol.Qt.utils.AsyncFunc` + `MainThreadCaller` + `PopupOnException` | **Shipped with PyMOL** — removes any need for a third-party async lib. Use `AsyncFunc` for bulk PDB download; `cmd.fetch(async_=1)` for non-blocking HTTP | HIGH |
| **Save format** | JSON (stdlib) | Human-readable, diff-friendly, cross-version-safe (unlike pickle), gitignore-friendly (unlike `*.npy`); `.pse` only as optional "export view" | HIGH |
| **RNG** | `random.Random(seed).choices(population, weights=...)` (stdlib) | `random.choices` was added in Python 3.6.0 — exactly the test env. Seedable for classroom reproducibility. No numpy RNG version coupling | HIGH |
| **PDB acquisition** | `cmd.fetch(code, type='pdb'\|'cif', async_=0, path=...)` + bundled small/critical | Built-in host/caching/async/locking; `async_=0` is critical for headless; bundle small + one-time bulk-download prompt for large | HIGH |
| **PubChem small molecules** | `cmd.fetch(str(cid), type='cid', ...)` | Built-in — no `requests`/parser to maintain. CIDs must be strings + per-claim verified | HIGH |
| **Protonation (v1)** | `cmd.fetch(resn, type='cc')` (PDB CCD canonical state) + lookup-table hardcoding + user-adjustable via `h_add`/`h_fill`/`remove` | `h_add` is **valence-only, NOT pH-aware**. Lookup table absorbs the gap — no PROPKA/RDKit needed for v1. Revisit vendoring in v1.5/v2 only if proven insufficient | HIGH |
| **Plugin packaging** | Package dir `c14_tale_of_c/` with `__init_plugin__` + `addmenuitemqt`, zip-installed via Plugin Manager or symlinked to `~/.pymol/startup/` | Multi-module + bundled PDB data → package is the supported shape (single-file is for tiny plugins) | HIGH |

**Critical version rule:** Target **Python 3.6 syntax universally** (WSL test env 3.6.9 + guarantees compatibility with PyMOL's bundled interpreter). **AVOID** (confirmed 3.6.9 `py_compile` failures from a sibling project): walrus `:=`, f-string self-documenting `=`, positional-only `/`, `dataclasses`, `from __future__ import annotations`. Use `typing.NamedTuple`/`namedtuple`, plain classes, `typing.List[...]`. For dict-order-dependent save stability, use `collections.OrderedDict` explicitly (3.6 implementation detail → 3.7 guarantee).

**The key "no vendoring needed for v1" finding:** Every gameplay requirement is met by what PyMOL 2.5.0 already ships. The two-interpreter reality (WSL 3.6.9 tests + Windows PyMOL runtime) is *designed for* by keeping the pure-Python domain tier import-clean of `pymol` — that's the testability boundary.

### From FEATURES.md — table stakes, differentiators, anti-features

**Table Stakes (must-have; missing any = plugin feels broken):**
- T1 Plugin loads via modern `pymol.Qt` + menu entry
- T2 In-game help text + editing pointers + PyMOL wiki links
- T3 Save/load buttons persist game state to file
- T4 Multiple-choice text UI drives the story
- T5 Show specific residue representations as game proceeds (the "you are in PyMOL" payoff)
- T6 Protein cast of ~20+ enzymes with PDB ID + resolution + citation
- T7 Small-molecule substrates as 3D models from PubChem/PDB
- T8 Protonation physiological-pH (or reaction-relevant) by default; user-adjustable

*Table-stakes validation load is dominated by T5/T6/T7/T8 — these are where per-claim approval will spend most cycles.*

**Differentiators (set this game apart):**
- **D1** C14 hero identification + 3-character selection (glucose / fatty acid / alcohol)
- **D2** Branching narrative graph of pathway choice points (DAG, not free text — keeps validation finite)
- **D3** Four ending tiers (True=ATP / Good=storage or amino acid / Normal=CO2 / Bad=lost-released-host-death-decay-cycle-trap); all 4 reachable for all 3 characters
- **D4** **RNG-weighted stochastic steps (TCA cycle shuffle), SEEDABLE for teaching — single most important differentiator for the educator audience** (educator sets seed → every student sees the same fate → discussable). Provide "fixed-seed (demo)" + "random (play)" modes. Probabilities must be scientifically grounded (HIGH validation load).
- **D5** Limited molecule editing: point mutations, substrate edits, protonation changes
- **D6** **Edit routing via lookup table + bad-ending fallback** (settled design — replaces a chemistry-correctness engine; validation is finite and enumerable, unlike an open-ended correctness engine)
- **D7** "Reveal correct 3D model" / restore safety net (keep gameplay smooth after a broken edit)
- **D8** Achievement board (limited unlocks + collection, **deliberately not a leaderboard** — collection rewards exploration of the content space, which is the pedagogical goal)
- **D9** Dramatic cast list (protein name + PDB ID + resolution) in README + in-game + dramatic slogan
- **D10** Two-layer text: dramatic layer (plain-language stakes) + teaching layer (correct terminology, pathway logic)
- **D11** Anaerobic pathway representation (framing TBD — open design question)
- **D12** Hybrid PDB acquisition (bundle small, one-time bulk download for large)

**Anti-Features (explicitly NOT build):**
- A1 Full MD simulation (out of scope; heavy deps; visual reps suffice for teaching pathway *logic*)
- A2 Automated chemistry-correctness engine (replaced by D6 lookup table)
- A3 Stat / XP / leveling (deferred to v2; ATP double-meaning collision)
- A4 Real-time / multiplayer (out of scope; breaks educator reproducibility)
- A5 Scoring leaderboard (Foldit optimizes for citizen-science competition; we optimize for teaching exploration — collection not ranking)
- A6 Non-respiratory pathways (out of scope)
- A7 Mobile / web port (out of scope)
- A8 Legacy `pmgqt` / Tk interface (spec-forbidden)
- A9 Fabricated or unverified science (the hard constraint — non-feature enforced by per-claim checkpoint)

### From ARCHITECTURE.md — the testability-first 3-tier layering

**System overview:** Layered single-process app inside PyMOL's Python interpreter. **Inviolable dependency direction:** Qt UI → Controller → GameEngine → Pure-Python Domain. PyMOL Layer is called *by* the Controller/Engine via a narrow `MolAction` interface, never the reverse. Domain tier imports nothing from `pymol` or `pymol.Qt`.

**Six architectural patterns (the design backbone):**

1. **Testability-first layering** — 3 import tiers with one-way dependency rule. `MolAction` data type carries intent from engine to `pymol_layer`. ~70% of codebase becomes unit-testable in WSL with zero mocking.
2. **Ink-inspired story graph** — borrow [Inkle/ink](https://github.com/inkle/ink)'s *data model* (knots/stitches/diverts/choices/gathers/conditions/alternatives/`SEED_RANDOM`/read-counts/variables), store as **JSON we own**, write ~200 lines of pure-Python interpreter. **No ink runtime dep** (C#/inkpy would need approval). TCA shuffles map to ink's shuffle alternatives; classroom reproducibility maps to `SEED_RANDOM`.
3. **Edit routing via lookup table + bad-ending fallback** — `EditIntent` → `data/edits.json` lookup → known branch + `EditApplier` pre-built variant load, OR bad-ending pool. No chemistry engine.
4. **Citation Registry + per-claim approval gate** — every scientific claim carries `claim_ids`; `data/citations.json` maps each to source metadata + `approval_status`; `tools/check_citations.py` is a pre-ship gate that refuses to build if any referenced claim is missing/unapproved. **This is the no-fabricated-science rule made architectural, not a matter of discipline.**
5. **Hybrid asset management** — `data/assets.json` declares every structure with `class ∈ {bundled, download}`. `AssetManager.resolve(key)` checks cache then either reads bundled file or calls `cmd.fetch(code, type=..., async_=0, path=...)`. One-time bulk-download prompt on first play.
6. **Save/load as game-state JSON (not `.pse`)** — `SaveStore` serializes `GameState` (current node, character, flags, counters, RNG seed + state, visit counts, edit history, protonation pref, achievements). On load, replay the current node's `on_enter` `MolAction`s. Small, inspectable, version-portable.

**Recommended project structure:** `c14/` package with `__init_plugin__` in `c14/__init__.py`; pure-Python domain in `c14/{engine,state,rng,edit_router,citations,assets,persist,achievements}.py` + `c14/story/`; ALL `pymol.cmd` imports confined to `c14/pymol_layer/`; ALL `pymol.Qt` imports confined to `c14/ui/` + `c14/controller.py`. `data/` holds `story/` (one JSON per pathway for diffability), `edits.json`, `citations.json`, `assets.json`, `achievements.json`, `assets/{bundled,downloaded}/`. `tests/` = pure-Python unittests (WSL); `smoke/` = headless cmd-only scripts (run-conda-pymol.bat); `tools/` = check_citations + build_cast_list.

### From PITFALLS.md — the top pitfalls and how to mitigate them

**Critical (must address early or they block the project):**

1. **WSL/Windows path resolution** (P1) — *highest-frequency breakage.* PyMOL resolves paths against cmd.exe cwd, not WSL cwd. Mitigation: resolve every path via `os.path.dirname(__file__)`; pass `path=<absolute>` to `cmd.fetch`; add a startup self-check.
2. **`pymol.Qt.*` untestable from WSL** (P2) — *architectural constraint.* Defines the testability boundary. Mitigation: rigid logic/UI split from first commit; manual GUI test matrix for Qt PRs.
3. **`cmd.create(obj, seg, 1, 1)` is a SILENT NO-OP** (P3) — `source_state=1, target_state=1` = self-copy. Mitigation: `cmd.create(backup, selection)` with default args (copies all states); verify with `cmd.count_atoms` before mutating.
4. **ATP / True-Ending carbon-fate science conflict** (P4) — *the spec's "True = become ATP" conflicts with carbon-fate biochemistry (carbon exits as CO2 via PDH decarboxylation + TCA decarboxylations; ATP carbon comes from ribose/PPP, not respiration).* Conflates energy yield with carbon fate. Mitigation: **surface to human at the first content milestone** with 3 options: (a) redefine True as "energy fully harvested / released as CO2 after TCA" (accurate carbon fate), (b) re-route through PPP so carbon enters ribose → ATP (defensible but expands scope), (c) keep ATP framing but make dramatic layer explicitly about *energy* not *carbon*. **Do NOT silently pick.** **[RESOLVED 2026-08-13 — the human adopted the soul-jump reframing (a variant of option c): the hero's electrons ("soul") are harvested into ATP via the ETC after the RNG-weighted TCA path; the carbon body is released as CO2. See PROJECT.md Key Decisions + PITFALLS.md Pitfall 4.]**
5. **`cmd.fetch` races, defaults to CIF, silently fails offline** (P5) — async-by-default in interactive mode; `type=''` resolves to `cif` (not `pdb` since 1.7.6); network/firewall can block classroom use. Mitigation: always `async_=0, type='pdb'` (or `'cif'` deliberately), `path=<plugin_data_dir>`; manifest-driven bulk download with per-structure `count_atoms` verification + offline fallback that locks only affected characters.
6. **`cmd.alter` without `cmd.sort` corrupts downstream `create`/`byres`** (P6) — *directly breaks the editing feature + restore safety net.* Explicit WARNING in `editing.py:1457-1460`. Silent corruption. Mitigation: wrap every edit in a single `apply_edit(selection, expression)` helper that always `cmd.sort` + `cmd.rebuild`; snapshot before edit with default-args `cmd.create`; restore = `cmd.delete` + `cmd.create` from backup, never in-place reverse.
7. **Per-claim approval is the project's slowest validation mode — timeline-dominating** (P7) — ~400 claims at 5 min/claim = ~33 hours of human review. Mitigation: **batch approval by source** (approve ONE source, all claims traceable to it inherit approval — confirm with human); build the claims registry early; front-load source approval in research phase; decouple code from content (engineering on `UNAPPROVED_PLACEHOLDER` content); estimate approval load explicitly in the roadmap.
8. **Branching complexity explosion** (P8) — 3 chars × 4 endings × branch points × RNG re-entry is unmanageable as linear prose. Mitigation: model the game as a directed graph from day one (JSON data, not embedded prose); author a reachability checker (pure Python, WSL-unit-testable): assert all 4 endings reachable per character; centralize cast descriptions in one registry; cap RNG re-entry (N visits max before forced exit); render graph to Graphviz DOT for review.

**Other significant pitfalls (MEDIUM-HIGH):**
- **P9** C14 radioactive-decay bad-ending is scientifically odd at gameplay timescales (half-life ~5,730 years; decay probability per playthrough ~10⁻⁵ to 10⁻³). Resolve at content-authoring start: drop / time-compression device / reframe as "isotope lottery" teaching moment.
- **P10** Edit-routing lookup table has a long-tail completeness problem — "known edit" is a moving target; sparse coverage feels unfair. Mitigation: define "known edit" categories explicitly; per-enzyme minimum coverage (≥1 catalytic-residue mutation + ≥1 neutral edit + restore path); bad-endings are **explanatory, not punitive** ("this edit isn't modeled — in reality, [brief correct explanation]"); log unknown edits for table-growth backlog; restore button always one click away.

---

## Implications for Roadmap

The architecture's 6-phase build order (P0–P5) is the backbone of the roadmap. The research suggests **collapsing it into 5 execution phases** + 1 pre-content decision milestone that gates Phase 4 content. The critical path is *engineering on placeholder content* racing in parallel with *human source-approval + science-framing decisions*.

### Critical Pre-Content Decisions (human must make BEFORE Phase 4 content authoring)

These four decisions block content authoring and should be a discrete roadmap milestone (or an explicit parallel track started in Phase 0):

1. **ATP / True-Ending carbon-fate reframing** (Pitfall 4) — ~~pick option (a), (b), or (c)~~ **RESOLVED 2026-08-13 via the soul-jump reframing** (electrons-as-soul harvested into ATP via ETC after the RNG-weighted TCA path; carbon body released as CO2; tied to RNG TCA shuffle). No longer blocks True-Ending narrative. See PROJECT.md Key Decisions.
2. **C14-decay timescale framing** (Pitfall 9) — drop / time-compress / reframe as teaching moment. Blocks bad-ending text.
3. **Anaerobic framing** (FEATURES.md D11 / PROJECT.md) — 3 pending options: host-condition branch vs separate scenario vs bad-ending trigger. Blocks the anaerobic content slice.
4. **Batch-by-source vs strict per-claim approval** (Pitfall 7) — process decision that determines whether content authoring is feasible at all. Recommend batch-by-source (approve a source, inherit for all traceable claims) — confirm with human upfront.

### Suggested Build Order (5 phases + 1 pre-content milestone)

| Phase | What it delivers | Rationale | Features from FEATURES.md | Pitfalls it must avoid | Research needed? |
|-------|------------------|-----------|----------------------------|------------------------|-------------------|
| **P0 — Foundations + Citation Gate** | Pure-Python plumbing (rng, state, story/model, citations schema, assets schema, edit_router skeleton) + `tools/check_citations.py` + `data/claims.jsonl` schema + path-self-check helper | Establishes the testability boundary AND the approval gate on day one. No PyMOL, no Qt — fully WSL-testable. Ships the architecture's hardest invariants before any feature code. | T3 (state schema), D2 (story graph model), D4 (RNG seedability primitives) | P1 (paths — bake the absolute-path convention + self-check), P2 (testability boundary), P7 (claims registry) | Skip — well-documented (stdlib + ink model) |
| **P1 — Story Interpreter + Engine Core** | `c14/story/interpreter.py` + `validate.py` + `c14/engine.py` + minimal 2-node story (intro → one choice → ending) + `tests/` (interpreter, RNG determinism, validator, citation gate) | Proves the whole architecture end-to-end in WSL with mocked `MolAction`s. De-risks before any PyMOL/Qt code. Validates the ink-inspired graph + reachability checker on a toy graph. | D2 (narrative graph + reachability), D4 (RNG-weighted branches), D8 (achievement skeleton) | P8 (graph model + reachability checker from day one) | Skip — patterns verified against official ink docs |
| **P2 — PyMOL `cmd` Layer + Smoke Tests** | `c14/pymol_layer/{assets,molops}.py` + `smoke/{assets,molops}_smoke.py` + `api-sanity` smoke + `data/assets.json` (real entries for ~5-6 critical-path enzymes, per-claim gated) | Proves the molecular layer against the real API surface (headless via `run-conda-pymol.bat -cq`). Surfaces the `cmd.create` no-op trap, the `alter`→`sort` trap, and the `fetch` async/CIF defaults *early* while only smoke tests depend on them. | T6 (first slice of cast), T7 (substrates), T12 (hybrid acquisition) | P1 (paths — re-verify under headless), P3 (api-sanity smoke + `file:line` citation rule), P5 (async_=0 + type= + path= + manifest) | Skip — APIs verified line-by-line in STACK.md |
| **P3 — Editing + Protonation + Restore Safety Net** | `c14/pymol_layer/{edits,protonation}.py` + `apply_edit` helper (always `cmd.sort` + `cmd.rebuild`) + `EditApplier.backup/restore` (default-args `cmd.create`) + `data/edits.json` schema + per-enzyme minimum coverage scan | **The highest technical-risk phase** — the `alter`→`sort` silent-corruption trap and the no-op `cmd.create` trap both bite here. Build the helper + tests + backup-restore pattern before any edit flows ship. Protonation as curated variants (no pH engine). | D5 (limited editing), D6 (edit routing lookup), D7 (restore safety net), T8 (protonation) | P3 (no-op `cmd.create`), P6 (`alter`→`sort` — primary risk), P10 (define "known edit" categories + per-enzyme minimum coverage) | **YES — `/gsd-research-phase`**: per-residue protonation variant set per structure (HIGH validation load), edit-table coverage criteria |
| **P4 — Minimal Playable MVP (Qt UI + glucose + True+Bad endings)** | `c14/controller.py` + `c14/ui/{main_window,choice_panel,cast_dialog,help_dialog,save_load,achievement_board}.py` + `c14/__init__.py` (`__init_plugin__` + `addmenuitemqt`) + glucose path (single True + single Bad ending) + ~5-6 critical-path enzymes + bulk-download prompt + README (cast + slogan). **First human-verify milestone.** | First time Qt runs in a real Windows PyMOL session. By this point the engine, molecular layer, and edit/restore are all solid — the UI is a thin adapter. Glucose-only + True+Bad is the minimal loop that proves the full vertical. | T1 (plugin shell), T2 (help), T3 (save/load), T4 (MC UI), T5 (residue reps at stages), D1 (C14 hero + glucose), D3 (True + Bad endings only), D7 (restore), D8 (achievements), D9 (cast list + slogan), D10 (two-layer text — minimal) | P1 (paths — re-verify in real install), P2 (manual GUI test matrix from here on), P5 (bulk-download UX + offline fallback) | **YES — `/gsd-research-phase`**: ATP/True-Ending reframing (must be resolved BEFORE this phase's content), critical-path cast PDB IDs + resolutions + citations, TCA RNG weight values, anaerobic framing (if reached in this slice) |
| **P5 — Content + Character Expansion + Polish** | Fatty acid + alcohol characters, all 4 endings, anaerobic path, full ~20+ cast, edit-table population per enzyme, achievement unlocks, two-layer text polish, playtest-driven table expansion, colorblind-safe palette, glossary/tooltips, full manual test matrix run | **The content marathon.** Dominated by per-claim approval (Pitfall 7). Build the engine+UI once, then expand content. Engineering load is low; validation load is XL. | D1 (fatty acid + alcohol), D3 (Good + Normal endings), D11 (anaerobic), T6 (long tail of cast), D6 (full edit table), D10 (two-layer polish) | P7 (per-claim approval throughput — batch-by-source), P9 (C14-decay framing), P10 (table completeness via session logs + playtest iteration) | **YES — `/gsd-research-phase`**: full ~20+ cast enumeration + citations, fatty acid / alcohol pathway branches + ending fates, anaerobic-path content once framing decided, edit-table population per enzyme |

### Research Flags Summary

| Phase | `/gsd-research-phase` needed? | Why |
|-------|------------------------------|-----|
| P0 Foundations + Citation Gate | No | Stdlib + ink data model — well-documented |
| P1 Story Interpreter + Engine Core | No | Ink patterns verified; architecture owns the interpreter |
| P2 PyMOL `cmd` Layer + Smoke Tests | No | APIs verified line-by-line against `tmp/pymol-src/` in STACK.md |
| P3 Editing + Protonation + Restore | **Yes** | Per-residue protonation variant set per structure; edit-table coverage criteria (HIGH validation load) |
| P4 Minimal Playable MVP | **Yes (heaviest)** | ATP/True-Ending reframing (Pitfall 4 — blocks content), critical-path cast PDB IDs + resolutions + citations, TCA RNG weight values, anaerobic framing |
| P5 Content + Character Expansion | **Yes** | Full ~20+ cast enumeration + citations, fatty acid / alcohol pathway branches + ending fates, full edit-table population per enzyme |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| **Stack** | HIGH | APIs verified line-by-line in `tmp/pymol-src/modules/pymol/`; `pymol.Qt.utils` discovery removes the async-lib question; only the bundled Python minor version in `chemtools-win10` is MEDIUM (unverifiable from WSL — doesn't change the 3.6-syntax recommendation) |
| **Features** | MEDIUM-HIGH | PyMOL plugin conventions + Foldit/Reactome comparators HIGH (live-fetched); educational-game pedagogy MEDIUM (Wikipedia/Barab 2009 — article flagged for style); specific competitor metabolism games beyond Foldit LOW (deliberately not asserted to avoid fabrication) |
| **Architecture** | HIGH | PyMOL plugin/Qt structure source-verified; ink data model verified against official docs; testability split is a direct consequence of AGENTS.md; edit-routing details MEDIUM (design-driven, API surface verified, exact "known edit" set is content — needs per-claim approval) |
| **Pitfalls** | HIGH for PyMOL/Qt/WSL environment + API pitfalls (source-verified); MEDIUM-HIGH for scientific pitfalls (grounded in basic biochem, every claim still needs per-claim human approval); MEDIUM for game-design/educational pitfalls (domain reasoning, less source-grounded) |

### Gaps to Address (couldn't be resolved in research — need attention during planning/execution)

1. **ATP / True-Ending carbon-fate reframing** — ~~science decision the human must make before Phase 4 content~~ **RESOLVED 2026-08-13** via the soul-jump reframing (Pitfall 4). The hero's electrons ("soul") are harvested into ATP via the ETC after the RNG-weighted TCA path; the carbon body is released as CO2. See PROJECT.md Key Decisions.
2. **C14-decay timescale framing** — science decision before bad-ending content (Pitfall 9). Half-life figure itself needs an approved citation.
3. **Anaerobic framing** — 3 options pending (host-condition branch / separate scenario / bad-ending trigger). Architecture supports all three; the choice is content (FEATURES.md D11).
4. **Batch-by-source vs strict per-claim approval** — process decision that determines whether content authoring is feasible at all (Pitfall 7). Recommend batch-by-source; confirm with human.
5. **Exact PDB ID list for the ~20+ cast** — needs pathway-by-pathway research + per-claim approval. Architecture is ready; content is not. Phase 4 + Phase 5 research flags.
6. **TCA RNG probability values** (D4 weights) — content-research task per pathway step, gated by per-claim approval. Treat "define + approve RNG weights" as a content slice, not engineering.
7. **Bundled vs download split per PDB** — needs the PDB list + size measurements. AssetManifest schema ready; populate during Phase 2.
8. **Per-residue protonation variant set per structure** — per-structure content decision. Phase 3 research flag.
9. **Edit-router table contents per enzyme** — curating "known edits" is a per-enzyme content/research task. Phase 3 + Phase 5.
10. **Exact Python minor version in `chemtools-win10`** — confirm in a real Windows session (`import sys; print(sys.version_info)`) during first human-verify checkpoint. Doesn't change the 3.6-syntax recommendation but removes the MEDIUM-uncertainty.
11. **User-writable path for saves/achievements on Windows PyMOL 2.5.0** — verify `cmd.get('user_dotdir')` behavior in scaffolding (Phase 0).
12. **PROPKA / Dimorphite-DL / PDB2PQR license + 3.6-compat** — only if a phase proves the lookup-table protonation model is insufficient. **Not needed for v1.** Flagged for v1.5/v2.
13. **Stat/XP v2 model** ("luck that affects host condition") — needs a scientifically-grounded source before it can be designed. v2 research prerequisite, not a v1 gap.

---

## Sources (aggregated from research files)

### Primary — PyMOL 2.5.0 source (HIGHEST confidence, version-exact)
`tmp/pymol-src/modules/pymol/` (read-only, gitignored):
- `plugins/__init__.py`, `installation.py`, `managergui_qt.py`, `legacysupport.py` — plugin discovery, `__init_plugin__`, `addmenuitemqt`, install paths/zip/package formats, metadata, `get_pmgapp()` may be None in headless
- `importing.py:635,1115-1147,1323-1394` — `cmd.fetch`/`cmd.load` signatures, RCSB/PDBe/PDBj/PubChem/CCD URLs (HTTPS), `async_=0` for sync, CIF default (1.7.6), `fetch_path` default, network/firewall note
- `internal.py:310` — `cmd.download_chem_comp` CCD CIF helper
- `viewing.py:65,281,491,528,568,605,705,1858,2019` — `show`/`show_as`/`hide`/`zoom`/`orient`/`get_view`/`set_view`/`color`/`spectrum`
- `editing.py:800,937,1163,1195,1216,1257,1288,1424-1473,1490-1533` — `remove`/`fuse`/`h_fill`/`h_fix` (unsupported)/`h_add` (**valence-only, not pH**)/`sort` (required after alter)/`replace`/`alter` (sort WARNING at 1457-1460)/`iterate` (Python-callback new in 2.5)
- `creating.py:929,960,1002-1003` — `fragment` (meager amino-acid library)/`create` (**`create(obj,sele,1,1)` is a no-op**)/`copy_properties` unsupported in open-source
- `commanding.py:496` — `delete`
- `exporting.py:782,991,994` — `save`/`get_str` formats (pdb/mol2/sdf/pse/pkl/pkla)
- `querying.py:131,1148` — `get_object_list`/`get_names`
- `wizard/mutagenesis.py:38,47-48,58` — interactive mutagenesis; raises if movie loaded; reads `PYMOL_DATA` for sidechain library; `_rot_type_xref` lists protonation resnames (`HID`/`HIE`/`HIP`/`ASPH`/`GLUH`/`ARGN`/`LYSN`)
- `Qt/__init__.py:26-40` — `pymol.Qt` wrapper: PyQt5 → PySide2 → PyQt4 fallback; exports `QtCore`/`QtGui`/`QtWidgets`; `Signal = pyqtSignal`, `Slot = pyqtSlot`
- `Qt/utils.py:4,98,145,227,247,267,311` — `UpdateLock`/`AsyncFunc`/`MainThreadCaller`/`getSaveFileNameWithExt`/`getMonospaceFont`/`loadUi`/`PopupOnException`

### Reference plugins (Pymol-script-repo/plugins/, MEDIUM-HIGH for conventions)
- `dynoplot.py:21,445` — canonical modern `pymol.Qt` + `__init_plugin__` + `addmenuitemqt` template (ported 2024 by Thomas Holder, plugins-engine author)
- `outline.py:29,311`, `optimize.py:29,53,73`, `show_contacts.py:280,321,331` — modern QDialog/QTabWidget patterns
- `emovie.py` — game-like storyboard plugin; save/load (pickle), scene system, in-context help on every dialog (HIGH for conventions; legacy Tk — cautionary anti-pattern A8)
- `rendering_plugin.py`, `resicolor_plugin.py` — legacy Tk/Pmw anti-references

### Inkle/ink narrative model (HIGH for story-graph design; field reference)
`github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md` — knots/stitches/diverts/choices/gathers/conditions/alternatives (sequence/cycle/shuffle)/tags/`SEED_RANDOM`/read-counts/variables. We borrow the **data model**, not the runtime (no external dep).

### Comparator tools (HIGH, live-fetched 2026-08-12)
- Reactome, https://reactome.org — curated/provenance/citation model for teaching metabolism interactively (v97, 2026-06-30; 2,883 human pathways, 16,423 reactions). Reference for the PDB cast + per-claim approval discipline.
- Foldit, https://en.wikipedia.org/wiki/Foldit — tutorials → puzzles → tools → score → leaderboard → citizen-science model. Justifies Anti-Feature A5 (no leaderboard) and the scaffolded-tutorial pattern (borrow).
- Educational game, https://en.wikipedia.org/wiki/Educational_game — MEDIUM (article flagged for style/citation issues); confirms "conceptual play"/"empathetic embodiment" (Barab 2009), "risk-free experimentation with consequences," "awareness of consequentiality."

### Project context (HIGHEST for constraints)
- `spec.md` — plot, RNG, endings, edit model, citation rule, protonation rule, hybrid asset acquisition, no-install rule, no-fabricated-science rule
- `.planning/PROJECT.md` — confirmed scope, key decisions (edit routing = lookup table + bad-ending fallback; stat/XP deferred; per-claim approval chosen as safest/slowest mode; success measure = all endings reachable for all characters; anaerobic framing pending)
- `AGENTS.md` — WSL/Windows split, `run-conda-pymol.bat -cq` headless pattern, `cmd.create(obj,seg,1,1)` no-op pitfall, verification tiers, no-install / no-new-deps-silently rules

### Cross-session corroboration (MEDIUM)
Sibling project "bioCHEMeleon" tool-output logs — corroboration of 3.6.9 syntax constraints (walrus/f-string=/positional-only `py_compile` failures), WSL/Windows verification tiers, `py_compile`+`unittest`+headless-`run-conda-pymol.bat` pattern. Used only to corroborate AGENTS.md, not as sole source.

### Flagged LOW confidence (needs dedicated research when its phase is planned)
- PROPKA / Dimorphite-DL / PDB2PQR license terms + Python 3.6 compatibility + vendoring footprint — only if a phase proves lookup-table protonation insufficient. Not needed for v1.
- PyMOL 2.5.0 bundled Python version in `chemtools-win10` (MEDIUM; inferred from release era; not directly queryable from WSL).

---

*Synthesis complete for: RPG: Tale of C — PyMOL 2.5.0 Respiratory-Pathway RPG Plugin*
*Synthesized: 2026-08-12*
*Source files: STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md (4 parallel research passes)*
