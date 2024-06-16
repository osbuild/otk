import pytest

from otk.context import CommonContext
from otk.error import TransformDirectiveTypeError
from otk.transform import define
from otk.parserstate import ParserState

def test_define():
    ctx = CommonContext()
    state = ParserState(path="test")

    define(ctx, state, {"a": "b", "c": 1})

    assert ctx.variable("a") == "b"
    assert ctx.variable("c") == 1


def test_define_duplicate():
    ctx = CommonContext()
    state = ParserState(path="test")

    define(ctx, state, {"a": "b", "c": 1})

    assert ctx.variable("a") == "b"
    assert ctx.variable("c") == 1

    define(ctx, state, {"a": "a", "c": 2})

    assert ctx.variable("a") == "a"
    assert ctx.variable("c") == 2


def test_define_unhappy():
    ctx = CommonContext()
    state = ParserState(path="test")

    with pytest.raises(TransformDirectiveTypeError):
        define(ctx, state, 1)

    with pytest.raises(TransformDirectiveTypeError):
        define(ctx, state, "str")
