from otk import transform
from otk.context import CommonContext


def test_resolve_list():
    assert transform.resolve_list(
        CommonContext(),
        [
            1,
        ],
    ) == [
        1,
    ]


def test_resolve_dict():
    assert transform.resolve_dict(CommonContext(), {1: 1}) == {1: 1}
    assert transform.resolve_dict(CommonContext(), {"1": 1}) == {"1": 1}
