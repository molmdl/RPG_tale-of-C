"""Unit tests for c14.story.model (Node, Choice, MolAction). Pure-Python, stdlib only.

Run: ``python3.6 -m unittest tests.test_model -v``
"""
import unittest

from c14.story.model import Node, Choice, MolAction


class TestModel(unittest.TestCase):

    def test_mol_action_roundtrip(self):
        """MolAction to_dict/from_dict round-trips; default args is {} when omitted."""
        m = MolAction("load", "pdb:1TNR", {"object": "hero"})
        d = m.to_dict()
        self.assertEqual(d, {"op": "load", "target": "pdb:1TNR",
                             "args": {"object": "hero"}})
        m2 = MolAction.from_dict(d)
        self.assertEqual(m, m2)

        # Default args is {} when omitted (both constructor and from_dict).
        bare = MolAction("hide_all")
        self.assertEqual(bare.args, {})
        bare2 = MolAction.from_dict({"op": "hide_all"})
        self.assertEqual(bare2.args, {})
        self.assertEqual(bare, bare2)

    def test_choice_defaults(self):
        """Choice with only a label gets None/goto/cond/weight and {}/[] defaults."""
        c = Choice("Continue")
        self.assertEqual(c.label, "Continue")
        self.assertIsNone(c.goto)
        self.assertIsNone(c.cond)
        self.assertIsNone(c.weight)
        self.assertEqual(c.effects, {})
        self.assertEqual(c.tags, [])

    def test_choice_from_dict(self):
        """A raw weighted choice round-trips through from_dict/to_dict."""
        raw = {"label": "Go", "goto": "end", "weight": 1.0,
               "tags": ["rng:weighted"]}
        c = Choice.from_dict(raw)
        self.assertEqual(c.label, "Go")
        self.assertEqual(c.goto, "end")
        self.assertEqual(c.weight, 1.0)
        self.assertEqual(c.tags, ["rng:weighted"])
        # effects defaults to {} when not in the raw dict.
        self.assertEqual(c.effects, {})
        # Round-trip equality.
        self.assertEqual(c.to_dict()["label"], "Go")
        self.assertEqual(c, Choice.from_dict(c.to_dict()))

    def test_node_defaults(self):
        """Node with only an id gets empty lists and is_ending=None."""
        n = Node("intro.start")
        self.assertEqual(n.id, "intro.start")
        self.assertEqual(n.text_dramatic, "")
        self.assertEqual(n.text_teaching, "")
        self.assertEqual(n.claim_ids, [])
        self.assertEqual(n.choices, [])
        self.assertEqual(n.on_enter, [])
        self.assertEqual(n.tags, [])
        self.assertIsNone(n.is_ending)
        self.assertIsNone(n.on_enter_divert)

    def test_node_from_dict_full(self):
        """Node.from_dict parses nested choices (->Choice) and on_enter (->MolAction)."""
        raw = {
            "id": "intro.start",
            "text_dramatic": "You are a carbon atom.",
            "text_teaching": "Cellular respiration begins with glucose.",
            "claim_ids": ["intro.glucose"],
            "on_enter": [
                {"op": "hide_all"},
                {"op": "load", "target": "pdb:1TNR",
                 "args": {"object": "1TNR"}},
            ],
            "choices": [
                {"label": "Continue (luck decides)", "weight": 1.0,
                 "goto": "tca.resolve", "tags": ["rng:weighted"]},
                {"label": "Try to edit the enzyme", "goto": "edit.prompt",
                 "tags": ["edit:offer"]},
            ],
            "is_ending": None,
        }
        node = Node.from_dict(raw)
        self.assertEqual(node.id, "intro.start")
        self.assertEqual(node.text_dramatic, "You are a carbon atom.")
        self.assertEqual(node.claim_ids, ["intro.glucose"])
        # Nested Choice parse.
        self.assertEqual(len(node.choices), 2)
        self.assertIsInstance(node.choices[0], Choice)
        self.assertEqual(node.choices[0].weight, 1.0)
        self.assertEqual(node.choices[0].goto, "tca.resolve")
        # Nested MolAction parse.
        self.assertEqual(len(node.on_enter), 2)
        self.assertIsInstance(node.on_enter[0], MolAction)
        self.assertEqual(node.on_enter[0].op, "hide_all")
        self.assertEqual(node.on_enter[1].target, "pdb:1TNR")
        self.assertIsNone(node.is_ending)

    def test_node_is_ending(self):
        """is_ending_node property reflects whether is_ending is set."""
        self.assertTrue(Node("e", is_ending="good").is_ending_node)
        self.assertTrue(Node("e", is_ending="bad").is_ending_node)
        self.assertFalse(Node("x").is_ending_node)
        self.assertFalse(Node("x", is_ending=None).is_ending_node)

    def test_node_roundtrip(self):
        """A fully-populated Node round-trips through to_dict/from_dict."""
        original = Node(
            id="tca.shuffle",
            text_dramatic="The great wheel spins.",
            text_teaching="TCA cycle intermediates rearrange.",
            claim_ids=["tca.redistribution"],
            choices=[
                Choice("Continue (luck decides)", goto="tca.resolve",
                       weight=1.0, tags=["rng:weighted"]),
                Choice("Try to edit the enzyme", goto="edit.prompt",
                       tags=["edit:offer"]),
            ],
            on_enter=[
                MolAction("hide_all"),
                MolAction("load", "pdb:1TNR", {"object": "1TNR"}),
                MolAction("show", args={"rep": "cartoon"}),
            ],
            is_ending=None,
            tags=["stage:tca", "rng:shuffle"],
            on_enter_divert=None,
        )
        roundtripped = Node.from_dict(original.to_dict())
        self.assertEqual(original, roundtripped)


if __name__ == "__main__":
    unittest.main()
