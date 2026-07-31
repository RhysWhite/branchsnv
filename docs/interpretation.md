# Interpretation guide

## What a fixed-exclusive result means

At the supplied site, every descendant of the selected branch has the same
unambiguous nucleotide, every outside taxon is unambiguously callable, and the
descendant nucleotide is absent outside the clade.

This is a strong marker in the supplied dataset. It is not proof that the state
will remain exclusive after additional sampling.

## What an unambiguous parsimony change means

Under the supplied rooted topology and an unordered equal-cost model, every
globally most-parsimonious reconstruction assigns one specific state to the
parent and another specific state to the child of the selected edge.

It does not mean:

- that the substitution was experimentally observed in the ancestor;
- that the site is free from recombination;
- that likelihood or Bayesian reconstruction would give the same result;
- that the change is unique elsewhere in the tree;
- that the mutation caused acquisition of a mobile element or phenotype; or
- that the tree itself is correct.

## Ambiguous categories

`change_state_ambiguous` means a change is required on the edge, but the exact
transition is not unique across optimal reconstructions.

`placement_ambiguous` means some optimal reconstructions place a change on the
edge and others place it elsewhere. Such a site should not be described as a
resolved branch substitution.

## Fixed-exclusive and parsimony can disagree

A perfect clade marker can still have ambiguous placement if the ancestral state
is not resolved. A branch change can also recur outside the clade, making it
non-exclusive. BRANCHSNV preserves both questions rather than merging them.

## Suggested reporting language

For fixed-exclusive mode:

> We identified nucleotide states fixed among all descendants of the selected
> branch and absent from all callable genomes outside the clade.

For unambiguous parsimony mode:

> We identified substitutions assigned unambiguously to the selected branch
> across all globally optimal equal-cost parsimony reconstructions.

Always report the alignment filtering, tree-building method, rooting method,
branch-selection rule, BRANCHSNV version, and whether ambiguous sites were
included.
