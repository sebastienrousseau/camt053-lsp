# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Language Server Protocol (LSP) server for Camt053 reversing-entry files.

This server helps developers author **camt053 reversing-entry data JSON
files** - a JSON array of flat reversing-entry record objects (the same records
that drive reversal XML generation). It provides three editor features, all
backed by :mod:`camt053.services` so they behave identically to the CLI, REST
API, and MCP server:

* **Diagnostics** - each record is validated against a message type's input
  JSON Schema, and any ``account_id`` / ``account_servicer_bic`` /
  ``counterparty_account`` values are additionally checked with the dedicated
  IBAN / BIC validators.
* **Completion** - every input field (with its description) plus the list of
  supported message types are offered as completion items.
* **Hover** - hovering a field name shows its schema description; hovering a
  supported ``camt.05x`` message type shows its human-readable name.
* **Code actions** - for each record missing required fields, a quick-fix
  inserts the missing keys (with placeholder values) into that record.
* **Document symbols (outline)** - one symbol per record (with its
  ``statement_msg_id`` / ``entry_ref`` as detail) and a child symbol per field.
* **Formatting** - pretty-prints the document with a stable 2-space indent
  while preserving key order.

Parsing is tolerant of JSONC: ``//`` line comments and trailing commas are
stripped before the document is handed to the standard-library JSON parser, so
all features work on JSONC data files while clean JSON behaves exactly as
before. (YAML data files are noted as a future enhancement and are not yet
supported.)

The intended message type defaults to ``camt.053.001.14`` (Bank to Customer
Statement); the pure helpers accept a ``message_type`` argument so a different
type can be configured.

Launching
---------
The package installs a ``camt053-lsp`` console entry point (declared in
``pyproject.toml`` as ``camt053.lsp.server:main``) which starts the server over
stdio::

    camt053-lsp

Editor wiring
-------------
Point your editor's LSP client at the ``camt053-lsp`` command for JSON files.
For Neovim (``nvim-lspconfig`` / the built-in ``vim.lsp.config`` API) register a
server whose ``cmd`` is ``{ "camt053-lsp" }`` and ``filetypes`` includes
``"json"``. VS Code clients spawn the same command over stdio.

The business logic lives in pure, testable helper functions
(:func:`compute_diagnostics`, :func:`completion_items`, :func:`hover_text`,
:func:`hover_markup`, :func:`message_type_name`, :func:`code_actions`,
:func:`document_symbols`, :func:`format_text`); the LSP handlers below are thin
glue that map those plain dicts to ``lsprotocol`` types.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from camt053 import services
from camt053.exceptions import Camt053Error
from lsprotocol import types as lsp
from pygls.lsp.server import LanguageServer

from . import __version__

DEFAULT_MESSAGE_TYPE = "camt.053.001.14"

# Flat-record fields whose values are financial identifiers, mapped to the
# identifier kind understood by ``services.validate_identifier``.
_IDENTIFIER_FIELDS = {
    "account_id": "iban",
    "account_servicer_bic": "bic",
    "counterparty_account": "iban",
}


# ---------------------------------------------------------------------------
# Pure helpers (no LSP/server I/O - directly unit-testable)
# ---------------------------------------------------------------------------
def _strip_jsonc(text: str) -> str:
    """Strip JSONC sugar (``//`` line comments, trailing commas) to plain JSON.

    A dependency-free pre-step so JSONC data files parse with the standard
    library. ``//`` only starts a comment outside of strings; ``"`` quoting and
    backslash escapes are tracked so comment markers and commas inside string
    values are preserved. Clean JSON is returned unchanged in substance (only
    superfluous trailing commas / comments are removed).

    Args:
        text: The raw (possibly JSONC) document text.

    Returns:
        The text with line comments removed and trailing commas dropped.
    """
    out: list[str] = []
    in_string = False
    escaped = False
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < length and text[i + 1] == "/":
            # Skip to (but keep) the end-of-line.
            while i < length and text[i] != "\n":
                i += 1
            continue
        out.append(ch)
        i += 1

    stripped = "".join(out)
    # Drop trailing commas that immediately precede a closing ``}`` or ``]``
    # (optionally separated by whitespace), again only outside of strings.
    result: list[str] = []
    in_string = False
    escaped = False
    for idx, ch in enumerate(stripped):
        if in_string:
            result.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            result.append(ch)
            continue
        if ch == ",":
            rest = stripped[idx + 1 :]
            if rest.lstrip()[:1] in ("}", "]"):
                continue
        result.append(ch)
    return "".join(result)


