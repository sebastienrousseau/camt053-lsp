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
"""Tests for message_type_name() returning None for unknown tokens."""

import pytest

pytest.importorskip("pygls")

import camt053_lsp.server as lsp_server  # noqa: E402


def test_message_type_name_returns_none_for_unknown_token():
    """An unrecognised token returns None."""
    assert lsp_server.message_type_name("not-a-type") is None


def test_message_type_name_returns_none_for_empty_string():
    """An empty string returns None."""
    assert lsp_server.message_type_name("") is None


def test_message_type_name_returns_name_for_valid_token():
    """A supported message type returns its human-readable name."""
    result = lsp_server.message_type_name("camt.053.001.14")
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0
