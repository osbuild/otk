import pytest
from otk import transform
from otk.context import CommonContext
from otk.traversal import State


@pytest.mark.parametrize(
    "data,defines",
    [
        (
            # simple
            {"a": 1, "b": 2},
            {"a": 1, "b": 2}
        ),
        (
            # intra-block reference
            {"a": "alpha", "b": "${a}"},
            {"a": "alpha", "b": "alpha"},
        ),
        (
            # subblock
            {"a": "alpha", "b": {"c": "${a}"}},
            {"a": "alpha", "b": {"c": "alpha"}},
        ),
        (
            # nested define (ignored)
            {"a": 1, "otk.define.sub": {"b": 2}},
            {"a": 1, "b": 2},
        ),
        (
            # sub-block reference
            {"a": "alpha", "b": {"a": "subalpha", "c": "${b.a}"}},
            {"a": "alpha", "b": {"a": "subalpha", "c": "subalpha"}},
        ),
    ]
)
def test_transform_process_defines(data, defines):
    ctx = CommonContext()
    state = State("", [])

    transform.process_defines(ctx, state, data)
    assert ctx._variables == defines
