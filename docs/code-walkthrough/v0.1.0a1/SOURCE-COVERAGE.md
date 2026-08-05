# Source coverage ledger

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `pyproject.toml`, `src/branchsnv/*.py`  
**Last checked against source:** 5 August 2026

This ledger shows where every production source line in the documented snapshot is explained. Blank lines are formatting and are included within the enclosing ranges.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## Coverage by file

| File | Lines | Walkthrough document | Covered ranges |
|---|---:|---|---|
| `pyproject.toml` | 52 | `01-entry-points-and-cli.md` | executable entry point 45–46 only; other packaging metadata is outside stated scope |
| `src/branchsnv/__init__.py` | 3 | `01-entry-points-and-cli.md` | 1–3 |
| `src/branchsnv/__main__.py` | 3 | `01-entry-points-and-cli.md` | 1–3 |
| `src/branchsnv/cli.py` | 286 | `01-entry-points-and-cli.md` | 1–286 |
| `src/branchsnv/errors.py` | 21 | `02-models-errors-and-utilities.md` | 1–21 |
| `src/branchsnv/models.py` | 119 | `02-models-errors-and-utilities.md` | 1–119 |
| `src/branchsnv/util.py` | 32 | `02-models-errors-and-utilities.md` | 1–32 |
| `src/branchsnv/nexus.py` | 317 | `03-transposed-nexus-parser.md` | 1–317 |
| `src/branchsnv/newick.py` | 421 | `04-newick-parser.md`, `05-tree-operations-rooting-and-selection.md` | 1–186, 189–421; lines 187–188 are blank separators |
| `src/branchsnv/parsimony.py` | 214 | `06-parsimony-reconstruction.md` | 1–214 |
| `src/branchsnv/analysis.py` | 151 | `07-branch-analysis.md` | 1–151 |
| `src/branchsnv/validation.py` | 44 | `08-validation-provenance-and-writing.md` | 1–44 |
| `src/branchsnv/provenance.py` | 90 | `08-validation-provenance-and-writing.md` | 1–90 |
| `src/branchsnv/writing.py` | 161 | `08-validation-provenance-and-writing.md` | 1–161 |

## Production-code total

The 13 Python modules contain **1,862 physical lines**, including blank lines,
docstrings, comments, imports, declarations, and executable statements. All are
covered by the documents above. The command-entry metadata at `pyproject.toml`
lines 45–46 is also covered.

## Interpretation of “line by line”

The walkthrough accounts for every source line, but syntactically inseparable
continuation lines are usually explained as one range. For example, a multi-line
`BranchRecord(...)` constructor is one Python operation and is explained as one
unit. Exact numbered source is reproduced immediately above each explanation so
the reader can still inspect each physical line.
