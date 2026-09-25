# Define Sequence Of Tests With Parametrize Decorator

I have a function that I want to test across a bunch of different inputs. That
way I can make sure the logic of that function handles all the different
scenarios I have in mind.

While working on [`py-vmt`](https://github.com/jbranchaud/py-vmt), I started by
writing a big single test function with a sequence of variable assignments and
`assert` statements. Here's my starting point:

```python
def test_format_time_delta_everything():
    # less than a minute
    thirty_seconds = timedelta(seconds=30)
    assert "30s" == format_time_delta(thirty_seconds)

    # one minute exactly
    one_minute = timedelta(seconds=60)
    assert "1m" == format_time_delta(one_minute)

    # more than a minute
    assert "1m30s" == format_time_delta(one_minute + thirty_seconds)

    # bunch of minutes and seconds
    delta = timedelta(minutes=24, seconds=8)
    assert "24m8s" == format_time_delta(delta)

    # one hour exactly
    one_hour = timedelta(hours=1)
    assert "1h" == format_time_delta(one_hour)

    # more than one hour
    assert "1h24m" == format_time_delta(one_hour + delta)
```

I knew I would eventually need to break it up into individual test functions,
but I couldn't bare to start there because it seemed quite repetitive.

There is another way to approach this without all the duplication. Pytest comes
with [a "parametrize" decorator](https://docs.pytest.org/en/stable/example/parametrize.html). This is
used to define a set of test data (and expected values) that will get passed
one-by-one to the test function as parameters.

```python
@pytest.mark.parametrize("input,expected", [
    (timedelta(seconds=30), "30s"),
    (timedelta(seconds=60), "1m"),
    (timedelta(seconds=90), "1m30s"),
    (timedelta(minutes=24, seconds=8), "24m8s"),
    (timedelta(hours=1), "1h"),
    (timedelta(hours=1, minutes=24, seconds=8), "1h24m"),
])
def test_format_time_delta(input, expected):
    assert format_time_delta(input) == expected
```

I ditch all of the duplication this way. I define a list of tuples that
represent my input values and expected values. Then the body of the test can be
minimal. And I get a separate test execution for each parameter tuple making it
easier to see fine-grained pass/fail results.
