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

"""Load/stress tests for the Camt053 LSP server's hot paths.

These hammer the same handlers an editor drives hardest - document
open/change (diagnostics), completion, and hover - with sustained
concurrent requests from a thread pool, and assert three things:

* **Zero errors** - no handler raises and no valid document ever
  produces a spurious diagnostic under concurrency.
* **Bounded latency** - the per-request p95 stays under a generous
  bound even with all workers contending for the GIL (single-threaded
  means are well under 5 ms; the bounds below leave two orders of
  magnitude of headroom so CI machines never flake).
* **Bounded memory** - a sustained mixed workload does not grow traced
  memory beyond a small fixed budget (:mod:`tracemalloc`), i.e. the
  handlers do not leak per-request state.

The whole module is marked ``perf`` and excluded from the default gate
(``-m "not perf"`` in ``addopts``); run it explicitly with::

    pytest -m perf --no-cov
"""

import gc
import json
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor

import pytest

pytest.importorskip("pygls")

from lsprotocol import types as lsp  # noqa: E402

import camt053_lsp.server as lsp_server  # noqa: E402

pytestmark = pytest.mark.perf

# Workload shape: enough iterations to expose leaks and contention,
# small enough that the whole module stays well under a minute.
WORKERS = 8
ITERATIONS = 400

# Per-request wall-clock p95 bounds (seconds). Single-threaded means are
# ~4 ms (diagnostics) and ~0.2 ms (completion/hover); the bounds allow
# for WORKERS-way GIL contention plus slow CI hardware.
P95_DIAGNOSTICS = 0.25
P95_COMPLETION = 0.10
P95_HOVER = 0.10

# Traced-memory growth budget for the sustained mixed workload (bytes).
MEMORY_BUDGET = 8 * 1024 * 1024


# ---------------------------------------------------------------------------
# Lightweight stubs (mirroring test_lsp_server) - one server per worker.
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


def _document_text(reversal_record: dict, seq: int) -> str:
    """A valid multi-record document, made unique per iteration."""
    records = []
    for offset in range(3):
        record = dict(reversal_record)
        record["entry_ref"] = f"RVSL-NTRY-{seq:04d}-{offset}"
        record["amount"] = f"{100 + (seq % 900)}.{offset:02d}"
        records.append(record)
    return json.dumps(records, indent=2)


def _percentile(samples: list, fraction: float) -> float:
    """The ``fraction`` percentile of ``samples`` (nearest-rank)."""
    ordered = sorted(samples)
    index = min(len(ordered) - 1, int(len(ordered) * fraction))
    return ordered[index]


def _run_concurrently(task, count: int):  # noqa: ANN001
    """Run ``task(i)`` for ``i`` in ``range(count)`` across the pool.

    Returns ``(latencies, errors)`` where each latency is the wall-clock
    seconds of one call and ``errors`` collects every raised exception.
    """
    latencies: list = []
    errors: list = []

    def timed(i: int) -> None:
        start = time.perf_counter()
        try:
            task(i)
        except Exception as exc:  # noqa: BLE001 - collected, then asserted
            errors.append(exc)
        finally:
            latencies.append(time.perf_counter() - start)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(timed, range(count)))
    return latencies, errors


# ---------------------------------------------------------------------------
# (A) Sustained document open/change -> diagnostics.
# ---------------------------------------------------------------------------
def test_sustained_open_change_diagnostics(reversal_record):
    """Concurrent open+change cycles publish clean diagnostics, p95 bounded."""
    servers = []

    def lifecycle(i: int) -> None:
        document = _FakeDocument(_document_text(reversal_record, i))
        ls = _FakeLanguageServer(document)
        servers.append(ls)
        uri = f"file:///stress-{i}.json"
        lsp_server.did_open(
            ls,
            lsp.DidOpenTextDocumentParams(
                text_document=lsp.TextDocumentItem(
                    uri=uri,
                    language_id="json",
                    version=1,
                    text=document.source,
                )
            ),
        )
        document.source = _document_text(reversal_record, i + ITERATIONS)
        lsp_server.did_change(
            ls,
            lsp.DidChangeTextDocumentParams(
                text_document=lsp.VersionedTextDocumentIdentifier(
                    uri=uri, version=2
                ),
                content_changes=[],
            ),
        )

    latencies, errors = _run_concurrently(lifecycle, ITERATIONS)

    assert errors == []
    assert len(latencies) == ITERATIONS
    # Every cycle published open+change diagnostics, all clean (the
    # documents are valid, so any diagnostic is a concurrency artefact).
    assert all(len(ls.published) == 2 for ls in servers)
    assert all(
        params.diagnostics == [] for ls in servers for params in ls.published
    )
    p95 = _percentile(latencies, 0.95)
    assert p95 < P95_DIAGNOSTICS, f"diagnostics p95 {p95:.3f}s over budget"


