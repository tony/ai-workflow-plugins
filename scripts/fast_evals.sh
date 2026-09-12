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

cd "$(dirname "$0")/.."

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
  for case_dir in "$eval_dir"/*/; do
    [[ -d "$case_dir" ]] || continue
    name="$(basename "$case_dir")"
    # A scaffolded case needs tool grants the tripwire does not hand out.
    [[ -f "$case_dir/scaffold.sh" ]] && continue
    if [[ "$name" == *neg* ]]; then
      specs+=("$plugin|$name")
    elif [[ -z "$trigger" ]]; then
      trigger="$name"
    fi
  done
  [[ -n "$trigger" ]] && specs+=("$plugin|$trigger")
done

if (( LIST_ONLY )); then
  printf '%s\n' "${specs[@]}"
  echo "${#specs[@]} cases"
  exit 0
fi

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
    if python3 -c "
import json, sys
score = json.load(open('$result'))['aggregates']['overallScore']
sys.exit(0 if score >= $THRESHOLD else 1)
" 2>/dev/null; then
      echo "skip $plugin/$case_name (scored previously)"
    else
      failed+=("$plugin/$case_name")
      echo "FAIL $plugin/$case_name (scored previously)"
    fi
    continue
  fi
  if ! env -u ANTHROPIC_API_KEY claude plugin eval "plugins/$plugin" \
      --case "$case_name" \
      --ablation none \
      --runs 1 \
      --judge-model "$JUDGE" \
      --threshold "$THRESHOLD" \
      --max-cost-usd "$MAX_COST" \
      --trust-plugin \
      --no-publish \
      --output-dir "$OUT/$plugin--$case_name" \
      >"$OUT/$plugin--$case_name.log" 2>&1; then
    failed+=("$plugin/$case_name")
    echo "FAIL $plugin/$case_name"
  else
    echo "ok   $plugin/$case_name"
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
