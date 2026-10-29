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

"""Version-consistency guard.

Ensures ``camt053_lsp.__version__`` stays in lock-step with the packaged
``pyproject.toml`` version, so the version announced to LSP clients and the
published package never drift apart again.

The ``pyproject.toml`` version is read with ``tomllib``, which is in the
standard library on every supported Python (3.11 and newer).
"""

import tomllib
from pathlib import Path

import camt053_lsp

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _pyproject_version() -> str:
    """Return ``[tool.poetry] version`` from ``pyproject.toml``."""
    with _PYPROJECT.open("rb") as handle:
        version = tomllib.load(handle)["tool"]["poetry"]["version"]
    assert isinstance(version, str), "no version string in pyproject.toml"
    return version


def test_version_matches_pyproject() -> None:
    """``__version__`` must equal the packaged ``pyproject.toml`` version."""
    assert camt053_lsp.__version__ == _pyproject_version()
