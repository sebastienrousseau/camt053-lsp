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

"""Tests for the Camt053 Language Server Protocol server.

These exercise the pure helper functions directly (no server I/O required) plus
a couple of smoke checks on the module-level ``server`` object and ``main``.
"""

import json
import logging
import sys

import pytest

pytest.importorskip("pygls")

from lsprotocol import types as lsp  # noqa: E402

import camt053_lsp.server as lsp_server  # noqa: E402
from camt053_lsp import __version__  # noqa: E402


# ---------------------------------------------------------------------------
# Lightweight stubs for the LSP glue handlers (no live server).
# ---------------------------------------------------------------------------
class _FakeDocument:
    """Minimal stand-in for a pygls text document."""

    def __init__(self, source: str, word: str = "") -> None:
        self.source = source
        self._word = word

    def word_at_position(self, position) -> str:  # noqa: ANN001
        return self._word


class _FakeWorkspace:
    def __init__(self, document: _FakeDocument) -> None:
        self._document = document

    def get_text_document(self, uri: str) -> _FakeDocument:
        return self._document


class _FakeLanguageServer:
    """Records published diagnostics; exposes a fake workspace."""

    def __init__(self, document: _FakeDocument) -> None:
        self.workspace = _FakeWorkspace(document)
        self.published: list = []

    def text_document_publish_diagnostics(
        self, params
    ) -> None:  # noqa: ANN001
        self.published.append(params)


def test_valid_records_produce_no_diagnostics(reversal_record):
    """A complete, valid record yields no diagnostics."""
    text = json.dumps([reversal_record])
    diagnostics = lsp_server.compute_diagnostics(text)
    assert diagnostics == []


def test_single_dict_is_treated_as_one_record(reversal_record):
    """A single record object (not wrapped in a list) is accepted."""
    text = json.dumps(reversal_record)
    assert lsp_server.compute_diagnostics(text) == []


def test_missing_required_fields_produce_error(reversal_record):
    """A record missing required fields produces at least one error."""
    record = dict(reversal_record)
    record.pop("statement_msg_id", None)
    record.pop("reason_code", None)
    text = json.dumps([record])
    diagnostics = lsp_server.compute_diagnostics(text)
    errors = [d for d in diagnostics if d["severity"] == "error"]
    assert len(errors) >= 1


def test_bad_identifier_produces_diagnostic(reversal_record):
    """A record with an invalid IBAN/BIC is flagged."""
    record = dict(reversal_record)
    record["account_servicer_bic"] = "INVALID!"
    text = json.dumps([record])
    diagnostics = lsp_server.compute_diagnostics(text)
    assert any("account_servicer_bic" in d["message"] for d in diagnostics)
    assert len(diagnostics) >= 1


def test_malformed_json_produces_single_diagnostic():
    """Malformed JSON yields exactly one syntax diagnostic."""
    diagnostics = lsp_server.compute_diagnostics("[{not json}]")
    assert len(diagnostics) == 1
    assert diagnostics[0]["severity"] == "error"
    assert "Invalid JSON" in diagnostics[0]["message"]


def test_completion_items_include_field_and_message_type():
    """Completion includes a known field and at least one message type."""
    labels = {item["label"] for item in lsp_server.completion_items()}
    assert "reason_code" in labels
    assert any(label.startswith("camt.") for label in labels)


def test_hover_text_known_and_unknown():
    """Hover returns a description for a known field and None otherwise."""
    text = lsp_server.hover_text("account_servicer_bic")
    assert text
    assert isinstance(text, str)
    assert lsp_server.hover_text("nope") is None


def test_server_and_main_exist():
    """The module exposes a ``server`` object and a callable ``main``."""
    assert lsp_server.server is not None
    assert callable(lsp_server.main)


# ---------------------------------------------------------------------------
# (A) Pure-helper edge branches.
# ---------------------------------------------------------------------------
def test_empty_list_yields_expected_array_diagnostic():
    """An empty JSON array (no records) yields the 'Expected a JSON array' error."""
    diagnostics = lsp_server.compute_diagnostics("[]")
    assert len(diagnostics) == 1
    assert diagnostics[0]["severity"] == "error"
    assert "Expected a JSON array" in diagnostics[0]["message"]


def test_bare_json_int_yields_expected_array_diagnostic():
    """A bare JSON int is neither a list nor a dict -> normalise returns []."""
    diagnostics = lsp_server.compute_diagnostics("42")
    assert len(diagnostics) == 1
    assert "Expected a JSON array" in diagnostics[0]["message"]


