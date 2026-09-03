#!/usr/bin/env python
# tools/scene_capture.py -- Phase 7 Plan 07-19 scene-capture tool (user
# request 2026-08-30): read a live PyMOL session's state via READ-ONLY cmd.*
# introspection and emit a paste-ready on_enter MolAction JSON sequence
# (per-object reps/colors/labels + named selections + camera) using ONLY op
# names dispatched by rpg/pymol_layer/molops.py:140-170 -- plus ONE
# Phase-10-flagged set_view entry. molops.py is FROZEN in Phase 7; the
# set_view dispatch lands in Phase 10 (a WARNING is printed to stdout, never
# into the JSON).
#
# READ-ONLY CONTRACT: capture NEVER mutates session state -- it calls only
# get/iterate/count/get_names/get_type/get_color_*/get_view style READ APIs.
# Never set/show/color/select/zoom/delete/create/load. Every read API call
# carries a `# src: tmp/pymol-src/modules/pymol/<file>.py:<line>` citation on
# the line directly above (Phase 3 convention; line numbers pinned to PyMOL
# 2.5.0).
#
# FROZEN VOCABULARY (the molops.py:140-170 dispatch): the ONLY ops emitted
# are set_color (molops.py:160) / show_as (:148) / color (:157) / show (:145)
# / label (:164) / select_focus (:151) / zoom (:154) + the FLAGGED set_view.
# `load` and `hide_all` are REPLAY-SIDE ops (the engine's on_enter brings
# objects in and wipes the scene) -- NEVER emitted by capture. The `set` op
# (molops.py:174, per-atom settings) is OBSERVED but NOT emitted (NOT
# CAPTURED comment) per the 07-19 plan.
#
# EMISSION ORDER (deterministic):
#   1. `//` header comments (found objects; the replay-side note)
#   2. per molecule object in ALPHABETICAL order, ops grouped:
#      set_color defs -> show_as -> color -> show -> label
#        * primary rep = first ON of [sticks, cartoon, spheres] -- the probe
#          order IS the precedence (sticks > cartoon > spheres); each
#          additional ON rep becomes one `show` op layered ON TOP (the 5.4
#          ball-and-stick precedent: show_as sticks + show spheres).
#      followed by the per-object `# NOT CAPTURED` comments (multi-state,
#      mixed colors/labels, per-atom settings)
#   3. named selections (alphabetical): select_focus IF the defining
#      expression is recoverable, else a `# NOT CAPTURED` comment
#   4. zoom -- ONLY when >=1 select_focus was emitted (sele = that selection
#      name); else a `# NOT CAPTURED` comment (the exact camera in set_view
#      preserves the framing)
#   5. exactly ONE {"op":"set_view","args":{"view":[18 floats]}} entry, LAST.
#
# ANYTHING observed-but-unmappable becomes a `# NOT CAPTURED: <description>`
# comment line in the returned list -- nothing silently dropped, no invented
# ops. Documented capture scope: reps are probed for the game's three reps
# only (sticks/cartoon/spheres -- the frozen vocabulary's representational
# surface); mixed per-atom rep SCOPING within an object is likewise beyond
# the object-level model (NOT CAPTURED if it would round-trip wrongly is not
# detectable here -- the emitter captures object-level rep state, which is
# what the 5.4 scene templates author).
#
# EMPIRICAL PIN (tmp/07-19-probe.py, real Windows PyMOL 2.5.0 headless via
# run-conda-pymol.bat -cq, SMOKE_RESULT: PASS):
#   * OBS1: cmd.get_type(<named selection>) returns the bare type tag
#     'selection' -- the DEFINING EXPRESSION is not recoverable via it (and
#     the session entry stores resolved atom indices, not the expression --
#     OBS4). The 07-19 plan's "recoverable -> emit select_focus(name, expr)"
#     path is therefore UNREACHABLE on this build: the NOT-CAPTURED fallback
#     is the pinned branch, NO zoom op is emitted, and the exact camera rides
#     home in the single flagged set_view entry.
#   * OBS5/OBS6: cmd.get_color_index("hero_cyan") == -1 in a fresh session
#     (undefined), so the 5-name palette probe cannot collide with a custom
#     session-allocated index; standard palette names resolve normally.
#   * OBS12/OBS14: per-atom sphere_scale is readable via iterate
#     `s.sphere_scale` (setting.py:351 docstring documents the `s.` atom-
#     setting namespace); the global baseline is readable via cmd.get.
#
# set_color NAMING (deterministic, documented): the rgb branch emits
# {"op":"set_color","target":null,"args":{"name":"captured_<idx>",
# "rgb":[r,g,b]}} where <idx> is the capture session's atom color index. The
# name is arbitrary-but-unique in the REPLAY session (indices are session-
# allocated -- 05.4-RESEARCH-api Pitfall 4); set_color defines it
# idempotently before the paired `color` op consumes it, so the round-trip
# is exact regardless of the replay session's own index allocation.
#
# RETURNS: capture_scene(cmd) -> a JSON-serializable list preserving the
# EXACT emission order; entries are MolAction-shaped dicts ({op,target,args}
# per 05.4-CONVENTION.md:370-380) or comment strings ("// ..." headers and
# "# NOT CAPTURED: ..." annotations). main() renders the `//` header lines,
# then the dicts as ONE paste-ready JSON array, then the NOT-CAPTURED lines
# (jsonc comments cannot live inside a JSON array, so the render groups the
# annotations around it; the returned list keeps strict emission order).
#
# CLI: `run tools/scene_capture.py` from a PyMOL session (or plugin console)
# prints the render; `--out <path>` (best-effort argv parse) also writes the
# file. Imports: pymol + json/sys ONLY -- no rpg.* imports (standalone tool;
# the headless smoke imports this module directly).
#
# PYTHON 3.6 ONLY (repo precedent): .format() strings, no f-strings, no
# dataclasses. Passes `python3.6 -m py_compile`.

