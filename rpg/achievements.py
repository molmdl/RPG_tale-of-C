"""AchievementBoard: a collection-based achievement board persisted to a
user-writable JSON file (ACH-01, ACH-02). Pure-Python domain module.

ACH-01 (collection-based, NOT a ranked leaderboard): the board records WHAT
was found -- characters tried (set), endings found (one entry per unique
node_id), branches discovered (set of node ids), and a fixed catalog of
unlockable achievements (``achievements_unlocked``). There are NO scores,
ranks, or points anywhere in the schema. The player "fills in" a fixed
catalog; the board never ranks playthroughs.

ACH-02 (persists across PyMOL restarts AND plugin reinstalls): the JSON lives
at ``user_data_path("achievements.json")`` (``~/.pymol/rpg-tale-of-c/`` on
Linux/Mac, ``%APPDATA%/pymol/rpg-tale-of-c/`` on Windows) -- OUTSIDE the
plugin install dir (``~/.pymol/startup/<plugin>/``), so a delete-and-reinstall
of the plugin does NOT wipe the player's progress (06-RESEARCH
Pitfall 5 / Pattern 5).

Decoupling: the CONTROLLER (06-06) calls ``board.on_turn(turn_result,
character, is_new_game)`` after each ``engine.start`` / ``choose`` /
``apply_player_edit``. The engine stays pure-domain -- it never calls the
board (06-RESEARCH Open Question 6). The board reads ``turn_result.node``
(``engine.py:54-55``), inspecting ``node.id`` + ``node.is_ending``
(``model.py:251-252,310-314``: ``None`` = non-ending, or one of
``"true"|"good"|"normal"|"bad"``).

Design constraints honored:
- Python 3.6 stdlib ONLY (``json``, ``os``, ``datetime``). NO pymol/PyQt5
  imports (the Phase 1 AST gate ``tools/check_imports.py`` scans this file --
  it lives in ``rpg/`` root). Importable in pure WSL ``python3.6`` for unit
  tests.
- NO ``@dataclass`` (3.7+ -- research Pitfall 1). Plain class on instance
  attributes, matching the ``SaveStore`` (``rpg/persist.py``) + ``Node``
  (``rpg/story/model.py``) precedent.
- NO f-strings (3.6); ``.format()`` / ``%`` for interpolation, matching repo
  convention.
- JSON persistence mirrors ``SaveStore`` (``persist.py:38-65``): ``indent=2``
  for human-readable diff-friendly files + a trailing newline + parent-dir
  ``os.makedirs(parent, exist_ok=True)`` on save.
- Forward-compatible ``.get`` merge on load: a partial / older-schema JSON
  (missing keys) defaults to the empty-list defaults rather than crashing
  (backward-compat; lets the schema grow across phases without a migration).
- ``_unlock`` NO-OPS on unknown achievement ids (the catalog lookup misses):
  only ``glucose_tried`` is defined for Phase 6 (glucose MVP); Phase 8 will
  add ``fatty_acid_tried`` + ``alcohol_tried``. Because ``_unlock`` safely
  no-ops on a missing catalog entry, future expansion needs NO code change
  here -- the controller can call ``_unlock(character + "_tried")`` for any
  character and it unlocks only when the catalog has the id.
- Idempotent: reaching the same ending twice does NOT duplicate the
  ``endings_found`` entry (deduped by ``node_id``) or the tier achievement
  (deduped by achievement id); visiting the same node twice does NOT
  duplicate the ``branches_discovered`` entry (deduped by ``node.id``);
  starting a new game as the same character twice does NOT duplicate
  ``characters_tried`` (deduped by character).
- Save discipline: ``on_turn`` persists to disk ONLY when something changed
  this turn (``_unlock`` returns ``True`` iff it appended a new achievement,
  so the ``changed`` flag tracks every mutation including unlocks). This
  avoids redundant writes on no-op turns.
"""

import datetime
import json
import os

from rpg.paths import user_data_path


# v1 achievement catalog: (id, name, description). The fixed set the player
# "fills in" (ACH-01: a collection, NOT a leaderboard). Only glucose_tried is
# defined for Phase 6 (glucose MVP); fatty_acid_tried + alcohol_tried are
# Phase 8 ids -- _unlock no-ops on them until the catalog is extended, so the
# controller can call _unlock("<character>_tried") for any character safely.
ACHIEVEMENT_CATALOG_V1 = [
    ("first_game",    "First Steps",     "Started your first playthrough"),
    ("glucose_tried", "Glucose",         "Began a playthrough as glucose"),
    ("true_ending",   "Soul Harvested",  "Reached a True ending (electrons -> ATP via ETC)"),
    ("bad_ending",    "Lost Connection", "Reached a Bad ending"),
    ("good_ending",   "Retained",        "Reached a Good ending (carbon body retained)"),
    ("normal_ending", "Released",        "Reached a Normal ending (CO2 released)"),
]

# Maps Node.is_ending tier -> the achievement id unlocked when that ending is
# reached. ``true`` -> "Soul Harvested" (the soul-jump / metamorphosis destiny;
# the hero's electrons harvested into ATP via the ETC), ``good`` -> "Retained"
# (carbon body retained pre-oxidation), ``normal`` -> "Released" (CO2 without
# the full harvest arc), ``bad`` -> "Lost Connection" (failure / cycle-trap /
# host-death / critical-residue-break).
TIER_ACHIEVEMENT_ID = {
    "true":   "true_ending",
    "good":   "good_ending",
    "normal": "normal_ending",
    "bad":    "bad_ending",
}


