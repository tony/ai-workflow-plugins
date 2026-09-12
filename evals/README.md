# Cross-plugin eval cases

Cases here load more than one plugin at once and check which skill wins. They
live outside `plugins/` because they have to.

A case's `plugins` field names directories, resolved relative to the case
directory, and every entry must sit under a *containment root*. When a case
lives inside a plugin, that root is the enclosing plugin — so a case under
`plugins/model-cli/evals/` can only reach plugins nested inside `model-cli`,
and can never load a sibling. For a case outside any plugin the root is the
directory the run targets, which is why these cases sit at the repository root
and spell their entries `../../plugins/<name>`.

## Running them

```console
$ claude plugin eval . \
    --eval-dir evals \
    --case 'routing-*' \
    --ablation with-without \
    --runs 3
```

Keep the `--case` filter. Targeting `.` walks the whole tree, so without it the
run also discovers every suite under `plugins/*/evals/` and evaluates the entire
marketplace.

No plugin resolves from the target `.`, so the without-arm loads none of them.
That makes the ablation read as "did the right skill fire at all", and the
`arm: both` markers on the winner graders are what put that difference into the
score.

## What a routing case asserts

Three things, and the third is what makes it a routing test rather than a
trigger test:

- the expected skill fired
- the competing plugin's skills did not
- the reply engages with the request the winner is for

Pairs matter more than single cases. A case that only checks "gh wins on a bug
report" is also passed by a plugin that fires on everything, which is why the
tracker prompt is mirrored against the same two plugins with the winner
reversed.

Grading leans on regular expressions over the final message rather than the
judge. These replies are long, and a reply that opens by naming what it could
not verify reads to a small judge as a refusal even when the draft that follows
is complete.
