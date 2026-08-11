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

    def test_provenance_contract_closes_rooting_selection_and_parameters(self) -> None:
        path = Path(__file__).parents[1] / "schemas" / "branchsnv-report.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))

        rooting = schema["properties"]["rooting"]
        self.assertEqual(
            rooting["oneOf"],
            [
                {"$ref": "#/$defs/rootingExistingRoot"},
                {"$ref": "#/$defs/rootingOutgroup"},
                {"$ref": "#/$defs/rootingOutgroupFile"},
            ],
        )

        selection = schema["properties"]["branch"]["properties"]["selection"]
        self.assertEqual(
            selection["oneOf"],
            [
                {"$ref": "#/$defs/selectionExactDescendantFile"},
                {"$ref": "#/$defs/selectionMrca"},
                {"$ref": "#/$defs/selectionBranchId"},
            ],
        )

        parameters = schema["properties"]["parameters"]
        self.assertFalse(parameters["additionalProperties"])
        self.assertEqual(parameters["properties"]["mode"]["enum"], ["fixed-exclusive", "parsimony", "both"])
        self.assertEqual(parameters["properties"]["state_cost_model"]["const"], "unordered_equal_cost")
        self.assertEqual(parameters["properties"]["gap_treatment"]["const"], "unknown_state")
        self.assertEqual(parameters["properties"]["missing_treatment"]["const"], "unknown_state")
        self.assertEqual(parameters["properties"]["fixed_exclusive_descendant_call_rate"]["const"], 1.0)
        self.assertEqual(parameters["properties"]["fixed_exclusive_outside_call_rate"]["const"], 1.0)


if __name__ == "__main__":
    unittest.main()
