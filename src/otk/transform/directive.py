"""Implements the directives, these are named transformations that can be used
in an omnifest."""

# Enables postponed annotations on older snakes (PEP-563)
# Enables | union syntax for types on older snakes (PEP-604)
from __future__ import annotations

import itertools
import logging
import pathlib

from typing import Any

from .context import Context
from ..parse.document import Omnifest
from ..error import (
    TransformDirectiveTypeError,
    TransformDirectiveUnknownError,
)
from .. import tree


log = logging.getLogger(__name__)


# The prefix used for directives
PREFIX = "otk."


@tree.must_be(dict)
def define(ctx: Context, tree: Any) -> Any:
    """Takes an `otk.define` block (which must be a dictionary and registers
    everything in it as variables in the context."""

    for key, value in tree.items():
        ctx.define(key, value)


@tree.must_be(str)
def include(ctx: Context, tree: Any) -> Any:
    """Include a separate file."""

    tree = desugar(ctx, tree)

    file = ctx._path / pathlib.Path(tree)

    # TODO str'ed for json log, lets add a serializer for posixpath
    # TODO instead
    log.info("otk.include=%s", str(file))

    if not file.exists():
        # TODO, better error type
        raise Exception("otk.include nonexistent file %r" % file)

    return Omnifest.from_yaml_path(file, ensure=False).to_tree()


def op(ctx: Context, tree: Any, key: str) -> Any:
    """Dispatch the various `otk.op` directives while handling unknown
    operations."""

    if key == "otk.op.seq.merge":
        return op_seq_merge(ctx, tree)
    elif key == "otk.op.map.merge":
        return op_map_merge(ctx, tree)
    else:
        raise TransformDirectiveUnknownError("nonexistent op %r", key)


@tree.must_be(dict)
@tree.must_pass(tree.has_keys(["values"]))
def op_seq_merge(ctx: Context, tree: dict[str, Any]) -> Any:
    """Merge to sequences by concatenating them together."""

    values = tree["values"]

    if not isinstance(values, list):
        raise TransformDirectiveTypeError(
            "seq merge received values of the wrong type, was expecting a list of lists but got %r",
            values,
        )

    if not all(isinstance(sl, list) for sl in values):
        raise TransformDirectiveTypeError(
            "seq merge received values of the wrong type, was expecting a list of lists but got %r",
            values,
        )

    return list(itertools.chain.from_iterable(values))


@tree.must_be(dict)
@tree.must_pass(tree.has_keys(["values"]))
def op_map_merge(ctx: Context, tree: dict[str, Any]) -> Any:
    """Merge two dictionaries. Keys from the second dictionary overwrite keys
    in the first dictionary."""

    values = tree["values"]

    if not isinstance(values, list):
        raise TransformDirectiveTypeError(
            "map merge received values of the wrong type, was expecting a list of lists but got %r",
            values,
        )

    if not all(isinstance(sl, dict) for sl in values):
        raise TransformDirectiveTypeError(
            "map merge received values of the wrong type, was expecting a list of dicts but got %r",
            values,
        )

    result = {}

    for value in values:
        result.update(value)

    return result


@tree.must_be(dict)
@tree.must_pass(tree.has_keys(["scope", "if-set"]))
def customization(ctx: Context, tree: dict[str, Any], key) -> Any:
    """Apply a customization."""
    log.warning("applying customization %r", key)

    # TODO take in customizations somewhere and use them here, this is
    # TODO currently just a placeholder.
    return tree.get("default")


@tree.must_be(str)
def desugar(ctx: Context, tree: str) -> Any:
    """Desugar a string. If the string consists of a single `${name}` value
    then we return the object it refers to by looking up its name in the
    variables.

    If the string has anything around a variable such as `foo${name}-${bar}`
    then we replace the values inside the string. This requires the type of
    the variable to be replaced to be either str, int, or float."""

    # TODO use parsimonous instead of this

    if tree.startswith("${"):
        name = tree[2 : tree.index("}")]
        data = ctx.variable(tree[2 : tree.index("}")])
        log.debug("desugaring %r as fullstring to %r", name, data)
        return ctx.variable(tree[2 : tree.index("}")])

    if "${" in tree:
        name = tree[tree.index("${") + 2 : tree.index("}")]
        head = tree[: tree.index("${")]
        tail = tree[tree.index("}") + 1 :]

        data = ctx.variable(name)

        if isinstance(data, (int, float)):
            data = str(data)

        if not isinstance(data, str):
            raise TransformDirectiveTypeError(
                "string sugar resolves to an incorrect type, expected int, float, or str but got %r",
                data,
            )

        data = head + data + tail

        log.debug("desugaring %r as substring to %r", name, data)

        return data

    return tree