def _loads_tolerant(text: str) -> Any:
    """Parse ``text`` as JSON, tolerating JSONC comments and trailing commas.

    Clean JSON parses identically to :func:`json.loads`; JSONC sugar is removed
    by :func:`_strip_jsonc` first. Raises :class:`json.JSONDecodeError` for input
    that is still not valid JSON.
    """
    return json.loads(_strip_jsonc(text))


def _normalise_records(parsed: Any) -> list[dict[str, Any]]:
    """Coerce parsed JSON into a list of record dicts.

    A single dict is treated as one record; a list is returned as-is.
    """
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return parsed
    return []


def _record_line_offsets(text: str) -> list[int]:
    """Best-effort mapping of record index -> line number.

    Uses the position of each top-level ``{`` opening brace. This is a heuristic
    (stdlib ``json`` does not expose offsets), but it lets diagnostics point at
    roughly the right record. Falls back to line 0 when a record cannot be
    located.
    """
    offsets: list[int] = []
    depth = 0
    in_string = False
    escaped = False
    line = 0
    for ch in text:
        if escaped:
            escaped = False
        elif ch == "\\" and in_string:
            escaped = True
        elif ch == '"':
            in_string = not in_string
        elif not in_string:
            if ch == "\n":
                line += 1
                continue
            if ch == "{":
                if depth == 0:
                    offsets.append(line)
                depth += 1
            elif ch == "}":
                depth = max(0, depth - 1)
        if ch == "\n":
            line += 1
    return offsets


def compute_diagnostics(
    text: str, message_type: str = DEFAULT_MESSAGE_TYPE
) -> list[dict]:
    """Compute diagnostics for a camt053 reversing-entry JSON document.

    Parses ``text`` as JSON (a list of record dicts, or a single dict treated as
    one record). On a JSON syntax error, returns a single diagnostic at line 0.
    For valid JSON, runs schema validation via
    :func:`camt053.services.validate_records` and additionally checks any present
    identifier fields with :func:`camt053.services.validate_identifier`.

    Args:
        text: The raw document text.
        message_type: The camt message type to validate against.

    Returns:
        A list of plain dicts::

            {"line": int, "character": int,
             "severity": "error" | "warning", "message": str}
    """
    try:
        parsed = _loads_tolerant(text)
    except json.JSONDecodeError as exc:
        return [
            {
                "line": max(0, exc.lineno - 1),
                "character": max(0, exc.colno - 1),
                "severity": "error",
                "message": f"Invalid JSON: {exc.msg}",
            }
        ]

    records = _normalise_records(parsed)
    if not records:
        return [
            {
                "line": 0,
                "character": 0,
                "severity": "error",
                "message": (
                    "Expected a JSON array of record objects "
                    "(or a single record object)."
                ),
            }
        ]

    line_offsets = _record_line_offsets(text)

    def line_for(row: int) -> int:
        """Return the source line for a record index, or 0 if unknown."""
        if 0 <= row < len(line_offsets):
            return line_offsets[row]
        return 0

    diagnostics: list[dict] = []

    # Schema validation (required fields, types, patterns, lengths, ...).
    report = services.validate_records(message_type, records)
    for err in report["errors"]:
        row = err.get("row", 0)
        path = err.get("path") or ""
        prefix = f"{path}: " if path else ""
        diagnostics.append(
            {
                "line": line_for(row),
                "character": 0,
                "severity": "error",
                "message": f"{prefix}{err['message']}",
            }
        )

    # Identifier validation (IBAN / BIC) for any present values.
    for row, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        for field, kind in _IDENTIFIER_FIELDS.items():
            value = record.get(field)
            if not value or not isinstance(value, str):
                continue
            if not services.validate_identifier(kind, value)["valid"]:
                diagnostics.append(
                    {
                        "line": line_for(row),
                        "character": 0,
                        "severity": "warning",
                        "message": (
                            f"{field}: {value!r} is not a valid "
                            f"{kind.upper()}."
                        ),
                    }
                )

    return diagnostics


