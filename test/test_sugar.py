import pytest

from otk.parse.document import Omnifest
from otk.transform.context import Context
from otk.transform import resolve
from otk.error import TransformDirectiveTypeError


def test_simple_sugar():
    data = """
otk.version: 1
otk.define:
  variable: "foo"

otk.target.osbuild: {}

my_var: ${variable}
"""

    context = Context()
    omnifest_under_test = Omnifest.from_yaml_bytes(data).to_tree()

    omnifest_result = resolve(context, omnifest_under_test)

    assert omnifest_result["my_var"] == "foo"


def test_simple_sugar_tree():
    data = """
otk.version: 1
otk.define:
  variable:
    - 1
    - 2

otk.target.osbuild: {}

my_var: ${variable}
"""

    context = Context()
    omnifest_under_test = Omnifest.from_yaml_bytes(data).to_tree()

    omnifest_result = resolve(context, omnifest_under_test)

    assert omnifest_result["my_var"] == [1, 2]


def test_simple_sugar_tree_fail():
    data = """
otk.version: 1
otk.define:
  variable:
    - 1
    - 2

otk.target.osbuild: {}

my_var: my_prefix_${variable}
"""
    expected_error = "string sugar resolves to an incorrect type, expected int, float, or str but got %r"

    context = Context()
    omnifest_under_test = Omnifest.from_yaml_bytes(data).to_tree()

    with pytest.raises(TransformDirectiveTypeError, match=expected_error):
        resolve(context, omnifest_under_test)