import sys
import json

import pymol
from pymol import cmd

# The named-palette probe (05.4-CONVENTION.md section 2.3 -- the game's
# palette): a uniform atom color matching one of these emits the `color` op
# with the NAME; anything else emits the set_color+color rgb pair.
PALETTE = ("hero_cyan", "gray", "green", "magenta", "orange")

# The ONLY ops this emitter may emit (molops.py:140-170 dispatch vocabulary
# + the one Phase-10-flagged set_view). The smoke's no-invented-ops
# invariant asserts every emitted op lands in this set.
EMITTED_OPS = frozenset((
    "set_color", "show_as", "color", "show", "label",
    "select_focus", "zoom", "set_view"))

# The rep probe order IS the primary-rep precedence (first ON wins):
# sticks > cartoon > spheres (the 5.4 game reps; surface/mesh/etc are outside
# the game's representational vocabulary).
REP_PROBES = ("sticks", "cartoon", "spheres")


# ---------------------------------------------------------------------------
# read-only probes (each returns plain data; each cmd.* call carries its src
# citation on the line directly above)
# ---------------------------------------------------------------------------

def _atom_color_indices(cmd, obj):
    # type: (object, str) -> list
    """All atom color indices of `obj`, in atom order (READ-ONLY)."""
    out = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
    # (collector `cidx` deliberately NON-colliding -- a collector named
    # `color` would shadow the atom property and raise AttributeError,
    # 05.4-RESEARCH-api section F Pitfall 1).
    cmd.iterate(obj, "cidx.append(color)", space={"cidx": out})
    return out


def _atom_labels(cmd, obj):
    # type: (object, str) -> list
    """All atom label texts of `obj`, in atom order (READ-ONLY; unlabeled
    atoms iterate as '')."""
    out = []
    # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
    # (collector `lbls` NON-colliding with the atom property `label`.)
    cmd.iterate(obj, "lbls.append(label)", space={"lbls": out})
    return out


def _atom_sphere_scales(cmd, obj):
    # type: (object, str) -> list
    """Per-atom sphere_scale values, or None if the s.<name> probe is
    unavailable (defensive)."""
    out = []
    try:
        # src: tmp/pymol-src/modules/pymol/editing.py:1490 cmd.iterate
        # (`s.sphere_scale` reads the per-atom setting; setting.py:351's
        # docstring: "Atom level settings can be queried with iterate".)
        cmd.iterate(obj, "scs.append(s.sphere_scale)", space={"scs": out})
        return out
    except Exception:
        return None


