# AGENTS.md

PyMOL plugin project: an RPG game following a carbon atom — the hero (tracked through the pathway as the isotope C14) — through the respiratory pathway. Spec lives in `spec.md` (authoritative for plot, constraints, and the "do not install / do not make up citations" rules — read it first). Repo is in early stage: no plugin code yet, only spec + reference material.

> **Hero-identity note (anti-confusion):** the hero is a *carbon atom*; C14 is its *tracking isotope label*, not the hero's fate or identity. The spec's "true end = become ATP" is reconciled via the **soul-jump reframing** (the carbon's electrons — the narrative "soul" — flow via NADH/FADH2 → ETC → ATP synthase; the carbon body is shed as CO2; True ending = soul harvested into ATP, tied to the RNG TCA shuffle). See `.planning/PROJECT.md` Key Decisions (Pitfall 4, RESOLVED 2026-08-13). **Do not reintroduce** claims that the C14 carbon itself becomes ATP or enters oxidative phosphorylation — those are scientifically wrong. Pitfall 9 (C14 radioactive-decay timescale) remains a separate Pending decision.

## Environment — the WSL/Windows split (read first)

The single most common way to break things.

- **Dev shell is WSL Ubuntu.** Do NOT install anything, do NOT create conda envs, do NOT `pip install`. `python3.6` (3.6.9) is for syntax checks and unit tests of pure-Python (non-PyMOL) modules ONLY. `opencode.json` denies `rm*`, `rg*`; most other commands (pip/apt/conda/python/mv/wget/curl) are `ask`.
- **PyMOL 2.5.0 runs in a Windows conda env** (`chemtools-win10`), NOT WSL. A WSL agent CANNOT launch the interactive GUI and CANNOT exercise `pymol.Qt.*` at runtime — Qt needs a real display.
- **Headless PyMOL CAN be run from WSL** via `C:\src\run-conda-pymol.bat`, which activates the Windows env and runs `python .../pymol/__init__.py %*`. Pass `-cq` for no-GUI quiet. Pattern for a pure-`pymol.cmd.*` script (no Qt, no viewer):
  ```bash
  # cd into a Windows-readable path first (PyMOL resolves relative paths against the cmd.exe cwd).
  # /mnt/c/... paths are readable by Windows PyMOL; \\wsl$ paths work but are flakier.
  timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq path\\to\\script.py" 2>&1 | tail -50
  # exit 0 = clean; nonzero = crash.
  ```
  This closes the WSL/Windows gap for cmd-only scripts. It does NOT help with Qt — GUI/prompt tests remain human-verify checkpoints.
- **`setenv.bat` / `wsl2win_cp.sh` referenced in `spec.md` do NOT exist in this repo** (borrowed verbatim from a sibling project's AGENTS.md). Do not call or rely on them. `run-conda-pymol.bat` at `/mnt/c/src/` is the real, verified entry point.

## Reference sources (read-only, gitignored / symlinked)

- **`tmp/pymol-src/`** — symlink to the PyMOL 2.5.0 open-source Python modules. Read API signatures here when a citation behaves differently than expected. Key modules: `creating.py` (create/fuse), `editing.py` (alter/alter_state/iterate/remove/sort), `querying.py` (identify/count_atoms/iterate), `viewing.py` (show/hide), `commanding.py` (delete/fetch), `wizard/` (wizard base). Path: `tmp/pymol-src/modules/pymol/`.
- **`Pymol-script-repo/`** — symlink to 3rd-party PyMOL plugins (31 single-file plugins in `plugins/`). Use as idiomatic reference for plugin structure and PyQt conventions (e.g. `plugins/dynoplot.py` shows the modern `from pymol.Qt import QtCore, QtGui, QtWidgets` style).
- **`LICENSE_pymol-open-source`** — license for the bundled/derived PyMOL source. Keep attribution when borrowing patterns.

## Constraints from spec.md (non-negotiable)

- **No fabricated science.** ALL claims and citations (DOIs, PDB IDs, pathway facts) MUST be verified against a source and explicitly approved by the human. Seek approval before using any source.
- **No new dependencies silently.** Assume only what `pymol-open-source` ships (PyQt5 via `pymol.Qt`, numpy). If another lib is needed, write the list to a file, seek user approval, and either the user installs it or the agent vendoring a local copy under `./3rd_party_lib/` (git-ignored) with its license noted. State whether setup needs a linux env or can keep the WSL-calls-cmd approach.
- **Use the modern Qt interface** for the plugin (`pymol.Qt`, not the legacy `pmgqt`/`Tk`).
- **Protonation** must be physiological pH or reaction-relevant, or user-adjustable.
- Code must be efficient, traceable, clean, safe; repo must be structured. UI simple and user-friendly with clear in-game explanation.
- `Pymol-script-repo`, `tmp`, `3rd_party_lib/**`, `*.env`, `*.npy`/`*.npz`, and secrets are git-ignored — do not commit them.

## Plugin conventions to follow

- Single-file plugins in `Pymol-script-repo/plugins/` use the modern form `from pymol.Qt import QtCore, QtGui, QtWidgets`. Match this.
- Plugin GUIs are QtWidgets subclasses; `pymol.cmd.*` for all molecular operations. Never reach into PyMOL internals when a `cmd.` API exists — verify against `tmp/pymol-src/modules/pymol/` first.

## Verification

- Pure-Python (non-PyMOL) modules: `python3.6 -m py_compile <file>` for syntax; `python3.6 -m unittest` / `python3.6 -m pytest` if tests exist (none yet).
- Pure-`pymol.cmd.*` scripts: headless via `run-conda-pymol.bat -cq` (above). Wrap in `timeout`; tail output.
- Qt / GUI code: human-verify in a real Windows PyMOL session — cannot be automated from WSL.
