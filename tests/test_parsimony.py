from __future__ import annotations

import itertools
import random
import unittest

from branchsnv.newick import parse_newick, select_exact_descendants
from branchsnv.parsimony import compile_tree, reconstruct_site

STATES = "ACGT"
IUPAC = {
    "A": {"A"},
    "C": {"C"},
    "G": {"G"},
    "T": {"T"},
    "R": {"A", "G"},
    "Y": {"C", "T"},
    "N": set(STATES),
    "?": set(STATES),
    "-": set(STATES),
}


def exhaustive_oracle(tree, focal_node, leaf_symbols):  # type: ignore[no-untyped-def]
    nodes = tuple(tree.iter_preorder())
    internal = [node for node in nodes if not node.is_tip]
    best_score = None
    best_pairs = set()
    for assignment_values in itertools.product(STATES, repeat=len(internal)):
        assignment = dict(zip(internal, assignment_values))
        valid = True
        for tip in tree.tips():
            if assignment_values is None:  # pragma: no cover - keeps type checkers quiet
                pass
            symbol = leaf_symbols[tip.name]
            if assignment.get(tip, None) is not None:
                raise AssertionError("Tip unexpectedly treated as internal")
            if not IUPAC[symbol]:
                valid = False
        if not valid:
            continue
        score = 0
        for node in nodes:
            if node is tree.root:
                continue
            parent = node.parent
            assert parent is not None
            parent_state = assignment[parent]
            if node.is_tip:
                allowed = IUPAC[leaf_symbols[node.name]]
                edge_cost = min(parent_state != state for state in allowed)
            else:
                edge_cost = parent_state != assignment[node]
            score += int(edge_cost)
        # The score above minimizes each terminal edge independently, which is
        # equivalent to enumerating allowed leaf states because leaves do not
        # connect to any other edge.
        parent = focal_node.parent
        assert parent is not None
        parent_state = assignment[parent]
        if focal_node.is_tip:
            child_states = IUPAC[leaf_symbols[focal_node.name]]
        else:
            child_states = {assignment[focal_node]}
        focal_pairs = {(parent_state, state) for state in child_states}

        if best_score is None or score < best_score:
            best_score = score
            best_pairs = focal_pairs
        elif score == best_score:
            best_pairs.update(focal_pairs)
    assert best_score is not None
    return best_score, tuple(sorted(best_pairs))


class ParsimonyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = parse_newick("(O,((A,B),(C,D)));")
        self.branch = select_exact_descendants(self.tree, {"A", "B"})
        self.index = {name: index for index, name in enumerate(("O", "A", "B", "C", "D"))}
        self.compiled = compile_tree(self.tree, self.branch.node, self.index)

    def result(self, symbols: str):  # type: ignore[no-untyped-def]
        return reconstruct_site(self.compiled, symbols, gap="-", missing="?")

    def test_clean_branch_change(self) -> None:
        result = self.result("GAAGG")
        self.assertEqual(result.score, 1)
        self.assertEqual(result.status, "unambiguous_change")
        self.assertEqual(result.possible_pairs, (("G", "A"),))

    def test_no_branch_change(self) -> None:
        result = self.result("GAGGG")
        self.assertEqual(result.status, "no_change")

    def test_parallel_pattern_can_make_placement_ambiguous(self) -> None:
        result = self.result("GAAGA")
        self.assertEqual(result.score, 2)
        self.assertEqual(result.status, "placement_ambiguous")
        self.assertIn(("G", "A"), result.possible_pairs)
        self.assertIn(("A", "A"), result.possible_pairs)

    def test_missing_descendant_is_not_forced(self) -> None:
        result = self.result("G?AGG")
        self.assertEqual(result.status, "placement_ambiguous")

    def test_matches_exhaustive_oracle_for_generated_patterns(self) -> None:
        random_generator = random.Random(20260731)
        symbols = list("ACGT") + ["N", "R", "Y", "?", "-"]
        tips = ("O", "A", "B", "C", "D")
        for _ in range(250):
            pattern = "".join(random_generator.choice(symbols) for _ in tips)
            leaf_symbols = dict(zip(tips, pattern))
            expected_score, expected_pairs = exhaustive_oracle(
                self.tree, self.branch.node, leaf_symbols
            )
            observed = self.result(pattern)
            self.assertEqual(observed.score, expected_score, pattern)
            self.assertEqual(observed.possible_pairs, expected_pairs, pattern)


if __name__ == "__main__":
    unittest.main()
