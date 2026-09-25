# Display All Git Log Entries In My Local Timezone

I tend to work with remote teams distributed across across multiple time zones.
In that context, it is important to have an awareness of what time zone each
person is operating in and to communicate clearly around that.

When looking at the output for `git log` on a distributed team, the timestamps
for each entry can be all over the place. If I want to understand when something
was committed, I have to look at the time as well as the time zone offset and
mentally translate it to my own time zone.

There is a `git config` option to alleviate this issue by having `git log`
convert and display all timestamps into your local time zone.

```bash
$ git config --global log.date rfc-local
```

Running that will add this entry to your _global_ git config file:

```
[log]
	date = rfc-local
```

Now the time that was displaying as `Wed Apr 8 20:12:33 2026 -0400` will display
as `Wed, 8 Apr 2026 19:12:33 -0500`.

This also helps with smoothing out differences from DST and for commits produced
by AI agents in sandbox environments where the locale is set to UTC.
