# Deprecation Policy

`otk` has little in the way of deprecations. The important part is if or when [directives](./omnifest/directive) get deprecated. This will never happen with a [version](./omnifest/directive#otkversion). If in the future `otk` decides to deprecate an [omnifest](./omnifest) version then we will:

0. Document the intent to deprecate.
1. Emit warning level logs (shown by default) for at least 6 months.
2. Disable the omnifest version by default for at least 6 months, with a flag to re-enable it.
3. Remove the omnifest version.

This gives users a one year migration path.
