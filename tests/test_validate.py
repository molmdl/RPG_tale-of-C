"""Unit tests for ``c14.story.validate``.

Covers:
- ``check_reachability`` -- green (well-formed), red (orphaned ending),
  multi-hop chains, and the missing-start graceful edge case. Proves Phase 2
  success criterion #4 (the reachability checker reports green on a
  well-formed graph and red on one with an orphaned ending).
- ``validate_graph`` -- dangling divert detection + clean graph.
- ``collect_claim_ids`` -- on a single file (backward-compatible with the
  Phase 1 fixtures) and on a directory bundle (new multi-file capability),
  plus bad-schema and nonexistent-path error paths.

Fixtures are inline raw dicts (the simplest form) so the tests prove the
functions work on the raw JSON shapes the gate sees -- the same shapes
``collect_claim_ids`` returns. The ``_choices``/``_goto``/``_is_ending``
helpers in ``validate.py`` duck-type these dicts exactly like ``Node``
objects, so passing raw dicts exercises the same code path as Node objects.

Python 3.6 stdlib ONLY (``unittest``, ``os``, ``json``, ``tempfile``,
``shutil``). NO pytest (not installed). Temp files/dirs are created with
``tempfile.mkdtemp`` and removed in ``tearDown`` (no leak across tests).
"""
import json
import os
import shutil
import tempfile
import unittest

from c14.story.validate import (
    check_reachability,
    validate_graph,
    collect_claim_ids,
    ReachabilityReport,
    Issue,
)


# ---------------------------------------------------------------------------
# Inline fixture helpers (raw dicts -- the shape collect_claim_ids sees)
# ---------------------------------------------------------------------------

def _node(id, choices=None, claim_ids=None, is_ending=None):
    """Build a raw-dict node (same shape as JSON: id/choices/claim_ids/is_ending)."""
    return {
        "id": id,
        "choices": choices if choices is not None else [],
        "claim_ids": claim_ids if claim_ids is not None else [],
        "is_ending": is_ending,
    }


def _choice(goto=None, weight=None):
    """Build a raw-dict choice (goto/weight only -- enough for the algorithms)."""
    return {"goto": goto, "weight": weight}


