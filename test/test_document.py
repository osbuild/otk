import textwrap

import pytest

from otk.document import Omnifest
from otk.error import ParseTypeError, ParseVersionError


def test_omnifest_read_dict():
    assert Omnifest.read({}) == {}


def test_omnifest_read_list():
    with pytest.raises(ParseTypeError):
        Omnifest.read([])


def test_omnifest_read_string():
    with pytest.raises(ParseTypeError):
        Omnifest.read("")


def test_omnifest_ensure():
    Omnifest.ensure({"otk.version": 1})


def test_omnifest_ensure_no_keys():
    with pytest.raises(ParseVersionError):
        assert Omnifest.ensure({})


def test_omnifest_from_yaml_bytes_sad():
    # A bunch of YAMLs that don't contain a top level map
    with pytest.raises(ParseTypeError):
        Omnifest.from_yaml_bytes(
            """
"""
        )

    with pytest.raises(ParseTypeError):
        Omnifest.from_yaml_bytes(
            """
1
"""
        )

    with pytest.raises(ParseTypeError):
        Omnifest.from_yaml_bytes(
            """
- 1
- 2
"""
        )

    with pytest.raises(ParseTypeError):
        Omnifest.from_yaml_bytes(
            """
"1"
"""
        )

    # And a YAML that does have a top level map, but no `otk.version` key
    with pytest.raises(ParseVersionError):
        Omnifest.from_yaml_bytes(
            """
otk.not-version: 1
"""
        )


TEST_CASES = [
    (
        textwrap.dedent("""
        otk.version: 1
        otk.target.osbuild:
          some: key
        """),
        {"otk.target.osbuild": {"some": "key"}, "otk.version": 1},
    )
]


@pytest.mark.parametrize("fake_input,expected_tree", TEST_CASES)
def test_omnifest_from_yaml_bytes_happy(fake_input, expected_tree):
    omi = Omnifest.from_yaml_bytes(fake_input)
    assert omi.tree == expected_tree


@pytest.mark.parametrize("fake_input,expected_tree", TEST_CASES)
def test_omnifest_from_yaml_file_happy(tmp_path, fake_input, expected_tree):
    fake_yaml_path = tmp_path / "test.otk"
    fake_yaml_path.write_text(fake_input)

    with fake_yaml_path.open() as fp:
        omi = Omnifest.from_yaml_file(fp)
    assert omi.tree == expected_tree
