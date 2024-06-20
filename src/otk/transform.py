"""To transform trees `otk` recursively modifies them. Trees are visited depth
first from left-to-right (top-to-bottom in omnifests).

Each type we can encounter in the tree has its own resolver. For many types
this would be the `dont_resolve`-resolver which leaves the value as is. For
collection types we want to recursively resolve the elements of the collection.

In the dictionary case we apply our directives. Directives are based on the
keys in the dictionaries."""

import logging
from typing import Any

from .constant import (NAME_VERSION, PREFIX_DEFINE, PREFIX_INCLUDE, PREFIX_OP,
                       PREFIX_TARGET)
from .context import Context, OSBuildContext
from .directive import define, include, is_directive, op, substitute_vars
from .external import call

log = logging.getLogger(__name__)


def resolve(ctx: Context, data: Any) -> Any:
    """Resolves a value of any supported type into a new value. Each type has
    its own specific handler to replace the data value."""

    if isinstance(data, dict):
        return resolve_dict(ctx, data)
    if isinstance(data, list):
        return resolve_list(ctx, data)
    if isinstance(data, str):
        return resolve_str(ctx, data)
    if isinstance(data, (int, float, bool, type(None))):
        return data

    log.fatal("could not look up %r in resolvers", type(data))
    raise TypeError(type(data))


def resolve_dict(ctx: Context, tree: dict[str, Any]) -> Any:
    """...."""

    for key, val in tree.items():
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


def resolve_list(ctx, tree: list[Any]) -> list[Any]:
    """Resolving a list means applying the resolve function to each element in
    the list."""

    log.debug("resolving list %r", tree)

    return [resolve(ctx, val) for val in tree]


def resolve_str(ctx, tree: str) -> Any:
    """Resolving strings means they are parsed for any variable
    interpolation."""

    log.debug("resolving str %r", tree)

    return substitute_vars(ctx, tree)
