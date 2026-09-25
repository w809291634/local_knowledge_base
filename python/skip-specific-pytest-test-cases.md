# Skip Specific Pytest Test Cases

While using a failing test case to build a small new feature for
[`py-vmt`](https://github.com/jbranchaud/py-vmt), I realized I needed to do some
refactoring first. It wasn't significant enough to warrant stashing my current
changes and switching to a different branch, so I kept all the changes around. I
did find the initial failing test distracting from the refactoring I was trying
to do. To temporarily shelve that failure, I can use a Pytest decorator to mark
it as _skipped_.

```python
@pytest.mark.skip(reason="not yet implemented")
def test_log_recent_activity():
    runner = CliRunner()

    # set up the data dir file with some existing session entries
    initial_datetime = datetime.datetime(
        2026, 3, 14, 15, 5, 11, 0, datetime.timezone.utc
    )
    with freeze_time(initial_datetime) as frozen_datetime:
        # ...
```

The [`@pytest.mark.skip` decorator](https://docs.pytest.org/en/stable/how-to/skipping.html#skipping-test-functions)
tells the Pytest runner to skip of that specific test case instead of executing
it. In the test runner output, I'll see an `s` rather than a `.` or `F` and the
summary will include it in a count of skipped tests:

```
=========================== 3 failed, 4 passed, 1 skipped in 0.09s ===========================
```

Another way to think about this is to mark this test case as _expected to fail_
with `@pytest.mark.xfail`. That will display as an `x` and show up in the summary as:

```
=========================== 3 failed, 4 passed, 1 xfailed in 0.11s ===========================
```