def _global_sphere_scale(cmd):
    # type: (object) -> float
    """Global sphere_scale baseline for the per-atom-override check."""
    try:
        # src: tmp/pymol-src/modules/pymol/setting.py:351 cmd.get
        # (EMPIRICAL: returns '1.00000' in a fresh session -- probe OBS13.)
        return float(cmd.get("sphere_scale"))
    except (TypeError, ValueError):
        return 1.0  # PyMOL's documented sphere_scale default


def _palette_color(cmd, idx):
    # type: (object, int) -> str
    """Return the PALETTE name whose color index equals `idx`, else None."""
    for pal in PALETTE:
        # src: tmp/pymol-src/modules/pymol/querying.py:851 cmd.get_color_index
        # (returns -1 for undefined names; EMPIRICAL probe OBS5/OBS6:
        # hero_cyan == -1 in a fresh session -- no collision possible).
        if cmd.get_color_index(pal) == idx:
            return pal
    return None


def _selection_expression(cmd, sel):
    # type: (object, str) -> str
    """Attempt to recover a named selection's DEFINING EXPRESSION (READ-ONLY).

    07-19 plan: recovery is attempted via cmd.get_type. EMPIRICAL PIN
    (tmp/07-19-probe.py OBS1, PyMOL 2.5.0 headless): get_type returns the
    bare type tag 'selection' -- never an expression -- so this helper
    returns None on this build and the caller emits the NOT-CAPTURED
    fallback (no invented expression, no silent drop). The helper is the
    single honest seam to extend if a future PyMOL read API exposes the
    defining expression.
    """
    # src: tmp/pymol-src/modules/pymol/querying.py:1199 cmd.get_type
    tag = cmd.get_type(sel)
    if tag == "selection":
        return None  # a type tag, NOT the expression (probe OBS1)
    return None      # any other tag is not a named-selection expression either


# ---------------------------------------------------------------------------
# the emitter
# ---------------------------------------------------------------------------

