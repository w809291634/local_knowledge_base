# Count Number Of Tokens In A File

Over time you have accumulated a bunch of small directives, corrections, and
project details in your `CLAUDE.md` or `AGENTS.md` file. The file doesn't seem
too big, but you are mindful that it is being included in every prompt. How many
tokens is it eating from the context window?

OpenAI's BPE (Byte Pair Encoding) tokenization library,
[`tiktoken`](https://github.com/openai/tiktoken), is an open-source Python
package. If it is installed on our machine, then we can use it as part of the
following one-liner to check a file:

```bash
❯ python -c "import tiktoken, sys; print(len(tiktoken.encoding_for_model('gpt-4o').encode(open(sys.argv[1], 'r', encoding='utf-8').read())))" \
    AGENTS.md
1018
```

I ran this against the `AGENTS.md` file in a team project I'm on. It came out to
1018 tokens. This is a very good approximation based on the tokenizer trained
for `gpt-4o`. The tokenizers may vary a little from model to model, but the
differences for our purposes here are going to be negligible.

This one-liner gets the "first" argument to the command, reads it in, and runs
that string against the tokenizer. The length of the tokenized encoding is then
printed.
