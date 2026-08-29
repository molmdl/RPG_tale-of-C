"""c14/ui/bulk_download_dialog.py -- BulkDownloadDialog (CAST-04).

Gate-EXEMPT: ``c14/ui/`` is in ``tools/check_imports.py`` SKIP_DIRS, so this
module MAY import ``pymol.Qt``. Importing it in pure WSL python3.6 FAILS (no
Qt installed) -- that is EXPECTED; only ``python3.6 -m py_compile`` is
WSL-verifiable here. The functional dialog (per-file progress bar advances,
cancel button responds between fetches, retry re-runs, offline lock applies
only to affected characters) is human-verify in plan 06-14.

The dialog WRAPS the Qt-free runner ``c14/ui/bulk_download.py`` (run_bulk_download).
The runner does the per-file fetch loop with on_progress / on_cancel_check
callbacks; the dialog's callback implementations pump the Qt event loop via
``QApplication.processEvents()`` BETWEEN fetches so the cancel button +
label stay live. ``cmd.fetch(async_=0)`` is SYNC + blocking with NO per-byte
progress callback (importing.py:1386-1393, 1215-1245), so the UX is PER-FILE
progress (NOT per-byte) -- this is CORRECT, not a bug
(06-RESEARCH-persistence-achievements.md Pitfall 1).

Cancel aborts the LOOP after the current fetch finishes (NOT a mid-fetch
interrupt -- you cannot interrupt a blocking ``file_read``; Pitfall 7).
The Cancel button label says "Cancel (after current file)" to set that
expectation honestly. Retry re-runs the loop; ``cmd.fetch`` skips already-
downloaded files (importing.py:1211-1213) + the runner's ``missing_large_pdbs``
already filters them, so retry only re-fetches the still-missing ones (free
idempotent cache).

Offline fallback (Pattern 2): on failure, the helper
``maybe_run_bulk_download`` maps the ``failed`` entries to a set of
character ids via ``characters_to_lock`` and asks the controller to lock
ONLY those characters on the start screen. Glucose's bundled small/critical
structures (loaded via ``AssetManager.load_bundled``, no network) keep
glucose always playable -- SC4 "locks only affected characters".

Python 3.6 compatible: no f-strings (uses ``.format()``).
"""
from pymol.Qt import QtCore, QtWidgets

from c14.ui.bulk_download import (
    characters_to_lock,
    missing_large_pdbs,
    run_bulk_download,
)


class BulkDownloadDialog(QtWidgets.QProgressDialog):
    """Modal per-file bulk-download progress dialog (CAST-04).

    Wraps the Qt-free ``run_bulk_download`` runner. The runner loops
    ``AssetManager.fetch_pdb`` once per missing code; this dialog's
    ``on_progress`` / ``on_cancel_check`` callbacks update the label + value
    bar and pump ``QApplication.processEvents()`` BETWEEN fetches (NOT
    during -- ``cmd.fetch(async_=0)`` blocks; see 06-RESEARCH-persistence-
    achievements.md Pitfall 1) so the cancel button stays responsive.

    Cancel aborts the LOOP after the current fetch (Pitfall 7 -- you cannot
    interrupt a blocking ``file_read``); the button label says
    "Cancel (after current file)" to set that expectation. The loop's
    ``on_cancel_check`` reads ``self._canceled`` (set by the ``canceled``
    signal) at the START of each iteration, before the next fetch.

    The dialog is modal (``QtCore.Qt.ApplicationModal``) -- it blocks the
    main window during download. ``self.show()`` is called at the start of
    ``run()`` so the dialog is visible immediately (QProgressDialog's default
    auto-show has a multi-second delay that would hide the bar during a fast
    fetch loop; explicit show is the robust choice).
    """

    def __init__(self, cmd, missing_codes, parent=None):
        # QProgressDialog(labelText, cancelButtonText, minimum, maximum, parent).
        # maximum = len(missing_codes) -> the bar advances per file (0..N).
        super(BulkDownloadDialog, self).__init__(
            "Downloading structures...",
            "Cancel (after current file)",
            0,
            len(missing_codes),
            parent,
        )
        self.setWindowTitle("RPG: Tale of C — One-time Structure Download")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self._cmd = cmd
        self._missing = missing_codes
        self._canceled = False
        # The canceled signal fires when the cancel button is clicked. We do
        # NOT abort mid-fetch (impossible -- cmd.fetch blocks); we set a flag
        # the loop's on_cancel_check reads BETWEEN fetches (Pitfall 7).
        self.canceled.connect(self._on_cancel)

    def _on_cancel(self):
        # Set the flag; the loop checks it at the start of the NEXT iteration
        # (between fetches), not mid-fetch. The button label tells the user
        # "after current file" so the wait is expected.
        self._canceled = True

    def run(self):
        """Run the per-file fetch loop; return {completed, failed, canceled}.

        Shows the dialog, delegates to the Qt-free ``run_bulk_download`` runner
        with two callbacks:
          * ``on_progress(i, total, pdb_id)`` -- updates the label ("Downloading
            <pdb_id> (i+1 of total)...") + the value bar, then pumps
            ``QApplication.processEvents()`` so the cancel button + label
            repaint BETWEEN fetches (NOT during -- cmd.fetch blocks).
          * ``on_cancel_check()`` -- pumps ``processEvents()`` (so the cancel
            click is observed) then returns ``self._canceled``. The runner
            breaks the loop if this returns True (Pitfall 7: between fetches).

        Returns the runner's result dict ``{"completed", "failed", "canceled"}``.
        The helper ``maybe_run_bulk_download`` maps ``failed`` to per-character
        locks (Pattern 2) and handles the retry-on-cancel prompt.
        """
        # Explicit show -- QProgressDialog's auto-show delay would hide the
        # bar during a fast fetch loop. Show + processEvents so the dialog is
        # painted before the first fetch (which blocks the event loop).
        self.show()
        QtWidgets.QApplication.processEvents()

        def on_progress(i, total, pdb_id):
            self.setLabelText("Downloading {0} ({1} of {2})...".format(
                pdb_id, i + 1, total))
            self.setValue(i)
            # Pump the event loop BETWEEN fetches so the label + cancel button
            # repaint. cmd.fetch (inside the runner) blocks the loop DURING
            # the fetch -- per-byte progress is impossible (Pitfall 1); per-
            # file progress between fetches is the correct UX.
            QtWidgets.QApplication.processEvents()

        def on_cancel_check():
            # Pump first so the cancel click (a queued signal) is processed
            # before we read the flag, then return the flag. The runner checks
            # this at the START of each iteration (between fetches).
            QtWidgets.QApplication.processEvents()
            return self._canceled

        result = run_bulk_download(
            self._cmd, self._missing,
            on_progress=on_progress, on_cancel_check=on_cancel_check,
        )
        # Advance to 100% (the runner completed or canceled; either way the
        # bar should read full so the dialog dismisses cleanly).
        self.setValue(len(self._missing))
        return result


