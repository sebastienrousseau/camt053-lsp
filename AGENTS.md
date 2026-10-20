<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# AGENTS.md

Invariants for AI-assisted contributions to `camt053-lsp`. Read this before changing anything.

Everything here applies equally to humans and automated agents. It is addressed to agents because agents can make breaking changes across multiple files before anyone notices.

## What this repository is

`camt053-lsp` is the Language Server of the camt053 suite: diagnostics, completion, hover, code actions, document symbols and formatting for the JSON and JSONC reversing-entry records that drive ISO 20022 `camt.053` reversal generation. It holds no validation rules of its own; every check goes through the core's `camt053.services` facade, so the editor reports exactly what the CLI, REST API and MCP server would. Its core value is that feedback arrives while someone types, and never disagrees with the core.

## 1. Core Invariants

1. **Versioning**: releases stay on the `0.0.x` line and increment strictly by `0.0.1`. Version work happens on `feat/v<next-version>` only. `v0.1.0` follows `v0.0.999`.
2. **Suite lockstep**: every member ships the core's version, and the core releases first. `scripts/check_suite_consistency.py` is the shared copy every member carries (only `THIS` differs); change it in every member or not at all. The `camt053` floor in `pyproject.toml` and `requirements/*.in` is the newest released core.
3. **Single source of truth**: the version in `pyproject.toml` must agree with `camt053_lsp/__init__.py`, `CHANGELOG.md`, `CITATION.cff`, the README's latest-release line and `SECURITY.md` (checked by `scripts/verify_versions.py`).
4. **The core decides**: validation, identifier checks and CBPR+ readiness come from `camt053.services`. Do not reimplement a rule here; fix it in the core.
5. **Output is the contract**: a change to the diagnostics, completion items, code actions, symbols or edits the server returns for the same document, or to the plain-dict shapes of the helpers in `camt053_lsp.server`, is breaking even when no signature moves.
6. **Every keystroke re-parses the document**: work done per change must stay linear in its length (`tests/test_stress.py`, run with `pytest -m perf --no-cov`).
7. **Stdout is the transport**: logs go to stderr only.
8. **Dual licensing**: Apache-2.0 OR MIT.

## 2. Before You Claim To Be Done

```console
make check
```

It runs ruff, black, mypy `--strict`, bandit, the complexity gate, pytest (100% line and branch coverage) and the examples; CI also runs `python3 scripts/verify_versions.py`, interrogate, `pip-audit`, CodeQL, Scorecard and ClusterFuzzLite. Every function stays within cyclomatic 10, cognitive 15, Halstead difficulty 30 and 60 lines, every file within 500 lines; existing offenders are in `complexity-baseline.json`, which may only shrink.

## 3. Hygiene First

Before any feature, fix or release work: open Dependabot PRs and alerts, code-scanning and secret-scanning alerts, `pip-audit`, and a red CI on `main` are cleared first. A dependency with an advisory is floored in `pyproject.toml` (and the `requirements/*.in` it appears in) so no affected version resolves.

## 4. Leave Alone

- `tests/test_suite_conformance.py` is a vendored, checksummed copy shared across the suite; it is excluded from black for that reason.
- `poetry.lock` and `requirements/*.txt` are generated (`poetry lock`, `make pip-compile`); never hand-edit them.
- `.github/demo.gif` is rendered from `.github/demo.tape` by `make demo`; never edit it by hand.
