# Integration

`otk` will integrate with various build systems.

## osbuild-composer

The [osbuild-composer](../osbuild-composer) integration allows for [omnifests](./omnifest) to be consumed by [images](../images). This provides an API and jobqueue to facilitate building artifacts in [Image Builder](../image-builder), [Image Builder Frontend](../image-builder-frontend), and [Cockpit Composer](../cockpit-composer).

There will be requirements on an omnifest to be consumed by [images](../images). Most likely an [otk.meta.\<name\>](./omnifest/directive#otkmetaname) directive will be required. This directive will contain information necessary for the integration.

## koji

The plan is to extend the koji-osbuild-plugin with additional tasks that make use of `otk`. We want to provide a workflow similar to kickstarts and livemediacreator.
