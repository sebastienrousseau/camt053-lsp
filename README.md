<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

<p align="center">
  <img src="https://cloudcdn.pro/camt053/v1/logos/camt053.svg" alt="camt053-lsp logo" width="128" />
</p>

<h1 align="center">camt053-lsp</h1>

<p align="center">
  A Language Server that checks ISO 20022 reversing-entry records as you type them.
</p>

<p align="center">
  <a href="https://github.com/sebastienrousseau/camt053-lsp/actions"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/camt053-lsp/ci.yml?style=for-the-badge&logo=github" alt="Build" height="28" /></a>
  <a href="https://pypi.org/project/camt053-lsp/"><img src="https://img.shields.io/pypi/v/camt053-lsp?style=for-the-badge&color=fc8d62&logo=python" alt="Registry" height="28" /></a>
  <a href="https://sebastienrousseau.github.io/camt053/"><img src="https://img.shields.io/badge/docs-camt053-blue?style=for-the-badge&labelColor=555555&logo=readthedocs" alt="Docs" height="28" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/sebastienrousseau/camt053-lsp"><img src="https://img.shields.io/ossf-scorecard/github.com/sebastienrousseau/camt053-lsp?style=for-the-badge&label=OpenSSF%20Scorecard&logo=openssf" alt="OpenSSF Scorecard" height="28" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg?style=for-the-badge" alt="License: Apache-2.0 OR MIT" height="28" /></a>
  <a href="https://github.com/sebastienrousseau/camt053-lsp/blob/main/docs/POLICIES.md"><img src="https://img.shields.io/badge/Python-3.10%2B-93450a.svg?style=for-the-badge&logo=python" alt="Python 3.10 or newer" height="28" /></a>
  <a href="https://www.bestpractices.dev/projects/13375"><img src="https://img.shields.io/cii/level/13375?style=for-the-badge&label=OpenSSF%20Best%20Practices&logo=openssf" alt="OpenSSF Best Practices" height="28" /></a>
</p>

<p align="center">
  <img src=".github/demo.gif" alt="camt053-lsp demo: the command-line help, then the diagnostics and code-action helpers the server runs on every edit, against sample reversing-entry records" width="100%" />
</p>

---

## Contents

**Getting started**

