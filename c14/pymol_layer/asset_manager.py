# c14/pymol_layer/asset_manager.py -- Phase 3 Plan 03-02 AssetManager.
#
# Thin asset resolver + loader for the PyMOL cmd layer. Resolves a bundled
# PDB and a fetched PubChem/PDB substrate to local files and loads each into
# a non-empty PyMOL object, with the cmd.fetch pitfalls (CIF default, `path=.`
# cwd default, async interactive default -- 03-RESEARCH.md §2 Pitfall 5)
# mitigated by ALWAYS passing type=, async_=0, path=<abs dir>.
#
# DESIGN -- 3-tier testability pattern (inject cmd):
#   * cmd is INJECTED via the constructor (NOT imported at module top). This
#     keeps the module importable in pure WSL python3.6 with no pymol
#     installed, so the dispatch/path/arg logic is unit-testable with a
#     MockCmd (tests/test_asset_manager.py).
#   * The REAL cmd.* calls (cmd.load, cmd.fetch, cmd.count_atoms post-
#     conditions) are verified by tools/asset_smoke.py (headless via
#     tools/run_headless.sh -- the WSL->Windows PyMOL bridge), NOT by unit
#     tests. Unit tests prove the dispatch/path/args; the smoke proves the
#     real API contract.
#
# GATE EXCLUSION: lives in c14/pymol_layer/ which tools/check_imports.py
# excludes via SKIP_DIRS = {"pymol_layer","ui","__pycache__"} -- the domain
# tier (c14/ root) stays pure-Python (no pymol import).
#
# PYTHON 3.6 ONLY: plain class on instance attributes, .format() strings,
# NO @dataclass / walrus (matches Phase 1/2 precedent; 3.6.9 has no
# dataclasses module).
#
# Every self._cmd.load / self._cmd.fetch call carries a
# `# src: tmp/pymol-src/modules/pymol/<file>.py:<line> cmd.<name>` comment on
# the line directly above -- the source-citation convention established by
# Plan 03-01 (success criterion #4). Line numbers pinned to PyMOL 2.5.0.
"""AssetManager -- resolves bundled/fetched assets into PyMOL objects.

Inject ``cmd`` so the path/arg logic is unit-testable in pure WSL python3.6
with a MockCmd (the real cmd.* calls are verified by tools/asset_smoke.py,
not unit tests). All fetch calls force ``type=``, ``async_=0``, ``path=<abs
dir>`` to mitigate the three cmd.fetch pitfalls (03-RESEARCH.md §2):

  * Pitfall 5a -- CIF default: ``type=''`` resolves to ``cif`` (importing.py:1346).
    We always pass ``type=`` explicitly (``"cid"``/``"sid"`` for PubChem,
    ``"pdb"`` for PDB proteins).
  * Pitfall 5b -- ``path`` default = cwd: ``path`` defaults to
    ``get('fetch_path') or '.'`` (importing.py:1379-1381) so downloads land
    in the cmd.exe cwd. We always pass the ABSOLUTE plugin downloaded dir.
  * Pitfall 5c -- async default: API default ``async_=0`` is sync in 2.5.0
    (importing.py:1382-1383), but the interactive/CLI default differs. We
    always pass ``async_=0`` explicitly as defense.
"""
import os

import c14.paths


class AssetManager(object):
    """Resolve asset keys to local files and load/fetch them into PyMOL objects.

    Constructor takes the PyMOL ``cmd`` object (dependency injection) so the
    dispatch/path/arg logic is unit-testable in pure WSL python3.6 with a
    MockCmd. The real cmd.* calls are verified by the headless smoke
    (tools/asset_smoke.py).
    """

    def __init__(self, cmd):
        self._cmd = cmd

    def _download_dir(self):
        """Return the absolute downloaded-asset dir, creating it if missing.

        Uses c14.paths.data_path (``__file__``-relative -- cwd-independent,
        Phase 1 invariant). The dir MUST exist before cmd.fetch because
        fetch expects ``path`` to be a real directory. ``exist_ok=True`` is
        idempotent. The dir is gitignored (Plan 03-01 .gitignore entry).
        """
        d = str(c14.paths.data_path("data", "assets", "downloaded"))
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        return d

    def load_bundled(self, filename, object_name):
        """Load a bundled PDB into ``object_name``; assert non-empty.

        Resolves ``filename`` under c14/data/assets/bundled/ (committed;
        ships in the plugin zip) via the ABSOLUTE c14.paths.data_path --
        relative paths break headless (cmd.exe cwd, Pitfall 1). cmd.load
        returns None (importing.py:635) so we use count_atoms as the
        post-condition.
        """
        # src: tmp/pymol-src/modules/pymol/importing.py:635 cmd.load
        p = str(c14.paths.data_path("data", "assets", "bundled", filename))
        self._cmd.load(p, object_name)
        if self._cmd.count_atoms(object_name) <= 0:
            raise RuntimeError(
                "load_bundled: {0} produced no atoms".format(filename)
            )
        return object_name

    def fetch_pubchem(self, cid, object_name, kind="cid"):
        """Fetch a PubChem substrate (cid/sid) into ``object_name``; assert non-empty.

        Pitfall 5 mitigations baked in: ``type=kind`` (NOT the CIF default),
        ``async_=0`` (sync -- NOT the interactive default), ``path=<abs dir>``
        (NOT cwd). Network required; on failure the count_atoms post-
        condition raises RuntimeError("... (offline?)").
        """
        # src: tmp/pymol-src/modules/pymol/importing.py:1323 cmd.fetch
        d = self._download_dir()
        self._cmd.fetch(str(cid), object_name, type=kind, async_=0, path=d)
        if self._cmd.count_atoms(object_name) <= 0:
            raise RuntimeError(
                "fetch_pubchem: cid {0} produced no atoms (offline?)".format(cid)
            )
        return object_name

    def fetch_pdb(self, code, object_name, ftype="pdb"):
        """Fetch a PDB-type structure (default pdb -- NOT the CIF default) into ``object_name``.

        Same Pitfall 5 mitigations as fetch_pubchem, but ``ftype`` defaults to
        ``"pdb"`` (proteins) rather than the cmd.fetch CIF default.
        """
        # src: tmp/pymol-src/modules/pymol/importing.py:1323 cmd.fetch
        d = self._download_dir()
        self._cmd.fetch(str(code), object_name, type=ftype, async_=0, path=d)
        if self._cmd.count_atoms(object_name) <= 0:
            raise RuntimeError(
                "fetch_pdb: {0} produced no atoms".format(code)
            )
        return object_name
