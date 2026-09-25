# Sort A List Of Dataclass Instances

Sorting lists of scalar values (integers, strings, floats, even booleans) in
Python is simple because the natural ordering of the list elements will be used.
We can call `sorted` on the list and it _just works_.

```python
>>> items = ["orange", "apple", "banana", "mango"]
>>> sorted(items)
['apple', 'banana', 'mango', 'orange']
```

However, if we have a list of non-scalar values, it is a little more complex. We
have to give `sorted` some help with knowing how to sort things that don't have
a natural ordering.

Let's take this `dataclass` that represents a time-based `Session` as an
example.

```python
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Session:
    start_time: datetime
    project_name: str
    end_time: datetime | None = None

    # plus several methods ...
```

If I have a list of `Session` instances that I want to sort, I have to give
`sorted` a `key` to sort on. In the case of these `Session` instances, we'll
pass a `lambda` that can be evaluated to determine the sort value (which needs
to be sortable). `datetime` instances are sortable and I want to sort these
sessions based on their `start_time` values.

Here is a snippet from my `py_vmt` CLI where I make sure that each list of
sessions in this day-by-day `dict` is sorted based on the `start_time`:

```python
for date in sessions_grouped_by_day.keys():
    sessions_grouped_by_day[date].sort(
        key=lambda session: session.start_time.time()
    )
```

`sort` (and `sorted`) translates each item in the list to the values produced
by the lambda and then sorts them by those values.

[source](https://docs.python.org/3/howto/sorting.html)
