# 05 — Tree operations, rooting, and branch selection

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `src/branchsnv/newick.py (lines 189–421)`  
**Last checked against source:** 5 August 2026

This chapter covers descendant calculation, branch identity, exact and MRCA selection, and deterministic outgroup rerooting.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## `descendant_tip_map`: lines 189–200

```python
189  def descendant_tip_map(tree: Tree) -> dict[Node, tuple[str, ...]]:
190      result: dict[Node, tuple[str, ...]] = {}
191      for node in tree.iter_postorder():
192          if node.is_tip:
193              assert node.name is not None
194              result[node] = (node.name,)
195          else:
196              names: list[str] = []
197              for child in node.children:
198                  names.extend(result[child])
199              result[node] = tuple(sorted(names))
200      return result
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 189 | Declares mapping from each `Node` object to a sorted tuple of descendant tip names. | Node identity is the key. |
| 190 | Creates empty result dictionary. | Filled bottom-up. |
| 191 | Traverses nodes postorder. | Children are available before parent aggregation. |
| 192–194 | For a tip, asserts name and stores a one-item tuple. | Parser validation makes the assertion safe for parsed trees. |
| 195–199 | For an internal node, extends names from children and sorts the full list. | Sorting removes sibling-order dependence from descendants and downstream hashes. |
| 200 | Returns map for every node including root. | Recomputed when called; no cache. |

## Display labels and branch records: lines 203–238

```python
203  def _display_label(node: Node, descendants: tuple[str, ...]) -> str:
204      if node.is_tip:
205          assert node.name is not None
206          return node.name
207      if node.name:
208          return node.name
209      return f"internal[{len(descendants)} tips]"
210  
211  
212  def branch_records(tree: Tree) -> list[BranchRecord]:
213      descendants = descendant_tip_map(tree)
214      records: list[BranchRecord] = []
215      full_ids: set[str] = set()
216      for node in tree.iter_preorder():
217          if node is tree.root:
218              continue
219          tips = descendants[node]
220          digest = sha256_lines(tips)
221          branch_id = f"b_{digest}"
222          if branch_id in full_ids:
223              raise ValidationError("Two branches unexpectedly produced the same descendant-set hash.")
224          full_ids.add(branch_id)
225          parent = node.parent
226          assert parent is not None
227          records.append(
228              BranchRecord(
229                  branch_id=branch_id,
230                  short_id=branch_id[:18],
231                  node=node,
232                  descendant_tips=tips,
233                  descendant_count=len(tips),
234                  parent_label=_display_label(parent, descendants[parent]),
235                  child_label=_display_label(node, tips),
236              )
237          )
238      return records
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 203–209 | `_display_label` returns tip name, then internal name if present, otherwise `internal[N tips]`. | Display labels are human-readable only; they are not branch IDs. |
| 212 | Defines generation of all non-root branch records. | One record per incoming edge to a non-root node. |
| 213–215 | Computes descendant map, creates record list and collision set. | Full IDs are checked within this tree. |
| 216–218 | Traverses preorder and skips root. | Root has no incoming branch. |
| 219 | Retrieves sorted exact descendants for the child node. | This is the branch's biological membership under the current root. |
| 220 | Hashes names with terminal newlines. | Deterministic membership digest. |
| 221 | Prefixes digest with `b_`. | Distinguishes branch IDs from raw hashes. |
| 222–224 | Rejects an unexpected full-ID collision, then records the ID. | A cryptographic collision is extraordinarily unlikely; the guard prevents silent ambiguity. |
| 225–226 | Retrieves and asserts parent. | Non-root nodes must have one parent. |
| 227–237 | Constructs `BranchRecord`; short ID is first 18 characters, i.e. `b_` plus 16 hex characters. | Records node pointer, membership, count, and display labels. |
| 238 | Returns records in rooted preorder. | `write_branches` later imposes its own output sorting. |

Branch IDs ignore sibling order, branch lengths, and internal labels. They intentionally change when rooting changes descendant membership.

## `resolve_branch_id`: lines 241–251

