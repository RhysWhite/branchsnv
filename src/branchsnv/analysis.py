"""Branch-associated SNV analysis."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .models import Alignment, BranchRecord, SiteResult, Tree
from .parsimony import compile_tree, reconstruct_site
from .util import parse_coordinate


@dataclass(frozen=True)
class AnalysisSummary:
    results: tuple[SiteResult, ...]
    sites_examined: int
    fixed_exclusive_sites: int
    unambiguous_change_sites: int
    change_state_ambiguous_sites: int
    placement_ambiguous_sites: int
    no_change_sites: int
    reported_sites: int


def _is_unambiguous_base(symbol: str) -> bool:
    return symbol.upper() in {"A", "C", "G", "T"}


def analyse_branch(
    alignment: Alignment,
    tree: Tree,
    branch: BranchRecord,
    mode: str,
    include_ambiguous: bool = False,
) -> AnalysisSummary:
    if mode not in {"fixed-exclusive", "parsimony", "both"}:
        raise ValueError(f"Unknown analysis mode: {mode}")

    taxon_index = alignment.taxon_index
    descendant_indices = tuple(taxon_index[name] for name in branch.descendant_tips)
    descendant_set = set(descendant_indices)
    outside_indices = tuple(index for index in range(alignment.ntax) if index not in descendant_set)
    compiled = compile_tree(tree, branch.node, taxon_index)

    results: list[SiteResult] = []
    fixed_exclusive_count = 0
    status_counts = Counter()

    for site in alignment.sites:
        descendant_symbols = [site.states[index].upper() for index in descendant_indices]
        outside_symbols = [site.states[index].upper() for index in outside_indices]

        descendant_callable = sum(_is_unambiguous_base(symbol) for symbol in descendant_symbols)
        outside_callable = sum(_is_unambiguous_base(symbol) for symbol in outside_symbols)
        callable_descendant_states = [
            symbol for symbol in descendant_symbols if _is_unambiguous_base(symbol)
        ]
        descendant_state = ""
        fixed_within = False
        descendant_state_count = 0
        if descendant_callable == len(descendant_indices) and callable_descendant_states:
            unique = set(callable_descendant_states)
            if len(unique) == 1:
                descendant_state = callable_descendant_states[0]
                fixed_within = True
                descendant_state_count = descendant_callable

        outside_same_count = (
            sum(symbol == descendant_state for symbol in outside_symbols)
            if descendant_state
            else 0
        )
        exclusive = (
            fixed_within
            and outside_callable == len(outside_indices)
            and outside_same_count == 0
        )
        fixed_exclusive = fixed_within and exclusive
        if fixed_exclusive:
            fixed_exclusive_count += 1

        parsimony = reconstruct_site(
            compiled=compiled,
            states=site.states,
            gap=alignment.gap,
            missing=alignment.missing,
        )
        status_counts[parsimony.status] += 1

        selected_fixed = mode in {"fixed-exclusive", "both"} and fixed_exclusive
        selected_parsimony = mode in {"parsimony", "both"} and (
            parsimony.status == "unambiguous_change"
            or (include_ambiguous and parsimony.status in {"change_state_ambiguous", "placement_ambiguous"})
        )
        if not (selected_fixed or selected_parsimony):
            continue

        if selected_fixed and selected_parsimony:
            reason = "both"
        elif selected_fixed:
            reason = "fixed-exclusive"
        else:
            reason = "parsimony"

        if len(parsimony.possible_pairs) == 1:
            parent_state, child_state = parsimony.possible_pairs[0]
            change = f"{parent_state}>{child_state}" if parent_state != child_state else ""
        else:
            change = "|".join(
                f"{parent}>{child}" for parent, child in parsimony.possible_pairs if parent != child
            )

        reference, position = parse_coordinate(site.site_id)
        results.append(
            SiteResult(
                site_id=site.site_id,
                reference=reference,
                position=position,
                input_row=site.input_row,
                parent_states="|".join(parsimony.parent_states),
                child_states="|".join(parsimony.child_states),
                possible_pairs="|".join(
                    f"{parent}>{child}" for parent, child in parsimony.possible_pairs
                ),
                change=change,
                parsimony_status=parsimony.status,
                fixed_within_clade=fixed_within,
                exclusive_to_clade=exclusive,
                descendant_state=descendant_state,
                descendant_total=len(descendant_indices),
                descendant_callable=descendant_callable,
                descendant_state_count=descendant_state_count,
                outside_total=len(outside_indices),
                outside_callable=outside_callable,
                outside_same_state_count=outside_same_count,
                parsimony_score=parsimony.score,
                selection_reason=reason,
            )
        )

    results.sort(key=lambda item: item.input_row)
    return AnalysisSummary(
        results=tuple(results),
        sites_examined=alignment.nchar,
        fixed_exclusive_sites=fixed_exclusive_count,
        unambiguous_change_sites=status_counts["unambiguous_change"],
        change_state_ambiguous_sites=status_counts["change_state_ambiguous"],
        placement_ambiguous_sites=status_counts["placement_ambiguous"],
        no_change_sites=status_counts["no_change"],
        reported_sites=len(results),
    )
