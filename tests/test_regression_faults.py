"""Fixtures designed to catch common implementation faults.

These tests do not mutate production code. Each scenario has a result that a
specific plausible fault would change, so the suite acts as a permanent guard
against those faults entering the implementation.
"""

from __future__ import annotations

import unittest

from branchsnv.newick import parse_newick, select_exact_descendants
from branchsnv.parsimony import compile_tree, reconstruct_site


class FaultRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = parse_newick("(O,((A,B),(C,D)));")
        self.branch = select_exact_descendants(self.tree, {"A", "B"})
        index = {name: position for position, name in enumerate(("O", "A", "B", "C", "D"))}
        self.compiled = compile_tree(self.tree, self.branch.node, index)

    def test_catches_wrong_side_of_branch(self) -> None:
        result = reconstruct_site(self.compiled, "GAAGG", gap="-", missing="?")
        self.assertEqual(result.possible_pairs, (("G", "A"),))

    def test_catches_majority_state_substitution_for_parsimony(self) -> None:
        # A majority-only rule would call G as the ancestor and force G>A.
        # Exact parsimony shows that placement is ambiguous.
        result = reconstruct_site(self.compiled, "GAAGA", gap="-", missing="?")
        self.assertEqual(result.status, "placement_ambiguous")

    def test_catches_gap_as_fifth_state(self) -> None:
        result = reconstruct_site(self.compiled, "G-A GG".replace(" ", ""), gap="-", missing="?")
        self.assertNotEqual(result.status, "unambiguous_change")

    def test_catches_arbitrary_resolution_of_ties(self) -> None:
        result = reconstruct_site(self.compiled, "GCCAA", gap="-", missing="?")
        self.assertGreater(len(result.possible_pairs), 1)


if __name__ == "__main__":
    unittest.main()
