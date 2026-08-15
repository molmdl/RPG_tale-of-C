# Phase 5 Research — C14 Decay Timescale Framing (Pitfall 9)

**Researched:** 2026-08-15
**Aspect:** C14 radioactive-decay bad-ending timescale framing (Pitfall 9) — ONE of the 4 Phase 5 science-framing decisions
**Phase goal addressed:** Success Criterion #2 — "The C14 radioactive-decay bad-ending timescale framing is resolved (drop / time-compress / reframe as teaching moment) and documented; if decay is kept, the half-life citation is approved."
**Decision owner:** THE HUMAN. This document GATHERS options + REAL candidate sources FOR THE HUMAN to decide. It does NOT decide. It does NOT approve any source. Every candidate source below is marked `CANDIDATE — needs human approval`.
**Confidence:** HIGH for the existence/resolvability of the primary nuclear-data sources (NUBASE2020 DOI + NuDat 3.0 + IAEA LiveChart pages were fetched live during research); MEDIUM for textbook candidates (not web-verified); the precise decay-probability numbers are DERIVED (computed from the half-life + decay law) and are NOT sourced claims — only their inputs are.

---

> **No-fabricated-science invariant (read first).** Per `spec.md` and `AGENTS.md`, every scientific claim and citation must be verified against a real source AND explicitly human-approved per claim before landing in code/content. This research **proposes real, identifiable candidate sources** for the human to approve later. It does NOT invent DOIs, PDB IDs, or references. Exactly **one** DOI appears below (`10.1088/1674-1137/abddae`) — it was **verified to resolve** via `https://doi.org/...` during this research (not invented). No other DOI is asserted. Textbook references are given by title/author/publisher without invented ISBNs and are flagged `verify existence + edition`.

---

## Summary

Pitfall 9 is a localized, scientifically-fixable framing problem, not a blocker: the spec lists "radioactive decay" as a bad-ending trigger (spec.md line 18), but C14's half-life is ~5,700 years, so the probability of a single C14 atom decaying during one respiration cycle (seconds–minutes, the actual gameplay timescale) is ~10⁻¹² — not "essentially zero" in a vague sense, but ~12 orders of magnitude below 1. Presenting decay as a live in-game risk is scientifically misleading about decay rates, and a biochem-educator reviewer will flag it.

The good news: the science is well-established and has clean, authoritative, **verifiable** primary sources — the NUBASE2020 evaluated nuclear-data library (DOI verified to resolve), the NNDC/BNL NuDat 3.0 database (page live), and the IAEA LiveChart of Nuclides (page live). Educational/teaching-layer coverage exists in the LibreTexts Nuclear Chemistry hub (page live, CC BY-NC-SA 4.0) — aligning with the project's spec.md leaning toward LibreTexts as a source family. So **no source-availability risk** blocks this decision: the human can approve any of several real sources.

