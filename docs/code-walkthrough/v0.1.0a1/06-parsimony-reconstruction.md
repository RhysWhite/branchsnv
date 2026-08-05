# 06 — Exact focal-edge Sankoff parsimony

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `src/branchsnv/parsimony.py`  
**Last checked against source:** 5 August 2026

This chapter explains the dynamic program that retains every globally optimal parent–child nucleotide pair across one selected rooted edge.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## State encoding and leaf costs: lines 1–32

```python
 1  """Exact unordered-state Sankoff reconstruction for a selected rooted branch."""
 2  
 3  from __future__ import annotations
 4  
 5  from dataclasses import dataclass
 6  
 7  from .errors import ValidationError
 8  from .models import Node, ParsimonyResult, Tree
 9  
10  _STATES = ("A", "C", "G", "T")
11  _INF = 10**8
12  _IUPAC_MASKS = {
13      "A": 0b0001,
14      "C": 0b0010,
15      "G": 0b0100,
16      "T": 0b1000,
17      "R": 0b0101,
18      "Y": 0b1010,
19      "S": 0b0110,
20      "W": 0b1001,
21      "K": 0b1100,
22      "M": 0b0011,
23      "B": 0b1110,
24      "D": 0b1101,
25      "H": 0b1011,
26      "V": 0b0111,
27      "N": 0b1111,
28  }
29  _LEAF_COSTS = {
30      symbol: tuple(0 if mask & (1 << state) else _INF for state in range(4))
31      for symbol, mask in _IUPAC_MASKS.items()
32  }
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 1 | Module docstring. | “Unordered-state” means every change between distinct bases costs one. |
| 3–8 | Imports annotations, dataclass, validation error, and tree/result models. | No numerical dependency. |
| 10 | Fixes state index order as `A, C, G, T`. | All cost vectors use this order. |
| 11 | Defines a large finite sentinel cost. | Makes incompatible leaf states effectively impossible in realistic trees while retaining integer arithmetic. |
| 12–28 | Maps every IUPAC symbol to a four-bit compatible-state mask. | For example `R` permits A/G and `N` permits all four. |
| 29–32 | Precomputes a four-entry cost tuple for every IUPAC symbol: zero for permitted states, `_INF` otherwise. | Avoids rebuilding leaf vectors for every site and tip. |

Gap and configured missing symbols are not in this table during reconstruction; they receive `[0,0,0,0]` directly and are therefore unknown among A/C/G/T, not a fifth state.

## `CompiledTree`: lines 35–44

```python
35  @dataclass(frozen=True)
36  class CompiledTree:
37      nodes: tuple[Node, ...]
38      root_index: int
39      children: tuple[tuple[int, ...], ...]
40      postorder: tuple[int, ...]
41      tip_alignment_index: tuple[int, ...]
42      focal_parent: int
43      focal_child: int
44      path_to_focal_parent: tuple[int, ...]
```

| Field | Meaning |
|---|---|
| `nodes` | Rooted preorder tuple of actual `Node` objects. |
| `root_index` | Integer index of root in `nodes`. |
| `children` | For each node index, tuple of child indices. |
| `postorder` | Node indices in child-before-parent order. |
| `tip_alignment_index` | For each node, alignment column index; internals use `-1`. |
| `focal_parent`, `focal_child` | Integer endpoints of selected edge. |
| `path_to_focal_parent` | Root-to-focal-parent node indices, inclusive. |

The dataclass is frozen, so the topology/index plan can be safely reused for every alignment site.

## `compile_tree`: lines 47–84

```python
47  def compile_tree(
48      tree: Tree,
49      focal_node: Node,
50      alignment_taxon_index: dict[str, int],
51  ) -> CompiledTree:
52      nodes = tuple(tree.iter_preorder())
53      node_index = {node: index for index, node in enumerate(nodes)}
54      if focal_node is tree.root or focal_node.parent is None:
55          raise ValidationError("The selected branch must lead to a non-root node.")
56  
57      children: list[tuple[int, ...]] = []
58      tip_alignment_index: list[int] = [-1] * len(nodes)
59      for index, node in enumerate(nodes):
60          children.append(tuple(node_index[child] for child in node.children))
61          if node.is_tip:
62              assert node.name is not None
63              if node.name not in alignment_taxon_index:
64                  raise ValidationError(f"Tree tip {node.name!r} is absent from the alignment.")
65              tip_alignment_index[index] = alignment_taxon_index[node.name]
66  
67      focal_parent = node_index[focal_node.parent]
68      path_nodes: list[Node] = []
69      cursor: Node | None = focal_node.parent
70      while cursor is not None:
71          path_nodes.append(cursor)
72          cursor = cursor.parent
73      path_nodes.reverse()
74  
75      return CompiledTree(
76          nodes=nodes,
77          root_index=node_index[tree.root],
78          children=tuple(children),
79          postorder=tuple(node_index[node] for node in tree.iter_postorder()),
80          tip_alignment_index=tuple(tip_alignment_index),
81          focal_parent=focal_parent,
82          focal_child=node_index[focal_node],
83          path_to_focal_parent=tuple(node_index[node] for node in path_nodes),
84      )
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 47–51 | Declares compilation from rooted tree, focal child node, and alignment taxon map. | The selected branch is represented by its child node. |
| 52 | Materialises rooted preorder nodes. | Stable integer indices replace repeated object/dictionary work per site. |
| 53 | Maps node identity to index. | `Node(eq=False)` makes identity hashing available. |
| 54–55 | Rejects root or parentless focal node. | Focal branch must have two endpoints. |
| 57 | Starts child-index list. | One tuple per node. |
| 58 | Creates `-1` alignment index for every node. | Only tip entries are overwritten. |
| 59–60 | For every node, converts child pointers to integer indices. | Encodes topology compactly. |
| 61–65 | For tips, asserts name, requires it in alignment map, stores column index. | Protects exact tip-to-state mapping even if compatibility validation was bypassed programmatically. |
| 67 | Stores focal parent index. | `focal_node.parent` is known non-`None`. |
| 68–73 | Walks focal parent to root, stores nodes, then reverses. | Produces root→parent path for the restricted outside-cost pass. |
| 75–84 | Constructs immutable `CompiledTree`, including postorder indices and focal child index. | This object is reused for all sites in `analyse_branch`. |

