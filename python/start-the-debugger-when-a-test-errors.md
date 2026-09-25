# Start The Debugger When A Test Errors

While working on [some
tests](https://github.com/jbranchaud/build-an-llm-from-scratch/blob/main/tests/chapter_02/test_bpe_tokenizer.py)
for my Byte Pair Encoding tokenizer, I was running into an unexpected test
failure. To better understand what was going on, I needed to inspect the state
of the program around the time the code raised an exception.

Instead of needing to manually set a breakpoint at the correct spot to begin
debugging, I can run the test with the Pytest-supported `--pdb` flag. That's
short for _python debugger_.

> Start the interactive Python debugger on errors or KeyboardInterrupt

What this does during a test run is opens you up to the interactive Python
debugger at the exact moment an exception is raised. This gives you the ability
to inspect values of the program state at that point in execution which could
help inform the needed fix.

```bash
uv run pytest -vv --pdb -k "test_train_bpe"
```

There I am running a specific test that matches against `-k "test_train_bpe"`
and the python debugger will start up if there is an error.

See `uv run pytest --help` for more details.
