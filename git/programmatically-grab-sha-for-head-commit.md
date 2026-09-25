# Programmatically Grab SHA For Head Commit

When I use `gh browse path/to/some-file.txt`, it opens the browser to that file
in GitHub. However, it targets the default branch (`main`) by default which is
not very useful as a permalink because what that file looks like on `main` is
liable to change.

There is a `--commit` flag you can use to have it instead open to that file at a
specific commit SHA.

So what SHA do I pass as an argument to that flag?

Often what I would like to grab is a reference to the current version of the
file which is whatever it looks like for the `HEAD` commit. But `HEAD` is
another moving target reference. The `git rev-parse` command can translate
`HEAD` into a specific SHA though.

```bash
❯ git rev-parse --short HEAD
3402428

❯ git rev-parse HEAD
3402428aadc02cfdc9825c8feb593443e72f50cd
```

Either of those will work. I can use a bash command substitution then to tie it
all together into a single command:

```bash
❯ gh browse path/to/some-file.txt --commit=$(git rev-parse --short HEAD)
```

See `man git-rev-parse` for more details.
