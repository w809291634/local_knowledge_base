# Use The Readline Keybindings Anywhere

There are these features of the "shell" that I've often heard called _emac
keybindings_. These are things like `ctrl-a` (move the cursor to the beginning
of the line) and `ctrl-e` (move the cursor to the end of the line) that I use
every single day. There are several others that are in my heavy rotation,
however, I learned about a couple more reading through [Shell Tricks That
Actually Make Life Easier (And Save Your
Sanity)](https://blog.hofstede.it/shell-tricks-that-actually-make-life-easier-and-save-your-sanity/).

These are [Readline commands](https://www.gnu.org/software/bash/manual/html_node/Bindable-Readline-Commands.html)
(or keybindings) which means they are supported by anything that uses Readline
under the hood. So while you might be using these to great effect in `bash` and
`zsh`, you should look for other places they are available.

A non-exhaustive list includes:

- Ruby's `irb`
- Python's `python`
- Node.js' `node`
- PostgreSQL's `psql`
- Claude Code

And many more similar REPLs and command line tools.

Try these keybindings out in one of your favorites and when you're done hit
`ctrl-c` to exit out of it.

PS. subsets of these keybindings are sometimes supported in unexpected places
like the Chrome URL bar.
