import pytest

from otk.parse.document import Omnifest
from otk.error import ParseTypeError, ParseVersionError, ParseTargetError


def test_omnifest_read_dict():
    assert Omnifest.read({}) == {}


def test_omnifest_read_list():
    with pytest.raises(ParseTypeError):
        Omnifest.read([])


def test_omnifest_read_string():
    with pytest.raises(ParseTypeError):
        Omnifest.read("")


def test_omnifest_ensure():
    Omnifest.ensure({"otk.version": 1, "otk.target.osbuild": {}})


def test_omnifest_ensure_no_keys():
    with pytest.raises(ParseVersionError):
        assert Omnifest.ensure({})


def test_omnifest_from_yaml_bytes():
    # Happy
    Omnifest.from_yaml_bytes("""
otk.version: 1
otk.target.osbuild: {}
""")

    # A bunch of YAMLs that don't contain a top level map
    with pytest.raises(ParseTypeError):
        Omnifest.from_yaml_bytes("""
""")

    with pytest.raises(ParseTypeError):
        Omnifest.from_yaml_bytes("""
1
""")

    with pytest.raises(ParseTypeError):
        Omnifest.from_yaml_bytes("""
- 1
- 2
""")

    with pytest.raises(ParseTypeError):
        Omnifest.from_yaml_bytes("""
"1"
""")

    # And a YAML that does have a top level map, but no `otk.version` key
    with pytest.raises(ParseVersionError):
        Omnifest.from_yaml_bytes("""
otk.not-version: 1
""")

    # And a YAML that does have a top level map and `otk.version` but no
    # targets
    with pytest.raises(ParseTargetError):
        Omnifest.from_yaml_bytes("""
otk.version: 1
""")


def test_omnifest_from_yaml_path():
    # TODO
    ...