def test_normalise_records_rejects_non_collection():
    """``_normalise_records`` returns [] for scalars (the fallthrough branch)."""
    assert lsp_server._normalise_records(42) == []
    assert lsp_server._normalise_records("x") == []
    assert lsp_server._normalise_records({"a": 1}) == [{"a": 1}]
    assert lsp_server._normalise_records([1, 2]) == [1, 2]


def test_schema_error_path_present_and_empty_branches(
    reversal_record, monkeypatch
):
    """Schema errors exercise both the path-present and path-empty branches."""

    def fake_validate_records(message_type, records):
        return {
            "valid": False,
            "total": len(records),
            "valid_count": 0,
            "errors": [
                {"row": 0, "path": "$.amount", "message": "bad amount"},
                {"row": 0, "path": "", "message": "missing field"},
            ],
        }

    monkeypatch.setattr(
        lsp_server.services, "validate_records", fake_validate_records
    )
    text = json.dumps([dict(reversal_record)])
    diagnostics = lsp_server.compute_diagnostics(text)
    messages = [d["message"] for d in diagnostics]
    # Path present -> prefixed; path empty -> no prefix.
    assert "$.amount: bad amount" in messages
    assert "missing field" in messages


def test_line_offset_out_of_range_falls_back_to_zero(
    reversal_record, monkeypatch
):
    """A diagnostic for a row beyond the located offsets falls back to line 0."""

    def fake_validate_records(message_type, records):
        return {
            "valid": False,
            "total": len(records),
            "valid_count": 0,
            "errors": [{"row": 99, "path": "$", "message": "out of range"}],
        }

    monkeypatch.setattr(
        lsp_server.services, "validate_records", fake_validate_records
    )
    text = json.dumps([dict(reversal_record)])
    diagnostics = lsp_server.compute_diagnostics(text)
    assert any(d["line"] == 0 for d in diagnostics)


def test_record_line_offsets_handles_braces_and_escapes():
    """Brace/escape tracking: braces and escaped quotes inside strings are ignored."""
    text = (
        "[\n"
        '  {"a": "has { brace and \\" quote"},\n'
        '  {"b": "second"}\n'
        "]"
    )
    offsets = lsp_server._record_line_offsets(text)
    # Two top-level records located on lines 1 and 2 (0-indexed).
    assert offsets == [1, 2]


def test_record_line_offsets_newline_inside_string():
    """A literal newline inside a quoted string still advances the line count."""
    # The newline occurs while ``in_string`` is True, so the trailing
    # ``if ch == "\\n": line += 1`` branch (not the in-block continue) runs.
    text = '[\n  {"a": "line one\nline two"},\n  {"b": 2}\n]'
    offsets = lsp_server._record_line_offsets(text)
    # First record opens on line 1; the embedded newline pushes the second
    # record's opening brace to line 3.
    assert offsets == [1, 3]


def test_record_line_offsets_nested_braces():
    """A nested object brace must not be counted as a new top-level record."""
    text = '[{"a": {"nested": 1}}, {"b": 2}]'
    offsets = lsp_server._record_line_offsets(text)
    assert offsets == [0, 0]


def test_identifier_skip_and_warning_branches(reversal_record):
    """Empty/non-string identifiers are skipped; invalid ones warn."""
    record = dict(reversal_record)
    record["account_id"] = ""  # falsy -> skip branch
    record["counterparty_account"] = 12345  # non-string -> skip branch
    record["account_servicer_bic"] = "INVALID!"  # invalid -> warning branch
    text = json.dumps([record])
    diagnostics = lsp_server.compute_diagnostics(text)
    warnings = [d for d in diagnostics if d["severity"] == "warning"]
    assert any("account_servicer_bic" in w["message"] for w in warnings)
    assert not any("account_id" in w["message"] for w in warnings)
    assert not any("counterparty_account" in w["message"] for w in warnings)


def test_identifier_validation_skips_non_dict_record(monkeypatch):
    """A non-dict record in the list is skipped by the identifier loop."""

    def fake_validate_records(message_type, records):
        return {
            "valid": True,
            "total": len(records),
            "valid_count": len(records),
            "errors": [],
        }

    monkeypatch.setattr(
        lsp_server.services, "validate_records", fake_validate_records
    )
    # A list whose only element is not a dict (normalise keeps the list).
    text = json.dumps(["not a record"])
    diagnostics = lsp_server.compute_diagnostics(text)
    assert diagnostics == []