Three framing options are on the table (per SC#2: drop / time-compress / reframe as teaching moment), plus three additional options this research identifies (decay-as-side-note only, decay-as-deep-time-epilogue, decay-as-educator-demo-toggle). Each is laid out below with pros/cons, story-graph impact, the all-4-endings-reachability implication, and the per-claim approval load.

**Primary recommendation (advisory):** Option **(c) REFRAME AS TEACHING MOMENT** — keep decay as a bad-ending trigger but make the teaching layer explicitly state that C14's half-life is ~5,700 years and decay during one respiration cycle is effectively impossible; the decay ending is a dramatic device, and C14's *long* half-life is precisely why it is useful as a tracking isotope. This aligns with the spec (keeps the trigger), with the project's two-layer text design, with the educator audience, and with PITFALLS.md's own recommended mitigation. The key **tradeoff flagged**: (c) carries the **highest** per-claim approval load of the options (~5–6 claims), and the "essentially zero probability" claim requires the human to fix a defensible comparison timescale. If minimizing approval throughput dominates, option (a) DROP or (d-i) SIDE-NOTE-ONLY have the lowest load — but for this single bad-ending sub-trigger the absolute claim count is small relative to the hundreds of claims in the full content (Pitfall 7), so the educational-value argument should dominate over the throughput argument here.

---

## The Science (candidate sources — each `CANDIDATE — needs human approval`)

### The core facts that need sourcing

| # | Fact the narrative may assert | Status |
|---|-------------------------------|--------|
| F1 | C14 has a half-life of ~5,700 years | Needs approved source (value + source) |
| F2 | C14 decays to N14 via beta-minus (β⁻) emission: ¹⁴C → ¹⁴N + e⁻ + ν̄ₑ (+ ~0.1565 MeV) | Needs approved source |
| F3 | Radioactive decay follows the decay law N(t) = N₀·e^(−λt), with λ = ln(2)/t½ | Needs approved source (textbook-level) |
| F4 | The probability of a single C14 atom decaying during one respiration cycle is effectively zero (~10⁻¹²) | **DERIVED** from F1+F3+ a defined "respiration cycle" duration; the duration needs a biochem source |
| F5 | C14's long half-life is why it is useful as a tracking/tracer isotope | Conceptual claim; needs a source |

### Candidate primary sources (nuclear data — authoritative for F1, F2)

**S1. NUBASE2020 evaluation — `CANDIDATE — needs human approval` (PRIMARY, HIGH confidence it exists)**
- Reference: Kondev, F. G.; Wang, M.; Huang, W. J.; Naimi, S.; Audi, G. (2021). "The NUBASE2020 evaluation of nuclear physics properties." *Chinese Physics C*, 45(3), 030001.
- DOI: `10.1088/1674-1137/abddae` — **VERIFIED TO RESOLVE** during this research (fetched `https://doi.org/10.1088/1674-1137/abddae` and received the publisher's bibliographic record).
- What it backs: the half-life value (F1) and the decay-mode classification (F2). NUBASE is the international standard *evaluated* nuclear-data library for ground-state properties (half-lives, decay modes, isospin, etc.), maintained by the Atomic Mass Data Center (AMDC, CSNSM, CNRS/IN2P3, Orsay, France). It is the source Wikipedia's Carbon-14 article cites for the "5700 ± 30 years" figure.
- Host page (for context only, not the citable artifact): `https://www.amdc.in2p3.fr/` — **NOTE: this page returned transport errors during research (flaky, not necessarily gone). The citable artifact is the *published evaluation* (the Chinese Physics C paper + DOI above), not the AMDC website. Do not rely on the website URL at approval time; cite the paper.**
- Freshness flag: NUBASE evaluations are revised roughly every 3–4 years (NUBASE2016 → NUBASE2020). As of the research date (2026-08-15), Wikipedia's Carbon-14 article (last edited 2026-07-17) still cites NUBASE2020 — a reasonable signal it is still the current evaluation, **but the human should confirm at approval time** whether a newer evaluation (e.g. NUBASE2024) has superseded it.

**S2. NuDat 3.0 — `CANDIDATE — needs human approval` (PRIMARY, HIGH confidence it exists)**
- Reference: National Nuclear Data Center (NNDC), Brookhaven National Laboratory. "NuDat 3.0 database."
- URL: `https://www.nndc.bnl.gov/nudat3/` — **VERIFIED LIVE** during this research (page fetched; interactive chart of nuclides + decay-radiation search).
- What it backs: the decay mode (F2), decay radiation/energy (the ~0.1565 MeV beta endpoint), and an independently-browsable half-life value. NuDat draws from the **Evaluated Nuclear Structure Data File (ENSDF)**, the NNDC's maintained evaluated dataset. Wikipedia's Carbon-14 article cites NuDat 3.0 for the decay energy.
- Why useful as a SECOND primary alongside NUBASE2020: NuDat is the interactive, queryable view; NUBASE2020 is the published evaluation. Citing both (or either) is standard practice. NuDat lets a reviewer look up the C14 record directly without reading a journal paper.

**S3. IAEA LiveChart of Nuclides — `CANDIDATE — needs human approval` (PRIMARY, HIGH confidence it exists)**
- Reference: IAEA Nuclear Data Section, Vienna. "LiveChart of Nuclides."
- URL: `https://www-nds.iaea.org/relnsd/vcharthtml/VChartHTML.html` — **VERIFIED LIVE** during this research (page fetched; "Table of Nuclides - Nuclear structure and decay data," IAEA Nuclear Data Section footer present).
- What it backs: F1 (half-life) and F2 (decay mode), from an IAEA-maintained evaluation. A third independent authoritative database (intergovernmental). Useful as a cross-check or as the single source if the human prefers an IAEA reference over a Chinese-physics-journal DOI.
- Note: the more commonly linked path `.../VDVChart.html` returned 404; the **working** URL is `VChartHTML.html` (capitalization matters). Confirm the exact landing URL at approval time.

### Candidate educational / teaching-layer sources (for F3, F5, and the two-layer text)

**S4. LibreTexts — Nuclear Chemistry (hub) — `CANDIDATE — needs human approval` (HIGH confidence the hub exists; MEDIUM confidence on the exact subpage URL)**
- Reference: "Nuclear Chemistry," Supplemental Modules (Physical and Theoretical Chemistry), Chemistry LibreTexts.
- URL: `https://chem.libretexts.org/Bookshelves/Physical_and_Theoretical_Chemistry_Textbook_Maps/Supplemental_Modules_(Physical_and_Theoretical_Chemistry)/Nuclear_Chemistry` — **VERIFIED LIVE** during this research (page fetched; CC BY-NC-SA 4.0; subtopics listed: *Radioactivity*, *Nuclear Energetics and Stability*, *Fission and Fusion*, *Nuclear Kinetics*, *Applications of Nuclear Chemistry*).
- What it backs: F3 (the decay law / half-life math, under the *Nuclear Kinetics* subtopic) and the educational-layer explanation of half-life for the teaching text (under *Radioactivity*). Aligns with `spec.md`'s leaning toward LibreTexts as a source family ("Refer to the biochemistry libretext to plan the plot and paths" — though that line is about the *biochemistry* paths; for the *nuclear* half-life fact, a nuclear-chemistry LibreText is the appropriate family member).
- Caveat: the **specific subpage** for "Half-Life" (under Radioactivity) and the "decay law" (under Nuclear Kinetics) was NOT individually fetched — my URL guesses for the half-life subpage 404'd. The hub + subtopic structure is confirmed. **At approval time, fetch and confirm the exact subpage URL + that it states the decay law N = N₀·e^(−λt).**

**S5. Krane, K. S. — *Introductory Nuclear Physics* — `CANDIDATE — verify existence + edition + seek human approval` (LOW-MEDIUM confidence; NOT web-verified)**
- Reference (provisional): Krane, Kenneth S. *Introductory Nuclear Physics.* Wiley. (Commonly cited 1988 first edition; later editions may exist.)
- What it backs: F3 (the decay law, half-life, beta decay) at a standard-undergraduate-textbook level — a citable non-web source if the human prefers a print textbook over a LibreTexts page for the decay-law claim.
- **Honesty flag:** this is a well-known real textbook in my training data, but I did NOT web-verify its existence/edition/ISBN during this research. The instruction prohibits inventing DOIs/ISBNs, so none is given. The human should verify the exact edition + ISBN before approving. If a LibreTexts page (S4) covers the decay law adequately, this textbook candidate may be unnecessary.

### Sources considered and NOT recommended for this specific decision

| Source | Why not the lead candidate here (but may still be proposed for OTHER Phase 5 decisions) |
|--------|---------------------------------------------------------------------------------------------------|
| **IUPAC** (Commission on Isotopic Abundances and Atomic Weights, CIAAW) | IUPAC's domain is *natural isotopic abundances and atomic weights*, not nuclear half-lives. Not the right primary source for F1/F2. (Could be relevant elsewhere if a claim about C14 *natural abundance* is needed — see F-optional below.) |
| **NIST** (Physical Reference Data / XCOM) | NIST aggregates some nuclear data, but the authoritative *evaluations* for half-lives are NUBASE/ENSDF (hosted by NNDC, S2). Citing NUBASE2020 directly (S1) is cleaner than citing an aggregator. |
| **Wikipedia "Carbon-14"** | Tertiary source — useful to *find* the primary sources (which is how this research located NUBASE2020, NuDat 3.0) but NOT itself an approved source per the project's no-fabricated-science rule. The human should approve a primary/educational source, not Wikipedia. |

### An optional fact (only if the hero-intro/cast text mentions natural abundance)

**F-optional.** "C14 occurs naturally in trace amounts (~1.2 parts per trillion of atmospheric carbon)." If the hero-intro or cast text asserts C14's *natural abundance* (not required for the decay bad-ending framing), that claim would need its own source. Wikipedia cites NUBASE2020 and the global-carbon-budget literature for this, but the chain to a single clean primary source is less clear than for F1/F2. **`CANDIDATE — verify primary source at approval time`**; do not assert abundance unless a source is approved. (This fact is NOT needed for any of the framing options below; it is listed only for completeness.)

---

## Framing Options (for the human to choose)

For each option: **pros / cons / story-graph impact / all-4-endings reachability impact / per-claim approval load**.

### (a) DROP decay as a bad-ending trigger entirely

- **What:** Remove "radioactive decay" from the bad-ending pool. Bad endings are reached only via the spec's *other* triggers: lost connection, RNG cycle-trap → host death, breaking a critical residue/enzyme → host cannot survive (spec.md line 18).
- **Pros:**
  - Scientifically cleanest — no misleading timescale claim anywhere in the bad-ending text.
  - **Lowest per-claim approval load** for the decay decision: zero decay-*narrative* claims.
  - Simplifies the bad-ending pool and the story graph (one fewer sub-trigger to wire + balance).
- **Cons:**
  - **Spec deviation**: spec.md line 18 explicitly lists "radioactive decay" as a bad-ending trigger. Dropping it is a conscious, documented change to the authoritative spec — flag to the human and record in PROJECT.md Key Decisions.
  - Loses a dramatic beat and slightly weakens the "why C14" resonance (the tracking isotope's radioactivity becomes invisible). Note: C14's *tracking* role remains the primary in-game reason it's the hero, so this is a minor loss.
  - Does NOT eliminate ALL C14-radioactivity claims: if the hero-intro/cast text still mentions C14 *is* radioactive (F1, F2), those still need approval — just not the *bad-ending-timescale* claims (F3, F4, F5).
- **Story-graph impact:** removes one bad-ending sub-branch. Bad-tier reachability now depends entirely on the other triggers remaining reachable.
- **All-4-endings reachability impact:** **NEUTRAL IF** the other Bad triggers (cycle-trap-host-death, critical-residue-break, lost-connection) remain reachable for every character. This is a Phase 5.1 story-graph property this research cannot verify — **the chosen option must be paired with a Phase 5.1 reachability-checker confirmation that ≥1 Bad-ending trigger stays reachable per character.** Risk: if some character currently relies on *decay* as its only Bad-ending trigger, dropping decay breaks that character's Bad reachability. (Inspect the Phase 5.1 skeleton when it exists.)
- **Per-claim approval load:** ~0 decay-narrative claims. Hero-intro/cast radioactivity claims (F1, F2) only if those texts mention radioactivity.

### (b) TIME-COMPRESS — keep decay as a narrative device with explicit "we fast-forward time" framing

- **What:** Keep decay as a bad-ending trigger, but the transition into it is an explicit narrative time-skip ("eons pass... the hero, patient beyond measure, finally decays"). The time-compression is stated, not hidden.
- **Pros:**
  - Preserves the spec's trigger (no spec deviation).
  - The dramatic decay beat is preserved.
  - Honest framing (the time-skip is explicit), addressing the timescale-mismatch problem by *narrating around* it.
- **Cons:**
  - Tonal mismatch with the rest of the game, which happens at biological timescale: "this respiration step took seconds; the decay ending took millennia" is a jarring jump. An educator may still ask "why is decay a bad ending at all if it takes 5,700 years?"
  - The time-skip device must be **unmistakably** explicit, or it re-creates the misleading-timescale pitfall it's meant to fix.
  - Requires per-claim approval of F1, F2, and the time-skip caveat's embedded "5,700 years" number.
- **Story-graph impact:** keeps the decay bad-ending branch; adds a "time-skip" transition edge/framing on the path into it.
- **All-4-endings reachability impact:** neutral-to-positive (keeps a Bad trigger, contributing to Bad-tier reachability).
- **Per-claim approval load:** F1 (half-life), F2 (decay mode), and the embedded "5,700 years" in the time-skip text. The "fast-forward" framing itself is game design (not a scientific claim), but its embedded number inherits F1's approval. ~3 claims.

### (c) REFRAME AS TEACHING MOMENT — keep decay, make the teaching layer say it's a dramatic device (PITFALLS.md's recommended mitigation)

- **What:** Keep decay as a bad-ending trigger, but the bad-ending's **teaching layer** explicitly states: "C14's half-life is ~5,700 years, so during one respiration cycle decay is essentially impossible (~10⁻¹² probability); we include decay as a dramatic device. C14's *long* half-life is precisely why it's a useful tracking isotope." The dramatic layer keeps the stakes; the teaching layer keeps the science honest.
- **Pros:**
  - **Best fit for the educator audience** — turns the pitfall into a pedagogical feature. An educator reviewing the cast will applaud rather than flag this.
  - Preserves the spec's trigger (no spec deviation).
  - Aligns with the project's **two-layer text design** (dramatic + teaching) — this is exactly what the teaching layer is for.
  - Reinforces the soul-jump/identity framing (Pitfall 4): C14 is a *tracking label*, and the decay teaching moment explains *why* a long-lived isotope makes a good tracker — thematically consistent with "C14 is a label, not a fate."
  - Matches PITFALLS.md Pitfall 9's own recommended mitigation.
- **Cons:**
  - **Highest per-claim approval load** of the options: F1, F2, F3 (decay law), F4 (the ~10⁻¹² probability claim), F5 (the "long half-life = good tracker" conceptual claim).
  - F4 requires the human to **fix a defensible comparison timescale** ("one respiration cycle" — seconds? minutes? the duration needs a biochem source or a stated definition) before the "~10⁻¹²" number can be approved.
  - Most two-layer authoring work (dramatic + teaching text for the decay ending).
- **Story-graph impact:** keeps the decay bad-ending branch; the branch's teaching-layer text carries the disclaimer. Reachability unchanged.
- **All-4-endings reachability impact:** neutral-to-positive (keeps a Bad trigger).
- **Per-claim approval load:** ~5–6 claims (F1, F2, F3, F4, F5, and the disclaimer's embedded numbers). See the per-claim inventory below.

### (d-i) Decay only as a "what-if" SIDE NOTE / glossary entry, NOT a gameplay trigger

- **What:** Drop decay from the *bad-ending pool* (like option a), but the hero-intro / cast / in-game glossary still teaches the *fact* that C14 is radioactive with a ~5,700-yr half-life (as flavor about the tracking isotope), without ever making it a gameplay outcome.
- **Pros:**
  - Clean separation: gameplay stays at biological timescale only; radioactivity is factual flavor, not a threat.
  - Still teaches the real fact (F1, F2) — captures the educational value without the timescale-mismatch problem.
  - Lower claim load than (c): just F1, F2, and F5 (no F3/F4 — no "probability during gameplay" claim is made because decay is never a gameplay event).
- **Cons:**
  - Spec deviation (drops decay as a *trigger*, though not as a *fact*) — document in PROJECT.md.
  - Less dramatic (no "decay" bad-ending at all).
- **Story-graph impact:** same as (a) for the bad-ending pool; adds a glossary/hero-intro fact node.
- **All-4-endings reachability impact:** same as (a) — neutral IF other Bad triggers cover; verify in Phase 5.1.
- **Per-claim approval load:** ~3 claims (F1, F2, F5).

### (d-ii) Decay tied to a "DEEP-TIME EPILOGUE" (outside the 4 ending tiers)

- **What:** Reframe decay NOT as a "bad" ending but as a distinct post-credits / special "deep-time" epilogue the player can reach under a rare condition (e.g. a special seed, or after seeing all 4 standard endings). The epilogue fast-forwards millennia and the hero decays — narratively framed as "the very long view, far beyond one respiration cycle," outside the 4-tier model.
- **Pros:**
  - Preserves the decay narrative beat in a tonally-appropriate place (epilogue, not gameplay) — the timescale mismatch becomes a *feature* ("this is what happens on geological time").
  - **Does not touch the 4-ending-tier reachability invariant** — the epilogue is orthogonal to the 4 tiers, so "all 4 endings reachable per character" is unaffected.
  - Pedagogically clean: explicitly contrasts biological timescale (the 4 endings) with nuclear timescale (the epilogue).
- **Cons:**
  - Adds scope: a 5th ending-type (epilogue) outside the 4-tier model — needs design care to keep it clearly *separate* from the 4 tiers (so it doesn't accidentally become a 5th ending that breaks "all 4 reachable").
  - Spec deviation (decay moves out of the "bad ending" list into an epilogue).
  - Requires an access mechanism (seed? unlock? all-endings-seen?) — an extra design + implementation surface.
- **Story-graph impact:** adds an epilogue node outside the 4-tier endings; bad-ending pool loses decay (like a/d-i).
- **All-4-endings reachability impact:** neutral (epilogue is orthogonal; Bad still reachable via other triggers; verify in Phase 5.1).
- **Per-claim approval load:** ~3–4 claims (F1, F2, F3, and the embedded "millennia" framing number, which inherits F1).

### (d-iii) Decay as an explicit EDUCATOR-DEMO TOGGLE (not a live gameplay trigger)

- **What:** An educator-toggle in settings that, when enabled, runs a "decay demo" illustrating the half-life + decay-probability math with the explicit "this is a teaching demo, not a live gameplay risk" framing. Off by default; the bad-ending pool does not include decay.
- **Pros:**
  - **Strongest teaching fit**: the decay-rate lesson is opt-in and unambiguous, and the seedable RNG makes the demo reproducible for classrooms (aligns with the seedable-RNG requirement).
  - Default gameplay is biologically-timescale-clean.
- **Cons:**
  - Adds a feature (educator toggle + demo) — scope beyond a content decision.
  - Spec deviation (decay not a default bad-ending trigger).
- **Story-graph impact:** bad-ending pool loses decay; adds an out-of-band demo path (not a story-graph node — a settings-driven demo).
- **All-4-endings reachability impact:** neutral (Bad via other triggers; demo is orthogonal; verify in Phase 5.1).
- **Per-claim approval load:** ~4–5 claims (F1, F2, F3, F4, the demo framing).

### Option comparison at a glance

| Option | Spec deviation? | Bad-tier reachability | Per-claim load | Educator fit | Notes |
|--------|-----------------|----------------------|----------------|--------------|-------|
| (a) DROP | Yes (removes trigger) | Neutral IF other triggers cover | Lowest (~0–2) | OK (no decay lesson) | Cleanest science |
| (b) TIME-COMPRESS | No | Neutral+ | Medium (~3) | Mixed (tonal jump) | Honest but jarring |
| (c) TEACHING MOMENT | No | Neutral+ | Highest (~5–6) | **Best** (applauds) | Matches PITFALLS.md mitigation |
| (d-i) SIDE-NOTE | Yes (removes trigger) | Neutral IF other triggers cover | Low (~3) | Good | Fact preserved, trigger dropped |
| (d-ii) DEEP-TIME EPILOGUE | Yes (moves to epilogue) | Neutral (orthogonal) | Medium (~3–4) | Good (timescale contrast) | Adds a 5th ending-type |
| (d-iii) EDUCATOR TOGGLE | Yes (removes default trigger) | Neutral (orthogonal) | Medium (~4–5) | Good (opt-in demo) | Adds a feature |

---

## Recommendation (advisory — the human decides)

**Lean: Option (c) REFRAME AS TEACHING MOMENT**, with this concrete implementation:
- The decay bad-ending's **teaching layer** carries: (i) "C14 has a half-life of ~5,700 years [F1, source NUBASE2020]"; (ii) "during one respiration cycle (seconds–minutes), the probability a single C14 atom decays is ~10⁻¹² — effectively impossible [F4, derived from F1+F3]"; (iii) "we include decay as a dramatic device, not a realistic in-game risk"; (iv) "C14's *long* half-life is exactly why it's a good tracking isotope for following carbon through a pathway [F5]". The dramatic layer keeps the stakes ("the hero, patient beyond measure, finally decays…").
- Approve sources in this order: **S1 (NUBASE2020)** for F1/F2 → **S2 (NuDat 3.0)** as the queryable cross-check → **S4 (LibreTexts Nuclear Chemistry)** for F3/F5 teaching text. (S3 IAEA LiveChart optional as a third cross-check; S5 Krane textbook only if the human prefers a print source for F3.)

**The key tradeoff to flag (the reason this is advisory, not a fait accompli):**
- (c) maximizes **educational value** and is the only option that *teaches* decay rates (the others avoid, compress, or hide the issue) — best for the educator audience.
- (c) carries the **highest per-claim approval load** (~5–6 claims) and requires the human to fix a defensible comparison timescale for F4.
- **BUT** the absolute claim count for this single bad-ending sub-trigger is small relative to the hundreds of claims in the full content scope (Pitfall 7 estimates ~400+). The throughput argument that drives the *batch-by-source* decision (Pitfall 7) is weak *here*: saving ~2–3 claims is negligible against the project total. So the educational-value argument should dominate for this specific decision.
- If the human nonetheless wants the **lowest-friction path**: choose **(a) DROP** or **(d-i) SIDE-NOTE**. (d-i) is the better of those two — it still teaches the real C14-radioactivity fact in the glossary (preserving educational value) while removing the timescale-mismatched *trigger*. If the human wants the **strongest teaching artifact** and accepts the load: choose **(c)**, or **(d-iii) EDUCATOR TOGGLE** if a reproducible classroom demo is worth the feature scope.

**Mandatory pairing for ANY chosen option:** whichever option is chosen, **Phase 5.1's reachability checker must confirm ≥1 Bad-ending trigger remains reachable per character** (this research cannot verify it; it's a story-graph property decided when the glucose skeleton is designed). If any character currently relies on *decay* as its only Bad trigger, options (a)/(d-i)/(d-ii)/(d-iii) would break that character's Bad reachability unless another trigger is added. Flag this dependency to the Phase 5.1 designer.

---

## If Decay Kept: Per-Claim Inventory (claim_id → claim text → candidate source)

The claims that would land in the bad-ending (and hero-intro/glossary) narrative text if decay is kept (options b, c, d-ii, d-iii; plus the F1/F2/F5 hero-intro claims that apply under (d-i) too). Format matches the Phase 1 claims-registry contract (`data/claims.jsonl`: `{claim, source, source_id, status, ...}`).

| claim_id | Claim text (to be approved) | Candidate source | Source type | Notes |
|----------|-----------------------------|-----------------|------------|-------|
| **C14-HL-01** | "Carbon-14 has a half-life of approximately 5,700 years (evaluated value 5700 ± 30 years)." | S1: NUBASE2020 (Kondev et al., 2021, *Chinese Physics C* 45(3) 030001, DOI 10.1088/1674-1137/abddae) — **DOI verified to resolve** | PRIMARY | **Value reconciliation needed**: project docs (PITFALLS.md, PROJECT.md) quote "~5,730 years" (the older Cambridge half-life, Godwin 1962). NUBASE2020's current evaluated value is 5700 ± 30. The human must approve a *specific value + source pair*; recommend the NUBASE2020 value (5700 ± 30) as primary, and note the 5730 figure is the older Cambridge value. Do not ship both values without explanation. |
| **C14-DM-01** | "Carbon-14 decays to nitrogen-14 via beta-minus (β⁻) emission: ¹⁴C → ¹⁴N + e⁻ + ν̄ₑ, with decay energy ~0.1565 MeV." | S1: NUBASE2020 (decay mode) + S2: NuDat 3.0 (NNDC/BNL, decay radiation/energy) — both **pages/DOI verified** | PRIMARY pair | The decay equation + energy are standard; cite NUBASE2020 for the mode, NuDat 3.0 for the radiation energy. |
| **C14-DL-01** | "Radioactive decay follows the law N(t) = N₀·e^(−λt), where the decay constant λ = ln(2)/t½." | S4: LibreTexts Nuclear Chemistry (Nuclear Kinetics subtopic) — **hub verified live**; verify exact subpage at approval. Alt: S5: Krane, *Introductory Nuclear Physics* (verify edition) | EDUCATIONAL / TEXTBOOK | Textbook-level standard physics. Needed only if the narrative states the decay *law* (options c, d-iii) — not needed for (a)/(b)/(d-i) unless the time-skip text names the law. |
| **C14-PROB-01** | "The probability that a single C14 atom decays during one respiration cycle (~seconds–minutes) is ~10⁻¹² — effectively impossible." | **DERIVED** from C14-HL-01 + C14-DL-01 + a defined "respiration cycle" duration. The duration needs its own biochem source. | DERIVED | This is *arithmetic*, not a sourced claim. The registry entry should record it as `derived_from: [C14-HL-01, C14-DL-01, C14-TIME-01]`. Approve the *inputs* first. See computation table below. |
| **C14-PROB-02** (optional) | "Over a human lifetime (~80 years), the probability a single C14 atom decays is ~1% (~10⁻²)." | DERIVED from C14-HL-01 + C14-DL-01 + "80 years" (a stated assumption, not a sourced biochem fact). | DERIVED | Only if the teaching text makes this comparison. Optional — the stronger comparison is the respiration-cycle one (C14-PROB-01). |
| **C14-TIME-01** (supporting) | "A single respiration-cycle step in this game represents a timescale of seconds to minutes." | A biochem/cell-biology source for respiration timescales (e.g. a LibreTexts biochem chapter on respiration rate) — **CANDIDATE — propose + approve in the glucose critical-path source batch** (Phase 5 SC#4), not separately here. | BIOCHEM | This is the timescale definition that makes C14-PROB-01 concrete. It belongs to the *biochem* source family (the spec's "biochemistry libretext"), not the nuclear family. Flag it as a cross-decision dependency: the decay framing leans on a biochem timescale source approved elsewhere in Phase 5. |
| **C14-TRACK-01** | "C14's long half-life is precisely why it is useful as a tracking/tracer isotope — it persists long enough to follow carbon through a pathway without significant loss." | S4: LibreTexts (a radiocarbon-dating or isotope-tracer section) — **CANDIDATE — verify exact page**. Alt: a biochem textbook's "carbon labeling / isotope tracers" section — **CANDIDATE**. | EDUCATIONAL / CONCEPTUAL | This is the conceptual claim that ties the decay fact to the hero's *identity* (tracking isotope). Needed for option (c)'s teaching moment and (d-i)'s glossary. Verify the specific source page at approval. |
| **C14-DD-01** (game-design, mixed) | "The decay bad-ending is a dramatic device; decay does not realistically occur during one respiration cycle." | Mixed: the embedded scientific content = C14-PROB-01; the "dramatic device" framing = game design (not a scientific claim). | MIXED | The registry entry should link the embedded scientific claim to C14-PROB-01; the framing itself needs no source but must not introduce unsourced numbers. |
| **C14-AB-01** (optional, only if abundance is mentioned) | "C14 occurs naturally in trace amounts (~1.2 parts per trillion of atmospheric carbon)." | Wikipedia cites NUBASE2020 + global-carbon-budget literature; **the clean primary source for the abundance figure is less clear than for F1/F2 — `CANDIDATE — verify primary source`** before asserting. | PRIMARY (TBD) | NOT needed for any framing option. Listed only for completeness if the hero-intro mentions natural abundance. |

### The C14-PROB-01 computation (for transparency — NOT a sourced claim)

Using the decay law P(decay in time t) = 1 − e^(−λt) ≈ λt for λt ≪ 1, with λ = ln(2)/t½ and t½ = 5700 yr (NUBASE2020):

| Timescale (t) | P(single C14 atom decays) | Orders of magnitude | Gameplay/biological relevance |
|---------------|---------------------------|---------------------|------------------------------|
| 1 second | ~3.9 × 10⁻¹² | ~10⁻¹² | One enzymatic step (actual gameplay timescale) |
| 1 minute | ~2.3 × 10⁻¹⁰ | ~10⁻¹⁰ | One "playthrough step" (narrative timescale) |
| 1 hour | ~1.4 × 10⁻⁸ | ~10⁻⁸ | A short host-cell event |
| 1 day | ~3.3 × 10⁻⁷ | ~10⁻⁷ | A long host-cell event |
| 1 year | ~1.2 × 10⁻⁴ | ~10⁻⁴ | A short-lived organism's lifetime |
| 10 years | ~1.2 × 10⁻³ | ~10⁻³ | A medium-lived organism |
| 80 years (human lifetime) | ~9.7 × 10⁻³ (~1%) | ~10⁻² | A long-lived host |
| 1000 years | ~11.5% | ~10⁻¹ | Far beyond any host |
| 5700 years (one half-life) | 50% | 10⁻⁰·⁵ | By definition |

**Important correction to PITFALLS.md:** PITFALLS.md quotes the decay probability as "~10⁻⁵ to 10⁻³" for "hours to years." The computation above shows the actual range is ~10⁻⁸ (hours) to ~10⁻⁴ (one year) — PITFALLS.md's range is closer to "weeks to a decade." More importantly, for the **actual gameplay timescale (seconds–minutes per step)**, the probability is ~10⁻¹² to ~10⁻¹⁰ — **~5–7 orders of magnitude smaller** than PITFALLS.md's quoted range. This *strengthens* the "essentially zero" claim for the gameplay framing: the realistic per-step decay probability is ~1 in a trillion, not ~1 in a hundred thousand. The teaching-layer text (option c) can state this concretely and accurately, which is more pedagogically powerful than the vague "essentially zero." (This correction does not change any decision; it sharpens option (c)'s teaching text. The numbers above are reproducible arithmetic from C14-HL-01 + C14-DL-01 — not independent claims.)

---

## Boundary with Pitfall 4 (soul-jump) — confirm independence

**The two decisions are INDEPENDENT. Do not conflate them.**

| | Pitfall 4 (RESOLVED 2026-08-13) | Pitfall 9 (THIS decision — pending) |
|---|---------------------------------|--------------------------------------|
| **Question** | Where does the carbon *chemically* go? Does the carbon body become ATP? | Can the C14 nucleus *nuclearly* decay during the game? At what timescale? |
| **Domain** | Biochemistry — carbon fate through respiration | Nuclear physics — radioactive decay kinetics |
| **Resolution** | Soul-jump reframing: the hero's *electrons* (the narrative "soul") are harvested into ATP via the ETC → ATP synthase after the RNG-weighted TCA path; the carbon body is released as CO2. C14 is a *tracking label*, not a fate determinant. | Pending: drop / time-compress / reframe / side-note / epilogue / toggle (this research). |
| **What changes about the hero** | The carbon body's *chemical* location (exits as CO2) vs its electrons' fate (→ ATP). The hero **remains a carbon atom**. | IF decay is kept: the hero's *nucleus* transmutes C → N (it **stops being a carbon atom**, becomes a nitrogen atom). |
| **Timescale** | Biological (seconds–minutes per step; the playthrough) | Nuclear (~5,700-yr half-life; the playthrough is ~10⁻¹² of a half-life) |

**Why they don't conflict:**
1. Pitfall 4 is about *chemical fate* (carbon → CO2 vs → ATP-carbon). Pitfall 9 is about *nuclear transformation* (C14 → N14). These are different physical processes at different timescales.
2. The soul-jump reframing says the carbon body exits as CO2 (Normal/True endings) and the electrons are harvested (True ending). A C14 atom that exits as CO2 is **still C14 and still radioactive** — it just hasn't decayed during the game. The decay bad-ending is a *separate branch* where the nucleus transmutes, which is a categorically different event from any chemical-fate ending.
3. **Consistency note for the human (important):** IF decay is KEPT (options b, c, d-ii, d-iii), the decay bad-ending changes the hero's **element** (C → N) — a stronger transformation than the chemical-fate endings (which keep the carbon as carbon). The two-layer text must clearly distinguish "your carbon body was released as CO2" (chemical fate, Pitfall 4) from "your nucleus transmuted into nitrogen" (nuclear decay, Pitfall 9). They are not the same event and must not be described with overlapping language. The soul-jump framing (electrons = "soul") and the decay framing (nucleus transmutes) are about *different parts of the atom* — narratively, the decay ending is "the hero's body changes identity," which is a distinct beat from "the hero's soul is harvested."
4. **Preclusion relationship:** decay is a *Bad* ending; the soul-jump arc (True ending) requires reaching the ETC. If the hero decays (Bad), the soul-jump never happens — the soul never reaches ATP. So decay *precludes* the True-ending soul-jump, consistent with it being a Bad ending. No conflict; just a terminal-branch relationship.
5. **Do NOT revisit Pitfall 4.** Per AGENTS.md, the soul-jump reframing is settled. This Pitfall 9 research does not reopen the carbon-fate question; it treats the soul-jump as settled context and addresses only the decay-timescale question.

---

## Open Questions for the Human

These are the specific decisions / verifications the human must make or commission. This research does NOT resolve them.

1. **Which framing option?** (a) DROP / (b) TIME-COMPRESS / (c) TEACHING MOMENT / (d-i) SIDE-NOTE / (d-ii) DEEP-TIME EPILOGUE / (d-iii) EDUCATOR TOGGLE. Advisory lean: (c). See Recommendation + tradeoff.

2. **Which half-life VALUE + source pair to approve?** The project docs quote "~5,730 years" (older Cambridge value). NUBASE2020's current evaluated value is **5700 ± 30 years**. Recommend approving the NUBASE2020 value (C14-HL-01) as primary and explicitly noting the 5730 figure is the older Cambridge half-life, so the shipped text doesn't silently carry a superseded value. **The human must pick one value + one source.**

3. **Is S1 (NUBASE2020) the primary source, or does the human prefer S3 (IAEA LiveChart) or S2 (NuDat 3.0) as the single cited source?** All three are real and verified live/resolvable. NUBASE2020 is the *published evaluation* (most citable); NuDat 3.0 and IAEA LiveChart are the *queryable databases* (most reviewer-friendly). Recommend NUBASE2020 as primary + NuDat 3.0 as cross-check, but the human decides.

4. **Freshness check: is NUBASE2020 still the current NUBASE evaluation?** Wikipedia (edited 2026-07-17) still cites it — a reasonable signal. But the human should confirm at approval time whether a newer evaluation (e.g. NUBASE2024) has superseded it and whether the C14 value changed.

5. **For option (c)/(d-iii): what is the approved "respiration cycle" timescale (C14-TIME-01)?** The "~10⁻¹²" probability (C14-PROB-01) depends on a defined comparison timescale (seconds? minutes?). This is a *biochem* source (respiration rate), to be approved in the Phase 5 glucose critical-path source batch (SC#4), not separately here. Flag: the decay framing's strongest claim leans on a biochem source approved *elsewhere* in Phase 5.

6. **For F5 (C14-TRACK-01, "long half-life = good tracker"): which source?** Needs a radiocarbon-dating or isotope-tracer reference. LibreTexts (S4) likely has a suitable page; verify the exact page at approval. This conceptual claim is what makes option (c) pedagogically *connect* the decay fact to the hero's identity.

7. **Spec-deviation documentation (for options a, d-i, d-ii, d-iii):** if the human chooses an option that drops/moves decay as a trigger, the change must be recorded in PROJECT.md Key Decisions and the spec.md line 18 reference annotated in-place (as was done for Pitfall 4 on 2026-08-13). This research does not edit those files.

8. **Reachability verification (mandatory for any option):** Phase 5.1's reachability checker must confirm ≥1 Bad-ending trigger remains reachable per character after this decision. This research cannot verify it (story-graph property). If any character currently relies on *decay* as its only Bad trigger, the chosen option (if it drops/moves decay) needs a replacement trigger added — flag to the Phase 5.1 designer.

9. **AMDC website flakiness:** the AMDC homepage (`https://www.amdc.in2p3.fr/`) returned transport errors during research. The NUBASE2020 *paper* (via DOI) is the citable artifact and resolved fine. Do not block approval on the AMDC website being up; cite the paper, not the website.

10. **Optional C14-AB-01 (natural abundance):** only if the hero-intro/cast text mentions C14's natural abundance. The clean primary source is less clear than for F1/F2 — verify before asserting. Not needed for any framing option.

---

## Sources

### Primary (HIGH confidence — verified live/resolvable during this research)
- **S1: NUBASE2020** — Kondev, F. G.; Wang, M.; Huang, W. J.; Naimi, S.; Audi, G. (2021). "The NUBASE2020 evaluation of nuclear physics properties." *Chinese Physics C*, 45(3), 030001. DOI `10.1088/1674-1137/abddae` — **DOI verified to resolve** via `https://doi.org/10.1088/1674-1137/abddae`. Cited by Wikipedia's Carbon-14 article for the "5700 ± 30 years" half-life. Backs F1, F2.
- **S2: NuDat 3.0** — National Nuclear Data Center (NNDC), Brookhaven National Laboratory. `https://www.nndc.bnl.gov/nudat3/` — **page fetched live**. Interactive chart of nuclides drawing from ENSDF. Backs F2 (decay mode/radiation/energy).
- **S3: IAEA LiveChart of Nuclides** — IAEA Nuclear Data Section, Vienna. `https://www-nds.iaea.org/relnsd/vcharthtml/VChartHTML.html` — **page fetched live** (note: `VChartHTML.html`, not `VDVChart.html` which 404'd). Backs F1, F2.

### Educational (HIGH confidence the hub exists; MEDIUM on exact subpage)
- **S4: LibreTexts Nuclear Chemistry** — "Nuclear Chemistry," Supplemental Modules (Physical and Theoretical Chemistry), Chemistry LibreTexts. `https://chem.libretexts.org/Bookshelves/Physical_and_Theoretical_Chemistry_Textbook_Maps/Supplemental_Modules_(Physical_and_Theoretical_Chemistry)/Nuclear_Chemistry` — **hub fetched live**, CC BY-NC-SA 4.0. Subtopics: Radioactivity, Nuclear Kinetics (these cover F3 and the teaching-layer half-life explanation). **Specific "Half-Life" / "decay law" subpage URLs NOT individually verified — confirm at approval time.** Aligns with spec.md's LibreTexts leaning.

### Textbook (LOW-MEDIUM confidence — NOT web-verified; flag for verification)
- **S5: Krane, K. S. — *Introductory Nuclear Physics*** — Wiley. Commonly cited 1988 first edition; later editions may exist. Backs F3 (decay law, half-life, beta decay) at undergraduate-textbook level. **CANDIDATE — verify exact edition + ISBN before approving. No ISBN/DOI asserted here (per no-fabricated-science rule). Only needed if the human prefers a print source over S4 for the decay-law claim.**

### Used for discovery (NOT approved sources — tertiary, not citable per project rules)
- **Wikipedia "Carbon-14"** (`https://en.wikipedia.org/wiki/Carbon-14`, last edited 2026-07-17) — used to *locate* the primary sources (NUBASE2020, NuDat 3.0) via its reference list. NOT itself an approved source. Also used to confirm the half-life value nuance (5700±30 NUBASE2020 vs 5730 Cambridge).

---

## Metadata

**Confidence breakdown:**
- Existence/resolvability of primary nuclear-data sources (S1, S2, S3): **HIGH** — DOI verified + pages fetched live.
- The half-life value (5700±30, NUBASE2020): **HIGH** — DOI verified, Wikipedia (tertiary) cross-references it; freshness against a possible NUBASE2024 flagged.
- Educational-source hub (S4 LibreTexts): **HIGH** (hub) / **MEDIUM** (exact subpage).
- Textbook candidate (S5 Krane): **LOW-MEDIUM** — not web-verified; flagged for human verification.
- Decay-probability numbers (C14-PROB-01/02): **N/A (derived)** — reproducible arithmetic from F1+F3, not a sourced claim.
- The "5730 years" figure in existing project docs vs "5700±30" in NUBASE2020: **MEDIUM** discrepancy flagged for human reconciliation.

**Research date:** 2026-08-15
**Valid until:** 2026-09-14 (30 days — stable domain; the only freshness risk is a possible newer NUBASE evaluation, flagged in Open Question #4)
