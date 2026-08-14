"""Edit routing: EditIntent -> story-node-id (known -> branch, unknown -> pool).

Pure-Python domain tier, AST-gate-clean (imports ONLY stdlib ``json`` + the
``c14.story`` data model + validator -- NO ``pymol``, NO ``random``).

The edit-routing model is settled (PROJECT.md Key Decisions: lookup table +
bad-ending fallback; the chemistry-correctness engine is OUT OF SCOPE). This
module implements the routing MECHANICS:

- :class:`EditIntent` (defined in :mod:`c14.story.model`) is the routing INPUT
  (player -> router). Its ``signature()`` produces a canonical match dict.
- :class:`EditsTable` loads the ``edits.json`` lookup table (CWD-independent).
- :class:`EditRouter` routes an ``EditIntent`` to a story-node id: a KNOWN edit
  (exact signature match) -> its ``branch_node``; an UNKNOWN edit -> a
  bad-ending pool node picked uniformly via the single injected ``RngEngine``
  (Anti-Pattern 7: all stochastic draws through the seeded engine, reproducible
  + save/load-safe).
- :func:`validate_edits_table` cross-validates the table against the story
  graph (dangling refs, empty pools, non-ending pool nodes, dup signatures).
- :func:`scan_edit_coverage` is the SC5 helper: every cast enzyme has >=1
  known-edit entry.

The router is STATELESS across playthroughs (mirrors StoryInterpreter): it
holds only the immutable ``EditsTable``; the ``RngEngine`` is passed per
``route()`` call. The router returns node-id STRINGS -- it never applies edits,
never names pymol. The edit APPLICATION (backup + alter + sort + rebuild) is
the apply_edit helper's job (``c14/pymol_layer/``), triggered by the routed
branch's ``on_enter`` MolAction.

Design constraints honored:
- Python 3.6 stdlib ONLY (``json``). NO ``@dataclass`` (3.7+). Plain classes
  on instance attributes, matching the Phase 1 ``CitationRegistry`` precedent.
- NO pymol/PyQt5 imports (the Phase 1 AST gate scans ``c14/`` root). NO
  ``random`` import (Anti-Pattern 7 -- all draws via the injected ``RngEngine``).
- Matching is EXACT dict equality on a normalized signature -- zero fuzzy /
  chemistry logic (Pitfall 1). Dict equality is order-independent on 3.6.9
  (empirically verified in 04-RESEARCH-edit-routing.md).
- ``.format()`` for string interpolation (the established repo convention).
"""

import json

from c14.story.model import EditIntent  # noqa: F401 (re-exported for callers)
from c14.story.validate import Issue, _is_ending


class EditRoutingError(Exception):
    """Raised when edit routing cannot proceed (e.g. empty bad-ending pool).

    Pitfall 2 mitigation: a missing/empty bad-ending pool raises this clear
    exception (NOT a bare ``IndexError`` from ``weighted_pick``) so the caller
    gets context about which enzyme has no fallback.
    """
    pass


class EditsTable(object):
    """The parsed ``edits.json`` lookup table (immutable data).

    Attributes:
        _table: the raw parsed dict (version, bad_ending_pool, enzymes).
    """

    def __init__(self, table):
        # type: (dict) -> None
        self._table = table

    @classmethod
    def load(cls, edits_path):
        # type: (str) -> EditsTable
        """Load + ``json.load`` ``edits.json`` from ``edits_path``.

        CWD-independent (explicit ``edits_path`` arg, mirrors
        ``StoryGraph.load(story_dir)``). The caller resolves the path.
        """
        with open(edits_path, "r", encoding="utf-8") as fh:
            return cls(json.load(fh))

    @property
    def global_pool(self):
        # type: () -> list
        """Return a copy of the top-level ``bad_ending_pool`` list."""
        return list(self._table.get("bad_ending_pool", []))

    def enzyme(self, enzyme_id):
        # type: (str) -> dict
        """Return the per-enzyme dict for ``enzyme_id`` (or ``None`` if absent).

        The returned dict (when not None) has ``edits`` (list) and an optional
        ``bad_ending_pool`` (list) override.
        """
        return self._table.get("enzymes", {}).get(enzyme_id)

    def to_dict(self):
        # type: () -> dict
        """Return the raw parsed table dict (the authoritative data)."""
        return self._table

    def __repr__(self):
        n_enzymes = len(self._table.get("enzymes", {}))
        return "EditsTable(enzymes={}, global_pool={})".format(
            n_enzymes, len(self.global_pool))


