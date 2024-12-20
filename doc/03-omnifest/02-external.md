# External

External directives are directives that are implemented externally from `otk`.
They are meant to be used to provide target-specific behavior and can be used
to express things where `otk` is not expressive enough.

## Protocol

Directives are small executables that receive JSON and are expected to output
JSON again in a specific format. Additional keys are not allowed.

When we have an [omnifest](./index.md) that looks like this:

```yaml
otk.external.name:
  child:
    - 1
  options: "are here"
```

The external gets called with the following JSON:

```json
{
  "tree": {
    "child": [1],
    "options": "are here"
  }
}
```

And is expected to return a JSON dict with a single top-level `tree` object that can contain arbitrary values. Additional top-level keys are not allowed. Example:

```json
{
  "tree": {
    "what": {
      "you": "want"
    }
  }
}
```

Which will replace the previous `otk.external.name` subtree with the output of new subtree from the external command. Example:

```yaml
tree:
  what:
    you: "want"
```

If the external returns `{}`, an empty object, `otk` will assume that there is
no tree to replace and remove the node instead. This will turn the following
YAML:

```yaml
dummy:
  otk.external.name:
    options:
```

Into this YAML structure:

```yaml
dummy:
```

## Example

The following example demonstrates how an external can be used to implement string
concatenation.

Given the following script called `concat` in `/usr/local/libexec/otk/concat`:

```bash
#!/usr/bin/env bash

output="$(cat - | jq -jr '.tree.parts[]')"
echo "{\"tree\":{\"output\":\"$output\"}}"
```

and the following directive:

```yaml
examplestring:
  otk.external.concat:
    parts:
      - list
      - of
      - strings
```

the script is called with the following data on stdin:

```json
{
  "tree": {
    "parts": [
      "list",
      "of",
      "strings"
    ]
  }
}
```

which results in the following output:

```json
{
  "tree": {
    "output": "listofstrings"
  }
}
```

and the final omnifest will be:

```yaml
examplestring:
  output: listofstrings
```

## Paths

`otk` will look for external directives in the following paths, stopping when
it finds the first match:

- A path defined by the `OTK_EXTERNAL_PATH` environment variable.
- `/usr/local/libexec/otk/external`
- `/usr/libexec/otk/external`
- `/usr/local/lib/otk/external`
- `/usr/lib/otk/external`

The filename for an external executable is based on the external name. When the
following directive is encountered: `otk.external.<name>` then
`otk` will try to find an executable called `<name>` in the previously
mentioned search paths.

Examples:

- `otk.external.foo` -> `foo`
- `otk.external.osbuild-bar` -> `osbuild-bar`

## Naming

So far we've followed a common naming scheme for the externals we're providing.
So far externals usually generate defines which are then later used by other
externals to transform those variables into (for example) `osbuild` stages or
sources.

For our naming we prefix the externals that generate variables in a define block
with: `osbuild-gen-` which indicates that this external is meant for use with
`osbuild` and that it *generates* variables.

Externals that use (generated) variables follow the idiom of `osbuild-make-`.

As an example the `osbuild-gen-depsolve-dnf4` external will dependency solve its
options into a bunch of variables which are then later used to generate stages in
an `osbuild` target with `osbuild-make-depsolve-dnf4-rpm-stage` and sources with
`osbuild-make-depsolve-dnf4-curl-source`.

## Implementations

`otk` currently ships together with some external implementations to work with
`osbuild`.

### `osbuild-gen-depsolve-dnf4`.

The `osbuild` target requires a list of solved packages and sources in its manifest.
The `osbuild-gen-depsolve-dnf4` external is used to generate these based on a list
of packages to be included and excluded.

This external requires `osbuild-depsolve-dnf` to be installed on the system that runs
`otk`.

An example invocation is like this:

```yaml
otk.define:
  packages:
    otk.external.osbuild-gen-depsolve-dnf4:
      architecture: "x86_64"
      module_platform_id: "c9s"
      releasever: "9"
      repositories:
        - id: "foo"
          baseurl: "https://example.com/"
        - id: "bar"
          baseurl: "https://example.com/"
      packages:
        include:
          - "@core"
        exclude:
          - "foo"
```

