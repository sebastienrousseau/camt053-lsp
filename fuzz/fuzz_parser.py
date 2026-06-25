#!/usr/bin/env python3
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

"""Atheris fuzz harness for the camt053-lsp document-processing entry points.

Every function exercised here is *total*: it is fed untrusted document text
straight from the editor and must return a value (never raise) for arbitrary
input -- malformed JSON, JSONC sugar, broken XML, control characters, etc.
A crash (uncaught exception) is therefore a real bug.

Run locally::

    pip install atheris
    python fuzz/fuzz_parser.py -atheris_runs=100000

In CI this target is built and run by ClusterFuzzLite (see ``.clusterfuzzlite``).
"""

import sys

import atheris

with atheris.instrument_imports():
    from camt053_lsp import server


def test_one_input(data: bytes) -> None:
    """Drive the total, text-consuming entry points with fuzzed input."""
    fdp = atheris.FuzzedDataProvider(data)
    text = fdp.ConsumeUnicodeNoSurrogates(sys.maxsize)

    # JSON / JSONC document pipeline -- all designed to tolerate any input.
    server.compute_diagnostics(text)
    server.code_actions(text)
    server.document_symbols(text)
    server.format_text(text)

    # XML (CBPR+) diagnostics pipeline.
    server.compute_xml_diagnostics(text)
    server._looks_like_xml(text)

    # Token-driven hover/lookup helpers.
    server.hover_markup(text)
    server.message_type_name(text)


def main() -> None:
    """Wire the harness into the libFuzzer driver and start fuzzing."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