class EditRouter(object):
    """Routes an ``EditIntent`` to a story-node id.

    Known edit (exact signature match in the enzyme's ``edits`` list) -> the
    entry's ``branch_node``. Unknown edit (no match, or unknown enzyme) -> a
    bad-ending pool node picked uniformly via the injected ``RngEngine``.

    Stateless across playthroughs (mirrors ``StoryInterpreter``): holds only
    the immutable ``EditsTable``; the ``RngEngine`` is passed per ``route()``
    call so save/load reproducibility follows from the engine's existing RNG
    state sync.
    """

    def __init__(self, edits_table):
        # type: (EditsTable) -> None
        self._table = edits_table

    def route(self, edit_intent, enzyme_id, rng):
        # type: (EditIntent, str, object) -> str
        """Return the node id to enter (branch_node for known; pool node for unknown).

        Algorithm (deterministic, no fuzzy/chemistry -- Pitfall 1):

        1. ``sig = edit_intent.signature()`` (canonical match dict).
        2. Look up the enzyme's entry. If present, scan its ``edits`` list for
           an entry whose ``signature`` equals ``sig`` (EXACT dict equality).
           First match -> return its ``branch_node`` (KNOWN -> branch).
        3. No match (or unknown enzyme) -> bad-ending pool. Per-enzyme override
           if present + non-empty, else global fallback.
        4. Empty pool -> raise :class:`EditRoutingError` (Pitfall 2, fail-loud).
        5. ``rng.weighted_pick(pool, [1.0]*len(pool))`` -> uniform, reproducible
           (Anti-Pattern 7: all draws through the single seeded engine).
        """
        sig = edit_intent.signature()
        enzyme = self._table.enzyme(enzyme_id)
        if enzyme is not None:
            for entry in enzyme.get("edits", []):
                if entry.get("signature") == sig:  # EXACT dict equality
                    return entry["branch_node"]    # KNOWN -> branch
        pool = self.bad_ending_pool(enzyme_id)
        if not pool:
            raise EditRoutingError(
                "bad-ending pool is empty for enzyme {!r} (no per-enzyme pool "
                "and no/empty global pool)".format(enzyme_id))
        return rng.weighted_pick(list(pool), [1.0] * len(pool))

    def bad_ending_pool(self, enzyme_id):
        # type: (str) -> list
        """Return the effective bad-ending pool for ``enzyme_id``.

        OVERRIDE semantics (simpler + deterministic than merge): if the enzyme
        has a per-enzyme ``bad_ending_pool`` that is present + non-empty, use
        it; otherwise fall back to the global pool. Returns an empty list if
        both are empty (callers / :func:`validate_edits_table` check this;
        :meth:`route` raises :class:`EditRoutingError` on empty).
        """
        enzyme = self._table.enzyme(enzyme_id)
        if enzyme is not None:
            per = enzyme.get("bad_ending_pool")
            if per:  # per-enzyme override (non-empty)
                return list(per)
        return self._table.global_pool  # global fallback (may be empty)

    def __repr__(self):
        return "EditRouter(table={!r})".format(self._table)


def validate_edits_table(edits_table, story_nodes):
    # type: (EditsTable, dict) -> list
    """Cross-validate an ``EditsTable`` against a ``{id: node}`` story graph.

    Returns a list of :class:`c14.story.validate.Issue` (empty = valid). Checks:

    - ``dangling_edit_branch``: a ``branch_node`` not in ``story_nodes``.
    - ``dangling_pool_node``: a pool node id not in ``story_nodes``.
    - ``empty_bad_ending_pool``: the global pool OR a per-enzyme pool is empty.
    - ``pool_node_not_ending``: a pool node exists but ``_is_ending`` is False.
    - ``duplicate_signature``: two edits in one enzyme share a signature.

    Duck-types on ``story_nodes`` (Node objects OR raw dicts) via the existing
    ``_is_ending`` helper from :mod:`c14.story.validate`.
    """
    issues = []
    table = edits_table.to_dict()
    # Global pool checks (emptiness is an error here -- it's the ultimate
    # fallback for any enzyme without a per-enzyme override).
    gpool = table.get("bad_ending_pool", [])
    issues.extend(_check_pool(gpool, "global", story_nodes))
    # Per-enzyme checks. A per-enzyme pool that is ABSENT or EMPTY is NOT an
    # error -- it means "fall back to the global pool" (OVERRIDE semantics).
    # Only non-empty per-enzyme pools are checked for dangling/non-ending nodes.
    for eid, e in table.get("enzymes", {}).items():
        per_pool = e.get("bad_ending_pool")
        if per_pool:  # non-empty per-enzyme override -> validate its nodes
            issues.extend(_check_pool(per_pool, eid, story_nodes))
        seen = set()
        for entry in e.get("edits", []):
            bn = entry.get("branch_node")
            if bn is not None and bn not in story_nodes:
                issues.append(Issue(
                    "dangling_edit_branch", bn,
                    detail="enzyme {} branch_node".format(eid)))
            sig = json.dumps(entry.get("signature", {}), sort_keys=True)
            if sig in seen:
                issues.append(Issue(
                    "duplicate_signature", eid,
                    detail="signature {}".format(sig)))
            seen.add(sig)
    return issues


def _check_pool(pool, label, story_nodes):
    # type: (list, str, dict) -> list
    """Validate a single bad-ending pool list. Returns a list of Issue.

    Flags an empty pool (``empty_bad_ending_pool``), dangling pool node ids
    (``dangling_pool_node``), and pool nodes that exist but are not endings
    (``pool_node_not_ending``). ``label`` identifies which pool (``"global"``
    or the enzyme id) for the issue detail.
    """
    out = []
    if not pool:
        out.append(Issue("empty_bad_ending_pool", label))
    for nid in pool:
        if nid not in story_nodes:
            out.append(Issue(
                "dangling_pool_node", nid, detail="pool {}".format(label)))
        elif not _is_ending(story_nodes[nid]):
            out.append(Issue(
                "pool_node_not_ending", nid, detail="pool {}".format(label)))
    return out


def scan_edit_coverage(edits_table, cast_enzyme_ids):
    # type: (EditsTable, list) -> list
    """SC5 helper: every cast enzyme has >=1 known-edit entry.

    Returns a list of ``Issue(kind="missing_edit_coverage", node_id=<eid>)``
    for enzymes in ``cast_enzyme_ids`` that have no entry in the table OR an
    empty ``edits`` list. Phase 4: green on the placeholder cast; the 04-04
    plan's ``check_edit_coverage.py`` tool wraps this. The SHARED manifest =
    ``enzyme_id`` keys in ``edits.json`` MUST match the cast registry's enzyme
    ids (SC5).
    """
    issues = []
    enzymes = edits_table.to_dict().get("enzymes", {})
    for eid in cast_enzyme_ids:
        e = enzymes.get(eid)
        if e is None or not e.get("edits"):  # no entry OR empty edits list
            issues.append(Issue("missing_edit_coverage", eid))
    return issues
