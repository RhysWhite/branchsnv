from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from branchsnv.errors import ValidationError
from branchsnv.newick import parse_newick
from branchsnv.nexus import read_transposed_nexus
from branchsnv.validation import validate_compatibility


class ValidationTests(unittest.TestCase):
    def test_rejects_taxon_set_mismatch(self) -> None:
        text = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=2 NCHAR=1;
        FORMAT TRANSPOSE SYMBOLS='ACGT';
        TAXLABELS A B;
        MATRIX site_1 A C;
        END;
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.nex"
            path.write_text(text, encoding="utf-8")
            alignment = read_transposed_nexus(path)
        tree = parse_newick("(A,C);")
        with self.assertRaisesRegex(ValidationError, "taxon sets differ"):
            validate_compatibility(alignment, tree)


if __name__ == "__main__":
    unittest.main()
