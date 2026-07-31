"""Exact unordered-state Sankoff reconstruction for a selected rooted branch."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ValidationError
from .models import Node, ParsimonyResult, Tree

_STATES = ("A", "C", "G", "T")
_INF = 10**8
_IUPAC_MASKS = {
    "A": 0b0001,
    "C": 0b0010,
    "G": 0b0100,
    "T": 0b1000,
    "R": 0b0101,
    "Y": 0b1010,
    "S": 0b0110,
    "W": 0b1001,
    "K": 0b1100,
    "M": 0b0011,
    "B": 0b1110,
    "D": 0b1101,
    "H": 0b1011,
    "V": 0b0111,
    "N": 0b1111,
}
_LEAF_COSTS = {
    symbol: tuple(0 if mask & (1 << state) else _INF for state in range(4))
    for symbol, mask in _IUPAC_MASKS.items()
}


@dataclass(frozen=True)
class CompiledTree:
    nodes: tuple[Node, ...]
    root_index: int
    children: tuple[tuple[int, ...], ...]
    postorder: tuple[int, ...]
    tip_alignment_index: tuple[int, ...]
    focal_parent: int
    focal_child: int
    path_to_focal_parent: tuple[int, ...]


def compile_tree(
    tree: Tree,
    focal_node: Node,
    alignment_taxon_index: dict[str, int],
) -> CompiledTree:
    nodes = tuple(tree.iter_preorder())
    node_index = {node: index for index, node in enumerate(nodes)}
    if focal_node is tree.root or focal_node.parent is None:
        raise ValidationError("The selected branch must lead to a non-root node.")

    children: list[tuple[int, ...]] = []
    tip_alignment_index: list[int] = [-1] * len(nodes)
    for index, node in enumerate(nodes):
        children.append(tuple(node_index[child] for child in node.children))
        if node.is_tip:
            assert node.name is not None
            if node.name not in alignment_taxon_index:
                raise ValidationError(f"Tree tip {node.name!r} is absent from the alignment.")
            tip_alignment_index[index] = alignment_taxon_index[node.name]

    focal_parent = node_index[focal_node.parent]
    path_nodes: list[Node] = []
    cursor: Node | None = focal_node.parent
    while cursor is not None:
        path_nodes.append(cursor)
        cursor = cursor.parent
    path_nodes.reverse()

    return CompiledTree(
        nodes=nodes,
        root_index=node_index[tree.root],
        children=tuple(children),
        postorder=tuple(node_index[node] for node in tree.iter_postorder()),
        tip_alignment_index=tuple(tip_alignment_index),
        focal_parent=focal_parent,
        focal_child=node_index[focal_node],
        path_to_focal_parent=tuple(node_index[node] for node in path_nodes),
    )



def reconstruct_site(
    compiled: CompiledTree,
    states: str,
    gap: str,
    missing: str,
) -> ParsimonyResult:
    """Return every globally optimal state pair across the selected edge.

    The down-pass is performed for the whole tree. The outside-cost pass is
    restricted to the single root-to-focal-parent path, avoiding unnecessary
    work on branches that cannot affect the selected edge.
    """

    node_count = len(compiled.nodes)
    down: list[list[int]] = [[0, 0, 0, 0] for _ in range(node_count)]
    gap_upper = gap.upper()
    missing_upper = missing.upper()

    for node_index in compiled.postorder:
        child_indices = compiled.children[node_index]
        if not child_indices:
            symbol = states[compiled.tip_alignment_index[node_index]].upper()
            if symbol == gap_upper or symbol == missing_upper:
                down[node_index] = [0, 0, 0, 0]
            else:
                try:
                    down[node_index] = list(_LEAF_COSTS[symbol])
                except KeyError as exc:
                    raise ValidationError(f"Unsupported nucleotide state symbol {symbol!r}.") from exc
            continue

        total0 = total1 = total2 = total3 = 0
        for child_index in child_indices:
            child = down[child_index]
            child_min = min(child)
            alt = child_min + 1
            value = child[0]
            total0 += value if value <= alt else alt
            value = child[1]
            total1 += value if value <= alt else alt
            value = child[2]
            total2 += value if value <= alt else alt
            value = child[3]
            total3 += value if value <= alt else alt
        down[node_index] = [total0, total1, total2, total3]

    optimal_score = min(down[compiled.root_index])

    # up_cost is conditioned on the current path node state and contains only
    # information outside that node's subtree.
    up_cost = [0, 0, 0, 0]
    path = compiled.path_to_focal_parent
    for path_position in range(len(path) - 1):
        parent_index = path[path_position]
        child_on_path = path[path_position + 1]
        sibling0 = sibling1 = sibling2 = sibling3 = 0
        for sibling_index in compiled.children[parent_index]:
            if sibling_index == child_on_path:
                continue
            sibling = down[sibling_index]
            sibling_min = min(sibling)
            alt = sibling_min + 1
            value = sibling[0]
            sibling0 += value if value <= alt else alt
            value = sibling[1]
            sibling1 += value if value <= alt else alt
            value = sibling[2]
            sibling2 += value if value <= alt else alt
            value = sibling[3]
            sibling3 += value if value <= alt else alt

        base = [
            up_cost[0] + sibling0,
            up_cost[1] + sibling1,
            up_cost[2] + sibling2,
            up_cost[3] + sibling3,
        ]
        base_min = min(base)
        alternative = base_min + 1
        up_cost = [
            base[0] if base[0] <= alternative else alternative,
            base[1] if base[1] <= alternative else alternative,
            base[2] if base[2] <= alternative else alternative,
            base[3] if base[3] <= alternative else alternative,
        ]

    parent_index = compiled.focal_parent
    child_index = compiled.focal_child
    sibling_costs = [0, 0, 0, 0]
    for sibling_index in compiled.children[parent_index]:
        if sibling_index == child_index:
            continue
        sibling = down[sibling_index]
        sibling_min = min(sibling)
        alt = sibling_min + 1
        for state in range(4):
            value = sibling[state]
            sibling_costs[state] += value if value <= alt else alt

    possible_pairs: list[tuple[str, str]] = []
    child_down = down[child_index]
    for parent_state in range(4):
        outside = up_cost[parent_state] + sibling_costs[parent_state]
        for child_state in range(4):
            pair_cost = outside + (parent_state != child_state) + child_down[child_state]
            if pair_cost == optimal_score:
                possible_pairs.append((_STATES[parent_state], _STATES[child_state]))

    if not possible_pairs:
        raise ValidationError("Internal error: no optimal reconstruction for the selected edge.")

    unique_pairs = tuple(sorted(set(possible_pairs)))
    changes = [parent != child for parent, child in unique_pairs]
    if all(changes):
        status = "unambiguous_change" if len(unique_pairs) == 1 else "change_state_ambiguous"
    elif any(changes):
        status = "placement_ambiguous"
    else:
        status = "no_change"

    return ParsimonyResult(
        score=optimal_score,
        status=status,
        possible_pairs=unique_pairs,
        parent_states=tuple(sorted({pair[0] for pair in unique_pairs})),
        child_states=tuple(sorted({pair[1] for pair in unique_pairs})),
    )
