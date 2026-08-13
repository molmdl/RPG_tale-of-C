"""Graph validator + reachability checker + claim-id collector.

Pure-Python algorithms, stdlib only (``json``, ``os``, ``collections``). NO
pymol/PyQt5 imports -- this module is scanned by the Phase 1 AST gate as part
of ``c14/`` and stays in the domain tier (ARCHITECTURE.md Pattern 1).

The reachability checker establishes the "all endings reachable" invariant
(Pitfall 8): every authored ending must be reachable from the start node via
``choice.goto`` edges. ``check_reachability`` runs a pure BFS over the graph
and reports which endings are reachable -- green on a well-formed graph, red
on one with an orphaned ending. This is a pure graph algorithm with no file
I/O, so it is trivially unit-testable in WSL with inline node fixtures.

``collect_claim_ids`` is the Phase 2 home of the citation gate's story-walker
(forward-compatible with Phase 1's inline ``collect_referenced_claim_ids``).
It accepts EITHER a single ``.json`` file (backward-compatible with the Phase
1 fixtures) OR a directory (reads ``manifest.json`` + merges the listed
files' ``nodes`` dicts). It does its OWN minimal file loading and does NOT
import ``c14.story.graph`` -- this keeps Plan 03 (validate) independent of
Plan 02 (graph loader) so the two plans can run in parallel. The minor
manifest-reading overlap with ``graph.py`` is an acceptable trade for module
independence + parallel execution.

The reachability/validate functions accept a ``{id: node}`` dict as their
``nodes`` argument (the exact shape ``StoryGraph.all_nodes()`` returns, pinned
to the dict not a list, so Plan 05 can pass ``g.all_nodes()`` directly). They
work on both ``Node`` objects (from ``graph.py``) and raw JSON dicts (from
``collect_claim_ids`` fixtures) via small ``_choices``/``_goto``/``_is_ending``
helpers that duck-type the two shapes.

Design constraints honored:
- Python 3.6 stdlib ONLY. NO ``@dataclass`` (3.7+). Plain classes on
  instance attributes, matching the Phase 1 ``CitationRegistry`` precedent
  and the Plan 02-01 ``Node``/``Choice``/``MolAction`` precedent.
- ``.format()`` for string interpolation (f-strings are 3.6+ but ``.format()``
  is the established repo convention for consistency).
- No walrus operator (3.8+), no ``from __future__ import annotations`` (3.7+).
"""

import collections
import json
import os


# ---------------------------------------------------------------------------
# Plain result classes
# ---------------------------------------------------------------------------

class Issue(object):
    """A graph validation issue found by :func:`validate_graph`.

    Attributes:
        kind: issue category string. One of ``"dangling_divert"``,
            ``"unreachable_ending"``, or ``"unknown"``.
        node_id: the id of the node where the issue originates.
        detail: optional human-readable detail string (e.g.
            ``"choice -> nonexistent"``). Defaults to ``None``.
    """

    def __init__(self, kind, node_id, detail=None):
        # type: (str, str, str) -> None
        self.kind = kind
        self.node_id = node_id
        self.detail = detail

    def __repr__(self):
        if self.detail is not None:
            return "Issue(kind={!r}, node_id={!r}, detail={!r})".format(
                self.kind, self.node_id, self.detail)
        return "Issue(kind={!r}, node_id={!r})".format(self.kind, self.node_id)

    def __eq__(self, other):
        if not isinstance(other, Issue):
            return NotImplemented
        return (self.kind == other.kind
                and self.node_id == other.node_id
                and self.detail == other.detail)

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result


class ReachabilityReport(object):
    """Result of :func:`check_reachability`: which endings are reachable.

    Attributes:
        start_id: the node id the search started from.
        all_endings: list of every ending node id in the graph (in
            insertion order of the ``nodes`` dict).
        reachable_endings: subset of ``all_endings`` reachable from
            ``start_id`` via ``choice.goto`` edges.
        unreachable_endings: subset of ``all_endings`` NOT reachable --
            these are orphaned endings (Pitfall 8).
    """

    def __init__(self, start_id, all_endings, reachable_endings,
                 unreachable_endings):
        # type: (str, list, list, list) -> None
        self.start_id = start_id
        self.all_endings = list(all_endings)
        self.reachable_endings = list(reachable_endings)
        self.unreachable_endings = list(unreachable_endings)

    @property
    def is_ok(self):
        # type: () -> bool
        """True iff every ending is reachable (no orphaned endings)."""
        return len(self.unreachable_endings) == 0

    def __repr__(self):
        return ("ReachabilityReport(start={!r}, reachable={!r}, "
                "unreachable={!r}, ok={})").format(
                    self.start_id, self.reachable_endings,
                    self.unreachable_endings, self.is_ok)


