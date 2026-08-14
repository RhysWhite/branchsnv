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

## 7. PyPI trusted publishing

BRANCHSNV uses a dedicated GitHub Actions workflow for tokenless PyPI
publication: `.github/workflows/publish-pypi.yml`. The workflow rebuilds from
an immutable release tag, reruns the production tests and installed-package
checks, and only then passes the wheel and source distribution to PyPI.

For the initial PyPI registration, configure a **pending trusted publisher** in
PyPI with the following exact values:

- PyPI project name: `branchsnv`
- GitHub owner: `RhysWhite`
- GitHub repository: `branchsnv`
- Workflow filename: `publish-pypi.yml`
- GitHub environment: `pypi`

Create the `pypi` environment in the GitHub repository before publishing.
Restrict deployment to trusted maintainers if approval controls are available.
Do not create or store a long-lived PyPI API token for this workflow.

For an already published immutable GitHub release, run the **Publish to PyPI**
workflow manually and supply the corresponding tag, for example `v0.1.0`.
Future GitHub releases will also trigger the workflow when the release is
published.

After publication, verify installation independently in a clean environment:

```bash
python -m venv /tmp/branchsnv-pypi-test
/tmp/branchsnv-pypi-test/bin/python -m pip install branchsnv==0.1.0
/tmp/branchsnv-pypi-test/bin/branchsnv --version
/tmp/branchsnv-pypi-test/bin/python -m pip check
```

Only after this check succeeds should the README advertise
`python -m pip install branchsnv` as a stable installation route.

## 8. Read the Docs

Documentation builds are configured as code using:

- `.readthedocs.yaml`
- `mkdocs.yml`
- `docs/requirements.txt`

Import `RhysWhite/branchsnv` into Read the Docs using `main` as the default
branch. The project should use the repository configuration file rather than
manually duplicated build settings. Confirm that both the default documentation
build and the stable release documentation build successfully before adding a
documentation badge or URL to package metadata.

## 9. Software Heritage

Submit both public repositories through Software Heritage **Save Code Now**:

- `https://github.com/RhysWhite/branchsnv`
- `https://github.com/RhysWhite/branchsnv-validation`

After ingestion completes, verify that the stable annotated release tags are
visible and record the Software Heritage persistent identifiers where useful.
Zenodo remains the DOI-bearing scholarly archive; Software Heritage provides an
independent content-addressed archive of the source-code history.

## 10. bio.tools

Register the production software in the ELIXIR bio.tools registry under the
identifier `branchsnv`. The entry should point to the canonical production
repository and, once live, include the stable documentation, Zenodo DOI, PyPI,
Bioconda and BioContainer links. The separate validation repository should be
linked as supporting validation material rather than registered as a second
software tool.

Do not add speculative URLs. Verify every external service is live before
adding its link to the README or package metadata.

## 11. Bioconda and BioContainers

After the Bioconda recipe is processed, verify the exact package version on the
Bioconda/Anaconda package page and test installation in a clean environment.
Bioconda automatically generates a corresponding BioContainer and uploads it
to Quay.io. Record and test the exact container tag produced for the stable
package; do not guess the build-string component of the tag.

Once the package and container are confirmed live, update installation
documentation to include the tested Conda command and the exact container pull
command.

## 12. Cross-link the distribution records

Once PyPI, Read the Docs, Bioconda/BioContainers, Software Heritage and
bio.tools are live, update the README and project metadata in one coordinated
commit. Cross-link only verified endpoints so that GitHub remains the canonical
source repository, Zenodo remains the DOI-bearing release archive, and every
additional service points back to the same software identity and release.
