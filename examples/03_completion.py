#!/usr/bin/env python3
"""Example: ``completion_items``.

Editor completion proposals: every input field for the message type
(with its schema description as the detail) plus every supported
camt.05x message type.

Usage::

    python examples/03_completion.py
"""

from camt053_lsp.server import completion_items


def main() -> None:
    items = completion_items()
    print(f"completion items: {len(items)}")
    for i in items[:8]:
        label = i.get("label", "?")
        detail = (i.get("detail") or "")[:60]
        print(f"  {label:<24}  {detail}")
    if len(items) > 8:
        print(f"  ... and {len(items) - 8} more")


if __name__ == "__main__":
    main()