- [Install](#install) — pip, pipx or uv, then editor wiring
- [Requirements](#requirements) — toolchain floor, platforms
- [Quick Start](#quick-start) — point your editor at `camt053-lsp`, or call the helpers directly

**The camt053-lsp ecosystem**

- [The camt053-lsp ecosystem](#the-camt053-lsp-ecosystem) — the camt053 core library and its five companion packages

**Library reference**

- [Capabilities at a glance](#capabilities-at-a-glance) — the current surface by theme
- [Ecosystem comparison](#ecosystem-comparison) — short matrix; full table at [`docs/COMPARISON.md`](docs/COMPARISON.md)
- [Benchmarks](#benchmarks) — headline numbers; full table at [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md)
- [Features](#features) — module-level capability list
- [Configuration](#configuration) — core options
- [Examples](#examples) — runnable example index

**Operational**

- [When not to use camt053-lsp](#when-not-to-use-camt053-lsp) — limitations
- [Development](#development) — make targets, fuzzing, CI
- [Security](#security) — guarantees and compliance
- [Documentation](#documentation) — all reference docs
- [Stability guarantees](#stability-guarantees) — SemVer axis, output stability, minimum toolchain discipline
- [License](#license)

---

## Install

### As a Python library

```sh
python -m pip install camt053-lsp
```

> **Latest release: v0.0.20**: the `camt053` suite aligned on one version
> number, with a scheduled drift check against PyPI. Schema and IBAN/BIC
> diagnostics, field and message-type completion, hover, code actions,
> document symbols and formatting, all backed by `camt053.services`.
> [See what's new →][release]

The package installs a `camt053-lsp` console command and pulls in the core
[`camt053`][camt053] library and [`pygls`][pygls]. To keep the command on
your `PATH` without touching a project environment:

```sh
pipx install camt053-lsp
uv tool install camt053-lsp
```

Check the install:

```sh
camt053-lsp --version
```

---

## Requirements

- Python 3.10 or newer, tested in CI on 3.10, 3.11, 3.12, 3.13 and 3.14 on
  Linux ([toolchain policy](docs/POLICIES.md)). The package is pure Python
  and runs wherever its dependencies do: macOS, Linux and Windows.
- `camt053` 0.0.20 or newer (below 1.0) and `pygls` 1.3 or newer, installed
  automatically.
- `anyio` 4.14.2 or newer: earlier releases are affected by
  GHSA-3w57-8xmc-8v26, GHSA-5p39-cfhj-2xmp and GHSA-82r6-8w77-94w6 and cannot
  resolve.
- An editor with a Language Server Protocol client (Neovim, VS Code, Helix,
  Emacs, Sublime Text LSP and others).

---

## Quick Start

```lua
-- Neovim 0.11+, built-in LSP client
vim.lsp.config["camt053"] = {
  cmd = { "camt053-lsp" },
  filetypes = { "json", "jsonc" },
  root_markers = { ".git" },
}
vim.lsp.enable("camt053")
```

Open a JSON (or JSONC) array of reversing-entry records. The server
validates every record on open and on each change, completes field names and
`camt` message types, shows schema descriptions on hover, offers a quick fix
that inserts missing required fields, and outlines the document by record.
`camt053-lsp` speaks LSP on stdin and stdout, so any editor that can spawn a
command over stdio can use it; [`docs/quickstart.md`](docs/quickstart.md)
covers VS Code, Helix and Emacs.

The same logic is importable, without an editor:

```python
import json

from camt053_lsp.server import code_actions, compute_diagnostics

doc = json.dumps([{"statement_msg_id": "RVSL-STMT-0001"}])
for diagnostic in compute_diagnostics(doc)[:2]:
    print(diagnostic["severity"], diagnostic["message"])
print(code_actions(doc)[0]["title"])
```

---

## The camt053-lsp ecosystem

`camt053-lsp` is one of six packages built around the [`camt053`][camt053]
library for ISO 20022 bank-to-customer statements. They release together at
one version, the core first, and every interface calls the same
`camt053.services` layer, so the editor, the command line, the REST API and
an AI agent all apply the same rules.

| Component | Purpose | Use case |
| :--- | :--- | :--- |
| [`camt053`](https://github.com/sebastienrousseau/camt053) | Core library, Click CLI and FastAPI REST API: parse, validate and reverse `camt.053` statements | You process statements in code, scripts or a service |
| [`camt053-lsp`](#install) | Language Server for the reversing-entry records that drive reversal generation | You author or review those records in an editor: **this package** |
| [`camt053-loader-mt940`](https://github.com/sebastienrousseau/camt053-loader-mt940) | SWIFT MT940 to `camt.053` loader | Your statements still arrive as MT940 |
| [`camt053-loader-mt942`](https://github.com/sebastienrousseau/camt053-loader-mt942) | SWIFT MT942 interim reports to `camt.052` | You need intraday reports in ISO 20022 form |
| [`camt053-writer-xlsx`](https://github.com/sebastienrousseau/camt053-writer-xlsx) | Excel `.xlsx` writer for parsed statements | Finance teams want a spreadsheet |
| [`camt053-mcp`](https://github.com/sebastienrousseau/camt053-mcp) | Model Context Protocol server exposing the library as agent tools | You work with statements from an AI assistant |

---

## Capabilities at a glance

| Area | Capability | Status |
| :--- | :--- | :--- |
| Diagnostics | Each record checked against the message type's input JSON Schema; IBAN and BIC fields checked with the core validators | Released |
| Diagnostics (XML) | CBPR+ November 2026 readiness issues on opened `camt.05x` XML, detected by content | Released |
| Completion | Every input field with its schema description, plus every supported `camt` message type | Released |
| Hover | Field descriptions, and the human-readable name of a `camt.05x` message type | Released |
| Code actions | Quick fix inserting a record's missing required fields | Released |
| Outline | One document symbol per record, one child per field | Released |
| Formatting | Whole-document pretty-print, 2-space indent, key order kept | Released |
| JSONC | `//` comments and trailing commas accepted by every feature | Released; linear time since 0.0.23 |
| YAML data files | Same features on YAML | Planned, see [`ROADMAP.md`](ROADMAP.md) |

---

## Ecosystem comparison

The alternatives to this server are a JSON Schema alone, in any schema-aware
editor, and running the `camt053` command line after saving.

| Project | Feedback while typing | IBAN check digits | Quick fix for missing fields |
| :--- | :---: | :---: | :---: |
| **camt053-lsp** | Yes | Yes | Yes |
| A JSON Schema alone | Yes | No | No |
| `camt053` CLI | No | Yes | No |

See [`docs/COMPARISON.md`](docs/COMPARISON.md) for the evidence and complete matrix.

---

## Benchmarks

Diagnostics run on every keystroke, so the number that matters is how large
a document stays interactive. Measured with `benches/bench_diagnostics.py`
for 0.0.18. Most of the cost is the core library re-checking its JSON Schema
for every record; see the benchmarks page for the profile.

| Scenario | Result | Environment |
| :--- | ---: | :--- |
| Diagnostics, cost per record | 0.86 ms | recorded for 0.0.18 (2026-08-29) |
| Interactive budget (under 100 ms per change) | ~116 records | recorded for 0.0.18 (2026-08-29) |
| JSONC stripping, 1.2 MB document | 3.2 s before 0.0.23, linear since | Apple A18 Pro, Python 3.12.15 |

See [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) for methodology and full results.

---

## Features

For reversing-entry data files: a JSON array of flat reversing-entry
records, or a single record object treated as one record.

- **Diagnostics**: schema validation reports missing required fields, wrong
  types, and pattern or length violations. `account_id`,
  `account_servicer_bic` and `counterparty_account` are also checked as IBAN
  or BIC. Malformed JSON gives one syntax diagnostic at the offending
  position. Opened `camt.05x` XML gets the CBPR+ November 2026 readiness
  checks instead.
- **Completion**: every input field for the message type, with its schema
  description as the detail, plus every supported `camt` message type.
- **Hover**: the schema `description` of the field under the cursor, or the
  name of a supported message type (`camt.053.001.14`: Bank To Customer
  Statement).
- **Code actions**: for each record missing required fields, a quick fix
  inserts the missing keys with empty placeholder values. Valid records and
  malformed JSON propose nothing.
- **Document symbols**: one symbol per record (`Record N`, with its
  `statement_msg_id` or `entry_ref` as the detail) and a child per field.
- **Formatting**: pretty-prints the document with a stable 2-space indent,
  keeping key order, as one full-document edit. Invalid JSON is left alone.
- **JSONC tolerance**: `//` line comments and trailing commas are removed
  before parsing (`camt053_lsp/_jsonc.py`). Clean JSON is unaffected.

The logic lives in pure helpers in `camt053_lsp.server`:
`compute_diagnostics`, `compute_xml_diagnostics`, `completion_items`,
`hover_text`, `hover_markup`, `message_type_name`, `code_actions`,
`document_symbols` and `format_text`. The LSP handlers map their plain dicts
to `lsprotocol` types. Each diagnostic is
`{"line": int, "character": int, "severity": "error" | "warning", "message": str}`.

---

## Configuration

| Flag | Description |
| --- | --- |
| `--version` | Print the package version and exit. |
| `--help` | Print usage and exit. |
| `--log-level {DEBUG,INFO,WARNING,ERROR}` | Logging verbosity (default `WARNING`). |

With no arguments the server speaks LSP over stdio. Logs go to stderr so
they never corrupt the transport on stdout; raise the level when an editor
integration misbehaves:

```sh
camt053-lsp --log-level DEBUG
```

The message type defaults to `camt.053.001.14` (Bank to Customer
Statement). The helpers take a `message_type` argument for the others.

---

## Examples

One runnable script per capability in [`examples/`](examples/README.md),
each run end to end by `tests/test_examples.py`:

| Example | Demonstrates |
| :--- | :--- |
| [`01_compute_diagnostics.py`](examples/01_compute_diagnostics.py) | Schema and IBAN/BIC diagnostics on JSON records |
| [`02_compute_xml_diagnostics.py`](examples/02_compute_xml_diagnostics.py) | CBPR+ readiness diagnostics on `camt.05x` XML |
| [`03_completion.py`](examples/03_completion.py) | Field and message-type completion |
| [`04_hover.py`](examples/04_hover.py) | Schema-description hover |
| [`05_code_actions.py`](examples/05_code_actions.py) | The missing-fields quick fix |
| [`06_document_symbols.py`](examples/06_document_symbols.py) | The per-record outline |
| [`07_formatting.py`](examples/07_formatting.py) | JSONC-tolerant formatting |
| [`lsp_helpers.py`](examples/lsp_helpers.py) | All of the above in one script |

```sh
git clone https://github.com/sebastienrousseau/camt053-lsp.git && cd camt053-lsp
poetry install
poetry run python examples/01_compute_diagnostics.py
```

---

## When not to use camt053-lsp

- **You have no LSP-capable editor.** Scripts and CI are better served by
  the `camt053` CLI and REST API.
- **You are authoring `camt.053` XML.** The CBPR+ diagnostics fire on opened
  XML, but completion and schema-aware hover target the reversing-entry
  JSON records, not XML.
- **You lint files outside an editor.** Use the CLI:
  `camt053 check-cbpr-readiness statement.xml` or `camt053 validate`.
- **Your documents run to thousands of records.** Diagnostics cost about
  0.86 ms per record (see [Benchmarks](#benchmarks)), so very large files lag
  on every change until the core validator is faster.
- **You generate `pain.001` payment files.** Use
  [`pain001-lsp`](https://github.com/sebastienrousseau/pain001-lsp).

---

## Development

```bash
git clone https://github.com/sebastienrousseau/camt053-lsp.git && cd camt053-lsp
poetry install
make check         # lint, mypy, bandit, complexity, tests, examples
make test          # pytest, 100% line and branch coverage enforced
make complexity    # per-function ceilings against complexity-baseline.json
make fuzz          # the Atheris harness, locally
make pip-compile   # regenerate the hash-pinned requirements/*.txt
make demo          # re-render .github/demo.gif with VHS
```

CI installs from hash-pinned `requirements/*.txt` (compiled from
`requirements/*.in` with `uv pip compile --generate-hashes`) and runs the
test matrix on Python 3.10 to 3.14, ruff, black, mypy in strict mode,
bandit, interrogate (100% docstrings), the complexity ceilings, the
version-source check, CodeQL, OpenSSF Scorecard and ClusterFuzzLite. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/RELEASING.md`](docs/RELEASING.md).

---

## Security

The server reads only the document text the editor sends over stdio. It
opens no network socket, executes nothing from the document, and parses
JSON with the standard library after a purely syntactic JSONC pass. XML goes
to `camt053.services`, which uses `defusedxml` with a byte cap and a
DOCTYPE and ENTITY pre-flight. The text entry points are fuzzed with
[Atheris][atheris] under ClusterFuzzLite on every pull request and on a
schedule (see [`fuzz/`](fuzz/)). Actions are pinned by SHA, `pip` installs
are hash-pinned, workflow tokens are least-privilege, and releases carry
SLSA provenance, PEP 740 attestations and cosign signatures. The project
holds the [OpenSSF Best Practices][bestpractices] badge.

Report vulnerabilities according to [`SECURITY.md`](SECURITY.md).

---

## Documentation

[User manual](https://sebastienrousseau.github.io/camt053/) ·
[API reference: the helpers](#features) ·
[Developer guide](CONTRIBUTING.md) ·
[Family map](#the-camt053-lsp-ecosystem) ·
[Quickstart](docs/quickstart.md) · [Releasing](docs/RELEASING.md) ·
[Changelog](CHANGELOG.md) · [Roadmap](ROADMAP.md) ·
[Security policy](SECURITY.md) · [Support](SUPPORT.md)

---

## Stability guarantees

The project is pre-1.0 and versions advance in `0.0.1` steps, in lockstep
with the rest of the camt053 suite. The breaking axis is what an editor
receives: the capabilities the server advertises, and the diagnostics,
completion items, code actions, symbols and edits it returns, including the
plain-dict shapes of the public helpers. A change to what the server
reports for the same document is breaking even when no Python signature
moves, and is called out in the [changelog](CHANGELOG.md). The Python floor
moves only as described in the [toolchain policy](docs/POLICIES.md).

---

## License

This project is dual-licensed under either:

* Apache License, Version 2.0 ([`LICENSE-APACHE`](LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
* MIT License ([`LICENSE-MIT`](LICENSE-MIT) or <https://opensource.org/licenses/MIT>)

at your option. Any contribution submitted for inclusion is licensed the same
way, without additional terms. Dependencies keep their own licences.

[atheris]: https://github.com/google/atheris
[bestpractices]: https://www.bestpractices.dev/projects/13375
[camt053]: https://github.com/sebastienrousseau/camt053
[pygls]: https://github.com/openlawlibrary/pygls
[release]: https://github.com/sebastienrousseau/camt053-lsp/releases/tag/v0.0.20
