# Evidence tiers

Every claim a study makes sits in one of two tiers, and the tier decides what
the claim must carry. The tier is recorded on the term's row in `terms.jsonl`
and honored by the evidence documents.

## Structural

*This is-a that. These are the members. This term means this.*

Backed by a pinned citation, per `citation.md`. The reader checks it by
opening the link and reading the quoted lines at the recorded locator.

A structural claim needs no number. "A plugin is an agent domain when its name
denotes a doer rather than the thing acted on" is settled by pointing at the
names, not by counting them.

## Distributional

*How often. How similar. How concentrated. How it changed.*

Backed by a command a reader can paste and the output it produced, both
recorded in `evidence/metrics.md`. The command goes in a `console` block, the
output in the block beneath it.

The measurement must be reproducible from the study's own artifacts or from
the pinned corpus. A number copied from a run nobody can repeat is folklore
wearing a decimal point.

Keep a measurement together with the conditions that produced it. A score
without the corpus it was computed over says nothing.

## The closing rule

A claim that fits neither tier does not go in the brief.

That is not a counsel of perfection. Impressions are worth having, and they
belong in `evidence/contested.md` as claims that were raised and not settled,
where a later round can pick them up. What they may not do is appear in the
brief in the same voice as a claim that carries its evidence.
