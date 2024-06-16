"""`otk` is primarily a tree transformation tool. This module contains the
objects used validate tree arguments for functions that deal with trees."""

# Enables postponed annotations on older snakes (PEP-563)
from __future__ import annotations


import functools
from typing import Type

from .error import TransformDirectiveArgumentError, TransformDirectiveTypeError


def must_be(kind: Type):
    """Handles the tree having to be of a specific type at runtime."""

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            if not isinstance(args[2], kind):
                raise TransformDirectiveTypeError(
                    "otk.define expects a %r as its argument but received a `%s`: `%r`" % (kind, type(args[2]), args[2])
                )
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
            if key not in tree:
                raise TransformDirectiveArgumentError("Expected key %r", key)

    return inner
