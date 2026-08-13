# Aim

Develop a PyMOL plugn as an RPG game of the hero, for their path taken in the respiratory pathway.

# Description of the game

A PyMOL-based role playing game of the path taken by C, every step brings them closer to destiny.

## Requirements of the pymol plugin

1. About the plot
   * Refer to the biochemistry libretext to plan the plot and paths. **Seek my approval before you use any source. Any scientific knowledge must be cite, validated, and explicitly approved**
   * some RNG decided stuff for pathways that is know to have some probability shuffle, e.g. in the TCA cycle
   * True ending, good ending, normal ending and bad ending (convert to a story-like without saying the exact scientific word.) e.g. 
      * the true end is end up as ATP
      * good ending can have more, e.g. end up as fatty acid storage, becomes amino acid, etc
      * normal end can be ending up as CO2
      * a bad ending can be from if failing to reach a destination or from RNG stay in a cycle long enough for the host organism passed or radioactive decay. Or, if a player make change to an important residue in the enzyme breaking the important pathway and the host cannot survive.
2. The player act as the hero, C14, who can chose the character to start with, e.g. glucose, fatty acid, alcohol, other suger, etc. 
3.  About the "cast"/"NPC"
   * Proteins should be from the PDB. Due to possible large file size of huge protein, may need to prompt a data download step before the first time the user play a game.
   * small molecules are 3D models from either PubChem or PDB. 
   * Protonation must be under physiological pH or relevant to the enzymatic reaction, or the spectic physiological condition, or user-adjustable 
4. Gameplay must have the following elements:
   * simple text-based multiple choice
   * limited edits of the protein/small molecule. include option to restore or reveal correct 3D model for a smooth gameplay.
   * showing specific representation of residue as as the game proceed to certain stage
   * a board of achiement limited number of achievement unlock, limited collection of starting point and ending. save to a file so the use see it.
   * minimal stat/exp growing feature that unlock additional options, if u have a scientifically correct way to do it.
   * buttons to save the progress/state of the game and load a saved session
5. Documentaion: 
   * repo root README and in-game help text should include a drama-like cast of protein name, PDB ID, and resolution.
   * you may include some instructions on how to edit molecules in pymol, and/or point to pymol wiki.
   * a dramatic slogan should be included in both README and the in-game description, like "featuring high-resolution, real protein models in our cast"

# WORKING ENV

Currently we are using WSL ubuntu.

DO NOT install anything. DO NOT create any conda env.

python 3.6 is available in this shell to test syntax, but DO NOT install anything

To access the env with pymol (in a windows conda env), use setenv.bat which is a bat script for windows cmd.exe

Use the modern QT interface for pymol plugin

The version of pymol installed here is PyMOL2.5.0 from anaconda.

# Reference

We provide the repo of open-source pymol in ./tmp/pymol-src and repo of 3rd-party plugins in ./Pymol-script-repo which is git ignored for the agent to learn how to write pymol plugins


# Constraints

The code should be efficient, tracable, clean and safe. This repo should be structured.

The UI should be simple, user-friendly with clear but sufficient in-game explanation.

If a specific python library is needed other than the library required by pymol-open-source, the agent must write the list to a file and explicitly seek approval from the user. 
In this case, the user would either install locally or let the agent to obtain a local version of library for local import in ./3rd_party_lib, note the license of the library, and state if the user should setup a linux-like env or can keep the "calling cmd from wsl" approach. The downloaded lib should also be git-ignored.

Do NOT make up anything. ALL the claims and citations MUST BE VERIFIED against a source and explicitly approved by human.

**Seek my approval before you use any source. Any scientific knowledge must be cite, validated, and explicitly approved**


---

# Contents borrowed from the AGENTS.md of another repo that develop a pymol plugin

## Environment — the WSL/Windows split (read first)

This is the single most common way to break things.

- **Dev shell is WSL Ubuntu.** Do NOT install anything, do NOT create conda envs, do NOT `pip install`. `python3.6` (3.6.9) is for syntax checks and unit tests ONLY. (`opencode.json` denies `pip*`, `apt*`, `conda*`, `rm*`.)
- **PyMOL 2.5.0 runs in a Windows conda env**, not WSL. `setenv.bat` is a Windows cmd.exe batch that activates env `chemtools-win10` from `C:\ProgramData\Miniconda3`; it does NOT launch PyMOL — you run `pymol` from the activated shell. A WSL agent CANNOT run the interactive GUI, and CANNOT use Qt (`pymol.Qt.*`) at runtime.
- **Headless PyMOL CAN be run from WSL** (discovered Phase 3, 2026-08-06). `C:\src\run-conda-pymol.bat` accepts args passed through to `python .../pymol/__init__.py %*`. The `-cq` flags run PyMOL without the GUI (command-line, quiet). So a WSL agent CAN execute any pure-cmd script (no Qt, no interactive viewer) headlessly via:
  ```bash
  # 1. Stage the package + script to the Windows-facing path first:
  bash wsl2win_cp.sh                          # copies RPG_tale-of-C/ -> tmp/RPG_tale-of-C/RPG_tale-of-C/
  mkdir -p tmp/RPG_tale-of-C/smoke && cp smoke/phase3_smoke.py tmp/RPG_tale-of-C/smoke/  # stage the script
  # 2. Run headlessly (no GUI, ~30s for the phase3 smoke). Wrap in timeout + tail to avoid hangs:
  cd tmp/RPG_tale-of-C && timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\phase3_smoke.py" 2>&1 | tail -50
  # 3. Check exit code: 0 = clean (or sys.exit(1) caught by wrapper); nonzero = crash.
  ```
  This closes the WSL/Windows runtime gap for cmd-only scripts. It does NOT help with Qt (GUI/prompt tests still need a human in a real PyMOL session). Always `cd` into the staged Windows path first (PyMOL resolves relative paths against the cmd.exe cwd, which is the WSL cwd mapped to `\\wsl$` or the /mnt/c path — use the /mnt/c path so Windows PyMOL can read it).
