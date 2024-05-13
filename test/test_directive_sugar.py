import pytest

from otk.context import CommonContext
from otk.document import Omnifest
from otk.error import TransformDirectiveTypeError
from otk.directive import desugar


def test_simple_sugar():
    context = CommonContext()
    context.define("my_var", "foo")

    assert desugar(context, "${my_var}") == "foo"


def test_simple_sugar_tree():
    context = CommonContext()
    context.define("my_var", [1, 2])

    assert desugar(context, "${my_var}") == [1, 2]


def test_simple_sugar_tree_fail():
    context = CommonContext()
    context.define("my_var", [1, 2])

    expected_error = "string sugar resolves to an incorrect type, expected int, float, or str but got %r"

    with pytest.raises(TransformDirectiveTypeError, match=expected_error):
        desugar(context, "a${my_var}")


def test_sugar_multiple():
    context = CommonContext()
    context.define("a", "foo")
    context.define("b", "bar")

    assert desugar(context, "${a}-${b}") == "foo-bar"


def test_sugar_multiple_fail():
    context = CommonContext()
    context.define("a", "foo")
    context.define("b", [1, 2])

    expected_error = "string sugar resolves to an incorrect type, expected int, float, or str but got %r"

    # Fails due to non-str type
    with pytest.raises(TransformDirectiveTypeError, match=expected_error):
        desugar(context, "${a}-${b}")
