---
name: spike-ratchet
description: >-
  Use when asked to spike, bake off, then spike again; rinse and repeat,
  keep spiking, converge on a design, and stop when nothing new fights back.
metadata:
  source: "plugins/spike/skills/ratchet/SKILL.md"
---

# this skill

Convergence harness. the `spike-probe` skill answers "does this path work?".
the `spike-bakeoff` skill answers "which path is best?". Neither answers "what
is the right design?" — that only emerges from hitting real code
several times and watching which parts keep fighting back. The ratchet
runs both in rounds until the design stops resisting.

This skill is invoked by name, never routed to on the model's
initiative: it runs multiple mutating rounds and (in `--replay`)
creates commits, so it must be user-explicit, not router-inferred.

## Core thesis

Across rounds the code is disposable and **the ledger is the
product**. Each round throws away its implementation and keeps what it
learned: which approaches the code rejected, which decisions are now
settled, which questions are still open.

A ratchet is worth running when the shape of the answer is unknown — a
port to another language, an API whose ergonomics only show up in use,
a subsystem where the first sketch is expected to be wrong. When one
approach is already clear, use the `spike-probe` skill. When two or three named
approaches compete once, use the `spike-bakeoff` skill.

## The Iron Rule

```
EVERY ROUND PRODUCES ZERO COMMITS
```

Inherited whole from the `spike-probe` skill, including its rationalization
table, and unchanged by round count: five rounds of exploration is
five times the reason not to put it in history. Rounds end in stashes;
commits happen only in `--replay`, after the final plan is approved.

**Red flag** unique to this skill: "round 3 is basically final, commit
it as a checkpoint so round 4 has a base." Round 4 starts from the
stash, and the ledger is the base.

## The ledger

One markdown file, written outside the working tree:

```
git rev-parse --path-format=absolute --git-common-dir
```

The ledger lives at `<that path>/spike/<goal-slug>.md`. That location
is load-bearing, not a preference: a ledger kept in the working tree
gets swallowed by the round's own `git stash push -u`, erased by
`git clean -xdf`, and shows up as an untracked file in every
`git status` the user reads. The common dir also resolves to the same
absolute path from every bakeoff worktree, so contenders and the main
checkout write to one file.

Announce the path in the Phase 1 brief, and append to whatever ledger
is already there rather than truncating it.

Each round appends one section:

- **Probed** — what this round built, and its stash SHA.
- **Stumbling blocks** — what fought back, per the `spike-probe` skill's
  definition. New ones only; repeats are marked as repeats.
- **Bakeoff** — contenders, winner, why, and which grafts were taken
  (omit when no bakeoff ran this round).
- **Locked** — decisions that will not be revisited, with the evidence
  that settled them.
- **Open** — questions carried into the next round.

Keep every entry to a line or two. The ledger is read by the next
round and by the final rewrite; it is not a transcript.

## `$ARGUMENTS` contract

Non-flag text is the goal, resolved by the same ladder as
the `spike-probe` skill — typed goal wins, empty mines the conversation,
provenance recorded in the brief.

| Flag | Default | Effect |
|---|---|---|
| `--rounds=<n>` | 3 | Cap on the rounds the ratchet runs on its own. It may stop earlier by converging; only an explicit choice from the closing panel takes it further. |
| `--replay` | off | At Phase 4, land the approved plan immediately instead of stopping at the panel, following the `spike-probe` skill Phase 6. Never applies to a round. |

## Phase 0: Situational awareness

the `spike-probe` skill Phase 0 once for the whole ratchet — conventions files, the
five gate buckets and CI split per
`references/verification-gates.md`, dirty-tree halt — plus:

1. Resolve the ledger path and read it if it already exists.
2. Confirm `git worktree` is usable, since any round may call a
   bakeoff.

## Phase 1: Orchestration plan

Enter plan mode if the host supports it (Claude Code: `EnterPlanMode`;
Cursor / Codex / Gemini: `/plan` or `Shift+Tab`) and present the
**ratchet brief**:

1. The goal, one line, with provenance.
2. What "converged" means for this goal — the demo or property the
   final design must satisfy, not just the first round's smoke check.
3. The round cap, and any rounds already in the ledger.
4. Discovered gate commands and the local-vs-CI split.
5. The ledger path.
6. The intended exit: clean rewrite, or landing plan.

