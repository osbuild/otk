class State:
    def __init__(self, path, defines):
        self.path = path
        self.defines = defines

    def copy(self, *, path=None, defines=None) -> "State":
        """
        Return a new State, optionally redefining the path and defines
        properties. Properties not defined in the args are (shallow) copied
        from the existing instance.
        A shallow copy of the 'defines' allows us to keep modifying the global
        context variables through the reference on this State object, which can
        refer to a sub-object of the global context when necessary.
        """
        if path is None:
            path = self.path
        if defines is None:
            defines = self.defines

        return State(path, defines)
