<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# `camt053-lsp` style guide

`camt053-lsp` follows the cross-suite
[`STYLEGUIDE.md`](https://github.com/sebastienrousseau/camt053/blob/main/STYLEGUIDE.md)
maintained in the core repository. That document is the single source of
truth for:

- Voice + spelling conventions (British prose, American code, no
  em-dashes, no emojis outside standard checkmark/cross in
  supported-versions tables).
- README structure (18-section template + badge order).
- CHANGELOG structure (Keep-a-Changelog + suite Quality gates + Suite
  alignment tables).
- SECURITY.md structure (6-section template including the NIST SSDF
  practice mapping).
- SUPPORT.md / CONTRIBUTING.md structure.
- CI floor (8 gates + release-only gates).
- PR style (conventional commits + signed commits + branch policy).
- Branch naming, issue filing, naming conventions.

## Local additions

`camt053-lsp` adds one local convention: **pure-helper functions back
every LSP capability**. The handler decorated with `@lsp_server.feature`
is glue; the real work lives in a separate importable helper:

```python
# server.py
def compute_diagnostics(text: str, *, message_type: str = "camt.053.001.14") -> list[dict]:
    """Pure helper — no LSP types, no `LanguageServer` argument."""
    ...

@lsp_server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: lsp.DidOpenTextDocumentParams) -> None:
    diags = compute_diagnostics(params.text_document.text)
    # ... convert to lsp.Diagnostic objects and publish
```

The pure helpers are what the tests target — no need to spin up a
`LanguageServer` instance in test code. Editor consumers that don't run
the LSP can also call the helpers directly.

## Updating

If you find divergence between this repo's practice and the core
STYLEGUIDE, the core wins; open a PR to align this repo (and/or fix
the deviation).
