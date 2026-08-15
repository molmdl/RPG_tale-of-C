# Phase 5 Research — Anaerobic Pathway Framing

**Researched:** 2026-08-15
**Aspect:** Anaerobic-pathway framing decision (host-condition branch / separate scenario / bad-ending trigger) — ONE of the 4 Phase 5 science-framing decisions
**Phase goal addressed:** Success Criterion #3 — "The anaerobic-pathway framing is resolved (host-condition branch / separate scenario / bad-ending trigger) and documented in PROJECT.md Key Decisions."
**Downstream consumer:** Phase 5.1 (Story Graph Design — the anaerobic branch topology) and Phase 9 (Anaerobic Pathway + Full Cast — anaerobic framing implemented).
**Decision owner:** THE HUMAN. This document GATHERS options + REAL candidate sources FOR THE HUMAN to decide. It does NOT decide. It does NOT approve any source. Every candidate source below is marked `CANDIDATE — needs human approval`.
**Confidence:** HIGH for the core biochemistry (five LibreTexts pages were fetched LIVE during research; the O2-as-terminal-acceptor + pyruvate→lactate/ethanol-without-O2 facts are stated explicitly on those pages). MEDIUM for the textbook candidates (Lehninger / Garrett & Grisham are confirmed to EXIST because the verified LibreTexts pages cite them in their reference lists, but the exact edition/ISBN/chapter was NOT web-verified here). LOW for the "fatty acids are obligately aerobic" claim as a single quotable sentence — the MECHANISM is fully established from the verified pages, but an explicit one-line textbook statement still needs to be located at approval time (see F-FAB-01).

---

> **No-fabricated-science invariant (read first).** Per `spec.md` and `AGENTS.md`, every scientific claim and citation must be verified against a real source AND explicitly human-approved per claim before landing in code/content. This research **proposes real, identifiable candidate sources** for the human to approve later. It does NOT invent DOIs, PDB IDs, ISBNs, or references. **Zero DOIs/ISBNs are asserted in this document.** All five primary sources are CC BY-NC-SA 4.0 LibreTexts web pages whose URLs were fetched live during research (verification timestamps in the Sources section). The two textbook candidates (Lehninger; Garrett & Grisham) are flagged `CANDIDATE — verify edition + chapter + seek human approval` because their existence is confirmed (the verified LibreTexts pages cite them) but their exact edition/chapter was not web-verified here.

---

## Summary

The anaerobic decision is **not** a localized framing tweak like the C14-decay decision (sibling `05-RESEARCH-c14-decay.md`). It collides head-on with **two project invariants at once**, and the human needs to understand both collisions before choosing:

1. **The soul-jump / ETC collision (Pitfall 4, RESOLVED — but anaerobic re-opens the wound).** The True ending is defined as "the hero's electrons (the 'soul') are harvested into ATP via the ETC → ATP synthase after the RNG-weighted TCA path." The ETC's terminal electron acceptor is **oxygen** (verified: LibreTexts *Electron Transport Chain* + *Biological Oxidation* pages state this explicitly — Complex IV transfers electrons to O₂ to make water; "molecular oxygen as the final electron acceptor at the end"; oxidative phosphorylation forms ATP "as a result of the transfer of electrons" to O₂). **Without O₂, the ETC cannot run, no proton gradient, no ATP synthase, no electron-harvest into ATP.** Therefore the True ending (soul-jump) is **biochemically unreachable under anaerobic conditions.** This is not a framing choice — it is settled chemistry. Any anaerobic framing that expects the True ending to be reachable is scientifically wrong and will fail a per-claim review.

2. **The "all 4 endings reachable for every character" collision.** The v1 success measure (PROJECT.md) requires all 4 ending tiers reachable per character. The science says:
   - **Glucose** has a clean anaerobic path (lactic fermentation: pyruvate→lactate, no CO₂; ethanolic fermentation: pyruvate→acetaldehyde+CO₂→ethanol) — BUT can reach at most **3/4 endings anaerobically** (no True, because no ETC). Lactate retains the carbon (Good-ish); ethanol releases CO₂ (Normal-ish); host energy crisis (Bad).
   - **Fatty acid** has **no anaerobic catabolic path at all** in a mammalian/yeast host: β-oxidation produces FADH₂ (via Acyl-CoA dehydrogenase) and NADH (via Hydroxyacyl-CoA dehydrogenase), both of which can ONLY be re-oxidized by the ETC (the FADH₂ specifically via ETF→ubiquinone→Complex III/IV→O₂). Fermentation regenerates NAD⁺ from pyruvate — it does **not** regenerate FAD. So β-oxidation is mechanistically **obligately aerobic**. A "fatty-acid anaerobic branch" would strand the hero at the entry enzyme — a reachability dead-end.
   - **Alcohol** is **paradoxical** anaerobically: ethanol is itself the *end product* of alcoholic fermentation (pyruvate→acetaldehyde→ethanol via pyruvate decarboxylase + alcohol dehydrogenase). The alcohol character's aerobic path runs ADH in the *oxidizing* direction (ethanol→acetaldehyde→acetate→acetyl-CoA→TCA→ETC). Anaerobically, the energetically favorable direction is the *reverse* (toward ethanol). So "anaerobic alcohol character" has no forward metabolism — it's already at fermentation's destination.

**The crux:** the v1 invariant "all 4 endings reachable for every character" can only be satisfied **aerobically**. Anaerobic paths reach at most 3/4 (glucose) or 0/4 of the aerobic-style endings (fatty acid, alcohol). This is not a design failure to fix — it is the science. The decision the human faces is therefore **how to scope the invariant relative to anaerobic**: keep "all 4 reachable" as an **aerobic-only** property and treat anaerobic as a reduced/separate/failure scope (options b/c/d), or try to expand the host organism to an anaerobic-respiration bacterium (non-O₂ terminal acceptor) to recover a True-variant — high scope, conflicts with the mammalian/yeast framing of the 3 characters.

