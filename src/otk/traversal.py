import copy
import inspect
import pathlib
from typing import Any, Optional

from .annotation import AnnotatedPath, AnnotatedList
from .error import CircularIncludeError


class State:

    def __init__(self, path: Optional[AnnotatedPath] = None) -> None:
        if path is None:
            path = AnnotatedPath()

        if not isinstance(path, AnnotatedPath):
            # mainly for edge cases and tests
            path = AnnotatedPath(path)

        self.path = path
        self._define_subkeys: list[str] = []
        self._includes = AnnotatedList[Any]()
        if path != pathlib.Path():
            self._includes.append(path)

    def copy(self, *, path: Optional[AnnotatedPath] = None, subkey_add: Optional[str] = None) -> "State":
        """
        Return a new State, optionally redefining the path and add a define
        subkey. Properties not defined in the args are (shallow) copied
        from the existing instance.
        """
        new_state = copy.deepcopy(self)
        if subkey_add:
            new_state._define_subkeys.append(subkey_add)
        if path:
            if not isinstance(path, AnnotatedPath):
                path = AnnotatedPath(path)
            if path in self._includes:
                circle = [p.fspath_with_include() for p in new_state._includes]
                circle.append(path.fspath_with_include())
                circle_str = ' ->\n'.join(circle)
                raise CircularIncludeError(f"circular include detected:\n{circle_str}")
            new_state.path = path
            new_state._includes.append(path)
        return new_state

    def define_subkey(self, key: Optional[str] = None) -> str:
        """
        Return the current dotted path for a define, e.g. "key.subkey"
        """
        if key is None:
            return ".".join(self._define_subkeys)
        return ".".join(self._define_subkeys + [key])

    def __setattr__(self, name: str, val: Any) -> None:
        caller = inspect.stack()[1][3]
        # ideally we would check that the caller is State.copy() here
        if hasattr(self, name) and caller != "copy":
            class_name = self.__class__.__name__
            raise ValueError(
                f"cannot set '{name}': {class_name} cannot be changed after creation, use {class_name}.copy() instead")
        super().__setattr__(name, val)
