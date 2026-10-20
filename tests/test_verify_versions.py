# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""scripts/verify_versions.py finds every restatement of the version."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "verify_versions.py"

FILES = {
    "pyproject.toml": (
        '[tool.poetry]\nversion = "0.0.23"\n\n'
        '[tool.poetry.dependencies]\ncamt053 = ">=0.0.23,<1"\n'
    ),
    "pkg/__init__.py": '__version__ = "0.0.23"\n',
    "CHANGELOG.md": "# Changelog\n\n## [0.0.23] - 2026-10-20\n",
    "CITATION.cff": 'cff-version: 1.2.0\nversion: "0.0.23"\n',
    "README.md": "> **Latest release: v0.0.23**: an editor server.\n",
    "SECURITY.md": "| 0.0.23  | :white_check_mark: |\n| < 0.0.23 | :x: |\n",
}


@pytest.fixture
def tree(monkeypatch, tmp_path):
    """Write ``FILES`` (with overrides) to ``tmp_path`` and run main()."""
    spec = importlib.util.spec_from_file_location("verify_versions", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)

    def run(**overrides: str | None) -> list[str]:
        for name, text in {**FILES, **overrides}.items():
            path = tmp_path / name
            if text is None:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        expected = module._pyproject_version()
        return [p for check in module.CHECKS for p in check(expected)[1]]

    return run


def test_every_source_on_one_version_is_clean(tree):
    assert tree() == []


@pytest.mark.parametrize(
    ("name", "text", "problem"),
    [
        (
            "pkg/__init__.py",
            '__version__ = "0.0.20"\n',
            "__version__ differs from pyproject.toml",
        ),
        (
            "CHANGELOG.md",
            "## [0.0.20] - 2026-08-29\n",
            "CHANGELOG.md has no [0.0.23] heading",
        ),
        (
            "CITATION.cff",
            'version: "0.0.20"\n',
            "CITATION.cff version differs",
        ),
        (
            "README.md",
            "> **Latest release: v0.0.14**: old news.\n",
            "README.md latest release is v0.0.14",
        ),
        (
            "SECURITY.md",
            "| 0.0.14  | :white_check_mark: |\n",
            "SECURITY.md supports 0.0.14, not 0.0.23",
        ),
    ],
    ids=["package", "changelog", "citation", "readme", "security"],
)
def test_a_stale_source_fails(tree, name, text, problem):
    assert tree(**{name: text}) == [problem]


def test_a_missing_citation_fails(tree):
    """CITATION.cff is required, not optional, in this repository."""
    assert tree(**{"CITATION.cff": None}) == ["CITATION.cff is missing"]


def test_the_repository_agrees_with_itself():
    """The committed tree passes, so CI can run the script unchanged."""
    spec = importlib.util.spec_from_file_location("verify_tree", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main() == 0


@pytest.fixture
def family(monkeypatch, tmp_path):
    """``_check_family`` run against a tree written to ``tmp_path``."""
    spec = importlib.util.spec_from_file_location("verify_family", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    (tmp_path / "requirements").mkdir()

    def run(pyproject: str, req: str) -> list[str]:
        (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")
        (tmp_path / "requirements" / "test.in").write_text(
            req, encoding="utf-8"
        )
        return module._check_family("0.0.23")[1]

    return run


PYPROJECT = '[tool.poetry.dependencies]\ncamt053 = ">=0.0.23,<1"\n'
REQ = "camt053>=0.0.23,<1\npygls>=1.3.1\n"


def test_a_core_floor_on_the_suite_version_is_clean(family):
    assert family(PYPROJECT, REQ) == []


def test_a_stale_pyproject_core_floor_fails(family):
    """The 0.0.23 wheel shipped ``camt053 (>=0.0.20,<1)`` unnoticed."""
    stale = PYPROJECT.replace(">=0.0.23", ">=0.0.20")
    assert family(stale, REQ) == [
        "pyproject.toml: camt053>=0.0.20, the suite is at 0.0.23"
    ]


def test_a_stale_requirements_core_floor_fails(family):
    stale = REQ.replace(">=0.0.23", ">=0.0.20")
    assert family(PYPROJECT, stale) == [
        "requirements/test.in: camt053>=0.0.20, the suite is at 0.0.23"
    ]


def test_a_missing_core_floor_fails(family):
    """No floor at all would let any core resolve."""
    assert family("[tool.poetry.dependencies]\n", REQ) == [
        "pyproject.toml declares no camt053 floor"
    ]
