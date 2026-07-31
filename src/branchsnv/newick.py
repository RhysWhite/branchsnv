"""Dependency-free Newick parsing and deterministic rooted-tree operations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from .errors import NewickFormatError, SelectionError, ValidationError
from .models import BranchRecord, Node, Tree
from .util import sha256_lines


@dataclass
class _Parser:
    text: str
    index: int = 0

    def parse(self) -> Tree:
        self._skip_space_and_comments()
        root = self._parse_subtree()
        self._skip_space_and_comments()
        if self._peek() != ";":
            raise self._error("Expected ';' at the end of the Newick tree")
        self.index += 1
        self._skip_space_and_comments()
        if self.index != len(self.text):
            raise self._error("Unexpected content after the terminating ';'")
        root.parent = None
        self._validate(root)
        return Tree(root=root)

    def _parse_subtree(self) -> Node:
        self._skip_space_and_comments()
        if self._peek() == "(":
            self.index += 1
            children = [self._parse_subtree()]
            self._skip_space_and_comments()
            while self._peek() == ",":
                self.index += 1
                children.append(self._parse_subtree())
                self._skip_space_and_comments()
            if self._peek() != ")":
                raise self._error("Expected ')' to close an internal node")
            self.index += 1
            name = self._parse_optional_label()
            length = self._parse_optional_length()
            node = Node(name=name, length=length, children=children)
            for child in children:
                child.parent = node
            return node

        name = self._parse_required_label()
        length = self._parse_optional_length()
        return Node(name=name, length=length)

    def _parse_required_label(self) -> str:
        label = self._parse_optional_label()
        if label is None or label == "":
            raise self._error("Tip labels must not be empty")
        return label

    def _parse_optional_label(self) -> str | None:
        self._skip_space_and_comments()
        char = self._peek()
        if char in {None, ":", ",", ")", ";"}:
            return None
        if char == "'":
            self.index += 1
            chars: list[str] = []
            while self.index < len(self.text):
                current = self.text[self.index]
                if current == "'":
                    if self.index + 1 < len(self.text) and self.text[self.index + 1] == "'":
                        chars.append("'")
                        self.index += 2
                        continue
                    self.index += 1
                    return "".join(chars)
                chars.append(current)
                self.index += 1
            raise self._error("Unterminated quoted Newick label")

        start = self.index
        while self.index < len(self.text):
            current = self.text[self.index]
            if current.isspace() or current in {":", ",", "(", ")", ";", "["}:
                break
            self.index += 1
        if self.index == start:
            return None
        return self.text[start:self.index]

    def _parse_optional_length(self) -> float | None:
        self._skip_space_and_comments()
        if self._peek() != ":":
            return None
        self.index += 1
        self._skip_space_and_comments()
        start = self.index
        while self.index < len(self.text):
            char = self.text[self.index]
            if char.isspace() or char in {",", ")", ";", "["}:
                break
            self.index += 1
        token = self.text[start:self.index]
        if not token:
            raise self._error("Branch length is missing after ':'")
        try:
            value = float(token)
        except ValueError as exc:
            raise self._error(f"Invalid branch length: {token!r}") from exc
        if not math.isfinite(value):
            raise self._error("Branch lengths must be finite")
        return value

    def _skip_space_and_comments(self) -> None:
        while self.index < len(self.text):
            if self.text[self.index].isspace():
                self.index += 1
                continue
            if self.text[self.index] == "[":
                depth = 1
                self.index += 1
                while self.index < len(self.text) and depth:
                    if self.text[self.index] == "[":
                        depth += 1
                    elif self.text[self.index] == "]":
                        depth -= 1
                    self.index += 1
                if depth:
                    raise self._error("Unterminated Newick comment")
                continue
            break

    def _peek(self) -> str | None:
        if self.index >= len(self.text):
            return None
        return self.text[self.index]

    def _error(self, message: str) -> NewickFormatError:
        line = self.text.count("\n", 0, self.index) + 1
        column = self.index - self.text.rfind("\n", 0, self.index)
        return NewickFormatError(f"{message} at line {line}, column {column}.")

    @staticmethod
    def _validate(root: Node) -> None:
        stack = [root]
        tip_names: list[str] = []
        while stack:
            node = stack.pop()
            if node.is_tip:
                if node.name is None:
                    raise NewickFormatError("Every tip must have a label.")
                tip_names.append(node.name)
            elif len(node.children) < 2:
                raise NewickFormatError("Internal Newick nodes must have at least two children.")
            stack.extend(node.children)
        seen: set[str] = set()
        duplicates: set[str] = set()
        for name in tip_names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)
        if duplicates:
            preview = ", ".join(sorted(duplicates)[:5])
            raise NewickFormatError(f"Duplicate tree tip label(s): {preview}.")



def parse_newick(text: str) -> Tree:
    """Parse one Newick tree from text."""

    if not text.strip():
        raise NewickFormatError("Newick text is empty.")
    return _Parser(text).parse()

def read_newick(path: str | Path) -> Tree:
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise NewickFormatError(f"Could not read Newick file {source}: {exc}") from exc
    if not text.strip():
        raise NewickFormatError("Newick file is empty.")
    return parse_newick(text)


def descendant_tip_map(tree: Tree) -> dict[Node, tuple[str, ...]]:
    result: dict[Node, tuple[str, ...]] = {}
    for node in tree.iter_postorder():
        if node.is_tip:
            assert node.name is not None
            result[node] = (node.name,)
        else:
            names: list[str] = []
            for child in node.children:
                names.extend(result[child])
            result[node] = tuple(sorted(names))
    return result


def _display_label(node: Node, descendants: tuple[str, ...]) -> str:
    if node.is_tip:
        assert node.name is not None
        return node.name
    if node.name:
        return node.name
    return f"internal[{len(descendants)} tips]"


def branch_records(tree: Tree) -> list[BranchRecord]:
    descendants = descendant_tip_map(tree)
    records: list[BranchRecord] = []
    full_ids: set[str] = set()
    for node in tree.iter_preorder():
        if node is tree.root:
            continue
        tips = descendants[node]
        digest = sha256_lines(tips)
        branch_id = f"b_{digest}"
        if branch_id in full_ids:
            raise ValidationError("Two branches unexpectedly produced the same descendant-set hash.")
        full_ids.add(branch_id)
        parent = node.parent
        assert parent is not None
        records.append(
            BranchRecord(
                branch_id=branch_id,
                short_id=branch_id[:18],
                node=node,
                descendant_tips=tips,
                descendant_count=len(tips),
                parent_label=_display_label(parent, descendants[parent]),
                child_label=_display_label(node, tips),
            )
        )
    return records


def resolve_branch_id(records: list[BranchRecord], identifier: str) -> BranchRecord:
    matches = [record for record in records if record.branch_id == identifier]
    if not matches:
        matches = [record for record in records if record.branch_id.startswith(identifier)]
    if not matches:
        raise SelectionError(f"No branch matches identifier {identifier!r}.")
    if len(matches) > 1:
        raise SelectionError(
            f"Branch identifier prefix {identifier!r} is ambiguous; provide more characters."
        )
    return matches[0]


def select_exact_descendants(tree: Tree, requested: set[str]) -> BranchRecord:
    if not requested:
        raise SelectionError("The descendant-tip list is empty.")
    all_tips = {tip.name for tip in tree.tips()}
    missing = sorted(requested - all_tips)
    if missing:
        raise SelectionError(
            "Requested descendant tip(s) are absent from the tree: " + ", ".join(missing[:10])
        )
    records = branch_records(tree)
    exact = [record for record in records if set(record.descendant_tips) == requested]
    if exact:
        return exact[0]
    mrca = find_mrca(tree, requested)
    descendants = descendant_tip_map(tree)[mrca]
    extras = sorted(set(descendants) - requested)
    message = "Requested tips do not form exactly one rooted clade."
    if extras:
        message += " Their MRCA also contains: " + ", ".join(extras[:10])
        if len(extras) > 10:
            message += f" (and {len(extras) - 10} more)"
        message += "."
    raise SelectionError(message)


def find_mrca(tree: Tree, requested: set[str]) -> Node:
    if not requested:
        raise SelectionError("At least one tip is required to identify an MRCA.")
    tip_nodes = {tip.name: tip for tip in tree.tips()}
    missing = sorted(requested - tip_nodes.keys())
    if missing:
        raise SelectionError("MRCA tip(s) absent from tree: " + ", ".join(missing[:10]))

    ancestor_paths: list[list[Node]] = []
    for name in sorted(requested):
        node = tip_nodes[name]
        path: list[Node] = []
        while node is not None:
            path.append(node)
            node = node.parent  # type: ignore[assignment]
        ancestor_paths.append(path)

    common = set(ancestor_paths[0])
    for path in ancestor_paths[1:]:
        common.intersection_update(path)
    for node in ancestor_paths[0]:
        if node in common:
            return node
    raise SelectionError("Could not determine an MRCA.")


def select_mrca_branch(tree: Tree, requested: set[str]) -> BranchRecord:
    node = find_mrca(tree, requested)
    if node is tree.root:
        raise SelectionError("The requested MRCA is the root and has no incoming branch.")
    for record in branch_records(tree):
        if record.node is node:
            return record
    raise SelectionError("Could not resolve the branch leading to the requested MRCA.")


def reroot_on_outgroup(tree: Tree, outgroup: set[str]) -> Tree:
    """Root on the unique edge separating exactly the requested outgroup tips.

    Branch lengths are irrelevant to BRANCHSNV's topology-based analysis. When a
    new root is inserted, the selected edge length is split evenly if present.
    """

    if not outgroup:
        raise ValidationError("At least one outgroup tip is required.")
    tip_names = {tip.name for tip in tree.tips()}
    missing = sorted(outgroup - tip_names)
    if missing:
        raise ValidationError("Outgroup tip(s) absent from tree: " + ", ".join(missing[:10]))
    if outgroup == tip_names:
        raise ValidationError("The outgroup cannot contain every tree tip.")

    descendants = descendant_tip_map(tree)
    all_tips = set(descendants[tree.root])

    # If the existing root already lies on the requested outgroup edge, retain
    # it exactly. A degree-two root splits one unrooted edge into two rooted
    # edges, which would otherwise appear as two equivalent matches.
    if len(tree.root.children) == 2:
        root_sides = [set(descendants[child]) for child in tree.root.children]
        if outgroup in root_sides:
            return tree

    selected_child: Node | None = None
    for node, tips_tuple in descendants.items():
        if node is tree.root:
            continue
        side = set(tips_tuple)
        if side == outgroup or all_tips - side == outgroup:
            if selected_child is not None:
                # A singleton tip can match only one biological edge; duplicate
                # matches would indicate a pathological degree-two representation.
                raise ValidationError("Outgroup maps to more than one edge.")
            selected_child = node
    if selected_child is None:
        raise ValidationError("Outgroup tips are not monophyletic on any tree edge.")

    endpoint_a = selected_child
    endpoint_b = selected_child.parent
    assert endpoint_b is not None

    # Build an undirected adjacency list before replacing the root orientation.
    adjacency: dict[Node, list[tuple[Node, float | None]]] = {}
    for node in tree.iter_preorder():
        adjacency.setdefault(node, [])
        for child in node.children:
            adjacency[node].append((child, child.length))
            adjacency.setdefault(child, []).append((node, child.length))

    edge_length = selected_child.length
    half = None if edge_length is None else edge_length / 2.0

    # A degree-two root in a Newick representation is an artificial point on
    # an unrooted edge. If rerooting elsewhere, suppress that point so it does
    # not become a unary internal node in the newly oriented tree.
    old_root = tree.root
    if len(adjacency.get(old_root, [])) == 2:
        (left_node, left_length), (right_node, right_length) = adjacency[old_root]
        adjacency[left_node] = [item for item in adjacency[left_node] if item[0] is not old_root]
        adjacency[right_node] = [item for item in adjacency[right_node] if item[0] is not old_root]
        if left_length is None or right_length is None:
            joined_length = None
        else:
            joined_length = left_length + right_length
        adjacency[left_node].append((right_node, joined_length))
        adjacency[right_node].append((left_node, joined_length))
        del adjacency[old_root]

    new_root = Node()

    def orient(current: Node, previous: Node | None, incoming_length: float | None) -> Node:
        clone = Node(name=current.name, length=incoming_length)
        neighbours = [item for item in adjacency[current] if item[0] is not previous]
        # Deterministic ordering based on the smallest descendant tip reachable
        # through each neighbour in the undirected graph.
        def side_key(item: tuple[Node, float | None]) -> str:
            neighbour, _ = item
            stack = [(neighbour, current)]
            names: list[str] = []
            while stack:
                node, parent = stack.pop()
                if node.is_tip and node.name is not None:
                    names.append(node.name)
                for next_node, _length in adjacency[node]:
                    if next_node is not parent:
                        stack.append((next_node, node))
            return min(names)

        for neighbour, length in sorted(neighbours, key=side_key):
            child = orient(neighbour, current, length)
            child.parent = clone
            clone.children.append(child)
        return clone

    left = orient(endpoint_a, endpoint_b, half)
    right = orient(endpoint_b, endpoint_a, half)
    left.parent = new_root
    right.parent = new_root
    new_root.children = [left, right]

    rooted = Tree(root=new_root)
    _Parser._validate(rooted.root)
    return rooted
