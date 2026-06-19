# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.0.5]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.5
[0.0.4]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.4
[0.0.3]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.3
[0.0.2]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.2
[0.0.1]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.1
