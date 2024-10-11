import os
import pathlib

import pytest

from otk.annotation import AnnotatedPath
from otk.error import CircularIncludeError
from otk.traversal import State


def test_state_error_on_write():
    state = State("some-path")
    assert state.path == AnnotatedPath("some-path")
    with pytest.raises(ValueError) as exc:
        state.path = "new-path"
    assert str(exc.value) == "cannot set 'path': State cannot be changed after creation, use State.copy() instead"


def test_state_copy():
    state = State("some-path")
    assert state.path == AnnotatedPath("some-path")
    assert state.define_subkey() == ""
    assert state._includes == [AnnotatedPath("some-path")]
    new_state = state.copy(path="new-path")
    assert state.path == AnnotatedPath("some-path")
    assert state._includes == [AnnotatedPath("some-path")]
    assert new_state.path == AnnotatedPath("new-path")
    assert new_state._includes == [AnnotatedPath("some-path"), AnnotatedPath("new-path")]

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
    # workaround for strange phenomenon, when just running `pytest`
    os.path.curdir = pathlib.Path()
    with pytest.raises(CircularIncludeError) as exc:
        state = State(AnnotatedPath("a.yaml"))
        ns1 = state.copy(path="b.yaml")
        ns2 = ns1.copy(path="c/c.yaml")
        ns2.copy(path=AnnotatedPath("a.yaml"))
    assert str(exc.value) == "circular include detected:\na.yaml ->\nb.yaml ->\nc/c.yaml ->\na.yaml"
    assert ns2._includes == [AnnotatedPath("a.yaml"), AnnotatedPath("b.yaml"), AnnotatedPath("c/c.yaml")]


def test_state_detect_circular_2():
    state = State("a.yaml")
    with pytest.raises(CircularIncludeError) as exc:
        state.copy(path="a.yaml")
    assert str(exc.value) == "circular include detected:\na.yaml ->\na.yaml"


def test_state_empty_includes():
    state = State()
    assert len(state._includes) == 0
