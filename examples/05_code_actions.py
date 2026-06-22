#!/usr/bin/env python3
"""Example: ``code_actions``.

Returns quick-fix actions for the records in a document. The standard
fix inserts a record's missing required keys with empty placeholder
values, so the operator just fills them in.

Usage::

    python examples/05_code_actions.py
"""

import json

from camt053_lsp.server import code_actions

VALID = json.dumps(
    [
        {
            "statement_msg_id": "RVSL",
            "creation_date_time": "2026-06-15T08:00:00",
            "statement_id": "RVSL",
            "account_id": "GB29NWBK60161331926819",
            "account_currency": "EUR",
            "account_servicer_bic": "NWBKGB2LXXX",
            "amount": "10",
            "currency": "EUR",
            "credit_debit": "DBIT",
            "reason_code": "AC04",
            "counterparty_account": "DE89370400440532013000",
        }
    ]
)
MISSING = json.dumps([{"statement_msg_id": "ONLY-ID"}])


def main() -> None:
    print(f"valid record    : {len(code_actions(VALID))} action(s) proposed")

    fixes = code_actions(MISSING)
    print(f"missing-fields  : {len(fixes)} action(s) proposed")
    for f in fixes:
        print(f"  -> {f.get('title')}")


if __name__ == "__main__":
    main()
