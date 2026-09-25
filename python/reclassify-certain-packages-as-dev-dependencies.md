# Reclassify Certain Packages As Dev Dependencies

When I first started working on [py-vmt](https://github.com/jbranchaud/py-vmt),
I wasn't differentiating certain test packages as _dev_ dependencies as opposed
to standard, production dependencies. This can lead to bloated installs across a
variety of distribution channels.

Notice that I have everything treated as production dependencies:

```bash
❯ uv tree --no-dev
Resolved 18 packages in 2ms
py-vmt v0.1.0
├── click v8.3.1
├── dateparser v1.3.0
│   ├── python-dateutil v2.9.0.post0
│   │   └── six v1.17.0
│   ├── pytz v2026.1.post1
│   ├── regex v2026.2.28
│   └── tzlocal v5.3.1
├── freezegun v1.5.5
│   └── python-dateutil v2.9.0.post0 (*)
├── platformdirs v4.9.4
├── pytest v9.0.2
│   ├── iniconfig v2.3.0
│   ├── packaging v26.0
│   ├── pluggy v1.6.0
│   └── pygments v2.19.2
└── types-dateparser v1.3.0.20260211
(*) Package tree already displayed
```

`pytest`, `freezegun`, and `types-dateparser` are better suited as _dev_
dependencies.

I can reclassify them by moving them from `dependencies` into a `dev` dependency
group in `pyproject.toml`:

```toml
dependencies = ["click>=8.3.1", "dateparser>=1.3.0", "platformdirs>=4.9.4"]
[dependency-groups]
dev = ["freezegun>=1.5.5", "pytest>=9.0.2", "types-dateparser>=1.3.0.20260211"]
```

I only had `dependencies` before, so I had to add `[dependency-groups]` and `dev = []` to my `pyproject.toml` file.

I can then tell `uv` to sync up the installation and virtualenv based on the new
organization of the dependencies.

```bash
❯ uv sync
warning: Skipping installation of entry points (`project.scripts`) because this project is not packaged; to install entry points, set `tool.uv.package = true` or define a `build-system`
Resolved 18 packages in 518ms
```

Now when I check the `--no-dev` tree of dependencies, it's just the essentials:

```bash
❯ uv tree --no-dev
Resolved 18 packages in 1ms
py-vmt v0.1.0
├── click v8.3.1
├── dateparser v1.3.0
│   ├── python-dateutil v2.9.0.post0
│   │   └── six v1.17.0
│   ├── pytz v2026.1.post1
│   ├── regex v2026.2.28
│   └── tzlocal v5.3.1
└── platformdirs v4.9.
```

Another way to achieve this would have been to run `uv remove` and `uv add` with
the relevant sets of package names. In retrospect, I would have preferred using
that approach in the first place. If you're wanting to be pinned to specific
versions of certain packages, you'd have to be a little more careful to get this
right.
