# Branch selection

The selected object is an **edge**, represented by its child node under the
explicit root. Its descendant tips define the focal clade.

## Exact descendant file

```bash
branchsnv find ... --clade-tips lineage.txt
```

This is the recommended method for a manuscript or permanent analysis. It
records the exact intended membership independently of visual tree order.
BRANCHSNV requires the list to equal the descendants of one non-root node.

If the listed tips are non-monophyletic, BRANCHSNV reports that their MRCA
contains additional taxa and stops.

## MRCA selection

```bash
branchsnv find ... --mrca isolate_1 isolate_2 isolate_3
```

This is convenient during exploration. The named tips are anchors, not a full
membership declaration. The selected MRCA may contain other tips. Always inspect
the generated branch-membership file before using the result.

## Deterministic branch ID

```bash
branchsnv inspect ... --output branches.tsv
branchsnv find ... --branch-id b_0123456789abcdef
```

The ID hashes the sorted exact descendant names. It is invariant to sibling
order and Newick formatting outside taxon labels, but exact taxon-name content
—including internal spaces in quoted labels—is significant. A prefix is
accepted only when it matches one branch uniquely.

Descendant count alone is not a safe branch selector. Multiple branches can
have the same number of descendants, and counts do not record which taxa are
included.
