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

import camt053_lsp.server as lsp_server  # noqa: E402


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
