"""Story-bundle loader: reads manifest.json + merges per-file node fragments
into one dict of Node. Pure-Python, stdlib only.

``StoryGraph.load(story_dir)`` reads ``manifest.json`` (version, default_seed,
start, files list) and merges every listed file's ``nodes`` dict into one
``{node_id: Node}`` mapping built via ``Node.from_dict``. The loader is
CWD-independent: it takes an explicit ``story_dir`` so the engine and tests can
point it at any directory (repo-root ``data/story/`` at dev time, a bundled
``c14/data/story/`` copy at runtime).

Node ids are the JSON object keys under ``"nodes"`` (the
``{"nodes": {id: {"claim_ids": [...]}}}`` shape is preserved for forward
compatibility with the Phase 1 citation gate's story-walker and the Plan 03/05
validators). The loader injects each key as the node's ``id`` field before
``Node.from_dict`` so the data model's required ``id`` is satisfied without
duplicating it inside each node body.

Design constraints honored:
- Python 3.6 stdlib ONLY (``json``, ``os``). NO pymol/PyQt5 imports (the Phase 1
  AST gate scans this file).
- Plain class on instance attributes, matching the Phase 1 ``CitationRegistry``
  precedent and the Plan 01 ``Node`` / ``GameState`` classes (NO ``@dataclass``).
- ``all_nodes()`` returns the ``{id: Node}`` dict (NOT a list of values) -- that
  dict shape is the contract consumed by Plan 03's ``check_reachability`` /
  ``validate_graph`` and Plan 05's tests.
"""

import json
import os

from c14.story.model import Node


class StoryGraph(object):
    """A loaded story bundle: a dict of Node + bundle metadata.

    Attributes:
        nodes: ``{node_id: Node}`` mapping (the merged graph).
        default_seed: bundle-level default RNG seed (from manifest).
        version: story-bundle format version (from manifest).
    """

    def __init__(self, nodes, default_seed=0, version=1, start=None):
        # type: (dict, int, int, str) -> None
        self.nodes = nodes
        self.default_seed = default_seed
        self.version = version
        self._start = start

    @classmethod
    def load(cls, story_dir):
        # type: (str) -> StoryGraph
        """Load a story bundle from ``story_dir``.

        Reads ``manifest.json`` (version, default_seed, start, files) and
        merges every listed file's ``nodes`` dict into one ``{node_id: Node}``
        mapping via ``Node.from_dict``. Raises ``ValueError`` on a duplicate
        node id across files (authoring error); lets ``KeyError`` from
        :meth:`get_node` propagate to callers (bad divert/goto fails loud).
        """
        manifest_path = os.path.join(story_dir, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        version = manifest.get("version", 1)
        default_seed = manifest.get("default_seed", 0)
        files = manifest.get("files", [])
        start = manifest.get("start")

        nodes = {}
        for filename in files:
            file_path = os.path.join(story_dir, filename)
            with open(file_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            raw_nodes = data.get("nodes", {})
            for node_id, raw in raw_nodes.items():
                if node_id in nodes:
                    raise ValueError(
                        "Duplicate node id {!r} in story file {!r} "
                        "(already defined in an earlier file)".format(
                            node_id, filename))
                # The node id is the JSON key; inject it so Node.from_dict's
                # required "id" field is satisfied without duplicating it in
                # each node body (keeps the {"nodes": {id: {...}}} shape that
                # the Phase 1 citation gate story-walker reads).
                raw_with_id = dict(raw)
                raw_with_id["id"] = node_id
                nodes[node_id] = Node.from_dict(raw_with_id)
        return cls(nodes, default_seed, version, start)

    def get_node(self, node_id):
        # type: (str) -> Node
        """Return the Node with id ``node_id`` (raises KeyError if missing).

        Callers check existence before advancing; letting KeyError propagate is
        the intended contract (fail-loud on a bad divert/goto target).
        """
        return self.nodes[node_id]

    def all_nodes(self):
        # type: () -> dict
        """Return the ``{node_id: Node}`` dict (NOT a list of values).

        The dict shape is the contract: Plan 03's ``check_reachability`` /
        ``validate_graph`` and Plan 05's tests consume ``{id: Node}``.
        """
        return self.nodes

    def start_node(self):
        # type: () -> str
        """Return the start node id (from the manifest's explicit ``start``)."""
        return self._start

    def endings(self):
        # type: () -> list
        """Return the list of ending Nodes (``is_ending`` is not None)."""
        return [n for n in self.nodes.values() if n.is_ending is not None]

    def __len__(self):
        return len(self.nodes)

    def __contains__(self, node_id):
        return node_id in self.nodes

    def __repr__(self):
        return "StoryGraph(nodes={}, endings={}, start={!r})".format(
            len(self.nodes), len(self.endings()), self._start)
