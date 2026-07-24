# Weave ensemble techniques — cascade gate, residual re-attack, consensus signal

Three cost/quality protocols shared by the weave commands. Each command
wires only the techniques that pay off for it and points here for the
full procedure; this file is the single source of truth for semantics.

- **Cascade gate** (`--cascade`) — wired into `ask` and `review`.
- **Residual re-attack** — governs multi-pass (N ≥ 2) in `ask` and
  `review`, and the Distribute step in `refine`.
- **Consensus signal** — wired into `ask` and `review` synthesis.
  Intentionally not applied to `brainstorm` — independent diversity is
  the product there, not agreement.

Commands inline the consensus tag spec they need at render time; this
file is read only when `--cascade` is set or a pass N ≥ 2 begins.
Without one of those, nothing in this file runs.

Throughout, `M` = the number of lanes that produced an output this
pass. When `M` = 1 (Claude-only fallback, or cascade early-exit) the
residual and consensus procedures are skipped — both need multiple
lanes to mean anything.

---

## Technique 1 — Cascade gate (`--cascade`)

Every weave invocation normally pays full-ensemble price up front. With
`--cascade`, a cheap Claude-only pass runs first, self-verifies, and
fans out to the external lanes only when a confidence trigger fires or
the user escalates.

### Caller contract

The caller runs the gate after session-directory initialization and
context-packet write, **before** launching any external lane. Inputs:
`SESSION_DIR`, the command's Phase 3 Claude-lane prompt (verbatim,
role preamble included), and the command's Verify Claims procedure.

### Step 1 — Cheap pass

Run the command's Claude lane exactly as its Phase 3 specifies — same
Task agent, same prompt, same context packet — and capture the output
to `$SESSION_DIR/pass-0001/outputs/claude.md`. No external CLI runs
yet. Running the lane verbatim means the output is reusable unchanged
if the gate escalates.

### Step 2 — Confidence gate

Run the command's Verify Claims procedure (synthesis Step 1) against
the cheap-pass output itself — self-verification against the codebase,
classifying each claim `verified` / `plausible-unverified` / `false`.
Then evaluate these triggers in order. **Escalate if ANY fires**; each
is a yes/no check an LLM can execute without judgment about the gate
itself:

1. **Contradicted claim** — any claim classified `false` during
   self-verification.
2. **Unverified load-bearing claim** — any claim classified
   `plausible-unverified` whose removal would change the answer's
   conclusion or a finding's severity. Test: delete the claim mentally;
   if the conclusion or severity must change, it is load-bearing.
3. **Ambiguous request** — the question or review focus admits two or
   more materially different readings, and the output committed to one
   without codebase evidence deciding between them. Record each reading
   in the ledger.
4. **Coverage gap** — an explicit part of the request (a sub-question,
   a named file or focus area) has no corresponding content in the
   output.