def _looks_like_xml(text: str) -> bool:
    """Return ``True`` if ``text`` looks like an XML document.

    Used to dispatch between the JSON reversing-entry diagnostics and the
    XML CBPR+ readiness diagnostics. Tolerates leading whitespace / BOM and
    accepts either an XML declaration or a bare root element.
    """
    stripped = text.lstrip("﻿").lstrip()
    return stripped.startswith("<?xml") or stripped.startswith("<")


def compute_xml_diagnostics(text: str) -> list[dict]:
    """Compute CBPR+ Nov 2026 diagnostics for a camt.05x XML document.

    Wraps :func:`camt053.services.check_cbpr_readiness`. Each issue from
    the readiness report becomes one diagnostic. Positions are pinned to
    line 0 today (XPath-style location is included in the message so the
    user can navigate); precise line/column mapping requires an
    ``lxml.sourceline``-aware re-parse and is tracked separately.

    A payload that is not parseable XML (malformed, wrong namespace, or
    refused by ``camt053.security.xml_guard``) yields a single
    error-severity diagnostic at line 0.

    Args:
        text: The raw XML document text.

    Returns:
        A list of plain dicts with the same shape as the JSON-record
        diagnostics: ``{"line", "character", "severity", "message"}``.
    """
    try:
        report = services.check_cbpr_readiness(text)
    except (ValueError, Camt053Error) as exc:
        return [
            {
                "line": 0,
                "character": 0,
                "severity": "error",
                "message": f"CBPR+ check failed: {exc}",
            }
        ]
    diagnostics: list[dict] = []
    for issue in report["issues"]:
        diagnostics.append(
            {
                "line": 0,
                "character": 0,
                "severity": issue["severity"],
                "message": (
                    f"{issue['code']} at {issue['path']}: "
                    f"{issue['message']}"
                ),
            }
        )
    return diagnostics


def completion_items(
    message_type: str = DEFAULT_MESSAGE_TYPE,
) -> list[dict]:
    """Return completion items for a camt053 reversing-entry document.

    Offers every input field for ``message_type`` (with its schema description as
    the detail) plus every supported message type.

    Args:
        message_type: The camt message type whose fields are offered.

    Returns:
        A list of ``{"label": str, "detail": str, "kind": "field"}`` dicts.
    """
    items: list[dict] = []
    properties = services.get_input_schema(message_type).get("properties", {})
    for field, spec in properties.items():
        items.append(
            {
                "label": field,
                "detail": (spec or {}).get("description", "") or "",
                "kind": "field",
            }
        )
    for entry in services.list_message_types():
        items.append(
            {
                "label": entry["message_type"],
                "detail": entry["name"],
                "kind": "field",
            }
        )
    return items


def hover_text(
    field: str, message_type: str = DEFAULT_MESSAGE_TYPE
) -> str | None:
    """Return the schema description for ``field``, or ``None``.

    Args:
        field: An input field name.
        message_type: The camt message type whose schema is consulted.

    Returns:
        The field's ``description`` string, or ``None`` if the field is unknown
        or has no description.
    """
    properties = services.get_input_schema(message_type).get("properties", {})
    spec = properties.get(field)
    if not spec:
        return None
    description = spec.get("description")
    return description or None


