# BRANCHSNV

**Reproducible identification of branch-associated single-nucleotide variants
from rooted phylogenies and transposed NEXUS matrices.**

BRANCHSNV replaces manual spreadsheet comparison of phylogenetic SNV matrices.
It matches taxa by exact name, identifies the descendants of a selected branch,
and reports either:

- **fixed-exclusive markers**: one unambiguous nucleotide is fixed in every
  descendant, all taxa outside the clade are callable, and none carries that
  nucleotide; or
- **parsimony branch changes**: the parent and child states on the selected edge
  are evaluated across every globally optimal equal-cost Sankoff
  reconstruction.

BRANCHSNV is a Python command-line tool with **no runtime dependencies**.

> [!IMPORTANT]
> BRANCHSNV analyses an existing alignment and tree. It does not call variants,
> build or root a phylogeny, detect recombination, annotate genes, infer
> functional effects, or establish that a substitution caused a phenotype.

## Why BRANCHSNV?

A spreadsheet workflow can identify useful clade markers, but it is vulnerable
to column-order errors, incomplete clade membership, hidden missing calls, and
unrecorded filtering decisions. BRANCHSNV makes those decisions explicit and
produces deterministic results with SHA-256 provenance.

Taxon order in the NEXUS file does **not** need to match visual tip order in the
tree. Matching is performed by exact taxon name.

## Installation

BRANCHSNV requires Python 3.10 or later.

From a cloned repository:

```bash
git clone https://github.com/RhysWhite/branchsnv.git
cd branchsnv
python -m pip install .
```

For development:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Quick start

Validate that the alignment and tree contain exactly the same taxa and that the
requested outgroup defines one tree edge:

```bash
branchsnv validate \
  --alignment alignment.nex \
  --tree tree.nwk \
  --outgroup Outgroup_isolate
```

List all branches and their deterministic identifiers:

```bash
branchsnv inspect \
  --tree tree.nwk \
  --outgroup Outgroup_isolate \
  --output branches.tsv
```

Identify SNVs associated with a branch whose exact descendants are recorded in
`clade_tips.txt`:

```bash
branchsnv find \
  --alignment alignment.nex \
  --tree tree.nwk \
  --outgroup Outgroup_isolate \
  --clade-tips clade_tips.txt \
  --mode both \
  --output branch_snvs.tsv \
  --members-output branch_members.txt \
  --report branchsnv_report.json
```

The bundled example can be run with:

```bash
branchsnv find \
  --alignment examples/simple/alignment.nex \
  --tree examples/simple/tree.nwk \
  --outgroup Outgroup \
  --clade-tips examples/simple/clade_tips.txt \
  --mode both \
  --output example_results.tsv \
  --members-output example_members.txt \
  --report example_report.json
```

## Selecting a branch

### Exact descendant list — recommended for publication analyses

```bash
--clade-tips clade_tips.txt
```

The file contains one exact tip name per line. BRANCHSNV stops if those tips do
not form exactly one rooted clade. The resulting sorted membership list and its
SHA-256 digest are recorded.

### MRCA of selected tips

```bash
--mrca isolate_A isolate_B isolate_C
```

This selects the incoming branch of their most recent common ancestor. The
output membership file shows every descendant actually selected. An MRCA may
contain additional tips beyond those named on the command line.

### Deterministic branch identifier

```bash
--branch-id b_daee1cd25194ae95
```

Run `branchsnv inspect` first. A branch ID is derived from the SHA-256 hash of
the sorted exact descendant-tip names. It is unaffected by Newick sibling order
or branch lengths. A full ID or unambiguous prefix may be supplied.

## Rooting is explicit

BRANCHSNV never silently decides that a tree is correctly rooted. Every command
that interprets branches requires one of:

```bash
--outgroup isolate_name
--outgroup-file outgroup_tips.txt
--accept-existing-root
```

`--outgroup` and `--outgroup-file` verify that the requested taxa are
monophyletic on one edge and root there. `--accept-existing-root` means that the
user accepts the root encoded by the Newick topology.

Branch direction, parent state, child state, and the meaning of a reported
change depend on the root.

## Analysis modes

### `--mode fixed-exclusive`

A site is reported only when:

1. every descendant is an unambiguous `A`, `C`, `G`, or `T`;
2. every descendant has the same state;
3. every outside taxon is also unambiguously callable; and
4. no outside taxon has the descendant state.

This is the strict, reproducible equivalent of the conservative spreadsheet
filtering approach.

### `--mode parsimony`

BRANCHSNV uses an unordered equal-cost Sankoff model over `A`, `C`, `G`, and
`T`. Missing, gap, and IUPAC ambiguity symbols are represented as sets of
possible states. It retains **all** globally most-parsimonious reconstructions
and classifies the selected edge as:

