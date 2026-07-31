from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


class ProcessDeterminismTests(unittest.TestCase):
    def test_outputs_ignore_python_hash_seed(self) -> None:
        observed: list[tuple[bytes, bytes, bytes]] = []
        with tempfile.TemporaryDirectory() as parent:
            for seed in ("1", "987654"):
                directory = Path(parent) / seed
                directory.mkdir()
                result = directory / "results.tsv"
                members = directory / "members.txt"
                report = directory / "report.json"
                environment = os.environ.copy()
                environment["PYTHONHASHSEED"] = seed
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "branchsnv",
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
                    ],
                    check=True,
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                observed.append((result.read_bytes(), members.read_bytes(), report.read_bytes()))
        self.assertEqual(observed[0], observed[1])


if __name__ == "__main__":
    unittest.main()