class TestValidate(unittest.TestCase):
    """Unit tests for the graph validator + reachability checker + claim collector."""

    def setUp(self):
        self._tempdirs = []

    def tearDown(self):
        for d in self._tempdirs:
            shutil.rmtree(d, ignore_errors=True)

    # -- check_reachability -------------------------------------------------

    def test_reachability_green(self):
        """Well-formed graph (all endings reachable) -> is_ok True."""
        nodes = {
            "a": _node("a", [_choice("b"), _choice("c")]),
            "b": _node("b", is_ending="good"),
            "c": _node("c", is_ending="bad"),
        }
        report = check_reachability(nodes, "a")
        self.assertTrue(report.is_ok)
        self.assertEqual(sorted(report.reachable_endings), ["b", "c"])
        self.assertEqual(report.unreachable_endings, [])

    def test_reachability_red_orphaned(self):
        """Orphaned ending (no incoming edge) -> is_ok False, ending unreachable."""
        nodes = {
            "a": _node("a", [_choice("b")]),
            "b": _node("b", is_ending="good"),
            "c": _node("c", is_ending="bad"),  # c has no incoming edge
        }
        report = check_reachability(nodes, "a")
        self.assertFalse(report.is_ok)
        self.assertIn("c", report.unreachable_endings)
        self.assertIn("b", report.reachable_endings)

    def test_reachability_multi_hop(self):
        """Multi-hop chain a->b->c->ending: all reachable -> is_ok True."""
        nodes = {
            "a": _node("a", [_choice("b")]),
            "b": _node("b", [_choice("c")]),
            "c": _node("c", [_choice("end")]),
            "end": _node("end", is_ending="true"),
        }
        report = check_reachability(nodes, "a")
        self.assertTrue(report.is_ok)
        self.assertEqual(report.reachable_endings, ["end"])
        self.assertEqual(report.unreachable_endings, [])

    def test_reachability_missing_start(self):
        """start_id not in nodes -> graceful, is_ok False, all endings unreachable."""
        nodes = {"a": _node("a", is_ending="good")}
        report = check_reachability(nodes, "zzz")
        self.assertFalse(report.is_ok)
        self.assertEqual(report.unreachable_endings, ["a"])
        self.assertEqual(report.reachable_endings, [])

    def test_reachability_report_is_ok_property(self):
        """ReachabilityReport.is_ok is True iff unreachable_endings is empty."""
        ok = ReachabilityReport("s", ["e1"], ["e1"], [])
        bad = ReachabilityReport("s", ["e1", "e2"], ["e1"], ["e2"])
        self.assertTrue(ok.is_ok)
        self.assertFalse(bad.is_ok)

    # -- validate_graph -----------------------------------------------------

    def test_validate_graph_dangling_divert(self):
        """A choice.goto pointing to a nonexistent node -> one dangling_divert Issue."""
        nodes = {"a": _node("a", [_choice("nonexistent")])}
        issues = validate_graph(nodes)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].kind, "dangling_divert")
        self.assertEqual(issues[0].node_id, "a")
        self.assertIn("nonexistent", issues[0].detail)

    def test_validate_graph_clean(self):
        """Well-formed graph (all gotos resolve) -> empty issue list."""
        nodes = {
            "a": _node("a", [_choice("b")]),
            "b": _node("b", is_ending="good"),
        }
        self.assertEqual(validate_graph(nodes), [])

    def test_validate_graph_none_goto_ok(self):
        """A choice with goto=None is a leaf, not a dangling divert."""
        nodes = {"a": _node("a", [_choice(None)])}
        self.assertEqual(validate_graph(nodes), [])

    # -- collect_claim_ids (file) -------------------------------------------

    def test_collect_claim_ids_file(self):
        """Single .json file -> {node_id: [claim_id]} (backward-compat with Phase 1)."""
        d = tempfile.mkdtemp()
        self._tempdirs.append(d)
        path = os.path.join(d, "story.json")
        with open(path, "w") as f:
            json.dump({
                "nodes": {
                    "n1": {"claim_ids": ["c1"]},
                    "n2": {"claim_ids": ["c2", "c3"], "is_ending": "true"},
                }
            }, f)
        result = collect_claim_ids(path)
        self.assertEqual(result, {"n1": ["c1"], "n2": ["c2", "c3"]})

    def test_collect_claim_ids_file_no_claim_ids_key(self):
        """A node with no claim_ids key contributes an empty list (narrative node)."""
        d = tempfile.mkdtemp()
        self._tempdirs.append(d)
        path = os.path.join(d, "story.json")
        with open(path, "w") as f:
            json.dump({"nodes": {"n1": {"text": "no claims here"}}}, f)
        result = collect_claim_ids(path)
        self.assertEqual(result, {"n1": []})

    # -- collect_claim_ids (directory) -------------------------------------

    def test_collect_claim_ids_directory(self):
        """Directory with manifest.json + file(s) -> merged {node_id: [claim_id]}."""
        d = tempfile.mkdtemp()
        self._tempdirs.append(d)
        with open(os.path.join(d, "manifest.json"), "w") as f:
            json.dump({"files": ["x.json"]}, f)
        with open(os.path.join(d, "x.json"), "w") as f:
            json.dump({"nodes": {"n1": {"claim_ids": ["c1"]}}}, f)
        result = collect_claim_ids(d)
        self.assertEqual(result, {"n1": ["c1"]})

    def test_collect_claim_ids_directory_multi_file(self):
        """Directory with multiple manifest files -> all nodes merged."""
        d = tempfile.mkdtemp()
        self._tempdirs.append(d)
        with open(os.path.join(d, "manifest.json"), "w") as f:
            json.dump({"files": ["x.json", "y.json"]}, f)
        with open(os.path.join(d, "x.json"), "w") as f:
            json.dump({"nodes": {"n1": {"claim_ids": ["c1"]}}}, f)
        with open(os.path.join(d, "y.json"), "w") as f:
            json.dump({"nodes": {"n2": {"claim_ids": ["c2", "c3"]}}}, f)
        result = collect_claim_ids(d)
        self.assertEqual(result, {"n1": ["c1"], "n2": ["c2", "c3"]})

    # -- collect_claim_ids (error paths) -----------------------------------

    def test_collect_claim_ids_bad_schema_raises(self):
        """A file with non-dict 'nodes' raises ValueError (gate -> exit 2)."""
        d = tempfile.mkdtemp()
        self._tempdirs.append(d)
        path = os.path.join(d, "bad.json")
        with open(path, "w") as f:
            json.dump({"nodes": "not a dict"}, f)
        with self.assertRaises(ValueError):
            collect_claim_ids(path)

    def test_collect_claim_ids_nonexistent_raises(self):
        """A nonexistent path raises ValueError (gate catches -> exit 2)."""
        with self.assertRaises(ValueError):
            collect_claim_ids("does/not/exist")


if __name__ == "__main__":
    unittest.main()
