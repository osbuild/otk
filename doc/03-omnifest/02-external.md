# External

## osbuild

These directives are only allowed within a [`otk.target.osbuild.<name>`](./directive#otktargetconsumername).

### `otk.external.osbuild.depsolve-dnf4`

Solves a list of package specifications to RPMs and specifies them in the
osbuild manifest as sources.

### `otk.external.osbuild.depsolve-dnf5`

Expects a `map` as its value.

`osbuild` directives to write files. **If a stage exists for the type of file
you want to write: use it.** See the [best practices](../best-practices).

### `otk.external.osbuild.file-from-text`

Write inline text to a file. Creates a source in the manifest and copies that
source to the destination in the tree.

Path components up to the destination must be pre-existing in the tree.

```yaml
otk.external.osbuild.file-from-text:
  destination: /path/to
  text: |
    Hello, World!
```

### `otk.external.osbuild.file-from-path`

Copy a file. Source is relative to the path of the entrypoint omnifest. Creates
a source in the manifest and copies that source to the destination in tree.

Path components up to the destination must be pre-existing in the tree.

```yaml
otk.external.osbuild.file-from-path:
  source: README.md
  destination: /path/to
```
