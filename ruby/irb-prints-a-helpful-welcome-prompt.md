# IRB Prints A Helpful Welcome Prompt

I've been using `irb` for over 15 years as a REPL for executing Ruby code. It
has always been pretty plain in a lot of ways. For this reason, I often used
[`pry`](https://github.com/pry/pry) instead, especially in a Rails context.
`irb` has gotten notably better in recent years. I was delighted to recently
notice that earlier this year they landed delightful, colorful, and helpful
improvement to the welcome prompt.

It looks more or less like this:

```
❯ irb

⢀⡴⠊⢉⡟⢿  IRB v1.18.0 - Ruby 3.4.4
⣎⣀⣴⡋⡟⣻  "ls [object] -g pattern" to filter methods and properties
⣟⣼⣱⣽⣟⣾  ~/dev/jbranchaud/pool-league-pro

irb(main):001>
```

Notice it includes a random tip on the second line. I had no idea you could
include `-g pattern` with an `ls`, so that will likely be landing as a new TIL
soon.

This improved welcome message has been available since `1.18.0` and originated
in [this PR](https://github.com/ruby/irb/pull/1183).