Wait for approval, then exit plan mode. If plan mode is unavailable,
present the brief inline and proceed on confirmation. In a
non-interactive run, record the brief and proceed.

## Phase 2: A round

Repeat until Phase 3 says stop. Each round:

1. **Probe.** Follow the `spike-probe` skill Phases 2 through 4 against the goal
   as sharpened by the ledger's open questions: shortest path to
   proven, cheapest verification signal, `SPIKE:` markers, stumbling
   blocks, the exit gate, and a stash with a recorded SHA. A round
   borrows those phases, it does not invoke the whole skill — probe's
   Phase 0 already ran once in Phase 0 above, its Phase 1 brief is the
   ratchet brief you already approved, and its plan and replay phases
   belong to the ratchet's exit. This is also why `--replay` never
   reaches a round.
2. **Branch on what fought back.** A stumbling block that admits two
   or more genuinely different resolutions is what the `spike-bakeoff` skill
   exists for — run it on those resolutions as the contender list. A
   stumbling block with one obvious fix is not a bakeoff; fold it into
   the next probe.
3. **Re-probe the graft.** Grafts leave a bakeoff unproven in
   combination. When a round takes them, the ratchet seeds the next
   round's tree itself — apply the winner's stash, then the graft
   hunks — and that round probes from there, so the proving check runs
   on the tree actually chosen. Seeding is the ratchet's own step rather
   than a probe invocation, which is why probe's dirty-tree halt does
   not fire on a tree the ratchet deliberately built. A graft that fails
   the check is dropped and recorded as dropped.
4. **Record.** Append the round's ledger section before starting the
   next one. A round that ends without its ledger entry written did
   not happen — the next round has no other memory of it.

Except when carrying grafts, a round starts from a clean tree. What it
inherits from round N-1 is the ledger's locked decisions, not its code.

## Phase 3: Convergence test

Stop when any of these holds, and say which one in the report:

Test them in this order, because a repeats-only round satisfies more
than one:

- **Thrashing** — the round surfaced stumbling blocks, but every one
  was already recorded and decided in an earlier round. Repetition is
  evidence that more spiking cannot settle the question; stop and
  surface it rather than spending another round.
- **Converged** — the round surfaced no stumbling block at all.
- **Capped** — `--rounds` is exhausted. Report the still-open
  questions plainly; a capped ratchet is an honest partial result, not a
  failure to hide.

Otherwise start the next round from the ledger's open questions.

## Phase 4: Exit

The surviving artifacts are the ledger, the final round's stash SHA,
and every earlier round's stash SHA. Offer the two exits:

- **Clean rewrite** — write the final implementation from the ledger's
  locked decisions rather than from the accumulated code, keeping the
  final stash as reference and fallback. This is the right exit when
  the code carries the marks of rounds that were later abandoned.
- **Landing plan** — a commit-by-commit plan for the final stash, built
  as the `spike-probe` skill Phase 5, and landed under `--replay` as its
  Phase 6. This is the right exit when the last round's code is
  already what the design wants.

Recommend one and say why. Never drop earlier stashes — the ledger
cites them by SHA as the evidence for its locked decisions.

## Output contract

1. Hero block (1–3 lines): `✓ converged in <n> rounds` /
   `⚠ capped at <n> rounds` / `⚠ thrashing — stopped at round <n>` +
   the goal.
2. `## Rounds` — one block per round: what was probed, what fought
   back, bakeoff winner if any, what got locked.
3. `## Design` — the locked decisions as they now stand, read as a
   specification rather than a history. This is what the rewrite
   consumes.
4. `## Open` — questions the ratchet did not settle, and for a thrashing
   stop, why spiking cannot settle them.
5. `## Stashes` — table: round, stash message, **SHA**, restore
   command. Every round appears, and so does every contender a round's
   bakeoff stashed: a ratchet never runs bakeoff's own replay, so those
   stashes outlive it and belong in the accounting rather than in
   `git stash list` alone.
6. `## Next` — the recommended exit, and the landing plan when one was
   produced.
7. End with an `ask-user-choice` panel: rewrite from the ledger / land
   the final stash / run another round / stop and keep the ledger —
   unless already in plan mode or `--replay` was given. In a
   non-interactive run, record the question and default to stopping
   with the ledger kept.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
