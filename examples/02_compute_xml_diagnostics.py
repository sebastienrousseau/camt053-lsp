#!/usr/bin/env python3
"""Example: ``compute_xml_diagnostics``.

When a user opens a camt.053 XML file in their editor, the LSP also
runs lightweight XML well-formedness checks so syntax errors surface
inline. The pure helper takes raw text and returns a list of diagnostic
dicts.

Usage::

    python examples/02_compute_xml_diagnostics.py
"""

from camt053_lsp.server import compute_xml_diagnostics

WELL_FORMED = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.14">
  <BkToCstmrStmt>
    <GrpHdr><MsgId>STMT</MsgId></GrpHdr>
  </BkToCstmrStmt>
</Document>"""

BROKEN_OPEN = "<Document><BkToCstmrStmt><GrpHdr>"  # never closed
BROKEN_AMP = "<Doc>tom & jerry</Doc>"              # unescaped ampersand


def main() -> None:
    for label, xml in (
        ("well-formed", WELL_FORMED),
        ("never-closed", BROKEN_OPEN),
        ("unescaped-amp", BROKEN_AMP),
    ):
        diags = compute_xml_diagnostics(xml)
        print(f"{label:<14}: {len(diags)} diagnostic(s)")
        for d in diags[:2]:
            print(f"               -> {d.get('message')}")


if __name__ == "__main__":
    main()