# ---------------------------------------------------------------------------
# (B) Concurrent completion and hover.
# ---------------------------------------------------------------------------
def test_sustained_completion_requests(reversal_record):
    """Concurrent completion requests all return full lists, p95 bounded."""
    expected_labels = {item["label"] for item in lsp_server.completion_items()}

    def complete(i: int) -> None:
        document = _FakeDocument(_document_text(reversal_record, i))
        ls = _FakeLanguageServer(document)
        result = lsp_server.completion(
            ls,
            lsp.CompletionParams(
                text_document=lsp.TextDocumentIdentifier(
                    uri=f"file:///stress-{i}.json"
                ),
                position=lsp.Position(line=0, character=0),
            ),
        )
        assert isinstance(result, lsp.CompletionList)
        assert {item.label for item in result.items} == expected_labels

    latencies, errors = _run_concurrently(complete, ITERATIONS)

    assert errors == []
    p95 = _percentile(latencies, 0.95)
    assert p95 < P95_COMPLETION, f"completion p95 {p95:.3f}s over budget"


def test_sustained_hover_requests(reversal_record):
    """Concurrent hover requests resolve fields and types, p95 bounded."""
    words = [
        "reason_code",
        "account_servicer_bic",
        "camt.053.001.14",
        "amount",
    ]

    def hover(i: int) -> None:
        word = words[i % len(words)]
        document = _FakeDocument(_document_text(reversal_record, i), word=word)
        ls = _FakeLanguageServer(document)
        result = lsp_server.hover(
            ls,
            lsp.HoverParams(
                text_document=lsp.TextDocumentIdentifier(
                    uri=f"file:///stress-{i}.json"
                ),
                position=lsp.Position(line=0, character=1),
            ),
        )
        assert isinstance(result, lsp.Hover)
        assert result.contents

    latencies, errors = _run_concurrently(hover, ITERATIONS)

    assert errors == []
    p95 = _percentile(latencies, 0.95)
    assert p95 < P95_HOVER, f"hover p95 {p95:.3f}s over budget"


# ---------------------------------------------------------------------------
# (C) Memory growth under a sustained mixed workload.
# ---------------------------------------------------------------------------
def test_memory_growth_bounded_under_mixed_load(reversal_record):
    """A sustained mixed workload stays within the traced-memory budget."""

    def mixed(i: int) -> None:
        text = _document_text(reversal_record, i)
        document = _FakeDocument(text, word="reason_code")
        ls = _FakeLanguageServer(document)
        lsp_server._validate_and_publish(ls, f"file:///stress-{i}.json")
        lsp_server.completion(
            ls,
            lsp.CompletionParams(
                text_document=lsp.TextDocumentIdentifier(
                    uri=f"file:///stress-{i}.json"
                ),
                position=lsp.Position(line=0, character=0),
            ),
        )
        lsp_server.hover(
            ls,
            lsp.HoverParams(
                text_document=lsp.TextDocumentIdentifier(
                    uri=f"file:///stress-{i}.json"
                ),
                position=lsp.Position(line=0, character=1),
            ),
        )

    # Warm every cache (schema loads, message-type tables) before the
    # baseline so only per-request growth is measured.
    warmup_errors = _run_concurrently(mixed, WORKERS * 4)[1]
    assert warmup_errors == []

    tracemalloc.start()
    try:
        gc.collect()
        baseline, _ = tracemalloc.get_traced_memory()
        latencies, errors = _run_concurrently(mixed, ITERATIONS)
        gc.collect()
        current, _ = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert errors == []
    assert len(latencies) == ITERATIONS
    growth = current - baseline
    assert growth < MEMORY_BUDGET, (
        f"traced memory grew {growth / 1024 / 1024:.2f} MiB "
        f"(budget {MEMORY_BUDGET / 1024 / 1024:.0f} MiB)"
    )