def test_hover_text_known_with_no_description(monkeypatch):
    """A field present in the schema but with no description returns None."""

    def fake_get_input_schema(message_type):
        return {"properties": {"weird": {"type": "string"}}}

    monkeypatch.setattr(
        lsp_server.services, "get_input_schema", fake_get_input_schema
    )
    assert lsp_server.hover_text("weird") is None
    assert lsp_server.hover_text("unknown") is None


def test_completion_item_empty_detail_branch(monkeypatch):
    """A field with no/None description yields an empty detail string."""

    def fake_get_input_schema(message_type):
        return {"properties": {"nodesc": None, "blank": {"type": "string"}}}

    monkeypatch.setattr(
        lsp_server.services, "get_input_schema", fake_get_input_schema
    )
    monkeypatch.setattr(lsp_server.services, "list_message_types", lambda: [])
    items = {
        item["label"]: item["detail"] for item in lsp_server.completion_items()
    }
    assert items["nodesc"] == ""
    assert items["blank"] == ""


# ---------------------------------------------------------------------------
# (B) LSP glue handlers, driven with lightweight stubs.
# ---------------------------------------------------------------------------
def test_to_lsp_diagnostics_severity_mapping():
    """Error/warning map to their severities; unknown maps to the default."""
    raw = [
        {"line": 0, "character": 0, "severity": "error", "message": "e"},
        {"line": 1, "character": 0, "severity": "warning", "message": "w"},
        {"line": 2, "character": 0, "severity": "mystery", "message": "u"},
    ]
    diagnostics = lsp_server._to_lsp_diagnostics(raw)
    assert diagnostics[0].severity == lsp.DiagnosticSeverity.Error
    assert diagnostics[1].severity == lsp.DiagnosticSeverity.Warning
    # Unknown severity falls back to Error via _SEVERITY.get default.
    assert diagnostics[2].severity == lsp.DiagnosticSeverity.Error


def test_did_open_publishes_diagnostics(reversal_record):
    """``did_open`` computes diagnostics and publishes them."""
    record = dict(reversal_record)
    record["account_servicer_bic"] = "INVALID!"
    document = _FakeDocument(json.dumps([record]))
    ls = _FakeLanguageServer(document)
    params = lsp.DidOpenTextDocumentParams(
        text_document=lsp.TextDocumentItem(
            uri="file:///doc.json",
            language_id="json",
            version=1,
            text=document.source,
        )
    )
    lsp_server.did_open(ls, params)
    assert len(ls.published) == 1
    assert ls.published[0].uri == "file:///doc.json"
    assert ls.published[0].diagnostics


def test_did_change_publishes_diagnostics(reversal_record):
    """``did_change`` computes diagnostics and publishes them."""
    document = _FakeDocument(json.dumps([dict(reversal_record)]))
    ls = _FakeLanguageServer(document)
    params = lsp.DidChangeTextDocumentParams(
        text_document=lsp.VersionedTextDocumentIdentifier(
            uri="file:///doc.json", version=2
        ),
        content_changes=[],
    )
    lsp_server.did_change(ls, params)
    assert len(ls.published) == 1
    assert ls.published[0].uri == "file:///doc.json"


def test_completion_handler_returns_completion_list():
    """``completion`` returns a populated ``CompletionList``."""
    document = _FakeDocument("[]")
    ls = _FakeLanguageServer(document)
    params = lsp.CompletionParams(
        text_document=lsp.TextDocumentIdentifier(uri="file:///doc.json"),
        position=lsp.Position(line=0, character=0),
    )
    result = lsp_server.completion(ls, params)
    assert isinstance(result, lsp.CompletionList)
    assert result.is_incomplete is False
    assert result.items
    assert all(
        item.kind == lsp.CompletionItemKind.Field for item in result.items
    )


def test_hover_handler_known_word_returns_hover():
    """``hover`` returns a ``Hover`` for a word that maps to a description."""
    document = _FakeDocument("[]", word="reason_code")
    ls = _FakeLanguageServer(document)
    params = lsp.HoverParams(
        text_document=lsp.TextDocumentIdentifier(uri="file:///doc.json"),
        position=lsp.Position(line=0, character=1),
    )
    result = lsp_server.hover(ls, params)
    assert isinstance(result, lsp.Hover)
    assert result.contents


