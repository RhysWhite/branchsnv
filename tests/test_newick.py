from __future__ import annotations

import unittest

from branchsnv.errors import NewickFormatError, ValidationError
from branchsnv.newick import (
    branch_records,
    descendant_tip_map,
    parse_newick,
    reroot_on_outgroup,
)


class NewickTests(unittest.TestCase):
    def test_parses_labels_lengths_comments_and_polytomy(self) -> None:
        tree = parse_newick("[&R]('A one':1,B:2,C:3)root:0;")
        self.assertEqual(sorted(tip.name for tip in tree.tips()), ["A one", "B", "C"])
        self.assertEqual(tree.root.name, "root")
        self.assertEqual(len(tree.root.children), 3)

    def test_rejects_duplicate_tips(self) -> None:
        with self.assertRaisesRegex(NewickFormatError, "Duplicate tree tip"):
            parse_newick("(A:1,A:2);")

    def test_branch_ids_ignore_sibling_order(self) -> None:
        first = parse_newick("(O,((A,B),(C,D)));")
        second = parse_newick("(((D,C),(B,A)),O);")
        first_ids = {record.branch_id for record in branch_records(first)}
        second_ids = {record.branch_id for record in branch_records(second)}
        self.assertEqual(first_ids, second_ids)

    def test_reroots_on_internal_outgroup_and_suppresses_old_root(self) -> None:
        tree = parse_newick("(A:1,((B:1,C:1):1,(D:1,E:1):1):1);")
        rooted = reroot_on_outgroup(tree, {"B", "C"})
        descendants = descendant_tip_map(rooted)
        root_sides = {frozenset(descendants[child]) for child in rooted.root.children}
        self.assertIn(frozenset({"B", "C"}), root_sides)
        self.assertIn(frozenset({"A", "D", "E"}), root_sides)
        self.assertEqual(len(rooted.tips()), 5)
        self.assertTrue(all(len(node.children) != 1 for node in rooted.iter_preorder()))

    def test_keeps_existing_matching_root(self) -> None:
        tree = parse_newick("(O,((A,B),(C,D)));")
        rooted = reroot_on_outgroup(tree, {"O"})
        self.assertIs(rooted, tree)

    def test_rejects_non_monophyletic_outgroup(self) -> None:
        tree = parse_newick("(O,((A,B),(C,D)));")
        with self.assertRaisesRegex(ValidationError, "not monophyletic"):
            reroot_on_outgroup(tree, {"A", "C"})


if __name__ == "__main__":
    unittest.main()
