from __future__ import annotations

import unittest
from pathlib import Path

from branchsnv.analysis import analyse_branch
from branchsnv.newick import read_newick, reroot_on_outgroup, select_exact_descendants
from branchsnv.nexus import read_transposed_nexus

FIXTURES = Path(__file__).parent / "fixtures"


class AnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.alignment = read_transposed_nexus(FIXTURES / "simple.nex")
        self.tree = reroot_on_outgroup(read_newick(FIXTURES / "simple.nwk"), {"Outgroup"})
        self.branch = select_exact_descendants(self.tree, {"A", "B"})

    def test_default_both_mode_reports_union(self) -> None:
        summary = analyse_branch(
            self.alignment, self.tree, self.branch, mode="both", include_ambiguous=False
        )
        self.assertEqual([result.site_id for result in summary.results], ["ref_1", "ref_6"])
        self.assertEqual(summary.fixed_exclusive_sites, 2)
        self.assertEqual(summary.unambiguous_change_sites, 1)

    def test_fixed_exclusive_is_strict_about_missing_descendants(self) -> None:
        summary = analyse_branch(
            self.alignment,
            self.tree,
            self.branch,
            mode="fixed-exclusive",
            include_ambiguous=False,
        )
        site_ids = {result.site_id for result in summary.results}
        self.assertNotIn("ref_5", site_ids)

    def test_fixed_exclusive_requires_callable_outside_taxa(self) -> None:
        from branchsnv.models import Alignment, Site

        modified_sites = list(self.alignment.sites)
        original = modified_sites[0]
        # Outgroup is outside the selected A/B clade. Making it missing must
        # prevent a strict fixed-exclusive call even though no outside taxon
        # is observed with the descendant state.
        modified_sites[0] = Site(
            site_id=original.site_id,
            states="?" + original.states[1:],
            input_row=original.input_row,
        )
        modified = Alignment(
            path=self.alignment.path,
            taxa=self.alignment.taxa,
            sites=tuple(modified_sites),
            ntax=self.alignment.ntax,
            nchar=self.alignment.nchar,
            gap=self.alignment.gap,
            missing=self.alignment.missing,
            symbols=self.alignment.symbols,
        )
        summary = analyse_branch(
            modified, self.tree, self.branch, mode="fixed-exclusive", include_ambiguous=False
        )
        self.assertNotIn("ref_1", {result.site_id for result in summary.results})


    def test_change_state_ambiguous_is_reported_explicitly(self) -> None:
        from branchsnv.models import Alignment, Site

        alignment = Alignment(
            path=self.alignment.path,
            taxa=self.alignment.taxa,
            sites=(Site(site_id="ambiguous", states="CRRCC", input_row=1),),
            ntax=self.alignment.ntax,
            nchar=1,
            gap=self.alignment.gap,
            missing=self.alignment.missing,
            symbols=self.alignment.symbols,
        )
        hidden = analyse_branch(
            alignment, self.tree, self.branch, mode="parsimony", include_ambiguous=False
        )
        shown = analyse_branch(
            alignment, self.tree, self.branch, mode="parsimony", include_ambiguous=True
        )

        self.assertEqual(hidden.change_state_ambiguous_sites, 1)
        self.assertEqual(hidden.reported_sites, 0)
        self.assertEqual(shown.change_state_ambiguous_sites, 1)
        self.assertEqual(shown.reported_sites, 1)
        result = shown.results[0]
        self.assertEqual(result.parsimony_status, "change_state_ambiguous")
        self.assertEqual(result.parent_states, "C")
        self.assertEqual(result.child_states, "A|G")
        self.assertEqual(result.possible_pairs, "C>A|C>G")
        self.assertEqual(result.change, "C>A|C>G")

    def test_ambiguous_option_reports_ambiguous_parsimony_sites(self) -> None:
        summary = analyse_branch(
            self.alignment, self.tree, self.branch, mode="parsimony", include_ambiguous=True
        )
        statuses = {result.site_id: result.parsimony_status for result in summary.results}
        self.assertEqual(statuses["ref_2"], "placement_ambiguous")
        self.assertEqual(statuses["ref_5"], "placement_ambiguous")


if __name__ == "__main__":
    unittest.main()