def test_hover_handler_unknown_word_returns_none():
    """``hover`` returns None for a word with no description."""
    document = _FakeDocument("[]", word="not_a_field")
    ls = _FakeLanguageServer(document)
    params = lsp.HoverParams(
        text_document=lsp.TextDocumentIdentifier(uri="file:///doc.json"),
        position=lsp.Position(line=0, character=1),
    )
    assert lsp_server.hover(ls, params) is None


def test_hover_handler_empty_word_returns_none():
    """``hover`` returns None when the cursor is not on a word."""
    document = _FakeDocument("[]", word="")
    ls = _FakeLanguageServer(document)
    params = lsp.HoverParams(
        text_document=lsp.TextDocumentIdentifier(uri="file:///doc.json"),
        position=lsp.Position(line=0, character=0),
    )
    assert lsp_server.hover(ls, params) is None


def test_main_starts_io(monkeypatch):
    """``main`` delegates to ``server.start_io`` (stubbed to a no-op)."""
    calls = []
    monkeypatch.setattr(
        lsp_server.server,
        "start_io",
        lambda: calls.append(True),
    )
    # Stub ``basicConfig`` so the test never mutates global logging state.
    monkeypatch.setattr(logging, "basicConfig", lambda **kwargs: None)
    monkeypatch.setattr(sys, "argv", ["camt053-lsp"])
    lsp_server.main()
    assert calls == [True]


def test_main_version_flag(monkeypatch, capsys):
    """``--version`` prints the package version and exits 0."""
    monkeypatch.setattr(sys, "argv", ["camt053-lsp", "--version"])
    with pytest.raises(SystemExit) as exc:
        lsp_server.main()
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_main_help_flag(monkeypatch, capsys):
    """``--help`` prints usage and exits 0 without starting the server."""
    monkeypatch.setattr(sys, "argv", ["camt053-lsp", "--help"])
    with pytest.raises(SystemExit) as exc:
        lsp_server.main()
    assert exc.value.code == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_main_log_level_default(monkeypatch):
    """``main`` configures logging at WARNING on stderr by default."""
    captured = {}
    monkeypatch.setattr(sys, "argv", ["camt053-lsp"])
    monkeypatch.setattr(lsp_server.server, "start_io", lambda: None)
    monkeypatch.setattr(
        logging, "basicConfig", lambda **kwargs: captured.update(kwargs)
    )
    lsp_server.main()
    assert captured["level"] == logging.WARNING
    assert captured["stream"] is sys.stderr
    # ``force=True`` is what makes the level apply even if the root logger
    # was already configured by an imported dependency.
    assert captured["force"] is True


@pytest.mark.parametrize(
    ("name", "level"),
    [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
    ],
)
def test_main_log_level_sets_level(monkeypatch, name, level):
    """``--log-level NAME`` maps to the matching level and logs to stderr."""
    captured = {}
    monkeypatch.setattr(sys, "argv", ["camt053-lsp", "--log-level", name])
    monkeypatch.setattr(lsp_server.server, "start_io", lambda: None)
    monkeypatch.setattr(
        logging, "basicConfig", lambda **kwargs: captured.update(kwargs)
    )
    lsp_server.main()
    assert captured["level"] == level
    assert captured["stream"] is sys.stderr


def test_main_log_level_rejects_invalid(monkeypatch, capsys):
    """An unknown ``--log-level`` value exits non-zero with an error."""
    monkeypatch.setattr(sys, "argv", ["camt053-lsp", "--log-level", "TRACE"])
    with pytest.raises(SystemExit) as exc:
        lsp_server.main()
    assert exc.value.code != 0
    assert "invalid choice" in capsys.readouterr().err.lower()


def test_validate_and_publish_directly(reversal_record):
    """``_validate_and_publish`` pulls the document and publishes diagnostics."""
    document = _FakeDocument(json.dumps([dict(reversal_record)]))
    ls = _FakeLanguageServer(document)
    lsp_server._validate_and_publish(ls, "file:///doc.json")
    assert len(ls.published) == 1


# ---------------------------------------------------------------------------
# (C) JSONC tolerance.
# ---------------------------------------------------------------------------
def test_strip_jsonc_removes_line_comments_and_trailing_commas():
    """``//`` comments and trailing commas are stripped; strings preserved."""
    text = (
        "[\n"
        "  // leading comment\n"
        '  {"a": 1, "b": "http://x", "c": 2,},\n'
        '  {"d": "trailing, comma in string",},\n'
        "]"
    )
    stripped = lsp_server._strip_jsonc(text)
    parsed = json.loads(stripped)
    assert parsed == [
        {"a": 1, "b": "http://x", "c": 2},
        {"d": "trailing, comma in string"},
    ]