## `reconstruct_site`: lines 88–214

```python
 88  def reconstruct_site(
 89      compiled: CompiledTree,
 90      states: str,
 91      gap: str,
 92      missing: str,
 93  ) -> ParsimonyResult:
 94      """Return every globally optimal state pair across the selected edge.
 95  
 96      The down-pass is performed for the whole tree. The outside-cost pass is
 97      restricted to the single root-to-focal-parent path, avoiding unnecessary
 98      work on branches that cannot affect the selected edge.
 99      """
100  
101      node_count = len(compiled.nodes)
102      down: list[list[int]] = [[0, 0, 0, 0] for _ in range(node_count)]
103      gap_upper = gap.upper()
104      missing_upper = missing.upper()
105  
106      for node_index in compiled.postorder:
107          child_indices = compiled.children[node_index]
108          if not child_indices:
109              symbol = states[compiled.tip_alignment_index[node_index]].upper()
110              if symbol == gap_upper or symbol == missing_upper:
111                  down[node_index] = [0, 0, 0, 0]
112              else:
113                  try:
114                      down[node_index] = list(_LEAF_COSTS[symbol])
115                  except KeyError as exc:
116                      raise ValidationError(f"Unsupported nucleotide state symbol {symbol!r}.") from exc
117              continue
118  
119          total0 = total1 = total2 = total3 = 0
120          for child_index in child_indices:
121              child = down[child_index]
122              child_min = min(child)
123              alt = child_min + 1
124              value = child[0]
125              total0 += value if value <= alt else alt
126              value = child[1]
127              total1 += value if value <= alt else alt
128              value = child[2]
129              total2 += value if value <= alt else alt
130              value = child[3]
131              total3 += value if value <= alt else alt
132          down[node_index] = [total0, total1, total2, total3]
133  
134      optimal_score = min(down[compiled.root_index])
135  
136      # up_cost is conditioned on the current path node state and contains only
137      # information outside that node's subtree.
138      up_cost = [0, 0, 0, 0]
139      path = compiled.path_to_focal_parent
140      for path_position in range(len(path) - 1):
141          parent_index = path[path_position]
142          child_on_path = path[path_position + 1]
143          sibling0 = sibling1 = sibling2 = sibling3 = 0
144          for sibling_index in compiled.children[parent_index]:
145              if sibling_index == child_on_path:
146                  continue
147              sibling = down[sibling_index]
148              sibling_min = min(sibling)
149              alt = sibling_min + 1
150              value = sibling[0]
151              sibling0 += value if value <= alt else alt
152              value = sibling[1]
153              sibling1 += value if value <= alt else alt
154              value = sibling[2]
155              sibling2 += value if value <= alt else alt
156              value = sibling[3]
157              sibling3 += value if value <= alt else alt
158  
159          base = [
160              up_cost[0] + sibling0,
161              up_cost[1] + sibling1,
162              up_cost[2] + sibling2,
163              up_cost[3] + sibling3,
164          ]
165          base_min = min(base)
166          alternative = base_min + 1
167          up_cost = [
168              base[0] if base[0] <= alternative else alternative,
169              base[1] if base[1] <= alternative else alternative,
170              base[2] if base[2] <= alternative else alternative,
171              base[3] if base[3] <= alternative else alternative,
172          ]
173  
174      parent_index = compiled.focal_parent
175      child_index = compiled.focal_child
176      sibling_costs = [0, 0, 0, 0]
177      for sibling_index in compiled.children[parent_index]:
178          if sibling_index == child_index:
179              continue
180          sibling = down[sibling_index]
181          sibling_min = min(sibling)
182          alt = sibling_min + 1
183          for state in range(4):
184              value = sibling[state]
185              sibling_costs[state] += value if value <= alt else alt
186  
187      possible_pairs: list[tuple[str, str]] = []
188      child_down = down[child_index]
189      for parent_state in range(4):
190          outside = up_cost[parent_state] + sibling_costs[parent_state]
191          for child_state in range(4):
192              pair_cost = outside + (parent_state != child_state) + child_down[child_state]
193              if pair_cost == optimal_score:
194                  possible_pairs.append((_STATES[parent_state], _STATES[child_state]))
195  
196      if not possible_pairs:
197          raise ValidationError("Internal error: no optimal reconstruction for the selected edge.")
198  
199      unique_pairs = tuple(sorted(set(possible_pairs)))
200      changes = [parent != child for parent, child in unique_pairs]
201      if all(changes):
202          status = "unambiguous_change" if len(unique_pairs) == 1 else "change_state_ambiguous"
203      elif any(changes):
204          status = "placement_ambiguous"
205      else:
206          status = "no_change"
207  
208      return ParsimonyResult(
209          score=optimal_score,
210          status=status,
211          possible_pairs=unique_pairs,
212          parent_states=tuple(sorted({pair[0] for pair in unique_pairs})),
213          child_states=tuple(sorted({pair[1] for pair in unique_pairs})),
214      )
```

