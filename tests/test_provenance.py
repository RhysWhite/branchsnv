from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from branchsnv import __version__
from branchsnv.cli import main
from branchsnv.util import sha256_file

FIXTURES = Path(__file__).parent / "fixtures"


class ProvenanceTests(unittest.TestCase):
    def test_report_is_internally_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results = root / "results.tsv"
            members = root / "members.txt"
            report_path = root / "report.json"
            code = main(
                [
                    "find",
                    "--alignment",
                    str(FIXTURES / "simple.nex"),
                    "--tree",
                    str(FIXTURES / "simple.nwk"),
                    "--outgroup",
                    "Outgroup",
                    "--clade-tips",
                    str(FIXTURES / "ab_tips.txt"),
                    "--mode",
                    "both",
                    "--output",
                    str(results),
                    "--members-output",
                    str(members),
                    "--report",
                    str(report_path),
                ]
            )
            self.assertEqual(code, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            results_sha = sha256_file(results)
            members_sha = sha256_file(members)

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["tool"], {"name": "BRANCHSNV", "version": __version__})
        self.assertEqual(report["outputs"]["results_tsv"]["sha256"], results_sha)
        self.assertEqual(report["outputs"]["branch_members"]["sha256"], members_sha)
        membership_digest = report["branch"]["descendant_taxa_sha256"]
        self.assertEqual(report["branch"]["branch_id"], f"b_{membership_digest}")
        self.assertEqual(report["branch"]["short_id"], f"b_{membership_digest[:16]}")
        self.assertEqual(
            report["rooting"],
            {"method": "outgroup", "outgroup": ["Outgroup"]},
        )
        self.assertEqual(
            report["branch"]["selection"],
            {
                "method": "exact_descendant_file",
                "source": "ab_tips.txt",
                "sha256": sha256_file(FIXTURES / "ab_tips.txt"),
            },
        )
        self.assertEqual(
            report["parameters"],
            {
                "mode": "both",
                "include_ambiguous_parsimony_sites": False,
                "state_cost_model": "unordered_equal_cost",
                "gap_treatment": "unknown_state",
                "missing_treatment": "unknown_state",
                "fixed_exclusive_descendant_call_rate": 1.0,
                "fixed_exclusive_outside_call_rate": 1.0,
            },
        )
        counts = report["results"]["parsimony"]
        self.assertEqual(sum(counts.values()), report["results"]["sites_examined"])
        self.assertEqual(report["warnings"], [])


if __name__ == "__main__":
    unittest.main()
