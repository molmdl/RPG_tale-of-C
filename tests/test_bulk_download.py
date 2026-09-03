# Source: stdlib unittest + MockCmd inject pattern (mirrors tests/test_asset_manager.py).
# Python 3.6 compatible (unittest, os, tempfile, shutil, json -- all stdlib; NO pymol import).
#
# Pure-WSL unit tests for rpg.ui.bulk_download (the Qt-free bulk-download runner).
# The module under test imports ONLY `os`, `json`, `rpg.paths`, +
# `rpg.pymol_layer.asset_manager.AssetManager` (cmd is INJECTED as a function
# param, like AssetManager) -- so these tests run under python3.6 with no
# pymol/Qt installed. A MockCmd records `fetch` dispatches + returns a
# configurable count_atoms per object name so the AssetManager.fetch_pdb
# post-condition (RuntimeError on count_atoms<=0 = the failure signal) is
# exercisable.
#
# The REAL cmd.fetch / cmd.count_atoms contract is verified by
# tools/asset_smoke.py (headless) -- NOT these tests. These tests prove the
# runner's loop logic (per-file progress, cancel-between-files, failure
# recorded + continues, per-character lock mapping, PLACEHOLDER skip,
# Pitfall 3 lowercase filename check, Qt-free importability).
"""Unit tests for rpg.ui.bulk_download (Qt-free runner, MockCmd inject).

Pure WSL python3.6 -- NO pymol/Qt import. Tests:
  1. missing_large_pdbs on the REAL bundled cast (Phase 7 plan 07-15: 12 real
     download enzymes) -- hermetic via a temp downloaded dir; pins the 12-id
     bulk list + the real-pdb_id hygiene (no PLACEHOLDER ids remain).
  2. missing_large_pdbs detects a missing real pdb_id.
  3. missing_large_pdbs skips an existing lowercase file (Pitfall 3 cache).
  3b. missing_large_pdbs skips a PLACEHOLDER pdb_id (guard regression -- the
      Phase 6 contract, kept as a temp-cast unit test now that the real cast
      carries no placeholder entries).
  4. run_bulk_download success path (count_atoms>0 -> completed=N).
  5. run_bulk_download failure recorded + loop continues (count_atoms=0 ->
     RuntimeError; one failure does not abort the loop).
  6. run_bulk_download cancel between files (on_cancel_check -> break).
  7. run_bulk_download on_progress callback fired per file (i, total, pdb_id).
  8. characters_to_lock maps failed -> set of character ids (Pattern 2).
  9. characters_to_lock empty when no failures (glucose stays playable -- SC4).
  10. Qt-free import: `import rpg.ui.bulk_download` succeeds in pure WSL.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

import rpg.paths
import rpg.ui.bulk_download as bulk_download
from rpg.ui.bulk_download import (
    characters_to_lock,
    expected_download_characters,
    missing_large_pdbs,
    run_bulk_download,
)


class MockCmd(object):
    """Records every cmd.* dispatch as (name, args, kwargs); returns configurable count_atoms.

    ``count_atoms`` is an EXPLICIT method (overrides the __getattr__ fallback)
    returning ``self._counts.get(sel, self._default_count)`` so the
    AssetManager.fetch_pdb post-condition (``if count_atoms(...) <= 0: raise``)
    is exercisable per object name: set ``default_count=3`` for the success
    path, ``default_count=0`` for the all-fail path, or ``counts={obj: 0}``
    for a single failure in the middle of a loop (proves the loop continues).
    Explicit count_atoms is NOT recorded in self.calls (it is a post-
    condition probe, not a dispatched op) so ``calls`` holds only the real
    fetch dispatches -- mirroring tests/test_asset_manager.py's MockCmd.
    """

    def __init__(self, default_count=3, counts=None):
        self.calls = []
        self._default_count = default_count
        self._counts = counts or {}

    def __getattr__(self, name):
        # Returns a recording stub for any cmd.* attr except count_atoms
        # (which is an explicit method and bypasses __getattr__ entirely).
        def f(*a, **k):
            self.calls.append((name, a, k))
            return 0
        return f

    def count_atoms(self, sel="(all)"):
        # Explicit method -> normal attribute lookup finds this BEFORE
        # __getattr__ is consulted, so count_atoms is not recorded. Returns
        # the per-sel configured count or the default (so a single object can
        # be made to fail while others succeed -- proves loop-continues).
        return self._counts.get(sel, self._default_count)


class TestRealCastBulkList(unittest.TestCase):
    """Test 1: the REAL bundled cast.json download list is real, pre-fetchable data.

    Phase 7 plan 07-15 replaced the Phase-6 placeholder cast (fixture_enzyme_1
    + PLACEHOLDER_large_enzyme) with the 12 real mutable-enzyme entries (the
    rpg/data/edits.json buckets). This test pins the bulk-download list
    HERMETICALLY: the real cast manifest is read via an explicit cast_path
    while rpg.paths.data_path is monkeypatched to a temp root, so the
    downloaded-dir probe hits an empty temp dir -- the gitignored dev cache
    (rpg/data/assets/downloaded/) can never influence the result (cache state
    is environment-dependent; a fresh clone has NONE).
    """

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="rpg_bulkdl_realcast_")
        self._orig_data_path = rpg.paths.data_path
        # Capture the REAL cast path BEFORE patching (original data_path).
        self._real_cast_path = str(rpg.paths.data_path("data", "cast.json"))
        rpg.paths.data_path = self._fake_data_path

    def tearDown(self):
        rpg.paths.data_path = self._orig_data_path
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _fake_data_path(self, *parts):
        # Downloaded-dir probes resolve into a temp root (hermetic); the real
        # cast.json is read via the explicit cast_path captured in setUp.
        return os.path.join(self._tmp, *parts)

    def test_real_cast_lists_12_real_download_enzymes(self):
        # Empty temp downloaded dir -> EVERY download enzyme is "missing":
        # the full pre-play bulk list is exactly the 12 real cast entries.
        missing = missing_large_pdbs(None, cast_path=self._real_cast_path)
        self.assertEqual(len(missing), 12)
        by_pdb = {}
        for pdb_id, object_name, enzyme_id, character in missing:
            by_pdb[pdb_id] = (object_name, enzyme_id, character)
            # Real 4-char RCSB ids only -- the PLACEHOLDER guard must never be
            # needed again (plan 07-15 removed the placeholder cast entries).
            self.assertEqual(len(pdb_id), 4)
            self.assertTrue(pdb_id.isalnum())
            self.assertFalse(pdb_id.startswith("PLACEHOLDER"))
            # object_name = enzyme_id (the runner's naming convention) and the
            # glucose character is carried for the per-character lock mapping.
            self.assertEqual(object_name, enzyme_id)
            self.assertEqual(character, "glucose")
        # The exact bulk list (plan 07-15 recorded outcomes; update BOTH files
        # in the same plan if a cast id is ever swapped).
        self.assertEqual(
            set(by_pdb),
            {"4PFK", "7FS3", "6CFO", "1ACO", "5GRE", "6WCV",
             "5UPP", "4WLU", "5LDW", "1ZOY", "1BGY", "1OCC"})
        # All 12 download enzymes belong to the glucose character (lock UI).
        self.assertEqual(
            expected_download_characters(cast_path=self._real_cast_path),
            {"glucose"})


class TestMissingLargePdbsTempCast(unittest.TestCase):
    """Tests 2-3: missing-large-pdbs detection with a temp cast.json + temp downloaded dir.

    setUp writes a temp cast.json with a real-looking pdb_id "1abc" +
    source="download", and monkeypatches rpg.paths.data_path to a temp root
    so _downloaded_dir() probes a temp dir (NOT the real bundled downloaded
    dir -- keeps the test hermetic). The fake data_path returns <tmp>/<parts>
    so _downloaded_dir() -> <tmp>/data/assets/downloaded (Pitfall 3 lowercase
    check: <tmp>/data/assets/downloaded/1abc.pdb).
    """

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="rpg_bulkdl_missing_")
        self._orig_data_path = rpg.paths.data_path
        rpg.paths.data_path = self._fake_data_path
        # Temp cast.json with a real-looking download enzyme (non-PLACEHOLDER).
        self._cast_path = os.path.join(self._tmp, "cast.json")
        cast = {
            "version": 1,
            "enzymes": [
                {"id": "fixture_enzyme_1", "label": "Fixture (bundled)",
                 "fixture": "_edit_smoke.pdb", "source": "bundled",
                 "claim_id": "PLACEHOLDER_PHASE5"},
                {"id": "real_large_enzyme", "label": "Real large enzyme",
                 "source": "download", "pdb_id": "1abc", "character": "glucose",
                 "claim_id": "PLACEHOLDER_PHASE7"},
            ],
        }
        with open(self._cast_path, "w", encoding="utf-8") as fh:
            json.dump(cast, fh)

    def tearDown(self):
        rpg.paths.data_path = self._orig_data_path
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _fake_data_path(self, *parts):
        # Return <tmp>/<parts> so the downloaded dir probes a temp path.
        return os.path.join(self._tmp, *parts)

    def test_missing_large_pdbs_detects_missing(self):
        # The downloaded dir does NOT contain 1abc.pdb -> the entry is missing.
        # missing_large_pdbs returns [(pdb_id, object_name, enzyme_id, character)].
        missing = missing_large_pdbs(None, cast_path=self._cast_path)
        self.assertEqual(len(missing), 1)
        pdb_id, object_name, enzyme_id, character = missing[0]
        self.assertEqual(pdb_id, "1abc")
        self.assertEqual(object_name, "real_large_enzyme")  # object_name = enzyme_id
        self.assertEqual(enzyme_id, "real_large_enzyme")
        self.assertEqual(character, "glucose")

    def test_missing_large_pdbs_skips_existing(self):
        # Pitfall 3: create the LOWERCASE file 1abc.pdb in the temp downloaded
        # dir (cmd.fetch lowercases the code at importing.py:1200). The
        # idempotent cache is respected -> missing_large_pdbs returns [].
        downloaded = os.path.join(self._tmp, "data", "assets", "downloaded")
        os.makedirs(downloaded, exist_ok=True)
        # LOWERCASE filename (Pitfall 3 -- uppercase would be a false miss).
        with open(os.path.join(downloaded, "1abc.pdb"), "w") as fh:
            fh.write("dummy")
        missing = missing_large_pdbs(None, cast_path=self._cast_path)
        self.assertEqual(missing, [])

    def test_missing_large_pdbs_skips_placeholder_pdb_id(self):
        # Test 3b (guard regression, Phase 6 contract): a download enzyme whose
        # pdb_id starts with PLACEHOLDER is SKIPPED -- the prompt must never
        # fire for placeholder content. The real bundled cast no longer
        # carries placeholder entries (plan 07-15), so this contract is
        # exercised with a dedicated temp cast.
        cast_path2 = os.path.join(self._tmp, "cast_placeholder.json")
        cast2 = {
            "version": 1,
            "enzymes": [
                {"id": "ph_enzyme", "label": "Placeholder (regression probe)",
                 "source": "download", "pdb_id": "PLACEHOLDER_PDB",
                 "character": "glucose", "claim_id": "PLACEHOLDER_PHASE7"},
            ],
        }
        with open(cast_path2, "w", encoding="utf-8") as fh:
            json.dump(cast2, fh)
        self.assertEqual(missing_large_pdbs(None, cast_path=cast_path2), [])
        # The placeholder-only character is NOT in the lock universe either.
        self.assertEqual(expected_download_characters(cast_path=cast_path2),
                         set())


class TestRunBulkDownload(unittest.TestCase):
    """Tests 4-7: the Qt-free fetch loop (success / failure / cancel / progress).

    setUp monkeypatches rpg.paths.data_path to a temp root so
    AssetManager._download_dir() makedirs + writes into a temp dir (NOT the
    real bundled downloaded dir -- keeps the test hermetic). The missing_codes
    list is built directly (no cast.json needed for the loop logic).
    """

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="rpg_bulkdl_run_")
        self._orig_data_path = rpg.paths.data_path
        rpg.paths.data_path = self._fake_data_path

    def tearDown(self):
        rpg.paths.data_path = self._orig_data_path
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _fake_data_path(self, *parts):
        return os.path.join(self._tmp, *parts)

    def _make_missing(self, n, character="glucose"):
        # Build n missing-code 4-tuples: (pdb_id, object_name, enzyme_id, character).
        return [("pdb{0}".format(i), "obj{0}".format(i), "enz{0}".format(i), character)
                for i in range(n)]

    def test_run_bulk_download_success(self):
        # count_atoms=3 (>0) -> all fetches succeed; completed=N, failed=[], canceled=False.
        mock = MockCmd(default_count=3)
        missing = self._make_missing(3)
        result = run_bulk_download(mock, missing)
        self.assertEqual(result["completed"], 3)
        self.assertEqual(result["failed"], [])
        self.assertFalse(result["canceled"])
        # 3 fetch dispatches recorded (count_atoms is NOT recorded -- explicit method).
        fetch_calls = [c for c in mock.calls if c[0] == "fetch"]
        self.assertEqual(len(fetch_calls), 3)

    def test_run_bulk_download_failure_recorded(self):
        # Middle object fails (count_atoms=0 -> RuntimeError); the loop CONTINUES
        # (does not crash on one failure). completed=2, failed has 1 entry,
        # canceled=False. This proves Pattern 1's "loop continues past a failure".
        mock = MockCmd(default_count=3, counts={"obj1": 0})
        missing = self._make_missing(3)
        result = run_bulk_download(mock, missing)
        self.assertEqual(result["completed"], 2)  # obj0 + obj2 succeeded
        self.assertFalse(result["canceled"])
        self.assertEqual(len(result["failed"]), 1)
        pdb_id, enzyme_id, character, err = result["failed"][0]
        self.assertEqual(pdb_id, "pdb1")
        self.assertEqual(enzyme_id, "enz1")
        self.assertEqual(character, "glucose")
        # The error message is the RuntimeError string from AssetManager.fetch_pdb,
        # which formats with the pdb_id (code), NOT the object_name (asset_manager.py:125).
        self.assertIn("pdb1", err)
        # All 3 fetches were attempted (loop continued past the middle failure).
        fetch_calls = [c for c in mock.calls if c[0] == "fetch"]
        self.assertEqual(len(fetch_calls), 3)

    def test_run_bulk_download_cancel_between_files(self):
        # on_cancel_check returns True on the 3rd call (after 2 files fetched).
        # canceled=True, the loop breaks, the 3rd file is NOT fetched.
        # Pitfall 7: cancel is BETWEEN fetches (not mid-fetch).
        mock = MockCmd(default_count=3)
        missing = self._make_missing(3)
        call_count = [0]

        def on_cancel_check():
            call_count[0] += 1
            return call_count[0] >= 3  # True on the 3rd call (start of i=2)

        result = run_bulk_download(mock, missing, on_cancel_check=on_cancel_check)
        self.assertTrue(result["canceled"])
        self.assertEqual(result["completed"], 2)  # files 0 + 1 fetched before cancel
        self.assertEqual(result["failed"], [])
        # Only 2 fetches dispatched (file 2 was canceled before its fetch).
        fetch_calls = [c for c in mock.calls if c[0] == "fetch"]
        self.assertEqual(len(fetch_calls), 2)

    def test_run_bulk_download_on_progress_callback(self):
        # on_progress called with (i, total, pdb_id) per file BEFORE the fetch.
        mock = MockCmd(default_count=3)
        missing = self._make_missing(3)
        progress_calls = []

        def on_progress(i, total, pdb_id):
            progress_calls.append((i, total, pdb_id))

        result = run_bulk_download(mock, missing, on_progress=on_progress)
        self.assertEqual(result["completed"], 3)
        self.assertEqual(len(progress_calls), 3)
        self.assertEqual(progress_calls[0], (0, 3, "pdb0"))
        self.assertEqual(progress_calls[1], (1, 3, "pdb1"))
        self.assertEqual(progress_calls[2], (2, 3, "pdb2"))


class TestCharactersToLock(unittest.TestCase):
    """Tests 8-9: Pattern 2 per-character lock mapping (pure data, no cmd)."""

    def test_characters_to_lock_maps_failed_to_characters(self):
        # failed = [(pdb, enzyme, character, err)] -> {character} (Pattern 2).
        failed = [("1abc", "real_large_enzyme", "glucose", "RuntimeError: no atoms")]
        locked = characters_to_lock(failed)
        self.assertEqual(locked, {"glucose"})

    def test_characters_to_lock_empty_when_no_failures(self):
        # No failures -> empty lock set -> all characters playable (SC4 "locks
        # only affected characters"; glucose's bundled structures keep it
        # always playable even if other characters' downloads failed).
        self.assertEqual(characters_to_lock([]), set())

    def test_characters_to_lock_dedupes_characters(self):
        # Two failures for the same character -> one entry in the lock set.
        failed = [
            ("1abc", "enz_a", "glucose", "err1"),
            ("2xyz", "enz_b", "glucose", "err2"),
            ("3pdq", "enz_c", "fatty_acid", "err3"),
        ]
        locked = characters_to_lock(failed)
        self.assertEqual(locked, {"glucose", "fatty_acid"})


class TestRunnerQtFreeImport(unittest.TestCase):
    """Test 10: the runner imports cleanly in pure WSL python3.6 (no Qt/pymol).

    rpg/ui/ is gate-EXEMPT (tools/check_imports.py SKIP_DIRS) so the AST gate
    never scans bulk_download.py. This test is the runtime twin: importing
    the module must not pull in pymol/PyQt5 as a side effect (it stays Qt-free
    by design -- cmd is injected, NOT imported at module top).
    """

    def test_runner_qt_free_import(self):
        # The module-level import at the top of this file already proved
        # importability; re-assert + check sys.modules for the gate-clean twin.
        # (Re-import is a no-op if already loaded -- Python caches modules.)
        import importlib
        importlib.reload(bulk_download)
        self.assertNotIn(
            "pymol", sys.modules,
            "rpg.ui.bulk_download must not import pymol (Qt-free runner)")
        self.assertNotIn(
            "PyQt5", sys.modules,
            "rpg.ui.bulk_download must not import PyQt5 (Qt-free runner)")


if __name__ == "__main__":
    unittest.main()
