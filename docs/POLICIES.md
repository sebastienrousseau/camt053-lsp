<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Toolchain policy

Python 3.10 is the floor (`python = ">=3.10,<4.0"` in `pyproject.toml`), with
Linux CI on 3.10, 3.11, 3.12, 3.13 and 3.14. The floor matches the `camt053`
core library and moves with the rest of the camt053 suite. Raising it is a
maintainer decision, recorded in the changelog. No distro-system Python is
supported.
