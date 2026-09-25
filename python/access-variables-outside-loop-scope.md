# Access Variables Outside Loop Scope

Here is a function that loops over a list to find the first occurrence of a
falsy value.

```python
def find_false(self):
    for item in self.items:
        item_type = type(item)
        print(f"Current item: {item} ({item_type})")
        if not item:
            break

    print(f"First false item: {item} ({item_type})")
```

Notice how at the end of the function, outside of the loop, I am able to access
both `item` (defined in the loop definition) and `item_type` (defined within the
loop's body).

Both of these variables are defined, by the loop, in _function scope_ and are
accessible anywhere in the function after they have been defined.

The title of this TIL is a bit of a misnomer because Python doesn't have the
concept of a _loop scope_. There are two levels of scope in Python --
module/global scope and function scope.

I spend most of my time writing Ruby which also has _block scope_, so Python's
simplified two-level scoping took me by surprise.

Though the code sample above is contrived, this function scope assignment can be
taken advantage of with loop definitions in scenarios where you want to know
what the last `item` defined was before the loop terminated.

```python
for submission in submissions:
    if passes(submission, criteria):
        break
else:
    raise ValueError("No submissions that meet given criteria")

print(f"Submit first passing submission: {submission.id}")
submit(submission)
```
