import pytest

from otk.transform.directive import op_seq_merge, op_map_merge, desugar, define, include
from otk.context import Context
from otk.error import TransformDirectiveTypeError, TransformDirectiveArgumentError


def test_define():
    ctx = Context()

    define(ctx, {"a": "b", "c": 1})

    assert ctx.variable("a") == "b"
    assert ctx.variable("c") == 1


def test_define_unhappy():
    ctx = Context()

    with pytest.raises(TransformDirectiveTypeError):
        define(ctx, 1)

    with pytest.raises(TransformDirectiveTypeError):
        define(ctx, "str")


def test_include_unhappy():
    ctx = Context()

    with pytest.raises(TransformDirectiveTypeError):
        include(ctx, 1)


def test_op_seq_merge():
    ctx = Context()

    l1 = [1, 2, 3]
    l2 = [4, 5, 6]

    d = {"values": [l1, l2]}

    assert op_seq_merge(ctx, d) == [1, 2, 3, 4, 5, 6]


def test_op_seq_merge_unhappy():
    ctx = Context()

    with pytest.raises(TransformDirectiveTypeError):
        op_seq_merge(ctx, 1)

    with pytest.raises(TransformDirectiveArgumentError):
        op_seq_merge(ctx, {})

    with pytest.raises(TransformDirectiveTypeError):
        op_seq_merge(ctx, {"values": 1})

    with pytest.raises(TransformDirectiveTypeError):
        op_seq_merge(ctx, {"values": [1, {2: 3}]})


def test_op_map_merge():
    ctx = Context()

    d1 = {"foo": "bar"}
    d2 = {"bar": "foo"}

    d = {"values": [d1, d2]}

    assert op_map_merge(ctx, d) == {"foo": "bar", "bar": "foo"}


def test_op_map_merge_unhappy():
    ctx = Context()

    with pytest.raises(TransformDirectiveTypeError):
        op_map_merge(ctx, 1)

    with pytest.raises(TransformDirectiveArgumentError):
        op_map_merge(ctx, {})

    with pytest.raises(TransformDirectiveTypeError):
        op_map_merge(ctx, {"values": 1})

    with pytest.raises(TransformDirectiveTypeError):
        op_map_merge(ctx, {"values": [1, {2: 3}]})


def test_desugar():
    ctx = Context()
    ctx.define("str", "bar")
    ctx.define("int", 1)
    ctx.define("float", 1.1)

    assert desugar(ctx, "") == ""
    assert desugar(ctx, "${str}") == "bar"
    assert desugar(ctx, "a${str}b") == "abarb"
    assert desugar(ctx, "${int}") == 1
    assert desugar(ctx, "a${int}b") == "a1b"
    assert desugar(ctx, "${float}") == 1.1
    assert desugar(ctx, "a${float}b") == "a1.1b"


def test_desugar_unhappy():
    ctx = Context()
    ctx.define("dict", {})

    with pytest.raises(TransformDirectiveTypeError):
        desugar(ctx, 1)

    with pytest.raises(TransformDirectiveTypeError):
        desugar(ctx, "a${dict}b")
