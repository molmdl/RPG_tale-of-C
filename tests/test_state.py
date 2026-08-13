"""Unit tests for c14.state.GameState. Pure-Python, stdlib only.

Run: ``python3.6 -m unittest tests.test_state -v``

Covers: defaults, to_dict key set, full JSON round-trip (incl. rng_state),
human-readable JSON, new_game started_at, helper methods, from_dict tolerance
of missing fields.
"""
import json
import unittest

from c14.state import GameState


class TestGameState(unittest.TestCase):

    def test_defaults(self):
        """GameState() has empty dicts/lists, version=1, physiological pref, finished=None."""
        s = GameState()
        self.assertEqual(s.flags, {})
        self.assertEqual(s.counters, {})
        self.assertEqual(s.visit_counts, {})
        self.assertEqual(s.edits_history, [])
        self.assertEqual(s.version, 1)
        self.assertEqual(s.protonation_pref, "physiological")
        self.assertIsNone(s.finished)
        self.assertIsNone(s.ending_tier)
        self.assertIsNone(s.rng_state)
        self.assertIsNone(s.current_node)
        self.assertIsNone(s.started_at)

    def test_to_dict_keys(self):
        """to_dict() has the full ARCHITECTURE.md GameState key set."""
        d = GameState().to_dict()
        expected_keys = {
            "version", "seed", "character", "current_node", "flags",
            "counters", "visit_counts", "edits_history", "rng_state",
            "protonation_pref", "started_at", "finished", "ending_tier",
        }
        self.assertEqual(set(d.keys()), expected_keys)

    def test_roundtrip_preserves_all_fields(self):
        """Full JSON round-trip preserves every field including rng_state."""
        original = GameState(
            seed=235,
            character="glucose",
            current_node="tca.resolve",
            flags={"seen_tca": True},
            counters={"turns": 12, "edits_made": 1},
            visit_counts={"tca.entry": 1},
            edits_history=[{"context": "x", "intent": {}}],
            rng_state={"version": 3, "state": [0] * 625, "gauss_next": None},
            started_at="2026-08-13T00:00:00Z",
            finished=None,
        )
        js = json.dumps(original.to_dict())
        restored = GameState.from_dict(json.loads(js))
        self.assertEqual(restored.to_dict(), original.to_dict())

    def test_json_human_readable(self):
        """JSON output is human-readable (indent, readable values present as text)."""
        state = GameState(seed=235, character="glucose")
        js = json.dumps(state.to_dict(), indent=2)
        self.assertIn('"seed": 235', js)
        self.assertIn('"character": "glucose"', js)

    def test_new_game_sets_started_at(self):
        """new_game() sets a non-None started_at and the start current_node."""
        s = GameState.new_game("glucose", 42, "intro.start")
        self.assertIsNotNone(s.started_at)
        self.assertEqual(s.current_node, "intro.start")
        self.assertEqual(s.seed, 42)
        self.assertEqual(s.character, "glucose")
        self.assertIsNone(s.rng_state)

    def test_helpers(self):
        """flag/set_flag/incr/record_visit/mark_finished behave as specified."""
        state = GameState()
        state.set_flag("seen_tca")
        self.assertTrue(state.flag("seen_tca"))
        # Default flag value is False for unset.
        self.assertFalse(state.flag("other"))

        state.incr("turns")
        state.incr("turns")
        self.assertEqual(state.counters["turns"], 2)

        state.record_visit("n1")
        state.record_visit("n1")
        self.assertEqual(state.visit_counts["n1"], 2)

        state.mark_finished("good")
        self.assertTrue(state.finished)
        self.assertEqual(state.ending_tier, "good")

    def test_from_dict_tolerates_missing(self):
        """from_dict does not raise when fields are missing (graceful defaults)."""
        s = GameState.from_dict({"seed": 1, "character": "x"})
        self.assertEqual(s.seed, 1)
        self.assertEqual(s.character, "x")
        self.assertEqual(s.flags, {})
        self.assertEqual(s.counters, {})
        self.assertEqual(s.version, 1)
        self.assertIsNone(s.rng_state)


if __name__ == "__main__":
    unittest.main()
