"""..."""

# Enables postponed annotations on older snakes (PEP-563)
from __future__ import annotations

import logging
import pathlib
from abc import ABC, abstractmethod
from typing import Any, Optional

from .error import (TransformVariableIndexRangeError,
                    TransformVariableIndexTypeError,
                    TransformVariableLookupError, TransformVariableTypeError)

log = logging.getLogger(__name__)


class Context(ABC):
    @abstractmethod
    def version(self, v: int) -> None: ...

    @abstractmethod
    def define(self, name: str, value: Any) -> None: ...

    @abstractmethod
    def variable(self, name: str) -> Any: ...

    @property
    @abstractmethod
    def defines(self) -> dict: ...

    @defines.setter
    @abstractmethod
    def defines(self, val): ...


class CommonContext(Context):
    _version: Optional[int]
    _path: pathlib.Path
    _variables: dict[str, Any]

    def __init__(
        self,
        path: Optional[pathlib.Path] = None,
    ) -> None:
        self._version = None
        self._path = path if path else pathlib.Path(".")
        self._variables = {}

    def version(self, v: int) -> None:
        # Set the context version, duplicate definitions with different
        # versions are an error
        if self._version is not None:
            if self._version != v:
                raise ValueError("duplicate but different version")

        log.debug("context setting version to %r", v)
        self._version = v

    def define(self, name: str, value: Any) -> None:
        log.debug("defining %r", name)

        cur_var_scope = self._variables
        parts = name.split(".")
        for part in parts[:-1]:
            if not isinstance(cur_var_scope.get(part), dict):
                cur_var_scope[part] = {}
            cur_var_scope = cur_var_scope[part]
        cur_var_scope[parts[-1]] = value

    def variable(self, name: str) -> Any:
        parts = name.split(".")

        value = self._variables

        for part in parts:
            if isinstance(value, dict):
                if part not in value:
                    raise TransformVariableLookupError("Could not find %r" % parts)

                # TODO how should we deal with integer keys, convert them
                # TODO on KeyError? Check for existence of both?
                value = value[part]
            elif isinstance(value, list):
                if not part.isnumeric():
                    raise TransformVariableIndexTypeError()

                try:
                    value = value[int(part)]
                except IndexError:
                    raise TransformVariableIndexRangeError()
            else:
                raise TransformVariableTypeError("tried to look up %r.%r but %r isn't a dictionary")

        return value

    @property
    def defines(self) -> dict:
        return self._variables

    @defines.setter
    def defines(self, val):
        self._variables = val


class OSBuildContext(Context):
    """Composes in a `GenericContext` while providing support for `osbuild`
    concepts such as sources."""

    sources: dict[str, list[Any]]

    def __init__(self, context: Context) -> None:
        self.sources = {}
        self._context = context

    def version(self, v: int) -> None:
        return self._context.version(v)

    def define(self, name: str, value: Any) -> None:
        return self._context.define(name, value)

    def variable(self, name: str) -> Any:
        return self._context.variable(name)

    @property
    def _path(self):
        return self._context._path

    def for_external(self):
        return {
            "path": str(self._context._path),
            "variables": self._context._variables,
            "sources": self.sources,
        }

    def from_external(self, data: str):
        self._context._variables = data["variables"]
        self.sources = data.get("sources", {})

    @property
    def defines(self) -> dict:
        return self._context._variables

    @defines.setter
    def defines(self, val):
        self._context._variables = val


registry = {
    "osbuild": OSBuildContext,
}
