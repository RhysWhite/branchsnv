# BRANCHSNV validation overview

**Software version:** 0.1.0a1

BRANCHSNV uses two complementary validation layers:

1. tests and packaging checks maintained with the production software; and
2. an independent publication-validation framework maintained separately at
   [RhysWhite/branchsnv-validation](https://github.com/RhysWhite/branchsnv-validation).

This separation prevents the independent oracle and deliberately faulted
implementations from sharing or modifying the production reconstruction logic.

## Production test suite

The current production suite passes **42/42 tests**.

It covers:

- strict transposed NEXUS parsing and malformed-input rejection;
- Newick parsing, explicit rerooting, multifurcations, and deterministic branch
  IDs;
- exact branch selection, MRCA selection, and non-monophyly rejection;
- strict fixed-exclusive marker rules with complete inside/outside callability;
- focal-edge equal-cost Sankoff reconstruction;
- generated comparisons against an independent exhaustive internal-state
  oracle;
- permanent fault-regression patterns;
- deterministic output across separate processes and `PYTHONHASHSEED` values;
- LF line-ending consistency;
- output overwrite and input/output collision protection;
- provenance checksum and count consistency;
- report-schema integrity; and
- release-metadata consistency.

Run the suite with:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

GitHub Actions runs the test suite on Python 3.10–3.14 on Linux and additionally
on macOS and Windows with Python 3.14.

## Bundled example

The installed command reproduces the committed simple example:

- 5 taxa;
- 6 sites;
- 2 descendants on the selected branch; and
- 2 reported rows in default `both` mode.

GitHub Actions compares the generated `results.tsv`, `members.txt`, and
`report.json` with the committed expected files.

## Publication-validation snapshot

The separate publication-validation repository contains six experiment layers.
Its committed snapshot evaluates BRANCHSNV v0.1.0a1 and verifies the following
headline results:

| Experiment | Result |
|---|---|
| Independent exhaustive oracle | 128,881/128,881 exact comparisons across seven topology-edge settings |
| Deliberately faulted implementations | 10/10 fault classes detected across 280,216 fault-challenge comparisons; 118,916 differentiating outputs |
| SNPPar comparison | 877/877 BRANCHSNV-unambiguous substitutions matched SNPPar; 66 additional SNPPar events were retained as placement-ambiguous |
| Published focal branches | 46/46 published SNVs reproduced across MRSA AK3, MRSA ST97, and *E. coli* ST131/OXA-48 |
| Complete-phylogeny empirical analysis | 31,644 informative comparisons across five phylogenies; 827 (2.61%) fell outside the fixed-exclusive/unambiguous-substitution intersection |
| Scalability | 39/39 measured end-to-end command-line runs completed |

For the 675 unambiguous focal-edge substitutions that were not fixed-exclusive,
645 (95.56%) had the derived nucleotide elsewhere in the same phylogeny.

The snapshot is integrity-gated with SHA-256 manifests. From the validation
repository root:

```bash
python verify_publication_snapshot.py
```

returns:

```text
PUBLICATION SNAPSHOT: PASS
```

The production-source SHA-256 hashes recorded by the validation snapshot for
`analysis.py` and `parsimony.py` match the corresponding files in this
v0.1.0a1 production snapshot.

## Packaging and installed-package checks

The CI build job:

1. builds both wheel and source distributions from `pyproject.toml`;
2. validates the distributions with `twine check`;
3. installs each distribution into a clean virtual environment;
4. runs the installed `branchsnv --version` command;
5. validates the installed package contents; and
6. runs `pip check`.

The package declares no runtime dependencies.

## Legacy AK3 working-data regression

The [`validation/ak3/`](validation/ak3/) directory is retained as an older,
checksum-gated working-data regression recipe. It is useful for guarding
against changes in behaviour on those exact development inputs, but it is no
longer the primary evidence supporting BRANCHSNV's scientific validation.

The authoritative manuscript-associated validation record is the separate
`branchsnv-validation` repository.
