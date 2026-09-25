# Avoid Modification With Frozen Dataclass

The `@dataclass` decorator can be set as _frozen_ to prevent modification of
values on instances of that `dataclass`.

Without making it frozen, I can easily subvert validations by changing the value
of attributes after the `__post_init__` validations are called.

```python
>>> config = BPEConfig(300, []) # passes validations
>>> config.vocab_size = 22 # this is invalid, wish this was prevented
```

Here is the updated `@dataclass` declaration with `frozen=True` passed as a
parameter.

```python
from dataclasses import dataclass
from typing import ClassVar

@dataclass(frozen=True)
class BPEConfig:
    BASE_VOCAB_SIZE: ClassVar[int] = 256

    vocab_size: int
    special_tokens: list[str]

    def __post_init__(self):
        if self.vocab_size < self.BASE_VOCAB_SIZE:
            msg = f"vocab_size ({self.vocab_size}) must be greater than or equal to BASE_VOCAB_SIZE ({self.BASE_VOCAB_SIZE})"
            raise ValueError(msg)
```

Now I am prevented from modifying a scalar value like `vocab_size` after the
instance has been created.

```python
>>> config = BPEConfig(300, [])
>>> config.vocab_size = 22
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<string>", line 4, in __setattr__
dataclasses.FrozenInstanceError: cannot assign to field 'vocab_size'
```

This doesn't prevent you from modifying the contents of attributes that are
`list` or `dict` types.
