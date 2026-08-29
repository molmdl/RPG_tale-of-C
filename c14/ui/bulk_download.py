# c14/ui/bulk_download.py -- Qt-free bulk-download runner (CAST-04).
#
# One-time bulk-download primitive for large PDB structures. On first play,
# the controller asks `missing_large_pdbs(cmd)` which large PDBs are not yet
# on disk; if any, it shows a modal dialog (c14/ui/bulk_download_dialog.py)
# that loops `AssetManager.fetch_pdb` once per missing code, updating the
# label + value BETWEEN fetches via QApplication.processEvents().
#
# `cmd.fetch(async_=0)` is SYNC + blocking with NO per-byte progress callback
# (importing.py:1386-1393 calls _multifetch directly; the _fetch download loop
# at importing.py:1215-1245 has no per-byte callback hook). So the UX is a
# PER-FILE progress loop with processEvents() between fetches (NOT per-byte).
# This is CORRECT, not a bug -- see 06-RESEARCH-persistence-achievements.md
# Pitfall 1.
#
# DESIGN -- Qt-free for WSL testability (mirror the Phase 3 AssetManager
# inject-cmd pattern):
#   * This module lives in c14/ui/ (gate-EXEMPT via tools/check_imports.py
#     SKIP_DIRS) but DOES NOT import pymol.Qt -- it is the Qt-FREE runner.
#     It imports only `os`, `json`, `c14.paths`, and
#     `c14.pymol_layer.asset_manager.AssetManager` at module top. `cmd` is
#     a FUNCTION PARAMETER (dependency injection, exactly like AssetManager),
#     so the runner is unit-testable in pure WSL python3.6 with a MockCmd
#     (tests/test_bulk_download.py) and NO Qt/pymol installed.
#   * The QDialog wrapper (c14/ui/bulk_download_dialog.py) IS gate-exempt
#     and DOES import pymol.Qt -- it wraps this runner, calling
#     on_progress/on_cancel_check callbacks that pump the Qt event loop
#     BETWEEN fetches (NOT during -- cmd.fetch blocks).
#
# GATE COMPLIANCE: although c14/ui/ is in SKIP_DIRS, this module imports
# ONLY stdlib + c14.* (no pymol.Qt) so it stays importable in pure WSL
# python3.6. The AST gate never scans it (SKIP_DIRS), but importing it is
# the runtime proof (tests/test_bulk_download.py::test_runner_qt_free_import).
#
# PYTHON 3.6 ONLY: plain functions, .format() strings, no f-strings, no
# @dataclass / walrus (matches Phase 1-4 precedent; 3.6.9 has no dataclasses
# module).
#
# cmd.fetch Pitfall 5 mitigations are baked into AssetManager.fetch_pdb
# (type="pdb" NOT CIF default, async_=0 sync, path=<abs downloaded dir>) --
# the runner delegates to fetch_pdb and NEVER calls cmd.fetch directly
# (06-RESEARCH-persistence-achievements.md Anti-Pattern). cmd.fetch skips
# already-downloaded files (importing.py:1211-1213) so retry is a free
# idempotent cache -- the runner's missing_large_pdbs already filters them
# out, and re-running on retry only re-fetches the still-missing ones.
"""Qt-free bulk-download runner for large PDB structures (CAST-04).

Importable in pure WSL python3.6 with no Qt/pymol installed (cmd is INJECTED
as a function parameter, mirroring c14.pymol_layer.asset_manager.AssetManager).
The QDialog wrapper (c14/ui/bulk_download_dialog.py) calls these functions
via on_progress/on_cancel_check callbacks that pump QApplication.processEvents()
BETWEEN fetches (NOT during -- cmd.fetch(async_=0) is sync + blocking with NO
per-byte progress callback; see 06-RESEARCH-persistence-achievements.md
Pitfall 1).

Functions:
  * missing_large_pdbs(cmd, cast_path=None) -> list of (pdb_id, object_name,
    enzyme_id, character) for expected-but-not-yet-downloaded large PDBs.
  * run_bulk_download(cmd, missing_codes, on_progress=None,
    on_cancel_check=None) -> {"completed", "failed", "canceled"}.
  * characters_to_lock(failed, cast_path=None) -> set of character ids to
    lock on the character-select screen (offline fallback -- Pattern 2).
  * expected_download_characters(cast_path=None) -> set of character ids
    that have >=1 download enzyme (for the lock UI).

Phase 6 caveat: the only download enzyme in c14/data/cast.json is
PLACEHOLDER_large_enzyme with pdb_id "PLACEHOLDER_PDB" -- the PLACEHOLDER
guard in missing_large_pdbs skips it, so the bulk-download prompt does NOT
fire for placeholder content. Phase 7 fills the real per-enzyme large-PDB
list (05.4 no-fabricated-science -- do NOT fabricate real PDB IDs here).
"""
import json
import os

import c14.paths
from c14.pymol_layer.asset_manager import AssetManager


