import pytest

from otk.context import CommonContext
from otk.error import TransformDirectiveTypeError
from otk.directive import define


def test_define():
    ctx = CommonContext()

    define(ctx, {"a": "b", "c": 1})

    assert ctx.variable("a") == "b"
    assert ctx.variable("c") == 1


def test_define_duplicate():
    ctx = CommonContext()

    define(ctx, {"a": "b", "c": 1})

    assert ctx.variable("a") == "b"
    assert ctx.variable("c") == 1

    define(ctx, {"a": "a", "c": 2})

    assert ctx.variable("a") == "a"
    assert ctx.variable("c") == 2


def test_define_unhappy():
    ctx = CommonContext()

    with pytest.raises(TransformDirectiveTypeError):
        define(ctx, 1)

    with pytest.raises(TransformDirectiveTypeError):
        define(ctx, "str")
