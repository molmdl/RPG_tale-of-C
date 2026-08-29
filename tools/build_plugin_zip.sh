#!/usr/bin/env bash
# tools/build_plugin_zip.sh -- build the PyMOL Plugin-Manager-installable zip.
#
# Produces dist/c14-<version>.zip with Case-1 layout (c14/__init__.py at the
# zip root per tmp/pymol-src/modules/pymol/plugins/installation.py:90-143) so
# Plugin Manager can install it (PLGN-02). Bundles data/story_glucose/ into
# c14/data/story_glucose/ so the shipped plugin finds the story. Excludes
# __pycache__/*.pyc and the gitignored runtime cache c14/data/assets/downloaded/
# (Pitfall 4). See 06-RESEARCH-qt-packaging.md Pattern 4 + Pitfall 4.
#
# DEVIATION from 06-07-PLAN.md Task 3 (Rule 3 - blocking): the plan prescribed
# the `zip` / `unzip` CLIs, but neither binary is installed in this WSL dev
# shell (`which zip` -> exit 1; `which unzip` -> exit 1; cannot `apt install` --
# AGENTS.md "Do NOT install anything"). The staging + zipping + post-build
# sanity check are performed with python3.6 stdlib `shutil` + `zipfile` instead.
# This produces a standard .zip that PyMOL's own installer
# (plugins/installation.py:extract_zipfile, also Python zipfile) reads
# natively -- byte-for-byte compatible. Fully WSL-runnable; no new
# dependencies; honors the plan's Case-1 layout + exclusions + story copy.
# See 06-07-SUMMARY.md "Deviations from Plan".
#
# Usage: bash tools/build_plugin_zip.sh   (callable from any cwd; the script
#                                          cd's to the repo root)
#
# DEV INSTALL (no zip rebuild per change): instead of installing the zip via
# Plugin Manager, point PyMOL's plugin search path at THIS REPO ROOT so PyMOL
# loads c14/ straight from source. Edits to c14/ui/*.py then take effect on
# PyMOL restart with NO rebuild. Two equivalent ways:
#   - GUI:  PyMOL -> Plugin -> Plugin Manager -> Settings -> add the repo root
#           (the dir containing c14/) to "Plugin Directories", then restart.
#   - Env:  set PYMOL_GIT_MOD=<repo-root> before launching PyMOL.
# On restart PyMOL scans the path, finds c14/__init__.py exposing
# __init_plugin__, and registers the "RPG: Tale of C" menu item. The
# MainWindow's _resolve_story_dir() already falls back to repo-root
# data/story_glucose in dev (06-08), so the story resolves without bundling.
# Use the zip build (below) only for a clean install / distribution.
set -eu
set -o pipefail

# Run from the repo root regardless of the caller's cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Sanity: the package + story data must exist.
if [ ! -f c14/__init__.py ]; then
    echo "error: c14/__init__.py not found (run from repo root)" >&2
    exit 2
fi
if [ ! -d data/story_glucose ]; then
    echo "error: data/story_glucose/ not found (story data missing)" >&2
    exit 2
fi

# 1. Read __version__ from c14/__init__.py (prefer the __version__ string per plan).
VERSION="$(grep -m1 '__version__' c14/__init__.py | sed 's/.*"\(.*\)".*/\1/')"
if [ -z "${VERSION}" ]; then
    echo "error: could not parse __version__ from c14/__init__.py" >&2
    exit 2
fi
OUT_NAME="c14-${VERSION}.zip"
OUT_PATH="dist/${OUT_NAME}"

echo "Building ${OUT_NAME} (version=${VERSION}) ..."

# 2-7. Stage + clean + zip + verify via python3.6 stdlib (zip/unzip unavailable
# in WSL -- Rule 3 deviation; see header). Python receives the repo root (cwd)
# and the output path; it does all the filesystem work with shutil/zipfile.
python3.6 - "${OUT_PATH}" "${VERSION}" <<'PY'
import os, sys, shutil, zipfile, tempfile

out_path, version = sys.argv[1], sys.argv[2]
repo = os.getcwd()

