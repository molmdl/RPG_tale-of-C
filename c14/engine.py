"""GameEngine: the turn loop. Wires StoryInterpreter + GameState + RngEngine.
Emits MolActions to an injected sink (never cmd.* -- testability boundary).
Save/load syncs RNG state and replays on_enter to reconstruct the scene
(Pattern 6). Pure-Python, stdlib only.

This is the ARCHITECTURE.md "Data Flow / Playthrough Walkthrough" + Pattern 6
design, adopted near-verbatim. The engine is the controller's pure-Python
collaborator: it pulls the current node, presents choices, receives the
player's choice (or the RNG's weighted pick), applies effects, advances, and
emits on_enter MolActions to an injected ``molaction_sink`` (a callable taking
a single MolAction -- dispatched per action, so a plain list's ``.append`` is
the mock sink in tests). The engine NEVER calls ``cmd.*`` -- the sink is the
testability boundary (in Phase 4+ the controller dispatches to
``c14/pymol_layer/molops.py``).

Save/load (Pattern 6): ``save`` syncs the live ``RngEngine`` state into
``GameState`` then serializes via ``SaveStore``; ``load`` restores
``GameState`` AND rebuilds the ``RngEngine`` from ``(seed, rng_state)`` via
``RngEngine.from_state``, then replays the current node's ``on_enter``
MolActions to reconstruct the scene (the molecular scene is a pure function
of game state, NOT a saved .pse session -- Anti-Pattern 5 avoided). The
replay uses ``record_visit=False`` so loading does NOT double-count visits.

Design constraints honored:
- Python 3.6 stdlib ONLY. NO pymol/PyQt5 imports (the Phase 1 AST gate scans
  this file). NO ``random`` import -- the ``RngEngine`` is owned, not ad-hoc
  (Anti-Pattern 7: all stochastic draws go through the single seeded engine).
- Plain classes (NOT ``@dataclass``) for ``TurnResult`` and ``GameEngine``,
  matching the Phase 1 ``CitationRegistry`` precedent and the Plan 01
  ``Node`` / ``RngEngine`` / ``GameState`` classes.
- ``.format()`` for string interpolation (the established repo convention).
"""

from c14.story.graph import StoryGraph  # noqa: F401 (type hint in docstrings)
from c14.story.interpreter import StoryInterpreter
from c14.rng import RngEngine
from c14.state import GameState
from c14.persist import SaveStore
from c14.story.model import MolAction, EditIntent  # noqa: F401 (docstring refs)
from c14.edit_router import EditRoutingError  # noqa: F401 (raised by route(); docstring ref)


class TurnResult(object):
    """The result of one turn: the current Node, the on_enter MolActions
    emitted on entry, and the eligible Choices the player can pick from.

    ``eligible_choices`` is None or [] at an ending node (no choices offered).
    For a non-ending node it is the node's raw ``choices`` list; the UI/test can
    filter by condition/weight -- the engine does not pre-draw the RNG for the
    presentation (the RNG is only consumed when ``choose`` resolves a weighted
    pick).
    """

    def __init__(self, node, molactions, eligible_choices=None):
        # type: (object, list, list) -> None
        self.node = node
        self.molactions = molactions
        self.eligible_choices = eligible_choices

    def __repr__(self):
        return "TurnResult(node={!r}, molactions={}, eligible_choices={})".format(
            self.node,
            len(self.molactions),
            len(self.eligible_choices) if self.eligible_choices is not None else None)


