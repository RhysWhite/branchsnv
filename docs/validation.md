# Validation strategy

BRANCHSNV validation is layered so that correctness does not depend on one set
of example outputs.

## Parser validation

Permanent tests cover valid and malformed examples for:

- transposed NEXUS dimensions and row lengths;
- duplicate taxa and site identifiers;
- compact and separated state strings;
- nested comments and quoted labels;
- Newick comments, lengths, multifurcations, and duplicate tips; and
- tree/alignment taxon mismatch.

## Independent exhaustive oracle

For small trees, the test suite enumerates every possible internal-node
assignment over A/C/G/T. It independently calculates the global minimum score
and all possible parent-child state pairs on the focal edge.

The production dynamic-programming implementation is compared against this
oracle for 250 deterministic generated patterns containing unambiguous bases,
IUPAC ambiguity, gaps, and missing states.

The oracle and production algorithm do not share their reconstruction logic.

## Fault-regression scenarios

Permanent examples are chosen to fail if an implementation:

- analyses the wrong side of the branch;
- substitutes a majority-state shortcut for parsimony;
- treats a gap as a fifth nucleotide;
- chooses one arbitrary solution when optimal reconstructions tie;
- accepts a non-monophyletic descendant list; or
- matches taxa by position instead of exact name.

## Determinism

The CLI is run in separate temporary directories. Result TSVs, membership
files, and parsed JSON reports must be identical. Existing outputs are not
replaced without `--force`.

## Real working-data check

`validation/ak3/` records an external working input pair, exact SHA-256 hashes,
two exact descendant lists, and committed expected TSVs. The large alignment
and tree are not duplicated in this repository. The validation script refuses
to run against files with different hashes.

The MRSA AK3 360-descendant branch yields the 23 SNV positions reported in the
published MRSA branch table after excluding the table's deletion, which is
outside the current BRANCHSNV alpha scope.

The 385-descendant working branch yields 15 SNVs. Fourteen positions overlap
the published SaPITokyo12571-like branch table's SNV rows, while position
1,891,191 is additionally present in the supplied working files. The nucleotide
directions in those working files also differ from the published table for
those positions. This discrepancy is preserved and documented rather than
silently reconciled.

The published article is:

> White RT et al. *Microbial Genomics* 2025;11:001452.
> DOI: 10.1099/mgen.0.001452.