**Primary recommendation (advisory):** Option **(c) BAD-ENDING TRIGGER** (oxygen depletion → host energy crisis / host death), OR a **(c+d) hybrid** where anaerobic is primarily a Bad-ending trigger for the fatty-acid and alcohol characters (which cannot ferment) AND a player-facing CHOICE for glucose only (lactic = Good-ish retained-carbon ending; ethanolic = Normal-ish CO₂ ending; energy-crisis = Bad). This (i) respects the science (no fabricated anaerobic True ending), (ii) keeps the "all 4 reachable" invariant **aerobically** for all 3 characters, (iii) gives glucose a pedagogically rich anaerobic branch (the educator audience's main interest in anaerobic is fermentation), and (iv) sidesteps the fatty-acid/alcohol reachability dead-ends by making oxygen-depletion a Bad-ending path for them rather than a broken branch. The key **tradeoff flagged**: (c/c+d) means the v1 success measure must be **re-worded** from "all 4 endings reachable for every character" to "all 4 endings reachable **aerobically** for every character; anaerobic is a reduced-scope branch (glucose) / failure mode (fatty acid, alcohol)." That re-wording is a spec-adjacent change the human must approve and record in PROJECT.md Key Decisions. If the human instead insists that anaerobic must reach all 4 endings for all 3 characters, **no option on the table can deliver that without fabricating science** — the only path would be option (e) EXPAND HOST TO ANAEROBIC-RESPIRATION ORGANISM (high scope, new host, conflicts with the 3-character framing).

---

## The Science per Character (candidate sources — each `CANDIDATE — needs human approval`)

A terminological note the human should fix early: "anaerobic respiration" and "fermentation" are **different processes**. The verified *Fermentation* page (S-FERM) states: respiration uses an electron transport chain to a terminal electron acceptor (O₂ aerobically; in anaerobic organisms, "various metals like Fe(III), Mn(IV) and Co(III), CO₂, nitrate, sulfur"); **fermentation** is the *alternative* — it recycles NADH→NAD⁺ by reducing an organic molecule (pyruvate→lactate or acetaldehyde→ethanol), with **no ETC and no external terminal acceptor**. The game's mammalian/yeast host context uses **fermentation**, not anaerobic respiration. This distinction is load-bearing for the soul-jump tension (see that section).

### Glucose — anaerobic = fermentation (lactic OR ethanolic)

| Fact | Status |
|------|--------|
| G1 | Glycolysis yields pyruvate; pyruvate's fate depends on O₂ presence | Verified live (S-GLY, S-FERM) |
| G2 | Without O₂, pyruvate is reduced to **lactate** via **lactate dehydrogenase**, NADH is the reducing agent, NAD⁺ is regenerated — **no CO₂ released** | Verified live (S-FERM, S-BIOX) |
| G3 | Without O₂ (yeast), pyruvate → **acetaldehyde + CO₂** via **pyruvate decarboxylase**, then acetaldehyde → **ethanol** via **alcohol dehydrogenase**, regenerating NAD⁺ — **CO₂ IS released** | Verified live (S-FERM) |
| G4 | Fermentation recycles NAD⁺ so glycolysis can continue; energy yield is "much less than... the TCA cycle and ETC" | Verified live (S-FERM) |
| G5 | Lactic fermentation occurs in "oxygen depleted muscle and some bacteria"; ethanolic in yeast | Verified live (S-FERM) |

**Critical carbon-fact for ending assignment:** in **lactic** fermentation the C14 carbon is **retained** (pyruvate→lactate, no carbon lost) → maps to the project's **Good** ending semantics ("carbon body retained pre-oxidation"). In **ethanolic** fermentation the C14 carbon **is released as CO₂** (pyruvate decarboxylase) → maps to **Normal** ("CO₂ released without the full electron-harvest arc"). Neither releases the soul (electrons) into ATP — **no True**. A host energy crisis if fermentation can't keep up → **Bad**. So glucose-anaerobic reaches {Good, Normal, Bad}, NOT True.

**Critical host-organism fact:** lactic fermentation is mammalian (muscle); ethanolic is yeast. **A single host organism does not naturally do both.** This constrains option (a) HOST-CONDITION BRANCH: the glucose host must pick ONE fermentation type. The project's host organism is currently unspecified — resolving the anaerobic decision likely forces a host-organism micro-decision (mammal vs yeast vs "generic"). Flag for the human.

**Candidate sources for glucose anaerobic:**
- **S-FERM** — "Fermentation," Supplemental Modules (Biological Chemistry), Chemistry LibreTexts. URL: `https://chem.libretexts.org/Bookshelves/Biological_Chemistry/Supplemental_Modules_(Biological_Chemistry)/Metabolism/Catabolism/Fermentation` — **PAGE FETCHED LIVE** during this research. CC BY-NC-SA 4.0. Authors: Darik Benson (UC Davis), Mike Blaber (FSU). Backs G2, G3, G4, G5. `CANDIDATE — needs human approval`.
- **S-GLY** — "Glycolysis," same hub. URL: `.../Catabolism/Glycolysis` — **PAGE FETCHED LIVE**. CC BY-NC-SA 4.0. Author: Darik Benson. Explicitly: pyruvate "can be reduced to lactate or ethanol in the absence of oxygen using a process known as Fermentation." Backs G1, G2/G3 framing. `CANDIDATE — needs human approval`.
- **S-BIOX** — "Biological Oxidation," same hub. URL: `.../Catabolism/Biological_Oxidation` — **PAGE FETCHED LIVE**. CC BY-NC-SA 4.0. Explicitly: "if it lacks sufficient amounts of oxygen the end product pyruvate, is reduced to lactate with NADH as the reducing agent." Backs G2. `CANDIDATE — needs human approval`.
- **S-LEHNINGER** — Nelson, D. L., and Cox, M. M. *Lehninger Principles of Biochemistry.* W. H. Freeman. **CONFIRMED TO EXIST** (the verified S-BIOX page cites "Nelson, David, and Michael Cox. LEHNINGER PRINCIPLES OF BIOCHEMISTRY. 5th. New York, NY: Freeman and Company" in its reference list). The standard graduate/undergrad biochem textbook; the fermentation chapter is the canonical citable source. **`CANDIDATE — verify exact edition (5th cited) + chapter + ISBN + seek human approval`. No ISBN asserted here.** Best used as the citable primary if the human prefers a print source over LibreTexts web pages.
- **S-GARRETT** — Garrett, R. H., and Grisham, C. M. *Biochemistry.* (Cited by S-FERM, S-BETA, S-GLY as "Garrett, H., Reginald and Charles Grisham. Biochemistry. Boston: Twayne Publishers, 2008.") **CONFIRMED TO EXIST** by being cited in three verified LibreTexts pages. `CANDIDATE — verify edition (2008 cited) + chapter + ISBN + seek human approval`. No ISBN asserted.

### Fatty acid — anaerobic catabolism is NOT available (obligately aerobic)

| Fact | Status |
|------|--------|
| F1 | β-oxidation occurs in the mitochondria; produces **FADH₂** (1st oxidation, Acyl-CoA dehydrogenase, FAD prosthetic group) and **NADH** (2nd/3rd oxidation, Hydroxyacyl-CoA dehydrogenase, NAD⁺) per cycle | Verified live (S-BETA) |
| F2 | The FADH₂ from β-oxidation is re-oxidized via **ETF (Electron-transferring flavoprotein) Dehydrogenase → ubiquinone → ETC → O₂** | Verified live (S-ETC — "ETF Dehydrogenase... is a part the B-oxidation cycle... passes those electrons from [FADH₂] to ubiquinone and on through the ETC") |
| F3 | The ETC's terminal acceptor is O₂; without O₂ the ETC stalls, FAD and NAD⁺ are NOT regenerated | Verified live (S-ETC, S-BIOX) |
| F4 | Fermentation regenerates NAD⁺ from **pyruvate** — it does NOT regenerate FAD, and it does NOT reach β-oxidation's substrates | Verified live (S-FERM — fermentation is explicitly a pyruvate-recycling process) |
| F5 | **Conclusion (mechanism):** β-oxidation cannot proceed without O₂ in a mammalian/yeast host — both its redox cofactors (FAD, NAD⁺) depend on the ETC to be regenerated, and fermentation cannot substitute | **DERIVED** from F1+F2+F3+F4 (mechanism, not a single quoted sentence) |

**Critical reachability fact:** the fatty-acid character has **no anaerobic catabolic path** in a mammalian/yeast host. Any "anaerobic fatty-acid branch" strands the hero at the entry enzyme (Acyl-CoA synthetase / carnitine shuttle / Acyl-CoA dehydrogenase) with nowhere to go — a reachability dead-end. This is the single hardest constraint on option (a) HOST-CONDITION BRANCH.

**The "explicit quotable sentence" gap (honesty flag):** the verified pages establish the *mechanism* (F1–F4) conclusively, but **no single sentence on the verified pages says verbatim "fatty acid β-oxidation is obligately aerobic" / "fatty acids cannot be metabolized under anaerobic conditions."** That explicit one-line claim — if the narrative asserts it — needs its own source. The strongest candidate is a textbook (S-LEHNINGER or S-GARRETT) discussion of β-oxidation regulation / cofactor regeneration. **`CANDIDATE — locate the explicit statement in S-LEHNINGER or S-GARRETT at approval time; do not assert F5 in shipped text without it.`** The mechanism (F1–F4) is citable now; the one-line conclusion needs the textbook.

**Candidate sources for fatty acid anaerobic:**
- **S-BETA** — "Beta-Oxidation," same hub. URL: `.../Catabolism/Beta-Oxidation` — **PAGE FETCHED LIVE**. CC BY-NC-SA 4.0. Author: Darik Benson. Backs F1, the FAD/NAD⁺ cofactor dependence, mitochondrial location. `CANDIDATE — needs human approval`.
- **S-ETC** — "Electron Transport Chain," same hub. URL: `.../Catabolism/Electron_Transport_Chain` — **PAGE FETCHED LIVE**. CC BY-NC-SA 4.0. Backs F2 (ETF→ubiquinone→ETC) and F3 (O₂ terminal acceptor). `CANDIDATE — needs human approval`.
- **S-LEHNINGER / S-GARRETT** — as above, the best candidates for the explicit F5 one-line claim. `CANDIDATE — verify chapter + seek human approval`.

### Alcohol — anaerobic is paradoxical (ethanol is fermentation's product, not its substrate)

| Fact | Status |
|------|--------|
| A1 | The alcohol character's **aerobic** path: ethanol → acetaldehyde (via **alcohol dehydrogenase**, oxidizing direction, produces NADH) → acetate (via **acetaldehyde dehydrogenase**) → acetyl-CoA → TCA → ETC | Aerobic path; the ADH-oxidizing-direction claim needs its own source (S-FERM shows the reverse direction only) |
| A2 | Alcoholic **fermentation** runs ADH in the **reducing direction**: acetaldehyde → ethanol, consuming NADH, regenerating NAD⁺ | Verified live (S-FERM) |
| A3 | ADH is a **reversible** enzyme — same enzyme catalyzes both directions; direction is governed by substrate/product concentrations and the cell's redox state | Standard enzymology; needs a source (S-LEHNINGER / S-GARRETT ADH discussion, or an enzyme-specific reference) |
| A4 | **Conclusion:** ethanol is the *end product* of anaerobic fermentation. "Anaerobic alcohol character" has no forward catabolism — the hero is already at fermentation's destination. The energetically favorable anaerobic direction is **toward** ethanol, not away from it. | **DERIVED** from A1+A2+A3 |

**Critical reachability fact:** the alcohol character cannot "go through anaerobic metabolism" in the forward sense — it IS the anaerobic product. Like the fatty acid, an "anaerobic alcohol branch" has no forward path. This is the second hard constraint on option (a).

**Candidate sources for alcohol anaerobic:**
- **S-FERM** — backs A2 (ADH reducing direction in alcoholic fermentation). `CANDIDATE — needs human approval`.
- **S-LEHNINGER / S-GARRETT** — best candidates for A1 (ADH oxidizing direction, the aerobic alcohol path), A3 (ADH reversibility), and the alcohol metabolism chapter generally. `CANDIDATE — verify chapter + seek human approval`. Note: the alcohol character's full aerobic path (ethanol→acetaldehyde→acetate→acetyl-CoA) is a **Phase 8** content concern; only the anaerobic-direction paradox is in scope here.
- **S-ADH-ENZYME** (optional) — an enzyme-database or review reference for ADH directionality/reversibility if the human prefers an enzyme-specific source over a textbook chapter. `CANDIDATE — propose specific reference at approval time (e.g. BRENDA / UniProt / a review); do not assert a specific reference here without verifying it exists`.

---

## Framing Options (for the human to choose)

For each option: **what / pros / cons / all-4-endings reachability impact / story-graph (Phase 5.1) impact / per-claim approval load**. The reachability impact is the decisive axis here.

### (a) HOST-CONDITION BRANCH — oxygen availability is a host-condition flag; each character branches aerobic vs anaerobic

- **What:** A single host-condition flag (`oxygen: high|low`) gates a branch point early in each character's path. Same character, two sub-tracks.
- **Pros:**
  - Most "biologically faithful" framing — oxygen availability IS the real physiological switch for glycolysis→pyruvate fate.
  - Reuses the existing 3-character roster (no 4th character needed).
  - Pedagogically strong for glucose: the pyruvate branch (→acetyl-CoA vs →lactate/ethanol) is a classic teaching point.
- **Cons (SEVERE):**
  - **Breaks reachability for 2 of 3 characters.** Fatty acid: no anaerobic catabolism (F5) — the anaerobic sub-track is a dead-end. Alcohol: ethanol is the anaerobic product (A4) — no forward anaerobic path. Only glucose has a viable anaerobic sub-track.
  - **Breaks the True ending anaerobically for ALL characters** (ETC requires O₂ — see Soul-Jump section). So even glucose's anaerobic sub-track reaches at most 3/4.
  - Forces a host-organism micro-decision (mammal=lactic / yeast=ethanolic) because one host doesn't do both fermentations — an under-the-radar scope expansion.
  - The "all 4 reachable per character" invariant is violated on the anaerobic sub-track for every character. The invariant would have to be redefined as "aerobically, all 4 reachable" — at which point (a) has lost its main advantage over (c)/(d).
- **All-4-endings reachability impact:** **NEGATIVE — breaks the invariant for the anaerobic sub-track of all 3 characters** (True unreachable for all; entire sub-track dead for fatty acid + alcohol). To salvage, the human would have to either (i) accept the invariant is aerobic-only (then why branch?), or (ii) fabricate an anaerobic True ending (forbidden), or (iii) expand the host to anaerobic-respiration organisms (option e, high scope).
- **Story-graph (Phase 5.1) impact:** adds an O₂-availability branch point per character + anaerobic sub-track nodes per character. The fatty-acid and alcohol anaerobic sub-tracks would be dead-ends the reachability checker would flag red — forcing the designer to either add fabricated nodes (forbidden) or accept the sub-tracks don't reach all endings. Messy.
- **Per-claim approval load:** HIGH — anaerobic narrative claims for all 3 characters (even if fatty-acid/alcohol are short, the "why you can't proceed" text needs claims). Plus the host-organism claims.

### (b) SEPARATE SCENARIO — anaerobic is a distinct playthrough/scenario the player selects, separate from the 3-character aerobic roster

- **What:** The new-game screen offers aerobic characters (glucose/FA/alcohol) AND a separate "anaerobic scenario" entry. The anaerobic scenario is effectively a 4th track.
- **Pros:**
  - Cleanly isolates the anaerobic reachability problem: the "all 4 reachable" invariant applies to the **3 aerobic characters**; the anaerobic scenario has its own (reduced) ending set, clearly communicated to the player.
  - Lets the anaerobic scenario be **glucose-only** (the only character with a real anaerobic path), avoiding the fatty-acid/alcohol dead-ends entirely.
  - Pedagogically clean: "select the anaerobic scenario to explore fermentation" is a clear classroom affordance.
- **Cons:**
  - Adds a 4th top-level track to the new-game screen (scope creep on the "3 characters" framing — though spec.md says "anaerobic path" is in v1 scope, so this may be acceptable).
  - The anaerobic scenario STILL cannot reach the True ending (no ETC) — so its ending set is {Good, Normal, Bad} at best. The player must be told this (a teaching opportunity, not a flaw).
  - Two-layer text for an entirely separate scenario = a separate content slice (~one Phase 9 plan's worth).
- **All-4-endings reachability impact:** **NEUTRAL** — IF the invariant is scoped to "the 3 aerobic characters reach all 4 aerobically" and the anaerobic scenario is openly a reduced-ending track. The human must approve the invariant re-wording.
- **Story-graph (Phase 5.1) impact:** adds a separate anaerobic story graph (glucose-derived) alongside the aerobic glucose graph. The aerobic glucose graph keeps its pyruvate branch but routes the anaerobic fate into the separate scenario rather than a same-character sub-track. Cleaner than (a).
- **Per-claim approval load:** MEDIUM — anaerobic claims for glucose only (lactic + ethanolic). The fatty-acid/alcohol "no anaerobic path" need not be narrated (they're simply absent from the scenario).

### (c) BAD-ENDING TRIGGER — oxygen depletion triggers a bad ending (host energy crisis / host death)

- **What:** Anaerobic conditions (oxygen depletion) are a **failure mode**, not a full track. When O₂ runs out (RNG event, edit consequence, or story choice), the host enters energy crisis and the hero is routed to a Bad ending (host dies / cycle-trap / released from host).
- **Pros:**
  - **Scientifically honest about the ETC dependence** — oxygen depletion causing energy crisis IS the real consequence for obligate-aerobic tissues/organisms. This is the option most aligned with the science for the fatty-acid and alcohol characters (which genuinely cannot survive anaerobically in the mammalian/yeast framing).
  - **Sidesteps the True-ending tension entirely** — anaerobic is a Bad ending, so the question of "is True reachable anaerobically" never arises. The "all 4 reachable" invariant stays **aerobic-only**, untouched.
  - No 4th character, no anaerobic sub-tracks for FA/alcohol (they just die — pedagogically correct).
  - Lowest story-graph disruption: a Bad-ending pool entry + an O₂-depletion trigger edge, not a whole new graph.
- **Cons:**
  - **Loses the fermentation teaching opportunity** if applied uniformly — lactic/ethanolic fermentation is a major biochem topic and a pure-Bad framing makes anaerobic = "you lose," which undersells it for the educator audience.
  - For glucose specifically, "anaerobic = Bad" is scientifically oversimplified (muscle fermentation is normal physiology, not death). An educator reviewer may push back on glucose-anaerobic-as-pure-Bad.
  - Spec.md line 18 lists "host organism passed" / "host cannot survive" as Bad-ending triggers already — this option folds anaerobic into that existing pool, which is consistent.
- **All-4-endings reachability impact:** **NEUTRAL-POSITIVE** — the invariant stays aerobic-only and intact; anaerobic contributes a Bad-ending trigger (which *helps* Bad-tier reachability). No character loses an ending.
- **Story-graph (Phase 5.1) impact:** minimal — an O₂-depletion trigger node routing to the existing Bad-ending pool. May be the lowest-impact option on the graph.
- **Per-claim approval load:** LOW-MEDIUM — the "O₂ depletion → ETC stalls → energy crisis" claim (mechanism, S-ETC + S-BIOX) + the per-character Bad-ending framing text.

### (d) ANAEROBIC AS A PLAYER CHOICE (glucose only) — fermentation reachable as Good/Normal endings, with Bad for energy crisis

- **What:** A hybrid of (b) and (c). The player, as glucose, can CHOOSE to enter anaerobic conditions (or is forced by a host-condition event). Under anaerobic glucose: lactic fermentation → Good (carbon retained as lactate); ethanolic fermentation → Normal (CO₂ released); energy crisis → Bad. True is openly unreachable anaerobically (stated in the teaching layer). Fatty acid + alcohol: anaerobic = Bad-ending trigger (option c for them).
- **Pros:**
  - **Best pedagogical fit** for the educator audience: fermentation is taught as a real, reachable glucose fate with distinct ending semantics (lactate=retained, ethanol=CO₂), not just "you lose."
  - Scientifically honest: glucose gets a real 3-ending anaerobic branch; FA/alcohol get the scientifically-correct "can't survive anaerobic" Bad ending.
  - The "all 4 reachable" invariant is preserved **aerobically** for all 3 characters; the anaerobic glucose branch is openly a 3-ending sub-track (the teaching layer explains why no True — a strong teaching moment about the ETC).
  - Reuses the existing glucose graph (adds an anaerobic branch), no 4th character.
- **Cons:**
  - Most complex to author (a 3-ending anaerobic sub-branch for glucose + Bad-trigger for FA/alcohol).
  - The host-organism micro-decision still applies for glucose (lactic vs ethanolic — pick one host, or allow the player to pick the host organism?).
  - Requires the invariant re-wording (aerobic-only) — same as (b)/(c).
  - Highest per-claim approval load of the science-honest options (fermentation claims × 2 types + energy-crisis claim + per-character framing).
- **All-4-endings reachability impact:** **NEUTRAL** — invariant scoped to aerobic; anaerobic glucose reaches 3/4 (openly); FA/alcohol anaerobic = Bad (a single ending, contributing to Bad reachability).
- **Story-graph (Phase 5.1) impact:** MODERATE — an anaerobic branch off the glucose pyruvate node (3 endings: Good-lactate / Normal-ethanol / Bad-crisis) + an O₂-depletion→Bad edge for FA/alcohol. The reachability checker must be told the invariant is aerobic-scoped or it will flag the anaerobic glucose sub-branch as "missing True."
- **Per-claim approval load:** HIGHEST among (b/c/d) — but still small relative to the full content's hundreds of claims (Pitfall 7). ~8–12 claims (see Per-Claim Inventory).

### (e) EXPAND HOST TO ANAEROBIC-RESPIRATION ORGANISM (non-O₂ terminal acceptor) — to recover a True-variant anaerobically

- **What:** Change the host organism from mammalian/yeast to an anaerobic-respiration bacterium/archaeon (terminal acceptor = nitrate/sulfate/Fe(III)/fumarate/etc.). Then a variant ETC runs anaerobically, and a "soul-jump variant" (electrons → ATP via the anaerobic ETC) could be reachable.
- **Pros:**
  - The ONLY option that could make a True-ending-variant reachable anaerobically — satisfies a strict reading of "all 4 reachable per character including anaerobic."
  - Scientifically real (anaerobic respiration is a real process; S-FERM notes non-O₂ terminal acceptors).
- **Cons (SEVERE):**
  - **Scope explosion + framing conflict.** The 3 characters (glucose, fatty acid, alcohol) and their pathways (glycolysis, β-oxidation, ADH) are framed around a mammalian/yeast host. Switching to an anaerobic bacterium changes the host organism, the cast (different enzymes), the endings' resonance, and arguably the game's identity. This is a v2-scale change, not a Phase 5 framing tweak.
  - **β-oxidation in anaerobic bacteria** uses different pathways in some species (not the canonical mitochondrial β-oxidation) — major citation + content burden.
  - **Alcohol character** is even more paradoxical in a bacterial host.
  - The educator audience expects mammalian/yeast fermentation pedagogy, not anaerobic-respiration microbiology — likely an audience mismatch.
- **All-4-endings reachability impact:** COULD reach 4/4 anaerobically — but at the cost of redefining the host, cast, and arguably the game. Not recommended for v1.
- **Story-graph impact:** rewrite, not edit.
- **Per-claim approval load:** VERY HIGH — entirely new host-organism + pathway claims.
- **This option is listed for completeness; the advisory lean is against it for v1.** It is the only technically-correct answer to "anaerobic must reach all 4 endings for all characters," and flagging that is this research's obligation — but the cost is disproportionate.

### Options comparison matrix

| Option | All-4 reachable? (per the science) | FA anaerobic | Alcohol anaerobic | True anaerobic? | Scope cost | Educator value | Advisory lean |
|--------|-------------------------------------|--------------|-------------------|-----------------|-----------|----------------|---------------|
| (a) Host-condition branch | NO (3/4 glucose; 0 for FA/Alc) | Dead-end | Dead-end | NO | Med | Med (glucose) | **Against** (breaks invariant for 2 chars) |
| (b) Separate scenario | Aerobic yes; anaerobic 3/4 (glucose only) | n/a (absent) | n/a (absent) | NO | Med | High | Plausible |
| (c) Bad-ending trigger | Aerobic yes (unchanged) | Bad (correct) | Bad (correct) | n/a (anaerobic=Bad) | **Low** | Low-Med | **Lean** (cleanest) |
| (d) Choice (glucose) + Bad (FA/Alc) | Aerobic yes; anaerobic 3/4 (glucose) | Bad (correct) | Bad (correct) | NO (openly stated) | Med-High | **Highest** | **Lean** (best pedagogy) |
| (e) Anaerobic-respiration host | Possibly 4/4 | Different pathway | Paradox | Maybe (variant) | **Very High** | Low (audience mismatch) | Against (v2-scale) |

---

## Recommendation (advisory — the human decides)

**Lean: option (c) BAD-ENDING TRIGGER as the baseline, optionally upgraded to (d) CHOICE-FOR-GLUCOSE + BAD-FOR-FA/ALC if the human prioritizes fermentation pedagogy.** Reasoning:

1. **The science forces the invariant to be aerobic-scoped.** No honest option reaches the True ending anaerobically (ETC needs O₂ — verified). So "all 4 endings reachable for every character" MUST be re-worded to "all 4 reachable **aerobically** for every character" regardless of which option is chosen (except (e), which is v2-scale). The human should approve that re-wording explicitly. Once that re-wording is accepted, the anaerobic decision becomes "what does the anaerobic scope look like *given* the invariant is aerobic?" — and the answer is a pedagogy/scope tradeoff, not a science conflict.

2. **(c) is the cleanest and lowest-risk.** It treats oxygen depletion as the energy-crisis failure mode it actually is for obligate-aerobic metabolism, routes to the existing Bad-ending pool (consistent with spec.md line 18's "host organism passed" / "host cannot survive"), touches the story graph minimally, and carries the lowest per-claim load. It is scientifically unimpeachable for FA and alcohol. **Its weakness is pedagogical for glucose** — fermentation-as-pure-Bad undersells a major topic.

3. **(d) fixes (c)'s pedagogical weakness for glucose** at the cost of more content. If the educator audience's interest in anaerobic is primarily fermentation (likely — fermentation is the canonical "anaerobic" topic in biochem courses), (d) delivers that as a real, reachable glucose branch with distinct ending semantics (lactate=Good/retained, ethanol=Normal/CO₂). This is the best teaching artifact. **The cost is a 3-ending anaerobic glucose sub-branch + the claim load (~8–12 claims).**

4. **(a) and (e) are not recommended.** (a) breaks the invariant for 2 of 3 characters in a way no re-wording fixes (FA/alcohol have no forward anaerobic path — a dead-end, not a missing ending). (e) is v2-scale and audience-mismatched.

**The reachability + ETC tension, flagged explicitly (the human MUST weigh this):**
- **The True ending is biochemically unreachable anaerobically.** This is not negotiable; it is verified chemistry (S-ETC, S-BIOX). Any option that implies a True ending under anaerobic conditions is fabricated science.
- **The "all 4 endings reachable for every character" v1 success measure is, strictly, an aerobic property.** The human must either (i) re-word it to "aerobically" (recommended; pairs with b/c/d), or (ii) accept v1 falls short of the strict reading for the anaerobic scope (also acceptable if documented), or (iii) pursue (e) at v2 scope. **Do not** pick an option that silently violates the invariant without re-wording it — that stores up a verifier/reviewer conflict.

**Mandatory pairing for ANY chosen option:** Phase 5.1's reachability checker must be configured with the aerobic-scoped invariant (or the chosen re-wording) AND must confirm the anaerobic sub-graph (if any) reaches exactly the endings the science permits (3/4 for glucose-anaerobic under (d); Bad-only for FA/Alc under (c)/(d); none for the absent characters under (b)). This research cannot verify the graph property — it's decided when the Phase 5.1 skeleton is designed. Flag to the Phase 5.1 designer.

---

## Per-Claim Inventory if Implemented (claim_id → claim text → candidate source)

Format matches the Phase 1 claims-registry contract (`data/claims.jsonl`: `{claim, source, source_id, status, ...}`). Claims below would land in anaerobic narrative text under options (b)/(c)/(d). Mark each `pending` until human-approved. **No claim ships without its source approved.**

| claim_id | Claim text (to be approved) | Candidate source | Source type | Notes |
|----------|-----------------------------|-----------------|------------|-------|
| **AN-G-01** | "Glycolysis converts glucose to pyruvate; pyruvate's fate depends on the presence of oxygen." | S-GLY (LibreTexts Glycolysis) + S-FERM | EDUCATIONAL (CC BY-NC-SA 4.0) | Foundational framing claim. Verified live. |
| **AN-G-02** | "In the absence of oxygen, pyruvate is reduced to lactate by lactate dehydrogenase, with NADH as the reducing agent; NAD⁺ is regenerated. No CO₂ is released." | S-FERM + S-BIOX | EDUCATIONAL | Verified live. Backs the glucose-anaerobic **lactic** / Good-ending path. |
| **AN-G-03** | "In the absence of oxygen (yeast), pyruvate is converted to acetaldehyde and CO₂ by pyruvate decarboxylase, then acetaldehyde is reduced to ethanol by alcohol dehydrogenase, regenerating NAD⁺." | S-FERM | EDUCATIONAL | Verified live. Backs the glucose-anaerobic **ethanolic** / Normal-ending path. CO₂ release is the key carbon-fact. |
| **AN-G-04** | "Fermentation recycles NAD⁺ so that glycolysis can continue, but yields far less energy than the TCA cycle and ETC." | S-FERM ("energy... much less than... TCA cycle and ETC") | EDUCATIONAL | Verified live. Backs the "no True anaerobically" teaching-layer explanation. |
| **AN-G-05** | "Lactic fermentation occurs in oxygen-depleted muscle and some bacteria; ethanolic fermentation occurs in yeast." | S-FERM | EDUCATIONAL | Verified live. Backs the host-organism micro-decision. Forces the mammal-vs-yeast host choice for option (a)/(d). |
| **AN-FAB-01** | "Fatty acid β-oxidation requires oxygen: it produces FADH₂ and NADH that must be re-oxidized by the electron transport chain, whose terminal electron acceptor is oxygen. Without oxygen, β-oxidation cannot proceed." | **MECHANISM:** S-BETA + S-ETC + S-BIOX (verified). **EXPLICIT one-line statement:** S-LEHNINGER or S-GARRETT (β-oxidation chapter) — `CANDIDATE — locate the explicit sentence at approval time` | MIXED | The mechanism (F1–F4) is citable now from verified pages; the one-line conclusion needs a textbook sentence. **Do not ship AN-FAB-01 until the textbook sentence is located + approved.** Backs the fatty-acid "no anaerobic path" framing (option c/d Bad-ending). |
| **AN-FAB-02** | "The FADH₂ produced in the first oxidation step of β-oxidation is re-oxidized via electron-transferring flavoprotein (ETF) dehydrogenase, which feeds electrons into the electron transport chain at ubiquinone." | S-ETC ("ETF Dehydrogenase... is a part the B-oxidation cycle... passes those electrons from [FADH₂] to ubiquinone") | EDUCATIONAL | Verified live. Strengthens AN-FAB-01's mechanism (FAD can ONLY be regenerated via ETC, not fermentation). |
| **AN-ETC-01** | "The electron transport chain uses oxygen as its terminal electron acceptor; Complex IV (cytochrome c oxidase) transfers electrons to oxygen, producing water." | S-ETC + S-BIOX ("molecular oxygen as the final electron acceptor at the end") | EDUCATIONAL | Verified live. **The load-bearing claim for the soul-jump tension.** |
| **AN-ETC-02** | "ATP synthesis via oxidative phosphorylation depends on electrons reaching oxygen; without oxygen, the electron transport chain stalls, the proton gradient collapses, and ATP synthase cannot produce ATP at the rates required." | S-BIOX ("oxidative phosphorylation... ATP is able to form as a result of the transfer of electrons" [to O₂]) + S-ETC | EDUCATIONAL | Verified live. Backs the "True ending unreachable anaerobically" teaching layer + the Bad-ending energy-crisis trigger. |
| **AN-Alc-01** | "Ethanol is the product of alcoholic fermentation: under anaerobic conditions, acetaldehyde is reduced to ethanol by alcohol dehydrogenase." | S-FERM | EDUCATIONAL | Verified live. Backs the alcohol-character anaerobic paradox (A2/A4). |
| **AN-Alc-02** | "Alcohol dehydrogenase is reversible; in the aerobic metabolism of ethanol it catalyzes the oxidation of ethanol to acetaldehyde." | S-LEHNINGER or S-GARRETT (ADH / alcohol metabolism chapter) — `CANDIDATE — verify chapter` | TEXTBOOK | The aerobic-direction claim is NOT on the verified fermentation page (which shows only the reducing direction). Needs the textbook. Backs the alcohol character's aerobic path (A1) — primarily a Phase 8 concern, but flagged here because the anaerobic paradox leans on ADH reversibility. |
| **AN-ANAER-DEF-01** | "Fermentation regenerates NAD⁺ from NADH by reducing an organic molecule (e.g. pyruvate), without an electron transport chain; anaerobic respiration, by contrast, uses an electron transport chain with a non-oxygen terminal acceptor (e.g. nitrate, sulfate, Fe(III))." | S-FERM ("In anaerobic organisms, the terminal electron acceptor can vary... metals... CO₂, nitrate, sulfur") | EDUCATIONAL | Verified live. The terminological distinction. Only needed if the teaching layer explicitly distinguishes fermentation from anaerobic respiration (recommended for the educator audience). |
| **AN-DD-01** (game-design, mixed) | "Under anaerobic conditions, the True ending (electrons harvested into ATP via the ETC) is unreachable, because the ETC requires oxygen." | Embedded science = AN-ETC-01 + AN-ETC-02; the framing = game design. | MIXED | The registry entry should link the embedded claims; the framing needs no separate source. **This is the claim that makes the invariant re-wording necessary.** |

**Note on derived vs sourced:** AN-G-02 through AN-Alc-01 are directly stated on verified LibreTexts pages (sourced). AN-FAB-01 is the only claim that is *mechanism-derived* (F1–F4 are sourced; the one-line conclusion needs a textbook). AN-DD-01 is game-design framing with embedded sourced science. The honesty rule: the registry should mark AN-FAB-01 as `mechanism_derived_from: [S-BETA, S-ETC, S-BIOX]` + `pending_explicit_source` until the textbook sentence is approved.

---

## Cast Impact (anaerobic-specific enzymes for the ~20+ cast)

The anaerobic decision adds **at most 2 enzymes** to the ~20+ cast (modest), and reuses 1 existing one. Which ones land depends on the chosen option + the host-organism micro-decision:

| Enzyme | Anaerobic role | Already in aerobic cast? | Added under which option? |
|--------|----------------|--------------------------|---------------------------|
| **Lactate dehydrogenase (LDH)** | Lactic fermentation: pyruvate → lactate | No (aerobic glucose goes pyruvate→acetyl-CoA via PDH) | (a)/(d) if mammalian host; (b) if lactic scenario |
| **Pyruvate decarboxylase** | Ethanolic fermentation: pyruvate → acetaldehyde + CO₂ | No | (a)/(d) if yeast host; (b) if ethanolic scenario |
| **Alcohol dehydrogenase (ADH)** | Ethanolic fermentation: acetaldehyde → ethanol (reducing direction) | **Yes** — ADH is the alcohol character's aerobic ENTRY enzyme (ethanol→acetaldehyde, oxidizing direction). Same enzyme, opposite direction. | Reused under (a)/(b)/(d); no new PDB needed if the alcohol character's ADH structure is already cast |
| **(ETF: Electron-transferring flavoprotein dehydrogenase)** | Not anaerobic-specific — but the enzyme that makes β-oxidation obligately aerobic (FADH₂→ETC). Mentioned in S-ETC. | Possibly (part of the FA character's aerobic cast) | Not added by anaerobic; noted here because it's the mechanistic reason FA can't go anaerobic |

**Net cast impact:** +1 to +2 enzymes (LDH and/or pyruvate decarboxylase), depending on fermentation type. ADH is shared. This does NOT materially change the "~20+ cast" target (Phase 9). **Each new enzyme still needs a verified PDB ID + resolution + citation** (CAST-01) — propose no PDB IDs here (no-fabricated-science rule); the cast enumeration is a Phase 9 task once framing is decided. Flag: the host-organism micro-decision (mammal vs yeast) determines WHICH of LDH / pyruvate decarboxylase enters the cast — so the cast composition depends on the framing outcome.

**Fatty-acid and alcohol characters add NO anaerobic enzymes** under options (c)/(d) (they get a Bad-ending trigger, not a metabolic branch). Under option (a) they would need anaerobic-path enzymes that DON'T EXIST in the mammalian/yeast framing — another reason (a) is not recommended.

---

## Interaction with Soul-Jump Reframing (Pitfall 4) — the ETC / True-ending tension

**This is the single most important section for the human to weigh.** The soul-jump reframing (Pitfall 4, RESOLVED 2026-08-13) defines:

- **True ending** = the hero's *electrons* (the "soul") are harvested into ATP via the ETC → ATP synthase after the RNG-weighted TCA path; the carbon body is released as CO₂.

The anaerobic decision collides with this definition directly:

### The collision (verified science)

| Step | Fact | Source |
|------|------|--------|
| 1 | The True ending requires electrons to flow through the ETC to ATP synthase. | Pitfall 4 resolution (PROJECT.md) |
| 2 | The ETC's terminal electron acceptor is **oxygen**; Complex IV transfers electrons to O₂ → water. | S-ETC, S-BIOX (verified live) |
| 3 | Oxidative phosphorylation (ATP synthase producing ATP) depends on the electron flow to O₂; "ATP is able to form as a result of the transfer of electrons" [to O₂]. | S-BIOX (verified live) |
| 4 | **Without O₂, the ETC stalls, the proton gradient collapses, ATP synthase cannot produce ATP at the required rate.** | S-ETC, S-BIOX (verified live) — mechanism |
| 5 | **Therefore the True ending (soul-jump) is biochemically unreachable under anaerobic conditions.** | Conclusion from 1–4 |

This is **not** a framing preference — it is settled chemistry verified against two independent LibreTexts pages. The hero's electrons cannot reach ATP via the ETC if there is no O₂ to accept them at Complex IV. (The only exception is anaerobic *respiration* in some bacteria, which use a non-O₂ terminal acceptor — option (e), v2-scale, host-organism change.)

### Why this is a tension, not a contradiction

Pitfall 4's resolution is about **chemical fate** (where the carbon goes; whether the carbon becomes ATP). The soul-jump says: carbon → CO₂; electrons → ATP via ETC. That remains correct **aerobically**. The anaerobic decision is about **environmental conditions** (is O₂ present?). Under anaerobic conditions:
- The carbon body's fate is STILL chemically well-defined (pyruvate→lactate retains it; pyruvate→ethanol+CO₂ releases one carbon).
- The electrons' fate is NOT "harvested into ATP via ETC" — they go to reducing pyruvate (lactate) or acetaldehyde (ethanol). The "soul" is spent regenerating NAD⁺, not harvested into ATP.
- So anaerobically, **the soul-jump does not occur.** The True ending's defining event is absent.

This is consistent (not contradictory) with Pitfall 4: Pitfall 4 settled the aerobic carbon-vs-electrons question; it did not promise the True ending is reachable under all conditions. The anaerobic decision simply makes explicit that **the True ending is conditional on O₂** — which is the science.

### What this means for the design

1. **The v1 success measure "all 4 endings reachable for every character" is, strictly, an aerobic property.** No anaerobic path reaches True. The human MUST re-word the invariant (to "aerobically, all 4 reachable") OR explicitly accept that anaerobic falls short OR pursue option (e). **Do not** silently leave the invariant un-re-worded while shipping an anaerobic scope — the reachability checker (Phase 5.1) will flag it red and a reviewer will ask why.

2. **Anaerobic endings, by tier, under the science:**
   - **True:** UNREACHABLE anaerobically (no ETC electron harvest). No option fixes this without (e).
   - **Good:** REACHABLE for glucose via lactic fermentation (carbon retained as lactate — matches "carbon body retained pre-oxidation"). NOT reachable for FA (no anaerobic catabolism) or alcohol (already the product).
   - **Normal:** REACHABLE for glucose via ethanolic fermentation (CO₂ released without the soul-jump arc — matches "CO₂ released without the full electron-harvest"). NOT reachable for FA/alcohol.
   - **Bad:** REACHABLE for all (energy crisis / host death from ETC failure — matches "host organism passed" / "host cannot survive"). This is the one ending anaerobic reliably delivers for every character.

3. **The teaching-layer opportunity (a reason to keep some anaerobic content):** the *reason* the True ending is unreachable anaerobically IS the pedagogical point — "no oxygen → no ETC → no ATP from oxidative phosphorylation → energy crisis / fermentation only." This is a strong teaching moment about why oxygen matters. Option (d) captures it best (the teaching layer openly states "you cannot reach the True ending here because the ETC needs oxygen"); option (c) captures it in the Bad-ending text; option (b) in the scenario intro.

### Consistency note (mirrors the c14-decay research's pattern)

The soul-jump framing (Pitfall 4) and the anaerobic decision are **consistent but coupled**: Pitfall 4 sets the aerobic ending semantics; the anaerobic decision determines which of those semantics survive without O₂. The two-layer text must clearly distinguish:
- "Your carbon body was released as CO₂ and your electrons were harvested into ATP" (aerobic True — soul-jump occurred).
- "Your carbon body was released as CO₂ [ethanolic] / retained as lactate [lactic], but your electrons were NOT harvested into ATP — the ETC could not run without oxygen" (anaerobic Normal/Good — soul-jump did NOT occur).

These are different fates and must not be described with overlapping language. **Do NOT revisit Pitfall 4** (per AGENTS.md, the soul-jump is settled). The anaerobic decision takes the soul-jump as settled context and addresses only which endings are reachable without O₂.

---

## Open Questions for the Human

These are the specific decisions / verifications the human must make. This research does NOT resolve them.

1. **Which framing option?** (a) Host-condition branch / (b) Separate scenario / (c) Bad-ending trigger / (d) Choice-for-glucose + Bad-for-FA-Alc / (e) Anaerobic-respiration host. Advisory lean: **(c)** as baseline, **(d)** if fermentation pedagogy is prioritized. See Recommendation + tradeoffs.

2. **Re-word the v1 success measure?** The current "all 4 endings reachable for every character" is, strictly, an aerobic property (True is unreachable anaerobically — verified). Options:
   - (i) Re-word to "all 4 reachable **aerobically** for every character; anaerobic is a reduced-scope branch/failure mode." (Recommended; pairs with b/c/d.)
   - (ii) Keep the strict wording and accept v1 falls short for the anaerobic scope (document the shortfall).
   - (iii) Pursue (e) to technically satisfy the strict wording at v2 scope.
   The chosen re-wording must be recorded in PROJECT.md Key Decisions. **This is the single most consequential sub-decision.**

3. **Host-organism micro-decision.** Lactic fermentation is mammalian (muscle); ethanolic is yeast. A single host doesn't do both. If option (a) or (d) is chosen for glucose, the human must pick a host (mammal → lactic; yeast → ethanolic) OR allow the player to pick the host organism (scope creep). What is the game's host organism? (Currently unspecified in spec.md/PROJECT.md.) This also determines whether LDH or pyruvate decarboxylase enters the cast.

4. **For AN-FAB-01 ("β-oxidation is obligately aerobic"): locate the explicit textbook sentence.** The mechanism is verified (S-BETA + S-ETC + S-BIOX), but no verified page states the one-line conclusion verbatim. The human should approve a textbook (S-LEHNINGER or S-GARRETT β-oxidation chapter) and the specific sentence. Do not ship AN-FAB-01 without it.

5. **For AN-Alc-02 (ADH oxidizing direction / reversibility): approve a source.** The verified S-FERM page shows only the reducing direction. The aerobic alcohol path (A1) and the reversibility claim (A3) need a textbook or enzyme reference. (Primarily a Phase 8 concern, but the anaerobic paradox leans on it.)

6. **Are S-FERM / S-GLY / S-BIOX / S-BETA / S-ETC (the five verified LibreTexts pages) approved as the source family for the anaerobic content?** All five are CC BY-NC-SA 4.0, align with spec.md line 12's "biochemistry libretext" leaning, and were fetched live. The human may prefer to approve S-LEHNINGER (textbook) as primary + LibreTexts as cross-check, OR vice versa. Recommend: approve the LibreTexts pages as the primary source family (they directly state most claims) + S-LEHNINGER as the textbook cross-check for the textbook-only claims (AN-FAB-01, AN-Alc-02).

7. **Is the fermentation-vs-anaerobic-respiration distinction (AN-ANAER-DEF-01) in the teaching layer?** Recommended for the educator audience (it's a common student confusion). Adds 1 claim. The human decides whether the teaching layer explicitly makes this distinction or just says "anaerobic / no oxygen."

8. **Spec-deviation / invariant-re-wording documentation.** Whichever option is chosen, the change to the invariant (Q2) and the host-organism micro-decision (Q3) must be recorded in PROJECT.md Key Decisions, and (if the strict invariant is dropped) the spec.md line 33 ("All 4 ending tiers reachable for each character") reference annotated in-place (as was done for Pitfall 4 on 2026-08-13). This research does not edit those files.

9. **Reachability verification (mandatory for any option):** Phase 5.1's reachability checker must be configured with the chosen invariant scope (aerobic-scoped per Q2) AND must confirm the anaerobic sub-graph reaches exactly the endings the science permits (3/4 for glucose-anaerobic under (d); Bad-only for FA/Alc under (c)/(d); none for absent characters under (b)). This research cannot verify the graph property — flag to the Phase 5.1 designer.

10. **Interaction with the C14-decay decision (sibling research).** Both anaerobic-Bad and C14-decay-Bad feed the same Bad-ending pool. If both are kept, ensure the Bad-ending text distinguishes "host died from oxygen-depletion energy crisis" (anaerobic) from "your nucleus transmuted into nitrogen" (decay) — they are categorically different events (mirrors the c14-decay research's two-layer-text guidance). Coordinate the Bad-ending pool composition across the two Phase 5 decisions.

---

## Sources

### Primary — LibreTexts (HIGH confidence; all five pages FETCHED LIVE during this research, 2026-08-15; all CC BY-NC-SA 4.0)

All five live under the same hub: `https://chem.libretexts.org/Bookshelves/Biological_Chemistry/Supplemental_Modules_(Biological_Chemistry)/Metabolism/Catabolism/`

- **S-FERM** — "Fermentation." Authors: Darik Benson (UC Davis), Mike Blaber (FSU). URL: `.../Fermentation`. **FETCHED LIVE.** Backs G2, G3, G4, G5, A2, AN-G-02/03/04/05, AN-Alc-01, AN-ANAER-DEF-01. Explicitly states lactic + alcoholic fermentation mechanisms, the CO₂ release in alcoholic fermentation, the NAD⁺-recycling purpose, and the fermentation-vs-anaerobic-respiration terminal-acceptor distinction.
- **S-GLY** — "Glycolysis." Author: Darik Benson. URL: `.../Glycolysis`. **FETCHED LIVE.** Backs G1, AN-G-01. Explicitly: pyruvate "can be reduced to lactate or ethanol in the absence of oxygen using a process known as Fermentation."
- **S-BIOX** — "Biological Oxidation." Author: Brent Younglove (Hope). URL: `.../Biological_Oxidation`. **FETCHED LIVE.** Backs G2, AN-ETC-01/02. Explicitly: "if it lacks sufficient amounts of oxygen the end product pyruvate, is reduced to lactate with NADH as the reducing agent"; "oxidative phosphorylation... ATP is able to form as a result of the transfer of electrons" [to O₂]; "molecular oxygen as the final electron acceptor at the end." **Cites Lehninger (S-LEHNINGER) in its reference list — confirms that textbook exists.**
- **S-BETA** — "Beta-Oxidation." Author: Darik Benson. URL: `.../Beta-Oxidation`. **FETCHED LIVE.** Backs F1, AN-FAB-01 (mechanism). Confirms β-oxidation produces FADH₂ (FAD prosthetic group, Acyl-CoA dehydrogenase) and NADH (Hydroxyacyl-CoA dehydrogenase); mitochondrial location; acetyl-CoA enters TCA/ETC.
- **S-ETC** — "Electron Transport Chain." URL: `.../Electron_Transport_Chain`. **FETCHED LIVE.** Backs F2, F3, AN-ETC-01/02, AN-FAB-02. Confirms O₂ as terminal acceptor (Complex IV → water), the proton-gradient-driven ATP synthase, and the ETF→ubiquinone feed from β-oxidation's FADH₂.

### Textbook candidates (MEDIUM confidence — confirmed to EXIST because verified LibreTexts pages cite them; exact edition/chapter NOT web-verified here)

- **S-LEHNINGER** — Nelson, D. L., and Cox, M. M. *Lehninger Principles of Biochemistry.* W. H. Freeman. **Existence CONFIRMED** (S-BIOX cites "Nelson, David, and Michael Cox. LEHNINGER PRINCIPLES OF BIOCHEMISTRY. 5th. New York, NY: Freeman and Company"). The standard biochem textbook; fermentation + β-oxidation + ETC chapters are canonical. **`CANDIDATE — verify edition (5th cited) + chapter + ISBN + seek human approval`. No ISBN/DOI asserted.** Best candidate for the textbook-only claims (AN-FAB-01 explicit conclusion, AN-Alc-02 ADH reversibility).
- **S-GARRETT** — Garrett, R. H., and Grisham, C. M. *Biochemistry.* **Existence CONFIRMED** (S-FERM, S-BETA, S-GLY all cite "Garrett, H., Reginald and Charles Grisham. Biochemistry. Boston: Twayne Publishers, 2008"). **`CANDIDATE — verify edition (2008 cited) + chapter + ISBN + seek human approval`. No ISBN/DOI asserted.** Alternative to S-LEHNINGER for the textbook-only claims.
- **S-RAVEN** — Raven, P. *Biology.* **Existence CONFIRMED** (cited by S-FERM, S-BETA, S-GLY). A general-biology textbook; lighter on biochem mechanism than S-LEHNINGER. Listed for completeness; not the lead textbook candidate.

### Enzyme-specific (LOW confidence — NOT web-verified; propose at approval time)

- **S-ADH-ENZYME** (optional, for AN-Alc-02) — an enzyme-database or review reference for ADH directionality/reversibility (e.g. BRENDA, UniProt, or a journal review). **`CANDIDATE — propose a specific reference at approval time; do not assert a reference here without verifying it exists`.** Only needed if the human prefers an enzyme-specific source over S-LEHNINGER/S-GARRETT for ADH.

### Used for discovery (NOT approved sources — tertiary, not citable per project rules)

- None used. (Unlike the c14-decay research, which used Wikipedia to locate NUBASE2020, this research located all sources directly via the LibreTexts Catabolism hub navigation + the verified pages' own reference lists. No Wikipedia/Stack-Overflow reliance.)

---

## Metadata

**Confidence breakdown:**
- Glucose anaerobic science (G1–G5): **HIGH** — directly stated on verified-live LibreTexts pages (S-FERM, S-GLY, S-BIOX).
- ETC / O₂-dependence / True-ending-unreachable-anaerobically (AN-ETC-01/02): **HIGH** — explicitly stated on S-ETC + S-BIOX (verified live). This is the load-bearing finding.
- Fatty-acid "obligately aerobic" MECHANISM (F1–F4): **HIGH** — each step verified on S-BETA + S-ETC.
- Fatty-acid "obligately aerobic" ONE-LINE CONCLUSION (AN-FAB-01): **MEDIUM** — mechanism is citable; the explicit quotable sentence needs a textbook (S-LEHNINGER/S-GARRETT) at approval time. Flagged honestly.
- Alcohol anaerobic paradox (A2/A4): **HIGH** (A2 from S-FERM); **MEDIUM** (A1/A3 ADH oxidizing direction + reversibility — needs textbook, AN-Alc-02).
- Textbook candidates (S-LEHNINGER, S-GARRETT): **MEDIUM** — existence confirmed (cited by verified pages); edition/chapter not web-verified.
- Framing-option analysis (pros/cons/reachability): **HIGH** — derived directly from the verified science + the project's stated invariants; no speculative science.
- Cast impact: **HIGH** on which enzymes are anaerobic-specific (LDH, pyruvate decarboxylase, ADH-reuse); **LOW** on specific PDB IDs (correctly deferred to Phase 9; none asserted here).

**Research date:** 2026-08-15
**Valid until:** ~30 days (the biochemistry is stable; the LibreTexts URLs are stable hub pages but subpage content can be edited — re-verify the exact quoted sentences at approval time). The textbook editions may have newer versions — confirm currency at approval.
**Boundary with sibling research:** Independent of `05-RESEARCH-c14-decay.md` (Pitfall 9). The two decisions share only the Bad-ending pool (Q10 above) — coordinate the Bad-ending text composition. Do NOT conflate with Pitfall 4 (soul-jump, RESOLVED) — this research takes the soul-jump as settled context and addresses only which endings are reachable without O₂.
