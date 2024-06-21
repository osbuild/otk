import pytest

from otk.context import CommonContext
from otk.error import TransformDirectiveArgumentError, TransformDirectiveTypeError
from otk.directive import include, op_join


def test_include_unhappy():
    ctx = CommonContext()

    with pytest.raises(TransformDirectiveTypeError):
        include(ctx, 1)


def test_include_file_missing_errors(tmp_path):
    ctx = CommonContext()

    with pytest.raises(FileNotFoundError):
        include(ctx, "non-existing.yml")


def test_op_seq_join():
    ctx = CommonContext()

    l1 = [1, 2, 3]
    l2 = [4, 5, 6]

    d = {"values": [l1, l2]}

    assert op_join(ctx, d) == [1, 2, 3, 4, 5, 6]


def test_op_join_unhappy():
    ctx = CommonContext()

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, 1)

    with pytest.raises(TransformDirectiveArgumentError):
        op_join(ctx, {})

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, {"values": 1})

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, {"values": [1, {2: 3}]})

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, 1)

    with pytest.raises(TransformDirectiveArgumentError):
        op_join(ctx, {})

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, {"values": 1})

    with pytest.raises(TransformDirectiveTypeError):
        op_join(ctx, {"values": [1, {2: 3}]})


def test_op_map_join():
    ctx = CommonContext()

    d1 = {"foo": "bar"}
    d2 = {"bar": "foo"}

    d = {"values": [d1, d2]}

    assert op_join(ctx, d) == {"foo": "bar", "bar": "foo"}
