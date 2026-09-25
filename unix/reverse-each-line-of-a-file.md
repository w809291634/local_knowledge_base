# Reverse Each Line Of A File

The [`rev` command](https://man7.org/linux/man-pages/man1/rev.1.html) can be
used to reverse each line in a file. Every line is left where it is relative to
other lines, but the contents of each line is reversed.

So a file that contains the following text:

```bash
❯ cat stuff.md
Three
Two
One
go racecar go
```

can be piped to `rev` to get the following output:

```bash
❯ rev stuff.md
eerhT
owT
enO
og racecar og
```

This is an odd utility that doesn't have too much use that I can imagine. After
a brief chat with Claude where I asked for some practical use cases, the one
that stood out the most to me is to reverse a list of filenames, sort them, and
then reverse them again (putting them back in readable order). This can shuffle
filenames with similar endings near each other like source and test files.

Here is a list of files for me [`py-vmt`
project](https://github.com/jbranchaud/py-vmt):

```bash
❯ fd -t f .
README.md
pyproject.toml
src/py_vmt/__init__.py
src/py_vmt/cli.py
src/py_vmt/session.py
src/py_vmt/time_helpers.py
tests/src/py_vmt/test_cli.py
tests/src/py_vmt/test_session.py
```

Now I can pipe the output of that `fd` command through `rev | sort | rev` to get
my files organized in a different way.

```bash
❯ fd -t f . | rev | sort | rev
README.md
pyproject.toml
src/py_vmt/__init__.py
tests/src/py_vmt/test_cli.py
src/py_vmt/cli.py
tests/src/py_vmt/test_session.py
src/py_vmt/session.py
src/py_vmt/time_helpers.py
```

Again the value of doing something like this is a bit tenuous. At the very least
it is fun to know about.
