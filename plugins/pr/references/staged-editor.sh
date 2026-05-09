#!/bin/sh
# staged-editor.sh — non-interactive GIT_EDITOR for /pr:deslop autosquash.
#
# git invokes GIT_EDITOR with the path to a temporary commit-message
# file. The file does not expose the target SHA in a parseable form,
# so this script reads the message-file's first line — which during an
# autosquash will be `fixup! <subject>` for diff fixups and
# `amend! <subject>` for `--fixup=reword:` and `--fixup=amend:`
# rewrites — and looks the target up in
# `${DESLOP_TS_PID}/reword-map.tsv`. If the lookup succeeds, the
# matching reword-message file's contents replace the editor's target.
# If no match (e.g., the commit doesn't need rewording — autosquash
# applies the original message), the editor exits 0 leaving the file
# unchanged, which preserves git's default behavior.
#
# Required environment:
#   DESLOP_TS_PID  — the per-run directory name (e.g. `20260509-110825Z-1234`)
#                    relative to `.git/deslop/`. Set by the SKILL.md
#                    invocation in Step 10.
#
# Required filesystem layout under `.git/deslop/${DESLOP_TS_PID}/`:
#   reword-map.tsv  — one row per reword target. Tab-separated columns:
#                       <autosquash-subject>  (verbatim, including leading `fixup! ` / `amend! `)
#                       <target-sha>          (full SHA)
#                       <reword-file>         (relative path under reword/, e.g. `reword/abc1234.txt`)
#   reword/         — directory of reword-message files.
#
# Exit codes:
#   0  — success (file updated or intentionally left as-is).
#   2  — required environment variable missing or run directory not found.
#   3  — map file missing or unreadable.
#   4  — failed to read or write the editor's target file.

set -eu

target_file=${1:-}
if [ -z "$target_file" ]; then
    echo "staged-editor.sh: no target file argument" >&2
    exit 2
fi

if [ -z "${DESLOP_TS_PID:-}" ]; then
    echo "staged-editor.sh: DESLOP_TS_PID not set" >&2
    exit 2
fi

run_dir=".git/deslop/${DESLOP_TS_PID}"
if [ ! -d "$run_dir" ]; then
    echo "staged-editor.sh: run dir $run_dir not found" >&2
    exit 2
fi

map_file="$run_dir/reword-map.tsv"
if [ ! -r "$map_file" ]; then
    echo "staged-editor.sh: $map_file not readable" >&2
    exit 3
fi

if [ ! -r "$target_file" ]; then
    echo "staged-editor.sh: $target_file not readable" >&2
    exit 4
fi

first_line=$(sed -n '1p' "$target_file")

reword_file=""
while IFS=$(printf '\t') read -r subject sha rel_path; do
    case "$subject" in
        '#'*) continue ;;
        '') continue ;;
    esac
    if [ "$subject" = "$first_line" ]; then
        reword_file="$run_dir/$rel_path"
        break
    fi
done < "$map_file"

if [ -z "$reword_file" ]; then
    exit 0
fi

if [ ! -r "$reword_file" ]; then
    echo "staged-editor.sh: reword file $reword_file not readable" >&2
    exit 3
fi

tmp=$(mktemp "${target_file}.deslop.XXXXXX")
cat "$reword_file" > "$tmp"
mv "$tmp" "$target_file"
