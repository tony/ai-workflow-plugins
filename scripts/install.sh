#!/usr/bin/env bash
#
# install.sh -- Install portable skills from ai-workflow-plugins
# to Codex CLI (~/.codex/skills/) and/or Gemini CLI (~/.gemini/skills/).
#
# Usage:
#   scripts/install.sh [OPTIONS]
#
# Options:
#   --target <codex|gemini|all>   Target platform (default: all)
#   --plugin <name>               Install only this plugin's skills
#   --dry-run                     Show what would be done, change nothing
#   --force                       Overwrite existing skills without prompting
#   -h, --help                    Show this help message

set -euo pipefail

# --- Constants -----------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGINS_DIR="$REPO_ROOT/plugins"

# Plugins excluded from installation (not portable)
EXCLUDED_PLUGINS="model-cli loom"

# Target directories
CODEX_SKILLS_DIR="$HOME/.codex/skills"
GEMINI_SKILLS_DIR="$HOME/.gemini/skills"

# --- Defaults ------------------------------------------------------------

TARGET="all"
DRY_RUN=0
FORCE=0
PLUGIN_FILTER=""

# --- Functions -----------------------------------------------------------

usage() {
  printf 'Usage: scripts/install.sh [OPTIONS]\n\n'
  printf 'Options:\n'
  printf '  --target <codex|gemini|all>   Target platform (default: all)\n'
  printf '  --plugin <name>               Install only this plugin'"'"'s skills\n'
  printf '  --dry-run                     Show what would be done, change nothing\n'
  printf '  --force                       Overwrite existing skills without prompting\n'
  printf '  -h, --help                    Show this help message\n'
  exit 0
}

log() {
  printf '%s\n' "$*"
}

warn() {
  printf 'warn: %s\n' "$*" >&2
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

is_excluded() {
  local plugin="$1"
  local excluded
  for excluded in $EXCLUDED_PLUGINS; do
    [ "$plugin" = "$excluded" ] && return 0
  done
  return 1
}

install_skill() {
  local skill_name="$1"
  local skill_source_dir="$2"
  local target_base_dir="$3"

  local target_dir="$target_base_dir/$skill_name"
  local target_file="$target_dir/SKILL.md"
  local source_file="$skill_source_dir/SKILL.md"

  if [ -f "$target_file" ] && [ "$FORCE" -eq 0 ]; then
    warn "skip: $target_file already exists (use --force to overwrite)"
    return 0
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    log "  [dry-run] $source_file -> $target_file"
    return 0
  fi

  mkdir -p "$target_dir"
  cp "$source_file" "$target_file"
  log "  installed: $target_file"
}

# --- Parse Arguments -----------------------------------------------------

while [ $# -gt 0 ]; do
  case "$1" in
    --target)
      [ -n "${2:-}" ] || die "--target requires an argument (codex, gemini, all)"
      TARGET="$2"
      shift 2
      ;;
    --plugin)
      [ -n "${2:-}" ] || die "--plugin requires a plugin name"
      PLUGIN_FILTER="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      die "unknown option: $1"
      ;;
  esac
done

# --- Validate Inputs -----------------------------------------------------

case "$TARGET" in
  codex|gemini|all) ;;
  *) die "invalid target: $TARGET (must be codex, gemini, or all)" ;;
esac

if [ ! -d "$PLUGINS_DIR" ]; then
  die "plugins directory not found at $PLUGINS_DIR"
fi

if [ -n "$PLUGIN_FILTER" ]; then
  [ -d "$PLUGINS_DIR/$PLUGIN_FILTER" ] || die "plugin not found: $PLUGIN_FILTER"
  is_excluded "$PLUGIN_FILTER" && die "plugin '$PLUGIN_FILTER' is excluded (not portable)"
fi

# --- Main ----------------------------------------------------------------

TARGETS=""
case "$TARGET" in
  codex)  TARGETS="$CODEX_SKILLS_DIR" ;;
  gemini) TARGETS="$GEMINI_SKILLS_DIR" ;;
  all)    TARGETS="$CODEX_SKILLS_DIR $GEMINI_SKILLS_DIR" ;;
esac

SKILL_COUNT=0

for target_dir in $TARGETS; do
  target_name=$(basename "$(dirname "$target_dir")")
  log "Installing to $target_dir ..."

  if [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$target_dir"
  fi

  for plugin_dir in "$PLUGINS_DIR"/*/; do
    [ -d "$plugin_dir" ] || continue
    plugin_name="$(basename "$plugin_dir")"

    is_excluded "$plugin_name" && continue
    [ -n "$PLUGIN_FILTER" ] && [ "$plugin_name" != "$PLUGIN_FILTER" ] && continue
    [ -d "$plugin_dir/skills" ] || continue

    for skill_dir in "$plugin_dir"/skills/*/; do
      [ -f "$skill_dir/SKILL.md" ] || continue
      skill_name="$(basename "$skill_dir")"
      install_skill "$skill_name" "$skill_dir" "$target_dir"
      SKILL_COUNT=$((SKILL_COUNT + 1))
    done
  done
done

if [ "$SKILL_COUNT" -eq 0 ]; then
  warn "no portable skills found"
  exit 0
fi

if [ "$DRY_RUN" -eq 1 ]; then
  log ""
  log "Dry run complete. No files were changed."
else
  log ""
  log "Done. Installed $SKILL_COUNT skill(s)."
fi
