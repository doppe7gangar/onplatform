#!/usr/bin/env bash
# Installs the skills into ~/.claude/skills, for every Claude Code project.
#
# Safest: download, read, then run.
#     curl -fsSLO https://github.com/doppe7gangar/onplatform/releases/download/v1.0.0/install.sh
#     less install.sh
#     bash install.sh
#
# Options:
#     --dry-run         show what would change, and change nothing
#     --rollback        put back the skills as they were before the last install
#     --version TAG     install another release (default: the one this script is for)
#     --checks          also install Playwright, for the design checks
#     --force           install even though the onplatform plugin is installed
#
# What it does: fetches the release into ~/.onplatform, checks it is the exact
# commit this script was published with, saves your current copies of the
# five skills to ~/.claude/skills/.onplatform-backups/<time>/, then puts the new
# ones in place. Other skills you have are not touched. If you edited one
# of the five yourself, it says so before replacing it; your edit is in
# the backup either way.

set -euo pipefail

REPO="${ONPLATFORM_REPO:-https://github.com/doppe7gangar/onplatform}"
VERSION="v1.0.0"
# The commit the release above points at. A tag can be moved; a commit
# can't, so this is what's checked. Filled in when the release is made.
COMMIT=""
SRC="${ONPLATFORM_DIR:-$HOME/.onplatform}"
DEST="$HOME/.claude/skills"
BACKUPS="$DEST/.onplatform-backups"
STAMP_FILE="$DEST/.onplatform-installed"
SKILLS="ui-kit-for-android design-workflow hig-guide motion-for-apple-platforms ui-kit-for-apple-platforms"

DRY=0; ROLLBACK=0; CHECKS=0; FORCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --rollback) ROLLBACK=1 ;;
    --checks) CHECKS=1 ;;
    --force) FORCE=1 ;;
    --version) shift; VERSION="${1:?--version needs a tag, e.g. v1.0.0}"; COMMIT="" ;;
    -h|--help) sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1 (try --help)"; exit 2 ;;
  esac
  shift
done

say() { printf '%s\n' "$*"; }
sha256() { if command -v shasum >/dev/null; then shasum -a 256; else sha256sum; fi; }
fingerprint() {  # one hash over every file's content, for spotting local edits
  (cd "$1" && find . -type f ! -name '.DS_Store' ! -path '*/__pycache__/*' -print0 \
     | sort -z | xargs -0 cat 2>/dev/null | sha256 || true)
}

