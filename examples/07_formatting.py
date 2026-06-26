#!/usr/bin/env python3
# Copyright (C) 2023-2026 Sebastien Rousseau.
# SPDX-License-Identifier: Apache-2.0

"""Example: ``format_text`` (full-document pretty-print).

The LSP returns a single full-document edit that pretty-prints the
data with a stable 2-space indent, preserving key order. Invalid
JSON is left unchanged (``None``).

Usage::

    python examples/07_formatting.py
"""

from camt053_lsp.server import format_text

MINIFIED = (
    '[{"statement_msg_id":"RVSL","amount":"10","currency":"EUR",'
    '"credit_debit":"DBIT"}]'
)
INVALID = "{nope, not json"


def main() -> None:
    formatted = format_text(MINIFIED)
    print("formatted output:")
    print(formatted or "(none)")
    print()
    print(f"invalid input    : {format_text(INVALID)!r} (unchanged)")


if __name__ == "__main__":
    main()
