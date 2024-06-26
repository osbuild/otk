import pytest

from otk.context import CommonContext
from otk.error import (
    ParseError,
    TransformVariableIndexRangeError,
    TransformVariableIndexTypeError,
    TransformVariableLookupError,
    TransformVariableTypeError,
)


def test_context():
    ctx = CommonContext()
    ctx.define("foo", "foo")

    assert ctx.variable("foo") == "foo"

    ctx.define("bar", {"bar": "foo"})

    assert ctx.variable("bar.bar") == "foo"

    ctx.define("baz", {"baz": {"baz": "foo", "0": 1, 1: "foo"}})

    assert ctx.variable("baz.baz.baz") == "foo"
    assert ctx.variable("baz.baz.0") == 1

    # TODO numeric key lookups!
    # assert ctx.variable("baz.baz.1") == "foo"

    ctx.define("boo", [1, 2])

    assert ctx.variable("boo") == [1, 2]
    assert ctx.variable("boo.0") == 1
    assert ctx.variable("boo.1") == 2


def test_context_define_subkey():
    ctx = CommonContext()
    ctx.define("key", "val")
    assert ctx.variable("key") == "val"

    ctx.define("key.subkey", "subval")
    assert ctx.variable("key") == {"subkey": "subval"}
    ctx.define("key.subkey2", "subval2")
    assert ctx.variable("key") == {"subkey": "subval", "subkey2": "subval2"}
    ctx.define("key", "other-val")
    assert ctx.variable("key") == "other-val"

    ctx.define("other.key.with.subkey", "subval")
    assert ctx.variable("other") == {"key": {"with": {"subkey": "subval"}}}


def test_context_nonexistent():
    ctx = CommonContext()

    with pytest.raises(TransformVariableLookupError):
        ctx.variable("foo")

    with pytest.raises(TransformVariableLookupError):
        ctx.variable("foo.bar")

    ctx.define("bar", {"bar": "foo"})

    with pytest.raises(TransformVariableLookupError):
        ctx.variable("bar.nonexistent")


def test_context_unhappy():
    ctx = CommonContext()
    ctx.define("foo", "foo")

    with pytest.raises(TransformVariableTypeError):
        ctx.variable("foo.bar")

    ctx.define("bar", ["bar"])

    with pytest.raises(TransformVariableIndexTypeError):
        ctx.variable("bar.bar")

    with pytest.raises(TransformVariableIndexRangeError):
        ctx.variable("bar.3")


@pytest.mark.parametrize(
    "var_name",
    ["0", "00", "?", "a?b", "a.", "a..", "a|", "a.b?.c"])
def test_context_define_validates_bad(var_name):
    ctx = CommonContext()

    with pytest.raises(ParseError) as exc:
        ctx.define(var_name, "val")
    assert "invalid variable part " in str(exc.value)


def test_context_define_validates_err_msg():
    ctx = CommonContext()

    with pytest.raises(ParseError) as exc:
        ctx.define("a.b?.c", "val")
    assert "invalid variable part 'b?' in 'a.b?.c', allowed [a-zA-Z][a-zA-Z0-9_]*" in str(exc.value)


@pytest.mark.parametrize(
    "var_name",
    ["a", "a0", "A", "Aa", "a00", "aA0", "zZ9", "a_", "a__"])
def test_context_define_validates_good(var_name):
    ctx = CommonContext()
    ctx.define(var_name, "val")
