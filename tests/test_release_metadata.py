"""Tests for agreement among BRANCHSNV release metadata files."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import branchsnv


ROOT = Path(__file__).resolve().parents[1]


def extract(pattern: str, path: Path, label: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(pattern, text, flags=re.MULTILINE)

    if match is None:
        raise AssertionError(f"Could not find {label} in {path}")

    return match.group(1)


class ReleaseMetadataTests(unittest.TestCase):
    def test_versions_agree(self) -> None:
        pyproject_version = extract(
            r'^version\s*=\s*"([^"]+)"\s*$',
            ROOT / "pyproject.toml",
            "project version",
        )
        citation_version = extract(
            r'^version:\s*"?([^"\s]+)"?\s*$',
            ROOT / "CITATION.cff",
            "citation version",
        )

        self.assertEqual(pyproject_version, branchsnv.__version__)
        self.assertEqual(citation_version, branchsnv.__version__)

    def test_project_names_are_consistent(self) -> None:
        distribution_name = extract(
            r'^name\s*=\s*"([^"]+)"\s*$',
            ROOT / "pyproject.toml",
            "distribution name",
        )
        citation_title = extract(
            r'^title:\s*"([^"]+)"\s*$',
            ROOT / "CITATION.cff",
            "citation title",
        )

        self.assertEqual(distribution_name, "branchsnv")
        self.assertEqual(citation_title, "BRANCHSNV")


if __name__ == "__main__":
    unittest.main()
