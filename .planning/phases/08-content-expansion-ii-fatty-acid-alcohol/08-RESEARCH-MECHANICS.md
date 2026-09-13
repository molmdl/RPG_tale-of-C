# Phase 8: Content Expansion II (Fatty Acid + Alcohol) — Research: Multi-Character Content Mechanics

**Researched:** 2026-09-14
**Domain:** Mechanical substrate for Phase 8 — multi-character data layout, shared-TCA graph mechanics, CHAR-01 engine/UI surface, pinned-count/test/gate/tool migration, edits/cast/registry growth, approval-batch shape
**Confidence:** HIGH (every code claim below verified by reading the actual repo source + running the tools in WSL on 2026-09-14; no training-data claims)

**Scope note:** This is the "how to build it" research. Two sibling researchers own the SCIENCE content (08-RESEARCH-FA.md — NOT YET PRESENT at research time, verified absent 2026-09-14; 08-RESEARCH-ALC.md — present, read in full, its mechanics OQs are cross-referenced throughout). Every chemistry-adjacent item is reported as a MECHANICAL SLOT; its content comes from the siblings + human approval. Nothing here invents science. Code-level recommendations are Python 3.6 stdlib only.

---

## 1. Summary

Phase 8 adds the fatty-acid and alcohol characters (CHAR-01) and proves all 4 ending tiers × 3 characters reachable (STORY-02's 12 assertions). The mechanical substrate is far more ready than Phase 7's was: the engine already carries a `character` field end-to-end (rpg/state.py:60 `GameState.character`, serialized in saves rpg/state.py:88, exposed to story conds as `char` rpg/story/interpreter.py:129, passed by the controller rpg/ui/controller.py:343-352 and engine.start rpg/engine.py:108-120), the reachability checker already accepts an arbitrary start node (rpg/story/validate.py:167 `check_reachability(nodes, start_id)`), cast.json entries already carry a per-enzyme `character` field driving the bulk-download lock UI (rpg/data/cast.json; rpg/ui/bulk_download.py:120-178), and the achievements catalog already reserves `fatty_acid_tried`/`alcohol_tried` ids (rpg/achievements.py:66-71). The 05.1 design pre-agreed per-character shell nodes (`intro.shell_fa` / `intro.shell_alc`, 05.1-DESIGN.md:1745) living in the SAME graph.

The one structural decision that shapes everything: **one merged story bundle vs three per-character bundles.** Verified mechanics favor the **merged bundle** (Option A in §3): the loader is a single-manifest per-directory merge (rpg/story/graph.py:50-88) with no cross-directory goto resolution, the editor/7.1 toolchain + lint + viewer + zip are all hardwired to ONE bundle dir, the shared TCA/ETC/ending/bad-pool content is reused with zero duplication (the ALC sibling independently reached the same conclusion — 08-RESEARCH-ALC.md HF-2), per-character reachability needs NO new algorithm (BFS from each character's entry node), and save/load needs ZERO engine change (current_node ids resolve in the shared graph). Its cost is one large re-pin event: the 57/21/15-count pins plus ~20 more pinned constants across tests/lint/viewer/editor shift via the existing count-shift acknowledgment flow (tools/story_editor_lint.py:759-813).

The citation gate today exits 1 with a sanctioned residual of exactly 2 MISSING refs (`fa.stub`/`alc.stub` → `PLACEHOLDER_PHASE8`, data/story_glucose/intro.json:58,70) — Phase 8 retires that residual to 0 by replacing the stubs, which un-pins a chain of exact-count assertions (tests/test_glucose_content.py:213-236, :275-302; tools/story_editor_lint.py:127-128, :494-553; tools/story_graph_viewer.py:91,93).

**Primary recommendation:** ONE merged bundle (`data/story_glucose/` gains `fa_path.json` + `alcohol_path.json` manifest.files entries; nodes reuse `tca.json`/`etc_atp.json`/`endings.json`/`bad_endings.json` verbatim), char-entry BFS for the 12 assertions, StartDialog radio enable as the only required Qt change, shared edits.json/cast.json with new character-prefixed enzyme ids, and a Phase-7-shaped approval pipeline (2 science batches + 1 mechanics decision checkpoint + 1 registry-landing plan) with ledger PREPARATION now and approvals batched for the human's return.

---

## 2. Current-state mechanical inventory (what Phase 8 inherits, verified 2026-09-14)

### 2.1 The bundle + loader

- `data/story_glucose/manifest.json`: `version:1, default_seed:0, start:"intro.preface", files:[7]` (manifest.json:1-14). Loader `StoryGraph.load(story_dir)` reads ONE manifest and merges the listed files' `nodes` dicts; duplicate node ids across files raise ValueError (rpg/story/graph.py:76-80); `get_node` fails loud KeyError on bad goto targets (:90-97); `start_node()` returns the manifest's `start` (:108-111). **There is no multi-manifest or cross-directory mechanism** — a goto target must exist in the merged dict of the one loaded directory.
- The merge is CWD-independent and pure stdlib; the same manifest contract is re-implemented (deliberately, for plan-parallelism) in `collect_claim_ids` (rpg/story/validate.py:265-323, directory branch :291-314) and mirrored by the viewer/lint/editor loaders (tools/story_graph_viewer.py:124-162; tools/story_editor_lint.py:245-298; tools/story_editor.py:140-170).

### 2.2 Character plumbing that ALREADY works (zero engine change needed)

| Mechanism | Evidence | Phase 8 use |
|---|---|---|
| `GameState.character` stored + saved | rpg/state.py:60, :88 (`to_dict`), restored by `from_dict` with `"glucose"` default (:114) | FA/ALC saves carry `character` with NO schema change; old glucose saves load cleanly |
| Engine start accepts character | rpg/engine.py:108-120 (`start(character="glucose", seed=None)` → `GameState.new_game(character, ...)`) | FA/ALC new game = `engine.start("fatty_acid"/"alcohol", seed)` |
| `char` exposed to story conds | rpg/story/interpreter.py:123-133 (eval namespace `{"flags", "char", "counters", "visits"}`); the `char=='glucose'` example is in the model docstring (rpg/story/model.py:174) | character-gated choices are DATA-ONLY (`cond: "char=='fatty_acid'"`); nothing in today's data uses `char` conds yet (grep-verified) |
| Controller passes character through | rpg/ui/controller.py:343-352 (`start_game(character, seed)` → hero pre-pass → `engine.start`) | unchanged |
| Achievements `<character>_tried` reserved | rpg/achievements.py:66-71 ("fatty_acid_tried + alcohol_tried are Phase 8 ids — _unlock no-ops on them until the catalog is extended"); :208-211 records characters_tried + calls `_unlock(character + "_tried")` for ANY character | extend `ACHIEVEMENT_CATALOG_V1` with the 2 ids; zero controller change |
| Cast entries carry `character` | rpg/data/cast.json (all 12 entries `character:"glucose"`); bulk download + lock UI read it (rpg/ui/bulk_download.py:174-177, :236-275, :278-301) | new FA/ALC cast entries with their own character values |
| Per-character Qt start screen (disabled) | rpg/ui/main_window.py:128-138 (3 radios; FA+Alcohol `setEnabled(False)` + "Available in a future phase." tooltips), :171-173 (`accept()` hardcodes `result_character = "glucose"`) | CHAR-01's Qt surface = enable radios + return the checked one (human-verify) |
| Hero highlight is character-generic | intro.preface 6-op sequence (data/story_glucose/intro.json:8-19) + HeroResolver multi-C gate (rpg/ui/controller.py:98+) | same preface serves all 3 characters; FA/ALC multi-carbon shells exercise the existing OQ-6 multi-C warn+confirm path |

### 2.3 The graph shape Phase 8 grows (verified by scanning all 57 nodes)

- File breakdown: intro 5, glycolysis 7, pyruvate_branch 7, tca 13, etc_atp 7, endings 3, bad_endings 15 = **57 nodes**; **21 endings** = 1 true + 3 good + 2 normal + 15 bad; **15 edit-allowed nodes** (14 distinct `edit:enzyme:` tag values; `tca.aconitase` shared by `tca.aconitase` + `tca.shuffle`); **15 edit:offer choice nodes**; `edit.prompt` has 13 structural choices; `tca.shuffle` is the ONLY weighted node (0.5/0.5).
- Manifest relationship pin: cast(12) ⊂ edits(13) == tag values(14) − {tca.citrate_synthase}; cast == edits − {tca.akg_dh} (tests/test_glucose_content.py:404-449).
- The convergence joint FA/ALC flow into: **`tca.entry`** — the TCA/ETC/endings/bad-pool subgraph (tca.json + etc_atp.json + endings.json + bad_endings.json = 38 nodes incl. edit.prompt) is character-neutral (verified: `tca.entry`'s committed text asserts no glucose-specific chemistry; the ALC sibling reached the same conclusion, 08-RESEARCH-ALC.md §2.1 row 10).
- Registry: `data/citations.json` = **77 claims (73 approved + 4 pending BAD-*)**; `data/sources.json` = **81 records** (verified 2026-09-14). The 4 pending are the bad-pool framing claims (BAD-MISFOLD/INHIB/AGGREG/PH-01) — already the glucose bundle's only UNAPPROVED-referenced residue? No — verified: the 4 pending claims are NOT referenced by any node's claim_ids today (gate shows 0 UNAPPROVED).

---

## 3. THE structural decision: one merged bundle vs three per-character bundles

Two viable layouts; the repo's hardwired single-bundle tooling decides it.

### Option A — THREE per-character bundles (`data/story_fatty_acid/`, `data/story_alcohol/` + existing glucose)

Each dir self-contained (its own manifest + copied tca/etc/endings/bad_endings files). Costs, all verified in code:

| # | Cost | Evidence |
|---|---|---|
| A1 | **Content duplication:** ~38 nodes/char copied (tca 13 + etc 7 + endings 3 + bad 15 + edit.prompt); text divergence/drift risk ×2 | counted from the 7 files |
| A2 | **Controller/MainWindow graph switching:** the Controller loads ONE graph at construction (rpg/ui/controller.py:266); MainWindow builds it once from `_resolve_story_dir()` (rpg/ui/main_window.py:246-250, :74-96 — both hardcode `story_glucose`). CHAR-01 needs a character→dir map + a Controller rebuild per new game (Qt-side, human-verify) |
| A3 | **Load path breaks for cross-character saves:** `engine.load` re-enters `state.current_node` on the graph the engine was constructed with (rpg/engine.py:262-284) — loading an FA save under a glucose-constructed controller = KeyError. Requires save-peek + controller rebuild logic |
| A4 | **Relationship pin + coverage scan break:** the lint's `relationship_pin` computes tag values from ONE bundle vs the single edits.json (tools/story_editor_lint.py:609-641) — pointing it at the FA dir flags every glucose-only bucket as "bucket with no tag carrier". Same for `validate_edits_table` pool checks against one dir |
| A5 | **Gate/lint/test invocation triples:** 3× gate runs, 3× lint runs (each with glucose-pinned PINNED_* constants mis-firing), 3× zip staging (tools/build_plugin_zip.sh:101-103 copies only story_glucose; sanity `must` at :154) |
| A6 | **The 7.1 editor cannot edit FA/ALC at all:** MANIFEST_PATH + STORY_DIR_PREFIX are frozen constants `"data/story_glucose/manifest.json"` / `"data/story_glucose/"` (tools/story_editor_assets/10_load.js:112-113; 80_save.js:112; 45_lifecycle.js:189) |
| A7 | Viewer/editor FILE_COL/column map + STUB pinning assume one bundle | tools/story_graph_viewer.py:69-94 |

### Option B — ONE merged bundle (RECOMMENDED)

`data/story_glucose/` (historical name retained) gains 2 new story files appended to `manifest.files`; FA/ALC entry nodes are authored after `intro.select`; tca/etc/endings/bad_endings reused verbatim.

| # | Advantage | Evidence |
|---|---|---|
| B1 | **Zero engine/controller change:** `engine.start(character)` already parameterizes; `state.character` already rides saves; cond namespace already exposes `char` | rpg/engine.py:108-120; rpg/state.py:60; rpg/story/interpreter.py:129 |
| B2 | **Save/load works unchanged for FA/ALC:** current_node ids resolve in the shared graph; `GameState.from_dict` restores character; the 06-03 view capture/replay path is graph-agnostic | rpg/engine.py:262-284; rpg/state.py:101-126 |
| B3 | **Shared TCA = zero duplication:** FA/ALC early paths terminate into `tca.entry`; all approved TCA/ETC/soul-jump claims reused with no new registry entries for the shared arc | verified node text; ALC sibling HF-2/HF-3 concurs |
| B4 | **Per-character reachability needs NO new algorithm:** `check_reachability(nodes, start_id)` takes any start (rpg/story/validate.py:167-207); BFS from each character's entry node (e.g. `intro.shell_glucose` / `intro.shell_fa` / `intro.shell_alc`) = the 12-assertion matrix. The BFS ignores cond (validate.py:198-200 traverses cond-gated goto edges), which is exactly the semantics the glucose suite already relies on (tests/test_glucose_reachability.py:157-185) |
| B5 | **Editor support exists TODAY:** 07.1-17 shipped the manifest-edit-acknowledged new-file path that appends to `manifest.files` (07.1-17: "file select (7 manifest files + manifest-edit-acknowledged new-file path appending to manifest.files)"); 80_save DEST_MAP saves story files via the same prefix (tools/story_editor_assets/80_save.js:103-118) |
| B6 | **One gate/lint/zip invocation** retains every pinned command line used across TESTING.md/INTEGRATIONS.md/editor Help (verified grep: the exact string `tools/check_citations.py --story data/story_glucose --registry data/citations.json` is baked into 4 test files + story_editor.html:16099,16978) |
| B7 | **Relationship pin keeps its SHAPE:** cast(N+new) ⊂ edits(M+new) == tags(K+new) − {tca.citrate_synthase} — same assertion, bigger numbers | tests/test_glucose_content.py:404-449 |

**Costs of B (all manageable, none blocking):**
- B-C1: **One large re-pin event** — every pinned count in §6 shifts once, in the plans that add the nodes (the count-shift acknowledgment flow is explicitly designed for this: "Phase 8 topology work flows through this acknowledgment path", tools/story_editor_lint.py:43-48).
- B-C2: **intro.select dual-selector semantics:** the Qt StartDialog chooses the character BEFORE the graph loads; the in-story `intro.select` (3 unconditional choices, intro.json:33-37) then offers all 3 again. Resolution is data-only: cond-gate the 3 choices by `char` (each character sees its own "Continue as X" choice; `char=='glucose'` form is safe — the lint's BROKEN_COND_RE only flags `flags./visits./counters.` attribute forms, tools/story_editor_lint.py:170-171). The stubs' fate is a human checkpoint (§11 DC-2).
- B-C3: **Bad-tier reachability per character requires ≥1 edit-allowed node per character** (edit.prompt is reached only via edit:offer choices; the bad pool hangs off edit.prompt — data/story_glucose/bad_endings.json:15 nodes + edit.prompt 13 choices). ALC satisfies this via `alc.aldh2` (08-RESEARCH-ALC.md HF-4). **FA must author ≥1 edit-allowed node or the FA BFS goes red on 13+ bad endings** — a hard constraint to hand the FA sibling/planner (ACADM/MCAD-class disease mutants are the expected candidate; NOT verified — FA research pending).

**Recommendation: Option B.** It is the least-total-code-change layout, the least content duplication, and the only layout with which the existing editor, viewer, lint, gate, zip, and save/load machinery all keep working with parameter-value changes rather than structural changes.

---

## 4. Shared-TCA mechanics (deliverable 2)

**What the engine supports TODAY:** one graph per directory, merged from manifest.files; goto targets resolve by node id across file boundaries WITHIN the merge (verified: `pyr.pdh → tca.entry`, `tca.divert_to_good → etc.entry` are cross-file gotos in the live bundle). There is NO cross-file aliasing/import mechanism and NO cross-directory one — "sharing" is literal reuse of the same nodes in the same merged dict.

**Convergence topology (recommended):** FA early path: `intro.shell_fa` → fa.* beta-oxidation chain → **`tca.entry`**. ALC: `intro.shell_alc` → alc.* chain → `alc.acss2` → **`tca.entry`** (ALC sibling's roster, 08-RESEARCH-ALC.md HF-3). From `tca.entry` all three characters share: tca.json (13 nodes incl. the shared RNG shuffle + the glucose restoration branch `tca.aconitase_restored`), etc_atp.json (7), endings.json (3), bad_endings.json (15).

**Design consequences to encode in plans:**
1. **The RNG shuffle is shared** — FA/ALC True paths run the same seeded 50/50 (approved TCA-RNG-WEIGHT-01/-02). Determinism tests extend by walking each character's entry → shuffle (same documented fate; see §7.3). Adding any NEW weighted node would trip `weight_outside_shuffle` (tools/story_editor_lint.py:644-662 pins `SHUFFLE_NODE="tca.shuffle"`) — keep FA/ALC unweighted in v1 (ALC sibling recommends the same; its branch nodes are player-choice, not RNG).
2. **Restoration nodes are shared:** `gly.pfk_restored` + `tca.aconitase_restored` are router-only targets pinned by `ROUTER_ONLY_NODES` (tools/story_editor_lint.py:116) — a FA/ALC character editing the shared TCA aconitase routes to the SAME restored node. That is biochemically correct (same enzyme). No new restoration nodes required unless the FA/ALC siblings claim per-character arcs (ALC says ALDH2 is its own arc carrier — that's a NEW node pair, not a rebind).
3. **edits.json enzyme-id namespaces:** new FA/ALC enzymes must use NEW ids (`alc.aldh2`, `fa.acyl_coa_dh`, …) — the table is one flat dict keyed by enzyme_id (rpg/edit_router.py:85-92, :122-149); ids are namespaced by the dotted node convention and there is NO collision risk as long as new enzymes get new ids. Shared TCA enzymes keep their existing buckets (one bucket serves all characters — correct: same enzyme, same signatures).
4. **cast.json character-field semantics for shared PDBs:** if FA/ALC on_enter loads the same cast PDBs (1ACO etc.), the existing entries say `character:"glucose"`. A failed shared download would lock only "glucose" (bulk_download.py:236-275 maps failed→character) while FA/ALC scenes degrade via the controller's per-action swallow (rpg/ui/controller.py `_dispatch_molaction` try/except — non-crashing). Options: (a) accept under-locking (documented), (b) additive per-entry `characters:[...]` field the lock helpers learn to read (small bulk_download change, backward-compatible load-and-ignore), (c) per-character duplicate cast entries — REJECTED (duplicate ids break the cast==edits−{akg_dh} exactness pin). Recommend (a) for v1, (b) only if the human wants the lock precision — Checkpoint DC-7.
5. **`intro.shell_*` naming is pre-agreed:** 05.1-DESIGN.md:1745 names `intro.shell_fa` / `intro.shell_alc` as the Phase 8 shell nodes and :477 pins the pattern ("per-character — FA/Alc get their own shell nodes in Phase 8"). Use these ids.

---

## 5. CHAR-01 implementation surface (deliverable 3)

**What exists (human-verify surface already built in Phase 6):**
- The Qt StartDialog renders 3 radios with FA/Alcohol DISABLED (rpg/ui/main_window.py:128-138) and hardcodes `result_character="glucose"` on accept (:171-173).
- The controller start path + achievements + status bar are character-generic (controller.py:343-352; achievements.py:208-211; main_window.py:347).

**What Phase 8 must add (the complete list):**
1. **StartDialog:** enable the FA/Alcohol radios, update tooltips, set `result_character` from the checked radio. Character STRING choice: `"fatty_acid"` and `"alcohol"` — mandated by the reserved achievement ids `fatty_acid_tried`/`alcohol_tried` (achievements.py:66-71) and matching cast.json's snake_case convention. Qt-only → human-verify checkpoint (CHAR-01's verification mode per ROADMAP SC1).
2. **Achievements catalog:** append the 2 entries to `ACHIEVEMENT_CATALOG_V1` (achievements.py:63-71). Everything downstream (unlock, persistence, dialog render) already works generically (achievements_dialog.py:87-159).
3. **Story-side entry:** FA/ALC files authored with `intro.select` choices cond-gated by `char` (§3 B-C2) OR the stubs replaced by real shell nodes that are reached unconditionally when the Qt dialog pre-selected that character (ALC sibling's proposal: re-point `alc.stub` → `intro.shell_alc`, labels lose "(coming in Phase 8)"). Both are data-only; pick one in the mechanics decision checkpoint (§11 DC-2).
4. **Hero identification:** shared intro.preface hero-highlight fires for every character (it is the manifest start and is character-agnostic, intro.json:8-19). FA/ALC shells then load their own molecule; multi-carbon substrates trigger the EXISTING HeroResolver multi-C warn+confirm (controller.py:98+ — verified machinery). Nothing new to build; the human-verify matrix adds 2 rows.
5. **Engine entry-point handling:** NO change. `manifest.start` stays `intro.preface` for all characters (one bundle); character-specific entries are reached via the select/shell nodes. (If the human ever wants per-character manifests, engine.start already takes the character but `graph.start_node()` would need a character→start map — that is Option A territory, rejected in §3.)

**Explicitly NOT needed:** no GameState schema change, no save-version bump, no engine.py edit, no controller.py edit (beyond none), no new dialogs.

---

## 6. Gates/tests: the complete enumeration of pinned counts (deliverable 4)

Every pinned constant/assertion Phase 8 moves, with its owner and its post-Phase-8 value (Option B; FA node count ~10-14 estimated from the ALC template — LOW confidence until 08-RESEARCH-FA.md lands; ALC ~10 per sibling HF-3):

### 6.1 Test-suite pins (must be updated in the SAME plan that moves the count — OQ-K discipline)

| Pin | Today | Owner file:lines | Becomes (est.) |
|---|---|---|---|
| Node count | 57 | tests/test_glucose_reachability.py:136-155; :887-899 (`test_intro_topology_unchanged`); tools/story_editor_lint.py:152 `PINNED_NODE_COUNT`; tools/story_graph_viewer.py:105 `EXPECTED_NODES`; tools/story_editor_assets/20_validate.js:129; tests/test_story_editor_lint.py:625-630; tests/test_story_editor_lifecycle.py:433-434 (`PINNED_NODES = 57`) | ~75-81 (57 + FA ~10-14 + ALC 10, minus 0-2 stub conversions) |
| Ending count / tiers | 21 = 1T+3G+2N+15B | tests/test_glucose_reachability.py:157-189, :887-908; lint :153 `PINNED_TIER_COUNTS`; viewer :98; 20_validate.js:130 | 21 UNCHANGED if FA/ALC reuse shared ending nodes (recommended; ALC sibling HF-3 says "No new ending nodes") — but VERIFY FA doesn't add per-character endings; if it does, each +1 shifts this |
| Edit-allowed nodes | 15 (exact id set) | tests/test_glucose_reachability.py:264-324 (`expected_ids` frozenset); lint :154-159 `PINNED_EDIT_ALLOWED`; viewer :99-104; 20_validate.js:131-136 | 16-19 (+`alc.aldh2`; + FA's ≥1 required edit-allowed node §3 B-C3) |
| distinct edit:enzyme tag values | 14 | tests/test_glucose_content.py:429-431 | 15-18 |
| edits.json buckets | 13 (exact-equality vs tags) | tests/test_glucose_content.py:427-428, :398-400 (13 signature round-trips); lint relationship rule :609-641 | 14-18 |
| cast.json entries | 12 (`cast == edits − {tca.akg_dh}` exact) | tests/test_glucose_content.py:426, :441-445 | 14-17 (ALC: aldh2 + maybe adh; ACSS2 MUST NOT enter cast — coverage-scan trap, ALC sibling OQ-5) |
| edit:offer nodes | ≥15 (assertGreaterEqual) | tests/test_glucose_reachability.py:490-494 | grows automatically (additive assertion — no edit needed unless the floor is re-pinned) |
| gate residual | exit 1 with EXACTLY 2 MISSING (fa.stub/alc.stub→PLACEHOLDER_PHASE8), 0 UNAPPROVED | tests/test_glucose_content.py:275-302 (`test_gate_residual_exactly_two_documented_stubs`), :213-236 (`test_placeholder_phase8_only_on_documented_stubs`); lint :494-553 (sanctioned-residual exact-pair rule) | **exit 0, 0 MISSING, 0 UNAPPROVED** once both stubs retire their claim_ids (§8 DC-2) |
| expected_download_characters | `== {"glucose"}` | tests/test_bulk_download.py:142-145 | `{"glucose","fatty_acid","alcohol"}` subset per new cast entries |
| suite total | 599 tests OK (ran 2026-09-14, 26s) | `python3.6 -m unittest discover -s tests` | grows (+~15-30 new tests) |
| per-file batteries | reachability 21, content 19, lint 31, bulk_download 12, engine 23, integration 17, persist 5 | counted 2026-09-14 | referenced for review; no fixed pins besides those above |

### 6.2 The 12-assertion cross-character reachability test (STORY-02)

Shape (no new algorithm): one new test file (e.g. `tests/test_multichar_reachability.py`), parametrized over the 3 character entry nodes; for each, `check_reachability(g.all_nodes(), <entry>)` and assert the reachable tier set == {true, good, normal, bad} — 3 chars × 4 tiers = 12 subTest assertions. Entry nodes: `intro.shell_glucose` (existing), `intro.shell_fa`, `intro.shell_alc` (05.1-DESIGN.md:1745 names). Load ONE graph, call the checker 3× (it is pure and stateless, validate.py:167-207). RED-variant: one orphaned ending per character scope re-uses the :191-231 pattern. Keep the existing all-character BFS green too (union reachability from intro.preface).

### 6.3 Determinism tests per character

Existing pattern: `TestSeededDeterminismDesignB` (tests/test_glucose_content.py:485-537; seed 42 → `tca.co2_turn2`, the OTHER fate `tca.co2_turn1`, both-fates-over-30-seeds) + the only-weighted-node pin (:539-557). Phase 8 extends: for each new character, engine.start(char) → walk to `tca.shuffle` → seed 42 → documented fate. Because the shuffle node is shared, the fate is IDENTICAL to glucose's — one parametrized test over 3 characters suffices (ALC sibling HF-9 concurs). The `choice[0]`-walk helper (tests/test_glucose_content.py:442+ `_walk_to_shuffle`) needs a per-character path variant (FA/ALC branches are player choices, not index-0 chains — write the walk per character's True route).

### 6.4 Save/load round-trip tests (ROADMAP SC4)

Existing patterns to parametrize: tests/test_engine.py:125-186 (round-trip, replay, no-double-visit, rng-state) and tests/test_integration.py:254-334 (mid-playthrough save/load). New: for character in {fatty_acid, alcohol}: start → advance ≥2 nodes → save → load → assert state equality + replayed MolActions + `state.character` preserved + ending reachable after load. Zero engine change makes these pure test additions (§3 B2).

### 6.5 Citation-gate extension (deliverable 4d)

The gate needs NO code change: it takes `--story <dir>` (tools/check_citations.py:104-106) and the merged bundle keeps ONE invocation (`--story data/story_glucose`) whose exact string is baked into 4 test files + story_editor.html (verified grep). The gate already reads the manifest.files list dynamically (validate.py:298-313) — new files are scanned automatically. The Phase 8 end state: exit 0 with 0 MISSING (both stubs retire) — replacing today's sanctioned exit-1 residual. All three workflows (gate, lint, coverage) stay single-invocation.

---

## 7. Registry / edits / cast growth mechanics (deliverable 5)

### 7.1 Claim/source estimates (coordinate with siblings)

- **ALC (08-RESEARCH-ALC.md, read in full):** ~16 candidate claims (§2 inventory: 1 PubChem + ADH/ALDH2/reaction/NADH/lipogenesis/convergence + DIS-ALDH2-01-cand + 2-3 CAST-PDB + optional CO2WATER/FLUSH/TOX), ~10-14 new sources (2 Wikipedia CC BY-SA + 6-8 RCSB + 4-5 UniProt + 1 ClinVar + 1 PubChem). High-stakes individual-review tier: DIS-ALDH2-01-cand, ALC-LIPO-01-cand (+ ALC-PERIPH-ACETATE-01-cand only if a source is verified — currently pending-source, do NOT file).
- **FA (08-RESEARCH-FA.md):** ABSENT at research time (verified 2026-09-14). Estimate by the ALC template + beta-oxidation's larger enzyme surface (acyl-CoA synthetase, carnitine shuttle, acyl-CoA dehydrogenase chain, β-ketothiolase…): **~15-25 claims, ~10-18 sources, 2-4 cast PDBs, 1-2 restoration-arc candidates. LOW confidence — re-baseline when the file lands.**
- **Shared/cross-boundary claims (ALC OQ-6):** the ATP→AMP activation-cost claim and the lipogenesis/FA-synthesis wording overlap FA territory — one joint decision at the combined approval batch to avoid duplicate/contradicting registry entries. The shared TCA/ETC/endings arc needs ZERO new claims (verified node texts + ALC §2.2).
- **Registry growth mechanics are proven:** Phase 7 landed 5→77 claims / 5→81 sources in ONE sole-writer plan (07-05-SUMMARY.md: provides-section). Phase 8 lands via the same shape: one registry-landing plan applies both batch verdicts; M1 policy (keep `-cand` ids verbatim, flip approval_status only — 07-01-SUMMARY.md decision 5) continues to bind.

### 7.2 edits.json

- Schema unchanged (rpg/edit_router.py:57-102; the Phase 7 authoring spec in 07-RESEARCH-content-mechanics.md §4.1 remains the contract: lowercase targets, `new_res` args key on the EditIntent side vs `new_resn` on the MolAction side, duplicate-signature per bucket).
- New buckets keyed by NEW enzyme ids (`alc.aldh2`, FA equivalents) — zero collision risk with glucose ids (§4.3).
- The global bad_ending_pool (`bad.lost_connection`, `bad.released_from_host` — rpg/data/edits.json verified) serves all characters unchanged; per-enzyme pools for new enzymes are optional (OVERRIDE semantics, rpg/edit_router.py:151-166).
- The relationship-pin equality (`edits == tags − {tca.citrate_synthase}`) must hold ACROSS the merged graph — the plan that adds a bucket must add the matching tag-carrying node in the SAME plan (and vice versa), or the pin + lint rule go red (tests/test_glucose_content.py:404-449; tools/story_editor_lint.py:609-641).

### 7.3 cast.json + bulk download

- New entries follow the exact 12-entry schema (`id/label/source/pdb_id/character/claim_id` — verified). `source:"download"` + real pdb_id triggers the bulk-download prompt for the new PDBs automatically (bulk_download.py:120-178 — no code change). The PLACEHOLDER guard stays for any not-yet-approved id.
- Coverage coupling: every new cast id needs ≥1 edits.json bucket (check_edit_coverage.py:88-104 + scan_edit_coverage rpg/edit_router.py:238-255) — the ALC sibling already engineered its roster around this (ACSS2 stays narrative-only; HF-4 carries the arc on ALDH2).
- Zip: `tools/build_plugin_zip.sh` copies only `data/story_glucose` (:101-103) and sanity-checks `rpg/data/story_glucose/manifest.json` (:154) — under Option B these are UNCHANGED (one bundle). rpg/data/cast.json + edits.json ship via the existing copytree.

---

## 8. Tool / editor / viewer migration surface (deliverable 7 part 1)

| Tool | Pinned constants Phase 8 shifts | Change shape |
|---|---|---|
| tools/story_editor_lint.py | `PINNED_NODE_COUNT/TIER_COUNTS/EDIT_ALLOWED` (:152-159); `PHASE8_STUB_NODES`/`PHASE8_CLAIM` (:127-128) + the exact-pair sanctioned-residual rule (:494-553); `SHUFFLE_NODE` (:139 — unchanged if no new weighted nodes); `ROUTER_ONLY_NODES` (:116 — extended only if new restoration nodes); `START_NODE_PREFIX="intro."` (:135 — unchanged: shells are intro.*) | value re-pins + retire/keep the stub rule per DC-2; args already parametrized (--story-dir) so ONE default invocation keeps working |
| tools/story_graph_viewer.py | `FILE_COL`/`COL_LABELS`/`N_COLS=7` (:69-87 — new columns for fa/alcohol files; stub column 6 retires per ALC OQ-3); `STUB_IDS`/`PLACEHOLDER_CLAIM` (:91,93); `EXPECTED_NODES/TIER_COUNTS/EDIT_ALLOWED` (:98-105) | re-pin + regenerate `dev/story_graph_viewer.html`; integrity self-check is a HARD gate (exit 1 + no HTML on violation, :631-644) — re-pin in the SAME plan as the topology change |
| 7.1 editor (tools/story_editor_assets/*) | 10_load.js MANIFEST_PATH/STORY_DIR_PREFIX (:112-113) — UNCHANGED under Option B; 20_validate.js PINNED_* (:129-147) + obligations list; 45_lifecycle.js count-shift modal strings + `PINNED_NODES = 57` (tests/test_story_editor_lifecycle.py:433-434); 80_save DEST_MAP (:103-118 — new files save correctly via the same prefix) | re-pin values; new story files are loadable/editable TODAY via the 07.1-17 manifest-edit-acknowledged path; **committed story_editor.html must be REGENERATED** (`python3.6 tools/story_editor.py`) in any plan that touches assets or shifts pinned values (the 718KB artifact is a build product committed at repo root) |
| tools/check_citations.py / check_edit_coverage.py | none (single-invocation, hardcoded paths already correct) | none |
| tools/build_plugin_zip.sh | none under Option B | none |
| tools/demo_playthrough.py + controller_integration_smoke.py | STORY_DIR pins (demo_playthrough.py:69; smoke :196) stay glucose-valid; smoke already has 3 pre-existing FAILs (STATE.md Pending Todos) and `bulk_download_expected_chars_empty` will drift further once new cast entries land | smoke re-alignment is already a owed TODO — fold into the Phase 8 verification plan or leave flagged |
| rpg/ui/main_window.py | `_resolve_story_dir()` (:74-96) unchanged under Option B; StartDialog radios (:128-138, :171-173) | the ONLY required code edit outside tests |

---

## 9. Approval-batch mechanics (deliverable 6)

**The Phase 7 pattern to replicate (verified shape):** Wave 1 = 1 structural/mechanics decision checkpoint (07-01) + 3 approval-batch checkpoint plans (07-02/03/04, one per pathway segment, each presenting sources+claims grouped BY SOURCE with `Outcome:` verbatim recording) → Wave 2 = ONE registry-landing plan (07-05, sole writer of citations.json+sources.json, applies all verdicts, re-runs gate). Content plans then cite only approved claims (07-PLAN-INDEX.md global constraints).

**Recommended Phase 8 shape: 1 mechanics checkpoint + 2 science batches + 1 registry landing.**

| Plan | Type | Content |
|---|---|---|
| 08-01 | checkpoint:decision (mechanics) | THE §11 decisions: bundle layout ratification, stub fate, char-cond form, cast shared-PDB lock semantics, FA edit-allowed floor, batch grouping. Record `Outcome:` lines verbatim (07-01 ledger pattern) |
| 08-02 | checkpoint:decision (approval batch FA) | ALL FA sources+claims from 08-RESEARCH-FA.md, grouped by source; cross-boundary claims (ATP→AMP activation; lipogenesis wording) resolved here jointly with ALC (ALC OQ-6) |
| 08-03 | checkpoint:decision (approval batch ALC) | The alcohol batch per ALC HF-5: 2 Wikipedia sources + PDB records + UniProt/ClinVar/PubChem + ~14-16 claims; high-stakes individually (DIS-ALDH2-01-cand, ALC-LIPO-01-cand) |
| 08-04 | execute (registry landing) | Sole writer: apply both verdicts; M1 keep-`-cand` policy; re-run gate (residual after stub retirement = 0) |

**HUMAN-BOTTLENECK NOTE (binding):** the human is currently mid-checkpoint on Phase 7 (07-18 Task 2 batch content review PENDING + the 07.1-11 one-step Firefox re-verification, verified in .planning/STATE.md). Research and approval-batch PREPARATION (building 08-02/08-03 ledgers as presentation documents, pending-status registry seeds) can proceed now, but the batch checkpoints themselves must be scheduled/queued for when the human returns — do NOT run interactive decision checkpoints into a void. The 07-05 landing-plan pattern (verdicts recorded in ledgers → applied later by a sole writer) is exactly the async-safe mechanism: ledgers first, human verdicts whenever they arrive, landing after.

---

## 10. Plan-slicing recommendation (deliverable: wave order)

Constraints discovered: (1) ONE merged bundle → story-file writes are disjoint per plan but tests/lint/viewer/editor pins are shared serialization points; (2) registry = sole-writer plan; (3) edits.json + cast.json = single-owner plans each; (4) the count re-pin is one atomic event best owned by ONE plan (mirror of Phase 7's plan-12 pattern, 07-01-SUMMARY outcome 1: "test-count updates never deferred"); (5) approvals gate content.

- **Wave 1 (decisions + prep, human-async):** 08-01 mechanics decision checkpoint; 08-02/08-03 approval-batch ledger PREP (auto — build the presentation documents + pending registry seeds; checkpoints fire when the human returns).
- **Wave 2:** 08-04 registry landing (after verdicts). Parallel-safe once verdicts exist: 08-05 graph-infra plan — adds BOTH new story files with skeleton nodes + intro.select re-pointing + STUB retirement + THE count re-pin (tests + lint + viewer + editor constants + diagram + story_editor.html regen) as ONE atomic topology plan (the 07-12 mirror).
- **Wave 3 (content, parallel-safe per file):** 08-06 FA path content (fa file) + 08-07 ALC path content (alcohol file) — claim swaps from the landed registry, two-layer text, on_enter scene fills, edit-allowed nodes + their edits.json buckets (or a dedicated 08-08 edits plan if both siblings' buckets land together — single-owner rule).
- **Wave 4:** 08-09 cast.json + PDB assets (new entries, bulk-download verification); 08-10 the 12-assertion reachability + per-char determinism + save/load round-trip test battery; StartDialog enable + achievements catalog extension (small code plans, human-verify task).
- **Wave 5:** 08-11 cross-cutting verification — full gate exit 0 (residual 0), coverage green, lint green, suite green, zip rebuild sanity, smoke re-alignment (the 3 pre-existing controller smoke FAILs + new cast drift), human-verify summary (Qt char select, FA/ALC playthroughs to ≥1 ending each, bulk-download prompt with new PDBs).

Collapsible to ~6-8 plans if the human prefers (merge 08-06/07 into per-character mega-plans; fold 08-09/10 into 08-11) — the 10-plan version matches the Phase 7 granularity precedent.

---

## 11. Human decision checkpoints (mechanics-owned; science belongs to siblings)

1. **DC-1 — Bundle layout ratification:** merged bundle (recommended, §3) vs three dirs. The ALC sibling independently recommends merged (HF-2).
2. **DC-2 — fa.stub/alc.stub fate:** (a) REPLACE in place: stubs become/become-replaced-by `intro.shell_fa`/`intro.shell_alc`; `PLACEHOLDER_PHASE8` retires; gate residual → 0; lint sanctioned-residual rule retired; viewer stub column retired (ALC sibling OQ-2 proposal — RECOMMENDED); (b) keep stubs as honest signpost nodes with no claim_ids (57 count unchanged; select re-pointed; still retire the claim); (c) delete the nodes (57→55; most test churn). Note the in-story select vs Qt dialog dual-selector resolution rides on this (§3 B-C2).
3. **DC-3 — intro.select choice gating:** cond-gate by `char` (recommended) vs leave unconditional (in-story selector can contradict the Qt selector).
4. **DC-4 — FA edit-allowed floor:** confirm FA authors ≥1 edit-allowed node (bad-tier reachability requirement, §3 B-C3) and its disease candidate BEFORE batch approval.
5. **DC-5 — cast shared-PDB lock semantics:** accept under-locking (recommended v1) vs additive `characters` list field in bulk_download (small code change).
6. **DC-6 — new weighted nodes:** confirm NONE for FA/ALC in v1 (keeps `weight_outside_shuffle` + determinism story intact).
7. **DC-7 — approval cadence:** 2 science batches + async ledger prep (recommended) vs per-plan checkpoints.
8. **DC-8 — ACSS2-class narrative-only enzymes:** confirm cast.json stays strictly "has PDB + has bucket" (coverage invariant) — narrative-only nodes never enter cast.

---

## 12. Open questions

1. **08-RESEARCH-FA.md does not exist yet** (verified absent 2026-09-14). All FA-specific numbers in this doc are template-based estimates (LOW). The FA sibling's node roster, edit-allowed floor candidate, cast PDBs, and claim set will re-baseline §6/§7/§10. Coordinate: the joint approval batch must reconcile the shared activation-cost and lipogenesis claims (ALC OQ-6) BEFORE either lands.
2. **FA/ALC shell on_enter assets:** glucose shells load bundled `_smoke.pdb` placeholders (start-node no-network rule, tests/test_glucose_reachability.py:868-885 + lint start_node_pdb_load). FA/ALC shells are NOT start nodes (start stays intro.preface) so real `pdb:` loads are lint-legal there — but the small molecules (fatty acid, ethanol CID 702) would network-fetch on first encounter. Bundled-placeholder vs PubChem-fetch per shell is a content/planner call per character (ALC sibling flags PubChem CID 702 verified; the FA equivalent pending).
3. **Old glucose saves + stub retirement:** if stubs are deleted (DC-2c) a save sitting ON fa.stub/alc.stub would KeyError on load — no such save should exist in the wild (stubs were only ever bounce-through), but if DC-2(a)/(b) keeps the nodes the concern vanishes entirely. Another argument for (a)/(b).
4. **`test_15_edit_allowed_nodes` exact-set assertion vs additive growth:** the test pins an exact frozenset — every plan adding an edit-allowed node updates the set in the SAME plan (the D5 precedent, tests/test_glucose_reachability.py:264-324 history). Mechanical, but easy to miss across 2 sibling plans — the single re-pin plan (08-05) owning ALL count edits removes the race.
5. **Story-editor HTML regeneration cadence:** the committed artifact must be regenerated in every plan that lands assets or pin shifts (7.1 precedent). With 2-3 such plans in Phase 8, schedule regens to avoid in-flight-asset deferrals (the 07.1-09/12/14 deferral+heal pattern).
6. **`end.good.fatty_acid` naming collision with the FA character:** purely cosmetic confusion risk — the node is glucose-TCA-owned (citrate-export exit) and ALC's lipogenesis branch terminates INTO it; the FA character's Good ending likely uses the SAME node or a FA-specific one. Sibling + human decide; no mechanical impact (node ids are already dotted-namespaced).

---

## Sources (all HIGH — direct repo verification on 2026-09-14 unless noted)

- Code read in full: rpg/story/graph.py, model.py, validate.py, interpreter.py; rpg/engine.py, state.py, citations.py, edit_router.py, paths.py, achievements.py; rpg/ui/main_window.py (start dialog + story-dir resolution), controller.py (key sections), bulk_download.py; tools/check_citations.py, check_edit_coverage.py, story_editor_lint.py, story_graph_viewer.py (pins + integrity gate), story_editor.py (defaults), story_editor_assets/10_load.js, 20_validate.js, 80_save.js, 45_lifecycle.js (pins); build_plugin_zip.sh; tests/test_glucose_reachability.py, test_glucose_content.py, test_bulk_download.py (pins), test_integration.py, test_engine.py, test_persist.py (counts).
- Data scanned: data/story_glucose/*.json (all 7 + manifest — node/tag/ending/edit tag census), data/citations.json (77/73+4), data/sources.json (81), rpg/data/edits.json (13 buckets + pool), rpg/data/cast.json (12 entries), data/story/manifest.json (toy fixture).
- Tools executed: full unittest suite → **599 tests OK** (26s); node/tag census script (57/21/15/14/13/12 verified).
- Planning docs: ROADMAP.md (Phase 8 entry + Phase 7.1 details), STATE.md (current position: 07-18 Task 2 + 07.1-11 re-verify pending — the human-bottleneck basis), REQUIREMENTS.md (CHAR-01/STORY-02 text + anaerobic clause), 07-RESEARCH-content-mechanics.md (format + the approval/registry/edits contracts inherited), 07-01-SUMMARY.md (decision-ledger pattern + M1/OQ-K policies), 07-PLAN-INDEX.md (wave/roster conventions), 07-05-SUMMARY.md (registry-landing shape), 05.1-DESIGN.md:477-478,1003-1005,1184,1745 (pre-agreed shell nodes + stub semantics).
- Sibling research: 08-RESEARCH-ALC.md (read in full; HF-1..HF-10 + OQ-1..OQ-10 cross-referenced); 08-RESEARCH-FA.md (ABSENT — flagged).
- PyMOL source consulted: none needed this phase (no molops surface changes recommended).

**Research date:** 2026-09-14 · **Valid until:** stable (repo-internal mechanics; ~30 days or until the Phase 8 planning/08-RESEARCH-FA.md landing changes the numbers).

---

## PLANNER HANDOFF — the structural decisions to make, with recommendations

| # | Decision | Recommendation |
|---|----------|----------------|
| **H1. Data layout** | **ONE merged bundle** (Option B): append `fa_path.json` + `alcohol_path.json` (or sibling-chosen names) to `data/story_glucose/manifest.json.files`; zero engine/controller change; save/load works unchanged; editor new-file support exists (07.1-17). Reject 3-dir layout (§3 costs A1-A7). |
| **H2. Shared TCA** | Reuse `tca.json`/`etc_atp.json`/`endings.json`/`bad_endings.json` verbatim; both new paths converge into `tca.entry`; no node duplication, no new TCA/ETC claims, no new weighted nodes (DC-6). New enzymes get NEW namespaced ids (`alc.aldh2`, `fa.*`) sharing the flat edits.json table. |
| **H3. Manifest/entry scheme** | `manifest.start` stays `intro.preface`; per-character entries are `intro.shell_fa`/`intro.shell_alc` (pre-agreed, 05.1-DESIGN.md:1745) reached via intro.select; 12-assertion test = `check_reachability` per entry node (no new algorithm). |
| **H4. Stub fate + gate residual** | DC-2(a): replace stubs with real shell wiring; `PLACEHOLDER_PHASE8` retires; gate → exit 0 residual-0; retire the lint sanctioned-residual pair + viewer stub column in the SAME topology plan. |
| **H5. The one atomic re-pin plan** | Own ALL count shifts in ONE Wave-2 plan (07-12 mirror): tests (57→~N, tier counts, edit-allowed set, cast/edits/tags equalities, gate-residual tests, bulk-download char set) + lint PINNED_* + viewer EXPECTED_*/FILE_COL + 20_validate.js + story_editor.html regen + diagram. Never spread count edits across content plans. |
| **H6. Approval pipeline** | Phase-7 shape: 08-01 mechanics checkpoint + 08-02 (FA) / 08-03 (ALC) approval batches + 08-04 sole-writer registry landing. Ledger PREP is auto and starts now; the batch checkpoints queue for the human's return (they are mid-Phase-7). M1 keep-`-cand` policy continues. |
| **H7. Wave order** | W1 decisions+ledger-prep → W2 registry landing + the atomic re-pin/topology plan → W3 FA + ALC content (parallel, disjoint files; single-owner edits/cast plans) → W4 cast/bulk-download + 12-assertion/determinism/save-load battery + Qt radio enable + achievements catalog → W5 verification (gate exit 0, coverage, lint, suite, zip, smoke re-alignment, human-verify matrix). |
| **H8. FA constraint to enforce at planning** | FA must author ≥1 edit-allowed node (bad-tier BFS reachability via edit.prompt) and must NOT put non-PDB enzymes (ACSS2-class) into cast.json. Verify both in the FA content plan's done-conditions. |
| **H9. Shared-PDB lock semantics** | v1: accept the per-entry `character` under-locking on shared TCA PDBs (documented); the additive `characters` list in bulk_download is a deferred option (DC-5). |
| **H10. Qt/CHAR-01 code surface** | Exactly two small edits + one data extension: StartDialog radio enable (human-verify), `ACHIEVEMENT_CATALOG_V1` += fatty_acid_tried/alcohol_tried, intro.select char-cond labels. Nothing else in engine/controller/state. |
