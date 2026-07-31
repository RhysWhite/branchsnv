# Contributing

BRANCHSNV deliberately has a narrow scope. Changes should preserve exactness,
determinism, auditability, and the absence of runtime dependencies.

## Development setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
```

The tests use only the Python standard library. Building release artefacts
requires the `build` package:

```bash
python -m pip install build
python -m build
```

## Pull requests

A pull request should:

1. explain the scientific and software behaviour being changed;
2. add or update tests, including an adversarial case where appropriate;
3. preserve deterministic output unless the change is explicitly documented;
4. update user documentation and `CHANGELOG.md`;
5. avoid adding runtime dependencies without prior discussion.

Parser extensions must document the newly supported syntax and add malformed
input tests. Algorithm changes must be checked against an implementation that
is independent of the production algorithm.
