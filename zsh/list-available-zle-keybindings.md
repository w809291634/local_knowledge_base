# List Available Zle Keybindings

Unlike `bash` which uses `readline`, `zsh` has its own implementation of a line
editing library -- `zle`. A lot of the core bindings between the two are the
same, e.g. `Ctrl-a` and `Ctrl-e` to go the beginning and end of the command line
prompt, respectively.

All available `zle` keybindings can be listed out by running `bindkey` without
any arguments.

The best way to check out an unaltered version of this list is by starting a
fresh `zsh` process with no RCS files loaded in. The `-f` flag does that. Note
though that when `zsh` is starting fresh, it has to decide whether to start in
_Emacs_ mode or _Vi_ mode. If it sees that your default editor is something like
`vi`, `vim` or `nvim`, then it will start you in _Vi_ mode.

Starting in _Vi_ mode can be confusing because none of the standard _Emacs_
keybindings like `Ctrl-a` and `Ctrl-e` are available in that context. So first
ensure you're in _Emacs_ mode by running:

```sh
❯ zsh -f
lastword% bindkey -e
```

Now you can list out all the keybindings:

```sh
lastword% bindkey
"^@" set-mark-command
"^A" beginning-of-line
"^B" backward-char
"^D" delete-char-or-list
"^E" end-of-line
"^F" forward-char
"^G" send-break
"^H" backward-delete-char
"^I" expand-or-complete
"^J" accept-line
"^K" kill-line
...
```

See `man zshzle` for more details on `zle` and `bindkey`.