def message_type_name(token: str) -> str | None:
    """Return the human-readable name for a supported message type token.

    Args:
        token: A candidate ``camt.05x`` message-type string.

    Returns:
        The message type's name (e.g. ``"Bank To Customer Statement"``) when
        ``token`` is a supported message type, otherwise ``None``.
    """
    for entry in services.list_message_types():
        if entry["message_type"] == token:
            return str(entry["name"])
    return None


def hover_markup(
    token: str, message_type: str = DEFAULT_MESSAGE_TYPE
) -> str | None:
    """Return hover text for ``token`` (a field name or a message type).

    A supported ``camt.05x`` message-type token resolves to a
    ``"<type> — <name>"`` string; otherwise the token is treated as a field name
    and its schema description is returned (see :func:`hover_text`). Unknown
    tokens return ``None``.

    Args:
        token: The word under the cursor.
        message_type: The camt message type whose field schema is consulted.

    Returns:
        The hover markup string, or ``None`` if the token is neither a known
        message type nor a described field.
    """
    name = message_type_name(token)
    if name is not None:
        return f"{token} — {name}"
    return hover_text(token, message_type)


def code_actions(
    text: str, message_type: str = DEFAULT_MESSAGE_TYPE
) -> list[dict]:
    """Propose quick-fix actions inserting missing required fields.

    For each record missing one or more fields from
    :func:`camt053.services.get_required_fields`, a quick-fix action is proposed
    whose edit inserts the missing keys (with empty-string placeholder values)
    into that record object. The insertion point and indentation are derived
    from the record's opening-brace line via the :func:`_record_line_offsets`
    heuristic. Valid records yield no action; malformed JSON (or input that is
    not a list/dict of records) yields an empty list.

    Args:
        text: The raw (possibly JSONC) document text.
        message_type: The camt message type whose required fields are used.

    Returns:
        A list of plain dicts::

            {"title": str, "fields": list[str], "line": int,
             "character": int, "new_text": str}

        where ``line`` / ``character`` is the insertion position (just after the
        record's opening ``{``) and ``new_text`` is the text to insert.
    """
    try:
        parsed = _loads_tolerant(text)
    except json.JSONDecodeError:
        return []

    records = _normalise_records(parsed)
    if not records:
        return []

    required = services.get_required_fields(message_type)
    line_offsets = _record_line_offsets(text)
    lines = text.splitlines()

    actions: list[dict] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        missing = [field for field in required if field not in record]
        if not missing:
            continue
        line = line_offsets[index] if index < len(line_offsets) else 0
        source_line = lines[line] if 0 <= line < len(lines) else ""
        brace = source_line.find("{")
        character = brace + 1 if brace >= 0 else len(source_line)
        indent = " " * (brace + 2) if brace >= 0 else "  "
        insert = "".join(f'\n{indent}"{field}": "",' for field in missing)
        actions.append(
            {
                "title": "Insert missing required field(s): "
                + ", ".join(missing),
                "fields": missing,
                "line": line,
                "character": character,
                "new_text": insert,
            }
        )
    return actions


def document_symbols(text: str) -> list[dict]:
    """Return an outline of the document: one symbol per record.

    Each record becomes a parent symbol named ``"Record N"`` (1-indexed) whose
    detail is the record's ``statement_msg_id`` (falling back to ``entry_ref``)
    when present. Every field of a record becomes a child symbol named after the
    field, with its value rendered as the detail. Line numbers reuse the
    :func:`_record_line_offsets` brace-tracking heuristic; field lines fall back
    to their record's line.

    Malformed JSON (or input that is not a list/dict of records) yields an empty
    outline rather than raising.

    Args:
        text: The raw (possibly JSONC) document text.

    Returns:
        A list of plain dicts::

            {"name": str, "detail": str, "kind": "record" | "field",
             "line": int, "children": list[dict]}
    """
    try:
        parsed = _loads_tolerant(text)
    except json.JSONDecodeError:
        return []

    records = _normalise_records(parsed)
    line_offsets = _record_line_offsets(text)

    symbols: list[dict] = []
    for index, record in enumerate(records):
        line = line_offsets[index] if index < len(line_offsets) else 0
        detail = ""
        children: list[dict] = []
        if isinstance(record, dict):
            detail = str(
                record.get("statement_msg_id") or record.get("entry_ref") or ""
            )
            for field, value in record.items():
                children.append(
                    {
                        "name": str(field),
                        "detail": str(value),
                        "kind": "field",
                        "line": line,
                        "children": [],
                    }
                )
        symbols.append(
            {
                "name": f"Record {index + 1}",
                "detail": detail,
                "kind": "record",
                "line": line,
                "children": children,
            }
        )
    return symbols