def _default_cast_path(cast_path):
    """Return the cast.json path to read -- explicit arg or the bundled default.

    The bundled default lives at c14/data/cast.json (cwd-independent via
    c14.paths.data_path -- __file__-relative, Pitfall 1 mitigation). Tests
    pass an explicit cast_path pointing at a temp file so they don't touch
    the bundled manifest.
    """
    if cast_path is not None:
        return cast_path
    return str(c14.paths.data_path("data", "cast.json"))


def _load_cast(cast_path):
    """Read + parse cast.json; return the enzymes list (empty on missing file).

    Returns the ``enzymes`` list (a list of enzyme dicts). On a missing or
    unreadable file, returns an empty list (graceful -- the caller treats an
    empty expected list as "nothing to download"). On invalid JSON, raises
    ValueError (json.JSONDecodeError is a ValueError subclass on 3.6+); the
    bundled manifest MUST be valid JSON so a parse error is a real bug, not
    a graceful path.
    """
    with open(cast_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("enzymes", [])


def _downloaded_dir():
    """Return the absolute downloaded-asset dir (cwd-independent, Pitfall 1).

    Mirrors AssetManager._download_dir's path resolution (c14.paths.data_path)
    but does NOT create the dir -- the existence check in missing_large_pdbs
    is a pure os.path.exists probe (the dir may not exist yet on first play,
    which is fine -- every expected file is "missing" -> the prompt fires).
    AssetManager._download_dir makedirs on demand when fetch_pdb actually
    runs.
    """
    return str(c14.paths.data_path("data", "assets", "downloaded"))


def missing_large_pdbs(cmd, cast_path=None):
    """Return the list of expected-but-missing large PDB structures to download.

    Reads cast.json (explicit ``cast_path`` or the bundled default); for each
    enzyme with ``source == "download"`` and a non-PLACEHOLDER ``pdb_id``,
    checks whether the lowercase PDB file already exists in the downloaded
    dir (Pitfall 3: cmd.fetch lowercases the code at importing.py:1200 before
    building the filename at :1206, so the on-disk file is ``<pdb_id>.lower()
    + ".pdb"`` -- checking the uppercase code would always miss on a
    case-sensitive filesystem, defeating the free idempotent cache). Returns
    a list of 4-tuples ``(pdb_id, object_name, enzyme_id, character)`` for the
    MISSING ones (the prompt's fetch list).

    ``cmd`` is accepted for API symmetry with run_bulk_download (the QDialog
    helper calls ``missing = missing_large_pdbs(cmd)`` then
    ``run_bulk_download(cmd, missing)``); it is NOT used here -- the missing
    check is a pure os.path.exists probe, no cmd.* call. Kept in the signature
    so the caller does not have to thread two different arg shapes.

    The ``object_name`` is the enzyme_id (the PyMOL object name the story
    graph's ``load`` MolAction will reference -- e.g. ``{"op":"load",
    "target":"<enzyme_id>"}``). This keeps the bulk-download object name
    consistent with the on_enter scene-rebuild naming. Phase 7 may revisit
    if a different convention emerges (e.g. pdb_id as object name); document
    in the Phase 7 plan.

    PLACEHOLDER guard: ``pdb_id.startswith("PLACEHOLDER")`` entries are
    SKIPPED -- the bulk-download prompt does NOT fire for placeholder content
    (Phase 6's only download enzyme is PLACEHOLDER_large_enzyme -> this
    returns []). Phase 7's real entries (real PDB IDs, human-approved per
    05.4 no-fabricated-science) will trigger the prompt.
    """
    # `cmd` reserved for API symmetry with run_bulk_download (unused here).
    del cmd
    enzymes = _load_cast(_default_cast_path(cast_path))
    out = []
    downloaded = _downloaded_dir()
    for enz in enzymes:
        if enz.get("source") != "download":
            continue
        pdb_id = enz.get("pdb_id")
        if not pdb_id:
            continue
        if str(pdb_id).startswith("PLACEHOLDER"):
            # PLACEHOLDER guard: skip placeholder pdb_ids so the prompt does
            # NOT fire for placeholder content (Phase 6 only has PLACEHOLDER).
            continue
        # Pitfall 3: the on-disk file is lowercase (importing.py:1200 lowercases
        # the code before building the filename at :1206). Use .lower() so the
        # existence check matches the actual file cmd.fetch writes.
        expected_file = os.path.join(downloaded, str(pdb_id).lower() + ".pdb")
        if os.path.exists(expected_file):
            # Idempotent cache respected -- already downloaded, skip.
            continue
        enzyme_id = enz.get("id")
        character = enz.get("character")
        object_name = enzyme_id  # story-graph load target naming convention
        out.append((str(pdb_id), object_name, enzyme_id, character))
    return out


def run_bulk_download(cmd, missing_codes, on_progress=None, on_cancel_check=None):
    """Run the per-file fetch loop; return {completed, failed, canceled}.

    The Qt-free bulk-download primitive. Loops ``AssetManager.fetch_pdb`` once
    per ``(pdb_id, object_name, enzyme_id, character)`` in ``missing_codes``.
    Between fetches:
      * calls ``on_cancel_check()`` (if provided) -- returns True -> abort the
        LOOP after the current file (NOT a mid-fetch interrupt; cmd.fetch is
        blocking -- Pitfall 7). Sets ``canceled = True`` and breaks.
      * calls ``on_progress(i, total, pdb_id)`` (if provided) -- the QDialog
        wrapper uses this to update the label + value bar then pump
        QApplication.processEvents() so the cancel button stays live.

    ``AssetManager.fetch_pdb`` raises ``RuntimeError`` on
    ``count_atoms <= 0`` (asset_manager.py:123-126) -- the per-file failure
    signal (offline / 404 / corrupt). The loop CATCHES the exception, records
    the failure as ``(pdb_id, enzyme_id, character, str(e))`` in ``failed``,
    and CONTINUES to the next file (one failure does not abort the loop --
    the player still gets the structures that DID download). The QDialog
    wrapper maps ``failed`` to per-character locks via characters_to_lock
    (Pattern 2 -- locks only affected characters, NOT the whole game;
    glucose's bundled structures keep it always playable).

    Returns ``{"completed": int, "failed": list, "canceled": bool}``.
    ``completed`` is the count of successfully fetched files (excludes
    failures). Retry is idempotent: cmd.fetch skips already-downloaded files
    (importing.py:1211-1213) AND missing_large_pdbs already filters them, so
    re-running only re-fetches the still-missing ones (free cache).
    """
    assets = AssetManager(cmd)
    failed = []
    completed = 0
    canceled = False
    total = len(missing_codes)
    for i, entry in enumerate(missing_codes):
        pdb_id, object_name, enzyme_id, character = entry
        # Cancel check BETWEEN fetches (NOT mid-fetch -- cmd.fetch blocks;
        # Pitfall 7). The QDialog's on_cancel_check pumps processEvents
        # first so the cancel click is observed before we decide to abort.
        if on_cancel_check is not None and on_cancel_check():
            canceled = True
            break
        if on_progress is not None:
            on_progress(i, total, pdb_id)
        try:
            # AssetManager.fetch_pdb bakes in the Pitfall-5 mitigations
            # (type="pdb" NOT CIF default, async_=0 sync, path=<abs dir>).
            # Raises RuntimeError on count_atoms<=0 -- the failure signal.
            assets.fetch_pdb(pdb_id, object_name)
            completed += 1
        except Exception as exc:  # offline / 404 / corrupt / RuntimeError
            failed.append((pdb_id, enzyme_id, character, str(exc)))
    return {"completed": completed, "failed": failed, "canceled": canceled}


def characters_to_lock(failed, cast_path=None):
    """Map a bulk-download ``failed`` list to the set of character ids to lock.

    Pattern 2 (06-RESEARCH-persistence-achievements.md): on download failure,
    lock ONLY the characters whose large structures didn't download, NOT the
    whole game. Glucose's bundled small/critical structures (loaded via
    AssetManager.load_bundled, no network) keep glucose always playable --
    if glucose has no download enzymes (or they all succeeded), glucose is
    NOT in the lock set.

    ``failed`` is the ``run_bulk_download`` return's ``failed`` list of
    4-tuples ``(pdb_id, enzyme_id, character, err_msg)``. The character is
    carried in the 3rd slot (from missing_large_pdbs). If a failed entry's
    character is None/empty, fall back to resolving enzyme_id -> character
    via cast.json (the bundled manifest or explicit ``cast_path``).

    Returns a ``set`` of character ids (possibly empty -- empty = no
    characters locked = all playable, e.g. all downloads succeeded).
    """
    locked = set()
    # Preload cast.json only if we need the enzyme -> character fallback.
    cast_enzymes = None
    for entry in failed:
        pdb_id, enzyme_id, character, _err = entry
        if character:
            locked.add(character)
            continue
        # Fallback: resolve enzyme_id -> character via cast.json.
        if cast_enzymes is None:
            try:
                cast_enzymes = _load_cast(_default_cast_path(cast_path))
            except (OSError, ValueError):
                cast_enzymes = []
        for enz in cast_enzymes:
            if enz.get("id") == enzyme_id:
                ch = enz.get("character")
                if ch:
                    locked.add(ch)
                break
    return locked


def expected_download_characters(cast_path=None):
    """Return the set of characters that have >=1 real (non-PLACEHOLDER) download enzyme.

    For the lock UI: the full universe of characters that COULD be locked if
    their download fails. A character with only PLACEHOLDER download enzymes
    (Phase 6) is NOT in this set -- the prompt does not fire for placeholders,
    so there is nothing to lock. Phase 7's real entries populate this set.

    Reads cast.json (explicit ``cast_path`` or the bundled default). Returns
    a ``set`` of character ids (possibly empty for Phase 6 placeholder-only
    content).
    """
    enzymes = _load_cast(_default_cast_path(cast_path))
    out = set()
    for enz in enzymes:
        if enz.get("source") != "download":
            continue
        pdb_id = enz.get("pdb_id")
        if not pdb_id or str(pdb_id).startswith("PLACEHOLDER"):
            continue
        character = enz.get("character")
        if character:
            out.add(character)
    return out
