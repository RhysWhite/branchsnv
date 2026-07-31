# Release procedure

1. Confirm that the working tree is clean.
2. Run the full standard-library test suite:

   ```bash
   PYTHONPATH=src python -m unittest discover -s tests -v
   ```

3. Re-run the bundled example and compare it with the committed expected files.
4. Re-run the AK3 validation recipe when the external working inputs are
   available and inspect any difference rather than updating snapshots blindly.
5. Confirm that `pyproject.toml`, `src/branchsnv/__init__.py`, `CHANGELOG.md`,
   and `CITATION.cff` contain the same version.
6. Build in a clean environment:

   ```bash
   python -m pip install build
   python -m build
   ```

7. Install the wheel into a new environment and run:

   ```bash
   branchsnv --version
   branchsnv validate --help
   branchsnv inspect --help
   branchsnv find --help
   ```

8. Inspect wheel metadata and confirm that `Requires-Dist` is absent.
9. Create a signed or annotated Git tag `vX.Y.Z`.
10. Create a GitHub release using the changelog text and attach the source and
    wheel distributions.
11. Publish to PyPI only after the GitHub release artefacts have been verified.
12. Archive the release and record its DOI in `CITATION.cff` when available.

A release is not complete merely because the package builds. The scientific
validation, documentation, package metadata, and installed command must agree.
