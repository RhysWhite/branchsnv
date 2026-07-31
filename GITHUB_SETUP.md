# GitHub repository setup

## Repository metadata

- **Repository name:** `branchsnv`
- **Description:** `Dependency-free identification of branch-associated SNVs from rooted phylogenies and transposed NEXUS matrices.`
- **Visibility:** private during development; public only after validation and documentation review.
- **Topics:** `phylogenetics`, `snv`, `bacterial-genomics`, `nexus`, `newick`, `bioinformatics`, `ancestral-reconstruction`, `python`
- **Website:** leave blank until a permanent release or documentation site exists.

## Recommended settings

Enable:

- Issues
- Discussions only when there is capacity to moderate them
- Vulnerability reporting
- Automatically delete head branches after pull requests merge
- Require contributors to sign off commits only if the project adopts a DCO

Disable initially:

- Wiki, because versioned documentation is maintained in `docs/`
- GitHub Pages, unless a separate documentation build is added

## Main-branch protection

After the initial repository push, protect `main` with:

- pull requests required before merging;
- at least one approval;
- dismissal of stale approvals after new commits;
- required status checks for `CI / test`, `CI / build`, and CodeQL;
- conversation resolution required;
- force pushes and branch deletion disabled;
- administrator bypass avoided for normal changes.

For a single-maintainer repository, branch protection can be enabled after the
initial import so that the first commit does not require a pull request.

## First release gate

Do not create `v0.1.0` until:

1. CI passes on every supported Python version;
2. the built wheel installs in a clean environment;
3. wheel metadata contains no runtime dependencies;
4. the bundled example reproduces byte-for-byte;
5. the AK3 external validation passes against the recorded hashes;
6. the documented 385-branch discrepancy has been investigated or explicitly
   retained as an unresolved input/publication-version difference;
7. repository description, topics, citation metadata, and changelog agree; and
8. a clean release candidate has been independently reviewed.

## Suggested initial commit message

```text
Initial BRANCHSNV implementation and validation framework
```