5. **Judgment call** — the conclusion rests on preference or design
   trade-off rather than facts checkable in the repo (e.g. "which
   approach is better"). Single-lane judgment has no error correction,
   so it always warrants the ensemble. For `review`: any finding
   reported at **Critical** severity fires this trigger — Criticals
   always get ensemble confirmation before reaching the user.

If no trigger fires, the verdict is **early-exit**.

### Step 3 — Ledger and event

Write `$SESSION_DIR/cascade.md`: the verdict (`early-exit` or
`escalate`), then one line per trigger — fired or not, with the
specific claim/reading/gap as evidence when fired. Append to
`events.jsonl`:

```json
{"event":"cascade_gate","timestamp":"<ISO 8601 UTC>","verdict":"early-exit","triggers_fired":[]}
```

### Early-exit path

Skip the external lanes, blind judging, and rubric scoring (nothing to
compare). Keep the command's Critic step — it is the only remaining
error correction — and the deslop pass. Present via
`references/present-results.md` with `CASCADE_STATE` = `early-exit`:
the hero gains the suffix `— cascade early-exit (Claude lane only)` and
the next-step panel gains **Escalate to full ensemble** as the first
option. If the user picks it, continue below as if the gate had
escalated. Record `models` as `["claude"]` in `session.json` until
escalation happens.

### Escalation path

Launch the external lanes per the command's Phase 3, reusing the
cheap-pass output as the Claude lane — do not re-run Claude. Include
the fired triggers verbatim in the external prompts under a heading
`Known weak points in one prior attempt` (do not attribute it to
Claude — that would break blind judging). The command then proceeds
normally: blind labels, synthesis, passes 2..N if configured.

### Headless

Without `AskUserQuestion` (`claude -p`), the gate decides alone: no
early-exit panel, no escalation prompt. The verdict line is emitted in
the output.

---

## Technique 2 — Residual re-attack (multi-pass, N ≥ 2)

Pass N+1 must not re-run the whole task with the prior synthesis as
context. It re-attacks **only the residuals** — the regions where pass
N could not reach an evidence-backed, agreed answer.

### Residual sources

After completing pass N synthesis in `ask` or `review`, extract
residuals from exactly four sources:

1. **Unresolved conflicts** — adjudication Step 3 items where codebase
   evidence could not pick a side.
2. **Failed verification** — claims classified `false` (needs a
   correct replacement) or load-bearing `plausible-unverified` (needs
   evidence) in `verification.md`.
3. **Unincorporated critic findings** — items in `critic.md` that were
   neither folded into the synthesis nor refuted with evidence.
4. **Split consensus** — items marked `split` in the consensus map
   (Technique 3) that verification did not settle.

`refine` fills its ledger from its Distribute step instead: critique
points the woven version left unaddressed, runner-up strengths the
weave could not reconcile, and judge overrides or split judgments.

### Ledger format

Write `$SESSION_DIR/pass-NNNN/residuals.md` (internal bookkeeping, not
shown to the user). One entry per residual:

- **Source**: conflict | verification | critic | split-consensus
- **Region**: the disputed claim or synthesis passage, quoted verbatim
- **Positions**: what each blind label asserted, when they differ
- **Resolution criterion**: what specific evidence (file, behavior,
  convention rule) would settle it

An empty ledger means the pass converged: skip remaining passes,
report convergence (this is the operational definition behind each
command's early-stop).

### Scoped re-attack prompt

The pass N+1 prompt contains ONLY: the ledger entries, and for each
entry at most 10 surrounding lines of the pass-N synthesis for local
context. Never the full prior synthesis, never the original full task.
Instruct: "Resolve ONLY the items listed. For each, give your
resolution and the evidence (file paths, line references). Anything
outside these items is out of scope and will be discarded."

### Merge-back

Apply each resolved item as a local edit to the quoted region of the
pass-N synthesis; every untouched passage carries into the pass N+1
synthesis verbatim. Re-score only the rubric dimensions the resolved
items affect. Content a model volunteered outside the ledger is
discarded unread — scope discipline is what makes residual passes
cheap.

---

## Technique 3 — Consensus signal

Where lanes disagree, the variance is information. Adjudication decides
what is *true* (evidence wins); consensus reports how *confident* the
ensemble is — it must never be silently adjudicated away.

### Counting rule

During adjudication (synthesis Step 3), classify each lane per finding
or claim as **agree** (asserts it or a compatible position), **dissent**
(asserts an incompatible position, including "not an issue"), or
**silent** (does not address it). Count over the M participating lanes.

On cascade-escalated runs the external lanes were primed with the
fired triggers, so for any item that restates a fired trigger, count
only the external lanes — the cheap pass is not an independent source
for its own weak points.

### Levels

- **unanimous** — agree = M
- **majority** — agree > M/2, and at least one lane dissents or is
  silent
- **split** — no position held by more than M/2 lanes (includes 1–1
  conflicts at M = 2)
- **single** — agree = 1, all other lanes silent (no dissent)

Dissent and silence are not the same: a single-lane finding no one
contradicted outranks a split one.

### Artifacts

Write the per-item consensus map into `$SESSION_DIR/pass-NNNN/`
`consensus.md` using blind labels; model names are revealed there after
scoring, alongside the label map.

### Surfacing in output

- **review** — every finding under Verified Issues carries a consensus
  tag: `consensus 3/3`, `consensus 2/3`, `consensus 1/3 (uncontested)`.
  Split findings that verification could not settle MUST appear under
  Reviewer Disagreements with both positions and the evidence for each
  — never dropped. Within a severity band, order findings: unanimous
  and verified, then majority and verified, then single verified, then
  anything unverified.
- **ask** — the Disagreements section renders every split and
  majority-with-dissent item: both positions, which was adopted, and
  the deciding evidence (or "unresolved — both positions retained").

Consensus feeds ordering and labeling only. It never overrides
verification: a unanimous claim contradicted by the code is still
`false`, and the code wins.
