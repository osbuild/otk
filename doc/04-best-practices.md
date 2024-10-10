# Best Practices

As [omnifests](./03-omnifest/index.md) can become quite large here are some best practices to organise. We are trying to provide examples in our [repository](https://github.com/osbuild/otk) that adhere to these.

## Common

Some best practices that apply to [omnifest](./03-omnifest/index.md) files in general.

### Definitions in the entrypoint

Keep variable definitions in the [entrypoint](./03-omnifest/index.md#entrypoint) as much as possible. This gives a single unified place to read which variables affect the build.
