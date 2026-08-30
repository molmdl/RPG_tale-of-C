# c14/ui/controller.py -- Phase 6 Plan 06-06 the Qt-free Controller (mediator)
# + HeroResolver (OQ-6 multi-C warn+confirm gate).
#
# The Controller is the thin-adapter core (06-RESEARCH-ui-adapter.md Pattern 1):
# it wires QtWidgets events -> GameEngine -> MolOps dispatch. The QtWidgets
# widgets (main_window.py, 06-08) talk ONLY to the controller (never to the
# engine/molops/cmd directly). The controller constructs the engine with
# molaction_sink=<its own _dispatch_molaction method> + edit_router, then on
# each UI event calls one engine method and renders the returned TurnResult via
# the injected view.
#
# Qt-FREE: this module imports ONLY c14.* domain modules (engine, story.graph,
# story.model) + stdlib (sys). NO pymol, NO PyQt5. The c14/ui/ dir is
# AST-gate-EXEMPT (check_imports.py SKIP_DIRS includes "ui"), so Qt imports ARE
# allowed there -- but the controller OPTS OUT for testability (06-RESEARCH
# Pitfall 6). `python3.6 -c "import c14.ui.controller"` MUST succeed in pure
# WSL with no pymol/PyQt5 installed (the testability boundary, mirrors the
# Phase 3 AssetManager inject-cmd pattern).
#
# The OQ-6 multi-C hero-fallback gate (05.4-CONVENTION.md OQ-6 OVERRIDE) lives
# HERE in the controller layer (NOT in molops -- molops stays pure cmd.* only).
# The prompt is an injected callback (prompt_fn); the count is an injected
# callback (count_fn wrapping cmd.count_atoms). Both are dependency-injected so
# HeroResolver is unit-testable in WSL with mocks (06-RESEARCH Pattern 3).
#
# ALSO fixes SC#3 Blocker B (tca.shuffle routing): the node mixes 2 weighted
# RNG choices + 2 non-weighted (edit:offer, cycle-trap). The engine's choose()
# pre-empts the non-weighted (the RNG picks among the weighted). The controller
# routes the non-weighted via take_choice -> engine.goto (Task 1's new additive
# method), making the Bad ending (cycle-trap -> bad.cycle_trap_host_death) +
# edit:offer (-> edit.prompt) reachable.
#
# ALSO the edit-prompt seam (Warning 4 fix): request_edit(enzyme_id) stashes
# the enzyme_id from the edit-allowed SOURCE node + gotos edit.prompt. The
# MainWindow (06-08) reads _pending_edit_enzyme_id when render_turn sees
# turn.node.id == "edit.prompt" to open the EditDialog (06-09) with the right
# enzyme. build_edit_intent falls back to _pending_edit_enzyme_id at edit.prompt
# (which has no edit:enzyme: tag).
#
# ALSO Blocker 1 fix c: _dispatch_molaction wraps the molops.apply forward in a
# defensive try/except -- a failed load (network fetch of a real pdb:XXX
# target, a missing bundled fixture, any molops error) logs + continues to the
# next on_enter action rather than crashing the game (the start node is safe
# via 06-05's bundled _smoke.pdb; mid-game real pdb:XXX loads can fail offline
# -- degrade gracefully).
#
# PYTHON 3.6 ONLY: plain classes on instance attributes, .format() strings, NO
# @dataclass / f-strings / walrus (matches Phase 1/2 precedent; 3.6.9 has no
# dataclasses module).
"""Qt-free Controller (mediator) + HeroResolver (OQ-6 gate).

The Controller wires QtWidgets events -> GameEngine -> MolOps. Qt-free (imports
only c14.* domain modules + stdlib sys) so it is unit-testable in pure WSL
python3.6 with MockMolOps + MockView + mock prompt_fn/count_fn (the
testability boundary -- 06-RESEARCH-ui-adapter.md Pattern 1 + Pitfall 6).

HeroResolver implements the 05.4-CONVENTION.md OQ-6 default+warn+confirm rule:
single-C (count==1) is a deterministic no-op; multi-C (count!=1) prompts via
the injected prompt_fn + on confirm rewrites the hero ops' sele to the first
carbon. The confirm IS the no-fabricated-science guard.
"""

