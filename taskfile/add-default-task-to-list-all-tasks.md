# Add Default Task To List All Tasks

One thing I like about [`just`](https://github.com/casey/just) is that if you
run `just` by itself, the default behavior is to list out all the commands it
can run.

[Taskfile](https://github.com/go-task/task) technically does this as well, but
with a warning at the end:

```
❯ task
task: Available tasks for this project:
* notes:              Interactive picker for notes tasks
* notes:diff:         Show uncommitted changes in notes
* notes:edit:         All-in-one edit, commit, and push notes
* notes:log:          Show recent commit history for notes
* notes:open:         Opens NOTES.md (syncs latest changes first) in default editor
* notes:push:         Commit and push changes to notes submodule
* notes:status:       Check status of notes submodule
* notes:sync:         Sync latest changes from the notes submodule
task: Task "default" does not exist
```

I prefer to tidy this up a little by adding `task --list` as the _default_ in my
`Taskfile.yml`.

```yml
  default:
    desc: Show available commands
    cmds:
      - task --list
```

Now when I run `task` with no arguments, I get this minutely nicer version:

```
❯ task
Alias tip: t
task: [default] task --list
task: Available tasks for this project:
* default:            Show available commands
* notes:              Interactive picker for notes tasks
* notes:diff:         Show uncommitted changes in notes
* notes:edit:         All-in-one edit, commit, and push notes
* notes:log:          Show recent commit history for notes
* notes:open:         Opens NOTES.md (syncs latest changes first) in default editor
* notes:push:         Commit and push changes to notes submodule
* notes:status:       Check status of notes submodule
* notes:sync:         Sync latest changes from the notes submodule
```

Notice there is no `task: Task "default" does not exist` warning at the end.
