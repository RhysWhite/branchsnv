"""Core immutable and tree data structures used by BRANCHSNV."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass(eq=False)
class Node:
    """A rooted tree node.

    ``name`` stores a tip label or an optional internal-node label. Internal
    labels are not used to identify branches; branch identity is derived from
    exact descendant-tip membership.
    """

    name: str | None = None
    length: float | None = None
    children: list["Node"] = field(default_factory=list)
    parent: "Node | None" = field(default=None, repr=False)

    @property
    def is_tip(self) -> bool:
        return not self.children


@dataclass
class Tree:
    root: Node

    def iter_preorder(self) -> Iterator[Node]:
        stack = [self.root]
        while stack:
            node = stack.pop()
            yield node
            stack.extend(reversed(node.children))

    def iter_postorder(self) -> Iterator[Node]:
        stack: list[tuple[Node, bool]] = [(self.root, False)]
        while stack:
            node, visited = stack.pop()
            if visited:
                yield node
            else:
                stack.append((node, True))
                for child in reversed(node.children):
                    stack.append((child, False))

    def tips(self) -> list[Node]:
        return [node for node in self.iter_preorder() if node.is_tip]


@dataclass(frozen=True)
class Site:
    site_id: str
    states: str
    input_row: int


@dataclass(frozen=True)
class Alignment:
    path: Path
    taxa: tuple[str, ...]
    sites: tuple[Site, ...]
    ntax: int
    nchar: int
    gap: str
    missing: str
    symbols: str

    @property
    def taxon_index(self) -> dict[str, int]:
        return {name: index for index, name in enumerate(self.taxa)}


@dataclass(frozen=True)
class BranchRecord:
    branch_id: str
    short_id: str
    node: Node
    descendant_tips: tuple[str, ...]
    descendant_count: int
    parent_label: str
    child_label: str


@dataclass(frozen=True)
class ParsimonyResult:
    score: int
    status: str
    possible_pairs: tuple[tuple[str, str], ...]
    parent_states: tuple[str, ...]
    child_states: tuple[str, ...]


@dataclass(frozen=True)
class SiteResult:
    site_id: str
    reference: str
    position: int | None
    input_row: int
    parent_states: str
    child_states: str
    possible_pairs: str
    change: str
    parsimony_status: str
    fixed_within_clade: bool
    exclusive_to_clade: bool
    descendant_state: str
    descendant_total: int
    descendant_callable: int
    descendant_state_count: int
    outside_total: int
    outside_callable: int
    outside_same_state_count: int
    parsimony_score: int
    selection_reason: str