# ---------------------------------------------------------------------------
# Duck-typing helpers (work on Node objects OR raw JSON dicts)
# ---------------------------------------------------------------------------

def _choices(node):
    # type: (object) -> list
    """Return the choices list of ``node``.

    Works on ``Node`` objects (``node.choices``) and raw dicts
    (``node.get('choices', [])``). The ``hasattr`` check distinguishes the
    two: Node objects have a ``choices`` attribute; dicts do not.
    """
    if hasattr(node, "choices"):
        return getattr(node, "choices")
    return node.get("choices", [])


def _goto(choice):
    # type: (object) -> object
    """Return the goto target of ``choice`` (or ``None``).

    Works on ``Choice`` objects (``choice.goto``) and raw dicts
    (``choice.get('goto')``). ``None`` means the choice has no divert
    (a leaf choice / terminal).
    """
    if hasattr(choice, "goto"):
        return getattr(choice, "goto")
    return choice.get("goto")


def _is_ending(node):
    # type: (object) -> bool
    """True iff ``node`` is an ending (``is_ending`` is not ``None``).

    Works on ``Node`` objects (``node.is_ending``) and raw dicts
    (``node.get('is_ending')``). An ending is a node whose ``is_ending``
    value is non-None (one of ``"true"|"good"|"normal"|"bad"`` per the model).
    """
    if hasattr(node, "is_ending"):
        return getattr(node, "is_ending") is not None
    return node.get("is_ending") is not None


# ---------------------------------------------------------------------------
# Reachability checker (Pitfall 8: all endings reachable)
# ---------------------------------------------------------------------------

def check_reachability(nodes, start_id):
    # type: (dict, str) -> ReachabilityReport
    """BFS from ``start_id`` over ``choice.goto`` edges; report ending reach.

    ``nodes`` is a ``{id: node}`` dict where each node is either a ``Node``
    object or a raw dict (duck-typed via the ``_choices``/``_goto``/
    ``_is_ending`` helpers). Returns a :class:`ReachabilityReport` listing
    every ending and splitting it into reachable vs. unreachable.

    The search only follows edges to nodes that EXIST in ``nodes``; a goto
    pointing to a nonexistent node is simply not traversed (flagging such
    dangling diverts is :func:`validate_graph`'s job, not the reachability
    checker's -- separation of concerns).

    Edge case: if ``start_id`` is not in ``nodes``, the report has
    ``is_ok == False`` and every ending is listed as unreachable (graceful
    -- lets the checker report the problem rather than crashing).
    """
    all_endings = [nid for nid, node in nodes.items() if _is_ending(node)]

    if start_id not in nodes:
        # Graceful: start missing -> nothing reachable, all endings orphaned.
        return ReachabilityReport(start_id, all_endings, [], all_endings)

    # BFS from start_id over choice.goto edges (only to existing nodes).
    reachable = set()
    queue = collections.deque([start_id])
    reachable.add(start_id)
    while queue:
        nid = queue.popleft()
        node = nodes[nid]
        for choice in _choices(node):
            goto = _goto(choice)
            if goto is not None and goto in nodes and goto not in reachable:
                reachable.add(goto)
                queue.append(goto)

    reachable_endings = [e for e in all_endings if e in reachable]
    unreachable_endings = [e for e in all_endings if e not in reachable]
    return ReachabilityReport(start_id, all_endings, reachable_endings,
                               unreachable_endings)


# ---------------------------------------------------------------------------
# Graph validator (dangling diverts, ...)
# ---------------------------------------------------------------------------

