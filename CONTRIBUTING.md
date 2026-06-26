# Contributing to camt053-lsp

Thank you for your interest in contributing to **camt053-lsp**, the Language
Server Protocol server for the [camt053](https://github.com/sebastienrousseau/camt053)
suite. This guide covers the development workflow and standards.

## Development Setup

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation)
- Git with SSH commit signing configured

### Setup

```bash
# Clone and install
git clone git@github.com:sebastienrousseau/camt053-lsp.git
cd camt053-lsp
poetry install

# Verify
poetry run pytest tests/ -q
```

The package depends on the core `camt053` library and `pygls`; both are
installed automatically by `poetry install`.

### On macOS

```bash
brew install python@3.12 poetry
```

### On Linux (Debian/Ubuntu)

```bash
sudo apt install python3 python3-pip
pip install poetry
```

### On WSL

```bash
sudo apt install python3 python3-pip
pip install poetry
# Ensure ~/.local/bin is in PATH
```

## Good First Issues

New or casual contributors should start with issues labelled
[`good first issue`](https://github.com/sebastienrousseau/camt053-lsp/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
— small, self-contained tasks (a focused test, a docstring, a small
diagnostic tweak) that don't require deep knowledge of the codebase.
[`help wanted`](https://github.com/sebastienrousseau/camt053-lsp/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)
marks slightly larger tasks open for contribution. Comment on an issue to
claim it before starting.

## Workflow

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
3. **Make changes** — follow the coding standards below
4. **Run tests**:
   ```bash
   poetry run pytest tests/ -v
   ```
5. **Run linters**:
   ```bash
   poetry run ruff check camt053_lsp/
   poetry run mypy camt053_lsp/
   poetry run black --check camt053_lsp/ tests/
   ```
6. **Sign and commit**:
   ```bash
   git commit -S -m "feat: add my feature"
   ```
7. **Push** and open a pull request

## Commit Signing (Required)

All commits **must** be signed with SSH or GPG.

### SSH Signing

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519
git config --global commit.gpgsign true
```

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add hover support for optional balance fields
fix: handle malformed JSON offsets in diagnostics
docs: update README with editor wiring examples
test: cover the bad-identifier diagnostic path
refactor: simplify the record line-offset heuristic
```

## Coding Standards

- **Line length:** 79 characters (enforced by Black + Ruff)
- **Type hints:** Required on all public functions (mypy strict)
- **Docstrings:** Required on all public classes and functions
- **Tests:** Every new feature must include tests

## Testing

```bash
# Full suite
poetry run pytest tests/ -v

# Single file
poetry run pytest tests/test_lsp_server.py -v
```

## Pull Request Checklist

- [ ] All tests pass (`poetry run pytest`)
- [ ] Linters pass (`ruff check`, `mypy`, `black --check`)
- [ ] Commits are signed
- [ ] PR title follows conventional commit format
- [ ] New features include tests and documentation

## Code Review

All changes land through pull requests and are reviewed before release:

- **Every change is a pull request** against `main`; direct pushes are
  blocked by branch protection.
- **`main` is protected** — required status checks (tests on Python
  3.10–3.12, lint, type-check, security scan, CodeQL) must pass, the branch
  must be up to date, and force-pushes and deletions are disabled.
- **A maintainer reviews each PR** before merging, checking for: tests
  covering new behaviour, no drop in coverage, no new linter or type errors,
  signed commits, and a conventional-commit title. Security-sensitive changes
  additionally follow [`SECURITY.md`](SECURITY.md).

See [`MAINTAINERS.md`](MAINTAINERS.md) for who can approve and merge.

## Test Coverage

CI enforces **100% statement and branch coverage** for `camt053_lsp`
(`pytest --cov --cov-branch --cov-fail-under=100`) and **100% docstring
coverage** (`interrogate`). New code must keep both at 100%. Every script
under `examples/` is run end-to-end by `tests/test_examples.py`.

## Reproducible Builds

- Runtime dependencies are locked with hashes in `poetry.lock`; CI/release
  tool installs are hash-pinned via `requirements/*.txt`
  (`pip install --require-hashes`).
- Distributions are built with `poetry build` from the tagged source.
- Each release publishes **SLSA build provenance** attestations
  (`actions/attest-build-provenance`) and CycloneDX/SPDX SBOMs, so any
  artifact traces back to the exact workflow run and commit.

## License

By contributing, you agree that your contributions will be licensed under
the [Apache License 2.0](LICENSE).
