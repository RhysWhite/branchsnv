from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from branchsnv.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


class CliTests(unittest.TestCase):
    def test_validate(self) -> None:
        code = main(
            [
                "validate",
                "--alignment",
                str(FIXTURES / "simple.nex"),
                "--tree",
                str(FIXTURES / "simple.nwk"),
                "--outgroup",
                "Outgroup",
            ]
        )
        self.assertEqual(code, 0)

    def test_find_outputs_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first_directory, tempfile.TemporaryDirectory() as second_directory:
            outputs = []
            for directory in (first_directory, second_directory):
                root = Path(directory)
                result = root / "results.tsv"
                members = root / "members.txt"
                report = root / "report.json"
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
                        str(result),
                        "--members-output",
                        str(members),
                        "--report",
                        str(report),
                    ]
                )
                self.assertEqual(code, 0)
                outputs.append(
                    (
                        result.read_bytes(),
                        members.read_bytes(),
                        json.loads(report.read_text(encoding="utf-8")),
                    )
                )
            self.assertEqual(outputs[0], outputs[1])

    def test_refuses_to_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "branches.tsv"
            output.write_text("existing", encoding="utf-8")
            code = main(
                [
                    "inspect",
                    "--tree",
                    str(FIXTURES / "simple.nwk"),
                    "--outgroup",
                    "Outgroup",
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(code, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "existing")

    def test_refuses_to_overwrite_an_input_even_with_force(self) -> None:
        original = (FIXTURES / "simple.nwk").read_bytes()
        code = main(
            [
                "inspect",
                "--tree",
                str(FIXTURES / "simple.nwk"),
                "--outgroup",
                "Outgroup",
                "--output",
                str(FIXTURES / "simple.nwk"),
                "--force",
            ]
        )
        self.assertEqual(code, 2)
        self.assertEqual((FIXTURES / "simple.nwk").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
