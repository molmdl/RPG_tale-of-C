"""Tests for the citation registry + pre-ship gate.

Two test classes:

1. ``TestCitationRegistry`` -- unit tests importing ``c14.citations`` directly
   (no subprocess). Covers load() on all 4 fixture registries (pass/pending/
   missing/rejected) + error paths (bad status, malformed JSON, duplicate keys).

2. ``TestCheckCitationsExitCodes`` -- subprocess tests running
   ``tools/check_citations.py`` and asserting exit codes (0/1/2). The script's
   contract is its exit code, so subprocess is the canonical way to test it
   (in-process function calls don't verify the sys.exit + CLI wiring).

Python 3.6 stdlib ONLY (``unittest``, ``subprocess``, ``os``, ``sys``,
``tempfile``). NO pytest (not installed). subprocess uses
``stdout/stderr=PIPE`` + manual ``.decode()`` (NOT ``capture_output=True`` /
``text=True`` -- both 3.7+; this matches the verified pattern in
``tests/test_imports.py``). Tests use ``os.path`` relative to ``__file__``
(not CWD) so they pass regardless of working directory, and ``sys.executable``
(not hardcoded ``python3.6``) so the same interpreter running the test runs
the gate.

See .planning/phases/01-foundations-testability-citation-gate/01-RESEARCH-citations.md
Investigation Point 5 + Code Examples for the reference design.
"""
import os
import subprocess
import sys
import tempfile
import unittest

from c14.citations import CitationRegistry

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(HERE, "..")
FIXTURES = os.path.join(HERE, "fixtures")
GATE_SCRIPT = os.path.join(REPO_ROOT, "tools", "check_citations.py")


def _write_temp_registry(content):
    """Write ``content`` (a JSON string) to a NamedTemporaryFile and return its path.

    Caller is responsible for ``os.unlink(path)`` when done. ``delete=False``
    is required so the file survives closing (we pass the path to
    ``CitationRegistry.load``, which re-opens it).
    """
    fh = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        fh.write(content)
        fh.flush()
    finally:
        fh.close()
    return fh.name


class TestCitationRegistry(unittest.TestCase):
    """Unit tests for ``c14.citations.CitationRegistry`` (direct import, no subprocess)."""

    def test_load_pass_registry(self):
        reg = CitationRegistry.load(os.path.join(FIXTURES, "citations_pass.json"))
        self.assertTrue(reg.is_approved("placeholder-claim-1"))
        self.assertTrue(reg.is_approved("placeholder-claim-2"))
        self.assertEqual(len(reg), 2)
        self.assertIn("placeholder-claim-1", reg.claim_ids())
        self.assertIn("placeholder-claim-2", reg.claim_ids())

    def test_load_pending_registry(self):
        reg = CitationRegistry.load(os.path.join(FIXTURES, "citations_fail_pending.json"))
        # claim-1 is approved, claim-2 is pending -> not approved
        self.assertTrue(reg.is_approved("placeholder-claim-1"))
        self.assertFalse(reg.is_approved("placeholder-claim-2"))
        self.assertEqual(reg.status("placeholder-claim-2"), "pending")

    def test_load_missing_claim(self):
        reg = CitationRegistry.load(os.path.join(FIXTURES, "citations_fail_missing.json"))
        # claim-2 is absent entirely
        self.assertFalse(reg.contains("placeholder-claim-2"))
        self.assertIsNone(reg.status("placeholder-claim-2"))
        self.assertFalse(reg.is_approved("placeholder-claim-2"))
        # claim-1 is present and approved
        self.assertTrue(reg.contains("placeholder-claim-1"))
        self.assertEqual(len(reg), 1)

    def test_load_rejected_registry(self):
        reg = CitationRegistry.load(os.path.join(FIXTURES, "citations_fail_rejected.json"))
        # claim-2 is rejected -> must NOT be approved (Pitfall 6: == 'approved', not != 'pending')
        self.assertFalse(reg.is_approved("placeholder-claim-2"))
        self.assertEqual(reg.status("placeholder-claim-2"), "rejected")
        # claim-1 still approved
        self.assertTrue(reg.is_approved("placeholder-claim-1"))

    def test_load_bad_status_raises(self):
        # Typo in approval_status -- loader must reject at load time.
        bad = '{"placeholder-claim-1": {"approval_status": "appproved"}}'
        path = _write_temp_registry(bad)
        try:
            with self.assertRaises(ValueError):
                CitationRegistry.load(path)
        finally:
            os.unlink(path)

    def test_load_malformed_raises(self):
        # Malformed JSON -- json.JSONDecodeError is a ValueError subclass, so
        # the loader (which does not catch it) propagates it as ValueError.
        with self.assertRaises(ValueError):
            CitationRegistry.load(os.path.join(FIXTURES, "citations_malformed.json"))

    def test_load_duplicate_keys_raises(self):
        # Duplicate claim_id key in the JSON source -- object_pairs_hook must
        # detect it (Pitfall 3). Without the hook, json.load silently last-wins.
        dup = (
            '{"placeholder-claim-1": {"approval_status": "approved"}, '
            '"placeholder-claim-1": {"approval_status": "pending"}}'
        )
        path = _write_temp_registry(dup)
        try:
            with self.assertRaises(ValueError):
                CitationRegistry.load(path)
        finally:
            os.unlink(path)


