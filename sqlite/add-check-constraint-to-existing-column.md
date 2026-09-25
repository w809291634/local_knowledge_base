# Add Check Constraint To Existing Column

To not bury the lede, SQLite does not support adding a check constraint to an
existing column. Instead, if I want to add one after the fact, I can reconstruct
the table with the check constraint specified up front and then migrate the
data.

Here is a `sessions` table that includes `start_time` and `end_time` columns
that use the `text` data type to represent points in time.

```sql
sqlite> .schema sessions
CREATE TABLE sessions (
        id integer primary key,
        active integer not null check (active in (0, 1)),
        project_id integer not null references projects(id) on delete cascade,
        start_time text not null,
        end_time text,
        created_at text not null default (datetime('now')),
        updated_at text not null default (datetime('now'))
    );
CREATE UNIQUE INDEX idx_sessions_single_active
        on sessions(active)
        where active = 1;
```

I want `start_time` and `end_time` to both enforce the shape of the timestamp
strings with `check` constraints. To do that, I need to start a transaction,
create a new version of the table with the check constraints, migrate the data,
rename `sessions` to `sessions_old`, rename `sessions_new` to `sessions` (that's
the in-place swap), and then commit the transaction. `sessions_old` can be
dropped later once I feel good about the migration.

```sql
begin transaction;

create table sessions_new (
  id integer primary key,
  active integer not null check (active in (0, 1)),
  project_id integer not null references projects(id) on delete cascade,
  start_time text not null,
  end_time text,
  created_at text not null default (datetime('now')),
  updated_at text not null default (datetime('now')),
  check(start_time is strftime('%Y-%m-%dT%H:%M:%fZ', start_time)),
  check(end_time is strftime('%Y-%m-%dT%H:%M:%fZ', end_time))
);

insert into sessions_new (
  id, active, project_id, start_time, end_time, created_at, updated_at
)
select id, active, project_id, start_time, end_time, created_at, updated_at
from sessions;

alter table sessions rename to sessions_old;

alter table sessions_new rename to sessions;

drop index if exists idx_sessions_single_active; -- on sessions_old

create unique index idx_sessions_single_active
  on sessions(active)
  where active = 1;

commit;
```

Notice that after the table renames I also drop index (now pointing to
`sessions_old`) and recreate it for the _new_ `sessions` table.

This approach worked well for my situation, but may not be a one-size-fits-all
solution. Depending on how the database is deployed, the size of the tables, and
usage, this approach may not scale. Always do a dry-run of database migrations
like this.
