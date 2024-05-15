# Integration

`otk` will integrate with various build systems.

## osbuild-composer

The osbuild-composer integration allows for [omnifests](./03-omnifest/index.md) to be consumed by images. This provides an API and jobqueue to facilitate building artifacts in Image Builder, Image Builder Frontend, and Cockpit Composer.

There will be requirements on an omnifest to be consumed by images. Most likely an [otk.target.\<name\>](./03-omnifest/01-directive.md) directive will be required. This directive will contain information necessary for the integration.

## koji

The plan is to extend the koji-osbuild-plugin with additional tasks that make use of `otk`. We want to provide a workflow similar to kickstarts and livemediacreator.
