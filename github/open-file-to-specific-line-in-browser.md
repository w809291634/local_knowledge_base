# Open File To Specific Line In Browser

Often one of the best ways to point a teammate to a line of code is to share a
GitHub link to a specific file and line number. Sometimes even a specific
commit.

For the longest time I would manually open GitHub, navigate to that file, and so
forth. The `gh` CLI supports this with the `browse` subcommand and it takes way
less time if you already have the repo in your local filesystem.

For instance, if I want to point you to line 11 of the `zshrc.local` file in my
`dotfiles` repo, I can run the following command:

```bash
$ gh browse zshrc.local:11
```

That would open a browser tab to
[https://github.com/jbranchaud/dotfiles/blob/main/zshrc.local?plain=1#L11](https://github.com/jbranchaud/dotfiles/blob/main/zshrc.local?plain=1#L11).

If I wanted a range of lines, I could change it from `11` to, say, `11-27`:

```bash
$ gh browse zshrc.local:11-27
```

And I would see this in the browser --
[https://github.com/jbranchaud/dotfiles/blob/main/zshrc.local?plain=1#L11-L27](https://github.com/jbranchaud/dotfiles/blob/main/zshrc.local?plain=1#L11-L27).

Both of these URLs are pointing to the `main` branch. If I instead want to
reference a specific commit, I can use the `--commit` flag.

```bash
$ gh browse zshrc.local:11-27 --commit=f2f9e78d4fc784643f725c88f7a5a7a077e7f261
```

I grabbed that from the latest commit in `git log`. That opens to
[https://github.com/jbranchaud/dotfiles/blob/f2f9e78d4fc784643f725c88f7a5a7a077e7f261/zshrc.local?plain=1#L11-L27](https://github.com/jbranchaud/dotfiles/blob/f2f9e78d4fc784643f725c88f7a5a7a077e7f261/zshrc.local?plain=1#L11-L27).

Another way of doing that would be to use `git rev-parse HEAD`:

```bash
$ gh browse zshrc.local:11-27 --commit=$(git rev-parse HEAD)
```

See `gh browse --help` for more details.
