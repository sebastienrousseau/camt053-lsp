# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.9] - 2026-06-27

### Changed

- **Version** — suite-wide lockstep bump to `0.0.9`. No functional changes.

## [0.0.8] - 2026-06-26

### Changed

- **Version** — suite-wide lockstep bump to `0.0.8`. No functional changes.

## [Unreleased]

### Added

- **`--log-level` CLI flag** (`{DEBUG,INFO,WARNING,ERROR}`, default
  `WARNING`) that configures Python `logging` before the server starts.
  Logs are written to stderr so they never corrupt the LSP stdio
  transport; `basicConfig(force=True)` ensures the level applies even when
  a dependency has already configured the root logger.
  ([#45](https://github.com/sebastienrousseau/camt053-lsp/issues/45)).
- **Cross-repo release tooling** for the lockstep-versioned suite:
  `scripts/suite-status.sh` (read-only drift check across local / tag /
  GitHub Release / PyPI) and `scripts/suite-release.sh` (safe-by-default,
  idempotent orchestrator that bumps, PRs, merges, tags, and releases every
  package). A weekly `suite-version-check.yml` workflow guards against drift.
  See [`docs/RELEASING.md`](docs/RELEASING.md).

### Security

- **Keyless-signed releases** — the release workflow now signs every
  distribution with sigstore/cosign (Fulcio + Rekor via the workflow's OIDC
  identity) and attaches the `.sig` + `.pem` to the GitHub release, on top of
  the existing SLSA build-provenance attestations (OpenSSF Scorecard
  `Signed-Releases`).

## [0.0.7] - 2026-06-26

### Added

- **CLI `--version` / `--help` flags** — `camt053-lsp --version` prints the
  package version and `--help` prints usage; running with no arguments serves
  LSP over stdio as before
  ([#37](https://github.com/sebastienrousseau/camt053-lsp/issues/37)).
- **Editor setup examples** — dedicated Helix (`languages.toml`) and
  Emacs/Eglot (`init.el`) configuration sections in the Quickstart
  ([#38](https://github.com/sebastienrousseau/camt053-lsp/issues/38),
  [#39](https://github.com/sebastienrousseau/camt053-lsp/issues/39)).
- **More `_looks_like_xml` edge-case tests** — UTF-8 BOM and empty/blank
  input ([#40](https://github.com/sebastienrousseau/camt053-lsp/issues/40)).

### Security

Supply-chain and CI hardening to raise the OpenSSF Scorecard rating and clear
the imported Scorecard code-scanning alerts.

- **Pinned all GitHub Actions to full commit SHAs** (with version comments) in
  every workflow, replacing mutable tag/branch references
  (`Pinned-Dependencies`).
- **Hash-pinned every CI/release pip install** via new
  `requirements/*.txt` files compiled with `uv pip compile --generate-hashes`
  and installed with `pip install --require-hashes`. The test job now imports
  the package through `python -m pytest` (repo root on `sys.path`) instead of
  an un-pinnable `pip install -e .`. Regenerate with `make pip-compile`.
- **Applied least-privilege `GITHUB_TOKEN` permissions** in `release.yml`:
  the top-level token is now read-only, with `contents: write` (and
  `id-token`/`attestations: write`) granted only on the jobs that need them
  (`Token-Permissions`).
- **Added fuzzing** — an Atheris harness (`fuzz/fuzz_parser.py`) exercising the
  total document-processing entry points, wired into ClusterFuzzLite
  (`.clusterfuzzlite/`) with PR and scheduled batch workflows (`Fuzzing`).
- **Hardened checkouts** with `persist-credentials: false` across workflows.

### Documentation

Work toward the OpenSSF Best Practices **gold** badge.

- **Per-file copyright + `SPDX-License-Identifier: Apache-2.0` headers** added
  to every source file (`copyright_per_file` / `license_per_file`).
- **Documented code-review, test-coverage, and reproducible-build standards**
  in `CONTRIBUTING.md` (`code_review_standards` and supporting criteria).
- **Made the OpenSSF Best Practices badge consistent** with the other badges
  (shields.io `for-the-badge` style).

## [0.0.6] - 2026-06-22

### Added

- **In-editor CBPR+ Nov 2026 diagnostics for camt.05x XML documents**.
  When the LSP opens or receives changes for an XML file (detected by
  content sniff: leading `<?xml` or bare root element, tolerant of
  whitespace), it runs
  `camt053.services.check_cbpr_readiness` and publishes one
  diagnostic per issue: error-severity for unstructured-only postal
  addresses (the Nov 2026 reject case) and unknown schemas;
  warning-severity for deprecated schema versions. The XPath-style
  location of each `<PstlAdr>` is included in the diagnostic message;
  precise line/column mapping (via `lxml.sourceline`) is tracked as a
  v0.0.7 enhancement. JSON reversing-entry documents continue to use
  the existing record-validation path; the LSP dispatches on document
  content, so editors do not need new file-type registration.

Part of the v0.0.6 batch tracked in #16.

## [0.0.5] - 2026-06-19

### Fixed

- **Broken documentation links** — the `https://camt053.com` URLs in the README
  and the `homepage` field in `pyproject.toml` pointed at a domain that no
  longer resolves. They now point at the published documentation site at
  <https://sebastienrousseau.github.io/camt053/>
  ([#4](https://github.com/sebastienrousseau/camt053-lsp/issues/4)).

### Changed

- **Version** — bumped to `0.0.5` as part of the suite-wide lockstep version
  bump across the `camt053` projects. There are no functional changes to the
  Language Server in this release beyond the documentation link fix.

## [0.0.4] - 2026-06-19

### Added

- **Security policy** — a `SECURITY.md` describing supported versions, private
  vulnerability reporting via GitHub Security Advisories, response timelines,
  and scope for the Language Server
- **Dependabot** — weekly dependency update configuration for the `pip` and
  `github-actions` ecosystems, grouped and labelled for easier review
- **CodeQL** — a weekly (and push / pull-request) CodeQL scanning workflow
  running the `security-and-quality` query suite for Python
- **Bandit** — a `Security Scan` CI job that runs Bandit (`-ll`) over
  `camt053_lsp/` to catch medium- and high-severity issues
- **Issue & PR templates** — GitHub bug-report and feature-request issue
  templates (with a security-advisory contact link) and a pull-request template
- **CODEOWNERS** — a `CODEOWNERS` file requesting review from the maintainer on
  all changes

## [0.0.3] - 2026-06-19

### Fixed

- **Version consistency** — `camt053_lsp.__version__` and the version announced
  by the `LanguageServer` to clients now match the packaged `pyproject.toml`
  version. Previously `__version__` was `0.0.1` and the server announced
  `v0.0.2` while the published package was `0.0.2`, so the reported versions
  drifted from the actual release. A new version-consistency test asserts that
  `__version__` equals the `pyproject.toml` `version`, guarding against
  recurrence.

## [0.0.2] - 2026-06-18

### Added

- **Code actions** — a `code_actions` helper and a `textDocument/codeAction`
  handler that, for each record missing required fields (from
  `services.get_required_fields`), propose a quick-fix that inserts the missing
  keys (with empty placeholder values) into that record. Valid records and
  malformed JSON propose no action
- **Message-type hover** — hovering a supported `camt.05x` message-type token
  now shows its human-readable name (e.g.
  `camt.053.001.14 — Bank To Customer Statement`) via the new `hover_markup` /
  `message_type_name` helpers; field-description hover is unchanged
- **Document symbols (outline)** — a `document_symbols` helper and a
  `textDocument/documentSymbol` handler that produce one symbol per record
  (named `Record N`, with `statement_msg_id` / `entry_ref` as detail) and a
  child symbol per field, each with a best-effort line number. Malformed JSON
  yields an empty outline
- **Formatting** — a `format_text` helper and a `textDocument/formatting`
  handler that pretty-print the document with a stable 2-space indent while
  preserving key order, returned as a single full-document `TextEdit`. Invalid
  JSON leaves the document unchanged
- **JSONC tolerance** — a dependency-free pre-step strips `//` line comments and
  trailing commas before parsing, so diagnostics, symbols, and formatting all
  work on JSONC data files. Clean JSON behaviour is unchanged

### Deferred

- YAML data-file support is noted as a future enhancement and is not yet
  implemented (no YAML dependency added in this release)

## [0.0.1] - 2026-06-16

### Added

- Initial release of `camt053-lsp`, a [pygls](https://github.com/openlawlibrary/pygls)-based
  Language Server Protocol (LSP) server for authoring camt053 reversing-entry
  data JSON files (Python 3.10+)
- A `camt053-lsp` console entry point that starts the language server over
  stdio for editor LSP clients
- **Diagnostics** — schema validation of each record against a message
  type's input JSON Schema (missing required fields, types, patterns) plus
  IBAN / BIC validation of identifier fields
- **Completion** — every input field (with its schema description) and the
  full list of supported camt message types
- **Hover** — schema descriptions for the field under the cursor
- Pure, importable helper functions (`compute_diagnostics`,
  `completion_items`, `hover_text`) backed by the shared `camt053.services`
  layer, so editor behaviour matches the CLI, REST API, and MCP server
- Part of the **camt053 suite** alongside the core `camt053` library and the
  `camt053-mcp` Model Context Protocol server

[0.0.9]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.9
[0.0.8]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.8
[0.0.5]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.5
[0.0.4]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.4
[0.0.3]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.3
[0.0.2]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.2
[0.0.1]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.1
