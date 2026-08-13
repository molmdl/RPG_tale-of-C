"""Unit tests for c14.rng.RngEngine. Pure-Python, stdlib only.

Run: ``python3.6 -m unittest tests.test_rng -v``

Covers: same-seed determinism, diff-seed divergence, random-mode seed recording,
fixed-mode reproducibility via state, JSON state round-trip, weighted-pick
determinism.
"""
import json
import unittest

from c14.rng import RngEngine


class TestRngEngine(unittest.TestCase):

    def test_same_seed_same_sequence(self):
        """Two RngEngine(42) produce identical random() sequences (determinism)."""
        a = RngEngine(42)
        b = RngEngine(42)
        seq_a = [a.random() for _ in range(10)]
        seq_b = [b.random() for _ in range(10)]
        self.assertEqual(seq_a, seq_b)

    def test_diff_seed_diff_sequence(self):
        """RngEngine(42) vs RngEngine(43) produce different first draws."""
        a = RngEngine(42)
        c = RngEngine(43)
        self.assertNotEqual(a.random(), c.random())

    def test_random_mode_records_seed(self):
        """RngEngine(None) produces an int seed; two such engines differ."""
        eng = RngEngine(None)
        self.assertIsInstance(eng.seed, int)
        eng2 = RngEngine(None)
        # Non-deterministic: two random-mode engines almost surely get
        # different seeds (2**31 space). Assert inequality.
        self.assertNotEqual(eng.seed, eng2.seed)

    def test_fixed_mode_reproducible(self):
        """A second engine built from (seed, get_state after N draws) matches the (N+1)th draw."""
        eng = RngEngine(42)
        for _ in range(5):
            eng.random()
        st = eng.get_state()
        # Rebuild from the saved seed + state.
        eng2 = RngEngine.from_state(42, st)
        # The 6th draw of eng must equal the next draw of eng2.
        self.assertEqual(eng.random(), eng2.random())

    def test_state_json_roundtrip(self):
        """PRNG state survives json.dumps/loads and restores the exact next draw."""
        eng = RngEngine(7)
        eng.random()
        eng.random()
        st = eng.get_state()
        js = json.dumps(st)
        st2 = json.loads(js)
        eng2 = RngEngine.from_state(7, st2)
        self.assertEqual(eng.random(), eng2.random())

    def test_weighted_pick_deterministic(self):
        """Same seed + same weights -> same weighted_pick; a different seed may differ."""
        a = RngEngine(1)
        b = RngEngine(1)
        pick_a = a.weighted_pick(["a", "b"], [1, 2])
        pick_b = b.weighted_pick(["a", "b"], [1, 2])
        self.assertEqual(pick_a, pick_b)
        # The picked item is one of the inputs.
        self.assertIn(pick_a, ("a", "b"))
        # A different seed is *likely* to differ for a 2-item 1:2 split, but
        # this is not strictly guaranteed on every seed. We assert determinism
        # (above) as the hard property; the diff-seed case is exercised in
        # test_diff_seed_diff_sequence for the raw random() draw which is a
        # stronger guarantee.


if __name__ == "__main__":
    unittest.main()
