# BRANCHSNV validation overview

**Production software version:** 0.1.0

**Historical publication-validation snapshot:** 0.1.0a1

**Stable v0.1.0 release-validation record:** PASS (validation repository `35a0794ddd9782355e1e06dd95bd10e1cde4c735`)

BRANCHSNV uses two complementary validation layers:

1. tests and packaging checks maintained with the production software; and
2. an independent publication-validation framework maintained separately at
   [RhysWhite/branchsnv-validation](https://github.com/RhysWhite/branchsnv-validation).

This separation prevents the independent oracle and deliberately faulted
implementations from sharing or modifying the production reconstruction logic.

## Production test suite

The current production suite passes **72/72 tests**.

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

## Independent validation records

The separate publication-validation repository contains six experiment layers
and preserves two version-pinned records. The historical publication snapshot
evaluates BRANCHSNV v0.1.0a1. A separate stable v0.1.0 release-validation record
archives a fresh run against production commit `71b055bdbd8e00ee63afda136b88892aee0062f8`
using validation-framework commit `cfb07389191540ca57c9e822b254c279ab903f36`.

The stable run completed with `REPRODUCED RESULTS: PASS`: production source
identity was verified for all 13 Python source files, validation-script identity
was verified, deterministic analytical outputs matched the canonical scientific
snapshot exactly, Experiments 01–06 met their exact pass criteria, and the
Experiment 04 protocol contained 3 repetitions and 39 measured runs.

The two records support the following headline results:

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

The historical snapshot remains integrity-gated with SHA-256 manifests:

```bash
python verify_publication_snapshot.py
```

returns `PUBLICATION SNAPSHOT: PASS`.

The stable v0.1.0 record is stored under `release_validation/v0.1.0/` and
contains all 47 generated result files, a checksum manifest, and machine-readable
record metadata. At validation-repository commit
`35a0794ddd9782355e1e06dd95bd10e1cde4c735`, CI verifies the archived result
checksums and provenance and independently rechecks the archived scientific
outputs with `verify_reproduced_results.py`.

The historical snapshot retains the v0.1.0a1 production-source hashes. The
stable record separately records the successful source-identity check against
production commit `71b055bdbd8e00ee63afda136b88892aee0062f8`.

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

The authoritative independent validation records are maintained in the separate
`branchsnv-validation` repository: the historical publication snapshot and the
version-pinned stable v0.1.0 release-validation record.
