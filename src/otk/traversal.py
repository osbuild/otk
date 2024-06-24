class State:
    def __init__(self, path, define_subtree_ref, includes=None):
        self.path = path
        self.define_subtree_ref = define_subtree_ref
        if includes is None:
            includes = []
        self.includes = includes

    def copy(self, *, path=None, define_subtree_ref=None, includes=None) -> "State":
        """
        Return a new State, optionally redefining the path and defines
        properties. Properties not defined in the args are (shallow) copied
        from the existing instance.
        A reference the 'define_subtree_ref' allows us to keep modifying the global
        context variables through the reference on this State object, which can
        refer to the current (sub)tree of the defines in the global context.
        """
        if path is None:
            path = self.path
        if define_subtree_ref is None:
            define_subtree_ref = self.define_subtree_ref
        if includes is None:
            includes = self.includes.copy()

        return State(path, define_subtree_ref, includes)
