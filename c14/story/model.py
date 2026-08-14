"""Story data model: Node, Choice, MolAction. Pure-Python, stdlib only.

``MolAction`` is the domain->pymol_layer carrier (never a ``cmd.*`` call) --
the testability-boundary data type from ARCHITECTURE.md Pattern 1. The engine
emits ``MolAction`` instances; ``c14/pymol_layer/molops.py`` (Phase 4) translates
them to ``cmd.show/hide/select/zoom/color/delete/...``. Because this module is
pure data with no pymol import, it stays unit-testable in WSL.

Design constraints honored:
- Python 3.6 stdlib ONLY (``typing`` for annotations in docstrings; no runtime
  imports needed). NO ``@dataclass`` (3.7+ -- research Pitfall 1: verified
  ``ModuleNotFoundError: No module named 'dataclasses'`` on python3.6.9). Plain
  classes on instance attributes, matching the Phase 1 ``CitationRegistry``
  precedent.
- NO pymol/PyQt5 imports (the Phase 1 AST gate scans this file).
- ``from_dict``/``to_dict`` round-trip the validated ARCHITECTURE.md JSON node
  shape (Pattern 2 example) so the loader (Plan 02) can parse story JSON and
  the validator (Plan 04) can re-serialize it.

The ARCHITECTURE.md reference shows these as ``@dataclass``; the plan overrides
that to plain classes for 3.6 compatibility. Field names + semantics are kept
near-verbatim so the architecture doc stays the authoritative reference.
"""


class MolAction(object):
    """A molecular-layer intent emitted by the story interpreter.

    Pure data: ``op`` + ``target`` + ``args``. The PyMOL layer
    (``c14/pymol_layer/molops.py``) translates this to ``cmd.*`` calls. Because
    it carries only data, the domain tier never imports pymol and stays
    unit-testable in WSL (ARCHITECTURE.md Pattern 1, Anti-Pattern 1).

    Attributes:
        op: operation name. One of "load" | "hide_all" | "show" |
            "select_focus" | "zoom" | "color" | "delete" | "protonate" |
            "edit" | "restore" (the molops dispatch keys).
        target: asset key (e.g. "pdb:1TNR") or object name, or None for
            target-less ops like "hide_all".
        args: op-specific parameters (e.g. {"rep": "cartoon", "sele": "all"}).
            Defaults to an empty dict when omitted.
    """

    def __init__(self, op, target=None, args=None):
        # type: (str, str, dict) -> None
        self.op = op
        self.target = target
        self.args = args if args is not None else {}

    @classmethod
    def from_dict(cls, d):
        # type: (dict) -> MolAction
        """Build a MolAction from a raw dict (the JSON ``on_enter`` item)."""
        return cls(d["op"], d.get("target"), d.get("args"))

    def to_dict(self):
        # type: () -> dict
        """Serialize to a JSON-ready dict (inverse of :meth:`from_dict`)."""
        return {"op": self.op, "target": self.target, "args": self.args}

    def __eq__(self, other):
        if not isinstance(other, MolAction):
            return NotImplemented
        return (self.op == other.op
                and self.target == other.target
                and self.args == other.args)

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self):
        return hash((self.op, self.target))

    def __repr__(self):
        return "MolAction(op={!r}, target={!r}, args={!r})".format(
            self.op, self.target, self.args)


