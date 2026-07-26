# Weave worker backends

Every weave ensemble resolves its worker backend before gathering project
context or starting an operational phase. The choice controls how every
participant, judge, refinement pass, and cascade escalation runs for the
session.

## Caller contract

Parse `--workers=subagents|model-clis` from `$ARGUMENTS`, strip it from the
task sent to workers, and set `worker_backend`:

- `--workers=subagents` sets `worker_backend = subagents`.
- `--workers=model-clis` sets `worker_backend = model-clis`.
- An invalid value stops before execution and reports the accepted values.

When the flag is absent and an interactive choice tool is available, make this
the first question:

- **Question**: "How should weave run its adversarial workers?"
- **Header**: "Workers"
- **Adversarial sub-agents (Recommended)** — Use independent workers supplied
  by the current host. No separate AI command-line tools are launched.
- **Separate model CLIs** — Use the command's existing external-model lanes,
  including their detection, timeout, and retry behavior.

When interactive choice is unavailable or the session is headless, default to
`subagents`. Record `worker_backend` in session metadata and the session-start
event.

The selected backend is a session boundary. Retry and fallback may occur
within that backend, but never across it. Never switch from sub-agents to model
CLIs, or from model CLIs to sub-agents, without a new explicit user choice.

When calling shared result-rendering references, pass `worker_backend` as
`WORKER_BACKEND`, the successful artifact IDs as `PARTICIPANTS`, the
participant-to-executor mapping as `EXECUTORS`, and resolved providers or
models as `MODELS` only for `model-clis`.

## Backend adapter

The selected backend governs the whole session: setup, dispatch, retry,
artifact capture, judging, cascade, refinement, session metadata, result
rendering, and cleanup. Resolve an ordered participant roster once, then use
that roster in every later phase.

Each roster entry has four independent values:

- `role_id` — `maintainer`, `skeptic`, or `builder`.
- `participant_id` — the stable artifact and attribution ID for this backend.
- `executor` — `host-native`, `host`, `agy`, `codex`, or the resolved fallback
  executable.
- `model` — optional provider/model information reported by the executor.

Never infer one value from another. In particular, the `gpt` participant ID is
not an executable; its normal model-CLI executor is `codex`.

Use `<participant>` as the placeholder in backend-independent paths and
events. A single output is
`$SESSION_DIR/pass-NNNN/outputs/<participant>.md`; a variant is
`$SESSION_DIR/outputs/<participant>-v<N>.md`. Blind-label maps point to
participant IDs.

The command supplies the task prompt, context packet, project-access mode,
pass and variant numbers, output schema, rubric, and convergence rules. The
adapter turns those values into one WorkItem per participant:

- role and participant identity
- task prompt and context packet
- `read-only` or `mutating` project access
- pass, optional variant, and optional judge kind
- output path and isolated worktree path

The provider-named Claude, Antigravity, and GPT sections in a command are the
`model-clis` implementation of those WorkItems. Detection, timeout, shell
commands, provider artifact examples, and provider-specific fallback prose in
those sections apply only when `worker_backend == model-clis`.

When `worker_backend == subagents`, do not fall through to provider-named
sections. Dispatch the command's WorkItems through the native protocol below,
then resume at its backend-independent verification, rubric, synthesis,
transition-gate, adoption, and presentation steps. Interpret generic uses of
"model" in those shared steps as "participant"; use the roster rather than
hard-coded provider names or paths. Host judging means the current
orchestrator, never an assumed provider.

### Session contract

Every `session.json` and `session_start` event records `worker_backend` and
the ordered `participants`. `session.json` also records `executors` as an
object keyed by participant ID. Add `models` only for `model-clis`, and only
for values actually resolved or reported.

Pass and completion events use participant IDs, including
`participants_completed`, `winner`, and `judged_by`. Update `participants`
and `executors` when a worker becomes unavailable. Never write native role IDs
to `models`.

Every command passes these values to result rendering:

- `WORKER_BACKEND` — the selected backend
- `PARTICIPANTS` — successful participant IDs
- `EXECUTORS` — successful participant ID to executor mapping
- `MODELS` — resolved model-CLI provider/model values, or null for subagents

## Adversarial sub-agents

Use three independent host-native sub-agents. Dispatch them in parallel when
the host has capacity; otherwise queue them without combining roles or sharing
intermediate answers. Each WorkItem launches a fresh sub-agent; the
orchestrator persists the returned response to its declared output path.

### Maintainer

Prioritize correctness, project conventions, and minimal scope. Challenge work
that is not necessary for the stated goal.

### Skeptic

Challenge assumptions, expose failure modes and unstated requirements, and
test whether the proposed direction is sound.

### Builder

Prioritize simple, practical, shippable work. Identify unnecessary abstraction
and favor the shortest design that satisfies the contract.

