from otk import transform
from otk.context import CommonContext
from otk.parserstate import ParserState


def test_resolve_list():
    ctx = CommonContext()
    state = ParserState(path="/")
    assert transform.resolve_list(
        ctx, state,
        [
            1,
        ],
    ) == [
        1,
    ]


def test_resolve_dict():
    ctx = CommonContext()
    state = ParserState(path="/")
    assert transform.resolve_dict(ctx, state, {1: 1}) == {1: 1}
    assert transform.resolve_dict(ctx, state, {"1": 1}) == {"1": 1}