def format_text(text: str) -> str | None:
    """Pretty-print the JSON data file with a stable 2-space indent.

    Key order is preserved (not sorted). JSONC sugar (``//`` comments, trailing
    commas) is tolerated and normalised away. Returns ``None`` for input that is
    not valid JSON, signalling that the document should be left unchanged.

    Args:
        text: The raw (possibly JSONC) document text.

    Returns:
        The formatted JSON string (with a trailing newline), or ``None`` when
        the input cannot be parsed.
    """
    try:
        parsed = _loads_tolerant(text)
    except json.JSONDecodeError:
        return None
    return json.dumps(parsed, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# LSP glue (thin - maps plain dicts to lsprotocol types)
# ---------------------------------------------------------------------------
server = LanguageServer("camt053-lsp", "v0.0.5")

_SEVERITY = {
    "error": lsp.DiagnosticSeverity.Error,
    "warning": lsp.DiagnosticSeverity.Warning,
}

_SYMBOL_KIND = {
    "record": lsp.SymbolKind.Object,
    "field": lsp.SymbolKind.Field,
}


def _to_lsp_diagnostics(raw: list[dict]) -> list[lsp.Diagnostic]:
    """Map plain diagnostic dicts to ``lsprotocol`` ``Diagnostic`` objects."""
    diagnostics: list[lsp.Diagnostic] = []
    for item in raw:
        line = item["line"]
        char = item["character"]
        diagnostics.append(
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=line, character=char),
                    end=lsp.Position(line=line, character=char),
                ),
                message=item["message"],
                severity=_SEVERITY.get(
                    item["severity"], lsp.DiagnosticSeverity.Error
                ),
                source="camt053-lsp",
            )
        )
    return diagnostics


def _to_document_symbols(raw: list[dict]) -> list[lsp.DocumentSymbol]:
    """Map plain outline dicts to ``lsprotocol`` ``DocumentSymbol`` objects."""
    symbols: list[lsp.DocumentSymbol] = []
    for item in raw:
        line = item["line"]
        rng = lsp.Range(
            start=lsp.Position(line=line, character=0),
            end=lsp.Position(line=line, character=0),
        )
        symbols.append(
            lsp.DocumentSymbol(
                name=item["name"],
                detail=item["detail"] or None,
                kind=_SYMBOL_KIND.get(item["kind"], lsp.SymbolKind.Field),
                range=rng,
                selection_range=rng,
                children=_to_document_symbols(item["children"]),
            )
        )
    return symbols


def _validate_and_publish(ls: LanguageServer, uri: str) -> None:
    """Compute diagnostics for ``uri`` and publish them to the client.

    XML documents (detected by content) get CBPR+ Nov 2026 readiness
    diagnostics; everything else is treated as a JSON reversing-entry
    document.
    """
    document = ls.workspace.get_text_document(uri)
    source = document.source
    if _looks_like_xml(source):
        raw = compute_xml_diagnostics(source)
    else:
        raw = compute_diagnostics(source)
    ls.text_document_publish_diagnostics(
        lsp.PublishDiagnosticsParams(
            uri=uri,
            diagnostics=_to_lsp_diagnostics(raw),
        )
    )


@server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def did_open(
    ls: LanguageServer, params: lsp.DidOpenTextDocumentParams
) -> None:
    """Publish diagnostics when a document is opened."""
    _validate_and_publish(ls, params.text_document.uri)


