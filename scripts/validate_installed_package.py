"""Validate an installed BRANCHSNV distribution."""

from __future__ import annotations

import importlib.metadata

import branchsnv


def main() -> None:
    installed_version = importlib.metadata.version("branchsnv")

    if installed_version != branchsnv.__version__:
        raise SystemExit(
            "Version mismatch: "
            f"distribution={installed_version!r}, "
            f"package={branchsnv.__version__!r}"
        )

    requirements = importlib.metadata.requires("branchsnv") or []
    if requirements:
        raise SystemExit(f"Unexpected runtime dependencies: {requirements}")

    print(
        f"Installed BRANCHSNV {installed_version} validated; "
        "no runtime dependencies declared."
    )


if __name__ == "__main__":
    main()
