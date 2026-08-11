from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from branchsnv.errors import NexusFormatError
from branchsnv.nexus import read_transposed_nexus


FIXTURES = Path(__file__).parent / "fixtures"


class NexusTests(unittest.TestCase):
    def test_reads_transposed_matrix(self) -> None:
        alignment = read_transposed_nexus(FIXTURES / "simple.nex")
        self.assertEqual(alignment.ntax, 5)
        self.assertEqual(alignment.nchar, 6)
        self.assertEqual(alignment.taxa, ("Outgroup", "A", "B", "C", "D"))
        self.assertEqual(alignment.sites[0].site_id, "ref_1")
        self.assertEqual(alignment.sites[0].states, "GAAGG")

    def test_accepts_compact_states_and_comments(self) -> None:
        text = """#NEXUS
        [outer [nested] comment]
        BEGIN CHARACTERS;
        DIMENSIONS NTAX=4 NCHAR=1;
        FORMAT TRANSPOSE SYMBOLS='ACGT' GAP=. MISSING=?;
        TAXLABELS 'tax one' B C D;
        MATRIX
        site_1 ACGT
        ;
        END;
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.nex"
            path.write_text(text, encoding="utf-8")
            alignment = read_transposed_nexus(path)
        self.assertEqual(alignment.taxa[0], "tax one")
        self.assertEqual(alignment.sites[0].states, "ACGT")

    def test_rejects_non_transposed_matrix(self) -> None:
        text = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=2 NCHAR=1;
        FORMAT SYMBOLS='ACGT';
        TAXLABELS A B;
        MATRIX site_1 A C;
        END;
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(NexusFormatError, "TRANSPOSE"):
                read_transposed_nexus(path)


    def test_rejects_explicit_transpose_no(self) -> None:
        text = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=2 NCHAR=1;
        FORMAT TRANSPOSE=NO SYMBOLS='ACGT';
        TAXLABELS A B;
        MATRIX site_1 A C;
        END;
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(NexusFormatError, "TRANSPOSE"):
                read_transposed_nexus(path)

    def test_accepts_explicit_transpose_yes(self) -> None:
        text = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=2 NCHAR=1;
        FORMAT TRANSPOSE=YES SYMBOLS='ACGT';
        TAXLABELS A B;
        MATRIX site_1 A C;
        END;
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.nex"
            path.write_text(text, encoding="utf-8")
            alignment = read_transposed_nexus(path)
        self.assertEqual(alignment.sites[0].states, "AC")

    def test_rejects_invalid_gap_and_missing_symbols(self) -> None:
        directives = [
            "GAP=XX MISSING=?",
            "GAP='' MISSING=?",
            "GAP=- MISSING='??'",
            "GAP=- MISSING=''",
            "GAP=a MISSING=A",
            "GAP=A MISSING=?",
            "GAP=- MISSING=N",
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            for directive in directives:
                with self.subTest(directive=directive):
                    text = f"""#NEXUS
                    BEGIN DATA;
                    DIMENSIONS NTAX=2 NCHAR=1;
                    FORMAT TRANSPOSE SYMBOLS='ACGT' {directive};
                    TAXLABELS A B;
                    MATRIX site_1 A C;
                    END;
                    """
                    path.write_text(text, encoding="utf-8")
                    with self.assertRaises(NexusFormatError):
                        read_transposed_nexus(path)

    def test_reports_non_utf8_input_as_nexus_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            path.write_bytes(b"#NEXUS\nBEGIN DATA;\xff")
            with self.assertRaisesRegex(NexusFormatError, "UTF-8"):
                read_transposed_nexus(path)

    def test_rejects_wrong_state_count(self) -> None:
        text = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=3 NCHAR=1;
        FORMAT TRANSPOSE SYMBOLS='ACGT';
        TAXLABELS A B C;
        MATRIX site_1 A C;
        END;
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(NexusFormatError, "expected 3"):
                read_transposed_nexus(path)

    def test_rejects_duplicate_taxa_and_sites(self) -> None:
        duplicate_taxa = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=2 NCHAR=1;
        FORMAT TRANSPOSE SYMBOLS='ACGT';
        TAXLABELS A A;
        MATRIX site_1 A C;
        END;
        """
        duplicate_sites = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=2 NCHAR=2;
        FORMAT TRANSPOSE SYMBOLS='ACGT';
        TAXLABELS A B;
        MATRIX
        site_1 A C
        site_1 G T
        ;
        END;
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            path.write_text(duplicate_taxa, encoding="utf-8")
            with self.assertRaisesRegex(NexusFormatError, "Duplicate taxon"):
                read_transposed_nexus(path)
            path.write_text(duplicate_sites, encoding="utf-8")
            with self.assertRaisesRegex(NexusFormatError, "Duplicate matrix site"):
                read_transposed_nexus(path)

    def test_allows_explicit_interleave_no(self) -> None:
        text = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=2 NCHAR=1;
        FORMAT TRANSPOSE INTERLEAVE=NO SYMBOLS='ACGT';
        TAXLABELS A B;
        MATRIX site_1 A C;
        END;
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.nex"
            path.write_text(text, encoding="utf-8")
            alignment = read_transposed_nexus(path)
        self.assertEqual(alignment.sites[0].states, "AC")

    def test_rejects_multiple_data_blocks(self) -> None:
        text = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=2 NCHAR=1;
        FORMAT TRANSPOSE SYMBOLS='ACGT';
        TAXLABELS A B;
        MATRIX site_1 A C;
        END;
        BEGIN CHARACTERS;
        DIMENSIONS NTAX=2 NCHAR=1;
        FORMAT TRANSPOSE SYMBOLS='ACGT';
        TAXLABELS A B;
        MATRIX site_2 G T;
        END;
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(NexusFormatError, "Multiple DATA/CHARACTERS"):
                read_transposed_nexus(path)

    def test_reports_exact_matrix_row_line_number(self) -> None:
        text = """#NEXUS
BEGIN DATA;
DIMENSIONS NTAX=2 NCHAR=1;
FORMAT TRANSPOSE SYMBOLS='ACGT';
TAXLABELS A B;
MATRIX
site_only
;
END;
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(
                NexusFormatError, r"Matrix row near line 7 must contain"
            ):
                read_transposed_nexus(path)

    def test_rejects_matchchar_and_equate_directives(self) -> None:
        templates = [
            "MATCHCHAR=.",
            "EQUATE='X=A'",
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            for directive in templates:
                text = f"""#NEXUS
                BEGIN DATA;
                DIMENSIONS NTAX=2 NCHAR=1;
                FORMAT TRANSPOSE SYMBOLS='ACGT' {directive};
                TAXLABELS A B;
                MATRIX site_1 A C;
                END;
                """
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(NexusFormatError):
                    read_transposed_nexus(path)

    def test_rejects_explicit_non_nucleotide_datatype(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            for datatype in ("PROTEIN", "STANDARD", "RNA"):
                with self.subTest(datatype=datatype):
                    text = f"""#NEXUS
                    BEGIN DATA;
                    DIMENSIONS NTAX=2 NCHAR=1;
                    FORMAT DATATYPE={datatype} TRANSPOSE SYMBOLS='ACGT';
                    TAXLABELS A B;
                    MATRIX site_1 A C;
                    END;
                    """
                    path.write_text(text, encoding="utf-8")
                    with self.assertRaisesRegex(NexusFormatError, "DATATYPE"):
                        read_transposed_nexus(path)

    def test_accepts_explicit_nucleotide_datatype(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.nex"
            for datatype in ("DNA", "NUCLEOTIDE"):
                with self.subTest(datatype=datatype):
                    text = f"""#NEXUS
                    BEGIN DATA;
                    DIMENSIONS NTAX=2 NCHAR=1;
                    FORMAT DATATYPE={datatype} TRANSPOSE SYMBOLS='ACGT';
                    TAXLABELS A B;
                    MATRIX site_1 A C;
                    END;
                    """
                    path.write_text(text, encoding="utf-8")
                    alignment = read_transposed_nexus(path)
                    self.assertEqual(alignment.sites[0].states, "AC")

    def test_rejects_empty_taxon_and_site_labels(self) -> None:
        empty_taxon = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=2 NCHAR=1;
        FORMAT TRANSPOSE SYMBOLS='ACGT';
        TAXLABELS '' B;
        MATRIX site_1 A C;
        END;
        """
        empty_site = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=2 NCHAR=1;
        FORMAT TRANSPOSE SYMBOLS='ACGT';
        TAXLABELS A B;
        MATRIX '' A C;
        END;
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            path.write_text(empty_taxon, encoding="utf-8")
            with self.assertRaisesRegex(NexusFormatError, "Taxon labels must not be empty"):
                read_transposed_nexus(path)
            path.write_text(empty_site, encoding="utf-8")
            with self.assertRaisesRegex(NexusFormatError, "empty site identifier"):
                read_transposed_nexus(path)

    def test_rejects_line_breaks_in_taxon_labels(self) -> None:
        text = """#NEXUS
        BEGIN DATA;
        DIMENSIONS NTAX=2 NCHAR=1;
        FORMAT TRANSPOSE SYMBOLS='ACGT';
        TAXLABELS 'A
B' C;
        MATRIX site_1 A C;
        END;
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.nex"
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(NexusFormatError, "line breaks"):
                read_transposed_nexus(path)


if __name__ == "__main__":
    unittest.main()