def capture_scene(cmd):
    # type: (object) -> list
    """Read-only capture of the live session -> paste-ready MolAction list.

    Returns a list in EXACT emission order; entries are MolAction-shaped
    dicts ({op, target, args}) or comment strings ("// ..." / "# NOT
    CAPTURED: ..."). Emits ONLY the molops.py:140-170 dispatch vocabulary
    plus the single Phase-10-flagged set_view entry (with a stdout WARNING).
    Never mutates session state.
    """
    entries = []

    # ---- objects: molecules only, alphabetical ---------------------------
    # src: tmp/pymol-src/modules/pymol/querying.py:1148 cmd.get_names
    obj_names = sorted(cmd.get_names("objects"))
    molecules = []
    for name in obj_names:
        # src: tmp/pymol-src/modules/pymol/querying.py:1199 cmd.get_type
        otype = cmd.get_type(name)
        if otype == "object:molecule":
            molecules.append(name)
        else:
            entries.append(
                "# NOT CAPTURED: non-molecule object \"{0}\" (type={1})"
                "".format(name, otype))

    # ---- header comments (the jsonc preamble) ----------------------------
    entries.append(
        "// scene-capture: found {0} molecule object(s): {1}"
        "".format(len(molecules),
                  ", ".join(molecules) if molecules else "(none)"))
    entries.append(
        "// note: load/hide_all are REPLAY-SIDE ops -- the engine's on_enter"
        " brings objects in and wipes the scene; capture NEVER emits them.")

    # ---- per-object ops (alphabetical) ------------------------------------
    for obj in molecules:
        # multi-state guard (state-scoped replay is unrepresentable)
        # src: tmp/pymol-src/modules/pymol/querying.py:703 cmd.count_states
        nstates = cmd.count_states(obj)
        if nstates > 1:
            entries.append(
                "# NOT CAPTURED: multi-state object \"{0}\" ({1} states --"
                " state-scoped replay is not representable in the frozen"
                " vocabulary)".format(obj, nstates))
            continue

        # -- probe the scene facts (all READ-ONLY) --------------------------
        # reps ON (probe order == precedence sticks > cartoon > spheres)
        reps_on = []
        for rep in REP_PROBES:
            # src: tmp/pymol-src/modules/pymol/querying.py:1412 count_atoms
            if cmd.count_atoms("{0} and rep {1}".format(obj, rep)) > 0:
                reps_on.append(rep)
        # colors
        color_ops = []
        color_note = None
        cidx = _atom_color_indices(cmd, obj)
        distinct = set(cidx)
        if len(distinct) == 1:
            idx = cidx[0]
            pal = _palette_color(cmd, idx)
            if pal is not None:
                # palette hit -> the `color` op with the NAMED color
                color_ops.append(
                    {"op": "color", "target": obj,
                     "args": {"color": pal}})
            else:
                # rgb branch -> set_color definition + color op consuming it
                # src: tmp/pymol-src/modules/pymol/querying.py:825
                # cmd.get_color_tuple (EMPIRICAL: returns (r, g, b) floats
                # in 0.0-1.0 -- probe OBS7).
                rgb = cmd.get_color_tuple(idx)
                cname = "captured_{0}".format(idx)
                color_ops.append(
                    {"op": "set_color", "target": None,
                     "args": {"name": cname,
                              "rgb": [float(v) for v in rgb]}})
                color_ops.append(
                    {"op": "color", "target": obj,
                     "args": {"color": cname}})
        elif len(distinct) > 1:
            color_note = (
                "# NOT CAPTURED: mixed atom colors on \"{0}\" ({1} distinct"
                " color indices -- per-atom coloring is beyond the"
                " object-level model)".format(obj, len(distinct)))
        # labels
        label_ops = []
        label_note = None
        lbls = _atom_labels(cmd, obj)
        nonempty = [t for t in lbls if t]
        if lbls and len(nonempty) == len(lbls) and len(set(nonempty)) == 1:
            # uniform non-empty label -> ONE label op with the bare-string
            # text (molops.py:164-170 wraps it as the quoted expr)
            label_ops.append(
                {"op": "label", "target": obj,
                 "args": {"text": nonempty[0]}})
        elif nonempty:
            label_note = (
                "# NOT CAPTURED: mixed/partial labels on \"{0}\" ({1} of {2}"
                " atoms labeled, non-uniform)".format(
                    obj, len(nonempty), len(lbls)))
        # per-atom settings (the `set` op is excluded from capture per plan)
        setting_notes = []
        scales = _atom_sphere_scales(cmd, obj)
        if scales:
            base = _global_sphere_scale(cmd)
            if any(abs(s - base) > 1e-6 for s in scales):
                setting_notes.append(
                    "# NOT CAPTURED: per-atom sphere_scale override on"
                    " \"{0}\" (atom values {1} vs global {2}; the frozen"
                    " vocabulary's `set` op is excluded from capture per the"
                    " 07-19 plan)".format(
                        obj,
                        sorted(set(round(s, 6) for s in scales)),
                        base))

        # -- emit in the PINNED group order:
        #    set_color defs -> show_as -> color -> show -> label -----------
        for op_dict in color_ops:
            if op_dict["op"] == "set_color":
                entries.append(op_dict)
        if reps_on:
            # primary rep = first ON (probe order IS the precedence)
            entries.append(
                {"op": "show_as", "target": obj,
                 "args": {"rep": reps_on[0]}})
        for op_dict in color_ops:
            if op_dict["op"] == "color":
                entries.append(op_dict)
        for rep in reps_on[1:]:
            # additional ON reps layer ON TOP (`show` turns ON only -- the
            # 5.4 ball-and-stick precedent: show_as sticks + show spheres)
            entries.append(
                {"op": "show", "target": obj, "args": {"rep": rep}})
        for op_dict in label_ops:
            entries.append(op_dict)
        # per-object NOT-CAPTURED comments ride right after the object's ops
        if color_note:
            entries.append(color_note)
        if label_note:
            entries.append(label_note)
        for note in setting_notes:
            entries.append(note)

    # ---- named selections --------------------------------------------------
    # src: tmp/pymol-src/modules/pymol/querying.py:1148 cmd.get_names
    sel_names = sorted(cmd.get_names("selections"))
    captured_focus = None
    for sel in sel_names:
        expr = _selection_expression(cmd, sel)
        if expr is not None:
            # the plan's recoverable path (UNREACHABLE on PyMOL 2.5.0 -- see
            # _selection_expression / the EMPIRICAL PIN in the header)
            entries.append(
                {"op": "select_focus", "target": None,
                 "args": {"name": sel, "sele": expr}})
            captured_focus = sel
        else:
            try:
                # src: tmp/pymol-src/modules/pymol/querying.py:1512
                # cmd.get_selection_state (comment-only annotation)
                sel_state = cmd.get_selection_state(sel)
            except Exception:
                # raises when the selection spans objects in different
                # states (querying.py:1512 docstring) -- annotate "?" then
                sel_state = "?"
            entries.append(
                "# NOT CAPTURED: named selection \"{0}\" (defining"
                " expression not recoverable via get_type --"
                " querying.py:1199 returns the type tag 'selection' only;"
                " selection state={1})".format(sel, sel_state))

    # ---- zoom (ONLY when a select_focus was emitted) ------------------------
    if captured_focus is not None:
        entries.append(
            {"op": "zoom", "target": None,
             "args": {"sele": captured_focus}})
    else:
        entries.append(
            "# NOT CAPTURED: zoom (no recoverable named selection to frame;"
            " the exact camera in the set_view entry below preserves the"
            " framing)")

    # ---- camera: exactly ONE set_view entry, LAST (Phase-10 FLAGGED) --------
    # src: tmp/pymol-src/modules/pymol/viewing.py:605 cmd.get_view
    # (EMPIRICAL: returns 18 floats -- probe OBS8.)
    view = [float(v) for v in cmd.get_view()]
    entries.append(
        {"op": "set_view", "target": None, "args": {"view": view}})
    print("WARNING: scene_capture emitted a set_view op -- its dispatch"
          " lands in Phase 10 (molops.py is FROZEN in Phase 7); replaying"
          " this capture raises NotImplementedError until then.")
    return entries


