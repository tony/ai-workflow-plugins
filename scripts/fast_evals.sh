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
# No -e on purpose: a failing case must be judged by its verdict and the pass
# must continue, unlike the scaffolds, which abort on the first error.
set -uo pipefail

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"

# The helpers carry a PEP 723 header, so honour it when uv is present rather
# than silently running them on whatever python3 happens to be first on PATH.
if command -v uv >/dev/null 2>&1; then
  PY_RUN=(uv run --script)
else
  PY_RUN=(python3)
fi
cd "$SELF_DIR/.."

LIST_ONLY=0
[[ "${1:-}" == "--list" ]] && LIST_ONLY=1

OUT="${FAST_EVAL_OUT:-evals/results/fast}"
THRESHOLD="${FAST_EVAL_THRESHOLD:-0.5}"
MAX_COST="${FAST_EVAL_MAX_COST:-25}"
# A haiku judge misreads a reply that opens by naming what it could not verify.
JUDGE="${FAST_EVAL_JUDGE:-sonnet}"
# Parallel runs share one rate limit and one machine; raise with care.
JOBS="${FAST_EVAL_JOBS:-1}"

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
    # Anchored: a case merely containing "neg" (03-negotiate-timeout) is not a
    # should-not-fire case.
    if [[ "$name" == *-neg-* ]]; then
      specs+=("$plugin|$name")
      continue
    fi
    [[ -z "$trigger" ]] && trigger="$name"
    # Prefer a case that asserts the skill fired. This is a routing tripwire,
    # and a case graded on the artifact instead fails for want of the write
    # tools it is never given, which says nothing about routing.
    if [[ -z "$routing_trigger" ]] && grep -hEqs '^[[:space:]]*tool:[[:space:]]*["'"'"']?Skill["'"'"']?[[:space:]]*$' \
      "$case_dir/case.yaml" "$case_dir"/graders/*.md 2>/dev/null; then
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
  FAST_EVAL_THRESHOLD="$THRESHOLD" "${PY_RUN[@]}" "$SELF_DIR/fast_evals_verdict.py" "$1"
}

# Durations outlive the results they came from: a completed case is skipped and
# an incomplete one is deleted, so without this cache every pending case looks
# equally cheap and longest-first ordering does nothing.
TIMINGS="$OUT/.timings.json"

record_timing() {
  FAST_EVAL_TIMINGS="$TIMINGS" "${PY_RUN[@]}" "$SELF_DIR/fast_evals_order.py" \
    --record "$1|$2" "$OUT/$1--$2/aggregate-result.json" 2>/dev/null || true
}

mkdir -p "$OUT"

# Resolve what a previous pass already settled, so an interrupted run costs
# only what it has left to do.
pending=()
failed=()
accounted=0
for spec in "${specs[@]}"; do
  plugin="${spec%%|*}"
  case_name="${spec##*|}"
  result="$OUT/$plugin--$case_name/aggregate-result.json"
  if [[ -s "$result" ]]; then
    verdict="$(verdict_for "$result")"
    case "$verdict" in
      pass)
        echo "skip  $plugin/$case_name (scored previously)"
        accounted=$(( accounted + 1 ))
        continue ;;
      incomplete*)
        echo "redo  $plugin/$case_name (${verdict#incomplete: })"
        record_timing "$plugin" "$case_name"
        rm -rf "$OUT/$plugin--$case_name" ;;
      *)
        failed+=("$plugin/$case_name -- ${verdict#fail: }")
        echo "FAIL  $plugin/$case_name (${verdict#fail: })"
        accounted=$(( accounted + 1 ))
        continue ;;
    esac
  fi
  pending+=("$spec")
done

run_case() {
  local plugin="${1%%|*}" case_name="${1##*|}"
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
}

if (( ${#pending[@]} > 0 )); then
  echo "Running ${#pending[@]} case(s), $JOBS at a time."
  # Longest first, so the ten-minute ensemble case starts before the
  # forty-second ones rather than straggling alone at the end.
  if (( JOBS > 1 )); then
    # Ordering is an optimisation, never a filter. Take the new order only when
    # the helper succeeded and returned every case it was given; anything else
    # keeps discovery order. Command substitution, not process substitution,
    # because the latter hides the helper's exit status.
    if ordered_out="$(printf '%s\n' "${pending[@]}" \
        | FAST_EVAL_OUT="$OUT" "${PY_RUN[@]}" "$SELF_DIR/fast_evals_order.py")"; then
      ordered=()
      while IFS= read -r spec; do
        [[ -n "$spec" ]] && ordered+=("$spec")
      done <<<"$ordered_out"
      if (( ${#ordered[@]} == ${#pending[@]} )); then
        pending=("${ordered[@]}")
      else
        echo "warn: ordering returned ${#ordered[@]} of ${#pending[@]} cases; keeping discovery order"
      fi
    else
      echo "warn: ordering helper failed; keeping discovery order"
    fi
  fi
  # Batches rather than a `wait -n` pool: macOS ships bash 3.2, which has no
  # `wait -n`, and a batch keeps the runner readable for the small win it gives
  # up.
  batch=()
  for spec in "${pending[@]}"; do
    run_case "$spec" &
    batch+=($!)
    if (( ${#batch[@]} >= JOBS )); then
      wait "${batch[@]}" 2>/dev/null || true
      batch=()
    fi
  done
  (( ${#batch[@]} > 0 )) && { wait "${batch[@]}" 2>/dev/null || true; }

  for spec in "${pending[@]}"; do
    plugin="${spec%%|*}"
    case_name="${spec##*|}"
    record_timing "$plugin" "$case_name"
    verdict="$(verdict_for "$OUT/$plugin--$case_name/aggregate-result.json")"
    accounted=$(( accounted + 1 ))
    if [[ "$verdict" == pass ]]; then
      echo "ok    $plugin/$case_name"
    else
      failed+=("$plugin/$case_name -- ${verdict#*: }")
      echo "FAIL  $plugin/$case_name ($verdict)"
    fi
  done
fi

# Guards the whole class of bug this runner has now hit twice: reporting success
# for work it never did.
if (( accounted != ${#specs[@]} )); then
  echo
  echo "internal error: accounted for $accounted of ${#specs[@]} cases; refusing to report a result"
  exit 1
fi

if (( ${#failed[@]} > 0 )); then
  echo
  echo "${#failed[@]} case(s) below threshold $THRESHOLD:"
  printf '  %s\n' "${failed[@]}"
  exit 1
fi
echo
echo "All ${#specs[@]} cases at or above threshold $THRESHOLD."
