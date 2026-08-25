# Stage gates

Each stage has one exit condition. A stage may not hand off until its gate
passes, and a failed gate is reported rather than worked around.

The gates exist because the stages do not call each other — they communicate
through files. A stage that hands off a malformed artifact fails somewhere
downstream, where the cause is no longer visible.

## gather

Every source in `sources.jsonl` has a resolved ref, and every source recorded
as not read has a stated reason in `why`.

An unresolved ref means a citation cannot be pinned later. An unexplained
omission means the study cannot state its own coverage boundary.

## extract

Every row in `terms.jsonl` has a non-empty `definition` and at least one entry
in `cites`.

A term with no definition is a word the corpus happens to contain. A
definition with no citation is the analyst's summary of the corpus, which is
the thing this pipeline exists to avoid producing.

## distill

Every type has a discriminator, and `term-metrics.py` reports no orphans.

## contest

The analyzer has run, every finding it produced has a recorded verdict in
`evidence/contested.md`, and the last round produced no new contested claim.

A finding with no verdict is worse than no finding: it reads as a problem
someone already considered.

## render

The brief gate exits zero:

```console
$ ./references/term-metrics.py notes/ontology/<subject>/ --check-brief
```

A non-zero exit means the brief is not renderable yet. Fix the brief, not the
checker.
