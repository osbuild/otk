import pytest

from otk.external import convert


@pytest.mark.parametrize("text,exe,args", [
    ("otk.external.osbuild.foo", "otk_external_osbuild", ["foo",]),
    ("otk.external.osbuild.foo.bar", "otk_external_osbuild", ["foo", "bar",]),
    ("otk.external.foo.bar", "otk_external_foo", ["bar",]),
    ("otk.external.foo", "otk_external_foo", []),
])
def test_convert(text, exe, args):
    assert convert(text) == (exe, args)
