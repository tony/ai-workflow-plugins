# Measurement Contract

Formulas, statistics discipline, counterfactual quality, and quality
guardrails for `/business:*`. The variable definitions here are the
only definitions — commands use them verbatim, never re-derive them.

## Net per-instance saving

```
S_inst = (t_manual - (t_ai + t_verify)) - (p_fail * t_rework)
```

- `t_manual` — baseline time per instance without the skill.
  Measured, not self-reported; see the counterfactual ladder.
- `t_ai` — AI-assisted time per instance, including failed and
  abandoned runs.
- `t_verify` — verification and review time. Always inside the task
  boundary.
- `p_fail` — probability the AI-assisted result needs rework.
- `t_rework` — time to rework a failed instance.

## Net over a period, and break-even

```
S_net = (N * S_inst) - C_build - (C_maint * periods)
```

```
N_breakeven = (C_build + C_maint * periods) / S_inst
```

- `N` — instances in the period. `C_build` — one-time skill build
  time. `C_maint` — maintenance time per period.
- Report break-even explicitly: the instance count at which the
  skill pays back its build and upkeep is more honest and more
  useful than an annualized headline.

## Org-wide projection

```
Annual_hours_saved = V * F * t * s * a * r
```

- `V` — addressable population: people whose work contains the task.
- `F` — instances per person per period.
- `t` — baseline time per instance (measured, not self-reported).
- `s` — savings rate net of the verification tax.
- `a` — adoption, strictly < 1.0, explicit input. License-holding
  and active use are different numbers; `a` means active use.
- `r` — realization, strictly < 1.0, explicit input. Scattered
  minutes rarely convert to capacity; `r` is the fraction of gross
  saved time that becomes usable capacity.

Refuse to default `a` or `r` to 1.0. If either is absent from the
assumptions register, stop and ask the user, then append the answer
as an ESTIMATED entry with rationale and owner before projecting.

Segment the population: addressable ⊃ served ⊃ realized. Reporting
only the addressable figure is the most common inflation — always
show all three segments.

## Statistics discipline

- Medians plus IQR, not means: task durations are right-skewed,
  roughly log-normal, and means chase the tail.
- Bootstrapped intervals for medians, BCa preferred. Percentile
  methods want roughly n ≥ 60 for stable coverage; small n gets wide
  intervals and honesty, not precision. Deterministic seed, recorded
  with the result.
- Fewer than ~12–20 paired observations: present the raw pairs, the
  median difference, and a wide interval, and label the result
  **DIRECTIONAL**. Never single-decimal percentages from 5 tasks.
- Exclude the novelty ramp window; measure steady state. State the
  excluded window in the run README.

## Counterfactual quality ladder

Best → worst. Label which rung every comparison sits on:

1. Self-A/B with tasks pre-specified before randomization.
2. Paired task design.
3. Pre-period cycle-time distribution.
4. Matched historical tasks.
5. Retrospective recall — weakest; always labeled as such.

## Quality guardrails

Time saved that degrades these is not savings. Track them alongside
any savings claim:

- Delivery lead time.
- Deployment / change frequency.
- Change-failure rate and rework, revert, and reopen rates.
- Review latency.
- PR-size drift.
- CI failure and retry rates.

Activity metrics — lines of code, commit counts, PR counts — never
stand alone; that is SPACE's core warning. They may appear only next
to a quality or outcome metric.
