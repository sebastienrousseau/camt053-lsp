#!/usr/bin/env python3
"""Example: the LSP server's editor-feature helpers.

Usage:
    pip install camt053-lsp     # requires Python 3.10+
    python examples/lsp_helpers.py

The camt053 language server (launched as `camt053-lsp` over stdio) powers
editor features for reversing-entry data JSON files. Its logic lives in pure
helpers that you can call directly — exactly what the server runs on each edit.
"""

import json

from camt053_lsp.server import (
    code_actions,
    completion_items,
    compute_diagnostics,
    hover_markup,
    hover_text,
)

# --- Diagnostics: a valid record vs. common mistakes ------------------------
valid_doc = json.dumps(
    [
        {
            "statement_msg_id": "RVSL-STMT-0001",
            "creation_date_time": "2026-06-15T08:00:00",
            "statement_id": "RVSL-STMT-0001",
            "account_id": "GB29NWBK60161331926819",
            "account_currency": "EUR",
            "account_servicer_bic": "NWBKGB2LXXX",
            "amount": "1500.00",
            "currency": "EUR",
            "credit_debit": "DBIT",
            "reason_code": "AC04",
            "counterparty_account": "DE89370400440532013000",
        }
    ]
)
print("valid document diagnostics:", compute_diagnostics(valid_doc))

missing = json.dumps([{"statement_msg_id": "ONLY-ID"}])
print(
    "missing-fields diagnostics:",
    len(compute_diagnostics(missing)),
    "issue(s)",
)

bad_bic = json.dumps([{"account_servicer_bic": "INVALID"}])
print("bad-BIC diagnostics:       ", compute_diagnostics(bad_bic)[:1])

print("malformed JSON diagnostics:", compute_diagnostics("{not json"))

# --- Completion and hover ----------------------------------------------------
items = completion_items()
print(f"completion items:          {len(items)} (e.g. {items[0]['label']})")
print("hover account_servicer_bic:", hover_text("account_servicer_bic"))
print("hover unknown field:       ", hover_text("nope"))
print("hover message type:        ", hover_markup("camt.053.001.14"))

# --- Code actions: insert a record's missing required fields ----------------
fixes = code_actions(missing)
print("code action title:         ", fixes[0]["title"] if fixes else None)
print("code actions (valid doc):  ", code_actions(valid_doc))
