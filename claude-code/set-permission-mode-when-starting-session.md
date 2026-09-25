# Set Permission Mode When Starting Session

The way I typically use Claude Code day-to-day is with a couple long-running
sessions for one to two clones of the project. I start a session with `claude`
and then hit `shift+tab` until I've toggled it to _auto_ mode. I do tightly
scoped features and `/clear` the context in between each.

I get used to being in _auto_ mode, so whenever I start a new `claude` session I
forget to first toggle from _manual_ to _auto_ mode.

This is where the
[`--permission-mode`](https://code.claude.com/docs/en/permission-modes) flag can
help. I can start a session directly in _auto_ mode like so:

```bash
❯ claude --permission-mode auto
```

Or if I know I want to generate a plan first, I can start it in _plan_ mode.

```bash
❯ claude --permission-mode plan
```

There is also the `--dangerously-skip-permissions` flag which is equivalent to
`--permission-mode bypassPermissions`. I tend to stay away from those unless I'm
working from a sandboxed dev container.

See `claude --help` for more details.