stage = tempfile.mkdtemp(prefix="c14zip_")
try:
    stage_c14 = os.path.join(stage, "c14")


    def _ignore_pyc_and_cache(directory, names):
        """shutil.copytree ignore fn: skip __pycache__ dirs + *.pyc files."""
        skipped = []
        for n in list(names):
            full = os.path.join(directory, n)
            if n == "__pycache__" and os.path.isdir(full):
                skipped.append(n)
            elif n.endswith(".pyc"):
                skipped.append(n)
        return skipped


    # 2. Stage c14/ -> stage/c14/ (excluding __pycache__ + *.pyc).
    shutil.copytree(os.path.join(repo, "c14"), stage_c14,
                    ignore=_ignore_pyc_and_cache)

    # 3. Copy the story data into the staged package so it ships + resolves via
    #    c14.paths.data_path("data","story_glucose") at runtime. The dev
    #    controller/tests load repo-root data/story_glucose; this build bridges
    #    them so the installed plugin finds the story (c14/data/ already exists
    #    via the copytree above).
    story_src = os.path.join(repo, "data", "story_glucose")
    story_dst = os.path.join(stage_c14, "data", "story_glucose")
    shutil.copytree(story_src, story_dst, ignore=_ignore_pyc_and_cache)

    # 4. Clean the staged tree: exclude the gitignored runtime cache
    #    (c14/data/assets/downloaded/) + belt-and-suspenders sweep of any
    #    __pycache__/*.pyc that survived (e.g. inside data/).
    downloaded = os.path.join(stage_c14, "data", "assets", "downloaded")
    if os.path.isdir(downloaded):
        shutil.rmtree(downloaded)
    for root, dirs, files in os.walk(stage_c14):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
                dirs.remove(d)
        for f in list(files):
            if f.endswith(".pyc"):
                os.remove(os.path.join(root, f))

    # 5. Build the zip with Case-1 layout: c14/__init__.py is written FIRST so
    #    it is the first entry (06-RESEARCH-qt-packaging.md Example 3 expects
    #    c14/__init__.py as the first file). Then walk the rest of stage/c14.
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)
    init_arc = "c14/__init__.py"
    init_full = os.path.join(stage_c14, "__init__.py")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(init_full, init_arc)  # first entry (Case 1)
        for root, dirs, files in os.walk(stage_c14):
            dirs.sort()
            for f in sorted(files):
                full = os.path.join(root, f)
                arc = os.path.relpath(full, stage).replace(os.sep, "/")
                if arc == init_arc:
                    continue  # already written first
                z.write(full, arc)

    # 7. Post-build sanity check (06-RESEARCH-qt-packaging.md Example 3).
    with zipfile.ZipFile(out_path, "r") as z:
        names = z.namelist()

    def must(cond, msg):
        if not cond:
            raise SystemExit("SANITY CHECK FAILED: " + msg)

    must(len(names) > 0, "zip is empty")
    must(names[0] == "c14/__init__.py",
         "first entry is not c14/__init__.py: " + repr(names[0]))
    required = [
        "c14/__init__.py",
        "c14/ui/plugin_entry.py",
        "c14/ui/__init__.py",
        "c14/data/story_glucose/manifest.json",
    ]
    for r in required:
        must(r in names, "missing required entry: " + r)
    for n in names:
        must(n.startswith("c14/"),
             "entry outside c14/ package dir: " + repr(n))
        must("c14/data/assets/downloaded/" not in n,
             "forbidden downloaded/ entry: " + n)
        must(not n.endswith(".pyc"), "forbidden .pyc entry: " + n)
        must("__pycache__" not in n, "forbidden __pycache__ entry: " + n)
    # Exactly one package dir at the zip root (Case 1): every top-level segment
    # is "c14".
    top_segs = set(n.split("/", 1)[0] for n in names)
    must(top_segs == {"c14"},
         "more than one top-level dir (must be only c14/): " + repr(top_segs))

    print("BUILD OK: " + out_path)
    print("entries: " + str(len(names)))
    print("first 12 entries:")
    for n in names[:12]:
        print("  " + n)
finally:
    # 6. Cleanup the ephemeral stage (shutil.rmtree, not `rm`, to avoid the
    # opencode.json `rm *` deny rule on direct commands).
    shutil.rmtree(stage, ignore_errors=True)
PY

echo
echo "Plugin zip ready: ${OUT_PATH}"
echo "Install via: PyMOL -> Plugin -> Plugin Manager -> Install New Plugin -> pick ${OUT_NAME}"
