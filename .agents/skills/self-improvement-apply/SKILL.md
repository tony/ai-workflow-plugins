---
name: self-improvement-apply
description: >-
  Use when applying accepted self-improvement sweep findings to skills as
  individually gated edits and commits.
disable-model-invocation: true
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "AskUserQuestion", "Task"]
metadata:
  argument-hint: "[<finding id>...] [--dry-run]"
  source: "plugins/self-improvement/skills/apply/SKILL.md"
---

# this skill

Land what the sweep proved. The ledger already carries the evidence
and the change class per finding; this skill turns each one into the
smallest edit that removes the gap, behind the gates that catch a bad
one.

Invoked by name only: it edits the `SKILL.md` files that route the
whole catalog, and a bad edit there degrades skills that were working.

## The rule that makes this safe

```
NO EDIT WITHOUT A LEDGER ENTRY
```

Every edit traces to a finding with a ratio, a spread, a window, and a verdict.
An improvement noticed while working here is not in scope — it has no
usage evidence, which is exactly what separates this skill from
rewriting prose because it could read better.

Recompute the ledger key the sweep recorded — the catalog's `HEAD` and
the finding-set digest. A mismatch means the catalog moved since the
sweep: sweep again rather than apply a picture that no longer holds.

## `$ARGUMENTS` contract

Non-flag text selects finding ids; empty takes every accepted finding
in the ledger, in the order the ledger ranked them.

| Flag | Default | Effect |
|---|---|---|
| `--dry-run` | off | Show the edits and the gates each would run, and stop before the first write. |

## Phase 0: Situational awareness

Read the project's conventions files for its commit format and its
quality checks, and confirm the tree is clean. A dirty tree halts:
mixing a catalog edit with unrelated work is how an unreviewable
commit gets made.

## Phase 1: Orchestration plan

Enter plan mode if the host supports it (Claude Code: `EnterPlanMode`;
Cursor / Codex / Gemini: `/plan` or `Shift+Tab`) and present, per
finding: the id, the smallest edit that removes the gap, the files it
touches, and the gate it must clear. Then the commit sequence.

Say plainly which findings you are **not** applying and why. A sweep
proposes more than a catalog should absorb at once, and the restraint
is the point.

Wait for approval, then exit plan mode.

## Phase 2: Edit, one finding at a time

Match the edit to the verdict the sweep recorded, not to the
reviewer's instinct:

- A **capability gap** grows behavior the skill did not have.
- A **trust gap** echoes behavior it already performs, so the reader
  can see it fired. This is usually one line and never a new mechanism.
- A **present but not binding** finding never gets another sentence
  restating the rule that already failed. It gets a checked output
  gate, a resolved-and-echoed value, or an argument.

Prefer the smallest shape that works: a default over an argument, an
argument over a new skill. A new skill is the last resort and needs
its marketplace entry, its README row, and a description that survives
the collision check.

Strip evidence before it lands. The ledger may quote absolute paths,
hostnames, and client names; a `SKILL.md`, a commit message, a pull
request body, and an issue may not.

## Phase 3: Gate each edit

Any edit that touches a `description` is gated on the catalog's own
routing checks before it is committed — the collision ceiling and
description limits are enforced there, and a description that reads
better while colliding with a sibling makes both skills worse.

```console
uv run scripts/skill_evals.py check
```

Feed the mined prompts back through the router to confirm the edit
moved the ranking the way the finding predicted.

```console
uv run scripts/skill_evals.py route "<a redacted prompt from the finding>"
```

Then the project's own gates as its conventions define them, plus
whatever regenerates derived manifests. A red gate stops the run at
that finding; report and hand back rather than pressing on.

## Phase 4: Commit

One finding, one commit, in the project's commit format, describing
the defect and the fix in the project's own terms. It does not cite
the finding id or the sweep — a future reader wants to know what was
wrong, not who noticed. The ledger holds that mapping.

When the `slop` plugin is installed, the `slop-scan` skill already defines the
one-finding-one-commit loop and its gate discipline; follow it rather
than inventing a second version. Without it, the rule is the whole of
it: one finding per commit, each behind its own green gate.

## Phase 5: Verify what you wrote

Skill prose is written in one pass and reviewed by reading, so it
carries contradictions that gates cannot see: a phase that promises
what another phase forbids, a flag documented as absolute that a panel
overrides, a handoff to a skill that cannot accept the input.

Before handing back, re-read the edits against the skills they landed
in and look specifically for those. When the host supports sub-agents,
run this as an independent adversarial pass rather than re-reading
your own work.

Findings from this pass are fixed before handing back, not left for a
later review. While the branch is unpushed, amend the commit that
introduced the defect so the history stays one-finding-one-commit;
once it is pushed, the fix lands as its own commit.

## Output contract

1. Hero block (1–3 lines): `N applied, M skipped` plus the branch.
2. `## Applied` — per finding: the edit, the gates it cleared, and its
   commit subject.
3. `## Skipped` — findings not applied and why, including any the plan
   deliberately held back.
4. `## Verification` — gate commands run and their results, and what
   the adversarial pass found and fixed.
5. End with an `ask-user-choice` panel: open a pull request, sweep
   again, or stop. In a non-interactive run, record the options and
   stop.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