def validate_graph(nodes):
    # type: (dict) -> list
    """Structural validation of a ``{id: node}`` graph. Returns a list of
    :class:`Issue` (empty list = valid graph).

    Currently checks:
    - **dangling_divert**: a choice with a non-None ``goto`` that points to a
      node id not present in ``nodes``.

    Other checks can be added later; for Phase 2, dangling diverts is the
    key structural check (Pitfall 8 companion: a divert to nowhere is an
    orphaned-by-construction path).
    """
    issues = []
    for nid, node in nodes.items():
        for choice in _choices(node):
            goto = _goto(choice)
            if goto is not None and goto not in nodes:
                issues.append(
                    Issue("dangling_divert", nid,
                          detail="choice -> {}".format(goto)))
    return issues


# ---------------------------------------------------------------------------
# Claim-id collector (the gate's story-walker, Phase 2 home)
# ---------------------------------------------------------------------------

def _collect_from_nodes(nodes):
    # type: (dict) -> dict
    """Validate a ``nodes`` dict and return ``{node_id: [claim_id, ...]}``.

    Raises ``ValueError`` on bad schema (non-dict ``nodes`` or a non-dict
    node entry) -- the same contract as Phase 1's inline walker so the
    gate's exit-2 path still works. Nodes with no ``claim_ids`` key
    contribute an empty list (valid -- a purely narrative node).
    """
    if not isinstance(nodes, dict):
        raise ValueError(
            "story JSON must have a 'nodes' object; got {}".format(
                type(nodes).__name__))
    referenced = {}
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            raise ValueError(
                "node {!r} must be an object; got {}".format(
                    node_id, type(node).__name__))
        referenced[node_id] = list(node.get("claim_ids", []))
    return referenced


def collect_claim_ids(story_path):
    # type: (str) -> dict
    """Load a story (file OR directory) and return ``{node_id: [claim_id, ...]}``.

    Accepts EITHER:

    - A ``.json`` FILE: ``json.load`` it, read ``data["nodes"]``, validate it
      is a dict, and return ``{node_id: list(node["claim_ids"])}``. This is
      backward-compatible with Phase 1's inline ``collect_referenced_claim_ids``
      (same fixture shape, same return shape).
    - A DIRECTORY: read ``manifest.json`` inside it, take the ``files`` list,
      ``json.load`` each listed file, merge its ``nodes`` dict, and collect
      claim_ids from all merged nodes. (New multi-file capability for the
      real story graph bundle.)

    File vs. directory is detected via ``os.path.isdir``. If ``story_path``
    is neither an existing file nor a directory, raises ``ValueError`` (the
    gate maps this to exit 2). Raises ``ValueError`` on bad schema
    (non-dict ``nodes`` or non-dict node entry) and on malformed JSON
    (``json.JSONDecodeError`` is a ``ValueError`` subclass) -- same contract
    as Phase 1's walker so the gate's exit-2 path is unchanged.

    This function does its OWN minimal file loading and does NOT import
    ``c14.story.graph`` -- keeping Plan 03 (validate) independent of Plan 02
    (graph loader) so the two plans run in parallel.
    """
    if os.path.isdir(story_path):
        manifest_path = os.path.join(story_path, "manifest.json")
        if not os.path.isfile(manifest_path):
            raise ValueError(
                "story directory {!r} has no manifest.json".format(story_path))
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        files = manifest.get("files", [])
        if not isinstance(files, list):
            raise ValueError(
                "manifest 'files' must be a list; got {}".format(
                    type(files).__name__))
        merged_nodes = {}
        for fname in files:
            fpath = os.path.join(story_path, fname)
            with open(fpath, "r") as f:
                data = json.load(f)
            file_nodes = data.get("nodes", {})
            if not isinstance(file_nodes, dict):
                raise ValueError(
                    "story JSON must have a 'nodes' object; got {}".format(
                        type(file_nodes).__name__))
            merged_nodes.update(file_nodes)
        return _collect_from_nodes(merged_nodes)

    if not os.path.isfile(story_path):
        raise ValueError(
            "story path {!r} does not exist (not a file or directory)".format(
                story_path))

    with open(story_path, "r") as f:
        data = json.load(f)
    return _collect_from_nodes(data.get("nodes", {}))
