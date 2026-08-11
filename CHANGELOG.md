# Changelog

All notable changes to BRANCHSNV will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and releases use semantic versioning.

## [Unreleased]

## [0.1.0] - 2026-08-12

### Changed

- Reframed repository validation documentation around the independent
  `branchsnv-validation` publication framework and its six committed experiment
  layers.
- Updated the production validation report to the current 42-test suite and
  separated publication validation from the legacy AK3 working-data regression
  fixture.
- Updated release guidance so stable releases are validated against the exact
  release candidate before downstream packaging.
- Removed the obsolete development-only GitHub setup document from the public
  source package.

## [0.1.0a1] - 2026-07-31


### Fixed

- Enforced LF line endings for branch-membership and JSON provenance outputs
  on Windows, preserving byte-identical cross-platform results.

### Added

- Strict parsing of transposed nucleotide NEXUS matrices.
- Strict parsing of rooted Newick trees, including quoted labels, comments,
  branch lengths, and multifurcations.
- Explicit rooting by a monophyletic outgroup or acceptance of an existing root.
- Branch selection by exact descendant list, MRCA, or deterministic branch ID.
- Fixed-exclusive clade-marker analysis.
- Exact equal-cost Sankoff reconstruction across a selected branch, retaining
  all globally optimal parent-child state pairs.
- Deterministic TSV, branch-membership, and JSON provenance outputs.
- Atomic output replacement and refusal to overwrite without `--force`.
- Standard-library unit tests, generated oracle comparisons, fault-regression
  fixtures, and an AK3 working-dataset validation recipe.
