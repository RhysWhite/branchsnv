# Walking through BRANCHSNV v0.2.0

This guide is for readers who can run a terminal command but do not necessarily
know Python. Follow the [pinned v0.2.0 reproduction source](https://github.com/RhysWhite/branchsnv/tree/65eb791d9f1a202c3ca8816332a58c036794bd1f/src/branchsnv)
while reading. File and function names refer to that revision. For formal
input restrictions use [Input formats](../../input-formats.md); for the
mathematical algorithm use [Algorithm](../../algorithm.md).

## Start with a working example

Clone the repository and select the tested source revision:

```bash
git clone https://github.com/RhysWhite/branchsnv.git
cd branchsnv
git checkout --detach 65eb791d9f1a202c3ca8816332a58c036794bd1f
python3 -m venv .venv
. .venv/bin/activate             # Linux/macOS; on Windows use .venv\Scripts\activate
python -m pip install .
branchsnv validate --alignment examples/simple/alignment.nex \
  --tree examples/simple/tree.nwk --outgroup Outgroup
branchsnv find --alignment examples/simple/alignment.nex \
  --tree examples/simple/tree.nwk --outgroup Outgroup \
  --clade-tips examples/simple/clade_tips.txt --mode both \
  --output results.tsv --members-output members.txt --report report.json
```

A **repository** is the directory containing source, tests and examples. A
**Python module** is a `.py` file; `import` lets one module use functions and
classes defined in another. A **function** such as `read_nexus()` is an
operation called by another part of the program. A **test** checks a stated
behaviour using known inputs.

`validate` checks the input agreement without assigning branch changes. `find`
produces three files: a site-level TSV, the sorted selected descendants, and
a JSON provenance record. Never overwrite them during a reproduction run.

## The execution route

```text
terminal: branchsnv find
  -> src/branchsnv/__main__.py or installed console entry point
  -> cli.main() / cli._run_find()
  -> nexus.read_nexus() + newick.read_newick()
  -> cli._root_tree() + validation.validate_compatibility()
  -> cli._select_branch()
  -> analysis.analyse_branch()
       | observed-state fixed-exclusivity test
       +-> parsimony.compile_tree() / reconstruct_site()
  -> writing.write_results() + write_members()
  -> provenance.build_report() + writing.write_report()
  -> writing.AtomicOutputSet.commit()
```

| Read this source file | What to look for | Related tests |
|---|---|---|
| [`cli.py`](https://github.com/RhysWhite/branchsnv/blob/65eb791d9f1a202c3ca8816332a58c036794bd1f/src/branchsnv/cli.py) | `build_parser`, `_run_validate`, `_run_inspect`, `_run_find` | `tests/test_cli.py`, `test_selection.py` |
| [`nexus.py`](https://github.com/RhysWhite/branchsnv/blob/65eb791d9f1a202c3ca8816332a58c036794bd1f/src/branchsnv/nexus.py) | `_read_nexus`, `read_nexus` | `tests/test_nexus.py` |
| [`newick.py`](https://github.com/RhysWhite/branchsnv/blob/65eb791d9f1a202c3ca8816332a58c036794bd1f/src/branchsnv/newick.py) | `read_newick`, `reroot_on_outgroup`, `select_exact_descendants` | `tests/test_newick.py`, `test_selection.py` |
| [`validation.py`](https://github.com/RhysWhite/branchsnv/blob/65eb791d9f1a202c3ca8816332a58c036794bd1f/src/branchsnv/validation.py) | `validate_compatibility` | `tests/test_validation.py` |
| [`analysis.py`](https://github.com/RhysWhite/branchsnv/blob/65eb791d9f1a202c3ca8816332a58c036794bd1f/src/branchsnv/analysis.py) | `analyse_branch` | `tests/test_analysis.py` |
| [`parsimony.py`](https://github.com/RhysWhite/branchsnv/blob/65eb791d9f1a202c3ca8816332a58c036794bd1f/src/branchsnv/parsimony.py) | `compile_tree`, `reconstruct_site` | `tests/test_parsimony.py` |
| [`writing.py`](https://github.com/RhysWhite/branchsnv/blob/65eb791d9f1a202c3ca8816332a58c036794bd1f/src/branchsnv/writing.py), [`provenance.py`](https://github.com/RhysWhite/branchsnv/blob/65eb791d9f1a202c3ca8816332a58c036794bd1f/src/branchsnv/provenance.py) | `AtomicOutputSet`, `build_report` | `tests/test_writing.py`, `test_provenance.py` |

The links resolve to **the tested source revision**, not a moving `main`
branch. `models.py` defines the immutable data objects passed between stages;
`errors.py` supplies explicit user-facing exceptions and `util.py` supplies
hashing and coordinate helpers.

## 1. Convert the files to a consistent model

`nexus.read_nexus()` parses either a conventional taxon-by-character matrix
or a transposed character-by-taxon matrix. Both become one `Alignment`
containing ordered sites, unique taxon names, and a state string for each site.
For example, a site with states `A A G G` is stored in the alignment's
normalized taxon order regardless of how the input file arranged rows.

`newick.read_newick()` constructs `Node` objects with parents and children.
`cli._root_tree()` requires an explicit outgroup or `--accept-existing-root`;
it does **not** assume that the first printed Newick tip is an outgroup.
`validate_compatibility()` requires exactly the same unique taxon names in
both files, preventing an incorrect sample-to-tip mapping.

**Try it:** change one taxon name in a *copy* of the example alignment. Run
`branchsnv validate` again. The command should reject the mismatch; restore
the original file before continuing.

## 2. Select precisely one branch

In `cli._select_branch()`, `--clade-tips` asks for the **complete** set of
descendant names below one edge. `--mrca` instead uses supplied anchors to
find a common ancestral node; it can include additional descendants.
`--branch-id` resolves a deterministic identifier previously listed by
`branchsnv inspect`. For publication, exact descendants are easiest to audit.

`newick.branch_records()` derives the branch ID from sorted descendant-tip
names. It is stable under sibling reordering, but changes when exact
membership changes. The output `members.txt` lets the reader check what was
actually selected.

## 3. Evaluate clade exclusivity from observed tips

`analysis.analyse_branch()` loops over sites. A strict fixed-exclusive marker
requires **every** descendant to have the same unambiguous A/C/G/T nucleotide,
**every** outside taxon to be callable, and no outside taxon to carry that
nucleotide. This is an observed-data property, not ancestral reconstruction.
Missing or IUPAC-ambiguous calls prevent strict exclusivity.

The same function independently asks `parsimony.reconstruct_site()` to infer
possible substitutions on the incoming edge. A single site can therefore be
fixed-exclusive yet ambiguous in its substitution placement. With `--mode both`,
`selection_reason` records which criterion included the row.

## 4. Reconstruct the focal edge without choosing an arbitrary ancestor

In `parsimony.py`, `compile_tree()` turns the tree into indexed arrays once.
`reconstruct_site()` then computes the whole-tree minimum number of nucleotide
changes under **unordered equal-cost Sankoff parsimony**. The down-pass
calculates costs from tips toward the root. An outside-cost pass follows only
the root-to-focal-parent path, then tests all **16** A/C/G/T parent-child state
pairs on that edge.

A pair is retained only if its cost equals the *global* optimum. The results
have four categories:

| Status | Meaning |
|---|---|
| `unambiguous_change` | Exactly one optimal parent-to-child pair, and the states differ |
| `change_state_ambiguous` | Every optimal pair changes, but more than one nucleotide transition is possible |
| `placement_ambiguous` | Some optimal pairs change on the focal edge and others do not |
| `no_change` | Every optimal pair keeps the same nucleotide |

**Important:** `--include-ambiguous` also reports the two ambiguous-change
categories in parsimony/both mode; it does not magically resolve those
changes. The `possible_pairs` column records all optimal alternatives.
Branch lengths are parsed but **not used** by equal-cost parsimony. A
reconstructed change is conditional on the input alignment, topology, root
and cost model; it is not proof of the true historical mutation.

## 5. Write output that can be checked later

`writing.AtomicOutputSet` prepares temporary files, rejects input/output
collisions and existing output destinations unless `--force` was explicitly
requested, then commits the output set. `writing.write_results()` writes
`results.tsv` in input-site order, while `write_members()` lists the selected
clade's exact descendants.

`provenance.build_report()` records the input file hashes, selected branch,
rooting method, options, number of examined sites and SHA-256 hashes for the
result TSV and descendant list. It records **content identities**, not the
whole computational environment or the upstream variant-calling pipeline.
To verify the files later, compare their hashes to `report.json` and retain
the original alignment/tree and software version.

## 6. Test the claims rather than trusting an example

From the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -q
```

Production unit and regression tests do not replace independent scientific
validation. The separate [evidence index](https://github.com/RhysWhite/branchsnv-validation/blob/main/EVIDENCE_INDEX.md)
points to exhaustive oracle tests, deliberate-fault experiments, empirical
comparisons, and the frozen Experiment 07 benchmark. Compare its versioned
results against **the version you ran**, not whichever branch is newest.

For examples of why strict clade markers differ from branch substitutions,
see [Interpretation](../../interpretation.md) and the
[related papers and tools](../../references.md).