if [ "$ROLLBACK" = 1 ]; then
  last=$(ls -1d "$BACKUPS"/*/ 2>/dev/null | sed 's#/$##' | grep -v '\.restored$' | sort | tail -1 || true)
  [ -n "$last" ] || { say "No backup to roll back to in $BACKUPS."; exit 1; }
  say "Rolling back to the skills saved at $(basename "$last")"
  for s in $SKILLS; do
    if [ -d "$last/$s" ]; then
      [ "$DRY" = 1 ] && { say "  would restore $s"; continue; }
      rm -rf "${DEST:?}/$s.onplatform-new"
      cp -R "$last/$s" "$DEST/$s.onplatform-new"
      rm -rf "${DEST:?}/$s"
      mv "$DEST/$s.onplatform-new" "$DEST/$s"
      say "  restored $s"
    elif [ -d "$DEST/$s" ] && [ -f "$last/.absent-$s" ]; then
      [ "$DRY" = 1 ] && { say "  would remove $s (it wasn't installed before)"; continue; }
      rm -rf "${DEST:?}/$s"; say "  removed $s (it wasn't installed before)"
    fi
  done
  if [ "$DRY" = 0 ]; then
    if [ -f "$last/.installed" ]; then cp "$last/.installed" "$STAMP_FILE"; else rm -f "$STAMP_FILE"; fi
    # Used up: the next rollback goes one step further back.
    mv "$last" "$last.restored"
  fi
  exit 0
fi

# The plugin brings the same five skills. With both, every skill loads twice.
plugin_installed() {
  local f
  for f in "$HOME/.claude/plugins/installed_plugins.json" "$HOME/.claude/settings.json"; do
    [ -f "$f" ] && grep -q '"onplatform@' "$f" && return 0
  done
  return 1
}
if [ "$FORCE" = 0 ] && plugin_installed; then
  say "STOP: the onplatform plugin is already installed in Claude Code, and it brings"
  say "these five skills. Installing them here as well would load every skill twice."
  say "Nothing was installed. Keep the plugin (/plugin updates it), or remove it"
  say "with /plugin first. bash install.sh --force installs anyway."
  exit 1
fi

command -v git >/dev/null || { say "git is needed. On a Mac: xcode-select --install"; exit 1; }

# 1. Fetch the release.
if [ -d "$SRC/.git" ]; then
  say "Fetching $VERSION into $SRC"
  git -C "$SRC" fetch --quiet --depth 1 origin "refs/tags/$VERSION:refs/tags/$VERSION" \
    || git -C "$SRC" fetch --quiet --depth 1 origin "$VERSION"
else
  say "Downloading $VERSION to $SRC"
  git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$VERSION" "$REPO" "$SRC"
fi
git -C "$SRC" -c advice.detachedHead=false checkout --quiet "$VERSION"
got=$(git -C "$SRC" rev-parse HEAD)

# 2. Check it is the release this script was published with.
if [ -n "$COMMIT" ]; then
  [ "$got" = "$COMMIT" ] || { say "STOP: $VERSION is commit $got, but this script expects $COMMIT."
                              say "Nothing was installed. Re-download install.sh from the release page."; exit 1; }
  say "Verified: $VERSION is commit ${got:0:12}"
else
  say "Installing $VERSION at commit ${got:0:12} (not checked against a pinned commit)"
fi

# 3. Compare with what's there now.
mkdir -p "$DEST"
changes=0
for s in $SKILLS; do
  new="$SRC/.claude/skills/$s"
  if [ ! -d "$DEST/$s" ]; then
    say "  $s: new"; changes=1
  elif diff -rq -x '__pycache__' -x '.DS_Store' "$DEST/$s" "$new" >/dev/null 2>&1; then
    say "  $s: already up to date"
  else
    n=$( (diff -rq -x '__pycache__' -x '.DS_Store' "$DEST/$s" "$new" 2>/dev/null || true) | wc -l | tr -d ' ')
    say "  $s: $n file(s) differ"; changes=1
    if [ -f "$STAMP_FILE" ] && grep -q "^skill $s " "$STAMP_FILE"; then
      was=$(grep "^skill $s " "$STAMP_FILE" | cut -d' ' -f3)
      now=$(fingerprint "$DEST/$s" | cut -d' ' -f1)
      [ "$was" = "$now" ] || say "    you have edited $s since it was installed; your version goes in the backup"
    fi
  fi
done

if [ "$DRY" = 1 ]; then say "Dry run: nothing changed."; exit 0; fi
if [ "$changes" = 0 ]; then say "Nothing to do."; else

  # 4. Back up, then swap each skill in.
  stamp=$(date +%Y%m%d-%H%M%S)
  backup="$BACKUPS/$stamp"; i=2
  while [ -e "$backup" ] || [ -e "$backup.restored" ]; do backup="$BACKUPS/$stamp-$i"; i=$((i + 1)); done
  mkdir -p "$backup"
  if [ -f "$STAMP_FILE" ]; then cp "$STAMP_FILE" "$backup/.installed"; fi
  for s in $SKILLS; do
    if [ -d "$DEST/$s" ]; then cp -R "$DEST/$s" "$backup/$s"; else touch "$backup/.absent-$s"; fi
  done
  for s in $SKILLS; do
    rm -rf "${DEST:?}/$s.onplatform-new"
    cp -R "$SRC/.claude/skills/$s" "$DEST/$s.onplatform-new"
    rm -rf "${DEST:?}/$s"
    mv "$DEST/$s.onplatform-new" "$DEST/$s"
  done
  {
    echo "version $VERSION $got"
    for s in $SKILLS; do echo "skill $s $(fingerprint "$DEST/$s" | cut -d' ' -f1)"; done
  } > "$STAMP_FILE"
  say "Installed. Your previous skills are in $backup"
  say "Undo with: bash install.sh --rollback"
fi

if [ "$CHECKS" = 1 ]; then
  say "Installing Playwright for the design checks"
  if python3 -m pip install --quiet playwright pillow 2>/dev/null \
     || python3 -m pip install --quiet --user playwright pillow 2>/dev/null; then
    python3 -m playwright install chromium
  else
    say "pip refused (common with Homebrew's Python). Use a virtual environment:"
    say "  python3 -m venv ~/.onplatform-env && source ~/.onplatform-env/bin/activate"
    say "  pip install playwright pillow && python -m playwright install chromium"
  fi
fi

say ""
say "Start Claude Code in any folder (claude) and describe what you want."