Give every role the same task, context packet, constraints, and repository
baseline. Each sub-agent starts from an independent context and must not read
another role's output before its own artifact is complete.

Use role identities for artifacts and attribution:

- `maintainer`
- `skeptic`
- `builder`

Write a single result as `<role>.md` and a variant as
`<role>-v<N>.md`. User-facing output names the role and identifies the worker
backend as `subagents`; it must not claim that the roles are different models.

Persist `worker_backend = subagents`,
`participants = ["maintainer", "skeptic", "builder"]`, and an executor mapping
whose values are `host-native`. Record an actual provider or model only when
the host reports it; never infer one from the role.

For project-read-only commands, give every role its own
disposable isolated worktree under the session directory. Materialize it from
the captured
repository baseline and include relevant pre-existing working-tree changes in
the context packet. Point the worker at that worktree, never the user's working
tree.
Prompt hardening still forbids project writes, so an accidental write is
contained in a disposable tree.

For mutating commands, give every role its own isolated worktree on a
dedicated branch, including the Maintainer. A sub-agent may modify only its
assigned worktree. Keep the worktree across that role's refinement passes.
Compare and snapshot changes by participant ID, then adopt selected work only
through the command's existing synthesis flow.

After a read-only WorkItem returns, or after a mutating participant's diffs
and snapshots have been captured, remove only that participant's exact
session-scoped worktree. Native workers never run `checkout`, `clean`, or
`reset` against the user's checkout. If final fingerprint verification finds
main-tree drift, stop and report it; do not destroy data in an attempt to
repair it.

If the host cannot create native sub-agents, stop with a direct explanation.
In an interactive session, offer a new explicit choice to use separate model
CLIs. In a headless session, explain that the user can rerun with
`--workers=model-clis`; do not launch them automatically.

## Separate model CLIs

This backend preserves each command's existing host, Antigravity, and GPT
lanes. Run CLI detection only after the user explicitly selects
`model-clis`. Timeout discovery, retry classification, lesser-model fallback,
repository guards, and stderr capture remain conditional on
`worker_backend == model-clis`.

Preserve the existing participant IDs while recording their roles and
executors separately:

- `claude` carries the Maintainer role and runs through the host agent.
- `agy` carries the Skeptic role and normally runs through the `agy` CLI.
- `gpt` carries the Builder role and normally runs through the `codex` CLI.

Attribute each result with its role, lane artifact ID, and resolved executor.
Keep fallbacks within the lane's existing model-CLI chain. If a lane exhausts
that chain, mark its lane artifact ID unavailable; do not replace it with a
host-native sub-agent.

Persist `worker_backend = model-clis`, the successful participant IDs,
their executor mapping, and the resolved providers or models in `models`.
Use participant IDs in pass and completion events.

Project-read-only commands retain the Repo Guard Protocol. Mutating commands
retain their existing host-lane workflow and isolated worktrees for external
lanes. External CLI instructions, detection, timeouts, and repository-guard
commands must remain inside branches explicitly guarded by
`worker_backend == model-clis`.

## Shared execution semantics

### Partial failure

Retry a failed worker only through mechanisms provided by the selected
backend. A sub-agent retry creates a fresh independent sub-agent with the same
role and input. A model-CLI retry follows the command's existing lane-specific
retry and fallback chain.

Continue with two successful roles and report the unavailable role. With one
successful role, produce a single-role result, omit consensus claims, and
state that adversarial comparison was unavailable. If every role fails, stop
and report each failure without synthesizing an answer.

### Judging

Host judging evaluates the successful participant artifacts regardless of
backend and records `judged_by = host`. Round-robin judging rotates across
successful participant IDs in role order, not model names. A native
round-robin judge is a fresh sub-agent assigned the selected role; a model-CLI
judge uses the resolved executor for that participant.

Panel judging dispatches one independent judge per successful role. Peer-only
scoring excludes the artifact-producing role's own judge. If too few judges
remain for peer scoring, use the command's documented degraded-panel or host
fallback and name the degradation.

Judges receive immutable copies of the candidate artifacts and shared rubric.
They do not modify project files or candidate artifacts.

### Cascade

A cascade cheap pass uses the Maintainer role through the selected backend. If
the confidence gate escalates, launch the Skeptic and Builder through that same
backend and reuse the completed Maintainer artifact.

An early exit is attributed to the Maintainer role only. Escalation must not
change `worker_backend`, even when a role is unavailable.

### Refinement

Every refinement pass redispatches the successful participants through the
selected backend. Sub-agent mode uses fresh independent sub-agents; model-CLI
mode uses the resolved participant executors. Preserve role and participant
identities across passes so attribution, judge rotation, and failure reporting
stay stable.
