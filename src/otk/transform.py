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
from .constant import NAME_VERSION, PREFIX, PREFIX_DEFINE, PREFIX_INCLUDE, PREFIX_OP, PREFIX_TARGET
from .context import Context, validate_var_name
from .error import ParseError, TransformDirectiveTypeError, TransformDirectiveUnknownError
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


# XXX: look into this
# pylint: disable=too-many-branches
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

    for key, val in tree.copy().items():
        # Replace any variables in a value immediately before doing anything
        # else, so that variables defined in strings are considered in the
        # processing of all directives.
        if isinstance(val, str):
            val = substitute_vars(ctx, val)
        if is_directive(key):
            if key.startswith(PREFIX_DEFINE):
                del tree[key]  # remove otk.define from the output tree
                process_defines(ctx, state, val)
                continue

            if key == NAME_VERSION:
                continue

            if key.startswith(PREFIX_TARGET):
                # no target, "dry" run
                if not ctx.target_requested:
                    continue
                # wrong target
                if not key.startswith(PREFIX_TARGET + ctx.target_requested):
                    continue
                target = resolve(ctx, state, val)
                if not isinstance(target, dict):
                    raise ParseError(
                        f"First level below a 'target' should be a dictionary (not a {type(target).__name__})")

                tree.update(target)
                continue

            if key.startswith(PREFIX_INCLUDE):
                del tree[key]  # replace "otk.include" with resolved included data

                included = process_include(ctx, state, pathlib.Path(val))
                if not isinstance(included, dict):
                    return included

                tree.update(included)
                continue

            # Other directives do *not* allow siblings
            if len(tree) > 1:
                keys = list(tree.keys())
                raise KeyError(f"directive {key} should not have siblings: {keys!r}")

            if key.startswith(PREFIX_OP):
                # return is fine, no siblings allowed
                return resolve(ctx, state, op(ctx, resolve(ctx, state, val), key))

            if key.startswith("otk.external."):
                # no target, "dry" run
                if not ctx.target_requested:
                    continue
                # return is fine, no siblings allowed
                return resolve(ctx, state, call(key, resolve(ctx, state, val)))

        tree[key] = resolve(ctx, state, val)
    return tree


def resolve_list(ctx: Context, state: State, tree: list[Any]) -> list[Any]:
    """Resolving a list means applying the resolve function to each element in
    the list."""

    log.debug("resolving list %r", tree)

    return [resolve(ctx, state, val) for val in tree]


def resolve_str(ctx: Context, _: State, tree: str) -> Any:
    """Resolving strings means they are parsed for any variable
    interpolation."""

    log.debug("resolving str %r", tree)

    return substitute_vars(ctx, tree)


def is_directive(needle: Any) -> bool:
    """Is a given needle a directive identifier?"""
    return isinstance(needle, str) and needle.startswith(PREFIX)


def process_defines(ctx: Context, state: State, tree: Any) -> None:
    """
    Processes tree for new defines, resolving any references to other variables,
    and update the global context. The State holds a reference to the nested
    defines block the function is working in. New defines are added to the
    nested block but references are resolved from the global ctx.defines.
    """
    if tree is None:
        log.warning("empty otk.define in %s", state.path)
        return

    # Iterate over a copy of the tree so that we can modify it in-place.
    for key, value in tree.copy().items():
        if key.startswith("otk.define"):
            # nested otk.define: process the nested values directly
            process_defines(ctx, state, value)
            continue

        if key.startswith("otk.include"):
            raise ParseError(f"otk.include not allowed in an otk.define in {state.path}")

        if key.startswith("otk.op"):
            del tree[key]
            value = op(ctx, value, key)
            ctx.define(state.define_subkey(), value)
            continue

        if key.startswith("otk.external."):
            new_vars = resolve(ctx, state, call(key, resolve(ctx, state, value)))
            ctx.merge_defines(state.define_subkey(), new_vars)
            continue

        if isinstance(value, dict):
            new_state = state.copy(subkey_add=key)
            process_defines(ctx, new_state, value)

        elif isinstance(value, str):
            # value is a string: run it through substitute_vars() to resolve any variables and set the define
            ctx.define(state.define_subkey(key), substitute_vars(ctx, value))
        else:
            # for any other type, just set the value to the key
            ctx.define(state.define_subkey(key), value)


def process_include(ctx: Context, state: State, path: pathlib.Path) -> dict:
    """
    Load a yaml file and send it to resolve() for processing.
    """
    # resolve 'path' relative to 'state.path'
    if not path.is_absolute():
        cur_path = state.path.parent
        path = (cur_path / pathlib.Path(path)).resolve()
    try:
        with path.open(encoding="utf8") as fp:
            data = yaml.safe_load(fp)
    except FileNotFoundError as fnfe:
        raise FileNotFoundError(f"file {path} referenced from {state.path} was not found") from fnfe

    if data is not None:
        return resolve(ctx, state.copy(path=path), data)
    return {}


def op(ctx: Context, tree: Any, key: str) -> Any:
    """Dispatch the various `otk.op` directives while handling unknown
    operations."""

    if key == "otk.op.join":
        return op_join(ctx, tree)
    raise TransformDirectiveUnknownError(f"nonexistent op {key!r}")


@tree.must_be(dict)
@tree.must_pass(tree.has_keys(["values"]))
def op_join(_: Context, tree: dict[str, Any]) -> Any:
    """Join a map/seq."""

    values = tree["values"]
    if not isinstance(values, list):
        raise TransformDirectiveTypeError(
            f"seq join received values of the wrong type, was expecting a list of lists but got {values!r}")

    if all(isinstance(sl, list) for sl in values):
        return _op_seq_join(values)
    if all(isinstance(sl, dict) for sl in values):
        return _op_map_join(values)
    raise TransformDirectiveTypeError(f"cannot join {values}")


def _op_seq_join(values: List[list]) -> Any:
    """Join to sequences by concatenating them together."""

    if not all(isinstance(sl, list) for sl in values):
        raise TransformDirectiveTypeError(
            f"seq join received values of the wrong type, was expecting a list of lists but got {values!r}")

    return list(itertools.chain.from_iterable(values))


def _op_map_join(values: List[dict]) -> Any:
    """Join two dictionaries. Keys from the second dictionary overwrite keys
    in the first dictionary."""

    if not all(isinstance(sl, dict) for sl in values):
        raise TransformDirectiveTypeError(
            f"map join received values of the wrong type, was expecting a list of dicts but got {values!r}")

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
    pattern = bracket % r"(?P<name>[^}]+)"
    # If there is a single match and its span is the entire haystack then we
    # return its value directly.
    if m := re.fullmatch(pattern, data):
        validate_var_name(m.group("name"))
        return ctx.variable(m.group("name"))

    if matches := re.finditer(pattern, data):
        for m in matches:
            name = m.group("name")
            validate_var_name(m.group("name"))

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
            data = re.sub(bracket % re.escape(name), value, data)
            log.debug("substituting %r as substring to %r", name, data)

    return data