def test_strip_jsonc_preserves_escaped_quote_in_string():
    """An escaped quote inside a string must not end the string early."""
    text = '{"a": "he said \\"//hi\\"", "b": 2,}'
    parsed = json.loads(lsp_server._strip_jsonc(text))
    assert parsed == {"a": 'he said "//hi"', "b": 2}


def test_loads_tolerant_parses_clean_json_identically():
    """Clean JSON parses exactly as ``json.loads`` would."""
    assert lsp_server._loads_tolerant('[{"a": 1}]') == [{"a": 1}]


def test_diagnostics_tolerate_jsonc(reversal_record):
    """Diagnostics work on a JSONC document (comments + trailing commas)."""
    record = dict(reversal_record)
    body = json.dumps(record)
    text = "[\n  // a comment\n  " + body + ",\n]"
    assert lsp_server.compute_diagnostics(text) == []


# ---------------------------------------------------------------------------
# (D) Document symbols (outline).
# ---------------------------------------------------------------------------
def test_document_symbols_records_fields_and_lines(reversal_record):
    """Each record yields a parent symbol with its fields as children."""
    text = "[\n" + json.dumps(dict(reversal_record)) + "\n]"
    symbols = lsp_server.document_symbols(text)
    assert len(symbols) == 1
    record = symbols[0]
    assert record["name"] == "Record 1"
    assert record["kind"] == "record"
    assert record["detail"] == reversal_record["statement_msg_id"]
    assert record["line"] == 1
    names = {child["name"] for child in record["children"]}
    assert "reason_code" in names
    assert all(child["kind"] == "field" for child in record["children"])
    assert all(child["line"] == 1 for child in record["children"])


def test_document_symbols_entry_ref_fallback_detail():
    """When ``statement_msg_id`` is absent, ``entry_ref`` is used as detail."""
    text = json.dumps([{"entry_ref": "NTRY-9"}])
    symbols = lsp_server.document_symbols(text)
    assert symbols[0]["detail"] == "NTRY-9"


def test_document_symbols_no_id_empty_detail():
    """A record with neither id field gets an empty detail string."""
    text = json.dumps([{"other": 1}])
    symbols = lsp_server.document_symbols(text)
    assert symbols[0]["detail"] == ""


def test_document_symbols_non_dict_record_no_children():
    """A non-dict record yields a parent symbol with no children."""
    text = json.dumps(["scalar"])
    symbols = lsp_server.document_symbols(text)
    assert symbols[0]["children"] == []
    assert symbols[0]["detail"] == ""


def test_document_symbols_line_fallback_when_offset_missing(monkeypatch):
    """A record index beyond the located offsets falls back to line 0."""
    monkeypatch.setattr(lsp_server, "_record_line_offsets", lambda text: [])
    symbols = lsp_server.document_symbols(json.dumps([{"a": 1}]))
    assert symbols[0]["line"] == 0


def test_document_symbols_empty_and_malformed():
    """Empty arrays yield no symbols; malformed JSON yields an empty outline."""
    assert lsp_server.document_symbols("[]") == []
    assert lsp_server.document_symbols("[{not json}]") == []


# ---------------------------------------------------------------------------
# (E) Formatting.
# ---------------------------------------------------------------------------
def test_format_text_formats_valid_and_preserves_key_order():
    """Valid JSON is pretty-printed with 2-space indent, key order kept."""
    formatted = lsp_server.format_text('[{"b":1,"a":2}]')
    assert formatted == '[\n  {\n    "b": 1,\n    "a": 2\n  }\n]\n'


def test_format_text_tolerates_jsonc():
    """JSONC sugar is normalised away during formatting."""
    formatted = lsp_server.format_text('[{"a":1,},// c\n]')
    assert formatted == '[\n  {\n    "a": 1\n  }\n]\n'


def test_format_text_invalid_returns_none():
    """Invalid JSON returns ``None`` (document left unchanged)."""
    assert lsp_server.format_text("[{not json}]") is None


