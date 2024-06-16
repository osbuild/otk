"""To transform trees `otk` recursively modifies them. Trees are visited depth
first from left-to-right (top-to-bottom in omnifests).

Each type we can encounter in the tree has its own resolver. For many types
this would be the `dont_resolve`-resolver which leaves the value as is. For
collection types we want to recursively resolve the elements of the collection.

In the dictionary case we apply our directives. Directives are based on the
keys in the dictionaries."""

import copy
import logging
from typing import Any, Type

from . import tree
from .constant import (
    NAME_VERSION,
    PREFIX_DEFINE,
    PREFIX_OP,
    PREFIX_INCLUDE,
    PREFIX_TARGET,
)
from .context import Context, OSBuildContext
from .directive import desugar, include, is_directive, op
from .external import call
from .parserstate import ParserState

log = logging.getLogger(__name__)


def resolve(ctx: Context, state: ParserState, tree: Any) -> Any:
    """Resolves a (sub)tree of any type into a new tree. Each type has its own
    specific handler to rewrite the tree."""

    typ = type(tree)
    if typ == dict:
        return resolve_dict(ctx, state, tree)
    elif typ == list:
        return resolve_list(ctx, state, tree)
    elif typ == str:
        return resolve_str(ctx, state, tree)
    elif typ in [int, float, bool, type(None)]:
        return tree
    else:
        log.fatal("could not look up %r in resolvers", type(tree))
        raise Exception(type(tree))


def resolve_dict(ctx: Context, state: ParserState, tree: dict[str, Any]) -> Any:
    """...."""

    for key in list(tree.keys()):
        val = tree[key]
        if is_directive(key):
            # Define, target, and version are done separately, they allow
            # sibling elements thus they return the tree with their key set to their
            # (resolved) value.
            if key.startswith(PREFIX_DEFINE):
                define(ctx, state, val)
                print(ctx,state,val)
                del tree[key]
            elif key == NAME_VERSION:
                continue
            elif key.startswith(PREFIX_TARGET):
                continue

            if key.startswith(PREFIX_INCLUDE):
                new_val, new_path = include(ctx, state, val)
                # XXX make this nice
                new_state = copy.copy(state)
                new_state.path = new_path
                return resolve(ctx, new_state, new_val)
            elif key.startswith(PREFIX_OP):
                return resolve(ctx, op(ctx, state, resolve(ctx, state, val), key))
            elif key.startswith("otk.external."):
                if isinstance(ctx, OSBuildContext):
                    return resolve(ctx, state, call(key, resolve(ctx, val)))
                else:
                    log.error("%r:%r", key, ctx)

        tree[key] = resolve(ctx, state, val)

    return tree


def resolve_list(ctx: Context, state: ParserState, tree: list[Any]) -> list[Any]:
    """Resolving a list means applying the resolve function to each element in
    the list."""

    log.debug("resolving list %r", tree)

    return [resolve(ctx, state, val) for val in tree]


def resolve_str(ctx: Context, state: ParserState, tree: str) -> Any:
    """Resolving strings means they are parsed for any variable
    interpolation."""

    log.debug("resolving str %r", tree)

    return desugar(ctx, state, tree)


@tree.must_be(dict)
def define(ctx: Context, state: ParserState, tree: Any) -> Any:
    """Takes an `otk.define` block (which must be a dictionary and registers
    everything in it as variables in the context."""

    for key, value in tree.items():
        ctx.define(key, resolve(ctx, state, value))

    return tree
