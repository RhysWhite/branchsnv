# 10 — Maintenance observations and release checklist

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `src/branchsnv/*.py`, `tests/test_*.py`  
**Last checked against source:** 5 August 2026

This chapter records implementation details that are easy to forget. They are separated from the literal walkthrough so current behaviour is not confused with a recommendation to change it.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## Current behaviours worth preserving deliberately

1. **Branch identity is membership-based.** Internal labels and branch lengths do not identify branches.
2. **Rooting happens before selection.** Descendants and parent→child direction are rooted concepts.
3. **Strict marker calls require complete callability on both sides.** Missing outside data cannot be interpreted as absence.
4. **Gap and missing are unknown among four nucleotide states.** They are not a fifth state.
5. **All optimal focal-edge pairs are retained.** No arbitrary traceback is selected.
6. **Status counts include every site.** Reporting filters are applied after reconstruction/counting.
7. **The `possible_pairs` field is authoritative for ambiguity.** `change` is a display summary that omits no-change pairs.
8. **Provenance avoids timestamps and absolute paths.** Identical content and parameters can reproduce identical output bytes.

## Detailed maintenance observations

### 1. GAP and MISSING length validation is weaker than the error message implies

In `_parse_format`, the code takes `[0]` from the unquoted GAP/MISSING token before checking `len(gap)` and `len(missing)`. Consequently:

- `GAP=XX` becomes `X` and passes the later one-character check;
- an empty quoted value can raise `IndexError` rather than `NexusFormatError`.

This is current source behaviour, not the intended contract expressed by the error text. A future hardening change should validate the entire unquoted token first, then extract nothing. Add focused tests before changing it.

### 2. Case-only GAP/MISSING collisions can survive the distinctness check

The parser compares GAP and MISSING before uppercasing them for the `Alignment`. A configuration such as lowercase `a` versus uppercase `A` is distinct during `_parse_format` but becomes the same stored symbol. Typical NEXUS files use punctuation, so this is an edge case. It should either be explicitly forbidden or documented if format flexibility is expanded.

### 3. `FORMAT SYMBOLS` is recorded but does not define the complete accepted matrix alphabet

Matrix validation always accepts the built-in `_IUPAC` set plus gap/missing. It does not restrict states to the declared SYMBOLS string, and custom non-IUPAC symbols listed in SYMBOLS remain unsupported. This is consistent with BRANCHSNV's nucleotide-only purpose but should remain explicit.

### 4. Inline outgroup duplicates are silently collapsed

`_root_tree` converts `args.outgroup` directly to a set. Name files and `--mrca` explicitly reject duplicates. This inconsistency does not change the selected set, but a focused validation rule would improve input diagnostics.

### 5. Multi-file output commit is not one indivisible filesystem transaction

Every individual `os.replace(temp, target)` is atomic on the relevant filesystem. The three `find` outputs are replaced sequentially. If the process or filesystem fails between replacements, a mixed old/new output set is possible. Staging does guarantee that normal analysis or writer errors before `commit()` leave final targets untouched.

A stronger all-files transaction would need a different publication strategy, such as writing into a versioned directory and atomically switching one directory-level pointer where supported, or a rollback journal. The current report accurately hashes the staged results and member bytes.

### 6. `AtomicOutputSet.__enter__` can leave a temporary file if setup fails after an earlier target

Context-manager `__exit__` is not called when `__enter__` raises. Because existing-target checks and temporary-file creation are interleaved, a failure on a later target can leave a previously created hidden `.tmp` file. A future change could first validate all targets and parent directories, then create all temporary files inside a guarded cleanup block.

### 7. No `fsync` durability step is performed

Files are closed before replacement, but the code does not explicitly flush file contents and directory metadata to stable storage with `fsync`. This is normal for many scientific command-line utilities; it matters only for strong crash/power-loss durability claims. Do not describe the outputs as power-loss transactional without adding such handling.

### 8. Newick quote support is single-quote specific

