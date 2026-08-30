"""Unit tests for rpg.achievements.AchievementBoard. Pure-Python, stdlib only.

Run: ``python3.6 -m unittest tests.test_achievements -v``

Proves (15 tests):
- Each unlock type: first_game on new game; no first_game when not new game;
  true / bad / good / normal ending unlocks; branches_discovered records
  node ids; characters_tried records the character on a new game.
- Idempotency (3 forms): reaching the same ending twice (deduped by node_id +
  tier achievement appears once); visiting the same node twice (branches
  deduped by node.id); starting a new game as the same character twice
  (characters_tried deduped by character).
- Unknown-character no-op: fatty_acid_tried is NOT in the v1 catalog ->
  _unlock no-ops, but the character IS still recorded in characters_tried
  (safe for Phase 8 catalog expansion).
- Persistence: round-trip (unlock -> _save -> new AchievementBoard(same
  path) -> same data); backward-compat partial JSON (missing keys default
  to empty lists via the forward-compatible .get merge); _save creates the
  parent dir.
- ACH-01: the schema has NO score/rank/points keys; achievements_unlocked
  entries have only id/name/description/date (collection, NOT a leaderboard).
- ISO-UTC date: an unlocked achievement's date ends with "Z" and parses as
  ISO-8601.

Pure-Python domain test -- NO pymol/PyQt5 import (the board is WSL-testable).
Uses a temp dir for the path so tests never touch the real user data dir.
"""
import datetime
import json
import os
import shutil
import tempfile
import unittest

from rpg.achievements import (
    AchievementBoard,
    ACHIEVEMENT_CATALOG_V1,
    TIER_ACHIEVEMENT_ID,
)


# --- Tiny mock TurnResult / Node (duck-typed: the board only reads .node.id +
# .node.is_ending). Mirrors rpg.engine.TurnResult (engine.py:54-55) +
# rpg.story.model.Node (model.py:251-252,310-314) for the attributes the board
# actually inspects. ---------------------------------------------------------
class FakeNode(object):
    def __init__(self, id, is_ending=None):
        # type: (str, str) -> None
        self.id = id
        self.is_ending = is_ending


class FakeTurn(object):
    def __init__(self, node):
        # type: (FakeNode) -> None
        self.node = node