```python
241  def resolve_branch_id(records: list[BranchRecord], identifier: str) -> BranchRecord:
242      matches = [record for record in records if record.branch_id == identifier]
243      if not matches:
244          matches = [record for record in records if record.branch_id.startswith(identifier)]
245      if not matches:
246          raise SelectionError(f"No branch matches identifier {identifier!r}.")
247      if len(matches) > 1:
248          raise SelectionError(
249              f"Branch identifier prefix {identifier!r} is ambiguous; provide more characters."
250          )
251      return matches[0]
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 241 | Declares resolution from records plus user identifier. | Identifier may be full ID or prefix. |
| 242 | First searches exact equality. | Exact match takes precedence. |
| 243–244 | If none, searches `startswith`. | Allows short IDs and longer unique prefixes. |
| 245–246 | Rejects no matches. | Error quotes identifier with `repr`. |
| 247–250 | Rejects more than one prefix match and asks for more characters. | Prevents arbitrary first-match selection. |
| 251 | Returns the only match. | Preserves original `BranchRecord`/node identity. |

## Exact descendant selection: lines 254–276

```python
254  def select_exact_descendants(tree: Tree, requested: set[str]) -> BranchRecord:
255      if not requested:
256          raise SelectionError("The descendant-tip list is empty.")
257      all_tips = {tip.name for tip in tree.tips()}
258      missing = sorted(requested - all_tips)
259      if missing:
260          raise SelectionError(
261              "Requested descendant tip(s) are absent from the tree: " + ", ".join(missing[:10])
262          )
263      records = branch_records(tree)
264      exact = [record for record in records if set(record.descendant_tips) == requested]
265      if exact:
266          return exact[0]
267      mrca = find_mrca(tree, requested)
268      descendants = descendant_tip_map(tree)[mrca]
269      extras = sorted(set(descendants) - requested)
270      message = "Requested tips do not form exactly one rooted clade."
271      if extras:
272          message += " Their MRCA also contains: " + ", ".join(extras[:10])
273          if len(extras) > 10:
274              message += f" (and {len(extras) - 10} more)"
275          message += "."
276      raise SelectionError(message)
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 254 | Declares strict selection from a requested set. | The set must equal one branch's complete descendants. |
| 255–256 | Rejects an empty request. | No empty clade interpretation. |
| 257 | Builds set of all tip names. | Parsed-tree invariant means names are non-`None`. |
| 258–262 | Rejects requested names absent from the tree, displaying up to ten. | Selection does not silently drop names. |
| 263 | Generates branch records under the current root. | Selection is root-dependent. |
| 264 | Filters records whose descendant set exactly equals the request. | Not merely subset or MRCA containment. |
| 265–266 | Returns the first exact record. | Distinct branches cannot have the same exact descendant set in a valid rooted tree. |
| 267 | If no exact branch, finds MRCA for diagnosis. | Enables a useful non-monophyly explanation. |
| 268–269 | Gets MRCA descendants and computes extra taxa. | Extras show why the request is not exact. |
| 270 | Starts generic failure message. | Always raised when no exact record. |
| 271–275 | Appends up to ten extras and count of additional extras. | If requested tips are non-monophyletic, their MRCA contains extras. |
| 276 | Raises `SelectionError`. | No approximation is returned. |

## MRCA calculation and branch selection: lines 279–312

