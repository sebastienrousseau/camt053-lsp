# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
# Rendered by `make demo` (VHS: https://github.com/charmbracelet/vhs), which
# runs it under `poetry run` so the commands resolve to this checkout. It
# shows the server's command line and the helpers it calls on every edit,
# run against the records in examples/.

Output .github/demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 640
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms

Hide
Type "export PS1='$ ' && clear"
Enter
Show

Type "camt053-lsp --help"
Enter
Wait@60s /\$$/
Sleep 2s

Type "python examples/01_compute_diagnostics.py"
Enter
Wait@60s /\$$/
Sleep 3s

Type "python examples/05_code_actions.py"
Enter
Wait@60s /\$$/
Sleep 4s