The result in the `packages` variable can then be used by other externals.

### `osbuild-make-depsolve-dnf4-rpm-stage`

Use the generated defines from `osbuild-gen-depsolve-dnf4` to create an RPM
stage for an `osbuild` manifest:

```yaml
otk.external.osbuild-make-depsolve-dnf4-rpm-stage:
  packageset: ${packages}  # generated by `osbuild-gen-depsolve-dnf4`
  gpgkeys:
    - "---"
    - "---"
```

### `osbuild-make-depsolve-dnf4-curl-source`

Use the generated defines from `osbuild-gen-depsolve-dnf4` to create a sources
list for an `osbuild` manifest.

```yaml
otk.target.osbuild:
  sources:
    otk.external.osbuild-make-depsolve-dnf4-curl-source:
      packagesets:
        - ${packages}  # generated by `osbuild-gen-depsolve-dnf4`
```

### `osbuild-gen-partition-table`

The `osbuild-gen-partition-table` generates defines for stages and mounts that
create filesystems and partition tables in `osbuild`.

```yaml
otk.define:
  filesystem:
    otk.external.osbuild-gen-partition-table:
      modifications: {}  # empty
      properties:
        type: gpt
        bios: true
        default_size: "10 GiB"
        uuid: D209C89E-EA5E-4FBD-B161-B461CCE297E0
        create:
          bios_boot_partition: false
          esp_partition: true
          esp_partition_size: "200 MiB"
      partitions:
        - name: boot
          mountpoint: /boot
          label: boot
          size: "1 GiB"
          type: "xfs"
          fs_mntops: defaults
          # XXX: should we derive this automatically from the mountpoint?
          part_type: BC13C2FF-59E6-4262-A352-B275FD6F7172
          # we use hardcoded uuids for compatibility with "images"
          part_uuid: CB07C243-BC44-4717-853E-28852021225B
        - name: root
          mountpoint: /
          label: root
          type: "xfs"
          size: "2 GiB"
          fs_mntops: defaults
          # XXX: should we derive this automatically from the mountpoint?
          part_type: 0FC63DAF-8483-4772-8E79-3D69D8477DE4
          # we use hardcoded uuids for compatibility with "images"
          part_uuid: 6264D520-3FB9-423F-8AB8-7A0A8E3D3562
  # XXX: it would be nicer if the "fs_options" could be part of their
  # stages directly without this indirection.
  fs_options:
    otk.external.osbuild-make-partition-mounts-devices:
      ${filesystem}
```

### `osbuild-make-partition-mounts-devices`

Creates mounts and devices for `osbuild` based on the
`osbuild-gen-partition-table` external.

```yaml
otk.external.osbuild-make-partition-mounts-devices:
  ${filesystem}  # generated by `osbuild-gen-partition-table`
```

### `osbuild-make-partition-stages`

Creates stages for `osbuild` based on the `osbuild-gen-partition-table`
external.

The following example generates the stages and copy-to-device stages for
an image pipeline:

```yaml
otk.op.join:
  values:
    - otk.external.osbuild-make-partition-stages:
        ${filesystem}  # generated by `osbuild-gen-partition-table`
    - - type: org.osbuild.copy
        inputs:
          root-tree:
            type: org.osbuild.tree
            origin: org.osbuild.pipeline
            references:
              - name:os
        options:
          paths:
            - from: input://root-tree/
              to: mount://-/
        devices:
          ${fs_options.devices}  # generated by `osbuild-gen-partition-table`
        mounts:
          ${fs_options.mounts}  # generated by `osbuild-gen-partition-table`
```

### `osbuild-gen-inline-files`

Generate variables for inline files so they can be used as `osbuild` sources:

```yaml
files:
  otk.external.osbuild-gen-inline-files:
    inline:
      kickstart:
        contents: |
          # Run initial-setup on first boot
          # Created by osbuild
          firstboot --reconfig
          lang en_US.UTF-8
```

### `osbuild-make-inline-source`

Use the variables as generated by `osbuild-gen-inline-files` to create the
necessary sources for `osbuild`.

```yaml
otk.external.osbuild-make-inline-source:
  const:
    files: ${files.const.files}
```
