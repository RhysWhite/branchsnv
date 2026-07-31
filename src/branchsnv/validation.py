"""Cross-input validation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ValidationError
from .models import Alignment, Tree


@dataclass(frozen=True)
class Compatibility:
    alignment_taxa: int
    tree_tips: int
    matched_taxa: int
    alignment_only: tuple[str, ...]
    tree_only: tuple[str, ...]


def validate_compatibility(alignment: Alignment, tree: Tree) -> Compatibility:
    alignment_names = set(alignment.taxa)
    tree_names = {tip.name for tip in tree.tips()}
    alignment_only = tuple(sorted(alignment_names - tree_names))
    tree_only = tuple(sorted(tree_names - alignment_names))
    if alignment_only or tree_only:
        parts: list[str] = []
        if alignment_only:
            parts.append(
                "alignment-only: " + ", ".join(alignment_only[:10])
                + (f" (and {len(alignment_only) - 10} more)" if len(alignment_only) > 10 else "")
            )
        if tree_only:
            parts.append(
                "tree-only: " + ", ".join(tree_only[:10])
                + (f" (and {len(tree_only) - 10} more)" if len(tree_only) > 10 else "")
            )
        raise ValidationError("Tree and alignment taxon sets differ (" + "; ".join(parts) + ").")
    return Compatibility(
        alignment_taxa=alignment.ntax,
        tree_tips=len(tree_names),
        matched_taxa=len(tree_names),
        alignment_only=alignment_only,
        tree_only=tree_only,
    )
