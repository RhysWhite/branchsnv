# 09 — Test-to-code map

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `tests/test_*.py`, `src/branchsnv/*.py`  
**Last checked against source:** 5 August 2026

This chapter maps committed tests to production behaviours. A passing test establishes the specific assertion it makes; it does not prove every nearby behaviour.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## Current suite

The repository contains 42 `unittest` tests in the uploaded commit. The production walkthrough was checked by running:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Expected result for this source snapshot: `Ran 42 tests` and `OK`.

## Direct behaviour map

| Test | Production behaviour protected | Main source area |
|---|---|---|
| `AnalysisTests.test_default_both_mode_reports_union` | `both` reports union and counts strict/unambiguous sites | `analysis.py` selection and summary |
| `AnalysisTests.test_fixed_exclusive_is_strict_about_missing_descendants` | missing descendant prevents strict fixation | `analysis.py` callable descendant rule |
| `AnalysisTests.test_fixed_exclusive_requires_callable_outside_taxa` | incomplete outside calls prevent exclusivity | `analysis.py` outside call-rate rule |
| `AnalysisTests.test_ambiguous_option_reports_ambiguous_parsimony_sites` | option includes placement-ambiguous rows | `analysis.py` parsimony selection |
| `CliTests.test_validate` | validate command succeeds on fixture | CLI → parsers → rooting → compatibility |
| `CliTests.test_find_outputs_are_deterministic` | two directory runs produce same results/member bytes and same parsed report object | CLI, writers, provenance |
| `CliTests.test_text_outputs_use_lf_line_endings` | all three find outputs use LF and terminal newline | writers |
| `CliTests.test_refuses_to_overwrite_without_force` | existing output survives and command returns 2 | `AtomicOutputSet` + CLI handling |
| `CliTests.test_refuses_to_overwrite_an_input_even_with_force` | input/output alias is rejected despite force | CLI collision guard |
| `NewickTests.test_parses_labels_lengths_comments_and_polytomy` | single-quoted label, lengths, comment, root label, multifurcation | Newick parser |
| `NewickTests.test_rejects_duplicate_tips` | duplicate tip labels fail | Newick validation |
| `NewickTests.test_branch_ids_ignore_sibling_order` | branch membership IDs are child-order independent | descendant sorting + hashing |
| `NewickTests.test_reroots_on_internal_outgroup_and_suppresses_old_root` | correct split, all tips retained, no unary node | rerooting |
| `NewickTests.test_keeps_existing_matching_root` | matching degree-two root returns same tree | reroot early return |
| `NewickTests.test_rejects_non_monophyletic_outgroup` | no matching edge split fails | reroot edge search |
| `NexusTests.test_reads_transposed_matrix` | normal fixture metadata/states parse | NEXUS reader |
| `NexusTests.test_accepts_compact_states_and_comments` | compact state string and comments parse | comment stripper/normaliser |
| `NexusTests.test_rejects_non_transposed_matrix` | missing `TRANSPOSE` fails | FORMAT parser |
| `NexusTests.test_rejects_wrong_state_count` | row width mismatch fails | state normaliser |
| `NexusTests.test_rejects_duplicate_taxa_and_sites` | duplicate taxon and duplicate site IDs fail | NEXUS validation |
| `NexusTests.test_allows_explicit_interleave_no` | explicit false interleave accepted | FORMAT parser |
| `NexusTests.test_rejects_multiple_data_blocks` | multiple DATA/CHARACTERS blocks fail | block finder |
| `NexusTests.test_rejects_matchchar_and_equate_directives` | unsupported directives fail | FORMAT parser |
| `ParsimonyTests.test_clean_branch_change` | unique optimal change pair | reconstruction/classification |
| `ParsimonyTests.test_no_branch_change` | no-change classification | reconstruction/classification |
| `ParsimonyTests.test_parallel_pattern_can_make_placement_ambiguous` | change placement tie retained | pair enumeration |
| `ParsimonyTests.test_missing_descendant_is_not_forced` | missing data is unknown, not forced | leaf costs |
| `ParsimonyTests.test_matches_exhaustive_oracle_for_generated_patterns` | score, pair set, and status agree with independent exhaustive enumeration across generated patterns | whole parsimony algorithm |
| `ProcessDeterminismTests.test_outputs_ignore_python_hash_seed` | raw output bytes stable across two hash seeds and processes | sorting/serialisation |
| `ProvenanceTests.test_report_is_internally_consistent` | schema/tool, output hashes, branch ID relation, count sum, warnings | provenance |
| `FaultRegressionTests.test_catches_wrong_side_of_branch` | parent→child focal edge is not reversed or sibling-side | compiled focal endpoints/pair result |
| `FaultRegressionTests.test_catches_majority_state_substitution_for_parsimony` | majority rule cannot replace exact parsimony | parsimony DP |
| `FaultRegressionTests.test_catches_gap_as_fifth_state` | gap does not become a fifth nucleotide state | leaf unknown treatment |
| `FaultRegressionTests.test_catches_arbitrary_resolution_of_ties` | tied optimal pairs remain multiple | pair retention |
| `ReleaseMetadataTests.test_versions_agree` | package, project, citation versions match | release metadata |
| `ReleaseMetadataTests.test_project_names_are_consistent` | distribution and citation names are expected | release metadata |
| `SchemaTests.test_report_schema_is_valid_json_and_targets_version_one` | schema parses and requires key version-1 sections | JSON Schema metadata |
| `SelectionTests.test_exact_descendants` | exact clade selection returns correct members | exact selector |
| `SelectionTests.test_exact_descendants_rejects_non_monophyly` | non-exact requested set fails | exact selector/MRCA diagnosis |
| `SelectionTests.test_mrca_reports_actual_branch` | MRCA selector returns incoming branch | MRCA selector |
| `SelectionTests.test_branch_id_prefix` | short ID resolves to same node | ID resolver |
| `ValidationTests.test_rejects_taxon_set_mismatch` | exact taxon set mismatch fails | cross-input validation |