import sys

from c14.engine import GameEngine, TurnResult  # noqa: F401 (TurnResult re-exported for the view)
from c14.story.graph import StoryGraph
from c14.story.model import EditIntent, MolAction  # noqa: F401 (MolAction used by HeroResolver)


class HeroResolver(object):
    """Resolve the hero selector for a node's on_enter hero-highlight sequence
    (OQ-6 multi-C warn+confirm gate -- 05.4-CONVENTION.md OQ-6 OVERRIDE).

    Qt-free: the prompt is an injected callback (``prompt_fn``). Pure logic is
    unit-testable with a mock ``count_fn`` + mock ``prompt_fn``. Implements the
    05.4-CONVENTION.md default+warn+confirm rule:

    1. Detect a hero-highlight sequence via a ``label`` op with text "YOU" (the
       OQ-4 frozen hero marker). If none, return the actions unchanged (no
       hero-highlight, no-op).
    2. Count the atoms in the hero sele (``count_fn(hero_sele)``). If ``n == 1``
       (single-C, deterministic), return unchanged (no prompt).
   3. If ``n != 1`` (multi-C, ambiguous), pick a default (the first carbon:
      ``"first (<hero_obj> and elem C)"``) + warn + confirm via ``prompt_fn``.
      The confirm IS the no-fabricated-science guard (silently highlighting
      the wrong carbon would be a science error -- the hero-identity is
      load-bearing for the narrative).
    4. On confirm, return a NEW on_enter list with the hero ops' sele rewritten
       to the default. On reject, return unchanged.

    For Phase 6 placeholder content (known-by-construction selectors resolving
    to exactly 1 atom), this is a no-op pass-through -- the gate is WIRED +
    unit-tested with mocks but NOT triggered by shipped single-C content. The
    start node loads the bundled ``_smoke.pdb`` (2 carbons) -> the resolver
    prompts + highlights the first C (the 06-05 fix + the 05.4 convention).
    """

    def __init__(self, count_fn, prompt_fn):
        # type: (object, object) -> None
        # count_fn(sele) -> int  (wraps cmd.count_atoms; injectable for tests)
        # prompt_fn(message) -> bool  (QMessageBox.question in prod; mock in tests)
        self._count_fn = count_fn
        self._prompt_fn = prompt_fn

    def resolve(self, on_enter_actions):
        # type: (list) -> list
        """Return the (possibly rewritten) on_enter actions with the hero
        selector resolved.

        Returns the SAME list object for the no-op cases (single-C, rejected,
        no hero-highlight); returns a NEW list for the confirmed-rewrite case.
        The controller saves the original ``on_enter`` BEFORE calling resolve,
        so resolve may return a new list without mutating the input.
        """
        # 1. Find the hero marker: a `label` op with text "YOU".
        hero_label = None
        for action in on_enter_actions:
            if action.op == "label" and action.args.get("text") == "YOU":
                hero_label = action
                break
        if hero_label is None:
            return on_enter_actions  # no hero-highlight in this on_enter
        # 2. Count the atoms in the hero sele.
        hero_sele = hero_label.args.get("sele", hero_label.target)
        hero_obj = hero_label.target
        # The count is a best-effort pre-pass check: it runs BEFORE the
        # on_enter load dispatches (start_game / choose / take_choice all do
        # the hero pre-pass BEFORE engine.start/choose/goto enters the node +
        # runs on_enter). At pre-pass time the hero object may NOT exist yet
        # (the load is in on_enter). A bare cmd.count_atoms on a non-existent
        # object RAISES CmdException (03-01 decision: "Invalid selection
        # name"). Catch that + treat as ambiguous (n != 1) -> prompt the
        # player (OQ-6 multi-C path). The count becomes reliable only AFTER
        # the load dispatches; the prompt + confirm is the no-fabricated-
        # science guard regardless (the human/auto-confirm decides).
        try:
            n = self._count_fn(hero_sele)
        except Exception:
            n = 0  # count failed (object not yet loaded) -> ambiguous -> prompt
        if n == 1:
            return on_enter_actions  # single-C: deterministic, no prompt
        # 3. Multi-C (n != 1): default + warn + confirm (OQ-6 OVERRIDE).
        # The default sele MUST resolve to EXACTLY ONE carbon (06-14 SC2a
        # human-verify bug fix): the old "<hero_obj> and elem C" matched ALL
        # carbons (the bundled _smoke.pdb ethanol has 2 -> BOTH got spheres +
        # the "YOU" label). `first (...)` resolves to exactly 1 atom (the
        # first carbon by internal order -- C1 id=1 on the fixture),
        # EMPIRICALLY VERIFIED headlessly in PyMOL 2.5.0
        # (tools/probe_first_operator.py: count_atoms == 1, picks C1,
        # spheres+label post-conditions work on the sele; 03-01 precedent:
        # C-backed selectors cannot be confirmed from selector.py source
        # alone).
        default_sele = "first ({0} and elem C)".format(hero_obj)
        confirmed = self._prompt_fn(
            "This structure has {0} carbons. The hero (C14) is ambiguous. "
            "Highlight the first carbon as the hero?".format(n))
        if not confirmed:
            return on_enter_actions  # rejected: leave as-is
        # 4. Confirmed: rewrite the hero ops' sele to the default first-C.
        return self._rewrite_hero_sele(on_enter_actions, default_sele)

    def _rewrite_hero_sele(self, on_enter_actions, default_sele):
        # type: (list, str) -> list
        """Build a NEW on_enter list with the hero ops' sele rewritten to
        ``default_sele``.

        The hero ops whose sele is rewritten (the per-hero-atom highlight ops):
        - ``label`` with text "YOU" (the hero identity label)
        - ``show`` with rep "spheres" (the hero ball-and-stick sphere)
        - ``set`` with name "sphere_scale" (the small sphere scale)

        The ``show_as sticks`` + ``color`` ops KEEP their object-wide sele (they
        apply to the whole object by design -- sticks show ALL carbons, the
        color scopes to ``elem C`` already per the 05.4 convention). Other ops
        (``hide_all``, ``load``, ``set_color``) are copied unchanged.
        """
        out = []
        for action in on_enter_actions:
            if self._is_hero_sele_op(action):
                new_args = dict(action.args)
                new_args["sele"] = default_sele
                out.append(MolAction(action.op, action.target, new_args))
            else:
                out.append(action)  # unchanged: keep the same object
        return out

    @staticmethod
    def _is_hero_sele_op(action):
        # type: (MolAction) -> bool
        """Return True iff this MolAction is a hero-highlight op whose sele
        should be rewritten to the default first-C selector."""
        if action.op == "label" and action.args.get("text") == "YOU":
            return True
        if action.op == "show" and action.args.get("rep") == "spheres":
            return True
        if action.op == "set" and action.args.get("name") == "sphere_scale":
            return True
        return False

    def __repr__(self):
        return "HeroResolver()"


