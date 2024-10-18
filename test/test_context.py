import logging

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


def test_context_define_subkey(caplog):
    caplog.set_level(logging.WARNING)
    ctx = CommonContext()
    ctx.define("key", "val")
    assert ctx.variable("key") == "val"

    ctx.define("key.subkey", "subval")
    assert ctx.variable("key") == {"subkey": "subval"}
    assert len(caplog.records) == 0
    ctx.define("key.subkey2", "subval2")
    assert ctx.variable("key") == {"subkey": "subval", "subkey2": "subval2"}
    ctx.define("key", "other-val")
    assert ctx.variable("key") == "other-val"

    ctx.define("other.key.with.subkey", "subval")
    assert ctx.variable("other") == {"key": {"with": {"subkey": "subval"}}}


def test_context_warn_on_override_simple(caplog):
    caplog.set_level(logging.WARNING)
    ctx = CommonContext(warn_duplicated_defs=True)
    ctx.define("key", "val")
    assert len(caplog.records) == 0
    ctx.define("key", "new-val")
    expected_msg = "redefinition of 'key', previous value was 'val' and new value is 'new-val'"
    assert [expected_msg] == [r.message for r in caplog.records]


def test_context_warn_on_override_nested(caplog):
    caplog.set_level(logging.WARNING)
    ctx = CommonContext(warn_duplicated_defs=True)
    ctx.define("key.subkey.subsubkey", "subsubval")
    assert len(caplog.records) == 0
    ctx.define("key.subkey", "newsubval")
    # from dict -> str
    expected_msg1 = ("redefinition of 'key.subkey', previous value was "
                     "{'subsubkey': 'subsubval'} and new value is 'newsubval'")
    assert [expected_msg1] == [r.message for r in caplog.records]
    ctx.define("key.subkey", {"sub": "dict"})
    # from str -> dict
    expected_msg2 = ("redefinition of 'key.subkey', previous value was "
                     "'newsubval' and new value is {'sub': 'dict'}")
    assert [expected_msg1, expected_msg2] == [r.message for r in caplog.records]


def test_context_warn_on_override_nested_from_val_to_dict(caplog):
    caplog.set_level(logging.WARNING)
    ctx = CommonContext(warn_duplicated_defs=True)
    ctx.define("key.sub", "subval")
    assert len(caplog.records) == 0
    ctx.define("key.sub.subsub.subsubsub", {"subsubsub": "val2"})
    expected_msg = ("redefinition of 'key.sub', previous value was "
                    "'subval' and new value is {'subsub.subsubsub': {'subsubsub': 'val2'}}")

    assert [expected_msg] == [r.message for r in caplog.records]


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

    with pytest.raises(TransformVariableLookupError) as exc:
        ctx.variable("foo")
    assert "could not resolve 'foo' as 'foo' is not defined" in str(exc.value)

    ctx.define("foo", "foo")

    with pytest.raises(TransformVariableTypeError) as exc:
        ctx.variable("foo.bar")
    assert ("tried to look up 'foo.bar', but the value of prefix 'foo' "
            "is not a dictionary but <class 'otk.annotation.AnnotatedStr'>") in str(exc.value)

    ctx.define("bar", ["bar"])

    with pytest.raises(TransformVariableIndexTypeError) as exc:
        ctx.variable("bar.bar")
    assert "part is not numeric but <class 'str'>" in str(exc.value)

    with pytest.raises(TransformVariableIndexRangeError) as exc:
        ctx.variable("bar.3")
    assert "3 is out of range for ['bar']" in str(exc.value)


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
