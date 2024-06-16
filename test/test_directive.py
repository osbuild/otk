import os
import pathlib

import pytest

from otk.context import CommonContext
from otk.error import IncludeError, TransformDirectiveArgumentError, TransformDirectiveTypeError
from otk.directive import desugar, include, op_join
from otk.parserstate import ParserState


def test_include_unhappy():
    ctx = CommonContext()
    state = ParserState(path=pathlib.Path("."))

    with pytest.raises(TransformDirectiveTypeError):
        include(ctx, state, 1)


def test_include_file_missing_errors(tmp_path):
    ctx = CommonContext()
    state = ParserState(path=pathlib.Path("."))

    with pytest.raises(FileNotFoundError) as exc:
        include(ctx, state, "non-existing.yml")


def test_include_file_invalid_errors(tmp_path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("!bad::")

    ctx = CommonContext()
    state = ParserState(path=bad_yaml)
    with pytest.raises(IncludeError) as exc:
        include(ctx, state, os.fspath(bad_yaml))
    assert f"cannot include {tmp_path}/bad.yaml" == str(exc.value)


def test_op_seq_join():
    ctx = CommonContext()
    state = ParserState(path="test")

    l1 = [1, 2, 3]
    l2 = [4, 5, 6]

    d = {"values": [l1, l2]}

    assert op_join(ctx, state, d) == [1, 2, 3, 4, 5, 6]


def test_op_join_unhappy():
    ctx = CommonContext()
    state = ParserState(path="test")

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
    state = ParserState(path="test")

    d1 = {"foo": "bar"}
    d2 = {"bar": "foo"}

    d = {"values": [d1, d2]}

    assert op_join(ctx, state, d) == {"foo": "bar", "bar": "foo"}


def test_desugar():
    ctx = CommonContext()
    ctx.define("str", "bar")
    ctx.define("int", 1)
    ctx.define("float", 1.1)
    state = ParserState(path="test")

    assert desugar(ctx, state, "") == ""
    assert desugar(ctx, state, "${str}") == "bar"
    assert desugar(ctx, state, "a${str}b") == "abarb"
    assert desugar(ctx, state, "${int}") == 1
    assert desugar(ctx, state, "a${int}b") == "a1b"
    assert desugar(ctx, state, "${float}") == 1.1
    assert desugar(ctx, state, "a${float}b") == "a1.1b"


def test_desugar_unhappy():
    ctx = CommonContext()
    ctx.define("dict", {})
    state = ParserState(path="test")

    with pytest.raises(TransformDirectiveTypeError):
        desugar(ctx, state, 1)

    with pytest.raises(TransformDirectiveTypeError):
        desugar(ctx, state, "a${dict}b")
