from otk.transform import resolve
from otk.transform.context import Context


def test_tree_copy():
    # Ensure that the tree is copied
    t0 = {"a": "b"}
    t1 = resolve(Context(), t0)

    assert id(t0) != id(t1)
