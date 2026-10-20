#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Fail when the release version is restated differently anywhere.

Single source of truth: ``version`` in ``pyproject.toml``. The same string
must appear in the package's ``__version__``, as a ``## [X.Y.Z]`` heading in
``CHANGELOG.md``, in ``CITATION.cff`` (``version``), in the README's
``Latest release: vX.Y.Z`` callout, and as the supported row of the
``SECURITY.md`` version table.

The camt053 suite releases together at one version, core first, so the
core floor this server declares (``pyproject.toml`` and every
``requirements/*.in`` that names it) must be ``>=`` this version too.

The README and SECURITY.md had sat six releases behind the package
(v0.0.14 against 0.0.20) with nothing to notice. Standard library only,
so the workflow needs no install.

Usage: python3 scripts/verify_versions.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

Check = tuple[list[str], list[str]]


def _read(name: str) -> str | None:
    path = ROOT / name
    return path.read_text(encoding="utf-8") if path.exists() else None


def _search(pattern: str, text: str | None) -> str | None:
    match = re.search(pattern, text or "", re.MULTILINE)
    return match.group(1) if match else None


def _pyproject_version() -> str:
    found = _search(r'^version\s*=\s*"([^"]+)"', _read("pyproject.toml"))
    if found is None:
        raise SystemExit("pyproject.toml has no version field")
    return found


def _package_version() -> str | None:
    for init in sorted(ROOT.glob("*/__init__.py")):
        if init.parent.name.startswith(
            (".", "_", "tests", "docs", "examples")
        ):
            continue
        found = _search(
            r'^__version__\s*=\s*"([^"]+)"',
            init.read_text(encoding="utf-8"),
        )
        if found:
            return found
    return None


def _check_package(expected: str) -> Check:
    pkg = _package_version()
    if pkg is None:
        return [], ["no package __version__ found"]
    line = f"  __version__            = {pkg}"
    ok = pkg == expected
    return [line], [] if ok else ["__version__ differs from pyproject.toml"]


def _check_changelog(expected: str) -> Check:
    headings = re.findall(
        r"^## \[(\d+\.\d+\.\d+)\]", _read("CHANGELOG.md") or "", re.MULTILINE
    )
    line = f"  CHANGELOG.md newest    = {headings[0] if headings else None}"
    ok = expected in headings
    return [line], [] if ok else [f"CHANGELOG.md has no [{expected}] heading"]


def _check_citation(expected: str) -> Check:
    text = _read("CITATION.cff")
    if text is None:
        return [], ["CITATION.cff is missing"]
    found = _search(r'^version:\s*"?([^"\s]+)"?\s*$', text)
    line = f"  CITATION.cff           = {found}"
    ok = found == expected
    return [line], [] if ok else ["CITATION.cff version differs"]


def _check_readme(expected: str) -> Check:
    found = _search(r"Latest release: v(\d+\.\d+\.\d+)", _read("README.md"))
    line = f"  README latest release  = {found}"
    ok = found == expected
    return [line], [] if ok else [f"README.md latest release is v{found}"]


def _check_security(expected: str) -> Check:
    found = _search(
        r"^\|\s*(\d+\.\d+\.\d+)\s*\|\s*:white_check_mark:",
        _read("SECURITY.md"),
    )
    line = f"  SECURITY.md supported  = {found}"
    ok = found == expected
    problem = f"SECURITY.md supports {found}, not {expected}"
    return [line], [] if ok else [problem]


#: The suite members this server depends on, released before it.
FAMILY = ("camt053",)

_FLOOR = re.compile(
    r'^"?(' + "|".join(re.escape(n) for n in FAMILY) + r')"?\s*=?\s*"?'
    r"\s*>=\s*([0-9][0-9.]*)",
    re.MULTILINE,
)


def _floors(text: str) -> list[tuple[str, str]]:
    """Every ``(member, floor)`` declared in ``text``."""
    return [(m.group(1), m.group(2)) for m in _FLOOR.finditer(text)]


def _check_family(expected: str) -> Check:
    sources = [
        ROOT / "pyproject.toml",
        *sorted(ROOT.glob("requirements/*.in")),
    ]
    found = {
        path: _floors(path.read_text(encoding="utf-8")) for path in sources
    }
    problems = [
        f"{path.relative_to(ROOT)}: {name}>={floor}, the suite is at {expected}"
        for path, floors in found.items()
        for name, floor in floors
        if floor != expected
    ]
    declared = {name for name, _ in found[sources[0]]}
    problems += [
        f"pyproject.toml declares no {name} floor"
        for name in FAMILY
        if name not in declared
    ]
    lines = [f"  suite floors           = {len(problems)} not at {expected}"]
    return lines, problems


CHECKS = (
    _check_package,
    _check_changelog,
    _check_citation,
    _check_readme,
    _check_security,
    _check_family,
)


def main() -> int:
    """Compare every restatement of the version and report."""
    expected = _pyproject_version()
    problems: list[str] = []
    print(f"  pyproject.toml version = {expected}")
    for check in CHECKS:
        lines, found = check(expected)
        for line in lines:
            print(line)
        problems.extend(found)
    for problem in problems:
        print(f"ERROR: {problem}")
    if problems:
        return 1
    print("OK: every source agrees on", expected)
    return 0


if __name__ == "__main__":
    sys.exit(main())
