# Directives

`otk` has various directives that can be used in an omnifest. Generally these
directives can appear anywhere in the tree and they are replaced with other
trees or values.

## otk.define

Defines variables that can be used through the `otk.variable` directive in
other parts of the omnifest.

Variable scope is global, an `otk.define` directive anywhere in the omnifest
tree will result in the defined names being hoisted to the global scope.

Double definitions of variables are forbidden and will cause an error when
detected. It is thus wise to 'namespace' variables by putting them inside an
map.

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

## otk.argument

Define arguments that **MUST** be passed on the command line to `otk` with
`otk compile -A`.

Expects a `seq` for its value.

```yaml
otk.argument:
  - version
  - architecture
```

## otk.variable

Use a previously defined variable.

The short form expects a `str` for its value, the long form expects a `map` for
its value.

```yaml
otk.define:
  variable: "foo"

otk.include:
  otk.variable: variable
```

It is also possible to use a sugared form of `otk.variable`. For any `str` 
value that starts with `$` the value is replaced with the value as defined
in the `otk.define` block.

```yaml
otk.define:
  variable: "foo"

otk.include: $variable
```

If a `$` appears later in a `str` value then its string value as it appears
in `otk.define` is replaced into the string. Note that using the sugared form
in this form requires the value to be a string in the `otk.define`.

```yaml
# this is OK
otk.define:
  variable: aarch64

otk.include: path/$variable.yaml
```

The following example is an error as the value of `variable` is a `seq`, which
is not allowed inside a string format.

```yaml
# this is NOT OK
otk.define:
  variable:
    - 1
    - 2

otk.include: path/$variable.yaml
```

## otk.include

Include a file at this position in the tree, replacing the directive with the
contents of the file.

Note that cyclical includes are forbidden and will cause an error.

The short form expects a `str` for its value, the long form expects a `map` for
its value.

```yaml
otk.include: file.yaml
```

## otk.op

Perform various operations on variables.

### otk.op.seq.join

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
        - $a
        - $b
```

### otk.op.map.join

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
    otk.op.hash.merge:
      values:
        - $a
        - $b
```

## otk.meta

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

## otk.customization

Customizations are conditional blocks that receive separate input through
`otk compile -Cname=data`, a customization is considered to be active when it
is passed data. If a customization is passed multiple times then the `defined`
block is replaced multiple times, once for each data input.

Expects a `map` for its value which contains a `defined` key. The `default` key
is optional. The values of `default` and `defined` can be of any type.

```yaml
otk.customization.name:
  default:
    - type: org.osbuild.stage
      options: none
  defined:
    - type: org.osbuild.stage
      options: $this.data  # it's not going to be `this`
    - type: org.osbuild.stage
      options: $this.data  # it's not going to be `this`
```

## otk.target.<consumer>

Only act on this sub-tree if producing output for the specified consumer.
Anything specific to the pipelines of e.g. osbuild would be put under:
`otk.target.osbuild`. This allows the otk file to generate valid osbuild
json manifest as well as future targets like kiwi.

An output is necessary for `otk` to generate any outputs. The target
is namespaced to a specific application. `otk` tries to keep little
context but it does need to know what it is outputting for. This
allows us to scope `otk.external` things to only be allowed within
specific targets and for those externals to assume certain things will
be in the tree.

```yaml
otk.target.osbuild:
  pipelines:
    - otk.include: pipelines/root.yaml
    - otk.include: pipelines/tree.yaml
```

## otk.external

External directives. Directives starting with `otk.external` are redirected
to `/usr/libexec/otk/external`-binaries. For example
`otk.external.osbuild.depsolve-dnf4` will execute `otk-osbuild depsolve-dnf4`
with the tree under the directive on stdin and expect a new tree to replace
the directive with on stdout.

### otk.external.osbuild.depsolve-dnf4

Expects a `map` as its value.

### otk.external.osbuild.depsolve-dnf5

Expects a `map` as its value.

### otk.external.osbuild.embed-file

Expects a `map` as its value.

---

### otk.external.osbuild.partition
