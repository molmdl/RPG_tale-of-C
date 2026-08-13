# Source: standard Python package-data pattern; corroborated by
# .planning/research/PITFALLS.md Pitfall 1 ("resolve every path via
# os.path.dirname(__file__) joined to the data dir").
# pathlib.Path is available on Python 3.6 (verified 2026-08-13).
"""Path resolution for the c14 plugin package.

Pure-Python (no pymol / PyQt5 imports) so it is unit-testable in WSL
without a display. All bundled-data lookups must go through data_path()
so they work regardless of the current working directory.

When the plugin is unzipped into PyMOL's ``startup/`` dir, the runtime
CWD is PyMOL's launch directory (or wherever the user's shell was) --
unrelated to where the plugin lives. ``os.getcwd()``-relative paths
silently break; ``__file__``-relative paths always work. This is Pitfall
#1 in .planning/research/PITFALLS.md and the #1 breakage mode in
.planning/research/SUMMARY.md. Baking the convention into a single
helper in Phase 1 means every later phase inherits correct path handling.
"""
from pathlib import Path

# Package root = the directory containing THIS file (c14/paths.py -> c14/).
# .resolve() makes it absolute and dereferences the repo symlink during dev.
_PACKAGE_ROOT = Path(__file__).resolve().parent


def data_path(*relative_parts):
    # type: (*str) -> Path
    """Resolve a bundled data file path relative to the package root.

    Returns an absolute Path derived from __file__, NOT from os.getcwd().
    Does NOT check existence -- callers should call .exists() or handle
    FileNotFoundError when opening. Returns Path (use str() for PyMOL
    cmd.* APIs that take string paths, e.g. cmd.load(str(data_path(...)))).

    Pure resolver by design: a resolver that raises couples path
    arithmetic to filesystem state and breaks "compute where a future
    file would go" use cases. Resolve-only; let callers open.

    Example:
        p = data_path("data", "story", "glucose.json")
        # -> /abs/.../c14/data/story/glucose.json
    """
    return _PACKAGE_ROOT.joinpath(*relative_parts)


def selfcheck():
    # type: () -> str
    """Resolve a known bundled fixture and verify it exists.

    Returns the fixture's absolute path as a string. Raises
    FileNotFoundError if the package data layout is broken (e.g. the
    data/ dir wasn't shipped). Intended to be called both by the unit
    test (to prove CWD-independence) and, in a later phase, by the plugin
    loader at startup (Pitfall 1 mitigation: "fail loud on plugin load").
    """
    fixture = data_path("data", "selfcheck.json")
    if not fixture.is_file():
        raise FileNotFoundError(
            "c14 path self-check failed: bundled fixture not found at "
            "{path}. The package data/ directory may be missing.".format(
                path=fixture
            )
        )
    return str(fixture)