`_parse_optional_label` implements Newick single-quoted labels and doubled single-quote escapes. Double quotes are not a supported quoting mechanism in this parser. Documentation should not imply otherwise.

### 9. Negative finite branch lengths parse

The parser requires finite numbers but does not require non-negative values. Since BRANCHSNV ignores branch lengths analytically, this does not alter SNV reconstruction. It does affect what the parser accepts and how lengths are combined/split during rerooting.

### 10. NEXUS block finding is regex-based rather than a complete document grammar

The parser is deliberately a strict subset. `BEGIN DATA` and `END` detection is not a fully quote-aware parse of every possible NEXUS construct outside the supported block. Keep input documentation narrow and avoid claiming general NEXUS compliance.

### 11. `analyse_branch` always runs parsimony, including fixed-exclusive mode

This supplies parsimony fields and complete status counts even when only fixed-exclusive rows are selected. It also means fixed-exclusive-only execution does not avoid reconstruction cost. Any optimisation to skip parsimony would change output/report content unless the schema and semantics were redesigned.

### 12. `exclusive_to_clade` includes fixation in its current implementation

The variable `exclusive` is defined with `fixed_within` as a prerequisite. Therefore an output row cannot have `exclusive_to_clade=true` and `fixed_within_clade=false`. The later `fixed_exclusive = fixed_within and exclusive` is redundant. Preserve this field meaning or explicitly version the output contract if changing it.

### 13. `_INF` is finite

Incompatible leaf states receive cost `10**8`. This is safely larger than any plausible bacterial tree parsimony score, but it is not mathematical infinity. An impossibly enormous tree with more than 100 million changes could undermine the sentinel assumption. This is not a practical dataset limit; it is an implementation fact.

### 14. Compilation validates tree tips are in the alignment, not the reverse

`compile_tree` protects programmatic calls by checking every tip name in the alignment index. Exact absence of extra alignment taxa is enforced separately by `validate_compatibility` in the CLI workflow. Direct API callers should run compatibility validation first.

### 15. NEXUS command start-line tracking is only approximate

`_split_commands` records a `start_line` for each semicolon-terminated command. The nested condition intended to advance that value after a newline cannot be reached with the current cursor/update order. As a result, a MATRIX command may retain the line number of the preceding command's terminating semicolon rather than the first line of MATRIX content. This affects only diagnostic wording such as “near line …”; it does not alter parsed states or site order. A focused test could pin the intended line-reporting behaviour before changing it.

### 16. Source line numbers are release-specific

Any source edit can shift lines even when behaviour is unchanged. This walkthrough is pinned to commit `582d3883d39adb8c591d9eb152143227c9696eec`; do not update its line references to `main` while leaving the documented version as `0.1.0a1`.

## Release update checklist

For a later release:

1. Copy this directory to `docs/code-walkthrough/<new-version>/`.
2. Replace the version and full commit identifier in every document.
3. Regenerate all numbered snippets from the new source; never hand-shift line numbers.
4. Follow the real CLI call path and update behaviour, not just code text.
5. Re-run the complete test suite and record the exact count.
6. Update `09-test-to-code-map.md` from actual test methods.
7. Review every observation above and mark it as unchanged, fixed, or superseded.
8. Run a coverage checker ensuring every production source line is assigned.
9. Check all relative Markdown links.
10. Add the new walkthrough link to the root README while preserving this versioned record.

## Suggested focused tests before the next stable release

The highest-value additions from this review are:

- reject empty and multi-character GAP/MISSING with `NexusFormatError`;
- reject case-normalised GAP/MISSING equality;
- reject duplicate inline outgroup names consistently;
- verify ambiguous/nonexistent branch ID prefix errors;
- verify MRCA-at-root error;
- test output/output alias rejection;
- test cleanup when a later output setup/write fails;
- add an explicit `change_state_ambiguous` fixture;
- test `_read_name_file` comments, empty file, and duplicate diagnostics;
- test exact MATRIX diagnostic line numbers across command-separating newlines.
