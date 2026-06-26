#!/usr/bin/env python3
# Copyright (C) 2023-2026 Sebastien Rousseau.
# SPDX-License-Identifier: Apache-2.0

"""Example: ``document_symbols`` (outline view).

The LSP returns one symbol per reversing-entry record, with a child
symbol for every field, so editors can render an outline / breadcrumb
view of the data file.

Usage::

    python examples/06_document_symbols.py
"""

from pathlib import Path

from camt053_lsp.server import document_symbols


def main() -> None:
    text = (Path(__file__).parent / "_data" / "sample_records.json").read_text()
    symbols = document_symbols(text)
    print(f"top-level symbols: {len(symbols)}")
    for s in symbols:
        children = s.get("children", [])
        print(
            f"  {s.get('name'):<14} ({s.get('detail', '-')})  "
            f"{len(children)} field(s)"
        )

    # Malformed JSON yields an empty outline (graceful degradation):
    print(f"malformed input  : {len(document_symbols('{nope'))} symbols")


if __name__ == "__main__":
    main()
