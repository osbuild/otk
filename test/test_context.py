import pytest

from otk.context import Context
from otk.error import (
    TransformVariableLookupError,
    TransformVariableTypeError,
    TransformVariableIndexTypeError,
    TransformVariableIndexRangeError,
    TransformDefineDuplicateError,
)


def test_context():
    ctx = Context()
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


def test_context_nonexistent():
    ctx = Context()

    with pytest.raises(TransformVariableLookupError):
        ctx.variable("foo")

    with pytest.raises(TransformVariableLookupError):
        ctx.variable("foo.bar")

    ctx.define("bar", {"bar": "foo"})

    with pytest.raises(TransformVariableLookupError):
        ctx.variable("bar.nonexistent")


def test_context_unhappy():
    ctx = Context()
    ctx.define("foo", "foo")

    with pytest.raises(TransformVariableTypeError):
        ctx.variable("foo.bar")

    ctx.define("bar", ["bar"])

    with pytest.raises(TransformVariableIndexTypeError):
        ctx.variable("bar.bar")

    with pytest.raises(TransformVariableIndexRangeError):
        ctx.variable("bar.3")


def test_context_duplicate_definition():
    ctx0 = Context()

    # Redefinition allowed
    ctx0.define("foo", "bar")
    ctx0.define("foo", "bar")

    ctx1 = Context(duplicate_definitions_allowed=False)

    # Redefinition NOT allowed
    ctx1.define("foo", "bar")

    with pytest.raises(TransformDefineDuplicateError):
        ctx1.define("foo", "bar")
