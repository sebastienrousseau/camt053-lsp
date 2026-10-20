<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Scope comparison

The comparison that matters for this server is with the two things it
replaces when someone edits reversing-entry records: a JSON Schema alone
(in any schema-aware editor), and running the `camt053` command line after
saving. No competitor ranking or comparative performance claim is made.

| Capability | **camt053-lsp** | A JSON Schema alone | `camt053` CLI |
| :--- | :---: | :---: | :---: |
| Feedback while typing | Yes | Yes | No, on each run |
| Required fields, types, patterns, lengths | Yes | Yes | Yes |
| IBAN check digits and BIC structure | Yes | No | Yes (`validate-id`) |
| Same rules as the CLI, REST API and MCP server | Yes | No | Yes |
| Quick fix that inserts missing required fields | Yes | No | No |
| `//` comments and trailing commas (JSONC) | Yes | Depends on the editor | No |
| CBPR+ November 2026 checks on `camt.05x` XML | Yes | No | Yes (`check-cbpr-readiness`) |

Why the middle column says no: JSON Schema can require a field and match a
pattern, but it has no keyword that computes the ISO 13616 mod-97 check
digits of an IBAN, so a structurally plausible IBAN with wrong check digits
passes. This server sends identifier fields (`account_id`,
`account_servicer_bic`, `counterparty_account`) through
`camt053.services.validate_identifier`, the validator the CLI uses.

Every row for camt053-lsp is exercised by the test suite
(`tests/test_lsp_server.py`) and by the runnable scripts in
[`examples/`](../examples/README.md).
