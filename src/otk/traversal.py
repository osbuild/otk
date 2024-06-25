class State:
    def __init__(self, path, define_subkeys, includes=None):
        self.path = path
        self.define_subkeys = define_subkeys
        if includes is None:
            includes = []
        self.includes = includes

    def copy(self, *, path=None, define_subkeys=None, includes=None) -> "State":
        """
        Return a new State, optionally redefining the path and define_subkeys
        properties. Properties not defined in the args are (shallow) copied
        from the existing instance.
        The 'define_subkeys' keeps track how deep in a define the recursion
        is and can be used to modify the global context.
        """
        if path is None:
            path = self.path
        if define_subkeys is None:
            define_subkeys = self.define_subkeys
        if includes is None:
            includes = self.includes.copy()

        return State(path, define_subkeys, includes)
