import re

import pytest

from otk.annotation import AnnotatedStr, AnnotatedList, AnnotatedDict
from otk.context import CommonContext
from otk.transform import substitute_vars
from otk.traversal import State
from otk.error import ParseError, TransformDirectiveTypeError, TransformVariableLookupError, TransformVariableTypeError


def test_simple_sub_var():
    state = State("")
    context = CommonContext()
    context.define("my_var", "foo")

    assert substitute_vars(context, state, "${my_var}") == "foo"


def test_simple_sub_var_nested():
    state = State("")
    context = CommonContext()
    context.define("my_var", [1, 2])

    assert substitute_vars(context, state, "${my_var}") == [1, 2]


def test_simple_sub_var_nested_fail():
    state = State()
    context = CommonContext()

    test_list = AnnotatedList([1, 2])
    test_list.set_annotation("src", "test.yml:1")
    context.define("my_var", test_list)

    data = AnnotatedStr("a${my_var}")
    data.set_annotation("src", "test.yml:2")

    expected_error = re.escape(
        f"test.yml:1 - expected int, float, or str. Can not use AnnotatedList to resolve string '{data}' (test.yml:2)"
    )

    with pytest.raises(TransformDirectiveTypeError, match=expected_error):
        substitute_vars(context, state, data)


def test_sub_var_multiple():
    state = State("")
    context = CommonContext()
    context.define("a", "foo")
    context.define("b", "bar")

    assert substitute_vars(context, state, AnnotatedStr("${a}-${b}")) == "foo-bar"


def test_sub_var_missing_var_in_context():
    state = State("foo.yaml")
    context = CommonContext()
    # toplevel
    expected_err = r"could not resolve 'a' as 'a' is not defined"
    with pytest.raises(TransformVariableLookupError, match=expected_err):
        substitute_vars(context, state, AnnotatedStr("${a}"))
    # different subtree
    context.define("a", {"there-is-no-b": True})
    expected_err = r"could not resolve 'a.b' as 'b' is not defined"
    with pytest.raises(TransformVariableLookupError, match=expected_err):
        substitute_vars(context, state, AnnotatedStr("${a.b}"))
    # no subtree
    context.define("a", "foo")
    expected_err = r"foo.yaml: tried to look up 'a.b', but the value of " \
        "prefix 'a' is not a dictionary but <class 'otk.annotation.AnnotatedStr'>"
    with pytest.raises(TransformVariableTypeError, match=expected_err):
        substitute_vars(context, state, AnnotatedStr("${a.b}"))


def test_sub_var_incorrect_var():
    state = State("")
    context = CommonContext()
    expected_err = r"invalid variable part 'a-' in 'a-', allowed .*"
    with pytest.raises(ParseError, match=expected_err):
        substitute_vars(context, state, AnnotatedStr("${a-}"))
    # nested
    expected_err = r"invalid variable part 'b-' in 'a.b-', allowed .*"
    with pytest.raises(ParseError, match=expected_err):
        substitute_vars(context, state, AnnotatedStr("${a.b-}"))
    # "recursive"
    expected_err = r"invalid variable part '\$\{b' in 'a.\$\{b', allowed .*"
    with pytest.raises(ParseError, match=expected_err):
        substitute_vars(context, state, AnnotatedStr("${a.${b}}"))


def test_sub_var_multiple_fail():
    state = State("")
    context = CommonContext()

    test_str = AnnotatedStr("foo")
    test_str.set_annotation("src", "test.yml:1")

    context.define("a", test_str)

    test_list = AnnotatedList([1, 2])
    test_list.set_annotation("src", "test.yml:3")

    context.define("b", test_list)

    test_dict = AnnotatedDict({"one": 1})
    test_dict.set_annotation("src", "test.yml:4")
    context.define("c", test_dict)

    data = AnnotatedStr("${a}-${b}")
    data.set_annotation("src", "test.yml:5")

    # the a will be replaced but the b will cause an error
    expected_error = re.escape(
        r"test.yml:3 - expected int, float, or str. Can not use AnnotatedList to resolve string 'foo-${b}' "
        r"(variable from test.yml:1 applied to test.yml:5)"
    )

    # Fails due to non-str type
    with pytest.raises(TransformDirectiveTypeError, match=expected_error):
        substitute_vars(context, state, data)

    data = AnnotatedStr("${a}-${c}")
    data.set_annotation("src", "test.yml:5")

    # the a will be replaced but the c will cause an error
    expected_error = re.escape(
        r"test.yml:4 - expected int, float, or str. Can not use AnnotatedDict to resolve string 'foo-${c}' "
        r"(variable from test.yml:1 applied to test.yml:5)"
    )

    # Fails due to non-str type
    with pytest.raises(TransformDirectiveTypeError, match=expected_error):
        substitute_vars(context, state, data)


def test_substitute_vars():
    state = State("")
    ctx = CommonContext()
    ctx.define("str", "bar")
    ctx.define("int", 1)
    ctx.define("float", 1.1)

    assert substitute_vars(ctx, state, AnnotatedStr("")) == ""
    assert substitute_vars(ctx, state, AnnotatedStr("${str}")) == "bar"
    assert substitute_vars(ctx, state, AnnotatedStr("a${str}b")) == "abarb"
    assert substitute_vars(ctx, state, AnnotatedStr("${int}")) == 1
    assert substitute_vars(ctx, state, AnnotatedStr("a${int}b")) == "a1b"
    assert substitute_vars(ctx, state, AnnotatedStr("${float}")) == 1.1
    assert substitute_vars(ctx, state, AnnotatedStr("a${float}b")) == "a1.1b"


def test_substitute_vars_unhappy():
    state = State("foo.yaml")
    ctx = CommonContext()
    ctx.define("dict", {})

    with pytest.raises(TransformDirectiveTypeError) as exc:
        substitute_vars(ctx, state, 1)
    assert "foo.yaml: otk.define expects a <class 'str'> as its argument but received a `<class 'int'>" in str(
        exc.value)

    with pytest.raises(TransformDirectiveTypeError) as exc:
        var_template = AnnotatedStr("a${dict}b")
        var_template.set_annotation("src", "foo.yaml:1")
        substitute_vars(ctx, state, var_template)
    assert ("foo.yaml: expected int, float, or str. Can not use AnnotatedDict "
            "to resolve string 'a${dict}b' (foo.yaml:1)") in str(exc.value)
