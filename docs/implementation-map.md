# Implementation map (v0.2.0)

This map follows a single invocation of the v0.2.0 command-line implementation.
It is an orientation guide, not a substitute for the [algorithm specification](algorithm.md)
or the [source-specific validation record](validation.md).

```text
NEXUS + rooted Newick
        |
        v
parse and validate -> resolve rooting -> select one focal edge
        |                                      |
        +-> observed clade states              +-> global parsimony optimum
        |                                      +-> all optimal focal-edge pairs
        v                                      v
strict fixed-exclusive marker          focal-edge change classification
        |                                      |
        +-----------------+--------------------+
                          v
                   TSV + members + JSON
                 (content hashes and inputs)
```

| Stage | Source | Scientific invariant | Independent evidence |
|---|---|---|---|
| Command and selection | [`cli.py`](../src/branchsnv/cli.py) | One selected edge; explicit rooting | [validation Experiments 01–02](https://github.com/RhysWhite/branchsnv-validation/tree/main/experiments) |
| Nucleotide matrix | [`nexus.py`](../src/branchsnv/nexus.py) | Accept conventional and transposed NEXUS; normalize to one site model | Production NEXUS orientation tests; see `tests/` |
| Phylogeny | [`newick.py`](../src/branchsnv/newick.py), [`models.py`](../src/branchsnv/models.py) | Exact taxa, root, descendants, deterministic IDs | Validation Experiment 02 |
| Strict marker | [`analysis.py`](../src/branchsnv/analysis.py) | Every ingroup and outgroup observation must be callable for a marker | Validation Experiments 01–02 and 06 |
| Edge substitutions | [`parsimony.py`](../src/branchsnv/parsimony.py) | Retain **all** globally optimal equal-cost Sankoff parent-child state pairs | Validation Experiment 01 oracle |
| Output | [`writing.py`](../src/branchsnv/writing.py), [`provenance.py`](../src/branchsnv/provenance.py) | Deterministic files, no silent overwriting, source/input checksums | Production regression tests |

## Interpretation boundaries

- `fixed-exclusive` is a property of the observed dataset, not an inference of
  ancestral substitution placement.
- `unambiguous_change` means one optimal parent-child nucleotide pair differs;
  it is not an estimate of all actual historical substitutions, nor proof of
  unique mutation placement under another evolutionary model.
- `change_state_ambiguous` and `placement_ambiguous` retain non-identifiability
  rather than selecting one convenient ancestral reconstruction.
- Missing, gaps and IUPAC ambiguity are interpreted according to the
  [input specification](input-formats.md) and [algorithm](algorithm.md).
- BRANCHSNV does not infer the tree, remove recombination, call variants or
  annotate biological consequences.

## Version boundaries

The implementation here describes **v0.2.0**. The committed independent six-
experiment stable validation record tests **v0.1.0**, not v0.2.0. The additional
conventional-NEXUS parser is regression-tested in production, but needs a
version-specific independently reproduced release-validation record before
v0.2.0 is claimed to have the same archival validation status.

The historical [v0.1.0a1 code walkthrough](code-walkthrough/README.md) is
preserved for reproducibility. Do not treat its individual source-line mapping
as current to v0.2.0.
