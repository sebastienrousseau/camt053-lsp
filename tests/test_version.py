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

The ``pyproject.toml`` version is read with a regex on the file text rather
than ``tomllib`` because Python 3.10 (which lacks ``tomllib``) is part of the
CI matrix.
"""

import re
from pathlib import Path

import camt053_lsp

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
_VERSION_RE = re.compile(r'(?m)^version\s*=\s*"([^"]+)"')


def _pyproject_version() -> str:
    """Extract the ``version`` string from ``pyproject.toml`` via regex."""
    text = _PYPROJECT.read_text(encoding="utf-8")
    match = _VERSION_RE.search(text)
    assert match is not None, "no version string found in pyproject.toml"
    return match.group(1)


def test_version_matches_pyproject() -> None:
    """``__version__`` must equal the packaged ``pyproject.toml`` version."""
    assert camt053_lsp.__version__ == _pyproject_version()