## Particularly strong tests

### Exhaustive parsimony oracle

`test_matches_exhaustive_oracle_for_generated_patterns` independently enumerates internal-node assignments for generated tip patterns and compares three endpoints: global score, complete focal-edge pair set, and status. This is stronger than checking only one expected example because it directly challenges tie handling.

### Cross-process determinism

`test_outputs_ignore_python_hash_seed` invokes `python -m branchsnv` in separate processes with different `PYTHONHASHSEED` values and compares raw bytes. This catches hidden dependence on unordered hash-container iteration that same-process object comparisons may miss.

### Fault-regression fixtures

The four regression tests encode patterns that would change under plausible but wrong implementations: analysing the wrong edge side, substituting majority state for parsimony, treating gap as a fifth state, or choosing one tied optimum.

## Behaviours not directly isolated by a dedicated test in this commit

The suite may exercise some of these indirectly, but there is no narrowly named assertion for each:

- duplicate or comment handling in `_read_name_file`;
- duplicate inline outgroup names;
- `--accept-existing-root` with an invalid one-child programmatic tree;
- ambiguous or nonexistent branch ID prefixes;
- an MRCA request resolving to the root;
- branch-ID hash collision guard;
- finite but negative Newick branch lengths;
- nested Newick comments specifically;
- double-quoted Newick labels;
- empty or multi-character GAP/MISSING format values;
- exact NEXUS MATRIX diagnostic line numbers;
- custom SYMBOLS characters outside built-in IUPAC;
- an output/output path collision;
- writer failure before commit and cleanup of all staged files;
- failure partway through sequential multi-file commit;
- `parse_coordinate` edge cases;
- unsupported state passed directly to `reconstruct_site`;
- `change_state_ambiguous` as a dedicated unit pattern separate from exhaustive coverage.

These are not claims that the behaviours are wrong. They identify where a future maintainer cannot point to one focused regression test.

## How to read test evidence

A unit test demonstrates the behaviour of the exact fixture and assertions it contains. The exhaustive oracle substantially broadens parsimony evidence, but no finite suite proves absence of every defect. The validation repository and published-data comparisons complement, rather than replace, these tests.
