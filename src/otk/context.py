"""..."""

# Enables postponed annotations on older snakes (PEP-563)
from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Optional

from .annotation import AnnotatedDict, AnnotatedBase
from .constant import VALID_VAR_NAME_RE
from .error import (ParseError,
                    TransformVariableIndexRangeError,
                    TransformVariableIndexTypeError,
                    TransformVariableLookupError, TransformVariableTypeError)

log = logging.getLogger(__name__)


def validate_var_name(name):
    for part in name.split("."):
        if not re.fullmatch(VALID_VAR_NAME_RE, part):
            raise ParseError(f"invalid variable part '{part}' in '{name}', allowed {VALID_VAR_NAME_RE}", annotated=name)


class Context(ABC):
    @abstractmethod
    def version(self, v: int) -> None: ...

    @abstractmethod
    def define(self, name: str, value: Any) -> None: ...

    @abstractmethod
    def merge_defines(self, name: str, defines: dict[str, Any]) -> None: ...

    @abstractmethod
    def variable(self, name: str) -> Any: ...

    @property
    @abstractmethod
    def target_requested(self) -> str: ...


class CommonContext(Context):
    warn_duplicated_defs: bool
    _target_requested: str
    _version: Optional[int]
    _variables: AnnotatedDict[str, Any]

    def __init__(
        self,
        *,
        target_requested: str = "",
        warn_duplicated_defs: bool = False,
    ) -> None:
        self._version = None
        self._variables = AnnotatedDict()
        self._target_requested = target_requested
        self.warn_duplicated_defs = warn_duplicated_defs

    @property
    def target_requested(self) -> str:
        return self._target_requested

    def version(self, v: int) -> None:
        # Set the context version, duplicate definitions with different
        # versions are an error
        if self._version is not None:
            if self._version != v:
                raise ValueError("duplicate but different version")

        log.debug("context setting version to %r", v)
        self._version = v

    def _maybe_log_var_override(self, cur_var_scope, parts, value):
        if not self.warn_duplicated_defs:
            return
        key = parts[-1]
        if cur_var_scope.get(key):
            log.warning("redefinition of %r, previous value was %r and new value is %r",
                        ".".join(parts), cur_var_scope[parts[-1]], value)

    def define(self, name: str, value: Any) -> None:
        log.debug("defining %r", name)

        if not isinstance(value, AnnotatedBase):
            # mainly for edge cases and tests
            value = AnnotatedBase.deep_convert(value)

        validate_var_name(name)

        cur_var_scope = self._variables
        parts = name.split(".")
        for i, part in enumerate(parts[:-1]):
            if not isinstance(cur_var_scope.get(part), dict):
                self._maybe_log_var_override(cur_var_scope, parts[:i+1], {".".join(parts[i+1:]): value})
                cur_var_scope[part] = AnnotatedDict()
            cur_var_scope = cur_var_scope[part]
        self._maybe_log_var_override(cur_var_scope, parts, value)
        cur_var_scope[parts[-1]] = value

    def variable(self, name: str) -> Any:
        parts = name.split(".")
        value = self._variables
        for i, part in enumerate(parts):
            if isinstance(value, dict):
                if part not in value:
                    raise TransformVariableLookupError(f"could not resolve '{name}' as '{part}' is not defined")

                # TODO how should we deal with integer keys, convert them
                # TODO on KeyError? Check for existence of both?
                value = value[part]
            elif isinstance(value, list):
                if not part.isnumeric():
                    raise TransformVariableIndexTypeError(f"part is not numeric but {type(part)}")

                try:
                    value = value[int(part)]
                except IndexError as exc:
                    raise TransformVariableIndexRangeError(f"{part} is out of range for {value}") from exc
            else:
                prefix = ".".join(parts[:i])
                raise TransformVariableTypeError(
                    f"tried to look up '{prefix}.{part}', but the value of "
                    f"prefix '{prefix}' is not a dictionary but {type(value)}")

        return value

    def merge_defines(self, name: str, defines: Any) -> None:
        if name == "":
            self._variables.update(defines)
        else:
            self.define(name, defines)


class OSBuildContext(Context):
    """Composes in a `GenericContext` while providing support for `osbuild`
    concepts."""

    def __init__(self, context: CommonContext) -> None:
        self._context = context

    def version(self, v: int) -> None:
        return self._context.version(v)

    def define(self, name: str, value: Any) -> None:
        return self._context.define(name, value)

    def variable(self, name: str) -> Any:
        return self._context.variable(name)

    def merge_defines(self, name: str, defines: dict[str, Any]) -> None:
        self._context.merge_defines(name, defines)

    @property
    def target_requested(self) -> str:
        return self._context._target_requested
