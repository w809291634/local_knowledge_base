# List PRs Awaiting Your Review

If you work on a software team or steward an open-source project, then there are
likely some open PRs that you've been tagged to review. I am usually able to
catch most review requests as they come up either from the GitHub email
notifications or by keeping an eye on the PRs tab of active projects. Sometimes
I get consumed by a task and something slips through the cracks.

There are a couple other ways to quickly check if anything is waiting on my
review.

From the web UI I can visit the following URL which will show all PRs across all
projects where my review has been requested:

[https://github.com/pulls/review-requested](https://github.com/pulls/review-requested)

The GitHub CLI (`gh`) can do the same and I can do it right from the terminal
instead of navigating several clicks within GitHub's web UI.

```bash
$ gh search prs --review-requested=@me --state=open
```

That too will list PRs across all projects that are open and awaiting my review.

If that one ends up being a little too noisy, you can also use `gh` to _list_
just PRs for the current project:

```bash
$ gh pr list --search "review-requested:@me"
```
