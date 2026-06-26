#!/usr/bin/env bash
# Report the version of every camt053 suite package across all four surfaces
# (local pyproject, latest git tag, GitHub release, PyPI) and flag any drift.
#
# Read-only: makes no changes. Exit code 0 = all in sync, 1 = drift detected.
#
# Usage:
#   scripts/suite-status.sh            # human table + drift check
#   SUITE_DIR=~/code scripts/suite-status.sh
#
# Env:
#   SUITE_DIR  Parent directory holding the sibling repo clones.
#              Defaults to the parent of this repository.
#   OWNER      GitHub owner/org (default: sebastienrousseau).
set -euo pipefail

OWNER="${OWNER:-sebastienrousseau}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUITE_DIR="${SUITE_DIR:-$(dirname "$REPO_ROOT")}"

# Core first (dependency order); the rest are leaves.
REPOS=(camt053 camt053-lsp camt053-mcp camt053-writer-xlsx camt053-loader-mt940)

pyproject_version() {  # $1 = repo dir
  [ -f "$1/pyproject.toml" ] || { echo "-"; return; }
  grep -m1 -E '^version *= *"' "$1/pyproject.toml" | sed -E 's/.*"([^"]+)".*/\1/'
}

pypi_version() {  # $1 = package name
  curl -fsS -m 20 "https://pypi.org/pypi/$1/json" 2>/dev/null \
    | python3 -c 'import sys,json; print(json.load(sys.stdin)["info"]["version"])' \
    2>/dev/null || echo "-"
}

gh_release() {  # $1 = repo
  gh release view --repo "$OWNER/$1" --json tagName --jq '.tagName' 2>/dev/null \
    | sed 's/^v//' || echo "-"
}

latest_tag() {  # $1 = repo
  git ls-remote --tags "https://github.com/$OWNER/$1.git" 2>/dev/null \
    | sed -E 's#.*refs/tags/##' | grep -v '\^{}' | sed 's/^v//' \
    | sort -V | tail -1 || echo "-"
}

printf '%-26s %-10s %-10s %-12s %-8s\n' "REPO" "pyproject" "tag" "ghRelease" "PyPI"
printf '%-26s %-10s %-10s %-12s %-8s\n' "----" "---------" "---" "---------" "----"

seen_versions=""
drift=0
for r in "${REPOS[@]}"; do
  local_v="$(pyproject_version "$SUITE_DIR/$r")"
  tag_v="$(latest_tag "$r")"
  rel_v="$(gh_release "$r")"
  pypi_v="$(pypi_version "$r")"
  printf '%-26s %-10s %-10s %-12s %-8s\n' "$r" "$local_v" "${tag_v:--}" "${rel_v:--}" "$pypi_v"
  for v in "$local_v" "$pypi_v"; do
    [ "$v" = "-" ] && continue
    seen_versions="$seen_versions $v"
  done
done

uniq_versions="$(echo "$seen_versions" | tr ' ' '\n' | sed '/^$/d' | sort -u)"
n="$(echo "$uniq_versions" | grep -c . || true)"
echo
if [ "$n" -le 1 ]; then
  echo "✓ Suite in sync at version: $(echo "$uniq_versions" | tr -d '\n')"
else
  echo "✗ VERSION DRIFT across the suite: $(echo "$uniq_versions" | tr '\n' ' ')"
  drift=1
fi
exit "$drift"
