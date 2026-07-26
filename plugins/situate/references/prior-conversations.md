# Prior conversations

Shared by `/situate` and the `situational-awareness` skill. This layer
runs only when the user passes `--with-agentgrep` or asks for it in
words.

## Why it is opt-in

The first five layers read the repository — a bounded, current, shared
artifact. This one reads local transcripts from every AI CLI on the
machine: other projects, other people's names, credentials pasted into
a terminal two months ago. It is slower, noisier, and carries material
the repository never agreed to hold.

It earns its place when the repository does not explain itself: a
branch whose commits do not say why an approach was chosen, a decision
that left no artifact, work resumed after a gap.

## Requirements

`agentgrep` reads Codex, Claude, Cursor, Gemini, Antigravity, Grok, Pi,
and OpenCode stores. Run it through `uvx` so no install is needed:

```console
uvx agentgrep search --only-here --limit 20 <terms>
```

Absent network or a `uvx` failure, report the layer unavailable and
continue with the rest of the sweep. It is never a hard dependency.

## Scoping

Scope to this project first. `--only-here` filters to records from the
current repository; `--here` merely boosts them and will drag in
unrelated projects.

```console
uvx agentgrep search --only-here --branch "$(git branch --show-current)" --limit 20 <terms>
```

Search prompts before conversations. The default `--scope prompts`
returns what the user asked for, which is the record of intent;
`--scope conversations` adds every assistant reply and buries it.
Widen only when prompts return nothing.

Derive terms from what the earlier layers already found — the feature
name, the ticket ID, the module the diff concentrates in. A query
composed of generic words returns generic noise.

```console
uvx agentgrep search --only-here 'ENG-123 OR "retry backoff"' --limit 20
```

Cap the layer. Twenty ranked results is enough to establish whether
prior context exists; if it does and matters, say so and let the user
ask for more.

## Reconciling with the repository

A prior conversation is evidence of **intent**, not of **state**. A
plan discussed three weeks ago may have been implemented, abandoned,
or reversed by a commit since — and the transcript will look exactly
the same either way.

Every finding from this layer gets checked against the repository
before it is reported. When they disagree, the repository wins and the
disagreement itself is the finding: an approach discussed but never
landed is more useful to know than either fact alone.

Order findings by recency and say when each was. A decision's age is
most of its weight.

## Privacy

Report what was decided, not the transcript.

- Never print store paths, session file paths, or any local absolute
  path. Cite a finding by agent, date, and subject.
- Never quote a third party's name, address, key, or token, even when
  it appears verbatim in a match. Summarize around it.
- Quote the user's own words only when the exact phrasing is the point,
  and keep it to a line.

The report is something the user may paste into an issue or hand to a
teammate. Everything in it should survive that.
