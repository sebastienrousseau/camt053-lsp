<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Releasing camt053-lsp

The camt053 suite releases every member together at one version. The core
goes first, then the members, in this order:

| Order | Package | Repository |
| :---: | :--- | :--- |
| 1 | `camt053` (core) | [camt053](https://github.com/sebastienrousseau/camt053) |
| 2 | `camt053-lsp` | [camt053-lsp](https://github.com/sebastienrousseau/camt053-lsp) |
| 3 | `camt053-loader-mt940` | [camt053-loader-mt940](https://github.com/sebastienrousseau/camt053-loader-mt940) |
| 4 | `camt053-loader-mt942` | [camt053-loader-mt942](https://github.com/sebastienrousseau/camt053-loader-mt942) |
| 5 | `camt053-writer-xlsx` | [camt053-writer-xlsx](https://github.com/sebastienrousseau/camt053-writer-xlsx) |
| 6 | `camt053-mcp` | [camt053-mcp](https://github.com/sebastienrousseau/camt053-mcp) |

Each member's release is a real iteration, not a bare version bump: its
Dependabot updates and security alerts are folded in, its floors on the
core move to the newest released version, its open issues are triaged, and
its CHANGELOG says what changed in it.

## The release branch

Work for version `X.Y.Z` happens on `feat/vX.Y.Z`, opened from `main`. Topic
work and Dependabot updates reach it as commits, never as pull requests into
it. One pull request, `feat: release vX.Y.Z`, takes it to `main`; it is the
only open pull request against `main`, and the Dependabot pull requests it
supersedes are closed with a link to it once it merges.

Before that pull request is ready:

1. Every version source says `X.Y.Z`: `pyproject.toml`,
   `camt053_lsp/__init__.py`, the `CHANGELOG.md` heading, `CITATION.cff`, the
   README's "Latest release" callout and the `SECURITY.md` supported row.
   `python3 scripts/verify_versions.py` checks all of them, and CI runs it.
2. `poetry.lock` matches `pyproject.toml` (`poetry check --lock`), and the
   hash-pinned `requirements/*.txt` are recompiled with `make pip-compile`.
3. `make check` passes.

`main` is squash-merged only (linear history, signed commits).

## Tagging and publishing

The tag is cut on the squash commit, only once `camt053` `X.Y.Z` is the
latest version on PyPI (the core releases first):

- Tag `vX.Y.Z`, SSH-signed and annotated, with the message
  `camt053-lsp vX.Y.Z`.
- Pushing the tag runs [`release.yml`](../.github/workflows/release.yml):
  PyPI Trusted Publishing with PEP 740 attestations, SLSA provenance, cosign
  signatures, and CycloneDX, SPDX and licence manifests on the GitHub
  release.
- The GitHub release is titled `camt053-lsp X.Y.Z` (no leading `v`). Its
  notes have `## Highlights ⭐️`, `## What's Changed`, `## Checksums` (the
  SHA-256 of every attached asset) and a `**Full Changelog**` compare link,
  with no em dashes.

## Checking the suite

- [`scripts/check_suite_consistency.py`](../scripts/check_suite_consistency.py)
  runs daily ([`suite-consistency.yml`](../.github/workflows/suite-consistency.yml)):
  every member must publish the core's version, and this tree must match
  camt053-lsp's own PyPI release.
- [`scripts/suite-status.sh`](../scripts/suite-status.sh) runs weekly
  ([`suite-version-check.yml`](../.github/workflows/suite-version-check.yml))
  and prints each member's version in `pyproject.toml`, its latest tag, its
  GitHub release and PyPI. It assumes the sibling repositories are cloned
  next to this one (override with `SUITE_DIR=/path/to/parent`).

## Branch protection note

`main` requires signed commits, linear history and the `Analyze (Python)
(python)`, `Lint & Type Check` and `Security Scan` checks, enforced for
admins. Squash merges through GitHub are GitHub-signed and satisfy the
signature rule. See [`MAINTAINERS.md`](../MAINTAINERS.md) for the bypass
procedure.
