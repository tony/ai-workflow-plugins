# Adopting the vendor's default rule set

When a release curates a substantially larger default rule set, a repository with an explicit `select` gets nothing from it. Not "nothing to do" — *nothing*. The vendor's recommended baseline lands, and the repo is silently opted out of it, permanently, because `select` replaces the default set rather than extending it.

That opt-out is invisible. Nothing in the config records it, no diagnostic reports it, and every future release quietly widens the gap. Turning it into an explicit decision is the point of this document.

## First, measure — do not reason about it

The blast radius is the only thing that decides whether this is a five-minute change or a project. Measure it without editing anything, by extending the repo's configured selection with the default set on the command line and diffing the finding counts:

Get the default set from the binary itself rather than from documentation, which can lag the release. Ruff prints its resolved selection under `linter.rules.enabled` when asked to show settings with an isolated config, and that output is authoritative for the exact binary in the lockfile.

Then run the linter twice — once as configured, once with the default codes added via `--extend-select` — and take the difference. That difference, per repository and broken down per rule, is the real cost. Do this for every repository in scope before proposing anything, because the number varies enormously: repos with disciplined codebases often land at zero, while one with an unusual file layout can produce hundreds of findings from a single rule.

**A local measurement is a lower bound, not the answer.** Some rules are gated on the host platform and go silent where you are measuring, then fire on the CI runner. The clearest case: rules that check a file's executable permission bit are skipped entirely under WSL, because Windows filesystems have no executable bit and everything reports as executable — ruff's `shebang-not-executable` opens with an explicit early return for exactly this reason. Measure on WSL and those rules report zero; the Linux runner then fails the lint step on a finding that was invisible to the whole pre-flight. Filesystem-sensitive checks generally are suspect this way: permission bits, symlinks, case-sensitivity, line endings.

Treat a CI failure on a rule your measurement said would not fire as a platform gap first and a mistake second. Confirm it by reading the rule's implementation for a platform guard rather than guessing, and say in the report that the measurement under-reported that class.

## The three config shapes, and why two of them are wrong

**Enumerate every default code in `select`.** Explicit and frozen: a future release can never change the enabled set silently. Costs hundreds of config lines per repository, must be regenerated and re-reviewed on every release, and it fights what the curated default set exists to provide. Reasonable only for a repository under a change-control regime that genuinely requires a frozen, auditable rule list.

**Expand `select` to whole linter prefixes covering the defaults.** Superficially attractive — it matches the prefix style most configs already use, and it is short. It is also badly wrong, and the measurement proves it: a curated default set takes a *subset* of each linter, not the whole thing. One linter may contribute forty-odd rules to the defaults while another contributes one or two. Selecting the whole prefix therefore enables far more than the vendor recommends. Measured on real repositories, this produced 50-100x more findings than the exact default set — thousands rather than dozens. Reject it, and say why, rather than leaving it as an option.

**Leave `select` unset and use `extend-select` for the repo's own additions.** The default set applies implicitly; `extend-select` layers the project's extra linters on top; `ignore` and `per-file-ignores` carve out what the project does not want. This is what the mechanism is designed for. The config shrinks to roughly the length of the old `select`, and it enables exactly the defaults plus the project's own choices — identical, today, to the enumerated form.

Default to the third. The trade-off to state plainly: it tracks the vendor's defaults as they evolve, so a future release can surface new findings without the config changing. That exposure is real, but it is not new — any config selecting whole prefixes already has exactly that exposure, and usually for far more rules.

**Check whether the tool offers a token for the default set before assuming.** Some linters let you write the default set by name in an explicit selection, which would make the enumerated form cheap. Read the selector type in the tool's own source at the release tag rather than guessing; if the only tokens are "everything" and per-linter prefixes, the enumerated form is the only explicit option and its cost is what it is.

## Curating what the defaults surface

Two failure modes, opposite and equally bad: fixing an idiom the project chose deliberately, and blanket-ignoring a rule that found real bugs.

Read the code at every site before deciding. Sort each rule into:

**Real findings.** Fix them. Typing rules that catch a concrete class where the self type belongs, naive datetime construction, mechanical simplifications, redundant syntax. These are why adopting the defaults is worth doing at all.

**Deliberate idioms.** Scope an ignore to exactly where the idiom lives — a per-file ignore, never a repo-wide one — and write the reason in the config. A rule that fires on a documentation build script's use of dynamic execution, or on a notebook format's generated function shape, or on a deliberately ordered set of numbered lesson modules, is not finding a bug; it is failing to know the context. The narrower the scope, the more the ignore documents itself.

**Load-bearing patterns that look redundant.** The dangerous class, because the "fix" is silently destructive. The clearest example: an import aliased to its own name reads as pure redundancy, and a rule will say so, but it is the standard explicit re-export form — under a strict type-checking configuration, removing the alias stops the symbol being re-exported and breaks downstream consumers with no local test failure. Before fixing anything that looks merely redundant, check whether another tool in the project depends on the shape.

**Vendored code.** Not yours. Exclude the tree or scope an ignore to it, matching whatever the repo already does.

**Coverage gates react to fixes.** Touching a line that no test exercises turns it into a "patch" line, and a patch-coverage gate that was green before the bump can go red purely because a one-token lint fix landed in an uncovered constructor. The fix is a test that pins the behaviour the lint change had to preserve — which is worth having anyway, since it is the only thing proving the change was safe.

When a rule fires broadly and *none* of its findings are real, the answer is a documented `ignore` entry in the config, not a scattering of inline suppressions and not code contorted to satisfy a rule the project does not want.

## Landing it

The config change is one commit, alone, before any fix or ignore. It is the commit that makes everything else legible: without it, a reviewer cannot tell why a hundred unrelated findings suddenly needed attention. Report the enabled-rule count before and after in its body — that number is the whole point of the change.

Then one commit per rule fixed, and one commit per ignore added, each body carrying the rule's documentation URL. Resolve the URL slug from the tool's own rule-lookup command rather than guessing it from the code. A reviewer's first question about any lint commit is "what is this rule and do I agree with it", and a link answers it in one click.
