"""Walks the story graph: evaluates choice conditions, picks weighted (RNG)
branches, runs on_enter MolActions (pure data), records visit counts, detects
endings. Pure-Python, no pymol -- emits MolAction lists, never cmd.* calls.

This is the ARCHITECTURE.md Pattern 2 ``StoryInterpreter`` (the ink-inspired
story walker), adopted near-verbatim. The interpreter is the pure-Python
domain-tier walker: it evaluates ``choice.cond`` conditions against
``GameState``, picks among weighted (RNG) branches deterministically via the
single ``RngEngine``, runs a node's ``on_enter`` MolAction hooks (returning
them as a *list of pure data* -- the caller/controller dispatches to the
pymol_layer; in tests a mock sink just collects them), records visit counts,
and detects ending nodes.

The testability boundary is strict: ``enter_node`` returns ``node.on_enter``
(the ``MolAction`` list) and NEVER calls ``cmd.*``. The future controller
(Phase 2 engine / Phase 6 Qt UI) is the only thing that translates MolActions
to ``cmd.*`` via ``c14/pymol_layer/molops.py``. Because this module never names
a pymol type, it stays unit-testable in WSL with zero pymol import.

Design constraints honored:
- Python 3.6 stdlib ONLY. NO pymol/PyQt5 imports (the Phase 1 AST gate scans
  this file). NO ``random`` import -- the ``RngEngine`` is dependency-injected
  (Anti-Pattern 7: all stochastic draws go through the single seeded engine,
  never an ad-hoc ``random.random()``).
- Plain class, matching the Phase 1 ``CitationRegistry`` precedent and the
  Plan 01 ``Node`` / ``RngEngine`` / ``GameState`` classes (NO ``@dataclass``).
- ``.format()`` for string interpolation (the established repo convention).
"""

from c14.story.model import Node, Choice, MolAction


class StoryInterpreter(object):
    """Walks a StoryGraph: choice conditions, RNG-weighted picks, on_enter
    MolAction emission, visit recording, ending detection.

    The interpreter is stateless across calls -- it holds no per-playthrough
    data; ``GameState`` and ``RngEngine`` are passed in (dependency injection)
    so a single interpreter instance can serve any number of playthroughs and
    the state/engine remain the saveable/replayable units.
    """

    def pick_choice(self, node, state, rng):
        # type: (Node, object, object) -> object
        """Resolve the choices on ``node`` for ``state``.

        Filters by condition, then:
        - If any eligible choice is weighted (``c.weight is not None``) AND the
          total weight is > 0: pick exactly one deterministically via the single
          ``RngEngine`` (``rng.random() * total`` + cumulative sum) and return
          that ``Choice``. This is the RNG-decides branch (the TCA shuffle / the
          "Proceed (luck decides)" weighted choices).
        - Otherwise (no weighted choices, or total weight == 0): return the
          full eligible ``list[Choice]`` for the caller/player to select from
          by index (the UI presents them; the player picks).

        A node can be all-weighted (RNG decides, like ``intro.start``) or a mix;
        when all eligible choices are weighted, a single ``Choice`` is returned.
        """
        eligible = [c for c in node.choices if self._cond(c.cond, state)]
        weighted = [c for c in eligible if c.weight is not None]
        if weighted:
            total = sum(c.weight for c in weighted)
            if total > 0:
                r = rng.random() * total
                upto = 0.0
                for c in weighted:
                    upto += c.weight
                    if r <= upto:
                        return c
        # non-weighted (or zero total weight): present all eligible to the
        # caller/player (the UI picks by index).
        return eligible

    def enter_node(self, node, state, rng, record_visit=True):
        # type: (Node, object, object, bool) -> list
        """Enter ``node``: record the visit, emit on_enter MolActions, detect
        an ending.

        Returns the node's ``on_enter`` MolAction list (pure data -- the caller
        dispatches to the pymol_layer; NEVER ``cmd.*`` here). Records the visit
        count (for conditions + cycle-trap detection) and, if the node is an
        ending (``is_ending is not None``), marks the playthrough finished with
        the ending tier. ``rng`` is accepted for signature symmetry with future
        on_enter hooks that may draw (e.g. text-variant shuffles); this minimal
        version does not draw on entry.

        ``record_visit`` (default True) controls whether the visit count is
        bumped. The engine sets it to False on load-replay so re-entering the
        current node to reconstruct the scene does NOT double-count visits
        (ARCHITECTURE.md Pattern 6: the scene is a pure function of game state).
        Ending detection runs regardless of ``record_visit``.
        """
        if record_visit:
            state.record_visit(node.id)
        actions = list(node.on_enter)
        if node.is_ending is not None:
            state.mark_finished(node.is_ending)
        return actions

    def _cond(self, cond, state):
        # type: (str, object) -> bool
        """Safe condition evaluator.

        If ``cond`` is ``None``: return ``True`` (always eligible). Otherwise
        evaluate ``cond`` against a restricted namespace exposing the state's
        ``flags`` (dict), ``char`` (the character string, matching the
        architecture's ``char=='glucose'`` example), ``counters`` (dict), and
        ``visits`` (dict) -- with NO builtins (``{"__builtins__": {}}``).

        Security model: story content is TRUSTED -- it is bundled JSON authored
        by the team, not user input -- and the namespace has no builtins, so
        ``eval`` is bounded to reading those four state fields. (Like any
        Python ``eval`` sandbox this is not a defense against a hostile author
        with attribute-walking tricks; the trust boundary is content
        authorship, not runtime isolation.) On ANY exception (NameError,
        SyntaxError, TypeError, ...) the choice is silently disabled (return
        ``False``) -- fail-safe: a malformed condition never crashes the game,
        it just hides its choice.
        """
        if cond is None:
            return True
        try:
            return bool(eval(
                cond,
                {"__builtins__": {}},
                {
                    "flags": state.flags,
                    "char": state.character,
                    "counters": state.counters,
                    "visits": state.visit_counts,
                },
            ))
        except Exception:
            return False

    def apply_effects(self, choice, state):
        # type: (Choice, object) -> None
        """Apply a choice's ``effects`` dict to ``state``.

        ``effects`` may contain:
        - ``"set"``: a dict of flag -> value; each applied via
          ``state.set_flag(name, value)``.
        - ``"incr"``: a dict of counter -> delta; each applied via
          ``state.incr(name, delta)``.
        Missing keys are tolerated (a choice with no effects is a no-op).
        """
        effects = choice.effects or {}
        if "set" in effects:
            for name, value in effects["set"].items():
                state.set_flag(name, value)
        if "incr" in effects:
            for name, delta in effects["incr"].items():
                state.incr(name, delta)

    def __repr__(self):
        return "StoryInterpreter()"
