# c14/pymol_layer/molops.py -- Phase 3 Plan 03-03 MolOps.
#
# Translates a MolAction (the pure-data carrier from c14/story/model.py) into
# the right cmd.* call, per-action (ONE MolAction per apply() call -- the
# 02-04 per-action dispatch contract: the engine emits
# `for action in actions: self.molaction_sink(action)` and the Phase 4+
# controller calls `molops.apply(action)` per action).
#
# DESIGN -- 3-tier testability pattern (inject cmd + AssetManager):
#   * cmd AND asset_manager are INJECTED via the constructor (NOT imported at
#     module top). This keeps the module importable in pure WSL python3.6 with
#     no pymol installed, so the per-action dispatch logic is unit-testable
#     with a MockCmd/MockAssets (tests/test_molops.py).
#   * The REAL cmd.* calls (hide/show/show_as/select/zoom/color/delete) are
#     verified by tools/molops_smoke.py (headless via tools/run_headless.sh
#     -- the WSL->Windows PyMOL bridge), NOT by unit tests. Unit tests prove
#     the per-op dispatch mapping; the smoke proves the real API contract +
#     the `rep` keyword "representation visible" post-condition (SC #3).
#
# GATE EXCLUSION: lives in c14/pymol_layer/ which tools/check_imports.py
# excludes via SKIP_DIRS = {"pymol_layer","ui","__pycache__"} -- the domain
# tier (c14/ root) stays pure-Python (no pymol import). `from c14.story.model
# import MolAction` is ALLOWED here: MolAction is pure data (no pymol import;
# verified -- c14/story/model.py imports only stdlib), AND molops.py is in
# the gate-excluded pymol_layer/ dir. The AST gate only bans pymol/PyQt5 in
# the DOMAIN tier (c14/ excluding pymol_layer/ + ui/).
#
# PYTHON 3.6 ONLY: plain class on instance attributes, .format() strings, NO
# @dataclass / walrus (matches Phase 1/2 precedent; 3.6.9 has no dataclasses
# module).
#
# Every direct self._cmd.* call (hide/show/show_as/select/zoom/color/delete)
# carries a `# src: tmp/pymol-src/modules/pymol/<file>.py:<line> cmd.<name>`
# comment on the line directly above -- the source-citation convention
# established by Plan 03-01 (success criterion #4). Line numbers pinned to
# PyMOL 2.5.0. The `load` op delegates to AssetManager (no direct cmd.* call
# here -- the citations live in asset_manager.py).
"""MolOps -- translates a MolAction into the right cmd.* call, per-action.

Inject ``cmd`` (and an ``AssetManager``) so the per-action dispatch logic is
unit-testable in pure WSL python3.6 with a MockCmd/MockAssets (the real cmd.*
calls are verified by tools/molops_smoke.py, not unit tests).

Per-action dispatch (the 02-04 contract): ``apply(action)`` takes ONE
MolAction per call. The engine emits ``for action in actions:
self.molaction_sink(action)``; the Phase 4+ controller calls
``molops.apply(action)`` per action. ``apply_all(actions)`` is a thin
convenience loop over ``apply``.

Implemented ops (Phase 3):
  * hide_all      -> cmd.hide("everything", "all")
  * show         -> cmd.show(rep, sele)
  * show_as      -> cmd.show_as(rep, sele)   (turns off other reps atomically)
  * select_focus -> cmd.select(name, sele)
  * zoom         -> cmd.zoom(sele)
  * color        -> cmd.color(color, sele)
  * load         -> delegates to AssetManager (fetch_pubchem / fetch_pdb /
                    load_bundled per args["source"]). Raises RuntimeError if
                    no AssetManager was injected.
  * delete       -> cmd.delete(target)

Phase 4 boundary (explicit):
  * edit / protonate / restore / unknown  -> raise NotImplementedError. These
    are NOT implemented in Phase 3; the NotImplementedError makes the
    boundary explicit so a stray MolAction never silently no-ops.
"""
from c14.story.model import MolAction  # MolAction is pure data (no pymol) -- OK to import here


class MolOps(object):
    """Translates MolAction -> cmd.* calls. Inject ``cmd`` (and an AssetManager)
    so the dispatch logic is unit-testable in pure WSL python3.6 with a MockCmd;
    the real cmd.* calls are verified by tools/molops_smoke.py (headless).

    Per-action dispatch: apply(action) takes ONE MolAction per call (the 02-04
    contract: the engine emits for action in actions: sink(action)). edit/
    protonate/restore raise NotImplementedError (explicit Phase 4 boundary).
    """

    def __init__(self, cmd, asset_manager=None):
        self._cmd = cmd
        self._assets = asset_manager  # may be None if no 'load' ops are dispatched

    def apply(self, action):
        op = action.op
        if op == "hide_all":
            # src: tmp/pymol-src/modules/pymol/viewing.py:568 cmd.hide
            self._cmd.hide("everything", "all")
        elif op == "show":
            # src: tmp/pymol-src/modules/pymol/viewing.py:491 cmd.show
            self._cmd.show(action.args["rep"], action.args.get("sele", action.target))
        elif op == "show_as":
            # src: tmp/pymol-src/modules/pymol/viewing.py:528 cmd.show_as
            self._cmd.show_as(action.args["rep"], action.args.get("sele", action.target))
        elif op == "select_focus":
            # src: tmp/pymol-src/modules/pymol/selecting.py:48 cmd.select
            self._cmd.select(action.args.get("name", "focus"), action.args["sele"])
        elif op == "zoom":
            # src: tmp/pymol-src/modules/pymol/viewing.py:65 cmd.zoom
            self._cmd.zoom(action.args.get("sele", action.target or "all"))
        elif op == "color":
            # src: tmp/pymol-src/modules/pymol/viewing.py:1858 cmd.color
            self._cmd.color(action.args["color"], action.args.get("sele", action.target))
        elif op == "load":
            if self._assets is None:
                raise RuntimeError("molops.load requires an AssetManager")
            src = action.args.get("source", "bundled")
            if src == "cid":
                self._assets.fetch_pubchem(action.args["cid"], action.args.get("object", action.target))
            elif src == "pdb":
                self._assets.fetch_pdb(action.args["code"], action.args.get("object", action.target))
            else:
                self._assets.load_bundled(action.args["file"], action.args.get("object", action.target))
        elif op == "delete":
            # src: tmp/pymol-src/modules/pymol/commanding.py:496 cmd.delete
            self._cmd.delete(action.target)
        else:
            raise NotImplementedError(
                "molops: unknown op {!r} (edit/protonate/restore are Phase 4)".format(op))

    def apply_all(self, actions):
        """Convenience: dispatch a sequence of MolActions one at a time.

        The unit boundary is per-action ``apply``; this is a thin loop over
        it (the 02-04 contract -- one MolAction per apply() call).
        """
        for a in actions:
            self.apply(a)
