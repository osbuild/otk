"""To transform trees `otk` recursively modifies them. Trees are visited depth
first from left-to-right (top-to-bottom in omnifests).

Each type we can encounter in the tree has its own resolver. For many types
this would be the `dont_resolve`-resolver which leaves the value as is. For
collection types we want to recursively resolve the elements of the collection.

In the dictionary case we apply our directives. Directives are based on the
keys in the dictionaries."""

# Enables postponed annotations on older snakes (PEP-563)
from __future__ import annotations

import itertools
import logging
import pathlib
import re
from typing import Any, List

import yaml

from . import tree
from .constant import (NAME_VERSION, PREFIX, PREFIX_DEFINE, PREFIX_INCLUDE,
                       PREFIX_OP, PREFIX_TARGET)
from .context import Context, OSBuildContext
from .error import TransformDirectiveTypeError, TransformDirectiveUnknownError
from .external import call
from .traversal import State

log = logging.getLogger(__name__)


def resolve(ctx: Context, state: State, data: Any) -> Any:
    """Resolves a value of any supported type into a new value. Each type has
    its own specific handler to replace the data value."""

    if isinstance(data, dict):
        return resolve_dict(ctx, state, data)
    if isinstance(data, list):
        return resolve_list(ctx, state, data)
    if isinstance(data, str):
        return resolve_str(ctx, state, data)
    if isinstance(data, (int, float, bool, type(None))):
        return data

    log.fatal("could not look up %r in resolvers", type(data))
    raise TypeError(type(data))


def resolve_dict(ctx: Context, state: State, tree: dict[str, Any]) -> Any:
    """
    Dictionaries are iterated through and both the keys and values are processed.
    Keys define how a value is interpreted:
    - otk.include.* loads the file specified by the value.
    - otk.op.* processes the value with the named operation.
    - otk.define.* updates the defines dictionary with all the defined key-value
      pairs.
    - Values under any other key are processed based on their type (see resolve()).
    """

    for key, val in tree.items():
        # Replace any variables in a value immediately before doing anything
        # else, so that variables defined in strings are considered in the
        # processing of all directives.
        if isinstance(val, str):
            val = substitute_vars(ctx, val)
        if is_directive(key):
            # Define, target, and version are done separately, they allow
            # sibling elements thus they return the tree with their key set to their
            # (resolved) value.
            if key.startswith(PREFIX_DEFINE):
                return tree | {"otk.define": resolve(ctx, define(ctx, val))}
            elif key == NAME_VERSION:
                continue
            elif key.startswith(PREFIX_TARGET):
                continue

            # Other directives do *not* allow siblings
            if len(tree) > 1:
                raise Exception("no siblings!")

            if key.startswith(PREFIX_INCLUDE):
                return resolve(ctx, include(ctx, val))
            elif key.startswith(PREFIX_OP):
                return resolve(ctx, op(ctx, resolve(ctx, val), key))
            elif key.startswith("otk.external."):
                if isinstance(ctx, OSBuildContext):
                    return resolve(ctx, call(key, resolve(ctx, val)))
                else:
                    log.error("%r:%r", key, ctx)

        tree[key] = resolve(ctx, val)

    return tree


def resolve_list(ctx, state: State, tree: list[Any]) -> list[Any]:
    """Resolving a list means applying the resolve function to each element in
    the list."""

    log.debug("resolving list %r", tree)

    return [resolve(ctx, state, val) for val in tree]


def resolve_str(ctx, state: State, tree: str) -> Any:
    """Resolving strings means they are parsed for any variable
    interpolation."""

    log.debug("resolving str %r", tree)

    return substitute_vars(ctx, tree)


def is_directive(needle: Any) -> bool:
    """Is a given needle a directive identifier?"""
    return isinstance(needle, str) and needle.startswith(PREFIX)


def process_defines(ctx: Context, state: State, tree: Any):
    """
    Processes tree for new defines, resolving any references to other variables,
    and update the global context. The State holds a reference to the nested
    defines block the function is working in. New defines are added to the
    nested block but references are resolved from the global ctx.defines.
    """

    subblock = state.defines

    # Iterate over a copy of the tree so that we can modify it in-place.
    for key, value in tree.copy().items():
        if key.startswith("otk.define"):
            # nested otk.define: process the nested values directly
            process_defines(ctx, state, value)
            continue

        if key.startswith("otk.include"):
            # TODO: disallow this (see https://github.com/osbuild/otk/issues/116)
            del tree[key]
            # Pass {"otk.include...": path} to resolve() to have it processed recursively.
            # The contents will become the define block.
            incl = resolve(ctx, state, {key: value})
            subblock.update(incl)

        if isinstance(value, dict):
            # the value is a dict: process it recursively under a new subblock
            new_subblock = subblock.get(key, {})
            # set the new subblock on the parent so that both context and subblock are available immediately
            subblock[key] = new_subblock
            new_state = state.copy(defines=new_subblock)
            process_defines(ctx, new_state, value)

        elif isinstance(value, str):
            # value is a string: run it through substitute_vars() to resolve any variables and set the define
            subblock[key] = substitute_vars(ctx, value)
        else:
            # for any other type, just set the value to the key
            subblock[key] = value


