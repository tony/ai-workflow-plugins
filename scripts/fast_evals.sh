#!/usr/bin/env bash
# Routing tripwire: every should-not-fire case, plus one trigger case per
# plugin. Answers "did routing break", not "how good is the answer", so it
# runs one arm and one run per case.
#
#   scripts/fast_evals.sh            # run it
#   scripts/fast_evals.sh --list     # print the case list and exit
#
# Cases carrying a scaffold are skipped: they need per-case tool grants and a
# throwaway repository, which is the slow suite's job. Run those with the
# command in each plugin's eval directory.
#
# Requires a logged-in Claude Code on the runner. Budget roughly one minute
# and a few cents of API-equivalent usage per case.
set -uo pipefail

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SELF_DIR/.."

LIST_ONLY=0
[[ "${1:-}" == "--list" ]] && LIST_ONLY=1

OUT="${FAST_EVAL_OUT:-evals/results/fast}"
THRESHOLD="${FAST_EVAL_THRESHOLD:-0.5}"
MAX_COST="${FAST_EVAL_MAX_COST:-25}"
# A haiku judge misreads a reply that opens by naming what it could not verify.
JUDGE="${FAST_EVAL_JUDGE:-sonnet}"

specs=()
for eval_dir in plugins/*/evals; do
  [[ -d "$eval_dir" ]] || continue
  plugin="$(basename "$(dirname "$eval_dir")")"
  trigger=""
  routing_trigger=""
  for case_dir in "$eval_dir"/*/; do
    [[ -d "$case_dir" ]] || continue
    name="$(basename "$case_dir")"
    # Only a directory that defines a case is one. Running an eval with its
    # default output location creates evals/results/, which is not.
    [[ -f "$case_dir/case.yaml" || -f "$case_dir/prompt.md" ]] || continue
    # A scaffolded case needs tool grants the tripwire does not hand out.
    [[ -f "$case_dir/scaffold.sh" ]] && continue
    if [[ "$name" == *neg* ]]; then
      specs+=("$plugin|$name")
      continue
    fi
    [[ -z "$trigger" ]] && trigger="$name"
    # Prefer a case that asserts the skill fired. This is a routing tripwire,
    # and a case graded on the artifact instead fails for want of the write
    # tools it is never given, which says nothing about routing.
    if [[ -z "$routing_trigger" ]] && grep -rqs 'tool: Skill' "$case_dir"; then
      routing_trigger="$name"
    fi
  done
  [[ -n "$routing_trigger" ]] && trigger="$routing_trigger"
  [[ -n "$trigger" ]] && specs+=("$plugin|$trigger")
done

if (( LIST_ONLY )); then
  printf '%s\n' "${specs[@]}"
  echo "${#specs[@]} cases"
  exit 0
fi

# Without this every per-case log redirect fails, and each case is recorded as
# a failure without ever being run.
# A result passes only when it is complete, free of run errors, and every
# grader asserting a Skill invocation passed. An aggregate score cannot carry
# that alone: a routing case usually pairs one routing grader with one answer
# grader, so at a 0.5 threshold the answer keeps a broken route green.
verdict_for() {
  FAST_EVAL_THRESHOLD="$THRESHOLD" python3 "$SELF_DIR/fast_evals_verdict.py" "$1"
}

mkdir -p "$OUT"

echo "Fast suite: ${#specs[@]} cases, one run each, no ablation."
failed=()
for spec in "${specs[@]}"; do
  plugin="${spec%%|*}"
  case_name="${spec##*|}"
  # Already scored in a previous pass: reuse the verdict, so an interrupted run
  # resumes instead of paying for every case again. Delete the output
  # directory to force a re-run.
  result="$OUT/$plugin--$case_name/aggregate-result.json"
  if [[ -s "$result" ]]; then
    verdict="$(verdict_for "$result")"
    case "$verdict" in
      pass)
        echo "skip $plugin/$case_name (scored previously)"
        continue ;;
      incomplete*)
        echo "redo  $plugin/$case_name (${verdict#incomplete: })"
        rm -rf "$OUT/$plugin--$case_name" ;;
      *)
        failed+=("$plugin/$case_name -- ${verdict#fail: }")
        echo "FAIL $plugin/$case_name (${verdict#fail: })"
        continue ;;
    esac
  fi
  env -u ANTHROPIC_API_KEY claude plugin eval "plugins/$plugin" \
      --case "$case_name" \
      --ablation none \
      --runs 1 \
      --judge-model "$JUDGE" \
      --threshold "$THRESHOLD" \
      --max-cost-usd "$MAX_COST" \
      --trust-plugin \
      --no-publish \
      --output-dir "$OUT/$plugin--$case_name" \
      >"$OUT/$plugin--$case_name.log" 2>&1
  verdict="$(verdict_for "$result")"
  if [[ "$verdict" == pass ]]; then
    echo "ok    $plugin/$case_name"
  else
    failed+=("$plugin/$case_name -- ${verdict#*: }")
    echo "FAIL  $plugin/$case_name ($verdict)"
  fi
done

if (( ${#failed[@]} > 0 )); then
  echo
  echo "${#failed[@]} case(s) below threshold $THRESHOLD:"
  printf '  %s\n' "${failed[@]}"
  exit 1
fi
echo
echo "All ${#specs[@]} cases at or above threshold $THRESHOLD."
