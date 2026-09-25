# Specify Parameter Name For Click Option

[Click](https://click.palletsprojects.com/en/stable/)'s option decorator
provides a versatile way to define flags for a command. It has good defaults
that minimize the aspects of a flag that I need to be explicit about.

For example, a boolean `--init` flag for the `config` command could be specified
like so:

```python
@cli.command()
@click.option(
    "--init",
    help="Initialize a config file with minimal defaults",
    is_flag=True,
)
@pass_cli
def config(cli_ctx: CliContext, init: bool):
    # ...
```

Notice, in particular, that the flag string (`--init`) that I pass as the first
argument to `@click.option` has to correspond to the name of the parameter
`init`. Click passes all the defined options as keyword arguments when invoking
`config`. If the `init` parameter was changed to `initial`, there would be a
runtime error like this: `TypeError: config() got an unexpected keyword argument 'init'`.

Like I said though, Click is flexible when I need it to be. I can leave the flag
name as it is, but specify a different name to be used for the function
parameter. I found this useful when I realized that as I added support for a
`--json` flag I was inadvertently superseding the `json` import.

The second positional argument to `@click.option` can be included to rename that
parameter:

```python
import json


@cli.command()
@click.option(
    "--json",
    "use_json",
    help="Output all info details in JSON format",
    is_flag=True,
)
@pass_cli
def info(cli_ctx: CliContext, use_json: bool):
    # ...

    if use_json:
        click.echo(json.dumps(info_details, indent=2))
```

Both of these code blocks are excerpts from my [`py-vmt` time tracker project](https://github.com/jbranchaud/py-vmt).
