"""`otk` is primarily a tree transformation tool. This module contains the
objects used validate tree arguments for functions that deal with trees."""

# Enables postponed annotations on older snakes (PEP-563)
from __future__ import annotations


import functools
from typing import Callable, Type

from .error import TransformDirectiveArgumentError, TransformDirectiveTypeError


def must_be(kind: Type) -> Callable:
    """Handles the tree having to be of a specific type at runtime."""

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            if not isinstance(args[2], kind):
                # XXX: this needs state to give proper errors
                raise TransformDirectiveTypeError(
                    f"otk.define expects a {kind!r} as its argument but "
                    f"received a `{type(args[2])}`: `{args[2]!r}`", args[1])
            return function(*args, **kwargs)

        return wrapper

    return decorator


def must_pass(*vs):
    """Handles the tree having to pass specific validators at runtime."""

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            for v in vs:
                v(args[2])
            return function(*args, **kwargs)

        return wrapper

    return decorator


def has_keys(keys):
    def inner(tree):
        for key in keys:
            if key not in tree.value:
                raise TransformDirectiveArgumentError(f"Expected key {key!r}")

    return inner
