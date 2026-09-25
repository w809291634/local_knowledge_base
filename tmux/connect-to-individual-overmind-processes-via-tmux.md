# Connect To Individual Overmind Processes Via tmux

A common `Procfile.dev` in a Rails project might look something like this.

```
web: bin/rails server -p $PORT
vite: bin/vite dev
worker: bundle exec good_job start
```

Instead of starting up each process that needs to be running for development to
work, I can instead run a tool that reads the procfile and sets it all up for me
-- like `overmind`.

```bash
❯ overmind start -f Procfile.dev
```

What's cool about `overmind` is that it starts its own `tmux` session and then
runs each of these processes in its own window.

I can connect to any one of them by name with `overmind connect <name>`. Or I
can connect to the session defaulting to the first window with just `overmind
connect`.

If I need to see what is going on with my background jobs, I'll run:

```bash
❯ overmind connect worker
```

This behaves like any other tmux session, so I can use my prefix key (`ctrl-z`
in my case) to access tmux-specific keybindings. Most notably, once I'm done
looking, I'll want to hit `ctrl-z d` to detach from the session.

I'm already using tmux as my daily driver which means its easy for me to end up
in a nested tmux session if I connect while already in my development session.
To help with that, I set up [a forwarding
prefix](set-up-forwarding-prefix-for-nested-session.md).
