# Register SQLite Adapter To Serialize Datetimes

SQLite doesn't have a datetime or timestamp data type, so that information has
to be stored as `text` or a unix epoch `int`. That means when using Python's
`sqlite3` module to perform writes I need to tell it what shape to write a
datetime value.

I could manually convert `datetime` values everywhere they are involved in
_write_ operations.

```python
# Prepare `sessions` insert payload
session_data = {
    "active": 1 if active else 0,
    "project_id": project_id,
    "start_time": datetime.isoformat(session.start_time),
    "end_time": None,
}

if session.end_time:
    session_data["end_time"] = datetime.isoformat(session.end_time)

# Insert the new active session
cursor = self.conn.execute(
    """
    insert into sessions (active, project_id, start_time, end_time)
    values (:active, :project_id, :start_time, :end_time)
    returning id;
""",
    session_data,
)
```

I've used `datetime.isoformat` above which formats `datetime` objects like so:

```python
>>> datetime.now().isoformat()
'2026-08-28T11:52:04.709907'
```

I'd like to make two improvements.

1. I want these `datetime` values to be formatted instead like `2026-08-28T18:15:27.213Z`.
2. I want `datetime` values to be serialized automatically in the specific shape
   without having to manually convert them everywhere.

I can achieve both of these things by [registering an adapter with `sqlite3`](https://docs.python.org/3/library/sqlite3.html#how-to-register-adapter-callables)
that handles the serialize of `datetime` objects.

First, I define a function that can perform the `datetime` to `str` conversion.
I decided to put this in `db.py` where I have some other database-specific
functions.

```python
from datetime import datetime, timezone

def to_db(dt: datetime) -> str:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"Unable to store naive datetime: {dt!r}")
    dt = dt.astimezone(timezone.utc)
    return f"{dt:%Y-%m-%dT%H:%M:%S}.{dt.microsecond // 1000:03d}Z"
```

Then I register the adapter before creating the connection that gets used for
database interactions.

```python
import sqlite3
from datetime import datetime
from pathlib import Path
from sqlite3 import Connection

def initialize_conn(db_file: Path) -> Connection:
    # register adapters
    sqlite3.register_adapter(datetime, to_db)

    conn: Connection = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row

    return conn
```

Then I can run write operations with `datetime` objects knowing they will be
correctly serialized.

```python
with self.conn:
    query = "update sessions set active = :active, end_time = :end_time where active = 1;"
    self.conn.execute(
        query,
        {"active": 0, "end_time": session.end_time},
    )
```
