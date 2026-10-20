<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Benchmarks

`benches/bench_diagnostics.py` measures how long an editor waits for this
server: diagnostics on every change, across document sizes, for valid and
malformed documents, plus completion and hover. CI runs it with `--quick` as
a smoke test. Nothing asserts a threshold: wall-clock depends on hardware,
Python and dependency versions, and no hardware-independent claim is made.

```sh
poetry install
python benches/bench_diagnostics.py           # 1, 25, 100 and 500 records
python benches/bench_diagnostics.py --quick   # what CI runs
python benches/bench_diagnostics.py --json
```

The table marks two thresholds: 16 ms (one frame, feels instant) and 100 ms
(the limit of "reacting instantly"). The number to read is the budget: how
large a document stays interactive.

## Recorded results

Measured for 0.0.18 (2026-08-29) and recorded in the
[changelog](../CHANGELOG.md). The three language servers in the suite do the
same shape of work:

| Server | Diagnostics cost | Interactive budget |
| :--- | ---: | ---: |
| `bankstatementparser-lsp` | 0.0018 ms per entry | ~56,000 entries |
| `pain001-lsp` | 0.08 ms per record | ~1,200 records |
| `camt053-lsp` | 0.86 ms per record | ~116 records |

## Where the time goes

Profiling `compute_diagnostics` on a 100-record document on 2026-10-20
(Python 3.12.15, camt053 0.0.20):

| Step | Share of the call |
| :--- | ---: |
| `camt053.services.validate_records` (JSON Schema validation in the core) | about 89% |
| of which `jsonschema` re-checking the schema itself, once per record | about 80% |
| JSONC stripping (`camt053_lsp/_jsonc.py`) | about 9% |

The core library calls `jsonschema.validate`, which validates the schema
against its metaschema before every record. That is the cost that makes
this server ten times slower than `pain001-lsp`, and it is fixed in the core,
not here, because every interface in the suite shares that validator.

Before 0.0.23 the JSONC pass was quadratic: each comma copied the rest of
the document. Stripping a 1.2 MB document took 3.2 s; it is now linear.
`tests/test_stress.py::test_strip_jsonc_scales_linearly` (run with
`pytest -m perf --no-cov`) holds it there.

A full run on a quiet machine was not possible when 0.0.23 was prepared (the
load average was above 20), so no new absolute numbers are published here.
