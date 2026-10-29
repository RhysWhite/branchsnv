<p align="center">
  <img
    src="assets/BRANCHSNV_logo.png"
    alt="BRANCHSNV — Exact branch-level SNV interrogation from a rooted tree and alignment"
    width="1000"
  >
</p>

<p align="center">
  <a href="https://github.com/RhysWhite/branchsnv/actions/workflows/ci.yml">
    <img src="https://github.com/RhysWhite/branchsnv/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://github.com/RhysWhite/branchsnv/actions/workflows/codeql.yml">
    <img src="https://github.com/RhysWhite/branchsnv/actions/workflows/codeql.yml/badge.svg" alt="CodeQL">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Python-3.10%E2%80%933.14-3776AB?logo=python&logoColor=white" alt="Python 3.10–3.14">
  </a>
  <a href="https://github.com/RhysWhite/branchsnv/releases">
    <img src="https://img.shields.io/github/v/release/RhysWhite/branchsnv?display_name=tag&sort=semver" alt="Latest release">
  </a>
</p>

<p align="center">
  <a href="https://pypi.org/project/branchsnv/">
    <img src="https://img.shields.io/pypi/v/branchsnv.svg" alt="PyPI">
  </a>
  <a href="https://anaconda.org/bioconda/branchsnv">
    <img src="https://img.shields.io/conda/vn/bioconda/branchsnv.svg?label=Bioconda" alt="Bioconda">
  </a>
  <a href="https://anaconda.org/bioconda/branchsnv">
    <img src="https://img.shields.io/conda/dn/bioconda/branchsnv.svg?label=Conda%20downloads" alt="Conda downloads">
  </a>
  <a href="https://branchsnv.readthedocs.io/en/latest/">
    <img src="https://readthedocs.org/projects/branchsnv/badge/?version=latest" alt="Documentation status">
  </a>
  <a href="https://bio.tools/branchsnv">
    <img src="https://img.shields.io/badge/bio.tools-branchsnv-005a9c.svg" alt="bio.tools">
  </a>
  <a href="https://doi.org/10.5281/zenodo.23518619">
    <img src="https://zenodo.org/badge/DOI/10.5281/zenodo.23518619.svg" alt="v0.2.0 software archive DOI">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/runtime%20dependencies-0-2ea44f" alt="Runtime dependencies: 0">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
  </a>
  <img src="https://img.shields.io/badge/status-beta-blue" alt="Status: beta">
</p>

**Identify nucleotide states that distinguish a clade and substitutions that
reconstruct to a selected phylogenetic branch — without conflating the two.**

BRANCHSNV is a dependency-free Python command-line tool for interrogating one
selected branch of a rooted bacterial phylogeny using a nucleotide NEXUS SNV
matrix. It reports strict clade-exclusive nucleotide markers separately from
substitutions reconstructed on the focal edge, retains uncertainty across
all globally optimal equal-cost parsimony solutions, validates exact taxon and
branch membership, and records deterministic SHA-256 provenance.

```text
NEXUS alignment             ─┐
Newick tree + rooting choice ├──> BRANCHSNV ───> results.tsv
exact focal-clade tip list ──┘                  members.txt
                                                report.json
```

> [!IMPORTANT]
> BRANCHSNV starts **after** variant calling, alignment generation, phylogeny
> inference, recombination filtering, and other upstream processing. It does
> not call variants, build a tree, detect recombination, annotate genes, infer
> functional effects, or establish causation.

