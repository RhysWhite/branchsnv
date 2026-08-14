# BRANCHSNV

BRANCHSNV is a dependency-free Python command-line tool for interrogating one selected branch of a rooted bacterial phylogeny using a transposed NEXUS SNV matrix.

It reports two properties separately:

- **strict clade-exclusive nucleotide markers**, defined from the observed tip states; and
- **substitutions reconstructed on the focal edge**, evaluated across all globally optimal equal-cost Sankoff parsimony reconstructions.

This separation prevents clade exclusivity from being treated as equivalent to substitution placement on a branch.

## Installation

BRANCHSNV requires Python 3.10 or later. The stable v0.1.0 release can be installed directly from its immutable Git tag:

```bash
git clone https://github.com/RhysWhite/branchsnv.git
cd branchsnv
git checkout v0.1.0
python -m pip install .
branchsnv --version
```

Additional package-manager installation routes are linked from the main repository as they become available.

## Start here

- [Input formats](input-formats.md): accepted NEXUS and Newick input scope.
- [Branch selection](branch-selection.md): exact descendant sets, MRCA selection, deterministic branch IDs, and rooting.
- [Algorithm](algorithm.md): clade-exclusivity logic and equal-cost Sankoff reconstruction.
- [Interpretation](interpretation.md): what BRANCHSNV results do and do not imply.
- [Workflow integration](workflow-integration.md): use in reproducible pipelines.
- [Validation](validation.md): production testing and independent publication validation.
- [Code walkthrough](code-walkthrough/README.md): line-by-line implementation documentation.

## Citation and archival record

The stable software release is archived in Zenodo with DOI **10.5281/zenodo.21919038**. Citation metadata are also provided in `CITATION.cff` in the source repository.
