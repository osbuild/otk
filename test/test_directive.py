import pytest

from otk.annotation import AnnotatedDict, AnnotatedBase
from otk.context import CommonContext
from otk.error import (TransformDirectiveArgumentError,
                       TransformDirectiveTypeError)
from otk.transform import op_join
from otk.traversal import State


def test_op_seq_join():
    ctx = CommonContext()
    state = State("")

    l1 = [1, 2, 3]
    l2 = [4, 5, 6]

    d = AnnotatedBase.deep_convert({"values": [l1, l2]})

    assert op_join(ctx, state, d) == [1, 2, 3, 4, 5, 6]


def test_op_join_unhappy():
    ctx = CommonContext()
    state = State("foo.yaml")

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, state, AnnotatedBase.deep_convert(1))

    with pytest.raises(TransformDirectiveArgumentError):
        op_join(ctx, state, AnnotatedBase.deep_convert({}))

    with pytest.raises(TransformDirectiveTypeError) as exc:
        op_join(ctx, state, AnnotatedBase.deep_convert({"values": 1}))
    assert "foo.yaml: seq join received values of the wrong type, " in str(exc.value)

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, state, AnnotatedBase.deep_convert({"values": [1, {2: 3}]}))

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, state, AnnotatedBase.deep_convert(1))

    with pytest.raises(TransformDirectiveArgumentError):
        op_join(ctx, state, AnnotatedBase.deep_convert({}))

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, state, AnnotatedBase.deep_convert({"values": 1}))

    with pytest.raises(TransformDirectiveTypeError) as exc:
        op_join(ctx, state, AnnotatedBase.deep_convert({"values": [1, {2: 3}]}))
    assert "foo.yaml: cannot join " in str(exc.value)


def test_op_map_join():
    ctx = CommonContext()
    state = State("")

    d1 = {"foo": "bar"}
    d2 = {"bar": "foo"}

    d = AnnotatedBase.deep_convert({"values": [d1, d2]})

    assert op_join(ctx, state, d) == AnnotatedDict({"foo": "bar", "bar": "foo"})
