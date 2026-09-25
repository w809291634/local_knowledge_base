# Avoid Vulnerabilities In New Package Versions

It seems like every week there is a new supply chain attack where malicious code
is embedded in a popular, widely-used OSS package. This week's is
[axios](https://www.stepsecurity.io/blog/axios-compromised-on-npm-malicious-versions-drop-remote-access-trojan).

The [`pnpm` package manager](https://pnpm.io/) has a nice feature that helps
avoid installing these vulnerable package versions in the first place.

> To reduce the risk of installing compromised packages, you can delay the
> installation of newly published versions. In most cases, malicious releases
> are discovered and removed from the registry within an hour.

The [`minimumReleaseAge` config option](https://pnpm.io/settings#minimumreleaseage) tells `pnpm` to not install
a dependency (including transitive ones) until it has been released for at least
that many minutes.

For instance, if you wanted to set this to 72 hours, then you'd set this option
to `4320` minutes like so:

```
$ pnpm config set minimum-release-age 4320 -g
```

The global flag (`-g`) will set that in your global config location, e.g.
`$XDG_CONFIG_HOME/pnpm/rc`. You could also add it specifically to your project
in the `pnpm-workspace.yaml` file.

[source](https://bsky.app/profile/styfle.dev/post/3miekuyeyrs2w)
