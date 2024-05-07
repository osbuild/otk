# Best Practices

As [omnifests](./03-omnifest/index.md) can become quite large here are some best practices to organise. We are trying to provide examples in our [repository](https://github.com/osbuild/otk) that adhere to these.

Since `otk` can produce outputs for different image build tools our best practices are organised.

## Common

Some best practices that apply to [omnifest](./03-omnifest/index.md) files in general.

### Definitions in the entrypoint

Keep variable definitions in the [entrypoint](./03-omnifest/index.md#entrypoint) as much as possible. This gives a single unified place to read which variables affect the build.

## osbuild

When an [osbuild](../osbuild) target is defined it is a good plan to follow these specific practices.

### Embed a file or use a stage?

`otk` makes it easy to [inline](./03-omnifest/02-external.md#otkexternalosbuildfile-from-text) or [include](./03-omnifest/02-external.md#otkexternalosbuildfile-from-path) files. This makes it appealing to use it for configuration files. It is however generally a better idea to use a domain specific stage to write these sorts of files.

Using a stage to write configuration files comes with the benefit that the inputs can be verified at validation or build time. This allows `osbuild` to try and guarantee that the configuration file will work.
