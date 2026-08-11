"""Deterministic, atomic output writing."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .models import BranchRecord, SiteResult
from .util import bool_text

_TSV_FIELDS = (
    "site_id",
    "reference",
    "position",
    "input_row",
    "parent_states",
    "child_states",
    "possible_pairs",
    "change",
    "parsimony_status",
    "fixed_within_clade",
    "exclusive_to_clade",
    "descendant_state",
    "descendant_total",
    "descendant_callable",
    "descendant_state_count",
    "outside_total",
    "outside_callable",
    "outside_same_state_count",
    "parsimony_score",
    "selection_reason",
)

_BRANCH_FIELDS = (
    "branch_id",
    "short_id",
    "descendant_count",
    "parent_label",
    "child_label",
    "first_descendant",
    "last_descendant",
)


class AtomicOutputSet:
    """Stage several files and replace all targets only after every write succeeds."""

    def __init__(self, targets: list[Path], force: bool = False):
        self.targets = targets
        self.force = force
        self.temporary: dict[Path, Path] = {}

    def __enter__(self) -> "AtomicOutputSet":
        canonical = [path.resolve() for path in self.targets]
        duplicates = [path for path in canonical if canonical.count(path) > 1]
        if duplicates:
            raise ValidationError(f"Output paths must be distinct: {duplicates[0]}.")
        for target in self.targets:
            if target.exists() and not self.force:
                raise ValidationError(f"Output already exists: {target}. Use --force to replace it.")
        try:
            for target in self.targets:
                target.parent.mkdir(parents=True, exist_ok=True)
                descriptor, name = tempfile.mkstemp(
                    prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
                )
                self.temporary[target] = Path(name)
                os.close(descriptor)
        except Exception:
            self._cleanup_temporary()
            raise
        return self

    def _cleanup_temporary(self) -> None:
        for path in self.temporary.values():
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        self.temporary.clear()

    def staged_path(self, target: Path) -> Path:
        return self.temporary[target]

    def commit(self) -> None:
        for target in self.targets:
            os.replace(self.temporary[target], target)
        self.temporary.clear()

    def __exit__(self, exc_type, exc, traceback) -> None:  # type: ignore[no-untyped-def]
        self._cleanup_temporary()


def write_results(path: Path, results: tuple[SiteResult, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=_TSV_FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for item in results:
            writer.writerow(
                {
                    "site_id": item.site_id,
                    "reference": item.reference,
                    "position": "" if item.position is None else item.position,
                    "input_row": item.input_row,
                    "parent_states": item.parent_states,
                    "child_states": item.child_states,
                    "possible_pairs": item.possible_pairs,
                    "change": item.change,
                    "parsimony_status": item.parsimony_status,
                    "fixed_within_clade": bool_text(item.fixed_within_clade),
                    "exclusive_to_clade": bool_text(item.exclusive_to_clade),
                    "descendant_state": item.descendant_state,
                    "descendant_total": item.descendant_total,
                    "descendant_callable": item.descendant_callable,
                    "descendant_state_count": item.descendant_state_count,
                    "outside_total": item.outside_total,
                    "outside_callable": item.outside_callable,
                    "outside_same_state_count": item.outside_same_state_count,
                    "parsimony_score": item.parsimony_score,
                    "selection_reason": item.selection_reason,
                }
            )


def write_members(path: Path, branch: BranchRecord) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(f"{name}\n" for name in branch.descendant_tips))


def write_report(path: Path, report: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        )


def write_branches(path: Path, branches: list[BranchRecord]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=_BRANCH_FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for branch in sorted(
            branches,
            key=lambda item: (-item.descendant_count, item.descendant_tips, item.branch_id),
        ):
            writer.writerow(
                {
                    "branch_id": branch.branch_id,
                    "short_id": branch.short_id,
                    "descendant_count": branch.descendant_count,
                    "parent_label": branch.parent_label,
                    "child_label": branch.child_label,
                    "first_descendant": branch.descendant_tips[0],
                    "last_descendant": branch.descendant_tips[-1],
                }
            )
