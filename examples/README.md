# camt053-lsp examples

Runnable, self-contained examples for the **camt053-lsp** language server. Run
any of them from the repository root:

```sh
python examples/<name>.py
```

There is one runnable script per LSP capability, covering every feature the
server exposes:

| Example | Capability | Demonstrates |
|---------|------------|--------------|
| [`01_compute_diagnostics.py`](01_compute_diagnostics.py) | Diagnostics (JSON) | `compute_diagnostics` — schema + IBAN/BIC validation of reversing-entry JSON |
| [`02_compute_xml_diagnostics.py`](02_compute_xml_diagnostics.py) | Diagnostics (XML) | `compute_xml_diagnostics` — CBPR+ Nov 2026 readiness checks for `camt.05x` XML |
| [`03_completion.py`](03_completion.py) | Completion | `completion_items` — field and message-type completion |
| [`04_hover.py`](04_hover.py) | Hover | `hover_text` / `hover_markup` — schema-description hover |
| [`05_code_actions.py`](05_code_actions.py) | Code actions | `code_actions` — quick-fixes inserting missing required fields |
| [`06_document_symbols.py`](06_document_symbols.py) | Document symbols | `document_symbols` — per-record outline view |
| [`07_formatting.py`](07_formatting.py) | Formatting | `format_text` — full-document pretty-print (JSONC-tolerant) |
| [`lsp_helpers.py`](lsp_helpers.py) | Umbrella | The diagnostics / completion / hover helpers in one script |

These helpers are exactly what the `camt053-lsp` server runs on each edit, so
you can call them directly to see the diagnostics, completion items, hover text,
code actions, symbols, and formatting an editor would receive. Every script is
executed end-to-end by the test suite (`tests/test_examples.py`), so the
examples stay in lockstep with the code.

Both `camt053-lsp` and its core dependency `camt053` must be installed
(Python 3.10+):

```sh
pip install camt053-lsp
```
