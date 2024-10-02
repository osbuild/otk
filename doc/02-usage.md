# Usage

After [installing](./00-installation.md) `otk` you'll probably want to start using it. If you've followed the [installation instructions](./00-installation.md) for a source checkout you'll have an examples directory available. You can compile one of the examples like so:

```
€ OTK_EXTERNAL_PATH="./external" otk compile example/centos/centos-9-x86_64-minimal-raw.yaml
# ...
```

Note that this example will take some time to generate, this is due to dependency solving. After the command is done it will output the generated content on `STDOUT`.
