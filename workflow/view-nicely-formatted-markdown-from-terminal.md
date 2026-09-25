# View Nicely Formatted Markdown From Terminal

The [`glow`](https://github.com/charmbracelet/glow) utility is CLI markdown
renderer written in Go. It is part of the CCU
([charmbraclet](https://github.com/charmbracelet) CLI universe). And yes, I just
made up _CCU_.

`glow` is great because it processes and outputs a markdown file with some
styling tailored to a terminal including:

- colors to emphasize things like headings
- styling of inline code snippets
- syntax highlighting for fenced code blocks
- rendering of markdown tables
- and a lot more that I'm not thinking to mention

In the past I've installed this with `brew`, but I currently manage my `glow`
install with [this mise config](https://github.com/jbranchaud/dotfiles/blob/main/config/mise/config.toml?plain=1#L66).

To view a nicely rendered markdown file, I can run:

```bash
$ glow README.md
```

For long markdown files like [this `README.md`](https://github.com/jbranchaud/til/blob/master/README.md), this
doesn't work too well because it renders until the end and spits you at at the
bottom.

Fortunately, `glow` has a built-in pager that maintains all the styling while
allowing you to navigate and search similar to `less`.

```bash
$ glow -p README.md
```

There is also a TUI version (`-t`), but I find that less intuitive and useful
than the pager.

See `glow --help` for more details.
