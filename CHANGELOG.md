# Changelog

All notable changes to BRANCHSNV will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and release identifiers follow PEP 440 conventions.

## [Unreleased]

## [0.1.0] - 2026-08-12

### Added

- Expanded production regression coverage for ambiguous focal-edge state changes,
  branch-selection failures, taxon-list parsing, path aliases, deep Newick trees,
  quote-aware NEXUS block detection, and provenance-schema constraints.

### Changed

- Reframed repository validation documentation around the independent
  `branchsnv-validation` publication framework and its six committed experiment
  layers, while distinguishing the historical v0.1.0a1 publication snapshot from
  validation of the current release candidate.
- Tightened the JSON report schema so rooting, branch-selection, and analysis
  parameter provenance must match forms BRANCHSNV can actually emit.
- Updated release guidance so stable releases are validated against the exact
  release candidate before downstream packaging.
- Removed the obsolete development-only GitHub setup document from the public
  source package.

### Fixed

- Hardened transposed-NEXUS validation for explicit transpose settings, nucleotide
  datatype declarations, gap/missing symbols, empty labels, malformed UTF-8, and
  exact matrix-row diagnostics.
- Made NEXUS DATA-block detection quote-aware so quoted `BEGIN DATA;` or `END;`
  text is not interpreted as file structure.
- Hardened Newick input handling for malformed UTF-8 and taxon labels that cannot
  be represented safely in branch-membership provenance.
- Removed Python recursion-depth limits from deep Newick parsing and rerooting.
- Hardened taxon-list diagnostics and duplicate inline outgroup/MRCA rejection.
- Prevented failed multi-output writes from leaking staged temporary files and
  added path-alias rejection coverage.
- Corrected manual release-workflow dispatch so the requested tag is checked out,
  verified against `HEAD`, and used to name the release artifact.

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
