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

import pytest

pytest.importorskip("pygls")

from lsprotocol import types as lsp  # noqa: E402

import camt053_lsp.server as lsp_server  # noqa: E402


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
    lsp_server.main()
    assert calls == [True]


def test_validate_and_publish_directly(reversal_record):
    """``_validate_and_publish`` pulls the document and publishes diagnostics."""
    document = _FakeDocument(json.dumps([dict(reversal_record)]))
    ls = _FakeLanguageServer(document)
    lsp_server._validate_and_publish(ls, "file:///doc.json")
    assert len(ls.published) == 1
