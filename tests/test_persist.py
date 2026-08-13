"""Unit tests for c14.persist.SaveStore. Pure-Python, stdlib only.

Run: ``python3.6 -m unittest tests.test_persist -v``

Proves: save/load round-trip preserves all GameState fields (incl. seed +
rng_state); JSON is human-readable (indent=2, readable values present as
text); parent directories are created on save; malformed JSON raises
ValueError; a missing save file raises OSError.
"""
import json
import os
import shutil
import tempfile
import unittest

from c14.persist import SaveStore
from c14.state import GameState


class TestSaveStore(unittest.TestCase):
    """Round-trip + human-readable JSON + parent-dir creation + error paths."""

    def setUp(self):
        # Track temp files/dirs created per-test; clean in tearDown.
        self._paths = []
        self._dirs = []

    def tearDown(self):
        for p in self._paths:
            try:
                os.unlink(p)
            except OSError:
                pass
        for d in self._dirs:
            try:
                shutil.rmtree(d)
            except OSError:
                pass

    def _mkstate(self):
        # type: () -> GameState
        """A fully-populated GameState (every field set, incl. rng_state)."""
        return GameState(
            seed=235,
            character="glucose",
            current_node="intro.start",
            flags={"seen_tca": True},
            counters={"turns": 5},
            visit_counts={"intro.start": 1},
            edits_history=[],
            rng_state={"version": 3, "state": [0] * 625, "gauss_next": None},
            started_at="2026-08-13T00:00:00Z",
        )

    def _tmpfile(self, name="save.json"):
        # type: (str) -> str
        """A path inside a fresh temp dir (cleaned in tearDown)."""
        d = tempfile.mkdtemp()
        self._dirs.append(d)
        p = os.path.join(d, name)
        self._paths.append(p)
        return p

    def test_save_load_roundtrip(self):
        """save then load returns an equal GameState (all fields preserved,
        including seed + rng_state)."""
        s = self._mkstate()
        p = self._tmpfile()
        SaveStore.save(s, p)
        loaded = SaveStore.load(p)
        self.assertEqual(loaded.to_dict(), s.to_dict(),
                         "round-trip preserves all fields incl. rng_state")

    def test_save_creates_parent_dir(self):
        """save to a nested path creates the parent directories."""
        s = self._mkstate()
        d = tempfile.mkdtemp()
        self._dirs.append(d)
        nested = os.path.join(d, "sub", "nested", "save.json")
        self._paths.append(nested)
        SaveStore.save(s, nested)
        self.assertTrue(os.path.isfile(nested), "nested save file created")
        self.assertTrue(os.path.isdir(os.path.dirname(nested)),
                        "parent directories created")

    def test_save_json_is_human_readable(self):
        """The saved file is valid, indented JSON with readable values."""
        s = self._mkstate()
        p = self._tmpfile()
        SaveStore.save(s, p)
        with open(p, "r", encoding="utf-8") as fh:
            txt = fh.read()
        self.assertIn('"seed": 235', txt, "seed value present as text")
        self.assertIn('"character": "glucose"', txt,
                      "character value present as text")
        self.assertIn("\n", txt, "indent=2 produces newlines (human-readable)")
        self.assertIn("  ", txt, "indent=2 produces 2-space indentation")
        # Must be valid JSON (round-trips through json.loads).
        json.loads(txt)

    def test_load_malformed_raises(self):
        """load of a malformed JSON file raises ValueError (JSONDecodeError is
        a ValueError subclass)."""
        p = self._tmpfile()
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("{ this is not json")
        with self.assertRaises(ValueError):
            SaveStore.load(p)

    def test_load_missing_raises(self):
        """load of a nonexistent path raises OSError (FileNotFoundError is an
        OSError subclass)."""
        with self.assertRaises(OSError):
            SaveStore.load("/nonexistent/path/that/does/not/exist.json")


if __name__ == "__main__":
    unittest.main()
