# Evals

Three separate things live here, and they answer different questions.

- `cases/` — a prompt corpus for `scripts/skill_evals.py check`, which scores
  routing offline with TF-IDF. No model calls, so it runs in CI on every pull
  request.
- `routing-*/` — cross-plugin cases that load two competing plugins and check
  which skill wins. These call a model.
- `results/` — run output. Generated, ignored, safe to delete.

Per-skill cases live beside their plugin, in `plugins/<name>/evals/`.

## The fast suite

`scripts/fast_evals.sh` is a routing tripwire: every should-not-fire case plus
one trigger case per plugin. It answers "did routing break", not "is the answer
good", so it runs one arm and one run per case.

```console
$ scripts/fast_evals.sh --list
```

prints the selection and spends nothing.

```console
$ scripts/fast_evals.sh
```

runs it.

### What it costs

Measured over a full pass of 52 cases:

- **62 minutes** wall clock, run serially
- **$19** of API-equivalent usage
- **43 s** median per case, 69 s mean

Raising `FAST_EVAL_JOBS` cuts the wall clock but not the cost.

The spread matters more than the mean. One ensemble case (`weave`) takes ten
minutes on its own — a sixth of the total — while half the suite finishes inside
45 seconds. Budget for the tail, not the average.

### Reading a verdict

Each case resolves to one of three states, decided by
`scripts/fast_evals_verdict.py`:

- **pass** — complete, no run errors, and every grader asserting a Skill
  invocation passed.
- **fail** — a routing grader did not pass, or the score is below
  `FAST_EVAL_THRESHOLD` (default `0.5`).
- **incomplete** — the run was interrupted or errored. The case is rerun rather
  than cached, because a stored verdict otherwise reports the suite green on
  grading that never finished.

A routing grader is judged on its own rather than folded into the score. A
routing case usually pairs one such grader with one grading the answer, so at a
0.5 threshold the answer alone would keep a broken route green — which is the
one thing this suite exists to catch.

### Resuming

A pass reuses any verdict already stored under `results/fast/`, so an
interrupted run costs only what it has left to do. Delete a case's directory to
force it to run again, and delete `results/fast/` entirely after changing the
judge model or a rubric — **a stored verdict outlives the configuration that
produced it.**

### Knobs

- `FAST_EVAL_THRESHOLD` — per-case floor, default `0.5`.
- `FAST_EVAL_JUDGE` — judge model, default `sonnet`. Do not lower this. A
  haiku-tier judge reads a reply that opens by naming what it could not verify
  as a refusal, and hid three real failures here.
- `FAST_EVAL_MAX_COST` — per-case ceiling, default `25`.
- `FAST_EVAL_OUT` — output directory, default `evals/results/fast`.
- `FAST_EVAL_JOBS` — cases in flight, default `1`. Parallel runs share one rate
  limit and one machine, and each is a full model session, so raise this in
  small steps and watch memory. With it above 1 the pending cases are ordered
  longest-first, so the ten-minute ensemble case starts before the
  forty-second ones instead of straggling alone at the end.

### Which case becomes a plugin's trigger

The first that is not a negative, does not carry a `scaffold.sh`, and defines a
case. Two exclusions earn their keep:

A scaffolded case needs tool grants the tripwire does not hand out, so it
belongs to the per-plugin suites instead. And a directory is only a case when it
holds a `case.yaml` or a `prompt.md` — an eval run writing to its default
location creates `evals/results/`, which would otherwise be picked up as one.

Among the eligible cases, one asserting a Skill invocation wins. That is what a
routing tripwire measures, and a case graded on the artifact its ensemble writes
fails for want of write tools it is never given.

## Cross-plugin routing cases

A `plugins` entry in `case.yaml` names directories, resolved relative to the
case directory, and every entry must sit under a containment root. For a case
inside a plugin that root is the enclosing plugin — so a case under
`plugins/model-cli/evals/` can only reach plugins nested inside `model-cli`, and
never a sibling. For a case outside any plugin the root is the directory the run
targets, which is why these sit here and spell their entries
`../../plugins/<name>`.

```console
$ claude plugin eval . \
    --eval-dir evals \
    --case 'routing-*' \
    --ablation with-without \
    --runs 3
```

Keep the `--case` filter. Targeting the repository root walks the whole tree, so
without it the run also discovers every suite under `plugins/*/evals/` and
evaluates the entire marketplace; a cost ceiling is what stops it.

Assert three things, and the third is what makes it a routing test rather than a
trigger test: the expected skill fired, the competing plugin's skills did not,
and the reply engages with the request. Mirror the pair — a case that only
checks "gh wins on a bug report" is also passed by a plugin that fires on
everything.

## Scheduled runs

`.github/workflows/evals-scheduled.yml` runs the fast suite weekly and on
demand. It needs a `CLAUDE_CODE_OAUTH_TOKEN` secret; without one the job fails
at the eval step.
