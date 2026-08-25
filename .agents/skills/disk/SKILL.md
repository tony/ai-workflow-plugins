---
name: disk
description: >-
  Use when disk space is low; find large directories, free space, decide if
  Claude sessions or npm cache are safe to remove, or shrink WSL.
metadata:
  source: "plugins/disk/skills/disk/SKILL.md"
---

# Disk

Find what is consuming a machine's disk, and reclaim it without losing
anything the user cannot get back.

the `disk-usage` skill runs the survey and classification read-only.
the `disk-reclaim` skill runs the full pipeline through to execution.

The failure mode this guards against is not missing some space. It is
deleting a directory whose name suggested it was a duplicate and which
turned out to hold the only copy of something. Every destructive step
is gated on a proof, and the proofs are specified rather than left to
judgment.

## Non-negotiables

**Never halt the environment.** `wsl --shutdown`, `wsl --terminate`,
VM stop commands, and container-runtime restarts are the user's to run.
They kill unsaved work across every shell and editor on the machine.
Print the command, say what it interrupts, and stop. Approval to delete
caches is not approval to terminate the environment.

**Never delete on the strength of a name.** `*-backup-*`, `.old`,
`.bak`, and `archive-*` carry no information about whether a copy is
redundant. Run the proof.

**Agent history is protected by default.** Reclaim from transcripts and
session stores only through the owning tool's own archival path, or by
proving one copy redundant against another.

**Report guest and host separately.** Space freed inside a virtual disk
is not space freed on the machine until the disk is compacted.

## Survey

Establish the layer structure before measuring anything. Read
`references/virtual-disks.md`.

Run `df -h` and identify every distinct filesystem. When one is a
virtual disk, locate its backing file on the host and compare the
file's allocated size against the used space reported inside it. The
difference is balloon, recoverable without deleting anything.

Then measure. Prefer `dust` with an explicit depth and minimum size
where available, falling back to `du`. Survey each filesystem
separately. Resolve symlinks before recording a size, so a
dotfiles-managed directory is not counted twice under two paths.

State the constraint in one line before any detail: which layer is
actually full, and how much headroom it has. When the host is critical
and the guest is comfortable, say so first — it changes which findings
matter.

## Classify

Assign every candidate above the size threshold to exactly one tier
from `references/candidate-catalog.md`. Default
to the highest tier that plausibly applies, and classify where content
is homogeneous rather than propagating a parent's tier to its children.

For each apparent duplicate, run the path-set comparison from
`references/redundancy-proofs.md` and record the
outcome as redundant, mergeable, conflicted, or unique. A `diff`
reporting no differing files proves nothing on its own — establish the
size of the intersection.

For agent history, read
`references/agent-history.md`. Determine each
tool's discovery glob and whether it maintains a state database, and
check for native compression support before considering any
hand-rolled compression.

For directories of upstream clones kept for reading, read
`references/study-repos.md`. Report huge clones,
clones that are not shallow, and build artifacts as three separate
groups, and verify no clone holds unpushed work.

## Orchestration plan

Enter plan mode before proposing anything destructive. In Claude Code
call `EnterPlanMode`; in Cursor, Codex, or Gemini use `/plan` or
`Shift+Tab`. Where plan mode is unavailable, the phase structure above
still applies — present the plan as text and wait for approval.

The plan states, per tier: what will be reclaimed, the proof that made
it safe, the expected recovery, and which layer that recovery lands on.
It separates what the agent will run from what only the user can run,
and names what is being left alone.

Group approvals by tier. Regenerable caches take one blanket approval.
Redundant copies are listed individually with their proof outcome.
Stale-but-unique data is decided per directory. Protected history
appears as an inventory, or as a compression proposal with its access
tradeoff stated plainly.

Never present compression as free. When a tool cannot read its own
compressed history, compression converts sessions from resumable to
archive-only — offer an age cutoff so recent sessions stay live. When a
tool can compress natively, propose enabling that instead.

Exit plan mode once approved.

## Reclaim

Work the approved plan in tier order, largest first within each tier.

Merges run before the deletions that depend on them. After each merge,
re-run the path-set comparison with arguments reversed and confirm the
source now holds nothing unique. Only then may the source be removed.

Prefer a tool's own prune or archive command over `rm`. It understands
its own reference counting and leaves the store consistent.

Stop and report rather than improvising when a proof fails, a candidate
turns out to hold unique data, or a repository has unpushed work. A
surprise means the classification was wrong, not that there is an
obstacle to route around.

Verify after each tier by re-reading free space on the affected layer,
and report the measured delta rather than the predicted one. When they
disagree, say so and investigate before continuing.

Finish with the steps only the user can run — the guest shutdown and
any host-side compaction — as exact commands with their consequences
stated. Report the host recovery as pending, not achieved.

## Reporting

Follow `references/output-contract.md`.

Lead with the constraint, not the inventory. A ranked list of large
directories is not an answer to "where did my space go" when the
binding limit is a full host disk the user has not noticed.

Give exact figures with their layer attached. Distinguish what was
freed, what is already free inside the guest awaiting compaction, and
what the host stands to recover once the user acts.

Name what was deliberately left alone and why. A cleanup that silently
skips a large protected history store reads as having missed it.


## Portability notes

- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