class GameEngine(object):
    """The turn loop: wires StoryInterpreter + GameState + RngEngine and emits
    on_enter MolAction lists to an injected sink.

    The engine owns one ``GameState`` and one ``RngEngine`` per playthrough
    (constructed at ``start`` / rebuilt at ``load``). It delegates graph
    walking to the stateless ``StoryInterpreter`` (conditions, weighted picks,
    effects, on_enter emission, visit recording, ending detection).

    An optional ``edit_router`` (Phase 4) enables ``apply_player_edit``: route
    a player's :class:`~c14.story.model.EditIntent` to a story node (known ->
    branch, unknown -> bad-ending pool), record it in ``edits_history``, and
    enter the routed node. When ``None`` (default), edit-routing is disabled --
    ``start``/``choose``/``save``/``load`` work unchanged (backward-compatible).
    """

    def __init__(self, graph, molaction_sink=None, edit_router=None):
        # type: (StoryGraph, object, object) -> None
        self.graph = graph
        self.interpreter = StoryInterpreter()
        self.molaction_sink = molaction_sink
        self.edit_router = edit_router
        self.state = None
        self.rng = None

    def start(self, character="glucose", seed=None):
        # type: (str, object) -> TurnResult
        """Begin a new game: build the RngEngine, init GameState at the start
        node, and enter the start node (emitting its on_enter MolActions).

        ``seed=None`` -> random/play mode (the engine records the auto-picked
        seed on GameState for replay). ``seed=int`` -> fixed/demo mode. Returns
        the TurnResult for the start node.
        """
        self.rng = RngEngine(seed)
        start_id = self.graph.start_node()
        self.state = GameState.new_game(character, self.rng.seed, start_id)
        return self._enter(start_id)

    def choose(self, index=0):
        # type: (int) -> TurnResult
        """Make a choice on the current node and advance.

        Resolves the choice via the interpreter:
        - If the current node's eligible choices are weighted (RNG decides),
          the interpreter returns a single ``Choice`` and ``index`` is ignored
          (the RNG picked).
        - If the choices are non-weighted (the player picks), the interpreter
          returns the eligible ``list[Choice]`` and ``index`` selects among
          them (out of range raises ``IndexError``).
        Applies the choice's effects, then advances to ``choice.goto`` (entering
        the next node, emitting its on_enter). Returns the new node's TurnResult.
        """
        node = self.graph.get_node(self.state.current_node)
        pick = self.interpreter.pick_choice(node, self.state, self.rng)
        if isinstance(pick, list):
            # non-weighted: the player selects by index.
            if index < 0 or index >= len(pick):
                raise IndexError(
                    "choice index {} out of range ({} eligible choices)".format(
                        index, len(pick)))
            choice = pick[index]
        else:
            # weighted: the RNG decided; index is ignored.
            choice = pick
        self.interpreter.apply_effects(choice, self.state)
        return self._enter(choice.goto)

    def apply_player_edit(self, edit_intent, enzyme_id):
        # type: (EditIntent, str) -> TurnResult
        """Route a player edit + enter the routed node (the SC3 entry point).

        1. ``node_id = self.edit_router.route(edit_intent, enzyme_id, self.rng)``
        2. ``self.state.add_edit({"enzyme": enzyme_id, "intent": edit_intent.to_dict(), "route": node_id})``
        3. ``return self._enter(node_id)``  (reuse existing _enter: on_enter
           MolActions flow to the existing ``molaction_sink``).

        The edit APPLICATION (backup + alter + sort + rebuild) is NOT done here
        -- it's the apply_edit helper's job (pymol_layer), triggered by the
        routed branch's ``on_enter`` MolAction("edit",...). This method is pure
        routing + entry; it stays WSL-unit-testable (no PyMOL).

        Raises ``RuntimeError`` if no ``edit_router`` was injected. Raises
        :class:`~c14.edit_router.EditRoutingError` if the bad-ending pool is
        empty.
        """
        if self.edit_router is None:
            raise RuntimeError("GameEngine has no edit_router; cannot apply edits")
        node_id = self.edit_router.route(edit_intent, enzyme_id, self.rng)
        self.state.add_edit({
            "enzyme": enzyme_id,
            "intent": edit_intent.to_dict(),
            "route": node_id,
        })
        return self._enter(node_id)

    def _enter(self, node_id, record_visit=True):
        # type: (str, bool) -> TurnResult
        """Enter ``node_id``: set current_node, run on_enter (emitting
        MolActions, recording the visit unless ``record_visit=False``,
        detecting an ending), sync the RNG state into GameState, dispatch the
        MolActions to the sink, and return a TurnResult.

        Syncing ``state.rng_state = rng.get_state()`` after entry means a save
        at any point captures the exact PRNG position (the next draw is
        reproducible after load -- success criterion #2/#3).
        """
        node = self.graph.get_node(node_id)
        self.state.current_node = node_id
        actions = self.interpreter.enter_node(
            node, self.state, self.rng, record_visit=record_visit)
        # Sync the live PRNG position into state so a save at any point
        # captures the exact next draw (success criterion #2/#3).
        self.state.rng_state = self.rng.get_state()
        # Dispatch each MolAction individually to the sink (a callable taking
        # a single MolAction). Per-action dispatch -- not a single list call --
        # so a plain list's ``.append`` collects one entry per action (the
        # test mock sink asserts ``len(sink) == 2`` and ``sink[0].op`` after
        # entering a node whose on_enter has 2 MolActions). The sink is the
        # testability boundary; the engine NEVER calls cmd.* here.
        if self.molaction_sink is not None:
            for action in actions:
                self.molaction_sink(action)
        if node.is_ending is not None:
            eligible_choices = []
        else:
            eligible_choices = node.choices
        return TurnResult(node, actions, eligible_choices)

    def save(self, path):
        # type: (str) -> None
        """Sync the live RngEngine state into GameState, then serialize via
        SaveStore to ``path`` (human-readable JSON)."""
        self.state.rng_state = self.rng.get_state()
        SaveStore.save(self.state, path)

    def load(self, path):
        # type: (str) -> TurnResult
        """Restore a saved game: load GameState, rebuild the RngEngine from
        ``(seed, rng_state)``, then re-enter the current node (replaying its
        on_enter MolActions to reconstruct the scene -- Pattern 6) with
        ``record_visit=False`` (loading does NOT double-count visits).
        Returns the TurnResult for the re-entered current node.
        """
        self.state = SaveStore.load(path)
        self.rng = RngEngine.from_state(self.state.seed, self.state.rng_state)
        return self._enter(self.state.current_node, record_visit=False)

    def __repr__(self):
        return "GameEngine(graph={!r}, current={!r}, finished={!r})".format(
            self.graph,
            self.state.current_node if self.state is not None else None,
            self.state.finished if self.state is not None else None)
