import re

import pytest
from otk.context import CommonContext
from otk.transform import substitute_vars
from otk.error import ParseError, TransformDirectiveTypeError, TransformVariableLookupError, TransformVariableTypeError


def test_simple_sub_var():
    context = CommonContext()
    context.define("my_var", "foo")

    assert substitute_vars(context, "${my_var}") == "foo"


def test_simple_sub_var_nested():
    context = CommonContext()
    context.define("my_var", [1, 2])

    assert substitute_vars(context, "${my_var}") == [1, 2]


def test_simple_sub_var_nested_fail():
    context = CommonContext()
    context.define("my_var", [1, 2])
    data = "a${my_var}"

    expected_error = re.escape(
        f"string '{data}' resolves to an incorrect type, " "expected int, float, or str but got list"
    )

    with pytest.raises(TransformDirectiveTypeError, match=expected_error):
        substitute_vars(context, data)


def test_sub_var_multiple():
    context = CommonContext()
    context.define("a", "foo")
    context.define("b", "bar")

    assert substitute_vars(context, "${a}-${b}") == "foo-bar"


def test_sub_var_missing_var_in_context():
    context = CommonContext()
    # toplevel
    expected_err = r"could not resolve 'a' as 'a' is not defined"
    with pytest.raises(TransformVariableLookupError, match=expected_err):
        substitute_vars(context, "${a}")
    # different subtree
    context.define("a", {"there-is-no-b": True})
    expected_err = r"could not resolve 'a.b' as 'b' is not defined"
    with pytest.raises(TransformVariableLookupError, match=expected_err):
        substitute_vars(context, "${a.b}")
    # no subtree
    context.define("a", "foo")
    expected_err = r"tried to look up 'a.b', but prefix 'a' value 'foo' is not a dictionary"
    with pytest.raises(TransformVariableTypeError, match=expected_err):
        substitute_vars(context, "${a.b}")


def test_sub_var_incorrect_var():
    context = CommonContext()
    expected_err = r"invalid variable part 'a-' in 'a-', allowed .*"
    with pytest.raises(ParseError, match=expected_err):
        substitute_vars(context, "${a-}")
    # nested
    expected_err = r"invalid variable part 'b-' in 'a.b-', allowed .*"
    with pytest.raises(ParseError, match=expected_err):
        substitute_vars(context, "${a.b-}")
    # "recursive"
    expected_err = r"invalid variable part '\$\{b' in 'a.\$\{b', allowed .*"
    with pytest.raises(ParseError, match=expected_err):
        substitute_vars(context, "${a.${b}}")


def test_sub_var_multiple_fail():
    context = CommonContext()
    context.define("a", "foo")
    context.define("b", [1, 2])
    context.define("c", {"one": 1})
    data = "${a}-${b}"

    # the a will be replaced but the b will cause an error
    expected_error = re.escape(
        r"string 'foo-${b}' resolves to an incorrect type, expected int, float, or str but got list"
    )

    # Fails due to non-str type
    with pytest.raises(TransformDirectiveTypeError, match=expected_error):
        substitute_vars(context, data)

    data = "${a}-${c}"

    # the a will be replaced but the c will cause an error
    expected_error = re.escape(
        r"string 'foo-${c}' resolves to an incorrect type, expected int, float, or str but got dict"
    )

    # Fails due to non-str type
    with pytest.raises(TransformDirectiveTypeError, match=expected_error):
        substitute_vars(context, data)


def test_substitute_vars():
    ctx = CommonContext()
    ctx.define("str", "bar")
    ctx.define("int", 1)
    ctx.define("float", 1.1)

    assert substitute_vars(ctx, "") == ""
    assert substitute_vars(ctx, "${str}") == "bar"
    assert substitute_vars(ctx, "a${str}b") == "abarb"
    assert substitute_vars(ctx, "${int}") == 1
    assert substitute_vars(ctx, "a${int}b") == "a1b"
    assert substitute_vars(ctx, "${float}") == 1.1
    assert substitute_vars(ctx, "a${float}b") == "a1.1b"


def test_substitute_vars_unhappy():
    ctx = CommonContext()
    ctx.define("dict", {})

    with pytest.raises(TransformDirectiveTypeError):
        substitute_vars(ctx, 1)

    with pytest.raises(TransformDirectiveTypeError):
        substitute_vars(ctx, "a${dict}b")
