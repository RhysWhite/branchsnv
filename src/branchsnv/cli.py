"""Command-line interface for BRANCHSNV."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from . import __version__
from .analysis import analyse_branch
from .errors import BranchSNVError, SelectionError, ValidationError
from .models import BranchRecord, Tree
from .newick import (
    branch_records,
    read_newick,
    reroot_on_outgroup,
    resolve_branch_id,
    select_exact_descendants,
    select_mrca_branch,
)
from .nexus import read_transposed_nexus
from .provenance import build_report
from .validation import validate_compatibility
from .util import sha256_file
from .writing import (
    AtomicOutputSet,
    write_branches,
    write_members,
    write_report,
    write_results,
)


def _read_name_file(path: Path) -> set[str]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except UnicodeError as exc:
        raise SelectionError(f"Could not decode taxon list {path} as UTF-8: {exc}") from exc
    except OSError as exc:
        raise SelectionError(f"Could not read taxon list {path}: {exc}") from exc
    names: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        names.append(value)
    if not names:
        raise SelectionError(f"Taxon list {path} contains no names.")
    duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
    if duplicates:
        raise SelectionError(f"Taxon list contains duplicate name(s): {', '.join(duplicates[:10])}.")
    return set(names)


def _add_rooting_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--outgroup",
        nargs="+",
        metavar="TIP",
        help="Root on the edge separating these monophyletic outgroup tips.",
    )
    group.add_argument(
        "--outgroup-file",
        type=Path,
        help="File containing one outgroup tip name per line.",
    )
    group.add_argument(
        "--accept-existing-root",
        action="store_true",
        help="Use the root encoded by the Newick topology without rerooting.",
    )


def _root_tree(tree: Tree, args: argparse.Namespace) -> tuple[Tree, dict[str, object]]:
    if args.accept_existing_root:
        if len(tree.root.children) < 2:
            raise ValidationError("The existing root must have at least two children.")
        return tree, {"method": "existing_newick_root", "outgroup": []}
    if args.outgroup_file:
        names = _read_name_file(args.outgroup_file)
        method = "outgroup_file"
        source = args.outgroup_file.name
    else:
        inline_names = args.outgroup or []
        if len(set(inline_names)) != len(inline_names):
            raise ValidationError("--outgroup contains duplicate tip names.")
        names = set(inline_names)
        method = "outgroup"
        source = None
    rooted = reroot_on_outgroup(tree, names)
    report: dict[str, object] = {"method": method, "outgroup": sorted(names)}
    if source:
        report["source"] = source
        report["source_sha256"] = sha256_file(args.outgroup_file)
    return rooted, report


def _select_branch(tree: Tree, args: argparse.Namespace) -> tuple[BranchRecord, dict[str, object]]:
    if args.clade_tips:
        requested = _read_name_file(args.clade_tips)
        branch = select_exact_descendants(tree, requested)
        return branch, {
            "method": "exact_descendant_file",
            "source": args.clade_tips.name,
            "sha256": sha256_file(args.clade_tips),
        }
    if args.mrca:
        requested = set(args.mrca)
        if len(requested) != len(args.mrca):
            raise SelectionError("--mrca contains duplicate tip names.")
        branch = select_mrca_branch(tree, requested)
        return branch, {"method": "mrca", "tips": sorted(requested)}
    if args.branch_id:
        branch = resolve_branch_id(branch_records(tree), args.branch_id)
        return branch, {"method": "branch_id", "requested": args.branch_id}
    raise SelectionError("No branch-selection method was supplied.")



def _reject_output_input_collisions(
    outputs: list[Path], inputs: list[Path | None]
) -> None:
    input_map = {path.resolve(): path for path in inputs if path is not None}
    for output in outputs:
        resolved = output.resolve()
        if resolved in input_map:
            raise ValidationError(
                f"Output path {output} resolves to input path {input_map[resolved]}."
            )

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="branchsnv",
        description=(
            "Identify fixed clade-associated nucleotide states and parsimoniously "
            "reconstructed substitutions on a selected phylogenetic branch."
        ),
    )
    parser.add_argument("--version", action="version", version=f"BRANCHSNV {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate", help="Validate a transposed NEXUS alignment and rooted Newick tree."
    )
    validate_parser.add_argument("--alignment", required=True, type=Path)
    validate_parser.add_argument("--tree", required=True, type=Path)
    _add_rooting_arguments(validate_parser)

    inspect_parser = subparsers.add_parser(
        "inspect", help="List every non-root branch and its deterministic identifier."
    )
    inspect_parser.add_argument("--tree", required=True, type=Path)
    inspect_parser.add_argument("--output", required=True, type=Path)
    inspect_parser.add_argument("--force", action="store_true")
    _add_rooting_arguments(inspect_parser)

    find_parser = subparsers.add_parser(
        "find", help="Identify SNVs associated with one selected branch."
    )
    find_parser.add_argument("--alignment", required=True, type=Path)
    find_parser.add_argument("--tree", required=True, type=Path)
    _add_rooting_arguments(find_parser)
    selection = find_parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--clade-tips",
        type=Path,
        help="File containing the exact descendants of the selected branch.",
    )
    selection.add_argument(
        "--mrca",
        nargs="+",
        metavar="TIP",
        help="Select the branch leading to the MRCA of these tips.",
    )
    selection.add_argument(
        "--branch-id",
        help="Full deterministic branch identifier or an unambiguous prefix from inspect.",
    )
    find_parser.add_argument(
        "--mode",
        choices=("fixed-exclusive", "parsimony", "both"),
        default="both",
    )
    find_parser.add_argument(
        "--include-ambiguous",
        action="store_true",
        help="Also report parsimony sites with ambiguous change state or placement.",
    )
    find_parser.add_argument("--output", required=True, type=Path, help="Results TSV.")
    find_parser.add_argument(
        "--members-output", required=True, type=Path, help="Sorted descendant-tip list."
    )
    find_parser.add_argument("--report", required=True, type=Path, help="Provenance JSON.")
    find_parser.add_argument("--force", action="store_true")
    return parser


def _run_validate(args: argparse.Namespace) -> int:
    alignment = read_transposed_nexus(args.alignment)
    tree, rooting = _root_tree(read_newick(args.tree), args)
    compatibility = validate_compatibility(alignment, tree)
    print(
        f"VALID: {compatibility.matched_taxa} taxa, {alignment.nchar} sites; "
        f"rooting={rooting['method']}."
    )
    return 0


def _run_inspect(args: argparse.Namespace) -> int:
    _reject_output_input_collisions(
        [args.output], [args.tree, args.outgroup_file]
    )
    tree, _rooting = _root_tree(read_newick(args.tree), args)
    records = branch_records(tree)
    with AtomicOutputSet([args.output], force=args.force) as transaction:
        write_branches(transaction.staged_path(args.output), records)
        transaction.commit()
    print(f"Wrote {len(records)} branches to {args.output}.")
    return 0


def _run_find(args: argparse.Namespace) -> int:
    _reject_output_input_collisions(
        [args.output, args.members_output, args.report],
        [args.alignment, args.tree, args.clade_tips, args.outgroup_file],
    )
    alignment = read_transposed_nexus(args.alignment)
    tree, rooting = _root_tree(read_newick(args.tree), args)
    validate_compatibility(alignment, tree)
    branch, selector = _select_branch(tree, args)
    summary = analyse_branch(
        alignment=alignment,
        tree=tree,
        branch=branch,
        mode=args.mode,
        include_ambiguous=args.include_ambiguous,
    )

    targets = [args.output, args.members_output, args.report]
    with AtomicOutputSet(targets, force=args.force) as transaction:
        staged_results = transaction.staged_path(args.output)
        staged_members = transaction.staged_path(args.members_output)
        staged_report = transaction.staged_path(args.report)
        write_results(staged_results, summary.results)
        write_members(staged_members, branch)
        report = build_report(
            alignment=alignment,
            alignment_path=args.alignment,
            tree=tree,
            tree_path=args.tree,
            branch=branch,
            rooting=rooting,
            selector=selector,
            mode=args.mode,
            include_ambiguous=args.include_ambiguous,
            summary=summary,
            results_path=args.output,
            members_path=args.members_output,
            results_hash_path=staged_results,
            members_hash_path=staged_members,
        )
        write_report(staged_report, report)
        transaction.commit()

    print(
        f"Selected {branch.short_id} ({branch.descendant_count} descendants); "
        f"reported {summary.reported_sites} of {summary.sites_examined} sites."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return _run_validate(args)
        if args.command == "inspect":
            return _run_inspect(args)
        if args.command == "find":
            return _run_find(args)
        parser.error("Unknown command.")
    except BranchSNVError as exc:
        print(f"BRANCHSNV error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"BRANCHSNV I/O error: {exc}", file=sys.stderr)
        return 2
    return 1
