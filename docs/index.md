# BRANCHSNV

BRANCHSNV identifies **strict clade-exclusive nucleotide markers** and
**parsimony-reconstructed substitutions on one selected branch** of a rooted
bacterial phylogeny. These are different claims; see
[Interpretation](interpretation.md) before reporting results.

## Choose a starting point

| I want to… | Start here |
|---|---|
| Install and run the included example | [README: installation and quick start](https://github.com/RhysWhite/branchsnv#installation) |
| Understand NEXUS, Newick or root selection | [Input formats](input-formats.md) and [branch selection](branch-selection.md) |
| Interpret `results.tsv` accurately | [Interpretation](interpretation.md) and [algorithm](algorithm.md) |
| Follow the Python code without prior developer experience | [v0.2.0 code walkthrough](code-walkthrough/v0.2.0/README.md) |
| Put BRANCHSNV in a pipeline | [Workflow integration](workflow-integration.md) |
| Inspect validation claims and reproduce evidence | [Validation strategy](validation.md) and [validation evidence index](https://github.com/RhysWhite/branchsnv-validation/blob/main/EVIDENCE_INDEX.md) |
| Find related methods, publications and tools | [References and related tools](references.md) |

BRANCHSNV does **not** call variants, infer a phylogeny, filter recombination,
or demonstrate an evolutionary or phenotypic cause. Those are upstream or
separate analyses.

## Version and archives

The source tree documents **v0.2.0** (conventional and transposed NEXUS).
The package-installation instructions deliberately distinguish the historical
v0.1.0 packages from the source-identical v0.2.0 reproduction.

- [v0.2.0 software archive](https://doi.org/10.5281/zenodo.23518619)
- [v0.2.0 independent validation archive](https://doi.org/10.5281/zenodo.23518684)
- [Experiment 07 benchmark v0.3.0](https://doi.org/10.5281/zenodo.23684441) — separate from Experiments 01–06
- [Historical v0.1.0a1 code walkthrough](code-walkthrough/v0.1.0a1/README.md)

Version-specific citation details are in
[`CITATION.cff`](https://github.com/RhysWhite/branchsnv/blob/main/CITATION.cff).
