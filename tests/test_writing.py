from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from branchsnv.errors import ValidationError
from branchsnv.writing import AtomicOutputSet


class AtomicOutputSetTests(unittest.TestCase):

    def test_rejects_output_path_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "results.tsv"
            alias = root / "nested" / ".." / "results.tsv"

            with self.assertRaisesRegex(ValidationError, "Output paths must be distinct"):
                with AtomicOutputSet([target, alias]):
                    pass

            self.assertFalse(target.exists())
            self.assertFalse((root / "nested").exists())

    def test_existing_later_target_does_not_leak_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.tsv"
            second = root / "second.tsv"
            second.write_text("existing\n", encoding="utf-8")

            with self.assertRaisesRegex(ValidationError, "Output already exists"):
                with AtomicOutputSet([first, second], force=False):
                    pass

            self.assertEqual(sorted(path.name for path in root.iterdir()), ["second.tsv"])

    def test_staging_failure_cleans_already_created_temporary_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.tsv"
            second = root / "second.tsv"
            real_mkstemp = tempfile.mkstemp
            calls = 0

            def fail_on_second(*args: object, **kwargs: object) -> tuple[int, str]:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated staging failure")
                return real_mkstemp(*args, **kwargs)

            with patch("branchsnv.writing.tempfile.mkstemp", side_effect=fail_on_second):
                with self.assertRaisesRegex(OSError, "simulated staging failure"):
                    with AtomicOutputSet([first, second]):
                        pass

            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
