# Omnifest

An omnifest is the name for the YAML-based format that is used by `otk` as its input. `otk` transforms omnifests into inputs for other image build tools. To do so it works with [directives](./directive).

## Entrypoint

As omnifests can include other omnifests it is important to note that `otk` treats the entrypoint omnifest differently from included omnifests. The entrypoint omnifest is the file that is passed to `otk compile [file]`. This entrypoint is required to have:

1. An [otk.version](./directive#otkversion) directive.
1. An [otk.target](./directive#otktarget) directive.

A minimal entrypoint would look like:

```yaml
otk.version: "1"

otk.target.osbuild.example:
  example: "data"
```

## Targets

The [otk.target.\<consumer\>.\<name\>](./directive#otktargetconsumername) directives in the omnifest provide the umbrella to put exports under. They are namespaced to a specific consumer (e.g. `osbuild`) and tell `otk` which [external](./external) directives are available, how to format the export, and how to validate the export.

An omnifest that contains a single target will use that target by default:

```
€ otk compile example.yaml  # example from above
# ...
```

When a file contains multiple targets an error will be shown; you'll have to select the target you want to export.


```
€ otk compile example.yaml  # contains `osbuild.bar` and `osbuild.foo` targets
[05/05/24 09:42:20] CRITICAL CRITICAL:otk.command:omnifest contains multiple targets, please select one with `-t`: ['osbuild.foo', 'osbuild.bar']
€ otk compile example.yaml -t osbuild.foo
# ...
```

Only a single target can be selected for export.
