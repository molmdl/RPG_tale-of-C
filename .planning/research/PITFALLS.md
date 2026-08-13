# Pitfalls Research

**Domain:** PyMOL 2.5.0 plugin RPG teaching cellular respiration (C14 hero through respiratory pathway)
**Researched:** 2026-08-12
**Confidence:** HIGH for PyMOL/Qt/WSL environment + API pitfalls (verified against `tmp/pymol-src/` source); MEDIUM-HIGH for scientific-accuracy pitfalls (grounded in basic biochem, but every claim still needs per-claim human approval per spec.md); MEDIUM for game-design / educational pitfalls (domain reasoning, less source-grounded).

> **Source-grounding note.** Where a pitfall cites a PyMOL API behavior, the citation is to the bundled PyMOL 2.5.0 open-source modules at `tmp/pymol-src/modules/pymol/` (read-only, gitignored). File:line references are given so a later phase can re-verify. No external scientific claim below is asserted as fact — every such claim is flagged as needing the project's per-claim human-approval checkpoint before it lands in code/content.

---

## Critical Pitfalls

### Pitfall 1: WSL/Windows path resolution silently breaks PyMOL `cmd.*` calls

**Severity:** CRITICAL — highest-frequency breakage source per AGENTS.md ("the single most common way to break things"); affects every `cmd.load`/`cmd.fetch`/data-file access in the plugin.

**What goes wrong:**
A script developed in WSL uses a relative path (e.g. `cmd.load("data/cast/1a00.pdb")`) or `cmd.fetch(...)` (which writes to `fetch_path`, default `.`). When run headlessly via `run-conda-pymol.bat`, PyMOL resolves the path against the **cmd.exe working directory**, not the WSL cwd. The file is "not found" (or worse, lands in an unexpected Windows directory) even though `ls` in WSL shows it exists. `\\wsl$\...` paths sometimes work but are flaky; `/mnt/c/...` paths are reliable.

**Why it happens:**
PyMOL is a Windows process launched through `cmd.exe`. Its filesystem view is the Windows cwd. The WSL cwd and the cmd.exe cwd are not the same thing unless you explicitly `cd` into a `/mnt/c/...` path before invoking `cmd.exe`. `cmd.fetch` writes downloaded files to `get('fetch_path') or '.'` (`importing.py:1379-1381`) — i.e. the Windows cwd, silently.

**How to avoid:**
- Before any headless invocation, `cd` into the staged Windows-facing path (a `/mnt/c/...` directory). AGENTS.md documents this but it's easy to forget per-script.
- In plugin code, **never use relative paths** for data files. Resolve every path via `os.path.dirname(__file__)` joined to the data dir, and prefer absolute paths.
- For `cmd.fetch`, explicitly pass `path=<absolute_windows_or_mount_path>` and `async_=0` (see Pitfall 5).
- Add a startup self-check: on plugin load, assert that a known bundled data file is readable via the same path-resolution code the game will use at runtime. Fail loud with a dialog if not.