### Setup and Sankoff down-pass: lines 88–134

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 88–99 | Defines reconstruction and documents full-tree down-pass plus path-restricted outside pass. | Returns every optimal focal-edge pair, not one traceback. |
| 101 | Gets number of compiled nodes. | Sets cost-matrix height. |
| 102 | Creates one mutable four-state down-cost vector per node. | `down[v][s]` becomes minimum cost inside node `v`'s subtree when `v` has state `s`. |
| 103–104 | Uppercases configured gap and missing characters. | State comparison is case-insensitive. |
| 106 | Processes nodes in postorder. | Child costs are complete before parent calculation. |
| 107–108 | Gets child indices and detects leaves by empty child tuple. | Mirrors `Node.is_tip`. |
| 109 | Retrieves the leaf's alignment character using precompiled taxon index. | Tree order is irrelevant. |
| 110–111 | Treats configured gap or missing as any of A/C/G/T at zero leaf cost. | Unknown, not an extra evolutionary state. |
| 112–116 | Otherwise loads precomputed IUPAC cost vector; wraps unknown symbols as `ValidationError`. | Parser should already reject unsupported symbols, but this protects programmatic calls. |
| 117 | Continues to next node after leaf setup. | Prevents internal calculation on leaves. |
| 119 | Initialises total cost for each possible current node state. | Four scalars are used for speed. |
| 120–131 | For every child and each current state, adds the smaller of: child having same state, or child's best state plus one change. | This is the unordered equal-cost Sankoff recurrence, optimized from a four-way minimum. |
| 132 | Stores parent down vector. | Completes this subtree. |
| 134 | Takes minimum root state cost as global parsimony score. | Root state is not fixed. |

