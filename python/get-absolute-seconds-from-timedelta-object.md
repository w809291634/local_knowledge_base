# Get Absolute Seconds From `timedelta` Object

The [`timedelta` object provided by
`datetime`](https://docs.python.org/3/library/datetime.html#timedelta-objects)
is a useful built-in concept for representing a duration of time.

```python
>>> from datetime import timedelta
>>> diff = timedelta(hours=1, minutes=1, seconds=6)
>>> diff.seconds
3666
```

It is pretty minimal though. There are only a couple things you can inspect
about it -- `days`, `seconds` (as I did in the snippet above), and
`microseconds`.

And perhaps that is enough to hint at the issue I recently ran into with it --
specifically that you can access both `days` and `seconds`.

Let's look at what happens when I have a `timedelta` with more than a day worth
of seconds.

```python
>>> diff = timedelta(seconds=(3600 * 24 + 1))
>>> diff.seconds
1
>>> diff.days
1
```

I thought `seconds` was going to produce `86401` instead of `1`. The reason is
because any amount of duration over a day gets converted into the `days` value
and its the remaining time smaller than a day that is represented by `seconds`.

In my [original implementation of
`format_time_delta`](https://github.com/jbranchaud/py-vmt/blob/c14eaa56cf5f5c6d0120a95f04f95a6c87443e1c/src/py_vmt/time_helpers.py#L11-L14),
I was trying to build a relative time string by converting `seconds` into hours,
minutes, and seconds. That approach falls apart as soon as the delta is greater
than a day.

```python
def format_time_delta(diff) -> str:
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, remainder = divmod(remainder, 60)
    seconds = remainder

    # ...
```

Instead, I needed to reach for [the `total_seconds()` function](https://docs.python.org/3/library/datetime.html#datetime.timedelta.total_seconds).
This gives "the total number of seconds contained in the duration" and is
described as equivalent to `diff / timedelta(seconds=1)`.

Here is the [updated version of `format_time_delta`](https://github.com/jbranchaud/py-vmt/blob/ec1875a9d73552f5481e3945ddf522e94d0cc018/src/py_vmt/time_helpers.py?plain=1#L11-L16):

```python
def format_time_delta(diff: timedelta) -> str:
    total_seconds = int(diff.total_seconds())

    hours, remainder = divmod(total_seconds, 3600)
    minutes, remainder = divmod(remainder, 60)
    seconds = remainder
```
