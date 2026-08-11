from __future__ import annotations

import unittest

from branchsnv.errors import SelectionError
from branchsnv.newick import (
    branch_records,
    parse_newick,
    resolve_branch_id,
    select_exact_descendants,
    select_mrca_branch,
)


class SelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = parse_newick("(O,((A,B),(C,D)));")

    def test_exact_descendants(self) -> None:
        branch = select_exact_descendants(self.tree, {"A", "B"})
        self.assertEqual(branch.descendant_tips, ("A", "B"))

    def test_exact_descendants_rejects_non_monophyly(self) -> None:
        with self.assertRaisesRegex(SelectionError, "do not form exactly"):
            select_exact_descendants(self.tree, {"A", "C"})

    def test_mrca_reports_actual_branch(self) -> None:
        branch = select_mrca_branch(self.tree, {"A", "B"})
        self.assertEqual(branch.descendant_count, 2)

    def test_branch_id_prefix(self) -> None:
        branch = select_exact_descendants(self.tree, {"A", "B"})
        resolved = resolve_branch_id(branch_records(self.tree), branch.short_id)
        self.assertIs(resolved.node, branch.node)

    def test_branch_id_rejects_unknown_identifier(self) -> None:
        with self.assertRaisesRegex(SelectionError, "No branch matches identifier"):
            resolve_branch_id(branch_records(self.tree), "b_not_a_real_branch")

    def test_branch_id_rejects_ambiguous_prefix(self) -> None:
        with self.assertRaisesRegex(SelectionError, "is ambiguous"):
            resolve_branch_id(branch_records(self.tree), "b_")

    def test_mrca_rejects_root(self) -> None:
        with self.assertRaisesRegex(SelectionError, "MRCA is the root"):
            select_mrca_branch(self.tree, {"O", "A"})


if __name__ == "__main__":
    unittest.main()
