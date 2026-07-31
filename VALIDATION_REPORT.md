# BRANCHSNV alpha validation report

**Version:** 0.1.0a1  
**Validation date:** 31 July 2026  
**Local environment:** Python 3.13.5 on Linux

This report records checks completed before the initial repository handoff. It
is not a substitute for the GitHub Actions matrix, which will run only after the
repository is pushed.

## Standard-library test suite

The complete suite passed:

```text
Ran 39 tests
OK
```

The suite covers:

- strict transposed NEXUS parsing and malformed-input rejection;
- Newick parsing, rerooting, multifurcations, and deterministic branch IDs;
- exact branch selection, MRCA selection, and non-monophyly rejection;
- fixed-exclusive marker rules with strict inside and outside callability;
- exact selected-edge Sankoff reconstruction;
- comparison with an independent exhaustive enumeration oracle for 250
  deterministic generated patterns containing bases, IUPAC ambiguity, gaps,
  and missing data;
- permanent fault-regression patterns;
- output/input path collision protection;
- deterministic results across distinct `PYTHONHASHSEED` values;
- output overwrite protection;
- provenance checksum and count consistency; and
- report-schema JSON integrity.

## Bundled example

The installed command reproduced the committed simple example byte-for-byte:

- 5 taxa;
- 6 sites;
- 2 descendants on the selected branch;
- 2 reported rows in default `both` mode.

## AK3 working-data validation

The following external files were verified by SHA-256 before analysis:

```text
40c49b026c52e04530ecbbee7044567ac3355eccf7adda42a7d96bf977df9014  396_MRSA_AK3(1).nex
18322b2808baf621d09dd5292027205e68a0f207d7be44f043bd044d0d314bd0  Cluster_1_396genomes_refsa230905_barcode06_ML_Flitered_BS.nwk
```

Structural validation found:

- 396 NEXUS taxa;
- 396 Newick tips;
- exact 396/396 name correspondence;
- 10,481 matrix rows; and
- explicit outgroup rooting with `SRR13968194`.

Real-data results:

- 385-descendant working branch: 15 fixed-exclusive and unambiguous-parsimony
  SNV rows;
- 360-descendant MRSA AK3 branch: 23 fixed-exclusive and
  unambiguous-parsimony SNV rows.

The 360-branch positions match the 23 SNV rows in the published MRSA AK3 branch
table; its deletion is outside the current tool scope.

The 385-branch working files contain 14 positions present in the published
SaPITokyo12571-like branch table plus position 1,891,191. The nucleotide
orientations in the supplied matrix differ from the corresponding published
table entries. This remains documented as an unresolved working-input versus
publication discrepancy. BRANCHSNV does not alter output to force agreement.

## Packaging

The alpha wheel was built with setuptools, installed into a clean virtual
environment, and executed through the installed `branchsnv` console command.
Wheel metadata contained no `Requires-Dist` entries, confirming no runtime
dependencies.

The source distribution and wheel were both built successfully from
`pyproject.toml`. The source distribution was inspected to confirm that it did
not contain bytecode caches or build directories.

## Checks deferred to GitHub

The repository configures CI for Python 3.10, 3.11, 3.12, 3.13, and 3.14, plus
CodeQL and clean package builds. Those hosted checks have not yet run and must
pass before a final `v0.1.0` release.