@server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
def did_change(
    ls: LanguageServer, params: lsp.DidChangeTextDocumentParams
) -> None:
    """Publish diagnostics when a document changes."""
    _validate_and_publish(ls, params.text_document.uri)


@server.feature(lsp.TEXT_DOCUMENT_COMPLETION)
def completion(
    ls: LanguageServer, params: lsp.CompletionParams
) -> lsp.CompletionList:
    """Offer input-field and message-type completions."""
    items = [
        lsp.CompletionItem(
            label=item["label"],
            detail=item["detail"],
            kind=lsp.CompletionItemKind.Field,
        )
        for item in completion_items()
    ]
    return lsp.CompletionList(is_incomplete=False, items=items)


@server.feature(lsp.TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: lsp.HoverParams) -> lsp.Hover | None:
    """Show the schema description or message-type name under the cursor."""
    document = ls.workspace.get_text_document(params.text_document.uri)
    word = document.word_at_position(params.position)
    if not word:
        return None
    text = hover_markup(word)
    if text is None:
        return None
    return lsp.Hover(contents=text)


@server.feature(lsp.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(
    ls: LanguageServer, params: lsp.DocumentSymbolParams
) -> list[lsp.DocumentSymbol]:
    """Provide an outline (records and their fields) for the document."""
    document = ls.workspace.get_text_document(params.text_document.uri)
    return _to_document_symbols(document_symbols(document.source))


@server.feature(lsp.TEXT_DOCUMENT_FORMATTING)
def formatting(
    ls: LanguageServer, params: lsp.DocumentFormattingParams
) -> list[lsp.TextEdit]:
    """Pretty-print the whole document as a single full-document edit."""
    document = ls.workspace.get_text_document(params.text_document.uri)
    formatted = format_text(document.source)
    if formatted is None:
        return []
    lines = document.source.splitlines()
    end_line = len(lines)
    rng = lsp.Range(
        start=lsp.Position(line=0, character=0),
        end=lsp.Position(line=end_line, character=0),
    )
    return [lsp.TextEdit(range=rng, new_text=formatted)]


@server.feature(lsp.TEXT_DOCUMENT_CODE_ACTION)
def code_action(
    ls: LanguageServer, params: lsp.CodeActionParams
) -> list[lsp.CodeAction]:
    """Offer quick-fixes that insert a record's missing required fields."""
    document = ls.workspace.get_text_document(params.text_document.uri)
    uri = params.text_document.uri
    actions: list[lsp.CodeAction] = []
    for raw in code_actions(document.source):
        position = lsp.Position(line=raw["line"], character=raw["character"])
        edit = lsp.TextEdit(
            range=lsp.Range(start=position, end=position),
            new_text=raw["new_text"],
        )
        actions.append(
            lsp.CodeAction(
                title=raw["title"],
                kind=lsp.CodeActionKind.QuickFix,
                edit=lsp.WorkspaceEdit(changes={uri: [edit]}),
            )
        )
    return actions


def main() -> None:
    """Run the server over stdio, or handle --version / --help / --log-level.

    With no arguments the ``camt053-lsp`` language server runs over stdio.
    ``--version`` prints the package version and ``--help`` prints usage;
    both then exit without starting the server.
    ``--log-level`` configures Python logging before the server starts.
    Logs go to stderr so they never corrupt the LSP stdio transport.
    """
    parser = argparse.ArgumentParser(
        prog="camt053-lsp",
        description=(
            "Language Server Protocol server for camt053 reversing-entry "
            "data files. With no arguments, serves LSP over stdio."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"camt053-lsp {__version__}",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="WARNING",
        help="Set the logging level (default: WARNING). Logs go to stderr.",
    )
    args = parser.parse_args()
    import logging
    import sys
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        stream=sys.stderr,
        format="%(levelname)s %(name)s %(message)s",
    )
    server.start_io()


if __name__ == "__main__":  # pragma: no cover
    main()
