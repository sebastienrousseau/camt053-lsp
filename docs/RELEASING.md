# Releasing the camt053 suite

The camt053 suite is versioned in **lockstep**: every package shares the same
version and is released together. The five packages are:

| Package | Repo |
| :--- | :--- |
| `camt053` (core) | [camt053](https://github.com/sebastienrousseau/camt053) |
| `camt053-lsp` | [camt053-lsp](https://github.com/sebastienrousseau/camt053-lsp) |
| `camt053-mcp` | [camt053-mcp](https://github.com/sebastienrousseau/camt053-mcp) |
| `camt053-writer-xlsx` | [camt053-writer-xlsx](https://github.com/sebastienrousseau/camt053-writer-xlsx) |
| `camt053-loader-mt940` | [camt053-loader-mt940](https://github.com/sebastienrousseau/camt053-loader-mt940) |

## Tooling

Two scripts in [`scripts/`](../scripts) operate across the whole suite. They
assume the sibling repos are cloned next to this one (override with
`SUITE_DIR=/path/to/parent`).

### `scripts/suite-status.sh` — drift check (read-only)

Prints the version of every package across all four surfaces — local
`pyproject.toml`, latest git tag, GitHub Release, and PyPI — and exits non-zero
if they disagree. Run it any time; it is also run weekly in CI by
[`suite-version-check.yml`](../.github/workflows/suite-version-check.yml).

```sh
./scripts/suite-status.sh
```

### `scripts/suite-release.sh` — orchestrated release

Bumps every version source, adds a lockstep `CHANGELOG` entry, opens a PR, waits
for CI, squash-merges, then pushes a **signed tag** that triggers each repo's
`release.yml` (PyPI Trusted Publishing + SLSA provenance + SBOMs + GitHub
release). It processes **core first**, then the leaf packages.

- **Safe by default**: prints the plan and changes nothing without `--yes`.
- **Idempotent / resumable**: repos already at the target version skip the bump;
  existing tags are not recreated, so re-running after a partial failure
  continues cleanly.

```sh
./scripts/suite-release.sh 0.0.8            # dry run — review the plan
./scripts/suite-release.sh 0.0.8 --yes      # perform the release
./scripts/suite-release.sh 0.0.8 --yes --repos camt053,camt053-lsp  # subset
```

## Manual checklist (if releasing a single repo by hand)

1. Bump **all** version sources (core has three: `pyproject.toml`,
   `camt053/__init__.py`, `camt053/constants.py`; the others have
   `pyproject.toml` + the package `__init__.py`).
2. If `pyproject.toml` changed, run `poetry lock` so the release SBOM job's
   `poetry install` does not fail on a stale lock.
3. Update `CHANGELOG.md` (+ footer link).
4. Open a PR; merge once CI is green.
5. `git tag -s vX.Y.Z -m vX.Y.Z && git push origin vX.Y.Z`.
6. Confirm with `./scripts/suite-status.sh`.

## Branch protection note

`main` on `camt053`, `camt053-lsp`, and `camt053-mcp` requires PRs (0 approvals,
so the solo maintainer can self-merge). `camt053-lsp` additionally enforces
admins and signed commits — squash-merges via the GitHub UI / `gh` are
GitHub-signed and satisfy that automatically. See
[`MAINTAINERS.md`](../MAINTAINERS.md) for the bypass procedure.
