# 00 — End-to-end execution map

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `pyproject.toml`, `src/branchsnv/*.py`  
**Last checked against source:** 5 August 2026

This chapter provides the mental model needed before reading individual lines.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## The three commands

| Command | Reads | Main work | Writes |
|---|---|---|---|
| `branchsnv validate` | NEXUS, Newick, rooting choice | Parses, roots, and checks exact taxon-set equality | Nothing; prints a validation summary |
| `branchsnv inspect` | Newick, rooting choice | Roots the tree and assigns deterministic IDs to every non-root branch | Branch table TSV |
| `branchsnv find` | NEXUS, Newick, rooting choice, branch selector | Selects one branch, analyses every site, builds provenance | Results TSV, members file, report JSON |

## `find` control flow

```text
shell: branchsnv find ...
    │
    ├─ packaging launcher imports branchsnv.cli:main
    │
    ├─ main()
    │   ├─ constructs argparse parser
    │   ├─ validates command-line shape
    │   └─ dispatches to _run_find()
    │
    ├─ _run_find()
    │   ├─ rejects output/input path collisions
    │   ├─ read_transposed_nexus()
    │   │   ├─ removes comments without changing line structure
    │   │   ├─ finds one DATA/CHARACTERS block
    │   │   ├─ validates DIMENSIONS, FORMAT, TAXLABELS, MATRIX
    │   │   └─ returns immutable Alignment + Site records
    │   ├─ read_newick()
    │   │   ├─ parses labels, comments, branch lengths and topology
    │   │   └─ returns a mutable Node tree
    │   ├─ _root_tree()
    │   │   ├─ accepts the encoded root, or
    │   │   └─ reroots on an exact monophyletic outgroup edge
    │   ├─ validate_compatibility()
    │   │   └─ requires exact tree-tip/alignment-taxon equality
    │   ├─ _select_branch()
    │   │   ├─ exact descendant set, or
    │   │   ├─ MRCA anchors, or
    │   │   └─ deterministic branch ID
    │   ├─ analyse_branch()
    │   │   ├─ compiles the rooted tree once
    │   │   └─ for every alignment row:
    │   │       ├─ evaluates strict fixed-exclusive status
    │   │       ├─ reconstructs all optimal focal-edge state pairs
    │   │       ├─ classifies parsimony ambiguity
    │   │       └─ decides whether to report the row
    │   ├─ AtomicOutputSet stages all output files
    │   ├─ writes results and members to temporary files
    │   ├─ build_report() hashes inputs and staged outputs
    │   ├─ writes report to a temporary file
    │   └─ commit() replaces final output paths
    │
    └─ process exits 0 on success, 2 on expected input/I/O errors
```

## Two separate scientific questions

BRANCHSNV deliberately evaluates two definitions independently.

### Fixed-exclusive

A site qualifies only when:

1. every descendant taxon is callable as exactly `A`, `C`, `G`, or `T`;
2. every descendant has the same base;
3. every outside taxon is callable; and
4. no outside taxon has the descendant base.

This is a dataset-level marker definition. It does not prove that the state arose
on the focal edge.

### Parsimony reconstruction

The selected edge has a parent node and a child node. BRANCHSNV finds every
parent/child base pair that occurs in at least one globally minimum-cost Sankoff
reconstruction of the entire tree at that site. It does not choose one arbitrary
ancestral reconstruction when several tie.

## Core data transformations

```text
NEXUS row states in alignment order
    ↓ taxon-name lookup
leaf states attached to tree tips
    ↓ Sankoff down-pass
minimum subtree cost for A/C/G/T at every node
    ↓ outside-cost pass along root → focal parent
cost outside the focal child subtree
    ↓ enumerate 16 parent/child pairs
all pairs whose total equals the global optimum
    ↓ classification
unambiguous_change / change_state_ambiguous /
placement_ambiguous / no_change
```

## Determinism strategy

The source avoids outputs that depend on set or dictionary iteration order by:

- sorting descendant names before hashing and recording them;
- assigning branch IDs from sorted exact descendant names;
- ordering rerooted children by the smallest reachable tip name;
- sorting optimal state pairs and distinct state sets;
- sorting JSON keys and using fixed indentation;
- writing LF line endings explicitly; and
- omitting timestamps and absolute paths from the report.

The committed tests run the tool under different `PYTHONHASHSEED` values and
compare output bytes.