# ---------------------------------------------------------------------------
# (F) New LSP glue handlers, driven with stubs.
# ---------------------------------------------------------------------------
def test_to_document_symbols_maps_kinds_and_detail():
    """The mapper sets kinds, ranges, nests children, and blanks empty detail."""
    raw = [
        {
            "name": "Record 1",
            "detail": "ID-1",
            "kind": "record",
            "line": 2,
            "children": [
                {
                    "name": "f",
                    "detail": "",
                    "kind": "field",
                    "line": 2,
                    "children": [],
                },
                {
                    "name": "g",
                    "detail": "v",
                    "kind": "mystery",
                    "line": 2,
                    "children": [],
                },
            ],
        }
    ]
    symbols = lsp_server._to_document_symbols(raw)
    assert symbols[0].kind == lsp.SymbolKind.Object
    assert symbols[0].detail == "ID-1"
    assert symbols[0].range.start.line == 2
    child_empty, child_unknown = symbols[0].children
    assert child_empty.kind == lsp.SymbolKind.Field
    # Empty detail is mapped to None.
    assert child_empty.detail is None
    # Unknown kind falls back to Field.
    assert child_unknown.kind == lsp.SymbolKind.Field


def test_document_symbol_handler_returns_symbols(reversal_record):
    """``document_symbol`` returns ``DocumentSymbol`` objects for the doc."""
    document = _FakeDocument("[" + json.dumps(dict(reversal_record)) + "]")
    ls = _FakeLanguageServer(document)
    params = lsp.DocumentSymbolParams(
        text_document=lsp.TextDocumentIdentifier(uri="file:///doc.json")
    )
    result = lsp_server.document_symbol(ls, params)
    assert result
    assert all(isinstance(sym, lsp.DocumentSymbol) for sym in result)
    assert result[0].children


def test_formatting_handler_returns_single_edit(reversal_record):
    """``formatting`` returns one full-document ``TextEdit`` for valid JSON."""
    source = '[{"b":1,"a":2}]'
    document = _FakeDocument(source)
    ls = _FakeLanguageServer(document)
    params = lsp.DocumentFormattingParams(
        text_document=lsp.TextDocumentIdentifier(uri="file:///doc.json"),
        options=lsp.FormattingOptions(tab_size=2, insert_spaces=True),
    )
    result = lsp_server.formatting(ls, params)
    assert len(result) == 1
    assert result[0].new_text == '[\n  {\n    "b": 1,\n    "a": 2\n  }\n]\n'
    assert result[0].range.start.line == 0
    assert result[0].range.end.line == 1


def test_formatting_handler_invalid_returns_no_edits():
    """``formatting`` returns no edits for invalid JSON (unchanged doc)."""
    document = _FakeDocument("[{not json}]")
    ls = _FakeLanguageServer(document)
    params = lsp.DocumentFormattingParams(
        text_document=lsp.TextDocumentIdentifier(uri="file:///doc.json"),
        options=lsp.FormattingOptions(tab_size=2, insert_spaces=True),
    )
    assert lsp_server.formatting(ls, params) == []


# ---------------------------------------------------------------------------
# (G) Message-type hover.
# ---------------------------------------------------------------------------
def test_message_type_name_known_and_unknown():
    """A supported message type resolves to its name; others -> None."""
    name = lsp_server.message_type_name("camt.053.001.14")
    assert name == "Bank To Customer Statement"
    assert lsp_server.message_type_name("reason_code") is None
    assert lsp_server.message_type_name("camt.999.999.99") is None


def test_hover_markup_message_type_field_and_unknown():
    """Hover markup covers message-type, field, and unknown tokens."""
    markup = lsp_server.hover_markup("camt.053.001.14")
    assert markup == "camt.053.001.14 — Bank To Customer Statement"
    field = lsp_server.hover_markup("account_servicer_bic")
    assert field and "camt.053" not in field
    assert lsp_server.hover_markup("nope") is None


def test_hover_handler_message_type_returns_hover():
    """``hover`` returns the message-type name for a message-type token."""
    document = _FakeDocument("[]", word="camt.053.001.14")
    ls = _FakeLanguageServer(document)
    params = lsp.HoverParams(
        text_document=lsp.TextDocumentIdentifier(uri="file:///doc.json"),
        position=lsp.Position(line=0, character=1),
    )
    result = lsp_server.hover(ls, params)
    assert isinstance(result, lsp.Hover)
    assert result.contents == "camt.053.001.14 — Bank To Customer Statement"


