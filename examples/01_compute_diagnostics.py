#!/usr/bin/env python3
# Copyright (C) 2023-2026 Sebastien Rousseau.
# SPDX-License-Identifier: Apache-2.0

"""Example: ``compute_diagnostics`` (JSON reversing-entry data files).

Validates an array of reversing-entry records: schema (required fields,
types, patterns) plus dedicated IBAN / BIC checks for identifier
fields. Shows valid, missing-fields, bad-BIC, and malformed-JSON cases.

Usage::

    python examples/01_compute_diagnostics.py
"""

import json
from pathlib import Path

from camt053_lsp.server import compute_diagnostics


def main() -> None:
    valid_doc = (Path(__file__).parent / "_data" / "sample_records.json").read_text()
    print(f"valid       : {len(compute_diagnostics(valid_doc))} diagnostic(s)")

    missing = json.dumps([{"statement_msg_id": "ONLY-ID"}])
    print(f"missing     : {len(compute_diagnostics(missing))} diagnostic(s)")

    bad_bic = json.dumps([{"account_servicer_bic": "INVALID"}])
    print(f"bad-bic     : {len(compute_diagnostics(bad_bic))} diagnostic(s)")
    if (d := compute_diagnostics(bad_bic)):
        print(f"              first: {d[0].get('message')}")

    print(f"malformed   : {len(compute_diagnostics('{not json'))} diagnostic(s)")


if __name__ == "__main__":
    main()
