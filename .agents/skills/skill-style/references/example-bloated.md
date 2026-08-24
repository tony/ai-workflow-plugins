# A bloated skill, with every defect named

Below is a SKILL.md of the kind the deletion test exists for. It is
not a strawman: everything in it is true, well-meant, and grammatical.
That is what makes it expensive. `example-ideal.md` is the same skill
after the test.

## The file

````markdown
---
name: db-helper
description: A helpful skill for working with databases. You can use this to restore backups and do other database-related things.
---

# Database Helper Skill

## Introduction

Welcome to the database helper skill! This skill is designed to help
you work with PostgreSQL databases in a safe and effective manner.

PostgreSQL is a powerful, open-source object-relational database
system with over 35 years of active development. It is known for its
reliability, feature robustness, and performance. Backups in
PostgreSQL are typically created using the `pg_dump` utility, which
produces a file containing the SQL commands needed to recreate the
database.

## Overview

This section provides an overview of what this skill does. This skill
helps with restoring PostgreSQL database backups. It walks through the
process step by step.

## Why This Matters

Database restoration is an important operation. Getting it wrong can
lead to data loss, which can be very costly for an organization. It is
therefore generally considered a best practice to be careful when
performing restores. Taking your time and double-checking your work
can help you avoid problems down the line.

## Prerequisites

Before you begin, you will need to have a few things set up. You
should make sure you have the appropriate tools installed and that you
have the necessary permissions to perform the restore operation.

## Choosing Your Approach

There are several ways to restore a PostgreSQL backup, and the right
one depends on your situation:

| Option | Tool | Notes |
|---|---|---|
| A1 | `pg_restore` | Works with custom-format dumps |
| A2 | `psql` | Works with plain SQL dumps |
| A3 | pgAdmin | Has a graphical interface |
| A4 | Docker exec | If you are running in a container |
| A5 | Cloud console | If you are on a managed service |

You can pick whichever of these options works best for you. Option A1
is often a reasonable default, but feel free to use Option A2 or
Option A3 if you prefer.

## The Restore Process

This section explains the restore process.

### Step 1: Locate the backup

First, you need to find the backup file. Backups are stored in the
backup directory. Look in that directory for the most recent file.

```bash
ls -la C:\backups\nightly\
```

### Step 2: Restore the database

Now that you have located the backup file, you can restore it. Run the
restore command shown below. This command will restore the database
from the backup file you located in the previous step.

```bash
pg_restore --dbname=mydb backup.dump
```

The command above uses the `--dbname` flag to specify which database
to restore into, and takes the path to the backup file as its final
argument.

### Step 3: Verify

After the restore completes, you should verify that it worked. Use the
`query_database` tool to check that the data looks correct. Note that
as of the 2024 release, the verification step is faster than it used
to be.

## Additional Information

For more details, see `reference/advanced.md`, which links onward to
`reference/internals.md` where the full explanation lives.

## Conclusion

That's it! You now know how to restore a PostgreSQL database backup.
If you have any questions, feel free to ask. Happy restoring!
````

## What the test cuts, and why

**The description routes nothing.** `A helpful skill for working with
databases` says what it is about, never when to reach for it, and
`You can use this to` is second person in a system prompt. Nobody
types "database-related things", so nothing matches it.

**`Introduction`, `Overview`, and `Why This Matters` teach the agent
nothing it does not know.** Postgres's age, `pg_dump`'s existence, and
the fact that data loss is costly all survive as *true* and fail as
*load-bearing*. Deleting all three changes no command, constraint,
trigger, output, or fork.

**`This section explains the restore process` restates its own
heading.** So does `This section provides an overview`. A line whose
content is its heading is the purest form of the defect.

**`Prerequisites` names no prerequisite.** "The appropriate tools" and
"the necessary permissions" cannot be acted on. Either name the binary
and the role, or cut the section.

**The options table is five ways to fail.** Presented as equals with
no rule for choosing, it hands the agent a decision it has no basis to
make. One default and one named escape hatch replaces the whole table
— and the table was not matrix-shaped to begin with, so prose reads
better even after the cut.

**`A1` through `A5` are coded labels.** The reader has to hold an
index in their head to follow the paragraph underneath.

**The prose under each fence repeats the fence.** `The command above
uses the --dbname flag to specify which database to restore into` is
the command, in English, one line lower. Where a fence and its prose
say the same thing, the prose goes — the fence is what was verified.

**The commands themselves are wrong in ways the test protects.**
`C:\backups\nightly\` is a Windows path that breaks on any Unix host,
and the `pg_restore` invocation has no `--clean`, no ordering
constraint, and no mention that it overwrites. These are defects to
*fix by verifying against a real system* — never by editing the
characters inside a fence on style grounds. The deletion test cuts
prose; it does not touch what is inside a fence.

**`query_database` is an unqualified tool name.** Once a second server
is connected the agent cannot resolve it. Qualify it as
`ServerName:query_database`.

**`as of the 2024 release` rots.** Any sentence anchored to a date is
wrong on a schedule.

**The reference chain is two levels deep.** The body links
`reference/advanced.md`, which links `reference/internals.md`, where
the answer actually is. An agent that follows the second link tends to
preview the file rather than read it, then act on the fragment.

**`Conclusion` is postamble.** `That's it!`, `feel free to ask`, and
`Happy restoring!` are conversational filler in a file no human reads
conversationally.

## What survives

Three things: the name of the tool to run, the fact that a restore
overwrites, and the requirement to verify afterward. Everything else
in 110 lines was scaffolding around those three facts — which is the
usual ratio, and the reason the test is worth running.