class TestCheckCitationsExitCodes(unittest.TestCase):
    """Subprocess tests for ``tools/check_citations.py`` exit codes.

    The gate's contract is its exit code (0/1/2), so we run it as a subprocess
    and assert ``.returncode`` + stdout/stderr content. In-process function
    calls would not verify the ``sys.exit`` + argparse wiring.
    """

    def _run(self, story, registry):
        """Run the gate with the named fixture files. Returns the CompletedProcess.

        Uses ``stdout/stderr=PIPE`` + manual decode (NOT ``capture_output`` /
        ``text`` -- both 3.7+; matches the verified pattern in test_imports.py).
        Paths are resolved relative to this test file (not CWD) so the tests
        pass regardless of working directory.
        """
        return subprocess.run(
            [sys.executable, GATE_SCRIPT,
             "--story", os.path.join(FIXTURES, story),
             "--registry", os.path.join(FIXTURES, registry)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def test_pass(self):
        r = self._run("story_pass.json", "citations_pass.json")
        stdout = r.stdout.decode("utf-8")
        self.assertEqual(r.returncode, 0, "expected exit 0 (pass)\nstdout=%r\nstderr=%r"
                         % (stdout, r.stderr.decode("utf-8")))
        self.assertIn("PASSED", stdout)

    def test_fail_pending(self):
        r = self._run("story_pass.json", "citations_fail_pending.json")
        stdout = r.stdout.decode("utf-8")
        self.assertEqual(r.returncode, 1, "expected exit 1 (pending)\nstdout=%r" % stdout)
        self.assertIn("UNAPPROVED", stdout)
        self.assertIn("pending", stdout)

    def test_fail_missing(self):
        r = self._run("story_pass.json", "citations_fail_missing.json")
        stdout = r.stdout.decode("utf-8")
        self.assertEqual(r.returncode, 1, "expected exit 1 (missing)\nstdout=%r" % stdout)
        self.assertIn("MISSING", stdout)

    def test_fail_rejected(self):
        r = self._run("story_pass.json", "citations_fail_rejected.json")
        stdout = r.stdout.decode("utf-8")
        self.assertEqual(r.returncode, 1, "expected exit 1 (rejected)\nstdout=%r" % stdout)
        self.assertIn("UNAPPROVED", stdout)
        self.assertIn("rejected", stdout)

    def test_malformed(self):
        r = self._run("story_pass.json", "citations_malformed.json")
        stderr = r.stderr.decode("utf-8")
        self.assertEqual(r.returncode, 2, "expected exit 2 (malformed/config error)\nstderr=%r" % stderr)
        self.assertIn("ERROR", stderr)


if __name__ == "__main__":
    unittest.main()