- `unambiguous_change`: one parent-child pair is possible and the states differ;
- `change_state_ambiguous`: every optimal reconstruction changes on the edge,
  but more than one nucleotide transition is possible;
- `placement_ambiguous`: some optimal reconstructions change on the edge and
  others do not;
- `no_change`: no optimal reconstruction changes on the edge.

By default, only `unambiguous_change` sites are reported. Add
`--include-ambiguous` to include the two ambiguous categories.

### `--mode both` — default

The output is the union of strict fixed-exclusive markers and selected
parsimony results. `selection_reason` records `fixed-exclusive`, `parsimony`, or
`both` for every row.

The two definitions are intentionally separate. A nucleotide may be a perfect
clade marker while its placement on the incoming branch remains ambiguous under
parsimony. Conversely, a parsimoniously reconstructed branch change may recur
outside the clade and therefore not be exclusive.

## Output files

### Results TSV

Important columns include:

- `site_id`, `reference`, `position`, and `input_row`;
- `parent_states`, `child_states`, and every optimal `possible_pairs` value;
- `change` and `parsimony_status`;
- `fixed_within_clade` and `exclusive_to_clade`;
- descendant and outside call counts;
- `outside_same_state_count`;
- whole-tree `parsimony_score`; and
- `selection_reason`.

Coordinates are parsed only when the site identifier ends in `_<integer>`.
The original site identifier is always retained.

### Branch-membership file

A sorted, one-name-per-line record of every descendant of the selected branch.
This file is itself hashed and referenced in the JSON report.

### Provenance JSON

The deterministic report records:

- BRANCHSNV version;
- input names, dimensions, and SHA-256 checksums;
- rooting method and outgroup;
- branch identifier, descendant count, and membership checksum;
- branch-selection method;
- state and call-rate rules;
- result counts; and
- output checksums.

The report intentionally omits execution timestamps and absolute paths so that
identical files and parameters generate identical outputs in different working
directories.

Report schema version 1 is documented in
[`schemas/branchsnv-report.schema.json`](schemas/branchsnv-report.schema.json).

## Supported input subset

The current BRANCHSNV alpha supports:

- one rooted Newick tree with unique exact tip names;
- single-quoted Newick labels, comments, internal labels, branch lengths, and
  multifurcations;
- one `DATA` or `CHARACTERS` NEXUS block;
- `DIMENSIONS NTAX=... NCHAR=...`;
- `FORMAT ... TRANSPOSE` nucleotide matrices;
- one `TAXLABELS` statement;
- one site per physical matrix row;
- separated single-character states or one compact state string;
- `A`, `C`, `G`, `T`, standard IUPAC ambiguity codes, the declared missing
  symbol, and the declared gap symbol.

Interleaved matrices, non-transposed matrices, repeated blocks, indel
reconstruction, structural variants, and general-purpose NEXUS dialects are
outside the current scope. Unsupported input is rejected rather than guessed.

## Interpretation

A reported result is conditional on:

- the supplied alignment;
- all upstream variant and site filtering;
- the supplied tree topology;
- the supplied root;
- the selected descendants; and
- the chosen state model.

“Branch-associated” does not mean causal, adaptive, unique in all future
sampling, or free from recombination unless those properties were established
upstream. See [`docs/interpretation.md`](docs/interpretation.md).

## Validation

The repository includes:

- hand-calculated parser and topology fixtures;
- exhaustive enumeration of internal states as an independent oracle for
  generated small-tree examples;
- tests for missing data, IUPAC ambiguity, multifurcations, parallel patterns,
  non-monophyletic selections, and taxon mismatch;
- permanent scenarios designed to detect wrong-side selection, majority-state
  shortcuts, arbitrary tie resolution, and treatment of gaps as a fifth base;
- deterministic-output checks; and
- an AK3 working-dataset validation recipe with fixed input hashes and expected
  outputs.

Run all tests with:

```bash
python -m unittest discover -s tests -v
```

See [`docs/validation.md`](docs/validation.md),
[`validation/ak3/README.md`](validation/ak3/README.md), and the
[`VALIDATION_REPORT.md`](VALIDATION_REPORT.md) produced for this alpha.

## Scope and limitations

The current BRANCHSNV alpha does not:

- infer or optimize a phylogenetic tree;
- infer an outgroup;
- use branch lengths in ancestral reconstruction;
- model unequal substitution rates or nucleotide frequencies;
- distinguish mutation from recombination;
- reconstruct insertions or deletions;
- annotate coding consequences;
- accept partial or fuzzy taxon-name matches; or
- silently discard taxa or malformed sites.

These are deliberate boundaries, not missing documentation.

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
