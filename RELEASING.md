# Releasing convert-md

For maintainers. Releases are built and published by GitHub Actions when a version tag is pushed.

## Every release

1. Make sure the **Tests** workflow is green on `main`.
2. Update the version in `src/convert_md/__init__.py` (for example `1.0.1`), following
   [Semantic Versioning](https://semver.org/): fixes bump the last number, new features the middle one,
   breaking changes the first.
3. In `CHANGELOG.md`, move the items under **Unreleased** into a new `## [1.0.1] - YYYY-MM-DD` section
   and update the links at the bottom.
4. Commit, tag and push:

   ```powershell
   git commit -am "Release 1.0.1"
   git tag v1.0.1
   git push origin main --tags
   ```

The **Release** workflow then:

| Job | Does |
|---|---|
| build | Checks the tag matches the version, builds the wheel and source package, runs `twine check` |
| github-release | Creates the GitHub release with notes from `CHANGELOG.md` and attaches the packages |
| pypi | Publishes to PyPI (only when PyPI publishing is turned on, below) |

If the tag doesn't match the version, the workflow stops before anything is published. Delete the tag
(`git tag -d v1.0.1` and `git push origin :refs/tags/v1.0.1`), fix the version, and tag again.

## One-time PyPI setup

The PyPI project name is **convert-md**, the same as the repository and the command.
(The working name `md-convert` couldn't be used: PyPI already has `mdconvert` and treats names that
differ only by `-`, `_` or `.` as the same.)

Publishing uses PyPI trusted publishing, so no API token is stored in GitHub.

1. Create a PyPI account at https://pypi.org (turn on two-factor authentication).
2. Go to **Your account → Publishing → Add a new pending publisher** and enter:

   | Field | Value |
   |---|---|
   | PyPI project name | `convert-md` |
   | Owner | `W3i-io` |
   | Repository name | `convert-md` |
   | Workflow name | `release.yml` |
   | Environment name | `pypi` |

3. In the GitHub repository: **Settings → Environments → New environment** named `pypi`.
   Optionally add yourself as a required reviewer so each PyPI upload waits for approval.
4. **Settings → Secrets and variables → Actions → Variables → New repository variable**:
   `PUBLISH_TO_PYPI` = `true`.
5. Publish by re-running the **Release** workflow for the current tag, or with the next tag.

To rehearse first, register the same pending publisher on https://test.pypi.org and temporarily add
`repository-url: https://test.pypi.org/legacy/` under the `pypa/gh-action-pypi-publish` step.

## Repository settings worth turning on

| Setting | Where |
|---|---|
| Private vulnerability reporting | **Settings → Code security → Private vulnerability reporting** (used by SECURITY.md) |
| Dependabot alerts and security updates | **Settings → Code security** |
| Branch protection for `main`, requiring the Tests workflow | **Settings → Branches** |
