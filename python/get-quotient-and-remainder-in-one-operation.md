# Get Quotient And Remainder In One Operation

While writing some custom code to transform a number of seconds into the
constituent hours, minutes, and seconds, I found myself needing to get both the
quotient and remainder from a division between two numbers.

```python
>>> import math
>>> math.floor(3666 / 3600)
1
>>> 3666 % 3600
66
```

Instead, I can use Python's built-in
[`divmod`](https://docs.python.org/3/library/functions.html#divmod) function to
compute both values in one statement.

```python
>>> divmod(3666, 3600)
(1, 66)
```

The result is a tuple with the first value being my quotient (in this case, the
number of hours) and the remainder (the remaining number of seconds).

This kind of operation is known as [Euclidian
Division](https://en.wikipedia.org/wiki/Euclidean_division).

Here is a snippet of some actual code where I use this in
[`py-vmt`](https://github.com/jbranchaud/py-vmt/blob/b9eae8b258e9fd720cfa3bb63b601225df352051/src/py_vmt/time_helpers.py#L14-L16):

```python
def format_time_delta(diff: timedelta) -> str:
    total_seconds = int(diff.total_seconds())

    hours, remainder = divmod(total_seconds, 3600)
    minutes, remainder = divmod(remainder, 60)
    seconds = remainder

    # ...
```
