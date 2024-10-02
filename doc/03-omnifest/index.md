# Omnifest

An omnifest is the name for the YAML-based format that is used by `otk` as its input. `otk` transforms omnifests into inputs for other image build tools. To do so it works with [directives](./01-directive.md).

## Entrypoint

As omnifests can include other omnifests it is important to note that `otk` treats the entrypoint omnifest differently from included omnifests. The entrypoint omnifest is the file that is passed to `otk compile [file]`. This entrypoint is required to have:

1. An [otk.version](./01-directive.md#otkversion) directive.
1. An [otk.target](./01-directive.md#otktarget) directive.

A minimal entrypoint would look like:

```yaml
otk.version: "1"

otk.target.osbuild:
  example: "data"
```

## Targets

The [otk.target.\<consumer\>(.\<name\>)](./01-directive.md#otktargetconsumername) directives in the omnifest provide the umbrella to put exports under. They are namespaced to a specific consumer (e.g. `osbuild`).

An omnifest that contains a single target will use that target by default:

```
€ otk compile example.yaml  # example from above
# ...
```

When a file contains multiple targets an error will be shown; you'll have to select the target you want to export.


```
€ otk compile example.yaml  # contains `osbuild.ami` and `osbuild.iso` targets
CRITICAL:otk.command:INPUT contains multiple targets, `-t` is required
€ otk compile example.yaml -t osbuild.iso
# ...
```

Only a single target can be selected for export at a time.
