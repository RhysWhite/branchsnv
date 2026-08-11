# Release procedure

This checklist is for maintainers preparing a tagged BRANCHSNV release. A
release is not complete merely because the package builds: production tests,
independent validation, documentation, package metadata, and installed command
behaviour must all refer to the same software version.

## 1. Prepare the release candidate

1. Confirm that the working tree is clean and that all intended changes are on
   `main`.
2. Confirm that `pyproject.toml`, `src/branchsnv/__init__.py`, `CHANGELOG.md`,
   and `CITATION.cff` contain the intended release version.
3. Confirm that README and documentation examples use commands supported by
   that version.

## 2. Run production tests

Run the full standard-library suite:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Re-run the bundled example and compare all generated files with the committed
expected outputs.

## 3. Validate the exact release candidate independently

Use the separate publication-validation repository:

```bash
cd ../branchsnv-validation
bash run_completed_experiments.sh ../branchsnv
python verify_publication_snapshot.py
```

Before a stable publication release, regenerate and commit the validation
snapshot against the exact production release candidate. Do not claim that a
new version is validated merely because its analytical source is expected to
be unchanged.

Benchmark timings are environment-specific, but deterministic analytical
outputs and integrity checks must reproduce as documented.

## 4. Build and inspect distributions

From the production repository:

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
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
2. Push the tag and confirm the release-build GitHub Actions workflow passes.
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
