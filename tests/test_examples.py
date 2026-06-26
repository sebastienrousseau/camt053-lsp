# Copyright (C) 2023-2026 Sebastien Rousseau.
# SPDX-License-Identifier: Apache-2.0

"""Exercise every shipping example end-to-end as part of CI.

Each script under ``examples/`` whose name starts with two digits (the
per-capability examples) is imported as a module and its ``main`` is
run. The test passes if no exception is raised. The pre-existing
``examples/lsp_helpers.py`` umbrella script is included too.
"""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def _example_paths() -> list[Path]:
    return sorted(
        p
        for p in EXAMPLES_DIR.glob("*.py")
        if p.stem[0].isdigit() or p.stem == "lsp_helpers"
    )


@pytest.mark.parametrize(
    "example",
    _example_paths(),
    ids=lambda p: p.stem,
)
def test_example_runs(example: Path) -> None:
    spec = importlib.util.spec_from_file_location(example.stem, example)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "main"):
        if asyncio.iscoroutinefunction(module.main):
            asyncio.run(module.main())
        else:
            module.main()