**BRANCHSNV v0.2.0 archival records:** [software (10.5281/zenodo.23518619)](https://doi.org/10.5281/zenodo.23518619) · [independent validation and reproduction (10.5281/zenodo.23518684)](https://doi.org/10.5281/zenodo.23518684).

## What BRANCHSNV reports

| Mode | Question answered | Reporting rule |
|---|---|---|
| `fixed-exclusive` | Which nucleotide states are strict markers of this clade in the supplied dataset? | Every descendant has the same unambiguous base; every outside taxon is callable; no outside taxon has that base. |
| `parsimony` | Which substitutions reconstruct to the selected branch? | Parent and child states are evaluated across **all** globally optimal equal-cost Sankoff reconstructions. |
| `both` | Which sites meet either definition? | Reports the union and records the reason for each row. This is the default. |

The definitions are deliberately separate. A strict clade marker can have
ambiguous placement on the incoming branch, while a reconstructed branch change
can recur elsewhere and therefore not be clade-exclusive.

## Installation

BRANCHSNV requires Python 3.10 or later.

The PyPI and Bioconda commands below are pinned to the historical **v0.1.0**
package; they are not instructions for installing v0.2.0. **v0.2.0** additionally
supports conventional NEXUS matrices. To use the version reproduced in the
independent October 2026 validation, install its exact Git commit below.
Version-specific [v0.2.0 software and validation archives](https://doi.org/10.5281/zenodo.23518684)
are published; see the [evidence index](https://github.com/RhysWhite/branchsnv-validation/blob/main/EVIDENCE_INDEX.md)
for the associated Git identities and verification commands.

Install the independently validated v0.1.0 release from Bioconda:

```bash
conda create -n branchsnv branchsnv=0.1.0 \
  --channel conda-forge \
  --channel bioconda \
  --strict-channel-priority
conda activate branchsnv
branchsnv --version
```

Alternatively, install from PyPI:

```bash
python -m pip install branchsnv==0.1.0
branchsnv --version
```

Or install directly from the tagged source release:

```bash
git clone https://github.com/RhysWhite/branchsnv.git
cd branchsnv
git checkout v0.1.0
python -m pip install .
branchsnv --version
```

To install the **v0.2.0 source used in the full independent reproduction**,
check out the exact validated commit:

```bash
git clone https://github.com/RhysWhite/branchsnv.git
cd branchsnv
git checkout 65eb791d9f1a202c3ca8816332a58c036794bd1f
python -m pip install .
branchsnv --version
```

For development installation and contribution guidance, see
[`CONTRIBUTING.md`](CONTRIBUTING.md).

For current source-to-algorithm navigation, see the
[v0.2.0 implementation map](docs/implementation-map.md). For immutable
evidence paths and version-scoped claims, use the
[validation repository evidence index](https://github.com/RhysWhite/branchsnv-validation/blob/main/EVIDENCE_INDEX.md).

## Quick start

The bundled example contains five taxa, six sites, and a focal branch containing
isolates `A` and `B`.

```bash
branchsnv find \
  --alignment examples/simple/alignment.nex \
  --tree examples/simple/tree.nwk \
  --outgroup Outgroup \
  --clade-tips examples/simple/clade_tips.txt \
  --mode both \
  --output results.tsv \
  --members-output members.txt \
  --report report.json
```

BRANCHSNV reports:

```text
Selected b_daee1cd25194ae95 (2 descendants); reported 2 of 6 sites.
```

The full TSV contains the original site identifier, inferred parent and child
states, all optimal focal-edge state pairs, call counts, parsimony score, and
selection reason. The example reduces to:

| Site | Reconstructed change | Parsimony status | Fixed-exclusive | Reported because |
|---|---:|---|---:|---|
| `ref_1` | `G>A` | `unambiguous_change` | yes | `both` |
| `ref_6` | ambiguous | `placement_ambiguous` | yes | `fixed-exclusive` |

Committed expected outputs are available in
[`examples/simple/expected/`](examples/simple/expected/).

## Running BRANCHSNV on your data

### 1. Prepare three inputs

You need:

1. a nucleotide NEXUS matrix in conventional taxon-by-character or transposed
   character-by-taxon orientation;
2. a Newick tree containing exactly the same taxon names; and
3. the exact tip names descending from the branch of interest.

The NEXUS taxon order does **not** need to match the visual tip order in the
tree. BRANCHSNV matches taxa by exact name.

Example focal-clade file:

```text
isolate_A
isolate_B
isolate_C
```

### 2. Validate the alignment, tree, and root

For a single outgroup tip:

```bash
branchsnv validate \
  --alignment alignment.nex \
  --tree tree.nwk \
  --outgroup Outgroup_isolate
```

For an outgroup containing several genomes:

```bash
branchsnv validate \
  --alignment alignment.nex \
  --tree tree.nwk \
  --outgroup outgroup_1 outgroup_2 outgroup_3 outgroup_4
```

A one-name-per-line outgroup file can instead be supplied with
`--outgroup-file outgroup_tips.txt`.

### 3. Find branch-associated SNVs

```bash
branchsnv find \
  --alignment alignment.nex \
  --tree tree.nwk \
  --outgroup-file outgroup_tips.txt \
  --clade-tips clade_tips.txt \
  --mode both \
  --output branch_snvs.tsv \
  --members-output branch_members.txt \
  --report branchsnv_report.json
```

BRANCHSNV stops if the requested tips do not form exactly one rooted clade, if
tree and alignment taxa differ, or if unsupported input is encountered.

## Selecting a branch

| Method | Option | Best use | Important detail |
|---|---|---|---|
| Exact descendants | `--clade-tips clade_tips.txt` | Publication and permanent analyses | Recommended. The file must equal the complete descendant set of one branch. |
| MRCA anchors | `--mrca isolate_A isolate_B` | Exploration | The selected MRCA may contain additional descendants. Inspect `members.txt`. |
| Deterministic branch ID | `--branch-id b_daee1cd25194ae95` | Repeating an inspected selection | Generate IDs first with `branchsnv inspect`. Full IDs or unique prefixes are accepted. |

To list every branch and its deterministic identifier:

```bash
branchsnv inspect \
  --tree tree.nwk \
  --outgroup-file outgroup_tips.txt \
  --output branches.tsv
```

A branch ID is derived from the SHA-256 hash of its sorted exact descendant-tip
names. It is unaffected by sibling order, branch lengths, or Newick formatting
outside taxon labels, but exact taxon-name content is significant. It
intentionally changes when rooting or descendant membership changes.

See [`docs/branch-selection.md`](docs/branch-selection.md) for details.

## Rooting is explicit

Every command that interprets branches requires one of:

```text
--outgroup TIP [TIP ...]
--outgroup-file outgroup_tips.txt
--accept-existing-root
```

BRANCHSNV never silently assumes that the encoded Newick root is biologically
appropriate. Branch direction and reconstructed parent-to-child changes depend
on the chosen root.

## Output files

| File | Purpose |
|---|---|
| `results.tsv` | Reported sites, ancestral-state results, call counts, parsimony scores, and selection reasons. |
| `members.txt` | Sorted, one-name-per-line record of every descendant on the selected branch. |
| `report.json` | Deterministic provenance: versions, input dimensions, rooting and selection methods, parameters, counts, and SHA-256 checksums. |

The JSON report omits timestamps and absolute paths so that identical input
files and parameters produce identical output bytes in different working
directories. Its schema is documented in
[`schemas/branchsnv-report.schema.json`](schemas/branchsnv-report.schema.json).

## Parsimony classifications

BRANCHSNV uses unordered equal-cost Sankoff parsimony over `A`, `C`, `G`, and
`T`, retaining the complete set of parent-child state pairs attainable on the
focal edge among globally optimal reconstructions.

| Status | Interpretation |
|---|---|
| `unambiguous_change` | One parent-child pair is possible and the states differ. |
| `change_state_ambiguous` | Every optimum changes on the edge, but the exact transition is not unique. |
| `placement_ambiguous` | Some optima change on the edge and others do not. |
| `no_change` | No optimum changes on the selected edge. |

By default, parsimony mode reports only `unambiguous_change`. Add
`--include-ambiguous` to include the two ambiguous categories.

## Input scope

BRANCHSNV accepts one nucleotide `DATA` or `CHARACTERS` NEXUS block in
conventional taxon-by-character or transposed character-by-taxon orientation,
together with one Newick tree with unique exact tip names. It supports quoted
labels, comments, branch lengths, multifurcations, standard IUPAC ambiguity
codes, and declared missing and gap symbols.

It deliberately does not support interleaved matrices,
multiple data blocks, indel reconstruction, structural variants, fuzzy taxon
matching, or general-purpose NEXUS dialects. Unsupported content is rejected
rather than guessed.

See [`docs/input-formats.md`](docs/input-formats.md) for the complete accepted
subset.

## Interpretation and limitations

Every result is conditional on the supplied alignment, upstream filters, tree
topology, root, selected descendants, and state model.

“Branch-associated” does not mean causal, adaptive, free from recombination, or
unique under future sampling. BRANCHSNV also does not use branch lengths,
unequal substitution rates, or nucleotide frequencies in ancestral
reconstruction.

See [`docs/interpretation.md`](docs/interpretation.md) for reporting language and
interpretive cautions.

## Validation and reproducibility

The [production test suite](docs/validation.md) checks parsing, branch selection,
parsimony, output determinism and packaging. In this source snapshot,
`PYTHONPATH=src python -m unittest discover -s tests -q` runs **80 tests**.

Independent results and their source identities belong to
[`branchsnv-validation`](https://github.com/RhysWhite/branchsnv-validation).
Start at its [evidence index](https://github.com/RhysWhite/branchsnv-validation/blob/main/EVIDENCE_INDEX.md),
not a floating branch or a headline number. It distinguishes:

| Scope | Evidence and limitation |
|---|---|
| Experiments 01–06 | Exhaustive oracle, fault challenges, SNPPar concordance, scalability, published focal branches and complete-phylogeny empirical analysis; independently reproduced for v0.2.0 and [archived](https://doi.org/10.5281/zenodo.23518684). |
| Experiment 07 | Separate 150-scenario comparison with a [frozen publication snapshot](https://github.com/RhysWhite/branchsnv-validation/tree/2afa89f47815eac3b85b722c2fddd14d9c17f22e) and [v0.3.0 data archive](https://doi.org/10.5281/zenodo.23684441). This is *not* part of the six-experiment v0.2.0 release validation. |
| Supplementary Table S8 | Post-hoc attribution and identifiability analyses; source and outputs were reproduced byte-for-byte in a release-candidate replay. The separate S8 supplement **has not yet received a public DOI**. Do not cite it as deposited. |

Exact result tables, reproducibility steps and the limits of each comparison
are documented in the [validation evidence index](https://github.com/RhysWhite/branchsnv-validation/blob/main/EVIDENCE_INDEX.md).


## Documentation

Hosted documentation is available at
[branchsnv.readthedocs.io](https://branchsnv.readthedocs.io/en/latest/).

BRANCHSNV is indexed in the ELIXIR bio.tools registry as
[`biotools:branchsnv`](https://bio.tools/branchsnv). The archived software
release is available from [Zenodo](https://doi.org/10.5281/zenodo.21919038),
and installable releases are available from
[Bioconda](https://anaconda.org/bioconda/branchsnv) and
[PyPI](https://pypi.org/project/branchsnv/).

| Topic | Document |
|---|---|
| Accepted NEXUS and Newick syntax | [`docs/input-formats.md`](docs/input-formats.md) |
| Exact descendants, MRCA, and branch IDs | [`docs/branch-selection.md`](docs/branch-selection.md) |
| Fixed-exclusive and Sankoff algorithms | [`docs/algorithm.md`](docs/algorithm.md) |
| Scientific interpretation | [`docs/interpretation.md`](docs/interpretation.md) |
| Validation design | [`docs/validation.md`](docs/validation.md) |
| Shell and Snakemake integration | [`docs/workflow-integration.md`](docs/workflow-integration.md) |
| Beginner-friendly v0.2.0 source walkthrough | [`docs/code-walkthrough/v0.2.0/README.md`](docs/code-walkthrough/v0.2.0/README.md) |
| Historical v0.1.0a1 line-by-line walkthrough | [`docs/code-walkthrough/v0.1.0a1/README.md`](docs/code-walkthrough/v0.1.0a1/README.md) |
| Related research and tools | [`docs/references.md`](docs/references.md) |
| Contributing | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Release history | [`CHANGELOG.md`](CHANGELOG.md) |

## Funding and affiliation

<p align="center">
  <a href="https://www.genomics-aotearoa.org.nz/">
    <img
      src="assets/genomics-aotearoa-logo.png"
      alt="Genomics Aotearoa"
      height="80">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.phfscience.nz/">
    <img
      src="assets/phf-science-logo.png"
      alt="PHF Science"
      height="80">
  </a>
</p>

<p align="center">
  Development of BRANCHSNV was supported by
  <strong>Genomics Aotearoa</strong> and undertaken at
  <strong>Public Health and Forensic Science (PHF Science),
  Aotearoa New Zealand</strong>.
</p>

BRANCHSNV was developed and is maintained by [Rhys White](https://github.com/RhysWhite).

## Citation

Citation metadata are provided in [`CITATION.cff`](CITATION.cff).

For **v0.2.0**, cite the [software archive](https://doi.org/10.5281/zenodo.23518619)
and, when relevant, the [independent validation archive](https://doi.org/10.5281/zenodo.23518684).
Historical v0.1.0 records remain available as
[software](https://doi.org/10.5281/zenodo.21919038) and
[validation](https://doi.org/10.5281/zenodo.21919067).

## Licence

BRANCHSNV is released under the MIT License.
