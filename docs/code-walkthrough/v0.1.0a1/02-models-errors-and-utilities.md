# 02 — Models, exceptions, and deterministic utilities

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `src/branchsnv/models.py`, `src/branchsnv/errors.py`, `src/branchsnv/util.py`  
**Last checked against source:** 5 August 2026

These small modules define the objects and low-level helpers used by every analytical layer.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## Exception hierarchy: `errors.py`, lines 1–21

```python
 1  """BRANCHSNV exception types."""
 2  
 3  
 4  class BranchSNVError(Exception):
 5      """Base class for expected user-facing errors."""
 6  
 7  
 8  class NexusFormatError(BranchSNVError):
 9      """Raised when a NEXUS alignment is malformed or unsupported."""
10  
11  
12  class NewickFormatError(BranchSNVError):
13      """Raised when a Newick tree is malformed or unsupported."""
14  
15  
16  class ValidationError(BranchSNVError):
17      """Raised when inputs are individually valid but incompatible."""
18  
19  
20  class SelectionError(BranchSNVError):
21      """Raised when a requested branch cannot be selected unambiguously."""
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 1 | Module docstring. | Identifies expected BRANCHSNV exception types. |
| 4–5 | Defines `BranchSNVError`, inheriting from `Exception`. | `main()` catches this shared base class. |
| 8–9 | Defines `NexusFormatError`. | Malformed or unsupported NEXUS input. |
| 12–13 | Defines `NewickFormatError`. | Malformed or unsupported Newick input. |
| 16–17 | Defines `ValidationError`. | Inputs may parse individually but violate a cross-input or safety condition. |
| 20–21 | Defines `SelectionError`. | A requested outgroup, MRCA, branch, or taxon list cannot be resolved as requested. |

The classes contain no methods or extra data. Their value is semantic categorisation and shared user-facing handling.

## Tree node and tree traversal: `models.py`, lines 1–52

```python
 1  """Core immutable and tree data structures used by BRANCHSNV."""
 2  
 3  from __future__ import annotations
 4  
 5  from dataclasses import dataclass, field
 6  from pathlib import Path
 7  from typing import Iterator
 8  
 9  
10  @dataclass(eq=False)
11  class Node:
12      """A rooted tree node.
13  
14      ``name`` stores a tip label or an optional internal-node label. Internal
15      labels are not used to identify branches; branch identity is derived from
16      exact descendant-tip membership.
17      """
18  
19      name: str | None = None
20      length: float | None = None
21      children: list["Node"] = field(default_factory=list)
22      parent: "Node | None" = field(default=None, repr=False)
23  
24      @property
25      def is_tip(self) -> bool:
26          return not self.children
27  
28  
29  @dataclass
30  class Tree:
31      root: Node
32  
33      def iter_preorder(self) -> Iterator[Node]:
34          stack = [self.root]
35          while stack:
36              node = stack.pop()
37              yield node
38              stack.extend(reversed(node.children))
39  
40      def iter_postorder(self) -> Iterator[Node]:
41          stack: list[tuple[Node, bool]] = [(self.root, False)]
42          while stack:
43              node, visited = stack.pop()
44              if visited:
45                  yield node
46              else:
47                  stack.append((node, True))
48                  for child in reversed(node.children):
49                      stack.append((child, False))
50  
51      def tips(self) -> list[Node]:
52          return [node for node in self.iter_preorder() if node.is_tip]
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 1–7 | Docstring, postponed annotations, and imports. | `field` supplies safe list defaults; `Iterator` annotates traversal generators. |
| 10 | Applies `@dataclass(eq=False)` to `Node`. | Identity, not field equality, distinguishes nodes. This keeps nodes hashable by object identity for dictionaries and sets used throughout tree algorithms. |
| 11–17 | Declares `Node` and documents label semantics. | Internal labels are display metadata, never branch identity. |
| 19 | `name` may be a tip label, an internal label, or `None`. | Parsed tips are later required to have names. |
| 20 | `length` stores the incoming edge length, if present. | Topology-based analysis does not use length values. |
| 21 | Creates a fresh child list per node. | Avoids the shared-mutable-default bug. |
| 22 | Stores parent pointer, excluded from `repr`. | Parent links support MRCA paths and edge direction without recursive representations. |
| 24–26 | `is_tip` is true exactly when `children` is empty. | No separate node-type flag can become inconsistent. |
| 29–31 | Defines `Tree` with one root node. | Root is the entry point for all traversal. |
| 33–38 | Iterative preorder traversal: pop node, yield it, push reversed children. | Reversal preserves original left-to-right child order when using a LIFO stack and avoids recursion depth limits. |
| 40–49 | Iterative postorder traversal with `(node, visited)` markers. | Every child is yielded before its parent, required for descendant aggregation and Sankoff down-pass. |
| 51–52 | Materialises all nodes satisfying `is_tip`. | Returns a new list on each call. |

## Alignment records: `models.py`, lines 55–75