class EditIntent(object):
    """A player's edit intent -- the routing INPUT (player -> EditRouter).

    Pure data, like MolAction, but a SEPARATE type: MolAction is the execution
    carrier (engine -> molops); EditIntent is the routing carrier (player ->
    router) and carries the enzyme_id lookup key MolAction lacks.

    Attributes:
        op: edit category. One of "point_mutation" | "substrate_edit" |
            "protonation_change" (the EDIT-01/02/03 categories -- FINER than
            MolAction's single "edit" op, because the lookup table matches on
            these categories).
        target: residue/atom selector or object name (e.g. "resi 57 and chain A"
            for a point mutation; "substrate" for a substrate edit). Matched
            verbatim against the table signature after normalization.
        args: op-specific parameters (e.g. {"new_res": "ALA"} for a point
            mutation; {"group": "-OH", "action": "add"} for a substrate edit;
            {"resn": "HIP"} for a protonation change). Defaults to {}.
        enzyme_id: the enzyme/substrate context id for lookup (e.g.
            "hexokinase" or "pdb:1TNR"). The current story node determines this
            (Phase 5.1 edit-node contract); the controller passes it.
    """

    def __init__(self, op, target=None, args=None, enzyme_id=None):
        # type: (str, str, dict, str) -> None
        self.op = op
        self.target = target
        self.args = args if args is not None else {}
        self.enzyme_id = enzyme_id

    def signature(self):
        # type: () -> dict
        """Return the canonical match dict: {"op","target","args"}.

        Deterministic: target is whitespace-stripped + lowercased; args values
        are stringified via _norm_val; keys are the raw op/target/args (no
        enzyme_id -- the enzyme_id is the lookup BUCKET, not part of the
        per-edit signature). Compared with == against edits.json "signature"
        entries (dict equality is order-independent on 3.6.9 -- verified).
        """
        return {
            "op": self.op,
            "target": (self.target or "").strip().lower(),
            "args": {k: _norm_val(v) for k, v in (self.args or {}).items()},
        }

    @classmethod
    def from_dict(cls, d):
        # type: (dict) -> EditIntent
        return cls(d["op"], d.get("target"), d.get("args"), d.get("enzyme_id"))

    def to_dict(self):
        # type: () -> dict
        return {"op": self.op, "target": self.target,
                "args": self.args, "enzyme_id": self.enzyme_id}

    def __eq__(self, other):
        if not isinstance(other, EditIntent):
            return NotImplemented
        return (self.op == other.op and self.target == other.target
                and self.args == other.args
                and self.enzyme_id == other.enzyme_id)

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else not r

    def __repr__(self):
        return "EditIntent(op={!r}, target={!r}, enzyme_id={!r})".format(
            self.op, self.target, self.enzyme_id)


def _norm_val(v):
    # type: (object) -> str
    """Normalize a signature value to a deterministic string.

    Scalars -> str(v).strip(); nested dicts/lists -> json.dumps(sort_keys=True)
    so dict-key order never breaks equality (Pitfall 6).
    """
    if isinstance(v, dict) or isinstance(v, list):
        import json
        return json.dumps(v, sort_keys=True)
    return str(v).strip()


class Choice(object):
    """A player-selectable choice on a Node.

    Attributes:
        label: human-readable choice text shown in the UI.
        goto: divert target node id (e.g. "knot.stitch"), or None.
        cond: condition expression string evaluated against GameState
            (e.g. "not seen_tca and char=='glucose'"), or None.
        weight: if set (float), this is an RNG-weighted branch (TCA shuffle);
            the interpreter picks among weighted choices via RngEngine.
        effects: dict with optional "set"/"incr" sub-dicts applied to
            GameState when this choice is taken. Defaults to {}.
        tags: list of game-side hook tags (e.g. "rng:weighted", "edit:offer").
            Defaults to [].
    """

    def __init__(self, label, goto=None, cond=None, weight=None,
                 effects=None, tags=None):
        # type: (str, str, str, float, dict, list) -> None
        self.label = label
        self.goto = goto
        self.cond = cond
        self.weight = weight
        self.effects = effects if effects is not None else {}
        self.tags = tags if tags is not None else []

    @classmethod
    def from_dict(cls, d):
        # type: (dict) -> Choice
        """Build a Choice from a raw dict (the JSON ``choices`` item)."""
        return cls(
            label=d["label"],
            goto=d.get("goto"),
            cond=d.get("cond"),
            weight=d.get("weight"),
            effects=d.get("effects"),
            tags=d.get("tags"),
        )

    def to_dict(self):
        # type: () -> dict
        """Serialize to a JSON-ready dict (inverse of :meth:`from_dict`)."""
        return {
            "label": self.label,
            "goto": self.goto,
            "cond": self.cond,
            "weight": self.weight,
            "effects": self.effects,
            "tags": self.tags,
        }

    def __eq__(self, other):
        if not isinstance(other, Choice):
            return NotImplemented
        return (self.label == other.label
                and self.goto == other.goto
                and self.cond == other.cond
                and self.weight == other.weight
                and self.effects == other.effects
                and self.tags == other.tags)

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __repr__(self):
        return "Choice(label={!r}, goto={!r}, weight={!r})".format(
            self.label, self.goto, self.weight)


