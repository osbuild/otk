# Directive

In [omnifests](./) directives are sections of the document that get transformed by `otk` into something else.

`otk` has various directives that can be used in an omnifest. Generally these directives can appear anywhere in the tree unless otherwise specified (see below) and they are replaced with other trees or values as produced by the directive.

There are [example omnifests](https://github.com/osbuild/otk/tree/main/example) for various distributions and images in a [source checkout](../installation).

## `otk.version`

### Example

```yaml
otk.version: "1"
```

## `otk.target.<consumer>.<name>`

Only act on this sub-tree if producing output for the specified consumer. Anything specific to the pipelines of e.g. osbuild would be put under `otk.target.osbuild`. This allows `otk` to infer context for the omnifest that is being processed.

A target is necessary for `otk` to generate any outputs. The target is namespaced to a specific application. `otk` tries to keep little context but it does need to know what it is outputting for. This allows us to scope [otk.external](#otkexternal) things to only be allowed within specific targets and for those externals to assume certain things will be in the tree.

The following values are valid for the `<consumer>` part of the key, this list can grow as other image build tooling is supported:

- `osbuild`

The `<name>` part of the key is free form and allows you to use a descriptive name for the export. Note that there MUST be no duplication of the `<consumer>.<name>` tuple.

```yaml
otk.target.osbuild.tree:
  pipelines:
    - otk.include: pipelines/root.yaml
    - otk.include: pipelines/tree.yaml
```

---

## `otk.define`

Defines variables that can be used through the `otk.variable` directive in
other parts of the omnifest.

Variable scope is global, an `otk.define` directive anywhere in the omnifest
tree will result in the defined names being hoisted to the global scope.

Redefinitions of variables are allowed. This allows for setting up default
values. If `-w duplicate-definition` is passed as an argument to `otk` then
`otk` will warn on all duplicate definitions.

Expects a `map` for its value.

```yaml
otk.define:
  packages:
    include:
      - @core
      - kernel
    exclude:
      - linux-util
  boot_mode: uefi
```

## Usage of `${}`

Use a previously defined variable. String values can be used inside other
string values, non-string values *must* stand on their own.

```yaml
otk.define:
  variable: "foo"

otk.include: ${variable}
```

If a `${}` appears in a `str` value then its string value as it appears
in `otk.define` is replaced into the string. Note that using the sugared form
in this form requires the value to be a string in the `otk.define`.

```yaml
# this is OK
otk.define:
  variable: aarch64

otk.include: path/${variable}.yaml
```

The following example is an error as the value of `variable` is a `seq`, which
is not allowed inside a string format.

```yaml
# this is NOT OK
otk.define:
  variable:
    - 1
    - 2

otk.include: path/${variable}.yaml
```

This is okay because `${variable}` is there on it's own so it's unambiguous.
```yaml
# this is OK
otk.define:
  variable:
    - 1
    - 2

some:
 thing: ${variable}
```

## `otk.include`

Include a file at this position in the tree, replacing the directive with the
contents of the file.

Note that cyclical includes are forbidden and will cause an error.

The short form expects a `str` for its value, the long form expects a `map` for
its value.

```yaml
otk.include: file.yaml
```

## `otk.op`

Perform various operations on variables.

### `otk.op.seq.join`

Join two or more variables of type sequence together, trying to join other types
will cause an error.

Expects a `map` for its value that contains a `values` key with a value of type
`seq`

```yaml
otk.define:
  a:
    - 1
    - 2
  b:
    - 3
    - 4
  c:
    otk.op.seq.join:
      values:
        - ${a}
        - ${b}
        - - 5
          - 6
```

### `otk.op.map.join`

Join two or more variables of type map together. Trying to merge other types
will cause an error. Duplicate keys in the maps are considered an error.

Expects a `map` for its value that contains a `values` key with a value of type
`seq`

```yaml
otk.define:
  a:
    a: 1
  b:
    b: 2
  c:
    otk.op.map.merge:
      values:
        - ${a}
        - ${b}
```

## `otk.meta.<name>`

Under the `otk.meta` namespace any data can be stored that other applications
need to use from an omnifest.

Expects a `map` for its value.

```yaml
otk.meta.osbuild-composer:
  boot_mode: uefi
  export: image
  pipelines:
    build:
      - root
    system:
      - tree

otk.meta.kiwi:
  label: "A Label"
```

## `otk.customization`

Customizations are conditional blocks that receive separate input through
`otk compile -Cname=data`, a customization is considered to be active when it
is passed data. If a customization is passed multiple times then the `defined`
block is repeated multiple times, once for each input.

Expects a `map` for its value which contains an `if-set` key. The `default` key
is optional. If a `default` key is not passed and the customization is inactive
then the customization block is effectively a no-op and will be removed from the
tree. The values of `default` and `if-set` can be of any type.

```yaml
otk.customization.name:
  default:
    - type: org.osbuild.stage
      options: none
  if-set:
    - type: org.osbuild.stage
      options: ${this.data}  # it's not going to be `this`
    - type: org.osbuild.stage
      options: ${this.data}  # it's not going to be `this`
```

## `otk.external`

External directives. Directives starting with `otk.external` are redirected
to `/usr/libexec/otk/`-binaries. For example the directive
`otk.external.osbuild.depsolve-dnf4` will execute `otk-osbuild depsolve-dnf4`
with the tree under the directive on stdin and expect a new tree to replace
the directive with on stdout.

When `otk` processes omnifests initially it performs a "common" translation
which processes all non-external directives. After this it processes each
target in the omnifest with a context specific to the target. In this phase
the `otk.external` directives are resolved.

Read more about [external directives](./external) in their specific
documentation section.