def _apply_lock(controller, locked_characters, reason=""):
    """Tell the controller to lock characters on the start screen (Pattern 2).

    Duck-typed: if the controller exposes a ``lock_characters`` method, call
    it with the locked set + a human-readable reason. Otherwise no-op (the
    caller inspects the returned ``locked_characters`` set from
    ``maybe_run_bulk_download`` and applies the lock itself).

    This keeps the helper decoupled from the controller's exact API (the
    MainWindow/controller is built in plan 06-08; the contract is finalized
    there). If 06-08 names the method differently, update this helper -- it
    is the single point of contact.
    """
    if controller is not None and locked_characters and \
            hasattr(controller, "lock_characters"):
        controller.lock_characters(locked_characters, reason=reason)


def maybe_run_bulk_download(controller, cmd, parent=None):
    """One-time bulk-download prompt (CAST-04) -- the MainWindow entry point.

    Called by the MainWindow's ``_new_game`` (plan 06-08) BEFORE starting the
    game. Flow:
      1. Compute missing large PDBs via ``missing_large_pdbs(cmd)``. If none,
         return immediately (no prompt -- the game starts instantly; SC4:
         small/critical structures are bundled).
      2. Open ``BulkDownloadDialog`` and run the per-file fetch loop.
      3. On ``failed`` (non-empty): map ``failed`` -> character ids via
         ``characters_to_lock`` (Pattern 2) and ask the controller to lock
         ONLY those characters on the start screen. Glucose's bundled
         structures keep it always playable.
      4. On ``canceled``: ask "Retry?" via QMessageBox. If yes, recompute the
         still-missing list (some may have downloaded before the cancel) and
         re-run (free idempotent cache -- cmd.fetch skips already-downloaded
         files). If no, lock the characters whose structures are STILL
         missing (SC4 -- locks only affected characters).

    Returns a dict ``{"ran": bool, "failed": list, "canceled": bool,
    "locked_characters": set}``. ``ran`` is False if no prompt was shown
    (nothing missing); True otherwise. The MainWindow may use ``ran`` to
    decide whether to surface a "downloads complete" toast.
    """
    missing = missing_large_pdbs(cmd)
    if not missing:
        # Nothing missing -- no prompt. The game starts instantly (SC4:
        # small/critical structures bundled; large structures already on
        # disk from a prior session).
        return {"ran": False, "failed": [], "canceled": False,
                "locked_characters": set()}

    while True:
        dialog = BulkDownloadDialog(cmd, missing, parent=parent)
        result = dialog.run()

        if result["canceled"]:
            # Ask Retry?. The user canceled mid-download; some structures may
            # be missing. Re-run only re-fetches the still-missing (free
            # idempotent cache).
            retry = QtWidgets.QMessageBox.question(
                parent,
                "RPG: Tale of C — Download Canceled",
                "Download was canceled. Some structures may not be available.\n"
                "Retry?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes,
            )
            if retry == QtWidgets.QMessageBox.Yes:
                # Recompute the still-missing list (some may have downloaded
                # before the cancel). If everything made it, nothing left to do.
                missing = missing_large_pdbs(cmd)
                if not missing:
                    return {"ran": True, "failed": [], "canceled": True,
                            "locked_characters": set()}
                continue  # re-run with the still-missing list
            # Declined retry: proceed with the game, but lock the characters
            # whose structures are STILL missing (SC4 -- only affected
            # characters; glucose stays playable if its bundled structures
            # are intact). The still-missing entries are treated as failed
            # for lock purposes (reason "canceled").
            still_missing = missing_large_pdbs(cmd)
            lock_entries = list(result["failed"])
            for entry in still_missing:
                pdb_id, _obj, enzyme_id, character = entry
                lock_entries.append((pdb_id, enzyme_id, character, "canceled"))
            locked = characters_to_lock(lock_entries)
            _apply_lock(controller, locked,
                        reason="structure unavailable (download canceled)")
            return {"ran": True, "failed": result["failed"], "canceled": True,
                    "locked_characters": locked}

        # Completed (not canceled).
        if result["failed"]:
            # Pattern 2: lock only the characters whose structures failed to
            # download. Glucose's bundled structures keep it always playable.
            locked = characters_to_lock(result["failed"])
            _apply_lock(controller, locked,
                        reason="structure unavailable (download failed)")
        else:
            locked = set()
        return {"ran": True, "failed": result["failed"], "canceled": False,
                "locked_characters": locked}
