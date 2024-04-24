from otk import transform
from otk.context import CommonContext


def test_dont_resolve():
    assert transform.dont_resolve(CommonContext(), 1) == 1
    assert transform.dont_resolve(CommonContext(), 1.0) == 1.0
    assert transform.dont_resolve(CommonContext(), "foo") == "foo"
    assert transform.dont_resolve(CommonContext(), True)
    assert transform.dont_resolve(CommonContext(), None) is None


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
