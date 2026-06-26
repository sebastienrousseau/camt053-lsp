#!/usr/bin/env python3
# Copyright (C) 2023-2026 Sebastien Rousseau.
# SPDX-License-Identifier: Apache-2.0

"""Example: ``hover_text`` and ``hover_markup``.

When the cursor lands on a field name, the LSP returns the field's
schema description. When it lands on a `camt.05x` message-type
literal, it returns the human-readable name.

Usage::

    python examples/04_hover.py
"""

from camt053_lsp.server import hover_markup, hover_text


def main() -> None:
    cases = [
        "account_servicer_bic",  # known field with description
        "amount",
        "nope",                  # unknown token
    ]
    for token in cases:
        text = hover_text(token)
        print(f"  hover field   {token:<22} -> {text or '(no hover)'}")

    for token in ("camt.053.001.14", "camt.052.001.14", "camt.999.999.99"):
        markup = hover_markup(token)
        print(f"  hover msgtype {token:<22} -> {markup or '(no hover)'}")


if __name__ == "__main__":
    main()
