# Annotated BRANCHSNV code walkthrough

**Documented release:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Prepared:** 5 August 2026

This is a source-level explanation of BRANCHSNV. It follows the program in the
order a real `branchsnv find` command executes, then maps that behaviour back to
the tests. It is written so that a reader who is not an experienced Python
programmer can still determine:

- what each source statement does;
- why the statement exists in BRANCHSNV;
- what data enter and leave each function;
- which scientific or software invariant it enforces;
- which tests protect the behaviour; and
- where the current implementation has assumptions or maintenance risks.

## How to use this walkthrough

Read `00-execution-map.md` first. Then follow documents 01–10 in order. The
walkthrough is pinned to one commit because source line numbers and behaviour can
change in later releases.

| Order | Document | Main question |
|---:|---|---|
| 00 | [`00-execution-map.md`](00-execution-map.md) | What happens from the shell command to the final files? |
| 01 | [`01-entry-points-and-cli.md`](01-entry-points-and-cli.md) | How is the program installed, how are arguments parsed, and how are commands dispatched? |
| 02 | [`02-models-errors-and-utilities.md`](02-models-errors-and-utilities.md) | What objects carry trees, alignments, branches, and results? |
| 03 | [`03-transposed-nexus-parser.md`](03-transposed-nexus-parser.md) | How is the alignment read and rejected when malformed? |
| 04 | [`04-newick-parser.md`](04-newick-parser.md) | How is Newick text converted into a rooted node structure? |
| 05 | [`05-tree-operations-rooting-and-selection.md`](05-tree-operations-rooting-and-selection.md) | How are descendants, branch IDs, rooting, and branch selection implemented? |
| 06 | [`06-parsimony-reconstruction.md`](06-parsimony-reconstruction.md) | How does BRANCHSNV retain all globally optimal parent–child state pairs? |
| 07 | [`07-branch-analysis.md`](07-branch-analysis.md) | How are fixed-exclusive and parsimony results combined and classified? |
| 08 | [`08-validation-provenance-and-writing.md`](08-validation-provenance-and-writing.md) | How are inputs cross-checked and outputs made deterministic and traceable? |
| 09 | [`09-test-to-code-map.md`](09-test-to-code-map.md) | Which tests protect which behaviours, and what is not directly tested? |
| 10 | [`10-maintenance-observations.md`](10-maintenance-observations.md) | What assumptions, limitations, and possible future hardening points were found? |
| — | [`SOURCE-COVERAGE.md`](SOURCE-COVERAGE.md) | Is every production source line accounted for? |
| — | [`QA-REPORT.md`](QA-REPORT.md) | What checks were run before packaging this walkthrough? |

## Verification performed

- The archive comment identifies source commit `582d3883d39adb8c591d9eb152143227c9696eec`.
- No production source or test file was changed while preparing this walkthrough.
- All 42 committed tests passed under Python 3.13.5 using `PYTHONPATH=src python -m unittest discover -s tests -v`.
- All 1,862 physical lines across the 13 production Python modules are accounted for; every non-blank source line appears in an exact numbered snippet.
- Every local Markdown link in the walkthrough and root README resolves to an existing file.
- All walkthrough Markdown files were parsed successfully with a CommonMark/GFM-compatible parser during preparation.

## Scope

Included:

- `pyproject.toml` command entry point;
- all Python modules in `src/branchsnv/`;
- the relationship between production code and the committed test suite.

Not expanded line by line:

- GitHub Actions, packaging metadata beyond the executable entry point;
- example input files and expected outputs;
- validation shell scripts;
- the JSON Schema itself.

Those materials are referenced where they protect or constrain production
behaviour.

## Terminology used here

- **Source line** means the numbered line in the pinned commit.
- **Statement** means one complete Python operation. A statement can span several
  source lines.
- **Invariant** means a condition that must remain true for the implementation to
  be scientifically or operationally correct.
- **Maintenance observation** means a current behaviour worth remembering. It is
  not automatically a defect.

## Updating this documentation

Do not silently edit this directory to describe a later implementation. Preserve
it as the record of `v0.1.0a1`, then create a new versioned directory for a later
release. The update checklist is in
[`10-maintenance-observations.md`](10-maintenance-observations.md#release-update-checklist).
