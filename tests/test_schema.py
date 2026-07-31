from __future__ import annotations

import json
import unittest
from pathlib import Path


class SchemaTests(unittest.TestCase):
    def test_report_schema_is_valid_json_and_targets_version_one(self) -> None:
        path = Path(__file__).parents[1] / "schemas" / "branchsnv-report.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertIn("branch", schema["required"])
        self.assertIn("outputs", schema["required"])


if __name__ == "__main__":
    unittest.main()
