# Output Query Result In Nicely Formatted Table

When I start a fresh SQLite connection and run a query, all the results are
squished together in a way that is poorly formatted, hard to read, and missing
column headers.

```sql
sqlite> select sessions.id, start_time, end_time, projects.name from sessions join projects on projects.id = sessions.project_id limit 3;
1|2026-07-26T21:15:50.062936+00:00|2026-07-26T21:53:13.990Z|taco
2|2026-07-26T21:53:40.019946+00:00|2026-07-26T22:14:09.168Z|TIL
3|2026-08-02T17:00:16.119169+00:00|2026-08-02T17:30:16.119Z|py-vmt
```

I can drastically improve the look of this by turning _headers_ on and switching
to _box_ mode.

```sql
sqlite> .headers on
sqlite> .mode box
sqlite> select sessions.id, start_time, end_time, projects.name from sessions join projects on projects.id = sessions.project_id limit 3;
┌────┬──────────────────────────────────┬──────────────────────────┬────────┐
│ id │            start_time            │         end_time         │  name  │
├────┼──────────────────────────────────┼──────────────────────────┼────────┤
│ 1  │ 2026-07-26T21:15:50.062936+00:00 │ 2026-07-26T21:53:13.990Z │ taco   │
│ 2  │ 2026-07-26T21:53:40.019946+00:00 │ 2026-07-26T22:14:09.168Z │ TIL    │
│ 3  │ 2026-08-02T17:00:16.119169+00:00 │ 2026-08-02T17:30:16.119Z │ py-vmt │
└────┴──────────────────────────────────┴──────────────────────────┴────────┘
```

I personally find that much easier on the eyes. It is also a nicer format to
copy and paste into a post like this or a formatted code block that I'm sharing
with a colleague.

I can also do this directly from the CLI with a one-liner using `-header` and
`-box` like so:

```bash
❯ sqlite3 /Users/lastword/.local/share/vmt/sessions.db -header -box "select sessions.id, start_time, end_time, projects.name from sessions join projects on projects.id = sessions.project_id limit 3"
┌────┬──────────────────────────────────┬──────────────────────────┬────────┐
│ id │            start_time            │         end_time         │  name  │
├────┼──────────────────────────────────┼──────────────────────────┼────────┤
│ 1  │ 2026-07-26T21:15:50.062936+00:00 │ 2026-07-26T21:53:13.990Z │ taco   │
│ 2  │ 2026-07-26T21:53:40.019946+00:00 │ 2026-07-26T22:14:09.168Z │ TIL    │
│ 3  │ 2026-08-02T17:00:16.119169+00:00 │ 2026-08-02T17:30:16.119Z │ py-vmt │
└────┴──────────────────────────────────┴──────────────────────────┴────────┘
```

Run the `.help` dot-command from a SQLite prompt for a full listing of these
commands. See also `sqlite3 --help` from the CLI for usage details about all
flags.
