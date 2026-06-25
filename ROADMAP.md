<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# `camt053-lsp` roadmap

## Mission

The Language Server Protocol (LSP) server for the
[`camt053`](https://github.com/sebastienrousseau/camt053) ISO 20022
bank-statement library — real-time editor help for authoring
reversing-entry data files. Diagnostics, completion, hover, code-actions,
document-symbols, formatting; pure helpers behind every capability so the
same logic powers tests and downstream tooling.

## Where we are (v0.0.7, shipped 2026-06-22)

- **7 LSP capabilities** with pure-helper backings:
  - **Diagnostics**: `compute_diagnostics` (JSON record validation,
    schema + IBAN/BIC checks) + `compute_xml_diagnostics` (XML
    well-formedness).
  - **Completion**: `completion_items` — every input field with its
    schema description, plus supported camt.05x message types.
  - **Hover**: `hover_text` + `hover_markup` — schema description for the
    field under the cursor.
  - **Code actions**: `code_actions` — quick-fix "insert missing
    required fields" for records that fail validation.
  - **Document symbols**: `document_symbols` — outline view of every
    record + field for the editor's breadcrumb.
  - **Formatting**: `format_text` — full-document pretty-print.
- **JSONC tolerance**: `//` line comments and trailing commas stripped
  before parsing, so all of the above work on JSONC data files.
- **Editor wiring documentation**: `docs/quickstart.md` covers Neovim
  built-in LSP, VS Code generic LSP client, Helix/Emacs/generic
  stdio clients.
- **Supply chain**: 100% line + branch coverage, OpenSSF Scorecard,
  SLSA Build L3 + PEP 740 sigstore attestations on every release,
  CycloneDX 1.6 + SPDX 2.3 + pip-licenses SBOMs on every GitHub
  release, NIST SP 800-218 SSDF practice mapping in `SECURITY.md`.

## v0.0.8 — Q3 2026

Goal: YAML support, richer code-actions, OpenSSF Best Practices Silver.

- **YAML data file support** (mirrors the JSONC tolerance pattern):
  same 7 capabilities, just on YAML reversing-entry data files.
- **More code-actions**: "insert missing optional fields" (current
  action only inserts required), "convert single record to array",
  "infer message_type from filename".
- **Diagnostics for cross-record consistency**: warn when records in
  the same array reference different accounts, currencies, or
  message types that the user probably didn't intend.
- **OpenSSF Best Practices Silver** badge live.
- **Second maintainer** named (recruiting per
  [`MAINTAINERS.md`](MAINTAINERS.md)).

## v0.0.9 — Q4 2026

Goal: editor-first ergonomics.

- **`textDocument/rename`** for field names that get renamed in the
  schema (e.g. `account_servicer_bic` → `agent_bic`).
- **Inlay hints**: show resolved camt message type + schema version
  at the top of each record block.
- **Semantic tokens**: distinguish field names from values, valid
  identifiers from invalid ones.

## v0.1.0 — Q1 2027

Goal: first stable minor.

- **LSP helper API surface frozen**: any rename of the pure helpers
  is a minor-bump event.
- **OpenSSF Best Practices Gold**.

## Out of scope (until a contributor steps up)

- **Real-time XML editing**: the LSP targets JSON/JSONC/YAML data
  files (which become camt.053 XML via the core library). Direct
  XML editing in the editor is a different shape (XSD-driven
  diagnostics, namespace handling); a separate package would fit
  better.
- **Browser-based LSP**: the server is Python + stdio. A
  WebAssembly port (à la Pyodide-LSP) is on the wishlist but
  outside our v0.0.x scope.

## How to influence the roadmap

- Open an issue with the proposed capability + use case.
- For larger items, sketch a design in the issue body.
- See [`GOVERNANCE.md`](GOVERNANCE.md) for the decision-making
  process.
