import copy
import inspect
import os
import pathlib
from typing import Optional

from .error import CircularIncludeError


class State:

    def __init__(self, path: Optional[pathlib.Path] = None) -> None:
        if path is None:
            path = pathlib.Path()
        self.path = path
        self._define_subkeys: list[str] = []
        self._includes = []
        if path != pathlib.Path():
            self._includes.append(path)

    def copy(self, *, path: Optional[pathlib.Path] = None, subkey_add: Optional[str] = None) -> "State":
        """
        Return a new State, optionally redefining the path and add a define
        subkey. Properties not defined in the args are (shallow) copied
        from the existing instance.
        """
        new_state = copy.deepcopy(self)
        if subkey_add:
            new_state._define_subkeys.append(subkey_add)
        if path:
            if path in self._includes:
                circle = [os.fspath(p) for p in new_state._includes]
                circle.append(os.fspath(path))
                raise CircularIncludeError(f"circular include from {'->'.join(circle)}")
            new_state.path = path
            new_state._includes.append(path)
        return new_state

    def define_subkey(self, key: Optional[str] = None):
        """
        Return the current dotted path for a define, e.g. "key.subkey"
        """
        if key is None:
            return ".".join(self._define_subkeys)
        return ".".join(self._define_subkeys + [key])

    def __setattr__(self, name, val):
        caller = inspect.stack()[1][3]
        # ideally we would check that the caller is State.copy() here
        if hasattr(self, name) and caller != "copy":
            class_name = self.__class__.__name__
            raise ValueError(
                f"cannot set '{name}': {class_name} cannot be changed after creation, use {class_name}.copy() instead")
        super().__setattr__(name, val)