def process_include(ctx: Context, state: State, path: pathlib.Path) -> dict:
    """
    Load a yaml file and send it to resolve() for processing.
    """
    # resolve 'path' relative to 'state.path'
    cur_path = state.path.parent
    path = cur_path / pathlib.Path(path)
    try:
        with open(path, mode="r", encoding="utf=8") as fp:
            data = yaml.safe_load(fp)
    except FileNotFoundError as fnfe:
        raise FileNotFoundError(f"file {path} referenced from {state.path} was not found") from fnfe

    if data is not None:
        new_state = state.copy(path=path)
        return resolve(ctx, new_state, data)
    return {}



@tree.must_be(str)
def include(ctx: Context, tree: Any) -> Any:
    """Include a separate file."""

    tree = substitute_vars(ctx, tree)

    file = ctx._path / pathlib.Path(tree)

    # TODO str'ed for json log, lets add a serializer for posixpath
    # TODO instead
    log.info("otk.include=%s", str(file))

    # TODO
    return yaml.safe_load(file.read_text())


def op(ctx: Context, tree: Any, key: str) -> Any:
    """Dispatch the various `otk.op` directives while handling unknown
    operations."""

    if key == "otk.op.join":
        return op_join(ctx, tree)
    else:
        raise TransformDirectiveUnknownError("nonexistent op %r", key)


@tree.must_be(dict)
@tree.must_pass(tree.has_keys(["values"]))
def op_join(ctx: Context, tree: dict[str, Any]) -> Any:
    """Join a map/seq."""

    values = tree["values"]
    if not isinstance(values, list):
        raise TransformDirectiveTypeError(
            "seq join received values of the wrong type, was expecting a list of lists but got %r",
            values,
        )
    if all(isinstance(sl, list) for sl in values):
        return _op_seq_join(ctx, values)
    elif all(isinstance(sl, dict) for sl in values):
        return _op_map_join(ctx, values)
    else:
        raise TransformDirectiveTypeError(f"cannot join {values}")


def _op_seq_join(ctx: Context, values: List[list]) -> Any:
    """Join to sequences by concatenating them together."""

    if not all(isinstance(sl, list) for sl in values):
        raise TransformDirectiveTypeError(
            "seq join received values of the wrong type, was expecting a list of lists but got %r",
            values,
        )

    return list(itertools.chain.from_iterable(values))


def _op_map_join(ctx: Context, values: List[dict]) -> Any:
    """Join two dictionaries. Keys from the second dictionary overwrite keys
    in the first dictionary."""

    if not all(isinstance(sl, dict) for sl in values):
        raise TransformDirectiveTypeError(
            "map join received values of the wrong type, was expecting a list of dicts but got %r",
            values,
        )

    result = {}

    for value in values:
        result.update(value)

    return result


@tree.must_be(str)
def substitute_vars(ctx: Context, data: str) -> Any:
    """Substitute variables in the `data` string.

    If `data` consists only of a single `${name}` value then we return the
    object that `name` refers to by looking it up in the context variables. The
    value can be of any supported type (str, int, float, dict, list).

    If `data` contains one or more variable references as substrings, such as
    `foo${name}-${bar}` the function will replace the values for each variable
    named (`name` and `bar`, in the example). In this case, the type of the
    value in the names variables must be primitive types, either str, int, or
    float."""

    bracket = r"\$\{%s\}"
    pattern = bracket % r"(?P<name>[a-zA-Z0-9-_\.]+)"

    # If there is a single match and its span is the entire haystack then we
    # return its value directly.
    if match := re.fullmatch(pattern, data):
        return ctx.variable(match.group("name"))

    # Let's find all matches if there are any. We use `list(re.finditer(...))`
    # to get a list of match objects instead of `re.findall` which gives a list
    # of matchgroups.

    # If there are multiple matches then we always interpolate strings.
    if matches := list(re.finditer(pattern, data)):
        for match in matches:
            name = match.group("name")
            value = ctx.variable(name)

            # We know how to turn ints and floats into str's
            if isinstance(value, (int, float)):
                value = str(value)

            # Any other type we do not
            if not isinstance(value, str):
                raise TransformDirectiveTypeError(
                    f"string {data!r} resolves to an incorrect type, "
                    f"expected int, float, or str but got {type(value).__name__}",
                )

            # Replace all occurences of this name in the str

            # NOTE: this means we can recursively replace names, do we want
            # that?
            data = re.sub(bracket % re.escape(name), value, data)

        log.debug("substituting %r as substring to %r", name, data)

        return data

    return data