class Controller(object):
    """The mediator: wires QtWidgets events -> GameEngine -> MolOps dispatch.

    Qt-free: holds NO QtWidgets reference. The widgets call controller methods;
    the controller calls back into the widgets via an injected ``view``
    interface (a thin protocol the MainWindow implements -- ``render_turn``).
    This keeps the mediator logic unit-testable in WSL python3.6 with a
    MockView + MockMolOps + mock prompt/count (06-RESEARCH Pattern 1).

    The controller constructs the engine with
    ``molaction_sink=self._dispatch_molaction`` (the engine emits one MolAction
    per call -- the 02-04 per-action contract) + the injected ``edit_router`` +
    optional ``view_provider``/``view_applier`` (06-03 view-matrix injection).
    On each UI event the controller calls one engine method (``start`` /
    ``choose`` / ``take_choice`` / ``apply_edit`` / ``request_edit`` / ``save``
    / ``load``), records the achievement turn, and renders the TurnResult.
    """

    def __init__(self, story_dir, molops, cmd, edit_router, view=None,
                 prompt_fn=None, count_fn=None, achievement_board=None,
                 view_provider=None, view_applier=None):
        # type: (str, object, object, object, object, object, object, object, object, object) -> None
        """Construct the controller over the story graph at ``story_dir``.

        Args:
            story_dir: path to the story bundle dir (manifest.json + per-file
                node fragments). DI so plugin_entry passes the bundled path +
                tests pass the repo-root path.
            molops: the MolOps instance (real in prod; MockMolOps in tests).
                The controller forwards each MolAction the engine emits to
                ``molops.apply(action)`` (the 02-04 per-action contract).
            cmd: the pymol.cmd handle (used ONLY for the default count_fn; the
                controller NEVER calls cmd.* directly except via count_fn). May
                be None when count_fn is injected.
            edit_router: the EditRouter instance (real in prod; real or mock in
                tests). Passed to the engine for apply_player_edit routing.
            view: the MainWindow (implements ``render_turn(turn_result)``), or
                None for headless/tests. The controller calls view.render_turn
                after each engine turn.
            prompt_fn: the OQ-6 warn+confirm callback (``message -> bool``).
                None => OQ-6 gate disabled (no HeroResolver; Phase 6 placeholder
                content uses known-by-construction selectors, so the gate is a
                no-op). Injected so molops stays pure (06-RESEARCH Pattern 3).
            count_fn: wraps ``cmd.count_atoms`` (``sele -> int``). Defaults to
                ``lambda sele: cmd.count_atoms(sele)``. Injectable for tests.
            achievement_board: the AchievementBoard (06-04), or None. The
                controller calls ``board.on_turn(turn, character, is_new_game)``
                after each start/choose/take_choice/apply_edit/request_edit.
            view_provider: zero-arg callable returning the 18-float view list
                (06-03 view-matrix injection). Passed to the engine for save.
            view_applier: callable taking the 18-float view list. Passed to the
                engine for load.
        """
        self._graph = StoryGraph.load(story_dir)
        self._molops = molops
        self._cmd = cmd
        self._view = view
        self._prompt_fn = prompt_fn
        self._achievement_board = achievement_board
        self._count_fn = count_fn if count_fn is not None else (
            lambda sele: cmd.count_atoms(sele))
        # HeroResolver is constructed ONLY when prompt_fn is injected (the OQ-6
        # gate is opt-in). Without prompt_fn the controller skips hero
        # resolution entirely (Phase 6 placeholder content is safe).
        self._hero_resolver = (
            HeroResolver(self._count_fn, self._prompt_fn)
            if prompt_fn is not None else None)
        # The engine's molaction_sink = THIS controller's dispatch method. The
        # engine emits `for action in actions: sink(action)` (engine.py:203-205);
        # our dispatch forwards each to molops.apply (defensively -- Blocker 1
        # fix c). view_provider/view_applier close the 06-03 view-matrix gap.
        self._engine = GameEngine(
            self._graph,
            molaction_sink=self._dispatch_molaction,
            edit_router=edit_router,
            view_provider=view_provider,
            view_applier=view_applier)
        # The edit-prompt seam (Warning 4 fix): request_edit stashes the
        # enzyme_id from the edit-allowed SOURCE node BEFORE goto edit.prompt;
        # the MainWindow (06-08) reads this when render_turn sees
        # turn.node.id == "edit.prompt" to open the EditDialog (06-09) with the
        # right enzyme_id. build_edit_intent falls back to this at edit.prompt
        # (which has no edit:enzyme: tag).
        self._pending_edit_enzyme_id = None

    # ---- the molaction_sink the engine calls (engine.py:203-205) ----

    def _dispatch_molaction(self, action):
        # type: (MolAction) -> None
        """Forward one MolAction to ``molops.apply`` (the 02-04 per-action
        contract). The engine calls this once per on_enter action.

        Blocker 1 fix c: wrap the forward in a defensive try/except. A failed
        load (network fetch of a real ``pdb:XXX`` target downstream, a missing
        bundled fixture, or any molops error) MUST log + continue to the next
        on_enter action rather than crash the game. Per-action swallow: one
        failed load doesn't skip the rest of on_enter. Broad bare
        ``except Exception`` (the start node is safe via 06-05's bundled
        placeholder; mid-game real pdb:XXX loads can fail offline -- degrade
        gracefully). MockMolOps in tests doesn't raise, so this is a no-op
        there -- tests assert the dispatch still forwards.
        """
        try:
            self._molops.apply(action)
        except Exception as e:  # noqa: BLE001 -- Blocker 1 fix c: degrade gracefully
            sys.stderr.write(
                "controller: molops.apply failed for op={op!r} target={t!r}: "
                "{err}\n".format(op=action.op, t=action.target, err=e))

    # ---- UI event handlers (called by the QtWidgets widgets) ----

    def start_game(self, character="glucose", seed=None):
        # type: (str, object) -> TurnResult
        """Begin a new game: resolve the hero for the start node (OQ-6 pre-pass,
        monkey-patch + restore), enter it via ``engine.start``, record the
        achievement turn (``is_new_game=True``), and render.
        """
        start_id = self._engine.graph.start_node()
        patch = self._resolve_hero_for_target(start_id)
        try:
            turn = self._engine.start(character, seed)
        finally:
            self._restore_hero_patch(patch)
        self._record_achievement(turn, character, is_new_game=True)
        self._render(turn)
        return turn

    def choose(self, index):
        # type: (int) -> TurnResult
        """Make a choice on the current node + advance.

        Resolves the hero for the target node FIRST (OQ-6 pre-pass; for a
        weighted node the target is unknown ahead of time so the pre-pass is
        skipped -- no weighted-choice target in the current skeleton has a hero
        highlight), then calls ``engine.choose(index)``. Records + renders.
        """
        target_id = self._target_node_id_for_choose(index)
        patch = self._resolve_hero_for_target(target_id)
        try:
            turn = self._engine.choose(index)
        finally:
            self._restore_hero_patch(patch)
        self._record_achievement(turn, self._engine.state.character)
        self._render(turn)
        return turn

    def take_choice(self, choice):
        # type: (object) -> TurnResult
        """Route a NON-WEIGHTED choice at a mixed weighted+non-weighted node
        (tca.shuffle's edit:offer + cycle-trap) via ``engine.goto`` (NOT
        ``engine.choose``, which would RNG-pick among the weighted choices and
        pre-empt the non-weighted). SC#3 Blocker B fix.

        Used for edit:offer -> edit.prompt + cycle-trap ->
        bad.cycle_trap_host_death. The UI (06-08 ChoicePanel) calls this for
        non-weighted choices at a mixed node (detected via
        :meth:`is_mixed_weighted_node`); ``choose`` stays for pure-MC nodes.
        Resolves the hero for ``choice.goto``, then ``engine.goto(choice.goto)``,
        records + renders.
        """
        patch = self._resolve_hero_for_target(choice.goto)
        try:
            turn = self._engine.goto(choice.goto)
        finally:
            self._restore_hero_patch(patch)
        self._record_achievement(turn, self._engine.state.character)
        self._render(turn)
        return turn

    def apply_edit(self, edit_intent):
        # type: (EditIntent) -> TurnResult
        """Apply a player edit: read the enzyme_id from the current node's
        ``edit:enzyme:<id>`` tag + call ``engine.apply_player_edit`` (which
        routes via EditRouter -> branch or bad-ending pool). Records + renders.

        The enzyme_id comes from the current node's ``edit:enzyme:<id>`` tag (the
        edit-allowed source). At ``edit.prompt`` (which has NO ``edit:enzyme:``
        tag) it falls back to ``edit_intent.enzyme_id`` -- the value
        :meth:`build_edit_intent` stashed from ``_pending_edit_enzyme_id`` (set
        by :meth:`request_edit` at the source edit-allowed node). Raises
        ``RuntimeError`` only if both are absent.
        """
        enzyme_id = self._current_enzyme_id()
        if enzyme_id is None:
            # edit.prompt has no edit:enzyme:<id> tag -- use the enzyme_id the
            # EditIntent carries (build_edit_intent stashed it from the pending
            # stash set by request_edit at the source edit-allowed node).
            enzyme_id = getattr(edit_intent, "enzyme_id", None)
        if enzyme_id is None:
            raise RuntimeError(
                "cannot apply_edit: current node {!r} has no edit:enzyme:<id> "
                "tag and the EditIntent carries no enzyme_id".format(
                    self._engine.state.current_node))
        turn = self._engine.apply_player_edit(edit_intent, enzyme_id)
        self._record_achievement(turn, self._engine.state.character)
        self._render(turn)
        return turn

    def request_edit(self, enzyme_id):
        # type: (str) -> TurnResult
        """The edit-prompt seam (Warning 4 fix): stash the enzyme_id from the
        edit-allowed SOURCE node + goto ``edit.prompt`` directly via
        ``engine.goto`` (NOT ``choose`` -- the source node may be a mixed
        weighted node like tca.shuffle where choose would RNG-pick).

        Called by the ChoicePanel's edit:offer button (06-08) INSTEAD of
        ``take_choice`` for the edit:offer choice -- it bundles the enzyme_id
        stash + the goto in one call so the MainWindow doesn't have to reach
        back into the source node's tags after the advance. The MainWindow's
        render_turn detects ``turn.node.id == "edit.prompt"`` + opens the
        EditDialog (06-09) with ``self._pending_edit_enzyme_id``. Records +
        renders.
        """
        self._pending_edit_enzyme_id = enzyme_id
        patch = self._resolve_hero_for_target("edit.prompt")
        try:
            turn = self._engine.goto("edit.prompt")
        finally:
            self._restore_hero_patch(patch)
        self._record_achievement(turn, self._engine.state.character)
        self._render(turn)
        return turn

    def build_edit_intent(self, op, target, args):
        # type: (str, str, dict) -> EditIntent
        """Build an EditIntent whose ``signature()`` must match edits.json.

        The edit dialog (06-09) collects op/target/args from curated options;
        the controller assembles the EditIntent + reads the enzyme_id. The
        enzyme_id comes from the current node's ``edit:enzyme:<id>`` tag; at
        ``edit.prompt`` (which has NO ``edit:enzyme:`` tag) it falls back to the
        stashed ``_pending_edit_enzyme_id`` (set by :meth:`request_edit` at the
        source edit-allowed node). Raises ``RuntimeError`` if both are None.
        """
        enzyme_id = self._current_enzyme_id()
        if enzyme_id is None:
            enzyme_id = self._pending_edit_enzyme_id
        if enzyme_id is None:
            raise RuntimeError(
                "cannot build EditIntent: current node {!r} has no "
                "edit:enzyme:<id> tag and no pending enzyme_id stash".format(
                    self._engine.state.current_node))
        return EditIntent(op, target, args, enzyme_id)

    def save(self, path):
        # type: (str) -> None
        """Save the game: delegates to ``engine.save`` (Pattern 6: the scene
        rebuilds on load via on_enter replay -- no .pse saved)."""
        self._engine.save(path)

    def load(self, path):
        # type: (str) -> TurnResult
        """Load a saved game: delegates to ``engine.load`` (replays the current
        node's on_enter -> molops -> cmd.* to reconstruct the scene) + renders
        the restored turn."""
        turn = self._engine.load(path)
        self._render(turn)
        return turn

    # ---- helpers ----

    def is_mixed_weighted_node(self, node):
        # type: (object) -> bool
        """Return True iff ``node`` has >=1 weighted eligible choice AND >=1
        non-weighted eligible choice (the tca.shuffle case).

        The view (06-08) uses this to decide the UI rendering: a mixed node
        shows a "Spin" button (the RNG picks among the weighted) + separate
        Edit/conditional buttons (the non-weighted, routed via
        :meth:`take_choice` / :meth:`request_edit`); a pure-MC node shows one
        button per choice (routed via :meth:`choose`). Delegates cond check to
        ``engine.choice_cond_met`` (Task 1's additive method).
        """
        eligible = [c for c in node.choices
                    if self._engine.choice_cond_met(c)]
        weighted = [c for c in eligible if c.weight is not None]
        non_weighted = [c for c in eligible if c.weight is None]
        return len(weighted) >= 1 and len(non_weighted) >= 1

    def _current_enzyme_id(self):
        # type: () -> str
        """Read the ``edit:enzyme:<id>`` tag from the current node (05.1-DESIGN
        edit-node contract). Returns None if the current node is not
        edit-allowed (no such tag)."""
        node = self._engine.graph.get_node(self._engine.state.current_node)
        return next((t.split(":", 2)[2] for t in node.tags
                     if t.startswith("edit:enzyme:")), None)

    def _target_node_id_for_choose(self, index):
        # type: (int) -> str
        """Peek at the choice target for the OQ-6 hero pre-pass.

        For a non-weighted choice, returns ``eligible[index].goto`` (the
        controller can read the target ahead of time). For a weighted node,
        returns None (the RNG picks; the target is unknown ahead of time -- and
        in the current skeleton no weighted-choice target has a hero highlight,
        so skipping the pre-pass is safe). Mirrors the interpreter's
        ``pick_choice`` eligibility filter (cond-gated) + the weighted check.
        """
        node = self._engine.graph.get_node(self._engine.state.current_node)
        eligible = [c for c in node.choices
                    if self._engine.choice_cond_met(c)]
        weighted = [c for c in eligible if c.weight is not None]
        if weighted:
            return None
        if 0 <= index < len(eligible):
            return eligible[index].goto
        return None

    def _resolve_hero_for_target(self, target_node_id):
        # type: (str) -> object
        """OQ-6 hero pre-pass: monkey-patch the target node's ``on_enter`` with
        the HeroResolver's resolution (06-RESEARCH Pattern 3, Open Question 2
        recommended: one-shot mutate + restore is safe -- the engine re-reads
        ``node.on_enter`` each ``_enter``).

        Returns a ``(target, original_on_enter)`` restore-token to pass to
        :meth:`_restore_hero_patch`, or None if no patching happened (no
        resolver, no target, or resolve returned the same list unchanged -- the
        single-C / no-hero-highlight / rejected cases). The caller wraps the
        engine call in try/finally + calls ``_restore_hero_patch`` to restore
        the original on_enter.
        """
        if self._hero_resolver is None or target_node_id is None:
            return None
        target = self._engine.graph.get_node(target_node_id)
        original = target.on_enter
        resolved = self._hero_resolver.resolve(original)
        if resolved is original:
            return None  # no-op (single-C, no hero highlight, or rejected)
        target.on_enter = resolved
        return (target, original)

    @staticmethod
    def _restore_hero_patch(patch):
        # type: (object) -> None
        """Restore the original ``on_enter`` after a monkey-patch (the
        try/finally in start_game/choose/take_choice/request_edit). No-op if
        patch is None (no patching happened)."""
        if patch is not None:
            patch[0].on_enter = patch[1]

    def _record_achievement(self, turn, character, is_new_game=False):
        # type: (TurnResult, str, bool) -> None
        """Record one engine turn's unlocks via the AchievementBoard (06-04).
        ``is_new_game=True`` only on ``start_game`` (triggers first_game +
        <character>_tried). No-op if no board was injected."""
        if self._achievement_board is not None:
            self._achievement_board.on_turn(turn, character, is_new_game)

    def _render(self, turn):
        # type: (TurnResult) -> None
        """Render the TurnResult into the view (the widgets). No-op if no view
        was injected (headless/tests)."""
        if self._view is not None:
            self._view.render_turn(turn)

    def __repr__(self):
        return "Controller(current={!r}, finished={!r})".format(
            self._engine.state.current_node if self._engine.state is not None else None,
            self._engine.state.finished if self._engine.state is not None else None)
