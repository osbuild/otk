import pytest

from otk.context import CommonContext
from otk.error import TransformDirectiveTypeError
from otk.directive import desugar
from otk.parserstate import ParserState


def test_simple_sugar():
    context = CommonContext()
    context.define("my_var", "foo")
    state = ParserState(path="test")

    assert desugar(context, state, "${my_var}") == "foo"


def test_simple_sugar_nested():
    context = CommonContext()
    context.define("my_var", [1, 2])
    state = ParserState(path="test")

    assert desugar(context, state, "${my_var}") == [1, 2]


def test_simple_sugar_nested_fail():
    context = CommonContext()
    context.define("my_var", [1, 2])
    state = ParserState(path="test")

    expected_error = r"string sugar resolves to an incorrect type, expected int, float, or str but got \[1, 2\] in test"

    with pytest.raises(TransformDirectiveTypeError, match=expected_error):
        desugar(context, state, "a${my_var}")


def test_sugar_multiple():
    context = CommonContext()
    context.define("a", "foo")
    context.define("b", "bar")
    state = ParserState(path="test")

    assert desugar(context, state, "${a}-${b}") == "foo-bar"


def test_sugar_multiple_fail():
    context = CommonContext()
    context.define("a", "foo")
    context.define("b", [1, 2])
    state = ParserState(path="test")

    expected_error = r"string sugar resolves to an incorrect type, expected int, float, or str but got \[1, 2\] in test"

    # Fails due to non-str type
    with pytest.raises(TransformDirectiveTypeError, match=expected_error):
        desugar(context, state, "${a}-${b}")
