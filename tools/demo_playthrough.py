#!/usr/bin/env python3.6
"""Runnable architecture-proof demo. Plays the minimal 2-node story in WSL
(no PyMOL/Qt), prints the playthrough, saves, loads, prints restored state.
Exits 0. This is the tangible Phase 2 proof point -- the whole game
architecture works end-to-end in pure Python before any PyMOL/Qt code is
written.

Run::

    python3.6 tools/demo_playthrough.py

The demo is deterministic (fixed seed 42) so the output is reproducible -- a
classroom/demo artifact. It prints the dramatic + teaching text of each node,
the weighted choices (with the RNG's pick), every MolAction the engine emits
(the domain -> pymol_layer intent flow -- the testability boundary made
visible), the ending, the full game-state JSON, then a save/load round-trip
that re-enters the current node by replaying its on_enter MolActions
(Pattern 6: the scene is a pure function of game state, NOT a saved .pse
session -- Anti-Pattern 5 avoided).

Design constraints honored:
- Python 3.6 stdlib ONLY (``os``, ``sys``, ``tempfile``, ``json``). NO
  pymol/PyQt5 imports -- the demo imports only ``c14.*`` pure-Python modules
  and runs entirely in WSL.
- ``sys.path`` insertion of the repo root (same pattern as
  ``tools/check_citations.py`` -- this script lives in ``tools/``, not in
  ``c14/``, so it must put the repo root on ``sys.path`` to import the
  package without install).
- ``GameEngine`` dispatches MolActions PER-ACTION to the sink (the 02-04
  contract): the sink receives an individual ``MolAction`` per call, so the
  demo's ``sink(action)`` prints one MolAction per emission (not a list).
- CWD-independent: ``STORY_DIR`` is resolved relative to ``__file__`` so
  the demo runs from any working directory.
- ``.format()`` for string interpolation (the established repo convention).
"""

import os
import sys
import tempfile
import json

# Make the c14 package importable when run as a loose script from the repo.
# Resolves repo root from __file__ so the script runs regardless of CWD
# (same pattern as tools/check_citations.py).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from c14.engine import GameEngine  # noqa: E402  (sys.path setup above)
from c14.story.graph import StoryGraph  # noqa: E402  (sys.path setup above)

# Story directory resolved relative to this file (CWD-independent).
STORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "data", "story")
# Fixed demo seed for deterministic, reproducible output (classroom/demo).
SEED = 42


def main():
    # type: () -> None
    print("=== RPG: Tale of C -- Architecture Proof (Phase 2, WSL, no PyMOL) ===")
    print("")

    # Mock MolAction sink: prints each MolAction as the engine emits it.
    # Per-action dispatch (02-04 contract): the sink receives ONE MolAction
    # per call -- this makes the domain -> pymol_layer intent flow visible
    # (the testability boundary made tangible).
    def sink(action):
        print("  [MolAction] op={}, target={}, args={}".format(
            action.op, action.target, action.args))

    g = StoryGraph.load(STORY_DIR)
    eng = GameEngine(g, molaction_sink=sink)

    # --- Start node ------------------------------------------------------
    print("")
    print("--- Node: {} ---".format(g.start_node()))
    tr = eng.start('glucose', SEED)
    print(tr.node.text_dramatic)
    print(tr.node.text_teaching)
    print("Choices:")
    for i, c in enumerate(tr.node.choices):
        print("  [{}] {} (weight={}, goto={})".format(
            i, c.label, c.weight, c.goto))

    # --- Make the weighted choice (RNG decides; index ignored) ----------
    print("")
    print("--- Choice made (RNG-weighted, seed={}) ---".format(SEED))
    tr = eng.choose(0)
    print("--- Node: {} (ENDING: {}) ---".format(tr.node.id, tr.node.is_ending))
    print(tr.node.text_dramatic)
    print(tr.node.text_teaching)

    # --- Game state ------------------------------------------------------
    print("")
    print("--- Game state: ---")
    print(json.dumps(eng.state.to_dict(), indent=2))

    # --- Save ------------------------------------------------------------
    p = os.path.join(tempfile.mkdtemp(), "demo_save.json")
    eng.save(p)
    print("")
    print("--- Saved to: {} ---".format(p))

    # --- Load (replays on_enter MolActions above) ------------------------
    print("")
    print("--- Loading (replayed on_enter MolActions above) ---")
    eng2 = GameEngine(g, molaction_sink=sink)
    tr2 = eng2.load(p)
    print("--- Restored state: ---")
    print(json.dumps(eng2.state.to_dict(), indent=2))

    # --- In-script sanity check ------------------------------------------
    print("")
    assert eng2.state.to_dict() == eng.state.to_dict(), (
        "load must restore identical state")
    print("VERIFY: loaded state identical to saved state -- OK")

    print("")
    print("=== Architecture proof complete (exit 0) ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
