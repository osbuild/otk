"""Transforming trees."""

import logging

from typing import Any, Type

from ..context import Context
from .directive import op, define, include, desugar, customization


log = logging.getLogger(__name__)


def resolve_dict(ctx: Context, tree: dict[str, Any]) -> Any:
    log.debug("resolving dict %r", tree)

    for key, val in tree.items():
        if key == "otk.include":
            data = include(ctx, val)

            # We special case dictionaries of length one, when they contain a directive
            # it means we want to replace the entire dictionary with the value of that
            # directive
            if len(tree) == 1:
                log.debug(
                    "single-item otk.include dict %r replacing with %r",
                    tree,
                    data,
                )
                return resolve(ctx, data)
            else:
                # This seems like we're ignoring the rest of the keys, however
                # since resolving happens in multiple cycles those keys will
                # get resolved on the next cycle.
                log.debug(
                    "multi-item otk.include dict %r updating with %r",
                    tree,
                    data,
                )
                return tree | resolve(ctx, data)

        if key.startswith("otk.op"):
            # TODO Do we want to pass key always?
            # TODO Is this the correct order?
            data = op(ctx, resolve(ctx, val), key)

            # We special case dictionaries of length one, when they contain a directive
            # it means we want to replace the entire dictionary with the value of that
            # directive
            if len(tree) == 1:
                log.debug("single-item otk.op dict %r replacing with %r", tree, data)
                return resolve(ctx, data)
            else:
                # This seems like we're ignoring the rest of the keys, however
                # since resolving happens in multiple cycles those keys will
                # get resolved on the next cycle.
                log.debug("multi-item otk.op dict %r updating with %r", tree, data)
                return tree | resolve(ctx, data)

        if key == "otk.define":
            define(ctx, val)

        if key.startswith("otk.customization."):
            return resolve(ctx, customization(ctx, val, key))

        tree[key] = resolve(ctx, val)

    return tree


def resolve_list(ctx, tree: list[Any]) -> list[Any]:
    log.debug("resolving list %r", tree)

    for idx, val in enumerate(tree):
        tree[idx] = resolve(ctx, val)

    return tree


def resolve_str(ctx, tree: str) -> Any:
    log.debug("resolving str %r", tree)
    return desugar(ctx, tree)


def resolve_int(ctx, tree: int) -> int:
    log.debug("resolving int %r", tree)
    return tree


def resolve_float(ctx, tree: float) -> float:
    log.debug("resolving float %r", tree)
    return tree


def resolve_bool(ctx, tree: bool) -> bool:
    log.debug("resolving bool %r", tree)
    return tree


def resolve_none(ctx: Context, tree: None) -> None:
    log.debug("resolving none %r", tree)
    return tree


resolvers: dict[Type, Any] = {
    dict: resolve_dict,
    list: resolve_list,
    str: resolve_str,
    int: resolve_int,
    float: resolve_float,
    bool: resolve_bool,
    type(None): resolve_none,
}


def resolve(ctx: Context, tree: Any) -> Any:
    """Resolves a (sub)tree of any type into a new tree. Each type has its own
    specific handler to rewrite the tree."""

    # TODO we want to do deepcopy's but it needs a rethink of how directives
    # TODO get replaced (especially: `otk.define`).

    # tree = deepcopy(tree)

    if type(tree) not in resolvers:
        log.fatal("could not look up %r in resolvers", type(tree))
        raise Exception(type(tree))

    return resolvers[type(tree)](ctx, tree)
