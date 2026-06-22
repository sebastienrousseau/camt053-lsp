# Quickstart

A 10-minute install → editor wiring → first reversing-entry edit
tutorial for `camt053-lsp`.

## 1. Install

`camt053-lsp` runs on macOS, Linux, and Windows and requires Python
3.10+. It pulls in the core `camt053` library and `pygls`
automatically.

```sh
python -m pip install camt053-lsp
```

Verify:

```sh
python -c "import camt053_lsp; print(camt053_lsp.__version__)"
```

## 2. Confirm the server starts

```sh
camt053-lsp
```

Nothing visible happens — the command speaks LSP on stdin/stdout. Press
Ctrl-C to exit. It is meant to be launched by your editor, not used
interactively.

## 3. Wire it up

### Neovim (built-in `vim.lsp.config`)

Add to your config:

```lua
vim.lsp.config["camt053"] = {
  cmd = { "camt053-lsp" },
  filetypes = { "json" },
  root_markers = { ".git" },
}
vim.lsp.enable("camt053")
```

### VS Code

Use a generic LSP client extension (e.g. *LSP Sample*) and point its
`serverOptions` at `{ command: "camt053-lsp", transport:
TransportKind.stdio }`. Filetype: `json`.

### Helix / Emacs / others

Anything that speaks LSP over stdio works. Configure the language
server `command` as `camt053-lsp`, filetype `json`.

## 4. Open a reversing-entry data file

Create `reversal.json`:

```json
[
  {
    "statement_msg_id": "RVSL-STMT-0001"
  }
]
```

As soon as the editor opens this file the LSP reports diagnostics for
the missing required fields. Trigger the `Insert missing required
fields` code action and the LSP rewrites the record with every
required key present (empty values you then fill in). Tab through the
new fields; completion proposes each field's name plus every
supported `camt.05x` message type, and hover shows the schema
description for the field under the cursor.

## 5. Use the helpers in-process (no editor needed)

To prototype or write integration tests, call the LSP feature logic
directly. Every example in `examples/` follows this pattern. The
shortest one:

```python
import json

from camt053_lsp.server import compute_diagnostics

doc = json.dumps([{"statement_msg_id": "ONLY-ID"}])
print(compute_diagnostics(doc))  # list of diagnostic dicts
```

A focused example exists for every public capability —
`examples/01_compute_diagnostics.py` through
`examples/07_formatting.py`.

## 6. Next steps

- Browse the full [feature list](../README.md#features) (diagnostics,
  completion, hover, code actions, document symbols, formatting,
  JSONC tolerance).
- Read the suite's deeper docs at
  <https://sebastienrousseau.github.io/camt053/>.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `command not found: camt053-lsp` | Install went to a venv not on PATH | Re-install in your active env, or invoke `python -m camt053_lsp.server` |
| Editor doesn't show diagnostics | LSP client not configured for `json` filetype on this file | Check the filetype mapping in your client config; LSP only attaches to `json` |
| No completion for fields | Cursor is on a value, not a key | Position the cursor on a key (or where a key would go) and trigger completion manually |