# ---------------------------------------------------------------------------
# (H) Code actions.
# ---------------------------------------------------------------------------
def test_code_actions_missing_fields_proposes_action():
    """A record missing required fields proposes a quick-fix with an edit."""
    text = '[\n  {"statement_msg_id": "X"}\n]'
    actions = lsp_server.code_actions(text)
    assert len(actions) == 1
    action = actions[0]
    # ``statement_msg_id`` is present; the rest of the required set is missing.
    assert "amount" in action["fields"]
    assert "statement_msg_id" not in action["fields"]
    assert "amount" in action["title"]
    # Insertion is just after the record's opening brace on its line.
    assert action["line"] == 1
    assert action["character"] == 3
    assert '"amount": ""' in action["new_text"]


def test_code_actions_valid_record_yields_none(reversal_record):
    """A complete record produces no code action."""
    text = json.dumps([dict(reversal_record)])
    assert lsp_server.code_actions(text) == []


def test_code_actions_malformed_json_yields_none():
    """Malformed JSON produces no code actions."""
    assert lsp_server.code_actions("[{not json}]") == []


def test_code_actions_empty_records_yields_none():
    """An empty array (no records) produces no code actions."""
    assert lsp_server.code_actions("[]") == []


def test_code_actions_skips_non_dict_record():
    """A non-dict record is skipped by the code-action loop."""
    assert lsp_server.code_actions(json.dumps(["scalar"])) == []


def test_code_actions_line_fallback_when_offset_missing(monkeypatch):
    """A record index beyond the located offsets falls back to line 0."""
    monkeypatch.setattr(lsp_server, "_record_line_offsets", lambda text: [])
    actions = lsp_server.code_actions(json.dumps([{"statement_msg_id": "X"}]))
    assert actions
    assert actions[0]["line"] == 0
    assert '"amount": ""' in actions[0]["new_text"]


def test_code_actions_no_brace_uses_default_indent(monkeypatch):
    """When the record's line holds no ``{``, the default indent is used."""
    # Force line 0 (which has no brace: it's the bare opening bracket here)
    # for a record by faking offsets, and split so the brace is on line 1.
    monkeypatch.setattr(lsp_server, "_record_line_offsets", lambda text: [0])
    text = '[\n{"statement_msg_id": "X"}\n]'
    actions = lsp_server.code_actions(text)
    assert actions
    # Line 0 is "[" -> no brace -> two-space default indent, insert at line end.
    assert actions[0]["line"] == 0
    assert actions[0]["character"] == 1
    assert '\n  "amount": ""' in actions[0]["new_text"]


def test_code_action_handler_returns_code_actions():
    """``code_action`` returns ``CodeAction`` objects with workspace edits."""
    document = _FakeDocument('[\n  {"statement_msg_id": "X"}\n]')
    ls = _FakeLanguageServer(document)
    params = lsp.CodeActionParams(
        text_document=lsp.TextDocumentIdentifier(uri="file:///doc.json"),
        range=lsp.Range(
            start=lsp.Position(line=0, character=0),
            end=lsp.Position(line=0, character=0),
        ),
        context=lsp.CodeActionContext(diagnostics=[]),
    )
    result = lsp_server.code_action(ls, params)
    assert len(result) == 1
    action = result[0]
    assert isinstance(action, lsp.CodeAction)
    assert action.kind == lsp.CodeActionKind.QuickFix
    edits = action.edit.changes["file:///doc.json"]
    assert len(edits) == 1
    assert '"amount": ""' in edits[0].new_text


def test_code_action_handler_no_actions_for_valid(reversal_record):
    """``code_action`` returns no actions for a valid document."""
    document = _FakeDocument(json.dumps([dict(reversal_record)]))
    ls = _FakeLanguageServer(document)
    params = lsp.CodeActionParams(
        text_document=lsp.TextDocumentIdentifier(uri="file:///doc.json"),
        range=lsp.Range(
            start=lsp.Position(line=0, character=0),
            end=lsp.Position(line=0, character=0),
        ),
        context=lsp.CodeActionContext(diagnostics=[]),
    )
    assert lsp_server.code_action(ls, params) == []


# ─── XML / CBPR+ readiness diagnostics (Nov 14-16 2026 cliff) ───────────────

