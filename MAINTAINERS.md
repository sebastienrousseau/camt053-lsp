<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Maintainers

The people who can merge PRs and cut releases for `camt053` and the four
sibling packages in the suite (`camt053-lsp`, `camt053-mcp`,
`camt053-writer-xlsx`, `camt053-loader-mt940`). See
[`GOVERNANCE.md`](GOVERNANCE.md) for roles, decision making, and how to
become a maintainer — we are actively looking for a second one.

| Maintainer | GitHub | Areas | Release authority |
| :--- | :--- | :--- | :--- |
| Sebastien Rousseau (lead) | [@sebastienrousseau](https://github.com/sebastienrousseau) | All | Yes |
| _open_ | — | — | — |

## Emeritus

_None yet._

## Becoming a maintainer

The path is intentionally short:

1. Three substantive merged PRs that touch core code (not docs-only) within
   any rolling 6-month window.
2. Nomination from the lead maintainer in `MAINTAINERS.md` (this file) via
   a PR opened by the candidate.
3. Two weeks of public comment on that PR. Existing maintainers may object;
   absent objection, the PR merges and the candidate is added.

Maintainers are also expected to follow the project's
[Code of Conduct](CODE_OF_CONDUCT.md) and the disclosure timeline in
[`SECURITY.md`](SECURITY.md).

## Releasing

The suite is versioned in **lockstep** — every `camt053*` package shares the
same version. Cut a release by pushing a signed `vX.Y.Z` tag; `release.yml`
then builds the package, publishes to PyPI via Trusted Publishing, attaches
SLSA build provenance + SBOMs, and creates the GitHub release.

```bash
git tag -s vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z
```

### Branch-protection bypass

`main` enforces required status checks **for admins** (`enforce_admins`) and
**requires signed commits**. Squash-merges through the GitHub UI / `gh` are
GitHub-signed and satisfy the signing requirement automatically.

If a required check is ever stuck and a merge must proceed, temporarily lift
admin enforcement, merge, then restore it:

```bash
gh api -X DELETE repos/sebastienrousseau/camt053-lsp/branches/main/protection/enforce_admins
# ... perform the merge ...
gh api -X POST   repos/sebastienrousseau/camt053-lsp/branches/main/protection/enforce_admins
```