### Outside-cost pass to focal parent: lines 136–173

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 136–138 | Documents and initialises `up_cost=[0,0,0,0]` at root. | Nothing exists outside root's subtree. |
| 139 | Retrieves root→focal-parent path. | Includes focal parent. |
| 140 | Iterates every path edge except beyond focal parent. | Updates outside costs one level downward. |
| 141–142 | Identifies current path parent and next path child. | Siblings of next child contribute to its outside context. |
| 143 | Initialises sibling contribution by current parent state. | Four totals. |
| 144–157 | For every off-path sibling, adds its best conditional contribution using same unordered recurrence. | Includes all data in sibling subtrees while excluding the path child subtree. |
| 159–164 | Adds current node's prior outside cost and its off-path sibling costs. | `base[p]` is total outside the path child if current node state is `p`. |
| 165–172 | Transforms `base` across the path edge: same state costs `base[s]`; a different parent state costs global minimum `base+1`. | Produces costs conditioned on the path child's state. |

### Focal-edge pair enumeration: lines 174–199

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 174–175 | Gets focal parent and child indices. | Defines edge being interrogated. |
| 176 | Initialises contributions from focal child's siblings. | These are outside the focal child subtree but inside focal parent subtree. |
| 177–185 | Sums conditional sibling costs for every parent state. | Same equal-cost recurrence. |
| 187 | Creates pair list. | At most 16 A/C/G/T ordered pairs. |
| 188 | Retrieves focal child down vector. | Represents all data below the selected edge. |
| 189–194 | For each parent and child state, computes outside + edge-change indicator + child subtree cost; retains pair exactly when total equals global optimum. | `(parent_state != child_state)` is a Boolean used as integer 0/1. Equality to global optimum ensures every retained pair belongs to at least one globally optimal reconstruction. |
| 196–197 | Raises if no pair was found. | Indicates an internal inconsistency, not ordinary input ambiguity. |
| 199 | De-duplicates and lexicographically sorts pairs. | Output is deterministic. |

### Classification and return: lines 200–214

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 200 | Converts each pair to a change/no-change Boolean. | One value per unique optimal pair. |
| 201–202 | If every pair changes, status is `unambiguous_change` only for one pair; otherwise `change_state_ambiguous`. | A change is certain, but exact transition may not be. |
| 203–204 | If some but not all pairs change, status is `placement_ambiguous`. | There are equally optimal reconstructions with and without a focal-edge change. |
| 205–206 | If no pair changes, status is `no_change`. | The focal edge never changes in an optimum. |
| 208–214 | Returns score, status, all pairs, and sorted distinct parent/child state sets. | No arbitrary ancestral state is chosen. |

## Why pair enumeration is sufficient

For a fixed parent state and child state, the down-pass supplies the best cost in
the child subtree; the outside pass and focal siblings supply the best cost
outside it; and the edge contributes zero or one. If their sum equals the global
root optimum, at least one complete globally optimal assignment has that pair.
If it is greater, no globally optimal assignment can use that pair.

## Tests most relevant to this chapter

- clean focal change and no-change cases;
- placement ambiguity from a parallel pattern;
- missing descendant is not forced;
- exhaustive oracle comparison across generated patterns;
- regression guards for wrong branch side, majority-state substitution, gap as a fifth state, and arbitrary tie resolution.
