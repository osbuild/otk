class Target:
    pass


class OSBuildTarget(Target):
    pass


registry = {
    "osbuild": OSBuildTarget,
}
