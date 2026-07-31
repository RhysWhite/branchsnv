"""Deterministic provenance report construction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import __version__
from .analysis import AnalysisSummary
from .models import Alignment, BranchRecord, Tree
from .util import sha256_file, sha256_lines


def build_report(
    *,
    alignment: Alignment,
    alignment_path: Path,
    tree: Tree,
    tree_path: Path,
    branch: BranchRecord,
    rooting: dict[str, Any],
    selector: dict[str, Any],
    mode: str,
    include_ambiguous: bool,
    summary: AnalysisSummary,
    results_path: Path,
    members_path: Path,
    results_hash_path: Path | None = None,
    members_hash_path: Path | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "tool": {"name": "BRANCHSNV", "version": __version__},
        "inputs": {
            "alignment": {
                "name": alignment_path.name,
                "sha256": sha256_file(alignment_path),
                "ntax": alignment.ntax,
                "nchar": alignment.nchar,
                "format": "transposed_nexus",
                "gap_symbol": alignment.gap,
                "missing_symbol": alignment.missing,
            },
            "tree": {
                "name": tree_path.name,
                "sha256": sha256_file(tree_path),
                "tips": len(tree.tips()),
                "format": "newick",
            },
        },
        "rooting": rooting,
        "branch": {
            "branch_id": branch.branch_id,
            "short_id": branch.short_id,
            "descendant_count": branch.descendant_count,
            "descendant_taxa_sha256": sha256_lines(branch.descendant_tips),
            "selection": selector,
        },
        "parameters": {
            "mode": mode,
            "include_ambiguous_parsimony_sites": include_ambiguous,
            "state_cost_model": "unordered_equal_cost",
            "gap_treatment": "unknown_state",
            "missing_treatment": "unknown_state",
            "fixed_exclusive_descendant_call_rate": 1.0,
            "fixed_exclusive_outside_call_rate": 1.0,
        },
        "results": {
            "sites_examined": summary.sites_examined,
            "reported_sites": summary.reported_sites,
            "fixed_exclusive_sites": summary.fixed_exclusive_sites,
            "parsimony": {
                "unambiguous_change": summary.unambiguous_change_sites,
                "change_state_ambiguous": summary.change_state_ambiguous_sites,
                "placement_ambiguous": summary.placement_ambiguous_sites,
                "no_change": summary.no_change_sites,
            },
        },
        "outputs": {
            "results_tsv": {
                "name": results_path.name,
                "sha256": sha256_file(results_hash_path or results_path),
            },
            "branch_members": {
                "name": members_path.name,
                "sha256": sha256_file(members_hash_path or members_path),
            },
        },
        "warnings": [],
    }
