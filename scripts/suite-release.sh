#!/usr/bin/env bash
# Orchestrate a lockstep release of the whole camt053 suite.
#
# For each repo (core first): bump every version source, add a lockstep
# CHANGELOG entry, open a PR, wait for CI, squash-merge, then push a signed
# tag that triggers the repo's release.yml (PyPI + GitHub release + SBOMs).
#
# SAFE BY DEFAULT: prints the plan and changes nothing unless --yes is passed.
# Idempotent: repos already at the target version skip the bump; existing tags
# are not recreated — so re-running after a partial failure resumes cleanly.
#
# Usage:
#   scripts/suite-release.sh 0.0.8            # dry run (no writes)
#   scripts/suite-release.sh 0.0.8 --yes      # perform the release
#   scripts/suite-release.sh 0.0.8 --yes --repos camt053,camt053-lsp
#
# Env: SUITE_DIR (parent of the clones, default: parent of this repo),
#      OWNER (default sebastienrousseau).
set -euo pipefail

VERSION="${1:-}"
[ -z "$VERSION" ] && { echo "usage: $0 <version> [--yes] [--repos a,b]"; exit 2; }
shift || true
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+ ]] || { echo "bad version: $VERSION"; exit 2; }

DO=0
ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --yes) DO=1 ;;
    --repos) ONLY="$2"; shift ;;
    *) echo "unknown arg: $1"; exit 2 ;;
  esac
  shift
done

OWNER="${OWNER:-sebastienrousseau}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUITE_DIR="${SUITE_DIR:-$(dirname "$REPO_ROOT")}"
ALL_REPOS=(camt053 camt053-lsp camt053-mcp camt053-writer-xlsx camt053-loader-mt940)
if [ -n "$ONLY" ]; then IFS=',' read -r -a REPOS <<< "$ONLY"; else REPOS=("${ALL_REPOS[@]}"); fi

say()  { printf '\033[1m==>\033[0m %s\n' "$*"; }
run()  { if [ "$DO" = 1 ]; then eval "$*"; else printf '   [dry-run] %s\n' "$*"; fi; }

bump_versions() {  # $1=dir
  local d="$1"
  run "perl -i -pe 's/^version = \"[^\"]*\"/version = \"$VERSION\"/m' '$d/pyproject.toml'"
  while IFS= read -r f; do
    run "perl -i -pe 's/^__version__ = \"[^\"]*\"/__version__ = \"$VERSION\"/' '$f'"
  done < <(find "$d" -name '__init__.py' -not -path '*/tests/*' -not -path '*/.venv/*' 2>/dev/null)
  while IFS= read -r f; do
    run "perl -i -pe 's/^VERSION = \"[^\"]*\"/VERSION = \"$VERSION\"/' '$f'"
  done < <(find "$d" -name 'constants.py' -not -path '*/tests/*' -not -path '*/.venv/*' 2>/dev/null)
}

changelog_entry() {  # $1=dir $2=repo
  local cl="$1/CHANGELOG.md"
  [ -f "$cl" ] || return 0
  grep -q "^## \[$VERSION\]" "$cl" && { say "  CHANGELOG already has [$VERSION]"; return 0; }
  local today; today="$(date +%F)"
  local entry="## [$VERSION] - $today\n\n### Changed\n\n- **Version** — suite-wide lockstep bump to \`$VERSION\`. No functional changes.\n"
  run "perl -0777 -i -pe 's/(Semantic Versioning[^\n]*\n\n)/\${1}$entry\n/' '$cl'"
  local link="[$VERSION]: https://github.com/$OWNER/$2/releases/tag/v$VERSION"
  if grep -qE '^\[[0-9]+\.[0-9]+\.[0-9]+\]: ' "$cl"; then
    run "perl -i -pe 'print \"$link\\n\" if !\$d && /^\\[[0-9]+\\.[0-9]+\\.[0-9]+\\]: / and (\$d=1)' '$cl'"
  fi
}

notes_file() {  # $1=dir $2=repo  (repos with a releases/ dir need vX.Y.Z.md)
  local d="$1" r="$2"
  [ -d "$d/releases" ] || return 0
  [ -f "$d/releases/v$VERSION.md" ] && return 0
  run "printf '# %s v%s\n\nSuite-wide lockstep release aligned to the camt053 suite v%s line. No functional changes in this package.\n' '$r' '$VERSION' '$VERSION' > '$d/releases/v$VERSION.md'"
}

release_one() {  # $1=repo
  local r="$1" d="$SUITE_DIR/$1"
  say "[$r]"
  [ -d "$d/.git" ] || { echo "   SKIP: $d is not a git clone"; return 0; }
  ( cd "$d"
    git rev-parse --abbrev-ref HEAD | grep -qx main || { echo "   SKIP: not on main"; return 0; }
    [ -z "$(git status --porcelain)" ] || { echo "   SKIP: working tree dirty"; return 0; }
    git fetch -q origin
    local cur; cur="$(grep -m1 -E '^version *= *"' pyproject.toml | sed -E 's/.*"([^"]+)".*/\1/')"
    if [ "$cur" != "$VERSION" ]; then
      say "  bump $cur -> $VERSION + open PR"
      run "git checkout -b release/v$VERSION"
      bump_versions "$d"; changelog_entry "$d" "$r"; notes_file "$d" "$r"
      # Keep poetry.lock in sync — bumping the version invalidates its
      # content hash (poetry 2.x), which otherwise fails the release SBOM job.
      if [ -f poetry.lock ] && command -v poetry >/dev/null; then
        say "  refresh poetry.lock"; run "poetry lock"
      fi
      run "git add -A"
      run "git commit -S -m 'chore(release): bump to $VERSION (suite lockstep)'"
      run "git push -u origin release/v$VERSION"
      run "gh pr create --base main --head release/v$VERSION --title 'chore(release): bump to $VERSION (suite lockstep)' --body 'Suite-wide lockstep bump to $VERSION. Automated by scripts/suite-release.sh.'"
      run "gh pr checks release/v$VERSION --watch"
      run "gh pr merge release/v$VERSION --squash --delete-branch"
      run "git checkout main && git pull -q origin main"
    else
      say "  already at $VERSION (skip bump)"
    fi
    if git ls-remote --tags origin "v$VERSION" | grep -q .; then
      say "  tag v$VERSION already exists (skip)"
    else
      say "  tag + push v$VERSION (triggers release.yml)"
      run "git checkout main && git pull -q origin main"
      run "git tag -s v$VERSION -m v$VERSION"
      run "git push origin v$VERSION"
    fi
  )
}

say "Suite release $VERSION  (mode: $([ "$DO" = 1 ] && echo APPLY || echo DRY-RUN))"
say "suite dir: $SUITE_DIR   repos: ${REPOS[*]}"
for r in "${REPOS[@]}"; do release_one "$r"; done
say "Done. Verify with: scripts/suite-status.sh"
