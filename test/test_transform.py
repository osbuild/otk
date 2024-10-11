import pytest
from otk import transform
from otk.annotation import AnnotatedDict
from otk.error import ParseTypeError
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
        (
            # special
            {"a": {}},
            {"a": {}},
        ),
    ]
)
def test_transform_process_defines(data, defines):
    ctx = CommonContext()
    state = State("")

    transform.process_defines(ctx, state, AnnotatedDict(data))
    assert ctx._variables.deep_dump() == defines


def test_transform_resolve_unknown_type():
    ctx = CommonContext()
    state = State("foo.yaml")

    with pytest.raises(ParseTypeError) as exc:
        transform.resolve(ctx, state, 1j)
    assert str(exc.value) == "foo.yaml: could not look up <class 'complex'> in resolvers"
