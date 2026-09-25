# Assert Is Only A Development Check

The `assert` keyword is used in Python to write a statement that will check some
assertion and raise an error if it isn't met. This is only meant to be used as a
check during development because it can be easily optimized out of the code.

```python
stuff = None

assert stuff, "We need to have some stuff to proceed"

print(f"We have {stuff or 'something'}!")
```

If I execute this code with `python`, it will raise on that second line of code.

```bash
❯ python assert_example.py
Traceback (most recent call last):
  File "/Users/lastword/dev/jbranchaud/py-vmt/assert_example.py", line 3, in <module>
    assert stuff, "We need to have some stuff to proceed"
           ^^^^^
AssertionError: We need to have some stuff to proceed
```

This `assert` statement will be stripped out of the compiled bytecode if the
`-O` (capital o) flag is used. Notice how running the same file with that flag
does not lead to an `AssertionError`.

```python
❯ python -O assert_example.py
We have something!
```

If I want to make sanity checks for situations that would be caused by a bug in
the code, an `assert` statement can be a good candidate. However, if I am making
runtime checks like validating user input, then an `if` statement and raising
something like a `ValueError` is better.
