# BRANCHSNV

[![CI](https://github.com/RhysWhite/branchsnv/actions/workflows/ci.yml/badge.svg)](https://github.com/RhysWhite/branchsnv/actions/workflows/ci.yml)
[![CodeQL](https://github.com/RhysWhite/branchsnv/actions/workflows/codeql.yml/badge.svg)](https://github.com/RhysWhite/branchsnv/actions/workflows/codeql.yml)
![Python 3.10–3.14](https://img.shields.io/badge/Python-3.10%E2%80%933.14-3776AB?logo=python&logoColor=white)
![Runtime dependencies](https://img.shields.io/badge/runtime%20dependencies-0-2ea44f)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Status: alpha](https://img.shields.io/badge/status-alpha-orange)

**Identify nucleotide states that distinguish a clade and substitutions that
reconstruct to a selected phylogenetic branch — without manual comparison.**

BRANCHSNV is a dependency-free Python command-line tool for rooted bacterial
phylogenies and transposed NEXUS SNV matrices. It validates exact taxon
membership, identifies the descendants of a selected branch, and produces
reproducible results with SHA-256 provenance.

```text
transposed NEXUS alignment  ─┐
Newick tree + rooting choice ├──> BRANCHSNV ───> results.tsv
exact focal-clade tip list ──┘                  members.txt
                                                report.json
```

> [!IMPORTANT]
> BRANCHSNV starts **after** variant calling, alignment generation, phylogeny
> inference, recombination filtering, and other upstream processing. It does
> not call variants, build a tree, detect recombination, annotate genes, infer
> functional effects, or establish causation.

## What BRANCHSNV reports

| Mode | Question answered | Reporting rule |
|---|---|---|
| `fixed-exclusive` | Which nucleotide states are strict markers of this clade in the supplied dataset? | Every descendant has the same unambiguous base; every outside taxon is callable; no outside taxon has that base. |
| `parsimony` | Which substitutions reconstruct to the selected branch? | Parent and child states are evaluated across **all** globally optimal equal-cost Sankoff reconstructions. |
| `both` | Which sites meet either definition? | Reports the union and records the reason for each row. This is the default. |

The definitions are deliberately separate. A perfect clade marker can have
ambiguous placement on the incoming branch, while a reconstructed branch change
can recur elsewhere and therefore not be exclusive.

## Installation

BRANCHSNV requires Python 3.10 or later.

Install the tagged alpha release from the repository:

```bash
git clone https://github.com/RhysWhite/branchsnv.git
cd branchsnv
git checkout v0.1.0a1
python -m pip install .
branchsnv --version
```

For development installation and contribution guidance, see
[`CONTRIBUTING.md`](CONTRIBUTING.md).

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
states, all optimal state pairs, call counts, parsimony score, and selection
reason. The example reduces to:

| Site | Reconstructed change | Parsimony status | Fixed-exclusive | Reported because |
|---|---:|---|---:|---|
| `ref_1` | `G>A` | `unambiguous_change` | yes | `both` |
| `ref_6` | ambiguous | `placement_ambiguous` | yes | `fixed-exclusive` |

Committed expected outputs are available in
[`examples/simple/expected/`](examples/simple/expected/).

## Running BRANCHSNV on your data

### 1. Prepare three inputs

You need:

1. a transposed nucleotide NEXUS matrix, with sites as rows and taxa as columns;
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
names. It is unaffected by sibling order or branch lengths, but intentionally
changes when rooting or descendant membership changes.

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
`T`, retaining every globally optimal reconstruction.

| Status | Interpretation |
|---|---|
| `unambiguous_change` | One parent-child pair is possible and the states differ. |
| `change_state_ambiguous` | Every optimum changes on the edge, but the exact transition is not unique. |
| `placement_ambiguous` | Some optima change on the edge and others do not. |
| `no_change` | No optimum changes on the selected edge. |

By default, parsimony mode reports only `unambiguous_change`. Add
`--include-ambiguous` to include the two ambiguous categories.

## Input scope

The current alpha supports one transposed nucleotide `DATA` or `CHARACTERS`
NEXUS block and one Newick tree with unique exact tip names. It supports quoted
labels, comments, branch lengths, multifurcations, standard IUPAC ambiguity
codes, and declared missing and gap symbols.

It deliberately does not support non-transposed or interleaved matrices,
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

BRANCHSNV uses layered validation rather than relying on a few successful
example files. The repository includes:

- strict parser and topology fixtures;
- comparison with an independent exhaustive internal-state oracle on generated
  small-tree patterns;
- permanent fault-regression scenarios designed to catch plausible incorrect
  implementations;
- deterministic-output and cross-platform line-ending checks;
- clean wheel and source-distribution validation; and
- a working-data validation recipe for two branches in a published MRSA AK3
  dataset.

Run the test suite after development installation:

```bash
python -m unittest discover -s tests -v
```

See [`VALIDATION_REPORT.md`](VALIDATION_REPORT.md),
[`docs/validation.md`](docs/validation.md), and
[`validation/ak3/README.md`](validation/ak3/README.md).

## Documentation

| Topic | Document |
|---|---|
| Accepted NEXUS and Newick syntax | [`docs/input-formats.md`](docs/input-formats.md) |
| Exact descendants, MRCA, and branch IDs | [`docs/branch-selection.md`](docs/branch-selection.md) |
| Fixed-exclusive and Sankoff algorithms | [`docs/algorithm.md`](docs/algorithm.md) |
| Scientific interpretation | [`docs/interpretation.md`](docs/interpretation.md) |
| Validation design | [`docs/validation.md`](docs/validation.md) |
| Shell and Snakemake integration | [`docs/workflow-integration.md`](docs/workflow-integration.md) |
| Annotated source-code walkthrough (`v0.1.0a1`) | [`docs/code-walkthrough/v0.1.0a1/README.md`](docs/code-walkthrough/v0.1.0a1/README.md) |
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

Citation metadata are provided in [`CITATION.cff`](CITATION.cff). A permanent
archive DOI should be added after the first public release.

## Licence

BRANCHSNV is released under the MIT License.
