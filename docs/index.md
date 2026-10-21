# BRANCHSNV

**BRANCHSNV v0.2.0 archival records:** [software (10.5281/zenodo.23518619)](https://doi.org/10.5281/zenodo.23518619) · [independent validation and reproduction (10.5281/zenodo.23518684)](https://doi.org/10.5281/zenodo.23518684).

BRANCHSNV is a dependency-free Python command-line tool for interrogating one selected branch of a rooted bacterial phylogeny using a nucleotide NEXUS SNV matrix in conventional or transposed orientation.

It reports two properties separately:

- **strict clade-exclusive nucleotide markers**, defined from the observed tip states; and
- **substitutions reconstructed on the focal edge**, evaluated across all globally optimal equal-cost Sankoff parsimony reconstructions.

This separation prevents clade exclusivity from being treated as equivalent to substitution placement on a branch.

## Installation

See the [version-pinned installation instructions](../README.md#installation).
They distinguish the independently validated v0.1.0 release from this
v0.2.0 source checkout, which adds conventional NEXUS support. See the
[validation record](validation.md) for the scope of independent testing.

## Start here

- [Input formats](input-formats.md): accepted NEXUS and Newick input scope.
- [Branch selection](branch-selection.md): exact descendant sets, MRCA selection, deterministic branch IDs, and rooting.
- [Algorithm](algorithm.md): clade-exclusivity logic and equal-cost Sankoff reconstruction.
- [Interpretation](interpretation.md): what BRANCHSNV results do and do not imply.
- [Workflow integration](workflow-integration.md): use in reproducible pipelines.
- [Validation](validation.md): production testing and independent publication validation.
- [Current implementation map](implementation-map.md): concise source-to-algorithm navigation for v0.2.0.
- [Historical code walkthrough](code-walkthrough/README.md): source-specific documentation for v0.1.0a1 only.

## Citation and archival record

The stable software release is archived in Zenodo with DOI **10.5281/zenodo.21919038**. Citation metadata are also provided in `CITATION.cff` in the source repository.
