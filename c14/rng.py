"""Seedable PRNG for the game. Single random.Random instance per playthrough.

Fixed-seed (demo/classroom) and random-seed (play) modes. State is
JSON-serializable for save/load (Anti-Pattern 7 mitigation).

This is the single seeded PRNG instance that ALL stochastic draws must use
(ARCHITECTURE.md Anti-Pattern 7: ad-hoc ``random.random()`` breaks classroom
reproducibility). The engine holds one ``RngEngine`` per playthrough, seeded at
``engine.start(seed)``; weighted choices, text-variant shuffles, and TCA
redistribution all draw from this one instance. The seed is part of GameState
and saved with the game, so a run is replayable.

Design constraints honored:
- Python 3.6 stdlib ONLY (``random``, ``secrets``). NO ``@dataclass`` (3.7+).
  Plain class on instance attributes, matching the Phase 1 ``CitationRegistry``
  precedent.
- NO pymol/PyQt5 imports (the Phase 1 AST gate scans this file).
- ``random.Random.getstate()`` returns a 3-tuple
  ``(version=3, internalstate=tuple-of-625-ints, gauss_next)``; JSON round-trip
  of the state (lists<->tuples) restores an equivalent engine and produces the
  same next draw (verified on python3.6.9).
- ``random.choices(pop, weights=w, k=1)`` is 3.6+ (verified).
"""

import random
import secrets


class RngEngine(object):
    """Seedable PRNG wrapping a single ``random.Random`` instance.

    Two construction modes:
    - Fixed-seed (demo/classroom repro): ``RngEngine(seed=42)``. Two engines
      with the same seed produce identical ``random()`` sequences.
    - Random-seed (play): ``RngEngine(seed=None)``. Picks a non-deterministic
      seed via ``secrets.randbits(31)`` and records it on ``self.seed`` so the
      run is replayable (the seed is saved with GameState).

    The internal ``random.Random`` state is JSON-serializable via
    :meth:`get_state` / :meth:`set_state` so a save/load round-trip restores the
    exact next draw (the PRNG position survives serialization).
    """

    def __init__(self, seed=None):
        # type: (object) -> None
        if seed is None:
            # Random/play mode: pick a non-deterministic seed and record it so
            # the run is replayable. randbits(31) yields a non-negative int <
            # 2**31 (a comfortable positive seed for random.Random).
            self._seed = secrets.randbits(31)
        else:
            # Fixed/demo mode: caller-provided seed (int) for reproducibility.
            self._seed = seed
        self._rng = random.Random(self._seed)

    @property
    def seed(self):
        # type: () -> int
        """The seed this engine was started with (saved with GameState).

        For random/play mode this is the auto-picked non-deterministic seed,
        so a run can be replayed by constructing ``RngEngine(seed=that_seed)``.
        """
        return self._seed

    def random(self):
        # type: () -> float
        """Return the next float in [0.0, 1.0) from the wrapped Random."""
        return self._rng.random()

    def weighted_pick(self, items, weights):
        # type: (list, list) -> object
        """Pick one item from ``items`` with per-item ``weights`` (3.6+ choices).

        Returns the picked item (not its index). Deterministic given the seed.
        """
        return self._rng.choices(items, weights=weights, k=1)[0]

    def get_state(self):
        # type: () -> dict
        """Return a JSON-serializable dict snapshot of the PRNG state.

        ``random.Random.getstate()`` returns ``(version, internalstate,
        gauss_next)`` where ``internalstate`` is a tuple of 625 ints. Tuples are
        not JSON-serializable, so the internal state is converted to a list.
        Use :meth:`set_state` (or :meth:`from_state`) to restore.
        """
        st = self._rng.getstate()
        return {
            "version": st[0],
            "state": list(st[1]),
            "gauss_next": st[2],
        }

    def set_state(self, state_dict):
        # type: (dict) -> None
        """Restore the PRNG state from a :meth:`get_state` dict.

        Converts the list back to a tuple for ``random.Random.setstate``.
        """
        self._rng.setstate((
            state_dict["version"],
            tuple(state_dict["state"]),
            state_dict["gauss_next"],
        ))

    @classmethod
    def from_state(cls, seed, state_dict):
        # type: (object, dict) -> RngEngine
        """Construct an RngEngine from ``seed`` and restore its PRNG state.

        Used on load to rebuild the exact PRNG position: the engine is
        constructed with the saved seed (so its identity/mode is known) and then
        its state is overwritten with the saved position, so the next draw
        matches the pre-save next draw.
        """
        eng = cls(seed)
        eng.set_state(state_dict)
        return eng

    def __repr__(self):
        return "RngEngine(seed={})".format(self._seed)