class AchievementBoard(object):
    """Collection-based achievement board persisted to a user-writable JSON.

    The controller calls :meth:`on_turn` after each engine turn; this module
    diffs + persists. The Qt achievements dialog (06-12) reads the JSON (or
    this object) to render unlocks. Pure data + unlock logic -- no UI, no
    pymol, no engine coupling.
    """

    def __init__(self, path=None):
        # type: (str) -> None
        """Construct a board backed by ``path`` (default: the user-writable
        ``user_data_path("achievements.json")`` -- survives PyMOL restarts +
        plugin reinstalls). Loads any existing data (forward-compatible
        ``.get`` merge; missing keys default to empty collections).
        """
        self.path = path or str(user_data_path("achievements.json"))
        self.data = {
            "version": 1,
            "characters_tried": [],
            "endings_found": [],
            "branches_discovered": [],
            "achievements_unlocked": [],
        }
        self._load()

    def _load(self):
        # type: () -> None
        """Load existing JSON into ``self.data`` if the file exists.

        Forward-compatible ``.get`` merge: for each key in the default
        ``self.data``, take the loaded value if present, else keep the
        default. Lets a partial / older-schema JSON (missing keys) load
        cleanly without a migration -- missing keys default to empty lists.
        """
        if os.path.isfile(self.path):
            with open(self.path, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            for k in self.data:
                self.data[k] = loaded.get(k, self.data[k])

    def _save(self):
        # type: () -> None
        """Write ``self.data`` to ``self.path`` as human-readable JSON.

        Mirrors ``SaveStore.save`` (``persist.py:38-65``): ``indent=2`` for
        diff-friendly files, a trailing newline for clean diffs, and
        ``os.makedirs(parent, exist_ok=True)`` so callers can save to a
        nested user-dir path without pre-creating it. Guarded against paths
        with no dirname (``os.path.dirname`` returns "" for a bare filename).
        """
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2)
            fh.write("\n")

    def _unlock(self, achievement_id):
        # type: (str) -> bool
        """Unlock an achievement by id (idempotent). Returns ``True`` iff a
        NEW achievement was appended this call; ``False`` if it was already
        unlocked OR the id is not in ``ACHIEVEMENT_CATALOG_V1``.

        Safe for future expansion: an unknown id (e.g. ``fatty_acid_tried`` in
        Phase 6, before the Phase 8 catalog extension) is a no-op -- the
        catalog lookup simply misses. The controller can call
        ``_unlock(character + "_tried")`` for any character and it unlocks
        only when the catalog has the matching id.
        """
        if achievement_id is None:
            return False
        if any(a["id"] == achievement_id for a in self.data["achievements_unlocked"]):
            return False
        for aid, name, desc in ACHIEVEMENT_CATALOG_V1:
            if aid == achievement_id:
                self.data["achievements_unlocked"].append({
                    "id": aid,
                    "name": name,
                    "description": desc,
                    "date": datetime.datetime.utcnow().isoformat() + "Z",
                })
                return True
        return False  # not in catalog (e.g. fatty_acid_tried in Phase 6) -- safe no-op

    def on_turn(self, turn_result, character, is_new_game=False):
        # type: (object, str, bool) -> None
        """Record one engine turn's unlocks + persist if anything changed.

        Called by the controller after each ``engine.start`` /
        ``choose`` / ``apply_player_edit``. Idempotent: dedupes by id
        (endings by ``node_id``, branches by ``node.id``, characters by
        ``character``, achievements by achievement id).

        Args:
            turn_result: an object with a ``.node`` attribute whose
                ``.id`` (str) and ``.is_ending`` (None or one of
                "true"|"good"|"normal"|"bad") are read. Typically a
                ``TurnResult`` (``engine.py:54-55``).
            character: the current character id (e.g. "glucose"), or None.
            is_new_game: True iff this turn is the first turn of a fresh
                playthrough (i.e. the controller just called
                ``engine.start(character)``). Triggers the ``first_game``
                + ``<character>_tried`` unlocks + records the character in
                ``characters_tried``.
        """
        changed = False
        if is_new_game:
            # NOTE: ``self._unlock(...) or changed`` (NOT ``changed or ...``)
            # so _unlock ALWAYS executes even when changed is already True
            # (Python ``or`` short-circuits the RIGHT operand -- putting
            # changed on the right keeps the side effect live).
            changed = self._unlock("first_game") or changed
            if character and character not in self.data["characters_tried"]:
                self.data["characters_tried"].append(character)
                changed = True
            changed = self._unlock(character + "_tried") or changed
        node = turn_result.node
        if node.id not in self.data["branches_discovered"]:
            self.data["branches_discovered"].append(node.id)
            changed = True
        if node.is_ending is not None:
            entry = {
                "node_id": node.id,
                "tier": node.is_ending,
                "character": character,
                "date": datetime.datetime.utcnow().isoformat() + "Z",
            }
            if not any(e["node_id"] == node.id for e in self.data["endings_found"]):
                self.data["endings_found"].append(entry)
                changed = True
            changed = self._unlock(TIER_ACHIEVEMENT_ID.get(node.is_ending)) or changed
        if changed:
            self._save()
