# c14/pymol_layer/molops.py -- Phase 3 Plan 03-03 MolOps + Phase 4 Plan 04-05
# edit/restore/protonate delegation.
#
# Translates a MolAction (the pure-data carrier from c14/story/model.py) into
# the right cmd.* call, per-action (ONE MolAction per apply() call -- the
# 02-04 per-action dispatch contract: the engine emits
# `for action in actions: self.molaction_sink(action)` and the Phase 4+
# controller calls `molops.apply(action)` per action).
#
# DESIGN -- 3-tier testability pattern (inject cmd + AssetManager + EditOps +
# ProtonationManager):
#   * cmd AND asset_manager AND editops AND protonation are INJECTED via the
#     constructor (NOT imported at module top). This keeps the module
#     importable in pure WSL python3.6 with no pymol installed, so the
#     per-action dispatch logic is unit-testable with a MockCmd/MockAssets/
#     MockEditOps/MockProtonationManager (tests/test_molops.py).
#   * The REAL cmd.* calls (hide/show/show_as/select/zoom/color/delete) are
#     verified by tools/molops_smoke.py (headless via tools/run_headless.sh
#     -- the WSL->Windows PyMOL bridge), NOT by unit tests. Unit tests prove
#     the per-op dispatch mapping; the smoke proves the real API contract +
#     the `rep` keyword "representation visible" post-condition (SC #3).
#   * The edit/restore/protonate branches DELEGATE to the injected EditOps
#     (04-01) + ProtonationManager (04-03) -- NO direct cmd.alter/h_add here
#     (the alter gate allowlist stays at edit_ops.py only). The REAL cmd.*
#     contract for these branches is verified by tools/edit_smoke.py +
#     tools/protonation_smoke.py (04-05 headless smokes).
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
# here -- the citations live in asset_manager.py). The edit/restore/protonate
# branches delegate to EditOps/ProtonationManager (no direct cmd.* call here
# either -- the citations live in edit_ops.py/protonation.py). molops.py has
# NO cmd.alter (the alter gate allowlist stays at edit_ops.py only -- SC1).
"""MolOps -- translates a MolAction into the right cmd.* call, per-action.

Inject ``cmd`` (and optional ``AssetManager`` + ``EditOps`` +
``ProtonationManager``) so the per-action dispatch logic is unit-testable in
pure WSL python3.6 with mocks (the real cmd.* calls are verified by
tools/molops_smoke.py + tools/edit_smoke.py + tools/protonation_smoke.py,
not unit tests).

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

Phase 4 implemented (delegated -- Plan 04-05):
  * edit        -> delegates to EditOps (point_mutation /
                   substrate_remove_group / substrate_add_group /
                   protonation_change per args["edit_type"]). Raises
                   RuntimeError if no EditOps was injected; ValueError for an
                   unknown edit_type.
  * protonate   -> delegates to ProtonationManager.apply_variant (per
                   args["variant_id"]). Raises RuntimeError if no
                   ProtonationManager was injected.
  * restore     -> delegates to EditOps.restore (per action.target). Raises
                   RuntimeError if no EditOps was injected.
  * unknown ops -> still raise NotImplementedError (a stray op fails loudly --
                   the boundary is preserved for genuinely unknown ops).
"""
from c14.story.model import MolAction  # MolAction is pure data (no pymol) -- OK to import here


class MolOps(object):
    """Translates MolAction -> cmd.* calls. Inject ``cmd`` (and optional
    ``AssetManager`` + ``EditOps`` + ``ProtonationManager``) so the dispatch
    logic is unit-testable in pure WSL python3.6 with mocks; the real cmd.*
    calls are verified by tools/molops_smoke.py + the 04-05 smokes (headless).

    Per-action dispatch: apply(action) takes ONE MolAction per call (the 02-04
    contract: the engine emits for action in actions: sink(action)). The
    edit/restore/protonate branches delegate to the injected EditOps /
    ProtonationManager (Phase 4 Plan 04-05 -- no more NotImplementedError for
    these 3 ops); unknown ops still raise NotImplementedError (a stray op
    fails loudly).
    """

    def __init__(self, cmd, asset_manager=None, editops=None, protonation=None):
        self._cmd = cmd
        self._assets = asset_manager    # may be None if no 'load' ops are dispatched
        self._editops = editops         # may be None if no 'edit'/'restore' ops are dispatched
        self._protonation = protonation  # may be None if no 'protonate' ops are dispatched

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
        elif op == "edit":
            # Phase 4 (04-05): delegate to EditOps. Dispatches on
            # args["edit_type"] to one of the 4 convenience methods. Raises
            # RuntimeError if no EditOps was injected (backward-compatible:
            # MolOps(cmd) with no editops still fails loudly, but with
            # RuntimeError instead of NotImplementedError). molops.py has NO
            # cmd.alter here -- the alter gate allowlist stays at edit_ops.py
            # (SC1); the sanctioned-alter path is EditOps.apply_edit, which
            # the convenience methods call internally.
            if self._editops is None:
                raise RuntimeError("molops.edit requires an EditOps (editops=None)")
            et = action.args.get("edit_type")
            if et == "point_mutation":
                self._editops.point_mutation(
                    action.target, action.args["sele"], action.args["new_resn"])
            elif et == "substrate_remove_group":
                self._editops.substrate_remove_group(
                    action.target, action.args["group_sele"])
            elif et == "substrate_add_group":
                self._editops.substrate_add_group(
                    action.target, action.args["frag_atom_sele"],
                    action.args["target_atom_sele"])
            elif et == "protonation_change":
                self._editops.protonation_change(
                    action.target, action.args["sele"], action.args["new_resn"],
                    action.args.get("h_ops"))
            else:
                raise ValueError(
                    "molops.edit: unknown edit_type {!r}".format(et))
        elif op == "protonate":
            # Phase 4 (04-05): delegate to ProtonationManager.apply_variant.
            # Raises RuntimeError if no ProtonationManager was injected.
            # ProtonationManager delegates its alter/h_add to edit_ops
            # (no direct cmd.alter here -- SC1 gate holds).
            if self._protonation is None:
                raise RuntimeError(
                    "molops.protonate requires a ProtonationManager (protonation=None)")
            self._protonation.apply_variant(
                action.target, action.args["variant_id"])
        elif op == "restore":
            # Phase 4 (04-05): delegate to EditOps.restore. Raises RuntimeError
            # if no EditOps was injected. EditOps.restore looks up the handle
            # registered by the most recent apply_edit (the EDIT-05 safety net).
            if self._editops is None:
                raise RuntimeError("molops.restore requires an EditOps (editops=None)")
            self._editops.restore(action.target)
        else:
            # Genuinely unknown op -- still fails loudly with NotImplementedError
            # (the Phase 4 boundary is preserved for ops molops doesn't know
            # about; edit/protonate/restore are now implemented above).
            raise NotImplementedError(
                "molops: unknown op {!r}".format(op))

    def apply_all(self, actions):
        """Convenience: dispatch a sequence of MolActions one at a time.

        The unit boundary is per-action ``apply``; this is a thin loop over
        it (the 02-04 contract -- one MolAction per apply() call).
        """
        for a in actions:
            self.apply(a)
