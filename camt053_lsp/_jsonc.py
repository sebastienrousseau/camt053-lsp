# SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""JSONC tolerance: ``//`` line comments and trailing commas, removed.

The editor re-parses the whole document on every change, so each pass
here is linear in the length of the text. Strings are skipped whole
(escapes included), so comment markers and commas inside string values
are kept.
"""

from __future__ import annotations


def strip_jsonc(text: str) -> str:
    """Strip JSONC sugar (``//`` line comments, trailing commas) to plain JSON.

    A dependency-free pre-step so JSONC data files parse with the standard
    library. ``//`` only starts a comment outside of strings; ``"`` quoting and
    backslash escapes are tracked so comment markers and commas inside string
    values are preserved. Clean JSON is returned unchanged in substance (only
    superfluous trailing commas / comments are removed).

    Args:
        text: The raw (possibly JSONC) document text.

    Returns:
        The text with line comments removed and trailing commas dropped.
    """
    return _drop_trailing_commas(_strip_line_comments(text))


def _string_end(text: str, start: int) -> int:
    """Index just past the JSON string that opens at ``text[start]``.

    Backslash escapes are skipped, so an escaped quote does not end the
    string. An unterminated string runs to the end of ``text``.
    """
    i = start + 1
    length = len(text)
    while i < length:
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == '"':
            return i + 1
        i += 1
    return length


def _strip_line_comments(text: str) -> str:
    """Remove ``//`` comments outside strings, keeping each end-of-line."""
    out: list[str] = []
    i = 0
    length = len(text)
    while i < length:
        if text[i] == '"':
            end = _string_end(text, i)
            out.append(text[i:end])
            i = end
        elif text.startswith("//", i):
            newline = text.find("\n", i)
            i = length if newline == -1 else newline
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _next_significant(text: str, start: int) -> str:
    """The first non-whitespace character at or after ``start``, or ``""``."""
    i = start
    length = len(text)
    while i < length and text[i].isspace():
        i += 1
    return text[i : i + 1]


def _drop_trailing_commas(text: str) -> str:
    """Drop each comma outside strings that precedes ``}`` or ``]``.

    The look-ahead walks only the whitespace after the comma, so the pass
    stays linear in the length of the document.
    """
    out: list[str] = []
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        if ch == '"':
            end = _string_end(text, i)
            out.append(text[i:end])
            i = end
            continue
        if ch != "," or _next_significant(text, i + 1) not in ("}", "]"):
            out.append(ch)
        i += 1
    return "".join(out)
