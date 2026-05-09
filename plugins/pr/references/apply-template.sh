#!/bin/sh
# apply-template.sh — POSIX shell template for /pr:deslop apply.sh.
#
# The skill copies this file to `.git/deslop/<ts>-<pid>/apply.sh` per
# run, substituting the placeholders below before writing it. It is
# the single artifact the user runs to apply the proposed fixups.
#
# Substituted by the skill at materialization time (Step 8):
#   __DESLOP_TS_PID__       — directory name (e.g. `20260509-110825Z-1234`)
#   __REGISTRY_PATH__       — built-in or `--taxonomy=<path>` source
#   __REGISTRY_SHA256__     — SHA-256 of the registry at materialize time
#   __BASELINE_SHA__        — trunk SHA locked at Step 1
#   __TRUNK_REF__           — `origin/<trunk>` for force-with-lease reminders
#
# Idempotency:
#   * Each step writes `.checkpoint/<NNNN>.done` on success. Re-runs
#     skip completed steps. To force re-application of a single step,
#     remove its checkpoint file.
#   * Patches are applied per target SHA, in lexical order of the
#     numbered patch files. All `.patch` files for one target SHA are
#     applied to the working tree before the single `git commit
#     --fixup=<target-sha>` for that target.
#   * Reword messages are pre-staged in each fixup commit's body
#     with an `amend! <subject>` prefix line; autosquash strips the
#     prefix and uses the remainder as the new commit message.
#     `reword-map.tsv` records the mapping for audit/provenance only.
#
# Stages explicit paths only — never `git add -A` / `git add .` per
# `plugins/commit/commands/commit.md:181-191` (rule line 187).
#
# Exit codes:
#   0  — all checkpointed steps complete.
#   1  — registry SHA-256 diverged since materialization (live registry
#        was edited between materialize and apply).
#   2  — clean-tree precondition failed (working tree dirty).
#   3  — `git apply` failed for a patch step; checkpoint not written.
#   4  — fixup commit creation failed (`git commit` rejected, e.g.
#        by a pre-commit hook).
#   5  — failed to write reword file or reword-map row.
#   6  — pre-commit / commit-msg hook rejected a fixup (do not bypass —
#        the user repairs and re-runs).

set -eu

run_dir=".git/deslop/__DESLOP_TS_PID__"
checkpoint_dir="$run_dir/.checkpoint"
mkdir -p "$checkpoint_dir"

# ── registry SHA-256 lock ─────────────────────────────────────────

current_sha256=$(sha256sum -- "__REGISTRY_PATH__" 2>/dev/null | awk '{print $1}')
if [ -z "$current_sha256" ]; then
    current_sha256=$(shasum -a 256 -- "__REGISTRY_PATH__" 2>/dev/null | awk '{print $1}')
fi

if [ -z "$current_sha256" ]; then
    echo "apply.sh: cannot compute SHA-256 of registry __REGISTRY_PATH__" >&2
    exit 1
fi

if [ "$current_sha256" != "__REGISTRY_SHA256__" ]; then
    echo "apply.sh: registry SHA-256 changed since materialization" >&2
    echo "  expected: __REGISTRY_SHA256__" >&2
    echo "  current:  $current_sha256" >&2
    echo "  re-run /pr:deslop to materialize a fresh patch series" >&2
    exit 1
fi

# ── clean-tree precondition ───────────────────────────────────────

if [ -n "$(git status --porcelain)" ]; then
    echo "apply.sh: working tree is dirty; commit or stash first" >&2
    git status --short >&2
    exit 2
fi

# ── per-step helper ───────────────────────────────────────────────

checkpoint_path() {
    printf '%s/%04d.done' "$checkpoint_dir" "$1"
}

is_done() {
    [ -f "$(checkpoint_path "$1")" ]
}

mark_done() {
    : > "$(checkpoint_path "$1")"
}

# ── patch application loop ────────────────────────────────────────
#
# For each target SHA, apply its diff patches (if any), then create a
# single fixup commit. The skill writes the patch files in numeric
# order; we group them by target SHA via the embedded SHA in the
# filename (`NNNN-fixup-<sha>-<finding-id>.patch`,
# `NNNN-amend-<sha>.patch`, `NNNN-reword-<sha>.txt`,
# `NNNN-drop-<sha>.note`).

