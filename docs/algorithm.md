# Algorithm

## 1. Input validation

BRANCHSNV parses one transposed nucleotide NEXUS matrix and one Newick tree.
Before analysis it verifies that:

- `NTAX` equals the number of unique taxon labels;
- `NCHAR` equals the number of unique matrix rows;
- every matrix row contains exactly `NTAX` states;
- every tree tip name is unique;
- the tree and alignment taxon sets are identical; and
- the requested branch exists under the explicit root.

Taxa are matched by exact string equality. Matrix column order and Newick tip
order are irrelevant.

## 2. Rooting

With `--outgroup` or `--outgroup-file`, BRANCHSNV identifies the unique edge
whose one side contains exactly the requested outgroup taxa. If the existing
root already lies on that edge, it is retained. Otherwise, the tree is
reoriented on that edge. A degree-two artificial Newick root is suppressed
before reorientation.

With `--accept-existing-root`, no rerooting occurs.

## 3. Branch identity

For every non-root node, the exact descendant-tip names are sorted and serialized
as one UTF-8 line per name. The branch identifier is:

```text
b_<SHA-256 of sorted descendant lines>
```

This identifier is invariant to sibling order, whitespace, comments, internal
labels, and branch lengths. It can change when taxon membership or rooting
changes, which is intentional.

## 4. Fixed-exclusive analysis

For a selected branch with descendant set `D` and outside set `O`, a site is a
strict fixed-exclusive marker when:

```text
all states in D are unambiguous A/C/G/T
all states in D are identical
all states in O are unambiguous A/C/G/T
no state in O equals the state fixed in D
```

No majority threshold is used. Missing or ambiguous data on either side prevent
a fixed-exclusive call.

## 5. Parsimony analysis

BRANCHSNV applies unordered equal-cost Sankoff parsimony over four states:

```text
A, C, G, T
```

The transition cost is zero when two adjacent states are equal and one when
they differ. Standard IUPAC symbols are represented by their compatible state
sets. The declared gap and missing symbols are treated as unknown among all
four states, not as a fifth nucleotide.

### Down-pass

For each node `v` and state `s`, BRANCHSNV calculates:

```text
down[v, s] = minimum cost within the subtree rooted at v,
             conditional on v having state s
```

For a leaf, compatible states cost zero and incompatible states are impossible.
For an internal node, costs are summed independently over children.

### Outside cost along the focal path

Only the path from the root to the parent of the selected branch is required.
For each path node and state, BRANCHSNV calculates the minimum cost outside that
node's subtree conditional on the node state. This avoids a full all-branches
up-pass while preserving exactness for the selected edge.

### Focal-edge state pairs

For each of the 16 parent-child state pairs on the selected edge, BRANCHSNV
combines:

- the cost outside the parent subtree;
- all sibling-subtree costs;
- the focal edge transition cost; and
- the child-subtree cost.

Every pair whose combined cost equals the whole-tree optimum is retained.
BRANCHSNV never chooses one arbitrary optimal reconstruction.

The classification is:

- `unambiguous_change`: exactly one optimal pair and the states differ;
- `change_state_ambiguous`: all optimal pairs differ, but multiple transitions
  are possible;
- `placement_ambiguous`: at least one optimal pair changes and at least one does
  not;
- `no_change`: all optimal pairs have equal parent and child states.

## 6. Determinism

Results retain matrix input-row order. Branch members
are sorted lexicographically. JSON keys are sorted. UTF-8 encoding and LF line
endings are used. Absolute paths and timestamps are omitted.

## 7. Complexity

For `S` sites, `N` tree nodes, and four nucleotide states, the dominant cost is
approximately `O(S × N × 4)`. Memory use for the alignment is proportional to
`NTAX × NCHAR`; per-site parsimony storage is proportional to the number of tree
nodes.
