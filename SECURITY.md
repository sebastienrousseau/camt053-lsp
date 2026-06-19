# Security Policy

The camt053-lsp maintainers take the security of this project seriously. This
document explains which versions receive security updates and how to report a
vulnerability responsibly. camt053-lsp is the Language Server (LSP) companion to
the core `camt053` library, providing diagnostics, completion, and hover for
authoring reversing-entry data.

## Supported Versions

Security fixes are applied to the latest released minor version. While the
project is in its `0.0.x` series, only the most recent release line receives
security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.0.x   | :white_check_mark: |
| < 0.0.1 | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.**

We support coordinated disclosure. To report a vulnerability, use either of the
following private channels:

- **GitHub Security Advisories** (preferred): open a private report via the
  repository's
  [Security tab → "Report a vulnerability"](https://github.com/sebastienrousseau/camt053-lsp/security/advisories/new).
- **Email**: contact the maintainer at
  [sebastian.rousseau@gmail.com](mailto:sebastian.rousseau@gmail.com).

When reporting, please include as much of the following as possible:

- A description of the vulnerability and its potential impact.
- Steps to reproduce, or a proof-of-concept.
- The affected version(s) and environment (Python version, OS).
- Any known mitigations or workarounds.

## Response Timeline

We aim to meet the following targets, on a best-effort basis:

| Stage                     | Target                          |
| ------------------------- | ------------------------------- |
| Acknowledge receipt       | Within 3 business days          |
| Initial assessment        | Within 7 business days          |
| Fix or mitigation plan    | Within 30 days of confirmation  |
| Public disclosure         | Coordinated, after a fix ships  |

We will keep you informed of progress throughout the process and will credit
reporters in the advisory unless anonymity is requested.

## Scope

The following are in scope:

- The `camt053-lsp` Language Server (LSP) as published in this repository,
  including its diagnostics, completion, and hover features for authoring
  reversing-entry data, and the way it consumes the core `camt053` library.
- Parsing and validation paths for the data files the server processes,
  including JSON / JSONC handling and any path-traversal handling.
- Input validation for IBAN, BIC, LEI, currency, and reason-code data surfaced
  through the server.

The following are generally out of scope:

- Vulnerabilities in third-party dependencies (please report those upstream;
  we will track and update affected dependencies via Dependabot).
- Issues requiring a compromised host, malicious local configuration, or
  physical access.
- Denial of service caused by intentionally malformed, multi-gigabyte inputs
  beyond documented usage.

Thank you for helping keep camt053-lsp and its users safe.