class Node(object):
    """A story graph node (a scene/step in a pathway).

    Attributes:
        id: dotted address (e.g. "intro.start", "tca.shuffle").
        text_dramatic: in-character dramatic prose shown to the player.
        text_teaching: scientific teaching text (the "what's really happening").
        claim_ids: list of citation claim_ids backing this node's science
            (checked by the citation gate). Defaults to [].
        choices: list of Choice objects offered to the player. Defaults to [].
        on_enter: list of MolAction hooks fired on node entry (queued for the
            PyMOL layer). Defaults to [].
        is_ending: None for a non-ending node, or one of
            "true"|"good"|"normal"|"bad" for an ending node.
        tags: list of game-side hook tags (e.g. "stage:tca", "rng:shuffle").
            Defaults to [].
        on_enter_divert: auto-advance target node id, or None. When set, the
            interpreter runs on_enter then immediately diverts (no choice).
    """

    def __init__(self, id, text_dramatic="", text_teaching="", claim_ids=None,
                 choices=None, on_enter=None, is_ending=None, tags=None,
                 on_enter_divert=None):
        # type: (str, str, str, list, list, list, str, list, str) -> None
        self.id = id
        self.text_dramatic = text_dramatic
        self.text_teaching = text_teaching
        self.claim_ids = claim_ids if claim_ids is not None else []
        self.choices = choices if choices is not None else []
        self.on_enter = on_enter if on_enter is not None else []
        self.is_ending = is_ending
        self.tags = tags if tags is not None else []
        self.on_enter_divert = on_enter_divert

    @classmethod
    def from_dict(cls, d):
        # type: (dict) -> Node
        """Build a Node from a raw dict (the JSON node object).

        Parses nested ``choices`` as Choice instances and ``on_enter`` as
        MolAction instances (ARCHITECTURE.md Pattern 2 JSON shape).
        """
        choices = [Choice.from_dict(c) for c in d.get("choices", [])]
        on_enter = [MolAction.from_dict(m) for m in d.get("on_enter", [])]
        return cls(
            id=d["id"],
            text_dramatic=d.get("text_dramatic", ""),
            text_teaching=d.get("text_teaching", ""),
            claim_ids=d.get("claim_ids"),
            choices=choices,
            on_enter=on_enter,
            is_ending=d.get("is_ending"),
            tags=d.get("tags"),
            on_enter_divert=d.get("on_enter_divert"),
        )

    def to_dict(self):
        # type: () -> dict
        """Serialize to a JSON-ready dict (inverse of :meth:`from_dict`)."""
        return {
            "id": self.id,
            "text_dramatic": self.text_dramatic,
            "text_teaching": self.text_teaching,
            "claim_ids": list(self.claim_ids),
            "choices": [c.to_dict() for c in self.choices],
            "on_enter": [m.to_dict() for m in self.on_enter],
            "is_ending": self.is_ending,
            "tags": list(self.tags),
            "on_enter_divert": self.on_enter_divert,
        }

    @property
    def is_ending_node(self):
        # type: () -> bool
        """True iff this node is an ending (``is_ending`` is not None)."""
        return self.is_ending is not None

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __repr__(self):
        return "Node(id={!r}, is_ending={!r}, choices={})".format(
            self.id, self.is_ending, len(self.choices))