```python
55  @dataclass(frozen=True)
56  class Site:
57      site_id: str
58      states: str
59      input_row: int
60  
61  
62  @dataclass(frozen=True)
63  class Alignment:
64      path: Path
65      taxa: tuple[str, ...]
66      sites: tuple[Site, ...]
67      ntax: int
68      nchar: int
69      gap: str
70      missing: str
71      symbols: str
72  
73      @property
74      def taxon_index(self) -> dict[str, int]:
75          return {name: index for index, name in enumerate(self.taxa)}
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 55–59 | Defines immutable `Site(site_id, states, input_row)`. | `states` is one character per alignment taxon; `input_row` preserves original row order. |
| 62–71 | Defines immutable `Alignment`. | Stores source path, exact taxon order, immutable site tuple, declared dimensions, gap/missing symbols, and declared symbol string. |
| 73–75 | Builds a fresh `{taxon_name: column_index}` mapping on access. | Tree tips are attached to alignment columns by exact name rather than visual order. Duplicate taxa are rejected before this mapping is used. |

`frozen=True` prevents accidental reassignment of record fields, but contained objects would still be mutable if mutable values were supplied. Here, taxa and sites are tuples and strings, so the alignment representation is effectively immutable.

## Branch and result records: `models.py`, lines 78–119

```python
 78  @dataclass(frozen=True)
 79  class BranchRecord:
 80      branch_id: str
 81      short_id: str
 82      node: Node
 83      descendant_tips: tuple[str, ...]
 84      descendant_count: int
 85      parent_label: str
 86      child_label: str
 87  
 88  
 89  @dataclass(frozen=True)
 90  class ParsimonyResult:
 91      score: int
 92      status: str
 93      possible_pairs: tuple[tuple[str, str], ...]
 94      parent_states: tuple[str, ...]
 95      child_states: tuple[str, ...]
 96  
 97  
 98  @dataclass(frozen=True)
 99  class SiteResult:
100      site_id: str
101      reference: str
102      position: int | None
103      input_row: int
104      parent_states: str
105      child_states: str
106      possible_pairs: str
107      change: str
108      parsimony_status: str
109      fixed_within_clade: bool
110      exclusive_to_clade: bool
111      descendant_state: str
112      descendant_total: int
113      descendant_callable: int
114      descendant_state_count: int
115      outside_total: int
116      outside_callable: int
117      outside_same_state_count: int
118      parsimony_score: int
119      selection_reason: str
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 78–86 | Defines immutable `BranchRecord`. | Holds full/short deterministic IDs, the live focal child `Node`, sorted descendants, count, and display labels. |
| 89–95 | Defines immutable `ParsimonyResult`. | Carries global score, status, all optimal focal-edge pairs, and distinct parent/child state sets. |
| 98–119 | Defines immutable `SiteResult`, mirroring the output TSV fields. | Combines coordinate parsing, parsimony reconstruction, strict marker counts, and selection reason into one row object. |

### Important nuance

`BranchRecord` is frozen, but its `node` points to a mutable tree node. The record prevents replacing the pointer; it does not freeze the entire tree. BRANCHSNV does not mutate the rooted tree after branch records are generated.

## SHA-256 helpers: `util.py`, lines 1–19

```python
 1  """Small deterministic utilities."""
 2  
 3  from __future__ import annotations
 4  
 5  import hashlib
 6  from pathlib import Path
 7  
 8  
 9  def sha256_file(path: Path) -> str:
10      digest = hashlib.sha256()
11      with path.open("rb") as handle:
12          for chunk in iter(lambda: handle.read(1024 * 1024), b""):
13              digest.update(chunk)
14      return digest.hexdigest()
15  
16  
17  def sha256_lines(values: list[str] | tuple[str, ...]) -> str:
18      payload = "".join(f"{value}\n" for value in values).encode("utf-8")
19      return hashlib.sha256(payload).hexdigest()
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 1–6 | Docstring and imports. | Uses only the standard library. |
| 9 | Declares file hashing. | Returns lowercase hexadecimal text. |
| 10 | Creates a SHA-256 digest object. | Fresh digest per file. |
| 11 | Opens the file in binary mode. | Hashes bytes, not decoded text. |
| 12–13 | Reads 1 MiB chunks until `b""`, updating the digest. | Avoids loading large alignments into memory a second time solely for hashing. |
| 14 | Returns 64 hex characters. | Used for inputs and output provenance. |
| 17 | Declares deterministic line-list hashing. | Accepts list or tuple of strings. |
| 18 | Appends `\n` to every value, concatenates, and UTF-8 encodes. | The delimiter makes `("ab", "c")` distinct from `("a", "bc")`; a terminal newline is part of the identity. |
| 19 | Hashes the payload in one operation. | Used for branch membership and branch IDs. |

Callers sort descendant names before `sha256_lines`, so membership identity is independent of sibling order. The function itself does not sort.

## Coordinate parsing and Boolean text: `util.py`, lines 22–32

```python
22  def parse_coordinate(site_id: str) -> tuple[str, int | None]:
23      """Split a terminal ``_<integer>`` coordinate without guessing earlier underscores."""
24  
25      head, separator, tail = site_id.rpartition("_")
26      if separator and head and tail.isdigit():
27          return head, int(tail)
28      return site_id, None
29  
30  
31  def bool_text(value: bool) -> str:
32      return "true" if value else "false"
```

| Line(s) | Literal effect | Examples |
|---|---|---|
| 22–23 | Defines coordinate parsing and documents that only the terminal underscore is considered. | Earlier underscores remain part of the reference identifier. |
| 25 | Splits at the final underscore into `(head, separator, tail)`. | `chr_part_25` → `chr_part`, `_`, `25`. |
| 26–27 | If there is a nonempty head and an all-digit tail, returns `(head, int(tail))`. | `ref_001` becomes position integer `1`; original `site_id` is still retained elsewhere. |
| 28 | Otherwise returns the complete identifier and `None`. | `ref_x`, `_12`, and `ref_-1` are not guessed as coordinates. |
| 31–32 | Converts a Python Boolean to lowercase JSON-like text. | TSV uses `true`/`false`, not `True`/`False`. |

## Invariants supplied by these modules

- Nodes are compared by identity, not by matching fields.
- Alignment column order is explicit and recoverable by exact taxon name.
- Branch identity is based on descendant membership, not internal labels or lengths.
- Result records have a fixed field-level contract with output writers.
- Hashes are byte- or canonical-line-content based.
