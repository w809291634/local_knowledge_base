# Summarize Amount Of Change For Specific Commit

To get a quick headline summary of the amount of change that happened in a
commit, I can use the `--shortstat` flag. This will sum up file changed, lines
added, and lines removed. This can be combined with an _empty_ format flag to
suppress all other output.

I can run this for the latest commit on the current branch by referencing
`HEAD`.

```bash
❯ git show --shortstat --format= HEAD
 3 files changed, 1046 insertions(+), 462 deletions(-)
```

Or I can point at some other commit via its SHA:

```bash
❯ git show --shortstat --format= 8cbfcdd7
 1 file changed, 238 insertions(+)
```

I can even summarize the amount of change for the entire feature branch I'm
working on by referencing a range between `main` and the `HEAD` commit.

```bash
❯ git diff --shortstat main...HEAD
 36 files changed, 1125 insertions(+), 134 deletions(-)
```

See `man git-show` and `man git-diff` for more details.