step_num=0

for entry in "$run_dir"/[0-9]*; do
    [ -e "$entry" ] || continue

    base=$(basename -- "$entry")

    case "$base" in
        0000-*|0005-advisory.md)
            continue
            ;;
    esac

    step_num=$(( step_num + 1 ))

    if is_done "$step_num"; then
        continue
    fi

    case "$base" in
        *-fixup-*.patch|*-amend-*.patch)
            target_sha=$(echo "$base" | sed -E 's/^[0-9]+-(fixup|amend)-([0-9a-f]+)(-[^.]+)?\.patch$/\2/')
            if [ -z "$target_sha" ]; then
                echo "apply.sh: cannot extract target SHA from $base" >&2
                exit 3
            fi

            if ! git apply -- "$entry"; then
                echo "apply.sh: git apply failed on $base" >&2
                echo "  fix the patch (or remove it) and re-run" >&2
                exit 3
            fi

            paths=$(git diff --name-only)
            if [ -z "$paths" ]; then
                mark_done "$step_num"
                continue
            fi

            echo "$paths" | while IFS= read -r p; do
                [ -n "$p" ] && git add -- "$p"
            done

            if ! git commit --no-edit --fixup="$target_sha"; then
                echo "apply.sh: git commit --fixup=$target_sha failed" >&2
                echo "  if a hook rejected the commit, repair and re-run" >&2
                exit 6
            fi

            mark_done "$step_num"
            ;;

        *-reword-*.txt)
            target_sha=$(echo "$base" | sed -E 's/^[0-9]+-reword-([0-9a-f]+)\.txt$/\1/')
            if [ -z "$target_sha" ]; then
                echo "apply.sh: cannot extract target SHA from $base" >&2
                exit 5
            fi

            mkdir -p "$run_dir/reword"
            cp -- "$entry" "$run_dir/reword/${target_sha}.txt"

            subject_line=$(git -P log -1 --format='%s' "$target_sha" 2>/dev/null)
            if [ -z "$subject_line" ]; then
                echo "apply.sh: cannot resolve subject for $target_sha" >&2
                exit 5
            fi

            # Pre-stage the new message in the fixup commit body.
            # Autosquash strips the `amend! <subject>` prefix line and
            # uses the rest of the body as the new commit message —
            # no editor invocation, no shim required.
            msg_tmp=$(mktemp "$run_dir/.amend-msg.XXXXXX")
            printf 'amend! %s\n\n' "$subject_line" > "$msg_tmp"
            cat -- "$entry" >> "$msg_tmp"

            map_row=$(printf 'amend! %s\t%s\treword/%s.txt' \
                "$subject_line" "$target_sha" "$target_sha")
            echo "$map_row" >> "$run_dir/reword-map.tsv"

            if ! git commit --allow-empty -F "$msg_tmp"; then
                rm -f -- "$msg_tmp"
                echo "apply.sh: git commit reword for $target_sha failed" >&2
                echo "  if a hook rejected the commit, repair and re-run" >&2
                exit 4
            fi

            rm -f -- "$msg_tmp"
            mark_done "$step_num"
            ;;

        *-drop-*.note)
            target_sha=$(echo "$base" | sed -E 's/^[0-9]+-drop-([0-9a-f]+)\.note$/\1/')
            if [ -z "$target_sha" ]; then
                echo "apply.sh: cannot extract target SHA from $base" >&2
                exit 5
            fi

            map_row=$(printf 'drop\t%s\t%s' "$target_sha" "$base")
            echo "$map_row" >> "$run_dir/reword-map.tsv"

            mark_done "$step_num"
            ;;

        *)
            echo "apply.sh: unrecognized artifact $base — skipping" >&2
            mark_done "$step_num"
            ;;
    esac
done

echo "apply.sh: $step_num steps complete"
echo "apply.sh: fixup commits visible via: git log --oneline '__BASELINE_SHA__..HEAD'"
echo "apply.sh: to autosquash, run /pr:deslop --apply-rebase or:"
echo "          GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash __TRUNK_REF__"