**Warning signs:**
- "Unable to load file" or empty objects after `cmd.load` / `cmd.fetch` in headless runs.
- Downloaded PDBs appearing in `C:\Windows\System32\` or the WSL home dir instead of the plugin's data folder.
- Tests pass on the developer's machine (because they happened to `cd` correctly) but fail in a fresh shell.

**Phase to address:** Scaffolding — bake absolute-path resolution + a path-self-check into the plugin loader on day one. Every later phase inherits the convention.

---

### Pitfall 2: `pymol.Qt.*` cannot be exercised from WSL — the entire GUI is untestable in CI

**Severity:** CRITICAL — architectural constraint that determines the whole project's testability boundary; mishandled, it means the most user-visible code ships unverified.

**What goes wrong:**
The dev shell is WSL Ubuntu; PyMOL 2.5.0 runs in a Windows conda env. Qt needs a real display. A WSL agent (and any automated test) **cannot** import `pymol.Qt`, instantiate a `QtWidgets.QDialog`, or run any GUI code path. Headless PyMOL (`-cq`) only exercises `pymol.cmd.*`. The result: the most user-visible part of the game (the RPG UI, dialogs, achievement board, help text) is verified only by a human in a real Windows PyMOL session. Regressions accumulate invisibly.

**Why it happens:**
Qt binds to a windowing system. WSL has no display server attached to the Windows PyMOL process. There is no workaround that lets WSL drive Qt in the Windows env. This is a hard environmental constraint documented in AGENTS.md.

**How to avoid:**
- **Separate logic from UI rigidly.** All game-state, pathway-graph, RNG, edit-routing, achievement, and save/load logic must live in pure-Python modules with **zero** `pymol.Qt` imports. These ARE unit-testable in WSL (`python3.6 -m unittest`). The Qt layer becomes a thin view that calls into the logic layer.
- **Define a GUI contract** (methods/return types the logic layer exposes) and unit-test the logic layer against it. The Qt layer's job is only to render results and forward clicks.
- **Maintain a human-test matrix** (a checklist of GUI flows: start game, choose character, make an edit, trigger bad-ending, save, load, open achievement board). Run it before every merge that touches Qt files. Track it as a manual test artifact in the repo.
- **Headless smoke for `cmd.*` paths only.** Don't let a passing headless smoke lull you into thinking the GUI works.

**Warning signs:**
- A PR "passes all tests" but touches `.py` files that import `pymol.Qt` — those lines were never executed by any test.
- Qt import statements appear inside logic-layer modules.
- "It works on my machine" from the one human who ran it in Windows PyMOL.

**Phase to address:** Scaffolding — the logic/UI split must exist from the first commit. UI phase enforces the manual test matrix. Polish phase runs the full matrix.

---

### Pitfall 3: `cmd.create(obj, selection, 1, 1)` is a SILENT NO-OP (and other API surprises)

**Severity:** HIGH — silent failures with no error/warning; bounded to specific API calls but each instance can block a feature for hours if undiagnosed.

**What goes wrong:**
Code written from memory or older examples calls `cmd.create(obj, seg, 1, 1)` expecting "copy state 1 into a new object." It does nothing visible. The signature is actually `create(name, selection, source_state=0, target_state=0, ...)` (`creating.py:960-962`). Passing `1, 1` means `source_state=1, target_state=1` — copy state 1 **into state 1 of the same object**, a self-copy. No error, no warning, no result. AGENTS.md flags this as a real discovery from a prior spike.

This is one instance of a broader class: **PyMOL 2.5.0 API behaves differently than citations/examples suggest**, and the only authoritative reference is the bundled source at `tmp/pymol-src/modules/pymol/`.

**Why it happens:**
- PyMOL's API has decades of accreted defaults; many tutorials predate default changes.
- The function returns `DEFAULT_ERROR` / `DEFAULT_SUCCESS` codes that are easy to ignore.
- Open-source PyMOL differs from incentive PyMOL in some features (`copy_properties` prints "not supported in Open-Source PyMOL", `creating.py:1002-1003`).

**How to avoid:**
- **Rule: never trust a PyMOL API call from memory.** When introducing any new `cmd.*` call, read its signature + docstring in `tmp/pymol-src/modules/pymol/` first. Cite the file:line in a comment.
- Wrap critical `cmd.*` calls and check return values / `cmd.count_atoms` afterwards to confirm the effect.
- Maintain a small `api-sanity` headless smoke that exercises each `cmd.*` call the game uses, with assertions on the post-condition. Run it via `run-conda-pymol.bat -cq` whenever touching the cmd-interfacing layer.
- Known traps to pre-empt (all verified in source):
  - `cmd.create` self-copy no-op (above).
  - `cmd.alter` **requires `cmd.sort` afterward** or subsequent `create`/`byres` operations are confounded (explicit WARNING, `editing.py:1457-1460`). This is critical for the editing feature.
  - `cmd.fetch` defaults to **CIF**, not PDB (changed in 1.7.6; `importing.py:1346`). Code that parses PDB-specific records will silently get CIF.
  - `cmd.fetch` is **async by default in interactive mode** (`importing.py:1382-1383`); pass `async_=0` to block. Fetch-then-operate races otherwise.
  - Mutagenesis wizard **raises if a movie is loaded** (`mutagenesis.py:47-48`) and **reads `os.environ['PYMOL_DATA']`** for its sidechain library (`mutagenesis.py:58`) — a `KeyError` in non-standard installs / some headless configs.
  - `cmd.iterate` with a Python callback is **new in 2.5** (`editing.py:1512-1515`); older `stored.`-dict patterns still work but the callback form is cleaner for C14 atom tracking.

**Warning signs:**
- A `cmd.*` call returns successfully but the object is empty / unchanged.
- "It worked in the tutorial" but not here.
- Side-effects (sort, rebuild) missing after alter operations.

**Phase to address:** Scaffolding (set the "read the source first" convention + api-sanity smoke). Editing phase (the `alter`→`sort` trap bites hardest here). Content-authoring phase (fetch/CIF parsing).

---

### Pitfall 4: The spec's "true ending = become ATP" conflicts with carbon-fate biochemistry

> **✅ RESOLVED (2026-08-13) via the soul-jump reframing.** The human adopted: the hero's *electrons* (the narrative "soul") are harvested into ATP via the ETC → ATP synthase after the RNG-weighted TCA path, while the carbon body is released as CO2 (via pyruvate dehydrogenase + TCA decarboxylations). This preserves the dramatic True=ATP arc with scientific accuracy — a labeled carbon never enters oxidative phosphorylation or becomes ATP carbon; only its electrons continue. Tied to the RNG TCA shuffle (the soul reaches ATP only via the RNG-weighted path). Ending semantics: True = soul (electrons) harvested into ATP; Good = carbon body retained pre-oxidation (fatty-acid/amino-acid); Normal = CO2 without full electron harvest; Bad = failure/cycle-trap/host-death/critical-residue-break. C14 is treated as a tracking label only, not a fate determinant. See PROJECT.md Key Decisions. The original pitfall text below is retained for provenance. **Pitfall 9 (C14 decay timescale) remains Pending and is NOT resolved here.**

**Severity:** CRITICAL — design-level science conflict that blocks True-Ending authoring; the project's "no fabricated science" rule and "spec is authoritative" rule collide here, so it must be resolved by the human early.

**What goes wrong:**
The hero is a **C14 atom** (a carbon). The spec defines the True Ending as "end up as ATP." But in cellular respiration, the **carbon from glucose exits as CO2** (via pyruvate dehydrogenase decarboxylation and TCA cycle decarboxylations). ATP is an energy currency — its carbon comes from ribose (via pentose phosphate pathway, not respiration) and the adenine base. A carbon atom tracing respiration does **not** become the carbon skeleton of ATP. Teaching "the carbon hero becomes ATP" is a scientifically inaccurate conflation of **energy yield** with **carbon fate**.

This is a design-level tension between the dramatic layer (a satisfying destiny) and the teaching layer (correct carbon tracking). It will surface at the first per-claim approval checkpoint for the True Ending narrative.

**Why it happens:**
- The dramatic framing ("become ATP = destiny fulfilled") is pedagogically attractive but conflates two distinct concepts.
- Respiration pedagogy often emphasizes "ATP is made" without distinguishing carbon fate from energy fate.
- The spec is explicitly "authoritative" (AGENTS.md), so an agent may be reluctant to question it — but spec.md ALSO mandates "no fabricated science" and per-claim approval, which is exactly the mechanism that should catch this.

**How to avoid:**
- **Surface this to the human at the first content milestone**, before authoring the True Ending narrative. Frame it as: "The spec's True Ending = ATP conflicts with carbon-fate biochemistry (carbon exits as CO2). Options: (a) redefine True Ending as 'energy fully harvested / released as CO2 after completing TCA' — scientifically accurate carbon fate; (b) re-route True Ending through PPP so the carbon enters ribose → ATP — scientifically defensible but expands scope beyond respiration; (c) keep ATP framing but make the dramatic layer explicitly about *energy* not *carbon*. Seek approval."
- Do NOT silently pick one. The per-claim approval process exists for exactly this; use it early.
- Apply the same scrutiny to every ending: Good (fatty-acid storage — carbon fate is defensible), Normal (CO2 — defensible), Bad (radioactive decay — see Pitfall 9, timing issue). Only ATP-as-carbon-destiny is the acute conflict.
- For ALL carbon-fate claims, prepare to cite a primary biochem source (the project mandates source approval before use; do not assume a source — propose candidates and get approval).

**Warning signs:**
- A reviewer/educator asks "wait, how does the carbon get INTO ATP?" and there's no answer.
- The True Ending narrative reads "your carbon becomes the energy of ATP" — a tell that energy and carbon are being conflated.
- TCA-cycle decarboxylation steps are glossed in the story (the CO2 exits are where the carbon actually leaves).

**Phase to address:** Content-authoring — must be resolved at the **start** of ending-narrative authoring, not after. Flag in research as a science-reconciliation blocker. The per-claim approval checkpoint is the mitigation; this pitfall is "be ready for it and resolve it early, not late."

---

### Pitfall 5: `cmd.fetch` races, defaults to CIF, and silently fails offline — PDB acquisition is fragile

**Severity:** HIGH — core feature (PDB cast) with three independent failure modes; mitigable with explicit args + manifest, but a classroom-network failure is a launch-blocking incident.

**What goes wrong:**
The spec calls for a hybrid PDB acquisition model (bundle small/critical, one-time bulk download for large). Three independent `fetch` footguns combine into one fragile feature:
1. **Async-by-default** (`importing.py:1382-1383`): in interactive mode `async_ = not quiet` → background download. Code that fetches then immediately operates on the object races — the object isn't loaded yet.
2. **CIF default** (`importing.py:1346`): `type=''` resolves to `cif`, not `pdb`. PDB-record-parsing assumptions break silently.
3. **Network dependency** (`importing.py:1367-1368`, docstring): "Fetch requires a direct connection to the internet and thus may not work behind certain types of network firewalls." A classroom with restricted networking sees the bulk-download step fail with no recovery.

**Why it happens:**
- The default changed (`pdb` → `cif` in 1.7.6) and many examples predate it.
- Async is convenient for interactive use but wrong for scripted game-flow.
- The bulk-download feature assumes network reliability the plugin can't guarantee.

**How to avoid:**
- **Always pass `async_=0` and `type='pdb'` (or `'cif'` deliberately)** in plugin fetch calls. Never rely on defaults.
- **Manifest-driven bundling.** Maintain a `cast_manifest.json` (PDB ID → size category → bundled-or-download). Bundle the small/critical structures in `data/cast/`. For large ones, the "one-time bulk download" step reads the manifest, fetches each with `async_=0`, and **verifies** `cmd.count_atoms > 0` per structure before marking it acquired.
- **Offline fallback.** If the bulk download fails partway, the game must degrade gracefully: lock the encounters that need missing structures, show a clear "download incomplete, these characters unavailable" message, and let the player retry. Never a hard crash.
- **Path control.** Pass `path=<plugin_data_dir>` explicitly to `cmd.fetch` so downloads land in the right place regardless of cwd (see Pitfall 1).
- **Cache validation.** After download, record each PDB's resolution from the file header (for the dramatic cast list) — don't re-fetch for the citation.

**Warning signs:**
- Intermittent "object not found" right after a fetch.
- CIF files where PDB was expected (parsing code throws or silently misreads).
- A classroom reports the plugin "doesn't work" on their network.

**Phase to address:** Scaffolding (define manifest + data dir layout). Content-authoring (populate manifest, bundle small structures). UI (download prompt + retry/fallback UX).

---

### Pitfall 6: `cmd.alter` without `cmd.sort` corrupts downstream `create`/`byres` — directly threatens the editing feature

**Severity:** CRITICAL — directly breaks the spec-mandated "limited molecule editing" + "restore correct 3D model" safety net; corruption is silent and hits exactly when the player needs the restore.

**What goes wrong:**
The "limited molecule editing" feature lets the player mutate residues / edit substrates. The natural implementation uses `cmd.alter` (change `resn`, `resi`, `chain`, etc.) or the mutagenesis wizard. The `alter` docstring carries an explicit WARNING (`editing.py:1457-1460`): *"You should always issue a 'sort' command on an object after modifying any property which might affect canonical atom ordering (names, chains, etc.). Failure to do so will confound subsequent 'create' and 'byres' operations."* Skip the `sort` and subsequent selections (`byres`, `create`, the "reveal correct 3D model" restore) return wrong atoms or silently no-op. The "restore correct model" safety net breaks exactly when the player needs it most.

**Why it happens:**
- The warning is in the docstring, not enforced by the API.
- The corruption is silent — no exception, just wrong results downstream.
- It's easy to forget in the heat of implementing an edit handler.

**How to avoid:**
- **Wrap every edit in a helper** `apply_edit(selection, expression)` that always calls `cmd.sort(object)` after `cmd.alter(...)` and `cmd.rebuild()` if representations need updating. Make the helper the only sanctioned way to alter.
- **Unit-test the helper** headlessly: alter a residue, sort, then `byres` select and assert the expected atoms are returned.
- **Snapshot before edit.** Before any player edit, `cmd.create(obj + "_backup", obj)` (with `source_state=0, target_state=0` to copy all states correctly — see Pitfall 3 on the no-op trap). The "restore correct 3D model" button reloads from this backup. Never try to reverse an edit in-place.
- **Prefer the mutagenesis wizard for residue substitution** (it handles sidechain replacement, bump-checking, caps) — but note it can't run with a movie loaded (`mutagenesis.py:47-48`) and needs `PYMOL_DATA` set (`mutagenesis.py:58`). Validate the env supports it before relying on it.

**Warning signs:**
- After an edit, "reveal correct model" shows the wrong residues or an empty selection.
- `byres` selections return unexpected atoms post-edit.
- Edits appear to work but the C14-tracking selection (`elem C and ...`) drifts.

**Phase to address:** Editing — this is the editing feature's #1 technical risk. Address on day one of the editing phase with the `apply_edit` helper + tests + backup-snapshot pattern.

---

### Pitfall 7: Per-claim scientific approval is the project's slowest validation mode — throughput will dominate timeline

**Severity:** CRITICAL — timeline-dominating process constraint chosen by the user (PROJECT.md Key Decisions); not a code bug but the single biggest schedule risk. Hundreds of claims × per-claim review.

**What goes wrong:**
The spec + PROJECT.md mandate: every scientific claim and citation (DOIs, PDB IDs, pathway facts) must be verified against an approved source AND explicitly human-approved **per claim** before landing. Scope: 3 characters + anaerobic = 4 pathway tracks × ~20+ proteins × multiple branch points × 4 endings × dramatic + teaching text layers. This is **hundreds** of approval checkpoints. Throughput is bounded by human review speed, not agent speed. The project will appear to "stall" not because of code difficulty but because of approval queue depth.

**Why it happens:**
- The user explicitly chose per-claim approval as the safest of three options (PROJECT.md Key Decisions). It eliminates fabricated-science risk but is the slowest mode.
- Content authoring and approval are coupled: an agent can't draft a branch and move on, because the draft is blocked on approval of its claims.
- There's no batch-approval mechanism defined — each claim is a separate checkpoint.

**How to avoid:**
- **Batch claims by source, not by branch.** Get ONE approved source (e.g. a specific LibreTexts chapter, a specific PDB entry) approved up front, then all claims traceable to that source inherit approval. This is still per-claim but amortizes the source-approval cost. Confirm with the human that this is acceptable.
- **Build a claims registry** early: a structured file (e.g. `data/claims.jsonl`) listing every scientific claim with `{claim, source, source_id, status: pending|approved|rejected, approved_by, approved_date}`. The game refuses to ship content whose claims aren't `approved`. This makes the approval queue visible and trackable.
- **Front-load source approval in research/content-authoring phase.** Before authoring any branch narrative, get the source set approved. Then authoring becomes "draft text that cites approved sources" rather than "draft text that waits on approval."
- **Decouple code from content.** The plugin skeleton, edit-routing engine, RNG, save/load, achievement board can all be built and tested with **placeholder content** (clearly marked `UNAPPROVED_PLACEHOLDER`). Don't block engineering on content approval.
- **Estimate approval load explicitly** in the roadmap. If 4 tracks × 20 proteins × ~5 claims each = 400 claims, at even 5 min/claim that's 33 hours of human review. Plan for it.

**Warning signs:**
- Engineering phases finish fast but content phases drag.
- The claims queue grows faster than it drains.
- An agent, blocked on approval, fabricates a "plausible" claim to keep moving — exactly what the process exists to prevent. Watch for this.

**Phase to address:** Scaffolding (claims registry). Content-authoring (front-load source approval, batch by source). Every content-bearing phase thereafter.

---

### Pitfall 8: Branching-complexity explosion — 3 chars × 4 endings × branch points × RNG is unmanageable without a graph model

**Severity:** HIGH — "all 4 endings reachable for all characters" is the stated v1 success measure (PROJECT.md); without a graph model + reachability checker, it's unverifiable. Cheap if done early, near-rewrite if done late.

**What goes wrong:**
The scope (3 characters + anaerobic, all 4 endings reachable per character, RNG-weighted stochastic steps like TCA shuffles, edit-routing branches) yields a combinatorial narrative space. If content is authored as linear prose per character, branch interactions and RNG re-entry points multiply into an unreadable, untestable, inconsistent tangle. The same NPC protein gets described differently in different branches; an ending becomes unreachable because a branch point was missed; RNG re-rolls create cycles the author didn't intend.

**Why it happens:**
- "All 4 endings reachable for every character" sounds additive but is multiplicative in content.
- RNG-weighted steps (TCA shuffle) mean the same node is visited multiple times with different state — a graph problem, not a tree problem.
- Without an explicit data structure, the author holds the graph in their head and it drifts.

**How to avoid:**
- **Model the game as a directed graph from day one.** Nodes = (character, pathway-state, RNG-state-relevant) game states. Edges = choices / RNG transitions / edit-routing. Store as data (JSON or a Python dict), not as embedded prose. Prose lives on edges ("when transitioning A→B, show this text").
- **Author a reachability checker** (pure Python, unit-testable in WSL): for each character, assert all 4 endings are reachable from the start node. Run it on every content change. This makes "all endings reachable" a verifiable invariant, not a hope.
- **Centralize NPC/protein descriptions** in one cast registry. Every branch references the cast entry; the cast entry has one canonical description. No per-branch re-description.
- **Cap RNG re-entry.** A shuffle node can be visited N times max before forced exit; otherwise the player can cycle indefinitely (the spec's "host dies from cycle-trap" bad ending exists, but the cap should be deterministic, not reliant on the player quitting).
- **Visualize the graph** (render to Graphviz DOT) as a dev artifact. Inconsistencies (orphan nodes, dead ends, unreachable endings) become visible.

**Warning signs:**
- An ending that "should be reachable" isn't, and nobody can explain why.
- The same enzyme is described three different ways across branches.
- RNG steps sometimes loop forever.
- Content files grow linearly but the mental model grows exponentially.

**Phase to address:** Scaffolding (graph data structure + reachability checker + cast registry). Content-authoring (author against the graph). Editing (edit-routing extends the graph).

---

### Pitfall 9: C14 radioactive-decay bad ending is scientifically odd at gameplay timescales

**Severity:** MEDIUM — localized to one bad-ending framing; scientifically fixable with a reframing or time-compression device, but an educator will notice if ignored.

**What goes wrong:**
The spec lists "radioactive decay" as a bad-ending trigger. C14's half-life is ~5,730 years. The probability of a C14 atom decaying during a single organism's lifetime (hours to years) is essentially zero (~10⁻⁵ to 10⁻³). Presenting decay as a live gameplay risk during a respiration playthrough is scientifically misleading about decay rates. An educator reviewing the cast will flag it.

**Why it happens:**
- The dramatic framing ("the hero decays away") is evocative but ignores timescale.
- C14 was chosen as the hero (tracking isotope), which makes decay salient — but the very reason C14 is useful for tracking (long half-life) is the reason it won't decay during the game.

**How to avoid:**
- **Resolve this at content-authoring start.** Options to propose to the human: (a) drop radioactive decay as a bad-ending trigger within a single playthrough; (b) keep it but add a dramatic framing device that compresses time ("eons pass..."); (c) reframe it as a rare "isotope lottery" outcome with a stated probability, used for teaching decay rates rather than as a live threat. Get approval.
- **Do not assert a specific decay probability without an approved source.** The half-life figure itself needs an approved citation.
- If kept, ensure the teaching layer (not just the drama layer) is accurate: "C14 decays slowly — over thousands of years — so during one respiration cycle decay is essentially impossible; we include it as a dramatic device." This turns the pitfall into a teaching moment.

**Warning signs:**
- The bad-ending pool lists decay alongside "host dies" as if equally likely.
- An educator reviewer asks "how long is this playthrough supposed to take?"
- The narrative implies decay happens in real-time.

**Phase to address:** Content-authoring — resolve framing before writing bad-ending text.

---

### Pitfall 10: Edit-routing lookup table has a long-tail completeness problem

**Severity:** HIGH — the table IS the game's correctness model (no chemistry engine, per PROJECT.md); sparse coverage makes the game feel unfair, which directly undermines the educational goal.

**What goes wrong:**
The settled design (PROJECT.md Key Decisions): player edits route via a lookup table; known edits → defined branches; unknown edits → bad-ending pool ("lost connection" / "released from host"). The trap: **"known edit" is a moving target.** The table must enumerate every edit the designers consider "meaningful" per enzyme/substrate context. Edge cases (edit a residue that's on the path but not in the table; edit a residue that IS in the table but in a different protonation state; edit a substrate atom that's the C14 itself) all fall through to bad-ending. Players who make a "reasonable" edit and get a bad-ending feel punished, not taught.

**Why it happens:**
- Without a chemistry engine (explicitly out of scope), the table is the entire correctness model. Its coverage IS the game's perceived fairness.
- Edge cases are discovered only through playtesting, which is late.
- "What counts as known" is a design judgment, not a derived property.

**How to avoid:**
- **Define "known edit" categories explicitly** up front: (a) catalytic-residue mutations (per enzyme), (b) substrate functional-group edits (per substrate), (c) protonation-state changes (per residue). Each category has a documented table-completeness criterion.
- **Per-enzyme minimum coverage.** Every enzyme in the cast must have at least: one catalytic-residue mutation (→ bad ending with explanation), one neutral edit (→ story continues), and the "restore" path. No enzyme ships with an empty table.
- **Bad endings are explanatory, not punitive.** An unknown edit routes to bad-ending **with a teaching-layer note**: "this edit isn't one the game models — in reality, [brief correct explanation]. Restore to continue." This converts a fallthrough into a teaching moment and reduces perceived unfairness. (The teaching-layer text still needs per-claim approval.)
- **Log unknown edits.** Track every fallthrough in a session log. Post-launch, the most common unknown edits become candidates for table expansion. This turns the long tail into an iterate-able backlog.
- **The "restore correct 3D model" safety net must always be one click away** after any edit (spec requirement). The player never gets stuck.

**Warning signs:**
- Playtesters say "I edited X and got a bad ending, that's not fair."
- The bad-ending pool is the most common ending in testing (table too sparse).
- No session log of unknown edits → no way to prioritize table growth.

**Phase to address:** Editing (define categories + per-enzyme minimum coverage + explanatory bad-ending template). Content-authoring (populate the table per enzyme). Polish (playtest-driven table expansion).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Embedding narrative prose inline in Python view code | Quick to draft a scene | Content changes require code edits + re-test; translators can't touch it; branching changes become code refactors | **Never** — separate content (data) from code (logic/UI) from day one |
| Hardcoding PDB IDs as strings in game logic | Fast to wire one encounter | Cast changes require code edits; can't diff against the manifest; resolution citations drift from the actual file | **Never** — single `cast_manifest.json` is the source of truth |
| Skipping `cmd.sort` after a one-off `cmd.alter` | Saves a line | Silent downstream corruption (Pitfall 6); hard to trace | **Never** — use the `apply_edit` helper |
| Using `pickle` for save files / achievement persistence | Trivial to serialize arbitrary objects | Security risk (arbitrary code execution on load); brittle across PyMOL/Python version changes; not human-readable | **Never** — use JSON (stdlib, no new dep); for PyMOL session state use `cmd.save` (.pse) or a manifest of PDB IDs + view settings |
| `cmd.fetch` with default args (async, CIF) | Less typing | Races, wrong format, silent failures (Pitfall 5) | **Never in plugin code** — always `async_=0`, explicit `type=`, explicit `path=` |
| Relative paths for data files | Works in the dev's cwd | Breaks on any other cwd (Pitfall 1) | **Never** — resolve via `__file__` |
| Testing only the `cmd.*` path headlessly and calling the feature "done" | Fast CI signal | GUI regressions ship (Pitfall 2) | Only acceptable for logic-layer modules; GUI flows require the manual test matrix |
| Authoring endings without a reachability checker | Faster initial content writing | Unreachable endings discovered late; rework | **Never** — build the checker before authoring content |
| Letting RNG state live only in memory | Simpler game loop | Demos aren't reproducible; save/load can't restore an exact game; "seedable for classrooms" requirement unmet | **Never** — RNG seed + state are part of the save blob |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| PyMOL plugin loader | Defining `__init__(self, pmgapp)` (legacy) and assuming it's called; or assuming `pmgapp` is never None | Modern entry point is `__init_plugin__(pmgapp)` (`plugins/__init__.py:321`); `pmgapp` can be None in headless/non-GUI contexts (`legacysupport.py:26-31`) — handle None gracefully. Also support `__init__` as fallback for older loaders. |
| PyMOL plugin metadata | Omitting the header comment block; missing `Version` / `Citation-Required` | Plugin manager parses `# Key: Value` lines at file start (`plugins/__init__.py:193-210`). Include `# Version:`, `# Citation-Required:`, reStructuredText docstring. |
| `cmd.fetch` (RCSB/PDBe/PDBj/PubChem) | Relying on sync behavior; not handling partial failures in bulk download | Pass `async_=0`, explicit `type=`, explicit `path=`. For bulk: loop with per-structure `count_atoms` verification + retry + offline fallback (Pitfall 5). |
| Mutagenesis wizard | Calling it when a movie is loaded; assuming `PYMOL_DATA` is set | Guard: `if cmd.get_movie_length() > 0: raise` is in the wizard itself (`mutagenesis.py:47-48`) — clear movies first. Check `os.environ.get('PYMOL_DATA')` before relying on sidechain library; fall back to a manual alter-based mutation if absent. |
| Headless PyMOL via `run-conda-pymol.bat` | Forgetting to `cd` to a `/mnt/c/...` path first; not wrapping in `timeout` | Always `cd` into a Windows-readable `/mnt/c/...` dir; wrap in `timeout 90 ...`; tail output; check exit code (0=clean, nonzero=crash). Per AGENTS.md. |
| `pymol.Qt` import | Importing `pymol.Qt` at module top-level of a logic-layer file (makes it un-importable in WSL tests) | Import `pymol.Qt` **only** inside UI-layer modules. Logic layer imports only `pymol.cmd` (and even that, lazily/behind a seam for unit tests). |
| Save-file format (PyMOL session + game state) | Mixing PyMOL object state and game state into one blob; or saving them inconsistently | Save game state as JSON (logic layer) + a list of PDB IDs / object names to reload + view settings. On load, re-fetch/re-load structures then re-apply view. Don't try to serialize live PyMOL objects into JSON. |
| Achievement persistence | Writing to a file in the plugin dir (may be read-only on install) | Write to a user-writable location: `os.path.join(cmd.get('user_dotdir', ...), 'c14_achievements.json')` or similar. Confirm the right path on Windows PyMOL 2.5.0. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `cmd.alter` on large proteins | UI freeze after an edit ("several seconds per thousand atoms altered", `editing.py:1451-1452`) | Alter only the target selection (narrow selection string), not `all`. Show a "working..." modal. | Any protein > ~2000 atoms (most of the respiratory chain) |
| Synchronous `cmd.fetch` blocking the GUI during bulk download | UI frozen for minutes on first play | Run the bulk download in a background thread (`threading` or Qt worker); show a progress bar; the GUI must stay responsive enough to cancel. Note: `cmd.*` calls from a non-main thread need care with PyMOL's lock — prefer a Qt-signaled worker that calls `cmd.fetch` on the main thread via signal/slot. | 20+ structures, any sizeable fraction large |
| Re-fetching PDBs on every encounter | Network latency per scene; offline failure mid-game | Fetch once, cache to `data/cast/`, load from disk thereafter. Manifest tracks what's cached. | Always (don't hit network during gameplay) |
| Full PyMOL scene rebuild after every edit | Sluggish "restore correct model" | Snapshot backup object (Pitfall 6); restore = `cmd.delete` + `cmd.load` from backup, not a rebuild. | Any large structure |
| Loading all 20+ cast structures at startup | Long plugin load; high memory | Load on demand per encounter; `cmd.delete` when leaving a scene (after snapshotting game-relevant state). | Always — lazy-load per encounter |
| Unbounded RNG cycle (TCA shuffle) | Player stuck in a cycle; "host dies" bad ending triggers unexpectedly | Cap re-entry count (Pitfall 8); after N visits, force-exit to the next pathway step. | Whenever RNG weight keeps re-entering the same node |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Using `pickle` for save files or achievement persistence | Arbitrary code execution when a malicious save file is loaded (a crafted pickle can instantiate any class) | Use JSON only. PyMOL session state goes through `cmd.save`/`cmd.load` (.pse, PyMOL's own format) or a manifest — never pickle. |
| Loading untrusted PDB/CIF files from arbitrary paths | Malformed files could exploit parser bugs; user-shared "save files" that reference arbitrary structure paths | Only load structures named in the approved cast manifest or fetched from the official RCSB/PDBe/PDBj URLs (`importing.py:1116-1145`). Treat user-supplied save files as untrusted JSON: validate structure references against the manifest before loading. |
| `cmd.fetch` over the network without TLS verification awareness | MitM could substitute a malicious structure file | PyMOL's fetch URLs are HTTPS (`importing.py:1116+`). Don't override to HTTP. Don't add `verify=False`-style overrides anywhere. |
| Storing achievement/save data world-readable | Multi-user machine: another user reads or clobbers progress | Use the user dotdir (per-user); set restrictive file permissions on write (`os.path.join(cmd.get('user_dotdir'), ...)`, `chmod 600` equivalent). |
| Vendoring a 3rd-party lib under `3rd_party_lib/` without reading its license | License violation; copyleft contamination of the plugin | Read + record the license in `3rd_party_lib/<lib>/LICENSE` (AGENTS.md requires this). Get user approval before vendoring. Note whether setup needs a linux env or can stay WSL-calls-cmd. |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Color-only residue representation (PyMOL default) | Colorblind students can't distinguish residues; "showing specific representation of residue as the game proceeds" (spec req) fails a subset of learners | Pair color with labels (`cmd.label`) and/or patterns; offer a colorblind-safe palette toggle in settings. |
| Text MCQ assumes biochem vocabulary (TCA, acetyl-CoA, decarboxylation) | Novices bounce; educators spend class time pre-teaching terms | In-game glossary / hover-tooltips on jargon; the teaching layer defines the term on first use. Dramatic layer uses plain language. |
| Bad-ending with no explanation | Player feels punished for a reasonable edit; teaching moment lost | Every bad-ending has a teaching-layer note explaining (a) what the edit did in reality, (b) why the game routed here. (Pitfall 10.) |
| Edit feature with no discoverable "restore" | Player edits, breaks the scene, can't recover, quits | "Reveal correct 3D model" / "restore" button is always visible during edit-enabled scenes, with a keyboard shortcut. Spec requires this — make it prominent, not buried. |
| Bulk-download prompt with no progress or retry | First-play user hits "download", waits, fails, gives up | Progress bar + cancel + retry; clear messaging about which structures are needed; offline fallback that locks only affected characters (Pitfall 5). |
| Dramatic cast list (PDB ID + resolution) buried in README only | Educators running in-class don't see it; "featuring high-resolution real protein models" slogan unseen | Show the cast list + slogan in-game (spec req: "in-game help text should include a dramatic cast"). Not just README. |
| RNG that visibly "re-rolls" on every action | Breaks immersion; feels arbitrary | RNG steps are narrated ("the cycle shuffles you again..."); deterministic seed is invisible to students, only educators set it. |
| Save/load that doesn't restore the exact RNG state | "Reproducible demos" requirement (educator use case) breaks; reloaded game diverges from original playthrough | RNG seed + current RNG state are part of the save blob; load restores both. Document the seed field for educators. |

## "Looks Done But Isn't" Checklist

- [ ] **Plugin loads:** Often missing verification that `__init_plugin__(pmgapp)` is actually called by the Plugin Manager, and that it survives a PyMOL restart (autoload). Verify: install via Plugin Manager, restart PyMOL, confirm menu item appears without manual re-load. (Human-verify — Qt.)
- [ ] **All 4 endings reachable:** Often missing per-character reachability verification. Verify: run the reachability checker (Pitfall 8) for each of the 4 tracks (glucose, fatty acid, alcohol, anaerobic) × 4 endings = 16 assertions. Don't assume reachability from "I played it once."
- [ ] **RNG is seedable:** Often missing save/load of the RNG state. Verify: set seed, play 5 steps, save; load, play same 5 steps, confirm identical outcomes. Then change seed, confirm divergence.
- [ ] **PDB cast is cited correctly:** Often missing verification that resolution numbers come from the actual PDB/CIF file header, not memory/approximation. Verify: parse `REMARK 2 RESOLUTION.` (PDB) or the equivalent CIF field from each bundled/downloaded file; assert it matches the cast list.
- [ ] **Protonation is physiological:** Often missing verification that HETATM hydrogens, not just protein backbone, are at the right state. Verify: for each cast structure, document the protonation method used (`cmd.h_add`? fetched with hydrogens? force-field assignment?) and get the method approved per-claim.
- [ ] **Edit table has per-enzyme minimum coverage:** Often missing the "at least one catalytic-residue edit + one neutral edit + restore path per enzyme" check (Pitfall 10). Verify: automated scan of the edit table asserts every cast enzyme has ≥1 known-edit entry.
- [ ] **"Restore correct 3D model" works after ANY edit:** Often missing the backup-snapshot-before-edit pattern (Pitfall 6). Verify: for each edit type, apply edit, hit restore, assert atom count + residue identity match pre-edit.
- [ ] **Save/load round-trips a full mid-game session:** Often missing verification that loaded state reproduces not just story position but loaded PyMOL objects, view, RNG, achievements. Verify: automated round-trip test on the logic layer + manual Qt test for the full session.
- [ ] **Headless smoke passes ≠ GUI works:** Often missing the recognition that headless only covers `cmd.*` (Pitfall 2). Verify: maintain the manual GUI test matrix; don't let a green headless run count as "feature done."
- [ ] **Achievement board persists across PyMOL version upgrades:** Often missing forward-compatibility of the JSON schema. Verify: schema-version field in the achievement file; loader handles old versions gracefully.
- [ ] **Bulk-download retry actually resumes:** Often missing partial-download recovery. Verify: kill the download mid-way, restart, confirm it picks up missing structures without re-downloading completed ones (manifest-driven).
- [ ] **Per-claim approval is actually recorded:** Often missing the claims registry (Pitfall 7). Verify: grep the shipped content; every scientific claim has a corresponding `approved` entry in `data/claims.jsonl`. No un-approved claim ships.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong/fabricated PDB ID cited in shipped content | LOW | Replace ID in cast manifest + claims registry; re-fetch correct structure; re-approve via per-claim checkpoint; re-run reachability (cast change can break encounters). |
| `alter`-without-`sort` corruption already in code | MEDIUM | Introduce `apply_edit` helper (Pitfall 6); find all bare `cmd.alter` calls (grep); route through helper; add the sort+rebuild; re-test edit flows headlessly. |
| Branching spaghetti (no graph model) | HIGH | Refactor content into graph data structure (Pitfall 8); migrate existing prose onto edges; build reachability checker; this is a near-rewrite of the content layer — do it early, not late. |
| ATP-as-true-ending conflict discovered late (Pitfall 4) | MEDIUM-HIGH | Re-author True Ending narrative for the approved reframing; may touch cast (PPP enzymes?) and reachability (new ending path?). Cheaper the earlier it's caught — front-load. |
| Save format uses pickle (discovered post-ship) | MEDIUM | Migrate to JSON; write a one-time pickle→JSON migration for existing user saves (with security review of the loader); version the new format. |
| Bulk-download fails in classroom (offline) | LOW (per-session) | Degrade: lock affected characters; show retry; educator can pre-download on a connected machine and copy `data/cast/`. |
| Bad-ending pool feels unfair (playtest feedback) | LOW per entry | Expand edit table for the most-common unknown edits (session logs, Pitfall 10); add explanatory text; iterate. |
| GUI regression shipped (headless didn't catch it) | LOW per fix, HIGH per incident | Run the manual test matrix; fix; add the failing flow to the matrix so it doesn't regress again. |
| RNG not reproducible after save/load | MEDIUM | Add RNG seed+state to save schema; write a migration for old saves (seed unknown → mark "non-reproducible"); re-test demo workflow. |
| Qt import in logic layer blocks WSL tests | MEDIUM | Refactor: move Qt imports behind a UI seam; logic layer takes a "view interface" (duck-typed); re-enable unit tests. |

## Pitfall-to-Phase Mapping

Mapping each pitfall to the rough phase (per project context: scaffolding, content-authoring, editing, UI, polish) that must prevent it, and how to verify prevention worked.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. WSL/Windows path resolution | Scaffolding | Path-self-check passes on plugin load in a fresh shell; `cmd.fetch` with explicit `path=` lands files in the plugin data dir (assert via `count_atoms`). |
| 2. Qt untestable from WSL | Scaffolding | Logic-layer modules import-clean under `python3.6` with no `pymol.Qt`; unit tests run green in WSL; manual GUI test matrix exists and is run pre-merge for Qt-touching PRs. |
| 3. `cmd.create` no-op + API surprises | Scaffolding + Editing | `api-sanity` headless smoke runs (each `cmd.*` call has a post-condition assert); every new `cmd.*` call has a `file:line` source citation in a comment. |
| 4. ATP-as-true-ending science conflict | Content-authoring (start) | First content-milestone output is an approved reframing of the True Ending; claims registry has an `approved` entry for the chosen carbon-fate claim. |
| 5. `cmd.fetch` races/CIF/offline | Scaffolding + UI | All fetch calls use `async_=0, type=, path=`; manifest-driven bulk download has progress/cancel/retry; offline-fallback locks only affected characters (manual test). |
| 6. `alter` without `sort` | Editing | `apply_edit` helper is the only sanctioned alter path (grep finds no bare `cmd.alter`); helper has headless unit tests; restore-from-backup works for every edit type (manual GUI test). |
| 7. Per-claim approval bottleneck | Scaffolding + Content-authoring | Claims registry (`data/claims.jsonl`) exists; source-batch-approval workflow agreed with human; shipped content is 100% `approved` (grep-check). |
| 8. Branching complexity | Scaffolding | Graph data structure + reachability checker exist; reachability checker is green for all 4 tracks × 4 endings; graph renders to DOT for review. |
| 9. C14 decay timescale | Content-authoring | Bad-ending framing for decay is approved (per-claim); teaching-layer note explains timescale if decay is kept. |
| 10. Edit-table completeness | Editing + Content-authoring + Polish | Per-enzyme minimum-coverage scan is green; bad-endings have explanatory teaching-layer text; session log of unknown edits exists for iteration. |

## Sources

**Verified against bundled PyMOL 2.5.0 source (`tmp/pymol-src/modules/pymol/`, read-only):**
- `creating.py:960-962, 1002-1003` — `cmd.create` signature, no-op on `1,1`; `copy_properties` unsupported in open-source.
- `editing.py:1424-1473` — `cmd.alter` signature + the sort-after-alter WARNING at lines 1457-1460.
- `editing.py:1490-1533` — `cmd.iterate` including the Python-callback form (new in 2.5) at lines 1512-1515.
- `importing.py:1323-1394` — `cmd.fetch` signature, async-default behavior (`1382-1383`), `fetch_path` default (`1379-1381`), CIF default (`1346`), network/firewall note (`1367-1368`).
- `importing.py:1116-1145` — fetch host paths (RCSB/PDBe/PDBj/PubChem/ligand URLs, all HTTPS).
- `wizard/mutagenesis.py:47-48` — Mutagenesis wizard raises if a movie is loaded.
- `wizard/mutagenesis.py:58` — Mutagenesis wizard reads `os.environ['PYMOL_DATA']` for sidechain library.
- `plugins/__init__.py:193-210` — plugin metadata parsed from `# Key: Value` header.
- `plugins/__init__.py:248-324` — plugin load lifecycle; `__init_plugin__(pmgapp)` at line 321, legacy `__init__(pmgapp)` at 324.
- `plugins/legacysupport.py:26-31` — `get_pmgapp()` may return None (headless / non-GUI).
- `Pymol-script-repo/plugins/dynoplot.py:21` — modern Qt import idiom: `from pymol.Qt import QtCore, QtGui, QtWidgets`.
- `Pymol-script-repo/plugins/views.py:15`, `vina.py:23` — confirming the `pymol.Qt` convention across plugins.

**From AGENTS.md + spec.md (authoritative for this repo):**
- WSL/Windows split, `run-conda-pymol.bat` at `/mnt/c/src/` as the real entry point; `setenv.bat`/`wsl2win_cp.sh` do NOT exist here.
- `python3.6` (3.6.9) for syntax + pure-Python unit tests only; no pip/apt/conda.
- Per-claim scientific approval requirement; no fabricated science; no silent dependencies.
- PyQt5 via `pymol.Qt` + numpy only.

**From `.planning/PROJECT.md` (project context):**
- Scope: 3 characters + anaerobic = 4 tracks; all 4 endings reachable per character; ~20+ PDB proteins; edit-routing = lookup table + bad-ending fallback; RNG seedable for classroom reproducibility; stat/XP deferred to v2.
- Key Decisions table: per-claim approval chosen as safest (slowest) mode; hybrid PDB acquisition; success measure = all endings reachable for all characters.

**Domain reasoning (MEDIUM confidence — needs per-claim approval before any such claim lands in content):**
- Carbon-fate-in-respiration vs. ATP-as-destiny tension (Pitfall 4): basic biochemistry; the specific reframing options must be human-approved.
- C14 half-life (~5,730 years) vs. gameplay timescale (Pitfall 9): the half-life figure itself needs an approved source before use.
- Anaerobic-pathway-per-character variation (mentioned in Pitfall 4 context): lactate vs. ethanol fermentation differ by organism; the alcohol character's anaerobic fate specifically needs care.

**Gaps / not investigated here (flag for phase-specific research):**
- Exact PyMOL 2.5.0 Python version inside `chemtools-win10` (affects whether 3.7+ features are safe in plugin code vs. only testable modules being 3.6-limited). Recommend a `import sys; print(sys.version_info)` headless probe early in scaffolding.
- The correct user-writable path for achievement/save files on Windows PyMOL 2.5.0 (`cmd.get('user_dotdir')` behavior) — verify in scaffolding.
- Whether `pymol.Qt` provides a worker-thread abstraction for background fetch (affects Pitfall 5's bulk-download UI threading choice).
- The full set of respiratory-chain PDB candidates and their sizes (informs the bundle-vs-download threshold in the cast manifest) — a content-research task, not a pitfalls task.

---
*Pitfalls research for: PyMOL 2.5.0 plugin RPG teaching cellular respiration (C14 hero)*
*Researched: 2026-08-12*
*Confidence: HIGH (environment/API, source-verified) · MEDIUM-HIGH (scientific, needs per-claim approval) · MEDIUM (game-design/educational, domain reasoning)*
