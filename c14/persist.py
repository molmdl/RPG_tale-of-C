"""SaveStore: serialize/restore GameState to human-readable JSON. Pure data
(de)serialization -- the engine owns the on_enter MolAction replay on load
(Pattern 6: the scene is a pure function of game state, not a .pse session).
Pure-Python, stdlib only.

The engine replays the current node's on_enter MolActions after load to
reconstruct the molecular scene (see GameEngine.load). SaveStore does NOT save
a .pse PyMOL session (Anti-Pattern 5).

Design constraints honored:
- Python 3.6 stdlib ONLY (``json``, ``os``). NO pymol/PyQt5 imports (the Phase 1
  AST gate scans this file). NO ``@dataclass`` (3.7+).
- ``indent=2`` for human-readable, diff-friendly saves (Decision D2). A trailing
  newline is written for clean file diffs.
- Parent directories are created on save (``os.makedirs(..., exist_ok=True)``)
  so callers can save to nested paths without pre-creating them. The makedirs
  is guarded against paths with no dirname (e.g. just "save.json") where
  ``os.path.dirname`` returns "".
- ``SaveStore.load`` lets ``ValueError`` (malformed JSON; ``JSONDecodeError`` is
  a ``ValueError`` subclass) and ``OSError`` (missing/unreadable file) propagate
  to the caller -- the engine/caller handles save-load errors.
"""

import json
import os

from c14.state import GameState


class SaveStore(object):
    """Serialize/restore GameState to human-readable JSON.

    Pure data (de)serialization -- it does NOT replay MolActions and does NOT
    save a .pse session. The engine owns the on_enter replay on load (Pattern 6:
    the molecular scene is a pure function of game state, not a saved session).
    """

    @staticmethod
    def save(state, path):
        # type: (GameState, str) -> None
        """Write ``state`` to ``path`` as human-readable JSON (indent=2).

        Creates the parent directory if needed (guarded against paths with no
        dirname -- e.g. just "save.json" -- where ``os.path.dirname`` is "").
        Adds a trailing newline for clean file diffs.
        """
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state.to_dict(), fh, indent=2, sort_keys=False)
            fh.write("\n")

    @staticmethod
    def load(path):
        # type: (str) -> GameState
        """Read ``path`` and return a restored GameState.

        Raises ``ValueError`` on malformed JSON (``json.JSONDecodeError`` is a
        ``ValueError`` subclass) and ``OSError`` on a missing/unreadable file;
        both propagate to the caller (the engine handles save-load errors).
        """
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return GameState.from_dict(data)

    def __repr__(self):
        return "SaveStore()"