# ---------------------------------------------------------------------------
# CLI render
# ---------------------------------------------------------------------------

def _out_path_from_argv(argv):
    # type: (list) -> str
    """Best-effort `--out <path>` extraction (PyMOL `run` may not forward
    argv; without it the render prints to the console instead)."""
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            return argv[i + 1]
    return None


def render_capture(entries):
    # type: (list) -> str
    """Render the capture as paste-ready jsonc text.

    The `//` header comments first, then the MolAction dicts as ONE JSON
    array (the paste-ready on_enter value), then the `# NOT CAPTURED`
    comment lines. (capture_scene's RETURNED LIST keeps the exact emission
    order; this render groups the annotations around the array because
    jsonc comments are not valid inside a JSON array.)
    """
    headers = [e for e in entries
               if isinstance(e, str) and e.startswith("//")]
    notes = [e for e in entries
             if isinstance(e, str) and not e.startswith("//")]
    ops = [e for e in entries if isinstance(e, dict)]
    lines = list(headers)
    lines.append(json.dumps(ops, indent=2))
    lines.extend(notes)
    return "\n".join(lines) + "\n"


def main():
    # type: () -> None
    """CLI entry (run-friendly no-arg path prints to the console)."""
    entries = capture_scene(cmd)
    text = render_capture(entries)
    out_path = _out_path_from_argv(sys.argv)
    if out_path:
        with open(out_path, "w") as fh:
            fh.write(text)
        print("scene-capture: wrote {0} ops -> {1}".format(
            sum(1 for e in entries if isinstance(e, dict)), out_path))
    else:
        print(text, end="")


if __name__ in ("__main__", "pymol"):
    # PyMOL's `run` executes scripts in the pymol package's global namespace
    # (parsing.py:424 cmd.run namespace='global' -> run_file(path, ns_pymol,
    # ns_pymol)), where __name__ == 'pymol' -- NOT '__main__'. Fire main()
    # for BOTH entry forms, while a plain `import scene_capture` (the smoke)
    # stays import-side-effect-free (__name__ == 'scene_capture').
    main()
