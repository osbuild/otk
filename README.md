# Omnifest Toolkit

> [!CAUTION]
> This project is currently discontinued. After working on it for a while we've decided to start off with adding declarative formats to our [image definitions](https://github.com/osbuild/images) first; instead of reinventing how to define images.

This is the "Omnifest Toolkit", also known as `otk`. A YAML transpiler to
take omnifest inputs and translate them into [osbuild](https://osbuild.org)
manifests.

## Documentation

You can find `otk`'s documentation in the [/doc](./doc) subdirectory. This README contains a small summary of directly useful information.

## Usage

If you want to quickly run and try out `otk` without installation you can use our container image:

```
podman run -i -v .:/app:z ghcr.io/osbuild/otk compile /app/test/data/base/01-define.yaml
```

or rebuild the container locally

```shell
make container
```

and run an example

```shell
make container-test
```

If you want to hack on `otk` then read the [installation instructions](./doc/00-installation.md).

## Documentation

There is documentation about the [format](./doc/03-omnifest/index.md) and the available
[directives](./doc/03-omnifest/01-directive.md).

## Examples

Read the [examples](./example) to see what omnifests look like.

## Development

### Pre Commit Checks

To check our code for basic problems we use [pre-commit](https://pre-commit.com)
The tool itself will be installed by the `pip` command above (see [Usage](#Usage)) after that you
should run

```shell
pre-commit install
```

After this the system automatically checks upon commit, or you can run it against the whole
repository including all the tests with:

```
make test
```

### Tests

To run the tests, you can run `make test`.

## Principles

- Omnifests are valid YAML, no preprocessing is done on them.
- No introspection of the tree.
- No language-specific quirks in the directives (e.g. `eval`).

## Project

 * **Website**: https://www.osbuild.org
 * **Bug Tracker**: https://github.com/osbuild/otk/issues
 * **Discussions**: https://github.com/orgs/osbuild/discussions
 * **Matrix**: [#image-builder on fedoraproject.org](https://matrix.to/#/#image-builder:fedoraproject.org)
 * **Changelog**: https://github.com/osbuild/otk/releases
