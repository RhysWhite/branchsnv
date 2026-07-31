# Schemas

`branchsnv-report.schema.json` describes provenance report schema version 1
using JSON Schema draft 2020-12.

The schema is documentation and an integration aid; BRANCHSNV has no JSON Schema
runtime dependency. Workflows may validate reports with any compatible external
validator.

A future incompatible report structure must increment `schema_version` and add
a new schema file rather than changing version 1 in place.