- **Consequence:** any code path that executes `pymol.Qt.*` at runtime STILL cannot be run from WSL (GUI/Qt needs a real display). Pure `pymol.cmd.*` paths CAN be run headlessly as above. Only the pure data layer (`RPG_tale-of-C/setup_state.py`) is unit-testable in WSL without invoking PyMOL at all. Qt/GUI smoke tests remain human-verify checkpoints.
- `wsl2win_cp.sh` copies `RPG_tale-of-C/` to `tmp/RPG_tale-of-C/` so the Windows PyMOL Plugin Manager (or the headless cmd.exe invocation above) can point at a Windows-side path.
- **PyMOL source for API verification:** `tmp/pymol-src/` holds the PyMOL 2.5.0 open-source Python modules (gitignored — NOT present in parallel-execution worktrees). It IS readable from any worktree via the main-repo absolute path `tmp/pymol-src/modules/pymol/` (i.e. `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/RPG_tale-of-C/tmp/pymol-src/modules/pymol/`). When a plan cites an API with a `file:line` reference (e.g. `creating.py:960`, `editing.py:1424`, `querying.py:1269`, `viewing.py:491`, `editing.py:800`, `editing.py:1535`) and you need to confirm the signature or debug unexpected runtime behavior, Read the file at that absolute path. The inline citations are usually sufficient on their own; the source is for when the API behaves differently than the citation suggests (Phase 5 05-06 spike discovered `cmd.create(obj, seg, 1, 1)` is a NO-OP despite the citation — that kind of surprise is when you consult the source). Key modules: `creating.py` (create/fuse), `editing.py` (alter/alter_state/iterate/remove/sort), `querying.py` (identify/count_atoms/iterate), `viewing.py` (show/hide), `commanding.py` (delete/fetch), `wizard/` (wizard base).

## Code & UI standards (spec.md constraints)

- Code must be efficient, traceable, clean, and safe; the repo must be structured.
- UI must be simple and user-friendly, with clear but sufficient in-game explanation.

## Dependencies & attribution (spec.md constraints)

- Assume only what `pymol-open-source` ships (PyQt5 via `pymol.Qt`, numpy). If a specific Python lib is needed beyond that, the agent MUST write the list to a file and explicitly seek user approval first. Then the user either installs it locally, or the agent obtains a local copy for import from `./3rd_party_lib/` (git-ignored) with the library's license noted. When proposing a lib, state whether the user must set up a linux-like env or can keep the "calling cmd from WSL" approach. Do NOT `pip install` silently.
- Do NOT make up anything. ALL claims and citations (DOIs, PDB IDs, sources) MUST be verified against a source and explicitly approved by a human. Bundled demo sources are in `RPG_tale-of-C/data/demos/SOURCES.md`.

## Parallel subagent execution (worktree/branch protocol)

When `/gsd-execute-phase` runs **≥2 plans in parallel** (one wave with
multiple autonomous plans), each `gsd-executor` subagent commits on a
**shared git index** — concurrent `git add`/`git commit` calls race and
sweep in each other's staged files (happened in Phase 4 Wave 1: 3 agents,
~3 Rule-3 collision fixes). To eliminate this collision class:

- **One worktree per parallel plan.** Before spawning a wave, the
  orchestrator creates a git worktree (or branch) per parallel plan:
  `git worktree add tmp/exec-04-01 -b exec/04-01` (etc.). Each agent is
  spawned with `workdir=tmp/exec-04-01` so it commits on an isolated
  index — zero shared-index races.
- **Merge back in dependency order.** After all agents in the wave return,
  the orchestrator merges/fast-forwards each branch into the base in
  dependency order (`git merge exec/04-01`, then `exec/04-02`, ...). Real
  conflicts (same file touched by two plans — should be rare given
  disjoint `files_modified` frontmatter) are resolved explicitly here.
- **Single-plan waves skip this.** Waves with one plan (no parallelism)
  need no worktree — commit directly on the base branch. The protocol
  only applies when ≥2 plans run concurrently.
- **TDD multi-commit safety.** Each agent can still do atomic
  RED/GREEN/REFACTOR commits freely on its own branch — the per-task
  commit granularity is preserved (unlike an orchestrator-owned commit
  gate, which would collapse TDD's commit boundaries).

Orchestrators: if `parallelization: true` in `.planning/config.json` and a
wave has >1 plan, use this protocol. See `.planning/quick/001-*` for the
rationale + rejected alternatives (message-board lock, orchestrator commit
gate).