```python
279  def find_mrca(tree: Tree, requested: set[str]) -> Node:
280      if not requested:
281          raise SelectionError("At least one tip is required to identify an MRCA.")
282      tip_nodes = {tip.name: tip for tip in tree.tips()}
283      missing = sorted(requested - tip_nodes.keys())
284      if missing:
285          raise SelectionError("MRCA tip(s) absent from tree: " + ", ".join(missing[:10]))
286  
287      ancestor_paths: list[list[Node]] = []
288      for name in sorted(requested):
289          node = tip_nodes[name]
290          path: list[Node] = []
291          while node is not None:
292              path.append(node)
293              node = node.parent  # type: ignore[assignment]
294          ancestor_paths.append(path)
295  
296      common = set(ancestor_paths[0])
297      for path in ancestor_paths[1:]:
298          common.intersection_update(path)
299      for node in ancestor_paths[0]:
300          if node in common:
301              return node
302      raise SelectionError("Could not determine an MRCA.")
303  
304  
305  def select_mrca_branch(tree: Tree, requested: set[str]) -> BranchRecord:
306      node = find_mrca(tree, requested)
307      if node is tree.root:
308          raise SelectionError("The requested MRCA is the root and has no incoming branch.")
309      for record in branch_records(tree):
310          if record.node is node:
311              return record
312      raise SelectionError("Could not resolve the branch leading to the requested MRCA.")
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 279–281 | `find_mrca` rejects an empty request. | At least one anchor is meaningful; a single tip's MRCA is that tip. |
| 282 | Maps exact tip names to node objects. | Duplicate tree names were already rejected. |
| 283–285 | Rejects missing anchors. | Displays up to ten. |
| 287 | Creates list of ancestor paths. | Each path runs tip→root. |
| 288 | Processes requested names in sorted order. | Makes which path is used for the final depth search deterministic. |
| 289–294 | Walks each node's parent pointers to root, storing the path. | The type-ignore permits assigning optional parent back into a variable inferred as nonoptional `Node`. |
| 296–298 | Intersects all ancestor-node sets. | Leaves only nodes ancestral to every requested tip. |
| 299–301 | Scans the first tip→root path and returns first common node. | First is the deepest common ancestor, therefore the MRCA. |
| 302 | Defensive failure if no common node exists. | A connected tree should always share the root. |
| 305–306 | `select_mrca_branch` obtains the MRCA node. | Converts a node result into an incoming branch record. |
| 307–308 | Rejects root MRCA because root has no incoming branch. | Prevents undefined focal edge. |
| 309–311 | Generates branch records and returns the one with identical node object. | Uses identity, not labels. |
| 312 | Defensive failure if record lookup somehow fails. | Should not occur for a valid non-root node. |

## `reroot_on_outgroup`: lines 315–421

```python
315  def reroot_on_outgroup(tree: Tree, outgroup: set[str]) -> Tree:
316      """Root on the unique edge separating exactly the requested outgroup tips.
317  
318      Branch lengths are irrelevant to BRANCHSNV's topology-based analysis. When a
319      new root is inserted, the selected edge length is split evenly if present.
320      """
321  
322      if not outgroup:
323          raise ValidationError("At least one outgroup tip is required.")
324      tip_names = {tip.name for tip in tree.tips()}
325      missing = sorted(outgroup - tip_names)
326      if missing:
327          raise ValidationError("Outgroup tip(s) absent from tree: " + ", ".join(missing[:10]))
328      if outgroup == tip_names:
329          raise ValidationError("The outgroup cannot contain every tree tip.")
330  
331      descendants = descendant_tip_map(tree)
332      all_tips = set(descendants[tree.root])
333  
334      # If the existing root already lies on the requested outgroup edge, retain
335      # it exactly. A degree-two root splits one unrooted edge into two rooted
336      # edges, which would otherwise appear as two equivalent matches.
337      if len(tree.root.children) == 2:
338          root_sides = [set(descendants[child]) for child in tree.root.children]
339          if outgroup in root_sides:
340              return tree
341  
342      selected_child: Node | None = None
343      for node, tips_tuple in descendants.items():
344          if node is tree.root:
345              continue
346          side = set(tips_tuple)
347          if side == outgroup or all_tips - side == outgroup:
348              if selected_child is not None:
349                  # A singleton tip can match only one biological edge; duplicate
350                  # matches would indicate a pathological degree-two representation.
351                  raise ValidationError("Outgroup maps to more than one edge.")
352              selected_child = node
353      if selected_child is None:
354          raise ValidationError("Outgroup tips are not monophyletic on any tree edge.")
355  
356      endpoint_a = selected_child
357      endpoint_b = selected_child.parent
358      assert endpoint_b is not None
359  
360      # Build an undirected adjacency list before replacing the root orientation.
361      adjacency: dict[Node, list[tuple[Node, float | None]]] = {}
362      for node in tree.iter_preorder():
363          adjacency.setdefault(node, [])
364          for child in node.children:
365              adjacency[node].append((child, child.length))
366              adjacency.setdefault(child, []).append((node, child.length))
367  
368      edge_length = selected_child.length
369      half = None if edge_length is None else edge_length / 2.0
370  
371      # A degree-two root in a Newick representation is an artificial point on
372      # an unrooted edge. If rerooting elsewhere, suppress that point so it does
373      # not become a unary internal node in the newly oriented tree.
374      old_root = tree.root
375      if len(adjacency.get(old_root, [])) == 2:
376          (left_node, left_length), (right_node, right_length) = adjacency[old_root]
377          adjacency[left_node] = [item for item in adjacency[left_node] if item[0] is not old_root]
378          adjacency[right_node] = [item for item in adjacency[right_node] if item[0] is not old_root]
379          if left_length is None or right_length is None:
380              joined_length = None
381          else:
382              joined_length = left_length + right_length
383          adjacency[left_node].append((right_node, joined_length))
384          adjacency[right_node].append((left_node, joined_length))
385          del adjacency[old_root]
386  
387      new_root = Node()
388  
389      def orient(current: Node, previous: Node | None, incoming_length: float | None) -> Node:
390          clone = Node(name=current.name, length=incoming_length)
391          neighbours = [item for item in adjacency[current] if item[0] is not previous]
392          # Deterministic ordering based on the smallest descendant tip reachable
393          # through each neighbour in the undirected graph.
394          def side_key(item: tuple[Node, float | None]) -> str:
395              neighbour, _ = item
396              stack = [(neighbour, current)]
397              names: list[str] = []
398              while stack:
399                  node, parent = stack.pop()
400                  if node.is_tip and node.name is not None:
401                      names.append(node.name)
402                  for next_node, _length in adjacency[node]:
403                      if next_node is not parent:
404                          stack.append((next_node, node))
405              return min(names)
406  
407          for neighbour, length in sorted(neighbours, key=side_key):
408              child = orient(neighbour, current, length)
409              child.parent = clone
410              clone.children.append(child)
411          return clone
412  
413      left = orient(endpoint_a, endpoint_b, half)
414      right = orient(endpoint_b, endpoint_a, half)
415      left.parent = new_root
416      right.parent = new_root
417      new_root.children = [left, right]
418  
419      rooted = Tree(root=new_root)
420      _Parser._validate(rooted.root)
421      return rooted
```

### Preconditions and edge identification: lines 315–358

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 315–320 | Defines rerooting and documents branch-length treatment. | Analysis is topology-based; selected edge length is split only to preserve a sensible representation. |
| 322–323 | Requires a nonempty outgroup set. | Defensive for programmatic use. |
| 324–327 | Builds tip set and rejects absent outgroup names. | Does not silently prune or ignore tips. |
| 328–329 | Rejects an outgroup equal to all tips. | No ingroup side would remain. |
| 331–332 | Computes descendant sets and all tips under current root. | Needed to recognise either side of every unrooted edge. |
| 334–340 | If a degree-two root already splits exactly the requested outgroup as one root side, returns the original tree object unchanged. | Avoids treating the two child edges created by an artificial root point as duplicate representations of the same unrooted edge. |
| 342 | Initialises selected endpoint. | `None` means no matching edge yet. |
| 343–347 | Examines every non-root edge; a match occurs if child descendants or their complement equals the outgroup. | This tests monophyly on an unrooted edge, independent of the current root direction. |
| 348–351 | Rejects a second matching edge. | Protects against pathological degree-two representations or structural ambiguity. |
| 352 | Stores the child endpoint of the matching represented edge. | Even when the complement is the outgroup, this still identifies the correct undirected edge. |
| 353–354 | Rejects no edge match as non-monophyletic. | Outgroup tips must form one exact split. |
| 356–358 | Sets the two endpoints and asserts parent exists. | The selected node cannot be root. |

### Undirected graph and old-root suppression: lines 360–387

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 360–366 | Builds an undirected adjacency list, storing each child edge length in both directions. | Orientation must be discarded before a new root is imposed. |
| 368–369 | Reads selected edge length and halves it if present. | Each new root child receives half; `None` remains unknown. |
| 371–385 | If the old root has degree two, removes that artificial point and directly joins its neighbours; lengths are summed only when both are known. | Prevents the old root from becoming a unary internal node after rerooting elsewhere. The old root label is discarded. |
| 387 | Creates a blank new root. | Name and incoming length are `None`; it will receive two children. |

### Deterministic orientation and validation: lines 389–421

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 389 | Defines recursive orientation from an undirected endpoint away from the new root. | Returns cloned nodes; original tree is not reoriented in place. |
| 390 | Clones current node name and assigns supplied incoming length. | Child list starts empty and parent unset. |
| 391 | Excludes the neighbour from which traversal arrived. | Prevents walking back along the undirected edge. |
| 392–405 | Defines a sorting key: traverse the side reachable through each neighbour, collect tip names, return the minimum. | Disjoint sides and unique tip names give deterministic neighbour order independent of original sibling order. |
| 407 | Sorts neighbours by that key. | Ensures stable cloned child ordering. |
| 408–410 | Recursively orients each neighbour, sets its parent to clone, appends it. | Rebuilds a rooted parent/child structure. |
| 411 | Returns oriented clone. | Used recursively and for the two selected endpoints. |
| 413–414 | Orients both sides of selected edge, excluding the opposite endpoint; each receives half selected-edge length. | Inserts the root at the edge midpoint for representation. |
| 415–417 | Sets both parent pointers and installs two root children. | New root is degree two. |
| 419 | Wraps new root in `Tree`. | Creates independent rooted topology. |
| 420 | Reuses parser structural validation. | Confirms tip labels, no duplicates, and no unary internals after transformation. |
| 421 | Returns the new tree. | Caller records rooting metadata separately. |

## Rooting invariants

- No arbitrary Newick root is used unless explicitly accepted.
- Requested outgroup must be exactly one edge side.
- Every original tip appears exactly once after rerooting.
- A degree-two old Newick root is suppressed when rerooting elsewhere.
- Parent-to-child direction is then defined by the new orientation.

## Tests most relevant to this chapter

- branch IDs ignore sibling order;
- rerooting on an internal outgroup suppresses old root and retains all tips;
- an already matching root is returned unchanged;
- non-monophyletic outgroups are rejected;
- exact descendants, non-monophyly diagnosis, MRCA selection, and ID prefixes are tested.
