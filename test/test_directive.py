import pytest
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

    d = {"values": [l1, l2]}

    assert op_join(ctx, state, d) == [1, 2, 3, 4, 5, 6]


def test_op_join_unhappy():
    ctx = CommonContext()
    state = State("")

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, state, 1)

    with pytest.raises(TransformDirectiveArgumentError):
        op_join(ctx, state, {})

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, state, {"values": 1})

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, state, {"values": [1, {2: 3}]})

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, state, 1)

    with pytest.raises(TransformDirectiveArgumentError):
        op_join(ctx, state, {})

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, state, {"values": 1})

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, state, {"values": [1, {2: 3}]})


def test_op_map_join():
    ctx = CommonContext()
    state = State("")

    d1 = {"foo": "bar"}
    d2 = {"bar": "foo"}

    d = {"values": [d1, d2]}

    assert op_join(ctx, state, d) == {"foo": "bar", "bar": "foo"}
