# Release procedure

This checklist is for maintainers preparing a tagged BRANCHSNV release. A
release is not complete merely because the package builds: production tests,
independent validation, documentation, package metadata, and installed command
behaviour must all refer to the same software version.

## 1. Prepare the release candidate

1. Confirm that the working tree is clean and that all intended changes are on
   `main`.
2. Record the exact production commit with `git rev-parse HEAD`.
3. Confirm that `pyproject.toml`, `src/branchsnv/__init__.py`, `CHANGELOG.md`,
   and `CITATION.cff` contain the intended release version.
4. Confirm that README and documentation examples use commands supported by
   that version.

## 2. Run production tests

Run the full standard-library suite in an environment isolated from the Python
user site:

```bash
PYTHONNOUSERSITE=1 PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONNOUSERSITE=1 PYTHONWARNINGS=error PYTHONPATH=src \
  python -m unittest discover -s tests -v
```

Re-run the bundled example and compare all generated files with the committed
expected outputs.

## 3. Validate the exact release candidate independently

Use the separate `branchsnv-validation` repository and its documented locked
validation environment. Record the exact validation-repository commit before
running the experiments.

From the validation repository, run all completed experiments against the exact
production working tree:

```bash
PRODUCTION_ROOT=/path/to/branchsnv
EXPECTED_VERSION=X.Y.Z

PYTHONNOUSERSITE=1 bash run_completed_experiments.sh "$PRODUCTION_ROOT"

PYTHONNOUSERSITE=1 python verify_reproduced_results.py \
  --results-dir reproduced_results \
  --branchsnv-root "$PRODUCTION_ROOT" \
  --expected-version "$EXPECTED_VERSION" \
  --benchmark-repetitions 3
```

The verifier must finish with `REPRODUCED RESULTS: PASS` and confirm the
production source identity, validation-script identity, deterministic
analytical outputs, Experiments 01–06 pass criteria, and Experiment 04
benchmark protocol.

`verify_publication_snapshot.py` verifies the committed historical publication
snapshot. It is an integrity check for that frozen record and must not be used
as evidence that a newly generated release candidate has been validated.

`run_completed_experiments.sh` refuses to reuse a non-empty reproduction
output directory and refuses to write into the canonical `results/` snapshot.
Remove or archive an earlier `reproduced_results/` directory before starting a
new release validation run.

Benchmark timings are environment-specific, but deterministic analytical
outputs and integrity checks must reproduce as documented. Preserve the exact
production and validation commit identifiers with the release record.

## 4. Build and inspect distributions

From the production repository:

```bash
PYTHONNOUSERSITE=1 python -m pip install --upgrade build twine
PYTHONNOUSERSITE=1 python -m build
PYTHONNOUSERSITE=1 python -m twine check dist/*
```

Install the wheel into a fresh environment and run:

```bash
branchsnv --version
branchsnv validate --help
branchsnv inspect --help
branchsnv find --help
python -m pip check
```

Repeat the installed-package check for the source distribution.

Confirm that wheel metadata contains no unexpected `Requires-Dist` entries.

## 5. Create the release

1. Create a signed or annotated tag `vX.Y.Z` matching the package version.
2. Push the tag and confirm the release-build GitHub Actions workflow passes
   for that exact tag and commit.
3. Create the GitHub release from that exact tag using the corresponding
   changelog entry.
4. Attach verified distribution artefacts and checksums if release policy
   requires them.
5. Archive the exact production and validation releases in a permanent archive
   such as Zenodo and record the resulting DOI(s) in `CITATION.cff` and the
   manuscript.

## 6. Package-manager release

Only after the GitHub release is final should downstream packaging be prepared.
For Bioconda, build the recipe from the immutable tagged source archive and its
SHA-256 checksum rather than from a moving branch. Test the installed
`branchsnv` command in the recipe.

If PyPI publication is desired, publish only the already-verified release
artefacts or rebuild from the exact immutable release tag under the documented
release process.
