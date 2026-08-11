# Validation strategy

BRANCHSNV uses layered validation so that confidence in the software does not
depend on one implementation, one dataset, or one successful example.

Production testing and publication validation are deliberately separated. The
production repository contains development-facing tests and regression checks.
The independent publication-validation framework is maintained at
[RhysWhite/branchsnv-validation](https://github.com/RhysWhite/branchsnv-validation)
and records the analyses supporting the manuscript-level validation claims.
The committed publication snapshot described below is retained as a version-pinned
historical record for BRANCHSNV v0.1.0a1.

## Production test suite

The current production suite contains 72 standard-library tests. GitHub Actions
runs the suite on Python 3.10, 3.11, 3.12, 3.13, and 3.14 on Linux, with
additional Python 3.14 jobs on macOS and Windows.

The production tests cover:

- strict transposed NEXUS parsing and malformed-input rejection;
- Newick parsing, explicit rerooting, multifurcations, and duplicate-tip
  rejection;
- exact branch selection, MRCA selection, deterministic branch IDs, and
  non-monophyly rejection;
- exact tree/alignment taxon-name correspondence;
- strict fixed-exclusive marker rules, including descendant and outside-taxon
  callability;
- focal-edge equal-cost Sankoff reconstruction;
- generated comparisons against an independent exhaustive internal-state
  oracle;
- permanent fault-regression examples;
- deterministic output across distinct `PYTHONHASHSEED` values;
- LF line-ending consistency;
- overwrite and input/output collision protection;
- provenance checksum and count consistency;
- report-schema integrity; and
- release-metadata consistency.

Run the production suite from the repository root with:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Independent publication validation

The separate publication-validation repository exists so that independent
or deliberately incorrect validation implementations cannot alter the
production code being tested. The currently committed publication snapshot
evaluates BRANCHSNV v0.1.0a1; it is a historical snapshot rather than a claim
that the current 0.1.0 release candidate has already been independently
revalidated.

The six validation and empirical-analysis layers are:

### 1. Independent exhaustive oracle

The oracle explicitly enumerates possible internal-node assignments on small
rooted trees and independently calculates the whole-tree parsimony optimum and
the complete set of parent-child state pairs attainable on the focal edge.

The committed validation corpus contains 128,881 tip-pattern × focal-edge
comparisons across seven topology-edge settings. BRANCHSNV matched the oracle
in all 128,881 comparisons for global parsimony score, complete optimal
focal-edge state-pair set, and reconstruction class.

Coverage includes internal, terminal, and root-adjacent focal edges;
bifurcating and multifurcating trees; all supported IUPAC ambiguity symbols;
and gap and missing-data symbols.

### 2. Deliberately faulted implementations

Ten controlled fault classes challenge rooting, branch selection, taxon
mapping, state handling, reconstruction, and exclusivity logic. Across 280,216
fault-challenge comparisons, all 10 fault classes were detected; 118,916
comparisons produced outputs that differed from the correct implementation.

The differentiation fractions are properties of the deliberately constructed
challenge sets and are not estimates of fault prevalence in empirical data.

### 3. SNPPar comparison

Four public SNV matrices distributed with the SNPPar validation data were
analysed across 816 descendant-defined branch-matrix comparisons.

BRANCHSNV classified 877 focal-edge substitutions as unambiguous. All 877
matched SNPPar in descendant-defined edge, genomic position, and parent-to-child
nucleotide direction. SNPPar reported 66 additional events; every one was
contained in BRANCHSNV's globally optimal focal-edge pair set but was classified
by BRANCHSNV as placement-ambiguous because equally optimal reconstructions
included both a change and no change on the focal edge.

### 4. Published focal branches

BRANCHSNV reproduced all 46 published SNV positions and corresponding
branch-state contrasts across three focal branches:

- 23 MRSA AK3 SNVs;
- 10 MRSA ST97 SNVs; and
- 13 *E. coli* ST131/OXA-48 SNVs.

All 46 were classified as both fixed-exclusive and `unambiguous_change`.
Published insertion/deletion events were excluded because the current release
reconstructs nucleotide substitutions only.

### 5. Complete-phylogeny empirical analysis

Five rooted bacterial phylogenies were evaluated across 1,804 eligible
non-root-adjacent branches. Of 31,644 informative site-edge comparisons:

- 30,817 (97.39%) were both fixed-exclusive and unambiguous focal-edge
  substitutions;
- 675 (2.13%) were unambiguous focal-edge substitutions that were not
  fixed-exclusive; and
- 152 (0.48%) were placement-ambiguous.

Thus, 827/31,644 informative comparisons (2.61%) fell outside the intersection
of the two criteria. In 645/675 (95.56%) non-exclusive unambiguous focal-edge
substitutions, the derived nucleotide also occurred elsewhere in the same
phylogeny.

### 6. Scalability

The committed benchmark contains 39 measured command-line invocations spanning
taxon scaling, site scaling, and analysis-mode comparisons. All 39 runs
completed. Runtime and peak resident memory were approximately linear over the
tested taxon and site ranges.

## Snapshot integrity and production-source identity

The publication-validation repository stores machine-readable result snapshots,
input and result checksums, and hashes of the production source files used by
its experiments.

From the validation repository root:

```bash
python verify_publication_snapshot.py
```

verifies the committed empirical inputs, result checksums, and headline claims.
The committed snapshot reports:

```text
PUBLICATION SNAPSHOT: PASS
```

The production `analysis.py` and `parsimony.py` hashes recorded by the
publication-validation snapshot match the corresponding files in the historical
v0.1.0a1 production snapshot.

## Bundled example and package validation

GitHub Actions installs BRANCHSNV from the repository, runs the test suite,
reproduces the bundled example against committed expected outputs, builds both
wheel and source distributions, validates them with `twine`, installs each into
a clean environment, runs the installed command, and checks the installed
package.

These packaging checks complement the scientific validation: they test that the
software users install is usable and contains the expected package metadata.

## Legacy AK3 working-data regression recipe

[`validation/ak3/`](../validation/ak3/) predates the publication-validation
repository. It records checksum-gated working files and expected outputs for two
branches in an MRSA AK3 working dataset.

It remains useful as a permanent regression fixture, but it is **not** the
authoritative publication-validation record. The publication claims are tied to
the separate `branchsnv-validation` repository described above.
