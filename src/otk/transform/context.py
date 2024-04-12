# Enables postponed annotations on older snakes (PEP-563)
# Enables | union syntax for types on older snakes (PEP-604)
from __future__ import annotations

import logging
import pathlib

from typing import Any

from ..error import (
    TransformVariableLookupError,
    TransformVariableTypeError,
    TransformDefineDuplicateError,
    TransformVariableIndexTypeError,
    TransformVariableIndexRangeError,
)


log = logging.getLogger(__name__)


class Context:
    _version: int | None
    _path: pathlib.Path
    _variables: dict[str, Any]

    def __init__(self, path: pathlib.Path | None = None) -> None:
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
        # Since we go through the tree multiple times it's easy to ignore
        # duplicate definitions as long as they define to the *same* value.
        if name in self._variables and self._variables[name] != value:
            raise TransformDefineDuplicateError()

        self._variables[name] = value

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
                raise TransformVariableTypeError(
                    "tried to look up %r.%r but %r isn't a dictionary"
                )

        return value
