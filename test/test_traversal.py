import pytest

from otk.error import CircularIncludeError
from otk.traversal import State


def test_state_error_on_write():
    state = State("some-path")
    assert state.path == "some-path"
    with pytest.raises(ValueError) as exc:
        state.path = "new-path"
    assert str(exc.value) == "cannot set 'path': State cannot be changed after creation, use State.copy() instead"


def test_state_copy():
    state = State("some-path")
    assert state.path == "some-path"
    assert state.define_subkey() == ""
    assert state._includes == ["some-path"]
    new_state = state.copy(path="new-path")
    assert state.path == "some-path"
    assert state._includes == ["some-path"]
    assert new_state.path == "new-path"
    assert new_state._includes == ["some-path", "new-path"]

    ns2 = state.copy(subkey_add="key")
    assert state.define_subkey() == ""
    assert ns2.define_subkey("subkey") == "key.subkey"


def test_state_define_subkey():
    state = State("some-path")
    assert state.define_subkey() == ""
    assert state.define_subkey("key") == "key"

    new_state = state.copy(subkey_add="newkey")
    assert new_state.define_subkey() == "newkey"
    assert new_state.define_subkey("key") == "newkey.key"


def test_state_detect_circular_1():
    state = State("a.yaml")
    ns1 = state.copy(path="b.yaml")
    ns2 = ns1.copy(path="c/c.yaml")
    with pytest.raises(CircularIncludeError) as exc:
        ns2.copy(path="a.yaml")
    assert str(exc.value) == "circular include from ['a.yaml', 'b.yaml', 'c/c.yaml']"
    assert ns2._includes == ["a.yaml", "b.yaml", "c/c.yaml"]


def test_state_detect_circular_2():
    state = State("a.yaml")
    with pytest.raises(CircularIncludeError) as exc:
        state.copy(path="a.yaml")
    assert str(exc.value) == "circular include from ['a.yaml']"


def test_state_empty_includes():
    state = State()
    assert state._includes == []