_CBPR_READY_V08 = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.08">'
    "<BkToCstmrStmt><GrpHdr><MsgId>M</MsgId>"
    "<CreDtTm>2026-06-21T10:00:00</CreDtTm></GrpHdr>"
    "<Stmt><Id>S</Id>"
    "<Acct><Id><IBAN>DE89370400440532013000</IBAN></Id></Acct>"
    "</Stmt></BkToCstmrStmt></Document>"
)

_CBPR_BAD_UNSTRUCTURED = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.08">'
    "<BkToCstmrStmt><GrpHdr><MsgId>M</MsgId>"
    "<CreDtTm>2026-06-21T10:00:00</CreDtTm></GrpHdr>"
    "<Stmt><Id>S</Id>"
    "<Acct><Id><IBAN>DE89370400440532013000</IBAN></Id></Acct>"
    "<Ntry><NtryDtls><TxDtls><RltdPties><Cdtr>"
    "<PstlAdr><AdrLine>Line only</AdrLine></PstlAdr>"
    "</Cdtr></RltdPties></TxDtls></NtryDtls></Ntry>"
    "</Stmt></BkToCstmrStmt></Document>"
)


def test_looks_like_xml_detects_xml_decl():
    """An XML declaration prefix is recognised as XML."""
    assert lsp_server._looks_like_xml(_CBPR_READY_V08) is True


def test_looks_like_xml_detects_bare_root_element():
    """A bare root element with no XML declaration is also XML."""
    assert lsp_server._looks_like_xml("<Document/>") is True


def test_looks_like_xml_tolerates_leading_whitespace():
    """Leading whitespace does not defeat the sniff."""
    assert lsp_server._looks_like_xml("   <Document/>") is True


def test_looks_like_xml_rejects_json_documents():
    """A JSON array or object is not XML."""
    assert lsp_server._looks_like_xml("[]") is False
    assert lsp_server._looks_like_xml("{}") is False


def test_looks_like_xml_tolerates_utf8_bom():
    """A leading UTF-8 BOM before the declaration or root element is XML."""
    assert lsp_server._looks_like_xml("﻿<?xml version='1.0'?>") is True
    assert lsp_server._looks_like_xml("﻿   <Document/>") is True


def test_looks_like_xml_rejects_empty_or_blank():
    """Empty or whitespace-only input is not XML."""
    assert lsp_server._looks_like_xml("") is False
    assert lsp_server._looks_like_xml("   \n\t") is False


def test_compute_xml_diagnostics_clean_v08_yields_none():
    """A clean v08 payload yields no diagnostics."""
    assert lsp_server.compute_xml_diagnostics(_CBPR_READY_V08) == []


def test_compute_xml_diagnostics_unstructured_yields_error():
    """An unstructured-only address yields one error diagnostic."""
    diagnostics = lsp_server.compute_xml_diagnostics(_CBPR_BAD_UNSTRUCTURED)
    assert len(diagnostics) == 1
    issue = diagnostics[0]
    assert issue["severity"] == "error"
    assert "UNSTRUCTURED_ONLY_ADDRESS" in issue["message"]
    assert "PstlAdr" in issue["message"]


def test_compute_xml_diagnostics_malformed_xml_yields_one_diagnostic():
    """Malformed XML produces a single CBPR+ check failed diagnostic."""
    diagnostics = lsp_server.compute_xml_diagnostics("<Document>unclosed")
    assert len(diagnostics) == 1
    assert diagnostics[0]["severity"] == "error"
    assert "CBPR+ check failed" in diagnostics[0]["message"]


def test_validate_and_publish_dispatches_xml(reversal_record):
    """Opening an XML file routes through the CBPR+ diagnostic path."""
    document = _FakeDocument(_CBPR_BAD_UNSTRUCTURED)
    ls = _FakeLanguageServer(document)
    lsp_server._validate_and_publish(ls, "file:///statement.xml")
    assert len(ls.published) == 1
    diags = ls.published[0].diagnostics
    assert len(diags) == 1
    assert diags[0].severity == lsp.DiagnosticSeverity.Error
    assert "UNSTRUCTURED_ONLY_ADDRESS" in diags[0].message


def test_validate_and_publish_still_handles_json_records(reversal_record):
    """A JSON document still goes through the original validator."""
    document = _FakeDocument(json.dumps([dict(reversal_record)]))
    ls = _FakeLanguageServer(document)
    lsp_server._validate_and_publish(ls, "file:///records.json")
    # The valid reversal record produces zero diagnostics in the existing
    # JSON validator path; the test asserts that the JSON dispatch wins.
    assert ls.published[0].diagnostics == []
