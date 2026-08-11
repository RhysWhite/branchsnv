from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from branchsnv.cli import _read_name_file, main
from branchsnv.errors import SelectionError

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

    def test_rejects_duplicate_inline_outgroup_names(self) -> None:
        code = main(
            [
                "validate",
                "--alignment",
                str(FIXTURES / "simple.nex"),
                "--tree",
                str(FIXTURES / "simple.nwk"),
                "--outgroup",
                "Outgroup",
                "Outgroup",
            ]
        )
        self.assertEqual(code, 2)

    def test_rejects_duplicate_inline_mrca_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code = main(
                [
                    "find",
                    "--alignment",
                    str(FIXTURES / "simple.nex"),
                    "--tree",
                    str(FIXTURES / "simple.nwk"),
                    "--outgroup",
                    "Outgroup",
                    "--mrca",
                    "A",
                    "A",
                    "--output",
                    str(root / "results.tsv"),
                    "--members-output",
                    str(root / "members.txt"),
                    "--report",
                    str(root / "report.json"),
                ]
            )
            self.assertEqual(code, 2)
            self.assertFalse((root / "results.tsv").exists())
            self.assertFalse((root / "members.txt").exists())
            self.assertFalse((root / "report.json").exists())


    def test_name_file_allows_comments_blank_lines_and_outer_whitespace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "names.txt"
            path.write_text("# comment\n\n  A  \nB\n", encoding="utf-8-sig")
            self.assertEqual(_read_name_file(path), {"A", "B"})

    def test_name_file_rejects_empty_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "names.txt"
            path.write_text("# comment only\n\n", encoding="utf-8")
            with self.assertRaisesRegex(SelectionError, "contains no names"):
                _read_name_file(path)

    def test_name_file_rejects_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "names.txt"
            path.write_text("A\nB\nA\n", encoding="utf-8")
            with self.assertRaisesRegex(SelectionError, r"duplicate name\(s\): A"):
                _read_name_file(path)

    def test_non_utf8_name_file_is_user_facing_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad_names = root / "bad_names.txt"
            bad_names.write_bytes(b"A\n\xff\n")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
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
                        str(bad_names),
                        "--output",
                        str(root / "results.tsv"),
                        "--members-output",
                        str(root / "members.txt"),
                        "--report",
                        str(root / "report.json"),
                    ]
                )
            self.assertEqual(code, 2)
            self.assertIn("Could not decode taxon list", stderr.getvalue())
            self.assertIn("as UTF-8", stderr.getvalue())

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

    def test_text_outputs_use_lf_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results = root / "results.tsv"
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
                    str(results),
                    "--members-output",
                    str(members),
                    "--report",
                    str(report),
                ]
            )

            self.assertEqual(code, 0)

            for output in (results, members, report):
                data = output.read_bytes()
                self.assertNotIn(b"\r\n", data)
                self.assertTrue(data.endswith(b"\n"))

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
