# Sort Normalized Version Of Data

Let's say I have a list of names that I want to sort. However, because of
inconsistency in how the data was entered, sometimes those names are capitalized
and other times they are not. Using
[`methodcaller`](https://docs.python.org/3/library/operator.html#operator.methodcaller),
I can normalize the sorting `key` used when comparing list items.

First, let's look at calling `sorted` with the list and no `key`:

```python
>>> sorted(["butler", "Jemisin", "le guin", "Erdrich"])
['Erdrich', 'Jemisin', 'butler', 'le guin']
```

`butler` which starts with a `b` gets moved to the 3rd position because it is
lowercase.

To sort this list using a normalized comparison, we will use `methodcaller` to
create a callable out of `lower` which is then passed as the sort `key`:

```python
>>> from operator import methodcaller
>>> sorted(["butler", "Jemisin", "le guin", "Erdrich"], key=methodcaller("lower"))
['butler', 'Erdrich', 'Jemisin', 'le guin']
```

That's the sort order I was originally hoping for.

What `methodcaller` is doing is creating a callable function that will invoke
`lower` with each string instance as the target. Conceptually similar to
`"Erdrich".lower()` or even `getattr("Erdrich", "lower")()` (notice this needs
to be immediately invoked).
