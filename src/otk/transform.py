"""To transform trees `otk` recursively modifies them. Trees are visited depth
first from left-to-right (top-to-bottom in omnifests).

Each type we can encounter in the tree has its own resolver. For many types
this would be the `dont_resolve`-resolver which leaves the value as is. For
collection types we want to recursively resolve the elements of the collection.

In the dictionary case we apply our directives. Directives are based on the
keys in the dictionaries."""

import logging
from typing import Any, Type

from .constant import (
    NAME_VERSION,
    PREFIX_CUSTOMIZATION,
    PREFIX_DEFINE,
    PREFIX_OP,
    PREFIX_INCLUDE,
    PREFIX_TARGET,
)
from .context import Context, OSBuildContext
from .directive import customization, define, desugar, include, is_directive, op
from .external import call

log = logging.getLogger(__name__)


def resolve_dict(ctx: Context, tree: dict[str, Any]) -> Any:
    """...."""

    for key, val in tree.items():
        # Find directives
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
            elif key.startswith(PREFIX_CUSTOMIZATION):
                return resolve(ctx, customization(ctx, val, key))
            elif key.startswith("otk.external."):
                if isinstance(ctx, OSBuildContext):
                    return resolve(ctx, call(ctx, key, resolve(ctx, val)))
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

    return desugar(ctx, tree)


def dont_resolve(ctx: Context, tree: Any) -> Any:
    """Some types don't need resolving."""

    return tree


registry: dict[Type, Any] = {
    dict: resolve_dict,
    list: resolve_list,
    str: resolve_str,
    int: dont_resolve,
    float: dont_resolve,
    bool: dont_resolve,
    type(None): dont_resolve,
}


def resolve(ctx: Context, tree: Any) -> Any:
    """Resolves a (sub)tree of any type into a new tree. Each type has its own
    specific handler to rewrite the tree."""

    # tree = copy.deepcopy(tree)

    if type(tree) not in registry:
        log.fatal("could not look up %r in resolvers", type(tree))
        raise Exception(type(tree))

    return registry[type(tree)](ctx, tree)
