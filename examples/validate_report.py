#!/usr/bin/env python3
"""Validate selected BRANCHSNV report fields using only the standard library."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--expected-descendants", required=True, type=int)
    parser.add_argument("--minimum-reported-sites", required=True, type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    observed_descendants = report["branch"]["descendant_count"]
    observed_sites = report["results"]["reported_sites"]
    warnings = report.get("warnings", [])

    if observed_descendants != args.expected_descendants:
        raise SystemExit(
            f"Descendant count mismatch: expected {args.expected_descendants}, "
            f"observed {observed_descendants}."
        )
    if observed_sites < args.minimum_reported_sites:
        raise SystemExit(
            f"Too few reported sites: required at least {args.minimum_reported_sites}, "
            f"observed {observed_sites}."
        )
    if warnings:
        raise SystemExit(f"BRANCHSNV report contains warnings: {warnings}")

    print(
        f"VALID: descendants={observed_descendants}; reported_sites={observed_sites}; "
        "warnings=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