class TestAchievementBoard(unittest.TestCase):
    """Unlock detection + persistence + idempotency + backward-compat +
    collection-based-not-leaderboard + ISO-UTC date."""

    def setUp(self):
        # Track temp dirs created per-test; clean in tearDown so tests never
        # touch the real user data dir (~/.pymol/rpg-tale-of-c/...).
        self._dirs = []

    def tearDown(self):
        for d in self._dirs:
            try:
                shutil.rmtree(d)
            except OSError:
                pass

    def _tmpfile(self, name="achievements.json"):
        # type: (str) -> str
        """A path inside a fresh temp dir (cleaned in tearDown)."""
        d = tempfile.mkdtemp()
        self._dirs.append(d)
        return os.path.join(d, name)

    def _new_board(self, name="achievements.json"):
        # type: (str) -> AchievementBoard
        """A fresh AchievementBoard backed by a temp-dir path."""
        return AchievementBoard(path=self._tmpfile(name))

    def _unlocked_ids(self, board):
        # type: (AchievementBoard) -> list
        return [a["id"] for a in board.data["achievements_unlocked"]]

    def _parse_iso_utc(self, date_str):
        # type: (str) -> datetime.datetime
        """Parse a '...Z' ISO-8601 UTC timestamp. Python 3.6 has no
        ``datetime.fromisoformat`` (3.7+), so try strptime with and without
        microseconds. Fails the test if it does not parse."""
        self.assertTrue(date_str.endswith("Z"),
                        "date must end with 'Z' (UTC marker): %r" % date_str)
        core = date_str[:-1]
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.datetime.strptime(core, fmt)
            except ValueError:
                continue
        self.fail("date does not parse as ISO-8601: %r" % date_str)

    # --- Each unlock type ---------------------------------------------------

    def test_first_game_unlock_on_new_game(self):
        """is_new_game=True unlocks first_game + <character>_tried and
        records the character in characters_tried."""
        b = self._new_board()
        b.on_turn(FakeTurn(FakeNode("intro.preface")), "glucose",
                  is_new_game=True)
        ids = self._unlocked_ids(b)
        self.assertIn("first_game", ids, "first_game unlocked on new game")
        self.assertIn("glucose_tried", ids, "glucose_tried unlocked")
        self.assertIn("glucose", b.data["characters_tried"],
                      "character recorded in characters_tried")

    def test_no_first_game_unlock_when_not_new_game(self):
        """is_new_game=False does NOT unlock first_game and does NOT record
        the character (a mid-playthrough turn is not a new game)."""
        b = self._new_board()
        b.on_turn(FakeTurn(FakeNode("gly.start")), "glucose", is_new_game=False)
        self.assertNotIn("first_game", self._unlocked_ids(b),
                         "first_game NOT unlocked mid-playthrough")
        self.assertEqual(b.data["characters_tried"], [],
                         "characters_tried empty when not a new game")

    def test_true_ending_unlock(self):
        """Reaching a True ending unlocks true_ending and records the
        ending in endings_found with node_id/tier/character."""
        b = self._new_board()
        b.on_turn(FakeTurn(FakeNode("end.true", is_ending="true")), "glucose")
        self.assertIn("true_ending", self._unlocked_ids(b),
                      "true_ending unlocked")
        self.assertEqual(len(b.data["endings_found"]), 1,
                         "one ending recorded")
        e = b.data["endings_found"][0]
        self.assertEqual(e["node_id"], "end.true")
        self.assertEqual(e["tier"], "true")
        self.assertEqual(e["character"], "glucose")

    def test_bad_ending_unlock(self):
        """Reaching a Bad ending unlocks bad_ending."""
        b = self._new_board()
        b.on_turn(FakeTurn(FakeNode("end.bad", is_ending="bad")), "glucose")
        self.assertIn("bad_ending", self._unlocked_ids(b),
                      "bad_ending unlocked")

    def test_good_and_normal_ending_unlocks(self):
        """Reaching a Good ending unlocks good_ending; reaching a Normal
        ending unlocks normal_ending (distinct node ids so both register)."""
        b = self._new_board()
        b.on_turn(FakeTurn(FakeNode("end.good", is_ending="good")), "glucose")
        self.assertIn("good_ending", self._unlocked_ids(b),
                      "good_ending unlocked")
        b.on_turn(FakeTurn(FakeNode("end.normal", is_ending="normal")), "glucose")
        self.assertIn("normal_ending", self._unlocked_ids(b),
                      "normal_ending unlocked")

    def test_branches_discovered_records_node_id(self):
        """Every visited node id is recorded in branches_discovered."""
        b = self._new_board()
        b.on_turn(FakeTurn(FakeNode("tca.shuffle")), "glucose")
        self.assertIn("tca.shuffle", b.data["branches_discovered"],
                      "node id recorded in branches_discovered")

    # --- Idempotency (3 forms) ---------------------------------------------

    def test_idempotent_reaching_same_ending_twice(self):
        """Reaching the same ending twice does NOT duplicate the
        endings_found entry (deduped by node_id) NOR the tier achievement
        (deduped by achievement id)."""
        b = self._new_board()
        turn = FakeTurn(FakeNode("end.true", is_ending="true"))
        b.on_turn(turn, "glucose")
        b.on_turn(turn, "glucose")
        self.assertEqual(len(b.data["endings_found"]), 1,
                         "endings_found deduped by node_id")
        true_count = sum(1 for a in b.data["achievements_unlocked"]
                         if a["id"] == "true_ending")
        self.assertEqual(true_count, 1, "tier achievement appears once")

    def test_idempotent_same_node_visited_twice(self):
        """Visiting the same node twice records its id in branches_discovered
        only once (deduped by node.id)."""
        b = self._new_board()
        turn = FakeTurn(FakeNode("gly.start"))
        b.on_turn(turn, "glucose")
        b.on_turn(turn, "glucose")
        self.assertEqual(b.data["branches_discovered"].count("gly.start"), 1,
                         "branches_discovered deduped by node.id")

    def test_idempotent_same_character_new_game_twice(self):
        """Starting a new game as the same character twice records the
        character in characters_tried only once (deduped by character)."""
        b = self._new_board()
        turn = FakeTurn(FakeNode("intro.preface"))
        b.on_turn(turn, "glucose", is_new_game=True)
        b.on_turn(turn, "glucose", is_new_game=True)
        self.assertEqual(b.data["characters_tried"], ["glucose"],
                         "characters_tried deduped by character")

    # --- Unknown-character no-op (forward-compat for Phase 8) --------------

    def test_unknown_character_tried_no_op(self):
        """A character whose <character>_tried id is NOT in the v1 catalog
        (e.g. fatty_acid_tried in Phase 6, before the Phase 8 catalog
        extension) does NOT unlock the achievement, but the character IS
        still recorded in characters_tried (_unlock no-ops safely on unknown
        ids)."""
        b = self._new_board()
        b.on_turn(FakeTurn(FakeNode("fa.start")), "fatty_acid", is_new_game=True)
        self.assertNotIn("fatty_acid_tried", self._unlocked_ids(b),
                         "fatty_acid_tried NOT unlocked (not in v1 catalog)")
        self.assertIn("fatty_acid", b.data["characters_tried"],
                      "character still recorded in characters_tried")

    # --- Persistence --------------------------------------------------------

    def test_persistence_round_trip(self):
        """Unlock a few things (on_turn auto-saves when changed); a NEW
        AchievementBoard with the same path loads the same
        characters_tried / endings_found / branches_discovered /
        achievements_unlocked."""
        b = self._new_board()
        b.on_turn(FakeTurn(FakeNode("intro.preface")), "glucose", is_new_game=True)
        b.on_turn(FakeTurn(FakeNode("tca.true", is_ending="true")), "glucose")
        # New board from the same path -> _load reads the saved JSON.
        b2 = AchievementBoard(path=b.path)
        self.assertEqual(b2.data["characters_tried"], b.data["characters_tried"],
                         "characters_tried survives reload")
        self.assertEqual(b2.data["endings_found"], b.data["endings_found"],
                         "endings_found survives reload")
        self.assertEqual(b2.data["branches_discovered"],
                         b.data["branches_discovered"],
                         "branches_discovered survives reload")
        self.assertEqual(b2.data["achievements_unlocked"],
                         b.data["achievements_unlocked"],
                         "achievements_unlocked survives reload")

    def test_backward_compat_partial_json(self):
        """A partial JSON (missing keys) loads cleanly: present keys are
        kept; missing keys default to empty lists (forward-compatible .get
        merge -- lets the schema grow across phases without a migration)."""
        p = self._tmpfile()
        with open(p, "w", encoding="utf-8") as fh:
            json.dump({"version": 1, "characters_tried": ["glucose"]}, fh)
        b = AchievementBoard(path=p)
        self.assertEqual(b.data["characters_tried"], ["glucose"],
                         "present key preserved")
        self.assertEqual(b.data["endings_found"], [],
                         "missing key defaults to empty list")
        self.assertEqual(b.data["branches_discovered"], [],
                         "missing key defaults to empty list")
        self.assertEqual(b.data["achievements_unlocked"], [],
                         "missing key defaults to empty list")

    def test_save_creates_parent_dir(self):
        """on_turn triggers _save, which os.makedirs(parent, exist_ok=True)
        for a path with a non-existent parent dir; the file is created."""
        d = tempfile.mkdtemp()
        self._dirs.append(d)
        path = os.path.join(d, "sub", "nested", "achievements.json")
        self.assertFalse(os.path.isdir(os.path.dirname(path)),
                         "precondition: parent dir does not exist")
        b = AchievementBoard(path=path)
        b.on_turn(FakeTurn(FakeNode("intro.preface")), "glucose",
                  is_new_game=True)
        self.assertTrue(os.path.isfile(path),
                        "_save created the parent dir + the file")

    # --- ACH-01: collection-based, NOT a leaderboard ------------------------

    def test_collection_based_not_leaderboard(self):
        """The schema has NO score/rank/points keys (ACH-01: collection-based,
        NOT a ranked leaderboard); each achievements_unlocked entry has only
        id/name/description/date (no score field)."""
        b = self._new_board()
        b.on_turn(FakeTurn(FakeNode("intro.preface")), "glucose", is_new_game=True)
        for banned_key in ("score", "rank", "points"):
            self.assertNotIn(banned_key, b.data,
                              "ACH-01: no %r key in schema" % banned_key)
        for entry in b.data["achievements_unlocked"]:
            self.assertEqual(set(entry.keys()),
                             {"id", "name", "description", "date"},
                             "achievement entry has only id/name/description/date")

    def test_date_is_iso_utc(self):
        """An unlocked achievement's date ends with 'Z' (UTC marker) and
        parses as ISO-8601 (3.6-compatible strptime with/without
        microseconds)."""
        b = self._new_board()
        b.on_turn(FakeTurn(FakeNode("intro.preface")), "glucose",
                  is_new_game=True)
        self.assertTrue(b.data["achievements_unlocked"],
                        "precondition: at least one achievement unlocked")
        for entry in b.data["achievements_unlocked"]:
            parsed = self._parse_iso_utc(entry["date"])
            self.assertIsInstance(parsed, datetime.datetime,
                                  "date parses as a datetime")


if __name__ == "__main__":
    unittest.main()
