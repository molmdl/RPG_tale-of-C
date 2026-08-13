"""Citation registry loader for the no-fabricated-science gate. Pure-Python, stdlib only.

This module is the data source for ``tools/check_citations.py`` -- the pre-ship
gate that blocks release if any story node references a missing or
non-approved ``claim_id``. Together they enforce spec.md's strongest constraint
architecturally: *no fabricated science ships*.

The registry is a JSON object (``data/citations.json``) keyed by ``claim_id``,
each value a record carrying ``source`` metadata + ``approval_status``. The
gate's core predicate is ``approval_status == "approved"`` -- NOT ``!= "pending"``
(research Pitfall 6: ``!= "pending"`` would let a ``rejected`` claim pass).

Design constraints honored:
- Python 3.6 stdlib ONLY (``json``). NO ``@dataclass`` (3.7+ -- research
  Pitfall 1: verified ``ModuleNotFoundError: No module named 'dataclasses'``
  on python3.6.9). Plain class on a dict.
- NO pymol/PyQt5 imports (the Phase 1 AST gate in ``tools/check_imports.py``
  scans this file -- it lives in the gate-enforced ``c14/`` domain tier).
- Duplicate ``claim_id`` keys are detected at load via ``object_pairs_hook``
  (research Pitfall 3 -- verified working on 3.6.9); without it, ``json.load``
  silently last-wins, letting two authors clobber each other.

See .planning/phases/01-foundations-testability-citation-gate/01-RESEARCH-citations.md
Investigation Point 1 for the full reference design.
"""
import json


def _no_duplicate_keys(pairs):
    """``object_pairs_hook`` that rejects duplicate keys in the registry JSON.

    Without this, ``json.load`` silently keeps the *last* value for a duplicate
    key (verified). Two authors adding the same ``claim_id`` with different
    sources would clobber each other with no warning. This hook raises a
    ``ValueError`` naming the offending key so the loader can surface it.

    Verified working on ``python3.6.9`` (research Pitfall 3).
    """
    d = {}
    seen = set()
    for k, v in pairs:
        if k in seen:
            raise ValueError("duplicate claim_id in registry: {!r}".format(k))
        seen.add(k)
        d[k] = v
    return d


class CitationRegistry(object):
    """Loads + validates ``data/citations.json``. The gate's data source.

    A plain class (NOT ``@dataclass`` -- 3.6-incompatible) wrapping the loaded
    dict of ``claim_id -> claim record``. The gate's core predicate is
    :meth:`is_approved`, which is a single ``dict.get`` + status check
    (O(1) per referenced claim).
    """

    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"
    _VALID_STATUSES = (PENDING, APPROVED, REJECTED)

    def __init__(self, data):
        # data: dict of claim_id -> claim record (already validated by load())
        self._claims = data

    @classmethod
    def load(cls, path):
        """Load + validate a citation registry JSON file.

        Raises ``ValueError`` on:
        - malformed JSON (``json.JSONDecodeError`` is a ``ValueError`` subclass)
        - duplicate ``claim_id`` keys (via ``object_pairs_hook``)
        - non-dict top level (registry must be a JSON object keyed by claim_id)
        - any entry that is not a dict
        - any entry whose ``approval_status`` is not in ``_VALID_STATUSES``

        Returns a new ``CitationRegistry`` wrapping the loaded dict.
        """
        with open(path, "r") as f:
            data = json.load(f, object_pairs_hook=_no_duplicate_keys)
        if not isinstance(data, dict):
            raise ValueError(
                "citations registry must be a JSON object keyed by claim_id; "
                "got {}".format(type(data).__name__)
            )
        for cid, entry in data.items():
            if not isinstance(entry, dict):
                raise ValueError(
                    "claim {!r} must be an object; got {}".format(cid, type(entry).__name__)
                )
            status = entry.get("approval_status")
            if status not in cls._VALID_STATUSES:
                raise ValueError(
                    "claim {!r} has invalid approval_status: {!r} "
                    "(must be one of {})".format(cid, status, cls._VALID_STATUSES)
                )
        return cls(data)

    def is_approved(self, claim_id):
        """True iff ``claim_id`` exists AND its ``approval_status == "approved"``.

        This is the gate's core predicate. Note the strict equality: a
        ``rejected`` claim fails identically to a ``pending`` one (research
        Pitfall 6 -- ``!= "pending"`` would erroneously pass ``rejected``).
        Returns ``False`` for missing, pending, or rejected claims.
        """
        entry = self._claims.get(claim_id)
        return entry is not None and entry.get("approval_status") == self.APPROVED

    def status(self, claim_id):
        """Return the ``approval_status`` string, or ``None`` if missing.

        For gate reporting (``[UNAPPROVED] ... status is 'pending'``). Returns
        ``None`` for a missing claim so callers can distinguish missing from
        present-but-pending -- but note :meth:`is_approved` already covers the
        pass/fail decision; this is purely for the human-readable report.
        """
        entry = self._claims.get(claim_id)
        return entry.get("approval_status") if entry is not None else None

    def contains(self, claim_id):
        """True iff ``claim_id`` is a key in the registry (regardless of status)."""
        return claim_id in self._claims

    def __len__(self):
        return len(self._claims)

    def claim_ids(self):
        """Return a list of all ``claim_id`` keys in the registry."""
        return list(self._claims.keys())
