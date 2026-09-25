# Stash The Current Prompt To Send Another First

I've been working my way through the current cohort of Matt Pocock's [Claude
Code for Real
Engineers](https://www.aihero.dev/cohorts/claude-code-for-real-engineers-2026-04).
The best part about going through a series of videos like this is being able to
pick up big and small tips and tricks from another person's workflow.

One of the small things I picked up in an early video is the ability to stash
the current prompt.

Let's say I've gone to the trouble of writing out a detailed prompt, `@`'ing
some files, and so forth. Then I realize I need first prompt Claude to do
something else first. Instead of copy-pasting that prompt into my notes,
deleting it, issuing a different prompt, and then pasting it back in, I can hit
`Ctrl-s`.

`Ctrl-s` will _stash_ the current prompt, clearing out the prompt input. I can
then type in something else. Once I hit enter for that new prompt, it will be
sent to Claude and the stashed prompt will be immediately populated back into
the input.

Though `Ctrl-s` is mentioned when you hit `?` from within `claude` session, I
don't see it documented anywhere in their [Interactive Mode
reference](https://code.claude.com/docs/en/interactive-mode).
