# Make Dataclass Sortable By Specific Field

One way to sort a list of some `dataclass` is to define the `key` parameter when
calling `sort` or `sorted` like I discussed in [Sort a List of Dataclass
Instances](sort-a-list-of-dataclass-instances.md):

```python
for date in sessions_grouped_by_day.keys():
    sessions_grouped_by_day[date].sort(
        key=lambda session: session.start_time.time()
    )
```

But then that lambda for `key` needs to be defined everywhere you sort.

If the dataclass has a single, specific field that acts as a natural proxy for
sort order, then you can define that in the `dataclass` implementation with the
`__lt__` method.

As long as a class defines the _less than_ dunder method, it will be sortable.

Here is what that looks like for this `Session` dataclass:

```python
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Session:
    start_time: datetime
    project_name: str
    end_time: datetime | None = None

    def __lt__(self, other):
        if not isinstance(other, Session):
            return NotImplemented
        return self.start_time < other.start_time

    # more methods below ...
```

This implementation of `__lt__` tells the sorting methods that _this_ (`self`)
instance of `Session` can be compared to some `other` instance of `Session` by
comparing their `start_time` values to see which is less than. The guard at the
beginning makes sure only instances of `Session` are being compared.
