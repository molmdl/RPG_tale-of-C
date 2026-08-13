"""Mutable per-playthrough state: current node, character, flags, counters,
visit counts, edit history, RNG seed + state, protonation pref, ending.

JSON-serializable via to_dict/from_dict. Pure-Python, stdlib only.

GameState is pure data -- it does NOT hold a live ``RngEngine``; it stores
``seed`` + ``rng_state`` (the serialized PRNG state) so the engine can rebuild
the ``RngEngine`` on load (ARCHITECTURE.md "GameState (the saveable unit)" +
Anti-Pattern 7: RNG state must persist across save/load).

Design constraints honored:
- Python 3.6 stdlib ONLY (``datetime`` for ``started_at``). NO ``@dataclass``
  (3.7+). Plain class on instance attributes, matching the Phase 1
  ``CitationRegistry`` precedent.
- NO pymol/PyQt5 imports (the Phase 1 AST gate scans this file).
- ``to_dict`` key order matches the ARCHITECTURE.md GameState JSON shape so
  saves are human-readable and diff-stable; ``from_dict`` reads every field
  with ``.get`` defaults so partial/older saves don't crash.
- The ``rng_state`` field carries the dict from ``RngEngine.get_state()`` (or
  None before the first draw); the engine syncs it into state before save and
  rebuilds the RngEngine from (seed, rng_state) on load.
"""

import datetime


class GameState(object):
    """The saveable per-playthrough state.

    Attributes:
        version: save-format version (for future migrations). Defaults to 1.
        seed: the RngEngine seed this playthrough started with.
        character: the player's molecule character (e.g. "glucose").
        current_node: the dotted id of the node the player is currently at.
        flags: dict of boolean story flags (e.g. {"seen_tca": True}).
        counters: dict of integer counters (e.g. {"turns": 12, "edits_made": 1}).
        visit_counts: dict of node_id -> visit count (cycle-trap detection).
        edits_history: list of edit records (context + intent + route).
        rng_state: serialized RngEngine state (dict from get_state()) or None.
        protonation_pref: "physiological" (default) or a user-adjustable value.
        started_at: ISO-8601 UTC timestamp string the game started at.
        finished: None while playing, truthy when an ending node is reached.
        ending_tier: the ending tier ("true"|"good"|"normal"|"bad") or None.
    """

    def __init__(self, seed=0, character="glucose", current_node=None,
                 flags=None, counters=None, visit_counts=None,
                 edits_history=None, rng_state=None,
                 protonation_pref="physiological", started_at=None,
                 finished=None, ending_tier=None, version=1):
        # type: (object, str, str, dict, dict, dict, list, dict, str, str, object, str, int) -> None
        self.version = version
        self.seed = seed
        self.character = character
        self.current_node = current_node
        self.flags = flags if flags is not None else {}
        self.counters = counters if counters is not None else {}
        self.visit_counts = visit_counts if visit_counts is not None else {}
        self.edits_history = edits_history if edits_history is not None else []
        self.rng_state = rng_state
        self.protonation_pref = protonation_pref
        self.started_at = started_at
        self.finished = finished
        self.ending_tier = ending_tier

    def to_dict(self):
        # type: () -> dict
        """Serialize to a JSON-ready dict matching the ARCHITECTURE.md shape.

        Key order is stable (version, seed, character, current_node, flags,
        counters, visit_counts, edits_history, rng_state, protonation_pref,
        started_at, finished, ending_tier) so saves are human-readable and
        diff-stable. ``rng_state`` is the dict from ``RngEngine.get_state()``
        or None.
        """
        return {
            "version": self.version,
            "seed": self.seed,
            "character": self.character,
            "current_node": self.current_node,
            "flags": dict(self.flags),
            "counters": dict(self.counters),
            "visit_counts": dict(self.visit_counts),
            "edits_history": list(self.edits_history),
            "rng_state": self.rng_state,
            "protonation_pref": self.protonation_pref,
            "started_at": self.started_at,
            "finished": self.finished,
            "ending_tier": self.ending_tier,
        }

    @classmethod
    def from_dict(cls, d):
        # type: (dict) -> GameState
        """Build a GameState from a parsed dict, tolerating missing fields.

        Reads every field with ``.get`` defaults so partial/older saves don't
        crash (forward-compatible with future field additions).
        """
        return cls(
            version=d.get("version", 1),
            seed=d.get("seed", 0),
            character=d.get("character", "glucose"),
            current_node=d.get("current_node"),
            flags=d.get("flags"),
            counters=d.get("counters"),
            visit_counts=d.get("visit_counts"),
            edits_history=d.get("edits_history"),
            rng_state=d.get("rng_state"),
            protonation_pref=d.get("protonation_pref", "physiological"),
            started_at=d.get("started_at"),
            finished=d.get("finished"),
            ending_tier=d.get("ending_tier"),
        )

    @classmethod
    def new_game(cls, character, seed, start_node_id):
        # type: (str, object, str) -> GameState
        """Convenience constructor for a fresh playthrough.

        Sets ``started_at`` to a UTC ISO-8601 timestamp, ``current_node`` to the
        start node, ``seed`` to the provided seed, and ``rng_state`` to None
        (the engine fills it after the first draw).
        """
        started_at = datetime.datetime.utcnow().isoformat() + "Z"
        return cls(
            seed=seed,
            character=character,
            current_node=start_node_id,
            rng_state=None,
            started_at=started_at,
        )

    # -- small helpers (used by the interpreter's choice effects) -------------

    def flag(self, name):
        # type: (str) -> bool
        """Return the value of flag ``name`` (False if unset)."""
        return self.flags.get(name, False)

    def set_flag(self, name, value=True):
        # type: (str, object) -> None
        """Set flag ``name`` to ``value`` (default True)."""
        self.flags[name] = value

    def incr(self, name, by=1):
        # type: (str, int) -> None
        """Increment counter ``name`` by ``by`` (default 1), starting from 0."""
        self.counters[name] = self.counters.get(name, 0) + by

    def record_visit(self, node_id):
        # type: (str) -> None
        """Bump the visit count for ``node_id`` (cycle-trap detection)."""
        self.visit_counts[node_id] = self.visit_counts.get(node_id, 0) + 1

    def add_edit(self, edit_record):
        # type: (dict) -> None
        """Append an edit record to history and bump the ``edits_made`` counter."""
        self.edits_history.append(edit_record)
        self.counters["edits_made"] = self.counters.get("edits_made", 0) + 1

    def mark_finished(self, ending_tier):
        # type: (str) -> None
        """Mark the playthrough finished with the given ending tier.

        Called by the interpreter when entering an ending node. Sets
        ``finished`` truthy and records the ``ending_tier``.
        """
        self.finished = True
        self.ending_tier = ending_tier

    # -- dunder --------------------------------------------------------------

    def __eq__(self, other):
        if not isinstance(other, GameState):
            return NotImplemented
        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __repr__(self):
        return "GameState(seed={!r}, character={!r}, current_node={!r}, finished={!r})".format(
            self.seed, self.character, self.current_node, self.finished)
