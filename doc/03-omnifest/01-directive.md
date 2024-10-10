# Directive

In [omnifests](./index.md) directives are sections of the document that get transformed by `otk` into something else.

`otk` has various directives that can be used in an omnifest. Generally these directives can appear anywhere in the tree unless otherwise specified (see below) and they are replaced with other trees or values as produced by the directive.

There are [example omnifests](https://github.com/osbuild/otk/tree/main/example) for various distributions and images in a [source checkout](../00-installation.md).

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

Defines variables that can be used through the `${}` directive in
other parts of the omnifest.

Variable scope is global, an `otk.define` directive anywhere in the omnifest
tree will result in the defined names being hoisted to the global scope.

Redefinitions of variables are allowed. This allows for setting up default
values. If `-W duplicate-definition` is passed as an argument to `otk` then
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

Valid variable names must start with `[a-zA-Z]` and after that initial
char can also contain `[a-zA-Z0-9_]`. E.g. `foo` is valid but `f?` is
not.

## Usage of `${}`

Use a previously defined variable. String values can be used inside other
string values, non-string values *must* stand on their own.

```yaml
otk.define:
  variable: "foo"

otk.include: ${variable}
```

Using the above `packages` map example you can refer to the include and exclude
lists using `${packages.include}` and `${packages.exclude}`.

If a `${}` appears in a `str` value then its string value as it appears
in `otk.define` is replaced into the string. Note that substitutions
in this form require the value to be a string in the `otk.define`.

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

It expects a `str` for its value and as with other strings variable substitution
is performed before using it.

```yaml
otk.include: file.yaml
```

## `otk.op`

Perform various operations on variables.

### `otk.op.join`

Join two or more variables of type `sequence` or `map` together, trying to
join other types or mix types will cause an error. Duplicate keys in
maps are considered an error.

Expects a `map` for its value that contains a `values` key with a value of type
`seq` or `map`.

Example when using with a `sequence` as input:

```yaml
otk.define:
  a:
    - 1
    - 2
  b:
    - 3
    - 4
  c:
    otk.op.join:
      values:
        - ${a}
        - ${b}

-> Result c: [1, 2, 3, 4]
```

Example when using with a `map` as input:

```yaml
otk.define:
  a:
    a: 1
  b:
    b: 2
  c:
    otk.op.join:
      values:
        - ${a}
        - ${b}

-> Result
  c:
   a: 1
   b: 2
```

## `otk.external`

External directives. Directives starting with `otk.external` are redirected
to `/usr/libexec/otk/external`-binaries. For example the directive
`otk.external.osbuild-depsolve-dnf4` will execute `osbuild-depsolve-dnf4`
with the tree under the directive on stdin and expect a new tree to replace
the directive with on stdout.

Read more about [external directives](./02-external.md) in their specific
documentation section.
