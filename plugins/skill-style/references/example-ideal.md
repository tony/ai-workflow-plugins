# The same skill, after the deletion test

Every line below survives: it carries a command, a constraint, a
trigger, an output contract, or a fork. Nothing explains PostgreSQL to
a model that already knows it.

````markdown
---
name: restoring-postgres-backups
description: Restores a PostgreSQL database from a nightly pg_dump, into a scratch database first and then over the target. Use when restoring a Postgres backup, recovering a dropped table, loading a production dump into a local or staging database, or when the user mentions pg_restore, pg_dump, a .dump file, or a nightly backup.
allowed-tools: ["Bash", "Read"]
---

# Restoring Postgres backups

`pg_restore --clean` drops every object it is about to recreate. Restore
into a scratch database and verify there before touching the target.

## Locate the dump

Nightly dumps land in `/srv/backups/pg/` named `<db>-<YYYYMMDD>.dump`.

```console
$ ls -t /srv/backups/pg/*.dump | head -5
```

## Restore into scratch

Create the scratch database and restore into it. `--exit-on-error`
turns a partial restore into a failure instead of a half-populated
database:

```console
$ createdb restore_scratch
```

```console
$ pg_restore \
    --dbname=restore_scratch \
    --exit-on-error \
    --jobs=4 \
    /srv/backups/pg/<db>-<date>.dump
```

A plain-SQL dump (`.sql`, not `.dump`) has no custom-format header and
`pg_restore` will reject it. Pipe those through `psql` instead:

```console
$ psql --dbname=restore_scratch --set ON_ERROR_STOP=1 \
    --file=/srv/backups/pg/<db>-<date>.sql
```

## Verify before promoting

Compare row counts against what the dump claimed. Any table at zero is
a failed restore, not an empty table:

```console
$ psql --dbname=restore_scratch --command='\dt+'
```

If a count is wrong, re-run the restore with `--verbose` and read the
first error. Do not promote a scratch database you have not verified.

## Promote

Promotion is irreversible and takes the target offline. Confirm with
the owner first, then:

```console
$ pg_restore \
    --dbname=<target> \
    --clean \
    --if-exists \
    --exit-on-error \
    /srv/backups/pg/<db>-<date>.dump
```

## Drop the scratch database

```console
$ dropdb restore_scratch
```

## Point-in-time recovery

Restoring to a moment between nightlies needs WAL replay, not
`pg_restore`. See `reference/pitr.md`.
````
